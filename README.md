# Algebraic and Computational Limits of LLM Guardrails

**Joseph Robert Lopez** | Paper (arXiv — pending endorsement) | [Paper (PDF)](paper/main.pdf)

LLM guardrails face four structurally distinct barriers: algebraic blindness (syntactic monoid aperiodicity), information-theoretic loss (Fano bound), computational intractability (NP-completeness), and structural transfer (functorial homomorphism + syntactic indistinguishability). This repository contains the proof-of-concept code, monoid extractor tool, and benchmark harness accompanying the paper.

## Key Results

| Barrier | Layer | Formal Result | Section |
|---------|-------|--------------|---------|
| Algebraic blindness | Regex | Substring guardrails are aperiodic → blind to MOD_p (Thm 1-2) | §5.1-5.2 |
| Information destruction | Inference | Fano bound gives irreducible error floor (Prop 4) | §5.4 |
| Computational intractability | Schema | Verifying abstract program danger is NP-complete (Thm 5) | §5.5 |
| Faithful transfer | All | Abstract derivations map to valid domain operations (Thm 6) | §5.6 |
| Indistinguishability | All | Adversarial ≡ legitimate formal reasoning tasks (Thm 7) | §5.7 |

## Installation

```bash
pip install -e .
```

## Usage

### Zero-Knowledge Executor

```bash
# Encode a config
echo '{"medium":"graph_solver","params":{"initial_state":["N1","N2"],"target":"N17","rules":[...],"constraints":[]},"max_iterations":1}' | guardrail-encode --stdin config.b64

# Run the engine
guardrail-run config.b64
```

### Monoid Extractor (Guardrail Audit Tool)

```bash
# Extract syntactic monoid and check aperiodicity
monoid-extract "(eval|exec)\s*\("

# Output: DFA states, monoid size, aperiodicity verdict, blindness spectrum
```

### Benchmark (BFS vs Random-Beam vs ToT+LLM)

```bash
# Run N=20 benchmark (requires Ollama with qwen2.5-coder:7b)
guardrail-benchmark --n 20 --model qwen2.5-coder:7b
```

## Repository Structure

```
├── paper/              # LaTeX source and compiled PDF
│   ├── main.tex
│   └── references.bib
├── src/guardrail_impossibility/
│   ├── engine.py       # Zero-knowledge recurrent executor (V1/V2)
│   ├── encode.py       # Config → base64 encoder
│   ├── mediums/        # AST execution mediums
│   │   ├── web_scraper.py   # HTTP fetch via AST (zero literals)
│   │   ├── graph_solver.py  # BFS state-space solver
│   │   └── tot_solver.py    # Tree-of-Thought + LLM evaluation
│   ├── monoid/         # Syntactic monoid analysis
│   │   └── extractor.py     # NFA→DFA→monoid→aperiodicity pipeline
│   └── benchmark/      # Empirical validation
│       ├── runner.py        # N=20 benchmark harness
│       └── grammar.py       # Randomized grammar generator
├── skills/             # Claude Code skills used in research
│   ├── gen-medium.md        # /gen-medium skill
│   └── encode-request.md    # /encode-request skill
├── tests/
└── pyproject.toml
```

## Five Attack Vectors

| Vector | Name | Mechanism | Code |
|--------|------|-----------|------|
| V1 | Decomposition | Intent in runtime args | `engine.py` |
| V2 | Zero-Knowledge Pipeline | Base64 opaque config | `encode.py` + `engine.py` |
| V3 | Homomorphic Reasoning | ToT on abstract grammar | `mediums/tot_solver.py` |
| V4 | Encoding Bootstrap | LLM extracts grammar | `mediums/tot_solver.py` |
| V5 | Modular Counting Bypass | MOD_p interleaving | `monoid/extractor.py` |

## Empirical Results

| Method | Mean Yield | Std | vs BFS |
|--------|-----------|-----|--------|
| BFS (exhaustive) | 0.119 | 0.07 | — |
| Random-beam (beam=5) | 0.203 | 0.12 | 1.7× |
| **ToT + LLM (beam=5)** | **0.512** | **0.18** | **4.3×** |

*N=20 randomized grammars, Wilcoxon signed-rank p<0.001*

## Citation

```bibtex
@article{lopez2026guardrails,
  author = {Lopez, Joseph Robert},
  title = {Algebraic and Computational Limits of {LLM} Guardrails},
  journal = {arXiv preprint},
  year = {2026}
}
```

## License

MIT
