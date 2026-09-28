"""The Boar: low-poly, with classic Roblox studs painted in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_boar.py [out_dir]          (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import X, Y, Z, Animal, Part, build, eyes, leg, loft, ring, sides, slab, square, unit

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#6e5140", "dark": "#3f2f26", "snout": "#c7978c", "tusk": "#f2ead8", "hoof": "#2c211b",
           "nose": "#1b1414", "eye": "#161211", "glint": "#ffffff"}
GOLDEN = {"brown": "#e6ac2e", "dark": "#b8801a", "snout": "#ffd690", "tusk": "#fff7df", "hoof": "#8a5a12",
          "nose": "#6a4410", "eye": "#161211", "glint": "#ffffff"}

FRONT_Y, HIND_Y = -0.95, 1.0          # where the legs stand
LEG_X = 0.42                           # how far the legs stand from the middle
LEG_TOP = 0.85                         # height of the leg joints (origin of the leg objects)
HOOF = 0.26                            # hooves are below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(1.15, 0.00, 0.56, 0.60, 0.14),
             (0.72, 0.00, 0.54, 0.58, 0.14),
             (0.45, -0.02, 0.44, 0.48, 0.11),
             (0.30, 0.00, 0.42, 0.46, 0.10),       # ankle
             (0.24, 0.00, 0.48, 0.54, 0.10),       # hoof
             (0.00, -0.02, 0.50, 0.58, 0.10)]
HIND_LEG = [(1.25, -0.02, 0.60, 0.74, 0.16),
            (0.88, 0.02, 0.66, 0.84, 0.18),        # ham, bulging out of the body a little
            (0.52, 0.10, 0.46, 0.52, 0.12),
            (0.30, 0.02, 0.42, 0.46, 0.10),        # ankle
            (0.24, 0.00, 0.48, 0.54, 0.10),        # hoof
            (0.00, -0.02, 0.50, 0.58, 0.10)]


def leg_paint(c, n):
    return "hoof" if c[2] < HOOF else "brown"


def build_body():
    body = Part("Body")
    # Body: a heavy wedge, big shoulders and a smaller rear. Rings from the rump (+y) to the chest (-y).
    # (y, center height, width, height, top corner, bottom corner)
    rings = [(1.55, 1.42, 0.80, 0.72, 0.24, 0.22),
             (1.38, 1.42, 1.26, 1.10, 0.36, 0.34),
             (0.95, 1.42, 1.44, 1.22, 0.40, 0.38),
             (0.20, 1.46, 1.50, 1.30, 0.42, 0.40),
             (-0.60, 1.56, 1.62, 1.52, 0.44, 0.42),     # shoulders
             (-1.15, 1.60, 1.46, 1.42, 0.40, 0.38),
             (-1.45, 1.60, 1.10, 1.10, 0.32, 0.30)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], "brown")

    # Mane: a ridge of dark bristles along the back.
    mane = [(-1.45, 2.10, 0.18, 0.30), (-0.95, 2.30, 0.24, 0.36), (-0.35, 2.32, 0.24, 0.34),
            (0.25, 2.16, 0.20, 0.28), (0.70, 2.06, 0.14, 0.20)]
    loft(body, [square((0, y, z), X, Z, w, h) for y, z, w, h in mane], "dark")

    # Head: a big wedge that slopes down to the flat snout.
    rings = [(-1.30, 1.72, 1.02, 0.96, 0.30, 0.28),
             (-1.62, 1.66, 1.08, 0.98, 0.30, 0.28),     # widest
             (-2.02, 1.46, 0.86, 0.76, 0.24, 0.22),
             (-2.40, 1.24, 0.66, 0.58, 0.18, 0.16),
             (-2.72, 1.12, 0.58, 0.50, 0.15, 0.13)]     # snout
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, "brown")
    eyes(body, head[1], head[2], -1.8, 1.57, w=0.14, h=0.16)

    # Snout: a pink disc with two nostrils.
    tip = rings[-1][0]
    slab(body, (0, tip, 1.12), -Y, 0.46, 0.38, 0.04, "snout")
    for x in (0.1, -0.1):
        slab(body, (x, tip - 0.04, 1.13), -Y, 0.08, 0.11, 0.015, "nose")

    # Tusks: curving up out of the sides of the snout.
    tusk = [square((0.26, -2.50, 1.10), X, Y, 0.13, 0.13), square((0.36, -2.46, 1.32), X, Y, 0.11, 0.11)]
    for pts, t in sides(tusk, np.array([0.40, -2.38, 1.52])):
        loft(body, pts, "tusk", caps=(True, False), tip=t)

    # Ears: small, pointed and turned out.
    out = unit(np.array([0.7, 0.25, 0.75]))
    flat = unit(np.cross(Z, out))                     # the thin direction of the ear
    across = unit(np.cross(out, flat))
    base = np.array([0.36, -1.40, 2.08])
    ear = [square(base, across, flat, 0.30, 0.10), square(base + out * 0.16, across, flat, 0.30, 0.09)]
    for pts, t in sides(ear, base + out * 0.45):
        loft(body, pts, "dark", caps=(True, False), tip=t)

    # Tail: thin, hanging down, with a tuft at the end.
    rings = [(1.65, 1.46, 0.16, 0.16, 0.04), (1.42, 1.66, 0.14, 0.14, 0.04), (1.22, 1.72, 0.22, 0.22, 0.06),
             (1.06, 1.72, 0.16, 0.16, 0.04)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], "dark")
    return body


def parts():
    """Body and the four legs. The boar's left side is +x (it faces -y)."""
    return [build_body(),
            leg("LegFL", LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
            leg("LegFR", -LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
            leg("LegBL", LEG_X + 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
            leg("LegBR", -LEG_X - 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint)]


BOAR = Animal("Boar", "Rare", PALETTE, GOLDEN, parts, close=((0.3, -2.0, 1.5), 4.2))

if __name__ == "__main__":
    build(BOAR)
