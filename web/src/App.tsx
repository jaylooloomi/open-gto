import { useCallback, useEffect, useRef, useState } from "react";
import { HandPicker } from "./HandPicker";
import { MultiActionGrid } from "./MultiActionGrid";
import { PositionTree } from "./PositionTree";
import { solvePreflop } from "./api";
import { effectiveBb, type Position } from "./scenario";
import {
  ACTION_COLOR,
  ACTION_ZH,
  aggregate,
  POSITION_ZH,
  topAction,
  type PreflopResult,
} from "./preflop";
import { startTour } from "./tour";

const TOUR_FLAG = "open-gto-tour-seen-v2";
const STEPS = ["① 盲注+籌碼", "② 人數", "③ 位置", "④ 手牌", "⑤ GTO 建議"];

function defaultPath(position: Position, result: PreflopResult): string {
  if (position === "SB") return result.root; // SB first-in
  for (const p of ["raise", "allin", "limp"]) {
    const n = result.nodes[p];
    if (n && n.player === 1 && !n.is_terminal) return p;
  }
  return result.root;
}

export function App() {
  const [smallBlind, setSmallBlind] = useState(0.5);
  const [bigBlind, setBigBlind] = useState(1);
  const [stackChips, setStackChips] = useState(50);
  const [position, setPosition] = useState<Position>("SB");
  const [hand, setHand] = useState("AA");
  const [path, setPath] = useState("");
  const [result, setResult] = useState<PreflopResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tourPending = useRef(false);

  const bb = effectiveBb(stackChips, bigBlind);

  const doSolve = useCallback(async (stackBb: number, autoTour = false) => {
    if (stackBb <= 0) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await solvePreflop(stackBb));
      if (autoTour) tourPending.current = true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "求解失敗,請確認後端 API 是否啟動。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const firstVisit = !localStorage.getItem(TOUR_FLAG);
    doSolve(bb, firstVisit);
  }, [bb, doSolve]);

  // Reset the viewed node when the result or the chosen seat changes.
  useEffect(() => {
    if (result) setPath(defaultPath(position, result));
  }, [result, position]);

  useEffect(() => {
    if (result && tourPending.current) {
      tourPending.current = false;
      localStorage.setItem(TOUR_FLAG, "1");
      const t = setTimeout(startTour, 400);
      return () => clearTimeout(t);
    }
  }, [result]);

  const node = result ? result.nodes[path] : null;
  const chart = node && !node.is_terminal ? node.chart ?? {} : {};
  const row = chart[hand] ?? {};
  const best = node && !node.is_terminal ? topAction(row) : "";
  const bestPct = Math.round((row[best] ?? 0) * 100);
  const tone = best === "fold" ? "#33414f" : ACTION_COLOR[best] ?? "#c98a2b";
  const freqs = node && !node.is_terminal ? aggregate(chart, node.actions) : {};

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
          單挑德州撲克 preflop · 設定牌局,看每手牌的 GTO 建議。不會打也能用。
        </p>
      </header>

      <ol className="stepper">
        {STEPS.map((s, i) => (
          <li key={s} className={i === STEPS.length - 1 ? "goal" : ""}>{s}</li>
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
            </div>
          </div>
          <div className="field" data-tour="position">
            <label>④ 你的位置</label>
            <div className="row">
              <button className={position === "SB" ? "opt active" : "opt"}
                onClick={() => setPosition("SB")}>小盲 SB(先動)</button>
              <button className={position === "BB" ? "opt active" : "opt"}
                onClick={() => setPosition("BB")}>大盲 BB(面對開池)</button>
            </div>
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
          ) : node && node.is_terminal ? (
            <p className="hint">這條線已結束({node.kind})。點上方「開局」回到決策點。</p>
          ) : node ? (
            <>
              <div className="verdict" style={{ background: tone }}>
                <div className="verdict-head">GTO 建議:{ACTION_ZH[best] ?? best} {bestPct}%</div>
                <div className="verdict-detail">
                  此節點輪到 {POSITION_ZH[node.player ?? 0]};你的 {hand} 最高頻打法是「{ACTION_ZH[best] ?? best}」。
                </div>
              </div>
              <ul className="result-meta">
                <li>有效籌碼:<b>{bb} bb</b></li>
                <li>可剝削度(SB EV):<b>{result ? result.sb_ev.toFixed(3) : "—"}</b> bb</li>
                <li className="note">註:看翻牌的線用權益實現近似(非權威 GTO);全下/蓋牌線為精確。</li>
              </ul>
            </>
          ) : (
            <p className="hint">設定後會自動計算。</p>
          )}
        </section>
      </div>

      {result && node && !node.is_terminal && (
        <>
          <PositionTree result={result} path={path} onNavigate={setPath} />

          <div data-tour="freq" className="freqbar">
            <div className="freqbar-track">
              {node.actions.map((a) => (
                <div key={a} style={{ width: `${freqs[a] ?? 0}%`, background: ACTION_COLOR[a] ?? "#888" }} />
              ))}
            </div>
            <div className="freqbar-legend">
              {node.actions.map((a) => (
                <span key={a}>
                  <i style={{ background: ACTION_COLOR[a] ?? "#888" }} /> {ACTION_ZH[a] ?? a} {freqs[a] ?? 0}%
                </span>
              ))}
            </div>
          </div>

          <div className="range-head">完整範圍表 · 點任一格更新上方建議</div>
          <MultiActionGrid chart={chart} actions={node.actions} selected={hand} onSelect={setHand} />
        </>
      )}

      <details className="glossary">
        <summary>名詞小辭典(新手點開)</summary>
        <ul>
          <li><b>開池 / 加注 (raise)</b>:第一個主動下注加碼。</li>
          <li><b>跛入 (limp)</b>:只跟大盲、不加注地進池。</li>
          <li><b>3bet / 4bet</b>:再加注、再再加注。</li>
          <li><b>全下 (allin)</b>:把所有籌碼一次推進去。</li>
          <li><b>SB / BB</b>:小盲 / 大盲,單挑的兩個位置。</li>
          <li><b>GTO</b>:對手怎麼打都無法占你便宜的博弈論最優策略。</li>
        </ul>
      </details>
    </div>
  );
}
