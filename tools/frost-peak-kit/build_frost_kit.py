#!/usr/bin/env python3
"""Frost Peak kit: the pieces for the big snowy mountain area, built from Parts.

The look follows the reference picture: grey basalt-column cliffs with thick snow caps, layered pines heavy with
snow, turquoise rivers and frozen lakes with ice floes, waterfalls pouring off the ledges, rope bridges, wooden
fences and warm lantern posts, and a cave tunnel in the mountain.

Made for mid-range phones, like the Dark Woods kit:
  * plain anchored Parts (no meshes, no textures to upload), a small part budget per model;
  * only cliffs, rocks, trunks and wood you walk on collide; plants, snow details, water and effects don't;
  * small parts don't cast shadows, only lanterns, the campfire and the cave have a PointLight;
  * trees and cliffs use Model.LevelOfDetail = StreamingMesh for cheap far-away versions.

    python3 tools/frost-peak-kit/build_frost_kit.py                  -> build/kit.json and build/world.json (preview)
    python3 tools/frost-peak-kit/build_frost_kit.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
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

from lib import add, angles, apply, hex_color, matmul  # noqa: E402
from build_kit import Asset, build_instances, height_of, viewer_parts  # noqa: E402

SPARKLE = "rbxasset://textures/particles/sparkles_main.dds"
SMOKE = "rbxasset://textures/particles/smoke_main.dds"
FIRE = "rbxasset://textures/particles/fire_main.dds"


def C(h):
    return hex_color(h)


ROCK = [C("#5f6584"), C("#6f7596"), C("#8187a6"), C("#979cb8")]
ROCK_DARK = C("#454a66")
ROCK_LIGHT = C("#aeb3cc")
SNOW, SNOW_SHADE, SNOW_BLUE = C("#ffffff"), C("#e4ecf7"), C("#cddcf0")
PINE = [C("#1f6b3a"), C("#2a8046"), C("#349452"), C("#43a860")]
BARK, BARK_DARK = C("#7a4a26"), C("#5a3418")
WATER, WATER_DEEP, WATER_LIGHT = C("#3fc4f0"), C("#1f9be0"), C("#8fe6ff")
ICE, ICE_LIGHT = C("#bff0ff"), C("#e8fbff")
WOOD, WOOD_DARK, WOOD_LIGHT = C("#9a6334"), C("#6e4220"), C("#c48a4e")
ROPE = C("#c9a064")
DIRT = C("#b98a58")
GRASS = [C("#3f9e3a"), C("#58bb43"), C("#74d14c")]
LANTERN = C("#ffc861")

DETAIL = dict(collide=False, shadow=False)
GLOW = dict(material="Neon", collide=False, shadow=False)


def light(color, brightness=1.0, range_=12):
    return {"class": "PointLight", "name": "Glow",
            "props": {"Color": list(C(color)), "Brightness": brightness, "Range": range_, "Shadows": False}}


def emitter(name, color, texture=SPARKLE, rate=4, lifetime=(1, 2), speed=(0.5, 1), spread=180,
            size=((0, 0.5), (1, 0)), transparency=((0, 0.3), (1, 1)), light_=1.0, accel=(0, 0, 0), drag=0,
            color2=None, emit="Top", rot_speed=(-60, 60)):
    color2 = color2 or color
    return {"class": "ParticleEmitter", "name": name, "props": {
        "Texture": texture, "Rate": rate, "Lifetime": list(lifetime), "Speed": list(speed),
        "SpreadAngle": [spread, spread], "LightEmission": light_, "LightInfluence": 0 if light_ else 1,
        "Size": [list(s) for s in size], "Transparency": [list(t) for t in transparency],
        "Color": [[0, *C(color)], [1, *C(color2)]], "Acceleration": list(accel), "Drag": drag,
        "EmissionDirection": emit, "Rotation": [0, 360], "RotSpeed": list(rot_speed)}}


def flow_beam(asset, name, top, bottom, width, color="#e8fbff", speed=1.6):
    """Attachments at the top and bottom of a waterfall, with a Beam whose sparkle texture flows downwards."""
    a0, a1 = f"{asset}.{name}A", f"{asset}.{name}B"
    return [
        {"class": "Attachment", "name": f"{name}Top", "id": a0, "props": {"CFrame": [*top, 0, 0, 1, 0, 1, 0, -1, 0, 0]}},
        {"class": "Attachment", "name": f"{name}Bottom", "id": a1,
         "props": {"CFrame": [*bottom, 0, 0, 1, 0, 1, 0, -1, 0, 0]}},
        {"class": "Beam", "name": name, "props": {
            "Attachment0": {"ref": a0}, "Attachment1": {"ref": a1}, "Width0": width, "Width1": width * 1.1,
            "FaceCamera": False, "Segments": 2, "LightEmission": 0.6, "LightInfluence": 0.4,
            "Texture": SPARKLE, "TextureMode": "Wrap", "TextureLength": 3, "TextureSpeed": speed,
            "Color": [[0, *C(color)], [1, *C(color)]], "Transparency": [[0, 0.35], [1, 0.5]]}},
    ]


# ------------------------------------------------------------ building blocks --

def slab(a, name, size, pos, color, yaw=0.0, **kw):
    a.box(name, size, pos, color, rot=(0, yaw, 0), **kw)


def snow_cap(a, center, w, d, yaw, rng, t=0.7, drips=4, name="Snow"):
    """A thick snow cap on a flat top: a slab that overhangs a little, a softer mound on top and icing that drips
    over the edges."""
    cx, top, cz = center
    slab(a, name, (w + 0.4, t, d + 0.4), (cx, top + t / 2 - 0.05, cz), SNOW, yaw, collide=False)
    slab(a, f"{name}Mound", (w * 0.62, t * 0.7, d * 0.62), (cx + rng.uniform(-0.2, 0.2) * w, top + t + 0.15, cz),
         SNOW, yaw + rng.uniform(15, 35), **DETAIL)
    R = angles(0, yaw, 0)
    for i in range(drips):
        side = rng.choice((0, 1, 2, 3))
        u = rng.uniform(-0.38, 0.38)
        local = {0: (u * w, 0, -(d / 2 + 0.2)), 1: (u * w, 0, d / 2 + 0.2),
                 2: (-(w / 2 + 0.2), 0, u * d), 3: (w / 2 + 0.2, 0, u * d)}[side]
        h = rng.uniform(0.6, 1.6)
        p = add((cx, top, cz), apply(R, local))
        size = (rng.uniform(0.8, 1.6), h, 0.4) if side < 2 else (0.4, h, rng.uniform(0.8, 1.6))
        slab(a, f"{name}Drip", size, add(p, (0, -h / 2 + t * 0.4, 0)), SNOW_SHADE, yaw, **DETAIL)


def column(a, base, w, d, h, rng, yaw=None, snow=True, name="Column"):
    """One basalt column: two stacked blocks with a ledge between them, a facet, dark cracks, and a snow cap."""
    yaw = rng.uniform(0, 90) if yaw is None else yaw
    col = rng.choice(ROCK[1:])
    x, y, z = base
    split = h * rng.uniform(0.45, 0.65)
    a.box(name, (w, split, d), (x, y + split / 2, z), col, rot=(rng.uniform(-3, 3), yaw, rng.uniform(-3, 3)))
    a.box(f"{name}Upper", (w * 0.9, h - split, d * 0.9), (x, y + split + (h - split) / 2, z), rng.choice(ROCK[1:]),
          rot=(rng.uniform(-5, 5), yaw + rng.uniform(-8, 8), rng.uniform(-5, 5)))
    slab(a, f"{name}Ledge", (w * 1.02, 0.5, d * 1.02), (x, y + split, z), ROCK_LIGHT, yaw, **DETAIL)
    if h > 6:
        snow_cap(a, (x, y + split + 0.25, z), w * 0.98, d * 0.98, yaw, rng, t=0.4, drips=1, name=f"{name}LedgeSnow")
    # Chamfer: the same block turned 45 degrees, a little smaller, gives it facets.
    slab(a, f"{name}Facet", (w * 0.8, split * 0.98, d * 0.8), (x, y + split / 2, z), ROCK[0], yaw + 45, **DETAIL)
    R = angles(0, yaw, 0)
    for k, side in enumerate((-1, 1)):
        crack = add((x, y + h * (0.3 + 0.35 * k), z), apply(R, (rng.uniform(-0.3, 0.3) * w, 0, side * (d / 2 + 0.02))))
        slab(a, f"{name}Crack", (0.28, h * 0.32, 0.12), crack, ROCK_DARK, yaw, **DETAIL)
    if h > 7 and rng.random() < 0.6:
        for k in range(3):
            ic = add((x, y + split - 0.1, z), apply(R, ((k - 1) * w * 0.25, 0, -d / 2 - 0.15)))
            ih = rng.uniform(0.8, 1.8)
            a.wedge(f"{name}Icicle", (0.45, ih, 0.3), add(ic, (0, -ih / 2, 0)), ICE, rot=(180, yaw, 0), **DETAIL)
    a.box(f"{name}Frost", (w * 0.91, 0.6, d * 0.91), (x, y + h - 0.3, z), ROCK_LIGHT,
          rot=(0, yaw + rng.uniform(-8, 8), 0), **DETAIL)
    if snow:
        snow_cap(a, (x, y + h, z), w * 0.9, d * 0.9, yaw, rng, drips=3)
    return y + h


def pine_tree(a, rng, h, w, tiers, snow=1.0, x=0.0, z=0.0, name="Pine"):
    """A snowy pine in the style of the forest kit's pines: every layer is a faceted cone of 8 wedges, and snow lies
    on the upper half of each layer (white wedges on the same slopes, a hair above them)."""
    trunk_h = h * 0.16
    a.octo(f"{name}Trunk", (w * 0.13, trunk_h + 1.0, w * 0.13), (x, (trunk_h + 1.0) / 2, z), BARK)
    y = trunk_h
    hgt0 = (h - trunk_h) / (tiers * 0.55 + 0.45)
    for i in range(tiers):
        f = 1 - i / (tiers + 0.6)
        ww = w * f
        hgt = hgt0 * (0.75 + 0.25 * f)
        color = PINE[1] if i < tiers / 3 else PINE[2] if i < 2 * tiers / 3 else PINE[3]
        yaw0 = rng.uniform(0, 90)
        for j, yaw in enumerate((0, 90, 180, 270, 45, 135, 225, 315)):
            R = angles(0, yaw0 + yaw, 0)
            wj = ww if j < 4 else ww * 0.94
            pos = add((x, y + hgt / 2, z), apply(R, (0, 0, -wj / 4)))
            a.wedge(f"{name}Needles", (wj, hgt, wj / 2), pos, color if j < 4 else PINE[0], R=R, collide=False)
            if snow:
                # The same wedge shape scaled down around its top edge covers the top of the slope with snow.
                k = (0.62 if j < 4 else 0.5) * snow
                top_inner = add((x, y + hgt, z), (0, 0.16, 0))
                spos = add(top_inner, apply(R, (0, -hgt * k / 2, -wj * k / 4)))
                a.wedge(f"{name}Snow", (wj * 0.99, hgt * k, wj * k / 2), spos, SNOW if j % 2 == 0 else SNOW_SHADE,
                        R=R, **DETAIL)
        if snow and ww > 2.5:
            # Clumps of snow resting on the tips of the branches.
            for j in range(3):
                ang = math.radians(yaw0 + 45 + j * 120 + rng.uniform(-20, 20))
                p = (x + math.cos(ang) * ww * 0.36, y + hgt * 0.28, z + math.sin(ang) * ww * 0.36)
                a.box(f"{name}SnowClump", (ww * 0.16, hgt * 0.16, ww * 0.12), p, SNOW,
                      rot=(rng.uniform(-15, 15), -math.degrees(ang), rng.uniform(-20, 0)), **DETAIL)
        y += hgt * 0.55
    if snow:
        a.octo(f"{name}TopSnow", (w * 0.12, hgt0 * 0.3, w * 0.12), (x, y + hgt0 * 0.42, z), SNOW, **DETAIL)


def grass_tuft(a, pos, rng, k=1.0):
    for j in range(rng.randint(3, 5)):
        h = rng.uniform(0.6, 1.3) * k
        a.wedge("Grass", (0.25 * k, h, 0.5 * k), add(pos, (rng.uniform(-0.5, 0.5) * k, h / 2, rng.uniform(-0.5, 0.5) * k)),
                rng.choice(GRASS), rot=(rng.uniform(-15, 15), rng.uniform(0, 360), 0), **DETAIL)


def boulder(a, center, s, rng, snow=True, name="Boulder"):
    yaw = rng.uniform(0, 90)
    x, y, z = center
    sx, sy, sz = s
    slab(a, name, (sx, sy, sz), (x, y + sy / 2, z), rng.choice(ROCK[1:]), yaw)
    slab(a, f"{name}Facet", (sx * 0.8, sy * 1.1, sz * 0.8), (x, y + sy * 0.52, z), rng.choice(ROCK), yaw + 40,
         **DETAIL)
    slab(a, f"{name}Top", (sx * 0.6, sy * 0.3, sz * 0.6), (x, y + sy * 1.05, z), ROCK[3], yaw + 20, **DETAIL)
    if snow:
        slab(a, f"{name}Snow", (sx * 0.66, sy * 0.22, sz * 0.66), (x, y + sy * 1.2 + 0.1, z), SNOW, yaw + 20, **DETAIL)


# ---------------------------------------------------------------- assets ---

def trees(rng):
    out = []
    for name, h, w, tiers, note in (("PineSapling", 5, 2.6, 3, "young pine with a little snow"),
                                    ("SnowPineSmall", 10, 5, 4, "small pine heavy with snow"),
                                    ("SnowPine", 16, 7.5, 5, "pine with snow on every layer"),
                                    ("SnowPineLarge", 22, 9.5, 6, "big pine with snow on every layer"),
                                    ("SnowPineTall", 30, 10, 8, "tall narrow pine for the slopes")):
        a = Asset(name, "Trees", "Slopes", note)
        pine_tree(a, rng, h, w, tiers)
        out.append(a)
    a = Asset("PineCluster", "Trees", "Slopes", "three pines growing together, with a snowy rock")
    pine_tree(a, rng, 18, 8, 5, x=-2.5, z=1.0, name="PineA")
    pine_tree(a, rng, 13, 6, 4, x=3.2, z=-1.0, name="PineB")
    pine_tree(a, rng, 8, 4, 3, x=0.5, z=-4.0, name="PineC")
    boulder(a, (2.5, 0, 3.0), (2.4, 1.6, 2.2), rng)
    out.append(a)
    a = Asset("SnowyBush", "Trees", "Valley", "round evergreen bush with a snow cap")
    for j, (x, z, r) in enumerate(((0, 0, 1.6), (1.4, 0.6, 1.1), (-1.2, 0.8, 1.0))):
        a.octo("Bush", (2 * r, r * 1.5, 2 * r), (x, r * 0.75, z), PINE[1 + j % 2], yaw=rng.uniform(0, 45),
               collide=False)
        a.octo("BushSnow", (1.6 * r, r * 0.35, 1.6 * r), (x, r * 1.55, z), SNOW, yaw=rng.uniform(0, 45), **DETAIL)
    out.append(a)
    return out


def cliff(name, note, columns, rng, pines=0, grass=4, zone="Slopes"):
    """A cliff made of basalt columns: list of (x, z, w, d, h)."""
    a = Asset(name, "Cliffs", zone, note)
    tops = []
    for i, (x, z, w, d, h) in enumerate(columns):
        tops.append((x, column(a, (x, 0, z), w, d, h, rng, name=f"Column{i}"), z, w))
    for _ in range(pines):
        x, top, z, w = rng.choice(tops)
        before = len(a.parts)
        pine_tree(a, rng, rng.uniform(5, 8), rng.uniform(2.6, 3.6), 3, x=x, z=z, name="LedgePine")
        for p in a.parts[before:]:   # stand the little pine on top of the column's snow
            p["p"] = add(p["p"], (0, top + 0.6, 0))
    xs = [c[0] for c in columns]
    for _ in range(grass):
        grass_tuft(a, (rng.uniform(min(xs) - 2, max(xs) + 2), 0, rng.uniform(-6, -3)), rng)
    for _ in range(2):
        boulder(a, (rng.uniform(min(xs), max(xs)), 0, rng.uniform(-5.5, -4)), (rng.uniform(1.4, 2.4),) * 3, rng,
                name="FootRock")
    return a


def cliffs(rng):
    out = []
    out.append(cliff("CliffSmall", "low cliff of a few snow-capped columns", [
        (-2.5, 0, 4, 4, 6), (1.2, 0.6, 3.5, 3.8, 8), (4.2, -0.4, 3, 3.4, 5)], rng, grass=3))
    out.append(cliff("CliffMedium", "cliff of basalt columns with snow and a little pine", [
        (-5, 0.5, 4.5, 4.5, 10), (-1, 0, 4, 4.4, 13), (3, 0.6, 4.4, 4, 11), (6.6, -0.2, 3.4, 3.6, 8)], rng,
        pines=1))
    out.append(cliff("CliffLarge", "big cliff wall with ledges, snow and pines", [
        (-8, 0.4, 5, 5, 16), (-3.5, -0.2, 4.6, 5, 20), (1, 0.5, 5, 4.6, 18), (5.5, 0, 4.6, 5, 22),
        (9.6, 0.6, 4, 4.4, 14)], rng, pines=2, grass=6))
    out.append(cliff("CliffTall", "tall cliff for the mountain face", [
        (-4, 0, 5, 5, 26), (0.5, 0.6, 4.6, 5, 32), (4.8, -0.2, 4.6, 4.6, 28)], rng, pines=1))
    out.append(cliff("CliffWall", "long straight cliff wall (24 studs), to line a river or a path", [
        (-10 + i * 4, rng.uniform(-0.6, 0.6), 4.2, 4.6, rng.uniform(10, 14)) for i in range(6)], rng, pines=2,
        grass=6))
    corner = [(math.cos(t) * 9 - 9, math.sin(t) * 9, 4.4, 4.4, rng.uniform(10, 15))
              for t in (math.radians(d) for d in (0, 22, 44, 66, 88))]
    out.append(cliff("CliffCorner", "curved cliff corner (a quarter circle)", corner, rng, pines=1))
    a = Asset("CliffPillar", "Cliffs", "Slopes", "tall rock pillar with a snowy top and a pine")
    column(a, (0, 0, 0), 4.5, 4.5, 18, rng, name="Pillar")
    column(a, (1.5, 0, 1.6), 2.8, 2.8, 12, rng, name="PillarSide")
    before = len(a.parts)
    pine_tree(a, rng, 6, 3.0, 3, name="TopPine")
    for p in a.parts[before:]:
        p["p"] = add(p["p"], (0, 18.6, 0))
    out.append(a)
    # A natural stone arch, like the one over the river in the picture: two legs and a half circle of stones.
    a = Asset("StoneArch", "Cliffs", "Valley", "natural stone arch (18 studs wide) with snow on top")
    column(a, (-9, 0, 0), 5, 5, 10, rng, snow=False, name="ArchLegL")
    column(a, (9, 0, 0), 5, 5, 10, rng, snow=False, name="ArchLegR")
    n = 9
    for i in range(n):
        ang = math.pi * (1 - (i + 0.5) / n)            # from the left leg over the top to the right leg
        cx, cy = math.cos(ang) * 9, 10 + math.sin(ang) * 9
        tilt = math.degrees(ang) - 90
        a.box("ArchStone", (3.6, 4.0, 5.2 + rng.uniform(-0.4, 0.4)), (cx, cy, rng.uniform(-0.2, 0.2)),
              rng.choice(ROCK[1:]), rot=(rng.uniform(-4, 4), 0, tilt))
        if 0.5 < ang < math.pi - 0.5:
            out_x, out_y = math.cos(ang) * 11.1, 10 + math.sin(ang) * 11.1
            a.box("ArchSnow", (3.8, 0.7, 5.6), (out_x, out_y, 0), SNOW, rot=(0, 0, tilt), **DETAIL)
    for k in range(4):
        a.wedge("ArchIcicle", (0.5, rng.uniform(1, 2), 0.3), (rng.uniform(-4, 4), 17.3, rng.uniform(-2, 2)), ICE,
                rot=(180, 0, 0), **DETAIL)
    out.append(a)
    for name, s, note in (("Boulder", (3.2, 2.4, 3.0), "snowy boulder"),
                          ("BoulderLarge", (6, 4.4, 5.4), "big snowy boulder")):
        a = Asset(name, "Cliffs", "Valley", note)
        boulder(a, (0, 0, 0), s, rng)
        grass_tuft(a, (s[0] * 0.6, 0, -s[2] * 0.5), rng)
        out.append(a)
    a = Asset("RockPile", "Cliffs", "Valley", "pile of rocks with snow")
    for x, z, s in ((0, 0, 2.6), (2.2, 0.8, 1.8), (-1.8, 1.2, 1.6), (0.8, -1.8, 1.4), (-0.6, 0.6, 1.2)):
        boulder(a, (x, 0 if s > 1.3 else 1.6, z), (s, s * 0.8, s * 0.9), rng, snow=s > 1.5, name="Pile")
    out.append(a)
    return out


def water(rng):
    out = []
    # Tall waterfall: place it against a cliff, with its top at the cliff's edge.
    a = Asset("WaterfallTall", "Water", "Slopes", "waterfall 24 studs high with a splash pool; put it against a cliff")
    H = 24.0
    a.box("FallBack", (6.0, H, 0.6), (0, H / 2, 0.4), WATER_DEEP, collide=False, shadow=False)
    a.box("Fall", (5.4, H, 0.8), (0, H / 2, 0), WATER, collide=False, shadow=False, transparency=0.15,
          effects=flow_beam("WaterfallTall", "Flow", (0, H / 2, -0.6), (0, -H / 2, -0.6), 5.4))
    for j, x in enumerate((-2.0, -0.7, 0.6, 1.9)):
        a.box("Streak", (0.35, H * rng.uniform(0.6, 0.95), 0.2), (x, H * 0.5, -0.45), WATER_LIGHT, **DETAIL)
    a.box("Lip", (6.4, 0.8, 2.2), (0, H, -0.4), WATER_LIGHT, rot=(-30, 0, 0), **DETAIL)
    a.disc("Pool", 14, 0.5, (0, 0.25, -3.4), WATER, collide=False, shadow=False)
    a.disc("PoolDeep", 8, 0.55, (0, 0.27, -3.0), WATER_DEEP, **DETAIL)
    for j in range(7):
        ang = j * 2 * math.pi / 7
        a.octo("Foam", (rng.uniform(1.4, 2.2),) * 2 + (rng.uniform(1.4, 2.2),),
               (math.cos(ang) * 2.2, 0.6, -1.6 + math.sin(ang) * 1.2), SNOW, yaw=rng.uniform(0, 45), **DETAIL)
    a.parts[-1]["effects"] = [
        emitter("Mist", "#ffffff", texture=SMOKE, rate=6, lifetime=(1.5, 2.5), speed=(1, 3), spread=60,
                size=((0, 2.5), (1, 6)), transparency=((0, 0.6), (1, 1)), light_=0.2, accel=(0, 1, 0)),
        emitter("Spray", "#e8fbff", rate=10, lifetime=(0.6, 1.2), speed=(3, 6), spread=50,
                size=((0, 0.4), (1, 0)), accel=(0, -8, 0))]
    out.append(a)
    # Cascade: water falling over three steps, like the falls in the middle of the picture.
    a = Asset("WaterfallCascade", "Water", "Valley", "wide waterfall over three rock steps (16 studs wide)")
    for i, (y, z) in enumerate(((0, 0), (4, 4), (8, 8))):
        a.box(f"Step{i}", (18, 4, 4.2), (0, y + 2, z + 2), rng.choice(ROCK[1:]))
        a.box(f"StepWater{i}", (15, 0.4, 4.0), (0, y + 4.2, z + 2), WATER, collide=False, shadow=False)
        a.box(f"StepFall{i}", (15, 4.2, 0.6), (0, y + 2.1, z - 0.2), WATER, collide=False, shadow=False,
              transparency=0.1, effects=flow_beam("WaterfallCascade", f"Flow{i}", (0, 2.1, -0.5), (0, -2.1, -0.5), 15,
                                                  speed=1.2))
        for x in (-7.5, 7.5):
            snow_cap(a, (x * 1.12, y + 4, z + 2), 2.6, 4.2, 0, rng, drips=2, name=f"StepSnow{i}")
        for k in range(5):
            a.octo(f"StepFoam{i}", (rng.uniform(1.4, 2.4), 0.8, 1.2), (rng.uniform(-6.5, 6.5), y + 0.4, z - 0.8), SNOW,
                   **DETAIL)
    a.parts[-1]["effects"] = [emitter("Mist", "#ffffff", texture=SMOKE, rate=6, lifetime=(1.5, 2.5), speed=(1, 2),
                                      spread=80, size=((0, 3), (1, 7)), transparency=((0, 0.65), (1, 1)), light_=0.2)]
    out.append(a)
    # River pieces.
    a = Asset("RiverStraight", "Water", "Valley", "straight piece of turquoise river (16 x 32 studs) with snowy banks")
    a.box("Water", (16, 0.6, 32), (0, 0.3, 0), WATER, collide=False, shadow=False)
    a.box("WaterDeep", (8, 0.62, 32), (0, 0.31, 0), WATER_DEEP, **DETAIL)
    for j in range(8):
        a.box("Ripple", (rng.uniform(1.5, 4), 0.1, 0.35), (rng.uniform(-6, 6), 0.66, rng.uniform(-15, 15)), WATER_LIGHT,
              rot=(0, rng.uniform(-10, 10), 0), **DETAIL)
    for side in (-1, 1):
        a.box("Bank", (2.4, 1.2, 32), (side * 9.0, 0.6, 0), SNOW_SHADE, collide=False)
        for j in range(4):
            boulder(a, (side * 8.6, 0, -13 + j * 8.5 + rng.uniform(-2, 2)), (1.6, 1.0, 1.4), rng, name="BankRock")
    out.append(a)
    a = Asset("RiverBend", "Water", "Valley", "river bend (a quarter circle, 16 studs wide)")
    for j in range(7):
        t = (j + 0.5) / 7 * math.pi / 2
        x, z = 16 - math.cos(t) * 16, math.sin(t) * 16
        a.box("Water", (16, 0.6, 4.2), (x - 16, 0.3, z), WATER, rot=(0, -math.degrees(t), 0), collide=False,
              shadow=False)
        a.box("WaterDeep", (8, 0.62, 4.2), (x - 16, 0.31, z), WATER_DEEP, rot=(0, -math.degrees(t), 0), **DETAIL)
        for side in (-1, 1):
            radius = 16 + side * 8.8          # inner and outer bank
            bx, bz = 16 - math.cos(t) * radius, math.sin(t) * radius
            a.box("Bank", (2.4, 1.2, radius * math.pi / 2 / 7 * 1.1), (bx - 16, 0.6, bz), SNOW_SHADE,
                  rot=(0, -math.degrees(t), 0), collide=False)
    out.append(a)
    a = Asset("FrozenLake", "Water", "Valley", "frozen lake (40 studs) with cracks, ice floes and a snowy shore")
    a.disc("Shore", 42, 0.4, (0, 0.2, 0), SNOW_SHADE, collide=False)
    a.disc("Lake", 38, 0.5, (0, 0.27, 0), WATER, collide=False, shadow=False)
    a.disc("LakeDeep", 22, 0.52, (0, 0.28, 0), WATER_DEEP, **DETAIL)
    for j in range(9):
        ang = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(4, 15)
        a.octo("IceFloe", (rng.uniform(2.5, 5), 0.5, rng.uniform(2, 4)), (math.cos(ang) * r, 0.5, math.sin(ang) * r),
               ICE_LIGHT, yaw=rng.uniform(0, 90), **DETAIL)
    for j in range(7):
        a.box("Crack", (rng.uniform(3, 7), 0.06, 0.16), (rng.uniform(-12, 12), 0.55, rng.uniform(-12, 12)), ICE_LIGHT,
              rot=(0, rng.uniform(0, 180), 0), **DETAIL)
    for j in range(8):
        ang = j * 2 * math.pi / 8 + rng.uniform(-0.2, 0.2)
        boulder(a, (math.cos(ang) * 20, 0, math.sin(ang) * 20), (rng.uniform(1.6, 2.6),) * 3, rng, name="ShoreRock")
    out.append(a)
    a = Asset("IceFloes", "Water", "Valley", "a few floating ice floes; put them on any water")
    for j in range(5):
        a.octo("Floe", (rng.uniform(2.4, 4.4), 0.7, rng.uniform(2, 3.6)), (rng.uniform(-4, 4), 0.35, rng.uniform(-4, 4)),
               ICE_LIGHT, yaw=rng.uniform(0, 90), **DETAIL)
        a.octo("FloeTop", (1.6, 0.25, 1.4), (a.parts[-1]["p"][0], 0.8, a.parts[-1]["p"][2]), SNOW, **DETAIL)
    out.append(a)
    a = Asset("Icicles", "Water", "Slopes", "icicles to hang under a ledge or a bridge (pivot at the top)")
    for j in range(8):
        h = rng.uniform(1.2, 3.6)
        x = -3.5 + j
        a.box("IcicleBase", (0.9, 0.3, 0.9), (x, -0.15, 0), ICE_LIGHT, **DETAIL)
        a.wedge("Icicle", (0.6, h, 0.35), (x, -0.3 - h / 2, -0.17), ICE, rot=(180, 0, 0), **DETAIL)
        a.wedge("Icicle", (0.6, h, 0.35), (x, -0.3 - h / 2, 0.17), ICE, rot=(180, 180, 0), **DETAIL)
    out.append(a)
    return out


def wood(rng):
    out = []
    # Rope bridge, 36 studs, sagging between two posts on each end.
    a = Asset("RopeBridge", "Wood", "Valley", "rope bridge 36 studs long; the ends sit on the ground")
    L, sag = 36.0, 2.2
    for i in range(24):
        t = (i + 0.5) / 24
        z = -L / 2 + L * t
        y = 1.2 - sag * math.sin(math.pi * t)
        a.box("Plank", (5.0, 0.35, 1.3), (rng.uniform(-0.15, 0.15), y + 0.6, z), WOOD if i % 3 else WOOD_LIGHT,
              rot=(0, rng.uniform(-4, 4), 0))
    for side in (-1, 1):
        for end in (-1, 1):
            a.octo("Post", (0.7, 5.2, 0.7), (side * 2.8, 2.6, end * (L / 2 + 0.6)), WOOD_DARK)
            a.box("PostCap", (0.9, 0.5, 0.9), (side * 2.8, 5.4, end * (L / 2 + 0.6)), SNOW, **DETAIL)
        prev = None
        for i in range(13):
            t = i / 12
            z = -L / 2 + L * t
            hand = (side * 2.8, 4.8 - sag * 0.8 * math.sin(math.pi * t), z)
            low = (side * 2.6, 1.0 - sag * math.sin(math.pi * t), z)
            if prev:
                a.rod("Rope", prev[0], hand, 0.22, ROPE, octagon=False, **DETAIL)
                a.rod("Rope", prev[1], low, 0.22, ROPE, octagon=False, **DETAIL)
            if 0 < i < 12:
                a.rod("Hanger", hand, low, 0.14, ROPE, octagon=False, **DETAIL)
            prev = (hand, low)
    out.append(a)
    a = Asset("WoodFence", "Wood", "Valley", "wooden fence piece (12 studs) with snow on the rails")
    for x in (-6, 0, 6):
        a.box("FencePost", (0.8, 4.2, 0.8), (x, 2.1, 0), WOOD_DARK)
        a.box("PostSnow", (1.0, 0.4, 1.0), (x, 4.35, 0), SNOW, **DETAIL)
    for y in (1.6, 3.3):
        a.box("Rail", (12.8, 0.55, 0.45), (0, y, 0), WOOD)
        a.box("RailSnow", (rng.uniform(5, 9), 0.25, 0.55), (rng.uniform(-2, 2), y + 0.38, 0), SNOW, **DETAIL)
    grass_tuft(a, (-3, 0, 0.6), rng)
    out.append(a)
    a = Asset("WoodStairs", "Wood", "Slopes", "wooden steps up a slope (8 studs up, 12 long)")
    for i in range(8):
        a.box("Step", (6, 0.5, 1.6), (0, 0.75 + i, -i * 1.5), WOOD if i % 2 else WOOD_LIGHT)
        a.box("StepSnow", (rng.uniform(1.5, 3), 0.15, 1.2), (rng.uniform(-1.5, 1.5), 1.08 + i, -i * 1.5), SNOW, **DETAIL)
    for side in (-1, 1):
        a.rod("Stringer", (side * 3.1, 0.3, 0.8), (side * 3.1, 8.3, -11.3), 0.6, WOOD_DARK, octagon=False)
        for i in (0, 4, 7):
            a.box("RailPost", (0.5, 3, 0.5), (side * 3.1, 2.3 + i, -i * 1.5), WOOD_DARK)
        a.rod("HandRail", (side * 3.1, 3.8, 0), (side * 3.1, 10.8, -10.5), 0.4, WOOD, octagon=False)
    out.append(a)
    a = Asset("SignPost", "Wood", "Valley", "signpost with three arrow boards (write on them with a SurfaceGui)")
    a.box("SignPole", (0.7, 8, 0.7), (0, 4, 0), WOOD_DARK)
    for i, (y, yaw) in enumerate(((6.8, 20), (5.4, -150), (4.0, 70))):
        R = angles(0, yaw, 0)
        a.box(f"Board{i}", (4.2, 1.1, 0.3), add((0, y, 0), apply(R, (2.2, 0, 0))), WOOD_LIGHT, R=R)
        a.wedge(f"BoardTip{i}", (0.3, 1.1, 0.7), add((0, y, 0), apply(R, (4.65, 0, 0))), WOOD_LIGHT,
                R=matmul(R, angles(0, 90, 0)))
        a.box(f"BoardSnow{i}", (3.8, 0.2, 0.36), add((0, y + 0.62, 0), apply(R, (2.2, 0, 0))), SNOW, R=R, **DETAIL)
    a.box("PoleSnow", (0.9, 0.35, 0.9), (0, 8.15, 0), SNOW, **DETAIL)
    out.append(a)
    # Cave tunnel into the mountain, with a timber frame and a warm glow inside.
    a = Asset("CaveEntrance", "Wood", "Peak", "cave tunnel into the mountain (8 studs wide) with a timber frame and a light")
    for i, (x, z, w, d, h) in enumerate(((-8, 0, 6, 8, 16), (8, 0, 6, 8, 17), (-6, 4, 6, 6, 20), (6, 4, 6, 6, 21),
                                         (0, 6, 12, 6, 22))):
        column(a, (x, 0, z), w, d, h, rng, yaw=0, snow=i < 4, name=f"CaveRock{i}")
    a.box("CaveRoof", (10, 6, 8), (0, 13, 0), rng.choice(ROCK[1:]))
    snow_cap(a, (0, 16, 0), 10, 8, 0, rng, drips=6, name="CaveSnow")
    a.box("CaveDark", (8, 10, 0.4), (0, 5, 2.6), C("#1a1424"), collide=False, shadow=False)
    a.box("CaveFloor", (8, 0.3, 6), (0, 0.15, 0), DIRT, collide=False)
    for x in (-3.6, 3.6):
        a.box("TimberPost", (0.9, 10, 0.9), (x, 5, -3.4), WOOD_DARK)
    a.box("TimberBeam", (9, 1.1, 1.1), (0, 10.4, -3.4), WOOD)
    a.box("BeamSnow", (8.4, 0.35, 1.2), (0, 11.1, -3.4), SNOW, **DETAIL)
    a.box("CaveLanternHook", (0.2, 1.2, 0.2), (0, 9.3, -3.4), C("#3a3a44"), **DETAIL)
    a.octo("CaveLantern", (0.9, 1.2, 0.9), (0, 8.2, -3.4), LANTERN, material="Neon", collide=False, shadow=False,
           effects=[light("#ffc861", 1.6, 18)])
    a.octo("CaveGlow", (6, 8, 0.4), (0, 4.6, 2.2), C("#ff9a3a"), material="Neon", collide=False, shadow=False,
           transparency=0.75)
    out.append(a)
    return out


def ground(rng):
    out = []
    a = Asset("SnowPatch", "Ground", "Valley", "flat patch of snow to put over grass or dirt")
    for j in range(6):
        a.octo("Snow", (rng.uniform(3, 6), 0.3, rng.uniform(3, 6)), (rng.uniform(-3, 3), 0.15, rng.uniform(-3, 3)),
               SNOW if j % 2 else SNOW_SHADE, yaw=rng.uniform(0, 45), **DETAIL)
    out.append(a)
    a = Asset("SnowDrift", "Ground", "Slopes", "soft snow drifts")
    for j, (x, z, w, h) in enumerate(((0, 0, 6, 1.6), (3.5, 1.5, 4, 1.1), (-3, 1, 3.6, 0.9), (1, -2.5, 3, 0.8))):
        a.octo("Drift", (w, h, w * 0.8), (x, h / 2, z), SNOW, yaw=rng.uniform(0, 45), collide=False)
        a.octo("DriftTop", (w * 0.6, h * 0.4, w * 0.5), (x + 0.3, h + 0.15, z), SNOW_SHADE, **DETAIL)
    out.append(a)
    a = Asset("GrassTufts", "Ground", "Valley", "green grass poking through the snow")
    for j in range(5):
        grass_tuft(a, (rng.uniform(-3, 3), 0, rng.uniform(-3, 3)), rng, k=rng.uniform(0.9, 1.3))
    out.append(a)
    a = Asset("DirtPath", "Ground", "Valley", "piece of dirt path (12 x 6) with snow along the edges")
    a.box("Path", (12, 0.3, 6), (0, 0.15, 0), DIRT, collide=False)
    for j in range(8):
        side = (-1) ** j
        a.octo("PathSnow", (rng.uniform(1.5, 3), 0.35, rng.uniform(1, 1.6)), (rng.uniform(-5.5, 5.5), 0.2, side * 3),
               SNOW, yaw=rng.uniform(0, 45), **DETAIL)
    for j in range(5):
        a.box("Pebble", (0.5, 0.25, 0.4), (rng.uniform(-5, 5), 0.35, rng.uniform(-2, 2)), ROCK[3],
              rot=(0, rng.uniform(0, 90), 0), **DETAIL)
    out.append(a)
    a = Asset("Pebbles", "Ground", "Valley", "a scatter of small snowy stones")
    for j in range(8):
        s = rng.uniform(0.5, 1.2)
        a.octo("Pebble", (s, s * 0.6, s), (rng.uniform(-3, 3), s * 0.3, rng.uniform(-3, 3)), rng.choice(ROCK),
               yaw=rng.uniform(0, 45), **DETAIL)
        if s > 0.9:
            a.octo("PebbleSnow", (s * 0.6, 0.15, s * 0.6), (a.parts[-1]["p"][0], s * 0.65, a.parts[-1]["p"][2]), SNOW,
                   **DETAIL)
    out.append(a)
    return out


def lights(rng):
    out = []
    a = Asset("LanternPost", "Lights", "Valley", "wooden lantern post with a warm hanging lantern (with a light)")
    a.box("Post", (0.9, 9, 0.9), (0, 4.5, 0), WOOD_DARK)
    a.box("PostFoot", (1.6, 0.8, 1.6), (0, 0.4, 0), ROCK[2])
    a.box("Arm", (3.2, 0.6, 0.6), (1.3, 8.6, 0), WOOD)
    a.box("Brace", (1.6, 0.4, 0.4), (0.7, 7.8, 0), WOOD, rot=(0, 0, 45))
    a.box("ArmSnow", (2.6, 0.25, 0.7), (1.4, 9.0, 0), SNOW, **DETAIL)
    a.box("PostSnow", (1.1, 0.35, 1.1), (0, 9.15, 0), SNOW, **DETAIL)
    a.box("Hook", (0.15, 0.8, 0.15), (2.5, 7.9, 0), C("#3a3a44"), **DETAIL)
    a.box("LanternTop", (1.3, 0.35, 1.3), (2.5, 7.4, 0), C("#3a3a44"), **DETAIL)
    a.octo("Lantern", (1.0, 1.3, 1.0), (2.5, 6.6, 0), LANTERN, material="Neon", collide=False, shadow=False,
           effects=[light("#ffc861", 1.5, 16)])
    a.box("LanternBottom", (1.2, 0.25, 1.2), (2.5, 5.85, 0), C("#3a3a44"), **DETAIL)
    for dx, dz in ((-0.55, 0), (0.55, 0), (0, -0.55), (0, 0.55)):
        a.box("LanternBar", (0.12, 1.3, 0.12), (2.5 + dx, 6.6, dz), C("#3a3a44"), **DETAIL)
    out.append(a)
    a = Asset("Campfire", "Lights", "Valley", "campfire in a ring of stones, with logs to sit on (with a light)")
    for j in range(8):
        ang = j * math.pi / 4
        boulder(a, (math.cos(ang) * 2.2, 0, math.sin(ang) * 2.2), (0.9, 0.7, 0.9), rng, snow=False, name="RingStone")
    for j in range(4):
        a.cyl("FireLog", 3.0, 0.6, (0, 0.5, 0), BARK, R=angles(0, j * 45, 25), **DETAIL)
    a.octo("Embers", (1.6, 0.4, 1.6), (0, 0.3, 0), C("#ff6a1a"), material="Neon", collide=False, shadow=False,
           effects=[light("#ff9a3a", 1.8, 18),
                    emitter("Flames", "#ffd27a", texture=FIRE, rate=18, lifetime=(0.5, 0.9), speed=(2, 4), spread=15,
                            size=((0, 1.6), (1, 0.4)), transparency=((0, 0.2), (1, 1)), color2="#ff5a1a"),
                    emitter("Smoke", "#8a8a96", texture=SMOKE, rate=3, lifetime=(2, 3), speed=(2, 3), spread=15,
                            size=((0, 1), (1, 4)), transparency=((0, 0.6), (1, 1)), light_=0)])
    for ang in (30, 210):
        R = angles(0, ang, 0)
        a.cyl("SeatLog", 4.0, 1.2, apply(R, (0, 0.6, 5.0)), BARK, R=matmul(R, angles(0, 0, 0)))
        a.box("SeatSnow", (2.6, 0.2, 0.8), apply(R, (0, 1.25, 5.0)), SNOW, R=R, **DETAIL)
    out.append(a)
    a = Asset("SnowfallZone", "Lights", "Peak", "invisible box (40 x 40) that makes snow fall; scale it to cover an area")
    a.box("SnowfallZone", (40, 1, 40), (0, 30, 0), SNOW, transparency=1, collide=False, shadow=False,
          effects=[emitter("Snowfall", "#ffffff", rate=40, lifetime=(6, 9), speed=(3, 5), spread=15, emit="Bottom",
                           size=((0, 0.35), (1, 0.25)), transparency=((0, 0.1), (1, 0.4)), light_=0.3,
                           accel=(1, 0, 0), rot_speed=(-90, 90))])
    out.append(a)
    a = Asset("MistPatch", "Lights", "Valley", "low drifting mist (see-through, use a few)")
    for j in range(4):
        a.octo("Mist", (rng.uniform(6, 10), 1.6, rng.uniform(5, 8)), (rng.uniform(-3, 3), 0.9, rng.uniform(-3, 3)),
               SNOW, yaw=rng.uniform(0, 45), collide=False, shadow=False, transparency=0.82)
    out.append(a)
    return out


CATEGORIES = [("Trees", 18.0), ("Cliffs", 30.0), ("Water", 46.0), ("Wood", 46.0), ("Ground", 14.0), ("Lights", 22.0)]
ROW_Z = {"Trees": 0.0, "Cliffs": 44.0, "Water": 104.0, "Wood": 170.0, "Ground": 218.0, "Lights": 238.0}


def make_kit():
    rng = random.Random(42)
    return trees(rng) + cliffs(rng) + water(rng) + wood(rng) + ground(rng) + lights(rng)


def layout(assets):
    spots = {}
    for cat, gap in CATEGORIES:
        row = [a for a in assets if a.category == cat]
        for i, a in enumerate(row):
            y = 8.0 if a.name == "Icicles" else 0.0
            spots[a.name] = ((i - (len(row) - 1) / 2) * gap, y, ROW_Z[cat])
    return spots


def model_props(a):
    return {"LevelOfDetail": "StreamingMesh"} if a.category in ("Trees", "Cliffs") else {}


# ---------------------------------------------------------------- preview --

def preview_world(assets, spots):
    """The catalog, and a mountain valley built from the kit in the spirit of the reference picture."""
    by = {a.name: a for a in assets}
    r = lambda v: [round(x, 3) for x in v]

    def block(name, size, pos, color, rot=0.0, material="SmoothPlastic"):
        R = angles(0, rot, 0)
        return {"n": name, "s": "block", "z": list(size), "cf": r([*pos, *R[0], *R[1], *R[2]]), "c": list(color),
                "m": material, "t": 0, "r": 0, "st": False, "sh": True}

    parts = [block("Ground", (460, 2, 320), (0, -1, 110), C("#c9d6e8"))]
    catalog = [(a, spots[a.name], 0.0, 1.0) for a in assets]
    rng = random.Random(7)
    scene = []
    # The valley: a river running towards the camera between terraces of cliffs, the big mountain behind.
    oz = -260.0
    parts.append(block("ValleyGround", (360, 2, 300), (0, -1, oz), SNOW))
    for z in range(-120, 121, 32):
        scene.append((by["RiverStraight"], (0.0, 0.0, oz + z), 0.0, 1.0))
    scene.append((by["FrozenLake"], (0.0, 0.0, oz - 150), 0.0, 1.6))
    for side in (-1, 1):
        for i, z in enumerate(range(-130, 131, 26)):
            k = rng.uniform(0.9, 1.3)
            scene.append((by[rng.choice(["CliffWall", "CliffMedium", "CliffLarge"])], (side * 26, 0.0, oz + z),
                          90.0 * side + rng.uniform(-10, 10), k))
        # Higher terraces behind.
        for z in range(-140, 141, 34):
            scene.append((by[rng.choice(["CliffLarge", "CliffTall"])], (side * 62, 10.0, oz + z),
                          90.0 * side + rng.uniform(-12, 12), rng.uniform(1.1, 1.5)))
            parts.append(block("Terrace", (40, 12, 36), (side * 70, 5, oz + z), ROCK[1]))
            parts.append(block("TerraceSnow", (40, 1, 36), (side * 70, 11.3, oz + z), SNOW))
    for _ in range(140):
        side = rng.choice((-1, 1))
        x = side * rng.uniform(38, 120)
        z = oz + rng.uniform(-150, 150)
        y = 12.0 if abs(x) > 50 else 0.0
        scene.append((by[rng.choice(["SnowPine", "SnowPineSmall", "SnowPineLarge", "SnowPineTall", "PineCluster"])],
                      (x, y, z), rng.uniform(0, 360), rng.uniform(0.85, 1.25)))
    for _ in range(40):
        side = rng.choice((-1, 1))
        scene.append((by[rng.choice(["SnowyBush", "Boulder", "RockPile", "GrassTufts", "SnowDrift"])],
                      (side * rng.uniform(12, 20), 0.0, oz + rng.uniform(-140, 140)), rng.uniform(0, 360), 1.0))
    # Waterfalls pouring off the terraces, bridges over the river, a path with fences and lanterns.
    for side, z in ((-1, -60), (1, 10), (-1, 80)):
        scene.append((by["WaterfallTall"], (side * 27.5, 0.0, oz + z), -90.0 * side, 0.7))
    scene.append((by["WaterfallCascade"], (0.0, 0.0, oz - 128), 180.0, 1.0))
    for z in (-40, 50):
        scene.append((by["RopeBridge"], (0.0, 0.0, oz + z), 90.0, 1.0))
    scene.append((by["StoneArch"], (0.0, 0.0, oz - 100), 0.0, 1.1))
    for i in range(10):
        z = oz + 120 - i * 14
        scene.append((by["DirtPath"], (17.0, 0.0, z), 90.0, 1.0))
        if i % 2 == 0:
            scene.append((by["WoodFence"], (13.0, 0.0, z), 90.0, 1.0))
        if i % 4 == 1:
            scene.append((by["LanternPost"], (21.0, 0.0, z), 180.0, 1.0))
    # The mountain at the back: stacked cliff rings rising to a snowy peak, with the cave tunnel.
    peak = (0.0, 0.0, oz - 230)
    for ring, (radius, y, n, kind, k) in enumerate(((70, 0, 14, "CliffLarge", 1.5), (52, 20, 12, "CliffTall", 1.3),
                                                     (34, 44, 9, "CliffTall", 1.2), (18, 72, 6, "CliffTall", 1.0))):
        parts.append(block("MountainCore", (radius * 1.9, y + 26, radius * 1.9), (peak[0], (y + 26) / 2, peak[2]),
                           ROCK[ring % 3], rot=ring * 20))
        parts.append(block("MountainSnow", (radius * 1.7, 1.5, radius * 1.7), (peak[0], y + 26.5, peak[2]), SNOW,
                           rot=ring * 20 + 10))
        for j in range(n):
            ang = 2 * math.pi * j / n + ring * 0.3
            scene.append((by[kind], (peak[0] + math.cos(ang) * radius, y, peak[2] + math.sin(ang) * radius),
                          -math.degrees(ang) + 90, k))
    parts.append(block("Summit", (16, 30, 16), (peak[0], 112, peak[2]), ROCK[2], rot=20))
    parts.append(block("SummitSnow", (14, 12, 14), (peak[0], 128, peak[2]), SNOW, rot=65))
    scene.append((by["CaveEntrance"], (24.0, 20.0, oz - 190), 0.0, 1.3))
    scene.append((by["WaterfallTall"], (-14.0, 44.0, oz - 196), 0.0, 1.4))

    parts += viewer_parts(assets, catalog) + viewer_parts(assets, scene)
    env = {"sky": [[0, "#3f8fef"], [0.55, "#86c2ff"], [1, "#d8efff"]], "fog": ["#d8efff", 260, 760],
           "sun": {"dir": [-0.45, 1.0, 0.5], "intensity": 2.6}, "hemi": ["#ffffff", "#9fb4d0", 1.5],
           "bloom": [0.45, 0.5, 0.85]}
    shots = {
        "catalog": {"camera": {"pos": [0, 120, 400], "target": [0, 4, 120], "fov": 50},
                    "shadow": {"center": [0, 0, 120], "radius": 260}, "env": {"fog": ["#d8efff", 500, 1200]}},
        "trees_cliffs": {"camera": {"pos": [0, 42, -60], "target": [0, 6, 30], "fov": 62},
                         "shadow": {"center": [0, 0, 30], "radius": 200}},
        "water_wood": {"camera": {"pos": [0, 60, 40], "target": [0, 2, 150], "fov": 60},
                       "shadow": {"center": [0, 0, 140], "radius": 200}},
        "vista": {"camera": {"pos": [30, 46, oz + 175], "target": [-4, 26, oz - 120], "fov": 62},
                  "shadow": {"center": [0, 0, oz - 40], "radius": 260}},
        "path": {"camera": {"pos": [22, 7, oz + 128], "target": [-6, 6, oz + 40], "fov": 70},
                 "shadow": {"center": [10, 0, oz + 90], "radius": 90}},
        "valley": {"camera": {"pos": [16, 9, oz + 112], "target": [0, 8, oz + 20], "fov": 66},
                   "shadow": {"center": [0, 0, oz + 60], "radius": 140}},
    }
    return {"env": env, "parts": parts, "models": [], "texts": [], "sprites": [], "shots": shots}


def main():
    assets = make_kit()
    names = [a.name for a in assets]
    assert len(names) == len(set(names)), "duplicate asset names"
    spots = layout(assets)
    scatter = (HERE / "FrostPeakScatter.lua").read_text()
    tree = build_instances(assets, spots, scatter, kit_name="FrostPeakKit", scatter_name="FrostPeakScatter",
                           categories=CATEGORIES, model_props=model_props)
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "kit.json").write_text(json.dumps(tree))
    world = preview_world(assets, spots)
    (out / "world.json").write_text(json.dumps(world))
    total = 0
    for a in assets:
        total += len(a.parts)
        print(f"{a.category:7} {a.name:18} {a.zone:7} {len(a.parts):4} parts  {height_of(a):5} studs")
    print(f"{len(assets)} assets, {total} parts")
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cargo", "run", "--quiet", "--release", "--manifest-path",
                        str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "kit.json"), target],
                       check=True)


if __name__ == "__main__":
    main()
