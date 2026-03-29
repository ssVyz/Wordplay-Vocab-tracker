from __future__ import annotations

import logging
from typing import Callable

from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from LLM.service import LLMService

logger = logging.getLogger(__name__)


class LLMWorker(QThread):
    """General-purpose worker that runs a callable in a background thread.

    Emits *result_ready* with the return value on success or *error_occurred*
    with the exception message on failure.
    """

    result_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, func: Callable[[], str], parent=None) -> None:
        super().__init__(parent)
        self._func = func

    def run(self) -> None:
        try:
            result = self._func()
            self.result_ready.emit(result)
        except Exception as exc:
            logger.exception("LLM worker error")
            self.error_occurred.emit(str(exc))


class LLMPanel(QGroupBox):
    """Bottom-right panel for generating and displaying LLM context.

    Shows the availability status of the LLM service and allows generating
    context information for the currently selected word.
    """

    def __init__(self, parent=None) -> None:
        super().__init__("LLM Context", parent)

        self._llm_service: LLMService | None = None
        self._current_word: str | None = None
        self._current_language: str | None = None
        self._worker: LLMWorker | None = None

        layout = QVBoxLayout(self)

        # Status row
        status_layout = QHBoxLayout()
        self._status_label = QLabel("LLM Unavailable")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        self._generate_button = QPushButton("Generate Context")
        self._generate_button.setEnabled(False)
        self._generate_button.clicked.connect(self._on_generate)
        status_layout.addWidget(self._generate_button)

        layout.addLayout(status_layout)

        # Output area
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText(
            "Select a word and click Generate Context to see LLM analysis."
        )
        layout.addWidget(self._output)

    def set_llm_service(self, service: LLMService) -> None:
        """Bind the panel to an LLM service and update the status label."""
        self._llm_service = service
        if service.is_available():
            self._status_label.setText("LLM Ready")
        else:
            self._status_label.setText("LLM Unavailable")
        self._update_button_state()

    def set_current_word(self, word: str | None, language: str | None) -> None:
        """Set the word and language that the Generate button will act on."""
        self._current_word = word
        self._current_language = language
        self._output.clear()
        self._update_button_state()

    def clear(self) -> None:
        """Clear the panel state."""
        self._current_word = None
        self._current_language = None
        self._output.clear()
        self._update_button_state()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _update_button_state(self) -> None:
        enabled = (
            self._llm_service is not None
            and self._llm_service.is_available()
            and self._current_word is not None
            and self._current_language is not None
            and self._worker is None
        )
        self._generate_button.setEnabled(enabled)

    def _on_generate(self) -> None:
        if (
            self._llm_service is None
            or self._current_word is None
            or self._current_language is None
        ):
            return

        word = self._current_word
        language = self._current_language
        service = self._llm_service

        self._output.setPlainText("Generating...")
        self._generate_button.setEnabled(False)

        self._worker = LLMWorker(lambda: service.get_context(word, language))
        self._worker.result_ready.connect(self._on_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_result(self, text: str) -> None:
        self._output.setPlainText(text)

    def _on_error(self, message: str) -> None:
        self._output.setPlainText(f"Error: {message}")

    def _on_worker_finished(self) -> None:
        self._worker = None
        self._update_button_state()
