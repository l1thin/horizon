# test_ws_voice.py
import asyncio
import queue
import threading

import pyaudio

from ai.config import Config
from ai.realtime import get_realtime_session

# Gemini Live outputs PCM16 at 24kHz mono
SAMPLE_RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16


def make_audio_player():
    """Returns (audio_queue, player_thread). Push bytes onto the queue to play."""
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


async def main():
    print(f"--- 🔌 Testing Generalized WebSocket ({Config.VOICE_PROVIDER.upper()}) ---")

    prompt = """
    You are an AI interviewer testing a voice downlink.
    Acknowledge what the user says, tell them their mic works, and keep it to one short sentence.
    """

    session = get_realtime_session(
        "test_voice_01", system_prompt=prompt, max_phase_turns=1
    )

    audio_byte_counter = 0
    audio_queue, player_thread = make_audio_player()
    phase_done = asyncio.Event()

    async def handle_audio_stream(chunk: bytes):
        nonlocal audio_byte_counter
        audio_byte_counter += len(chunk)
        audio_queue.put_nowait(chunk)  # play it in real time
        print(
            f"🔊 [WS DOWNLINK] Streamed {audio_byte_counter} total raw audio bytes...",
            end="\r",
        )

    async def handle_turn_end(history):
        print("\n\n✅ [WS EVENT] Turn finalized. Transcript:")
        for msg in history:
            print(f"   ({msg['role']}): {msg['content']}")
        phase_done.set()

    session.on_audio_to_frontend = handle_audio_stream
    session.on_phase_complete = handle_turn_end

    print(f"Connecting to {Config.VOICE_PROVIDER} edge server...")
    await session.connect()
    print("Connection established!")

    print("\nSending initial test message to wake up the AI...")
    await session.send_user_text("Hello system, testing the downlink.")

    print("Waiting for AI to finish speaking (up to 10 seconds)...")
    try:
        await asyncio.wait_for(phase_done.wait(), timeout=10)
    except asyncio.TimeoutError:
        print("\n⚠️  Timeout — no turn_complete received within 10s.")

    await session.close()

    # Drain the audio queue so the last chunk finishes playing
    audio_queue.put(None)
    player_thread.join(timeout=5)

    print(f"\n🎉 Test complete! Piped {audio_byte_counter} bytes of PCM16 audio.")


if __name__ == "__main__":
    asyncio.run(main())
