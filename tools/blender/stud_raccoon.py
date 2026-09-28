"""The Raccoon: low-poly, with classic Roblox studs painted in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_raccoon.py [out_dir]       (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import X, Y, Z, Animal, Part, build, eyes, leg, loft, ring, sides, slab, square, unit

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"grey": "#8f8b86", "light": "#e8e4dc", "dark": "#37312f", "eyering": "#f4f1ea", "nose": "#1a1716",
           "eye": "#161211", "glint": "#ffffff"}
GOLDEN = {"grey": "#e6ac2e", "light": "#fff3c4", "dark": "#9a6412", "eyering": "#fff8e0", "nose": "#6a4410",
          "eye": "#161211", "glint": "#ffffff"}
NO_STUDS = ("eyering", "nose", "eye", "glint")

PAWS = 0.3                             # the dark paws are below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(0.95, 0.00, 0.40, 0.42, 0.10),
             (0.55, 0.00, 0.40, 0.42, 0.10),
             (0.25, -0.02, 0.36, 0.40, 0.09),
             (0.12, -0.05, 0.40, 0.50, 0.09),      # paw
             (0.00, -0.06, 0.42, 0.52, 0.09)]
HIND_LEG = [(1.10, 0.00, 0.46, 0.60, 0.12),
            (0.75, 0.02, 0.52, 0.68, 0.14),        # thigh
            (0.35, 0.06, 0.40, 0.46, 0.10),
            (0.12, -0.04, 0.40, 0.56, 0.09),       # paw
            (0.00, -0.06, 0.42, 0.58, 0.09)]


def body_paint(c, n):
    return "light" if n[2] < -0.45 else "grey"         # lighter belly


def head_paint(c, n):
    if c[1] < -1.32:
        return "light"                                  # white muzzle
    if c[1] < -1.1:
        return "light" if n[2] < -0.3 else "dark"      # the black mask across the face...
    if abs(n[0]) > 0.45 and c[2] < 1.8 and c[1] < -0.8:
        return "dark"                                   # ...and around the eyes
    if n[2] < -0.4:
        return "light"                                  # chin
    return "grey"


def ear_paint(c, n):
    return "light" if n[1] < -0.6 else "grey"          # white inside


def tail_paint(c, n):
    band = int((c[1] - 1.2) // 0.25)
    return "dark" if band % 2 or c[1] > 2.2 else "grey"   # black rings and a black tip


def leg_paint(c, n):
    return "dark" if c[2] < PAWS else "grey"           # black paws


def build_body():
    body = Part("Body")
    # Body: round and chubby, the rear higher than the shoulders. Rings from the back (+y) to the chest (-y).
    # (y, center height, width, height, top corner, bottom corner)
    rings = [(1.05, 1.20, 0.70, 0.66, 0.22, 0.20),
             (0.90, 1.20, 1.12, 1.06, 0.34, 0.32),
             (0.50, 1.22, 1.30, 1.24, 0.38, 0.36),      # round rear
             (-0.10, 1.12, 1.22, 1.06, 0.36, 0.34),
             (-0.55, 1.12, 1.10, 1.00, 0.33, 0.32),     # chest
             (-0.80, 1.16, 0.84, 0.80, 0.26, 0.24)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    # Head: wide cheeks and a pointed muzzle, sitting on the front of the body.
    rings = [(-0.66, 1.62, 0.84, 0.74, 0.24, 0.22),
             (-0.86, 1.66, 1.00, 0.84, 0.28, 0.26),     # widest: cheeks
             (-1.12, 1.62, 0.90, 0.74, 0.26, 0.24),     # eyes
             (-1.30, 1.50, 0.50, 0.42, 0.13, 0.11),     # muzzle
             (-1.58, 1.44, 0.34, 0.28, 0.09, 0.08)]
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)
    eyes(body, head[1], head[2], -0.99, 1.63, w=0.18, h=0.2, rim="eyering")
    slab(body, (0, rings[-1][0], rings[-1][1] + 0.04), -Y, 0.16, 0.10, 0.04, "nose")

    # Ears: small and rounded, white inside.
    out = unit(np.array([0.45, 0.1, 1.0]))
    flat = unit(-Y - np.dot(-Y, out) * out)            # the thin direction of the ear
    across = unit(np.cross(out, flat))
    base = np.array([0.30, -0.72, 1.98])
    ear = [square(base, across, flat, 0.30, 0.10), square(base + out * 0.14, across, flat, 0.32, 0.10),
           square(base + out * 0.28, across, flat, 0.18, 0.08)]
    for pts, _ in sides(ear):
        loft(body, pts, ear_paint)

    # Tail: bushy, with black rings.
    rings = [(0.95, 1.30, 0.34, 0.34, 0.10),
             (1.20, 1.22, 0.46, 0.46, 0.13),
             (1.45, 1.12, 0.50, 0.50, 0.14),
             (1.70, 1.02, 0.50, 0.50, 0.14),
             (1.95, 0.94, 0.46, 0.46, 0.13),
             (2.20, 0.88, 0.36, 0.36, 0.10),
             (2.34, 0.86, 0.20, 0.20, 0.06)]
    loft(body, [ring((0, y, z), X, Z, w, h, c) for y, z, w, h, c in rings], tail_paint)
    return body


def parts():
    """Body and the four legs. The raccoon's left side is +x (it faces -y)."""
    return [build_body(),
            leg("LegFL", 0.30, -0.50, 0.75, FRONT_LEG, leg_paint),
            leg("LegFR", -0.30, -0.50, 0.75, FRONT_LEG, leg_paint),
            leg("LegBL", 0.36, 0.55, 0.85, HIND_LEG, leg_paint),
            leg("LegBR", -0.36, 0.55, 0.85, HIND_LEG, leg_paint)]


RACCOON = Animal("Raccoon", "Common", PALETTE, GOLDEN, parts, close=((0.2, -0.9, 1.5), 3.2), no_studs=NO_STUDS)

if __name__ == "__main__":
    build(RACCOON)
