from groq.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from typing_extensions import cast

from ai.config import Config
from ai.providers.base_providers import BaseTextProvider
from groq import AsyncGroq


class GroqTextProvider(BaseTextProvider):

    def __init__(self) -> None:
        super().__init__()
        self.client = AsyncGroq(api_key=Config.GROQ_API_KEY)

    async def generate_text(self, system_prompt: str, messages: list[dict], max_tokens: int = 3000) -> str:
        api_messages = [{"role":"system","content":system_prompt}] + messages


        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=cast(list[ChatCompletionMessageParam], api_messages)
            
        )

        return response.choices[0].message.content or ""