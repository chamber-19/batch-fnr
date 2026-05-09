# Batch Find & Replace — agent guide

This repository is a **single-purpose** Chamber 19 backend service: batch
find and replace text across multiple AutoCAD DWG files. Nothing else.

## Architecture (hard rules)

```text
backend/                  Python FastAPI service (HTTP API)
└── app.py                /api/health, /api/scan-folder, /api/preview, /api/execute

processor/                .NET 10 console app — the AutoCAD sidecar
└── BatchFnr/             Headless Database (no COM, no AutoCAD UI)

frontend/                 Legacy Tauri UI (deprecated, not built/deployed)
```

The backend talks to the .NET sidecar over newline-delimited JSON on
stdin/stdout. One JSON object per line, flushed after every write.

## What was retired (do **not** re-add)

The previous repository had grown a number of orthogonal tools. All of it is
gone, on purpose:

- **Text unifier** — retired
- **Layer cleanup** — retired
- **Text scaling** — retired
- **Docker / `docker-compose` / nginx** — retired
- **`V1.5/` (PySide6 rewrite that was never finished)** — retired; every
  endpoint returned mock data
- **PySide6 / Tkinter / any Python GUI** — retired
- **`BatchFindAndReplaceV1/`** — deleted; do not recreate it. The V1 logic
  was rewritten in `processor/BatchFnr/` as a .NET 10 headless sidecar.

## Forbidden

Do not, under any circumstances:

- Re-introduce the text unifier, layer cleanup, scaling, or any other
  side-feature. This tool does **one** thing.
- Add docker-compose/nginx orchestration layers for local runtime wiring.
- A single backend Dockerfile is allowed for packaging/deployment.
- Add a Python GUI (PySide6, Tkinter, etc.).
- Add COM automation (`win32com`, `pythoncom`, `pyautocad`). The .NET
  sidecar uses the headless managed API (`Database` class) only.
- Add Tauri IPC back into active runtime flow for this repo.
- Copy the Autodesk reference assemblies into the build output. The
  `<Private>False</Private>` setting on every `accoremgd` / `acdbmgd` /
  `acmgd` reference is mandatory; copying them produces runtime version
  conflicts.

## Backend conventions

- FastAPI endpoints are stateless request/response handlers.
- Use `pathlib.Path` for filesystem handling.
- Return structured HTTP errors (`4xx` for input, `5xx` for execution failures).
- Keep sidecar communication strictly newline-delimited JSON.
- Never use bare `except:`.

## Environment verification

Run these before merging non-trivial changes:

```bash
# .NET sidecar
dotnet build processor/BatchFnr.sln

# Backend tests
python -m pytest backend/tests -v

# Backend run smoke check
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
