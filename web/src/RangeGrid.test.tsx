import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RangeGrid } from "./RangeGrid";
import type { Chart } from "./hands";

function makeChart(overrides: Chart = {}): Chart {
  // A uniform 0-frequency chart with optional per-hand overrides.
  const chart: Chart = {};
  const ranks = "AKQJT98765432".split("");
  for (let r = 0; r < 13; r++) {
    for (let c = 0; c < 13; c++) {
      const label =
        r === c
          ? ranks[r] + ranks[r]
          : r < c
            ? ranks[r] + ranks[c] + "s"
            : ranks[c] + ranks[r] + "o";
      chart[label] = 0;
    }
  }
  return { ...chart, ...overrides };
}

describe("RangeGrid", () => {
  it("renders all 169 cells", () => {
    render(<RangeGrid chart={makeChart()} />);
    expect(screen.getAllByRole("gridcell")).toHaveLength(169);
  });

  it("reflects a hand's jam frequency", () => {
    render(<RangeGrid chart={makeChart({ AA: 1 })} />);
    const aa = document.querySelector('[data-label="AA"]') as HTMLElement;
    expect(aa).toBeInTheDocument();
    expect(aa.dataset.freq).toBe("1");
    expect(aa.textContent).toContain("100");
  });

  it("places pairs on the diagonal and suited above it", () => {
    render(<RangeGrid chart={makeChart()} />);
    expect(document.querySelector('[data-label="AKs"]')).toBeInTheDocument();
    expect(document.querySelector('[data-label="AKo"]')).toBeInTheDocument();
    expect(document.querySelector('[data-label="22"]')).toBeInTheDocument();
  });
});
