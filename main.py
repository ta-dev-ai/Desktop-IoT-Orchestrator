"""Point d'entrée robuste pour l'application desktop.

Usage:
    python main.py

Ce fichier exécute directement le launcher PySide6, sans dépendre d'une
fonction `main()` exportée par `launcher.ui`.
"""

from __future__ import annotations

import runpy
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
LAUNCHER_ENTRY = ROOT_DIR / "launcher" / "ui.py"


if __name__ == "__main__":
    if not LAUNCHER_ENTRY.exists():
        raise FileNotFoundError(
            f"Launcher introuvable: {LAUNCHER_ENTRY}"
        )

    runpy.run_path(str(LAUNCHER_ENTRY), run_name="__main__")
