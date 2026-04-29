"""MQTT command API routes.

This file is intentionally thin:
- routes receive HTTP requests
- services contain the real business logic

Keeping this layer small makes it easier to test and avoids putting Mosquitto
process logic directly inside FastAPI endpoint functions.
"""

from fastapi import APIRouter

from app.models.payloads import PublishMessagePayload
from app.services import mosquitto_service


router = APIRouter(prefix="/api/commands", tags=["commands"])
legacy_router = APIRouter(tags=["legacy commands"])


@router.post("/start-broker")
def start_broker():
    """Start the Mosquitto broker process."""
    return mosquitto_service.start_broker()


@router.post("/stop-broker")
def stop_broker():
    """Stop the broker process managed by this backend."""
    return mosquitto_service.stop_broker()


@router.post("/start-subscriber")
def start_subscriber():
    """Start a local subscriber on the default temperature topic."""
    return mosquitto_service.start_subscriber()


@router.post("/stop-subscriber")
def stop_subscriber():
    """Stop the local subscriber managed by this backend."""
    return mosquitto_service.stop_subscriber()


@router.post("/publish-temperature")
def publish_temperature():
    """Publish the default MVP test temperature message."""
    return mosquitto_service.publish_temperature()


@router.post("/publish-message")
def publish_message(payload: PublishMessagePayload):
    """Publish a dynamic message on the topic provided by the UI."""
    return mosquitto_service.publish_message(payload)


@router.post("/restart-broker")
def restart_broker():
    """Restart the managed broker process."""
    return mosquitto_service.restart_broker()


@router.post("/open-terminal")
def open_terminal():
    """Open a Windows terminal in the project directory."""
    return mosquitto_service.open_terminal()


@router.post("/verify-mqtt-port")
def verify_mqtt_port():
    """Check whether the MQTT port is reachable locally."""
    return mosquitto_service.verify_mqtt_port()


@legacy_router.post("/start-broker")
def legacy_start_broker():
    """Legacy route kept for older Swagger/manual tests."""
    return mosquitto_service.start_broker()


@legacy_router.post("/subscribe")
def legacy_subscribe():
    """Legacy route kept for older Swagger/manual tests."""
    return mosquitto_service.start_subscriber()


@legacy_router.post("/publish")
def legacy_publish(payload: dict | None = None):
    """Legacy route kept for older Swagger/manual tests."""
    payload = payload or {}
    message = str(payload.get("message") or payload.get("payload") or "25°C")
    topic = str(payload.get("topic") or "temperature")
    return mosquitto_service.publish_message(
        PublishMessagePayload(topic=topic, message=message)
    )
