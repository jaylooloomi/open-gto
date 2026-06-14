import { comboWeight, TOTAL_COMBOS } from "./combos";

// Types mirroring the /preflop response.
export type ActionFreq = Record<string, number>; // action -> frequency
export type NodeChart = Record<string, ActionFreq>; // hand -> action -> frequency

export interface PreNode {
  path: string;
  player: number | null; // 0 = SB, 1 = BB, null = terminal
  is_terminal: boolean;
  kind: string | null;
  actions: string[];
  contrib: number[];
  children: Record<string, string>; // action -> child path
  chart?: NodeChart;
}

export interface PreflopResult {
  stack_bb: number;
  sb_ev: number;
  root: string;
  nodes: Record<string, PreNode>;
}

// Fixed colour per action (the master-plan rule: each action has its own colour,
// not just red/blue) so multi-size trees stay readable.
export const ACTION_COLOR: Record<string, string> = {
  fold: "#33414f",
  check: "#1d9e75",
  limp: "#1d9e75",
  call: "#3b9c4f",
  raise: "#d99a2b",
  "3bet": "#e07b3c",
  "4bet": "#d85a30",
  "5bet": "#c0452f",
  allin: "#e4564a",
};

export const ACTION_ZH: Record<string, string> = {
  fold: "蓋牌",
  check: "過牌",
  limp: "跛入",
  call: "跟注",
  raise: "加注",
  "3bet": "3bet 再加注",
  "4bet": "4bet",
  "5bet": "5bet",
  allin: "全下",
};

export const POSITION_ZH = ["小盲 SB", "大盲 BB"];

/** The highest-frequency action in a per-hand row. */
export function topAction(row: ActionFreq): string {
  let best = "";
  let bestFreq = -1;
  for (const [action, freq] of Object.entries(row)) {
    if (freq > bestFreq) {
      bestFreq = freq;
      best = action;
    }
  }
  return best;
}

/** Combo-weighted frequency per action across a node's chart. */
export function aggregate(chart: NodeChart, actions: string[]): Record<string, number> {
  const totals: Record<string, number> = {};
  for (const a of actions) totals[a] = 0;
  for (const [hand, row] of Object.entries(chart)) {
    const w = comboWeight(hand);
    for (const a of actions) totals[a] += (row[a] ?? 0) * w;
  }
  for (const a of actions) totals[a] = Math.round((totals[a] / TOTAL_COMBOS) * 100);
  return totals;
}
