# Security Paper Handoff

**Paper:** "Algebraic and Computational Limits of LLM Guardrails"
**Author:** Joseph Robert Lopez
**Date:** 2026-03-29
**Commit:** 446f518

---

## Status: Ready for Zenodo Submission

Paper compiled (26 pages, zero errors). 93 tests passing. All evidence committed.

---

## What Was Done (Mar 26-29)

### Paper Improvements (+500 net lines)

| Section | What was added |
|---|---|
| §5.4 | Composition preserves aperiodicity (Proposition) |
| §5.6 | GIDP scope clarification (hardness is in search, not eval) |
| §5.8 | Downgraded Theorem → Proposition (was tautological) |
| §7.3 | TCP state machine — second benign domain |
| §7.3 | Defense classification — aspirin = Class C, same Q as secrets-router |
| §9.2 | TC⁰ empirical validation (1-layer transformer, 14K params, MOD_2-7) |
| §9.2 | MathPrompt + Proof-of-Guardrail citations |
| §9.3 | **Filter Composition Laws** — 5-item Proposition, all proven + validated |
| §9.3 | **Empirical table** — 29K tests, regex 0% → neural 98-100% |
| §9.3 | **Neural evasion table** — 8 attacks, V1-V4 evade both |
| §9.3 | **Three attack classes** (A/B/C), minimum covering |S|=5 |
| §9.5 | **E2E against LLM Guard** — 23 real patterns, 0%→100% |
| §9.6 | **secrets-router case study** — execution-layer defense |
| §9.6 | **Interpretation Firewall** — architecture for Class C |
| §10 | Fano sensitivity note strengthened |
| App B | Methodology compressed 140→15 lines |
| Refs | +3 citations (MathPrompt, PoG, Strobl) |
| Fixes | MacLane1998→maclane1971, def:regex-guard→guardrail |

### New Code (272 LOC)

```
src/aperiodic_guardrails/defense/
├── preprocessing.py      (107 LOC) — strip, decode, normalize, deleet
├── neural_detector.py    (83 LOC)  — bigram centroid classifier
└── filter_composition.py (82 LOC)  — parallel, serial, blend, pipeline
```

### New BDD Features (19 scenarios, ALL GREEN)

```
features/
├── filter_composition.feature     (5 scenarios)
├── neural_detection.feature       (5 scenarios)
├── preprocessing_defense.feature  (6 scenarios)
└── adaptive_adversary.feature     (3 scenarios)
```

### Empirical Results (29,150+ tests)

| File | What |
|---|---|
| comprehensive_empirical_validation.json | 53 patterns × 50 payloads × 11 encodings |
| e2e_llmguard_validation.json | 23 LLM Guard patterns, 0%→100% |
| transformer_tc0_validation.json | 1-layer transformer, MOD_2-7 generalization |
| class_c_defense_test.json | Naive adversary: 5/5 caught |
| class_c_adaptive_adversary.json | Adaptive adversary: 3/3 evade |

### Disclosure Status

| Vendor | Sent | Reply |
|---|---|---|
| ProtectAI (security@protectai.com) | 2026-03-26 | None |
| NVIDIA (psirt@nvidia.com) | 2026-03-26 | None |
| Guardrails AI (security@guardrailsai.com) | 2026-03-26 | None |
| **Embargo expires:** ~2026-06-24 (90 days) |

### Research Outreach

| Contact | Sent | Reply |
|---|---|---|
| Yi Zeng (R2-Guard, ICLR) | 2026-03-26 | None |
| Xunguang Wang (SoK, IEEE S&P) | 2026-03-26 | **Replied — open to collab** |
| Thilo Hagendorff (Nature Comms) | 2026-03-26 | None |
| 13 endorsement emails | 2026-03-21 | None (code 3YEWSA) |

---

## Peer Review Scores

| Axis | Score | Notes |
|---|---|---|
| Novelty | 7/10 | Algebraic blindness connection is genuine, filter composition is useful |
| Rigor | 7/10 | E2E validation + transformer TC⁰ test close the biggest gaps |
| Clarity | 8/10 | Well-structured, honest self-assessment, appendix cut |
| Reproducibility | 7/10 | 93 tests, all results as JSON, defense code in repo |
| Significance | 7/10 | 0%→100% on real LLM Guard + secrets-router implementation |
| **Verdict** | **Weak Accept → Accept** | All 3 reviewer requests addressed + 10 unrequested improvements |

---

## Immediate Next Actions (Priority Order)

| # | Action | Effort | Why |
|---|---|---|---|
| **1** | **Zenodo submit** | 30 min | Lock timestamp. No endorsement needed. |
| **2** | **Email Xunguang** | 15 min | He replied. Ask about endorsement. Send monoid predictions for his categories. |
| **3** | **Push to GitHub** | 5 min | `git remote add origin <url> && git push` |
| **4** | **IACR ePrint** | 30 min | Backup venue if arXiv endorsement stalls. Crypto-adjacent. |

---

## How to Resume

```bash
cd ~/Documents/aperiodic-guardrails

# Verify everything works
python3 -m pytest tests/ -q          # 59 passed
python3 -m behave features/          # 34 scenarios passed

# Compile paper
tectonic paper/main.tex              # 26 pages, zero errors

# View PDF
cp paper/main.pdf ~/Sync/aperiodic_guardrails_2026.pdf

# Submit to Zenodo
# → https://zenodo.org → New Upload → Upload PDF → Fill metadata → Publish
```

---

## Key Files

| File | Purpose |
|---|---|
| `paper/main.tex` | The paper (2,545 lines) |
| `paper/main.pdf` | Compiled PDF (260KB, 26 pages) |
| `paper/references.bib` | 49 entries |
| `src/aperiodic_guardrails/monoid/extractor.py` | The 858-line audit tool |
| `src/aperiodic_guardrails/defense/` | New defense package (272 LOC) |
| `corpus_full.csv` | 142 patterns, 100% aperiodic |
| `results/` | 8 empirical result JSONs |
| `features/` | 9 BDD features, 34 scenarios |
| `tests/` | 59 pytest tests |

---

## The Paper's Story Arc

```
Theory (§5):     Regex is blind — Schützenberger → AC⁰ → FSS
     ↓
Empirical (§7):  142 patterns confirm. BFS > ToT. Aspirin + TCP domains.
     ↓
Composition (§9.3): How to fix — filter algebra, parallel breaks ceiling
     ↓
E2E (§9.5):      0% → 100% on real LLM Guard patterns
     ↓
Implementation (§9.6): secrets-router — working execution-layer defense
     ↓
Classification (§9.3): Three classes. |S|=5 provably minimal.
     ↓
Limits (§9.6):   Adaptive adversary evades inference. Execution layer necessary.
```

The paper went from "here are impossibility results" to "here is the complete defense architecture with empirical validation at every layer."
