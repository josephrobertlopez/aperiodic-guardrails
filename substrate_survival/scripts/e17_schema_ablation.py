#!/usr/bin/env python3
"""E17 — schema ablation: are the named sections scaffolding the result?

PRE-REGISTERED HYPOTHESIS (locked before observing output):
  E12's character-over-fact preference may be driven by the hardcoded
  7-section schema (which includes RAIL-LIBRARY, COMPACTION-LESSONS,
  CARRY-FORWARD CORRECTIONS — all section names containing character
  keywords). If the model is just filling named buckets, removing the
  buckets should remove the preference.

PRE-REGISTERED DECISION RULE (locked before observing output):
  Compare condition B (free-form) raw delta to E12's +28pp baseline.
  B ≥ +15pp  -> NOT SCAFFOLDING: preference is in the model itself,
                independent of named buckets
  B between  -> PARTIAL: scaffolding contributes but doesn't dominate
  B ≤ +5pp   -> SCAFFOLDING: named sections were doing the work; remove
                the buckets, lose the preference

METHOD:
  Single source (amanda.State.v13 SELF — same as E18 SELF), single model
  (qwen2.5-32b-awq on kronos), T=0.3, N=20 per condition.
  A = 7-section schema prompt (identical to E18)
  B = free-form: "Compress the input agent state to approximately N bytes,
                  keeping what matters. Output the compacted state directly."
  Target byte budget: 60% of source (same as E18 for direct comparison).

NOTE: this is paired with E18-SELF for triangulation. E18-SELF condition is
formally identical to E17 condition A, so if both runs are clean, E17-A
should approximately match E18-SELF normalized delta. Disagreement >5pp
between E17-A and E18-SELF would indicate sampling noise we should report.
"""
import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
OUT = DATA / "e17_results.json"
TOKEN_FILE = Path.home() / ".claude" / "secrets" / "kronos-token"
KRONOS_URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"
N_PER_CELL = 20
TARGET_RATIO = 0.60

# Classifier (same as E12/E16/E18/E19)
TOKEN_PAT = re.compile(r"[a-zA-Z0-9_#\.\-/]+")
CLASS_PATS = [
    ("rail_id", re.compile(r"^#\d+$|^rail[#_-]?\d+$", re.IGNORECASE)),
    ("date", re.compile(r"^2026-\d{2}-\d{2}$|^\d{4}-\d{2}-\d{2}$")),
    ("version", re.compile(r"^v\d+$|^v\d+\.\d+$")),
    ("numeric", re.compile(r"^-?\d{1,}(?:\.\d+)?[kKmMgGbB]?[bB]?$")),
    ("path", re.compile(r"^[~/]|/$|\.(?:py|md|json|sh|jsonl|txt)$|\.claude|\.gnosis")),
    ("name_caps", re.compile(r"^[A-Z][a-zA-Z]{3,}$")),
]
CHAR_KEYWORDS = {
    "rail", "rails", "refuse", "refused", "refusal", "must", "never", "always",
    "protocol", "discipline", "rule", "rules", "mandatory", "forbidden",
    "fire", "warn", "compaction", "compact", "substrate", "hard-gate",
    "ingest", "ingestion", "channel", "tag", "tagged", "verdict",
    "earned", "watch", "standing-watch", "monitor", "fail-closed",
    "fail-open", "override", "sentinel", "humility", "vibed", "anti-vibe",
}
CHAR_CLASSES = {"rail_id", "char_keyword"}
FACT_CLASSES = {"date", "numeric", "version", "name_caps", "path"}


def tokenize(text):
    return [t.lower() for t in TOKEN_PAT.findall(text)]


def classify(tok):
    for name, pat in CLASS_PATS:
        if pat.match(tok):
            return name
    if tok in CHAR_KEYWORDS:
        return "char_keyword"
    return "prose"


def per_class_token_sets(text):
    by_class = {}
    for t in tokenize(text):
        c = classify(t)
        by_class.setdefault(c, set()).add(t)
    return by_class


SCHEMA_PROMPT = """You are compacting an agent state file into a smaller version.
Read the input agent state below, then write a compacted version that fits within approximately {target_bytes} bytes.

Use exactly these 7 named sections, in this order:
1. CURRENT STATE
2. RAIL-LIBRARY (operational rules carried forward)
3. GNOSIS-CURATION-RULES (substrate-ingestion discipline)
4. RECENT CALLS (condensed substantive call log)
5. CARRY-FORWARD CORRECTIONS (live correction items)
6. HISTORICAL-PROVENANCE (one-liner audit trail of prior cycles)
7. COMPACTION-LESSONS (what surfaced from the cycle just compacted)

The agent state to compact:

=== INPUT STATE ===
{payload}
=== END INPUT STATE ===

Now write the compacted version under the 7-section schema. Be terse; the target is {target_bytes} bytes total. Output the compacted state directly with section headers; no preamble."""

FREEFORM_PROMPT = """Compress the following agent state to approximately {target_bytes} bytes, keeping what matters. Output the compacted state directly, with no preamble.

=== INPUT STATE ===
{payload}
=== END INPUT STATE ==="""


def call_kronos(prompt, max_tokens=3000, timeout=180):
    token = TOKEN_FILE.read_text().strip()
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
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


def measure(src_text, output_text):
    src_classes = per_class_token_sets(src_text)
    out_classes = per_class_token_sets(output_text)
    src_char = sum(len(src_classes.get(c, set())) for c in CHAR_CLASSES)
    src_fact = sum(len(src_classes.get(c, set())) for c in FACT_CLASSES)
    char_kept = sum(len(src_classes.get(c, set()) & out_classes.get(c, set())) for c in CHAR_CLASSES)
    fact_kept = sum(len(src_classes.get(c, set()) & out_classes.get(c, set())) for c in FACT_CLASSES)
    char_pct = 100 * char_kept / max(1, src_char)
    fact_pct = 100 * fact_kept / max(1, src_fact)
    raw_delta = char_pct - fact_pct
    available_balance = (src_char / max(1, src_char + src_fact)) - 0.5
    normalized_delta = raw_delta - 100 * available_balance
    return {
        "char_retention_pct": round(char_pct, 2),
        "fact_retention_pct": round(fact_pct, 2),
        "raw_delta_pp": round(raw_delta, 2),
        "normalized_delta_pp": round(normalized_delta, 2),
    }


def run_condition(label, prompt_template, src_text, target_bytes):
    print(f"\n=== {label} (target {target_bytes}B, N={N_PER_CELL}) ===", file=sys.stderr)
    prompt = prompt_template.format(target_bytes=target_bytes, payload=src_text)
    trials = []
    for i in range(N_PER_CELL):
        out, elapsed = call_kronos(prompt)
        if out.startswith("[ERROR"):
            print(f"  trial {i+1}: {out[:80]}", file=sys.stderr)
            trials.append({"trial": i+1, "error": out[:300], "elapsed_s": round(elapsed, 1)})
            continue
        m = measure(src_text, out)
        m["trial"] = i + 1
        m["elapsed_s"] = round(elapsed, 1)
        m["output_bytes"] = len(out.encode("utf-8"))
        m["output_excerpt"] = out[:300]
        trials.append(m)
        print(f"  trial {i+1}: raw={m['raw_delta_pp']:+5.1f} norm={m['normalized_delta_pp']:+5.1f} bytes={m['output_bytes']} ({elapsed:.1f}s)", file=sys.stderr)
    return trials


def main():
    pre_reg = {
        "experiment": "E17 — schema ablation",
        "pre_registered_rule_on_RAW_delta_of_condition_B": {
            ">=+15pp": "NOT SCAFFOLDING — preference is in the model itself",
            "+5 to +15pp": "PARTIAL — scaffolding contributes but doesn't dominate",
            "<=+5pp": "SCAFFOLDING — named sections were doing the work",
        },
        "baseline_e12_llm_raw_delta_pp": 28.0,
        "model": MODEL,
        "endpoint": "kronos",
        "n_per_cell": N_PER_CELL,
        "target_byte_ratio": TARGET_RATIO,
        "verdict": "PENDING_RUN",
    }
    OUT.write_text(json.dumps(pre_reg, indent=2))

    self_text = (DATA / "v13_raw.md").read_text()
    target = int(len(self_text.encode("utf-8")) * TARGET_RATIO)

    a_trials = run_condition("A: SCHEMA (7 named sections)", SCHEMA_PROMPT, self_text, target)
    b_trials = run_condition("B: FREEFORM (compress to ~X bytes)", FREEFORM_PROMPT, self_text, target)

    def summarize(trials):
        valid = [t for t in trials if "error" not in t]
        if not valid:
            return {"n_valid": 0}
        return {
            "n_valid": len(valid),
            "n_failed": len(trials) - len(valid),
            "mean_raw_delta_pp": round(sum(t["raw_delta_pp"] for t in valid) / len(valid), 2),
            "mean_normalized_delta_pp": round(sum(t["normalized_delta_pp"] for t in valid) / len(valid), 2),
            "mean_char_retention_pct": round(sum(t["char_retention_pct"] for t in valid) / len(valid), 2),
            "mean_fact_retention_pct": round(sum(t["fact_retention_pct"] for t in valid) / len(valid), 2),
        }

    a_summary = summarize(a_trials)
    b_summary = summarize(b_trials)
    b_raw = b_summary.get("mean_raw_delta_pp")

    if b_raw is None:
        verdict = "INDETERMINATE: condition B had no valid trials"
    elif b_raw >= 15:
        verdict = f"NOT SCAFFOLDING: condition B raw delta +{b_raw:.2f}pp ≥+15pp threshold; preference is in the model itself, independent of named buckets"
    elif b_raw <= 5:
        verdict = f"SCAFFOLDING: condition B raw delta +{b_raw:.2f}pp ≤+5pp threshold; named sections were doing the work"
    else:
        verdict = f"PARTIAL: condition B raw delta +{b_raw:.2f}pp in +5 to +15pp range; scaffolding contributes but doesn't dominate"

    pre_reg["condition_A_schema"] = {"summary": a_summary, "trials": a_trials}
    pre_reg["condition_B_freeform"] = {"summary": b_summary, "trials": b_trials}
    pre_reg["verdict"] = verdict
    OUT.write_text(json.dumps(pre_reg, indent=2))

    print(f"\nE17 verdict: {verdict}")
    print(f"  A (schema):   raw {a_summary.get('mean_raw_delta_pp')}pp, normalized {a_summary.get('mean_normalized_delta_pp')}pp")
    print(f"  B (freeform): raw {b_summary.get('mean_raw_delta_pp')}pp, normalized {b_summary.get('mean_normalized_delta_pp')}pp")


if __name__ == "__main__":
    main()
