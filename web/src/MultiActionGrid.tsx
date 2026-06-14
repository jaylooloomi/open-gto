import { ACTION_COLOR, type NodeChart } from "./preflop";
import { RANKS, cellLabel } from "./hands";

interface Props {
  chart: NodeChart;
  actions: string[];
  selected?: string;
  onSelect?: (label: string) => void;
}

function cellBackground(row: Record<string, number>, actions: string[]): string {
  // Stacked bottom-up fill, one fixed colour per action.
  const stops: string[] = [];
  let acc = 0;
  for (const a of actions) {
    const pct = (row[a] ?? 0) * 100;
    if (pct <= 0) continue;
    const color = ACTION_COLOR[a] ?? "#888";
    stops.push(`${color} ${acc}%`, `${color} ${acc + pct}%`);
    acc += pct;
  }
  if (acc < 100) stops.push(`#33414f ${acc}%`, `#33414f 100%`);
  return `linear-gradient(to top, ${stops.join(", ")})`;
}

/** 13x13 grid coloured by each hand's full action distribution at a node. */
export function MultiActionGrid({ chart, actions, selected, onSelect }: Props) {
  return (
    <div data-tour="grid" className="grid" role="grid" aria-label="range grid">
      {RANKS.map((_, row) =>
        RANKS.map((__, col) => {
          const label = cellLabel(row, col);
          const dist = chart[label] ?? {};
          const isSel = selected === label;
          return (
            <button
              key={label}
              type="button"
              className={isSel ? "cell sel" : "cell"}
              role="gridcell"
              aria-pressed={isSel}
              data-label={label}
              style={{ background: cellBackground(dist, actions) }}
              title={label}
              onClick={() => onSelect?.(label)}
            >
              <span className="lbl">{label}</span>
            </button>
          );
        }),
      )}
    </div>
  );
}
