"""System and diagnostic API routes."""

from fastapi import APIRouter

from app.services.dependency_service import build_system_status
from app.services import mosquitto_service


router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {"ok": True, "status": "healthy"}


@router.get("/logs")
def logs():
    return {"ok": True, "items": []}


@router.get("/api/system/status")
def system_status():
    return build_system_status()


@router.get("/api/system/runtime-status")
def runtime_status():
    return mosquitto_service.runtime_status()


@router.post("/api/system/shutdown-managed")
def shutdown_managed():
    return mosquitto_service.shutdown_managed()
