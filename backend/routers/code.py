# Horizon - code.py - owned by Dev 2 (Backend)
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.executor import LANGUAGE_IDS, run_on_judge0

router = APIRouter()

# Placeholder DB dependency
async def get_db():
    pass

class CodeSubmitPayload(BaseModel):
    code: str
    language: str
    question_id: str

@router.post("/api/sessions/{session_id}/code")
async def submit_code(session_id: str, payload: CodeSubmitPayload, db = Depends(get_db)):
    lang = payload.language.lower()
    if lang not in LANGUAGE_IDS:
        raise HTTPException(status_code=422, detail="Unsupported language")
        
    result = await run_on_judge0(payload.code, lang)
    
    # TODO: Store result in DB linked to question_id
    # await db.execute(...)
    
    return result
