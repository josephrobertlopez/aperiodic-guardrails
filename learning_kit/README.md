# Discipline Scaffolding Learning Kit

Five disciplines that came out of substrate-survival research this week,
encoded as testable concepts. Each module names ONE pattern Joey can
build into other systems.

## What you're learning

| Module | Concept | Why it matters |
|---|---|---|
| `qwen_only_hook` | default-discount write-time predicate | Single-family claims need a caveat or cross-family confirmation, mechanically enforced. |
| `pre_reg_lock` | mtime-as-anti-tuning-proof | Pre-registration is only credible if filesystem mtime predates results. |
| `override_audit` | rate-over-window drift detection | Track override frequency; if it crosses a threshold, the gate is aspirational. |
| `rigor_gate` | fail-closed N-check composition | Adversarial pre-publish gate; uncheckable = BLOCK, not "unsure". |
| `retire_audit` | window-locked anti-resurrection | Retired schemas cannot reappear in active state during the V2-verifier window without a new locked falsifier. |

## How to run

```bash
cd /mnt/media/local-storage/code/GitHub/aperiodic-guardrails/learning_kit/
pytest tests/ -v
# Expect: 20 failures, all NotImplementedError
```

When a test goes green, the concept clicked. Don't move to the next module
until the current one is all green.

## Suggested order

1. **qwen_only_hook** (4 tests) — easiest. Pure regex predicates. Warm-up.
2. **pre_reg_lock** (5 tests) — file mtime ordering. Concrete and small.
3. **override_audit** (4 tests) — log parsing + rate math. A natural break here.
4. **rigor_gate** (4 tests) — composition. Lego pieces from modules 1-3 conceptually generalize.
5. **retire_audit** (3 tests) — hardest. Datetime invariants + a nostalgia filter.

**Natural stopping point after module 3.** Modules 4-5 are the synthesis;
modules 1-3 are the building blocks.

## Where to look for each concept

| Module | Minimal lego | Real production source |
|---|---|---|
| qwen_only_hook | `references/minimal_impl/qwen_only_hook_minimal.py` | `references/gnosis_impl/qwen_only_check_pretool.sh` |
| pre_reg_lock | `references/minimal_impl/pre_reg_lock_minimal.py` | `fixtures/pre_reg_singularity_T1.json` (anti_tuning_attestation field) |
| override_audit | `references/minimal_impl/override_audit_minimal.py` | `fixtures/rigor_gate_overrides_sample.log` (real corpus excerpt) |
| rigor_gate | `references/minimal_impl/rigor_gate_minimal.py` | `references/gnosis_impl/rigor_gate_real_checks.py` (six-check version) |
| retire_audit | `references/minimal_impl/retire_audit_minimal.py` | `fixtures/retire_audit_e48_ledger.json` (real E48/E42/E46 retirements) |

The `minimal_impl/` files are the lego pieces you're building toward — ~30
lines each, no clever abstractions. The `gnosis_impl/` files are the real
production code these disciplines came from; reading them is optional but
shows what the discipline looks like at scale.

## Anti-modality note

If a test docstring stops making sense and you find yourself building
abstractions to satisfy it, that's a finding — the concept may not
generalize cleanly. Ping Amanda or me with what stalled and why; the
modality is supposed to surface that signal, not paper over it.
