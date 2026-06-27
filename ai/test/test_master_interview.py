import asyncio
import json
import sys
import textwrap

from ai.orchestrator import InterviewOrchestrator
from ai.realtime import get_realtime_session
from ai.sandbox import LocalPythonRunner
from ai.test.test_voice import setup_audio

MOCK_RESUME = """
Jane Doe
Location: Kochi, Kerala
Education: B.Tech in Computer Science (Focus on AI/ML and Robotics)
Experience & Projects:
- LeaDi-Screener: Built a multimodal AI system for early detection of learning disabilities using a FastAPI backend, React frontend, and MobileNetV3 for visual analysis.
- Smart Supply Chain: Developed a predictive backend integrating TomTom APIs to forecast delivery disruptions based on real-time traffic data.
- MRDRS (Modular Rapid-Deployment Rescue System): Contributed to a college robotics project involving ESP32-CAM and motor drivers for a portable winch-based rescue platform.
Skills: Python, FastAPI, Machine Learning, Computer Vision, YOLO, MobileNetV3, Reinforcement Learning, C++.
"""

JOB_DESCRIPTION = "Junior AI & Robotics Software Engineer. Must have experience with Python backends and computer vision models."


async def run_master_pipeline():
    print("==================================================")
    print("🎓 THE ULTIMATE CAPSTONE DEMO: FULL INTERVIEW")
    print("==================================================\n")

    orchestrator = InterviewOrchestrator()

    # ---------------------------------------------------------
    # PHASE 0: RESUME PARSING & PLAN GENERATION
    # ---------------------------------------------------------
    print("📄 PHASE 0: AI Analyzing Resume...")
    profile = await orchestrator.extract_profile(MOCK_RESUME)
    inferred_skills = profile.get("inferred_target_skills", ["Python", "Algorithms"])

    print(f"✅ Extracted Skills: {inferred_skills}")

    plan = await orchestrator.generate_interview_plan(MOCK_RESUME, JOB_DESCRIPTION)

    first_question = (
        plan[0]["base_question"]
        if plan
        else "Tell me about your experience with FastAPI."
    )

    speaker_queue, mic_queue = setup_audio()

    # ---------------------------------------------------------
    # PHASE 1: Q&A (Behavioral / Technical Warm-up)
    # ---------------------------------------------------------
    print("\n🗣️ PHASE 1: Technical Q&A")
    system_prompt = (
        "You are a technical interviewer for an AI engineering role. "
        "Start by warmly welcoming the candidate, then ask them this specific question based on their resume: "
        f"'{first_question}'. "
        "Keep your responses strictly to one short sentence."
    )

    session = get_realtime_session("master_demo", system_prompt, turns=99)

    async def on_audio(chunk: bytes):
        speaker_queue.put(chunk)

    session.on_audio_to_frontend = on_audio

    print("🔗 Connecting Voice Edge...")
    await session.connect()

    async def stream_mic():
        while True:
            chunk = await mic_queue.get()
            await session.send_user_audio(chunk, end_of_stream=False)

    mic_task = asyncio.create_task(stream_mic())

    print("\n✅ AI is listening! (Answer their warm-up question)")

    # ---------------------------------------------------------
    # SKIPPABLE PHASE 1 WAIT
    # ---------------------------------------------------------
    try:
        await asyncio.to_thread(
            input,
            "\n⚠️  Press ENTER (or Ctrl+C) when you are ready to move to the Coding Challenge...\n",
        )
    except (KeyboardInterrupt, asyncio.CancelledError, EOFError):
        print("\n\n⏸️ Q&A Interrupted! Moving directly to the coding phase...\n")

    # ---------------------------------------------------------
    # PHASE 2: DYNAMIC PROBLEM GENERATION
    # ---------------------------------------------------------
    print("\n🧠 PHASE 2: Generating Coding Challenge...")
    challenge = await orchestrator.generate_coding_challenge(inferred_skills)
    question_text = challenge.get(
        "base_question", "Write a Python function to solve this."
    )

    print(f"\n📝 PROBLEM: {challenge.get('title')}")
    print(f"{question_text}\n")

    # ---------------------------------------------------------
    # PHASE 3: VOICE PAIR-PROGRAMMING & LIVE CODING
    # ---------------------------------------------------------
    print("🗣️ PHASE 3: Voice Pair-Programming")
    print("✅ Mic is still HOT! Talk to the AI about how you'd solve this new problem.")

    await session.send_user_text(
        f"[SYSTEM NOTE: The interview has transitioned to the coding phase. "
        f"The candidate is now looking at this problem: {question_text}. "
        f"Ask them how they plan to approach it. Keep it brief.]"
    )

    print("\n💻 LIVE TERMINAL CODE EDITOR")
    print("Type or paste your Python solution below.")
    print(">>> WHEN FINISHED: Press Ctrl+Z (Win) or Ctrl+D (Mac/Linux) + ENTER.")
    print(
        ">>> OR hit Ctrl+C to instantly submit whatever is written and end the interview."
    )

    def get_multiline_code():
        try:
            return sys.stdin.read()
        except KeyboardInterrupt:
            return ""

    actual_user_code = ""

    # ---------------------------------------------------------
    # SKIPPABLE PHASE 3 WAIT
    # ---------------------------------------------------------
    try:
        actual_user_code = await asyncio.to_thread(get_multiline_code)
    except (KeyboardInterrupt, asyncio.CancelledError, EOFError):
        print("\n\n⏹️ Coding Phase Interrupted! Submitting what we have...")

    if not actual_user_code or not actual_user_code.strip():
        actual_user_code = "def solve(*args, **kwargs):\n    pass"

    print("\n⏹️ Submitting Code and closing mic...")
    mic_task.cancel()
    await session.close()
    speaker_queue.put(None)

    # ---------------------------------------------------------
    # PHASE 4: EXECUTION & EVALUATION
    # ---------------------------------------------------------
    print("\n🧪 PHASE 4: AI Generating Tests, Executing, and Grading...")

    review = await orchestrator.evaluate_code_submission(
        question_text=question_text,
        source_code=actual_user_code,
        transcript_history=session.history,
    )

    print("==================================================")
    print("🏆 FINAL SCORECARD")
    print("==================================================")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    try:
        # On Windows, we use a custom event loop policy to prevent "Proactor" socket errors on shutdown
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(run_master_pipeline())
    except KeyboardInterrupt:
        # Silently catch the delayed Ctrl+C signal during teardown
        pass
    except Exception:
        pass
    finally:
        print("\n👋 Interview session closed cleanly.")
