from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QProcess
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:  # pragma: no cover - fallback when WebEngine is unavailable
    QWebEngineView = None


class LauncherWindow(QMainWindow):
    def __init__(self, project_root: Path, checker, parent=None):
        super().__init__(parent)
        self.project_root = project_root
        self.checker = checker
        self.backend_process: QProcess | None = None

        self.setWindowTitle("MQTT Control Launcher")
        self.resize(1400, 900)

        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()

        title = QLabel("MQTT Control Launcher")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        subtitle = QLabel("Check dependencies, launch FastAPI, and display the dashboard.")
        subtitle.setStyleSheet("color: #6b7280;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.refresh_btn = QPushButton("Check dependencies")
        self.launch_btn = QPushButton("Launch project")
        self.open_btn = QPushButton("Open dashboard")

        self.refresh_btn.clicked.connect(self.refresh_report)
        self.launch_btn.clicked.connect(self.launch_project)
        self.open_btn.clicked.connect(self.open_dashboard)

        button_bar = QHBoxLayout()
        button_bar.setSpacing(10)
        button_bar.addWidget(self.refresh_btn)
        button_bar.addWidget(self.launch_btn)
        button_bar.addWidget(self.open_btn)

        header.addLayout(title_box, stretch=1)
        header.addLayout(button_bar)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)

        self.status_label = QLabel("Status: not checked")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: 600;")

        self.report_view = QPlainTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setFont(QFont("Consolas", 10))

        left_layout.addWidget(self.status_label)
        left_layout.addWidget(self.report_view, stretch=1)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)

        self.dashboard_tabs = QTabWidget()
        self.dashboard_tabs.addTab(self._build_dashboard_widget(), "Dashboard")
        right_layout.addWidget(self.dashboard_tabs, stretch=1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([420, 900])

        layout.addWidget(splitter, stretch=1)
        self.setCentralWidget(root)

        self.refresh_report()

    def _build_dashboard_widget(self) -> QWidget:
        if QWebEngineView is not None:
            view = QWebEngineView()
            dashboard_file = self.project_root / "mqtt-dashboard" / "index.html"
            view.setUrl(QUrl.fromLocalFile(str(dashboard_file)))
            return view

        fallback = QWidget()
        layout = QVBoxLayout(fallback)
        label = QLabel(
            "QWebEngineView is not available.\n"
            "Install PySide6-WebEngine to embed the dashboard here.\n"
            "The launcher still works and can open the dashboard in a browser."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        return fallback

    def log(self, message: str) -> None:
        current = self.report_view.toPlainText().strip()
        next_text = f"{current}\n{message}".strip() if current else message
        self.report_view.setPlainText(next_text)
        self.report_view.verticalScrollBar().setValue(self.report_view.verticalScrollBar().maximum())

    def refresh_report(self) -> None:
        report = self.checker()
        self.status_label.setText(f"Status: {'ready' if report.ok else 'attention needed'}")
        self.report_view.setPlainText("\n".join(report.summary_lines()))

    def launch_project(self) -> None:
        self.log("Launch requested.")
        self.refresh_report()

        if self.backend_process is not None and self.backend_process.state() != QProcess.NotRunning:
            self.log("Backend already running.")
            return

        self.backend_process = QProcess(self)
        self.backend_process.setWorkingDirectory(str(self.project_root))
        self.backend_process.setProgram(sys.executable)
        self.backend_process.setArguments(["-m", "uvicorn", "app.main:app", "--reload"])
        self.backend_process.readyReadStandardOutput.connect(self._read_backend_output)
        self.backend_process.readyReadStandardError.connect(self._read_backend_error)
        self.backend_process.start()
        self.log("FastAPI backend started.")

    def open_dashboard(self) -> None:
        dashboard_file = self.project_root / "mqtt-dashboard" / "index.html"
        if QWebEngineView is None:
            import webbrowser

            webbrowser.open(dashboard_file.as_uri())
            self.log("Dashboard opened in the default browser.")
            return

        self.dashboard_tabs.setCurrentIndex(0)
        self.log("Dashboard shown inside the launcher.")

    def _read_backend_output(self) -> None:
        if not self.backend_process:
            return
        text = bytes(self.backend_process.readAllStandardOutput()).decode("utf-8", errors="ignore").strip()
        if text:
            self.log(text)

    def _read_backend_error(self) -> None:
        if not self.backend_process:
            return
        text = bytes(self.backend_process.readAllStandardError()).decode("utf-8", errors="ignore").strip()
        if text:
            self.log(text)
