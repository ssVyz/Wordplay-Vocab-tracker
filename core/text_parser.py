from __future__ import annotations

import re


def tokenize_text(text: str) -> list[str]:
    """Split input text into individual words.

    - Splits by whitespace and punctuation
    - Lowercases all words
    - Removes duplicates (preserving first occurrence order)
    - Strips empty strings
    - Removes pure numbers
    """
    # Use regex to find word tokens (unicode-aware to support foreign languages)
    words = re.findall(r"[\w]+", text.lower(), re.UNICODE)

    # Filter out pure numbers
    words = [w for w in words if not w.isdigit()]

    # Deduplicate preserving order
    seen: set[str] = set()
    result: list[str] = []
    for w in words:
        if w not in seen:
            seen.add(w)
            result.append(w)

    return result
