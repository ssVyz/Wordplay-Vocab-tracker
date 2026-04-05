from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from core.models import WordType, Rarity


@dataclass
class WordAnalysis:
    """Result of analyzing a single word through the LLM."""
    base_form: str       # Dictionary/base form of the word
    translation: str     # English translation
    word_type: WordType  # Grammatical category
    rarity: Rarity       # Frequency/rarity classification


class LLMService(ABC):
    """Abstract interface for LLM operations used by the app."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM backend is loaded and ready."""
        ...

    @abstractmethod
    def analyze_word(self, word: str, language: str, context: str | None = None) -> WordAnalysis:
        """Analyze a word: find base form, classify type and rarity.

        Args:
            word: The word to analyze (may be conjugated/declined)
            language: The target language name (e.g., "German", "French")
            context: Optional surrounding words for disambiguation
                     (e.g. "die kleine [Katze] lief schnell")
        Returns:
            WordAnalysis with base_form, word_type, rarity populated.
            The translation field may be empty.
        Raises:
            RuntimeError if LLM is not available
        """
        ...

    @abstractmethod
    def translate_word(self, word: str, language: str) -> str:
        """Translate a base-form word to English.

        Args:
            word: The dictionary/base form of the word
            language: The source language name
        Returns:
            English translation string
        Raises:
            RuntimeError if LLM is not available
        """
        ...

    @abstractmethod
    def get_context(self, word: str, language: str) -> str:
        """Generate context information for a word.

        For verbs: present tense conjugations, brief usage overview.
        For nouns: gender/article if applicable, plural form, usage.
        For all: example sentences, brief semantic overview.

        Args:
            word: The base/dictionary form of the word
            language: The target language name
        Returns:
            Formatted text with context information
        Raises:
            RuntimeError if LLM is not available
        """
        ...
