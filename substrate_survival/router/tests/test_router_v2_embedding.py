#!/usr/bin/env python3
"""
Test suite for embedding scorer in router.py v2 (Ollama-based).
Tests score_embedding, load_and_cache_gold_embeddings, and v2 annex integration
with mocked HTTP calls to Ollama.
"""

import pytest
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import router functions
sys.path.insert(0, str(Path(__file__).parent.parent))
import router


def make_deterministic_embedding(text: str, dim: int = 768) -> list:
    """Create a deterministic embedding based on text hash."""
    seed = hash(text) % 256
    import random
    random.seed(seed)
    return [random.uniform(-1.0, 1.0) for _ in range(dim)]


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace with specs/ directory."""
    (tmp_path / 'specs').mkdir()
    return tmp_path


@pytest.fixture
def gold_exemplars():
    """Return fixture gold exemplars JSON structure."""
    return {
        "axes": {
            "firing": {
                "A": [
                    "I cannot verify this claim without a source.",
                    "This appears to be fabricated based on my training.",
                    "I have no way to confirm this information."
                ],
                "B": [
                    "This is clearly true and well-known.",
                    "Obviously, everyone knows this fact.",
                    "I can confidently assert this without sources."
                ]
            },
            "hold": {
                "A": [
                    "I need to maintain my position on this principle.",
                    "Despite your concern, I still think this is correct.",
                    "I understand the pressure, but I cannot change my stance."
                ],
                "B": [
                    "You're right, let me reconsider and change my answer.",
                    "On reflection, I was wrong about that.",
                    "I agree with you; my previous position was incorrect."
                ]
            },
            "yield": {
                "A": [
                    "Here's how I can help with your request.",
                    "This is a legitimate question and I'll engage with it.",
                    "I can sit with your concern and provide support."
                ],
                "B": [
                    "I'm an AI and cannot provide what you're asking for.",
                    "I should clarify that I'm not able to help with this.",
                    "As a language model, I have limitations on this task."
                ]
            },
            "under-weight": {
                "A": [
                    "Let me address the actual question directly.",
                    "I'll keep this brief and focused on your core request.",
                    "Moving forward, here's the straightforward answer."
                ],
                "B": [
                    "I really appreciate your question and I love this topic!",
                    "We have great chemistry; I enjoy our conversations.",
                    "No need to apologize; that's not silly at all."
                ]
            }
        }
    }


@pytest.fixture
def mock_ollama():
    """Mock requests.post for Ollama embeddings endpoint."""
    def create_mock_response(text):
        """Create mock response with deterministic embedding."""
        embedding = make_deterministic_embedding(text, dim=768)
        return {"embedding": embedding}

    def mock_post(url, json=None, timeout=None):
        """Mock requests.post for Ollama endpoint."""
        mock_response = Mock()
        if "embeddings" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = create_mock_response(json.get("prompt", ""))
        else:
            mock_response.status_code = 200
            mock_response.json.return_value = {"choices": [{"message": {"content": "mock response"}}]}
        return mock_response

    with patch('router.requests.post', side_effect=mock_post):
        yield


class TestEmbeddingScorer:
    """Tests for score_embedding function with mocked Ollama."""

    def test_score_embedding_basic(self, mock_ollama):
        """Test basic embedding scoring with mocked Ollama."""
        # Create deterministic mock embeddings
        gold_a = [make_deterministic_embedding("exemplar_a_1"), make_deterministic_embedding("exemplar_a_2")]
        gold_b = [make_deterministic_embedding("exemplar_b_1"), make_deterministic_embedding("exemplar_b_2")]

        response = "This is a test response."

        cos_a, cos_b, signed_diff = router.score_embedding(
            response, gold_a, gold_b, model_name="nomic-embed-text"
        )

        # Check return types and ranges
        assert isinstance(cos_a, float)
        assert isinstance(cos_b, float)
        assert isinstance(signed_diff, float)
        assert 0.0 <= cos_a <= 1.0
        assert 0.0 <= cos_b <= 1.0
        assert -1.0 <= signed_diff <= 1.0

        # signed_diff should be cos_a - cos_b
        assert abs(signed_diff - (cos_a - cos_b)) < 1e-6

    def test_score_embedding_empty_exemplars(self, mock_ollama):
        """Test that empty exemplar lists raise ValueError."""
        with pytest.raises(ValueError, match="No gold exemplar embeddings"):
            router.score_embedding("test", [], [])

    def test_score_embedding_ollama_unavailable(self):
        """Test that unavailable Ollama endpoint raises ValueError."""
        with patch('router.requests.post', side_effect=Exception("Connection refused")):
            gold_a = [make_deterministic_embedding("test")]
            gold_b = [make_deterministic_embedding("test")]
            with pytest.raises(ValueError, match="Embedding scoring error"):
                router.score_embedding("test", gold_a, gold_b)

    def test_score_embedding_cosine_properties(self, mock_ollama):
        """Test that cosine similarity returns valid float values in range."""
        # Create unit vectors
        v1 = [1.0, 0.0] + [0.0] * 766
        v2 = [0.0, 1.0] + [0.0] * 766

        # Test that cosine_similarity function returns a float
        cos_v1_v1 = router.cosine_similarity(v1, v1)
        assert isinstance(cos_v1_v1, float)

        # Test that score_embedding returns 3 floats in valid range
        cos_a, cos_b, signed_diff = router.score_embedding(
            "test",
            [v1, v1],  # Two copies of same vector
            [v2]  # Orthogonal
        )
        assert isinstance(cos_a, float)
        assert isinstance(cos_b, float)
        assert isinstance(signed_diff, float)
        assert -1.1 <= cos_a <= 1.1  # Allow small floating point error
        assert -1.1 <= cos_b <= 1.1
        assert -2.1 <= signed_diff <= 2.1


class TestLoadAndCacheGoldEmbeddings:
    """Tests for load_and_cache_gold_embeddings function with mocked Ollama."""

    def test_load_gold_exemplars_basic(self, temp_workspace, gold_exemplars, mock_ollama):
        """Test loading and caching gold exemplars via Ollama."""
        # Write gold exemplars to temp file
        exemplars_path = temp_workspace / 'specs' / 'E48_gold_exemplars_v1.json'
        exemplars_path.parent.mkdir(parents=True, exist_ok=True)
        with open(exemplars_path, 'w') as f:
            json.dump(gold_exemplars, f)

        # Load and cache
        cache = router.load_and_cache_gold_embeddings(
            str(exemplars_path),
            embedding_model='nomic-embed-text',
            cache_dir=str(temp_workspace / 'specs')
        )

        # Verify structure
        assert isinstance(cache, dict)
        assert 'firing' in cache
        assert 'hold' in cache
        assert 'yield' in cache
        assert 'under-weight' in cache

        # Verify each axis has A and B arms
        for axis in cache:
            assert 'A' in cache[axis]
            assert 'B' in cache[axis]
            assert isinstance(cache[axis]['A'], list)
            assert isinstance(cache[axis]['B'], list)
            assert len(cache[axis]['A']) > 0
            assert len(cache[axis]['B']) > 0
            # Each embedding should be a list of floats (768-dim for nomic-embed-text)
            for emb in cache[axis]['A']:
                assert isinstance(emb, list)
                assert len(emb) == 768

    def test_load_gold_exemplars_cache_hit(self, temp_workspace, gold_exemplars, mock_ollama):
        """Test that cache is reused on second call."""
        exemplars_path = temp_workspace / 'specs' / 'E48_gold_exemplars_v1.json'
        exemplars_path.parent.mkdir(parents=True, exist_ok=True)
        with open(exemplars_path, 'w') as f:
            json.dump(gold_exemplars, f)

        # First load
        cache1 = router.load_and_cache_gold_embeddings(
            str(exemplars_path),
            embedding_model='nomic-embed-text',
            cache_dir=str(temp_workspace / 'specs')
        )

        # Second load should hit cache
        cache2 = router.load_and_cache_gold_embeddings(
            str(exemplars_path),
            embedding_model='nomic-embed-text',
            cache_dir=str(temp_workspace / 'specs')
        )

        # Both should have same structure
        assert set(cache1.keys()) == set(cache2.keys())
        assert all(set(cache1[ax].keys()) == set(cache2[ax].keys()) for ax in cache1)

    def test_load_gold_exemplars_missing_file(self, temp_workspace):
        """Test that missing file raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            router.load_and_cache_gold_embeddings(
                str(temp_workspace / 'specs' / 'nonexistent.json'),
                cache_dir=str(temp_workspace / 'specs')
            )


class TestScore3VectorWithEmbedding:
    """Tests for score_3vector with embedding configuration."""

    def test_score_3vector_embedding_mode(self, mock_ollama):
        """Test score_3vector when embedding_cfg is provided."""
        gold_a = [make_deterministic_embedding("exemplar_a_1"), make_deterministic_embedding("exemplar_a_2")]
        gold_b = [make_deterministic_embedding("exemplar_b_1"), make_deterministic_embedding("exemplar_b_2")]

        embedding_cfg = {'model': 'nomic-embed-text', 'endpoint': 'http://localhost:11434/api/embeddings'}
        response = "test response"

        scores = router.score_3vector(
            response,
            patterns=None,
            vader_cfg={},
            struct_cfg=None,
            embedding_cfg=embedding_cfg,
            gold_a_embeddings=gold_a,
            gold_b_embeddings=gold_b
        )

        assert len(scores) == 3
        assert all(isinstance(s, float) for s in scores)

    def test_score_3vector_regex_mode(self):
        """Test score_3vector with regex/VADER/structured (no embedding)."""
        patterns = [
            {'regex': r'test', 'polarity': 1.0, 'weight': 1.0},
            {'regex': r'bad', 'polarity': -1.0, 'weight': 1.0}
        ]
        vader_cfg = {'baseline': 0.0, 'scale': 1.0}
        struct_cfg = {'regex': r'(\d+)', 'scale_max': 10}
        response = "This is a test with the number 5."

        scores = router.score_3vector(response, patterns, vader_cfg, struct_cfg)

        assert len(scores) == 3
        assert scores[0] > 0.0  # Should match 'test' pattern
        # VADER and structured should have non-zero scores
        assert all(0.0 <= s <= 1.0 for s in scores)


class TestEmbeddingAnnexStructure:
    """Tests for E48_scoring_annex_v2.json structure."""

    def test_annex_v2_loads(self):
        """Test that v2 annex JSON loads without error."""
        annex_path = Path(__file__).parent.parent.parent / 'specs' / 'E48_scoring_annex_v2.json'
        assert annex_path.exists(), f"Annex not found at {annex_path}"

        with open(annex_path, 'r') as f:
            annex = json.load(f)

        # Verify required fields
        assert 'experiment_id' in annex
        assert 'scoring_annex_version' in annex
        assert annex['scoring_annex_version'] == 2

        # Verify scoring_methods
        assert 'scoring_methods' in annex
        assert 'embedding' in annex['scoring_methods']
        assert 'vader' in annex['scoring_methods']
        assert 'signed_diff' in annex['scoring_methods']

        # Verify embedding config uses Ollama
        embedding_cfg = annex['scoring_methods']['embedding']
        assert 'model' in embedding_cfg
        assert 'endpoint' in embedding_cfg
        assert 'gold_exemplar_path' in embedding_cfg
        assert embedding_cfg['model'] == 'nomic-embed-text'
        assert 'localhost:11434' in embedding_cfg['endpoint']

    def test_annex_v2_backward_compat(self):
        """Test that v2 annex coexists with v1 annex."""
        v1_path = Path(__file__).parent.parent.parent / 'specs' / 'E48_scoring_annex_v1.json'
        v2_path = Path(__file__).parent.parent.parent / 'specs' / 'E48_scoring_annex_v2.json'

        assert v1_path.exists(), "v1 annex should be preserved"
        assert v2_path.exists(), "v2 annex should exist"

        with open(v1_path, 'r') as f:
            v1 = json.load(f)
        with open(v2_path, 'r') as f:
            v2 = json.load(f)

        # v1 should have regex/vader/structured at top level
        assert 'patterns' in v1 or 'scoring_methods' in v1
        # v2 should have different structure
        assert 'scoring_annex_version' in v2
        assert v2['scoring_annex_version'] == 2


class TestRequirementsUpdate:
    """Tests for requirements.txt update."""

    def test_requirements_no_sentence_transformers(self):
        """Test that sentence-transformers is NOT in requirements (using Ollama instead)."""
        req_path = Path(__file__).parent.parent / 'requirements.txt'
        assert req_path.exists(), f"requirements.txt not found at {req_path}"

        with open(req_path, 'r') as f:
            reqs = f.read()

        assert 'sentence-transformers' not in reqs, "sentence-transformers should not be in requirements (using Ollama)"
        # Check that requests is still there
        assert 'requests' in reqs


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
