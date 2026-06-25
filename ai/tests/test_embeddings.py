# Horizon - test_embeddings.py - owned by Dev 3 (AI + Infra)
#
# Tests for ai/embeddings.py — vector-based skill gap computation.

from __future__ import annotations

import math

import pytest

from ai.embeddings import (
    compute_skill_gap_vectors,
    cosine_similarity,
    get_embedding,
    rank_gaps,
)


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------


def test_cosine_identical_vectors():
    """Identical vectors should have similarity ≈ 1.0."""
    vec = [1.0, 2.0, 3.0]
    assert math.isclose(cosine_similarity(vec, vec), 1.0, rel_tol=1e-9)


def test_cosine_orthogonal_vectors():
    """Orthogonal vectors should have similarity ≈ 0.0."""
    assert math.isclose(
        cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0, rel_tol=1e-9
    )


def test_cosine_opposite_vectors():
    """Opposite vectors should have similarity ≈ -1.0."""
    assert math.isclose(
        cosine_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0, rel_tol=1e-9
    )


def test_cosine_mismatched_lengths():
    """Vectors of different lengths should raise ValueError."""
    with pytest.raises(ValueError):
        cosine_similarity([1.0, 2.0], [1.0])


def test_cosine_zero_vector():
    """A zero vector should return 0.0 similarity."""
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


# ---------------------------------------------------------------------------
# get_embedding
# ---------------------------------------------------------------------------


def test_get_embedding_returns_list():
    """get_embedding should return a list of floats."""
    vec = get_embedding("Python")
    assert isinstance(vec, list)
    assert all(isinstance(v, float) for v in vec)


def test_get_embedding_deterministic():
    """Same input should produce the same embedding (placeholder is hash-based)."""
    assert get_embedding("Python") == get_embedding("Python")


def test_get_embedding_different_inputs():
    """Different inputs should produce different embeddings."""
    assert get_embedding("Python") != get_embedding("Java")


# ---------------------------------------------------------------------------
# compute_skill_gap_vectors
# ---------------------------------------------------------------------------


def test_compute_skill_gap_vectors_structure():
    """Each result should have the expected keys."""
    results = compute_skill_gap_vectors(
        candidate_skills=["Python", "SQL"],
        required_skills=["Python", "TensorFlow"],
    )
    assert len(results) == 2
    for r in results:
        assert "required_skill" in r
        assert "best_match" in r
        assert "similarity" in r
        assert "gap_score" in r


def test_exact_match_has_high_similarity():
    """When a required skill is also a candidate skill, similarity should be 1.0."""
    results = compute_skill_gap_vectors(
        candidate_skills=["Python"],
        required_skills=["Python"],
    )
    assert math.isclose(results[0]["similarity"], 1.0, rel_tol=1e-4)
    assert math.isclose(results[0]["gap_score"], 0.0, abs_tol=1e-4)


# ---------------------------------------------------------------------------
# rank_gaps
# ---------------------------------------------------------------------------


def test_rank_gaps_filters_below_threshold():
    """Gaps below the threshold should be excluded."""
    gaps = [
        {"required_skill": "A", "best_match": "X", "similarity": 0.8, "gap_score": 0.2},
        {"required_skill": "B", "best_match": "Y", "similarity": 0.3, "gap_score": 0.7},
    ]
    ranked = rank_gaps(gaps, threshold=0.5)
    assert len(ranked) == 1
    assert ranked[0]["required_skill"] == "B"


def test_rank_gaps_sorted_descending():
    """Results should be sorted by gap_score descending."""
    gaps = [
        {"required_skill": "A", "best_match": "X", "similarity": 0.4, "gap_score": 0.6},
        {"required_skill": "B", "best_match": "Y", "similarity": 0.1, "gap_score": 0.9},
        {"required_skill": "C", "best_match": "Z", "similarity": 0.2, "gap_score": 0.8},
    ]
    ranked = rank_gaps(gaps, threshold=0.5)
    scores = [r["gap_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
