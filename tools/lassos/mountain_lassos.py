#!/usr/bin/env python3
"""Three lasso Tools for the Mountain Range area, in the same build as build_lassos.py (same grip, coil, spinning
loop, LassoFX and LassoBurst scripts):

  * Frostbite Lasso (Epic): an ice-blue rope with icicles and frost crystals and a glowing snowflake.
  * Skyfeather Lasso (Legendary): a white and gold rope with golden griffin feathers and a winged sky gem.
  * Aurora Lasso (Mythic): a night-blue rope with glowing strands in aurora colours, star crystals and ribbons
    of northern lights waving over the loop.

    python3 tools/lassos/mountain_lassos.py                   -> build/mountain_lassos.json, build/mountain_world.json
    python3 tools/lassos/mountain_lassos.py --rbxm OUT.rbxm   -> also writes the .rbxm (needs cargo)
"""

import json
import math
import random
import subprocess
import sys
from pathlib import Path

from build_lassos import (FIRE, GRIP_TOP, HERE, LOOP_CENTER, LOOP_NORMAL, LOOP_R, SMOKE, SPARK, C, Lasso,
                          coil, colors, crystal, emitter, grip, loop_light_and_burst, loop_rope, preview,
                          preview_motes, preview_trail, ring_emitters, seq, tool_node)
from lib import IDENTITY, add, aim, angles, apply, matmul, scale, sub, unit

GLOW = "rbxasset://textures/particles/forcefield_glow_main.dds"


def outward(L, ang):
    return apply(L.R, (math.cos(ang), 0, math.sin(ang)))


def flake(g, center, a_dir, b_dir, flat_axis, radius, color, name="Snowflake", material="Neon"):
    """A six-armed snowflake in the plane of a_dir and b_dir, with two twigs on every arm."""
    for k in range(6):
        ang = k * math.pi / 3
        d = unit(add(scale(a_dir, math.cos(ang)), scale(b_dir, math.sin(ang))))
        g.box(name, (radius, 0.05, 0.08), add(center, scale(d, radius / 2)), C(color),
              R=aim(d, roll_up=flat_axis), material=material, shadow=False)
        for sgn in (-1, 1):
            t = unit(add(scale(a_dir, math.cos(ang + sgn * 1.0)), scale(b_dir, math.sin(ang + sgn * 1.0))))
            base = add(center, scale(d, radius * 0.62))
            g.box(name + "Twig", (radius * 0.32, 0.05, 0.07), add(base, scale(t, radius * 0.14)), C(color),
                  R=aim(t, roll_up=flat_axis), material=material, shadow=False)
    g.part("ball", name + "Core", (radius * 0.4,) * 3, center, C("#ffffff"), material="Neon", shadow=False)


# -------------------------------------------------------------- Frostbite ---

def frostbite():
    t = dict(name="FrostbiteLasso", display="Frostbite Lasso", rarity="Epic",
             rope=("#bfe9ff", "#7fc8ec"), strand="#e6fbff", leather="#24364f", leather2="#1a2738",
             metal="#cfe3f2", metal2="#ffffff", refl=0.25, binding="#5fb8e8", tuft="#ffffff",
             trail=("#ffffff", "#5fd0ff"), light=("#8fe0ff", 1.7, 10),
             description="Frozen on Frost Ridge. Icicles hang from the rope and snow falls wherever it spins.")
    t["burst"] = [
        emitter("BurstSnow", SPARK, colors((0, "#ffffff"), (0.5, "#dff6ff"), (1, "#7fd0ff")),
                seq((0, 0.7), (1, 0)), 0, (1.0, 1.6), (6, 12), spread=(180, 180), drag=3, accel=(0, -3, 0),
                enabled=False, rotspeed=(-200, 200)),
        emitter("BurstFrost", SMOKE, colors((0, "#ffffff"), (1, "#bfe9ff")), seq((0, 1.0), (1, 2.6)), 0, (0.6, 0.9),
                (4, 7), spread=(180, 180), drag=4, light=0, enabled=False,
                transparency=seq((0, 0.4), (1, 1))),
        emitter("BurstFlash", SPARK, colors((0, "#ffffff"), (1, "#8fe0ff")), seq((0, 3.5), (1, 0)), 0, (0.25, 0.35),
                (0, 0), enabled=False, z=1),
    ]
    L = Lasso(t)
    grip(L)
    coil(L)
    a = loop_rope(L)
    g = L.loop
    # Icicles hanging under the rope, long and short.
    rng = random.Random(4)
    for k in range(10):
        ang = a + 0.4 + k * (2 * math.pi - 0.8) / 9
        base = L.on_loop(ang, LOOP_R + rng.uniform(-0.05, 0.05), -0.08)
        ln = 0.28 + 0.22 * ((k * 5) % 3) / 2
        crystal(g, base, scale(LOOP_NORMAL, -1), ln, 0.12, "#d8f4ff", "#ffffff")
    # Frost crystals growing up out of the rope.
    for k in range(1, 5):
        ang = a + k * 2 * math.pi / 5
        base = L.on_loop(ang, LOOP_R + 0.05)
        crystal(g, base, unit(add(outward(L, ang), scale(LOOP_NORMAL, 1.2))), 0.5, 0.18, "#a8e4ff", "#e6fbff")
    # The honda: a glowing snowflake.
    out = outward(L, a)
    flake(g, add(L.on_loop(a), scale(out, 0.48)), out, LOOP_NORMAL, L.tangent(a), 0.5, "#dff6ff")
    # Particles: snow falling from the loop, a cold mist and twinkling frost.
    for k, ang in enumerate((a + 1.5, a + 3.1, a + 4.7)):
        L.hub_attachment(f"Snow{k}", L.on_loop(ang), [
            emitter("Snow", SPARK, colors((0, "#ffffff"), (1, "#cfefff")), seq((0, 0.22), (1, 0.1)), 5, (1.4, 2.2),
                    (0.2, 0.6), spread=(180, 180), accel=(0, -1.8, 0), drag=0.6, rotspeed=(-90, 90))])
    ring_emitters(L, "FrostMist", 2, a + 2.3, lambda: emitter(
        "FrostMist", SMOKE, colors((0, "#ffffff"), (1, "#bfe9ff")), seq((0, 0.5), (1, 1.4)), 1.5, (1.0, 1.6),
        (0.1, 0.4), accel=(0, -0.8, 0), light=0, rotspeed=(-30, 30), transparency=seq((0, 1), (0.3, 0.7), (1, 1))))
    ring_emitters(L, "Glints", 4, a + 0.6, lambda: emitter(
        "Glints", SPARK, colors((0, "#ffffff"), (1, "#bfefff")), seq((0, 0), (0.5, 0.4), (1, 0)), 1.5,
        (0.3, 0.5), (0, 0), locked=True))
    loop_light_and_burst(L)
    # Snowflake charm and an ice crystal pommel.
    b = L.base
    b.rod("CharmChain", (0, -0.6, -0.24), (0, -0.84, -0.42), 0.05, C("#ffffff"), collide=False, shadow=False)
    flake(b, (0, -1.02, -0.44), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.2, "#bfefff", name="FlakeCharm")
    crystal(b, (0, 0.62, 0), (0, 1, 0), 0.3, 0.16, "#a8e4ff", "#ffffff")
    crystal(b, (0.12, 0.6, 0), unit((0.7, 1, 0)), 0.18, 0.1, "#d8f4ff", "#ffffff")
    crystal(b, (-0.12, 0.6, 0), unit((-0.7, 1, 0)), 0.18, 0.1, "#d8f4ff", "#ffffff")
    rng = random.Random(5)
    preview_motes(L, rng, "#ffffff", n=26, rise=-1.0, size=0.12)
    preview_trail(L, "#bfefff")
    return L


# ------------------------------------------------------------- Skyfeather ---

def feather(g, base, d, side, length, width, color, tip, name="Feather"):
    """A flat feather from base along d: a vane, a lighter tip and a gold quill (side = the flat axis)."""
    R = aim(d, roll_up=side)
    g.box(name, (length * 0.72, 0.05, width), add(base, scale(d, length * 0.36)), C(color), R=R, shadow=False)
    g.box(name + "Tip", (length * 0.3, 0.05, width * 0.75), add(base, scale(d, length * 0.85)), C(tip), R=R,
          shadow=False)
    g.box(name + "Quill", (length * 0.95, 0.07, 0.05), add(base, scale(d, length * 0.47)), C("#e8b84a"), R=R,
          shadow=False)


def skyfeather():
    t = dict(name="SkyfeatherLasso", display="Skyfeather Lasso", rarity="Legendary",
             rope=("#fff6e0", "#e8b84a"), strand="#ffe08a", leather="#8a5a2e", leather2="#6b4220",
             metal="#f2c14e", metal2="#fff0a8", refl=0.25, binding="#3fa9f5", tuft="#ffffff",
             trail=("#ffffff", "#7fd0ff"), light=("#ffe8a8", 1.6, 10),
             description="Braided with golden griffin feathers from the summit. The wind follows it.")
    t["burst"] = [
        emitter("BurstFeathers", SPARK, colors((0, "#ffffff"), (0.5, "#fff3c4"), (1, "#ffd36b")),
                seq((0, 0.8), (1, 0.3)), 0, (1.2, 1.8), (6, 11), spread=(180, 180), drag=3, accel=(0, -2, 0),
                enabled=False, rotspeed=(-150, 150), squash=seq((0, 1.8), (1, 1.8))),
        emitter("BurstWind", SPARK, colors((0, "#ffffff"), (1, "#7fd0ff")), seq((0, 0.35), (1, 0.1)), 0, (0.4, 0.6),
                (12, 18), spread=(0, 180), drag=4, enabled=False, Orientation="VelocityParallel",
                squash=seq((0, 2.5), (1, 2.5))),
        emitter("BurstFlash", SPARK, colors((0, "#fffbe0"), (1, "#ffe08a")), seq((0, 3.5), (1, 0)), 0, (0.25, 0.35),
                (0, 0), enabled=False, z=1),
    ]
    L = Lasso(t)
    grip(L)
    coil(L)
    a = loop_rope(L)
    g = L.loop
    # Golden feathers tucked into the rope in fans of three, sweeping back against the spin.
    for k in range(1, 6):
        ang = a + k * 2 * math.pi / 6
        p = L.on_loop(ang, LOOP_R + 0.08, 0.05)
        out, back = outward(L, ang), scale(L.tangent(ang), -1)
        for j, (lift, ln) in enumerate(((0.25, 1.05), (0.8, 0.85), (-0.25, 0.75))):
            d = unit(add(add(scale(out, 0.75), scale(back, 0.55)), scale(LOOP_NORMAL, lift)))
            feather(g, add(p, scale(back, 0.1 * j)), d, L.tangent(ang), ln, 0.3,
                    ("#ffffff", "#fff3d6", "#ffffff")[j], ("#f2c14e", "#e8a63a", "#f2c14e")[j])
        g.box("FeatherBand", (0.14, 0.32, 0.32), L.on_loop(ang), C("#f2c14e"), R=aim(L.tangent(ang), roll_up=LOOP_NORMAL),
              reflectance=0.3, shadow=False)
    # The honda: a sky-blue gem with two golden wings.
    out = outward(L, a)
    gem = add(L.on_loop(a), scale(out, 0.42))
    for turn in (0, 45):
        g.box("SkyGem", (0.26, 0.26, 0.12), gem, C("#7fd0ff"),
              R=matmul(aim(out, roll_up=LOOP_NORMAL), matmul(angles(0, 90, 0), angles(0, 0, turn))), material="Neon",
              shadow=False)
    g.cyl("GemSetting", 0.1, 0.38, gem, C("#f2c14e"), R=aim(L.tangent(a), roll_up=LOOP_NORMAL), reflectance=0.3,
          shadow=False)
    for sgn in (-1, 1):
        for j in range(3):
            d = unit(add(scale(out, 0.35 + 0.25 * j), scale(LOOP_NORMAL, sgn * (1.0 - 0.2 * j))))
            g.box("GemWing", (0.42 - 0.08 * j, 0.05, 0.14), add(gem, scale(d, 0.3 - 0.03 * j)), C("#ffe08a"),
                  R=aim(d, roll_up=L.tangent(a)), reflectance=0.3, shadow=False)
    # Particles: feathers drifting off the loop, wind streaks and gold glints.
    for k, ang in enumerate((a + 1.6, a + 3.6)):
        L.hub_attachment(f"Feathers{k}", L.on_loop(ang), [
            emitter("Feathers", SPARK, colors((0, "#ffffff"), (1, "#ffe8a8")), seq((0, 0.3), (1, 0.2)), 3, (1.5, 2.4),
                    (0.3, 0.8), spread=(180, 180), accel=(0, -1.2, 0), drag=1, rotspeed=(-120, 120),
                    squash=seq((0, 1.8), (1, 1.8)), light=0.4)])
    ring_emitters(L, "Wind", 3, a + 0.9, lambda: emitter(
        "Wind", SPARK, colors((0, "#ffffff"), (1, "#bfe6ff")), seq((0, 0.12), (1, 0.04)), 4, (0.3, 0.5),
        (2, 3), spread=(10, 10), Orientation="VelocityParallel", squash=seq((0, 3), (1, 3)),
        transparency=seq((0, 0.4), (1, 1))))
    ring_emitters(L, "Glints", 4, a + 0.4, lambda: emitter(
        "Glints", SPARK, colors((0, "#ffffff"), (1, "#ffe08a")), seq((0, 0), (0.5, 0.45), (1, 0)), 1.5,
        (0.3, 0.5), (0, 0), locked=True))
    loop_light_and_burst(L)
    # A feather charm and a winged pommel.
    b = L.base
    b.rod("CharmChain", (0, -0.6, -0.24), (0, -0.84, -0.42), 0.05, C("#fff0a8"), collide=False, shadow=False)
    feather(b, (0, -0.84, -0.44), (0, -1, 0), (0, 0, 1), 0.5, 0.16, "#ffffff", "#f2c14e", name="FeatherCharm")
    for sx in (-1, 1):
        for j in range(3):
            d = unit((sx * (1.0 - 0.25 * j), 0.5 + 0.35 * j, 0))
            b.box("PommelWing", (0.32 - 0.06 * j, 0.05, 0.12), add((0, 0.68, 0), scale(d, 0.2)), C("#ffe08a"),
                  R=aim(d, roll_up=(0, 0, 1)), reflectance=0.3, shadow=False)
    b.part("ball", "PommelGem", (0.18, 0.18, 0.18), (0, 0.7, 0), C("#7fd0ff"), material="Neon", shadow=False)
    rng = random.Random(6)
    preview_motes(L, rng, "#fff3c4", n=16, rise=-0.8, size=0.16)
    preview_trail(L, "#e6f6ff")
    return L


# ----------------------------------------------------------------- Aurora ---

AURORA = ("#5effb0", "#3fd6ff", "#b45cff")


def aurora():
    t = dict(name="AuroraLasso", display="Aurora Lasso", rarity="Mythic",
             rope=("#1c2a5a", "#2d1f5e"), strand=None, leather="#1a1f3a", leather2="#11152a",
             metal="#cfd8ff", metal2="#ffffff", refl=0.25, binding="#3fd6ff", tuft="#5effb0",
             trail=("#5effb0", "#b45cff"), light=("#6fe8ff", 1.8, 11),
             description="Spun from the northern lights over the summit. Ribbons of aurora dance over the loop.")
    t["burst"] = [
        emitter("BurstStars", SPARK, colors((0, "#ffffff"), (0.35, "#5effb0"), (0.7, "#3fd6ff"), (1, "#b45cff")),
                seq((0, 0.9), (1, 0)), 0, (1.0, 1.6), (7, 13), spread=(180, 180), drag=3, enabled=False,
                rotspeed=(-250, 250)),
        emitter("BurstAurora", GLOW, colors((0, "#5effb0"), (0.5, "#3fd6ff"), (1, "#b45cff")), seq((0, 1.5), (1, 5)),
                0, (0.6, 0.8), (0, 0), enabled=False, transparency=seq((0, 0.3), (1, 1)), rotspeed=(-60, 60)),
        emitter("BurstFlash", SPARK, colors((0, "#ffffff"), (1, "#6fe8ff")), seq((0, 3.5), (1, 0)), 0, (0.25, 0.35),
                (0, 0), enabled=False, z=1),
    ]
    L = Lasso(t)
    grip(L)
    coil(L)
    a = loop_rope(L)
    g = L.loop
    # Glowing strands in aurora colours wound round the dark rope.
    for i, up in enumerate((0.11, -0.11)):
        g.ring("AuroraStrand", add(LOOP_CENTER, apply(L.R, (0, up, 0))), L.R, LOOP_R, 0.07,
               [C(c) for c in (AURORA if i == 0 else AURORA[::-1])], n=18, twist=False, material="Neon",
               collide=False, shadow=False)
    # Star crystals rising from the rope, each a different aurora colour, with star beads between them.
    for k in range(1, 6):
        ang = a + k * 2 * math.pi / 6
        base = L.on_loop(ang, LOOP_R + 0.05)
        col = AURORA[k % 3]
        crystal(g, base, unit(add(scale(outward(L, ang), 0.5), LOOP_NORMAL)), 0.5, 0.17, col, "#ffffff")
        star = L.on_loop(ang + math.pi / 6, LOOP_R + 0.02, 0.05)
        for turn in (0, 45):
            g.box("StarBead", (0.24, 0.24, 0.07), star, C("#ffffff"),
                  R=matmul(aim(outward(L, ang + math.pi / 6), roll_up=LOOP_NORMAL),
                           matmul(angles(0, 90, 0), angles(0, 0, turn))), material="Neon", shadow=False)
    # The honda: a four-pointed star of light round an aurora gem.
    out = outward(L, a)
    center = add(L.on_loop(a), scale(out, 0.46))
    for k in range(4):
        ang = k * math.pi / 2
        d = unit(add(scale(out, math.cos(ang)), scale(LOOP_NORMAL, math.sin(ang))))
        g.wedge("StarPoint", (0.08, 0.42, 0.14), add(center, add(scale(d, 0.25), scale(L.tangent(a), 0.0))),
                C("#e8fbff"), R=matmul(aim(L.tangent(a), roll_up=d), angles(0, 0, 0)), material="Neon", shadow=False)
    g.part("ball", "AuroraGem", (0.26, 0.26, 0.26), center, C("#5effb0"), material="Neon", shadow=False)
    g.part("ball", "AuroraGemShell", (0.34, 0.34, 0.34), center, C("#3fd6ff"), material="Glass", transparency=0.5,
           shadow=False)
    # Ribbons of aurora: three curved beams arching over the loop, between points on the rope.
    for k in range(3):
        a0 = a + 0.8 + k * 2 * math.pi / 3
        a1 = a0 + 1.6
        p0 = L.on_loop(a0, LOOP_R, 0.25)
        p1 = L.on_loop(a1, LOOP_R, 0.25)
        n0, n1 = f"AuroraA{k}", f"AuroraB{k}"
        beam_node = {"class": "Beam", "name": "AuroraRibbon", "props": {
            "Attachment0": {"ref": f"{t['name']}.{n0}"}, "Attachment1": {"ref": f"{t['name']}.{n1}"},
            "Width0": 0.9, "Width1": 0.9, "CurveSize0": 1.4, "CurveSize1": -1.4, "Segments": 16,
            "FaceCamera": True, "LightEmission": 1, "LightInfluence": 0, "ZOffset": 0.2,
            "Color": colors((0, AURORA[k]), (0.5, AURORA[(k + 1) % 3]), (1, AURORA[(k + 2) % 3])),
            "Transparency": seq((0, 1), (0.2, 0.45), (0.5, 0.3), (0.8, 0.45), (1, 1)),
            "Texture": GLOW, "TextureSpeed": 0.6, "TextureMode": "Stretch", "TextureLength": 1}}
        up = LOOP_NORMAL
        L.hub_attachment(n0, p0, [beam_node], R=aim(up, roll_up=outward(L, a0)))
        L.hub_attachment(n1, p1, [], R=aim(up, roll_up=outward(L, a1)))
    # Particles: falling stars, soft aurora glow and twinkles.
    for k, ang in enumerate((a + 1.4, a + 3.3, a + 5.0)):
        L.hub_attachment(f"Stars{k}", L.on_loop(ang), [
            emitter("Stars", SPARK, colors((0, "#ffffff"), (0.5, AURORA[k]), (1, AURORA[(k + 1) % 3])),
                    seq((0, 0.28), (1, 0)), 4, (1.0, 1.8), (0.2, 0.7), spread=(180, 180), accel=(0, -1.5, 0),
                    rotspeed=(-150, 150))])
    ring_emitters(L, "AuroraGlow", 3, a + 2.2, lambda: emitter(
        "AuroraGlow", GLOW, colors((0, "#5effb0"), (0.5, "#3fd6ff"), (1, "#b45cff")), seq((0, 0.6), (1, 1.2)), 1.2,
        (1.0, 1.4), (0, 0.2), accel=(0, 0.6, 0), transparency=seq((0, 1), (0.4, 0.75), (1, 1))))
    ring_emitters(L, "Glints", 4, a + 0.5, lambda: emitter(
        "Glints", SPARK, colors((0, "#ffffff"), (1, "#bff6ff")), seq((0, 0), (0.5, 0.45), (1, 0)), 1.5,
        (0.3, 0.5), (0, 0), locked=True))
    loop_light_and_burst(L)
    # A star charm and a glowing aurora pommel.
    b = L.base
    b.rod("CharmChain", (0, -0.6, -0.24), (0, -0.84, -0.42), 0.05, C("#cfd8ff"), collide=False, shadow=False)
    for k in range(4):
        b.wedge("StarCharm", (0.06, 0.2, 0.1), (0.1 * math.cos(k * math.pi / 2) * 1.0, -1.02 + 0.1 * math.sin(k * math.pi / 2),
                                                 -0.44), C("#e8fbff"), rot=(0, 0, k * 90 - 90), material="Neon",
                shadow=False)
    b.part("ball", "StarCharmCore", (0.12, 0.12, 0.12), (0, -1.02, -0.44), C("#5effb0"), material="Neon",
           shadow=False)
    crystal(b, (0, 0.62, 0), (0, 1, 0), 0.26, 0.14, "#3fd6ff", "#ffffff")
    crystal(b, (0.12, 0.6, 0), unit((0.7, 1, 0)), 0.16, 0.1, "#5effb0", "#ffffff")
    crystal(b, (-0.12, 0.6, 0), unit((-0.7, 1, 0)), 0.16, 0.1, "#b45cff", "#ffffff")
    # Preview stand-ins for the ribbons: thin glowing arcs over the loop.
    for k in range(3):
        a0 = a + 0.8 + k * 2 * math.pi / 3
        for i in range(8):
            u, v = a0 + 1.6 * i / 8, a0 + 1.6 * (i + 1) / 8
            h0, h1 = 0.25 + 0.9 * math.sin(math.pi * i / 8), 0.25 + 0.9 * math.sin(math.pi * (i + 1) / 8)
            pa, pb = L.on_loop(u, LOOP_R, h0), L.on_loop(v, LOOP_R, h1)
            L.preview_fx.append(("block", "RibbonFx", (math.dist(pa, pb) * 1.05, 0.22, 0.03), scale(add(pa, pb), 0.5),
                                 C(AURORA[(k + i // 3) % 3]), "Neon", aim(sub(pb, pa), roll_up=LOOP_NORMAL)))
    rng = random.Random(7)
    preview_motes(L, rng, "#ffffff", n=14, rise=-0.8, size=0.1)
    preview_motes(L, rng, "#5effb0", n=10, rise=0.6, size=0.12)
    preview_trail(L, "#6fe8ff")
    return L


LASSOS = [frostbite, skyfeather, aurora]


def main():
    fx_source = (HERE / "LassoFX.lua").read_text()
    burst_source = (HERE / "LassoBurst.lua").read_text()
    lassos = [make() for make in LASSOS]
    tools = [tool_node(L, fx_source, burst_source) for L in lassos]
    for tool in tools:
        tool["tags"] = ["Lasso", "MountainLasso"]
    tree = [{"class": "Folder", "name": "MountainLassos", "children": tools}]
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "mountain_lassos.json").write_text(json.dumps(tree))
    world = preview(lassos)
    world["env"] = {"sky": [[0, "#3f8fef"], [0.55, "#86c2ff"], [1, "#d8efff"]], "fog": ["#d8efff", 120, 300],
                    "sun": {"dir": [-0.4, 1.0, -0.7], "intensity": 2.0}, "hemi": ["#ffffff", "#8fa3c4", 1.2],
                    "bloom": [0.5, 0.5, 0.8]}
    world["parts"][0].update(c=list(C("#b9c6d6")), m="Snow")
    (out / "mountain_world.json").write_text(json.dumps(world))
    for L in lassos:
        n = len(L.base.parts) + len(L.loop.parts) + 1
        emitters = json.dumps(L.hub_fx + L.handle_fx + L.t["burst"]).count("ParticleEmitter")
        print(f"{L.t['display']:17} {n:4} parts, {emitters} particle emitters")
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cargo", "run", "--quiet", "--release", "--manifest-path",
                        str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "mountain_lassos.json"),
                        target], check=True)


if __name__ == "__main__":
    main()
