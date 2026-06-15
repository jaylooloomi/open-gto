# ♠ open-gto

**Learn the GTO-correct play for any heads-up hold'em spot — pick your cards, get a plain-language answer. Free, local, beginner-first.**

![python](https://img.shields.io/badge/engine-Python%203.11+-3776ab)
![web](https://img.shields.io/badge/web-React%20+%20Vite-61dafb)
![tests](https://img.shields.io/badge/tests-85%20passing-brightgreen)
![solver](https://img.shields.io/badge/solver-CFR%20%2F%20CFR+%20%2F%20DCFR-orange)

> 繁體中文介面 · 內建新手導覽 · [線上互動式範圍表](#-quickstart)

---

## The problem

Want to know the *mathematically optimal* way to play a poker hand?

- **Commercial solvers** (GTO Wizard, PioSOLVER) are powerful but **paid, dense, and assume you already speak poker** — ranges, combos, blockers, OOP/IP.
- **Strategy charts** are free but static: you memorize a picture without knowing *why*, and they don't adapt to your stack or the action.

A beginner just wants to ask: *"I have A♠K♠, 50bb deep, I'm the small blind — what do I do?"* and get a clear answer.

## The solution

**open-gto** computes Game-Theory-Optimal strategy **from scratch** with a real CFR solver, then puts it behind a setup flow anyone can use:

```
盲注 → 籌碼 → 人數 → 位置 → 手牌  ───►  GTO 建議:全下推注 / 加注 / 蓋牌
                                        + 完整 13×13 範圍表 + 走賽局樹
```

No account, no payment, runs on your machine. A guided tour (driver.js) walks first-timers through every step in Traditional Chinese.

## ✨ Key features

- 🧠 **A real solver, not a lookup table** — CFR / CFR+ / DCFR computes Nash equilibria live; validated on games with *known* answers (Kuhn poker value −1/18, Leduc's 288 infosets).
- 🎯 **Plain-language verdict** — pick your two cards → "GTO 建議:加注 100%" with a one-line why. No jargon required.
- 🌳 **Walk the game tree** — open → BB 3bet → 4bet …; see each player's GTO range at every node.
- 🎴 **Exact river solver** — true postflop equilibrium on any board (showdowns decided exactly, no approximation).
- 🀄 **Beginner-first, in Chinese** — setup wizard, glossary, onboarding tour, per-action colored 13×13 grid.
- 🆓 **Free & local** — your laptop is the solver. No subscription, no cloud.
- ✅ **Honest about accuracy** — exact where it's exact (push/fold, all-in lines, river); clearly labeled where it approximates (preflop see-flop EV).

## open-gto vs the alternatives

| | Strategy charts | GTO Wizard | **open-gto** |
|---|---|---|---|
| Cost | Free | Paid | **Free** |
| Beginner-friendly | ⚠️ memorize blindly | ❌ expert-oriented | ✅ guided, plain-language |
| Real solver | ❌ | ✅ | ✅ (live CFR) |
| Adapts to stack/action | ❌ | ✅ | ✅ |
| Runs locally / private | n/a | ❌ cloud | ✅ |
| Coverage | varies | full (preflop+postflop, 6-max) | HU push/fold + preflop tree + **river** (growing) |

## 🚀 Quickstart

**Prerequisites:** Python 3.11+, Node 18+.

```bash
# 1. backend (solver + API)
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"        # Windows
# source .venv/bin/activate && pip install -e ".[dev]" # macOS/Linux
.venv\Scripts\uvicorn api.main:app --reload            # http://localhost:8000

# 2. frontend (the web app)
cd web && npm install && npm run dev                   # http://localhost:5173
```

Open **http://localhost:5173** — the onboarding tour starts automatically. Set your stack, pick your seat and hand, and read the GTO advice. Click an action to walk deeper into the tree.

**Just want the numbers?** Use the CLI:

```bash
.venv\Scripts\python -m engine.cli preflop --stack 50           # HU preflop ranges
.venv\Scripts\python -m engine.cli push_fold --stack 10         # short-stack jam/fold
.venv\Scripts\python -m engine.cli river --board As,Kd,7h,2c,9s # exact river solve
```

## What's inside

```
engine/                pure-Python solver (no web deps)
  game.py              ExtensiveFormGame interface
  cfr.py               CFR / CFR+ / DCFR (regret matching)
  exploitability.py    infoset-constrained best response (Nash distance)
  eval7.py             7-card hand evaluator
  equity.py            169-hand preflop equity (Monte Carlo, cached)
  games/               kuhn · leduc · push_fold
  preflop/             betting tree + vectorized public-tree CFR (bet sizes)
  postflop/river.py    exact HU river solver
  cli.py               command-line solver
api/                   FastAPI: /solve (push/fold), /preflop (tree + charts)
web/                   React + TS + Vite — setup flow, tree nav, driver.js tour
docs/                  design spec · plans · GTO-Wizard UI analysis · master plan
tests/                 pytest (65) + web vitest (20)
```

## How the solver works

- **CFR** — regret matching; the *average* strategy converges to Nash at O(1/√T) (Zinkevich et al. 2007).
- **CFR+** (default) — regret-matching⁺ clamps cumulative regret at 0; the *current* strategy converges directly and ~10× faster (Tammelin 2014).
- **DCFR** — Discounted CFR, defaults α=3/2, β=0, γ=2 (Brown & Sandholm 2019).
- **Vectorized public-tree CFR** — preflop/river carry a per-hand *range vector* and value terminals with matrix ops (the architecture real solvers use). Cross-validated against the generic engine on game value.
- **Exploitability** — sum of both players' best-response gains; 0 at Nash. The convergence metric.

## Accuracy: what's exact, what's approximate

| Spot | Status |
|---|---|
| Toy games (Kuhn, Leduc) | ✅ exact, matches known equilibria |
| HU preflop push/fold | ✅ exact (all-in/fold showdowns) |
| HU river | ✅ exact (showdowns via 7-card eval) |
| HU preflop with bet sizes | ⚠️ approximate — "see-flop" EV uses equity realization (no postflop yet); all-in/fold lines exact |

We surface this in the UI rather than pretending. Authoritative bet-sizing needs postflop (on the roadmap).

## Roadmap

- [x] CFR engine + toy-game validation
- [x] HU preflop push/fold + 13×13 web UI
- [x] HU preflop bet-size tree + action-tree navigation
- [x] Exact river solver
- [ ] Turn / flop solving (card abstraction)
- [ ] 6-max / 9-max multi-position
- [ ] One-click desktop app (see below)

## Test

```bash
.venv\Scripts\python -m pytest                 # full suite (65)
.venv\Scripts\python -m pytest -m "not slow"   # fast subset
cd web && npm run test                         # frontend (20)
```

## License

TBD. Built with [Claude Code](https://claude.com/claude-code).
