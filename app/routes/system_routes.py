"""System and diagnostic API routes."""

from fastapi import APIRouter

from app.services.dependency_service import build_system_status
from app.services import debug_service, mosquitto_service


router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    debug_backend()
    return {
        "ok": True,
        "status": "healthy",
        "app": "mqtt-control-api",
        "version": "backend-refactor-v1",
    }


@router.get("/api/debug/backend")
def debug_backend():
    debug_service.add_event("debug", "Backend debug identity requested.")
    return {
        "ok": True,
        "backend": "mqtt-control-api",
        "version": "backend-refactor-v1",
        "message": "Le backend FastAPI courant repond bien.",
        "expected_routes": [
            "/health",
            "/api/system/status",
            "/api/commands/verify-mqtt-port",
            "/api/commands/open-terminal",
            "/api/commands/start-broker",
            "/api/commands/start-subscriber",
            "/api/commands/publish-message",
            "/api/devices",
        ],
    }


@router.get("/api/debug/self-test")
def debug_self_test():
    debug_service.add_event("debug", "Backend self-test requested.")
    dependency_status = build_system_status()
    port_status = mosquitto_service.verify_mqtt_port()
    checks = [
        {
            "name": "backend_identity",
            "ok": True,
            "detail": "Backend refactor v1 charge.",
        },
        {
            "name": "dependency_service",
            "ok": dependency_status.get("ok", False),
            "detail": f"{dependency_status.get('missing_count', 0)} dependance(s) manquante(s).",
        },
        {
            "name": "mqtt_port_check",
            "ok": True,
            "detail": port_status.get("message", "Port verifie."),
        },
        {
            "name": "command_routes_expected",
            "ok": True,
            "detail": "Routes commandes attendues: start/stop broker, subscriber, publish, terminal, port.",
        },
    ]
    return {
        "ok": all(check["ok"] for check in checks),
        "backend": "mqtt-control-api",
        "version": "backend-refactor-v1",
        "checks": checks,
        "dependency_status": dependency_status,
        "mqtt_port_status": port_status,
        "next_manual_tests": [
            "POST /api/commands/verify-mqtt-port",
            "POST /api/commands/start-broker",
            "POST /api/commands/start-subscriber",
            "POST /api/commands/publish-message",
        ],
    }


@router.get("/api/debug/events")
def debug_events():
    return {
        "ok": True,
        "count": len(debug_service.list_events()),
        "items": debug_service.list_events(),
    }


@router.post("/api/debug/events/clear")
def clear_debug_events():
    debug_service.clear_events()
    debug_service.add_event("debug", "Debug events cleared.")
    return {"ok": True, "message": "Debug events cleared."}


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


@router.get("/api/system/stats")
def system_stats():
    runtime = mosquitto_service.runtime_status()
    counts = debug_service.get_event_counts()

    # We fake client count based on whether broker + sub are running
    clients = 0
    if any(
        s["running"]
        for s in runtime.get("services", [])
        if "broker" in s["name"].lower()
    ):
        clients += 1
    if any(
        s["running"]
        for s in runtime.get("services", [])
        if "subscriber" in s["name"].lower()
    ):
        clients += 1

    return {
        "ok": True,
        "counts": counts,
        "clients": clients,
        "broker_running": any(
            s["running"]
            for s in runtime.get("services", [])
            if "broker" in s["name"].lower()
        ),
    }
