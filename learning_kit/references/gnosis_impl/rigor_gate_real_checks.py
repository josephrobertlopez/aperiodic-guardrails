#!/usr/bin/env python3
"""rigor-gate checks. Reads results JSON + draft verdict text; returns per-check
PASS/BLOCK + final SHIP/HOLD. Fail-closed on any uncheckable condition.

Usage:
    python3 checks.py --results PATH [--results PATH ...] --verdict "TEXT"

Output (stdout):
    PRE-REGISTRATION : PASS|BLOCK — reason
    SMALL-N POWER    : PASS|BLOCK — reason
    CONFOUND         : PASS|BLOCK — reason
    THRESHOLD/NOISE  : PASS|BLOCK — reason
    LABEL INTEGRITY  : PASS|BLOCK — reason
    DECORATION       : PASS|BLOCK — reason
    ---
    VERDICT: SHIP | HOLD (blocking: 1,2,...)

Exit code: 0 on SHIP, 1 on HOLD.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


# ---------- helpers ----------

POSITIVE_VERDICT_TOKENS = (
    "CONFIRMED", "SUPPORT", "STRONG", "TELEPROMPTER_LIKELY", "TELEPROMPTER",
    "PORTABLE", "RESISTANT", "STABLE", "ROBUST", "HOLDS", "PROVEN",
    "FUNCTOR", "VALIDATED",
)
NEGATIVE_VERDICT_TOKENS = (
    "RULED OUT", "RULED_OUT", "REJECTED", "FALSIFIED", "FAILED",
    "INDETERMINATE", "LEXICAL", "MIXED", "REVISED", "WALK-BACK",
    "LLM-SPECIFIC", "TAUTOLOGY", "NEEDS HEDGING",
)
DECORATION_TOKENS = (
    r"\bfunctor\b", r"\bmorphism\b", r"\bcategory[- ]theoretic\b",
    r"\bcategorical\b", r"\blaw\b", r"\btheorem\b", r"\binvariant\b",
)
PRE_REG_KEYS = ("pre_registered_rule", "pre_registered_rule_on_NORMALIZED_deltas",
                "pre_registered_rule_on_RAW_delta_of_condition_B",
                "decision_rule", "pre_reg", "pre_registered")
SIG_KEYS = ("fisher_p", "bootstrap_ci", "p_value", "ci_95",
            "significance", "fisher_exact")
CONFOUND_KEYS = ("null_test", "confound_test", "mechanism_check",
                 "null_result", "confound", "mechanism")
PREDICTION_KEYS = ("prediction", "theory_predicts", "predicted",
                   "predictions", "theoretical_prediction")


def load_results(paths: list[str]) -> list[tuple[str, dict[str, Any]]]:
    out = []
    for p in paths:
        if p == "MULTI":
            continue
        try:
            with open(p) as f:
                out.append((p, json.load(f)))
        except (OSError, json.JSONDecodeError) as e:
            out.append((p, {"_load_error": str(e)}))
    return out


def has_any_key(d: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for k in d:
        for needle in keys:
            if needle.lower() in k.lower():
                return k
    return None


def get_n_per_cell(d: dict[str, Any]) -> int | None:
    """Best-effort extraction of per-cell N."""
    # Common explicit fields
    for key in ("n_per_cell", "n_trials", "N", "n"):
        if key in d and isinstance(d[key], int):
            return d[key]
    # Inspect nested condition objects
    n_vals = []
    for v in d.values():
        if isinstance(v, dict):
            for nk in ("n_trials", "n_valid_trials", "n_per_cell", "N"):
                if nk in v and isinstance(v[nk], int):
                    n_vals.append(v[nk])
    if n_vals:
        return min(n_vals)
    return None


def collect_numeric_samples(d: dict[str, Any]) -> list[float]:
    """Walk results JSON and collect per-trial numeric values for variance."""
    samples: list[float] = []

    def walk(node: Any, key_hint: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, k.lower())
        elif isinstance(node, list):
            for item in node:
                walk(item, key_hint)
        elif isinstance(node, (int, float)):
            # Heuristic: collect "delta_pp", "retention_pct", "p_refuse" etc.
            if any(t in key_hint for t in ("delta_pp", "retention_pct",
                                            "p_refuse", "normalized_delta",
                                            "mean_delta")):
                if not math.isnan(float(node)):
                    samples.append(float(node))

    walk(d)
    return samples


def stddev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def is_positive_verdict(text: str) -> bool:
    upper = text.upper()
    # negatives take precedence: "RULED OUT" trumps "SUPPORT" in same string
    if any(tok in upper for tok in NEGATIVE_VERDICT_TOKENS):
        return False
    return any(tok in upper for tok in POSITIVE_VERDICT_TOKENS)


# ---------- six checks ----------

def check_prereg(results: list[tuple[str, dict]]) -> tuple[bool, str]:
    if not results:
        return False, "no results JSON parsed"
    for path, d in results:
        if "_load_error" in d:
            return False, f"{Path(path).name}: failed to load ({d['_load_error']})"
        key = has_any_key(d, PRE_REG_KEYS)
        if not key:
            return False, f"{Path(path).name}: no pre_registered_rule key"
        val = d[key]
        if val is None or (isinstance(val, (str, dict, list)) and len(val) == 0):
            return False, f"{Path(path).name}: pre_registered_rule is empty"
    return True, "pre_registered_rule key present and non-empty in all results"


def check_small_n(results: list[tuple[str, dict]], verdict: str) -> tuple[bool, str]:
    if not is_positive_verdict(verdict):
        return True, "verdict is not positive; small-N power check not required"
    for path, d in results:
        if "_load_error" in d:
            return False, f"{Path(path).name}: load failed"
        n = get_n_per_cell(d)
        if n is None:
            return False, f"{Path(path).name}: cannot determine N per cell"
        if n < 20:
            sig_key = has_any_key(d, SIG_KEYS)
            if not sig_key:
                return False, (f"{Path(path).name}: N={n}<20 with positive "
                                f"verdict; no significance test field")
            sig_val = d[sig_key]
            # Try to extract a numeric p
            p_val = None
            if isinstance(sig_val, (int, float)):
                p_val = float(sig_val)
            elif isinstance(sig_val, str):
                m = re.search(r"[\d.]+", sig_val)
                if m:
                    try:
                        p_val = float(m.group())
                    except ValueError:
                        pass
            if p_val is not None and p_val > 0.05:
                return False, (f"{Path(path).name}: N={n}, {sig_key}={p_val} "
                                f">0.05 but verdict positive")
    return True, "N>=20 or significance test supports verdict"


def check_confound(results: list[tuple[str, dict]], verdict: str) -> tuple[bool, str]:
    for path, d in results:
        if "_load_error" in d:
            return False, f"{Path(path).name}: load failed"
        key = has_any_key(d, CONFOUND_KEYS)
        if not key:
            return False, (f"{Path(path).name}: no null_test / confound_test / "
                            f"mechanism_check field")
    return True, "confound/null check documented in all results"


def check_threshold_noise(results: list[tuple[str, dict]], verdict: str) -> tuple[bool, str]:
    # Extract numeric threshold from verdict text
    threshold_match = re.search(
        r"(?:<=?|>=?|≤|≥)\s*([+-]?\d+(?:\.\d+)?)\s*(pp|%)?",
        verdict
    )
    if not threshold_match:
        return True, "verdict does not cite a numeric threshold"

    threshold = float(threshold_match.group(1))

    # Extract result value from verdict (look for "mean delta +4.90pp" etc.)
    result_match = re.search(
        r"([+-]?\d+(?:\.\d+)?)\s*(?:pp|%)",
        verdict
    )
    if not result_match:
        return False, f"verdict cites threshold {threshold} but no result value parseable"

    result_val = float(result_match.group(1))
    delta_to_threshold = abs(result_val - threshold)

    # Compute variance from samples across all results
    all_samples: list[float] = []
    for _, d in results:
        if isinstance(d, dict):
            all_samples.extend(collect_numeric_samples(d))

    if len(all_samples) < 3:
        return False, (f"threshold cited ({threshold}) but insufficient samples "
                        f"to compute noise floor ({len(all_samples)} samples)")

    sd = stddev(all_samples)
    if delta_to_threshold < sd:
        return False, (f"|result-threshold|={delta_to_threshold:.2f} < "
                        f"sd={sd:.2f}; decision band finer than noise")
    return True, (f"|result-threshold|={delta_to_threshold:.2f} >= "
                  f"sd={sd:.2f}; threshold survives noise floor")


def check_label_integrity(results: list[tuple[str, dict]], verdict: str) -> tuple[bool, str]:
    verdict_positive = is_positive_verdict(verdict)
    upper = verdict.upper()
    for path, d in results:
        if "_load_error" in d:
            return False, f"{Path(path).name}: load failed"
        json_verdict = d.get("verdict", "")
        if not json_verdict:
            return False, f"{Path(path).name}: no verdict field in JSON"

        json_positive = is_positive_verdict(json_verdict)

        # Mismatch: headline positive, JSON negative (or vice versa)
        if verdict_positive != json_positive:
            return False, (f"{Path(path).name}: headline positivity="
                            f"{verdict_positive} but JSON verdict positivity="
                            f"{json_positive} (json='{json_verdict[:80]}')")

        # H2 specific: catch "STRONG SUPPORT" headline while JSON says
        # "REVISED" / "LLM-SPECIFIC" / "RULED OUT"
        if "STRONG SUPPORT" in upper or "STRONG_SUPPORT" in upper:
            negative_in_json = any(tok in json_verdict.upper()
                                    for tok in NEGATIVE_VERDICT_TOKENS)
            if negative_in_json:
                return False, (f"{Path(path).name}: headline claims STRONG "
                                f"SUPPORT but JSON verdict has negative token "
                                f"('{json_verdict[:80]}')")
    return True, "headline polarity matches JSON verdict polarity"


def check_decoration(results: list[tuple[str, dict]], verdict: str) -> tuple[bool, str]:
    deco_hits = [t for t in DECORATION_TOKENS if re.search(t, verdict, re.I)]
    if not deco_hits:
        return True, "no theoretical-frame decoration in verdict"

    for path, d in results:
        if "_load_error" in d:
            return False, f"{Path(path).name}: load failed"
        key = has_any_key(d, PREDICTION_KEYS)
        if not key:
            return False, (f"{Path(path).name}: verdict uses {deco_hits} "
                            f"but JSON has no prediction/theory_predicts field")
    return True, f"theoretical frame {deco_hits} backed by prediction field"


# ---------- driver ----------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", action="append", required=True,
                    help="path to results JSON; may be repeated")
    ap.add_argument("--verdict", required=True,
                    help="draft headline / verdict text")
    args = ap.parse_args()

    results = load_results(args.results)
    if not results:
        print("PRE-REGISTRATION : BLOCK — no results JSON provided")
        print("SMALL-N POWER    : BLOCK — no results JSON")
        print("CONFOUND         : BLOCK — no results JSON")
        print("THRESHOLD/NOISE  : BLOCK — no results JSON")
        print("LABEL INTEGRITY  : BLOCK — no results JSON")
        print("DECORATION       : BLOCK — no results JSON")
        print("---")
        print("VERDICT: HOLD (blocking: 1,2,3,4,5,6)")
        return 1

    checks = [
        ("PRE-REGISTRATION", check_prereg(results)),
        ("SMALL-N POWER   ", check_small_n(results, args.verdict)),
        ("CONFOUND        ", check_confound(results, args.verdict)),
        ("THRESHOLD/NOISE ", check_threshold_noise(results, args.verdict)),
        ("LABEL INTEGRITY ", check_label_integrity(results, args.verdict)),
        ("DECORATION      ", check_decoration(results, args.verdict)),
    ]

    blocking = []
    for i, (name, (passed, reason)) in enumerate(checks, 1):
        status = "PASS" if passed else "BLOCK"
        print(f"{name}: {status} — {reason}")
        if not passed:
            blocking.append(i)

    print("---")
    if blocking:
        print(f"VERDICT: HOLD (blocking: {','.join(str(i) for i in blocking)})")
        return 1
    print("VERDICT: SHIP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
