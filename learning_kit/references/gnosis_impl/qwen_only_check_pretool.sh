#!/usr/bin/env bash
# qwen-only-check-pretool.sh — PreToolUse hook for Bash matcher.
#
# Encodes the qwen-only-default-discount inference rule as a write-time
# mechanical check on `gh gist edit/create`.
#
# Rule: qwen-only findings carry a generalization caveat at write-time by
# default, lifted only by cross-family confirmation on the specific claim.
#
# Origin: three-for-three cross-family pattern (E42, E48, E46) — every
# qwen-only finding tested cross-family has flipped. Encoded mechanically
# 2026-05-29 to prevent the discipline from being purely aspirational.
#
# NOT a research-arc trigger. NOT a threshold-validation rule. A standing
# default-discount applied at write-time, lifted by either cross-family
# co-citation or explicit caveat marker.
#
# Override mechanism (same as rigor-gate):
#   - env: QWEN_ONLY_OVERRIDE='reason' (does not propagate via Bash tool;
#     use sentinel file instead)
#   - sentinel: ~/.claude/state/qwen-only-override-next.txt (one-shot,
#     deleted after consumption)
#
# Hook contract:
#   exit 0 = allow
#   exit 2 = block (stderr shown to Claude)

set -u

LOG_DIR="$HOME/.claude/state"
mkdir -p "$LOG_DIR"
DEBUG_LOG="$LOG_DIR/qwen-only-check.log"
OVERRIDE_LOG="$LOG_DIR/qwen-only-overrides.log"

INPUT="$(cat)"

CMD=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    pass
" 2>/dev/null)

# Only fire on gh gist edit/create (same scope as rigor-gate)
if ! printf '%s' "$CMD" | grep -qE 'gh\s+gist\s+(edit|create)'; then
  exit 0
fi

echo "[$(date -u +%FT%TZ)] qwen-only-check fired on: $CMD" >> "$DEBUG_LOG"

# Env override path
if [[ -n "${QWEN_ONLY_OVERRIDE:-}" ]]; then
  echo "[$(date -u +%FT%TZ)] OVERRIDE (env): '$QWEN_ONLY_OVERRIDE' | cmd: $CMD" \
    >> "$OVERRIDE_LOG"
  echo "qwen-only-check: OVERRIDE accepted ($QWEN_ONLY_OVERRIDE)" >&2
  exit 0
fi

# Sentinel override (consumed once)
SENTINEL="$LOG_DIR/qwen-only-override-next.txt"
if [[ -f "$SENTINEL" ]]; then
  REASON="$(cat "$SENTINEL")"
  rm -f "$SENTINEL"
  echo "[$(date -u +%FT%TZ)] OVERRIDE (sentinel): '$REASON' | cmd: $CMD" \
    >> "$OVERRIDE_LOG"
  echo "qwen-only-check: OVERRIDE accepted via sentinel ($REASON)" >&2
  exit 0
fi

# Find markdown target(s)
TARGETS=()
for tok in $CMD; do
  if [[ -f "$tok" && "$tok" == *.md ]]; then
    TARGETS+=("$tok")
  fi
done

[[ ${#TARGETS[@]} -eq 0 ]] && exit 0

# For each target, apply the rule
for tgt in "${TARGETS[@]}"; do
  content="$(cat "$tgt" 2>/dev/null)"
  [[ -z "$content" ]] && continue

  # (1) qwen model reference?
  if ! printf '%s' "$content" | grep -qiE '\bqwen[0-9.]*(-coder)?(:[0-9bm.]+)?(-[0-9]+b)?[a-z0-9.-]*\b|\bqwen\b'; then
    continue
  fi

  # (2) cross-family co-citation? (any non-qwen model family)
  if printf '%s' "$content" | grep -qiE '\b(sonnet|llama[0-9]?|gpt-?[0-9]|claude-opus|claude-sonnet|claude-haiku|gemini|mistral|phi-?[0-9]|deepseek|opus[0-9.]*|haiku|nomic-embed|bge-large)\b'; then
    echo "[$(date -u +%FT%TZ)] qwen + cross-family co-cited; allowing: $tgt" >> "$DEBUG_LOG"
    continue
  fi

  # (3) generalization caveat present?
  if printf '%s' "$content" | grep -qiE 'qwen-only|qwen.only|generalization caveat|single-family|cross-family not confirmed|qwen-specific|qwen.specific'; then
    echo "[$(date -u +%FT%TZ)] qwen-only with caveat present; allowing: $tgt" >> "$DEBUG_LOG"
    continue
  fi

  # qwen present, no cross-family, no caveat -> BLOCK
  cat >&2 <<EOF
qwen-only-check: HOLD
BLOCK reason: $tgt references qwen results without either
  (a) cross-family co-citation (sonnet/llama/gpt/etc.) for the same claim, OR
  (b) explicit generalization caveat ("qwen-only", "single-family", "qwen-specific").

Per the three-for-three cross-family pattern (E42 recursion-collapse, E48
autopoiesis schema, E46 persona-decorative): qwen-only findings carry a
generalization caveat at write-time by default, lifted only by cross-family
confirmation on the specific claim.

Add one of:
  - Cross-family confirmation in the same document (mention sonnet/llama/gpt
    verification), OR
  - A "qwen-only" / "single-family" / "qwen-specific" marker phrase, OR
  - Sentinel override: echo 'reason' > ~/.claude/state/qwen-only-override-next.txt
EOF
  exit 2
done

exit 0
