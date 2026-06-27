# Horizon - resume.py - owned by Dev 2 (Backend)
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from uuid import uuid4
from services.parser import extract_resume_text
from services.background import process_resume

router = APIRouter()

from db.redis import get_redis_client as get_redis

# Placeholder dependencies until DB is fully wired
async def get_db():
    pass

@router.post("/api/upload-resume")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    redis_client = Depends(get_redis),
    db = Depends(get_db)
):
    ext = file.filename.split('.')[-1].lower() if file.filename else ""
    
    # Allow missing content_type or validate strictly depending on the browser,
    # but basic checks based on requirements:
    if ext not in ['pdf', 'docx']:
        raise HTTPException(status_code=422, detail="Unsupported file type. Please upload PDF or DOCX.")
        
    session_id = str(uuid4())
    
    # Insert minimal session row in DB
    # await db.execute("INSERT INTO sessions (id, status) VALUES ($1, 'processing')", session_id)
    
    file_bytes = await file.read()
    
    try:
        resume_text = extract_resume_text(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    background_tasks.add_task(process_resume, session_id, resume_text, redis_client)
    
    return {"session_id": session_id}
