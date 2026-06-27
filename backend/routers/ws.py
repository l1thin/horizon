# Horizon - ws.py - owned by Dev 2 (Backend)
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ai.orchestrator import InterviewOrchestrator

router = APIRouter()

from db.redis import get_redis_client as get_redis

# Placeholder dependencies and DB functions
async def save_raw_answer(session_id: str, question_id: str, payload: dict):
    """Append raw answer to the session's answer list in the in-memory store."""
    redis = get_redis()
    raw = await redis.get(f"session:{session_id}:raw_answers")
    answers = json.loads(raw) if raw else []
    answers.append({"question_id": question_id, **payload})
    await redis.set(f"session:{session_id}:raw_answers", json.dumps(answers), ex=7200)

async def save_raw_code_answer(session_id: str, question_id: str, payload: dict):
    """Append raw code answer to the session's answer list in the in-memory store."""
    redis = get_redis()
    raw = await redis.get(f"session:{session_id}:raw_answers")
    answers = json.loads(raw) if raw else []
    answers.append({"question_id": question_id, "type": "coding", **payload})
    await redis.set(f"session:{session_id}:raw_answers", json.dumps(answers), ex=7200)

async def store_report(session_id: str, evaluated: list):
    """Store the evaluated report in the in-memory store so the report endpoint can serve it."""
    redis = get_redis()
    await redis.set(f"session:{session_id}:report", json.dumps(evaluated), ex=7200)

@router.websocket("/ws/session/{session_id}")
async def session_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    redis = get_redis()
    
    # Load question plan from Redis
    raw = await redis.get(f"session:{session_id}:questions")
    if not raw:
        await websocket.send_json({"type": "error", "payload": {"message": "Session not found or not ready"}})
        await websocket.close()
        return

    questions = json.loads(raw)
    q_index = 0
    pending_follow_up = None  # set when follow_up should be injected next
    raw_answers = []          # collected for post-session eval

    try:
        while True:
            # Determine the current question (might be a follow-up)
            if pending_follow_up:
                current_q = pending_follow_up
                pending_follow_up = None
                state = "QUESTION"
            else:
                if q_index >= len(questions):
                    # All questions done → trigger post-session eval + report
                    state = "REPORT"
                else:
                    current_q = questions[q_index]
                    state = "QUESTION"

            if state == "QUESTION":
                await websocket.send_json({
                    "type": current_q.get("type", "question"),  # "question", "follow_up", or "coding"
                    "payload": {
                        "question_id": current_q["id"],
                        "text": current_q["text"],
                        "question_type": current_q.get("type", "question"),
                        "index": q_index + 1,
                        "total": len(questions),
                        "time_limit_seconds": current_q.get("time_limit_seconds", 300) if current_q.get("type") == "coding" else None
                    }
                })

            elif state == "REPORT":
                # Run evaluation as a background task (non-blocking)
                asyncio.create_task(run_post_session_eval(session_id, raw_answers, redis))
                await websocket.send_json({"type": "end", "payload": {"session_id": session_id}})
                break

            # Wait for client answer
            msg = await websocket.receive_json()

            if msg.get("type") == "answer":
                payload = msg.get("payload", {})
                raw_answers.append({
                    "question_id": current_q["id"],
                    "question_text": current_q["text"],
                    "question_type": current_q.get("type", "question"),
                    "transcript": payload.get("transcript", ""),
                    "integrity": payload.get("integrity", {})
                })
                # Save raw answer to DB (no eval yet)
                await save_raw_answer(session_id, current_q["id"], payload)

                # Check if follow-up should be injected
                follow_up_text = current_q.get("follow_up")
                integrity = payload.get("integrity", {})
                should_inject = (
                    integrity.get("think_time_ms", 9999) < 2000 or
                    integrity.get("tab_switches", 0) > 0
                )
                if follow_up_text and should_inject and not pending_follow_up:
                    pending_follow_up = {
                        "id": f"{current_q['id']}_followup",
                        "type": "follow_up",
                        "text": follow_up_text,
                        "criteria": current_q.get("criteria", {}),
                        "follow_up": None
                    }
                else:
                    q_index += 1  # only advance if no follow-up injected

                # Acknowledge to client
                await websocket.send_json({"type": "eval_ack", "payload": {"question_id": current_q["id"]}})

            elif msg.get("type") == "code_submit":
                payload = msg.get("payload", {})
                raw_answers.append({
                    "question_id": current_q["id"],
                    "question_text": current_q["text"],
                    "question_type": "coding",
                    "code": payload.get("code", ""),
                    "language": payload.get("language"),
                    "timed_out": payload.get("timed_out", False)
                })
                await save_raw_code_answer(session_id, current_q["id"], payload)
                q_index += 1
                await websocket.send_json({"type": "eval_ack", "payload": {"question_id": current_q["id"]}})

    except WebSocketDisconnect:
        # Save current state so client can reconnect
        await redis.set(f"session:{session_id}:q_index", q_index, ex=3600)
        await redis.set(f"session:{session_id}:raw_answers", json.dumps(raw_answers), ex=3600)
    except Exception as e:
        # Attempt to inform the client of an error if the connection is still alive
        try:
            await websocket.send_json({"type": "error", "payload": {"message": str(e)}})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

async def run_post_session_eval(session_id: str, raw_answers: list, redis):
    """Runs after WS closes. Calls Dev 3's generate_final_scorecard and stores report."""
    try:
        orchestrator = InterviewOrchestrator()
        
        # Retrieve target skills
        target_skills_raw = await redis.get(f"session:{session_id}:target_skills")
        if target_skills_raw:
            target_skills = json.loads(target_skills_raw)
        else:
            target_skills = []
            
        session_transcripts = []
        for ans in raw_answers:
            session_transcripts.append({
                "question": ans["question_text"],
                "type": ans["question_type"],
                "history": [{"role": "user", "content": ans.get("transcript", "")}]
            })
            
        evaluated = await orchestrator.generate_final_scorecard(
            session_transcripts, 
            target_job_skills=target_skills
        )
        
        await store_report(session_id, evaluated)
        await redis.set(f"session:{session_id}:status", "report_ready")
    except Exception as e:
        await redis.set(f"session:{session_id}:eval_error", str(e))
