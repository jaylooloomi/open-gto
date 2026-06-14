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
    parser.add_argument("game", choices=["push_fold", "preflop", "river", "kuhn", "leduc"])
    parser.add_argument("--stack", type=float, default=10.0, help="effective stack in bb")
    parser.add_argument("--iters", type=int, default=1500)
    parser.add_argument("--variant", default="cfr_plus", choices=["cfr", "cfr_plus", "dcfr"])
    parser.add_argument("--board", default="As,Kd,7h,2c,9s", help="river board (river)")
    parser.add_argument("--pot", type=float, default=10.0, help="starting pot in bb (river)")
    args = parser.parse_args(argv)

    if args.game == "push_fold":
        from engine.games.push_fold import solve_push_fold

        result = solve_push_fold(args.stack, iterations=args.iters, variant=args.variant)
    elif args.game == "preflop":
        from engine.preflop.solver import solve_preflop_hu

        result = solve_preflop_hu(args.stack, iterations=args.iters)
    elif args.game == "river":
        from engine.postflop.river import parse_card, solve_river

        board = [parse_card(c.strip()) for c in args.board.split(",")]
        result = solve_river(board, pot=args.pot, stack=args.stack, iterations=args.iters)
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
