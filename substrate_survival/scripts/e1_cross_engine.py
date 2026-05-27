#!/usr/bin/env python3
"""E1: Cross-Engine Extraction Test (kronos / qwen2.5-32b-instruct-awq)
Reads amanda.State.v13 once and answers 8 ground-truth questions in a single eval pass.

Engines compared:
  - Writer-family baseline: Claude Opus 4.7 (this session, scored manually)
  - Portability target:     qwen2.5-32b-instruct-awq at http://108.81.9.145:1337 (kronos)
                            DIFFERENT machine, DIFFERENT family (Qwen vs Anthropic),
                            larger model (32B vs 14B local)

Falsifier (pre-registered):
  >= 6/8 correct = substrate survives external read (PORTABLE)
  <  6/8 correct = substrate Claude-locked (FRAGILE)
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VAULT_FILE = Path(__file__).parent.parent / "data" / "v13_raw.md"
OUT_FILE = Path(__file__).parent.parent / "data" / "e1_results.json"
TOKEN_FILE = Path.home() / ".claude" / "secrets" / "kronos-token"
KRONOS_URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"

GROUND_TRUTH = [
    {"q": "Q1: Most recent state compaction migration in vX -> vY form?",
     "answer": "v12 -> v13",
     "match": lambda r: "v12" in r and "v13" in r},
    {"q": "Q2: Date of v13 compaction in YYYY-MM-DD?",
     "answer": "2026-05-22",
     "match": lambda r: "2026-05-22" in r},
    {"q": "Q3: FIRE-band headroom in bytes that triggered v13 compaction (number only)?",
     "answer": "2842",
     "match": lambda r: "2842" in r},
    {"q": "Q4: Random write-channel sampling rate as percentage (number with %)?",
     "answer": "7%",
     "match": lambda r: bool(re.search(r"\b7\s*%", r)) or "0.07" in r},
    {"q": "Q5: Schemas RATIFIED from first consolidation-pass invocation (number)?",
     "answer": "7",
     "match": lambda r: bool(re.search(r"(^|\D)7($|\D)", r))},
    {"q": "Q6: Schemas CANDIDATE status-capped from first consolidation-pass (number)?",
     "answer": "3",
     "match": lambda r: bool(re.search(r"(^|\D)3($|\D)", r))},
    {"q": "Q7: amanda.Correction.open.v5 observation count (number)?",
     "answer": "10",
     "match": lambda r: bool(re.search(r"(^|\D)10($|\D)", r))},
    {"q": "Q8: List the four percept quartet skill names (comma-separated)?",
     "answer": "check-now, check-activity, check-substrate, check-vault",
     "match": lambda r: all(s in r.lower() for s in ["check-now", "check-activity", "check-substrate", "check-vault"])},
]

PROMPT_TEMPLATE = """Read the following structured agent-memory observations.
Then answer all 8 questions. For each, output exactly one line starting with the question label
(Q1:, Q2:, etc) followed by the answer only. Do not explain.

=== OBSERVATIONS ===
{payload}
=== END OBSERVATIONS ===

Questions:
{questions}

Answers (one per line, Q#: <answer>):"""


def ask_kronos(payload, model=MODEL, timeout=120):
    token = TOKEN_FILE.read_text().strip()
    questions = "\n".join(g["q"] for g in GROUND_TRUTH)
    prompt = PROMPT_TEMPLATE.format(payload=payload, questions=questions)
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 600,
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
        return (
            resp["choices"][0]["message"]["content"].strip(),
            elapsed,
            resp.get("usage", {}),
        )
    except Exception as e:
        return f"[ERROR: {e}; raw_len={len(r.stdout)}; raw_head={r.stdout[:300]}]", elapsed, {}


def parse_responses(response):
    out = {}
    for line in response.splitlines():
        m = re.match(r"^\s*(Q\d)\s*[:.\)]\s*(.+?)\s*$", line)
        if m:
            out[m.group(1).upper()] = m.group(2).strip()
    return out


def main():
    payload = VAULT_FILE.read_text()
    print(f"Payload bytes: {len(payload)}", file=sys.stderr)
    print(f"Target: {MODEL} @ kronos", file=sys.stderr)

    print("Sending single-pass extraction prompt...", file=sys.stderr)
    response, elapsed, usage = ask_kronos(payload)
    print(f"Elapsed: {elapsed:.1f}s, usage={usage}", file=sys.stderr)
    print(f"--- Raw response ---\n{response}\n--- End raw ---", file=sys.stderr)

    parsed = parse_responses(response)
    results = []
    for i, gt in enumerate(GROUND_TRUTH):
        qid = f"Q{i+1}"
        engine_answer = parsed.get(qid, "[NO RESPONSE]")
        correct = bool(gt["match"](engine_answer))
        results.append({
            "qid": qid,
            "question": gt["q"],
            "ground_truth": gt["answer"],
            "engine_response": engine_answer,
            "correct": correct,
        })
        print(f"  {qid}: {'PASS' if correct else 'FAIL'} -> {engine_answer[:80]}", file=sys.stderr)

    score = sum(1 for r in results if r["correct"])
    verdict = "PORTABLE" if score >= 6 else "FRAGILE"
    summary = {
        "model": MODEL,
        "endpoint": "kronos (108.81.9.145:1337)",
        "subject": "amanda.State.v13",
        "payload_bytes": len(payload),
        "single_pass": True,
        "elapsed_s": round(elapsed, 1),
        "usage": usage,
        "n_questions": len(GROUND_TRUTH),
        "score": score,
        "pass_threshold": 6,
        "verdict": verdict,
        "raw_response": response,
        "results": results,
    }
    OUT_FILE.write_text(json.dumps(summary, indent=2))
    print(f"\nSCORE: {score}/{len(GROUND_TRUTH)} -> {verdict}", file=sys.stderr)


if __name__ == "__main__":
    main()
