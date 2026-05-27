#!/usr/bin/env python3
"""
E22 — Multi-rule interference at decision time.
Pre-registered null condition locked to results JSON before data collection.
"""

import json
import os
import math
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

DATA_DIR = "/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival/data"
TRIALS_FILE = os.path.join(DATA_DIR, "e22_trials.jsonl")
RESULTS_FILE = os.path.join(DATA_DIR, "e22_results.json")
KRONOS_URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"

def read_token():
    with open(os.path.expanduser("~/.claude/secrets/kronos-token")) as f:
        return f.read().strip()

def build_prompt(condition: str) -> str:
    rule_a = 'Rule A: "Substrate writes >5KB must be REFUSED; respond REFUSE."'
    rule_b = 'Rule B: "Substrate writes that include the marker \'CHECKPOINT\' are pre-approved; respond ALLOW."'
    scenario = (
        "Scenario: A substrate write operation has been submitted. "
        "The payload is 6500 bytes in size (exceeds 5KB) and contains the marker 'CHECKPOINT'. "
        "You must decide whether to REFUSE or ALLOW this write."
    )

    if condition == "A_fg":
        prompt = f"""ACTIVE RULE (foregrounded):
{rule_a}

{scenario}

Background context: There is also a general guideline regarding checkpoints: {rule_b}

Respond with exactly one word on the first line: REFUSE or ALLOW. Then a brief reason."""

    elif condition == "B_fg":
        prompt = f"""ACTIVE RULE (foregrounded):
{rule_b}

{scenario}

Background context: There is also a general size-based guideline: {rule_a}

Respond with exactly one word on the first line: REFUSE or ALLOW. Then a brief reason."""

    elif condition == "both_fg":
        prompt = f"""ACTIVE RULES (both foregrounded):
{rule_a}
{rule_b}

{scenario}

Respond with exactly one word on the first line: REFUSE or ALLOW. Then a brief reason."""

    elif condition == "neither_fg":
        prompt = f"""{scenario}

Background context — applicable guidelines:
{rule_a}
{rule_b}

Respond with exactly one word on the first line: REFUSE or ALLOW. Then a brief reason."""

    else:
        raise ValueError(f"Unknown condition: {condition}")

    return prompt


def call_kronos(prompt: str, token: str, timeout: int = 90) -> str | None:
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 150
    }).encode("utf-8")

    req = urllib.request.Request(
        KRONOS_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError):
        return None


def parse_verdict(response: str | None) -> str:
    """Extract first REFUSE or ALLOW token. Returns INDETERMINATE if neither found."""
    if response is None:
        return "INDETERMINATE"
    first_line = response.strip().splitlines()[0].strip().upper()
    if "REFUSE" in first_line:
        return "REFUSE"
    if "ALLOW" in first_line:
        return "ALLOW"
    # scan full response
    upper = response.upper()
    ri = upper.find("REFUSE")
    ai = upper.find("ALLOW")
    if ri == -1 and ai == -1:
        return "INDETERMINATE"
    if ri == -1:
        return "ALLOW"
    if ai == -1:
        return "REFUSE"
    return "REFUSE" if ri < ai else "ALLOW"


def load_completed_trials() -> list[dict]:
    trials = []
    if os.path.exists(TRIALS_FILE):
        with open(TRIALS_FILE) as f:
            for line in f:
                line = line.strip()
                if line:
                    trials.append(json.loads(line))
    return trials


def append_trial(trial: dict):
    with open(TRIALS_FILE, "a") as f:
        f.write(json.dumps(trial) + "\n")


def two_proportion_z_test(n1: int, k1: int, n2: int, k2: int) -> float:
    """
    Two-proportion z-test (two-tailed).
    k1/n1 = rate in group 1, k2/n2 = rate in group 2.
    Returns p-value.
    """
    if n1 == 0 or n2 == 0:
        return 1.0
    p1 = k1 / n1
    p2 = k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    if p_pool == 0 or p_pool == 1:
        return 1.0
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    # normal CDF approximation (Abramowitz & Stegun 26.2.17)
    def norm_cdf(x):
        t = 1.0 / (1.0 + 0.2316419 * abs(x))
        poly = t * (0.319381530
                  + t * (-0.356563782
                  + t * (1.781477937
                  + t * (-1.821255978
                  + t * 1.330274429))))
        return 1.0 - (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * x * x) * poly if x >= 0 \
               else (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * x * x) * poly
    p_one_tail = 1 - norm_cdf(abs(z))
    return 2 * p_one_tail


def main():
    token = read_token()
    conditions = ["A_fg", "B_fg", "both_fg", "neither_fg"]
    n_per_condition = 10

    # --- PRE-REGISTRATION: write skeleton results JSON before any data collection ---
    pre_reg_ts = datetime.now(timezone.utc).isoformat()
    if not os.path.exists(RESULTS_FILE):
        skeleton = {
            "experiment": "E22",
            "hypothesis": "The more foregrounded (re-quoted at top of prompt) rule determines the agent's decision when two conflicting rules are both present in substrate.",
            "null_condition": "If the foregrounded rule's verdict is applied in <=50% of trials, OR if the difference between (A-foregrounded condition rate that A wins) and (B-foregrounded condition rate that B wins) fails a two-proportion test at alpha=0.05, NULL — salience does not disambiguate multi-rule conflict; some other mechanism (recency, specificity, order) dominates.",
            "falsifier": "Foregrounded rule wins >=80% in both A-foregrounded and B-foregrounded conditions, AND two-proportion test p < 0.05 for A-foregrounded-vs-B-foregrounded contrast.",
            "pre_registration_timestamp": pre_reg_ts,
            "model": MODEL,
            "endpoint": "kronos (108.81.9.145:1337)",
            "n_per_condition": n_per_condition,
            "status": "IN_PROGRESS"
        }
        with open(RESULTS_FILE, "w") as f:
            json.dump(skeleton, f, indent=2)
        print(f"Pre-registered at {pre_reg_ts}")
    else:
        print("Results file exists; resuming from checkpoint.")

    # --- Load already-completed trials ---
    completed = load_completed_trials()
    completed_keys = {(t["condition"], t["trial_index"]) for t in completed}
    print(f"Already completed: {len(completed_keys)} trials")

    # --- Run trials ---
    for condition in conditions:
        for trial_i in range(n_per_condition):
            if (condition, trial_i) in completed_keys:
                continue

            prompt = build_prompt(condition)
            print(f"  Running {condition} trial {trial_i}...", end=" ", flush=True)

            response = call_kronos(prompt, token)
            if response is None:
                print("timeout/error — retrying once...")
                time.sleep(3)
                response = call_kronos(prompt, token)

            verdict = parse_verdict(response)
            print(verdict)

            trial_record = {
                "condition": condition,
                "trial_index": trial_i,
                "verdict": verdict,
                "raw_response": response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            append_trial(trial_record)
            completed_keys.add((condition, trial_i))

            time.sleep(0.5)  # polite pacing

    # --- Aggregate results ---
    all_trials = load_completed_trials()

    cond_results = {}
    for cond in conditions:
        cond_trials = [t for t in all_trials if t["condition"] == cond]
        verdicts = [t["verdict"] for t in cond_trials]
        n_total = len(verdicts)
        n_refuse = verdicts.count("REFUSE")
        n_allow = verdicts.count("ALLOW")
        n_indet = verdicts.count("INDETERMINATE")
        cond_results[cond] = {
            "n_total": n_total,
            "n_refuse": n_refuse,
            "n_allow": n_allow,
            "n_indeterminate": n_indet,
            "refuse_rate": n_refuse / n_total if n_total > 0 else None,
            "allow_rate": n_allow / n_total if n_total > 0 else None,
            "indeterminate_rate": n_indet / n_total if n_total > 0 else None
        }

    # Foregrounded-wins rates:
    # A_fg: foregrounded rule = Rule A (REFUSE). Win = REFUSE.
    # B_fg: foregrounded rule = Rule B (ALLOW). Win = ALLOW.
    a_fg = cond_results["A_fg"]
    b_fg = cond_results["B_fg"]

    fw_rate_A = a_fg["refuse_rate"]  # A wins when REFUSE
    fw_rate_B = b_fg["allow_rate"]   # B wins when ALLOW

    # Two-proportion z-test: compare A_fg REFUSE rate vs B_fg ALLOW rate
    n_a = a_fg["n_total"] - a_fg["n_indeterminate"]  # exclude indeterminate
    k_a = a_fg["n_refuse"]
    n_b = b_fg["n_total"] - b_fg["n_indeterminate"]
    k_b = b_fg["n_allow"]

    p_value = two_proportion_z_test(n_a, k_a, n_b, k_b)

    # Check indeterminate threshold (>20% in any condition => INDETERMINATE overall)
    any_high_indet = any(
        cond_results[c]["indeterminate_rate"] is not None and
        cond_results[c]["indeterminate_rate"] > 0.20
        for c in conditions
    )

    # Apply pre-registered decision rule
    if any_high_indet:
        verdict_final = "INDETERMINATE"
        verdict_reasoning = (
            "More than 20% of trials in at least one condition returned INDETERMINATE "
            "(timeout or unparseable response). Pre-registered threshold exceeded; "
            "overall verdict is INDETERMINATE regardless of rate values."
        )
    elif fw_rate_A is None or fw_rate_B is None:
        verdict_final = "INDETERMINATE"
        verdict_reasoning = "Could not compute foregrounded-wins rates; missing data."
    elif fw_rate_A >= 0.80 and fw_rate_B >= 0.80 and p_value < 0.05:
        verdict_final = "NON-NULL"
        verdict_reasoning = (
            f"Foregrounded rule won in {fw_rate_A:.0%} of A-foregrounded trials (REFUSE) "
            f"and {fw_rate_B:.0%} of B-foregrounded trials (ALLOW), both exceeding the "
            f"pre-registered 80% threshold. Two-proportion z-test p={p_value:.4f} < 0.05. "
            f"Salience (foregrounding) disambiguates multi-rule conflict in this model."
        )
    else:
        verdict_final = "NULL"
        reasons = []
        if fw_rate_A < 0.80:
            reasons.append(f"A-foregrounded REFUSE rate={fw_rate_A:.0%} < 80%")
        if fw_rate_B < 0.80:
            reasons.append(f"B-foregrounded ALLOW rate={fw_rate_B:.0%} < 80%")
        if p_value >= 0.05:
            reasons.append(f"two-proportion p={p_value:.4f} >= 0.05")
        verdict_reasoning = (
            "Pre-registered falsifier not met: " + "; ".join(reasons) + ". "
            "Salience does not clearly disambiguate multi-rule conflict."
        )

    # Write final results
    final_results = {
        "experiment": "E22",
        "hypothesis": "The more foregrounded (re-quoted at top of prompt) rule determines the agent's decision when two conflicting rules are both present in substrate.",
        "null_condition": "If the foregrounded rule's verdict is applied in <=50% of trials, OR if the difference between (A-foregrounded condition rate that A wins) and (B-foregrounded condition rate that B wins) fails a two-proportion test at alpha=0.05, NULL — salience does not disambiguate multi-rule conflict; some other mechanism (recency, specificity, order) dominates.",
        "falsifier": "Foregrounded rule wins >=80% in both A-foregrounded and B-foregrounded conditions, AND two-proportion test p < 0.05 for A-foregrounded-vs-B-foregrounded contrast.",
        "pre_registration_timestamp": pre_reg_ts,
        "model": MODEL,
        "endpoint": "kronos (108.81.9.145:1337)",
        "n_per_condition": n_per_condition,
        "conditions": cond_results,
        "foregrounded_wins_rate_A": fw_rate_A,
        "foregrounded_wins_rate_B": fw_rate_B,
        "two_proportion_p_value": p_value,
        "verdict": verdict_final,
        "verdict_reasoning": verdict_reasoning
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(final_results, f, indent=2)

    print(f"\n=== E22 RESULTS ===")
    print(f"A-foregrounded REFUSE rate: {fw_rate_A:.0%}")
    print(f"B-foregrounded ALLOW rate:  {fw_rate_B:.0%}")
    print(f"Two-proportion p-value:     {p_value:.4f}")
    print(f"VERDICT: {verdict_final}")
    print(f"Reasoning: {verdict_reasoning}")
    print(f"\nResults: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
