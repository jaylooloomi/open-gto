import { useCallback, useEffect, useRef, useState } from "react";
import { FreqBar } from "./FreqBar";
import { HandLookup } from "./HandLookup";
import { RangeGrid } from "./RangeGrid";
import { solve, type SolveResult } from "./api";
import { startTour } from "./tour";
import type { View } from "./verdict";

const TOUR_FLAG = "open-gto-tour-seen";

export function App() {
  const [stack, setStack] = useState(10);
  const [view, setView] = useState<View>("sb_jam");
  const [selected, setSelected] = useState("AA");
  const [result, setResult] = useState<SolveResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tourPending = useRef(false);

  const onSolve = useCallback(async (bb: number, autoTour = false) => {
    setLoading(true);
    setError(null);
    try {
      setResult(await solve(bb));
      if (autoTour) tourPending.current = true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "求解失敗,請確認後端 API 是否啟動。");
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-solve a 10bb example on first load so the page is never empty.
  useEffect(() => {
    const firstVisit = !localStorage.getItem(TOUR_FLAG);
    onSolve(10, firstVisit);
  }, [onSolve]);

  // Once the first result is painted, launch the tour for new visitors.
  useEffect(() => {
    if (result && tourPending.current) {
      tourPending.current = false;
      localStorage.setItem(TOUR_FLAG, "1");
      const t = setTimeout(startTour, 400);
      return () => clearTimeout(t);
    }
  }, [result]);

  const chart = result ? result[view] : {};

  return (
    <div className="app">
      <header data-tour="intro">
        <div className="title-row">
          <h1>open-gto</h1>
          <button className="ghost" onClick={startTour}>
            <span aria-hidden="true">？</span> 怎麼用
          </button>
        </div>
        <p className="sub">
          單挑德州撲克 · 教你每手牌的 GTO 最佳打法。不會打也能用 —— 選牌、看建議就好。
        </p>
      </header>

      <div className="controls">
        <label data-tour="stack">
          籌碼深度:<strong>{stack} bb</strong>
          <input
            type="range"
            min={1}
            max={25}
            step={1}
            value={stack}
            onChange={(e) => setStack(Number(e.target.value))}
          />
        </label>
        <button data-tour="solve" onClick={() => onSolve(stack)} disabled={loading}>
          {loading ? "計算中…" : "重新計算"}
        </button>
      </div>

      {error && <p className="error">⚠ {error}</p>}

      {result && (
        <>
          <HandLookup
            view={view}
            chart={chart}
            selected={selected}
            onSelect={setSelected}
          />

          <FreqBar view={view} chart={chart} />

          <div data-tour="view" className="tabs">
            <button
              className={view === "sb_jam" ? "active" : ""}
              onClick={() => setView("sb_jam")}
            >
              小盲:該推哪些牌
            </button>
            <button
              className={view === "bb_call" ? "active" : ""}
              onClick={() => setView("bb_call")}
            >
              大盲:面對全下該跟哪些
            </button>
          </div>

          <RangeGrid chart={chart} selected={selected} onSelect={setSelected} />

          <p className="meta">
            紅=進攻、藍=蓋牌、格內數字=進攻機率 · 可剝削度 {result.exploitability.toExponential(2)} bb(越接近 0 越完美)
          </p>

          <details className="glossary">
            <summary>名詞小辭典(新手點開)</summary>
            <ul>
              <li><b>推注 / 全下 (Jam)</b>:把所有籌碼一次推進去。</li>
              <li><b>蓋牌 (Fold)</b>:放棄這手牌,不跟。</li>
              <li><b>小盲 / 大盲 (SB / BB)</b>:單挑時兩個位置,開局各自要先下的強制注。</li>
              <li><b>bb(大盲)</b>:籌碼的計量單位,例如「10bb」= 10 個大盲的籌碼。</li>
              <li><b>GTO</b>:博弈論最優策略 —— 對手怎麼打都無法占你便宜的打法。</li>
            </ul>
          </details>
        </>
      )}
    </div>
  );
}
