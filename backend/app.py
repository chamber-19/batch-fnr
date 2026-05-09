from fastapi import FastAPI, HTTPException

from backend.core.business_logic import SidecarProtocolError, SidecarRunner
from backend.core.models import (
    ExecuteRequest,
    ExecuteResponse,
    HealthResponse,
    PreviewRequest,
    PreviewResponse,
    ScanFolderRequest,
)
from backend.core.utils import find_dwg_files

SERVICE_NAME = "batch-fnr-backend"
SERVICE_VERSION = "1.0.0"

app = FastAPI(title="Batch Find and Replace Backend", version=SERVICE_VERSION)


def _get_runner() -> SidecarRunner:
    runner = getattr(app.state, "runner", None)
    if runner is None:
        runner = SidecarRunner()
        app.state.runner = runner
    return runner


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.post("/api/scan-folder")
def scan_folder(payload: ScanFolderRequest) -> dict[str, list[str]]:
    try:
        files = find_dwg_files(payload.folder)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"files": files}


@app.post("/api/preview", response_model=PreviewResponse)
def preview(payload: PreviewRequest) -> PreviewResponse:
    if len(payload.files) == 0:
        raise HTTPException(status_code=400, detail="files cannot be empty")
    if len(payload.pairs) == 0:
        raise HTTPException(status_code=400, detail="pairs cannot be empty")

    pairs = [pair.model_dump() for pair in payload.pairs]
    try:
        response = _get_runner().run_action("preview", payload.files, pairs)
    except (SidecarProtocolError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return PreviewResponse.model_validate(response)


@app.post("/api/execute", response_model=ExecuteResponse)
def execute(payload: ExecuteRequest) -> ExecuteResponse:
    if len(payload.files) == 0:
        raise HTTPException(status_code=400, detail="files cannot be empty")
    if len(payload.pairs) == 0:
        raise HTTPException(status_code=400, detail="pairs cannot be empty")

    pairs = [pair.model_dump() for pair in payload.pairs]
    try:
        response = _get_runner().run_action("execute", payload.files, pairs)
    except (SidecarProtocolError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ExecuteResponse.model_validate(response)
