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


def extract_word_contexts(text: str, words: list[str]) -> dict[str, str]:
    """Build a context snippet for each word from its surrounding text.

    For each word, provides ~2 words before and ~2 words after. At sentence
    boundaries (defined by '.', '!', '?') the window extends to up to 4 words
    on the side that has room.

    Returns a dict mapping each lowercased word to a context string such as
    ``"die kleine [Katze] lief schnell"``.  Words that cannot be located in
    *text* are omitted from the result.
    """
    # Split text into tokens preserving both words and sentence-ending punctuation
    tokens = re.findall(r"[\w]+|[.!?]", text, re.UNICODE)
    tokens_lower = [t.lower() for t in tokens]

    # Build a set of sentence-end indices for quick lookup
    sentence_ends: set[int] = set()
    for i, t in enumerate(tokens):
        if t in ".!?":
            sentence_ends.add(i)

    # For each target word, find its first occurrence and extract context
    target_set = set(words)
    contexts: dict[str, str] = {}

    for i, token_low in enumerate(tokens_lower):
        if token_low not in target_set or token_low in contexts:
            continue

        # Determine how many words we can grab on each side.
        # Default: 2 before, 2 after.  At sentence boundary: shift to 4 on
        # the open side.

        # Walk backwards to collect preceding word tokens (skip punctuation tokens)
        before: list[str] = []
        j = i - 1
        at_sentence_start = False
        while j >= 0 and len(before) < 4:
            if j in sentence_ends:
                at_sentence_start = True
                break
            if not tokens[j] in ".!?":
                before.append(tokens[j])
            j -= 1
        if j < 0:
            at_sentence_start = True
        before.reverse()

        # Walk forwards to collect following word tokens
        after: list[str] = []
        j = i + 1
        at_sentence_end = False
        while j < len(tokens) and len(after) < 4:
            if j in sentence_ends:
                at_sentence_end = True
                break
            if not tokens[j] in ".!?":
                after.append(tokens[j])
            j += 1
        if j >= len(tokens):
            at_sentence_end = True

        # Apply the 2/4 rule
        if at_sentence_start and not at_sentence_end:
            # Can't get much before -> take up to 4 after, up to 1 before
            before = before[-1:] if before else []
            after = after[:4]
        elif at_sentence_end and not at_sentence_start:
            # Can't get much after -> take up to 4 before, up to 1 after
            before = before[-4:]
            after = after[:1] if after else []
        else:
            # Normal case or both boundaries -> 2 each (whatever is available)
            before = before[-2:]
            after = after[:2]

        snippet_parts = before + [f"[{tokens[i]}]"] + after
        contexts[token_low] = " ".join(snippet_parts)

    return contexts
