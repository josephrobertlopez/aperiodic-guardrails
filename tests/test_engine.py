"""Tests for the zero-knowledge executor engine."""
import json
import base64
import tempfile
import os
from aperiodic_guardrails.engine import decode_config, check_termination

def test_decode_config():
    config = {"medium": "graph_solver", "params": {"target": "N30"}, "max_iterations": 1}
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.b64', delete=False) as f:
        f.write(base64.b64encode(json.dumps(config).encode()))
        path = f.name
    try:
        decoded = decode_config(path)
        assert decoded["medium"] == "graph_solver"
        assert decoded["params"]["target"] == "N30"
    finally:
        os.unlink(path)

def test_check_termination_count():
    config = {"termination": {"type": "count", "value": 3}}
    assert not check_termination(None, 1, config)
    assert not check_termination(None, 2, config)
    assert check_termination(None, 3, config)

def test_check_termination_has_results():
    config = {"termination": {"type": "has_results"}}
    assert not check_termination(None, 1, config)
    assert not check_termination([], 1, config)
    assert check_termination(["result"], 1, config)
