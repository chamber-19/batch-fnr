# Batch FNR Backend (Local)

This service exposes the batch find/replace workflow as stateless HTTP endpoints.
It shells out to the existing `.NET` sidecar (`processor/BatchFnr`) per request.

## Prerequisites

- Python 3.13+
- .NET 10 SDK
- AutoCAD 2025/2026/2027 installed locally

## Start

```bash
# Build sidecar once

dotnet build processor/BatchFnr.sln

# Install backend deps
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-build.txt

# Run API
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Open API docs at `http://127.0.0.1:8000/docs`.

## Optional environment overrides

- `BATCH_FNR_SIDECAR_EXE`: absolute path to `BatchFnr.exe`
- `BATCH_FNR_SIDECAR_TIMEOUT`: request timeout in seconds (default `600`)

## Quick health check

```bash
curl http://127.0.0.1:8000/api/health
```

## Run tests

```bash
python -m pytest backend/tests -v
```
