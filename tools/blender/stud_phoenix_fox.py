"""Phoenix Fox (Mythic): a fire fox with flame wings and three burning tails, low-poly with Roblox studs
(see stud_animal.py).

Run: python3 tools/blender/stud_phoenix_fox.py [out_dir]   (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.

Parts: Body, the four legs, the wings WingL and WingR (they turn at the shoulder), and the flames Crest (on the
head and ears) and TailFlames. The wings and flames glow: the setup script makes them Neon in Roblox.
"""

import numpy as np

from stud_animal import (X, Y, Z, Animal, Part, build, centered, effect, eyes, leg, loft, mirror, ring, scaled,
                         sides, slab, square, turn, unit)

FLAME, WING = "#ffc02e", "#ff8a1a"

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"fire": "#ff6b2c", "cream": "#fff1dc", "ember": "#6b2417", "nose": "#2a0f0a", "eye": "#161211",
           "glint": "#ffffff", "flame": FLAME, "wing": WING}
GOLDEN = {"fire": "#e6ac2e", "cream": "#fff3c4", "ember": "#9a6412", "nose": "#6a4410", "eye": "#161211",
          "glint": "#ffffff", "flame": FLAME, "wing": WING}
NO_STUDS = ("nose", "eye", "glint", "flame", "wing")

SIZE = 1.3                             # the whole fox is this many times bigger than the numbers in this file
FRONT_Y, HIND_Y = -0.8, 0.85          # where the legs stand
LEG_X = 0.27                           # how far the legs stand from the middle
LEG_TOP = 1.3                          # height of the leg joints (origin of the leg objects)
SOCKS = 0.6                            # the legs are dark red below this height

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
# Tails, level rings from inside the rump up to the tip: (height, forward/back, width, depth, corner).
TAIL = [(1.62, 1.05, 0.30, 0.34, 0.09),
        (1.90, 1.40, 0.46, 0.50, 0.13),
        (2.25, 1.66, 0.52, 0.56, 0.15),
        (2.62, 1.80, 0.46, 0.50, 0.13),
        (2.90, 1.84, 0.30, 0.34, 0.09)]
TAIL_ROOT = (0, 1.05, 1.62)
TAIL_ANGLES = (-32, 0, 32)             # the three tails fan out sideways


def tail_paint(c, n):
    return "cream" if np.linalg.norm(c - TAIL_ROOT) > 1.2 else "fire"   # cream near the tip


def body_paint(c, n):
    if n[2] < -0.45 or (n[1] < -0.35 and c[2] < 1.75):
        return "cream"                                  # belly and chest
    return "fire"


def head_paint(c, n):
    if n[2] < -0.3 or (c[2] < 2.32 and n[2] < 0.5):
        return "cream"                                  # cheeks and jaw
    return "fire"


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
         lambda c, n: "cream" if n[1] < -0.3 else "fire")

    rings = [(-1.26, 2.40, 0.74, 0.64, 0.20, 0.18),
             (-1.44, 2.44, 0.90, 0.72, 0.24, 0.22),     # cheeks
             (-1.72, 2.42, 0.80, 0.64, 0.22, 0.20),     # eyes
             (-1.92, 2.30, 0.46, 0.40, 0.12, 0.10),     # muzzle
             (-2.28, 2.22, 0.34, 0.30, 0.09, 0.08)]
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)
    eyes(body, head[1], head[2], -1.58, 2.42, w=0.18, h=0.2)
    slab(body, (0, rings[-1][0], rings[-1][1] + 0.05), -Y, 0.16, 0.10, 0.04, "nose")

    for pts, tip in sides(*ear()):
        loft(body, pts, lambda c, n: "cream" if n[1] < -0.6 else "fire", caps=(True, False), tip=tip)

    # Three big tails fanning out behind, cream near the tip.
    rings = [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in TAIL]
    for angle in TAIL_ANGLES:
        loft(body, turn(rings, TAIL_ROOT, Y, angle), tail_paint)
    return body


def ear():
    """The left ear: rings and tip (big and pointed, the inside facing forward)."""
    out = unit(np.array([0.35, 0.1, 1.0]))
    flat = unit(-Y - np.dot(-Y, out) * out)
    across = unit(np.cross(out, flat))
    base = np.array([0.24, -1.36, 2.72])
    return [square(base, across, flat, 0.36, 0.12), square(base + out * 0.18, across, flat, 0.32, 0.10)], \
        base + out * 0.5


def build_crest():
    part = Part("Crest")
    # Three flames standing on the head, leaning back, and a small flame on the tip of each ear.
    for x, lean, height, size in ((0, 0, 0.62, 0.24), (0.16, 0.14, 0.46, 0.2), (-0.16, -0.14, 0.46, 0.2)):
        base = np.array([x, -1.42, 2.70])
        loft(part, [square(base, X, Y, size, size)], "flame", caps=(True, False),
             tip=base + (x + lean, 0.22, height))
    out = unit(np.array([0.35, 0.1, 1.0]))
    tip = ear()[1]
    for pts, t in sides([square(tip - out * 0.1, X, Y, 0.14, 0.12)], tip + out * 0.34):
        loft(part, pts, "flame", caps=(True, False), tip=t)
    return centered(part)


def build_tail_flames():
    part = Part("TailFlames")
    top = TAIL[-1]
    for angle in TAIL_ANGLES:
        base = square((0, top[1], top[0] - 0.05), X, Y, 0.30, 0.34)
        tip = turn([[(0, top[1] + 0.08, top[0] + 0.55)]], TAIL_ROOT, Y, angle)[0][0]
        loft(part, turn([base], TAIL_ROOT, Y, angle), "flame", caps=(True, False), tip=tip)
    return centered(part)


def build_wing(name, sign):
    # A flat flame wing rising up and back from the shoulder. (out, forward/back, height, length, thickness)
    rings = [(0.40, -0.55, 1.90, 0.70, 0.14), (0.85, -0.40, 2.25, 0.92, 0.13), (1.25, -0.16, 2.68, 0.78, 0.11)]
    pts = [square((x, y, z), Y, Z, length, thick) for x, y, z, length, thick in rings]
    tip = np.array([1.50, 0.18, 3.10])
    if sign < 0:
        pts, tip = [mirror(r) for r in pts], mirror([tip])[0]
    part = Part(name, origin=(sign * 0.40, -0.55, 1.90))
    loft(part, pts, "wing", caps=(True, False), tip=tip)
    return part


def parts():
    """Body, legs, wings and flames, SIZE times as big. The phoenix fox faces -y; its left is +x."""
    socks = lambda c, n: "ember" if c[2] < SOCKS else "fire"
    return scaled([build_body(),
                   leg("LegFL", LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, socks),
                   leg("LegFR", -LEG_X, FRONT_Y, LEG_TOP, FRONT_LEG, socks),
                   leg("LegBL", LEG_X + 0.03, HIND_Y, LEG_TOP, HIND_LEG, socks),
                   leg("LegBR", -LEG_X - 0.03, HIND_Y, LEG_TOP, HIND_LEG, socks),
                   build_wing("WingL", 1), build_wing("WingR", -1), build_crest(), build_tail_flames()], SIZE)


PHOENIX_FOX = Animal(
    "PhoenixFox", "Mythic", PALETTE, GOLDEN, parts, close=((0.3, -1.6, 3.0), 5.2), no_studs=NO_STUDS,
    display="Phoenix Fox",
    glow={"Crest": FLAME, "TailFlames": FLAME, "WingL": WING, "WingR": WING},
    effects=[effect("TailFire", "TailFlames", "Fire", "#ff8c1a", "#ff3b1f", rate=12, size=(1.0, 0),
                    lifetime=(0.4, 0.7), speed=(1.5, 2.5), spread=20),
             effect("Embers", "Body", "Sparkles", "#ffd23f", "#ff3b1f", rate=5, size=(0.4, 0), speed=(0.5, 1.2),
                    accel=(0, 2, 0))],
    light=("Body", "#ff8c1a", 1.5, 14))

if __name__ == "__main__":
    build(PHOENIX_FOX)
