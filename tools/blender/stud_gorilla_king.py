"""The Gorilla King (Secret): a dripped-out silverback gorilla with a golden crown, a heavy gold chain and gold
grills, low-poly with Roblox studs (see stud_animal.py).

Run: python3 tools/blender/stud_gorilla_king.py [out_dir]  (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.

The gorilla walks on its knuckles: LegFL and LegFR are its long arms, LegBL and LegBR its short legs. Extra parts:
Crown (glows: Neon in Roblox), Chains (the heavy gold chain and medallion on its chest), Grills (gold teeth with
two diamonds) and the gold bracelets BraceletL and BraceletR (they are attached to the arms and move with them).
The gold parts are shiny in Roblox.
"""

import numpy as np

from stud_animal import (X, Y, Z, Animal, Part, build, centered, diamond, effect, eyes, leg, loft, ring,
                         scaled, slab, square, unit)

CROWN = "#ffd23a"

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"fur": "#2a2730", "silver": "#9a98a4", "skin": "#4f4854", "gold": "#f2c037", "ruby": "#e0183a",
           "diamond": "#dff6ff", "mouth": "#140d12", "nose": "#141116", "eye": "#ffb020", "glint": "#ffffff",
           "crown": CROWN}
GOLDEN = {**PALETTE, "fur": "#e6ac2e", "silver": "#fff0a0", "skin": "#c98a1a"}
NO_STUDS = ("gold", "ruby", "diamond", "mouth", "nose", "eye", "glint", "crown")

SIZE = 1.35                            # the whole gorilla is this many times bigger than the numbers in this file
ARM_X, ARM_Y, SHOULDER = 0.95, -0.62, 2.70      # where the arms hang and the shoulder joints
LEG_X, LEG_Y, HIP = 0.50, 0.72, 1.50            # where the legs stand and the hip joints

# Arms and legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
ARM = [(2.95, 0.00, 0.80, 0.80, 0.22),
       (2.30, 0.00, 0.86, 0.86, 0.24),             # upper arm
       (1.55, -0.04, 0.70, 0.72, 0.20),            # elbow
       (0.85, -0.08, 0.78, 0.80, 0.21),            # big forearm
       (0.40, -0.10, 0.66, 0.68, 0.18),            # wrist
       (0.32, -0.12, 0.80, 0.84, 0.20),            # fist, walking on the knuckles
       (0.00, -0.14, 0.82, 0.86, 0.20)]
LEG = [(1.90, 0.00, 0.66, 0.80, 0.20),
       (1.35, 0.02, 0.80, 0.92, 0.24),             # thigh
       (0.80, 0.06, 0.62, 0.70, 0.17),             # knee
       (0.34, 0.02, 0.58, 0.62, 0.16),
       (0.26, -0.10, 0.72, 0.98, 0.18),            # foot
       (0.00, -0.12, 0.74, 1.02, 0.18)]


def body_paint(c, n):
    if n[2] > 0.4 and c[1] > -0.6:
        return "silver"                                 # the silver back
    if n[1] < -0.4 and c[2] < 3.0 or n[2] < -0.45:
        return "skin"                                   # chest and belly
    return "fur"


def head_paint(c, n):
    return "skin" if c[1] < -1.38 and n[2] < 0.6 else "fur"      # the bare face


def limb_paint(c, n):
    return "skin" if c[2] < 0.34 else "fur"            # knuckles and soles


def link(part, a, b, flip, paint="gold", width=0.17, thick=0.07, facing=-Y):
    """One chain link from a to b: a flat bar, turned a quarter turn from the link before (flip)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = unit(b - a)
    side = unit(np.cross(facing, d))
    front = np.cross(d, side)
    u, v = (front, side) if flip else (side, front)
    extra = d * np.linalg.norm(b - a) * 0.08          # a little longer, so the links touch
    loft(part, [square(a - extra, u, v, width, thick), square(b + extra, u, v, width, thick)], paint)


def chain(part, points, **kw):
    for i, (a, b) in enumerate(zip(points, points[1:])):
        link(part, a, b, i % 2, **kw)


def build_body():
    body = Part("Body")
    # A huge chest and shoulders, sloping down to small hips. (y, center height, width, height, top/bottom corner)
    rings = [(1.05, 1.72, 1.10, 1.00, 0.32, 0.30),
             (0.88, 1.76, 1.56, 1.36, 0.44, 0.42),      # hips
             (0.30, 1.98, 1.78, 1.66, 0.50, 0.48),
             (-0.35, 2.36, 2.16, 2.00, 0.60, 0.56),     # huge shoulders
             (-0.82, 2.50, 1.96, 1.80, 0.54, 0.50),
             (-1.08, 2.46, 1.40, 1.30, 0.40, 0.36)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    # Head: low between the shoulders, a heavy brow, a bare face and a wide muzzle.
    rings = [(-0.92, 2.92, 1.00, 0.96, 0.30, 0.28),
             (-1.18, 2.98, 1.12, 1.04, 0.34, 0.30),
             (-1.44, 2.94, 1.10, 0.98, 0.32, 0.30),     # face
             (-1.62, 2.70, 0.86, 0.66, 0.24, 0.22),     # muzzle
             (-1.76, 2.64, 0.70, 0.52, 0.18, 0.16)]
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)
    loft(body, [square((x, -1.56, 3.12), Y, Z, 0.18, 0.16) for x in (-0.46, 0.46)], "fur")   # the brow
    eyes(body, head[2], head[3], -1.52, 2.90, w=0.14, h=0.16)
    slab(body, (0, -1.76, 2.72), -Y, 0.34, 0.12, 0.03, "nose")
    slab(body, (0, -1.76, 2.50), -Y, 0.50, 0.18, 0.02, "mouth")        # a wide grin, full of gold (see Grills)

    diamond(body, (0, -1.40, 3.52), 0.14, 0.2, "ruby")                  # ruby on the front of the crown
    diamond(body, (0, -1.25, 1.86), 0.18, 0.26, "ruby")                 # ruby in the medallion
    return body


def build_crown():
    part = Part("Crown")
    center = np.array([0, -1.10, 3.42])
    loft(part, [ring(center, X, Y, 0.64, 0.56, 0.16), ring(center + Z * 0.20, X, Y, 0.64, 0.56, 0.16)], "crown")
    for x, y, height in ((0, -1.36, 0.36), (0.26, -1.22, 0.28), (-0.26, -1.22, 0.28), (0.26, -0.98, 0.24),
                         (-0.26, -0.98, 0.24), (0, -0.84, 0.24)):
        base = np.array([x, y, 3.58])
        loft(part, [square(base, X, Y, 0.13, 0.13)], "crown", caps=(True, False), tip=base + Z * height)
    return centered(part)


def build_chains():
    part = Part("Chains")
    # A heavy chain hanging across the chest, with a round medallion at the bottom.
    pts = []
    for x in np.linspace(-0.78, 0.78, 12):
        y = -1.14 + max(abs(x) - 0.45, 0) * 0.9
        pts.append((x, y, 2.10 + 0.8 * (x / 0.78) ** 2))
    chain(part, pts)
    slab(part, (0, -1.17, 1.86), -Y, 0.46, 0.46, 0.06, "gold", corner=0.13)
    return centered(part)


def build_grills():
    """Gold teeth on the grin, two of them diamonds."""
    part = Part("Grills")
    for i, x in enumerate(np.linspace(-0.18, 0.18, 5)):
        slab(part, (x, -1.78, 2.53), -Y, 0.075, 0.1, 0.03, "diamond" if i in (1, 3) else "gold")
    slab(part, (0, -1.78, 2.46), -Y, 0.42, 0.05, 0.025, "gold")        # the bottom row
    return centered(part)


def build_bracelet(name, arm, sign):
    """A chunky gold bracelet around the wrist, with a ring of gold links on it."""
    part = Part(name, parent=arm)
    x, y = ARM_X * sign, ARM_Y - 0.10
    loft(part, [ring((x, y, z), X, Y, 0.80, 0.82, 0.22) for z in (0.42, 0.62)], "gold")
    around = [(x + 0.44 * np.cos(t), y + 0.45 * np.sin(t), 0.52) for t in np.linspace(0, 2 * np.pi, 13)]
    chain(part, around, facing=Z, width=0.12, thick=0.05)
    return centered(part)


def parts():
    """Body, arms, legs, crown, chains and cuffs, SIZE times as big. The gorilla faces -y; its left is +x."""
    return scaled([build_body(),
                   leg("LegFL", ARM_X, ARM_Y, SHOULDER, ARM, limb_paint),
                   leg("LegFR", -ARM_X, ARM_Y, SHOULDER, ARM, limb_paint),
                   leg("LegBL", LEG_X, LEG_Y, HIP, LEG, limb_paint),
                   leg("LegBR", -LEG_X, LEG_Y, HIP, LEG, limb_paint),
                   build_crown(), build_chains(), build_grills(),
                   build_bracelet("BraceletL", "LegFL", 1), build_bracelet("BraceletR", "LegFR", -1)], SIZE)


GORILLA_KING = Animal(
    "GorillaKing", "Secret", PALETTE, GOLDEN, parts, close=((0.55, -1.9, 4.0), 6.5), no_studs=NO_STUDS,
    display="Gorilla King",
    glow={"Crown": CROWN}, shine={"Chains": 0.35, "Grills": 0.4, "BraceletL": 0.35, "BraceletR": 0.35},
    effects=[effect("CrownSparkles", "Crown", "Sparkles", CROWN, "#ffffff", rate=5, size=(0.4, 0), speed=(0.3, 0.8)),
             effect("GoldSparkles", "Chains", "Sparkles", CROWN, rate=4, size=(0.3, 0), speed=(0.2, 0.5)),
             effect("GrillShine", "Grills", "Sparkles", "#ffffff", "#bfefff", rate=2, size=(0.25, 0),
                    lifetime=(0.3, 0.6), speed=(0.1, 0.3))],
    light=("Crown", CROWN, 1.2, 12))

if __name__ == "__main__":
    build(GORILLA_KING)
