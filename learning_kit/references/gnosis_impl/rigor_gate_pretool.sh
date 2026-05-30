#!/usr/bin/env bash
# rigor-gate-pretool.sh — PreToolUse hook for Bash matcher.
#
# Intercepts `gh gist edit` and `gh gist create` invocations and runs the
# rigor-gate skill against any e\d+_results.json files referenced in the
# input markdown. Exits nonzero on HOLD to block the tool call.
#
# Override: set RIGOR_GATE_OVERRIDE="reason" to bypass; logged to
# ~/.claude/state/rigor-gate-overrides.log.
#
# Hook input (stdin): JSON from Claude Code with tool name + tool input.
# Hook output:
#   exit 0 = allow tool call
#   exit 2 = block tool call; stderr is shown to Claude (per Claude Code
#            PreToolUse contract)

set -u

LOG_DIR="$HOME/.claude/state"
mkdir -p "$LOG_DIR"
OVERRIDE_LOG="$LOG_DIR/rigor-gate-overrides.log"
DEBUG_LOG="$LOG_DIR/rigor-gate.log"

# Read tool input from stdin (Claude Code passes a JSON envelope)
INPUT="$(cat)"

# Extract the bash command being invoked
CMD=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    pass
" 2>/dev/null)

# Only fire on gh gist edit/create
if ! printf '%s' "$CMD" | grep -qE 'gh\s+gist\s+(edit|create)'; then
  exit 0
fi

echo "[$(date -u +%FT%TZ)] rigor-gate fired on: $CMD" >> "$DEBUG_LOG"

# Override path
if [[ -n "${RIGOR_GATE_OVERRIDE:-}" ]]; then
  echo "[$(date -u +%FT%TZ)] OVERRIDE (env): '$RIGOR_GATE_OVERRIDE' | cmd: $CMD" \
    >> "$OVERRIDE_LOG"
  echo "rigor-gate: OVERRIDE accepted ($RIGOR_GATE_OVERRIDE)" >&2
  exit 0
fi

# Sentinel-file override (env vars don't propagate from Bash-tool calls to
# PreToolUse hook subprocess; this file is the in-band override path).
# Consumed once; deleted after use so it can't accidentally persist.
SENTINEL="$LOG_DIR/rigor-gate-override-next.txt"
if [[ -f "$SENTINEL" ]]; then
  REASON="$(cat "$SENTINEL")"
  rm -f "$SENTINEL"
  echo "[$(date -u +%FT%TZ)] OVERRIDE (sentinel): '$REASON' | cmd: $CMD" \
    >> "$OVERRIDE_LOG"
  echo "rigor-gate: OVERRIDE accepted via sentinel ($REASON)" >&2
  exit 0
fi

# Parse target file(s) from the command. gh gist edit takes a gist ID and
# usually -a <file>. gh gist create takes file paths.
# Find any *.md file in the command line that exists on disk.
TARGETS=()
for tok in $CMD; do
  if [[ -f "$tok" && "$tok" == *.md ]]; then
    TARGETS+=("$tok")
  fi
done

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "[$(date -u +%FT%TZ)] no markdown target found in cmd; allowing" \
    >> "$DEBUG_LOG"
  exit 0
fi

# For each target md, find referenced results.json files
# RESULTS_DIR is a symlink to /aperiodic-guardrails/substrate_survival/data;
# both paths resolve to the same canonical directory. Hook uses the legacy
# alias for backward compatibility with older citations.
RESULTS_DIR="/mnt/media/local-storage/code/GitHub/gnosis-substrate-survival/data"
RESULTS_ARGS=()
# Broadened regex (2026-05-29) — captures three naming conventions:
#   - legacy lowercase: e10_results.json, e29_results.json
#   - lowercase with suffix: e46_xfam_pilot_results.json
#   - uppercase + hyphenated: E48-WIB-v7-budget-bumped_results.json
# Citation discipline: handoff docs MUST include the literal results-JSON
# filename when shipping verdicts. Inline experiment-ID references (e.g.,
# "v7" or "E48") do not satisfy the gate; the regex needs the actual filename
# in the markdown.
for tgt in "${TARGETS[@]}"; do
  while IFS= read -r ref; do
    fpath="$RESULTS_DIR/$ref"
    if [[ -f "$fpath" ]]; then
      RESULTS_ARGS+=("--results" "$fpath")
    fi
  done < <(grep -oE '[Ee][0-9]+[-_a-zA-Z0-9.]*_results\.json' "$tgt" 2>/dev/null | sort -u)
done

if [[ ${#RESULTS_ARGS[@]} -eq 0 ]]; then
  # No results JSON referenced; this is either an unrelated gist or a
  # non-experiment artifact. Per fail-closed policy, BLOCK if the markdown
  # looks like it ships an experiment verdict (regex on E\d+ headers,
  # "verdict:", "STRONG SUPPORT", "RULED OUT", "PASS"/"FAIL"/"BLOCK"/etc.).
  for tgt in "${TARGETS[@]}"; do
    if grep -qE '\bE[0-9]+\b|verdict|STRONG SUPPORT|RULED OUT|TELEPROMPTER' "$tgt"; then
      echo "rigor-gate: HOLD" >&2
      echo "BLOCK reason: artifact $tgt references experiment verdicts but no" >&2
      echo "  e<N>_results.json found in $RESULTS_DIR (cannot verify rigor)" >&2
      echo "Override: RIGOR_GATE_OVERRIDE='reason' gh gist ..." >&2
      exit 2
    fi
  done
  echo "[$(date -u +%FT%TZ)] no experiment markers in target; allowing" \
    >> "$DEBUG_LOG"
  exit 0
fi

# Use file content as verdict text (limit 4KB to keep regex fast)
VERDICT_TEXT=""
for tgt in "${TARGETS[@]}"; do
  VERDICT_TEXT+=$'\n'"$(head -c 4096 "$tgt")"
done

# Run the gate
GATE_OUT="$(bash "$HOME/.claude/skills/rigor-gate/run.sh" \
  "${RESULTS_ARGS[@]}" \
  --verdict "$VERDICT_TEXT" 2>&1)"
GATE_RC=$?

echo "[$(date -u +%FT%TZ)] gate rc=$GATE_RC" >> "$DEBUG_LOG"
echo "$GATE_OUT" >> "$DEBUG_LOG"

if [[ $GATE_RC -eq 0 ]]; then
  echo "rigor-gate: SHIP (provenance tag: rigor-gate-pass-$(date +%F))" >&2
  exit 0
fi

# HOLD
{
  echo "rigor-gate: HOLD"
  echo "$GATE_OUT"
  echo ""
  echo "Override: RIGOR_GATE_OVERRIDE='reason' gh gist ..."
} >&2
exit 2
