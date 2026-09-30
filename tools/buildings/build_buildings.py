#!/usr/bin/env python3
"""Hub buildings: the Lasso Shop, the Animal Market, the Worlds station and the Wrangler Camp, built from
Parts in the game's warm log-cabin style, with a lot more detail than the old ones.

Every building is its own Model with its pivot on the ground in the middle, and its front facing -Z
(Roblox's Front). The file also has a small ModuleScript, SwapIn, that puts a new building exactly where an
old one stands (same spot, same turn, same size), so it replaces it 1:1.

    python3 tools/buildings/build_buildings.py                  -> build/buildings.json and build/world.json
    python3 tools/buildings/build_buildings.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
"""

import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "animal-models"))
sys.path.insert(0, str(HERE.parent / "statue"))
sys.path.insert(0, str(HERE.parent / "forest-entrance"))

from lib import IDENTITY, add, aim, angles, apply, cframe, matmul, scale, sub  # noqa: E402
from build_statue import C, Group, group_instance  # noqa: E402
from build_entrance import (barrel, campfire, crate, lantern, log, point_light, sack, surface_text, tri,  # noqa: E402
                            wagon, wheel)

LOG = C("#c9803f")
LOG2 = C("#b8712f")
LOG_END = C("#f0b673")
LOG_RING = C("#d99a55")
DECK = C("#d9974f")
DECK2 = C("#c9863f")
DARK = C("#7a4a2a")
DEEP = C("#5a3418")
STONE = [C("#9aa6b8"), C("#b3bfcc"), C("#8794a6")]
IRON = C("#3a3a42")
GOLD = C("#f2c14e")
ROPE = C("#d8a861")
ROPE2 = C("#c48f4c")
CREAM = C("#fff4dc")
FLOWERS = ["#ff5a5a", "#ffd23f", "#ff8fb8", "#b58cff", "#ffffff", "#ff9a3c"]

D = dict(collide=False)            # decoration: no collision
DS = dict(collide=False, shadow=False)


def at(base, R, off):
    return add(base, apply(R, off))


def cut_end(g, pos, d, R=IDENTITY):
    """Round-ish cut end of a log facing local X."""
    g.box("LogEnd", (0.08, d * 0.82, d * 0.82), pos, LOG_END, R=R, **D)
    g.box("LogEnd", (0.09, d * 0.8, d * 0.8), pos, LOG_END, R=matmul(R, angles(45, 0, 0)), **D)
    g.box("LogRing", (0.1, d * 0.38, d * 0.38), pos, LOG_RING, R=matmul(R, angles(45, 0, 0)), **D)


# ---------------------------------------------------------------- walls ---

def log_wall(g, axis, fixed, a0, a1, y0, rows, d, holes=(), stick=0.0, ends=True, shift=0):
    """Horizontal logs stacked from y0. axis "x": logs run along X at z = fixed; "z": along Z at x = fixed.
    holes: (from, to, y_from, y_to) openings. stick: how far logs stick out past the corners (every other row)."""
    for i in range(rows):
        y = y0 + d / 2 + i * d
        out = stick if (i + shift) % 2 == 0 else -d * 0.1
        segs = [(a0 - out, a1 + out)]
        for h0, h1, hy0, hy1 in holes:
            if hy0 < y < hy1:
                nxt = []
                for s0, s1 in segs:
                    if h1 <= s0 or h0 >= s1:
                        nxt.append((s0, s1))
                        continue
                    if h0 > s0:
                        nxt.append((s0, h0))
                    if h1 < s1:
                        nxt.append((h1, s1))
                segs = nxt
        color = LOG if i % 2 else LOG2
        for s0, s1 in segs:
            if s1 - s0 < 0.3:
                continue
            p0 = (s0, y, fixed) if axis == "x" else (fixed, y, s0)
            p1 = (s1, y, fixed) if axis == "x" else (fixed, y, s1)
            log(g, "Log", p0, p1, d, color)
        if ends and out > 0:
            for s in (a0 - out, a1 + out):
                p = (s, y, fixed) if axis == "x" else (fixed, y, s)
                cut_end(g, p, d, IDENTITY if axis == "x" else angles(0, 90, 0))


# ----------------------------------------------------------------- roofs ---

def slope(g, name, x0, x1, ridge, eave, colors, rng, thick=0.45, row=1.25, base=DEEP):
    """One shingled roof plane from the ridge line (z, y) down to the eave line (z, y), from x0 to x1."""
    (zr, yr), (ze, ye) = ridge, eave
    dz, dy = ze - zr, ye - yr
    L = math.hypot(dz, dy)
    u = (0, dy / L, dz / L)
    n = (0, abs(dz) / L, -dy / L * (1 if dz > 0 else -1)) if dz != 0 else (0, 1, 0)
    if n[1] < 0:
        n = scale(n, -1)
    theta = math.degrees(math.atan2(-u[1], u[2]))
    R = angles(theta, 0, 0)
    W = x1 - x0
    xm = (x0 + x1) / 2
    mid = add((xm, yr, zr), scale(u, L / 2))
    g.box(f"{name}Deck", (W, thick, L), mid, base, R=R)
    rows = max(2, round(L / row))
    rl = L / rows
    for r in range(rows):
        t = (r + 0.5) * rl
        # Stagger the shingles on every row, in two or three shades.
        x = x0 - rng.uniform(0.2, 1.4)
        while x < x1:
            w = rng.uniform(1.8, 3.2)
            a, b = max(x, x0), min(x + w, x1)
            if b - a > 0.2:
                c = add((0, 0, 0), scale(u, t))
                pos = add(add(((a + b) / 2, yr, zr), c), scale(n, thick / 2 + 0.12 + 0.04 * (r % 2)))
                g.box(f"{name}Shingle", (b - a - 0.06, 0.24, rl * 1.12), pos, colors[rng.randrange(len(colors))],
                      R=matmul(R, angles(-5, 0, 0)), **D)
            x += w
    # Barge boards along the sloped edges and a fascia board at the eave.
    for x in (x0 - 0.12, x1 + 0.12):
        g.box(f"{name}Barge", (0.26, 0.7, L + 0.2), add((x, 0, 0), add(mid, scale(n, 0.1))), CREAM if False else DARK,
              R=R, **D)
    g.box(f"{name}Fascia", (W + 0.5, 0.6, 0.3), add((xm, ye, ze), scale(n, 0.05)), DARK, **D)
    return R, u, n, L


def roof_height(ridge, eave, z):
    (zr, yr), (ze, ye) = ridge, eave
    t = (z - zr) / (ze - zr)
    return yr + (ye - yr) * t


# --------------------------------------------------------------- pieces ---

def window(g, center, w=2.8, h=3.0, shutter=C("#4a90d9"), box_flowers=True, rng=None, R=IDENTITY):
    """Window on a wall facing -Z (before R): glass, frame, cross bars, shutters with a Z brace, flower box."""
    rng = rng or random.Random(1)
    g.box("Glass", (w, h, 0.12), center, C("#a8d8ff"), R=R, reflectance=0.25, **D)
    g.box("GlassShine", (w * 0.25, h * 0.5, 0.13), at(center, R, (-w * 0.2, h * 0.12, -0.02)), C("#e6f5ff"), R=R, **DS)
    for dx, dy, sx, sy in ((0, h / 2 + 0.15, w + 0.6, 0.3), (0, -h / 2 - 0.15, w + 0.6, 0.3),
                           (w / 2 + 0.15, 0, 0.3, h), (-w / 2 - 0.15, 0, 0.3, h)):
        g.box("Frame", (sx, sy, 0.3), at(center, R, (dx, dy, -0.1)), CREAM, R=R, **D)
    g.box("Bar", (0.16, h, 0.2), at(center, R, (0, 0, -0.08)), CREAM, R=R, **D)
    g.box("Bar", (w, 0.16, 0.2), at(center, R, (0, 0, -0.08)), CREAM, R=R, **D)
    g.box("Sill", (w + 1.0, 0.25, 0.7), at(center, R, (0, -h / 2 - 0.4, -0.3)), DARK, R=R, **D)
    for sgn in (-1, 1):
        sc = at(center, R, (sgn * (w / 2 + 0.95), 0, -0.12))
        g.box("Shutter", (1.4, h + 0.2, 0.16), sc, shutter, R=R, **D)
        for dy in (-h / 3, 0, h / 3):
            g.box("ShutterSlat", (1.2, 0.08, 0.18), at(sc, R, (0, dy, -0.02)), C("#ffffff"), R=R, **DS)
        g.box("ShutterBrace", (0.14, h * 0.95, 0.19), at(sc, R, (0, 0, -0.03)), DEEP, R=matmul(R, angles(0, 0, 28)), **DS)
    if box_flowers:
        flower_box(g, at(center, R, (0, -h / 2 - 1.0, -0.55)), w + 0.6, rng, R=R)


def flower_box(g, pos, w, rng, R=IDENTITY, h=0.8, d=0.9):
    g.box("FlowerBox", (w, h, d), pos, DECK, R=R)
    g.box("FlowerBoxTrim", (w + 0.2, 0.2, d + 0.2), at(pos, R, (0, h / 2, 0)), DARK, R=R, **D)
    g.box("Soil", (w - 0.2, 0.1, d - 0.2), at(pos, R, (0, h / 2 + 0.05, 0)), C("#6b4a2a"), R=R, **DS)
    n = max(2, int(w / 0.8))
    for i in range(n):
        x = -w / 2 + 0.45 + (w - 0.9) * i / max(1, n - 1)
        top = at(pos, R, (x, h / 2 + 0.55, rng.uniform(-0.15, 0.15)))
        g.box("Leaf", (0.6, 0.5, 0.6), at(pos, R, (x, h / 2 + 0.3, 0)), C("#4fb84f"), R=matmul(R, angles(0, 45, 0)), **DS)
        g.box("Bloom", (0.5, 0.45, 0.5), top, C(FLOWERS[rng.randrange(len(FLOWERS))]),
              R=matmul(R, angles(0, rng.uniform(0, 90), 0)), **DS)
        g.box("BloomHeart", (0.2, 0.47, 0.2), top, C("#ffe066"), R=R, **DS)


def lamp_post(g, pos, yaw=0.0):
    R = angles(0, yaw, 0)
    g.octagon("LampBase", 0.55, 0.5, add(pos, (0, 0.25, 0)), STONE[0])
    g.octagon("LampPost", 0.28, 6.4, add(pos, (0, 3.7, 0)), DARK)
    g.box("LampArm", (0.25, 0.25, 1.6), at(pos, R, (0, 6.6, -0.7)), DARK, R=R, **D)
    g.rod("LampBrace", at(pos, R, (0, 5.6, 0)), at(pos, R, (0, 6.5, -1.0)), 0.16, DARK, **D)
    lantern(g, "Lamp", at(pos, R, (0, 6.45, -1.3)), chain=0.3)


def fence(g, p0, p1, h=2.6, every=2.4, color=DECK):
    length = math.dist(p0, p1)
    n = max(1, round(length / every))
    for i in range(n + 1):
        p = tuple(a + (b - a) * i / n for a, b in zip(p0, p1))
        g.box("FencePost", (0.45, h, 0.45), add(p, (0, h / 2, 0)), DARK)
        g.box("FenceCap", (0.55, 0.15, 0.55), add(p, (0, h + 0.07, 0)), DEEP, **D)
    for y in (h * 0.45, h * 0.85):
        g.rod("FenceRail", add(p0, (0, y, 0)), add(p1, (0, y, 0)), 0.3, color)


def rope_coil(g, center, R, r=0.7, k=0.14, loops=2):
    for i in range(loops):
        g.ring("RopeCoil", add(center, apply(R, (0, 0.1 * i, 0))), R, r - 0.08 * i, k, [ROPE, ROPE2], n=14, **D)


def hay_bale(g, pos, yaw=0.0, k=1.0):
    R = angles(0, yaw, 0)
    g.box("HayBale", (2.4 * k, 1.2 * k, 1.5 * k), add(pos, (0, 0.6 * k, 0)), C("#e8c35a"), R=R)
    g.box("HayTop", (2.3 * k, 0.15, 1.4 * k), add(pos, (0, 1.22 * k, 0)), C("#f2d57a"), R=R, **D)
    for dx in (-0.6, 0.6):
        g.box("HayStrap", (0.14, 1.24 * k, 1.54 * k), at(add(pos, (0, 0.6 * k, 0)), R, (dx * k, 0, 0)), C("#a8761c"), R=R,
              **D)
    for i in range(4):
        g.box("Straw", (0.5, 0.1, 0.1), at(add(pos, (0, 1.25 * k, 0)), R, (-0.8 + 0.5 * i, 0, 0.3)), C("#f2d57a"),
              R=matmul(R, angles(0, 30 * i, 0)), **DS)


def chimney(g, x, z, y0, y1):
    rng = random.Random(4)
    y = y0
    i = 0
    while y < y1:
        h = 0.8
        for dx, dz in ((0, 0),):
            g.box("Chimney", (2.2, h, 2.2), (x + dx, y + h / 2, z + dz), STONE[i % 3],
                  rot=(0, rng.uniform(-3, 3), 0))
        y += h
        i += 1
    g.box("ChimneyCap", (2.7, 0.4, 2.7), (x, y1 + 0.2, z), DARK)
    smoke = {"class": "ParticleEmitter", "name": "Smoke", "props": {
        "Texture": "rbxasset://textures/particles/smoke_main.dds", "Rate": 2.5, "Lifetime": [3, 5],
        "Speed": [1.5, 2.5], "SpreadAngle": [8, 8], "Size": [[0, 1.2], [1, 4.5]], "Transparency": [[0, 0.55], [1, 1]],
        "Color": [[0, 0.85, 0.85, 0.85], [1, 0.95, 0.95, 0.95]], "LightInfluence": 1, "Acceleration": [0.8, 0, 0],
        "RotSpeed": [-20, 20], "Rotation": [0, 360]}}
    g.box("ChimneyTop", (1.4, 0.1, 1.4), (x, y1 + 0.45, z), C("#2a2224"), children=[smoke], **DS)


def hanging_sign(g, text, center, w, h, color, frame=DEEP, R=IDENTITY, text_color="#fff4dc", stroke="#5a3418",
                 back_text=None):
    kids = [surface_text(text, "Front", color=text_color, ppu=60, stroke=stroke)]
    if back_text:
        kids.append(surface_text(back_text, "Back", color=text_color, ppu=60, stroke=stroke))
    board = g.box("SignBoard", (w, h, 0.35), center, color, R=R, children=kids)
    for y in (-h / 2 - 0.12, h / 2 + 0.12):
        g.box("SignFrame", (w + 0.5, 0.3, 0.5), at(center, R, (0, y, 0)), frame, R=R, **D)
    for x in (-w / 2 - 0.12, w / 2 + 0.12):
        g.box("SignFrame", (0.3, h + 0.5, 0.5), at(center, R, (x, 0, 0)), frame, R=R, **D)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box("SignBolt", (0.3, 0.3, 0.1), at(center, R, (sx * (w / 2 + 0.12), sy * (h / 2 + 0.12), -0.28)), GOLD,
                  R=matmul(R, angles(0, 0, 45)), **DS)
    return board


# ------------------------------------------------------------------ shop ---

W, ZF, ZB, Y0, D_LOG, ROWS = 22.0, -3.0, 8.0, 1.2, 0.95, 10
YW = Y0 + D_LOG * ROWS                     # top of the walls
RIDGE = ((ZF + ZB) / 2, 17.0)
EAVE_F = (ZF - 1.3, roof_height(RIDGE, (ZF, YW), ZF - 1.3))
EAVE_B = (ZB + 1.3, roof_height(RIDGE, (ZB, YW), ZB + 1.3))
PORCH_Z = -9.6


def shop(name, roof_colors, accent, sign_text, rng, emblem, extras, curtain):
    g = Group(name)
    hx = W / 2
    # Foundation: a stone base with stones on the face, and the porch deck on joists.
    g.box("Foundation", (W + 1.2, Y0, ZB - ZF + 1.2), (0, Y0 / 2, (ZF + ZB) / 2), STONE[2])
    x = -hx - 0.6
    i = 0
    while x < hx + 0.6:
        w = rng.uniform(1.2, 2.2)
        for row, y in enumerate((0.3, 0.9)):
            xx = x + (0.5 if row else 0)
            if xx + w / 2 < hx + 0.6:
                g.box("FoundationStone", (min(w, hx + 0.6 - xx) - 0.1, 0.52, 0.2),
                      (xx + min(w, hx + 0.6 - xx) / 2, y, ZB + 0.62), STONE[(i + row) % 3], **DS)
        x += w
        i += 1
    g.box("PorchFrame", (W + 2, Y0 - 0.25, ZF - PORCH_Z), (0, (Y0 - 0.25) / 2, (ZF + PORCH_Z) / 2), DEEP)
    nplank = 8
    for k in range(nplank):
        z = PORCH_Z + (ZF - PORCH_Z) * (k + 0.5) / nplank
        g.box("DeckPlank", (W + 2, 0.25, (ZF - PORCH_Z) / nplank - 0.08), (0, Y0 - 0.12, z), DECK if k % 2 else DECK2)
    for x in (-hx - 1, hx + 1):
        g.box("DeckEdge", (0.3, 0.35, ZF - PORCH_Z + 0.2), (x, Y0 - 0.1, (ZF + PORCH_Z) / 2), DARK, **D)
    g.box("DeckEdge", (W + 2.3, 0.35, 0.3), (0, Y0 - 0.1, PORCH_Z - 0.05), DARK, **D)
    # Steps in front of the counter.
    for s, (dz, y) in enumerate(((0.7, Y0 * 2 / 3), (1.4, Y0 / 3))):
        g.box("Step", (6.4, y, 0.75), (0, y / 2, PORCH_Z - dz + 0.35), DECK if s else DECK2)
        g.box("StepNose", (6.5, 0.12, 0.2), (0, y, PORCH_Z - dz), DARK, **D)

    # Log walls. The front has the big counter window.
    win = (-5.0, 5.0, 4.3, 8.9)
    log_wall(g, "x", ZF, -hx, hx, Y0, ROWS, D_LOG, holes=[win], stick=0.7)
    log_wall(g, "x", ZB, -hx, hx, Y0, ROWS, D_LOG, stick=0.7)
    for x in (-hx, hx):
        log_wall(g, "z", x, ZF, ZB, Y0, ROWS, D_LOG, stick=0.7, shift=1)
    # Gables: vertical boards under the roof on both sides.
    for x in (-hx, hx):
        z = ZF + 0.5
        k = 0
        while z < ZB - 0.3:
            top = roof_height(RIDGE, (ZF, YW), z) if z < RIDGE[0] else roof_height(RIDGE, (ZB, YW), z)
            h = top - YW - 0.2
            if h > 0.2:
                g.box("GableBoard", (0.4, h, 0.95), (x, YW + h / 2, z), DECK if k % 2 else DECK2)
            z += 0.95
            k += 1
        g.octagon("GableVent", 0.55, 0.2, (x - 0.12 * (1 if x > 0 else -1), YW + 3.0, RIDGE[0]), DEEP, collide=False)
    # Interior: floor, shelves and goods behind the counter, a warm light.
    g.box("InteriorFloor", (W - 1.5, 0.12, ZB - ZF - 1.5), (0, Y0 + 0.06, (ZF + ZB) / 2), DECK2, **D)
    g.box("InteriorCeiling", (W - 1, 0.2, ZB - ZF - 1), (0, YW - 0.1, (ZF + ZB) / 2), DEEP, **D,
          children=[point_light("#ffd9a0", 1.2, 18)])
    for y in (4.4, 6.6):
        g.box("Shelf", (12, 0.25, 1.1), (0, y, ZB - 1.0), DECK, **D)
        g.box("ShelfTrim", (12.1, 0.3, 0.12), (0, y, ZB - 1.55), DARK, **D)
    # Goods on the shelves: jars, boxes and rope coils in the shop's colors.
    for y in (4.4, 6.6):
        x = -5.5
        while x < 5.5:
            kind = rng.randrange(3)
            if kind == 0:
                g.octagon("Jar", 0.3, 0.8, (x, y + 0.53, ZB - 1.0), C(rng.choice(["#8fd0ff", "#ffd166", "#b58cff"])),
                          collide=False)
                g.octagon("JarLid", 0.32, 0.15, (x, y + 1.0, ZB - 1.0), DARK, collide=False)
            elif kind == 1:
                g.box("Goods", (0.8, 0.7, 0.7), (x, y + 0.48, ZB - 1.0), curtain[rng.randrange(2)], **D)
            else:
                g.ring("ShelfRope", (x, y + 0.2, ZB - 1.0), IDENTITY, 0.4, 0.14, [ROPE, ROPE2], n=10, **DS)
            x += rng.uniform(0.9, 1.3)
    g.box("Counter", (10.8, 3.1, 1.4), (0, Y0 + 1.55, ZF + 0.6), DECK2)
    g.box("CounterTop", (11.2, 0.35, 2.4), (0, 4.45, ZF - 0.1), DECK)
    g.box("CounterTrim", (11.3, 0.2, 0.2), (0, 4.25, ZF - 1.3), DARK, **D)
    for x in (-4.5, -1.5, 1.5, 4.5):
        g.box("CounterPanel", (2.4, 2.2, 0.12), (x, Y0 + 1.5, ZF - 0.12), DECK, **D)
    g.octagon("Bell", 0.25, 0.3, (3.8, 4.8, ZF - 0.6), GOLD, collide=False)
    g.box("BellKnob", (0.12, 0.2, 0.12), (3.8, 5.05, ZF - 0.6), GOLD, **DS)
    # Curtains and a scalloped valance in the counter window.
    for sx in (-1, 1):
        for j in range(3):
            g.box("Curtain", (0.7, 4.3, 0.2), (sx * (4.6 - 0.55 * j), 6.7, ZF - 0.35 + 0.05 * j), curtain[j % 2], **D)
        g.box("CurtainTie", (1.8, 0.25, 0.3), (sx * 4.0, 6.0, ZF - 0.5), GOLD, **DS)
    for i in range(10):
        x = -4.5 + i
        g.box("Valance", (1.0, 0.6, 0.2), (x, 8.6, ZF - 0.55), curtain[i % 2], **D)
        g.cyl("ValanceScallop", 0.2, 1.0, (x, 8.3, ZF - 0.55), curtain[i % 2], R=angles(0, 90, 0), **DS)
    # A door on the right and a window on the left.
    dx = 8.0
    g.box("Door", (3.0, 6.4, 0.3), (dx, Y0 + 3.2, ZF - 0.55), DECK)
    for i in range(4):
        g.box("DoorPlank", (0.08, 6.3, 0.32), (dx - 1.1 + 0.73 * i, Y0 + 3.2, ZF - 0.56), DARK, **DS)
    for y in (1.6, 5.2):
        g.box("DoorBrace", (2.9, 0.35, 0.34), (dx, Y0 + y, ZF - 0.6), DARK, **D)
    g.box("DoorBrace", (0.3, 4.2, 0.35), (dx, Y0 + 3.4, ZF - 0.6), DARK, rot=(0, 0, 38), **D)
    g.octagon("DoorKnob", 0.18, 0.3, (dx - 1.1, Y0 + 3.2, ZF - 0.8), GOLD, collide=False)
    for y, sx, sy in ((Y0 + 6.6, 3.8, 0.4), (Y0 + 3.2, 0.4, 6.8)):
        for xx in ((dx,) if sx > 1 else (dx - 1.7, dx + 1.7)):
            g.box("DoorFrame", (sx, sy, 0.4), (xx, y, ZF - 0.5), CREAM, **D)
    g.box("OpenSign", (1.8, 0.8, 0.12), (dx, Y0 + 5.0, ZF - 0.75), C("#2f8f3a"),
          children=[surface_text("OPEN", "Front", ppu=80, stroke="#1b4a22")], **D)
    window(g, (-8.2, 6.0, ZF - 0.55), shutter=accent, rng=rng)

    # Roof: shingled main roof, and a lower roof over the porch.
    oh = 1.2
    slope(g, "Roof", -hx - oh, hx + oh, RIDGE, EAVE_F, roof_colors, rng)
    slope(g, "Roof", -hx - oh, hx + oh, RIDGE, EAVE_B, roof_colors, rng)
    log(g, "Ridge", (-hx - oh - 0.2, RIDGE[1] + 0.35, RIDGE[0]), (hx + oh + 0.2, RIDGE[1] + 0.35, RIDGE[0]), 0.8, DARK)
    porch_top = (ZF - 0.2, YW - 0.6)
    porch_eave = (PORCH_Z - 0.6, 8.3)
    slope(g, "PorchRoof", -hx - 1.2, hx + 1.2, porch_top, porch_eave, roof_colors, rng, row=1.4)
    # Porch posts, braces and the beam that carries the porch roof.
    beam_y = roof_height(porch_top, porch_eave, PORCH_Z + 0.4) - 0.55
    for x in (-hx - 0.4, -3.3, 3.3, hx + 0.4):
        g.octagon("PorchPost", 0.36, beam_y - Y0, (x, (beam_y + Y0) / 2, PORCH_Z + 0.4), LOG)
        g.octagon("PostFoot", 0.5, 0.3, (x, Y0 + 0.15, PORCH_Z + 0.4), DARK)
        for sx in (-1, 1):
            if abs(x + sx * 1.3) < hx + 0.6:
                g.rod("PostBrace", (x, beam_y - 1.6, PORCH_Z + 0.4), (x + sx * 1.3, beam_y - 0.1, PORCH_Z + 0.4), 0.25,
                      LOG, **D)
    log(g, "PorchBeam", (-hx - 1.2, beam_y, PORCH_Z + 0.4), (hx + 1.2, beam_y, PORCH_Z + 0.4), 0.6, LOG2)
    # Railings on the porch, with a gap for the steps.
    for x0, x1 in ((-hx - 0.4, -3.3), (3.3, hx + 0.4)):
        for y in (Y0 + 0.4, Y0 + 2.4):
            g.box("Rail", (x1 - x0, 0.25, 0.25), ((x0 + x1) / 2, y, PORCH_Z + 0.4), DARK)
        x = x0 + 0.5
        while x < x1 - 0.3:
            g.box("Baluster", (0.18, 2.0, 0.18), (x, Y0 + 1.4, PORCH_Z + 0.4), LOG, **D)
            x += 0.6
    for sx in (-1, 1):
        for y in (Y0 + 0.4, Y0 + 2.4):
            g.box("Rail", (0.25, 0.25, ZF - PORCH_Z - 0.4), (sx * (hx + 0.4), y, (ZF + PORCH_Z + 0.4) / 2), DARK)
        z = PORCH_Z + 0.9
        while z < ZF - 0.3:
            g.box("Baluster", (0.18, 2.0, 0.18), (sx * (hx + 0.4), Y0 + 1.4, z), LOG, **D)
            z += 0.6
    # Lanterns under the porch roof.
    for x in (-7.0, 7.0):
        lantern(g, "PorchLantern", (x, beam_y - 0.3, PORCH_Z + 0.4), chain=0.4)
    chimney(g, 7.0, ZB - 2.2, YW - 1.0, RIDGE[1] + 2.4)

    # The sign on the porch roof, and the shop's emblem on the main roof.
    sy = porch_eave[1] + 1.9
    hanging_sign(g, sign_text, (0, sy, PORCH_Z - 0.2), 13.0, 2.6, C("#f0a35a"), R=angles(-8, 0, 0),
                 stroke="#6b3a14")
    for sx in (-1, 1):
        g.box("SignStand", (0.35, 2.4, 0.35), (sx * 5.5, sy - 1.0, PORCH_Z + 0.2), DARK, rot=(-8, 0, 0), **D)
    emblem(g, (0, roof_height(RIDGE, EAVE_F, 0.2) + 2.3, 0.2), IDENTITY)

    # Around the shop: flower boxes, lamp posts, fences, barrels and crates.
    for sx in (-1, 1):
        flower_box(g, (sx * 8.5, 0.4, PORCH_Z - 1.4), 4.0, rng)
        lamp_post(g, (sx * 14.5, 0, PORCH_Z - 0.8), yaw=0)
        fence(g, (sx * 15.5, 0, -4.0), (sx * 21.0, 0, -4.0))
    barrel(g, "Barrel", (-10.2, Y0, PORCH_Z + 2.0))
    crate(g, "Crate", (10.0, Y0, PORCH_Z + 1.9), 1.3, yaw=12)
    extras(g, rng)
    return g


# ---------------------------------------------------------------- emblems ---

def lasso_emblem(g, pos, R):
    g.ring("EmblemLasso", pos, matmul(angles(90, 0, 0), IDENTITY), 2.2, 0.45, [ROPE, ROPE2], n=20)
    g.ring("EmblemLasso", add(pos, (0, 0, -0.1)), angles(90, 0, 0), 1.7, 0.2, [C("#fff0c8")], n=18, **DS)
    g.box("EmblemKnot", (0.8, 0.8, 0.7), add(pos, (0, -2.2, 0)), ROPE2, rot=(0, 0, 45))
    g.rod("EmblemTail", add(pos, (0, -2.4, 0)), add(pos, (1.6, -3.6, 0.3)), 0.4, ROPE)


def paw_emblem(g, pos, R):
    white = C("#ffffff")
    g.cyl("PawPad", 0.3, 2.6, add(pos, (0, -0.6, 0)), white, R=angles(0, 90, 0))
    for x, y, d in ((-1.35, 1.0, 1.0), (-0.45, 1.6, 1.05), (0.45, 1.6, 1.05), (1.35, 1.0, 1.0)):
        g.cyl("PawToe", 0.3, d, add(pos, (x, y, 0)), white, R=angles(0, 90, 0))
    g.cyl("PawRim", 0.25, 3.0, add(pos, (0, -0.6, 0.12)), C("#2f7a3a"), R=angles(0, 90, 0), **DS)


def globe_emblem(g, pos, R):
    """A globe with green lands and a gold ring around it: the way to other worlds."""
    g.part("ball", "GlobeSea", (3.6, 3.6, 3.6), pos, C("#3f8fe0"))
    rng = random.Random(12)
    for i in range(7):
        yaw, pitch = rng.uniform(-70, 70), rng.uniform(-50, 50)
        d = apply(matmul(angles(0, yaw, 0), angles(pitch, 0, 0)), (0, 0, -1))
        g.box("GlobeLand", (rng.uniform(0.8, 1.4), rng.uniform(0.6, 1.1), 0.3), add(pos, scale(d, 1.7)),
              C("#58c24a") if i % 3 else C("#f2d49a"), R=aim(d, roll_up=(0, 1, 0)), **D)
    g.ring("GlobeRing", pos, angles(90, 0, 25), 2.5, 0.28, [GOLD, C("#ffe38a")], n=24, twist=False, **D)
    g.cyl("GlobeStand", 1.2, 0.35, add(pos, (0, -2.2, 0.4)), DARK, R=angles(0, 0, 90))
    for i in range(4):
        t = 2 * math.pi * i / 4 + 0.4
        g.box("GlobeSpark", (0.35, 0.35, 0.35), add(pos, (math.cos(t) * 3.0, math.sin(t) * 3.0, -0.3)), C("#fff27a"),
              rot=(45, 45, 0), material="Neon", **DS)


# ------------------------------------------------------------ shop extras ---

def lasso_extras(g, rng):
    # Lassos hanging from pegs on the front wall.
    for x in (-10.0, 10.3):
        g.box("Peg", (0.2, 0.2, 0.7), (x, 7.8, ZF - 0.7), DEEP, **D)
        g.ring("WallLasso", (x, 6.8, ZF - 0.75), angles(90, 0, 0), 1.0, 0.2, [ROPE, ROPE2], n=14, **D)
        g.ring("WallLasso", (x + 0.1, 6.7, ZF - 0.8), angles(90, 0, 0), 0.85, 0.18, [ROPE2, ROPE], n=14, **D)
    # A display rack with three lasso upgrades: Rope, Gold and Rainbow.
    rx, rz = -16.5, -8.0
    for sx in (-1, 1):
        g.box("RackLeg", (0.35, 5.2, 0.35), (rx + sx * 2.4, 2.6, rz), DARK)
    g.box("RackBeam", (5.4, 0.35, 0.4), (rx, 5.1, rz), DARK)
    g.box("RackSign", (3.6, 0.9, 0.2), (rx, 5.9, rz - 0.05), C("#f0a35a"),
          children=[surface_text("UPGRADES", "Front", ppu=80, stroke="#6b3a14")], **D)
    for i, cols in enumerate(([ROPE, ROPE2], [GOLD, C("#ffe38a")],
                              [C("#ff5a5a"), C("#ffd23f"), C("#5ad0ff"), C("#b58cff")])):
        x = rx - 1.6 + 1.6 * i
        g.box("RackHook", (0.12, 0.4, 0.12), (x, 4.8, rz), IRON, **D)
        g.ring("DisplayLasso", (x, 3.9, rz - 0.1), angles(90, 0, 0), 0.7, 0.18, cols, n=14, **D,
               **({"material": "Neon"} if i == 2 else {}))
    # A big rope spool and a practice steer made of a sawhorse and hay.
    g.cyl("Spool", 1.8, 2.6, (15.8, 1.3, -8.4), DECK, R=angles(0, 90, 0))
    g.cyl("SpoolRope", 1.5, 2.1, (15.8, 1.3, -8.4), ROPE, R=angles(0, 90, 0))
    for i in range(5):
        g.cyl("SpoolWrap", 0.15, 2.18, (15.2 + 0.3 * i, 1.3, -8.4), ROPE2, R=angles(0, 90, 0), **DS)
    steer(g, (16.5, 0, -13.5), -30)
    rope_coil(g, (13.2, 0.1, -13.2), IDENTITY, r=1.0, loops=3)
    barrel(g, "RopeBarrel", (10.8, 0, -12.0))
    rope_coil(g, (10.8, 1.6, -12.0), IDENTITY, r=0.55, loops=2)


def steer(g, pos, yaw):
    R = angles(0, yaw, 0)
    P = lambda x, y, z: at(pos, R, (x, y, z))
    for sz in (-1, 1):
        for sx in (-1, 1):
            g.rod("SawhorseLeg", P(sx * 0.9, 0, sz * 1.4), P(0, 2.2, sz * 1.4), 0.3, DARK)
    g.box("SawhorseBeam", (0.5, 0.5, 3.4), P(0, 2.3, 0), LOG, R=R)
    g.box("SteerBody", (1.6, 1.3, 2.8), P(0, 3.0, 0.2), C("#e8c35a"), R=R)
    for dz in (-0.7, 0.7):
        g.box("SteerStrap", (1.66, 1.36, 0.14), P(0, 3.0, 0.2 + dz), C("#a8761c"), R=R, **D)
    g.box("SkullHead", (1.1, 1.1, 1.3), P(0, 3.4, -1.7), C("#f2ead8"), R=R)
    g.box("SkullSnout", (0.8, 0.7, 0.6), P(0, 3.0, -2.5), C("#e6dcc3"), R=R, **D)
    for sx in (-1, 1):
        g.box("SkullEye", (0.3, 0.3, 0.1), P(sx * 0.28, 3.55, -2.37), IRON, R=R, **DS)
        g.rod("Horn", P(sx * 0.5, 3.8, -1.7), P(sx * 1.5, 4.3, -1.5), 0.28, C("#f2ead8"), **D)
        g.rod("HornTip", P(sx * 1.5, 4.3, -1.5), P(sx * 1.8, 4.9, -1.4), 0.18, IRON, **D)


def market_extras(g, rng):
    # A pen on the right with hay, a water trough and a feed bucket.
    px, pz = 17.5, 2.0
    fence(g, (px - 3.5, 0, pz - 5), (px + 3.5, 0, pz - 5), every=1.8)
    fence(g, (px + 3.5, 0, pz - 5), (px + 3.5, 0, pz + 5), every=1.8)
    fence(g, (px - 3.5, 0, pz + 5), (px + 3.5, 0, pz + 5), every=1.8)
    g.box("PenStraw", (6.8, 0.12, 9.8), (px, 0.06, pz), C("#f2d57a"), **DS)
    hay_bale(g, (px + 1.5, 0, pz + 3.2), yaw=90)
    hay_bale(g, (px + 1.5, 1.2, pz + 3.2), yaw=80, k=0.85)
    g.box("Trough", (1.4, 1.0, 4.0), (px - 2.3, 0.5, pz), DECK)
    g.box("TroughWater", (1.1, 0.1, 3.7), (px - 2.3, 0.95, pz), C("#5ad0ff"), **DS)
    g.octagon("FeedBucket", 0.45, 0.8, (px + 1.8, 0.4, pz - 2.8), C("#8c8c96"))
    for i in range(6):
        g.box("Feed", (0.2, 0.15, 0.2), (px + 1.6 + 0.12 * i, 0.83, pz - 2.9 + 0.08 * (i % 2)), C("#f2c14e"), **DS)
    # Crates of carrots and apples, feed sacks and a chalkboard with prices.
    for i, (x, color, leaf) in enumerate(((-15.5, "#ff8a2a", "#4fb84f"), (-13.4, "#e0405a", "#6b3a14"))):
        crate(g, "ProduceCrate", (x, 0, -10.5), 1.8, yaw=0)
        for j in range(6):
            p = (x - 0.55 + 0.45 * (j % 3), 1.9, -10.8 + 0.5 * (j // 3))
            g.box("Produce", (0.4, 0.4, 0.4), p, C(color), rot=(0, 30 * j, 20), **DS)
            g.box("ProduceLeaf", (0.12, 0.25, 0.12), add(p, (0, 0.3, 0)), C(leaf), **DS)
    for i in range(3):
        sack(g, "FeedSack", (-17.5 + 1.1 * i, 0, -7.8), yaw=15 * i)
    g.box("ChalkboardLeg", (0.2, 3.0, 0.2), (-10.8, 1.5, -12.6), DARK, rot=(12, 0, 0), **D)
    g.box("ChalkboardLeg", (0.2, 3.0, 0.2), (-10.8, 1.5, -11.9), DARK, rot=(-12, 0, 0), **D)
    g.box("Chalkboard", (2.6, 2.2, 0.15), (-10.8, 2.4, -12.75), C("#2e3a33"), rot=(12, 0, 0),
          children=[surface_text("BUY & SELL", "Front", color="#ffffff", ppu=70)], **D)
    # Small cages with bars, and a paw-print trail to the door.
    for i, x in enumerate((13.0, 14.8)):
        g.box("CageBase", (1.5, 0.2, 1.5), (x, 0.1, -11.5), DARK)
        g.box("CageTop", (1.5, 0.2, 1.5), (x, 1.6, -11.5), DARK, **D)
        for k in range(4):
            for sx in (-1, 1):
                g.box("CageBar", (0.08, 1.4, 0.08), (x - 0.6 + 0.4 * k, 0.85, -11.5 + sx * 0.7), IRON, **DS)
        g.box("CageBunny", (0.6, 0.6, 0.8), (x, 0.5, -11.5), C("#ffffff") if i else C("#c98a52"), **DS)
    for i in range(6):
        g.box("PawPrint", (0.5, 0.04, 0.45), (-1.5 + (i % 2) * 1.0, 0.02, PORCH_Z - 3.0 - 1.1 * i), C("#8a5a2e"), **DS)


def coach(g, origin, yaw):
    """A real stagecoach: rounded body with doors and windows, driver's box, roof rack with luggage."""
    R = angles(0, yaw, 0)
    P = lambda x, y, z: at(origin, R, (x, y, z))
    RED, RED2, TRIM = C("#b83a2e"), C("#9a2e24"), GOLD
    for z, r in ((2.8, 2.2), (-3.0, 1.7)):
        for sx in (-1, 1):
            wheel(g, "CoachWheel", P(2.7 * sx, r, z), r, spokes=12)
        g.box("Axle", (5.6, 0.35, 0.35), P(0, r, z), DEEP, R=R)
    g.box("Perch", (0.4, 0.4, 6.4), P(0, 1.9, 0), DEEP, R=R)
    for z in (-2.0, 2.0):
        g.box("Thoroughbrace", (3.6, 0.2, 0.5), P(0, 2.35, z), C("#5a3418"), R=R, **D)
    # Body: lower panel, upper panel with windows, curved front and back.
    g.box("BodyLower", (4.0, 2.0, 4.6), P(0, 3.4, 0), RED, R=R)
    g.box("BodyUpper", (3.8, 2.2, 4.2), P(0, 5.5, 0), RED2, R=R)
    for sz in (-1, 1):
        g.wedge("BodyCurve", (4.0, 1.0, 0.8), P(0, 2.9, sz * 2.7), RED, R=matmul(R, angles(180, 90 - 90 * sz, 0)))
    g.box("Roof", (4.4, 0.35, 5.0), P(0, 6.75, 0), C("#2e2a36"), R=R)
    for sz in (-1, 1):
        g.box("RoofRail", (4.2, 0.4, 0.15), P(0, 7.1, sz * 2.3), GOLD, R=R, **D)
    for sx in (-1, 1):
        g.box("RoofRail", (0.15, 0.4, 4.6), P(sx * 2.1, 7.1, 0), GOLD, R=R, **D)
        # Door with a window, a curtain and a gold handle on each side.
        g.box("Door", (0.12, 3.6, 1.8), P(sx * 2.02, 4.4, 0), RED, R=R, **D)
        g.box("DoorWindow", (0.13, 1.2, 1.3), P(sx * 2.04, 5.6, 0), C("#2a2230"), R=R, **D)
        g.box("DoorCurtain", (0.14, 1.2, 0.4), P(sx * 2.05, 5.6, 0.45), C("#f2c14e"), R=R, **DS)
        g.box("DoorHandle", (0.2, 0.15, 0.4), P(sx * 2.1, 4.4, -0.6), GOLD, R=R, **DS)
        for z in (-1.6, 1.6):
            g.box("SideWindow", (0.13, 1.0, 0.8), P(sx * 1.92, 5.7, z), C("#2a2230"), R=R, **D)
        for y in (2.45, 4.45, 6.55):
            g.box("Pinstripe", (0.14, 0.15, 4.4), P(sx * 2.03, y, 0), TRIM, R=R, **DS)
        g.box("DoorPlate", (0.14, 0.6, 1.6), P(sx * 2.06, 3.3, 0), C("#2e2a36"), R=R,
              children=[surface_text("WORLDS", "Right" if sx > 0 else "Left", color="#f2c14e", ppu=60)], **DS)
    # Driver's box, footboard and lamps at the front; the boot at the back.
    g.box("DriverSeat", (3.6, 0.35, 1.2), P(0, 6.2, -2.9), C("#5a3418"), R=R)
    g.box("SeatBack", (3.6, 1.0, 0.2), P(0, 6.8, -2.4), C("#5a3418"), R=R, **D)
    g.box("Footboard", (3.6, 0.2, 1.2), P(0, 4.3, -3.7), DARK, R=R)
    g.rod("FootboardStay", P(0, 4.3, -3.2), P(0, 6.0, -2.6), 0.2, DARK, **D)
    for sx in (-1, 1):
        g.box("CoachLamp", (0.5, 0.8, 0.5), P(sx * 2.1, 5.9, -2.6), C("#ffe7a3"), R=R, material="Neon", **DS)
        g.box("CoachLampCap", (0.65, 0.2, 0.65), P(sx * 2.1, 6.4, -2.6), IRON, R=R, **D)
    g.box("Boot", (3.4, 2.0, 1.4), P(0, 4.1, 3.0), C("#4a2e1a"), R=R)
    g.box("BootFlap", (3.5, 0.2, 1.5), P(0, 5.15, 3.0), C("#3a2416"), R=R, **D)
    # Luggage on the roof, strapped down.
    for (x, z, w, h, d, col) in ((-0.9, -1.0, 1.4, 0.9, 1.8, "#7a4a2a"), (0.8, -0.8, 1.2, 0.8, 1.2, "#2f6f8f"),
                                 (0.2, 1.1, 2.2, 1.0, 1.4, "#8e2b2b"), (-1.0, 1.3, 0.9, 0.6, 0.9, "#6b8f3a")):
        g.box("Luggage", (w, h, d), P(x, 6.95 + h / 2, z), C(col), R=R)
        g.box("LuggageStrap", (w + 0.04, h + 0.04, 0.15), P(x, 6.95 + h / 2, z), C("#3a2416"), R=R, **DS)
        g.box("LuggageLatch", (0.25, 0.2, 0.08), P(x, 6.95 + h * 0.7, z - d / 2 - 0.04), GOLD, R=R, **DS)
    g.rod("Tongue", P(0, 1.8, -3.4), P(0, 0.6, -8.4), 0.35, DARK)
    g.box("Doubletree", (2.8, 0.25, 0.3), P(0, 0.65, -8.0), DARK, R=R)


WORLDS = [("Forest", "#58bb43"), ("Dark Woods", "#8a5cc8"), ("???", "#8c8c96")]


def world_board(g, pos):
    """A big board with a roof: CHOOSE A WORLD, and a tile for every world (the last one still locked)."""
    x, _, z = pos
    for sx in (-1, 1):
        g.octagon("BoardPost", 0.3, 7.6, (x + sx * 4.2, 3.8, z), DARK)
        g.octagon("BoardFoot", 0.45, 0.4, (x + sx * 4.2, 0.2, z), STONE[2])
    g.box("WorldBoard", (8.0, 5.6, 0.3), (x, 4.6, z), C("#2e3a4a"))
    g.box("WorldBoardFrame", (8.5, 0.35, 0.5), (x, 7.55, z), DEEP, **D)
    g.box("WorldBoardFrame", (8.5, 0.35, 0.5), (x, 1.65, z), DEEP, **D)
    g.box("WorldBoardTitle", (7.4, 1.2, 0.2), (x, 6.7, z - 0.2), C("#f0a35a"),
          children=[surface_text("CHOOSE A WORLD", "Front", ppu=70, stroke="#6b3a14")], **D)
    for i, (name, color) in enumerate(WORLDS):
        tx = x + 2.5 - 2.5 * i  # first world on the left, seen from the front
        g.box("WorldTile", (2.2, 3.4, 0.2), (tx, 4.0, z - 0.2), C(color), **D)
        g.box("WorldName", (2.1, 0.8, 0.22), (tx, 2.7, z - 0.25), C("#1b1530"),
              children=[surface_text(name, "Front", ppu=80)], **D)
        if name == "???":
            # A padlock: still locked.
            g.box("Lock", (1.0, 0.8, 0.25), (tx, 4.2, z - 0.35), GOLD, **DS)
            g.ring("LockShackle", (tx, 4.75, z - 0.35), angles(90, 0, 0), 0.35, 0.12, [GOLD], n=10, twist=False, **DS)
        elif name == "Forest":
            for j in range(3):
                tri(g, "TilePine", (tx - 0.6 + 0.6 * j, 3.2, z - 0.32), 0.8, 1.4, 0.05, C("#2f8f3a"), **DS)
        else:
            for j in range(4):
                g.box("TileCrystal", (0.3, 0.9, 0.05), (tx - 0.6 + 0.4 * j, 3.6 + 0.2 * (j % 2), z - 0.32),
                      C("#d9b8ff"), rot=(0, 0, 10 * (j - 1.5)), material="Neon", **DS)
    g.box("BoardRoof", (9.2, 0.35, 1.6), (x, 8.0, z + 0.1), C("#4a7cc4"), rot=(-12, 0, 0))
    for sx in (-1, 1):
        lantern(g, "BoardLantern", (x + sx * 4.6, 7.8, z - 0.5), chain=0.3)


def boarding_pad(g, pos):
    """A glowing pad next to the coach: put your teleport script on BoardingPad."""
    x, _, z = pos
    g.cyl("BoardingPad", 0.3, 6.0, (x, 0.15, z), C("#6aa0e6"), R=angles(0, 0, 90))
    g.ring("PadGlow", (x, 0.32, z), IDENTITY, 2.7, 0.25, [C("#9fe8ff"), C("#ffffff")], n=24, twist=False,
           material="Neon", **DS)
    g.ring("PadGlow", (x, 0.32, z), IDENTITY, 1.6, 0.2, [C("#9fe8ff")], n=16, twist=False, material="Neon", **DS)
    beam = {"class": "ParticleEmitter", "name": "Sparkles", "props": {
        "Texture": "rbxasset://textures/particles/sparkles_main.dds", "Rate": 8, "Lifetime": [1.2, 2],
        "Speed": [1.5, 3], "SpreadAngle": [15, 15], "Size": [[0, 0.35], [1, 0]], "Transparency": [[0, 0], [1, 1]],
        "Color": [[0, *C("#ffffff")], [1, *C("#9fe8ff")]], "LightEmission": 1, "LightInfluence": 0}}
    g.box("PadSparkles", (4.0, 0.1, 4.0), (x, 0.35, z), C("#ffffff"), transparency=1, children=[beam], **DS)
    for sx in (-1, 1):
        g.octagon("PadPost", 0.25, 3.6, (x + sx * 3.4, 1.8, z + 2.2), DARK)
    g.box("PadSign", (5.4, 1.1, 0.25), (x, 3.4, z + 2.2), C("#f0a35a"),
          children=[surface_text("BOARD HERE", "Front", ppu=70, stroke="#6b3a14"),
                    surface_text("BOARD HERE", "Back", ppu=70, stroke="#6b3a14")])


def worlds_extras(g, rng):
    coach(g, (-18.5, 0, -7.5), 0)
    boarding_pad(g, (-13.0, 0, -16.5))
    world_board(g, (21.0, 0, -8.5))
    # Departures board on the wall, a bench and a pile of luggage on the porch.
    g.box("Departures", (3.6, 2.6, 0.2), (-8.2, 3.0, ZF - 1.1), C("#2e3a33"),
          children=[surface_text("Forest\nDark Woods\n???", "Front", color="#ffffff", ppu=60)], **D)
    for sx in (-1, 1):
        g.box("DeparturesFrame", (0.25, 2.9, 0.3), (-8.2 + sx * 1.9, 3.0, ZF - 1.15), DARK, **D)
    for x in (-10.0, -7.4):
        g.box("BenchLeg", (0.3, 1.2, 1.0), (x, Y0 + 0.6, PORCH_Z + 1.6), DARK)
    g.box("BenchSeat", (3.4, 0.25, 1.2), (-8.7, Y0 + 1.3, PORCH_Z + 1.6), DECK)
    for (x, z, w, h, d, col) in ((10.0, PORCH_Z + 2.2, 1.8, 1.2, 1.1, "#7a4a2a"), (10.2, PORCH_Z + 2.2, 1.4, 0.8, 0.9,
                                                                                  "#2f6f8f"),
                                 (8.3, PORCH_Z + 2.4, 1.2, 1.4, 0.8, "#8e2b2b")):
        y = Y0 + (1.2 if col == "#2f6f8f" else 0)
        g.box("Suitcase", (w, h, d), (x, y + h / 2, z), C(col))
        g.box("SuitcaseStrap", (w + 0.05, h + 0.05, 0.15), (x, y + h / 2, z), C("#3a2416"), **DS)
        g.box("SuitcaseHandle", (0.5, 0.15, 0.15), (x, y + h + 0.08, z), C("#3a2416"), **DS)
    # Signpost with three arrows, a hitching post and a water trough for the horses.
    x, z = 10.5, -15.0
    g.octagon("PostBase", 0.55, 0.4, (x, 0.2, z), STONE[2])
    g.box("SignPost", (0.45, 7.0, 0.45), (x, 3.7, z), DARK)
    g.box("SignPostTop", (0.6, 0.3, 0.6), (x, 7.3, z), DEEP, **D)
    for text, y, yaw, color in (("Forest", 6.3, 150, "#e8a054"), ("Hub", 5.3, 20, "#d98b3a"),
                                ("Dark Woods", 4.3, -110, "#8a5cc8")):
        R = angles(0, yaw, 0)
        length = 3.4
        g.box("ArrowBoard", (length, 0.8, 0.2), at((x, y, z), R, (-length / 2 - 0.1, 0, 0)), C(color), R=R,
              children=[surface_text(text, "Front", ppu=70, stroke="#3a2416"),
                        surface_text(text, "Back", ppu=70, stroke="#3a2416")])
        tip = at((x, y, z), R, (-length - 0.1, 0, 0))
        for sgn in (-1, 1):
            g.wedge("ArrowTip", (0.2, 0.4, 0.7), at(tip, R, (-0.3, 0.2 * sgn, 0)), C(color),
                    R=matmul(R, angles(0, 90, 0 if sgn > 0 else 180)), **D)
    g.box("Trough", (4.0, 1.0, 1.4), (-22.5, 0.5, -11.0), DECK)
    g.box("TroughWater", (3.7, 0.1, 1.1), (-22.5, 0.95, -11.0), C("#5ad0ff"), **DS)
    for sx in (-1, 1):
        g.box("HitchPost", (0.4, 2.8, 0.4), (-22.5 + sx * 2.4, 1.4, -8.8), DARK)
    g.box("HitchRail", (5.2, 0.3, 0.3), (-22.5, 2.6, -8.8), LOG)
    hay_bale(g, (22.0, 0, -3.5), yaw=20)


# ------------------------------------------------------------------ camp ---

def tent(g, pos, yaw, cloth, cloth2, rng):
    R = angles(0, yaw, 0)
    P = lambda x, y, z: at(pos, R, (x, y, z))
    L, half, h = 8.0, 3.4, 5.0
    ang = math.degrees(math.atan2(h, half))
    side = math.hypot(half, h)
    g.box("GroundCloth", (2 * half + 1.2, 0.12, L + 1.2), P(0, 0.06, 0), C("#8a7a5a"), R=R, **DS)
    for sx in (-1, 1):
        Rs = matmul(R, angles(0, 0, sx * (90 - ang)))
        g.box("TentSide", (0.2, side, L), P(sx * half / 2, h / 2, 0), cloth, R=Rs)
        for k in (-1, 0, 1):
            g.box("TentSeam", (0.22, side, 0.18), P(sx * half / 2 + 0.02 * sx, h / 2, k * L / 3), cloth2, R=Rs, **DS)
        g.box("TentHem", (0.25, 0.4, L + 0.1), P(sx * (half - 0.1), 0.25, 0), cloth2, R=R, **D)
    log(g, "RidgePole", P(0, h + 0.1, -L / 2 - 0.5), P(0, h + 0.1, L / 2 + 0.5), 0.3, DARK, **D)
    for z in (-L / 2 - 0.3, L / 2 + 0.3):
        g.box("TentPole", (0.3, h + 0.6, 0.3), P(0, (h + 0.6) / 2, z), DARK)
        g.box("PoleTop", (0.45, 0.3, 0.45), P(0, h + 0.75, z), GOLD, R=R, **DS)
    # Back wall, and the front flaps tied open.
    tri(g, "TentBack", P(0, 0, L / 2 - 0.05), 2 * half, h, 0.15, cloth2, R=R)
    for sx in (-1, 1):
        Rf = matmul(R, angles(0, sx * 55, 0))
        tri(g, "TentFlap", at(P(sx * half * 0.5, 0, -L / 2), Rf, (sx * half * 0.25, 0, 0)), half, h * 0.9, 0.12,
            cloth2, R=Rf, **D)
        g.box("FlapTie", (0.2, 0.2, 0.9), P(sx * (half - 0.2), h * 0.45, -L / 2 - 0.2), ROPE, R=R, **DS)
    # Guy ropes and stakes.
    for z in (-L / 2 - 0.3, L / 2 + 0.3):
        stake = P(0, 0.3, z + (2.4 if z > 0 else -2.4))
        g.rod("GuyRope", P(0, h + 0.5, z), stake, 0.08, ROPE, **DS)
        g.box("Stake", (0.2, 0.7, 0.2), stake, DEEP, R=R, **D)
    for sx in (-1, 1):
        for z in (-L / 3, L / 3):
            stake = P(sx * (half + 1.6), 0.25, z)
            g.rod("GuyRope", P(sx * half * 0.55, h * 0.45, z), stake, 0.07, ROPE, **DS)
            g.box("Stake", (0.2, 0.6, 0.2), stake, DEEP, R=R, **D)
    # Inside: a bedroll, a pillow and a lantern.
    g.octagon("Bedroll", 0.45, 1.6, P(-1.0, 0.45, 0.6), C("#6b8f3a"), collide=False)
    g.box("Blanket", (1.8, 0.2, 3.8), P(1.0, 0.2, 0.8), C("#c0392b"), R=R, **D)
    for i in range(3):
        g.box("BlanketStripe", (1.82, 0.22, 0.2), P(1.0, 0.21, -0.4 + 1.2 * i), C("#f2e6c8"), R=R, **DS)
    g.box("Pillow", (1.2, 0.4, 0.8), P(1.0, 0.35, 2.5), C("#f3ecd9"), R=R, **D)
    lantern(g, "TentLantern", P(0, h - 0.2, -L / 2 + 1.0), chain=0.3)


def saddle_rack(g, pos, yaw):
    R = angles(0, yaw, 0)
    P = lambda x, y, z: at(pos, R, (x, y, z))
    for sz in (-1, 1):
        for sx in (-1, 1):
            g.rod("RackLeg", P(sx * 0.8, 0, sz * 1.3), P(0, 2.4, sz * 1.3), 0.3, DARK)
    g.box("RackBeam", (0.5, 0.5, 3.2), P(0, 2.5, 0), LOG, R=R)
    g.box("SaddleBlanket", (2.4, 0.15, 1.8), P(0, 2.78, 0.1), C("#2f6f8f"), R=R, **D)
    g.box("SaddleSeat", (1.6, 0.5, 1.6), P(0, 3.05, 0.1), C("#8a4a22"), R=R)
    g.box("SaddleHorn", (0.35, 0.7, 0.35), P(0, 3.5, -0.6), C("#6b3a14"), R=R, **D)
    g.box("SaddleCantle", (1.4, 0.6, 0.3), P(0, 3.4, 0.85), C("#6b3a14"), R=R, **D)
    for sx in (-1, 1):
        g.box("Fender", (0.15, 1.4, 0.9), P(sx * 0.9, 2.3, 0.2), C("#8a4a22"), R=R, **D)
        g.box("Stirrup", (0.2, 0.4, 0.6), P(sx * 0.95, 1.4, 0.2), GOLD, R=R, **DS)


def bunting(g, p0, p1, colors, n=10, sag=1.2):
    pts = []
    for i in range(n + 1):
        t = i / n
        p = tuple(a + (b - a) * t for a, b in zip(p0, p1))
        pts.append(add(p, (0, -sag * 4 * t * (1 - t), 0)))
    for a, b in zip(pts, pts[1:]):
        g.rod("BuntingRope", a, b, 0.07, ROPE, **DS)
    d = sub(p1, p0)
    yaw = math.degrees(math.atan2(-d[2], d[0]))
    for i, p in enumerate(pts[1:-1]):
        tri(g, "Pennant", add(p, (0, -0.9, 0)), 0.9, 0.9, 0.06, C(colors[i % len(colors)]),
            R=matmul(angles(0, yaw, 0), angles(0, 0, 180)), **DS)


def camp(rng):
    g = Group("WranglerCamp")
    ground = Group("Ground")
    # Sandy plaza with an inner ring and four paths (in their own model, so you can delete them).
    for i, (r, col) in enumerate(((24.0, "#f2d49a"), (21.0, "#f5dcaa"))):
        ground.cyl("Plaza", 0.2 + 0.02 * i, 2 * r, (0, 0.1 + 0.01 * i, 0), C(col), R=angles(0, 0, 90))
    for k in range(4):
        yaw = 45 + 90 * k
        d = apply(angles(0, yaw, 0), (0, 0, -1))
        ground.box("Path", (8, 0.2, 16), (d[0] * 30, 0.1, d[2] * 30), C("#e2b77f"), rot=(0, yaw, 0))
    for i in range(28):
        t = 2 * math.pi * i / 28
        ground.box("PlazaStone", (1.6, 0.3, 0.9), (math.cos(t) * 24.2, 0.15, math.sin(t) * 24.2), STONE[i % 3],
                   rot=(0, -math.degrees(t) + 90, 0), collide=False)

    # Campfire in the middle with four log benches.
    campfire(g, (0, 0, 0))
    for k in range(4):
        yaw = 90 * k
        R = angles(0, yaw, 0)
        c = apply(R, (0, 0, -5.5))
        a, b = add(c, apply(R, (-2.2, 0.75, 0))), add(c, apply(R, (2.2, 0.75, 0)))
        log(g, "BenchLog", a, b, 0.9, LOG)
        for sgn in (-1, 1):
            cut_end(g, add(c, apply(R, (sgn * 2.25, 0.75, 0))), 0.9, R)
            g.octagon("BenchStump", 0.4, 0.4, add(c, apply(R, (sgn * 1.5, 0.2, 0))), DARK)
    # A woodpile next to the fire.
    for i, (x, y) in enumerate(((0, 0.35), (0.7, 0.35), (1.4, 0.35), (0.35, 0.95), (1.05, 0.95), (0.7, 1.55))):
        log(g, "Firewood", (4.0 + x, y, 3.2), (4.0 + x, y, 5.2), 0.65, LOG2 if i % 2 else LOG)
        cut_end(g, (4.0 + x, y, 3.18), 0.65, angles(0, 90, 0))

    # Three tents, the wagon and eight lamp posts at the four paths.
    tent(g, (-13.5, 0, -5.0), 70, C("#9fd08a"), C("#7ab87a"), rng)
    tent(g, (14.0, 0, 1.0), -90, C("#f3ecd9"), C("#e0d3b0"), rng)
    tent(g, (-2.5, 0, 14.0), 180, C("#f0916a"), C("#e0735a"), rng)
    wagon(g, origin=(2.0, 0, -18.5), yaw=90)
    hanging_sign_stand(g, (-4.5, 0, -15.0), "Supplies")
    for k in range(4):
        yaw = 45 + 90 * k
        for side in (-1, 1):
            p = apply(angles(0, yaw, 0), (side * 5.5, 0, -22.0))
            lamp_post(g, p, yaw=yaw + 180)

    # Saddle rack, lasso practice steer and rope, hay, barrels, crates and a water trough.
    saddle_rack(g, (-7.0, 0, -12.0), 40)
    steer(g, (11.0, 0, 11.0), 210)
    rope_coil(g, (7.5, 0.1, 9.0), IDENTITY, r=1.0, loops=3)
    hay_bale(g, (16.0, 0, 8.5), yaw=30)
    hay_bale(g, (17.2, 0, 10.4), yaw=70)
    hay_bale(g, (16.4, 1.2, 9.4), yaw=50, k=0.85)
    for p in ((-9.0, 0, 10.0), (-10.2, 0, 11.0), (8.8, 0, -13.5)):
        barrel(g, "Barrel", p)
    crate(g, "Crate", (-11.5, 0, 9.0), 1.4, yaw=15)
    crate(g, "Crate", (-11.4, 1.4, 9.1), 1.0, yaw=-10)
    crate(g, "Crate", (10.2, 0, -14.5), 1.3, yaw=30)
    sack(g, "Sack", (9.8, 0, -12.3), yaw=20)
    g.box("Trough", (1.4, 1.0, 4.0), (-18.0, 0.5, 6.0), DECK, rot=(0, 20, 0))
    g.box("TroughWater", (1.1, 0.1, 3.7), (-18.0, 0.95, 6.0), C("#5ad0ff"), rot=(0, 20, 0), **DS)
    # Bunting flags between the tents' poles and the wagon.
    bunting(g, (-13.5, 5.8, -9.0), (-2.0, 6.5, -17.0), ["#ff5a5a", "#ffd23f", "#45a6ff", "#52d273"])
    bunting(g, (10.5, 5.8, 1.0), (4.0, 6.0, -17.0), ["#ffd23f", "#ff8fb8", "#45a6ff", "#ff9a3c"])
    bunting(g, (-2.5, 5.8, 10.0), (10.5, 5.8, 1.0), ["#52d273", "#ff5a5a", "#ffd23f", "#b58cff"])
    return g, ground


def hanging_sign_stand(g, pos, text):
    x, _, z = pos
    for sx in (-1, 1):
        g.box("StandPost", (0.4, 4.4, 0.4), (x + sx * 1.8, 2.2, z), DARK)
    g.box("StandBeam", (4.4, 0.35, 0.4), (x, 4.4, z), DARK)
    for sx in (-1, 1):
        g.box("StandChain", (0.1, 0.6, 0.1), (x + sx * 1.2, 4.0, z), IRON, **DS)
    g.box("StandSign", (3.2, 1.1, 0.25), (x, 3.2, z), C("#f0a35a"),
          children=[surface_text(text, "Front", ppu=70, stroke="#6b3a14"),
                    surface_text(text, "Back", ppu=70, stroke="#6b3a14")])


# ----------------------------------------------------------- upgrade camp ---

def add_asset(g, asset, pos, yaw=0.0, k=1.0):
    """Copies a forest-kit model (trees, bushes, flowers) into a Group, turned by yaw and scaled by k."""
    Ry = angles(0, yaw, 0)
    for p in asset.parts:
        if p["transparency"] >= 1:
            continue
        g.parts.append({"shape": p["shape"], "name": p["name"], "size": tuple(v * k for v in p["size"]),
                        "R": matmul(Ry, p["R"]), "p": add(pos, apply(Ry, scale(p["p"], k))), "color": p["color"],
                        "material": p["material"], "collide": p["collide"], "shadow": p["shadow"],
                        "transparency": p["transparency"], "reflectance": 0.0, "paint": None, "children": [],
                        "id": None})


def arrow_up(g, center, size, color, R=IDENTITY):
    """A chunky up arrow (the upgrade symbol) facing local -Z."""
    w = size
    g.box("ArrowStem", (w * 0.42, w * 0.6, 0.15), at(center, R, (0, -w * 0.25, 0)), color, R=R, material="Neon", **DS)
    for sgn in (-1, 1):
        g.wedge("ArrowHead", (0.15, w * 0.5, w * 0.5), at(center, R, (sgn * w * 0.25, w * 0.3, 0)), color,
                R=matmul(R, angles(0, 90 if sgn < 0 else -90, 0)), material="Neon", **DS)


def trainer_booth(g, pos, yaw, rng):
    """Old Pete's upgrade stand: a plank booth with a striped awning, a counter, shelves of upgrades and a big sign."""
    R = angles(0, yaw, 0)
    P = lambda x, y, z: at(pos, R, (x, y, z))
    W, Dp = 9.0, 6.0
    stripe = [C("#e0482c"), C("#fff4dc")]
    # Platform with planks and a step.
    g.box("BoothDeck", (W + 1, 0.6, Dp + 1), P(0, 0.3, 0), DEEP, R=R)
    for i in range(7):
        g.box("BoothPlank", (W + 1, 0.2, (Dp + 1) / 7 - 0.06), P(0, 0.68, -Dp / 2 - 0.5 + (i + 0.5) * (Dp + 1) / 7),
              DECK if i % 2 else DECK2, R=R)
    g.box("BoothStep", (3.0, 0.35, 0.9), P(0, 0.18, -Dp / 2 - 1.0), DECK2, R=R)
    # Back wall of vertical planks, low side walls.
    for i in range(10):
        x = -W / 2 + 0.45 + i * (W - 0.9) / 9
        g.box("BackPlank", (0.9, 6.4, 0.3), P(x, 3.9, Dp / 2), DECK if i % 2 else DECK2, R=R)
    g.box("BackBeam", (W + 0.4, 0.4, 0.4), P(0, 7.2, Dp / 2), DARK, R=R, **D)
    for sx in (-1, 1):
        for j in range(4):
            g.box("SidePlank", (0.3, 3.0, (Dp - 0.4) / 4 - 0.05), P(sx * W / 2, 2.3, -Dp / 2 + 0.3 + (j + 0.5) * (Dp - 0.4) / 4),
                  DECK if j % 2 else DECK2, R=R)
        g.box("SideRail", (0.4, 0.3, Dp), P(sx * W / 2, 3.9, 0), DARK, R=R, **D)
    # Four log posts and a sloped, striped awning with a scalloped edge.
    for sx in (-1, 1):
        for z, h in ((-Dp / 2 + 0.3, 6.6), (Dp / 2 - 0.2, 7.6)):
            g.octagon("BoothPost", 0.3, h, P(sx * (W / 2 + 0.1), 0.8 + h / 2, z), LOG)
    n = 9
    for i in range(n):
        x = -W / 2 - 0.4 + (i + 0.5) * (W + 0.8) / n
        g.box("Awning", ((W + 0.8) / n + 0.02, 0.2, Dp + 1.6), P(x, 7.9, -0.4), stripe[i % 2], R=matmul(R, angles(-9, 0, 0)))
        g.cyl("AwningScallop", 0.2, (W + 0.8) / n, P(x, 7.25, -Dp / 2 - 1.15), stripe[i % 2], R=matmul(R, angles(0, 90, 0)),
              **DS)
    # Counter with panels and a bell, and a register with a big up arrow.
    g.box("Counter", (W - 0.8, 3.0, 1.2), P(0, 2.3, -Dp / 2 + 1.2), DECK2, R=R)
    g.box("CounterTop", (W - 0.4, 0.35, 1.8), P(0, 3.95, -Dp / 2 + 1.1), DECK, R=R)
    for x in (-3, 0, 3):
        g.box("CounterPanel", (2.4, 2.2, 0.12), P(x, 2.2, -Dp / 2 + 0.58), DECK, R=R, **D)
        arrow_up(g, P(x, 2.2, -Dp / 2 + 0.5), 1.1, C("#5dff7a"), R=R)
    g.octagon("Bell", 0.25, 0.3, P(3.4, 4.3, -Dp / 2 + 1.0), GOLD, collide=False)
    # Shelves on the back wall with upgrades: boots, horseshoes, lassos and glowing potions.
    for y in (4.4, 6.0):
        g.box("Shelf", (W - 1.0, 0.25, 1.0), P(0, y, Dp / 2 - 0.65), DECK, R=R, **D)
    for i, x in enumerate((-3.2, -1.6, 0, 1.6, 3.2)):
        if i % 2 == 0:
            g.box("Boot", (0.6, 0.9, 0.4), P(x - 0.25, 5.0, Dp / 2 - 0.7), C("#7a4a2a"), R=R, **D)
            g.box("BootToe", (0.6, 0.4, 0.8), P(x - 0.25, 4.75, Dp / 2 - 0.95), C("#7a4a2a"), R=R, **DS)
            g.box("BootSpur", (0.2, 0.2, 0.2), P(x - 0.25, 4.7, Dp / 2 - 0.4), GOLD, R=R, **DS)
        else:
            g.ring("ShelfHorseshoe", P(x, 5.05, Dp / 2 - 0.7), matmul(R, angles(90, 0, 0)), 0.45, 0.14, [GOLD], n=10,
                   twist=False, **DS)
        col = ["#5dff7a", "#5ad0ff", "#ffd23f", "#ff7be5", "#b58cff"][i]
        g.octagon("Potion", 0.28, 0.7, P(x, 6.5, Dp / 2 - 0.7), C(col), material="Neon", collide=False)
        g.octagon("PotionCork", 0.14, 0.25, P(x, 6.97, Dp / 2 - 0.7), DECK, collide=False)
    for x in (-3.8, 3.8):
        g.ring("WallLasso", P(x, 3.0, Dp / 2 - 0.3), matmul(R, angles(90, 0, 0)), 0.8, 0.18, [ROPE, ROPE2], n=14, **D)
    # The big UPGRADES sign on top of the awning.
    hanging_sign(g, "UPGRADES", P(0, 9.6, -Dp / 2 + 0.2), 8.0, 1.9, C("#f0a35a"), R=matmul(R, angles(-6, 0, 0)),
                 stroke="#6b3a14")
    for sx in (-1, 1):
        arrow_up(g, P(sx * 5.0, 9.6, -Dp / 2 + 0.1), 1.4, C("#5dff7a"), R=R)
        lantern(g, "BoothLantern", P(sx * (W / 2 - 0.4), 7.1, -Dp / 2 - 0.4), chain=0.4)
    # Chalkboard with the three upgrades, and a round mat where the trainer can stand.
    g.box("Chalkboard", (2.6, 3.0, 0.15), P(W / 2 + 1.4, 2.4, -Dp / 2 - 0.6), C("#2e3a33"), R=matmul(R, angles(10, -20, 0)),
          children=[surface_text("SPEED\nPOWER\nLASSO", "Front", color="#ffffff", ppu=60)], **D)
    g.rod("ChalkboardLeg", P(W / 2 + 0.3, 0, -Dp / 2 - 0.2), P(W / 2 + 0.6, 3.6, -Dp / 2 - 0.6), 0.18, DARK, **D)
    g.rod("ChalkboardLeg", P(W / 2 + 2.5, 0, -Dp / 2 - 1.0), P(W / 2 + 2.2, 3.6, -Dp / 2 - 0.6), 0.18, DARK, **D)
    g.box("TrainerSpot", (3.0, 0.1, 2.0), P(0, 0.83, Dp / 2 - 1.9), C("#c9803f"), transparency=1, collide=False,
          shadow=False, pid="UpgradeCamp.TrainerSpot")


def chopping_block(g, pos, rng):
    x, _, z = pos
    g.octagon("ChopBlock", 1.0, 1.6, (x, 0.8, z), LOG2)
    g.octagon("ChopTop", 0.9, 0.1, (x, 1.62, z), LOG_END, collide=False)
    g.octagon("ChopRing", 0.5, 0.12, (x, 1.63, z), LOG_RING, collide=False)
    g.rod("AxeHandle", (x + 0.2, 1.65, z), (x + 1.2, 3.6, z + 0.3), 0.2, DECK, **D)
    g.box("AxeHead", (0.12, 0.8, 1.0), (x + 0.15, 1.9, z - 0.1), C("#8c8c96"), rot=(0, 15, 25), reflectance=0.2, **D)
    g.box("AxeEdge", (0.14, 0.8, 0.2), (x + 0.1, 1.85, z - 0.55), C("#d6d6de"), rot=(0, 15, 25), **DS)
    for _ in range(8):
        g.box("WoodChip", (0.35, 0.08, 0.2), (x + rng.uniform(-1.8, 1.8), 0.04, z + rng.uniform(-1.8, 1.8)), LOG_END,
              rot=(0, rng.uniform(0, 180), 0), **DS)
    for i in range(2):
        log(g, "SplitLog", (x - 1.9, 0.35, z + 0.8 + 0.7 * i), (x - 0.9, 0.35, z + 0.9 + 0.7 * i), 0.6, LOG, collide=False)


def woodpile(g, pos):
    x, _, z = pos
    for i, (dx, y) in enumerate(((0, 0.4), (0.8, 0.4), (1.6, 0.4), (2.4, 0.4), (0.4, 1.1), (1.2, 1.1), (2.0, 1.1),
                                 (0.8, 1.8), (1.6, 1.8), (1.2, 2.5))):
        log(g, "Firewood", (x + dx, y, z - 1.4), (x + dx, y, z + 1.4), 0.75, LOG2 if i % 2 else LOG)
        cut_end(g, (x + dx, y, z - 1.42), 0.75, angles(0, 90, 0))
    for sx in (-0.5, 2.9):
        g.box("PileStake", (0.25, 3.2, 0.25), (x + sx, 1.6, z), DARK)


def lasso_target(g, pos, rng):
    """A post with a hay-stuffed target head and rope rings: practice lassoing."""
    x, _, z = pos
    g.octagon("TargetPost", 0.3, 4.2, (x, 2.1, z), DARK)
    g.box("TargetHead", (1.6, 1.4, 1.4), (x, 4.6, z), C("#e8c35a"))
    for dx in (-0.4, 0.4):
        g.box("TargetStrap", (0.14, 1.44, 1.44), (x + dx, 4.6, z), C("#a8761c"), **D)
    for sx in (-1, 1):
        g.rod("TargetHorn", (x + sx * 0.6, 5.2, z), (x + sx * 1.4, 5.8, z - 0.2), 0.22, C("#f2ead8"), **D)
    g.ring("TargetRing", (x, 0.1, z), IDENTITY, 1.8, 0.2, [C("#ffffff"), C("#e0482c")], n=18, twist=False, **DS)


def upgrade_camp(rng):
    import build_kit  # forest kit (on the path through build_entrance)
    kit = {a.name: a for a in build_kit.make_kit()}
    g = Group("UpgradeCamp")
    ground = Group("Ground")
    # A dirt clearing with a ring of stones (its own model: delete it to keep your own ground).
    ground.cyl("Clearing", 0.2, 44, (0, 0.1, 0), C("#e6c088"), R=angles(0, 0, 90))
    ground.cyl("ClearingInner", 0.22, 30, (0, 0.11, 0), C("#ecca95"), R=angles(0, 0, 90))
    ground.box("EntrancePath", (8, 0.2, 10), (0, 0.1, -24), C("#e2b77f"))
    for i in range(24):
        t = 2 * math.pi * i / 24
        if abs(math.sin(t)) < 0.97 or math.sin(t) > 0:  # leave a gap for the entrance at the front
            ground.box("ClearingStone", (1.5, 0.3, 0.9), (math.cos(t) * 22.2, 0.15, math.sin(t) * 22.2), STONE[i % 3],
                       rot=(0, -math.degrees(t) + 90, 0), collide=False)

    # The big shade tree at the back, and two tents.
    add_asset(g, kit["OakLarge"], (0, 0, 13), 30, 1.45)
    for i, (dx, dz) in enumerate(((-2.5, -2.5), (2.8, -1.5), (-1.5, 2.8))):
        g.octagon("Root", 0.55, 0.5, (dx, 0.25, 13 + dz), DARK, collide=False)
    tent(g, (-12.5, 0, 8.5), 25, C("#f3ecd9"), C("#e0d3b0"), rng)
    tent(g, (12.5, 0, 9.5), -25, C("#f3ecd9"), C("#e0d3b0"), rng)
    # Campfire with three log benches.
    campfire(g, (0, 0, -1.5))
    for k, yaw in enumerate((0, 90, -90)):
        Rb = angles(0, yaw, 0)
        c = add((0, 0, -1.5), apply(Rb, (0, 0, 5.0)))
        a, b = add(c, apply(Rb, (-2.3, 0.75, 0))), add(c, apply(Rb, (2.3, 0.75, 0)))
        log(g, "BenchLog", a, b, 0.9, LOG)
        for sgn in (-1, 1):
            cut_end(g, add(c, apply(Rb, (sgn * 2.35, 0.75, 0))), 0.9, Rb)
            g.octagon("BenchStump", 0.4, 0.4, add(c, apply(Rb, (sgn * 1.5, 0.2, 0))), DARK)
    # Old Pete's upgrade booth on the right, with his chopping block.
    trainer_booth(g, (13.5, 0, -6.0), -20, rng)
    chopping_block(g, (19.5, 0, 1.5), rng)
    # Training on the left: lasso targets, a practice steer, a woodpile.
    for i, z in enumerate((-4.0, 2.0, 8.0)):
        lasso_target(g, (-21.0 + (i % 2) * 1.5, 0, z), rng)
    steer(g, (-13.0, 0, -10.0), 40)
    rope_coil(g, (-10.0, 0.1, -13.0), IDENTITY, r=1.0, loops=3)
    woodpile(g, (-19.0, 0, -12.5))
    # The entrance arch with the camp's name, and lamp posts.
    for sx in (-1, 1):
        g.octagon("ArchPost", 0.5, 9.5, (sx * 5.5, 4.75, -20.0), LOG)
        g.octagon("ArchFoot", 0.8, 0.6, (sx * 5.5, 0.3, -20.0), STONE[2])
        g.octagon("ArchTop", 0.45, 0.3, (sx * 5.5, 9.65, -20.0), LOG_END, collide=False)
        g.rod("ArchBrace", (sx * 5.5, 7.0, -20.0), (sx * 3.8, 8.8, -20.0), 0.35, LOG, **D)
        lantern(g, "ArchLantern", (sx * 4.2, 8.6, -20.4), chain=0.3)
        lamp_post(g, (sx * 9.0, 0, -18.0), yaw=0)
    log(g, "ArchBeam", (-6.8, 9.0, -20.0), (6.8, 9.0, -20.0), 0.9, LOG2)
    for sx in (-1, 1):
        cut_end(g, (sx * 6.85, 9.0, -20.0), 0.9)
    hanging_sign(g, "Old Pete's Camp", (0, 7.2, -20.0), 8.6, 1.9, C("#f0a35a"), stroke="#6b3a14",
                 back_text="Old Pete's Camp")
    for sx in (-1, 1):
        g.box("SignChain", (0.12, 0.8, 0.12), (sx * 3.4, 8.5, -20.0), IRON, **DS)
    for i, x in enumerate((-3.0, 0.0, 3.0)):
        tri(g, "ArchPine", (x, 9.45, -20.0), 1.2, 1.6, 0.12, C(("#3f9e3a", "#58bb43", "#3f9e3a")[i]), **D)
    # Bunting from the tents to the tree, flowers, bushes, a stump and mushrooms.
    bunting(g, (-12.5, 5.9, 8.5), (0, 8.5, 11.0), ["#ff5a5a", "#ffd23f", "#45a6ff", "#52d273"])
    bunting(g, (0, 8.5, 11.0), (12.5, 5.9, 9.5), ["#ffd23f", "#ff8fb8", "#45a6ff", "#ff9a3c"])
    for name, x, z in (("FlowerPatch", -7.5, -15), ("FlowerPatch", 7.5, -15), ("FlowerPatch", -18, 14),
                       ("FlowerPatch", 19, 12), ("BushSmall", -20.5, 13.5), ("BushLarge", 21, 7), ("BerryBush", -6, 18),
                       ("MushroomCluster", 5.5, 17), ("StumpMossy", 17.5, 15.5), ("GrassTuft", -15, -17),
                       ("GrassTuft", 15, -16), ("FlowerPatch", 3, -9.5), ("MushroomCluster", -24, -8)):
        add_asset(g, kit[name], (x, 0, z), rng.uniform(0, 360), 1.0)
    for sx in (-1, 1):
        flower_box(g, (sx * 7.8, 0.4, -21.0), 3.2, rng)
    barrel(g, "Barrel", (8.0, 0, 3.5))
    crate(g, "Crate", (9.2, 0, 2.0), 1.2, yaw=20)
    hay_bale(g, (-7.0, 0, 13.5), yaw=15)
    return g, ground


# ----------------------------------------------------------------- build ---

SWAP_SOURCE = (HERE / "SwapIn.lua").read_text() if (HERE / "SwapIn.lua").exists() else ""


def model(name, groups, tags):
    root = {"class": "Part", "name": "Root", "id": f"{name}.Root",
            "props": {"Size": [1, 0.1, 1], "CFrame": cframe(IDENTITY, (0, 0.05, 0)), "Transparency": 1,
                      "Anchored": True, "CanCollide": False, "CanTouch": False, "CanQuery": False,
                      "CastShadow": False, "PivotOffset": cframe(IDENTITY, (0, -0.05, 0))}}
    children = [root]
    for g in groups:
        node = group_instance(g)
        # Give each sub-model its own unique ids.
        for i, c in enumerate(node["children"]):
            if "id" in c:
                c["id"] = f"{name}.{c['id']}"
        children.append(node)
    return {"class": "Model", "name": name, "tags": tags, "props": {"PrimaryPart": {"ref": f"{name}.Root"}},
            "children": children}


def build():
    rng = random.Random(7)
    lasso = shop("LassoShop", [C("#e0482c"), C("#c93a22"), C("#d64a2e")], C("#e0482c"), "Lasso Shop", rng,
                 lasso_emblem, lasso_extras, [C("#e0482c"), C("#f06a4a")])
    market = shop("AnimalMarket", [C("#6fbf4a"), C("#5aa83c"), C("#7ccc55")], C("#4fa83c"), "Animal Market", rng,
                  paw_emblem, market_extras, [C("#5aa83c"), C("#7ccc55")])
    worlds = shop("Worlds", [C("#5a8fd9"), C("#4a7cc4"), C("#6aa0e6")], C("#4a7cc4"), "Worlds", rng,
                  globe_emblem, worlds_extras, [C("#4a7cc4"), C("#6aa0e6")])
    camp_g, ground = camp(rng)
    upg, upg_ground = upgrade_camp(rng)
    buildings = [("LassoShop", [lasso]), ("AnimalMarket", [market]), ("Worlds", [worlds]),
                 ("WranglerCamp", [camp_g, ground]), ("UpgradeCamp", [upg, upg_ground])]
    offsets = {"LassoShop": (-60, 0, 0), "AnimalMarket": (0, 0, 0), "Worlds": (60, 0, 0),
               "WranglerCamp": (0, 0, 80), "UpgradeCamp": (80, 0, 80)}
    tree_models = []
    for name, groups in buildings:
        m = model(name, groups, ["HubBuilding"])
        shift(m, offsets[name])
        tree_models.append(m)
    swap = {"class": "ModuleScript", "name": "SwapIn", "props": {"Source": SWAP_SOURCE}}
    tree = [{"class": "Folder", "name": "HubBuildings", "children": [swap] + tree_models}]
    return tree, buildings, offsets


def shift(node, off):
    """Moves a model (all its parts) by off, so the four buildings stand side by side when inserted."""
    if off == (0, 0, 0):
        return
    for c in node.get("children", []):
        if c["class"] in ("Part", "WedgePart"):
            cf = c["props"]["CFrame"]
            c["props"]["CFrame"] = [cf[0] + off[0], cf[1] + off[1], cf[2] + off[2]] + cf[3:]
        elif c["class"] == "Model":
            shift(c, off)


# --------------------------------------------------------------- preview ---

def preview(buildings, offsets):
    r = lambda v: [round(x, 3) for x in v]
    parts = [{"n": "Ground", "s": "block", "z": [300, 2, 260], "cf": r(cframe(IDENTITY, (0, -1, 30))),
              "c": list(C("#7ed957")), "m": "Grass", "t": 0, "r": 0, "st": False, "sh": True}]
    texts = []
    count = 0
    for name, groups in buildings:
        off = offsets[name]
        for g in groups:
            for p in g.parts:
                if p["transparency"] >= 1:
                    continue
                count += 1
                pn = f"{p['name']}_{count}"
                parts.append({"n": pn, "s": p["shape"], "z": r(p["size"]), "cf": r(cframe(p["R"], add(p["p"], off))),
                              "c": r(p["color"]), "m": p["material"], "t": p["transparency"],
                              "r": p.get("reflectance", 0), "st": False, "sh": p["shadow"]})
                for ch in p["children"]:
                    if ch["class"] == "SurfaceGui" and ch["props"]["Face"] == "Front":
                        label = ch["children"][0]["props"]
                        lines = [{"text": t, "color": "#%02x%02x%02x" % tuple(int(v * 255) for v in label["TextColor3"]),
                                  "size": 1, "font": "body",
                                  **({"strokeColor": "#%02x%02x%02x" % tuple(int(v * 255) for v in label["TextStrokeColor3"])}
                                     if "TextStrokeColor3" in label else {})}
                                 for t in label["Text"].split("\n")]
                        texts.append({"part": pn, "lines": lines, "pad": 0.14})
    env = {"sky": [[0, "#3f9fff"], [0.55, "#96d0ff"], [1, "#dff2ff"]], "fog": ["#dff2ff", 300, 700],
           "sun": {"dir": [-0.5, 1.0, -0.6], "intensity": 2.4}, "hemi": ["#ffffff", "#8fb070", 1.5],
           "bloom": [0.35, 0.5, 0.9]}
    shots = {}
    for name, (ox, _, oz) in offsets.items():
        if name == "WranglerCamp":
            shots["camp"] = {"camera": {"pos": [ox + 26, 34, oz + 42], "target": [ox, 2, oz], "fov": 55},
                             "shadow": {"center": [ox, 0, oz], "radius": 45}}
            shots["camp_top"] = {"camera": {"pos": [ox + 2, 70, oz + 20], "target": [ox, 0, oz], "fov": 55},
                                 "shadow": {"center": [ox, 0, oz], "radius": 45}}
            shots["camp_close"] = {"camera": {"pos": [ox - 10, 9, oz + 14], "target": [ox - 6, 3, oz - 6], "fov": 62},
                                   "shadow": {"center": [ox, 0, oz], "radius": 40}}
        else:
            key = name.lower()
            shots[key] = {"camera": {"pos": [ox + 12, 17, oz - 36], "target": [ox + 2, 7, oz], "fov": 55},
                          "shadow": {"center": [ox, 0, oz], "radius": 40}}
            shots[key + "_side"] = {"camera": {"pos": [ox + 30, 12, oz - 22], "target": [ox + 4, 5, oz - 2], "fov": 55},
                                    "shadow": {"center": [ox, 0, oz], "radius": 40}}
    return {"env": env, "parts": parts, "models": [], "texts": texts, "sprites": [], "shots": shots}


def main():
    tree, buildings, offsets = build()
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "buildings.json").write_text(json.dumps(tree))
    (out / "world.json").write_text(json.dumps(preview(buildings, offsets)))
    for name, groups in buildings:
        print(f"{name:14} {sum(len(g.parts) for g in groups):5} parts")
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        cmd = ["cargo", "run", "--quiet", "--release", "--manifest-path",
               str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "buildings.json"), target]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
