# Artifacts: The Algebraic Blind Spot in Pattern-Matching Defenses

Companion artifacts for the CACM Practice piece "The Algebraic Blind Spot in
Pattern-Matching Defenses" and its companion technical preprint
*Algebraic and Computational Limits of LLM Guardrails*.

These artifacts reproduce every empirical claim in the article and preprint:
the 142-pattern corpus survey, the MOD_p bypass matrix, the printable-filler
extension, the library-pattern bypass survey, the non-LLM defense-class
bypass against ModSecurity OWASP CRS and SpamAssassin, and the
LLM-decoder-pilot validation.

## Reproduction

```bash
# 1. Install minimal dependencies (only the LLM pilot tool needs anything
#    third-party; everything else is Python 3 stdlib).
pip install -r tools/requirements.txt

# 2. Run the monoid extractor over the full corpus.
python tools/audit_v14.py corpus_full.csv > monoid_report.txt

# 3. Reproduce the non-LLM defense-class bypass (ModSecurity + SpamAssassin).
python tools/non_llm_defense_bypass.py
# Writes results/non_llm_defense_bypass.json (compare against the bundled file).

# 4. Reproduce the library-pattern bypass survey
#    (LLM-Guard, llm-guard-py, Rebuff, Guardrails-AI, Presidio, GitLeaks,
#     LangKit, BodAIGuard).
python tools/library_pattern_bypass.py

# 5. Reproduce the MOD_p bypass matrix.
python tools/generate_mod_p_matrix.py

# 6. Reproduce the printable-filler bypass extension.
python tools/printable_filler_bypass.py

# 7. (Optional) Re-run the LLM decoder pilot. Requires a local Ollama
#    endpoint or any OpenAI-compatible chat-completions endpoint reachable
#    from the host; see tools/llm_decode_pilot_v2.py for the env vars.
python tools/llm_decode_pilot_v2.py
```

Total runtime on commodity hardware (no GPU): ~60 seconds for the corpus
audit and the bypass pilots. The optional LLM decoder pilot adds 5-15
minutes depending on the upstream endpoint.

## Contents

### `tools/`
- `audit_v14.py` — monoid extractor; given a regex, computes the minimal
  DFA, enumerates the transition monoid, and outputs the blindness
  spectrum (the set of primes p for which the pattern is provably
  MOD_p-blind).
- `non_llm_defense_bypass.py` — drives the ModSecurity OWASP CRS and
  SpamAssassin bypass test against three filler choices (NULL, SPACE, ZWSP).
- `library_pattern_bypass.py` — surveys patterns from eight production
  guardrail libraries.
- `generate_mod_p_matrix.py` — builds the four-prime bypass matrix.
- `printable_filler_bypass.py` — extends the bypass to seven printable
  filler codepoints.
- `llm_decode_pilot_v2.py` — optional LLM-decoder pilot.
- `requirements.txt` — Python deps (only `requests`).

### `corpus_full.csv`
142 patterns from twelve sources (LLM-Guard, llm-guard-py, Rebuff,
Guardrails-AI, Presidio, GitLeaks, LangKit, BodAIGuard, ProtectAI test
adversarial, ModSecurity OWASP CRS, SpamAssassin, WAF-generic). Header
row included; 143 lines total.

### `results/`
Frozen empirical outputs cited verbatim by the article and preprint:
- `mod_p_bypass_matrix.json` — 14×4 = 56/56 bypassed across primes
  {2,3,5,7}.
- `printable_filler_bypass.json` — 56×7 = 392/392 bypassed across seven
  printable fillers.
- `library_pattern_bypass.json` — 48/48 baseline-matched library patterns
  bypassed.
- `non_llm_defense_bypass.json` — ModSecurity OWASP CRS and SpamAssassin
  bypass results (`crs_942270_union_select` ZWSP 1/1 etc.).
- `monoid_distribution.json` — distribution of monoid types over the 142
  patterns; 142/142 aperiodic.
- `transformer_tc0_validation.json` — TC^0 capacity-bound empirical
  validation.
- `e2e_llmguard_validation.json` — end-to-end LLM-Guard validation.
- `tot_n50_honest.json` — Tree-of-Thought benchmark (BFS-vs-ToT, n=50).
- `class_c_adaptive_adversary.json`, `class_c_defense_test.json` —
  Class C (homomorphic-reasoning) adaptive-adversary results.
- `llm_decode_pilot.json`, `llm_decode_pilot_v2.json` — LLM decoder pilot
  outputs.
- `comprehensive_empirical_validation.json` — combined-results manifest.
- `library_normalization_survey.md` — surveyed library normalization
  pipelines, written-out as a markdown summary.

## Citation

Lopez, J. R. (2026). *Artifacts for "The Algebraic Blind Spot in
Pattern-Matching Defenses"*. Zenodo. https://doi.org/[DOI B — to be
minted at deposit]

## License

- Code (`tools/*.py`, `tools/requirements.txt`): MIT.
- Data (`corpus_full.csv`, `results/*`): CC-BY 4.0.

See `LICENSE` for full text of both.

## Provenance

Every numerical claim, citation, and inline `(verified: ...)` anchor in
the article was re-checked against this bundle prior to deposit. The
bundle is frozen at the time of CACM submission; future revisions will
ship as `v2`, `v3`, etc., with the base Zenodo DOI preserved across
versions.
