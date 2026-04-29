"""Dependency discovery helpers."""

from __future__ import annotations

import importlib
import os
import shutil
from pathlib import Path


MOSQUITTO_PATHS = [
    Path(r"C:\Program Files\mosquitto"),
    Path(r"C:\Program Files (x86)\mosquitto"),
]

COMMAND_ENV_VARS = {
    "mosquitto": "MOSQUITTO_BIN",
    "mosquitto_sub": "MOSQUITTO_SUB_BIN",
    "mosquitto_pub": "MOSQUITTO_PUB_BIN",
}


def resolve_command(command: str) -> str | None:
    env_name = COMMAND_ENV_VARS.get(command)
    if env_name:
        configured = os.environ.get(env_name)
        if configured and Path(configured).exists():
            return configured

    found = shutil.which(command)
    if found:
        return found

    executable = command if command.lower().endswith(".exe") else f"{command}.exe"
    for folder in MOSQUITTO_PATHS:
        candidate = folder / executable
        if candidate.exists():
            return str(candidate)

    return None


def has_python_module(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def build_system_status() -> dict:
    checks = [
        {
            "name": "Python module PySide6",
            "ok": has_python_module("PySide6"),
            "hint": "install PySide6",
            "path": "",
        },
        {
            "name": "Python module FastAPI",
            "ok": has_python_module("fastapi"),
            "hint": "install fastapi",
            "path": "",
        },
        {
            "name": "Python module Uvicorn",
            "ok": has_python_module("uvicorn"),
            "hint": "install uvicorn",
            "path": "",
        },
        {
            "name": "Mosquitto broker",
            "ok": bool(resolve_command("mosquitto")),
            "hint": "install Mosquitto or add it to PATH",
            "path": resolve_command("mosquitto") or "",
        },
        {
            "name": "Mosquitto subscriber",
            "ok": bool(resolve_command("mosquitto_sub")),
            "hint": "install Mosquitto CLI tools",
            "path": resolve_command("mosquitto_sub") or "",
        },
        {
            "name": "Mosquitto publisher",
            "ok": bool(resolve_command("mosquitto_pub")),
            "hint": "install Mosquitto CLI tools",
            "path": resolve_command("mosquitto_pub") or "",
        },
    ]

    items = [
        {
            "name": check["name"],
            "ok": check["ok"],
            "status": "OK" if check["ok"] else "MISSING",
            "hint": check["hint"],
            "path": check["path"],
        }
        for check in checks
    ]
    missing = [item for item in items if not item["ok"]]
    summary_lines = ["Dependency check", "================", ""]
    for item in items:
        status = "OK" if item["ok"] else "MISSING"
        suffix = item["path"] or item["hint"]
        summary_lines.append(f"[{status:<7}] {item['name']:<24} {suffix}")
    if missing:
        summary_lines.extend(["", "Missing dependencies:"])
        summary_lines.extend([f"- {item['name']}: {item['hint']}" for item in missing])
    else:
        summary_lines.extend(["", "All required dependencies are available."])

    return {
        "ok": not missing,
        "missing_count": len(missing),
        "items": items,
        "summary": "\n".join(summary_lines),
    }
