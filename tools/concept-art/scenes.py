#!/usr/bin/env python3
"""Concept-art scenes for Hunt an Animal: the Hub and the Hunting Grounds.

Builds blocky studded scenes with the real animal models placed in them and
writes build/hub.json and build/grounds.json for viewer/scene.html.
"""

import json
import math
import random
import sys
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "animal-models"))

from lib import IDENTITY, Animal, add, angles, apply, cframe, hex_color, matmul  # noqa: E402

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
             "RoyalGriffin": 0.58, "Bear": 0.65, "Moonbear": 0.65, "StarlightKitsune": 0.68, "MossbackTortle": 0.8}


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

    def animal(self, animal_id, pos, yaw=0.0, scale=1.0):
        self.models.append({"id": animal_id, "pos": list(self.world(pos)), "yaw": self.frames[-1][2] + yaw,
                            "scale": scale})

    def shot(self, name, pos, target, fov=50, shadow=None, env=None, hud=None):
        self.shots[name] = {
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


def player(s, pos, yaw, shirt, pants, skin="#ffd6a5", hair="#4a2c17", camera=True):
    with s.frame(pos, yaw):
        for x in (-0.5, 0.5):
            s.box("Leg", (0.95, 2.0, 1.0), (x, 1.0, 0), C(pants))
        s.box("Torso", (2.0, 2.0, 1.0), (0, 3.0, 0), C(shirt))
        if camera:
            for x in (-1.2, 1.2):
                s.box("Arm", (0.9, 2.0, 0.9), (x, 3.55, -0.75), C(skin), rot=(-75, 0, 0))
            s.bevel("Camera", (1.8, 1.2, 0.9), (0, 3.95, -1.9), C("#2b2b33"), b=0.2, bottom=0.2)
            s.cyl("Lens", 0.6, 0.8, (0, 3.9, -2.55), C("#111118"), R=angles(0, 90, 0))
            s.box("Flash", (0.4, 0.3, 0.1), (0.55, 4.35, -2.37), C("#fff7c2"), material="Neon", shadow=False)
        else:
            for x in (-1.5, 1.5):
                s.box("Arm", (1.0, 2.0, 1.0), (x, 3.0, 0), C(skin))
        s.bevel("Head", (1.3, 1.3, 1.3), (0, 4.65, 0), C(skin), b=0.3, bottom=0.3)
        s.box("Hair", (1.4, 0.45, 1.4), (0, 5.35, 0.05), C(hair))
        s.box("HairBack", (1.4, 1.0, 0.35), (0, 4.95, 0.55), C(hair))
        for x in (-0.28, 0.28):
            s.box("PlayerEye", (0.18, 0.32, 0.05), (x, 4.8, -0.66), C("#1b1420"), material="SmoothPlastic",
                  shadow=False)
        s.box("Smile", (0.5, 0.1, 0.05), (0, 4.42, -0.66), C("#1b1420"), material="SmoothPlastic", shadow=False)


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


# ----------------------------------------------------------- HUD ----

def hub_hud(countdown="2:34"):
    return f"""
<div class="pill game" style="left:28px;top:24px;font-size:38px;color:#ffd84a">$12,450
  <span style="font-size:24px;color:#7dff8a">&nbsp;+$85/s</span></div>
<div class="pill game" style="left:50%;transform:translateX(-50%);top:20px;font-size:34px">NEXT HUNT
  <span style="color:#ffd84a">{countdown}</span></div>
<div class="pill game" style="right:28px;top:24px;font-size:30px;color:#6dff8a">&#9752; LUCK x1.5</div>
<div class="game" style="position:absolute;left:50%;transform:translateX(-50%);bottom:56px;font-size:26px">LEVEL 7</div>
<div class="bar" style="left:50%;transform:translateX(-50%);bottom:26px;width:560px">
  <div style="width:62%;background:linear-gradient(#9be0ff,#3f8fff)"></div></div>
""" + "".join(f"""
<div class="btn game" style="left:28px;top:{150 + i * 108}px;width:84px;height:84px;background:{bg};
  display:flex;align-items:center;justify-content:center;font-size:19px">{name}</div>
{'' if not badge else f'<div class="btn game" style="left:92px;top:{142 + i * 108}px;width:30px;height:30px;border-width:3px;background:#3fdc5a;display:flex;align-items:center;justify-content:center;font-size:20px">!</div>'}
""" for i, (name, bg, badge) in enumerate([("SHOP", "#ffb52e", True), ("INDEX", "#45a6ff", False),
                                            ("QUESTS", "#b861ff", True), ("WHEEL", "#ff5a7a", True)]))


def viewfinder_hud():
    corner = "position:absolute;width:96px;height:96px;border:0 solid #fff;"
    return f"""
<div style="position:absolute;inset:0;box-shadow:inset 0 0 260px 90px rgba(0,0,0,.7)"></div>
<div style="{corner}left:14%;top:12%;border-left-width:9px;border-top-width:9px"></div>
<div style="{corner}right:14%;top:12%;border-right-width:9px;border-top-width:9px"></div>
<div style="{corner}left:14%;bottom:14%;border-left-width:9px;border-bottom-width:9px"></div>
<div style="{corner}right:14%;bottom:14%;border-right-width:9px;border-bottom-width:9px"></div>
<div style="position:absolute;left:50%;top:50%;width:260px;height:260px;margin:-130px 0 0 -130px;border-radius:50%;
  border:5px solid rgba(255,255,255,.85);box-shadow:0 0 12px rgba(0,0,0,.5)"></div>
<div style="position:absolute;left:50%;top:50%;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;
  border:4px solid #fff"></div>
<div class="game" style="position:absolute;left:50%;transform:translateX(-50%);top:19%;font-size:46px;color:#c77bff">FROSTFANG WOLF</div>
<div class="game" style="position:absolute;left:50%;transform:translateX(-50%);top:25.5%;font-size:26px">EPIC &middot; 45 STUDS</div>
<div class="game" style="position:absolute;left:50%;transform:translateX(-50%);bottom:24%;font-size:64px;color:#ffd84a">
  &#9733;&#9733;<span style="color:rgba(255,255,255,.45)">&#9733;</span></div>
<div class="game" style="position:absolute;left:50%;transform:translateX(-50%);bottom:18.5%;font-size:24px">CAPTURE</div>
<div class="bar" style="left:50%;transform:translateX(-50%);bottom:13.5%;width:520px;height:26px">
  <div style="width:78%;background:linear-gradient(90deg,#3fdc5a,#ffd84a)"></div></div>
<div class="pill game" style="left:28px;top:24px;font-size:30px">HUNT ENDS <span style="color:#ffd84a">3:12</span></div>
<div class="pill game" style="left:28px;top:92px;font-size:24px">23 LEFT &middot; <span style="color:#ffcc33">1 LEGENDARY</span>
  &middot; <span style="color:#c77bff">3 EPIC</span></div>
<div class="pill game" style="right:28px;top:24px;font-size:30px;color:#6dff8a">&#9752; LUCK x2.5</div>
<div class="pill game" style="right:28px;top:92px;font-size:26px;color:#ffa54a">STREAK x3</div>
<div class="bar" style="right:52px;top:34%;width:20px;height:260px"><div style="height:62%;margin-top:auto;
  background:#fff;position:absolute;bottom:0;width:100%"></div></div>
<div class="game" style="position:absolute;right:38px;top:calc(34% + 272px);font-size:28px">3X</div>
<div class="btn" style="right:70px;bottom:64px;width:150px;height:150px;background:rgba(255,255,255,.2)"></div>
<div class="btn" style="right:92px;bottom:86px;width:116px;height:116px;background:#fff;border-color:#ddd"></div>
<div class="btn game" style="right:262px;bottom:78px;width:92px;height:92px;background:#ffd84a;display:flex;
  align-items:center;justify-content:center;font-size:20px;color:#fff">FLASH</div>
""" + "".join(f"""
<div style="position:absolute;left:{28 + i * 118}px;bottom:40px;width:104px;height:140px;border-radius:14px;
  background:linear-gradient({col},#1b1530);border:4px solid #fff;box-shadow:0 5px 0 rgba(0,0,0,.35)">
  <div class="game" style="position:absolute;top:10px;width:100%;text-align:center;font-size:20px">{name}</div>
  <div class="game" style="position:absolute;bottom:10px;width:100%;text-align:center;font-size:24px;color:#ffd84a">{timer}</div>
</div>""" for i, (name, col, timer) in enumerate([("WOLF", "#45a6ff", "1:42"), ("DEER", "#62e36e", "2:10")]))


# ----------------------------------------------------------- Hub ----

PLOTS = [
    ("LunaPlayz", "#ff7ac8", ["Sandsnapper", "Thunderhoof", "Moonbear", "Bear", "FrostfangWolf", "Wolf"], "$38.4K/s"),
    ("Noob_123", "#52d273", ["Rabbit", "Rabbit", "Puffhop", "Deer"], "$10/s"),
    (None, "#bfc6d1", [], ""),
    ("ChrisHunter", "#4f9dff", ["PhoenixFox", "CrystalHare", "GlowhornStag", "EmberbackBoar", "Boar", "MossbackTortle"],
     "$26.1K/s"),
    ("xXFoxXx", "#ff9a3c", ["Wolf", "Boar", "Deer", "Puffhop", "MossbackTortle"], "$88/s"),
    (None, "#bfc6d1", [], ""),
    ("Builder_Bob", "#a66bff", ["Voidwhisker", "Bear", "Wolf", "Rabbit"], "$15.2K/s"),
    ("StarQueen", "#ffd23f", ["StarlightKitsune", "RoyalGriffin", "SkyfinWhale", "Moonbear", "CrystalHare"],
     "$183K/s"),
]


def zoo_plot(s, owner, color, animals, value, rng):
    s.box("PlotBase", (56, 1, 56), (0, 0.5, 0), C("#f3e6c6"))
    wall = C(color)
    s.box("Wall", (56, 3, 1.5), (0, 2.5, 27.25), wall)
    for x in (-27.25, 27.25):
        s.box("Wall", (1.5, 3, 56), (x, 2.5, 0), wall)
    for x in (-17, 17):
        s.box("Wall", (22, 3, 1.5), (x, 2.5, -27.25), wall)
    for x in (-7.5, 7.5):
        s.bevel("GatePillar", (2.6, 10, 2.6), (x, 6, -27.25), C("#ffffff"), b=0.5)
    if owner is None:
        s.sign("PlotSign", (17, 3.2, 1), (0, 11.2, -27.25), wall, [L("FREE PLOT")])
        s.box("PlotGrass", (50, 0.3, 46), (0, 1.15, 3), C("#9bd67e"))
        s.label((0, 6, 0), [L("CLAIM ME!", "#ffffff")], h=3)
        return
    s.sign("PlotSign", (17, 3.2, 1), (0, 11.2, -27.25), wall, [L(f"{owner}'s Zoo")])
    s.box("SignPost", (0.8, 6, 0.8), (-12.5, 3.5, -31), C("#8b5a2b"))
    s.sign("ValueSign", (8, 3.4, 0.6), (-12.5, 7.4, -31), "#ffffff",
           [L("ZOO VALUE", "#ffcf3a", 0.8), L(value, "#3fdc5a", 1.1)])
    s.box("PlotGrass", (50, 0.3, 46), (0, 1.15, 3), C("#86d06a"))
    pens = [(-17, -10), (0, -10), (17, -10), (-17, 10), (0, 10), (17, 10)]
    for i, (x, z) in enumerate(pens):
        s.box("PenFloor", (15, 0.4, 15), (x, 1.5, z), C("#9fdc7f"))
        for dz in (-7.25, 7.25):
            s.box("PenFence", (15, 1.3, 0.5), (x, 2.35, z + dz), C("#ffffff"))
        for dx in (-7.25, 7.25):
            s.box("PenFence", (0.5, 1.3, 15), (x + dx, 2.35, z), C("#ffffff"))
        for dx in (-7.25, 7.25):
            for dz in (-7.25, 7.25):
                s.box("PenPost", (0.9, 2.2, 0.9), (x + dx, 2.8, z + dz), wall)
        s.box("CollectPad", (4, 0.3, 2.2), (x, 1.85, z - 5.3), C("#ffcf3a"), **NEON)
        if i < len(animals):
            aid = animals[i]
            name, rarity, income = ANIMALS[aid]
            s.animal(aid, (x, 1.7, z + 0.6), yaw=rng.uniform(-25, 25), scale=PEN_SCALE.get(aid, 0.72))
            s.label((x, 12.5, z), [L(name, RARITY[rarity]), L(income, "#5dff7a", 0.8)], h=1.9, aspect=4.2)
            if rng.random() < 0.45:
                s.label((x + 3.5, 8.5 + rng.uniform(0, 2), z - 4), [L("+" + income.replace("/s", ""), "#ffd84a")],
                        h=1.8, aspect=2.6)
    for x in (-24, 24):
        bush(s, (x, 1.3, 24), "#4fb84f")


def hub_buildings(s, rng):
    # Hunting Gate with the giant clock (north).
    with s.frame((0, 0, -112), 180):
        s.box("GateSteps", (72, 1.2, 26), (0, 0.6, 0), C("#d6ceb9"))
        s.box("GateSteps", (60, 1.2, 8), (0, 1.8, 0), C("#e2dac6"))
        for x in (-24, 24):
            s.bevel("GatePillar", (10, 44, 10), (x, 24.4, 0), C("#b9b3a7"), b=2.0)
            s.bevel("GateCap", (12, 3, 12), (x, 47.9, 0), C("#f2c14e"), b=0.8, reflectance=0.2)
            s.box("Banner", (6.5, 13, 0.4), (x, 33, -5.3), C("#d8283f"))
            s.box("BannerEmblem", (3, 3, 0.2), (x, 34, -5.55), C("#ffd23a"), rot=(0, 0, 45))
            s.box("Torch", (1.4, 3, 1.4), (x, 18, -5.8), C("#3a2a22"))
            s.box("TorchFlame", (1.6, 2.2, 1.6), (x, 20.4, -5.8), C("#ff8a1f"), **NEON)
        s.bevel("GateBeam", (58, 9, 12), (0, 43, 0), C("#a8a092"), b=2.0)
        s.sign("GateName", (40, 5, 0.6), (0, 43, -6.3), "#5b3a22", [L("HUNTING GATE", "#ffd84a")])
        s.box("ClockFrame", (40, 17, 2.4), (0, 57, 0.6), C("#f2c14e"), reflectance=0.2)
        s.sign("Clock", (36, 14, 3), (0, 57, 0), "#1d2033",
               [L("NEXT HUNT", "#ffffff", 0.75), L("2:34", "#ffe14a", 1.35)], glow=True)
        for x in (-16, 0, 16):
            s.tri("ClockSpike", (x, 65.5, 0.6), 4, 4, 1.5, C("#f2c14e"), reflectance=0.2)
        for x in (-9.6, 9.6):
            s.box("Door", (19, 34, 2), (x, 19.4, 1.5), C("#8a5a33"))
            for dx in (-6, 0, 6):
                s.box("DoorPlank", (0.5, 33, 0.4), (x + dx, 19.4, 0.4), C("#6b4226"))
            s.box("DoorBand", (19, 1.2, 0.4), (x, 28, 0.35), C("#3a2a22"))
            s.box("DoorBand", (19, 1.2, 0.4), (x, 10, 0.35), C("#3a2a22"))
        s.box("DoorGlow", (0.8, 33, 0.4), (0, 19.4, 0.8), C("#7dff9a"), **NEON)
        for i, (x, z, shirt, pants, hair) in enumerate([
                (-8, -16, "#ff5a5a", "#2b3a6b", "#3a2412"), (-3, -19, "#45a6ff", "#333", "#e8c07a"),
                (4, -17, "#3fdc5a", "#4a3a2a", "#111"), (10, -20, "#ffd23f", "#2b3a6b", "#a33"),
                (1, -23, "#b861ff", "#222", "#ffe6a8")]):
            player(s, (x, 2.4 if abs(z) < 13 else 1.2, z), 180 + rng.uniform(-20, 20), shirt, pants, hair=hair,
                   camera=i % 2 == 0)

    # Shop (north-east).
    with s.frame(polar(45, 92), 135):
        s.box("ShopFloor", (26, 1, 18), (0, 0.5, 0), C("#caa472"))
        s.bevel("ShopBack", (26, 12, 2), (0, 7, 8), C("#fff1d6"), b=0)
        for x in (-12, 12):
            s.box("ShopSide", (2, 12, 18), (x, 7, 0), C("#fff1d6"))
        s.box("ShopRoof", (28, 1.5, 20), (0, 13.7, 0), C("#e0473c"))
        for i in range(7):
            s.wedge("Awning", (4, 3, 5), (-12 + 4 * i, 11.5, -11.4), C("#e0473c" if i % 2 == 0 else "#ffffff"))
        s.sign("ShopSign", (18, 4.5, 1), (0, 17.2, -3), "#ffcf3a", [L("SHOP")])
        s.box("Counter", (20, 4, 3), (0, 3, -6), C("#9c6b3f"))
        s.box("CounterTop", (21, 0.5, 3.4), (0, 5.2, -6), C("#fff1d6"))
        for i, (x, col) in enumerate([(-7, "#3fdc5a"), (-4, "#b861ff"), (4, "#45a6ff"), (7, "#ffcf3a")]):
            s.box("Potion", (1.2, 1.8, 1.2), (x, 6.4, -6), C(col), material="Glass", transparency=0.1)
        s.bevel("DisplayCamera", (2.6, 1.8, 1.4), (0, 6.4, -6), C("#2b2b33"), b=0.3, bottom=0.3)
        player(s, (0, 1, -2), 0, "#ffffff", "#333", hair="#6a3", camera=False)
        s.label((0, 23, -3), [L("RESTOCKED!", "#ffd84a")], h=3)

    # Bounty Board (east).
    with s.frame(polar(90, 88), 90):
        for x in (-12, 12):
            s.box("BoardPost", (1.5, 18, 1.5), (x, 9, 0.5), C("#6b4226"))
        s.box("Board", (26, 14, 1.2), (0, 11, 0), C("#9c6b3f"))
        s.box("BoardRoof", (29, 2, 4), (0, 19, 0), C("#5b3a22"))
        s.sign("BoardTitle", (22, 3, 0.4), (0, 16, -0.8), "#5b3a22", [L("BOUNTY BOARD", "#ffd84a")])
        for x, lines in ((-8, ["BIG DEER", "3 STARS", "$5,000"]), (0, ["ANY GOLDEN", "ANIMAL", "$12,000"]),
                         (8, ["FROSTFANG", "WOLF", "$25,000"])):
            s.sign("Poster", (6.5, 8.6, 0.3), (x, 9.6, -0.75), "#f6e7c1",
                   [L("WANTED", "#d8283f", 1.2), L(lines[0], "#3a2a22", 0.8), L(lines[1], "#3a2a22", 0.8),
                    L(lines[2], "#2fae4a", 1.0)], pad=0.1)

    # Lucky Wheel (south-east).
    with s.frame(polar(135, 90), 45):
        s.box("WheelBase", (12, 2, 7), (0, 1, 1), C("#7b4bd6"))
        for x in (-5.5, 5.5):
            s.box("WheelPost", (1.6, 16, 1.6), (x, 9, 1.5), C("#5a32b0"))
        s.cyl("WheelRim", 1.2, 26, (0, 17.5, 0.5), C("#ffd23a"), R=angles(0, 90, 0), reflectance=0.2)
        s.cyl("WheelFace", 1.2, 24, (0, 17.5, -0.2), C("#ffffff"), R=angles(0, 90, 0))
        colors = ["#ff5a5a", "#ff9a3c", "#ffd23f", "#52d273", "#3fe0e0", "#4f9dff", "#a66bff", "#ff7ac8"]
        for k, col in enumerate(colors):
            a = math.radians(22.5 + 45 * k)
            s.box("WheelSlice", (10.5, 5.2, 0.4), (5.9 * math.cos(a), 17.5 + 5.9 * math.sin(a), -1.0), C(col),
                  rot=(0, 0, 22.5 + 45 * k))
            b = math.radians(45 * k)
            s.ball("Bulb", 0.9, (12.4 * math.cos(b), 17.5 + 12.4 * math.sin(b), -0.4), C("#fff3a0"), **NEON)
        s.cyl("WheelHub", 1.2, 4, (0, 17.5, -1.4), C("#ffd23a"), R=angles(0, 90, 0), reflectance=0.2)
        s.tri("WheelPointer", (0, 33.2, -1.2), 3.2, 3.4, 1.2, C("#ff3b3b"), R=angles(0, 0, 180))
        s.sign("WheelSign", (16, 3.2, 0.8), (0, 3.8, -3.2), "#7b4bd6", [L("LUCKY WHEEL", "#ffd84a")])
        s.label((0, 36.5, 0), [L("FREE SPIN!", "#5dff7a")], h=3)

    # Leaderboards (south).
    with s.frame(polar(180, 88), 0):
        boards = [
            ("RICHEST ZOO", ["1. StarQueen  $183K/s", "2. LunaPlayz  $38.4K/s", "3. ChrisHunter  $26.1K/s",
                             "4. Builder_Bob  $15.2K/s", "5. xXFoxXx  $88/s"]),
            ("RAREST MUTATION", ["1. StarQueen  CELESTIAL", "2. LunaPlayz  GALAXY", "3. ChrisHunter  RAINBOW",
                                 "4. Builder_Bob  BLAZING", "5. Noob_123  GOLDEN"]),
            ("HUNT MVPS", ["1. LunaPlayz  42", "2. StarQueen  37", "3. ChrisHunter  29", "4. xXFoxXx  12",
                           "5. Builder_Bob  9"]),
        ]
        for i, (title, rows) in enumerate(boards):
            x = (i - 1) * 16
            s.box("LbPost", (1.2, 5, 1.2), (x, 2.5, 0.6), C("#3a3f5c"))
            s.box("LbFrame", (14, 17.4, 0.8), (x, 13.2, 0.5), C("#f2c14e"), reflectance=0.2)
            s.sign("Leaderboard", (13, 16.4, 1), (x, 13.2, 0), "#1f2340",
                   [L(title, "#ffd84a", 1.3)] + [L(r, "#ffffff", 0.8, "body") for r in rows], pad=0.06)

    # VIP lounge (south-west).
    with s.frame(polar(225, 92), -45):
        s.box("VipFloor", (26, 1.6, 20), (0, 0.8, 0), C("#f2c14e"), reflectance=0.2)
        s.box("VipCarpet", (8, 0.3, 20.2), (0, 1.75, 0), C("#c9243f"))
        for x in (-11, 11):
            s.box("RopePost", (0.8, 3, 0.8), (x, 3.1, -9.2), C("#ffd23a"), reflectance=0.3)
        s.beam("Rope", (-11, 4, -9.2), (-4, 3.4, -9.2), 0.35, C("#c9243f"))
        s.beam("Rope", (4, 3.4, -9.2), (11, 4, -9.2), 0.35, C("#c9243f"))
        for x in (-7, 7):
            s.box("Couch", (8, 2.2, 3.2), (x, 2.7, 4.5), C("#8a2be2"))
            s.box("CouchBack", (8, 3, 1), (x, 4, 6.3), C("#6a1fb0"))
            tree(s, (x * 1.5, 1.6, 8.5), rng, leaf="#3fbf5a", k=0.8)
        s.sign("VipSign", (12, 4.4, 1), (0, 9.5, 8.8), "#6a35c9", [L("VIP", "#ffd84a", 1.3), L("LOUNGE", "#ffffff", 0.7)])
        player(s, (-7, 3.8, 4.2), 0, "#111111", "#111111", hair="#ffd23a", camera=False)

    # Quests board and a reward chest (north-west).
    with s.frame(polar(315, 88), -135):
        for x in (-10, 10):
            s.box("BoardPost", (1.4, 15, 1.4), (x, 7.5, 0.5), C("#6b4226"))
        s.sign("QuestBoard", (22, 12, 1.2), (0, 9.5, 0), "#2f7ad9",
               [L("DAILY QUESTS", "#ffd84a", 1.3), L("Capture 5 Rabbits  3/5", "#ffffff", 0.8, "body"),
                L("Get 3 stars on a Wolf  0/1", "#ffffff", 0.8, "body"),
                L("Roll any mutation  2/3", "#ffffff", 0.8, "body")], pad=0.08)
        chest(s, (14, 1, -2), 20, k=1.6)

    # Training Track arch (west).
    with s.frame(polar(270, 55), 180):
        for x in (-6.5, 6.5):
            s.box("ArchPost", (1.6, 13, 1.6), (x, 6.5, 0), C("#ff9a3c"))
        s.sign("TrackSign", (16, 3.4, 1), (0, 12.6, 0), "#ff9a3c", [L("TRAINING TRACK")])


def build_hub():
    rng = random.Random(7)
    s = Scene("hub", env={
        "sky": [[0, "#3f9fff"], [0.55, "#96d0ff"], [1, "#dff2ff"]], "fog": ["#dff2ff", 330, 900],
        "sun": {"dir": [-0.5, 1.0, 0.45], "intensity": 2.5}, "hemi": ["#ffffff", "#8fb070", 1.45],
        "bloom": [0.45, 0.45, 0.93],
    })
    ground(s, (4000, 4000), (0, 0, 0), "#72c255")
    octagon(s, "Plaza", 50, 0.6, 0.6, "#efe2bf")
    octagon(s, "PlazaInner", 30, 0.8, 0.7, "#e3cf9f")
    for k in range(8):
        b = 45 * k
        s.box("Track", (49.7, 0.8, 10), polar(b, 55, 0.4), C("#d0543f"), rot=(0, -b, 0))
        s.box("TrackLine", (49.7, 0.3, 0.5), polar(b, 55, 0.85), C("#ffffff"), rot=(0, -b, 0))
    for k in range(8):
        b = 22.5 + 45 * k
        s.box("Path", (12, 0.5, 36), polar(b, 78, 0.25), C("#d9cfb8"), rot=(0, -b, 0))
    s.box("GatePath", (22, 0.5, 40), polar(0, 80, 0.25), C("#d9cfb8"))

    # The magic camera statue in the middle of the plaza.
    octagon(s, "Pedestal", 9, 3, 3.7, "#c9c1ad")
    octagon(s, "PedestalTop", 7, 1.5, 5.2, "#f2c14e", reflectance=0.2)
    with s.frame((0, 5.2, 0), 180):
        s.bevel("StatueBody", (15, 9.5, 7), (0, 5.5, 0), C("#e8423f"), b=1.6, bottom=1.6)
        s.bevel("StatueTop", (6, 2.4, 5), (1.5, 11.2, 0), C("#2b2b33"), b=0.5)
        s.cyl("StatueLens", 3.2, 6.6, (0, 5.3, -4.8), C("#2b2b33"), R=angles(0, 90, 0))
        s.cyl("StatueGlass", 0.4, 5, (0, 5.3, -6.5), C("#7fd8ff"), R=angles(0, 90, 0), **NEON)
        s.box("StatueFlash", (3.4, 2.2, 1), (-4.6, 8.8, -3.3), C("#fff7c2"), **NEON)
        s.cyl("StatueButton", 1.2, 1.8, (-4.5, 10.9, 0), C("#ffd23a"), R=angles(0, 0, 90), reflectance=0.3)
        s.box("StatueStripe", (15.1, 1.2, 7.1), (0, 2.5, 0), C("#ffffff"))
    with s.frame((0, 0, 0), 180):
        s.sign("TitleSign", (16, 2.6, 0.6), (0, 2.2, -9.4), "#1f2340", [L("HUNT AN ANIMAL", "#ffd84a")])

    for k, (owner, color, animals, value) in enumerate(PLOTS):
        theta = 22.5 + 45 * k
        with s.frame(polar(theta, 122), 180 - theta):
            zoo_plot(s, owner, color, animals, value, rng)

    hub_buildings(s, rng)

    for x, z, shirt in [(-12, 18, "#ff7ac8"), (16, 10, "#52d273"), (-20, -8, "#ffd23f"), (8, 26, "#45a6ff"),
                        (26, -22, "#ff9a3c"), (-30, 24, "#3fe0e0")]:
        player(s, (x, 0.7, z), rng.uniform(0, 360), shirt, "#2b3a6b", hair=rng.choice(["#3a2412", "#111", "#e8c07a"]),
               camera=rng.random() < 0.5)

    for _ in range(70):
        b, r = rng.uniform(0, 360), rng.uniform(170, 300)
        if abs(((b + 180) % 360) - 180) < 14 and r < 230:
            continue
        tree(s, polar(b, r), rng, k=rng.uniform(1.0, 1.5), kind=rng.choice(["round", "round", "pine"]))
    for k in range(8):
        b = 45 * k
        for side in (-1, 1):
            bush(s, polar(b + side * 7, 64), rng.choice(["#4fb84f", "#3fa347"]))
            flower(s, polar(b + side * 10, 66), rng.choice(["#ff7ac8", "#ffd23f", "#ffffff", "#ff5a5a"]), rng)

    plot3 = polar(157.5, 122)
    s.shot("overview", (0, 205, 245), (0, 4, -28), fov=52, shadow={"center": [0, 0, -10], "radius": 270})
    s.shot("gate", (24, 11, -52), (0, 30, -112), fov=58, shadow={"center": [0, 0, -95], "radius": 90},
           hud=hub_hud())
    cam = polar(150, 88, 27)
    s.shot("zoo", cam, (plot3[0] + 2, 2, plot3[2] + 2), fov=50, shadow={"center": [plot3[0], 0, plot3[2]], "radius": 70})
    return s


# ------------------------------------------------ Hunting Grounds ----

BIOMES = {
    "forest": (-85, -35, 105, 235, "#4f9d3a"),
    "frost": (-35, 5, 125, 270, "#eef5ff"),
    "crystal": (5, 45, 140, 280, "#5d5775"),
    "canyon": (45, 92, 115, 265, "#e6a15a"),
}


def patch(s, b0, b1, r0, r1, color, top):
    step = 7
    b = b0
    while b <= b1:
        width = r1 * math.radians(step) * 1.25
        s.box("Biome", (width, 0.6, r1 - r0), polar(b, (r0 + r1) / 2, top - 0.3), C(color), rot=(0, -b, 0))
        b += step


def in_biome(rng, key, pad_b=3, pad_r=8):
    b0, b1, r0, r1, _ = BIOMES[key]
    return rng.uniform(b0 + pad_b, b1 - pad_b), rng.uniform(r0 + pad_r, r1 - pad_r)


def place(s, aid, bearing, r, yaw=None, rng=None, scale=1.0, y=None, beam=True):
    pos = polar(bearing, r, y if y is not None else 0.4)
    s.animal(aid, pos, yaw=yaw if yaw is not None else (rng.uniform(0, 360) if rng else 0), scale=scale)
    rarity = ANIMALS[aid][1]
    if beam and rarity not in ("Common", "Uncommon"):
        loot_beam(s, pos, rarity)


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


def base_camp(s, rng):
    octagon(s, "Camp", 26, 0.8, 0.8, "#d9b77c")
    for k in range(8):
        b = 45 * k + 22.5
        if k in (3, 4):
            continue
        a0, a1 = polar(b - 18, 25.5, 0.8), polar(b + 18, 25.5, 0.8)
        fence(s, a0, a1, color="#8b5a2b", h=3)
    for b, col in ((-60, "#f2a541"), (60, "#4fa3e0"), (-120, "#e55b5b")):
        with s.frame(polar(b, 15, 0.8), -b):
            s.tri("Tent", (0, 0, 0), 10, 7, 9, C(col), R=angles(0, 90, 0))
            s.box("TentDoor", (0.3, 3.5, 2.6), (-4.35, 1.75, 0), C("#3a2a22"), rot=(0, 0, 0))
    with s.frame((0, 0.8, 0)):
        for k in range(8):
            a = math.radians(45 * k)
            s.box("FireStone", (1.3, 1.0, 1.3), (3 * math.cos(a), 0.5, 3 * math.sin(a)), C("#8d8d99"))
        s.beam("Log", (-2, 0.5, -1), (2, 0.5, 1), 0.8, C("#6b4226"))
        s.beam("Log", (-2, 0.5, 1), (2, 0.5, -1), 0.8, C("#6b4226"))
        s.box("Flame", (1.8, 2.4, 1.8), (0, 1.8, 0), C("#ff7a1a"), rot=(0, 45, 0), **NEON)
        s.box("FlameTip", (1.0, 1.6, 1.0), (0, 3.2, 0), C("#ffd23f"), rot=(0, 20, 0), **NEON)
    # Exit Portal at the south edge, facing the camp.
    with s.frame((0, 0.8, 20), 180):
        octagon(s, "PortalBase", 7, 1.2, 1.2, "#b9b3a7")
        for k in range(8):
            a = math.radians(22.5 + 45 * k)
            s.box("PortalFrame", (8.8, 2.6, 2.6), (10.5 * math.cos(a), 12.5 + 10.5 * math.sin(a), 0), C("#8d86a3"),
                  rot=(0, 0, 22.5 + 45 * k + 90))
        s.cyl("PortalSwirl", 0.6, 20, (0, 12.5, 0), C("#b86bff"), R=angles(0, 90, 0), transparency=0.3, **NEON)
        s.cyl("PortalCore", 0.8, 11, (0, 12.5, 0), C("#6fe8ff"), R=angles(0, 90, 0), transparency=0.25, **NEON)
        s.sign("PortalSign", (15, 3, 0.8), (0, 25.5, 0), "#3a2a5c", [L("EXIT PORTAL", "#d9b8ff")])
    s.box("SignPost", (0.9, 9, 0.9), (8, 5.3, 6), C("#8b5a2b"))
    for i, (text, yaw) in enumerate([("FOREST", -60), ("FROSTPEAK", -15), ("CAVERNS", 25), ("CANYON", 70)]):
        with s.frame((8, 7.6 - i * 1.6, 6), -yaw + 90):
            s.sign("Arrow", (6, 1.3, 0.3), (2.6, 0, 0), "#e8c48a", [L(text, "#5b3a22", 1, stroke=False)])
    chest(s, (-9, 0.8, -6), 30)


def toward(src, dst):
    """Yaw that makes a model at `src` face `dst` (models face -Z)."""
    dx, dz = dst[0] - src[0], dst[2] - src[2]
    return -math.degrees(math.atan2(dx, -dz))


def near_segment(p, a, b, dist):
    ax, az, bx, bz, px, pz = a[0], a[2], b[0], b[2], p[0], p[2]
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + t * vx), pz - (az + t * vz)) < dist


def build_grounds():
    rng = random.Random(11)
    s = Scene("grounds", env={
        "sky": [[0, "#3f9fff"], [0.6, "#a6dcff"], [1, "#e3f5ff"]], "fog": ["#e3f5ff", 480, 1250],
        "sun": {"dir": [-0.55, 1.0, 0.5], "intensity": 2.5}, "hemi": ["#ffffff", "#8fb070", 1.45],
        "bloom": [0.55, 0.5, 0.9],
    })
    ground(s, (5000, 5000), (0, 0, 0), "#86d45f")
    for key, (b0, b1, r0, r1, col) in BIOMES.items():
        patch(s, b0, b1, r0, r1, col, 0.35 if key != "canyon" else 0.3)
    for b in (-60, -15, 25, 68):
        s.box("Path", (7, 0.5, 100), polar(b, 74, 0.2), C("#d8b77a"), rot=(0, -b, 0))

    base_camp(s, rng)

    # Shot layouts (animal spots, camera spots) so nothing blocks the view.
    wolves = polar(-71, 142)
    forest_cam = polar(-60, 100, 10)
    fang = polar(-15, 182)
    fang_cam = polar(-15, 137, 5.6)
    snap = polar(63, 172)
    canyon_cam = polar(63, 124, 10)

    # Sunny Meadow around camp.
    for _ in range(120):
        b, r = rng.uniform(0, 360), rng.uniform(32, 112)
        flower(s, polar(b, r, 0), rng.choice(["#ff7ac8", "#ffd23f", "#ffffff", "#ff5a5a", "#b861ff"]), rng)
    for _ in range(16):
        bush(s, polar(rng.uniform(0, 360), rng.uniform(40, 110)), rng.choice(["#4fb84f", "#63c95a"]))
    for aid, b, r in [("Rabbit", -150, 45), ("Rabbit", 160, 60), ("Rabbit", -100, 70), ("Puffhop", 130, 52),
                      ("Puffhop", -30, 80), ("Deer", 100, 85), ("Deer", -125, 95), ("Rabbit", 20, 70),
                      ("Rabbit", -52, 88), ("Puffhop", -68, 90)]:
        place(s, aid, b, r, rng=rng)
    for i in range(12):
        p = polar(-25 + (i % 2) * 3, 34 + i * 4.5, 0.2)
        s.box("MysteryTrack", (0.9, 0.2, 1.4), p, C("#6fe8ff"), rot=(0, 25 + (i % 2) * 20, 0), **NEON)
    s.label(polar(-26, 92, 6), [L("???", "#6fe8ff")], h=4, aspect=2)

    # Whispering Forest with its river and a clearing where the wolf pack roams.
    for _ in range(75):
        b, r = in_biome(rng, "forest")
        p = polar(b, r)
        if 158 < r < 182 or math.dist(p, wolves) < 26 or near_segment(p, forest_cam, wolves, 12):
            continue
        tree(s, p, rng, k=rng.uniform(1.1, 1.7), kind=rng.choice(["round", "round", "pine"]))
    for i in range(8):
        b = -88 + i * 7.2
        s.box("River", (math.radians(8) * 170 * 1.2, 0.5, 13), polar(b, 170, 0.45), C("#4fb7ff"), rot=(0, -b, 0),
              material="Water", transparency=0.1)
    s.box("LogBridge", (4, 1.4, 18), polar(-58, 170, 1.0), C("#8b5a2b"), rot=(0, 58, 0))
    for i, off in enumerate([(-5, 0, 2), (6, 0, -3), (1, 0, 9)]):
        p = add(wolves, off)
        s.animal("Wolf", add(p, (0, 0.4, 0)), yaw=toward(p, forest_cam) + (i - 1) * 25)
        loot_beam(s, add(p, (0, 0.4, 0)), "Rare")
    boar = polar(-80, 150)
    s.animal("Boar", add(boar, (0, 0.4, 0)), yaw=toward(boar, forest_cam) + 30)
    loot_beam(s, add(boar, (0, 0.4, 0)), "Rare")
    place(s, "MossbackTortle", -64, 162, yaw=150)
    place(s, "MossbackTortle", -44, 190, rng=rng)
    place(s, "Deer", -50, 125, yaw=200)
    chest(s, polar(-52, 205, 0.4), 40, k=1.4)
    hunter = add(forest_cam, (0, -10, 0))
    hunter = add(hunter, tuple(0.16 * (w - c) for w, c in zip(wolves, hunter)))
    hunter = add(hunter, (-6.5, 0.4, 2.0))
    player(s, hunter, toward(hunter, wolves), "#ff5a5a", "#2b3a6b", hair="#3a2412")

    # Frostpeak Mountains.
    for b, r, k in [(-30, 245, 1.3), (-17, 268, 1.6), (-4, 250, 1.2), (-32, 205, 0.9), (2, 215, 0.8)]:
        mountain(s, polar(b, r), k, rng)
    s.box("FrozenLake", (44, 0.6, 28), polar(-24, 200, 0.5), C("#bfe8ff"), rot=(0, 24, 0), material="Ice",
          reflectance=0.2)
    for _ in range(26):
        b, r = in_biome(rng, "frost")
        p = polar(b, r)
        if math.dist(p, fang) < 16 or near_segment(p, fang_cam, fang, 10) or math.dist(p, polar(-24, 200)) < 26:
            continue
        tree(s, p, rng, leaf="#2f7a4a", k=rng.uniform(1.0, 1.4), kind="pine", snow=True)
    place(s, "Bear", -30, 150, rng=rng)
    place(s, "Bear", -4, 200, yaw=toward(polar(-4, 200), fang_cam) - 40)
    s.animal("FrostfangWolf", add(fang, (0, 0.4, 0)), yaw=toward(fang, fang_cam) - 18)
    for _ in range(90):
        d = rng.uniform(14, 44)
        t = d / math.dist(fang_cam, fang)
        p = tuple(c + (f - c) * t for c, f in zip(fang_cam, fang))
        p = add(p, (rng.uniform(-0.45, 0.45) * d, rng.uniform(-0.3, 0.4) * d, rng.uniform(-0.45, 0.45) * d))
        s.box("Snowflake", (0.16, 0.16, 0.16), p, C("#ffffff"), rot=(45, 45, 0), material="SmoothPlastic",
              shadow=False)
    chest(s, polar(-8, 230, 0.4), 10, k=1.7)

    # Crystal Caverns.
    with s.frame(polar(25, 250), -25):
        for i, (w, h, d, y, col) in enumerate([(80, 30, 50, 0, "#4e4863"), (62, 22, 40, 30, "#5d5775"),
                                                (40, 16, 28, 52, "#6d6784")]):
            s.bevel("CaveRock", (w, h, d), (0, y + h / 2, 0), C(col), b=5)
        s.box("CaveMouth", (18, 20, 2), (0, 10, -25.2), C("#120d1e"))
        for x, k in ((-4.5, 7), (4, 6.5), (0, 5), (-1, 5.5)):
            rock(s, (x, 0, -28 - (k - 5) * 0.8), (k, k * 0.85, k), "#8d8d99", rng)
        for x, y, z, h, col in [(-22, 30, -8, 22, "#7ff0ff"), (18, 30, -10, 18, "#ff8fe0"), (-8, 52, -6, 16, "#b07bff"),
                                (6, 68, 0, 20, "#7ff0ff"), (30, 0, -26, 16, "#b07bff"), (-32, 0, -26, 14, "#ff8fe0")]:
            crystal(s, (x, y, z), h, col, rng)
    for _ in range(22):
        b, r = in_biome(rng, "crystal", pad_r=6)
        if r > 215:
            continue
        crystal(s, polar(b, r, 0.3), rng.uniform(10, 24), rng.choice(["#7ff0ff", "#ff8fe0", "#b07bff"]), rng)
    place(s, "CrystalHare", 20, 190, yaw=190)
    place(s, "Voidwhisker", 32, 205, yaw=210)
    chest(s, polar(12, 215, 0.4), -20, k=2.0)

    # Scorched Canyon at sunset.
    for b, r, k in [(50, 235, 1.3), (64, 258, 1.2), (80, 238, 1.3), (90, 172, 0.9), (44, 168, 0.8)]:
        mesa(s, polar(b, r), k, rng)
    for b, r, w, d in [(70, 200, 26, 12), (56, 205, 16, 9), (82, 150, 14, 8)]:
        s.box("LavaRim", (w + 3, 0.6, d + 3), polar(b, r, 0.4), C("#3a2a2a"), rot=(0, -b + 20, 0))
        s.box("Lava", (w, 0.6, d), polar(b, r, 0.55), C("#ff6a1a"), rot=(0, -b + 20, 0), **NEON)
    for _ in range(12):
        b, r = in_biome(rng, "canyon")
        p = polar(b, r)
        if math.dist(p, snap) < 22 or near_segment(p, canyon_cam, snap, 12):
            continue
        with s.frame(p, rng.uniform(0, 90)):
            s.box("Cactus", (1.6, 6, 1.6), (0, 3, 0), C("#3fa347"))
            s.box("CactusArm", (1.2, 3, 1.2), (1.4, 4, 0), C("#3fa347"))
    s.animal("Sandsnapper", add(snap, (0, 0.4, 0)), yaw=toward(snap, canyon_cam) + 25)
    loot_beam(s, add(snap, (0, 0.4, 0)), "Legendary")
    ember = polar(72, 160)
    s.animal("EmberbackBoar", add(ember, (0, 0.4, 0)), yaw=toward(ember, canyon_cam) - 20)
    loot_beam(s, add(ember, (0, 0.4, 0)), "Epic")
    place(s, "Thunderhoof", 76, 214, yaw=toward(polar(76, 214), canyon_cam) + 70)
    place(s, "PhoenixFox", 56, 218, yaw=toward(polar(56, 218), canyon_cam) - 10)
    chest(s, polar(74, 250, 0.4), -30, k=2.2)

    # Sky Isles floating high above the far side.
    for b, r, y, size in [(-18, 330, 62, 34), (-2, 360, 80, 40), (14, 330, 70, 30), (6, 405, 100, 36),
                          (-14, 395, 92, 28)]:
        island(s, polar(b, r, y), size, rng, trees=1 if size < 35 else 2)
    for b, r, y, k in [(-8, 330, 50, 1.4), (20, 375, 72, 1.6), (-24, 360, 76, 1.2), (8, 300, 88, 1.0)]:
        cloud(s, polar(b, r, y), k, rng)
    place(s, "StarlightKitsune", -2, 360, yaw=200, y=81.8)
    place(s, "SkyfinWhale", 8, 345, yaw=230, y=58, beam=False)
    loot_beam(s, polar(8, 345, 58), "Mythic", h=110)

    # Other hunters, and hills and trees around the edge of the grounds.
    for b, r, yaw, shirt in [(-20, 118, 20, "#45a6ff"), (62, 108, -60, "#ffd23f"), (10, 60, 0, "#b861ff"),
                             (-140, 30, 200, "#3fdc5a")]:
        player(s, polar(b, r, 0.4), -b + yaw, shirt, "#2b3a6b", hair=rng.choice(["#3a2412", "#111", "#e8c07a"]))
    for _ in range(90):
        b, r = rng.uniform(0, 360), rng.uniform(300, 470)
        if -30 < ((b + 180) % 360) - 180 < 30:
            continue
        tree(s, polar(b, r), rng, k=rng.uniform(1.2, 1.8), kind=rng.choice(["round", "pine"]))
    for b in range(0, 360, 20):
        k = rng.uniform(1.2, 2.2)
        s.bevel("Hill", (70 * k, 22 * k, 50 * k), polar(b + rng.uniform(-6, 6), rng.uniform(520, 620), 8 * k),
                C(rng.choice(["#6cbf4a", "#78c95a", "#5fae45"])), b=12 * k, R=angles(0, -b, 0))

    s.shot("overview", (20, 245, 205), (0, 0, -135), fov=56, shadow={"center": [0, 0, -130], "radius": 330})
    s.shot("forest", forest_cam, add(wolves, (0, 4, 0)), fov=50, shadow={"center": list(wolves), "radius": 70})
    s.shot("canyon", canyon_cam, add(snap, (0, 5, 0)), fov=56, shadow={"center": list(snap), "radius": 80}, env={
        "sky": [[0, "#40306e"], [0.45, "#d4655a"], [0.8, "#ffab6a"], [1, "#ffd9a0"]],
        "fog": ["#f2a67a", 170, 700], "sun": {"dir": [-1.0, 0.32, 0.25], "color": "#ffb070", "intensity": 2.6},
        "hemi": ["#ffcf9e", "#6a4a5a", 1.15], "bloom": [0.7, 0.55, 0.85]})
    s.shot("viewfinder", fang_cam, add(fang, (0, 5.6, 0)), fov=29, shadow={"center": list(fang), "radius": 60},
           env={"sky": [[0, "#6aa9e0"], [0.6, "#c4e2ff"], [1, "#f4fbff"]], "fog": ["#e8f4ff", 80, 520]},
           hud=viewfinder_hud())
    return s


def main():
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    for scene in (build_hub(), build_grounds()):
        (out / f"{scene.id}.json").write_text(json.dumps(scene.export()))
        print(f"{scene.id}: {len(scene.parts)} parts, {len(scene.models)} animals, {len(scene.shots)} shots")


if __name__ == "__main__":
    main()
