# Horizon - report.py - owned by Dev 2 (Backend)
import json
import asyncio
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()

from db.redis import get_redis_client as get_redis

async def get_db():
    pass

# Placeholder DB fetch functions
async def fetch_report_from_db(session_id, db):
    return None

async def fetch_raw_answers_from_db(session_id, db):
    return []

@router.get("/api/sessions/{session_id}/report")
async def get_report(session_id: str, redis_client = Depends(get_redis), db = Depends(get_db)):
    # Check Redis for cached report
    cached_report = await redis_client.get(f"session:{session_id}:report")
    if cached_report:
        return json.loads(cached_report if isinstance(cached_report, str) else cached_report.decode('utf-8'))
        
    # If not cached: fetch from DB
    report = await fetch_report_from_db(session_id, db)
    
    if not report:
        # Check status
        status = await redis_client.get(f"session:{session_id}:status")
        if isinstance(status, bytes):
            status = status.decode('utf-8')
            
        if status == "report_ready":
            # Wait up to 5s with 1s polls
            for _ in range(5):
                await asyncio.sleep(1.0)
                report = await fetch_report_from_db(session_id, db)
                if report:
                    break
                    
        if not report:
            raise HTTPException(status_code=425, detail="Evaluation still in progress")
            
    # Compute integrity_summary from raw answer keystroke data
    raw_answers = await fetch_raw_answers_from_db(session_id, db)
    tab_switches = 0
    fast_answers = 0
    for ans in raw_answers:
        integrity = ans.get("integrity", {})
        tab_switches += len(integrity.get("tab_switches", []))
        if integrity.get("think_time_ms", 9999) < 2000:
            fast_answers += 1
            
    verdict = "pass"
    if tab_switches > 3 or fast_answers > 2:
        verdict = "review_needed"
        
    report["integrity"] = {
        "tab_switches": tab_switches,
        "fast_answer_questions": fast_answers,
        "verdict": verdict
    }
    
    # Cache result in Redis for 1 hour
    await redis_client.set(f"session:{session_id}:report", json.dumps(report), ex=3600)
    
    return report
