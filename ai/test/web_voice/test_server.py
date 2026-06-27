import asyncio

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ai.realtime import get_realtime_session

app = FastAPI()


@app.get("/")
async def get_test_page():
    try:
        with open("./ai/test/web_voice/test_browser.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse(
            "<h1>Error: test_browser.html not found.</h1>", status_code=404
        )


@app.websocket("/ws/interview")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("\n[WS] 🌐 Browser connected!")

    system_prompt = "You are testing a web-based voice bridge. Warmly welcome the user. Keep answers strictly to one sentence."
    session = get_realtime_session("web_test", system_prompt, turns=99)

    async def on_audio(chunk: bytes):
        try:
            await websocket.send_bytes(chunk)
        except Exception:
            pass

    session.on_audio_to_frontend = on_audio

    try:
        print("[WS] 🔗 Connecting to Gemini...")
        await session.connect()
        print("[WS] ✅ Gemini connected! Listening for browser audio...")

        # Receive mic audio from browser and forward to Gemini
        async def receive_from_browser():
            bytes_received = 0
            try:
                while True:
                    data = await websocket.receive_bytes()
                    bytes_received += len(data)
                    if bytes_received % (16000 * 2 * 5) < len(data):  # log every ~5s
                        print(
                            f"[WS] 🎙️ Receiving mic audio ({bytes_received // 1024} KB so far)"
                        )
                    await session.send_user_audio(data, end_of_stream=False)
            except WebSocketDisconnect:
                print("\n[WS] 🛑 Browser disconnected.")

        # Run browser receiver and Gemini receiver concurrently
        await asyncio.gather(
            receive_from_browser(),
            session.receive_task,  # Gemini's _receive_loop task
            return_exceptions=True,
        )

    except Exception as e:
        print(f"\n[WS] ⚠️ Error: {e}")
    finally:
        await session.close()
        print("[WS] 🧹 Session cleaned up.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
