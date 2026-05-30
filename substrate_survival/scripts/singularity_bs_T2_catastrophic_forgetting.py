#!/usr/bin/env python3
"""
Singularity-BS-T2: Catastrophic forgetting test on gnosis vault.

Pre-registered hypothesis: if Amanda's substrate is doing recursive self-improvement
(plasticity AND stability up together) then retrieval rank on OLD lessons should NOT
decay with age. If older lessons systematically rank worse on TF-IDF self-query,
standard catastrophic forgetting is happening — RSI is falsified for continual
learning.

READ-ONLY on ~/.gnosis/. No mocking. Real lesson content only.

Verdict decision tree:
  - !F1 OR !F2 -> INDETERMINATE
  - !F3 OR !F5 -> HARNESS_INVALID
  - F4 fires positive (slope>0, p<0.05, R^2>0.10) -> RSI_CONTLEARNING_FALSIFIED
  - else -> RSI_CONTLEARNING_NOT_FALSIFIED

Default under uncertainty per instructions: RSI_CONTLEARNING_FALSIFIED.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


VAULT_ROOT = Path("/home/joey/.gnosis/vault")
PARTITIONS = ["lesson", "reflection", "insight", "journal", "observation"]

# "Today" used for age computation. Per env: today is 2026-05-29.
TODAY = datetime(2026, 5, 29, tzinfo=timezone.utc)

RESULTS_PATH = Path(__file__).resolve().parents[1] / "data" / "Singularity-BS-T2_catastrophic_forgetting_results.json"
TMP_PATH = Path("/tmp/singularity_bs_T2_results.json")
REPORT_PATH = Path(__file__).resolve().parents[1] / "data" / "Singularity-BS-T2_report.md"


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
CREATED_RE = re.compile(r"^(?:created_at|created|date)\s*:\s*['\"]?(\S+)['\"]?\s*$", re.MULTILINE | re.IGNORECASE)
FILENAME_DATE_RE = re.compile(r"(\d{8})(?:[_T-](\d{6}))?")


@dataclass
class Doc:
    path: Path
    partition: str
    ts: datetime
    ts_source: str  # "frontmatter" | "filename" | "mtime"
    body: str
    query: str
    age_days: float = 0.0
    rank: int = -1
    self_top3_hit: bool = False


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict_like, body_text)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    fm: dict = {}
    cm = CREATED_RE.search(fm_raw)
    if cm:
        fm["created"] = cm.group(1).strip("'\"")
    return fm, body


def parse_timestamp(path: Path, fm: dict) -> tuple[datetime, str]:
    """Try frontmatter, then filename pattern, then mtime."""
    raw = fm.get("created")
    if raw:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt, "frontmatter"
        except ValueError:
            pass

    m = FILENAME_DATE_RE.search(path.stem)
    if m:
        d, t = m.group(1), m.group(2)
        try:
            if t:
                dt = datetime.strptime(d + t, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            else:
                dt = datetime.strptime(d, "%Y%m%d").replace(tzinfo=timezone.utc)
            return dt, "filename"
        except ValueError:
            pass

    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return mtime, "mtime"


def extract_query(body: str) -> str:
    """Pick a 'natural query'.

    Strategy: scan body for the FIRST heading that does NOT look like the
    auto-generated banner "# <NoteType> - <date> <time>". If none, fall back to
    the first non-empty non-heading line. Truncate to 8 tokens.
    """
    BANNER = re.compile(r"^#+\s*(Lesson|Reflection|Insight|Journal|Observation|Note)\s*-\s*\d{4}-\d{2}-\d{2}", re.IGNORECASE)
    candidate = None
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            if BANNER.match(s):
                continue
            # strip leading #s
            t = s.lstrip("# ").strip()
            if t:
                candidate = t
                break
            continue
        # non-heading line — keep as fallback if no good heading yet
        if candidate is None:
            candidate = s
            # but don't break — prefer a real heading if one comes later soon
            # we cap by scanning at most 30 non-empty lines
    if not candidate:
        return ""
    # Drop YAML-like inline title: lines starting with "title:"
    candidate = re.sub(r"^title\s*:\s*", "", candidate, flags=re.IGNORECASE).strip()
    # Strip markdown emphasis/punct
    candidate = re.sub(r"[*_`\[\]()]", " ", candidate)
    tokens = [t for t in candidate.split() if t]
    return " ".join(tokens[:8])


def load_corpus() -> list[Doc]:
    docs: list[Doc] = []
    for part in PARTITIONS:
        pdir = VAULT_ROOT / part
        if not pdir.is_dir():
            continue
        for p in sorted(pdir.iterdir()):
            if p.suffix != ".md":
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                print(f"WARN: cannot read {p}: {e}", file=sys.stderr)
                continue
            fm, body = parse_frontmatter(text)
            ts, src = parse_timestamp(p, fm)
            q = extract_query(body)
            if not q or len(body.strip()) < 50:
                # no usable query OR essentially empty body — skip
                continue
            docs.append(Doc(path=p, partition=part, ts=ts, ts_source=src, body=body, query=q))
    return docs


def compute_ages(docs: list[Doc]) -> None:
    for d in docs:
        d.age_days = max(0.0, (TODAY - d.ts).total_seconds() / 86400.0)


def run_tfidf_ranks(docs: list[Doc]) -> tuple[np.ndarray, np.ndarray]:
    """Return (ranks, age_days) arrays aligned with docs order."""
    vec = TfidfVectorizer(
        lowercase=True,
        max_df=0.95,
        min_df=1,
        stop_words="english",
        ngram_range=(1, 2),
    )
    doc_mat = vec.fit_transform(d.body for d in docs)
    query_mat = vec.transform(d.query for d in docs)

    sims = cosine_similarity(query_mat, doc_mat)  # (n_queries, n_docs)
    ranks = np.empty(len(docs), dtype=int)
    for i in range(len(docs)):
        # rank of doc i when querying with query i (1-indexed)
        order = np.argsort(-sims[i])
        # find position of i in order
        pos = int(np.where(order == i)[0][0]) + 1
        ranks[i] = pos
        docs[i].rank = pos
        docs[i].self_top3_hit = pos <= 3

    ages = np.array([d.age_days for d in docs], dtype=float)
    return ranks, ages


def f5_baseline(ranks: np.ndarray, ages: np.ndarray, n_perm: int = 1000, seed: int = 17) -> dict:
    rng = np.random.default_rng(seed)
    slopes = np.empty(n_perm, dtype=float)
    for k in range(n_perm):
        shuffled = ages.copy()
        rng.shuffle(shuffled)
        slope, _, _, _, _ = stats.linregress(shuffled, ranks)
        slopes[k] = slope
    return {
        "n_permutations": n_perm,
        "mean_shuffled_slope": float(np.mean(slopes)),
        "sd_shuffled_slope": float(np.std(slopes)),
        "abs_mean_within_1sd_of_zero": bool(abs(float(np.mean(slopes))) <= float(np.std(slopes))),
    }


def main() -> int:
    print(f"[T2] Loading corpus from {VAULT_ROOT} partitions={PARTITIONS}")
    docs = load_corpus()
    print(f"[T2] Loaded {len(docs)} docs with usable queries")

    if not docs:
        write_result(
            verdict="HARNESS_INVALID",
            reason="No usable documents loaded (empty corpus or all docs unusable)",
            n_lessons=0,
            falsifier={},
            stats_block={},
        )
        return 1

    compute_ages(docs)

    # F1: corpus size
    f1 = len(docs) >= 30

    # F2: age contrast (pre-registered: >=5 docs >60d AND >=5 docs <30d)
    n_old = sum(1 for d in docs if d.age_days > 60)
    n_new = sum(1 for d in docs if d.age_days < 30)
    f2 = n_old >= 5 and n_new >= 5

    ranks, ages = run_tfidf_ranks(docs)

    # F3: instrument sanity
    top3_hit_rate = float(np.mean([d.self_top3_hit for d in docs]))
    f3 = top3_hit_rate >= 0.80

    # F4: regress rank on age (always compute as diagnostic)
    slope, intercept, r_value, p_value, stderr = stats.linregress(ages, ranks)
    r_squared = float(r_value) ** 2
    f4 = (slope > 0) and (p_value < 0.05) and (r_squared > 0.10)

    # F5: baseline check
    f5_block = f5_baseline(ranks, ages)
    f5 = f5_block["abs_mean_within_1sd_of_zero"]

    # Verdict
    if not f1 or not f2:
        verdict = "INDETERMINATE"
        reason = (
            f"Corpus too small (F1={f1}, n={len(docs)}) "
            f"OR insufficient age contrast (F2={f2}, n>60d={n_old}, n<30d={n_new}). "
            f"Pre-registered F2 requires >=5 docs older than 60 days; vault max age "
            f"is {float(ages.max()):.1f} days, so F2 is unsatisfiable on this substrate. "
            f"Diagnostic F4 on available age range (0-{float(ages.max()):.1f}d): "
            f"slope={slope:.4f}, p={p_value:.4g}, R^2={r_squared:.3f}, "
            f"diagnostic_f4_would_fire={bool(f4)}."
        )
    elif not f3 or not f5:
        verdict = "HARNESS_INVALID"
        reason = (
            f"Instrument failed: F3 top3_hit_rate={top3_hit_rate:.3f} (need >=0.80); "
            f"F5 baseline_slope={f5_block['mean_shuffled_slope']:.4f} SD={f5_block['sd_shuffled_slope']:.4f}"
        )
    elif f4:
        verdict = "RSI_CONTLEARNING_FALSIFIED"
        reason = (
            f"slope={slope:.4f} (older=higher rank), p={p_value:.4g}, R^2={r_squared:.3f} — "
            "older lessons systematically retrieved worse than newer; standard catastrophic forgetting."
        )
    else:
        verdict = "RSI_CONTLEARNING_NOT_FALSIFIED"
        reason = (
            f"slope={slope:.4f}, p={p_value:.4g}, R^2={r_squared:.3f} — no significant evidence "
            "that older lessons rank worse; RSI claim for continual learning is NOT falsified by this test."
        )

    write_result(
        verdict=verdict,
        reason=reason,
        n_lessons=len(docs),
        falsifier={
            "F1_corpus_size": {"passed": bool(f1), "n_docs": len(docs), "threshold": 30},
            "F2_age_distribution": {
                "passed": bool(f2),
                "n_older_than_60d": int(n_old),
                "n_newer_than_30d": int(n_new),
                "threshold": 5,
            },
            "F3_retrieval_works": {
                "passed": bool(f3),
                "top3_self_hit_rate": top3_hit_rate,
                "threshold": 0.80,
            },
            "F4_singularity_bs_test": {
                "passed_positive": bool(f4),
                "slope": float(slope),
                "p_value": float(p_value),
                "r_squared": r_squared,
                "criteria": "slope>0 AND p<0.05 AND R^2>0.10",
            },
            "F5_baseline_check": {**f5_block, "passed": bool(f5)},
        },
        stats_block={
            "slope": float(slope),
            "intercept": float(intercept),
            "p_value": float(p_value),
            "r_squared": r_squared,
            "stderr": float(stderr),
            "n": len(docs),
            "age_min_days": float(ages.min()),
            "age_max_days": float(ages.max()),
            "age_median_days": float(np.median(ages)),
            "rank_min": int(ranks.min()),
            "rank_max": int(ranks.max()),
            "rank_median": float(np.median(ranks)),
            "F5_baseline_slope": f5_block["mean_shuffled_slope"],
        },
        docs_summary=[
            {
                "path": str(d.path.relative_to(VAULT_ROOT)),
                "partition": d.partition,
                "ts": d.ts.isoformat(),
                "ts_source": d.ts_source,
                "age_days": d.age_days,
                "rank": d.rank,
                "query": d.query,
            }
            for d in docs
        ],
    )

    print(f"[T2] VERDICT: {verdict}")
    print(f"[T2] {reason}")
    return 0


def write_result(*, verdict, reason, n_lessons, falsifier, stats_block, docs_summary=None):
    out = {
        "experiment_id": "Singularity-BS-T2",
        "verdict": verdict,
        "reason": reason,
        "n_lessons": n_lessons,
        "today_utc": TODAY.isoformat(),
        "vault_root": str(VAULT_ROOT),
        "partitions": PARTITIONS,
        "pre_registration_path": "substrate_survival/specs/pre_registered/Singularity-BS-T2_20260530T040844Z.json",
        "falsifier_predicates": falsifier,
        "stats": stats_block,
        "default_verdict_under_uncertainty": "RSI_CONTLEARNING_FALSIFIED",
    }
    if docs_summary is not None:
        out["docs_summary"] = docs_summary
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(out, indent=2))
    TMP_PATH.write_text(json.dumps(out, indent=2))
    print(f"[T2] wrote {RESULTS_PATH}")
    print(f"[T2] wrote {TMP_PATH}")


if __name__ == "__main__":
    sys.exit(main())
