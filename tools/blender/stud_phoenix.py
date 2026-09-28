"""The Phoenix (Mythic): a bird of fire with burning wings, low-poly with Roblox studs (see stud_animal.py).

Run: python3 tools/blender/stud_phoenix.py [out_dir]       (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.

The phoenix stands upright like the owl. Parts: Body (with head, beak and the three long tail feathers), the wings
WingL and WingR (they turn at the shoulder), the legs LegL and LegR, and the flames that glow (Neon in Roblox):
Crest (on the head), TailFlames, and WingFlameL / WingFlameR (they are attached to the wings and move with them).
"""

import numpy as np

from stud_animal import (X, Y, Z, Animal, Part, build, centered, effect, eyes, leg, loft, mirror, ring, scaled,
                         square, turn, unit)

FLAME = "#ffc02e"

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"red": "#e8331f", "orange": "#ff7a1a", "yellow": "#ffc13a", "gold": "#f5b82e", "beak": "#ffd23f",
           "eyering": "#ffd23f", "eye": "#1a0a05", "glint": "#ffffff", "flame": FLAME}
GOLDEN = {**PALETTE, "red": "#e6ac2e", "orange": "#ffd66b", "yellow": "#fff0a0", "gold": "#fff6d2"}
NO_STUDS = ("beak", "eyering", "eye", "glint", "flame")

SIZE = 1.25                            # the whole phoenix is this many times bigger than the numbers in this file

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
LEG = [(1.10, 0.00, 0.26, 0.28, 0.07),
       (0.60, 0.02, 0.20, 0.22, 0.05),
       (0.18, -0.02, 0.20, 0.22, 0.05),
       (0.10, -0.14, 0.34, 0.56, 0.08),            # talons, forward
       (0.00, -0.16, 0.36, 0.60, 0.08)]

# Wings rise up and out from the shoulder.
SHOULDER = np.array([0.42, 0.05, 2.20])
SPAN = unit(np.array([0.85, 0.12, 0.62]))          # from the shoulder to the wing tip
_back, _up = unit(Y - np.dot(Y, SPAN) * SPAN), unit(Z - np.dot(Z, SPAN) * SPAN)
CHORD = unit(0.55 * _back + 0.85 * _up)             # across the wing: to the back edge, turned so the wing
THIN = unit(np.cross(SPAN, CHORD))                  # shows its face from the front too; THIN: its thin direction
# (distance along the span, width across, thickness, how far the wing sweeps back)
WING = [(0.0, 0.80, 0.16, 0.0), (0.7, 1.15, 0.14, 0.06), (1.5, 1.25, 0.12, 0.16), (2.2, 0.90, 0.10, 0.32)]

# Tail feathers: from inside the body back, then sweeping up. (y, height, width, thickness)
FEATHER = [(0.45, 1.05, 0.34, 0.10), (1.00, 0.82, 0.44, 0.09), (1.60, 0.78, 0.46, 0.09), (2.10, 1.02, 0.40, 0.08),
           (2.40, 1.40, 0.30, 0.07)]
FEATHER_ROOT = (0, 0.45, 1.05)
FEATHER_ANGLES = (-26, 0, 26)          # the three tail feathers fan out sideways


def by_length(root, direction, near, far):
    """red close to root, then orange, then yellow (the colors of fire), measured along direction."""
    def paint(c, n):
        d = np.dot(np.asarray(c) - root, direction) if direction is not None else np.linalg.norm(c - root)
        return "red" if d < near else ("orange" if d < far else "yellow")
    return paint


def feather_rings():
    """Rings of one tail feather, each standing across the feather where it is (the feather bends upward)."""
    pts = [np.array([0, y, z]) for y, z, _, _ in FEATHER]
    rings = []
    for i, (_, _, w, t) in enumerate(FEATHER):
        along = unit(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        rings.append(square(pts[i], X, unit(np.cross(X, along)), w, t))
    return rings, unit(pts[-1] - pts[-2])


def build_body():
    body = Part("Body")
    # Body: an upright egg, the chest pushed forward. (height, forward/back, width, depth, corner)
    rings = [(0.95, 0.22, 0.66, 0.74, 0.20),
             (1.20, 0.12, 1.04, 1.06, 0.30),
             (1.70, -0.02, 1.14, 1.10, 0.32),           # chest
             (2.20, -0.14, 0.96, 0.92, 0.28),
             (2.52, -0.24, 0.70, 0.68, 0.20)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings],
         lambda c, n: "orange" if n[1] < -0.5 or n[2] < -0.5 else "red")
    rings = [(2.40, -0.24, 0.66, 0.64, 0.19), (2.85, -0.38, 0.56, 0.54, 0.16), (3.10, -0.44, 0.52, 0.50, 0.15)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], "red")

    # Head, with golden rings around the eyes and a hooked golden beak.
    rings = [(-0.18, 3.22, 0.62, 0.60, 0.19, 0.17), (-0.40, 3.26, 0.72, 0.68, 0.22, 0.20),
             (-0.72, 3.20, 0.60, 0.54, 0.18, 0.16)]
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, "red")
    eyes(body, head[1], head[2], -0.56, 3.22, w=0.16, h=0.16, rim="eyering")
    beak = [square((0, -0.66, 3.16), X, Z, 0.30, 0.26), square((0, -0.90, 3.10), X, Z, 0.22, 0.18)]
    loft(body, beak, "beak", caps=(True, False), tip=(0, -1.08, 2.94))

    # Three long tail feathers, fanning out behind: red, then orange, then yellow at the end.
    rings, _ = feather_rings()
    for angle in FEATHER_ANGLES:
        loft(body, turn(rings, FEATHER_ROOT, Z, angle), by_length(np.array(FEATHER_ROOT), None, 0.8, 1.6))
    return body


def build_crest():
    part = Part("Crest")
    for x, base_y, tip in ((0, -0.42, (0, 0.0, 4.25)), (0.16, -0.36, (0.40, 0.10, 4.02)),
                           (-0.16, -0.36, (-0.40, 0.10, 4.02))):
        loft(part, [square((x, base_y, 3.50), X, Y, 0.18, 0.18)], "flame", caps=(True, False), tip=tip)
    return centered(part)


def build_tail_flames():
    part = Part("TailFlames")
    rings, end = feather_rings()
    last = np.mean(rings[-1], 0)
    base = [p - end * 0.05 for p in rings[-1]]
    for angle in FEATHER_ANGLES:
        tip = turn([[last + end * 0.6]], FEATHER_ROOT, Z, angle)[0][0]
        loft(part, turn([base], FEATHER_ROOT, Z, angle), "flame", caps=(True, False), tip=tip)
    return centered(part)


def wing_point(dist, across=0.0):
    return SHOULDER + SPAN * dist + CHORD * across


def build_wing(name, sign):
    rings = [square(wing_point(d, sweep), CHORD, THIN, width, thick) for d, width, thick, sweep in WING]
    if sign < 0:
        rings = [mirror(r) for r in rings]
    part = Part(name, origin=SHOULDER * (sign, 1, 1))
    root, span = SHOULDER * (sign, 1, 1), SPAN * (sign, 1, 1)
    loft(part, rings, by_length(root, span, 0.6, 1.45))
    return part


def build_wing_flames(name, wing, sign):
    """Flame feathers at the tip and along the back edge of a wing."""
    part = Part(name, parent=wing)
    flames = []
    for k in (-1, 0, 1):                                 # three fingers of fire at the tip
        base = wing_point(2.05, 0.32 + k * 0.3)
        flames.append((base, base + unit(SPAN + CHORD * k * 0.35) * 0.8, CHORD, 0.24))
    for d in (0.8, 1.45):                                # two flames trailing from the back edge
        base = wing_point(d, 0.55)
        flames.append((base, base + unit(CHORD - SPAN * 0.2 - Z * 0.3) * 0.55, SPAN, 0.2))
    for base, tip, across, size in flames:
        pts = [square(base, across, THIN, size, 0.08)]
        if sign < 0:
            pts, tip = [mirror(pts[0])], mirror([tip])[0]
        loft(part, pts, "flame", caps=(True, False), tip=tip)
    return centered(part)


def parts():
    """Body, wings, legs and flames, SIZE times as big. The phoenix faces -y; its left is +x."""
    legs = lambda c, n: "gold"
    return scaled([build_body(), build_wing("WingL", 1), build_wing("WingR", -1),
                   leg("LegL", 0.26, 0.10, 1.0, LEG, legs), leg("LegR", -0.26, 0.10, 1.0, LEG, legs),
                   build_wing_flames("WingFlameL", "WingL", 1), build_wing_flames("WingFlameR", "WingR", -1),
                   build_crest(), build_tail_flames()], SIZE)


PHOENIX = Animal(
    "Phoenix", "Mythic", PALETTE, GOLDEN, parts, close=((0.4, -0.6, 3.9), 5.5), no_studs=NO_STUDS,
    glow={"Crest": FLAME, "TailFlames": FLAME, "WingFlameL": FLAME, "WingFlameR": FLAME},
    effects=[effect("TailFire", "TailFlames", "Fire", "#ff8c1a", "#ff3b1f", rate=14, size=(1.1, 0),
                    lifetime=(0.4, 0.7), speed=(1.5, 2.5), spread=25),
             effect("WingFire", "WingFlameL", "Fire", "#ffb21a", "#ff3b1f", rate=8, size=(0.9, 0),
                    lifetime=(0.3, 0.6), speed=(1, 2), spread=25),
             effect("WingFire", "WingFlameR", "Fire", "#ffb21a", "#ff3b1f", rate=8, size=(0.9, 0),
                    lifetime=(0.3, 0.6), speed=(1, 2), spread=25),
             effect("Embers", "Body", "Sparkles", "#ffd23f", "#ff3b1f", rate=8, size=(0.4, 0), speed=(0.5, 1.5),
                    accel=(0, 3, 0))],
    light=("Body", "#ff8c1a", 1.8, 18))

if __name__ == "__main__":
    build(PHOENIX)
