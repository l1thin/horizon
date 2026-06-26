import os

from dotenv import load_dotenv
load_dotenv()

class Config:
    def __init__(self):
        load_dotenv()

    TEXT_PROVIDER = os.environ.get("TEXT_PROVIDER", "groq").lower()
    VOICE_PROVIDER = os.environ.get("VOICE_PROVIDER", "openai").lower()

    TEXT_MODEL = os.environ.get("TEXT_MODEL", "llama3-8b-8192")
    VOICE_MODEL = os.environ.get("VOICE_MODEL", "gpt-4o-audio-preview")

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

    @classmethod
    def validate_keys(cls, provider_type: str, provider_name: str):

        keys = {
            "openai": cls.OPENAI_API_KEY,
            "gemini": cls.GEMINI_API_KEY,
            "groq": cls.GROQ_API_KEY,
        }

        if not keys.get(provider_name):
            raise EnvironmentError(
                f"Missing API key for {provider_type} provider: {provider_name}"
            )
