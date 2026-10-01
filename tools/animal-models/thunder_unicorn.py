"""The Thunder Unicorn: an exclusive mount (game pass), in the same blocky studded style as the other animals.

A storm-blue unicorn with a mane and tail of storm clouds full of lightning, a golden spiral horn that crackles,
glowing thunder hooves, lightning brands on its flanks, a royal saddle and three charged orbs that circle it,
linked by arcs of electricity. Faces -Z, +X is its right side and y = 0 is the ground.

The AnimalFX script animates it (profile "ThunderUnicorn"): a walk, a gallop at speed that leaves lightning
trails, sparks and a shockwave under every hoof, and every few seconds while it stands still it rears up and
calls a lightning bolt down onto its horn.

The RideAttachment on the RootPart is where the rider sits (on the saddle). The model's attributes Mount = true
and SpeedMultiplier = 8 are for your mount script.
"""

import math
import random

from animals import DETAIL, find, fx
from dark_woods import GLOW, beam, emitter, extras, light, pulse, scale_animal, seg, trail, unfight
from lib import SIDES, SMOKE_TEXTURE, SPARKLE_TEXTURE, Animal, add, aim, angles, apply, cross, matmul, scale, \
    sub, unit
from lib import hex_color as C

COAT, COAT_DARK, BELLY = C("#5468d8"), C("#3f4fae"), C("#aab7ff")
CLOUD = [C("#8e9bd0"), C("#b9c4ee"), C("#e4e9ff")]   # dark underside, middle, light top
BOLT, BOLT_HOT, SPARK = C("#ffe14d"), C("#fff7c2"), C("#4fd6ff")
GOLD, GOLD_DARK, ROYAL, ROYAL_DARK = C("#ffcf3f"), C("#d9962a"), C("#4a238f"), C("#2b1257")

K = 1.45   # final scale: the rider sits about 12 studs up


def cloud(a, name, center, size, rng, R=None, shade=None):
    """A puff of storm cloud: a big soft ball with two smaller ones on top, dark below and light above."""
    w, h, d = size
    a.ell(name, (w, h, d), center, shade or CLOUD[1], role="Secondary")
    a.ell(f"{name}Puff", (w * 0.62, h * 0.62, d * 0.62), add(center, (w * 0.2, h * 0.32, -d * 0.12)), CLOUD[2],
          role="Secondary", shadow=False)
    a.ell(f"{name}Puff2", (w * 0.5, h * 0.5, d * 0.5), add(center, (-w * 0.25, h * 0.25, d * 0.18)), CLOUD[2],
          role="Secondary", shadow=False)
    a.ell(f"{name}Under", (w * 0.7, h * 0.45, d * 0.7), add(center, (0, -h * 0.3, 0)), CLOUD[0], role="Secondary",
          shadow=False)


def bolt(a, name, start, end, width, color=BOLT, side=(1, 0, 0), jag=0.32):
    """A lightning bolt: a zigzag of three glowing beams from start to end."""
    d = sub(end, start)
    n = unit(cross(unit(d), side)) if abs(sum(x * y for x, y in zip(unit(d), side))) < 0.95 else (0, 0, 1)
    off = scale(n, math.dist(start, end) * jag)
    p1 = add(add(start, scale(d, 0.36)), off)
    p2 = add(add(start, scale(d, 0.64)), scale(off, -1))
    pts = [start, p1, p2, end]
    for i in range(3):
        seg(a, f"{name}{i}", pts[i], pts[i + 1], width * (1 - 0.18 * i), color, ext=0.45, **GLOW)
    return pts


def thunder_unicorn():
    rng = random.Random(8)
    a = Animal("ThunderUnicorn", "Thunder Unicorn", "Exclusive")

    # -- body ---------------------------------------------------------------
    a.oct("Body", (3.8, 3.4, 7.2), (0, 6.0, 0.4), COAT, b=1.0, bottom=0.7)
    a.bevel("Belly", (3.86, 1.2, 6.4), (0, 4.9, 0.45), BELLY, b=0, bottom=0.73, role="Secondary")
    a.oct("Chest", (3.1, 2.6, 0.5), (0, 5.9, -3.35), BELLY, b=0.45, role="Secondary")
    a.oct("Withers", (2.4, 0.6, 1.6), (0, 7.75, -2.2), COAT, b=0.25)
    # Lightning brands on the hindquarters.
    for s, S in SIDES:
        bolt(a, f"FlankBolt{S}", (1.93 * s, 7.2, 2.0), (1.93 * s, 5.2, 3.3), 0.32, side=(1, 0, 0), jag=0.25)
    # The chest medallion: a gold disc with a lightning bolt.
    a.cyl("ChestMedal", 0.2, 1.3, (0, 6.2, -3.66), GOLD, R=angles(0, 90, 0), role="Accent", reflectance=0.2)
    a.cyl("ChestMedalRim", 0.14, 1.5, (0, 6.2, -3.6), GOLD_DARK, R=angles(0, 90, 0), role="Accent")
    bolt(a, "ChestBolt", (0.15, 6.68, -3.8), (-0.12, 5.72, -3.8), 0.16, side=(0, 0, 1), jag=0.35)

    # -- saddle -------------------------------------------------------------
    a.bevel("Blanket", (4.06, 0.3, 3.2), (0, 7.72, 0.3), ROYAL, b=0.12, role="Accent")
    for s, S in SIDES:
        a.box(f"BlanketFlap{S}", (0.22, 1.9, 3.2), (2.0 * s, 6.85, 0.3), ROYAL, role="Accent")
        a.box(f"BlanketTrim{S}", (0.26, 0.24, 3.3), (2.02 * s, 5.95, 0.3), GOLD, role="Accent", reflectance=0.15)
        a.box(f"BlanketTrimBack{S}", (0.26, 1.9, 0.22), (2.02 * s, 6.85, 1.85), GOLD, role="Accent", shadow=False)
        a.box(f"BlanketTrimFront{S}", (0.26, 1.9, 0.22), (2.02 * s, 6.85, -1.25), GOLD, role="Accent", shadow=False)
        bolt(a, f"BlanketBolt{S}", (2.14 * s, 7.45, -0.3), (2.14 * s, 6.25, 0.85), 0.22, side=(1, 0, 0), jag=0.28)
        # Stirrup leathers and golden stirrups.
        a.box(f"StirrupStrap{S}", (0.12, 2.0, 0.3), (2.25 * s, 5.85, 0.2), ROYAL_DARK, role="Accent", shadow=False)
        a.box(f"Stirrup{S}", (0.5, 0.14, 0.8), (2.32 * s, 4.75, 0.2), GOLD, role="Accent", reflectance=0.2)
        for z in (-0.35, 0.35):
            a.box(f"StirrupSide{S}{'F' if z < 0 else 'B'}", (0.5, 0.6, 0.12), (2.32 * s, 5.0, 0.2 + z), GOLD,
                  role="Accent", shadow=False)
    a.bevel("Seat", (2.7, 0.55, 2.5), (0, 8.12, 0.3), ROYAL_DARK, b=0.2, role="Accent")
    a.bevel("Cantle", (2.5, 0.75, 0.45), (0, 8.55, 1.45), ROYAL_DARK, b=0.2, role="Accent")
    a.box("CantleTrim", (2.56, 0.16, 0.5), (0, 8.95, 1.45), GOLD, role="Accent", shadow=False)
    a.bevel("Pommel", (1.6, 0.6, 0.45), (0, 8.5, -0.85), ROYAL_DARK, b=0.2, role="Accent")
    a.post("SaddleHorn", (0.4, 0.5, 0.4), (0, 9.05, -0.85), GOLD, b=0.1, role="Accent")
    a.box("SaddleHornCap", (0.65, 0.18, 0.65), (0, 9.35, -0.85), GOLD, role="Accent", reflectance=0.2)
    a.box("Girth", (4.0, 0.4, 0.5), (0, 4.4, 0.3), ROYAL_DARK, role="Accent", shadow=False)

    # -- head and neck --------------------------------------------------------
    with a.bone("Head", "Body", (0, 7.2, -2.6)):
        neck_R = matmul(angles(-38, 0, 0), angles(90, 0, 0))
        a.taper("Neck", (2.3, 2.5), (1.8, 2.0), 4.4, (0, 8.75, -3.6), COAT, R=neck_R, r=0.35)
        a.box("Throat", (1.2, 2.6, 0.3), (0, 8.25, -4.45), BELLY, rot=(-38, 0, 0), role="Secondary")
        head_R = angles(-22, 0, 0)
        hc = (0, 10.95, -5.35)
        hat = lambda x, y, z: add(hc, apply(head_R, (x, y, z)))
        a.oct("Head", (2.6, 3.0, 2.9), hc, COAT, b=0.8, bottom=0.55, R=head_R)
        a.taper("Muzzle", (2.2, 1.5), (1.95, 1.3), 1.9, hat(0, -0.62, -2.2), BELLY, R=head_R, r=0.32,
                role="Secondary")
        for s, S in SIDES:
            a.box(f"Nostril{S}", (0.3, 0.36, 0.12), hat(0.48 * s, -0.4, -3.17), C("#3a3f7a"), R=head_R, **DETAIL)
        a.box("Smile", (0.7, 0.12, 0.1), hat(0, -0.98, -3.16), C("#3a3f7a"), R=head_R, **DETAIL)
        for s, S in SIDES:
            eye_R = matmul(head_R, angles(0, -14 * s, 0))
            a.eye2(f"Eye{S}", hat(0.66 * s, 0.68, -1.5), R=eye_R, w=1.0, h=1.2, iris=SPARK, glow=True)
            a.box(f"Brow{S}", (0.75, 0.16, 0.12), hat(0.7 * s, 1.42, -1.52), C("#2b2f66"),
                  R=matmul(eye_R, angles(0, 0, -14 * s)), **DETAIL)
            a.box(f"Cheek{S}", (0.5, 0.26, 0.1), hat(1.0 * s, -0.08, -1.49), C("#ff9ecf"), R=eye_R, **DETAIL)
            ear_R = matmul(angles(0, 0, -16 * s), angles(78, 0, 0))
            a.taper(f"Ear{S}", (0.75, 0.8), (0.3, 0.35), 1.6, hat(0.8 * s, 2.15, 0.55), COAT, R=ear_R, r=0.4)
            a.box(f"InnerEar{S}", (0.34, 1.0, 0.1), hat(0.8 * s, 2.1, 0.17), SPARK,
                  R=matmul(head_R, angles(0, 0, -16 * s)), **GLOW)
            # Bridle: a cheek strap with a gold rosette, and a rein back to the neck.
            a.box(f"CheekStrap{S}", (0.12, 2.4, 0.26), hat(1.32 * s, 0.0, -0.2), ROYAL, R=head_R, **DETAIL)
            a.cyl(f"Rosette{S}", 0.14, 0.55, hat(1.37 * s, 0.95, -0.2), GOLD, R=head_R, role="Accent", shadow=False)
        a.box("BrowBand", (2.66, 0.26, 0.3), hat(0, 1.25, -0.2), GOLD, R=head_R, role="Accent", shadow=False)

        # The horn: a golden spiral with glowing bands, crackling at the tip.
        horn_dir = unit(apply(head_R, (0, 0.82, -0.57)))
        base = hat(0, 1.45, -0.75)
        a.cyl("HornBase", 0.35, 0.95, add(base, scale(horn_dir, 0.1)), GOLD_DARK, R=_axis(horn_dir), role="Accent")
        length, n = 3.3, 6
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            p = add(base, scale(horn_dir, length * (t0 + t1) / 2 + 0.2))
            d = 0.78 * (1 - t0 * 0.8)
            a.box(f"Horn{i}", (length / n * 1.08, d, d), p, GOLD if i % 2 == 0 else C("#ffe27a"),
                  R=matmul(_axis(horn_dir), angles(i * 30, 0, 0)), role="Accent", reflectance=0.25, studs=False)
            a.box(f"HornBand{i}", (0.1, d * 1.06, d * 1.06), add(p, scale(horn_dir, length / n * 0.5)), SPARK,
                  R=matmul(_axis(horn_dir), angles(i * 30 + 15, 0, 0)), **GLOW)
        tip = add(base, scale(horn_dir, length + 0.35))
        a.box("HornTip", (0.34, 0.34, 0.34), tip, BOLT_HOT, R=_axis(horn_dir), **GLOW)

        # Forelock and mane: storm clouds down the neck, with lightning bolts poking out.
        cloud(a, "Forelock", hat(0, 1.75, 0.3), (1.6, 0.9, 1.3), rng)
        mane = [((0, 12.2, -4.3), 1.35), ((0, 11.5, -3.7), 1.5), ((0, 10.7, -3.1), 1.55), ((0, 9.85, -2.55), 1.5),
                ((0, 9.0, -2.0), 1.4), ((0, 8.35, -1.55), 1.2)]
        for i, (p, s_) in enumerate(mane):
            cloud(a, f"Mane{i}", add(p, (0.12 * (-1) ** i, 0, 0.35)), (s_ * 1.1, s_ * 0.85, s_), rng)
        for i, (p, h) in enumerate([((0, 12.3, -3.9), 1.2), ((0, 10.8, -2.75), 1.3), ((0, 9.2, -1.7), 1.1)]):
            sx = (-1) ** i
            bolt(a, f"ManeBolt{i}", add(p, (0.3 * sx, 0.2, 0.2)), add(p, (0.85 * sx, 0.2 + h, 0.9)), 0.2,
                 side=(0, 0, 1), jag=0.3)

    # -- legs ---------------------------------------------------------------
    for s, S in SIDES:
        for z, F in ((-2.3, "F"), (2.7, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (1.15 * s, 4.7, z)):
                a.taper(f"Leg{F}{S}", (1.25, 1.3), (0.9, 0.95), 2.5, (1.15 * s, 3.55, z), COAT, R=angles(-90, 0, 0),
                        r=0.3)
                a.post(f"LowerLeg{F}{S}", (0.82, 2.2, 0.88), (1.15 * s, 1.55, z), COAT_DARK, b=0.25)
                # Storm feathering around the fetlock, then a glowing thunder hoof.
                a.ell(f"Feather{F}{S}", (1.55, 0.75, 1.55), (1.15 * s, 0.85, z), CLOUD[1], role="Secondary")
                a.ell(f"FeatherPuff{F}{S}", (1.0, 0.55, 1.0), (1.15 * s + 0.2 * s, 1.12, z - 0.2), CLOUD[2],
                      role="Secondary", shadow=False)
                a.bevel(f"Hoof{F}{S}", (1.12, 0.58, 1.18), (1.15 * s, 0.29, z), SPARK, b=0.18, **GLOW)
                a.box(f"HoofCore{F}{S}", (0.7, 0.62, 0.6), (1.15 * s, 0.31, z - 0.32), BOLT_HOT, **GLOW)

    # -- tail ----------------------------------------------------------------
    with a.bone("Tail", "Body", (0, 7.0, 3.9)):
        pts = [(0, 7.25, 4.2), (0, 6.7, 4.95), (0, 5.9, 5.45), (0, 5.0, 5.7), (0, 4.1, 5.75)]
        for i, (p, s_) in enumerate(zip(pts, (1.25, 1.45, 1.4, 1.25, 1.0))):
            cloud(a, f"Tail{i}", add(p, (0.1 * (-1) ** i, 0, 0)), (s_, s_ * 0.95, s_ * 0.9), rng)
        bolt(a, "TailBolt", (0, 4.2, 5.8), (0.2, 2.9, 6.3), 0.26, side=(1, 0, 0), jag=0.4)
        bolt(a, "TailBoltSmall", (0.5, 6.3, 5.4), (1.2, 6.9, 6.3), 0.16, side=(0, 1, 0), jag=0.3)

    # -- charged orbs that circle the unicorn ------------------------------------
    with a.bone("Orbit", "Body", (0, 6.4, 0.4)):
        for i in range(3):
            ang = i * 2 * math.pi / 3
            p = (math.cos(ang) * 4.6, 6.4 + 0.5 * math.sin(3 * ang), 0.4 + math.sin(ang) * 5.6)
            a.ball(f"Orb{i}", 0.9, p, SPARK, **GLOW)
            a.ball(f"OrbCore{i}", 0.5, p, BOLT_HOT, **GLOW)
            for j, rot in enumerate(((0, 0, 0), (0, 0, 90), (90, 0, 0))):
                a.box(f"OrbSpike{i}{j}", (1.5, 0.12, 0.12), p, BOLT, rot=rot, **GLOW)

    a.ride_height, a.ride_z = 8.45, 0.25
    a.overhead = 13.4

    scale_animal(a, K)
    unfight(a, "Belly", "Chest", "Seat", "Blanket", "Throat", "Muzzle", d=0.04)

    # -- effects ---------------------------------------------------------------
    fx(a, "HornTip",
       light("HornLight", SPARK, brightness=2.2, range_=16, pulse=0.9),
       emitter("HornCrackle", BOLT_HOT, texture=SPARKLE_TEXTURE, rate=16, lifetime=(0.2, 0.45), speed=(2, 5),
               sizes=((0, 0.55), (1, 0)), transparency=((0, 0), (1, 1)), color2=SPARK, drag=3))
    for i in (1, 3, 5):
        fx(a, f"Mane{i}",
           emitter("StormCloud", CLOUD[1], texture=SMOKE_TEXTURE, rate=2.5, lifetime=(1.2, 2.0), speed=(0.3, 0.8),
                   sizes=((0, 1.2), (1, 2.6)), transparency=((0, 0.55), (1, 1)), light=0, accel=(0, 0.6, 0),
                   color2=CLOUD[0]),
           emitter("ManeSparks", BOLT, texture=SPARKLE_TEXTURE, rate=4, lifetime=(0.25, 0.5), speed=(2, 4),
                   sizes=((0, 0.45), (1, 0)), transparency=((0, 0), (1, 1)), color2=SPARK))
    fx(a, "Tail2",
       emitter("TailCloud", CLOUD[1], texture=SMOKE_TEXTURE, rate=3, lifetime=(1.2, 2.0), speed=(0.3, 0.7),
               sizes=((0, 1.4), (1, 2.8)), transparency=((0, 0.55), (1, 1)), light=0, color2=CLOUD[0]),
       emitter("TailSparks", BOLT, texture=SPARKLE_TEXTURE, rate=5, lifetime=(0.25, 0.5), speed=(2, 4),
               sizes=((0, 0.45), (1, 0)), transparency=((0, 0), (1, 1)), color2=SPARK))
    for s, S in SIDES:
        for F in ("F", "B"):
            fx(a, f"Hoof{F}{S}",
               emitter("HoofCrackle", SPARK, texture=SPARKLE_TEXTURE, rate=5, lifetime=(0.2, 0.4), speed=(1, 3),
                       sizes=((0, 0.4), (1, 0)), transparency=((0, 0), (1, 1)), emit="Bottom", spread=70,
                       color2=BOLT_HOT))
        # Lightning trails behind the back hooves while it gallops.
        hoof = find(a, f"HoofB{S}")["p"]
        trail(a, f"HoofB{S}", add(hoof, (0, 0.35 * K, 0)), add(hoof, (0, -0.25 * K, 0)), SPARK, name=f"HoofTrail{S}",
              lifetime=0.35, color2=BOLT, transparency=((0, 0.1), (1, 1)))
    tail_tip = find(a, "TailBolt2")["p"]
    trail(a, "Tail0", add(find(a, "Tail0")["p"], (0, 0.5 * K, 0)), add(tail_tip, (0, 0, 0)), BOLT, name="StormTrail",
          lifetime=0.45, color2=SPARK, transparency=((0, 0.35), (1, 1)))
    for i in range(3):
        fx(a, f"Orb{i}", light(f"OrbLight{i}", SPARK, brightness=1.0, range_=8, pulse=0.6 + 0.2 * i))
        orb, nxt = find(a, f"Orb{i}")["p"], find(a, f"Orb{(i + 1) % 3}")["p"]
        beam(a, f"Orb{i}", orb, f"Orb{(i + 1) % 3}", nxt, SPARK, name=f"Arc{i}", width=(0.35, 0.35),
             curve=(1.5, -1.5), transparency=((0, 0.35), (0.5, 0.1), (1, 0.35)), segments=12,
             color2=BOLT_HOT, texture=SPARKLE_TEXTURE, texture_speed=4)
    fx(a, "Body",
       emitter("Static", SPARK, texture=SPARKLE_TEXTURE, rate=6, lifetime=(0.3, 0.6), speed=(0.5, 1.5),
               sizes=((0, 0.4), (1, 0)), transparency=((0, 0), (1, 1)), color2=BOLT_HOT),
       light("StormLight", SPARK, brightness=1.0, range_=18, pulse=1.8))
    pulse(a, "HoofFL", "HoofFR", "HoofBL", "HoofBR", seconds=0.8)
    pulse(a, "InnerEarL", "InnerEarR", seconds=1.2)
    extras(a, attrs={"OrbitSpeed": 0.45, "Mount": True, "SpeedMultiplier": 8, "WalkSpeed": 16},
           highlight=(SPARK, C("#bff3ff"), 1.0, 0.6))
    return a


def _axis(d):
    """Rotation whose local X axis points along d (for horn pieces)."""
    return aim(d)


ALL = [thunder_unicorn]
