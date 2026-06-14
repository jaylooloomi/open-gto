import type { Chart } from "./hands";

// Number of card combinations per 169-class: pocket pair = 6, suited = 4,
// offsuit = 12. They sum to C(52,2) = 1326.
export const TOTAL_COMBOS = 1326;

export function comboWeight(label: string): number {
  if (label.length === 2) return 6; // pocket pair
  return label.endsWith("s") ? 4 : 12;
}

export interface Aggregate {
  actionCombos: number; // combos taking the aggressive action (jam/call)
  foldCombos: number;
  actionPct: number; // 0..100, combo-weighted
}

/** Combo-weighted aggregate of a chart's aggressive-action frequency. */
export function aggregate(chart: Chart): Aggregate {
  let actionCombos = 0;
  for (const [label, freq] of Object.entries(chart)) {
    actionCombos += freq * comboWeight(label);
  }
  const pct = (actionCombos / TOTAL_COMBOS) * 100;
  return {
    actionCombos: Math.round(actionCombos),
    foldCombos: Math.round(TOTAL_COMBOS - actionCombos),
    actionPct: Math.round(pct),
  };
}
