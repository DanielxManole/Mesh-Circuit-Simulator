"""
Simulator circuite electrice — entry point.

Echipa 631AB Sg.2, FIIR-SIA (Andrei, Manole, Pralea).
Documentația proiectului se află în folderul `docs/`.
"""

import sys
import logging

from PyQt6.QtWidgets import QApplication

from src.persistence import setup_logging
from src.ui.main_window import MainWindow


def _global_stylesheet() -> str:
    return """
    QMainWindow, QWidget { background: #ffffff; color: #212121; }
    QStatusBar { background: #f5f7fa; border-top: 1px solid #e0e0e0; }
    QToolBar  { background: #f5f7fa; border-bottom: 1px solid #e0e0e0; spacing: 4px; padding: 4px; }
    QMenuBar  { background: #f5f7fa; }
    QMenuBar::item:selected { background: #e3eaf2; }
    QPushButton {
        background: #1976d2; color: white; border: 0; padding: 6px 12px; border-radius: 4px;
    }
    QPushButton:hover  { background: #1565c0; }
    QPushButton:pressed{ background: #0d47a1; }
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
        border: 1px solid #cfd8dc; border-radius: 3px; padding: 3px 6px;
        background: white; selection-background-color: #bbdefb;
    }
    QGroupBox {
        border: 1px solid #e0e0e0; border-radius: 4px; margin-top: 8px;
        font-weight: 600;
    }
    QGroupBox::title {
        subcontrol-origin: margin; left: 8px; padding: 0 4px;
        background: white; color: #455a64;
    }
    QTreeWidget, QTableWidget, QTextEdit {
        border: 1px solid #e0e0e0; background: white;
    }
    QHeaderView::section {
        background: #eceff1; padding: 4px; border: 0; border-right: 1px solid #cfd8dc;
        font-weight: 600;
    }
    QTabWidget::pane { border: 1px solid #e0e0e0; top: -1px; }
    QTabBar::tab {
        background: #eceff1; padding: 5px 12px; border: 1px solid #e0e0e0;
        border-bottom: 0; border-top-left-radius: 3px; border-top-right-radius: 3px;
    }
    QTabBar::tab:selected { background: white; color: #1976d2; font-weight: 600; }
    """


def main():
    setup_logging()
    logging.getLogger().info("Pornesc Simulatorul de circuite electrice…")

    app = QApplication(sys.argv)
    app.setApplicationName("Simulator circuite electrice")
    app.setOrganizationName("FIIR-SIA")
    app.setStyleSheet(_global_stylesheet())

    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
