#!/usr/bin/env python3
"""Forest entrance: a detailed covered wagon, a log archway with a hanging "To the Forest" sign, a signpost,
a campfire and cargo, built from Parts in the style of the Wrangler Camp statue.

The path runs along Z: players come from +Z (the camp) and walk towards -Z into the forest. The origin is the
middle of the path at the entrance. Every piece is its own Model, so you can move or delete them separately.

    python3 tools/forest-entrance/build_entrance.py                  -> build/entrance.json and build/world.json
    python3 tools/forest-entrance/build_entrance.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
"""

import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "animal-models"))
sys.path.insert(0, str(HERE.parent / "statue"))
sys.path.insert(0, str(HERE.parent / "forest-kit"))

from lib import IDENTITY, add, aim, angles, apply, cframe, matmul, scale, sub, unit  # noqa: E402
from build_statue import C, Group, group_instance  # noqa: E402

WOOD = C("#a36a36")
WOOD_DARK = C("#7a4a2a")
WOOD_LIGHT = C("#b97a46")
WOOD_DEEP = C("#5a3418")
IRON = C("#3a3a42")
CANVAS = C("#f3ecd9")
CANVAS2 = C("#e6dcc3")
CUT = C("#e0b276")
STONE = C("#9aa6b8")
STONE_DARK = C("#7e8a9c")
LEAF = [C("#3f9e3a"), C("#58bb43"), C("#74d14c")]
FONT = {"family": "rbxasset://fonts/families/FredokaOne.json", "weight": 400}


def at(base, R, off):
    return add(base, apply(R, off))


def log(g, name, p0, p1, d, color, **kw):
    """Round-ish log between two points: a square beam plus the same beam turned 45 degrees."""
    R = aim(sub(p1, p0))
    mid = scale(add(p0, p1), 0.5)
    length = math.dist(p0, p1)
    g.box(name, (length, d, d), mid, color, R=R, **kw)
    g.box(name, (length * 0.999, d * 0.97, d * 0.97), mid, color, R=matmul(R, angles(45, 0, 0)), **kw)


def tri(g, name, base, width, height, thick, color, R=IDENTITY, **kw):
    """Flat upright triangle (two wedges) standing on `base`, facing Z before R."""
    for sgn in (-1, 1):
        pos = at(base, R, (sgn * width / 4, height / 2, 0))
        g.wedge(name, (thick, height, width / 2), pos, color, R=matmul(R, angles(0, 90 if sgn < 0 else -90, 0)), **kw)


def surface_text(text, face, color="#fff4dc", ppu=60, stroke=None):
    label = {"Size": [1, 0, 1, 0], "BackgroundTransparency": 1, "Text": text, "TextScaled": True,
             "TextColor3": list(C(color)), "FontFace": FONT}
    if stroke:
        label.update(TextStrokeColor3=list(C(stroke)), TextStrokeTransparency=0.2)
    return {"class": "SurfaceGui", "name": f"Text{face}",
            "props": {"Face": face, "SizingMode": "PixelsPerStud", "PixelsPerStud": ppu, "LightInfluence": 0.5},
            "children": [{"class": "TextLabel", "name": "Label", "props": label,
                          "children": [{"class": "UIPadding", "name": "Padding",
                                        "props": {"PaddingLeft": [0.05, 0], "PaddingRight": [0.05, 0],
                                                  "PaddingTop": [0.12, 0], "PaddingBottom": [0.1, 0]}}]}]}


def point_light(color, brightness=1.4, range_=16):
    return {"class": "PointLight", "name": "Glow",
            "props": {"Color": list(C(color)), "Brightness": brightness, "Range": range_, "Shadows": False}}


def lantern(g, name, top, chain=0.8):
    """Hanging lantern: a hook, a short chain, a dark frame and a glowing glass."""
    for i in range(3):
        g.box(f"{name}Chain", (0.12, 0.3, 0.12), add(top, (0, -0.15 - 0.27 * i, 0)), IRON, rot=(0, 45 * (i % 2), 0),
              collide=False)
    y = top[1] - chain - 0.8
    c = (top[0], y, top[2])
    g.box(f"{name}Cap", (0.9, 0.2, 0.9), add(c, (0, 0.72, 0)), IRON, collide=False)
    g.box(f"{name}Cap", (0.5, 0.25, 0.5), add(c, (0, 0.9, 0)), IRON, rot=(0, 45, 0), collide=False)
    g.box(f"{name}Glass", (0.6, 1.0, 0.6), c, C("#ffe7a3"), material="Neon", collide=False, shadow=False,
          children=[point_light("#ffd88a", 1.3, 14)])
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.box(f"{name}Bar", (0.1, 1.1, 0.1), add(c, (0.33 * sx, 0, 0.33 * sz)), IRON, collide=False)
    g.box(f"{name}Base", (0.8, 0.15, 0.8), add(c, (0, -0.58, 0)), IRON, collide=False)


def barrel(g, name, pos, k=1.0):
    r, h = 0.62 * k, 1.5 * k
    g.octagon(name, r, h, add(pos, (0, h / 2, 0)), WOOD)
    for y in (0.3 * k, h - 0.3 * k):
        g.octagon(f"{name}Hoop", r + 0.04, 0.14 * k, add(pos, (0, y, 0)), IRON, collide=False)
    g.octagon(f"{name}Lid", r - 0.1, 0.06, add(pos, (0, h + 0.03, 0)), WOOD_LIGHT, collide=False)


def crate(g, name, pos, size=1.2, yaw=0):
    R = angles(0, yaw, 0)
    s = size
    g.box(name, (s, s, s), add(pos, (0, s / 2, 0)), WOOD_LIGHT, R=R)
    for sgn in (-1, 1):
        for axis in range(2):
            off = [0, 0, 0]
            off[0 if axis == 0 else 2] = sgn * (s / 2 + 0.02)
            size_ = (0.06, s * 0.98, 0.18) if axis == 0 else (0.18, s * 0.98, 0.06)
            g.box(f"{name}Edge", size_, at(add(pos, (0, s / 2, 0)), R, (off[0] + (0 if axis == 0 else sgn * 0), 0,
                                                                          off[2])), WOOD_DARK, R=R, collide=False)
        # Diagonal slat on the front and back faces.
        g.box(f"{name}Slat", (s * 1.3, 0.16, 0.05), at(add(pos, (0, s / 2, 0)), R, (0, 0, sgn * (s / 2 + 0.03))),
              WOOD_DARK, R=matmul(R, angles(0, 0, 45)), collide=False)
    g.box(f"{name}Top", (s * 1.02, 0.1, s * 1.02), add(pos, (0, s + 0.04, 0)), WOOD_DARK, R=R, collide=False)


def sack(g, name, pos, yaw=0):
    R = angles(0, yaw, 0)
    g.box(name, (1.0, 0.9, 0.7), add(pos, (0, 0.45, 0)), C("#d9c39a"), R=R)
    g.box(f"{name}Top", (0.7, 0.3, 0.5), add(pos, (0, 1.0, 0)), C("#cdb487"), R=R)
    g.box(f"{name}Tie", (0.35, 0.15, 0.35), add(pos, (0, 1.2, 0)), WOOD_DEEP, R=R, collide=False)
    g.box(f"{name}Stripe", (1.02, 0.15, 0.72), add(pos, (0, 0.55, 0)), C("#b8844c"), R=R, collide=False)


def wheel(g, name, center, radius, spokes=12):
    """Spoked wagon wheel on an axle along X: iron tire, wooden rim, spokes and a hub."""
    R = angles(0, 0, 90)  # ring normal (local Y) along X
    g.ring(f"{name}Tire", center, R, radius - 0.1, 0.25, [IRON], n=24, twist=False)
    g.ring(f"{name}Rim", center, R, radius - 0.32, 0.3, [WOOD_DARK, WOOD], n=24, twist=False)
    for i in range(spokes):
        t = 2 * math.pi * i / spokes
        tip = add(center, (0, math.sin(t) * (radius - 0.4), math.cos(t) * (radius - 0.4)))
        g.rod(f"{name}Spoke", center, tip, 0.16, WOOD)
    g.cyl(f"{name}Hub", 0.7, 0.75, center, WOOD_DARK)
    g.cyl(f"{name}Cap", 0.8, 0.45, center, IRON)


# ------------------------------------------------------------------ wagon ---

def wagon(g, origin=(0, 0, 0), yaw=0.0):
    """Covered wagon. Front (tongue) points to -Z before `yaw`; built at `origin`."""
    Ry = angles(0, yaw, 0)
    P = lambda x, y, z: add(origin, apply(Ry, (x, y, z)))
    Rw = Ry
    L = 9.4

    # Wheels and undercarriage.
    for z, r, y in ((2.9, 2.0, 2.0), (-2.9, 1.7, 1.7)):
        for sx in (-1, 1):
            wheel(g, "Wheel", P(2.75 * sx, y, z), r)
        g.box("Axle", (5.8, 0.4, 0.4), P(0, y, z), WOOD_DEEP, R=Rw)
        g.box("Bolster", (4.6, 0.45, 0.6), P(0, y + 0.42, z), WOOD_DARK, R=Rw)
    g.box("Reach", (0.35, 0.35, 7.4), P(0, 2.05, 0), WOOD_DEEP, R=Rw)
    # Floor: planks with dark gaps between them.
    g.box("FloorBase", (4.2, 0.26, L), P(0, 2.5, 0), WOOD_DEEP, R=Rw)
    for i in range(7):
        x = -1.8 + 0.6 * i
        g.box("Plank", (0.55, 0.3, L), P(x, 2.66, 0), WOOD if i % 2 else WOOD_LIGHT, R=Rw)
    # Sideboards, stakes, rails and iron brackets.
    for sx in (-1, 1):
        for j, y in enumerate((3.2, 3.9)):
            g.box("Sideboard", (0.25, 0.66, L), P(2.1 * sx, y, 0), WOOD_LIGHT if j else WOOD, R=Rw)
        g.box("Rail", (0.42, 0.22, L + 0.2), P(2.12 * sx, 4.33, 0), WOOD_DARK, R=Rw)
        g.box("Skirt", (0.3, 0.3, L), P(2.12 * sx, 2.55, 0), WOOD_DARK, R=Rw)
        for z in (-4.4, -1.5, 1.5, 4.4):
            g.box("Stake", (0.3, 2.0, 0.32), P(2.33 * sx, 3.35, z), WOOD_DARK, R=Rw)
            g.box("StakeCap", (0.36, 0.2, 0.38), P(2.33 * sx, 4.4, z), IRON, R=Rw)
            g.box("Bracket", (0.34, 0.18, 0.36), P(2.33 * sx, 2.8, z), IRON, R=Rw)
        for z in (-4.65, 4.65):
            g.box("Corner", (0.1, 1.4, 0.3), P(2.24 * sx, 3.55, z), IRON, R=Rw)
    # Front board and a low back tailgate with chains.
    for j, y in enumerate((3.2, 3.9)):
        g.box("FrontBoard", (4.4, 0.66, 0.25), P(0, y, -4.75), WOOD_LIGHT if j else WOOD, R=Rw)
    g.box("Tailgate", (4.4, 0.8, 0.25), P(0, 3.15, 4.75), WOOD, R=Rw)
    g.box("TailgateTrim", (4.5, 0.18, 0.3), P(0, 3.6, 4.75), WOOD_DARK, R=Rw)
    for sx in (-1, 1):
        for i in range(3):
            g.box("TailChain", (0.1, 0.28, 0.1), P(1.95 * sx, 3.75 + 0.25 * i, 4.8), IRON, R=Rw, collide=False)

    # Canvas bonnet: strips around an arch, with wooden bows and flared ends.
    rx, ry, base = 2.35, 3.0, 4.35
    n = 12

    def arc(t, k=1.0):
        return (rx * k * math.cos(t), base + ry * k * math.sin(t))

    for i in range(n):
        t0, t1 = math.pi * i / n, math.pi * (i + 1) / n
        (x0, y0), (x1, y1) = arc(t0), arc(t1)
        tx, ty = x1 - x0, y1 - y0
        width = math.hypot(tx, ty)
        tx, ty = tx / width, ty / width
        # Local X along the arch, Z along the wagon, Y out of the canvas.
        Rl = ((tx, -ty, 0), (ty, tx, 0), (0, 0, 1))
        R = matmul(Ry, Rl)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        g.box("Canvas", (width * 1.06, 0.12, L - 0.8), P(mx, my, 0), CANVAS if i % 2 else CANVAS2, R=R)
        for z in (-3.6, -1.2, 1.2, 3.6):
            (bx0, by0), (bx1, by1) = arc(t0, 1.03), arc(t1, 1.03)
            g.box("Bow", (width * 1.08, 0.14, 0.28), P((bx0 + bx1) / 2, (by0 + by1) / 2, z), WOOD_DARK, R=R,
                  collide=False)
        for sz in (-1, 1):
            # Flared, slightly bigger ends of the bonnet.
            (ex0, ey0), (ex1, ey1) = arc(t0, 1.1), arc(t1, 1.1)
            Rf = matmul(R, angles(-16 * sz, 0, 0))
            g.box("CanvasEnd", (width * 1.14, 0.12, 0.9), P((ex0 + ex1) / 2, (ey0 + ey1) / 2 - 0.05, sz * (L / 2 - 0.1)),
                  CANVAS2 if i % 2 else CANVAS, R=Rf)
            g.box("CanvasHem", (width * 1.16, 0.16, 0.18), P((ex0 + ex1) / 2 * 1.02, (ey0 + ey1) / 2, sz * (L / 2 + 0.3)),
                  WOOD_DARK, R=Rf, collide=False)
    # Rope lashing where the canvas is tied to the rail.
    for sx in (-1, 1):
        for z in (-3.0, 0.0, 3.0):
            for dz in (-0.12, 0.12):
                g.box("Rope", (0.5, 0.36, 0.09), P(2.2 * sx, 4.4, z + dz), C("#c9a46a"), R=Rw, collide=False)
    # A coiled lasso hanging on the side: the wrangler's own wagon.
    hook = P(-2.42, 4.1, 2.9)
    g.box("LassoHook", (0.4, 0.14, 0.14), hook, IRON, R=Rw, collide=False)
    g.ring("Lasso", add(hook, (-0.12, -0.75, 0)), matmul(Rw, angles(0, 0, 90)), 0.7, 0.14,
           [C("#d8a861"), C("#c48f4c")], n=16, collide=False)
    g.ring("Lasso", add(hook, (-0.2, -0.8, 0.05)), matmul(Rw, angles(0, 0, 90)), 0.62, 0.13,
           [C("#c48f4c"), C("#d8a861")], n=16, collide=False)
    g.box("LassoWrap", (0.3, 0.3, 0.3), add(hook, (-0.15, -0.12, 0)), C("#a8763c"), R=Rw, collide=False)
    # Shovel strapped to the other side.
    g.rod("ShovelHandle", P(2.45, 3.2, -3.6), P(2.45, 3.2, -1.0), 0.16, WOOD_LIGHT, collide=False)
    g.box("ShovelBlade", (0.08, 0.7, 0.8), P(2.47, 3.2, -4.0), C("#8c8c96"), R=Rw, collide=False)
    g.box("ShovelGrip", (0.14, 0.4, 0.14), P(2.45, 3.2, -0.9), WOOD_DARK, R=Rw, collide=False)

    # Driver's bench with a plaid blanket, and the tongue.
    g.box("Bench", (3.6, 0.25, 1.0), P(0, 4.75, -4.1), WOOD_LIGHT, R=Rw)
    for sx in (-1, 1):
        g.box("BenchLeg", (0.25, 1.85, 0.25), P(1.5 * sx, 3.72, -4.1), WOOD_DARK, R=Rw)
    g.box("Blanket", (1.5, 0.12, 1.02), P(-0.8, 4.92, -4.1), C("#c0392b"), R=Rw, collide=False)
    for i in range(3):
        g.box("BlanketStripe", (0.12, 0.13, 1.03), P(-1.3 + 0.5 * i, 4.93, -4.1), C("#f2e6c8"), R=Rw, collide=False)
    g.rod("Tongue", P(0, 1.75, -3.3), P(0, 0.5, -8.6), 0.34, WOOD_DARK)
    g.box("Doubletree", (2.8, 0.25, 0.3), P(0, 0.62, -8.2), WOOD_DARK, R=Rw)
    for sx in (-1, 1):
        g.box("SingleTree", (0.3, 0.2, 1.2), P(1.3 * sx, 0.55, -8.3), WOOD_DEEP, R=Rw)

    # Side details: water bucket, toolbox, spare wheel and a lantern at the back.
    g.octagon("Bucket", 0.42, 0.8, P(-2.75, 3.2, -1.0), WOOD_LIGHT)
    g.octagon("BucketHoop", 0.45, 0.12, P(-2.75, 3.4, -1.0), IRON, collide=False)
    g.rod("BucketHandle", P(-2.75, 3.6, -1.4), P(-2.6, 4.2, -1.0), 0.07, IRON, collide=False)
    g.box("Toolbox", (0.55, 0.6, 1.8), P(2.62, 2.95, 0.2), WOOD, R=Rw)
    g.box("ToolboxLid", (0.62, 0.12, 1.86), P(2.62, 3.3, 0.2), WOOD_DARK, R=Rw, collide=False)
    for z in (-0.5, 0.9):
        g.box("ToolboxStrap", (0.64, 0.66, 0.12), P(2.62, 2.95, z), IRON, R=Rw, collide=False)
    lantern(g, "WagonLantern", P(1.5, 7.2, 4.9), chain=0.5)
    g.box("LanternHook", (0.12, 0.12, 0.8), P(1.5, 7.2, 4.6), IRON, R=Rw, collide=False)

    # Cargo you can see through the open back.
    barrel(g, "CargoBarrel", P(-1.05, 2.8, 3.4))
    crate(g, "CargoCrate", P(0.95, 2.8, 3.5), size=1.2, yaw=yaw + 10)
    sack(g, "CargoSack", P(-0.2, 2.8, 1.8), yaw=yaw + 20)
    sack(g, "CargoSack", P(1.1, 2.8, 1.6), yaw=yaw - 15)
    g.octagon("Bedroll", 0.4, 1.8, P(-1.2, 3.25, 1.3), C("#6b8f3a"), yaw=0)
    g.box("BedrollStrap", (0.1, 0.85, 0.85), P(-1.2, 3.25, 1.3), WOOD_DEEP, R=Rw, collide=False)


# ------------------------------------------------------------------ arch ---

def arch(g, z=-9.0, half=7.5, rng=None):
    rng = rng or random.Random(3)
    top = 11.4
    for sx in (-1, 1):
        x = half * sx
        g.octagon("Footing", 1.15, 1.1, (x, 0.55, z), STONE_DARK)
        g.octagon("FootingCap", 1.0, 0.3, (x, 1.25, z), STONE)
        g.box("Moss", (1.4, 0.2, 0.9), (x - 0.2 * sx, 1.45, z - 0.3), C("#4f9e4a"), rot=(0, 20, 0), collide=False)
        g.octagon("Post", 0.62, top - 1.2, (x, 1.3 + (top - 1.2) / 2, z), WOOD_DARK)
        for y in (3.0, 6.2, 9.4):
            g.box("Bark", (0.12, 1.4, 0.3), (x + 0.6 * sx, y, z + 0.2), WOOD_DEEP, collide=False)
        g.octagon("PostTop", 0.5, 0.3, (x, top + 0.95, z), CUT)
        # Diagonal braces between the posts and the top beam.
        log(g, "Brace", (x, 8.6, z), (x - 2.2 * sx, top - 0.3, z), 0.45, WOOD)
    # Top log with cut ends, and a lower beam that holds the sign.
    log(g, "TopBeam", (-half - 1.6, top, z), (half + 1.6, top, z), 1.0, WOOD_DARK)
    for sx in (-1, 1):
        g.box("BeamEnd", (0.1, 0.85, 0.85), ((half + 1.65) * sx, top, z), CUT, collide=False)
        g.box("BeamEnd", (0.12, 0.82, 0.82), ((half + 1.66) * sx, top, z), CUT, rot=(45, 0, 0), collide=False)
    log(g, "SignBeam", (-half, 9.6, z), (half, 9.6, z), 0.55, WOOD)
    # Leaves and hanging vines on the top beam.
    for i, (x, w) in enumerate([(-8.2, 1.8), (-6.4, 1.4), (-2.5, 1.2), (1.2, 1.0), (5.6, 1.6), (7.8, 1.9)]):
        for j in range(3):
            g.box("Leaves", (w * rng.uniform(0.7, 1.0), w * 0.6, w * rng.uniform(0.7, 1.0)),
                  (x + rng.uniform(-0.5, 0.5), top + 0.5 + 0.3 * j, z + rng.uniform(-0.4, 0.4)), LEAF[(i + j) % 3],
                  rot=(rng.uniform(-25, 25), rng.uniform(0, 90), rng.uniform(-25, 25)), collide=False)
    for x, length in ((-7.0, 2.4), (-5.9, 1.6), (6.2, 2.0), (7.2, 2.8), (-0.9, 1.2)):
        g.rod("Vine", (x, top - 0.4, z - 0.45), (x + 0.15, top - 0.4 - length, z - 0.5), 0.1, C("#3f8a3c"),
              collide=False)
        for k in range(int(length / 0.7)):
            g.box("VineLeaf", (0.35, 0.2, 0.3), (x + 0.1 * (k % 2), top - 0.9 - 0.7 * k, z - 0.52), LEAF[k % 3],
                  rot=(0, 30 * k, 20), collide=False)
    # Hanging sign on chains.
    sign_y, sign_w, sign_h = 7.3, 8.2, 2.3
    for sx in (-1, 1):
        for i in range(4):
            g.box("SignChain", (0.14, 0.34, 0.14), (3.3 * sx, 9.2 - 0.3 * i, z), IRON, rot=(0, 45 * (i % 2), 0),
                  collide=False)
        g.box("SignRing", (0.3, 0.3, 0.3), (3.3 * sx, sign_y + sign_h / 2 + 0.05, z), IRON, rot=(45, 0, 0),
              collide=False)
    board = g.box("SignBoard", (sign_w, sign_h, 0.3), (0, sign_y, z), WOOD_LIGHT,
                  children=[surface_text("To the Forest", "Back", stroke="#5a3418"),
                            surface_text("To Wrangler Camp", "Front", stroke="#5a3418")])
    for sz in (-1, 1):
        for y in (-0.38, 0.38):
            g.box("PlankLine", (sign_w * 0.96, 0.05, 0.02), (0, sign_y + y, z + sz * 0.16), WOOD_DARK, collide=False)
    for y in (-1, 1):
        g.box("SignFrame", (sign_w + 0.3, 0.25, 0.42), (0, sign_y + y * (sign_h / 2 + 0.05), z), WOOD_DEEP)
    for sx in (-1, 1):
        g.box("SignFrame", (0.25, sign_h + 0.6, 0.42), (sx * (sign_w / 2 + 0.05), sign_y, z), WOOD_DEEP)
        # Little pine trees carved at both ends of the sign (on both faces).
        for sz in (-1, 1):
            for j, (h, w) in enumerate([(0.9, 1.1), (0.7, 0.85), (0.5, 0.6)]):
                tri(g, "SignPine", (sx * (sign_w / 2 - 0.75), sign_y - 0.75 + 0.42 * j, z + sz * 0.18), w, h, 0.06,
                    LEAF[j], collide=False)
    # Lanterns hanging from the top beam, outside the sign.
    for sx in (-1, 1):
        lantern(g, "ArchLantern", (5.9 * sx, top - 0.5, z))


# -------------------------------------------------------------- signpost ---

def signpost(g, pos=(8.6, 0, -2.0)):
    x, _, z = pos
    g.octagon("PostBase", 0.55, 0.4, (x, 0.2, z), STONE_DARK)
    g.box("SignPost", (0.45, 7.0, 0.45), (x, 3.7, z), WOOD_DARK)
    g.box("SignPostTop", (0.6, 0.3, 0.6), (x, 7.3, z), WOOD_DEEP)
    boards = [("Critter Woods", 6.3, 90, "#b97a46"), ("Deep Woods", 5.3, 70, "#8a5a2e"),
              ("Wrangler Camp", 4.3, -90, "#b97a46")]
    for text, y, yaw, color in boards:
        R = angles(0, yaw, 0)
        length = 3.4
        center = at((x, y, z), R, (-length / 2 - 0.1, 0, 0))
        g.box("ArrowBoard", (length, 0.75, 0.2), center, C(color), R=R,
              children=[surface_text(text, "Front", ppu=70, stroke="#3a2416"),
                        surface_text(text, "Back", ppu=70, stroke="#3a2416")])
        tip = at((x, y, z), R, (-length - 0.1, 0, 0))
        for sgn in (-1, 1):
            g.wedge("ArrowTip", (0.2, 0.4, 0.7), at(tip, R, (-0.3, 0.19 * sgn, 0)), C(color),
                    R=matmul(R, angles(0, 90, 0 if sgn > 0 else 180)))
        g.box("Nail", (0.1, 0.1, 0.24), (x, y, z), IRON, collide=False)


# -------------------------------------------------------------- campfire ---

def campfire(g, pos=(5.0, 0, 5.5)):
    rng = random.Random(9)
    x, _, z = pos
    for i in range(9):
        t = 2 * math.pi * i / 9
        g.box("FireStone", (0.7, 0.45, 0.6), (x + math.cos(t) * 1.3, 0.22, z + math.sin(t) * 1.3),
              STONE if i % 2 else STONE_DARK, rot=(rng.uniform(-8, 8), math.degrees(-t), rng.uniform(-8, 8)))
    g.box("Ashes", (1.8, 0.1, 1.8), (x, 0.05, z), C("#3a3434"), rot=(0, 20, 0), collide=False)
    for i in range(4):
        t = 2 * math.pi * i / 4 + 0.4
        log(g, "FireLog", (x + math.cos(t) * 0.9, 0.15, z + math.sin(t) * 0.9), (x, 1.0, z), 0.3, WOOD_DEEP,
            collide=False)
    flames = {"class": "Fire", "name": "Flames", "props": {
        "Heat": 8, "Size": 3.2, "Color": list(C("#ff9a3c")), "SecondaryColor": list(C("#ffd166"))}}
    smoke = {"class": "ParticleEmitter", "name": "Smoke", "props": {
        "Texture": "rbxasset://textures/particles/smoke_main.dds", "Rate": 3, "Lifetime": [2.5, 4],
        "Speed": [2, 3], "SpreadAngle": [10, 10], "Size": [[0, 1], [1, 4]], "Transparency": [[0, 0.6], [1, 1]],
        "Color": [[0, 0.55, 0.55, 0.55], [1, 0.8, 0.8, 0.8]], "LightInfluence": 1, "Acceleration": [0.6, 0, 0]}}
    embers = {"class": "ParticleEmitter", "name": "Embers", "props": {
        "Texture": "rbxasset://textures/particles/sparkles_main.dds", "Rate": 6, "Lifetime": [1, 1.8],
        "Speed": [2, 4], "SpreadAngle": [25, 25], "Size": [[0, 0.25], [1, 0]], "Transparency": [[0, 0], [1, 1]],
        "Color": [[0, 1, 0.8, 0.3], [1, 1, 0.4, 0.1]], "LightEmission": 1, "LightInfluence": 0}}
    g.box("FireCore", (0.8, 0.8, 0.8), (x, 0.7, z), C("#ffb347"), transparency=1, collide=False, shadow=False,
          children=[flames, smoke, embers, point_light("#ff9a3c", 2.0, 20)])
    # Tripod with a cooking pot.
    for i in range(3):
        t = 2 * math.pi * i / 3
        g.rod("Tripod", (x + math.cos(t) * 1.6, 0, z + math.sin(t) * 1.6), (x, 3.4, z), 0.14, WOOD_DEEP,
              collide=False)
    g.rod("PotChain", (x, 3.4, z), (x, 2.4, z), 0.08, IRON, collide=False)
    g.octagon("Pot", 0.55, 0.7, (x, 1.95, z), IRON, collide=False)
    g.octagon("PotRim", 0.6, 0.12, (x, 2.3, z), C("#4a4a54"), collide=False)
    g.octagon("Stew", 0.45, 0.05, (x, 2.32, z), C("#8a5a2e"), collide=False)
    # Two logs to sit on.
    log(g, "SeatLog", (x + 2.2, 0.4, z - 1.6), (x + 2.8, 0.4, z + 1.4), 0.8, WOOD)
    log(g, "SeatLog", (x - 1.4, 0.4, z + 2.4), (x + 1.6, 0.4, z + 2.6), 0.8, WOOD)


# ------------------------------------------------------------------ props ---

def cargo(g):
    barrel(g, "Barrel", (-8.2, 0, 4.8))
    barrel(g, "Barrel", (-7.0, 0, 5.8), k=0.9)
    crate(g, "Crate", (-8.3, 0, 7.2), 1.4, yaw=8)
    crate(g, "Crate", (-8.2, 1.4, 7.2), 1.0, yaw=-12)
    crate(g, "Crate", (-6.9, 0, 7.6), 1.1, yaw=25)
    sack(g, "Sack", (-6.6, 0, 3.9), yaw=30)
    sack(g, "Sack", (-7.6, 0, 3.3), yaw=-20)
    g.box("HayBale", (2.6, 1.3, 1.6), (-8.1, 0.65, 1.5), C("#e8c35a"), rot=(0, 90, 0))
    g.box("HayTop", (2.6, 0.2, 1.6), (-8.1, 1.4, 1.5), C("#f2d57a"), rot=(0, 90, 0), collide=False)
    for dz in (-0.7, 0.7):
        g.box("HayStrap", (0.14, 1.36, 1.66), (-8.1, 0.66, 1.5 + dz), C("#a8761c"), collide=False)
    g.rod("Pitchfork", (-7.4, 0, 0.4), (-7.9, 3.4, 0.9), 0.1, WOOD_DARK, collide=False)
    for i in range(3):
        g.rod("Tine", (-7.9 + 0.12 * (i - 1), 3.35, 0.9), (-8.0 + 0.12 * (i - 1), 4.0, 1.0), 0.05, IRON, collide=False)


# ----------------------------------------------------------------- build ---

def build():
    wg, ar, sp, cf, cg = (Group(n) for n in ("Wagon", "Archway", "Signpost", "Campfire", "Cargo"))
    wagon(wg, origin=(-4.2, 0, 1.5), yaw=0)
    arch(ar)
    signpost(sp)
    campfire(cf)
    cargo(cg)
    groups = (wg, ar, sp, cf, cg)
    root = {"class": "Part", "name": "Root", "id": "Root",
            "props": {"Size": [1, 0.1, 1], "CFrame": cframe(IDENTITY, (0, 0.05, 0)), "Transparency": 1,
                      "Anchored": True, "CanCollide": False, "CanTouch": False, "CanQuery": False,
                      "CastShadow": False, "PivotOffset": cframe(IDENTITY, (0, -0.05, 0))}}
    model = {"class": "Model", "name": "ForestEntrance", "tags": ["ForestEntrance"],
             "props": {"PrimaryPart": {"ref": "Root"}},
             "children": [root] + [group_instance(g) for g in groups]}
    return [model], groups


def preview(groups):
    r = lambda v: [round(x, 3) for x in v]
    vp = lambda n, s, z, cf, c, m="SmoothPlastic", t=0, sh=True: {
        "n": n, "s": s, "z": r(z), "cf": r(cf), "c": r(c), "m": m, "t": t, "r": 0, "st": False, "sh": sh}
    parts = [vp("Ground", "block", (80, 2, 120), cframe(IDENTITY, (0, -1, -10)), C("#6fd35a"), m="Grass"),
             vp("Path", "block", (12, 0.1, 40), cframe(IDENTITY, (0, 0.05, 14)), C("#f2b394"))]
    rng = random.Random(2)
    # Blocky cliffs on both sides, like in the game.
    for sx in (-1, 1):
        for i in range(14):
            for j in range(4):
                w = rng.uniform(4, 6)
                parts.append(vp("Cliff", "block", (w, 3.2, w), cframe(angles(0, rng.uniform(-8, 8), 0),
                                (sx * (13.5 + j * 3 + rng.uniform(0, 1.5)), 1.6 + j * 3.1, 18 - i * 4.2)),
                                C("#b3c3d9") if (i + j) % 2 else C("#c4d2e4")))
            parts.append(vp("CliffGrass", "block", (8, 0.6, 4.5), cframe(IDENTITY, (sx * 20, 12.8, 18 - i * 4.2)),
                            C("#6fd35a")))
    count = 0
    for g in groups:
        for p in g.parts:
            if p["transparency"] >= 1:
                continue
            count += 1
            name = p["name"] if p["name"] == "SignBoard" else f"{p['name']}_{count}"
            parts.append(vp(name, p["shape"], p["size"], cframe(p["R"], p["p"]), p["color"], m=p["material"],
                            t=p["transparency"], sh=p["shadow"]))
    # The viewer draws text on a part's -Z face, so add a thin copy of the sign that faces the camp.
    sign = next(p for p in groups[1].parts if p["name"] == "SignBoard")
    parts.append(vp("SignBack", "block", (sign["size"][0] - 0.1, sign["size"][1] - 0.1, 0.02),
                    cframe(angles(0, 180, 0), add(sign["p"], (0, 0, 0.17))), sign["color"]))
    texts = [{"part": "SignBack", "lines": [{"text": "To the Forest", "color": "#fff4dc", "size": 1, "font": "body",
                                             "strokeColor": "#5a3418"}], "pad": 0.14}]
    # Pine forest behind the archway, from the forest kit.
    try:
        import build_kit
        kit = {a.name: a for a in build_kit.make_kit()}
        rng = random.Random(6)
        spots = []
        for _ in range(60):
            x, z = rng.uniform(-12, 12), rng.uniform(-48, -15)
            if abs(x) < 5 + (z + 48) * 0.12:
                continue
            spots.append((kit[rng.choice(["PineMedium", "PineTall", "OakMedium", "PineMedium", "OakLarge"])],
                          (x, 0.0, z), rng.uniform(0, 360), rng.uniform(0.9, 1.25)))
        for name, x, z in (("BushSmall", -3.8, -12), ("FlowerPatch", 3.6, -11), ("GrassTuft", -10, -4),
                           ("GrassTuft", 10.5, 3), ("FlowerPatch", -10.2, 10)):
            spots.append((kit[name], (x, 0.0, z), rng.uniform(0, 360), 1.0))
        parts.extend(build_kit.viewer_parts(list(kit.values()), spots))
    except Exception as exc:
        print("no forest kit trees in the preview:", exc)
    env = {"sky": [[0, "#3f9fff"], [0.55, "#96d0ff"], [1, "#dff2ff"]], "fog": ["#dff2ff", 200, 500],
           "sun": {"dir": [-0.5, 1.0, 0.45], "intensity": 2.5}, "hemi": ["#ffffff", "#8fb070", 1.45],
           "bloom": [0.4, 0.5, 0.9]}
    shots = {
        "game": {"camera": {"pos": [2, 22, 32], "target": [-1, 4, -4], "fov": 55},
                 "shadow": {"center": [0, 0, 0], "radius": 30}},
        "side": {"camera": {"pos": [16, 9, 12], "target": [-3, 4, -1], "fov": 55},
                 "shadow": {"center": [0, 0, 0], "radius": 30}},
        "wagon": {"camera": {"pos": [4, 8, 14], "target": [-4, 4, 2], "fov": 50},
                  "shadow": {"center": [-4, 0, 2], "radius": 16}},
        "arch": {"camera": {"pos": [0, 7, 6], "target": [0, 8, -9], "fov": 55},
                 "shadow": {"center": [0, 0, -9], "radius": 16}},
    }
    return {"env": env, "parts": parts, "models": [], "texts": texts, "sprites": [], "shots": shots}


def main():
    tree, groups = build()
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "entrance.json").write_text(json.dumps(tree))
    (out / "world.json").write_text(json.dumps(preview(groups)))
    for g in groups:
        print(f"{g.name:10} {len(g.parts):4} parts")
    print(f"total {sum(len(g.parts) for g in groups)} parts")
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        cmd = ["cargo", "run", "--quiet", "--release", "--manifest-path",
               str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "entrance.json"), target]
        if "--rbxmx" in sys.argv:
            cmd.append(sys.argv[sys.argv.index("--rbxmx") + 1])
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
