import { useCallback, useState, type DragEvent } from "react";
import { pickDwgFiles, pickFolder, scanFolderForDwg, isTauri } from "../ipc";

interface Props {
  files: string[];
  onChange: (files: string[]) => void;
  /** Optional per-file processing status, keyed by absolute path. */
  status?: Record<string, "pending" | "processing" | "done" | "error">;
}

function fileName(p: string): string {
  // Works for both POSIX and Windows paths regardless of host OS.
  const i = Math.max(p.lastIndexOf("/"), p.lastIndexOf("\\"));
  return i >= 0 ? p.slice(i + 1) : p;
}

export function FileList({ files, onChange, status }: Props) {
  const [dragging, setDragging] = useState(false);

  const addFiles = useCallback(
    (incoming: string[]) => {
      const seen = new Set(files);
      const merged = [...files];
      for (const f of incoming) {
        if (!seen.has(f)) {
          merged.push(f);
          seen.add(f);
        }
      }
      onChange(merged);
    },
    [files, onChange],
  );

  const handleBrowse = async () => {
    const picked = await pickDwgFiles();
    if (picked.length) addFiles(picked);
  };

  const handleAddFolder = async () => {
    const folder = await pickFolder();
    if (!folder) return;
    const found = await scanFolderForDwg(folder);
    if (found.length) addFiles(found);
  };

  const remove = (path: string) => {
    onChange(files.filter((f) => f !== path));
  };

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    // The HTML5 dnd path only works in browser dev — in Tauri, file drops are
    // delivered via a separate `tauri://drag-drop` event handled in App.tsx.
    const paths: string[] = [];
    for (const item of Array.from(e.dataTransfer.files)) {
      // In a regular browser the File object has no path; ignore.
      const p = (item as File & { path?: string }).path;
      if (p && p.toLowerCase().endsWith(".dwg")) paths.push(p);
    }
    if (paths.length) addFiles(paths);
  };

  return (
    <div className="panel left">
      <div className="panel-header">
        <h2>Files ({files.length})</h2>
        <div className="panel-actions">
          <button onClick={handleBrowse} disabled={!isTauri}>
            Add files
          </button>
          <button onClick={handleAddFolder} disabled={!isTauri}>
            Add folder
          </button>
        </div>
      </div>
      <div className="panel-body">
        <div
          className={`drop-zone ${dragging ? "dragging" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          Drop DWG files here
        </div>
        {files.length === 0 ? (
          <div className="empty">No files selected.</div>
        ) : (
          files.map((f) => {
            const s = status?.[f];
            return (
              <div key={f} className="file-row" title={f}>
                <span className="status">
                  {s === "processing" ? <span className="spinner" /> : null}
                  {s === "done" ? (
                    <span className="success-text">✓</span>
                  ) : null}
                  {s === "error" ? <span className="error-text">✗</span> : null}
                </span>
                <span className="name">{fileName(f)}</span>
                <button
                  className="danger"
                  onClick={() => remove(f)}
                  aria-label={`Remove ${fileName(f)}`}
                >
                  ×
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
