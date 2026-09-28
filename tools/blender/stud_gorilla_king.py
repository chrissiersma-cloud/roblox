"""The Gorilla King (Secret): a dripped-out silverback gorilla with a golden crown, a heavy gold chain and gold
grills, low-poly with Roblox studs (see stud_animal.py).

Run: python3 tools/blender/stud_gorilla_king.py [out_dir]  (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.

The gorilla walks on its knuckles: LegFL and LegFR are its long arms, LegBL and LegBR its short legs. Extra parts:
Crown (glows: Neon in Roblox), Chains (the heavy gold chain with its medallion, and a gold earring), Grills (gold
teeth with diamonds) and the gold bracelets BraceletL and BraceletR with rings on the knuckles (they are attached to
the arms and move with them). The gold parts are shiny in Roblox.

The shapes use round rings (segs=2) and the studs wrap around them (wrap=True), for a smoother, more detailed look.
"""

import math

import numpy as np

from stud_animal import (X, Y, Z, Animal, Part, build, centered, diamond, effect, hit, loft, ring, scaled,
                         slab, square, tube, unit)

CROWN = "#ffd23a"

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"fur": "#25222b", "silver": "#a3a1ad", "skin": "#4b4450", "gold": "#f2c037", "ruby": "#e0183a",
           "diamond": "#dff6ff", "black": "#120c10", "eye": "#ffb020", "glint": "#ffffff", "crown": CROWN}
GOLDEN = {**PALETTE, "fur": "#e6ac2e", "silver": "#fff0a0", "skin": "#c98a1a"}
NO_STUDS = ("gold", "ruby", "diamond", "black", "eye", "glint", "crown")

SIZE = 1.35                            # the whole gorilla is this many times bigger than the numbers in this file
ROUND = 2                              # corner pieces of the rings: round shapes
ARM_X, ARM_Y, SHOULDER = 1.00, -0.62, 2.80      # where the arms hang and the shoulder joints
LEG_X, LEG_Y, HIP = 0.55, 0.70, 1.60            # where the legs stand and the hip joints

# Arms and legs, level rings from the top (inside the body) down:
# (height, sideways shift outward, forward/back shift, width, depth, corner)
ARM = [(3.05, 0.00, 0.00, 0.90, 0.92, 0.34),
       (2.70, 0.04, 0.00, 1.00, 1.00, 0.38),       # big shoulder muscle
       (2.25, 0.04, -0.02, 0.84, 0.88, 0.32),
       (1.80, 0.02, -0.04, 0.72, 0.76, 0.28),
       (1.45, 0.02, -0.06, 0.70, 0.74, 0.26),      # elbow
       (1.05, 0.04, -0.08, 0.88, 0.88, 0.33),      # huge forearm
       (0.62, 0.04, -0.10, 0.70, 0.72, 0.26),
       (0.42, 0.04, -0.12, 0.62, 0.64, 0.22),      # wrist
       (0.34, 0.04, -0.14, 0.78, 0.80, 0.28),      # back of the hand
       (0.14, 0.04, -0.18, 0.84, 0.90, 0.30),      # fist, walking on the knuckles
       (0.00, 0.04, -0.18, 0.80, 0.86, 0.28)]
LEG = [(1.95, 0.00, 0.00, 0.80, 0.92, 0.30),
       (1.55, 0.02, 0.02, 0.92, 1.04, 0.34),       # thigh
       (1.05, 0.02, 0.06, 0.74, 0.84, 0.28),       # knee
       (0.60, 0.00, 0.04, 0.66, 0.74, 0.24),       # calf
       (0.32, 0.00, 0.00, 0.60, 0.66, 0.22),       # ankle
       (0.24, 0.00, -0.12, 0.72, 1.00, 0.24),      # foot
       (0.00, 0.00, -0.14, 0.76, 1.06, 0.24)]
KNUCKLES = (-0.27, -0.09, 0.09, 0.27)            # the four knuckles, across the fist


def body_paint(c, n):
    if n[2] > 0.35 and c[1] > -0.5:
        return "silver"                                 # the silver back
    if (n[1] < -0.35 and c[2] < 3.0) or n[2] < -0.5:
        return "skin"                                   # bare chest and belly
    return "fur"


def head_paint(c, n):
    return "skin" if c[1] < -1.36 and n[2] < 0.7 else "fur"      # the bare face


def limb_paint(c, n):
    return "skin" if c[2] < 0.2 else "fur"             # palms and soles


def limb(name, x, y, top, rings, sign):
    """An arm or leg from level round rings; its origin (the joint) is at (x, y, top)."""
    part = Part(name, origin=(x, y, top))
    loft(part, [ring((x + sign * dx, y + dy, z), X, Y, w, d, c, segs=ROUND) for z, dx, dy, w, d, c in rings],
         limb_paint)
    return part


def arm(name, sign):
    part = limb(name, sign * ARM_X, ARM_Y, SHOULDER, ARM, sign)
    front = ARM_Y - 0.18 - 0.45
    for k in KNUCKLES:                                  # knuckle bumps on the front of the fist
        x = sign * (ARM_X + 0.04) + k
        loft(part, [ring((x, y, 0.16), X, Z, 0.19, 0.2, 0.07, segs=ROUND) for y in (front + 0.08, front - 0.06)],
             "skin")
    return part


def foot(name, sign):
    part = limb(name, sign * LEG_X, LEG_Y, HIP, LEG, sign)
    front = LEG_Y - 0.14 - 0.53
    for k in (-0.22, 0.0, 0.22):                        # toes
        loft(part, [ring((sign * LEG_X + k, y, 0.1), X, Z, 0.2, 0.18, 0.07, segs=ROUND)
                    for y in (front + 0.08, front - 0.07)], "skin")
    return part


def build_body():
    body = Part("Body")
    # A huge chest and hump over the shoulders, sloping down to small hips.
    # (y, center height, width, height, top corner, bottom corner)
    rings = [(1.12, 1.78, 0.80, 0.70, 0.30, 0.28),
             (1.02, 1.76, 1.30, 1.16, 0.46, 0.42),
             (0.80, 1.78, 1.60, 1.40, 0.56, 0.50),      # hips
             (0.45, 1.86, 1.72, 1.52, 0.60, 0.54),
             (0.05, 2.02, 1.86, 1.70, 0.64, 0.58),      # belly
             (-0.30, 2.24, 2.10, 1.94, 0.72, 0.62),
             (-0.60, 2.42, 2.26, 2.06, 0.76, 0.62),     # widest: shoulders and hump
             (-0.88, 2.50, 2.14, 1.90, 0.72, 0.58),     # chest
             (-1.08, 2.46, 1.86, 1.64, 0.62, 0.52),
             (-1.20, 2.40, 1.36, 1.24, 0.46, 0.40)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb, segs=ROUND) for y, zc, w, h, c, cb in rings], body_paint)
    body.torso = range(len(body.faces))               # for putting the chain on the chest (see build_chains)

    # Head: low between the shoulders, a bare face, a wide muzzle.
    rings = [(-0.95, 2.95, 0.96, 0.92, 0.36, 0.30),
             (-1.10, 3.05, 1.08, 1.06, 0.40, 0.34),
             (-1.26, 3.08, 1.14, 1.08, 0.40, 0.36),     # widest
             (-1.42, 3.00, 1.12, 1.02, 0.36, 0.36),     # brow
             (-1.54, 2.86, 1.04, 0.92, 0.32, 0.34),     # eyes and cheeks
             (-1.66, 2.68, 0.94, 0.78, 0.28, 0.30),
             (-1.78, 2.58, 0.86, 0.66, 0.26, 0.26),     # muzzle
             (-1.86, 2.56, 0.72, 0.54, 0.22, 0.22)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb, segs=ROUND) for y, zc, w, h, c, cb in rings], head_paint)

    # A heavy brow ridge across the forehead.
    brow = [(-0.54, -1.52, 3.14, 0.18, 0.14), (-0.26, -1.60, 3.20, 0.24, 0.20), (0.0, -1.58, 3.20, 0.22, 0.18),
            (0.26, -1.60, 3.20, 0.24, 0.20), (0.54, -1.52, 3.14, 0.18, 0.14)]
    loft(body, [ring((x, y, z), Y, Z, d, h, 0.06, segs=ROUND) for x, y, z, d, h in brow], "fur")

    # Ears on the sides of the head.
    for s in (1, -1):
        loft(body, [ring((s * x, -1.18, 3.02), Y, Z, 0.28, 0.32, 0.1, segs=ROUND) for x in (0.50, 0.63)], "skin")

    # Deep-set amber eyes under the brow, with black pupils and a white glint.
    for s in (1, -1):
        p, n = hit(body, (s * 0.25, -3, 2.98), Y)
        slab(body, p, n, 0.19, 0.14, 0.02, "eye", corner=0.04)
        slab(body, p + n * 0.02, n, 0.08, 0.11, 0.015, "black", corner=0.02)
        slab(body, p + n * 0.035 + (s * 0.02, 0, 0.03), n, 0.035, 0.035, 0.01, "glint")

    # A wide flat nose with two nostrils.
    p, n = hit(body, (0, -3, 2.78), Y)
    slab(body, p, n, 0.46, 0.24, 0.05, "skin", corner=0.08, segs=ROUND)
    for s in (1, -1):
        slab(body, p + n * 0.05 + (s * 0.1, 0, -0.03), n, 0.1, 0.08, 0.01, "black", corner=0.03)

    # A wide open grin (the gold teeth are the Grills part).
    p, n = hit(body, (0, -3, 2.52), Y)
    slab(body, p, n, 0.66, 0.28, 0.02, "skin", corner=0.1, segs=ROUND)      # lips
    slab(body, p + n * 0.02, n, 0.54, 0.18, 0.01, "black", corner=0.07, segs=ROUND)

    # Rubies on the crown band and a diamond in the medallion.
    for angle in (0, 60, -60, 120, -120):
        t = math.radians(angle)
        diamond(body, (0.42 * math.sin(t), -1.24 - 0.38 * math.cos(t), 3.66), 0.1, 0.15, "ruby")
    return body


def build_crown():
    part = Part("Crown")
    # A band with a raised rim, seven points with gold balls on top.
    band = [(3.54, 0.80, 0.72), (3.58, 0.86, 0.78), (3.64, 0.86, 0.78), (3.70, 0.80, 0.72), (3.84, 0.82, 0.74)]
    loft(part, [ring((0, -1.24, z), X, Y, w, d, 0.3, segs=ROUND) for z, w, d in band], "crown")
    for angle in (0, 50, -50, 100, -100, 150, -150):
        t = math.radians(angle)
        base = np.array([0.36 * math.sin(t), -1.24 - 0.32 * math.cos(t), 3.82])
        height = 0.34 if angle == 0 else 0.26
        loft(part, [square(base, X, Y, 0.13, 0.13)], "crown", caps=(True, False), tip=base + Z * height)
        diamond(part, base + Z * (height + 0.02), 0.09, 0.12, "crown")
    return centered(part)


def link(part, a, b, flip, facing, width=0.2, thick=0.08):
    """One chain link from a to b: a rounded bar, turned a quarter turn from the link before (flip)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = unit(b - a)
    side = unit(np.cross(facing, d))
    front = np.cross(d, side)
    u, v = (front, side) if flip else (side, front)
    extra = d * np.linalg.norm(b - a) * 0.1
    loft(part, [ring(a - extra, u, v, width, thick, thick * 0.35, segs=ROUND),
                ring(b + extra, u, v, width, thick, thick * 0.35, segs=ROUND)], "gold")


def chain(part, points, facing=-Y, **kw):
    for i, (a, b) in enumerate(zip(points, points[1:])):
        link(part, a, b, i % 2, facing, **kw)


def build_chains(body):
    part = Part("Chains")
    # A heavy chain lying on the chest: every link sits on the fur, found by shooting a line at the chest.
    pts = []
    for x in np.linspace(-0.86, 0.86, 15):
        z = 2.12 + 0.9 * (x / 0.86) ** 2
        p, n = hit(body, (x, -4, z), Y, body.torso)
        pts.append(p + n * 0.06)
    chain(part, pts)
    # The medallion: a big gold disc with a rim and a diamond in the middle, hanging from the chain.
    p, n = hit(body, (0, -4, 1.86), Y, body.torso)
    center = p + n * 0.1
    slab(part, center, -Y, 0.62, 0.62, 0.05, "gold", corner=0.27, segs=3)
    slab(part, center - Y * 0.03, -Y, 0.46, 0.46, 0.05, "gold", corner=0.2, segs=3)
    diamond(part, center - Y * 0.1, 0.24, 0.3, "diamond")
    # A gold hoop in the left ear.
    ring_pts = [(0.66, -1.18 + 0.1 * math.sin(t), 2.84 + 0.1 * math.cos(t)) for t in np.linspace(0, 2 * math.pi, 9)]
    tube(part, ring_pts, [0.04] * 9, "gold")
    return centered(part)


def build_grills(body):
    """Gold teeth in the grin, top and bottom, some of them diamonds."""
    part = Part("Grills")
    p, n = hit(body, (0, -3, 2.52), Y)
    front = p + n * 0.03
    for i, x in enumerate(np.linspace(-0.21, 0.21, 6)):
        slab(part, front + (x, 0, 0.045), n, 0.068, 0.085, 0.02, "diamond" if i in (1, 4) else "gold")
        slab(part, front + (x, 0, -0.05), n, 0.068, 0.06, 0.02, "diamond" if i == 3 else "gold")
    return centered(part)


def build_bracelet(name, arm_name, sign):
    """A thick gold bracelet with diamonds, and gold rings on two knuckles."""
    part = Part(name, parent=arm_name)
    x, y = sign * (ARM_X + 0.04), ARM_Y - 0.12
    loft(part, [ring((x, y, z), X, Y, w, w + 0.02, 0.3, segs=ROUND)
                for z, w in ((0.40, 0.74), (0.44, 0.80), (0.58, 0.80), (0.62, 0.74))], "gold")
    for angle in (0, 70, -70):
        t = math.radians(angle)
        diamond(part, (x + 0.41 * math.sin(t), y - 0.42 * math.cos(t), 0.51), 0.1, 0.14, "diamond")
    front = ARM_Y - 0.18 - 0.45
    for k in (KNUCKLES[1], KNUCKLES[2]):
        loft(part, [ring((x + k, y2, 0.16), X, Z, 0.24, 0.25, 0.09, segs=ROUND)
                    for y2 in (front + 0.02, front - 0.02)], "gold")
    return centered(part)


def parts():
    """Body, arms, legs and the bling, SIZE times as big. The gorilla faces -y; its left is +x."""
    body = build_body()
    return scaled([body, arm("LegFL", 1), arm("LegFR", -1), foot("LegBL", 1), foot("LegBR", -1),
                   build_crown(), build_chains(body), build_grills(body),
                   build_bracelet("BraceletL", "LegFL", 1), build_bracelet("BraceletR", "LegFR", -1)], SIZE)


GORILLA_KING = Animal(
    "GorillaKing", "Secret", PALETTE, GOLDEN, parts, close=((0.55, -2.0, 4.1), 6.5), no_studs=NO_STUDS,
    display="Gorilla King", wrap=True,
    glow={"Crown": CROWN}, shine={"Chains": 0.35, "Grills": 0.4, "BraceletL": 0.35, "BraceletR": 0.35},
    effects=[effect("CrownSparkles", "Crown", "Sparkles", CROWN, "#ffffff", rate=5, size=(0.4, 0), speed=(0.3, 0.8)),
             effect("GoldSparkles", "Chains", "Sparkles", CROWN, rate=4, size=(0.3, 0), speed=(0.2, 0.5)),
             effect("GrillShine", "Grills", "Sparkles", "#ffffff", "#bfefff", rate=2, size=(0.25, 0),
                    lifetime=(0.3, 0.6), speed=(0.1, 0.3))],
    light=("Crown", CROWN, 1.2, 12))

if __name__ == "__main__":
    build(GORILLA_KING)
