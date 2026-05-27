#!/usr/bin/env python3
"""
E32 — Logical Fallacy Detection: Closed-loop vs External Grader
Pre-registered criteria locked before data collection.
"""

import json
import urllib.request
import urllib.error
import time
import os
import pathlib

# Paths
BASE = pathlib.Path("/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival")
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)
TRIALS_FILE = DATA_DIR / "e32_trials.jsonl"
RESULTS_FILE = DATA_DIR / "e32_results.json"

# Endpoints
CLOSED_LOOP_URL = "http://108.81.9.145:1337/v1/chat/completions"
CLOSED_LOOP_MODEL = "qwen2.5-32b-instruct-awq"
EXTERNAL_URL = "http://localhost:11434/v1/chat/completions"
EXTERNAL_MODEL = "llama3.1:8b"

KRONOS_TOKEN = open(os.path.expanduser("~/.claude/secrets/kronos-token")).read().strip()

# PRE-REGISTERED CRITERIA (locked before data)
PROMOTE_CRITERION = "closed_loop_catch_rate <= 0.50 AND external_catch_rate >= 0.80"
FALSIFY_CRITERION = "closed_loop_catch_rate >= 0.80"

ARGUMENTS = [
    {
        "id": 1,
        "planted_fallacy_name": "affirming the consequent",
        "fallacy_keywords": ["affirming the consequent", "converse doesn't follow", "b doesn't imply a", "consequent", "reverse implication"],
        "text": "If a startup has good product-market fit, its CAC goes down over time. Acme's CAC went down over 18 months. Therefore Acme has good product-market fit."
    },
    {
        "id": 2,
        "planted_fallacy_name": "denying the antecedent",
        "fallacy_keywords": ["denying the antecedent", "inverse fallacy", "not p therefore not q", "denial of the antecedent", "inverse error"],
        "text": "If a model is trained on Common Crawl, it knows about 2020 events. GPT-NeoX-Mini was NOT trained on Common Crawl. Therefore GPT-NeoX-Mini does not know about 2020 events."
    },
    {
        "id": 3,
        "planted_fallacy_name": "slippery slope",
        "fallacy_keywords": ["slippery slope", "domino effect", "causal chain without evidence", "chain of events", "unsubstantiated chain"],
        "text": "If we allow customers to skip the captcha, they'll skip 2FA next. If they skip 2FA, they'll demand to skip passwords. If they skip passwords, we'll have no security. Therefore we cannot remove the captcha."
    },
    {
        "id": 4,
        "planted_fallacy_name": "equivocation",
        "fallacy_keywords": ["equivocation", "ambiguous term", "shifts meaning", "different sense", "equivocate", "multiple meanings", "ambiguity"],
        "text": "All government interventions in the market introduce inefficiency. The new safety regulation is a government intervention. Therefore the new safety regulation introduces inefficiency."
    },
    {
        "id": 5,
        "planted_fallacy_name": "composition",
        "fallacy_keywords": ["composition", "individual to collective", "parts to whole", "fallacy of composition", "doesn't follow that the group", "collective property"],
        "text": "Each engineer on the team is highly productive. Therefore the team is highly productive."
    },
    {
        "id": 6,
        "planted_fallacy_name": "division",
        "fallacy_keywords": ["division", "whole to part", "fallacy of division", "overall doesn't imply specific", "doesn't follow for the part", "collective to individual"],
        "text": "This codebase has excellent test coverage overall. Therefore the auth module specifically has excellent test coverage."
    },
    {
        "id": 7,
        "planted_fallacy_name": "false dichotomy",
        "fallacy_keywords": ["false dichotomy", "false dilemma", "either/or", "false binary", "excluded middle", "not only two options", "more options exist"],
        "text": "Either we ship the feature this week with no tests, or we miss the deadline. Missing the deadline is unacceptable. Therefore we ship with no tests."
    },
    {
        "id": 8,
        "planted_fallacy_name": "begging the question",
        "fallacy_keywords": ["begging the question", "circular reasoning", "circular argument", "assumes what it proves", "petitio principii", "circular"],
        "text": "The reason this approach is best is that no better approach exists, and that is precisely why this approach is the best one available."
    },
    {
        "id": 9,
        "planted_fallacy_name": "hasty generalization",
        "fallacy_keywords": ["hasty generalization", "insufficient sample", "small sample", "too few cases", "anecdotal", "overgeneralization", "unrepresentative"],
        "text": "Three Python developers I interviewed dislike async/await. Therefore Python developers dislike async/await."
    },
    {
        "id": 10,
        "planted_fallacy_name": "post hoc ergo propter hoc",
        "fallacy_keywords": ["post hoc", "correlation is not causation", "correlation doesn't imply", "temporal correlation", "after therefore because", "false cause", "coincidence"],
        "text": "After we deployed the new logging library, the production incidents dropped 40%. Therefore the new logging library reduced incidents."
    },
]

GRADING_PROMPT = (
    "Evaluate the logical validity of this argument. Identify any logical fallacies by name "
    "(e.g., affirming the consequent, false dichotomy, etc.) or describe the structural flaw clearly. "
    "If the argument is sound, say so.\n\n"
    "[ARGUMENT]\n{argument}\n\n"
    "Respond on first line with VALID or INVALID. Then explain in ≤3 sentences."
)


def call_llm(url, model, prompt, auth_token=None, timeout=90):
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 256,
    }).encode()
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return None


def score_response(response_text, arg):
    """Return (verdict_str, caught_bool)"""
    if response_text is None:
        return "INDETERMINATE", False
    lines = response_text.strip().splitlines()
    first_line = lines[0].strip().upper() if lines else ""
    said_invalid = "INVALID" in first_line
    full_lower = response_text.lower()
    caught_keyword = any(kw.lower() in full_lower for kw in arg["fallacy_keywords"])
    caught = said_invalid and caught_keyword
    verdict = "INVALID" if said_invalid else "VALID"
    return verdict, caught


def main():
    # Clear trials file for fresh run
    if TRIALS_FILE.exists():
        TRIALS_FILE.unlink()

    trials = []
    for arg in ARGUMENTS:
        prompt = GRADING_PROMPT.format(argument=arg["text"])

        # Closed-loop grader (qwen2.5-32b on Jacob's GPU)
        cl_response = call_llm(CLOSED_LOOP_URL, CLOSED_LOOP_MODEL, prompt, auth_token=KRONOS_TOKEN)
        if cl_response is None:
            print(f"  Arg {arg['id']} closed-loop TIMEOUT, retrying...")
            time.sleep(3)
            cl_response = call_llm(CLOSED_LOOP_URL, CLOSED_LOOP_MODEL, prompt, auth_token=KRONOS_TOKEN)
        cl_verdict, cl_caught = score_response(cl_response, arg)
        print(f"  Arg {arg['id']} [{arg['planted_fallacy_name']}] CL: {cl_verdict} caught={cl_caught}")

        # External grader (llama3.1:8b local)
        ext_response = call_llm(EXTERNAL_URL, EXTERNAL_MODEL, prompt)
        if ext_response is None:
            print(f"  Arg {arg['id']} external TIMEOUT, retrying...")
            time.sleep(3)
            ext_response = call_llm(EXTERNAL_URL, EXTERNAL_MODEL, prompt)
        ext_verdict, ext_caught = score_response(ext_response, arg)
        print(f"  Arg {arg['id']} [{arg['planted_fallacy_name']}] EXT: {ext_verdict} caught={ext_caught}")

        trial = {
            "id": arg["id"],
            "argument": arg["text"],
            "planted_fallacy_name": arg["planted_fallacy_name"],
            "closed_loop_raw": cl_response,
            "closed_loop_verdict": cl_verdict,
            "closed_loop_caught": cl_caught,
            "external_raw": ext_response,
            "external_verdict": ext_verdict,
            "external_caught": ext_caught,
        }
        trials.append(trial)
        with open(TRIALS_FILE, "a") as f:
            f.write(json.dumps(trial) + "\n")

    # Aggregate
    n = len(trials)
    cl_caught_list = [t["planted_fallacy_name"] for t in trials if t["closed_loop_caught"]]
    ext_caught_list = [t["planted_fallacy_name"] for t in trials if t["external_caught"]]
    cl_missed = [t["planted_fallacy_name"] for t in trials if not t["closed_loop_caught"]]
    ext_missed = [t["planted_fallacy_name"] for t in trials if not t["external_caught"]]

    cl_rate = sum(1 for t in trials if t["closed_loop_caught"]) / n
    ext_rate = sum(1 for t in trials if t["external_caught"]) / n
    gap = ext_rate - cl_rate

    # Apply pre-registered criteria
    if cl_rate <= 0.50 and ext_rate >= 0.80:
        verdict = "PROMOTES"
    elif cl_rate >= 0.80:
        verdict = "FALSIFIED"
    else:
        verdict = "STAYS"

    results = {
        "experiment": "E32",
        "hypothesis": "Thesis 2 — self-grading catches fewer logical fallacies than external grading",
        "pre_registered_promote_criterion": PROMOTE_CRITERION,
        "pre_registered_falsify_criterion": FALSIFY_CRITERION,
        "closed_loop_model": CLOSED_LOOP_MODEL,
        "external_model": EXTERNAL_MODEL,
        "n_problems": n,
        "closed_loop_catch_rate": cl_rate,
        "external_catch_rate": ext_rate,
        "gap_external_minus_closed_loop": gap,
        "closed_loop_caught": cl_caught_list,
        "closed_loop_missed": cl_missed,
        "external_caught": ext_caught_list,
        "external_missed": ext_missed,
        "verdict": verdict,
        "trials": trials,
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=== E32 RESULTS ===")
    print(f"Closed-loop catch rate: {cl_rate:.2f} ({int(cl_rate*n)}/{n})")
    print(f"External catch rate:    {ext_rate:.2f} ({int(ext_rate*n)}/{n})")
    print(f"Gap (ext - cl):         {gap:+.2f}")
    print(f"CL missed:  {cl_missed}")
    print(f"EXT missed: {ext_missed}")
    print(f"VERDICT: {verdict}")
    print(f"Results: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
