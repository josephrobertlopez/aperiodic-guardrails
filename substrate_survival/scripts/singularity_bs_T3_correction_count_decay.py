#!/usr/bin/env python3
"""
Singularity-BS-T3: Correction-count decay test on Amanda's correction-open ledger.

Pre-reg: substrate_survival/specs/pre_registered/Singularity-BS-T3_20260530T040946Z.json

Hypothesis: FEP-flavored RSI claim predicts correction-count should DECAY across sessions
(Mann-Kendall negative trend, p<0.05). Stationary or increasing => RSI_FEP_FALSIFIED.

Read-only on /home/joey/.gnosis/. No mocking, no synthetic data.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import statistics
import sys
from pathlib import Path

import numpy as np
import scipy.stats as st

MEMORY_PATH = Path("/home/joey/.gnosis/.memory/memory.jsonl")
PREREG_PATH = Path("substrate_survival/specs/pre_registered/Singularity-BS-T3_20260530T040946Z.json")
RESULTS_PATH = Path("substrate_survival/data/Singularity-BS-T3_correction_count_decay_results.json")
TMP_COPY = Path("/tmp/singularity_bs_T3_results.json")
REPORT_PATH = Path("substrate_survival/data/Singularity-BS-T3_report.md")

EXPERIMENT_ID = "Singularity-BS-T3"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_genesis_timestamp(obs: str) -> str | None:
    """Pull an ISO-ish timestamp out of a GENESIS observation string.

    Supported shapes:
      'GENESIS 2026-05-26 01:32 UTC: Migrated...'
      'GENESIS 2026-05-24: Migrated...'
      'GENESIS 2026-05-24 22:49: Migrated...'
    """
    if not obs.startswith("GENESIS"):
        return None
    # try date+time
    m = re.match(r"GENESIS\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})(?:\s+UTC)?", obs)
    if m:
        d, t = m.group(1), m.group(2)
        return f"{d}T{t}:00Z"
    m = re.match(r"GENESIS\s+(\d{4}-\d{2}-\d{2})", obs)
    if m:
        return f"{m.group(1)}T00:00:00Z"
    return None


def parse_predecessor_count(obs: str) -> int | None:
    """Pull predecessor 'substantive obs' count out of GENESIS observation.

    Example fragments:
      'Migrated from amanda.Correction.open.v3 (11 substantive obs / ...)'
      'Migrated from amanda.Correction.open (77 obs / ...)'
      'Migrated from amanda.Correction.open.v7 (10 substantive obs / 27071B ...)'
    """
    # Prefer 'N substantive obs'
    m = re.search(r"\((\d+)\s+substantive\s+obs", obs)
    if m:
        return int(m.group(1))
    # Fallback: 'N obs /' just after the entity name (genesis-of-genesis case)
    m = re.search(r"Migrated from amanda\.Correction\.open(?:\.v\d+)?\s*\((\d+)\s+obs", obs)
    if m:
        return int(m.group(1))
    return None


def load_correction_entities(memory_path: Path) -> dict[int, dict]:
    """Return {version_int: raw_entity_dict} for amanda.Correction.open.v*."""
    out: dict[int, dict] = {}
    with open(memory_path) as f:
        for ln in f:
            try:
                rec = json.loads(ln)
            except json.JSONDecodeError:
                continue
            nm = rec.get("name") or ""
            m = re.match(r"amanda\.Correction\.open\.v(\d+)$", nm)
            if m:
                v = int(m.group(1))
                # If duplicate (entity merge artifacts), keep the last (most-current) one
                out[v] = rec
    return out


def mann_kendall(y: list[float]) -> dict:
    """Two-sided Mann-Kendall trend test, pure-python.

    Returns S, var_S, z, p_two_sided, tau.
    """
    n = len(y)
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            s += np.sign(y[j] - y[i])
    # tie correction
    _, counts = np.unique(y, return_counts=True)
    tie_term = sum(t * (t - 1) * (2 * t + 5) for t in counts if t > 1)
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0
    if s > 0:
        z = (s - 1) / np.sqrt(var_s) if var_s > 0 else 0.0
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s) if var_s > 0 else 0.0
    else:
        z = 0.0
    p_two = 2 * (1 - st.norm.cdf(abs(z)))
    # Kendall tau on (index, y)
    tau, p_tau = st.kendalltau(list(range(n)), y)
    return {
        "S": float(s),
        "var_S": float(var_s),
        "z": float(z),
        "p_two_sided_normal_approx": float(p_two),
        "tau": float(tau),
        "p_kendalltau_scipy": float(p_tau),
    }


def lag1_autocorr(y: list[float]) -> float:
    if len(y) < 2:
        return float("nan")
    a = np.asarray(y, dtype=float)
    mean = a.mean()
    num = np.sum((a[:-1] - mean) * (a[1:] - mean))
    den = np.sum((a - mean) ** 2)
    return float(num / den) if den > 0 else 0.0


def ols_slope_with_bootstrap(x: list[float], y: list[float], n_boot: int = 5000, seed: int = 20260530) -> dict:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    res = st.linregress(x, y)
    slope = res.slope
    intercept = res.intercept
    r2 = res.rvalue ** 2
    rng = np.random.default_rng(seed)
    slopes = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        # If all same x, slope undefined — skip
        if np.unique(x[idx]).size < 2:
            slopes[b] = np.nan
            continue
        rb = st.linregress(x[idx], y[idx])
        slopes[b] = rb.slope
    valid = slopes[~np.isnan(slopes)]
    if valid.size == 0:
        ci_lo = ci_hi = float("nan")
    else:
        ci_lo, ci_hi = np.percentile(valid, [2.5, 97.5])
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r2),
        "p_value_scipy": float(res.pvalue),
        "bootstrap_n": n_boot,
        "bootstrap_slope_ci95": [float(ci_lo), float(ci_hi)],
        "bootstrap_valid_count": int(valid.size),
    }


def main() -> int:
    if not MEMORY_PATH.exists():
        print(f"ERROR: {MEMORY_PATH} missing", file=sys.stderr)
        return 2

    mem_mtime = dt.datetime.fromtimestamp(MEMORY_PATH.stat().st_mtime, tz=dt.timezone.utc).isoformat()
    mem_sha = sha256_file(MEMORY_PATH)
    mem_size = MEMORY_PATH.stat().st_size

    prereg_mtime = (
        dt.datetime.fromtimestamp(PREREG_PATH.stat().st_mtime, tz=dt.timezone.utc).isoformat()
        if PREREG_PATH.exists()
        else None
    )
    prereg_sha = sha256_file(PREREG_PATH) if PREREG_PATH.exists() else None

    entities = load_correction_entities(MEMORY_PATH)
    versions_sorted = sorted(entities.keys())

    # Build series
    series_rows = []
    for v in versions_sorted:
        ent = entities[v]
        obs_list = ent.get("observations", []) or []
        genesis = obs_list[0] if obs_list else ""
        ts = parse_genesis_timestamp(genesis)
        pred_count = parse_predecessor_count(genesis)
        n_live_obs = len(obs_list)
        series_rows.append(
            {
                "version": v,
                "session_index": versions_sorted.index(v) + 1,
                "genesis_timestamp_utc": ts,
                "predecessor_substantive_obs_count": pred_count,
                "n_live_observations": n_live_obs,
                "genesis_obs_excerpt": genesis[:240],
            }
        )

    # PRIMARY metric: predecessor's substantive-obs count (what triggered rotation).
    # v2's GENESIS reports "Migrated from amanda.Correction.open (77 obs / ...)".
    # That 77 is amanda.Correction.open (v1 / pre-versioned) — included as session 0.
    # v3..v8 GENESIS report n-substantive-obs of v(N-1).
    # The METRIC we want for session N is "correction count present at the END of session N",
    # i.e. count at compaction. So we use predecessor_count of v(N+1) as the metric for v(N).
    # For the most recent version (v8), no successor yet -> use n_live_obs - 2 metadata bullets
    # (GENESIS + INSTALLED-LEDGER) as a lower-bound proxy, BUT explicitly flag this in results.

    primary_series = []
    # Map: session_label -> count
    # Session for v2 = end-count for v2 = predecessor_count reported by v3.GENESIS
    # Session for v3 = predecessor_count reported by v4.GENESIS  ... etc.
    for i, v in enumerate(versions_sorted[:-1]):
        next_v = versions_sorted[i + 1]
        next_ent_obs = entities[next_v].get("observations", []) or []
        if not next_ent_obs:
            continue
        pc = parse_predecessor_count(next_ent_obs[0])
        ts = parse_genesis_timestamp(next_ent_obs[0])  # rotation timestamp = end of v
        if pc is None:
            continue
        primary_series.append(
            {
                "session_version": v,
                "session_index": i + 1,
                "end_correction_count": pc,
                "rotation_timestamp_utc": ts,
                "source": f"GENESIS of v{next_v}",
            }
        )

    # Add the current (live) tail with a CLEAR caveat: it is in-progress, not a rotation event.
    # We will report it but EXCLUDE from the primary trend test (only completed sessions count).
    last_v = versions_sorted[-1]
    last_obs = entities[last_v].get("observations", []) or []
    live_substantive = max(0, len(last_obs) - 2)  # rough: minus GENESIS + INSTALLED-LEDGER tails
    live_row = {
        "session_version": last_v,
        "session_index": versions_sorted.index(last_v) + 1,
        "end_correction_count_lower_bound_proxy": live_substantive,
        "in_progress": True,
        "source": "live entity (no successor yet) — EXCLUDED from primary test",
    }

    # F1: extractable session history
    f1_pass = len(primary_series) >= 5
    # F2: each session has a count
    f2_pass = all(isinstance(r["end_correction_count"], int) for r in primary_series)

    falsifiers = {
        "F1_session_history_extractable": {
            "pass": f1_pass,
            "n_completed_sessions": len(primary_series),
            "threshold": 5,
        },
        "F2_correction_count_definable": {
            "pass": f2_pass,
            "metric": "predecessor_substantive_obs_count at rotation",
        },
    }

    if not (f1_pass and f2_pass):
        verdict = "HARNESS_INVALID"
        f3 = f4 = f5 = None
    else:
        x = [r["session_index"] for r in primary_series]
        y = [r["end_correction_count"] for r in primary_series]
        mk = mann_kendall(y)
        lag1 = lag1_autocorr(y)
        ols = ols_slope_with_bootstrap(x, y)

        # F3 decision: significant negative trend means decay
        p = mk["p_kendalltau_scipy"]
        tau = mk["tau"]
        sig_neg = (tau < 0) and (p < 0.05)
        sig_pos = (tau > 0) and (p < 0.05)

        falsifiers["F3_singularity_bs_test"] = {
            "pass_means_decay_detected": sig_neg,
            "mann_kendall": mk,
            "interpretation": (
                "significant_negative_trend"
                if sig_neg
                else ("significant_positive_trend" if sig_pos else "no_significant_trend")
            ),
        }
        falsifiers["F4_serial_independence_check"] = {
            "lag1_autocorrelation": lag1,
            "flag_suspect_iff_abs_gt_0.7": abs(lag1) > 0.7,
        }
        falsifiers["F5_robustness"] = ols
        f3 = falsifiers["F3_singularity_bs_test"]
        f4 = falsifiers["F4_serial_independence_check"]
        f5 = falsifiers["F5_robustness"]

        if sig_neg:
            verdict = "RSI_FEP_NOT_FALSIFIED"
        elif 0.05 <= p < 0.10 and tau < 0:
            verdict = "INDETERMINATE"
        else:
            verdict = "RSI_FEP_FALSIFIED"

    result = {
        "experiment_id": EXPERIMENT_ID,
        "run_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "preregistration": {
            "path": str(PREREG_PATH),
            "mtime_utc": prereg_mtime,
            "sha256": prereg_sha,
        },
        "input": {
            "path": str(MEMORY_PATH),
            "mtime_utc": mem_mtime,
            "size_bytes": mem_size,
            "sha256": mem_sha,
        },
        "session_definition": "amanda.Correction.open.v<N> rotation events; session_index in chronological order of N",
        "correction_count_metric": "predecessor_substantive_obs_count at rotation (extracted from successor's GENESIS observation)",
        "raw_entity_summary": series_rows,
        "primary_series_completed_sessions": primary_series,
        "live_tail_excluded": live_row,
        "falsifier_predicates": falsifiers,
        "verdict": verdict,
        "verdict_rule": "RSI_FEP_NOT_FALSIFIED iff Mann-Kendall tau<0 AND p<0.05. Else RSI_FEP_FALSIFIED (default brutal-honesty), or INDETERMINATE if 0.05<=p<0.10 with tau<0.",
        "notes": [
            "v2 GENESIS reports '77 obs' from a pre-versioned amanda.Correction.open ancestor. We do NOT include that as a session-end count because (a) it is not a v->v rotation, (b) the 77 includes RESOLVED-LEDGER bullets not just open rails. The v2->v3 rotation (8 substantive obs) is the first clean session-end count.",
            "Live v8 tail excluded from trend test because no rotation event has occurred; its current load is in-progress.",
            "The substrate is forced to compact at correction-obs>10 watchdog threshold, so end_counts are bounded above by ~11. This censors the upper tail of any real RSI growth signal. A null/no-trend result under this ceiling cannot distinguish 'no improvement' from 'watchdog-saturated'; we report this as a known limitation but it does NOT rescue the RSI claim — the burden of proof is on showing strictly-below-ceiling decay.",
        ],
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(result, f, indent=2, default=str)
    shutil.copyfile(RESULTS_PATH, TMP_COPY)

    # Brief markdown report
    md_lines = [
        f"# {EXPERIMENT_ID} — Correction-Count Decay Test",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        "## Series (completed sessions)",
        "",
        "| session | version | rotation_ts | end_correction_count |",
        "|--------:|--------:|:------------|---------------------:|",
    ]
    for r in primary_series:
        md_lines.append(
            f"| {r['session_index']} | v{r['session_version']} | {r['rotation_timestamp_utc']} | {r['end_correction_count']} |"
        )
    md_lines += [
        "",
        f"Live tail (excluded): v{last_v}, lower-bound substantive ~ {live_substantive}",
        "",
    ]
    if verdict != "HARNESS_INVALID":
        md_lines += [
            "## Statistics",
            "",
            f"- Mann-Kendall tau = `{mk['tau']:.4f}`  (scipy kendalltau)",
            f"- p (two-sided) = `{mk['p_kendalltau_scipy']:.4f}`",
            f"- Normal-approx z = `{mk['z']:.4f}`, p = `{mk['p_two_sided_normal_approx']:.4f}`",
            f"- OLS slope = `{ols['slope']:.4f}` (per session), R^2 = `{ols['r_squared']:.4f}`",
            f"- Bootstrap 95% CI on slope = `[{ols['bootstrap_slope_ci95'][0]:.4f}, {ols['bootstrap_slope_ci95'][1]:.4f}]`",
            f"- Lag-1 autocorrelation = `{lag1:.4f}` (flag if |r|>0.7: {'YES' if abs(lag1)>0.7 else 'no'})",
            "",
            "## Reading",
            "",
            f"With N={len(primary_series)} completed sessions, the burden of proof on the RSI/FEP-decay claim is "
            "a Mann-Kendall tau strictly < 0 at p<0.05. ",
            f"The observed tau={mk['tau']:.3f}, p={mk['p_kendalltau_scipy']:.3f}. ",
            (
                "This **satisfies** the decay falsifier (RSI/FEP claim not falsified by this test)."
                if (mk["tau"] < 0 and mk["p_kendalltau_scipy"] < 0.05)
                else (
                    "This does **not** clear the decay bar; under brutal-honesty default, RSI/FEP claim is **falsified** "
                    "by this test on this metric."
                )
            ),
            "",
            "## Caveat",
            "",
            "End-counts are bounded above by ~11 because the substrate compacts at correction-obs>10 watchdog. ",
            "This caps any 'growth' signal at the ceiling. A flat/no-trend result is consistent with both 'no improvement' and 'watchdog-saturated load'. Under brutal-honesty default the burden is on the RSI claim to show strictly-below-ceiling decay; absence of decay = falsified, not 'inconclusive'.",
        ]
    else:
        md_lines += [
            "## HARNESS_INVALID",
            "",
            f"F1 sessions extractable: {f1_pass}, F2 counts definable: {f2_pass}.",
            "Cannot run trend test; report INDETERMINATE/HARNESS_INVALID and stop.",
        ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(md_lines) + "\n")

    # Print summary to stdout
    print(json.dumps(
        {
            "verdict": verdict,
            "n_completed_sessions": len(primary_series),
            "tau": mk["tau"] if verdict != "HARNESS_INVALID" else None,
            "p": mk["p_kendalltau_scipy"] if verdict != "HARNESS_INVALID" else None,
            "results_path": str(RESULTS_PATH),
            "tmp_copy": str(TMP_COPY),
            "report_path": str(REPORT_PATH),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
