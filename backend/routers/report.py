# Horizon - report.py - owned by Dev 2 (Backend)
import json
import asyncio
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()

from db.redis import get_redis_client as get_redis


def _transform_report_for_frontend(raw_report: dict, questions_meta: list, raw_answers: list) -> dict:
    """
    Transforms the orchestrator's generate_final_scorecard output into the
    format expected by the frontend FeedbackDashboard component.
    
    Backend format:
        overall_interview_score, question_breakdowns[], top_3_vector_skill_gaps[]
    Frontend format:
        overall_score, questions[{question_id, question_text, question_type, score, depth_rating, feedback}],
        skill_gaps[{skill, gap_score}], integrity{}
    """
    # Overall score: orchestrator returns 0-10 float, frontend shows as integer 0-100
    overall_raw = raw_report.get("overall_interview_score", 0)
    overall_score = round(overall_raw * 10)

    # Map question breakdowns to frontend format
    breakdowns = raw_report.get("question_breakdowns", [])
    questions = []
    for i, ev in enumerate(breakdowns):
        # Get the matching question metadata if available
        q_meta = questions_meta[i] if i < len(questions_meta) else {}
        
        questions.append({
            "question_id": q_meta.get("id", f"q{i+1}"),
            "question_text": q_meta.get("text", f"Question {i+1}"),
            "question_type": q_meta.get("type", "technical"),
            "score": ev.get("score", 0),
            "depth_rating": ev.get("depth_rating", "surface"),
            "feedback": {
                "what_was_good": ", ".join(ev.get("key_strengths", [])) or "No specific strengths identified.",
                "what_was_missing": ", ".join(ev.get("critical_missing_points", [])) or "No critical gaps identified.",
                "suggestions": ev.get("demonstrated_skills", [])
            }
        })

    # Map skill gaps
    raw_gaps = raw_report.get("top_3_vector_skill_gaps", [])
    skill_gaps = []
    for gap in raw_gaps:
        if isinstance(gap, dict):
            skill_gaps.append({
                "skill": gap.get("skill", gap.get("required_skill", "Unknown")),
                "gap_score": round(gap.get("gap_score", gap.get("distance", 0)) * 10) if gap.get("gap_score", gap.get("distance", 0)) <= 1 else gap.get("gap_score", 0)
            })
        elif isinstance(gap, str):
            skill_gaps.append({"skill": gap, "gap_score": 5})

    # Compute integrity from raw answers
    tab_switches = 0
    fast_answers = 0
    for ans in raw_answers:
        integrity = ans.get("integrity", {})
        if isinstance(integrity.get("tab_switches"), list):
            tab_switches += len(integrity["tab_switches"])
        elif isinstance(integrity.get("tab_switches"), (int, float)):
            tab_switches += int(integrity["tab_switches"])
        if integrity.get("think_time_ms", 9999) < 2000:
            fast_answers += 1

    verdict = "pass"
    if tab_switches > 3 or fast_answers > 2:
        verdict = "review_needed"

    return {
        "overall_score": overall_score,
        "questions": questions,
        "skill_gaps": skill_gaps,
        "integrity": {
            "tab_switches": tab_switches,
            "fast_answer_questions": fast_answers,
            "verdict": verdict
        }
    }


@router.get("/api/sessions/{session_id}/report")
async def get_report(session_id: str, redis_client = Depends(get_redis)):
    # Check for cached/stored report
    cached_report = await redis_client.get(f"session:{session_id}:report")
    
    if not cached_report:
        # Check session status to determine if we should wait
        status = await redis_client.get(f"session:{session_id}:status")
        if isinstance(status, bytes):
            status = status.decode('utf-8')
        
        if status in ("report_ready", "ready"):
            # Evaluation may still be running — poll for up to 10s
            for _ in range(10):
                await asyncio.sleep(1.0)
                cached_report = await redis_client.get(f"session:{session_id}:report")
                if cached_report:
                    break
        
        if not cached_report:
            # Check for evaluation error
            eval_error = await redis_client.get(f"session:{session_id}:eval_error")
            if eval_error:
                error_msg = eval_error.decode('utf-8') if isinstance(eval_error, bytes) else str(eval_error)
                raise HTTPException(status_code=500, detail=f"Evaluation failed: {error_msg}")
            raise HTTPException(status_code=425, detail="Evaluation still in progress")
    
    # Parse the raw report from the orchestrator
    if isinstance(cached_report, bytes):
        cached_report = cached_report.decode('utf-8')
    raw_report = json.loads(cached_report)
    
    # Load question metadata (original questions with ids and text)
    questions_raw = await redis_client.get(f"session:{session_id}:questions")
    questions_meta = json.loads(questions_raw) if questions_raw else []
    
    # Load raw answers for integrity computation
    raw_answers_data = await redis_client.get(f"session:{session_id}:raw_answers")
    if raw_answers_data:
        if isinstance(raw_answers_data, bytes):
            raw_answers_data = raw_answers_data.decode('utf-8')
        raw_answers = json.loads(raw_answers_data)
    else:
        raw_answers = []
    
    # Transform to frontend format
    return _transform_report_for_frontend(raw_report, questions_meta, raw_answers)
