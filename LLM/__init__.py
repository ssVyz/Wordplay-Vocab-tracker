from __future__ import annotations
import logging
from LLM.service import LLMService, WordAnalysis

logger = logging.getLogger(__name__)


class _DisabledLLMService(LLMService):
    """Fallback service when LLM is unavailable."""
    def is_available(self) -> bool:
        return False
    def analyze_word(self, word, language, context=None):
        raise RuntimeError("LLM service is not available")
    def translate_word(self, word, language):
        raise RuntimeError("LLM service is not available")
    def get_context(self, word, language):
        raise RuntimeError("LLM service is not available")


def get_llm_service() -> LLMService:
    """Create and return the default (Phi-3) LLM service.

    Returns a disabled fallback if the LLM fails to initialize.
    """
    try:
        from LLM.phi3_backend import Phi3Backend
        service = Phi3Backend()
        if service.is_available():
            logger.info("LLM service initialized successfully")
            return service
        else:
            logger.warning("LLM model failed to load, running in degraded mode")
            return _DisabledLLMService()
    except Exception as e:
        logger.error(f"Failed to initialize LLM service: {e}")
        return _DisabledLLMService()


def get_gemini_service(api_key: str) -> LLMService:
    """Create and return a Gemini LLM service.

    Returns a disabled fallback if initialization fails.
    """
    try:
        from LLM.gemini_backend import GeminiBackend
        service = GeminiBackend(api_key)
        if service.is_available():
            logger.info("Gemini LLM service initialized successfully")
            return service
        else:
            logger.warning("Gemini service not available (no API key?)")
            return _DisabledLLMService()
    except Exception as e:
        logger.error(f"Failed to initialize Gemini service: {e}")
        return _DisabledLLMService()
