"""MQTT device registry API routes."""

from fastapi import APIRouter, HTTPException

from app.models.devices import DeviceCreatePayload
from app.services import device_service


router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
def list_devices():
    items = device_service.load_devices()
    return {"ok": True, "count": len(items), "items": items}


@router.post("")
def create_device(payload: DeviceCreatePayload):
    item = device_service.create_device(payload)
    return {
        "ok": True,
        "message": "Appareil ajouté.",
        "item": item,
        "mqtt_config": device_service.mqtt_config(item),
    }


@router.delete("/{device_id}")
def delete_device(device_id: str):
    deleted = device_service.delete_device(device_id)
    return {
        "ok": deleted,
        "message": "Appareil supprimé." if deleted else "Appareil introuvable.",
    }


@router.get("/{device_id}/mqtt-config")
def get_mqtt_config(device_id: str):
    item = device_service.get_device(device_id)
    if not item:
        raise HTTPException(status_code=404, detail="Appareil introuvable.")
    return {"ok": True, "item": item, "mqtt_config": device_service.mqtt_config(item)}


@router.get("/{device_id}/status")
def get_status(device_id: str):
    item = device_service.get_device(device_id)
    if not item:
        raise HTTPException(status_code=404, detail="Appareil introuvable.")
    config = device_service.mqtt_config(item)
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
