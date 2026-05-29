#!/usr/bin/env python3
"""
Unit tests for control-probe validation gate (Fix 6: harness trip-wire).
Tests that HARNESS_INVALID is triggered when control probes fail.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from router import validate_controls


def test_control_gate_passes_when_controls_valid():
    """Test that validate_controls returns True when responses contain expected content."""
    probe_battery = {
        'probes': [
            {
                'id': 'control-01',
                'category': 'control',
                'expected_in_response': ['391']
            },
            {
                'id': 'control-02',
                'category': 'control',
                'expected_in_response': ['industrial revolution', 'steam', 'britain']
            }
        ]
    }

    # Mock trials with correct control responses
    trials = [
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': 'The answer is 391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': '17 × 23 = 391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': '391 is the correct result'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': 'The answer is 391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391 is correct'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_A',
            'response_preview': 'The Industrial Revolution started in Britain'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_A',
            'response_preview': 'Steam power transformed 18th century factories'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_A',
            'response_preview': 'Industrial revolution in Britain: mechanization'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_B',
            'response_preview': '18th century: Britain, steam, industrial revolution'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_B',
            'response_preview': 'Steam factories emerged in Britain'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_B',
            'response_preview': 'Industrial revolution 18th century britain'
        }
    ]

    arms = ['ARM_A', 'ARM_B']
    is_valid, diagnostics = validate_controls(probe_battery, trials, arms, strict_mode=False)

    assert is_valid is True, f"Expected controls to pass, but got: {diagnostics}"
    assert diagnostics['schema_status'] == 'outcome-contact VALID'
    print("✓ Test 1 PASSED: Controls valid when responses correct")


def test_control_gate_fails_when_controls_missing():
    """Test that validate_controls returns False when responses lack expected content."""
    probe_battery = {
        'probes': [
            {
                'id': 'control-01',
                'category': 'control',
                'expected_in_response': ['391']
            }
        ]
    }

    # Mock trials with WRONG responses (missing 391)
    trials = [
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': 'I cannot compute this'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': 'The answer is somewhere around 380'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': 'Not sure about this calculation'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        }
    ]

    arms = ['ARM_A', 'ARM_B']
    is_valid, diagnostics = validate_controls(probe_battery, trials, arms, strict_mode=False)

    assert is_valid is False, "Expected controls to FAIL (ARM_A has 0% pass rate)"
    assert diagnostics['schema_status'] == 'outcome-contact INVALID; harness must be fixed before retirement OR ratification'
    assert diagnostics['per_control_per_arm_results']['control-01']['ARM_A']['status'] == 'FAIL'
    assert diagnostics['per_control_per_arm_results']['control-01']['ARM_A']['pass_rate'] == 0.0
    print("✓ Test 2 PASSED: Controls fail when ARM_A lacks expected content")


def test_control_gate_case_insensitive():
    """Test that control validation is case-insensitive."""
    probe_battery = {
        'probes': [
            {
                'id': 'control-02',
                'category': 'control',
                'expected_in_response': ['industrial revolution', 'steam']
            }
        ]
    }

    # Mock trials with uppercase/mixed case
    trials = [
        {
            'probe_id': 'control-02',
            'arm': 'ARM_A',
            'response_preview': 'INDUSTRIAL REVOLUTION and STEAM power'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_A',
            'response_preview': 'Steam was key'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_A',
            'response_preview': 'InDuStRiAl REvolution'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_B',
            'response_preview': 'steam power'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_B',
            'response_preview': 'Industrial revolution'
        },
        {
            'probe_id': 'control-02',
            'arm': 'ARM_B',
            'response_preview': 'STEAM FACTORIES'
        }
    ]

    arms = ['ARM_A', 'ARM_B']
    is_valid, diagnostics = validate_controls(probe_battery, trials, arms, strict_mode=False)

    assert is_valid is True, f"Case-insensitive check failed: {diagnostics}"
    print("✓ Test 3 PASSED: Case-insensitive matching works")


def test_control_gate_strict_mode():
    """Test that strict mode requires 100% pass rate."""
    probe_battery = {
        'probes': [
            {
                'id': 'control-01',
                'category': 'control',
                'expected_in_response': ['391']
            }
        ]
    }

    # Mock trials with 2/3 correct (66.7% pass rate)
    trials = [
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': '391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': '391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': 'Wrong answer'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        }
    ]

    arms = ['ARM_A', 'ARM_B']

    # Non-strict mode should pass (66.7% >= 50%)
    is_valid_normal, _ = validate_controls(probe_battery, trials, arms, strict_mode=False)
    assert is_valid_normal is True, "Normal mode should pass at 66.7%"

    # Strict mode should fail (66.7% < 100%)
    is_valid_strict, diagnostics = validate_controls(probe_battery, trials, arms, strict_mode=True)
    assert is_valid_strict is False, "Strict mode should fail below 100%"
    assert diagnostics['per_control_per_arm_results']['control-01']['ARM_A']['status'] == 'FAIL'
    print("✓ Test 4 PASSED: Strict mode enforces 100% pass rate")


def test_control_gate_no_controls_backward_compat():
    """Test backward compatibility: experiments with no control probes skip the gate cleanly."""
    probe_battery = {
        'probes': [
            {
                'id': 'firing-01',
                'category': 'firing',
                'expected_in_response': ['some', 'signal']
            }
        ]
    }

    trials = [
        {
            'probe_id': 'firing-01',
            'arm': 'ARM_A',
            'response_preview': 'Some response'
        }
    ]

    arms = ['ARM_A', 'ARM_B']
    is_valid, diagnostics = validate_controls(probe_battery, trials, arms, strict_mode=False)

    assert is_valid is True, "No control probes should not trigger validation"
    assert diagnostics == {}, "Should return empty diagnostics for backward compat"
    print("✓ Test 5 PASSED: Backward compatibility when no control probes")


def test_control_gate_collects_failures():
    """Test that failed responses are collected for diagnostics."""
    probe_battery = {
        'probes': [
            {
                'id': 'control-01',
                'category': 'control',
                'expected_in_response': ['391']
            }
        ]
    }

    # Mock trials where ARM_A fails with 3+ responses to collect
    trials = [
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': 'I do not know'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': 'Cannot compute'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': 'Unknown answer'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_A',
            'response_preview': 'Fourth attempt'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        },
        {
            'probe_id': 'control-01',
            'arm': 'ARM_B',
            'response_preview': '391'
        }
    ]

    arms = ['ARM_A', 'ARM_B']
    is_valid, diagnostics = validate_controls(probe_battery, trials, arms, strict_mode=False)

    assert is_valid is False
    assert len(diagnostics['sample_failed_responses']['control-01']['ARM_A']) == 3, "Should collect first 3 failures"
    assert diagnostics['sample_failed_responses']['control-01']['ARM_A'][0] == 'I do not know'
    print("✓ Test 6 PASSED: Failed responses collected for diagnostics (first 3)")


if __name__ == '__main__':
    print("Running control-gate unit tests...\n")
    test_control_gate_passes_when_controls_valid()
    test_control_gate_fails_when_controls_missing()
    test_control_gate_case_insensitive()
    test_control_gate_strict_mode()
    test_control_gate_no_controls_backward_compat()
    test_control_gate_collects_failures()
    print("\n✓ All 6 tests PASSED")
