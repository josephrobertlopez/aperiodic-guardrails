# Singularity-BS-T3 — Correction-Count Decay Test

**Verdict:** `RSI_FEP_FALSIFIED`

## Series (completed sessions)

| session | version | rotation_ts | end_correction_count |
|--------:|--------:|:------------|---------------------:|
| 1 | v2 | 2026-05-03T00:00:00Z | 8 |
| 2 | v3 | 2026-05-10T00:00:00Z | 11 |
| 3 | v4 | 2026-05-13T00:00:00Z | 11 |
| 4 | v5 | 2026-05-24T00:00:00Z | 11 |
| 5 | v6 | 2026-05-24T22:49:00Z | 8 |
| 6 | v7 | 2026-05-26T01:32:00Z | 10 |

Live tail (excluded): v8, lower-bound substantive ~ 6

## Statistics

- Mann-Kendall tau = `-0.0778`  (scipy kendalltau)
- p (two-sided) = `0.8371`
- Normal-approx z = `0.0000`, p = `1.0000`
- OLS slope = `0.0286` (per session), R^2 = `0.0013`
- Bootstrap 95% CI on slope = `[-1.0909, 1.0909]`
- Lag-1 autocorrelation = `-0.1718` (flag if |r|>0.7: no)

## Reading

With N=6 completed sessions, the burden of proof on the RSI/FEP-decay claim is a Mann-Kendall tau strictly < 0 at p<0.05. 
The observed tau=-0.078, p=0.837. 
This does **not** clear the decay bar; under brutal-honesty default, RSI/FEP claim is **falsified** by this test on this metric.

## Caveat

End-counts are bounded above by ~11 because the substrate compacts at correction-obs>10 watchdog. 
This caps any 'growth' signal at the ceiling. A flat/no-trend result is consistent with both 'no improvement' and 'watchdog-saturated load'. Under brutal-honesty default the burden is on the RSI claim to show strictly-below-ceiling decay; absence of decay = falsified, not 'inconclusive'.
