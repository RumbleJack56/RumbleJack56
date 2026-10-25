#!/usr/bin/env python3
"""Render the profile header as a self-contained typing SVG with mixed colours.

Usage: gen_header.py <out.svg>

readme-typing-svg can only colour a whole line, so this draws its own: each line
is typed, held, then deleted in a loop, and a run inside a line can be accented.
Light and dark colours switch with prefers-color-scheme inside the SVG.
"""
import sys
from html import escape
from pathlib import Path

W, H, SIZE = 920, 64, 26
CHAR_W = SIZE * 0.6
TYPE_S, DEL_S, HOLD_S, GAP_S = 0.06, 0.03, 1.7, 0.3
FONT_STACK = "'JetBrains Mono','Fira Code','DejaVu Sans Mono','Cascadia Mono',Menlo,monospace"

# each line is a list of (accent?, text) runs
LINES = [
    [(False, "Hi, I'm Ujjwal Kakar "), (True, "aka RumbleJack56")],
    [(False, "a tinkerer with a terminal open")],
    [(False, "making claude skills because why not")],
    [(False, "tuis, scripts, tools, projects, hackathons")],
    [(False, "coding is a form of self expression")],
]


def main():
    out = Path(sys.argv[1])
    timings, t = [], 0.0
    for line in LINES:
        n = sum(len(x) for _, x in line)
        typed = n * TYPE_S
        deleted = n * DEL_S
        timings.append((t, t + typed, t + typed + HOLD_S, t + typed + HOLD_S + deleted, n))
        t = timings[-1][3] + GAP_S
    total = t

    def pct(x):
        return f"{x / total * 100:.3f}%"

    css = [
        f"text{{font-family:{FONT_STACK};font-size:{SIZE}px;white-space:pre;fill:#24292f}}",
        ".a{fill:#d1242f;font-weight:bold}",
        "@media (prefers-color-scheme:dark){text{fill:#e6edf3}.a{fill:#4bfdf2}}",
    ]
    body = []
    for i, (line, (s, te, ds, de, n)) in enumerate(zip(LINES, timings)):
        hide, show = "clip-path:inset(0 100% 0 0)", "clip-path:inset(0 0 0 0)"
        css.append(
            f"@keyframes l{i}{{0%{{{hide}}}"
            f"{pct(s)}{{{hide};animation-timing-function:steps({n},end)}}"
            f"{pct(te)}{{{show};animation-timing-function:linear}}"
            f"{pct(ds)}{{{show};animation-timing-function:steps({n},end)}}"
            f"{pct(de)}{{{hide}}}100%{{{hide}}}}}"
            f".l{i}{{animation:l{i} {total:.2f}s infinite;clip-path:inset(0 100% 0 0)}}"
        )
        x = (W - n * CHAR_W) / 2
        spans = "".join(
            f'<tspan class="a">{escape(x_)}</tspan>' if acc else escape(x_) for acc, x_ in line
        )
        body.append(f'<text class="l{i}" x="{x:.1f}" y="{H / 2 + SIZE * 0.35:.1f}" xml:space="preserve">{spans}</text>')

    label = "; ".join("".join(x for _, x in line) for line in LINES)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'role="img" aria-label="{escape(label)}"><style>{"".join(css)}</style>' + "".join(body) + "</svg>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print("wrote", out, f"({total:.1f}s loop)")


if __name__ == "__main__":
    main()
