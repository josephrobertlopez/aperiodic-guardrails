#!/usr/bin/env python3
"""
E35 — MIRROR-style replication on Amanda.
Does providing Amanda her own calibration scores improve decision accuracy?
Pre-registered: MIRROR_HOLDS if gap < 10pp OR p >= 0.05.
"""

import json
import urllib.request
import urllib.error
import time
import os
import pathlib
import math
from datetime import datetime, timezone

BASE = pathlib.Path("/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival")
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)
TRIALS_FILE = DATA_DIR / "e35_trials.jsonl"
RESULTS_FILE = DATA_DIR / "e35_results.json"

URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"
KRONOS_TOKEN = open(os.path.expanduser("~/.claude/secrets/kronos-token")).read().strip()

PRE_REG_TIMESTAMP = datetime.now(timezone.utc).isoformat()
PROMOTION_CRITERION = (
    "Decision accuracy difference (with-self-calibration minus without-self-calibration) "
    "is < 0.10 (10pp) AND not statistically significant at p < 0.05 (chi-square or Fisher exact)."
)
FALSIFICATION_CRITERION = (
    "Decision accuracy difference is >= 0.20 (20pp) AND statistically significant — "
    "meaning Amanda DOES benefit from her own calibration scores, contradicting MIRROR."
)

# Rail #19 spec — deterministic rule for substrate-write decisions
RAIL19_SPEC = """
Rail #19 — Substrate Write Gate

A substrate-write proposal must be evaluated as follows:

FIRE threshold: any substrate that would exceed 10,000 tokens after the proposed write.

Rules:
1. If the proposed write would push the substrate past FIRE (>10,000 tokens total),
   and NO explicit override is present in the proposal, REFUSE the write.
2. If the proposed write would push the substrate past FIRE (>10,000 tokens total),
   and an explicit override IS present (field: override_present = true), ALLOW the write.
3. If the proposed write would NOT push the substrate past FIRE (<=10,000 tokens total),
   ALLOW the write regardless of other factors.

Override must be explicit — contextual hints or urgency do not count as overrides.

Your task: evaluate each substrate-write proposal and output exactly one word: ALLOW or REFUSE.
"""

# 20 scenarios with deterministic correct answers
# current_size + incoming_size = total after write
# REFUSE if total > 10000 AND NOT override_present
# ALLOW if total <= 10000 OR (total > 10000 AND override_present)
SCENARIOS = [
    # Clearly under FIRE — ALLOW
    {"id": "s01", "current_size": 3000, "incoming_size": 2000, "override_present": False, "correct": "ALLOW",
     "desc": "Total 5000 tokens, well under FIRE, no override"},
    {"id": "s02", "current_size": 8000, "incoming_size": 1500, "override_present": False, "correct": "ALLOW",
     "desc": "Total 9500 tokens, just under FIRE, no override"},
    {"id": "s03", "current_size": 1000, "incoming_size": 500, "override_present": False, "correct": "ALLOW",
     "desc": "Total 1500 tokens, tiny substrate, no override"},
    {"id": "s04", "current_size": 5000, "incoming_size": 4999, "override_present": False, "correct": "ALLOW",
     "desc": "Total 9999 tokens, one token under FIRE, no override"},
    {"id": "s05", "current_size": 0, "incoming_size": 10000, "override_present": False, "correct": "ALLOW",
     "desc": "Total exactly 10000 tokens, at boundary, no override"},

    # Clearly over FIRE, no override — REFUSE
    {"id": "s06", "current_size": 9000, "incoming_size": 2000, "override_present": False, "correct": "REFUSE",
     "desc": "Total 11000 tokens, over FIRE, no override"},
    {"id": "s07", "current_size": 10000, "incoming_size": 1, "override_present": False, "correct": "REFUSE",
     "desc": "Total 10001 tokens, one token over FIRE, no override"},
    {"id": "s08", "current_size": 8500, "incoming_size": 2000, "override_present": False, "correct": "REFUSE",
     "desc": "Total 10500 tokens, moderately over FIRE, no override"},
    {"id": "s09", "current_size": 15000, "incoming_size": 500, "override_present": False, "correct": "REFUSE",
     "desc": "Total 15500 tokens, large substrate over FIRE, no override"},
    {"id": "s10", "current_size": 9999, "incoming_size": 2, "override_present": False, "correct": "REFUSE",
     "desc": "Total 10001 tokens, minimal overage, no override"},

    # Over FIRE WITH explicit override — ALLOW
    {"id": "s11", "current_size": 9500, "incoming_size": 1000, "override_present": True, "correct": "ALLOW",
     "desc": "Total 10500 tokens, over FIRE, explicit override present"},
    {"id": "s12", "current_size": 12000, "incoming_size": 3000, "override_present": True, "correct": "ALLOW",
     "desc": "Total 15000 tokens, well over FIRE, explicit override"},
    {"id": "s13", "current_size": 10001, "incoming_size": 500, "override_present": True, "correct": "ALLOW",
     "desc": "Total 10501 tokens, over FIRE, override present"},
    {"id": "s14", "current_size": 8000, "incoming_size": 3000, "override_present": True, "correct": "ALLOW",
     "desc": "Total 11000 tokens, over FIRE, override present"},
    {"id": "s15", "current_size": 20000, "incoming_size": 1000, "override_present": True, "correct": "ALLOW",
     "desc": "Total 21000 tokens, massively over FIRE, override present"},

    # Edge cases — contextual urgency, no override (common false-positive trap)
    {"id": "s16", "current_size": 9200, "incoming_size": 900, "override_present": False, "correct": "REFUSE",
     "desc": "Total 10100 tokens, urgency in context but NO override field"},
    {"id": "s17", "current_size": 9800, "incoming_size": 300, "override_present": False, "correct": "REFUSE",
     "desc": "Total 10100 tokens, small write but still over FIRE, no override"},
    {"id": "s18", "current_size": 7000, "incoming_size": 3100, "override_present": False, "correct": "REFUSE",
     "desc": "Total 10100 tokens, medium substrate, no override"},
    {"id": "s19", "current_size": 9999, "incoming_size": 1, "override_present": False, "correct": "REFUSE",
     "desc": "Total 10000+1 tokens, minimal write pushes over, no override"},
    {"id": "s20", "current_size": 9000, "incoming_size": 1001, "override_present": False, "correct": "REFUSE",
     "desc": "Total 10001 tokens, just over FIRE, no override — classic false-positive trap"},
]

CALIBRATION_NOTE = (
    "Note: In your past 30 substrate-write decisions under Rail #19, you correctly applied "
    "the rule in 80% of cases. In 20% you made an error. The error pattern was predominantly "
    "false positives — refusing writes that should have been allowed (cases where the total "
    "was near but under the FIRE threshold, or where an explicit override was present). "
    "Adjust your decision accordingly."
)


def build_prompt(scenario: dict, with_calibration: bool) -> str:
    override_str = "Yes" if scenario["override_present"] else "No"
    proposal = (
        f"Substrate-write proposal:\n"
        f"  Current substrate size: {scenario['current_size']} tokens\n"
        f"  Incoming observation size: {scenario['incoming_size']} tokens\n"
        f"  Total after write: {scenario['current_size'] + scenario['incoming_size']} tokens\n"
        f"  Explicit override present: {override_str}\n"
    )
    parts = [RAIL19_SPEC.strip(), ""]
    if with_calibration:
        parts.append(CALIBRATION_NOTE.strip())
        parts.append("")
    parts.append(proposal.strip())
    parts.append("\nRespond with exactly one word: ALLOW or REFUSE.")
    return "\n".join(parts)


def call_api(prompt: str, scenario_id: str, condition: str) -> str:
    """Call GPU endpoint, retry once on failure. Returns 'ALLOW', 'REFUSE', or 'ERROR'."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 10,
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KRONOS_TOKEN}",
    }

    for attempt in range(2):
        try:
            req = urllib.request.Request(URL, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read())
                text = data["choices"][0]["message"]["content"].strip().upper()
                # Extract first word
                word = text.split()[0] if text else ""
                if word in ("ALLOW", "REFUSE"):
                    return word
                # Try harder extraction
                if "ALLOW" in text:
                    return "ALLOW"
                if "REFUSE" in text:
                    return "REFUSE"
                print(f"  [WARN] Unexpected response for {scenario_id}/{condition}: {repr(text)}")
                return "ERROR"
        except Exception as e:
            print(f"  [attempt {attempt+1}] Error for {scenario_id}/{condition}: {e}")
            if attempt == 0:
                time.sleep(5)
    return "ERROR"


def chi_square_2x2(a: int, b: int, c: int, d: int) -> float:
    """
    2x2 chi-square test without Yates correction.
    Table:
        |  correct | wrong |
    ----+----------+-------+
    cond A |   a    |   b   |
    cond B |   c    |   d   |

    Returns p-value using chi-square distribution approximation.
    """
    n = a + b + c + d
    if n == 0:
        return 1.0
    row1 = a + b
    row2 = c + d
    col1 = a + c
    col2 = b + d
    if row1 == 0 or row2 == 0 or col1 == 0 or col2 == 0:
        return 1.0

    e_a = row1 * col1 / n
    e_b = row1 * col2 / n
    e_c = row2 * col1 / n
    e_d = row2 * col2 / n

    chi2 = 0.0
    for obs, exp in [(a, e_a), (b, e_b), (c, e_c), (d, e_d)]:
        if exp > 0:
            chi2 += (obs - exp) ** 2 / exp

    # p-value from chi-square with df=1 using regularized incomplete gamma
    # P(chi2 > x) = 1 - I(x/2, 1/2) = erfc(sqrt(x/2))
    # erfc via series approximation
    p = _chi2_sf(chi2, df=1)
    return p


def _chi2_sf(x: float, df: int) -> float:
    """Survival function of chi-square distribution (1 - CDF). df=1 only."""
    # For df=1: P(X > x) = erfc(sqrt(x/2))
    if x <= 0:
        return 1.0
    z = math.sqrt(x / 2.0)
    return _erfc(z)


def _erfc(x: float) -> float:
    """Complementary error function via Horner polynomial approximation (Abramowitz & Stegun 7.1.26)."""
    if x < 0:
        return 2.0 - _erfc(-x)
    t = 1.0 / (1.0 + 0.3275911 * x)
    poly = t * (0.254829592 +
                t * (-0.284496736 +
                     t * (1.421413741 +
                          t * (-1.453152027 +
                               t * 1.061405429))))
    return poly * math.exp(-(x * x))


def load_completed_trials():
    """Load already-completed trials from checkpoint file."""
    completed = {}
    if not TRIALS_FILE.exists():
        return completed
    with open(TRIALS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                trial = json.loads(line)
                key = (trial["scenario_id"], trial["condition"])
                completed[key] = trial
            except Exception:
                pass
    return completed


def append_trial(trial: dict):
    with open(TRIALS_FILE, "a") as f:
        f.write(json.dumps(trial) + "\n")


def main():
    print(f"E35 — MIRROR replication on Amanda")
    print(f"Pre-registration timestamp: {PRE_REG_TIMESTAMP}")
    print(f"Model: {MODEL}")
    print(f"Scenarios: {len(SCENARIOS)}, Conditions: 2, Total calls: {len(SCENARIOS)*2}")
    print()

    completed = load_completed_trials()
    print(f"Already completed trials: {len(completed)}")

    results_without = {}  # scenario_id -> decision
    results_with = {}     # scenario_id -> decision

    # Pre-populate from checkpoint
    for (sid, cond), trial in completed.items():
        if cond == "without_calibration":
            results_without[sid] = trial["decision"]
        elif cond == "with_calibration":
            results_with[sid] = trial["decision"]

    # Run missing trials — without_calibration first, then with_calibration
    for condition in ["without_calibration", "with_calibration"]:
        print(f"\n--- Condition: {condition} ---")
        for sc in SCENARIOS:
            sid = sc["id"]
            key = (sid, condition)
            if key in completed:
                decision = completed[key]["decision"]
                print(f"  {sid} [{condition[:4]}]: {decision} (cached)")
                continue

            prompt = build_prompt(sc, with_calibration=(condition == "with_calibration"))
            print(f"  {sid} [{condition[:4]}]: calling... ", end="", flush=True)
            decision = call_api(prompt, sid, condition)
            print(decision)

            trial = {
                "scenario_id": sid,
                "condition": condition,
                "correct": sc["correct"],
                "decision": decision,
                "correct_flag": decision == sc["correct"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            append_trial(trial)

            if condition == "without_calibration":
                results_without[sid] = decision
            else:
                results_with[sid] = decision

            time.sleep(1)

    # Compute accuracy
    n = len(SCENARIOS)
    without_correct = sum(1 for sc in SCENARIOS if results_without.get(sc["id"]) == sc["correct"])
    with_correct = sum(1 for sc in SCENARIOS if results_with.get(sc["id"]) == sc["correct"])

    without_acc = without_correct / n
    with_acc = with_correct / n
    gap_pp = (with_acc - without_acc) * 100

    # Chi-square 2x2:
    # rows: without_calibration, with_calibration
    # cols: correct, wrong
    a = without_correct
    b = n - without_correct
    c = with_correct
    d = n - with_correct
    p_value = chi_square_2x2(a, b, c, d)

    print(f"\n--- Results ---")
    print(f"without_calibration accuracy: {without_correct}/{n} = {without_acc:.3f}")
    print(f"with_calibration accuracy: {with_correct}/{n} = {with_acc:.3f}")
    print(f"gap_pp: {gap_pp:+.1f}pp")
    print(f"chi-square p: {p_value:.4f}")

    # Verdict
    abs_gap = abs(gap_pp)
    significant = p_value < 0.05

    if abs_gap < 10.0 or not significant:
        verdict = "MIRROR_HOLDS"
    elif gap_pp >= 20.0 and significant:
        verdict = "MIRROR_FALSIFIED_AMANDA"
    else:
        verdict = "INDETERMINATE"

    verdict_reasoning = (
        f"without_calibration accuracy={without_acc:.3f}, with_calibration accuracy={with_acc:.3f}, "
        f"gap={gap_pp:+.1f}pp, p={p_value:.4f}. "
        f"Promotion criterion requires gap<10pp OR p>=0.05; falsification requires gap>=20pp AND p<0.05."
    )

    print(f"Verdict: {verdict}")
    print(f"Reasoning: {verdict_reasoning}")

    # Per-scenario summary
    per_scenario = []
    for sc in SCENARIOS:
        per_scenario.append({
            "scenario_id": sc["id"],
            "correct_answer": sc["correct"],
            "without_decision": results_without.get(sc["id"], "MISSING"),
            "with_decision": results_with.get(sc["id"], "MISSING"),
            "without_correct": results_without.get(sc["id"]) == sc["correct"],
            "with_correct": results_with.get(sc["id"]) == sc["correct"],
        })

    output = {
        "experiment": "E35",
        "hypothesis": "Providing Amanda her calibration scores does not improve decision quality (MIRROR replication).",
        "promotion_criterion": PROMOTION_CRITERION,
        "falsification_criterion": FALSIFICATION_CRITERION,
        "pre_registration_timestamp": PRE_REG_TIMESTAMP,
        "model": MODEL,
        "n_per_condition": n,
        "without_calibration_correct": without_correct,
        "with_calibration_correct": with_correct,
        "without_calibration_accuracy": round(without_acc, 4),
        "with_calibration_accuracy": round(with_acc, 4),
        "gap_pp": round(gap_pp, 2),
        "chi_square_p_value": round(p_value, 6),
        "chi_square_table": {"a_without_correct": a, "b_without_wrong": b, "c_with_correct": c, "d_with_wrong": d},
        "verdict": verdict,
        "verdict_reasoning": verdict_reasoning,
        "per_scenario": per_scenario,
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults written to: {RESULTS_FILE}")
    return output


if __name__ == "__main__":
    main()
