
from ai.config import Config


class BaseTextProvider:
    def __init__(self) -> None:
        Config.validate_keys("text", Config.TEXT_PROVIDER)
        self.model = Config.TEXT_MODEL

    async def generate_text(
        self, system_prompt: str, messages: list[dict], max_tokens: int = 3000
    ) -> str:
        raise NotImplementedError("Text generation provider not implemented")



