# Desktop IoT Orchestrator

Desktop IoT Orchestrator is a beginner-friendly desktop control suite for MQTT systems.
It combines a PySide6 launcher, a FastAPI backend, and a modern HTML dashboard to make
MQTT testing and control easy to demonstrate in a portfolio.

## Demo

<img src="public/gif/Enregistrement%202026-04-28%20123440.gif" alt="Desktop IoT Orchestrator demo" />

## What it does

- launches a desktop app from a single `.exe`
- checks Python, PySide6, FastAPI, Uvicorn, and Mosquitto tools at startup
- starts the FastAPI backend automatically
- displays the MQTT dashboard inside the desktop app
- shows logs, broker status, and command results in a clear UI

## Why it looks good for recruiters

- real desktop product feel
- clear separation between launcher, backend, and UI
- useful for IoT, automation, and internal tooling demos
- easy to extend toward WebSocket live updates and packaging

## Current stack

- Python
- PySide6
- FastAPI
- Uvicorn
- HTML
- CSS
- JavaScript vanilla
- MQTT / Mosquitto

## Project structure

```text
smart_controlle_mosquitto/
├── app/
│   └── main.py
├── launcher/
│   ├── main.py
│   ├── checker.py
│   └── ui.py
├── mqtt-dashboard/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── public/
│   └── gif/
│       └── Enregistrement 2026-04-28 123440.gif
├── doc/
│   ├── install.md
│   ├── launcher_plan.md
│   └── venv.md
├── scripts/
│   └── install.ps1
├── source_projet/
├── requirements.txt
├── package.json
└── README.md
```

## Run the web dashboard

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the backend:

```bash
uvicorn app.main:app --reload
```

3. Open the dashboard:

```text
http://127.0.0.1:8000
```

## Run the launcher

When the launcher is ready:

```bash
python launcher/main.py
```

The launcher will:

- verify dependencies
- start the backend
- display the dashboard

## Local setup helpers

- `doc/venv.md` explains how to create and use the Python virtual environment
- `scripts/install.ps1` installs Python dependencies automatically
- `package.json` provides a minimal Node.js project shell for the dashboard script
- `npm run check` validates the dashboard JavaScript syntax with Node.js

## MQTT commands used by the project

- `mosquitto -v`
- `mosquitto_sub -h localhost -t temperature`
- `mosquitto_pub -h localhost -t temperature -m "25°C"`

## Notes

Mosquitto must be installed and available in the `PATH`, or configured through these
environment variables:

- `MOSQUITTO_BIN`
- `MOSQUITTO_SUB_BIN`
- `MOSQUITTO_PUB_BIN`
