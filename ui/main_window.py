from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
    QWidget,
)

from core.language import get_language_path, list_languages
from core.models import WordEntry
from core.registry import WordRegistry
from core.text_parser import tokenize_text
from LLM.service import LLMService
from ui.import_dialog import ImportDialog
from ui.language_selector import LanguageSelector
from ui.llm_panel import LLMPanel
from ui.word_detail_panel import WordDetailPanel
from ui.word_list_panel import WordListPanel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window for Wordplay.

    Ties together the language selector, word list panel, word detail panel,
    and LLM context panel.
    """

    def __init__(self, llm_service: LLMService) -> None:
        super().__init__()
        self.setWindowTitle("Wordplay")
        self.resize(1100, 700)

        self._llm_service = llm_service
        self._registry: WordRegistry | None = None

        self._build_ui()
        self._connect_signals()

        # If no languages exist, prompt to create one
        if not list_languages():
            self._prompt_create_first_language()
        else:
            # Trigger initial language load from the selector's current value
            lang = self._language_selector.current_language()
            if lang:
                self._on_language_changed(lang)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Toolbar with language selector
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._language_selector = LanguageSelector()
        toolbar.addWidget(self._language_selector)

        # Central splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: word list
        self._word_list_panel = WordListPanel()
        main_splitter.addWidget(self._word_list_panel)

        # Right: vertical splitter with detail + llm
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        self._word_detail_panel = WordDetailPanel()
        right_splitter.addWidget(self._word_detail_panel)

        self._llm_panel = LLMPanel()
        self._llm_panel.set_llm_service(self._llm_service)
        right_splitter.addWidget(self._llm_panel)

        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)

        main_splitter.addWidget(right_splitter)

        # Stretch factors: ~40% left, ~60% right
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 3)

        self.setCentralWidget(main_splitter)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._language_selector.language_changed.connect(self._on_language_changed)
        self._word_list_panel.word_selected.connect(self._on_word_selected)
        self._word_list_panel.add_word_requested.connect(self._on_add_word)
        self._word_list_panel.import_text_requested.connect(self._on_import_text)
        self._word_detail_panel.delete_requested.connect(self._on_delete_word)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_language_changed(self, language: str) -> None:
        try:
            path = get_language_path(language)
            self._registry = WordRegistry(path)
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            self._registry = None

        self._word_list_panel.set_registry(self._registry)
        self._word_detail_panel.show_word(None)
        self._llm_panel.clear()

    def _on_word_selected(self, entry: WordEntry) -> None:
        self._word_detail_panel.show_word(entry)
        lang = self._language_selector.current_language()
        self._llm_panel.set_current_word(entry.identified_word, lang)

    def _on_add_word(self, text: str) -> None:
        language = self._language_selector.current_language()
        if language is None or self._registry is None:
            QMessageBox.warning(self, "Error", "Please select a language first.")
            return

        dialog = ImportDialog(
            self, [text], language, self._llm_service, self._registry
        )
        if dialog.exec() == ImportDialog.DialogCode.Accepted:
            self._word_list_panel.refresh()

    def _on_import_text(self) -> None:
        language = self._language_selector.current_language()
        if language is None or self._registry is None:
            QMessageBox.warning(self, "Error", "Please select a language first.")
            return

        text, ok = QInputDialog.getMultiLineText(
            self, "Import Text", "Paste text to import words from:"
        )
        if not ok or not text.strip():
            return

        words = tokenize_text(text)
        if not words:
            QMessageBox.information(self, "Import", "No words found in text.")
            return

        dialog = ImportDialog(
            self, words, language, self._llm_service, self._registry
        )
        if dialog.exec() == ImportDialog.DialogCode.Accepted:
            self._word_list_panel.refresh()

    def _on_delete_word(self, identified_word: str) -> None:
        if self._registry is None:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f'Delete the word "{identified_word}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        removed = self._registry.remove_word(identified_word)
        if removed:
            logger.info("Deleted word: %s", identified_word)
        self._word_detail_panel.show_word(None)
        self._llm_panel.clear()
        self._word_list_panel.refresh()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _prompt_create_first_language(self) -> None:
        """Show a dialog asking the user to create the first language."""
        QMessageBox.information(
            self,
            "Welcome to Wordplay",
            "No languages found. Let's create your first one!",
        )
        # Delegate to the language selector's new-language button handler
        self._language_selector._on_new_language()
