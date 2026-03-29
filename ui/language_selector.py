from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
)

from core.language import create_language, list_languages

logger = logging.getLogger(__name__)


class LanguageSelector(QWidget):
    """Widget for selecting and creating languages.

    Contains a combo box populated from the languages directory and a button
    to create new languages.
    """

    language_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Language:"))

        self._combo = QComboBox()
        self._combo.setMinimumWidth(150)
        self._combo.currentTextChanged.connect(self._on_selection_changed)
        layout.addWidget(self._combo)

        self._new_button = QPushButton("New Language")
        self._new_button.clicked.connect(self._on_new_language)
        layout.addWidget(self._new_button)

        self.refresh()

    def refresh(self) -> None:
        """Reload the language list from disk and repopulate the combo box."""
        previous = self._combo.currentText()
        self._combo.blockSignals(True)
        self._combo.clear()

        languages = list_languages()
        self._combo.addItems(languages)

        # Try to restore previous selection
        if previous and previous in languages:
            self._combo.setCurrentText(previous)

        self._combo.blockSignals(False)

        # Emit the current selection so listeners can update
        current = self.current_language()
        if current is not None:
            self.language_changed.emit(current)

    def current_language(self) -> str | None:
        """Return the currently selected language name, or None if nothing is selected."""
        text = self._combo.currentText()
        return text if text else None

    def _on_selection_changed(self, text: str) -> None:
        if text:
            self.language_changed.emit(text)

    def _on_new_language(self) -> None:
        name, ok = QInputDialog.getText(
            self, "New Language", "Enter language name:"
        )
        if not ok or not name.strip():
            return

        name = name.strip()
        try:
            create_language(name)
            logger.info("Created language: %s", name)
            self._combo.blockSignals(True)
            self.refresh()
            self._combo.blockSignals(False)
            self._combo.setCurrentText(name)
            self.language_changed.emit(name)
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
