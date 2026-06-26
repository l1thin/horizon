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
        self.setup_complete = asyncio.Event()

        self.turns = turns

    async def connect(self):
        print(f"[DEBUG] Connecting to model: {self.model}")
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
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    disabled=False,
                )
            ),
        )
        self.context_manager = self.client.live.connect(model=self.model, config=config)
        self.live_session = await self.context_manager.__aenter__()
        print(type(self.live_session))
        print(self.live_session)

        self.receive_task = asyncio.create_task(self._receive_loop())
        print(f"[DEBUG] ✅ Connected to {self.model}")

    async def send_user_audio(self, pcm_audio_bytes: bytes, end_of_stream=False):
        if self.live_session is None:
            return
        await self.live_session.send_realtime_input(
            audio=types.Blob(
                data=pcm_audio_bytes,
                mime_type="audio/pcm;rate=16000",
            )
        )

        if (
            end_of_stream
        ):  # DO NOT SEND THEM TOGETHER , NEVER PUT STREAM END IN THE ABOVE SEND
            await self.live_session.send_realtime_input(audio_stream_end=True)

    async def send_user_text(self, text: str):
        if not self.live_session:
            return

        self.history.append({"role": "user", "content": text})

        await self.live_session.send(
            input=types.LiveClientContent(
                turns=[
                    types.Content(role="user", parts=[types.Part.from_text(text=text)])
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

    async def _receive_loop(self):
        if not self.live_session:
            return
        try:
            while self.live_session:
                async for message in self.live_session.receive():
                    sc = message.server_content
                    if not sc:
                        continue

                    # Audio chunks
                    if sc.model_turn and sc.model_turn.parts:
                        for part in sc.model_turn.parts:
                            if (
                                part.inline_data
                                and self.on_audio_to_frontend
                                and part.inline_data.data
                            ):
                                await self.on_audio_to_frontend(part.inline_data.data)

                    # Spoken transcript
                    if sc.output_transcription:
                        text = sc.output_transcription.text
                        if text:
                            if self.history and self.history[-1]["role"] == "model":
                                self.history[-1]["content"] += text
                            else:
                                self.history.append(
                                    {
                                        "role": "model",
                                        "content": text,
                                    }
                                )

                    # End of turn
                    if sc.turn_complete:
                        self.turn_count += 1

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
