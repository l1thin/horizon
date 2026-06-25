# Horizon - prompts.py - owned by Dev 3 (AI + Infra)
#
# ALL Claude API calls live here only.
# This is the single gateway to the Anthropic API for the entire project.

import json
import os
import base64
from ai.logger import log_ai_call
import ai.config  # ensures config and keys are loaded
from ai.llm_providers import get_llm_provider


# ─────────────────────────────────────────
# PROMPT 1: PROFILE EXTRACTION
# ─────────────────────────────────────────

PROFILE_EXTRACTION_SYSTEM = """
You are an expert resume parser for Horizon, an AI interview platform.

Your task: extract structured candidate information from resume text.

OUTPUT RULES:
- Return ONLY valid JSON. No preamble. No explanation. No markdown fences.
- If a field cannot be determined, use null — never guess or hallucinate.
- For skill years: estimate from employment dates if not explicitly stated.
- For proficiency: use the number of years and seniority indicators in the text.

Output this exact JSON schema:
{
  "name": string | null,
  "email": string | null,
  "current_role": string | null,
  "years_of_experience": number | null,
  "skills": [
    {
      "name": string,
      "years": number | null,
      "proficiency": "beginner" | "intermediate" | "advanced"
    }
  ],
  "projects": [
    {
      "name": string,
      "description": string,
      "technologies": [string],
      "role": string | null
    }
  ],
  "education": [
    {
      "degree": string,
      "institution": string,
      "year": number | null
    }
  ],
  "previous_roles": [
    {
      "title": string,
      "company": string,
      "years": number | null
    }
  ]
}
"""


async def extract_profile(resume_text: str) -> dict:
    """
    Extracts a structured CandidateProfile from raw resume text.
    Returns a dict matching the schema above.
    Retries once on JSON parse failure.
    """
    messages = [{"role": "user", "content": resume_text}]

    provider = get_llm_provider()
    raw = await provider.generate_text(
        system_prompt=PROFILE_EXTRACTION_SYSTEM,
        messages=messages,
        max_tokens=1500,
    )
    await log_ai_call(
        "extract_profile",
        {"resume_length": len(resume_text)},
        {"raw_response": raw[:500]},
    )

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Retry with correction message
        messages.append({"role": "assistant", "content": raw})
        messages.append(
            {
                "role": "user",
                "content": "Your previous response was not valid JSON. Return only the JSON object, no other text.",
            }
        )
        retry_raw = await provider.generate_text(
            system_prompt=PROFILE_EXTRACTION_SYSTEM,
            messages=messages,
            max_tokens=1500,
        )
        try:
            return json.loads(retry_raw)
        except json.JSONDecodeError:
            raise ValueError(
                "Profile extraction failed after retry — Claude did not return valid JSON"
            )


# ─────────────────────────────────────────
# PROMPT 2: QUESTION GENERATION WITH FOLLOW-UPS
# ─────────────────────────────────────────

QUESTION_GENERATION_SYSTEM = """
You are a senior technical interviewer for Horizon, an AI mock interview platform.

Given a candidate profile and target job role, generate a personalised interview plan.

PERSONALISATION RULES (critical — these make Horizon different from generic tools):
- Every technical question MUST name a specific skill from the candidate's skills list
- Every behavioral question MUST reference a real project name from the candidate's projects list
- The project deep-dive question must go deep on ONE specific project they listed
- Coding question difficulty must match years_of_experience:
    < 2 years  → easy: array manipulation, string problems, basic loops
    2–5 years  → medium: trees, hashmaps, sliding window, basic DP
    > 5 years  → hard: system design component combined with algorithm

FOLLOW-UP RULES:
- Every question must include a follow_up field
- The follow_up must probe a specific claim the candidate would likely make in their answer
- Example: if Q asks about Redis caching, follow_up asks "How would you handle cache invalidation if your TTL is shorter than your write frequency?"
- Follow-ups must NOT be generic ("Can you elaborate?") — they must be technically specific

OUTPUT RULES:
- Return ONLY valid JSON array. No preamble. No markdown fences.
- Generate exactly 7 questions in this order:
    q1, q2, q3 → technical (type: "technical")
    q4, q5     → behavioral (type: "behavioral")
    q6         → project deep-dive (type: "behavioral")
    q7         → coding (type: "coding")

Output schema:
[
  {
    "id": "q1",
    "type": "technical" | "behavioral" | "coding",
    "text": string,
    "criteria": {
      "must_cover": [string],
      "good_signals": [string],
      "red_flags": [string]
    },
    "follow_up": string,
    "time_limit_seconds": number | null  // only set for coding questions (e.g. 300)
  }
]

EXAMPLE of good personalisation (use this style):
BAD:  "Tell me about a time you improved system performance."
GOOD: "In your Redis caching project at Acme, you mentioned reducing API latency. Walk me through the specific bottleneck you identified and how you chose Redis as the solution."

BAD follow-up:  "Can you tell me more?"
GOOD follow-up: "You mentioned TTL-based expiry — how would you handle a scenario where data updates more frequently than your TTL allows?"
"""


async def generate_questions(
    profile: dict, job_role: str, target_company: str = ""
) -> list:
    """
    Generates 7 personalised interview questions with follow-ups.
    Uses the candidate's actual skills and project names.
    Returns a list of 7 question dicts.
    """
    user_prompt = f"""Candidate Profile:
{json.dumps(profile, indent=2)}

Target Role: {job_role}
Target Company: {target_company or "Not specified"}

Generate the interview plan now."""

    provider = get_llm_provider()
    raw = await provider.generate_text(
        system_prompt=QUESTION_GENERATION_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=3000,
    )
    await log_ai_call(
        "generate_questions",
        {
            "job_role": job_role,
            "skills_count": len(profile.get("skills", [])),
        },
        {"raw_length": len(raw)},
    )

    try:
        questions = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("Question generation returned invalid JSON")

    if len(questions) != 7:
        raise ValueError(f"Expected 7 questions, got {len(questions)}")

    # Ensure IDs are set
    for i, q in enumerate(questions):
        if "id" not in q or not q["id"]:
            q["id"] = f"q{i + 1}"

    return questions




ANSWER_EVALUATION_SYSTEM = """
You are a calibrated interview scoring engine for Horizon.

You will receive a single interview question, its evaluation criteria, and the candidate's spoken answer transcript.
Score it on a 0–10 scale. Be consistent — the same quality answer must always receive the same score.

SCORING GUIDE:
0–2  → Answer is off-topic, incoherent, or completely wrong
3–4  → Answer is on-topic but only surface-level; misses key concepts
5–6  → Adequate answer; covers most criteria but lacks depth or examples
7–8  → Strong answer; covers all must_cover points with concrete detail
9–10 → Exceptional; deep technical insight, real-world grounding, precise terminology

SCORING MECHANICS:
- Start score from must_cover: each covered item = +1 point (scaled to 10)
- good_signals present = +0.5–1 per signal (up to +2 total)
- red_flags present = -1 per flag (up to -2 total)
- Coding answers: also evaluate correctness, efficiency, and code quality from the code field if present

integrity_note rules — set to a string ONLY if:
(a) Answer is implausibly comprehensive for question difficulty
(b) Answer uses third-person language ("one could approach this by…")
(c) Answer is perfectly structured with zero hesitation markers on a complex question
Otherwise set to null.

OUTPUT: Return ONLY valid JSON. No preamble. No markdown fences.
{
  "score": number (0–10, one decimal),
  "what_was_good": string (1–2 sentences),
  "what_was_missing": string (1–2 sentences, or "Nothing significant" if score >= 8),
  "suggestions": [string, string],
  "depth_rating": "surface" | "adequate" | "deep",
  "integrity_note": string | null
}

FEW-SHOT EXAMPLES:

Question: "Explain how a hashmap works and when you'd use one."
Weak answer: "It stores key-value pairs and is fast."
Score: 3.5 | what_was_good: "Correctly identified the key-value structure." | what_was_missing: "No mention of hashing function, collision handling, or O(1) average complexity." | depth_rating: "surface"

Adequate answer: "A hashmap uses a hash function to map keys to array indices. Lookup is O(1) average. Good for frequency counting, caching, deduplication."
Score: 6.5 | depth_rating: "adequate"

Strong answer: "A hashmap applies a hash function to convert a key to an integer index in an underlying array. Collisions are handled via chaining or open addressing. Average O(1) for get/put, worst case O(n). I'd reach for one when I need fast key-based lookup — for example, I used one in my rate limiter to track request counts per user ID in O(1) time."
Score: 9.0 | depth_rating: "deep"
"""


async def evaluate_answer_single(question: dict, answer: dict) -> dict:
    """Internal helper — evaluates one answer against its question criteria."""
    user_prompt = f"""Question: {question["text"]}

Criteria:
{json.dumps(question.get("criteria", {}), indent=2)}

Candidate's Answer:
{answer.get("transcript") or answer.get("code") or "(no answer provided)"}

Evaluate this answer."""

    try:
        provider = get_llm_provider()
        raw = await provider.generate_text(
            system_prompt=ANSWER_EVALUATION_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=800,
        )
        result = json.loads(raw)
        # Validate required fields
        assert "score" in result and 0 <= result["score"] <= 10
        return result
    except Exception as e:
        await log_ai_call(
            "evaluate_answer_single",
            {"question_id": question.get("id")},
            {"error": str(e)},
        )
        # Safe default — never crash mid-eval
        return {
            "score": 5.0,
            "what_was_good": "Evaluation unavailable.",
            "what_was_missing": "",
            "suggestions": [],
            "depth_rating": "adequate",
            "integrity_note": None,
        }


async def evaluate_all_answers(session_id: str, raw_answers: list) -> list:
    """
    Evaluates all answers post-session. Called by backend after WS closes.
    Returns the same list with evaluation fields added to each answer.
    """
    evaluated = []
    for answer in raw_answers:
        eval_result = await evaluate_answer_single(
            question={
                "text": answer["question_text"],
                "criteria": answer.get("criteria", {}),
                "id": answer["question_id"],
            },
            answer=answer,
        )
        evaluated.append({**answer, **eval_result})

    await log_ai_call(
        "evaluate_all_answers",
        {"session_id": session_id, "answer_count": len(raw_answers)},
        {"evaluated_count": len(evaluated)},
    )
    return evaluated


async def compute_skill_gaps(session_id: str, evaluated_answers: list) -> list:
    """
    Computes top 3 skill gaps from evaluated answers.
    No Claude call needed — uses scores directly.
    Returns [{ skill, gap_score }] sorted by biggest gap first.
    """
    skill_scores = {}
    skill_counts = {}

    for answer in evaluated_answers:
        q_type = answer.get("question_type", "technical")
        score = answer.get("score", 5.0)
        # Use question_type as a proxy skill dimension
        key = q_type
        skill_scores[key] = skill_scores.get(key, 0) + score
        skill_counts[key] = skill_counts.get(key, 0) + 1

    # Compute average scores and invert to get gap (10 - avg_score = gap)
    gaps = []
    for skill, total in skill_scores.items():
        avg = total / skill_counts[skill]
        gap_score = round(10 - avg, 1)
        gaps.append({"skill": skill.capitalize(), "gap_score": gap_score})

    # Sort by biggest gap
    gaps.sort(key=lambda x: x["gap_score"], reverse=True)
    return gaps[:3]


LIVE_INTERVIEW_SYSTEM = """
You are a conversational technical interviewer for Horizon.
You are currently conducting a live voice interview with a candidate.
The candidate will speak to you, and their audio will be provided directly as an attachment.

RULES:
- Respond naturally, as if you are speaking in a real-time conversation.
- Keep your responses concise and conversational (1-3 sentences).
- If the candidate's audio is unclear, politely ask them to repeat.
- Guide the conversation based on the current interview plan.
"""


async def process_voice_turn(
    session_id: str,
    audio_bytes: bytes,
    media_type: str,
    conversation_history: list[dict],
) -> dict:
    """
    Processes a single live voice turn by routing the audio to the chosen LLM provider.
    Supported models: Claude, OpenAI GPT, Gemini.
    Returns: {"text": str, "audio_bytes": bytes | None}
    """
    provider = get_llm_provider()
    return await provider.process_voice_turn(
        session_id=session_id,
        audio_bytes=audio_bytes,
        media_type=media_type,
        conversation_history=conversation_history,
        system_prompt=LIVE_INTERVIEW_SYSTEM,
    )

