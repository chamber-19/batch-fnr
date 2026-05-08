//! Tauri commands that bridge the React UI to the .NET sidecar.
//!
//! Communication with the sidecar is line-delimited JSON on stdin/stdout —
//! one JSON object per line, flushed after every write. This module owns the
//! sidecar lifecycle for a single request: spawn → write request → read until
//! the terminating `{"status":"complete"}` line → kill.
//!
//! Intermediate `{"status":"progress"}` lines are forwarded to the frontend
//! via the `fnr-progress` event so the UI can update its progress bar.

use std::path::PathBuf;
use std::process::Stdio;

use serde::{Deserialize, Serialize};
use serde_json::Value;
use tauri::{AppHandle, Emitter, Manager};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, Command};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FnrPair {
    pub find: String,
    pub replace: String,
    pub case_sensitive: bool,
    pub use_regex: bool,
}

#[derive(Debug, Serialize)]
struct SidecarRequest<'a> {
    action: &'a str,
    files: &'a [String],
    pairs: &'a [FnrPair],
}

/// Resolve the sidecar binary path. We look first in the bundled `resources`
/// directory (production install), then in the dev-time output directory for
/// `dotnet build` so `npm run tauri dev` works without a release build.
fn sidecar_path(app: &AppHandle) -> Result<PathBuf, String> {
    let exe_name = if cfg!(target_os = "windows") {
        "BatchFnr.exe"
    } else {
        "BatchFnr"
    };

    // Production: bundled under <resources>/processor/BatchFnr/<exe>
    if let Ok(resource_dir) = app.path().resource_dir() {
        let candidate = resource_dir
            .join("processor")
            .join("BatchFnr")
            .join(exe_name);
        if candidate.exists() {
            return Ok(candidate);
        }
        // Tauri's `bundle.resources` flattens its globbed paths into the
        // resource dir's root, so check there too.
        let flat = resource_dir.join(exe_name);
        if flat.exists() {
            return Ok(flat);
        }
    }

    // Dev fallback: ../../processor/BatchFnr/bin/{x64/Debug,x64/Release}/net10.0-windows/<exe>
    // This makes `cargo run` and `tauri dev` work as long as the .NET project
    // has been built once.
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    for cfg in ["x64/Debug", "x64/Release"] {
        let candidate = manifest_dir
            .join("..")
            .join("..")
            .join("processor")
            .join("BatchFnr")
            .join("bin")
            .join(cfg)
            .join("net10.0-windows")
            .join(exe_name);
        if candidate.exists() {
            return Ok(candidate);
        }
    }

    Err(format!(
        "BatchFnr sidecar not found. Build it with `dotnet build processor/BatchFnr.sln` and try again. Looking for `{exe_name}`."
    ))
}

fn spawn_sidecar(app: &AppHandle) -> Result<Child, String> {
    let exe = sidecar_path(app)?;
    Command::new(&exe)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true)
        .spawn()
        .map_err(|e| format!("failed to spawn sidecar `{}`: {e}", exe.display()))
}

/// Send one JSON request, then read newline-delimited responses until we see
/// a final `{"status":"complete"}` line. Progress lines are emitted on the
/// `fnr-progress` event channel.
async fn run_action(
    app: AppHandle,
    action: &str,
    files: Vec<String>,
    pairs: Vec<FnrPair>,
) -> Result<Value, String> {
    let mut child = spawn_sidecar(&app)?;

    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| "sidecar stdin not available".to_string())?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "sidecar stdout not available".to_string())?;
    let stderr = child
        .stderr
        .take()
        .ok_or_else(|| "sidecar stderr not available".to_string())?;

    // Drain stderr into a buffer in the background so it never blocks the
    // child, and so we can include it in error messages.
    let stderr_handle = tokio::spawn(async move {
        let mut buf = String::new();
        let mut reader = BufReader::new(stderr);
        let _ = tokio::io::AsyncReadExt::read_to_string(&mut reader, &mut buf).await;
        buf
    });

    // Write the single request line.
    let req = SidecarRequest {
        action,
        files: &files,
        pairs: &pairs,
    };
    let mut payload =
        serde_json::to_vec(&req).map_err(|e| format!("encode request: {e}"))?;
    payload.push(b'\n');
    stdin
        .write_all(&payload)
        .await
        .map_err(|e| format!("write to sidecar: {e}"))?;
    stdin.flush().await.ok();
    // Closing stdin signals end-of-input so the sidecar's read loop exits
    // after sending its final response.
    drop(stdin);

    // Read responses line by line.
    let mut reader = BufReader::new(stdout);
    let mut line = String::new();
    let mut final_value: Option<Value> = None;

    loop {
        line.clear();
        let n = reader
            .read_line(&mut line)
            .await
            .map_err(|e| format!("read from sidecar: {e}"))?;
        if n == 0 {
            // EOF before completion.
            break;
        }
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let value: Value = match serde_json::from_str(trimmed) {
            Ok(v) => v,
            Err(e) => {
                // The sidecar is supposed to emit only valid JSON. Forward the
                // raw line in the error so debugging is possible.
                return Err(format!(
                    "invalid sidecar output: {e}; line was: {trimmed}"
                ));
            }
        };

        let status = value.get("status").and_then(|s| s.as_str()).unwrap_or("");
        match status {
            "progress" => {
                // Best-effort emit; a failed emit should not abort the batch.
                let _ = app.emit("fnr-progress", value.clone());
            }
            "error" => {
                return Err(value
                    .get("error")
                    .and_then(|s| s.as_str())
                    .unwrap_or("unknown sidecar error")
                    .to_string());
            }
            "complete" => {
                final_value = Some(value);
                break;
            }
            _ => {
                // Unknown payload type — forward as a progress event so the UI
                // can decide what to do with it instead of silently dropping.
                let _ = app.emit("fnr-progress", value);
            }
        }
    }

    // Reap the child so it doesn't linger.
    let _ = child.wait().await;
    let stderr_contents = stderr_handle.await.unwrap_or_default();

    final_value.ok_or_else(|| {
        if stderr_contents.is_empty() {
            "sidecar exited before completing".to_string()
        } else {
            format!("sidecar exited before completing. stderr: {stderr_contents}")
        }
    })
}

#[tauri::command]
pub async fn preview_replacements(
    app: AppHandle,
    files: Vec<String>,
    pairs: Vec<FnrPair>,
) -> Result<Value, String> {
    run_action(app, "preview", files, pairs).await
}

#[tauri::command]
pub async fn execute_replacements(
    app: AppHandle,
    files: Vec<String>,
    pairs: Vec<FnrPair>,
) -> Result<Value, String> {
    run_action(app, "execute", files, pairs).await
}

/// Recursively collect `.dwg` paths under `folder`. Done in Rust so the
/// webview never needs an open `fs` capability.
#[tauri::command]
pub async fn scan_folder_for_dwg(folder: String) -> Result<Vec<String>, String> {
    // walkdir is blocking; offload to the blocking pool to keep the async
    // runtime responsive on huge folders.
    tokio::task::spawn_blocking(move || {
        let mut out = Vec::new();
        for entry in walkdir::WalkDir::new(&folder).follow_links(false) {
            let entry = match entry {
                Ok(e) => e,
                Err(_) => continue,
            };
            if !entry.file_type().is_file() {
                continue;
            }
            let path = entry.path();
            let ext_match = path
                .extension()
                .and_then(|e| e.to_str())
                .map(|e| e.eq_ignore_ascii_case("dwg"))
                .unwrap_or(false);
            if ext_match {
                if let Some(s) = path.to_str() {
                    out.push(s.to_string());
                }
            }
        }
        out
    })
    .await
    .map_err(|e| format!("folder scan failed: {e}"))
}
