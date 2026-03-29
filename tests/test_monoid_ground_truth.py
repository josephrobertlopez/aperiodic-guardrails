"""
Ground-truth monoid tests for patterns with known formal-language-theory structure.

Each entry in GROUND_TRUTH is (pattern, expected_aperiodic, expected_group_orders).
expected_group_orders is None for aperiodic languages (no non-trivial cyclic subgroups),
or a list of the expected group orders for periodic ones.
"""

import pytest
from aperiodic_guardrails.monoid.extractor import extract_monoid

# (pattern, aperiodic, group_orders_or_None)
GROUND_TRUTH = [
    ("a*b*",            True,  None),    # 4-element aperiodic monoid
    ("(ab)*",           True,  None),    # 6-element B₂ (Brandt monoid, aperiodic)
    ("(aa)*",           False, [2]),     # Z/2Z — NOT aperiodic
    ("(aaa)*",          False, [3]),     # Z/3Z — NOT aperiodic
    ("a*",              True,  None),    # 3-element aperiodic
    ("(a|b)*a(a|b)",    True,  None),    # aperiodic
    ("(a|b)*aba(a|b)*", True,  None),    # aperiodic
    ("a(a|b)*b",        True,  None),    # aperiodic
    ("(ab|ba)*",        True,  None),    # aperiodic
    ("[ab]*a[ab][ab]",  True,  None),    # aperiodic
]


@pytest.mark.parametrize("pattern,expected_aperiodic,expected_groups", GROUND_TRUTH,
                         ids=[t[0] for t in GROUND_TRUTH])
def test_aperiodicity(pattern, expected_aperiodic, expected_groups):
    result = extract_monoid(pattern)
    assert result['aperiodic'] == expected_aperiodic, (
        f"Pattern {pattern!r}: expected aperiodic={expected_aperiodic}, "
        f"got aperiodic={result['aperiodic']} (monoid size={result['size']}, "
        f"groups={result['groups']})"
    )


@pytest.mark.parametrize("pattern,expected_aperiodic,expected_groups",
                         [t for t in GROUND_TRUTH if t[1] is False],
                         ids=[t[0] for t in GROUND_TRUTH if t[1] is False])
def test_group_orders(pattern, expected_aperiodic, expected_groups):
    """For periodic languages, verify the reported cyclic group orders match theory."""
    result = extract_monoid(pattern)
    actual_groups = result['groups']
    for order in expected_groups:
        assert order in actual_groups, (
            f"Pattern {pattern!r}: expected group order {order} in {actual_groups}"
        )
