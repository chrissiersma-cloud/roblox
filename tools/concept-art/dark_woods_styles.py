#!/usr/bin/env python3
"""Style ideas for the trees and decorations of the Dark Woods (concept art, not the final models).

Each style is a small forest clearing at night, built from prototype trees and decorations in that style, with a
few of the real Dark Woods animals and a player for scale.

    python3 tools/concept-art/dark_woods_styles.py  -> tools/concept-art/build/dark_woods_styles.json

Render: copy that file and tools/animal-models/build/dark_woods.json to tools/viewer/ and run
    node sceneshot.js dark_woods_styles.json <shot> out.png      (shots: purple, shrooms, willow, crystal)
"""

import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS / "animal-models"))
sys.path.insert(0, str(TOOLS / "forest-kit"))

from lib import add, angles, apply, matmul  # noqa: E402
from build_kit import Asset, crown, roots, viewer_parts  # noqa: E402
from scenes import C, L, Scene, player  # noqa: E402

GLOW = dict(material="Neon", collide=False, shadow=False)


def light(color, brightness=1.2, range_=12):
    return {"class": "PointLight", "name": "Glow",
            "props": {"Color": list(C(color)), "Brightness": brightness, "Range": range_, "Shadows": False}}


def bent_trunk(a, pts, widths, color):
    """Crooked trunk through a list of points, with a joint block at every bend."""
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        a.rod("Trunk", p, q, widths[i], color)
        if i:
            a.octo("TrunkJoint", (widths[i - 1] * 0.98, widths[i - 1] * 0.98, widths[i - 1] * 0.98), p, color)


def crystal(a, base, w, h, color, tilt=(0, 0, 0), yaw=0.0):
    """Crystal: a prism with a pointed ridge on top, and a glowing core."""
    R = matmul(angles(*tilt), angles(0, yaw, 0))
    body = h * 0.62
    a.box("Crystal", (w, body, w), add(base, apply(R, (0, body / 2, 0))), C(color), R=R, material="Glass",
          transparency=0.2, collide=False)
    tip = h - body
    for sgn in (-1, 1):
        Rt = matmul(R, angles(0, 90 + 90 * sgn, 0))
        a.wedge("CrystalTip", (w, tip, w / 2), add(base, apply(R, (0, body + tip / 2, sgn * w / 4))), C(color), R=Rt,
                material="Glass", transparency=0.2, collide=False)
    a.box("CrystalCore", (w * 0.35, body * 0.8, w * 0.35), add(base, apply(R, (0, body * 0.5, 0))), C(color), R=R,
          **GLOW)


def flat(a, name, size, pos, color, yaw, transparency=0.0, material="SmoothPlastic"):
    a.box(name, (size[0], 0.06, size[1]), (pos[0], 0.03 + pos[1], pos[2]), C(color), rot=(0, yaw, 0),
          collide=False, shadow=False, transparency=transparency, material=material)


# ------------------------------------------------ style A: Moonlit Purple --

PURPLE = [C("#2a1f4a"), C("#3b2a66"), C("#503a88"), C("#6a4fa8")]
INDIGO = [C("#1c1f4a"), C("#262d66"), C("#34408a"), C("#4656a8")]


def shadow_oak(rng, k=1.0, pal=PURPLE):
    a = Asset("ShadowOak", "Trees", "Deep", "Twisted black oak with purple leaves and glowing berries")
    bark = C("#2b2233")
    lean = rng.uniform(0, 360)
    d = apply(angles(0, lean, 0), (0, 0, -1))
    pts = [(0, 0, 0), (d[0] * 1.2 * k, 5 * k, d[2] * 1.2 * k), (-d[0] * 0.6 * k, 10 * k, -d[2] * 0.6 * k),
           (d[0] * 0.8 * k, 14 * k, d[2] * 0.8 * k)]
    bent_trunk(a, pts, [2.2 * k, 1.8 * k, 1.4 * k], bark)
    roots(a, 2.2 * k, bark, rng, n=5, length=2.6 * k, height=1.6 * k)
    top = pts[-1]
    crown(a, add(top, (0, 3 * k, 0)), (5.2 * k, 4.2 * k, 5.2 * k), pal, rng, n=11)
    for i in range(2):
        ang = math.radians(lean + 120 + i * 120)
        c = (math.cos(ang) * 4.8 * k, 12.5 * k, math.sin(ang) * 4.8 * k)
        a.rod("Branch", pts[2], c, 0.7 * k, bark)
        crown(a, c, (3.4 * k, 2.8 * k, 3.4 * k), pal, rng, n=6)
        # A vine hanging from the branch.
        a.rod("Vine", c, add(c, (0, -5.5 * k, 0)), 0.18, C("#2f5a3a"), octagon=False, collide=False)
    for _ in range(9):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(3.2, 4.6) * k
        a.box("Berry", (0.55, 0.55, 0.55), add(top, (math.cos(ang) * r, rng.uniform(1.0, 4.5) * k, math.sin(ang) * r)),
              C(rng.choice(["#c77dff", "#ff7be5"])), rot=(45, 45, 0), **GLOW)
    return a


def gnarled_tree(rng, k=1.0):
    a = Asset("GnarledTree", "Trees", "Deep", "Bare, crooked ash-grey tree")
    bark = C("#4a4a5e")
    bent_trunk(a, [(0, 0, 0), (0.8 * k, 4 * k, 0), (-0.6 * k, 8 * k, 0.4 * k), (0.3 * k, 11 * k, -0.3 * k)],
               [1.5 * k, 1.2 * k, 0.9 * k], bark)
    roots(a, 1.5 * k, bark, rng, n=4)
    for yaw, y0, out, up in ((30, 6, 3.6, 3), (150, 8, 3.2, 3.5), (260, 9.5, 2.8, 3), (340, 4.5, 3.0, 2)):
        d = apply(angles(0, yaw + rng.uniform(-15, 15), 0), (0, 0, -1))
        mid = (d[0] * out * 0.6 * k, (y0 + up * 0.8) * k, d[2] * out * 0.6 * k)
        tip = (d[0] * out * k, (y0 + up) * k, d[2] * out * k)
        a.rod("Branch", (0, y0 * k, 0), mid, 0.5 * k, bark)
        a.rod("Branch", mid, tip, 0.3 * k, bark)
        a.rod("Twig", tip, add(tip, (d[2] * 1.2, 1.1, -d[0] * 1.2)), 0.2, bark)
    return a


def thorn_bramble(rng):
    a = Asset("ThornBramble", "Plants", "Deep", "Tangle of purple thorny branches")
    for i in range(10):
        yaw, pitch = rng.uniform(0, 360), rng.uniform(15, 55)
        d = apply(matmul(angles(0, yaw, 0), angles(pitch, 0, 0)), (0, 0, -1))
        start = (rng.uniform(-0.5, 0.5), 0.2, rng.uniform(-0.5, 0.5))
        end = add(start, (d[0] * 3.2, abs(d[1]) * 3.2 + 0.6, d[2] * 3.2))
        a.rod("Thorn", start, end, 0.28, C("#3d2450"), collide=False)
        a.wedge("Spike", (0.2, 0.5, 0.3), add(end, (0, 0.2, 0)), C("#b58cff"), collide=False, shadow=False)
    return a


def wisp_lantern(rng):
    a = Asset("WispLantern", "Lights", "Deep", "Crooked post with a hanging lantern")
    wood = C("#2b2233")
    a.rod("Post", (0, 0, 0), (0.3, 7, 0), 0.6, wood)
    a.rod("Arm", (0.3, 6.6, 0), (2.2, 7.3, 0), 0.4, wood)
    a.rod("Chain", (2.1, 7.2, 0), (2.1, 6.2, 0), 0.1, C("#8d8d99"), octagon=False, collide=False)
    a.box("LanternCap", (1.2, 0.3, 1.2), (2.1, 6.1, 0), C("#1b1420"))
    a.box("Lantern", (0.9, 1.1, 0.9), (2.1, 5.4, 0), C("#c77dff"), effects=[light("#c77dff", 1.4, 14)], **GLOW)
    a.box("LanternBase", (1.1, 0.25, 1.1), (2.1, 4.75, 0), C("#1b1420"))
    return a


def purple_leaves(rng):
    a = Asset("PurpleLeaves", "Ground", "Deep", "Fallen purple and blue leaves")
    for i in range(18):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 3.4)
        s = rng.uniform(0.45, 0.8)
        flat(a, "Leaf", (s, s * 0.6), (math.cos(ang) * r, i * 0.004, math.sin(ang) * r),
             rng.choice(["#6a4fa8", "#4656a8", "#8a5cc8", "#3b2a66"]), rng.uniform(0, 180))
    return a


# -------------------------------------------------- style B: Glowshroom --

def mushroom_tree(rng, k=1.0, cap="#6b3fa0", glow="#ff7be5"):
    a = Asset("MushroomTree", "Trees", "Deep", "Giant mushroom with glowing gills")
    stem = C("#e9e1d0")
    bend = rng.uniform(-1.2, 1.2) * k
    h = 11 * k
    bent_trunk(a, [(0, 0, 0), (bend, h * 0.5, 0), (bend * 0.4, h, 0)], [2.0 * k, 1.6 * k], stem)
    a.octo("StemBase", (3.0 * k, 1.2 * k, 3.0 * k), (0, 0.6 * k, 0), stem)
    top = (bend * 0.4, h, 0)
    a.octo("Gills", (9.4 * k, 0.4 * k, 9.4 * k), add(top, (0, 0.2 * k, 0)), C(glow), material="Neon", collide=False,
           shadow=False)
    a.octo("Cap", (10 * k, 1.4 * k, 10 * k), add(top, (0, 1.0 * k, 0)), C(cap))
    a.octo("Cap", (8 * k, 1.4 * k, 8 * k), add(top, (0, 2.3 * k, 0)), C(cap), yaw=22)
    a.octo("Cap", (5 * k, 1.1 * k, 5 * k), add(top, (0, 3.4 * k, 0)), C(cap))
    for _ in range(7):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(1.0, 3.6) * k
        y = 3.05 * k if r > 2.4 * k else 4.0 * k
        a.box("Spot", (0.9 * k, 0.2, 0.9 * k), add(top, (math.cos(ang) * r, y, math.sin(ang) * r)), C(glow),
              rot=(0, rng.uniform(0, 90), 0), **GLOW)
    a.parts[-1]["effects"].append(light(glow, 1.2, 16))
    return a


def shroom_cluster(rng, colors=("#ff7be5", "#5ef0ff", "#c77dff")):
    a = Asset("GlowShrooms", "Plants", "Deep", "Little glowing mushrooms in three colors")
    for i in range(6):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 1.4)
        k = rng.uniform(0.4, 0.9)
        p = (math.cos(ang) * r, 0, math.sin(ang) * r)
        col = C(colors[i % 3])
        a.octo("Stem", (0.4 * k, 1.2 * k, 0.4 * k), add(p, (0, 0.6 * k, 0)), C("#e9e1d0"), collide=False, shadow=False)
        a.octo("Cap", (1.4 * k, 0.5 * k, 1.4 * k), add(p, (0, 1.3 * k, 0)), col, material="Neon", collide=False,
               shadow=False)
    return a


def puffballs(rng):
    a = Asset("Puffballs", "Plants", "Deep", "Round pale puffballs")
    for i in range(5):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 1.6)
        d = rng.uniform(0.7, 1.5)
        a.ball("Puff", d, (math.cos(ang) * r, d * 0.45, math.sin(ang) * r), C("#d9d2f0"), collide=False)
    return a


def glow_moss(rng, colors=("#7dffc4", "#5ef0ff")):
    a = Asset("GlowMoss", "Ground", "Deep", "Dark moss with glowing specks")
    for i in range(6):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2.2)
        s = rng.uniform(1.6, 2.8)
        flat(a, "Moss", (s, s * 0.8), (math.cos(ang) * r, i * 0.004, math.sin(ang) * r), "#244a36", rng.uniform(0, 90))
    for i in range(12):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 3.0)
        flat(a, "Speck", (0.25, 0.25), (math.cos(ang) * r, 0.03, math.sin(ang) * r), rng.choice(colors), 45,
             material="Neon")
    return a


# ----------------------------------------------- style C: Misty willows --

WILLOW = [C("#1d4a45"), C("#26605a"), C("#317a6e"), C("#3f9282")]


def willow(rng, k=1.0):
    a = Asset("WeepingWillow", "Trees", "Deep", "Weeping tree with hanging strands and glowing pods")
    bark = C("#2e2a24")
    bent_trunk(a, [(0, 0, 0), (0.6 * k, 5 * k, 0), (0, 10 * k, 0.4 * k)], [2.4 * k, 1.8 * k], bark)
    roots(a, 2.4 * k, bark, rng, n=5, length=2.4 * k, height=1.4 * k)
    top = (0, 12 * k, 0.3 * k)
    crown(a, top, (8 * k, 3.6 * k, 8 * k), WILLOW, rng, n=12)
    for i in range(22):
        ang = i * 2 * math.pi / 22 + rng.uniform(-0.1, 0.1)
        r = rng.uniform(4.2, 5.6) * k
        y0 = top[1] - rng.uniform(0.5, 1.5) * k
        length = rng.uniform(5.5, 8.5) * k
        x, z = math.cos(ang) * r, top[2] + math.sin(ang) * r
        a.box("Strand", (0.5 * k, length, 0.25 * k), (x, y0 - length / 2, z), WILLOW[2 + i % 2],
              rot=(0, -math.degrees(ang), rng.uniform(-4, 4)), collide=False, shadow=False)
        if i % 2 == 0:
            a.ball("Pod", 0.7 * k, (x, y0 - length - 0.2, z), C("#7dffc4"), **GLOW)
    a.parts[-1]["effects"].append(light("#7dffc4", 1.0, 14))
    return a


def fog_patch(rng):
    a = Asset("FogPatch", "Ground", "Deep", "Low mist lying on the ground")
    for i in range(5):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 3)
        s = rng.uniform(6, 10)
        a.box("Fog", (s, 0.8, s * 0.7), (math.cos(ang) * r, 0.5 + i * 0.25, math.sin(ang) * r), C("#c9d4ff"),
              rot=(0, rng.uniform(0, 90), 0), transparency=0.96, collide=False, shadow=False)
    return a


def dark_pool(rng):
    a = Asset("DarkPool", "Ground", "Deep", "Still black pool with glowing lily pads")
    for yaw in (0, 45):
        a.box("Water", (14, 0.2, 10), (0, 0.1, 0), C("#10202e"), rot=(0, yaw, 0), material="Glass", transparency=0.1,
              collide=False)
    for i in range(4):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(1.5, 4)
        p = (math.cos(ang) * r, 0.25, math.sin(ang) * r * 0.7)
        a.box("Pad", (1.8, 0.1, 1.8), p, C("#2f7a5a"), rot=(0, rng.uniform(0, 90), 0), collide=False, shadow=False)
        a.box("Bloom", (0.5, 0.4, 0.5), add(p, (0.3, 0.25, 0.2)), C("#7dffc4"), rot=(0, 45, 0), **GLOW)
    return a


def glow_reeds(rng):
    a = Asset("GlowReeds", "Plants", "Deep", "Reeds with glowing tips")
    for i in range(7):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 1.0)
        h = rng.uniform(3.0, 4.6)
        R = angles(rng.uniform(-8, 8), 0, rng.uniform(-8, 8))
        base = (math.cos(ang) * r, 0, math.sin(ang) * r)
        a.box("Reed", (0.16, h, 0.16), add(base, apply(R, (0, h / 2, 0))), C("#2f5a3a"), R=R, collide=False,
              shadow=False)
        a.box("Tip", (0.35, 0.7, 0.35), add(base, apply(R, (0, h, 0))), C("#7dffc4"), R=R, **GLOW)
    return a


# ------------------------------------------------ style D: Crystal grove --

def crystal_tree(rng, k=1.0, colors=("#b58cff", "#5ef0ff")):
    a = Asset("CrystalTree", "Trees", "Heart", "Dark tree with leaves of crystal")
    bark = C("#1f1a2a")
    bent_trunk(a, [(0, 0, 0), (0.5 * k, 5 * k, 0), (-0.3 * k, 10 * k, 0)], [1.8 * k, 1.4 * k], bark)
    roots(a, 1.8 * k, bark, rng, n=4)
    top = (-0.3 * k, 10 * k, 0)
    for i in range(4):
        ang = math.radians(i * 90 + 45 + rng.uniform(-15, 15))
        c = (math.cos(ang) * 3.5 * k, 12 * k, math.sin(ang) * 3.5 * k)
        a.rod("Branch", (0, 8 * k, 0), c, 0.55 * k, bark)
    for i in range(16):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 4.5) * k
        base = add(top, (math.cos(ang) * r, rng.uniform(0.5, 3.5) * k, math.sin(ang) * r))
        tilt = (math.degrees(math.sin(ang)) * r * 5 / k, 0, -math.degrees(math.cos(ang)) * r * 5 / k)
        crystal(a, base, rng.uniform(0.9, 1.5) * k, rng.uniform(2.8, 4.8) * k, colors[i % 2],
                tilt=(max(-40, min(40, tilt[0])), 0, max(-40, min(40, tilt[2]))), yaw=rng.uniform(0, 90))
    a.parts[-1]["effects"].append(light(colors[0], 1.2, 16))
    return a


def crystal_cluster(rng, colors=("#b58cff", "#5ef0ff")):
    a = Asset("CrystalCluster", "Rocks", "Heart", "Crystals growing out of a rock")
    a.box("Rock", (3.4, 1.4, 3.0), (0, 0.6, 0), C("#2e2a3a"), rot=(0, rng.uniform(0, 90), 6))
    for i in range(5):
        ang = rng.uniform(0, 2 * math.pi)
        crystal(a, (math.cos(ang) * 0.7, 0.9, math.sin(ang) * 0.7), rng.uniform(0.7, 1.2), rng.uniform(2.2, 4.2),
                colors[i % 2], tilt=(rng.uniform(-25, 25), 0, rng.uniform(-25, 25)), yaw=rng.uniform(0, 90))
    return a


def rune_stone(rng):
    a = Asset("RuneStone", "Rocks", "Heart", "Standing stone with glowing runes")
    a.box("Stone", (2.6, 7, 1.4), (0, 3.4, 0), C("#3a3848"), rot=(0, 0, rng.uniform(-4, 4)))
    a.box("StoneTop", (2.0, 1.0, 1.2), (0.1, 7.2, 0), C("#3a3848"), rot=(0, 0, 12))
    for i, (x, y, w, h) in enumerate([(0, 5.6, 0.2, 1.2), (-0.35, 5.0, 0.8, 0.2), (0.3, 4.2, 0.2, 1.0),
                                      (0, 3.3, 1.0, 0.2), (-0.3, 2.5, 0.2, 0.9), (0.2, 1.8, 0.7, 0.2)]):
        a.box("Rune", (w, h, 0.1), (x, y, -0.72), C("#5ef0ff"), **GLOW)
    a.parts[-1]["effects"].append(light("#5ef0ff", 1.0, 10))
    return a


# ------------------------------------------------------------------ scenes --

STYLES = {
    "purple": {
        "title": "IDEA 1: MOONLIT PURPLE",
        "trees": [(shadow_oak, 0.55), (shadow_oak, 0.25, dict(pal=INDIGO)), (gnarled_tree, 0.2)],
        "decor": [(thorn_bramble, 3), (purple_leaves, 3), (wisp_lantern, 0), (glow_moss, 1, dict(colors=("#c77dff", "#ff7be5")))],
        "ground": "#231d38", "path": "#4a3a5e",
        "animals": [("UmbraPanther", (-6, 0, -8), 30), ("Moonraven", (10, 0, -14), -40), ("NightHedgehog", (3, 0, 4), 200)],
        "fog": "#2a2352",
    },
    "shrooms": {
        "title": "IDEA 2: GLOWSHROOM FOREST",
        "trees": [(mushroom_tree, 0.35), (mushroom_tree, 0.3, dict(cap="#1f5a6a", glow="#5ef0ff")),
                  (mushroom_tree, 0.15, dict(cap="#8a2a5a", glow="#ffd84a")), (shadow_oak, 0.2, dict(pal=INDIGO))],
        "decor": [(shroom_cluster, 4), (puffballs, 2), (glow_moss, 3)],
        "ground": "#1d2e33", "path": "#3e4a52",
        "animals": [("ShroomSnail", (-8, 0, -6), 40), ("Glowmoth", (6, 0, -16), -30), ("Barkling", (10, 0, 2), -120)],
        "fog": "#1f2a45",
    },
    "willow": {
        "title": "IDEA 3: MISTY WILLOWS",
        "trees": [(willow, 0.7), (gnarled_tree, 0.3)],
        "decor": [(fog_patch, 3), (glow_reeds, 2), (glow_moss, 2), (dark_pool, 0)],
        "ground": "#1c2e2a", "path": "#3a4a42",
        "animals": [("WispLynx", (-6, 0, -10), 30), ("MossbackToad", (9, 0, 0), -110), ("Duskbat", (4, 0, -18), 0)],
        "fog": "#243a44",
    },
    "crystal": {
        "title": "IDEA 4: CRYSTAL GROVE",
        "trees": [(crystal_tree, 0.45), (crystal_tree, 0.2, dict(colors=("#ff7be5", "#b58cff"))),
                  (shadow_oak, 0.35, dict(pal=INDIGO))],
        "decor": [(crystal_cluster, 2), (rune_stone, 0), (glow_moss, 2, dict(colors=("#b58cff", "#5ef0ff")))],
        "ground": "#1f1c30", "path": "#3e3a52",
        "animals": [("MosskingElk", (-10, 0, -14), 40), ("HollowBadger", (8, 0, 2), -130),
                    ("NightshadeDrake", (10, 0, -22), -20)],
        "fog": "#231f45",
    },
}


def call(entry, rng):
    fn, *rest = entry
    kw = rest[1] if len(rest) > 1 else {}
    return fn(rng, **kw)


def build():
    s = Scene("styles", env={
        "sky": [[0, "#0d0b2a"], [0.5, "#2b2160"], [0.85, "#5a3f86"], [1, "#7a5a9a"]],
        "fog": ["#2a2352", 60, 190],
        "sun": {"color": "#c9d4ff", "dir": [0.35, 1.0, 0.55], "intensity": 2.1},
        "hemi": ["#b7c0ff", "#2a3a3a", 1.6],
        "bloom": [0.85, 0.55, 0.72],
    })
    placements, assets = [], []
    for si, (key, st) in enumerate(STYLES.items()):
        rng = random.Random(10 + si)
        ox = si * 400.0
        # Prototype models for this style, several variants of each tree.
        tree_variants = []
        for entry in st["trees"]:
            for _ in range(3):
                t = call(entry, rng)
                tree_variants.append((t, entry[1]))
                assets.append(t)
        decor = []
        for entry in st["decor"]:
            d = call(entry, rng)
            decor.append((d, entry[1]))
            assets.append(d)

        s.box("Ground", (300, 2, 300), (ox, -1, -40), C(st["ground"]), material="Grass")
        for i in range(24):
            z0, z1 = 40 - i * 6, 40 - (i + 1) * 6
            x0, x1 = ox + 3 * math.sin(z0 / 14), ox + 3 * math.sin(z1 / 14)
            s.box("Path", (7.5, 0.12, 6.6), ((x0 + x1) / 2, 0.06, (z0 + z1) / 2), C(st["path"]),
                  rot=(0, math.degrees(math.atan2(x1 - x0, 6)), 0), material="SmoothPlastic", shadow=False)
        placed = []

        def free(x, z, gap):
            return all(math.dist((x, z), q) >= max(gap, g) for q, g in placed)

        weights = [w / 3 for _, w in tree_variants]
        for _ in range(3000):
            x, z = rng.uniform(-110, 110), rng.uniform(-150, 50)
            if abs(x - 3 * math.sin(z / 14)) < 9 + max(0, z + 30) * 0.4 and z > -110:
                continue
            if math.dist((x, z), (0, -8)) < 22 or not free(x, z, 11):
                continue
            t = rng.choices([t for t, _ in tree_variants], weights)[0]
            placements.append((t, (ox + x, 0.0, z), rng.uniform(0, 360), rng.uniform(0.85, 1.2)))
            placed.append(((x, z), 11))
        for d, n in decor:
            if n == 0:
                continue
            for _ in range(n * 14):
                x, z = rng.uniform(-40, 40), rng.uniform(-70, 40)
                if abs(x - 3 * math.sin(z / 14)) < 4.5 or not free(x, z, 3):
                    continue
                placements.append((d, (ox + x, 0.0, z), rng.uniform(0, 360), rng.uniform(0.9, 1.2)))
                placed.append(((x, z), 3))
        # Special single pieces near the clearing.
        for d, n in decor:
            if n == 0:
                spot = (ox - 14, 0.0, -2) if d.name != "DarkPool" else (ox + 14, 0.0, -12)
                placements.append((d, spot, 20.0, 1.0))
        for aid, pos, yaw in st["animals"]:
            s.animal(aid, add(pos, (ox, 0, 0)), yaw=yaw)
        player(s, (ox - 2, 0, 12), 180, "#45a6ff", "#2b3a6b", hair="#3a2412")
        s.shot(key, (ox + 6, 9, 50), (ox, 11, -14), fov=64, shadow={"center": [ox, 0, -10], "radius": 80},
               env={"fog": [st["fog"], 55, 180]},
               hud=f'<div class="game" style="position:absolute;left:32px;top:24px;font-size:44px;color:#e9dcff">'
                   f'{st["title"]}</div>')

    world = s.export()
    world["parts"] += viewer_parts(assets, placements)
    world["modelsFile"] = "dark_woods.json"
    return world


def main():
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    world = build()
    (out / "dark_woods_styles.json").write_text(json.dumps(world))
    print(f"styles: {len(world['parts'])} parts, {len(world['shots'])} shots")
    subprocess.run([sys.executable, str(TOOLS / "animal-models" / "build_dark_woods.py")], check=True,
                   cwd=TOOLS / "animal-models", stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
