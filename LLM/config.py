from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LLMConfig:
    """Configuration for the LLM backend."""
    model_path: str = "models/Phi-3-mini-4k-instruct-q4.gguf"
    n_ctx: int = 2048
    n_gpu_layers: int = 0
    temperature: float = 0.3
    max_tokens: int = 512


# Field types for parsing config values
_FIELD_TYPES: dict[str, type] = {
    "model_path": str,
    "n_ctx": int,
    "n_gpu_layers": int,
    "temperature": float,
    "max_tokens": int,
}


def get_config_path() -> Path:
    """Return the path to the .config file in the LLM/ directory."""
    return Path(__file__).parent / ".config"


def load_config() -> LLMConfig:
    """Read the .config file and return an LLMConfig.

    Missing fields fall back to defaults. If the file does not exist
    or cannot be parsed, a default config is returned.
    """
    config = LLMConfig()
    path = get_config_path()

    if not path.exists():
        return config

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return config

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, _, raw_value = line.partition("=")
        key = key.strip()
        raw_value = raw_value.strip()

        if key not in _FIELD_TYPES:
            continue

        field_type = _FIELD_TYPES[key]
        try:
            if field_type is str:
                # Strip surrounding quotes if present
                value = raw_value.strip('"').strip("'")
            else:
                value = field_type(raw_value)
            setattr(config, key, value)
        except (ValueError, TypeError):
            # Keep the default for this field
            pass

    return config


def save_config(config: LLMConfig) -> None:
    """Write the config to the .config file in TOML-style plain text."""
    path = get_config_path()
    lines = [
        f'model_path = "{config.model_path}"',
        f"n_ctx = {config.n_ctx}",
        f"n_gpu_layers = {config.n_gpu_layers}",
        f"temperature = {config.temperature}",
        f"max_tokens = {config.max_tokens}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
