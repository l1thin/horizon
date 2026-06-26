from ai.config import Config


class BaseTextProvider:
    def __init__(self) -> None:
        Config.validate_keys("text", Config.TEXT_PROVIDER)
        self.model = Config.TEXT_MODEL

    async def generate_text(
        self, system_prompt: str, messages: list[dict], max_tokens: int = 3000
    ) -> str:
        raise NotImplementedError("Text generation provider not implemented")


class BaseVoiceProvider:
    def __init__(self):
        Config.validate_keys("voice", Config.VOICE_PROVIDER)
        self.model = Config.VOICE_MODEL

    async def process_voice_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        media_type: str,
        conversation_history: list[dict],
        system_prompt: str,
    ) -> dict:
        raise NotImplementedError("Voice proccessing not implemented for this provider")


