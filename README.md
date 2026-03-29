# Wordplay

A vocabulary learning aid for tracking words across multiple languages. Words are analyzed by a local LLM (Phi-3) which identifies base forms, translations, word types, and rarity.

## How it works

1. **Create a language** — On first launch you are prompted to create a language bucket (e.g. "German"). Each language gets its own folder under `languages/` with a `words.json` registry.

2. **Import words** — Type a single word in the bottom-left field, or click **Import Text** to paste a larger passage. The text is tokenized into individual words, each word is sent to the LLM for analysis, and the results appear in an import dialog where you can review and edit every field before committing.

3. **Browse and filter** — The word list supports sorting by any column (click headers) and filtering by text search, word type, or rarity.

4. **Get context from the LLM** — Select a word and click **Generate Context** to get conjugations, example sentences, and usage notes in the bottom-right panel.

5. **Graceful degradation** — If the LLM fails to load the app still starts; you can browse your registry but import analysis and context generation are disabled.

## Project structure

```
wordplay/
├── main.py                  # Entry point
├── core/
│   ├── models.py            # WordEntry, WordType, Rarity
│   ├── registry.py          # WordRegistry (JSON CRUD, filter, sort)
│   ├── language.py          # Language bucket management
│   └── text_parser.py       # Text tokenization for import
├── LLM/
│   ├── service.py           # Abstract LLMService interface
│   ├── phi3_backend.py      # Phi-3 implementation (llama-cpp-python)
│   ├── config.py            # LLM config management
│   ├── .config              # Model settings (TOML-style)
│   ├── test_llm.py          # Standalone Tkinter test UI
│   └── models/              # GGUF model files
├── ui/
│   ├── main_window.py       # 3-panel QMainWindow
│   ├── word_list_panel.py   # Left: filterable word table
│   ├── word_detail_panel.py # Top-right: selected word metadata
│   ├── llm_panel.py         # Bottom-right: LLM context output
│   ├── import_dialog.py     # Word import dialog
│   └── language_selector.py # Language switcher
└── languages/               # Per-language data (created at runtime)
```

The three layers — **core**, **LLM**, and **ui** — are decoupled. The LLM layer exposes a generic `LLMService` interface so the backend can be swapped (e.g. to a cloud API) without touching the rest of the app. The UI layer only depends on core and the LLM interface, making it replaceable as well.

## Running

```
uv run python main.py
```

To test LLM functions independently:

```
uv run python LLM/test_llm.py
```

## Dependencies

- **PySide6** — Main application UI
- **llama-cpp-python** — Local LLM inference (Phi-3 GGUF)
