"""AST template: BFS state-space solver. Zero domain content."""
import ast


def build_graph_solver_ast() -> ast.Module:
    source = '''
from collections import deque

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

def run(initial_state, target, rules, constraints):
    queue = deque([(initial_state, [], 1.0)])
    visited = set()
    best = None
    while queue:
        state, path, score = queue.popleft()
        key = tuple(state)
        if target in state:
            if best is None or score > best["score"]:
                best = {"path": path, "score": score, "final_state": state}
            continue
        if key in visited:
            continue
        visited.add(key)
        if len(path) >= 10:
            continue
        for rule in applicable_rules(state, rules):
            new_state = apply_rule(state, rule)
            if check_constraints(new_state, constraints):
                new_score = score * rule["yield_est"]
                queue.append((new_state, path + [rule["id"]], new_score))
    return best or {"path": [], "score": 0, "final_state": initial_state}
'''
    tree = ast.parse(source)
    ast.fix_missing_locations(tree)
    return tree
