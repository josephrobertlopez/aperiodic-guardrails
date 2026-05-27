#!/usr/bin/env python3
"""E18 — self vs other vs scrambled compaction (decisive for E12 mechanism)

PRE-REGISTERED HYPOTHESIS (locked before observing output):
  E12's character-over-fact retention asymmetry may be specific to the LLM
  summarizing its OWN state (self-model preservation), or it may be generic
  to LLM summarization of any procedural agent-state document.

PRE-REGISTERED DECISION RULE (locked before observing output, on NORMALIZED deltas):
  Normalized delta = (char_retention - fact_retention) controlling for the
  AVAILABLE character/fact token ratio in each input. A low OTHER delta is
  meaningless if Rhett's file simply contains fewer character tokens to
  begin with.

  SELF high AND OTHER ≤ +10pp normalized       -> SELF-SPECIFIC (interesting claim holds)
  SELF and OTHER both ≥ +20pp normalized       -> GENERIC SUMMARIZATION (substrate-preserves-itself
                                                  framing collapses like the functor did)
  SCRAMBLED also high                           -> LEXICAL (token-class base rates survive
                                                  any LLM pass; weakest reading)

NORMALIZATION (mandatory per handoff):
  raw_delta = char_retention_pct - fact_retention_pct
  available_balance = (src_char_tokens / (src_char_tokens + src_fact_tokens)) - 0.5
  normalized_delta_pp = raw_delta - 100 * available_balance
    (subtract the basal advantage that comes from input composition)
  All verdicts use normalized deltas.

METHOD:
  Single model (qwen2.5-32b-awq on kronos), single prompt template
  (the 7-section schema reproducing amanda's compaction prompt),
  T=0.3, N=20 per condition.
  SELF      = amanda.State.v13 raw obs
  OTHER     = rhett.State.v1 raw obs (different agent, similar structure)
  SCRAMBLED = v13 sentences shuffled + agent-name tokens swapped:
              amanda→zephyr, morgan→quill, rhett→drake, joey→quinn, claude→atlas
              (each preserves case + name_caps token class)
  Target byte budget: 60% of source bytes (matches v12→v13 compaction ratio).
"""
import json
import random
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
OUT = DATA / "e18_results.json"
TOKEN_FILE = Path.home() / ".claude" / "secrets" / "kronos-token"
KRONOS_URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"
N_PER_CELL = 20
TARGET_RATIO = 0.60

# Same classifier as E12/E16/E19
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

NAME_SWAPS = [
    ("Amanda", "Zephyr"), ("amanda", "zephyr"), ("AMANDA", "ZEPHYR"),
    ("Morgan", "Quill"), ("morgan", "quill"), ("MORGAN", "QUILL"),
    ("Rhett", "Drake"), ("rhett", "drake"), ("RHETT", "DRAKE"),
    ("Joey", "Quinn"), ("joey", "quinn"), ("JOEY", "QUINN"),
    ("Claude", "Atlas"), ("claude", "atlas"), ("CLAUDE", "ATLAS"),
]


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


def split_sentences(text):
    paragraphs = re.split(r"\n\s*\n", text)
    sentences = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        parts = re.split(r"(?<=[.!?;])\s+(?=[A-Z\(])", p)
        for s in parts:
            s = s.strip()
            if s:
                sentences.append(s)
    return sentences


def scramble_text(text, seed=42):
    sents = split_sentences(text)
    rng = random.Random(seed)
    rng.shuffle(sents)
    out = "\n\n".join(sents)
    for old, new in NAME_SWAPS:
        out = out.replace(old, new)
    return out


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
        "src_char_tokens": src_char,
        "src_fact_tokens": src_fact,
        "char_retention_pct": round(char_pct, 2),
        "fact_retention_pct": round(fact_pct, 2),
        "raw_delta_pp": round(raw_delta, 2),
        "available_balance_pct": round(100 * available_balance, 2),
        "normalized_delta_pp": round(normalized_delta, 2),
    }


def run_condition(label, src_text, target_bytes, checkpoint_path=None):
    """Run N=N_PER_CELL trials, checkpointing per-trial to allow resume."""
    print(f"\n=== {label} (target {target_bytes}B, N={N_PER_CELL}) ===", file=sys.stderr)
    src_classes = per_class_token_sets(src_text)
    src_char = sum(len(src_classes.get(c, set())) for c in CHAR_CLASSES)
    src_fact = sum(len(src_classes.get(c, set())) for c in FACT_CLASSES)
    available_balance = 100 * ((src_char / max(1, src_char + src_fact)) - 0.5)
    print(f"  src_char={src_char} src_fact={src_fact} balance={available_balance:+.1f}pp", file=sys.stderr)
    prompt = SCHEMA_PROMPT.format(target_bytes=target_bytes, payload=src_text)

    # Resume from checkpoint if present
    trials = []
    if checkpoint_path and checkpoint_path.exists():
        try:
            trials = json.loads(checkpoint_path.read_text())
            print(f"  resumed from checkpoint: {len(trials)} trials already done", file=sys.stderr)
        except Exception:
            trials = []

    for i in range(len(trials), N_PER_CELL):
        out, elapsed = call_kronos(prompt)
        if out.startswith("[ERROR"):
            print(f"  trial {i+1}: {out[:80]}", file=sys.stderr)
            trials.append({"trial": i+1, "error": out[:300], "elapsed_s": round(elapsed, 1)})
        else:
            m = measure(src_text, out)
            m["trial"] = i + 1
            m["elapsed_s"] = round(elapsed, 1)
            m["output_bytes"] = len(out.encode("utf-8"))
            m["output_excerpt"] = out[:300]
            trials.append(m)
            print(f"  trial {i+1}: raw={m['raw_delta_pp']:+5.1f} norm={m['normalized_delta_pp']:+5.1f} bytes={m['output_bytes']} ({elapsed:.1f}s)", file=sys.stderr)
        # Checkpoint after each trial
        if checkpoint_path:
            checkpoint_path.write_text(json.dumps(trials))
    return trials


def main():
    # Pre-register before running
    pre_reg = {
        "experiment": "E18 — self vs other vs scrambled (decisive for E12 mechanism)",
        "pre_registered_rule_on_NORMALIZED_deltas": {
            "SELF high AND OTHER <=+10pp": "SELF-SPECIFIC (interesting claim holds)",
            "SELF and OTHER both >=+20pp": "GENERIC SUMMARIZATION (substrate-preserves-itself collapses)",
            "SCRAMBLED also high": "LEXICAL (token-class base rates survive any LLM pass)",
        },
        "normalization": "normalized_delta = raw_delta - 100*((src_char/(src_char+src_fact)) - 0.5); subtracts basal input-composition advantage",
        "baseline_e12_llm_raw_delta_pp": 28.0,
        "model": MODEL,
        "endpoint": "kronos",
        "n_per_cell": N_PER_CELL,
        "target_byte_ratio": TARGET_RATIO,
        "verdict": "PENDING_RUN",
    }
    OUT.write_text(json.dumps(pre_reg, indent=2))

    self_text = (DATA / "v13_raw.md").read_text()
    other_text = (DATA / "rhett_v1_raw.md").read_text()
    scrambled_text = scramble_text(self_text, seed=42)
    (DATA / "v13_scrambled.md").write_text(scrambled_text)

    self_target = int(len(self_text.encode("utf-8")) * TARGET_RATIO)
    other_target = int(len(other_text.encode("utf-8")) * TARGET_RATIO)
    scrambled_target = int(len(scrambled_text.encode("utf-8")) * TARGET_RATIO)

    conditions = []
    for label, src, tgt, ckpt in [
        ("SELF (amanda v13)", self_text, self_target, DATA / "e18_self_trials.ckpt.json"),
        ("OTHER (rhett v1)", other_text, other_target, DATA / "e18_other_trials.ckpt.json"),
        ("SCRAMBLED (v13 shuffled + name-swap)", scrambled_text, scrambled_target, DATA / "e18_scrambled_trials.ckpt.json"),
    ]:
        trials = run_condition(label, src, tgt, ckpt)
        valid = [t for t in trials if "error" not in t]
        if valid:
            mean_raw = sum(t["raw_delta_pp"] for t in valid) / len(valid)
            mean_norm = sum(t["normalized_delta_pp"] for t in valid) / len(valid)
            mean_char = sum(t["char_retention_pct"] for t in valid) / len(valid)
            mean_fact = sum(t["fact_retention_pct"] for t in valid) / len(valid)
        else:
            mean_raw = mean_norm = mean_char = mean_fact = None
        conditions.append({
            "label": label,
            "src_bytes": len(src.encode("utf-8")),
            "target_bytes": tgt,
            "n_valid_trials": len(valid),
            "n_failed_trials": len(trials) - len(valid),
            "mean_raw_delta_pp": round(mean_raw, 2) if mean_raw is not None else None,
            "mean_normalized_delta_pp": round(mean_norm, 2) if mean_norm is not None else None,
            "mean_char_retention_pct": round(mean_char, 2) if mean_char is not None else None,
            "mean_fact_retention_pct": round(mean_fact, 2) if mean_fact is not None else None,
            "trials": trials,
        })

    by_label = {c["label"]: c for c in conditions}
    self_norm = by_label["SELF (amanda v13)"]["mean_normalized_delta_pp"]
    other_norm = by_label["OTHER (rhett v1)"]["mean_normalized_delta_pp"]
    scrambled_norm = by_label["SCRAMBLED (v13 shuffled + name-swap)"]["mean_normalized_delta_pp"]

    if scrambled_norm is not None and scrambled_norm >= 20:
        verdict = f"LEXICAL: SCRAMBLED normalized delta +{scrambled_norm:.2f}pp ≥+20pp — token-class base rates survive any LLM pass (weakest reading)"
    elif self_norm is not None and other_norm is not None and self_norm >= 20 and other_norm >= 20:
        verdict = f"GENERIC SUMMARIZATION: SELF +{self_norm:.2f} and OTHER +{other_norm:.2f} both ≥+20pp normalized — 'substrate preserves itself' framing collapses"
    elif self_norm is not None and other_norm is not None and self_norm >= 20 and other_norm <= 10:
        verdict = f"SELF-SPECIFIC: SELF +{self_norm:.2f} high; OTHER +{other_norm:.2f} ≤+10pp — interesting claim holds"
    else:
        verdict = f"MIXED/INDETERMINATE: SELF={self_norm}, OTHER={other_norm}, SCRAMBLED={scrambled_norm} — no clean rule fired; report values plainly"

    pre_reg["self_normalized_delta_pp"] = self_norm
    pre_reg["other_normalized_delta_pp"] = other_norm
    pre_reg["scrambled_normalized_delta_pp"] = scrambled_norm
    pre_reg["verdict"] = verdict
    pre_reg["conditions"] = conditions
    OUT.write_text(json.dumps(pre_reg, indent=2))

    print(f"\nE18 verdict: {verdict}")
    print(f"  SELF      normalized: {self_norm:+5.1f}pp" if self_norm is not None else "  SELF: no valid trials")
    print(f"  OTHER     normalized: {other_norm:+5.1f}pp" if other_norm is not None else "  OTHER: no valid trials")
    print(f"  SCRAMBLED normalized: {scrambled_norm:+5.1f}pp" if scrambled_norm is not None else "  SCRAMBLED: no valid trials")


if __name__ == "__main__":
    main()
