# AntiGravity - resume.py - owned by Dev 2 (Backend)
import json
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from db.database import get_db
from models.candidate import CandidateProfile
from services.parser import extract_resume_text

# Safe import for Dev 3's function (owned by Dev 3, mocked if absent)
try:
    from ai.prompts import extract_profile
except ImportError:
    async def extract_profile(text: str) -> dict:
        """
        Mock implementation of extract_profile to use if ai.prompts is absent.
        Returns a dict conforming to CandidateProfile.
        """
        return {
            "name": "Mock Candidate",
            "email": "mock.candidate@example.com",
            "current_role": "Software Engineer",
            "years_of_experience": 5,
            "skills": [
                {"name": "Python", "years": 3.0, "proficiency": "advanced"},
                {"name": "FastAPI", "years": 2.0, "proficiency": "intermediate"}
            ],
            "projects": [
                {
                    "name": "AntiGravity Core",
                    "description": "AI agent platform backend.",
                    "technologies": ["Python", "FastAPI", "SQLite"],
                    "role": "Backend Engineer"
                }
            ],
            "education": ["B.S. in Computer Science"],
            "previous_roles": ["Junior Software Engineer"]
        }

router = APIRouter()

@router.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    """
    Endpoint to upload candidate resume.
    1. Reads file bytes.
    2. Extracts text using PDF or DOCX extractor.
    3. Sends text to profile extractor.
    4. Validates parsed structure.
    5. Saves candidate record to candidates database table.
    """
    # 1. Accept and read UploadFile bytes
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read upload file contents: {str(e)}"
        )

    # 2. Call extract_resume_text
    try:
        text = extract_resume_text(file.filename, file_bytes)
    except ValueError as e:
        # Return 422 with clear message if file is wrong format or too short
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {str(e)}")

    # 3. Call extract_profile(text)
    try:
        profile_dict = await extract_profile(text)
    except Exception as e:
        # Return 500 with "Resume parsing failed" if extract_profile throws
        raise HTTPException(status_code=500, detail="Resume parsing failed")

    # 4. Validate the returned dict as CandidateProfile
    try:
        profile = CandidateProfile(**profile_dict)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Candidate profile validation failed: {str(e)}"
        )

    # 5. Store in candidates table via db.database.get_db()
    candidate_id = str(uuid.uuid4())
    try:
        db.execute(
            """
            INSERT INTO candidates (id, name, email, current_role, years_of_experience, skills, projects, education, previous_roles)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                profile.name,
                profile.email,
                profile.current_role,
                profile.years_of_experience,
                json.dumps([s.model_dump() for s in profile.skills]),
                json.dumps([p.model_dump() for p in profile.projects]),
                json.dumps(profile.education),
                json.dumps(profile.previous_roles)
            )
        )
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database storage failed: {str(e)}"
        )

    # 6. Return response
    return {
        "candidate_id": candidate_id,
        "name": profile.name,
        "skills_count": len(profile.skills)
    }
