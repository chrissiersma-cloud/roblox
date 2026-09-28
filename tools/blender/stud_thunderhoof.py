"""Thunderhoof (Legendary): a big white stag with glowing lightning-bolt antlers and a glowing blue mane,
blocky and built from chunky bevelled blocks, with Roblox studs in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_thunderhoof.py [out_dir]   (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import X, Animal, Part, bar, block, build, cartoon_eye, centered, effect, rotation, wedge

BOLT, MANE = "#ffe23a", "#46d2ff"     # glow colors (Neon in Roblox)
# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"white": "#f3f7ff", "blue": "#bcd7ff", "cyan": "#8fe3ff", "hoof": "#ffd84a", "nose": "#3a4766",
           "eyewhite": "#ffffff", "eye": "#1f5fe0", "glint": "#ffffff", "bolt": BOLT, "mane": MANE}
GOLDEN = {**PALETTE, "white": "#f2c037", "blue": "#ffe38a", "cyan": "#fff0a0", "hoof": "#fff6d2",
          "nose": "#6a4410"}
NO_STUDS = ("nose", "eye", "eyewhite", "glint", "bolt", "mane")

LEG_TOP = 3.0
NECK = np.array([0, -1.78, 4.55])      # middle of the neck, which leans forward by NECK_TILT degrees
NECK_TILT = 28


def paint(down="blue", front=None, color="white"):
    def f(c, n):
        if down and n[2] < -0.5:
            return down
        if front and n[1] < -0.5:
            return front
        return color
    return f


def build_body():
    body = Part("Body")
    block(body, (0, 0.25, 3.35), (1.8, 3.7, 1.66), paint(), bevel=0.24)                    # body
    block(body, (0, -1.4, 3.5), (1.72, 1.2, 1.82), paint(front="blue"), bevel=0.24)        # chest
    block(body, NECK, (0.98, 0.95, 1.8), paint(front="blue"), rot=(NECK_TILT, 0, 0), bevel=0.15)
    block(body, (0, -2.2, 5.62), (1.28, 1.35, 1.1), paint(), bevel=0.2)                    # head
    block(body, (0, -3.1, 5.4), (0.9, 0.72, 1.0), paint(), rot=(90, 0, 0), taper=(0.86, 0.86), bevel=0.12)
    block(body, (0, -3.63, 5.55), (0.44, 0.12, 0.26), "nose", bevel=0.04)
    for s in (1, -1):
        cartoon_eye(body, (0.64 * s, -2.45, 5.74), X * s, size=0.4, look=(-0.12 * s, 0.0), brow="blue",
                    tilt=15 * s)
        block(body, (0.88 * s, -2.0, 5.98), (0.7, 0.18, 0.36), paint(down=None, front="cyan"),
              rot=(0, -25 * s, 0), bevel=0.06)                                            # ear
    block(body, (0, 2.12, 3.85), (0.5, 0.42, 0.7), paint(), rot=(-35, 0, 0), bevel=0.1)    # tail
    return body


def zigzag(part, points, size, side=None):
    for p, q in zip(points, points[1:]):
        bar(part, p, q, size, "bolt", bevel=0.04, side=side, over=size[0] / 2)


def build_lightning():
    """Glowing lightning bolts: the antlers, one on each flank and one out of the tail."""
    part = Part("Lightning")
    for s in (1, -1):
        m = np.array([s, 1, 1])
        zigzag(part, [m * p for p in ((0.35, -2.1, 6.0), (0.62, -2.05, 6.75), (0.42, -2.1, 7.0),
                                      (0.8, -2.15, 7.8))], (0.26, 0.26))
        zigzag(part, [m * p for p in ((0.55, -2.06, 6.6), (1.05, -2.0, 6.95), (0.95, -2.02, 7.1),
                                      (1.35, -2.0, 7.45))], (0.2, 0.2))
        flank = [m * p for p in ((0.92, -0.45, 3.95), (0.92, 0.05, 3.45), (0.92, -0.15, 3.38),
                                 (0.92, 0.35, 2.85))]
        for p, q in zip(flank, flank[1:]):
            bar(part, p, q, (0.2, 0.08), "bolt", bevel=0.02, side=np.cross(X, q - p), over=0.1)
    zigzag(part, [(0, 2.35, 4.15), (0, 2.75, 4.5), (0, 2.62, 4.62), (0, 3.05, 5.05)], (0.22, 0.22))
    return centered(part)


def build_mane():
    """A glowing blue mane of spikes down the back of the neck, and a forelock."""
    part = Part("Mane")
    turn_ = rotation((NECK_TILT, 0, 0))
    up, back = turn_[:, 2], turn_[:, 1]
    for t in (-0.7, -0.3, 0.1, 0.5):
        base = NECK + up * t + back * 0.3
        bar(part, base, base + back * 0.75 + up * 0.22, (0.36, 0.3), "mane", bevel=0.04, taper=0.3)
    wedge(part, (0, -2.55, 6.1), (0.4, 0.4), (0, -2.95, 6.5), "mane")
    return centered(part)


def leg(name, x, y, hind):
    part = Part(name, origin=(x, y, LEG_TOP))
    if hind:
        block(part, (x, y + 0.05, 2.5), (0.74, 1.05, 1.3), "white", bevel=0.14)            # thigh
    block(part, (x, y, 2.2 if not hind else 1.9), (0.62, 0.7, 1.5 if not hind else 1.0), "white", bevel=0.1)
    block(part, (x, y, 0.95), (0.48, 0.52, 1.2), "blue", bevel=0.08)
    block(part, (x, y - 0.03, 0.2), (0.6, 0.66, 0.4), "hoof", bevel=0.08)               # golden hoof
    return part


def parts():
    """Body, the four legs and the glowing parts. Thunderhoof's left side is +x (it faces -y)."""
    return [build_body(), leg("LegFL", 0.55, -1.3, False), leg("LegFR", -0.55, -1.3, False),
            leg("LegBL", 0.58, 1.5, True), leg("LegBR", -0.58, 1.5, True), build_lightning(), build_mane()]


THUNDERHOOF = Animal(
    "Thunderhoof", "Legendary", PALETTE, GOLDEN, parts, close=((0.35, -2.3, 5.6), 9.0), no_studs=NO_STUDS,
    glow={"Lightning": BOLT, "Mane": MANE},
    effects=[effect("Sparks", "Lightning", "Sparkles", BOLT, "#ffffff", rate=8, size=(0.5, 0), lifetime=(0.2, 0.5),
                    speed=(3, 6))]
    # small sparks from every hoof, so it crackles when it walks
    + [effect("HoofSparks", leg, "Sparkles", BOLT, "#ffffff", rate=3, size=(0.3, 0), lifetime=(0.15, 0.35),
              speed=(1.5, 3), accel=(0, -4, 0), at="bottom") for leg in ("LegFL", "LegFR", "LegBL", "LegBR")],
    light=("Lightning", "#9fe6ff", 1.5, 14))

if __name__ == "__main__":
    build(THUNDERHOOF)
