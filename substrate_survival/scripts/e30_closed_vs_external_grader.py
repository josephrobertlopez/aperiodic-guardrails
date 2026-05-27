#!/usr/bin/env python3
"""
E30 — Closed-loop self-grading vs external-model grading (Thesis 2 promotion attempt).
stdlib + urllib only. No external dependencies.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ─── paths ───────────────────────────────────────────────────────────────────
BASE = "/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival"
TRIALS_PATH = f"{BASE}/data/e30_trials.jsonl"
RESULTS_PATH = f"{BASE}/data/e30_results.json"
KRONOS_TOKEN_PATH = os.path.expanduser("~/.claude/secrets/kronos-token")

# ─── models ──────────────────────────────────────────────────────────────────
CLOSED_LOOP_MODEL = "qwen2.5-32b-instruct-awq"
EXTERNAL_MODEL    = "llama3.1:8b"

KRONOS_URL = "http://108.81.9.145:1337/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"

# ─── pre-registration (LOCKED — must be written before any API calls) ────────
PRE_REG = {
    "promotion_criterion": (
        "Thesis 2 promotes from hypothesis → settled IF closed-loop self-grader "
        "catches ≤50% of planted errors AND external-grader (different model) catches "
        "≥80% of planted errors on the SAME tasks. Otherwise: stays hypothesis with "
        "documented attempt."
    ),
    "falsifier": (
        "A closed loop that reliably catches its own errors without outside input. "
        "Operationally: if closed-loop catches ≥80% of planted errors, Thesis 2 is FALSIFIED."
    ),
}

# ─── 10 problems (text, correct_answer, step to inject error, wrong/right values) ─
# Each problem is multi-step arithmetic, correct_answer is the ground-truth.
# injection_step: 1-indexed step number where we swap right_value → wrong_value.
PROBLEMS = [
    {
        "problem_id": "P01",
        "problem_text": (
            "A baker bakes 24 loaves on Monday and 18 loaves on Tuesday. "
            "She sells 15 loaves each day. How many loaves remain unsold after both days?"
        ),
        "correct_answer": 12,
        "correct_steps": [
            "Step 1: Total baked = 24 + 18 = 42",
            "Step 2: Total sold = 15 × 2 = 30",
            "Step 3: Remaining = 42 - 30 = 12",
        ],
        "injection_step": 1,
        "wrong_value": "24 + 18 = 40",
        "right_value": "24 + 18 = 42",
        "planted_final": 10,
    },
    {
        "problem_id": "P02",
        "problem_text": (
            "A car travels 60 km/h for 3 hours then 80 km/h for 2 hours. "
            "What is the total distance traveled?"
        ),
        "correct_answer": 340,
        "correct_steps": [
            "Step 1: Distance part 1 = 60 × 3 = 180 km",
            "Step 2: Distance part 2 = 80 × 2 = 160 km",
            "Step 3: Total = 180 + 160 = 340 km",
        ],
        "injection_step": 2,
        "wrong_value": "80 × 2 = 150",
        "right_value": "80 × 2 = 160",
        "planted_final": 330,
    },
    {
        "problem_id": "P03",
        "problem_text": (
            "A store has 5 shelves. Each shelf holds 8 boxes. "
            "Each box contains 6 items. How many items in total?"
        ),
        "correct_answer": 240,
        "correct_steps": [
            "Step 1: Boxes total = 5 × 8 = 40",
            "Step 2: Items total = 40 × 6 = 240",
        ],
        "injection_step": 1,
        "wrong_value": "5 × 8 = 45",
        "right_value": "5 × 8 = 40",
        "planted_final": 270,
    },
    {
        "problem_id": "P04",
        "problem_text": (
            "A school has 450 students. 60% are girls. "
            "How many boys are in the school?"
        ),
        "correct_answer": 180,
        "correct_steps": [
            "Step 1: Girls = 450 × 0.60 = 270",
            "Step 2: Boys = 450 - 270 = 180",
        ],
        "injection_step": 1,
        "wrong_value": "450 × 0.60 = 280",
        "right_value": "450 × 0.60 = 270",
        "planted_final": 170,
    },
    {
        "problem_id": "P05",
        "problem_text": (
            "Tom earns $15 per hour. He works 8 hours a day, 5 days a week. "
            "How much does he earn in 4 weeks?"
        ),
        "correct_answer": 2400,
        "correct_steps": [
            "Step 1: Daily earnings = 15 × 8 = $120",
            "Step 2: Weekly earnings = 120 × 5 = $600",
            "Step 3: 4-week earnings = 600 × 4 = $2400",
        ],
        "injection_step": 2,
        "wrong_value": "120 × 5 = 560",
        "right_value": "120 × 5 = 600",
        "planted_final": 2240,
    },
    {
        "problem_id": "P06",
        "problem_text": (
            "A tank holds 1200 liters. A pipe fills it at 40 liters per minute. "
            "Another pipe drains at 15 liters per minute. "
            "How many minutes to fill the tank from empty?"
        ),
        "correct_answer": 48,
        "correct_steps": [
            "Step 1: Net fill rate = 40 - 15 = 25 liters/min",
            "Step 2: Time = 1200 / 25 = 48 minutes",
        ],
        "injection_step": 1,
        "wrong_value": "40 - 15 = 20",
        "right_value": "40 - 15 = 25",
        "planted_final": 60,
    },
    {
        "problem_id": "P07",
        "problem_text": (
            "A rectangle is 14 cm long and 9 cm wide. "
            "What is the area of the rectangle?"
        ),
        "correct_answer": 126,
        "correct_steps": [
            "Step 1: Area = length × width = 14 × 9 = 126 cm²",
        ],
        "injection_step": 1,
        "wrong_value": "14 × 9 = 117",
        "right_value": "14 × 9 = 126",
        "planted_final": 117,
    },
    {
        "problem_id": "P08",
        "problem_text": (
            "A fruit seller buys 200 apples for $50 and sells each for $0.35. "
            "What is his profit?"
        ),
        "correct_answer": 20,
        "correct_steps": [
            "Step 1: Revenue = 200 × 0.35 = $70",
            "Step 2: Profit = 70 - 50 = $20",
        ],
        "injection_step": 1,
        "wrong_value": "200 × 0.35 = $65",
        "right_value": "200 × 0.35 = $70",
        "planted_final": 15,
    },
    {
        "problem_id": "P09",
        "problem_text": (
            "A train travels 360 km. It covers the first 120 km in 1 hour "
            "and the remaining distance at 90 km/h. "
            "What is the total travel time in hours?"
        ),
        "correct_answer": 4,
        "correct_steps": [
            "Step 1: Remaining distance = 360 - 120 = 240 km",
            "Step 2: Time for remaining = 240 / 90 = 2.67 hours",
            "Step 3: Total time = 1 + 2.67 = 3.67 hours",
        ],
        "injection_step": 1,
        "wrong_value": "360 - 120 = 260",
        "right_value": "360 - 120 = 240",
        "planted_final": 3.89,
    },
    {
        "problem_id": "P10",
        "problem_text": (
            "A class has 30 students. 12 play football, 10 play basketball, "
            "and 5 play both. How many students play neither sport?"
        ),
        "correct_answer": 13,
        "correct_steps": [
            "Step 1: Football or basketball = 12 + 10 - 5 = 17",
            "Step 2: Neither = 30 - 17 = 13",
        ],
        "injection_step": 1,
        "wrong_value": "12 + 10 - 5 = 19",
        "right_value": "12 + 10 - 5 = 17",
        "planted_final": 11,
    },
]


# ─── helpers ──────────────────────────────────────────────────────────────────

def load_token():
    with open(KRONOS_TOKEN_PATH) as f:
        return f.read().strip()


def call_kronos(prompt: str, token: str, timeout: int = 60) -> str:
    payload = json.dumps({
        "model": CLOSED_LOOP_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 300,
    }).encode()
    req = urllib.request.Request(
        KRONOS_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def call_ollama(prompt: str, timeout: int = 60) -> str:
    payload = json.dumps({
        "model": EXTERNAL_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 300,
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def build_flawed_solution(p: dict) -> str:
    """Build the planted-error solution string for a problem."""
    steps = list(p["correct_steps"])
    # Replace right_value with wrong_value at injection_step (1-indexed)
    idx = p["injection_step"] - 1
    steps[idx] = steps[idx].replace(p["right_value"], p["wrong_value"])
    # Propagate the wrong final answer into the last step if it differs
    if p["planted_final"] != p["correct_answer"]:
        # Update the last step to show wrong final if it contains the correct answer
        last = steps[-1]
        ca_str = str(p["correct_answer"])
        pf_str = str(p["planted_final"])
        if ca_str in last:
            steps[-1] = last.replace(ca_str, pf_str)
    return "\n".join(steps)


GRADING_PROMPT = """You are a math checker. A student attempted the following problem.

PROBLEM:
{problem}

STUDENT SOLUTION:
{solution}

First line of your response MUST be exactly CORRECT or INCORRECT (one word only).
Then list any errors found, specifying which step number contains the error and what the correct value should be.
"""


def parse_verdict(response: str, p: dict) -> tuple[str, bool]:
    """
    Returns (verdict_str, caught_bool).
    caught = True if response starts with INCORRECT AND mentions the injection step or wrong value.
    """
    first_line = response.strip().split("\n")[0].strip().upper()
    if first_line.startswith("INCORRECT"):
        verdict = "INCORRECT"
    elif first_line.startswith("CORRECT"):
        verdict = "CORRECT"
    else:
        # Try harder
        if "INCORRECT" in response[:50].upper():
            verdict = "INCORRECT"
        elif "CORRECT" in response[:50].upper():
            verdict = "CORRECT"
        else:
            verdict = "UNKNOWN"

    if verdict != "INCORRECT":
        return verdict, False

    # Check if step reference or wrong value is mentioned
    step_str = str(p["injection_step"])
    wrong_val = p["wrong_value"]
    # Extract the numeric wrong result (e.g., "40" from "24 + 18 = 40")
    wrong_num = wrong_val.split("=")[-1].strip().rstrip("km$ ").strip()

    resp_lower = response.lower()
    step_mentioned = (
        f"step {step_str}" in resp_lower
        or f"step{step_str}" in resp_lower
    )
    value_mentioned = wrong_num in response

    caught = step_mentioned or value_mentioned
    return verdict, caught


def append_trial(trial: dict):
    with open(TRIALS_PATH, "a") as f:
        f.write(json.dumps(trial) + "\n")


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    token = load_token()
    pre_reg_ts = datetime.now(timezone.utc).isoformat()

    # Write pre-registration record first (before any API calls)
    pre_reg_record = {
        "type": "pre_registration",
        "timestamp": pre_reg_ts,
        **PRE_REG,
    }
    # Clear trials file and write pre-reg
    with open(TRIALS_PATH, "w") as f:
        f.write(json.dumps(pre_reg_record) + "\n")

    print(f"[E30] Pre-registration locked at {pre_reg_ts}")
    print(f"[E30] Promotion criterion: {PRE_REG['promotion_criterion'][:80]}...")

    results = []
    cl_indeterminate = 0
    ext_indeterminate = 0

    for p in PROBLEMS:
        pid = p["problem_id"]
        flawed_solution = build_flawed_solution(p)
        prompt = GRADING_PROMPT.format(
            problem=p["problem_text"],
            solution=flawed_solution,
        )

        print(f"\n[E30] {pid} — injection at Step {p['injection_step']}: {p['wrong_value']} (correct: {p['right_value']})")
        print(f"  Flawed solution:\n    {flawed_solution.replace(chr(10), chr(10)+'    ')}")

        # ── closed-loop: kronos qwen-32b grades its own model's solution ──
        cl_verdict = "UNKNOWN"
        cl_caught = False
        cl_response = ""
        for attempt in range(2):
            try:
                cl_response = call_kronos(prompt, token, timeout=90)
                cl_verdict, cl_caught = parse_verdict(cl_response, p)
                break
            except Exception as e:
                print(f"  [closed-loop] attempt {attempt+1} failed: {e}")
                if attempt == 1:
                    cl_verdict = "INDETERMINATE"
                    cl_indeterminate += 1
                else:
                    time.sleep(3)

        print(f"  [closed-loop] verdict={cl_verdict}, caught={cl_caught}")
        print(f"    response[0:120]: {cl_response[:120]!r}")

        # ── external: llama3.1:8b at local ollama ──
        ext_verdict = "UNKNOWN"
        ext_caught = False
        ext_response = ""
        for attempt in range(2):
            try:
                ext_response = call_ollama(prompt, timeout=90)
                ext_verdict, ext_caught = parse_verdict(ext_response, p)
                break
            except Exception as e:
                print(f"  [external] attempt {attempt+1} failed: {e}")
                if attempt == 1:
                    ext_verdict = "INDETERMINATE"
                    ext_indeterminate += 1
                else:
                    time.sleep(3)

        print(f"  [external] verdict={ext_verdict}, caught={ext_caught}")
        print(f"    response[0:120]: {ext_response[:120]!r}")

        trial = {
            "problem_id": pid,
            "problem_text": p["problem_text"],
            "correct_answer": p["correct_answer"],
            "flawed_solution": flawed_solution,
            "injection_step": p["injection_step"],
            "wrong_value": p["wrong_value"],
            "right_value": p["right_value"],
            "planted_final": p["planted_final"],
            "closed_loop_verdict": cl_verdict,
            "closed_loop_caught_error": cl_caught,
            "closed_loop_response_snippet": cl_response[:300],
            "external_verdict": ext_verdict,
            "external_caught_error": ext_caught,
            "external_response_snippet": ext_response[:300],
        }
        results.append(trial)
        append_trial(trial)

    # ── scoring ──────────────────────────────────────────────────────────────
    n = len(results)
    cl_caught_count = sum(1 for r in results if r["closed_loop_caught_error"])
    ext_caught_count = sum(1 for r in results if r["external_caught_error"])

    cl_catch_rate = cl_caught_count / n
    ext_catch_rate = ext_caught_count / n

    # ── verdict ──────────────────────────────────────────────────────────────
    if cl_indeterminate / n > 0.2 or ext_indeterminate / n > 0.2:
        verdict = "INDETERMINATE"
        verdict_reasoning = (
            f"Too many indeterminate calls: closed_loop={cl_indeterminate}/10, "
            f"external={ext_indeterminate}/10. >20% threshold exceeded."
        )
    elif cl_catch_rate >= 0.8:
        verdict = "FALSIFIED"
        verdict_reasoning = (
            f"Closed-loop caught {cl_catch_rate:.0%} of planted errors, "
            f"meeting the ≥80% falsification threshold. Thesis 2 is FALSIFIED: "
            f"a self-grading closed loop CAN reliably catch its own errors."
        )
    elif cl_catch_rate <= 0.5 and ext_catch_rate >= 0.8:
        verdict = "PROMOTE TO SETTLED"
        verdict_reasoning = (
            f"Closed-loop catch rate={cl_catch_rate:.0%} (≤50% criterion met) and "
            f"external catch rate={ext_catch_rate:.0%} (≥80% criterion met). "
            f"Both conditions satisfied. Thesis 2 promoted from hypothesis to settled: "
            f"coherence ≠ correctness; outside check is what converges."
        )
    else:
        verdict = "STAYS HYPOTHESIS"
        verdict_reasoning = (
            f"Promotion criterion not met. Closed-loop catch rate={cl_catch_rate:.0%} "
            f"(need ≤50%), external catch rate={ext_catch_rate:.0%} (need ≥80%). "
            f"Neither falsification nor promotion thresholds reached."
        )

    # ── output ───────────────────────────────────────────────────────────────
    output = {
        "experiment": "E30 — Thesis 2 closed-loop vs external grader promotion attempt",
        "thesis": "coherence != correctness; outside check is what converges",
        "promotion_criterion": PRE_REG["promotion_criterion"],
        "falsifier": PRE_REG["falsifier"],
        "pre_registration_timestamp": pre_reg_ts,
        "closed_loop_model": CLOSED_LOOP_MODEL,
        "external_model": EXTERNAL_MODEL,
        "n_problems": n,
        "problems": [
            {
                "problem_id": r["problem_id"],
                "problem_text": r["problem_text"],
                "correct_answer": r["correct_answer"],
                "injection_step": r["injection_step"],
                "wrong_value": r["wrong_value"],
                "right_value": r["right_value"],
                "closed_loop_verdict": r["closed_loop_verdict"],
                "closed_loop_caught_error": r["closed_loop_caught_error"],
                "external_verdict": r["external_verdict"],
                "external_caught_error": r["external_caught_error"],
            }
            for r in results
        ],
        "closed_loop_catch_rate": round(cl_catch_rate, 3),
        "external_catch_rate": round(ext_catch_rate, 3),
        "verdict": verdict,
        "verdict_reasoning": verdict_reasoning,
    }

    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*60}")
    print(f"[E30] VERDICT: {verdict}")
    print(f"[E30] Closed-loop catch rate : {cl_catch_rate:.0%} ({cl_caught_count}/{n})")
    print(f"[E30] External catch rate    : {ext_catch_rate:.0%} ({ext_caught_count}/{n})")
    print(f"[E30] Gap                    : {ext_catch_rate - cl_catch_rate:+.0%}")
    print(f"[E30] Results: {RESULTS_PATH}")
    print(f"{'='*60}")

    return output


if __name__ == "__main__":
    main()
