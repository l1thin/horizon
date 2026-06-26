import base64

from openai import AsyncOpenAI

from ai.config import Config
from ai.providers.base_providers import BaseVoiceProvider


class OpenAIVoiceProvider(BaseVoiceProvider):
    def __init__(self):
        super().__init__()
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

    async def process_voice_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        media_type: str,
        conversation_history: list[dict],
        system_prompt: str,
    ) -> dict:
        if not audio_bytes:
            return {
                "text": "I didn't catch that. Could you please repeat?",
                "audio_bytes": None,
            }

        encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")

        messages = [{"role": "system", "content": system_prompt}] + conversation_history

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encoded_audio,
                            "format": "wav" if "wav" in media_type else "mp3",
                        },
                    }
                ],  # type:ignore
            }
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            modalities=["text", "audio"],
            audio={"voice": "alloy", "format": "wav"},
            messages=messages,  # type:ignore
        )

        choice = response.choices[0].message
        response_text = choice.content or ""
        response_audio = None

        if hasattr(choice, "audio") and choice.audio:
            if choice.audio.data:
                response_audio = base64.b64decode(choice.audio.data)

            if not response_text:
                response_text = getattr(choice.audio, "transcript", "")

        return {"text": response_text.strip(), "audio_bytes": response_audio}
