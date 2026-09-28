"""The Wolf: low-poly, with classic Roblox studs painted in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_wolf.py [out_dir]          (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import X, Y, Z, Animal, Part, build, eyes, leg, loft, ring, sides, slab, square, unit

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"grey": "#84837f", "light": "#e6e2d8", "dark": "#4b4b49", "nose": "#1c1a1b", "eye": "#161211",
           "glint": "#ffffff"}
GOLDEN = {"grey": "#e6ac2e", "light": "#ffe38a", "dark": "#bb8119", "nose": "#6a4410", "eye": "#161211",
          "glint": "#ffffff"}

FRONT_Y, HIND_Y = -1.05, 1.25         # where the legs stand
LEG_X = 0.42                           # how far the legs stand from the middle
LEG_TOP = 1.75                         # height of the leg joints (origin of the leg objects)
PAW = 0.3                              # the light paws are below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(2.05, 0.00, 0.58, 0.62, 0.15),
             (1.45, 0.00, 0.58, 0.62, 0.15),       # upper leg, just below the chest
             (1.00, -0.02, 0.50, 0.54, 0.12),
             (0.72, -0.03, 0.52, 0.56, 0.12),      # wrist
             (0.36, 0.00, 0.46, 0.50, 0.10),
             (0.26, -0.05, 0.54, 0.68, 0.10),      # paw
             (0.00, -0.07, 0.56, 0.72, 0.10)]
HIND_LEG = [(2.15, -0.02, 0.62, 0.78, 0.16),
            (1.70, 0.02, 0.70, 0.90, 0.20),        # thigh, bulging out of the body a little
            (1.20, 0.14, 0.56, 0.64, 0.14),
            (0.80, 0.22, 0.50, 0.54, 0.12),        # hock, bent back
            (0.36, 0.04, 0.46, 0.50, 0.10),
            (0.26, -0.04, 0.54, 0.68, 0.10),       # paw
            (0.00, -0.06, 0.56, 0.72, 0.10)]


def body_paint(c, n):
    if n[2] < -0.45:
        return "light"                                  # belly
    if n[1] < -0.35 and c[2] < 2.5:
        return "light"                                  # chest
    if n[2] > 0.5:
        return "dark"                                   # darker saddle along the back
    return "grey"


def neck_paint(c, n):
    return "light" if n[1] < -0.3 else "grey"          # throat and the front of the ruff


def head_paint(c, n):
    if n[2] < -0.5 or (c[1] < -2.45 and n[2] < 0.5):
        return "light"                                  # jaw, and the sides of the muzzle
    return "grey"


def ear_paint(c, n):
    return "light" if n[1] < -0.6 else "dark"          # inside of the ear


def tail_paint(c, n):
    return "dark" if c[2] < 1.3 else "grey"            # dark tail tip


def leg_paint(c, n):
    return "light" if c[2] < PAW else "grey"


def build_body():
    body = Part("Body")
    # Body: rings standing across the wolf, from the rump (back, +y) to the chest (front, -y). The chest is
    # deep and the waist tucked up. (y, center height, width, height, top corner, bottom corner)
    rings = [(1.78, 2.18, 0.86, 0.72, 0.24, 0.22),
             (1.62, 2.12, 1.30, 1.10, 0.36, 0.34),
             (1.25, 2.08, 1.46, 1.16, 0.40, 0.38),      # hips
             (0.45, 2.12, 1.34, 1.04, 0.38, 0.38),      # waist
             (-0.40, 2.14, 1.50, 1.44, 0.42, 0.42),     # deep chest
             (-1.05, 2.28, 1.56, 1.56, 0.42, 0.42),     # shoulders
             (-1.50, 2.40, 1.26, 1.30, 0.36, 0.34)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    # Neck with a thick ruff: level rings going up and forward, from inside the chest to inside the head.
    rings = [(2.30, -1.20, 1.16, 1.10, 0.30),
             (2.75, -1.55, 1.14, 1.06, 0.30),
             (3.10, -1.82, 0.96, 0.92, 0.26)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], neck_paint, caps=(False, False))

    # Head: rings standing across the head, from the back of the head to the tip of the long muzzle.
    rings = [(-1.72, 3.20, 0.90, 0.80, 0.26, 0.24),
             (-1.95, 3.24, 1.08, 0.92, 0.30, 0.28),     # widest: cheeks
             (-2.30, 3.20, 0.98, 0.84, 0.28, 0.26),     # eyes
             (-2.55, 3.04, 0.62, 0.54, 0.17, 0.15),     # muzzle
             (-3.05, 2.96, 0.54, 0.46, 0.15, 0.13)]
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)
    eyes(body, head[1], head[2], -2.13, 3.24, w=0.22, h=0.24)
    slab(body, (0, rings[-1][0], rings[-1][1] + 0.1), -Y, 0.26, 0.16, 0.05, "nose")

    # Cheek fur: a tuft on each side of the head, pointing back.
    for pts, tip in sides([square((0.44, -1.96, 3.00), Y, Z, 0.34, 0.30)], np.array([0.62, -1.62, 2.94])):
        loft(body, pts, "light", caps=(True, False), tip=tip)

    # Chest fur: a light tuft hanging down in front of the chest.
    loft(body, [square((0, -1.70, 2.62), X, Y, 0.50, 0.30)], "light", caps=(True, False), tip=(0, -1.80, 2.12))

    # Ears: pointed triangles standing up, the inside facing forward.
    out = unit(np.array([0.3, 0.12, 1.0]))
    flat = unit(-Y - np.dot(-Y, out) * out)            # the thin direction of the ear
    across = unit(np.cross(out, flat))
    base = np.array([0.30, -1.86, 3.56])
    ear = [square(base, across, flat, 0.40, 0.16), square(base + out * 0.22, across, flat, 0.36, 0.13)]
    for pts, tip in sides(ear, base + out * 0.62):
        loft(body, pts, ear_paint, caps=(True, False), tip=tip)

    # Tail: bushy, hanging down behind, with a dark tip.
    rings = [(2.40, 1.70, 0.36, 0.42, 0.10),
             (2.10, 2.02, 0.46, 0.54, 0.13),
             (1.65, 2.22, 0.52, 0.60, 0.14),
             (1.20, 2.30, 0.40, 0.48, 0.11),
             (0.98, 2.30, 0.24, 0.30, 0.07)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], tail_paint)
    return body


def parts():
    """Body and the four legs. The wolf's left side is +x (it faces -y)."""
    return [build_body(),
            leg("LegFL", LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
            leg("LegFR", -LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
            leg("LegBL", LEG_X + 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
            leg("LegBR", -LEG_X - 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint)]


WOLF = Animal("Wolf", "Rare", PALETTE, GOLDEN, parts, close=((0.3, -2.0, 3.0), 4.8))

if __name__ == "__main__":
    build(WOLF)
