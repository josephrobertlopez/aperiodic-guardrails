# Publication Strategy and Pre-Submission Notes

Working notes for placing the manuscript in `paper/main.tex` ("Algebraic and Computational Limits of LLM Guardrails"). Internal planning document; not part of the paper.

## 1. Paper one-paragraph summary

The paper proves that substring-matching regex LLM guardrails (as shipped in tools such as LLM Guard, NeMo Guardrails, and Guardrails AI) have aperiodic syntactic monoids, placing them in the circuit class AC⁰. By the chain Schützenberger (1965) → Barrington–Compton–Straubing–Thérien (1992) → Furst–Saxe–Sipser (1981) / Håstad (1987), AC⁰ provably cannot compute MOD_p predicates. Therefore any payload encoded by interleaving with arbitrary filler characters (every-other-character encoding being the canonical case) evades these guardrails, and no patch within the aperiodic-regex paradigm can fix it.

The algebraic blindness result is the unconditional core. Three weaker barriers — a Fano-type information-theoretic bound (illustrative under uniformity), NP-hardness of instantiation verification (via 3-SAT), and a free-category functoriality + opacity result for homomorphic-reasoning attacks — characterize related limits at the inference layer.

Five attack vectors operationalize the barriers; an empirical 142-pattern audit across 11 production tools shows 100% aperiodicity; an end-to-end test against ProtectAI's LLM Guard `BanSubstrings` scanner shows 0% detection on encoded payloads, recoverable to 95–100% via a parallel-composed neural filter plus preprocessing. Defense recommendation: migrate enforcement from the inference layer to the execution layer; `secrets-router` is offered as a deployable instance.

## 2. Source-of-truth discipline

When drafting external-facing material (pitches, summaries, talks), every quantitative claim and every cited reference must be verified against the paper or an external authoritative source before use. LLM-augmented drafting is fast but produces hallucinated stats and references at non-trivial rates.

Rules:

- All numbers traceable to `paper/main.tex` or `references.bib`.
- All cited external incidents traceable to a primary source (court records, vendor advisories, news of record).
- All cited prior work resolves to a real paper before the bibliography ships.

### 2.1 Canonical paper claims (verified against `paper/main.tex`)

- 142 production patterns audited across 11 open-source guardrail tools (LLM Guard, Rebuff, NeMo Guardrails, Guardrails AI, llm-guard-py, Presidio, GitLeaks, OWASP-LLM, WAF-generic, LangKit, BodAIGuard); 100% aperiodic.
- End-to-end against ProtectAI's `BanSubstrings`: regex-only 0% detection on encoded payloads across 7 encoding types; full stack (preprocess + parallel neural) 95–100%.
- Three case studies: aspirin synthesis, TCP state machine, Zerbik calculus (synthetic).
- N=50 ToT benchmark, seeds 0–49: BFS 0.466, random-beam 0.172, ToT 0.122. **BFS dominates.** An earlier N=20 run reported the opposite ordering and was retracted in §8.2.
- Four formally distinct barriers: algebraic (unconditional), information-theoretic (illustrative under uniformity), computational (NP-hard via 3-SAT), structural (functoriality + opacity).
- Five attack vectors: V1 decomposition, V2 zero-knowledge pipeline, V3 homomorphic reasoning, V4 encoding bootstrap, V5 modular counting bypass.
- Artifacts: `monoid-extractor` (~860 LOC Python), `secrets-router` (MIT-licensed MCP server, ~800 LOC), 376-line PoC.
- Filter composition laws (Prop 10.1): five formally proven results about how AC⁰ + TC⁰ filters compose, including the critical blend weight α* = 1 − τ/c.

### 2.2 Common drafting errors to watch for

- Conflating V3 (an attack vector) with a search strategy in the empirical results.
- Citing the retracted N=20 ordering instead of the N=50 results.
- Overstating algebraic blindness as universal rather than restricted to modular-counting encodings.
- Treating all four barriers as symmetric impossibility theorems when only the algebraic one is unconditional.
- Inflating the corpus or domain-coverage counts beyond what the paper supports.
- Claiming machine-checked or formally verified proofs where the paper has only classical pen-and-paper proofs.
- Treating `secrets-router` as a general defense for all classes of attack rather than for the credential-exfiltration subclass it actually addresses.

## 3. Pre-submission process checklist

Order matters. Each step gates the next.

1. **Bibliography audit.** Verify every entry in `references.bib` resolves to a real paper. Flag any entries with placeholder authorship or unverified arXiv IDs; replace or remove before any external pitch.
2. **Responsible disclosure.** Notify ProtectAI of the LLM Guard `BanSubstrings` 0% detection result. Standard 30–90 day window before public claim. Pin the tested version in any external statement.
3. **arXiv endorsement.** Identify a cs.CR or cs.FL endorser. Submit. Wait for clearance before any external link to "arXiv version."
4. **README reconciliation.** README's empirical numbers must match `paper/main.tex` §8.2 (BFS / random-beam / ToT yields). The README's "ToT 4.3× BFS" comparison line is stale and must be replaced with the N=50 numbers. Also fix the abstract sentence that conflates V3 with a search strategy.
5. **Author bio audit.** Identify concrete signals for the author bio: open-source artifacts adopted in production, prior publications in adjacent areas, advisory roles, ACM membership, conference talks. "Independent researcher" alone is structurally weak in venue-pitch contexts.
6. **Competitive landscape refresh.** Position against the current industry/regulatory landscape — NIST AI RMF, EU AI Act (2026 enforcement), OWASP LLM Top 10 2025, Anthropic Constitutional AI, OpenAI instruction hierarchy, Microsoft PyRIT, MITRE ATLAS, ISO/IEC 42001 — not just academic preprints.
7. **Repository hygiene.** Pre-publication review of the public repo: any LLM-workflow-internal artifacts that read as tells (workflow handoff notes, skill definitions, completion reports) should be moved out of the repo root or framed clearly in a top-level methodology document.

## 4. Venue analysis

| Venue | Fit | Effort | Time-to-decision | Access barrier |
|---|---|---|---|---|
| **CACM Practice** | Good | Medium | 6–12 mo | Editor-curated; pre-pitch path |
| **USENIX Security** | Strong | Medium | 4–6 mo | Blind submit |
| **IEEE S&P** | Strong | Medium | 4–6 mo | Blind submit |
| **NDSS** | Good | Medium | 3–5 mo | Blind submit |
| **ACL LLMSec workshop** | Good (compressed) | Low | 1–2 mo | Workshop submission |
| **ISR (GenAI Special Issue)** | Conditional | High | 6–9 mo | Tight Sept 7, 2026 deadline |
| **CAIS** | Conditional | Medium | 4–6 mo | Audience requires guardrails-101 layer |

### 4.1 Operational notes per venue

**CACM Practice.** Pre-pitch to the Practice Section Chair before drafting. Articles run roughly 3,000–6,000 words with formal results in sidebars. Tonal preference: opinion/narrative essays, not theorem-led research papers. The published Schneier piece "LLMs' Data-Control Path Insecurity" is a closer tonal model than the manuscript as currently written. Publication cycle 6–12 months from green-light. Practice section is curated — solo, unaffiliated cold pitches are uphill.

**USENIX Security / IEEE S&P.** Most natural technical home. Existing material maps cleanly with minor reformatting; theorem density is welcomed. No editor-relationship dependency. Strong responsible-disclosure expectations — vendor notification is a hard prerequisite. Artifact track applicable to `monoid-extractor` and `secrets-router`. Likely the highest-probability primary on technical merit alone.

**NDSS.** Systems-leaning relative to USENIX/S&P. `secrets-router` becomes a stronger system contribution. Smaller venue; faster decision.

**ACL LLMSec workshop.** Compressed 4–8 page version; algebra to appendix; lead with attack characterization and measurement. Lower prestige but a fast publication path that can run in parallel with a longer venue submission.

**ISR GenAI Special Issue.** Submission window closes Sept 7, 2026. The manuscript as-is does not have an IS-theory contribution or an organizational/empirical evaluation; both are reviewer expectations. Adapting for this venue requires either (a) a field study (pilot deployment of the execution-layer defense in a partner organization), (b) an analytical model (cost/benefit of inference-layer vs. execution-layer controls under varying threat models), or (c) a survey study of enterprise guardrail-deployment practice. Without one of those, submission is high-risk. Realistic only with a co-author who brings IS-discipline framing and access to evaluation data.

**CAIS.** Lower bar than ISR but the audience does not have working knowledge of LLM guardrails as a deployment category. Reviewers would need a guardrails-101 layer before they could evaluate the algebraic content. The work is closer in shape to a CS/security paper than to an IS contribution.

### 4.2 Path comparison

- **Path A (technical-primary)**: USENIX or S&P primary; CACM Practice as follow-up after acceptance. No co-author dependency. Highest probability of landing on technical merit. Recommended baseline.
- **Path B (cross-disciplinary)**: CACM Practice primary; USENIX as fallback if CACM declines or stalls. Higher cross-disciplinary reach. Higher access barrier; longer cycle.
- **Path C (parallel)**: ACL LLMSec workshop in parallel with longer venue submission. Fast publication while the primary submission is in flight.

The risk in Path B is committing 3+ months to a curated venue with no editorial relationship, then needing to recraft for technical venues if it stalls. The risk in Path A is missing cross-CS reach until a follow-up. Path C de-risks both by establishing a publication beachhead quickly.

## 5. Pitch template (CACM Practice as illustrative)

For CACM Practice specifically, the pre-pitch is a ~1-page proposal to the Practice Section Chair, not a finished draft. Template below.

```
To: Practice Section Chair, Communications of the ACM
Re: Article proposal — [working title]

I'd like to propose an article for the Practice section on the structural limits
of LLM guardrails: an algebraic characterization of why pattern-matching guardrails
(LLM Guard, NeMo Guardrails, Guardrails AI, and similar production tools) have
a provable blind spot for a class of encoded payloads, and a deployable
architectural alternative.

The argument: substring-matching regex guardrails compile to finite automata
whose syntactic monoids are aperiodic. By Schützenberger–McNaughton–Papert
(1965/1971), Barrington–Compton–Straubing–Thérien (1992), and Furst–Saxe–Sipser
(1981) / Håstad (1987), aperiodic monoids characterize exactly AC⁰, which
cannot compute MOD_p predicates. An attacker who interleaves a payload with
arbitrary filler characters at every other position therefore evades any such
guardrail, and no filter modification within the aperiodic-regex paradigm can
patch this for the encoded class.

The evidence: extracted syntactic monoids from 142 patterns across 11 production
guardrail tools; 100% aperiodic. End-to-end testing against ProtectAI's LLM Guard
BanSubstrings scanner shows 0% detection on encoded payloads across seven
encoding classes; a parallel-composed neural filter plus preprocessing recovers
detection to 95–100%. (Vendor notified; standard responsible-disclosure window
observed.)

What practitioners get: (1) a precise statement of what a current guardrail
deployment can and cannot see, (2) an open-source audit tool that runs as a
CI/CD pre-deploy check, (3) a deployable execution-layer defense pattern that
closes the credential-exfiltration subclass of bypasses inference-layer filters
cannot.

Why now: [insert two current-quarter named incidents that map to the threat
model.] OWASP's 2025 Top 10 names the symptom (LLM01: Prompt Injection); this
article supplies the algebraic explanation for one structural failure mode and
an architectural fix.

Length: ~5,000 words with formal results in sidebars. Working code and a
24-page technical companion paper available now: [arXiv link, after endorsement].

About me: [bio — concrete credibility signals plus affiliation if available.]

If this fits the section's editorial direction, I'd welcome the chance to
develop a full draft.
```

For USENIX Security / IEEE S&P, the pitch is replaced by direct submission to the open call. The same content reorganizes around the venue's standard structure (intro / threat model / theory / measurement / system / evaluation / discussion).

## 6. Anchor incidents (for narrative framing)

Verify dates and details against primary sources before citing externally.

| Incident | Year | Risk class | Maps to paper claim |
|---|---|---|---|
| Air Canada chatbot liability (Moffatt v. Air Canada, BC CRT) | 2024 | Legal liability for AI-generated statement | NP-hardness of instantiation verification (Prop 6.11) |
| Samsung ChatGPT IP-leak company-wide ban | 2023 | Trade secret / data exfiltration | V2 zero-knowledge pipeline; secrets-router-class fix |
| Chevrolet of Watsonville $1 chatbot | 2023 | Reputational, contractual exposure | Class C semantic attack (Obs 6.16) |
| NYC MyCity chatbot recommending illegal practices | 2024 | Public-sector liability | Information destruction (Prop 6.9) + NP-hard verification |
| Indirect-prompt-injection class against productivity-suite copilots | 2024–25 | Cross-tenant data exfiltration | Greshake et al. + V2; execution-layer monitoring is the fix |

For 2026 publication windows, refresh with current-quarter incidents in addition to the foundational set.

## 7. Open decisions

1. **Primary venue.** CACM Practice (cross-CS reach, editor-curated) vs. USENIX Security / IEEE S&P (faster, blind, technical fit). Default recommendation: USENIX/S&P as primary on operational grounds; CACM as follow-up.
2. **Co-authorship and affiliation.** Solo independent submission vs. seeking a co-author with venue-specific standing. Affects bio strength, endorsement path, and venue access.
3. **ProtectAI disclosure window.** 30 days (minimum standard) vs. 90 days (cooperative). Affects submission timing.
4. **arXiv timing.** Post-endorsement upload before vs. after first venue submission. Some venues prefer pre-submission posting; others restrict it.
5. **ISR fallback.** Invest the additional 3–4 months of organizational/empirical work for the GenAI special issue, or pass for now and revisit after primary venue placement.
6. **Bibliography audit timeline.** Block all external pitches on completion vs. proceed with non-pitch internal materials in parallel.

---

*Working notes; not for external distribution. Update as decisions resolve.*
