from __future__ import annotations
import logging
from LLM.service import LLMService, WordAnalysis

logger = logging.getLogger(__name__)


class _DisabledLLMService(LLMService):
    """Fallback service when LLM is unavailable."""
    def is_available(self) -> bool:
        return False
    def analyze_word(self, word, language):
        raise RuntimeError("LLM service is not available")
    def get_context(self, word, language):
        raise RuntimeError("LLM service is not available")


def get_llm_service() -> LLMService:
    """Create and return the configured LLM service.

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
