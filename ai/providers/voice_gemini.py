from google import genai
from google.genai import types

from ai.config import Config
from ai.providers import BaseVoiceProvider


class GeminiVoiceProvider(BaseVoiceProvider):
    def __init__(self):
        super().__init__()
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY).aio

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

        formatted_contents = []
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            formatted_contents.append(
                {"role": role, "parts": [{"text": msg["content"]}]}
            )

        current_turn_parts = [
            types.Part.from_bytes(data=audio_bytes, mime_type=media_type)
        ]
        formatted_contents.append({"role": "user", "parts": current_turn_parts})

        response = await self.client.models.generate_content(
            model=self.model,
            contents=formatted_contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )

        response_text = response.text


        return {"text": response_text or "", "audio_bytes": None}
