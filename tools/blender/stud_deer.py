"""The Deer: low-poly, with classic Roblox studs painted in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_deer.py [out_dir]          (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import X, Y, Z, Animal, Part, build, eyes, leg, loft, ring, sides, slab, square, unit

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#a86a3d", "cream": "#f0dcb6", "white": "#fbf8f1", "antler": "#d9b98c",
           "hoof": "#4a2f21", "nose": "#4a2f21", "eye": "#161211", "glint": "#ffffff"}
GOLDEN = {"brown": "#e6ac2e", "cream": "#ffe38a", "white": "#fff6d2", "antler": "#fff0b8",
          "hoof": "#8a5a12", "nose": "#8a5a12", "eye": "#161211", "glint": "#ffffff"}

FRONT_Y, HIND_Y = -1.05, 1.3          # where the legs stand
LEG_X = 0.45                           # how far the legs stand from the middle
LEG_TOP = 2.3                          # height of the leg joints (origin of the leg objects)
HOOF = 0.38                            # hooves are below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(2.55, 0.00, 0.60, 0.62, 0.15),
             (1.90, 0.00, 0.62, 0.66, 0.15),       # upper leg, just below the chest
             (1.40, -0.02, 0.52, 0.56, 0.12),
             (1.08, -0.04, 0.54, 0.58, 0.12),      # knee
             (0.80, -0.02, 0.48, 0.52, 0.10),
             (0.40, 0.00, 0.50, 0.54, 0.10),       # ankle
             (0.33, 0.00, 0.56, 0.62, 0.10),       # hoof
             (0.00, -0.03, 0.58, 0.66, 0.10)]
HIND_LEG = [(2.70, -0.02, 0.62, 0.76, 0.16),
            (2.20, 0.02, 0.74, 0.92, 0.20),        # thigh, bulging out of the body a little
            (1.60, 0.10, 0.60, 0.70, 0.15),
            (1.08, 0.18, 0.52, 0.56, 0.12),        # hock, bent back
            (0.80, 0.10, 0.48, 0.52, 0.10),
            (0.40, 0.02, 0.50, 0.54, 0.10),        # ankle
            (0.33, 0.00, 0.56, 0.62, 0.10),        # hoof
            (0.00, -0.03, 0.58, 0.66, 0.10)]


def body_paint(c, n):
    if n[2] < -0.45:
        return "cream"                                  # belly
    if n[1] < -0.35 and c[2] < 3.1:
        return "cream"                                  # chest
    return "brown"


def neck_paint(c, n):
    return "cream" if n[1] < -0.3 and c[2] < 4.1 else "brown"     # throat


def head_paint(c, n):
    return "cream" if n[2] < -0.5 else "brown"         # chin


def ear_paint(c, n):
    return "cream" if n[1] < -0.6 else "brown"         # inside of the ear


def tail_paint(c, n):
    return "white" if n[2] < -0.2 else "brown"         # white under the tail


def leg_paint(c, n):
    return "hoof" if c[2] < HOOF else "brown"


def build_body():
    body = Part("Body")
    # Body: rings standing across the deer, from the rump (back, +y) to the chest (front, -y).
    # (y, center height, width, height, top corner, bottom corner)
    rings = [(2.04, 2.86, 0.90, 0.76, 0.26, 0.24),
             (1.92, 2.78, 1.36, 1.24, 0.38, 0.36),      # round rump
             (1.62, 2.70, 1.72, 1.50, 0.44, 0.42),      # hips
             (1.05, 2.66, 1.70, 1.46, 0.44, 0.44),
             (0.30, 2.64, 1.62, 1.42, 0.42, 0.44),      # waist
             (-0.50, 2.70, 1.68, 1.54, 0.42, 0.44),
             (-1.08, 2.80, 1.64, 1.58, 0.42, 0.40),     # shoulders
             (-1.55, 2.90, 1.30, 1.26, 0.36, 0.34)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    # Neck: level rings going up and forward, from inside the chest to inside the head.
    rings = [(2.70, -1.18, 1.00, 1.02, 0.26),
             (3.30, -1.44, 0.92, 0.94, 0.24),
             (3.85, -1.64, 0.84, 0.86, 0.22),
             (4.35, -1.80, 0.80, 0.82, 0.20)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], neck_paint, caps=(False, False))

    # Head: rings standing across the head, from the back of the head to the snout.
    rings = [(-1.38, 4.56, 0.90, 0.84, 0.26, 0.24),
             (-1.62, 4.61, 1.10, 1.04, 0.30, 0.28),     # widest: forehead
             (-1.98, 4.56, 1.06, 0.98, 0.28, 0.28),     # eyes
             (-2.36, 4.38, 0.84, 0.76, 0.22, 0.22),
             (-2.72, 4.20, 0.66, 0.58, 0.16, 0.14)]     # snout
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)

    # Eyes (black, with a small white glint) on the sides of the head, nose on the front of the snout.
    eyes(body, head[1], head[2], -1.82, 4.58)
    slab(body, (0, rings[-1][0], rings[-1][1] + 0.08), -Y, 0.32, 0.18, 0.05, "nose")

    # Ears: big flat leaves pointing out and up, the inside facing forward.
    out = unit(np.array([0.85, 0.22, 0.5]))
    flat = unit(np.cross(Z, out))                     # the thin direction of the ear
    across = unit(np.cross(out, flat))
    base = np.array([0.40, -1.46, 4.88])
    ear = [square(base, across, flat, 0.34, 0.12), square(base + out * 0.30, across, flat, 0.50, 0.11),
           square(base + out * 0.58, across, flat, 0.38, 0.09)]
    for pts, tip in sides(ear, base + out * 0.86):
        loft(body, pts, ear_paint, caps=(True, False), tip=tip)

    # Antlers: a main beam going up and out, a tine forward and a tine outward, all with blunt ends.
    for beam in [[(0.28, -1.66, 5.00, 0.26), (0.40, -1.64, 5.35, 0.24), (0.56, -1.66, 5.62, 0.22),
                  (0.66, -1.74, 5.98, 0.16)],
                 [(0.39, -1.66, 5.30, 0.21), (0.41, -1.86, 5.50, 0.19), (0.43, -2.02, 5.72, 0.15)],
                 [(0.56, -1.66, 5.56, 0.21), (0.76, -1.62, 5.72, 0.18), (0.94, -1.60, 5.90, 0.15)]]:
        for r, _ in sides([square(p[:3], X, Y, p[3], p[3]) for p in beam]):
            loft(body, r, "antler")

    # Tail: a short tuft sticking out and up at the back, white underneath.
    rings = [(1.95, 3.10, 0.46, 0.34), (2.24, 3.32, 0.44, 0.32), (2.42, 3.54, 0.32, 0.24)]
    loft(body, [ring((0, y, z), X, Z, w, h, 0.09) for y, z, w, h in rings], tail_paint)
    return body


def parts():
    """Body and the four legs. The deer's left side is +x (it faces -y)."""
    return [build_body(),
            leg("LegFL", LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
            leg("LegFR", -LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
            leg("LegBL", LEG_X + 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
            leg("LegBR", -LEG_X - 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint)]


DEER = Animal("Deer", "Common", PALETTE, GOLDEN, parts, close=((0.3, -1.6, 4.4), 6.5))

if __name__ == "__main__":
    build(DEER)
