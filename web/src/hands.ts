// Canonical 13x13 starting-hand grid. Rows and columns run A,K,Q,...,2.
// Suited hands are above the diagonal, offsuit below, pocket pairs on it.
// Labels match the engine's HANDS_169 (higher rank first, e.g. "AKs", "AKo").

export const RANKS = "AKQJT98765432".split("");

export function cellLabel(row: number, col: number): string {
  if (row === col) return RANKS[row] + RANKS[row];
  if (row < col) return RANKS[row] + RANKS[col] + "s"; // suited (upper-right)
  return RANKS[col] + RANKS[row] + "o"; // offsuit (lower-left)
}

export type Chart = Record<string, number>;
