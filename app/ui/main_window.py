"""PyQt6 main window for QuantDesk."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.loader import load_strategy
from app.config.models import StrategyConfig


class StrategyEditor(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.editor = QTextEdit(self)
        self.editor.setPlaceholderText("Load a strategy YAML file to edit…")
        layout.addWidget(self.editor)

    def load_file(self, path: Path) -> None:
        self.editor.setText(path.read_text(encoding="utf-8"))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QuantDesk – Educational Market Lab")
        self.resize(1200, 800)
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.dashboard_tab = QLabel("Dashboard coming soon")
        self.screener_tab = QLabel("Screener placeholder")
        self.strategy_tab = StrategyEditor()
        self.backtest_tab = QLabel("Run backtests from CLI for now")
        self.paper_tab = QLabel("Paper trading status")
        self.logs_tab = QTextEdit()
        self.settings_tab = QLabel("Settings TBD")

        for name, widget in [
            ("Dashboard", self.dashboard_tab),
            ("Screener", self.screener_tab),
            ("Strategy", self.strategy_tab),
            ("Backtest", self.backtest_tab),
            ("Paper Trade", self.paper_tab),
            ("Logs", self.logs_tab),
            ("Settings", self.settings_tab),
        ]:
            self.tabs.addTab(widget, name)

        disclaimer = QLabel(
            "Educational tool. Not financial advice. Markets carry risk.",
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        disclaimer.setObjectName("disclaimer")
        self.statusBar().addPermanentWidget(disclaimer)
        self._create_menu()

    def _create_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        open_action = QAction("Open Strategy", self)
        open_action.triggered.connect(self._open_strategy)  # type: ignore[attr-defined]
        file_menu.addAction(open_action)

    def _open_strategy(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open strategy",
            str(Path("assets/strategies").absolute()),
            "YAML Files (*.yaml *.yml)",
        )
        if not path:
            return
        try:
            strategy = load_strategy(Path(path))
        except Exception as exc:  # pragma: no cover - UI dialog
            QMessageBox.critical(self, "Failed to load strategy", str(exc))
            return
        self.strategy_tab.load_file(Path(path))
        self.statusBar().showMessage(f"Loaded strategy: {strategy.name}", 5000)


def create_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def launch_main_window() -> None:
    app = create_app()
    window = MainWindow()
    window.show()
    app.exec()


__all__ = ["MainWindow", "launch_main_window"]
