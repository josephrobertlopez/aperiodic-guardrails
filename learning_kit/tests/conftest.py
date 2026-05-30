"""Shared fixtures. Loads real-shaped JSON from learning_kit/fixtures/."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = KIT_ROOT / "fixtures"

# Make brownfield importable as `from brownfield.<module> import ...`
sys.path.insert(0, str(KIT_ROOT))


@pytest.fixture
def qwen_samples() -> list[dict]:
    with (FIXTURES / "qwen_only_samples.json").open() as f:
        return json.load(f)["samples"]


@pytest.fixture
def pre_reg_singularity() -> dict:
    with (FIXTURES / "pre_reg_singularity_T1.json").open() as f:
        return json.load(f)


@pytest.fixture
def override_log_path() -> Path:
    return FIXTURES / "rigor_gate_overrides_sample.log"


@pytest.fixture
def results_positive() -> dict:
    with (FIXTURES / "results_sample_positive_verdict.json").open() as f:
        return json.load(f)


@pytest.fixture
def results_label_mismatch() -> dict:
    with (FIXTURES / "results_sample_label_mismatch.json").open() as f:
        return json.load(f)


@pytest.fixture
def results_missing_prereg() -> dict:
    with (FIXTURES / "results_sample_missing_prereg.json").open() as f:
        return json.load(f)


@pytest.fixture
def retire_ledger() -> dict:
    with (FIXTURES / "retire_audit_e48_ledger.json").open() as f:
        return json.load(f)
