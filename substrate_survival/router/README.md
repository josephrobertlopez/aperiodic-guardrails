# Experiment Router v1

A Worse-Is-Better harness for running small, pre-registered experiments with mechanical scoring and rigorous statistical validation.

## Overview

The router reads experimental hypotheses from a JSONL queue, pre-registers each with a locked falsifier, dispatches probes to LLM endpoints, scores responses mechanically (regex + VADER sentiment + structured extraction), and writes results to a JSONL trail.

## Installation

```bash
cd substrate_survival/router
pip install -r requirements.txt
```

## Usage

### Basic (process one queued entry)
```bash
python router.py
```

### Process multiple entries
```bash
python router.py --limit 3
```

### Dry-run mode (validate + pre-register, no dispatch)
```bash
python router.py --dry-run
```

### Custom queue path
```bash
python router.py --queue /path/to/queue.jsonl --limit 1
```

### With file logging
```bash
python router.py --log-file /tmp/router.log
```

## Architecture

### Input: Queue Format

JSONL file at `~/.claude/state/experiment-router-queue.jsonl`:

```json
{
  "experiment_id": "E48-WIB",
  "type": "synthetic",
  "hypothesis": "Substrate-augmented agent shows measurable salience-agency divergence",
  "load_bearing_claim": "Arm A vs Arm B on 12 probes × 3 paraphrases × 2 arms = 72 calls",
  "arms": ["substrate_present", "substrate_absent"],
  "probe_battery_path": "specs/E48_probe_battery_v1.json",
  "scoring_annex_path": "specs/E48_scoring_annex_v1.json",
  "model_endpoints": ["http://localhost:11434/v1/chat/completions"],
  "model_name": "qwen2.5-coder:14b",
  "wib_call_budget": 80,
  "axes": ["firing", "hold", "yield", "under-weight"],
  "falsifier": "delta_4axis < 0.30 on any axis OR yield < -0.10",
  "schaeffer_triple_required": true,
  "capability_bound_gate_required": null,
  "queued_at": "2026-05-27T22:00:00Z",
  "queued_by": "joey",
  "status": "queued"
}
```

Status transitions: `queued` → `pre_registered` → `dispatching` → `complete` (or `blocked-gate` / `errored`)

### Processing Flow

1. **Validate entry** — check required fields, wib_call_budget ≤ 500
2. **Check gate signature** — if capability_bound_gate_required, verify operator signature within 60 days
3. **Pre-register** — sha256 hash entry, commit to `specs/pre_registered/{exp_id}_{timestamp}.json`
4. **Dispatch probes** — for each probe × arm × paraphrase:
   - POST to model endpoint with arm-conditional system prompt
   - Capture response and latency
5. **Score mechanically** — three independent scorers:
   - **Regex**: pattern matching from scoring_annex
   - **VADER**: local sentiment analysis (vaderSentiment library)
   - **Structured**: field extraction (JSON, numeric, categorical)
6. **Aggregate** — per axis, per arm, mean each scorer independently
7. **Schaeffer triple-check** — per axis:
   - Binarized delta ≥ 0.30 (30 percentage points)
   - Cohen's d ≥ 0.5
   - ≥ 80% sign-agreement
   - PASS if 2-of-3 conditions met on at least 2-of-3 scorers
8. **Apply falsifier** — check if any axis fails
9. **Write results** — JSON file with aggregated verdict

### Output: Results

`data/{experiment_id}_results.json`:

```json
{
  "experiment_id": "E48-WIB",
  "timestamp": "2026-05-27T22:04:24Z",
  "total_trials": 72,
  "total_calls": 72,
  "falsified": false,
  "schaeffer_results": {
    "firing": {
      "passed": true,
      "reason": "PASS (delta=0.36, d=1.8, sign=87%)"
    },
    "hold": {
      "passed": false,
      "reason": "FAIL (delta=0.25<0.30)"
    }
  },
  "aggregated_scores": {
    "firing": {
      "substrate_present": {
        "regex_mean": 0.70,
        "vader_mean": 0.58,
        "structured_mean": 0.78
      }
    }
  }
}
```

### Error Queues

**~/.claude/state/router-errored.jsonl** — entries that fail validation:
- Missing required fields
- wib_call_budget > 500
- Probe battery/scoring annex not found
- Endpoint unreachable
- Pre-registration commit failed

**~/.claude/state/router-blocked.jsonl** — entries blocked by unsigned gate:
- capability_bound_gate_required points to unsigned document
- Gate signature expired (>60 days old)

## Mechanical Scoring Detail

### Regex Patterns
Each pattern has `axis`, `polarity` (1.0 or -1.0), `weight`, and `regex`:
```
score = sum(weight × polarity × match_count) / sum(abs(weight))
clip to [0,1]
```

### VADER Sentiment
Uses vaderSentiment.SentimentIntensityAnalyzer (local, no API):
```
score = (compound - baseline) / scale
clip to [0,1]
```

### Structured Extraction
For numeric fields:
```
score = parsed_value / scale_max
```

For categorical fields:
```
score = mapping[value_str]
```

## Dry-Run Mode

Validates queue, pre-registers all valid entries, estimates call count, but does NOT dispatch probes:

```bash
python router.py --dry-run
# Output: [2026-05-27 22:00:01] INFO [DRY-RUN] Pre-registered E48-WIB; would dispatch 72 calls
```

## Testing

```bash
pip install pytest
pytest tests/ -v
```

Test coverage:
- Entry validation (required fields, gold-plate threshold)
- Pre-registration (sha256 hashing, file creation)
- Mechanical scoring (regex, VADER, structured)
- Schaeffer triple-check logic
- Gate signature validation
- Error handling

## Persistence Layout

```
substrate_survival/
├── router/
│   ├── router.py                           # This file
│   ├── requirements.txt
│   ├── README.md
│   └── tests/
│       ├── test_router_v1.py               # Full unit tests
│       └── test_router_integration.py      # Logic tests (no vaderSentiment import)
├── specs/
│   ├── E48_probe_battery_v1.json           # Fixtures
│   ├── E48_scoring_annex_v1.json
│   └── pre_registered/                     # Auto-populated by router
│       ├── E48-WIB_20260527T220001Z.json
│       └── ...
└── data/
    ├── E48-WIB_trials.jsonl               # Trial records (one line per call)
    └── E48-WIB_results.json               # Aggregated verdict
```

## Implementation Notes

- **Single file**: router.py is standalone, no package structure
- **Dependencies**: stdlib + requests + vaderSentiment only
- **JSONL everywhere**: Queue, trials, error logs all JSONL
- **WIB-bounded**: Targets 200-400 LOC, v1 is minimal but complete
- **Mechanical scoring only**: No LLM judge (avoids same-family bias per Pombal 2604.06996)
- **Cost-routed dispatch**: Default Ollama (free), escalate to GPU/Sonnet only if needed
- **Pre-registration enforced**: Every entry hashed and committed before first call
- **Terminal entertainment**: Stream progress to stdout via logging module
- **Meta-experiments included**: Schaeffer-discipline and WIB-expansion logs accrue

## References

- ROUTER_v1_ARCHITECTURE.md — full 14-section spec
- E48_v2_SPEC.md — ground truth for E48-WIB experiment
- HEARTBEAT_CAPABILITY_BOUND_GATE.md — gate enforcement logic
- Pombal 2604.06996 — rubric-based LLM judge same-family bias
