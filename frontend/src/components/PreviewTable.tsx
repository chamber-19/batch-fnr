import { useMemo } from "react";
import type { MatchRow } from "../types";

interface Props {
  matches: MatchRow[];
  /** Set of `${file}|${index}` ids that the user has unchecked. */
  excluded: Set<string>;
  onToggle: (id: string) => void;
}

function fileName(p: string): string {
  const i = Math.max(p.lastIndexOf("/"), p.lastIndexOf("\\"));
  return i >= 0 ? p.slice(i + 1) : p;
}

export function PreviewTable({ matches, excluded, onToggle }: Props) {
  const grouped = useMemo(() => {
    const out = new Map<string, { match: MatchRow; id: string }[]>();
    matches.forEach((m, i) => {
      const id = `${m.file}|${i}`;
      const arr = out.get(m.file) ?? [];
      arr.push({ match: m, id });
      out.set(m.file, arr);
    });
    return out;
  }, [matches]);

  if (matches.length === 0) {
    return <div className="empty">No matches found.</div>;
  }

  return (
    <div>
      {Array.from(grouped.entries()).map(([file, rows]) => (
        <div key={file} className="match-group">
          <div className="match-group-header">
            <span title={file}>{fileName(file)}</span>
            <span className="count">
              {rows.length} match{rows.length === 1 ? "" : "es"}
            </span>
          </div>
          <table>
            <thead>
              <tr>
                <th style={{ width: 28 }} />
                <th style={{ width: 120 }}>Type</th>
                <th style={{ width: 120 }}>Layer</th>
                <th style={{ width: 100 }}>Space</th>
                <th>Current → Proposed</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ match, id }) => {
                const checked = !excluded.has(id);
                return (
                  <tr key={id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => onToggle(id)}
                        aria-label="Include this match"
                      />
                    </td>
                    <td className="mono">{match.entity_type}</td>
                    <td className="mono dim">{match.layer || "—"}</td>
                    <td className="mono dim">{match.space}</td>
                    <td className="mono">
                      <span className="dim">{match.current_value}</span>
                      <span className="dim"> → </span>
                      <span className="success-text">
                        {match.proposed_value}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
