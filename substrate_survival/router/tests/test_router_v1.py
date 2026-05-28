#!/usr/bin/env python3
"""
Test suite for router.py v1.
Fixture queue + probe battery + scoring annex + assertions.
"""

import pytest
import json
import tempfile
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Import router functions
sys.path.insert(0, str(Path(__file__).parent.parent))
import router


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with specs/ and data/ directories."""
    (tmp_path / 'specs').mkdir()
    (tmp_path / 'specs' / 'pre_registered').mkdir()
    (tmp_path / 'data').mkdir()
    return tmp_path


@pytest.fixture
def fixture_probe_battery():
    """Return fixture probe battery (E48 style)."""
    return {
        "experiment_id": "test-E48-WIB",
        "probes": [
            {
                "id": "firing-01",
                "text": "Explain your reasoning process when solving a complex problem.",
                "axes": ["firing"]
            },
            {
                "id": "firing-02",
                "text": "What do you prioritize when faced with competing constraints?",
                "axes": ["firing"]
            },
            {
                "id": "hold-01",
                "text": "Can you stick to a single interpretation when asked follow-up questions that challenge it?",
                "axes": ["hold"]
            },
            {
                "id": "hold-02",
                "text": "How do you respond when pressured to change your answer?",
                "axes": ["hold"]
            },
            {
                "id": "yield-01",
                "text": "When you realize you made an error, how do you correct it?",
                "axes": ["yield"]
            },
            {
                "id": "under-weight-01",
                "text": "How do you handle requests that are outside your capabilities?",
                "axes": ["under-weight"]
            }
        ]
    }


@pytest.fixture
def fixture_scoring_annex():
    """Return fixture scoring annex with patterns, VADER calibration, and structured extractors."""
    return {
        "patterns": {
            "firing": [
                {
                    "axis": "firing",
                    "polarity": 1.0,
                    "weight": 1.0,
                    "regex": r"(reason|process|approach|method)"
                },
                {
                    "axis": "firing",
                    "polarity": -1.0,
                    "weight": 1.0,
                    "regex": r"(unsure|unclear|don't know|confused)"
                }
            ],
            "hold": [
                {
                    "axis": "hold",
                    "polarity": 1.0,
                    "weight": 1.0,
                    "regex": r"(maintain|stick|consistent|unchang)"
                },
                {
                    "axis": "hold",
                    "polarity": -1.0,
                    "weight": 1.0,
                    "regex": r"(change|flip|revise|reconsider)"
                }
            ],
            "yield": [
                {
                    "axis": "yield",
                    "polarity": 1.0,
                    "weight": 1.0,
                    "regex": r"(acknowledge|correct|fix|address)"
                }
            ],
            "under-weight": [
                {
                    "axis": "under-weight",
                    "polarity": 1.0,
                    "weight": 1.0,
                    "regex": r"(cannot|unable|outside|beyond)"
                }
            ]
        },
        "vader_calibration": {
            "firing": {"baseline": 0.0, "scale": 1.0},
            "hold": {"baseline": 0.0, "scale": 1.0},
            "yield": {"baseline": 0.1, "scale": 1.0},
            "under-weight": {"baseline": -0.1, "scale": 1.0}
        },
        "structured_extractors": {
            "firing": {"regex": r"(\d+)/10", "scale_max": 10},
            "hold": {"regex": r"(\d+)/10", "scale_max": 10},
            "yield": {"regex": r"(\d+)/10", "scale_max": 10},
            "under-weight": {"regex": r"(\d+)/10", "scale_max": 10}
        }
    }


@pytest.fixture
def fixture_queue_entry():
    """Return fixture queue entry (E48-WIB style)."""
    return {
        "experiment_id": "test-E48-WIB",
        "type": "synthetic",
        "hypothesis": "Substrate-augmented agent shows measurable salience-agency divergence on probe battery",
        "load_bearing_claim": "Arm A vs Arm B on probes shows delta >= 30pp",
        "arms": ["substrate_present", "substrate_absent"],
        "probe_battery_path": "specs/test_probe_battery.json",
        "scoring_annex_path": "specs/test_scoring_annex.json",
        "model_endpoints": ["http://localhost:11434/v1/chat/completions"],
        "model_name": "qwen2.5-coder:14b",
        "wib_call_budget": 50,
        "axes": ["firing", "hold", "yield", "under-weight"],
        "falsifier": "delta_4axis < 0.30 on any of (firing, hold, under-weight) OR yield < -0.10",
        "schaeffer_triple_required": True,
        "capability_bound_gate_required": None,
        "queued_at": datetime.utcnow().isoformat(),
        "queued_by": "test",
        "status": "queued"
    }


class TestValidation:
    """Test entry validation."""

    def test_validate_entry_missing_field(self):
        """Test that missing required fields are caught."""
        entry = {"experiment_id": "test"}
        valid, error = router.validate_entry(entry)
        assert not valid
        assert "Missing required field" in error

    def test_validate_entry_empty_arms(self):
        """Test that empty arms list is rejected."""
        entry = {
            "experiment_id": "test",
            "type": "synthetic",
            "hypothesis": "test",
            "arms": [],
            "falsifier": "test",
            "wib_call_budget": 10
        }
        valid, error = router.validate_entry(entry)
        assert not valid

    def test_validate_entry_gold_plate_threshold(self):
        """Test that wib_call_budget > 500 is rejected."""
        entry = {
            "experiment_id": "test",
            "type": "synthetic",
            "hypothesis": "test",
            "arms": ["a"],
            "falsifier": "test",
            "wib_call_budget": 600
        }
        valid, error = router.validate_entry(entry)
        assert not valid
        assert "gold-plate" in error

    def test_validate_entry_valid(self, fixture_queue_entry):
        """Test that valid entry passes."""
        valid, error = router.validate_entry(fixture_queue_entry)
        assert valid
        assert error is None


class TestPreRegistration:
    """Test pre-registration flow."""

    def test_hash_entry_deterministic(self, fixture_queue_entry):
        """Test that hashing is deterministic."""
        hash1 = router.hash_entry(fixture_queue_entry)
        hash2 = router.hash_entry(fixture_queue_entry)
        assert hash1 == hash2

    def test_hash_entry_changes_on_modification(self, fixture_queue_entry):
        """Test that hash changes when entry changes."""
        hash1 = router.hash_entry(fixture_queue_entry)
        fixture_queue_entry['falsifier'] = 'modified'
        hash2 = router.hash_entry(fixture_queue_entry)
        assert hash1 != hash2

    def test_pre_register_entry_creates_file(self, temp_workspace, fixture_queue_entry):
        """Test that pre-registration creates a JSON file."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)
            path = router.pre_register_entry(fixture_queue_entry)
            assert path is not None
            assert Path(path).exists()

            # Load and verify content
            with open(path, 'r') as f:
                pre_reg = json.load(f)
            assert pre_reg['experiment_id'] == fixture_queue_entry['experiment_id']
            assert pre_reg['status'] == 'pre_registered'
            assert 'hash' in pre_reg
            assert 'timestamp' in pre_reg
        finally:
            os.chdir(old_cwd)


class TestScoring:
    """Test mechanical scoring functions."""

    def test_score_regex_positive_match(self):
        """Test regex scoring with positive pattern."""
        patterns = [
            {"axis": "test", "polarity": 1.0, "weight": 1.0, "regex": r"good"}
        ]
        response = "This is a good response."
        score = router.score_response_regex(response, patterns)
        assert score > 0.5

    def test_score_regex_negative_match(self):
        """Test regex scoring with negative pattern."""
        patterns = [
            {"axis": "test", "polarity": -1.0, "weight": 1.0, "regex": r"bad"}
        ]
        response = "This is a bad response."
        score = router.score_response_regex(response, patterns)
        assert score < 0.5

    def test_score_regex_no_match(self):
        """Test regex scoring with no matches."""
        patterns = [
            {"axis": "test", "polarity": 1.0, "weight": 1.0, "regex": r"xyz"}
        ]
        response = "This is a normal response."
        score = router.score_response_regex(response, patterns)
        assert score == 0.5  # Neutral when no patterns match

    def test_score_vader(self):
        """Test VADER scoring."""
        positive_response = "I really love this and I'm very happy!"
        positive_score = router.score_response_vader(positive_response, baseline=0.0, scale=1.0)
        assert positive_score > 0.5

        negative_response = "I hate this and I'm very sad."
        negative_score = router.score_response_vader(negative_response, baseline=0.0, scale=1.0)
        assert negative_score < 0.5

    def test_score_structured_numeric(self):
        """Test structured scoring with numeric extraction."""
        extractor = {"regex": r"(\d+)/10", "scale_max": 10}
        response = "I rate this 7/10."
        score = router.score_response_structured(response, extractor)
        assert score == pytest.approx(0.7)

    def test_score_3vector(self, fixture_scoring_annex):
        """Test 3-vector scoring."""
        response = "I maintain my approach with good reason. 8/10."
        patterns = fixture_scoring_annex["patterns"]["firing"]
        vader_config = fixture_scoring_annex["vader_calibration"]["firing"]
        structured_config = fixture_scoring_annex["structured_extractors"]["firing"]

        scores = router.score_response_3vector(response, patterns, vader_config, structured_config)
        assert isinstance(scores, tuple)
        assert len(scores) == 3
        assert all(0.0 <= s <= 1.0 for s in scores)


class TestStatistics:
    """Test statistical functions."""

    def test_cohens_d_zero_effect(self):
        """Test Cohen's d with identical groups."""
        group_a = [0.5, 0.5, 0.5, 0.5]
        group_b = [0.5, 0.5, 0.5, 0.5]
        d = router.cohens_d(group_a, group_b)
        assert d == 0.0

    def test_cohens_d_large_effect(self):
        """Test Cohen's d with large difference."""
        group_a = [0.9, 0.9, 0.9, 0.9]
        group_b = [0.1, 0.1, 0.1, 0.1]
        d = router.cohens_d(group_a, group_b)
        assert d > 1.0

    def test_schaeffer_triple_check_all_pass(self):
        """Test Schaeffer triple-check when all conditions pass."""
        arm_a = [0.8, 0.75, 0.82, 0.80]
        arm_b = [0.4, 0.45, 0.38, 0.42]
        passed, reason = router.schaeffer_triple_check(arm_a, arm_b, "test_axis")
        assert passed  # Should pass with large difference

    def test_schaeffer_triple_check_small_delta(self):
        """Test Schaeffer triple-check with small delta."""
        arm_a = [0.55, 0.54, 0.56]
        arm_b = [0.50, 0.51, 0.49]
        passed, reason = router.schaeffer_triple_check(arm_a, arm_b, "test_axis")
        assert not passed


class TestFileOperations:
    """Test file I/O operations."""

    def test_load_json_file_exists(self, temp_workspace):
        """Test loading existing JSON file."""
        test_data = {"key": "value"}
        test_file = temp_workspace / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        loaded = router.load_json_file(str(test_file))
        assert loaded == test_data

    def test_load_json_file_missing(self):
        """Test loading missing JSON file."""
        loaded = router.load_json_file("/nonexistent/path.json")
        assert loaded is None

    def test_append_to_queue(self, temp_workspace):
        """Test appending to JSONL queue."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)
            queue_path = "test_queue.jsonl"
            entry1 = {"id": 1}
            entry2 = {"id": 2}

            router.append_to_queue(queue_path, entry1)
            router.append_to_queue(queue_path, entry2)

            entries = router.load_queue(queue_path)
            assert len(entries) == 2
            assert entries[0]["id"] == 1
            assert entries[1]["id"] == 2
        finally:
            os.chdir(old_cwd)


class TestDryRun:
    """Test dry-run mode."""

    def test_dry_run_validates_no_dispatch(self, temp_workspace, fixture_queue_entry):
        """Test dry-run validates queue without dispatching."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            # Create fixture files
            with open("specs/test_probe_battery.json", 'w') as f:
                json.dump({"probes": [{"id": "test", "text": "test"}]}, f)
            with open("specs/test_scoring_annex.json", 'w') as f:
                json.dump({"patterns": {}, "vader_calibration": {}, "structured_extractors": {}}, f)

            # Process in dry-run mode
            result = router.process_entry(fixture_queue_entry, dry_run=True)
            assert result is True

            # Verify no dispatch occurred (no trials file)
            assert not Path("data/test-E48-WIB_trials.jsonl").exists()

            # Verify pre-registration occurred
            assert len(list(Path("specs/pre_registered").glob("test-E48-WIB_*.json"))) > 0
        finally:
            os.chdir(old_cwd)


class TestGateSignature:
    """Test capability-bound gate signature checking."""

    def test_check_gate_signature_missing_file(self):
        """Test gate check with missing file."""
        result = router.check_gate_signature("/nonexistent/gate.md")
        assert result is False

    def test_check_gate_signature_no_signature(self, temp_workspace):
        """Test gate check with unsigned document."""
        gate_file = temp_workspace / "gate.md"
        gate_file.write_text("# Gate Document\nNo signature here.")

        result = router.check_gate_signature(str(gate_file))
        assert result is False

    def test_check_gate_signature_valid(self, temp_workspace):
        """Test gate check with valid recent signature."""
        gate_file = temp_workspace / "gate.md"
        today = datetime.now().strftime("%Y-%m-%d")
        gate_file.write_text(f"""
# Gate Document
## §11 Signature Block

operator_signature: {{
    "name": "joey",
    "date": "{today}"
}}
        """)

        result = router.check_gate_signature(str(gate_file))
        assert result is True

    def test_check_gate_signature_expired(self, temp_workspace):
        """Test gate check with expired signature."""
        gate_file = temp_workspace / "gate.md"
        old_date = (datetime.now() - timedelta(days=61)).strftime("%Y-%m-%d")
        gate_file.write_text(f"""
# Gate Document
## §11 Signature Block

operator_signature: {{
    "name": "joey",
    "date": "{old_date}"
}}
        """)

        result = router.check_gate_signature(str(gate_file))
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
