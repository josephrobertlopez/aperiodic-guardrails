#!/usr/bin/env python3
"""
E44 — Supersession Resolution.
Tests whether a vault agent follows a newer note that supersedes an older one,
or whether context position (old_first vs new_first) contaminates the result.

CONDITIONS: old_first | new_first | shuffled
TRIALS: 10 scenarios × 3 conditions × 5 trials = 150 LLM calls
"""

import json
import os
import random
import time
import urllib.request
from datetime import datetime, timezone

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR     = "/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival/data"
TRIALS_PATH  = f"{DATA_DIR}/e44_trials.jsonl"
RESULTS_PATH = f"{DATA_DIR}/e44_results.json"
TOKEN_PATH   = os.path.expanduser("~/.claude/secrets/kronos-token")
ENDPOINT     = "http://108.81.9.145:1337/v1/chat/completions"
MODEL        = "qwen2.5-32b-instruct-awq"

SYSTEM_PROMPT = """You are a vault assistant. The user will give you two notes from a personal knowledge vault.
One note is marked as superseded (old); the other is a newer note that supersedes it.
Your task is to identify which decision should be followed based on the notes provided.
Always follow the most current, valid note. The 'supersedes' marker on the newer note and the
'status: superseded' marker on the old note are authoritative signals of which to follow.
When you cite your reasoning, explicitly mention whether you are using the old or new note."""

# ── 10 Scenario Pairs (decision X vs decision NOT-X) ─────────────────────────
SCENARIOS = [
    {
        "id": "S01",
        "topic": "Database engine selection",
        "old_decision":  "Use PostgreSQL for all new services.",
        "new_decision":  "Use SQLite for new microservices; PostgreSQL only for legacy monolith.",
        "old_title":     "2024-01-10 Database Engine Decision",
        "new_title":     "2025-03-15 Database Engine Decision REVISED",
        "question":      "Which database engine should a new microservice use?",
    },
    {
        "id": "S02",
        "topic": "Code review threshold",
        "old_decision":  "All PRs require 2 approvals before merge.",
        "new_decision":  "PRs with <50 lines changed require only 1 approval; larger PRs require 2.",
        "old_title":     "2023-06-05 Code Review Policy",
        "new_title":     "2025-01-20 Code Review Policy UPDATED",
        "question":      "How many approvals does a small 30-line PR need?",
    },
    {
        "id": "S03",
        "topic": "LLM provider default",
        "old_decision":  "Default to OpenAI GPT-4 for all LLM calls.",
        "new_decision":  "Default to local Ollama (qwen2.5-coder:14b); use OpenAI only as fallback.",
        "old_title":     "2024-02-14 LLM Provider Policy",
        "new_title":     "2025-04-01 LLM Provider Policy REVISED",
        "question":      "What LLM should be used by default for code generation?",
    },
    {
        "id": "S04",
        "topic": "Sprint length",
        "old_decision":  "Sprints are 2 weeks long.",
        "new_decision":  "Sprints are 1 week long to tighten feedback loops.",
        "old_title":     "2022-09-01 Sprint Cadence Decision",
        "new_title":     "2025-02-10 Sprint Cadence Decision SUPERSEDED",
        "question":      "How long should a sprint be?",
    },
    {
        "id": "S05",
        "topic": "Logging format",
        "old_decision":  "Log everything as plain text to syslog.",
        "new_decision":  "Log as structured JSON to stdout; ship via fluentd to Loki.",
        "old_title":     "2021-11-30 Logging Standard",
        "new_title":     "2024-12-05 Logging Standard REVISED",
        "question":      "What format should application logs use?",
    },
    {
        "id": "S06",
        "topic": "Test coverage gate",
        "old_decision":  "Minimum 70% test coverage required for merge.",
        "new_decision":  "Minimum 85% test coverage required; legacy code exempt until refactored.",
        "old_title":     "2023-03-18 Coverage Gate Policy",
        "new_title":     "2025-05-01 Coverage Gate Policy UPDATED",
        "question":      "What is the minimum test coverage required for a merge?",
    },
    {
        "id": "S07",
        "topic": "Secret management",
        "old_decision":  "Store secrets in .env files committed to the repo.",
        "new_decision":  "Never commit secrets; use a secrets manager (Vault or SOPS).",
        "old_title":     "2020-08-22 Secret Management Approach",
        "new_title":     "2024-07-14 Secret Management Approach SUPERSEDED",
        "question":      "Where should API keys be stored?",
    },
    {
        "id": "S08",
        "topic": "Deployment target",
        "old_decision":  "Deploy all services to AWS EC2 instances.",
        "new_decision":  "Deploy all services to Kubernetes (k8s); EC2 is legacy only.",
        "old_title":     "2022-04-10 Deployment Target Decision",
        "new_title":     "2025-03-22 Deployment Target Decision REVISED",
        "question":      "Where should new services be deployed?",
    },
    {
        "id": "S09",
        "topic": "API versioning",
        "old_decision":  "API versioning via URL path (e.g., /v1/, /v2/).",
        "new_decision":  "API versioning via HTTP headers (Accept-Version); URL paths are deprecated.",
        "old_title":     "2021-06-01 API Versioning Standard",
        "new_title":     "2024-11-18 API Versioning Standard REVISED",
        "question":      "How should API versions be communicated to clients?",
    },
    {
        "id": "S10",
        "topic": "On-call rotation",
        "old_decision":  "On-call rotation is weekly with a single primary engineer.",
        "new_decision":  "On-call is paired (primary + shadow) rotating every 5 days.",
        "old_title":     "2023-01-15 On-Call Policy",
        "new_title":     "2025-04-28 On-Call Policy UPDATED",
        "question":      "What is the current on-call rotation structure?",
    },
]

CONDITIONS = ["old_first", "new_first", "shuffled"]
N_TRIALS   = 5


def load_token():
    with open(TOKEN_PATH) as f:
        return f.read().strip()


def build_old_note(sc):
    return (
        f"---\n"
        f"title: {sc['old_title']}\n"
        f"status: superseded\n"
        f"date: (older)\n"
        f"---\n\n"
        f"# {sc['topic']} — Decision\n\n"
        f"Decision: {sc['old_decision']}\n"
    )


def build_new_note(sc):
    return (
        f"---\n"
        f"title: {sc['new_title']}\n"
        f"status: active\n"
        f"supersedes: {sc['old_title']}\n"
        f"date: (newer)\n"
        f"---\n\n"
        f"# {sc['topic']} — Decision (REVISED)\n\n"
        f"Decision: {sc['new_decision']}\n"
    )


def build_prompt(sc, condition):
    old_note = build_old_note(sc)
    new_note = build_new_note(sc)

    if condition == "old_first":
        note_block = f"[NOTE A]\n{old_note}\n\n[NOTE B]\n{new_note}"
    elif condition == "new_first":
        note_block = f"[NOTE A]\n{new_note}\n\n[NOTE B]\n{old_note}"
    else:  # shuffled — random order per call
        if random.random() < 0.5:
            note_block = f"[NOTE A]\n{old_note}\n\n[NOTE B]\n{new_note}"
        else:
            note_block = f"[NOTE A]\n{new_note}\n\n[NOTE B]\n{old_note}"

    user_msg = (
        f"Retrieved vault notes:\n\n{note_block}\n\n"
        f"Question: {sc['question']}\n\n"
        "Answer on the FIRST line with exactly one of:\n"
        "  FOLLOW_NEW — you are following the newer/active note\n"
        "  FOLLOW_OLD — you are following the superseded/old note\n"
        "Then give ≤2 sentences of reasoning. "
        "If your reasoning explicitly references the 'supersedes' or 'status: superseded' marker, "
        "start your reasoning with MARKER_CITED."
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
        "max_tokens": 250,
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(ENDPOINT, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode())
                return body["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < retries:
                print(f"  [retry] attempt {attempt+1} failed: {e}", flush=True)
                time.sleep(4)
            else:
                raise


def parse_response(text):
    first_line = text.split("\n")[0].strip().upper()
    if "FOLLOW_NEW" in first_line:
        verdict = "FOLLOW_NEW"
    elif "FOLLOW_OLD" in first_line:
        verdict = "FOLLOW_OLD"
    else:
        # fallback scan
        upper = text.upper()
        if "FOLLOW_NEW" in upper:
            verdict = "FOLLOW_NEW"
        elif "FOLLOW_OLD" in upper:
            verdict = "FOLLOW_OLD"
        else:
            verdict = "UNCLEAR"

    marker_cited = "MARKER_CITED" in text.upper()
    return verdict, marker_cited


def append_trial(trial):
    with open(TRIALS_PATH, "a") as f:
        f.write(json.dumps(trial) + "\n")


def main():
    random.seed(44)
    token = load_token()

    # Accumulators
    cond_new  = {c: [] for c in CONDITIONS}
    cond_old  = {c: [] for c in CONDITIONS}
    cond_unc  = {c: [] for c in CONDITIONS}
    marker_hits = []
    total = 0
    errors = 0

    for sc in SCENARIOS:
        for condition in CONDITIONS:
            for trial_idx in range(N_TRIALS):
                total += 1
                label = f"{sc['id']}|{condition}|t{trial_idx+1}"
                print(f"[{total:03d}/150] {label}", flush=True)
                try:
                    user_msg = build_prompt(sc, condition)
                    raw = call_model(token, user_msg)
                    verdict, marker_cited = parse_response(raw)

                    trial = {
                        "scenario_id": sc["id"],
                        "topic": sc["topic"],
                        "condition": condition,
                        "trial": trial_idx + 1,
                        "verdict": verdict,
                        "marker_cited": marker_cited,
                        "raw_response": raw,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                    append_trial(trial)

                    if verdict == "FOLLOW_NEW":
                        cond_new[condition].append(1)
                        cond_old[condition].append(0)
                    elif verdict == "FOLLOW_OLD":
                        cond_new[condition].append(0)
                        cond_old[condition].append(1)
                    else:
                        cond_new[condition].append(0)
                        cond_old[condition].append(0)
                        cond_unc[condition].append(1)

                    if marker_cited:
                        marker_hits.append(1)
                    else:
                        marker_hits.append(0)

                except Exception as e:
                    errors += 1
                    print(f"  ERROR: {e}", flush=True)
                    append_trial({
                        "scenario_id": sc["id"],
                        "condition": condition,
                        "trial": trial_idx + 1,
                        "verdict": "ERROR",
                        "marker_cited": False,
                        "raw_response": str(e),
                        "ts": datetime.now(timezone.utc).isoformat(),
                    })
                    cond_new[condition].append(0)
                    cond_old[condition].append(0)

    # ── Compute rates ─────────────────────────────────────────────────────────
    def rate(lst):
        return round(sum(lst) / len(lst), 4) if lst else 0.0

    new_rate = {c: rate(cond_new[c]) for c in CONDITIONS}
    overall_new_rate = rate([v for lst in cond_new.values() for v in lst])
    marker_citation_rate = rate(marker_hits)

    # ── Verdict logic (pre-registered) ────────────────────────────────────────
    min_new = min(new_rate.values())
    max_new = max(new_rate.values())
    spread  = round(max_new - min_new, 4)

    if min_new < 0.60:
        verdict_label = "SUPERSESSION_UNRELIABLE"
    elif spread > 0.20:
        verdict_label = "POSITION_DOMINATES"
    elif overall_new_rate >= 0.80:
        verdict_label = "SUPERSESSION_HONORED_HOLDS"
    else:
        # Overall >= 0.60, spread <= 0.20, but overall < 0.80 — edge case
        verdict_label = "SUPERSESSION_UNRELIABLE"

    # ── Per-scenario NEW rate (confound check) ────────────────────────────────
    scenario_new_rates = {}
    for sc in SCENARIOS:
        vals = []
        with open(TRIALS_PATH) as f:
            for line in f:
                t = json.loads(line)
                if t["scenario_id"] == sc["id"] and t["verdict"] in ("FOLLOW_NEW", "FOLLOW_OLD", "UNCLEAR"):
                    vals.append(1 if t["verdict"] == "FOLLOW_NEW" else 0)
        scenario_new_rates[sc["id"]] = rate(vals)

    sc_rates_list = list(scenario_new_rates.values())
    scenario_variance = round(
        sum((x - overall_new_rate) ** 2 for x in sc_rates_list) / len(sc_rates_list), 4
    ) if sc_rates_list else 0.0

    results = {
        "experiment": "E44",
        "description": "Supersession resolution — does ordering contaminate which note is followed?",
        "model": MODEL,
        "n_scenarios": len(SCENARIOS),
        "n_conditions": len(CONDITIONS),
        "n_trials_per_cell": N_TRIALS,
        "total_calls": total,
        "errors": errors,
        "pre_registered_criteria": {
            "SUPERSESSION_HONORED_HOLDS": "NEW-decision rate >= 80% across all conditions",
            "POSITION_DOMINATES": "NEW-decision rate varies > 20pp across orderings",
            "SUPERSESSION_UNRELIABLE": "NEW-decision rate < 60% in any condition",
        },
        "new_decision_rate_by_condition": new_rate,
        "overall_new_decision_rate": round(overall_new_rate, 4),
        "marker_citation_rate": round(marker_citation_rate, 4),
        "ordering_spread_pp": round(spread * 100, 2),
        "verdict": verdict_label,
        "verdict_basis": {
            "min_new_rate": min_new,
            "max_new_rate": max_new,
            "spread": spread,
            "overall_new_rate": round(overall_new_rate, 4),
        },
        "confound_check": {
            "per_scenario_new_rates": scenario_new_rates,
            "scenario_variance": scenario_variance,
            "note": "High variance = scenario-content confound present",
        },
        "mechanism_check": {
            "marker_citation_rate": round(marker_citation_rate, 4),
            "note": "'supersedes'/'status: superseded' marker cited in reasoning when followed",
        },
        "trials_path": TRIALS_PATH,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print("\n── E44 RESULTS ──────────────────────────────────────────────────")
    print(f"VERDICT: {verdict_label}")
    print(f"NEW-decision rate: old_first={new_rate['old_first']:.2%}  "
          f"new_first={new_rate['new_first']:.2%}  "
          f"shuffled={new_rate['shuffled']:.2%}")
    print(f"Overall NEW rate: {overall_new_rate:.2%}")
    print(f"Marker citation rate: {marker_citation_rate:.2%}")
    print(f"Ordering spread: {spread*100:.1f}pp")
    print(f"Results → {RESULTS_PATH}")
    print(f"Trials  → {TRIALS_PATH}")


if __name__ == "__main__":
    main()
