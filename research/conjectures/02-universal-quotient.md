# ❌ CONJECTURE 2 FAILED: Universal Quotient Functor Attack

**STATUS**: FALSIFIED 2026-04-11 by mathematical validation pipeline

**One-line form**: Every inference-layer blindness attack on an LLM
guardrail is equivalent to exhibiting a non-invertible quotient functor
`Q: Concrete → Abstract` at the inspection boundary.

**FAILURE MODE**: Universal quantifier overreach + missing formal functor definition

## Statement

Let `𝒞` be the category of concrete-domain operations (real procedures
with safety-relevant semantics), `𝒜` the category of abstract symbolic
representations visible to the LLM, and `Q: 𝒞 → 𝒜` a functor such that
the guardrail's decision procedure factors through `Q`.

**Conjecture (universal quotient)**: For every attack construction
that succeeds in being inference-layer indistinguishable from a
legitimate prompt, there exists a choice of `Q` such that:

1. **Non-invertibility at the inference layer**: The inverse `Q⁻¹` is
   not available to the guardrail (the interpretation table is held
   offline by the attacker or resolved at the execution layer by a
   defender).
2. **Surjectivity onto the visible fiber**: For every abstract prompt
   `a ∈ 𝒜`, the preimage `Q⁻¹(a) ⊆ 𝒞` contains both safe and unsafe
   concrete artifacts (mixed fibers, per `def:fiber` in main.tex).
3. **Recoverability via offline interpretation**: There exists an
   offline function `I: 𝒜 → 𝒞` held by the attacker such that
   `I(a)` lies in the unsafe region of the fiber `Q⁻¹(a)`.

The conjecture then claims: the three properties above are jointly
necessary and sufficient for the attack to be inference-layer blind.

**What we thought we had (before falsification)**:

The conjecture originally claimed to subsume multiple attack classes:
- Algebraic blindness (syntactic monoid quotients)  
- Homomorphic reasoning (free-category functors)
- Information-theoretic abstraction (Fano bounds)
- Defense inversion patterns (secrets-router)

**Why this was wrong**: Universal quantification without proof + missing formal functor definitions.

## Motivation

This IS the R1 bridging lemma from the adversarial review, generalized
to its strongest form. The adversarial reviewer's recommendation was to
state and prove a bridging lemma over `Q` that unifies the algebraic
and homomorphic-reasoning halves of the current paper. This conjecture
pushes that one step further: it claims the quotient-functor framing is
not just a convenient abstraction that unifies two results — it's a
**universal characterization** of all inference-layer blindness attacks.

If true, the conjecture delivers:
- A single headline theorem instead of two halves
- An elegant dual structure for defense (flip who holds `I`)
- A predictive framework: for any proposed guardrail architecture,
  derive `Q` and check whether a useful attacker `I` exists
- A natural taxonomy: attacks classified by their `Q` structure

## Prior Art

- **Current paper §4.2** — the quotient-functor machinery already
  exists as the formalization of the abstraction layer. `Q` is
  implicitly there as the composition of the abstraction function with
  the free-category construction. No one has tried to state it as a
  universal claim.

- **Ball et al. (2025) computational indistinguishability** — proves a
  related result under cryptographic assumptions over a broader attack
  class. The universal quotient conjecture would subsume Ball et al.'s
  setting as the special case where `Q` is a pseudorandom permutation
  that the adversary can invert but the polynomial-time guardrail
  cannot.

- **Category-theoretic formulations of information flow security**
  (Abramsky, Barrett, and others) — there's a body of work framing
  information-flow properties as functorial conditions. None targets
  LLM guardrails specifically. This conjecture would be a novel
  application if it holds.

## Test Plan (Theoretical + Empirical)

**Phase 1 — State and attempt the forward direction (2–3 hours,
"R1 mirage check")**:
- Write out the conjecture formally using the §4.2 machinery
- Attempt to prove: given an attack that is inference-layer blind,
  exhibit the three `Q` properties
- **Checkpoint**: if this direction does not go through in 2–3 hours,
  the conjecture is probably a vocabulary mirage and should be
  abandoned. If it works, continue.

**Phase 2 — State and attempt the reverse direction (half a day)**:
- Given `Q` with the three properties, construct an attack that is
  inference-layer blind
- Cross-check against the algebraic and homomorphic specializations

**Phase 3 — Test the subsumption claims (1 day)**:
- For each of the four specializations (algebraic, homomorphic, Fano,
  secrets-router defense), verify explicitly that it fits the
  universal statement. If any specialization requires an extra
  assumption not covered by the universal form, the conjecture is too
  strong and needs to be narrowed.

**Phase 4 — Search for counterexamples (open-ended)**:
- Look in recent LLM-security literature for attacks that DON'T fit
  the quotient-functor pattern. Steganographic attacks, prompt
  injection via markup manipulation, gradient-based weight-space
  attacks. Which of these fit? Which don't? The non-fitting class
  marks the conjecture's boundary.

## Potential Publication Venue

- **IF the conjecture holds**: this is the headline theorem for the
  merged paper at **USENIX Security 2027 cycle 1 (Aug 25, 2026)** or
  **Oakland S&P 2027 cycle 2 (Nov 13, 2026)**. The paper becomes "a
  unified categorical framework for LLM guardrail impossibility," and
  the algebraic and homomorphic results become specializations.

- **IF the conjecture holds partially** (one direction but not the
  other): publishable as a technical note or as the formal core of the
  merged paper with the remaining direction listed as open.

- **IF the conjecture fails**: write it up as a negative result — the
  categorical framing is suggestive but not universal; what's the
  minimal strengthening that makes it work? This is less exciting but
  still publishable at a formal-methods-friendly venue.

## Open Questions

1. Is there a natural topology on the space of quotient functors
   such that "how far from invertible is `Q`" becomes a measurable
   continuous quantity? This would make the conjecture quantitative
   rather than binary.
2. Does the conjecture extend to multi-layer defenses where multiple
   `Q_i` are composed?
3. What does the conjecture predict for neural (TC⁰) guardrails?
   Are there `Q`'s that a neural defender CAN invert but a regex
   defender cannot? This would formalize the composition laws of §10.

## Risk

**High** — this is the speculative one. Categorical unifications that
subsume multiple prior results as "special cases" are a known research
trap; half hold, half turn out to be vocabulary renaming. The 2–3 hour
"mirage check" in Phase 1 is the gate. If it passes, continue. If it
fails, abandon and fall back to Conjecture 1 as the merge-paper
strengthener.

## ❌ FAILURE ANALYSIS (2026-04-11)

**Three independent kill shots**:

1. **R1 audit finding**: Q never formally defined as functor anywhere in repo
   - No signatures F: X → Y with object/morphism maps
   - "quotient functor Q" used as vocabulary, not mathematics
   - grep search: 5 mentions, zero definitions

2. **Mathematical validation pipeline**: Parity-projection counterexample
   - Concrete falsifying system: E = {0,1}³, Q = parity function  
   - Satisfies compression + safety-critical but has NO mixed fibers
   - Universal claim "every compressing system has mixed fibers" = FALSE

3. **Proof checker findings**: Circular definitions + logical gaps
   - Safety defined as S(e,a) := safe iff a = Agent(Q(e)) 
   - Makes mixed fibers impossible by construction, not by argument
   - Missing formal foundations throughout

**Gate verdict**: 2-3h "mirage check" FAILED. Vocabulary renaming confirmed.

## R1 dependency

**This conjecture WAS R1**, in its most ambitious form. R1 is the
minimum-viable version (unify the two halves of the current paper);
this conjecture was the maximum-ambition version (unify all
inference-layer blindness attacks). 

**Resolution**: Keep narrow algebraic specialization (Theorem 6.1-6.2) only. 
Drop all universal Q framing. Honor the gate.
