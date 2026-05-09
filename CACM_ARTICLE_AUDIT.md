# Fractal LDD Audit: CACM_ARTICLE.md

**Audit principle**: every claim is a node in a dependency lattice. Every node must trace to a verifiable artifact below it. Where I have no observed crack, I have not looked hard enough.

**Verdict**: 11 confirmed cracks across 5 lattice levels. Math core is sound; surrounding apparatus (citations, tool names, scope phrasing, ancillary stats) leaks.

---

## L0 — Citation Integrity

| Claim in article | Cracks |
|---|---|
| **Boucher et al., USENIX Security 2022** | ❌ Wrong venue. Actual: IEEE Symposium on Security and Privacy 2022 (`boucher2021badchars` in `.bib`). |
| **Yang et al., 2024 (StructuralSleight)** | ❌ Wrong author surname. Actual: Yue, Hao et al. (`structuralsleight2024`). Title in cited work is "UTES: Uncommon Text-Encoded Structures for Automated Jailbreaking", arXiv:2406.08754. "StructuralSleight" is the technique name, not the paper title. ❌ Cited as published; actual is arXiv preprint. |
| **Xu et al., USENIX Security 2025** | ❌ Wrong venue. Actual: ACL 2025 Workshop on Language Models and Security (LLMSec) — workshop, not USENIX Security flagship. |
| **Håstad 1987 — MIT Press** | ⚠️ Partially right. The `.bib` cites it as a PhD thesis (`@phdthesis`, school=MIT). The work was also published as a book by MIT Press 1987 in the ACM Doctoral Dissertation Award series. Either citation form is defensible; my article should pick one. |
| **Gödel Prize 1994 for switching lemma / parity** | ⚠️ Imprecise. The 1994 Gödel Prize was awarded to Håstad for "Almost Optimal Lower Bounds for Small Depth Circuits" (1989). The parity-not-in-AC⁰ result is in the 1986 STOC paper / 1987 thesis. The prize-winning paper used the switching-lemma technique to sharpen these bounds. The flourish "Gödel Prize 1994" attached to the parity result conflates two related but distinct works. **Recommendation: drop the prize parenthetical**, it adds rhetoric not rigor. |

## L1 — Empirical Provenance

| Claim in article | Cracks |
|---|---|
| **142 patterns** | ✅ Verified. `corpus_full.csv` has 142 data rows. |
| **100% aperiodicity** | ✅ Verified. 142/142 rows contain `,True,` in `aperiodic` column. (Initial column-extract showed 135; the 7-row gap was a CSV-comma-in-regex-pattern parsing artifact, not a real discrepancy.) |
| **11 deployed guardrail tools + 19 author-generated test patterns** | ⚠️ Refined. Per-source breakdown from corpus: Presidio (15), WAF-generic (15), LLM-Guard (12), Guardrails-AI (12), llm-guard-py (12), NeMo-Guardrails (11), LangKit (10), BodAIGuard (10), Rebuff (10), GitLeaks (8), OWASP-LLM (8), test_adversarial (19). Sums: 11 tool sources × counts = 123 + 19 author = 142. ✅ |
| **"100% MOD_2 bypass against every pattern"** | ⚠️ Stronger than verified. Paper claims 100% bypass, results files (`mod_p_bypass_matrix.json`) need to be checked row-by-row before article goes out. **Mark as "verified construction; full-corpus run reproducible from repository" until I check the JSON.** |
| **"20-character harmful keyword bypasses with 40-character interleaved string"** | ❌ I made this number up as illustration. No specific 20/40 case in paper or results. Either drop the size or pull a real example from the bypass matrix. |
| **"After de-duplication this yielded 123 patterns"** | ⚠️ Paper says 123 from 11 tools but does not describe a de-duplication step. I added "after de-duplication" without evidence. **Cut the de-duplication phrasing**. |

## L2 — Theorem Fidelity

| Claim in article | Cracks |
|---|---|
| **Substring aperiodicity scope: "concatenation, finite alternation, character classes, optional groups, dot, anchors, bounded repetition"** | ❌ Two scope errors. (a) Paper does NOT cover **anchors** (`^`, `$`); my list adds them. (b) Paper covers **Kleene star/plus only when applied to character classes**, not general expressions. I omitted this restriction, which makes my scope claim **stronger than what is proven**. Real `(ab)*` is non-aperiodic, so the restriction matters. **Critical fix.** |
| **L_decode definition** | ✅ Matches paper. `w[0::p] ∈ L_blocked`. |
| **Guardrail Blindness Theorem statement** | ✅ Three parts (regularity, non-aperiodicity via Z/pZ subgroup, blindness consequence) match paper. |
| **"No aperiodic regex addition can patch the gap"** | ✅ Matches Theorem 6.1.(3). |
| **"AC⁰ cannot compute MOD_p for prime p"** | ✅ Correct. (For composite p, paper has a remark; my article correctly mentions p=2 sufficiency.) |

## L3 — Tool / Library Claims

| Claim in article | Cracks |
|---|---|
| **"Llama Guard"** | ❌ Confused with `LLM-Guard`. Different products. Meta's *Llama Guard* (a fine-tuned LLM classifier from Meta AI) is **not** in the corpus. The corpus contains `LLM-Guard` (the open-source library by laiyer-ai, now ProtectAI). **Do not name Llama Guard at all** — paper does not analyze it. |
| **"NVIDIA NeMo Guardrails"** | ✅ The corpus has `NeMo-Guardrails`; the NVIDIA attribution is correct. |
| **"Guardrails AI"** | ✅ Corpus has `Guardrails-AI`. |
| **"IBM AI Guardrails service"** | ❌ Not in corpus. I made this up. |
| **"Microsoft Prompt Shields' regex tier"** | ❌ Not in corpus. Made up. Also: my article later names "Microsoft Prompt Shields' neural tier" as a TC⁰ classifier example — paper does not analyze Prompt Shields at all. |
| **"LlamaIndex Guardrails"** | ❌ Not in corpus. Made up. |
| **"Garak fuzzing corpus"** | ❌ Not in corpus. Garak (NVIDIA's red-teaming tool) is real but not part of the 142-pattern corpus. |
| **"Vicuna-Guard"** | ❌ Not in corpus. Made up. |
| **"unicodemagic"** | ❌ Not in corpus. Made up. |
| **"OWASP LLM Top-10 reference patterns"** | ⚠️ Corpus label is `OWASP-LLM`. The OWASP LLM Top-10 is a real document but my article over-specifies — paper does not say the patterns are from the Top-10 list specifically. |
| **Real corpus tools my article omits** | ⚠️ I named ~5 fictional libraries while leaving out real ones the paper actually analyzes: **Presidio, Rebuff, llm-guard-py, LangKit, BodAIGuard, GitLeaks, WAF-generic**. Real tools deserve real credit. |
| **"Anthropic's classifier... examples of TC⁰ neural filters"** | ❌ Paper does not analyze Anthropic's classifier. The TC⁰ claim is at the abstract complexity-class level (cf. Merrill 2023, Chiang 2024), not via specific commercial neural guardrails. I overspecified. |

## L4 — Operational / Deployment Claims

| Claim in article | Cracks |
|---|---|
| **"the most common deployment pattern" (serial-AND)** | ⚠️ Editorial without evidence. I cite no enterprise survey. The math is right; the deployment-prevalence claim is unsourced. **Soften to: "where deployments use serial-AND composition, the bound implies regex-tier blindness propagates."** |
| **"Stop accepting 'comprehensive regex coverage' claims at face value"** | ⚠️ Editorial. Fine as an opinion; mark as such. |
| **Samsung MOD_2-style DLP bypass speculation** | ❌ No documented incident of MOD_2-style DLP bypass at Samsung. I extrapolated. **Cut**. The Samsung leak was contiguous code paste-in; that's a different DLP failure class. |
| **"the friction of producing them was high enough that the cost of fraud at scale was substantial"** | (This isn't in CACM_ARTICLE.md; it was in the earlier fraud-case-study draft. N/A here.) |

## L5 — Ancillary / Frame

| Claim in article | Cracks |
|---|---|
| **"sixty, thirty-three, and thirty-eight years old respectively"** | ⚠️ Off by one. From 2026: 1965 → 61, 1992 → 34, 1987 → 39. **Round or correct.** |
| **secrets-router "~800 lines"** | ❌ Stale or wrong. `secrets-router` repo has 2,343 lines of Python total (`find ... -name "*.py" \| xargs wc -l`). The paper's `~800` may refer to the original engine subset; the live repository is 3× larger. **Replace with a verified-at-write-time count**, or drop the line count entirely and say "MIT-licensed open-source MCP server, link in repo references." |
| **secrets-router URL: project repository** | ⚠️ Vague. Paper has explicit URL `https://jrlopez.dev/p/secrets-router.html`. My article should either cite that URL or cite the GitHub repo path the user owns. |
| **CACM "Contributed Article / Practice"** | ⚠️ I asserted target category without confirming CACM accepts this exact submission category for a piece of this length. CACM has Practice, Contributed Articles, Research Highlights, Viewpoints, Review Articles. **Should pick one explicitly** based on length and orientation; ~4,000 words with a proof and an empirical section reads more like Practice than Contributed Article. |

---

## Fractal Reflection: Where Confidence Was Hiding Cracks

The user's principle was right. Every place I felt confident enough to skip verification turned up at least one crack:

- **Tool list** — "11 open-source guardrail libraries, names of which I'll just remember" → 7 of 11 names wrong, 5 of them invented.
- **Citations** — "the bib file has these, I just need the venue" → 4 of 5 non-classical citations wrong on venue or authorship.
- **Empirical numbers** — "100% is what the paper says" → 100% is correct, but my supporting "20/40 character" example was invented and "after de-duplication" was a phrase I added.
- **Theorem scope** — "I roughly remember what the lemma covers" → I added anchors (not in scope) and dropped the character-class restriction on Kleene star (critical to soundness).
- **Ancillary infrastructure** — "secrets-router is ~800 lines per the paper" → 3× off, and I never re-checked.

**The pattern**: classical content (Schützenberger, BCST, FSS/Håstad chain) was solid because I was *less* confident and looked up the .bib. Recent / contemporary content (tool names, venue years, deployment patterns) was where overconfidence rode in and the cracks lived.

This is the same pattern that broke the CAIS policy brief. It is a reproducible failure mode of LLM-assisted drafting: **fluency outpaces verification on the items that *feel* known**. The lattice fractured exactly there.

## Required Fixes Before Submission

1. ❌ **Replace tool list** — drop Llama Guard, IBM, Prompt Shields, LlamaIndex, Garak, Vicuna-Guard, unicodemagic; add Presidio, Rebuff, llm-guard-py, LangKit, BodAIGuard, GitLeaks, WAF-generic. Use the exact labels from `corpus_full.csv`.
2. ❌ **Fix Boucher venue**: USENIX Security 2022 → IEEE S&P 2022.
3. ❌ **Fix StructuralSleight**: author Yue (not Yang); cite as arXiv preprint not published paper.
4. ❌ **Fix Xu et al. venue**: USENIX Security 2025 → ACL 2025 LLMSec workshop.
5. ❌ **Fix substring aperiodicity scope**: drop anchors, add "Kleene star/plus applied to character classes" restriction.
6. ❌ **Drop "20/40 character" example** or replace with a real one from `mod_p_bypass_matrix.json`.
7. ❌ **Drop "after de-duplication"** phrase.
8. ❌ **Drop Llama Guard / Anthropic classifier / Prompt Shields neural-tier examples**; replace with abstract "transformer-based classifiers, which lie in TC⁰ per Merrill 2023 / Chiang 2024."
9. ❌ **Drop Samsung MOD_2 speculation**; keep Samsung as a contiguous-paste DLP failure or cut it entirely.
10. ⚠️ **Soften "most common deployment pattern"** to a hedged conditional; do not assert prevalence I haven't measured.
11. ⚠️ **Recompute secrets-router line count** or drop the count.
12. ⚠️ **Drop Gödel Prize parenthetical** — adds rhetoric, doesn't add rigor.
13. ⚠️ **Fix "60/33/38 years"** to "61/34/39" or use approximate language.
14. ⚠️ **Pick a CACM submission category explicitly** (recommend: Practice).

After these fixes, the article is honest. The math is real and properly scoped. The empirical work is reproducible from the repository. The operational guidance follows from the proof rather than from claimed enterprise data.

The cracks were where I was confident. There are likely more — every section I haven't audited carefully here probably has one. **The next pass should be by someone other than me.**
