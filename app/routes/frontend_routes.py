"""Routes that serve the vanilla dashboard."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.core.paths import DASHBOARD_DIR, LEGACY_FRONTEND_DIR


router = APIRouter()


MEDIA_TYPES = {
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


def resolve_dashboard_file(filename: str):
    for folder in (DASHBOARD_DIR, LEGACY_FRONTEND_DIR):
        candidate = folder / filename
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def file_response(filename: str) -> FileResponse:
    candidate = resolve_dashboard_file(filename)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Asset introuvable: {filename}")
    return FileResponse(candidate, media_type=MEDIA_TYPES.get(candidate.suffix.lower(), "application/octet-stream"))


@router.get("/")
@router.get("/index.html")
@router.get("/dashboard")
@router.get("/dashboard/")
def dashboard():
    return file_response("index.html")


@router.get("/{asset_path:path}")
def dashboard_asset(asset_path: str, request: Request):
    if asset_path.startswith(("api/", "docs", "openapi")) or ".." in asset_path:
        raise HTTPException(status_code=404, detail="Route introuvable.")
    return file_response(asset_path)
