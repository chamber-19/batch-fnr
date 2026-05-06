interface Props {
  /** Number of files completed so far. */
  processed: number;
  /** Total files in the batch. */
  total: number;
  /** Current file being processed, if any. */
  current?: string;
}

function fileName(p: string): string {
  const i = Math.max(p.lastIndexOf("/"), p.lastIndexOf("\\"));
  return i >= 0 ? p.slice(i + 1) : p;
}

export function ProgressBar({ processed, total, current }: Props) {
  const pct = total === 0 ? 0 : Math.min(100, (processed / total) * 100);
  return (
    <div>
      <div className="progress-bar" role="progressbar" aria-valuenow={pct}>
        <div className="fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="progress-meta">
        <span className="mono">{current ? fileName(current) : "…"}</span>
        <span className="mono">
          {processed} / {total}
        </span>
      </div>
    </div>
  );
}
