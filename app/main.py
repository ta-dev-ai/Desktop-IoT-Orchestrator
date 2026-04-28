from __future__ import annotations

import os
import shutil
import subprocess
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from launcher.checker import build_dependency_report


ROOT_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = ROOT_DIR / "mqtt-dashboard"
DASHBOARD_FILE = DASHBOARD_DIR / "index.html"
STYLE_FILE = DASHBOARD_DIR / "style.css"
SCRIPT_FILE = DASHBOARD_DIR / "script.js"

DEFAULT_TOPIC = os.getenv("MQTT_TOPIC", "temperature")
DEFAULT_MESSAGE = os.getenv("MQTT_MESSAGE", "25°C")

LOGS: Deque[dict[str, str]] = deque(maxlen=50)
BROKER_PROCESS: subprocess.Popen | None = None
SUBSCRIBER_PROCESS: subprocess.Popen | None = None

app = FastAPI(title="Smart Controle Mosquitto", version="0.1.0")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(level: Literal["info", "error"], message: str) -> None:
    LOGS.appendleft({"timestamp": _timestamp(), "level": level, "message": message})


def _resolve_command(env_name: str, fallback: str) -> str:
    command = os.getenv(env_name, fallback)
    if shutil.which(command) is None:
        raise HTTPException(
            status_code=500,
            detail=f"Commande introuvable: {command}. Installe Mosquitto ou renseigne {env_name}.",
        )
    return command


def _spawn_process(command: list[str], label: str) -> subprocess.Popen:
    try:
        return subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Echec au lancement de {label}.") from exc


def _start_process(command: list[str], label: str) -> dict[str, str]:
    process = _spawn_process(command, label)
    _log("info", f"{label} lancé: {process.pid}")
    return {"message": f"{label} lancé", "pid": str(process.pid), "command": " ".join(command)}


@app.get("/")
def home() -> FileResponse:
    if not DASHBOARD_FILE.exists():
        raise HTTPException(status_code=500, detail="Dashboard introuvable.")
    return FileResponse(DASHBOARD_FILE)


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return home()


@app.get("/style.css")
def dashboard_style() -> FileResponse:
    if not STYLE_FILE.exists():
        raise HTTPException(status_code=500, detail="Fichier CSS introuvable.")
    return FileResponse(STYLE_FILE, media_type="text/css")


@app.get("/script.js")
def dashboard_script() -> FileResponse:
    if not SCRIPT_FILE.exists():
        raise HTTPException(status_code=500, detail="Fichier JavaScript introuvable.")
    return FileResponse(SCRIPT_FILE, media_type="application/javascript")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/logs")
def logs() -> dict[str, list[dict[str, str]]]:
    return {"logs": list(LOGS)}


@app.get("/api/system/status")
def system_status() -> dict[str, object]:
    report = build_dependency_report()
    return {
        "ok": report.ok,
        "missing_count": len(report.missing_items),
        "items": [
            {
                "category": item.category,
                "name": item.name,
                "ok": item.ok,
                "status": item.status,
                "detail": item.detail,
            }
            for item in report.items
        ],
        "summary": report.summary_lines(),
    }


@app.post("/api/commands/start-broker")
def start_broker() -> dict[str, str]:
    global BROKER_PROCESS

    if BROKER_PROCESS and BROKER_PROCESS.poll() is None:
        return {"message": "Mosquitto broker déjà démarré", "pid": str(BROKER_PROCESS.pid)}

    mosquitto = _resolve_command("MOSQUITTO_BIN", "mosquitto")
    command = [mosquitto, "-v"]
    BROKER_PROCESS = _spawn_process(command, "Mosquitto broker")
    _log("info", f"Mosquitto broker lancé: {BROKER_PROCESS.pid}")
    return {
        "message": "Mosquitto broker lancé",
        "pid": str(BROKER_PROCESS.pid),
        "command": " ".join(command),
    }


@app.post("/api/commands/stop-broker")
def stop_broker() -> dict[str, str]:
    global BROKER_PROCESS

    if not BROKER_PROCESS or BROKER_PROCESS.poll() is not None:
        _log("info", "Demande d'arrêt broker: aucun processus suivi.")
        return {"message": "Aucun broker démarré depuis ce launcher"}

    pid = BROKER_PROCESS.pid
    BROKER_PROCESS.terminate()
    BROKER_PROCESS = None
    _log("info", f"Mosquitto broker arrêté: {pid}")
    return {"message": "Mosquitto broker arrêté", "pid": str(pid)}


@app.post("/api/commands/start-subscriber")
def subscribe() -> dict[str, str]:
    global SUBSCRIBER_PROCESS

    if SUBSCRIBER_PROCESS and SUBSCRIBER_PROCESS.poll() is None:
        return {"message": "MQTT subscriber déjà démarré", "pid": str(SUBSCRIBER_PROCESS.pid)}

    mosquitto_sub = _resolve_command("MOSQUITTO_SUB_BIN", "mosquitto_sub")
    command = [mosquitto_sub, "-h", "localhost", "-t", DEFAULT_TOPIC]
    SUBSCRIBER_PROCESS = _spawn_process(command, "MQTT subscriber")
    _log("info", f"MQTT subscriber lancé: {SUBSCRIBER_PROCESS.pid}")
    return {
        "message": "MQTT subscriber lancé",
        "pid": str(SUBSCRIBER_PROCESS.pid),
        "command": " ".join(command),
    }


@app.post("/api/commands/publish-temperature")
def publish() -> dict[str, str]:
    mosquitto_pub = _resolve_command("MOSQUITTO_PUB_BIN", "mosquitto_pub")
    command = [
        mosquitto_pub,
        "-h",
        "localhost",
        "-t",
        DEFAULT_TOPIC,
        "-m",
        DEFAULT_MESSAGE,
    ]
    return _start_process(command, "MQTT publisher")


@app.post("/api/commands/restart-broker")
def restart_broker() -> dict[str, str]:
    stop_broker()
    return start_broker()


@app.post("/api/commands/open-terminal")
def open_terminal() -> dict[str, str]:
    _log("info", "Ouverture terminal demandée depuis le dashboard.")
    return {
        "message": "Demande terminal reçue",
        "note": "Dans la version desktop, PySide6 pourra ouvrir une console système.",
    }


@app.post("/start-broker")
def legacy_start_broker() -> dict[str, str]:
    return start_broker()


@app.post("/subscribe")
def legacy_subscribe() -> dict[str, str]:
    return subscribe()


@app.post("/publish")
def legacy_publish() -> dict[str, str]:
    return publish()
