"""
E21 — Memory decay across compaction depth.
Measures token-set retention between amanda.State versions as a function
of version distance (depth), using the same set-intersection method as E12/E16/E18/E19.
"""

import json
import re
import math
import collections
import datetime
import os

# ── Configuration ──────────────────────────────────────────────────────────────

DATA_SOURCE = "/home/joey/.gnosis/.memory/memory.jsonl"
OUTPUT_PATH = "/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival/data/e21_results.json"

TARGET_VERSIONS = [
    "amanda.State.v8",
    "amanda.State.v9",
    "amanda.State.v10",
    "amanda.State.v11",
    "amanda.State.v12",
    "amanda.State.v13",
    "amanda.State.v14",
]

VERSION_KEYS = ["v8", "v9", "v10", "v11", "v12", "v13", "v14"]

STOPWORDS = {
    "that", "this", "with", "from", "have", "been", "will", "when",
    "they", "them", "their", "there", "then", "than", "what", "which",
    "also", "into", "only", "over", "some", "such", "about", "after",
    "before", "more", "very", "just", "were", "does", "each", "must",
    "should", "would", "could", "shall", "where", "while", "both",
    "through", "during", "under", "again", "further", "once", "here",
    "because", "until", "against", "between", "being", "having",
}

# ── Pre-registration block (written first, before data collection) ─────────────

PRE_REG = {
    "experiment": "E21",
    "hypothesis": (
        "Recall of facts stored in amanda.State degrades as a function of compaction depth "
        "(number of intervening compactions between storage and recall point)."
    ),
    "null_condition": (
        "If retention(depth=1) − retention(depth=6) < 10 percentage points, NULL — no depth effect; "
        "substrate carries facts forward without measurable decay across observed depths."
    ),
    "falsifier": (
        "Retention falls monotonically with depth, with a gap of ≥10pp between adjacent v_n and v_n-6. "
        "Reverse pattern (deeper = more retained) would also falsify the hypothesis as stated."
    ),
    "method": (
        "For each amanda.State version v8–v14, build a fact set by tokenising all observations: "
        "case-fold, keep tokens of length ≥ 4, strip stopwords and pure-punctuation tokens. "
        "retention(v_k, v_{k+d}) = |fact_set(v_k) ∩ fact_set(v_{k+d})| / |fact_set(v_{k+d})|. "
        "Average over all (k, k+d) pairs for d = 1..6. Apply pre-registered null rule."
    ),
    "pre_registration_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
}


def tokenize(observations):
    """Case-fold, split on non-alpha, keep len>=4, drop stopwords and pure-digit tokens."""
    tokens = set()
    for obs in observations:
        words = re.split(r"[^a-zA-Z0-9]+", obs.lower())
        for w in words:
            if len(w) >= 4 and w not in STOPWORDS and not w.isdigit():
                tokens.add(w)
    return tokens


def load_versions():
    """Load observations for all target versions from memory.jsonl."""
    found = {}
    with open(DATA_SOURCE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                name = r.get("name", "")
                if name in TARGET_VERSIONS:
                    found[name] = r.get("observations", [])
            except Exception:
                continue
    return found


def retention(fact_k, fact_kd):
    """Set-intersection retention: |A ∩ B| / |B|."""
    if not fact_kd:
        return None
    return len(fact_k & fact_kd) / len(fact_kd)


def main():
    # Write pre-registration block immediately
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result = dict(PRE_REG)

    # Load data
    raw = load_versions()
    versions_used = []
    fact_sets = {}
    missing = []

    for key, full_name in zip(VERSION_KEYS, TARGET_VERSIONS):
        if full_name in raw:
            versions_used.append(key)
            fact_sets[key] = tokenize(raw[full_name])
        else:
            missing.append(key)

    result["versions_used"] = versions_used
    result["versions_missing"] = missing
    result["fact_set_sizes"] = {k: len(v) for k, v in fact_sets.items()}

    if missing:
        result["verdict"] = "INDETERMINATE"
        result["verdict_reasoning"] = (
            f"Versions missing from data source: {missing}. "
            "Cannot compute full depth range without all seven anchor points."
        )
        with open(OUTPUT_PATH, "w") as f:
            json.dump(result, f, indent=2)
        print(f"INDETERMINATE — missing versions: {missing}")
        return

    # Compute retention by depth
    retention_by_depth = {}
    retention_mean_by_depth = {}

    for d in range(1, 7):
        pairs = []
        for i, vk in enumerate(VERSION_KEYS):
            j = i + d
            if j < len(VERSION_KEYS):
                vkd = VERSION_KEYS[j]
                r = retention(fact_sets[vk], fact_sets[vkd])
                if r is not None:
                    pairs.append({
                        "from": vk,
                        "to": vkd,
                        "retention": round(r, 6)
                    })
        retention_by_depth[f"d{d}"] = pairs
        if pairs:
            mean_val = sum(p["retention"] for p in pairs) / len(pairs)
            retention_mean_by_depth[f"d{d}"] = round(mean_val, 6)
        else:
            retention_mean_by_depth[f"d{d}"] = None

    result["retention_by_depth"] = retention_by_depth
    result["retention_mean_by_depth"] = retention_mean_by_depth

    # Apply pre-registered decision rule
    r_d1 = retention_mean_by_depth.get("d1")
    r_d6 = retention_mean_by_depth.get("d6")

    if r_d1 is None or r_d6 is None:
        gap = None
        verdict = "INDETERMINATE"
        reasoning = "Could not compute d1 or d6 mean — insufficient version pairs."
    else:
        gap = round((r_d1 - r_d6) * 100, 4)  # in percentage points
        if gap < 10.0:
            verdict = "NULL"
            reasoning = (
                f"The mean retention at depth-1 is {r_d1*100:.2f}pp and at depth-6 is {r_d6*100:.2f}pp, "
                f"a difference of {gap:.2f}pp. This falls below the pre-registered 10pp threshold. "
                "The substrate carries token-level fact content forward across six compaction depths "
                "without a measurable decay gradient under this measure."
            )
        else:
            # Check monotonicity
            means = [retention_mean_by_depth.get(f"d{d}") for d in range(1, 7)]
            monotone_decrease = all(
                means[i] is None or means[i+1] is None or means[i] >= means[i+1]
                for i in range(len(means)-1)
            )
            verdict = "NON-NULL"
            mono_str = "monotonically decreasing" if monotone_decrease else "non-monotonically distributed"
            reasoning = (
                f"The mean retention at depth-1 is {r_d1*100:.2f}pp and at depth-6 is {r_d6*100:.2f}pp, "
                f"a difference of {gap:.2f}pp, exceeding the 10pp threshold. "
                f"Retention across depths d1–d6 is {mono_str}. "
                "A depth-dependent retention gradient is present in the token-set intersection measure."
            )

    result["depth_gap_d1_minus_d6"] = gap
    result["verdict"] = verdict
    result["verdict_reasoning"] = reasoning

    # Print summary to stdout
    print(f"\nE21 Summary")
    print(f"  Versions used: {versions_used}")
    print(f"  Fact set sizes: {result['fact_set_sizes']}")
    print(f"  Retention means by depth:")
    for d in range(1, 7):
        key = f"d{d}"
        val = retention_mean_by_depth.get(key)
        pairs = retention_by_depth.get(key, [])
        pair_strs = ", ".join(f"{p['from']}→{p['to']}={p['retention']:.4f}" for p in pairs)
        print(f"    d={d}: mean={val} [{pair_strs}]")
    print(f"  d1 - d6 gap: {gap} pp")
    print(f"  Verdict: {verdict}")
    print(f"  Reasoning: {reasoning}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
