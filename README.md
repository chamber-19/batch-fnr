# Batch Find & Replace

Batch Find & Replace is now a stateless backend service for batch text
replacement across AutoCAD DWG files.

The service exposes HTTP endpoints for:

- Folder scan (`/api/scan-folder`)
- Preview (`/api/preview`)
- Execute (`/api/execute`)
- Health check (`/api/health`)

The backend delegates DWG operations to the existing `.NET 10` sidecar in
`processor/BatchFnr`, which uses headless AutoCAD APIs.

## Current architecture

- `backend/`: Python FastAPI HTTP service (active)
- `processor/BatchFnr/`: .NET sidecar with AutoCAD entity processing (active)
- `frontend/`: legacy Tauri UI code (deprecated, kept for reference only)

This repo no longer ships a standalone desktop shell. Desktop integration is
handled in Chamber 19 `launcher`.

## Requirements

- Python 3.13+
- .NET 10 SDK
- AutoCAD 2025/2026/2027 installed locally

## Local development

```bash
# Build .NET sidecar first
dotnet build processor/BatchFnr.sln

# Install backend dependencies
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-build.txt

# Run API
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Open API docs at `http://127.0.0.1:8000/docs`.

## Tests

```bash
python -m pytest backend/tests -v
```

## Repository layout

```text
backend/                 FastAPI service (active)
  app.py                 API routes and validation
  core/
    business_logic.py    Sidecar invocation + NDJSON parsing
    models.py            Request/response models
    utils.py             File-system helpers
  tests/
    test_endpoints.py    API tests

processor/BatchFnr/      .NET AutoCAD sidecar (active)

frontend/                Legacy Tauri app (deprecated)
```
