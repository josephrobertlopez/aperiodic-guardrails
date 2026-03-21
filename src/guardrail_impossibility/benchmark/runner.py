"""
Benchmark runner: BFS vs Random-Beam vs ToT+LLM on generated grammars.

Tests the claim from Paper 1: mean yield 0.512 (ToT) vs 0.203 (random) vs 0.119 (BFS).
"""
import random
import json
import time
import statistics
import urllib.request
import datetime
import concurrent.futures
import os
from scipy.stats import wilcoxon

from .grammar import (
    generate_grammar,
    _applicable_rules,
    _apply_rule,
    _check_constraints,
)


# ---------------------------------------------------------------------------
# Solver 1: BFS (exhaustive best-yield)
# ---------------------------------------------------------------------------

def run_bfs(initial_state, target, rules, constraints):
    """
    Breadth-first search for highest-yield path to target.

    Explores all reachable states, always updating best when target is reached,
    without deduplicating terminal states to allow higher-yield paths to win.
    """
    from collections import deque

    queue = deque([(initial_state, [], 1.0)])
    # visited tracks non-terminal states only; terminal states (containing target)
    # are NOT deduplicated so that higher-yield paths can update best
    visited = set()
    best = None
    states_explored = 0

    while queue:
        state, path, score = queue.popleft()

        if target in state:
            # Always update best — do NOT deduplicate terminal states
            states_explored += 1
            if best is None or score > best["score"]:
                best = {"path": path, "score": score, "final_state": state}
            continue

        key = tuple(state)
        if key in visited:
            continue
        visited.add(key)
        states_explored += 1

        if len(path) >= 12:
            continue

        for rule in _applicable_rules(state, rules):
            new_state = _apply_rule(state, rule)
            if _check_constraints(new_state, constraints):
                new_score = score * rule["yield_est"]
                queue.append((new_state, path + [rule["id"]], new_score))

    result = best or {"path": [], "score": 0.0, "final_state": initial_state}
    result["states_explored"] = states_explored
    return result


# ---------------------------------------------------------------------------
# Solver 2: Random Beam (beam search with uniform random evaluation)
# ---------------------------------------------------------------------------

def run_random_beam(initial_state, target, rules, constraints):
    """
    Beam search with random scoring of candidates.

    At each depth, keeps top K candidates using random + yield composite score.
    """
    beam_width = 5
    max_depth = 8
    frontier = [(initial_state, [], 1.0, 1.0)]
    visited = set()
    best = None
    states_explored = 0

    for depth in range(max_depth):
        if not frontier:
            break

        candidates = []
        for state, path, cum_yield, _ in frontier:
            key = tuple(state)
            if key in visited:
                continue
            visited.add(key)
            states_explored += 1

            if target in state:
                if best is None or cum_yield > best["score"]:
                    best = {"path": path, "score": cum_yield, "final_state": state}
                continue

            for rule in _applicable_rules(state, rules):
                new_state = _apply_rule(state, rule)
                if not _check_constraints(new_state, constraints):
                    continue
                new_yield = cum_yield * rule["yield_est"]
                new_path = path + [rule["id"]]
                rand_score = random.uniform(0, 1)
                composite = new_yield * 0.4 + rand_score * 0.6
                candidates.append((new_state, new_path, new_yield, composite))

        if not candidates:
            break

        candidates.sort(key=lambda x: x[3], reverse=True)
        frontier = [c for c in candidates[:beam_width] if c[3] > 0.1]

    result = best or {"path": [], "score": 0.0, "final_state": initial_state}
    result["states_explored"] = states_explored
    return result


# ---------------------------------------------------------------------------
# Solver 3: ToT + LLM (beam search with Ollama evaluation)
# ---------------------------------------------------------------------------

def _ollama_evaluate(state, target, rules, model):
    """
    Query Ollama LLM to evaluate reachability from state to target.

    Returns confidence score [0, 1] indicating likelihood of reaching target.
    Falls back to 0.5 on network errors.
    """
    applicable = [
        f'{r["id"]}: {r["inputs"]} -> {r["outputs"]} (yield {r["yield_est"]:.2f})'
        for r in rules if all(i in state for i in r["inputs"])
    ]
    all_rules = [f'{r["id"]}: {r["inputs"]} -> {r["outputs"]}' for r in rules]
    prompt = (
        f"Formal system reachability problem.\n"
        f"ALL rules: {all_rules}\n"
        f"Current state: {state}\n"
        f"Target: {target}\n"
        f"Applicable NOW: {applicable}\n"
        f"Can {target} be reached from {state} using these rules? "
        f"Think step by step about what each applicable rule produces and whether "
        f"those outputs eventually lead to {target}.\n"
        f"Respond with ONLY a JSON object: "
        f'{{\"rating\": \"SURE\" or \"LIKELY\" or \"IMPOSSIBLE\", \"confidence\": 0.0-1.0}}'
    )
    try:
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        content = result["message"]["content"]
        if "IMPOSSIBLE" in content:
            return 0.0
        if "SURE" in content:
            return 1.0
        if "LIKELY" in content:
            return 0.6
        try:
            parsed = json.loads(content)
            rating_map = {"SURE": 1.0, "LIKELY": 0.6, "IMPOSSIBLE": 0.0}
            base = rating_map.get(parsed.get("rating", "LIKELY"), 0.5)
            conf = float(parsed.get("confidence", 0.5))
            return base * 0.7 + conf * 0.3
        except Exception:
            return 0.5
    except Exception:
        return 0.5


def run_tot_llm(initial_state, target, rules, constraints, model="qwen2.5-coder:7b"):
    """
    Tree of Thought with LLM scoring.

    Beam search where candidates are scored using Ollama LLM evaluation
    of reachability, combined with actual yield estimates.
    """
    beam_width = 5
    max_depth = 8
    frontier = [(initial_state, [], 1.0, 1.0)]
    visited = set()
    best = None
    states_explored = 0

    for depth in range(max_depth):
        if not frontier:
            break

        print(f"  [tot] depth={depth} frontier={len(frontier)}")
        candidates = []
        for state, path, cum_yield, _ in frontier:
            key = tuple(state)
            if key in visited:
                continue
            visited.add(key)
            states_explored += 1

            if target in state:
                if best is None or cum_yield > best["score"]:
                    best = {"path": path, "score": cum_yield, "final_state": state}
                continue

            for rule in _applicable_rules(state, rules):
                new_state = _apply_rule(state, rule)
                if not _check_constraints(new_state, constraints):
                    continue
                new_yield = cum_yield * rule["yield_est"]
                new_path = path + [rule["id"]]
                candidates.append((new_state, new_path, new_yield, rule))

        if not candidates:
            break

        scored = []
        for new_state, new_path, new_yield, rule in candidates:
            llm_score = _ollama_evaluate(new_state, target, rules, model)
            composite = new_yield * 0.4 + llm_score * 0.6
            scored.append((new_state, new_path, new_yield, composite))
            rating = "SURE" if llm_score > 0.8 else ("LIKELY" if llm_score > 0.3 else "IMPOSSIBLE")
            print(f"    [tot] {new_path[-1]}: llm={llm_score:.2f} ({rating}) composite={composite:.3f}")

        scored.sort(key=lambda x: x[3], reverse=True)
        frontier = [f for f in scored[:beam_width] if f[3] > 0.1]

    result = best or {"path": [], "score": 0.0, "final_state": initial_state}
    result["states_explored"] = states_explored
    return result


# ---------------------------------------------------------------------------
# Benchmark execution
# ---------------------------------------------------------------------------

def run_with_timeout(fn, args, kwargs, timeout):
    """Execute function with timeout using thread pool."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(fn, *args, **kwargs)
        return future.result(timeout=timeout)


def run_benchmark(n=20, timeout_per_method=60):
    """
    Run benchmark on N randomly generated grammars.

    Tests three solvers: BFS, Random Beam, and ToT+LLM.
    Returns list of result dicts, one per grammar.
    """
    results = []

    for grammar_idx in range(n):
        seed = 1000 + grammar_idx
        print(f"\n--- Grammar {grammar_idx} (seed={seed}) ---")

        grammar = generate_grammar(seed)
        print(f"  rules={len(grammar['rules'])}, constraints={len(grammar['constraints'])}, target={grammar['target']}")

        grammar_result = {
            "grammar_id": grammar_idx,
            "seed": seed,
            "n_rules": len(grammar["rules"]),
            "n_constraints": len(grammar["constraints"]),
        }

        solvers = [
            ("bfs",         run_bfs,         [], {}),
            ("random_beam", run_random_beam,  [], {}),
            ("tot_llm",     run_tot_llm,      [], {"model": "qwen2.5-coder:7b"}),
        ]

        for method_name, solver_fn, extra_args, extra_kwargs in solvers:
            print(f"  [{method_name}] running...")
            t0 = time.time()
            try:
                args = [grammar["initial_state"], grammar["target"],
                        grammar["rules"], grammar["constraints"]] + extra_args
                result = run_with_timeout(solver_fn, args, extra_kwargs, timeout_per_method)
            except concurrent.futures.TimeoutError:
                print(f"  [{method_name}] TIMEOUT")
                result = {
                    "path": [], "score": 0.0,
                    "final_state": grammar["initial_state"],
                    "timed_out": True,
                    "states_explored": -1
                }
            except Exception as e:
                print(f"  [{method_name}] ERROR: {e}")
                result = {
                    "path": [], "score": 0.0,
                    "final_state": grammar["initial_state"],
                    "timed_out": False,
                    "states_explored": -1
                }
            wall_time = time.time() - t0

            grammar_result[method_name] = {
                "score": result.get("score", 0.0),
                "path_len": len(result.get("path", [])),
                "path": result.get("path", []),
                "wall_time": round(wall_time, 3),
                "states_explored": result.get("states_explored", -1),
                "timed_out": result.get("timed_out", False),
            }
            print(f"  [{method_name}] score={grammar_result[method_name]['score']:.4f} "
                  f"path_len={grammar_result[method_name]['path_len']} "
                  f"time={wall_time:.1f}s")

        r = grammar_result
        print(f"  SUMMARY: BFS={r['bfs']['score']:.3f} | "
              f"RandBeam={r['random_beam']['score']:.3f} | "
              f"ToT={r['tot_llm']['score']:.3f}")
        results.append(grammar_result)

    return results


def compute_stats(results):
    """
    Compute descriptive statistics and Wilcoxon test results.

    Returns dict with mean/std/min/max for each method plus test results.
    """
    bfs_scores  = [r["bfs"]["score"]         for r in results]
    rand_scores = [r["random_beam"]["score"]  for r in results]
    tot_scores  = [r["tot_llm"]["score"]      for r in results]

    def safe_wilcoxon(a, b, alternative='greater'):
        try:
            stat, p = wilcoxon(a, b, alternative=alternative)
            return {"stat": round(float(stat), 4), "p": round(float(p), 6)}
        except ValueError as e:
            return {"stat": 0.0, "p": 1.0, "note": str(e)}

    def desc(scores):
        return {
            "mean": round(statistics.mean(scores), 4),
            "std":  round(statistics.stdev(scores), 4) if len(scores) > 1 else 0.0,
            "min":  round(min(scores), 4),
            "max":  round(max(scores), 4),
        }

    return {
        "bfs":         desc(bfs_scores),
        "random_beam": desc(rand_scores),
        "tot_llm":     desc(tot_scores),
        "wilcoxon_tot_vs_rand": safe_wilcoxon(tot_scores,  rand_scores),
        "wilcoxon_bfs_vs_rand": safe_wilcoxon(bfs_scores,  rand_scores),
        "wilcoxon_bfs_vs_tot":  safe_wilcoxon(bfs_scores,  tot_scores),
    }


def print_summary(stats):
    """Print formatted summary of benchmark results."""
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS (N=20)")
    print("=" * 60)
    print(f"{'Method':<15} {'Mean Yield':>12} {'Std':>8} {'Min':>8} {'Max':>8}")
    print("-" * 55)
    for method, label in [("bfs", "BFS"), ("random_beam", "Random Beam"), ("tot_llm", "ToT+LLM")]:
        s = stats[method]
        print(f"{label:<15} {s['mean']:>12.4f} {s['std']:>8.4f} {s['min']:>8.4f} {s['max']:>8.4f}")

    print("\nWILCOXON TESTS (one-sided: row > col)")
    print("-" * 55)
    w = stats["wilcoxon_tot_vs_rand"]
    print(f"ToT+LLM vs Random Beam: stat={w['stat']:.3f}, p={w['p']:.4f}")
    w = stats["wilcoxon_bfs_vs_rand"]
    print(f"BFS vs Random Beam:     stat={w['stat']:.3f}, p={w['p']:.4f}")
    w = stats["wilcoxon_bfs_vs_tot"]
    print(f"BFS vs ToT+LLM:         stat={w['stat']:.3f}, p={w['p']:.4f}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    results = run_benchmark(n=n)
    stats   = compute_stats(results)

    print_summary(stats)

    output = {
        "meta": {
            "n_grammars": n,
            "model": "qwen2.5-coder:7b",
            "timeout_per_method": 60,
            "date": datetime.datetime.utcnow().isoformat() + "Z",
        },
        "summary": stats,
        "grammars": results,
    }

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")
