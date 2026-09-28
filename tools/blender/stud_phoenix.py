"""The Phoenix (Mythic): a bird of fire with burning wings, low-poly with Roblox studs (see stud_animal.py).

Run: python3 tools/blender/stud_phoenix.py [out_dir]       (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.

The phoenix stands upright like the owl. Parts: Body (with head, beak, a collar of feathers and the long tail
feathers), the wings WingL and WingR (they turn at the shoulder), the legs LegL and LegR with talons, and the flames
that glow (Neon in Roblox): Crest (the plumes on the head), TailFlames, and WingFlameL / WingFlameR (attached to the
wings, so they move with them).

The shapes use round rings (segs=2) and the studs wrap around them (wrap=True), for a smoother, more detailed look.
"""

import math

import numpy as np

from stud_animal import (X, Y, Z, Animal, Part, build, centered, effect, hit, loft, mirror, ring, scaled, slab,
                         square, turn, unit)

FLAME = "#ffc02e"

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"red": "#e8331f", "orange": "#ff7a1a", "yellow": "#ffc13a", "gold": "#f5b82e", "beak": "#ffd23f",
           "claw": "#2a1a10", "eyering": "#ffd23f", "eye": "#1a0a05", "glint": "#ffffff", "flame": FLAME}
GOLDEN = {**PALETTE, "red": "#e6ac2e", "orange": "#ffd66b", "yellow": "#fff0a0", "gold": "#fff6d2"}
NO_STUDS = ("beak", "claw", "eyering", "eye", "glint", "flame")

SIZE = 1.25                            # the whole phoenix is this many times bigger than the numbers in this file
ROUND = 2                              # corner pieces of the rings: round shapes

# Wings rise up and out from the shoulder.
SHOULDER = np.array([0.44, 0.02, 2.20])
SPAN = unit(np.array([0.85, 0.12, 0.62]))          # from the shoulder to the wing tip
_back, _up = unit(Y - np.dot(Y, SPAN) * SPAN), unit(Z - np.dot(Z, SPAN) * SPAN)
CHORD = unit(0.55 * _back + 0.85 * _up)             # across the wing, turned so it shows its face from the front
THIN = unit(np.cross(SPAN, CHORD))                  # the thin direction of the wing
# The arm of the wing: (distance along the span, width across, thickness, how far it sweeps back)
WING = [(0.0, 0.80, 0.20, 0.0), (0.5, 1.00, 0.18, 0.04), (1.1, 1.05, 0.16, 0.10), (1.6, 0.80, 0.13, 0.20),
        (1.95, 0.45, 0.10, 0.32)]
# Long feathers at the tip: (where along the span, where across, angle from the span towards the back, length)
PRIMARIES = [(1.55, -0.30, -12, 1.05), (1.65, -0.10, 5, 1.15), (1.70, 0.10, 22, 1.15), (1.65, 0.30, 40, 1.0),
             (1.50, 0.45, 58, 0.85)]
# Shorter feathers along the back edge: (where along the span, length)
SECONDARIES = [(0.30, 0.55), (0.70, 0.62), (1.10, 0.66), (1.40, 0.6)]

# Tail feathers: from inside the body back, then sweeping up. (y, height, width, thickness)
FEATHER = [(0.40, 1.05, 0.30, 0.10), (0.95, 0.82, 0.42, 0.09), (1.55, 0.78, 0.46, 0.09), (2.05, 1.02, 0.40, 0.08),
           (2.35, 1.42, 0.28, 0.07)]
FEATHER_ROOT = (0, 0.40, 1.05)
FEATHER_ANGLES = (-34, -17, 0, 17, 34)             # the tail feathers fan out sideways


def fire(root, near, far):
    """red close to root, then orange, then yellow (the colors of fire)."""
    def paint(c, n):
        d = np.linalg.norm(np.asarray(c) - root)
        return "red" if d < near else ("orange" if d < far else "yellow")
    return paint


def feather(part, root, direction, flat, length, width, paint, tip_part=None, thin=0.06):
    """A flat feather from root along direction, widest a third of the way; flat: its thin direction.
    tip_part: also put a flame on its tip in that part."""
    across = unit(np.cross(flat, direction))
    pts = [root + direction * length * f for f in (0.0, 0.35, 0.8)]
    loft(part, [square(p, across, flat, width * s, thin) for p, s in zip(pts, (0.7, 1.0, 0.7))], paint,
         caps=(True, False), tip=root + direction * length)
    if tip_part is not None:
        base = root + direction * length * 0.8
        loft(tip_part, [square(base, across, flat, width * 0.5, thin * 0.8)], "flame", caps=(True, False),
             tip=root + direction * (length + 0.45))


def wing_point(dist, across=0.0):
    return SHOULDER + SPAN * dist + CHORD * across


def build_wing(name, flames_name, sign):
    """A wing and its flames (a separate part, attached to the wing). Built on the left side, then mirrored."""
    wing, flames = Part(name, origin=SHOULDER * (sign, 1, 1)), Part(flames_name, parent=name)
    rings = [ring(wing_point(d, sweep), CHORD, THIN, width, thick, thick * 0.45, segs=ROUND)
             for d, width, thick, sweep in WING]
    loft(wing, rings, fire(SHOULDER, 0.7, 1.5))
    for d, across, angle, length in PRIMARIES:
        t = math.radians(angle)
        feather(wing, wing_point(d, across), unit(SPAN * math.cos(t) + CHORD * math.sin(t)), THIN, length, 0.26,
                fire(SHOULDER, 1.4, 2.1), flames)
    for d, length in SECONDARIES:
        direction = unit(CHORD * 0.85 - SPAN * 0.2 - Z * 0.35)
        feather(wing, wing_point(d, 0.40), direction, THIN, length, 0.24, fire(SHOULDER, 0.9, 1.5),
                flames if d > 1.0 else None)
    if sign < 0:                                        # the mirror image: turn the faces around as well
        for part in (wing, flames):
            part.verts = mirror(part.verts)
            part.faces = [f[::-1] for f in part.faces]
    return wing, centered(flames)


def feather_rings(width_scale=1.0):
    """Rings of one tail feather, each standing across the feather where it is (the feather bends upward)."""
    pts = [np.array([0, y, z]) for y, z, _, _ in FEATHER]
    rings = []
    for i, (_, _, w, t) in enumerate(FEATHER):
        along = unit(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        rings.append(square(pts[i], X, unit(np.cross(X, along)), w * width_scale, t))
    return rings, unit(pts[-1] - pts[-2])


def build_body():
    body = Part("Body")
    # Body: an upright egg with a full chest. (height, forward/back, width, depth, corner)
    rings = [(0.92, 0.26, 0.56, 0.62, 0.22), (1.05, 0.18, 0.86, 0.92, 0.34), (1.30, 0.08, 1.06, 1.08, 0.42),
             (1.62, -0.02, 1.14, 1.12, 0.44), (1.95, -0.10, 1.06, 1.02, 0.40), (2.22, -0.18, 0.88, 0.84, 0.34),
             (2.45, -0.24, 0.66, 0.64, 0.26)]
    loft(body, [ring((0, y, z), X, Y, w, d, c, segs=ROUND) for z, y, w, d, c in rings],
         lambda c, n: "orange" if n[1] < -0.45 or n[2] < -0.5 else "red")
    rings = [(2.40, -0.24, 0.62, 0.60, 0.24), (2.70, -0.34, 0.54, 0.52, 0.21), (2.98, -0.42, 0.50, 0.48, 0.19),
             (3.12, -0.44, 0.48, 0.46, 0.18)]
    loft(body, [ring((0, y, z), X, Y, w, d, c, segs=ROUND) for z, y, w, d, c in rings],
         lambda c, n: "orange" if n[1] < -0.45 else "red")

    # A collar of flame feathers around the bottom of the neck.
    for k in range(10):
        t = 2 * math.pi * k / 10
        out = np.array([math.sin(t), -math.cos(t), 0.0])
        root = np.array([0, -0.26, 2.42]) + out * np.array([0.28, 0.27, 0])
        direction = unit(out - Z * 0.55)
        feather(body, root, direction, unit(np.cross(direction, Z)), 0.42, 0.2, fire(root, 0.12, 0.3))

    # Head, with golden rings around the eyes and a hooked golden beak.
    rings = [(-0.14, 3.24, 0.50, 0.50, 0.19, 0.17), (-0.26, 3.28, 0.66, 0.64, 0.26, 0.23),
             (-0.44, 3.30, 0.72, 0.68, 0.28, 0.25), (-0.62, 3.26, 0.66, 0.60, 0.25, 0.22),
             (-0.76, 3.20, 0.52, 0.46, 0.19, 0.17)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb, segs=ROUND) for y, zc, w, h, c, cb in rings], "red")
    for s in (1, -1):
        p, n = hit(body, (s * 2, -0.52, 3.31), -X * s)
        slab(body, p, n, 0.22, 0.2, 0.015, "eyering", corner=0.08, segs=ROUND)
        slab(body, p + n * 0.015, n, 0.13, 0.14, 0.02, "eye", corner=0.05, segs=ROUND)
        slab(body, p + n * 0.035 + (0, -0.03, 0.03), n, 0.04, 0.04, 0.01, "glint")
    beak = [ring((0, y, z), X, Z, w, h, h * 0.35, segs=ROUND)
            for y, z, w, h in ((-0.70, 3.18, 0.30, 0.22), (-0.88, 3.14, 0.24, 0.17), (-1.00, 3.08, 0.16, 0.12))]
    loft(body, beak, "beak", caps=(True, False), tip=(0, -1.08, 2.94))
    loft(body, [square((0, -0.70, 3.03), X, Z, 0.22, 0.1)], "beak", caps=(True, False), tip=(0, -0.92, 3.0))

    # Tail: long feathers fanning out behind and sweeping up, red to yellow; the outer ones a bit narrower.
    for angle in FEATHER_ANGLES:
        rings, _ = feather_rings(1.0 if abs(angle) < 20 else 0.85)
        loft(body, turn(rings, FEATHER_ROOT, Z, angle), fire(np.array(FEATHER_ROOT), 0.8, 1.6))
    return body


def build_crest():
    part = Part("Crest")
    # Five flame plumes on the head, streaming back.
    for x, length in ((0, 1.0), (0.13, 0.85), (-0.13, 0.85), (0.25, 0.68), (-0.25, 0.68)):
        root = np.array([x, -0.46, 3.52])
        direction = unit(np.array([x * 1.2, 0.75, 0.62]))
        across = unit(np.cross(direction, Y if abs(x) > 0.2 else X))
        flat = unit(np.cross(direction, across))
        pts = [root, root + direction * length * 0.4]
        loft(part, [square(p, across, flat, s, 0.1) for p, s in zip(pts, (0.14, 0.2))], "flame", caps=(True, False),
             tip=root + direction * length + Z * 0.08)
    return centered(part)


def build_tail_flames():
    part = Part("TailFlames")
    for angle in FEATHER_ANGLES:
        rings, end = feather_rings(1.0 if abs(angle) < 20 else 0.85)
        last = np.mean(rings[-1], 0)
        base = [p - end * 0.05 for p in rings[-1]]
        tip = turn([[last + end * 0.65]], FEATHER_ROOT, Z, angle)[0][0]
        loft(part, turn([base], FEATHER_ROOT, Z, angle), "flame", caps=(True, False), tip=tip)
    return centered(part)


def bird_leg(name, x):
    """A golden leg with three talons forward and one back."""
    part = Part(name, origin=(x, 0.10, 1.0))
    rings = [(1.12, 0.00, 0.34, 0.36, 0.14), (0.80, 0.02, 0.30, 0.32, 0.12), (0.45, 0.02, 0.18, 0.20, 0.07),
             (0.14, -0.02, 0.20, 0.22, 0.08), (0.06, -0.02, 0.24, 0.26, 0.09)]
    loft(part, [ring((x, 0.10 + dy, z), X, Y, w, d, c, segs=ROUND) for z, dy, w, d, c in rings], "gold")
    for dx, direction in ((-0.1, (-0.35, -1, 0)), (0, (0, -1, 0)), (0.1, (0.35, -1, 0)), (0, (0, 1, 0))):
        d = unit(np.array(direction, float))
        root = np.array([x + dx, 0.08, 0.04])
        side = unit(np.cross(Z, d))
        toe = [square(root, side, Z, 0.09, 0.08), square(root + d * 0.22, side, Z, 0.08, 0.07)]
        loft(part, toe, "gold")
        loft(part, [square(root + d * 0.2, side, Z, 0.07, 0.06)], "claw", caps=(True, False),
             tip=root + d * 0.34 - Z * 0.04)
    return part


def parts():
    """Body, wings, legs and flames, SIZE times as big. The phoenix faces -y; its left is +x."""
    wing_l, flames_l = build_wing("WingL", "WingFlameL", 1)
    wing_r, flames_r = build_wing("WingR", "WingFlameR", -1)
    return scaled([build_body(), wing_l, wing_r, bird_leg("LegL", 0.26), bird_leg("LegR", -0.26),
                   flames_l, flames_r, build_crest(), build_tail_flames()], SIZE)


PHOENIX = Animal(
    "Phoenix", "Mythic", PALETTE, GOLDEN, parts, close=((0.4, -0.6, 3.9), 5.5), no_studs=NO_STUDS, wrap=True,
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
