# Copilot instructions — batch-fnr

## What this repo is

A Chamber 19 Tauri 2.0 desktop app that does **one** thing: batch find and
replace text inside AutoCAD DWG files. The app has three layers:

1. **React 19 + TypeScript** UI in `frontend/src/`
2. **Rust / Tauri 2.0** shell in `frontend/src-tauri/` (IPC + sidecar lifecycle)
3. **.NET 10 console app** in `processor/BatchFnr/` — the AutoCAD sidecar

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

## Tauri 2.0 IPC rules

- Use `app.path()`, not `app.path_resolver()`.
- Use `app.emit(...)`, not `app.emit_all(...)`.
- Commands return `Result<serde_json::Value, String>`. Never `unwrap()` or
  `expect()` on user-reachable code paths.
- Long-running sidecar work runs through `tokio::process::Command` (already
  async) or `tokio::task::spawn_blocking` — never block the runtime.
- The React side gates every `invoke()` behind:
  ```ts
  const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
  ```
  so the UI still renders in a plain browser.
- Progress events from the sidecar are forwarded as `fnr-progress` via
  `app.emit`. The frontend listens with `@tauri-apps/api/event#listen`.

## Frontend rules

- React 19 + Vite + TypeScript only. **No** Tailwind, **no** Material UI,
  **no** Chakra. Design tokens live in `frontend/src/styles/global.css`.
- Three states only: **Build → Preview → Results**. Don't add modal flows
  or a "settings" page.
- Colors and fonts are non-negotiable: `#1C1B19`, `#C4884D`, `#6B9E6B`,
  `#C4A24D`, `#B85C5C`, DM Sans, JetBrains Mono.

## Forbidden re-introductions

If you find yourself reaching for any of these, stop:

- Docker / docker-compose / nginx / any container stack
- A FastAPI / Flask / Express / localhost HTTP layer between UI and backend
- PySide6, Tkinter, or any other Python GUI
- COM automation in any form
- The text unifier, layer cleanup, or text scaling tools

## Verification commands

```bash
dotnet build processor/BatchFnr.sln          # .NET sidecar
cd frontend/src-tauri && cargo check         # Tauri shell
cd frontend && npm install && npm run build  # Frontend
```

The .NET build requires AutoCAD's `accoremgd.dll` / `acdbmgd.dll` to be
resolvable. Override the install path with
`dotnet build processor/BatchFnr.sln -p:AcadDir="C:\Program Files\Autodesk\AutoCAD 2025"`.
