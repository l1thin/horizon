from google import genai
from google.genai import types
from ai.config import Config
from ai.providers.base_providers import BaseTextProvider


class GeminiTextProvider(BaseTextProvider):
    def __init__(self) -> None:
        super().__init__()

        self.client = genai.Client(api_key=Config.GEMINI_API_KEY).aio

    async def generate_text(
        self, system_prompt: str, messages: list[dict], max_tokens: int = 3000
    ) -> str:

        formatted_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            formatted_contents.append({
                "role":role,
                "parts":[msg["content"]]
            })

        response = await self.client.models.generate_content(
            model=self.model,
            contents=formatted_contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
            )
        )
        return response.text or "" 
