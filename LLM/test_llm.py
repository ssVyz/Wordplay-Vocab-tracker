"""Standalone Tkinter UI for testing LLM functions independently of PySide6."""

from __future__ import annotations

import sys
import threading
import traceback
from pathlib import Path

# Ensure the project root is on sys.path so that imports work
# when running via `python LLM/test_llm.py` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk
from tkinter import scrolledtext, messagebox

from LLM.config import LLMConfig, load_config, save_config
from LLM.phi3_backend import Phi3Backend


class TestLLMApp:
    """Main application window for testing LLM functions."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("LLM Test UI")
        self.root.geometry("720x700")
        self.root.minsize(600, 550)

        self.backend: Phi3Backend | None = None
        self._config = load_config()

        self._build_ui()
        self._populate_config_fields()

        # Kick off model loading in a background thread.
        self._load_model_async()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ---- Config Section ----
        config_frame = tk.LabelFrame(self.root, text="Config", padx=8, pady=8)
        config_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        labels = ["model_path", "n_ctx", "n_gpu_layers", "temperature", "max_tokens"]
        self.config_vars: dict[str, tk.StringVar] = {}

        for idx, name in enumerate(labels):
            tk.Label(config_frame, text=name, anchor="w", width=14).grid(
                row=idx, column=0, sticky="w", pady=2
            )
            var = tk.StringVar()
            entry = tk.Entry(config_frame, textvariable=var, width=50)
            entry.grid(row=idx, column=1, sticky="ew", padx=(4, 0), pady=2)
            self.config_vars[name] = var

        config_frame.columnconfigure(1, weight=1)

        btn_row = tk.Frame(config_frame)
        btn_row.grid(row=len(labels), column=0, columnspan=2, pady=(6, 0))

        tk.Button(btn_row, text="Save Config", width=14, command=self._on_save_config).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        tk.Button(btn_row, text="Reload Model", width=14, command=self._on_reload_model).pack(
            side=tk.LEFT
        )

        # ---- Test Section ----
        test_frame = tk.LabelFrame(self.root, text="Test", padx=8, pady=8)
        test_frame.pack(fill=tk.X, padx=8, pady=4)

        tk.Label(test_frame, text="Language", anchor="w", width=14).grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.language_var = tk.StringVar(value="German")
        tk.Entry(test_frame, textvariable=self.language_var, width=30).grid(
            row=0, column=1, sticky="ew", padx=(4, 0), pady=2
        )

        tk.Label(test_frame, text="Word", anchor="w", width=14).grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.word_var = tk.StringVar(value="laufen")
        tk.Entry(test_frame, textvariable=self.word_var, width=30).grid(
            row=1, column=1, sticky="ew", padx=(4, 0), pady=2
        )

        test_frame.columnconfigure(1, weight=1)

        test_btn_row = tk.Frame(test_frame)
        test_btn_row.grid(row=2, column=0, columnspan=2, pady=(6, 0))

        self.btn_analyze = tk.Button(
            test_btn_row, text="Test Analyze Word", width=18, command=self._on_analyze_word
        )
        self.btn_analyze.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_context = tk.Button(
            test_btn_row, text="Test Get Context", width=18, command=self._on_get_context
        )
        self.btn_context.pack(side=tk.LEFT)

        # ---- Output Section ----
        output_frame = tk.LabelFrame(self.root, text="Output", padx=8, pady=8)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 10)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # ---- Status Bar ----
        self.status_var = tk.StringVar(value="Initializing...")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var, anchor="w",
            relief=tk.SUNKEN, padx=4, pady=2
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 8))

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    def _populate_config_fields(self) -> None:
        """Fill the config entry fields from the current LLMConfig."""
        self.config_vars["model_path"].set(self._config.model_path)
        self.config_vars["n_ctx"].set(str(self._config.n_ctx))
        self.config_vars["n_gpu_layers"].set(str(self._config.n_gpu_layers))
        self.config_vars["temperature"].set(str(self._config.temperature))
        self.config_vars["max_tokens"].set(str(self._config.max_tokens))

    def _read_config_from_fields(self) -> LLMConfig:
        """Parse the current entry field values into an LLMConfig."""
        return LLMConfig(
            model_path=self.config_vars["model_path"].get().strip(),
            n_ctx=int(self.config_vars["n_ctx"].get()),
            n_gpu_layers=int(self.config_vars["n_gpu_layers"].get()),
            temperature=float(self.config_vars["temperature"].get()),
            max_tokens=int(self.config_vars["max_tokens"].get()),
        )

    # ------------------------------------------------------------------
    # Output / status helpers
    # ------------------------------------------------------------------

    def _append_output(self, text: str) -> None:
        """Append text to the output widget (thread-safe via root.after)."""
        def _do() -> None:
            self.output_text.configure(state=tk.NORMAL)
            self.output_text.insert(tk.END, text + "\n")
            self.output_text.see(tk.END)
            self.output_text.configure(state=tk.DISABLED)

        self.root.after(0, _do)

    def _set_status(self, text: str) -> None:
        """Update the status bar (thread-safe via root.after)."""
        self.root.after(0, lambda: self.status_var.set(text))

    def _set_buttons_state(self, state: str) -> None:
        """Enable or disable the test buttons (thread-safe)."""
        def _do() -> None:
            self.btn_analyze.configure(state=state)
            self.btn_context.configure(state=state)

        self.root.after(0, _do)

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model_async(self) -> None:
        """Load the LLM backend in a background thread."""
        self._set_status("Loading model...")
        self._set_buttons_state(tk.DISABLED)
        self._append_output("--- Loading model ---")

        def _work() -> None:
            try:
                self.backend = Phi3Backend(self._config)
                if self.backend.is_available():
                    self._append_output("Model loaded successfully.")
                    self._set_status("LLM loaded and available")
                    self._set_buttons_state(tk.NORMAL)
                else:
                    self._append_output("Model object created but is NOT available.")
                    self._set_status("LLM NOT available (model failed to load)")
            except Exception:
                tb = traceback.format_exc()
                self._append_output(f"Failed to load model:\n{tb}")
                self._set_status("LLM NOT available (error during load)")

        threading.Thread(target=_work, daemon=True).start()

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_save_config(self) -> None:
        """Validate fields, save to disk, and update internal config."""
        try:
            cfg = self._read_config_from_fields()
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Invalid config", f"Could not parse config values:\n{exc}")
            return

        save_config(cfg)
        self._config = cfg
        self._append_output("Config saved to LLM/.config")

    def _on_reload_model(self) -> None:
        """Re-read fields and reload the model."""
        try:
            cfg = self._read_config_from_fields()
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Invalid config", f"Could not parse config values:\n{exc}")
            return

        self._config = cfg
        self._load_model_async()

    def _on_analyze_word(self) -> None:
        """Run analyze_word in a background thread."""
        word = self.word_var.get().strip()
        language = self.language_var.get().strip()
        if not word or not language:
            messagebox.showwarning("Input required", "Please enter both a language and a word.")
            return

        self._set_buttons_state(tk.DISABLED)
        self._set_status("Processing analyze_word...")
        self._append_output(f"\n--- analyze_word(word={word!r}, language={language!r}) ---")
        self._append_output("Processing...")

        def _work() -> None:
            try:
                result = self.backend.analyze_word(word, language)
                lines = [
                    "Result:",
                    f"  base_form   : {result.base_form}",
                    f"  translation : {result.translation}",
                    f"  word_type   : {result.word_type.value}",
                    f"  rarity      : {result.rarity.value}",
                ]
                self._append_output("\n".join(lines))
                self._set_status("analyze_word complete")
            except Exception:
                tb = traceback.format_exc()
                self._append_output(f"Error:\n{tb}")
                self._set_status("analyze_word failed")
            finally:
                self._set_buttons_state(tk.NORMAL)

        threading.Thread(target=_work, daemon=True).start()

    def _on_get_context(self) -> None:
        """Run get_context in a background thread."""
        word = self.word_var.get().strip()
        language = self.language_var.get().strip()
        if not word or not language:
            messagebox.showwarning("Input required", "Please enter both a language and a word.")
            return

        self._set_buttons_state(tk.DISABLED)
        self._set_status("Processing get_context...")
        self._append_output(f"\n--- get_context(word={word!r}, language={language!r}) ---")
        self._append_output("Processing...")

        def _work() -> None:
            try:
                result = self.backend.get_context(word, language)
                self._append_output(f"Result:\n{result}")
                self._set_status("get_context complete")
            except Exception:
                tb = traceback.format_exc()
                self._append_output(f"Error:\n{tb}")
                self._set_status("get_context failed")
            finally:
                self._set_buttons_state(tk.NORMAL)

        threading.Thread(target=_work, daemon=True).start()


def main() -> None:
    root = tk.Tk()
    TestLLMApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
