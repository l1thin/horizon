# Horizon - llm_providers.py - owned by Dev 3 (AI + Infra)

from __future__ import annotations
import base64
import os
from ai.logger import log_ai_call


class BaseLLMProvider:
    """Base interface for model-agnostic text and voice interactions."""
    async def process_voice_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        media_type: str,
        conversation_history: list[dict],
        system_prompt: str,
    ) -> dict:
        raise NotImplementedError

    async def generate_text(self, system_prompt: str, messages: list[dict], max_tokens: int = 3000) -> str:
        raise NotImplementedError


class ClaudeLLMProvider(BaseLLMProvider):
    def __init__(self):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=os.environ.get("CLAUDE_API_KEY"))

    async def generate_text(self, system_prompt: str, messages: list[dict], max_tokens: int = 3000) -> str:
        response = await self.client.messages.create(
            model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text

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

        msgs = conversation_history + [user_message]
        response = await self.client.messages.create(
            model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
            max_tokens=500,
            system=system_prompt,
            messages=msgs,
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


class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self):
        import openai
        self.client = openai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    async def generate_text(self, system_prompt: str, messages: list[dict], max_tokens: int = 3000) -> str:
        api_messages = [{"role": "system", "content": system_prompt}] + messages
        response = await self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            max_tokens=max_tokens,
            messages=api_messages
        )
        return response.choices[0].message.content or ""

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
        msgs = [{"role": "system", "content": system_prompt}] + conversation_history
        msgs.append({
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

        response = await self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-audio-preview"),
            modalities=["text", "audio"],
            audio={"voice": "alloy", "format": "wav"},
            messages=msgs
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


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.genai = genai

    async def generate_text(self, system_prompt: str, messages: list[dict], max_tokens: int = 3000) -> str:
        model = self.genai.GenerativeModel(
            model_name=os.environ.get("GEMINI_MODEL", "gemini-1.5-pro"),
            system_instruction=system_prompt
        )
        gemini_history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})
            
        chat = model.start_chat(history=gemini_history)
        response = await chat.send_message_async(
            messages[-1]["content"],
            generation_config={"max_output_tokens": max_tokens}
        )
        return response.text

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

        model = self.genai.GenerativeModel(
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
        response = await chat.send_message_async([audio_part])
        
        response_text = response.text
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


def get_llm_provider() -> BaseLLMProvider:
    provider = os.environ.get("LLM_PROVIDER", "claude").lower()
    if provider == "openai":
        return OpenAILLMProvider()
    elif provider == "gemini":
        return GeminiLLMProvider()
    else:
        return ClaudeLLMProvider()
