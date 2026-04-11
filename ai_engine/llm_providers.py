from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from django.conf import settings

from .exceptions import InvalidJSONOutputError, LLMConnectionError, LLMTimeoutError


class BaseLLMProvider(ABC):
    """Strategy interface for JSON-capable LLM providers."""

    @abstractmethod
    def generate_json(self, prompt: str) -> dict[str, Any]:
        """Generate a JSON dictionary from a plain-text prompt."""


class GeminiProvider(BaseLLMProvider):
    """Google Gemini implementation for roadmap generation."""

    def __init__(self) -> None:
        self.model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        self.api_key = getattr(settings, "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

    def generate_json(self, prompt: str) -> dict[str, Any]:
        if not self.api_key:
            raise LLMConnectionError("Gemini API key is not configured.")

        try:
            import google.generativeai as genai  # Imported lazily for safer app startup.
        except Exception as exc:  # pragma: no cover - environment dependent
            raise LLMConnectionError("google-generativeai package is unavailable.") from exc

        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"},
            )
        except TimeoutError as exc:
            raise LLMTimeoutError("Gemini request timed out.") from exc
        except Exception as exc:
            message = str(exc).lower()
            if "timeout" in message or "deadline" in message:
                raise LLMTimeoutError("Gemini request timed out.") from exc
            raise LLMConnectionError("Failed to connect to Gemini provider.") from exc

        raw_text = getattr(response, "text", None)
        if not raw_text:
            raise InvalidJSONOutputError("Gemini returned an empty response.")

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise InvalidJSONOutputError("Gemini returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise InvalidJSONOutputError("Gemini JSON output must be an object.")

        return data

