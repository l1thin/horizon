from openai.types.chat import ChatCompletionMessageParam
from typing_extensions import cast

from ai.config import Config
from ai.providers.base_providers import BaseTextProvider
from openai import AsyncOpenAI

class OpenAITextProvider(BaseTextProvider):

    def __init__(self) -> None:
        super().__init__()
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

    async def generate_text(self, system_prompt: str, messages: list[dict], max_tokens: int = 3000) -> str:
        api_messages = [{"role":"system","content":system_prompt}] + messages


        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=cast(list[ChatCompletionMessageParam], api_messages)
            
        )

        return response.choices[0].message.content or ""