import { useCallback, useEffect, useRef, useState } from "react";
import { FreqBar } from "./FreqBar";
import { HandPicker } from "./HandPicker";
import { RangeGrid } from "./RangeGrid";
import { solve, type SolveResult } from "./api";
import {
  effectiveBb,
  POSITION_CONTEXT,
  viewForPosition,
  type Position,
} from "./scenario";
import { startTour } from "./tour";
import { verdict } from "./verdict";

const TOUR_FLAG = "open-gto-tour-seen";
const STEPS = ["① 盲注+籌碼", "② 人數", "③ 位置", "④ 手牌", "⑤ GTO 建議"];

export function App() {
  const [smallBlind, setSmallBlind] = useState(0.5);
  const [bigBlind, setBigBlind] = useState(1);
  const [stackChips, setStackChips] = useState(10);
  const [position, setPosition] = useState<Position>("SB");
  const [hand, setHand] = useState("AA");
  const [result, setResult] = useState<SolveResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tourPending = useRef(false);

  const bb = effectiveBb(stackChips, bigBlind);

  const doSolve = useCallback(async (stackBb: number, autoTour = false) => {
    if (stackBb <= 0) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await solve(stackBb));
      if (autoTour) tourPending.current = true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "求解失敗,請確認後端 API 是否啟動。");
    } finally {
      setLoading(false);
    }
  }, []);

  // Re-solve whenever the effective stack (in bb) changes.
  useEffect(() => {
    const firstVisit = !localStorage.getItem(TOUR_FLAG);
    doSolve(bb, firstVisit);
  }, [bb, doSolve]);

  useEffect(() => {
    if (result && tourPending.current) {
      tourPending.current = false;
      localStorage.setItem(TOUR_FLAG, "1");
      const t = setTimeout(startTour, 400);
      return () => clearTimeout(t);
    }
  }, [result]);

  const view = viewForPosition(position);
  const chart = result ? result[view] : {};
  const v = verdict(view, chart[hand] ?? 0);
  const tone =
    v.kind === "do" ? "#e4564a" : v.kind === "fold" ? "#33414f" : "#c98a2b";

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
          單挑德州撲克 · 照步驟設定牌局,直接看到 GTO 最佳打法。不會打也能用。
        </p>
      </header>

      <ol className="stepper">
        {STEPS.map((s, i) => (
          <li key={s} className={i === STEPS.length - 1 ? "goal" : ""}>
            {s}
          </li>
        ))}
      </ol>

      <div className="flow">
        <section className="setup">
          <h2 className="panel-title">設定情境</h2>

          <div className="field" data-tour="blinds">
            <label>① 盲注面額 <small>(換算用,不影響 GTO)</small></label>
            <div className="row">
              <span className="cap">小盲</span>
              <input type="number" min={0} step={0.5} value={smallBlind}
                onChange={(e) => setSmallBlind(Number(e.target.value))} />
              <span className="cap">大盲</span>
              <input type="number" min={0.5} step={0.5} value={bigBlind}
                onChange={(e) => setBigBlind(Number(e.target.value))} />
            </div>
          </div>

          <div className="field" data-tour="stack">
            <label>② 你的有效籌碼 <span className="tag ok">GTO 真正輸入</span></label>
            <div className="row">
              <input type="number" min={0} step={1} value={stackChips}
                onChange={(e) => setStackChips(Number(e.target.value))} />
              <span className="arrow">→</span>
              <strong>{bb} bb</strong>
            </div>
          </div>

          <div className="field" data-tour="players">
            <label>③ 牌桌人數</label>
            <div className="row">
              <button className="opt active">單挑 HU</button>
              <button className="opt locked" disabled>6Max 🔒</button>
              <button className="opt locked" disabled>9Max 🔒</button>
            </div>
          </div>

          <div className="field" data-tour="position">
            <label>④ 你的位置</label>
            <div className="row">
              <button className={position === "SB" ? "opt active" : "opt"}
                onClick={() => setPosition("SB")}>小盲 SB</button>
              <button className={position === "BB" ? "opt active" : "opt"}
                onClick={() => setPosition("BB")}>大盲 BB</button>
            </div>
            <p className="ctx">{POSITION_CONTEXT[position]}</p>
          </div>

          <div className="field" data-tour="hand">
            <label>⑤ 你的手牌</label>
            <HandPicker selected={hand} onSelect={setHand} />
          </div>
        </section>

        <section className="result" data-tour="verdict">
          <h2 className="panel-title">GTO 建議{loading && " · 計算中…"}</h2>
          {error ? (
            <p className="error">⚠ {error}</p>
          ) : (
            <>
              <div className="verdict" style={{ background: tone }}>
                <div className="verdict-head">{v.headline}</div>
                <div className="verdict-detail">{v.detail}</div>
              </div>
              <ul className="result-meta">
                <li>有效籌碼:<b>{bb} bb</b>(實際 {stackChips} 元)</li>
                <li>{position === "SB" ? "推注即全下" : "跟注即全下對手"}:<b>{stackChips} 元</b></li>
                <li>可剝削度:<b>{result ? result.exploitability.toExponential(2) : "—"}</b> bb(越接近 0 越完美)</li>
              </ul>
            </>
          )}
        </section>
      </div>

      {result && (
        <>
          <FreqBar view={view} chart={chart} />

          <div className="range-head">
            <span>完整範圍表 · 紅=進攻、藍=蓋牌,點任一格更新上方建議</span>
          </div>
          <RangeGrid chart={chart} selected={hand} onSelect={setHand} />

          <details className="glossary">
            <summary>名詞小辭典(新手點開)</summary>
            <ul>
              <li><b>推注 / 全下 (Jam)</b>:把所有籌碼一次推進去。</li>
              <li><b>蓋牌 (Fold)</b>:放棄這手牌,不跟。</li>
              <li><b>小盲 / 大盲 (SB / BB)</b>:單挑的兩個位置,開局各自要先下的強制注。</li>
              <li><b>bb(大盲)</b>:籌碼的計量單位,例如「10bb」= 10 個大盲的籌碼。</li>
              <li><b>有效籌碼</b>:雙方之中較少的那份籌碼 —— 真正能輸贏的上限。</li>
              <li><b>GTO</b>:博弈論最優策略 —— 對手怎麼打都無法占你便宜的打法。</li>
            </ul>
          </details>
        </>
      )}
    </div>
  );
}
