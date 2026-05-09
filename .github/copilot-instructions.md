# Copilot instructions — batch-fnr

## What this repo is

A Chamber 19 backend service that does **one** thing: batch find and replace
text inside AutoCAD DWG files.

Active runtime layers:

1. **Python FastAPI** service in `backend/`
2. **.NET 10 console app** in `processor/BatchFnr/` — the AutoCAD sidecar

Legacy reference code (not built/deployed):

- `frontend/` (React + Tauri)

Read `AGENTS.md` at the repo root before proposing structural changes.

## Single-purpose, period

This tool does not unify text, clean layers, scale text, or anything else.
Earlier versions of this repo did; those features were retired and must not
return. If a request implies a side-feature, push back and confirm scope.

## .NET sidecar rules

> **Before touching any AutoCAD entity code**, read the relevant files in
> the `autocad-knowledge` repo — it is the authoritative reference for all
> .NET patterns used in this sidecar:
> - `headless-processing.md` — the exact pattern this sidecar follows (`Database(false, true)` + `ReadDwgFile`)
> - `transaction-model.md` — foundation for all entity reads/writes
> - `attributes.md` — block attribute read/write (for any future attribute work)
> - `electrical-engineering.md` — R3P batch scanning patterns, MText caveats, layer conventions
> - `gotchas.md` — 23 known failure modes; check here before opening a bug report
> - `limitations/block-attributes-not-queryable.md` — the architectural reason this tool exists (Autodesk Assistant cannot read attributes)

- Headless **only**: `using var db = new Database(false, true);` plus
  `db.ReadDwgFile(...)`. **No COM**, no `Application.DocumentManager`, no
  `pyautocad` / `win32com` / `pythoncom`.
- Every Autodesk reference (`accoremgd`, `acdbmgd`) must have
  `<Private>False</Private>`. Copying them to the output directory causes
  runtime assembly version conflicts the moment AutoCAD's own copies load.
- Communication with the Rust shell is **newline-delimited JSON on
  stdin/stdout**. One JSON object per line, flush after every write.
  stderr is reserved for fatal/internal diagnostics.
- A failure on one file (locked, corrupt, permission denied) must **not**
  abort the batch. Record it on the response's `errors` array and move on.
- MText: match against the formatting-stripped text (see
  `MTextStripper.cs` — explicit scanner, **not** regex), then prefer to
  rewrite the raw `Contents` so surrounding formatting codes survive.

## Backend service rules

- Endpoints are stateless HTTP request/response handlers.
- Use `pathlib.Path` for filesystem logic.
- Keep sidecar communication newline-delimited JSON on stdin/stdout.
- Return structured HTTP errors: `400` for invalid input, `500` for sidecar/runtime failures.
- Type-hint Python functions and avoid bare `except:`.

## Forbidden re-introductions

If you find yourself reaching for any of these, stop:

- docker-compose / nginx orchestration layers
- Tauri IPC as active transport for this repo
- PySide6, Tkinter, or any other Python GUI
- COM automation in any form
- The text unifier, layer cleanup, or text scaling tools

## Verification commands

```bash
dotnet build processor/BatchFnr.sln     # .NET sidecar
python -m pytest backend/tests -v       # backend tests
python -m uvicorn backend.app:app       # local backend run
```

The .NET build requires AutoCAD's `accoremgd.dll` / `acdbmgd.dll` to be
resolvable. Override the install path with
`dotnet build processor/BatchFnr.sln -p:AcadDir="C:\Program Files\Autodesk\AutoCAD 2025"`.


<!-- Added by chamber-19-skill-sync — required skill references for this repo's stack -->
- Read [`docs/skills/AUTOCAD_DOTNET.md`](https://github.com/chamber-19/.github/blob/main/docs/skills/AUTOCAD_DOTNET.md) before any AutoCAD .NET work.
- Read [`docs/skills/RUST.MD`](https://github.com/chamber-19/.github/blob/main/docs/skills/RUST.MD) before any Rust work.
- Read [`docs/skills/TAURI.MD`](https://github.com/chamber-19/.github/blob/main/docs/skills/TAURI.MD) before any Tauri work.
