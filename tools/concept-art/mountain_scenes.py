#!/usr/bin/env python3
"""Concept art of the Mountain Range, in the same style as the first forest concept art: blocky studded scenes that
look like screenshots from the game, with the HUD on top.

The Mountain Range climbs in five zones, each higher than the one before, with a speed gate at the top of every
ramp:

    Pine Foothills   green hills and pines, the entrance gate             (Common)
    Canyon Pass      a red-rock canyon with a river, a rope bridge, a waterfall and crystal caves
    Alpine Lakes     turquoise lakes, bamboo groves and snowy pines
    Frost Ridge      snow, ice crystals and a blizzard
    The Summit       the peak at night under the northern lights, with the griffin's nest and the rune shrine

It is about 240 x 760 studs and climbs 120 studs: roughly four times the Dark Woods.

The animals in these pictures are quick stand-ins built for the drawings (see mountain_animals.py for the real
designs); this script makes no Roblox models.

    python3 tools/concept-art/mountain_scenes.py    -> concept-art/mountain-range/*.png (needs node + playwright)
"""

import json
import math
import os
import random
import shutil
import subprocess
from pathlib import Path

from scenes import (L, NEON, RARITY, C, Scene, bezier, cloud, hotbar, lasso_loop, model_point, mountain, pill,
                    player, rope, toward, top_bar, tree)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
from lib import add, angles  # noqa: E402  (scenes.py put animal-models on the path)

WIDTH, DEPTH = 240, 150
ZONES = [  # name, ground height, ground colour, speed
    ("PINE FOOTHILLS", 0, "#6fcf5a", "0"),
    ("CANYON PASS", 12, "#d9874f", "25K"),
    ("ALPINE LAKES", 40, "#8fd37a", "60K"),
    ("FROST RIDGE", 74, "#f2f6ff", "120K"),
    ("THE SUMMIT", 112, "#e6ecf8", "250K"),
]
GLOW = dict(NEON)


def z0(i):
    return -DEPTH * i


def zc(i):
    return z0(i) - DEPTH / 2


def H(i):
    return ZONES[i][1]


# --------------------------------------------------------------- stand-in animals ---
# Quick blocky versions of the designs, facing -Z.

def eyes(s, x, y, z, k=1.0, glow=None):
    for sx in (-1, 1):
        s.box("EyeWhite", (0.1, 0.8 * k, 0.65 * k), (sx * x, y, z), C("#ffffff"), material="SmoothPlastic",
              shadow=False)
        s.box("Pupil", (0.12, 0.5 * k, 0.36 * k), (sx * (x + 0.02), y - 0.05 * k, z - 0.1 * k),
              C(glow or "#1b1420"), shadow=False, **({"material": "Neon"} if glow else {"material": "SmoothPlastic"}))


def quad(s, pos, yaw, k, coat, *, L=6.0, W=3.4, Hb=3.2, leg=3.0, lw=0.95, legc=None, hoof=None, belly=None,
         head=(2.8, 2.6, 2.6), head_up=1.4, snout=None, ears="tri", earc=None, horns=None, tail="short",
         tailc=None, eye_glow=None, extra=None, headc=None):
    with s.frame(pos, yaw):
        S = lambda v: tuple(x * k for x in v)
        legc = legc or coat
        y = leg
        s.bevel("Body", S((W, Hb, L)), S((0, y + Hb / 2, 0)), C(coat), b=0.6 * k)
        if belly:
            s.box("Belly", S((W * 1.02, Hb * 0.3, L * 0.8)), S((0, y + Hb * 0.15, 0)), C(belly))
        for sx in (-1, 1):
            for sz in (-1, 1):
                p = (sx * (W / 2 - lw / 2), y / 2, sz * (L / 2 - lw / 2 - 0.3))
                s.box("Leg", S((lw, y + 0.4, lw)), S(add(p, (0, 0.2, 0))), C(legc))
                if hoof:
                    s.box("Hoof", S((lw + 0.1, 0.5, lw + 0.1)), S((p[0], 0.25, p[2])), C(hoof))
        hw, hh, hd = head
        hz = -L / 2 - hd * 0.25
        hy = y + Hb * 0.6 + head_up
        s.bevel("Head", S(head), S((0, hy, hz)), C(headc or coat), b=0.5 * k)
        if snout:
            col, sw, sh, sd = snout
            s.box("Snout", S((sw, sh, sd)), S((0, hy - hh * 0.2, hz - hd / 2 - sd / 2 + 0.1)), C(col))
            s.box("Nose", S((sw * 0.5, sh * 0.3, 0.2)), S((0, hy - hh * 0.2 + sh * 0.25, hz - hd / 2 - sd)),
                  C("#2a1a1a"), material="SmoothPlastic")
        eyes(s, hw / 2 * k * 0.98, hy * k + 0.3 * k, (hz - hd * 0.2) * k, k, glow=eye_glow)
        ec = C(earc or coat)
        for sx in (-1, 1):
            if ears == "tri":
                s.wedge("Ear", S((0.4, 1.2, 0.9)), S((sx * hw * 0.32, hy + hh / 2 + 0.5, hz + 0.3)), ec)
            elif ears == "round":
                s.box("Ear", S((0.9, 0.9, 0.4)), S((sx * hw * 0.38, hy + hh / 2 + 0.3, hz + 0.2)), ec)
            elif ears == "long":
                s.box("Ear", S((0.6, 3.2, 0.4)), S((sx * hw * 0.25, hy + hh / 2 + 1.5, hz + 0.3)), ec,
                      rot=(10, 0, sx * -8))
            elif ears == "side":
                s.box("Ear", S((1.2, 0.4, 0.7)), S((sx * (hw / 2 + 0.5), hy + 0.5, hz + 0.3)), ec,
                      rot=(0, 0, sx * -15))
        if horns:
            kind, hc = horns
            for sx in (-1, 1):
                if kind == "curl":
                    for j in range(6):
                        a = math.radians(-90 + j * 55)
                        p = (sx * (hw / 2 + 0.4), hy + 0.6 + 1.0 * math.sin(a), hz + 0.4 + 1.0 * math.cos(a))
                        s.box("Horn", S((0.8, 0.8 - j * 0.06, 0.8 - j * 0.06)), S(p), C(hc))
                elif kind == "back":
                    for j in range(6):
                        p = (sx * hw * 0.25, hy + hh / 2 + 0.6 + j * 0.55 - j * j * 0.04, hz + 0.6 + j * 0.65)
                        s.box("Horn", S((0.45, 0.5, 0.6)), S(p), C(hc), rot=(-35, 0, 0))
                elif kind == "tiny":
                    s.box("Horn", S((0.35, 1.0, 0.35)), S((sx * hw * 0.25, hy + hh / 2 + 0.4, hz + 0.3)), C(hc),
                          rot=(-25, 0, 0))
                elif kind == "yak":
                    s.box("Horn", S((1.3, 0.45, 0.45)), S((sx * (hw / 2 + 0.6), hy + 0.9, hz + 0.2)), C(hc))
                    s.box("HornTip", S((0.4, 1.1, 0.4)), S((sx * (hw / 2 + 1.1), hy + 1.5, hz + 0.2)), C(hc))
        if tail:
            tc = C(tailc or coat)
            tz = L / 2
            if tail == "short":
                s.box("Tail", S((0.6, 0.6, 0.9)), S((0, y + Hb * 0.8, tz + 0.3)), tc)
            elif tail == "fluffy":
                s.bevel("Tail", S((1.6, 1.6, 1.6)), S((0, y + Hb * 0.6, tz + 0.6)), tc, b=0.4 * k)
            elif tail == "long":
                for j in range(5):
                    s.box("Tail", S((0.9, 0.9, 1.0)), S((0, y + Hb * 0.5 + j * 0.5, tz + 0.5 + j * 0.8)), tc)
            elif tail == "ringed":
                for j in range(6):
                    s.box("Tail", S((1.2, 1.1, 1.0)), S((0, y + Hb * 0.5 + j * 0.7, tz + 0.6 + j * 0.3)),
                          tc if j % 2 == 0 else C("#f2c49a"))
        if extra:
            extra(s, S, y, Hb, L, W, hy, hz)


def mk_label(s, pos, name, rarity, h):
    s.label(add(pos, (0, h, 0)), [L(name.upper(), RARITY[rarity]), L(rarity.upper(), "#ffffff", 0.7)], h=2.3)


def critter(s, kind, pos, yaw, k=1.0, label=True):
    """The stand-ins. Returns nothing; adds a name label above it like in the game."""
    info = {}

    def ice_back(s, S, y, Hb, L, W, hy, hz, color="#7fe3ff", n=4):
        for j in range(n):
            s.shard("IceSpike", S((0, y + Hb, -L / 3 + j * L / (n + 1))), 0.7 * k, (1.6 + 0.6 * (j % 2)) * k,
                    C(color), material="Neon", shadow=False)

    if kind == "PebbleMarmot":
        quad(s, pos, yaw, k, "#b07a45", L=3.2, W=3.0, Hb=3.0, leg=0.8, belly="#ecc995", head=(2.6, 2.3, 2.2),
             head_up=1.2, snout=("#ecc995", 1.4, 0.9, 0.6), ears="round", tail="short",
             extra=lambda s, S, y, Hb, L, W, hy, hz: s.bevel("Pebble", S((1.2, 0.7, 1.0)), S((0, hy + 1.5, hz)),
                                                            C("#9aa0ad"), b=0.25 * k))
        info = ("Pebble Marmot", "Common", 7 * k)
    elif kind == "PikaPuff":
        with s.frame(pos, yaw):
            s.bevel("Body", (3.2 * k, 3.0 * k, 3.0 * k), (0, 1.6 * k, 0), C("#c9a27a"), b=1.0 * k)
            for sx in (-1, 1):
                s.box("Ear", (1.1 * k, 1.1 * k, 0.4 * k), (sx * 0.9 * k, 3.4 * k, 0), C("#c9a27a"))
            eyes(s, 0.9 * k * 0.9, 2.0 * k, -1.52 * k, k * 0.8)
        info = ("Pika Puff", "Common", 5 * k)
    elif kind == "CliffKid":
        quad(s, pos, yaw, k, "#f3efe6", L=4.4, W=2.4, Hb=2.2, leg=2.4, lw=0.6, hoof="#4a3a30", head=(2.0, 2.0, 2.0),
             snout=("#ffffff", 1.2, 0.9, 0.8), ears="side", horns=("tiny", "#b9a690"), tail="short")
        info = ("Cliff Kid", "Common", 7.5 * k)
    elif kind == "SnowshoeHare":
        quad(s, pos, yaw, k, "#f6f8fc", L=3.6, W=2.6, Hb=2.4, leg=0.8, head=(2.2, 2.0, 2.0), head_up=1.0,
             ears="long", earc="#f6f8fc", tail="fluffy", hoof="#9fc8f0")
        info = ("Snowshoe Hare", "Common", 9 * k)
    elif kind == "BighornRam":
        quad(s, pos, yaw, k, "#c4925e", L=6.0, W=3.0, Hb=2.8, leg=3.0, lw=0.8, belly="#f2e2c8", hoof="#3a2a20",
             head=(2.4, 2.4, 2.4), snout=("#f2e2c8", 1.6, 1.2, 1.0), ears="side", horns=("curl", "#d9c2a0"))
        info = ("Bighorn Ram", "Rare", 10 * k)
    elif kind == "AlpineIbex":
        quad(s, pos, yaw, k, "#8d7a62", L=5.6, W=2.8, Hb=2.6, leg=3.0, lw=0.7, hoof="#2e241c",
             head=(2.2, 2.2, 2.2), snout=("#a8977f", 1.4, 1.1, 1.0), ears="side", horns=("back", "#b8a48a"))
        info = ("Alpine Ibex", "Rare", 11 * k)
    elif kind == "RedPanda":
        quad(s, pos, yaw, k, "#d4582a", L=4.2, W=2.4, Hb=2.0, leg=1.4, lw=0.7, legc="#2e1a16",
             head=(2.4, 2.2, 2.0), head_up=0.8, snout=("#fff4e6", 1.2, 0.8, 0.6), ears="tri", earc="#d4582a",
             tail="ringed")
        info = ("Red Panda", "Rare", 7 * k)
    elif kind == "MountainYak":
        def blanket(s, S, y, Hb, L, W, hy, hz):
            s.box("Blanket", S((W + 0.2, 1.4, 2.6)), S((0, y + Hb - 0.3, 0)), C("#c4302b"))
            s.box("BlanketStripe", S((W + 0.3, 0.3, 2.7)), S((0, y + Hb - 0.6, 0)), C("#2bb0a8"))
            s.bevel("Snow", S((W - 0.4, 0.6, 2.2)), S((0, y + Hb + 0.6, 0)), C("#ffffff"), b=0.2 * k)
            s.box("Bell", S((0.7, 0.8, 0.7)), S((0, hy - 1.8, hz - 0.2)), C("#ffd23f"), reflectance=0.2)
            s.box("Fringe", S((W + 0.3, 1.0, L - 0.4)), S((0, y + 0.1, 0)), C("#6b4c38"))
        quad(s, pos, yaw, k, "#4a3426", L=7.4, W=4.6, Hb=4.0, leg=2.4, lw=1.2, hoof="#1e140e",
             head=(2.8, 2.6, 2.6), head_up=-0.4, snout=("#6b4c38", 1.8, 1.4, 0.8), ears="side",
             horns=("yak", "#efe6d2"), tail="short", extra=blanket)
        info = ("Mountain Yak", "Epic", 11 * k)
    elif kind == "GeodeTortoise":
        with s.frame(pos, yaw):
            s.bevel("Shell", (5.0 * k, 3.0 * k, 5.6 * k), (0, 2.4 * k, 0), C("#8a8fa8"), b=1.2 * k)
            s.box("ShellRim", (5.4 * k, 0.6 * k, 6.0 * k), (0, 1.0 * k, 0), C("#6f748a"))
            for sx in (-1, 1):
                for sz in (-1, 1):
                    s.box("Leg", (1.0 * k, 1.2 * k, 1.0 * k), (sx * 2.0 * k, 0.6 * k, sz * 2.0 * k), C("#8aa86a"))
            s.bevel("Head", (1.6 * k, 1.5 * k, 1.8 * k), (0, 1.8 * k, -3.4 * k), C("#8aa86a"), b=0.4 * k)
            eyes(s, 0.8 * k, 2.0 * k, -3.9 * k, k * 0.7)
            for j, (x, z, h, c) in enumerate(((-0.8, 0.3, 2.4, "#b46bff"), (0.3, -0.4, 3.2, "#d9a6ff"),
                                              (0.9, 0.6, 2.2, "#7fd8ff"))):
                s.shard("Geode", (x * k, 3.6 * k, z * k), 0.8 * k, h * k, C(c), material="Neon", shadow=False)
        info = ("Geode Tortoise", "Epic", 9 * k)
    elif kind == "PeakEagle":
        with s.frame(pos, yaw):
            s.bevel("Body", (2.4 * k, 3.4 * k, 2.6 * k), (0, 2.4 * k, 0), C("#6b4a2e"), b=0.7 * k)
            s.bevel("Head", (2.0 * k, 1.8 * k, 2.0 * k), (0, 4.8 * k, -0.4 * k), C("#f2e6cf"), b=0.5 * k)
            s.box("Beak", (0.7 * k, 0.6 * k, 1.0 * k), (0, 4.6 * k, -1.8 * k), C("#ffc93c"))
            eyes(s, 0.98 * k, 5.0 * k, -0.9 * k, k * 0.7)
            for sx in (-1, 1):
                s.box("Wing", (5.5 * k, 0.4 * k, 2.4 * k), (sx * 3.8 * k, 3.4 * k, 0.4 * k), C("#5a3a20"),
                      rot=(0, 0, sx * 12))
                s.box("WingTip", (1.6 * k, 0.45 * k, 2.0 * k), (sx * 6.6 * k, 4.0 * k, 0.6 * k), C("#ffc93c"),
                      rot=(0, 0, sx * 12))
        info = ("Peak Eagle", "Epic", 8 * k)
    elif kind == "SnowLeopard":
        def spots(s, S, y, Hb, L, W, hy, hz):
            for j, (x, yy, z) in enumerate(((W / 2 + 0.05, y + Hb * 0.6, -1.2), (W / 2 + 0.05, y + Hb * 0.4, 0.8),
                                            (-W / 2 - 0.05, y + Hb * 0.55, -0.2), (0, y + Hb + 0.05, 0.6))):
                s.box("Rosette", S((0.15 if abs(x) > 0.1 else 0.8, 0.8 if abs(x) > 0.1 else 0.15, 0.8)),
                      S((x, yy, z)), C("#5ee0ff"), **GLOW)
        quad(s, pos, yaw, k, "#e6e8ee", L=6.4, W=2.8, Hb=2.4, leg=2.2, lw=0.9, head=(2.6, 2.3, 2.3),
             snout=("#ffffff", 1.4, 0.9, 0.7), ears="round", tail="long", eye_glow="#5ee0ff", extra=spots)
        info = ("Snow Leopard", "Legendary", 9 * k)
    elif kind == "FrostfangWolf":
        quad(s, pos, yaw, k, "#dfe9f5", L=6.0, W=2.8, Hb=2.6, leg=2.6, lw=0.85, head=(2.4, 2.3, 2.4),
             snout=("#f6faff", 1.4, 1.0, 1.4), ears="tri", tail="fluffy", eye_glow="#7fe3ff",
             extra=lambda s, S, y, Hb, L, W, hy, hz: ice_back(s, S, y, Hb, L, W, hy, hz))
        info = ("Frostfang Wolf", "Legendary", 9.5 * k)
    elif kind == "LittleYeti":
        with s.frame(pos, yaw):
            s.bevel("Body", (3.6 * k, 4.4 * k, 3.0 * k), (0, 3.2 * k, 0), C("#ffffff"), b=1.0 * k)
            s.bevel("Face", (2.2 * k, 1.8 * k, 0.4 * k), (0, 4.4 * k, -1.5 * k), C("#8fb3e6"), b=0.3 * k)
            eyes(s, 0.6 * k, 4.6 * k, -1.75 * k, k * 0.8)
            for sx in (-1, 1):
                s.box("Arm", (1.0 * k, 2.6 * k, 1.0 * k), (sx * 2.3 * k, 3.0 * k, -0.4 * k), C("#ffffff"))
                s.box("Foot", (1.3 * k, 0.8 * k, 1.6 * k), (sx * 0.9 * k, 0.4 * k, -0.2 * k), C("#8fb3e6"))
                s.box("Horn", (0.4 * k, 1.0 * k, 0.4 * k), (sx * 1.1 * k, 5.9 * k, 0), C("#c9cfe8"))
            s.bevel("Snowball", (1.6 * k, 1.6 * k, 1.6 * k), (2.5 * k, 4.6 * k, -1.2 * k), C("#ffffff"), b=0.5 * k)
        info = ("Little Yeti", "Legendary", 9 * k)
    elif kind == "SkyGriffin":
        def wings(s, S, y, Hb, L, W, hy, hz):
            for sx in (-1, 1):
                for j in range(4):
                    s.box("Feather", S((1.3, 0.35, 5.0 - j * 0.6)), S((sx * (W / 2 + 0.8 + j * 1.3), y + Hb + 1.5 + j * 1.1,
                                                                          -0.6 + j * 0.4)), C("#f6f2e8" if j < 3 else "#ffc93c"),
                          rot=(0, 0, sx * -35))
            s.box("Beak", S((0.9, 0.8, 1.3)), S((0, hy - 0.2, hz - 1.6)), C("#ffc93c"))
        quad(s, pos, yaw, k, "#e2a93a", L=6.4, W=3.2, Hb=2.8, leg=2.6, lw=1.0, head=(2.6, 2.6, 2.6),
             ears="tri", earc="#ffffff", tail="long", tailc="#c47a1c", extra=wings, headc="#ffffff")
        info = ("Sky Griffin", "Mythic", 14 * k)
    elif kind == "GlacierMammoth":
        def mammoth(s, S, y, Hb, L, W, hy, hz):
            ice_back(s, S, y, Hb, L, W, hy, hz, n=5)
            for sx in (-1, 1):
                for j in range(4):
                    s.box("Tusk", S((0.5, 0.5, 0.9)), S((sx * 0.9, hy - 1.4 + j * 0.3, hz - 1.4 - j * 0.6)),
                          C("#bff3ff"), material="Neon", shadow=False)
            for j in range(4):
                s.box("Trunk", S((0.9, 0.9, 0.8)), S((0, hy - 1.0 - j * 0.8, hz - 1.5 - j * 0.1)), C("#cfe3f2"))
        quad(s, pos, yaw, k, "#cfe3f2", L=6.8, W=4.8, Hb=4.2, leg=2.6, lw=1.4, head=(3.6, 3.6, 3.0), head_up=0.4,
             ears="side", tail="short", extra=mammoth)
        info = ("Glacier Mammoth", "Mythic", 14 * k)
    elif kind == "AuroraDragon":
        cols = ["#5effb0", "#4fe8d8", "#3fd6ff", "#6f9cff", "#9a7bff", "#b45cff"]
        with s.frame(pos, yaw):
            prev = None
            n = 26
            for j in range(n):
                t = j / (n - 1)
                p = (12 * k * math.sin(t * 2.6 * math.pi), 6 * k * math.sin(t * 1.4 * math.pi) + 4 * k,
                     -18 * k + 36 * k * t)
                if prev:
                    s.beam("DragonBody", prev, p, (2.6 - 1.4 * t) * k, C(cols[min(5, int(t * 6))]), material="Neon",
                           shadow=False, transparency=0.15)
                if j % 3 == 1:
                    s.shard("Spine", add(p, (0, (1.2 - 0.6 * t) * k, 0)), 0.5 * k, 1.4 * k, C("#e9ddff"),
                            material="Neon", shadow=False)
                prev = p
            head = (0, 4 * k, -19.5 * k)
            s.bevel("DragonHead", (3.0 * k, 2.4 * k, 3.4 * k), head, C("#4fd8e8"), b=0.6 * k)
            eyes(s, 1.5 * k, 4.6 * k, -20.6 * k, k, glow="#ffe14d")
            for sx in (-1, 1):
                s.beam("Antler", add(head, (sx * 0.8 * k, 1.0 * k, 0.6 * k)),
                       add(head, (sx * 2.0 * k, 3.4 * k, 2.0 * k)), 0.45 * k, C("#ffe9a8"))
        info = ("Aurora Dragon", "Secret", 14 * k)
    if label and info:
        mk_label(s, pos, info[0], info[1], info[2])


# -------------------------------------------------------------------- world ---

def pine(s, pos, rng, k=1.0, snow=False):
    tree(s, pos, rng, leaf=rng.choice(["#2f8f3a", "#3fa347", "#2a7f44"]), k=k, kind="pine", snow=snow)


def flowers(s, center, rng, n, spread):
    for _ in range(n):
        p = add(center, (rng.uniform(-spread, spread), 0, rng.uniform(-spread, spread)))
        s.box("Flower", (0.9, 0.9, 0.9), add(p, (0, 0.6, 0)), C(rng.choice(["#ffffff", "#ffd23f", "#ff7ac8",
                                                                             "#b98cff"])), rot=(0, 30, 45))


def rock(s, pos, size, rng, color="#9aa0ad"):
    s.bevel("Rock", size, add(pos, (0, size[1] / 2, 0)), C(color), b=min(size) * 0.28,
            R=angles(0, rng.uniform(0, 90), 0))


def gate(s, i, rng):
    """The speed gate at the top of the ramp into zone i."""
    name, h, _, speed = ZONES[i]
    glow = {"CANYON PASS": "#ffb35a", "ALPINE LAKES": "#5ef0e0", "FROST RIDGE": "#8fe9ff",
            "THE SUMMIT": "#c38bff"}[name]
    with s.frame((0, h, z0(i) - 2), 180):
        for x in (-16, 16):
            s.bevel("GatePillar", (5, 24, 5), (x, 12, 0), C("#8a8fa8"), b=1)
            s.box("GatePillarCap", (6.4, 2, 6.4), (x, 25, 0), C("#ffffff"))
        s.box("GateBeam", (40, 4, 5), (0, 23, 0), C("#6b4424"))
        s.sign("GateSign", (30, 7.5, 1), (0, 29, 0), "#1d2033",
               [L(name, "#ffffff", 0.9), L(f"{speed} SPEED RECOMMENDED", "#ffd84a", 0.75)], glow=True)
        s.box("SpeedBarrier", (27, 20, 0.4), (0, 10.5, 0), C(glow), transparency=0.7, material="Glass", shadow=False)


def zone_block(s, i):
    """The zone's ground, a cliff down to the zone before it, and a ramp up the middle."""
    name, h, col, _ = ZONES[i]
    s.box("ZoneGround", (WIDTH, h + 4, DEPTH), (0, (h - 4) / 2, zc(i)), C(col))
    if i > 0:
        prev = H(i - 1)
        rise = h - prev
        run = max(20, rise * 1.6)
        # Ramp: a wedge rising towards -Z, ending at this zone's front edge.
        s.wedge("Ramp", (24, rise, run), (0, prev + rise / 2, z0(i) + run / 2), C("#c9a77a"), rot=(0, 180, 0))
        for x in (-13, 13):
            s.wedge("RampRail", (1.2, rise + 1.5, run), (x, prev + rise / 2 + 0.75, z0(i) + run / 2), C("#6b4424"),
                    rot=(0, 180, 0))


def foothills(s, rng):
    i = 0
    # The path from the entrance gate to the first ramp.
    s.box("Path", (14, 0.3, DEPTH), (0, 0.15, zc(i)), C("#d9b98c"))
    # Entrance gate: two log towers and a big sign (turned so the sign faces the player coming in).
    with s.frame((0, 0, 4), 180):
        for x in (-14, 14):
            for j in range(4):
                s.box("GateLog", (6, 4, 6), (x, 2 + j * 4, 0), C("#8b5a2b" if j % 2 == 0 else "#a36a36"))
            s.box("GateRoof", (8, 1.6, 8), (x, 17, 0), C("#e0453a"))
            pine(s, (x, 18, 0), rng, 0.45, snow=True)
        s.sign("EntranceSign", (34, 8, 1.4), (0, 22, 0), "#2b3f6b",
               [L("MOUNTAIN RANGE", "#ffffff", 1.0), L("CLIMB TO THE SUMMIT!", "#ffd84a", 0.7)], glow=True)
        s.box("SignBeam", (30, 1.4, 1.4), (0, 17.5, 0), C("#6b4424"))
    # Signpost.
    s.box("Signpost", (0.8, 9, 0.8), (12, 4.5, -16), C("#6b4424"))
    for j, (txt, col) in enumerate((("SUMMIT ^", "#c38bff"), ("CANYON PASS ^", "#ffb35a"), ("< BASE CAMP", "#6fcf5a"))):
        s.sign("SignBoard", (8, 1.6, 0.4), (12 + (-1.5 if j == 2 else 1.5), 8 - j * 2, -16), "#a36a36",
               [L(txt, col, 0.6)])
    # Base camp: tents and a campfire.
    for x, z, c in ((-40, -30, "#e0453a"), (-56, -44, "#2b8fd8"), (-32, -52, "#ffb52e")):
        with s.frame((x, 0, z), rng.uniform(0, 90)):
            s.wedge("Tent", (6, 5, 4), (0, 2.5, -2), C(c))
            s.wedge("Tent", (6, 5, 4), (0, 2.5, 2), C(c), rot=(0, 180, 0))
    s.box("Campfire", (2, 0.6, 2), (-44, 0.3, -42), C("#5a3a20"))
    s.box("Fire", (1.2, 1.6, 1.2), (-44, 1.4, -42), C("#ff9a2a"), **GLOW)
    for _ in range(70):
        x = rng.uniform(-WIDTH / 2 + 6, WIDTH / 2 - 6)
        if abs(x) < 14:
            continue
        p = (x, 0, rng.uniform(z0(i) - 8, z0(i + 1) + 25))
        if -66 < x < -24 and -60 < p[2] < -20:
            continue
        pine(s, p, rng, rng.uniform(0.8, 1.4))
    for _ in range(14):
        flowers(s, (rng.uniform(-90, 90), 0, rng.uniform(-130, -10)), rng, 4, 4)
    for _ in range(8):
        rock(s, (rng.uniform(-100, 100), 0, rng.uniform(-140, -10)), (rng.uniform(3, 7),) * 3, rng)
    critter(s, "PebbleMarmot", (18, 0, -38), 200, 1.0)
    critter(s, "PikaPuff", (-14, 0, -60), 160, 1.0)
    critter(s, "CliffKid", (26, 0, -70), 230, 1.0)
    critter(s, "CliffKid", (34, 0, -76), 250, 0.8, label=False)
    rock(s, (32, 0, -92), (8, 6, 8), rng)
    critter(s, "CliffKid", (32, 6, -92), 210, 0.8, label=False)


def canyon(s, rng):
    i = 1
    h = H(i)
    # Canyon walls: layered red rock on both sides.
    bands = ["#c9643a", "#e07b3c", "#c9643a", "#f0a15a", "#b85532"]
    for side in (-1, 1):
        for j in range(8):
            z = z0(i) - 10 - j * 18
            top = rng.uniform(40, 62)
            x = side * (WIDTH / 2 - 26 - rng.uniform(0, 8))
            y = h
            for b, col in enumerate(bands):
                bh = top / len(bands)
                w = 44 - b * 4
                s.bevel("CanyonWall", (w, bh, 20), (x, y + bh / 2, z), C(col), b=1.2)
                y += bh
    # The river, with a rope bridge and a waterfall.
    s.box("River", (22, 0.5, DEPTH), (-34, h + 0.25, zc(i)), C("#3fb6ff"), material="Glass", transparency=0.15)
    for j in range(8):
        s.box("Foam", (rng.uniform(2, 5), 0.3, rng.uniform(1, 3)), (-34 + rng.uniform(-9, 9), h + 0.55,
                                                                    zc(i) + rng.uniform(-70, 70)), C("#ffffff"))
    wf_x, wf_z = -62, zc(i) - 20
    s.box("Waterfall", (10, 46, 3), (wf_x + 6, h + 23, wf_z), C("#7fd6ff"), material="Glass", transparency=0.25,
          shadow=False)
    for j in range(5):
        s.box("WaterfallStreak", (1.2, 44, 0.5), (wf_x + 2 + j * 2, h + 23, wf_z - 1.8), C("#ffffff"),
              transparency=0.3, shadow=False)
    for j in range(6):
        s.bevel("Mist", (rng.uniform(4, 7),) * 3, (wf_x + 6 + rng.uniform(-5, 5), h + 1.5, wf_z + rng.uniform(-4, 4)),
                C("#ffffff"), b=1.2, transparency=0.35)
    bz = zc(i) + 30
    for j in range(14):
        x = -48 + j * 2.1
        sag = 1.4 * math.sin(math.pi * j / 13)
        s.box("BridgePlank", (1.8, 0.4, 5), (x, h + 4 - sag, bz), C("#a36a36" if j % 2 else "#8b5a2b"))
    for zz in (bz - 2.6, bz + 2.6):
        rope(s, bezier((-49, h + 7, zz), (-34, h + 4, zz), (-19, h + 7, zz), 10), 0.3)
    s.box("Path", (14, 0.3, DEPTH), (0, h + 0.15, zc(i)), C("#e8b98a"))
    # Crystal caves in the right wall, with the Geode Tortoise in front.
    cave = (WIDTH / 2 - 52, h, zc(i) - 34)
    s.box("CaveMouth", (2, 14, 16), add(cave, (-2, 7, 0)), C("#2a1a3a"))
    for j in range(5):
        s.shard("CaveCrystal", add(cave, (-4 - rng.uniform(0, 4), 0, rng.uniform(-7, 7))), 1.2, rng.uniform(3, 6),
                C(rng.choice(["#b46bff", "#d9a6ff", "#7fd8ff"])), material="Neon", shadow=False)
    critter(s, "GeodeTortoise", add(cave, (-12, 0, 0)), 270, 1.0)
    # Animals.
    critter(s, "BighornRam", (10, h, zc(i) + 10), 160, 1.0)
    critter(s, "BighornRam", (20, h, zc(i) - 6), 200, 0.85, label=False)
    ledge = (WIDTH / 2 - 44, h + 30, zc(i) + 30)
    critter(s, "AlpineIbex", ledge, 250, 1.0)
    critter(s, "PeakEagle", (-10, h + 46, zc(i) - 10), 120, 1.3)


def lakes(s, rng):
    i = 2
    h = H(i)
    s.box("Path", (14, 0.3, DEPTH), (0, h + 0.15, zc(i)), C("#d9b98c"))
    s.cyl("Lake", 0.6, 96, (-52, h + 0.3, zc(i) + 8), C("#1fc8e0"), R=angles(0, 0, 90), material="SmoothPlastic",
          reflectance=0.25)
    for j in range(6):
        s.box("LakeShine", (rng.uniform(6, 14), 0.2, 0.8), (-52 + rng.uniform(-30, 30), h + 0.65,
                                                             zc(i) + 8 + rng.uniform(-30, 30)), C("#bff7ff"))
    s.cyl("LakeShore", 0.4, 102, (-52, h + 0.2, zc(i) + 8), C("#f2e2c4"), R=angles(0, 0, 90))
    s.cyl("Lake2", 0.6, 46, (62, h + 0.3, zc(i) - 30), C("#1fc8e0"), R=angles(0, 0, 90), material="SmoothPlastic",
          reflectance=0.25)
    for _ in range(18):
        p = (rng.uniform(-110, 110), h + 0.2, rng.uniform(zc(i) - 70, zc(i) + 70))
        if math.dist((p[0], p[2]), (-52, zc(i) + 8)) < 52 or abs(p[0]) < 10:
            continue
        s.bevel("SnowPatch", (rng.uniform(8, 16), 0.5, rng.uniform(8, 16)), p, C("#ffffff"), b=0.2)
    for _ in range(40):
        x = rng.uniform(-WIDTH / 2 + 6, WIDTH / 2 - 6)
        z = rng.uniform(z0(i) - 8, z0(i + 1) + 10)
        if abs(x) < 12 or math.dist((x, z), (-52, zc(i) + 8)) < 54 or math.dist((x, z), (62, zc(i) - 30)) < 28:
            continue
        pine(s, (x, h, z), rng, rng.uniform(0.9, 1.5), snow=True)
    # Bamboo grove with the red panda.
    grove = (48, h, zc(i) + 30)
    for _ in range(26):
        p = add(grove, (rng.uniform(-10, 10), 0, rng.uniform(-10, 10)))
        hh = rng.uniform(8, 14)
        s.box("Bamboo", (0.8, hh, 0.8), add(p, (0, hh / 2, 0)), C("#7cc457"))
        s.box("BambooLeaves", (2.6, 0.4, 1.2), add(p, (0.8, hh - 1, 0)), C("#5fae3e"), rot=(0, rng.uniform(0, 90), 20))
    critter(s, "RedPanda", add(grove, (-14, 0, 6)), 240, 1.0)
    for j, (x, z, yaw) in enumerate(((-14, zc(i) - 30, 150), (-24, zc(i) - 40, 170), (-6, zc(i) - 48, 200))):
        critter(s, "MountainYak", (x, h, z), yaw, 1.0 if j == 0 else 0.9, label=j == 0)
    critter(s, "SnowshoeHare", (24, h, zc(i) - 10), 220, 1.0)
    # Gondola station.
    s.bevel("GondolaStation", (16, 10, 12), (96, h + 5, zc(i) + 40), C("#e0453a"), b=1)
    s.box("GondolaRoof", (18, 1.6, 14), (96, h + 10.8, zc(i) + 40), C("#ffffff"))


def frost(s, rng):
    i = 3
    h = H(i)
    s.box("Path", (14, 0.3, DEPTH), (0, h + 0.15, zc(i)), C("#cfe0f2"))
    for _ in range(10):
        c = (rng.uniform(-100, 100), h, rng.uniform(zc(i) - 65, zc(i) + 65))
        if abs(c[0]) < 14:
            continue
        for _ in range(rng.randint(3, 6)):
            s.shard("IceCrystal", add(c, (rng.uniform(-4, 4), 0, rng.uniform(-4, 4))), rng.uniform(1.4, 2.6),
                    rng.uniform(5, 12), C(rng.choice(["#7fe3ff", "#bff3ff", "#5ec8ff"])), material="Glass",
                    transparency=0.15, reflectance=0.25,
                    R=angles(rng.uniform(-20, 20), rng.uniform(0, 90), rng.uniform(-20, 20)))
    for _ in range(12):
        rock(s, (rng.uniform(-110, 110), h, rng.uniform(zc(i) - 70, zc(i) + 70)), (rng.uniform(6, 14),
             rng.uniform(4, 9), rng.uniform(6, 14)), rng, "#bcd0e8")
    for _ in range(28):
        x = rng.uniform(-WIDTH / 2 + 6, WIDTH / 2 - 6)
        if abs(x) < 14:
            continue
        tree(s, (x, h, rng.uniform(z0(i) - 8, z0(i + 1) + 10)), rng, leaf="#2a6f5a", k=rng.uniform(0.8, 1.3),
             kind="pine", snow=True)
    # Blizzard.
    for _ in range(260):
        s.box("Snowflake", (0.4, 0.4, 0.4), (rng.uniform(-110, 110), h + rng.uniform(1, 40),
                                              rng.uniform(z0(i) + 30, z0(i + 1))), C("#ffffff"), shadow=False,
              material="SmoothPlastic")
    critter(s, "SnowLeopard", (22, h, zc(i) + 24), 210, 1.0)
    for j, (x, z) in enumerate(((-24, zc(i) + 4), (-34, zc(i) + 12), (-30, zc(i) - 6))):
        critter(s, "FrostfangWolf", (x, h, z), 160, 1.0 if j == 0 else 0.85, label=j == 0)
    critter(s, "LittleYeti", (14, h, zc(i) - 24), 200, 1.1)
    critter(s, "GlacierMammoth", (-40, h, zc(i) - 40), 140, 1.3)


def summit(s, rng, night=True):
    i = 4
    h = H(i)
    # The peak rising behind the summit plateau.
    mountain(s, (0, h, z0(i + 1) - 30), 3.0, rng, rock_col="#8a96b0")
    # Rune shrine: a ring of standing stones with glowing runes.
    shrine = (0, h, zc(i) + 10)
    for j in range(8):
        a = j * math.pi / 4
        p = add(shrine, (math.cos(a) * 18, 0, math.sin(a) * 18))
        s.bevel("Standing", (3, 10, 2), add(p, (0, 5, 0)), C("#7d869c"), b=0.6, R=angles(0, -math.degrees(a) + 90, 0))
        s.box("Rune", (1.2, 3, 0.3), add(p, (0, 6, 0)), C("#5effb0" if j % 2 else "#b45cff"),
              R=angles(0, -math.degrees(a) + 90, 0), **GLOW)
    s.cyl("ShrineFloor", 0.3, 30, add(shrine, (0, 0.2, 0)), C("#5effb0"), R=angles(0, 0, 90), transparency=0.88,
          **GLOW)
    # Griffin nest on a rock pillar.
    nest = (64, h, zc(i) - 10)
    for j in range(3):
        s.bevel("NestPillar", (14 - j * 2, 8, 14 - j * 2), add(nest, (0, 4 + j * 8, 0)), C("#8a96b0"), b=1.5)
    for j in range(10):
        a = j * math.pi / 5
        s.box("NestTwig", (6, 1, 1), add(nest, (math.cos(a) * 5, 24.5, math.sin(a) * 5)), C("#8b5a2b"),
              rot=(0, -math.degrees(a) + 90, 0))
    for dx in (-1, 1.2):
        s.bevel("GoldenEgg", (1.6, 2.2, 1.6), add(nest, (dx, 25.5, 0)), C("#ffd23f"), b=0.6, reflectance=0.3)
    critter(s, "SkyGriffin", add(nest, (-14, 0, 10)), 240, 1.1)
    if not night:
        return
    # The northern lights: tall glowing curtains in the sky.
    for band, (col, y0, zoff) in enumerate((("#5effb0", 150, -60), ("#3fd6ff", 170, -90), ("#b45cff", 190, -120))):
        for j in range(26):
            x = -150 + j * 12
            y = h + y0 + 12 * math.sin(j * 0.6 + band)
            s.box("Aurora", (12.5, 46, 1), (x, y, z0(i + 1) + zoff + 18 * math.sin(j * 0.4 + band)), C(col),
                  transparency=0.55, shadow=False, material="Neon")
    critter(s, "AuroraDragon", (8, h + 30, zc(i) - 20), 100, 1.7)
    for _ in range(80):
        s.box("Star", (0.8, 0.8, 0.8), (rng.uniform(-300, 300), h + rng.uniform(120, 260), z0(i + 1) - rng.uniform(150, 260)),
              C("#ffffff"), shadow=False, material="Neon")


def frame_mountains(s, rng):
    """Big mountains on both sides and at the back, so the area sits inside a mountain range."""
    for side in (-1, 1):
        for j in range(11):
            z = 20 - j * 74
            k = 1.6 + j * 0.16 + rng.uniform(-0.2, 0.2)
            mountain(s, (side * (WIDTH / 2 + 34 + rng.uniform(0, 30)), H(min(4, j // 2)) - 2, z), k, rng)
    for x in (-260, -130, 130, 260):
        mountain(s, (x, 60, z0(5) - 90), 3.6, rng, rock_col="#8a96b0")
    for j in range(10):
        cloud(s, (rng.uniform(-260, 260), rng.uniform(150, 230), rng.uniform(-750, 50)), rng.uniform(1.4, 2.4), rng)


# ---------------------------------------------------------------------- HUD ---

def zone_pill(name, speed):
    return pill("left:50%", "top:20px", f'{name} <span style="font-size:22px;color:#ffd84a">{speed} SPEED</span>', 30,
                extra="transform:translateX(-50%)")


def overview_hud():
    return ('<div class="game" style="position:absolute;left:40px;top:32px;font-size:58px;color:#ffffff">'
            'MOUNTAIN RANGE</div>'
            '<div class="game" style="position:absolute;left:42px;top:104px;font-size:26px;color:#ffd84a">'
            '5 ZONES &middot; 16 ANIMALS &middot; ABOUT 4X THE DARK WOODS</div>')


def lasso_hud():
    return (top_bar(coins="$1.2M", income="+$48K/s", speed="31,200") + zone_pill("CANYON PASS", "25K")
            + '<div class="btn game" style="right:60px;bottom:60px;width:150px;height:150px;background:#ffb52e;'
              'display:flex;align-items:center;justify-content:center;text-align:center;font-size:26px">THROW<br>LASSO</div>'
            + hotbar("LASSO"))


def secret_hud():
    return (top_bar(coins="$48.6M", income="+$2.1M/s", speed="268,000") + zone_pill("THE SUMMIT", "250K")
            + '<div class="game" style="position:absolute;left:50%;top:110px;transform:translateX(-50%);font-size:52px;'
              'color:#7dffcf;text-shadow:0 0 18px #5effb0">A SECRET ANIMAL APPEARED!</div>'
            + '<div class="game" style="position:absolute;left:50%;top:176px;transform:translateX(-50%);font-size:28px">'
              'THE AURORA DRAGON IS CIRCLING THE SUMMIT</div>' + hotbar("LASSO"))


# --------------------------------------------------------------------- build ---

def build(night=False):
    rng = random.Random(77)
    s = Scene("mountains", env={
        "sky": [[0, "#3f9fff"], [0.55, "#96d0ff"], [1, "#e8f6ff"]], "fog": ["#e8f6ff", 500, 1500],
        "sun": {"dir": [-0.5, 1.0, 0.45], "intensity": 2.5}, "hemi": ["#ffffff", "#8fb0c0", 1.45],
        "bloom": [0.5, 0.5, 0.9],
    })
    for i in range(5):
        zone_block(s, i)
        if i > 0:
            gate(s, i, rng)
    foothills(s, rng)
    canyon(s, rng)
    lakes(s, rng)
    frost(s, rng)
    summit(s, rng, night)
    frame_mountains(s, rng)
    # Gondola cable from the foothills to the summit, with cabins.
    a, b = (WIDTH / 2 - 24, 34, -20), (WIDTH / 2 - 24, H(4) + 40, z0(4) - 40)
    s.beam("GondolaCable", a, b, 0.4, C("#3a3a44"))
    for t in (0.2, 0.45, 0.7):
        p = tuple(x + (y - x) * t for x, y in zip(a, b))
        s.box("GondolaHanger", (0.4, 3, 0.4), add(p, (0, -1.5, 0)), C("#3a3a44"))
        s.bevel("GondolaCabin", (4, 3.6, 5), add(p, (0, -4.6, 0)), C("#e0453a"), b=0.6)
        s.box("GondolaWindow", (4.1, 1.4, 3.6), add(p, (0, -4.0, 0)), C("#bff3ff"))

    # Canyon: a player throws a lasso at the Bighorn Ram.
    h1 = H(1)
    ram = (10, h1, zc(1) + 10)
    thrower = (-2, h1 + 0.3, zc(1) + 36)
    hands = player(s, thrower, toward(thrower, ram), "#ff5a5a", "#2b3a6b", hair="#3a2412", pose="throw")
    neck = model_point(ram, 160, 1, (0, 6.6, -3.4))
    edge = lasso_loop(s, add(neck, (0, 1.2, 0)), 2.8, tilt=(12, 0, -10))
    rope(s, bezier(hands["R"], add(tuple((p + q) / 2 for p, q in zip(hands["R"], edge)), (0, 10, 0)), edge, 14))

    # Entrance: a player walks up to the gate.
    player(s, (4, 0.3, 26), 0, "#45a6ff", "#2b3a6b", hair="#e8c07a", pose="run")
    # Frost Ridge and the summit: players.
    player(s, (4, H(3) + 0.3, zc(3) + 46), 180, "#52d273", "#2b3a6b", hair="#111")
    summit_player = (14, H(4) + 0.3, zc(4) + 30)
    player(s, summit_player, 180, "#ffd23f", "#4a3a2a", hair="#3a2412")

    s.shot("overview", (300, 300, 230), (0, 40, -360), fov=50, shadow={"center": [0, 40, -360], "radius": 440},
           env={"fog": ["#e8f6ff", 800, 2200]}, hud=overview_hud(), hide_sprites=True)
    s.shot("entrance", (14, 16, 70), (0, 14, -40), fov=60, shadow={"center": [0, 0, -30], "radius": 110},
           hud=top_bar(coins="$420K", income="+$12K/s", speed="18,400") + zone_pill("PINE FOOTHILLS", "0")
           + hotbar("LASSO"))
    s.shot("canyon", (-12, h1 + 10, zc(1) + 52), (8, h1 + 9, zc(1) - 10), fov=60,
           shadow={"center": list(ram), "radius": 110}, hud=lasso_hud())
    s.shot("lakes", (40, H(2) + 26, zc(2) + 72), (-30, H(2) + 4, zc(2) - 20), fov=58,
           shadow={"center": [-20, H(2), zc(2)], "radius": 120},
           hud=top_bar(coins="$6.8M", income="+$310K/s", speed="64,000") + zone_pill("ALPINE LAKES", "60K")
           + hotbar("LASSO"))
    s.shot("frost", (8, H(3) + 14, zc(3) + 66), (-8, H(3) + 6, zc(3) - 20), fov=60,
           shadow={"center": [0, H(3), zc(3)], "radius": 110},
           env={"sky": [[0, "#8fa8cf"], [0.6, "#c9d8ef"], [1, "#eef4ff"]], "fog": ["#e6eef9", 60, 260],
                "sun": {"dir": [-0.3, 1.0, 0.3], "intensity": 1.6}},
           hud=top_bar(coins="$22M", income="+$950K/s", speed="131,000") + zone_pill("FROST RIDGE", "120K")
           + '<div class="game" style="position:absolute;left:28px;top:110px;font-size:26px;color:#bff3ff">'
             '&#10052; BLIZZARD! -20% SPEED</div>' + hotbar("LASSO"))
    s.shot("summit", (56, H(4) + 30, zc(4) + 62), (2, H(4) + 18, zc(4) - 28), fov=66,
           shadow={"center": [0, H(4), zc(4)], "radius": 120},
           env={"sky": [[0, "#07061a"], [0.5, "#15123a"], [1, "#2a2a5a"]], "fog": ["#1a1a3a", 200, 700],
                "sun": {"dir": [0.3, 1.0, 0.2], "intensity": 0.7}, "hemi": ["#9fb0ff", "#2a2a4a", 0.9],
                "bloom": [1.0, 0.6, 0.6]},
           hud=secret_hud())
    return s


def main():
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    viewer = HERE.parent / "viewer"
    for night in (False, True):   # the northern lights only show in the night picture of the summit
        world = build(night)
        path = out / f"mountains_{'night' if night else 'day'}.json"
        path.write_text(json.dumps(world.export()))
        shutil.copy(path, viewer / path.name)
        print(f"{path.name}: {len(world.parts)} parts")
    dest = ROOT / "concept-art" / "mountain-range"
    dest.mkdir(parents=True, exist_ok=True)
    names = {"overview": "1-overzicht", "entrance": "2-ingang-pine-foothills", "canyon": "3-canyon-pass-lasso",
             "lakes": "4-alpine-lakes", "frost": "5-frost-ridge", "summit": "6-the-summit-secret"}
    only = os.environ.get("SHOTS", ",".join(names)).split(",")
    for shot in only:
        world = "mountains_night.json" if shot == "summit" else "mountains_day.json"
        subprocess.run(["node", "sceneshot.js", world, shot, str(dest / f"{names[shot]}.png")],
                       cwd=viewer, check=True, env={**os.environ, "NODE_PATH": "/opt/node22/lib/node_modules"})


if __name__ == "__main__":
    main()
