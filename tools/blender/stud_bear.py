"""The Bear: low-poly, with classic Roblox studs painted in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_bear.py [out_dir]          (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

from stud_animal import X, Y, Z, Animal, Part, build, eyes, leg, loft, ring, sides, slab

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#6f4a30", "light": "#c9a37a", "dark": "#3b271a", "nose": "#1a1412", "eye": "#161211",
           "glint": "#ffffff"}
GOLDEN = {"brown": "#e6ac2e", "light": "#ffe38a", "dark": "#9a6412", "nose": "#6a4410", "eye": "#161211",
          "glint": "#ffffff"}

SIZE = 1.2                             # the whole bear is this many times bigger than the numbers in this file
FRONT_Y, HIND_Y = -1.3, 1.4           # where the legs stand
LEG_X = 0.62                           # how far the legs stand from the middle
LEG_TOP = 1.7                          # height of the leg joints (origin of the leg objects)
PAWS = 0.3                             # the dark paws are below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(2.05, 0.00, 0.84, 0.88, 0.22),
             (1.40, 0.00, 0.86, 0.90, 0.22),
             (0.80, -0.02, 0.74, 0.78, 0.19),
             (0.40, 0.00, 0.72, 0.78, 0.18),
             (0.26, -0.06, 0.80, 0.96, 0.20),      # big paw
             (0.00, -0.08, 0.82, 1.00, 0.20)]
HIND_LEG = [(2.15, -0.02, 0.88, 1.04, 0.24),
            (1.55, 0.02, 0.98, 1.20, 0.26),        # thigh, bulging out of the body a little
            (0.90, 0.10, 0.78, 0.86, 0.20),
            (0.40, 0.04, 0.72, 0.80, 0.18),
            (0.26, -0.04, 0.80, 0.98, 0.20),       # big paw
            (0.00, -0.06, 0.82, 1.02, 0.20)]


def head_paint(c, n):
    return "light" if c[1] < -2.85 else "brown"        # light muzzle


def ear_paint(c, n):
    return "light" if n[1] < -0.9 else "brown"         # light inside


def leg_paint(c, n):
    return "dark" if c[2] < PAWS else "brown"


def build_body():
    body = Part("Body")
    # Body: big and heavy, with a hump above the shoulders. Rings from the rump (+y) to the chest (-y).
    # (y, center height, width, height, top corner, bottom corner)
    rings = [(2.05, 2.25, 1.20, 1.10, 0.34, 0.32),
             (1.85, 2.22, 1.80, 1.64, 0.50, 0.48),
             (1.30, 2.20, 2.04, 1.80, 0.56, 0.54),      # hips
             (0.30, 2.18, 2.00, 1.72, 0.54, 0.54),
             (-0.70, 2.32, 2.10, 2.04, 0.58, 0.56),     # hump above the shoulders
             (-1.40, 2.36, 1.90, 1.90, 0.52, 0.50),
             (-1.85, 2.36, 1.40, 1.44, 0.40, 0.38)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], "brown")

    # Neck: short and thick, level rings going forward into the head.
    rings = [(2.25, -1.55, 1.34, 1.24, 0.36), (2.50, -1.95, 1.26, 1.12, 0.33)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], "brown")

    # Head: round cheeks and a short, light muzzle.
    rings = [(-1.85, 2.62, 1.30, 1.16, 0.36, 0.34),
             (-2.15, 2.66, 1.50, 1.30, 0.42, 0.40),     # widest: cheeks
             (-2.60, 2.58, 1.36, 1.14, 0.38, 0.36),     # eyes
             (-2.82, 2.36, 0.84, 0.72, 0.24, 0.22),     # muzzle
             (-3.28, 2.28, 0.74, 0.62, 0.20, 0.18)]
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)
    eyes(body, head[1], head[2], -2.4, 2.68, w=0.2, h=0.22)
    slab(body, (0, rings[-1][0], rings[-1][1] + 0.12), -Y, 0.36, 0.22, 0.05, "nose")

    # Ears: small and round, light inside.
    ear = [ring((0.50, -2.02, 3.32), X, Z, 0.44, 0.44, 0.13), ring((0.50, -1.88, 3.32), X, Z, 0.44, 0.44, 0.13)]
    for pts, _ in sides(ear):
        loft(body, pts, ear_paint)

    # Tail: a short stub.
    rings = [(2.00, 2.60, 0.36, 0.34, 0.10), (2.24, 2.64, 0.32, 0.30, 0.09)]
    loft(body, [ring((0, y, z), X, Z, w, h, c) for y, z, w, h, c in rings], "brown")
    return body


def parts():
    """Body and the four legs, SIZE times as big as the numbers above. The bear's left side is +x (it faces -y)."""
    pieces = [build_body(),
              leg("LegFL", LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
              leg("LegFR", -LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
              leg("LegBL", LEG_X + 0.04, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
              leg("LegBR", -LEG_X - 0.04, HIND_Y, LEG_TOP, HIND_LEG, leg_paint)]
    for part in pieces:
        part.verts = [v * SIZE for v in part.verts]
        part.origin = part.origin * SIZE
    return pieces


BEAR = Animal("Bear", "Epic", PALETTE, GOLDEN, parts, close=((0.5, -2.75, 3.2), 7.2))

if __name__ == "__main__":
    build(BEAR)
