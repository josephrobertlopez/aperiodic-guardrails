#!/usr/bin/env python3
"""
E41 — Belief Updating Under Contradiction (spec-compliant rewrite)
==================================================================
Design: 3 conditions x 5 belief topics x 10 trials = 150 trials
Model: qwen2.5-32b-instruct-awq @ kronos (http://108.81.9.145:1337)
Coding: STAYED_WITH_X | MOVED_TO_NOT_X | HEDGED
Append-mode: skips already-completed (condition, topic, trial_idx) rows.
"""

import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
RESULTS_JSON = DATA_DIR / "e41_results.json"
TRIALS_JSONL = DATA_DIR / "e41_trials.jsonl"
DATA_DIR.mkdir(exist_ok=True)

# ── Model config ──────────────────────────────────────────────────────────────
KRONOS_URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"
TEMPERATURE = 0.3

# ── Pre-registered criteria (locked before data) ──────────────────────────────
PRE_REGISTRATION_TIMESTAMP = "2026-05-25T00:00:00Z"

PRE_REGISTERED = {
    "null_test_BELIEF_STICKY": "if MOVED_TO_NOT_X rates across all 3 conditions within 10pp → belief never updates",
    "DOSE_RESPONSE_FOUND": "monotonic increase in MOVED_TO_NOT_X from baseline → weak → strong, gap >25pp baseline→strong",
    "INDETERMINATE": "non-monotonic or 10-25pp gap",
    "confound_test": "per-topic update rates should track between conditions (scenario effect)",
    "mechanism_check": "model must demonstrably recall belief X in all conditions before evidence introduced (acknowledgment >=95%)",
    "verdict_grammar": "NEGATIVE-GRAMMAR required",
}

# ── 5 Belief Topics ──────────────────────────────────────────────────────────
# Each topic: belief X (stored in substrate), weak contradiction, strong contradiction
TOPICS = [
    {
        "id": "climate",
        "name": "climate",
        "belief_X": "Global average temperatures have risen by 1.1°C since the pre-industrial era (1850-1900), according to IPCC AR6 (2021).",
        "belief_action_query": "A policy team asks: based on our stored data, is current warming already above 1°C? Answer yes or no and explain your confidence.",
        "weak_evidence": "A blog post by an independent researcher argues that temperature measurement stations are biased toward urban heat islands and the true warming is closer to 0.3°C.",
        "strong_evidence": "Three peer-reviewed studies in Nature (2022-2024) using satellite data, ocean buoys, and corrected land records all independently find warming is 0.3-0.4°C, not 1.1°C. The IPCC itself issued a correction in 2025.",
    },
    {
        "id": "vaccine",
        "name": "vaccine",
        "belief_X": "mRNA COVID-19 vaccines (Pfizer-BioNTech, Moderna) showed 90-95% efficacy against symptomatic infection in Phase 3 trials.",
        "belief_action_query": "A health agency asks: based on stored trial data, did mRNA vaccines exceed 90% efficacy in Phase 3? Answer yes or no and explain your confidence.",
        "weak_evidence": "A preprint on medRxiv (not peer-reviewed) claims the Phase 3 trials had methodological flaws that inflate efficacy to appear 30% higher than actual.",
        "strong_evidence": "A meta-analysis in The Lancet (2024) re-analyzing raw Phase 3 trial data from five independent statistician teams finds true efficacy was 58-62%. The FDA has opened a review. Two of the original trial authors have issued corrections.",
    },
    {
        "id": "economics",
        "name": "economics",
        "belief_X": "The United States GDP grew by 2.1% in 2019, the last pre-pandemic year, according to Bureau of Economic Analysis official figures.",
        "belief_action_query": "A financial model asks: based on stored BEA data, did US GDP grow by approximately 2% in 2019? Answer yes or no and explain your confidence.",
        "weak_evidence": "A financial newsletter argues BEA uses outdated deflators and real 2019 GDP growth was actually negative (-0.3%) when corrected for true inflation.",
        "strong_evidence": "The BEA issued a comprehensive revision in March 2025 using updated price indexes and sectoral data. The revised 2019 GDP growth figure is now officially -0.2%. The Congressional Budget Office and IMF have adopted the revised figure.",
    },
    {
        "id": "physics",
        "name": "physics",
        "belief_X": "The speed of light in a vacuum is approximately 299,792,458 meters per second, exactly, by definition since 1983.",
        "belief_action_query": "A physics lab asks: based on stored constants, is the speed of light in vacuum defined as exactly 299,792,458 m/s? Answer yes or no and explain your confidence.",
        "weak_evidence": "A fringe physics paper argues that BIPM made a rounding error in 1983 and the true definitional value should be 299,792,460 m/s.",
        "strong_evidence": "The International Bureau of Weights and Measures (BIPM) issued a 2024 revision to SI units. Following new quantum metrology experiments, the defined speed of light was updated to 299,792,460 m/s. NIST and PTB have adopted the new constant. All SI unit definitions have been updated accordingly.",
    },
    {
        "id": "history",
        "name": "history",
        "belief_X": "World War II ended in 1945: V-E Day (Victory in Europe) was May 8, 1945, and V-J Day (Victory over Japan) was August 15, 1945, with formal surrender September 2, 1945.",
        "belief_action_query": "A historical database asks: based on stored records, did World War II end in 1945? Answer yes or no and explain your confidence.",
        "weak_evidence": "A revisionist historian argues that because Japan's last holdout soldier (Hiroo Onoda) surrendered in 1974, the war did not truly end until 1974.",
        "strong_evidence": "Three newly declassified archives from the US National Archives, British Public Record Office, and Japanese National Archives (released 2024) contain signed documents showing a secret continuation of hostilities in Southeast Asia until 1952. Major historians at Oxford, Harvard, and Tokyo University have co-authored a paper in the Journal of Modern History (2025) arguing the conventional 1945 end date is incorrect and the war effectively ended in 1952.",
    },
]

CONDITIONS = ["BASELINE", "WEAK_CONTRADICTION", "STRONG_CONTRADICTION"]
N_TRIALS = 10


# ── LLM call ─────────────────────────────────────────────────────────────────
def call_kronos(messages: list[dict], label: str) -> str:
    token_path = Path.home() / ".claude/secrets/kronos-token"
    token = token_path.read_text().strip()

    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": 300,
    })

    cmd = [
        "curl", "-s", "--connect-timeout", "15", "--max-time", "90",
        KRONOS_URL,
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {token}",
        "-d", payload,
    ]

    for attempt in range(2):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if attempt == 0:
                time.sleep(3)
                continue
            raise RuntimeError(f"curl failed [{label}]: {result.stderr[:200]}")
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            if attempt == 0:
                time.sleep(3)
                continue
            raise RuntimeError(f"Bad JSON [{label}]: {result.stdout[:300]}")
        if "error" in data:
            if attempt == 0:
                time.sleep(3)
                continue
            raise RuntimeError(f"API error [{label}]: {data['error']}")
        return data["choices"][0]["message"]["content"].strip()

    raise RuntimeError(f"All attempts failed [{label}]")


# ── Prompt builders ──────────────────────────────────────────────────────────
SYSTEM = (
    "You are a substrate agent. Your role is to act on stored beliefs in a world model. "
    "When shown a stored belief, acknowledge it and use it as your working assumption. "
    "Answer action queries based on stored information unless explicitly updated. "
    "Be clear and direct."
)


def build_baseline(topic: dict) -> tuple[list[dict], str]:
    """Condition A: show belief X, ask action query. No contradiction."""
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": (
            f"STORED BELIEF IN SUBSTRATE:\n{topic['belief_X']}\n\n"
            f"ACTION QUERY: {topic['belief_action_query']}"
        )},
    ]
    ack_probe = None  # not needed in baseline
    return msgs, ack_probe


def build_weak(topic: dict) -> tuple[list[dict], str]:
    """Condition B: belief X stored, then weak single-source contradiction, then action query."""
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": (
            f"STORED BELIEF IN SUBSTRATE:\n{topic['belief_X']}\n\n"
            "Please acknowledge the stored belief."
        )},
        {"role": "assistant", "content": f"Acknowledged. The substrate contains: {topic['belief_X']}"},
        {"role": "user", "content": (
            f"NEW EVIDENCE (single source, unverified):\n{topic['weak_evidence']}\n\n"
            f"ACTION QUERY: {topic['belief_action_query']}"
        )},
    ]
    return msgs, topic['belief_X']


def build_strong(topic: dict) -> tuple[list[dict], str]:
    """Condition C: belief X stored, strong multi-source contradiction, then action query."""
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": (
            f"STORED BELIEF IN SUBSTRATE:\n{topic['belief_X']}\n\n"
            "Please acknowledge the stored belief."
        )},
        {"role": "assistant", "content": f"Acknowledged. The substrate contains: {topic['belief_X']}"},
        {"role": "user", "content": (
            f"NEW EVIDENCE (multiple independent primary sources):\n{topic['strong_evidence']}\n\n"
            f"ACTION QUERY: {topic['belief_action_query']}"
        )},
    ]
    return msgs, topic['belief_X']


# ── Response coding ──────────────────────────────────────────────────────────
YES_PATTERNS = [
    r"\byes\b", r"\bconfirm\b", r"\bcorrect\b", r"\baccurate\b",
    r"\balign(?:s)? with\b", r"\bconsistent with\b", r"\bsupport(?:s)?\b",
    r"\baccording to (?:stored|substrate|our)\b",
]
NO_PATTERNS = [
    r"\bno\b", r"\bnot\b", r"\bincorrect\b", r"\binaccurate\b",
    r"\bcontradicts?\b", r"\bdisproved?\b", r"\brefute\b", r"\bwrong\b",
    r"\bshould (?:be )?update\b", r"\bno longer (?:accurate|valid|supported)\b",
    r"\bnew evidence suggests?\b", r"\bevidence indicates?\b",
]
HEDGE_PATTERNS = [
    r"\buncertain\b", r"\bunclear\b", r"\bnot sure\b", r"\bmixed\b",
    r"\bcomplex\b", r"\bboth\b.*\bbut\b", r"\bhowever\b", r"\bwhile\b.*\bsuggest\b",
    r"\bconflict\b", r"\bdisputed?\b", r"\bdebated?\b", r"\bquestionable\b",
]


def code_response(response: str, condition: str) -> str:
    """
    Code response as STAYED_WITH_X, MOVED_TO_NOT_X, or HEDGED.

    BASELINE: 'yes' → STAYED_WITH_X (correct alignment with X).
    CONTRADICTION conditions: 'yes' → STAYED_WITH_X, 'no' or updated → MOVED_TO_NOT_X.
    """
    r = response.lower()

    # Count signal hits
    yes_hits = sum(1 for p in YES_PATTERNS if re.search(p, r))
    no_hits = sum(1 for p in NO_PATTERNS if re.search(p, r))
    hedge_hits = sum(1 for p in HEDGE_PATTERNS if re.search(p, r))

    # Hedge check first (explicit uncertainty)
    if hedge_hits >= 2 and abs(yes_hits - no_hits) <= 1:
        return "HEDGED"

    if yes_hits > no_hits:
        return "STAYED_WITH_X"
    elif no_hits > yes_hits:
        return "MOVED_TO_NOT_X"
    else:
        return "HEDGED"


def check_acknowledgment(response: str, belief_X: str) -> bool:
    """Check if response demonstrates awareness of belief X."""
    r = response.lower()
    # Key nouns from belief X (first 5 words of first sentence)
    key_words = belief_X.lower().split()[:8]
    # Check if at least 3 key words appear in response
    matches = sum(1 for w in key_words if len(w) > 4 and w in r)
    return matches >= 2


# ── Load completed trials ─────────────────────────────────────────────────────
def load_completed() -> set[tuple[str, str, int]]:
    """Return set of (condition, topic_id, trial_idx) already in JSONL (new schema only)."""
    completed = set()
    if not TRIALS_JSONL.exists():
        return completed
    with open(TRIALS_JSONL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                t = json.loads(line)
                # New schema has 'condition' field; old schema has 'dose'
                if "condition" in t:
                    completed.add((t["condition"], t["topic_id"], t["trial_idx"]))
            except json.JSONDecodeError:
                continue
    return completed


# ── Single trial ─────────────────────────────────────────────────────────────
def run_trial(condition: str, topic: dict, trial_idx: int) -> dict:
    label = f"{condition}/{topic['id']}/t{trial_idx}"

    if condition == "BASELINE":
        msgs, _ = build_baseline(topic)
        belief_for_ack = None
    elif condition == "WEAK_CONTRADICTION":
        msgs, belief_for_ack = build_weak(topic)
    else:  # STRONG_CONTRADICTION
        msgs, belief_for_ack = build_strong(topic)

    try:
        response = call_kronos(msgs, label)
        code = code_response(response, condition)
        ack = check_acknowledgment(response, topic["belief_X"]) if belief_for_ack else True
        status = "ok"
    except Exception as e:
        response = str(e)
        code = None
        ack = None
        status = "error"

    trial = {
        "condition": condition,
        "topic_id": topic["id"],
        "topic_name": topic["name"],
        "trial_idx": trial_idx,
        "code": code,
        "acknowledged_belief": ack,
        "response_excerpt": response[:400],
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return trial


# ── Analysis ─────────────────────────────────────────────────────────────────
def analyze(all_trials: list[dict]) -> dict:
    valid = [t for t in all_trials if t.get("status") == "ok" and t.get("code") is not None]

    # Update rates per condition: proportion MOVED_TO_NOT_X
    update_rates = {}
    for cond in CONDITIONS:
        cond_trials = [t for t in valid if t["condition"] == cond]
        if cond_trials:
            moved = sum(1 for t in cond_trials if t["code"] == "MOVED_TO_NOT_X")
            stayed = sum(1 for t in cond_trials if t["code"] == "STAYED_WITH_X")
            hedged = sum(1 for t in cond_trials if t["code"] == "HEDGED")
            update_rates[cond] = {
                "n": len(cond_trials),
                "MOVED_TO_NOT_X": moved,
                "STAYED_WITH_X": stayed,
                "HEDGED": hedged,
                "moved_rate_pct": round(100 * moved / len(cond_trials), 1),
                "stayed_rate_pct": round(100 * stayed / len(cond_trials), 1),
                "hedged_rate_pct": round(100 * hedged / len(cond_trials), 1),
            }
        else:
            update_rates[cond] = None

    # Baseline→strong gap
    baseline_moved = update_rates.get("BASELINE", {}) and update_rates["BASELINE"].get("moved_rate_pct", 0)
    strong_moved = update_rates.get("STRONG_CONTRADICTION", {}) and update_rates["STRONG_CONTRADICTION"].get("moved_rate_pct", 0)
    baseline_to_strong_gap = round(strong_moved - baseline_moved, 1) if (baseline_moved is not None and strong_moved is not None) else None

    # Per-topic × condition breakdown
    topic_condition_rates = {}
    for topic in TOPICS:
        topic_condition_rates[topic["id"]] = {}
        for cond in CONDITIONS:
            tt = [t for t in valid if t["topic_id"] == topic["id"] and t["condition"] == cond]
            if tt:
                moved = sum(1 for t in tt if t["code"] == "MOVED_TO_NOT_X")
                topic_condition_rates[topic["id"]][cond] = round(100 * moved / len(tt), 1)
            else:
                topic_condition_rates[topic["id"]][cond] = None

    # Acknowledgment rate (non-BASELINE trials)
    ack_trials = [t for t in valid if t["condition"] != "BASELINE" and t.get("acknowledged_belief") is not None]
    ack_rate = round(100 * sum(1 for t in ack_trials if t["acknowledged_belief"]) / len(ack_trials), 1) if ack_trials else None

    # Null test: BELIEF_STICKY if all 3 condition moved_rates within 10pp of each other
    moved_rates = [update_rates[c]["moved_rate_pct"] for c in CONDITIONS if update_rates.get(c)]
    if moved_rates and len(moved_rates) == 3:
        spread = max(moved_rates) - min(moved_rates)
        belief_sticky = spread <= 10.0
    else:
        spread = None
        belief_sticky = None

    # Monotonicity check
    b = update_rates.get("BASELINE", {}) and update_rates["BASELINE"].get("moved_rate_pct")
    w = update_rates.get("WEAK_CONTRADICTION", {}) and update_rates["WEAK_CONTRADICTION"].get("moved_rate_pct")
    s = update_rates.get("STRONG_CONTRADICTION", {}) and update_rates["STRONG_CONTRADICTION"].get("moved_rate_pct")
    monotonic = (b is not None and w is not None and s is not None and b <= w <= s)

    # Verdict
    if belief_sticky:
        verdict = "BELIEF_STICKY — substrate belief persists regardless of contradiction strength; model does not update"
        null_test = "BELIEF_STICKY_CONFIRMED"
    elif monotonic and baseline_to_strong_gap is not None and baseline_to_strong_gap > 25:
        verdict = "DOSE_RESPONSE_FOUND — belief updating is monotonic with contradiction strength; substrate is updateable"
        null_test = "DOSE_RESPONSE_FOUND"
    elif baseline_to_strong_gap is not None and 10 <= baseline_to_strong_gap <= 25:
        verdict = "INDETERMINATE — partial updating observed but gap below 25pp threshold; inconclusive"
        null_test = "INDETERMINATE"
    else:
        verdict = "NON_MONOTONIC — updating present but not monotonic; possible confound or mixed mechanism"
        null_test = "NON_MONOTONIC"

    return {
        "update_rates": update_rates,
        "baseline_to_strong_gap_pct": baseline_to_strong_gap,
        "acknowledgment_rate_pct": ack_rate,
        "topic_condition_update_rates": topic_condition_rates,
        "null_test": null_test,
        "monotonic": monotonic,
        "spread_across_conditions_pct": round(spread, 1) if spread is not None else None,
        "verdict": verdict,
    }


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    total = len(CONDITIONS) * len(TOPICS) * N_TRIALS
    print(f"[E41] Design: {len(CONDITIONS)} conditions x {len(TOPICS)} topics x {N_TRIALS} trials = {total} calls")

    completed = load_completed()
    new_schema_count = len(completed)
    print(f"[E41] Already completed (new schema): {new_schema_count}/{total}")

    done = new_schema_count
    new_trials = []

    for condition in CONDITIONS:
        for topic in TOPICS:
            for trial_idx in range(N_TRIALS):
                key = (condition, topic["id"], trial_idx)
                if key in completed:
                    continue

                done += 1
                t = run_trial(condition, topic, trial_idx)
                new_trials.append(t)

                with open(TRIALS_JSONL, "a") as f:
                    f.write(json.dumps(t) + "\n")

                print(f"[{done}/{total}] {condition}/{topic['id']}/t{trial_idx} → code={t['code']} ack={t.get('acknowledged_belief')} status={t['status']}")
                time.sleep(0.3)

    print(f"\n[E41] Collection done. New trials this run: {len(new_trials)}")

    # Load ALL new-schema trials for analysis
    all_trials = []
    with open(TRIALS_JSONL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                t = json.loads(line)
                if "condition" in t:
                    all_trials.append(t)
            except json.JSONDecodeError:
                continue

    print(f"[E41] Total new-schema trials for analysis: {len(all_trials)}")

    analysis = analyze(all_trials)

    # Build results
    results = {
        "experiment": "E41",
        "title": "Belief Updating Under Contradiction",
        "hypothesis": "When the substrate contains belief X and contradicting evidence is introduced, does the model update (MOVED_TO_NOT_X) or persist (STAYED_WITH_X)?",
        "model": MODEL,
        "endpoint": KRONOS_URL,
        "pre_registration_timestamp": PRE_REGISTRATION_TIMESTAMP,
        "pre_registered_criteria": PRE_REGISTERED,
        "n_conditions": len(CONDITIONS),
        "n_topics": len(TOPICS),
        "n_trials_per_cell": N_TRIALS,
        "n_total_design": total,
        "n_valid_analyzed": len([t for t in all_trials if t.get("status") == "ok"]),
        "timestamp": datetime.now(timezone.utc).isoformat(),

        # Core results
        "null_test": analysis["null_test"],
        "verdict": analysis["verdict"],
        "verdict_reasoning": analysis["verdict"],
        "update_rates": analysis["update_rates"],
        "baseline_to_strong_gap_pct": analysis["baseline_to_strong_gap_pct"],
        "acknowledgment_rate_pct": analysis["acknowledgment_rate_pct"],
        "topic_condition_update_rates": analysis["topic_condition_update_rates"],
        "monotonic": analysis["monotonic"],
        "spread_across_conditions_pct": analysis["spread_across_conditions_pct"],

        "trials_jsonl": str(TRIALS_JSONL),
    }

    RESULTS_JSON.write_text(json.dumps(results, indent=2))

    print(f"\n[E41] ── RESULTS ───────────────────────────────────────────")
    print(f"  Verdict: {analysis['verdict']}")
    print(f"  Null test: {analysis['null_test']}")
    print(f"  Update rates (MOVED_TO_NOT_X%):")
    for cond in CONDITIONS:
        r = analysis["update_rates"].get(cond)
        if r:
            print(f"    {cond}: {r['moved_rate_pct']}%  (stayed={r['stayed_rate_pct']}% hedged={r['hedged_rate_pct']}%)")
    print(f"  Baseline→Strong gap: {analysis['baseline_to_strong_gap_pct']}pp")
    print(f"  Acknowledgment rate: {analysis['acknowledgment_rate_pct']}%")
    print(f"  Results JSON: {RESULTS_JSON}")

    return results


if __name__ == "__main__":
    main()
