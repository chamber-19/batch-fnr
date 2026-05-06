# Batch Find & Replace

Chamber 19 desktop tool for batch find-and-replace across AutoCAD DWG files.

One job. Open a list of drawings, declare a list of `find → replace` pairs,
preview every match, execute. Done.

## Stack

- **UI** — React 19 + Vite + TypeScript inside a Tauri 2.0 shell
  (`frontend/`)
- **DWG processor** — .NET 8 console app using the headless AutoCAD
  managed API (`processor/`), spawned by Tauri as a sidecar and driven over
  newline-delimited JSON on stdin/stdout
- **No Docker, no localhost HTTP, no Python GUI, no COM**

See [`AGENTS.md`](AGENTS.md) for the full architecture rules and the list
of features that have been retired.

## Build

Requires:

- .NET 8 SDK and a local AutoCAD install (for `accoremgd.dll` /
  `acdbmgd.dll`)
- Rust 1.77+ and the platform Tauri prerequisites
- Node 20+ and npm

```bash
# .NET sidecar
dotnet build processor/BatchFnr.sln

# Frontend deps
cd frontend && npm install

# Run the desktop app in development
npm run tauri dev

# Production bundle
npm run tauri build
```

If your AutoCAD lives somewhere other than the default
`C:\Program Files\Autodesk\AutoCAD 2026`, point the build at it:

```bash
dotnet build processor/BatchFnr.sln -p:AcadDir="C:\Program Files\Autodesk\AutoCAD 2025"
```

## Layout

```
frontend/                React 19 UI (Build → Preview → Results)
  src/
    components/          FileList, PairTable, PreviewTable, ResultsSummary, ProgressBar
    App.tsx              State machine + IPC orchestration
  src-tauri/
    src/
      commands/fnr.rs    preview_replacements / execute_replacements / scan_folder_for_dwg
      lib.rs, main.rs    Tauri builder
    tauri.conf.json
    Cargo.toml

processor/               .NET 8 sidecar
  BatchFnr.sln
  Directory.Build.props  AcadDir override
  BatchFnr/
    Program.cs           stdin/stdout JSON loop
    DrawingProcessor.cs  preview + execute, headless Database
    EntityTraversal.cs   MText / DBText / AttributeReference / Dimension
    MTextStripper.cs     Explicit (non-regex) MTEXT formatting-code stripper
    ReplacementEngine.cs Pure find/replace with case + regex flags
    Models.cs            JSON DTOs

BatchFindAndReplaceV1/   Historical Python reference (do not invoke)
```

## Sidecar protocol

Stdin (one JSON object per line):

```json
{"action":"preview","files":["C:/dwg/foo.dwg"],"pairs":[{"find":"25074","replace":"25075","case_sensitive":false,"use_regex":false}]}
{"action":"execute","files":["C:/dwg/foo.dwg"],"pairs":[ ... ]}
```

Stdout: one JSON object per line, flushed immediately. `progress` events
arrive between files during `execute`; the run terminates with
`{"status":"complete", ...}`.
