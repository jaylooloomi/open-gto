import { describe, expect, it } from "vitest";
import { classFromCards } from "./hands";
import { aggregate, comboWeight, TOTAL_COMBOS } from "./combos";
import { verdict } from "./verdict";

describe("classFromCards", () => {
  it("maps a pocket pair", () => {
    expect(classFromCards("A", "s", "A", "h")).toBe("AA");
  });
  it("maps suited with higher rank first", () => {
    expect(classFromCards("K", "s", "A", "s")).toBe("AKs");
    expect(classFromCards("A", "d", "K", "d")).toBe("AKs");
  });
  it("maps offsuit", () => {
    expect(classFromCards("A", "s", "K", "h")).toBe("AKo");
  });
  it("orders ranks regardless of input order", () => {
    expect(classFromCards("5", "c", "T", "c")).toBe("T5s");
    expect(classFromCards("2", "h", "7", "s")).toBe("72o");
  });
});

describe("comboWeight", () => {
  it("weights pairs/suited/offsuit", () => {
    expect(comboWeight("AA")).toBe(6);
    expect(comboWeight("AKs")).toBe(4);
    expect(comboWeight("AKo")).toBe(12);
  });
  it("all 169 classes sum to 1326", () => {
    const ranks = "AKQJT98765432".split("");
    let total = 0;
    for (let r = 0; r < 13; r++)
      for (let c = 0; c < 13; c++) {
        const label =
          r === c
            ? ranks[r] + ranks[r]
            : r < c
              ? ranks[r] + ranks[c] + "s"
              : ranks[c] + ranks[r] + "o";
        total += comboWeight(label);
      }
    expect(total).toBe(TOTAL_COMBOS);
  });
});

describe("aggregate", () => {
  it("computes combo-weighted action percentage", () => {
    // Only AA jams (6 combos out of 1326).
    const agg = aggregate({ AA: 1, KK: 0, AKs: 0 });
    expect(agg.actionCombos).toBe(6);
    expect(agg.foldCombos).toBe(1320);
    expect(agg.actionPct).toBe(0); // 6/1326 rounds to 0%
  });
});

describe("verdict", () => {
  it("recommends jamming a pure-jam hand", () => {
    const v = verdict("sb_jam", 1);
    expect(v.kind).toBe("do");
    expect(v.headline).toContain("Jam");
  });
  it("recommends folding a pure-fold hand", () => {
    const v = verdict("sb_jam", 0);
    expect(v.kind).toBe("fold");
    expect(v.headline).toContain("Fold");
  });
  it("flags a mixed hand with its percentage", () => {
    const v = verdict("sb_jam", 0.37);
    expect(v.kind).toBe("mix");
    expect(v.pct).toBe(37);
  });
  it("uses call wording for the BB view", () => {
    expect(verdict("bb_call", 1).headline).toContain("Call");
  });
});
