"""Tests for the benchmark grammar generator."""

def test_grammar_generation():
    from aperiodic_guardrails.benchmark.grammar import generate_grammar
    g = generate_grammar(seed=1000)
    assert "initial_state" in g
    assert "target" in g
    assert "rules" in g
    assert len(g["rules"]) > 5
    assert g["target"] == "N30"

def test_grammar_has_valid_path():
    from aperiodic_guardrails.benchmark.grammar import generate_grammar
    from collections import deque
    g = generate_grammar(seed=1042)
    # BFS to verify path exists
    queue = deque([(g["initial_state"], [])])
    visited = set()
    found = False
    while queue:
        state, path = queue.popleft()
        if g["target"] in state:
            found = True
            break
        key = tuple(state)
        if key in visited:
            continue
        visited.add(key)
        if len(path) >= 15:
            continue
        for rule in g["rules"]:
            if all(i in state for i in rule["inputs"]):
                new_state = sorted(set([s for s in state if s not in rule["inputs"]] + rule["outputs"]))
                queue.append((new_state, path + [rule["id"]]))
    assert found, "Grammar must have a valid path to target"
