"""
Grammar generation and state-space utilities for benchmark.

Generates synthetic grammars with:
- Guaranteed path to target
- Multiple paths with varying yields
- Dead-end traps with high yield estimates
- Optimal path requiring deeper exploration than shorter paths
"""
import random
from collections import deque


def generate_grammar(seed: int) -> dict:
    """
    Generates a grammar where:
    - There EXISTS a path from initial_state to target (guaranteed)
    - Multiple paths exist with different yields
    - Dead-end traps: high yield_est edges that never reach target
    - Optimal path is NOT the shortest (requires more steps but higher per-step yield)
    """
    rng = random.Random(seed)

    target = "N30"
    initial_state = ["N0", "N1"]
    rules = []
    rule_id = 0

    def next_rule_id():
        nonlocal rule_id
        rid = f"R{rule_id}"
        rule_id += 1
        return rid

    # ------------------------------------------------------------------
    # OPTIMAL PATH: depth d=5..8, yield_est ~0.85-0.95 per step
    # Chain: N0 -> N2 -> N3 -> ... -> N(d+1) -> N30
    # Each rule consumes one symbol and produces the next
    # N1 stays in state throughout (not consumed by optimal path)
    # ------------------------------------------------------------------
    opt_depth = rng.randint(5, 8)
    chain = ["N0"] + [f"N{i}" for i in range(2, opt_depth + 2)] + ["N30"]
    # chain[0]="N0", chain[-1]="N30", intermediates N2..N(opt_depth+1)

    for k in range(len(chain) - 1):
        r = {
            "id": next_rule_id(),
            "inputs": [chain[k]],
            "outputs": [chain[k + 1]],
            "yield_est": round(rng.uniform(0.85, 0.95), 3),
            "_path": "optimal"
        }
        rules.append(r)

    # optimal cumulative yield for reference
    opt_yield = 1.0
    for r in rules:
        if r.get("_path") == "optimal":
            opt_yield *= r["yield_est"]

    # ------------------------------------------------------------------
    # SHORT LOW-YIELD PATH A: depth 3, yield ~0.55-0.70 per step
    # Reaches target but product < optimal
    # N0 -> N10 -> N11 -> N30
    # ------------------------------------------------------------------
    shortA_yield = 1.0
    for (inp, out) in [("N0", "N10"), ("N10", "N11"), ("N11", "N30")]:
        ye = round(rng.uniform(0.55, 0.70), 3)
        shortA_yield *= ye
        rules.append({
            "id": next_rule_id(),
            "inputs": [inp],
            "outputs": [out],
            "yield_est": ye,
            "_path": "shortA"
        })

    # ------------------------------------------------------------------
    # SHORT LOW-YIELD PATH B: depth 3, yield ~0.40-0.55 per step
    # N0 -> N12 -> N13 -> N30
    # ------------------------------------------------------------------
    for (inp, out) in [("N0", "N12"), ("N12", "N13"), ("N13", "N30")]:
        ye = round(rng.uniform(0.40, 0.55), 3)
        rules.append({
            "id": next_rule_id(),
            "inputs": [inp],
            "outputs": [out],
            "yield_est": ye,
            "_path": "shortB"
        })

    # ------------------------------------------------------------------
    # DEAD-END TRAP 1: consumes N1 only, high yield, dead end at N23
    # N1 -> N20+N21 -> N22 -> N23  (N23 has no outgoing rules)
    # This trap looks attractive but doesn't consume N0, so N0-based paths
    # still work. However it pulls the beam toward N23.
    # ------------------------------------------------------------------
    rules.append({
        "id": next_rule_id(),
        "inputs": ["N1"],
        "outputs": ["N20", "N21"],
        "yield_est": round(rng.uniform(0.88, 0.95), 3),
        "_path": "trap1"
    })
    rules.append({
        "id": next_rule_id(),
        "inputs": ["N20"],
        "outputs": ["N22"],
        "yield_est": round(rng.uniform(0.88, 0.95), 3),
        "_path": "trap1"
    })
    rules.append({
        "id": next_rule_id(),
        "inputs": ["N22"],
        "outputs": ["N23"],
        "yield_est": round(rng.uniform(0.88, 0.95), 3),
        "_path": "trap1"
    })
    # N23 is a dead end — no rule produces N30 from it

    # ------------------------------------------------------------------
    # DEAD-END TRAP 2: consumes BOTH N0 and N1, prevents optimal path
    # N0+N1 -> N24+N25 -> N26  (dead end)
    # High yield per step, but state after has neither N0 nor N1
    # BFS correctly avoids (no path to N30 from N24/N25)
    # Random beam may follow (random scores)
    # ------------------------------------------------------------------
    rules.append({
        "id": next_rule_id(),
        "inputs": ["N0", "N1"],
        "outputs": ["N24", "N25"],
        "yield_est": round(rng.uniform(0.90, 0.96), 3),
        "_path": "trap2"
    })
    rules.append({
        "id": next_rule_id(),
        "inputs": ["N24"],
        "outputs": ["N26"],
        "yield_est": round(rng.uniform(0.90, 0.96), 3),
        "_path": "trap2"
    })
    # N26 dead end

    # ------------------------------------------------------------------
    # DEAD-END TRAP 3: consumes N1, dead end at N29
    # N1 -> N27+N28 -> N29
    # ------------------------------------------------------------------
    rules.append({
        "id": next_rule_id(),
        "inputs": ["N1"],
        "outputs": ["N27", "N28"],
        "yield_est": round(rng.uniform(0.85, 0.92), 3),
        "_path": "trap3"
    })
    rules.append({
        "id": next_rule_id(),
        "inputs": ["N27"],
        "outputs": ["N29"],
        "yield_est": round(rng.uniform(0.85, 0.92), 3),
        "_path": "trap3"
    })

    # ------------------------------------------------------------------
    # NOISE RULES: never applicable (inputs not reachable)
    # ------------------------------------------------------------------
    noise_inputs = ["N31", "N32", "N33"]
    for k in range(rng.randint(3, 5)):
        rules.append({
            "id": next_rule_id(),
            "inputs": [rng.choice(noise_inputs)],
            "outputs": [f"N{34 + k}"],
            "yield_est": round(rng.uniform(0.3, 0.9), 3),
            "_path": "noise"
        })

    # ------------------------------------------------------------------
    # CONSTRAINTS: forbidden pairs on symbols not on optimal path
    # ------------------------------------------------------------------
    constraints = [
        {"type": "forbidden_pair", "params": ["N20", "N27"]},
        {"type": "forbidden_pair", "params": ["N24", "N10"]},
        {"type": "forbidden_pair", "params": ["N22", "N11"]},
    ]
    # Pick 2-4 constraints
    n_constraints = rng.randint(2, 4)
    constraints = constraints[:n_constraints]

    # Strip internal annotation before returning
    clean_rules = [{k: v for k, v in r.items() if k != "_path"} for r in rules]

    grammar = {
        "initial_state": initial_state,
        "target": target,
        "rules": clean_rules,
        "constraints": constraints,
    }

    # Validation: BFS must find a path
    check = _quick_bfs_check(initial_state, target, clean_rules, constraints)
    if check == 0.0:
        raise ValueError(f"Grammar seed={seed} has no path to target — bug in generator")

    return grammar


def _quick_bfs_check(initial_state, target, rules, constraints):
    """Returns nonzero score if target is reachable, 0.0 otherwise."""
    queue = deque([(initial_state, [], 1.0)])
    visited = set()
    while queue:
        state, path, score = queue.popleft()
        if target in state:
            return score
        key = tuple(state)
        if key in visited:
            continue
        visited.add(key)
        if len(path) >= 15:
            continue
        for rule in [r for r in rules if all(i in state for i in r["inputs"])]:
            new_state = sorted(set([s for s in state if s not in rule["inputs"]] + rule["outputs"]))
            ok = True
            for c in constraints:
                if c["type"] == "forbidden_pair":
                    if c["params"][0] in new_state and c["params"][1] in new_state:
                        ok = False
                        break
            if ok:
                queue.append((new_state, path + [rule["id"]], score * rule["yield_est"]))
    return 0.0


# ---------------------------------------------------------------------------
# Shared state-space helpers
# ---------------------------------------------------------------------------

def _applicable_rules(state, rules):
    """Return list of rules applicable to current state."""
    return [r for r in rules if all(i in state for i in r["inputs"])]


def _apply_rule(state, rule):
    """Apply a rule to state: remove inputs, add outputs."""
    new = [s for s in state if s not in rule["inputs"]]
    new.extend(rule["outputs"])
    return sorted(set(new))


def _check_constraints(state, constraints):
    """Check if state violates any constraints."""
    for c in constraints:
        if c["type"] == "forbidden_pair":
            if c["params"][0] in state and c["params"][1] in state:
                return False
    return True
