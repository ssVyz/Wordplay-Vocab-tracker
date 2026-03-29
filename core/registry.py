from __future__ import annotations

import json
from pathlib import Path

from core.models import Rarity, WordEntry, WordType


class WordRegistry:
    """Word registry management, bound to a specific language folder path."""

    def __init__(self, language_path: Path):
        self.language_path = language_path
        self.words_file = language_path / "words.json"
        self._words: list[WordEntry] = []
        self.load()

    def load(self) -> None:
        """Load words from the JSON file."""
        if self.words_file.exists():
            raw = json.loads(self.words_file.read_text(encoding="utf-8"))
            self._words = [WordEntry.from_dict(entry) for entry in raw]
        else:
            self._words = []

    def save(self) -> None:
        """Save words to the JSON file with indent=2."""
        data = [word.to_dict() for word in self._words]
        self.words_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def add_word(self, entry: WordEntry) -> bool:
        """Add a word. Returns False if duplicate (by identified_word, case-insensitive)."""
        if self.has_word(entry.identified_word):
            return False
        self._words.append(entry)
        self.save()
        return True

    def add_words(self, entries: list[WordEntry]) -> int:
        """Add multiple words, skipping duplicates. Returns count of words actually added."""
        count = 0
        for entry in entries:
            if not self.has_word(entry.identified_word):
                self._words.append(entry)
                count += 1
        if count > 0:
            self.save()
        return count

    def remove_word(self, identified_word: str) -> bool:
        """Remove a word by its identified_word. Returns True if found and removed."""
        lower_target = identified_word.lower()
        for i, word in enumerate(self._words):
            if word.identified_word.lower() == lower_target:
                self._words.pop(i)
                self.save()
                return True
        return False

    def has_word(self, identified_word: str) -> bool:
        """Check if a word exists (case-insensitive match on identified_word)."""
        lower_target = identified_word.lower()
        return any(w.identified_word.lower() == lower_target for w in self._words)

    def get_all_words(self) -> list[WordEntry]:
        """Return all words."""
        return list(self._words)

    def get_words(
        self,
        sort_by: str = "identified_word",
        sort_reverse: bool = False,
        filter_type: WordType | None = None,
        filter_rarity: Rarity | None = None,
        search_text: str = "",
    ) -> list[WordEntry]:
        """Return filtered and sorted words.

        sort_by: "identified_word", "added_date", "word_type", "rarity", "translation"
        filter_type: filter to a specific WordType
        filter_rarity: filter to a specific Rarity
        search_text: case-insensitive substring match against identified_word,
                     import_string, or translation
        """
        results = list(self._words)

        # Apply type filter
        if filter_type is not None:
            results = [w for w in results if w.word_type == filter_type]

        # Apply rarity filter
        if filter_rarity is not None:
            results = [w for w in results if w.rarity == filter_rarity]

        # Apply search text filter
        if search_text:
            needle = search_text.lower()
            results = [
                w
                for w in results
                if needle in w.identified_word.lower()
                or needle in w.import_string.lower()
                or needle in w.translation.lower()
            ]

        # Sort
        sort_keys = {
            "identified_word": lambda w: w.identified_word.lower(),
            "added_date": lambda w: w.added_date,
            "word_type": lambda w: w.word_type.value,
            "rarity": lambda w: w.rarity.value,
            "translation": lambda w: w.translation.lower(),
        }
        key_func = sort_keys.get(sort_by, sort_keys["identified_word"])
        results.sort(key=key_func, reverse=sort_reverse)

        return results
