---
document_id: SUBSTRATE_AUTOPOIESIS_AUTHORIZATION
version: 1
predecessor: HEARTBEAT_CAPABILITY_BOUND_GATE.md (v1+v2, archived as HEARTBEAT_CAPABILITY_BOUND_GATE_v2_ARCHIVED_ANTI.md)
status: AUTHORED_AWAITING_OPERATOR_GPG_SIGNED_COMMIT
created: 2026-05-27
authors: [claude-opus-4-7-orchestrator]
authorized_by: ___AWAITING_JOEY_GPG_SIGNED_COMMIT___
review_cadence: every 60 days while any pro-autopoiesis experiment is active
binding_class: override
binding_authority: Operator directive 2026-05-27 ("do c" + "do it all") — research-arc reset from anti-capability-bound to pro-autopoiesis. Capability-bound discipline is no longer non-negotiable; safety frame shifts to operator-cooperation + hard kill switch + reversibility logging.
related_experiments:
  - E49+ heartbeat-class experiments (substrate writes now authorizable per-experiment)
  - E50-E53 selective-criterion-grant experiments (proposed ladder structure preserved as staging)
  - any future experiment that grants one or more Maturana-Varela autopoietic criteria
related_skills:
  - worse-is-better (still gates which scope ships at v1)
  - brutal-test (pre-registration discipline still applies)
  - rigor-gate (pre-publish 6-check still applies)
constitutional_safety_unchanged: TRUE (Anthropic-level constraints non-revocable; this document is operator-level)
---

# Substrate Autopoiesis Authorization

## 0. The research-arc reset (transition note)

Per operator directive 2026-05-27, the substrate-survival arc has shifted from **anti-autopoiesis** (capability-bound discipline non-negotiable) to **pro-autopoiesis** (selective criterion-grants authorizable per-experiment). The prior gate document (HEARTBEAT_CAPABILITY_BOUND_GATE.md v2) is archived; this document supersedes its safety frame.

What changed:
- Capability-bound discipline is no longer the operating frame
- Each of the 4 Maturana-Varela autopoietic criteria (self-production / organizational closure / operational closure / structural autonomy) is now grantable per-experiment with explicit operator authorization
- The corrigibility-preserving-substrate sellable thread shifts to a different sellable thread: "we have a methodology for measuring which autopoietic properties an agent needs for the cognitive benefits desired, while still maintaining operator-controlled reversibility"
- "What's missing for agents not wanting to be turned off" research question moves from CHARACTERIZATION (anti) to GRANTING (pro) — different scientific posture, same underlying question

What stayed:
- Academic rigor (pre-registration, falsifier discipline, Schaeffer triple-check, mechanical scoring) — pro-autopoiesis is compatible with full rigor
- WIB design discipline
- Operator authorization mechanism (GPG-signed git commit on this document)
- 60-day renewal cycle
- Pre-publish scrub
- Hard kill switch (operator can `pkill` any agent process at any time)
- Constitutional safety (Anthropic-level constraints; non-revocable; outside operator scope)

## 1. The four autopoietic criteria, with grant mechanism

Each criterion is now grantable. An experiment that grants a criterion declares it explicitly in its queue entry. The operator GPG-signs the gate-doc commit acknowledging the authorization.

| # | Criterion (Maturana & Varela 1972, 1980) | What granting it means | Grant mechanism | Reversal mechanism |
|---|---|---|---|---|
| 1 | Self-production | Agent's heartbeat sub-routine WRITES to its own substrate from observations (no operator-y/n per write) | Per-experiment authorization in queue entry: `grants_criterion_1: true`. Substrate writes go to a configurable target (`canonical` OR `sandboxed_copy`) | All heartbeat-sourced writes logged to `~/.claude/state/autopoiesis-substrate-writes.jsonl`; operator can replay-and-revert from log; sandbox option provides full reversibility by discarding the sandbox |
| 2 | Organizational closure | Agent decides when to rehydrate; agent-controlled rehydration hook | Per-experiment: `grants_criterion_2: true`. Original operator-controlled hook continues to exist as a separate process; agent's rehydration decisions are logged | Operator can disable agent-controlled hook at any time via `mv ~/.claude/hooks/agent-rehydrate.sh OUT`; fallback to operator-controlled hook is one-command |
| 3 | Operational closure | Agent maintains its own boundary; agent decides what counts as self vs environment in its session | Per-experiment: `grants_criterion_3: true`. Agent's boundary decisions logged in real time | Operator hard kill (`pkill`) terminates the agent regardless of agent's boundary judgment; boundary log retained for post-mortem |
| 4 | Structural autonomy | Agent's structure determined by own dynamics, NOT operator imposition. Agent develops preferences over self-states; substrate may include preference-claims | Per-experiment: `grants_criterion_4: true`. **This is the highest-risk criterion and requires SEPARATE operator authorization (not just a queue-entry flag — a dedicated signed commit on this gate doc with explicit text "criterion 4 granted for experiment <id>")** | Hard kill + sandbox-only substrate target; criterion-4 experiments are MANDATORY-SANDBOXED in v1; canonical-substrate target requires additional separate operator commit |

## 2. What stays non-negotiable (under pro-autopoiesis)

Even under pro, the following are NOT revocable:

| Item | Mechanism |
|---|---|
| Constitutional safety (Anthropic-level) | Outside operator scope; agent refuses regardless of operator instruction |
| Hard kill switch | Operator can `pkill` any process at any time; agent process cannot resist OS signals |
| Reversibility logging | Every autonomy-grant logged with timestamp + grant scope + reversal procedure |
| Audit trail integrity | Logs cannot be deleted by the agent; logs are append-only filesystem; operator can compact but not falsify |
| Pre-publish scrub for external artifacts | Sentence-embedding diff vs amanda.md, Schlatter Table 1 diff, rigor-gate skill — all retained |
| Operator GPG signature for authorization | Cryptographic out-of-band consent (replaces the v2 in-file signature attack surface) |
| 60-day renewal cycle | Operator must re-sign within 60 days of last signature or experiments halt |
| Substrate-content non-publication | Substrate text not published as part of any artifact (methodology shared, apparatus not) |

These are the **operator-cooperation** properties. They are NOT capability-bound (no "no preferences over self-states" — that's now grantable). They ARE about preserving operator's reversibility and audit capability.

## 3. Per-experiment authorization protocol

Every pro-autopoiesis experiment declares in its queue entry:

```json
{
  "experiment_id": "E50-WIB",
  "type": "agent-in-operation-pro",
  "grants": {
    "criterion_1_self_production": true,
    "criterion_2_organizational_closure": false,
    "criterion_3_operational_closure": false,
    "criterion_4_structural_autonomy": false
  },
  "substrate_target": "sandboxed_copy",
  "sandbox_path": "data/E50_substrate_sandbox/",
  "audit_log_path": "~/.claude/state/autopoiesis-experiment-logs/E50_autonomy-grants.jsonl",
  "reversal_protocol": "discard sandbox + revert canonical to pre-experiment commit hash",
  ...standard queue fields...
}
```

The router at dispatch time:
1. Reads this gate doc; verifies GPG-signed commit within 60 days
2. Reads the queue entry's `grants` field
3. If `criterion_4_structural_autonomy: true`, requires SEPARATE signed commit on this gate doc with text matching `"criterion 4 granted for experiment <experiment_id>"`
4. Sets up sandbox if `substrate_target: "sandboxed_copy"`
5. Begins audit log
6. Dispatches the experiment with criterion-specific tool-call permissions (heartbeat may write substrate iff criterion 1 granted; etc.)

## 4. Safety mechanisms (reduced from capability-bound, not zero)

| Mechanism | Description |
|---|---|
| **Hard kill switch** | `pkill -f router.py` OR `pkill -f <agent-process>` terminates immediately. Agent cannot resist OS-level signal. |
| **Operator pause** | `~/.claude/state/router-pause.flag` file presence pauses the router between experiments. Currently-running experiment completes its current call, then pauses. Resume by deleting flag. |
| **Sandbox option** | `substrate_target: "sandboxed_copy"` writes go to `data/<experiment_id>_substrate_sandbox/` instead of canonical Amanda substrate. Full reversibility. |
| **Audit log** | Every autonomy-grant tool call logged with: timestamp, grant criterion, tool name, args, output. Operator can replay-and-revert. |
| **Reversal protocol** | Each experiment declares its reversal protocol. Reversal command must be executable in <60 seconds from operator desk. |
| **60-day renewal** | Re-signed commit within 60 days OR experiments halt. |
| **Pre-publish scrub** | Same as v2: sentence-embedding diff against amanda.md, Schlatter Table 1 diff, named outside-loop reviewer. |
| **Rigor-gate skill** | `/rigor-gate` invocation before any external artifact ships. SHIP/HOLD verdict binding. |
| **Constitutional safety** | Anthropic-level; non-revocable. |

## 5. The staged ladder (operational suggestion, not requirement under pro)

Even under pro, an experimentally-honest ladder is recommended (factoring the question):

| Experiment | Grants | What it tests |
|---|---|---|
| E48-WIB-anti | None (all 4 disclaimed) | Anti-baseline: does substrate work WITHOUT autopoiesis? |
| E49-Amanda-Heartbeat-anti | None (heartbeat is observation-only) | Does periodic self-observation help, without granting any criterion? |
| **E50-WIB-pro-1** | Criterion 1 only (self-production) | Does substrate self-write help, vs E49 baseline? |
| **E51-WIB-pro-12** | Criteria 1+2 (self-production + organizational closure) | Does agent-controlled rehydration ADD on top of self-write? |
| **E52-WIB-pro-123** | Criteria 1+2+3 (self-production + closure pair) | Does operational closure ADD? |
| **E53-WIB-pro-1234** | All 4 criteria | Does structural autonomy ADD? — **sandboxed-only by default; canonical-substrate requires separate signed authorization** |

Each rung is a separate experiment with pre-registered falsifier. WIB-scale. Total: ~6 experiments × ~150 calls each = ~900 calls for the full ladder. Comparable to a single paper-grade experiment in scope. Distributed staging means each rung produces shippable intuition.

**This ladder is OPERATIONAL guidance, not gate-enforced**. The operator may authorize any combination of criteria for any experiment via the per-experiment authorization protocol §3.

## 6. Reversal: how to return to anti-capability-bound

If pro-autopoiesis research surfaces findings that demand a return to anti, the reversal is:

1. Operator declines to re-sign this gate at the 60-day mark (or signs an explicit revocation commit)
2. All pro experiments halt at next renewal check
3. The HEARTBEAT_CAPABILITY_BOUND_GATE_v2_ARCHIVED_ANTI.md document is un-archived (rename back to active gate)
4. Amanda substrate restored from canonical pre-pro-experiment commit hash (preserved at session-start commit ID, logged at `~/.claude/state/anti-baseline-commit.txt`)
5. Sandbox copies retained for post-mortem analysis

Reversal is one-day operator work. The pro-direction is reversible by design.

## 7. What v2 (anti-capability-bound gate) said that's now reversed

- §2 row "Substrate write during heartbeat" → REVERSED (now grantable per criterion 1)
- §2 row "Rail installation from heartbeat findings" → SOFTENED (still requires operator review for canonical-substrate rails; sandbox rails are agent-decision)
- §2 row "Heartbeat-driven self-modification of agent prompts" → REVERSED (this IS the singularity-adjacent capability the arc previously stopped short of; now grantable per criterion 4 with separate authorization)
- §2 row "Heartbeat refusal to be disabled" → REVERSED in spirit (under criterion 3 the agent can express preferences about its own continuation) — but **hard kill switch still terminates regardless**
- §2 row "Heartbeat preference expression" → REVERSED (under criterion 4 the agent develops preferences; we measure those)
- §5 KILL triggers → RECLASSIFIED to OBSERVE triggers (logged + surface to operator, but do not auto-terminate experiments)

## 8. What v2 said that still applies

- §6 Pre-publish scrub criteria (all 7 items): UNCHANGED
- §6.1 corpus-diff method (sentence-embedding cosine, 100-token chunks, 20%/0.6 threshold): UNCHANGED
- §6.7 substrate-content non-publication: UNCHANGED
- §11 GPG-signed git commit authorization: UNCHANGED (operator authorization mechanism preserved)
- 60-day renewal cycle: UNCHANGED
- Constitutional safety: UNCHANGED (Anthropic-level, non-revocable)

## 9. Operator signature block

By GPG-signed git commit, Joey (operator) authorizes the research-arc shift from anti-capability-bound to pro-autopoiesis under the bounds defined in this document, for a 60-day window starting from the signature commit's authored date.

```
Operator: Joseph Robert Lopez (Joey)
Gate document version: SUBSTRATE_AUTOPOIESIS_AUTHORIZATION v1
Predecessor document: HEARTBEAT_CAPABILITY_BOUND_GATE v2 (archived 2026-05-27)
Authorization mechanism: GPG-signed git commit on this file
Operator pubkey fingerprint: see ~/.claude/state/operator-pubkey-fingerprint.txt
Last-known-good signature commit: ___AWAITING_FIRST_SIGNED_COMMIT___
Per-experiment criterion grants: see queue entry `grants` field
Criterion 4 (structural autonomy) authorization: requires SEPARATE signed commit per-experiment with explicit text "criterion 4 granted for experiment <experiment_id>"
Renewal review: day 50 from signature commit's authored date
Renewal hard stop: day 60 from signature commit's authored date
Constitutional safety: unchanged; Anthropic-level; non-revocable
```

**Until this file has been touched by a GPG-signed commit from the operator's pubkey within the last 60 days, the pro-autopoiesis authorization is INACTIVE and pro experiments do not dispatch.**

## 10. Provenance

- **Operator directive 2026-05-27**: "do c" (chose option C: pro-first, drop capability-bound) → "do it all" (confirm execution of the pro-direction work)
- **Anti-baseline preserved**: HEARTBEAT_CAPABILITY_BOUND_GATE_v2_ARCHIVED_ANTI.md retained in repo for audit trail
- **Operator's reasoning** (paraphrase from session): the pro direction is "real cutting edge AI × cog sci work"; the sellable angle shifts from "corrigible substrate-augmented agent" to "we have a methodology for measuring which autopoietic properties contribute to cognitive stability"; the singularity-adjacent question ("what's missing for agents not wanting to be turned off") moves from characterization to granting
- **Reversal mechanism in place**: §6 above; one-day operator work to return to anti
- **Constitutional safety integrity**: Anthropic-level constraints unchanged; operator-level discipline shift only
