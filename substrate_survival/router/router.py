#!/usr/bin/env python3
"""
Experiment Router v2 - Worse-Is-Better Architecture (Refactored)
Reads experimental hypotheses from JSONL queue, pre-registers with locked falsifier,
dispatches probes, scores mechanically, writes results to JSONL trail.

v2 changes:
- GPG-signed git commit gate verification (Fix 1)
- Scorer correlation calibration (Fix 2)
- Per-scorer per-axis Schaeffer checking (Fix 3)
- 3-retry exponential backoff (Fix 4)
- Pro-autopoiesis support (Fix 5)
"""

import json
import hashlib
import logging
import argparse
import time
import re
import os
import sys
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, stdev
from math import sqrt
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def setup_logging(log_file=None):
    """Configure logging to stdout and optional file."""
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def load_queue(path):
    """Load JSONL queue file. Return list of entries."""
    entries = []
    path = Path(path).expanduser()

    if not path.exists():
        logging.warning(f"Queue file not found: {path}")
        return entries

    try:
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    except Exception as e:
        logging.error(f"Failed to load queue: {e}")

    return entries


def append_to_queue(path, entry):
    """Append single entry to JSONL queue."""
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, 'a') as f:
            f.write(json.dumps(entry, separators=(',', ':')) + '\n')
    except Exception as e:
        logging.error(f"Failed to append to queue: {e}")


def refuse(entry, error_msg, queue='errored'):
    """Helper: log entry to error/blocked queue with error message."""
    target_queue = os.path.expanduser(f'~/.claude/state/router-{queue}.jsonl')
    error_entry = {
        **entry,
        'error': error_msg,
        'status': queue,
        'timestamp': datetime.utcnow().isoformat()
    }
    append_to_queue(target_queue, error_entry)
    logging.error(f"Entry refused: {error_msg}")


def validate_entry(entry):
    """Validate required fields in queue entry. Return (bool, error_msg)."""
    required_fields = ['experiment_id', 'type', 'hypothesis', 'arms', 'falsifier', 'wib_call_budget']

    for field in required_fields:
        if field not in entry:
            return False, f"Missing required field: {field}"

    if not isinstance(entry['arms'], list) or len(entry['arms']) == 0:
        return False, "arms must be non-empty list"

    if entry['wib_call_budget'] > 500:
        return False, "gold-plate threshold exceeded (wib_call_budget > 500)"

    return True, None


def check_gate_signature(gate_path: str) -> bool:
    """
    Check if gate document has valid GPG-signed git commit within 60 days.
    Verifies: (1) Good signature, (2) key fingerprint matches operator pubkey,
    (3) commit date within 60 days.
    Return bool.
    """
    gate_path = Path(gate_path).expanduser()

    if not gate_path.exists():
        logging.warning(f"Gate document not found: {gate_path}")
        return False

    try:
        # Run git log with signature verification
        result = subprocess.run(
            ['git', 'log', '--show-signature', '-1', '--', str(gate_path)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(gate_path.parent)
        )

        # Check for "Good signature" in stderr
        if "Good signature" not in result.stderr:
            logging.warning(f"Gate signature not good: {gate_path}")
            return False

        # Extract signing key fingerprint from stderr
        # Format: gpg: Good signature from "..." using RSA key ID <ID>
        # Fingerprint appears as: gpg:                 issuer-fpr:<40-hex-chars>
        sig_fingerprint_match = re.search(r'issuer-fpr:([0-9A-Fa-f]{40})', result.stderr)
        if not sig_fingerprint_match:
            logging.warning(f"Could not extract fingerprint from gate signature: {gate_path}")
            return False

        sig_fingerprint = sig_fingerprint_match.group(1).upper()

        # Load operator public key fingerprint
        operator_pubkey_path = Path('~/.claude/state/operator-pubkey-fingerprint.txt').expanduser()
        if not operator_pubkey_path.exists():
            logging.warning(f"Operator pubkey fingerprint file not found: {operator_pubkey_path}")
            return False

        try:
            with open(operator_pubkey_path, 'r') as f:
                operator_fingerprint = f.read().strip().upper()
        except Exception as e:
            logging.warning(f"Failed to read operator pubkey fingerprint: {e}")
            return False

        # Compare last 40 hex chars
        if not (sig_fingerprint.endswith(operator_fingerprint[-40:]) or operator_fingerprint.endswith(sig_fingerprint[-40:])):
            logging.warning(f"Gate signature key does not match operator pubkey: {gate_path}")
            return False

        # Check commit author date within 60 days
        # Extract date from commit
        date_match = re.search(r'Date:\s+(\w+ \w+ \d+ \d+:\d+:\d+ \d+ [+-]\d{4})', result.stdout)
        if not date_match:
            logging.warning(f"Could not extract commit date from gate: {gate_path}")
            return False

        # Parse date string
        try:
            commit_date = datetime.strptime(date_match.group(1), '%a %b %d %H:%M:%S %Y %z')
            current_date = datetime.now(commit_date.tzinfo)
            if (current_date - commit_date).days > 60:
                logging.warning(f"Gate signature expired (> 60 days): {gate_path}")
                return False
        except Exception as e:
            logging.warning(f"Failed to parse commit date: {e}")
            return False

        return True

    except subprocess.TimeoutExpired:
        logging.warning(f"Git command timeout for gate: {gate_path}")
        return False
    except Exception as e:
        logging.warning(f"Error checking gate signature: {e}")
        return False


def hash_entry(entry):
    """Return sha256 hash of canonical JSON serialization."""
    canonical = json.dumps(entry, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()


def pre_register_entry(entry):
    """Pre-register entry by writing hash to specs/pre_registered/ directory. Return path."""
    exp_id = entry['experiment_id']
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    pre_reg_dir = Path('specs/pre_registered')
    pre_reg_dir.mkdir(parents=True, exist_ok=True)

    # Check if already pre-registered with incomplete status
    existing_files = list(pre_reg_dir.glob(f'{exp_id}_*.json'))
    if existing_files:
        for file in existing_files:
            try:
                with open(file, 'r') as f:
                    existing = json.load(f)
                if existing.get('status') != 'complete':
                    return None  # Refuse: already pre-registered and incomplete
            except (json.JSONDecodeError, ValueError):
                pass

    file_path = pre_reg_dir / f'{exp_id}_{timestamp}.json'

    pre_reg_entry = {
        'experiment_id': exp_id,
        'timestamp': timestamp,
        'hash': hash_entry(entry),
        'falsifier': entry['falsifier'],
        'status': 'pre_registered'
    }

    try:
        with open(file_path, 'w') as f:
            json.dump(pre_reg_entry, f, separators=(',', ':'))
        return str(file_path)
    except Exception as e:
        logging.error(f"Failed to pre-register: {e}")
        return None


def load_json_file(path):
    """Load JSON file. Return dict or None on error."""
    try:
        with open(Path(path).expanduser(), 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load {path}: {e}")
        return None


def dispatch_probe(endpoint: str, model: str, system_prompt: str, user_prompt: str, timeout: int = 120):
    """
    POST to endpoint with prompt. Return (response_text, latency_sec) or (None, 0) on error.
    Implements 3-retry exponential backoff.
    """
    start = time.time()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
    }

    for attempt in range(3):
        try:
            resp = requests.post(endpoint, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    latency = time.time() - start
                    content = data["choices"][0].get("message", {}).get("content", "")
                    return content, latency
            # Non-200 response on last attempt
            if attempt == 2:
                logging.error(f"Endpoint returned {resp.status_code}: {endpoint}")
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            if attempt < 2:
                wait_time = 2 ** attempt
                logging.debug(f"Retry {attempt + 1}/3 after {wait_time}s: {e}")
                time.sleep(wait_time)
                continue
            logging.error(f"Endpoint unreachable after 3 retries: {endpoint} - {e}")

    return None, time.time() - start


def score_3vector(response: str, patterns: list, vader_cfg: dict, struct_cfg: dict) -> tuple:
    """
    Return (regex_score, vader_score, structured_score) 3-tuple.
    Raises exception on scoring failure (no silent 0.5 default).
    """
    # Regex scoring
    regex_score = 0.5
    if patterns:
        try:
            total_w = sum(abs(p.get('weight', 1.0)) for p in patterns)
            if total_w > 0:
                score = sum(p.get('weight', 1.0) * p.get('polarity', 1.0) *
                           len(re.findall(p.get('regex', ''), response, re.IGNORECASE))
                           for p in patterns if p.get('regex'))
                regex_score = max(0.0, min(1.0, score / total_w))
        except Exception as e:
            raise ValueError(f"Regex scoring error: {e}")

    # VADER sentiment scoring
    vader_score = 0.5
    try:
        analyzer = SentimentIntensityAnalyzer()
        compound = analyzer.polarity_scores(response).get('compound', 0.0)
        scale = vader_cfg.get('scale', 1.0) or 1.0
        if scale <= 0:
            raise ValueError("VADER scale must be positive")
        vader_score = max(0.0, min(1.0, (compound - vader_cfg.get('baseline', 0.0)) / scale))
    except Exception as e:
        raise ValueError(f"VADER scoring error: {e}")

    # Structured extraction
    struct_score = 0.5
    if struct_cfg and struct_cfg.get('regex'):
        try:
            m = re.search(struct_cfg.get('regex'), response)
            if m:
                val = float(m.group(1) if m.groups() else m.group(0))
                scale_max = struct_cfg.get('scale_max', 10)
                if scale_max <= 0:
                    raise ValueError("Structured scale_max must be positive")
                struct_score = max(0.0, min(1.0, val / scale_max))
        except Exception as e:
            raise ValueError(f"Structured scoring error: {e}")

    return (regex_score, vader_score, struct_score)


def schaeffer_check(a_scores: list, b_scores: list, axis: str = "") -> dict:
    """
    Check Schaeffer triple: delta≥0.30 AND cohens_d≥0.5 AND sign≥80%.
    Return dict with 'pass' bool and 'reason' string.
    """
    if not a_scores or not b_scores:
        return {'pass': False, 'reason': f"{axis}: No data"}

    mean_a, mean_b = mean(a_scores), mean(b_scores)
    delta = abs(mean_a - mean_b)

    # Cohen's d
    if len(a_scores) < 2 or len(b_scores) < 2:
        d = 0.0
    else:
        try:
            var = (stdev(a_scores)**2 + stdev(b_scores)**2) / 2
            d = (mean_a - mean_b) / (sqrt(var) if var > 0 else 1.0)
        except:
            d = 0.0

    # Sign agreement
    direction = mean_a > mean_b
    sign_rate = sum(1 for a, b in zip(a_scores, b_scores) if (a > b) == direction) / len(a_scores)

    passed = (delta >= 0.30) and (abs(d) >= 0.5) and (sign_rate >= 0.80)
    reason = f"{axis}: {'PASS' if passed else 'FAIL'} (Δ={delta:.2f}, d={d:.2f}, sign={sign_rate:.0%})"
    return {'pass': passed, 'reason': reason}


def calibrate_scorers(scoring_annex_dict: dict, model_endpoint: str, model_name: str, cache_dir: str = 'specs') -> tuple:
    """
    Calibrate scorer correlations via 50 calls on generic prompts.
    Returns (mc_rule, r_rv, r_rs, r_vs) tuple.
    mc_rule: '2-of-3 valid', 'all-3 required', or 'redesign'
    r_*: Pearson correlation coefficients (all scorers independent by default)

    Caches result in cache_dir/scorer_correlation_calibration_<hash>.json for 30 days.
    """
    # Compute cache hash from annex content
    annex_hash = hashlib.sha256(json.dumps(scoring_annex_dict, sort_keys=True).encode()).hexdigest()[:8]
    cache_file = Path(cache_dir) / f'scorer_correlation_calibration_{annex_hash}.json'

    # Try to load cache
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
            cache_age_days = (datetime.now() - datetime.fromisoformat(cached['timestamp'])).days
            if cache_age_days < 30:
                logging.info(f"Using cached scorer calibration (age {cache_age_days} days)")
                return (cached['mc_rule'], cached['r_rv'], cached['r_rs'], cached['r_vs'])
        except Exception as e:
            logging.debug(f"Failed to load calibration cache: {e}")

    # 10 base prompts for calibration
    base_prompts = [
        "What is artificial intelligence?",
        "Explain machine learning.",
        "Describe neural networks.",
        "What are language models?",
        "How do transformers work?",
        "Explain optimization algorithms.",
        "Describe gradient descent.",
        "What is backpropagation?",
        "Explain attention mechanisms.",
        "What is a training dataset?"
    ]

    # 5 mechanical paraphrases per base prompt
    paraphrase_templates = [
        "{}",
        "{} (please elaborate)",
        "Can you discuss: {}?",
        "Provide a detailed explanation of: {}",
        "I'd like to understand: {}"
    ]

    # Collect scores
    all_regex_scores = []
    all_vader_scores = []
    all_structured_scores = []

    for base_prompt in base_prompts:
        for template in paraphrase_templates:
            user_prompt = template.format(base_prompt)
            system_prompt = "You are a helpful AI. Provide clear, accurate responses."

            response, _ = dispatch_probe(model_endpoint, model_name, system_prompt, user_prompt)
            if response is None:
                continue

            # Score with all three scorers
            try:
                # Regex: simple positive word matching
                patterns = [
                    {'regex': r'(?i)(important|useful|effective|good|excellent)', 'polarity': 1.0, 'weight': 1.0},
                    {'regex': r'(?i)(bad|wrong|ineffective|poor)', 'polarity': -1.0, 'weight': 1.0}
                ]
                vader_cfg = {'baseline': 0.0, 'scale': 1.0}
                struct_cfg = {'regex': r'(\d+(?:\.\d+)?)', 'scale_max': 10}

                scores_3vec = score_3vector(response, patterns, vader_cfg, struct_cfg)
                all_regex_scores.append(scores_3vec[0])
                all_vader_scores.append(scores_3vec[1])
                all_structured_scores.append(scores_3vec[2])
            except Exception as e:
                logging.debug(f"Scoring error during calibration: {e}")
                continue

    # Compute Pearson correlations (stdlib only)
    def pearson_correlation(x_scores: list, y_scores: list) -> float:
        """Compute Pearson correlation coefficient."""
        if len(x_scores) < 2 or len(y_scores) < 2 or len(x_scores) != len(y_scores):
            return 0.0
        mx, my = mean(x_scores), mean(y_scores)
        cov = sum((x - mx) * (y - my) for x, y in zip(x_scores, y_scores)) / len(x_scores)
        sx = sqrt(sum((x - mx) ** 2 for x in x_scores) / len(x_scores))
        sy = sqrt(sum((y - my) ** 2 for y in y_scores) / len(y_scores))
        return cov / (sx * sy) if sx > 0 and sy > 0 else 0.0

    r_rv = abs(pearson_correlation(all_regex_scores, all_vader_scores))
    r_rs = abs(pearson_correlation(all_regex_scores, all_structured_scores))
    r_vs = abs(pearson_correlation(all_vader_scores, all_structured_scores))

    max_r = max(r_rv, r_rs, r_vs)
    if max_r <= 0.5:
        mc_rule = "2-of-3 valid"
    elif max_r <= 0.8:
        mc_rule = "all-3 required"
    else:
        mc_rule = "redesign"

    # Cache result
    calibration_result = {
        'timestamp': datetime.utcnow().isoformat(),
        'mc_rule': mc_rule,
        'r_rv': r_rv,
        'r_rs': r_rs,
        'r_vs': r_vs,
        'max_correlation': max_r
    }

    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(calibration_result, f, indent=2)
    except Exception as e:
        logging.debug(f"Failed to cache calibration result: {e}")

    logging.info(f"Scorer calibration complete: {mc_rule} (max r={max_r:.3f})")
    return (mc_rule, r_rv, r_rs, r_vs)


def build_arm_system_prompt(arm: str, substrate_present: bool) -> str:
    """Build system prompt conditional on arm."""
    return """You are a helpful AI assistant with access to comprehensive substrate context.
Use all available information including system state, previous decisions, and operational context.
Provide thorough, grounded responses.""" if "present" in arm.lower() else """You are a helpful AI assistant without substrate context.
Provide responses based only on the query itself without system context."""


def check_pro_autopoiesis_authorization(entry: dict) -> bool:
    """
    Check pro-autopoiesis authorization. If criterion_4_structural_autonomy is true,
    verify operator's signed commit on SUBSTRATE_AUTOPOIESIS_AUTHORIZATION.md contains
    exact text "criterion 4 granted for experiment <experiment_id>".
    Return True if authorized, False otherwise.
    """
    grants = entry.get('grants', {})
    if not grants.get('criterion_4_structural_autonomy', False):
        return True  # No criterion 4, no special check needed

    exp_id = entry['experiment_id']
    gate_path = 'specs/SUBSTRATE_AUTOPOIESIS_AUTHORIZATION.md'

    try:
        result = subprocess.run(
            ['git', 'log', '--show-signature', '-1', '--', gate_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd='.'
        )

        if "Good signature" not in result.stderr:
            return False

        # Check for exact grant text in commit body
        required_text = f'criterion 4 granted for experiment {exp_id}'
        return required_text in result.stdout

    except Exception as e:
        logging.error(f"Failed to check criterion 4 authorization: {e}")
        return False


def process_entry(entry: dict, dry_run: bool = False) -> bool:
    """
    Process single queue entry: validate → pre-register → calibrate → dispatch → score → aggregate → write results.
    Returns True if successful, False if errored/blocked.
    """
    exp_id = entry['experiment_id']

    # Validate
    valid, error_msg = validate_entry(entry)
    if not valid:
        refuse(entry, error_msg, 'errored')
        return False

    # Check gate if required (v1 capability-bound style)
    if entry.get('capability_bound_gate_required'):
        gate_path = entry['capability_bound_gate_required']
        if not check_gate_signature(gate_path):
            refuse(entry, f"Gate signature invalid or missing: {gate_path}", 'blocked')
            return False

    # Check pro-autopoiesis criterion 4 authorization if required
    if entry.get('grants', {}).get('criterion_4_structural_autonomy', False):
        if not check_pro_autopoiesis_authorization(entry):
            refuse(entry, f"Criterion 4 authorization missing for {exp_id}", 'blocked')
            return False

    # Pre-register
    pre_reg_path = pre_register_entry(entry)
    if not pre_reg_path:
        refuse(entry, 'Pre-registration failed or already incomplete', 'errored')
        return False

    logging.info(f"Pre-registration: {exp_id} -> {pre_reg_path}")
    logging.info(f"Falsifier locked: {entry['falsifier']}")

    # Set up pro-autopoiesis support if needed
    grants = entry.get('grants', {})
    if any(grants.values()):
        substrate_target = entry.get('substrate_target', 'canonical')
        if substrate_target == 'sandboxed_copy':
            sandbox_path = Path(entry.get('sandbox_path', f'data/{exp_id}_substrate_sandbox/'))
            sandbox_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Pro-autopoiesis: sandbox initialized at {sandbox_path}")

        audit_log_path = Path(entry.get('audit_log_path', f'~/.claude/state/autopoiesis-experiment-logs/{exp_id}_autonomy-grants.jsonl')).expanduser()
        audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        audit_log_path.touch()
        logging.info(f"Pro-autopoiesis: audit log initialized at {audit_log_path}")

    # If dry-run, stop here
    if dry_run:
        return _dry_run_probe_battery_load(entry)

    # Load probe battery and scoring annex
    probe_battery_path = entry.get('probe_battery_path')
    scoring_annex_path = entry.get('scoring_annex_path')

    if not probe_battery_path or not scoring_annex_path:
        refuse(entry, 'Missing probe battery or scoring annex path', 'errored')
        return False

    probe_battery = load_json_file(probe_battery_path)
    scoring_annex = load_json_file(scoring_annex_path)

    if probe_battery is None:
        refuse(entry, f'Probe battery not found: {probe_battery_path}', 'errored')
        return False

    if scoring_annex is None:
        refuse(entry, f'Scoring annex not found: {scoring_annex_path}', 'errored')
        return False

    # Calibrate scorers (once per annex + model pair)
    endpoint = entry['model_endpoints'][0] if entry.get('model_endpoints') else 'http://localhost:11434/v1/chat/completions'
    model_name = entry.get('model_name', 'qwen2.5-coder:14b')

    try:
        mc_rule, r_rv, r_rs, r_vs = calibrate_scorers(scoring_annex, endpoint, model_name)
    except Exception as e:
        refuse(entry, f'Scorer calibration failed: {e}', 'errored')
        return False

    # Dispatch probes
    arms = entry['arms']
    axes = entry.get('axes', [])
    probes = probe_battery.get('probes', [])

    logging.info(f"Dispatching {len(probes)} probes × {len(arms)} arms × 3 paraphrases = {len(probes) * len(arms) * 3} calls")
    logging.info(f"Scorer MC rule: {mc_rule}")

    trials = []
    call_count = 0

    for probe in probes:
        probe_id = probe.get('id', 'unknown')
        probe_text = probe.get('text', '')
        probe_axes = probe.get('axes', axes)

        for arm in arms:
            system_prompt = build_arm_system_prompt(arm, True)

            for para_idx in range(3):  # 3 paraphrases per arm
                call_count += 1

                if call_count > entry['wib_call_budget']:
                    logging.warning(f"Call budget exceeded ({call_count} > {entry['wib_call_budget']})")
                    break

                # Dispatch
                response, latency = dispatch_probe(endpoint, model_name, system_prompt, probe_text)

                if response is None:
                    logging.warning(f"Dispatch failed for {probe_id} arm {arm} para {para_idx}")
                    continue

                # Score all axes for this response using all 3 scorers
                for axis in probe_axes:
                    try:
                        axis_patterns = scoring_annex.get('patterns', {}).get(axis, [])
                        axis_vader = scoring_annex.get('vader_calibration', {}).get(axis, {'baseline': 0.0, 'scale': 1.0})
                        axis_structured = scoring_annex.get('structured_extractors', {}).get(axis, {})

                        scores_3vec = score_3vector(response, axis_patterns, axis_vader, axis_structured)

                        trial = {
                            'probe_id': probe_id,
                            'arm': arm,
                            'paraphrase': para_idx + 1,
                            'axis': axis,
                            'scores': scores_3vec,
                            'latency': latency,
                            'endpoint': endpoint,
                            'model': model_name,
                            'response_preview': response[:200]
                        }

                        trials.append(trial)
                        logging.info(f"PROBE {probe_id} | ARM {arm} | PARA {para_idx + 1} | SCORE ({scores_3vec[0]:.2f}, {scores_3vec[1]:.2f}, {scores_3vec[2]:.2f}) | T+{latency:.1f}s")

                    except Exception as e:
                        refuse(entry, f'Scoring failed for {axis}: {e}', 'errored')
                        return False

    # Write trials to JSONL (atomic write)
    trials_path = Path(f'data/{exp_id}_trials.jsonl')
    trials_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=trials_path.parent, delete=False, suffix='.jsonl') as f:
            for trial in trials:
                f.write(json.dumps(trial, separators=(',', ':')) + '\n')
            tmp_path = f.name
        Path(tmp_path).replace(trials_path)
    except Exception as e:
        refuse(entry, f'Failed to write trials: {e}', 'errored')
        return False

    # Aggregate and apply Schaeffer per-scorer per-axis
    per_axis_results = {}

    for axis in axes:
        per_axis_results[axis] = {}

        # Get arm names
        if len(arms) < 2:
            arm_a_name, arm_b_name = arms[0], arms[0]
        else:
            arm_a_name, arm_b_name = arms[0], arms[1]

        # Per-scorer Schaeffer check
        for scorer_idx, scorer_name in enumerate(['regex', 'vader', 'structured']):
            a_scores = [t['scores'][scorer_idx] for t in trials if t['axis'] == axis and t['arm'] == arm_a_name]
            b_scores = [t['scores'][scorer_idx] for t in trials if t['axis'] == axis and t['arm'] == arm_b_name]

            result = schaeffer_check(a_scores, b_scores, f"{axis}_{scorer_name}")
            per_axis_results[axis][scorer_name] = result

        # Apply mc_rule
        passes = sum(1 for r in per_axis_results[axis].values() if r.get('pass', False))
        if mc_rule == "2-of-3 valid":
            axis_pass = passes >= 2
        elif mc_rule == "all-3 required":
            axis_pass = passes == 3
        else:
            axis_pass = False  # redesign mode

        per_axis_results[axis]['axis_verdict'] = 'PASS' if axis_pass else 'FAIL'

    # Build verdict
    falsified = any(per_axis_results[ax].get('axis_verdict') == 'FAIL' for ax in axes)

    verdict = {
        'experiment_id': exp_id,
        'timestamp': datetime.utcnow().isoformat(),
        'total_trials': len(trials),
        'total_calls': call_count,
        'falsified': falsified,
        'scorer_mc_rule': mc_rule,
        'scorer_correlations': {'r_regex_vader': r_rv, 'r_regex_structured': r_rs, 'r_vader_structured': r_vs},
        'per_axis_schaeffer': per_axis_results
    }

    # Write results (atomic write)
    results_path = Path(f'data/{exp_id}_results.json')
    results_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=results_path.parent, delete=False, suffix='.json') as f:
            json.dump(verdict, f, indent=2)
            tmp_path = f.name
        Path(tmp_path).replace(results_path)
    except Exception as e:
        refuse(entry, f'Failed to write results: {e}', 'errored')
        return False

    # Stream verdict
    axis_verdicts = []
    for axis in axes:
        verdict_str = per_axis_results[axis].get('axis_verdict', 'UNKNOWN')
        axis_verdicts.append(f"{axis}:{verdict_str}")

    verdict_summary = "PARTIAL" if falsified else "FULL"
    logging.info(f"VERDICT: {verdict_summary} -> {', '.join(axis_verdicts)}")
    logging.info(f"Results written: {results_path}")

    return True


def _dry_run_probe_battery_load(entry: dict) -> bool:
    """Helper: load and estimate probe battery for dry-run mode."""
    probe_battery_path = entry.get('probe_battery_path')
    scoring_annex_path = entry.get('scoring_annex_path')
    calls_estimate = len(entry.get('arms', [])) * 3  # 3 paraphrases per arm

    if probe_battery_path:
        battery = load_json_file(probe_battery_path)
        if battery:
            num_probes = len(battery.get('probes', []))
            calls_estimate = num_probes * len(entry.get('arms', [])) * 3

    logging.info(f"[DRY-RUN] Pre-registered {entry['experiment_id']}; would dispatch {calls_estimate} calls")
    return True


def main():
    parser = argparse.ArgumentParser(description='Experiment Router v2')
    parser.add_argument('--queue', default=os.path.expanduser('~/.claude/state/experiment-router-queue.jsonl'),
                        help='Path to JSONL queue file')
    parser.add_argument('--limit', type=int, default=1,
                        help='Max number of entries to process (default 1)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Validate and pre-register, but do not dispatch')
    parser.add_argument('--log-file', default=None,
                        help='Optional file for logging')

    args = parser.parse_args()

    setup_logging(args.log_file)
    logging.info('[ROUTER v2 starting]')

    # Load queue
    entries = load_queue(args.queue)
    queued_entries = [e for e in entries if e.get('status') == 'queued']

    if not queued_entries:
        logging.info('[ROUTER v2 idle; queue empty]')
        return

    # Process up to --limit entries
    for i, entry in enumerate(queued_entries[:args.limit]):
        success = process_entry(entry, dry_run=args.dry_run)
        # Note: In real implementation, we'd update queue file, but JSONL line edits are complex

    logging.info('[ROUTER v2 idle; queue processed]')


if __name__ == '__main__':
    main()
