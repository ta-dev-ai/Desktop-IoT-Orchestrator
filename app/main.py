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


ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_FILE = ROOT_DIR / "frontend" / "index.html"

DEFAULT_TOPIC = os.getenv("MQTT_TOPIC", "temperature")
DEFAULT_MESSAGE = os.getenv("MQTT_MESSAGE", "25°C")

LOGS: Deque[dict[str, str]] = deque(maxlen=50)

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


def _start_process(command: list[str], label: str) -> dict[str, str]:
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Echec au lancement de {label}.") from exc

    _log("info", f"{label} lancé: {process.pid}")
    return {"message": f"{label} lancé", "pid": str(process.pid), "command": " ".join(command)}


@app.get("/")
def home() -> FileResponse:
    if not FRONTEND_FILE.exists():
        raise HTTPException(status_code=500, detail="Frontend introuvable.")
    return FileResponse(FRONTEND_FILE)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/logs")
def logs() -> dict[str, list[dict[str, str]]]:
    return {"logs": list(LOGS)}


@app.post("/start-broker")
def start_broker() -> dict[str, str]:
    mosquitto = _resolve_command("MOSQUITTO_BIN", "mosquitto")
    return _start_process([mosquitto, "-v"], "Mosquitto broker")


@app.post("/subscribe")
def subscribe() -> dict[str, str]:
    mosquitto_sub = _resolve_command("MOSQUITTO_SUB_BIN", "mosquitto_sub")
    return _start_process([mosquitto_sub, "-h", "localhost", "-t", DEFAULT_TOPIC], "MQTT subscriber")


@app.post("/publish")
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


