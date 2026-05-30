"""pre_reg_lock — anti-tuning scaffolding via filesystem mtime ordering.

Concept: a pre-registration is only credible if it was written BEFORE the
data it predicts. The mtime of the pre-reg JSON file, captured and stored
inside the results JSON, IS the audit proof. If pre_reg_mtime >= results_mtime,
the pre-reg may have been tuned to the data.

Real source: substrate_survival/specs/pre_registered/*.json pattern, where
every results JSON carries the pre-reg's path and mtime.

You implement:
    1. write_prereg(spec_dict, prereg_path) -> float (the captured mtime)
    2. attach_prereg_mtime(results_dict, prereg_path) -> dict
    3. audit_prereg_ordering(results_dict, results_path) -> bool
"""
from __future__ import annotations

from typing import Any


def write_prereg(spec_dict: dict[str, Any], prereg_path: str) -> float:
    """Write `spec_dict` as JSON to `prereg_path` and return its filesystem mtime.

    Concept: capturing the mtime AT write-time. The returned float is the
    audit anchor — store it alongside the spec so it can be verified later.
    """
    raise NotImplementedError("concept: write-and-capture-mtime")


def attach_prereg_mtime(
    results_dict: dict[str, Any],
    prereg_path: str,
) -> dict[str, Any]:
    """Return a copy of `results_dict` with the pre-reg path AND mtime attached.

    Concept: provenance attachment. The result MUST carry the pre-reg's
    identity (path) and its mtime (the audit anchor) inside the JSON itself,
    not in a sidecar. Add keys: 'pre_reg_path' and 'pre_reg_mtime'.
    """
    raise NotImplementedError("concept: provenance attachment")


def audit_prereg_ordering(
    results_dict: dict[str, Any],
    results_path: str,
) -> bool:
    """Verify pre-reg was written BEFORE results.

    Concept: temporal ordering as anti-tuning proof. Return True iff
    pre_reg_mtime (from results_dict) is strictly less than the mtime of
    `results_path`. If either is missing, raise ValueError — fail-closed on
    missing provenance.
    """
    raise NotImplementedError("concept: anti-tuning temporal-ordering audit")
