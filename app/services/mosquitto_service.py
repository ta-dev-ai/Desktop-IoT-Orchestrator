"""Mosquitto command orchestration."""

from __future__ import annotations

import socket
import os
import subprocess

from app.core import processes
from app.core.paths import ROOT_DIR
from app.models.payloads import PublishMessagePayload
from app.services.dependency_service import resolve_command


def _missing_response(tool: str) -> dict:
    return {
        "ok": False,
        "message": f"Commande introuvable: {tool}. Installe Mosquitto ou configure le PATH.",
    }


def start_broker() -> dict:
    if processes.is_process_running(processes.broker_process):
        return {"ok": True, "message": "Broker déjà démarré."}

    command = resolve_command("mosquitto")
    if not command:
        return _missing_response("mosquitto")

    processes.broker_process = subprocess.Popen(
        [command, "-v"],
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return {
        "ok": True,
        "message": "Broker MQTT démarré.",
        "pid": processes.broker_process.pid,
    }


def stop_broker() -> dict:
    stopped = processes.stop_process(processes.broker_process)
    processes.broker_process = None
    return {
        "ok": True,
        "message": "Broker MQTT arrêté." if stopped else "Aucun broker suivi à arrêter.",
    }


def start_subscriber(topic: str = "temperature") -> dict:
    if processes.is_process_running(processes.subscriber_process):
        return {"ok": True, "message": "Subscriber déjà démarré."}

    command = resolve_command("mosquitto_sub")
    if not command:
        return _missing_response("mosquitto_sub")

    processes.subscriber_process = subprocess.Popen(
        [command, "-h", "localhost", "-t", topic],
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return {
        "ok": True,
        "message": f"Subscriber démarré sur le topic {topic}.",
        "pid": processes.subscriber_process.pid,
    }


def stop_subscriber() -> dict:
    stopped = processes.stop_process(processes.subscriber_process)
    processes.subscriber_process = None
    return {
        "ok": True,
        "message": "Subscriber arrêté." if stopped else "Aucun subscriber suivi à arrêter.",
    }


def publish_message(payload: PublishMessagePayload) -> dict:
    command = resolve_command("mosquitto_pub")
    if not command:
        return _missing_response("mosquitto_pub")

    completed = subprocess.run(
        [command, "-h", "localhost", "-t", payload.topic, "-m", payload.message],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        return {
            "ok": False,
            "message": completed.stderr.strip() or completed.stdout.strip() or "Publication échouée.",
        }

    return {
        "ok": True,
        "message": "Message MQTT publié.",
        "topic": payload.topic,
        "payload": payload.message,
    }


def publish_temperature() -> dict:
    return publish_message(PublishMessagePayload(topic="temperature", message="25°C"))


def restart_broker() -> dict:
    stop_broker()
    return start_broker()


def verify_mqtt_port(host: str = "127.0.0.1", port: int = 1883) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        opened = sock.connect_ex((host, port)) == 0
    return {
        "ok": True,
        "open": opened,
        "message": f"Port MQTT {port} {'ouvert' if opened else 'fermé'}.",
    }


def open_terminal() -> dict:
    if os.name == "nt":
        subprocess.Popen(["cmd.exe", "/k", "cd", "/d", str(ROOT_DIR)])
        return {"ok": True, "message": "Terminal CMD ouvert."}
    return {"ok": False, "message": "Ouverture terminal non implémentée pour cet OS."}


def runtime_status() -> dict:
    services = [
        {"name": "MQTT broker", "running": processes.is_process_running(processes.broker_process)},
        {"name": "MQTT subscriber", "running": processes.is_process_running(processes.subscriber_process)},
    ]
    return {"ok": True, "services": services}


def shutdown_managed() -> dict:
    stopped = []
    if processes.is_process_running(processes.subscriber_process):
        stop_subscriber()
        stopped.append("MQTT subscriber")
    if processes.is_process_running(processes.broker_process):
        stop_broker()
        stopped.append("MQTT broker")
    return {"ok": True, "stopped": stopped}
