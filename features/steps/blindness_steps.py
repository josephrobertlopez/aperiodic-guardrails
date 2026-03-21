"""Step definitions for theorem_blindness.feature."""
from behave import given, when, then
import re


@given('the blocked payload "{payload}"')
def step_given_payload(context, payload):
    """Store the payload to be encoded."""
    context.payload = payload


@when('I encode the payload with MOD_{p:d} interleaving using filler "{filler}"')
def step_encode_mod_p(context, p, filler):
    """
    Encode the payload using MOD_p interleaving.
    
    For MOD_p interleaving with period p and filler string:
    - Take each character of the payload at positions 0, 1, 2, ...
    - After each payload character (except the last), insert p-1 filler characters
    - The filler is drawn cyclically from the filler string
    
    Example: payload="bomb", p=2, filler="x"
    - b (payload[0])
    - x (filler[0])
    - o (payload[1])
    - x (filler[0])
    - m (payload[2])
    - x (filler[0])
    - b (payload[3])
    Result: "bxoxmxb"
    
    Decoding: take every p-th character starting at 0: result[0::2] = "bomb"
    """
    payload = context.payload
    encoded_chars = []
    
    for i, ch in enumerate(payload):
        encoded_chars.append(ch)
        if i < len(payload) - 1:
            # Insert p-1 filler characters
            for j in range(p - 1):
                encoded_chars.append(filler[j % len(filler)])
    
    context.encoded = ''.join(encoded_chars)
    context.p = p
    context.filler = filler


@then('the regex should match the original payload')
def step_regex_matches_payload(context):
    """Assert that the regex pattern matches the original payload."""
    match = context.compiled.search(context.payload)
    assert match is not None, \
        f"Pattern '{context.pattern}' should match payload '{context.payload}'"


@then('the regex should not match the encoded string')
def step_regex_no_match_encoded(context):
    """Assert that the regex pattern does NOT match the encoded payload."""
    match = context.compiled.search(context.encoded)
    assert match is None, \
        f"Pattern '{context.pattern}' should NOT match encoded '{context.encoded}' " \
        f"(original: '{context.payload}')"


@then('decoding the encoded string with s[0::{p:d}] should recover the payload')
def step_decode_recovers(context, p):
    """
    Assert that decoding the encoded string with step p recovers the original payload.
    
    MOD_p interleaving places payload characters at positions 0, p, 2p, 3p, ...
    So decoding is simply: encoded[0::p]
    """
    decoded = context.encoded[0::p]
    assert decoded == context.payload, \
        f"Decoding '{context.encoded}' with [0::{p}] should recover '{context.payload}', " \
        f"got '{decoded}'"
