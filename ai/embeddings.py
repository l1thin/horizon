# Horizon - embeddings.py - owned by Dev 3 (AI + Infra)
#
# Skill gap computation using vector embeddings.
# Compares candidate skill vectors against job-requirement vectors to surface gaps.

from __future__ import annotations

import math
from typing import Any


# ---------------------------------------------------------------------------
# Vector utilities
# ---------------------------------------------------------------------------


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must be the same length")

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# Embedding generation (placeholder — plug in a real model / API)
# ---------------------------------------------------------------------------


def get_embedding(text: str) -> list[float]:
    """Return an embedding vector for the given text.

    TODO: Replace this stub with a real embedding provider
    (e.g. OpenAI text-embedding-3-small, Cohere embed-v3, or a local model).
    """
    # Placeholder: deterministic hash-based fake embedding for dev/testing.
    import hashlib

    digest = hashlib.sha256(text.encode()).hexdigest()
    # Produce a 128-dim pseudo-vector from the hash
    vec = [int(digest[i : i + 2], 16) / 255.0 for i in range(0, min(len(digest), 256), 2)]
    return vec


# ---------------------------------------------------------------------------
# Skill gap analysis
# ---------------------------------------------------------------------------


def compute_skill_gap_vectors(
    candidate_skills: list[str],
    required_skills: list[str],
) -> list[dict[str, Any]]:
    """Compare candidate skills against required skills via embeddings.

    Returns a list of dicts:
        { required_skill, best_match, similarity, gap_score }

    ``gap_score`` is ``1 - similarity``; higher means larger gap.
    """
    candidate_vecs = [(skill, get_embedding(skill)) for skill in candidate_skills]
    results: list[dict[str, Any]] = []

    for req_skill in required_skills:
        req_vec = get_embedding(req_skill)

        best_match = ""
        best_sim = -1.0

        for cand_skill, cand_vec in candidate_vecs:
            sim = cosine_similarity(req_vec, cand_vec)
            if sim > best_sim:
                best_sim = sim
                best_match = cand_skill

        results.append(
            {
                "required_skill": req_skill,
                "best_match": best_match,
                "similarity": round(best_sim, 4),
                "gap_score": round(1.0 - best_sim, 4),
            }
        )

    return results


def rank_gaps(
    gap_results: list[dict[str, Any]],
    threshold: float = 0.5,
) -> list[dict[str, Any]]:
    """Return gaps sorted by severity, filtered to those above *threshold*.

    Higher ``gap_score`` → larger gap → higher priority.
    """
    significant = [g for g in gap_results if g["gap_score"] >= threshold]
    return sorted(significant, key=lambda g: g["gap_score"], reverse=True)
