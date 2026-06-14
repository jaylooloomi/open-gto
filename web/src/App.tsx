import { useState } from "react";
import { RangeGrid } from "./RangeGrid";
import { solve, type SolveResult } from "./api";

type View = "sb_jam" | "bb_call";

export function App() {
  const [stack, setStack] = useState(10);
  const [view, setView] = useState<View>("sb_jam");
  const [result, setResult] = useState<SolveResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSolve() {
    setLoading(true);
    setError(null);
    try {
      setResult(await solve(stack));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to solve");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>open-gto</h1>
        <p className="sub">Heads-up NLHE preflop push/fold — GTO solver</p>
      </header>

      <div className="controls">
        <label>
          Effective stack: <strong>{stack} bb</strong>
          <input
            type="range"
            min={1}
            max={25}
            step={1}
            value={stack}
            onChange={(e) => setStack(Number(e.target.value))}
          />
        </label>
        <button onClick={onSolve} disabled={loading}>
          {loading ? "Solving…" : "Solve"}
        </button>
      </div>

      {error && <p className="error">⚠ {error}</p>}

      {result && (
        <>
          <div className="tabs">
            <button
              className={view === "sb_jam" ? "active" : ""}
              onClick={() => setView("sb_jam")}
            >
              SB jam range
            </button>
            <button
              className={view === "bb_call" ? "active" : ""}
              onClick={() => setView("bb_call")}
            >
              BB call vs jam
            </button>
          </div>
          <RangeGrid chart={result[view]} />
          <p className="meta">
            Exploitability: {result.exploitability.toExponential(2)} bb · {stack}bb
          </p>
          <div className="legend">
            <span><i style={{ background: "#e4564a" }} /> {view === "sb_jam" ? "Jam" : "Call"}</span>
            <span><i style={{ background: "#33414f" }} /> Fold</span>
          </div>
        </>
      )}

      {!result && !error && <p className="hint">Pick a stack depth and hit Solve.</p>}
    </div>
  );
}
