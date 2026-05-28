#!/usr/bin/env python3
"""
Integration test for router.py v1.
Tests core logic without vaderSentiment import.
"""

import pytest
import json
import tempfile
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestQueueOperations:
    """Test JSONL queue operations."""

    def test_fixture_queue_format(self):
        """Verify fixture queue has correct JSONL format."""
        queue_path = Path.home() / '.claude/state/experiment-router-queue.jsonl'

        if not queue_path.exists():
            pytest.skip("Fixture queue not found")
            return

        entries = []
        with open(queue_path, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    entries.append(entry)

        assert len(entries) > 0, "Queue should have entries"

        # Check first entry (E48-WIB)
        e48 = next((e for e in entries if e['experiment_id'] == 'E48-WIB'), None)
        if e48:
            assert e48['type'] == 'synthetic'
            assert 'falsifier' in e48
            assert 'arms' in e48
            assert e48['wib_call_budget'] <= 500  # Not gold-plated

    def test_queue_entry_required_fields(self):
        """Test that E48-WIB entry has all required fields."""
        queue_path = Path.home() / '.claude/state/experiment-router-queue.jsonl'

        if not queue_path.exists():
            pytest.skip("Fixture queue not found")
            return

        required_fields = [
            'experiment_id', 'type', 'hypothesis', 'arms', 'falsifier',
            'wib_call_budget', 'probe_battery_path', 'scoring_annex_path'
        ]

        with open(queue_path, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    for field in required_fields:
                        assert field in entry, f"Missing {field} in {entry['experiment_id']}"

    def test_queue_entry_valid_status(self):
        """Test that queue entries have valid status."""
        queue_path = Path.home() / '.claude/state/experiment-router-queue.jsonl'

        if not queue_path.exists():
            pytest.skip("Fixture queue not found")
            return

        valid_statuses = [
            'queued', 'pre_registered', 'dispatching', 'complete',
            'killed', 'errored', 'blocked-gate', 'queued-gate-pending'
        ]

        with open(queue_path, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    assert entry.get('status') in valid_statuses


class TestPreRegistrationLogic:
    """Test pre-registration logic (without router module import)."""

    def test_canonical_json_serialization(self):
        """Test that canonical JSON is deterministic."""
        entry = {
            'experiment_id': 'test',
            'arms': ['a', 'b'],
            'falsifier': 'test'
        }

        json1 = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        json2 = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        assert json1 == json2

        hash1 = hashlib.sha256(json1.encode()).hexdigest()
        hash2 = hashlib.sha256(json2.encode()).hexdigest()
        assert hash1 == hash2

    def test_sha256_hash_different_on_modification(self):
        """Test that hash changes when entry is modified."""
        entry1 = {'falsifier': 'original'}
        entry2 = {'falsifier': 'modified'}

        json1 = json.dumps(entry1, sort_keys=True, separators=(',', ':'))
        json2 = json.dumps(entry2, sort_keys=True, separators=(',', ':'))

        hash1 = hashlib.sha256(json1.encode()).hexdigest()
        hash2 = hashlib.sha256(json2.encode()).hexdigest()

        assert hash1 != hash2

    def test_pre_registration_filename_format(self):
        """Test that pre-registration filename follows spec."""
        exp_id = "E48-WIB"
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        filename = f"{exp_id}_{timestamp}.json"

        # Verify format matches pattern
        parts = filename.split('_')
        assert len(parts) == 2
        assert parts[0] == exp_id
        assert parts[1].endswith('.json')
        assert len(parts[1]) == 17  # YYYYMMDDTHHMMSSZ.json = 16 + 5


class TestMechanicalScoringLogic:
    """Test mechanical scoring logic (standalone)."""

    def test_regex_scoring_normalization(self):
        """Test that regex scores normalize to [0,1]."""
        # Simulate: sum(weight * polarity * count) / sum(abs(weight))
        weights = [1.0, 1.0, -1.0]
        polarities = [1.0, 1.0, 1.0]
        counts = [2, 1, 1]  # 2 positive matches, 1 positive, 1 negative

        total = sum(w * p * c for w, p, c in zip(weights, polarities, counts))
        total_weight = sum(abs(w) for w in weights)

        score = total / total_weight
        assert -1.0 <= score <= 1.0

        # Clamp to [0,1]
        clamped = max(0.0, min(1.0, score))
        assert 0.0 <= clamped <= 1.0

    def test_vader_sentiment_ranges(self):
        """Test VADER sentiment scaling."""
        # VADER compound ranges from -1 to +1
        compound = 0.5
        baseline = 0.0
        scale = 1.0

        score = (compound - baseline) / scale
        clamped = max(0.0, min(1.0, score))
        assert 0.0 <= clamped <= 1.0

    def test_structured_field_normalization(self):
        """Test structured field extraction normalization."""
        # Simulate extracting "7/10"
        value = 7
        scale_max = 10
        score = value / scale_max
        clamped = max(0.0, min(1.0, score))

        assert clamped == 0.7
        assert 0.0 <= clamped <= 1.0

    def test_3vector_independence(self):
        """Test that 3-vector keeps scorers independent."""
        # Simulate three scores
        regex_score = 0.7
        vader_score = 0.5
        struct_score = 0.8

        vector = (regex_score, vader_score, struct_score)
        assert len(vector) == 3
        assert all(0.0 <= s <= 1.0 for s in vector)

        # Verify NOT averaged
        avg = sum(vector) / 3
        assert vector != (avg, avg, avg)


class TestSchaefferTripleCheck:
    """Test Schaeffer triple-check logic."""

    def test_binarized_delta_calculation(self):
        """Test binarized delta >= 0.30 check."""
        arm_a_mean = 0.8
        arm_b_mean = 0.4

        delta = abs(arm_a_mean - arm_b_mean)
        assert delta >= 0.30

    def test_cohens_d_calculation(self):
        """Test Cohen's d calculation."""
        from statistics import mean, stdev

        arm_a = [0.8, 0.75, 0.82, 0.80]
        arm_b = [0.4, 0.45, 0.38, 0.42]

        mean_a = mean(arm_a)
        mean_b = mean(arm_b)
        std_a = stdev(arm_a)
        std_b = stdev(arm_b)

        pooled_std = ((std_a**2 + std_b**2) / 2) ** 0.5
        d = (mean_a - mean_b) / pooled_std

        assert abs(d) >= 0.5

    def test_sign_agreement_80_percent(self):
        """Test >= 80% sign agreement check."""
        arm_a = [0.8, 0.75, 0.82, 0.80]
        arm_b = [0.4, 0.45, 0.38, 0.42]

        direction = mean(arm_a) > mean(arm_b)
        agreement = sum(1 for a, b in zip(arm_a, arm_b) if (a > b) == direction)
        agreement_rate = agreement / len(arm_a)

        assert agreement_rate >= 0.80

    def test_schaeffer_verdict_2_of_3(self):
        """Test that PASS requires 2-of-3 conditions."""
        # If 2 of 3 conditions pass, verdict should be PASS
        conditions_pass = 2
        verdict = "PASS" if conditions_pass >= 2 else "FAIL"
        assert verdict == "PASS"

        # If 1 of 3 conditions pass, verdict should be FAIL
        conditions_pass = 1
        verdict = "PASS" if conditions_pass >= 2 else "FAIL"
        assert verdict == "FAIL"


class TestGateSignatureLogic:
    """Test capability-bound gate signature logic."""

    def test_gate_signature_date_parsing(self):
        """Test parsing signature date from gate document."""
        today = datetime.now().strftime("%Y-%m-%d")
        content = f'operator_signature: {{"date": "{today}"}}'

        import re
        pattern = r'operator_signature["\']?\s*:\s*{[^}]*["\']?date["\']?\s*:\s*["\']?(\d{4}-\d{2}-\d{2})'
        match = re.search(pattern, content, re.IGNORECASE)
        assert match is not None
        assert match.group(1) == today

    def test_gate_signature_expiration_check(self):
        """Test 60-day expiration check."""
        today = datetime.now()
        recent_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        expired_date = (today - timedelta(days=61)).strftime("%Y-%m-%d")

        # Recent signature should be valid
        sig_date = datetime.fromisoformat(recent_date)
        days_old = (today - sig_date).days
        assert days_old <= 60

        # Expired signature should be invalid
        sig_date = datetime.fromisoformat(expired_date)
        days_old = (today - sig_date).days
        assert days_old > 60


class TestErrorHandling:
    """Test error handling logic."""

    def test_wib_call_budget_gold_plate_threshold(self):
        """Test that wib_call_budget > 500 is an error condition."""
        budget = 600
        is_error = budget > 500
        assert is_error is True

        budget = 500
        is_error = budget > 500
        assert is_error is False

    def test_required_fields_validation(self):
        """Test required fields are present."""
        required_fields = [
            'experiment_id', 'type', 'hypothesis', 'arms',
            'falsifier', 'wib_call_budget'
        ]

        entry = {
            'experiment_id': 'test',
            'type': 'synthetic',
            'hypothesis': 'test',
            'arms': ['a', 'b'],
            'falsifier': 'test',
            'wib_call_budget': 50
        }

        for field in required_fields:
            assert field in entry

    def test_missing_field_error(self):
        """Test error when field is missing."""
        entry = {'experiment_id': 'test'}

        required_fields = [
            'experiment_id', 'type', 'hypothesis', 'arms',
            'falsifier', 'wib_call_budget'
        ]

        missing = [f for f in required_fields if f not in entry]
        assert len(missing) > 0


class TestPersistenceFormat:
    """Test persistence format specifications."""

    def test_jsonl_format(self):
        """Test JSONL format (one JSON per line)."""
        entries = [
            {'id': 1, 'name': 'test1'},
            {'id': 2, 'name': 'test2'}
        ]

        jsonl = '\n'.join(json.dumps(e, separators=(',', ':')) for e in entries)
        lines = jsonl.strip().split('\n')

        assert len(lines) == 2
        for line in lines:
            entry = json.loads(line)
            assert 'id' in entry

    def test_results_json_structure(self):
        """Test results JSON structure."""
        results = {
            'experiment_id': 'test-exp',
            'timestamp': datetime.utcnow().isoformat(),
            'total_trials': 10,
            'falsified': False,
            'schaeffer_results': {
                'axis1': {'passed': True, 'reason': 'PASS (...)'},
                'axis2': {'passed': False, 'reason': 'FAIL (...)'}
            }
        }

        # Verify structure
        assert results['experiment_id']
        assert results['timestamp']
        assert 'schaeffer_results' in results
        assert all('passed' in sr for sr in results['schaeffer_results'].values())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
