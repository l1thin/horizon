# Horizon - background.py - owned by Dev 2 (Backend)
import json

try:
    from ai.prompts import extract_profile, generate_questions
except ImportError:
    async def extract_profile(text):
        return {"name":"","skills":[],"projects":[],"years_of_experience":0}
        
    async def generate_questions(profile, job_role, target_company):
        return []

async def save_candidate_profile(session_id: str, profile: dict):
    # TODO: Implement DB save logic once schema and DB access is ready
    pass

async def process_resume(session_id: str, resume_text: str, redis_client):
    try:
        # Step 1 — update status
        await redis_client.set(f"session:{session_id}:status", "processing")

        # Step 2 — extract profile (Dev 3's function)
        profile = await extract_profile(resume_text)

        # Step 3 — generate questions + follow-ups (Dev 3's function)
        # job_role defaults to profile's current_role if not provided
        questions = await generate_questions(
            profile=profile,
            job_role=profile.get("current_role", "Software Engineer"),
            target_company=""
        )

        # Step 4 — store profile + questions in DB and Redis
        await save_candidate_profile(session_id, profile)
        
        await redis_client.set(
            f"session:{session_id}:questions",
            json.dumps(questions),
            ex=7200  # 2 hour TTL
        )
        await redis_client.set(
            f"session:{session_id}:profile",
            json.dumps(profile),
            ex=7200
        )

        # Step 5 — mark ready
        await redis_client.set(f"session:{session_id}:status", "ready")

    except Exception as e:
        await redis_client.set(f"session:{session_id}:status", "error")
        await redis_client.set(f"session:{session_id}:error", str(e))
        raise
