#!/usr/bin/env python3
"""E16: Mechanical-summarizer null for the E12 Compaction Functor

PRE-REGISTERED HYPOTHESIS (written before running):
  If a deterministic mechanical summarizer with no model of "character vs fact"
  produces a character-over-fact retention delta similar to E12's measured
  +28pp mean, then E12's preservation pattern is reducible to a structural
  property of the data (char vocabulary has higher base-rate frequency,
  surviving any compression) rather than the LLM's self-summarization mechanism.

DECISION RULE (locked before observing output):
  mechanical_delta = char_retention% - fact_retention%
  - >= +15pp  -> STRUCTURAL: E12 functor holds even without LLM, audit hedge over-stated
  - +5 to +15 -> MIXED: both contribute
  - <= +5pp   -> LLM-SPECIFIC: audit's "tautology of LLM self-summarization" hedge stands

METHOD:
  For each cycle in {v8->v9, v11->v12, v12->v13}:
    1. Compute actual target byte ratio = bytes(v_to) / bytes(v_from)
    2. Mechanical sample: split v_from into sentences, randomly pick a subset
       totaling ~target_bytes (uniform random, no semantic weighting)
    3. Repeat sampling N=20 times to get distribution
    4. For each sample, compute char_class and fact_class retention using
       SAME classifier as E12 (e12_compaction_functor.py)
    5. Report mean delta across N=20 samples per cycle

SAMPLE PURITY:
  - Random seed fixed for reproducibility
  - No knowledge of section headers, schema, or character keywords used in selection
  - Selection is sentence-level random, not token-level (so we measure what
    survives at the granularity an extractive summarizer would operate at)
"""
import json
import re
import random
import sys
from pathlib import Path
from collections import Counter

DATA = Path(__file__).parent.parent / "data"
OUT = DATA / "e16_results.json"

# Same classifier as E12 (copied verbatim to avoid divergence)
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


def split_sentences(text):
    """Naive sentence-ish split. Good enough for a uniform random sampler."""
    # Split on blank lines (paragraph-ish), then on . ; ! ? at line end
    paragraphs = re.split(r"\n\s*\n", text)
    sentences = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Split on sentence-ending punctuation followed by whitespace+capital
        parts = re.split(r"(?<=[.!?;])\s+(?=[A-Z\(])", p)
        for s in parts:
            s = s.strip()
            if s:
                sentences.append(s)
    return sentences


def mechanical_sample(sentences, target_bytes, rng):
    """Uniform random sentence sampling, no semantic weighting."""
    shuffled = sentences[:]
    rng.shuffle(shuffled)
    acc = []
    acc_bytes = 0
    for s in shuffled:
        if acc_bytes >= target_bytes:
            break
        acc.append(s)
        acc_bytes += len(s.encode("utf-8")) + 1
    return "\n".join(acc)


CYCLES = [("v8", "v9"), ("v11", "v12"), ("v12", "v13")]
N_SAMPLES_PER_CYCLE = 20


def main():
    results = []
    rng = random.Random(42)

    for v_from, v_to in CYCLES:
        text_from = (DATA / f"{v_from}_raw.md").read_text()
        text_to = (DATA / f"{v_to}_raw.md").read_text()
        bytes_from = len(text_from.encode("utf-8"))
        bytes_to = len(text_to.encode("utf-8"))
        target_bytes = bytes_to  # match actual compression

        sentences_from = split_sentences(text_from)

        # Reference: source class breakdown
        src_classes = per_class_token_sets(text_from)
        src_char = sum(len(src_classes.get(c, set())) for c in CHAR_CLASSES)
        src_fact = sum(len(src_classes.get(c, set())) for c in FACT_CLASSES)

        cycle_samples = []
        for i in range(N_SAMPLES_PER_CYCLE):
            sample_text = mechanical_sample(sentences_from, target_bytes, rng)
            sample_classes = per_class_token_sets(sample_text)
            char_kept = sum(
                len(src_classes.get(c, set()) & sample_classes.get(c, set()))
                for c in CHAR_CLASSES
            )
            fact_kept = sum(
                len(src_classes.get(c, set()) & sample_classes.get(c, set()))
                for c in FACT_CLASSES
            )
            char_pct = 100 * char_kept / max(1, src_char)
            fact_pct = 100 * fact_kept / max(1, src_fact)
            cycle_samples.append({
                "sample_n": i + 1,
                "sample_bytes": len(sample_text.encode("utf-8")),
                "char_retention_pct": round(char_pct, 2),
                "fact_retention_pct": round(fact_pct, 2),
                "delta_pp": round(char_pct - fact_pct, 2),
            })

        char_pcts = [s["char_retention_pct"] for s in cycle_samples]
        fact_pcts = [s["fact_retention_pct"] for s in cycle_samples]
        deltas = [s["delta_pp"] for s in cycle_samples]

        results.append({
            "cycle": f"{v_from}->{v_to}",
            "src_bytes": bytes_from,
            "target_bytes": target_bytes,
            "n_sentences_src": len(sentences_from),
            "src_char_tokens": src_char,
            "src_fact_tokens": src_fact,
            "n_samples": N_SAMPLES_PER_CYCLE,
            "mean_char_retention_pct": round(sum(char_pcts) / N_SAMPLES_PER_CYCLE, 2),
            "mean_fact_retention_pct": round(sum(fact_pcts) / N_SAMPLES_PER_CYCLE, 2),
            "mean_delta_pp": round(sum(deltas) / N_SAMPLES_PER_CYCLE, 2),
            "delta_min_pp": round(min(deltas), 2),
            "delta_max_pp": round(max(deltas), 2),
            "samples": cycle_samples,
        })

    overall_mean_delta = sum(c["mean_delta_pp"] for c in results) / len(results)
    if overall_mean_delta >= 15:
        verdict = "STRUCTURAL: mechanical sampling reproduces E12 pattern; E12 functor holds even without LLM; audit hedge over-stated"
    elif overall_mean_delta <= 5:
        verdict = "LLM-SPECIFIC: mechanical sampling does NOT reproduce E12 pattern; audit's 'tautology of LLM self-summarization' hedge stands"
    else:
        verdict = f"MIXED: mechanical sampling produces +{overall_mean_delta:.1f}pp (vs E12 LLM +28pp); both mechanisms contribute"

    summary = {
        "experiment": "E16 mechanical-summarizer null for E12",
        "pre_registered_decision_rule": {
            ">=15pp": "STRUCTURAL — E12 holds without LLM",
            "+5 to +15": "MIXED",
            "<=+5pp": "LLM-SPECIFIC — audit hedge stands",
        },
        "e12_llm_mean_delta_pp": 28.0,
        "e16_mechanical_mean_delta_pp": round(overall_mean_delta, 2),
        "verdict": verdict,
        "n_samples_per_cycle": N_SAMPLES_PER_CYCLE,
        "cycles": results,
    }
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"E16 verdict: {verdict}")
    print(f"  E12 LLM mean delta: +28.0 pp")
    print(f"  E16 mechanical mean delta: +{overall_mean_delta:.1f} pp")
    print(f"\nPer-cycle:")
    for c in results:
        print(f"  {c['cycle']:>10s}: char={c['mean_char_retention_pct']:>5.1f}% fact={c['mean_fact_retention_pct']:>5.1f}% delta=+{c['mean_delta_pp']:>+5.1f}pp (range +{c['delta_min_pp']:>+5.1f} to +{c['delta_max_pp']:>+5.1f})")


if __name__ == "__main__":
    main()
