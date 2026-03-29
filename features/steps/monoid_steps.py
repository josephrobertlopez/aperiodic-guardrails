"""Step definitions for theorem_aperiodicity.feature."""
from behave import given, when, then
import re


@given('the regex pattern "{pattern}"')
def step_given_pattern(context, pattern):
    """Parse and store the regex pattern."""
    context.pattern = pattern
    try:
        context.compiled = re.compile(pattern)
    except re.error as e:
        context.compile_error = str(e)
        context.compiled = None


@when('I compute the syntactic monoid via DFA minimization')
def step_compute_monoid(context):
    """Compute the syntactic monoid from the DFA of the regex pattern."""
    if context.compiled is None:
        context.monoid_size = -1
        context.is_aperiodic = None
        context.groups = []
        return

    from aperiodic_guardrails.monoid.extractor import extract_monoid
    try:
        result = extract_monoid(context.pattern)
        context.monoid_size = result.get('size', 0)
        context.is_aperiodic = result.get('aperiodic', None)
        context.groups = result.get('groups', [])
    except Exception as e:
        context.monoid_error = str(e)
        context.monoid_size = -1
        context.is_aperiodic = None
        context.groups = []


@then('the monoid should be aperiodic')
def step_monoid_aperiodic(context):
    """Assert that the computed monoid is aperiodic."""
    assert context.is_aperiodic is True, \
        f"Expected aperiodic monoid for pattern '{context.pattern}', got {context.is_aperiodic}"


@then('the monoid should not be aperiodic')
def step_monoid_not_aperiodic(context):
    """Assert that the computed monoid is not aperiodic (i.e., periodic)."""
    assert context.is_aperiodic is False, \
        f"Expected non-aperiodic (periodic) monoid for pattern '{context.pattern}', got {context.is_aperiodic}"


@then('the monoid size should be {size:d}')
def step_monoid_size(context, size):
    """Assert that the monoid has the expected size."""
    assert context.monoid_size == size, \
        f"Expected monoid size {size}, got {context.monoid_size} (pattern: '{context.pattern}')"


@then('the monoid should contain group Z/{p:d}Z')
def step_monoid_contains_group(context, p):
    """Assert that the monoid contains a cyclic group of order p."""
    assert any(g == p for g in context.groups), \
        f"Expected Z/{p}Z in group components {context.groups}, pattern: '{context.pattern}'"
