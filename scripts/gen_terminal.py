#!/usr/bin/env python3
"""Render the profile's animated terminal (fastfetch, whoami, ...) as SVGs.

Usage: gen_terminal.py <codercat.jpg> <out_dir>

GitHub strips <style> and scripts from READMEs but renders SVGs referenced by
<img>, so the colour and the typing animation live inside the SVG itself.
"""
import sys
from html import escape
from pathlib import Path

from PIL import Image

COLS = 54
CHAR_W, LINE_H, FONT = 7.8, 17, 13
FONT_STACK = "'JetBrains Mono','Fira Code','DejaVu Sans Mono','Cascadia Mono',Menlo,monospace"
RAMP = " .:-=+*#%@"
HOST = "rumblejack@github"

INFO = [
    ("Shell", "zsh"),
    ("Focus", "agentic AI, memory systems, LLM plumbing"),
    ("Research", "EVOLVE-MEM, NeurIPS '25 (SEA)"),
    ("Edge AI", "audio-language models in <8 GB VRAM"),
    ("Systems", "GraphRAG at 400k+ nodes, RTB under 2 ms"),
    ("Wins", "Techfest IITB x2, BuildWithDelhi '24"),
    ("Hobby", "scripts, TUIs, small tools"),
]

# (command, [output lines]); a line is a list of (role, text) runs.
# roles: fg, dim, key, dir, hash, ref
SCENES = [
    ("fastfetch", "FASTFETCH"),
    ("whoami", [
        [("key", "ujjwal kakar"), ("dim", "  aka  "), ("fg", "rumblejack56")],
        [("fg", "builds agentic AI systems by day, terminal tools by night")],
    ]),
    ("cat ~/.focus", [
        [("dim", "- "), ("fg", "build small tools that fix my own annoyances")],
        [("dim", "- "), ("fg", "terminal UIs over web UIs")],
        [("dim", "- "), ("fg", "agentic AI, memory systems, and the plumbing around LLMs")],
    ]),
    ("ls ~/projects", [
        [("dir", "scripts/  tuis/  skills/  evolve-mem/  decibel/  emogtn/  adwise/")],
    ]),
    ("git log --oneline ~/wins", [
        [("hash", "5e1a9c2 "), ("ref", "(HEAD) "), ("fg", "Grand Finalist, Smart India Hackathon 2025 (DRDO, MoD)")],
        [("hash", "b7f03d1 "), ("fg", "1st Runner Up, Adobe Devcraft 2025")],
        [("hash", "c94e6aa "), ("fg", "Winner, National Geo-AI Hackathon, Techfest '25 IITB")],
        [("hash", "2d8b710 "), ("fg", "Winner, BuildWithDelhi '24 (AI track)")],
        [("hash", "f1a5e38 "), ("fg", "Winner, TIH-IoT, Techfest '23 IITB")],
    ]),
]

THEMES = {
    "tokyonight": dict(bg="#1a1b26", fg="#a9b1d6", key="#7aa2f7", dim="#565f89", dir="#7dcfff",
                       hash="#e0af68", ref="#9ece6a", bar="#16161e", title="#bb9af7", accent="#7aa2f7",
                       swatch=["#f7768e", "#ff9e64", "#e0af68", "#9ece6a", "#73daca", "#7aa2f7", "#bb9af7", "#c0caf5"]),
    "dracula": dict(bg="#282a36", fg="#f8f8f2", key="#bd93f9", dim="#6272a4", dir="#8be9fd",
                    hash="#f1fa8c", ref="#50fa7b", bar="#21222c", title="#ff79c6", accent="#bd93f9",
                    swatch=["#ff5555", "#ffb86c", "#f1fa8c", "#50fa7b", "#8be9fd", "#bd93f9", "#ff79c6", "#f8f8f2"]),
    "hacker": dict(bg="#000000", fg="#00e600", key="#00ff00", dim="#007a00", dir="#66ff66",
                   hash="#99ff99", ref="#ccffcc", bar="#000000", title="#00ff00", accent="#00ff00",
                   swatch=["#003300", "#006600", "#009900", "#00cc00", "#00ff00", "#66ff66", "#99ff99", "#ccffcc"]),
}


def cat_cells(path):
    """Rows of (char, hex colour) for the image; background becomes blank."""
    img = Image.open(path).convert("RGB")
    px = img.point(lambda v: 255 if v < 245 else 0).convert("L")
    img = img.crop(px.getbbox())
    w, h = img.size
    rows = round(COLS * (h / w) * 0.5)
    small = img.resize((COLS, rows), Image.BOX)
    pal = small.quantize(colors=12, method=Image.MEDIANCUT).convert("RGB")
    out = []
    for y in range(rows):
        row = []
        for x in range(COLS):
            r, g, b = small.getpixel((x, y))
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            if lum > 0.93:
                row.append((" ", None))
                continue
            ch = RAMP[min(len(RAMP) - 1, int((1 - lum) * len(RAMP)))]
            row.append((ch, "#%02x%02x%02x" % pal.getpixel((x, y))))
        out.append(row)
    return out


def lift(hex_color):
    """Brighten near-black art colours so they stay visible on dark themes."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    if (0.299 * r + 0.587 * g + 0.114 * b) < 70:
        r, g, b = (min(255, v + 90) for v in (r, g, b))
    return "#%02x%02x%02x" % (r, g, b)


def art_tspans(row, mono=None):
    out, run, col = [], "", None
    for ch, c in row:
        c = mono or c
        if c != col and run:
            out.append((run, col))
            run = ""
        col = c
        run += ch
    if run:
        out.append((run, col))
    return "".join(
        f'<tspan fill="{c}">{escape(t)}</tspan>' if c and t.strip() else escape(t)
        for t, c in out
    )


def runs(line, t):
    return "".join(f'<tspan fill="{t[role]}">{escape(text)}</tspan>' for role, text in line)


def build(theme_name, header="mac", animated=False, mono_art=False, cat=None):
    t = THEMES[theme_name]
    rows = [[(ch, lift(c) if c else None) for ch, c in r] for r in cat]
    art_w = COLS * CHAR_W
    info_x = 28 + art_w + 28
    width = int(info_x + 50 * CHAR_W + 24)
    top = 56 if header != "retro" else 30
    radius = 0 if header == "retro" else 10

    body, r, clock = [], 0, 0.4  # r = current text row, clock = animation time

    def y_of(row):
        return top + row * LINE_H

    def reveal(delay, dur=0.35):
        return f' style="animation:show {dur}s ease-out {delay:.2f}s both"' if animated else ""

    def command(text, row, at):
        n = len(text) + 2
        dur = max(0.4, len(text) * 0.07)
        style = f' style="animation:type {dur:.2f}s steps({n}) {at:.2f}s both"' if animated else ""
        body.append(f'<text x="20" y="{y_of(row)}"{style}><tspan fill="{t["accent"]}">❯</tspan> '
                    f'<tspan fill="{t["fg"]}">{escape(text)}</tspan></text>')
        return at + dur + 0.25

    for cmd, out in SCENES:
        clock = command(cmd, r, clock)
        r += 1
        if out == "FASTFETCH":
            mono = t["accent"] if mono_art else None
            body.append(f"<g{reveal(clock, 0.7)}>")
            for i, row in enumerate(rows):
                body.append(f'<text x="28" y="{y_of(r + i)}" xml:space="preserve">{art_tspans(row, mono)}</text>')
            body.append("</g>")
            body.append(f"<g{reveal(clock + 0.5, 0.6)}>")
            yy = r
            body.append(f'<text x="{info_x}" y="{y_of(yy)}"><tspan fill="{t["title"]}" font-weight="bold">{HOST}</tspan></text>')
            body.append(f'<text x="{info_x}" y="{y_of(yy + 1)}" fill="{t["dim"]}">{"─" * len(HOST)}</text>')
            yy += 2
            for key, val in INFO:
                body.append(f'<text x="{info_x}" y="{y_of(yy)}" xml:space="preserve"><tspan fill="{t["key"]}" '
                            f'font-weight="bold">{escape(key):<9}</tspan><tspan fill="{t["fg"]}">{escape(val)}</tspan></text>')
                yy += 1
            yy += 1
            for i, c in enumerate(t["swatch"]):
                body.append(f'<rect x="{info_x + i * 18}" y="{y_of(yy) - 11}" width="18" height="14" fill="{c}"/>')
            body.append("</g>")
            r += len(rows)
            clock += 1.4
        else:
            for line in out:
                body.append(f'<text x="20" y="{y_of(r)}" xml:space="preserve"{reveal(clock, 0.25)}>{runs(line, t)}</text>')
                r += 1
                clock += 0.18
            clock += 0.35
        r += 1  # blank row between commands

    # final prompt with blinking cursor
    cur_style = f' style="animation:show .01s linear {clock:.2f}s both"' if animated else ""
    body.append(f'<g{cur_style}><text x="20" y="{y_of(r)}"><tspan fill="{t["accent"]}">❯</tspan> '
                f'<tspan class="cur" fill="{t["accent"]}">▌</tspan></text></g>')
    height = int(y_of(r) + 28)

    css = f"text{{font-family:{FONT_STACK};font-size:{FONT}px;white-space:pre}}"
    if animated:
        css += ("@keyframes type{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}"
                "@keyframes show{from{opacity:0}to{opacity:1}}"
                "@keyframes blink{50%{opacity:0}}"
                ".cur{animation:blink 1s step-end infinite}")
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" role="img" aria-label="Terminal session: fastfetch, whoami, focus, projects and wins for RumbleJack56">',
         f"<style>{css}</style>",
         f'<rect width="{width}" height="{height}" rx="{radius}" fill="{t["bg"]}"/>']
    if header == "mac":
        s.append(f'<path d="M0 {radius}a{radius} {radius} 0 0 1 {radius}-{radius}h{width - 2 * radius}'
                 f'a{radius} {radius} 0 0 1 {radius} {radius}V32H0z" fill="{t["bar"]}"/>')
        for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
            s.append(f'<circle cx="{20 + i * 20}" cy="16" r="6" fill="{c}"/>')
        s.append(f'<text x="{width / 2}" y="20" text-anchor="middle" fill="{t["dim"]}">{HOST}: ~</text>')
    s.extend(body)
    s.append("</svg>")
    return "\n".join(s)


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    cat = cat_cells(src)
    variants = {
        "v1-tokyonight-static": dict(theme_name="tokyonight", header="mac"),
        "v2-dracula-typing": dict(theme_name="dracula", header="mac", animated=True),
        "v3-hacker-retro": dict(theme_name="hacker", header="retro", animated=True, mono_art=True),
    }
    for name, kw in variants.items():
        (out / f"{name}.svg").write_text(build(cat=cat, **kw), encoding="utf-8")
        print("wrote", out / f"{name}.svg")
    (out / "codercat.txt").write_text("\n".join("".join(c for c, _ in r).rstrip() for r in cat) + "\n")
    print("wrote", out / "codercat.txt")


if __name__ == "__main__":
    main()
