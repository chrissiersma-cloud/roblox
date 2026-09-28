"""The Fox: low-poly, with classic Roblox studs painted in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_fox.py [out_dir]           (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import X, Y, Z, Animal, Part, build, eyes, leg, loft, ring, sides, slab, square, unit

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"orange": "#d9772e", "white": "#f6f0e4", "dark": "#34261f", "nose": "#1a1716", "eye": "#161211",
           "glint": "#ffffff"}
GOLDEN = {"orange": "#e6ac2e", "white": "#fff3c4", "dark": "#9a6412", "nose": "#6a4410", "eye": "#161211",
          "glint": "#ffffff"}

FRONT_Y, HIND_Y = -0.8, 0.85          # where the legs stand
LEG_X = 0.27                           # how far the legs stand from the middle
LEG_TOP = 1.3                          # height of the leg joints (origin of the leg objects)
SOCKS = 0.6                            # the legs are dark below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(1.55, 0.00, 0.42, 0.46, 0.10),
             (1.05, 0.00, 0.44, 0.48, 0.11),       # upper leg, just below the chest
             (0.62, -0.02, 0.38, 0.42, 0.09),
             (0.45, -0.02, 0.40, 0.44, 0.09),      # wrist
             (0.20, -0.04, 0.38, 0.46, 0.09),
             (0.00, -0.07, 0.42, 0.54, 0.09)]      # paw
HIND_LEG = [(1.60, -0.02, 0.46, 0.58, 0.12),
            (1.25, 0.02, 0.54, 0.70, 0.14),        # thigh, bulging out of the body a little
            (0.85, 0.12, 0.42, 0.48, 0.10),
            (0.55, 0.18, 0.38, 0.42, 0.09),        # hock, bent back
            (0.20, 0.02, 0.38, 0.44, 0.09),
            (0.00, -0.04, 0.42, 0.54, 0.09)]       # paw


def body_paint(c, n):
    if n[2] < -0.45:
        return "white"                                  # belly
    if n[1] < -0.35 and c[2] < 1.75:
        return "white"                                  # chest
    return "orange"


def neck_paint(c, n):
    return "white" if n[1] < -0.3 else "orange"        # throat


def head_paint(c, n):
    if n[2] < -0.3 or (c[2] < 2.32 and n[2] < 0.5):
        return "white"                                  # cheeks, jaw and the sides of the muzzle
    return "orange"


def ear_paint(c, n):
    return "white" if n[1] < -0.6 else "dark"          # white inside, black on the back


def tail_paint(c, n):
    return "white" if c[1] > 2.35 else "orange"        # white tail tip


def leg_paint(c, n):
    return "dark" if c[2] < SOCKS else "orange"        # black socks


def build_body():
    body = Part("Body")
    # Body: rings standing across the fox, from the rump (back, +y) to the chest (front, -y).
    # (y, center height, width, height, top corner, bottom corner)
    rings = [(1.20, 1.55, 0.62, 0.52, 0.18, 0.16),
             (1.08, 1.52, 0.96, 0.82, 0.28, 0.26),
             (0.80, 1.50, 1.06, 0.86, 0.30, 0.28),      # hips
             (0.15, 1.50, 0.98, 0.80, 0.28, 0.28),      # waist
             (-0.45, 1.56, 1.06, 0.98, 0.30, 0.30),     # chest
             (-0.92, 1.66, 0.96, 0.96, 0.28, 0.26),     # shoulders
             (-1.20, 1.74, 0.72, 0.76, 0.22, 0.20)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    # Neck: level rings going up and forward, from inside the chest to inside the head.
    rings = [(1.70, -0.95, 0.80, 0.78, 0.22),
             (2.05, -1.18, 0.76, 0.72, 0.21),
             (2.35, -1.36, 0.66, 0.64, 0.18)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], neck_paint)

    # Head: wide cheeks and a thin, pointed muzzle.
    rings = [(-1.26, 2.40, 0.74, 0.64, 0.20, 0.18),
             (-1.44, 2.44, 0.90, 0.72, 0.24, 0.22),     # widest: cheeks
             (-1.72, 2.42, 0.80, 0.64, 0.22, 0.20),     # eyes
             (-1.92, 2.30, 0.46, 0.40, 0.12, 0.10),     # muzzle
             (-2.28, 2.22, 0.34, 0.30, 0.09, 0.08)]
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)
    eyes(body, head[1], head[2], -1.58, 2.42, w=0.18, h=0.2)
    slab(body, (0, rings[-1][0], rings[-1][1] + 0.05), -Y, 0.16, 0.10, 0.04, "nose")

    # Ears: big pointed triangles, white inside (facing forward) and black on the back.
    out = unit(np.array([0.35, 0.1, 1.0]))
    flat = unit(-Y - np.dot(-Y, out) * out)            # the thin direction of the ear
    across = unit(np.cross(out, flat))
    base = np.array([0.24, -1.36, 2.72])
    ear = [square(base, across, flat, 0.36, 0.12), square(base + out * 0.18, across, flat, 0.32, 0.10)]
    for pts, tip in sides(ear, base + out * 0.5):
        loft(body, pts, ear_paint, caps=(True, False), tip=tip)

    # Tail: big and bushy, held out behind, with a white tip.
    rings = [(1.10, 1.70, 0.30, 0.30, 0.09),
             (1.45, 1.55, 0.50, 0.50, 0.14),
             (1.85, 1.35, 0.62, 0.60, 0.17),
             (2.25, 1.20, 0.56, 0.54, 0.15),
             (2.55, 1.16, 0.40, 0.38, 0.11),
             (2.72, 1.18, 0.20, 0.18, 0.05)]
    loft(body, [ring((0, y, z), X, Z, w, h, c) for y, z, w, h, c in rings], tail_paint)
    return body


def parts():
    """Body and the four legs. The fox's left side is +x (it faces -y)."""
    return [build_body(),
            leg("LegFL", LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
            leg("LegFR", -LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
            leg("LegBL", LEG_X + 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
            leg("LegBR", -LEG_X - 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint)]


FOX = Animal("Fox", "Common", PALETTE, GOLDEN, parts, close=((0.2, -1.5, 2.2), 3.6))

if __name__ == "__main__":
    build(FOX)
