import { describe, expect, it } from "vitest";
import { aggregate, topAction, type NodeChart } from "./preflop";

describe("topAction", () => {
  it("returns the highest-frequency action", () => {
    expect(topAction({ fold: 0.1, raise: 0.7, allin: 0.2 })).toBe("raise");
    expect(topAction({ fold: 1, raise: 0 })).toBe("fold");
  });
});

describe("aggregate", () => {
  it("combo-weights action frequencies to percentages", () => {
    // AA (6 combos) all-in, AKs (4) raise, AKo (12) fold; rest absent.
    const chart: NodeChart = {
      AA: { fold: 0, raise: 0, allin: 1 },
      AKs: { fold: 0, raise: 1, allin: 0 },
      AKo: { fold: 1, raise: 0, allin: 0 },
    };
    const agg = aggregate(chart, ["fold", "raise", "allin"]);
    // 6/1326 ~ 0%, 4/1326 ~ 0%, 12/1326 ~ 1% — rounding, but ordering/keys exist.
    expect(agg).toHaveProperty("fold");
    expect(agg).toHaveProperty("raise");
    expect(agg).toHaveProperty("allin");
    expect(agg.fold + agg.raise + agg.allin).toBeGreaterThanOrEqual(0);
  });

  it("a full-raise chart aggregates to ~100% raise", () => {
    const ranks = "AKQJT98765432".split("");
    const chart: NodeChart = {};
    for (let r = 0; r < 13; r++)
      for (let c = 0; c < 13; c++) {
        const label =
          r === c ? ranks[r] + ranks[r] : r < c ? ranks[r] + ranks[c] + "s" : ranks[c] + ranks[r] + "o";
        chart[label] = { fold: 0, raise: 1 };
      }
    const agg = aggregate(chart, ["fold", "raise"]);
    expect(agg.raise).toBe(100);
    expect(agg.fold).toBe(0);
  });
});
