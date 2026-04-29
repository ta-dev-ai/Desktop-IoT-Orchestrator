from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from PySide6.QtCore import QProcess, QTimer, QUrl
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtWebEngineCore import QWebEngineSettings
    from PySide6.QtWebEngineWidgets import QWebEngineView


except Exception:  # pragma: no cover - fallback when WebEngine is unavailable
    QWebEngineView = None


class LauncherWindow(QMainWindow):
    def __init__(self, project_root: Path, checker, parent=None):
        super().__init__(parent)
        self.project_root = project_root
        self.checker = checker
        self.backend_process: QProcess | None = None
        self.dashboard_view: QWebEngineView | None = None
        self.boot_started = False

        self.setWindowTitle("MQTT Control Launcher")
        self._resize_for_screen()

        self._build_ui()
        self._show_page("dashboard")
        QTimer.singleShot(250, self._auto_boot)

    def _resolve_python_executable(self) -> str:
        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        return sys.executable

    def _resize_for_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1480, 900)
            return

        geometry = screen.availableGeometry()
        target_width = min(1480, max(1180, int(geometry.width() * 0.9)))
        target_height = min(920, max(760, int(geometry.height() * 0.88)))

        self.resize(target_width, target_height)

        # Center the launcher on the available desktop area.
        x = geometry.x() + max(0, (geometry.width() - target_width) // 2)
        y = geometry.y() + max(0, (geometry.height() - target_height) // 2)
        self.move(x, y)

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        layout.addLayout(self._build_header())

        self.alert_bar = QFrame()
        self.alert_bar.setObjectName("alertBar")
        self.alert_bar.hide()
        alert_layout = QHBoxLayout(self.alert_bar)
        alert_layout.setContentsMargins(10, 6, 10, 6)
        alert_layout.setSpacing(8)

        self.alert_label = QLabel("")
        self.alert_label.setWordWrap(False)
        self.alert_label.setStyleSheet(
            "color: #9a3412; font-weight: 600; font-size: 12px;"
        )

        self.alert_settings_btn = QPushButton("Voir Settings")
        self.alert_settings_btn.clicked.connect(lambda: self._show_page("settings"))
        self.alert_settings_btn.setStyleSheet(
            "background: #ffffff; border: 1px solid #fdba74; border-radius: 9px; padding: 5px 10px; font-size: 12px;"
        )

        alert_layout.addWidget(self.alert_label, stretch=1)
        alert_layout.addWidget(self.alert_settings_btn)
        self.alert_bar.setStyleSheet(
            """
            QFrame#alertBar {
                background: #fffaf3;
                border: 1px solid #fdba74;
                border-radius: 10px;
                min-height: 34px;
            }
            """
        )
        layout.addWidget(self.alert_bar)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_dashboard_page())
        self.pages.addWidget(self._build_settings_page())
        layout.addWidget(self.pages, stretch=1)

        self.setCentralWidget(root)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        title_box = QVBoxLayout()

        self.page_title = QLabel("MQTT Control Launcher")
        self.page_title.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #0f172a;"
        )
        self.page_subtitle = QLabel(
            "Le dashboard du projet reste la navigation principale."
        )
        self.page_subtitle.setStyleSheet("color: #64748b; font-size: 14px;")

        title_box.addWidget(self.page_title)
        title_box.addWidget(self.page_subtitle)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(lambda: self._show_page("settings"))
        self.settings_btn.setStyleSheet(
            "background: #ffffff; color: #334155; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 14px; font-weight: 600;"
        )

        header.addLayout(title_box, stretch=1)
        header.addWidget(self.settings_btn)
        return header

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if QWebEngineView is not None:
            self.dashboard_view = QWebEngineView()
            self.dashboard_view.setZoomFactor(0.99)
            self._load_local_dashboard()
            layout.addWidget(self.dashboard_view, stretch=1)
            return page

        fallback = QLabel(
            "QWebEngineView n'est pas disponible.\n"
            "Installe PySide6-WebEngine pour afficher le dashboard dans l'application."
        )
        fallback.setWordWrap(True)
        fallback.setStyleSheet(
            "background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 22px; color: #334155;"
        )
        layout.addWidget(fallback)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("Settings / System Status")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0f172a;")

        hint = QLabel(
            "Cette page sert seulement au diagnostic. Le retour au projet se fait avec le bouton ci-dessous."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748b;")

        self.backend_state_label = QLabel("Backend: en attente")
        self.port_state_label = QLabel("Ports: API 8000 / MQTT 1883")
        self.dependency_status_label = QLabel("Dépendances: en attente")

        for label in [
            self.backend_state_label,
            self.port_state_label,
            self.dependency_status_label,
        ]:
            label.setStyleSheet(
                "background: white; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px 14px; color: #334155;"
            )

        actions = QHBoxLayout()
        actions.setSpacing(10)

        for label, callback in [
            ("Retour au projet", lambda: self._show_page("dashboard")),
            ("Restart backend", self.restart_backend),
            ("Recheck dependencies", self.refresh_report),
        ]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            button.setStyleSheet(
                "background: #ffffff; border: 1px solid #dbe2ff; border-radius: 12px; padding: 11px 14px; font-weight: 700;"
            )
            actions.addWidget(button)

        report_title = QLabel("Dependency check")
        report_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #0f172a;")

        self.report_view = QPlainTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setFont(QFont("Consolas", 10))
        self.report_view.setStyleSheet(
            "background: white; border: 1px solid #e2e8f0; border-radius: 18px; padding: 10px; color: #0f172a;"
        )

        logs_title = QLabel("Logs techniques")
        logs_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #0f172a;")

        self.logs_view = QPlainTextEdit()
        self.logs_view.setReadOnly(True)
        self.logs_view.setFont(QFont("Consolas", 10))
        self.logs_view.setStyleSheet(
            """
            QPlainTextEdit {
                background: #020617;
                color: #bbf7d0;
                border: 1px solid rgba(34, 197, 94, 0.18);
                border-radius: 18px;
                padding: 12px;
            }
            """
        )

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.backend_state_label)
        layout.addWidget(self.port_state_label)
        layout.addWidget(self.dependency_status_label)
        layout.addLayout(actions)
        layout.addWidget(report_title)
        layout.addWidget(self.report_view, stretch=1)
        layout.addWidget(logs_title)
        layout.addWidget(self.logs_view, stretch=1)
        return page

    def _show_page(self, page: str) -> None:
        if page == "settings":
            self.pages.setCurrentIndex(1)
            self.page_title.setText("Settings")
            self.page_subtitle.setText(
                "Diagnostic système, dépendances, ports et état backend"
            )
            self.alert_bar.hide()
            self.settings_btn.hide()
        else:
            self.pages.setCurrentIndex(0)
            self.page_title.setText("MQTT Control Launcher")
            self.page_subtitle.setText(
                "Le dashboard du projet reste la navigation principale."
            )
            self.settings_btn.show()
            if self.alert_label.text():
                self.alert_bar.show()

    def _auto_boot(self) -> None:
        if self.boot_started:
            return

        self.boot_started = True
        self.log("Initialisation automatique du launcher.")
        self.refresh_report()
        self.launch_project()
        self.open_dashboard()

    def log(self, message: str) -> None:
        for view in [self.logs_view, self.report_view]:
            current = view.toPlainText().strip()
            next_text = f"{current}\n{message}".strip() if current else message
            view.setPlainText(next_text)
            view.verticalScrollBar().setValue(view.verticalScrollBar().maximum())

    def refresh_report(self) -> None:
        report = self.checker()
        self.report_view.setPlainText("\n".join(report.summary_lines()))

        if report.ok:
            self.dependency_status_label.setText("Dépendances: tout est prêt")
            self._hide_alert()
        else:
            missing_count = len(report.missing_items)
            self.dependency_status_label.setText(
                f"Dépendances: {missing_count} élément(s) manquant(s)"
            )
            self._show_alert(f"Alerte: {missing_count} dépendance(s) manquante(s).")

        self._update_runtime_status(report.ok)

    def launch_project(self) -> None:
        report = self.checker()
        blocking_missing = [
            item
            for item in report.missing_items
            if item.category in {"Runtime", "Python modules"}
        ]
        if blocking_missing:
            self.log(
                "Le backend ne peut pas démarrer: dépendances Python/runtime manquantes. Ouvre Settings pour voir le détail."
            )
            self._update_runtime_status(report.ok)
            return

        self.log("Nettoyage des anciennes instances éventuelles...")
        self._cleanup_old_backend()

        if (
            self.backend_process is not None
            and self.backend_process.state() != QProcess.NotRunning
        ):
            self.log("Backend déjà démarré.")
            self._update_runtime_status(self._is_backend_reachable())
            return

        self.log("Démarrage du backend FastAPI.")
        python_executable = self._resolve_python_executable()
        self.backend_process = QProcess(self)
        self.backend_process.setWorkingDirectory(str(self.project_root))
        self.backend_process.setProgram(python_executable)
        self.backend_process.setArguments(["-m", "uvicorn", "app.main:app", "--reload"])
        self.backend_process.readyReadStandardOutput.connect(self._read_backend_output)
        self.backend_process.readyReadStandardError.connect(self._read_backend_error)
        self.backend_process.finished.connect(self._handle_backend_exit)
        self.backend_process.start()

        QTimer.singleShot(1800, self._poll_backend_ready)

    def restart_backend(self) -> None:
        self.log("Redémarrage du backend demandé.")
        self._stop_backend("Arrêt du backend avant redémarrage.")
        self._update_runtime_status(False)
        self.launch_project()

    def open_dashboard(self) -> None:
        if QWebEngineView is None:
            import webbrowser

            dashboard_file = self.project_root / "mqtt-dashboard" / "index.html"
            webbrowser.open(dashboard_file.as_uri())
            self.log("Dashboard local ouvert dans le navigateur.")
            return

        self._load_local_dashboard()
        self._show_page("dashboard")
        self.log("Dashboard affiché dans le launcher.")

    def _load_local_dashboard(self) -> None:
        if self.dashboard_view is None:
            return

        dashboard_file = self.project_root / "mqtt-dashboard" / "index.html"
        self.dashboard_view.setUrl(QUrl.fromLocalFile(str(dashboard_file)))

    def _poll_backend_ready(self) -> None:
        reachable = self._is_backend_reachable()
        self._update_runtime_status(reachable)
        if reachable:
            self.log("Backend joignable sur http://127.0.0.1:8000.")
        else:
            self.log("Backend non joignable pour l'instant.")

    def _handle_backend_exit(self) -> None:
        self.log("Le backend FastAPI s'est arrêté.")
        self._update_runtime_status(False)

    def _read_backend_output(self) -> None:
        if not self.backend_process:
            return

        text = (
            bytes(self.backend_process.readAllStandardOutput())
            .decode("utf-8", errors="ignore")
            .strip()
        )
        if text:
            self.log(text)
            if "Application startup complete" in text or "Uvicorn running on" in text:
                self._poll_backend_ready()

    def _read_backend_error(self) -> None:
        if not self.backend_process:
            return

        text = (
            bytes(self.backend_process.readAllStandardError())
            .decode("utf-8", errors="ignore")
            .strip()
        )
        if text:
            self.log(text)

    def _update_runtime_status(self, dependencies_ok: bool) -> None:
        backend_ok = self._is_backend_reachable()
        api_open = self._is_port_open(8000)
        mqtt_open = self._is_port_open(1883)

        self.backend_state_label.setText(
            f"Backend status: {'actif' if backend_ok else 'arrêté'}"
        )
        self.port_state_label.setText(
            f"Ports: API 8000 {'ouvert' if api_open else 'fermé'} | MQTT 1883 {'ouvert' if mqtt_open else 'fermé'}"
        )

        if self.pages.currentIndex() == 0:
            if backend_ok:
                self.page_subtitle.setText(
                    "Le dashboard du projet reste la navigation principale."
                )
            elif not dependencies_ok:
                self.page_subtitle.setText(
                    "Des dépendances manquent. Le dashboard reste utilisable."
                )
            else:
                self.page_subtitle.setText("Backend en cours de démarrage")

    def _show_alert(self, message: str) -> None:
        self.alert_label.setText(message)
        if self.pages.currentIndex() == 0:
            self.alert_bar.show()

    def _hide_alert(self) -> None:
        self.alert_bar.hide()

    def _is_port_open(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            return sock.connect_ex(("127.0.0.1", port)) == 0

    def _is_backend_reachable(self) -> bool:
        try:
            # We check /api/debug/backend which returns a unique identity string
            # to avoid being fooled by another service on port 8000.
            with urlopen(
                "http://127.0.0.1:8000/api/debug/backend", timeout=1.0
            ) as response:
                if response.status != 200:
                    return False
                data = json.loads(response.read().decode("utf-8"))
                return data.get("backend") == "mqtt-control-api"
        except Exception:
            return False

    def _cleanup_old_backend(self) -> None:
        """Find and kill any process listening on port 8000 if it's our backend."""
        # Note: We only do this if it's actually our backend to avoid killing random apps.
        if not self._is_backend_reachable():
            return

        self.log("Ancienne instance détectée sur le port 8000. Fermeture active...")
        try:
            # 1. Find the PID using netstat
            output = (
                subprocess.check_output(["netstat", "-ano"], text=True)
                .strip()
                .splitlines()
            )
            pid = None
            for line in output:
                if ":8000" in line and "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        break

            if pid:
                self.log(f"Killing process tree for PID {pid}...")
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", pid],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                # Give it a moment to release the port
                time.sleep(0.5)
        except Exception as e:
            self.log(f"Erreur lors du nettoyage : {e}")

    def _get_runtime_status(self) -> dict[str, object]:
        if not self._is_backend_reachable():
            return {"managed_services": []}

        try:
            with urlopen(
                "http://127.0.0.1:8000/api/system/runtime-status", timeout=0.8
            ) as response:
                payload = response.read().decode("utf-8")
            return json.loads(payload)
        except Exception:
            return {"managed_services": []}

    def _shutdown_managed_services(self) -> None:
        if not self._is_backend_reachable():
            return

        try:
            request = Request(
                "http://127.0.0.1:8000/api/system/shutdown-managed",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=1.2):
                pass
        except Exception:
            # We still continue with the local backend shutdown fallback.
            pass

    def _build_shutdown_message(self) -> str:
        runtime_status = self._get_runtime_status()
        managed_services = runtime_status.get("managed_services", [])
        running_services = [
            service for service in managed_services if service.get("running")
        ]

        if not running_services:
            return (
                "Fermer MQTT Control Launcher ?\n\n"
                "Le backend de l'application sera arrêté."
            )

        lines = [
            "Fermer MQTT Control Launcher ?",
            "",
            "Les services suivants seront arrêtés :",
        ]

        for service in running_services:
            name = str(service.get("name", "Service"))
            pid = str(service.get("pid", "")).strip()
            if pid:
                lines.append(f"- {name} (PID {pid})")
            else:
                lines.append(f"- {name}")

        lines.extend(
            [
                "",
                "Cliquez sur OK pour arrêter ces services, ou Annuler pour revenir à l'application.",
            ]
        )
        return "\n".join(lines)

    def _stop_backend(self, message: str | None = None) -> None:
        if (
            self.backend_process is None
            or self.backend_process.state() == QProcess.NotRunning
        ):
            return

        if message:
            self.log(message)

        pid = int(self.backend_process.processId())
        self.backend_process.terminate()
        if not self.backend_process.waitForFinished(3000):
            self.backend_process.kill()
            self.backend_process.waitForFinished(2000)

        if pid:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            except Exception:
                pass

        self.backend_process = None
        self._update_runtime_status(False)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        message = self._build_shutdown_message()
        answer = QMessageBox.question(
            self,
            "Confirmer la fermeture",
            message,
            QMessageBox.Ok | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if answer != QMessageBox.Ok:
            event.ignore()
            return

        self._shutdown_managed_services()
        self._stop_backend("Fermeture du launcher: arrêt du backend.")
        super().closeEvent(event)
