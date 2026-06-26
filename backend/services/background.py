# Horizon - background.py - owned by Dev 2 (Backend)
import json
import uuid

try:
    from ai.orchestrator import InterviewOrchestrator
except ImportError:
    pass

async def save_candidate_profile(session_id: str, profile: dict):
    # TODO: Implement DB save logic once schema and DB access is ready
    pass

async def process_resume(session_id: str, resume_text: str, redis_client):
    try:
        # Step 1 — update status
        await redis_client.set(f"session:{session_id}:status", "processing")

        orchestrator = InterviewOrchestrator()

        # Step 2 — extract profile (Dev 3's function)
        profile = await orchestrator.extract_profile(resume_text)

        # Step 3 — store profile in DB and Redis
        await save_candidate_profile(session_id, profile)
        
        await redis_client.set(
            f"session:{session_id}:profile",
            json.dumps(profile),
            ex=7200
        )
        
        # Crucial Step: Save inferred target skills
        target_skills = profile.get("inferred_target_skills", [])
        await redis_client.set(
            f"session:{session_id}:target_skills",
            json.dumps(target_skills), ex=7200
        )

        # Step 4 — generate questions
        # job_role defaults to profile's current_role if not provided
        questions_data = await orchestrator.generate_interview_plan(
            resume_text=resume_text,
            job_description=profile.get("current_role", "Software Engineer")
        )
        
        mapped_questions = []
        for q in questions_data:
            mapped_q = {
                "id": str(uuid.uuid4()),
                "text": q.get("base_question", ""),
                "type": q.get("question_type", "question")
            }
            if mapped_q["type"] == "coding":
                mapped_q["time_limit_seconds"] = 300
            mapped_questions.append(mapped_q)

        await redis_client.set(
            f"session:{session_id}:questions",
            json.dumps(mapped_questions),
            ex=7200  # 2 hour TTL
        )

        # Step 5 — mark ready
        await redis_client.set(f"session:{session_id}:status", "ready")

    except Exception as e:
        await redis_client.set(f"session:{session_id}:status", "error")
        await redis_client.set(f"session:{session_id}:error", str(e))
        raise
