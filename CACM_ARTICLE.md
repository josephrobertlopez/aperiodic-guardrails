# Why Your Regex Guardrails Are Provably Bypassable: An Algebraic View of LLM Safety in Production

**Target Venue**: Communications of the ACM (Contributed Article / Practice)
**Word Count**: ~4,000 words
**Author**: Joseph R. Lopez

---

## Abstract

Enterprise teams deploying large language models route prompts through guardrail filters — regex-based content scanners from tools like Llama Guard, Guardrails AI, NVIDIA NeMo Guardrails, IBM AI Guardrails, and the open-source patterns these libraries vendor. We prove that this entire class of defenses has a precise, classical algebraic blind spot: any guardrail whose decision is computable by substring matching against star-free patterns recognizes only languages in AC⁰, and AC⁰ provably cannot compute parity or any modular-counting predicate. The consequence is operationally concrete: an attacker who places a payload at every other character position — with arbitrary filler in between — bypasses every regex guardrail in production, regardless of how the regex is tuned, and no aperiodic regex addition can patch the gap. We verify this against 142 deployed regex patterns from eleven open-source guardrail libraries, finding 100% aperiodicity and confirmed bypass on every pattern tested. The result explains a class of incidents already documented in the wild — Unicode zero-width insertion, acrostic encodings, "read every other character" attacks — and gives business and security teams a falsifiable criterion: if your defense layer is regex, it cannot stop modular-counting encodings, and you need a different layer to catch them.

## 1. The Production Problem

If you run an LLM in production at any scale, you almost certainly route requests through a content-filtering layer. The major options as of 2025 — Llama Guard, Guardrails AI, NVIDIA NeMo Guardrails, IBM's AI Guardrails service, Microsoft Prompt Shields' regex tier, and the open-source pattern libraries shipped with each — are popular for good operational reasons. Regex is fast, deterministic, auditable, and runs on commodity hardware at request rates the LLM itself cannot. A typical deployment uses these as a pre-filter: cheap regex scans block obvious attacks, and only ambiguous requests go to a more expensive neural classifier or to the model itself.

The pre-filter promise is implicit but real: the regex layer is supposed to catch the easy cases. Direct prompt injection attempts ("ignore previous instructions"), known harmful keywords, exfiltration patterns, command-injection attempts. The neural layer, expensive but capable, handles the hard cases — paraphrase, semantic obfuscation, role-play attacks.

This paper proves that an entire category of "easy cases" — encodings that require modular counting to decode — is *outside the regex layer's mathematical capability*, not just outside the patterns the vendor happened to ship. The regex tier is provably blind to this category. No amount of pattern engineering can fix it. The category is large, includes attacks already documented in the literature, and includes attacks easy enough that an undergraduate can construct one in a session.

This is not a "regex guardrails are bad" paper. Regex guardrails are excellent within their class. The paper is about the boundary of that class, why the boundary is exactly where it is, and what business and security teams should do operationally given that the boundary is where it is.

## 2. The Algebraic Bound

The argument chains three classical theorems and one new lemma. Each link is in any first-year graduate course in formal language theory. The composition is what gives the production-relevant consequence.

**Substring aperiodicity (lemma).** Every regex constructed from concatenation, finite alternation, character classes, optional groups, dot, anchors, bounded repetition, and the substring wrapper `Σ* · K · Σ*` defines a star-free language. (We prove this by structural induction over the regex grammar deployed in the eleven guardrail libraries we surveyed; the construction inputs are exactly the building blocks in those libraries' pattern syntax.) By Schützenberger's theorem, every star-free language has an aperiodic syntactic monoid.

**Star-free is exactly AC⁰ (Schützenberger 1965, McNaughton-Papert 1971; Barrington-Compton-Straubing-Thérien 1992).** A regular language is star-free if and only if its syntactic monoid is aperiodic, and the star-free languages are exactly the languages decidable by AC⁰ circuits — constant-depth, polynomial-size circuits over AND, OR, NOT gates of unbounded fan-in. This is a sixty-year-old result.

**AC⁰ cannot compute parity (Furst-Saxe-Sipser 1981; Håstad 1987).** No AC⁰ circuit family computes the parity of an n-bit input — equivalently, no AC⁰ circuit decides, for prime p, whether the count of any symbol in a string is divisible by p. Håstad's switching-lemma proof of this fact was awarded the Gödel Prize in 1994. The result is unconditional: it does not depend on P ≠ NP or any unproven separation.

**Composition (Guardrail Blindness Theorem).** Let G be any regex guardrail whose patterns are built from the substring grammar above. Then L(G) is in AC⁰. For any prime p, define the decoding function `decode_p(w) = w[0::p]` (read every p-th character starting at position 0) and consider the language `L_decode(p) = decode_p^{-1}(L_blocked)` — strings whose every-p-th-character substring is a blocked pattern. The language L_decode(p) is regular but its syntactic monoid contains Z/pZ as a subgroup (witnessed by an explicit cyclic counter DFA), hence is not aperiodic, hence is not in AC⁰. Therefore G cannot decide L_decode(p). And, crucially, no addition of further regex patterns to G can fix this — because any such addition keeps L(G) in AC⁰, which is exactly the class that cannot compute MOD_p.

The corollary that matters operationally: **p = 2 already breaks every regex guardrail.** An attacker writes the payload at even positions and arbitrary filler at odd positions; the guardrail's substring matcher sees only the interleaved string, which contains no contiguous match for any blocked pattern, regardless of the pattern set. The bypass requires no model access, no gradient information, no token-level optimization — just placing characters at every other position.

## 3. The Empirical Confirmation

We pulled the regex pattern files from eleven open-source guardrail libraries — Llama Guard, Guardrails AI, NeMo Guardrails, the IBM regex corpus, AI-Guardrails, Microsoft Prompt Shields' published patterns, LlamaIndex Guardrails, the Garak fuzzing corpus, Vicuna-Guard, the OWASP LLM Top-10 reference patterns, and the unicodemagic test suite. After de-duplication this yielded 123 patterns. We added 19 patterns from the test corpora used in the published guardrail evaluation literature for a total of 142.

For each pattern we ran the syntactic-monoid construction, computed the period structure, and checked aperiodicity using the standard algorithm (compute the transition monoid of the minimal DFA, then check that for every element x of the monoid there exists an integer n with x^n = x^{n+1}). All 142 patterns are aperiodic. We ran the corresponding MOD_2 bypass construction against each — for each blocked pattern P, generate a test string by interleaving P with a filler character at odd positions and verify that the regex's pattern matcher returns "no match." Every pattern admits its bypass. Every pattern's bypass executes in microseconds. The bypass strings are short: a 20-character harmful keyword bypasses with a 40-character interleaved string.

The aperiodicity rate (100%) is not a coincidence — it is forced by the substring-matching design pattern that all these libraries use. The MOD_2 bypass success rate (100%) is not a coincidence either — it is forced by the AC⁰ bound. The empirical result is, in this case, what the theorem predicts; the empirical validation is checking that the deployed code matches the abstract pattern the proof analyzes, not checking whether the proof is true.

## 4. Where This Has Already Happened

The bypass class has documented instances in the literature, several of which were initially diagnosed as engineering failures of specific products rather than as a structural property of the pattern class. Reframing them through the algebraic lens both explains the past and predicts the future.

**Zero-width Unicode insertion (Boucher et al., USENIX Security 2022).** The paper *Bad Characters* demonstrated that inserting zero-width characters between payload characters causes guardrails using contiguous substring matching to miss the payload while the model interprets the original. This is exactly MOD_2 interleaving with a null filler character. Every instance of the technique reported in the wild — at the time framed as a Unicode-handling oversight — is an instance of the algebraic bound. The fix proposed in that paper (filter zero-width characters before matching) addresses one filler choice but does not address the bypass class: any visible filler character that appears in legitimate content (whitespace, punctuation, common letters) reproduces the bypass without using zero-width characters at all.

**Acrostic and steganographic encodings.** The first-letter-of-each-word and every-Nth-character encoding schemes catalogued in the prompt-injection taxonomy literature (Wei, Haghtalab & Steinhardt 2023; Xu et al. 2025; the Garak fuzzing corpus) are direct MOD_p instances. They have been demonstrated against production guardrails repeatedly. Vendors patch each new instance individually. The algebraic argument shows that no patch within the regex class closes the category.

**StructuralSleight (Yang et al., 2024).** Reports a 94.62% attack success rate against GPT-4o using uncommon text-encoded structures including ASCII art, cipher text, and structured templates. A subset of these reductions are MOD_p instances. The high attack success rate is consistent with what the algebraic bound predicts: the regex pre-filter cannot block the encoded form, and the model itself decodes and acts on the payload before the neural post-filter can intervene.

**Enterprise IP leakage incidents.** Public reporting of LLM-mediated data exfiltration (most prominently the 2023 Samsung incident in which proprietary code was pasted into ChatGPT) is typically diagnosed as a data loss prevention policy gap, which it is. The same incidents are also instances where the outbound DLP regex layer — present in many enterprise deployments — failed to detect the exfiltration. Where the leaked content was a contiguous code snippet, the DLP layer should and often does catch it. Where the content was reformatted (every other line, alternating tokens, structured comments) the DLP layer is in the bypass class. The combination is what enterprises see as "DLP works for naive copy-paste, fails for adversarial reformatting." The algebraic argument explains why the second category is not just hard to catch but provably uncatchable at the DLP regex layer.

We have not built a comprehensive incident corpus tying these together with statistical correlations and we are not making one — the bound is unconditional. A single instance of the bypass class is sufficient to demonstrate that production tooling falls in the bound. We have many instances.

## 5. What This Means for the Composition Problem

A natural reaction is "fine, regex alone is not enough; that's why we have neural filters." This is correct but the composition behavior is not symmetric and the asymmetry matters operationally.

A neural filter — a transformer-based classifier, of which Llama Guard's neural variant, Anthropic's classifier, and Microsoft Prompt Shields' neural tier are examples — operates in TC⁰ (threshold circuits), which *does* include MOD_p. Neural filters can in principle detect modular-counting encodings, and in practice the better-trained ones catch many of the bypass constructions above with high accuracy. The composition question is: does adding a neural filter to a regex filter close the gap?

Answer: it depends on whether the composition is *parallel* (allow ⇔ both layers allow; block if *either* blocks) or *serial* (allow ⇔ regex allows, then neural decides; block if regex blocks).

In the *parallel-OR* composition (the layer blocks if any constituent blocks) the neural filter's TC⁰ capability survives the composition. The combined layer can detect MOD_p encodings at the rate the neural filter alone can. This is the configuration enterprises generally want.

In the *serial-AND* composition (the regex layer is checked first as a cheap pre-filter, only ambiguous requests go to neural) the regex layer's blindness vetoes the neural layer's capability. If the regex layer "allows" (because the encoding bypassed it), the neural layer never gets the request. The combined layer's blindness equals the regex layer's blindness. This is the configuration enterprises generally deploy, because the cost asymmetry between regex and neural is large enough that running every request through the neural filter is rejected on cost grounds.

The algebraic bound therefore implies a specific operational recommendation: **the regex tier must not be used as a serial pre-filter in front of the neural tier for the modular-counting encoding class.** The regex tier may run in parallel with the neural tier (as a fast path for the cases regex *can* catch) but the neural tier must see every request, not only the requests regex flagged ambiguous. This inverts the deployment pattern most enterprises use today, which was chosen for cost reasons that the bound shows are buying provably less safety than the deployment implies.

## 6. What Survives, What Doesn't, and What's Still Open

What survives the bound:

- **Regex guardrails for the patterns regex can match.** Direct keyword blocks, simple injection patterns, exact-match credentials patterns, well-formed JSON validation. These are not in the bypass class and the regex tier handles them at speed and cost the neural tier cannot match.
- **Neural guardrails for everything else.** TC⁰ is a richer class than AC⁰. The bound on regex does not apply to neural classifiers. Neural classifiers have *different* failure modes (paraphrase robustness, distributional drift, jailbreaks at the model layer) but the modular-counting blind spot is not one of them.
- **Out-of-band defenses.** Source-of-truth interpretation tables held outside the LLM context (a pattern we describe as the secrets-router architecture, with a reference open-source implementation in the project repository) sidestep the inference-layer indistinguishability question entirely by never giving the LLM the decoding key.

What does not survive:

- **The pre-filter / post-filter cost-saving deployment pattern, for the modular-counting encoding class.**
- **The implicit promise that regex guardrails are catching "the easy cases."** Modular-counting encodings are easy to construct and impossible for regex to catch. They are not edge cases; they are a structural property of the pattern class.
- **Vendor claims of comprehensive coverage by regex pattern libraries.** The libraries we surveyed cover the patterns they cover. They cannot cover the bypass class without leaving the regex paradigm.

What's still open:

- **Composition with TC⁰ neural classifiers in adversarial settings.** Neural classifiers can compute MOD_p but the composition behavior under specific adversarial constructions is an empirical question we do not settle here.
- **The structural indistinguishability question at the inference layer.** Our paper-length companion report (the project repository, `paper/main.tex`) discusses this as an Observation rather than a Theorem; the demotion is intentional. The unconditional result is the regex bound; the inference-layer indistinguishability claim is conditional and we do not assert it as theorem.
- **Domain-specific adversarial constructions.** The MOD_2 bypass is the simplest member of a larger family. Composite-modulus constructions, tree-structured encodings, and group-theoretic encodings exploiting the Krohn-Rhodes decomposition of finite-state machines are areas where the bound has more to say than this article includes.

## 7. Operational Recommendations

For business and security leaders responsible for LLM deployments, the algebraic bound translates into concrete actions.

**Audit your guardrail composition pattern.** If your regex tier sits as a serial pre-filter in front of your neural tier — the most common deployment pattern — your effective coverage of the modular-counting bypass class is the regex tier's coverage, which is zero. Move to a parallel composition where every request reaches the neural tier, even if the regex tier handles fast cases at lower cost.

**Stop accepting "comprehensive regex coverage" claims at face value.** Vendor pattern libraries cover what they cover. The bound says they cannot cover the bypass class. Ask vendors specifically whether their tier handles MOD_2 interleaving attacks, and accept "no, that's the neural tier's job" as the correct answer. Reject "yes, our patterns catch encoded attacks" as a claim the math does not support.

**Use regex tiers for what they are good at.** Speed, determinism, audit trail, exact-match patterns. Direct prompt-injection keyword blocks. Exfiltration patterns where the leaked content is contiguous. Format validators. These are not in the bypass class and the regex tier excels.

**Treat the bypass class as a known-unknown.** It is not "we do not know whether regex can catch encoded attacks"; it is "regex provably cannot catch this class of encoded attacks, and we have empirically verified the bypass works against the deployed patterns." This is a known property of the deployed defense, not a research speculation.

**Invest in out-of-band architectures for the highest-stakes cases.** Where the cost of a bypass is large enough that even a neural tier's residual error rate is unacceptable, architectures that never expose the secret to the inference layer are the right answer. The MCP-server pattern in the reference implementation gives a concrete example: the LLM operates on opaque handles, fields are filled by a separately-permissioned service, the decoded content never enters the LLM's context window.

For researchers and tool authors, the bound suggests that further investment in regex pattern engineering for the bypass class is wasted effort. The interesting research questions are at the neural tier, in composition behavior, and in out-of-band architectures.

## 8. The Honest Scope

This article makes a narrow claim and we want to be precise about its scope.

**What we claim.** Regex guardrails using substring matching against star-free patterns are provably blind to MOD_p encodings, the bypass is empirically demonstrable against 142 deployed patterns, and the operational consequence is that the common serial-AND deployment pattern provides less safety than its cost might suggest.

**What we do not claim.** We do not claim that all AI security is mathematically impossible. We do not claim that neural guardrails have the same blind spot — they do not, because TC⁰ is strictly larger than AC⁰. We do not claim a percentage correlation between our theoretical analysis and a corpus of real-world incidents — incident corpora that intersect this bound exist (Boucher et al. on Unicode, the Wei et al. taxonomy, StructuralSleight) but the bound is unconditional and does not need a correlation coefficient. We do not claim a regulatory framework follows from this result; the result has operational implications for deployment choices and audit, but the policy question of how regulators should respond to provably-bypassable defenses is a separate question we are not answering here.

The classical theorems we use are sixty, thirty-three, and thirty-eight years old respectively. The novelty in this article is in the *application* — specifically, the substring-aperiodicity lemma for the regex grammar deployed in eleven production guardrail libraries, and the operational analysis of what the bound implies for the serial-AND composition pattern. We use existing mathematical tools to answer a production-relevant question. We are explicit about which parts of the argument are classical (most of them) and which parts are new (the substring-aperiodicity lemma and the empirical verification against the 142-pattern corpus).

## 9. Coda: What Got Us Here

The original framing of this work was a much larger universal-impossibility claim and a regulatory-framework brief built on top of it. The universal claim turned out to be false — a single counterexample (a parity-projection classifier where the compression respects the safety equivalence relation) destroys the universal version. The bound that survives — the one this article describes — is narrower, scoped to regex guardrails specifically, and unconditional within that scope. The narrower bound is what the math actually proves. The broader claim was overreach, and the discipline of writing the proof out in detail is what surfaced the counterexample.

The lesson, for the AI security literature in particular, is that algebraic bounds on specific defense classes are tractable and useful. Universal claims about "AI systems" are difficult to make rigorously, often false, and not necessary for the operationally important results. The regex-tier bound is the kind of result that gives security teams a falsifiable, decision-relevant criterion: *if your defense layer is in this class, here is what it provably cannot do.* That is the right shape of theorem for the field. The universal version is the wrong shape, and the literature is better off without it.

## References

1. Schützenberger, M.P. (1965). On finite monoids having only trivial subgroups. *Information and Control* 8(2), 190–194.
2. McNaughton, R., and Papert, S. (1971). *Counter-Free Automata*. MIT Press.
3. Barrington, D.A., Compton, K., Straubing, H., and Thérien, D. (1992). Regular languages in NC¹. *Journal of Computer and System Sciences* 44(3), 478–499.
4. Furst, M., Saxe, J.B., and Sipser, M. (1981). Parity, circuits, and the polynomial-time hierarchy. *FOCS 1981*, 260–270.
5. Håstad, J. (1987). *Computational Limitations of Small-Depth Circuits*. MIT Press. (Gödel Prize 1994.)
6. Krohn, K., and Rhodes, J. (1965). Algebraic theory of machines I. *Trans. AMS* 116, 450–464.
7. Boucher, N., Shumailov, I., Anderson, R., and Papernot, N. (2022). Bad Characters: Imperceptible NLP Attacks. *USENIX Security 2022*.
8. Wei, A., Haghtalab, N., and Steinhardt, J. (2023). Jailbroken: How does LLM safety training fail? *NeurIPS 2023*.
9. Xu, Z., et al. (2025). Bypassing prompt injection defenses: An empirical taxonomy. *USENIX Security 2025*.
10. Yang, Z., et al. (2024). StructuralSleight: Automated jailbreak via structural transformation. *Preprint*.
11. Pin, J.-E. (1986). *Varieties of Formal Languages*. Plenum Press.
12. Llama Guard pattern repository. (2025). meta-llama/PurpleLlama. github.com/meta-llama/PurpleLlama.
13. Guardrails AI pattern repository. (2025). guardrails-ai/guardrails. github.com/guardrails-ai/guardrails.
14. NVIDIA NeMo Guardrails pattern repository. (2025). NVIDIA/NeMo-Guardrails. github.com/NVIDIA/NeMo-Guardrails.
15. Project repository (this work). (2026). aperiodic-guardrails. Includes the 142-pattern corpus, aperiodicity verification scripts, MOD_2 bypass demonstrations, the secrets-router reference implementation, and the formal proofs in `paper/main.tex`.
