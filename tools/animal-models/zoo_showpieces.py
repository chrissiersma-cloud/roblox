"""The zoo's top animals rebuilt as showpieces in the part style of the other animals, so they replace the old stud
meshes (same AnimalId):

  * Voidwhisker (Mythic, about 500 parts): a slender shadow cat with galaxy fur full of stars and constellations,
    big pink slit-pupil eyes, a glowing rune on the brow, a void collar with a pink gem, two pink diamonds
    floating beside it (tethered to the collar by beams of light) and a crystal on its curling tail.
  * Gorilla King (Secret, about 800 parts): a huge knuckle-walking silverback with a gold crown full of rubies and
    diamonds, gold grills with diamond teeth, a heavy gold chain with a diamond medallion, an ermine collar, gold
    epaulettes, a gold earring and gold bracelets with diamonds. Gold coins and diamonds orbit around it.

Both face -Z, +X is their right side, y = 0 is the ground. Their animations and idle actions are in AnimalFX.lua
(profiles Voidwhisker and GorillaKing).
"""

import math
import random

from animals import DETAIL, find, fx
from dark_woods import GLOW, GLOW_TEXTURE, SHOCK_TEXTURE, VORTEX_TEXTURE, FLAMESPARK_TEXTURE, beam, chain, \
    emitter, extras, flat, grad, ground_ring, in_bone, light, plate, pulse, scale_animal, trail, unfight
from lib import SIDES, SPARKLE_TEXTURE, SMOKE_TEXTURE, WHITE, Animal, add, angles, apply, matmul, scale, sub, unit
from lib import hex_color as C

GLOW_T = dict(GLOW, transparency=0.25)
GLASS = dict(material="Glass", role="Glow", shadow=False, studs=False, transparency=0.15, reflectance=0.35)


def at(base, R, offset):
    return add(base, apply(R, offset))


def gem(a, name, center, width, height, color, R=None, **kw):
    """A cut gem: two crossed diamond shapes (a short point up, a long point down) round a small core."""
    R = R or angles()
    kw = kw or GLOW
    a.box(f"{name}Up", (width * 0.5,) * 3, center, color, R=matmul(R, angles(0, 45, 0)), **kw)
    a.box(f"{name}Down", (width * 0.3,) * 3, at(center, R, (0, -height * 0.2, 0)), color,
          R=matmul(R, angles(0, 45, 0)), **kw)
    for i, turn in enumerate((45, 135)):
        a.tri(f"{name}Top{i}", center, width, height * 0.4, width * 0.22, color, R=matmul(R, angles(0, turn, 0)), **kw)
        a.tri(f"{name}Low{i}", center, width, height * 0.6, width * 0.22, color, R=matmul(R, angles(0, turn, 180)),
              **kw)


def glint(name, color=WHITE, rate=1.5, size=1.2):
    """Bling: a star that twinkles on and off (diamonds, gold)."""
    return emitter(name, color, texture=SPARKLE_TEXTURE, rate=rate, lifetime=(0.35, 0.5), speed=(0, 0),
                   sizes=((0, 0), (0.5, size), (1, 0)), transparency=((0, 0), (1, 0.2)), lock=True,
                   rot_speed=(-200, 200))


# =================================================================================== Voidwhisker ===

FUR, FUR2, FUR3 = C("#24163d"), C("#33204f"), C("#170d29")
PINK, HOTPINK, VIOLET = C("#ff8ce6"), C("#ff4fd8"), C("#b14dff")
LILAC, GEMPINK, SLIT = C("#e3b8ff"), C("#ffd6ff"), C("#1a0a2a")


def voidwhisker():
    a = Animal("Voidwhisker", "Voidwhisker", "Mythic")
    rng = random.Random(7)

    # -- body ----------------------------------------------------------------------------------
    a.oct("Body", (3.0, 2.8, 6.2), (0, 5.3, 0.6), FUR, b=0.9, bottom=0.7)
    a.bevel("Belly", (3.0, 1.0, 5.2), (0, 4.35, 0.7), FUR2, b=0, bottom=0.7, role="Secondary")
    a.oct("Chest", (2.6, 2.6, 1.0), (0, 5.3, -2.4), FUR2, b=0.7, role="Secondary")
    for s, S in SIDES:
        a.wedge(f"ShoulderBlade{S}", (0.5, 0.8, 1.6), (0.9 * s, 6.85, -1.4), FUR, rot=(0, 0, 0))
    # Galaxy fur: nebula clouds on the flanks, stars and a constellation drawn between some of them.
    for s, S in SIDES:
        for j, (y, z, w, col, tr) in enumerate(((5.4, -0.7, 1.5, VIOLET, 0.55), (5.0, 0.4, 1.2, HOTPINK, 0.6),
                                                (5.5, 1.5, 1.6, VIOLET, 0.55), (4.9, 2.5, 1.0, HOTPINK, 0.6),
                                                (5.8, 3.2, 0.9, LILAC, 0.65))):
            a.box(f"Nebula{S}{j}", (0.06, w, w * 1.2), (1.52 * s, y, z), col, rot=(45 + 10 * j, 0, 0),
                  **dict(GLOW, transparency=tr))
        stars = [(5.9, -1.6), (5.2, -0.4), (5.7, 0.7), (4.8, 1.6), (5.5, 2.7), (6.1, 3.3)]
        for j, (y, z) in enumerate(stars):
            big = j % 2 == 0
            a.box(f"Star{S}{j}", (0.08, 0.3 if big else 0.2, 0.3 if big else 0.2), (1.56 * s, y, z),
                  WHITE if big else GEMPINK, rot=(45, 0, 0), **GLOW)
        for j in range(len(stars) - 1):
            (y0, z0), (y1, z1) = stars[j], stars[j + 1]
            a.beam(f"Constellation{S}{j}", (1.55 * s, y0, z0), (1.55 * s, y1, z1), 0.06, LILAC,
                   **dict(GLOW, transparency=0.35))
        for j in range(10):
            y, z = rng.uniform(4.2, 6.3), rng.uniform(-2.2, 3.6)
            a.box(f"Speck{S}{j}", (0.06, 0.12, 0.12), (1.54 * s, y, z), WHITE if j % 3 else LILAC, **GLOW)
        for j in range(4):
            a.wedge(f"BellyFringe{S}{j}", (0.22, 0.55, 0.8), (1.25 * s, 3.85, -1.2 + j * 1.2), FUR3, rot=(0, 0, 180),
                    role="Secondary")
    for j in range(12):
        x, z = rng.uniform(-1.0, 1.0), rng.uniform(-2.2, 3.6)
        a.box(f"BackSpeck{j}", (0.14, 0.06, 0.14), (x, 6.72, z), WHITE if j % 3 else GEMPINK, rot=(0, 45, 0), **GLOW)
    # A row of small void crystals along the spine.
    for j in range(5):
        a.shard(f"SpineCrystal{j}", (0, 6.6, -0.8 + j * 0.9), 0.3, 0.7 - 0.06 * j, VIOLET,
                R=angles(-25, 0, 0), **GLOW)
    # A ruff of soft fur on the chest.
    for j in range(7):
        x = -1.05 + j * 0.35
        a.wedge(f"ChestRuff{j}", (0.45, 0.9, 0.3), (x, 4.7 - 0.15 * (j % 2), -2.95), FUR2 if j % 2 else FUR,
                rot=(0, 90, 180), role="Secondary")

    # -- head ----------------------------------------------------------------------------------
    with a.bone("Head", "Body", (0, 6.6, -2.6)):
        a.post("Neck", (2.0, 2.0, 1.8), (0, 6.8, -2.8), FUR, b=0.5)
        a.oct("Head", (3.4, 2.8, 2.8), (0, 8.4, -3.7), FUR, b=0.8)
        a.oct("Muzzle", (1.7, 1.0, 0.7), (0, 7.55, -5.3), FUR2, b=0.3, role="Secondary")
        a.box("Chin", (1.0, 0.35, 0.5), (0, 7.0, -5.1), FUR2, role="Secondary")
        a.bevel("Nose", (0.55, 0.35, 0.25), (0, 7.95, -5.7), PINK, b=0.1, **DETAIL)
        a.box("NoseShine", (0.15, 0.08, 0.05), (-0.12, 8.06, -5.84), WHITE, **DETAIL)
        a.box("MouthLine", (0.08, 0.35, 0.06), (0, 7.62, -5.67), SLIT, **DETAIL)
        for s, S in SIDES:
            a.box(f"Mouth{S}", (0.4, 0.08, 0.06), (0.18 * s, 7.44, -5.67), SLIT, rot=(0, 0, -20 * s), **DETAIL)
            # Big pink eyes with slit pupils and a glowing rim of lilac lid above them.
            e = (0.82 * s, 8.5, -5.12)
            a.box(f"Eye{S}", (1.0, 1.2, 0.12), e, PINK, material="Neon", role="Eye", shadow=False, studs=False)
            a.box(f"Eye{S}Slit", (0.2, 0.95, 0.14), add(e, (0.05 * s, -0.02, -0.03)), SLIT, **DETAIL)
            a.box(f"Eye{S}Shine", (0.24, 0.24, 0.16), add(e, (-0.22 * s, 0.3, -0.05)), WHITE, **DETAIL)
            a.box(f"Eye{S}Glint", (0.12, 0.12, 0.16), add(e, (0.24 * s, -0.32, -0.05)), WHITE, **DETAIL)
            a.box(f"Eye{S}Lid", (1.15, 0.3, 0.2), add(e, (0, 0.62, -0.02)), FUR3, rot=(0, 0, -12 * s), **DETAIL)
            a.box(f"Eye{S}Liner", (0.5, 0.1, 0.1), add(e, (0.6 * s, 0.38, -0.04)), LILAC, rot=(0, 0, 25 * s), **GLOW)
            # Whiskers.
            for j in range(3):
                a.rod(f"Whisker{S}{j}", (0.75 * s, 7.65 - 0.15 * j, -5.55), (2.7 * s, 7.95 - 0.35 * j, -5.2 + 0.15 * j),
                      0.07, LILAC, **GLOW)
            # Cheek fluff.
            for j in range(3):
                a.wedge(f"CheekFluff{S}{j}", (0.3, 0.7, 0.9), (1.75 * s, 8.1 - 0.4 * j, -3.9 + 0.2 * j),
                        FUR2 if j % 2 else FUR, rot=(0, 0, 160 * s), role="Secondary")
            # Tall ears with glowing insides, tufts and a little void ring.
            R = angles(-6, 0, -14 * s)
            base = (1.05 * s, 9.6, -3.5)
            a.tri(f"Ear{S}", base, 1.5, 2.1, 0.5, FUR, R=R)
            a.tri(f"InnerEar{S}", at(base, R, (0, 0.15, -0.28)), 0.9, 1.4, 0.1, VIOLET, R=R, **GLOW)
            a.tri(f"EarTuft{S}", at(base, R, (0, 0.05, -0.36)), 0.5, 0.8, 0.1, LILAC, R=R, **DETAIL)
            a.tri(f"EarTip{S}", at(base, R, (0, 1.75, 0)), 0.42, 0.7, 0.52, FUR3, R=R)
            for j in range(2):
                a.box(f"EarRing{S}{j}", (0.12, 0.35, 0.35), at(base, R, (0.55 * s, 0.6 + 0.4 * j, 0)), VIOLET,
                      R=matmul(R, angles(45, 0, 0)), **GLOW)
        # The rune on the brow: a diamond over an arrow.
        a.box("Rune", (0.42, 0.42, 0.1), (0, 9.45, -5.13), HOTPINK, rot=(0, 0, 45), **GLOW)
        a.box("RuneStem", (0.12, 0.6, 0.1), (0, 8.95, -5.13), HOTPINK, **GLOW)
        for s, S in SIDES:
            a.box(f"RuneArm{S}", (0.12, 0.42, 0.1), (0.15 * s, 8.75, -5.13), HOTPINK, rot=(0, 0, 40 * s), **GLOW)
            a.box(f"RuneDot{S}", (0.16, 0.16, 0.1), (0.55 * s, 9.55, -5.13), PINK, rot=(0, 0, 45), **GLOW)
        # Stars on the head too.
        for j, (x, y) in enumerate(((-1.2, 9.7), (1.3, 9.5), (-0.6, 9.85), (0.9, 9.82))):
            a.box(f"HeadStar{j}", (0.16, 0.06, 0.16), (x, y, -3.4 + 0.3 * j), WHITE, rot=(0, 45, 0), **GLOW)
        # The void collar with a pink gem pendant.
        for j in range(14):
            ang = 2 * math.pi * j / 14
            c, s_ = math.cos(ang), math.sin(ang)
            a.box(f"Collar{j}", (0.36, 0.42, 0.5), (c * 1.15, 6.55, -2.8 + s_ * 1.05), VIOLET if j % 2 else HOTPINK,
                  rot=(0, -math.degrees(ang) + 90, 0), **GLOW)
        a.box("CollarStud0", (0.3, 0.3, 0.12), (0.7, 6.5, -3.75), GEMPINK, rot=(0, 0, 45), **GLOW)
        a.box("CollarStud1", (0.3, 0.3, 0.12), (-0.7, 6.5, -3.75), GEMPINK, rot=(0, 0, 45), **GLOW)
        a.box("PendantRing", (0.3, 0.3, 0.12), (0, 6.2, -3.95), VIOLET, rot=(0, 0, 45), **GLOW)
        gem(a, "CollarGem", (0, 5.55, -4.0), 0.6, 1.0, PINK)
        # A soft ruff of fur behind the collar and tufts on the top of the head.
        for j in range(9):
            ang = math.pi * (0.1 + 0.8 * j / 8)
            c, s_ = math.cos(ang), math.sin(ang)
            a.wedge(f"NeckRuff{j}", (0.5, 0.9, 0.35), (c * 1.2, 6.15, -2.75 + s_ * 1.1), FUR2 if j % 2 else FUR,
                    rot=(0, -math.degrees(ang) - 90, 180), role="Secondary")
        for j in range(3):
            a.wedge(f"HeadTuft{j}", (0.3, 0.5, 0.6), ((j - 1) * 0.35, 9.95, -3.2), FUR3, rot=(0, 0, (j - 1) * 15),
                    role="Secondary")

    # -- legs ----------------------------------------------------------------------------------
    for s, S in SIDES:
        with a.bone(f"LegF{S}", "Body", (0.95 * s, 4.6, -1.8)):
            a.post(f"UpperLegF{S}", (1.0, 2.2, 1.1), (0.95 * s, 3.6, -1.8), FUR, b=0.3)
            a.post(f"LowerLegF{S}", (0.85, 2.2, 0.95), (0.95 * s, 1.6, -1.9), FUR, b=0.25)
            a.paw(f"PawF{S}", (0.95 * s, 0, -2.05), 1.1, 1.3, FUR2, claws=VIOLET, h=0.55)
        with a.bone(f"LegB{S}", "Body", (1.05 * s, 5.0, 2.6)):
            a.oct(f"Thigh{S}", (1.2, 2.6, 2.2), (1.05 * s, 4.6, 2.7), FUR, b=0.4)
            a.post(f"LowerLegB{S}", (0.85, 2.6, 0.95), (1.05 * s, 1.7, 3.0), FUR, b=0.25)
            a.paw(f"PawB{S}", (1.05 * s, 0, 2.85), 1.1, 1.3, FUR2, claws=VIOLET, h=0.55)
            for j in range(2):
                a.box(f"ShinStar{S}{j}", (0.06, 0.16, 0.16), (1.49 * s, 1.4 + 0.9 * j, 3.0 - 0.1 * j), GEMPINK,
                      rot=(45, 0, 0), **GLOW)
            for j in range(3):
                a.box(f"ThighStar{S}{j}", (0.06, 0.2, 0.2), (1.66 * s, 4.2 + 0.5 * j, 2.3 + 0.45 * j), WHITE,
                      rot=(45, 0, 0), **GLOW)
    for F, z, x in (("F", -1.9, 0.95), ("B", 3.0, 1.05)):
        for s, S in SIDES:
            with in_bone(a, f"Leg{F}{S}"):
                for q in range(4):
                    ang = q * math.pi / 2 + math.pi / 4
                    a.box(f"Anklet{F}{S}{q}", (0.42, 0.16, 0.16),
                          (x * s + math.cos(ang) * 0.52, 0.95, z + math.sin(ang) * 0.52), VIOLET if q % 2 else HOTPINK,
                          rot=(0, -math.degrees(ang) + 90, 0), **GLOW)
                for j in range(2):
                    a.wedge(f"LegFluff{F}{S}{j}", (0.18, 0.6, 0.5), (x * s + (0.38 if j else -0.38), 2.4, z + 0.45),
                            FUR2, rot=(0, 0, 180), role="Secondary")

    # -- tail: an S that curls up high, with a crystal at the tip --------------------------------
    pts = [(0, 6.0, 3.6), (0, 6.5, 5.0), (0, 7.9, 5.8), (0, 9.6, 5.7), (0, 10.9, 5.1), (0, 11.7, 4.4)]
    with a.bone("Tail", "Body", pts[0]):
        chain(a, "Tail", pts, [0.8, 0.72, 0.66, 0.6, 0.54], FUR)
        for j in (1, 2, 3, 4):
            d = unit(sub(pts[j + 1], pts[j - 1]))
            a.box(f"TailRing{j}", (0.85 - 0.06 * j, 0.85 - 0.06 * j, 0.2), pts[j], VIOLET if j % 2 else HOTPINK,
                  R=matmul(angles(0, 0, 0), _aim(d)), **GLOW)
        for j in range(1, 5):
            for sx in (-1, 1):
                p0 = pts[j]
                d = unit(sub(pts[j + 1], pts[j]))
                plate(a, f"TailFur{j}{'R' if sx > 0 else 'L'}", p0, add(p0, add(scale(d, 0.7), (0.35 * sx, 0, 0))),
                      0.3, 0.08, FUR2, up=(sx, 0, 0), role="Secondary", shadow=False)
        for j in range(6):
            t = (j + 0.5) / 6 * (len(pts) - 1)
            i = min(int(t), len(pts) - 2)
            p = _lerp(pts[i], pts[i + 1], t - i)
            a.box(f"TailStar{j}", (0.12, 0.12, 0.12), add(p, (0.3 if j % 2 else -0.3, 0, 0)), WHITE, rot=(45, 45, 0),
                  **GLOW)
        a.box("TailCap", (0.55, 0.5, 0.55), (0, 12.0, 4.25), VIOLET, rot=(0, 45, 0), **GLOW)
        gem(a, "TailCrystal", (0, 12.75, 4.15), 0.9, 1.6, VIOLET)
        for j in range(3):
            ang = j * 2 * math.pi / 3
            a.shard(f"TailShard{j}", (math.cos(ang) * 0.35, 12.2, 4.2 + math.sin(ang) * 0.35), 0.22, 0.7, LILAC,
                    R=angles(math.sin(ang) * 30, 0, -math.cos(ang) * 30), **GLOW)
    a.bones["TailTip"] = {"parent": "Tail", "pivot": pts[3]}
    for part in a.parts:
        if part["bone"] == "Tail" and part["p"][1] > pts[3][1] - 0.2:
            part["bone"] = "TailTip"

    # -- orbit: two pink diamonds floating beside it, star shards and a void ring on the ground ---------------
    with a.bone("Orbit", "Body", (0, 5.3, 0.6)):
        for i, S in enumerate("RL"):
            ang = math.pi * i
            p = (math.cos(ang) * 3.6, 8.3, 0.6 + math.sin(ang) * 3.6)
            gem(a, f"FloatGem{S}", p, 0.9, 1.7, PINK)
            for j in range(4):
                q = j * math.pi / 2
                a.box(f"FloatGem{S}Halo{j}", (0.7, 0.08, 0.08), add(p, (math.cos(q) * 0.85, 0, math.sin(q) * 0.85)),
                      LILAC, rot=(0, -math.degrees(q) + 90, 0), **GLOW_T)
        for i in range(6):
            ang = 2 * math.pi * (i + 0.5) / 6
            p = (math.cos(ang) * 5.2, 6.8 + 0.9 * math.sin(ang * 3), 0.6 + math.sin(ang) * 5.2)
            a.shard(f"StarShard{i}", p, 0.3, 0.8, LILAC if i % 2 else GEMPINK, R=angles(30, -math.degrees(ang), 20),
                    **GLOW)
        ground_ring(a, "VoidRing", (0, 0.06, 0.6), 5.6, VIOLET, n=20, size=(0.4, 0.1, 1.4), transparency=0.3)
        for k in range(6):
            ang = k * math.pi / 3
            a.box(f"RuneRing{k}", (0.3, 0.08, 0.3), (math.cos(ang) * 4.6, 0.08, 0.6 + math.sin(ang) * 4.6), HOTPINK,
                  rot=(0, 45, 0), **GLOW)
        a.box("SigilCore", (0.4, 0.2, 0.4), (0, 0.2, 0.6), VIOLET, transparency=1, **DETAIL)

    a.ride_height, a.ride_z = 6.9, 0.6
    unfight(a, "Belly", "Chest")

    # -- effects -------------------------------------------------------------------------------
    p = lambda n: find(a, n)["p"]
    fx(a, "Body",
       light("VoidLight", VIOLET, brightness=1.6, range_=16, pulse=1.6),
       grad(emitter("VoidAura", VIOLET, texture=GLOW_TEXTURE, rate=1.5, lifetime=(1.4, 1.8), speed=(0, 0),
                    sizes=((0, 7), (0.5, 9), (1, 7)), transparency=((0, 1), (0.4, 0.8), (1, 1)), lock=True),
            (0, HOTPINK), (1, VIOLET)),
       grad(emitter("Stardust", WHITE, texture=SPARKLE_TEXTURE, rate=10, lifetime=(1.5, 2.5), speed=(0.3, 1.2),
                    sizes=((0, 0), (0.3, 0.45), (1, 0)), transparency=((0, 0), (1, 0.3)), accel=(0, 0.8, 0),
                    rot_speed=(-120, 120)), (0, WHITE), (0.5, GEMPINK), (1, VIOLET)),
       emitter("ShadowWisps", C("#2a1640"), texture=SMOKE_TEXTURE, rate=4, lifetime=(1.2, 1.8), speed=(0.2, 0.6),
               sizes=((0, 1.5), (1, 3)), transparency=((0, 0.55), (1, 1)), light=0, accel=(0, 0.6, 0)))
    for s, S in SIDES:
        fx(a, f"Eye{S}", light(f"EyeLight{S}", PINK, brightness=0.8, range_=5, pulse=1.3))
    fx(a, "Rune",
       light("RuneLight", HOTPINK, brightness=1.0, range_=7, pulse=1.1),
       emitter("RuneSparks", PINK, texture=SPARKLE_TEXTURE, rate=4, lifetime=(0.6, 1.0), speed=(0.5, 1.2),
               sizes=((0, 0.35), (1, 0)), spread=40, color2=VIOLET))
    fx(a, "CollarGemUp",
       light("GemLight", PINK, brightness=1.2, range_=8, pulse=0.9),
       glint("GemGlint", GEMPINK, rate=1.2, size=1.4))
    # The floating diamonds: tethered to the collar gem by curling beams of light, trailing pink light.
    k = 1.0
    for i, S in enumerate("RL"):
        gp = p(f"FloatGem{S}Up")
        fx(a, f"FloatGem{S}Up",
           light(f"FloatLight{S}", PINK, brightness=1.0, range_=9, pulse=1.2),
           glint(f"FloatGlint{S}", GEMPINK, rate=1.0, size=1.6),
           grad(emitter(f"FloatGlow{S}", PINK, texture=GLOW_TEXTURE, rate=2, lifetime=(0.8, 1.0), speed=(0, 0),
                        sizes=((0, 2.2), (0.5, 3), (1, 2.2)), transparency=((0, 1), (0.5, 0.45), (1, 1)), lock=True),
                (0, GEMPINK), (1, HOTPINK)),
           emitter(f"FloatDust{S}", GEMPINK, texture=SPARKLE_TEXTURE, rate=6, lifetime=(0.8, 1.4), speed=(0.2, 0.8),
                   sizes=((0, 0.3), (1, 0)), accel=(0, -1.5, 0), color2=VIOLET))
        beam(a, "CollarGemDown", p("CollarGemDown"), f"FloatGem{S}Down", p(f"FloatGem{S}Down"), HOTPINK,
             name=f"Tether{S}", width=(0.1, 0.35), curve=(2.0 * (1 if i else -1), -1.5), segments=16,
             transparency=((0, 0.6), (0.5, 0.2), (1, 0.5)), color2=VIOLET, texture=SPARKLE_TEXTURE, texture_speed=2)
        trail(a, f"FloatGem{S}Up", add(gp, (0, 0.6, 0)), add(gp, (0, -0.8, 0)), PINK, name=f"GemTrail{S}",
              lifetime=0.9, color2=VIOLET, transparency=((0, 0.2), (1, 1)), width=0)
    # The tail crystal: a small spinning void disc, a glow and falling sparkles.
    fx(a, "TailCrystalUp",
       light("TailLight", VIOLET, brightness=1.4, range_=10, pulse=1.0),
       grad(emitter("TailVortex", VIOLET, texture=VORTEX_TEXTURE, rate=1.2, lifetime=(2, 2), speed=(0, 0),
                    sizes=((0, 3), (0.5, 3.6), (1, 3)), transparency=((0, 1), (0.3, 0.45), (0.7, 0.45), (1, 1)),
                    lock=True, rot_speed=(120, 160)), (0, LILAC), (1, HOTPINK)),
       glint("TailGlint", LILAC, rate=1.5, size=1.8),
       emitter("TailDust", LILAC, texture=SPARKLE_TEXTURE, rate=8, lifetime=(1.0, 1.6), speed=(0.5, 1.5),
               sizes=((0, 0.35), (1, 0)), accel=(0, -2, 0), color2=HOTPINK))
    tp = p("TailCrystalUp")
    trail(a, "TailCrystalUp", add(tp, (0.5, 0, 0)), add(tp, (-0.5, 0, 0)), LILAC, name="TailTrail", lifetime=0.7,
          color2=HOTPINK, transparency=((0, 0.2), (1, 1)), width=0)
    # A void sigil turning on the ground, and star shards trailing light as they orbit.
    fx(a, "SigilCore",
       flat(grad(emitter("Sigil", VIOLET, texture=VORTEX_TEXTURE, rate=0.6, lifetime=(3, 3), speed=(0.01, 0.01),
                         spread=0, sizes=((0, 12), (1, 12)), transparency=((0, 1), (0.25, 0.5), (0.75, 0.5), (1, 1)),
                         lock=True, rot_speed=(-35, -35)), (0, HOTPINK), (1, VIOLET))),
       flat(grad(emitter("SigilGlow", VIOLET, texture=GLOW_TEXTURE, rate=0.8, lifetime=(2, 2), speed=(0.01, 0.01),
                         spread=0, sizes=((0, 13), (1, 13)), transparency=((0, 1), (0.5, 0.75), (1, 1)), lock=True),
                 (0, PINK), (1, VIOLET))),
       emitter("RisingStars", WHITE, texture=SPARKLE_TEXTURE, rate=5, lifetime=(1.5, 2.2), speed=(1.5, 3),
               sizes=((0, 0.4), (1, 0)), spread=60, color2=LILAC))
    for i in (0, 3):
        sp = p(f"StarShard{i}")
        trail(a, f"StarShard{i}", add(sp, (0, 0.4, 0)), add(sp, (0, -0.3, 0)), LILAC, name=f"ShardTrail{i}",
              lifetime=0.6, color2=VIOLET, width=0)
    pulse(a, "Rune", "RuneStem", "RuneArmR", "RuneArmL", "EyeR", "EyeL", seconds=1.3)
    pulse(a, *[f"Star{S}{j}" for S in "RL" for j in range(0, 6, 2)], seconds=0.9)
    pulse(a, *[f"Nebula{S}{j}" for S in "RL" for j in range(5)], seconds=2.4)
    extras(a, attrs={"WalkSpeed": 12, "OrbitSpeed": 0.9, "TailSway": 10}, highlight=(VIOLET, HOTPINK, 1.0, 0.5))
    return a


def _lerp(p, q, t):
    return tuple(a + (b - a) * t for a, b in zip(p, q))


def _aim(d):
    """Rotation whose local Z runs along d (a ring around a rod)."""
    from lib import aim
    R = aim(d)
    return matmul(R, angles(0, 90, 0))


# ================================================================================== Gorilla King ===

GFUR, GFUR2, GFUR3 = C("#26242c"), C("#34313b"), C("#1a191f")
SILVER, SILVER2 = C("#c3c7d1"), C("#9aa0ad")
SKIN, SKIN2 = C("#5d5a68"), C("#4a4755")
GOLD, GOLD2, GOLDHOT = C("#ffc93c"), C("#e0a01f"), C("#fff1a8")
RUBY, DIAMOND, AMBER_EYE = C("#e0103a"), C("#dff8ff"), C("#ff9a1a")
ERMINE, VELVET = C("#f4f1ea"), C("#8a0f2a")
GOLD_KW = dict(role="Accent", reflectance=0.3, material="SmoothPlastic", studs=False)


def gold_ring(a, name, center, radius, n, size, color=GOLD, axis="y", **kw):
    kw = kw or GOLD_KW
    for i in range(n):
        ang = 2 * math.pi * i / n
        c, s_ = math.cos(ang), math.sin(ang)
        if axis == "y":
            pos = add(center, (c * radius, 0, s_ * radius))
            R = angles(0, -math.degrees(ang) + 90, 0)
        else:  # ring in the x-y plane (an earring)
            pos = add(center, (0, s_ * radius, c * radius))
            R = angles(math.degrees(ang) + 90, 0, 0)
        a.box(f"{name}{i}", size, pos, color, R=R, **kw)


def gorilla_king():
    a = Animal("GorillaKing", "Gorilla King", "Secret")
    rng = random.Random(11)

    # -- body: massive shoulders, a silver back, sloping down to the rump ----------------------------
    a.oct("Body", (5.0, 4.4, 5.6), (0, 7.4, 0.6), GFUR, b=1.2)
    a.oct("Shoulders", (6.4, 4.8, 3.2), (0, 8.4, -1.5), GFUR, b=1.5)
    a.oct("Rump", (4.4, 3.4, 2.6), (0, 6.6, 3.1), GFUR, b=1.0)
    a.bevel("SilverBack", (5.1, 2.4, 4.6), (0, 8.5, 1.1), SILVER, b=1.25, role="Secondary")
    a.bevel("SilverRump", (4.5, 1.4, 2.2), (0, 7.65, 3.2), SILVER2, b=0.8, role="Secondary")
    for s, S in SIDES:
        a.bevel(f"Pec{S}", (2.3, 1.9, 0.5), (1.2 * s, 8.6, -3.15), SKIN, b=0.35, role="Secondary")
    for j in range(2):
        for s, S in SIDES:
            a.bevel(f"Abs{S}{j}", (1.1, 0.8, 0.4), (0.6 * s, 7.0 - 0.9 * j, -2.85 + 0.25 * j), SKIN2, b=0.2,
                    role="Secondary")
    a.bevel("Belly", (3.6, 1.0, 4.0), (0, 5.25, 0.4), SKIN2, b=0, bottom=0.5, role="Secondary")
    # Silver fur: strokes over the silver back, and dark fur strokes on the flanks.
    for r in range(4):
        for c in range(5):
            x = -1.6 + c * 0.8 + (0.4 if r % 2 else 0)
            if abs(x) > 2.0:
                continue
            p0 = (x, 9.72, -0.6 + r * 1.0)
            plate(a, f"SilverStroke{r}_{c}", p0, add(p0, (0, -0.02, 0.8)), 0.22, 0.06, WHITE if (r + c) % 2 else SILVER2,
                  role="Secondary", shadow=False)
    for s, S in SIDES:
        for r, y in enumerate((8.6, 7.5)):
            for j, z in enumerate((-0.4, 0.8, 2.0)):
                p0 = (2.57 * s, y, z)
                plate(a, f"SilverSide{S}{r}_{j}", p0, add(p0, (0.02 * s, -0.5, 0.7)), 0.2, 0.06, WHITE,
                      up=(s, 0, 0), role="Secondary", shadow=False)
        for r, y in enumerate((6.5, 5.7)):
            for j, z in enumerate((-0.6, 0.6, 1.8, 3.0)):
                p0 = (2.52 * s if z < 2.4 else 2.22 * s, y, z)
                plate(a, f"FurStroke{S}{r}_{j}", p0, add(p0, (0.03 * s, -0.55, 0.6)), 0.24, 0.07, GFUR3,
                      up=(s, 0, 0), role="Secondary", shadow=False)
        for j in range(5):
            a.wedge(f"BellyShag{S}{j}", (0.35, 0.8, 0.9), (2.05 * s, 5.05, -1.2 + j * 1.0), GFUR3, rot=(0, 0, 180),
                    role="Secondary")
        # Shaggy fur hanging off the shoulders.
        for j in range(4):
            a.wedge(f"ShoulderShag{S}{j}", (0.4, 1.1, 0.8), (3.2 * s, 7.5, -2.6 + j * 0.75), GFUR2 if j % 2 else GFUR,
                    rot=(0, 0, 180), role="Secondary")
    for j in range(5):
        a.wedge(f"RumpShag{j}", (0.8, 0.9, 0.4), (-1.6 + j * 0.8, 5.6, 4.45), GFUR3, rot=(0, 90, 180),
                role="Secondary")

    # -- the royal bling on the body: ermine collar, gold epaulettes, the chain and the medallion ----
    for j in range(14):
        ang = math.pi * (-0.12 + 1.24 * j / 13)
        c, s_ = math.cos(ang), math.sin(ang)
        pos = (c * 2.25, 10.85, -3.1 + s_ * 1.5)
        R = angles(0, -math.degrees(ang) + 90, 0)
        a.bevel(f"Ermine{j}", (0.95, 0.8, 1.1), pos, ERMINE, b=0.3, R=R, role="Secondary")
        if j % 2 == 0:
            a.box(f"ErmineSpot{j}", (0.18, 0.32, 0.1), at(pos, R, (0, 0.05, 0.56)), GFUR3, R=R, **DETAIL)
            a.box(f"ErmineSpotTop{j}", (0.18, 0.1, 0.3), at(pos, R, (0.15, 0.41, 0)), GFUR3, R=R, **DETAIL)
    for s, S in SIDES:
        ep = (3.05 * s, 10.15, -1.5)
        a.cyl(f"Epaulette{S}", 0.35, 2.0, ep, GOLD, R=angles(0, 0, 90), **GOLD_KW)
        a.cyl(f"EpauletteTop{S}", 0.3, 1.2, add(ep, (0, 0.25, 0)), GOLD2, R=angles(0, 0, 90), **GOLD_KW)
        a.box(f"EpauletteGem{S}", (0.4, 0.15, 0.4), add(ep, (0, 0.45, 0)), RUBY, rot=(0, 45, 0), **GLOW)
        for j in range(7):
            q = (ep[0] + s * 0.95 * math.sin(math.pi * j / 6), ep[1] - 0.55, ep[2] - 0.95 * math.cos(math.pi * j / 6))
            a.box(f"Fringe{S}{j}", (0.12, 0.7, 0.12), q, GOLDHOT, **DETAIL)
    # The chain: two strands of links over the chest, meeting at the medallion.
    for s, S in SIDES:
        path = [(1.95 * s, 10.0, -2.8), (1.5 * s, 9.3, -3.42), (1.0 * s, 8.4, -3.5), (0.5 * s, 7.6, -3.55),
                (0.12 * s, 7.15, -3.6)]
        n = 11
        for i in range(n):
            t = i / (n - 1) * (len(path) - 1)
            k = min(int(t), len(path) - 2)
            pt = _lerp(path[k], path[k + 1], t - k)
            d = unit(sub(path[k + 1], path[k]))
            size = (0.5, 0.36, 0.14) if i % 2 == 0 else (0.5, 0.14, 0.36)
            a.box(f"Chain{S}{i}", size, pt, GOLD, R=_aim_x(d), **GOLD_KW)
    a.bevel("Medallion", (1.8, 2.0, 0.35), (0, 6.35, -3.72), GOLD, b=0.3, **GOLD_KW)
    a.box("MedallionRim", (1.4, 1.6, 0.36), (0, 6.35, -3.76), GOLD2, **GOLD_KW)
    a.box("MedallionBail", (0.5, 0.5, 0.2), (0, 7.45, -3.66), GOLD, rot=(0, 0, 45), **GOLD_KW)
    a.box("MedallionDiamond", (0.95, 0.95, 0.3), (0, 6.3, -3.95), DIAMOND, rot=(0, 0, 45), **GLASS)
    a.box("MedallionDiamondCore", (0.5, 0.5, 0.3), (0, 6.3, -3.98), WHITE, rot=(0, 0, 45), **GLOW)
    for j in range(4):
        ang = j * math.pi / 2 + math.pi / 4
        a.box(f"MedallionStone{j}", (0.22, 0.22, 0.12), (math.cos(ang) * 0.68, 6.35 + math.sin(ang) * 0.78, -3.94),
              RUBY if j % 2 else DIAMOND, rot=(0, 0, 45), **GLOW)
    for j in range(3):
        a.wedge(f"MedallionCrown{j}", (0.12, 0.35 + 0.15 * (j == 1), 0.3), ((j - 1) * 0.45, 7.45 + 0.08 * (j == 1),
                                                                            -3.75), GOLD, rot=(0, 90, 0), **GOLD_KW)

    # -- head ----------------------------------------------------------------------------------
    with a.bone("Head", "Body", (0, 9.2, -2.8)):
        a.oct("Head", (3.0, 3.0, 2.8), (0, 10.0, -3.9), GFUR, b=0.8)
        a.wedge("Crest", (1.4, 0.8, 2.0), (0, 11.7, -3.4), GFUR, rot=(0, 180, 0))
        a.bevel("Face", (2.4, 2.0, 0.4), (0, 9.8, -5.35), SKIN, b=0.4, role="Secondary")
        a.bevel("Brow", (2.9, 0.6, 0.9), (0, 10.7, -5.45), GFUR2, b=0.2)
        a.oct("Muzzle", (2.6, 1.6, 1.2), (0, 9.0, -5.65), SKIN, b=0.45, role="Secondary")
        a.box("NoseBridge", (0.9, 0.7, 0.4), (0, 9.75, -5.85), SKIN2, **DETAIL)
        for s, S in SIDES:
            a.box(f"Nostril{S}", (0.32, 0.22, 0.12), (0.3 * s, 9.55, -6.27), GFUR3, **DETAIL)
            # Small fierce orange eyes deep under the brow.
            e = (0.62 * s, 10.15, -5.6)
            a.box(f"Eye{S}", (0.6, 0.45, 0.1), e, AMBER_EYE, material="Neon", role="Eye", shadow=False, studs=False)
            a.box(f"Eye{S}Pupil", (0.22, 0.32, 0.12), add(e, (-0.04 * s, -0.02, -0.02)), GFUR3, **DETAIL)
            a.box(f"Eye{S}Shine", (0.1, 0.1, 0.13), add(e, (0.14 * s, 0.1, -0.03)), WHITE, **DETAIL)
            a.box(f"BrowAngle{S}", (1.2, 0.25, 0.2), (0.7 * s, 10.45, -5.95), GFUR3, rot=(0, 0, -14 * s), **DETAIL)
            # Ears, a gold hoop in the right one and a diamond stud in the left.
            a.oct(f"Ear{S}", (0.45, 0.9, 0.7), (1.6 * s, 10.0, -3.8), SKIN, b=0.15)
            for j in range(3):
                a.wedge(f"CheekFur{S}{j}", (0.35, 0.9, 1.0), (1.55 * s, 9.2 - 0.3 * j, -4.4 + 0.5 * j), GFUR2,
                        rot=(0, 0, 160 * s), role="Secondary")
        gold_ring(a, "Earring", (1.9, 9.25, -3.8), 0.42, 8, (0.12, 0.14, 0.36), axis="x")
        a.box("EarringGem", (0.3, 0.3, 0.3), (1.9, 8.75, -3.8), DIAMOND, rot=(45, 0, 45), **GLOW)
        a.box("EarStud", (0.25, 0.25, 0.25), (-1.86, 9.9, -3.8), DIAMOND, rot=(45, 0, 45), **GLOW)
        # The mouth with gold grills and diamond teeth.
        a.box("Mouth", (1.9, 0.6, 0.2), (0, 8.7, -6.2), GFUR3, **DETAIL)
        for j in range(6):
            x = -0.75 + j * 0.3
            dia = j in (1, 4)
            a.box(f"GrillTop{j}", (0.27, 0.3, 0.14), (x, 8.86, -6.3), DIAMOND if dia else GOLD,
                  **(GLOW if dia else GOLD_KW))
            a.box(f"GrillLow{j}", (0.27, 0.24, 0.14), (x, 8.52, -6.3), DIAMOND if j in (2, 3) else GOLD,
                  **(GLOW if j in (2, 3) else GOLD_KW))
        for s, S in SIDES:
            a.tooth(f"Fang{S}", (0.85 * s, 8.98, -6.32), 0.22, 0.4, color=GOLDHOT)
        a.box("Lip", (2.0, 0.2, 0.3), (0, 8.33, -6.15), SKIN2, **DETAIL)

    # -- the crown (its own joint, so it can lift and spin) -----------------------------------------
    cc = (0, 11.95, -3.9)
    with a.bone("Crown", "Head", (0, 11.5, -3.9)):
        a.box("CrownCap", (2.4, 0.7, 2.4), add(cc, (0, 0.15, 0)), VELVET, role="Secondary")
        gold_ring(a, "CrownBand", cc, 1.5, 12, (0.82, 0.8, 0.25))
        gold_ring(a, "CrownRimLow", add(cc, (0, -0.42, 0)), 1.56, 12, (0.85, 0.16, 0.2), color=GOLD2)
        gold_ring(a, "CrownRimTop", add(cc, (0, 0.42, 0)), 1.56, 12, (0.85, 0.16, 0.2), color=GOLD2)
        for i in range(8):
            ang = 2 * math.pi * i / 8 - math.pi / 2
            c, s_ = math.cos(ang), math.sin(ang)
            h = 1.5 if i % 2 == 0 else 1.05
            base = add(cc, (c * 1.5, 0.45, s_ * 1.5))
            a.tri(f"CrownPoint{i}", base, 0.75, h, 0.2, GOLD, R=angles(0, -math.degrees(ang) - 90, 0), **GOLD_KW)
            a.ball(f"CrownPearl{i}", 0.3, add(base, (0, h + 0.1, 0)), GOLDHOT if i % 2 else WHITE, **GOLD_KW)
            stone = add(cc, (c * 1.66, 0, s_ * 1.66))
            a.box(f"CrownRuby{i}", (0.35, 0.35, 0.12), stone, RUBY if i % 2 == 0 else DIAMOND,
                  R=matmul(angles(0, -math.degrees(ang) - 90, 0), angles(0, 0, 45)), **GLOW)
            if i % 2 == 0:
                a.box(f"CrownPointGem{i}", (0.22, 0.22, 0.1), add(cc, (c * 1.64, 0.95, s_ * 1.64)), DIAMOND,
                      R=matmul(angles(0, -math.degrees(ang) - 90, 0), angles(0, 0, 45)), **GLOW)
        # Arches over the cap and an orb with a cross on top.
        for j in range(2):
            ang = j * 90
            R = angles(0, ang, 0)
            for q in range(5):
                t = (q + 0.5) / 5 * math.pi
                pt = add(cc, apply(R, (math.cos(t) * 1.3, 0.5 + math.sin(t) * 0.9, 0)))
                a.box(f"CrownArch{j}_{q}", (0.18, 0.55, 0.18), pt, GOLD,
                      R=matmul(R, angles(0, 0, math.degrees(t) - 90)), **GOLD_KW)
        a.ball("CrownOrb", 0.55, add(cc, (0, 1.6, 0)), GOLD, **GOLD_KW)
        a.box("CrownCross", (0.14, 0.7, 0.14), add(cc, (0, 2.1, 0)), GOLD, **GOLD_KW)
        a.box("CrownCrossBar", (0.45, 0.14, 0.14), add(cc, (0, 2.2, 0)), GOLD, **GOLD_KW)
        a.box("CrownJewel", (0.6, 0.6, 0.2), add(cc, (0, 0, -1.68)), RUBY, rot=(0, 0, 45), **GLOW)

    # -- arms (the front legs of a knuckle walker), with an elbow joint for the chest beat ----------------
    for s, S in SIDES:
        with a.bone(f"LegF{S}", "Body", (2.8 * s, 8.8, -1.8)):
            a.oct(f"ShoulderBall{S}", (2.0, 2.0, 2.2), (3.0 * s, 8.6, -1.8), GFUR, b=0.6)
            a.post(f"UpperArm{S}", (1.8, 3.8, 1.9), (3.05 * s, 6.9, -2.0), GFUR, b=0.5)
            for j in range(3):
                a.wedge(f"ArmShag{S}{j}", (0.3, 1.0, 0.7), (3.95 * s, 6.6 - 0.2 * j, -2.4 + 0.5 * j), GFUR2,
                        rot=(0, 0, 180), role="Secondary")
        with a.bone(f"Forearm{S}", f"LegF{S}", (3.05 * s, 5.1, -2.0)):
            a.post(f"Forearm{S}", (2.1, 3.6, 2.1), (3.05 * s, 3.25, -2.2), GFUR2, b=0.55)
            a.wedge(f"ElbowShag{S}", (0.9, 1.0, 0.5), (3.05 * s, 4.7, -1.0), GFUR2, rot=(0, 0, 180), role="Secondary")
            for j in range(3):
                a.wedge(f"ForearmShag{S}{j}", (0.3, 0.9, 0.7), (4.15 * s, 3.8 - 0.4 * j, -2.6 + 0.5 * j), GFUR3,
                        rot=(0, 0, 180), role="Secondary")
            # The gold bracelet with diamonds round the wrist.
            gold_ring(a, f"Bracelet{S}", (3.05 * s, 1.95, -2.2), 1.18, 10, (0.78, 0.5, 0.22))
            gold_ring(a, f"BraceletRim{S}", (3.05 * s, 2.25, -2.2), 1.22, 10, (0.8, 0.1, 0.2), color=GOLD2)
            for j in range(5):
                ang = 2 * math.pi * j / 5 - math.pi / 2
                a.box(f"BraceletDiamond{S}{j}", (0.3, 0.3, 0.12),
                      (3.05 * s + math.cos(ang) * 1.32, 1.95, -2.2 + math.sin(ang) * 1.32), DIAMOND,
                      R=matmul(angles(0, -math.degrees(ang) - 90, 0), angles(0, 0, 45)), **GLOW)
            # The fist, knuckles on the ground, with gold rings.
            a.bevel(f"Fist{S}", (2.1, 1.4, 1.9), (3.05 * s, 0.7, -2.35), SKIN, b=0.35)
            for j in range(4):
                x = 3.05 * s + (j - 1.5) * 0.48
                a.bevel(f"Knuckle{S}{j}", (0.42, 0.55, 0.5), (x, 0.32, -3.4), SKIN2, b=0.12)
                if j < 3:
                    a.box(f"FingerLine{S}{j}", (0.08, 0.5, 0.06), (x + 0.24, 0.85, -3.32), GFUR3, **DETAIL)
            for j in (1, 2):
                x = 3.05 * s + (j - 1.5) * 0.48
                a.box(f"FingerRing{S}{j}", (0.46, 0.22, 0.56), (x, 0.65, -3.42), GOLD, **GOLD_KW)
                a.box(f"FingerRingGem{S}{j}", (0.18, 0.18, 0.1), (x, 0.65, -3.72), RUBY if j == 1 else DIAMOND,
                      rot=(0, 0, 45), **GLOW)
            a.bevel(f"Thumb{S}", (0.5, 0.6, 0.9), (3.05 * s - 1.15 * s, 0.9, -2.9), SKIN2, b=0.15)

    # -- legs ----------------------------------------------------------------------------------
    for s, S in SIDES:
        with a.bone(f"LegB{S}", "Body", (1.7 * s, 6.4, 2.6)):
            a.oct(f"Thigh{S}", (1.9, 3.0, 2.4), (1.85 * s, 5.0, 2.8), GFUR, b=0.6)
            a.post(f"Shin{S}", (1.4, 2.6, 1.5), (1.85 * s, 2.4, 3.0), GFUR, b=0.4)
            a.bevel(f"Foot{S}", (1.7, 0.9, 2.5), (1.85 * s, 0.45, 2.6), SKIN, b=0.3)
            for j in range(4):
                x = 1.85 * s + (j - 1.5) * 0.4
                a.bevel(f"Toe{S}{j}", (0.36, 0.5, 0.4), (x, 0.25, 1.2), SKIN2, b=0.1)
            a.bevel(f"BigToe{S}", (0.5, 0.5, 0.7), (1.85 * s - 1.0 * s, 0.25, 1.9), SKIN2, b=0.12)
            gold_ring(a, f"Anklet{S}", (1.85 * s, 1.25, 3.0), 0.85, 8, (0.6, 0.3, 0.18))
            for j in range(3):
                a.wedge(f"ThighShag{S}{j}", (0.3, 0.9, 0.8), (2.85 * s, 4.6 - 0.3 * j, 2.2 + 0.6 * j), GFUR3,
                        rot=(0, 0, 180), role="Secondary")

    # -- orbit: gold coins and diamonds circling it, a gold ring and a crown sigil on the ground ---------
    with a.bone("Orbit", "Body", (0, 7.4, 0.6)):
        for i in range(8):
            ang = 2 * math.pi * i / 8
            pos = (math.cos(ang) * 7.2, 8.0 + 1.0 * math.sin(ang * 2), 0.6 + math.sin(ang) * 7.2)
            R = angles(20 * math.sin(ang * 3), -math.degrees(ang), 0)
            a.cyl(f"Coin{i}", 0.18, 1.1, pos, GOLD, R=R, **GOLD_KW)
            a.cyl(f"CoinFace{i}", 0.2, 0.7, pos, GOLD2, R=R, **GOLD_KW)
            a.box(f"CoinMark{i}", (0.22, 0.35, 0.12), pos, GOLDHOT, R=matmul(R, angles(0, 90, 0)), **DETAIL)
        for i in range(4):
            ang = 2 * math.pi * (i + 0.5) / 4
            pos = (math.cos(ang) * 6.0, 10.2, 0.6 + math.sin(ang) * 6.0)
            gem(a, f"OrbitDiamond{i}", pos, 0.6, 1.2, DIAMOND)
        ground_ring(a, "GoldRing", (0, 0.06, 0.6), 7.2, GOLD, n=24, size=(0.5, 0.1, 1.6), transparency=0.2)
        for i in range(8):
            ang = 2 * math.pi * i / 8
            c, s_ = math.cos(ang), math.sin(ang)
            a.wedge(f"SigilPoint{i}", (0.1, 0.9 if i % 2 else 1.4, 0.9), (c * 5.6, 0.08, 0.6 + s_ * 5.6), GOLDHOT,
                    R=matmul(angles(0, -math.degrees(ang) - 90, 0), angles(-90, 0, 0)), **dict(GLOW, transparency=0.3))
        a.box("SigilCore", (0.4, 0.2, 0.4), (0, 0.2, 0.6), GOLD, transparency=1, **DETAIL)

    a.ride_height, a.ride_z = 9.9, 0.8
    unfight(a, "SilverBack", "SilverRump", "Belly")

    # -- effects -------------------------------------------------------------------------------
    p = lambda n: find(a, n)["p"]
    fx(a, "Body",
       light("RoyalLight", GOLD, brightness=1.6, range_=20, pulse=2.0),
       grad(emitter("RoyalAura", GOLD, texture=GLOW_TEXTURE, rate=1.5, lifetime=(1.4, 1.8), speed=(0, 0),
                    sizes=((0, 10), (0.5, 13), (1, 10)), transparency=((0, 1), (0.4, 0.85), (1, 1)), lock=True),
            (0, GOLDHOT), (1, GOLD2)),
       grad(emitter("GoldDust", GOLDHOT, texture=SPARKLE_TEXTURE, rate=10, lifetime=(1.5, 2.5), speed=(0.5, 1.5),
                    sizes=((0, 0), (0.3, 0.5), (1, 0)), transparency=((0, 0), (1, 0.3)), accel=(0, 1, 0),
                    rot_speed=(-120, 120)), (0, WHITE), (0.5, GOLDHOT), (1, GOLD)))
    # The crown: a sun disc of gold light behind it, glow, sparkles and a twinkle on every diamond.
    fx(a, "CrownOrb",
       light("CrownLight", GOLDHOT, brightness=1.8, range_=14, pulse=1.4),
       grad(emitter("CrownGlow", GOLD, texture=GLOW_TEXTURE, rate=2, lifetime=(1.0, 1.2), speed=(0, 0),
                    sizes=((0, 4), (0.5, 5.5), (1, 4)), transparency=((0, 1), (0.5, 0.55), (1, 1)), lock=True),
            (0, GOLDHOT), (1, GOLD)),
       grad(emitter("CrownRays", GOLD, texture=VORTEX_TEXTURE, rate=1, lifetime=(2.5, 2.5), speed=(0, 0),
                    sizes=((0, 6), (0.5, 7), (1, 6)), transparency=((0, 1), (0.3, 0.6), (0.7, 0.6), (1, 1)),
                    lock=True, rot_speed=(40, 60)), (0, GOLDHOT), (1, GOLD2)),
       emitter("CrownSparkles", GOLDHOT, texture=SPARKLE_TEXTURE, rate=8, lifetime=(0.8, 1.4), speed=(1, 2.5),
               sizes=((0, 0.45), (1, 0)), spread=50, accel=(0, -1, 0), color2=GOLD))
    fx(a, "CrownJewel", glint("JewelGlint", C("#ffb3c4"), rate=1.2, size=1.6),
       light("JewelLight", RUBY, brightness=0.8, range_=6, pulse=1.1))
    for i in (0, 4):
        fx(a, f"CrownPointGem{i}", glint(f"PointGlint{i}", rate=0.8, size=1.2))
    # The bling on the chest: the medallion diamond twinkles and lights the chest up.
    fx(a, "MedallionDiamondCore",
       light("MedallionLight", DIAMOND, brightness=1.4, range_=10, pulse=0.9),
       glint("MedallionGlint", rate=1.6, size=2.4),
       grad(emitter("MedallionGlow", WHITE, texture=GLOW_TEXTURE, rate=2, lifetime=(0.8, 1.0), speed=(0, 0),
                    sizes=((0, 2.5), (0.5, 3.5), (1, 2.5)), transparency=((0, 1), (0.5, 0.5), (1, 1)), lock=True),
            (0, WHITE), (1, C("#9fe8ff"))))
    fx(a, "GrillTop1", glint("GrillGlint", rate=0.9, size=1.0))
    fx(a, "EarringGem", glint("EarGlint", rate=0.7, size=1.0))
    for s, S in SIDES:
        fx(a, f"BraceletDiamond{S}0", glint(f"BraceletGlint{S}", rate=1.0, size=1.4))
        fx(a, f"EpauletteGem{S}", light(f"EpauletteLight{S}", RUBY, brightness=0.6, range_=5, pulse=1.3))
        bp = p(f"Bracelet{S}0")
        trail(a, f"Bracelet{S}0", add(bp, (0, 0.5, 0)), add(bp, (0, -0.5, 0)), GOLDHOT, name=f"FistTrail{S}",
              lifetime=0.45, color2=GOLD, transparency=((0, 0.3), (1, 1)), width=0)
    # Coins and diamonds circling it: gold trails, twinkles, and a crown sigil turning on the ground.
    for i in (0, 2, 4, 6):
        cp = p(f"Coin{i}")
        trail(a, f"Coin{i}", add(cp, (0, 0.5, 0)), add(cp, (0, -0.5, 0)), GOLDHOT, name=f"CoinTrail{i}", lifetime=0.7,
              color2=GOLD, transparency=((0, 0.2), (1, 1)), width=0)
        fx(a, f"Coin{i}", glint(f"CoinGlint{i}", rate=0.8, size=1.2))
    for i in range(4):
        fx(a, f"OrbitDiamond{i}Up", glint(f"DiamondGlint{i}", rate=1.0, size=1.6),
           light(f"DiamondLight{i}", DIAMOND, brightness=0.6, range_=6, pulse=1.0 + 0.2 * i))
    fx(a, "SigilCore",
       flat(grad(emitter("Sigil", GOLD, texture=VORTEX_TEXTURE, rate=0.6, lifetime=(3, 3), speed=(0.01, 0.01),
                         spread=0, sizes=((0, 16), (1, 16)), transparency=((0, 1), (0.25, 0.5), (0.75, 0.5), (1, 1)),
                         lock=True, rot_speed=(25, 25)), (0, GOLDHOT), (1, GOLD2))),
       flat(grad(emitter("SigilGlow", GOLD, texture=GLOW_TEXTURE, rate=0.8, lifetime=(2, 2), speed=(0.01, 0.01),
                         spread=0, sizes=((0, 17), (1, 17)), transparency=((0, 1), (0.5, 0.75), (1, 1)), lock=True),
                 (0, GOLDHOT), (1, GOLD))),
       emitter("RisingGold", GOLDHOT, texture=FLAMESPARK_TEXTURE, rate=6, lifetime=(1.2, 2.0), speed=(1.5, 3),
               sizes=((0, 0.6), (1, 0)), spread=70, color2=GOLD, rot_speed=(-200, 200)))
    pulse(a, *[f"CrownRuby{i}" for i in range(8)], "CrownJewel", "MedallionDiamondCore", seconds=1.2)
    pulse(a, "EyeR", "EyeL", seconds=1.6)
    extras(a, attrs={"WalkSpeed": 9, "OrbitSpeed": 0.6}, highlight=(GOLD, GOLDHOT, 1.0, 0.55))
    return a


def _aim_x(d):
    """Rotation whose local X runs along d."""
    from lib import aim
    return aim(d)


ALL = [voidwhisker, gorilla_king]
