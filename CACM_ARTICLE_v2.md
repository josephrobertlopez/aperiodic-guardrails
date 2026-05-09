# Why Your Regex Guardrails Are Provably Bypassable: An Algebraic View of LLM Safety in Production

**Target Venue**: Communications of the ACM (Practice)
**Word Count**: ~3,900 words
**Author**: Joseph R. Lopez

---

## Abstract

Enterprise teams deploying large language models route prompts through guardrail filters — regex-based content scanners shipped by tools such as LLM-Guard, Guardrails-AI, NeMo-Guardrails, Rebuff, Presidio, and similar libraries. We prove that this entire class of defenses has a precise, classical algebraic blind spot: any guardrail whose decision is computable by substring matching against star-free patterns recognizes only languages in AC⁰, and AC⁰ provably cannot compute parity or any modular-counting predicate. The consequence is operationally concrete: an attacker who places a payload at every other character position — with arbitrary filler in between — bypasses every regex guardrail in this class, regardless of how the regex is tuned, and no further aperiodic regex addition can patch the gap. We verify the algebraic property against 142 regex patterns drawn from eleven open-source guardrail tools (123 patterns) plus 19 author-generated test patterns, finding 100% aperiodicity and confirmed MOD_2 bypass constructions across the corpus. The result explains a class of incidents already documented in the wild — Unicode zero-width insertion, even-position acrostics, "read every other character" attacks — and gives security teams a falsifiable criterion: if your defense layer is regex with the substring-matching design pattern, it cannot stop modular-counting encodings, and a different layer must catch them.

## 1. The Production Problem

If you run an LLM in production at any scale, you almost certainly route requests through a content-filtering layer. Open-source options popular as of 2025 include LLM-Guard, Guardrails-AI, NeMo-Guardrails, Rebuff, Presidio, GitLeaks, OWASP-LLM pattern collections, LangKit, and several enterprise-internal regex stacks. These are popular for good operational reasons. Regex is fast, deterministic, auditable, and runs on commodity hardware at request rates the LLM itself cannot. A typical deployment uses these as a pre-filter: cheap regex scans block obvious attacks, and only ambiguous requests go to a more expensive neural classifier or to the model itself.

The pre-filter promise is implicit but real: the regex layer is supposed to catch the easy cases — direct prompt injection attempts ("ignore previous instructions"), known harmful keywords, exfiltration patterns, command-injection attempts. The neural layer, expensive but capable, handles the hard cases — paraphrase, semantic obfuscation, role-play attacks.

This article proves that an entire category of "easy cases" — encodings that require modular counting to decode — is *outside the regex layer's mathematical capability*, not just outside the patterns the vendor happened to ship. The regex tier is provably blind to this category. No amount of pattern engineering can fix it within the regex paradigm. The category is large, includes attacks already documented in the literature, and includes attacks easy enough that an undergraduate can construct one in a session.

This is not a "regex guardrails are bad" article. Regex guardrails are excellent within their class. The article is about the boundary of that class, why the boundary is exactly where it is, and what teams should do operationally given that the boundary is where it is.

## 2. The Algebraic Bound

The argument chains three classical theorems and one new lemma. Each link is in any first-year graduate course in formal language theory. The composition is what gives the production-relevant consequence.

**Substring aperiodicity (lemma).** Every regex constructed from literals, character classes, alternation, optional groups, dot, bounded repetition, and Kleene star or plus *applied to character classes*, wrapped as `Σ* · L(r) · Σ*` (substring matching) defines a star-free language. (We prove this by structural induction over the regex grammar deployed in the eleven open-source guardrail libraries we surveyed; the construction inputs are the building blocks present in those libraries' pattern syntax.) By Schützenberger's theorem, every star-free language has an aperiodic syntactic monoid. Crucially, the result requires the Kleene-star/plus restriction to character classes — general `(r)*` for arbitrary regex `r` can yield non-aperiodic languages (`(ab)*` is the standard counterexample), and would not satisfy the lemma.

**Star-free is exactly AC⁰ (Schützenberger 1965, McNaughton-Papert 1971; Barrington-Compton-Straubing-Thérien 1992).** A regular language is star-free if and only if its syntactic monoid is aperiodic, and the star-free languages are exactly the languages decidable by AC⁰ circuits — constant-depth, polynomial-size circuits over AND, OR, NOT gates of unbounded fan-in.

**AC⁰ cannot compute parity (Furst-Saxe-Sipser 1981; Håstad 1987).** No AC⁰ circuit family computes the parity of an n-bit input — equivalently, no AC⁰ circuit decides, for prime p, whether the count of any symbol in a string is divisible by p. The result is unconditional: it does not depend on P ≠ NP or any unproven separation.

**Composition (Guardrail Blindness Theorem).** Let G be any regex guardrail whose patterns are built from the substring grammar above. Then L(G) is in AC⁰. For any prime p, define the decoding function `decode_p(w) = w[0::p]` (read every p-th character starting at position 0) and consider the language `L_decode(p) = { w : w[0::p] ∈ L_blocked }` — strings whose every-p-th-character substring is a blocked pattern. The language L_decode(p) is regular (witnessed by an explicit length-p cyclic counter DFA in product with the minimal DFA for L_blocked) but its syntactic monoid contains Z/pZ as a subgroup (witnessed by a filler character that cycles the counter without affecting the blocked component), hence is not aperiodic, hence is not in AC⁰. Therefore G cannot decide L_decode(p). Crucially, no addition of further regex patterns to G can fix this — because any such addition keeps L(G) in AC⁰, which is exactly the class that cannot compute MOD_p.

The corollary that matters operationally: **p = 2 already breaks every regex guardrail in this class.** An attacker writes the payload at even positions and arbitrary filler at odd positions; the guardrail's substring matcher sees only the interleaved string, which contains no contiguous match for any blocked pattern, regardless of the pattern set. The bypass requires no model access, no gradient information, no token-level optimization — just placing characters at every other position.

## 3. The Empirical Confirmation

We pulled regex pattern files from eleven open-source guardrail libraries: LLM-Guard, Rebuff, NeMo-Guardrails, Guardrails-AI, llm-guard-py, Presidio, GitLeaks, OWASP-LLM, LangKit, BodAIGuard, and a generic-WAF reference set commonly cited in deployed enterprise stacks. This yielded 123 patterns. We added 19 patterns from author-constructed test corpora (released alongside this work) for a total of 142.

For each pattern we ran the syntactic-monoid construction, computed the period structure, and checked aperiodicity using the standard algorithm: compile the regex to a Thompson NFA, convert to the minimal DFA via powerset construction with Hopcroft minimization, enumerate the transition monoid via BFS over the Cayley graph, then for each monoid element x test that x^n = x^{n+1} for some computable n ≤ |M|². All 142 patterns are aperiodic. We then ran the corresponding MOD_2 bypass construction against each: for each blocked pattern P, generate a test string by interleaving P with a filler character at odd positions and verify that the regex returns "no match." Every pattern admits its bypass. The corpus, the monoid extractor, and the bypass verification scripts are released with the project repository.

The aperiodicity rate (100%) is not a coincidence — it is forced by the substring-matching design pattern that all these libraries use. The MOD_2 bypass success rate is not a coincidence either — it is forced by the AC⁰ bound. The empirical result is, in this case, what the theorem predicts; the empirical work is checking that the deployed code matches the abstract pattern the proof analyzes, not checking whether the proof is true.

## 4. Where This Has Already Happened

The bypass class has documented instances in the literature, several of which were initially diagnosed as engineering failures of specific products rather than as a structural property of the pattern class. Reframing them through the algebraic lens both explains the past and predicts the future.

**Zero-width Unicode insertion (Boucher et al., IEEE S&P 2022, "Bad Characters").** The paper demonstrated that inserting zero-width characters between payload characters causes guardrails using contiguous substring matching to miss the payload while the model interprets the original. This is exactly MOD_2 interleaving with a null filler character. Every instance of the technique reported in the wild — at the time framed as a Unicode-handling oversight — is an instance of the algebraic bound. The fix proposed in that paper (filter zero-width characters before matching) addresses one filler choice but does not address the bypass class: any visible filler character that appears in legitimate content (whitespace, punctuation, common letters) reproduces the bypass without using zero-width characters at all.

**Even-position acrostic and steganographic encodings.** The first-letter-of-each-word and every-N-th-character encoding schemes catalogued in the prompt-injection bypass literature (Wei, Haghtalab & Steinhardt, NeurIPS 2023; Xu et al., ACL 2025 LLMSec workshop) are direct MOD_p instances. They have been demonstrated against production guardrails repeatedly. Vendors patch each new instance individually. The algebraic argument shows that no patch within the regex class closes the category.

**Uncommon Text-Encoded Structures (Yue et al., arXiv preprint 2406.08754, 2024, "UTES" / StructuralSleight).** The work reports a 94.62% attack success rate against GPT-4o using uncommon text-encoded structures including ASCII art, cipher text, and structured templates. A subset of these reductions are MOD_p instances. The high attack success rate is consistent with what the algebraic bound predicts when a regex pre-filter is in the path: the regex layer cannot block the encoded form, the model itself decodes and acts on the payload before the neural post-filter (when present) can intervene.

**Contiguous-paste data exfiltration.** Public reporting of LLM-mediated data exfiltration (most prominently the 2023 Samsung incident in which proprietary code was pasted into ChatGPT) is typically diagnosed as a data loss prevention (DLP) policy gap, which it is. The leaked content in the reported case was a contiguous code paste; that is a different DLP failure class than the one this article addresses, and we do not claim the algebraic bound explains it. The reason it appears here is that enterprises operating outbound DLP regex layers face the bound *additionally* for any future variant where outbound content is reformatted into a MOD_p encoding. We mention it as a forward-looking exposure for which the bound has implications, not as a retrospective diagnosis of the contiguous-paste case.

A single instance of the bypass class is sufficient to demonstrate that production tooling falls under the bound. We have many instances, several with peer-reviewed analyses, and the bound is unconditional.

## 5. What This Means for the Composition Problem

A natural reaction is "fine, regex alone is not enough; that's why we have neural filters." This is correct, but the composition behavior is not symmetric and the asymmetry matters operationally.

A neural filter — any transformer-based classifier — operates in TC⁰ (threshold circuits), as established by recent complexity-theoretic analyses of log-precision transformers (Merrill & Sabharwal 2023; Chiang, Cholak, & Pillay 2024). TC⁰ properly contains AC⁰ and *does* include MOD_p. Neural filters can in principle detect modular-counting encodings, and in practice the better-trained ones catch many of the bypass constructions above with high accuracy. The composition question is: does adding a neural filter to a regex filter close the gap?

Answer: it depends on whether the composition is *parallel* (allow ⇔ both layers allow; block if *either* blocks) or *serial* (allow ⇔ regex allows, then neural decides; block if regex blocks).

In the *parallel-OR* composition (the layer blocks if any constituent blocks), the neural filter's TC⁰ capability survives the composition. The combined layer can detect MOD_p encodings at the rate the neural filter alone can.

In the *serial-AND* composition (the regex layer is checked first as a cheap pre-filter, only ambiguous requests go to neural), the regex layer's blindness vetoes the neural layer's capability. If the regex layer "allows" (because the encoding bypassed it), the neural layer never gets the request. The combined layer's blindness equals the regex layer's blindness.

The algebraic bound therefore implies a specific operational recommendation: **wherever the regex tier sits as a serial pre-filter in front of a neural tier, the modular-counting encoding class bypasses both.** We do not claim a measured prevalence of either composition pattern in industry; we claim that the math distinguishes them sharply, and that any deployment using serial-AND for cost reasons should re-examine that choice with the bound in hand.

## 6. What Survives, What Doesn't, and What's Still Open

**What survives the bound.** Regex guardrails for the patterns regex can match — direct keyword blocks, simple injection patterns, exact-match credentials patterns, well-formed JSON validation. These are not in the bypass class and the regex tier handles them at speed and cost the neural tier cannot match. Neural guardrails for the modular-counting encoding class — TC⁰ is strictly larger than AC⁰, the bound on regex does not transfer. Out-of-band defenses that never expose secrets to the LLM context.

**What does not survive.** The serial-AND deployment pattern, for the modular-counting encoding class. The implicit promise that regex guardrails are catching "the easy cases" — modular-counting encodings are easy to construct and impossible for regex to catch within the substring-matching pattern. Vendor claims of comprehensive coverage by regex pattern libraries against encoded payloads.

**What's still open.** The composition behavior under specific adversarial constructions when both regex and neural classifiers are present in parallel. The structural indistinguishability question at the inference layer when the LLM itself is the decoder; the project's companion technical paper treats this as an Observation rather than a Theorem and we maintain that framing here. Composite-modulus constructions, tree-structured encodings, and group-theoretic encodings exploiting the Krohn-Rhodes decomposition of finite-state machines are areas where the bound has more to say than this article includes.

## 7. Operational Recommendations

For business and security leaders responsible for LLM deployments, the algebraic bound translates into concrete actions.

**Audit the composition pattern.** If the regex tier sits as a serial pre-filter in front of a neural tier, the effective coverage of the modular-counting bypass class is the regex tier's coverage, which is zero. A parallel composition where every request reaches the neural tier preserves the neural tier's MOD_p capability, even if the regex tier handles fast cases at lower cost.

**Treat regex coverage claims with the bound in mind.** Vendor pattern libraries cover what they cover. The bound says they cannot cover the modular-counting encoding class. "Yes, the neural tier handles encoded attacks" is the correct answer; "yes, our regex patterns catch encoded attacks" is a claim the math does not support for the substring-matching design pattern these libraries use.

**Use regex tiers for what they are good at.** Speed, determinism, audit trail, exact-match patterns. Direct prompt-injection keyword blocks. Exfiltration patterns where the leaked content is contiguous. Format validators. These are not in the bypass class and the regex tier excels.

**Treat the bypass class as a known-unknown.** It is not "we do not know whether regex can catch encoded attacks"; it is "regex provably cannot catch this class of encoded attacks within the substring-matching pattern, and the bypass has been empirically verified against the deployed patterns of eleven open-source libraries." This is a known property of the deployed defense.

**Invest in out-of-band architectures for the highest-stakes cases.** Where the cost of a bypass is large enough that even a neural tier's residual error rate is unacceptable, architectures that never expose the secret to the inference layer are the right answer. The project's reference implementation gives a concrete example: an MIT-licensed open-source MCP server (linked from the project repository) where the LLM operates on opaque handles, fields are filled by a separately-permissioned service, and the decoded content never enters the LLM's context window.

For researchers and tool authors, the bound suggests that further investment in regex pattern engineering for the bypass class is wasted effort. The interesting research questions are at the neural tier, in composition behavior, and in out-of-band architectures.

## 8. The Honest Scope

This article makes a narrow claim and we want to be precise about its scope.

**What we claim.** Regex guardrails using substring matching against star-free patterns are provably blind to MOD_p encodings, the bypass is empirically demonstrable against 142 patterns drawn from eleven open-source libraries plus author-generated test cases, and the operational consequence is that the serial-AND deployment pattern provides less safety than its cost might suggest.

**What we do not claim.** We do not claim that all AI security is mathematically impossible. We do not claim that neural guardrails have the same blind spot — they do not, because TC⁰ is strictly larger than AC⁰. We do not claim a percentage correlation between our theoretical analysis and a corpus of real-world incidents — incident corpora that intersect this bound exist (Boucher et al. on Unicode, Wei et al. and Xu et al. on encoding-based bypasses, the StructuralSleight/UTES results) but the bound is unconditional and does not need a correlation coefficient. We do not claim a regulatory framework follows from this result; the result has operational implications for deployment choices and audit, but the policy question of how regulators should respond to provably-bypassable defenses is a separate question we are not answering here.

The classical theorems we use are six decades old (Schützenberger), three decades old (Barrington-Compton-Straubing-Thérien; Furst-Saxe-Sipser; Håstad). The novelty in this article is in the *application* — specifically, the substring-aperiodicity lemma for the regex grammar present in eleven production open-source libraries, the empirical verification against the 142-pattern corpus, and the operational analysis of what the bound implies for the serial-AND composition pattern. We use existing mathematical tools to answer a production-relevant question. We are explicit about which parts of the argument are classical (most of them) and which parts are new (the substring-aperiodicity lemma in its scope, the corpus verification, and the operational composition analysis).

## 9. Coda

The original framing of this work was a much larger universal-impossibility claim covering all AI systems with compression capability, plus a regulatory-framework brief built on top of it. The universal claim turned out to be false — a single counterexample (a parity-projection classifier where the compression respects the safety equivalence relation) destroys the universal version. The bound that survives — the one this article describes — is narrower, scoped to regex guardrails using substring matching, and unconditional within that scope. The narrower bound is what the math actually proves. The broader claim was overreach, and the discipline of writing the proof out in detail is what surfaced the counterexample.

The lesson, for the AI security literature in particular, is that algebraic bounds on specific defense classes are tractable and useful. Universal claims about "AI systems" are difficult to make rigorously, often false, and not necessary for the operationally important results. The regex-tier bound is the kind of result that gives security teams a falsifiable, decision-relevant criterion: *if your defense layer is in this class, here is what it provably cannot do.* That is the right shape of theorem for the field. The universal version is the wrong shape, and the literature is better off without it.

## References

1. Schützenberger, M.-P. (1965). On finite monoids having only trivial subgroups. *Information and Control* 8(2), 190–194.
2. McNaughton, R., and Papert, S. (1971). *Counter-Free Automata*. MIT Press.
3. Barrington, D. A. M., Compton, K., Straubing, H., and Thérien, D. (1992). Regular languages in NC¹. *Journal of Computer and System Sciences* 44(3), 478–499.
4. Furst, M., Saxe, J. B., and Sipser, M. (1981). Parity, circuits, and the polynomial-time hierarchy. In *Proc. 22nd IEEE FOCS*, 260–270.
5. Håstad, J. (1987). *Computational Limitations of Small-Depth Circuits*. PhD thesis, MIT.
6. Krohn, K., and Rhodes, J. (1965). Algebraic theory of machines I: Prime decomposition theorem for finite semigroups and machines. *Trans. AMS* 116, 450–464.
7. Pin, J.-E. (1986). *Varieties of Formal Languages*. Plenum Press.
8. Boucher, N., Shumailov, I., Anderson, R., and Papernot, N. (2022). Bad Characters: Imperceptible NLP Attacks. In *Proc. IEEE Symposium on Security and Privacy*.
9. Wei, A., Haghtalab, N., and Steinhardt, J. (2023). Jailbroken: How does LLM safety training fail? In *Advances in Neural Information Processing Systems (NeurIPS)*.
10. Xu, Z., et al. (2025). Bypassing LLM guardrails: Empirical analysis of adversarial prompt strategies. In *Proc. ACL 2025 Workshop on Language Models and Security (LLMSec)*.
11. Yue, H., et al. (2024). UTES: Uncommon Text-Encoded Structures for Automated Jailbreaking. arXiv preprint 2406.08754.
12. Merrill, W., and Sabharwal, A. (2023). The Parallelism Tradeoff: Limitations of Log-Precision Transformers. *TACL* 11, 531–545.
13. Chiang, D., Cholak, P., and Pillay, A. (2024). Tighter bounds on the expressivity of transformer encoders. In *Proc. ICML*.
14. Hahn, M. (2020). Theoretical limitations of self-attention in neural sequence models. *TACL* 8, 156–171.
15. Project repository (this work, 2026). Includes the 142-pattern corpus (`corpus_full.csv`), aperiodicity verification scripts, MOD_2 bypass construction and verification, the formal proofs in `paper/main.tex`, the parity-projection counterexample (`counterexamples.md`), and the secrets-router reference implementation.
