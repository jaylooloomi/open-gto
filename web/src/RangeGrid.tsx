import type { Chart } from "./hands";
import { RANKS, cellLabel } from "./hands";

const JAM = "#e4564a"; // red  — action taken
const FOLD = "#33414f"; // slate — folded

export interface RangeGridProps {
  chart: Chart;
  selected?: string;
  onSelect?: (label: string) => void;
}

/** A 13x13 starting-hand grid; each cell is filled bottom-up by its frequency. */
export function RangeGrid({ chart, selected, onSelect }: RangeGridProps) {
  return (
    <div data-tour="grid" className="grid" role="grid" aria-label="range grid">
      {RANKS.map((_, row) =>
        RANKS.map((__, col) => {
          const label = cellLabel(row, col);
          const freq = chart[label] ?? 0;
          const pct = Math.round(freq * 100);
          const bg = `linear-gradient(to top, ${JAM} ${pct}%, ${FOLD} ${pct}%)`;
          const isSel = selected === label;
          return (
            <button
              key={label}
              type="button"
              className={isSel ? "cell sel" : "cell"}
              role="gridcell"
              aria-pressed={isSel}
              data-label={label}
              data-freq={freq}
              style={{ background: bg }}
              title={`${label}: ${pct}%`}
              onClick={() => onSelect?.(label)}
            >
              <span className="lbl">{label}</span>
              <span className="pct">{pct}</span>
            </button>
          );
        }),
      )}
    </div>
  );
}
