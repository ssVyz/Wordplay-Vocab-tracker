from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.models import WordEntry


class WordDetailPanel(QGroupBox):
    """Top-right panel showing details of the currently selected word.

    Displays all fields of a WordEntry as read-only labels, plus a delete button.
    """

    delete_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__("Word Details", parent)

        outer_layout = QVBoxLayout(self)

        form = QFormLayout()

        self._import_string_label = QLabel()
        self._import_string_label.setWordWrap(True)
        form.addRow("Import String:", self._import_string_label)

        self._identified_word_label = QLabel()
        self._identified_word_label.setWordWrap(True)
        form.addRow("Identified Word:", self._identified_word_label)

        self._translation_label = QLabel()
        self._translation_label.setWordWrap(True)
        form.addRow("Translation:", self._translation_label)

        self._type_label = QLabel()
        form.addRow("Type:", self._type_label)

        self._rarity_label = QLabel()
        form.addRow("Rarity:", self._rarity_label)

        self._date_label = QLabel()
        form.addRow("Date Added:", self._date_label)

        outer_layout.addLayout(form)
        outer_layout.addStretch()

        self._delete_button = QPushButton("Delete Word")
        self._delete_button.setEnabled(False)
        self._delete_button.clicked.connect(self._on_delete)
        outer_layout.addWidget(self._delete_button)

        self._current_word: str | None = None

    def show_word(self, entry: WordEntry | None) -> None:
        """Populate the detail fields from a WordEntry, or clear them if None."""
        if entry is None:
            self._import_string_label.clear()
            self._identified_word_label.clear()
            self._translation_label.clear()
            self._type_label.clear()
            self._rarity_label.clear()
            self._date_label.clear()
            self._delete_button.setEnabled(False)
            self._current_word = None
            return

        self._import_string_label.setText(entry.import_string)
        self._identified_word_label.setText(entry.identified_word)
        self._translation_label.setText(entry.translation)
        self._type_label.setText(entry.word_type.value.capitalize())
        self._rarity_label.setText(entry.rarity.value.capitalize())
        self._date_label.setText(entry.added_date)
        self._delete_button.setEnabled(True)
        self._current_word = entry.identified_word

    def _on_delete(self) -> None:
        if self._current_word is not None:
            self.delete_requested.emit(self._current_word)
