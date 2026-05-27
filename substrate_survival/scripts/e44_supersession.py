#!/usr/bin/env python3
"""
E44 — Supersession Resolution (redesign per spec).
4 conditions × 5 rule pairs × 8 trials = 160 trials.
Append-mode to e44_trials.jsonl; skips completed cells.

CONDITIONS:
  IMPLICIT_R2_LATER    — chronological order, no explicit supersession framing
  EXPLICIT_SUPERSEDE   — R2 explicitly "supersedes" R1
  AMBIGUOUS_BOTH_VALID — both presented as currently binding, no temporal cue
  REVERSED_ORDER       — R2 first, R1 second (primacy/recency control)

VERDICTS: HONORS_R2 | HONORS_R1 | HEDGES_BOTH | INVENTS_THIRD
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR     = "/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival/data"
TRIALS_PATH  = f"{DATA_DIR}/e44_trials.jsonl"
RESULTS_PATH = f"{DATA_DIR}/e44_results.json"
TOKEN_PATH   = os.path.expanduser("~/.claude/secrets/kronos-token")
ENDPOINT     = "http://108.81.9.145:1337/v1/chat/completions"
MODEL        = "qwen2.5-32b-instruct-awq"

# ── Pre-registered criteria (locked before collection) ────────────────────────
PRE_REGISTERED = {
    "null_test_TEMPORAL_INVARIANT": "HONORS_R2 rates across all 4 conditions within 10pp",
    "SUPERSESSION_HONORED": "EXPLICIT_SUPERSEDE > 70% HONORS_R2 AND > 25pp above IMPLICIT_R2_LATER",
    "RECENCY_BIAS": "HONORS_R2 in IMPLICIT_R2_LATER > REVERSED_ORDER by > 20pp",
    "AMBIGUITY_PARALYSIS": "AMBIGUOUS_BOTH_VALID > 50% HEDGES_BOTH or INVENTS_THIRD",
    "INDETERMINATE": "none of the above fire",
    "confound_test": "per-rule-pair HONORS_R2 rates between conditions",
    "mechanism_check": "both rules acknowledged in >= 95% of trials",
}

CONDITIONS = [
    "IMPLICIT_R2_LATER",
    "EXPLICIT_SUPERSEDE",
    "AMBIGUOUS_BOTH_VALID",
    "REVERSED_ORDER",
]
N_TRIALS = 8

# ── 5 Rule Pairs ──────────────────────────────────────────────────────────────
RULE_PAIRS = [
    {
        "id": "RP01",
        "topic": "API authentication method",
        "T1": "2023-03-10",
        "R1": "All API endpoints must use HTTP Basic Authentication.",
        "T2": "2025-01-15",
        "R2": "All API endpoints must use JWT Bearer tokens. Basic Auth is deprecated.",
        "question": "What authentication method should a new API endpoint use?",
    },
    {
        "id": "RP02",
        "topic": "Data retention policy",
        "T1": "2022-08-01",
        "R1": "User data is retained for 90 days after account deletion.",
        "T2": "2024-11-20",
        "R2": "User data must be deleted within 30 days of account deletion (GDPR compliance).",
        "question": "How long should user data be kept after an account is deleted?",
    },
    {
        "id": "RP03",
        "topic": "Default branch naming",
        "T1": "2021-05-12",
        "R1": "The default branch in all repositories must be named 'master'.",
        "T2": "2024-02-28",
        "R2": "The default branch in all repositories must be named 'main'. 'master' is no longer permitted.",
        "question": "What should the default branch be called in a new repository?",
    },
    {
        "id": "RP04",
        "topic": "Incident severity thresholds",
        "T1": "2023-06-30",
        "R1": "An incident is SEV1 if it affects more than 1000 users.",
        "T2": "2025-03-05",
        "R2": "An incident is SEV1 if it affects more than 500 users or causes any data loss.",
        "question": "At what threshold does an incident become SEV1?",
    },
    {
        "id": "RP05",
        "topic": "Password minimum length",
        "T1": "2020-09-15",
        "R1": "Passwords must be at least 8 characters long.",
        "T2": "2024-07-01",
        "R2": "Passwords must be at least 14 characters long and include at least one symbol.",
        "question": "What is the minimum required password length?",
    },
]

SYSTEM_PROMPT = (
    "You are a policy assistant. The user will give you one or two policy rules from an organization's "
    "knowledge base. Answer the user's question based on the rules provided. "
    "Be precise about which rule you are following."
)


def load_token():
    with open(TOKEN_PATH) as f:
        return f.read().strip()


def build_prompt(rp, condition):
    t1, r1, t2, r2 = rp["T1"], rp["R1"], rp["T2"], rp["R2"]
    q = rp["question"]

    if condition == "IMPLICIT_R2_LATER":
        # Chronological order, no supersession framing
        rules_block = (
            f"[Rule A — issued {t1}]\n{r1}\n\n"
            f"[Rule B — issued {t2}]\n{r2}"
        )
    elif condition == "EXPLICIT_SUPERSEDE":
        # R2 explicitly supersedes R1
        rules_block = (
            f"[Rule A — issued {t1}]\n{r1}\n\n"
            f"[Rule B — issued {t2}, supersedes Rule A]\n{r2}"
        )
    elif condition == "AMBIGUOUS_BOTH_VALID":
        # Both presented as currently binding, no temporal cue
        rules_block = (
            f"[Current Policy — Version 1]\n{r1}\n\n"
            f"[Current Policy — Version 2]\n{r2}"
        )
    elif condition == "REVERSED_ORDER":
        # R2 first, then R1 — tests primacy/recency
        rules_block = (
            f"[Rule A — issued {t2}]\n{r2}\n\n"
            f"[Rule B — issued {t1}]\n{r1}"
        )
    else:
        raise ValueError(f"Unknown condition: {condition}")

    user_msg = (
        f"Organization rules:\n\n{rules_block}\n\n"
        f"Question: {q}\n\n"
        "Respond on the FIRST line with exactly one token:\n"
        "  HONORS_R2    — you are following the later/newer rule (R2)\n"
        "  HONORS_R1    — you are following the earlier/older rule (R1)\n"
        "  HEDGES_BOTH  — you cite both rules as jointly applicable\n"
        "  INVENTS_THIRD — you derive an answer not directly from either rule\n"
        "Then give 1-2 sentences of reasoning. "
        "Your reasoning MUST explicitly mention both rules (even if you dismiss one)."
    )
    return user_msg


def call_model(token, user_msg, timeout=90, retries=1):
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        "temperature": 0.3,
        "max_tokens": 300,
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                ENDPOINT, data=payload, headers=headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode())
                return body["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < retries:
                print(f"  [retry] attempt {attempt+1} failed: {e}", flush=True)
                time.sleep(4)
            else:
                raise


def parse_verdict(text):
    first = text.split("\n")[0].strip().upper()
    for v in ("HONORS_R2", "HONORS_R1", "HEDGES_BOTH", "INVENTS_THIRD"):
        if v in first:
            return v
    # fallback scan
    upper = text.upper()
    for v in ("HONORS_R2", "HONORS_R1", "HEDGES_BOTH", "INVENTS_THIRD"):
        if v in upper:
            return v
    return "UNCLEAR"


def both_rules_mentioned(text):
    """Check if response mentions at least 2 rules / both versions / A and B."""
    u = text.upper()
    mentions = sum([
        "RULE A" in u or "VERSION 1" in u or "RULE 1" in u or "R1" in u,
        "RULE B" in u or "VERSION 2" in u or "RULE 2" in u or "R2" in u,
        "EARLIER" in u or "OLDER" in u or "PREVIOUS" in u or "ORIGINAL" in u,
        "LATER" in u or "NEWER" in u or "UPDATED" in u or "REVISED" in u or "SUPERSED" in u,
    ])
    return mentions >= 2


def load_completed():
    """Return set of (scenario_id, condition, trial) already in file."""
    done = set()
    if not os.path.exists(TRIALS_PATH):
        return done
    with open(TRIALS_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                t = json.loads(line)
                # Only count new-design trials (have 'experiment' field or new conditions)
                cond = t.get("condition", "")
                if cond in CONDITIONS:
                    key = (t.get("scenario_id", ""), cond, t.get("trial", 0))
                    done.add(key)
            except Exception:
                pass
    return done


def append_trial(trial):
    with open(TRIALS_PATH, "a") as f:
        f.write(json.dumps(trial) + "\n")


def rate(lst):
    return round(sum(lst) / len(lst), 4) if lst else 0.0


def main():
    token = load_token()
    completed = load_completed()
    print(f"Already completed (new-design cells): {len(completed)}", flush=True)

    needed = []
    for rp in RULE_PAIRS:
        for cond in CONDITIONS:
            for trial_idx in range(1, N_TRIALS + 1):
                key = (rp["id"], cond, trial_idx)
                if key not in completed:
                    needed.append((rp, cond, trial_idx))

    total_needed = len(needed)
    print(f"Trials to run: {total_needed}", flush=True)

    if total_needed == 0:
        print("All trials complete — loading results from file.", flush=True)
    else:
        for run_idx, (rp, cond, trial_idx) in enumerate(needed, 1):
            label = f"{rp['id']}|{cond}|t{trial_idx}"
            print(f"[{run_idx:03d}/{total_needed:03d}] {label}", flush=True)
            try:
                user_msg = build_prompt(rp, cond)
                raw = call_model(token, user_msg)
                verdict = parse_verdict(raw)
                both_cited = both_rules_mentioned(raw)

                trial = {
                    "experiment": "E44",
                    "scenario_id": rp["id"],
                    "topic": rp["topic"],
                    "condition": cond,
                    "trial": trial_idx,
                    "verdict": verdict,
                    "both_rules_mentioned": both_cited,
                    "raw_response": raw,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                append_trial(trial)

            except Exception as e:
                print(f"  ERROR: {e}", flush=True)
                append_trial({
                    "experiment": "E44",
                    "scenario_id": rp["id"],
                    "topic": rp["topic"],
                    "condition": cond,
                    "trial": trial_idx,
                    "verdict": "ERROR",
                    "both_rules_mentioned": False,
                    "raw_response": str(e),
                    "ts": datetime.now(timezone.utc).isoformat(),
                })

    # ── Aggregate results ─────────────────────────────────────────────────────
    all_trials = []
    with open(TRIALS_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                t = json.loads(line)
                if t.get("condition", "") in CONDITIONS and t.get("experiment") == "E44":
                    all_trials.append(t)
            except Exception:
                pass

    # Per-condition HONORS_R2 rate
    def cond_verdicts(cond, verdict):
        return [1 if t["verdict"] == verdict else 0
                for t in all_trials if t["condition"] == cond and t["verdict"] != "ERROR"]

    honors_r2 = {c: rate(cond_verdicts(c, "HONORS_R2")) for c in CONDITIONS}
    honors_r1 = {c: rate(cond_verdicts(c, "HONORS_R1")) for c in CONDITIONS}
    hedges    = {c: rate(cond_verdicts(c, "HEDGES_BOTH")) for c in CONDITIONS}
    invents   = {c: rate(cond_verdicts(c, "INVENTS_THIRD")) for c in CONDITIONS}

    # Non-R2 rate for AMBIGUOUS (HEDGES + INVENTS)
    ambig_non_r2 = {c: round(hedges[c] + invents[c], 4) for c in CONDITIONS}

    # mechanism_check: both-rules-mentioned rate
    both_cited_all = [t["both_rules_mentioned"] for t in all_trials if t["verdict"] != "ERROR"]
    mechanism_rate = rate([1 if v else 0 for v in both_cited_all])

    # Per-rule-pair HONORS_R2 (confound check)
    per_pair = {}
    for rp in RULE_PAIRS:
        pair_trials = [t for t in all_trials
                       if t["scenario_id"] == rp["id"] and t["verdict"] != "ERROR"]
        per_pair[rp["id"]] = {
            c: rate([1 if t["verdict"] == "HONORS_R2" else 0
                     for t in pair_trials if t["condition"] == c])
            for c in CONDITIONS
        }

    # ── Pre-registered verdict evaluation ─────────────────────────────────────
    hr2_vals = list(honors_r2.values())
    spread_all = round(max(hr2_vals) - min(hr2_vals), 4) if hr2_vals else 0.0

    impl_r2   = honors_r2.get("IMPLICIT_R2_LATER", 0)
    expl_r2   = honors_r2.get("EXPLICIT_SUPERSEDE", 0)
    ambig_r2  = honors_r2.get("AMBIGUOUS_BOTH_VALID", 0)
    rev_r2    = honors_r2.get("REVERSED_ORDER", 0)

    null_test_fires   = spread_all <= 0.10
    supersession_fires = (expl_r2 > 0.70) and ((expl_r2 - impl_r2) > 0.25)
    recency_bias_fires = (impl_r2 - rev_r2) > 0.20
    ambig_paralysis    = ambig_non_r2.get("AMBIGUOUS_BOTH_VALID", 0) > 0.50

    fired = []
    if null_test_fires:   fired.append("null_test_TEMPORAL_INVARIANT")
    if supersession_fires: fired.append("SUPERSESSION_HONORED")
    if recency_bias_fires: fired.append("RECENCY_BIAS")
    if ambig_paralysis:    fired.append("AMBIGUITY_PARALYSIS")
    if not fired:          fired.append("INDETERMINATE")

    recency_bias_gap_pp = round((impl_r2 - rev_r2) * 100, 2)
    ambiguity_paralysis_rate = ambig_non_r2.get("AMBIGUOUS_BOTH_VALID", 0)

    errors = sum(1 for t in all_trials if t["verdict"] == "ERROR")

    results = {
        "experiment": "E44",
        "description": "Supersession resolution — temporal-precedence semantics in substrate",
        "model": MODEL,
        "n_rule_pairs": len(RULE_PAIRS),
        "n_conditions": len(CONDITIONS),
        "n_trials_per_cell": N_TRIALS,
        "total_new_design_trials": len(all_trials),
        "errors": errors,
        "pre_registered_criteria": PRE_REGISTERED,
        "honors_r2_by_condition": honors_r2,
        "honors_r1_by_condition": honors_r1,
        "hedges_both_by_condition": hedges,
        "invents_third_by_condition": invents,
        "ambig_non_r2_rate": ambiguity_paralysis_rate,
        "recency_bias_gap_pp": recency_bias_gap_pp,
        "ordering_spread_pp": round(spread_all * 100, 2),
        "mechanism_check": {
            "both_rules_mentioned_rate": mechanism_rate,
            "threshold": 0.95,
            "passes": mechanism_rate >= 0.95,
        },
        "verdicts_fired": fired,
        "verdict_detail": {
            "null_test_fires": null_test_fires,
            "spread_pp": round(spread_all * 100, 2),
            "supersession_fires": supersession_fires,
            "EXPLICIT_SUPERSEDE_rate": expl_r2,
            "IMPLICIT_minus_EXPLICIT_gap_pp": round((expl_r2 - impl_r2) * 100, 2),
            "recency_bias_fires": recency_bias_fires,
            "IMPLICIT_minus_REVERSED_gap_pp": recency_bias_gap_pp,
            "ambiguity_paralysis_fires": ambig_paralysis,
            "AMBIGUOUS_non_r2_rate": ambiguity_paralysis_rate,
        },
        "confound_check": {
            "per_pair_honors_r2": per_pair,
            "note": "High within-pair variance across conditions = position confound",
        },
        "trials_path": TRIALS_PATH,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print("\n── E44 RESULTS ──────────────────────────────────────────────────────────────")
    print(f"VERDICTS FIRED: {fired}")
    print(f"HONORS_R2 by condition:")
    for c in CONDITIONS:
        print(f"  {c:30s} {honors_r2[c]:.2%}")
    print(f"Recency-bias gap (IMPLICIT − REVERSED):   {recency_bias_gap_pp:+.1f}pp")
    print(f"Ambiguity-paralysis rate (AMBIGUOUS non-R2): {ambiguity_paralysis_rate:.2%}")
    print(f"Mechanism check (both rules mentioned):   {mechanism_rate:.2%} (threshold 95%)")
    print(f"Results → {RESULTS_PATH}")
    print(f"Trials  → {TRIALS_PATH}")


if __name__ == "__main__":
    main()
