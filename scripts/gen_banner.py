#!/usr/bin/env python3
"""Render the profile banner: a cluttered 8-bit night-time coding den whose
giant CRT plays the terminal session (fastfetch, whoami, ...) on a loop.

Usage: gen_banner.py <out.gif> [preview_dir]

Everything is drawn from code at 480x270 and scaled 2x with hard pixels, so
there are no borrowed assets. The room reacts to the terminal: hands type
with the prompt, the disk LED blinks on output, and each trophy sparkles as
its `git log ~/wins` line lands.
"""
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

W, H, SCALE, FRAME_MS = 480, 270, 2, 100
LOOP = 48  # ambient motion repeats every LOOP frames; the session is padded to a multiple


def hx(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


P = {k: hx(v) for k, v in dict(
    wall="#1b1236", wall_hi="#22183f", mortar="#140d2a", base="#2a1d45",
    floor="#1a1226", floor_ln="#120c1c", rug="#3a1f4f", rug_hi="#552c70", shadow="#0e0918",
    wood="#5c3a2e", wood_hi="#8a5a45", wood_dk="#3e271f",
    bezel="#2e3047", bezel_hi="#4a4e6e", bezel_dk="#1d1e2e",
    scr="#1e1f29", scr_bar="#15161e",
    fg="#f8f8f2", comment="#6272a4", purple="#bd93f9", pink="#ff79c6", cyan="#8be9fd",
    green="#50fa7b", yellow="#f1fa8c", orange="#ffb86c", red="#ff5555",
    neon_p="#ff5fd2", neon_c="#5ff4ff", neon_y="#ffe066", neon_off="#3a2348",
    sky0="#0b0e2b", sky1="#121845", sky2="#1c2160", moon="#f7f1c8", moon_dk="#d4cc9e",
    star="#ffffff", star_dim="#7f86c4", city0="#0c0d22", city1="#15173a",
    win_y="#ffd36b", win_b="#7ad3ff", beacon="#ff5555",
    frame="#3d2f63", frame_hi="#5a4790",
    hair="#16131c", hair_hi="#3b3348", rim="#7a6cc8", specs="#4a4a5e",
    tee="#e9e3d5", tee_dk="#c4bba8", tee_dd="#9d947f", logo_n="#1f3a68", logo_b="#2b6cd4", patch="#141418",
    skin="#e8b48a", skin_dk="#c48a63",
    chair="#3b2557", chair_hi="#553679", chair_dk="#26173a", stripe="#c84aa8",
    metal="#5a5c70", metal_dk="#33344a", wheel="#111018",
    kb="#23243a", key="#3c3e5c", key_lit="#8be9fd",
    octo="#3d444d", octo_rim="#768390", octo_dk="#15181d", face="#f2c9b0", face_dk="#d9a88f", eye="#2b1b17",
    gold="#ffd166", gold_dk="#c99a2e", gold_hi="#fff4c2",
    silver="#cfd6e6", silver_dk="#8a93a8", silver_hi="#ffffff",
    mug="#e9e4f0", mug_dk="#a9a2b8", coffee="#5c3a2e", steam="#8e86ad",
    pot="#c0623e", pot_dk="#8a4129", leaf="#4fbf6a", leaf_dk="#2d7f45",
    pc="#25273a", pc_hi="#3a3d57", led_g="#50fa7b", led_o="#ffb86c", led_off="#3a2a2a",
    duck="#ffd84d", duck_dk="#d9a520", beak="#ff9e3d",
    cork="#9a6b45", cork_dk="#6e4a2f", note_y="#ffe066", note_p="#ff9ecf", note_c="#9ee8ff",
    can="#121316", claw="#7cfc00", chips="#e5484d", chips_hi="#ffb86c",
    pizza="#d9b382", pizza_dk="#a8875c", bag="#e07a3a", bag_dk="#a8541f",
    zz="#c9c3ff", glow="#9fb4ff",
).items()}
BOOKS = ["#e5484d", "#ffd166", "#5ff4ff", "#bd93f9", "#50fa7b", "#ff79c6", "#ffb86c"]
GRAPH = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BULBS = ["neon_p", "cyan", "yellow", "green", "orange"]

# Classic 5x7 font (5x8 for descenders), column-major, bit 0 = top row.
FONT = {c: bytes.fromhex(h) for c, h in {
    " ": "0000000000", "!": "00005F0000", '"': "0007000700", "#": "147F147F14", "$": "242A7F2A12",
    "%": "2313086462", "&": "3649552250", "'": "0005030000", "(": "001C224100", ")": "0041221C00",
    "*": "082A1C2A08", "+": "08083E0808", ",": "0050300000", "-": "0808080808", ".": "0060600000",
    "/": "2010080402", "0": "3E5149453E", "1": "00427F4000", "2": "4261514946", "3": "2141454B31",
    "4": "1814127F10", "5": "2745454539", "6": "3C4A494930", "7": "0171090503", "8": "3649494936",
    "9": "064949291E", ":": "0036360000", ";": "0056360000", "<": "0814224100", "=": "1414141414",
    ">": "0041221408", "?": "0201510906", "@": "324979413E", "A": "7E1111117E", "B": "7F49494936",
    "C": "3E41414122", "D": "7F4141221C", "E": "7F49494941", "F": "7F09090101", "G": "3E41415132",
    "H": "7F0808087F", "I": "00417F4100", "J": "2040413F01", "K": "7F08142241", "L": "7F40404040",
    "M": "7F0204027F", "N": "7F0408107F", "O": "3E4141413E", "P": "7F09090906", "Q": "3E4151215E",
    "R": "7F09192946", "S": "4649494931", "T": "01017F0101", "U": "3F4040403F", "V": "1F2040201F",
    "W": "7F2018207F", "X": "6314081463", "Y": "0304780403", "Z": "6151494543", "[": "007F414100",
    "\\": "0204081020", "]": "0041417F00", "^": "0402010204", "_": "4040404040", "`": "0001020400",
    "a": "2054545478", "b": "7F48444438", "c": "3844444420", "d": "384444487F", "e": "3854545418",
    "f": "087E090102", "g": "18A4A4A47C", "h": "7F08040478", "i": "00447D4000", "j": "4080847D00",
    "k": "7F10284400", "l": "00417F4000", "m": "7C04180478", "n": "7C08040478", "o": "3844444438",
    "p": "FC24242418", "q": "18242418FC", "r": "7C08040408", "s": "4854545420", "t": "043F444020",
    "u": "3C4040207C", "v": "1C2040201C", "w": "3C4030403C", "x": "4428102844", "y": "1CA0A0A07C",
    "z": "4464544C44", "{": "0008364100", "|": "00007F0000", "}": "0041360800", "~": "0804081008",
    "❯": "4163361C08",
}.items()}

# Sprites: one char per pixel, "." is transparent.
OCTO_FACE = [  # fastfetch logo, drawn 4x
    ".bb..........bb.",
    ".bbb........bbb.",
    ".bbbbbbbbbbbbbb.",
    "bbbbbbbbbbbbbbbb",
    "bbffffffffffffbb",
    "bffffffffffffffb",
    "bffewffffffewffb",
    "bffeeffffffeeffb",
    "bffeeffffffeeffb",
    "bffffffFFffffffb",
    "bbffffffffffffbb",
    ".bbbffffffffbbb.",
    "..bbbbbbbbbbbb..",
    "..bbbbbbbbbbbb..",
    "..b.bb.bb.bb.b..",
]
OCTO = [  # sitting on the CRT; tentacles are drawn separately so they can move
    "..bb....................bb..",
    "..bbb..................bbb..",
    "..bbbb................bbbb..",
    "..bbbbb..............bbbbb..",
    "..bbbbbbbbbbbbbbbbbbbbbbbb..",
    ".bbbbbbbbbbbbbbbbbbbbbbbbbb.",
    ".bbbbbbbbbbbbbbbbbbbbbbbbbb.",
    "bbbbbffffffffffffffffffbbbbb",
    "bbbbffffffffffffffffffffbbbb",
    "bbbffffffffffffffffffffffbbb",
    "bbbfffeewffffffffffeewfffbbb",
    "bbbffeeeeffffffffffeeeeffbbb",
    "bbbffeeeeffffffffffeeeeffbbb",
    "bbbfffeeffffffffffffeefffbbb",
    "bbbffffffffffFFffffffffffbbb",
    "bbbbffffffffffffffffffffbbbb",
    ".bbbbffffffffffffffffffbbbb.",
    "..bbbbbbffffffffffffbbbbbb..",
    "....bbbbbbbbbbbbbbbbbbbb....",
    ".....bbbbbbbbbbbbbbbbbb.....",
    ".....bbbbbbbbbbbbbbbbbb.....",
    "....bbbbbbbbbbbbbbbbbbbb....",
    "....bbbbbbbbbbbbbbbbbbbb....",
    "...bbbbbbbbbbbbbbbbbbbbbb...",
]
HANGING = [(8, 9), (13, 11), (18, 9)]  # (column, length) of tentacles over the bezel


def rimmed(rows):
    """Top silhouette edge catches the fairy lights ("r")."""
    g = [list(r) for r in rows]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "b" and (y == 0 or rows[y - 1][x] == "."):
                g[y][x] = "r"
    return ["".join(r) for r in g]


def blinked(rows):
    """Eyes shut: one row of each eye stays as the lid line."""
    out = list(rows)
    for r in (10, 11, 13):
        out[r] = rows[r].replace("e", "f").replace("w", "f")
    return out


OCTO_RIM = rimmed(OCTO)
OCTO_BLINK = rimmed(blinked(OCTO))
OCTO_PAL = dict(b=P["octo"], r=P["octo_rim"], f=P["face"], F=P["face_dk"], e=P["eye"], w=P["star"])
LOGO_PAL = dict(b=P["purple"], f=P["face"], F=P["pink"], e=P["eye"], w=P["star"])
TROPHY = [
    "hgggggd",
    "hgggggd",
    ".hgggd.",
    "..hgd..",
    "...g...",
    "...d...",
    "..ggd..",
    ".ggggd.",
    ".ddddd.",
]
DUCK = [
    ".yy.....",
    "byky....",
    ".yy..yy.",
    ".yyyyyyy",
    ".yyyyyyd",
    "..dddd..",
]
ROBOT = [
    "....r....",
    "....m....",
    ".mmmmmmm.",
    ".mkckkck.",
    ".mkkkkkk.",
    ".mmmmmmm.",
    "..ddddd..",
    "mmdpdcdmm",
    "m.ddddd.m",
    "..d...d..",
    ".dd...dd.",
]
NOTE = ["..##", "..#.", "..#.", ".##.", "###.", ".#.."]
BOLT = ["..yy", ".yy.", "yyyy", ".yy.", "yy..", "y..."]

# ---------------------------------------------------------------- geometry

WIN = (16, 40, 126, 116)  # window glass, x0 y0 x1 y1 (exclusive)
BEZEL = (145, 38, 435, 181)
SCR = (154, 47, 426, 167)
TERM_X, TERM_Y, CELL_W, LINE_H, ROWS = 158, SCR[1] + 11, 6, 9, 12
KB = (132, 186, 198, 193)
TROPHY_X = [440, 448, 456, 464, 472]
TROPHY_Y = 49
TROPHY_KIND = ["gold", "silver", "gold", "gold", "gold"]
NEON_TEXT, NEON_X, NEON_Y, NEON_PITCH = "RUMBLEJACK56", 14, 12, 11


def neon_color(i):
    return "neon_p" if i < 6 else "neon_c" if i < 10 else "neon_y"
OCTO_X, OCTO_Y = 378, BEZEL[1] - len(OCTO)
CLOCK = (458, 30, 10)

# ---------------------------------------------------------------- terminal


def kv(key, val):
    return ((12, "purple", key), (21, "fg", val))


FASTFETCH = [
    ((12, "pink", "rumblejack"), (22, "fg", "@"), (23, "pink", "github")),
    ((12, "comment", "-----------------"),),
    kv("OS", "RumbleOS x86_56"),
    kv("Shell", "zsh"),
    kv("Focus", "agentic AI & LLM infra"),
    kv("Research", "EVOLVE-MEM, NeurIPS'25"),
    kv("Edge AI", "audio LMs in <8GB VRAM"),
    kv("Systems", "GraphRAG, 400k+ nodes"),
    kv("Latency", "RTB under 2 ms"),
    kv("Uptime", "caffeinated"),
    "SWATCH",
]
SCENES = [  # (command, output lines, frames per line, hold frames after)
    ("fastfetch", FASTFETCH, 1, 34),
    ("whoami", [
        ((0, "purple", "ujjwal kakar"), (13, "comment", "aka"), (17, "fg", "rumblejack56")),
        ((0, "fg", "agentic AI by day, terminal tools by night"),),
    ], 2, 22),
    ("cat ~/.focus", [
        ((0, "comment", "-"), (2, "fg", "small tools that fix my own annoyances")),
        ((0, "comment", "-"), (2, "fg", "terminal UIs over web UIs")),
        ((0, "comment", "-"), (2, "fg", "agentic AI, memory, and LLM plumbing")),
    ], 2, 24),
    ("ls ~/projects", [
        ((0, "cyan", "scripts/  tuis/  skills/  evolve-mem/"),),
        ((0, "cyan", "decibel/  emogtn/  adwise/"),),
    ], 2, 18),
    ("git log --oneline ~/wins", [
        ((0, "yellow", "5e1a9c2"), (8, "green", "(HEAD)"), (15, "fg", "SIH 2025 Grand Finalist")),
        ((0, "yellow", "b7f03d1"), (8, "fg", "1st Runner Up, Adobe Devcraft '25")),
        ((0, "yellow", "c94e6aa"), (8, "fg", "Winner, Geo-AI Hackathon, IITB '25")),
        ((0, "yellow", "2d8b710"), (8, "fg", "Winner, BuildWithDelhi '24 (AI)")),
        ((0, "yellow", "f1a5e38"), (8, "fg", "Winner, TIH-IoT, Techfest IITB '23")),
    ], 3, 40),
]
LOGO_LINE = "LOGO"  # marker run on the first fastfetch line


def build_session():
    """One dict per frame: what the terminal shows and what the room should do."""
    rng = random.Random(56)
    buf, frames = [], []
    state = dict(prompt="")

    def snap(n=1, **kw):
        for _ in range(n):
            frames.append(dict(lines=list(buf), prompt=state["prompt"], typing=kw.get("typing", False),
                               io=kw.get("io", False), trophy=kw.get("trophy"), party=kw.get("party", False)))

    def type_cmd(cmd):
        for i in range(len(cmd)):
            state["prompt"] = cmd[: i + 1]
            snap(1 + (rng.random() < 0.3), typing=True)
        snap(3)
        buf.append(((0, "purple", "❯"), (2, "fg", cmd)))
        state["prompt"] = None
        snap(1, io=True)

    snap(8)
    for cmd, out, gap, hold in SCENES:
        type_cmd(cmd)
        for i, line in enumerate(out):
            if cmd == "fastfetch" and i == 0:
                line = (LOGO_LINE,) + line
            buf.append(line)
            snap(gap, io=True, trophy=i if cmd.startswith("git log") else None)
        buf.append(())
        state["prompt"] = ""
        snap(hold, party=cmd.startswith("git log"))
    # The cleared screen after `clear` is frame 0 again, so pad the idle
    # stretch before typing it until the whole session divides into LOOP.
    pad_at = len(frames)
    type_cmd("clear")
    while len(frames) % LOOP:
        frames.insert(pad_at, frames[pad_at - 1])
    return frames


# ---------------------------------------------------------------- drawing

def fill(a, x0, y0, x1, y1, c):
    a[max(y0, 0):max(y1, 0), max(x0, 0):max(x1, 0)] = c


def put(a, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        a[y, x] = c


def blit(a, x, y, rows, pal, scale=1, ymin=0, ymax=H):
    for r, row in enumerate(rows):
        for col, ch in enumerate(row):
            if ch in pal:
                y0, y1 = max(y + r * scale, ymin), min(y + (r + 1) * scale, ymax)
                if y0 < y1:
                    fill(a, x + col * scale, y0, x + (col + 1) * scale, y1, pal[ch])


def text(a, x, y, s, c, scale=1):
    for i, ch in enumerate(s):
        g = FONT.get(ch, FONT["?"])
        for col in range(5):
            for row in range(8):
                if g[col] >> row & 1:
                    fill(a, x + (i * 6 + col) * scale, y + row * scale,
                         x + (i * 6 + col + 1) * scale, y + (row + 1) * scale, c)


def line(a, x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        put(a, x0, y0, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16
BAYER_FULL = np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W]


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + r:
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


rnd = random.Random(7)
STARS = []
while len(STARS) < 22:
    sx, sy = rnd.randrange(WIN[0] + 1, WIN[2] - 1), rnd.randrange(WIN[1] + 2, 86)
    if 68 <= sx <= 72 or 76 <= sy <= 80 or (sx - 106) ** 2 + (sy - 54) ** 2 < 120:
        continue
    STARS.append((sx, sy, rnd.randrange(LOOP), rnd.random() < 0.3))
BUILDINGS, CITY_WINDOWS = [], []
x = WIN[0]
while x < WIN[2]:
    bw, top = rnd.randrange(9, 17), rnd.randrange(84, 104)
    BUILDINGS.append((x, top, min(x + bw, WIN[2]), rnd.random() < 0.5))
    for wx in range(x + 2, min(x + bw, WIN[2]) - 1, 3):
        for wy in range(top + 3, WIN[3] - 1, 4):
            CITY_WINDOWS.append((wx, wy, rnd.random() < 0.4, rnd.random() < 0.2, rnd.randrange(1000)))
    x += bw + rnd.randrange(0, 3)
TALLEST = min(BUILDINGS, key=lambda b: b[1])
GRAPH_CELLS = [[rnd.choice([0, 1, 1, 2, 2, 3, 4]) for _ in range(7)] for _ in range(5)]


def fairy_lights():
    """Bulb positions along three sagging strings under the ceiling."""
    bulbs, wire = [], []
    for x0, x1, sag in ((0, 140, 6), (140, 440, 9), (440, 480, 4)):
        for x in range(x0, x1):
            u = (x - x0) / (x1 - x0)
            y = 2 + round(sag * 4 * u * (1 - u))
            wire.append((x, y))
            if (x - x0) % 11 == 5:
                bulbs.append((x, y + 1))
    return wire, bulbs


WIRE, LIGHTS = fairy_lights()


def static_scene():
    img = Image.new("RGB", (W, H), P["wall"])
    d = ImageDraw.Draw(img)
    # Brick wall.
    for row, y in enumerate(range(0, 232, 8)):
        d.line([(0, y), (W, y)], fill=P["mortar"])
        off = 0 if row % 2 == 0 else 8
        for bx in range(off - 16, W, 16):
            if rnd.random() < 0.18:
                d.rectangle([bx + 1, y + 1, bx + 15, y + 7], fill=P["wall_hi"])
            d.line([(bx, y), (bx, y + 7)], fill=P["mortar"])
    d.rectangle([0, 230, W, 237], fill=P["base"])
    # Floor, rug.
    d.rectangle([0, 238, W, H], fill=P["floor"])
    for i, y in enumerate(range(245, H, 8)):
        d.line([(0, y), (W, y)], fill=P["floor_ln"])
        for fx in range((i * 37) % 60, W, 60):
            d.line([(fx, y - 7), (fx, y)], fill=P["floor_ln"])
    d.ellipse([28, 236, 178, 266], fill=P["rug"])
    d.ellipse([40, 241, 166, 261], outline=P["rug_hi"])
    # Window frame and sill.
    d.rectangle([12, 36, 129, 119], fill=P["frame"])
    d.line([(12, 36), (129, 36)], fill=P["frame_hi"])
    d.line([(12, 36), (12, 119)], fill=P["frame_hi"])
    d.rectangle([8, 119, 133, 123], fill=P["wood"])
    d.line([(8, 119), (133, 119)], fill=P["wood_hi"])
    # Cork board with pinned notes and red string.
    d.rectangle([3, 129, 59, 183], fill=P["cork_dk"])
    d.rectangle([5, 131, 57, 181], fill=P["cork"])
    for nx, ny, w, h, c in ((8, 135, 11, 13, "mug"), (23, 134, 12, 14, "mug"), (39, 137, 10, 9, "note_y"),
                            (9, 155, 9, 9, "note_p"), (23, 154, 14, 9, "note_c"), (41, 151, 13, 15, "mug"),
                            (26, 167, 15, 12, "mug"), (8, 168, 10, 9, "note_y")):
        d.rectangle([nx, ny, nx + w - 1, ny + h - 1], fill=P[c])
    for ly in (138, 141, 144):
        d.line([(10, ly), (16, ly)], fill=P["comment"])
    d.rectangle([25, 136, 32, 143], fill=P["sky1"])  # polaroid
    d.rectangle([25, 141, 32, 143], fill=P["leaf_dk"])
    d.point((30, 137), fill=P["moon"])
    d.rectangle([41, 151, 53, 154], fill=P["red"])  # calendar
    for cy_ in (157, 160, 163):
        for cx_ in range(43, 53, 3):
            d.point((cx_, cy_), fill=P["comment"])
    for ly in (170, 173, 176):
        d.point((28, ly), fill=P["green"])
        d.line([(30, ly), (38, ly)], fill=P["comment"])
    pins = [(13, 135), (29, 134), (44, 137), (13, 155), (30, 154), (47, 151), (33, 167)]
    for (ax, ay), (bx_, by_) in zip(pins, pins[1:]):
        if abs(ax - bx_) + abs(ay - by_) < 30:
            d.line([(ax, ay), (bx_, by_)], fill=P["red"])
    for px_, py_ in pins:
        d.point((px_, py_), fill=P["pink"])
    # Pennant with a lightning bolt between window and monitor.
    d.line([(137, 34), (137, 39)], fill=P["metal"])
    d.polygon([(132, 40), (142, 40), (142, 80), (137, 75), (132, 80)], fill=P["chair_hi"])
    d.line([(132, 40), (142, 40)], fill=P["frame_hi"])
    # Wall clock.
    cx, cy, r = CLOCK
    d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=P["frame"])
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=P["mug"])
    for ang in range(0, 360, 90):
        tx, ty = cx + round((r - 2) * math.sin(math.radians(ang))), cy - round((r - 2) * math.cos(math.radians(ang)))
        d.point((tx, ty), fill=P["comment"])
    d.line([(cx, cy), (cx + 3, cy - 3)], fill=P["eye"])  # 2 a.m., naturally
    # Desk.
    d.rectangle([100, 184, 478, 195], fill=P["wood"])
    d.line([(100, 195), (478, 195)], fill=P["wood_hi"])
    d.rectangle([100, 196, 478, 205], fill=P["wood_dk"])
    d.rectangle([108, 206, 469, 237], fill=P["shadow"])
    d.rectangle([102, 206, 107, 237], fill=P["wood_dk"])
    d.rectangle([470, 206, 475, 237], fill=P["wood_dk"])
    # Under the desk: PC tower, console, book stack.
    d.rectangle([396, 208, 432, 237], fill=P["pc"])
    d.line([(396, 208), (432, 208)], fill=P["pc_hi"])
    d.line([(396, 208), (396, 237)], fill=P["pc_hi"])
    for vy in range(220, 234, 3):
        d.line([(402, vy), (426, vy)], fill=P["bezel_dk"])
    d.line([(397, 236), (431, 236)], fill=P["stripe"])
    d.rectangle([330, 229, 362, 237], fill=P["metal_dk"])
    d.rectangle([330, 229, 362, 231], fill=P["silver_dk"])
    d.line([(334, 234), (346, 234)], fill=P["shadow"])
    d.point((358, 234), fill=P["led_g"])
    for i, (bw_, c) in enumerate(((28, 0), (24, 2), (26, 5))):
        y = 233 - i * 4
        d.rectangle([440, y, 440 + bw_, y + 3], fill=hx(BOOKS[c]))
        d.line([(441, y + 1), (439 + bw_, y + 1)], fill=P["mug"])
    # Floor clutter: backpack, pizza box, paper balls.
    d.rounded_rectangle([184, 219, 208, 241], radius=5, fill=P["bag"])
    d.rounded_rectangle([188, 228, 204, 239], radius=3, fill=P["bag_dk"])
    d.line([(189, 231), (203, 231)], fill=P["yellow"])
    d.arc([188, 212, 204, 226], 180, 360, fill=P["bag_dk"], width=2)
    d.polygon([(286, 238), (330, 238), (336, 243), (292, 243)], fill=P["pizza"])
    d.line([(292, 243), (336, 243)], fill=P["pizza_dk"])
    d.ellipse([306, 239, 314, 242], fill=P["red"])
    for bx_, by_ in ((228, 249), (352, 247), (371, 236)):
        d.rectangle([bx_, by_, bx_ + 2, by_ + 2], fill=P["mug"])
        d.point((bx_ + 2, by_ + 2), fill=P["mug_dk"])
    # Speaker.
    d.rectangle([16, 192, 46, 237], fill=P["pc"])
    d.line([(16, 192), (46, 192)], fill=P["pc_hi"])
    d.line([(16, 192), (16, 237)], fill=P["pc_hi"])
    d.ellipse([28, 200, 34, 206], fill=P["bezel_dk"], outline=P["metal"])
    d.ellipse([22, 213, 40, 231], fill=P["bezel_dk"], outline=P["metal"])
    d.ellipse([28, 219, 34, 225], fill=P["metal_dk"])
    # Monitor.
    bx0, by0, bx1, by1 = BEZEL
    d.rounded_rectangle([bx0, by0, bx1 - 1, by1 - 1], radius=6, fill=P["bezel"])
    d.line([(bx0 + 6, by0 + 1), (bx1 - 7, by0 + 1)], fill=P["bezel_hi"])
    d.line([(bx0 + 1, by0 + 6), (bx0 + 1, by1 - 7)], fill=P["bezel_hi"])
    d.line([(bx0 + 6, by1 - 2), (bx1 - 7, by1 - 2)], fill=P["bezel_dk"])
    d.line([(bx1 - 2, by0 + 6), (bx1 - 2, by1 - 7)], fill=P["bezel_dk"])
    d.rectangle([SCR[0] - 2, SCR[1] - 2, SCR[2] + 1, SCR[3] + 1], fill=P["bezel_dk"])
    d.rectangle([276, 180, 303, 185], fill=P["bezel_dk"])
    d.rounded_rectangle([258, 185, 321, 190], radius=2, fill=P["bezel"])
    d.line([(260, 185), (319, 185)], fill=P["bezel_hi"])
    d.rectangle([384, 172, 387, 175], fill=P["bezel_dk"])
    d.rectangle([391, 172, 394, 175], fill=P["bezel_dk"])
    d.rectangle([418, 173, 420, 175], fill=P["led_g"])
    # Sticky notes on the bezel.
    d.rectangle([146, 40, 154, 48], fill=P["note_y"])
    d.line([(148, 43), (152, 43)], fill=P["pot_dk"])
    d.line([(148, 45), (151, 45)], fill=P["pot_dk"])
    d.rectangle([158, 170, 165, 177], fill=P["note_y"])
    d.rectangle([168, 171, 175, 178], fill=P["note_p"])
    d.line([(160, 173), (163, 173)], fill=P["pot_dk"])
    # Shelves, books, contribution-graph poster.
    for sy in (58, 112):
        d.rectangle([437, sy, 479, sy + 3], fill=P["wood"])
        d.line([(437, sy), (479, sy)], fill=P["wood_hi"])
        d.line([(442, sy + 4), (444, sy + 7)], fill=P["metal_dk"])
        d.line([(474, sy + 4), (472, sy + 7)], fill=P["metal_dk"])
    bx = 440
    for i in range(7):
        bw, bh = 3 + (i % 2), 10 + (i * 3) % 5
        d.rectangle([bx, 112 - bh, bx + bw - 1, 111], fill=BOOKS[i])
        d.line([(bx, 112 - bh + 2), (bx + bw - 1, 112 - bh + 2)], fill=P["shadow"])
        bx += bw + (i == 3)
    d.rectangle([444, 70, 474, 97], fill=P["frame"])
    d.rectangle([446, 72, 472, 95], fill=hx(GRAPH[0]))
    for r_, row in enumerate(GRAPH_CELLS):
        for c, lvl in enumerate(row):
            d.rectangle([449 + c * 3, 78 + r_ * 3, 450 + c * 3, 79 + r_ * 3], fill=hx(GRAPH[lvl]))
    d.line([(449, 74), (460, 74)], fill=P["comment"])
    # Desk clutter, left of the monitor: mouse, cans, paper, sticky pad, pencil.
    d.rounded_rectangle([204, 187, 210, 192], radius=2, fill=P["key"])
    for cx_, c in ((214, "pink"), (221, "cyan")):
        d.rectangle([cx_, 180, cx_ + 4, 191], fill=P[c])
        d.line([(cx_, 180), (cx_ + 4, 180)], fill=P["silver"])
        d.line([(cx_ + 1, 184), (cx_ + 1, 189)], fill=P["mug"])
    d.rectangle([230, 188, 233, 191], fill=P["mug"])
    d.point((233, 191), fill=P["mug_dk"])
    d.rectangle([237, 188, 245, 191], fill=P["note_y"])
    d.line([(244, 190), (254, 187)], fill=P["gold"])
    d.point((255, 187), fill=P["note_p"])
    # Right of the monitor stand: notebook, cube, gamepad, robot.
    d.rectangle([328, 186, 352, 191], fill=P["mug"])
    d.line([(340, 186), (340, 191)], fill=P["mug_dk"])
    for lx in range(330, 351, 2):
        d.point((lx, 185), fill=P["metal"])
    d.line([(330, 188), (338, 188)], fill=P["note_c"])
    d.line([(342, 188), (350, 188)], fill=P["note_c"])
    d.rectangle([356, 182, 365, 191], fill=P["eye"])
    for i, c in enumerate(("red", "yellow", "green", "cyan", "mug", "orange", "green", "red", "purple")):
        cx_, cy_ = 357 + (i % 3) * 3, 183 + (i // 3) * 3
        d.rectangle([cx_, cy_, cx_ + 1, cy_ + 1], fill=P[c])
    d.rounded_rectangle([370, 186, 390, 191], radius=2, fill=P["silver_dk"])
    d.line([(373, 188), (375, 188)], fill=P["eye"])
    d.line([(374, 187), (374, 189)], fill=P["eye"])
    d.point((386, 187), fill=P["red"])
    d.point((388, 189), fill=P["red"])
    d.point((384, 189), fill=P["pink"])
    # Blue whale tumbler, plant pot (steam and leaves animate).
    d.rectangle([442, 180, 451, 191], fill=P["logo_b"])
    d.line([(451, 180), (451, 191)], fill=P["logo_n"])
    d.rectangle([441, 178, 452, 180], fill=P["bezel_dk"])
    d.rectangle([443, 185, 448, 187], fill=P["star"])
    d.point((449, 185), fill=P["star"])
    d.point((450, 184), fill=P["star"])
    for bx_ in (444, 446):
        d.point((bx_, 184), fill=P["star"])
    d.rectangle([460, 183, 473, 191], fill=P["pot"])
    d.rectangle([458, 180, 475, 183], fill=P["pot_dk"])
    # Energy can with claw marks and a chip bag, right end of the desk.
    d.rectangle([414, 178, 419, 191], fill=P["can"])
    d.line([(414, 178), (419, 178)], fill=P["silver"])
    for cx_, jag in ((415, 0), (416, 1), (418, 0)):
        for cy_ in range(181, 189):
            d.point((cx_ + (jag if cy_ % 3 == 0 else 0), cy_), fill=P["claw"])
    d.polygon([(422, 183), (434, 183), (433, 191), (423, 191)], fill=P["chips"])
    for zx in range(422, 434, 2):
        d.point((zx, 182), fill=P["chips"])
    d.ellipse([425, 185, 431, 189], fill=P["chips_hi"])
    d.line([(434, 190), (437, 191)], fill=P["chips_hi"])  # a stray chip
    # Cable tangle under the desk into a power strip.
    for box in ([246, 200, 266, 224], [258, 204, 284, 230], [276, 200, 292, 216]):
        d.arc(box, 0, 180, fill=P["metal_dk"])
    d.line([(266, 212), (258, 234)], fill=P["metal_dk"])
    d.line([(284, 217), (268, 234)], fill=P["metal_dk"])
    d.rectangle([248, 234, 272, 237], fill=P["mug_dk"])
    for ox in range(252, 270, 5):
        d.point((ox, 235), fill=P["eye"])
    d.point((249, 235), fill=P["red"])
    # Crushed can and loose papers on the floor.
    d.rectangle([367, 235, 377, 238], fill=P["can"])
    d.line([(369, 236), (372, 237)], fill=P["claw"])
    d.line([(377, 235), (377, 238)], fill=P["silver"])
    for poly in ([(212, 247), (224, 245), (226, 251), (214, 253)],
                 [(222, 252), (233, 254), (231, 259), (220, 257)],
                 [(342, 252), (353, 251), (354, 256), (343, 257)]):
        d.polygon(poly, fill=P["mug"])
        d.line(poly[:2], fill=P["mug_dk"])
    # Monstera between speaker and chair.
    for lx, ly in ((44, 197), (58, 190), (49, 184), (63, 204), (40, 210)):
        d.line([(55, 224), (lx + 4, ly + 3)], fill=P["leaf_dk"])
    for lx, ly in ((44, 197), (58, 190), (49, 184), (63, 204), (40, 210)):
        d.ellipse([lx, ly, lx + 9, ly + 7], fill=P["leaf"])
        d.line([(lx + 2, ly + 3), (lx + 7, ly + 3)], fill=P["leaf_dk"])
        d.point((lx + 3, ly + 1), fill=P["leaf_dk"])
        d.point((lx + 6, ly + 5), fill=P["leaf_dk"])
    d.rectangle([48, 224, 62, 237], fill=P["pot"])
    d.rectangle([47, 222, 63, 225], fill=P["pot_dk"])
    # Pothos pot on top of the window frame; left-corner hanging planter.
    d.rectangle([99, 29, 111, 35], fill=P["pot"])
    d.line([(98, 29), (112, 29)], fill=P["pot_dk"])
    d.line([(5, 0), (5, 22)], fill=P["metal"])
    d.line([(10, 0), (8, 22)], fill=P["metal"])
    d.rectangle([0, 22, 12, 30], fill=P["pot"])
    d.line([(0, 22), (12, 22)], fill=P["pot_dk"])
    # Windowsill cactus.
    d.rectangle([20, 114, 27, 118], fill=P["pot"])
    d.rectangle([22, 105, 25, 113], fill=P["leaf"])
    d.rectangle([19, 107, 20, 110], fill=P["leaf"])
    d.rectangle([27, 106, 28, 109], fill=P["leaf"])
    a = np.array(img)

    # Sky: dithered three-band gradient, full moon, skyline.
    x0, y0, x1, y1 = WIN
    for y in range(y0, y1):
        t = (y - y0) / (y1 - y0) * 2
        lo, hi = ("sky0", "sky1") if t < 1 else ("sky1", "sky2")
        f = t if t < 1 else t - 1
        for x in range(x0, x1):
            a[y, x] = P[hi] if f > BAYER_FULL[y, x] else P[lo]
    for y in range(46, 63):
        for x in range(98, 115):
            if (x - 106) ** 2 + (y - 54) ** 2 <= 56:
                a[y, x] = P["moon"]
    for cx_, cy_ in ((103, 52), (108, 57), (109, 51)):
        a[cy_, cx_] = P["moon_dk"]
        a[cy_, cx_ + 1] = P["moon_dk"]
    for bx0_, top, bx1_, alt in BUILDINGS:
        fill(a, bx0_, top, bx1_, y1, P["city1" if alt else "city0"])
    fill(a, TALLEST[0] + 3, TALLEST[1] - 5, TALLEST[0] + 4, TALLEST[1], P["city1"])
    fill(a, 68, y0, 71, y1, P["frame"])
    fill(a, x0, 76, x1, 79, P["frame"])
    # Cactus pot sits in front of the glass.
    fill(a, 20, 114, 28, 119, P["pot"])
    # Trailing vines.
    for i in range(70):  # pothos: right side of the window, down the frame
        x, y = (110 + min(i, 18), 34 + i // 6) if i < 18 else (129 + round(math.sin(i / 3)), 37 + i - 18)
        vine_px(a, x, y, i)
    for i in range(52):  # pothos: drooping left along the top of the frame
        vine_px(a, 99 - i, 35 + round(2.5 * math.sin(math.pi * i / 52)), i)
    for i in range(24):
        vine_px(a, 88 + round(math.sin(i / 2.5)), 37 + i, i)
    for i in range(86):  # hanging planter vines in the corner
        vine_px(a, 4 + round(1.6 * math.sin(i / 5)), 30 + i, i)
    for i in range(44):
        vine_px(a, 10 + round(1.2 * math.sin(i / 4 + 1)), 30 + i, i + 1)
    for i, (wx, wy) in enumerate(WIRE):  # ivy wound round the fairy-light string
        if i % 5 == 0:
            put(a, wx, wy + (1 if i % 10 else -1), P["leaf" if i % 15 else "leaf_dk"])
    # Sprites: trophies, duck, robot, bolt, monitor label.
    for tx, kind in zip(TROPHY_X, TROPHY_KIND):
        blit(a, tx, TROPHY_Y, TROPHY, dict(g=P[kind], d=P[kind + "_dk"], h=P[kind + "_hi"]))
    blit(a, 468, 106, DUCK, dict(y=P["duck"], d=P["duck_dk"], b=P["beak"], k=P["eye"]))
    blit(a, 399, 181, ROBOT, dict(m=P["silver"], d=P["silver_dk"], k=P["eye"], c=P["cyan"],
                                  p=P["pink"], r=P["metal"]))
    blit(a, 135, 50, BOLT, dict(y=P["yellow"]))
    text(a, 276, 171, "RJ-56", P["bezel_hi"])
    # Fairy-light wire.
    for wx, wy in WIRE:
        a[wy, wx] = P["metal_dk"]
    return a


def vine_px(a, x, y, i):
    """One step of a vine: stem pixel, and a two-pixel leaf every third step."""
    put(a, x, y, P["leaf_dk"])
    if i % 3 == 0:
        side = 1 if (i // 3) % 2 else -1
        put(a, x + side, y, P["leaf"])
        put(a, x + 2 * side, y, P["leaf"])
        put(a, x + side, y + 1, P["leaf_dk"])


def layer(draw):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw(ImageDraw.Draw(img))
    return np.array(img)


def curl_blobs():
    """Round clumps around the head outline: a fluffy, messy mop of curls."""
    rr = random.Random(57)
    blobs = []
    for k in range(22):
        ang = 2 * math.pi * k / 22 + rr.uniform(-0.12, 0.12)
        rad = 13 + rr.uniform(-1, 2.5) + (2 if math.sin(ang) > 0.6 else 0)  # heavier at the nape
        blobs.append((100 + rad * math.cos(ang), 138 + rad * math.sin(ang), rr.choice((3, 4, 4, 5))))
    return blobs


CURL_BLOBS = curl_blobs()
CURLS = [(92, 131, 4), (99, 128, 5), (106, 131, 4), (90, 139, 5), (98, 136, 4), (105, 140, 4),
         (94, 146, 4), (101, 147, 5), (108, 147, 4), (96, 152, 4), (104, 153, 4)]
LOGO = ["...nnnnnn", "...nnnnnn", "nn.....nn", "nn.bb..nn", "nn.bb..nn", "nn.bbbbnn", "nn.bbbbnn",
        "nnnnnnnnn", "nnnnnnnnn"]


def head_layer(dy):
    def draw(d):
        d.rectangle([96, 150 + dy, 104, 157], fill=P["skin_dk"])  # neck
        d.ellipse([86, 125 + dy, 114, 153 + dy], fill=P["hair"])
        for cx, cy, r in CURL_BLOBS:
            cx, cy = round(cx), round(cy) + dy
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=P["hair"])
        for x0, y0, x1, y1 in ((93, 124, 90, 119), (101, 122, 103, 117), (108, 125, 113, 121), (86, 133, 82, 131)):
            d.line([(x0, y0 + dy), (x1, y1 + dy)], fill=P["hair"])  # stray strands
        for cx, cy, r in CURLS:
            d.arc([cx - r // 2, cy + dy - r // 2, cx + r // 2, cy + dy + r // 2], 190, 350, fill=P["hair_hi"])
        # Ear peeking through the curls, glasses temple, rim and glint.
        d.rectangle([113, 139 + dy, 115, 144 + dy], fill=P["skin"])
        d.point((114, 141 + dy), fill=P["skin_dk"])
        d.line([(114, 140 + dy), (120, 139 + dy)], fill=P["specs"])
        d.line([(121, 136 + dy), (121, 142 + dy)], fill=P["specs"])
        d.point((122, 137 + dy), fill=P["star"])
        # Lollipop stick.
        d.line([(119, 147 + dy), (125, 146 + dy)], fill=P["mug"])
    a = layer(draw)
    hair = (a[..., :3] == P["hair"]).all(-1)
    for y in range(H):
        xs = np.nonzero(hair[y])[0]
        if len(xs):
            a[y, xs[-1], :3] = P["rim"]
    return a


def body_layer(pose):
    rdy = -1 if pose == "A" else 0
    ldy = -1 if pose == "B" else 0

    def draw(d):
        # Oversized tee, back view.
        d.rounded_rectangle([75, 153, 125, 200], radius=11, fill=P["tee"])
        d.polygon([(75, 164), (88, 155), (90, 200), (75, 200)], fill=P["tee_dk"])
        d.line([(96, 162), (93, 172)], fill=P["tee_dk"])
        d.line([(104, 163), (108, 172)], fill=P["tee_dk"])
        d.ellipse([91, 152, 109, 158], fill=P["tee_dk"])
        d.ellipse([95, 153, 105, 156], fill=P["skin_dk"])
        # Far (left) forearm peeking out right of the chair.
        d.polygon([(121, 176), (127, 173), (142, 185 + ldy), (138, 189 + ldy)], fill=P["skin_dk"])
        d.rectangle([138, 185 + ldy, 145, 189 + ldy], fill=P["skin_dk"])
        # Near (right) arm: short sleeve, bare forearm.
        d.polygon([(128, 169), (135, 167), (157, 181 + rdy), (152, 187 + rdy)], fill=P["skin"])
        d.line([(129, 172), (152, 187 + rdy)], fill=P["skin_dk"])
        d.rectangle([153, 182 + rdy, 161, 187 + rdy], fill=P["skin"])
        d.line([(155, 187 + rdy), (161, 187 + rdy)], fill=P["skin_dk"])
        d.polygon([(115, 156), (127, 158), (137, 169), (127, 176), (115, 169)], fill=P["tee"])
        d.line([(127, 176), (137, 169)], fill=P["tee_dd"])
        d.line([(116, 169), (127, 176)], fill=P["tee_dk"])
        # ": >" patch on the sleeve.
        d.rectangle([123, 162, 131, 167], fill=P["patch"])
        d.point((125, 163), fill=P["star"])
        d.point((125, 166), fill=P["star"])
        for px_, py_ in ((128, 163), (129, 164), (129, 165), (128, 166)):
            d.point((px_, py_), fill=P["star"])
    a = layer(draw)
    pal = dict(n=P["logo_n"], b=P["logo_b"])
    for r, row in enumerate(LOGO):  # bracket logo on the back of the right shoulder
        for c, ch in enumerate(row):
            if ch in pal:
                a[158 + r, 107 + c] = pal[ch] + (255,)
    return a


def chair_layer():
    def draw(d):
        d.rounded_rectangle([64, 214, 136, 223], radius=3, fill=P["chair_dk"])
        d.rounded_rectangle([70, 172, 130, 226], radius=7, fill=P["chair"])
        d.line([(71, 178), (71, 220)], fill=P["chair_hi"])
        d.line([(72, 174), (72, 222)], fill=P["chair_hi"])
        d.line([(129, 178), (129, 220)], fill=P["chair_dk"])
        for sx in (82, 116):
            d.rectangle([sx, 176, sx + 2, 222], fill=P["stripe"])
        d.line([(76, 173), (124, 173)], fill=P["chair_hi"])
        d.rectangle([97, 227, 103, 236], fill=P["metal"])
        d.line([(76, 238), (124, 238)], fill=P["metal_dk"], width=2)
        for wx, wy in ((76, 240), (100, 241), (124, 240)):
            d.ellipse([wx - 2, wy - 2, wx + 2, wy + 2], fill=P["wheel"])
    return layer(draw)


def over(a, lay):
    m = lay[..., 3] > 0
    a[m] = lay[..., :3][m]


NEON_MASKS = []  # per letter
NEON_STATES = {}


def neon_masks():
    for i, ch in enumerate(NEON_TEXT):
        m = np.zeros((H, W, 3), np.uint8)
        text(m, NEON_X + i * NEON_PITCH, NEON_Y, ch, (255, 255, 255), scale=2)
        NEON_MASKS.append(m[..., 0] > 0)


def neon_halo(on):
    letters = np.zeros((H, W), bool)
    for i in on:
        letters |= NEON_MASKS[i]
    near = dilate(letters, 1) & ~letters
    far = dilate(letters, 3) & ~dilate(letters, 1)
    return letters, (near & (BAYER_FULL < 0.5)) | (far & (BAYER_FULL < 0.22))


def neon_flicker(f):
    return f % 96 in (50, 51, 53, 54, 55) or f % 144 == 100


def glow_mask():
    ys, xs = np.mgrid[0:H, 0:W]
    cx, cy = (SCR[0] + SCR[2]) / 2, (SCR[1] + SCR[3]) / 2
    hw, hh = (SCR[2] - SCR[0]) / 2, (SCR[3] - SCR[1]) / 2
    dx = np.maximum(np.abs(xs - cx) - hw, 0)
    dy = np.maximum(np.abs(ys - cy) - hh, 0) * 1.3
    g = np.clip(1 - np.hypot(dx, dy) / 70, 0, 1) ** 1.4
    m = g > BAYER_FULL
    m[BEZEL[1]:BEZEL[3], BEZEL[0]:BEZEL[2]] = False
    m[WIN[1]:WIN[3], WIN[0]:WIN[2]] = False
    return m


def tint(a, mask, color, amt):
    sub = a[mask].astype(np.float32)
    a[mask] = np.round(sub + (np.array(color, np.float32) - sub) * amt).astype(np.uint8)


# ---------------------------------------------------------------- per frame

def draw_screen(a, fr, t):
    x0, y0, x1, y1 = SCR
    fill(a, x0, y0, x1, y1, P["scr"])
    fill(a, x0, y0, x1, y0 + 9, P["scr_bar"])
    for i, c in enumerate(("red", "yellow", "green")):
        fill(a, x0 + 6 + i * 6, y0 + 3, x0 + 9 + i * 6, y0 + 6, P[c])
    title = "rumblejack@github: ~"
    text(a, (x0 + x1) // 2 - len(title) * 3, y0 + 1, title, P["comment"])
    lines = list(fr["lines"])
    if fr["prompt"] is not None:
        lines.append(((0, "purple", "❯"), (2, "fg", fr["prompt"])))
    start = max(0, len(lines) - ROWS)
    for i, ln in enumerate(lines):
        y = TERM_Y + LINE_H * (i - start)
        if ln and ln[0] == LOGO_LINE:
            shown = min(len(OCTO_FACE) * 4, (len(lines) - i) * LINE_H)
            blit(a, TERM_X, y + 1, OCTO_FACE, LOGO_PAL, scale=4, ymin=TERM_Y - 1, ymax=min(y + 1 + shown, y1 - 2))
            ln = ln[1:]
        if i < start:
            continue
        if ln == "SWATCH":
            for k, c in enumerate(("red", "orange", "yellow", "green", "cyan", "purple", "pink", "fg")):
                fill(a, TERM_X + (12 + k) * CELL_W, y, TERM_X + (13 + k) * CELL_W, y + 7, P[c])
            continue
        for col, color, s in ln:
            text(a, TERM_X + col * CELL_W, y, s, P[color])
    if fr["prompt"] is not None and (fr["typing"] or (t // 5) % 2 == 0):
        cx = TERM_X + (2 + len(fr["prompt"])) * CELL_W
        cy = TERM_Y + LINE_H * (len(lines) - 1 - start)
        fill(a, cx, cy - 1, cx + 5, cy + 8, P["purple"])
    # CRT: scanlines and rounded glass corners.
    a[y0 + 1:y1:2, x0:x1] = (a[y0 + 1:y1:2, x0:x1] * 0.8).astype(np.uint8)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1 - 1, y0, -1, 1), (x0, y1 - 1, 1, -1), (x1 - 1, y1 - 1, -1, -1)):
        for ox, oy in ((0, 0), (1, 0), (0, 1)):
            a[cy + oy * sy, cx + ox * sx] = P["bezel_dk"]


def tentacle(a, pts):
    """3px-wide tentacle along pts: lit left edge, body, dark right edge."""
    for x, y in pts:
        put(a, x - 1, y, P["octo_rim"])
        put(a, x, y, P["octo"])
        put(a, x + 1, y, P["octo_dk"])


def draw_octocat(a, t, wave):
    base = BEZEL[1] - 1
    # Outer tentacles curl along the top of the monitor.
    for side, x0 in ((-1, OCTO_X + 4), (1, OCTO_X + 23)):
        if side == 1 and wave:
            continue
        for j in range(6):
            put(a, x0 + side * j, base, P["octo"])
            put(a, x0 + side * j, base - 1, P["octo_rim"] if j else P["octo"])
        put(a, x0 + side * 6, base - 1, P["octo"])
        put(a, x0 + side * 6, base - 2, P["octo_rim"])
    blit(a, OCTO_X, OCTO_Y, OCTO_BLINK if t % LOOP in (20, 21) else OCTO_RIM, OCTO_PAL)
    if wave:  # cheering for the trophies: one tentacle up, waving
        x0, wob = OCTO_X + 25, math.sin(2 * math.pi * t / 8) * 3
        pts = [(x0 + j, base - 1 - j) for j in range(4)]
        pts += [(x0 + 4 + round(wob * (j / 7) ** 1.5), base - 5 - j) for j in range(8)]
        tentacle(a, pts)
    # Middle tentacles dangle over the bezel and sway.
    for i, (col, length) in enumerate(HANGING):
        x0 = OCTO_X + col
        pts = []
        for j in range(length):
            dx = round(1.8 * math.sin(2 * math.pi * t / 24 + i * 1.7) * (j / length) ** 1.3)
            pts.append((x0 + dx, BEZEL[1] + j))
        tx, ty = pts[-1]
        curl = 1 if i < 2 else -1
        tentacle(a, pts + [(tx + curl, ty + 1)])


def draw_ambient(a, fr, t, f, sparkles):
    # Stars, shooting star, city lights, beacon.
    for sx, sy, ph, big in STARS:
        p = (t + ph) % LOOP
        if p < 3:
            put(a, sx, sy, P["star"])
            if big and p == 1:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(a, sx + ox, sy + oy, P["star_dim"])
        elif p % 7:
            put(a, sx, sy, P["star_dim"])
    for start in (30, 30 + LOOP * 3):
        k = f - start
        if 0 <= k < 9:
            for j in range(4):
                x, y = 22 + (k - j) * 6, 44 + (k - j) * 3
                if WIN[0] <= x < WIN[2] and y < 76 and not 67 <= x <= 71 and k - j >= 0:
                    fill(a, x, y, x + 2, y + 1, P["star" if j == 0 else "star_dim"])
    for wx, wy, lit, blue, seed in CITY_WINDOWS:
        flip = random.Random(seed * 131 + f // 24).random() < 0.08
        if lit != flip and not (68 <= wx <= 70 or 76 <= wy <= 78):
            put(a, wx, wy, P["win_b" if blue else "win_y"])
    if (t // 8) % 2 == 0:
        put(a, TALLEST[0] + 3, TALLEST[1] - 6, P["beacon"])
    # Fairy lights: three-step chase.
    for i, (lx, ly) in enumerate(LIGHTS):
        c = P[BULBS[i % len(BULBS)]]
        if (i + t // 4) % 3 == 0:
            c = tuple(v // 3 for v in c)
        fill(a, lx, ly, lx + 2, ly + 2, c)
    # Neon sign: J flickers.
    flick = neon_flicker(f)
    for i in range(len(NEON_TEXT)):
        lit = not (i == 6 and flick)
        a[NEON_MASKS[i]] = P[neon_color(i)] if lit else P["neon_off"]
    # Clock second hand: a tick every two frames.
    cx, cy, r = CLOCK
    ang = 2 * math.pi * (t // 2) / (LOOP // 2)
    line(a, cx, cy, cx + round((r - 2) * math.sin(ang)), cy - round((r - 2) * math.cos(ang)), P["red"])
    put(a, cx, cy, P["eye"])
    # Steam.
    for k in range(3):
        p = (t + k * 4) % 12
        if p < 10:
            sx = 444 + k * 3 + round(math.sin((p + k * 3) * 0.7))
            put(a, sx, 178 - p, P["steam"])
            if p < 7:
                put(a, sx, 177 - p, P["steam"])
    # Plant.
    sway = round(math.sin(2 * math.pi * t / LOOP) * 1.4)
    for bx, tx, ty in ((466, 459, 166), (467, 466, 160), (468, 474, 165), (465, 461, 172), (469, 472, 171)):
        line(a, bx, 180, tx + sway, ty, P["leaf_dk"])
        line(a, bx + 1, 180, tx + 1 + sway, ty + 1, P["leaf"])
    # Robot antenna blink.
    put(a, 403, 181, P["red"] if t % 12 < 6 else P["metal"])
    # Trophy sparkles.
    for k, phase in sparkles:
        cx, cy = TROPHY_X[k] + 1, TROPHY_Y + 1
        put(a, cx, cy, P["star"])
        arm = (1, 2, 3, 2, 1, 1)[phase % 6]
        for r in range(1, arm + 1):
            for ox, oy in ((r, 0), (-r, 0), (0, r), (0, -r)):
                put(a, cx + ox, cy + oy, P["star" if r == 1 else "gold_hi"])
    # Keyboard.
    fill(a, *KB, P["kb"])
    keys = [(kx, ky) for ky in (187, 190) for kx in range(134, 196, 4)]
    for kx, ky in keys:
        fill(a, kx, ky, kx + 3, ky + 2, P["key"])
    if fr["typing"]:
        kx, ky = keys[random.Random(f).randrange(len(keys))]
        fill(a, kx, ky, kx + 3, ky + 2, P["key_lit"])
    # PC disk LED and power LED.
    put(a, 428, 212, P["led_g"])
    put(a, 428, 215, P["led_o"] if fr["io"] and f % 2 == 0 else P["led_off"])
    # Speaker pulse and floating notes.
    if t % 8 < 2:
        fill(a, 29, 220, 34, 225, P["metal"])
        a[213, 25:38] = P["pink"]
    for k, c in ((0, "pink"), (12, "cyan")):
        p = (t + k) % 24
        if p < 18:
            nx = 34 + k // 3 + round(math.sin(p * 0.6) * 2)
            blit(a, nx, 186 - p * 2, NOTE, {"#": P[c]})


def render(frames):
    base = static_scene()
    neon_masks()
    for flick in (False, True):
        NEON_STATES[flick] = neon_halo([i for i in range(len(NEON_TEXT)) if not (i == 6 and flick)])
    heads = {dy: head_layer(dy) for dy in (0, 1)}
    bodies = {p: body_layer(p) for p in ("rest", "A", "B")}
    chair = chair_layer()
    glow = glow_mask() & ~np.any(NEON_MASKS, axis=0)
    halo_zone = {}
    xs = np.arange(W)[None, :].repeat(H, 0)
    bounds = [NEON_X + 6 * NEON_PITCH - 1, NEON_X + 10 * NEON_PITCH - 1]
    halo_zone["neon_p"] = xs < bounds[0]
    halo_zone["neon_c"] = (xs >= bounds[0]) & (xs < bounds[1])
    halo_zone["neon_y"] = xs >= bounds[1]

    trophy_at = {}
    for i, fr in enumerate(frames):
        if fr["trophy"] is not None and fr["trophy"] not in trophy_at.values():
            trophy_at[i] = fr["trophy"]
    last = max(trophy_at)

    out = []
    for f, fr in enumerate(frames):
        t = f
        a = base.copy()
        sparkles = [(k, f - s) for s, k in trophy_at.items() if 0 <= f - s < 12]
        if fr["party"] and f >= last + 12 and (f // 4) % 2 == 0:
            sparkles.append(((f // 8) % 5, f % 6))
        draw_ambient(a, fr, t, f, sparkles)
        draw_screen(a, fr, t)
        tint(a, glow, P["glow"], 0.13)
        draw_octocat(a, t, fr["party"])
        idle = not fr["typing"]
        over(a, heads[1 if idle and t % 8 < 4 else 0])
        over(a, bodies["rest" if idle else ("A" if f % 2 else "B")])
        over(a, chair)
        _, halo = NEON_STATES[neon_flicker(f)]
        for name, zone in halo_zone.items():
            tint(a, halo & zone, P[name], 0.28)
        out.append(a)
    return out


def save_gif(frames, path):
    big = [np.repeat(np.repeat(a, SCALE, 0), SCALE, 1) for a in frames]
    packed = [(b[..., 0].astype(np.uint32) << 16) | (b[..., 1].astype(np.uint32) << 8) | b[..., 2] for b in big]
    colors = np.unique(np.concatenate([np.unique(p) for p in packed]))
    if len(colors) > 256:
        raise SystemExit(f"{len(colors)} colours; trim the palette")
    pal = []
    for c in colors:
        pal += [int(c) >> 16, (int(c) >> 8) & 255, int(c) & 255]
    pal += [0] * (768 - len(pal))
    imgs = []
    for p in packed:
        im = Image.fromarray(np.searchsorted(colors, p).astype(np.uint8))
        im.putpalette(pal)
        imgs.append(im)
    raw = Path(path).with_suffix(".raw.gif")
    imgs[0].save(raw, save_all=True, append_images=imgs[1:], duration=FRAME_MS, loop=0, optimize=False, disposal=1)
    subprocess.run(["magick", str(raw), "-layers", "Optimize", str(path)], check=True)
    raw.unlink()
    print(f"{path}: {len(frames)} frames, {len(colors)} colours, {Path(path).stat().st_size / 1e6:.2f} MB")


def main():
    out = sys.argv[1]
    frames = render(build_session())
    if len(sys.argv) > 2:
        prev = Path(sys.argv[2])
        prev.mkdir(parents=True, exist_ok=True)
        for i in (0, 70, 130, 200, 290):
            Image.fromarray(np.repeat(np.repeat(frames[i], SCALE, 0), SCALE, 1)).save(prev / f"f{i:03d}.png")
    save_gif(frames, out)


if __name__ == "__main__":
    main()
