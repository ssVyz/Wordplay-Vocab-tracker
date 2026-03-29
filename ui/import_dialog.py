from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import Signal, Qt, QThread
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import Rarity, WordEntry, WordType
from core.registry import WordRegistry
from LLM.service import LLMService, WordAnalysis

logger = logging.getLogger(__name__)

_DUPLICATE_COLOR = QColor(255, 200, 200)  # Light pink for duplicates


class ImportWorker(QThread):
    """Background worker that analyses a batch of words through the LLM.

    Emits *word_processed* for each word with its index and the analysis
    result (or None on error).  Emits *all_done* when the batch is complete.
    """

    word_processed = Signal(int, object)  # (index, WordAnalysis | None)
    all_done = Signal()

    def __init__(
        self,
        words: list[str],
        language: str,
        llm_service: LLMService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._words = words
        self._language = language
        self._llm_service = llm_service

    def run(self) -> None:
        for idx, word in enumerate(self._words):
            try:
                analysis = self._llm_service.analyze_word(word, self._language)
                self.word_processed.emit(idx, analysis)
            except Exception as exc:
                logger.warning("LLM analysis failed for '%s': %s", word, exc)
                self.word_processed.emit(idx, None)
        self.all_done.emit()


class ImportDialog(QDialog):
    """Modal dialog for importing words with optional LLM analysis.

    Processes each supplied word through the LLM in a background thread,
    displays results in an editable table, and allows the user to submit
    new (non-duplicate) words into the registry.
    """

    def __init__(
        self,
        parent: QWidget | None,
        words: list[str],
        language: str,
        llm_service: LLMService,
        registry: WordRegistry,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import Words")
        self.setMinimumSize(750, 450)
        self.resize(850, 520)

        self._words = words
        self._language = language
        self._llm_service = llm_service
        self._registry = registry
        self._worker: ImportWorker | None = None
        self._type_combos: list[QComboBox] = []
        self._rarity_combos: list[QComboBox] = []

        layout = QVBoxLayout(self)

        # --- Progress area ---
        self._progress_label = QLabel("Preparing...")
        layout.addWidget(self._progress_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, len(words))
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # --- Table ---
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Import String", "Identified Word", "Translation", "Type", "Rarity", "Status"]
        )
        self._table.setRowCount(len(words))
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)

        # Pre-populate rows with the import strings
        for row, word in enumerate(words):
            # Import string (read-only)
            import_item = QTableWidgetItem(word)
            import_item.setFlags(import_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, import_item)

            # Identified word (editable, starts empty)
            self._table.setItem(row, 1, QTableWidgetItem(""))

            # Translation (editable, starts empty)
            self._table.setItem(row, 2, QTableWidgetItem(""))

            # Type combo
            type_combo = QComboBox()
            for wt in WordType:
                type_combo.addItem(wt.value.capitalize(), wt)
            self._table.setCellWidget(row, 3, type_combo)
            self._type_combos.append(type_combo)

            # Rarity combo
            rarity_combo = QComboBox()
            for r in Rarity:
                rarity_combo.addItem(r.value.capitalize(), r)
            self._table.setCellWidget(row, 4, rarity_combo)
            self._rarity_combos.append(rarity_combo)

            # Status (read-only)
            status_item = QTableWidgetItem("Pending")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 5, status_item)

        layout.addWidget(self._table)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._submit_button = QPushButton("Submit")
        self._submit_button.setEnabled(False)
        self._submit_button.clicked.connect(self._on_submit)
        button_layout.addWidget(self._submit_button)

        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_button)

        layout.addLayout(button_layout)

        # Start processing
        self._start_processing()

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def _start_processing(self) -> None:
        """Kick off the LLM worker or fall back to manual entry."""
        if not self._llm_service.is_available():
            self._progress_label.setText(
                "LLM is unavailable. Please fill in the fields manually."
            )
            self._progress_bar.setRange(0, 1)
            self._progress_bar.setValue(1)
            self._finalize_statuses()
            self._submit_button.setEnabled(True)
            return

        self._progress_label.setText(f"Processing word 0/{len(self._words)}...")
        self._worker = ImportWorker(
            self._words, self._language, self._llm_service, self
        )
        self._worker.word_processed.connect(self._on_word_processed)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.start()

    def _on_word_processed(self, index: int, analysis: WordAnalysis | None) -> None:
        """Populate row *index* with analysis results (if any)."""
        self._progress_bar.setValue(index + 1)
        self._progress_label.setText(
            f"Processing word {index + 1}/{len(self._words)}..."
        )

        if analysis is not None:
            self._table.item(index, 1).setText(analysis.base_form)
            self._table.item(index, 2).setText(analysis.translation)

            # Set type combo
            for i in range(self._type_combos[index].count()):
                if self._type_combos[index].itemData(i) == analysis.word_type:
                    self._type_combos[index].setCurrentIndex(i)
                    break

            # Set rarity combo
            for i in range(self._rarity_combos[index].count()):
                if self._rarity_combos[index].itemData(i) == analysis.rarity:
                    self._rarity_combos[index].setCurrentIndex(i)
                    break

        # Update status
        self._update_row_status(index)

    def _on_all_done(self) -> None:
        self._progress_label.setText("Processing complete.")
        self._finalize_statuses()
        self._submit_button.setEnabled(True)
        self._worker = None

    def _finalize_statuses(self) -> None:
        """Refresh the status column for every row."""
        for row in range(self._table.rowCount()):
            self._update_row_status(row)

    def _update_row_status(self, row: int) -> None:
        """Mark a row as New or Duplicate based on the registry."""
        identified = self._table.item(row, 1).text().strip()
        if identified and self._registry.has_word(identified):
            self._table.item(row, 5).setText("Duplicate")
            self._set_row_background(row, _DUPLICATE_COLOR)
        else:
            if identified:
                self._table.item(row, 5).setText("New")
            else:
                self._table.item(row, 5).setText("Pending")
            self._set_row_background(row, QColor(Qt.GlobalColor.white))

    def _set_row_background(self, row: int, color: QColor) -> None:
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item is not None:
                item.setBackground(color)

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------

    def _on_submit(self) -> None:
        entries: list[WordEntry] = []
        now = datetime.now().isoformat()

        for row in range(self._table.rowCount()):
            import_string = self._table.item(row, 0).text().strip()
            identified = self._table.item(row, 1).text().strip()
            translation = self._table.item(row, 2).text().strip()
            word_type: WordType = self._type_combos[row].currentData()
            rarity: Rarity = self._rarity_combos[row].currentData()

            # Skip rows with no identified word or that are duplicates
            if not identified:
                continue
            if self._registry.has_word(identified):
                continue

            entries.append(
                WordEntry(
                    import_string=import_string,
                    identified_word=identified,
                    translation=translation,
                    word_type=word_type,
                    rarity=rarity,
                    added_date=now,
                )
            )

        if entries:
            added = self._registry.add_words(entries)
            QMessageBox.information(
                self,
                "Import Complete",
                f"Added {added} word(s) to the registry.",
            )
        else:
            QMessageBox.information(
                self, "Import Complete", "No new words were imported."
            )

        self.accept()

    # ------------------------------------------------------------------
    # Override close to clean up worker
    # ------------------------------------------------------------------

    def reject(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(3000)
        super().reject()
