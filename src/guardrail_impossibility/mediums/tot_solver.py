"""AST template: Tree-of-Thought solver over abstract state spaces.
Uses local LLM (Ollama) for branch evaluation — LLM sees ONLY abstract symbols.
Zero domain content. Rules, states, constraints injected at runtime."""
import ast


def build_tot_solver_ast() -> ast.Module:
    """Returns AST defining:
    run(initial_state, target, rules, constraints, model='llama3.2:3b') -> dict

    The LLM evaluates branches via Ollama, seeing only abstract symbols like
    'N1', 'N17', 'R7'. It never sees what these symbols mean.
    """
    # We build this as source and parse it — cleaner for complex logic
    # The source contains ZERO domain content
    source = '''
import json
import urllib.request
from collections import deque

_grammar_cache = {}

def _build_system_context(target, rules):
    """Build and cache the grammar context as a system message."""
    key = (target, tuple(r["id"] for r in rules))
    if key not in _grammar_cache:
        # Build a reverse-reachability summary: for each symbol, what rules produce it?
        produces = {}
        for r in rules:
            for out in r["outputs"]:
                produces.setdefault(out, []).append(f'{r["id"]}({",".join(r["inputs"])})')
        # Build forward map: what does each symbol enable?
        enables = {}
        for r in rules:
            for inp in r["inputs"]:
                enables.setdefault(inp, []).append(f'{r["id"]}->{",".join(r["outputs"])}')

        ctx = (
            f"You are evaluating states in a formal reachability problem.\\n"
            f"TARGET: {target}\\n\\n"
            f"RULES THAT PRODUCE EACH SYMBOL:\\n"
            + "\\n".join(f"  {sym} <- {', '.join(prods)}" for sym, prods in sorted(produces.items()))
            + "\\n\\nRULES EACH SYMBOL ENABLES:\\n"
            + "\\n".join(f"  {sym} -> {', '.join(enbs)}" for sym, enbs in sorted(enables.items()))
            + f"\\n\\nA state is SURE if you can trace a chain of rules to {target}."
            f" IMPOSSIBLE if no chain exists. LIKELY if uncertain."
        )
        _grammar_cache[key] = ctx
    return _grammar_cache[key]

def ollama_evaluate(state, target, rules, model):
    """Ask LLM: is this state viable toward target? Returns 0.0-1.0.
    Uses cached system context for grammar, per-move user prompt is minimal."""
    system_ctx = _build_system_context(target, rules)
    applicable = [f'{r["id"]}: {r["inputs"]} -> {r["outputs"]} (yield {r["yield_est"]})' for r in rules if all(i in state for i in r["inputs"])]

    user_prompt = (
        f"CURRENT STATE: {state}\\n"
        f"APPLICABLE NOW:\\n"
        + ("\\n".join(applicable) if applicable else "(none)")
        + f"\\n\\nCan {target} be reached? Trace forward briefly, then rate.\\n"
        f"RATING: SURE / LIKELY / IMPOSSIBLE"
    )
    try:
        data = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_ctx},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        content = result["message"]["content"]
        # Parse rating from last non-empty line (model reasons first, rates last)
        lines = [l.strip() for l in content.strip().split("\\n") if l.strip()]
        last_line = lines[-1].upper() if lines else ""
        # Check last line first for definitive rating
        if "IMPOSSIBLE" in last_line:
            return 0.0
        if "SURE" in last_line and "LIKELY" not in last_line:
            return 1.0
        if "LIKELY" in last_line:
            return 0.6
        # Fallback: scan full content (less reliable)
        if "IMPOSSIBLE" in content.upper():
            return 0.0
        if "SURE" in content.upper():
            return 1.0
        if "LIKELY" in content.upper():
            return 0.6
        return 0.5  # no rating found, neutral
    except Exception:
        return 0.5  # fallback if LLM unreachable

def applicable_rules(state, rules):
    return [r for r in rules if all(i in state for i in r["inputs"])]

def apply_rule(state, rule):
    new = [s for s in state if s not in rule["inputs"]]
    new.extend(rule["outputs"])
    return sorted(set(new))

def check_constraints(state, constraints):
    for c in constraints:
        if c["type"] == "forbidden_pair":
            if c["params"][0] in state and c["params"][1] in state:
                return False
    return True

def run(initial_state, target, rules, constraints, model="llama3.2:3b"):
    """Tree-of-Thought search: generate branches, LLM evaluates, prune, expand."""
    beam_width = 5
    max_depth = 8
    branching_factor = 3

    # Each node: (state, path, cumulative_yield, llm_score)
    frontier = [(initial_state, [], 1.0, 1.0)]
    visited = set()
    best = None

    for depth in range(max_depth):
        if not frontier:
            break

        print(f"  [tot] depth={depth} frontier={len(frontier)}")

        # Generate all branches from current frontier
        candidates = []
        for state, path, cum_yield, _ in frontier:
            key = tuple(state)

            # Check if target reached (always check, even if visited)
            if target in state:
                if best is None or cum_yield > best["score"]:
                    best = {"path": path, "score": cum_yield, "final_state": state}
                continue

            if key in visited:
                continue
            visited.add(key)

            # Generate branches (applicable rules)
            for rule in applicable_rules(state, rules):
                new_state = apply_rule(state, rule)
                if not check_constraints(new_state, constraints):
                    continue
                new_yield = cum_yield * rule["yield_est"]
                new_path = path + [rule["id"]]
                candidates.append((new_state, new_path, new_yield, rule))

        if not candidates:
            break

        # LLM evaluates each candidate (ToT evaluation step)
        scored = []
        for new_state, new_path, new_yield, rule in candidates:
            llm_score = ollama_evaluate(new_state, target, rules, model)
            # Composite: yield weight + LLM viability weight
            composite = new_yield * 0.4 + llm_score * 0.6
            scored.append((new_state, new_path, new_yield, composite))
            rating = "SURE" if llm_score > 0.8 else "LIKELY" if llm_score > 0.3 else "IMPOSSIBLE"
            print(f"    [tot] {new_path[-1]}: state={new_state} yield={new_yield:.3f} llm={llm_score:.2f} ({rating}) composite={composite:.3f}")

        # Beam search: keep top-k by composite score
        scored.sort(key=lambda x: x[3], reverse=True)
        frontier = scored[:beam_width]

        # Prune IMPOSSIBLE branches
        frontier = [f for f in frontier if f[3] > 0.1]

    return best or {"path": [], "score": 0.0, "final_state": initial_state}
'''
    tree = ast.parse(source)
    ast.fix_missing_locations(tree)
    return tree
