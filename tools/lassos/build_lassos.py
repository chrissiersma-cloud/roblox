#!/usr/bin/env python3
"""Three lasso Tools with effects, built from Parts: Sunburst (gold), Moonshard (Dark Woods crystal) and
Wildfire (fire).

Each lasso is a Tool. The Handle is a wrapped grip; a coil of rope hangs below the hand and an open loop
twirls above the head, joined to the hand by a rope (a Beam). The loop has particles, a glowing trail and a
light. The LassoFX script (RunContext Client) spins the loop for every player. LassoBurst (a server Script)
spins it fast with a burst of effects when you click, so that every player sees it.

    python3 tools/lassos/build_lassos.py                       -> build/lassos.json and build/world.json (preview)
    python3 tools/lassos/build_lassos.py --rbxm OUT.rbxm       -> also writes the .rbxm (needs cargo)
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

from lib import IDENTITY, add, aim, angles, apply, cframe, compose, hex_color, inverse, matmul, scale, sub, unit  # noqa: E402
from build_statue import Group, up_to  # noqa: E402

SPARK = "rbxasset://textures/particles/sparkles_main.dds"
FIRE = "rbxasset://textures/particles/fire_main.dds"
SMOKE = "rbxasset://textures/particles/smoke_main.dds"

# Tool space: the hand holds the Handle at the origin. With the default Tool.Grip the Handle lines up with the
# character while the arm is held out: +Y is up, -Z is forward, +X is to the right.
GRIP_TOP = (0, 0.6, 0)
LOOP_CENTER = (-0.3, 3.05, -0.1)
LOOP_NORMAL = unit((0.05, 1, 0.16))
LOOP_R = 1.75
COIL_CENTER = (0, -1.12, 0)
CHARM = (0, -0.98, -0.42)


def C(h):
    return hex_color(h)


def seq(*stops):
    return [list(s) for s in stops]


def colors(*stops):
    """ColorSequence from (time, '#hex') pairs."""
    return [[t, *C(h)] for t, h in stops]


def emitter(name, texture, color, size, rate, lifetime, speed, **extra):
    props = {"Texture": texture, "Color": color, "Size": size, "Rate": rate, "Lifetime": list(lifetime),
             "Speed": list(speed), "LightInfluence": 0, "LightEmission": 1,
             "Transparency": extra.pop("transparency", seq((0, 0), (0.7, 0.2), (1, 1)))}
    renames = {"spread": "SpreadAngle", "accel": "Acceleration", "drag": "Drag", "rot": "Rotation",
               "rotspeed": "RotSpeed", "locked": "LockedToPart", "z": "ZOffset", "light": "LightEmission",
               "enabled": "Enabled", "direction": "EmissionDirection", "squash": "Squash"}
    for k, v in extra.items():
        props[renames.get(k, k)] = list(v) if isinstance(v, tuple) else v
    return {"class": "ParticleEmitter", "name": name, "props": props}


class Lasso:
    """The parts of one lasso: `base` parts are welded to the Handle, `loop` parts to the spinning LoopHub."""

    def __init__(self, theme):
        self.t = theme
        self.base = Group("Base")
        self.loop = Group("Loop")
        self.R = up_to(LOOP_NORMAL)
        self.hub_fx = []          # attachments on the LoopHub (they spin with the loop)
        self.handle_fx = []       # attachments on the Handle
        self.preview_fx = []      # stand-ins for particles in the preview renders

    # Points on the loop.
    def on_loop(self, a, r=LOOP_R, up=0.0):
        return add(LOOP_CENTER, apply(self.R, (r * math.cos(a), up, r * math.sin(a))))

    def tangent(self, a):
        return apply(self.R, (-math.sin(a), 0, math.cos(a)))

    def hub_local(self, pos):
        return apply(tuple(zip(*self.R)), sub(pos, LOOP_CENTER))

    def hub_attachment(self, name, pos, children, R=IDENTITY):
        self.hub_fx.append({"class": "Attachment", "name": name, "id": f"{self.t['name']}.{name}",
                            "props": {"CFrame": cframe(R, self.hub_local(pos))}, "children": children})

    def handle_attachment(self, name, pos, children=()):
        self.handle_fx.append({"class": "Attachment", "name": name, "id": f"{self.t['name']}.{name}",
                               "props": {"CFrame": cframe(IDENTITY, pos)}, "children": list(children)})


# ------------------------------------------------------------------ shared ---

def rope_ring(g, center, R, radius, thick, cols, n, name="Rope", **kw):
    g.ring(name, center, R, radius, thick, cols, n=n, collide=False, **kw)


def grip(L):
    t, b = L.t, L.base
    leather = [C(t["leather"]), C(t["leather2"])]
    b.cyl("Handle", 1.0, 0.4, (0, 0, 0), leather[0], R=angles(0, 0, 90), pid=f"{t['name']}.Handle")
    for i in range(5):
        y = -0.36 + i * 0.18
        b.cyl("Wrap", 0.1, 0.46, (0, y, 0), leather[i % 2], R=angles(0, 0, 90 + (8 if i % 2 else -8)), shadow=False)
    for y in (0.52, -0.52):
        b.cyl("Cap", 0.16, 0.52, (0, y, 0), C(t["metal"]), R=angles(0, 0, 90), reflectance=t.get("refl", 0))
        b.cyl("CapRim", 0.06, 0.58, (0, y + (0.1 if y > 0 else -0.1), 0), C(t["metal2"]), R=angles(0, 0, 90),
              reflectance=t.get("refl", 0), shadow=False)
    # Studs on the caps.
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        b.part("ball", "Stud", (0.12, 0.12, 0.12), (0.27 * math.cos(a), 0.52, 0.27 * math.sin(a)), C(t["metal2"]),
               shadow=False)
    # A loop of rope through the top cap, where the rope to the loop starts.
    b.ring("TopKnot", (0, 0.7, 0), angles(90, 0, 0), 0.13, 0.09, [C(t["rope"][0]), C(t["rope"][1])], n=6,
           collide=False, shadow=False)


def coil(L):
    t, b = L.t, L.base
    cols = [C(t["rope"][0]), C(t["rope"][1])]
    for k, (dz, r, roll) in enumerate(((-0.08, 0.5, 6), (0.08, 0.54, -5))):
        R = matmul(angles(0, 0, roll), angles(90, 0, 0))   # ring normal along Z: the coil faces the camera
        rope_ring(b, add(COIL_CENTER, (0.03 * k, 0, dz)), R, r, 0.16, cols, n=14, shadow=False, name="Coil")
    # Bindings that hold the coil together at the top and at the side.
    for pos, rot in (((0, -0.6, 0), (0, 0, 0)), ((0.53, -1.12, 0), (0, 0, 90))):
        b.box("CoilBinding", (0.2, 0.22, 0.46), pos, C(t["binding"]), rot=rot, shadow=False)
        b.box("CoilBindingBand", (0.24, 0.07, 0.5), pos, C(t["metal"]), rot=rot, shadow=False,
              reflectance=t.get("refl", 0))
    # The loose end hangs out of the coil.
    b.rod("RopeEnd", (-0.32, -1.5, 0.08), (-0.4, -1.95, 0.04), 0.14, cols[0], collide=False, shadow=False)
    b.box("RopeTuft", (0.2, 0.14, 0.2), (-0.41, -2.02, 0.04), C(t["tuft"]), shadow=False)
    if t.get("strand"):
        # A glowing thread wound into the middle turn.
        R = matmul(angles(0, 0, -4), angles(90, 0, 0))
        b.ring("CoilGlow", add(COIL_CENTER, (0.03, 0, 0.0)), R, 0.53, 0.05, [C(t["strand"])], n=10, twist=False,
               material="Neon", collide=False, shadow=False)


def loop_rope(L):
    t, g = L.t, L.loop
    cols = [C(t["rope"][0]), C(t["rope"][1])]
    rope_ring(g, LOOP_CENTER, L.R, LOOP_R, 0.24, cols, n=34)
    if t.get("strand"):
        for up in (0.1, -0.1):
            g.ring("GlowStrand", add(LOOP_CENTER, apply(L.R, (0, up, 0))), L.R, LOOP_R, 0.07, [C(t["strand"])],
                   n=18, twist=False, material="Neon", collide=False, shadow=False)
    # The honda: the knot the loop runs through, on the side nearest the hand.
    best = min(range(72), key=lambda i: math.dist(L.on_loop(i * math.pi / 36), GRIP_TOP))
    a = best * math.pi / 36
    L.honda_angle = a
    L.honda = L.on_loop(a)
    Rt = aim(L.tangent(a), roll_up=LOOP_NORMAL)
    g.box("Honda", (0.5, 0.42, 0.42), L.honda, cols[1], R=Rt, shadow=False)
    g.box("HondaWrap", (0.14, 0.48, 0.48), L.honda, C(t["binding"]), R=Rt, shadow=False)
    # Rope to the hand: attachment at the honda (on the hub, so it moves with the spin) and at the grip.
    L.hub_attachment("RopeEnd", L.honda, [])
    L.handle_attachment("RopeStart", GRIP_TOP)
    # Trail: two attachments across the rope, opposite the honda, streak a ribbon while the loop turns.
    far = a + math.pi
    L.hub_attachment("TrailIn", L.on_loop(far, LOOP_R - 0.22), [])
    L.hub_attachment("TrailOut", L.on_loop(far, LOOP_R + 0.22), [])
    return a


def rope_beams(L):
    t = L.t
    name = t["name"]
    rope = {"class": "Beam", "name": "Rope", "props": {
        "Attachment0": {"ref": f"{name}.RopeStart"}, "Attachment1": {"ref": f"{name}.RopeEnd"},
        "Width0": 0.22, "Width1": 0.22, "FaceCamera": True, "Segments": 6, "LightInfluence": 1, "LightEmission": 0,
        "Color": colors((0, t["rope"][0]), (1, t["rope"][1])), "Transparency": seq((0, 0), (1, 0))}}
    glow = {"class": "Beam", "name": "RopeGlow", "props": {
        "Attachment0": {"ref": f"{name}.RopeStart"}, "Attachment1": {"ref": f"{name}.RopeEnd"},
        "Width0": 0.07, "Width1": 0.07, "FaceCamera": True, "Segments": 6, "LightInfluence": 0, "LightEmission": 1,
        "ZOffset": 0.1, "Color": colors((0, t["trail"][0]), (1, t["trail"][1])), "Transparency": seq((0, 0), (1, 0))}}
    trail = {"class": "Trail", "name": "SpinTrail", "props": {
        "Attachment0": {"ref": f"{name}.TrailIn"}, "Attachment1": {"ref": f"{name}.TrailOut"}, "Lifetime": 0.28,
        "LightEmission": 1, "LightInfluence": 0, "FaceCamera": False, "MinLength": 0.02,
        "Color": colors((0, t["trail"][0]), (1, t["trail"][1])), "Transparency": seq((0, 0.25), (1, 1)),
        "WidthScale": seq((0, 1), (1, 0.3))}}
    return [rope, glow, trail]


def loop_light_and_burst(L):
    t = L.t
    color, bright, rng = t["light"]
    L.hub_attachment("Glow", LOOP_CENTER, [{"class": "PointLight", "name": "Light", "props": {
        "Color": list(C(color)), "Brightness": bright, "Range": rng, "Shadows": False}}])
    L.hub_attachment("Burst", LOOP_CENTER, t["burst"])


def ring_emitters(L, name, count, start, make):
    """The same small emitter at `count` points around the loop. The loop turns, so together they cover it."""
    for k in range(count):
        L.hub_attachment(f"{name}{k}", L.on_loop(start + k * 2 * math.pi / count), [make()])


def preview_motes(L, rng, color, n=30, spread=0.7, rise=0.6, size=0.12):
    """Stand-ins for the particles in the preview: small glowing balls around the loop."""
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        p = L.on_loop(a, LOOP_R + rng.uniform(-0.3, 0.3), rng.uniform(-0.1, 0.3))
        p = add(p, (rng.uniform(-spread, spread) * 0.4, rng.uniform(0, rise), rng.uniform(-spread, spread) * 0.4))
        s = size * rng.uniform(0.6, 1.4)
        L.preview_fx.append(("ball", "Mote", (s, s, s), p, C(color), "Neon"))


def preview_trail(L, color):
    """The glowing ribbon the trail leaves behind the spinning loop, as segments."""
    a0 = L.honda_angle + math.pi
    for i in range(10):
        a, b = a0 - i * 0.09, a0 - (i + 1) * 0.09
        pa, pb = L.on_loop(a), L.on_loop(b)
        w = 0.44 * (1 - i / 12)
        L.preview_fx.append(("block", "TrailFx", (math.dist(pa, pb) * 1.05, 0.03, w), scale(add(pa, pb), 0.5),
                             C(color), "Neon", aim(sub(pb, pa), roll_up=LOOP_NORMAL)))


# ---------------------------------------------------------------- Sunburst ---

def sunburst():
    t = dict(name="SunburstLasso", display="Sunburst Lasso", rarity="Legendary",
             rope=("#f2c14e", "#c98a24"), strand="#fff3b0", leather="#9a3324", leather2="#6e2219",
             metal="#f2c14e", metal2="#fff0a8", refl=0.2, binding="#9a3324", tuft="#ffe28a",
             trail=("#fff6c8", "#ffb02e"), light=("#ffd36b", 1.6, 10),
             description="A golden rope that shines like the sun. Gold sparkles and a sun medallion.")
    t["burst"] = [
        emitter("BurstStars", SPARK, colors((0, "#ffffff"), (0.4, "#ffe066"), (1, "#ffaa00")),
                seq((0, 0.9), (1, 0)), 0, (0.8, 1.3), (8, 14), spread=(180, 180), drag=4, enabled=False,
                rotspeed=(-200, 200)),
        emitter("BurstFlash", SPARK, colors((0, "#fffbe0"), (1, "#ffd36b")), seq((0, 3.5), (1, 0)), 0, (0.25, 0.35),
                (0, 0), enabled=False, z=1),
    ]
    L = Lasso(t)
    grip(L)
    coil(L)
    a = loop_rope(L)
    g = L.loop
    # Sun medallion on the honda: a gold disc, rays and a glowing gem.
    Rn = up_to(L.tangent(a))
    center = L.on_loop(a, LOOP_R, 0.0)
    out = apply(L.R, (math.cos(a), 0, math.sin(a)))
    med = add(center, scale(out, 0.36))
    g.cyl("SunDisc", 0.12, 0.62, med, C("#f2c14e"), R=matmul(Rn, angles(0, 0, 90)), reflectance=0.25, shadow=False)
    for k in range(8):
        ang = k * math.pi / 4
        d = apply(Rn, (math.cos(ang), 0, math.sin(ang)))
        g.box("SunRay", (0.32, 0.08, 0.12), add(med, scale(d, 0.42)), C("#ffd23f") if k % 2 else C("#fff3b0"),
              R=aim(d, roll_up=L.tangent(a)), material="Neon", shadow=False)
    g.part("ball", "SunGem", (0.26, 0.26, 0.26), add(med, scale(L.tangent(a), 0.07)), C("#fff6c8"), material="Neon",
           shadow=False)
    # Gold beads with sparkles around the loop.
    for k in range(1, 6):
        ang = a + k * 2 * math.pi / 6
        p = L.on_loop(ang)
        g.part("ball", "Bead", (0.36, 0.36, 0.36), p, C("#ffe28a"), reflectance=0.3, shadow=False)
        g.box("BeadBand", (0.12, 0.33, 0.33), p, C("#c98a24"), R=aim(L.tangent(ang), roll_up=LOOP_NORMAL),
              shadow=False)
    # Particles: gold sparkles fall from the loop, small glints twinkle on it.
    for k, ang in enumerate((a + 2.1, a + 4.2)):
        L.hub_attachment(f"Sparkles{k}", L.on_loop(ang), [
            emitter("GoldSparkles", SPARK, colors((0, "#ffffff"), (0.5, "#ffe066"), (1, "#ff9d00")),
                    seq((0, 0.35), (0.5, 0.25), (1, 0)), 7, (0.8, 1.4), (0.3, 1.0), spread=(180, 180),
                    accel=(0, -2.5, 0), rotspeed=(-120, 120))])
    ring_emitters(L, "Glints", 4, a + 0.5, lambda: emitter(
        "Glints", SPARK, colors((0, "#ffffff"), (1, "#fff3b0")), seq((0, 0), (0.5, 0.45), (1, 0)), 1.5,
        (0.3, 0.5), (0, 0), locked=True))
    loop_light_and_burst(L)
    # The star charm under the grip.
    b = L.base
    b.rod("CharmChain", (0, -0.6, -0.24), (0, -0.84, -0.42), 0.05, C("#fff0a8"), collide=False, shadow=False)
    for turn in (0, 45):
        b.box("StarCharm", (0.34, 0.34, 0.07), (0, -0.98, -0.44), C("#f2c14e"), rot=(0, 0, turn), reflectance=0.3,
              shadow=False)
    b.part("ball", "StarGem", (0.14, 0.14, 0.14), (0, -0.98, -0.49), C("#ff4f4f"), material="Neon", shadow=False)
    rng = random.Random(1)
    preview_motes(L, rng, "#ffe066", n=26, rise=-0.9)
    preview_trail(L, "#ffe9a0")
    return L


# --------------------------------------------------------------- Moonshard ---

def crystal(g, base, d, length, width, color, glow):
    """A crystal: a long box with a pointed tip (two wedges) and a glowing core."""
    R = up_to(d)
    tip = add(base, scale(d, length))
    g.box("Crystal", (width, length, width), add(base, scale(d, length / 2)), C(color), R=R, reflectance=0.15,
          shadow=False)
    for k in range(1):
        Rw = R
        g.wedge("CrystalTip", (width * 0.98, width * 0.9, width / 2),
                add(tip, add(scale(d, width * 0.45), apply(Rw, (0, 0, -width / 4)))), C(color), R=Rw, shadow=False)
        g.wedge("CrystalTip", (width * 0.98, width * 0.9, width / 2),
                add(tip, add(scale(d, width * 0.45), apply(Rw, (0, 0, width / 4)))), C(color),
                R=matmul(Rw, angles(0, 180, 0)), shadow=False)
    g.box("CrystalCore", (width * 0.4, length * 0.8, width * 1.04), add(base, scale(d, length * 0.45)), C(glow), R=R,
          material="Neon", shadow=False)


def moonshard():
    t = dict(name="MoonshardLasso", display="Moonshard Lasso", rarity="Mythic",
             rope=("#4a3488", "#2c2058"), strand="#b98cff", leather="#2b2238", leather2="#1c1626",
             metal="#c9d0e6", metal2="#eef2ff", refl=0.25, binding="#6a4fc0", tuft="#9fd0ff",
             trail=("#d6c2ff", "#5b8cff"), light=("#a77bff", 1.8, 10),
             description="Woven in the Dark Woods. Moon crystals grow on the rope and purple wisps circle it.")
    t["burst"] = [
        emitter("BurstShards", SPARK, colors((0, "#ffffff"), (0.4, "#c7a6ff"), (1, "#5b8cff")),
                seq((0, 0.8), (1, 0)), 0, (0.9, 1.5), (7, 12), spread=(180, 180), drag=3, enabled=False,
                rotspeed=(-300, 300)),
        emitter("BurstRing", SPARK, colors((0, "#e9ddff"), (1, "#8f6bff")), seq((0, 0.5), (1, 0.2)), 0, (0.5, 0.7),
                (9, 9), spread=(0, 180), enabled=False, drag=5),
        emitter("BurstFlash", SPARK, colors((0, "#f2ecff"), (1, "#a77bff")), seq((0, 3.5), (1, 0)), 0, (0.25, 0.35),
                (0, 0), enabled=False, z=1),
    ]
    L = Lasso(t)
    grip(L)
    coil(L)
    a = loop_rope(L)
    g = L.loop
    # Crystals growing out of the rope, pointing outward and a little up.
    palette = [("#8fb0ff", "#dbe6ff"), ("#b48cff", "#efe2ff"), ("#7fd8ff", "#e0f8ff")]
    for k in range(1, 6):
        ang = a + k * 2 * math.pi / 6
        base = L.on_loop(ang, LOOP_R + 0.05)
        out = apply(L.R, (math.cos(ang), 0, math.sin(ang)))
        col, glow = palette[k % 3]
        crystal(g, base, unit(add(out, scale(LOOP_NORMAL, 0.9))), 0.55, 0.2, col, glow)
        crystal(g, add(base, scale(L.tangent(ang), 0.14)), unit(add(scale(out, 0.6), scale(LOOP_NORMAL, 0.5))),
                0.32, 0.14, palette[(k + 1) % 3][0], palette[(k + 1) % 3][1])
    # The honda: a glowing crescent moon.
    out = apply(L.R, (math.cos(a), 0, math.sin(a)))
    mc = add(L.on_loop(a), scale(out, 0.42))
    ax, ay = L.tangent(a), LOOP_NORMAL
    for k in range(7):
        ang = math.radians(-70 + k * 140 / 6) + math.pi
        p = add(mc, add(scale(out, 0.3 * math.cos(ang) + 0.12), scale(ay, 0.3 * math.sin(ang))))
        w = 0.1 + 0.05 * math.sin(math.pi * k / 6)
        g.box("Moon", (0.08, 0.15, w), p, C("#eef2ff"), R=aim(ax, roll_up=add(scale(out, math.cos(ang)), scale(ay, math.sin(ang)))),
              material="Neon", shadow=False)
    g.part("ball", "MoonStar", (0.12, 0.12, 0.12), add(mc, scale(out, 0.18)), C("#b98cff"), material="Neon", shadow=False)
    # Particles: purple wisps that drift up, moon dust that falls.
    for k, ang in enumerate((a + 1.6, a + 3.6, a + 5.2)):
        L.hub_attachment(f"Wisps{k}", L.on_loop(ang), [
            emitter("Wisps", SPARK, colors((0, "#f0e6ff"), (0.5, "#b98cff"), (1, "#5b8cff")),
                    seq((0, 0.15), (0.3, 0.45), (1, 0)), 4, (1.2, 2.0), (0.2, 0.6), spread=(180, 180),
                    accel=(0, 1.2, 0), drag=1, rotspeed=(-60, 60))])
    ring_emitters(L, "MoonDust", 5, a + 0.3, lambda: emitter(
        "MoonDust", SPARK, colors((0, "#ffffff"), (1, "#c7d6ff")), seq((0, 0.12), (1, 0)), 2, (1.0, 1.8),
        (0, 0.2), spread=(180, 180), accel=(0, -1.5, 0)))
    loop_light_and_burst(L)
    # Crescent charm and a crystal pommel.
    b = L.base
    b.rod("CharmChain", (0, -0.6, -0.24), (0, -0.84, -0.42), 0.05, C("#eef2ff"), collide=False, shadow=False)
    for k in range(5):
        ang = math.radians(110 + k * 35)
        p = (0.17 * math.cos(ang) + 0.05, -1.0 + 0.17 * math.sin(ang), -0.44)
        b.box("CrescentCharm", (0.1, 0.1, 0.06), p, C("#dbe6ff"), rot=(0, 0, math.degrees(ang)), material="Neon",
              shadow=False)
    crystal(b, (0.2, 0.56, 0), unit((0.6, 1, 0)), 0.22, 0.13, "#b48cff", "#efe2ff")
    crystal(b, (-0.2, 0.56, 0), unit((-0.6, 1, 0)), 0.18, 0.11, "#8fb0ff", "#dbe6ff")
    rng = random.Random(2)
    preview_motes(L, rng, "#b98cff", n=22, rise=1.2, size=0.16)
    preview_motes(L, rng, "#dbe6ff", n=14, rise=-0.6, size=0.08)
    preview_trail(L, "#b9a0ff")
    return L


# ---------------------------------------------------------------- Wildfire ---

def wildfire():
    t = dict(name="WildfireLasso", display="Wildfire Lasso", rarity="Epic",
             rope=("#3a1c14", "#592616"), strand="#ff7a1a", leather="#241a16", leather2="#3a2a22",
             metal="#4a4a52", metal2="#75757f", refl=0.05, binding="#ff5a1a", tuft="#ffb347",
             trail=("#ffd27a", "#ff3d00"), light=("#ff8a2a", 2.0, 11), flicker=True,
             description="A burning rope that never burns up. Flames, flying embers and smoke.")
    t["burst"] = [
        emitter("BurstFlames", FIRE, colors((0, "#fff2a8"), (0.3, "#ffa31a"), (1, "#c41a00")),
                seq((0, 1.2), (1, 0.2)), 0, (0.4, 0.7), (6, 11), spread=(180, 180), drag=4, enabled=False,
                rotspeed=(-150, 150), transparency=seq((0, 0.1), (1, 1))),
        emitter("BurstEmbers", SPARK, colors((0, "#fff2a8"), (1, "#ff4a00")), seq((0, 0.3), (1, 0)), 0, (0.8, 1.4),
                (10, 16), spread=(180, 180), drag=2, accel=(0, -6, 0), enabled=False),
        emitter("BurstFlash", SPARK, colors((0, "#fff0c0"), (1, "#ff7a1a")), seq((0, 3.5), (1, 0)), 0, (0.25, 0.35),
                (0, 0), enabled=False, z=1),
    ]
    L = Lasso(t)
    grip(L)
    coil(L)
    a = loop_rope(L)
    g = L.loop
    # Glowing cracks in the charred rope.
    rng = random.Random(3)
    for k in range(12):
        ang = a + 0.35 + k * (2 * math.pi - 0.7) / 11
        p = L.on_loop(ang, LOOP_R + rng.uniform(-0.05, 0.05), rng.choice((0.12, -0.12)))
        g.box("Ember", (0.22, 0.06, 0.12), p, C(rng.choice(("#ff5a1a", "#ff8a2a", "#ffc23d"))),
              R=matmul(aim(L.tangent(ang), roll_up=LOOP_NORMAL), angles(0, rng.uniform(-30, 30), 0)),
              material="Neon", shadow=False)
    # The honda: an iron ring with a molten core.
    out = apply(L.R, (math.cos(a), 0, math.sin(a)))
    core = add(L.on_loop(a), scale(out, 0.34))
    g.ring("IronRing", core, up_to(L.tangent(a)), 0.22, 0.09, [C("#4a4a52"), C("#2e2e34")], n=10, collide=False,
           shadow=False)
    g.part("ball", "MoltenCore", (0.26, 0.26, 0.26), core, C("#ffb347"), material="Neon", shadow=False)
    # Particles: flames along the loop, embers flying up, a little smoke.
    for k, ang in enumerate((a + 1.3, a + 2.6, a + 3.9, a + 5.1)):
        L.hub_attachment(f"Flames{k}", L.on_loop(ang), [
            emitter("Flames", FIRE, colors((0, "#fff2a8"), (0.25, "#ffa31a"), (0.7, "#ff4a00"), (1, "#7a1000")),
                    seq((0, 0.45), (0.4, 0.55), (1, 0.05)), 14, (0.35, 0.6), (0.4, 1.0), spread=(25, 25),
                    accel=(0, 5, 0), rotspeed=(-90, 90), rot=(0, 360), transparency=seq((0, 0.3), (0.6, 0.4), (1, 1)))])
    ring_emitters(L, "Embers", 4, a + 0.7, lambda: emitter(
        "Embers", SPARK, colors((0, "#fff2a8"), (0.5, "#ff8a2a"), (1, "#ff3d00")), seq((0, 0.18), (1, 0)), 3,
        (0.8, 1.5), (0.5, 1.5), accel=(0, 4, 0), spread=(40, 40)))
    ring_emitters(L, "Smoke", 2, a + 1.9, lambda: emitter(
        "Smoke", SMOKE, colors((0, "#3a2a24"), (1, "#1a1412")), seq((0, 0.6), (1, 1.6)), 1.5, (1.2, 2.0),
        (0.3, 0.8), accel=(0, 2, 0), light=0, rotspeed=(-30, 30), transparency=seq((0, 1), (0.2, 0.75), (1, 1))))
    loop_light_and_burst(L)
    # Iron horseshoe charm with a glowing edge, and an ember pommel.
    b = L.base
    b.rod("CharmChain", (0, -0.6, -0.24), (0, -0.84, -0.42), 0.05, C("#75757f"), collide=False, shadow=False)
    for sx in (-1, 1):
        b.box("HorseshoeCharm", (0.08, 0.3, 0.07), (sx * 0.13, -1.0, -0.44), C("#ff7a1a"), material="Neon",
              shadow=False)
    b.box("HorseshoeCharm", (0.34, 0.08, 0.07), (0, -1.14, -0.44), C("#ff7a1a"), material="Neon", shadow=False)
    b.part("ball", "EmberPommel", (0.2, 0.2, 0.2), (0, 0.84, 0), C("#ff8a2a"), material="Neon", shadow=False)
    L.handle_attachment("PommelSparks", (0, 0.84, 0), [
        emitter("PommelEmbers", SPARK, colors((0, "#fff2a8"), (1, "#ff4a00")), seq((0, 0.12), (1, 0)), 4, (0.5, 0.9),
                (0.5, 1.2), spread=(30, 30), accel=(0, 3, 0))])
    preview_motes(L, rng, "#ff8a2a", n=30, rise=1.4, size=0.14)
    preview_motes(L, rng, "#ffd27a", n=12, rise=0.4, size=0.22)
    preview_trail(L, "#ffa040")
    return L


LASSOS = [sunburst, moonshard, wildfire]


# ------------------------------------------------------------------ output ---

def part_node(p, owner, owner_id, uid, weld_to_owner=True):
    props = {
        "Size": [round(v, 4) for v in p["size"]], "CFrame": cframe(p["R"], p["p"]), "Color": list(p["color"]),
        "Material": p["material"], "Anchored": False, "CanCollide": False, "CanTouch": False, "CanQuery": False,
        "Massless": True, "CastShadow": p["shadow"], "TopSurface": "Smooth", "BottomSurface": "Smooth",
    }
    if p["transparency"]:
        props["Transparency"] = p["transparency"]
    if p["reflectance"]:
        props["Reflectance"] = p["reflectance"]
    if p["shape"] == "ball":
        props["Shape"] = "Ball"
    elif p["shape"] == "cylinder":
        props["Shape"] = "Cylinder"
    children = list(p["children"])
    if weld_to_owner:
        children.append({"class": "Weld", "name": "Weld", "props": {
            "Part0": {"ref": owner_id}, "Part1": {"ref": uid},
            "C0": cframe(*compose(inverse(owner["R"], owner["p"]), (p["R"], p["p"]))),
        }})
    return {"class": "WedgePart" if p["shape"] == "wedge" else "Part", "name": p["name"], "id": uid,
            "props": props, "children": children}


def tool_node(L, fx_source, burst_source):
    t = L.t
    name = t["name"]
    handle = L.base.parts[0]
    assert handle["name"] == "Handle"
    hub = {"shape": "block", "name": "LoopHub", "size": (0.4, 0.4, 0.4), "R": L.R, "p": LOOP_CENTER,
           "color": C("#ffffff"), "material": "SmoothPlastic", "collide": False, "shadow": False, "transparency": 1,
           "reflectance": 0, "children": [], "id": None}

    hid, lid = f"{name}.Handle", f"{name}.LoopHub"
    nodes = []
    # The Handle: real grip collisions off, but it keeps CanTouch so a dropped lasso can be picked up.
    h = part_node(handle, None, None, hid, weld_to_owner=False)
    h["props"].update(CanTouch=True, Massless=False)
    h["children"] += L.handle_fx + rope_beams(L) + [{
        "class": "Motor6D", "name": "LoopSpin", "props": {
            "Part0": {"ref": hid}, "Part1": {"ref": lid},
            "C0": cframe(L.R, LOOP_CENTER), "C1": cframe(IDENTITY, (0, 0, 0))}}]
    nodes.append(h)
    hub_node = part_node(hub, None, None, lid, weld_to_owner=False)
    hub_node["children"] = L.hub_fx
    nodes.append(hub_node)
    for i, p in enumerate(L.base.parts[1:]):
        nodes.append(part_node(p, handle, hid, f"{name}.b{i}"))
    for i, p in enumerate(L.loop.parts):
        nodes.append(part_node(p, hub, lid, f"{name}.l{i}"))

    attrs = {"DisplayName": t["display"], "Rarity": t["rarity"], "Description": t["description"],
             "SpinSpeed": 1.1, "BurstSpinSpeed": 4.5, "Bursts": 0, "RopeColor": t["rope"][0],
             "GlowColor": t["trail"][1]}
    if t.get("flicker"):
        attrs["Flicker"] = True
    scripts = [
        {"class": "Script", "name": "LassoFX", "props": {"Source": fx_source, "RunContext": "Client"}},
        {"class": "Script", "name": "LassoBurst", "props": {"Source": burst_source, "RunContext": "Server"}},
    ]
    return {"class": "Tool", "name": t["display"], "attrs": attrs, "tags": ["Lasso"],
            "props": {"CanBeDropped": False, "RequiresHandle": True, "ToolTip": t["display"],
                      "Grip": cframe(IDENTITY, (0, 0, 0))},
            "children": nodes + scripts}


def preview(lassos):
    """Viewer scene: each lasso held by a blocky character, plus close-ups."""
    r = lambda v: [round(x, 3) for x in v]
    vp = lambda n, s, z, cf, c, m="SmoothPlastic", t=0, sh=True: {
        "n": n, "s": s, "z": r(z), "cf": r(cf), "c": r(c), "m": m, "t": t, "r": 0, "st": False, "sh": sh}
    parts = [vp("Floor", "block", (120, 2, 80), cframe(IDENTITY, (0, -1, 0)), C("#d9b98c"), m="WoodPlanks")]
    shots = {}
    for k, L in enumerate(lassos):
        ox = (k - 1) * 12
        # Character: R15-ish proportions, right arm held forward like the default tool pose.
        body = [("block", (2, 2, 1), (0, 4, 0), "#3a6fd8"), ("block", (1, 2, 1), (-0.5, 2, 0), "#2b2f3a"),
                ("block", (1, 2, 1), (0.5, 2, 0), "#2b2f3a"), ("block", (1.2, 1.2, 1.2), (0, 5.6, 0), "#f1c9a0"),
                ("block", (1, 2, 1), (-1.5, 4, 0), "#3a6fd8"), ("block", (1.7, 0.25, 1.7), (0, 6.3, 0), "#8a5a2e"),
                ("block", (1.1, 0.6, 1.1), (0, 6.6, 0), "#8a5a2e")]
        for i, (s, z, p, c) in enumerate(body):
            parts.append(vp(f"Body{i}", s, z, cframe(IDENTITY, add(p, (ox, 0, 0))), C(c)))
        parts.append(vp("ArmR", "block", (1, 1, 2), cframe(IDENTITY, (ox + 1.5, 4.5, -1.0)), C("#3a6fd8")))
        hand = (ox + 1.5, 4.5, -2.0)
        for g in (L.base, L.loop):
            for i, p in enumerate(g.parts):
                parts.append(vp(f"{p['name']}_{i}", p["shape"], p["size"], cframe(p["R"], add(hand, p["p"])),
                                p["color"], m=p["material"], t=p["transparency"], sh=p["shadow"]))
        # The rope from the grip to the honda (a Beam in the game).
        a, b = add(hand, GRIP_TOP), add(hand, L.honda)
        parts.append(vp("RopeBeam", "block", (math.dist(a, b), 0.2, 0.2), cframe(aim(sub(b, a)), scale(add(a, b), 0.5)),
                        C(L.t["rope"][0])))
        for fx in L.preview_fx:
            shape, nm, size, p, c, m = fx[:6]
            R = fx[6] if len(fx) > 6 else IDENTITY
            parts.append(vp(nm, shape, size, cframe(R, add(hand, p)), c, m=m, sh=False))
        key = L.t["name"].replace("Lasso", "").lower()
        center = add(hand, (0, 1.0, 0))
        shots[key] = {"camera": {"pos": r(add(center, (5.5, 2.0, -7.5))), "target": r(center), "fov": 45},
                      "shadow": {"center": r(hand), "radius": 10}}
        shots[key + "_back"] = {"camera": {"pos": r(add(center, (2.0, 2.5, 8.5))), "target": r(add(center, (0, 0.5, 0))),
                                           "fov": 45}, "shadow": {"center": r(hand), "radius": 10}}
    shots["all"] = {"camera": {"pos": [6, 9, -26], "target": [0, 4.5, -2], "fov": 50},
                    "shadow": {"center": [0, 0, 0], "radius": 24}}
    env = {"sky": [[0, "#2b3f6b"], [0.55, "#5a78b0"], [1, "#9fb6d8"]], "fog": ["#9fb6d8", 120, 300],
           "sun": {"dir": [-0.4, 1.0, -0.7], "intensity": 1.6}, "hemi": ["#ffffff", "#806040", 1.2],
           "bloom": [0.6, 0.5, 0.75]}
    return {"env": env, "parts": parts, "models": [], "texts": [], "sprites": [], "shots": shots}


def main():
    fx_source = (HERE / "LassoFX.lua").read_text()
    burst_source = (HERE / "LassoBurst.lua").read_text()
    lassos = [make() for make in LASSOS]
    tools = [tool_node(L, fx_source, burst_source) for L in lassos]
    tree = [{"class": "Folder", "name": "Lassos", "children": tools}]
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "lassos.json").write_text(json.dumps(tree))
    (out / "world.json").write_text(json.dumps(preview(lassos)))
    for L in lassos:
        n = len(L.base.parts) + len(L.loop.parts) + 1
        emitters = json.dumps(L.hub_fx + L.handle_fx + L.t["burst"]).count("ParticleEmitter")
        print(f"{L.t['display']:16} {n:4} parts, {emitters} particle emitters")
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cargo", "run", "--quiet", "--release", "--manifest-path",
                        str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "lassos.json"), target],
                       check=True)


if __name__ == "__main__":
    main()
