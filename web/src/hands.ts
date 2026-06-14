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

// Suits for the beginner card picker (display symbol + key).
export const SUITS = [
  { key: "s", symbol: "♠", name: "黑桃" },
  { key: "h", symbol: "♥", name: "紅心" },
  { key: "d", symbol: "♦", name: "方塊" },
  { key: "c", symbol: "♣", name: "梅花" },
] as const;

/** Map two concrete cards to their 169-class label (e.g. A♠ K♠ -> "AKs"). */
export function classFromCards(
  rank1: string,
  suit1: string,
  rank2: string,
  suit2: string,
): string {
  if (rank1 === rank2) return rank1 + rank2; // pocket pair
  // Higher rank first (lower index in RANKS == higher rank).
  const [hi, lo] =
    RANKS.indexOf(rank1) < RANKS.indexOf(rank2)
      ? [rank1, rank2]
      : [rank2, rank1];
  return hi + lo + (suit1 === suit2 ? "s" : "o");
}

export interface TwoCards {
  rank1: string;
  suit1: string;
  rank2: string;
  suit2: string;
}

/** A representative concrete pair of cards for a 169-class label. */
export function representativeCards(label: string): TwoCards {
  if (label.length === 2) {
    return { rank1: label[0], suit1: "s", rank2: label[1], suit2: "h" };
  }
  const suited = label.endsWith("s");
  return {
    rank1: label[0],
    suit1: "s",
    rank2: label[1],
    suit2: suited ? "s" : "h",
  };
}
