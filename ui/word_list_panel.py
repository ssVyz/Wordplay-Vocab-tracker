from __future__ import annotations

import logging

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import Rarity, WordEntry, WordType
from core.registry import WordRegistry

logger = logging.getLogger(__name__)

# Maps column index to the sort_by key expected by WordRegistry.get_words()
_COLUMN_SORT_KEYS: dict[int, str] = {
    0: "identified_word",
    1: "translation",
    2: "word_type",
    3: "rarity",
    4: "added_date",
}


class WordListPanel(QWidget):
    """Left panel showing a filterable, sortable table of words.

    Contains a filter bar at the top, a word table in the middle, and a
    bottom bar with quick-add and import buttons.
    """

    word_selected = Signal(object)  # WordEntry
    add_word_requested = Signal(str)
    import_text_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._registry: WordRegistry | None = None
        self._current_words: list[WordEntry] = []
        self._sort_column: int = 0
        self._sort_reverse: bool = False

        layout = QVBoxLayout(self)

        # --- Filter bar ---
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Filter words...")
        self._search_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._search_edit, stretch=1)

        self._type_combo = QComboBox()
        self._type_combo.addItem("All Types", None)
        for wt in WordType:
            self._type_combo.addItem(wt.value.capitalize(), wt)
        self._type_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._type_combo)

        self._rarity_combo = QComboBox()
        self._rarity_combo.addItem("All Rarities", None)
        for r in Rarity:
            self._rarity_combo.addItem(r.value.capitalize(), r)
        self._rarity_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._rarity_combo)

        layout.addLayout(filter_layout)

        # --- Word table ---
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Word", "Translation", "Type", "Rarity", "Date Added"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self._table.setSortingEnabled(False)  # We handle sorting ourselves
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

        # --- Bottom bar ---
        bottom_layout = QHBoxLayout()

        self._word_edit = QLineEdit()
        self._word_edit.setPlaceholderText("Enter a word...")
        self._word_edit.returnPressed.connect(self._on_add_word)
        bottom_layout.addWidget(self._word_edit, stretch=1)

        self._add_button = QPushButton("Add Word")
        self._add_button.clicked.connect(self._on_add_word)
        bottom_layout.addWidget(self._add_button)

        self._import_button = QPushButton("Import Text")
        self._import_button.clicked.connect(self._on_import_text)
        bottom_layout.addWidget(self._import_button)

        layout.addLayout(bottom_layout)

    def set_registry(self, registry: WordRegistry) -> None:
        """Bind to a word registry and refresh the table."""
        self._registry = registry
        self.refresh()

    def refresh(self) -> None:
        """Reload data from the registry using current filter and sort settings."""
        if self._registry is None:
            self._table.setRowCount(0)
            self._current_words = []
            return

        filter_type = self._type_combo.currentData()
        filter_rarity = self._rarity_combo.currentData()
        search_text = self._search_edit.text().strip()
        sort_by = _COLUMN_SORT_KEYS.get(self._sort_column, "identified_word")

        self._current_words = self._registry.get_words(
            sort_by=sort_by,
            sort_reverse=self._sort_reverse,
            filter_type=filter_type,
            filter_rarity=filter_rarity,
            search_text=search_text,
        )

        self._populate_table(self._current_words)

    def _populate_table(self, words: list[WordEntry]) -> None:
        """Fill the table widget from a list of WordEntry objects."""
        self._table.blockSignals(True)
        self._table.setRowCount(len(words))

        for row, entry in enumerate(words):
            word_item = QTableWidgetItem(entry.identified_word)
            word_item.setData(Qt.ItemDataRole.UserRole, row)
            self._table.setItem(row, 0, word_item)

            self._table.setItem(row, 1, QTableWidgetItem(entry.translation))
            self._table.setItem(
                row, 2, QTableWidgetItem(entry.word_type.value.capitalize())
            )
            self._table.setItem(
                row, 3, QTableWidgetItem(entry.rarity.value.capitalize())
            )
            self._table.setItem(row, 4, QTableWidgetItem(entry.added_date))

        self._table.blockSignals(False)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_filter_changed(self) -> None:
        self.refresh()

    def _on_header_clicked(self, logical_index: int) -> None:
        if self._sort_column == logical_index:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = logical_index
            self._sort_reverse = False
        self.refresh()

    def _on_selection_changed(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        row_index = rows[0].row()
        if 0 <= row_index < len(self._current_words):
            self.word_selected.emit(self._current_words[row_index])

    def _on_add_word(self) -> None:
        text = self._word_edit.text().strip()
        if text:
            self.add_word_requested.emit(text)
            self._word_edit.clear()

    def _on_import_text(self) -> None:
        self.import_text_requested.emit()
