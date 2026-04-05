from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    """Settings dialog for configuring the LLM backend.

    Allows switching between Phi-3 (local) and Gemini (cloud) backends.
    Returns the selected backend name and API key (if Gemini) via
    ``selected_backend`` and ``gemini_api_key`` after acceptance.
    """

    def __init__(
        self,
        parent: QWidget | None,
        current_backend: str = "phi3",
        current_api_key: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)

        self.selected_backend: str = current_backend
        self.gemini_api_key: str = current_api_key

        layout = QVBoxLayout(self)

        # --- LLM Backend selection ---
        form = QFormLayout()

        self._backend_combo = QComboBox()
        self._backend_combo.addItem("Phi-3 (Local)", "phi3")
        self._backend_combo.addItem("Gemini 2.5 Flash (Cloud)", "gemini")
        # Set current selection
        for i in range(self._backend_combo.count()):
            if self._backend_combo.itemData(i) == current_backend:
                self._backend_combo.setCurrentIndex(i)
                break
        form.addRow("LLM Backend:", self._backend_combo)

        # --- Gemini API key ---
        self._api_key_input = QLineEdit()
        self._api_key_input.setPlaceholderText("Enter your Gemini API key")
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setText(current_api_key)
        self._api_key_label = QLabel("API Key:")
        form.addRow(self._api_key_label, self._api_key_input)

        layout.addLayout(form)

        # Show/hide API key field based on selection
        self._backend_combo.currentIndexChanged.connect(self._on_backend_changed)
        self._on_backend_changed()

        # --- Buttons ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._on_apply)
        button_layout.addWidget(apply_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _on_backend_changed(self) -> None:
        is_gemini = self._backend_combo.currentData() == "gemini"
        self._api_key_label.setVisible(is_gemini)
        self._api_key_input.setVisible(is_gemini)

    def _on_apply(self) -> None:
        self.selected_backend = self._backend_combo.currentData()
        self.gemini_api_key = self._api_key_input.text().strip()
        self.accept()
