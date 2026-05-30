# Singularity-BS-T1 — Correction-Category Saturation Test

**Verdict:** `RSI_VARIETY_FALSIFIED`

**Reason:** F4_saturated=True (new_in_last_3_rotations=0); F6_growth=2 (need >=1)

- Pre-reg mtime: `2026-05-30T04:09:21.778693+00:00` (locked BEFORE run at `2026-05-30T04:14:31.002787+00:00`)
- Source: `/home/joey/.gnosis/.memory/memory.jsonl`
- Versions observed: 7 (amanda.Correction.open.v2, amanda.Correction.open.v3, amanda.Correction.open.v4, amanda.Correction.open.v5, amanda.Correction.open.v6, amanda.Correction.open.v7, amanda.Correction.open.v8)
- Distinct rail-class categories ever observed (primary regex): **11**
- Cumulative curve (primary): [9, 9, 9, 11, 11, 11, 11]
- New-per-rotation derivative (primary): [9, 0, 0, 2, 0, 0, 0]
- New categories in last 3 rotations (F4 threshold): **0**
- Mann-Kendall on derivative: S=-7, p=0.3675, trend=decreasing

## All distinct categories observed (canonical names, primary regex)
- COACHING/THERAPY DOMAIN RAIL
- COMMERCIAL/DOMAIN RAIL
- HOOK-ARBITRATION RAIL
- INSTRUMENT/MEASUREMENT RAIL
- PROVENANCE & CONSENT RAIL
- PUBLIC-SUBMISSION RAIL
- SELF-DISCIPLINE RAIL
- SYSTEM-NETWORK ISOLATION
- SYSTEM-OPS RAIL
- UNSOURCED-AGGREGATE / FALSE-CLOSE / CLOSURE-AMNESIA RAIL
- UNSOURCED-AGGREGATE / FALSE-CLOSE RAIL

## Sensitivity analysis (loose regex — includes appendix entries)

- Loose cumulative curve: [9, 10, 11, 13, 13, 14, 16]
- Loose derivative: [9, 1, 1, 2, 0, 1, 2]
- F4 saturated (loose)? **False** (new in last 3: 3)
- Loose regex picks up bottom-of-block 'NEW vN-CYCLE RAIL #X' single-rail appendix entries (v3.J=VOCABULARY-AS-ARCHITECTURE, v6.K=CROSS-REPO GREP COLLISION, v7.L=WRITE-INCREMENTAL-OR-LOSE-IT, v8.M=#R2). These are NOT new category buckets — they are single-rail historical entries that the substrate maintains chronologically. They appear once and then persist as audit lines, not as recurring class headers. Counting them as 'categories' over-inflates variety. Primary regex (A-I block only) is the semantically correct measurement.

## Method limitations

1. **Short history.** Substrate only goes back to v2 (2026-05-02). Total observed span ~24 days. Mann-Kendall p=0.37 is not statistically significant — derivative could be decreasing by chance. We do NOT lean on MK; verdict rests on F4 threshold.
2. **Conservative against the RSI claim.** We count UNSOURCED-AGGREGATE renamed-to-add-CLOSURE-AMNESIA as a NEW category (giving the substrate credit for variety expansion). Even so, F4 fires.
3. **Variety is ONE dimension.** Saturation here does not prove the substrate is non-improving overall — rail-instance count and per-rail elaboration both grow. T2/T3 cover those orthogonal dimensions.
4. **Regex-extracted taxonomy.** Categories are inferred from Amanda's own letter-prefixed section headers inside ACTIVE-RAIL-CORRECTIONS. If she silently merged two categories (e.g., COACHING/THERAPY → COMMERCIAL/DOMAIN at v5), we treat the rename as a new category. The merge itself is structural-change without variety-expansion.

## Interpretation

The rail-class taxonomy SATURATED early in Amanda's substrate lifecycle. The cumulative distinct-category set established by v2 was retained through v8 with little or no expansion. Instance-counts and individual rail numbers grew, but the higher-order category dimension did not. This is consistent with *pattern-completion within fixed variety* rather than recursive self-improvement on the variety dimension. RSI-variety claim FALSIFIED for this axis.
