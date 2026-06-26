import asyncio

from google import genai
from google.genai import types

from ai.config import Config
from ai.realtime.base_session import BaseRealtimeSession


class GeminiRealtimeSession(BaseRealtimeSession):
    def __init__(self, session_id: str, system_prompt: str, turns: int) -> None:
        super().__init__(session_id, system_prompt)
        Config.validate_keys("voice", "gemini")

        self.client = genai.Client(api_key=Config.GEMINI_API_KEY).aio

        self.model = Config.VOICE_MODEL

        self.live_session = None
        self.receive_task = None

        self.turns = turns

    async def connect(self):

        config = types.LiveConnectConfig(
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=self.system_prompt)]
            ),
            response_modalities=[types.Modality.AUDIO],
            output_audio_transcription=types.AudioTranscriptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                )
            ),
        )
        self.context_manager = self.client.live.connect(model=self.model, config=config)
        self.live_session = await self.context_manager.__aenter__()

        self.receive_task = asyncio.create_task(self._recieve_loop())

    async def send_user_audio(self, pcm_audio_bytes: bytes):

        if not self.live_session:
            return

        await self.live_session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[
                    types.Blob(data=pcm_audio_bytes, mime_type="audio/pcm;rate=16000")
                ]
            )
        )

    async def send_user_text(self, text: str):
        if not self.live_session:
            return

        self.history.append({"role": "user", "content": text})

        await self.live_session.send(
            input=types.LiveClientContent(
                turns=[
                    types.Content(
                        role="user", parts=[types.Part.from_text(text=text)]
                    )
                ],
                turn_complete=True,
            )
        )

    async def close(self):
        if self.receive_task and not self.receive_task.done():
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        self.live_session = None

    async def _recieve_loop(self):
        if not self.live_session:
            return
        try:
            while self.live_session:
                async for message in self.live_session.receive():
                    if (
                        message.server_content
                        and message.server_content.model_turn
                        and message.server_content.model_turn.parts
                    ):
                        for part in message.server_content.model_turn.parts:
                            if (
                                part.inline_data
                                and part.inline_data.data
                                and self.on_audio_to_frontend
                            ):
                                await self.on_audio_to_frontend(part.inline_data.data)
    
                            elif part.text:
                                self.history.append({"role": "model", "content": part.text})
    
                    if (
                        message.server_content
                        and message.server_content.output_transcription
                    ):
                        transcript_text = message.server_content.output_transcription.text
                        if transcript_text:
                            if self.history and self.history[-1]["role"] == "model":
                                self.history[-1]["content"] += transcript_text
                            else:
                                self.history.append(
                                    {"role": "model", "content": transcript_text}
                                )
    
                    if message.server_content and message.server_content.turn_complete:
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
            print(f"Gemini Live API Error: {e}")
            await asyncio.sleep(1)
