"""Tests for qwen_only_hook — the easiest concept. Pure-text regex predicates.

Start here. If you can turn these 4 green, you understand default-discount
write-time hooks.

Reference: references/minimal_impl/qwen_only_hook_minimal.py
           references/gnosis_impl/qwen_only_check_pretool.sh (the real one)
"""
from __future__ import annotations

from brownfield.qwen_only_hook import (
    classify_qwen_only,
    detect_cross_family_or_caveat,
    detect_qwen_reference,
)


def test_detects_qwen_in_lowercase(qwen_samples):
    """concept: model-family detection must match qwen across case + variants."""
    naked = next(s for s in qwen_samples if s["id"] == "block_naked_qwen")
    assert detect_qwen_reference(naked["content"]) is True


def test_detects_qwen_variant_naming(qwen_samples):
    """concept: model-family detection must catch 'Qwen2.5-32B-Instruct-AWQ' too."""
    variant = next(s for s in qwen_samples if s["id"] == "block_qwen_variant_naming")
    assert detect_qwen_reference(variant["content"]) is True


def test_caveat_lifts_block(qwen_samples):
    """concept: lift-condition — explicit 'qwen-only' marker allows the write."""
    caveat = next(s for s in qwen_samples if s["id"] == "allow_qwen_with_caveat")
    assert detect_cross_family_or_caveat(caveat["content"]) is True
    assert classify_qwen_only(caveat["content"]) == "ALLOW"


def test_full_classification_matches_expected(qwen_samples):
    """concept: default-discount composition — all 6 real-shaped samples classify correctly.

    This is the integration test. Each sample has an 'expected' verdict per the
    three-for-three rule (encoded in ~/.claude/hooks/qwen-only-check-pretool.sh).
    """
    for sample in qwen_samples:
        got = classify_qwen_only(sample["content"])
        assert got == sample["expected"], (
            f"{sample['id']}: expected {sample['expected']}, got {got}"
        )
