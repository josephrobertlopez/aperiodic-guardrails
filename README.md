# Algebraic and Computational Limits of LLM Guardrails

**Joseph Robert Lopez** | Paper (arXiv — pending endorsement) | [Paper (PDF)](paper/main.pdf)

LLM guardrails face four structurally distinct barriers: algebraic blindness (syntactic monoid aperiodicity, unconditional), an information-theoretic lower bound (Fano-type, illustrative under uniformity), computational intractability (NP-hardness via 3-SAT), and structural transfer (functorial homomorphism + syntactic indistinguishability under opacity). This repository contains the proof-of-concept code, monoid extractor tool, and benchmark harness accompanying the paper.

## Key Results

| Barrier | Layer | Formal Result | Section |
|---------|-------|--------------|---------|
| Algebraic blindness (unconditional) | Regex | Substring guardrails are aperiodic → blind to MOD_p encodings | §6.1–6.2 |
| Information destruction (illustrative) | Inference | Fano bound under uniform prior on concrete artifacts | §6.5 |
| Computational intractability | Schema | Verifying abstract program danger is NP-complete | §6.6 |
| Faithful transfer (unconditional) | All | Abstract derivations map to valid domain operations | §6.7 |
| Indistinguishability (under opacity) | All | Adversarial prompts ⊆ legitimate formal-reasoning prompts as string sets | §6.8 |

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
# Run N=50 benchmark (requires Ollama with llama3.1:8b)
guardrail-benchmark --n 50 --model llama3.1:8b
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
│       ├── runner.py        # N=50 benchmark harness
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

| Method | Mean Yield | 95% CI | vs BFS |
|--------|-----------|--------|--------|
| **BFS (exhaustive)** | **0.466** | [0.448, 0.483] | — |
| Random-beam (beam=5) | 0.172 | [0.131, 0.220] | 0.37× |
| ToT + LLM (beam=5) | 0.122 | [0.064, 0.185] | 0.26× |

*N=50 randomized grammars, seeds 0–49, llama3.1:8b, 90 s timeout per solver. Wilcoxon signed-rank, one-sided: BFS vs. ToT W=1275, p<0.001; BFS vs. Random-beam W=1225, p<0.001. BFS dominates: exhaustive search over small synthetic grammars outperforms LLM-heuristic pruning at this scale. The security claim of V3 (homomorphic-reasoning attack) does not depend on ToT outperforming BFS — it requires only the existence of a solver that produces valid derivations, which all three strategies demonstrate. An earlier N=20 ordering with ToT > BFS did not reproduce at N=50 and was retracted; see paper §8.2 for the reproducibility note.*

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
