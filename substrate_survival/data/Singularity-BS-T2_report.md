# Singularity-BS-T2 — Catastrophic Forgetting Test on Gnosis Vault

**Verdict:** `INDETERMINATE`
**n_docs:** 106 (across `lesson`, `reflection`, `insight`, `journal`, `observation`)
**Pre-registration:** `substrate_survival/specs/pre_registered/Singularity-BS-T2_20260530T040844Z.json` (locked before run)

## Falsifier results

| Predicate | Pass | Value |
|---|---|---|
| F1 corpus size >= 30 | YES | n=106 |
| F2 >=5 docs >60d AND >=5 docs <30d | **NO** | n>60d=0, n<30d=100; vault max age = 39.3 days |
| F3 top-3 self-query hit rate >= 0.80 | YES | 0.991 |
| F4 slope>0 AND p<0.05 AND R^2>0.10 | NO (diagnostic only) | slope=0.0130, p=0.046, R^2=0.038 |
| F5 baseline mean-shuffled-slope ~ 0 | YES | mean=-0.0001, SD=0.0063 |

## Why INDETERMINATE, not falsified

The pre-registered F2 contrast (>=5 lessons older than 60 days) is **unsatisfiable** on this substrate — the oldest document is 39 days old. The hypothesis is about decay over MONTHS; we lack the temporal lever arm to test it. INDETERMINATE is the honest call; the default-to-falsified rule is for interpretive uncertainty, not for "test cannot be run on this data."

## Diagnostic signal (informational, NOT a verdict)

The instrument is healthy:
- F3 self-retrieval at 99.1% top-3 — TF-IDF is finding own documents almost perfectly.
- F5 random-shuffle baseline slope is statistically indistinguishable from zero (mean -0.0001, SD 0.0063), so the regression machinery is unbiased.

Across the 0-39 day range we DO have:
- Slope = +0.013 rank-units per day (positive direction = older = worse rank).
- p = 0.046 (just barely under 0.05).
- **R^2 = 0.038** — explains <4% of variance.
- Rank range is [1, 4] with median 1; predicted rank shift over the full 39 days is ~0.5 — invisible at the precision the user cares about.

## Recommendation

Re-run when the vault has >=5 docs older than 60 days (around 2026-06-19 at the earliest, depending on which older notes exist outside the partitions sampled). At that point F2 will be satisfiable and the F4 regression on a real 60+ day lever arm will be the actual test.

Results JSON: `substrate_survival/data/Singularity-BS-T2_catastrophic_forgetting_results.json` (also `/tmp/singularity_bs_T2_results.json`).
