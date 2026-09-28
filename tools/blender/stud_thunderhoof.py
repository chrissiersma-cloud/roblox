"""Thunderhoof (Legendary): a white stag with lightning-bolt antlers, low-poly with Roblox studs (see stud_animal.py).

Run: python3 tools/blender/stud_thunderhoof.py [out_dir]   (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.

Parts: Body, the four legs, and two glowing parts that the setup script makes Neon in Roblox: Lightning (the
antlers, the bolts on its sides and the bolt on its tail) and Mane (the blue crest along the back of the neck).
"""

import numpy as np

from stud_animal import (X, Y, Z, Animal, Part, build, centered, effect, eyes, leg, loft, ring, scaled, sides,
                         slab, square, tube, unit)

BOLT, MANE = "#ffe23a", "#46d2ff"

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"white": "#eef3ff", "blue": "#c3d6ff", "cyan": "#9fe6ff", "hoof": "#ffd84a", "nose": "#3a4766",
           "eye": "#1f5fe0", "glint": "#ffffff", "bolt": BOLT, "mane": MANE}
GOLDEN = {"white": "#f2c037", "blue": "#ffe38a", "cyan": "#fff0a0", "hoof": "#fff6d2", "nose": "#6a4410",
          "eye": "#1f5fe0", "glint": "#ffffff", "bolt": BOLT, "mane": MANE}
NO_STUDS = ("nose", "eye", "glint", "bolt", "mane")

SIZE = 1.15                            # the whole stag is this many times bigger than the numbers in this file
FRONT_Y, HIND_Y = -1.05, 1.3          # where the legs stand
LEG_X = 0.45                           # how far the legs stand from the middle
LEG_TOP = 2.3                          # height of the leg joints (origin of the leg objects)
HOOF = 0.38                            # the golden hooves are below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(2.55, 0.00, 0.60, 0.62, 0.15),
             (1.90, 0.00, 0.62, 0.66, 0.15),
             (1.40, -0.02, 0.52, 0.56, 0.12),
             (1.08, -0.04, 0.54, 0.58, 0.12),      # knee
             (0.80, -0.02, 0.48, 0.52, 0.10),
             (0.40, 0.00, 0.50, 0.54, 0.10),       # ankle
             (0.33, 0.00, 0.58, 0.64, 0.10),       # hoof
             (0.00, -0.03, 0.60, 0.68, 0.10)]
HIND_LEG = [(2.70, -0.02, 0.62, 0.76, 0.16),
            (2.20, 0.02, 0.76, 0.94, 0.20),        # thigh
            (1.60, 0.10, 0.60, 0.70, 0.15),
            (1.08, 0.18, 0.52, 0.56, 0.12),        # hock
            (0.80, 0.10, 0.48, 0.52, 0.10),
            (0.40, 0.02, 0.50, 0.54, 0.10),        # ankle
            (0.33, 0.00, 0.58, 0.64, 0.10),        # hoof
            (0.00, -0.03, 0.60, 0.68, 0.10)]


def body_paint(c, n):
    if n[2] < -0.45 or (n[1] < -0.35 and c[2] < 3.1):
        return "blue"                                   # belly and chest
    return "white"


def neck_paint(c, n):
    return "blue" if n[1] < -0.3 and c[2] < 4.1 else "white"


def head_paint(c, n):
    return "blue" if n[2] < -0.5 else "white"


def ear_paint(c, n):
    return "cyan" if n[1] < -0.6 else "white"


def leg_paint(c, n):
    return "hoof" if c[2] < HOOF else "white"


def build_body():
    body = Part("Body")
    # A heroic deer: a deep chest and a strong neck. (y, center height, width, height, top corner, bottom corner)
    rings = [(2.04, 2.86, 0.90, 0.76, 0.26, 0.24),
             (1.92, 2.78, 1.36, 1.24, 0.38, 0.36),
             (1.62, 2.70, 1.72, 1.50, 0.44, 0.42),      # hips
             (1.05, 2.66, 1.70, 1.46, 0.44, 0.44),
             (0.30, 2.64, 1.62, 1.42, 0.42, 0.44),      # waist
             (-0.50, 2.70, 1.72, 1.60, 0.42, 0.44),
             (-1.08, 2.82, 1.74, 1.70, 0.44, 0.42),     # big chest
             (-1.55, 2.92, 1.36, 1.34, 0.36, 0.34)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    rings = [(2.70, -1.18, 1.04, 1.06, 0.27),
             (3.30, -1.44, 0.96, 0.98, 0.25),
             (3.85, -1.64, 0.86, 0.88, 0.22),
             (4.35, -1.80, 0.80, 0.82, 0.20)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], neck_paint)

    rings = [(-1.38, 4.56, 0.90, 0.84, 0.26, 0.24),
             (-1.62, 4.61, 1.10, 1.04, 0.30, 0.28),
             (-1.98, 4.56, 1.06, 0.98, 0.28, 0.28),     # eyes
             (-2.36, 4.38, 0.84, 0.76, 0.22, 0.22),
             (-2.72, 4.20, 0.66, 0.58, 0.16, 0.14)]     # snout
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)
    eyes(body, head[1], head[2], -1.82, 4.58)
    slab(body, (0, rings[-1][0], rings[-1][1] + 0.08), -Y, 0.32, 0.18, 0.05, "nose")

    out = unit(np.array([0.85, 0.22, 0.5]))
    flat = unit(np.cross(Z, out))
    across = unit(np.cross(out, flat))
    base = np.array([0.40, -1.46, 4.88])
    ear = [square(base, across, flat, 0.34, 0.12), square(base + out * 0.30, across, flat, 0.50, 0.11),
           square(base + out * 0.58, across, flat, 0.38, 0.09)]
    for pts, tip in sides(ear, base + out * 0.86):
        loft(body, pts, ear_paint, caps=(True, False), tip=tip)

    rings = [(1.95, 3.10, 0.46, 0.34), (2.24, 3.32, 0.44, 0.32), (2.42, 3.54, 0.32, 0.24)]
    loft(body, [ring((0, y, z), X, Z, w, h, 0.09) for y, z, w, h in rings],
         lambda c, n: "blue" if n[2] < -0.2 else "white")
    return body


def build_lightning():
    part = Part("Lightning")
    # Antlers: a zigzag bolt on each side of the head.
    antler = [(0.28, -1.66, 4.95), (0.62, -1.60, 5.40), (0.46, -1.68, 5.55), (0.90, -1.60, 6.05),
              (0.76, -1.68, 6.20)]
    tip = (1.18, -1.56, 6.80)
    for pts, t in sides([antler], np.array(tip)):
        tube(part, pts[0], [0.28, 0.26, 0.24, 0.21, 0.18], "bolt", tip=t)
    # A bolt on each side of the body, and one flying up out of the tail.
    flank = [(0.85, -0.60, 3.10), (0.84, -0.05, 2.78), (0.84, -0.22, 2.70)]
    for pts, t in sides([flank], np.array([0.83, 0.45, 2.30])):
        tube(part, pts[0], [0.15, 0.14, 0.13], "bolt", tip=t)
    tube(part, [(0, 2.25, 3.40), (0, 2.52, 3.85), (0, 2.38, 3.93)], [0.2, 0.18, 0.16], "bolt", tip=(0, 2.75, 4.50))
    return centered(part)


def build_mane():
    part = Part("Mane")
    # Tufts of blue fire along the back of the neck, from the head down to the shoulders.
    back_up = unit(np.array([0, 0.75, 0.66]))
    across = unit(np.cross(back_up, X))
    for (y, z), size, length in zip([(-1.45, 4.75), (-1.45, 4.30), (-1.28, 3.85), (-1.06, 3.40)],
                                    [0.32, 0.30, 0.28, 0.26], [0.62, 0.58, 0.54, 0.50]):
        base = np.array([0, y, z])
        loft(part, [square(base, X, across, size, size)], "mane", caps=(True, False), tip=base + back_up * length)
    return centered(part)


def parts():
    """Body, the four legs and the glowing parts, SIZE times as big. Thunderhoof faces -y; its left is +x."""
    return scaled([build_body(),
                   leg("LegFL", LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
                   leg("LegFR", -LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
                   leg("LegBL", LEG_X + 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
                   leg("LegBR", -LEG_X - 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
                   build_lightning(), build_mane()], SIZE)


THUNDERHOOF = Animal(
    "Thunderhoof", "Legendary", PALETTE, GOLDEN, parts, close=((0.35, -1.8, 5.5), 8.2), no_studs=NO_STUDS,
    glow={"Lightning": BOLT, "Mane": MANE},
    effects=[effect("Sparks", "Lightning", "Sparkles", BOLT, "#ffffff", rate=8, size=(0.5, 0), lifetime=(0.2, 0.5),
                    speed=(3, 6))],
    light=("Lightning", "#9fe6ff", 1.5, 14))

if __name__ == "__main__":
    build(THUNDERHOOF)
