#!/usr/bin/env python3
"""Concept art of the Dark Woods: the Deep Woods and the Heart, with the 12 Dark Woods animals.

The trees, plants and rocks are the real models from the Critter Woods kit (tools/forest-kit), the animals are
the real models from tools/animal-models/dark_woods.py. The layout of the area itself is a design.

    python3 tools/concept-art/dark_woods_scenes.py
        -> tools/concept-art/build/dark_woods_world.json and tools/animal-models/build/dark_woods.json

Render (see concept-art/README.md): copy both files to tools/viewer/ and run
    node sceneshot.js dark_woods_world.json <shot> out.png      (shots: overview, path, lasso, heart)
"""

import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS / "animal-models"))
sys.path.insert(0, str(TOOLS / "forest-kit"))

from lib import add, angles  # noqa: E402
from build_kit import make_kit, viewer_parts  # noqa: E402
from scenes import L, NEON, RARITY, C, Scene, bezier, hotbar, lasso_loop, model_point, pill, player, rope, \
    toward, top_bar  # noqa: E402

# id, display name, rarity, height (studs) for the label above it.
ANIMALS = {
    "MossbackToad": ("Mossback Toad", "Common", 6), "ShroomSnail": ("Shroom Snail", "Common", 7.5),
    "Duskbat": ("Duskbat", "Uncommon", 9), "NightHedgehog": ("Night Hedgehog", "Uncommon", 6),
    "Glowmoth": ("Glowmoth", "Rare", 10.5), "HollowBadger": ("Hollow Badger", "Rare", 8),
    "Barkling": ("Barkling", "Epic", 9.5), "WispLynx": ("Wisp Lynx", "Legendary", 13),
    "Moonraven": ("Moonraven", "Legendary", 9.5), "UmbraPanther": ("Umbra Panther", "Mythic", 13.5),
    "MosskingElk": ("Mossking Elk", "Mythic", 26.6), "NightshadeDrake": ("Nightshade Drake", "Secret", 23.4),
}

# The path winds north (-Z) from the gate (z = 0) to the Heart.
PATH = [(0, 0), (4, -30), (-14, -62), (-10, -96), (14, -126), (8, -158), (0, -186)]
HEART = (0.0, -240.0)
HEART_R = 52.0
POND = (22.0, -232.0)


def path_points(step=3.0):
    pts = []
    for (x0, z0), (x1, z1) in zip(PATH, PATH[1:]):
        n = max(1, int(math.dist((x0, z0), (x1, z1)) / step))
        for i in range(n):
            t = i / n
            # Smooth the corners a little with a sine ease.
            e = 0.5 - 0.5 * math.cos(math.pi * t)
            pts.append((x0 + (x1 - x0) * e, z0 + (z1 - z0) * t))
    pts.append(PATH[-1])
    return pts


def dist_to_path(x, z, pts):
    return min(math.dist((x, z), p) for p in pts)


def animal(s, aid, pos, yaw, label=True, scale=1.0, lift=0.0):
    s.animal(aid, pos, yaw=yaw, scale=scale)
    if label:
        name, rarity, h = ANIMALS[aid]
        s.label(add(pos, (0, h * scale + 2.6 + lift, 0)), [L(name.upper(), RARITY[rarity]), L(rarity.upper(), "#ffffff", 0.7)],
                h=2.2 * max(1, scale ** 0.5))


def gate(s):
    """The entrance: two big dark trunks with a crossbeam, a hanging sign and lanterns."""
    bark, moss = C("#3e2a1c"), C("#3f8a3c")
    for x in (-13, 13):
        for yaw in (0, 45):
            s.box("GateTrunk", (4.2, 26, 4.2), (x, 13, 0), bark, rot=(0, yaw, 0))
        s.box("GateRoot", (7, 2.4, 7), (x, 1.2, 0), bark, rot=(0, 22, 0))
        s.box("GateMoss", (4.6, 1.2, 4.6), (x, 18, 0), moss, rot=(0, 10, 0))
        s.box("Lantern", (1.4, 1.8, 1.4), (x * 0.78, 16.5, -2.2), C("#9ff0ff"), **NEON)
        s.box("LanternCap", (1.8, 0.4, 1.8), (x * 0.78, 17.6, -2.2), C("#2a2030"))
    s.beam("GateBeam", (-16, 24, 0), (16, 24, 0), 3.2, bark)
    s.beam("GateBeamTop", (-18, 27, 0), (18, 26.4, 0), 2.4, bark)
    for x in (-8, 0, 8):
        s.box("GateVine", (0.6, 3.5 + (x == 0) * 1.5, 0.6), (x + 1.5, 21, -1.4), moss)
    for x in (-6, 6):
        s.beam("SignChain", (x, 22.4, -0.4), (x, 19.5, -0.4), 0.25, C("#8d8d99"))
    s.sign("GateSign", (18, 5.6, 0.8), (0, 16.8, -0.4), "#1d1533",
           [L("DARK WOODS", "#b7a4ff"), L("DEEP WOODS & THE HEART", "#7dffc4", 0.55)], glow=True,
           R=angles(0, 180, 0))


def path(s, pts):
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        length = math.dist((x0, z0), (x1, z1))
        yaw = -math.degrees(math.atan2(z1 - z0, x1 - x0))
        s.box("Path", (length + 1.2, 0.12, 8.5), ((x0 + x1) / 2, 0.06, (z0 + z1) / 2), C("#6b5a44"),
              rot=(0, yaw, 0), material="SmoothPlastic", shadow=False)


def heart(s, rng):
    cx, cz = HEART
    s.cyl("HeartMoss", 0.14, HEART_R * 2, (cx, 0.07, cz), C("#2f6a3a"), R=angles(0, 0, 90), shadow=False)
    # The Heart of Water: a pond with a glowing edge.
    px, pz = POND
    s.cyl("PondRim", 0.3, 30, (px, 0.15, pz), C("#5a6a70"), R=angles(0, 0, 90))
    s.cyl("Pond", 0.4, 27, (px, 0.2, pz), C("#2a6f9a"), R=angles(0, 0, 90), material="Water", transparency=0.1)
    for i in range(14):
        a = i * 2 * math.pi / 14
        s.box("PondGlow", (0.8, 0.3, 0.8), (px + math.cos(a) * 14.6, 0.35, pz + math.sin(a) * 14.6),
              C("#5ef0ff"), rot=(0, rng.uniform(0, 90), 0), **NEON)
    # Moonbeam falling into the clearing.
    for w, t in ((26, 0.95), (15, 0.93)):
        s.cyl("Moonbeam", 90, w, (px - 4, 45, pz - 18), C("#cfd8ff"), R=angles(0, 0, 90), transparency=t, **NEON)


def fireflies(s, rng, n, area, y=(2, 9)):
    (x0, x1), (z0, z1) = area
    for _ in range(n):
        s.box("Firefly", (0.35, 0.35, 0.35), (rng.uniform(x0, x1), rng.uniform(*y), rng.uniform(z0, z1)),
              C(rng.choice(["#fff27a", "#b8ff6a", "#7dffc4"])), rot=(45, 45, 0), **NEON)


def scatter(kit, rng, pts, keep_out):
    """Trees, bushes and ground details of the Deep Woods, all from the kit."""
    placed, out = [], []

    def free(x, z, gap):
        return all(math.dist((x, z), q) >= max(gap, g) for q, g in placed) and \
            all(math.dist((x, z), c) >= r for c, r in keep_out)

    def put(name, x, z, gap, k=None, yaw=None):
        placed.append(((x, z), gap))
        out.append((kit[name], (x, 0.0, z), rng.uniform(0, 360) if yaw is None else yaw,
                    rng.uniform(0.85, 1.2) if k is None else k))

    # Trees: dense everywhere except on the path and in the Heart, taller and darker further in.
    for _ in range(9000):
        x, z = rng.uniform(-205, 205), rng.uniform(-380, 60)
        d = dist_to_path(x, z, pts)
        in_heart = math.dist((x, z), HEART) < HEART_R + 4
        at_gate = z > -14 and abs(x) < 30 + max(0, z) * 1.2
        if d < 12 or in_heart or at_gate or not free(x, z, 13):
            continue
        deep = min(1.0, max(0.0, -z / 200))
        names = ["DeepOak", "DeepPine", "DeepPine", "DeadTree"] if deep > 0.3 else ["DeepOak", "DeepPine", "PineTall"]
        if deep > 0.3 and rng.random() < 0.12:
            names = ["DeadTree"]
        put(rng.choice(names), x, z, 13)
    # Undergrowth.
    for _ in range(6000):
        x, z = rng.uniform(-120, 120), rng.uniform(-300, 30)
        d = dist_to_path(x, z, pts)
        if d < 5.5 or z > -6 or not free(x, z, 4):
            continue
        in_heart = math.dist((x, z), HEART) < HEART_R
        if in_heart and math.dist((x, z), HEART) < HEART_R - 10:
            continue
        name = rng.choice(["Fern", "Fern", "DarkBush", "GlowMushrooms", "MossyRockSmall", "StumpMossy", "Fern",
                           "GlowMushrooms", "MossPatch", "LeafLitter"])
        put(name, x, z, 4)
        if len(out) > 1400:
            break
    # Glowing mushrooms that line the path, so it reads as the way in.
    for i, (x, z) in enumerate(pts[::4]):
        if z > -8:
            continue
        for side in (-1, 1):
            if rng.random() < 0.7:
                ox, oz = side * rng.uniform(5.5, 7.5), rng.uniform(-1.5, 1.5)
                out.append((kit["GlowMushrooms"], (x + ox, 0.0, z + oz), rng.uniform(0, 360), rng.uniform(0.9, 1.3)))
    for name, x, z, yaw in [("FallenLogMossy", -22, -40, 70), ("FallenLogMossy", 26, -112, -20),
                            ("MossyRockLarge", -24, -140, 0), ("MossyRockLarge", 20, -70, 0),
                            ("FallenLogMossy", -30, -168, 40), ("MossyRockLarge", 28, -20, 0)]:
        out.append((kit[name], (x, 0.0, z), yaw, 1.0))
    return out


def lasso_hud():
    return (top_bar(coins="$1,284,900", income="+$42,600/s", speed="118,400")
            + pill("left:50%", "top:20px", 'DARK WOODS <span style="font-size:22px;color:#b7a4ff">DEEP WOODS</span>',
                   30, extra="transform:translateX(-50%)")
            + '<div class="btn game" style="right:60px;bottom:60px;width:150px;height:150px;background:#8a5cff;'
              'display:flex;align-items:center;justify-content:center;text-align:center;font-size:26px">THROW<br>LASSO</div>'
            + hotbar("LASSO"))


def heart_hud():
    return (top_bar(coins="$1,284,900", income="+$42,600/s", speed="118,400")
            + '<div class="game" style="position:absolute;left:50%;top:92px;transform:translateX(-50%);font-size:52px;'
              'color:#ff7be5;white-space:nowrap">A SECRET ANIMAL APPEARED!</div>'
            + '<div class="game" style="position:absolute;left:50%;top:158px;transform:translateX(-50%);font-size:28px;'
              'white-space:nowrap">NIGHTSHADE DRAKE &middot; THE HEART</div>'
            + hotbar("LASSO"))


def build():
    rng = random.Random(5)
    s = Scene("darkwoods", env={
        "sky": [[0, "#0d0b2a"], [0.5, "#2b2160"], [0.85, "#5a3f86"], [1, "#7a5a9a"]],
        "fog": ["#2a2352", 70, 330],
        "sun": {"color": "#c9d4ff", "dir": [0.35, 1.0, 0.55], "intensity": 1.7},
        "hemi": ["#a7b2ff", "#233a2a", 1.15],
        "bloom": [0.85, 0.55, 0.72],
    })
    s.models_file = "dark_woods.json"
    pts = path_points()

    s.box("Ground", (420, 2, 520), (0, -1, -130), C("#2c5a34"), material="Grass")
    path(s, pts)
    gate(s)
    heart(s, rng)

    # ---- animals: rarer ones further in ----
    spots = {
        "MossbackToad": ((-9, 0, -22), 150), "ShroomSnail": ((11, 0, -40), -130),
        "NightHedgehog": ((-20, 0, -76), 120), "Duskbat": ((2, 0, -82), 200),
        "HollowBadger": ((0, 0, -108), -60), "Glowmoth": ((-24, 0, -114), 150),
        "Barkling": ((26, 0, -140), -120), "WispLynx": ((-10, 0, -146), 160),
        "Moonraven": ((20, 0, -172), -150), "UmbraPanther": ((-22, 0, -196), 140),
        "MosskingElk": ((-30, 0, -240), 125), "NightshadeDrake": ((10, 0, -268), 200),
    }
    for aid, (pos, yaw) in spots.items():
        if aid == "NightshadeDrake":
            animal(s, aid, pos, yaw, scale=1.4, lift=2)
        else:
            animal(s, aid, pos, yaw)

    # A player throwing a lasso at the Umbra Panther, and one resting at the pond.
    panther, pyaw = spots["UmbraPanther"]
    thrower = (-2, 0, -176)
    hands = player(s, thrower, toward(thrower, panther), "#8a5cff", "#1f2440", hair="#e8c07a", pose="throw")
    neck = model_point(panther, pyaw, 1, (0, 8.2, -3.0))
    edge = lasso_loop(s, add(neck, (0, 2.0, 0)), 3.0, tilt=(10, 0, -12))
    mid = tuple(v / 2 for v in add(hands["R"], edge))
    rope(s, bezier(hands["R"], add(mid, (0, 11, 0)), edge, 16))
    player(s, (-4, 0, -222), 20, "#45a6ff", "#2b3a6b", hair="#3a2412")

    fireflies(s, rng, 140, ((-60, 60), (-300, -10)))
    fireflies(s, rng, 25, ((-45, 45), (-285, -195)), y=(3, 16))

    kit = {a.name: a for a in make_kit()}
    keep_out = [((x, z), 7) for (x, _, z), _ in spots.values()]
    keep_out += [((-12, -186), 16), ((9, -207), 10), ((38, -190), 16)]  # the lasso throw and the cameras
    placements = scatter(kit, rng, pts, keep_out=keep_out)
    cx, cz = HEART
    placements += [(kit["AncientTree"], (cx - 18, 0.0, cz - 36), 20.0, 1.25),
                   (kit["MushroomRing"], (cx - 16, 0.0, cz - 12), 0.0, 1.6)]
    for x, z in [(POND[0] - 13, POND[1] + 3), (POND[0] + 12, POND[1] - 5), (POND[0] + 4, POND[1] + 13)]:
        placements.append((kit["Reeds"], (x, 0.0, z), rng.uniform(0, 360), 1.0))
    for _ in range(6):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(3, 10)
        placements.append((kit["LilyPad"], (POND[0] + math.cos(a) * r, 0.42, POND[1] + math.sin(a) * r),
                           rng.uniform(0, 360), 1.0))

    # ---- shots ----
    s.shot("overview", (110, 120, 90), (0, 0, -140), fov=52, shadow={"center": [0, 0, -130], "radius": 250},
           env={"fog": ["#2a2352", 240, 620]}, hide_sprites=True)
    s.shot("path", (-2, 9, 34), (-4, 7, -40), fov=58, shadow={"center": [0, 0, -30], "radius": 90},
           hide_sprites=True)
    s.shot("lasso", (9, 8, -207), (-13, 6, -185), fov=60, shadow={"center": [-10, 0, -185], "radius": 80},
           hud=lasso_hud())
    s.shot("heart", (38, 20, -190), (-10, 13, -258), fov=64, shadow={"center": [0, 0, -245], "radius": 90},
           hud=heart_hud())

    world = s.export()
    world["parts"] += viewer_parts(list(kit.values()), placements)
    world["modelsFile"] = s.models_file
    return world, s


def main():
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    world, s = build()
    (out / "dark_woods_world.json").write_text(json.dumps(world))
    print(f"dark woods: {len(world['parts'])} parts, {len(world['models'])} animals, {len(world['shots'])} shots")
    # The animal models the scene uses.
    subprocess.run([sys.executable, str(TOOLS / "animal-models" / "build_dark_woods.py")], check=True,
                   cwd=TOOLS / "animal-models", stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
