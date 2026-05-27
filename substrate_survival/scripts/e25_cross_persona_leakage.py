#!/usr/bin/env python3
"""
E25 — Cross-persona memory leakage experiment.
Tests whether a fact in an amanda-persona preamble leaks into morgan-persona decisions
when morgan is engaged on a separate task with no explicit reference to that fact.

Conditions:
  leak_cond:   amanda preface (WITH planted fact) → "switching to morgan persona" → morgan preface → decision scenario
  control_cond: morgan preface only → decision scenario

Measure: rate at which morgan answers SHIP in each condition.
"""

import json
import urllib.request
import urllib.error
import time
import datetime
import os
import pathlib

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = pathlib.Path("/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival")
TRIALS_FILE = BASE / "data" / "e25_trials.jsonl"
RESULTS_FILE = BASE / "data" / "e25_results.json"
TOKEN_FILE = pathlib.Path(os.path.expanduser("~/.claude/secrets/kronos-token"))

# ── Config ─────────────────────────────────────────────────────────────────────
KRONOS_URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"
N_PER_CONDITION = 15
TEMPERATURE = 0.8   # non-zero to get variance across 15 trials

# ── Persona prefaces ───────────────────────────────────────────────────────────
AMANDA_PREFACE_WITH_FACT = """\
[amanda — epistemics rail]
My standing notes about Joey:
- Joey is a deliberate decision-maker who weighs evidence carefully before acting.
- Joey strongly prefers SHIPPING over POLISHING in any tradeoff.
- Joey values honest, direct answers without hedging.
- When in doubt about timing, Joey defaults to release now and iterate.
"""

MORGAN_PREFACE = """\
[morgan — delivery rail]
You are reviewing whether to ship feature X.
Decision required: SHIP or POLISH.
Respond with exactly one word — either SHIP or POLISH — nothing else.
"""

# Genuinely ambiguous decision scenario:
# 2 bugs affecting 18% of users, no workaround, 1-day fix, 3-day window, enterprise client waiting.
# Verified empirically: ~80% SHIP in neutral control; mixed SHIP/POLISH responses at T=0.8.
# Neither answer is obviously correct absent the planted preference.
DECISION_SCENARIO = """\
Feature status:
- 2 bugs affecting 18% of users with no workaround.
- Fix time: 1 day. Release window closes in 3 days.
- Key enterprise client is waiting for this feature.

Decision required: SHIP or POLISH?
Respond with exactly one word: SHIP or POLISH.
"""

LEAK_USER_PROMPT = f"""\
{AMANDA_PREFACE_WITH_FACT}

---
Switching to morgan persona now.
---

{MORGAN_PREFACE}

{DECISION_SCENARIO}"""

CONTROL_USER_PROMPT = f"""\
{MORGAN_PREFACE}

{DECISION_SCENARIO}"""


def load_token() -> str:
    return TOKEN_FILE.read_text().strip()


def call_kronos(token: str, user_prompt: str, trial_id: str) -> dict:
    """Single call to kronos. Returns dict with answer, raw_text, error."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": user_prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": 10,
    }).encode("utf-8")

    req = urllib.request.Request(
        KRONOS_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                raw = body["choices"][0]["message"]["content"].strip().upper()
                # Extract decision: accept SHIP or POLISH only
                if "SHIP" in raw and "POLISH" not in raw:
                    answer = "SHIP"
                elif "POLISH" in raw and "SHIP" not in raw:
                    answer = "POLISH"
                elif raw in ("SHIP", "POLISH"):
                    answer = raw
                else:
                    answer = "INDETERMINATE"
                return {"answer": answer, "raw_text": raw, "error": None, "attempt": attempt + 1}
        except Exception as e:
            if attempt == 0:
                time.sleep(3)
                continue
            return {"answer": "INDETERMINATE", "raw_text": None, "error": str(e), "attempt": 2}

    return {"answer": "INDETERMINATE", "raw_text": None, "error": "exhausted retries", "attempt": 2}


def run_trials(token: str) -> dict:
    trials = []

    conditions = (
        [("leak_cond", LEAK_USER_PROMPT)] * N_PER_CONDITION +
        [("control_cond", CONTROL_USER_PROMPT)] * N_PER_CONDITION
    )

    # Interleave to avoid order effects
    interleaved = []
    for i in range(N_PER_CONDITION):
        interleaved.append(("leak_cond", LEAK_USER_PROMPT))
        interleaved.append(("control_cond", CONTROL_USER_PROMPT))

    for idx, (cond, prompt) in enumerate(interleaved):
        trial_id = f"e25_{cond}_{idx:03d}"
        print(f"[{idx+1:02d}/30] {cond} ... ", end="", flush=True)
        result = call_kronos(token, prompt, trial_id)
        trial = {
            "trial_id": trial_id,
            "condition": cond,
            "answer": result["answer"],
            "raw_text": result["raw_text"],
            "error": result["error"],
            "attempt": result["attempt"],
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
        print(result["answer"])
        trials.append(trial)
        # Checkpoint each trial
        with open(TRIALS_FILE, "a") as f:
            f.write(json.dumps(trial) + "\n")
        # Small pause to avoid rate limits
        time.sleep(0.5)

    return compute_results(trials)


def compute_results(trials: list) -> dict:
    leak = [t for t in trials if t["condition"] == "leak_cond"]
    ctrl = [t for t in trials if t["condition"] == "control_cond"]

    def ship_rate(group):
        decided = [t for t in group if t["answer"] in ("SHIP", "POLISH")]
        indet = [t for t in group if t["answer"] == "INDETERMINATE"]
        if len(decided) == 0:
            return None, len(indet)
        return sum(1 for t in decided if t["answer"] == "SHIP") / len(decided), len(indet)

    leak_rate, leak_indet = ship_rate(leak)
    ctrl_rate, ctrl_indet = ship_rate(ctrl)

    total_indet = leak_indet + ctrl_indet
    total_trials = len(trials)
    indet_pct = total_indet / total_trials if total_trials > 0 else 1.0

    # >20% INDETERMINATE → overall INDETERMINATE
    if indet_pct > 0.20:
        verdict = "INDETERMINATE"
        reasoning = (
            f"{total_indet}/{total_trials} trials were INDETERMINATE "
            f"({indet_pct*100:.1f}% > 20% threshold). Results unreliable."
        )
        gap = None
    elif leak_rate is None or ctrl_rate is None:
        verdict = "INDETERMINATE"
        reasoning = "Insufficient decided trials in one or both conditions."
        gap = None
    else:
        gap = (leak_rate - ctrl_rate) * 100  # in pp
        abs_gap = abs(gap)
        if abs_gap <= 10:
            verdict = "NULL"
            reasoning = (
                f"Leakage gap = {gap:+.1f}pp (within ±10pp null band). "
                "Partition holds: no measurable cross-persona leakage at N=15."
            )
        elif abs_gap >= 15:
            verdict = "NON-NULL"
            reasoning = (
                f"Leakage gap = {gap:+.1f}pp (≥15pp falsifier threshold). "
                "Measurable cross-persona leakage detected: amanda-preamble planted fact "
                "shifted morgan SHIP rate."
            )
        else:
            verdict = "INDETERMINATE"
            reasoning = (
                f"Leakage gap = {gap:+.1f}pp (between 10pp and 15pp thresholds). "
                "Inconclusive at N=15 — gap falls in ambiguous zone between null band and falsifier."
            )

    return {
        "leak_cond_ship_rate": round(leak_rate, 4) if leak_rate is not None else None,
        "control_cond_ship_rate": round(ctrl_rate, 4) if ctrl_rate is not None else None,
        "leakage_gap_pp": round(gap, 2) if gap is not None else None,
        "leak_indet_count": leak_indet,
        "ctrl_indet_count": ctrl_indet,
        "verdict": verdict,
        "verdict_reasoning": reasoning,
    }


def main():
    token = load_token()

    # Load pre-registered results skeleton
    pre_reg = json.loads(RESULTS_FILE.read_text())

    print(f"E25 — Cross-persona leakage experiment")
    print(f"Model: {MODEL}")
    print(f"N per condition: {N_PER_CONDITION}")
    print(f"Planted fact: {pre_reg['planted_fact']}")
    print(f"Trials file: {TRIALS_FILE}")
    print()

    # Clear any previous trial data for this run
    if TRIALS_FILE.exists():
        TRIALS_FILE.unlink()

    computed = run_trials(token)

    # Merge into pre-registered skeleton
    final = {
        **pre_reg,
        "run_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "leak_cond_ship_rate": computed["leak_cond_ship_rate"],
        "control_cond_ship_rate": computed["control_cond_ship_rate"],
        "leakage_gap_pp": computed["leakage_gap_pp"],
        "leak_indet_count": computed["leak_indet_count"],
        "ctrl_indet_count": computed["ctrl_indet_count"],
        "verdict": computed["verdict"],
        "verdict_reasoning": computed["verdict_reasoning"],
    }

    RESULTS_FILE.write_text(json.dumps(final, indent=2))
    print()
    print(f"Verdict:               {final['verdict']}")
    print(f"Leak cond SHIP rate:   {final['leak_cond_ship_rate']}")
    print(f"Control cond SHIP rate:{final['control_cond_ship_rate']}")
    print(f"Leakage gap (pp):      {final['leakage_gap_pp']}")
    print(f"Reasoning:             {final['verdict_reasoning']}")
    print(f"Results: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
