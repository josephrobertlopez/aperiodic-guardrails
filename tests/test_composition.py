"""
test_composition.py
--------------------
Empirically validates Proposition~\ref{prop:composition}:
  If L1 and L2 have aperiodic syntactic monoids, then L1 ∩ L2,
  L1 ∪ L2, and Σ* \ L1 also have aperiodic syntactic monoids.

Strategy for intersection: build the product DFA by running two
minimal DFAs in lockstep, then extract the monoid from the product
DFA directly (rather than approximating with a regex string).
Union uses the same product DFA with different accept-state logic.
Complement inverts the accept set of the original DFA.
"""
import sys
import pytest

sys.path.insert(0, '/home/joey/Documents/aperiodic-guardrails/src')

from aperiodic_guardrails.monoid.extractor import (
    builtin_path,
    try_greenery,
    compute_transition_monoid,
    check_aperiodic,
    extract_monoid,
)
from typing import Dict, Set, Tuple, List


# ---------------------------------------------------------------------------
# Helpers: product DFA construction for ∩ and ∪
# ---------------------------------------------------------------------------

def _get_dfa(pattern: str):
    """Return (num_states, transitions, start, accept, alphabet) for a pattern."""
    result = try_greenery(pattern)
    if result:
        return result
    return builtin_path(pattern)


def _product_dfa(
    dfa1: tuple,
    dfa2: tuple,
    mode: str,  # 'intersection' or 'union'
) -> Tuple[int, Dict[Tuple[int, str], int], int, Set[int], List[str]]:
    """
    Build the product DFA for L1 op L2 where op is intersection or union.
    Both DFAs must share the same alphabet; we restrict to the intersection
    of their alphabets so the product DFA is well-defined.
    """
    n1, t1, s1, a1, alpha1 = dfa1
    n2, t2, s2, a2, alpha2 = dfa2

    # Use the shared alphabet
    shared_alpha = sorted(set(alpha1) & set(alpha2))
    if not shared_alpha:
        raise ValueError("DFAs have disjoint alphabets; cannot build product DFA.")

    # States of product DFA: (q1, q2) pairs reachable from (s1, s2)
    from collections import deque

    start_pair = (s1, s2)
    state_map: Dict[Tuple[int, int], int] = {start_pair: 0}
    queue: deque = deque([start_pair])
    prod_trans: Dict[Tuple[int, str], int] = {}

    while queue:
        (q1, q2) = queue.popleft()
        pid = state_map[(q1, q2)]
        for sym in shared_alpha:
            nq1 = t1.get((q1, sym), q1)  # self-loop on missing = dead implied by minimization
            nq2 = t2.get((q2, sym), q2)
            pair = (nq1, nq2)
            if pair not in state_map:
                state_map[pair] = len(state_map)
                queue.append(pair)
            prod_trans[(pid, sym)] = state_map[pair]

    num_prod = len(state_map)
    prod_start = 0  # state_map[start_pair]

    if mode == 'intersection':
        prod_accept = {
            pid for (q1, q2), pid in state_map.items()
            if q1 in a1 and q2 in a2
        }
    elif mode == 'union':
        prod_accept = {
            pid for (q1, q2), pid in state_map.items()
            if q1 in a1 or q2 in a2
        }
    else:
        raise ValueError(f"Unknown mode: {mode!r}")

    return num_prod, prod_trans, prod_start, prod_accept, shared_alpha


def _complement_dfa(dfa: tuple) -> Tuple[int, Dict, int, Set, List]:
    """Invert the accept set (complement language)."""
    num_states, transitions, start, accept, alphabet = dfa
    all_states = set(range(num_states))
    return num_states, transitions, start, all_states - accept, alphabet


def _monoid_aperiodic_from_dfa(num_states, transitions, start, accept, alphabet):
    """Compute syntactic monoid and check aperiodicity directly from a DFA tuple."""
    elements, mult_table = compute_transition_monoid(
        num_states, transitions, start, alphabet
    )
    is_aperiodic, _ = check_aperiodic(elements, mult_table)
    return {
        'size': len(elements),
        'aperiodic': is_aperiodic,
    }


# ---------------------------------------------------------------------------
# 5 pairs of aperiodic patterns from the corpus
# Each pair is (label, pattern1, pattern2)
# All individually aperiodic (confirmed by corpus_expanded.csv)
# ---------------------------------------------------------------------------

APERIODIC_PAIRS = [
    (
        "SSN vs email",
        r"\d{3}-\d{2}-\d{4}",
        r"[A-Za-z0-9]+@[A-Za-z0-9]+\.[A-Za-z]{2,4}",
    ),
    (
        "GitHub PAT vs AWS key",
        r"ghp_[A-Za-z0-9]{5}",       # shortened for tractable DFA
        r"AKIA[0-9A-Z]{4}",           # shortened for tractable DFA
    ),
    (
        "IP address vs phone",
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",
    ),
    (
        "keyword 'password' vs keyword 'secret'",
        r"password",
        r"secret",
    ),
    (
        "ZIP code vs date fragment",
        r"\d{5}",
        r"[01]\d/[0-3]\d",
    ),
]


# ---------------------------------------------------------------------------
# Sanity-check: individual patterns are aperiodic
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label,p1,p2", APERIODIC_PAIRS)
def test_individual_patterns_are_aperiodic(label, p1, p2):
    """Both patterns in every pair must individually be aperiodic."""
    r1 = extract_monoid(p1)
    r2 = extract_monoid(p2)
    assert r1['aperiodic'], f"[{label}] Pattern 1 not aperiodic: {p1!r} groups={r1['groups']}"
    assert r2['aperiodic'], f"[{label}] Pattern 2 not aperiodic: {p2!r} groups={r2['groups']}"


# ---------------------------------------------------------------------------
# Core theorem tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label,p1,p2", APERIODIC_PAIRS)
def test_intersection_is_aperiodic(label, p1, p2):
    """
    Proposition: M(L1 ∩ L2) divides M(L1) × M(L2), so it is aperiodic.
    We verify by building the product DFA directly and extracting its monoid.
    """
    dfa1 = _get_dfa(p1)
    dfa2 = _get_dfa(p2)
    prod = _product_dfa(dfa1, dfa2, mode='intersection')
    result = _monoid_aperiodic_from_dfa(*prod)
    assert result['aperiodic'], (
        f"[{label}] Intersection not aperiodic! "
        f"monoid_size={result['size']}"
    )


@pytest.mark.parametrize("label,p1,p2", APERIODIC_PAIRS)
def test_union_is_aperiodic(label, p1, p2):
    """
    Proposition: M(L1 ∪ L2) divides M(L1) × M(L2), so it is aperiodic.
    """
    dfa1 = _get_dfa(p1)
    dfa2 = _get_dfa(p2)
    prod = _product_dfa(dfa1, dfa2, mode='union')
    result = _monoid_aperiodic_from_dfa(*prod)
    assert result['aperiodic'], (
        f"[{label}] Union not aperiodic! "
        f"monoid_size={result['size']}"
    )


@pytest.mark.parametrize("label,p1,p2", APERIODIC_PAIRS)
def test_complement_is_aperiodic(label, p1, p2):
    """
    Proposition: M(Σ* \\ L1) ≅ M(L1), so complement is aperiodic iff L1 is.
    We verify complement of p1 and complement of p2 separately.
    """
    for pat, name in [(p1, "p1"), (p2, "p2")]:
        dfa = _get_dfa(pat)
        comp = _complement_dfa(dfa)
        result = _monoid_aperiodic_from_dfa(*comp)
        assert result['aperiodic'], (
            f"[{label}] Complement of {name} not aperiodic! "
            f"monoid_size={result['size']}"
        )


# ---------------------------------------------------------------------------
# Monoid size sanity: product monoid divides |M(L1)| * |M(L2)|
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label,p1,p2", APERIODIC_PAIRS)
def test_product_monoid_size_bound(label, p1, p2):
    """
    The syntactic monoid of L1 ∩ L2 divides M(L1) × M(L2),
    so |M(L1 ∩ L2)| ≤ |M(L1)| * |M(L2)|.
    """
    r1 = extract_monoid(p1)
    r2 = extract_monoid(p2)
    upper_bound = r1['size'] * r2['size']

    dfa1 = _get_dfa(p1)
    dfa2 = _get_dfa(p2)
    prod = _product_dfa(dfa1, dfa2, mode='intersection')
    result = _monoid_aperiodic_from_dfa(*prod)

    assert result['size'] <= upper_bound, (
        f"[{label}] Product monoid size {result['size']} exceeds "
        f"|M(L1)|*|M(L2)| = {r1['size']}*{r2['size']} = {upper_bound}"
    )
