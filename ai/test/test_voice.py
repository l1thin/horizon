import asyncio
import queue
import threading

import pyaudio

from ai.config import Config
from ai.realtime import get_realtime_session

# --- CONFIG ---
CHUNK = 320  # 20ms chunks (16000 * 0.02) - Crucial for low latency
IN_RATE = 16000  # Gemini input requirement
OUT_RATE = 24000  # Gemini output requirement
FORMAT = pyaudio.paInt16
CHANNELS = 1


def setup_audio():
    """Sets up PyAudio threads for non-blocking I/O."""
    p = pyaudio.PyAudio()

    # Speaker Output Stream
    out_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=OUT_RATE,
        output=True,
        frames_per_buffer=CHUNK,
    )
    speaker_queue = queue.Queue()

    def _speaker_worker():
        while True:
            data = speaker_queue.get()
            if data is None:
                break
            out_stream.write(data)

    threading.Thread(target=_speaker_worker, daemon=True).start()

    # Microphone Input Stream
    in_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=IN_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    mic_queue = asyncio.Queue()

    def _mic_worker():
        while True:
            data = in_stream.read(CHUNK, exception_on_overflow=False)
            # Use call_soon_threadsafe to push from thread to async queue
            loop.call_soon_threadsafe(mic_queue.put_nowait, data)

    # We need the loop to be running to access call_soon_threadsafe
    loop = asyncio.get_event_loop()
    threading.Thread(target=_mic_worker, daemon=True).start()

    return speaker_queue, mic_queue


async def run_audio_test():
    print(f"--- 🎙️ FULL-DUPLEX LIVE MICROPHONE TEST ---")
    speaker_queue, mic_queue = setup_audio()

    # Initialize your session
    session = get_realtime_session(
        "audio_test_01",
        "You are a helpful AI interviewer. Keep answers very short.",
        turns=99,
    )

    # 🔊 PLAYBACK HANDLER: Send incoming bytes to the speaker queue
    async def on_audio(chunk: bytes):
        speaker_queue.put(chunk)

    session.on_audio_to_frontend = on_audio

    print("🔗 Connecting...")
    await session.connect()

    # 🎙️ MIC HANDLER: Stream bytes to Gemini
    async def stream_mic():
        print("✅ Mic is HOT. Start talking! (Press Ctrl+C to exit)\n")
        while True:
            chunk = await mic_queue.get()
            # Send continuous stream
            await session.send_user_audio(chunk, end_of_stream=False)

    mic_task = asyncio.create_task(stream_mic())

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down...")
    finally:
        mic_task.cancel()
        await session.close()
        speaker_queue.put(None)


if __name__ == "__main__":
    asyncio.run(run_audio_test())
