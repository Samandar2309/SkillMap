from __future__ import annotations


# =========================
# BASE LLM ERRORS
# =========================

class LLMError(Exception):
    """Base class for all LLM-related errors."""
    
    def __init__(self, message: str, *, provider: str = "unknown", model: str = "unknown") -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model


class LLMConnectionError(LLMError):
    """Raised when the LLM provider cannot be reached.
    
    RETRY: Yes - network issues may be transient.
    """
    pass


class LLMTimeoutError(LLMError):
    """Raised when the LLM provider request times out.
    
    RETRY: Yes - timeouts may be transient load issues.
    """
    pass


class InvalidJSONOutputError(LLMError):
    """Raised when the LLM output is not valid JSON for the expected schema.
    
    RETRY: Yes - may be transient model hallucination.
    """
    pass


# =========================
# CONFIGURATION ERRORS (NO RETRY)
# =========================

class InvalidModelError(LLMError):
    """Raised when an invalid/unsupported model is requested.
    
    RETRY: No - configuration error, fix the model name.
    """
    pass


class LLMAuthError(LLMError):
    """Raised when API key is invalid or missing.
    
    RETRY: No - authentication error, fix credentials.
    """
    pass


class LLMConfigError(LLMError):
    """Raised when LLM configuration is invalid.
    
    RETRY: No - configuration error, fix settings.
    """
    pass


# =========================
# PROVIDER-SPECIFIC ERRORS
# =========================

class RateLimitError(LLMError):
    """Raised when rate limit is hit.
    
    RETRY: Yes - with exponential backoff.
    """
    pass


class ProviderUnavailableError(LLMError):
    """Raised when provider is temporarily unavailable.
    
    RETRY: Yes - switch provider or wait.
    """
    pass


class AllProvidersFailedError(LLMError):
    """Raised when all configured providers fail.
    
    RETRY: Depends on underlying errors.
    """
    def __init__(self, message: str, errors: list[Exception]) -> None:
        super().__init__(message)
        self.errors = errors

