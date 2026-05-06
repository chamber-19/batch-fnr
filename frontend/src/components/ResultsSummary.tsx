import type { ExecuteResponse } from "../types";

interface Props {
  result: ExecuteResponse;
  filesScanned: number;
}

export function ResultsSummary({ result, filesScanned }: Props) {
  const errors = result.errors ?? [];
  return (
    <div>
      <div className="results-summary">
        <div className="results-card">
          <div className="label">Files scanned</div>
          <div className="value">{filesScanned}</div>
        </div>
        <div className="results-card success">
          <div className="label">Files modified</div>
          <div className="value">{result.files_modified}</div>
        </div>
        <div className={`results-card ${errors.length ? "error" : ""}`}>
          <div className="label">Total changes</div>
          <div className="value">{result.total_changes}</div>
        </div>
      </div>
      {errors.length > 0 && (
        <div className="error-list">
          <h3>Errors ({errors.length})</h3>
          <ul>
            {errors.map((e, i) => (
              <li key={i}>
                <strong>{e.file}</strong>
                {": "}
                {e.error}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
