from ai.config import Config
from ai.providers.base_providers import (
    BaseTextProvider,
)
from ai.providers.text_gemini import GeminiTextProvider
from ai.providers.text_groq import GroqTextProvider
from ai.providers.text_openai import OpenAITextProvider


def get_text_provider() -> BaseTextProvider:
    provider = Config.TEXT_PROVIDER
    if provider == "groq":
        return GroqTextProvider()
    elif provider == "openai":
        return OpenAITextProvider()
    elif provider == "gemini":
        return GeminiTextProvider()

    raise ValueError(f"Unsupported Text Provider: {provider}")
