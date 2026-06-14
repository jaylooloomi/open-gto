"""Render a solved push/fold range as a 13x13 SVG grid (no browser needed).

Usage: python scripts/render_chart.py --stack 10 --view sb_jam --out chart.svg
"""
from __future__ import annotations

import argparse

from engine.games.push_fold import solve_push_fold

RANKS = "AKQJT98765432"
JAM = "#e4564a"
FOLD = "#33414f"


def cell_label(row: int, col: int) -> str:
    if row == col:
        return RANKS[row] * 2
    if row < col:
        return RANKS[row] + RANKS[col] + "s"
    return RANKS[col] + RANKS[row] + "o"


def render_svg(chart: dict[str, float], title: str) -> str:
    size, pad, top = 52, 6, 54
    w = pad * 2 + size * 13
    h = top + pad + size * 13 + 28
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="system-ui,sans-serif">',
        f'<rect width="{w}" height="{h}" fill="#1b2430"/>',
        f'<text x="{pad}" y="26" fill="#e7edf3" font-size="20" font-weight="700">{title}</text>',
    ]
    for row in range(13):
        for col in range(13):
            label = cell_label(row, col)
            freq = chart.get(label, 0.0)
            x, y = pad + col * size, top + row * size
            fill_h = freq * (size - 2)
            parts.append(f'<rect x="{x}" y="{y}" width="{size-2}" height="{size-2}" rx="3" fill="{FOLD}"/>')
            if fill_h > 0:
                parts.append(
                    f'<rect x="{x}" y="{y + (size-2) - fill_h:.1f}" width="{size-2}" '
                    f'height="{fill_h:.1f}" rx="3" fill="{JAM}"/>'
                )
            parts.append(
                f'<text x="{x + (size-2)/2:.0f}" y="{y + 21}" fill="#fff" font-size="12" '
                f'font-weight="700" text-anchor="middle">{label}</text>'
            )
            parts.append(
                f'<text x="{x + (size-2)/2:.0f}" y="{y + 36}" fill="#dfe7ee" font-size="11" '
                f'text-anchor="middle">{round(freq*100)}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stack", type=float, default=10.0)
    p.add_argument("--view", choices=["sb_jam", "bb_call"], default="sb_jam")
    p.add_argument("--iters", type=int, default=2000)
    p.add_argument("--out", default="chart.svg")
    args = p.parse_args(argv)

    result = solve_push_fold(args.stack, iterations=args.iters)
    label = "SB jam" if args.view == "sb_jam" else "BB call vs jam"
    title = f"{label} · {args.stack:.0f}bb · exploitability {result['exploitability']:.1e}"
    svg = render_svg(result[args.view], title)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
