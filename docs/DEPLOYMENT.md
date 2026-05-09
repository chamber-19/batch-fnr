# Deployment

## Local development

```bash
dotnet build processor/BatchFnr.sln
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-build.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Validate:

```bash
curl http://127.0.0.1:8000/api/health
python -m pytest backend/tests -v
```

## Runtime configuration

- `BATCH_FNR_SIDECAR_EXE`: absolute path to `BatchFnr.exe`
- `BATCH_FNR_SIDECAR_TIMEOUT`: sidecar timeout in seconds (default `600`)

## Docker

A reference Dockerfile exists at `backend/Dockerfile`.

Current image behavior:

- Installs Python dependencies
- Copies `backend/` and `processor/`
- Starts `uvicorn` on `0.0.0.0:8000`

Note: production containers still require access to a compatible AutoCAD-managed
runtime path for the sidecar's AutoCAD assembly resolution.

## CI release workflow

Tag push (`v*`) runs:

1. Python dependency install
2. Backend tests (`pytest`)
3. Backend boot
4. Health endpoint smoke check
