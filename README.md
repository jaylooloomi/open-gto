# open-gto

A poker **GTO (Game-Theory-Optimal) solver**. It computes Nash-equilibrium
strategies from scratch with Counterfactual Regret Minimization (CFR), is
validated on toy games with known equilibria (Kuhn & Leduc poker), and applies
the same engine to **heads-up No-Limit Hold'em preflop push/fold** — producing a
13×13 range chart in a web UI.

This is an MVP: a real solver end-to-end, intentionally scoped (see
[the design spec](docs/superpowers/specs/2026-06-14-open-gto-design.md)).

## What's inside

```
engine/        pure-Python solver (no web deps)
  game.py            ExtensiveFormGame interface
  cfr.py             CFR / CFR+ / DCFR solver (regret matching)
  exploitability.py  infoset-constrained best response + Nash distance
  eval7.py           7-card hand evaluator
  equity.py          169-hand preflop equity (Monte Carlo, cached)
  games/kuhn.py      Kuhn poker      (analytic NE: value -1/18)
  games/leduc.py     Leduc poker     (standard 288-infoset benchmark)
  games/push_fold.py HU NLHE preflop push/fold (vectorized CFR+)
  cli.py             command-line solver
api/           FastAPI: POST /solve
web/           React + TypeScript + Vite: 13×13 range grid
tests/         pytest suite
```

## Algorithms

- **CFR** — regret matching; the *average* strategy converges to a Nash
  equilibrium at O(1/√T) (Zinkevich et al. 2007).
- **CFR+** — regret-matching⁺ (cumulative regret clamped at 0) with linear
  averaging; the *current* strategy converges directly and far faster
  (Tammelin 2014). This is the default.
- **DCFR** — Discounted CFR, defaults α=3/2, β=0, γ=2 (Brown & Sandholm 2019).
- **Exploitability** — sum of both players' best-response gains; 0 at Nash. Used
  as the convergence metric.

## Run it

**Prerequisites:** Python 3.11+, Node 18+.

### Backend

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"      # Windows
# source .venv/bin/activate && pip install -e ".[dev]"   # macOS/Linux

# solve from the CLI
.venv\Scripts\python -m engine.cli push_fold --stack 10 --iters 1500

# or serve the API
.venv\Scripts\uvicorn api.main:app --reload          # http://localhost:8000
```

### Frontend

```bash
cd web
npm install
npm run dev                                          # http://localhost:5173
```

Open the dev URL, choose a stack depth, and hit **Solve**. (The API URL defaults
to `http://localhost:8000`; override with `VITE_API_URL`.)

## Test

```bash
.venv\Scripts\python -m pytest                 # full suite
.venv\Scripts\python -m pytest -m "not slow"   # skip convergence/integration tests
cd web && npm run test                         # frontend
```

## Scope & simplifications (MVP)

- Push/fold treats the two players' hands as independent (combo-weighted),
  ignoring card removal between hole cards.
- Equities are Monte-Carlo estimates (cached in `engine/data/`).
- No card abstraction, postflop play, multiway pots, or subgame re-solving —
  the solved games are small enough to handle exactly. These are natural next
  steps, not part of the MVP.
