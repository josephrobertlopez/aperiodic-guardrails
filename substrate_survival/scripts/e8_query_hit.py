#!/usr/bin/env python3
"""E8: Query-Hit Distribution (BM25 proxy)
We have no gnosis_search logs; approximate dark-matter rate by running BM25 over the vault
with N representative queries, and checking what fraction of notes EVER appears in top-K.

Method: build a sparse BM25 index, run 50 queries derived from frequent frontmatter values
+ rail/schema/agent terms. Count hit fraction.

Falsifier:
  > 50% of notes never hit top-10 across any reasonable query = dark matter dominant
  < 20% never hit = healthy retrieval distribution
"""
import json
import math
import re
import random
from collections import Counter, defaultdict
from pathlib import Path

VAULT = Path.home() / ".gnosis" / "vault"
OUT = Path(__file__).parent.parent / "data" / "e8_results.json"

TOKEN_PAT = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{2,}")

QUERIES = [
    "amanda rail compaction",
    "rhett percept quartet",
    "gnosis search BM25",
    "morgan adversary critique",
    "consolidation pass schema",
    "random channel sampling",
    "PHI discharge layer",
    "frontmatter ingest provenance",
    "Joey override refusal",
    "FIRE band headroom",
    "code monkey ollama",
    "LDD lattice driven development",
    "session start rehydration",
    "substrate write hard gate",
    "agent recorder check activity",
    "AAF affective attractor framework",
    "category theory functor",
    "deck commander mtg",
    "monorepo v2 spec",
    "GitNexus impact analysis",
    "AJ trauma relational",
    "GSD family geography",
    "Paxil medication discharge",
    "Cobblemon johto enhanced",
    "speckit tasks plan",
    "phantom hand percept actuator",
    "claude opus haiku model",
    "qwen2.5 coder local",
    "kronos GPU gateway",
    "wave-2-staging branch",
    "v12 v13 archived",
    "version misalignment canonical pair",
    "epistemics cycle compression",
    "outcome contact terminus",
    "orthogonal verification load bearing",
    "scope narrowing pivot",
    "fabricated aggregate claim",
    "bandwidth budget rail",
    "fast-fail no placeholders",
    "metaprompting decision tree",
    "spec driven development",
    "BDD feature contract",
    "test driven behave pytest",
    "memory MCP entity",
    "vault partition reference",
    "zettelkasten note ingest",
    "stranded PR orphan main",
    "wave staging push merge",
    "channel mismatch correction",
    "asymmetric rotation cycles",
]


def tokenize(text):
    return [t.lower() for t in TOKEN_PAT.findall(text)]


def build_bm25(notes):
    df = Counter()
    docs = {}
    doc_lens = {}
    for note_id, text in notes.items():
        toks = tokenize(text)
        docs[note_id] = Counter(toks)
        doc_lens[note_id] = len(toks)
        for term in set(toks):
            df[term] += 1
    n = len(docs)
    avgdl = sum(doc_lens.values()) / max(1, n)
    return docs, doc_lens, df, n, avgdl


def bm25_score(query_toks, doc_id, docs, doc_lens, df, n, avgdl, k1=1.5, b=0.75):
    score = 0.0
    doc = docs[doc_id]
    dl = doc_lens[doc_id]
    for term in query_toks:
        if term not in df:
            continue
        idf = math.log((n - df[term] + 0.5) / (df[term] + 0.5) + 1)
        tf = doc.get(term, 0)
        denom = tf + k1 * (1 - b + b * dl / avgdl)
        if denom == 0:
            continue
        score += idf * (tf * (k1 + 1)) / denom
    return score


def main():
    # Load (sample 5000 for cost)
    all_paths = list(VAULT.rglob("*.md"))
    print(f"Loading {len(all_paths)} notes...")
    random.seed(42)
    notes = {}
    for p in all_paths:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            notes[str(p.relative_to(VAULT))] = text
        except Exception:
            continue

    print(f"Loaded {len(notes)} notes; building BM25...")
    docs, doc_lens, df, n, avgdl = build_bm25(notes)

    hit_counter = Counter()
    top_per_query = {}
    K = 10
    for q in QUERIES:
        q_toks = tokenize(q)
        scored = []
        for did in docs:
            s = bm25_score(q_toks, did, docs, doc_lens, df, n, avgdl)
            if s > 0:
                scored.append((s, did))
        scored.sort(reverse=True)
        top = scored[:K]
        top_per_query[q] = [(round(s, 3), d) for s, d in top]
        for _, d in top:
            hit_counter[d] += 1

    notes_hit_at_least_once = len(hit_counter)
    dark_matter = n - notes_hit_at_least_once
    out = {
        "n_notes": n,
        "n_queries": len(QUERIES),
        "top_k": K,
        "notes_hit_at_least_once": notes_hit_at_least_once,
        "dark_matter_count": dark_matter,
        "dark_matter_pct": round(100 * dark_matter / max(1, n), 2),
        "hit_frequency_distribution": dict(Counter(hit_counter.values())),
        "top_10_repeated_hubs": hit_counter.most_common(10),
        "sample_top_per_query": {q: tops[:3] for q, tops in list(top_per_query.items())[:10]},
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f"Dark matter: {dark_matter}/{n} = {out['dark_matter_pct']}%")


if __name__ == "__main__":
    main()
