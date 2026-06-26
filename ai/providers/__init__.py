from ai.providers.base_providers import (
    BaseTextProvider,
    BaseVoiceProvider,
)

from ai.config import Config
from ai.providers.text_gemini import GeminiTextProvider
from ai.providers.text_groq import GroqTextProvider
from ai.providers.text_openai import OpenAITextProvider
from ai.providers.voice_gemini import GeminiVoiceProvider
from ai.providers.voice_openai import OpenAIVoiceProvider


def get_text_provider() -> BaseTextProvider:
    provider = Config.TEXT_PROVIDER
    if provider == "groq":
        return GroqTextProvider()
    elif provider == "openai":
        return OpenAITextProvider()
    elif provider == "gemini":
        return GeminiTextProvider()

    raise ValueError(f"Unsupported Text Provider: {provider}")


def get_voice_provider() -> BaseVoiceProvider:
    provider = Config.VOICE_PROVIDER
    if provider == "gemini":
        return GeminiVoiceProvider()
    elif provider == "openai":
        return OpenAIVoiceProvider()

    raise ValueError(f"Unsupported Text Provider: {provider}")