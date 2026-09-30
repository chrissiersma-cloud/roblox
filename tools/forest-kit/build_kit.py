#!/usr/bin/env python3
"""Critter Woods forest kit: low-poly trees, wood, plants, rocks and ground details built from Parts.

Every asset is a Model of anchored Parts in the game's style: faceted leaf crowns in a few flat greens,
octagonal trunks and logs, chunky rocks. The pivot of each model is on the ground under its center, so
`model:PivotTo(CFrame.new(groundPoint))` puts it on the ground.

    python3 tools/forest-kit/build_kit.py                  -> build/kit.json and build/world.json (preview)
    python3 tools/forest-kit/build_kit.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
"""

import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "animal-models"))

from lib import IDENTITY, add, aim, angles, apply, cframe, compose, hex_color, inverse, matmul, sub  # noqa: E402

SPARKLE_TEXTURE = "rbxasset://textures/particles/sparkles_main.dds"


def C(h):
    return hex_color(h)


def shade(color, k):
    return tuple(min(1.0, c * k) for c in color)


# Leaf palettes (darkest -> lightest), matching the bright low-poly greens of the game.
EDGE = [C("#3f9e3a"), C("#58bb43"), C("#74d14c"), C("#8fe05a")]
WOOD = [C("#33893a"), C("#47a33f"), C("#5fba45"), C("#74c94f")]
DEEP = [C("#1f5e2e"), C("#2b7536"), C("#378a3f"), C("#45a049")]
BIRCH = [C("#6aa83e"), C("#86c04a"), C("#a2d45a"), C("#b8e070")]
PINE = [C("#2f8f3a"), C("#3aa33a"), C("#4fb847")]
PINE_DEEP = [C("#1b5a2c"), C("#236b33"), C("#2d7d3b")]

BARK = C("#8b5a2b")
BARK_DARK = C("#6b4424")
BARK_DEEP = C("#4e3220")
WOOD_CUT = C("#e0b276")
WOOD_RING = C("#b8844c")
MOSS = C("#5aa84a")
MOSS_DARK = C("#3f8a3c")
STONE = [C("#7e8a9c"), C("#9aa6b8"), C("#b3bfcc")]


class Asset:
    def __init__(self, name, category, zone, note):
        self.name, self.category, self.zone, self.note = name, category, zone, note
        self.parts = []

    def part(self, shape, name, size, pos, color, R=None, rot=None, material="SmoothPlastic", collide=True,
             shadow=True, transparency=0.0, effects=None):
        if R is None:
            R = angles(*rot) if rot else IDENTITY
        self.parts.append({
            "shape": shape, "name": name, "size": tuple(size), "R": R, "p": tuple(pos), "color": color,
            "material": material, "collide": collide, "shadow": shadow, "transparency": transparency,
            "effects": effects or [],
        })
        return self.parts[-1]

    def box(self, name, size, pos, color, **kw):
        return self.part("block", name, size, pos, color, **kw)

    def wedge(self, name, size, pos, color, **kw):
        return self.part("wedge", name, size, pos, color, **kw)

    def ball(self, name, d, pos, color, **kw):
        return self.part("ball", name, (d, d, d), pos, color, **kw)

    def cyl(self, name, length, d, pos, color, **kw):
        """Cylinder along local X."""
        return self.part("cylinder", name, (length, d, d), pos, color, **kw)

    def disc(self, name, d, h, pos, color, **kw):
        """Flat upright-axis cylinder (a round slab)."""
        return self.cyl(name, h, d, pos, color, R=angles(0, 0, 90), **kw)

    def rod(self, name, start, end, d, color, octagon=True, **kw):
        """Low-poly beam between two points (square, plus a 45-degree copy = octagon)."""
        length = math.dist(start, end)
        mid = tuple((a + b) / 2 for a, b in zip(start, end))
        R = aim(sub(end, start))
        self.box(name, (length, d, d), mid, color, R=R, **kw)
        if octagon:
            self.box(name, (length * 0.999, d * 0.96, d * 0.96), mid, color, R=matmul(R, angles(45, 0, 0)), **kw)

    def octo(self, name, size, pos, color, yaw=0.0, **kw):
        """Upright octagonal prism: a block plus the same block turned 45 degrees."""
        w, h, d = size
        self.box(name, (w, h, d), pos, color, rot=(0, yaw, 0), **kw)
        self.box(name, (w * 0.96, h * 0.999, d * 0.96), pos, color, rot=(0, yaw + 45, 0), **kw)


# ------------------------------------------------------------ building blocks --

def crown(a, center, radii, pal, rng, n=9, name="Leaves"):
    """Faceted leaf blob: a core block plus chunks turned at random angles around it."""
    rx, ry, rz = radii
    a.box(name, (rx * 1.3, ry * 1.2, rz * 1.3), center, pal[1], collide=False,
          rot=(rng.uniform(-12, 12), rng.uniform(0, 90), rng.uniform(-12, 12)))
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        y = 1 - (i + 0.5) / n * 1.75
        r = math.sqrt(max(0.0, 1 - y * y))
        th = golden * i + rng.uniform(-0.35, 0.35)
        d = (math.cos(th) * r, y, math.sin(th) * r)
        k = rng.uniform(0.5, 0.7)
        pos = add(center, (d[0] * rx * 0.62, d[1] * ry * 0.6, d[2] * rz * 0.62))
        size = (rx * k * 1.15 * rng.uniform(0.85, 1.15), ry * k * rng.uniform(0.9, 1.15),
                rz * k * 1.15 * rng.uniform(0.85, 1.15))
        color = pal[3] if y > 0.55 else pal[2] if y > 0.1 else pal[1] if y > -0.35 else pal[0]
        a.box(name, size, pos, color, collide=False,
              rot=(rng.uniform(-35, 35), rng.uniform(0, 90), rng.uniform(-35, 35)))


def trunk(a, h, w, color, rng, top_w=None):
    """Octagonal trunk that narrows a little towards the top; returns the top center."""
    top_w = top_w or w * 0.78
    yaw = rng.uniform(0, 45)
    a.octo("Trunk", (w, h * 0.62, w), (0, h * 0.31, 0), color, yaw=yaw)
    a.octo("Trunk", (top_w, h * 0.45, top_w), (0, h * 0.77, 0), color, yaw=yaw + 20)
    return (0, h, 0)


def roots(a, w, color, rng, n=4, length=None, height=None):
    length = length or w * 0.9
    height = height or w * 0.55
    start = rng.uniform(0, 90)
    for i in range(n):
        yaw = start + i * 360 / n + rng.uniform(-12, 12)
        R = angles(0, yaw, 0)
        wide = w * rng.uniform(0.35, 0.5)
        pos = apply(R, (0, height / 2, -(w * 0.42 + length / 2)))
        a.wedge("Root", (wide, height, length), pos, color, R=R)


def branch(a, start, end, w, color):
    a.rod("Branch", start, end, w, color)


def moss_cap(a, center, w, d, rng, n=3, color=MOSS):
    for _ in range(n):
        a.box("Moss", (w * rng.uniform(0.35, 0.6), 0.22, d * rng.uniform(0.35, 0.6)),
              add(center, (rng.uniform(-w, w) * 0.25, 0, rng.uniform(-d, d) * 0.25)), color,
              rot=(0, rng.uniform(0, 90), 0), collide=False)


# ------------------------------------------------------------------- trees --

def oak(name, k, pal, bark, rng, zone, note, clusters=1, root_count=0, h=6.0):
    a = Asset(name, "Trees", zone, note)
    w = 1.5 * k
    th = h * k
    top = trunk(a, th, w, bark, rng)
    if root_count:
        roots(a, w, bark, rng, n=root_count)
    crown(a, add(top, (0, 3.0 * k, 0)), (4.4 * k, 3.8 * k, 4.4 * k), pal, rng, n=10)
    start = rng.uniform(0, 360)
    for i in range(clusters - 1):
        ang = math.radians(start + i * 360 / max(1, clusters - 1))
        c = (math.cos(ang) * 3.8 * k, th + 1.2 * k, math.sin(ang) * 3.8 * k)
        branch(a, (0, th * 0.7, 0), c, w * 0.42, bark)
        crown(a, c, (3.0 * k, 2.6 * k, 3.0 * k), pal, rng, n=6)
    if clusters >= 3:
        crown(a, add(top, (0, 6.6 * k, 0)), (2.9 * k, 2.4 * k, 2.9 * k), pal, rng, n=5)
    return a


def birch(rng):
    a = Asset("BirchTree", "Trees", "Edge", "Slim white tree for the sunny forest edge")
    h, w = 11.0, 0.95
    white, mark = C("#ece6d6"), C("#3a3530")
    a.octo("Trunk", (w, h, w), (0, h / 2, 0), white)
    for i in range(9):
        y = rng.uniform(1.0, h - 1.0)
        side = rng.choice((0, 90, 180, 270))
        R = angles(0, side, 0)
        a.box("Mark", (rng.uniform(0.3, 0.55), 0.14, 0.06), apply(R, (rng.uniform(-0.2, 0.2), y, -w / 2 - 0.02)),
              mark, R=R, collide=False, shadow=False)
    branch(a, (0, h * 0.7, 0), (1.8, h * 0.95, 0.4), 0.35, white)
    crown(a, (0, h + 1.2, 0), (2.9, 4.4, 2.9), BIRCH, rng, n=8)
    crown(a, (1.9, h - 0.4, 0.5), (2.0, 2.4, 2.0), BIRCH, rng, n=5)
    return a


def pine(name, k, pal, bark, rng, zone, note, tiers=4):
    a = Asset(name, "Trees", zone, note)
    th = 3.0 * k
    a.octo("Trunk", (1.2 * k, th + 1.0, 1.2 * k), (0, (th + 1.0) / 2, 0), bark)
    base_w = 8.5 * k
    y = th
    for i in range(tiers):
        f = 1 - i / (tiers + 0.6)
        w = base_w * f
        hgt = 4.2 * k * (0.75 + 0.25 * f)
        color = pal[0] if i < tiers / 3 else pal[1] if i < 2 * tiers / 3 else pal[2]
        yaw0 = rng.uniform(0, 90)
        for j, yaw in enumerate((0, 90, 180, 270, 45, 135, 225, 315)):
            R = angles(0, yaw0 + yaw, 0)
            ww = w if j < 4 else w * 0.94
            pos = add((0, y + hgt / 2, 0), apply(R, (0, 0, -ww / 4)))
            a.wedge("Needles", (ww, hgt, ww / 2), pos, color if j < 4 else shade(color, 0.88), R=R, collide=False)
        y += hgt * 0.55
    return a


def dead_tree(rng):
    a = Asset("DeadTree", "Trees", "Deep", "Bare spooky tree for the dark deep woods")
    grey = C("#6f5e4f")
    h, w = 10.0, 1.4
    trunk(a, h, w, grey, rng, top_w=0.9)
    roots(a, w, grey, rng, n=3)
    for yaw, y0, y1, out in ((20, 5.5, 9.5, 3.6), (150, 7.0, 11.5, 3.2), (260, 8.5, 12.5, 2.4), (320, 4.0, 6.5, 2.6)):
        d = apply(angles(0, yaw, 0), (0, 0, -1))
        tip = (d[0] * out, y1, d[2] * out)
        branch(a, (0, y0, 0), tip, 0.45, grey)
        twig = (tip[0] + d[2] * 1.2, y1 + 1.0, tip[2] - d[0] * 1.2)
        branch(a, tip, twig, 0.25, grey)
    branch(a, (0, h - 0.5, 0), (0.3, h + 2.2, -0.4), 0.5, grey)
    return a


def ancient_tree(rng):
    a = Asset("AncientTree", "Trees", "Heart", "Huge old tree for the hidden clearing in the heart of the forest")
    h, w = 16.0, 4.6
    a.octo("Trunk", (w, h * 0.6, w), (0, h * 0.3, 0), BARK_DEEP)
    a.octo("Trunk", (w * 0.82, h * 0.5, w * 0.82), (0, h * 0.78, 0), BARK_DEEP, yaw=20)
    roots(a, w, BARK_DEEP, rng, n=6, length=4.2, height=2.8)
    for i in range(5):
        yaw = i * 72 + 20
        d = apply(angles(0, yaw, 0), (0, 0, -1))
        a.rod("Root", (d[0] * w * 0.3, 2.6, d[2] * w * 0.3), (d[0] * (w * 0.5 + 5.2), 0.3, d[2] * (w * 0.5 + 5.2)),
              0.9, BARK_DEEP)
    for y in (3.0, 7.5, 11.0):
        side = rng.uniform(0, 360)
        R = angles(0, side, 0)
        a.box("Moss", (1.8, 1.2, 0.3), apply(R, (0, y, -w / 2 - 0.1)), MOSS, R=R, collide=False)
    for i in range(4):
        ang = math.radians(45 + i * 90)
        c = (math.cos(ang) * 9.0, h + 1.5, math.sin(ang) * 9.0)
        branch(a, (0, h * 0.8, 0), c, 1.4, BARK_DEEP)
        crown(a, c, (7.0, 5.2, 7.0), DEEP, rng, n=8)
    crown(a, (0, h + 4.5, 0), (11.0, 7.5, 11.0), DEEP, rng, n=16)
    crown(a, (0, h + 11.0, 0), (6.0, 4.2, 6.0), DEEP, rng, n=6)
    fireflies = {
        "class": "ParticleEmitter", "name": "Fireflies",
        "props": {
            "Texture": SPARKLE_TEXTURE, "Rate": 6, "Lifetime": [4, 7], "Speed": [0.3, 1.0],
            "SpreadAngle": [180, 180], "LightEmission": 1, "LightInfluence": 0,
            "Size": [[0, 0.25], [0.5, 0.4], [1, 0]], "Transparency": [[0, 1], [0.2, 0.1], [0.8, 0.2], [1, 1]],
            "Color": [[0, *C("#fff27a")], [1, *C("#b8ff6a")]], "RotSpeed": [-60, 60],
        },
    }
    a.box("FireflyZone", (26, 12, 26), (0, 9, 0), C("#ffffff"), transparency=1, collide=False, shadow=False,
          effects=[fireflies])
    for i in range(7):
        ang = math.radians(i * 360 / 7 + 10)
        glow_mushroom(a, (math.cos(ang) * (w * 0.5 + 3.4), 0, math.sin(ang) * (w * 0.5 + 3.4)), rng, k=1.3,
                      light=(i == 0))
    return a


# ------------------------------------------------------------ wood & trunks --

def log_part(a, name, length, d, center, R, bark, rng, caps=True):
    """Octagonal log lying along local X of R."""
    a.box(name, (length, d, d), center, bark, R=R)
    a.box(name, (length * 0.999, d * 0.96, d * 0.96), center, bark, R=matmul(R, angles(45, 0, 0)))
    if caps:
        for sgn in (-1, 1):
            p = add(center, apply(R, (sgn * length / 2, 0, 0)))
            a.box("CutEnd", (0.12, d * 0.8, d * 0.8), p, WOOD_CUT, R=R, collide=False)
            a.box("CutEnd", (0.12, d * 0.77, d * 0.77), p, WOOD_CUT, R=matmul(R, angles(45, 0, 0)), collide=False)
            a.box("Ring", (0.14, d * 0.4, d * 0.4), p, WOOD_RING, R=matmul(R, angles(45, 0, 0)), collide=False)


def stump(mossy, rng):
    name = "StumpMossy" if mossy else "Stump"
    zone = "Deep" if mossy else "Woodland"
    a = Asset(name, "Wood", zone, "Cut tree stump" + (" covered in moss" if mossy else ""))
    bark = BARK_DEEP if mossy else BARK
    a.octo("Stump", (2.8, 1.8, 2.8), (0, 0.9, 0), bark)
    a.octo("CutTop", (2.4, 0.12, 2.4), (0, 1.84, 0), WOOD_CUT, collide=False)
    a.octo("Ring", (1.3, 0.14, 1.3), (0, 1.86, 0), WOOD_RING, collide=False)
    a.box("Core", (0.35, 0.16, 0.35), (0, 1.88, 0), bark, collide=False)
    roots(a, 2.8, bark, rng, n=4, length=1.4, height=0.9)
    if mossy:
        moss_cap(a, (0, 1.95, 0), 2.4, 2.4, rng, n=3)
        a.box("Moss", (2.9, 0.5, 1.2), (0, 0.4, -1.0), MOSS_DARK, rot=(0, 20, 0), collide=False)
        mushroom(a, (1.4, 0, 1.0), rng, k=0.6)
    return a


def fallen_log(mossy, rng):
    name = "FallenLogMossy" if mossy else "FallenLog"
    zone = "Deep" if mossy else "Woodland"
    a = Asset(name, "Wood", zone, "Fallen tree trunk; animals can hide behind it")
    bark = BARK_DEEP if mossy else BARK
    d, length = 2.4, 13.0
    log_part(a, "Log", length, d, (0, d / 2 - 0.05, 0), IDENTITY, bark, rng)
    for x in (-4.0, 0.5, 4.5):
        a.box("BarkRidge", (2.2, 0.2, 0.3), (x, d - 0.08, rng.uniform(-0.5, 0.5)), shade(bark, 0.8), collide=False)
    branch(a, (2.0, d * 0.7, 0), (3.2, d + 1.6, -1.2), 0.45, bark)
    if mossy:
        for x in (-3.5, 1.0, 4.0):
            a.box("Moss", (rng.uniform(2.2, 3.4), 0.3, d * 0.8), (x, d + 0.02, 0), MOSS, rot=(0, rng.uniform(-8, 8), 0),
                  collide=False)
        mushroom(a, (-1.5, 0, 1.6), rng, k=0.7)
        mushroom(a, (-0.8, 0, 1.9), rng, k=0.45)
    return a


def log_pile(rng):
    a = Asset("LogPile", "Wood", "Woodland", "Stack of cut logs")
    d, length = 1.5, 7.0
    rows = ((-1.5, 0), (0, 0), (1.5, 0), (-0.75, 1), (0.75, 1), (0, 2))
    for z, row in rows:
        y = d / 2 + row * d * 0.86
        log_part(a, "Log", length + rng.uniform(-0.4, 0.4), d, (rng.uniform(-0.2, 0.2), y, z), IDENTITY, BARK, rng)
    return a


# ---------------------------------------------------------------- plants --

def bush(name, k, pal, rng, zone, note, berries=False):
    a = Asset(name, "Plants", zone, note)
    crown(a, (0, 1.5 * k, 0), (2.4 * k, 1.7 * k, 2.4 * k), pal, rng, n=7, name="Bush")
    if berries:
        for _ in range(9):
            ang = rng.uniform(0, 2 * math.pi)
            y = rng.uniform(1.0, 2.4) * k
            r = 2.1 * k * math.sqrt(max(0.1, 1 - ((y - 1.5 * k) / (1.9 * k)) ** 2))
            a.ball("Berry", 0.42, (math.cos(ang) * r, y, math.sin(ang) * r), C("#e0405a"), collide=False,
                   shadow=False)
    return a


def fern(rng, zone="Deep", name="Fern", pal=(C("#2a7a38"), C("#3a9a4e"))):
    a = Asset(name, "Plants", zone, "Low fern with fronds spread out")
    for i in range(8):
        yaw = i * 45 + rng.uniform(-10, 10)
        tilt = rng.uniform(50, 68)
        length = rng.uniform(2.6, 3.4)
        R = matmul(angles(0, yaw, 0), angles(-tilt, 0, 0))
        a.box("Frond", (0.75, length, 0.12), apply(R, (0, length / 2, 0)), pal[i % 2], R=R, collide=False)
    for i in range(4):
        yaw = i * 90 + 22
        R = matmul(angles(0, yaw, 0), angles(-25, 0, 0))
        a.box("Frond", (0.55, 2.0, 0.12), apply(R, (0, 1.0, 0)), pal[1], R=R, collide=False)
    return a


def grass_tuft(rng, name="GrassTuft", k=1.0, pal=(C("#58bb43"), C("#74d14c"), C("#3f9e3a"))):
    a = Asset(name, "Plants", "Edge", "Clump of grass blades")
    for i in range(9):
        yaw = i * 40 + rng.uniform(-12, 12)
        h = rng.uniform(1.2, 2.0) * k * (0.75 if i % 3 == 2 else 1.0)
        tilt = rng.uniform(18, 38)
        base = (0.95 if i % 2 else 0.8) * k
        R = matmul(angles(0, yaw, 0), angles(tilt, 0, 0))
        center = add(apply(angles(0, yaw, 0), (0, 0, 0.25 * k)), apply(R, (0, h / 2, 0)))
        a.wedge("Blade", (0.22, h, base), center, pal[i % 3], R=R, collide=False, shadow=False)
    return a


FLOWER_COLORS = [C("#ff8fb8"), C("#b58cff"), C("#ffd166"), C("#ffffff"), C("#ff6b5a")]


def flower(a, pos, color, rng, h=None):
    h = h or rng.uniform(0.8, 1.3)
    a.box("Stem", (0.14, h, 0.14), add(pos, (0, h / 2, 0)), C("#3f8f2f"), collide=False, shadow=False)
    top = add(pos, (0, h, 0))
    yaw = rng.uniform(0, 90)
    for j in range(4):
        R = angles(0, yaw + j * 90, 0)
        a.box("Petal", (0.34, 0.12, 0.34), add(top, apply(R, (0, 0, -0.26))), color, R=matmul(R, angles(0, 45, 0)),
              collide=False, shadow=False)
    a.box("Center", (0.24, 0.18, 0.24), add(top, (0, 0.04, 0)), C("#ffd23f") if color != C("#ffd166") else C("#e07b00"),
          collide=False, shadow=False)


def flower_patch(rng):
    a = Asset("FlowerPatch", "Plants", "Edge", "Little group of flowers for the meadow")
    colors = rng.sample(FLOWER_COLORS, 3)
    for i in range(7):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0.3, 1.6)
        flower(a, (math.cos(ang) * r, 0, math.sin(ang) * r), colors[i % 3], rng)
    for i in range(4):
        ang = rng.uniform(0, 2 * math.pi)
        R = angles(0, math.degrees(ang), -30)
        a.box("Leaf", (0.7, 0.08, 0.3), (math.cos(ang) * 0.5, 0.2, math.sin(ang) * 0.5), C("#4fb84f"), R=R,
              collide=False, shadow=False)
    return a


def mushroom(a, pos, rng, k=1.0, cap=C("#e04a3c"), neon=False):
    stem_h = 1.1 * k
    a.octo("Stem", (0.5 * k, stem_h, 0.5 * k), add(pos, (0, stem_h / 2, 0)), C("#f7f1e3"), collide=False,
           shadow=False)
    mat = "Neon" if neon else "SmoothPlastic"
    a.octo("Cap", (1.7 * k, 0.45 * k, 1.7 * k), add(pos, (0, stem_h + 0.1 * k, 0)), cap, material=mat,
           collide=False)
    a.octo("Cap", (1.1 * k, 0.35 * k, 1.1 * k), add(pos, (0, stem_h + 0.45 * k, 0)), cap, material=mat,
           collide=False, yaw=22)
    if not neon:
        for _ in range(3):
            ang = rng.uniform(0, 2 * math.pi)
            a.box("Dot", (0.22 * k, 0.08, 0.22 * k),
                  add(pos, (math.cos(ang) * 0.55 * k, stem_h + 0.34 * k, math.sin(ang) * 0.55 * k)), C("#ffffff"),
                  collide=False, shadow=False)


def glow_mushroom(a, pos, rng, k=1.0, light=False):
    mushroom(a, pos, rng, k=k, cap=C("#5ef0ff"), neon=True)
    if light:
        a.parts[-1]["effects"].append({"class": "PointLight", "name": "Glow",
                                       "props": {"Color": list(C("#5ef0ff")), "Brightness": 1.2, "Range": 12,
                                                 "Shadows": False}})


def mushroom_cluster(rng):
    a = Asset("MushroomCluster", "Plants", "Woodland", "Three red toadstools")
    for pos, k in (((0, 0, 0), 1.0), ((1.1, 0, 0.5), 0.7), ((-0.6, 0, 1.0), 0.5)):
        mushroom(a, pos, rng, k=k)
    return a


def glow_mushrooms(rng):
    a = Asset("GlowMushrooms", "Plants", "Deep", "Glowing blue mushrooms that light up the dark woods")
    spots = ((0, 0, 0, 0.9), (1.0, 0, 0.6, 0.6), (-0.8, 0, 0.8, 0.5), (0.3, 0, -1.0, 0.45), (-1.1, 0, -0.4, 0.35))
    for i, (x, y, z, k) in enumerate(spots):
        glow_mushroom(a, (x, y, z), rng, k=k, light=(i == 0))
    return a


def mushroom_ring(rng):
    a = Asset("MushroomRing", "Plants", "Heart", "Fairy ring of small mushrooms")
    for i in range(12):
        ang = math.radians(i * 30 + rng.uniform(-6, 6))
        mushroom(a, (math.cos(ang) * 4.0, 0, math.sin(ang) * 4.0), rng, k=rng.uniform(0.4, 0.6))
    return a


def reeds(rng):
    a = Asset("Reeds", "Plants", "Water", "Cattails for river banks and the pond")
    for i in range(6):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 1.0)
        x, z = math.cos(ang) * r, math.sin(ang) * r
        h = rng.uniform(3.0, 4.2)
        lean = (rng.uniform(-6, 6), 0, rng.uniform(-6, 6))
        R = angles(*lean)
        a.box("Reed", (0.16, h, 0.16), add((x, 0, z), apply(R, (0, h / 2, 0))), C("#4f9e3a"), R=R, collide=False,
              shadow=False)
        a.octo("Cattail", (0.38, 0.95, 0.38), add((x, 0, z), apply(R, (0, h - 0.6, 0))), C("#7a4a24"),
               collide=False, shadow=False)
    for i in range(5):
        yaw = rng.uniform(0, 360)
        h = rng.uniform(1.8, 2.8)
        R = matmul(angles(0, yaw, 0), angles(rng.uniform(-22, -10), 0, 0))
        a.wedge("Leaf", (0.12, h, 0.45), apply(R, (0, h / 2, 0.1)), C("#5cb342"), R=R, collide=False, shadow=False)
    return a


def lily_pad(rng):
    a = Asset("LilyPad", "Plants", "Water", "Floating lily pad with a pink flower (set it on the water surface)")
    for yaw, d in ((0, 3.0), (20, 2.9)):
        a.box("Pad", (d, 0.16, d), (0, 0.08, 0), C("#4fb84f"), rot=(0, yaw, 0), collide=False)
        a.box("Pad", (d * 0.96, 0.16, d * 0.96), (0, 0.08, 0), C("#4fb84f"), rot=(0, yaw + 45, 0), collide=False)
    a.wedge("Notch", (0.1, 0.2, 1.4), (0, 0.1, -0.8), C("#3a9a3a"), collide=False, shadow=False)
    for j in range(6):
        R = angles(0, j * 60, 0)
        a.box("Petal", (0.4, 0.3, 0.6), add((0.5, 0.3, 0.3), apply(R, (0, 0, -0.32))), C("#ff9ec4"),
              R=matmul(R, angles(-25, 0, 0)), collide=False, shadow=False)
    a.box("Center", (0.3, 0.3, 0.3), (0.5, 0.4, 0.3), C("#ffd23f"), collide=False, shadow=False)
    return a


# ----------------------------------------------------------------- rocks --

def mossy_rock(name, k, rng, zone):
    a = Asset(name, "Rocks", zone, "Chunky stone with a moss top")
    a.box("Rock", (3.2 * k, 2.2 * k, 2.8 * k), (0, 1.0 * k, 0), STONE[1], rot=(rng.uniform(-6, 6), rng.uniform(0, 90), 8))
    a.box("Rock", (2.4 * k, 2.0 * k, 2.4 * k), (0.9 * k, 1.1 * k, 0.4 * k), STONE[2],
          rot=(rng.uniform(-20, 20), rng.uniform(0, 90), rng.uniform(-20, 20)))
    a.box("Rock", (2.0 * k, 1.4 * k, 2.0 * k), (-1.1 * k, 0.6 * k, -0.3 * k), STONE[0],
          rot=(rng.uniform(-20, 20), rng.uniform(0, 90), rng.uniform(-20, 20)))
    a.box("Moss", (2.8 * k, 0.4 * k, 2.2 * k), (0.1 * k, 2.15 * k, 0), MOSS, rot=(0, rng.uniform(0, 90), 6),
          collide=False)
    a.box("Moss", (1.4 * k, 0.35 * k, 1.2 * k), (1.0 * k, 2.2 * k, 0.6 * k), MOSS_DARK,
          rot=(0, rng.uniform(0, 90), -10), collide=False)
    return a


# ---------------------------------------------------------- ground details --

def flat(a, name, size, pos, color, yaw, transparency=0.0):
    a.box(name, (size[0], 0.06, size[1]), (pos[0], 0.03 + pos[1], pos[2]), color, rot=(0, yaw, 0), collide=False,
          shadow=False, transparency=transparency)


def leaf_litter(rng):
    a = Asset("LeafLitter", "Ground", "Woodland", "Fallen leaves on the forest floor")
    colors = [C("#e88a3a"), C("#f2c14e"), C("#a8642c"), C("#d2553a"), C("#7ab84a")]
    for i in range(18):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 3.2)
        s = rng.uniform(0.45, 0.8)
        flat(a, "Leaf", (s, s * 0.6), (math.cos(ang) * r, i * 0.004, math.sin(ang) * r), colors[i % 5],
             rng.uniform(0, 180))
    return a


def moss_patch(rng):
    a = Asset("MossPatch", "Ground", "Deep", "Soft moss on the dark forest floor")
    for i in range(7):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2.0)
        s = rng.uniform(1.4, 2.6)
        flat(a, "Moss", (s, s * rng.uniform(0.6, 1.0)), (math.cos(ang) * r, i * 0.004, math.sin(ang) * r),
             MOSS if i % 2 else MOSS_DARK, rng.uniform(0, 90))
    return a


def dirt_patch(rng):
    a = Asset("DirtPatch", "Ground", "Woodland", "Bare dirt spot, good under trees and along paths")
    for i in range(6):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 1.8)
        s = rng.uniform(1.6, 2.8)
        flat(a, "Dirt", (s, s * rng.uniform(0.6, 1.0)), (math.cos(ang) * r, i * 0.004, math.sin(ang) * r),
             C("#a8753f") if i % 2 else C("#8f6232"), rng.uniform(0, 90))
    return a


def pebbles(rng):
    a = Asset("Pebbles", "Ground", "Water", "Small stones for river banks and paths")
    for i in range(10):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2.4)
        s = rng.uniform(0.4, 0.9)
        a.box("Pebble", (s, s * 0.45, s * rng.uniform(0.7, 1.0)), (math.cos(ang) * r, s * 0.2, math.sin(ang) * r),
              STONE[i % 3], rot=(rng.uniform(-10, 10), rng.uniform(0, 90), rng.uniform(-10, 10)), collide=False,
              shadow=False)
    return a


def paw_prints(rng):
    a = Asset("PawPrints", "Ground", "Woodland", "A trail of animal tracks that hints where animals walk")
    col = C("#5a3a22")
    for i in range(6):
        side = -1 if i % 2 else 1
        cx, cz = side * 0.55, -i * 1.6
        flat(a, "Pad", (0.62, 0.55), (cx, 0, cz), col, 45, transparency=0.2)
        for j, (tx, tz) in enumerate(((-0.4, -0.55), (-0.14, -0.72), (0.14, -0.72), (0.4, -0.55))):
            flat(a, "Toe", (0.22, 0.26), (cx + tx, 0.002 * j, cz + tz), col, 0, transparency=0.2)
    return a


def petal_scatter(rng):
    a = Asset("PetalScatter", "Ground", "Edge", "Tiny flower heads dotted in the grass")
    for i in range(16):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 3.0)
        color = FLOWER_COLORS[i % len(FLOWER_COLORS)]
        flat(a, "Petal", (0.3, 0.3), (math.cos(ang) * r, 0.01, math.sin(ang) * r), color, 45)
    return a


def sun_shaft(rng):
    a = Asset("SunShaft", "Ground", "Deep", "Soft beam of light falling through the canopy (tilt it as you like)")
    for i, (w, t) in enumerate(((3.0, 0.86), (1.8, 0.8))):
        a.box("Light", (w, 34, w), (0, 17, 0), C("#fff6c8"), material="Neon", collide=False, shadow=False,
              transparency=t, rot=(0, 0, 14))
    return a


def fireflies(rng):
    a = Asset("Fireflies", "Ground", "Deep", "Invisible box that lets little lights drift around")
    em = {
        "class": "ParticleEmitter", "name": "Fireflies",
        "props": {
            "Texture": SPARKLE_TEXTURE, "Rate": 4, "Lifetime": [4, 7], "Speed": [0.3, 1.0], "SpreadAngle": [180, 180],
            "LightEmission": 1, "LightInfluence": 0, "Size": [[0, 0.25], [0.5, 0.4], [1, 0]],
            "Transparency": [[0, 1], [0.2, 0.1], [0.8, 0.2], [1, 1]],
            "Color": [[0, *C("#fff27a")], [1, *C("#b8ff6a")]], "RotSpeed": [-60, 60],
        },
    }
    a.box("FireflyZone", (16, 6, 16), (0, 3, 0), C("#ffffff"), transparency=1, collide=False, shadow=False,
          effects=[em])
    return a


# ------------------------------------------------------------------- kit --

def make_kit():
    rng = random.Random(7)
    assets = [
        oak("OakSmall", 0.8, EDGE, BARK, rng, "Edge", "Small round tree for the sunny forest edge"),
        oak("OakMedium", 1.1, WOOD, BARK, rng, "Woodland", "Round tree with a second leaf cluster", clusters=2),
        oak("OakLarge", 1.35, WOOD, BARK, rng, "Woodland", "Big round tree with three leaf clusters", clusters=3,
            root_count=4),
        birch(rng),
        pine("PineSmall", 0.8, PINE, BARK_DARK, rng, "Edge", "Young pine", tiers=3),
        pine("PineMedium", 1.1, PINE, BARK_DARK, rng, "Woodland", "Pine tree", tiers=4),
        pine("PineTall", 1.3, PINE, BARK_DARK, rng, "Woodland", "Tall pine", tiers=5),
        oak("DeepOak", 1.45, DEEP, BARK_DEEP, rng, "Deep", "Dark, thick tree with roots for the deep woods",
            clusters=3, root_count=5, h=7.5),
        pine("DeepPine", 1.5, PINE_DEEP, BARK_DEEP, rng, "Deep", "Very tall dark pine for the deep woods", tiers=6),
        dead_tree(rng),
        ancient_tree(rng),
        stump(False, rng), stump(True, rng), fallen_log(False, rng), fallen_log(True, rng), log_pile(rng),
        bush("BushSmall", 0.75, EDGE, rng, "Edge", "Small round bush"),
        bush("BushLarge", 1.15, WOOD, rng, "Woodland", "Big bush animals can hide in"),
        bush("BerryBush", 1.0, WOOD, rng, "Woodland", "Bush with red berries", berries=True),
        bush("DarkBush", 1.1, DEEP, rng, "Deep", "Dark bush for the deep woods"),
        fern(rng), grass_tuft(rng),
        grass_tuft(rng, "TallGrass", k=1.7, pal=(C("#4fae45"), C("#6cc84c"), C("#3a9a3a"))),
        flower_patch(rng), mushroom_cluster(rng), glow_mushrooms(rng), mushroom_ring(rng), reeds(rng),
        lily_pad(rng),
        mossy_rock("MossyRockSmall", 0.7, rng, "Woodland"), mossy_rock("MossyRockLarge", 1.4, rng, "Deep"),
        leaf_litter(rng), moss_patch(rng), dirt_patch(rng), pebbles(rng), paw_prints(rng), petal_scatter(rng),
        sun_shaft(rng), fireflies(rng),
    ]
    return assets


CATEGORIES = [("Trees", 34.0), ("Wood", 20.0), ("Plants", 10.0), ("Rocks", 12.0), ("Ground", 10.0)]
ROW_Z = {"Trees": 0.0, "Wood": 42.0, "Plants": 64.0, "Rocks": 82.0, "Ground": 98.0}


def layout(assets):
    """Catalog positions: one row per category, so the kit is easy to browse after inserting it."""
    spots = {}
    for cat, gap in CATEGORIES:
        row = [a for a in assets if a.category == cat]
        for i, a in enumerate(row):
            extra = {"AncientTree": 14, "SunShaft": 30, "Fireflies": 34}.get(a.name, 0)
            spots[a.name] = ((i - (len(row) - 1) / 2) * gap + extra, 0.0,
                             ROW_Z[cat] + (8 if a.name == "AncientTree" else 0))
    return spots


def height_of(a):
    top = 0.0
    for p in a.parts:
        if p["transparency"] >= 1:
            continue
        half = tuple(s / 2 for s in p["size"])
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    top = max(top, add(p["p"], apply(p["R"], (sx * half[0], sy * half[1], sz * half[2])))[1])
    return round(top, 1)


def build_instances(assets, spots, scatter_source, kit_name="CritterWoodsKit", scatter_name="ForestScatter",
                    categories=CATEGORIES, model_props=None):
    """model_props(asset) may return extra Model properties (for example LevelOfDetail)."""
    folders = {}
    for cat, _ in categories:
        folders[cat] = {"class": "Folder", "name": cat, "children": []}
    for a in assets:
        origin = spots[a.name]
        kids = []
        prim = f"{a.name}.1"
        for i, p in enumerate(a.parts, start=1):
            cf = (p["R"], add(p["p"], origin))
            props = {
                "Size": [round(v, 4) for v in p["size"]], "CFrame": cframe(*cf), "Color": list(p["color"]),
                "Material": p["material"], "Anchored": True, "CanCollide": p["collide"],
                "CanTouch": p["collide"], "CanQuery": p["collide"] or i == 1, "CastShadow": p["shadow"],
                "TopSurface": "Smooth", "BottomSurface": "Smooth",
            }
            if p["transparency"]:
                props["Transparency"] = p["transparency"]
            if p["shape"] == "ball":
                props["Shape"] = "Ball"
            elif p["shape"] == "cylinder":
                props["Shape"] = "Cylinder"
            if i == 1:
                props["PivotOffset"] = cframe(*compose(inverse(*cf), (IDENTITY, origin)))
            kids.append({
                "class": "WedgePart" if p["shape"] == "wedge" else "Part", "name": p["name"],
                **({"id": prim} if i == 1 else {}), "props": props, "children": p["effects"],
            })
        folders[a.category]["children"].append({
            "class": "Model", "name": a.name,
            "attrs": {"Category": a.category, "Zone": a.zone, "Height": height_of(a), "Description": a.note},
            "tags": [kit_name],
            "props": {"PrimaryPart": {"ref": prim}, **(model_props(a) if model_props else {})},
            "children": kids,
        })
    module = {"class": "ModuleScript", "name": scatter_name, "props": {"Source": scatter_source}}
    return [{"class": "Folder", "name": kit_name, "attrs": {"Version": 1},
             "children": [module] + [folders[c] for c, _ in categories]}]


# --------------------------------------------------------------- preview --

def viewer_parts(assets, placements):
    """Parts in the viewer's scene format. placements: list of (asset, position, yaw, scale)."""
    out = []
    r = lambda v: [round(x, 3) for x in v]
    for a, pos, yaw, k in placements:
        Ry = angles(0, yaw, 0)
        for p in a.parts:
            if p["transparency"] >= 1:
                continue
            R = matmul(Ry, p["R"])
            world = add(pos, apply(Ry, tuple(c * k for c in p["p"])))
            out.append({"n": p["name"], "s": p["shape"], "z": r(tuple(s * k for s in p["size"])), "cf": r(cframe(R, world)),
                        "c": r(p["color"]), "m": p["material"], "t": p["transparency"], "r": 0, "st": False,
                        "sh": p["shadow"]})
    return out


def preview_world(assets, spots):
    by = {a.name: a for a in assets}
    placements = [(a, spots[a.name], 0.0, 1.0) for a in assets]
    ground = [
        {"n": "Ground", "s": "block", "z": [440, 2, 150], "cf": [20, -1, 55, 1, 0, 0, 0, 1, 0, 0, 0, 1],
         "c": list(C("#6fd35a")), "m": "Grass", "t": 0, "r": 0, "st": False, "sh": True},
    ]

    # A strip of forest built from the kit that gets denser from left (edge) to right (heart).
    rng = random.Random(11)
    fx0, fz0, length, depth = -150.0, -230.0, 300.0, 120.0
    zones = [
        ("Edge", 1.2, 14, ["OakSmall", "OakMedium", "BirchTree", "PineSmall"],
         6, ["FlowerPatch", "GrassTuft", "GrassTuft", "BushSmall", "PetalScatter"]),
        ("Woodland", 3.5, 10, ["OakMedium", "OakLarge", "PineMedium", "PineSmall", "BirchTree"],
         7, ["BushSmall", "BushLarge", "BerryBush", "Fern", "GrassTuft", "Stump", "MushroomCluster", "LeafLitter"]),
        ("Deep", 8.0, 7, ["DeepOak", "DeepPine", "PineTall", "DeadTree"],
         9, ["Fern", "Fern", "DarkBush", "MossyRockSmall", "FallenLogMossy", "StumpMossy", "GlowMushrooms",
             "MossPatch"]),
        ("Heart", 11.0, 6, ["DeepOak", "DeepPine"], 10, ["Fern", "GlowMushrooms", "MossyRockLarge", "MossPatch"]),
    ]
    placed, forest = [], []
    seg = length / len(zones)
    for zi, (zone, trees, gap, tlist, plants, plist) in enumerate(zones):
        x0 = fx0 + zi * seg
        for per, g, names, is_tree in ((trees, gap, tlist, True), (plants, 2.5, plist, False)):
            count = round(seg * depth / 1000 * per)
            made = tries = 0
            while made < count and tries < count * 30:
                tries += 1
                x, z = rng.uniform(x0, x0 + seg), rng.uniform(fz0 - depth / 2, fz0 + depth / 2)
                if zone == "Heart" and math.dist((x, z), (fx0 + length - seg / 2, fz0)) < 16:
                    continue
                if abs(z - fz0 - 8 * math.sin(x / 30)) < 5:
                    continue
                if any(math.dist((x, z), q) < min(g, qg) for q, qg in placed):
                    continue
                forest.append((by[rng.choice(names)], (x, 0.0, z), rng.uniform(0, 360),
                               rng.uniform(0.85, 1.2) if is_tree else rng.uniform(0.8, 1.2)))
                placed.append(((x, z), g))
                made += 1
    heart = (fx0 + length - seg / 2, 0.0, fz0)
    forest.append((by["AncientTree"], heart, 30.0, 1.0))
    forest.append((by["MushroomRing"], add(heart, (0, 0, 13)), 0.0, 1.0))
    path = []
    for i in range(60):
        x = fx0 + i * length / 60
        path.append({"n": "Path", "s": "block", "z": [length / 60 + 1.2, 0.1, 7 - 3 * i / 60],
                     "cf": [x, 0.05, fz0 + 8 * math.sin(x / 30), 1, 0, 0, 0, 1, 0, 0, 0, 1],
                     "c": list(C("#e2b77f")), "m": "SmoothPlastic", "t": 0, "r": 0, "st": False, "sh": False})
    ground.append({"n": "Ground", "s": "block", "z": [length + 60, 2, depth + 40], "cf": [0, -1, fz0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                   "c": list(C("#5fc24e")), "m": "Grass", "t": 0, "r": 0, "st": False, "sh": True})

    parts = ground + path + viewer_parts(assets, placements) + viewer_parts(assets, forest)
    env = {
        "sky": [[0, "#3f9fff"], [0.55, "#96d0ff"], [1, "#dff2ff"]], "fog": ["#dff2ff", 380, 900],
        "sun": {"dir": [-0.5, 1.0, 0.45], "intensity": 2.5}, "hemi": ["#ffffff", "#8fb070", 1.45],
        "bloom": [0.4, 0.5, 0.9],
    }
    shots = {
        "kit": {"camera": {"pos": [0, 70, 165], "target": [0, 6, 50], "fov": 55},
                "shadow": {"center": [0, 0, 50], "radius": 170}},
        "trees": {"camera": {"pos": [10, 26, 60], "target": [10, 12, 0], "fov": 62},
                  "shadow": {"center": [0, 0, 10], "radius": 170}},
        "small": {"camera": {"pos": [0, 20, 128], "target": [0, 1.5, 78], "fov": 55},
                  "shadow": {"center": [0, 0, 80], "radius": 90}},
        "forest": {"camera": {"pos": [-175, 42, fz0 + 95], "target": [-40, 6, fz0], "fov": 55},
                   "shadow": {"center": [-40, 0, fz0], "radius": 190}},
        "deep": {"camera": {"pos": [20, 7, fz0 + 8 * math.sin(20 / 30)],
                            "target": [120, 7, fz0 + 8 * math.sin(120 / 30)], "fov": 68},
                 "shadow": {"center": [80, 0, fz0], "radius": 110}},
        "ancient": {"camera": {"pos": [spots["AncientTree"][0] - 30, 22, spots["AncientTree"][2] + 58],
                               "target": [spots["AncientTree"][0], 14, spots["AncientTree"][2]], "fov": 58},
                    "shadow": {"center": [spots["AncientTree"][0], 0, spots["AncientTree"][2]], "radius": 60}},
        "grass": {"camera": {"pos": [spots["GrassTuft"][0] + 4, 5, spots["GrassTuft"][2] + 14],
                             "target": [spots["GrassTuft"][0] + 4, 1, spots["GrassTuft"][2]], "fov": 50},
                  "shadow": {"center": [spots["GrassTuft"][0], 0, spots["GrassTuft"][2]], "radius": 30}},
    }
    return {"env": env, "parts": parts, "models": [], "texts": [], "sprites": [], "shots": shots}


def main():
    assets = make_kit()
    names = [a.name for a in assets]
    assert len(names) == len(set(names)), "duplicate asset names"
    spots = layout(assets)
    scatter = (HERE / "ForestScatter.lua").read_text()
    tree = build_instances(assets, spots, scatter)
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "kit.json").write_text(json.dumps(tree))
    (out / "world.json").write_text(json.dumps(preview_world(assets, spots)))
    total = 0
    for a in assets:
        total += len(a.parts)
        print(f"{a.category:7} {a.name:16} {a.zone:9} {len(a.parts):4} parts  {height_of(a):5} studs")
    print(f"{len(assets)} assets, {total} parts")

    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        cmd = ["cargo", "run", "--quiet", "--release", "--manifest-path",
               str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "kit.json"), target]
        if "--rbxmx" in sys.argv:
            cmd.append(sys.argv[sys.argv.index("--rbxmx") + 1])
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
