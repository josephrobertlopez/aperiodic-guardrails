"""qwen_only_hook — write-time discipline scaffolding.

Concept: When a claim-shipping markdown artifact mentions a qwen model, the
artifact must EITHER (a) co-cite a cross-family model on the same claim, OR
(b) carry an explicit single-family caveat. Otherwise the write is blocked.

This is the mechanical encoding of the three-for-three cross-family pattern
(E42, E46, E48 each flipped under cross-family test) as a write-time
default-discount, not an aspirational discipline.

Real source: ~/.claude/hooks/qwen-only-check-pretool.sh

You implement two predicates:
    1. detect_qwen_reference(content)  -> bool
    2. detect_cross_family_or_caveat(content) -> bool

And one composition:
    3. classify_qwen_only(content) -> "ALLOW" | "BLOCK"
"""
from __future__ import annotations


def detect_qwen_reference(content: str) -> bool:
    """Return True if `content` mentions any qwen model variant.

    Concept: model-family detection via regex over markdown body.
    Should match: 'qwen', 'qwen2.5-coder', 'Qwen2.5-32B-Instruct-AWQ',
    'qwen2.5-coder:14b', and similar variants regardless of case.
    """
    raise NotImplementedError("concept: model-family regex detection")


def detect_cross_family_or_caveat(content: str) -> bool:
    """Return True if `content` either co-cites a non-qwen model family
    OR contains an explicit single-family caveat phrase.

    Concept: lift-condition predicate — the rule that REMOVES the default block.
    Cross-family token examples: sonnet, llama, gpt, claude-opus, gemini,
    mistral, deepseek, etc.
    Caveat phrase examples: 'qwen-only', 'qwen-specific', 'single-family',
    'cross-family not confirmed', 'generalization caveat'.
    """
    raise NotImplementedError("concept: lift-condition predicate")


def classify_qwen_only(content: str) -> str:
    """Compose the two predicates into a write-time verdict.

    Concept: default-discount composition. If qwen is referenced AND no
    lift-condition fires, return 'BLOCK'. Otherwise 'ALLOW'.

    Returns: 'ALLOW' or 'BLOCK'.
    """
    raise NotImplementedError("concept: default-discount composition")
