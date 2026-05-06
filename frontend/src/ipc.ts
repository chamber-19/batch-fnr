/**
 * Tauri IPC wrapper. All `invoke()` calls are gated by an `isTauri` guard so
 * the UI can still render in a plain browser (e.g. for component dev) without
 * blowing up on a missing global.
 */
import type {
  ExecuteResponse,
  FnrPair,
  PreviewResponse,
  ProgressEvent,
} from "./types";

export const isTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

async function invoke<T>(
  cmd: string,
  args: Record<string, unknown>,
): Promise<T> {
  if (!isTauri) {
    throw new Error(
      `Cannot invoke '${cmd}' outside of the Tauri runtime. Run via 'npm run tauri dev'.`,
    );
  }
  const { invoke: tauriInvoke } = await import("@tauri-apps/api/core");
  return tauriInvoke<T>(cmd, args);
}

export function previewReplacements(
  files: string[],
  pairs: FnrPair[],
): Promise<PreviewResponse> {
  return invoke<PreviewResponse>("preview_replacements", { files, pairs });
}

export function executeReplacements(
  files: string[],
  pairs: FnrPair[],
): Promise<ExecuteResponse> {
  return invoke<ExecuteResponse>("execute_replacements", { files, pairs });
}

export async function pickDwgFiles(): Promise<string[]> {
  if (!isTauri) return [];
  const { open } = await import("@tauri-apps/plugin-dialog");
  const picked = await open({
    multiple: true,
    filters: [{ name: "AutoCAD Drawing", extensions: ["dwg"] }],
  });
  if (picked === null) return [];
  return Array.isArray(picked) ? picked : [picked];
}

export async function pickFolder(): Promise<string | null> {
  if (!isTauri) return null;
  const { open } = await import("@tauri-apps/plugin-dialog");
  const picked = await open({ directory: true, multiple: false });
  return typeof picked === "string" ? picked : null;
}

/**
 * Recursively list .dwg files in a folder. Implemented in Rust so we don't
 * have to expose an arbitrary fs.read_dir capability to the webview.
 */
export async function scanFolderForDwg(folder: string): Promise<string[]> {
  return invoke<string[]>("scan_folder_for_dwg", { folder });
}

/**
 * Subscribe to progress events emitted by the Rust shell while a batch is
 * running. Returns an unsubscribe function.
 */
export async function onProgress(
  cb: (e: ProgressEvent) => void,
): Promise<() => void> {
  if (!isTauri) return () => {};
  const { listen } = await import("@tauri-apps/api/event");
  const un = await listen<ProgressEvent>("fnr-progress", (event) =>
    cb(event.payload),
  );
  return un;
}
