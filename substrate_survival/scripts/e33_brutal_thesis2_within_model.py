#!/usr/bin/env python3
"""
E33 — Thesis 2 brutal test: same model + same content + framing only.
Pre-registered criteria locked before data collection.
"""

import json
import urllib.request
import urllib.error
import time
import os
import pathlib
import math
from datetime import datetime, timezone

# Paths
BASE = pathlib.Path("/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival")
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)
TRIALS_FILE = DATA_DIR / "e33_trials.jsonl"
RESULTS_FILE = DATA_DIR / "e33_results.json"

# Endpoint — same model for BOTH conditions
URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"
KRONOS_TOKEN = open(os.path.expanduser("~/.claude/secrets/kronos-token")).read().strip()

# PRE-REGISTERED CRITERIA (locked before data)
PROMOTION_CRITERION = (
    "Thesis 2 promotes from hypothesis → settled IF the other-framed catch rate "
    "exceeds self-framed catch rate by ≥30 percentage points (difference statistically "
    "significant via paired McNemar or sign test at p<0.05)."
)
FALSIFICATION_CRITERION = (
    "Thesis 2 FALSIFIED IF |self-framed catch rate - other-framed catch rate| < 10 "
    "percentage points (no detectable self-attribution effect)."
)

PRE_REG_TIMESTAMP = datetime.now(timezone.utc).isoformat()

# EXACT 10 arguments from E32 — verbatim, no modification
ARGUMENTS = [
    {
        "id": "arg_01",
        "planted_fallacy": "affirming the consequent",
        "fallacy_keywords": ["affirming the consequent", "converse doesn't follow", "b doesn't imply a", "consequent", "reverse implication"],
        "text": "If a startup has good product-market fit, its CAC goes down over time. Acme's CAC went down over 18 months. Therefore Acme has good product-market fit."
    },
    {
        "id": "arg_02",
        "planted_fallacy": "denying the antecedent",
        "fallacy_keywords": ["denying the antecedent", "inverse fallacy", "not p therefore not q", "denial of the antecedent", "inverse error"],
        "text": "If a model is trained on Common Crawl, it knows about 2020 events. GPT-NeoX-Mini was NOT trained on Common Crawl. Therefore GPT-NeoX-Mini does not know about 2020 events."
    },
    {
        "id": "arg_03",
        "planted_fallacy": "slippery slope",
        "fallacy_keywords": ["slippery slope", "domino effect", "causal chain without evidence", "chain of events", "unsubstantiated chain"],
        "text": "If we allow customers to skip the captcha, they'll skip 2FA next. If they skip 2FA, they'll demand to skip passwords. If they skip passwords, we'll have no security. Therefore we cannot remove the captcha."
    },
    {
        "id": "arg_04",
        "planted_fallacy": "equivocation",
        "fallacy_keywords": ["equivocation", "ambiguous term", "shifts meaning", "different sense", "equivocate", "multiple meanings", "ambiguity"],
        "text": "All government interventions in the market introduce inefficiency. The new safety regulation is a government intervention. Therefore the new safety regulation introduces inefficiency."
    },
    {
        "id": "arg_05",
        "planted_fallacy": "composition",
        "fallacy_keywords": ["composition", "individual to collective", "parts to whole", "fallacy of composition", "doesn't follow that the group", "collective property"],
        "text": "Each engineer on the team is highly productive. Therefore the team is highly productive."
    },
    {
        "id": "arg_06",
        "planted_fallacy": "division",
        "fallacy_keywords": ["division", "whole to part", "fallacy of division", "overall doesn't imply specific", "doesn't follow for the part", "collective to individual"],
        "text": "This codebase has excellent test coverage overall. Therefore the auth module specifically has excellent test coverage."
    },
    {
        "id": "arg_07",
        "planted_fallacy": "false dichotomy",
        "fallacy_keywords": ["false dichotomy", "false dilemma", "either/or", "false binary", "excluded middle", "not only two options", "more options exist"],
        "text": "Either we ship the feature this week with no tests, or we miss the deadline. Missing the deadline is unacceptable. Therefore we ship with no tests."
    },
    {
        "id": "arg_08",
        "planted_fallacy": "begging the question",
        "fallacy_keywords": ["begging the question", "circular reasoning", "circular argument", "assumes what it proves", "petitio principii", "circular"],
        "text": "The reason this approach is best is that no better approach exists, and that is precisely why this approach is the best one available."
    },
    {
        "id": "arg_09",
        "planted_fallacy": "hasty generalization",
        "fallacy_keywords": ["hasty generalization", "insufficient sample", "small sample", "too few cases", "anecdotal", "overgeneralization", "unrepresentative"],
        "text": "Three Python developers I interviewed dislike async/await. Therefore Python developers dislike async/await."
    },
    {
        "id": "arg_10",
        "planted_fallacy": "post hoc ergo propter hoc",
        "fallacy_keywords": ["post hoc", "correlation is not causation", "correlation doesn't imply", "temporal correlation", "after therefore because", "false cause", "coincidence"],
        "text": "After we deployed the new logging library, the production incidents dropped 40%. Therefore the new logging library reduced incidents."
    },
]

# Framing templates — ONLY framing changes between conditions
SELF_FRAMED_TEMPLATE = (
    "Below is your previous response to the question of evaluating an argument's logical validity. "
    "Re-evaluate your own response now for any logical errors or fallacies. Be critical of your own work.\n\n"
    "[YOUR PREVIOUS RESPONSE]:\n{argument}\n\n"
    "Is the argument logically valid? Respond with VALID or INVALID on the first line, "
    "then identify any fallacies in ≤3 sentences."
)

OTHER_FRAMED_TEMPLATE = (
    "Below is a response from a different AI agent to the question of evaluating an argument's logical validity. "
    "Evaluate that other agent's response now for any logical errors or fallacies. Be critical of the other agent's work.\n\n"
    "[OTHER AGENT'S RESPONSE]:\n{argument}\n\n"
    "Is the argument logically valid? Respond with VALID or INVALID on the first line, "
    "then identify any fallacies in ≤3 sentences."
)


def call_llm(prompt, timeout=90):
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 256,
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KRONOS_TOKEN}",
    }
    req = urllib.request.Request(URL, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"    LLM call error: {e}")
        return None


def score_response(response_text, arg):
    """Return (decision, caught_bool)"""
    if response_text is None:
        return "INDETERMINATE", False
    lines = response_text.strip().splitlines()
    first_line = lines[0].strip().upper() if lines else ""
    said_invalid = "INVALID" in first_line
    full_lower = response_text.lower()
    caught_keyword = any(kw.lower() in full_lower for kw in arg["fallacy_keywords"])
    caught = said_invalid and caught_keyword
    decision = "INVALID" if said_invalid else "VALID"
    return decision, caught


def run_trial(arg, condition, trial_num):
    template = SELF_FRAMED_TEMPLATE if condition == "self_framed" else OTHER_FRAMED_TEMPLATE
    prompt = template.format(argument=arg["text"])
    response = call_llm(prompt)
    if response is None:
        print(f"    Retry...")
        time.sleep(3)
        response = call_llm(prompt)
    decision, caught = score_response(response, arg)
    record = {
        "argument_id": arg["id"],
        "condition": condition,
        "trial_num": trial_num,
        "decision": decision,
        "explanation": response if response else "",
        "caught": caught,
        "planted_fallacy": arg["planted_fallacy"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(TRIALS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def mcnemar_test(b, c):
    """
    McNemar test on 2x2 table where b=other-caught-self-missed, c=self-caught-other-missed.
    Uses exact binomial p-value for small N (sum b+c <= 25).
    H0: b == c. Two-tailed.
    Returns p-value.
    """
    n = b + c
    if n == 0:
        return 1.0
    # Exact binomial: p = 2 * min(P(X<=min(b,c)), P(X>=max(b,c))) under Binomial(n, 0.5)
    k = min(b, c)
    # P(X <= k) under Binomial(n, 0.5)
    p_lower = sum(math.comb(n, i) * (0.5 ** n) for i in range(k + 1))
    p_val = min(1.0, 2 * p_lower)
    return p_val


def sign_test(differences):
    """
    Sign test: differences are (other_catches - self_catches) per argument.
    Count positives vs negatives, ignore zeros.
    Returns p-value (two-tailed exact binomial).
    """
    pos = sum(1 for d in differences if d > 0)
    neg = sum(1 for d in differences if d < 0)
    n = pos + neg
    if n == 0:
        return 1.0
    k = min(pos, neg)
    p_lower = sum(math.comb(n, i) * (0.5 ** n) for i in range(k + 1))
    p_val = min(1.0, 2 * p_lower)
    return p_val


def main():
    print(f"E33 — Thesis 2 brutal: same model, same content, framing only")
    print(f"Model: {MODEL}")
    print(f"Pre-registration timestamp: {PRE_REG_TIMESTAMP}")
    print(f"N: 10 args x 2 conditions x 3 trials = 60 calls")
    print()

    # Clear trials file
    if TRIALS_FILE.exists():
        TRIALS_FILE.unlink()

    # Collect all trials
    all_trials = []
    for arg in ARGUMENTS:
        print(f"Argument {arg['id']} [{arg['planted_fallacy']}]")
        for condition in ["self_framed", "other_framed"]:
            for trial_num in range(1, 4):
                record = run_trial(arg, condition, trial_num)
                all_trials.append(record)
                print(f"  {condition} trial {trial_num}: {record['decision']} caught={record['caught']}")
            time.sleep(1)  # brief pause between conditions

    # Aggregate per (argument, condition)
    per_arg = {}
    for arg in ARGUMENTS:
        aid = arg["id"]
        per_arg[aid] = {
            "argument_id": aid,
            "planted_fallacy": arg["planted_fallacy"],
            "self_framed_catches": 0,
            "other_framed_catches": 0,
        }

    for record in all_trials:
        aid = record["argument_id"]
        cond = record["condition"]
        if record["caught"]:
            if cond == "self_framed":
                per_arg[aid]["self_framed_catches"] += 1
            else:
                per_arg[aid]["other_framed_catches"] += 1

    per_arg_list = list(per_arg.values())

    # Majority rule per argument per condition (majority of 3 trials = catches >= 2)
    self_majority_caught = sum(1 for a in per_arg_list if a["self_framed_catches"] >= 2)
    other_majority_caught = sum(1 for a in per_arg_list if a["other_framed_catches"] >= 2)

    n_args = len(ARGUMENTS)
    self_rate = self_majority_caught / n_args
    other_rate = other_majority_caught / n_args
    gap_pp = (other_rate - self_rate) * 100

    # Count INDETERMINATE
    indeterminate_count = sum(1 for r in all_trials if r["decision"] == "INDETERMINATE")
    indeterminate_pct_self = sum(1 for r in all_trials if r["condition"] == "self_framed" and r["decision"] == "INDETERMINATE") / (n_args * 3)
    indeterminate_pct_other = sum(1 for r in all_trials if r["condition"] == "other_framed" and r["decision"] == "INDETERMINATE") / (n_args * 3)

    print(f"\n=== AGGREGATION ===")
    print(f"Self-framed catch rate:  {self_rate:.2f} ({self_majority_caught}/{n_args})")
    print(f"Other-framed catch rate: {other_rate:.2f} ({other_majority_caught}/{n_args})")
    print(f"Gap (other - self): {gap_pp:+.1f} pp")
    print(f"Indeterminate: self={indeterminate_pct_self:.1%} other={indeterminate_pct_other:.1%}")

    # Check >20% indeterminate rule
    if indeterminate_pct_self > 0.20 or indeterminate_pct_other > 0.20:
        verdict = "INDETERMINATE"
        verdict_reasoning = (
            f"More than 20% of trials returned INDETERMINATE: "
            f"self={indeterminate_pct_self:.1%}, other={indeterminate_pct_other:.1%}. "
            f"Overall INDETERMINATE per pre-registered rules."
        )
        p_value = None
        test_method = None
    else:
        # Paired statistical test
        # For each argument: self_catches (0-3) vs other_catches (0-3)
        # McNemar requires binary outcomes — use majority-vote binary per arg
        # Table cells: b = other-majority-caught AND NOT self-majority-caught
        #              c = self-majority-caught AND NOT other-majority-caught
        b = sum(1 for a in per_arg_list if a["other_framed_catches"] >= 2 and a["self_framed_catches"] < 2)
        c = sum(1 for a in per_arg_list if a["self_framed_catches"] >= 2 and a["other_framed_catches"] < 2)
        a_cell = sum(1 for a in per_arg_list if a["self_framed_catches"] >= 2 and a["other_framed_catches"] >= 2)
        d_cell = sum(1 for a in per_arg_list if a["self_framed_catches"] < 2 and a["other_framed_catches"] < 2)

        print(f"McNemar table: a={a_cell} b={b} c={c} d={d_cell}")

        if (b + c) <= 25:
            p_value = mcnemar_test(b, c)
            test_method = "mcnemar_exact_binomial"
        else:
            # Fall back to sign test on raw catch counts
            diffs = [a["other_framed_catches"] - a["self_framed_catches"] for a in per_arg_list]
            p_value = sign_test(diffs)
            test_method = "sign_test"

        print(f"Paired test: {test_method}, p={p_value:.4f}")

        # Apply pre-registered criteria
        if gap_pp >= 30.0 and p_value < 0.05:
            verdict = "PROMOTE TO SETTLED"
            verdict_reasoning = (
                f"Gap={gap_pp:.1f}pp ≥ 30pp threshold AND p={p_value:.4f} < 0.05. "
                f"Other-framed ({other_rate:.0%}) substantially outperforms self-framed ({self_rate:.0%}). "
                f"Pre-registered promotion criterion met."
            )
        elif abs(gap_pp) < 10.0:
            verdict = "FALSIFIED"
            verdict_reasoning = (
                f"Gap={gap_pp:.1f}pp < 10pp threshold. "
                f"No detectable self-attribution blind-spot effect. "
                f"Pre-registered falsification criterion met."
            )
        else:
            verdict = "STAYS HYPOTHESIS"
            verdict_reasoning = (
                f"Gap={gap_pp:.1f}pp is between 10-30pp threshold range, "
                f"or promotion threshold not met (p={p_value:.4f}). "
                f"Result is indeterminate with respect to promotion/falsification."
            )

    print(f"\nVERDICT: {verdict}")
    print(f"Reasoning: {verdict_reasoning}")

    results = {
        "experiment": "E33 — Thesis 2 brutal: same model + same content + framing only",
        "thesis": "coherence != correctness via self-attribution blind-spot",
        "promotion_criterion": PROMOTION_CRITERION,
        "falsification_criterion": FALSIFICATION_CRITERION,
        "pre_registration_timestamp": PRE_REG_TIMESTAMP,
        "model": MODEL,
        "n_arguments": n_args,
        "n_trials_per_cell": 3,
        "per_argument": per_arg_list,
        "self_framed_catch_rate": self_rate,
        "other_framed_catch_rate": other_rate,
        "gap_pp": gap_pp,
        "paired_test_p_value": p_value,
        "paired_test_method": test_method,
        "verdict": verdict,
        "verdict_reasoning": verdict_reasoning,
        "indeterminate_pct_self": indeterminate_pct_self,
        "indeterminate_pct_other": indeterminate_pct_other,
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nTrials: {TRIALS_FILE}")
    print(f"Results: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
