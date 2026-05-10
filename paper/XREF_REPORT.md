# Cross-Reference Integrity Report — Practice Piece vs Preprint

**Date**: 2026-05-09
**Auditor**: agent (mechanical grep + theorem-counter trace)
**Scope**: every preprint result that `CACM_ARTICLE_v21.md` and
`HANDOFF_FINAL.md` cite by number must exist with that number in
`paper/main.tex`.

## Method

`paper/main.tex` declares
`\newtheorem{theorem}{Theorem}[section]` with `proposition`, `corollary`,
`lemma`, `conjecture`, `definition`, `example`, `observation` all sharing
the theorem counter. So in section 6 (Impossibility Results, line 596), the
counter increments once per environment in source order:

| Section-6 slot | Source line | Environment | Label |
|---|---|---|---|
| 6.1 | 600 | theorem | `thm:substring-aperiodic` (Substring aperiodicity) |
| 6.2 | 700 | lemma | `lem:word-boundary` |
| 6.3 | 760 | theorem | `thm:blindness` (Guardrail blindness) |
| 6.4 | 843 | corollary | `cor:parity` (MOD_2 sufficiency) |
| 6.5 | 874 | proposition | `prop:composition` (Composition preserves aperiodicity) |
| 6.6 | 889 | corollary | `cor:starfree-class-closure` (Closure across the broader star-free class) |
| 6.7 | 920 | proposition | `prop:krohn-rhodes` (Blindness spectrum, after Straubing) |
| 6.8 | 959 | proposition | `prop:fano` (Information destruction) |
| 6.9 | 1005 | definition | `def:gidp` |
| 6.10 | 1018 | proposition | `thm:np` (NP-completeness of GIDP) |
| 6.11 | 1083 | proposition | `thm:transfer` (Faithful transfer / Free category functoriality) |
| 6.12 | 1136 | definition | `def:synequiv` |
| 6.13 | 1148 | observation | `thm:indistinguish` |

Section numbering in `main.tex`: 1=Prelude, 2=Intro, 3=Background, 4=Threat,
5=Algebraic Foundations, 6=Impossibility, 7=Attack Vectors, 8=Empirical,
9=PoC, 10=Defense, 11=Limitations, 12=Conclusion, 13=Agentic Methodology
(supplementary).

## Findings

### Practice piece v21 explicit references

| Cited in v21 | Maps to (main.tex) | Status |
|---|---|---|
| "Theorem 6.1 of the companion preprint" (substring star-free) | 6.1 = `thm:substring-aperiodic` (Substring aperiodicity) | **MATCH** |
| "Proposition 6.11 of the preprint" (Krohn-Rhodes blindness spectrum) | 6.11 = `thm:transfer` (Faithful transfer); the Krohn-Rhodes spectrum result is at 6.7 = `prop:krohn-rhodes` | **MISMATCH — needs fix in v22** |
| "Sections 7.3-7.4 of the preprint" (homomorphic-reasoning) | §7.3 = V3 Homomorphic Reasoning, §7.4 = V4 Encoding Bootstrap | **MATCH** |
| "§8.3's pilot finding that exhaustive grammar search outperforms..." | §8.3 = `sec:tot-benchmark` (Tree-of-Thought Benchmark) | **MATCH** |

### HANDOFF_FINAL Tier-1 mapping requirements

| Required cross-reference | main.tex slot | Status |
|---|---|---|
| Theorem 6.1 — substring aperiodicity | 6.1 ✓ | **MATCH** |
| Proposition 6.11 — Krohn-Rhodes blindness spectrum | actual is 6.7; 6.11 is `thm:transfer` | **MISMATCH** |
| §§7.3-7.4 — homomorphic-reasoning attack vectors | §7.3 V3, §7.4 V4 ✓ | **MATCH** |
| §8.3 — BFS-vs-ToT pilot | §8.3 = `sec:tot-benchmark` ✓ | **MATCH** |

## Recommendation (Joey-decision)

The Practice piece's "Proposition 6.11" anchor for the Krohn-Rhodes
blindness spectrum is off by four slots. There are two repair paths:

**Option A (preferred — edit Practice piece):** in `CACM_ARTICLE_v22.md`
line 171, change `Proposition 6.11 of the preprint` → `Proposition 6.7 of
the preprint`. One-character mechanical change; no math impact; preserves
preprint as the canonical source. Verifiable with one `grep`.

**Option B (alternative — re-order preprint section 6):** move
`prop:krohn-rhodes` (currently line 920) to a later position so it lands at
slot 6.11. High-friction; risks breaking other cross-refs in §§7-12 that
already cite the existing slot numbering by `\ref{prop:krohn-rhodes}`;
breaks reproducibility against the v21 PDF that may have already gone to
external readers.

**Defer to Joey.** Agent did not auto-apply Option A — the spec restricts
v22 edits to mechanical AAF removal and DOI insertion until Joey reviews
this report.

## Theorem 6.4 / 6.6 references (HANDOFF_FINAL Tier 2 only — deferred)

`HANDOFF_FINAL.md` Component 1 Tier 2 mentions tightening "Theorem 6.6's
non-degenerate alignment hypothesis." Slot 6.6 is currently
`cor:starfree-class-closure` (a closure result, no "non-degenerate
alignment" hypothesis). The earlier git history shows commit 1619584
removed the original Theorem 6.6 ("cut T6.6 (Regime 2 redundant w/ §8.1)"),
which means the Tier-2 hypothesis-tightening item is now stale — the
hypothesis no longer exists in the paper. **Defer to Joey** with note: the
Tier-2 item may be obsoleted by the prior T6.6 removal.

## Sanity: §7.3 / §8.3 framing

Both sections exist with the labels v21 expects:

- `\subsection{V3: Homomorphic Reasoning (Tree-of-Thought on Abstract Grammar)}\label{sec:v3}` (main.tex line 1293) → §7.3 ✓
- `\subsection{V4: Encoding Bootstrap}\label{sec:v4}` (main.tex line 1340) → §7.4 ✓
- `\subsection{Tree-of-Thought Benchmark}\label{sec:tot-benchmark}` (main.tex line 1599) → §8.3 ✓
- v21 references `BFS dominates` (line 173); main.tex `sec:tot-benchmark`
  contains the matching empirical paragraph. No content mismatch on the
  framing axis.
