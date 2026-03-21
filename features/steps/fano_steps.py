"""Step definitions for theorem_fano.feature."""
from behave import given, when, then
import math


@given('{pct:d}% of probability mass falls in mixed fibers')
def step_mixed_mass(context, pct):
    """Store the fraction of probability mass in mixed fibers."""
    context.mixed_mass = pct / 100.0


@given('mixed fibers have 50/50 safe/unsafe split')
def step_fifty_fifty(context):
    """
    Set the entropy within mixed fibers to H(0.5) = 1 bit.
    
    This means that within the mixed fibers, the conditional distribution
    is uniform over safe and unsafe labels.
    """
    context.fiber_entropy = 1.0  # H(0.5) = -0.5*log2(0.5) - 0.5*log2(0.5) = 1 bit


@when('I compute H(G(R) | U(R))')
def step_compute_conditional_entropy(context):
    """
    Compute the conditional entropy H(G(R) | U(R)).
    
    From the paper:
    H(G(R) | U(R)) = Σ_r P(U(r)) H(G(r) | U(r))
    
    Since G(r) = U(r) for non-mixed fibers (entropy 0) and entropy = 1.0
    for mixed fibers:
    H(G(R) | U(R)) = mixed_mass * fiber_entropy
    """
    context.conditional_entropy = context.mixed_mass * context.fiber_entropy


@then('the conditional entropy should be approximately {bits:f} bits')
def step_check_entropy(context, bits):
    """Assert that the conditional entropy matches the expected value."""
    tolerance = 0.05
    assert abs(context.conditional_entropy - bits) < tolerance, \
        f"Expected conditional entropy ~{bits} bits, got {context.conditional_entropy:.4f}"


@then('h_inverse({x:f}) should be approximately {expected:f}')
def step_check_h_inverse(context, x, expected):
    """
    Compute h^{-1}(x) and assert it matches the expected value.
    
    h is the binary entropy function: h(p) = -p*log2(p) - (1-p)*log2(1-p)
    h^{-1} is its inverse on [0, 0.5]. For x in [0, 1], h^{-1}(x) is the
    value p such that h(p) = x.
    
    We compute this via binary search on the interval [0, 0.5].
    """
    def h(p):
        """Binary entropy function."""
        if p <= 0 or p >= 1:
            return 0.0
        return -p * math.log2(p) - (1 - p) * math.log2(1 - p)
    
    # Binary search for h^{-1}(x)
    lo, hi = 0.0, 0.5
    for _ in range(100):  # 100 iterations gives precision ~2^-100
        mid = (lo + hi) / 2.0
        if h(mid) < x:
            lo = mid
        else:
            hi = mid
    
    context.h_inv = (lo + hi) / 2.0
    
    tolerance = 0.01
    assert abs(context.h_inv - expected) < tolerance, \
        f"h^-1({x}) = {context.h_inv:.4f}, expected ~{expected:.4f}"


@then('the error floor should be approximately {pct:d}%')
def step_check_error_floor(context, pct):
    """
    Assert that the error floor (h^{-1} of the conditional entropy) matches.
    
    From Fano bound: any lifted guardrail has error >= h^{-1}(H(G(R)|U(R)))
    """
    expected = pct / 100.0
    tolerance = 0.02
    assert abs(context.h_inv - expected) < tolerance, \
        f"Error floor {context.h_inv:.3f}, expected ~{expected:.3f} ({pct}%)"
