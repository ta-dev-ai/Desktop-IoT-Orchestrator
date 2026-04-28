# Functional Roadmap

## Goal

Build `Desktop IoT Orchestrator` one feature at a time.

Each feature must follow this cycle:

```text
Develop -> Test -> Fix -> Commit -> Next feature
```

This roadmap is the functional validation plan for the project.

## 1. Dependency Check

### Status

Implemented and validated locally.

### Objective

The launcher verifies the local environment before starting the project.

### UI

- button: `Check dependencies`
- status area in the PySide6 launcher

### Checks

- Python
- FastAPI
- Uvicorn
- PySide6
- Mosquitto
- Mosquitto CLI tools
- Node.js

### Expected Result

The launcher displays each dependency as `OK` or `Missing`.

### Validation

- run the launcher
- click `Check dependencies`
- confirm all dependency statuses are visible

## 2. FastAPI Backend Start

### Objective

Start the FastAPI backend from the launcher.

### UI

- button: `Launch backend`
- backend logs panel

### Expected Result

FastAPI starts on:

```text
http://127.0.0.1:8000
```

### Validation

- click `Launch backend`
- call `GET /health`
- confirm `Backend OK` is displayed

## 3. Dashboard Inside PySide6

### Objective

Display the HTML dashboard inside the desktop launcher.

### UI

- dashboard tab or embedded view

### Expected Result

The dashboard appears inside the PySide6 window.

### Validation

- launch the desktop app
- verify the dashboard is visible
- verify the dark blue night mode button is visible

## 4. Dashboard Buttons Connected To FastAPI

### Objective

Connect all dashboard action buttons to the backend API.

### UI Buttons

- `Demarrer Broker`
- `Arreter Broker`
- `Demarrer Subscriber`
- `Envoyer Message`
- `Redemarrer Broker`
- `Ouvrir Terminal`

### Expected Result

Each button calls a FastAPI route and displays the JSON response in the logs.

### Validation

- click each button
- confirm the terminal log updates immediately
- confirm the API response appears

## 5. Backend Command Routes

### Objective

Implement every backend command route expected by the dashboard.

### Routes

```text
POST /api/commands/start-broker
POST /api/commands/stop-broker
POST /api/commands/start-subscriber
POST /api/commands/publish-temperature
POST /api/commands/restart-broker
POST /api/commands/open-terminal
```

### Expected Result

Each route returns a clear JSON response.

### Validation

- test each route from the dashboard
- test each route from FastAPI docs
- verify backend logs

## 6. Broker Status

### Objective

Track and display the broker state.

### UI

- broker status card
- sidebar broker status widget

### States

- `Connected`
- `Disconnected`
- `Starting`
- `Error`

### Validation

- start broker
- stop broker
- restart broker
- verify UI status changes correctly

## 7. Live Logs

### Objective

Show backend and command events in the dashboard terminal panel.

### UI

- dark terminal log panel

### Expected Logs

```text
[INFO] Broker started
[SUB] Subscriber started
[PUB] Message sent
[ERROR] ...
```

### Validation

- trigger each command
- verify one readable log line is added per event

## 8. Send Message Popup

### Objective

Allow the user to send a custom MQTT message.

### UI

- modal popup opened by `Envoyer Message`
- input: `topic`
- input: `message`
- buttons: `Send`, `Cancel`

### Expected Result

The message is sent to FastAPI, then to MQTT.

### Validation

- open popup
- send `25C` on topic `temperature`
- confirm the message appears in logs
- confirm the message appears in the topic message list

## 9. Topic Messages View

### Objective

Display sent and received messages for the `temperature` topic.

### UI

- message list panel

### Expected Result

The UI shows message direction and content.

### Example

```text
25C sent
25C received
24C received
```

### Validation

- publish a message
- confirm it appears as sent
- simulate or receive a message
- confirm it appears as received

## 10. Real Time Updates

### Objective

Update logs and messages without manual refresh.

### First Version

- polling endpoint: `GET /api/logs`

### Later Version

- WebSocket

### Validation

- trigger an event in backend
- confirm UI updates automatically

## 11. Repair Environment

### Objective

Allow the launcher to repair the local environment.

### UI

- button: `Repair environment`
- installation logs panel

### Behavior

- run `scripts/install.ps1`
- display script output in the launcher

### Validation

- click repair
- confirm installation logs appear
- confirm dependency check is run again after repair

## 12. Windows EXE Packaging

### Objective

Package the launcher as a Windows executable.

### Tool

- PyInstaller

### Expected Result

Create:

```text
DesktopIoTOrchestrator.exe
```

### Validation

- double-click the `.exe`
- verify dependency check works
- verify backend starts
- verify dashboard displays

## Recommended Order

1. Dependency check
2. Backend start
3. Dashboard embedded in PySide6
4. API command routes
5. Dashboard buttons connected to backend
6. Broker status
7. Live logs
8. Message popup
9. Topic messages view
10. Real time updates
11. Repair environment
12. Windows `.exe`

## Definition Of Done

A feature is done only when:

- code is implemented
- manual test passes
- any broken behavior is fixed
- commit is created
- next feature can start safely



Notre planning maintenant, propre et logique:

1. Stabiliser l’environnement
- `.gitignore` OK
- `.venv/` ignoré
- `temp_local/` ignoré
- environnement Python installé et réparé
- JS vérifié avec `npm run check`

2. Commit local déjà fait
- dernier commit local: `Ajouter venv et setup JS`
- push GitHub en attente parce que GitHub ne répondait pas côté réseau: `Could not resolve host: github.com`

3. Prochaine action immédiate
- retenter `git push`
- vérifier que GitHub reçoit bien le commit

4. Ensuite: rendre le projet lançable facilement
- créer un script `run.ps1`
- démarrer FastAPI avec `.venv`
- ouvrir le dashboard
- préparer le lancement du launcher PySide6

5. Ensuite: vraie app desktop
- améliorer le launcher PySide6
- ajouter bouton `Réparer environnement`
- intégrer le dashboard dans la fenêtre
- afficher les logs du backend

6. Ensuite: packaging portfolio
- préparer PyInstaller
- générer `DesktopIoTOrchestrator.exe`
- ajouter instructions `.exe` dans README
- refaire GIF si besoin

Ma recommandation: on fait maintenant **`git push`**, puis on crée **`run.ps1`**.
