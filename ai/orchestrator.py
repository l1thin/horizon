import json
import re

from ai.config import Config
from ai.embeddings import compute_skill_gap_vectors, rank_gaps
from ai.providers import get_text_provider
from ai.realtime.base_session import BaseRealtimeSession
from ai.realtime.session_gemini import GeminiRealtimeSession
from ai.realtime.session_openai import OpenAIRealtimeSession


class InterviewOrchestrator:
    def __init__(self):
        self.text_provider = get_text_provider()

    @staticmethod
    def _extract_clean_json(raw_text: str) -> str:
        """Safely extracts JSON objects or arrays even if buried inside markdown filler text."""
        text = raw_text.strip()
        # Find anything trapped inside markdown code fences first
        fence_match = re.search(
            r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE
        )
        if fence_match:
            return fence_match.group(1).strip()

        # Fallback: Find the first '[' or '{' and the last ']' or '}'
        first_idx = min(
            [idx for idx in [text.find("{"), text.find("[")] if idx != -1], default=-1
        )
        last_idx = max(text.rfind("}"), text.rfind("]"))

        if first_idx != -1 and last_idx != -1 and last_idx >= first_idx:
            return text[first_idx : last_idx + 1].strip()
        return text

    async def generate_interview_plan(
        self, resume_text: str, job_description: str = ""
    ) -> list[dict]:

        system_prompt = """
        You are an expert technical recruiter. Based on the provided resume,
                generate a 5-question interview plan.
                Output ONLY a valid JSON array of objects with 'question_type' (e.g., 'technical', 'behavioral', 'project')
                and 'base_question' (the actual question to ask).
        """

        user_message = f"Resume Text:\n{resume_text}\n\nJob Context:\n{job_description}"

        raw_response = await self.text_provider.generate_text(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=1500,
        )

        try:
            clean_json = self._extract_clean_json(raw_response)
            return json.loads(clean_json)
        except json.JSONDecodeError:
            print(f"Failed to parse interview plan: {raw_response}")
            return []

    def create_voice_session(
        self, session_id: str, current_question: str, accumulated_fact: dict
    ) -> BaseRealtimeSession:

        facts_string = json.dumps(accumulated_fact, indent=2)

        system_prompt = f"""
                You are a conversational technical interviewer for Horizon.

                YOUR CURRENT GOAL: Ask the following question and evaluate the candidate's answer through a natural conversation.
                Question: "{current_question}"

                CANDIDATE CONTEXT (Facts extracted from previous questions):
                {facts_string}

                RULES:
                1. Keep responses concise (1-2 sentences).
                2. Do not sound robotic. React naturally to what they say.
                3. If they mention a technology listed in their context, weave it into your follow-ups!
                """

        provider = Config.VOICE_PROVIDER
        if provider == "openai":
            return OpenAIRealtimeSession(session_id, system_prompt, turns=3)
        elif provider == "gemini":
            return GeminiRealtimeSession(session_id, system_prompt, turns=3)
        else:
            raise ValueError("Unsupported Realtime Provider configured.")

    async def extract_facts_from_transcript(self, transcript: list[dict]) -> dict:
        system_prompt = """
        You are analyzing an interview transcript to build a candidate skill profile.
                    IMPORTANT: Only extract technologies, frameworks, or methodologies that the CANDIDATE
                    (role: "user") explicitly claimed to have experience with in their own words.
                    Completely ignore anything said by the interviewer (role: "model" or "assistant") —
                    the interviewer's questions must never be a source of extracted skills.
                    If the candidate said nothing or gave no substantive answer, return {"new_skills_mentioned": []}.
                    Output ONLY a JSON object like {"new_skills_mentioned": ["React", "FastAPI"]}
            """

        # Convert the array of dicts into a readable string
        transcript_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in transcript]
        )

        raw_response = await self.text_provider.generate_text(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": transcript_text}],
            max_tokens=500,
        )

        try:
            clean_json = self._extract_clean_json(raw_response)
            return json.loads(clean_json)
        except json.JSONDecodeError:
            return {"new_skills_mentioned": []}

    async def evaluate_single_transcript(
        self, question_text: str, question_type: str, transcript: list[dict]
    ) -> dict:
        """Evaluates a single discrete session's transcript on a strict 0-10 scale."""
        system_prompt = """
        You are a strict, calibrated interview evaluation engine for Horizon.
        Analyze the candidate's spoken answers against the interviewer's question.

        SCORING GUIDE:
        0-2  -> Off-topic, inaccurate, or refused to answer.
        3-4  -> Surface level, missed core technical trade-offs.
        5-6  -> Adequate, but lacked concrete project examples or architectural depth.
        7-8  -> Strong, clear grounding in real-world engineering constraints.
        9-10 -> Exceptional, mastery of edge cases and precise domain terminology.

        Output ONLY valid JSON matching this schema:
        {
            "score": float (0.0 to 10.0),
            "depth_rating": "surface" | "adequate" | "deep",
            "key_strengths": [string],
            "critical_missing_points": [string],
            "demonstrated_skills": [string]
        }
        """

        transcript_str = "\n".join(
            [f"{m['role'].upper()}: {m['content']}" for m in transcript]
        )
        user_msg = f"Target Question ({question_type.upper()}): {question_text}\n\nTranscript:\n{transcript_str}"

        raw_resp = await self.text_provider.generate_text(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=800,
        )

        try:
            return json.loads(self._extract_clean_json(raw_resp))
        except Exception as e:
            # Documented explicit fallback instead of a silent bare swallow!
            print(
                f"[EVALUATION ERROR] Failed to score transcript: {e}\nRaw: {raw_resp}"
            )
            return {
                "score": 0.0,
                "depth_rating": "surface",
                "key_strengths": [],
                "critical_missing_points": [
                    "Evaluation engine failed to parse transcript."
                ],
                "demonstrated_skills": [],
            }

    async def generate_final_scorecard(
        self, session_transcripts: list[dict], target_job_skills: list[str]
    ) -> dict:
        """
        Executes Step 4 (Scoring) and Step 5 (Vector Embedding Skill Gaps) across the entire interview.
        `session_transcripts` format: [{'question': str, 'type': str, 'history': list[dict]}]
        """
        import asyncio

        # 1. Concurrently evaluate all discrete question sessions
        eval_tasks = [
            self.evaluate_single_transcript(
                item["question"], item["type"], item["history"]
            )
            for item in session_transcripts
        ]
        evaluations = await asyncio.gather(*eval_tasks)

        # 2. Aggregate scores and all uncovered candidate skills
        total_score = sum(ev["score"] for ev in evaluations)
        overall_score = round(total_score / max(len(evaluations), 1), 1)

        uncovered_skills = set()
        for ev in evaluations:
            uncovered_skills.update(ev.get("demonstrated_skills", []))

        # 3. Step 5: True Mathematical Vector Embedding Gap Analysis
        # Passes text claims into embeddings.py to run cosine similarity math!
        raw_vector_gaps = await compute_skill_gap_vectors(
            candidate_skills=list(uncovered_skills), required_skills=target_job_skills
        )
        top_skill_gaps = rank_gaps(raw_vector_gaps, threshold=0.3)[:3]

        return {
            "overall_interview_score": overall_score,
            "question_breakdowns": evaluations,
            "uncovered_candidate_skills": list(uncovered_skills),
            "top_3_vector_skill_gaps": top_skill_gaps,
        }
