# open-gto — Design Spec

**Date:** 2026-06-14
**Status:** Approved (autonomous-proceed per user instruction)
**Author:** Claude (brainstorming session)

## 1. Purpose

A poker GTO (Game-Theory-Optimal) analysis tool. The MVP is a **real solver
engine** — it computes Nash-equilibrium strategies from scratch via
Counterfactual Regret Minimization (CFR) — not a viewer of precomputed data.

The engine is first **validated on toy games with known equilibria** (Kuhn,
Leduc poker), then applied to a **real, tractable poker spot**: heads-up
No-Limit Hold'em **preflop push/fold (jam-or-fold)**, producing a 13×13 range
chart like commercial tools (e.g. GTO Wizard).

Target reader / user: an engineer building and extending the solver.

## 2. Scope

### In scope (MVP)
- Generic extensive-form-game interface.
- CFR family solver: vanilla CFR, CFR+, DCFR (shared tree traversal, pluggable
  regret update).
- Toy games: Kuhn poker, Leduc poker (correctness validation).
- HU NLHE preflop push/fold game model + preflop equity table.
- Exploitability (best-response) computation as the convergence metric.
- FastAPI backend exposing `POST /solve`.
- React + TypeScript + Vite frontend: 13×13 hand grid with per-hand action
  frequencies rendered as colored proportions, plus a frequency summary bar.
- Tests: engine convergence + known-solution assertions, API contract, frontend
  component rendering.

### Out of scope (explicitly deferred)
- Card abstraction / bucketing (k-means, EMD, potential-aware). Not needed:
  toy games and push/fold are small enough to solve **exactly**.
- Postflop solving, multi-street game trees, multiple bet sizes.
- Multiway (3+ player) spots.
- Subgame re-solving (Libratus/DeepStack style).
- Authentication, persistence, deployment infra.

## 3. Architecture

Layered monorepo. The math engine is a pure Python package with **zero web
dependencies**, independently testable and runnable via CLI. The API is a thin
layer over it; the web app only renders.

```
open-gto/
├── engine/                 # pure Python math core (no web deps)
│   ├── game.py             # abstract ExtensiveFormGame interface
│   ├── cfr.py              # CFR / CFR+ / DCFR solver (regret matching)
│   ├── exploitability.py   # best-response → Nash distance metric
│   ├── games/
│   │   ├── kuhn.py         # Kuhn poker (analytic NE → validation)
│   │   ├── leduc.py        # Leduc poker (standard benchmark)
│   │   └── push_fold.py    # HU NLHE preflop jam/fold (real deliverable)
│   └── equity.py           # 169-hand preflop all-in equity
├── api/                    # FastAPI: POST /solve -> strategy JSON
├── web/                    # React + TS + Vite: 13×13 grid + freq bars
└── tests/                  # pytest + TestClient + vitest
```

### Data flow
`web` sends scenario params (blinds, stack depth in bb) → `api` calls
`engine.solve()` → engine runs CFR+ to convergence → returns
`{hand: {action: frequency}}` JSON → `web` paints each of the 169 hand cells
with action-frequency-proportional coloring.

## 4. Components (units, interfaces, dependencies)

### `engine/game.py` — `ExtensiveFormGame` (abstract)
- **Does:** Defines the game tree contract the solver traverses.
- **Interface:** `initial_state()`, `is_terminal(s)`, `is_chance(s)`,
  `current_player(s)`, `legal_actions(s)`, `chance_outcomes(s)`,
  `next_state(s, a)`, `infoset_key(s)`, `terminal_utility(s, player)`.
- **Depends on:** nothing.

### `engine/cfr.py` — `CFRSolver`
- **Does:** Runs CFR/CFR+/DCFR self-play; accumulates regrets + average
  strategy; returns the equilibrium strategy per infoset.
- **Interface:** `CFRSolver(game, variant="cfr_plus")`, `.run(iterations)`,
  `.average_strategy()`, `.current_strategy()`.
- **Depends on:** `game.py`, numpy.
- **Key design:** one tree-walk; a `RegretMinimizer` strategy object encapsulates
  the per-variant regret update so CFR/CFR+/DCFR share traversal code.

### `engine/exploitability.py`
- **Does:** Computes each player's best-response value against a fixed strategy;
  exploitability = sum of best-response gains (Nash distance). Metric in mbb/hand
  where applicable.
- **Interface:** `exploitability(game, strategy) -> float`.

### `engine/games/*.py`
- Each implements `ExtensiveFormGame`. Self-contained, independently testable.
- `push_fold.py` consumes `equity.py`.

### `engine/equity.py`
- **Does:** Provides all-in preflop equity between two 169-class hands (or hand
  vs range), via enumeration/precomputed table.

### `api/` — FastAPI
- `POST /solve` body: `{game, params, iterations}`; response: strategy JSON +
  convergence (final exploitability). Pydantic-validated.

### `web/` — React
- 13×13 grid component; each cell shows hand label + colored action-frequency
  bars. Scenario controls (stack depth). Fetches `/solve`, renders result.

## 5. Algorithms (research-grounded)

- **Regret Matching:** strategy ∝ positive cumulative regrets; uniform if all
  ≤ 0. (Neller & Lanctot)
- **Counterfactual regret:** `v_i(σ_{I→a}) − v_i(σ)` weighted by opponent+chance
  reach probability.
- **Average strategy converges to Nash** (not current strategy) for vanilla CFR;
  O(1/√T). Two-player zero-sum: avg regret < ε ⇒ 2ε-Nash.
- **CFR+ (primary):** regret-matching+ clamps cumulative regret at 0 each update;
  current strategy converges directly; >10× faster than vanilla CFR.
- **DCFR (optional):** DCFR(3/2, 0, 2) recommended defaults; 2–3× over CFR+.
  LCFR = DCFR(1,1,1); CFR+ = DCFR(∞,−∞,2).
- **Convergence metric:** exploitability (mbb/hand). Toy games checked against
  known equilibria.

Sources: Neller & Lanctot CFR intro; Zinkevich et al. NIPS 2007; Tammelin 2014
(CFR+); Brown & Sandholm 2019 (DCFR); Lanctot et al. 2009 (MCCFR).

## 6. Tech stack
- Engine: Python 3.11+, numpy. No web deps.
- API: FastAPI + Uvicorn + pydantic.
- Web: React 18 + TypeScript + Vite.
- Tests: pytest, FastAPI TestClient, vitest.

## 7. Error handling
- Engine: validate game/variant args; guard against degenerate (zero-reach)
  infosets; deterministic seeding for reproducible tests.
- API: pydantic validation → 422 on bad input; cap `iterations` to a max;
  structured error JSON.
- Web: loading / error states around the solve request; disable controls while
  solving.

## 8. Testing strategy
- **Kuhn:** assert converged strategy lies in the analytic NE family and
  game value ≈ −1/18 for player 1.
- **Leduc:** assert exploitability drops below a small threshold within N iters.
- **Push/fold:** spot-check against published HU Nash push/fold charts.
- **Convergence:** assert exploitability is monotone-decreasing and → 0.
- **API:** contract test on `/solve` (shape, ranges sum to 1 per hand).
- **Web:** grid renders 169 cells; frequencies map to widths/colors.

## 9. Milestones
1. Engine skeleton + `ExtensiveFormGame` + Kuhn + CFR + exploitability (TDD).
2. CFR+/DCFR variants + Leduc validation.
3. `equity.py` + push/fold game + chart output.
4. FastAPI `/solve`.
5. React 13×13 grid UI wired to API.
6. End-to-end test + verification, then notify.
