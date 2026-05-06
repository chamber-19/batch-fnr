/**
 * Shared types between the React UI and the Rust IPC layer.
 * Keep these in sync with `processor/BatchFnr/Models.cs` and
 * `src-tauri/src/commands/fnr.rs`.
 */

export interface FnrPair {
  find: string;
  replace: string;
  case_sensitive: boolean;
  use_regex: boolean;
}

export interface MatchRow {
  file: string;
  entity_type: string;
  layer: string;
  current_value: string;
  proposed_value: string;
  space: string;
}

export interface FileError {
  file: string;
  error: string;
}

export interface PreviewResponse {
  status: "complete";
  matches: MatchRow[];
  files_scanned: number;
  total_matches: number;
  errors: FileError[];
}

export interface ExecuteResponse {
  status: "complete";
  total_changes: number;
  files_modified: number;
  errors: FileError[];
}

export interface ProgressEvent {
  status: "progress";
  file: string;
  processed: number;
  total: number;
  changes: number;
}
