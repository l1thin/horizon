# Horizon - sessions.py - owned by Dev 2 (Backend)
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

from db.redis import get_redis_client as get_redis

# Placeholder for get_db
async def get_db():
    pass

@router.get("/api/sessions/{session_id}/status")
async def get_session_status(session_id: str, redis_client = Depends(get_redis)):
    status = await redis_client.get(f"session:{session_id}:status")
    
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Handle async redis returning bytes
    if isinstance(status, bytes):
        status = status.decode("utf-8")
        
    error_msg = None
    if status == "error":
        error = await redis_client.get(f"session:{session_id}:error")
        if error:
            error_msg = error.decode("utf-8") if isinstance(error, bytes) else str(error)
            
    return {
        "status": status,
        "error_message": error_msg
    }

class SessionConfig(BaseModel):
    session_id: str
    preferred_language: str

@router.post("/api/sessions")
async def configure_session(session: SessionConfig, db = Depends(get_db)):
    lang = session.preferred_language.lower()
    
    if lang not in ["python", "javascript", "java", "cpp"]:
        raise HTTPException(status_code=422, detail="Unsupported language")
        
    # Update session record in DB
    # await db.execute("UPDATE sessions SET preferred_language = $1, status = 'active' WHERE id = $2", lang, session.session_id)
    
    return {"ok": True}
