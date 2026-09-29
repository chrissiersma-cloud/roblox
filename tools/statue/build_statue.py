#!/usr/bin/env python3
"""Wrangler Camp statue fountain, built from Parts in the game's blocky style.

A blocky cowboy on a two-tier sandstone pedestal with a gold "WRANGLER CAMP" plaque, spinning a lasso
over his head, in a round wooden tub fountain with four water jets, on a sheriff-star floor inlay with
barrels, a hay bale with a wagon wheel, cactus planters and lanterns around it.

    python3 tools/statue/build_statue.py                  -> build/statue.json and build/world.json (preview)
    python3 tools/statue/build_statue.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
"""

import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "animal-models"))
sys.path.insert(0, str(HERE.parent / "forest-kit"))

from lib import IDENTITY, add, aim, angles, apply, cframe, compose, cross, hex_color, inverse, matmul, scale, sub, unit  # noqa: E402

TAN22 = math.tan(math.radians(22.5))
SMOKE = "rbxasset://textures/particles/smoke_main.dds"

# Statue colours per style. Parts of the cowboy carry a "Paint" attribute with one of these keys,
# so the StatueStyle module can recolour him in Studio.
STYLES = {
    "Painted": {"shirt": "#d8433b", "vest": "#6b3f22", "jeans": "#2f5fd0", "skin": "#f1c9a0", "hat": "#a36a36",
                "hatDark": "#3a2416", "boots": "#5a3418", "bandana": "#2f5fd0", "belt": "#3a2416", "gold": "#f2c14e",
                "eye": "#1a1008", "hair": "#5a3418", "reflectance": 0.0},
    "Bronze": {"shirt": "#b07a44", "vest": "#8a5a2e", "jeans": "#9a6a3a", "skin": "#c48a50", "hat": "#8a5a2e",
               "hatDark": "#5a3418", "boots": "#6b4424", "bandana": "#a06a36", "belt": "#5a3418", "gold": "#d49a5a",
               "eye": "#3a2416", "hair": "#6b4424", "reflectance": 0.1},
    "Gold": {"shirt": "#e8b84a", "vest": "#c9962e", "jeans": "#d9a83c", "skin": "#f2cc6a", "hat": "#c9962e",
             "hatDark": "#8a6418", "boots": "#a8761c", "bandana": "#f2d57a", "belt": "#8a6418", "gold": "#fff0a8",
             "eye": "#6b4a10", "hair": "#a8761c", "reflectance": 0.2},
}


def C(h):
    return hex_color(h)


def up_to(d):
    """Rotation whose local Y axis points along d."""
    y = unit(d)
    ref = (0, 0, 1) if abs(y[2]) < 0.9 else (1, 0, 0)
    x = unit(cross(y, ref))
    z = cross(x, y)
    return tuple((x[i], y[i], z[i]) for i in range(3))


class Group:
    """A Model's worth of anchored parts (and extra instances)."""

    def __init__(self, name):
        self.name = name
        self.parts = []
        self.extra = []
        self.primary = None

    def part(self, shape, name, size, pos, color, R=None, rot=None, material="SmoothPlastic", collide=True,
             shadow=True, transparency=0.0, reflectance=0.0, paint=None, children=None, pid=None):
        if R is None:
            R = angles(*rot) if rot else IDENTITY
        if isinstance(color, str):
            color = C(color)
        p = {"shape": shape, "name": name, "size": tuple(size), "R": R, "p": tuple(pos), "color": color,
             "material": material, "collide": collide, "shadow": shadow, "transparency": transparency,
             "reflectance": reflectance, "paint": paint, "children": children or [], "id": pid}
        self.parts.append(p)
        return p

    def box(self, name, size, pos, color, **kw):
        return self.part("block", name, size, pos, color, **kw)

    def wedge(self, name, size, pos, color, **kw):
        return self.part("wedge", name, size, pos, color, **kw)

    def cyl(self, name, length, d, pos, color, **kw):
        return self.part("cylinder", name, (length, d, d), pos, color, **kw)

    def rod(self, name, a, b, d, color, **kw):
        mid = scale(add(a, b), 0.5)
        return self.box(name, (math.dist(a, b), d, d), mid, color, R=aim(sub(b, a)), **kw)

    def octagon(self, name, r, h, pos, color, yaw=0.0, **kw):
        """Real regular octagonal prism (flat faces facing +-X/+-Z before yaw), inradius r, height h."""
        s = 2 * r * TAN22
        leg = r - s / 2
        Ry = angles(0, yaw, 0)
        self.box(name, (2 * r, h, s), pos, color, R=Ry, **kw)
        self.box(name, (s, h, 2 * r), pos, color, R=Ry, **kw)
        Rw = ((0, 1, 0), (1, 0, 0), (0, 0, -1))  # wedge local X -> up, Y -> +X, Z -> -Z (triangle lies flat)
        for k in range(4):
            Rk = matmul(Ry, angles(0, 90 * k, 0))
            off = apply(Rk, (s / 2 + leg / 2, 0, s / 2 + leg / 2))
            self.wedge(name, (h, leg, leg), add(pos, off), color, R=matmul(Rk, Rw), **kw)

    def ring(self, name, center, R, radius, thick, colors, n=24, twist=True, **kw):
        """Ring of short square segments in the plane of R's local XZ (normal = R's local Y)."""
        normal = apply(R, (0, 1, 0))
        seg = 2 * math.pi * radius / n * 1.08
        for i in range(n):
            t = 2 * math.pi * i / n
            local = (radius * math.cos(t), 0, radius * math.sin(t))
            tangent = apply(R, (-math.sin(t), 0, math.cos(t)))
            Rs = aim(tangent, roll_up=normal)
            if twist and i % 2:
                Rs = matmul(Rs, angles(45, 0, 0))
            self.box(name, (seg, thick, thick), add(center, apply(R, local)), colors[i % len(colors)], R=Rs, **kw)


# ------------------------------------------------------------------ cowboy --

Y0 = 7.65  # top of the grass on the pedestal (the cowboy's feet)
PAINT = STYLES["Painted"]


def cowboy(g):
    P = lambda key: C(PAINT[key])
    kw = lambda key: {"paint": key}
    y0 = Y0
    # Legs and boots.
    for sx in (-1, 1):
        x = sx * 1.55
        g.box("Leg", (3.0, 3.9, 3.0), (x, y0 + 4.05, 0), P("jeans"), **kw("jeans"))
        g.box("Boot", (3.2, 2.4, 3.3), (x, y0 + 1.2, 0.05), P("boots"), **kw("boots"))
        g.box("BootToe", (3.2, 1.0, 1.3), (x, y0 + 0.5, -2.2), P("boots"), **kw("boots"))
        g.box("BootCuff", (3.35, 0.45, 3.45), (x, y0 + 2.35, 0.05), P("hatDark"), **kw("hatDark"))
        g.cyl("Spur", 0.3, 0.9, (x + sx * 1.1, y0 + 0.7, 1.75), P("gold"), R=angles(0, 0, 0), **kw("gold"))
    # Torso, vest, belt, bandana, badge.
    g.box("Torso", (6.2, 6.0, 3.1), (0, y0 + 9.0, 0), P("shirt"), **kw("shirt"))
    for sx in (-1, 1):
        g.box("Vest", (2.0, 5.2, 0.3), (sx * 2.1, y0 + 9.2, -1.7), P("vest"), **kw("vest"))
        g.box("Vest", (0.3, 5.2, 3.4), (sx * 3.2, y0 + 9.2, 0), P("vest"), **kw("vest"))
    g.box("Vest", (6.5, 5.2, 0.3), (0, y0 + 9.2, 1.7), P("vest"), **kw("vest"))
    g.box("Belt", (6.5, 0.8, 3.5), (0, y0 + 6.4, 0), P("belt"), **kw("belt"))
    g.box("Buckle", (1.3, 1.0, 0.25), (0, y0 + 6.4, -1.85), P("gold"), **kw("gold"))
    g.box("Bandana", (2.8, 1.0, 0.3), (0, y0 + 11.45, -1.7), P("bandana"), **kw("bandana"))
    g.box("Bandana", (1.5, 1.5, 0.3), (0, y0 + 10.7, -1.72), P("bandana"), rot=(0, 0, 45), **kw("bandana"))
    for turn in (0, 45):
        g.box("Badge", (1.05, 1.05, 0.12), (-2.1, y0 + 10.0, -1.92), P("gold"), rot=(0, 0, turn), **kw("gold"))
    g.box("Badge", (0.45, 0.45, 0.14), (-2.1, y0 + 10.0, -1.98), P("belt"), rot=(0, 0, 45), **kw("belt"))
    # Neck and head with face.
    g.box("Neck", (2.0, 0.7, 2.0), (0, y0 + 12.3, 0), P("skin"), **kw("skin"))
    g.box("Head", (4.4, 4.2, 4.0), (0, y0 + 14.7, 0), P("skin"), **kw("skin"))
    for sx in (-1, 1):
        g.box("Eye", (0.55, 0.85, 0.1), (sx * 0.95, y0 + 15.1, -2.02), P("eye"), shadow=False, **kw("eye"))
        g.box("Brow", (1.1, 0.28, 0.1), (sx * 0.95, y0 + 15.85, -2.02), P("hair"), rot=(0, 0, -sx * 8),
              shadow=False, **kw("hair"))
    g.box("Mustache", (2.4, 0.55, 0.2), (0, y0 + 13.95, -2.05), P("hair"), **kw("hair"))
    g.box("Mustache", (0.6, 0.9, 0.2), (-1.2, y0 + 13.6, -2.05), P("hair"), **kw("hair"))
    g.box("Mustache", (0.6, 0.9, 0.2), (1.2, y0 + 13.6, -2.05), P("hair"), **kw("hair"))
    # Hat: brim with curled sides, crown with a band and a pinched top.
    g.box("HatBrim", (6.6, 0.45, 7.4), (0, y0 + 16.6, 0), P("hat"), **kw("hat"))
    for sx in (-1, 1):
        g.box("HatBrim", (1.5, 0.45, 7.0), (sx * 3.85, y0 + 16.9, 0), P("hat"), rot=(0, 0, sx * 28), **kw("hat"))
    g.box("HatCrown", (4.8, 2.8, 4.5), (0, y0 + 18.2, 0), P("hat"), **kw("hat"))
    g.box("HatBand", (4.9, 0.6, 4.6), (0, y0 + 17.1, 0), P("hatDark"), **kw("hatDark"))
    g.wedge("HatTop", (4.8, 0.8, 2.25), (0, y0 + 20.0, -1.125), P("hat"), **kw("hat"))
    g.wedge("HatTop", (4.8, 0.8, 2.25), (0, y0 + 20.0, 1.125), P("hat"), rot=(0, 180, 0), **kw("hat"))
    # Left arm hangs down and holds a coil of rope.
    g.box("ArmL", (3.0, 6.0, 3.0), (-4.65, y0 + 9.0, 0), P("shirt"), **kw("shirt"))
    g.box("HandL", (2.6, 1.4, 2.6), (-4.65, y0 + 5.3, 0), P("skin"), **kw("skin"))
    coil_R = angles(0, 0, 90)
    g.ring("Coil", (-4.65, y0 + 3.5, -0.2), coil_R, 1.7, 0.5, [C("#c99a5b"), C("#a87a45")], n=14, collide=False)
    g.ring("Coil", (-4.95, y0 + 3.3, 0.2), coil_R, 1.6, 0.5, [C("#a87a45"), C("#c99a5b")], n=14, collide=False)
    # Right arm raised up, holding the lasso.
    pivot = (4.65, y0 + 11.0, 0)
    d = unit((0.2, 1, 0.1))
    Ra = up_to(d)
    g.box("ArmR", (3.0, 6.0, 3.0), add(pivot, scale(d, 2.4)), P("shirt"), R=Ra, **kw("shirt"))
    hand_pos = add(pivot, scale(d, 6.1))
    hand = g.box("HandR", (2.6, 1.4, 2.6), hand_pos, P("skin"), R=Ra, **kw("skin"))
    return hand, hand_pos


# ------------------------------------------------------------------ lasso ---

def lasso(g, hand_pos):
    center = add(hand_pos, (-3.6, 5.6, 0.2))
    normal = unit((0.18, 1, -0.28))
    R = up_to(normal)
    hub = g.box("Hub", (0.5, 0.5, 0.5), center, C("#ffffff"), R=R, transparency=1, collide=False, shadow=False,
                pid="Lasso.Hub")
    g.primary = "Lasso.Hub"
    radius = 6.3
    g.ring("Rope", center, R, radius, 0.55, [C("#c99a5b"), C("#a87a45")], n=32, collide=False)
    # Honda knot at the loop point nearest to the hand.
    best = min(range(64), key=lambda i: math.dist(
        add(center, apply(R, (radius * math.cos(i * math.pi / 32), 0, radius * math.sin(i * math.pi / 32)))), hand_pos))
    t = best * math.pi / 32
    honda_pos = add(center, apply(R, (radius * math.cos(t), 0, radius * math.sin(t))))
    honda = g.box("Honda", (1.0, 0.85, 0.85), honda_pos, C("#8d6232"), R=R, collide=False, pid="Lasso.Honda",
                  children=[{"class": "Attachment", "name": "RopeEnd", "id": "Lasso.RopeEnd", "props": {}}])
    return hub, honda_pos


# --------------------------------------------------------------- pedestal ---

def pedestal(g):
    sand, sand_dark, cap = C("#d4a26d"), C("#b07a44"), C("#efd3a2")
    g.octagon("Tier1", 8.0, 3.0, (0, 1.5, 0), sand_dark)
    g.octagon("Tier1Cap", 8.35, 0.5, (0, 3.0, 0), cap)
    g.octagon("Tier2", 5.5, 4.0, (0, 5.25, 0), sand)
    g.octagon("Tier2Cap", 5.85, 0.5, (0, 7.25, 0), cap)
    g.octagon("GrassEdge", 5.4, 0.35, (0, 7.55, 0), C("#4fc04a"), collide=False)
    g.octagon("Grass", 5.1, 0.4, (0, 7.45, 0), C("#6fd35a"))
    # Gold plaque with the camp name on the front face.
    gui = {
        "class": "SurfaceGui", "name": "PlaqueText",
        "props": {"Face": "Front", "SizingMode": "PixelsPerStud", "PixelsPerStud": 60, "LightInfluence": 0.4},
        "children": [{
            "class": "TextLabel", "name": "Label",
            "props": {"Size": [1, 0, 1, 0], "BackgroundTransparency": 1, "Text": "WRANGLER CAMP",
                      "TextScaled": True, "TextColor3": list(C("#4a2a10")),
                      "FontFace": {"family": "rbxasset://fonts/families/FredokaOne.json", "weight": 400}},
            "children": [{"class": "UIPadding", "name": "Padding",
                          "props": {"PaddingLeft": [0.06, 0], "PaddingRight": [0.06, 0],
                                    "PaddingTop": [0.14, 0], "PaddingBottom": [0.1, 0]}}],
        }],
    }
    g.box("PlaqueFrame", (4.5, 1.85, 0.2), (0, 5.3, -5.6), C("#a8761c"))
    g.box("Plaque", (4.2, 1.55, 0.25), (0, 5.3, -5.7), C("#f2c14e"), reflectance=0.1, children=[gui])
    # Horseshoes (open end up, for luck) on the two front diagonal faces.
    for yaw in (45, -45):
        R = angles(0, yaw, 0)
        at = lambda x, y: apply(R, (x, 5.3 + y, -5.5 - 0.12))
        for sx in (-1, 1):
            g.box("Horseshoe", (0.35, 1.3, 0.22), at(sx * 0.5, 0.15), C("#f2c14e"), R=R, reflectance=0.1)
        g.box("Horseshoe", (1.35, 0.35, 0.22), at(0, -0.5), C("#f2c14e"), R=R, reflectance=0.1)


# ---------------------------------------------------------------- fountain ---

POOL_R = 17.0
WATER_Y = 1.9


def fountain(g, rng):
    n = 28
    wall = 1.4
    r = POOL_R - wall / 2
    arc = 2 * math.pi * r / n
    for i in range(n):
        yaw = -360 * i / n
        R = angles(0, yaw, 0)
        pos = apply(R, (0, 1.2, -r))
        g.box("Plank", (arc * 1.04, 2.4, wall), pos, C("#a86b3e") if i % 2 else C("#b97a46"), R=R)
        g.box("Lip", (arc * 1.12, 0.4, wall + 0.5), apply(R, (0, 2.6, -r)), C("#d9a066"), R=R)
        for y in (0.6, 1.85):
            g.box("Hoop", (arc * 1.1, 0.3, wall + 0.12), apply(R, (0, y, -r)), C("#4a3426"), R=R, collide=False)
    g.cyl("PoolFloor", 0.6, 2 * (POOL_R - wall) + 0.2, (0, 0.3, 0), C("#2e9fe0"), R=angles(0, 0, 90))
    g.cyl("Water", 0.35, 2 * (POOL_R - wall) + 0.2, (0, WATER_Y - 0.175, 0), C("#45b9f2"), R=angles(0, 0, 90),
          material="Glass", transparency=0.25, collide=False, shadow=False)
    for x, z, s in ((-10.5, -6.0, 1.2), (11.0, 4.5, 1.0), (-6.5, 10.5, 0.9), (9.0, -9.5, 0.8)):
        g.octagon("LilyPad", s, 0.12, (x, WATER_Y + 0.06, z), C("#4fb84f"), yaw=rng.uniform(0, 45), collide=False)
    g.box("Flower", (0.5, 0.35, 0.5), (-10.2, WATER_Y + 0.3, -5.8), C("#ff9ec4"), rot=(0, 45, 0), collide=False)

    # Four gold spouts on the diagonal faces of the lower tier, each shooting a curved jet (Beam) into the pool.
    anchor_pos = (0, 0.2, 0)
    attachments, beams, splashes = [], [], []
    for k, yaw in enumerate((45, 135, 225, 315)):
        R = angles(0, yaw, 0)
        out = apply(R, (0, 0, -1))
        face = apply(R, (0, 2.3, -8.0))
        g.box("Spout", (0.8, 0.8, 1.3), add(face, scale(out, 0.55)), C("#f2c14e"), R=R, reflectance=0.1)
        start = add(face, scale(out, 1.25))
        end = add(scale(out, 13.6), (0, WATER_Y, 0))
        a0 = unit(add(scale(out, 1.0), (0, 1.4, 0)))
        a1 = unit(add(scale(out, 0.55), (0, -1.0, 0)))
        attachments.append({"class": "Attachment", "name": f"JetStart{k}", "id": f"Jet.S{k}",
                            "props": {"CFrame": cframe(aim(a0), sub(start, anchor_pos))}})
        attachments.append({"class": "Attachment", "name": f"JetEnd{k}", "id": f"Jet.E{k}",
                            "props": {"CFrame": cframe(aim(a1), sub(end, anchor_pos))}})
        beams.append({"class": "Beam", "name": f"Jet{k}", "props": {
            "Attachment0": {"ref": f"Jet.S{k}"}, "Attachment1": {"ref": f"Jet.E{k}"},
            "CurveSize0": 4.2, "CurveSize1": 3.0, "Width0": 0.9, "Width1": 0.6, "Segments": 24,
            "FaceCamera": True, "LightEmission": 0.35, "LightInfluence": 0.6,
            "Color": [[0, *C("#e6f8ff")], [1, *C("#9fdcfa")]], "Transparency": [[0, 0.05], [1, 0.3]],
        }})
        splash = {"class": "ParticleEmitter", "name": "Splash", "props": {
            "Texture": SMOKE, "Rate": 18, "Lifetime": [0.3, 0.6], "Speed": [3, 5], "SpreadAngle": [25, 25],
            "EmissionDirection": "Top", "Acceleration": [0, -22, 0], "LightEmission": 0.3,
            "Size": [[0, 0.5], [1, 1.3]], "Transparency": [[0, 0.25], [1, 1]],
            "Color": [[0, 1, 1, 1], [1, *C("#cdefff")]],
        }}
        g.box("SplashZone", (0.6, 0.2, 0.6), end, C("#ffffff"), transparency=1, collide=False, shadow=False,
              children=[splash])
        splashes.append((start, a0, end, a1))
    g.box("JetAnchor", (0.4, 0.4, 0.4), anchor_pos, C("#ffffff"), transparency=1, collide=False, shadow=False,
          children=attachments)
    g.extra.extend(beams)
    return splashes


# ------------------------------------------------------------- star floor ---

def star_floor(g):
    for turn, w, y, h, col in ((0, 48.0, 0.04, 0.08, "#f7d3b8"), (45, 48.0, 0.04, 0.08, "#f7d3b8"),
                               (0, 46.0, 0.06, 0.12, "#d9785a"), (45, 46.0, 0.06, 0.12, "#d9785a")):
        g.box("Star", (w, h, w), (0, y, 0), C(col), rot=(0, turn, 0), collide=False, shadow=False)


# ------------------------------------------------------------------- props ---

def barrel(g, pos, k=1.0):
    r, h = 1.5 * k, 3.6 * k
    g.octagon("Barrel", r, h, add(pos, (0, h / 2, 0)), C("#8a5a2e"))
    for y in (0.8 * k, h - 0.8 * k):
        g.octagon("BarrelHoop", r + 0.06, 0.35 * k, add(pos, (0, y, 0)), C("#3a2a20"), collide=False)
    g.octagon("BarrelLid", r - 0.25, 0.1, add(pos, (0, h + 0.05, 0)), C("#a36a36"), collide=False)


def hay_and_wheel(g, pos, yaw):
    R = angles(0, yaw, 0)
    at = lambda x, y, z: add(pos, apply(R, (x, y, z)))
    g.box("HayBale", (5.0, 2.6, 3.0), at(0, 1.3, 0), C("#e8c35a"), R=R)
    g.box("HayTop", (5.0, 0.35, 3.0), at(0, 2.75, 0), C("#f2d57a"), R=R, collide=False)
    for x in (-1.3, 1.3):
        g.box("HayStrap", (0.35, 2.95, 3.1), at(x, 1.47, 0), C("#a8761c"), R=R, collide=False)
    # Wagon wheel leaning against the front of the bale.
    center = at(0.4, 2.0, -2.0)
    Rw = matmul(R, angles(-80, 0, 0))  # wheel plane faces the front, leaning back a little
    g.ring("WheelRim", center, Rw, 1.9, 0.35, [C("#6b4424")], n=16, twist=False)
    for i in range(4):
        t = math.pi * i / 4
        a = add(center, apply(Rw, (1.85 * math.cos(t), 0, 1.85 * math.sin(t))))
        b = add(center, apply(Rw, (-1.85 * math.cos(t), 0, -1.85 * math.sin(t))))
        g.rod("WheelSpoke", a, b, 0.22, C("#6b4424"))
    g.box("WheelHub", (0.7, 0.7, 0.7), center, C("#3a2a20"), R=Rw)


def cactus_planter(g, pos, flower):
    g.octagon("Planter", 1.9, 1.8, add(pos, (0, 0.9, 0)), C("#b07a44"))
    g.octagon("PlanterRim", 2.1, 0.35, add(pos, (0, 1.8, 0)), C("#d4a26d"))
    g.octagon("Soil", 1.7, 0.1, add(pos, (0, 1.85, 0)), C("#7a4a2a"), collide=False)
    g.box("Cactus", (1.4, 5.2, 1.4), add(pos, (0, 4.4, 0)), C("#3f9e4a"))
    for sx, y0, h in ((-1, 3.6, 2.2), (1, 4.6, 1.8)):
        g.box("CactusArm", (1.2, 0.9, 0.9), add(pos, (sx * 1.2, y0, 0)), C("#3f9e4a"))
        g.box("CactusArm", (0.9, h, 0.9), add(pos, (sx * 1.65, y0 + h / 2 - 0.2, 0)), C("#3f9e4a"))
    for x in (-0.3, 0.3):
        g.box("CactusStripe", (0.12, 5.0, 1.42), add(pos, (x, 4.4, 0)), C("#358a40"), collide=False, shadow=False)
    g.box("CactusFlower", (0.7, 0.4, 0.7), add(pos, (0, 7.15, 0)), C(flower), rot=(0, 45, 0), collide=False)


def lantern(g, pos):
    g.box("LanternPost", (0.6, 8.0, 0.6), add(pos, (0, 4.0, 0)), C("#3a2a20"))
    g.box("LanternBase", (1.1, 0.4, 1.1), add(pos, (0, 0.2, 0)), C("#3a2a20"))
    g.box("LanternFrame", (1.8, 0.3, 1.8), add(pos, (0, 8.15, 0)), C("#3a2a20"))
    light = {"class": "PointLight", "name": "Glow",
             "props": {"Color": list(C("#ffd88a")), "Brightness": 1.6, "Range": 18, "Shadows": False}}
    g.box("LanternGlass", (1.3, 1.8, 1.3), add(pos, (0, 9.2, 0)), C("#ffe7a3"), material="Neon", collide=False,
          children=[light])
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.box("LanternBar", (0.18, 1.9, 0.18), add(pos, (sx * 0.7, 9.2, sz * 0.7)), C("#3a2a20"))
    g.box("LanternCap", (1.9, 0.35, 1.9), add(pos, (0, 10.25, 0)), C("#3a2a20"))
    g.box("LanternCap", (1.1, 0.4, 1.1), add(pos, (0, 10.6, 0)), C("#3a2a20"), rot=(0, 45, 0))


def props(g):
    for pos, k in (((-26.0, 0, -6.0), 1.0), ((-23.2, 0, -9.6), 1.0), ((-27.4, 0, -10.2), 0.8)):
        barrel(g, pos, k)
    hay_and_wheel(g, (26.0, 0, -6.0), -20)
    cactus_planter(g, (-22.0, 0, 16.0), "#ff8fb8")
    cactus_planter(g, (22.0, 0, 16.0), "#ffd166")
    lantern(g, (-20.0, 0, -18.0))
    lantern(g, (20.0, 0, -18.0))


# ------------------------------------------------------------------ export ---

def part_instance(p, prefix, i):
    props_ = {
        "Size": [round(v, 4) for v in p["size"]], "CFrame": cframe(p["R"], p["p"]), "Color": list(p["color"]),
        "Material": p["material"], "Anchored": True, "CanCollide": p["collide"], "CanTouch": p["collide"],
        "CanQuery": p["collide"], "CastShadow": p["shadow"], "TopSurface": "Smooth", "BottomSurface": "Smooth",
    }
    if p["transparency"]:
        props_["Transparency"] = p["transparency"]
    if p["reflectance"]:
        props_["Reflectance"] = p["reflectance"]
    if p["shape"] == "ball":
        props_["Shape"] = "Ball"
    elif p["shape"] == "cylinder":
        props_["Shape"] = "Cylinder"
    node = {"class": "WedgePart" if p["shape"] == "wedge" else "Part", "name": p["name"],
            "id": p["id"] or f"{prefix}.{i}", "props": props_, "children": p["children"]}
    if p["paint"]:
        node["attrs"] = {"Paint": p["paint"]}
    return node


def group_instance(g):
    node = {"class": "Model", "name": g.name,
            "children": [part_instance(p, g.name, i) for i, p in enumerate(g.parts)] + g.extra}
    if g.primary:
        node["props"] = {"PrimaryPart": {"ref": g.primary}}
    return node


def build():
    rng = random.Random(5)
    statue, loop, ped, fount, floor, deco = (Group(n) for n in
                                             ("Cowboy", "LassoLoop", "Pedestal", "Fountain", "StarFloor", "Props"))
    hand, hand_pos = cowboy(statue)
    hand["id"] = "Cowboy.HandR"
    hand["children"].append({"class": "Attachment", "name": "RopeStart", "id": "Cowboy.RopeStart",
                             "props": {"CFrame": cframe(IDENTITY, (0, 0.5, 0))}})
    _, honda_pos = lasso(loop, hand_pos)
    stem = {"class": "Beam", "name": "LassoRope", "props": {
        "Attachment0": {"ref": "Cowboy.RopeStart"}, "Attachment1": {"ref": "Lasso.RopeEnd"},
        "Width0": 0.55, "Width1": 0.55, "FaceCamera": True, "Segments": 8, "LightInfluence": 1,
        "Color": [[0, *C("#c99a5b")], [1, *C("#b0824d")]], "Transparency": [[0, 0], [1, 0]],
    }}
    pedestal(ped)
    jets = fountain(fount, rng)
    star_floor(floor)
    props(deco)

    root = {"class": "Part", "name": "Root", "id": "Root",
            "props": {"Size": [1, 0.1, 1], "CFrame": cframe(IDENTITY, (0, 0.05, 0)), "Transparency": 1,
                      "Anchored": True, "CanCollide": False, "CanTouch": False, "CanQuery": False,
                      "CastShadow": False, "PivotOffset": cframe(IDENTITY, (0, -0.05, 0))}}
    style_src = (HERE / "StatueStyle.lua").read_text()
    spin_src = (HERE / "LassoSpin.lua").read_text()
    model = {
        "class": "Model", "name": "WranglerCampStatue",
        "attrs": {"Style": "Painted", "SpinSpeed": 5.0},
        "tags": ["WranglerCampStatue"],
        "props": {"PrimaryPart": {"ref": "Root"}},
        "children": [
            root,
            {"class": "ModuleScript", "name": "StatueStyle", "props": {"Source": style_src}},
            {"class": "Script", "name": "LassoSpin", "props": {"Source": spin_src, "RunContext": "Client"}},
            group_instance(statue), group_instance(loop), stem, group_instance(ped), group_instance(fount),
            group_instance(floor), group_instance(deco),
        ],
    }
    groups = (statue, loop, ped, fount, floor, deco)
    return [model], groups, hand_pos, honda_pos, jets


# ----------------------------------------------------------------- preview ---

def bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))


def preview(groups, hand_pos, honda_pos, jets):
    r = lambda v: [round(x, 3) for x in v]
    vp = lambda n, s, z, cf, c, m="SmoothPlastic", t=0, sh=True: {
        "n": n, "s": s, "z": r(z), "cf": r(cf), "c": r(c), "m": m, "t": t, "r": 0, "st": False, "sh": sh}
    parts = [vp("Plaza", "block", (220, 2, 220), cframe(IDENTITY, (0, -1, 0)), C("#f2b394"), m="Slate")]
    # Plaza tile rings like the game's plaza.
    for rad in (30, 40, 52):
        for i in range(48):
            yaw = 360 * i / 48
            R = angles(0, yaw, 0)
            parts.append(vp("Tile", "block", (2 * math.pi * rad / 48, 0.02, 0.35), cframe(R, apply(R, (0, 0.01, -rad))),
                            C("#ffffff"), sh=False))
    count = 0
    for g in groups:
        for p in g.parts:
            if p["transparency"] >= 1:
                continue
            count += 1
            name = "Plaque" if p["name"] == "Plaque" else f"{p['name']}_{count}"
            parts.append(vp(name, p["shape"], p["size"], cframe(p["R"], p["p"]), p["color"], m=p["material"],
                            t=p["transparency"], sh=p["shadow"]))
    # Beams are not drawn by the viewer: show the rope and the jets as chains of small blocks.
    steps = 10
    for i in range(steps):
        a = add(hand_pos, scale(sub(honda_pos, hand_pos), i / steps))
        b = add(hand_pos, scale(sub(honda_pos, hand_pos), (i + 1) / steps))
        parts.append(vp("Rope", "block", (math.dist(a, b) * 1.05, 0.5, 0.5), cframe(aim(sub(b, a)), scale(add(a, b), 0.5)),
                        C("#c99a5b")))
    for start, a0, end, a1 in jets:
        p1 = add(start, scale(a0, 4.2))
        p2 = sub(end, scale(a1, 3.0))
        pts = [bezier(start, p1, p2, end, i / 24) for i in range(25)]
        for i in range(24):
            a, b = pts[i], pts[i + 1]
            w = 0.9 - 0.3 * i / 24
            parts.append(vp("Jet", "block", (math.dist(a, b) * 1.1, w, w), cframe(aim(sub(b, a)), scale(add(a, b), 0.5)),
                            C("#cdefff"), t=0.1, sh=False))
        for j in range(5):
            ang = 2 * math.pi * j / 5
            parts.append(vp("Splash", "ball", (0.7, 0.7, 0.7), cframe(IDENTITY, add(end, (math.cos(ang) * 0.6, 0.25, math.sin(ang) * 0.6))),
                            C("#ffffff"), sh=False))
    # Grass beds with trees from the forest kit behind the plaza, like in the game.
    try:
        import build_kit
        kit = {a.name: a for a in build_kit.make_kit()}
        rng = random.Random(4)
        for side in (-1, 1):
            parts.append(vp("Grass", "block", (60, 0.6, 26), cframe(IDENTITY, (side * 50, 0.3, 58)), C("#6fd35a"), m="Grass"))
            for i in range(4):
                a = kit[rng.choice(["OakSmall", "OakMedium", "OakMedium"])]
                pos = (side * (30 + i * 13 + rng.uniform(-2, 2)), 0.6, 58 + rng.uniform(-6, 6))
                parts.extend(build_kit.viewer_parts(list(kit.values()), [(a, pos, rng.uniform(0, 360), 1.0)]))
            for i in range(6):
                b = kit[rng.choice(["BushSmall", "FlowerPatch", "FlowerPatch"])]
                pos = (side * rng.uniform(24, 76), 0.6, 58 + rng.uniform(-10, 10))
                parts.extend(build_kit.viewer_parts(list(kit.values()), [(b, pos, rng.uniform(0, 360), 1.0)]))
    except Exception as exc:  # the preview still works without the forest kit
        print("no forest kit trees in the preview:", exc)

    env = {
        "sky": [[0, "#3f9fff"], [0.55, "#96d0ff"], [1, "#dff2ff"]], "fog": ["#dff2ff", 300, 700],
        "sun": {"dir": [-0.5, 1.0, 0.45], "intensity": 2.5}, "hemi": ["#ffffff", "#8fb070", 1.45],
        "bloom": [0.4, 0.5, 0.9],
    }
    texts = [{"part": "Plaque", "lines": [{"text": "WRANGLER CAMP", "color": "#4a2a10", "size": 1, "font": "body",
                                           "stroke": False}], "pad": 0.16}]
    shots = {
        "front": {"camera": {"pos": [-14, 30, -62], "target": [0, 13, 0], "fov": 50},
                  "shadow": {"center": [0, 0, 0], "radius": 50}},
        "top": {"camera": {"pos": [-40, 62, -58], "target": [0, 4, 4], "fov": 55},
                "shadow": {"center": [0, 0, 0], "radius": 60}},
        "close": {"camera": {"pos": [-9, 21, -26], "target": [0, 19, 0], "fov": 50},
                  "shadow": {"center": [0, 0, 0], "radius": 40}},
    }
    return {"env": env, "parts": parts, "models": [], "texts": texts, "sprites": [], "shots": shots}


def main():
    tree, groups, hand_pos, honda_pos, jets = build()
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "statue.json").write_text(json.dumps(tree))
    (out / "world.json").write_text(json.dumps(preview(groups, hand_pos, honda_pos, jets)))
    for g in groups:
        print(f"{g.name:10} {len(g.parts):4} parts")
    print(f"total {sum(len(g.parts) for g in groups)} parts")
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        cmd = ["cargo", "run", "--quiet", "--release", "--manifest-path",
               str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "statue.json"), target]
        if "--rbxmx" in sys.argv:
            cmd.append(sys.argv[sys.argv.index("--rbxmx") + 1])
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
