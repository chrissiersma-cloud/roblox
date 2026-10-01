"""The Thunder Unicorn: the exclusive mount (game pass), in the same blocky studded style as the other animals,
but built as the showpiece of the game.

A storm-navy winged unicorn with glowing lightning veins under its coat, platinum and gold armour (a chest plate
with a storm gem, neck plates, a face plate and leg guards), a crystal horn with three floating rings and an
energy column rising from its tip, a mane and tail of storm clouds and electric flames, and two great energy wings
that beat slowly while it stands and open wide when it gallops. A rune circle turns on the ground under it, and
charged orbs and crystal shards circle it, linked by arcs of electricity.

Faces -Z, +X is its right side and y = 0 is the ground. The AnimalFX script animates it (profile "ThunderUnicorn"):
a walk, a gallop with the wings spread that calls small lightning strikes down beside its hooves, and two idle
actions: "thunder" (rears up, a bolt strikes its horn) and "storm" (rears up with its wings spread and calls a
ring of lightning down around it).

The RideAttachment on the RootPart is where the rider sits (on the saddle). The model's attributes Mount = true
and SpeedMultiplier = 5 are for your mount script.
"""

import math
import random

from animals import DETAIL, find, fx, pixel_star
from dark_woods import GLOW, beam, emitter, extras, ground_ring, light, plate, pulse, scale_animal, seg, \
    trail, unfight
from lib import SIDES, SMOKE_TEXTURE, SPARKLE_TEXTURE, Animal, add, aim, angles, apply, cross, matmul, scale, \
    sub, unit
from lib import hex_color as C

FIRE_TEXTURE = "rbxasset://textures/particles/fire_main.dds"

COAT, COAT_HI, COAT_DARK, BELLY = C("#2b3277"), C("#3c47a3"), C("#1d2156"), C("#4a56b8")
CLOUD = [C("#3d4580"), C("#6872b4"), C("#a9b3e8")]       # underside, middle, top
SPARK, SPARK_HOT, ICE = C("#4fe3ff"), C("#e9fdff"), C("#9ff0ff")
BOLT = C("#ffe14d")
PLAT, PLAT_DARK = C("#dfe5f5"), C("#9aa4c4")
GOLD, GOLD_DARK = C("#ffcf3f"), C("#c98a1c")
ROYAL = C("#1b1d4f")

NECK_UP = (0, 0.788, -0.616)
NECK_BACK = (0, 0.616, 0.788)
K = 1.5
GLOW_T = dict(GLOW, transparency=0.2)
METAL = dict(role="Accent", reflectance=0.18)


def cloud(a, name, center, size):
    """A puff of storm cloud: a big soft ball with two lighter ones on top and a dark one underneath."""
    w, h, d = size
    a.ell(name, (w, h, d), center, CLOUD[1], role="Secondary")
    a.ell(f"{name}Puff", (w * 0.62, h * 0.62, d * 0.62), add(center, (w * 0.2, h * 0.32, -d * 0.12)), CLOUD[2],
          role="Secondary", shadow=False)
    a.ell(f"{name}Under", (w * 0.7, h * 0.45, d * 0.7), add(center, (0, -h * 0.3, 0)), CLOUD[0], role="Secondary",
          shadow=False)


def bolt(a, name, start, end, width, color=SPARK, side=(1, 0, 0), jag=0.32):
    """A lightning bolt: a zigzag of three glowing beams from start to end."""
    d = sub(end, start)
    n = unit(cross(unit(d), side)) if abs(sum(x * y for x, y in zip(unit(d), side))) < 0.95 else (0, 0, 1)
    off = scale(n, math.dist(start, end) * jag)
    pts = [start, add(add(start, scale(d, 0.36)), off), add(add(start, scale(d, 0.64)), scale(off, -1)), end]
    for i in range(3):
        seg(a, f"{name}{i}", pts[i], pts[i + 1], width * (1 - 0.18 * i), color, ext=0.45, **GLOW)
    return pts


def flame(a, name, base, direction, length, width, core=True):
    """A flickering energy flame: a translucent cyan blade with a white-hot core."""
    tip = add(base, scale(unit(direction), length))
    plate(a, name, base, tip, width, 0.14, SPARK, up=(1, 0, 0), **GLOW_T)
    if core:
        plate(a, f"{name}Core", base, add(base, scale(unit(direction), length * 0.65)), width * 0.4, 0.18, SPARK_HOT,
              up=(1, 0, 0), **GLOW)


def rune_disc(a, name, center, normal_axis, r, n=10):
    """A small glowing rune: a ring of dashes standing on a body side (normal along X)."""
    for i in range(n):
        ang = 2 * math.pi * i / n
        p = add(center, (0, r * math.sin(ang), r * math.cos(ang)))
        a.box(f"{name}{i}", (0.1, 0.12, 2 * math.pi * r / n * 0.6), p, SPARK, rot=(-math.degrees(ang), 0, 0), **GLOW)


# ------------------------------------------------------------------- wings ---

def wing(a, s, S):
    """One great energy wing (right for s = 1), folded up and back. Built in its own Wing joint at the withers, so
    AnimalFX can beat it."""
    root = (1.45 * s, 8.3, -1.8)
    arm = [root, (3.0 * s, 10.3, -1.3), (4.8 * s, 11.8, -0.1), (6.4 * s, 12.7, 1.5), (7.4 * s, 13.0, 2.9)]
    with a.bone(f"Wing{S}", "Body", root):
        # The arm: platinum bones with gold joints and a glowing leading edge.
        for i in range(len(arm) - 1):
            t = 0.55 - 0.08 * i
            seg(a, f"Wing{S}Arm{i}", arm[i], arm[i + 1], t, PLAT, **METAL)
            seg(a, f"Wing{S}Edge{i}", add(arm[i], (0, t * 0.55, -0.12)), add(arm[i + 1], (0, t * 0.55, -0.12)),
                0.12, SPARK, ext=0.3, **GLOW)
        for i in (1, 2, 3):
            a.ball(f"Wing{S}Joint{i}", 0.75 - 0.08 * i, arm[i], GOLD, **METAL)
        a.box(f"Wing{S}Gem", (0.42, 0.42, 0.42), add(arm[1], (0, 0.42, 0)), SPARK, rot=(45, 0, 45), **GLOW)
        back = unit((0.12 * s, -0.3, 1.0))           # feathers fall back and a little down
        armdir = unit(sub(arm[3], arm[0]))
        normal = unit(cross(armdir, back))
        if normal[1] < 0:
            normal = scale(normal, -1)

        def along(t):
            """Point at t (0..1) along the arm polyline."""
            x = t * (len(arm) - 1)
            i = min(int(x), len(arm) - 2)
            f = x - i
            return add(arm[i], scale(sub(arm[i + 1], arm[i]), f))

        # Coverts (short platinum feathers), secondaries (pale blue) and primaries (glowing energy, fanned out).
        # Near the body the feathers stay short, so the rider's legs have room.
        for i in range(8):
            t = 0.04 + i * 0.6 / 7
            p = along(t)
            plate(a, f"Wing{S}Covert{i}", p, add(p, scale(back, 1.2)), 0.8, 0.14, PLAT if i % 2 else PLAT_DARK,
                  up=normal, role="Accent", shadow=False)
            q = add(p, scale(back, 0.7))
            ln = (0.6 if t < 0.2 else 2.0) + 1.0 * t
            plate(a, f"Wing{S}Secondary{i}", q, add(q, scale(back, ln)), 0.78, 0.12,
                  C("#8fa3ff") if i % 2 else C("#b7c5ff"), up=normal, role="Secondary", shadow=False)
            a.box(f"Wing{S}SecondaryGlow{i}", (0.14, 0.14, 0.5), add(q, scale(back, ln + 0.05)), SPARK,
                  R=aim(back, roll_up=normal), **GLOW)
        for i in range(7):
            t = 0.55 + i * 0.45 / 6
            p = along(t)
            fan = unit(add(scale(back, 1.0 - 0.13 * i), scale(armdir, 0.16 * i)))
            ln = 3.0 + 0.25 * i
            q = add(p, scale(back, 0.5))
            plate(a, f"Wing{S}Primary{i}", q, add(q, scale(fan, ln)), 0.7, 0.12, SPARK, up=normal, **GLOW_T)
            plate(a, f"Wing{S}PrimaryCore{i}", q, add(q, scale(fan, ln * 0.7)), 0.26, 0.16, SPARK_HOT, up=normal,
                  **GLOW)
    return arm


# -------------------------------------------------------------------- model ---

def thunder_unicorn():
    random.seed(8)
    a = Animal("ThunderUnicorn", "Thunder Unicorn", "Exclusive")

    # -- body, sculpted ------------------------------------------------------------
    a.oct("Body", (3.9, 3.5, 7.4), (0, 6.1, 0.4), COAT, b=1.05, bottom=0.7)
    a.bevel("Belly", (3.96, 1.2, 6.5), (0, 4.95, 0.45), BELLY, b=0, bottom=0.73, role="Secondary")
    a.oct("Chest", (3.2, 2.7, 0.5), (0, 6.0, -3.5), BELLY, b=0.45, role="Secondary")
    a.oct("Withers", (2.5, 0.65, 1.7), (0, 7.88, -2.3), COAT, b=0.25)
    for s, S in SIDES:
        a.bevel(f"Shoulder{S}", (0.4, 2.4, 2.4), (1.98 * s, 6.25, -2.0), COAT_HI, b=0.15, role="Secondary")
        a.bevel(f"Haunch{S}", (0.4, 2.6, 2.8), (1.98 * s, 6.25, 2.55), COAT_HI, b=0.15, role="Secondary")
        # Lightning veins glowing through the coat, and a storm rune on each haunch.
        bolt(a, f"Vein{S}", (2.02 * s, 7.2, -0.9), (2.02 * s, 5.2, 0.6), 0.16, side=(1, 0, 0), jag=0.3)
        bolt(a, f"ShoulderVein{S}", (2.21 * s, 7.1, -2.6), (2.21 * s, 5.3, -1.6), 0.14, side=(1, 0, 0), jag=0.28)
        rune_disc(a, f"Rune{S}", (2.22 * s, 6.25, 2.55), (1, 0, 0), 0.85)
        bolt(a, f"RuneBolt{S}", (2.24 * s, 6.85, 2.75), (2.24 * s, 5.65, 2.35), 0.16, side=(1, 0, 0), jag=0.3)

    # -- armour: chest plate with a storm gem ------------------------------------
    a.bevel("Peytral", (2.4, 1.7, 0.3), (0, 6.25, -3.86), PLAT, b=0.25, **METAL)
    for s, S in SIDES:
        a.box(f"PeytralWing{S}", (1.0, 1.4, 0.26), (1.55 * s, 6.3, -3.6), PLAT_DARK, rot=(0, -38 * s, 0), **METAL)
        a.box(f"PeytralEdge{S}", (0.12, 1.5, 0.3), (2.0 * s, 6.3, -3.25), GOLD, rot=(0, -38 * s, 0), **METAL)
    a.box("PeytralTrim", (2.5, 0.2, 0.36), (0, 7.1, -3.88), GOLD, **METAL)
    a.box("PeytralTrimLow", (2.2, 0.18, 0.36), (0, 5.42, -3.88), GOLD, **METAL)
    a.box("ChestGemFrame", (1.15, 1.15, 0.2), (0, 6.25, -4.06), GOLD, rot=(0, 0, 45), **METAL)
    a.box("ChestGem", (0.8, 0.8, 0.3), (0, 6.25, -4.12), SPARK, rot=(0, 0, 45), **GLOW)
    a.box("ChestGemCore", (0.36, 0.36, 0.34), (0, 6.25, -4.16), SPARK_HOT, rot=(0, 0, 45), **GLOW)

    # -- saddle: royal caparison with glowing runes, platinum saddle -------------
    a.bevel("Blanket", (4.16, 0.3, 3.4), (0, 7.85, 0.35), ROYAL, b=0.12, role="Accent")
    for s, S in SIDES:
        a.box(f"BlanketFlap{S}", (0.22, 2.3, 3.4), (2.06 * s, 6.85, 0.35), ROYAL, role="Accent")
        a.box(f"BlanketGlow{S}", (0.26, 0.12, 3.44), (2.08 * s, 5.85, 0.35), SPARK, **GLOW)
        a.box(f"BlanketTrim{S}", (0.27, 0.22, 3.5), (2.08 * s, 5.62, 0.35), GOLD, **METAL)
        for k in range(6):
            a.box(f"Tassel{S}{k}", (0.12, 0.42, 0.16), (2.1 * s, 5.3, -1.0 + k * 0.54), GOLD, role="Accent",
                  shadow=False)
        bolt(a, f"BlanketBolt{S}", (2.19 * s, 7.6, -0.35), (2.19 * s, 6.15, 1.05), 0.22, color=BOLT,
             side=(1, 0, 0), jag=0.28)
        a.box(f"StirrupStrap{S}", (0.12, 2.0, 0.3), (2.3 * s, 5.95, 0.2), PLAT_DARK, role="Accent", shadow=False)
        a.box(f"Stirrup{S}", (0.52, 0.14, 0.82), (2.38 * s, 4.85, 0.2), GOLD, **METAL)
        for z in (-0.36, 0.36):
            a.box(f"StirrupSide{S}{'F' if z < 0 else 'B'}", (0.52, 0.6, 0.12), (2.38 * s, 5.1, 0.2 + z), GOLD,
                  role="Accent", shadow=False)
    a.bevel("Seat", (2.7, 0.55, 2.5), (0, 8.24, 0.35), C("#15163a"), b=0.2, role="Accent")
    a.box("SeatGlow", (2.76, 0.1, 2.56), (0, 8.0, 0.35), SPARK, **GLOW)
    a.bevel("Cantle", (2.6, 0.85, 0.45), (0, 8.72, 1.5), PLAT, b=0.2, **METAL)
    for s, S in SIDES:   # flared cantle wings
        a.wedge(f"CantleFlare{S}", (0.3, 0.9, 0.9), (1.35 * s, 9.15, 1.55), GOLD, rot=(0, 90 * s, 0), **METAL)
    a.bevel("Pommel", (1.6, 0.65, 0.45), (0, 8.62, -0.85), PLAT, b=0.2, **METAL)
    a.box("PommelGem", (0.42, 0.42, 0.2), (0, 8.7, -1.12), SPARK, rot=(0, 0, 45), **GLOW)
    a.post("SaddleHorn", (0.4, 0.5, 0.4), (0, 9.15, -0.85), GOLD, b=0.1, **METAL)
    a.box("SaddleHornCap", (0.66, 0.18, 0.66), (0, 9.45, -0.85), GOLD, **METAL)
    a.box("Girth", (4.1, 0.4, 0.5), (0, 4.45, 0.35), ROYAL, role="Accent", shadow=False)

    # -- wings ------------------------------------------------------------------------
    for s, S in SIDES:
        wing(a, s, S)

    # -- head and neck --------------------------------------------------------------
    with a.bone("Head", "Body", (0, 7.3, -2.7)):
        neck_R = matmul(angles(-38, 0, 0), angles(90, 0, 0))
        a.taper("Neck", (2.35, 2.55), (1.85, 2.05), 4.5, (0, 8.85, -3.7), COAT, R=neck_R, r=0.35)
        a.box("Throat", (1.2, 2.7, 0.3), (0, 8.35, -4.57), BELLY, rot=(-38, 0, 0), role="Secondary")
        # Neck plates (crinet) on both sides, with a glowing line.
        for s, S in SIDES:
            for k, t in enumerate((-0.9, 0.5, 1.8)):
                p = add(add((0, 9.5, -2.8), scale(NECK_UP, t)), (1.06 * s - 0.04 * t * s, -0.55, -0.55))
                a.box(f"Crinet{S}{k}", (0.16, 1.15, 1.25 - 0.1 * k), p, PLAT if k % 2 == 0 else PLAT_DARK,
                      rot=(-38, 0, 0), **METAL)
                a.box(f"CrinetGlow{S}{k}", (0.2, 0.1, 1.0 - 0.1 * k), add(p, (0.02 * s, 0.35, 0.3)), SPARK,
                      rot=(-38, 0, 0), **GLOW)

        head_R = angles(-22, 0, 0)
        hc = (0, 11.1, -5.45)
        hat = lambda x, y, z: add(hc, apply(head_R, (x, y, z)))
        a.oct("Head", (2.6, 3.0, 2.9), hc, COAT, b=0.8, bottom=0.55, R=head_R)
        a.taper("Muzzle", (2.2, 1.5), (1.95, 1.3), 1.9, hat(0, -0.62, -2.2), BELLY, R=head_R, r=0.32,
                role="Secondary")
        for s, S in SIDES:
            a.box(f"Nostril{S}", (0.3, 0.36, 0.12), hat(0.48 * s, -0.4, -3.17), C("#0f1236"), R=head_R, **DETAIL)
            a.box(f"NostrilGlow{S}", (0.14, 0.18, 0.14), hat(0.48 * s, -0.4, -3.19), SPARK, R=head_R, **GLOW)
        a.box("Smile", (0.7, 0.12, 0.1), hat(0, -0.98, -3.16), C("#0f1236"), R=head_R, **DETAIL)
        # Face plate (chanfron) down the nose, and a crest on the brow that the horn grows out of.
        a.bevel("Chanfron", (0.85, 0.14, 1.9), hat(0, 0.18, -2.25), PLAT, b=0.04, R=head_R, **METAL)
        a.box("ChanfronLine", (0.18, 0.18, 1.6), hat(0, 0.24, -2.25), SPARK, R=head_R, **GLOW)
        a.bevel("BrowCrest", (1.8, 0.55, 0.22), hat(0, 1.42, -1.5), PLAT, b=0.12, R=head_R, **METAL)
        a.box("BrowCrestTrim", (1.86, 0.14, 0.26), hat(0, 1.66, -1.5), GOLD, R=head_R, **METAL)
        for s, S in SIDES:
            eye_R = matmul(head_R, angles(0, -14 * s, 0))
            a.eye2(f"Eye{S}", hat(0.66 * s, 0.62, -1.5), R=eye_R, w=1.0, h=1.15, iris=SPARK, glow=True,
                   look=(0, 0.2))
            a.box(f"Brow{S}", (0.85, 0.18, 0.14), hat(0.72 * s, 1.18, -1.56), C("#0b0d2a"),
                  R=matmul(eye_R, angles(0, 0, 18 * s)), **DETAIL)
            a.tri(f"Lash{S}", hat(1.14 * s, 1.0, -1.52), 0.3, 0.42, 0.08, C("#0b0d2a"),
                  R=matmul(eye_R, angles(0, 0, -45 * s)), **DETAIL)
            ear_R = matmul(angles(0, 0, -16 * s), angles(78, 0, 0))
            a.taper(f"Ear{S}", (0.75, 0.8), (0.3, 0.35), 1.7, hat(0.82 * s, 2.15, 0.55), COAT, R=ear_R, r=0.4)
            a.box(f"InnerEar{S}", (0.34, 1.05, 0.1), hat(0.82 * s, 2.1, 0.17), SPARK,
                  R=matmul(head_R, angles(0, 0, -16 * s)), **GLOW)
            a.box(f"EarCap{S}", (0.4, 0.4, 0.4), hat(0.98 * s, 2.95, 0.6), GOLD,
                  R=matmul(head_R, angles(0, 0, -16 * s)), **METAL)
            a.box(f"CheekPlate{S}", (0.14, 1.1, 1.0), hat(1.33 * s, -0.15, -0.55), PLAT, R=head_R, **METAL)
            a.box(f"CheekGem{S}", (0.18, 0.4, 0.4), hat(1.41 * s, -0.15, -0.55), SPARK,
                  R=matmul(head_R, angles(45, 0, 0)), **GLOW)

        # The horn: a golden spiral base, then a glowing crystal blade, with three floating rune rings.
        hd = unit(apply(head_R, (0, 0.85, -0.53)))
        hR = aim(hd)
        base = hat(0, 1.55, -1.0)
        a.cyl("HornBase", 0.4, 1.05, add(base, scale(hd, 0.1)), GOLD_DARK, R=hR, role="Accent")
        for i in range(4):
            d = 0.82 - 0.08 * i
            a.box(f"HornSpiral{i}", (0.52, d, d), add(base, scale(hd, 0.45 + i * 0.48)), GOLD if i % 2 == 0
                  else C("#ffe27a"), R=matmul(hR, angles(i * 30, 0, 0)), studs=False, **METAL)
        for i in range(4):
            d = 0.5 - 0.1 * i
            p = add(base, scale(hd, 2.4 + i * 0.6))
            a.box(f"HornBlade{i}", (0.66, d, d), p, ICE, R=matmul(hR, angles(45 + i * 20, 0, 0)), **GLOW_T)
            a.box(f"HornCore{i}", (0.7, d * 0.45, d * 0.45), p, SPARK_HOT, R=matmul(hR, angles(45 + i * 20, 0, 0)),
                  **GLOW)
        tip = add(base, scale(hd, 4.95))
        a.box("HornTip", (0.3, 0.3, 0.3), tip, SPARK_HOT, R=hR, **GLOW)
        # Rings: dashes around the horn (in the plane at right angles to it).
        side1 = unit(cross(hd, (1, 0, 0)))
        side2 = unit(cross(hd, side1))
        for r_i, (t, r) in enumerate(((1.6, 0.85), (2.9, 0.7), (4.0, 0.52))):
            c0 = add(base, scale(hd, t))
            n = 8 if r_i < 2 else 6
            for i in range(n):
                ang = 2 * math.pi * i / n
                rad = add(scale(side1, math.cos(ang)), scale(side2, math.sin(ang)))
                tang = add(scale(side1, -math.sin(ang)), scale(side2, math.cos(ang)))
                a.box(f"HornRing{r_i}_{i}", (2 * math.pi * r / n * 0.55, 0.1, 0.1), add(c0, scale(rad, r)),
                      SPARK if i % 2 else SPARK_HOT, R=aim(tang, roll_up=hd), **GLOW)

        # Forelock and mane: storm clouds along the neck with electric flames blowing back.
        cloud(a, "Forelock", hat(0, 1.95, 0.25), (1.6, 0.9, 1.3))
        flame(a, "ForelockFlame", hat(0, 2.1, 0.5), (0, 0.55, 1), 1.6, 0.55)
        for i in range(6):
            t = 2.2 - i * 0.85
            p = add(add((0, 9.5, -2.8), scale(NECK_UP, t)), scale(NECK_BACK, 0.35))
            cloud(a, f"Mane{i}", p, (1.35, 1.0, 1.25))
            sx = 0.3 * (-1) ** i
            flame(a, f"ManeFlame{i}", add(p, (sx, 0.35, 0.2)), (sx, 0.5, 1.0), 2.0 + 0.3 * (i % 3), 0.62)
        for i, (t, h) in enumerate(((1.6, 1.3), (-0.2, 1.4), (-1.9, 1.1))):
            p = add(add((0, 9.5, -2.8), scale(NECK_UP, t)), scale(NECK_BACK, 0.6))
            sx = (-1) ** i
            bolt(a, f"ManeBolt{i}", add(p, (0.3 * sx, 0.2, 0.2)), add(p, (0.9 * sx, 0.2 + h, 1.0)), 0.2,
                 color=BOLT, side=(0, 0, 1), jag=0.3)

    # -- legs ----------------------------------------------------------------------------
    for s, S in SIDES:
        for z, F in ((-2.35, "F"), (2.75, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (1.17 * s, 4.75, z)):
                a.taper(f"Leg{F}{S}", (1.3, 1.35), (0.92, 0.98), 2.55, (1.17 * s, 3.58, z), COAT, R=angles(-90, 0, 0),
                        r=0.3)
                a.post(f"LowerLeg{F}{S}", (0.84, 2.25, 0.9), (1.17 * s, 1.55, z), COAT_DARK, b=0.25)
                bolt(a, f"LegVein{F}{S}", (1.17 * s + 0.47 * s, 4.3, z - 0.1), (1.17 * s + 0.47 * s, 3.1, z + 0.15),
                     0.12, side=(1, 0, 0), jag=0.3)
                a.box(f"KneeBand{F}{S}", (1.0, 0.3, 1.06), (1.17 * s, 2.6, z), GOLD, **METAL)
                a.bevel(f"Greave{F}{S}", (0.76, 1.3, 0.16), (1.17 * s, 1.75, z - 0.5), PLAT, b=0.1, **METAL)
                a.box(f"GreaveGem{F}{S}", (0.3, 0.3, 0.18), (1.17 * s, 2.05, z - 0.6), SPARK, rot=(0, 0, 45), **GLOW)
                a.ell(f"Feather{F}{S}", (1.6, 0.8, 1.6), (1.17 * s, 0.86, z), CLOUD[1], role="Secondary")
                a.ell(f"FeatherPuff{F}{S}", (1.0, 0.55, 1.0), (1.37 * s, 1.14, z - 0.2), CLOUD[2], role="Secondary",
                      shadow=False)
                for k, (dx, dz) in enumerate(((0.45, 0.3), (-0.45, 0.3), (0, 0.55))):
                    plate(a, f"HoofFlame{k}{F}{S}", (1.17 * s + dx, 0.75, z + dz), (1.17 * s + dx * 1.5, 1.65, z + dz + 0.4),
                          0.32, 0.1, SPARK, up=(1, 0, 0), **GLOW_T)
                a.bevel(f"Hoof{F}{S}", (1.14, 0.6, 1.2), (1.17 * s, 0.3, z), SPARK, b=0.18, **GLOW)
                a.box(f"HoofCore{F}{S}", (0.72, 0.64, 0.62), (1.17 * s, 0.32, z - 0.32), SPARK_HOT, **GLOW)
                a.box(f"Shoe{F}{S}", (1.2, 0.14, 1.26), (1.17 * s, 0.07, z), PLAT, **METAL)

    # -- tail: a long storm cloud with flames and a bolt ------------------------------
    with a.bone("Tail", "Body", (0, 7.1, 4.0)):
        pts = [(0, 7.35, 4.3), (0, 7.0, 5.1), (0, 6.25, 5.75), (0, 5.3, 6.1), (0, 4.25, 6.25), (0, 3.2, 6.2)]
        for i, (p, s_) in enumerate(zip(pts, (1.25, 1.45, 1.5, 1.4, 1.25, 1.0))):
            cloud(a, f"Tail{i}", add(p, (0.1 * (-1) ** i, 0, 0)), (s_, s_ * 0.95, s_ * 0.9))
            if i in (1, 2, 3, 4):
                flame(a, f"TailFlame{i}", add(p, (0.25 * (-1) ** i, 0.1, 0.35)), (0.25 * (-1) ** i, 0.25, 1.0),
                      1.8 - 0.2 * (i - 1), 0.55)
        bolt(a, "TailBolt", (0, 3.3, 6.3), (0.25, 1.9, 6.9), 0.26, color=BOLT, side=(1, 0, 0), jag=0.4)

    # -- the storm crown: orbs, crystal shards and a rune circle that circle it ---------
    with a.bone("Orbit", "Body", (0, 6.4, 0.4)):
        for i in range(3):
            ang = i * 2 * math.pi / 3
            p = (math.cos(ang) * 5.6, 7.4 + 0.6 * math.sin(3 * ang), 0.4 + math.sin(ang) * 6.6)
            a.ball(f"Orb{i}", 1.0, p, SPARK, **GLOW_T)
            a.ball(f"OrbCore{i}", 0.55, p, SPARK_HOT, **GLOW)
            for j, rot in enumerate(((0, 0, 0), (0, 0, 90), (90, 0, 0))):
                a.box(f"OrbSpike{i}{j}", (1.7, 0.12, 0.12), p, BOLT, rot=rot, **GLOW)
        for i in range(6):
            ang = i * 2 * math.pi / 6 + math.pi / 6
            p = (math.cos(ang) * 6.2, 4.2 + 1.2 * (i % 2), 0.4 + math.sin(ang) * 7.0)
            a.shard(f"Shard{i}", p, 0.45, 1.6, ICE, R=angles(0, -math.degrees(ang), 15 * (-1) ** i), cross=True,
                    **GLOW_T)
        ground_ring(a, "RuneOuter", (0, 0.12, 0.4), 7.4, SPARK, n=24, size=(0.4, 0.08, 1.4), transparency=0.15)
        ground_ring(a, "RuneInner", (0, 0.12, 0.4), 5.9, SPARK_HOT, n=16, size=(0.3, 0.08, 1.0), transparency=0.3)
        for i in range(6):   # rune marks between the two rings
            ang = i * 2 * math.pi / 6
            pixel_star(a, f"RuneMark{i}", (math.cos(ang) * 6.65, 0.12, 0.4 + math.sin(ang) * 6.65), 0.7, SPARK,
                       R=matmul(angles(0, -math.degrees(ang), 0), angles(-90, 0, 0)), depth=0.08)

    a.ride_height, a.ride_z = 8.6, 0.3
    a.overhead = 14.2
    scale_animal(a, K)
    unfight(a, "Belly", "Chest", "Seat", "Blanket", "Throat", "Muzzle", d=0.04)

    effects(a)
    pulse(a, *[f"HornRing{r}_{i}" for r in range(3) for i in range(0, 8, 2) if r < 2 or i < 6], seconds=0.7)
    pulse(a, "ChestGem", "PommelGem", "SeatGlow", seconds=1.3)
    pulse(a, "HoofFL", "HoofFR", "HoofBL", "HoofBR", seconds=0.8)
    pulse(a, *[f"RuneOuter{i}" for i in range(0, 24, 3)], seconds=1.6)
    extras(a, attrs={"OrbitSpeed": 0.5, "FlapSpeed": 1.6, "FlapAngle": 9, "Mount": True, "SpeedMultiplier": 5,
                     "WalkSpeed": 16},
           highlight=(SPARK, C("#bff7ff"), 1.0, 0.45))
    return a


def effects(a):
    p = lambda name: find(a, name)["p"]
    spark_kw = dict(texture=SPARKLE_TEXTURE, transparency=((0, 0), (1, 1)))
    # Horn: a crackling tip, an energy column rising into the sky, and a bright light.
    tip = p("HornTip")
    fx(a, "HornTip",
       light("HornLight", SPARK, brightness=2.6, range_=20, pulse=0.9),
       emitter("HornCrackle", SPARK_HOT, rate=22, lifetime=(0.2, 0.45), speed=(3, 7), sizes=((0, 0.6), (1, 0)),
               color2=SPARK, drag=3, **spark_kw),
       emitter("HornRise", SPARK, rate=10, lifetime=(1.0, 1.6), speed=(4, 7), spread=8,
               sizes=((0, 0.5), (1, 0)), color2=SPARK_HOT, **spark_kw))
    beam(a, "HornTip", tip, "HornTip", add(tip, (0, 14, 0)), SPARK, name="HornColumn", width=(0.9, 0.05),
         transparency=((0, 0.2), (0.6, 0.6), (1, 1)), segments=6, color2=SPARK_HOT, texture=SPARKLE_TEXTURE,
         texture_speed=3)
    beam(a, "HornTip", tip, "Orb0", p("Orb0"), SPARK, name="HornArc", width=(0.3, 0.3), curve=(3, -3),
         transparency=((0, 0.4), (0.5, 0.15), (1, 0.4)), segments=14, color2=SPARK_HOT, texture=SPARKLE_TEXTURE,
         texture_speed=5)
    # Mane and tail: electric flames, storm clouds and sparks.
    for i in (0, 2, 4):
        fx(a, f"ManeFlame{i}",
           emitter("ManeFire", SPARK, texture=FIRE_TEXTURE, rate=9, lifetime=(0.35, 0.6), speed=(1.5, 3),
                   sizes=((0, 0.9), (1, 0.2)), transparency=((0, 0.3), (1, 1)), color2=SPARK_HOT, spread=25,
                   accel=(0, 4, 3)),
           emitter("ManeSparks", BOLT, rate=4, lifetime=(0.25, 0.5), speed=(2, 4), sizes=((0, 0.45), (1, 0)),
                   color2=SPARK, **spark_kw))
    for i in (1, 4):
        fx(a, f"Mane{i}", emitter("StormCloud", CLOUD[1], texture=SMOKE_TEXTURE, rate=2.5, lifetime=(1.2, 2.0),
                                  speed=(0.3, 0.8), sizes=((0, 1.4), (1, 3.0)), transparency=((0, 0.55), (1, 1)),
                                  light=0, accel=(0, 0.6, 0), color2=CLOUD[0]))
    fx(a, "TailFlame2", emitter("TailFire", SPARK, texture=FIRE_TEXTURE, rate=10, lifetime=(0.35, 0.6), speed=(1, 3),
                                sizes=((0, 1.0), (1, 0.2)), transparency=((0, 0.3), (1, 1)), color2=SPARK_HOT,
                                spread=30, accel=(0, 3, 4)))
    fx(a, "Tail3", emitter("TailCloud", CLOUD[1], texture=SMOKE_TEXTURE, rate=3, lifetime=(1.2, 2.0), speed=(0.3, 0.7),
                           sizes=((0, 1.5), (1, 3.0)), transparency=((0, 0.55), (1, 1)), light=0, color2=CLOUD[0]))
    trail(a, "Tail0", add(p("Tail0"), (0, 0.6 * K, 0)), p("TailBolt2"), SPARK, name="StormTrail", lifetime=0.5,
          color2=BOLT, transparency=((0, 0.3), (1, 1)))
    # Wings: glitter drifting down from the feathers, light trails from the wing tips.
    for s, S in SIDES:
        fx(a, f"Wing{S}Primary3", emitter("WingGlitter", SPARK_HOT, rate=8, lifetime=(1.2, 2.0), speed=(0.3, 1.0),
                                          sizes=((0, 0.45), (1, 0)), color2=SPARK, accel=(0, -2, 0), **spark_kw))
        fx(a, f"Wing{S}Secondary4", emitter("WingDust", ICE, rate=5, lifetime=(1.0, 1.8), speed=(0.2, 0.6),
                                            sizes=((0, 0.35), (1, 0)), color2=SPARK, accel=(0, -1.5, 0), **spark_kw))
        tip_feather = find(a, f"Wing{S}Primary6")
        tip_p = tip_feather["p"]
        trail(a, f"Wing{S}Primary6", add(tip_p, (0, 0.5 * K, 0)), add(tip_p, (0, -0.5 * K, 0)), SPARK,
              name=f"WingTrail{S}", lifetime=0.4, color2=SPARK_HOT, transparency=((0, 0.2), (1, 1)))
    # Hooves: crackling lightning and light trails.
    for s, S in SIDES:
        for F in ("F", "B"):
            hoof = p(f"Hoof{F}{S}")
            fx(a, f"Hoof{F}{S}", emitter("HoofCrackle", SPARK, rate=6, lifetime=(0.2, 0.4), speed=(1, 3),
                                         sizes=((0, 0.45), (1, 0)), emit="Bottom", spread=70, color2=SPARK_HOT,
                                         **spark_kw))
            trail(a, f"Hoof{F}{S}", add(hoof, (0, 0.35 * K, 0)), add(hoof, (0, -0.25 * K, 0)), SPARK,
                  name=f"HoofTrail{F}{S}", lifetime=0.35, color2=BOLT, transparency=((0, 0.1), (1, 1)))
    # The storm crown: lit orbs linked by arcs, sparkling shards.
    for i in range(3):
        fx(a, f"Orb{i}", light(f"OrbLight{i}", SPARK, brightness=1.0, range_=9, pulse=0.6 + 0.2 * i),
           emitter("OrbSparks", SPARK_HOT, rate=6, lifetime=(0.3, 0.6), speed=(1, 3), sizes=((0, 0.4), (1, 0)),
                   color2=SPARK, **spark_kw))
        beam(a, f"Orb{i}", p(f"Orb{i}"), f"Orb{(i + 1) % 3}", p(f"Orb{(i + 1) % 3}"), SPARK, name=f"Arc{i}",
             width=(0.4, 0.4), curve=(2, -2), transparency=((0, 0.35), (0.5, 0.1), (1, 0.35)), segments=14,
             color2=SPARK_HOT, texture=SPARKLE_TEXTURE, texture_speed=4)
    for i in (0, 3):
        fx(a, f"Shard{i}", emitter("ShardGlint", SPARK_HOT, rate=3, lifetime=(0.5, 0.9), speed=(0.2, 0.6),
                                   sizes=((0, 0.5), (1, 0)), color2=ICE, **spark_kw))
    # Body: static sparks, a storm light and a chest gem light.
    fx(a, "Body",
       emitter("Static", SPARK, rate=8, lifetime=(0.3, 0.6), speed=(0.5, 1.5), sizes=((0, 0.45), (1, 0)),
               color2=SPARK_HOT, **spark_kw),
       light("StormLight", SPARK, brightness=1.2, range_=22, pulse=1.8))
    fx(a, "ChestGem", light("GemLight", SPARK, brightness=1.2, range_=10, pulse=1.3))


ALL = [thunder_unicorn]
