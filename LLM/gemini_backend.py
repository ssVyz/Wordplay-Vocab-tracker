from __future__ import annotations

import json
import logging
import re

from LLM.service import LLMService, WordAnalysis
from core.models import WordType, Rarity

logger = logging.getLogger(__name__)


class GeminiBackend(LLMService):
    """LLM backend using Google Gemini 2.5 Flash via the REST API."""

    _MODEL = "gemini-2.5-flash"
    _ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._available = bool(api_key)

    def is_available(self) -> bool:
        return self._available

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a request to the Gemini REST API."""
        if not self._available:
            raise RuntimeError("Gemini backend is not configured")

        import urllib.request
        import urllib.error

        url = f"{self._ENDPOINT}/{self._MODEL}:generateContent?key={self._api_key}"

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {"role": "user", "parts": [{"text": user_prompt}]},
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            logger.error("Gemini API error %s: %s", exc.code, error_body)
            raise RuntimeError(f"Gemini API error {exc.code}") from exc

        # Extract text from response
        try:
            return body["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as exc:
            logger.error("Unexpected Gemini response structure: %s", body)
            raise RuntimeError("Failed to parse Gemini response") from exc

    def _parse_json(self, raw: str) -> dict | None:
        """Extract a JSON object from an LLM response string."""
        try:
            json_str = raw
            if "```" in raw:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = raw[start:end]
            return json.loads(json_str)
        except json.JSONDecodeError:
            match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            return None

    def analyze_word(self, word: str, language: str, context: str | None = None) -> WordAnalysis:
        system_prompt = (
            "You are a linguistic analysis assistant. You analyze words and return results as JSON. "
            "Always respond with ONLY a valid JSON object, no other text."
        )

        context_line = ""
        if context:
            context_line = (
                f" The word marked with square brackets in the following "
                f"snippet is the word to analyze — the surrounding words are "
                f"only provided for disambiguation: {context}."
            )

        user_prompt = (
            f'Analyze ONLY the {language} word "{word}".{context_line} '
            f'Return a JSON object with these exact keys:\n'
            f'- "base_form": the dictionary/base form of "{word}" (nominative for nouns, infinitive for verbs)\n'
            f'- "word_type": one of "noun", "verb", "adjective", "adverb"\n'
            f'- "rarity": one of "common", "uncommon", "rare", "extremely rare"\n\n'
            f'Respond with ONLY the JSON object.'
        )

        raw = self._chat(system_prompt, user_prompt)
        data = self._parse_json(raw)

        if data is None:
            logger.error("Failed to parse Gemini response as JSON: %s", raw)
            return WordAnalysis(
                base_form=word,
                translation="",
                word_type=WordType.NOUN,
                rarity=Rarity.COMMON,
            )

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
            translation="",
            word_type=word_type,
            rarity=rarity,
        )

    def translate_word(self, word: str, language: str) -> str:
        system_prompt = (
            "You are a translation assistant. Translate words and return results as JSON. "
            "Always respond with ONLY a valid JSON object, no other text."
        )
        user_prompt = (
            f'Translate the {language} word "{word}" (dictionary/base form) to English. '
            f'Return a JSON object with one key:\n'
            f'- "translation": the English translation\n\n'
            f'Respond with ONLY the JSON object.'
        )

        raw = self._chat(system_prompt, user_prompt)
        data = self._parse_json(raw)

        if data is None:
            logger.error("Failed to parse Gemini translation response: %s", raw)
            return "(translation failed)"

        return data.get("translation", "(unknown)")

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
