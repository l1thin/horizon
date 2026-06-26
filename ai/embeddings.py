# ai/embeddings.py
from __future__ import annotations

import math
from typing import Any


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


async def get_embedding(text: str) -> list[float]:
    """Return an embedding vector for the given text."""
    import os

    provider = os.environ.get("VOICE_PROVIDER", "openai").lower()

    if provider == "gemini":
        from google import genai

        # Instantiate the modern async Client
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY")).aio

        response = await client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )

        if response.embeddings and response.embeddings[0].values:
            return response.embeddings[0].values
        else:
            raise ValueError(f"Couldn't get Embeddings for provider: {provider}")
    else:
        import openai

        client = openai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = await client.embeddings.create(
            input=text, model="text-embedding-3-small"
        )
        return response.data[0].embedding


async def compute_skill_gap_vectors(
    candidate_skills: list[str],
    required_skills: list[str],
) -> list[dict[str, Any]]:
    """Compare candidate skills against required skills via embeddings.

    Returns a list of dicts:
        { required_skill, best_match, similarity, gap_score }

    ``gap_score`` is ``1 - similarity``; higher means larger gap.
    """
    import asyncio

    # Return early if candidate didn't demonstrate any skills to compare against
    if not candidate_skills:
        return [
            {
                "required_skill": req,
                "best_match": "None",
                "similarity": 0.0,
                "gap_score": 1.0,
            }
            for req in required_skills
        ]

    # Fetch all candidate embeddings concurrently
    cand_tasks = [get_embedding(skill) for skill in candidate_skills]
    cand_embs = await asyncio.gather(*cand_tasks)
    candidate_vecs = list(zip(candidate_skills, cand_embs))

    # Fetch all required embeddings concurrently
    req_tasks = [get_embedding(skill) for skill in required_skills]
    req_embs = await asyncio.gather(*req_tasks)

    results: list[dict[str, Any]] = []

    for req_skill, req_vec in zip(required_skills, req_embs):
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
