#!/usr/bin/env python3
"""Concept-art scenes for Create a Zoo: the lobby with the players' zoos and the Wild.

Builds blocky studded scenes with the real animal models placed in them and
writes build/world.json for tools/viewer/scene.html.
"""

import json
import math
import random
import sys
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "animal-models"))

from lib import IDENTITY, Animal, add, angles, apply, cframe, hex_color, matmul, scale, sub  # noqa: E402

RARITY = {
    "Common": "#c9c9c9", "Uncommon": "#62e36e", "Rare": "#45a6ff", "Epic": "#b861ff",
    "Legendary": "#ffcc33", "Mythic": "#ff4a4a", "Secret": "#ff7be5", "Exclusive": "#ffd23a",
}
ANIMALS = {
    "Rabbit": ("Rabbit", "Common", "$1/s"), "Puffhop": ("Puffhop", "Common", "$2/s"),
    "Deer": ("Deer", "Uncommon", "$6/s"), "MossbackTortle": ("Mossback Tortle", "Uncommon", "$10/s"),
    "Boar": ("Boar", "Rare", "$30/s"), "Wolf": ("Wolf", "Rare", "$40/s"),
    "GlowhornStag": ("Glowhorn Stag", "Epic", "$150/s"), "Bear": ("Bear", "Epic", "$200/s"),
    "FrostfangWolf": ("Frostfang Wolf", "Epic", "$300/s"), "EmberbackBoar": ("Emberback Boar", "Epic", "$400/s"),
    "Moonbear": ("Moonbear", "Legendary", "$1.5K/s"), "Sandsnapper": ("Sandsnapper", "Legendary", "$2K/s"),
    "Thunderhoof": ("Thunderhoof", "Legendary", "$2.5K/s"), "CrystalHare": ("Crystal Hare", "Legendary", "$3K/s"),
    "Voidwhisker": ("Voidwhisker", "Mythic", "$15K/s"), "PhoenixFox": ("Phoenix Fox", "Mythic", "$20K/s"),
    "SkyfinWhale": ("Skyfin Whale", "Mythic", "$25K/s"), "StarlightKitsune": ("Starlight Kitsune", "Secret", "$150K/s"),
    "RoyalGriffin": ("Royal Griffin", "Exclusive", "$5K/s"),
}
PEN_SCALE = {"Rabbit": 0.9, "Puffhop": 0.9, "CrystalHare": 0.85, "Sandsnapper": 0.45, "SkyfinWhale": 0.42,
             "RoyalGriffin": 0.58, "Bear": 0.65, "Moonbear": 0.65, "StarlightKitsune": 0.68, "MossbackTortle": 0.8,
             "Thunderhoof": 0.62, "GlowhornStag": 0.62}


def C(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return hex_color(h)


def L(text, color="#ffffff", size=1.0, font=None, **kw):
    return {"text": text, "color": color, "size": size, **({"font": font} if font else {}), **kw}


def polar(bearing, r, y=0.0):
    """Bearing in degrees clockwise from north (-Z)."""
    b = math.radians(bearing)
    return (r * math.sin(b), y, -r * math.cos(b))


class Scene(Animal):
    def __init__(self, name, env):
        super().__init__(name, name, "Scene")
        self.env = env
        self.models, self.texts, self.sprites, self.shots = [], [], [], {}
        self.frames = [(IDENTITY, (0.0, 0.0, 0.0), 0.0)]
        self.count = 0

    @contextmanager
    def frame(self, origin, yaw=0.0):
        """Local coordinates: everything inside is moved to `origin` and turned by `yaw`."""
        R0, o0, y0 = self.frames[-1]
        self.frames.append((matmul(R0, angles(0, yaw, 0)), add(o0, apply(R0, origin)), y0 + yaw))
        try:
            yield
        finally:
            self.frames.pop()

    def world(self, pos):
        R0, o0, _ = self.frames[-1]
        return add(o0, apply(R0, pos))

    def _part(self, shape, name, size, pos, color, rot=None, R=None, **kw):
        if R is None:
            R = angles(*rot) if rot else IDENTITY
        R0, o0, _ = self.frames[-1]
        self.count += 1
        return super()._part(shape, f"{name}_{self.count}", size, add(o0, apply(R0, pos)), color,
                             R=matmul(R0, R), **kw)

    def sign(self, name, size, pos, color, lines, glow=False, bg=None, pad=None, **kw):
        part = self.box(name, size, pos, C(color) if isinstance(color, str) else color, **kw)
        self.texts.append({"part": part["name"], "lines": lines, "glow": glow, **({"bg": bg} if bg else {}),
                           **({"pad": pad} if pad is not None else {})})
        return part

    def label(self, pos, lines, h=2.2, aspect=3.4):
        self.sprites.append({"pos": list(self.world(pos)), "lines": lines, "h": h, "aspect": aspect})

    def animal(self, animal_id, pos, yaw=0.0, scale=1.0, tint=None):
        self.models.append({"id": animal_id, "pos": list(self.world(pos)), "yaw": self.frames[-1][2] + yaw,
                            "scale": scale, **({"tint": tint} if tint else {})})

    def shot(self, name, pos, target, fov=50, shadow=None, env=None, hud=None, hide_sprites=False):
        self.shots[name] = {
            **({"hideSprites": True} if hide_sprites else {}),
            "camera": {"pos": list(pos), "target": list(target), "fov": fov},
            **({"shadow": shadow} if shadow else {}), **({"env": env} if env else {}), **({"hud": hud} if hud else {}),
        }

    def export(self):
        r = lambda v: [round(x, 3) for x in v]
        parts = [{
            "n": p["name"], "s": p["shape"], "z": r(p["size"]), "cf": r(cframe(p["R"], p["p"])), "c": r(p["color"]),
            "m": p["material"], "t": p["transparency"], "r": p["reflectance"], "st": p["studs"], "sh": p["shadow"],
        } for p in self.parts]
        return {"env": self.env, "parts": parts, "models": self.models, "texts": self.texts,
                "sprites": self.sprites, "shots": self.shots}


# ---------------------------------------------------------- props ----

NEON = dict(material="Neon", shadow=False)


def ground(s, size, pos, color, h=2.0):
    s.box("Ground", (size[0], h, size[1]), (pos[0], pos[1] - h / 2, pos[2]), C(color))


def octagon(s, name, r, h, top, color, **kw):
    for yaw in (0, 45):
        s.box(name, (2 * r, h, 2 * r), (0, top - h / 2, 0), C(color), rot=(0, yaw, 0), **kw)


def tree(s, pos, rng, leaf=None, k=1.0, kind="round", snow=False):
    leaf = leaf or rng.choice(["#3fa347", "#4fb84f", "#2f8f3a", "#5cc44a"])
    with s.frame(pos, rng.uniform(0, 90)):
        if kind == "round":
            h = 7 * k
            s.box("Trunk", (1.8 * k, h, 1.8 * k), (0, h / 2, 0), C("#8b5a2b"))
            s.bevel("Leaves", (8 * k, 6 * k, 8 * k), (0, h + 2.2 * k, 0), C(leaf), b=1.4 * k, bottom=0.8 * k)
            s.bevel("LeavesTop", (5 * k, 3.6 * k, 5 * k), (0, h + 6.6 * k, 0), C(leaf), b=1.0 * k, bottom=0.4 * k)
        else:
            h = 4 * k
            s.box("Trunk", (1.6 * k, h, 1.6 * k), (0, h / 2, 0), C("#7a4a24"))
            for i, w in enumerate((9, 7, 5, 3)):
                y = h + 1.2 * k + i * 2.4 * k
                s.box("Tier", (w * k, 2.4 * k, w * k), (0, y, 0), C(leaf))
                if snow and i in (1, 3):
                    s.box("Snow", ((w - 0.6) * k, 0.6 * k, (w - 0.6) * k), (0, y + 1.4 * k, 0), C("#ffffff"))


def bush(s, pos, color, k=1.0):
    s.bevel("Bush", (3.4 * k, 2.4 * k, 3.4 * k), add(pos, (0, 1.2 * k, 0)), C(color), b=0.7 * k)


def flower(s, pos, color, rng):
    s.box("Stem", (0.3, 1.3, 0.3), add(pos, (0, 0.65, 0)), C("#3f8f2f"))
    s.box("Bloom", (1.0, 1.0, 1.0), add(pos, (0, 1.6, 0)), C(color), rot=(0, rng.uniform(0, 90), 45))


def rock(s, pos, size, color, rng, yaw=None):
    s.bevel("Rock", size, add(pos, (0, size[1] / 2, 0)), C(color), b=min(size) * 0.28,
            rot=None, R=angles(0, rng.uniform(0, 90) if yaw is None else yaw, 0))


def fence(s, start, end, color="#ffffff", h=3.0, every=5.0):
    length = math.dist(start, end)
    n = max(1, int(length // every))
    for i in range(n + 1):
        t = i / n
        p = tuple(a + (b - a) * t for a, b in zip(start, end))
        s.box("Post", (0.8, h, 0.8), add(p, (0, h / 2, 0)), C(color))
    for y in (h * 0.45, h * 0.85):
        s.beam("Rail", add(start, (0, y, 0)), add(end, (0, y, 0)), 0.4, C(color))


def player(s, pos, yaw, shirt, pants, skin="#ffd6a5", hair="#4a2c17", pose="idle"):
    """Blocky player. pose: idle, run, drag, throw, bat. Returns the world positions of both hands."""
    legs = {"run": (35, -35), "drag": (30, -30), "throw": (12, -18), "treadmill": (40, -40)}.get(pose, (0, 0))
    arms = {"run": (-40, 40), "treadmill": (-40, 40), "drag": (40, -45), "throw": (70, 160),
            "bat": (105, 105)}.get(pose, (0, 0))
    hands = {}
    with s.frame(pos, yaw):
        for x, th in zip((-0.5, 0.5), legs):
            d = apply(angles(th, 0, 0), (0, -1, 0))
            s.box("Leg", (0.95, 2.0, 1.0), add((x, 2.0, 0), d), C(pants), rot=(th, 0, 0))
        s.box("Torso", (2.0, 2.0, 1.0), (0, 3.0, 0), C(shirt))
        for x, ph, side in zip((-1.5, 1.5), arms, ("L", "R")):
            d = apply(angles(ph, 0, 0), (0, -1, 0))
            shoulder = (x, 3.85, 0)
            s.box("Arm", (1.0, 2.0, 1.0), add(shoulder, d), C(skin), rot=(ph, 0, 0))
            hands[side] = s.world(add(shoulder, scale(d, 2.0)))
        if pose == "bat":
            s.beam("Bat", (1.4, 4.3, -1.9), (2.2, 7.6, -0.5), 0.55, C("#d9a066"))
            s.box("BatKnob", (0.7, 0.3, 0.7), (1.35, 4.05, -2.0), C("#8b5a2b"))
        s.bevel("Head", (1.3, 1.3, 1.3), (0, 4.65, 0), C(skin), b=0.3, bottom=0.3)
        s.box("Hair", (1.4, 0.45, 1.4), (0, 5.35, 0.05), C(hair))
        s.box("HairBack", (1.4, 1.0, 0.35), (0, 4.95, 0.55), C(hair))
        for x in (-0.28, 0.28):
            s.box("PlayerEye", (0.18, 0.32, 0.05), (x, 4.8, -0.66), C("#1b1420"), material="SmoothPlastic",
                  shadow=False)
        s.box("Smile", (0.5, 0.1, 0.05), (0, 4.42, -0.66), C("#1b1420"), material="SmoothPlastic", shadow=False)
    return hands


def loot_beam(s, pos, rarity, h=150.0):
    x, y, z = pos
    if rarity == "Secret":
        for i, col in enumerate(("#ff6b9d", "#ffd84d", "#5ef0d0", "#7f8cff")):
            s.cyl("Beam", h, 1.3, (x + (i % 2 - 0.5) * 1.3, y + h / 2, z + (i // 2 - 0.5) * 1.3), C(col),
                  R=angles(0, 0, 90), transparency=0.35, **NEON)
        return
    color = C(RARITY[rarity])
    s.cyl("Beam", h, 3.2, (x, y + h / 2, z), color, R=angles(0, 0, 90), transparency=0.6, **NEON)
    s.cyl("BeamCore", h, 1.1, (x, y + h / 2, z), color, R=angles(0, 0, 90), transparency=0.25, **NEON)
    s.cyl("BeamRing", 0.2, 9, (x, y + 0.3, z), color, R=angles(0, 0, 90), transparency=0.45, **NEON)


def chest(s, pos, yaw, k=1.0):
    with s.frame(pos, yaw):
        s.box("Chest", (3.2 * k, 2.0 * k, 2.2 * k), (0, 1.0 * k, 0), C("#9c5f2e"))
        s.bevel("ChestLid", (3.3 * k, 1.1 * k, 2.3 * k), (0, 2.5 * k, 0), C("#b8732f"), b=0.4 * k,
                R=angles(0, 90, 0))
        s.box("ChestBand", (3.36 * k, 3.0 * k, 0.35 * k), (0, 1.55 * k, 0), C("#ffcf3a"), reflectance=0.25)
        s.box("ChestLock", (0.6 * k, 0.7 * k, 0.2 * k), (0, 1.9 * k, -1.2 * k), C("#ffe066"), **NEON)


def cloud(s, pos, k, rng):
    for dx, dy, dz, w in ((0, 0, 0, 1.0), (0.55, -0.2, 0.2, 0.7), (-0.6, -0.25, -0.1, 0.75), (0.1, 0.35, 0.3, 0.6)):
        size = (12 * w * k, 7 * w * k, 9 * w * k)
        s.bevel("Cloud", size, add(pos, (dx * 10 * k, dy * 5 * k, dz * 8 * k)), C("#ffffff"), b=2.2 * w * k,
                bottom=1.4 * w * k)


def mountain(s, pos, k, rng, rock_col="#9aa6b8", snow=True):
    with s.frame(pos, rng.uniform(0, 90)):
        tiers = [(40, 16), (29, 14), (18, 12), (9, 8)]
        y = 0
        for i, (w, h) in enumerate(tiers):
            s.bevel("Mountain", (w * k, h * k, w * k), (0, y + h * k / 2, 0), C(rock_col), b=min(3.5, w * 0.12) * k)
            if snow and i >= 1:
                s.bevel("MountainSnow", ((w - 3) * k, 1.6 * k, (w - 3) * k), (0, y + h * k + 0.4, 0), C("#ffffff"),
                        b=0.6 * k)
            y += h * k


def mesa(s, pos, k, rng):
    with s.frame(pos, rng.uniform(0, 90)):
        layers = [(34, 9, "#c9643a"), (30, 7, "#e07b3c"), (26, 8, "#c9643a"), (22, 5, "#f0a15a")]
        y = 0
        for w, h, col in layers:
            s.bevel("Mesa", (w * k, h * k, w * 0.8 * k), (0, y + h * k / 2, 0), C(col), b=1.2 * k)
            y += h * k


def island(s, pos, size, rng, trees=1):
    with s.frame(pos, rng.uniform(0, 90)):
        s.bevel("IslandTop", (size, 3.5, size), (0, 0, 0), C("#7ad35a"), b=size * 0.1)
        y = -3.7
        for w in (0.86, 0.62, 0.38, 0.16):
            s.box("IslandRock", (size * w, 4.2, size * w), (0, y, 0), C("#8b5a2b" if w > 0.5 else "#6e4521"))
            y -= 4.2
        for _ in range(trees):
            tree(s, (rng.uniform(-size / 4, size / 4), 1.7, rng.uniform(-size / 4, size / 4)), rng, k=0.8)
        for _ in range(4):
            flower(s, (rng.uniform(-size / 3, size / 3), 1.7, rng.uniform(-size / 3, size / 3)),
                   rng.choice(["#ff7ac8", "#ffd23f", "#ffffff"]), rng)


def crystal(s, pos, h, color, rng):
    s.shard("Crystal", pos, h * 0.28, h, C(color), R=angles(rng.uniform(-18, 18), rng.uniform(0, 90),
                                                             rng.uniform(-18, 18)),
            material="Glass", transparency=0.15, reflectance=0.2)
    s.box("CrystalCore", (h * 0.1, h * 0.55, h * 0.1), add(pos, (0, h * 0.3, 0)), C(color), **NEON)



# ------------------------------------------------- Create a Zoo props ----

ROPE = "#c9a064"
GOLD = [1.0, 0.8, 0.2]


def bezier(p0, p1, p2, n):
    return [tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2))
            for t in (i / n for i in range(n + 1))]


def rope(s, points, thickness=0.42):
    for a, b in zip(points, points[1:]):
        s.beam("Rope", a, b, thickness, C(ROPE), material="SmoothPlastic", shadow=False)


def lasso_loop(s, center, radius, tilt=(0, 0, 0), n=12, thickness=0.32):
    R = angles(*tilt)
    pts = [add(center, apply(R, (radius * math.cos(2 * math.pi * i / n), 0, radius * math.sin(2 * math.pi * i / n))))
           for i in range(n + 1)]
    rope(s, pts, thickness)
    return pts[n // 4]


def model_point(pos, yaw, k, local):
    return add(pos, apply(angles(0, yaw, 0), scale(local, k)))


def toward(src, dst):
    """Yaw that makes a model at `src` face `dst` (models face -Z)."""
    dx, dz = dst[0] - src[0], dst[2] - src[2]
    return -math.degrees(math.atan2(dx, -dz))


def treadmill(s, pos, yaw, runner=None, screen="+1 SPEED"):
    with s.frame(pos, yaw):
        s.box("TreadBase", (4.4, 1.0, 10), (0, 0.5, 0), C("#3a3f4a"))
        s.box("TreadBelt", (3.4, 0.3, 9.4), (0, 1.15, 0), C("#1b1b22"))
        for z in (-3, -1, 1, 3):
            s.box("TreadStripe", (3.42, 0.3, 0.3), (0, 1.16, z), C("#44ff88"), **NEON)
        for x in (-2.1, 2.1):
            s.box("TreadRail", (0.35, 3.6, 0.35), (x, 2.8, -3.8), C("#8d8d99"))
            s.beam("TreadHandle", (x, 4.3, -3.8), (x, 4.3, -1.0), 0.35, C("#8d8d99"))
        s.box("TreadConsole", (4.4, 0.4, 1.2), (0, 4.6, -4.0), C("#8d8d99"))
        s.sign("TreadScreen", (3.8, 1.9, 0.5), (0, 5.8, -4.0), "#10203a", [L(screen, "#44ff88")], glow=True)
        if runner:
            player(s, (0, 1.3, 0.6), 0, runner, "#2b3a6b", hair="#3a2412", pose="treadmill")
            s.label((0, 12, 0), [L("+1 SPEED", "#44ff88")], h=1.8, aspect=3.4)


def bear_trap(s, pos, yaw=0):
    with s.frame(pos, yaw):
        s.cyl("TrapBase", 0.3, 3.4, (0, 0.2, 0), C("#6d6d7a"), R=angles(0, 0, 90), reflectance=0.3)
        s.box("TrapPlate", (1.2, 0.3, 1.2), (0, 0.45, 0), C("#b8b8c4"), reflectance=0.3)
        for sgn in (-1, 1):
            s.box("TrapJaw", (3.6, 1.0, 0.3), (0, 0.8, sgn * 1.3), C("#8d8d99"), rot=(sgn * 35, 0, 0), reflectance=0.3)
            for x in (-1.2, 0, 1.2):
                s.tri("TrapTooth", (x, 1.25, sgn * 1.05), 0.5, 0.55, 0.2, C("#d6d6de"), R=angles(sgn * 35, 0, 0),
                      material="SmoothPlastic", shadow=False)


def bat_item(s, pos, rot):
    with s.frame(pos, rot[1]):
        s.beam("Bat", (0, 0, 0), (0, 3.2, 0.3), 0.55, C("#d9a066"))


def enclosure(s, x, z, color, aid=None, tint=None, income=None, plus=True, rng=None):
    s.box("EncFloor", (17, 0.4, 17), (x, 1.5, z), C("#9fdc7f"))
    for dz in (-8.25, 8.25):
        s.box("EncFence", (17, 1.6, 0.6), (x, 2.5, z + dz), C("#ffffff"))
    for dx in (-8.25, 8.25):
        s.box("EncFence", (0.6, 1.6, 17), (x + dx, 2.5, z), C("#ffffff"))
    for dx in (-8.25, 8.25):
        for dz in (-8.25, 8.25):
            s.box("EncPost", (1.0, 2.6, 1.0), (x + dx, 3.0, z + dz), C(color))
    s.box("Trough", (4, 1, 1.6), (x + 5.5, 2.2, z + 6), C("#8b5a2b"))
    s.box("TroughWater", (3.4, 0.2, 1.1), (x + 5.5, 2.75, z + 6), C("#4fb7ff"), material="Water", transparency=0.1)
    s.box("CollectPad", (4, 0.3, 2.2), (x - 4, 1.85, z - 6), C("#ffcf3a"), **NEON)
    if aid:
        name, rarity, inc = ANIMALS[aid]
        s.animal(aid, (x, 1.7, z + 0.5), yaw=(rng.uniform(-30, 30) if rng else 0), scale=PEN_SCALE.get(aid, 0.72),
                 tint=tint)
        label = ("GOLDEN " + name) if tint else name
        s.label((x, 13, z), [L(label, "#ffd23a" if tint else RARITY[rarity]), L(income or inc, "#5dff7a", 0.8)],
                h=1.9, aspect=4.6)
        if plus:
            s.label((x + 3.5, 9, z - 4), [L("+" + (income or inc).replace("/s", ""), "#ffd84a")], h=1.8, aspect=2.6)


ZOOS = [
    # (side, z, owner, color, animals)
    (-1, 60, "LunaPlayz", "#ff7ac8", ["Sandsnapper", "Thunderhoof", "Moonbear", "FrostfangWolf", "Wolf", "Bear"]),
    (1, 60, "Noob_123", "#52d273", ["Rabbit", "Puffhop", "Deer"]),
    (-1, 125, "StarQueen", "#ffd23f", ["StarlightKitsune", "RoyalGriffin", "SkyfinWhale", "Voidwhisker", "CrystalHare",
                                       "PhoenixFox"]),
    (1, 125, "xXFoxXx", "#ff9a3c", ["Wolf", "Boar", "Deer", "MossbackTortle"]),
    (-1, 190, "Builder_Bob", "#a66bff", ["Voidwhisker", "Bear", "Wolf", "Rabbit", "Boar"]),
    (1, 190, "ChrisHunter", "#4f9dff", ["PhoenixFox", "Thunderhoof", "GlowhornStag", "EmberbackBoar", "Boar",
                                        "MossbackTortle"]),
    (-1, 255, None, "#bfc6d1", []),
    (1, 255, "LilPanda", "#3fe0e0", ["Puffhop", "Rabbit", "MossbackTortle", "Deer"]),
]
MY_ZOO = 5


def zoo(s, owner, color, animals, rng, mine=False):
    """A player's zoo in local space: the gate (and treadmill) face -Z, towards the avenue."""
    wall = C(color)
    s.box("ZooBase", (58, 1, 64), (0, 0.5, 0), C("#f3e6c6"))
    s.box("ZooWall", (58, 3, 1.5), (0, 2.5, 31.25), wall)
    for x in (-28.25, 28.25):
        s.box("ZooWall", (1.5, 3, 64), (x, 2.5, 0), wall)
    for x in (-18, 18):
        s.box("ZooWall", (22, 3, 1.5), (x, 2.5, -31.25), wall)
    for x in (-7.5, 7.5):
        s.bevel("ZooGatePost", (2.6, 11, 2.6), (x, 6.5, -31.25), C("#ffffff"), b=0.5)
    if owner is None:
        s.sign("ZooSign", (18, 3.4, 1), (0, 12.2, -31.25), wall, [L("EMPTY ZOO")])
        s.box("ZooGrass", (52, 0.3, 58), (0, 1.15, 0), C("#9bd67e"))
        s.label((0, 7, 0), [L("CLAIM ME!", "#ffffff")], h=3)
        return
    s.sign("ZooSign", (18, 3.4, 1), (0, 12.2, -31.25), wall, [L(f"{owner}'s Zoo")])
    s.box("ZooGrass", (52, 0.3, 58), (0, 1.15, 0), C("#86d06a"))
    s.box("SignPost", (0.8, 6, 0.8), (-13, 3.5, -35), C("#8b5a2b"))
    s.sign("LevelSign", (8.5, 3.6, 0.6), (-13, 7.4, -35), "#ffffff",
           [L(f"ZOO LVL {3 + len(animals) // 2}", "#4f9dff", 0.9), L(f"{len(animals)}/8 ANIMALS", "#3a2a22", 0.8)])
    spots = [(-18, -12), (0, -12), (18, -12), (-18, 12), (0, 12), (18, 12)]
    for i, (x, z) in enumerate(spots):
        aid = animals[i] if i < len(animals) else None
        if mine and i == 1:
            enclosure(s, x, z, color, "Thunderhoof", tint=GOLD, income="$5K/s", plus=False, rng=rng)
            continue
        enclosure(s, x, z, color, aid, plus=rng.random() < 0.5, rng=rng)
    treadmill(s, (19, 0, -39), 90, runner="#ff5a5a" if mine else rng.choice(["#45a6ff", "#ffd23f", "#3fdc5a", None]))


def shop(s, title, color, items):
    s.box("ShopFloor", (26, 1, 18), (0, 0.5, 0), C("#caa472"))
    s.box("ShopBack", (26, 12, 2), (0, 7, 8), C("#fff1d6"))
    for x in (-12, 12):
        s.box("ShopSide", (2, 12, 18), (x, 7, 0), C("#fff1d6"))
    s.box("ShopRoof", (28, 1.5, 20), (0, 13.7, 0), C(color))
    for i in range(7):
        s.wedge("Awning", (4, 3, 5), (-12 + 4 * i, 11.5, -11.4), C(color if i % 2 == 0 else "#ffffff"))
    s.sign("ShopSign", (20, 4.5, 1), (0, 17.2, -3), color, [L(title)])
    s.box("Counter", (20, 4, 3), (0, 3, -6), C("#9c6b3f"))
    s.box("CounterTop", (21, 0.5, 3.4), (0, 5.2, -6), C("#fff1d6"))
    for x, kind in items:
        if kind == "lasso":
            with s.frame((x, 6.0, -6)):
                lasso_loop(s, (0, 0, 0), 1.1, tilt=(90, 0, 0), n=10, thickness=0.3)
        elif kind == "bat":
            s.beam("Bat", (x - 0.8, 5.5, -6), (x + 0.8, 7.8, -6), 0.5, C("#d9a066"))
        elif kind == "trap":
            s.box("TrapIcon", (2.2, 0.5, 2.2), (x, 5.75, -6), C("#8d8d99"), reflectance=0.3)
        else:
            s.box("Potion", (1.2, 1.8, 1.2), (x, 6.4, -6), C(kind), material="Glass", transparency=0.1)
    player(s, (0, 1, -2), 0, "#ffffff", "#333", hair="#6a3")


def lobby(s, rng):
    ground(s, (5000, 5000), (0, 0, 0), "#72c255")
    s.box("Avenue", (40, 0.5, 330), (0, 0.25, 170), C("#e9dcb8"))
    for x in (-20.5, 20.5):
        s.box("AvenueEdge", (1.2, 0.7, 330), (x, 0.35, 170), C("#c9b98f"))

    for i, (side, z, owner, color, animals) in enumerate(ZOOS):
        with s.frame((62 * side, 0, z), 90 * side):
            zoo(s, owner, color, animals, rng, mine=i == MY_ZOO)

    # Arch into the Wild, with the respawn clock.
    with s.frame((0, 0, 18), 180):
        for x in (-26, 26):
            s.bevel("ArchPillar", (9, 38, 9), (x, 19, 0), C("#8b5a2b"), b=1.5)
            s.bevel("ArchCap", (11, 3, 11), (x, 39.5, 0), C("#3fa347"), b=0.8)
        s.bevel("ArchBeam", (62, 8, 10), (0, 36, 0), C("#6b4226"), b=1.5)
        s.sign("ArchName", (40, 5, 0.6), (0, 36, -5.3), "#4a2e18", [L("TO THE WILD", "#ffd84a")])
        s.box("ClockFrame", (40, 15, 2.4), (0, 49, 0.6), C("#f2c14e"), reflectance=0.2)
        s.sign("Clock", (36, 12.5, 3), (0, 49, 0), "#1d2033",
               [L("ANIMALS RESPAWN IN", "#ffffff", 0.7), L("2:34", "#ffe14a", 1.35)], glow=True)
        for x in (-20, 20):
            s.box("Vine", (1.4, 20, 0.6), (x + (6 if x < 0 else -6), 26, -4.9), C("#3fa347"))

    # "Create a Zoo" arch over the avenue near spawn, facing the players who spawn south of it.
    with s.frame((0, 0, 300), 180):
        for x in (-17, 17):
            s.bevel("LogoPillar", (5, 22, 5), (x, 11, 0), C("#ffffff"), b=1)
        s.box("LogoBoard", (44, 13, 2), (0, 25, 0.8), C("#3fa347"))
        s.sign("Logo", (40, 11, 1.2), (0, 25, 0), "#2f8f3a",
               [L("CREATE A", "#ffffff", 0.8), L("ZOO!", "#ffd23f", 1.35)])
        for x in (-22, 22):
            s.tri("LogoLeaf", (x, 30, 0.5), 8, 7, 2, C("#58c44a"), R=angles(0, 0, 25 if x > 0 else -25))
    octagon(s, "Spawn", 12, 0.6, 0.9, "#ffffff")
    for k in range(8):
        a = math.radians(45 * k)
        s.box("SpawnGlow", (2, 0.3, 2), (9 * math.cos(a), 1.0, 320 + 9 * math.sin(a)), C("#6fe8ff"), **NEON)
    s.box("SpawnCenter", (8, 0.3, 8), (0, 1.0, 320), C("#6fe8ff"), rot=(0, 45, 0), **NEON)

    with s.frame((-50, 0, 318), -90):
        shop(s, "LASSO SHOP", "#e0473c", [(-7, "lasso"), (-2.5, "lasso"), (2.5, "#3fdc5a"), (7, "lasso")])
    with s.frame((50, 0, 318), 90):
        shop(s, "GEAR SHOP", "#4f9dff", [(-7, "bat"), (-2.5, "trap"), (2.5, "bat"), (7, "#b861ff")])

    for x, z, shirt, pose in [(-8, 150, "#ff7ac8", "run"), (6, 95, "#52d273", "idle"), (-4, 40, "#ffd23f", "run"),
                              (10, 230, "#45a6ff", "idle"), (-12, 280, "#3fe0e0", "idle"), (3, 312, "#ff9a3c", "idle")]:
        player(s, (x, 0.5, z), rng.uniform(150, 210) if pose == "run" else rng.uniform(0, 360), shirt, "#2b3a6b",
               hair=rng.choice(["#3a2412", "#111", "#e8c07a"]), pose=pose)

    for _ in range(80):
        x = rng.choice([-1, 1]) * rng.uniform(110, 260)
        z = rng.uniform(-10, 420)
        tree(s, (x, 0, z), rng, k=rng.uniform(1.0, 1.5), kind=rng.choice(["round", "round", "pine"]))
    for _ in range(30):
        tree(s, (rng.uniform(-100, 100), 0, rng.uniform(345, 440)), rng, k=rng.uniform(1.0, 1.4))


# ------------------------------------------------------------ the Wild ----

BIOMES = [
    # name, speed, ground, wall, guardian (id, scale), herd
    ("SUNNY MEADOW", "NO SPEED NEEDED", "#86d45f", "#4fa63a", ("Boar", 3.2),
     ["Rabbit", "Rabbit", "Puffhop", "Puffhop", "Deer"]),
    ("WHISPERING FOREST", "900 SPEED", "#4f9d3a", "#2f7a2f", ("Bear", 2.9),
     ["Wolf", "Wolf", "Wolf", "MossbackTortle", "GlowhornStag"]),
    ("SCORCHED DESERT", "10K SPEED", "#f2cf6b", "#d9a441", ("Sandsnapper", 2.7),
     ["Thunderhoof", "Sandsnapper", "Boar"]),
    ("FROSTPEAK", "40K SPEED", "#eef5ff", "#cfe6ff", ("FrostfangWolf", 2.9), ["Bear", "Moonbear", "FrostfangWolf"]),
    ("VOLCANO", "250K SPEED", "#4a3a3a", "#2e2528", ("EmberbackBoar", 3.1), ["EmberbackBoar", "PhoenixFox"]),
    ("CRYSTAL CAVERNS", "1M SPEED", "#5d5775", "#3e3854", ("Voidwhisker", 2.8), ["CrystalHare", "Voidwhisker"]),
    ("SKY ISLES", "700M SPEED", "#9fdcff", None, ("SkyfinWhale", 1.5), ["StarlightKitsune"]),
]
HEIGHT = {"Boar": 7.5, "Bear": 11.5, "Sandsnapper": 8.5, "FrostfangWolf": 11, "EmberbackBoar": 7.5,
          "Voidwhisker": 11}
DEPTH = 170
WIDTH = 230


def biome_z(i):
    """Front (south) edge of biome i; biomes run north (-Z) from the lobby arch."""
    return -10 - DEPTH * i


def speed_gate(s, z, name, speed, wall, glow):
    with s.frame((0, 0, z), 180):
        for x in (-WIDTH / 4 - 9, WIDTH / 4 + 9):
            s.bevel("GateWall", (WIDTH / 2 - 18, 12, 6), (x, 6, 0), C(wall), b=1.5)
        for x in (-18, 18):
            s.bevel("GatePillar", (6, 24, 6), (x, 12, 0), C("#ffffff"), b=1)
        s.box("GateBeam", (42, 4, 5), (0, 23, 0), C("#ffffff"))
        s.sign("GateSign", (34, 8, 1), (0, 29, 0), "#1d2033",
               [L(name, "#ffffff", 0.9), L(speed + (" RECOMMENDED" if "SPEED" in speed and "NO" not in speed else ""),
                                              "#ffd84a", 0.8)], glow=True)
        s.box("SpeedBarrier", (30, 20, 0.4), (0, 10.5, 0), C(glow), transparency=0.72, material="Glass",
              shadow=False)


def herd(s, center, ids, rng, spread=26):
    spots = []
    for i, aid in enumerate(ids):
        a = 2 * math.pi * i / max(1, len(ids)) + rng.uniform(-0.3, 0.3)
        p = add(center, (math.cos(a) * spread * rng.uniform(0.7, 1.0), 0.4, math.sin(a) * spread * 0.6))
        s.animal(aid, p, yaw=rng.uniform(0, 360))
        spots.append(p)
    return spots


def guardian(s, pos, aid, k, face):
    s.animal(aid, pos, yaw=toward(pos, face), scale=k)
    s.cyl("GuardianZone", 0.2, 70, add(pos, (0, 0.35, 0)), C("#ff3b3b"), R=angles(0, 0, 90), transparency=0.8, **NEON)


def wild(s, rng):
    for i, (name, speed, ground_col, wall, (gid, gk), ids) in enumerate(BIOMES):
        z0 = biome_z(i)
        zc = z0 - DEPTH / 2
        if name != "SKY ISLES":
            s.box("BiomeGround", (WIDTH + 20, 0.6, DEPTH), (0, 0.3, zc), C(ground_col))
            for x in (-WIDTH / 2 - 8, WIDTH / 2 + 8):
                s.bevel("BiomeWall", (14, 26, DEPTH), (x, 13, zc), C(wall), b=3)
        glow = {"SUNNY MEADOW": "#8cff7a", "WHISPERING FOREST": "#8cff7a", "SCORCHED DESERT": "#ffcf5a",
                "FROSTPEAK": "#8fe9ff", "VOLCANO": "#ff7a3a", "CRYSTAL CAVERNS": "#c38bff",
                "SKY ISLES": "#ff9cf2"}[name]
        if i > 0:
            speed_gate(s, z0, name, speed, BIOMES[i - 1][3] or "#ffffff", glow)
        else:
            s.sign("MeadowSign", (22, 5, 1), (-40, 8, z0 + 2), "#3fa347", [L(name), L(speed, "#ffffff", 0.7)],
                   R=angles(0, 180, 0))
            s.box("MeadowSignPost", (1, 6, 1), (-40, 3, z0 + 2), C("#8b5a2b"))

        gpos = (rng.uniform(-15, 15), 0.6, zc - 40)
        face = (0, 0, z0)
        herd_c = add(gpos, (0, 0, 35))
        if name == "WHISPERING FOREST":
            gpos, face, herd_c = (-12, 0.6, z0 - 112), (6, 0, z0 - 70), (-62, 0.6, z0 - 120)
        elif name == "SCORCHED DESERT":
            gpos, herd_c = (-34, 0.6, z0 - 118), (-70, 0.6, z0 - 70)
        if name == "SKY ISLES":
            for dx, dz, y, size in [(-50, -40, 30, 50), (40, -20, 40, 44), (0, -110, 55, 60), (-70, -120, 45, 40),
                                    (70, -100, 60, 46)]:
                island(s, (dx, y, z0 + dz), size, rng, trees=2)
            for dx, dz, y in [(-10, -60, 20), (60, -60, 70), (-80, -70, 70)]:
                cloud(s, (dx, y, z0 + dz), 1.6, rng)
            s.animal("SkyfinWhale", (20, 45, z0 - 70), yaw=160, scale=1.5)
            s.animal("StarlightKitsune", (0, 57.5, z0 - 110), yaw=180)
            continue
        guardian(s, gpos, gid, gk, face)
        herd(s, herd_c, ids, rng)
        s.label(add(gpos, (0, HEIGHT.get(gid, 10) * gk + 4, 0)), [L("GUARDIAN", "#ff4a4a")], h=4, aspect=3.4)

        if name in ("SUNNY MEADOW",):
            for _ in range(60):
                flower(s, (rng.uniform(-100, 100), 0.6, rng.uniform(z0 - 160, z0 - 10)),
                       rng.choice(["#ff7ac8", "#ffd23f", "#ffffff", "#ff5a5a"]), rng)
            for _ in range(12):
                tree(s, (rng.choice([-1, 1]) * rng.uniform(70, 105), 0.6, rng.uniform(z0 - 160, z0 - 10)), rng)
        elif name == "WHISPERING FOREST":
            for _ in range(46):
                x = rng.choice([-1, 1]) * rng.uniform(45, 108)
                tree(s, (x, 0.6, rng.uniform(z0 - 165, z0 - 12)), rng, k=rng.uniform(1.2, 1.8),
                     kind=rng.choice(["round", "pine"]))
            s.box("River", (WIDTH + 20, 0.5, 12), (0, 0.65, z0 - 140), C("#4fb7ff"), material="Water", transparency=0.1)
            s.box("LogBridge", (18, 1.4, 16), (30, 1.1, z0 - 140), C("#8b5a2b"))
        elif name == "SCORCHED DESERT":
            for x, dz, k in [(-85, -50, 1.1), (85, -110, 1.2), (-80, -140, 0.9), (80, -30, 0.8)]:
                mesa(s, (x, 0.6, z0 + dz), k, rng)
            for _ in range(16):
                spot = (rng.uniform(-100, 100), 0.6, rng.uniform(z0 - 160, z0 - 15))
                turn = rng.uniform(0, 90)
                if math.dist((spot[0], spot[2]), (0, z0 - 20)) < 40:
                    continue
                with s.frame(spot, turn):
                    s.box("Cactus", (1.8, 7, 1.8), (0, 3.5, 0), C("#3fa347"))
                    s.box("CactusArm", (1.3, 3.2, 1.3), (1.6, 4.5, 0), C("#3fa347"))
            s.sign("SpeedPost", (10, 5, 0.8), (gpos[0] + 26, 9, gpos[2] + 32), "#ff9a3c",
                   [L("10K", "#ffffff", 1.1), L("RECOMMENDED", "#ffffff", 0.6)], R=angles(0, 200, 0))
            s.box("SpeedPostPole", (1, 7, 1), (gpos[0] + 26, 3.5, gpos[2] + 32), C("#8b5a2b"))
        elif name == "FROSTPEAK":
            for x, dz, k in [(-80, -60, 1.2), (80, -120, 1.4), (-70, -150, 1.0), (75, -40, 0.9)]:
                mountain(s, (x, 0.6, z0 + dz), k, rng)
            for _ in range(20):
                tree(s, (rng.choice([-1, 1]) * rng.uniform(40, 100), 0.6, rng.uniform(z0 - 160, z0 - 15)), rng,
                     leaf="#2f7a4a", k=rng.uniform(1.0, 1.4), kind="pine", snow=True)
            s.box("FrozenLake", (50, 0.6, 30), (-45, 0.7, z0 - 95), C("#bfe8ff"), material="Ice", reflectance=0.2)
        elif name == "VOLCANO":
            with s.frame((0, 0.6, z0 - 150)):
                for w, h, y in [(90, 20, 0), (66, 18, 20), (44, 16, 38)]:
                    s.bevel("Volcano", (w, h, w * 0.6), (0, y + h / 2, 0), C("#3a2f33"), b=6)
                s.box("Crater", (26, 3, 14), (0, 54.5, 0), C("#ff6a1a"), **NEON)
            for x, dz in [(-60, -60), (55, -90), (-30, -120)]:
                s.box("Lava", (30, 0.6, 12), (x, 0.7, z0 + dz), C("#ff6a1a"), rot=(0, rng.uniform(-30, 30), 0), **NEON)
        elif name == "CRYSTAL CAVERNS":
            for _ in range(18):
                crystal(s, (rng.choice([-1, 1]) * rng.uniform(30, 100), 0.6, rng.uniform(z0 - 160, z0 - 15)),
                        rng.uniform(10, 26), rng.choice(["#7ff0ff", "#ff8fe0", "#b07bff"]), rng)


# ----------------------------------------------------------------- HUD ----

def pill(x_css, y_css, html, size=30, color="#ffffff", extra=""):
    return f'<div class="pill game" style="{x_css};{y_css};font-size:{size}px;color:{color};{extra}">{html}</div>'


ICONS = {
    "LASSO": '<div style="position:absolute;top:12px;left:24px;width:32px;height:26px;border-radius:50%;'
             'border:6px solid #c9a064"></div><div style="position:absolute;top:40px;left:52px;width:6px;height:16px;'
             'background:#c9a064;transform:rotate(-30deg)"></div>',
    "BAT": '<div style="position:absolute;top:10px;left:40px;width:12px;height:46px;border-radius:6px;'
           'background:#d9a066;transform:rotate(35deg)"></div>',
    "TRAP": '<div style="position:absolute;top:18px;left:22px;width:40px;height:26px;border-radius:0 0 20px 20px;'
            'background:#9a9aa8;border-top:6px dotted #e6e6ee"></div>',
}


def hotbar(selected):
    items = [("LASSO", "#c9a064"), ("BAT", "#d9a066"), ("TRAP", "#8d8d99")]
    out = ""
    for i, (name, col) in enumerate(items):
        border = "#ffd84a" if name == selected else "#ffffff"
        out += (f'<div class="game" style="position:absolute;left:calc(50% + {(i - 1) * 104 - 46}px);bottom:26px;'
                f'width:92px;height:92px;border-radius:16px;border:5px solid {border};background:rgba(20,16,40,.72);'
                f'display:flex;align-items:flex-end;justify-content:center;font-size:18px;padding-bottom:6px;'
                f'box-sizing:border-box;box-shadow:0 5px 0 rgba(0,0,0,.35)">'
                f'{ICONS[name]}{i + 1} {name}</div>')
    return out


def top_bar(coins="$48,210", income="+$1,250/s", speed="12,400"):
    return (pill("left:28px", "top:24px", f'{coins}<span style="font-size:22px;color:#7dff8a">&nbsp;{income}</span>',
                 36, "#ffd84a")
            + pill("right:28px", "top:24px", f'SPEED <span style="color:#44ff88">{speed}</span>', 32))


def lobby_hud():
    return (top_bar() + pill("left:50%", "top:20px", 'RESPAWN IN <span style="color:#ffd84a">2:34</span>', 32,
                             extra="transform:translateX(-50%)")
            + "".join(f'<div class="btn game" style="left:28px;top:{150 + i * 108}px;width:84px;height:84px;'
                      f'background:{bg};display:flex;align-items:center;justify-content:center;font-size:18px">{n}</div>'
                      for i, (n, bg) in enumerate([("SHOP", "#ffb52e"), ("ZOO", "#52d273"), ("GEAR", "#45a6ff"),
                                                   ("REBIRTH", "#ff5a7a")]))
            + hotbar("LASSO"))


def lasso_hud():
    return (top_bar()
            + pill("left:50%", "top:20px", 'SCORCHED DESERT <span style="font-size:22px;color:#ffd84a">10K SPEED</span>',
                   30, extra="transform:translateX(-50%)")
            + '<div class="btn game" style="right:60px;bottom:60px;width:150px;height:150px;background:#ffb52e;'
              'display:flex;align-items:center;justify-content:center;text-align:center;font-size:26px">THROW<br>LASSO</div>'
            + hotbar("LASSO"))


def escape_hud():
    return (top_bar(speed='1,450 <span style="color:#ff5a5a;font-size:22px">-30%</span>')
            + '<div class="game" style="position:absolute;left:50%;top:92px;transform:translateX(-50%);font-size:54px;'
              'color:#ff5a5a">RUN TO YOUR ZOO!</div>'
            + '<div class="game" style="position:absolute;left:50%;top:160px;transform:translateX(-50%);font-size:28px">'
              '&#9660; 212 STUDS &#9660;</div>'
            + pill("left:28px", "top:110px", 'CARRYING: <span style="color:#45a6ff">WOLF</span>', 26)
            + pill("left:28px", "top:176px", '<span style="color:#ff5a5a">GUARDIAN IS CHASING!</span>', 24)
            + hotbar("BAT"))


def gate_hud():
    return (top_bar()
            + '<div class="game" style="position:absolute;left:50%;top:40%;transform:translateX(-50%);font-size:44px;'
              'color:#ff5a5a;text-align:center">TOO SLOW!<br><span style="font-size:28px;color:#fff">'
              'YOU NEED 40K SPEED &middot; YOU HAVE 12,400</span></div>'
            + '<div class="game" style="position:absolute;left:50%;top:calc(40% + 110px);transform:translateX(-50%);'
              'font-size:24px;color:#44ff88">TRAIN ON YOUR TREADMILL!</div>'
            + hotbar("LASSO"))


def tame_hud():
    confetti = "".join(
        f'<div style="position:absolute;left:{x}%;top:{y}%;width:14px;height:22px;background:{c};'
        f'transform:rotate({r}deg);border-radius:3px"></div>'
        for x, y, c, r in [(30, 12, "#ff5a5a", 20), (36, 30, "#ffd23f", -30), (62, 16, "#45a6ff", 45),
                           (70, 34, "#52d273", 10), (25, 40, "#b861ff", -60), (75, 22, "#ff7ac8", 70),
                           (44, 8, "#3fe0e0", 15), (56, 38, "#ffd23f", -15), (20, 22, "#52d273", 35),
                           (80, 44, "#ffd23f", -40)])
    return (top_bar(coins="$53,420", income="+$6,250/s") + confetti
            + '<div class="game" style="position:absolute;left:50%;top:9%;transform:translateX(-50%);font-size:76px;'
              'color:#ffd23a">TAMED!</div>'
            + '<div style="position:absolute;right:5%;top:30%;width:430px;padding:18px 0;'
              'border-radius:22px;border:6px solid #ffd23a;background:linear-gradient(#5a3fb0,#1b1530);text-align:center;'
              'box-shadow:0 8px 0 rgba(0,0,0,.35)">'
              '<div class="game" style="font-size:40px;color:#ffd23a">GOLDEN THUNDERHOOF</div>'
              '<div class="game" style="font-size:26px;color:#ffcc33;margin-top:6px">LEGENDARY &middot; GOLDEN x2</div>'
              '<div class="game" style="font-size:34px;color:#5dff7a;margin-top:8px">$5,000/S</div></div>'
            + '<div class="btn game" style="right:calc(5% - 20px);top:calc(30% - 36px);width:74px;height:74px;background:#ff3b5c;'
              'display:flex;align-items:center;justify-content:center;font-size:22px">NEW!</div>'
            + hotbar("LASSO"))


# --------------------------------------------------------------- world ----

def build_world():
    rng = random.Random(21)
    s = Scene("world", env={
        "sky": [[0, "#3f9fff"], [0.55, "#96d0ff"], [1, "#dff2ff"]], "fog": ["#dff2ff", 420, 1150],
        "sun": {"dir": [-0.5, 1.0, 0.45], "intensity": 2.5}, "hemi": ["#ffffff", "#8fb070", 1.45],
        "bloom": [0.5, 0.5, 0.9],
    })
    lobby(s, rng)
    wild(s, rng)

    # My zoo: ChrisHunter, right side of the avenue.
    side, zz = ZOOS[MY_ZOO][0], ZOOS[MY_ZOO][1]
    zoo_center = (62 * side, 0, zz)

    # Desert: throwing a lasso at a Thunderhoof in front of the giant Sandsnapper.
    z0 = biome_z(2)
    thunder = (8, 0.9, z0 - 60)
    thrower = (-4, 0.6, z0 - 28)
    s.animal("Thunderhoof", thunder, yaw=toward(thunder, (60, 0, z0 - 60)))
    s.label(add(thunder, (0, 16.5, 0)), [L("THUNDERHOOF", "#ffcc33"), L("LEGENDARY", "#ffffff", 0.7)], h=2.4)
    hands = player(s, thrower, toward(thrower, thunder), "#ff5a5a", "#2b3a6b", hair="#3a2412", pose="throw")
    neck = model_point(thunder, toward(thunder, (60, 0, z0 - 60)), 1, (0, 10.6, -2.8))
    loop_c = add(neck, (0, 2.2, 0))
    edge = lasso_loop(s, loop_c, 3.4, tilt=(12, 0, -10))
    rope(s, bezier(hands["R"], add(scale(add(hands["R"], edge), 0.5), (0, 13, 0)), edge, 16))
    gpos = (-6, 0.6, z0 - 125)
    desert_cam = (10, 10, z0 - 6)

    # Forest: escaping with a lassoed Wolf, the giant Bear chasing, a rival with a bat.
    zf = biome_z(1)
    runner = (6, 0.6, zf - 70)
    wolf = (-5, 0.9, zf - 92)
    runner_yaw = 180
    hands_r = player(s, runner, runner_yaw, "#45a6ff", "#2b3a6b", hair="#e8c07a", pose="drag")
    wolf_yaw = toward(wolf, runner)
    s.animal("Wolf", wolf, yaw=wolf_yaw)
    wolf_neck = model_point(wolf, wolf_yaw, 1, (0, 6.2, -2.8))
    near = lasso_loop(s, wolf_neck, 1.9, tilt=(0, 0, 0), n=10)
    rope(s, bezier(hands_r["R"], add(scale(add(hands_r["R"], near), 0.5), (0, -1.2, 0)), near, 10))
    rival = (-17, 0.6, zf - 62)
    player(s, rival, toward(rival, runner), "#ffd23f", "#4a3a2a", hair="#111", pose="bat")
    bear_trap(s, (13, 0.6, zf - 50), 20)
    forest_cam = (12, 7.5, zf - 30)

    # Frostpeak speed gate seen from the desert.
    zg = biome_z(3)
    gate_cam = (12, 12, zg + 72)
    player(s, (4, 0.6, zg + 34), 0, "#ff5a5a", "#2b3a6b", hair="#3a2412")

    s.shot("lobby", (-165, 140, 430), (0, 0, 135), fov=50, shadow={"center": [0, 0, 170], "radius": 230},
           hud=lobby_hud())
    zc = zoo_center
    s.shot("zoo", (4, 24, zc[2] + 26), (zc[0] - 2, 2, zc[2] - 4), fov=55,
           shadow={"center": [zc[0], 0, zc[2]], "radius": 75})
    s.shot("wild", (150, 190, 60), (0, 0, -420), fov=52, shadow={"center": [0, 0, -330], "radius": 420},
           env={"fog": ["#dff2ff", 650, 1800]})
    s.shot("lasso", desert_cam, (-10, 9, z0 - 75), fov=60, shadow={"center": list(thunder), "radius": 110},
           hud=lasso_hud())
    s.shot("escape", forest_cam, add(runner, (-3, 6, -26)), fov=60, shadow={"center": list(runner), "radius": 90},
           hud=escape_hud(), hide_sprites=True)
    s.shot("gate", gate_cam, (0, 16, zg - 100), fov=55, shadow={"center": [0, 0, zg - 40], "radius": 140},
           hud=gate_hud())
    # Taming: close-up of the golden Thunderhoof in my zoo (enclosure 2, front row).
    to_world = lambda local: add(zoo_center, apply(angles(0, 90 * side, 0), local))
    enc = to_world((0, 0, -12))
    s.shot("tame", to_world((14, 13, -27)), add(enc, (0, 4, 0)), fov=52,
           shadow={"center": list(enc), "radius": 50}, hud=tame_hud(), hide_sprites=True)
    r = random.Random(3)
    for _ in range(16):
        p = add(enc, (r.uniform(-6, 6), r.uniform(2, 11), r.uniform(-6, 6)))
        s.box("Sparkle", (0.45, 0.45, 0.45), p, C("#ffe066"), rot=(45, 45, 0), **NEON)
    return s


def main():
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    world = build_world()
    (out / "world.json").write_text(json.dumps(world.export()))
    print(f"world: {len(world.parts)} parts, {len(world.models)} animals, {len(world.shots)} shots")


if __name__ == "__main__":
    main()
