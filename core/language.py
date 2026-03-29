from __future__ import annotations

import json
from pathlib import Path


def get_languages_dir() -> Path:
    """Return the path to the languages/ directory at the project root."""
    # This file lives at core/language.py, so go up one level to reach the project root
    return Path(__file__).resolve().parent.parent / "languages"


def list_languages() -> list[str]:
    """Scan the languages/ folder and return names of valid language buckets.

    A valid language bucket is a subfolder that contains a .config file.
    """
    languages_dir = get_languages_dir()
    if not languages_dir.exists():
        return []

    names: list[str] = []
    for entry in sorted(languages_dir.iterdir()):
        if entry.is_dir() and (entry / ".config").is_file():
            names.append(entry.name)
    return names


def create_language(name: str) -> Path:
    """Create a new language bucket under languages/<name>/.

    Creates the subfolder with a .config text file and an empty words.json.
    Returns the path to the new language folder.
    Raises ValueError if the language already exists.
    """
    languages_dir = get_languages_dir()
    language_path = languages_dir / name

    if language_path.exists():
        raise ValueError(f"Language '{name}' already exists.")

    language_path.mkdir(parents=True, exist_ok=False)

    # Write .config file
    config_file = language_path / ".config"
    config_file.write_text(f'language="{name}"\n', encoding="utf-8")

    # Write empty words.json
    words_file = language_path / "words.json"
    words_file.write_text(json.dumps([], indent=2) + "\n", encoding="utf-8")

    return language_path


def get_language_path(name: str) -> Path:
    """Return the path to an existing language folder.

    Raises ValueError if the language folder does not exist.
    """
    languages_dir = get_languages_dir()
    language_path = languages_dir / name

    if not language_path.exists() or not language_path.is_dir():
        raise ValueError(f"Language '{name}' does not exist.")

    return language_path
