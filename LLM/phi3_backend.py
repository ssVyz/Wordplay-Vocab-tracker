from __future__ import annotations
import json
import logging
import re
from pathlib import Path
from LLM.service import LLMService, WordAnalysis
from LLM.config import LLMConfig, load_config
from core.models import WordType, Rarity

logger = logging.getLogger(__name__)


class Phi3Backend(LLMService):
    def __init__(self, config: LLMConfig | None = None):
        self._config = config or load_config()
        self._model = None
        self._load_model()

    def _load_model(self):
        try:
            from llama_cpp import Llama
            model_path = Path(__file__).parent / self._config.model_path
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return
            self._model = Llama(
                model_path=str(model_path),
                n_ctx=self._config.n_ctx,
                n_gpu_layers=self._config.n_gpu_layers,
                verbose=False,
            )
            logger.info("Phi-3 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Phi-3 model: {e}")
            self._model = None

    def is_available(self) -> bool:
        return self._model is not None

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request to the model using Phi-3 chat format."""
        if not self.is_available():
            raise RuntimeError("LLM model is not available")

        response = self._model.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
        )
        return response["choices"][0]["message"]["content"].strip()

    def analyze_word(self, word: str, language: str) -> WordAnalysis:
        system_prompt = (
            "You are a linguistic analysis assistant. You analyze words and return results as JSON. "
            "Always respond with ONLY a valid JSON object, no other text."
        )
        user_prompt = (
            f'Analyze the {language} word "{word}". Return a JSON object with these exact keys:\n'
            f'- "base_form": the dictionary/base form (nominative for nouns, infinitive for verbs)\n'
            f'- "translation": the English translation\n'
            f'- "word_type": one of "noun", "verb", "adjective", "adverb"\n'
            f'- "rarity": one of "common", "uncommon", "rare", "extremely rare"\n\n'
            f'Respond with ONLY the JSON object.'
        )

        raw = self._chat(system_prompt, user_prompt)
        # Try to extract JSON from the response
        try:
            # Try to find JSON in the response (it might have markdown fences)
            json_str = raw
            if "```" in raw:
                # Extract content between code fences
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = raw[start:end]
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: try to find any JSON object in the response
            match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                logger.error(f"Failed to parse LLM response as JSON: {raw}")
                # Return a best-effort fallback
                return WordAnalysis(
                    base_form=word,
                    translation="(analysis failed)",
                    word_type=WordType.NOUN,
                    rarity=Rarity.COMMON,
                )

        # Map to enums with fallbacks
        try:
            word_type = WordType(data.get("word_type", "noun"))
        except ValueError:
            word_type = WordType.NOUN
        try:
            rarity = Rarity(data.get("rarity", "common"))
        except ValueError:
            rarity = Rarity.COMMON

        return WordAnalysis(
            base_form=data.get("base_form", word),
            translation=data.get("translation", "(unknown)"),
            word_type=word_type,
            rarity=rarity,
        )

    def get_context(self, word: str, language: str) -> str:
        system_prompt = (
            "You are a language learning assistant. Provide concise, helpful information "
            "about vocabulary words to help learners understand and use them correctly."
        )
        user_prompt = (
            f'For the {language} word "{word}", provide:\n'
            f'1. A brief definition and explanation of meaning\n'
            f'2. If it is a verb: present tense conjugation table\n'
            f'   If it is a noun: gender/article (if applicable), plural form\n'
            f'   If it is an adjective/adverb: comparative and superlative forms\n'
            f'3. Two example sentences with English translations\n'
            f'4. Any common related words or expressions\n\n'
            f'Keep it concise and well-formatted.'
        )
        return self._chat(system_prompt, user_prompt)
