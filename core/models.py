from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WordType(Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"


class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EXTREMELY_RARE = "extremely rare"


@dataclass
class WordEntry:
    import_string: str          # Original string as entered by user
    identified_word: str        # Dictionary/base form (the key identifier)
    translation: str            # English translation
    word_type: WordType
    rarity: Rarity
    added_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "import_string": self.import_string,
            "identified_word": self.identified_word,
            "translation": self.translation,
            "word_type": self.word_type.value,
            "rarity": self.rarity.value,
            "added_date": self.added_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WordEntry:
        return cls(
            import_string=data["import_string"],
            identified_word=data["identified_word"],
            translation=data["translation"],
            word_type=WordType(data["word_type"]),
            rarity=Rarity(data["rarity"]),
            added_date=data["added_date"],
        )
