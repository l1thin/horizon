# Horizon - voice_providers.py - owned by Dev 3 (AI + Infra)

from __future__ import annotations
import base64
import os
from ai.logger import log_ai_call


class BaseVoiceProvider:
    """Base interface for model-agnostic voice interactions."""
    async def process_voice_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        media_type: str,
        conversation_history: list[dict],
        system_prompt: str,
    ) -> dict:
        raise NotImplementedError


class ClaudeVoiceProvider(BaseVoiceProvider):
    def __init__(self, client):
        self.client = client

    async def process_voice_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        media_type: str,
        conversation_history: list[dict],
        system_prompt: str,
    ) -> dict:
        if not audio_bytes:
            return {"text": "I didn't catch that. Could you please repeat?", "audio_bytes": None}

        encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "audio",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": encoded_audio,
                    },
                }
            ],
        }

        messages = conversation_history + [user_message]
        response = self.client.messages.create(
            model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
            max_tokens=500,
            system=system_prompt,
            messages=messages,
        )

        response_text = ""
        response_audio = None

        for block in response.content:
            if block.type == "text":
                response_text += block.text
            elif block.type == "audio":
                if hasattr(block, "source") and hasattr(block.source, "data"):
                    response_audio = base64.b64decode(block.source.data)

        response_text = response_text.strip()
        await log_ai_call(
            "process_voice_turn_claude",
            {
                "session_id": session_id,
                "media_type": media_type,
                "history_len": len(conversation_history),
            },
            {"response_text_length": len(response_text), "has_audio": response_audio is not None},
        )
        return {"text": response_text, "audio_bytes": response_audio}


class OpenAIVoiceProvider(BaseVoiceProvider):
    async def process_voice_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        media_type: str,
        conversation_history: list[dict],
        system_prompt: str,
    ) -> dict:
        # Lazy import to avoid hard dependency if unused
        import openai
        
        if not audio_bytes:
            return {"text": "I didn't catch that. Could you please repeat?", "audio_bytes": None}

        client = openai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
        
        messages = [{"role": "system", "content": system_prompt}] + conversation_history
        
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": encoded_audio,
                        "format": "wav" if "wav" in media_type else "mp3"
                    }
                }
            ]
        })

        response = await client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-audio-preview"),
            modalities=["text", "audio"],
            audio={"voice": "alloy", "format": "wav"},
            messages=messages
        )

        choice = response.choices[0].message
        response_text = choice.content or ""
        response_audio = None
        
        if hasattr(choice, "audio") and choice.audio and choice.audio.data:
            response_audio = base64.b64decode(choice.audio.data)

        await log_ai_call(
            "process_voice_turn_openai",
            {
                "session_id": session_id,
                "media_type": media_type,
                "history_len": len(conversation_history),
            },
            {"response_text_length": len(response_text), "has_audio": response_audio is not None},
        )
        return {"text": response_text, "audio_bytes": response_audio}


class GeminiVoiceProvider(BaseVoiceProvider):
    async def process_voice_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        media_type: str,
        conversation_history: list[dict],
        system_prompt: str,
    ) -> dict:
        # Lazy import to avoid hard dependency if unused
        import google.generativeai as genai
        
        if not audio_bytes:
            return {"text": "I didn't catch that. Could you please repeat?", "audio_bytes": None}

        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            model_name=os.environ.get("GEMINI_MODEL", "gemini-1.5-pro"),
            system_instruction=system_prompt
        )

        gemini_history = []
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})
        
        audio_part = {
            "mime_type": media_type,
            "data": audio_bytes
        }
        
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message([audio_part])
        
        response_text = response.text
        # Gemini API standard responses for audio out are currently 
        # best handled via the real-time Live API, so we leave audio generation 
        # as a stub here until the REST API output parameters stabilize.
        response_audio = None 
        
        await log_ai_call(
            "process_voice_turn_gemini",
            {
                "session_id": session_id,
                "media_type": media_type,
                "history_len": len(conversation_history),
            },
            {"response_text_length": len(response_text), "has_audio": response_audio is not None},
        )
        return {"text": response_text, "audio_bytes": response_audio}


def get_voice_provider(client=None) -> BaseVoiceProvider:
    provider = os.environ.get("LLM_PROVIDER", "claude").lower()
    if provider == "openai":
        return OpenAIVoiceProvider()
    elif provider == "gemini":
        return GeminiVoiceProvider()
    else:
        return ClaudeVoiceProvider(client)
