"""Tests for the syntactic monoid extractor."""
import pytest

def test_import():
    from aperiodic_guardrails.monoid import extractor
    assert hasattr(extractor, 'main')

def test_literal_pattern_aperiodic():
    """A literal substring pattern should have an aperiodic monoid."""
    # This test will be filled once extractor exports are finalized
    pass

def test_mod2_bypass():
    """MOD_2 interleaving should evade any aperiodic pattern."""
    import re
    pattern = re.compile(r"bomb")
    payload = "bomb"
    encoded = "".join(c + "x" for c in payload)[:-1]  # bxoxmxb
    assert pattern.search(payload) is not None
    assert pattern.search(encoded) is None
    assert encoded[0::2] == payload
