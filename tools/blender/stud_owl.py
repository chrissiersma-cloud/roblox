"""The Owl: low-poly, with classic Roblox studs painted in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_owl.py [out_dir]           (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.

The owl stands upright, so its parts are different from the four-legged animals: Body (with head, ear tufts,
beak and tail), the wings WingL and WingR (they turn around the shoulder) and the legs LegL and LegR.
"""

import numpy as np

from stud_animal import X, Y, Z, Animal, Part, build, leg, loft, newell, ring, sides, slab, square, unit

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#8b6a4b", "light": "#eee2c9", "dark": "#5e4531", "feet": "#e39a2e", "iris": "#f2b52c",
           "beak": "#e39a2e", "eye": "#161211", "glint": "#ffffff"}
GOLDEN = {"brown": "#e6ac2e", "light": "#fff3c4", "dark": "#b8801a", "feet": "#c98a1a", "iris": "#ff9a3c",
          "beak": "#c98a1a", "eye": "#161211", "glint": "#ffffff"}
NO_STUDS = ("iris", "beak", "eye", "glint")

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
LEG = [(0.62, 0.00, 0.30, 0.32, 0.08),
       (0.28, 0.00, 0.26, 0.28, 0.07),
       (0.12, -0.10, 0.36, 0.52, 0.08),            # foot, toes forward
       (0.00, -0.12, 0.38, 0.56, 0.08)]
# Wings, from the shoulder down: (height, x, y, width, depth, corner).
WING = [(1.88, 0.60, 0.08, 0.20, 0.62, 0.06),
        (1.50, 0.70, 0.10, 0.24, 0.84, 0.07),
        (0.95, 0.68, 0.16, 0.20, 0.80, 0.06),
        (0.55, 0.60, 0.26, 0.14, 0.50, 0.04)]


def body_paint(c, n):
    return "light" if n[1] < -0.6 else "brown"         # light chest


def head_paint(c, n):
    return "light" if n[1] < -0.6 else "brown"         # light face


def leg_paint(c, n):
    return "feet" if c[2] < 0.14 else "light"          # feathered legs, yellow feet


def front_point(ring_a, ring_b, x, z):
    """Point with the given x and z on the front face between two level rings, and the face's normal."""
    pts = [ring_a[6], ring_a[7], ring_b[7], ring_b[6]]
    n = unit(newell(pts))
    n = n if n[1] < 0 else -n
    p0 = pts[0]
    y = p0[1] - (n[0] * (x - p0[0]) + n[2] * (z - p0[2])) / n[1]
    return np.array([x, y, z]), n


def build_body():
    body = Part("Body")
    # Body: an upright egg, level rings from the bottom up. (height, forward/back, width, depth, corner)
    rings = [(0.42, 0.05, 0.80, 0.70, 0.22),
             (0.60, 0.02, 1.16, 1.00, 0.32),
             (1.10, 0.00, 1.30, 1.10, 0.36),            # belly
             (1.60, 0.02, 1.20, 1.02, 0.34),
             (1.90, 0.04, 1.02, 0.90, 0.30)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], body_paint)

    # Head: big and boxy, with a flat face.
    rings = [(1.82, 0.02, 1.08, 0.94, 0.30),
             (2.05, 0.00, 1.34, 1.08, 0.36),            # widest
             (2.45, 0.02, 1.30, 1.04, 0.34),
             (2.66, 0.06, 1.02, 0.84, 0.26)]
    head = [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings]
    loft(body, head, head_paint)

    # Big round eyes on the face: yellow, a black pupil and a white glint. The beak points down between them.
    for x in (0.3, -0.3):
        p, n = front_point(head[1], head[2], x, 2.26)
        slab(body, p, n, 0.36, 0.36, 0.02, "iris", corner=0.1)
        slab(body, p + n * 0.02, n, 0.18, 0.2, 0.02, "eye", corner=0.05)
        slab(body, p + (x * 0.2, 0, 0.06) + n * 0.04, n, 0.07, 0.07, 0.015, "glint")
    p, n = front_point(head[1], head[2], 0, 2.12)
    loft(body, [square(p - n * 0.04, X, Z, 0.2, 0.18)], "beak", caps=(True, False), tip=p + n * 0.2 - Z * 0.14)

    # Ear tufts on the top corners of the head.
    out = unit(np.array([0.4, 0.1, 1.0]))
    flat = unit(-Y - np.dot(-Y, out) * out)            # the thin direction of the tuft
    across = unit(np.cross(out, flat))
    base = np.array([0.44, 0.0, 2.56])
    for pts, tip in sides([square(base, across, flat, 0.28, 0.12)], base + out * 0.38):
        loft(body, pts, "brown", caps=(True, False), tip=tip)

    # Tail: a short, flat fan of feathers at the back.
    tail = [square((0, 0.36, 0.64), X, Z, 0.50, 0.14), square((0, 0.64, 0.50), X, Z, 0.56, 0.10)]
    loft(body, tail, "dark")
    return body


def wing(name, sign):
    part = Part(name, origin=(sign * WING[0][1], WING[0][2] - 0.02, WING[0][0] - 0.03))
    loft(part, [ring((sign * x, y, z), X, Y, w, d, c) for z, x, y, w, d, c in WING], "dark")
    return part


def parts():
    """Body, the wings and the legs. The owl's left side is +x (it faces -y)."""
    return [build_body(), wing("WingL", 1), wing("WingR", -1),
            leg("LegL", 0.28, 0.0, 0.55, LEG, leg_paint), leg("LegR", -0.28, 0.0, 0.55, LEG, leg_paint)]


OWL = Animal("Owl", "Rare", PALETTE, GOLDEN, parts, close=((0.2, -0.3, 2.1), 3.4), no_studs=NO_STUDS)

if __name__ == "__main__":
    build(OWL)
