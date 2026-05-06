import { useEffect, useMemo, useState } from "react";
import { FileList } from "./components/FileList";
import { PairTable } from "./components/PairTable";
import { PreviewTable } from "./components/PreviewTable";
import { ProgressBar } from "./components/ProgressBar";
import { ResultsSummary } from "./components/ResultsSummary";
import {
  executeReplacements,
  isTauri,
  onProgress,
  previewReplacements,
} from "./ipc";
import type {
  ExecuteResponse,
  FnrPair,
  MatchRow,
  PreviewResponse,
  ProgressEvent,
} from "./types";
import "./styles/global.css";
import "./styles/app.css";

type View = "build" | "preview" | "executing" | "results";

type FileStatus = "pending" | "processing" | "done" | "error";

export default function App() {
  const [view, setView] = useState<View>("build");
  const [files, setFiles] = useState<string[]>([]);
  const [pairs, setPairs] = useState<FnrPair[]>([
    { find: "", replace: "", case_sensitive: false, use_regex: false },
  ]);

  const [matches, setMatches] = useState<MatchRow[]>([]);
  const [previewErrors, setPreviewErrors] = useState<
    PreviewResponse["errors"]
  >([]);
  const [excluded, setExcluded] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [fileStatus, setFileStatus] = useState<Record<string, FileStatus>>({});
  const [executeResult, setExecuteResult] = useState<ExecuteResponse | null>(
    null,
  );
  const [filesScannedAtPreview, setFilesScannedAtPreview] = useState(0);

  // Subscribe to per-file progress events from the sidecar.
  useEffect(() => {
    if (!isTauri) return;
    let unsubProgress: (() => void) | undefined;
    let unsubDrop: (() => void) | undefined;
    onProgress((e) => {
      setProgress(e);
      setFileStatus((prev) => ({
        ...prev,
        [e.file]: "done",
      }));
    }).then((u) => (unsubProgress = u));

    // Native Tauri file-drop. The browser HTML5 dnd path doesn't carry real
    // paths from the OS; this event does.
    import("@tauri-apps/api/webview").then(({ getCurrentWebview }) => {
      getCurrentWebview()
        .onDragDropEvent((event) => {
          if (event.payload.type !== "drop") return;
          const dropped = (event.payload.paths ?? []).filter((p) =>
            p.toLowerCase().endsWith(".dwg"),
          );
          if (dropped.length === 0) return;
          setFiles((prev) => {
            const seen = new Set(prev);
            const merged = [...prev];
            for (const p of dropped) if (!seen.has(p)) merged.push(p);
            return merged;
          });
        })
        .then((u) => (unsubDrop = u));
    });

    return () => {
      unsubProgress?.();
      unsubDrop?.();
    };
  }, []);

  const validPairs = useMemo(
    () => pairs.filter((p) => p.find.length > 0),
    [pairs],
  );

  const canPreview = files.length > 0 && validPairs.length > 0 && !busy;

  const includedMatches = useMemo(
    () => matches.filter((_, i) => !excluded.has(`${matches[i].file}|${i}`)),
    [matches, excluded],
  );

  const includedFiles = useMemo(
    () => Array.from(new Set(includedMatches.map((m) => m.file))),
    [includedMatches],
  );

  const handlePreview = async () => {
    setError(null);
    setBusy(true);
    try {
      const resp = await previewReplacements(files, validPairs);
      setMatches(resp.matches);
      setPreviewErrors(resp.errors);
      setFilesScannedAtPreview(resp.files_scanned);
      setExcluded(new Set());
      setView("preview");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleExecute = async () => {
    if (includedFiles.length === 0) return;
    setError(null);
    setBusy(true);
    setView("executing");

    // Reset per-file status to pending for the files we will touch.
    const initial: Record<string, FileStatus> = {};
    includedFiles.forEach((f) => (initial[f] = "pending"));
    setFileStatus(initial);
    setProgress({
      status: "progress",
      file: "",
      processed: 0,
      total: includedFiles.length,
      changes: 0,
    });

    try {
      const resp = await executeReplacements(includedFiles, validPairs);
      // Mark any files reported as failed so the file list shows ✗.
      setFileStatus((prev) => {
        const next = { ...prev };
        for (const err of resp.errors) next[err.file] = "error";
        return next;
      });
      setExecuteResult(resp);
      setView("results");
    } catch (e) {
      setError(String(e));
      setView("preview");
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    setView("build");
    setMatches([]);
    setPreviewErrors([]);
    setExcluded(new Set());
    setExecuteResult(null);
    setProgress(null);
    setFileStatus({});
    setError(null);
  };

  const toggleExclude = (id: string) => {
    setExcluded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Batch Find &amp; Replace</h1>
          <div className="subtitle">
            Chamber 19 · DWG · {view === "build" ? "build" : view}
          </div>
        </div>
        {!isTauri && (
          <div className="warning-text mono">
            Browser preview — Tauri commands disabled
          </div>
        )}
      </header>

      {view === "build" && (
        <>
          <div className="app-body">
            <FileList files={files} onChange={setFiles} status={fileStatus} />
            <PairTable pairs={pairs} onChange={setPairs} />
          </div>
          <footer className="app-footer">
            <span className="dim mono">
              {files.length} file{files.length === 1 ? "" : "s"} ·{" "}
              {validPairs.length} pair{validPairs.length === 1 ? "" : "s"}
            </span>
            <span style={{ display: "flex", gap: 12, alignItems: "center" }}>
              {error && <span className="error-text mono">{error}</span>}
              <button
                className="primary"
                disabled={!canPreview}
                onClick={handlePreview}
              >
                {busy ? "Scanning…" : "Preview"}
              </button>
            </span>
          </footer>
        </>
      )}

      {view === "preview" && (
        <>
          <div className="app-body">
            <div className="panel right" style={{ width: "100%" }}>
              <div className="panel-header">
                <h2>
                  Preview · {includedMatches.length} of {matches.length}{" "}
                  matches selected
                </h2>
              </div>
              <div className="panel-body">
                {matches.length > 0 && (
                  <div className="dim mono" style={{ marginBottom: 12 }}>
                    Note: unchecking every row in a file excludes that file
                    from execute. Within an included file, the sidecar
                    re-applies all configured pairs.
                  </div>
                )}
                {previewErrors.length > 0 && (
                  <div className="error-list">
                    <h3>Scan errors</h3>
                    <ul>
                      {previewErrors.map((e, i) => (
                        <li key={i}>
                          <strong>{e.file}</strong>: {e.error}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <PreviewTable
                  matches={matches}
                  excluded={excluded}
                  onToggle={toggleExclude}
                />
              </div>
            </div>
          </div>
          <footer className="app-footer">
            <button onClick={() => setView("build")}>← Back</button>
            <span style={{ display: "flex", gap: 12, alignItems: "center" }}>
              {error && <span className="error-text mono">{error}</span>}
              <button
                className="primary"
                disabled={includedMatches.length === 0 || busy}
                onClick={handleExecute}
              >
                Execute ({includedMatches.length} change
                {includedMatches.length === 1 ? "" : "s"} across{" "}
                {includedFiles.length} file
                {includedFiles.length === 1 ? "" : "s"})
              </button>
            </span>
          </footer>
        </>
      )}

      {view === "executing" && progress && (
        <div className="app-body" style={{ flexDirection: "column" }}>
          <div className="panel right" style={{ width: "100%" }}>
            <div className="panel-header">
              <h2>Executing…</h2>
            </div>
            <div className="panel-body">
              <ProgressBar
                processed={progress.processed}
                total={progress.total}
                current={progress.file}
              />
              <div style={{ marginTop: 24 }}>
                {includedFiles.map((f) => (
                  <div key={f} className="file-row" title={f}>
                    <span className="status">
                      {fileStatus[f] === "done" ? (
                        <span className="success-text">✓</span>
                      ) : fileStatus[f] === "error" ? (
                        <span className="error-text">✗</span>
                      ) : (
                        <span className="spinner" />
                      )}
                    </span>
                    <span className="name">{f}</span>
                    <span />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {view === "results" && executeResult && (
        <>
          <div className="app-body">
            <div className="panel right" style={{ width: "100%" }}>
              <div className="panel-header">
                <h2>Results</h2>
              </div>
              <div className="panel-body">
                <ResultsSummary
                  result={executeResult}
                  filesScanned={filesScannedAtPreview}
                />
              </div>
            </div>
          </div>
          <footer className="app-footer">
            <span />
            <button className="primary" onClick={reset}>
              New job
            </button>
          </footer>
        </>
      )}
    </div>
  );
}
