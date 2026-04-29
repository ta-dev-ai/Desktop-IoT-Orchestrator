"""Shared project paths used by the FastAPI backend."""

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
APP_DIR = ROOT_DIR / "app"
DASHBOARD_DIR = ROOT_DIR / "mqtt-dashboard"
LEGACY_FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "data"
DEVICES_DATA_FILE = DATA_DIR / "devices.json"
