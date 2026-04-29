from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Literal

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(level: Literal["info", "error"], message: str) -> None:
    LOGS.appendleft({"timestamp": _timestamp(), "level": level, "message": message})


def _resolve_command(env_name: str, fallback: str) -> str:
    command = os.getenv(env_name, fallback)
    resolved_path = _find_command_path(command)
    if resolved_path is None:
        raise HTTPException(
            status_code=500,
            detail=f"Commande introuvable: {command}. Installe Mosquitto ou renseigne {env_name}.",
        )
    return resolved_path


def _find_command_path(command: str) -> str | None:
    direct = shutil.which(command)
    if direct:
        return direct

    if os.name == "nt":
        candidates = [
            Path("C:/Program Files/mosquitto") / f"{command}.exe",
            Path("C:/Program Files (x86)/mosquitto") / f"{command}.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

    return None


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


class PublishMessagePayload(BaseModel):
    topic: str
    message: str


def _publish_message(topic: str, message: str) -> dict[str, str]:
    clean_topic = topic.strip()
    clean_message = message.strip()

    if not clean_topic:
        raise HTTPException(status_code=400, detail="Le topic est obligatoire.")

    if not clean_message:
        raise HTTPException(status_code=400, detail="Le message est obligatoire.")

    mosquitto_pub = _resolve_command("MOSQUITTO_PUB_BIN", "mosquitto_pub")
    command = [
        mosquitto_pub,
        "-h",
        "localhost",
        "-t",
        clean_topic,
        "-m",
        clean_message,
    ]
    response = _start_process(command, "MQTT publisher")
    response["topic"] = clean_topic
    response["payload"] = clean_message
    _log("info", f"Message publié sur {clean_topic}: {clean_message}")
    return response


def _is_local_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.35)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _open_terminal_window() -> dict[str, str]:
    if os.name != "nt":
        raise HTTPException(status_code=501, detail="Ouverture terminal supportée seulement sur Windows pour le moment.")

    creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    try:
        process = subprocess.Popen(
            ["cmd.exe", "/k", f"cd /d {ROOT_DIR}"],
            creationflags=creation_flags,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="Impossible d'ouvrir le terminal Windows.") from exc

    _log("info", f"Terminal Windows ouvert: {process.pid}")
    return {
        "message": "Terminal Windows ouvert",
        "pid": str(process.pid),
        "command": f'cmd.exe /k "cd /d {ROOT_DIR}"',
    }


def _process_is_running(process: subprocess.Popen | None) -> bool:
    return process is not None and process.poll() is None


def _stop_tracked_process(process: subprocess.Popen | None, label: str) -> tuple[subprocess.Popen | None, dict[str, str] | None]:
    if not _process_is_running(process):
        return None, None

    pid = process.pid
    process.terminate()
    _log("info", f"{label} arrêté: {pid}")
    return None, {"message": f"{label} arrêté", "pid": str(pid)}


@app.get("/")
def home() -> FileResponse:
    if not DASHBOARD_FILE.exists():
        raise HTTPException(status_code=500, detail="Dashboard introuvable.")
    return FileResponse(DASHBOARD_FILE)


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return home()


@app.get("/dashboard/")
def dashboard_with_slash() -> FileResponse:
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


@app.get("/api/system/runtime-status")
def runtime_status() -> dict[str, object]:
    broker_running = _process_is_running(BROKER_PROCESS)
    subscriber_running = _process_is_running(SUBSCRIBER_PROCESS)

    return {
        "backend": {"running": True},
        "managed_services": [
            {
                "name": "FastAPI backend",
                "running": True,
            },
            {
                "name": "MQTT broker",
                "running": broker_running,
                "pid": str(BROKER_PROCESS.pid) if broker_running and BROKER_PROCESS else "",
            },
            {
                "name": "MQTT subscriber",
                "running": subscriber_running,
                "pid": str(SUBSCRIBER_PROCESS.pid) if subscriber_running and SUBSCRIBER_PROCESS else "",
            },
        ],
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

    if not _process_is_running(BROKER_PROCESS):
        _log("info", "Demande d'arrêt broker: aucun processus suivi.")
        return {"message": "Aucun broker démarré depuis ce launcher"}

    BROKER_PROCESS, response = _stop_tracked_process(BROKER_PROCESS, "Mosquitto broker")
    return response or {"message": "Aucun broker démarré depuis ce launcher"}


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


@app.post("/api/commands/stop-subscriber")
def stop_subscriber() -> dict[str, str]:
    global SUBSCRIBER_PROCESS

    if not _process_is_running(SUBSCRIBER_PROCESS):
        _log("info", "Demande d'arrêt subscriber: aucun processus suivi.")
        return {"message": "Aucun subscriber démarré depuis ce launcher"}

    SUBSCRIBER_PROCESS, response = _stop_tracked_process(SUBSCRIBER_PROCESS, "MQTT subscriber")
    return response or {"message": "Aucun subscriber démarré depuis ce launcher"}


@app.post("/api/commands/publish-temperature")
def publish() -> dict[str, str]:
    return _publish_message(DEFAULT_TOPIC, DEFAULT_MESSAGE)


@app.post("/api/commands/publish-message")
def publish_message(payload: PublishMessagePayload) -> dict[str, str]:
    return _publish_message(payload.topic, payload.message)


@app.post("/api/commands/restart-broker")
def restart_broker() -> dict[str, str]:
    stop_broker()
    return start_broker()


@app.post("/api/commands/open-terminal")
def open_terminal() -> dict[str, str]:
    return _open_terminal_window()


@app.post("/api/commands/verify-mqtt-port")
def verify_mqtt_port() -> dict[str, str]:
    port = 1883
    port_open = _is_local_port_open(port)
    status = "ouvert" if port_open else "fermé"
    _log("info", f"Vérification du port MQTT {port}: {status}")
    return {
        "message": f"Port MQTT {port} {status}",
        "port": str(port),
        "status": status,
        "port_open": "true" if port_open else "false",
    }


@app.post("/api/system/shutdown-managed")
def shutdown_managed() -> dict[str, object]:
    global BROKER_PROCESS, SUBSCRIBER_PROCESS

    stopped_services: list[dict[str, str]] = []

    SUBSCRIBER_PROCESS, subscriber_response = _stop_tracked_process(SUBSCRIBER_PROCESS, "MQTT subscriber")
    if subscriber_response:
        stopped_services.append(subscriber_response)

    BROKER_PROCESS, broker_response = _stop_tracked_process(BROKER_PROCESS, "Mosquitto broker")
    if broker_response:
        stopped_services.append(broker_response)

    _log("info", f"Extinction des services gérés: {len(stopped_services)} service(s) arrêté(s).")
    return {
        "message": "Extinction des services gérés terminée",
        "stopped_services": stopped_services,
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


@app.get("/button-fallback.js")
def dashboard_button_fallback_script():
    return FileResponse(
        DASHBOARD_DIR / "button-fallback.js",
        media_type="application/javascript",
    )


@app.get("/launcher-bridge.js")
def dashboard_launcher_bridge_script():
    return FileResponse(
        DASHBOARD_DIR / "launcher-bridge.js",
        media_type="application/javascript",
    )


@app.get("/devices-module.js")
def dashboard_devices_module_script():
    return FileResponse(
        DASHBOARD_DIR / "devices-module.js",
        media_type="application/javascript",
    )


@app.get("/publish-visual-fallback.js")
def dashboard_publish_visual_fallback_script():
    return FileResponse(
        DASHBOARD_DIR / "publish-visual-fallback.js",
        media_type="application/javascript",
    )


@app.get("/command-rescue.js")
def dashboard_command_rescue_script():
    return FileResponse(
        DASHBOARD_DIR / "command-rescue.js",
        media_type="application/javascript",
    )


def _resolve_dashboard_file(filename: str):
    mqtt_candidate = DASHBOARD_DIR / filename
    if mqtt_candidate.exists():
        return mqtt_candidate

    legacy_candidate = ROOT_DIR / "frontend" / filename
    if legacy_candidate.exists():
        return legacy_candidate

    return None


@app.middleware("http")
async def ensure_dashboard_routes(request, call_next):
    from fastapi.responses import JSONResponse

    path = request.url.path
    dashboard_asset_types = {
        "/style.css": "text/css",
        "/script.js": "application/javascript",
        "/launcher-bridge.js": "application/javascript",
        "/button-fallback.js": "application/javascript",
        "/publish-visual-fallback.js": "application/javascript",
        "/devices-module.js": "application/javascript",
    }

    if path in {"/", "/index.html", "/dashboard", "/dashboard/"}:
        dashboard_file = _resolve_dashboard_file("index.html")
        if dashboard_file:
            return FileResponse(dashboard_file, media_type="text/html")
        return JSONResponse({"detail": "Frontend introuvable."}, status_code=404)

    if path in dashboard_asset_types:
        asset_file = _resolve_dashboard_file(path.lstrip("/"))
        if asset_file:
            return FileResponse(asset_file, media_type=dashboard_asset_types[path])
        return JSONResponse({"detail": f"Asset introuvable: {path}"}, status_code=404)

    # Generic fallback for dashboard static assets.
    # This prevents future 404s when a new JS/CSS/image file is added to
    # mqtt-dashboard but not yet explicitly wired in FastAPI routes.
    if not path.startswith("/api/") and not path.startswith("/docs") and not path.startswith("/openapi"):
        safe_name = path.lstrip("/")
        if safe_name and ".." not in safe_name:
            candidate = DASHBOARD_DIR / safe_name
            if candidate.exists() and candidate.is_file():
                suffix = candidate.suffix.lower()
                media_types = {
                    ".js": "application/javascript",
                    ".css": "text/css",
                    ".html": "text/html",
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".svg": "image/svg+xml",
                    ".ico": "image/x-icon",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                    ".json": "application/json",
                }
                return FileResponse(
                    candidate,
                    media_type=media_types.get(suffix, "application/octet-stream"),
                )

    return await call_next(request)


DEVICES_DATA_FILE = ROOT_DIR / "data" / "devices.json"


def _ensure_devices_store():
    import json

    DEVICES_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DEVICES_DATA_FILE.exists():
        DEVICES_DATA_FILE.write_text("[]", encoding="utf-8")

    try:
        data = json.loads(DEVICES_DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return
    except Exception:
        pass

    DEVICES_DATA_FILE.write_text("[]", encoding="utf-8")


def _load_devices():
    import json

    _ensure_devices_store()
    try:
        data = json.loads(DEVICES_DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _save_devices(devices):
    import json

    _ensure_devices_store()
    DEVICES_DATA_FILE.write_text(
        json.dumps(devices, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_device_mqtt_config(device):
    broker_host = "127.0.0.1"
    broker_port = 1883
    topics_sub = device.get("topics_sub") or []
    topics_pub = device.get("topics_pub") or []
    primary_topic = topics_sub[0] if topics_sub else (topics_pub[0] if topics_pub else "temperature")
    return {
        "broker_host": broker_host,
        "broker_port": broker_port,
        "primary_topic": primary_topic,
        "topics_sub": topics_sub,
        "topics_pub": topics_pub,
        "subscribe_example": f"mosquitto_sub -h {broker_host} -p {broker_port} -t {primary_topic}",
        "publish_example": f'mosquitto_pub -h {broker_host} -p {broker_port} -t {primary_topic} -m "test"',
    }


@app.get("/api/devices")
def list_devices():
    devices = _load_devices()
    return {
        "ok": True,
        "count": len(devices),
        "items": devices,
    }


@app.post("/api/devices")
def create_device(
    name: str,
    device_type: str = "generic",
    host: str = "",
    role: str = "subscriber",
    topics_sub: str = "",
    topics_pub: str = "",
    notes: str = "",
):
    import uuid
    from datetime import datetime

    devices = _load_devices()
    item = {
        "id": f"device-{uuid.uuid4().hex[:8]}",
        "name": name.strip() or "Appareil MQTT",
        "type": device_type.strip() or "generic",
        "host": host.strip(),
        "role": role.strip() or "subscriber",
        "topics_sub": [value.strip() for value in topics_sub.split(",") if value.strip()],
        "topics_pub": [value.strip() for value in topics_pub.split(",") if value.strip()],
        "notes": notes.strip(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    devices.append(item)
    _save_devices(devices)
    return {
        "ok": True,
        "message": "Appareil ajouté.",
        "item": item,
        "mqtt_config": _build_device_mqtt_config(item),
    }


@app.delete("/api/devices/{device_id}")
def delete_device(device_id: str):
    devices = _load_devices()
    kept = [item for item in devices if item.get("id") != device_id]
    deleted = len(kept) != len(devices)
    if deleted:
        _save_devices(kept)
    return {
        "ok": deleted,
        "message": "Appareil supprimé." if deleted else "Appareil introuvable.",
        "count": len(kept),
    }


@app.get("/api/devices/{device_id}/mqtt-config")
def get_device_mqtt_config(device_id: str):
    devices = _load_devices()
    for item in devices:
        if item.get("id") == device_id:
            return {
                "ok": True,
                "item": item,
                "mqtt_config": _build_device_mqtt_config(item),
            }
    return {
        "ok": False,
        "message": "Appareil introuvable.",
    }


@app.get("/api/devices/{device_id}/status")
def get_device_status(device_id: str):
    devices = _load_devices()
    for item in devices:
        if item.get("id") == device_id:
            config = _build_device_mqtt_config(item)
            return {
                "ok": True,
                "item": item,
                "status": {
                    "broker_ready": True,
                    "mqtt_port": config["broker_port"],
                    "mqtt_host": config["broker_host"],
                    "last_seen": item.get("created_at"),
                    "state": "configured",
                },
            }
    return {
        "ok": False,
        "message": "Appareil introuvable.",
    }


if __name__ == "__main__":
    print("Backend FastAPI démarré.")
    print("Pour ouvrir la fenêtre desktop, lance : python main.py")
    print("Ou bien : python launcher\\ui.py")
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
