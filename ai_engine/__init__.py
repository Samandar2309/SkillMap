"""
AI Engine for SkillMap - Production-grade LLM routing system.

Quick Start:
    from ai_engine.router import get_router
    
    router = get_router()
    result = router.generate_json("Your prompt here")
"""

__version__ = "2.0.0"

# Public API
from .exceptions import (
    AllProvidersFailedError,
    InvalidJSONOutputError,
    InvalidModelError,
    LLMAuthError,
    LLMConfigError,
    LLMConnectionError,
    LLMError,
    LLMTimeoutError,
    RateLimitError,
)
from .providers import (
    BaseLLMProvider,
    GenerationResult,
    GroqProvider,
    ModelRegistry,
    create_groq_provider,
)
from .router import LLMRouter, RouterConfig, _get_config_from_settings, generate_json, get_router

__all__ = [
    # Exceptions
    "AllProvidersFailedError",
    "InvalidJSONOutputError",
    "InvalidModelError",
    "LLMAuthError",
    "LLMConfigError",
    "LLMConnectionError",
    "LLMError",
    "LLMTimeoutError",
    "RateLimitError",
    # Providers
    "BaseLLMProvider",
    "GenerationResult",
    "GroqProvider",
    "ModelRegistry",
    "create_groq_provider",
    # Router
    "LLMRouter",
    "RouterConfig",
    "_get_config_from_settings",
    "generate_json",
    "get_router",
]
