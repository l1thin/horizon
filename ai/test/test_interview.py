# test_interview.py
import asyncio
import json  # <-- Added for pretty-printing the scorecard
import os
import queue
import threading

import pyaudio
from PyPDF2 import PdfReader

from ai.config import Config
from ai.orchestrator import InterviewOrchestrator

# Gemini Live outputs PCM16 at 24kHz mono
SAMPLE_RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16


def rip_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])


def make_audio_player():
    """Spin up a background thread that drains a queue and plays PCM16 audio."""
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        output=True,
        frames_per_buffer=1024,
    )
    audio_queue = queue.Queue()

    def _player():
        while True:
            chunk = audio_queue.get()
            if chunk is None:
                break
            stream.write(chunk)
        stream.stop_stream()
        stream.close()
        p.terminate()

    t = threading.Thread(target=_player, daemon=True)
    t.start()
    return audio_queue, t


async def run_master_test():
    print(
        f"--- 🧪 INITIALIZING CAPSTONE TEST HARNESS ({Config.VOICE_PROVIDER.upper()} MODE) ---"
    )
    orchestrator = InterviewOrchestrator()

    resume_path = "./ai/test/resume.pdf"
    if not os.path.exists(resume_path):
        # Fallback to root directory if not in test folder
        resume_path = "resume.pdf"
        if not os.path.exists(resume_path):
            print("❌ Error: Please drop a 'resume.pdf' in the directory!")
            return

    print("📄 1. Ripping resume text...")
    raw_resume = rip_pdf(resume_path)

    print(f"🧠 2. {Config.TEXT_PROVIDER.upper()} is generating the interview plan...")
    plan = await orchestrator.generate_interview_plan(raw_resume)

    if not plan or not isinstance(plan, list):
        print("⚠️  Plan generation failed — using fallback questions.")
        plan = [
            {
                "question_type": "technical",
                "base_question": "Explain a complex architectural decision you made.",
            },
            {
                "question_type": "behavioral",
                "base_question": "Tell me about a time a project was failing.",
            },
        ]

    print(f"✅ Generated {len(plan)} questions.")

    accumulated_brain_state = {}

    # NEW: Keep a master record of all transcripts for the final scorecard
    all_session_transcripts = []

    # Running just 2 questions for the test simulation
    for idx, q_data in enumerate(plan[:2]):
        q_text = q_data.get("base_question", "Tell me about your background.")
        q_type = q_data.get("question_type", "general")
        s_id = f"horizon_session_q{idx + 1}"

        print("\n=========================================================")
        print(f" 🚀 SESSION {idx + 1} [{q_type.upper()}]")
        print(f" Question: {q_text}")
        print(f" AI Knowledge So Far: {accumulated_brain_state}")
        print("=========================================================")

        session = orchestrator.create_voice_session(
            s_id, q_text, accumulated_brain_state, 3
        )

        bytes_received = 0
        phase_done = asyncio.Event()
        ai_turn_done = asyncio.Event()
        audio_queue, player_thread = make_audio_player()

        async def on_audio(chunk: bytes, _q=audio_queue):
            nonlocal bytes_received
            bytes_received += len(chunk)
            _q.put_nowait(chunk)
            print(f" 🔊 [AI Audio] {bytes_received} bytes streamed...", end="\r")

        async def on_turn(ev=ai_turn_done):
            ev.set()

        async def on_end(history, _ev=phase_done, _tev=ai_turn_done):
            print("\n ⏹️  Phase complete — turn limit reached.")
            _ev.set()
            _tev.set()

        session.on_audio_to_frontend = on_audio
        session.on_turn_complete = on_turn
        session.on_phase_complete = on_end

        print(f"🔗 Connecting to {Config.VOICE_PROVIDER} edge server...")
        await session.connect()
        print("✅ Connected!\n")

        print(" 🤖 Triggering AI to ask the question...")
        ai_turn_done.clear()  # Clear before speaking
        await session.send_user_text("I am ready. Please ask the question.")

        turn_counter = 1
        while not phase_done.is_set() and turn_counter < 3:
            print("\n ⏳ Waiting for AI to finish speaking...")

            try:
                await asyncio.wait_for(ai_turn_done.wait(), timeout=30)
            except asyncio.TimeoutError:
                print("\n⚠️  AI took too long — prompting anyway.")

            if phase_done.is_set():
                break

            print(
                f"\n 🎤 [TURN {turn_counter}] Your answer (or 'quit' to end session):"
            )
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, " You: "
                )
            except EOFError:
                break

            if user_input.strip().lower() in ["quit", "exit"]:
                break

            if not user_input.strip():
                print(" (empty input — please type your answer)")
                continue

            ai_turn_done.clear()  # Clear before speaking
            await session.send_user_text(user_input)
            turn_counter += 1

        # Clean shutdown
        await session.close()

        audio_queue.put(None)
        player_thread.join(timeout=5)

        # NEW: Save this session's transcript for the final evaluation
        all_session_transcripts.append(
            {"question": q_text, "type": q_type, "history": session.history}
        )

        print(f"\n 🧬 Extracting facts ({len(session.history)} transcript messages)...")
        extracted_facts = await orchestrator.extract_facts_from_transcript(
            session.history
        )
        accumulated_brain_state.update(extracted_facts)
        print(f" 🧠 Acquired: {extracted_facts}")

    print("\n=========================================================")
    print(" 📊 INTERVIEW COMPLETE. GENERATING FINAL SCORECARD...")
    print(" Running NLP evaluations and Vector Embedding Skill Gap Analysis...")
    print("=========================================================\n")

    # Define the mock skills required for the job we are interviewing for
    target_job_skills = [
        "Python",
        "Machine Learning",
        "FastAPI",
        "React",
        "System Architecture",
        "Computer Vision",
    ]

    # Run Steps 4 & 5
    final_scorecard = await orchestrator.generate_final_scorecard(
        session_transcripts=all_session_transcripts, target_job_skills=target_job_skills
    )

    print(json.dumps(final_scorecard, indent=2))
    print(
        "\n🏆 MASTER HARNESS TEST COMPLETE! THE HORIZON AI ENGINE IS FULLY OPERATIONAL."
    )


if __name__ == "__main__":
    asyncio.run(run_master_test())
