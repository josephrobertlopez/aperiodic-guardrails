"""pre_reg_lock minimal reference. ~30 lines.

Three functions: write, attach, audit. The mtime IS the audit anchor.
"""
from __future__ import annotations

import json
import os
from typing import Any


def write_prereg(spec_dict: dict[str, Any], prereg_path: str) -> float:
    with open(prereg_path, "w") as f:
        json.dump(spec_dict, f, indent=2)
    return os.path.getmtime(prereg_path)


def attach_prereg_mtime(
    results_dict: dict[str, Any],
    prereg_path: str,
) -> dict[str, Any]:
    enriched = dict(results_dict)
    enriched["pre_reg_path"] = prereg_path
    enriched["pre_reg_mtime"] = os.path.getmtime(prereg_path)
    return enriched


def audit_prereg_ordering(
    results_dict: dict[str, Any],
    results_path: str,
) -> bool:
    if "pre_reg_mtime" not in results_dict:
        raise ValueError("missing pre_reg_mtime; cannot audit ordering")
    prereg_mtime = results_dict["pre_reg_mtime"]
    results_mtime = os.path.getmtime(results_path)
    return prereg_mtime < results_mtime
