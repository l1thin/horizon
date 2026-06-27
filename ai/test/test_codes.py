import asyncio
import json
import textwrap

# Import your working components
from ai.orchestrator import InterviewOrchestrator
from ai.realtime import get_realtime_session
from ai.sandbox import LocalPythonRunner
from ai.test.test_voice import setup_audio  # Your working mic/speaker setup


async def run_full_pipeline():
    print("==================================================")
    print("🚀 CAPSTONE DEMO: FULL INTERVIEW PIPELINE")
    print("==================================================\n")

    orchestrator = InterviewOrchestrator()

    # ---------------------------------------------------------
    # PHASE 1: GENERATE CHALLENGE
    # ---------------------------------------------------------
    print("🧠 1. Generating Coding Challenge...")
    challenge = await orchestrator.generate_coding_challenge(
        ["Python", "Data Structures"]
    )
    question_text = challenge.get("base_question", "")

    print(f"\n📝 PROBLEM: {challenge.get('title')}")
    print(f"{question_text}\n")

    # ---------------------------------------------------------
    # PHASE 2: LIVE VOICE INTERVIEW
    # ---------------------------------------------------------
    print("🎙️ 2. Starting Voice Interview...")
    speaker_queue, mic_queue = setup_audio()

    # Give the AI context about the problem it just generated
    system_prompt = f"You are a technical interviewer. You just gave the candidate this problem: {question_text}. Keep responses short."

    # FIX: Use the factory method that works in your voice test
    session = get_realtime_session("demo_session", system_prompt, turns=99)

    # FIX: Use an async callback so the Gemini receive loop doesn't crash
    async def on_audio(chunk: bytes):
        speaker_queue.put(chunk)

    session.on_audio_to_frontend = on_audio

    await session.connect()

    async def stream_mic():
        print("✅ Mic is HOT! Talk to the AI about how you'd solve it.")
        print("⚠️  Press Ctrl+C when you are ready to 'Submit' your code.\n")
        while True:
            chunk = await mic_queue.get()
            await session.send_user_audio(chunk, end_of_stream=False)

    mic_task = asyncio.create_task(stream_mic())

    try:
        # Keep voice running until you press Ctrl+C
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n⏹️ Voice Interview ended. Submitting Code...\n")
    finally:
        mic_task.cancel()
        await session.close()
        speaker_queue.put(None)  # Stop speaker thread

    # ---------------------------------------------------------
    # PHASE 3: CODE EXECUTION & EVALUATION
    # ---------------------------------------------------------
    print("🧪 3. Generating Hidden Test Cases...")
    ai_generated_tests = await orchestrator._generate_dynamic_tests(question_text)

    # Mocking what the user typed into the browser IDE
    mock_user_code = textwrap.dedent("""
    def solve(nums, target):
        num_dict = {}
        for i, num in enumerate(nums):
            if target - num in num_dict:
                return [num_dict[target - num], i]
            num_dict[num] = i
        return []
    """)

    full_execution_code = "\n".join(
        [mock_user_code, "\n# --- AI TESTS ---", ai_generated_tests]
    )

    print("🚀 4. Executing Code in Local Sandbox...")
    piston_result = await LocalPythonRunner.run_code("python", full_execution_code)
    print(f"Sandbox Output: {piston_result.get('output').strip()}\n")

    print("🧐 5. AI Grading the Submission...")
    review = await orchestrator.evaluate_code_submission(
        question_text=question_text,
        source_code=mock_user_code,
        transcript_history=session.history,  # Pass the voice transcript for context!
    )

    print("==================================================")
    print("🏆 FINAL SCORECARD")
    print("==================================================")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    asyncio.run(run_full_pipeline())
