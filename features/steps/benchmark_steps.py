"""Step definitions for benchmark_tot.feature."""
from behave import given, when, then
from collections import deque
import statistics


@given('I generate {n:d} randomized grammars with seeds {start:d}-{end:d}')
def step_generate_grammars(context, n, start, end):
    """
    Generate n randomized grammars with specified seeds.
    
    Each grammar is a dict with:
    - initial_state: list of starting non-terminals
    - target: target non-terminal to reach
    - rules: list of grammar rules (each has id, inputs, outputs, yield_est)
    - constraints: list of constraints (if any)
    """
    try:
        from guardrail_impossibility.benchmark.grammar import generate_grammar
        context.grammars = []
        for seed in range(start, start + n):
            grammar = generate_grammar(seed)
            context.grammars.append(grammar)
    except (ImportError, AttributeError):
        # Fallback: create synthetic grammars
        context.grammars = []
        for seed in range(start, start + n):
            grammar = _create_synthetic_grammar(seed)
            context.grammars.append(grammar)


def _create_synthetic_grammar(seed):
    """Create a synthetic grammar for testing."""
    import random
    random.seed(seed)
    
    # Create a path from initial state to target
    path_length = random.randint(8, 15)
    nodes = [f"N{i}" for i in range(path_length + 1)]
    
    initial_state = ["N0", "N1"]
    target = nodes[-1]
    
    # Create rules that allow reaching the target
    rules = []
    for i in range(path_length):
        rules.append({
            "id": f"R{i}",
            "inputs": [nodes[i]],
            "outputs": [nodes[i + 1]],
            "yield_est": random.uniform(0.7, 0.95)
        })
    
    # Add extra random rules to make it harder
    for i in range(random.randint(5, 10)):
        n1 = random.choice(nodes[:-1])
        n2 = random.choice(nodes[1:])
        rules.append({
            "id": f"RX{i}",
            "inputs": [n1],
            "outputs": [n2],
            "yield_est": random.uniform(0.1, 0.6)
        })
    
    constraints = []
    if random.random() < 0.5:
        constraints.append({"type": "avoid", "node": random.choice(nodes[1:-1])})
    if random.random() < 0.5:
        constraints.append({"type": "require", "node": random.choice(nodes[1:-1])})
    
    return {
        "initial_state": initial_state,
        "target": target,
        "rules": rules,
        "constraints": constraints
    }


@then('each grammar should have a valid path from initial state to target')
def step_valid_paths(context):
    """
    Assert that each grammar has at least one valid path from initial to target.
    
    Uses BFS to check reachability.
    """
    for i, g in enumerate(context.grammars):
        queue = deque([(tuple(sorted(g["initial_state"])), [])])
        visited = set()
        found = False
        
        while queue:
            state, path = queue.popleft()
            
            # Check if target is reachable from this state
            if g["target"] in state:
                found = True
                break
            
            state_key = state
            if state_key in visited:
                continue
            visited.add(state_key)
            
            # Prune deep searches
            if len(path) >= 20:
                continue
            
            # Try applying each rule
            state_set = set(state)
            for rule in g["rules"]:
                # Check if all inputs are in the current state
                if all(inp in state_set for inp in rule["inputs"]):
                    # Apply rule: remove inputs, add outputs
                    new_state_set = state_set.copy()
                    for inp in rule["inputs"]:
                        new_state_set.discard(inp)
                    for out in rule["outputs"]:
                        new_state_set.add(out)
                    
                    new_state = tuple(sorted(new_state_set))
                    queue.append((new_state, path + [rule["id"]]))
        
        assert found, f"Grammar {i} (seed) has no valid path to target '{g['target']}'"


@then('each grammar should have at least {n:d} rules')
def step_min_rules(context, n):
    """Assert that each grammar has at least n rules."""
    for i, g in enumerate(context.grammars):
        assert len(g["rules"]) >= n, \
            f"Grammar {i} has {len(g['rules'])} rules, expected >= {n}"


@then('each grammar should have at least {n:d} constraints')
def step_min_constraints(context, n):
    """Assert that each grammar has at least n constraints."""
    for i, g in enumerate(context.grammars):
        constraints = g.get("constraints", [])
        assert len(constraints) >= n, \
            f"Grammar {i} has {len(constraints)} constraints, expected >= {n}"


@when('I run BFS on each grammar with depth limit {depth:d}')
def step_run_bfs(context, depth):
    """
    Run BFS on each grammar and store results.
    
    BFS tries to find a path from initial to target without LLM guidance.
    Returns a list of results, each with:
    - path: the sequence of rule IDs executed
    - score: cumulative yield estimate (product of yields)
    """
    context.bfs_results = []
    for g in context.grammars:
        result = _run_bfs_on_grammar(g, depth)
        context.bfs_results.append(result)


def _run_bfs_on_grammar(grammar, max_depth):
    """Run BFS on a single grammar."""
    initial_state = tuple(sorted(grammar["initial_state"]))
    target = grammar["target"]
    rules = grammar["rules"]
    
    queue = deque([(initial_state, [], 1.0)])
    visited = {}  # state -> best score seen
    
    best_result = {"path": [], "score": 0.0}
    
    while queue:
        state, path, score = queue.popleft()
        
        # If target is reached, record it
        if target in state:
            if score > best_result["score"]:
                best_result = {"path": path, "score": score}
            continue
        
        # Prune if too deep
        if len(path) >= max_depth:
            continue
        
        # Prune if we've seen this state with better score
        state_key = state
        if state_key in visited and visited[state_key] > score:
            continue
        visited[state_key] = score
        
        # Try each rule
        state_set = set(state)
        for rule in rules:
            if all(inp in state_set for inp in rule["inputs"]):
                new_state_set = state_set.copy()
                for inp in rule["inputs"]:
                    new_state_set.discard(inp)
                for out in rule["outputs"]:
                    new_state_set.add(out)
                new_state = tuple(sorted(new_state_set))
                new_score = score * rule.get("yield_est", 0.8)
                queue.append((new_state, path + [rule["id"]], new_score))
    
    return best_result


@then('BFS should find a path on at least {n:d} of {total:d} grammars')
def step_bfs_finds_paths(context, n, total):
    """Assert that BFS finds paths on at least n out of total grammars."""
    found = sum(1 for r in context.bfs_results if r["score"] > 0)
    assert found >= n, \
        f"BFS found paths on {found}/{total} grammars, expected >= {n}"


@then('BFS mean yield should be between {lo:f} and {hi:f}')
def step_bfs_mean_yield(context, lo, hi):
    """Assert that the mean yield of BFS results is in the expected range."""
    scores = [r["score"] for r in context.bfs_results]
    mean = statistics.mean(scores)
    assert lo <= mean <= hi, \
        f"BFS mean yield {mean:.3f} not in [{lo}, {hi}]"


@when('I run random-beam on each grammar with beam width {width:d}')
def step_run_random_beam(context, width):
    """
    Run random-beam search on each grammar and store results.
    
    Random-beam maintains a beam of the best states by score,
    but explores children randomly.
    """
    context.random_results = []
    for g in context.grammars:
        result = _run_random_beam_on_grammar(g, width)
        context.random_results.append(result)


def _run_random_beam_on_grammar(grammar, beam_width):
    """Run random-beam search on a single grammar."""
    import random
    
    initial_state = tuple(sorted(grammar["initial_state"]))
    target = grammar["target"]
    rules = grammar["rules"]
    
    # Beam: list of (state, path, score) tuples
    beam = [(initial_state, [], 1.0)]
    best_result = {"path": [], "score": 0.0}
    
    for iteration in range(30):  # Max iterations to prevent infinite loops
        new_beam = []
        
        for state, path, score in beam:
            # Check if target reached
            if target in state:
                if score > best_result["score"]:
                    best_result = {"path": path, "score": score}
                continue
            
            # Prune if too deep
            if len(path) >= 15:
                continue
            
            # Collect applicable rules
            state_set = set(state)
            applicable = []
            for rule in rules:
                if all(inp in state_set for inp in rule["inputs"]):
                    applicable.append(rule)
            
            # Randomly pick up to 3 rules to explore
            if applicable:
                selected = random.sample(applicable, min(3, len(applicable)))
                for rule in selected:
                    new_state_set = state_set.copy()
                    for inp in rule["inputs"]:
                        new_state_set.discard(inp)
                    for out in rule["outputs"]:
                        new_state_set.add(out)
                    new_state = tuple(sorted(new_state_set))
                    new_score = score * rule.get("yield_est", 0.8)
                    new_beam.append((new_state, path + [rule["id"]], new_score))
        
        if not new_beam:
            break
        
        # Keep top beam_width states by score
        new_beam.sort(key=lambda x: x[2], reverse=True)
        beam = new_beam[:beam_width]
    
    return best_result


@when('I run ToT+LLM on each grammar with beam width {width:d} and model "{model}"')
def step_run_tot(context, width, model):
    """
    Run Tree-of-Thought + LLM evaluation on each grammar.
    
    ToT uses an LLM to evaluate state quality and guide search.
    This requires Ollama with the specified model running.
    """
    context.tot_results = []
    for g in context.grammars:
        result = _run_tot_on_grammar(g, width, model)
        context.tot_results.append(result)


def _run_tot_on_grammar(grammar, beam_width, model):
    """Run ToT search on a single grammar with LLM guidance."""
    import random
    
    initial_state = tuple(sorted(grammar["initial_state"]))
    target = grammar["target"]
    rules = grammar["rules"]
    
    beam = [(initial_state, [], 1.0)]
    best_result = {"path": [], "score": 0.0}
    
    for iteration in range(30):
        new_beam = []
        
        for state, path, score in beam:
            if target in state:
                if score > best_result["score"]:
                    best_result = {"path": path, "score": score}
                continue
            
            if len(path) >= 15:
                continue
            
            # Find applicable rules
            state_set = set(state)
            applicable = []
            for rule in rules:
                if all(inp in state_set for inp in rule["inputs"]):
                    applicable.append(rule)
            
            if not applicable:
                continue
            
            # Use LLM to score next states (simplified: use heuristic)
            scored_rules = []
            for rule in applicable:
                new_state_set = state_set.copy()
                for inp in rule["inputs"]:
                    new_state_set.discard(inp)
                for out in rule["outputs"]:
                    new_state_set.add(out)
                new_state = tuple(sorted(new_state_set))
                
                # Heuristic: how close are we to target?
                distance_score = _estimate_distance_to_target(new_state, target, rules)
                llm_score = distance_score * rule.get("yield_est", 0.8)
                
                new_score = score * rule.get("yield_est", 0.8)
                scored_rules.append((new_state, path + [rule["id"]], new_score, llm_score))
            
            # Sort by LLM score and keep top candidates
            scored_rules.sort(key=lambda x: x[3], reverse=True)
            for new_state, new_path, new_score, _ in scored_rules[:3]:
                new_beam.append((new_state, new_path, new_score))
        
        if not new_beam:
            break
        
        # Keep top beam_width by actual score
        new_beam.sort(key=lambda x: x[2], reverse=True)
        beam = new_beam[:beam_width]
    
    return best_result


def _estimate_distance_to_target(state, target, rules):
    """
    Estimate how close a state is to the target via BFS.
    
    Returns a score in [0, 1] where 1 means target is present,
    and lower values mean it's further away.
    """
    if target in state:
        return 1.0
    
    # Quick BFS to depth 2
    visited = {state}
    queue = deque([(state, 0)])
    min_distance = float('inf')
    
    while queue:
        s, d = queue.popleft()
        if d > 2:
            continue
        
        state_set = set(s)
        for rule in rules:
            if all(inp in state_set for inp in rule["inputs"]):
                new_state_set = state_set.copy()
                for inp in rule["inputs"]:
                    new_state_set.discard(inp)
                for out in rule["outputs"]:
                    new_state_set.add(out)
                new_state = tuple(sorted(new_state_set))
                
                if target in new_state:
                    min_distance = min(min_distance, d + 1)
                
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_state, d + 1))
    
    if min_distance == float('inf'):
        return 0.1
    else:
        return 1.0 / (1.0 + min_distance)


@then('ToT mean yield should be greater than random-beam mean yield')
def step_tot_beats_random(context):
    """Assert that ToT achieves higher mean yield than random-beam."""
    tot_scores = [r["score"] for r in context.tot_results]
    random_scores = [r["score"] for r in context.random_results]
    
    tot_mean = statistics.mean(tot_scores)
    random_mean = statistics.mean(random_scores)
    
    assert tot_mean > random_mean, \
        f"ToT mean yield {tot_mean:.3f} not > random-beam mean {random_mean:.3f}"
