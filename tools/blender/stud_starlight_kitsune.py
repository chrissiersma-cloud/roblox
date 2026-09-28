"""Starlight Kitsune (Secret): a white fox with nine rainbow tails and a golden crown, low-poly with Roblox studs
(see stud_animal.py).

Run: python3 tools/blender/stud_starlight_kitsune.py [out_dir]   (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.

Parts: Body (with the nine tails), the four legs, and Crown: the golden crown and two gems floating next to the
kitsune. The crown glows: the setup script makes it Neon in Roblox.
"""

import numpy as np

from stud_animal import (X, Y, Z, Animal, Part, build, centered, diamond, effect, eyes, leg, loft, newell, ring,
                         scaled, sides, slab, square, turn, unit)

GOLD = "#ffe066"
RAINBOW = ["#ff6b9d", "#ff9b5e", "#ffd84d", "#8ef56b", "#5ef0d0", "#5cc8ff", "#7f8cff", "#b57bff", "#f27bff"]

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"white": "#f8f4ff", "lilac": "#dccdff", "violet": "#a77bff",
           **{f"tail{i + 1}": color for i, color in enumerate(RAINBOW)},
           "star": "#ff7be5", "nose": "#3a2350", "eye": "#6a3fd6", "glint": "#ffffff", "gold": GOLD}
GOLDEN = {**PALETTE, "white": "#ffe9a8", "lilac": "#fff3c4", "violet": "#e6ac2e",
          **{f"tail{i + 1}": "#f2c037" for i in range(9)}}
NO_STUDS = ("star", "nose", "eye", "glint", "gold")

SIZE = 1.3                             # the whole kitsune is this many times bigger than the numbers in this file
FRONT_Y, HIND_Y = -0.8, 0.85          # where the legs stand
LEG_X = 0.27                           # how far the legs stand from the middle
LEG_TOP = 1.3                          # height of the leg joints (origin of the leg objects)
PAWS = 0.24                            # the violet paws are below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(1.55, 0.00, 0.42, 0.46, 0.10),
             (1.05, 0.00, 0.44, 0.48, 0.11),
             (0.62, -0.02, 0.38, 0.42, 0.09),
             (0.45, -0.02, 0.40, 0.44, 0.09),      # wrist
             (0.20, -0.04, 0.38, 0.46, 0.09),
             (0.00, -0.07, 0.42, 0.54, 0.09)]      # paw
HIND_LEG = [(1.60, -0.02, 0.46, 0.58, 0.12),
            (1.25, 0.02, 0.54, 0.70, 0.14),        # thigh
            (0.85, 0.12, 0.42, 0.48, 0.10),
            (0.55, 0.18, 0.38, 0.42, 0.09),        # hock
            (0.20, 0.02, 0.38, 0.44, 0.09),
            (0.00, -0.04, 0.42, 0.54, 0.09)]       # paw
# One tail, level rings from inside the rump up to the tip: (height, forward/back, width, depth, corner).
# Nine copies fan out behind, each turned a bit further to the side.
TAIL = [(1.62, 1.05, 0.26, 0.30, 0.08),
        (1.92, 1.40, 0.38, 0.42, 0.11),
        (2.30, 1.64, 0.42, 0.46, 0.12),
        (2.68, 1.76, 0.34, 0.38, 0.10),
        (2.92, 1.78, 0.18, 0.20, 0.05)]
TAIL_ROOT = (0, 1.05, 1.62)
TAIL_ANGLES = range(-64, 65, 16)


def body_paint(c, n):
    return "lilac" if n[2] < -0.45 or (n[1] < -0.35 and c[2] < 1.75) else "white"


def head_paint(c, n):
    return "lilac" if n[2] < -0.3 or (c[2] < 2.32 and n[2] < 0.5) else "white"


def ear_paint(c, n):
    if c[2] > 2.9:
        return "violet"                                 # violet ear tips
    return "lilac" if n[1] < -0.6 else "white"


def leg_paint(c, n):
    return "violet" if c[2] < PAWS else "white"


def head_rings():
    rings = [(-1.26, 2.40, 0.74, 0.64, 0.20, 0.18),
             (-1.44, 2.44, 0.90, 0.72, 0.24, 0.22),     # cheeks
             (-1.72, 2.42, 0.80, 0.64, 0.22, 0.20),     # eyes
             (-1.92, 2.30, 0.46, 0.40, 0.12, 0.10),     # muzzle
             (-2.28, 2.22, 0.34, 0.30, 0.09, 0.08)]
    return [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]


def build_body():
    body = Part("Body")
    rings = [(1.20, 1.55, 0.62, 0.52, 0.18, 0.16),
             (1.08, 1.52, 0.96, 0.82, 0.28, 0.26),
             (0.80, 1.50, 1.06, 0.86, 0.30, 0.28),      # hips
             (0.15, 1.50, 0.98, 0.80, 0.28, 0.28),      # waist
             (-0.45, 1.56, 1.06, 0.98, 0.30, 0.30),     # chest
             (-0.92, 1.66, 0.96, 0.96, 0.28, 0.26),     # shoulders
             (-1.20, 1.74, 0.72, 0.76, 0.22, 0.20)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    rings = [(1.70, -0.95, 0.80, 0.78, 0.22), (2.05, -1.18, 0.76, 0.72, 0.21), (2.35, -1.36, 0.66, 0.64, 0.18)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings],
         lambda c, n: "lilac" if n[1] < -0.3 else "white")

    head = head_rings()
    loft(body, head, head_paint)
    eyes(body, head[1], head[2], -1.58, 2.42, w=0.18, h=0.2)
    slab(body, (0, -2.28, 2.27), -Y, 0.16, 0.10, 0.04, "nose")
    # A pink star mark on the forehead, on the face between the eyes and the muzzle.
    top = [head[2][2], head[2][3], head[3][3], head[3][2]]
    n = unit(newell(top))
    slab(body, np.mean(top, 0), n if n[2] > 0 else -n, 0.14, 0.16, 0.02, "star", corner=0.06)

    out = unit(np.array([0.35, 0.1, 1.0]))
    flat = unit(-Y - np.dot(-Y, out) * out)
    across = unit(np.cross(out, flat))
    base = np.array([0.24, -1.36, 2.72])
    ear = [square(base, across, flat, 0.36, 0.12), square(base + out * 0.18, across, flat, 0.32, 0.10)]
    for pts, tip in sides(ear, base + out * 0.5):
        loft(body, pts, ear_paint, caps=(True, False), tip=tip)

    # Nine tails: white, each with a tip in its own rainbow color.
    rings = [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in TAIL]
    for i, angle in enumerate(TAIL_ANGLES):
        tip_color = f"tail{i + 1}"
        loft(body, turn(rings, TAIL_ROOT, Y, angle),
             lambda c, n, tip_color=tip_color: tip_color if np.linalg.norm(c - TAIL_ROOT) > 0.95 else "white")
    return body


def build_crown():
    part = Part("Crown")
    # A golden crown between the ears: a band with three points.
    band = [ring((0, -1.40, 2.78), X, Y, 0.40, 0.34, 0.10), ring((0, -1.40, 2.92), X, Y, 0.40, 0.34, 0.10)]
    loft(part, band, "gold")
    for x, height in ((0, 0.34), (0.13, 0.24), (-0.13, 0.24)):
        loft(part, [square((x, -1.40, 2.90), X, Y, 0.12, 0.12)], "gold", caps=(True, False),
             tip=(x * 1.3, -1.40, 2.90 + height))
    for x in (0.9, -0.9):
        diamond(part, (x, -0.25, 2.45), 0.2, 0.3, "gold")            # gems floating next to the kitsune
    return centered(part)


def parts():
    """Body, legs and the crown, SIZE times as big. The kitsune faces -y; its left is +x."""
    return scaled([build_body(),
                   leg("LegFL", LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
                   leg("LegFR", -LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
                   leg("LegBL", LEG_X + 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
                   leg("LegBR", -LEG_X - 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
                   build_crown()], SIZE)


KITSUNE = Animal(
    "StarlightKitsune", "Secret", PALETTE, GOLDEN, parts, close=((0.3, -1.6, 3.0), 5.2), no_studs=NO_STUDS,
    display="Starlight Kitsune",
    glow={"Crown": GOLD},
    effects=[effect("Starfall", "Body", "Sparkles", "#ff9cf2", "#7fe8ff", rate=8, size=(0.5, 0), speed=(0.4, 1.2)),
             effect("CrownSparkles", "Crown", "Sparkles", GOLD, "#ffffff", rate=4, size=(0.4, 0),
                    speed=(0.3, 0.8))],
    light=("Body", "#d9b8ff", 1.4, 16))

if __name__ == "__main__":
    build(KITSUNE)
