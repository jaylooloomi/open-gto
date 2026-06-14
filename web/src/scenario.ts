// Scenario inputs that map to the solver. For GTO only the *effective stack in
// big blinds* matters; the blind face value is used purely to convert chips
// <-> bb for display at a real table.

export type Position = "SB" | "BB";

/** Effective stack in big blinds, from a chip stack and the big-blind size. */
export function effectiveBb(stackChips: number, bigBlind: number): number {
  if (bigBlind <= 0 || stackChips <= 0) return 0;
  return Math.max(1, Math.round(stackChips / bigBlind));
}

/** Which solved chart a position reads: SB jams, BB calls a jam. */
export function viewForPosition(pos: Position): "sb_jam" | "bb_call" {
  return pos === "SB" ? "sb_jam" : "bb_call";
}

export const POSITION_CONTEXT: Record<Position, string> = {
  SB: "輪到你先行動(推注或蓋牌)",
  BB: "小盲已全下,輪到你跟注或蓋牌",
};
