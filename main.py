from __future__ import annotations

import sys
import logging

from PySide6.QtWidgets import QApplication

from LLM import get_llm_service
from ui.main_window import MainWindow

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(name)s: %(message)s")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Wordplay")

    llm_service = get_llm_service()

    window = MainWindow(llm_service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
