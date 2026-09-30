#!/usr/bin/env python3
"""Dark Woods kit: trees, crystals, plants, rocks, ground details and lights for the dark forest, built from Parts.

The look is "Moonlit Purple with crystals": twisted black trees with purple and indigo leaves and glowing berries,
crooked ash-grey trees, thorny brambles, and crystal clusters (blue, purple, pink) growing from the ground.

Made for mid-range phones:
  * plain anchored Parts only (no meshes, no Glass, no textures), a small part budget per model;
  * only trunks, logs and big rocks collide; everything else has CanCollide, CanTouch and CanQuery off;
  * small parts don't cast shadows, Neon is used for the glow instead of lights, and only a few models
    have a PointLight (short range, no shadows);
  * trees use Model.LevelOfDetail = StreamingMesh, so with StreamingEnabled far-away trees are drawn as
    cheap low-detail versions.

    python3 tools/dark-woods-kit/build_dark_kit.py                  -> build/kit.json and build/world.json (preview)
    python3 tools/dark-woods-kit/build_dark_kit.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
"""

import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "animal-models"))
sys.path.insert(0, str(HERE.parent / "forest-kit"))

from lib import add, angles, apply, hex_color, matmul, scale  # noqa: E402
from build_kit import Asset, build_instances, crown, height_of, roots, viewer_parts  # noqa: E402

SPARKLE_TEXTURE = "rbxasset://textures/particles/sparkles_main.dds"


def C(h):
    return hex_color(h)


# Leaves (darkest -> lightest).
PURPLE = [C("#2a1f4a"), C("#3b2a66"), C("#503a88"), C("#6a4fa8")]
INDIGO = [C("#1c1f4a"), C("#262d66"), C("#34408a"), C("#4656a8")]
PLUM = [C("#34183f"), C("#4a2258"), C("#632e74"), C("#7e3f90")]

BARK = C("#2b2233")
BARK_ASH = C("#4a4a5e")
MOONWOOD = C("#a9a4c0")
MOONWOOD_DARK = C("#7d7896")
VINE = C("#2f5a4a")
MOSS = C("#3d2f66")
STONE = [C("#2a2638"), C("#353047"), C("#443d5a")]

PINK, VIOLET, CYAN, MOON = "#ff7be5", "#c77dff", "#5ef0ff", "#cfe0ff"
# Crystal colors: (body, glowing edge).
CRYSTALS = {"blue": (C("#4f9fd8"), C("#9ff0ff")), "purple": (C("#8a5cd8"), C("#d9b8ff")),
            "pink": (C("#d05ca8"), C("#ffb0e6"))}

DETAIL = dict(collide=False, shadow=False)
GLOW = dict(material="Neon", collide=False, shadow=False)


def light(color, brightness=1.0, range_=12):
    return {"class": "PointLight", "name": "Glow",
            "props": {"Color": list(C(color)), "Brightness": brightness, "Range": range_, "Shadows": False}}


def bent_trunk(a, pts, widths, color, name="Trunk", collide=True):
    """Crooked trunk through a list of points, with a joint block at every bend (no gaps)."""
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        a.rod(name, p, q, widths[i], color, collide=collide)
        if i:
            w = widths[i - 1] * 0.98
            a.octo(f"{name}Joint", (w, w, w), p, color, collide=collide)


def crystal(a, base, w, h, kind, tilt=(0, 0, 0), yaw=0.0):
    """One crystal: a square prism with a pointed ridge and glowing edges. 5 parts, no transparency."""
    body_c, glow_c = CRYSTALS[kind]
    R = matmul(angles(*tilt), angles(0, yaw, 0))
    body = h * 0.62
    tip = h - body
    at = lambda x, y, z: add(base, apply(R, (x, y, z)))
    a.box("Crystal", (w, body, w), at(0, body / 2, 0), body_c, R=R, **DETAIL)
    for sgn in (-1, 1):
        a.wedge("CrystalTip", (w, tip, w / 2), at(0, body + tip / 2, sgn * w / 4), body_c,
                R=matmul(R, angles(0, 90 + 90 * sgn, 0)), **DETAIL)
    # Glowing edge down the front corner and a bright core at the top of the prism.
    a.box("CrystalEdge", (w * 0.2, body * 0.92, w * 0.2), at(w * 0.42, body * 0.48, -w * 0.42), glow_c, R=R, **GLOW)
    a.box("CrystalGlint", (w * 0.55, w * 0.12, w * 0.55), at(0, body + 0.02, 0), glow_c, R=R, **GLOW)


def crystal_group(a, center, rng, kinds, n, h=(2.2, 4.0), w=(0.7, 1.1), spread=0.8, tilt_max=25):
    for i in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, spread)
        hh = rng.uniform(*h)
        tilt = (math.sin(ang) * tilt_max * (r / max(spread, 0.01) + 0.3), 0,
                -math.cos(ang) * tilt_max * (r / max(spread, 0.01) + 0.3))
        crystal(a, add(center, (math.cos(ang) * r, 0, math.sin(ang) * r)), rng.uniform(*w), hh,
                kinds[i % len(kinds)], tilt=tilt, yaw=rng.uniform(0, 90))


def berries(a, center, rng, n, radius, height, colors=(PINK, VIOLET)):
    for _ in range(n):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(radius * 0.75, radius)
        a.box("Berry", (0.55, 0.55, 0.55), add(center, (math.cos(ang) * r, rng.uniform(-0.3, 1.0) * height,
                                                       math.sin(ang) * r)),
              C(rng.choice(colors)), rot=(45, 45, 0), **GLOW)


def vine(a, top, length, rng, leaves=2):
    a.box("Vine", (0.18, length, 0.18), add(top, (0, -length / 2, 0)), VINE, **DETAIL)
    for i in range(leaves):
        y = -length * (i + 1) / (leaves + 1)
        a.box("VineLeaf", (0.55, 0.12, 0.35), add(top, (0.2 if i % 2 else -0.2, y, 0)), PURPLE[3],
              rot=(0, rng.uniform(0, 180), 25 if i % 2 else -25), **DETAIL)


def flat(a, name, size, pos, color, yaw, material="SmoothPlastic", transparency=0.0):
    a.box(name, (size[0], 0.06, size[1]), (pos[0], 0.03 + pos[1], pos[2]), color, rot=(0, yaw, 0),
          material=material, transparency=transparency, **DETAIL)


# ------------------------------------------------------------------- trees --

def shadow_oak(name, k, pal, rng, zone, note, clusters=2, vines=2, n_berries=8, root_n=5):
    a = Asset(name, "Trees", zone, note)
    lean = rng.uniform(0, 360)
    d = apply(angles(0, lean, 0), (0, 0, -1))
    pts = [(0, 0, 0), (d[0] * 1.2 * k, 5 * k, d[2] * 1.2 * k), (-d[0] * 0.6 * k, 10 * k, -d[2] * 0.6 * k),
           (d[0] * 0.8 * k, 14 * k, d[2] * 0.8 * k)]
    bent_trunk(a, pts, [2.2 * k, 1.8 * k, 1.4 * k], BARK)
    roots(a, 2.2 * k, BARK, rng, n=root_n, length=2.6 * k, height=1.6 * k)
    top = pts[-1]
    crown(a, add(top, (0, 3 * k, 0)), (5.2 * k, 4.2 * k, 5.2 * k), pal, rng, n=10)
    tips = []
    for i in range(clusters):
        ang = math.radians(lean + 120 + i * 360 / max(clusters, 1) * 0.7)
        c = (math.cos(ang) * 4.8 * k, 12.5 * k, math.sin(ang) * 4.8 * k)
        a.rod("Branch", pts[2], c, 0.7 * k, BARK)
        crown(a, c, (3.4 * k, 2.8 * k, 3.4 * k), pal, rng, n=5)
        tips.append(c)
    for c in tips[:vines]:
        vine(a, add(c, (0, -1.2 * k, 0)), rng.uniform(4.0, 6.0) * k, rng)
    berries(a, add(top, (0, 3 * k, 0)), rng, n_berries, 4.4 * k, 2.2 * k)
    return a


def shadow_pine(rng, k=1.25):
    a = Asset("ShadowPine", "Trees", "Deep", "Tall dark pine with glowing violet tips")
    th = 3.2 * k
    a.octo("Trunk", (1.3 * k, th + 1.0, 1.3 * k), (0, (th + 1.0) / 2, 0), BARK)
    tiers, y = 5, th
    for i in range(tiers):
        f = 1 - i / (tiers + 0.6)
        w = 8.8 * k * f
        hgt = 4.2 * k * (0.75 + 0.25 * f)
        color = INDIGO[min(3, i)]
        yaw0 = rng.uniform(0, 90)
        for j, yaw in enumerate((0, 90, 180, 270, 45, 135, 225, 315)):
            R = angles(0, yaw0 + yaw, 0)
            ww = w if j < 4 else w * 0.94
            a.wedge("Needles", (ww, hgt, ww / 2), add((0, y + hgt / 2, 0), apply(R, (0, 0, -ww / 4))), color, R=R,
                    collide=False)
        if i % 2 == 0:
            for j in range(4):
                R = angles(0, yaw0 + j * 90 + 45, 0)
                a.box("GlowTip", (0.45, 0.45, 0.45), add((0, y + 0.3, 0), apply(R, (0, 0, -w * 0.47))), C(VIOLET),
                      R=R, **GLOW)
        y += hgt * 0.55
    a.box("TopGlow", (0.6, 0.6, 0.6), (0, y + 1.2 * k, 0), C(PINK), rot=(45, 45, 0), **GLOW)
    return a


def gnarled_tree(rng, name="GnarledTree", crystals=False, k=1.0):
    zone = "Heart" if crystals else "Gloom"
    note = "Crooked bare tree with crystals growing at the forks" if crystals else "Crooked bare ash-grey tree"
    a = Asset(name, "Trees", zone, note)
    bent_trunk(a, [(0, 0, 0), (0.8 * k, 4 * k, 0), (-0.6 * k, 8 * k, 0.4 * k), (0.3 * k, 11 * k, -0.3 * k)],
               [1.5 * k, 1.2 * k, 0.9 * k], BARK_ASH)
    roots(a, 1.5 * k, BARK_ASH, rng, n=4)
    forks = []
    for yaw, y0, out, up in ((30, 6, 3.6, 3), (150, 8, 3.2, 3.5), (260, 9.5, 2.8, 3), (340, 4.5, 3.0, 2)):
        d = apply(angles(0, yaw + rng.uniform(-15, 15), 0), (0, 0, -1))
        mid = (d[0] * out * 0.6 * k, (y0 + up * 0.8) * k, d[2] * out * 0.6 * k)
        tip = (d[0] * out * k, (y0 + up) * k, d[2] * out * k)
        a.rod("Branch", (0, y0 * k, 0), mid, 0.5 * k, BARK_ASH)
        a.rod("Branch", mid, tip, 0.3 * k, BARK_ASH, octagon=False)
        a.rod("Twig", tip, add(tip, (d[2] * 1.2, 1.1, -d[0] * 1.2)), 0.2, BARK_ASH, octagon=False, collide=False)
        forks.append(mid)
    if crystals:
        for i, f in enumerate(forks[:3]):
            crystal_group(a, add(f, (0, 0.1, 0)), rng, [("blue", "purple", "pink")[i]], 2, h=(1.0, 1.8),
                          w=(0.35, 0.55), spread=0.2)
        crystal_group(a, (0, 0, 0), rng, ["purple", "blue"], 3, h=(1.2, 2.2), w=(0.5, 0.8), spread=1.6)
    return a


def moonwood_tree(rng):
    a = Asset("MoonwoodTree", "Trees", "Heart",
              "Huge silver tree for the Heart: purple crown, glowing runes, crystals at its roots, two lanterns")
    h, w = 19.0, 4.6
    a.octo("Trunk", (w, h * 0.6, w), (0, h * 0.3, 0), MOONWOOD)
    a.octo("Trunk", (w * 0.8, h * 0.5, w * 0.8), (0, h * 0.78, 0), MOONWOOD, yaw=20)
    roots(a, w, MOONWOOD_DARK, rng, n=6, length=5.2, height=3.6)
    for i in range(5):
        d = apply(angles(0, i * 72 + 20, 0), (0, 0, -1))
        a.rod("Root", (d[0] * w * 0.3, 2.6, d[2] * w * 0.3), (d[0] * (w * 0.5 + 5.6), 0.3, d[2] * (w * 0.5 + 5.6)),
              0.95, MOONWOOD_DARK)
    # Glowing runes on the bark, on two sides.
    for side in (0, 180):
        R = angles(0, side, 0)
        for x, y, sw, sh in [(0, 11.2, 0.4, 2.4), (-0.7, 9.9, 1.7, 0.4), (0.55, 8.3, 0.4, 2.0), (0, 6.6, 1.9, 0.4),
                             (-0.5, 5.0, 0.4, 1.8)]:
            a.box("Rune", (sw, sh, 0.12), apply(R, (x, y, -w / 2 - 0.02)), C(CYAN), R=R, **GLOW)
    a.parts[-1]["effects"].append(light(CYAN, 1.0, 14))
    # Crown: four side clusters and a big top.
    for i in range(4):
        ang = math.radians(45 + i * 90)
        c = (math.cos(ang) * 12.0, h - 1.0 + (i % 2) * 2.0, math.sin(ang) * 12.0)
        mid = (math.cos(ang) * 6.0, h * 0.8, math.sin(ang) * 6.0)
        bent_trunk(a, [(0, h * 0.62, 0), mid, c], [1.5, 1.1], MOONWOOD, name="Branch")
        crown(a, c, (6.4, 4.2, 6.4), PURPLE if i % 2 else PLUM, rng, n=7)
        if i < 2:
            # A lantern hanging from this branch.
            lx, lz = c[0] * 0.62, c[2] * 0.62
            a.box("Chain", (0.12, 3.0, 0.12), (lx, h - 1.6, lz), C("#8d8d99"), **DETAIL)
            a.box("LanternCap", (1.2, 0.3, 1.2), (lx, h - 3.2, lz), C("#1b1420"), **DETAIL)
            a.box("Lantern", (0.9, 1.1, 0.9), (lx, h - 3.9, lz), C(VIOLET), **GLOW,
                  effects=[light(VIOLET, 1.2, 14)] if i == 0 else None)
            a.box("LanternBase", (1.1, 0.25, 1.1), (lx, h - 4.55, lz), C("#1b1420"), **DETAIL)
    crown(a, (0, h + 3.5, 0), (8.5, 5.6, 8.5), PURPLE, rng, n=12)
    crown(a, (0, h + 8.2, 0), (5.0, 3.4, 5.0), PLUM, rng, n=5)
    berries(a, (0, h + 3.5, 0), rng, 12, 6.2, 2.2)
    # Crystals growing between the roots.
    for i, kind in enumerate(("blue", "pink", "purple")):
        ang = math.radians(i * 120 + 50)
        crystal_group(a, (math.cos(ang) * (w * 0.5 + 3.2), 0, math.sin(ang) * (w * 0.5 + 3.2)), rng,
                      [kind, "purple"], 3, h=(2.6, 4.6), w=(0.8, 1.2), spread=1.0)
    return a


# ------------------------------------------------------------ wood & roots --

def twisted_stump(rng):
    a = Asset("TwistedStump", "Wood", "Deep", "Dark stump with purple moss and glowing berries")
    a.octo("Stump", (2.8, 2.0, 2.8), (0, 1.0, 0), BARK)
    a.octo("CutTop", (2.4, 0.12, 2.4), (0, 2.04, 0), C("#5a4868"), collide=False)
    a.octo("Ring", (1.3, 0.14, 1.3), (0, 2.06, 0), C("#44344f"), collide=False)
    roots(a, 2.8, BARK, rng, n=4, length=1.4, height=0.9)
    a.box("Moss", (2.2, 0.3, 1.4), (0.2, 2.12, 0.4), MOSS, rot=(0, 20, 0), **DETAIL)
    berries(a, (0, 1.0, 0), rng, 3, 1.5, 0.6)
    return a


def fallen_log(rng):
    a = Asset("FallenShadowLog", "Wood", "Deep", "Fallen dark log with purple moss and a crystal sprouting from it")
    d, length = 2.4, 12.0
    for yaw in (0, 45):
        a.box("Log", (length, d * (1 if yaw == 0 else 0.96), d * (1 if yaw == 0 else 0.96)), (0, d / 2 - 0.05, 0), BARK,
              rot=(yaw, 0, 0))
    for sgn in (-1, 1):
        a.box("CutEnd", (0.12, d * 0.8, d * 0.8), (sgn * length / 2, d / 2 - 0.05, 0), C("#5a4868"), **DETAIL)
    for x in (-3.5, 1.5):
        a.box("Moss", (rng.uniform(2.2, 3.2), 0.3, d * 0.8), (x, d + 0.02, 0), MOSS, rot=(0, rng.uniform(-8, 8), 0),
              **DETAIL)
    a.rod("Branch", (2.0, d * 0.7, 0), (3.2, d + 1.6, -1.2), 0.45, BARK, collide=False)
    crystal_group(a, (-1.0, d - 0.1, 0.2), rng, ["purple", "blue"], 2, h=(1.4, 2.2), w=(0.5, 0.7), spread=0.3)
    return a


def root_arch(rng):
    a = Asset("RootArch", "Wood", "Gloom", "Two giant roots arching over a path (about 9 studs wide)")
    for z, lift in ((-0.8, 0.0), (0.9, 1.2)):
        pts = []
        for i in range(9):
            t = i / 8
            pts.append((-6.5 + 13 * t, (11 + lift) * math.sin(math.pi * t) ** 0.8, z + 0.6 * math.sin(2 * math.pi * t)))
        bent_trunk(a, pts, [1.7, 1.5, 1.3, 1.1, 1.1, 1.3, 1.5, 1.7], BARK, name="Root")
        vine(a, add(pts[3], (0, -0.4, 0)), 4.5, rng)
    berries(a, (0, 11, 0), rng, 4, 1.5, 0.5)
    return a


# ----------------------------------------------------------------- plants --

def thorn_bramble(rng, name="ThornBramble", n=9, size=3.2):
    a = Asset(name, "Plants", "Deep", "Tangle of dark purple thorny branches")
    for i in range(n):
        yaw, pitch = rng.uniform(0, 360), rng.uniform(15, 55)
        d = apply(matmul(angles(0, yaw, 0), angles(pitch, 0, 0)), (0, 0, -1))
        start = (rng.uniform(-0.5, 0.5), 0.05, rng.uniform(-0.5, 0.5))
        end = add(start, (d[0] * size, abs(d[1]) * size + 0.6, d[2] * size))
        a.rod("Thorn", start, end, 0.28, C("#3d2450"), octagon=False, collide=False, shadow=False)
        a.wedge("Spike", (0.2, 0.5, 0.3), add(end, (0, 0.2, 0)), C("#b58cff"), **DETAIL)
    return a


def shadow_bush(rng, name="ShadowBush", k=1.0, pal=PURPLE):
    a = Asset(name, "Plants", "Deep", "Round purple bush with glowing berries")
    crown(a, (0, 1.3 * k, 0), (2.4 * k, 1.7 * k, 2.4 * k), pal, rng, n=6, name="Bush")
    berries(a, (0, 1.3 * k, 0), rng, 4, 1.8 * k, 0.8 * k)
    return a


def shadow_fern(rng):
    a = Asset("ShadowFern", "Plants", "Deep", "Dark blue-purple fern with glowing tips")
    pal = (C("#2a2f66"), C("#3b3a80"))
    for i in range(7):
        yaw = i * 360 / 7 + rng.uniform(-10, 10)
        tilt = rng.uniform(50, 66)
        length = rng.uniform(2.6, 3.3)
        R = matmul(angles(0, yaw, 0), angles(-tilt, 0, 0))
        a.box("Frond", (0.75, length, 0.12), apply(R, (0, length / 2, 0)), pal[i % 2], R=R, **DETAIL)
        if i % 2 == 0:
            a.box("Tip", (0.35, 0.35, 0.14), apply(R, (0, length, 0)), C(CYAN), R=R, **GLOW)
    return a


def night_blooms(rng):
    a = Asset("NightBlooms", "Plants", "Deep", "Stalks with glowing moon-blue flower bulbs")
    for i in range(5):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 0.9)
        h = rng.uniform(1.6, 2.8)
        base = (math.cos(ang) * r, 0, math.sin(ang) * r)
        R = angles(rng.uniform(-10, 10), 0, rng.uniform(-10, 10))
        a.box("Stalk", (0.16, h, 0.16), add(base, apply(R, (0, h / 2, 0))), VINE, R=R, **DETAIL)
        a.box("Bulb", (0.38, 0.5, 0.38), add(base, apply(R, (0, h + 0.15, 0))), C("#9fd0ff"), R=R, **GLOW)
        a.box("Leaf", (0.8, 0.1, 0.35), add(base, (0, 0.35, 0)), C("#2a2f66"), rot=(0, rng.uniform(0, 180), -20),
              **DETAIL)
    return a


def glow_shrooms(rng):
    a = Asset("GlowShrooms", "Plants", "Deep", "Little glowing violet and pink mushrooms")
    for i in range(5):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 1.3)
        k = rng.uniform(0.45, 0.9)
        p = (math.cos(ang) * r, 0, math.sin(ang) * r)
        a.box("Stem", (0.35 * k, 1.2 * k, 0.35 * k), add(p, (0, 0.6 * k, 0)), C("#e9e1d0"), **DETAIL)
        a.octo("Cap", (1.3 * k, 0.45 * k, 1.3 * k), add(p, (0, 1.3 * k, 0)), C(PINK if i % 2 else VIOLET),
               material="Neon", **DETAIL)
    return a


def hanging_vines(rng):
    a = Asset("HangingVines", "Plants", "Deep",
              "Vines to hang under a branch: the pivot is at the TOP, so PivotTo(branchPoint) hangs them down")
    for i in range(5):
        x, z = rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2)
        vine(a, (x, 0, z), rng.uniform(3.5, 7.0), rng, leaves=3)
        if i % 2 == 0:
            a.box("Pod", (0.5, 0.5, 0.5), (x, -0.3 - rng.uniform(3.5, 3.6), z), C(PINK), rot=(45, 45, 0), **GLOW)
    a.box("Clump", (2.4, 0.5, 2.4), (0, -0.1, 0), PURPLE[2], rot=(0, 20, 0), **DETAIL)
    return a


# --------------------------------------------------------------- crystals --

def crystal_small(rng):
    a = Asset("CrystalSmall", "Crystals", "Deep", "Two small crystals on a stone")
    a.box("Rock", (1.8, 0.8, 1.6), (0, 0.3, 0), STONE[1], rot=(0, rng.uniform(0, 90), 5), **DETAIL)
    crystal_group(a, (0, 0.5, 0), rng, ["purple", "blue"], 2, h=(1.4, 2.2), w=(0.5, 0.7), spread=0.3)
    return a


def crystal_cluster(rng, name, kinds, note):
    a = Asset(name, "Crystals", "Deep", note)
    a.box("Rock", (3.4, 1.4, 3.0), (0, 0.6, 0), STONE[1], rot=(0, rng.uniform(0, 90), 6))
    a.box("Rock", (2.2, 1.0, 2.0), (1.0, 0.4, 0.8), STONE[0], rot=(0, rng.uniform(0, 90), -8), **DETAIL)
    crystal_group(a, (0, 0.9, 0), rng, kinds, 5, h=(2.2, 4.2), w=(0.7, 1.15), spread=0.8)
    return a


def crystal_large(rng):
    a = Asset("CrystalLarge", "Crystals", "Heart", "Big crystal formation (9 studs) that lights up the area")
    a.box("Rock", (6, 2, 5), (0, 0.9, 0), STONE[1], rot=(0, 15, 4))
    a.box("Rock", (3.5, 1.4, 3.2), (-2.2, 0.6, 1.4), STONE[0], rot=(0, 50, -6))
    crystal(a, (0, 1.4, 0), 2.0, 8.5, "purple", tilt=(4, 0, -6), yaw=10)
    crystal(a, (1.6, 1.2, 0.6), 1.4, 5.5, "blue", tilt=(-10, 0, -24), yaw=30)
    crystal(a, (-1.5, 1.2, -0.5), 1.3, 5.0, "pink", tilt=(12, 0, 22), yaw=60)
    crystal_group(a, (0.4, 1.3, 0.2), rng, ["blue", "pink", "purple"], 4, h=(1.8, 3.2), w=(0.6, 0.9), spread=2.0,
                  tilt_max=35)
    a.parts[0]["effects"].append(light(VIOLET, 1.3, 16))
    return a


def crystal_shards(rng):
    a = Asset("CrystalShards", "Crystals", "Deep", "Loose little crystal shards on the ground")
    for i in range(6):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0.3, 2.4)
        kind = ("blue", "purple", "pink")[i % 3]
        body, glow = CRYSTALS[kind]
        s = rng.uniform(0.3, 0.55)
        a.box("Shard", (s, s * 2, s), (math.cos(ang) * r, s * 0.35, math.sin(ang) * r), body if i % 2 else glow,
              rot=(rng.uniform(-50, 50), rng.uniform(0, 90), rng.uniform(-50, 50)),
              material="SmoothPlastic" if i % 2 else "Neon", **DETAIL)
    return a


# ------------------------------------------------------------------ rocks --

def shadow_boulder(rng, name="ShadowBoulder", k=1.0):
    a = Asset(name, "Rocks", "Gloom", "Dark rock with purple moss")
    a.box("Rock", (3.2 * k, 2.2 * k, 2.8 * k), (0, 1.0 * k, 0), STONE[1], rot=(rng.uniform(-6, 6), rng.uniform(0, 90), 8))
    a.box("Rock", (2.4 * k, 2.0 * k, 2.4 * k), (0.9 * k, 1.1 * k, 0.4 * k), STONE[2],
          rot=(rng.uniform(-20, 20), rng.uniform(0, 90), rng.uniform(-20, 20)))
    a.box("Rock", (2.0 * k, 1.4 * k, 2.0 * k), (-1.1 * k, 0.6 * k, -0.3 * k), STONE[0],
          rot=(rng.uniform(-20, 20), rng.uniform(0, 90), rng.uniform(-20, 20)))
    a.box("Moss", (2.8 * k, 0.4 * k, 2.2 * k), (0.1 * k, 2.15 * k, 0), MOSS, rot=(0, rng.uniform(0, 90), 6), **DETAIL)
    return a


def rune_stone(rng):
    a = Asset("RuneStone", "Rocks", "Heart", "Standing stone with glowing runes")
    a.box("Stone", (2.6, 7, 1.4), (0, 3.4, 0), C("#3a3848"), rot=(0, 0, 3))
    a.box("StoneTop", (2.0, 1.0, 1.2), (0.3, 7.2, 0), C("#3a3848"), rot=(0, 0, 12))
    for sgn in (-1, 1):
        for x, y, w, h in [(0, 5.6, 0.2, 1.2), (-0.35, 5.0, 0.8, 0.2), (0.3, 4.2, 0.2, 1.0), (0, 3.3, 1.0, 0.2),
                           (-0.3, 2.5, 0.2, 0.9)]:
            a.box("Rune", (w, h, 0.1), (x, y, sgn * 0.72), C(CYAN), **GLOW)
    a.box("Moss", (2.8, 0.3, 1.8), (0, 0.15, 0), MOSS, **DETAIL)
    return a


def rune_circle(rng):
    a = Asset("RuneCircle", "Rocks", "Heart", "Ring of six small rune stones (about 14 studs across)")
    for i in range(6):
        ang = i * math.pi / 3
        yaw = -math.degrees(ang) + 90
        R = angles(0, yaw, rng.uniform(-4, 4))
        pos = (math.cos(ang) * 7, 0, math.sin(ang) * 7)
        h = rng.uniform(3.0, 4.2)
        a.box("Stone", (1.6, h, 0.9), add(pos, (0, h / 2 - 0.1, 0)), C("#3a3848"), R=R)
        a.box("Rune", (0.2, h * 0.45, 0.1), add(pos, apply(R, (0, h * 0.55, -0.47))), C(CYAN), R=R, **GLOW)
        a.box("Rune", (0.7, 0.18, 0.1), add(pos, apply(R, (0, h * 0.62, -0.47))), C(CYAN), R=R, **GLOW)
    for i in range(12):
        ang = i * math.pi / 6 + math.pi / 12
        a.box("GlowStone", (0.6, 0.2, 0.6), (math.cos(ang) * 5.2, 0.1, math.sin(ang) * 5.2), C(VIOLET),
              rot=(0, 45, 0), **GLOW)
    return a


# ----------------------------------------------------------------- ground --

def purple_leaves(rng):
    a = Asset("PurpleLeaves", "Ground", "Deep", "Fallen purple and blue leaves")
    for i in range(16):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 3.4)
        s = rng.uniform(0.45, 0.8)
        flat(a, "Leaf", (s, s * 0.6), (math.cos(ang) * r, i * 0.004, math.sin(ang) * r),
             C(rng.choice(["#6a4fa8", "#4656a8", "#8a5cc8", "#3b2a66"])), rng.uniform(0, 180))
    return a


def glow_moss(rng):
    a = Asset("GlowMoss", "Ground", "Deep", "Dark moss with glowing violet and blue specks")
    for i in range(5):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2.0)
        s = rng.uniform(1.6, 2.8)
        flat(a, "Moss", (s, s * 0.8), (math.cos(ang) * r, i * 0.004, math.sin(ang) * r), MOSS, rng.uniform(0, 90))
    for i in range(10):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2.8)
        flat(a, "Speck", (0.25, 0.25), (math.cos(ang) * r, 0.03, math.sin(ang) * r), C(VIOLET if i % 2 else CYAN), 45,
             material="Neon")
    return a


def fog_patch(rng):
    a = Asset("FogPatch", "Ground", "Deep", "Low mist on the ground (see-through, use a handful, not hundreds)")
    for i in range(4):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 3)
        s = rng.uniform(7, 10)
        a.box("Fog", (s, 0.8, s * 0.7), (math.cos(ang) * r, 0.5 + i * 0.25, math.sin(ang) * r), C("#c9c4ff"),
              rot=(0, rng.uniform(0, 90), 0), transparency=0.95, **DETAIL)
    return a


def stepping_stones(rng):
    a = Asset("SteppingStones", "Ground", "Deep", "Row of flat stones with glowing moss, for paths (10 studs long)")
    for i in range(5):
        z = -4 + i * 2.1
        x = 0.5 * math.sin(i * 1.3)
        a.octo("Stone", (1.8, 0.3, 1.5), (x, 0.15, z), STONE[2], yaw=rng.uniform(0, 45))
        a.box("Glow", (0.3, 0.08, 0.3), (x + 0.9, 0.04, z + 0.3), C(VIOLET if i % 2 else CYAN), **GLOW)
    return a


# ----------------------------------------------------------------- lights --

def wisp_lantern(rng):
    a = Asset("WispLantern", "Lights", "Deep", "Crooked post with a glowing violet lantern (has a light)")
    a.rod("Post", (0, 0, 0), (0.3, 7, 0), 0.6, BARK)
    a.rod("Arm", (0.3, 6.6, 0), (2.2, 7.3, 0), 0.4, BARK, octagon=False)
    a.box("Chain", (0.1, 1.0, 0.1), (2.1, 6.7, 0), C("#8d8d99"), **DETAIL)
    a.box("LanternCap", (1.2, 0.3, 1.2), (2.1, 6.1, 0), C("#1b1420"), **DETAIL)
    a.box("Lantern", (0.9, 1.1, 0.9), (2.1, 5.4, 0), C(VIOLET), **GLOW, effects=[light(VIOLET, 1.2, 14)])
    a.box("LanternBase", (1.1, 0.25, 1.1), (2.1, 4.75, 0), C("#1b1420"), **DETAIL)
    return a


def hanging_lantern(rng):
    a = Asset("HangingLantern", "Lights", "Deep",
              "Lantern on a chain; the pivot is at the TOP of the chain, so PivotTo(branchPoint) hangs it")
    a.box("Chain", (0.12, 2.5, 0.12), (0, -1.25, 0), C("#8d8d99"), **DETAIL)
    a.box("LanternCap", (1.2, 0.3, 1.2), (0, -2.6, 0), C("#1b1420"), **DETAIL)
    a.box("Lantern", (0.9, 1.1, 0.9), (0, -3.3, 0), C(PINK), **GLOW, effects=[light(PINK, 1.0, 12)])
    a.box("LanternBase", (1.1, 0.25, 1.1), (0, -3.95, 0), C("#1b1420"), **DETAIL)
    return a


def moon_shaft(rng):
    a = Asset("MoonShaft", "Lights", "Heart", "Soft beam of moonlight falling into a clearing (see-through)")
    for w, t in ((6.0, 0.93), (3.4, 0.88)):
        a.box("Moonlight", (w, 36, w), (0, 18, 0), C(MOON), material="Neon", transparency=t, rot=(0, 0, 10), **DETAIL)
    return a


def wisps(rng):
    a = Asset("Wisps", "Lights", "Deep", "Invisible box with little violet and pink lights drifting around")
    em = {"class": "ParticleEmitter", "name": "Wisps", "props": {
        "Texture": SPARKLE_TEXTURE, "Rate": 3, "Lifetime": [4, 7], "Speed": [0.3, 0.9], "SpreadAngle": [180, 180],
        "LightEmission": 1, "LightInfluence": 0, "Size": [[0, 0.25], [0.5, 0.45], [1, 0]],
        "Transparency": [[0, 1], [0.2, 0.1], [0.8, 0.2], [1, 1]],
        "Color": [[0, *C(VIOLET)], [1, *C(PINK)]], "RotSpeed": [-60, 60]}}
    a.box("WispZone", (16, 6, 16), (0, 3, 0), C("#ffffff"), transparency=1, collide=False, shadow=False, effects=[em])
    return a


# -------------------------------------------------------------------- kit --

def make_kit():
    rng = random.Random(13)
    return [
        shadow_oak("ShadowOakSmall", 0.7, PURPLE, rng, "Gloom", "Young twisted oak with purple leaves", clusters=1,
                   vines=0, n_berries=4, root_n=4),
        shadow_oak("ShadowOak", 1.0, PURPLE, rng, "Deep", "Twisted black oak with purple leaves and glowing berries"),
        shadow_oak("ShadowOakLarge", 1.35, PURPLE, rng, "Deep", "Big twisted oak with three leaf clusters and vines",
                   clusters=3, vines=3, n_berries=12, root_n=6),
        shadow_oak("IndigoOak", 1.1, INDIGO, rng, "Deep", "Twisted oak with dark-blue leaves"),
        shadow_oak("PlumOak", 1.0, PLUM, rng, "Heart", "Twisted oak with plum-purple leaves", clusters=2, vines=1),
        shadow_pine(rng),
        gnarled_tree(rng),
        gnarled_tree(rng, "GnarledCrystalTree", crystals=True),
        moonwood_tree(rng),
        twisted_stump(rng), fallen_log(rng), root_arch(rng),
        thorn_bramble(rng), thorn_bramble(rng, "ThornBrambleSmall", n=6, size=2.0),
        shadow_bush(rng), shadow_bush(rng, "IndigoBush", k=1.2, pal=INDIGO),
        shadow_fern(rng), night_blooms(rng), glow_shrooms(rng), hanging_vines(rng),
        crystal_small(rng),
        crystal_cluster(rng, "CrystalCluster", ["blue", "purple"], "Crystal cluster in blue and purple on a rock"),
        crystal_cluster(rng, "CrystalClusterPink", ["pink", "purple"], "Crystal cluster in pink and purple on a rock"),
        crystal_large(rng), crystal_shards(rng),
        shadow_boulder(rng), shadow_boulder(rng, "ShadowBoulderLarge", k=1.6), rune_stone(rng), rune_circle(rng),
        purple_leaves(rng), glow_moss(rng), fog_patch(rng), stepping_stones(rng),
        wisp_lantern(rng), hanging_lantern(rng), moon_shaft(rng), wisps(rng),
    ]


CATEGORIES = [("Trees", 34.0), ("Wood", 22.0), ("Plants", 10.0), ("Crystals", 14.0), ("Rocks", 16.0),
              ("Ground", 12.0), ("Lights", 14.0)]
ROW_Z = {"Trees": 0.0, "Wood": 44.0, "Plants": 66.0, "Crystals": 84.0, "Rocks": 104.0, "Ground": 126.0,
         "Lights": 144.0}
HANGING = {"HangingVines", "HangingLantern"}


def layout(assets):
    spots = {}
    for cat, gap in CATEGORIES:
        row = [a for a in assets if a.category == cat]
        for i, a in enumerate(row):
            extra = {"MoonwoodTree": 16}.get(a.name, 0)
            y = 8.0 if a.name in HANGING else 0.0
            spots[a.name] = ((i - (len(row) - 1) / 2) * gap + extra, y, ROW_Z[cat] + (8 if a.name == "MoonwoodTree" else 0))
    return spots


def model_props(a):
    return {"LevelOfDetail": "StreamingMesh"} if a.category == "Trees" else {}


# ---------------------------------------------------------------- preview --

def preview_world(assets, spots):
    by = {a.name: a for a in assets}
    r = lambda v: [round(x, 3) for x in v]

    def block(name, size, pos, color, material="SmoothPlastic", rot=0.0):
        R = angles(0, rot, 0)
        return {"n": name, "s": "block", "z": list(size), "cf": r([*pos, *R[0], *R[1], *R[2]]), "c": list(C(color)),
                "m": material, "t": 0, "r": 0, "st": False, "sh": True}

    parts = [block("Ground", (420, 2, 190), (20, -1, 72), "#231d38")]
    catalog = [(a, spots[a.name], 0.0, 1.0) for a in assets]

    # A strip of dark forest: Gloom on the left, Deep in the middle, the Heart on the right.
    rng = random.Random(21)
    fx0, fz0, length, depth = -160.0, -240.0, 320.0, 130.0
    parts.append(block("Ground", (length + 60, 2, depth + 40), (0, -1, fz0), "#231d38"))
    zones = [
        ("Gloom", 3.0, 11, ["ShadowOakSmall", "ShadowOak", "GnarledTree", "IndigoOak"],
         7, ["ThornBrambleSmall", "PurpleLeaves", "ShadowBoulder", "ShadowFern", "CrystalShards", "ShadowBush"]),
        ("Deep", 6.5, 9, ["ShadowOak", "ShadowOakLarge", "IndigoOak", "ShadowPine", "GnarledTree"],
         9, ["ThornBramble", "ShadowFern", "GlowShrooms", "CrystalSmall", "CrystalCluster", "PurpleLeaves",
             "GlowMoss", "IndigoBush", "NightBlooms", "TwistedStump", "FallenShadowLog"]),
        ("Heart", 5.0, 10, ["PlumOak", "GnarledCrystalTree", "ShadowOakLarge"],
         9, ["CrystalCluster", "CrystalClusterPink", "NightBlooms", "GlowMoss", "ShadowFern", "CrystalShards"]),
    ]
    heart = (fx0 + length - 55, 0.0, fz0)
    placed, forest = [], []
    seg = length / len(zones)
    path_z = lambda x: fz0 + 8 * math.sin(x / 30)
    for zi, (zone, trees, gap, tlist, plants, plist) in enumerate(zones):
        x0 = fx0 + zi * seg
        for per, g, names, is_tree in ((trees, gap, tlist, True), (plants, 3.0, plist, False)):
            count = round(seg * depth / 1000 * per)
            made = tries = 0
            while made < count and tries < count * 30:
                tries += 1
                x, z = rng.uniform(x0, x0 + seg), rng.uniform(fz0 - depth / 2, fz0 + depth / 2)
                if math.dist((x, z), (heart[0], heart[2])) < (26 if is_tree else 12):
                    continue
                if abs(z - path_z(x)) < (8 if is_tree else 5):
                    continue
                if any(math.dist((x, z), q) < min(g, qg) for q, qg in placed):
                    continue
                forest.append((by[rng.choice(names)], (x, 0.0, z), rng.uniform(0, 360),
                               rng.uniform(0.85, 1.2) if is_tree else rng.uniform(0.85, 1.15)))
                placed.append(((x, z), g))
                made += 1
    forest += [(by["MoonwoodTree"], add(heart, (6, 0, -10)), 30.0, 1.0),
               (by["RuneCircle"], add(heart, (-8, 0, 8)), 0.0, 1.0),
               (by["CrystalLarge"], add(heart, (-20, 0, -6)), 40.0, 1.0),
               (by["MoonShaft"], add(heart, (-16, 0, -14)), 0.0, 1.0),
               (by["RootArch"], (fx0 + 40, 0.0, path_z(fx0 + 40)), 90.0 - math.degrees(math.atan(8 / 30 * math.cos((fx0 + 40) / 30))), 1.0),
               (by["WispLantern"], (fx0 + 120, 0.0, path_z(fx0 + 120) - 6), 0.0, 1.0),
               (by["WispLantern"], (fx0 + 190, 0.0, path_z(fx0 + 190) + 6), 180.0, 1.0),
               (by["SteppingStones"], (heart[0] - 38, 0.0, path_z(heart[0] - 38)), 90.0, 1.0)]
    for i in range(3):
        x = fx0 + 70 + i * 60
        forest.append((by["FogPatch"], (x, 0.0, path_z(x) + rng.uniform(-10, 10)), rng.uniform(0, 90), 1.0))
    for i in range(80):
        x = fx0 + i * length / 80
        parts.append(block("Path", (length / 80 + 1.2, 0.1, 7), (x, 0.05, path_z(x)), "#4a3a5e"))
    parts[-1]["sh"] = False

    parts += viewer_parts(assets, catalog) + viewer_parts(assets, forest)
    env = {
        "sky": [[0, "#0d0b2a"], [0.5, "#2b2160"], [0.85, "#5a3f86"], [1, "#7a5a9a"]], "fog": ["#2a2352", 120, 420],
        "sun": {"color": "#c9d4ff", "dir": [0.35, 1.0, 0.55], "intensity": 2.1}, "hemi": ["#b7c0ff", "#2a3a3a", 1.6],
        "bloom": [0.8, 0.55, 0.72],
    }
    mw = spots["MoonwoodTree"]
    shots = {
        "catalog": {"camera": {"pos": [0, 95, 250], "target": [0, 4, 70], "fov": 52},
                    "shadow": {"center": [0, 0, 70], "radius": 190}, "env": {"fog": ["#2a2352", 300, 700]}},
        "trees": {"camera": {"pos": [0, 24, 68], "target": [0, 12, 0], "fov": 64},
                  "shadow": {"center": [0, 0, 0], "radius": 170}, "env": {"fog": ["#2a2352", 200, 500]}},
        "small": {"camera": {"pos": [0, 28, 185], "target": [0, 2, 105], "fov": 58},
                  "shadow": {"center": [0, 0, 110], "radius": 120}, "env": {"fog": ["#2a2352", 200, 500]}},
        "forest": {"camera": {"pos": [fx0 - 30, 46, fz0 + 100], "target": [fx0 + 110, 4, fz0], "fov": 55},
                   "shadow": {"center": [0, 0, fz0], "radius": 200}},
        "deep": {"camera": {"pos": [fx0 + 95, 8, path_z(fx0 + 95)], "target": [fx0 + 180, 7, path_z(fx0 + 180)],
                            "fov": 66}, "shadow": {"center": [fx0 + 150, 0, fz0], "radius": 100}},
        "heart": {"camera": {"pos": [heart[0] - 26, 9, heart[2] + 24], "target": [heart[0] + 6, 14, heart[2] - 10],
                             "fov": 60}, "shadow": {"center": list(heart), "radius": 80}},
        "moonwood": {"camera": {"pos": [mw[0] - 28, 22, mw[2] + 52], "target": [mw[0], 15, mw[2]], "fov": 58},
                     "shadow": {"center": [mw[0], 0, mw[2]], "radius": 60}},
    }
    return {"env": env, "parts": parts, "models": [], "texts": [], "sprites": [], "shots": shots}


def main():
    assets = make_kit()
    names = [a.name for a in assets]
    assert len(names) == len(set(names)), "duplicate asset names"
    spots = layout(assets)
    scatter = (HERE / "DarkWoodsScatter.lua").read_text()
    tree = build_instances(assets, spots, scatter, kit_name="DarkWoodsKit", scatter_name="DarkWoodsScatter",
                           categories=CATEGORIES, model_props=model_props)
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "kit.json").write_text(json.dumps(tree))
    (out / "world.json").write_text(json.dumps(preview_world(assets, spots)))
    total = 0
    for a in assets:
        total += len(a.parts)
        lights = sum(1 for p in a.parts for e in p["effects"] if e["class"] == "PointLight")
        print(f"{a.category:8} {a.name:20} {a.zone:6} {len(a.parts):4} parts  {height_of(a):5} studs"
              f"{'  light' if lights else ''}")
    print(f"{len(assets)} assets, {total} parts")

    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        cmd = ["cargo", "run", "--quiet", "--release", "--manifest-path",
               str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "kit.json"), target]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
