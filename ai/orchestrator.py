import json
import re

from ai.config import Config
from ai.embeddings import compute_skill_gap_vectors, rank_gaps
from ai.piston import PistonExecutor
from ai.providers import get_text_provider
from ai.realtime import get_realtime_session
from ai.realtime.base_session import BaseRealtimeSession
from ai.sandbox import LocalPythonRunner


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
        self,
        session_id: str,
        current_question: str,
        accumulated_fact: dict,
        turns: int,
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

        provider = get_realtime_session(session_id, system_prompt, turns=turns)
        return provider

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

    async def extract_profile(self, resume_text: str) -> dict:
        system_prompt = """
        You are an expert resume parser for Horizon, an AI interview platform.
        Extract the candidate's profile information from the provided resume text.

        CRITICAL: Based on their current role and experience, infer the core technical
        requirements for the job they are likely interviewing for and list them under 'inferred_target_skills'.

        Output ONLY valid JSON matching this schema:
        {
          "name": "string or null",
          "current_role": "string or null",
          "years_of_experience": "number or null",
          "candidate_skills": ["string"],
          "inferred_target_skills": ["string"]
        }
        """

        raw_response = await self.text_provider.generate_text(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": resume_text}],
            max_tokens=1000,
        )

        try:
            clean_json = self._extract_clean_json(raw_response)
            return json.loads(clean_json)
        except Exception as e:
            print(f"Profile extraction failed: {e}")
            return {
                "name": "Error Profile",
                "current_role": "Error Profile",
                "years_of_experience": 0,
                "candidate_skills": [],
                "inferred_target_skills": [],
            }

    async def generate_coding_challenge(self, inferred_skills: list[str]) -> dict:

        skills_str = ", ".join(inferred_skills) if inferred_skills else ""

        system_prompt = f"""
        You are a Senior Engineering Manager. Generate ONE medium-difficulty coding challenge
                that tests algorithmic thinking, relevant to these skills: {skills_str}.

                The starter code MUST use a function named exactly `solve`.

                Output ONLY valid JSON matching this schema:
                {{
                  "question_type": "coding",
                  "title": "string (e.g., 'LRU Cache Implementation')",
                  "base_question": "string (Full problem description and constraints)",
                  "starter_code": "def solve(data):\n    # Write your solution here\n    pass\n"
                }}
        """

        raw_response = await self.text_provider.generate_text(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": "Generate the coding challeng."}],
            max_tokens=800,
        )

        try:
            return json.loads(self._extract_clean_json(raw_response))
        except Exception:
            return {
                "question_type": "coding",
                "title": "Two Sum",
                "base_question": "Given an array of integers and a target, return the indices of the two numbers that add up to the target.",
                "starter_code": "def solve(nums, target):\n    pass\n",
            }

    async def _generate_dynamic_tests(self, question_text: str) -> str:
        system_prompt = """
        You are a QA Automation Engineer. I will give you a coding problem description.
                The candidate's solution will be a Python function named `solve`.

                Write exactly 5 standard Python `assert` statements to test edge cases, standard cases, and null cases.
                Wrap them in a basic try/except block that prints 'ALL TESTS PASSED' if successful.

                Output ONLY plain Python code. NO explanations. NO markdown formatting.
        """

        raw_resp = await self.text_provider.generate_text(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": f"Problem: {question_text}"}],
            max_tokens=500,
        )

        clean_code = raw_resp.replace("```python", "").replace("```", "").strip()
        return clean_code

    async def evaluate_code_submission(
        self,
        question_text: str,
        source_code: str,
        transcript_history: list[dict],
        language: str = "python",
    ) -> dict:

        test_suite_code = await self._generate_dynamic_tests(question_text)

        full_execution_code = "\n".join(
            [source_code, "\n# --- AI GENERATED TESTS ---", test_suite_code]
        )

        piston_result = await LocalPythonRunner.run_code(language, full_execution_code)

        system_prompt = """
                You are a Senior Staff Engineer evaluating a candidate's coding interview.
                You will receive the problem, their code, the sandbox execution results,
                and their spoken transcript explaining their thought process.

                Analyze for:
                1. Correctness (Did it pass the tests?)
                2. Time/Space Complexity (Big-O)
                3. Communication (Did they explain their logic clearly in the transcript?)

                Output ONLY valid JSON:
                {
                  "score": float (0.0 to 10.0),
                  "passed_tests": boolean,
                  "time_complexity": "string",
                  "space_complexity": "string",
                  "feedback": "string (1-2 sentences)",
                  "optimal_solution_hint": "string (How could it be improved?)"
                }
                """

        transcript_str = "\n".join(
            [f"{m['role'].upper()}: {m['content']}" for m in transcript_history]
        )
        user_msg = f"PROBLEM:\n{question_text}\n\nCODE:\n{source_code}\n\nSANDBOX RESULT:\n{piston_result}\n\nTRANSCRIPT:\n{transcript_str}"

        raw_resp = await self.text_provider.generate_text(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=1000,
        )

        try:
            review_json = json.loads(self._extract_clean_json(raw_resp))
            review_json["execution_output"] = piston_result["output"]
            return review_json
        except Exception as e:
            print(f"[CODE EVAL ERROR] {e}")
            return {
                "score": 0.0,
                "feedback": "Evaluation engine failed.",
                "passed_tests": False,
            }

    def create_coding_voice_session(
        self, session_id: str, coding_challenge: dict, accumulated_fact: dict
    ) -> BaseRealtimeSession:
        """Spins up a specialized voice session designed to pair-program with the candidate."""
        facts_string = json.dumps(accumulated_fact, indent=2)

        q_title = coding_challenge.get("title", "Coding Challenge")
        q_desc = coding_challenge.get("base_question", "")

        system_prompt = f"""
            You are a Senior Engineering Manager conducting the coding portion of the Horizon interview.

            YOUR CURRENT GOAL: Introduce the coding challenge and act as a pair-programming interviewer.
            The problem text is already visible on the candidate's screen in a code editor.

            Problem Title: "{q_title}"
            Problem Description: "{q_desc}"

            RULES FOR THIS PHASE:
            1. Keep your introduction brief (1-2 sentences).
            2. Ask them to explain their algorithmic approach out loud before they start typing.
            3. If they get stuck or ask for help, offer Socratic hints (ask guiding questions), DO NOT write the code for them.
            4. Remind them to think about Time and Space Complexity.
            5. Acknowledge that when they click submit, their code will run against hidden test cases.
            6. Always uses English as means of communication.
            
            CANDIDATE CONTEXT (from previous rounds):
            {facts_string}
            """

        return get_realtime_session(session_id, system_prompt, turns=14)
