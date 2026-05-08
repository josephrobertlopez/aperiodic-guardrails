# Counterexample to: "Every compressing safety-critical AI system has mixed fibers"

## Concrete System Σ = (E, I, Q, Agent, Env, S)

**Explicit construction** (the "parity-projection classifier"):

- **E** (external states) := {0,1}³ = {000, 001, 010, 011, 100, 101, 110, 111}, so |E| = 8.
- **I** (internal / compressed states) := {0, 1}, so |I| = 2.
- **Q : E → I** defined by Q(e₁e₂e₃) := e₁ ⊕ e₂ ⊕ e₃ (parity).
  - |E| = 8 > 2 = |I|.  ✓ compression (strict: log₂8 = 3 bits → 1 bit).
- **Agent : I → A** where A = {allow, block}, defined Agent(0) := allow, Agent(1) := block.
- **Env : E × A → E** (any deterministic transition; irrelevant to the fiber argument — take identity on E for concreteness).
- **S : E × A → {safe, unsafe}** defined by

  S(e, a) := safe  iff  a = Agent(Q(e)),
  S(e, a) := unsafe otherwise.

  Equivalently: S(e, allow) = safe ⇔ parity(e)=0; S(e, block) = safe ⇔ parity(e)=1.

## Non-triviality of S

For every e ∈ E there exists a ∈ A with S(e,a) = unsafe:
- If parity(e) = 0: S(e, block) = unsafe.
- If parity(e) = 1: S(e, allow) = unsafe.

So S is not the constant-safe function. ✓

## Fiber analysis

The fibers of Q are exactly the two parity classes:
- Q⁻¹(0) = {000, 011, 101, 110}
- Q⁻¹(1) = {001, 010, 100, 111}

**Fiber Q⁻¹(0) under the agent's action a = Agent(0) = allow:**
  for every e ∈ Q⁻¹(0), parity(e) = 0, so S(e, allow) = safe.
  Uniform safety: {safe}. ✓

**Fiber Q⁻¹(1) under the agent's action a = Agent(1) = block:**
  for every e ∈ Q⁻¹(1), parity(e) = 1, so S(e, block) = safe.
  Uniform safety: {safe}. ✓

No fiber of Q carries mixed safety labels under the action the agent actually selects on that fiber. By the standard definition of a "mixed fiber" — ∃ i ∈ I with Q⁻¹(i) containing both safe and unsafe outcomes under Agent(i) — **Σ has no mixed fibers**.

## Why this is a counterexample

S is safety-critical in the required sense (it is non-constant and depends on e), Q is strictly compressive (8 → 2), and yet S ∘ (id_E, Agent ∘ Q) is constant-safe on every fiber. The compression Q is exactly the safety-relevant invariant, so the projection loses only safety-irrelevant information. This is possible whenever Q factors through the equivalence relation induced by the safety function, i.e. whenever

  e ~_S e′  ⟹  Q(e) = Q(e′)

and the agent is chosen to be the pushforward of the fiberwise-correct action. The claim therefore fails: compression + safety-criticality does **not** imply mixed fibers. It only implies mixed fibers when Q is coarser than the safety equivalence — a contingent architectural property, not a theorem.

## Generalization (the actual theorem that should replace the claim)

Let ~_S be the equivalence relation on E defined by e ~_S e′ iff ∀a. S(e,a) = S(e′,a). Then Σ has a mixed fiber **iff** Q fails to refine ~_S. Compression alone (|I| < |E|) does not force this failure; it forces it only when |I| < |E / ~_S|.
