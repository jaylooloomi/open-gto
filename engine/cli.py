"""Command-line solver entry point.

Examples:
  python -m engine.cli push_fold --stack 10 --iters 1500
  python -m engine.cli kuhn --iters 20000
"""
from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine.cli", description="open-gto solver")
    parser.add_argument("game", choices=["push_fold", "kuhn", "leduc"])
    parser.add_argument("--stack", type=float, default=10.0, help="effective stack in bb (push_fold)")
    parser.add_argument("--iters", type=int, default=1500)
    parser.add_argument("--variant", default="cfr_plus", choices=["cfr", "cfr_plus", "dcfr"])
    args = parser.parse_args(argv)

    if args.game == "push_fold":
        from engine.games.push_fold import solve_push_fold

        result = solve_push_fold(args.stack, iterations=args.iters, variant=args.variant)
    else:
        from engine.cfr import CFRSolver
        from engine.exploitability import exploitability
        from engine.games.kuhn import KuhnPoker
        from engine.games.leduc import LeducPoker

        game = (KuhnPoker if args.game == "kuhn" else LeducPoker)()
        solver = CFRSolver(game, variant=args.variant)
        solver.run(args.iters)
        result = {
            "game_value": getattr(solver, "game_value", lambda: None)()
            if args.game == "kuhn"
            else None,
            "exploitability": exploitability(game, solver.solution_strategy()),
        }

    json.dump(result, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
