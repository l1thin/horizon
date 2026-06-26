# ai/realtime/__init__.py
from ai.config import Config
from ai.realtime.base_session import BaseRealtimeSession
from ai.realtime.session_gemini import GeminiRealtimeSession
from ai.realtime.session_openai import OpenAIRealtimeSession


def get_realtime_session(
    session_id: str, system_prompt: str, max_phase_turns: int = 3
) -> BaseRealtimeSession:
    provider = Config.VOICE_PROVIDER.lower()

    if provider == "openai":
        return OpenAIRealtimeSession(session_id, system_prompt, max_phase_turns)
    elif provider == "gemini":
        return GeminiRealtimeSession(session_id, system_prompt, max_phase_turns)
    else:
        raise ValueError(
            f"Unsupported Voice Provider for Realtime Sessions: {provider}"
        )
