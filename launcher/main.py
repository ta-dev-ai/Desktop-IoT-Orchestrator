from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

from launcher.checker import build_dependency_report
from launcher.ui import LauncherWindow


def main() -> int:
    app = QApplication(sys.argv)
    project_root = Path(__file__).resolve().parent.parent
    window = LauncherWindow(project_root, build_dependency_report)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
