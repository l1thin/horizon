from typing import Awaitable, Callable


class BaseRealtimeSession:
    def __init__(self, session_id: str, system_prompt: str) -> None:
        self.session_id = session_id
        self.system_prompt = system_prompt
        self.turn_count = 0

        self.on_audio_to_frontend: Callable[[bytes], Awaitable[None]] | None = None
        self.on_phase_complete: Callable[[list[dict]], Awaitable[None]] | None = None
        self.on_turn_complete: Callable[[], Awaitable[None]] | None = None

        self.history = []

    async def connect(self):
        """Establish the WebSocket connection to the LLM provider."""
        raise NotImplementedError

    async def send_user_audio(
        self, pcm_audio_bytes: bytes, end_of_stream: bool = False
    ):
        """Stream raw user audio from the frontend to the LLM."""
        raise NotImplementedError

    async def send_user_text(self, text: str):
        """Inject text directly into the live conversation (useful for CLI testing or fallback)."""
        raise NotImplementedError

    async def close(self):
        """Safely teardown the connection."""
        raise NotImplementedError
