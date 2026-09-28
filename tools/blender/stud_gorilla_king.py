"""The Gorilla King (Secret): a dripped-out gorilla with a glowing golden crown, gold grills with diamond teeth,
a thick gold chain with a diamond medallion, a gold earring and gold bracelets with diamonds. Blocky, built
from chunky bevelled blocks, with Roblox studs in its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_gorilla_king.py [out_dir]  (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import Y, Animal, Part, bar, block, build, cartoon_eye, centered, effect, slab, wedge

CROWN = "#ffd23a"                     # glow color (Neon in Roblox)
# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"fur": "#2c2a33", "silver": "#aeb2bd", "skin": "#5e5462", "gold": "#f2c037", "ruby": "#e0183a",
           "diamond": "#dff6ff", "black": "#120c10", "eyewhite": "#ffb020", "eye": "#120c10", "glint": "#ffffff",
           "crown": CROWN}
GOLDEN = {**PALETTE, "fur": "#e6ac2e", "silver": "#fff0a0", "skin": "#c98a1a"}
NO_STUDS = ("gold", "ruby", "diamond", "black", "eye", "eyewhite", "glint", "crown")

TORSO_TILT = -15                      # the torso leans back: shoulders high, hips low (knuckle walking)
HEAD = np.array([0, -1.4, 3.95])      # middle of the head
HEAD_SIZE = np.array([1.3, 1.15, 1.2])


def front(color, other="fur"):
    return lambda c, n: color if n[1] < -0.5 else other


def build_body():
    body = Part("Body")
    block(body, (0, 0.25, 2.55), (2.1, 2.3, 1.8), lambda c, n: "silver" if n[2] > 0.8 else "fur",
          rot=(TORSO_TILT, 0, 0), bevel=0.28)                                            # torso, silver back
    block(body, (0, -0.95, 2.75), (1.8, 0.8, 1.5), front("skin"), bevel=0.22)            # chest
    block(body, HEAD, HEAD_SIZE, "fur", bevel=0.2)                                        # head
    block(body, (0, -2.0, 3.85), (1.02, 0.1, 0.95), "skin", bevel=0.04)                   # face
    block(body, (0, -2.08, 4.22), (1.1, 0.28, 0.22), "fur", bevel=0.06)                   # heavy brow
    block(body, (0, -2.2, 3.55), (0.86, 0.42, 0.52), "skin", bevel=0.1)                   # muzzle
    for s in (1, -1):
        slab(body, (0.13 * s, -2.41, 3.7), -Y, 0.13, 0.08, 0.02, "black")                 # nostril
        cartoon_eye(body, (0.24 * s, -2.05, 4.0), -Y, size=0.24, look=(0.0, 0.08))
        block(body, (0.68 * s, -1.45, 3.95), (0.12, 0.32, 0.38), "skin", bevel=0.04)      # ear
    return body


def build_crown():
    """A glowing golden crown with points and rubies."""
    part = Part("Crown")
    x, y0, y1, z = 0.7, -2.02, -0.78, 4.66
    block(part, (0, y0, z), (1.46, 0.12, 0.36), "crown", bevel=0.03)
    block(part, (0, y1, z), (1.46, 0.12, 0.36), "crown", bevel=0.03)
    for s in (1, -1):
        block(part, (x * s, (y0 + y1) / 2, z), (0.12, 1.36, 0.36), "crown", bevel=0.03)
    for px in (-x + 0.06, 0.0, x - 0.06):
        for py in (y0 + 0.06, y1 - 0.06):
            wedge(part, (px, py, z + 0.15), (0.2, 0.12), (px, py, z + 0.62), "crown")
    for s in (1, -1):
        wedge(part, (x * s - 0.06 * s, (y0 + y1) / 2, z + 0.15), (0.12, 0.2), (x * s, (y0 + y1) / 2, z + 0.62),
              "crown")
    for px in (-0.45, 0.0, 0.45):
        slab(part, (px, y0 - 0.06, z), -Y, 0.14, 0.14, 0.03, "ruby")
    return centered(part)


def build_chains():
    """A thick gold chain hanging in a V over the chest, a medallion with a diamond, and a gold earring."""
    part = Part("Chains")
    for s in (1, -1):
        pts = np.linspace((0.62 * s, -1.4, 3.35), (0.0, -1.42, 2.62), 6)
        for i, (p, q) in enumerate(zip(pts, pts[1:])):
            d = q - p
            bar(part, p, q, (0.2, 0.1) if i % 2 else (0.1, 0.2), "gold", bevel=0.02, side=np.cross(Y, d),
                over=0.03)                                                               # chain links
    block(part, (0, -1.43, 2.33), (0.64, 0.12, 0.64), "gold", bevel=0.06)                 # medallion
    block(part, (0, -1.52, 2.33), (0.3, 0.08, 0.3), "diamond", rot=(0, 45, 0), bevel=0.02)
    block(part, (0.76, -1.45, 3.72), (0.06, 0.18, 0.18), "gold", bevel=0.02)             # earring
    return centered(part)


def build_grills():
    """Gold grills with diamond teeth on the front of the muzzle."""
    part = Part("Grills")
    block(part, (0, -2.43, 3.42), (0.64, 0.05, 0.18), "gold", bevel=0.02)
    for x in (-0.22, -0.075, 0.075, 0.22):
        slab(part, (x, -2.46, 3.42), -Y, 0.1, 0.12, 0.02, "diamond")
    return centered(part)


def arm(name, s):
    x = 1.2 * s
    part = Part(name, origin=(1.1 * s, -0.75, 3.3))
    block(part, (1.18 * s, -0.9, 2.6), (0.8, 0.86, 1.5), "fur", bevel=0.16)              # upper arm
    block(part, (x, -1.05, 1.3), (0.74, 0.8, 1.3), "fur", bevel=0.14)                    # forearm
    block(part, (x, -1.12, 0.33), (0.86, 0.92, 0.66), "skin", bevel=0.14)                # big fist
    for dx in (-0.24, 0.0, 0.24):
        block(part, (x + dx, -1.6, 0.22), (0.2, 0.14, 0.3), "skin", bevel=0.05)          # knuckles
    return part


def bracelet(name, arm_name, s):
    """A gold bracelet with diamonds around the lower arm."""
    x = 1.2 * s
    part = Part(name, parent=arm_name)
    for y, w, d in ((-1.49, 0.86, 0.08), (-0.61, 0.86, 0.08)):
        block(part, (x, y, 0.92), (w, d, 0.24), "gold", bevel=0.02)
    for sx in (1, -1):
        block(part, (x + 0.42 * sx, -1.05, 0.92), (0.08, 0.9, 0.24), "gold", bevel=0.02)
    for dx in (-0.25, 0.0, 0.25):
        slab(part, (x + dx, -1.53, 0.92), -Y, 0.1, 0.1, 0.02, "diamond")
    return centered(part)


def leg(name, s):
    x = 0.75 * s
    part = Part(name, origin=(0.72 * s, 0.95, 1.7))
    block(part, (x, 1.0, 1.15), (0.8, 0.95, 1.2), "fur", bevel=0.16)                     # thigh
    block(part, (x, 0.9, 0.55), (0.66, 0.74, 0.7), "fur", bevel=0.12)                    # shin
    block(part, (x, 0.75, 0.2), (0.76, 1.2, 0.4), "skin", bevel=0.1)                    # foot
    return part


def parts():
    """Body, arms (LegFL, LegFR), legs (LegBL, LegBR) and the bling. The gorilla faces -y; its left is +x."""
    return [build_body(), arm("LegFL", 1), arm("LegFR", -1), leg("LegBL", 1), leg("LegBR", -1),
            build_crown(), build_chains(), build_grills(),
            bracelet("BraceletL", "LegFL", 1), bracelet("BraceletR", "LegFR", -1)]


GORILLA_KING = Animal(
    "GorillaKing", "Secret", PALETTE, GOLDEN, parts, close=((0.4, -1.8, 3.6), 7.0), no_studs=NO_STUDS,
    display="Gorilla King",
    glow={"Crown": CROWN}, shine={"Chains": 0.35, "Grills": 0.4, "BraceletL": 0.35, "BraceletR": 0.35},
    effects=[effect("CrownSparkles", "Crown", "Sparkles", CROWN, "#ffffff", rate=5, size=(0.4, 0), speed=(0.3, 0.8)),
             effect("GoldSparkles", "Chains", "Sparkles", CROWN, rate=4, size=(0.3, 0), speed=(0.2, 0.5)),
             effect("GrillShine", "Grills", "Sparkles", "#ffffff", "#bfefff", rate=2, size=(0.25, 0),
                    lifetime=(0.3, 0.6), speed=(0.1, 0.3)),
             effect("BraceletSparkles", "BraceletL", "Sparkles", CROWN, rate=2, size=(0.25, 0), speed=(0.1, 0.4)),
             effect("BraceletSparkles", "BraceletR", "Sparkles", CROWN, rate=2, size=(0.25, 0), speed=(0.1, 0.4))],
    light=("Crown", CROWN, 1.2, 12))

if __name__ == "__main__":
    build(GORILLA_KING)
