import { aggregate } from "./combos";
import type { Chart } from "./hands";
import type { View } from "./verdict";

/** Overview projection: combo-weighted aggressive-action vs fold proportions. */
export function FreqBar({ view, chart }: { view: View; chart: Chart }) {
  const agg = aggregate(chart);
  const actionLabel = view === "sb_jam" ? "全下" : "跟注";

  return (
    <div data-tour="freq" className="freqbar">
      <div className="freqbar-track">
        <div className="seg jam" style={{ width: `${agg.actionPct}%` }} />
        <div className="seg fold" style={{ width: `${100 - agg.actionPct}%` }} />
      </div>
      <div className="freqbar-legend">
        <span>
          <i style={{ background: "#e4564a" }} /> {actionLabel} {agg.actionPct}%
          <small> · {agg.actionCombos} 組合</small>
        </span>
        <span>
          <i style={{ background: "#33414f" }} /> 蓋牌 {100 - agg.actionPct}%
          <small> · {agg.foldCombos} 組合</small>
        </span>
      </div>
    </div>
  );
}
