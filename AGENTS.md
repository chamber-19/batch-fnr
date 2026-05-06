# Batch Find & Replace — agent guide

This repository is a **single-purpose** Chamber 19 desktop tool: batch find
and replace text across multiple AutoCAD DWG files. Nothing else.

## Architecture (hard rules)

```
frontend/                 React 19 + Vite + TypeScript inside a Tauri 2.0 shell
├── src/                  UI (Build → Preview → Results states)
└── src-tauri/            Rust shell, IPC commands, sidecar lifecycle

processor/                .NET 8 console app — the AutoCAD sidecar
└── BatchFnr/             Headless Database (no COM, no AutoCAD UI)
```

The frontend talks to the .NET sidecar **only** through the Rust shell, and
the Rust shell talks to the sidecar **only** over newline-delimited JSON on
stdin/stdout. There is no HTTP, no WebSocket, no localhost server, and no
COM automation between any two layers. One JSON object per line, flushed
after every write — same convention as every other Chamber 19 sidecar.

## What was retired (do **not** re-add)

The previous repository had grown a number of orthogonal tools and a Python
web stack. All of it is gone, on purpose:

- **Text unifier** — retired
- **Layer cleanup** — retired
- **Text scaling** — retired
- **Docker / `docker-compose` / nginx** — retired
- **`web-panel/` (FastAPI + React web UI)** — retired
- **`api_wrapper.py` (FastAPI REST wrapper)** — retired
- **`V1.5/` (PySide6 rewrite that was never finished)** — retired; every
  endpoint returned mock data
- **PySide6 / Tkinter / any Python GUI** — retired

The only surviving Python is `BatchFindAndReplaceV1/`, kept solely as the
historical reference for the entity-traversal logic that the new .NET
sidecar reimplements. It is not invoked, packaged, or tested.

## Forbidden

Do not, under any circumstances:

- Re-introduce the text unifier, layer cleanup, scaling, or any other
  side-feature. This tool does **one** thing.
- Add Docker, docker-compose, nginx, or any container orchestration.
- Add a Python GUI (PySide6, Tkinter, etc.).
- Add COM automation (`win32com`, `pythoncom`, `pyautocad`). The .NET
  sidecar uses the headless managed API (`Database` class) only.
- Add a localhost HTTP server, REST API, or WebSocket between the UI and
  the backend. Use Tauri IPC only.
- Copy the Autodesk reference assemblies into the build output. The
  `<Private>False</Private>` setting on every `accoremgd` / `acdbmgd`
  reference is mandatory; copying them produces runtime version conflicts.

## Tauri 2.0 conventions

- `app.path()` (not the deprecated `app.path_resolver()`)
- `app.emit(...)` (not `app.emit_all(...)`)
- Commands return `Result<serde_json::Value, String>` — never `unwrap()`
- Sidecar spawn must run on a blocking-friendly executor
  (`tokio::task::spawn_blocking` or async `tokio::process::Command`)
- All UI `invoke()` calls are guarded by
  `const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;`
  so the React app still renders in a plain browser

## Environment verification

Run all three before merging non-trivial changes:

```bash
# .NET sidecar (requires AutoCAD installed locally so accoremgd/acdbmgd resolve;
# override path with -p:AcadDir="C:\Program Files\Autodesk\AutoCAD 2025")
dotnet build processor/BatchFnr.sln

# Tauri shell
cd frontend/src-tauri && cargo check

# Frontend
cd frontend && npm install && npm run build
```

## Design system (non-negotiable)

| Token        | Value     |
| ------------ | --------- |
| Background   | `#1C1B19` |
| Accent       | `#C4884D` |
| Success      | `#6B9E6B` |
| Warning      | `#C4A24D` |
| Error        | `#B85C5C` |
| Body font    | DM Sans   |
| Mono font    | JetBrains Mono |

Tone: warm industrial, matter-of-fact. Tokens live in
`frontend/src/styles/global.css`; do not introduce a CSS framework.
