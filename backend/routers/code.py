# Horizon - code.py - owned by Dev 2 (Backend)
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.executor import SUPPORTED_LANGUAGES, execute_code

router = APIRouter()

# Placeholder DB dependencies
async def get_db():
    pass

async def get_redis():
    pass

class CodeSubmitPayload(BaseModel):
    code: str
    language: str
    question_id: str

@router.post("/api/sessions/{session_id}/submit-code")
async def submit_code(session_id: str, payload: CodeSubmitPayload, db = Depends(get_db)):
    lang = payload.language.lower()
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail="Unsupported language")
        
    result = await execute_code(payload.code, lang)
    
    # TODO: Store result in DB linked to question_id
    
    return result

@router.get("/api/sessions/{session_id}/coding-questions")
async def get_coding_questions(session_id: str, redis = Depends(get_redis)):
    # Pull questions from Redis
    raw = await redis.get(f"session:{session_id}:questions")
    if not raw:
        raise HTTPException(status_code=404, detail="Session not found or questions not ready")
        
    # Decode async redis bytes if necessary
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
        
    questions = json.loads(raw)
    coding_questions = [q for q in questions if q.get("type") == "coding"]
    
    return {"questions": coding_questions}

class EvaluateCodePayload(BaseModel):
    code: str
    language: str
    question_id: str

@router.post("/api/sessions/{session_id}/evaluate-code")
async def evaluate_code(session_id: str, payload: EvaluateCodePayload, db = Depends(get_db)):
    # This route delegates to Dev 3's AI evaluator
    try:
        try:
            from ai.orchestrator import InterviewOrchestrator
        except ImportError:
            # Stub if not yet available
            return {
                "score": 0,
                "feedback": {
                    "what_was_good": "Submission successful.",
                    "what_was_missing": "AI logic is currently stubbed.",
                    "suggestions": ["Ensure Dev 3's InterviewOrchestrator is imported."]
                }
            }
            
        orchestrator = InterviewOrchestrator()
        # In the future: feedback = await orchestrator.evaluate_code(payload.code, payload.question_id)
        # For now, returning a generic AI evaluation object pattern
        feedback = {
            "score": 10,
            "feedback": {
                "what_was_good": "Clean syntax",
                "what_was_missing": "Edge cases",
                "suggestions": ["Handle null inputs"]
            }
        }
        
        return feedback
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
