"""Voidwhisker (Mythic): a shadow cat with glowing purple runes, low-poly with Roblox studs (see stud_animal.py).

Run: python3 tools/blender/stud_voidwhisker.py [out_dir]   (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.

Parts: Body, the four legs, and three glowing parts that the setup script makes Neon in Roblox: Void (the rune on
the forehead, the collar and the whiskers), Gems (the gem on the collar and two orbs floating next to the cat)
and TailWisp (the crystal at the end of the tail).
"""

import numpy as np

from stud_animal import (X, Y, Z, Animal, Part, build, centered, diamond, effect, eyes, leg, loft, newell, ring,
                         scaled, sides, slab, square, tube, unit)

VOID, GEM = "#b14dff", "#ff9cf2"

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"fur": "#241640", "soft": "#3d2766", "inner": "#8e3fe0", "nose": "#c070ff", "eye": "#ff8cf5",
           "glint": "#ffffff", "void": VOID, "gem": GEM}
GOLDEN = {"fur": "#e6ac2e", "soft": "#ffe38a", "inner": "#fff0a0", "nose": "#c98a1a", "eye": "#ff8cf5",
          "glint": "#ffffff", "void": VOID, "gem": GEM}
NO_STUDS = ("nose", "eye", "glint", "void", "gem")

SIZE = 1.25                            # the whole cat is this many times bigger than the numbers in this file
FRONT_Y, HIND_Y = -0.75, 0.8          # where the legs stand
LEG_X = 0.28                           # how far the legs stand from the middle
LEG_TOP = 1.35                         # height of the leg joints (origin of the leg objects)
PAWS = 0.2                             # the lighter paws are below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(1.60, 0.00, 0.42, 0.44, 0.10),
             (1.10, 0.00, 0.42, 0.44, 0.10),
             (0.60, -0.02, 0.36, 0.40, 0.09),
             (0.18, -0.03, 0.36, 0.40, 0.09),
             (0.12, -0.05, 0.42, 0.52, 0.10),      # round paw
             (0.00, -0.06, 0.42, 0.52, 0.10)]
HIND_LEG = [(1.65, -0.02, 0.46, 0.58, 0.12),
            (1.25, 0.02, 0.54, 0.72, 0.14),        # thigh
            (0.80, 0.14, 0.40, 0.46, 0.10),
            (0.50, 0.18, 0.36, 0.40, 0.09),        # hock
            (0.18, 0.02, 0.36, 0.40, 0.09),
            (0.12, -0.02, 0.42, 0.52, 0.10),       # round paw
            (0.00, -0.04, 0.42, 0.52, 0.10)]
COLLAR = (-1.12, 2.22, 0.80, 0.76, 0.22)   # y, height, width, depth, corner: the glowing collar around the neck


def body_paint(c, n):
    return "soft" if n[2] < -0.45 or (n[1] < -0.35 and c[2] < 1.8) else "fur"


def head_paint(c, n):
    return "soft" if n[2] < -0.4 else "fur"


def leg_paint(c, n):
    return "soft" if c[2] < PAWS else "fur"


def head_rings():
    # A round cat head with a short muzzle. (y, center height, width, height, top corner, bottom corner)
    rings = [(-0.98, 2.56, 0.84, 0.74, 0.25, 0.23),
             (-1.16, 2.60, 1.02, 0.86, 0.30, 0.27),     # cheeks
             (-1.48, 2.56, 0.96, 0.78, 0.28, 0.25),     # eyes
             (-1.66, 2.42, 0.50, 0.40, 0.13, 0.11),     # muzzle
             (-1.80, 2.38, 0.38, 0.30, 0.09, 0.08)]
    return [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]


def build_body():
    body = Part("Body")
    rings = [(1.12, 1.60, 0.62, 0.54, 0.18, 0.16),
             (1.00, 1.58, 0.96, 0.84, 0.28, 0.26),
             (0.70, 1.56, 1.04, 0.86, 0.30, 0.28),      # hips
             (0.10, 1.54, 0.94, 0.78, 0.28, 0.28),      # slim waist
             (-0.40, 1.60, 1.00, 0.90, 0.30, 0.30),     # chest
             (-0.85, 1.70, 0.92, 0.88, 0.28, 0.26),
             (-1.10, 1.78, 0.70, 0.70, 0.22, 0.20)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    rings = [(1.75, -0.92, 0.76, 0.74, 0.21), (2.15, -1.08, 0.72, 0.68, 0.20), (2.45, -1.18, 0.64, 0.60, 0.17)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], "fur")

    head = head_rings()
    loft(body, head, head_paint)
    eyes(body, head[1], head[2], -1.32, 2.57, w=0.2, h=0.22)
    slab(body, (0, -1.80, 2.44), -Y, 0.14, 0.09, 0.03, "nose")

    # Big pointed ears, glowing purple inside (the inside faces forward).
    out = unit(np.array([0.35, 0.08, 1.0]))
    flat = unit(-Y - np.dot(-Y, out) * out)
    across = unit(np.cross(out, flat))
    base = np.array([0.26, -1.08, 2.92])
    ear = [square(base, across, flat, 0.40, 0.13), square(base + out * 0.2, across, flat, 0.36, 0.11)]
    for pts, tip in sides(ear, base + out * 0.58):
        loft(body, pts, lambda c, n: "inner" if n[1] < -0.6 else "fur", caps=(True, False), tip=tip)

    # A long tail curling up behind. (height, forward/back, width, depth, corner)
    rings = [(1.70, 1.02, 0.28, 0.30, 0.08), (1.95, 1.38, 0.28, 0.30, 0.08), (2.40, 1.62, 0.26, 0.28, 0.07),
             (2.95, 1.66, 0.24, 0.26, 0.07), (3.40, 1.50, 0.22, 0.24, 0.06)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], "fur")
    return body


def build_void():
    part = Part("Void")
    head = head_rings()
    # The rune: a glowing diamond on the forehead, on the face between the eyes and the muzzle.
    top = [head[2][2], head[2][3], head[3][3], head[3][2]]      # top face between those two rings
    n = unit(newell(top))
    n = n if n[2] > 0 else -n
    mid = np.mean(top, 0)
    slab(part, mid, n, 0.18, 0.2, 0.02, "void", corner=0.08)
    # The collar: a glowing band around the neck.
    y, z, w, d, c = COLLAR
    loft(part, [ring((0, y, z - 0.06), X, Y, w, d, c), ring((0, y, z + 0.06), X, Y, w, d, c)], "void")
    # Whiskers: two thin glowing sticks on each side of the muzzle.
    for whisker in ([(0.22, -1.70, 2.40), (0.64, -1.62, 2.47)], [(0.22, -1.70, 2.35), (0.62, -1.64, 2.28)]):
        for pts, _ in sides([whisker]):
            tube(part, pts[0], [0.04, 0.03], "void")
    return centered(part)


def build_gems():
    part = Part("Gems")
    y, z, w, d, c = COLLAR
    diamond(part, (0, y - d / 2 - 0.03, z), 0.18, 0.26, "gem")        # on the front of the collar
    for x in (0.95, -0.95):
        diamond(part, (x, -0.30, 2.55), 0.22, 0.34, "gem")            # floating next to the cat
    return centered(part)


def build_tail_wisp():
    part = Part("TailWisp")
    diamond(part, (0, 1.50, 3.66), 0.38, 0.6, "void")
    return centered(part)


def parts():
    """Body, legs and the glowing parts, SIZE times as big. Voidwhisker faces -y; its left is +x."""
    return scaled([build_body(),
                   leg("LegFL", LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
                   leg("LegFR", -LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, leg_paint),
                   leg("LegBL", LEG_X + 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
                   leg("LegBR", -LEG_X - 0.03, HIND_Y, LEG_TOP, HIND_LEG, leg_paint),
                   build_void(), build_gems(), build_tail_wisp()], SIZE)


VOIDWHISKER = Animal(
    "Voidwhisker", "Mythic", PALETTE, GOLDEN, parts, close=((0.3, -1.3, 2.8), 4.8), no_studs=NO_STUDS,
    glow={"Void": VOID, "Gems": GEM, "TailWisp": VOID},
    effects=[effect("VoidSparks", "TailWisp", "Sparkles", VOID, GEM, rate=6, size=(0.5, 0), speed=(0.3, 0.9)),
             effect("ShadowWisps", "Body", "Smoke", "#3a1466", rate=5, size=(1.2, 2.6), lifetime=(1.0, 1.6),
                    speed=(0.2, 0.6), transparency=0.5, light_emission=0)],
    light=("Body", VOID, 1.2, 12))

if __name__ == "__main__":
    build(VOIDWHISKER)
