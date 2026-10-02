#!/usr/bin/env python3
"""Frost Peak decal pack: every decoration piece that the Frost Peak area and the Aurora Dragon temple use, each
as its own model (pivot on the ground, front = -Z), sorted into folders, so they can be placed by hand.

    python3 tools/frost-peak-kit/build_frost_decals.py                  -> build/decals.json, build/decals_world.json
    python3 tools/frost-peak-kit/build_frost_decals.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
"""

import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_frost_area as A  # noqa: E402
import dragon_temple as T  # noqa: E402
from build_frost_kit import DETAIL, ROCK, ROCK_LIGHT, SNOW, SNOW_SHADE, Asset, make_kit, pine_tree  # noqa: E402
from build_kit import viewer_parts  # noqa: E402

# Pieces from the Frost Peak kit that the area uses.
KIT_PIECES = {
    "Trees": ["PineSapling", "SnowyBush"],
    "Rocks": ["Boulder", "BoulderLarge", "RockPile"],
    "Water": ["WaterfallTall", "FrozenLake", "IceFloes", "MistPatch"],
    "Paths": ["WoodFence", "RopeBridge", "SignPost", "StoneArch"],
    "Lights": ["LanternPost", "Campfire", "CaveEntrance", "SnowfallZone"],
    "Ground": ["SnowDrift", "GrassTufts", "Pebbles"],
}
ORDER = ["Mountains", "Trees", "Rocks", "Water", "Paths", "Lights", "Ground", "Temple"]
GAP = {"Mountains": 30, "Trees": 16, "Rocks": 16, "Water": 44, "Paths": 40, "Lights": 26, "Ground": 12, "Temple": 22}
ROW_Z = {"Mountains": -110, "Trees": 0, "Rocks": 34, "Water": 80, "Paths": 140, "Lights": 190, "Ground": 228, "Temple": 268}


def piece(name, category, note):
    return Asset(name, category, "Mountain", note)


def snowy_peak(name, R, k, rng):
    """The snowy peak from the top of the mountain on its own: faceted rock with four ridges, a jagged snow
    line and a white cap. R = radius of its foot, k scales the height (k = 1 is about 100 studs)."""
    foot = [(d, A.polar(R * 1.12, d, -1.0)) for d in A.ring_angles(40, rng)]
    rings = [foot] + A.peak_rings(lambda d: R, 0.0, rng, k)
    a = A.facet_asset(name, "Mountains", rings, rng, peak_from=0.0, snow_from=30 * k)
    a.note = f"snowy faceted peak, {102 * k:.0f} studs high and {2 * R:.0f} wide"
    return a


def basalt_cluster(rng, n=5, h=16.0):
    """Basalt columns of different heights standing together, like on the cliffs of the mountain."""
    a = piece("BasaltCluster", "Rocks", "basalt columns with snow on top")
    for k in range(n):
        w = rng.uniform(2.6, 3.8)
        hh = h * rng.uniform(0.55, 1.0)
        x, z = (k - (n - 1) / 2) * 3.2 + rng.uniform(-0.3, 0.3), rng.uniform(-0.8, 0.8)
        yaw = rng.uniform(-12, 12)
        a.box("Column", (w, hh, w * 0.9), (x, hh / 2, z), rng.choice(ROCK[1:]), rot=(rng.uniform(-3, 3), yaw, rng.uniform(-3, 3)))
        a.box("ColumnFacet", (w * 0.75, hh * 0.98, w * 0.75), (x, hh / 2, z), ROCK[0], rot=(0, yaw + 45, 0), **DETAIL)
        a.wedge("ColumnTop", (w * 0.95, 0.9, w * 0.85), (x, hh + 0.45, z), ROCK_LIGHT, rot=(0, yaw + 180 * (k % 2), 0),
                **DETAIL)
        a.box("ColumnSnow", (w * 0.8, 0.5, w * 0.7), (x, hh + 0.55, z), SNOW, rot=(0, yaw + 10, 0), **DETAIL)
    return a


def wood_stairs(rng, h=20.0):
    """The wooden stairs from the mountain, straight: climbing along +X, open side at the front (-Z)."""
    a = piece("WoodStairs", "Paths", f"wooden stairs on posts, {h:.0f} studs high, with a rope railing and a landing")
    run = h / A.STEP_RISE * A.STEP_TREAD

    def at(s, side, y):
        return (s * A.STEP_TREAD - run / 2, y, -side)

    A.stair_flight(a, 0.0, h, at, lambda s: 0.0, 4.0, rng)
    return a


def temple_pieces(rng):
    out = []
    a = piece("DragonTemple", "Temple", "the whole Aurora Dragon temple (upright)")
    a.parts = T.temple(random.Random(77)).parts
    out.append(a)
    a = piece("TemplePillar", "Temple", "lacquered pillar with gold bands and brackets")
    T.pillar(a, 0, 0, rng)
    out.append(T.shift(a, (0, -T.PT, 0)))
    a = piece("TemplePillarBroken", "Temple", "broken pillar with snow in the break")
    T.pillar(a, 0, 0, rng, broken=True)
    out.append(T.shift(a, (0, -T.PT, 0)))
    a = piece("FallenPillar", "Temple", "the top of a pillar lying in the snow")
    T.fallen_pillar(a, rng)
    out.append(T.shift(a, (-5.5, -0.9, 21.5)))
    a = piece("MoonGate", "Temple", "round gold gate full of aurora light (put it in a wall)")
    T.moon_gate(a, (0, 6.4, 0))
    out.append(a)
    a = piece("DragonAltar", "Temple", "round altar with a rune ring, a crystal heart and the DragonSpawn spot")
    T.altar(a, (0, 0, 0), rng)
    out.append(a)
    a = piece("GuardianStatue", "Temple", "coiled stone dragon on a pedestal")
    T.guardian(a, 0, 0, rng)
    out.append(a)
    a = piece("GuardianStatueBroken", "Temple", "the guardian that lost its head")
    T.guardian(a, 0, 0, rng, headless=True)
    out.append(a)
    a = piece("StoneLantern", "Temple", "stone lantern with an aurora flame (with a light)")
    T.stone_lantern(a, (0, 0, 0), rng, 0.15)
    out.append(a)
    a = piece("StoneLanternToppled", "Temple", "a stone lantern that fell over")
    T.stone_lantern(a, (0, 0, 0), rng, 0.5, toppled=True)
    out.append(a)
    for name, t, n, h in (("AuroraCrystalsGreen", 0.15, 6, 7.0), ("AuroraCrystalsBlue", 0.45, 5, 6.0),
                          ("AuroraCrystalsPink", 0.9, 5, 6.0), ("AuroraCrystalsLarge", 0.6, 8, 11.0)):
        a = piece(name, "Temple", "cluster of glowing aurora crystals (with a light)")
        T.crystals(a, (0, 0, 0), rng, n=n, h=h, t=t)
        out.append(a)
    return out


def make_pack():
    rng = random.Random(2027)
    kit = {a.name: a for a in make_kit()}
    pieces = []
    for v, (h, w, tiers) in enumerate(((10, 5, 4), (14, 6.5, 4), (17, 7.5, 5), (22, 9, 5), (28, 9.5, 6))):
        a = piece(f"SnowPine{v + 1}", "Trees", f"snowy pine, {h} studs")
        pine_tree(a, random.Random(100 + v), h, w, tiers, lite=True)
        pieces.append(a)
    pieces.append(snowy_peak("SnowyPeak", 40.0, 1.0, rng))
    pieces.append(snowy_peak("SnowyPeakSmall", 24.0, 0.6, rng))
    pieces.append(basalt_cluster(rng))
    a = piece("Landslide", "Rocks", "faceted heap of rock and snow")
    T.landslide(a, (0, 0, 0), 13.0, 17.0, rng)
    pieces.append(a)
    for name, H, w, stream in (("Waterfall", 22.0, 10.0, 14.0), ("WaterfallWide", 34.0, 16.0, 18.0)):
        a = A.waterfall(name, H, w, stream, rng)
        a.category = "Water"
        pieces.append(a)
    pieces.append(wood_stairs(rng))
    pieces += temple_pieces(rng)
    for cat, names in KIT_PIECES.items():
        for n in names:
            src = kit[n]
            a = piece(n, cat, src.note)
            a.parts = src.parts
            pieces.append(a)
    names = [a.name for a in pieces]
    assert len(names) == len(set(names)), "duplicate piece names"
    return pieces


def main():
    pieces = make_pack()
    folders = {c: [] for c in ORDER}
    spots = []
    for c in ORDER:
        row = [a for a in pieces if a.category == c]
        x = 0.0
        widths = []
        for a in row:
            xs = [p["p"][0] for p in a.parts] or [0]
            widths.append(max(8.0, max(xs) - min(xs) + 6))
        total = sum(widths)
        x = -total / 2
        for a, w in zip(row, widths):
            spots.append((a, (x + w / 2, 0.0, ROW_Z[c] * 1.0)))
            x += w
    for uid, (a, pos) in enumerate(spots):
        node = A.model_node(a, pos, 0.0, 1.0, f"D{uid}", a.category in ("Trees", "Rocks", "Mountains"))
        node["attrs"] = {"Description": a.note}
        folders[a.category].append(node)
    tree = [{"class": "Folder", "name": "FrostPeakDecals", "children": [
        {"class": "Folder", "name": c, "children": folders[c]} for c in ORDER]}]
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "decals.json").write_text(json.dumps(tree))
    for c in ORDER:
        n = sum(len(a.parts) for a in pieces if a.category == c)
        print(f"{c:7} {len(folders[c]):3} pieces {n:6} parts")
    print(f"total {len(pieces)} pieces")

    ground = [{"n": "Ground", "s": "block", "z": [520, 2, 560], "cf": [0, -1, 60, 1, 0, 0, 0, 1, 0, 0, 0, 1],
               "c": list(SNOW_SHADE), "m": "SmoothPlastic", "t": 0, "r": 0, "st": False, "sh": True}]
    parts = ground + viewer_parts([], [(a, pos, 0.0, 1.0) for a, pos in spots if a.name != "SnowfallZone"])
    env = {"sky": [[0, "#3f8fef"], [0.55, "#86c2ff"], [1, "#d8efff"]], "fog": ["#d8efff", 600, 1600],
           "sun": {"dir": [-0.45, 1.0, -0.6], "intensity": 2.6}, "hemi": ["#ffffff", "#8fa3c4", 1.15],
           "bloom": [0.3, 0.45, 0.9]}
    shots = {
        "peaks": {"camera": {"pos": [30, 70, -250], "target": [0, 40, -110], "fov": 55},
                  "shadow": {"center": [0, 0, -110], "radius": 120}},
        "catalog": {"camera": {"pos": [0, 190, -40], "target": [0, 0, 150], "fov": 55},
                    "shadow": {"center": [0, 0, 140], "radius": 260}},
        "nature": {"camera": {"pos": [0, 70, -70], "target": [0, 4, 60], "fov": 60},
                   "shadow": {"center": [0, 0, 60], "radius": 140}},
        "paths": {"camera": {"pos": [0, 60, 95], "target": [0, 6, 170], "fov": 62},
                  "shadow": {"center": [0, 0, 170], "radius": 140}},
        "temple": {"camera": {"pos": [-10, 34, 222], "target": [-10, 6, 268], "fov": 70},
                   "shadow": {"center": [0, 0, 268], "radius": 180}},
    }
    (out / "decals_world.json").write_text(json.dumps({"env": env, "parts": parts, "models": [], "texts": [],
                                                       "sprites": [], "shots": shots}))
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cargo", "run", "--quiet", "--release", "--manifest-path",
                        str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "decals.json"), target],
                       check=True)


if __name__ == "__main__":
    main()
