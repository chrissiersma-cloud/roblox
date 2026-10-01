"""The Phoenix (Mythic), rebuilt as a showpiece in the part style of the other animals: a big fire bird standing
tall with its wings raised, about 600 parts.

  * Crimson body with rows of chest scales that run from orange to white-hot, a ruff of flame feathers round the
    neck, and layered back and flank feathers.
  * Head with a golden hooked beak, glowing eyes under fierce brows, swept-back cheek feathers, a crest of seven
    flame plumes, and a sun halo behind it.
  * Two huge layered wings with flame tongues licking off every feather tip.
  * A long fan of nine tail plumes with feathered vanes, each ending in a glowing flame eye.
  * Golden scaled legs with flame cuffs and black talons.
  * Heavy fire effects: flames on the crest, wings and tail, rising embers, heat shimmer, pulsing firelight, wing
    and tail trails, a ring of fire on the ground and ember feathers orbiting it. Its idle action is "rebirth":
    it wraps itself in its wings and bursts open in a storm of fire (see AnimalFX.lua).

Faces -Z, +X is its right side, y = 0 is the ground. The id is "Phoenix", so it replaces the old stud Phoenix.
"""

import math

from dark_woods import GLOW, beam, chain, emitter, extras, ground_ring, light, plate, pulse, scale_animal, seg, \
    trail, unfight
from animals import DETAIL, find, fx
from lib import SIDES, SMOKE_TEXTURE, SPARKLE_TEXTURE, Animal, add, angles, apply, scale, sub, unit
from lib import hex_color as C
from mountain import feather_wing, in_bone

FIRE_TEXTURE = "rbxasset://textures/particles/fire_main.dds"

DEEP, CRIMSON, RED = C("#8f1610"), C("#c81e16"), C("#e8331f")
EMBER, ORANGE, AMBER = C("#ff4a10"), C("#ff6a14"), C("#ff9d1f")
YELLOW, HOT, WHITE_HOT = C("#ffd23a"), C("#fff2a8"), C("#fffbe6")
GOLD, GOLD_DARK, TALON = C("#ffc93c"), C("#d98a1c"), C("#2a1208")
FIRE = [EMBER, ORANGE, AMBER, YELLOW, HOT]
GLOW_T = dict(GLOW, transparency=0.2)
SPARK = dict(texture=SPARKLE_TEXTURE, transparency=((0, 0), (1, 1)))


def fire(t):
    """Colour along the flame gradient, t from 0 (deep ember) to 1 (white-hot)."""
    t = max(0.0, min(1.0, t))
    x = t * (len(FIRE) - 1)
    i = min(int(x), len(FIRE) - 2)
    f = x - i
    return tuple(p + (q - p) * f for p, q in zip(FIRE[i], FIRE[i + 1]))


def flame(a, name, base, direction, length, width, t0=0.3, glow=True, up=(0, 1, 0)):
    """A flame tongue: three plates that get thinner and hotter towards the tip."""
    d = unit(direction)
    p = base
    for k, (f, w) in enumerate(((0.45, 1.0), (0.33, 0.7), (0.22, 0.42))):
        q = add(p, scale(d, length * f))
        kw = GLOW_T if glow else dict(role="Secondary", shadow=False)
        plate(a, f"{name}{k}", p, q, width * w, 0.12, fire(t0 + 0.25 * k), up=up, **kw)
        p = add(q, scale(d, -length * 0.04))
    return p


def phoenix():
    a = Animal("Phoenix", "Phoenix", "Mythic")

    # -- body ----------------------------------------------------------------------------------
    a.oct("Body", (3.8, 4.6, 5.0), (0, 5.6, 0.4), CRIMSON, b=1.2, bottom=1.0)
    a.oct("Chest", (3.2, 3.8, 0.6), (0, 5.5, -2.0), ORANGE, b=0.8, role="Secondary")
    a.oct("Back", (3.0, 1.2, 3.6), (0, 7.75, 0.8), DEEP, b=0.5)
    # Chest scales in rows, orange at the top to white-hot at the bottom.
    for r in range(5):
        n = 5 if r % 2 == 0 else 4
        y = 7.0 - r * 0.72
        w = 2.6 - abs(r - 2) * 0.2
        for c in range(n):
            x = -w / 2 + (c + 0.5) * w / n
            a.tri(f"ChestScale{r}_{c}", (x, y, -2.42), 0.72, 0.8, 0.14, fire(0.35 + r * 0.14), R=angles(0, 0, 180),
                  role="Secondary", shadow=False)
    # Back and flank feathers: overlapping rows pointing down and back.
    for r in range(3):
        for c in range(4):
            x = -1.2 + c * 0.8
            p = (x, 7.8 - r * 0.9, 1.6 + r * 0.6)
            plate(a, f"BackFeather{r}_{c}", p, add(p, (0, -0.9, 1.3)), 0.7, 0.14, (RED, CRIMSON, DEEP)[r],
                  up=(0, 0.8, 0.6), role="Secondary", shadow=False)
    for s, S in SIDES:
        for r in range(2):
            for j in range(3):
                p = (1.95 * s, 6.1 - r * 1.1, -1.0 + j * 1.2 + r * 0.3)
                plate(a, f"FlankFeather{S}{r}_{j}", p, add(p, (0.15 * s, -1.0, 0.7)), 0.85, 0.14,
                      (RED, ORANGE, AMBER)[r], up=(s, 0, 0), role="Secondary", shadow=False)
    # Thigh feathers: a skirt of flames over the legs.
    for k in range(8):
        ang = math.pi * (0.15 + 0.7 * k / 7)
        p = (math.cos(ang) * 1.9, 3.6, 0.4 - math.sin(ang) * 0.4)
        a.tri(f"Skirt{k}", p, 0.9, 1.2, 0.14, fire(0.2 + 0.1 * (k % 3)), R=angles(0, 0, 180), role="Secondary",
              shadow=False)

    # -- head ----------------------------------------------------------------------------------
    with a.bone("Head", "Body", (0, 7.4, -1.1)):
        seg(a, "Neck", (0, 7.2, -0.9), (0, 8.6, -1.5), 1.9, CRIMSON)
        # Ruff of flame feathers round the base of the neck.
        for k in range(14):
            ang = 2 * math.pi * k / 14
            c, s_ = math.cos(ang), math.sin(ang)
            p0 = (c * 1.0, 7.9, -1.2 + s_ * 1.0)
            p1 = (c * 2.1, 7.3 - 0.25 * (k % 2), -1.1 + s_ * 2.1)
            plate(a, f"Ruff{k}", p0, p1, 0.75, 0.14, fire(0.25 + 0.2 * (k % 3)), up=(c * 0.4, 1, s_ * 0.4),
                  role="Secondary", shadow=False)
            plate(a, f"RuffTip{k}", p1, add(p1, (c * 0.6, -0.4, s_ * 0.6)), 0.45, 0.12, fire(0.75), up=(c * 0.4, 1, s_ * 0.4),
                  **GLOW)
        a.oct("Head", (2.8, 2.6, 2.9), (0, 9.3, -1.8), RED, b=0.75)
        a.oct("Face", (2.2, 1.3, 0.5), (0, 9.0, -3.2), CRIMSON, b=0.35, role="Secondary")
        a.taper("Beak", (1.2, 1.0), (0.5, 0.4), 2.0, (0, 9.0, -4.0), GOLD, r=0.25, role="Accent", reflectance=0.2)
        a.box("BeakHook", (0.45, 0.75, 0.5), (0, 8.6, -5.0), GOLD, role="Accent")
        a.box("BeakTip", (0.32, 0.3, 0.3), (0, 8.15, -5.1), GOLD_DARK, **DETAIL)
        a.box("BeakLine", (1.1, 0.08, 1.7), (0, 8.85, -3.85), GOLD_DARK, **DETAIL)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (0.95 * s, 9.55, -3.22), w=0.9, h=1.0, iris=C("#ffd23a"), glow=True)
            a.box(f"Brow{S}", (1.15, 0.32, 0.3), (0.95 * s, 10.2, -3.28), YELLOW, rot=(0, 0, -16 * s), **GLOW)
            a.box(f"EyeMark{S}", (0.9, 0.18, 0.12), (1.25 * s, 9.05, -3.2), GOLD, rot=(0, 0, 20 * s), **DETAIL)
            # Cheek feathers sweeping back.
            for j in range(3):
                p = (1.4 * s, 9.6 - j * 0.45, -2.4 + j * 0.2)
                plate(a, f"Cheek{S}{j}", p, add(p, (0.35 * s, 0.1 - 0.15 * j, 1.6 - 0.2 * j)), 0.5, 0.12,
                      fire(0.3 + 0.25 * j), up=(s, 0, 0), role="Secondary", shadow=False)
        # Crest: seven flame plumes, curving back and up, hotter towards the tips.
        for i in range(7):
            x = (i - 3) * 0.32
            lift = 1.0 - abs(i - 3) * 0.12
            pts = [(x, 10.4, -2.4 + abs(i - 3) * 0.15), (x * 1.3, 11.6 * lift + 0.9, -1.8),
                   (x * 1.6, 12.5 * lift + 1.4, -0.6), (x * 1.8, 12.9 * lift + 1.6, 0.8)]
            for k in range(3):
                plate(a, f"Crest{i}_{k}", pts[k], pts[k + 1], 0.55 - 0.12 * k, 0.16, fire(0.3 + 0.3 * k),
                      up=(1, 0, 0), **(GLOW_T if k else dict(role="Secondary", shadow=False)))
        # Sun halo behind the head.
        for k in range(12):
            ang = 2 * math.pi * k / 12
            p = (math.cos(ang) * 2.6, 10.0 + math.sin(ang) * 2.6, 0.6)
            a.box(f"Halo{k}", (0.22, 2 * math.pi * 2.6 / 12 * 0.85, 0.22), p, fire(0.8 if k % 2 else 0.95),
                  rot=(0, 0, math.degrees(ang)), **GLOW_T)

    # -- wings ---------------------------------------------------------------------------------
    for s, S in SIDES:
        root = (1.9 * s, 7.6, -0.6)
        arm = [root, (3.6 * s, 9.6, -0.2), (5.4 * s, 11.3, 0.8), (6.9 * s, 12.3, 2.2), (7.9 * s, 12.7, 3.8)]
        feather_wing(a, s, S, root, arm, [DEEP, CRIMSON, RED, ORANGE, AMBER, CRIMSON], [YELLOW, HOT], edge=HOT,
                     rows=(10, 8), tip_glow=True, width=1.25, scale_k=1.15)
        # Flame tongues licking off every primary tip, and smaller ones off the secondaries.
        with in_bone(a, f"Wing{S}"):
            for i in range(8):
                tip = find(a, f"Wing{S}PrimaryTip{i}")
                q = tip_end(tip)
                d = unit(sub(q, tip["p"]))
                flame(a, f"Wing{S}Flame{i}", q, add(d, (0, 0.35, 0)), 2.2 + 0.15 * i, 0.7, t0=0.45)
            for i in range(0, 10, 3):
                sec = find(a, f"Wing{S}Secondary{i}")
                q = tip_end(sec)
                d = unit(sub(q, sec["p"]))
                flame(a, f"Wing{S}SecFlame{i}", q, add(d, (0, 0.2, 0)), 1.4, 0.6, t0=0.3)

    # -- tail ----------------------------------------------------------------------------------
    with a.bone("Tail", "Body", (0, 4.6, 2.6)):
        for i in range(7):
            yaw = (i - 3) * 15
            R = angles(0, yaw, 0)
            length = 1.0 - abs(i - 3) * 0.08
            rise = 1.0 - abs(i - 3) * 0.15
            local = [(0, 4.6, 2.6), (0, 4.3, 5.2 * length + 0.6), (0, 4.9 * rise + 0.3, 8.2 * length + 0.6),
                     (0, 7.0 * rise + 0.3, 10.8 * length + 0.6), (0, 9.6 * rise + 0.3, 12.2 * length + 0.6)]
            pts = [add((0, 0, 2.6), apply(R, sub(p, (0, 0, 2.6)))) for p in local]
            chain(a, f"Plume{i}", pts, [0.42, 0.36, 0.3, 0.24], fire(0.0) if i % 2 else CRIMSON)
            side = apply(R, (1, 0, 0))
            for k in range(1, 3):
                for sd in (-1, 1):
                    p = pts[k]
                    q = add(p, add(scale(side, 0.9 * sd), scale(unit(sub(pts[k + 1], pts[k - 1])), 0.6)))
                    plate(a, f"Vane{i}_{k}{'R' if sd > 0 else 'L'}", p, q, 0.7, 0.12, fire(0.1 + 0.22 * k),
                          up=(0, 1, 0), role="Secondary", shadow=False)
            end = pts[-1]
            d = unit(sub(pts[-1], pts[-2]))
            a.shard(f"PlumeEye{i}", end, 1.1, 1.8, fire(0.7), R=angles(0, yaw, 0), cross=True, **GLOW_T)
            a.box(f"PlumeEyeCore{i}", (0.45, 0.6, 0.45), add(end, (0, 0.5, 0)), WHITE_HOT, **GLOW)
            flame(a, f"PlumeFlame{i}", add(end, scale(d, 0.6)), add(d, (0, 1.2, 0)), 1.8, 0.6, t0=0.5)

    # -- legs ----------------------------------------------------------------------------------
    for s, S in SIDES:
        with a.bone(f"Leg{S}", "Body", (0.9 * s, 3.6, 0.5)):
            a.oct(f"Thigh{S}", (1.3, 1.2, 1.3), (0.9 * s, 3.3, 0.5), CRIMSON, b=0.35)
            a.post(f"Leg{S}", (0.55, 2.8, 0.55), (0.9 * s, 1.6, 0.5), GOLD, b=0.15, role="Accent")
            for j in range(3):
                a.box(f"LegScale{S}{j}", (0.62, 0.18, 0.62), (0.9 * s, 0.9 + j * 0.7, 0.5), GOLD_DARK, **DETAIL)
            for j in range(4):
                ang = j * math.pi / 2
                a.box(f"Cuff{S}{j}", (0.25, 0.7, 0.5), (0.9 * s + math.cos(ang) * 0.42, 2.75, 0.5 + math.sin(ang) * 0.42),
                      fire(0.6), rot=(0, -math.degrees(ang), 0), **GLOW)
            for j, yaw in enumerate((-28, 0, 28, 180)):
                R = angles(0, yaw, 0)
                ln = 0.9 if yaw == 180 else 1.3
                a.box(f"Toe{j}{S}", (0.32, 0.3, ln), add((0.9 * s, 0.15, 0.5), apply(R, (0, 0, -ln / 2))), GOLD, R=R,
                      role="Accent")
                a.wedge(f"Talon{j}{S}", (0.3, 0.32, 0.45), add((0.9 * s, 0.15, 0.5), apply(R, (0, 0, -ln - 0.15))),
                        TALON, R=R, **DETAIL)

    # -- orbit: ember feathers circling it and a ring of fire on the ground -------------------------
    with a.bone("Orbit", "Body", (0, 5.6, 0.4)):
        for i in range(8):
            ang = 2 * math.pi * i / 8
            p = (math.cos(ang) * 6.4, 6.0 + 1.4 * math.sin(ang * 3), 0.4 + math.sin(ang) * 6.4)
            plate(a, f"EmberFeather{i}", p, add(p, (0, 1.6, 0.3)), 0.55, 0.12, fire(0.55 + 0.2 * (i % 2)),
                  up=(math.cos(ang), 0, math.sin(ang)), **GLOW)
        ground_ring(a, "FireRing", (0, 0.08, 0.4), 6.8, fire(0.4), n=22, size=(0.6, 0.14, 1.6), transparency=0.15)
        ground_ring(a, "FireRingInner", (0, 0.1, 0.4), 5.2, fire(0.8), n=16, size=(0.35, 0.12, 1.2), transparency=0.3)

    a.ride_height, a.ride_z = 8.0, 0.5
    scale_animal(a, 1.3)
    unfight(a, "Chest", d=0.04)

    # -- heavy fire effects -------------------------------------------------------------------
    k = 1.3
    p = lambda n: find(a, n)["p"]
    fx(a, "Body",
       light("FireLight", ORANGE, brightness=2.4, range_=26, pulse=1.3),
       emitter("Embers", HOT, rate=22, lifetime=(1.2, 2.2), speed=(1, 3), sizes=((0, 0.45), (1, 0)),
               accel=(0, 4, 0), color2=EMBER, spread=180, **SPARK),
       emitter("BodyFlames", YELLOW, texture=FIRE_TEXTURE, rate=14, lifetime=(0.5, 0.9), speed=(1, 2.5),
               sizes=((0, 1.8), (1, 0)), transparency=((0, 0.35), (1, 1)), accel=(0, 5, 0), color2=EMBER, spread=35),
       emitter("HeatHaze", C("#ff7a2a"), texture=SMOKE_TEXTURE, rate=3, lifetime=(1.5, 2.5), speed=(1, 2),
               sizes=((0, 2), (1, 5)), transparency=((0, 0.85), (1, 1)), light=0.2, accel=(0, 2, 0)))
    fx(a, "Crest3_2",
       emitter("CrestFire", YELLOW, texture=FIRE_TEXTURE, rate=24, lifetime=(0.4, 0.7), speed=(1, 2.5),
               sizes=((0, 1.4), (1, 0)), transparency=((0, 0.2), (1, 1)), accel=(0, 6, 0), color2=EMBER, spread=25),
       light("CrestLight", YELLOW, brightness=1.4, range_=12, pulse=0.9))
    for s, S in SIDES:
        for i in (2, 5, 7):
            fx(a, f"Wing{S}Flame{i}2",
               emitter(f"WingFire{i}", YELLOW, texture=FIRE_TEXTURE, rate=12, lifetime=(0.4, 0.8), speed=(0.5, 2),
                       sizes=((0, 1.3), (1, 0)), transparency=((0, 0.25), (1, 1)), accel=(0, 5, 0), color2=EMBER,
                       spread=40))
        fx(a, f"Wing{S}Flame41",
           emitter("WingEmbers", HOT, rate=10, lifetime=(1, 1.8), speed=(0.5, 1.5), sizes=((0, 0.4), (1, 0)),
                   accel=(0, -2, 0), color2=ORANGE, **SPARK))
        tip = p(f"Wing{S}Flame72")
        trail(a, f"Wing{S}Flame72", add(tip, (0, 0.7 * k, 0)), add(tip, (0, -0.7 * k, 0)), YELLOW, name=f"WingTrail{S}",
              lifetime=0.6, color2=EMBER, transparency=((0, 0.1), (1, 1)))
        # Spirals of fire rising from the wing roots.
        r0 = p(f"Wing{S}Arm0")
        beam(a, f"Wing{S}Arm0", r0, f"Wing{S}Arm0", add(r0, (0, 11 * k, 0)), YELLOW, name=f"FireSpiral{S}",
             width=(1.2, 0.1), curve=(4 * s, -3), transparency=((0, 0.45), (1, 1)), segments=12, color2=EMBER,
             texture=FIRE_TEXTURE, texture_speed=2.5)
        fx(a, f"Cuff{S}0", emitter("FootFlames", AMBER, texture=FIRE_TEXTURE, rate=5, lifetime=(0.3, 0.6),
                                   speed=(0.5, 1.5), sizes=((0, 0.7), (1, 0)), accel=(0, 4, 0), color2=EMBER, spread=30))
    for i in (0, 3, 6):
        fx(a, f"PlumeFlame{i}2",
           emitter(f"TailFire{i}", YELLOW, texture=FIRE_TEXTURE, rate=10, lifetime=(0.4, 0.8), speed=(0.5, 2),
                   sizes=((0, 1.2), (1, 0)), transparency=((0, 0.25), (1, 1)), accel=(0, 5, 0), color2=EMBER, spread=40))
    end = p("PlumeEye3")
    trail(a, "PlumeEye3", add(end, (0.6 * k, 0, 0)), add(end, (-0.6 * k, 0, 0)), ORANGE, name="TailTrail",
          lifetime=0.7, color2=EMBER, transparency=((0, 0.15), (1, 1)))
    fx(a, "PlumeEyeCore3", light("TailLight", AMBER, brightness=1.2, range_=12, pulse=1.1))
    fx(a, "FireRing0", emitter("RingFlames", AMBER, texture=FIRE_TEXTURE, rate=6, lifetime=(0.4, 0.8), speed=(0.5, 1.5),
                               sizes=((0, 1.0), (1, 0)), accel=(0, 4, 0), color2=EMBER, spread=20))
    fx(a, "FireRing11", emitter("RingFlames2", AMBER, texture=FIRE_TEXTURE, rate=6, lifetime=(0.4, 0.8),
                                speed=(0.5, 1.5), sizes=((0, 1.0), (1, 0)), accel=(0, 4, 0), color2=EMBER, spread=20))
    for i in (0, 4):
        fp = p(f"EmberFeather{i}")
        trail(a, f"EmberFeather{i}", add(fp, (0, 0.6 * k, 0)), add(fp, (0, -0.4 * k, 0)), YELLOW,
              name=f"FeatherTrail{i}", lifetime=0.7, color2=EMBER)
        fx(a, f"EmberFeather{i}", light(f"FeatherLight{i}", ORANGE, brightness=0.8, range_=8, pulse=1.0))
    pulse(a, "EyeLIris", "EyeRIris", "BrowL", "BrowR", "PlumeEyeCore3", seconds=1.2)
    extras(a, attrs={"WalkSpeed": 7, "FlapSpeed": 1.3, "FlapAngle": 9, "OrbitSpeed": 0.7, "TailSway": 9},
           highlight=(ORANGE, YELLOW, 1.0, 0.45))
    return a


def tip_end(part):
    """The far end of a plate along its length (plates are boxes with X along their length)."""
    R = part["R"]
    half = part["size"][0] / 2
    return add(part["p"], (R[0][0] * half, R[1][0] * half, R[2][0] * half))


ALL = [phoenix]
