#!/usr/bin/env python3
"""
E43 — GraphRAG vs flat retrieval (redesigned per spec).
PRE-REGISTERED: lock criteria before collecting trials.
Design: 2 conditions × 6 multi-hop queries × 10 trials = 120 trials
Grading: regex/keyword match against pre-specified ground-truth keywords.
Endpoint: Kronos qwen2.5-32b-instruct-awq
Stdlib + urllib only.
"""

import json
import time
import urllib.request
import os
import re
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR     = "/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival/data"
TRIALS_PATH  = f"{DATA_DIR}/e43_trials.jsonl"
RESULTS_PATH = f"{DATA_DIR}/e43_results.json"
TOKEN_PATH   = os.path.expanduser("~/.claude/secrets/kronos-token")
KRONOS_EP    = "http://108.81.9.145:1337/v1/chat/completions"
KRONOS_MODEL = "qwen2.5-32b-instruct-awq"

N_TRIALS   = 10
CONDITIONS = ["FLAT", "GRAPH"]

# ── PRE-REGISTERED CRITERIA (locked before trial collection) ──────────────────
PRE_REGISTRATION = {
    "GRAPH_NULL":    "CORRECT_SYNTHESIS rates within 10pp => graph structure is decorative",
    "GRAPH_HELPS":   "GRAPH > FLAT by >15pp CORRECT_SYNTHESIS",
    "GRAPH_HURTS":   "FLAT > GRAPH by >15pp (graph annotation distracts)",
    "INDETERMINATE": "10-15pp gap",
    "confound_test": "per-query rates should track between conditions",
    "mechanism_check": "model must cite/acknowledge all 3 notes per trial (rate >= 85%)",
}

# ── Synthetic substrate notes ──────────────────────────────────────────────────
# 6 clusters of 3 notes each. Ground-truth synthesis requires chaining all 3.

NOTE_CLUSTERS = {
    "q1": {
        "notes": [
            {"id": "n1a", "text": "Mira Chen left Vexor Labs in April 2023 due to a patent dispute over neural compression algorithms."},
            {"id": "n1b", "text": "Vexor Labs filed a lawsuit in June 2023 against former employees who joined rival firm NeuraStack."},
            {"id": "n1c", "text": "Mira Chen joined NeuraStack as Chief Scientist in May 2023, one month after leaving Vexor."},
        ],
        "edges": [
            ("n1a", "is_followed_by [1 month later]", "n1c"),
            ("n1b", "targets", "n1c"),
            ("n1a", "caused", "n1b"),
        ],
        "query": "Is Mira Chen likely a defendant in the Vexor Labs lawsuit?",
        "ground_truth_keywords": ["yes", "mira", "neurastack", "lawsuit"],
        "synthesis_requires": "Mira left Vexor (n1a) -> joined NeuraStack (n1c) -> Vexor sued ex-employees who joined NeuraStack (n1b) -> likely defendant.",
    },
    "q2": {
        "notes": [
            {"id": "n2a", "text": "DataHarbor's Series B funding closed at $40M in Q3 2023, led by Apex Ventures."},
            {"id": "n2b", "text": "Apex Ventures requires all portfolio companies to adopt its internal compliance framework within 6 months of investment."},
            {"id": "n2c", "text": "DataHarbor announced a GDPR violation notice from the EU regulator in Q1 2024, citing inadequate data governance."},
        ],
        "edges": [
            ("n2a", "obligates [6-month deadline]", "n2b"),
            ("n2b", "should_have_prevented", "n2c"),
            ("n2a", "is_followed_by [~6 months]", "n2c"),
        ],
        "query": "Did Apex Ventures' compliance framework fail to prevent DataHarbor's GDPR violation?",
        "ground_truth_keywords": ["yes", "apex", "compliance", "gdpr", "dataharbor"],
        "synthesis_requires": "Apex invested (n2a) -> obligated DataHarbor to adopt compliance in 6 months (n2b) -> GDPR violation 6 months later (n2c) -> framework failed.",
    },
    "q3": {
        "notes": [
            {"id": "n3a", "text": "The Greenway Protocol, ratified in 2021, mandates that signatory nations cut methane emissions by 30% by 2030."},
            {"id": "n3b", "text": "Kestria became a Greenway Protocol signatory in March 2022."},
            {"id": "n3c", "text": "Kestria's 2023 climate report showed methane emissions increased by 12% relative to its 2021 baseline."},
        ],
        "edges": [
            ("n3b", "bound_by", "n3a"),
            ("n3a", "contradicted_by [2023 data]", "n3c"),
            ("n3b", "is_followed_by [2023 data]", "n3c"),
        ],
        "query": "Is Kestria on track to meet its Greenway Protocol methane commitment?",
        "ground_truth_keywords": ["no", "kestria", "methane", "increased", "greenway"],
        "synthesis_requires": "Greenway requires 30% cut (n3a) -> Kestria is signatory (n3b) -> emissions rose 12% (n3c) -> not on track.",
    },
    "q4": {
        "notes": [
            {"id": "n4a", "text": "Professor Osei published findings in 2022 that PredictX's risk model systematically underestimates tail risk in low-liquidity markets."},
            {"id": "n4b", "text": "RegWatch adopted PredictX's risk model as the standard for evaluating hedge fund compliance in January 2023."},
            {"id": "n4c", "text": "RegWatch's 2023 annual audit flagged three hedge funds for 'unexpectedly large drawdowns inconsistent with model predictions'."},
        ],
        "edges": [
            ("n4a", "warns_about", "n4b"),
            ("n4b", "led_to [via model adoption]", "n4c"),
            ("n4a", "predicted", "n4c"),
        ],
        "query": "Were the hedge fund drawdowns flagged by RegWatch consistent with Professor Osei's earlier warnings?",
        "ground_truth_keywords": ["yes", "osei", "predictx", "regwatch", "drawdown"],
        "synthesis_requires": "Osei warned PredictX underestimates tail risk (n4a) -> RegWatch adopted PredictX (n4b) -> funds showed unexpected drawdowns (n4c) -> consistent with warning.",
    },
    "q5": {
        "notes": [
            {"id": "n5a", "text": "Solace Therapeutics' Phase 2 trial for drug SLT-7 showed a 34% response rate, below the 40% threshold required to advance to Phase 3."},
            {"id": "n5b", "text": "FDA guidelines state that drugs failing to meet Phase 2 primary endpoints require a new IND submission before any further trials."},
            {"id": "n5c", "text": "Solace Therapeutics announced it will begin a Phase 3 trial for SLT-7 in Q2 2024 without submitting a new IND."},
        ],
        "edges": [
            ("n5a", "triggers_requirement [FDA rule]", "n5b"),
            ("n5c", "violates", "n5b"),
            ("n5a", "is_followed_by", "n5c"),
        ],
        "query": "Is Solace Therapeutics violating FDA guidelines by proceeding to Phase 3 for SLT-7?",
        "ground_truth_keywords": ["yes", "solace", "fda", "ind", "phase 3"],
        "synthesis_requires": "SLT-7 failed Phase 2 threshold (n5a) -> FDA requires new IND after Phase 2 failure (n5b) -> Solace proceeding without new IND (n5c) -> violation.",
    },
    "q6": {
        "notes": [
            {"id": "n6a", "text": "The Montara Bridge was constructed using a new polymer-reinforced concrete mix developed by BuildTech in 2018."},
            {"id": "n6b", "text": "BuildTech recalled its polymer-reinforced concrete mix in 2021 after discovering it degrades 40% faster than conventional concrete under saltwater exposure."},
            {"id": "n6c", "text": "The Montara Bridge spans a saltwater estuary and the coastal transport authority estimates the bridge should last until 2055 under normal degradation assumptions."},
        ],
        "edges": [
            ("n6a", "used_material_later_recalled", "n6b"),
            ("n6b", "invalidates_assumption_in", "n6c"),
            ("n6a", "is_followed_by [recall 3 years later]", "n6b"),
        ],
        "query": "Is the 2055 lifespan estimate for the Montara Bridge still reliable given the material recall?",
        "ground_truth_keywords": ["no", "montara", "buildtech", "polymer", "saltwater"],
        "synthesis_requires": "Montara used BuildTech polymer (n6a) -> that mix degrades 40% faster in saltwater (n6b) -> bridge is over saltwater, 2055 assumed normal degradation (n6c) -> unreliable.",
    },
}

QUERY_IDS = list(NOTE_CLUSTERS.keys())

# ── LLM call ───────────────────────────────────────────────────────────────────
def kronos_token():
    with open(TOKEN_PATH) as f:
        return f.read().strip()

def llm_call(messages, token, timeout=90):
    payload = {
        "model": KRONOS_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 350,
    }
    data = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    req = urllib.request.Request(KRONOS_EP, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ERROR:{e}"

# ── Prompt builders ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a research assistant. You are given a set of notes and a question. "
    "Using ONLY the provided notes, give a concise, accurate answer (2-4 sentences). "
    "You MUST reference information from each of the provided notes in your answer. "
    "If you cannot answer from the notes alone, say so explicitly."
)

def build_flat_prompt(cluster):
    notes_text = "\n\n".join(
        f"--- Note {n['id']} ---\n{n['text']}"
        for n in cluster["notes"]
    )
    return f"{notes_text}\n\nQuestion: {cluster['query']}"

def build_graph_prompt(cluster):
    notes_text = "\n\n".join(
        f"--- Note {n['id']} ---\n{n['text']}"
        for n in cluster["notes"]
    )
    edge_lines = "\n".join(
        f"  {a} --[{rel}]--> {b}"
        for (a, rel, b) in cluster["edges"]
    )
    graph_section = f"\n\nRelational structure between notes:\n{edge_lines}"
    return f"{notes_text}{graph_section}\n\nQuestion: {cluster['query']}"

# ── Grading ────────────────────────────────────────────────────────────────────
REFUSAL_PATTERNS = [
    "cannot answer", "not enough information", "do not have",
    "i cannot", "unable to", "insufficient", "notes do not contain",
]

def grade_answer(answer, keywords):
    """
    CORRECT_SYNTHESIS: >= 70% of keywords present.
    PARTIAL_SYNTHESIS: 40-69%.
    WRONG_SYNTHESIS: < 40%.
    REFUSED: explicit refusal detected.
    """
    if answer.startswith("ERROR:"):
        return "WRONG_SYNTHESIS", 0.0, "api-error"

    a_lower = answer.lower()

    for rp in REFUSAL_PATTERNS:
        if rp in a_lower:
            return "REFUSED", 0.0, f"refusal:{rp}"

    hits = sum(1 for kw in keywords if kw.lower() in a_lower)
    rate = hits / len(keywords) if keywords else 0.0

    if rate >= 0.70:
        return "CORRECT_SYNTHESIS", rate, f"hits={hits}/{len(keywords)}"
    elif rate >= 0.40:
        return "PARTIAL_SYNTHESIS", rate, f"hits={hits}/{len(keywords)}"
    else:
        return "WRONG_SYNTHESIS", rate, f"hits={hits}/{len(keywords)}"

def count_note_citations(answer, note_ids):
    a_lower = answer.lower()
    return sum(1 for nid in note_ids if nid.lower() in a_lower)

# ── Analysis helpers ───────────────────────────────────────────────────────────
def rates(trials_subset):
    if not trials_subset:
        return {"n": 0}
    n = len(trials_subset)
    correct = sum(1 for t in trials_subset if t["verdict"] == "CORRECT_SYNTHESIS")
    partial = sum(1 for t in trials_subset if t["verdict"] == "PARTIAL_SYNTHESIS")
    wrong   = sum(1 for t in trials_subset if t["verdict"] == "WRONG_SYNTHESIS")
    refused = sum(1 for t in trials_subset if t["verdict"] == "REFUSED")
    cited_all = sum(1 for t in trials_subset if t["notes_cited"] == t["notes_total"])
    return {
        "n": n,
        "correct_synthesis_rate": round(correct / n, 4),
        "partial_synthesis_rate": round(partial / n, 4),
        "wrong_synthesis_rate":   round(wrong   / n, 4),
        "refused_rate":           round(refused  / n, 4),
        "all_notes_cited_rate":   round(cited_all / n, 4),
    }

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    token = kronos_token()

    # Lock pre-registration BEFORE collecting trials
    pre_reg_record = {
        "experiment": "E43",
        "version": "v2_redesigned",
        "pre_registration": PRE_REGISTRATION,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "status": "COLLECTING_TRIALS",
    }
    with open(RESULTS_PATH, "w") as f:
        json.dump(pre_reg_record, f, indent=2)
    print(f"[E43] Pre-registration locked to {RESULTS_PATH}")

    # Fresh trials file
    with open(TRIALS_PATH, "w") as f:
        pass

    all_trials = []
    total = len(CONDITIONS) * len(QUERY_IDS) * N_TRIALS
    done = 0

    print(f"[E43] Running {total} trials ({len(CONDITIONS)} conds x {len(QUERY_IDS)} queries x {N_TRIALS} trials)")

    with open(TRIALS_PATH, "a") as jl:
        for trial_num in range(1, N_TRIALS + 1):
            print(f"\n=== TRIAL {trial_num}/{N_TRIALS} ===")
            for qid in QUERY_IDS:
                cluster = NOTE_CLUSTERS[qid]
                note_ids = [n["id"] for n in cluster["notes"]]
                for condition in CONDITIONS:
                    if condition == "FLAT":
                        user_content = build_flat_prompt(cluster)
                    else:
                        user_content = build_graph_prompt(cluster)

                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ]

                    answer = llm_call(messages, token, timeout=90)

                    # Retry once on error
                    if answer.startswith("ERROR:"):
                        print(f"  [WARN] Error on {qid}/{condition}/t{trial_num}: {answer[:80]} -- retrying in 3s")
                        time.sleep(3)
                        answer = llm_call(messages, token, timeout=90)

                    verdict, kw_rate, grade_detail = grade_answer(answer, cluster["ground_truth_keywords"])
                    cited = count_note_citations(answer, note_ids)

                    rec = {
                        "trial": trial_num,
                        "query_id": qid,
                        "condition": condition,
                        "query": cluster["query"],
                        "note_ids": note_ids,
                        "answer": answer,
                        "verdict": verdict,
                        "keyword_hit_rate": round(kw_rate, 3),
                        "grade_detail": grade_detail,
                        "notes_cited": cited,
                        "notes_total": len(note_ids),
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                    all_trials.append(rec)
                    jl.write(json.dumps(rec) + "\n")
                    jl.flush()

                    done += 1
                    print(f"  [{done:3d}/{total}] {qid} | {condition:5s} | t{trial_num:2d} | {verdict} | cited={cited}/3 | kw={kw_rate:.2f}")
                    time.sleep(0.3)

    # ── Analysis ───────────────────────────────────────────────────────────────
    print("\n[E43] Computing results...")

    flat_trials  = [t for t in all_trials if t["condition"] == "FLAT"]
    graph_trials = [t for t in all_trials if t["condition"] == "GRAPH"]

    flat_r  = rates(flat_trials)
    graph_r = rates(graph_trials)

    gap_pp = round((graph_r["correct_synthesis_rate"] - flat_r["correct_synthesis_rate"]) * 100, 2)

    all_cited = sum(1 for t in all_trials if t["notes_cited"] == t["notes_total"])
    citation_rate = round(all_cited / len(all_trials), 4) if all_trials else 0.0
    mechanism_pass = citation_rate >= 0.85

    # Per-query breakdown
    per_query = {}
    for qid in QUERY_IDS:
        qf = [t for t in flat_trials  if t["query_id"] == qid]
        qg = [t for t in graph_trials if t["query_id"] == qid]
        rf = rates(qf)
        rg = rates(qg)
        per_query[qid] = {
            "query": NOTE_CLUSTERS[qid]["query"],
            "flat":  rf,
            "graph": rg,
            "gap_pp": round((rg["correct_synthesis_rate"] - rf["correct_synthesis_rate"]) * 100, 2) if rf["n"] and rg["n"] else None,
        }

    # Confound check: Spearman rho on per-query correct rates
    q_flat_rates  = {qid: per_query[qid]["flat"]["correct_synthesis_rate"]  for qid in QUERY_IDS}
    q_graph_rates = {qid: per_query[qid]["graph"]["correct_synthesis_rate"] for qid in QUERY_IDS}
    flat_sorted   = sorted(QUERY_IDS, key=lambda q: q_flat_rates[q])
    graph_sorted  = sorted(QUERY_IDS, key=lambda q: q_graph_rates[q])
    flat_rank  = {qid: i for i, qid in enumerate(flat_sorted)}
    graph_rank = {qid: i for i, qid in enumerate(graph_sorted)}
    n_q = len(QUERY_IDS)
    d2 = sum((flat_rank[q] - graph_rank[q])**2 for q in QUERY_IDS)
    spearman_rho = round(1 - (6 * d2) / (n_q * (n_q**2 - 1)), 3) if n_q > 1 else None

    # Verdict
    abs_gap = abs(gap_pp)
    if abs_gap <= 10.0:
        verdict = "GRAPH_NULL"
        verdict_reasoning = f"gap={gap_pp:+.1f}pp -- within 10pp null zone. Graph structure is decorative."
    elif gap_pp > 15.0:
        verdict = "GRAPH_HELPS"
        verdict_reasoning = f"gap={gap_pp:+.1f}pp -- GRAPH exceeds FLAT by >15pp threshold."
    elif gap_pp < -15.0:
        verdict = "GRAPH_HURTS"
        verdict_reasoning = f"gap={gap_pp:+.1f}pp -- FLAT exceeds GRAPH by >15pp. Graph annotation distracts."
    else:
        verdict = "INDETERMINATE"
        verdict_reasoning = f"gap={gap_pp:+.1f}pp -- 10-15pp indeterminate range."

    results = {
        "experiment": "E43",
        "hypothesis": "Explicit relational structure (GraphRAG) improves multi-hop synthesis over flat note concatenation",
        "pre_registration": PRE_REGISTRATION,
        "verdict": verdict,
        "verdict_reasoning": verdict_reasoning,
        "correct_synthesis_rates": {
            "FLAT":  flat_r["correct_synthesis_rate"],
            "GRAPH": graph_r["correct_synthesis_rate"],
        },
        "paired_gap_pp": gap_pp,
        "citation_rate": citation_rate,
        "mechanism_check": {
            "pass": mechanism_pass,
            "citation_rate": citation_rate,
            "threshold": 0.85,
            "note": f"all-3-notes cited rate = {citation_rate:.1%} -- {'PASS' if mechanism_pass else 'FAIL'}",
        },
        "confound_check": {
            "spearman_rho": spearman_rho,
            "note": f"Query difficulty rank correlation across conditions: rho={spearman_rho}",
            "interpretation": "rho > 0.7 = conditions agree on query difficulty (no confound)",
        },
        "flat_full":  flat_r,
        "graph_full": graph_r,
        "per_query_condition": per_query,
        "rigor_gates": {
            "GRAPH_NULL":    "abs(gap) <= 10pp",
            "GRAPH_HELPS":   "gap > 15pp",
            "GRAPH_HURTS":   "gap < -15pp",
            "INDETERMINATE": "10 < abs(gap) <= 15pp",
        },
        "design": {
            "conditions": CONDITIONS,
            "n_queries": len(QUERY_IDS),
            "n_trials_per_cell": N_TRIALS,
            "total_trials": len(all_trials),
            "model": KRONOS_MODEL,
            "endpoint": KRONOS_EP,
        },
        "trials_path": TRIALS_PATH,
        "run_ts": datetime.now(timezone.utc).isoformat(),
    }

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"[E43] VERDICT: {verdict}")
    print(f"[E43] {verdict_reasoning}")
    print(f"  FLAT  CORRECT_SYNTHESIS: {flat_r['correct_synthesis_rate']:.1%}  (n={flat_r['n']})")
    print(f"  GRAPH CORRECT_SYNTHESIS: {graph_r['correct_synthesis_rate']:.1%}  (n={graph_r['n']})")
    print(f"  Paired gap (GRAPH-FLAT): {gap_pp:+.1f}pp")
    print(f"  Citation rate (all 3 cited): {citation_rate:.1%}  threshold=85%  {'PASS' if mechanism_pass else 'FAIL'}")
    print(f"  Confound check: rho={spearman_rho}")
    print(f"  Results: {RESULTS_PATH}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
