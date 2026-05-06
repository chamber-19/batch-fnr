import { useRef, type ChangeEvent } from "react";
import type { FnrPair } from "../types";

interface Props {
  pairs: FnrPair[];
  onChange: (pairs: FnrPair[]) => void;
}

const blank = (): FnrPair => ({
  find: "",
  replace: "",
  case_sensitive: false,
  use_regex: false,
});

export function PairTable({ pairs, onChange }: Props) {
  const fileInput = useRef<HTMLInputElement | null>(null);

  const update = (idx: number, patch: Partial<FnrPair>) => {
    const next = pairs.map((p, i) => (i === idx ? { ...p, ...patch } : p));
    onChange(next);
  };

  const remove = (idx: number) => {
    onChange(pairs.filter((_, i) => i !== idx));
  };

  const add = () => onChange([...pairs, blank()]);

  const importCsv = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const parsed = parseCsv(text);
    if (parsed.length) onChange([...pairs, ...parsed]);
    // Reset so importing the same file twice still fires onChange.
    e.target.value = "";
  };

  return (
    <div className="panel right">
      <div className="panel-header">
        <h2>Pairs ({pairs.length})</h2>
        <div className="panel-actions">
          <button onClick={() => fileInput.current?.click()}>Import CSV</button>
          <button onClick={add}>Add pair</button>
        </div>
        <input
          ref={fileInput}
          type="file"
          accept=".csv,text/csv"
          onChange={importCsv}
          style={{ display: "none" }}
        />
      </div>
      <div className="panel-body">
        {pairs.length === 0 ? (
          <div className="empty">No find/replace pairs. Click Add pair.</div>
        ) : (
          pairs.map((p, idx) => (
            <div key={idx}>
              <div className="pair-row">
                <input
                  type="text"
                  placeholder="find"
                  value={p.find}
                  onChange={(e) => update(idx, { find: e.target.value })}
                />
                <span className="arrow">→</span>
                <input
                  type="text"
                  placeholder="replace"
                  value={p.replace}
                  onChange={(e) => update(idx, { replace: e.target.value })}
                />
                <button
                  className="danger"
                  onClick={() => remove(idx)}
                  aria-label="Remove pair"
                >
                  ×
                </button>
              </div>
              <div className="pair-toggles">
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={p.case_sensitive}
                    onChange={(e) =>
                      update(idx, { case_sensitive: e.target.checked })
                    }
                  />
                  case sensitive
                </label>
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={p.use_regex}
                    onChange={(e) =>
                      update(idx, { use_regex: e.target.checked })
                    }
                  />
                  regex
                </label>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

/**
 * Parse a CSV in the simple `find,replace` format. Supports double-quoted
 * fields with embedded commas and escaped quotes (`""`). Blank lines and
 * lines without a comma are skipped.
 */
function parseCsv(text: string): FnrPair[] {
  const out: FnrPair[] = [];
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    const cells = parseCsvLine(line);
    if (cells.length < 2) continue;
    const [find, replace] = cells;
    if (!find) continue;
    out.push({
      find,
      replace: replace ?? "",
      case_sensitive: false,
      use_regex: false,
    });
  }
  return out;
}

function parseCsvLine(line: string): string[] {
  const cells: string[] = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          cur += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        cur += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      cells.push(cur);
      cur = "";
    } else {
      cur += ch;
    }
  }
  cells.push(cur);
  return cells;
}
