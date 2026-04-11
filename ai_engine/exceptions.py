from __future__ import annotations


class LLMConnectionError(Exception):
    """Raised when the LLM provider cannot be reached."""


class LLMTimeoutError(Exception):
    """Raised when the LLM provider request times out."""


class InvalidJSONOutputError(Exception):
    """Raised when the LLM output is not valid JSON for the expected schema."""

