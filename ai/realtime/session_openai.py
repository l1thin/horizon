import asyncio
import base64
import json

import websockets

from ai.config import Config
from ai.realtime.base_session import BaseRealtimeSession


class OpenAIRealtimeSession(BaseRealtimeSession):
    def __init__(self, session_id: str, system_prompt: str, turns: int) -> None:
        super().__init__(session_id, system_prompt)
        Config.validate_keys("voice", "openai")
        self.api_key = Config.OPENAI_API_KEY

        self.url = f"wss://api.openai.com/v1/realtime?model={Config.VOICE_MODEL}"
        self.ws = None
        self.turns = turns
        self.recieve_task = None

    async def connect(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        self.ws = await websockets.connect(self.url, additional_headers=headers)

        init_event = {
            "type": "session.update",
            "session": {
                "instructions": self.system_prompt,
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "output_audio_format": "pcm16",
                "turn_detection": {"type": "server_vad"},
            },
        }
        await self.ws.send(json.dumps(init_event))

        self.recieve_task = asyncio.create_task(self._receive_loop())
        

    async def send_user_audio(self, pcm_audio_bytes: bytes, end_of_stream=False):

        if not self.ws:
            return

        encoded_audio = base64.b64encode(pcm_audio_bytes).decode("utf-8")
        event = {"type": "input_audio_buffer.append", "audio": encoded_audio}

        await self.ws.send(json.dumps(event))

    async def send_user_text(self, text: str):
        if not self.ws:
            return

        # 1. Send the text as a user message
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            },
        }
        await self.ws.send(json.dumps(event))

        # 2. Force the AI to respond to the text immediately
        await self.ws.send(json.dumps({"type": "response.create"}))

    async def close(self):
        if self.recieve_task:
            self.recieve_task.cancel()
        if self.ws:
            await self.ws.close()

    async def _receive_loop(self):
        if not self.ws:
            return

        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")

                # to frontend
                if event_type == "response.audio.delta":
                    if self.on_audio_to_frontend:
                        audio_chunk = base64.b64decode(event.get("delta"))
                        await self.on_audio_to_frontend(audio_chunk)

                elif (
                    event_type
                    == "conversation.item.input_audio_transcription.completed"
                ):
                    user_text = event.get("transcript", "")
                    self.history.append({"role": "user", "content": user_text})

                elif event_type == "response.audio_transcript.done":
                    ai_text = event.get("transcript", "")
                    self.history.append({"role": "assistant", "content": ai_text})

                elif event_type == "response.done":
                    self.turn_count += 1
                    await asyncio.sleep(1)
                    if self.on_turn_complete:
                        await self.on_turn_complete()
                    if self.turn_count >= self.turns:
                        if self.on_phase_complete:
                            await self.on_phase_complete(self.history)
                        return
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"OpenAI WebSocket Error: {e}")
