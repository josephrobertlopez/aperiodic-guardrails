#!/usr/bin/env python3
"""E19 — frequency-weighted null for E12 (can challenge E16).

PRE-REGISTERED HYPOTHESIS (locked before observing output):
  If character vocab simply has higher source-corpus frequency, then a
  frequency-aware mechanical sampler (no LLM, no schema) would reproduce
  the +28pp character-over-fact delta E12 found. E16 used uniform-random
  sampling and got +1.8pp; E19 weights selection by log-tf-idf to see if
  the asymmetry recovers without an LLM.

PRE-REGISTERED DECISION RULE (locked before observing output):
  mean_delta_pp = mean(char_retention - fact_retention) across 3 cycles
  ≤ +5pp   -> FREQUENCY-RULED-OUT: E16 robust; LLM selects beyond counts
  +5..+15  -> MIXED: partial frequency contribution
  ≥ +15pp  -> E16 WAS AN ARTIFACT of uniform sampling; a smart extractor
              recovers the asymmetry with NO LLM. Walk back part of E16
              and say so plainly.

METHOD:
  Same cycles (v8→v9, v11→v12, v12→v13), same byte budgets as E16.
  Same E12 classifier (imported logic, not re-derived).
  Selection: TF-IDF-weighted random sentence sampling.
    - Build document-frequency over all 6 v(N) files (the substrate corpus).
    - For each sentence in v_from, compute sum_of_logTFIDF over its tokens.
    - Sample sentences with probability proportional to that score.
    - Continue until target_bytes reached.
  Seed 42, N=20 samples per cycle. Same as E16 for direct comparison.
"""
import json
import math
import random
import re
from collections import Counter
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
OUT = DATA / "e19_results.json"

# E12/E16 classifier — verbatim
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

CYCLES = [("v8", "v9"), ("v11", "v12"), ("v12", "v13")]
N_SAMPLES_PER_CYCLE = 20
CORPUS_VERSIONS = ["v8", "v9", "v10", "v11", "v12", "v13"]


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


def build_corpus_idf(versions):
    """Document-frequency over the substrate corpus (6 state files)."""
    df = Counter()
    n_docs = len(versions)
    for v in versions:
        text = (DATA / f"{v}_raw.md").read_text()
        seen = set(tokenize(text))
        for tok in seen:
            df[tok] += 1
    idf = {tok: math.log((1 + n_docs) / (1 + dfc)) + 1 for tok, dfc in df.items()}
    return idf, n_docs


def sentence_score(sentence, idf):
    """sum_t log(1 + tf_in_sentence) * idf_corpus."""
    tf = Counter(tokenize(sentence))
    return sum(math.log1p(c) * idf.get(tok, 0.0) for tok, c in tf.items())


def weighted_sample_without_replacement(items, weights, target_bytes, rng):
    """Pick sentences with prob proportional to weight, until target_bytes."""
    items = list(items)
    weights = list(weights)
    picked = []
    acc_bytes = 0
    while items and acc_bytes < target_bytes:
        total = sum(weights)
        if total <= 0:
            # fall back to uniform on remaining
            idx = rng.randrange(len(items))
        else:
            r = rng.random() * total
            cum = 0.0
            idx = len(items) - 1
            for i, w in enumerate(weights):
                cum += w
                if cum >= r:
                    idx = i
                    break
        s = items.pop(idx)
        weights.pop(idx)
        picked.append(s)
        acc_bytes += len(s.encode("utf-8")) + 1
    return "\n".join(picked)


def main():
    # Persist pre-registered rule BEFORE running anything substantive
    pre_reg = {
        "experiment": "E19 — frequency-weighted null for E12 (can challenge E16)",
        "pre_registered_rule": {
            "<=+5pp": "FREQUENCY-RULED-OUT — E16 robust; LLM selects beyond counts",
            "+5 to +15pp": "MIXED — partial frequency contribution",
            ">=+15pp": "E16 WAS AN ARTIFACT of uniform sampling; smart extractor recovers asymmetry with no LLM (E16 walk-back)",
        },
        "baseline_e12_llm_mean_delta_pp": 28.0,
        "baseline_e16_uniform_mean_delta_pp": 1.8,
        "method": "TF-IDF over 6-version substrate corpus; sentence score = sum_t log1p(tf)*idf; weighted-without-replacement sampling to target_bytes per E16 byte budgets; seed 42, N=20/cycle",
        "verdict": "PENDING_RUN",
        "results": None,
    }
    OUT.write_text(json.dumps(pre_reg, indent=2))

    # Build corpus IDF
    idf, n_docs = build_corpus_idf(CORPUS_VERSIONS)

    rng = random.Random(42)
    results = []
    for v_from, v_to in CYCLES:
        text_from = (DATA / f"{v_from}_raw.md").read_text()
        text_to = (DATA / f"{v_to}_raw.md").read_text()
        target_bytes = len(text_to.encode("utf-8"))
        sentences = split_sentences(text_from)
        weights = [sentence_score(s, idf) for s in sentences]

        src_classes = per_class_token_sets(text_from)
        src_char = sum(len(src_classes.get(c, set())) for c in CHAR_CLASSES)
        src_fact = sum(len(src_classes.get(c, set())) for c in FACT_CLASSES)

        cycle_samples = []
        for i in range(N_SAMPLES_PER_CYCLE):
            sample_text = weighted_sample_without_replacement(sentences, weights, target_bytes, rng)
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

        deltas = [s["delta_pp"] for s in cycle_samples]
        char_pcts = [s["char_retention_pct"] for s in cycle_samples]
        fact_pcts = [s["fact_retention_pct"] for s in cycle_samples]
        results.append({
            "cycle": f"{v_from}->{v_to}",
            "src_bytes": len(text_from.encode("utf-8")),
            "target_bytes": target_bytes,
            "src_char_tokens": src_char,
            "src_fact_tokens": src_fact,
            "mean_char_retention_pct": round(sum(char_pcts) / N_SAMPLES_PER_CYCLE, 2),
            "mean_fact_retention_pct": round(sum(fact_pcts) / N_SAMPLES_PER_CYCLE, 2),
            "mean_delta_pp": round(sum(deltas) / N_SAMPLES_PER_CYCLE, 2),
            "delta_min_pp": round(min(deltas), 2),
            "delta_max_pp": round(max(deltas), 2),
            "samples": cycle_samples,
        })

    mean_delta = sum(c["mean_delta_pp"] for c in results) / len(results)
    if mean_delta <= 5:
        verdict = f"FREQUENCY-RULED-OUT: mean delta +{mean_delta:.2f}pp ≤ +5pp threshold; E16 robust; LLM selects beyond corpus frequency"
    elif mean_delta >= 15:
        verdict = f"E16-WALK-BACK: mean delta +{mean_delta:.2f}pp ≥ +15pp threshold; smart extractor recovers asymmetry without LLM; part of E16's null was an artifact of uniform sampling"
    else:
        verdict = f"MIXED: mean delta +{mean_delta:.2f}pp falls in +5 to +15pp range; partial frequency contribution"

    pre_reg["e19_frequency_mean_delta_pp"] = round(mean_delta, 2)
    pre_reg["verdict"] = verdict
    pre_reg["results"] = results
    OUT.write_text(json.dumps(pre_reg, indent=2))

    print(f"E19 verdict: {verdict}")
    print(f"  E12 LLM:      +28.0 pp")
    print(f"  E16 uniform:  +1.8 pp")
    print(f"  E19 freq-wt:  +{mean_delta:.2f} pp\n")
    for c in results:
        print(f"  {c['cycle']:>10s}: char={c['mean_char_retention_pct']:>5.1f}% fact={c['mean_fact_retention_pct']:>5.1f}% delta={c['mean_delta_pp']:+5.1f}pp range [{c['delta_min_pp']:+5.1f}, {c['delta_max_pp']:+5.1f}]")


if __name__ == "__main__":
    main()
