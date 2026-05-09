import json
import os
import subprocess
from pathlib import Path
from typing import Any


class SidecarProtocolError(RuntimeError):
    pass


class SidecarRunner:
    def __init__(self, sidecar_exe: str | None = None) -> None:
        self._sidecar_exe = sidecar_exe or self._resolve_default_sidecar_exe()

    @property
    def sidecar_exe(self) -> str:
        return self._sidecar_exe

    def run_action(self, action: str, files: list[str], pairs: list[dict[str, Any]]) -> dict[str, Any]:
        req = {
            "action": action,
            "files": files,
            "pairs": pairs,
        }
        payload = json.dumps(req, separators=(",", ":")) + "\n"
        result = subprocess.run(
            [self._sidecar_exe],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
            timeout=self._timeout_seconds,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            msg = stderr if stderr else f"sidecar exited with code {result.returncode}"
            raise SidecarProtocolError(msg)

        final_response: dict[str, Any] | None = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SidecarProtocolError(f"invalid sidecar output: {line}") from exc

            status = data.get("status")
            if status == "error":
                raise SidecarProtocolError(str(data.get("error", "unknown sidecar error")))
            if status == "complete":
                final_response = data

        if final_response is None:
            stderr = result.stderr.strip()
            extra = f" stderr: {stderr}" if stderr else ""
            raise SidecarProtocolError(f"sidecar returned no completion payload.{extra}")

        return final_response

    @property
    def _timeout_seconds(self) -> int:
        raw = os.environ.get("BATCH_FNR_SIDECAR_TIMEOUT", "600")
        try:
            parsed = int(raw)
        except ValueError:
            parsed = 600
        return max(parsed, 1)

    def _resolve_default_sidecar_exe(self) -> str:
        env_override = os.environ.get("BATCH_FNR_SIDECAR_EXE")
        if env_override:
            path = Path(env_override)
            if path.exists():
                return str(path.resolve())

        repo_root = Path(__file__).resolve().parents[2]
        candidates = [
            repo_root / "processor" / "BatchFnr" / "bin" / "x64" / "Debug" / "net10.0-windows" / "BatchFnr.exe",
            repo_root / "processor" / "BatchFnr" / "bin" / "x64" / "Release" / "net10.0-windows" / "BatchFnr.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate.resolve())

        searched = "\n".join(str(c) for c in candidates)
        raise FileNotFoundError(
            "BatchFnr sidecar executable not found. Build with `dotnet build processor/BatchFnr.sln`."
            f" Searched:\n{searched}"
        )
