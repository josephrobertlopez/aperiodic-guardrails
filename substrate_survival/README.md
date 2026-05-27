# Substrate-Survival Research Arc

Merged into aperiodic-guardrails on 2026-05-27 (branch: merge/substrate-survival-*).

## Provenance
Originally lived at `/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival/`
(NOT git-tracked, lost-on-disk-corruption risk before merger).

The old path is now a symlink for backwards compatibility with:
- 31 scripts that self-reference
- 23 vault notes that cite it
- gnosis_query / gnosis_search calls that hit BM25-indexed paths

## Contents
- data/ — 111 result + trial JSONL files (E29-E47 + xfam pilot)
- scripts/ — 56 per-experiment Python files
- experiments/ — design docs
- paper/ — substrate-survival paper draft
- SYNTHESIS_E38-E46.md — current synthesis

## Why merged into aperiodic-guardrails
Joey-direct decision 2026-05-27: "merge code but have papers being diff impls."
Two papers, one code substrate. Shared eval harness extracted to agent-eval-harness
(separate repo, sibling to this one).
