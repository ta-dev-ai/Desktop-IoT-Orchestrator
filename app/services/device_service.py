"""Local JSON registry for MQTT devices."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from app.core.paths import DEVICES_DATA_FILE
from app.models.devices import DeviceCreatePayload


def ensure_store() -> None:
    DEVICES_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DEVICES_DATA_FILE.exists():
        DEVICES_DATA_FILE.write_text("[]", encoding="utf-8")


def load_devices() -> list[dict]:
    ensure_store()
    try:
        data = json.loads(DEVICES_DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_devices(devices: list[dict]) -> None:
    ensure_store()
    DEVICES_DATA_FILE.write_text(
        json.dumps(devices, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def create_device(payload: DeviceCreatePayload) -> dict:
    devices = load_devices()
    item = {
        "id": f"device-{uuid.uuid4().hex[:8]}",
        "name": payload.name.strip() or "Appareil MQTT",
        "type": payload.device_type.strip() or "generic",
        "host": payload.host.strip(),
        "role": payload.role.strip() or "subscriber",
        "topics_sub": [value.strip() for value in payload.topics_sub.split(",") if value.strip()],
        "topics_pub": [value.strip() for value in payload.topics_pub.split(",") if value.strip()],
        "notes": payload.notes.strip(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    devices.append(item)
    save_devices(devices)
    return item


def delete_device(device_id: str) -> bool:
    devices = load_devices()
    kept = [item for item in devices if item.get("id") != device_id]
    save_devices(kept)
    return len(kept) != len(devices)


def get_device(device_id: str) -> dict | None:
    for item in load_devices():
        if item.get("id") == device_id:
            return item
    return None


def mqtt_config(device: dict) -> dict:
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
