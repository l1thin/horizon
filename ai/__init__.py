# Horizon - __init__.py - owned by Dev 3 (AI + Infra)

# Horizon AI layer — exported interface for backend:
# from ai.prompts import extract_profile, generate_questions, evaluate_all_answers, compute_skill_gaps
#
# Import direction rules:
# ai/ → imports: anthropic, stdlib, db connection only
# backend/ → imports from: ai/ only
# frontend/ → calls backend via HTTP/WS only
# NEVER: ai imports from backend. NEVER: backend imports from frontend.

from ai.prompts import (
    extract_profile,
    generate_questions,
    evaluate_all_answers,
    compute_skill_gaps,
    process_voice_turn,
)

__all__ = [
    "extract_profile",
    "generate_questions",
    "evaluate_all_answers",
    "compute_skill_gaps",
    "process_voice_turn",
]

