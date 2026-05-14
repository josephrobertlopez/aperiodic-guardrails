# Aperiodic Guardrails — The Algebraic Blind Spot in Pattern-Matching Defenses

**Joseph Robert Lopez**

Substring-matching pattern tiers — regex WAFs, spam filters, secret scanners, and LLM guardrails currently shielding production systems — share a structural property that determines what they can and cannot see. The property is aperiodicity of the syntactic monoid, and its consequence is concrete: no pattern in this class can decide whether a count is even or odd. Payloads encoded across alternating positions (MOD₂) bypass the tier, because deciding the alternation is precisely the modular-counting predicate the tier provably cannot compute.

This repository contains the artifacts accompanying the result: a CACM Practice piece for security architects, a 27-page technical preprint with full proofs, a 142-pattern corpus from twelve sources, and the monoid-extraction tooling.

## Headline numbers

| Measurement | Result |
|---|---|
| 142 patterns from 12 sources | 100% star-free aperiodic |
| MOD₂ bypass under printable filler | 392/392 |
| LLM-Guard default regex on MOD₂/MOD₃-encoded payloads | 0% detection |
| Parallel-OR composition with a TC⁰ neural tier | 95–100% detection |
| 14,753-parameter transformer on MOD₂/₃/₅/₇ | 90/90/100/100% |

## Reading order

1. **CACM Practice piece** — `CACM_ARTICLE_v22.md` / `CACM_ARTICLE_v22.pdf` (~11pp, operational, architectural checklist).
2. **Technical preprint** — `paper/main.pdf` (27pp, formal apparatus: substring-aperiodicity theorem, Krohn-Rhodes audit construction, composition laws, homomorphic-reasoning attack vectors). Deposited at Zenodo: <https://doi.org/10.5281/zenodo.20103491>.
3. **Artifact bundle** — `zenodo_artifact_bundle.zip` (142-pattern corpus, monoid extractor, bypass harnesses, pilot result JSONs). Deposited at Zenodo: <https://doi.org/10.5281/zenodo.20103493>.

The argument chains three classical theorems onto an empirical security setting: Schützenberger 1965 (star-free ↔ aperiodic) → Barrington-Compton-Straubing-Thérien 1992 (aperiodic ↔ AC⁰) → Furst-Saxe-Sipser 1981 (PARITY ∉ AC⁰). The novelty is the diagnostic, the measurement, and the architectural conclusion.

## Repository layout

```
CACM_ARTICLE_v22.md           # Practice piece source (canonical)
CACM_ARTICLE_v22.pdf          # Practice piece rendered
paper/                        # Technical preprint
  main.tex                    #   LaTeX source
  main.pdf                    #   rendered preprint (Zenodo 20103491)
  references.bib              #   bibliography
  supplementary/              #   appendix PoC source
  ZENODO_DOI_A.txt            #   preprint DOI marker
  ZENODO_DOI_B.txt            #   artifact bundle DOI marker
zenodo_artifact_bundle.zip    # Artifact bundle (Zenodo 20103493)
corpus_full.csv               # 142-pattern corpus (twelve sources)
src/aperiodic_guardrails/     # Code accompanying the paper
  engine.py                   #   V1/V2 zero-knowledge executor
  encode.py                   #   config → base64 encoder
  monoid/extractor.py         #   NFA → DFA → monoid → aperiodicity pipeline
  mediums/                    #   AST execution mediums (graph_solver, tot_solver, web_scraper)
  defense/                    #   parallel-OR composition + neural detector + preprocessing
  benchmark/                  #   N=50 benchmark harness
tools/                        # Pilot harnesses producing the cited result JSONs
  audit_v14.py                #   monoid extractor (cited in paper §6, table 1)
  generate_mod_p_matrix.py    #   results/mod_p_bypass_matrix.json
  library_pattern_bypass.py   #   results/library_pattern_bypass.json
  non_llm_defense_bypass.py   #   results/non_llm_defense_bypass.json (WAF + spam-filter pilots)
  printable_filler_bypass.py  #   results/printable_filler_bypass.json
  llm_decode_pilot.py(_v2)    #   results/llm_decode_pilot{,_v2}.json
  build_paper.sh              #   Docker-based preprint builder
results/                      # JSON outputs cited inline in v22 and the preprint
tests/                        # pytest suite covering monoid, engine, composition, MOD_p
skills/research-doc-targeting.md  # Audience-targeting methodology (CACM-Practice / CAIS-Policy templates)
```

## Install

```bash
pip install -e .
```

Tests:

```bash
pytest tests/
```

Monoid extractor on a single pattern:

```bash
python -m aperiodic_guardrails.monoid.extractor "(eval|exec)\s*\("
```

## Citation

```bibtex
@article{lopez2026aperiodic,
  author  = {Lopez, Joseph Robert},
  title   = {Algebraic and Computational Limits of {LLM} Guardrails},
  journal = {Zenodo preprint},
  year    = {2026},
  doi     = {10.5281/zenodo.20103491}
}

@misc{lopez2026artifacts,
  author       = {Lopez, Joseph Robert},
  title        = {Aperiodic Guardrails: Artifact Bundle},
  year         = {2026},
  doi          = {10.5281/zenodo.20103493},
  howpublished = {Zenodo}
}
```

## License

MIT (see `LICENSE`).
