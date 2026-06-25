# Horizon - test_prompts.py - owned by Dev 3 (AI + Infra)
#
# Tests for ai/prompts.py — Claude API gateway functions.

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_PROFILE = {
    "name": "Sarah Chen",
    "email": "sarah.chen@email.com",
    "current_role": "Senior Backend Engineer",
    "years_of_experience": 6,
    "skills": [
        {"name": "Python", "years": 5, "proficiency": "advanced"},
        {"name": "PostgreSQL", "years": 4, "proficiency": "advanced"},
        {"name": "Docker", "years": 3, "proficiency": "intermediate"},
        {"name": "AWS", "years": 3, "proficiency": "intermediate"},
        {"name": "FastAPI", "years": 2, "proficiency": "intermediate"},
    ],
    "projects": [
        {
            "name": "Real-time Analytics Pipeline",
            "description": "Built a streaming data pipeline processing 50k events/sec using Kafka and Flink.",
            "technologies": ["Python", "Kafka", "Apache Flink", "PostgreSQL"],
            "role": "Tech Lead",
        },
        {
            "name": "Auth Microservice",
            "description": "Designed and deployed an OAuth2/OIDC auth service handling 10M+ monthly logins.",
            "technologies": ["Python", "FastAPI", "Redis", "Docker"],
            "role": "Lead Developer",
        },
    ],
    "education": [
        {
            "degree": "B.S. Computer Science",
            "institution": "University of Washington",
            "year": 2019,
        }
    ],
    "previous_roles": [
        {"title": "Senior Backend Engineer", "company": "DataStream Inc.", "years": 3},
        {"title": "Backend Developer", "company": "CloudNova", "years": 2},
        {"title": "Junior Developer", "company": "StartupXYZ", "years": 1},
    ],
}

TYPICAL_RESUME = """
Sarah Chen
sarah.chen@email.com

EXPERIENCE
Senior Backend Engineer — DataStream Inc. (2022–Present)
- Led development of a real-time analytics pipeline processing 50k events/sec
- Tech stack: Python, Kafka, Apache Flink, PostgreSQL
- Managed a team of 3 engineers

Backend Developer — CloudNova (2020–2022)
- Designed and deployed an OAuth2/OIDC auth service handling 10M+ monthly logins
- Built with Python, FastAPI, Redis, Docker

Junior Developer — StartupXYZ (2019–2020)
- Full-stack development with Python and React

EDUCATION
B.S. Computer Science, University of Washington, 2019

SKILLS
Python (5 years), PostgreSQL (4 years), Docker (3 years), AWS (3 years), FastAPI (2 years)
""".strip()


def _mock_response(text: str) -> MagicMock:
    """Build a mock Anthropic ``Message`` response object."""
    content_block = MagicMock()
    content_block.text = text

    usage = MagicMock()
    usage.input_tokens = 200
    usage.output_tokens = 150

    msg = MagicMock()
    msg.content = [content_block]
    msg.usage = usage
    return msg


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_extract_profile_typical(mock_client, mock_log):
    """A 10-line resume should produce a profile with name, skills (list), and projects (list)."""
    mock_client.messages.create.return_value = _mock_response(json.dumps(VALID_PROFILE))

    from ai.prompts import extract_profile

    result = await extract_profile(TYPICAL_RESUME)

    # Core structure assertions
    assert result["name"] == "Sarah Chen"
    assert isinstance(result["skills"], list)
    assert len(result["skills"]) > 0
    assert isinstance(result["projects"], list)
    assert len(result["projects"]) > 0

    # Verify each skill has the expected sub-keys
    for skill in result["skills"]:
        assert "name" in skill
        assert "proficiency" in skill

    # Verify Claude was called exactly once (no retry needed)
    mock_client.messages.create.assert_called_once()
    mock_log.assert_awaited_once()


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_extract_profile_minimal(mock_client, mock_log):
    """A minimal one-liner resume should not crash, and name should be populated."""
    minimal_profile = {
        "name": "John Doe",
        "email": None,
        "current_role": "Python developer",
        "years_of_experience": 3,
        "skills": [{"name": "Python", "years": 3, "proficiency": "intermediate"}],
        "projects": [],
        "education": [],
        "previous_roles": [],
    }
    mock_client.messages.create.return_value = _mock_response(json.dumps(minimal_profile))

    from ai.prompts import extract_profile

    result = await extract_profile("John Doe, Python developer, 3 years")

    assert result["name"] == "John Doe"
    assert result["name"] is not None
    assert isinstance(result["skills"], list)
    # Should not crash even with sparse data
    assert isinstance(result["projects"], list)
    assert isinstance(result["education"], list)


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_extract_profile_retry(mock_client, mock_log):
    """When Claude returns invalid JSON on the first call, extract_profile retries and succeeds."""
    invalid_response = _mock_response("Sure! Here is the profile:\n{invalid json")
    valid_response = _mock_response(json.dumps(VALID_PROFILE))

    # First call → garbage, second call → valid JSON
    mock_client.messages.create.side_effect = [invalid_response, valid_response]

    from ai.prompts import extract_profile

    result = await extract_profile(TYPICAL_RESUME)

    # Should have succeeded on the retry
    assert result["name"] == "Sarah Chen"
    assert isinstance(result["skills"], list)

    # Verify Claude was called exactly twice (original + retry)
    assert mock_client.messages.create.call_count == 2

    # Verify the retry call included the correction message
    retry_call_args = mock_client.messages.create.call_args_list[1]
    retry_messages = retry_call_args.kwargs.get("messages") or retry_call_args[1].get("messages")
    # Should have 3 messages: original user, assistant (bad), user (correction)
    assert len(retry_messages) == 3
    assert retry_messages[1]["role"] == "assistant"
    assert retry_messages[2]["role"] == "user"
    assert "not valid JSON" in retry_messages[2]["content"]


# ---------------------------------------------------------------------------
# generate_questions — Fixtures
# ---------------------------------------------------------------------------

PERSONALISED_PROFILE = {
    "name": "Alex Rivera",
    "email": "alex@example.com",
    "current_role": "Backend Engineer",
    "years_of_experience": 4,
    "skills": [
        {"name": "FastAPI", "years": 3, "proficiency": "advanced"},
        {"name": "Redis", "years": 2, "proficiency": "intermediate"},
        {"name": "PostgreSQL", "years": 4, "proficiency": "advanced"},
    ],
    "projects": [
        {
            "name": "RedisCacheApp",
            "description": "Built a distributed caching layer using Redis to reduce API latency by 60%.",
            "technologies": ["Redis", "Python", "FastAPI"],
            "role": "Lead Developer",
        },
        {
            "name": "DataSync Pipeline",
            "description": "Real-time data sync between PostgreSQL and Elasticsearch.",
            "technologies": ["PostgreSQL", "Python", "Elasticsearch"],
            "role": "Developer",
        },
    ],
    "education": [
        {"degree": "B.S. Computer Science", "institution": "UC Berkeley", "year": 2021}
    ],
    "previous_roles": [
        {"title": "Backend Engineer", "company": "CacheCo", "years": 2},
        {"title": "Junior Developer", "company": "StartupABC", "years": 2},
    ],
}


def _build_mock_questions(
    *,
    profile: dict = PERSONALISED_PROFILE,
    coding_text: str = "Implement a hashmap-based LRU cache with O(1) get and put operations.",
) -> list[dict]:
    """Build a realistic 7-question mock response referencing the given profile."""
    skill_names = [s["name"] for s in profile.get("skills", [])]
    project_names = [p["name"] for p in profile.get("projects", [])]

    # Pick names to embed in question text for personalisation
    s1 = skill_names[0] if len(skill_names) > 0 else "Python"
    s2 = skill_names[1] if len(skill_names) > 1 else "SQL"
    s3 = skill_names[2] if len(skill_names) > 2 else "Docker"
    p1 = project_names[0] if len(project_names) > 0 else "Project A"
    p2 = project_names[1] if len(project_names) > 1 else "Project B"

    return [
        {
            "id": "q1",
            "type": "technical",
            "text": f"Explain how {s1} handles asynchronous request routing under high concurrency.",
            "criteria": {
                "must_cover": ["async/await", "event loop", "concurrency model"],
                "good_signals": ["mentions Starlette internals", "understands uvicorn workers"],
                "red_flags": ["confuses threads with async", "cannot explain event loop"],
            },
            "follow_up": f"If a {s1} endpoint blocks on a synchronous DB call, how does that affect other in-flight requests?",
            "time_limit_seconds": None,
        },
        {
            "id": "q2",
            "type": "technical",
            "text": f"Describe the {s2} eviction policies you've used and when you'd choose each one.",
            "criteria": {
                "must_cover": ["LRU", "TTL", "memory management"],
                "good_signals": ["mentions allkeys-lru vs volatile-lru trade-offs"],
                "red_flags": ["only knows one policy"],
            },
            "follow_up": f"How would you monitor {s2} memory usage in production to pre-empt OOM kills?",
            "time_limit_seconds": None,
        },
        {
            "id": "q3",
            "type": "technical",
            "text": f"Walk me through how you'd optimise a slow {s3} query that joins three tables with millions of rows.",
            "criteria": {
                "must_cover": ["EXPLAIN ANALYZE", "indexing strategy", "query plan"],
                "good_signals": ["mentions covering indexes", "discusses partitioning"],
                "red_flags": ["suggests SELECT * as first step"],
            },
            "follow_up": f"If adding an index on {s3} speeds up reads but your write throughput drops 40%, how would you handle that trade-off?",
            "time_limit_seconds": None,
        },
        {
            "id": "q4",
            "type": "behavioral",
            "text": f"In your {p1} project, you reduced API latency by 60%. Tell me about a technical disagreement you had with your team during that project and how you resolved it.",
            "criteria": {
                "must_cover": ["conflict resolution", "technical reasoning", "outcome"],
                "good_signals": ["data-driven argument", "compromise with rationale"],
                "red_flags": ["blames others", "no resolution mentioned"],
            },
            "follow_up": f"Looking back at {p1}, would you make the same architectural choice today? What would you change?",
            "time_limit_seconds": None,
        },
        {
            "id": "q5",
            "type": "behavioral",
            "text": f"Your {p2} involved syncing data between PostgreSQL and Elasticsearch in real-time. Describe a time during that project when you had to make a decision with incomplete information.",
            "criteria": {
                "must_cover": ["uncertainty handling", "risk assessment", "decision framework"],
                "good_signals": ["mentions reversibility of decision", "set up monitoring"],
                "red_flags": ["waited for perfect information", "no risk awareness"],
            },
            "follow_up": f"In {p2}, how did you validate that the sync was eventually consistent and not losing records?",
            "time_limit_seconds": None,
        },
        {
            "id": "q6",
            "type": "behavioral",
            "text": f"Let's go deep on {p1}. Walk me through the architecture end-to-end: how does a request flow from the client through your caching layer and back?",
            "criteria": {
                "must_cover": ["cache-aside or write-through pattern", "cache miss handling", "invalidation"],
                "good_signals": ["draws clear data flow", "mentions failure modes"],
                "red_flags": ["vague about cache strategy", "no mention of invalidation"],
            },
            "follow_up": f"In {p1}, what happens if your Redis node goes down mid-request? What's the fallback?",
            "time_limit_seconds": None,
        },
        {
            "id": "q7",
            "type": "coding",
            "text": coding_text,
            "criteria": {
                "must_cover": ["hash map", "doubly linked list", "O(1) complexity"],
                "good_signals": ["clean API", "handles edge cases"],
                "red_flags": ["O(n) eviction", "no capacity management"],
            },
            "follow_up": "How would you extend this to support TTL-based expiry in addition to capacity-based eviction?",
            "time_limit_seconds": 300,
        },
    ]


# ---------------------------------------------------------------------------
# Tests — generate_questions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_generate_personalised(mock_client, mock_log):
    """Questions should reference the candidate's actual skills and project names."""
    questions = _build_mock_questions(profile=PERSONALISED_PROFILE)
    mock_client.messages.create.return_value = _mock_response(json.dumps(questions))

    from ai.prompts import generate_questions

    result = await generate_questions(
        PERSONALISED_PROFILE, "Senior Backend Engineer", "Acme Corp"
    )

    # Flatten all question texts into one searchable string
    all_text = " ".join(q["text"] for q in result)

    # At least one question must mention the project name or a skill name
    assert "RedisCacheApp" in all_text or "FastAPI" in all_text, (
        "Questions should be personalised to reference the candidate's projects or skills"
    )


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_generate_count(mock_client, mock_log):
    """generate_questions must return exactly 7 questions."""
    questions = _build_mock_questions()
    mock_client.messages.create.return_value = _mock_response(json.dumps(questions))

    from ai.prompts import generate_questions

    result = await generate_questions(PERSONALISED_PROFILE, "Backend Engineer")

    assert len(result) == 7


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_generate_follow_ups(mock_client, mock_log):
    """Every question must have a non-empty 'follow_up' string."""
    questions = _build_mock_questions()
    mock_client.messages.create.return_value = _mock_response(json.dumps(questions))

    from ai.prompts import generate_questions

    result = await generate_questions(PERSONALISED_PROFILE, "Backend Engineer")

    for i, q in enumerate(result):
        assert "follow_up" in q, f"q{i + 1} is missing 'follow_up' field"
        assert isinstance(q["follow_up"], str), f"q{i + 1} follow_up is not a string"
        assert len(q["follow_up"].strip()) > 0, f"q{i + 1} follow_up is empty"


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_generate_coding_easy(mock_client, mock_log):
    """For a junior candidate (years_of_experience=1), the coding question should be easy-tier."""
    junior_profile = {
        **PERSONALISED_PROFILE,
        "years_of_experience": 1,
        "current_role": "Junior Developer",
    }
    easy_coding_text = (
        "Write a function that takes an array of integers and returns the two "
        "numbers that add up to a given target. Use a basic loop or hash set."
    )
    questions = _build_mock_questions(
        profile=junior_profile,
        coding_text=easy_coding_text,
    )
    mock_client.messages.create.return_value = _mock_response(json.dumps(questions))

    from ai.prompts import generate_questions

    result = await generate_questions(junior_profile, "Junior Developer")

    # Find the coding question (q7)
    coding_q = next(q for q in result if q["type"] == "coding")

    # Easy-tier should mention array/string/loop-level language
    coding_lower = coding_q["text"].lower()
    easy_keywords = ["array", "string", "loop", "basic", "hash set", "list"]
    assert any(kw in coding_lower for kw in easy_keywords), (
        f"Coding question for junior candidate should use easy-tier language, "
        f"got: {coding_q['text'][:100]}"
    )


# ---------------------------------------------------------------------------
# evaluate_all_answers — Fixtures
# ---------------------------------------------------------------------------

STRONG_EVAL_RESPONSE = {
    "score": 8.5,
    "what_was_good": "Thorough explanation of Redis eviction policies with real-world production context.",
    "what_was_missing": "Nothing significant",
    "suggestions": [
        "Could mention Redis Cluster sharding for horizontal scaling",
        "Consider discussing memory fragmentation metrics",
    ],
    "depth_rating": "deep",
    "integrity_note": None,
}

WEAK_EVAL_RESPONSE = {
    "score": 2.0,
    "what_was_good": "Acknowledged the topic area.",
    "what_was_missing": "No technical content provided. Missing all must_cover criteria.",
    "suggestions": [
        "Study Redis eviction policies: LRU, LFU, TTL-based",
        "Practice explaining trade-offs between eviction strategies",
    ],
    "depth_rating": "surface",
    "integrity_note": None,
}

SAFE_DEFAULT_EVAL = {
    "score": 5.0,
    "what_was_good": "Evaluation unavailable.",
    "what_was_missing": "",
    "suggestions": [],
    "depth_rating": "adequate",
    "integrity_note": None,
}


def _build_raw_answer(
    *,
    question_id: str = "q1",
    question_text: str = "Explain Redis eviction policies.",
    transcript: str = "I don't know.",
    criteria: dict | None = None,
) -> dict:
    """Build a single raw answer dict in the shape evaluate_all_answers expects."""
    return {
        "question_id": question_id,
        "question_text": question_text,
        "transcript": transcript,
        "criteria": criteria or {
            "must_cover": ["LRU", "TTL", "memory management"],
            "good_signals": ["mentions allkeys-lru vs volatile-lru"],
            "red_flags": ["only knows one policy"],
        },
    }


def _build_raw_answers_batch(count: int = 7) -> list[dict]:
    """Build a batch of raw answers for evaluate_all_answers."""
    return [
        _build_raw_answer(
            question_id=f"q{i + 1}",
            question_text=f"Question {i + 1} text",
            transcript=f"Answer {i + 1} content with some technical detail.",
        )
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# Tests — evaluate_all_answers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_evaluate_strong(mock_client, mock_log):
    """A detailed, technically deep answer should score >= 7."""
    mock_client.messages.create.return_value = _mock_response(
        json.dumps(STRONG_EVAL_RESPONSE)
    )

    from ai.prompts import evaluate_all_answers

    strong_answer = _build_raw_answer(
        transcript=(
            "Redis supports several eviction policies: allkeys-lru removes the least recently "
            "used key across all keys, volatile-lru does the same but only among keys with a TTL "
            "set. There's also allkeys-lfu for frequency-based eviction. In production at CacheCo, "
            "I configured volatile-ttl because our cached API responses had natural expiry times, "
            "and I monitored evicted_keys via Redis INFO to pre-empt OOM kills. We also set "
            "maxmemory-policy to noeviction on our session store to avoid silent data loss."
        ),
    )

    result = await evaluate_all_answers("session-001", [strong_answer])

    assert len(result) == 1
    assert result[0]["score"] >= 7
    assert result[0]["depth_rating"] == "deep"


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_evaluate_weak(mock_client, mock_log):
    """'I don't know' should score <= 3."""
    mock_client.messages.create.return_value = _mock_response(
        json.dumps(WEAK_EVAL_RESPONSE)
    )

    from ai.prompts import evaluate_all_answers

    weak_answer = _build_raw_answer(transcript="I don't know.")

    result = await evaluate_all_answers("session-002", [weak_answer])

    assert len(result) == 1
    assert result[0]["score"] <= 3
    assert result[0]["depth_rating"] == "surface"


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_evaluate_all_never_raises(mock_client, mock_log):
    """Even if Claude throws on every call, evaluate_all_answers returns safe defaults — never crashes."""
    mock_client.messages.create.side_effect = RuntimeError("API connection failed")

    from ai.prompts import evaluate_all_answers

    answers = _build_raw_answers_batch(3)
    result = await evaluate_all_answers("session-003", answers)

    # Should return all 3 answers with safe defaults, not raise
    assert len(result) == 3
    for item in result:
        assert item["score"] == 5.0
        assert item["what_was_good"] == "Evaluation unavailable."
        assert item["depth_rating"] == "adequate"
        assert item["integrity_note"] is None


@pytest.mark.asyncio
@patch("ai.prompts.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_evaluate_all_count(mock_client, mock_log):
    """Pass 7 answers → get exactly 7 evaluated answers back."""
    mock_client.messages.create.return_value = _mock_response(
        json.dumps(STRONG_EVAL_RESPONSE)
    )

    from ai.prompts import evaluate_all_answers

    answers = _build_raw_answers_batch(7)
    result = await evaluate_all_answers("session-004", answers)

    assert len(result) == 7
    # Each result should merge original answer fields + eval fields
    for i, item in enumerate(result):
        assert item["question_id"] == f"q{i + 1}"
        assert "score" in item
        assert "what_was_good" in item
        assert "depth_rating" in item


# ---------------------------------------------------------------------------
# Tests — process_voice_turn
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("ai.voice_providers.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_process_voice_turn_empty(mock_client, mock_log):
    """Empty audio should immediately return a fallback string without calling Claude."""
    from ai.prompts import process_voice_turn

    result = await process_voice_turn("session-1", b"", "audio/wav", [])

    assert "repeat" in result["text"].lower()
    assert result["audio_bytes"] is None
    mock_client.messages.create.assert_not_called()
    mock_log.assert_not_awaited()


class _MockTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text

class _MockAudioSource:
    def __init__(self, data):
        self.data = data

class _MockAudioBlock:
    def __init__(self, data):
        self.type = "audio"
        self.source = _MockAudioSource(data)

class _MockResponseWithAudio:
    def __init__(self, text, audio_base64):
        self.content = [_MockTextBlock(text), _MockAudioBlock(audio_base64)]

@pytest.mark.asyncio
@patch("ai.voice_providers.log_ai_call", new_callable=AsyncMock)
@patch("ai.prompts.client")
async def test_process_voice_turn_valid(mock_client, mock_log):
    """Valid audio should be wrapped in a multimodal audio block and appended to history.
    Claude's response should be parsed for both text and audio blocks."""
    import base64
    fake_audio = b"fake_claude_audio_response"
    encoded_audio = base64.b64encode(fake_audio).decode("utf-8")
    
    mock_client.messages.create.return_value = _MockResponseWithAudio("Sure, I can hear you.", encoded_audio)

    from ai.prompts import process_voice_turn

    history = [{"role": "assistant", "content": "How are you?"}]
    audio_data = b"dummy_audio_bytes"

    result = await process_voice_turn("session-2", audio_data, "audio/wav", history)

    assert result["text"] == "Sure, I can hear you."
    assert result["audio_bytes"] == fake_audio
    
    # Verify Claude was called with the correct multimodal payload
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args.kwargs
    messages = call_kwargs["messages"]
    
    # Should have 2 messages: the history + the new audio turn
    assert len(messages) == 2
    assert messages[0] == history[0]
    
    new_msg = messages[1]
    assert new_msg["role"] == "user"
    assert new_msg["content"][0]["type"] == "audio"
    assert new_msg["content"][0]["source"]["media_type"] == "audio/wav"
    assert "data" in new_msg["content"][0]["source"]


