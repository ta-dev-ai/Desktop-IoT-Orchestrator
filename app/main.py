"""FastAPI entry point for MQTT Control.

This file intentionally stays small. Business logic lives in services and HTTP
endpoints live in route modules.
"""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import command_routes, device_routes, frontend_routes, system_routes


app = FastAPI(title="MQTT Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(command_routes.router)
app.include_router(system_routes.router)
app.include_router(device_routes.router)
app.include_router(frontend_routes.router)


def main() -> None:
    print("Backend FastAPI demarre.")
    print("Dashboard: http://127.0.0.1:8000/")
    print("Application desktop: python main.py")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
