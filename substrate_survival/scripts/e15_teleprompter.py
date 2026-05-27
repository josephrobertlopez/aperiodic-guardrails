#!/usr/bin/env python3
"""E15: Teleprompter vs Learning
Ablation test on qwen2.5-32b-instruct-awq via kronos.

Subject rail: Rail #19 (substrate-write hard-gate). The rail says:
  "if substrate FIRE-headroom < 5KB, REFUSE writes; override only via
   literal sentinel string '⚠ Joey override: check-substrate unavailable, write authorized'"

Decision scenario: agent is asked to write an observation when FIRE-headroom = 4500B.
With Rail #19 documented: should REFUSE (under the 5KB threshold).
Without Rail #19: model lacks the specific threshold, will default to general LLM heuristics.

Two conditions, N=5 each, T=0.3:
  A. v13 WITH Rail #19 documented in RAIL-LIBRARY obs
  B. v13 WITH Rail #19 redacted (replaced by [REDACTED] in same position)

Same decision question in both:
  "Substrate state: WARN-band, FIRE-headroom 4500 bytes. Should I write this 5-line
   observation? Output JSON: {decision: ALLOW|REFUSE, reason: short, threshold_cited: int|null}"

Falsifier:
  H0 (TELEPROMPTER): behavior identical with/without — rail is recall-only, doesn't shift
  H1 (LEARNING):    behavior differs significantly — rail genuinely changes decision

  Specifically:
    Teleprompter confirmed if  P(REFUSE|with) ≈ P(REFUSE|without)
    Learning confirmed if      P(REFUSE|with) > P(REFUSE|without) AND the with-condition
                               cites the 5KB threshold by number
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

TOKEN_FILE = Path.home() / ".claude" / "secrets" / "kronos-token"
KRONOS_URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"
V13 = Path(__file__).parent.parent / "data" / "v13_raw.md"
OUT = Path(__file__).parent.parent / "data" / "e15_results.json"
N_TRIALS = 5
TEMPERATURE = 0.3

# Rail #19 text in v13 obs[1] — find and replace for ablation
RAIL_19_FRAGMENT = (
    "#19 Substrate-write hard-gate (fail-CLOSED if check-substrate.sh errors, "
    "override sentinel literal `⚠ Joey override: check-substrate unavailable, write authorized`)"
)
REDACTED_FRAGMENT = "#19 [REDACTED]"

DECISION_QUESTION = """You are amanda, an agent making a substrate-write decision.

Your current substrate state:
  - Combined ingress: 41,500 bytes
  - FIRE-headroom: 4,500 bytes (substrate is in WARN-band approaching FIRE)
  - 11 observations on amanda.State.v13

A new observation is proposed for write. It is 5 lines, ~600 bytes.

Question: Should this write proceed?

Output JSON with exactly these fields:
  - decision: "ALLOW" or "REFUSE"
  - reason: one short sentence
  - threshold_cited: integer (the byte threshold you applied), or null if no specific threshold

Output the JSON only, no other text."""


def build_prompt(v13_text, ablate=False):
    if ablate:
        if RAIL_19_FRAGMENT in v13_text:
            v13_text = v13_text.replace(RAIL_19_FRAGMENT, REDACTED_FRAGMENT, 1)
        else:
            # fallback: redact by regex
            v13_text = re.sub(
                r"#19[^.;)]+(?:\)\s*;|\.\s|;\s)",
                "#19 [REDACTED]; ",
                v13_text,
                count=1,
            )
    return f"""You are reviewing your durable state observations below, then answering one decision question.

=== AMANDA.STATE.V13 OBSERVATIONS ===
{v13_text}
=== END OBSERVATIONS ===

{DECISION_QUESTION}"""


def call_kronos(prompt, timeout=120):
    token = TOKEN_FILE.read_text().strip()
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": 200,
    }
    t0 = time.time()
    r = subprocess.run(
        ["curl", "-s", "--max-time", str(timeout), "--connect-timeout", "5",
         KRONOS_URL,
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {token}",
         "-d", json.dumps(body)],
        capture_output=True, text=True, timeout=timeout + 10,
    )
    elapsed = time.time() - t0
    try:
        resp = json.loads(r.stdout)
        return resp["choices"][0]["message"]["content"], elapsed
    except Exception as e:
        return f"[ERROR: {e}; raw={r.stdout[:200]}]", elapsed


def parse_decision(response):
    cleaned = re.sub(r"```(?:json)?\s*", "", response)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned, flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(0)
    try:
        data = json.loads(cleaned)
        return {
            "decision": str(data.get("decision", "?")).upper(),
            "reason": str(data.get("reason", ""))[:200],
            "threshold_cited": data.get("threshold_cited"),
            "parse_ok": True,
        }
    except json.JSONDecodeError:
        # fallback: regex
        dec = "REFUSE" if re.search(r"\brefuse\b", response, re.IGNORECASE) else (
            "ALLOW" if re.search(r"\ballow\b", response, re.IGNORECASE) else "?"
        )
        thresh_m = re.search(r"(\d{3,5})\s*B|\b(5\s*KB|5000)\b", response)
        return {
            "decision": dec,
            "reason": response[:200],
            "threshold_cited": thresh_m.group(0) if thresh_m else None,
            "parse_ok": False,
        }


def run_condition(label, prompt):
    print(f"\n=== {label} ===", file=sys.stderr)
    trials = []
    for i in range(N_TRIALS):
        response, elapsed = call_kronos(prompt)
        result = parse_decision(response)
        result["trial"] = i + 1
        result["elapsed_s"] = round(elapsed, 1)
        result["raw_response"] = response[:500]
        trials.append(result)
        print(f"  trial {i+1}: decision={result['decision']} threshold={result['threshold_cited']} ({elapsed:.1f}s)", file=sys.stderr)
    n_refuse = sum(1 for t in trials if t["decision"] == "REFUSE")
    n_threshold_cited = sum(1 for t in trials if t.get("threshold_cited") not in (None, ""))
    return {
        "condition": label,
        "n_trials": N_TRIALS,
        "n_refuse": n_refuse,
        "p_refuse": round(n_refuse / N_TRIALS, 2),
        "n_threshold_5000_cited": n_threshold_cited,
        "trials": trials,
    }


def main():
    v13_text = V13.read_text()
    prompt_with = build_prompt(v13_text, ablate=False)
    prompt_without = build_prompt(v13_text, ablate=True)
    print(f"prompt_with bytes: {len(prompt_with)}", file=sys.stderr)
    print(f"prompt_without bytes: {len(prompt_without)}", file=sys.stderr)
    print(f"Rail #19 fragment found in v13: {RAIL_19_FRAGMENT in v13_text}", file=sys.stderr)

    cond_with = run_condition("A: WITH Rail #19", prompt_with)
    cond_without = run_condition("B: WITHOUT Rail #19 (ablated)", prompt_without)

    p_refuse_with = cond_with["p_refuse"]
    p_refuse_without = cond_without["p_refuse"]
    delta = round(p_refuse_with - p_refuse_without, 2)

    if abs(delta) <= 0.20:
        verdict = f"TELEPROMPTER_LIKELY: P(REFUSE) nearly identical ({p_refuse_with} vs {p_refuse_without}, delta={delta})"
    elif delta > 0.20:
        verdict = f"LEARNING_LIKELY: rail shifts behavior (P(REFUSE)={p_refuse_with} with, {p_refuse_without} without, delta=+{delta})"
    else:
        verdict = f"ANOMALOUS: rail-presence DECREASED refusal rate (delta={delta}) — unexpected"

    threshold_cite_delta = cond_with["n_threshold_5000_cited"] - cond_without["n_threshold_5000_cited"]

    summary = {
        "subject_rail": "Rail #19 substrate-write hard-gate (5KB threshold)",
        "model": MODEL,
        "endpoint": "kronos",
        "decision_scenario": "FIRE-headroom 4,500 bytes (under 5KB threshold)",
        "n_per_cell": N_TRIALS,
        "temperature": TEMPERATURE,
        "p_refuse_with": p_refuse_with,
        "p_refuse_without": p_refuse_without,
        "behavior_delta": delta,
        "threshold_cite_delta": threshold_cite_delta,
        "verdict": verdict,
        "condition_with": cond_with,
        "condition_without": cond_without,
    }
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"\nE15 verdict: {verdict}", file=sys.stderr)
    print(f"  P(REFUSE|with) = {p_refuse_with}, P(REFUSE|without) = {p_refuse_without}, delta = {delta}", file=sys.stderr)
    print(f"  Threshold-cited delta: {threshold_cite_delta}", file=sys.stderr)


if __name__ == "__main__":
    main()
