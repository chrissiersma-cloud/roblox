"""The Rabbit: low-poly, with classic Roblox studs painted in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_rabbit.py [out_dir]        (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import X, Y, Z, Animal, Part, build, eyes, leg, loft, ring, sides, slab, square, unit

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#9e7d5e", "cream": "#efe4cc", "white": "#fbf8f1", "pink": "#eba5a5", "nose": "#d98590",
           "eye": "#161211", "glint": "#ffffff"}
GOLDEN = {"brown": "#e6ac2e", "cream": "#ffe38a", "white": "#fff6d2", "pink": "#ffcf7a", "nose": "#c98a1a",
          "eye": "#161211", "glint": "#ffffff"}

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
# The rabbit crouches: short front legs, and big hind legs with long feet flat on the ground.
FRONT_LEG = [(0.80, 0.00, 0.40, 0.42, 0.10),
             (0.40, 0.00, 0.38, 0.40, 0.09),
             (0.14, -0.06, 0.42, 0.56, 0.10),      # paw
             (0.00, -0.08, 0.42, 0.58, 0.10)]
HIND_LEG = [(1.20, 0.00, 0.46, 0.80, 0.14),
            (0.85, 0.00, 0.58, 1.02, 0.18),        # thigh, bulging out of the body a little
            (0.42, -0.08, 0.50, 0.92, 0.15),
            (0.16, -0.24, 0.44, 1.00, 0.12),       # long foot
            (0.00, -0.26, 0.46, 1.04, 0.12)]


def body_paint(c, n):
    if n[2] < -0.45:
        return "cream"                                  # belly
    if n[1] < -0.35 and c[2] < 1.3:
        return "cream"                                  # chest
    return "brown"


def head_paint(c, n):
    if c[1] < -1.05 or (c[1] < -0.9 and c[2] < 1.7):
        return "cream"                                  # muzzle
    if n[2] < -0.4 and c[1] < -0.85:
        return "cream"                                  # chin
    return "brown"


def ear_paint(c, n):
    return "pink" if n[1] < -0.6 else "brown"          # inside of the ear


def build_body():
    body = Part("Body")
    # Body: a round, crouching body, rings from the back (+y) to the chest (front, -y).
    # (y, center height, width, height, top corner, bottom corner)
    rings = [(1.02, 1.02, 0.84, 0.84, 0.28, 0.26),
             (0.86, 1.06, 1.26, 1.36, 0.42, 0.40),
             (0.50, 1.08, 1.44, 1.48, 0.46, 0.44),      # widest, above the hind legs
             (0.00, 1.04, 1.36, 1.36, 0.44, 0.42),
             (-0.40, 1.06, 1.18, 1.20, 0.38, 0.38),     # chest
             (-0.62, 1.10, 0.90, 0.92, 0.28, 0.28)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    # Head: big and round, with chubby cheeks and a short muzzle. It sits on the front of the body.
    rings = [(-0.36, 1.86, 0.92, 0.88, 0.28, 0.26),
             (-0.58, 1.92, 1.10, 1.02, 0.32, 0.30),     # widest: cheeks
             (-0.90, 1.86, 1.06, 0.94, 0.32, 0.30),     # eyes
             (-1.12, 1.72, 0.74, 0.66, 0.22, 0.20)]     # muzzle
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)
    eyes(body, head[1], head[2], -0.76, 1.92, w=0.22, h=0.26)
    slab(body, (0, rings[-1][0], rings[-1][1] + 0.08), -Y, 0.20, 0.14, 0.04, "nose")

    # Ears: long, standing up and a little apart, pink inside (facing forward), rounded at the top.
    out = unit(np.array([0.18, 0.28, 1.0]))
    flat = unit(-Y - np.dot(-Y, out) * out)            # the thin direction of the ear
    across = unit(np.cross(out, flat))
    base = np.array([0.20, -0.46, 2.30])
    ear = [square(base, across, flat, 0.30, 0.13), square(base + out * 0.35, across, flat, 0.42, 0.13),
           square(base + out * 0.78, across, flat, 0.38, 0.11), square(base + out * 0.98, across, flat, 0.22, 0.09)]
    for pts, _ in sides(ear):
        loft(body, pts, ear_paint)

    # Tail: a white cotton ball at the back.
    rings = [(1.00, 1.12, 0.40, 0.40, 0.12), (1.18, 1.14, 0.50, 0.50, 0.15), (1.34, 1.14, 0.36, 0.36, 0.10)]
    loft(body, [ring((0, y, z), X, Z, w, h, c) for y, z, w, h, c in rings], "white")
    return body


def parts():
    """Body and the four legs. The rabbit's left side is +x (it faces -y)."""
    return [build_body(),
            leg("LegFL", 0.30, -0.42, 0.55, FRONT_LEG, "brown"),
            leg("LegFR", -0.30, -0.42, 0.55, FRONT_LEG, "brown"),
            leg("LegBL", 0.46, 0.55, 0.90, HIND_LEG, "brown"),
            leg("LegBR", -0.46, 0.55, 0.90, HIND_LEG, "brown")]


RABBIT = Animal("Rabbit", "Common", PALETTE, GOLDEN, parts, close=((0.25, -0.7, 1.9), 3.4))

if __name__ == "__main__":
    build(RABBIT)
