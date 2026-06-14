# Phase B — HU Preflop with Bet Sizes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Solve heads-up NLHE *preflop* with a real action tree (fold / limp /
raise sizes / 3bet / 4bet / all-in) and show per-node GTO strategies, building
the reusable "game-tree + multiple bet sizes + multi-action coloring" machinery.

**Architecture:** A public **betting tree** (positions/actions) walked by a
**vectorized CFR** that carries a 169-vector range per player and values
terminals with the existing equity matrix. Exact for fold/all-in terminals;
"see-flop" terminals use a documented **equity-realization approximation**
(no postflop modeling yet — that's Phase D). Cross-validated against the
already-trusted generic `CFRSolver` on a tiny tree.

**Tech Stack:** Python + numpy (engine), FastAPI, React + TS (web).

> **Accuracy caveat (surface in UI):** ranges are approximate, not authoritative
> GTO, because postflop EV is modeled as raw equity realization. Exact for
> all-in/fold lines. This is a deliberate, documented MVP simplification.

---

## Decisions locked (2026-06-14, user-confirmed)

- **Multi-action tree + UI machinery is built now** (game-tree navigation,
  per-action fixed coloring, multi-action freq bar). This is reusable for 6Max
  and postflop later.
- **Solving uses a SINGLE open size** (no 2x-vs-3x choice). Rationale: choosing
  between raise *sizes* is fundamentally postflop-driven; without postflop EV the
  solver can't pick sizes meaningfully (it degenerates to "max size with value").
  True multi-size selection is **deferred until after Phase D (postflop)**, when
  it can be answered credibly. The tree/UI already support N sizes, so enabling
  them later is data-only, not a rewrite.
- **Locked sizes (tunable in config):** SB open = 2.5 bb; BB iso-vs-limp = 3.5 bb;
  3bet = 3× the prior raise; 4bet = 2.2× the 3bet; then all-in. Raise cap = 4.
- **Actions:** SB {fold, limp, raise, allin}; BB-vs-limp {check, raise, allin};
  vs-raise {fold, call, 3bet, allin}; vs-3bet {fold, call, 4bet, allin};
  vs-4bet/allin {fold, call}.
- **Stack support:** 10–100 bb; default 50 bb (bet-size lines are meaningful at
  these depths; very short stacks collapse toward push/fold, which Phase A covers).
- **Equity realization:** R = 1.0 (raw) for v1, configurable; refine in Phase D.

---

## File structure

- `engine/preflop/tree.py` — `BettingTree`: public nodes, actions, pot accounting, terminal classification.
- `engine/preflop/solver.py` — `PreflopSolver`: vectorized CFR over the tree with per-player range vectors.
- `engine/preflop/realization.py` — terminal valuation (fold / showdown / see-flop).
- `engine/games/preflop_hu.py` — `PreflopHU(ExtensiveFormGame)`: generic (small) version for cross-validation.
- `api/main.py` — extend `/solve` with `game="preflop_hu"` + node path.
- `web/src/tree.ts`, `web/src/PositionTree.tsx` — action-tree navigation.
- `web/src/RangeGrid.tsx` — multi-action cell coloring.
- Tests: `tests/test_preflop_tree.py`, `tests/test_preflop_solver.py`, `web/src/*.test.ts(x)`.

---

## Task 1: Betting tree model

**Files:** Create `engine/preflop/__init__.py`, `engine/preflop/tree.py`; Test `tests/test_preflop_tree.py`

Action abstraction (v1, configurable): SB ∈ {fold, limp, raise 2.5, allin};
BB-vs-limp ∈ {check, raise 3.5, allin}; vs-raise ∈ {fold, call, 3bet, allin};
vs-3bet ∈ {fold, call, allin}; vs-4bet/allin ∈ {fold, call}. Raise cap = 4.

- [ ] **Step 1: failing test** — build tree for stack=20; assert root is SB decision with the 4 actions; a fold child is terminal "fold"; an allin→call child is terminal "showdown"; a raise→call child is terminal "seeflop"; contributions tracked.

```python
# tests/test_preflop_tree.py
from engine.preflop.tree import build_tree

def test_root_actions_and_terminals():
    root = build_tree(stack_bb=20)
    assert root.player == 0  # SB acts first
    assert set(root.actions) == {"fold", "limp", "raise", "allin"}
    fold = root.child("fold")
    assert fold.is_terminal and fold.kind == "fold" and fold.folder == 0
    show = root.child("allin").child("call")
    assert show.is_terminal and show.kind == "showdown"
    flop = root.child("raise").child("call")
    assert flop.is_terminal and flop.kind == "seeflop"
    assert flop.contrib == (2.5, 2.5)  # both put in 2.5bb
```

- [ ] **Step 2: run, expect fail.** `.\.venv\Scripts\python -m pytest tests/test_preflop_tree.py -v`
- [ ] **Step 3: implement** `Node` (player, actions, children, is_terminal, kind ∈ {fold,showdown,seeflop}, folder, contrib=(sb,bb)) and `build_tree(stack_bb, sizes=...)` that expands the abstraction above with pot/contribution accounting and a raise cap. Full code at execution.
- [ ] **Step 4: run, expect pass.**
- [ ] **Step 5: commit** `feat(preflop): betting tree model`.

## Task 2: Terminal valuation (equity realization)

**Files:** Create `engine/preflop/realization.py`; Test `tests/test_preflop_realization.py`

- [ ] **Step 1: failing test** — fold: folder loses its contribution; showdown: `(2*eq-1)*contrib` per the all-in stake; seeflop (R=1): `value_i = eq*pot - contrib_i` so SB EV with eq=0.5, equal contribs = 0.
```python
from engine.preflop.realization import fold_value, showdown_value, seeflop_value
def test_values():
    assert fold_value(folder=1, contrib=(3.0,1.0))[0] == +1.0   # SB wins BB's 1
    assert abs(showdown_value(0.5, stake=10.0)[0]) < 1e-9        # coinflip allin = 0 EV
    assert abs(seeflop_value(0.5, contrib=(2.5,2.5))[0]) < 1e-9  # eq .5, equal pot
```
- [ ] **Step 2-4:** implement (R=1 realization coefficient, documented; configurable later), run.
- [ ] **Step 5: commit** `feat(preflop): terminal valuation with equity realization`.

## Task 3: Generic small `PreflopHU` for cross-validation

**Files:** Create `engine/games/preflop_hu.py`; Test `tests/test_preflop_hu_game.py`

- [ ] Implement `PreflopHU(ExtensiveFormGame)` over **n abstract hands** + equity matrix + the betting tree (chance deals i,j independent; SB/BB infosets keyed by hand+history). Mirrors `PushFoldGame`. Test structure + a terminal utility.
- [ ] **Commit** `feat(preflop): generic extensive-form HU preflop (small)`.

## Task 4: Vectorized public-tree solver

**Files:** Create `engine/preflop/solver.py`; Test `tests/test_preflop_solver.py`

- [ ] **Step 1: cross-validation test** — on a tiny instance (n=3 hands, the betting tree), `PreflopSolver` per-node strategies match the generic `CFRSolver` on `PreflopHU` within 0.05 (the correctness anchor, exactly as push/fold was validated).
- [ ] **Step 2: run, expect fail.**
- [ ] **Step 3: implement** vectorized CFR: walk the public tree carrying a 169- (or n-) vector reach per player; at decision nodes keep per-hand regret/strategy over that node's actions; at terminals fold/showdown/seeflop, compute per-hand counterfactual values via the equity matrix `A=2E-1` (matrix-vector products like `PushFoldSolver`). CFR+ updates. Full code at execution.
- [ ] **Step 4: run, expect pass.** Add a convergence test (exploitability-style gap → small).
- [ ] **Step 5: commit** `feat(preflop): vectorized public-tree CFR solver`.

## Task 5: Full-169 solve + per-node charts + sanity

**Files:** Modify `engine/preflop/solver.py`; Test `tests/test_preflop_solver.py`

- [ ] **Step 1: test** — full 169 solve at 50bb: SB open(raise) range mean reasonable (~70-90% open in HU); `AA` raises/jams ~100%; `72o` opens far less; BB 3bets `AA`/`KK` heavily. (Loose sanity bounds, marked `@pytest.mark.slow`.)
- [ ] **Step 2-4:** implement `node_chart(node_path)` → `{hand: {action: freq}}`; `solve_preflop_hu(stack_bb)` returning the tree + per-node charts.
- [ ] **Step 5: commit** `feat(preflop): full 169 solve and per-node charts`.

## Task 6: API — `/solve` for preflop_hu

**Files:** Modify `api/schemas.py`, `api/main.py`; Test `tests/test_api_preflop.py`

- [ ] Add `game="preflop_hu"`, `params.stack_bb`, optional `node` (action path like `["raise","call"]` → which decision node's strategy). Response: `{tree: <serialized actions per node>, node, strategy: {hand:{action:freq}}, actions: [...]}`. Test 200 + shape; bad node → 422.
- [ ] **Commit** `feat(api): preflop_hu solve endpoint`.

## Task 7: Web — action-tree navigation

**Files:** Create `web/src/tree.ts`, `web/src/PositionTree.tsx`; Test `web/src/tree.test.ts`

- [ ] `tree.ts`: types + helpers to render the action path as clickable chips (SB → BB → …), tracking the current node. Test path nav logic.
- [ ] `PositionTree.tsx`: the C-region strip — position + available actions, current node highlighted, click to navigate. 
- [ ] **Commit** `feat(web): preflop action-tree navigation`.

## Task 8: Web — multi-action grid + freq bar + colors

**Files:** Modify `web/src/RangeGrid.tsx`, `web/src/FreqBar.tsx`, `web/src/App.tsx`; Test updates

- [ ] Each cell shows a **stacked multi-action fill** (one fixed color per action: fold=slate, call=green, raise=amber, allin=red) instead of binary red/blue. FreqBar shows all actions. Verdict picks the highest-frequency action with plain-language text. Wire App to the new endpoint + tree nav, keeping the beginner setup-flow.
- [ ] **Commit** `feat(web): multi-action range grid and recommendations`.

## Task 9: End-to-end verification

- [ ] Backend `pytest` green; web `vitest` green + build clean.
- [ ] Browser: set stack → navigate SB open node → pick hand → see multi-action recommendation; 3bet node shows tighter range.
- [ ] Update README + master-plan status. Commit.

---

## Self-review
- **Coverage:** tree (T1), valuation (T2), generic cross-val game (T3), vectorized solver + validation (T4), full solve/charts (T5), API (T6), tree nav (T7), multi-action UI (T8), e2e (T9). ✓
- **Correctness anchor:** T4 cross-checks the vectorized solver against the trusted generic `CFRSolver` on a tiny tree (same pattern that validated push/fold). ✓
- **Approximation flagged:** equity-realization (R=1) documented in `realization.py`, plan header, and surfaced in the UI (T8). Replaceable by real postflop EV in Phase D. ✓
- **Type consistency:** `Node.kind ∈ {fold,showdown,seeflop}`, `contrib=(sb,bb)`, `node_chart(path)->{hand:{action:freq}}` used consistently across tasks. ✓
- **Scale note:** 169-vector public-tree CFR is the right architecture and reusable for postflop later; not the generic full-tree walk (too slow over 169×169 deals).
