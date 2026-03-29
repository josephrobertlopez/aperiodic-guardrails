"""
Honest N=50 benchmark: BFS vs Random-Beam vs ToT+LLM (llama3.1:8b).

Seeds 0-49. Records mean yield, solve rate, states explored, 95% CI,
and Wilcoxon signed-rank pairwise comparisons.

Results saved to results/tot_n50_honest.json
Checkpoint updated at checkpoints/FIX-tot-fabrication.json
"""

import sys
import os
import json
import time
import math
import statistics
import datetime
import concurrent.futures
import random

# Make src importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from aperiodic_guardrails.benchmark.grammar import generate_grammar
from aperiodic_guardrails.benchmark.runner import (
    run_bfs,
    run_random_beam,
    run_tot_llm,
    compute_stats,
)
from scipy.stats import wilcoxon


RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results", "tot_n50_honest.json")
CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "checkpoints", "FIX-tot-fabrication.json")
MODEL = "llama3.1:8b"
N = 50
TIMEOUT = 90  # seconds per solver per grammar


def run_with_timeout(fn, args, kwargs, timeout):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(fn, *args, **kwargs)
        return future.result(timeout=timeout)


def bootstrap_ci(scores, n_boot=2000, ci=0.95):
    """Bootstrap 95% confidence interval for the mean."""
    rng = random.Random(42)
    n = len(scores)
    boot_means = []
    for _ in range(n_boot):
        sample = [rng.choice(scores) for _ in range(n)]
        boot_means.append(statistics.mean(sample))
    boot_means.sort()
    lo = boot_means[int((1 - ci) / 2 * n_boot)]
    hi = boot_means[int((1 + ci) / 2 * n_boot)]
    return round(lo, 4), round(hi, 4)


def safe_wilcoxon(a, b, alternative="greater"):
    try:
        stat, p = wilcoxon(a, b, alternative=alternative)
        return {"stat": round(float(stat), 4), "p": round(float(p), 6)}
    except ValueError as e:
        return {"stat": 0.0, "p": 1.0, "note": str(e)}


def main():
    print(f"=== HONEST BENCHMARK: N={N}, model={MODEL} ===")
    print(f"Seeds: 0 to {N-1}\n")

    results = []

    for grammar_idx in range(N):
        seed = grammar_idx  # seeds 0-49 as specified
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
            ("tot_llm",     run_tot_llm,      [], {"model": MODEL}),
        ]

        for method_name, solver_fn, extra_args, extra_kwargs in solvers:
            print(f"  [{method_name}] running...", flush=True)
            t0 = time.time()
            try:
                args = [
                    grammar["initial_state"],
                    grammar["target"],
                    grammar["rules"],
                    grammar["constraints"],
                ] + extra_args
                result = run_with_timeout(solver_fn, args, extra_kwargs, TIMEOUT)
            except concurrent.futures.TimeoutError:
                print(f"  [{method_name}] TIMEOUT after {TIMEOUT}s")
                result = {
                    "path": [],
                    "score": 0.0,
                    "final_state": grammar["initial_state"],
                    "timed_out": True,
                    "states_explored": -1,
                }
            except Exception as e:
                print(f"  [{method_name}] ERROR: {e}")
                result = {
                    "path": [],
                    "score": 0.0,
                    "final_state": grammar["initial_state"],
                    "timed_out": False,
                    "states_explored": -1,
                }
            wall_time = time.time() - t0

            grammar_result[method_name] = {
                "score": result.get("score", 0.0),
                "solved": result.get("score", 0.0) > 0.0,
                "path_len": len(result.get("path", [])),
                "path": result.get("path", []),
                "wall_time": round(wall_time, 3),
                "states_explored": result.get("states_explored", -1),
                "timed_out": result.get("timed_out", False),
            }
            print(
                f"  [{method_name}] score={grammar_result[method_name]['score']:.4f} "
                f"solved={grammar_result[method_name]['solved']} "
                f"states={grammar_result[method_name]['states_explored']} "
                f"time={wall_time:.1f}s"
            )

        r = grammar_result
        print(
            f"  SUMMARY: BFS={r['bfs']['score']:.3f} | "
            f"RandBeam={r['random_beam']['score']:.3f} | "
            f"ToT={r['tot_llm']['score']:.3f}"
        )
        results.append(grammar_result)

        # Checkpoint after every grammar
        checkpoint = {
            "status": "in_progress",
            "grammar_idx": grammar_idx,
            "n_completed": grammar_idx + 1,
        }
        with open(CHECKPOINT_PATH, "w") as f:
            json.dump(checkpoint, f, indent=2)

    # ---- Aggregate stats ----
    bfs_scores   = [r["bfs"]["score"]        for r in results]
    rand_scores  = [r["random_beam"]["score"] for r in results]
    tot_scores   = [r["tot_llm"]["score"]     for r in results]

    bfs_solved   = [1 if r["bfs"]["solved"]        else 0 for r in results]
    rand_solved  = [1 if r["random_beam"]["solved"] else 0 for r in results]
    tot_solved   = [1 if r["tot_llm"]["solved"]     else 0 for r in results]

    bfs_states   = [r["bfs"]["states_explored"]        for r in results if r["bfs"]["states_explored"] >= 0]
    rand_states  = [r["random_beam"]["states_explored"] for r in results if r["random_beam"]["states_explored"] >= 0]
    tot_states   = [r["tot_llm"]["states_explored"]     for r in results if r["tot_llm"]["states_explored"] >= 0]

    def desc(scores, solved_flags, states_list):
        ci_lo, ci_hi = bootstrap_ci(scores)
        return {
            "mean_yield":  round(statistics.mean(scores), 4),
            "std_yield":   round(statistics.stdev(scores), 4) if len(scores) > 1 else 0.0,
            "min_yield":   round(min(scores), 4),
            "max_yield":   round(max(scores), 4),
            "ci_95":       [ci_lo, ci_hi],
            "solve_rate":  round(sum(solved_flags) / len(solved_flags), 4),
            "n_solved":    sum(solved_flags),
            "mean_states": round(statistics.mean(states_list), 1) if states_list else -1,
        }

    stats = {
        "bfs":         desc(bfs_scores,  bfs_solved,  bfs_states),
        "random_beam": desc(rand_scores, rand_solved, rand_states),
        "tot_llm":     desc(tot_scores,  tot_solved,  tot_states),
        "wilcoxon_bfs_vs_tot":      safe_wilcoxon(bfs_scores,  tot_scores,  alternative="greater"),
        "wilcoxon_tot_vs_bfs":      safe_wilcoxon(tot_scores,  bfs_scores,  alternative="greater"),
        "wilcoxon_bfs_vs_rand":     safe_wilcoxon(bfs_scores,  rand_scores, alternative="greater"),
        "wilcoxon_tot_vs_rand":     safe_wilcoxon(tot_scores,  rand_scores, alternative="greater"),
        "wilcoxon_rand_vs_tot":     safe_wilcoxon(rand_scores, tot_scores,  alternative="greater"),
    }

    # ---- Print honest summary ----
    print("\n" + "=" * 65)
    print(f"HONEST BENCHMARK RESULTS (N={N}, model={MODEL})")
    print("=" * 65)
    print(f"{'Method':<15} {'Mean Yield':>12} {'Std':>8} {'Solve%':>8} {'States':>10}")
    print("-" * 55)
    for method, label in [("bfs", "BFS"), ("random_beam", "Random Beam"), ("tot_llm", "ToT+LLM")]:
        s = stats[method]
        print(
            f"{label:<15} {s['mean_yield']:>12.4f} {s['std_yield']:>8.4f} "
            f"{s['solve_rate']*100:>7.1f}% {s['mean_states']:>10.1f}"
        )

    print("\n95% Confidence Intervals (bootstrap):")
    for method, label in [("bfs", "BFS"), ("random_beam", "Random Beam"), ("tot_llm", "ToT+LLM")]:
        s = stats[method]
        print(f"  {label}: [{s['ci_95'][0]:.4f}, {s['ci_95'][1]:.4f}]")

    print("\nWilcoxon signed-rank tests (one-sided):")
    for key, label in [
        ("wilcoxon_bfs_vs_tot",  "BFS > ToT"),
        ("wilcoxon_tot_vs_bfs",  "ToT > BFS"),
        ("wilcoxon_bfs_vs_rand", "BFS > Random"),
        ("wilcoxon_tot_vs_rand", "ToT > Random"),
    ]:
        w = stats[key]
        sig = "***" if w["p"] < 0.001 else ("**" if w["p"] < 0.01 else ("*" if w["p"] < 0.05 else "ns"))
        print(f"  {label}: W={w['stat']:.1f}, p={w['p']:.4f} {sig}")

    # Determine winner
    winner = max([("BFS", stats["bfs"]["mean_yield"]),
                  ("Random Beam", stats["random_beam"]["mean_yield"]),
                  ("ToT+LLM", stats["tot_llm"]["mean_yield"])],
                 key=lambda x: x[1])
    print(f"\nWINNER (mean yield): {winner[0]} ({winner[1]:.4f})")
    print("=" * 65)

    # ---- Save results ----
    output = {
        "meta": {
            "n_grammars": N,
            "seeds": f"0 to {N-1}",
            "model": MODEL,
            "timeout_per_method_s": TIMEOUT,
            "date": datetime.datetime.utcnow().isoformat() + "Z",
            "note": "Honest rerun. Seeds 0-49. No fabrication.",
        },
        "summary": stats,
        "winner": {"method": winner[0], "mean_yield": winner[1]},
        "grammars": results,
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {RESULTS_PATH}")

    # ---- Final checkpoint ----
    final_checkpoint = {
        "status": "completed",
        "started": None,
        "completed": datetime.datetime.utcnow().isoformat() + "Z",
        "evidence": [
            f"N={N} grammars, seeds 0-{N-1}",
            f"model={MODEL}",
            f"bfs_mean={stats['bfs']['mean_yield']}, solve_rate={stats['bfs']['solve_rate']}",
            f"rand_mean={stats['random_beam']['mean_yield']}, solve_rate={stats['random_beam']['solve_rate']}",
            f"tot_mean={stats['tot_llm']['mean_yield']}, solve_rate={stats['tot_llm']['solve_rate']}",
            f"winner={winner[0]}",
            f"wilcoxon_bfs_vs_tot: p={stats['wilcoxon_bfs_vs_tot']['p']}",
            f"wilcoxon_tot_vs_bfs: p={stats['wilcoxon_tot_vs_bfs']['p']}",
            f"results_file={RESULTS_PATH}",
        ],
    }
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(final_checkpoint, f, indent=2)
    print(f"Checkpoint updated at {CHECKPOINT_PATH}")

    return output


if __name__ == "__main__":
    main()
