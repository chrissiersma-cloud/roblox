"""The 16 animals of the Mountain Range, in the same blocky studded style as the other animals, from the
approved concept art (concept-art/mountain-range). Each faces -Z, +X is its right side and y = 0 is the ground.

Common and Rare animals are clean and detailed; Epic and Legendary ones get effects; the Mythic and Secret animals
(Sky Griffin, Glacier Mammoth, Aurora Dragon) are the showpieces with heavy effects: orbiting rings, beams, trails,
lights, particle storms and their own big idle action. The AnimalFX script animates all of them (profiles with the
same names in AnimalFX.lua).
"""

import math
from contextlib import contextmanager

from animals import DETAIL, MOUTH, PINK, _bunny, _canine, _deer, at, find, fx, pixel_star
from dark_woods import GLOW, beam, chain, emitter, extras, ground_ring, light, plate, pulse, scale_animal, seg, \
    trail, unfight
from lib import EYE, IDENTITY, SIDES, SMOKE_TEXTURE, SPARKLE_TEXTURE, WHITE, Animal, add, aim, angles, apply, \
    cross, matmul, scale, sub, unit
from lib import hex_color as C

FIRE_TEXTURE = "rbxasset://textures/particles/fire_main.dds"
ICE, ICE_HOT, ICE_DEEP = C("#7fe3ff"), C("#e6fbff"), C("#3fa8e0")
GOLD, GOLD_HOT, GOLD_DARK = C("#ffc93c"), C("#fff3b0"), C("#d98a1c")
GLOW_T = dict(GLOW, transparency=0.25)
SPARK = dict(texture=SPARKLE_TEXTURE, transparency=((0, 0), (1, 1)))


@contextmanager
def in_bone(a, name):
    """Adds parts to a joint a template already made."""
    prev, a.current_bone = a.current_bone, name
    try:
        yield
    finally:
        a.current_bone = prev


def drop(a, *prefixes):
    """Removes template parts (and their bevel pieces) whose names start with one of the prefixes."""
    gone = [p for p in a.parts if any(p["name"].startswith(x) for x in prefixes)]
    for p in gone:
        a.parts.remove(p)
        a._names.discard(p["name"])


def ice_shard(a, name, base, h, w, color=ICE, R=IDENTITY, glow=True):
    """A translucent ice crystal with a bright core."""
    a.shard(name, base, w, h, color, R=R, cross=True, material="Glass", transparency=0.2, reflectance=0.25,
            role="Glow", shadow=False)
    if glow:
        a.box(f"{name}Core", (w * 0.32, h * 0.5, w * 0.32), add(base, apply(R, (0, h * 0.28, 0))), ICE_HOT, R=R,
              **GLOW)


def rosette(a, name, center, r, color, normal="x"):
    """A glowing ring of four bars (snow leopard spots)."""
    for k in range(4):
        ang = k * math.pi / 2
        if normal == "x":
            off, size = (0, r * math.sin(ang), r * math.cos(ang)), (0.12, 0.18 + r * abs(math.cos(ang)) * 1.4,
                                                                     0.18 + r * abs(math.sin(ang)) * 1.4)
        else:
            off, size = (r * math.cos(ang), 0, r * math.sin(ang)), (0.18 + r * abs(math.sin(ang)) * 1.4, 0.12,
                                                                     0.18 + r * abs(math.cos(ang)) * 1.4)
        a.box(f"{name}{k}", size, add(center, off), color, **GLOW)


def feather_wing(a, s, S, root, arm, cols, tip_cols, edge=None, back=(0.1, -0.35, 1.0), rows=(8, 6), scale_k=1.0,
                 tip_glow=False, width=1.0):
    """A big layered wing in its own Wing joint: arm bones, coverts, secondaries and fanned primaries."""
    with a.bone(f"Wing{S}", "Body", root):
        for i in range(len(arm) - 1):
            seg(a, f"Wing{S}Arm{i}", arm[i], arm[i + 1], 0.6 - 0.08 * i, cols[0])
            if edge:
                seg(a, f"Wing{S}Edge{i}", add(arm[i], (0, 0.36, -0.1)), add(arm[i + 1], (0, 0.36, -0.1)), 0.14, edge,
                    ext=0.3, **GLOW)
        bk = unit((back[0] * s, back[1], back[2]))
        armdir = unit(sub(arm[-1], arm[0]))
        normal = unit(cross(armdir, bk))
        if normal[1] < 0:
            normal = scale(normal, -1)

        def along(t):
            x = t * (len(arm) - 1)
            i = min(int(x), len(arm) - 2)
            return add(arm[i], scale(sub(arm[i + 1], arm[i]), x - i))

        for i in range(rows[0]):
            t = 0.04 + i * 0.6 / (rows[0] - 1)
            p = along(t)
            plate(a, f"Wing{S}Covert{i}", p, add(p, scale(bk, 1.2 * scale_k)), 0.85 * width, 0.16, cols[1 + i % 2],
                  up=normal, role="Secondary", shadow=False)
            q = add(p, scale(bk, 0.7 * scale_k))
            ln = ((0.8 if t < 0.15 else 2.2) + 1.0 * t) * scale_k
            plate(a, f"Wing{S}Secondary{i}", q, add(q, scale(bk, ln)), 0.8 * width, 0.14, cols[3 + i % 2], up=normal,
                  role="Secondary", shadow=False)
        for i in range(rows[1]):
            t = 0.55 + i * 0.45 / (rows[1] - 1)
            p = along(t)
            fan = unit(add(scale(bk, 1.0 - 0.14 * i), scale(armdir, 0.17 * i)))
            ln = (3.0 + 0.25 * i) * scale_k
            q = add(p, scale(bk, 0.5 * scale_k))
            plate(a, f"Wing{S}Primary{i}", q, add(q, scale(fan, ln)), 0.72 * width, 0.14, cols[3 + i % 2], up=normal,
                  role="Secondary", shadow=False)
            tip0 = add(q, scale(fan, ln * 0.72))
            plate(a, f"Wing{S}PrimaryTip{i}", tip0, add(q, scale(fan, ln * 1.02)), 0.76 * width, 0.17, tip_cols[i % 2],
                  up=normal, **(GLOW if tip_glow else dict(role="Accent", shadow=False)))
    return arm


# ------------------------------------------------------------------ Common ----

def pebble_marmot():
    a = Animal("PebbleMarmot", "Pebble Marmot", "Common")
    fur, cream, stone, moss = C("#b07a45"), C("#ecc995"), C("#9aa0ad"), C("#7cc457")

    def head(a):
        for s, S in SIDES:
            a.oct(f"RoundEar{S}", (1.0, 1.0, 0.55), (1.45 * s, 6.55, -0.6), fur, b=0.3)
            a.box(f"RoundEarIn{S}", (0.55, 0.55, 0.1), (1.45 * s, 6.55, -0.92), PINK, **DETAIL)
        a.bevel("HatPebble", (1.7, 0.85, 1.4), (0.35, 7.05, -0.9), stone, b=0.3)
        a.bevel("HatMoss", (1.4, 0.32, 1.15), (0.35, 7.6, -0.9), moss, b=0.12, role="Secondary")
        a.rod("Sprout", (0.45, 7.75, -0.9), (0.7, 8.7, -1.0), 0.16, C("#4f9a32"), role="Accent")
        for s in (-1, 1):
            a.box(f"SproutLeaf{'R' if s > 0 else 'L'}", (0.7, 0.12, 0.38), (0.7 + 0.35 * s, 8.7, -1.0), moss,
                  rot=(0, 0, 25 * s), role="Accent")

    _bunny(a, fur, cream, ears=False, head_extra=head, tail=C("#8a5a2e"))
    with in_bone(a, "Body"):
        # Its favourite pebble, held against its chest, with a little moss on top.
        a.bevel("HeldPebble", (1.8, 1.3, 1.1), (0, 2.5, -2.2), stone, b=0.35)
        a.bevel("HeldMoss", (1.2, 0.3, 0.8), (0.1, 3.2, -2.2), moss, b=0.1, role="Secondary")
        a.box("PebbleShine", (0.35, 0.25, 0.08), (-0.4, 2.8, -2.78), WHITE, **DETAIL)
    extras(a, attrs={"WalkSpeed": 7})
    return a


def pika_puff():
    a = Animal("PikaPuff", "Pika Puff", "Common")
    fur, cream = C("#c9a27a"), C("#f2dcc0")

    def head(a):
        for s, S in SIDES:
            a.oct(f"RoundEar{S}", (1.8, 1.8, 0.55), (1.55 * s, 7.05, -0.7), fur, b=0.55)
            a.oct(f"RoundEarIn{S}", (1.15, 1.15, 0.1), (1.55 * s, 7.0, -1.02), C("#f0a6b4"), b=0.3, **DETAIL)
            for j, dy in enumerate((0.15, -0.15)):
                a.box(f"Whisker{j}{S}", (1.6, 0.08, 0.08), (1.6 * s, 4.15 + dy, -2.9), C("#3a2a20"),
                      rot=(0, 0, -10 * s * (1 if j else -1)), **DETAIL)
        # An edelweiss behind its right ear.
        c = (2.35, 7.6, -0.6)
        for k in range(6):
            ang = math.radians(k * 60)
            a.box(f"Petal{k}", (0.5, 0.18, 0.3), (c[0] + 0.32 * math.cos(ang), c[1] + 0.32 * math.sin(ang), c[2]),
                  WHITE, rot=(0, 0, k * 60), **DETAIL)
        a.box("FlowerHeart", (0.3, 0.3, 0.2), (c[0], c[1], c[2] - 0.05), C("#ffd23f"), **DETAIL)

    _bunny(a, fur, cream, ears=False, head_extra=head, tail=None)
    scale_animal(a, 0.8)
    extras(a, attrs={"WalkSpeed": 6})
    return a


def cliff_kid():
    a = Animal("CliffKid", "Cliff Kid", "Common")
    fur, cream, hoof, horn = C("#f3efe6"), C("#ffffff"), C("#4a3a30"), C("#b9a690")

    def horns(a):
        for s, S in SIDES:
            a.rod(f"Horn{S}", (0.6 * s, 11.1, -3.2), (0.75 * s, 12.3, -2.6), 0.42, horn, role="Accent")
            a.rod(f"HornTip{S}", (0.75 * s, 12.3, -2.6), (0.8 * s, 12.8, -2.0), 0.28, horn, role="Accent")

    def extra(a):
        a.tri("Beard", (0, 8.45, -5.5), 0.7, 1.0, 0.4, C("#e8e2d4"), R=angles(0, 0, 180), role="Secondary")
        a.box("Collar", (2.15, 0.42, 2.25), (0, 7.45, -2.55), C("#e23d3d"), rot=(-12, 0, 0), role="Accent")
        a.bevel("Bell", (0.75, 0.75, 0.6), (0, 6.95, -3.8), C("#ffd23f"), b=0.2, role="Accent", reflectance=0.2)
        a.box("BellSlot", (0.5, 0.1, 0.1), (0, 6.75, -4.12), EYE, **DETAIL)

    _deer(a, fur, cream, hoof, antlers=horns, head_extra=extra, tail=fur, iris=C("#c98a2a"))
    unfight(a, "Belly", "Chest", "Jaw")
    scale_animal(a, 0.72)
    extras(a, attrs={"WalkSpeed": 9})
    return a


def snowshoe_hare():
    a = Animal("SnowshoeHare", "Snowshoe Hare", "Common")
    _bunny(a, C("#f6f8fc"), C("#e2eaf6"), ear_tip=C("#6fa8e6"), eye={"iris": C("#3f7fbf")})
    for s, S in SIDES:
        with in_bone(a, f"LegB{S}"):
            # Its big snowshoe feet, with laces.
            a.box(f"Snowshoe{S}", (2.0, 0.2, 3.5), (1.55 * s, 0.1, 1.0), C("#bfe0ff"), role="Accent")
            for z in (0.2, 1.0, 1.8):
                a.box(f"Lace{S}{z}", (2.04, 0.24, 0.12), (1.55 * s, 0.1, z), C("#6fa8e6"), **DETAIL)
    extras(a, attrs={"WalkSpeed": 9})
    return a


# -------------------------------------------------------------------- Rare ----

def bighorn_ram():
    a = Animal("BighornRam", "Bighorn Ram", "Rare")
    fur, cream, hoof, horn, ridge = C("#c4925e"), C("#f2e2c8"), C("#3a2a20"), C("#d9c2a0"), C("#a88a62")

    def horns(a):
        for s, S in SIDES:
            # A big curl beside the head: up over where the ear would be, back, down and forward to the cheek.
            c = (2.0 * s, 10.2, -2.6)
            pts = []
            for j in range(14):
                phi = j * 1.75 * math.pi / 13
                r = 1.7 - 0.55 * phi / math.pi
                pts.append((c[0] + s * 0.45 * phi / math.pi, c[1] + r * math.cos(phi), c[2] + r * math.sin(phi)))
            for j in range(13):
                seg(a, f"Horn{j}{S}", pts[j], pts[j + 1], 1.15 - 0.05 * j, horn, ext=0.55, role="Accent")
                if j % 2 == 1:
                    a.box(f"HornRidge{j}{S}", (0.14, 1.2 - 0.05 * j, 1.2 - 0.05 * j), pts[j], ridge,
                          R=aim(sub(pts[j + 1], pts[j])), role="Accent", shadow=False)
            a.box(f"HornStripe{S}", (0.2, 0.3, 1.0), add(pts[3], (0.6 * s, 0, 0)), C("#c4552e"), **DETAIL)

    _deer(a, fur, cream, hoof, antlers=horns, tail=cream, iris=C("#c98a2a"))
    drop(a, "EarL", "EarR", "InnerEarL", "InnerEarR")
    with in_bone(a, "Body"):
        a.box("Rump", (3.0, 2.2, 0.2), (0, 5.8, 3.66), cream, role="Secondary")
    unfight(a, "Belly", "Chest", "Jaw")
    scale_animal(a, 1.1)
    extras(a, attrs={"WalkSpeed": 11})
    return a


def alpine_ibex():
    a = Animal("AlpineIbex", "Alpine Ibex", "Rare")
    fur, light_c, hoof, horn = C("#8d7a62"), C("#c9b79a"), C("#2e241c"), C("#b8a48a")

    def horns(a):
        for s, S in SIDES:
            pts = [(0.55 * s, 11.1, -3.0), (0.65 * s, 12.6, -2.6), (0.78 * s, 13.8, -1.6), (0.9 * s, 14.4, -0.2),
                   (0.98 * s, 14.2, 1.2), (1.02 * s, 13.5, 2.3)]
            chain(a, f"Horn{S}", pts, [0.8, 0.7, 0.6, 0.5, 0.4], horn, role="Accent")
            for j in range(1, 5):
                a.box(f"HornRidge{j}{S}", (0.85 - 0.1 * j, 0.2, 0.85 - 0.1 * j), pts[j], C("#7d6a52"),
                      R=aim(sub(pts[j + 1], pts[j - 1])), role="Accent", shadow=False)

    def extra(a):
        a.tri("Beard", (0, 8.5, -5.4), 0.8, 1.6, 0.4, C("#5a4a3a"), R=angles(0, 0, 180), role="Secondary")
        c = (0.9, 11.6, -3.2)
        for k in range(5):
            ang = math.radians(k * 72)
            a.box(f"Edelweiss{k}", (0.42, 0.16, 0.26), (c[0] + 0.25 * math.cos(ang), c[1] + 0.25 * math.sin(ang), c[2]),
                  WHITE, rot=(0, 0, k * 72), **DETAIL)
        a.box("EdelweissHeart", (0.24, 0.24, 0.2), (c[0], c[1], c[2] - 0.04), C("#ffd23f"), **DETAIL)

    _deer(a, fur, light_c, hoof, antlers=horns, head_extra=extra, tail=fur, iris=C("#c98a2a"))
    unfight(a, "Belly", "Chest", "Jaw")
    scale_animal(a, 1.1)
    extras(a, attrs={"WalkSpeed": 11})
    return a


def red_panda():
    a = Animal("RedPanda", "Red Panda", "Rare")
    fur, white, black, ring = C("#d4582a"), C("#fff4e6"), C("#2e1a16"), C("#f2c49a")

    def face(a):
        for s, S in SIDES:
            a.box(f"BrowPatch{S}", (0.95, 0.42, 0.1), (1.1 * s, 8.75, -5.72), white, **DETAIL)
            a.box(f"TearMark{S}", (0.45, 0.9, 0.1), (1.15 * s, 6.95, -5.74), C("#8a2a14"), **DETAIL)
        # A bamboo sprig in its mouth.
        a.rod("Bamboo", (-1.9, 6.15, -6.5), (2.2, 6.35, -6.6), 0.32, C("#7cc457"), role="Accent")
        for x in (-1.0, 0.9):
            a.box(f"BambooNode{x}", (0.14, 0.4, 0.4), (x, 6.25, -6.55), C("#5fae3e"), role="Accent", shadow=False)
        a.box("BambooLeaf", (1.4, 0.12, 0.5), (2.7, 6.5, -6.6), C("#5fae3e"), rot=(0, 0, 25), role="Accent")

    def tail(a):
        with a.bone("Tail", "Body", (0, 5.6, 4.1)):
            for j in range(6):
                R = angles(-30 - j * 6, 0, 0)
                a.oct(f"Tail{j}", (1.9 - 0.08 * j, 1.9 - 0.08 * j, 1.05), (0, 5.5 + j * 0.62, 4.6 + j * 0.85),
                      fur if j % 2 == 0 else ring, b=0.5, R=R, role="Secondary" if j % 2 else "Primary")

    _canine(a, fur, white, inner=white, eye={"iris": C("#5a2a10")}, snout="cat", ear=(1.7, 1.5), brows=False,
            fangs=False, paws=black, tail=tail, head_extra=face)
    unfight(a, "Belly", "Chest", "FaceMask")
    scale_animal(a, 0.75)
    extras(a, attrs={"WalkSpeed": 8})
    return a


# -------------------------------------------------------------------- Epic ----

def peak_eagle():
    a = Animal("PeakEagle", "Peak Eagle", "Epic")
    brown, dark, white, beak = C("#6b4a2e"), C("#4a3220"), C("#f6efe0"), C("#ffc23a")

    a.oct("Body", (3.6, 4.4, 5.0), (0, 5.4, 0.4), brown, b=1.1, bottom=0.9)
    a.oct("Chest", (3.0, 3.4, 0.5), (0, 5.4, -2.2), C("#8a6440"), b=0.7, role="Secondary")
    for i, x in enumerate((0.0, -1.0, 1.0)):
        R = angles(22, x * 18, 0)
        a.box(f"TailFeather{i}", (1.1, 0.35, 3.4), at((x * 0.7, 4.0, 2.7), R, (0, 0, 1.4)), white, R=R)
        a.box(f"TailTip{i}", (1.1, 0.37, 0.8), at((x * 0.7, 4.0, 2.7), R, (0, 0, 2.9)), GOLD, R=R, role="Accent")

    with a.bone("Head", "Body", (0, 7.2, -1.2)):
        a.oct("Head", (3.0, 2.8, 3.0), (0, 8.5, -1.6), white, b=0.8)
        a.tri("HeadCrest", (0, 9.7, -0.6), 1.6, 1.0, 0.6, white, R=angles(-60, 0, 0))
        a.taper("Beak", (1.4, 1.1), (0.6, 0.45), 2.2, (0, 8.1, -3.9), beak, r=0.25, role="Accent")
        a.box("BeakHook", (0.5, 0.7, 0.5), (0, 7.75, -4.95), beak, role="Accent")
        a.box("BeakLine", (1.3, 0.08, 1.9), (0, 8.0, -3.7), C("#a8701a"), **DETAIL)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (1.0 * s, 8.8, -3.12), w=0.95, h=1.0, iris=C("#ffb21c"))
            a.box(f"Brow{S}", (1.1, 0.3, 0.25), (1.0 * s, 9.45, -3.15), C("#e8dcc0"), rot=(0, 0, 14 * s), **DETAIL)

    for s, S in SIDES:
        pivot = (1.85 * s, 6.8, -0.8)
        with a.bone(f"Wing{S}", "Body", pivot):
            a.bevel(f"Wing{S}", (0.6, 3.8, 5.2), (2.1 * s, 5.6, 1.0), dark, b=0.25)
            a.box(f"WingBand{S}", (0.64, 1.0, 4.4), (2.12 * s, 6.7, 0.8), brown, role="Secondary")
            for i, (y, length) in enumerate([(4.2, 3.2), (4.75, 2.7), (5.3, 2.2)]):
                a.box(f"Primary{i}{S}", (0.5, 0.5, length), (2.0 * s, y, 3.4 + length / 2), dark, rot=(12, 0, 0))
                a.box(f"PrimaryGold{i}{S}", (0.54, 0.54, 0.8), (2.0 * s, y + 0.37 + 0.22 * (length / 2) * 0.4,
                                                                 3.4 + length - 0.3), GOLD, rot=(12, 0, 0), **GLOW)
        with a.bone(f"Leg{S}", "Body", (0.8 * s, 3.2, 0.6)):
            a.post(f"Leg{S}", (0.55, 3.2, 0.55), (0.8 * s, 1.8, 0.6), beak, b=0.15, role="Accent")
            a.box(f"Feathered{S}", (0.9, 0.9, 0.9), (0.8 * s, 3.1, 0.6), brown)
            for j, yaw in enumerate((-25, 0, 25)):
                R = angles(0, yaw, 0)
                a.box(f"Toe{j}{S}", (0.32, 0.3, 1.3), add((0.8 * s, 0.15, 0.6), apply(R, (0, 0, -0.6))), beak, R=R,
                      role="Accent")
                a.wedge(f"Talon{j}{S}", (0.3, 0.3, 0.4), add((0.8 * s, 0.15, 0.6), apply(R, (0, 0, -1.4))), EYE,
                        R=R, **DETAIL)
    a.ride_height, a.ride_z = 7.8, 0.5
    # Wind swirls and drifting golden feathers.
    fx(a, "Body",
       emitter("Wind", C("#ffffff"), rate=3, lifetime=(0.8, 1.4), speed=(2, 4), sizes=((0, 0.8), (1, 2.4)),
               transparency=((0, 0.6), (1, 1)), light=0, spread=60, rot_speed=(-200, 200)),
       emitter("GoldFeathers", GOLD, rate=1.5, lifetime=(2, 3), speed=(0.3, 0.8), sizes=((0, 0.45), (1, 0.35)),
               transparency=((0, 0.1), (1, 1)), accel=(0.4, -1.0, 0), rot_speed=(-180, 180), color2=GOLD_HOT,
               texture=SPARKLE_TEXTURE))
    for s, S in SIDES:
        p = find(a, f"PrimaryGold0{S}")["p"]
        trail(a, f"PrimaryGold0{S}", add(p, (0, 0.3, 0)), add(p, (0, -0.3, 0)), GOLD, name=f"WingTrail{S}",
              lifetime=0.4, color2=GOLD_HOT)
    scale_animal(a, 1.15)
    extras(a, attrs={"WalkSpeed": 6})
    return a


def mountain_yak():
    a = Animal("MountainYak", "Mountain Yak", "Epic")
    fur, shag, horn, hoof = C("#4a3426"), C("#6b4c38"), C("#efe6d2"), C("#1e140e")
    red, teal, gold = C("#c4302b"), C("#2bb0a8"), C("#ffd23f")

    a.oct("Body", (5.4, 5.0, 8.6), (0, 6.0, 0.4), fur, b=1.5, bottom=1.0)
    a.oct("Hump", (4.2, 1.6, 3.4), (0, 8.7, -1.6), fur, b=0.7)
    # The long shaggy skirt of hair.
    for s, S in SIDES:
        for j in range(7):
            z = -3.3 + j * 1.15
            a.wedge(f"Shag{j}{S}", (0.5, 1.8 + 0.35 * (j % 2), 1.2), (2.72 * s, 3.8, z), shag, rot=(0, 0, 180),
                    role="Secondary")
    for j in range(4):
        a.wedge(f"ShagBack{j}", (1.2, 1.8, 0.5), (-1.8 + j * 1.2, 3.8, 4.72), shag, rot=(0, 90, 180), role="Secondary")
    # The woven blanket with snow on top, and saddle bags.
    a.bevel("Blanket", (5.5, 0.4, 3.4), (0, 8.55, 1.0), red, b=0.15, role="Accent")
    for s, S in SIDES:
        a.box(f"BlanketSide{S}", (0.2, 2.6, 3.4), (2.76 * s, 7.4, 1.0), red, role="Accent")
        for k, (y, c) in enumerate(((7.9, teal), (7.1, gold), (6.4, teal))):
            a.box(f"BlanketStripe{k}{S}", (0.24, 0.3, 3.44), (2.77 * s, y, 1.0), c, **DETAIL)
    for j, (x, z, w) in enumerate(((-0.9, 0.6, 1.6), (0.7, 1.2, 1.8), (0.0, 1.9, 1.2), (-0.4, 0.2, 1.0))):
        a.bevel(f"Snow{j}", (w, 0.55, w * 0.9), (x, 8.95 + 0.1 * j, z), WHITE, b=0.2)

    with a.bone("Head", "Body", (0, 6.2, -3.6)):
        a.oct("Head", (3.4, 3.2, 3.2), (0, 5.8, -4.8), fur, b=0.9, bottom=0.6)
        a.oct("Muzzle", (2.4, 1.6, 1.0), (0, 5.0, -6.5), shag, b=0.45, role="Secondary")
        a.bevel("Nose", (1.4, 0.5, 0.3), (0, 5.3, -7.05), C("#2a1a12"), b=0.12, **DETAIL)
        for s, S in SIDES:
            a.box(f"Nostril{S}", (0.3, 0.3, 0.1), (0.4 * s, 5.3, -7.22), EYE, **DETAIL)
            a.eye2(f"Eye{S}", (1.2 * s, 6.3, -6.42), w=0.85, h=0.95, iris=C("#5a3216"), lid=fur, lid_drop=0.15)
            a.box(f"Ear{S}", (1.2, 0.5, 0.7), (2.1 * s, 6.2, -4.4), fur, rot=(0, 0, -20 * s))
            pts = [(1.4 * s, 7.0, -4.6), (2.5 * s, 7.3, -4.6), (3.2 * s, 8.2, -4.7), (3.1 * s, 9.2, -4.9)]
            chain(a, f"Horn{S}", pts, [0.75, 0.6, 0.45], horn, role="Accent")
        a.tri("Bangs", (0, 6.9, -6.3), 2.6, 1.0, 0.4, shag, R=angles(0, 0, 180), role="Secondary")
        # A red collar with golden bells.
        a.box("Collar", (3.6, 0.5, 3.0), (0, 4.6, -4.3), red, role="Accent")
        for x in (-0.8, 0.8):
            a.bevel(f"Bell{x > 0}", (0.8, 0.85, 0.7), (x, 3.9, -5.7), gold, b=0.22, role="Accent", reflectance=0.2)

    for s, S in SIDES:
        for z, F in ((-2.6, "F"), (3.0, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (1.75 * s, 3.6, z)):
                a.post(f"Leg{F}{S}", (1.4, 3.2, 1.5), (1.75 * s, 2.0, z), fur, b=0.35)
                a.bevel(f"Hoof{F}{S}", (1.5, 0.6, 1.6), (1.75 * s, 0.3, z), hoof, b=0.2, role="Accent")
    with a.bone("Tail", "Body", (0, 7.4, 4.6)):
        a.box("Tail", (0.6, 2.2, 0.6), (0, 6.4, 4.9), fur, rot=(10, 0, 0))
        a.wedge("TailTuft", (1.0, 1.2, 0.8), (0, 4.9, 5.2), shag, rot=(180, 0, 0), role="Secondary")
    a.ride_height, a.ride_z = 9.2, 0.6
    fx(a, "Snow1", emitter("SnowSprinkle", WHITE, rate=3, lifetime=(1.0, 1.6), speed=(0.5, 1.2),
                           sizes=((0, 0.35), (1, 0.2)), transparency=((0, 0.1), (1, 1)), light=0, accel=(0, -4, 0),
                           texture=SPARKLE_TEXTURE))
    unfight(a, "Hump", d=0.03)
    scale_animal(a, 1.15)
    extras(a, attrs={"WalkSpeed": 8})
    return a


def geode_tortoise():
    a = Animal("GeodeTortoise", "Geode Tortoise", "Epic")
    skin, stone, stone2, purple = C("#8aa86a"), C("#8a8fa8"), C("#6f748a"), C("#b46bff")

    a.oct("Body", (5.6, 1.4, 6.4), (0, 1.9, 0.3), stone2, b=0.5)
    a.oct("Shell", (5.2, 2.4, 6.0), (0, 3.4, 0.3), stone, b=1.2, bottom=0.2)
    a.oct("ShellDome", (3.6, 1.0, 4.4), (0, 4.95, 0.3), stone, b=0.5)
    for j, (x, z) in enumerate(((-1.6, -1.6), (1.6, -1.4), (-1.8, 1.8), (1.7, 2.0), (0, -2.6), (0, 3.0))):
        a.box(f"ShellScute{j}", (1.2, 0.2, 1.2), (x, 4.6 + 0.1 * (j % 2), z), stone2, rot=(0, 45, 0), **DETAIL)
    # The cracked-open geode on top, full of glowing crystals.
    a.bevel("GeodeRim", (2.8, 0.5, 3.2), (0, 5.55, 0.3), C("#4a3f6a"), b=0.2)
    a.box("GeodeHollow", (2.2, 0.2, 2.6), (0, 5.82, 0.3), C("#2a1a4a"), **DETAIL)
    for j, (x, z, h, c) in enumerate(((-0.6, -0.4, 2.2, purple), (0.4, 0.3, 3.0, C("#d9a6ff")),
                                      (0.8, -0.7, 1.8, C("#7fd8ff")), (-0.3, 0.9, 2.0, purple),
                                      (0.1, -0.9, 1.4, C("#d9a6ff")))):
        a.shard(f"Geode{j}", (x, 5.8, z), 0.55, h, c, R=angles(8 * (-1) ** j, j * 40, 10 * (-1) ** j), cross=True,
                **GLOW_T)
        a.box(f"GeodeCore{j}", (0.2, h * 0.5, 0.2), (x, 5.8 + h * 0.28, z), WHITE, **GLOW)
    with a.bone("Head", "Body", (0, 2.4, -2.9)):
        a.post("Neck", (1.3, 1.2, 1.6), (0, 2.4, -3.4), skin, b=0.3)
        a.oct("Head", (2.0, 1.8, 2.2), (0, 2.8, -4.5), skin, b=0.5)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (0.62 * s, 3.1, -5.62), w=0.6, h=0.7, iris=C("#5a2a8a"))
            a.box(f"Cheek{S}", (0.4, 0.2, 0.08), (0.75 * s, 2.55, -5.6), PINK, **DETAIL)
        a.box("Smile", (0.6, 0.1, 0.08), (0, 2.35, -5.62), C("#3a2a2a"), **DETAIL)
        a.box("HeadCrystal", (0.3, 0.6, 0.3), (0, 3.85, -4.3), C("#d9a6ff"), rot=(0, 45, 0), **GLOW)
    for s, S in SIDES:
        for z, F in ((-2.0, "F"), (2.4, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (2.3 * s, 1.6, z)):
                a.post(f"Leg{F}{S}", (1.3, 1.6, 1.3), (2.3 * s, 0.8, z), skin, b=0.35)
                for j in (-0.35, 0.35):
                    a.box(f"Claw{F}{S}{j > 0}", (0.25, 0.25, 0.3), (2.3 * s + j, 0.13, z - 0.7), C("#e8e2d4"), **DETAIL)
    with a.bone("Tail", "Body", (0, 2.0, 3.4)):
        a.wedge("Tail", (0.8, 0.6, 1.2), (0, 1.8, 3.9), skin, rot=(0, 180, 0))
    a.ride_height, a.ride_z = 6.2, 0.3
    fx(a, "Geode1",
       light("GeodeLight", purple, brightness=1.4, range_=12, pulse=1.6),
       emitter("CrystalDust", C("#e9d6ff"), rate=6, lifetime=(1.2, 2.0), speed=(0.5, 1.2), sizes=((0, 0.4), (1, 0)),
               accel=(0, 1.2, 0), color2=purple, **SPARK))
    pulse(a, "Geode0", "Geode2", "Geode4", "HeadCrystal", seconds=1.6)
    scale_animal(a, 1.1)
    extras(a, attrs={"WalkSpeed": 4})
    return a


# --------------------------------------------------------------- Legendary ----

def snow_leopard():
    a = Animal("SnowLeopard", "Snow Leopard", "Legendary")
    fur, white = C("#e6e8ee"), C("#ffffff")

    def tail(a):
        with a.bone("Tail", "Body", (0, 5.6, 4.1)):
            pts = [(0, 5.6, 4.1), (0, 5.2, 5.4), (0, 4.8, 6.9), (0, 5.2, 8.3), (0, 6.4, 9.2), (0, 7.9, 9.1)]
            chain(a, "Tail", pts, [1.5, 1.45, 1.4, 1.35, 1.3], fur)
            for j in (1, 3):
                rosette(a, f"TailRosette{j}", add(scale(add(pts[j], pts[j + 1]), 0.5), (0.73, 0, 0)), 0.32, ICE)

    def head(a):
        for s, S in SIDES:
            a.box(f"Whisker{S}", (1.4, 0.08, 0.08), (1.6 * s, 6.25, -6.4), C("#9aa4b8"), rot=(0, 0, -8 * s), **DETAIL)
        rosette(a, "BrowRosette", (0, 9.2, -3.8), 0.4, ICE, normal="y")

    _canine(a, fur, white, inner=PINK, eye={"iris": ICE, "glow": True}, snout="cat", ear=(1.4, 1.2), brows=True,
            brow_color=C("#b8c2d6"), fangs=False, paws=C("#f0f2f6"), tail=tail, head_extra=head)
    with in_bone(a, "Body"):
        for s, S in SIDES:
            for j, (y, z, r) in enumerate(((5.2, -1.4, 0.45), (4.4, 0.3, 0.38), (5.3, 1.6, 0.42), (4.5, 3.0, 0.34))):
                rosette(a, f"Rosette{j}{S}", (2.12 * s, y, z), r, ICE)
        for j, (x, z) in enumerate(((0.6, -0.8), (-0.6, 1.4), (0.5, 2.8))):
            rosette(a, f"BackRosette{j}", (x, 6.42, z), 0.36, ICE, normal="y")
    for s, S in SIDES:
        for F in ("F", "B"):
            paw = find(a, f"Paw{F}{S}")["p"]
            trail(a, f"Paw{F}{S}", add(paw, (0, 0.6, 0)), add(paw, (0, 0.05, 0)), ICE, name=f"FrostTrail{F}{S}",
                  lifetime=0.5, color2=ICE_HOT, transparency=((0, 0.3), (1, 1)))
    fx(a, "Body",
       emitter("Snowflakes", ICE_HOT, rate=8, lifetime=(1.5, 2.5), speed=(0.5, 1.5), sizes=((0, 0.4), (1, 0)),
               accel=(0, -0.5, 0), color2=ICE, rot_speed=(-120, 120), **SPARK),
       light("FrostLight", ICE, brightness=1.0, range_=12, pulse=2.0))
    pulse(a, *[f"Rosette{j}{S}{k}" for j in range(4) for S in "LR" for k in range(4)], seconds=1.8)
    unfight(a, "Belly", "Chest", "FaceMask")
    extras(a, attrs={"WalkSpeed": 13}, highlight=(ICE, ICE_HOT, 1.0, 0.75))
    return a


def frostfang_alpha():
    a = Animal("FrostfangAlpha", "Frostfang Alpha", "Legendary")
    fur, white, dark = C("#dfe9f5"), C("#ffffff"), C("#a9c3e0")

    def head(a):
        # An icicle crown.
        for j, (x, h, t) in enumerate(((-0.9, 1.4, -18), (0, 2.0, 0), (0.9, 1.4, 18))):
            ice_shard(a, f"Crown{j}", (x, 9.3, -3.6), h, 0.5, R=angles(-10, 0, t))

    def tail(a):
        with a.bone("Tail", "Body", (0, 5.6, 4.1)):
            R = angles(-30, 0, 0)
            base = (0, 5.6, 4.1)
            a.taper("Tail", (2.0, 2.0), (1.4, 1.4), 2.8, at(base, R, (0, 0, 1.5)), fur, R=R, r=0.35)
            ice_shard(a, "TailIce", at(base, R, (0, 0, 2.8)), 2.6, 0.9, R=matmul(R, angles(90, 0, 0)))

    _canine(a, fur, white, dark=dark, eye={"iris": ICE, "glow": True}, snout="wolf", ear=(1.8, 2.3),
            paws=C("#e8f2fb"), tail=tail, head_extra=head)
    with in_bone(a, "Body"):
        for j, (z, h) in enumerate(((-2.4, 2.2), (-1.2, 2.6), (0.0, 2.3), (1.2, 2.0), (2.4, 1.6))):
            ice_shard(a, f"BackIce{j}", (0.3 * (-1) ** j, 6.3, z), h, 0.75, R=angles(-15, 0, 12 * (-1) ** j))
    with in_bone(a, "Head"):
        for j, (y, z) in enumerate(((8.8, -2.6), (8.0, -2.0))):
            ice_shard(a, f"NeckIce{j}", (0, y, z), 2.2 - 0.3 * j, 0.7, R=angles(-25, 0, 0))
    for s, S in SIDES:
        for F in ("F", "B"):
            paw = find(a, f"Paw{F}{S}")["p"]
            trail(a, f"Paw{F}{S}", add(paw, (0, 0.6, 0)), add(paw, (0, 0.05, 0)), ICE, name=f"FrostTrail{F}{S}",
                  lifetime=0.5, color2=WHITE, transparency=((0, 0.3), (1, 1)))
    fx(a, "Snout", emitter("FrostBreath", ICE_HOT, texture=SMOKE_TEXTURE, rate=3, lifetime=(0.6, 1.0), speed=(2, 4),
                           spread=15, sizes=((0, 0.6), (1, 2.0)), transparency=((0, 0.5), (1, 1)), light=0.3,
                           emit="Front", color2=ICE, drag=2))
    fx(a, "BackIce2", light("IceLight", ICE, brightness=1.2, range_=14, pulse=1.6),
       emitter("IceGlitter", ICE_HOT, rate=6, lifetime=(0.6, 1.2), speed=(0.3, 1.0), sizes=((0, 0.4), (1, 0)),
               color2=ICE, **SPARK))
    unfight(a, "Belly", "Chest", "FaceMask", "Saddle")
    scale_animal(a, 1.1)
    extras(a, attrs={"WalkSpeed": 14}, highlight=(ICE, ICE_HOT, 1.0, 0.7))
    return a


def little_yeti():
    a = Animal("LittleYeti", "Little Yeti", "Legendary")
    fur, shade, face, horn = C("#f6f8fc"), C("#d5deee"), C("#8fb3e6"), C("#c9cfe8")

    a.oct("Body", (4.4, 4.6, 3.8), (0, 5.2, 0), fur, b=1.4, bottom=1.0)
    a.oct("Belly", (3.0, 3.0, 0.4), (0, 4.8, -1.95), shade, b=0.8, role="Secondary")
    for j, (x, y, z) in enumerate(((-2.2, 6.3, 0), (2.2, 6.3, 0), (-2.0, 4.2, 0.6), (2.0, 4.2, 0.6), (0, 3.0, 1.6),
                                   (0, 7.4, 1.5))):
        a.tuft(f"FurTuft{j}", (x, y, z), (0.8, 1.2, 1.4), fur, R=angles(0, 180 if z > 1 else 90 * (1 if x > 0 else -1), 0))
    with a.bone("Head", "Body", (0, 7.4, -0.2)):
        a.oct("Head", (4.2, 3.8, 3.6), (0, 9.2, -0.3), fur, b=1.3, bottom=0.6)
        a.oct("Face", (3.0, 2.4, 0.4), (0, 9.0, -2.1), face, b=0.7)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (0.7 * s, 9.35, -2.36), w=0.95, h=1.15, iris=C("#3a6fd8"))
            a.box(f"Cheek{S}", (0.5, 0.25, 0.08), (1.1 * s, 8.55, -2.32), C("#ff9ecf"), **DETAIL)
            a.tri(f"Fang{S}", (0.4 * s, 8.2, -2.34), 0.3, 0.35, 0.1, WHITE, R=angles(0, 0, 180), **DETAIL)
            pts = [(1.4 * s, 10.8, -0.3), (2.0 * s, 11.6, -0.2), (2.0 * s, 12.5, 0.0)]
            chain(a, f"Horn{S}", pts, [0.6, 0.45], horn, role="Accent")
        a.box("Mouth", (1.2, 0.2, 0.1), (0, 8.25, -2.32), C("#2a2a50"), **DETAIL)
        a.tuft("HeadFluff", (0, 11.2, 0.4), (2.0, 1.2, 1.6), fur, R=angles(0, 180, 0))
    for s, S in SIDES:
        with a.bone(f"Arm{S}", "Body", (2.4 * s, 6.6, -0.2)):
            a.post(f"Arm{S}", (1.4, 3.2, 1.4), (2.7 * s, 5.2, -0.4), fur, b=0.45)
            a.oct(f"Hand{S}", (1.3, 1.0, 1.3), (2.75 * s, 3.4, -0.6), face, b=0.35)
        with a.bone(f"Leg{S}", "Body", (1.1 * s, 3.2, 0.2)):
            a.post(f"Leg{S}", (1.5, 2.4, 1.5), (1.1 * s, 2.0, 0.2), fur, b=0.45)
            a.bevel(f"Foot{S}", (1.7, 0.8, 2.2), (1.1 * s, 0.4, -0.1), face, b=0.3)
    with in_bone(a, "ArmR"):
        a.oct("Snowball", (1.6, 1.6, 1.6), (2.8, 2.5, -1.2), WHITE, b=0.5)
    a.ride_height, a.ride_z = 7.6, 0.2
    fx(a, "Body",
       emitter("Snowflakes", WHITE, rate=6, lifetime=(1.5, 2.5), speed=(0.5, 1.5), sizes=((0, 0.45), (1, 0)),
               accel=(0, -0.8, 0), color2=ICE, rot_speed=(-120, 120), **SPARK),
       light("FrostLight", ICE, brightness=0.8, range_=10))
    unfight(a, "Belly", "Face", d=0.03)
    scale_animal(a, 1.05)
    extras(a, attrs={"WalkSpeed": 8}, highlight=(ICE, WHITE, 1.0, 0.75))
    return a


# ------------------------------------------------------------------ Mythic ----

def sky_griffin():
    a = Animal("SkyGriffin", "Sky Griffin", "Mythic")
    gold, deep, white, beak = C("#f2b632"), C("#c9861c"), C("#fffaf0"), C("#ffb52e")
    feather = [C("#fff6e0"), C("#ffffff"), C("#f2e6c8"), C("#ffe9a8"), C("#ffd77a")]

    # Lion body with feathered chest and a golden circlet of armour.
    a.oct("Body", (4.6, 4.2, 8.2), (0, 5.6, 0.6), gold, b=1.2, bottom=0.8)
    a.bevel("Belly", (4.66, 1.3, 7.2), (0, 4.1, 0.7), C("#ffe39a"), b=0, bottom=0.83, role="Secondary")
    a.oct("ChestFeathers", (4.2, 4.4, 1.6), (0, 6.0, -3.4), white, b=1.0, bottom=0.6, role="Secondary")
    for j, x in enumerate((-1.2, 0, 1.2)):
        a.tri(f"ChestPlume{j}", (x, 3.9, -4.0), 1.3, 1.2 - 0.2 * abs(x), 0.6, white, R=angles(0, 0, 180),
              role="Secondary")
    a.bevel("Peytral", (3.4, 1.2, 0.3), (0, 6.6, -4.28), GOLD, b=0.2, role="Accent", reflectance=0.25)
    a.box("PeytralGem", (0.7, 0.7, 0.3), (0, 6.6, -4.45), C("#4fe3ff"), rot=(0, 0, 45), **GLOW)
    for s, S in SIDES:
        for j, z in enumerate((-1.0, 1.4)):
            a.box(f"FlankFeather{j}{S}", (0.2, 1.4, 1.8), (2.34 * s, 6.2, z), white, rot=(20, 0, 0), role="Secondary")
    # A royal saddle.
    a.bevel("Saddle", (3.6, 0.8, 3.2), (0, 8.0, 1.0), C("#c4302b"), b=0.3, role="Accent")
    a.box("SaddleTrim", (3.9, 0.3, 3.5), (0, 7.65, 1.0), GOLD, role="Accent", reflectance=0.25)
    for s, S in SIDES:
        a.box(f"Drape{S}", (0.3, 2.0, 3.0), (2.4 * s, 6.85, 1.0), C("#c4302b"), role="Accent")
        a.box(f"DrapeTrim{S}", (0.34, 0.3, 3.04), (2.41 * s, 5.85, 1.0), GOLD, role="Accent")
        pixel_star(a, f"DrapeStar{S}", (2.58 * s, 7.0, 1.0), 1.0, GOLD_HOT, R=angles(0, 90, 0))

    with a.bone("Head", "Body", (0, 7.4, -3.2)):
        a.box("Neck", (3.2, 3.2, 2.6), (0, 7.9, -3.6), white)
        a.bevel("Head", (4.2, 3.7, 3.8), (0, 10.0, -4.5), white, b=1.0, bottom=0.4)
        a.bevel("Beak", (2.2, 1.3, 2.2), (0, 9.5, -7.4), beak, b=0.4, role="Accent")
        a.box("LowerBeak", (1.8, 0.6, 1.6), (0, 8.7, -7.2), C("#e89a1e"), role="Accent")
        a.box("BeakHook", (1.2, 1.0, 0.7), (0, 8.9, -8.6), beak, role="Accent")
        a.box("BeakGold", (2.26, 0.3, 0.5), (0, 9.95, -6.4), GOLD, role="Accent", reflectance=0.3)
        for i, (x, h) in enumerate(((0, 2.4), (0.9, 1.9), (-0.9, 1.9), (1.6, 1.3), (-1.6, 1.3))):
            plate(a, f"Crest{i}", (x, 11.4, -3.6), (x * 1.3, 11.4 + h, -2.2), 0.7, 0.3, GOLD_HOT if i % 2 else GOLD,
                  up=(1, 0, 0), role="Secondary")
        a.box("Circlet", (4.3, 0.45, 3.9), (0, 11.15, -4.5), GOLD, role="Accent", reflectance=0.3)
        a.box("CircletGem", (0.6, 0.6, 0.2), (0, 11.35, -6.48), C("#4fe3ff"), rot=(0, 0, 45), **GLOW)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (1.25 * s, 10.3, -6.45), w=1.05, h=1.25, iris=C("#ffb21c"), glow=True)
            a.box(f"Brow{S}", (1.2, 0.3, 0.25), (1.25 * s, 11.0, -6.46), deep, rot=(0, 0, 14 * s), **DETAIL)

    for s, S in SIDES:
        root = (2.0 * s, 8.0, -1.4)
        arm = [root, (3.8 * s, 10.4, -1.0), (5.8 * s, 12.2, 0.2), (7.6 * s, 13.2, 1.8), (8.8 * s, 13.6, 3.4)]
        feather_wing(a, s, S, root, arm, [GOLD] + feather, [GOLD, GOLD_HOT], edge=GOLD_HOT, tip_glow=True,
                     width=1.45, scale_k=1.15, rows=(10, 8))

    for s, S in SIDES:
        with a.bone(f"LegF{S}", "Body", (1.5 * s, 4.2, -2.4)):
            a.box(f"LegF{S}", (1.5, 1.8, 1.5), (1.5 * s, 3.4, -2.4), white)
            a.box(f"ShinF{S}", (1.1, 2.6, 1.1), (1.5 * s, 1.5, -2.4), beak, role="Accent")
            a.box(f"Bracer{S}", (1.3, 0.5, 1.3), (1.5 * s, 2.3, -2.4), GOLD, role="Accent", reflectance=0.25)
            a.box(f"TalonF{S}", (1.7, 0.5, 1.9), (1.5 * s, 0.25, -2.7), beak, role="Accent")
            for i, dx in enumerate((-0.5, 0.0, 0.5)):
                a.wedge(f"Claw{i}{S}", (0.4, 0.4, 0.7), (1.5 * s + dx, 0.2, -3.95), C("#3a2a1a"), **DETAIL)
        with a.bone(f"LegB{S}", "Body", (1.7 * s, 4.1, 3.6)):
            a.bevel(f"LegB{S}", (1.7, 3.8, 1.9), (1.7 * s, 2.2, 3.6), gold, b=0.4)
            a.box(f"PawB{S}", (1.9, 0.6, 2.3), (1.7 * s, 0.3, 3.3), gold)
    with a.bone("Tail", "Body", (0, 6.6, 4.7)):
        pts = [(0, 6.6, 4.7), (0, 6.0, 6.2), (0, 5.8, 7.6), (0, 6.6, 8.8)]
        chain(a, "Tail", pts, [0.6, 0.55, 0.5], gold)
        a.oct("TailTuft", (1.6, 1.6, 1.6), (0, 7.2, 9.6), deep, b=0.5, role="Secondary")
        a.box("TailRing", (0.9, 0.9, 0.5), (0, 6.6, 8.8), GOLD, role="Accent", reflectance=0.3)

    # Orbit: two rings of wind and eight golden feathers that circle it.
    with a.bone("Orbit", "Body", (0, 6.0, 0.6)):
        for r_i, (r, y, n) in enumerate(((6.6, 3.0, 18), (7.8, 9.4, 22))):
            for i in range(n):
                ang = 2 * math.pi * i / n
                if i % 3 == 2:
                    continue
                p = (math.cos(ang) * r, y + 0.5 * math.sin(ang * 2), 0.6 + math.sin(ang) * r)
                a.box(f"WindRing{r_i}_{i}", (0.25, 0.25, 2 * math.pi * r / n * 0.9), p, WHITE,
                      R=angles(0, -math.degrees(ang), 0), **GLOW_T)
        for i in range(8):
            ang = 2 * math.pi * i / 8 + 0.2
            p = (math.cos(ang) * 5.6, 6.2 + 1.2 * math.sin(ang * 3), 0.6 + math.sin(ang) * 5.6)
            plate(a, f"OrbitFeather{i}", p, add(p, (0, 1.8, 0.4)), 0.6, 0.14, GOLD_HOT if i % 2 else GOLD,
                  up=(math.cos(ang), 0, math.sin(ang)), **GLOW)

    # -- showpiece detail ---------------------------------------------------------------------------
    cream = C("#fff1cc")
    # Wing tip joints (at the wrist), so the outer wing trails behind every beat.
    for s, S in SIDES:
        a.bones[f"WingTip{S}"] = {"parent": f"Wing{S}", "pivot": (5.8 * s, 12.2, 0.2)}
        for part in a.parts:
            if part["name"].startswith((f"Wing{S}Primary", f"Wing{S}Arm2", f"Wing{S}Arm3", f"Wing{S}Edge2",
                                        f"Wing{S}Edge3")):
                part["bone"] = f"WingTip{S}"
        # A second, smaller layer of feathers over the coverts, a light vane down each primary, and gold
        # bands on the wing bones.
        with in_bone(a, f"Wing{S}"):
            for i in range(10):
                cv = find(a, f"Wing{S}Covert{i}")
                plate(a, f"Wing{S}Marginal{i}", add(cv["p"], (0, 0.18, -0.1)),
                      add(cv["p"], (0.1 * s, 0.05, 0.75)), 0.7, 0.14, cream if i % 2 else WHITE,
                      up=(0, 1, 0), role="Secondary", shadow=False)
            for i in range(3):
                q = find(a, f"Wing{S}Arm{i}")["p"]
                a.box(f"Wing{S}Band{i}", (0.75, 0.75, 0.75), q, GOLD, role="Accent", reflectance=0.25)
        with in_bone(a, f"WingTip{S}"):
            for i in range(8):
                pr = find(a, f"Wing{S}Primary{i}")
                a.box(f"Wing{S}Vane{i}", (pr["size"][0] * 0.8, pr["size"][1] + 0.04, 0.12), pr["p"], GOLD_HOT,
                      R=pr["R"], **DETAIL)
    with in_bone(a, "Body"):
        # Feather scales over the chest under the golden peytral, white to gold.
        for r in range(3):
            n = 5 if r % 2 == 0 else 4
            for c in range(n):
                x = -1.7 + (c + 0.5) * 3.4 / n
                a.tri(f"ChestScale{r}_{c}", (x, 5.7 - r * 0.7, -4.22), 0.75, 0.8, 0.14,
                      (WHITE, cream, GOLD_HOT)[r], R=angles(0, 0, 180), role="Secondary", shadow=False)
        # Rows of flank feathers in front of and behind the drape.
        for s, S in SIDES:
            for r in range(3):
                for j, z in enumerate((-3.0, -1.6, 3.0, 4.2)):
                    p0 = (2.33 * s, 7.2 - r * 0.95, z)
                    plate(a, f"FlankRow{S}{r}_{j}", p0, add(p0, (0.12 * s, -1.0, 0.8)), 0.8, 0.14,
                          (WHITE, cream, C("#ffe39a"))[r], up=(s, 0, 0), role="Secondary", shadow=False)
            # A fringe of golden fur along the belly.
            for j in range(7):
                a.wedge(f"BellyFringe{S}{j}", (0.35, 0.9, 0.9), (2.0 * s, 3.4, -2.0 + j * 1.0), deep,
                        rot=(0, 0, 180), role="Secondary")
        for j in range(3):
            a.oct(f"SpineTuft{j}", (1.0, 0.6, 1.0), (0, 7.85, 3.0 + j * 0.75), deep, b=0.25, role="Secondary")
        # Saddle gear: stirrups, gold studs, a horn and tassels on the drapes, and a sun medallion behind.
        a.box("SaddleHorn", (0.6, 0.9, 0.6), (0, 8.75, -0.4), C("#8a2a1e"), role="Accent")
        a.box("SaddleHornCap", (0.8, 0.25, 0.8), (0, 9.25, -0.4), GOLD, role="Accent", reflectance=0.3)
        for j in range(6):
            a.box(f"SaddleStud{j}", (0.3, 0.3, 0.3), ((-1.5 + j * 0.6), 8.42, 2.55), GOLD, **DETAIL)
        for s, S in SIDES:
            a.rod(f"StirrupStrap{S}", (2.1 * s, 7.9, 0.6), (2.6 * s, 5.4, 0.6), 0.2, C("#5a3418"), **DETAIL)
            a.box(f"Stirrup{S}", (0.7, 0.25, 0.9), (2.65 * s, 5.2, 0.6), GOLD, role="Accent", reflectance=0.3)
            for j in range(4):
                a.wedge(f"Tassel{S}{j}", (0.14, 0.7, 0.35), (2.42 * s, 5.35, -0.2 + j * 0.65), GOLD_HOT,
                        rot=(0, 90, 180), **DETAIL)
        a.cyl("SunMedallion", 0.25, 1.6, (0, 8.1, 2.75), GOLD, R=angles(0, 90, 0), role="Accent", reflectance=0.3)
        a.box("SunMedallionGem", (0.6, 0.6, 0.2), (0, 8.1, 2.92), C("#4fe3ff"), rot=(0, 0, 45), **GLOW)
        for j in range(8):
            ang = j * 45
            R = angles(0, 0, ang)
            a.box(f"SunRay{j}", (0.18, 0.6, 0.12), add((0, 8.1, 2.9), apply(R, (0, 1.05, 0))), GOLD_HOT, R=R,
                  **GLOW)
    with in_bone(a, "Head"):
        # A ruff of feathers round the neck.
        for k in range(14):
            ang = 2 * math.pi * k / 14
            c, s_ = math.cos(ang), math.sin(ang)
            p0 = (c * 1.5, 8.9, -3.6 + s_ * 1.5)
            p1 = (c * 2.4, 7.9, -3.5 + s_ * 2.4)
            plate(a, f"Ruff{k}", p0, p1, 0.75, 0.14, WHITE if k % 2 else cream, up=(c * 0.4, 1, s_ * 0.4),
                  role="Secondary", shadow=False)
            plate(a, f"RuffTip{k}", p1, add(p1, (c * 0.5, -0.35, s_ * 0.5)), 0.45, 0.12, GOLD_HOT,
                  up=(c * 0.4, 1, s_ * 0.4), role="Accent", shadow=False)
        for s, S in SIDES:
            for j in range(3):
                p0 = (2.05 * s, 10.4 - j * 0.5, -5.2 + j * 0.25)
                plate(a, f"Cheek{S}{j}", p0, add(p0, (0.3 * s, 0.15, 1.5)), 0.5, 0.12, (WHITE, cream, GOLD_HOT)[j],
                      up=(s, 0, 0), role="Secondary", shadow=False)
            for j in range(2):
                p0 = (1.7 * s, 11.6, -3.9 + j * 0.6)
                plate(a, f"EarTuft{S}{j}", p0, add(p0, (0.5 * s, 1.4 - 0.3 * j, 0.6)), 0.5, 0.14, GOLD if j else GOLD_HOT,
                      up=(s, 0, 0), role="Accent", shadow=False)
            a.box(f"Nostril{S}", (0.22, 0.18, 0.1), (0.45 * s, 9.75, -8.5), C("#7a4a1a"), **DETAIL)
        for j in range(5):
            x = (j - 2) * 0.8
            a.wedge(f"CircletSpike{j}", (0.3, 0.7 - 0.12 * abs(j - 2), 0.3), (x, 11.7, -6.45), GOLD, role="Accent",
                    reflectance=0.25)
    for s, S in SIDES:
        with in_bone(a, f"LegF{S}"):
            for j in range(3):
                a.box(f"ShinScale{S}{j}", (1.18, 0.16, 1.18), (1.5 * s, 0.9 + j * 0.55, -2.4), C("#e89a1e"), **DETAIL)
            for j in range(4):
                ang = j * math.pi / 2
                p0 = (1.5 * s + math.cos(ang) * 0.75, 4.1, -2.4 + math.sin(ang) * 0.75)
                plate(a, f"Pants{S}{j}", p0, add(p0, (math.cos(ang) * 0.3, -1.3, math.sin(ang) * 0.3)), 0.8, 0.14,
                      WHITE, up=(math.cos(ang), 0, math.sin(ang)), role="Secondary", shadow=False)
        with in_bone(a, f"LegB{S}"):
            for j, dx in enumerate((-0.6, 0.0, 0.6)):
                a.box(f"Toe{S}{j}", (0.55, 0.5, 0.7), (1.7 * s + dx, 0.3, 2.05), gold)
                a.wedge(f"PawClaw{S}{j}", (0.3, 0.3, 0.45), (1.7 * s + dx, 0.2, 1.55), C("#3a2a1a"), **DETAIL)
            for j in range(2):
                a.wedge(f"HockTuft{S}{j}", (0.3, 0.8, 0.7), (1.7 * s + (0.6 if j else -0.6), 2.0, 4.65), deep,
                        rot=(0, 0, 180), role="Secondary")
    with in_bone(a, "Tail"):
        for j in range(5):
            ang = (j - 2) * 22
            R = angles(0, 0, ang)
            base = (0, 7.6, 9.9)
            tip = add(base, apply(R, (0, 1.8, 0.6)))
            plate(a, f"TailPlume{j}", base, tip, 0.55, 0.14, GOLD_HOT if j % 2 else GOLD, up=(0, 0, 1),
                  role="Accent", shadow=False)
        a.box("TailRing2", (0.8, 0.8, 0.5), (0, 5.85, 7.0), GOLD, role="Accent", reflectance=0.3)
    with in_bone(a, "Head"):
        for j, (x, h) in enumerate(((0.45, 2.1), (-0.45, 2.1), (1.25, 1.5), (-1.25, 1.5))):
            plate(a, f"CrestBack{j}", (x, 11.3, -2.9), (x * 1.4, 11.3 + h, -1.6), 0.6, 0.26, cream if j % 2 else WHITE,
                  up=(1, 0, 0), role="Secondary", shadow=False)
    with in_bone(a, "Body"):
        # A golden chain hanging across the chest from shoulder to shoulder.
        for j in range(9):
            t = j / 8
            x = -2.0 + 4.0 * t
            y = 7.4 - 1.3 * math.sin(math.pi * t)
            a.box(f"ChestChain{j}", (0.36, 0.24, 0.2), (x, y, -4.48), GOLD if j % 2 else GOLD_HOT,
                  rot=(0, 0, (0.5 - t) * 70), role="Accent", reflectance=0.3)
        for s, S in SIDES:
            for j in range(7):
                a.wedge(f"BellyFringeB{S}{j}", (0.3, 0.7, 0.8), (1.4 * s, 3.45, -1.5 + j * 1.0), gold,
                        rot=(0, 0, 180), role="Secondary")
    for s, S in SIDES:
        with in_bone(a, f"LegF{S}"):
            for i, dx in enumerate((-0.5, 0.0, 0.5)):
                a.box(f"ClawGlow{S}{i}", (0.22, 0.22, 0.22), (1.5 * s + dx, 0.15, -4.3), GOLD_HOT, **GLOW)
            a.box(f"BracerGem{S}", (0.35, 0.35, 0.2), (1.5 * s, 2.3, -3.06), C("#4fe3ff"), rot=(0, 0, 45), **GLOW)
    with in_bone(a, "Orbit"):
        for i in range(4):
            ang = 2 * math.pi * i / 4 + 0.6
            p0 = (math.cos(ang) * 7.0, 8.4 + 0.8 * math.sin(ang * 2), 0.6 + math.sin(ang) * 7.0)
            plate(a, f"OrbitFeatherHigh{i}", p0, add(p0, (0, 1.6, 0.4)), 0.55, 0.14, GOLD_HOT if i % 2 else WHITE,
                  up=(math.cos(ang), 0, math.sin(ang)), **GLOW)
        n = 20
        for i in range(n):
            if i % 3 == 1:
                continue
            ang = 2 * math.pi * i / n + 0.15
            p0 = (math.cos(ang) * 9.2, 6.0 + 0.8 * math.sin(ang * 3), 0.6 + math.sin(ang) * 9.2)
            a.box(f"WindRing2_{i}", (0.22, 0.22, 2 * math.pi * 9.2 / n * 0.8), p0, GOLD_HOT,
                  R=angles(0, -math.degrees(ang), 0), **GLOW_T)

    a.ride_height, a.ride_z = 8.6, 1.0
    scale_animal(a, 1.25)
    unfight(a, "Belly", "ChestFeathers", "Saddle", d=0.04)

    # -- heavy effects ----------------------------------------------------------------
    k = 1.25
    p = lambda n: find(a, n)["p"]
    fx(a, "Body",
       light("SunLight", GOLD, brightness=1.8, range_=22, pulse=2.0),
       emitter("GoldenAura", GOLD_HOT, rate=14, lifetime=(1.2, 2.0), speed=(0.6, 1.6), sizes=((0, 0.6), (1, 0)),
               accel=(0, 1.6, 0), color2=GOLD, **SPARK),
       emitter("FallingFeathers", C("#fff6e0"), rate=3, lifetime=(2.5, 3.5), speed=(0.3, 0.9),
               sizes=((0, 0.6), (1, 0.5)), transparency=((0, 0.05), (0.8, 0.2), (1, 1)), light=0.5,
               accel=(0.5, -1.2, 0), drag=1, rot_speed=(-180, 180), color2=GOLD, texture=SPARKLE_TEXTURE))
    fx(a, "PeytralGem", light("GemLight", C("#4fe3ff"), brightness=1.0, range_=8, pulse=1.2))
    for s, S in SIDES:
        fx(a, f"PawB{S}", emitter("Gust", WHITE, texture=SMOKE_TEXTURE, rate=2, lifetime=(0.6, 1.0), speed=(2, 4),
                                  spread=70, sizes=((0, 1.0), (1, 2.6)), transparency=((0, 0.6), (1, 1)), light=0,
                                  emit="Bottom"))
        fx(a, f"Wing{S}PrimaryTip3", emitter("WingGold", GOLD_HOT, rate=10, lifetime=(0.8, 1.4), speed=(0.3, 1.0),
                                             sizes=((0, 0.5), (1, 0)), color2=GOLD, accel=(0, -1.5, 0), **SPARK))
        tip = p(f"Wing{S}PrimaryTip5")
        trail(a, f"Wing{S}PrimaryTip5", add(tip, (0, 0.6 * k, 0)), add(tip, (0, -0.6 * k, 0)), GOLD_HOT,
              name=f"WingTrail{S}", lifetime=0.6, color2=GOLD, transparency=((0, 0.1), (1, 1)))
        # Wind streams spiralling from the wing roots up into the sky.
        root = p(f"Wing{S}Arm0")
        beam(a, f"Wing{S}Arm0", root, f"Wing{S}Arm0", add(root, (0, 12 * k, 0)), WHITE, name=f"Updraft{S}",
             width=(1.4, 0.1), curve=(4 * (1 if s > 0 else -1), -3), transparency=((0, 0.5), (1, 1)), segments=12,
             color2=GOLD_HOT, texture=SPARKLE_TEXTURE, texture_speed=2.5)
    tuft = p("TailTuft")
    trail(a, "TailTuft", add(tuft, (0, 0.6 * k, 0)), add(tuft, (0, -0.6 * k, 0)), GOLD, name="TailTrail",
          lifetime=0.5, color2=GOLD_HOT)
    for i in (0, 4):
        fx(a, f"OrbitFeather{i}", light(f"FeatherLight{i}", GOLD, brightness=0.8, range_=8, pulse=1.0))
        fp = p(f"OrbitFeather{i}")
        trail(a, f"OrbitFeather{i}", add(fp, (0, 0.6 * k, 0)), add(fp, (0, -0.4 * k, 0)), GOLD_HOT,
              name=f"FeatherTrail{i}", lifetime=0.7, color2=GOLD)
    pulse(a, "PeytralGem", "CircletGem", "EyeLIris", "EyeRIris", seconds=1.4)
    extras(a, attrs={"WalkSpeed": 15, "OrbitSpeed": 0.6, "FlapSpeed": 1.4, "FlapAngle": 10},
           highlight=(GOLD, GOLD_HOT, 1.0, 0.45))
    return a


def glacier_mammoth():
    a = Animal("GlacierMammoth", "Glacier Mammoth", "Mythic")
    fur, shag, dark, plate_c = C("#cfe3f2"), C("#a9c8e2"), C("#5f86b0"), C("#e6f2ff")

    a.oct("Body", (6.4, 6.0, 9.0), (0, 7.2, 0.6), fur, b=2.0, bottom=1.2)
    a.oct("Hump", (5.0, 2.0, 4.2), (0, 10.4, -1.2), fur, b=0.9)
    for s, S in SIDES:
        for j in range(8):
            z = -3.4 + j * 1.15
            a.wedge(f"Shag{j}{S}", (0.5, 2.2 + 0.4 * (j % 2), 1.2), (3.22 * s, 4.6, z), shag, rot=(0, 0, 180),
                    role="Secondary")
    # The glacier growing on its back: big translucent ice crystals with bright cores.
    for j, (x, z, h, t) in enumerate(((0, -1.6, 4.6, 0), (-1.3, -0.4, 3.4, -14), (1.3, -0.2, 3.6, 14),
                                      (0, 1.0, 3.8, 0), (-1.1, 2.2, 2.6, -18), (1.0, 2.6, 2.4, 18),
                                      (0, 3.6, 2.0, 0), (0.2, -2.8, 2.8, 6))):
        ice_shard(a, f"Glacier{j}", (x, 10.8 - 0.12 * abs(z), z), h, 1.0 + 0.1 * (j % 3), R=angles(-6 * (z > 0), 0, t))
    # Ice armour: frozen plates on its shoulders.
    for s, S in SIDES:
        a.bevel(f"IcePlate{S}", (0.4, 3.0, 3.2), (3.26 * s, 7.8, -2.2), plate_c, b=0.2, material="Glass",
                transparency=0.15, reflectance=0.3, role="Glow")
        a.box(f"IcePlateRune{S}", (0.44, 1.6, 0.25), (3.28 * s, 7.8, -2.2), ICE, **GLOW)

    with a.bone("Head", "Body", (0, 8.0, -3.8)):
        a.oct("Head", (5.0, 5.2, 4.4), (0, 9.4, -5.2), fur, b=1.8, bottom=0.8)
        a.oct("Brow", (4.4, 1.4, 1.2), (0, 11.0, -7.1), shag, b=0.5, role="Secondary")
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (1.25 * s, 9.9, -7.45), w=1.0, h=1.2, iris=ICE_DEEP, glow=True)
            a.box(f"Cheek{S}", (0.6, 0.3, 0.1), (1.8 * s, 9.05, -7.4), C("#ff9ecf"), **DETAIL)
            a.oct(f"Ear{S}", (0.6, 3.0, 2.6), (2.7 * s, 9.0, -4.6), shag, b=0.6, role="Secondary")
            # Glowing ice tusks, curving out, up and forward.
            pts = [(1.2 * s, 7.6, -7.0), (1.6 * s, 6.6, -8.2), (2.0 * s, 6.6, -9.6), (2.1 * s, 7.6, -10.6),
                   (1.8 * s, 8.9, -10.9)]
            chain(a, f"Tusk{S}", pts, [0.85, 0.75, 0.6, 0.45], ICE_HOT, material="Neon", role="Glow", shadow=False)
            a.box(f"TuskBand{S}", (1.0, 0.3, 1.0), pts[1], C("#8fd8ff"), R=aim(sub(pts[2], pts[0])), **GLOW)
        # The trunk, curling at the end.
        pts = [(0, 8.4, -7.2), (0, 7.0, -7.8), (0, 5.6, -8.0), (0, 4.4, -7.8), (0, 3.6, -8.4), (0, 3.7, -9.3)]
        chain(a, "Trunk", pts, [1.5, 1.35, 1.2, 1.05, 0.9], fur)
        for j in range(1, 5):
            a.box(f"TrunkRing{j}", (1.6 - 0.15 * j, 0.14, 1.6 - 0.15 * j), pts[j], dark,
                  R=aim(sub(pts[j + 1], pts[j - 1])), **DETAIL)
        a.box("Crown", (1.6, 0.6, 1.6), (0, 12.2, -5.0), ICE, rot=(0, 45, 0), **GLOW_T)

    for s, S in SIDES:
        for z, F in ((-2.6, "F"), (3.4, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (2.1 * s, 4.6, z)):
                a.post(f"Leg{F}{S}", (2.1, 4.4, 2.2), (2.1 * s, 2.4, z), fur, b=0.6)
                a.bevel(f"Greave{F}{S}", (0.3, 1.6, 1.8), (2.1 * s + 1.12 * s, 2.0, z), plate_c, b=0.12,
                        material="Glass", transparency=0.2, reflectance=0.3, role="Glow")
                a.bevel(f"Foot{F}{S}", (2.4, 0.7, 2.5), (2.1 * s, 0.35, z), shag, b=0.25, role="Secondary")
                for j in (-0.6, 0.0, 0.6):
                    a.box(f"Nail{F}{S}{j}", (0.4, 0.4, 0.2), (2.1 * s + j, 0.3, z - 1.28), WHITE, **DETAIL)
    with a.bone("Tail", "Body", (0, 8.4, 5.0)):
        a.box("Tail", (0.6, 2.4, 0.6), (0, 7.3, 5.3), fur, rot=(12, 0, 0))
        ice_shard(a, "TailIce", (0, 6.1, 5.6), 1.4, 0.7, R=angles(180, 0, 0), glow=False)

    # Orbit: a ring of floating ice shards and a frozen rune circle on the ground.
    with a.bone("Orbit", "Body", (0, 7.0, 0.6)):
        for i in range(10):
            ang = 2 * math.pi * i / 10
            p = (math.cos(ang) * 8.0, 7.0 + 1.6 * math.sin(ang * 2), 0.6 + math.sin(ang) * 8.0)
            ice_shard(a, f"OrbitIce{i}", p, 2.2 if i % 2 else 1.5, 0.8, R=angles(25, -math.degrees(ang), 20),
                      glow=i % 2 == 0)
        ground_ring(a, "FrostRing", (0, 0.12, 0.6), 9.0, ICE, n=26, size=(0.4, 0.08, 1.6), transparency=0.2)
        ground_ring(a, "FrostRingIn", (0, 0.12, 0.6), 7.4, ICE_HOT, n=18, size=(0.3, 0.08, 1.2), transparency=0.35)

    # -- showpiece detail ---------------------------------------------------------------------------
    blanket, blanket2 = C("#2f5f9a"), C("#3f78b8")
    with in_bone(a, "Body"):
        for s, S in SIDES:
            # A second, higher layer of shaggy fur behind the ice plate.
            for j in range(5):
                z = 0.25 + j * 1.15
                a.wedge(f"ShagHigh{j}{S}", (0.45, 1.9, 1.2), (3.24 * s, 6.3, z), fur if j % 2 else shag,
                        rot=(0, 0, 180), role="Secondary")
            # More ice armour along the flanks, each with a glowing rune.
            for j, (y, z) in enumerate(((5.6, -2.0), (6.0, 3.8))):
                a.bevel(f"FlankPlate{S}{j}", (0.36, 1.8, 2.0), (3.28 * s, y, z), plate_c, b=0.15, material="Glass",
                        transparency=0.15, reflectance=0.3, role="Glow")
                a.box(f"FlankRune{S}{j}", (0.4, 0.9, 0.2), (3.3 * s, y, z), ICE, **GLOW)
            # Icicles hanging under the belly.
            for j in range(8):
                h = 0.6 + 0.5 * ((j * 7) % 3) / 2
                a.wedge(f"BellyIcicle{S}{j}", (0.3, h, 0.25), (2.3 * s, 4.15 - h / 2, -3.0 + j * 1.0), ICE,
                        rot=(180, 0, 0), material="Glass", transparency=0.2, role="Glow", shadow=False)
        # A shaggy beard on the chest and a fringe over the rump.
        for j in range(6):
            a.wedge(f"ChestBeard{j}", (0.8, 2.0, 0.45), (-2.0 + j * 0.8, 4.9, -3.95), shag if j % 2 else fur,
                    rot=(0, 90, 180), role="Secondary")
        for j in range(5):
            a.wedge(f"ChestBeardHigh{j}", (0.8, 1.6, 0.4), (-1.6 + j * 0.8, 6.2, -4.0), fur if j % 2 else shag,
                    rot=(0, 90, 180), role="Secondary")
        for j in range(7):
            a.wedge(f"RumpShag{j}", (0.8, 2.0, 0.45), (-2.4 + j * 0.8, 5.2, 5.15), shag if j % 2 else fur,
                    rot=(0, 90, 180), role="Secondary")
        # A woven blanket draped over its back behind the glacier, with tassels and glowing frost stitching.
        a.box("Blanket", (5.8, 0.3, 3.2), (0, 10.3, 2.1), blanket, role="Accent")
        for s, S in SIDES:
            a.box(f"BlanketSide{S}", (0.3, 2.4, 3.2), (3.3 * s, 9.1, 2.1), blanket, role="Accent")
            a.box(f"BlanketTrim{S}", (0.34, 0.3, 3.24), (3.31 * s, 7.95, 2.1), ICE, **GLOW)
            for j in range(4):
                a.wedge(f"BlanketTassel{S}{j}", (0.16, 0.7, 0.3), (3.33 * s, 7.45, 0.85 + j * 0.85), blanket2,
                        rot=(0, 90, 180), **DETAIL)
            for j in range(3):
                a.box(f"BlanketStitch{S}{j}", (0.33, 0.25, 0.6), (3.32 * s, 9.2 + (j - 1) * 0.6, 2.1),
                      ICE_HOT, rot=(45, 0, 0), **GLOW)
        for j, (x, z) in enumerate(((-1.8, -2.4), (1.8, -2.4), (-1.6, 3.6), (1.6, 3.4))):
            ice_shard(a, f"BackShard{j}", (x, 10.0, z), 1.4, 0.6, R=angles(0, 0, 18 if x < 0 else -18), glow=j < 2)
    with in_bone(a, "Head"):
        # A snowflake rune glowing on the forehead, a tuft of fur on top, fringed ears and an ice crown.
        for k in range(3):
            a.box(f"BrowRune{k}", (0.18, 1.4, 0.12), (0, 10.25, -7.5), ICE_HOT, rot=(0, 0, 60 * k), **GLOW)
        for j in range(5):
            a.wedge(f"HeadTuft{j}", (0.5, 1.1 + 0.2 * (j % 2), 0.9), (-1.2 + j * 0.6, 12.0, -4.6), shag,
                    rot=(0, 0, (j - 2) * 12), role="Secondary")
        for s, S in SIDES:
            for j in range(3):
                a.wedge(f"EarFringe{S}{j}", (0.35, 0.8, 0.7), (2.75 * s, 7.4, -5.6 + j * 0.85), shag, rot=(0, 0, 180),
                        role="Secondary")
            pts_t = [(1.2 * s, 7.6, -7.0), (1.6 * s, 6.6, -8.2), (2.0 * s, 6.6, -9.6), (2.1 * s, 7.6, -10.6)]
            for j in (2, 3):
                a.box(f"TuskBand{S}{j}", (0.8, 0.25, 0.8), pts_t[j], C("#8fd8ff"), R=aim(sub(pts_t[j], pts_t[j - 1])),
                      **GLOW)
            for j in range(2):
                a.box(f"TuskRune{S}{j}", (0.12, 0.35, 0.35), add(pts_t[1 + j], (0.38 * s, 0.25, -0.5)), ICE,
                      rot=(45, 0, 0), **GLOW)
        for j, (x, z, h) in enumerate(((-1.0, -5.6, 1.6), (1.0, -5.6, 1.6), (-0.6, -4.2, 1.2), (0.6, -4.2, 1.2))):
            ice_shard(a, f"CrownShard{j}", (x, 11.8, z), h, 0.55, R=angles(0, 0, 14 if x > 0 else -14), glow=j < 2)
        for s, S in SIDES:
            a.box(f"TrunkFinger{S}", (0.35, 0.45, 0.5), (0.35 * s, 3.55, -9.75), fur)
    for s, S in SIDES:
        for z, F in ((-2.6, "F"), (3.4, "B")):
            with in_bone(a, f"Leg{F}{S}"):
                # Fur cuffs round the top and the knee, and a fringe over the foot.
                for ring, y in enumerate((4.2, 2.9)):
                    for k in range(4):
                        ang = k * math.pi / 2 + math.pi / 4
                        c, s_ = math.cos(ang), math.sin(ang)
                        a.wedge(f"LegCuff{F}{S}{ring}{k}", (0.9, 0.9, 0.35),
                                (2.1 * s + c * 1.15, y, z + s_ * 1.15), shag if (k + ring) % 2 else fur,
                                rot=(0, -math.degrees(ang) + 90, 180), role="Secondary")
                for k in range(4):
                    ang = k * math.pi / 2
                    c, s_ = math.cos(ang), math.sin(ang)
                    a.wedge(f"FootFringe{F}{S}{k}", (1.0, 0.7, 0.35), (2.1 * s + c * 1.2, 1.05, z + s_ * 1.2), shag,
                            rot=(0, -math.degrees(ang) + 90, 180), role="Secondary")
    with in_bone(a, "Tail"):
        for j in range(4):
            a.wedge(f"TailHair{j}", (0.3, 1.0, 0.5), ((j - 1.5) * 0.25, 5.8, 5.55), shag, rot=(0, 0, 180 + (j - 1.5) * 10),
                    role="Secondary")
    with in_bone(a, "Orbit"):
        for i in range(6):
            ang = 2 * math.pi * (i + 0.5) / 6
            p0 = (math.cos(ang) * 10.5, 9.0 + 1.0 * math.sin(ang * 3), 0.6 + math.sin(ang) * 10.5)
            ice_shard(a, f"OrbitIceHigh{i}", p0, 1.8, 0.7, R=angles(-20, -math.degrees(ang), 15), glow=i % 2 == 0)
        # A snowflake rune on the ground inside the frost ring.
        for k in range(6):
            ang = k * math.pi / 3
            c, s_ = math.cos(ang), math.sin(ang)
            a.box(f"FlakeArm{k}", (6.0, 0.06, 0.35), (c * 3.2, 0.13, 0.6 + s_ * 3.2), ICE,
                  rot=(0, -math.degrees(ang), 0), transparency=0.3, **GLOW)
            for sgn in (-1, 1):
                b = (c * 4.4, 0.13, 0.6 + s_ * 4.4)
                a.box(f"FlakeTwig{k}{'a' if sgn > 0 else 'b'}", (1.6, 0.06, 0.3),
                      add(b, (math.cos(ang + sgn * 0.8) * 0.6, 0, math.sin(ang + sgn * 0.8) * 0.6)), ICE_HOT,
                      rot=(0, -math.degrees(ang + sgn * 0.8), 0), transparency=0.3, **GLOW)

    a.ride_height, a.ride_z = 11.2, 0.4
    scale_animal(a, 1.3)
    unfight(a, "Hump", "Brow", d=0.04)

    # -- heavy effects ----------------------------------------------------------------
    k = 1.3
    p = lambda n: find(a, n)["p"]
    fx(a, "Body",
       light("GlacierLight", ICE, brightness=1.6, range_=24, pulse=2.2),
       emitter("Blizzard", WHITE, rate=26, lifetime=(2.0, 3.2), speed=(1, 3), sizes=((0, 0.45), (1, 0.2)),
               transparency=((0, 0.1), (1, 1)), light=0.6, accel=(1.2, -2.5, 0), spread=180, rot_speed=(-120, 120),
               texture=SPARKLE_TEXTURE),
       emitter("ColdAura", ICE_HOT, rate=14, lifetime=(1.2, 2.0), speed=(0.4, 1.2), sizes=((0, 0.6), (1, 0)),
               accel=(0, 1.2, 0), color2=ICE, **SPARK))
    for s, S in SIDES:
        for F in ("F", "B"):
            fx(a, f"Foot{F}{S}", emitter("FrostMist", ICE_HOT, texture=SMOKE_TEXTURE, rate=3, lifetime=(1.0, 1.6),
                                         speed=(0.5, 1.5), spread=80, sizes=((0, 1.4), (1, 3.4)),
                                         transparency=((0, 0.65), (1, 1)), light=0.2, emit="Bottom", color2=ICE))
        tip = p(f"Tusk{S}3")
        trail(a, f"Tusk{S}3", add(tip, (0, 0.5 * k, 0)), add(tip, (0, -0.5 * k, 0)), ICE_HOT, name=f"TuskTrail{S}",
              lifetime=0.5, color2=ICE)
    for j in (0, 3):
        gp = p(f"Glacier{j}")
        fx(a, f"Glacier{j}", light(f"CrystalLight{j}", ICE, brightness=1.2, range_=12, pulse=1.3 + 0.3 * j),
           emitter("CrystalGlitter", ICE_HOT, rate=10, lifetime=(0.6, 1.2), speed=(0.5, 1.5),
                   sizes=((0, 0.5), (1, 0)), color2=ICE, **SPARK))
        beam(a, f"Glacier{j}", add(gp, (0, 2.5 * k, 0)), f"Glacier{j}", add(gp, (0, 14 * k, 0)), ICE,
             name=f"FrostColumn{j}", width=(1.2, 0.05), transparency=((0, 0.35), (1, 1)), segments=4,
             color2=ICE_HOT, texture=SPARKLE_TEXTURE, texture_speed=2)
    for i in (0, 2, 4, 6, 8):
        op, nxt = p(f"OrbitIce{i}"), p(f"OrbitIce{(i + 2) % 10}")
        beam(a, f"OrbitIce{i}", op, f"OrbitIce{(i + 2) % 10}", nxt, ICE, name=f"FrostArc{i}", width=(0.35, 0.35),
             curve=(2, -2), transparency=((0, 0.45), (0.5, 0.2), (1, 0.45)), segments=12, color2=ICE_HOT,
             texture=SPARKLE_TEXTURE, texture_speed=3)
    pulse(a, *[f"FrostRing{i}" for i in range(0, 26, 2)], "Crown", "IcePlateRuneL", "IcePlateRuneR", seconds=1.6)
    extras(a, attrs={"WalkSpeed": 9, "OrbitSpeed": 0.35}, highlight=(ICE, ICE_HOT, 1.0, 0.45))
    return a


# ------------------------------------------------------------------ Secret ----

AURORA = ["#5effb0", "#3ff0d0", "#3fd6ff", "#5fa0ff", "#8a7bff", "#b45cff", "#ff6bd6"]


def _aurora(t):
    """Colour along the aurora gradient, t from 0 (green) to 1 (pink)."""
    x = t * (len(AURORA) - 1)
    i = min(int(x), len(AURORA) - 2)
    c0, c1 = C(AURORA[i]), C(AURORA[i + 1])
    f = x - i
    return tuple(p + (q - p) * f for p, q in zip(c0, c1))


VORTEX_TEXTURE = "rbxasset://textures/particles/forcefield_vortex_main.dds"
GLOW_TEXTURE = "rbxasset://textures/particles/forcefield_glow_main.dds"
SHOCK_TEXTURE = "rbxasset://textures/particles/explosion01_shockwave_main.dds"
FLAMESPARK_TEXTURE = "rbxasset://textures/particles/fire_sparks_main.dds"


def _grad(e, *stops):
    """Gives an emitter a colour gradient with several stops: (t, colour), ..."""
    e["props"]["Color"] = [[t, *c] for t, c in stops]
    return e


def _grad_stops(i, n=16):
    return (0, _aurora(i / n)), (0.5, _aurora(min(1, i / n + 0.15))), (1, _aurora(min(1, i / n + 0.3)))


def _orient(e, how):
    e["props"]["Orientation"] = how
    return e


def aurora_dragon():
    a = Animal("AuroraDragon", "Aurora Dragon", "Secret")
    N = 16
    pts = [(1.6 * math.sin(i * 0.55), 6.6 + 2.0 * math.sin(i * 0.42 + 0.6), -1.0 + i * 1.75) for i in range(N + 2)]
    widths = [3.7 - 2.2 * (i / N) ** 0.9 for i in range(N + 1)]
    belly = C("#e9fff6")

    def segment(i):
        d = sub(pts[i + 1], pts[max(0, i - 1)])
        R = aim(d)       # local X along the body
        p = pts[i]
        w = widths[i]
        col = _aurora(i / N)
        a.bevel(f"Seg{i}", (2.0, w, w * 1.05), p, col, b=w * 0.28, R=R)
        a.box(f"SegBelly{i}", (2.0, w * 0.32, w * 0.9), add(p, (0, -w * 0.38, 0)), belly, R=R, role="Secondary")
        # Dorsal fin of light, and a row of glowing scales.
        fin_h = 1.6 + 1.2 * math.sin(math.pi * i / N)
        a.wedge(f"Fin{i}", (0.26, fin_h, 1.7), add(p, (0, w / 2 + fin_h / 2 - 0.1, 0.2)), col,
                R=matmul(R, angles(0, 90, 0)), **GLOW_T)
        for sx in (-1, 1):
            a.box(f"Scale{i}{'R' if sx > 0 else 'L'}", (1.0, 0.3, 0.12), add(p, (sx * w * 0.53, w * 0.1, 0)),
                  _aurora(min(1, i / N + 0.15)), R=matmul(R, angles(0, 90, 0)), **GLOW)
            S = "R" if sx > 0 else "L"
            # Two more rows of scales, a fin of light on each side, and a star speck on alternate sides.
            a.box(f"ScaleHigh{i}{S}", (0.8, 0.24, 0.1), add(p, (sx * w * 0.5, w * 0.36, 0.3)),
                  _aurora(min(1, i / N + 0.25)), R=matmul(R, angles(0, 90, 0)), role="Secondary", shadow=False)
            a.box(f"ScaleLow{i}{S}", (0.8, 0.24, 0.1), add(p, (sx * w * 0.5, -w * 0.16, -0.3)),
                  _aurora(max(0, i / N - 0.05)), R=matmul(R, angles(0, 90, 0)), role="Secondary", shadow=False)
            plate(a, f"SideFin{i}{S}", add(p, (sx * w * 0.48, -w * 0.22, 0.1)),
                  add(p, (sx * (w * 0.5 + 1.1 + 0.4 * math.sin(math.pi * i / N)), -w * 0.3 - 0.2, 0.9)), 0.8, 0.1,
                  _aurora(min(1, i / N + 0.1)), up=(0, 1, 0), **GLOW_T)
            if (i + (sx > 0)) % 2 == 0:
                a.box(f"StarSpeck{i}{S}", (0.2, 0.2, 0.2), add(p, (sx * w * 0.53, w * 0.24, -0.4)), WHITE, **GLOW)
        a.box(f"BellyRidge{i}", (0.26, w * 0.34, w * 0.94), add(p, (0, -w * 0.38, 0)), C("#bfeee0"), R=R, **DETAIL)
        # Flame tufts of aurora along the spine, a second smaller row of fins, belly plates, a golden bead
        # behind the fin, a golden band on every other segment and a second star.
        for sx in (-1, 1):
            S = "R" if sx > 0 else "L"
            plate(a, f"SpineTuft{i}{S}", add(p, (sx * 0.35, w / 2, 0.3)),
                  add(p, (sx * 0.95, w / 2 + 0.9 + 0.4 * math.sin(math.pi * i / N), 1.2)), 0.45, 0.1,
                  _aurora(min(1, i / N + 0.2)), up=(sx, 0, 0), **GLOW_T)
            plate(a, f"LowFin{i}{S}", add(p, (sx * w * 0.45, -w * 0.34, -0.3)),
                  add(p, (sx * (w * 0.5 + 0.75), -w * 0.45 - 0.35, 0.45)), 0.5, 0.08, _aurora(max(0, i / N - 0.1)),
                  up=(0, 1, 0), **GLOW_T)
            a.box(f"BellyPlate{i}{S}", (0.8, 0.1, w * 0.7), add(add(p, apply(R, (0.5 * sx, 0, 0))), (0, -w * 0.55, 0)),
                  C("#d6fff0"), R=R, role="Secondary", shadow=False)
            if (i + (sx < 0)) % 2 == 0:
                a.box(f"StarSpeckB{i}{S}", (0.16, 0.16, 0.16), add(p, (sx * w * 0.53, -w * 0.02, 0.5)), WHITE, **GLOW)
        a.ball(f"SpineBead{i}", 0.35, add(p, (0, w / 2 + 0.08, 0.75)), C("#ffe9a8"), role="Accent")
        if i % 2 == 0:
            a.box(f"GoldBand{i}", (0.26, w * 1.06, w * 1.12), p, C("#ffe9a8"), R=R, role="Accent", reflectance=0.2)
        a.wedge(f"Spike{i}", (0.3, 0.7, 0.55), add(p, (0, w / 2 + 0.25, -0.75)), C("#ffe9a8"),
                R=matmul(R, angles(0, 90, 0)), role="Accent")

    # Body = the first segment behind the head; every later segment is its own joint, so the body can ripple.
    segment(0)
    prev = "Body"
    for i in range(1, N + 1):
        with a.bone(f"SegJoint{i}", prev, scale(add(pts[i - 1], pts[i]), 0.5)):
            segment(i)
        prev = f"SegJoint{i}"
    # Tail fan at the end.
    with in_bone(a, prev):
        end = pts[N]
        for j, t in enumerate((-30, 0, 30)):
            R = angles(0, t, 0)
            a.wedge(f"TailFan{j}", (0.2, 2.6, 3.2), add(end, apply(R, (0, 0.4, 1.8))), _aurora(0.9 + 0.05 * j),
                    R=matmul(R, angles(0, 90, 0)), **GLOW_T)
    # Four little clawed legs.
    for i_seg, F in ((2, "F"), (9, "B")):
        parent = "Body" if i_seg == 0 else f"SegJoint{i_seg}"
        for s, S in SIDES:
            p = pts[i_seg]
            with a.bone(f"Leg{F}{S}", parent, add(p, (0.9 * s, -0.4, 0))):
                a.post(f"Leg{F}{S}", (0.7, 1.8, 0.7), add(p, (1.3 * s, -1.4, 0.1)), _aurora(i_seg / N), b=0.15)
                a.box(f"Claw{F}{S}", (1.0, 0.4, 1.2), add(p, (1.35 * s, -2.4, -0.2)), C("#ffe9a8"), role="Accent")
                for j in (-0.3, 0.3):
                    a.wedge(f"Talon{F}{S}{j > 0}", (0.25, 0.3, 0.5), add(p, (1.35 * s + j, -2.45, -0.95)),
                            C("#ffe9a8"), **DETAIL)

    # The head: an eastern dragon with golden antlers, a flame mane and long glowing whiskers.
    with a.bone("Head", "Body", (0, 6.6, -1.6)):
        hc = (0, 7.2, -3.4)
        a.oct("Head", (3.4, 3.0, 3.6), hc, C("#4fd8e8"), b=0.8)
        a.oct("Snout", (2.4, 1.6, 2.2), (0, 6.8, -5.6), C("#8cf0ff"), b=0.5, role="Secondary")
        a.box("Jaw", (2.2, 0.6, 2.4), (0, 5.9, -5.4), C("#3fb8d0"))
        a.box("Mouth", (1.8, 0.2, 0.1), (0, 6.15, -6.72), MOUTH, **DETAIL)
        for s, S in SIDES:
            a.tri(f"Fang{S}", (0.6 * s, 6.1, -6.7), 0.3, 0.4, 0.1, WHITE, R=angles(0, 0, 180), **DETAIL)
            a.box(f"Nostril{S}", (0.3, 0.3, 0.1), (0.5 * s, 7.15, -6.72), C("#1b3a50"), **DETAIL)
            a.eye2(f"Eye{S}", (0.95 * s, 7.9, -5.12), w=0.95, h=1.0, iris=C("#ffe14d"), glow=True,
                   lid=C("#2a6f88"), lid_tilt=16 * s, lid_drop=0.1)
            # Antlers.
            ant = [(0.8 * s, 8.4, -3.0), (1.3 * s, 9.8, -2.6), (2.0 * s, 10.9, -2.0), (2.1 * s, 12.0, -1.4)]
            chain(a, f"Antler{S}", ant, [0.45, 0.38, 0.3], C("#ffe9a8"), role="Accent")
            seg(a, f"AntlerBranch{S}", ant[1], (2.4 * s, 10.0, -3.2), 0.3, C("#ffe9a8"), role="Accent")
            seg(a, f"AntlerBranch2{S}", ant[2], (1.4 * s, 11.8, -2.9), 0.26, C("#ffe9a8"), role="Accent")
            # Whiskers.
            wk = [(1.1 * s, 6.9, -6.4), (2.2 * s, 6.6, -7.2), (3.3 * s, 6.0, -7.0), (4.0 * s, 5.2, -6.2)]
            chain(a, f"Whisker{S}", wk, [0.18, 0.15, 0.12], C("#e9fff6"), material="Neon", role="Glow", shadow=False)
        for j, (y, z, h) in enumerate(((8.6, -2.2, 2.2), (8.0, -1.2, 2.6), (7.4, -0.2, 2.2))):
            for sx in (-1, 1):
                plate(a, f"Mane{j}{'R' if sx > 0 else 'L'}", (0.5 * sx, y, z), (1.4 * sx, y + h, z + 1.4), 0.8, 0.14,
                      _aurora(0.1 + 0.25 * j), up=(1, 0, 0), **GLOW_T)
        a.box("BrowGem", (0.5, 0.5, 0.2), (0, 8.45, -5.0), C("#ffffff"), rot=(0, 0, 45), **GLOW)

    # -- showpiece detail ---------------------------------------------------------------------------
    gold = C("#ffe9a8")
    with in_bone(a, "Head"):
        beard = [(0, 5.6, -5.2), (0, 4.8, -5.0), (0, 4.0, -4.4), (0, 3.4, -3.6)]
        chain(a, "Beard", beard, [0.55, 0.42, 0.3], belly, role="Secondary")
        for j, x in enumerate((-0.35, 0.0, 0.35)):
            plate(a, f"BeardTip{j}", beard[-1], add(beard[-1], (x * 2, -0.9, 0.7)), 0.4, 0.1, _aurora(0.2 + 0.2 * j),
                  up=(1, 0, 0), **GLOW_T)
        for s, S in SIDES:
            for j, x in enumerate((0.25, 0.85)):
                a.tri(f"Tooth{S}{j}", (x * s, 6.15, -6.65), 0.2, 0.28, 0.08, WHITE, R=angles(0, 0, 180), **DETAIL)
            ant = [(0.8 * s, 8.4, -3.0), (1.3 * s, 9.8, -2.6), (2.0 * s, 10.9, -2.0), (2.1 * s, 12.0, -1.4)]
            seg(a, f"AntlerTine{S}", ant[2], (2.9 * s, 11.6, -1.4), 0.22, gold, role="Accent")
            seg(a, f"AntlerTine2{S}", ant[3], (1.6 * s, 12.8, -0.8), 0.2, gold, role="Accent")
            for j in range(2):
                p0 = (1.6 * s, 7.2 - 0.5 * j, -4.4 + 0.3 * j)
                plate(a, f"CheekFin{S}{j}", p0, add(p0, (1.1 * s, 0.7 - 0.3 * j, 1.4)), 0.55, 0.1,
                      _aurora(0.15 + 0.2 * j), up=(s, 0, 0), **GLOW_T)
            a.box(f"BrowRidge{S}", (1.1, 0.3, 0.4), (0.95 * s, 8.45, -4.85), C("#2a6f88"), rot=(0, 0, 12 * s), **DETAIL)
            a.wedge(f"Ear{S}", (0.25, 1.0, 0.8), (1.75 * s, 8.3, -2.8), _aurora(0.3), rot=(0, 0, -25 * s),
                    role="Secondary")
        for j in range(3):
            a.box(f"ForeheadRune{j}", (0.18, 0.18, 0.12), ((j - 1) * 0.4, 8.85 + 0.2 * (j == 1), -5.0), _aurora(0.5),
                  **GLOW)
        for j, (y, z, h) in enumerate(((9.0, -3.2, 1.8), (8.9, -2.6, 2.0), (7.0, 0.6, 1.9))):
            for sx in (-1, 1):
                plate(a, f"ManeB{j}{'R' if sx > 0 else 'L'}", (0.3 * sx, y, z), (1.0 * sx, y + h, z + 1.3), 0.7, 0.12,
                      _aurora(0.25 + 0.2 * j), up=(1, 0, 0), **GLOW_T)
    for i_seg, F in ((2, "F"), (9, "B")):
        for s, S in SIDES:
            p = pts[i_seg]
            with in_bone(a, f"Leg{F}{S}"):
                a.bevel(f"Shoulder{F}{S}", (0.9, 1.0, 1.2), add(p, (1.15 * s, -0.7, 0.1)), _aurora(i_seg / N + 0.1),
                        b=0.2, role="Secondary")
                a.box(f"Wrist{F}{S}", (0.85, 0.25, 0.85), add(p, (1.3 * s, -1.95, 0.1)), gold, role="Accent",
                      reflectance=0.25)
                for j in range(2):
                    plate(a, f"ElbowFlame{F}{S}{j}", add(p, (1.5 * s, -1.2, 0.5)),
                          add(p, (1.8 * s + 0.2 * j * s, -0.6 - 0.3 * j, 1.6)), 0.4, 0.1, _aurora(0.3 + 0.3 * j),
                          up=(s, 0, 0), **GLOW_T)
                for j in (-0.45, 0.45):
                    a.wedge(f"TalonSide{F}{S}{j > 0}", (0.22, 0.28, 0.45), add(p, (1.35 * s + j * 1.3, -2.45, -0.75)),
                            gold, **DETAIL)
    with in_bone(a, "LegFR"):
        p = pts[2]
        c = add(p, (1.4, -1.7, -1.3))
        a.ball("Pearl", 1.1, c, C("#f2fffa"), **GLOW)
        for j in range(6):
            ang = j * math.pi / 3
            a.box(f"PearlGlint{j}", (0.18, 0.18, 0.18), add(c, (math.cos(ang) * 0.75, math.sin(ang) * 0.75, 0)),
                  _aurora(j / 6), **GLOW)
    with in_bone(a, f"SegJoint{N}"):
        end = pts[N]
        for j, t in enumerate((-55, -15, 15, 55)):
            R = angles(0, t, 0)
            a.wedge(f"TailFanB{j}", (0.18, 2.0, 2.4), add(end, apply(R, (0, 0.2, 1.4))), _aurora(0.75 + 0.05 * j),
                    R=matmul(R, angles(0, 90, 0)), **GLOW_T)
        for j in range(3):
            plate(a, f"TailFlame{j}", add(end, (0, 0.6, 0.4)), add(end, ((j - 1) * 0.8, 2.0 + 0.4 * (j == 1), 1.2)),
                  0.5, 0.1, _aurora(0.9), up=(0, 0, 1), **GLOW_T)
    with in_bone(a, "Head"):
        # A crown of little horns along the brow, trailing mane ribbons, jaw scales and a chin pearl.
        for s, S in SIDES:
            for j in range(3):
                a.wedge(f"BrowHorn{S}{j}", (0.22, 0.6 - 0.1 * j, 0.4), (1.2 * s, 8.75 - 0.15 * j, -4.6 + j * 0.7), gold,
                        rot=(-20, 0, -15 * s), role="Accent")
            for j in range(2):
                p0 = (0.9 * s, 8.2 - 0.6 * j, -1.8)
                plate(a, f"ManeRibbon{S}{j}", p0, add(p0, (0.8 * s, 0.8 - 0.4 * j, 3.2)), 0.55, 0.1,
                      _aurora(0.35 + 0.25 * j), up=(s, 0, 0), **GLOW_T)
            for j in range(2):
                a.box(f"JawScale{S}{j}", (0.12, 0.35, 0.6), (1.12 * s, 5.95, -5.9 + j * 0.8), C("#2a8aa0"), **DETAIL)
            a.box(f"NostrilGlow{S}", (0.18, 0.18, 0.08), (0.5 * s, 7.15, -6.78), _aurora(0.2), **GLOW)
        a.ball("ChinPearl", 0.5, (0, 3.2, -3.4), C("#f2fffa"), **GLOW)
    for i_seg, F in ((2, "F"), (9, "B")):
        for s, S in SIDES:
            p = pts[i_seg]
            with in_bone(a, f"Leg{F}{S}"):
                for j in range(2):
                    a.wedge(f"ArmSpike{F}{S}{j}", (0.18, 0.55, 0.4), add(p, (1.62 * s, -1.2 - 0.4 * j, 0.45)), gold,
                            rot=(-30, 0, 0), role="Accent")
                    a.box(f"ToePad{F}{S}{j}", (0.3, 0.12, 0.3), add(p, (1.35 * s + (j - 0.5) * 0.5, -2.62, -0.6)),
                          C("#8cf0ff"), **DETAIL)
    with in_bone(a, "LegFR"):
        c = add(pts[2], (1.4, -1.7, -1.3))
        for ring_i, (r, tilt) in enumerate(((1.05, 30), (1.25, -40))):
            for j in range(8):
                ang = j * math.pi / 4
                R = angles(tilt, 0, 0)
                q = add(c, apply(R, (math.cos(ang) * r, 0, math.sin(ang) * r)))
                a.box(f"PearlRing{ring_i}_{j}", (0.12, 0.12, 0.5), q, _aurora((j + 4 * ring_i) / 8 % 1),
                      R=matmul(R, angles(0, -math.degrees(ang), 0)), **GLOW)
        a.box("PearlCore", (0.3, 0.3, 0.3), c, WHITE, transparency=1, **DETAIL)
    with in_bone(a, f"SegJoint{N}"):
        end = pts[N]
        for s, S in SIDES:
            wk = [add(end, (0.3 * s, 0.2, 0.2)), add(end, (1.4 * s, -0.3, 1.4)), add(end, (2.4 * s, -1.0, 2.0)),
                  add(end, (3.0 * s, -1.9, 1.8))]
            chain(a, f"TailWhisker{S}", wk, [0.16, 0.13, 0.1], C("#e9fff6"), material="Neon", role="Glow", shadow=False)
    # Little clouds drifting under its body.
    for k, i_seg in enumerate((3, 5, 8, 11, 13)):
        p = pts[i_seg]
        with in_bone(a, f"SegJoint{i_seg}"):
            for j, (dx, dy, dz, d) in enumerate(((0, 0, 0, 1.6), (1.0, -0.2, 0.3, 1.2), (-1.0, -0.2, -0.2, 1.3),
                                                 (0.4, 0.4, -0.6, 1.1), (-0.5, 0.3, 0.7, 1.0))):
                a.ball(f"Cloud{k}_{j}", d, add(p, (dx, -widths[i_seg] / 2 - 1.6 + dy, dz)), WHITE, transparency=0.25,
                       role="Secondary", shadow=False)

    # Orbit: a ring of stars and a halo of light around it.
    with a.bone("Orbit", "Body", (0, 6.4, 14.0)):
        for i in range(12):
            ang = 2 * math.pi * i / 12
            p = (math.cos(ang) * 13.0, 6.4 + 2.0 * math.sin(ang * 3), 14.0 + math.sin(ang) * 18.0)
            pixel_star(a, f"OrbitStar{i}", p, 1.2 if i % 2 else 0.8, C("#ffffff") if i % 3 else _aurora(i / 12),
                       R=angles(0, -math.degrees(ang), 0))
        # Spirit orbs circling with the stars (the constellation lines between them are beams).
        for i in range(8):
            ang = 2 * math.pi * (i + 0.25) / 8
            p = (math.cos(ang) * 9.5, 9.5 + 1.4 * math.sin(ang * 2), 14.0 + math.sin(ang) * 14.0)
            a.ball(f"SpiritOrb{i}", 0.9, p, _aurora(i / 8), **GLOW)
            for j, tilt in enumerate((0, 90)):
                a.box(f"SpiritOrbRing{i}_{j}", (1.5, 0.1, 0.1), p, WHITE, rot=(0, -math.degrees(ang) + tilt, 45),
                      **DETAIL)
        a.box("SigilCore", (0.4, 0.2, 0.4), (0, 0.2, 14.0), WHITE, transparency=1, **DETAIL)
        # A slow ring of aurora light below the stars.
        for i in range(16):
            ang = 2 * math.pi * (i + 0.5) / 16
            p = (math.cos(ang) * 11.0, 3.2 + 0.6 * math.sin(ang * 2), 14.0 + math.sin(ang) * 16.0)
            a.box(f"AuroraRing{i}", (0.3, 0.3, 4.0), p, _aurora(i / 16), R=angles(0, -math.degrees(ang), 0), **GLOW_T)

    with in_bone(a, "Body"):
        a.box("StarfallSource", (6, 0.2, 6), (0, 12.0, 6.0), WHITE, transparency=1, **DETAIL)
    a.ride_height, a.ride_z = 9.4, 2.0
    a.overhead = 13.5
    K = 1.5
    scale_animal(a, K)

    # -- heavy effects ----------------------------------------------------------------
    p = lambda n: find(a, n)["p"]
    # Aurora ribbons: wide shimmering curtains of light rising off its back along the body.
    for i in range(0, N - 1, 3):
        c0, c1 = _aurora(i / N), _aurora(min(1, (i + 3) / N))
        top0, top1 = add(p(f"Seg{i}"), (0, widths[i] * K, 0)), add(p(f"Seg{min(N, i + 3)}"), (0, widths[min(N, i + 3)] * K, 0))
        beam(a, f"Seg{i}", top0, f"Seg{min(N, i + 3)}", top1, c0, name=f"Ribbon{i}", width=(4.5, 3.5),
             curve=(3, -2), transparency=((0, 0.35), (0.5, 0.15), (1, 0.35)), segments=14, color2=c1,
             texture=SPARKLE_TEXTURE, texture_speed=1.5, face_camera=False, R0=angles(0, 0, 90), R1=angles(0, 0, 90))
    # Long aurora streamers trailing from the body.
    for i in (3, 7, 11, 15):
        sp = p(f"Seg{i}")
        trail(a, f"Seg{i}", add(sp, (0, 1.4 * K, 0)), add(sp, (0, -1.0 * K, 0)), _aurora(i / N),
              name=f"Streamer{i}", lifetime=1.4, color2=_aurora(min(1, i / N + 0.3)), transparency=((0, 0.2), (1, 1)))
    for s, S in SIDES:
        wp = p(f"Whisker{S}2")
        trail(a, f"Whisker{S}2", add(wp, (0, 0.3, 0)), add(wp, (0, -0.3, 0)), C("#e9fff6"), name=f"WhiskerTrail{S}",
              lifetime=0.8, color2=_aurora(0.4))
    # Stars inside its body, glowing mist, and light.
    for i in (1, 6, 11):
        fx(a, f"Seg{i}",
           emitter("Stardust", WHITE, rate=12, lifetime=(1.2, 2.2), speed=(0.4, 1.4), sizes=((0, 0.6), (1, 0)),
                   color2=_aurora(i / N), rot_speed=(-180, 180), **SPARK),
           emitter("AuroraMist", _aurora(i / N), texture=SMOKE_TEXTURE, rate=3, lifetime=(1.6, 2.6),
                   speed=(0.3, 0.8), sizes=((0, 2.0), (1, 4.5)), transparency=((0, 0.7), (1, 1)), light=1,
                   color2=_aurora(min(1, i / N + 0.3))),
           light(f"AuroraLight{i}", _aurora(i / N), brightness=1.6, range_=20, pulse=1.4 + 0.3 * i / 5))
    fx(a, "BrowGem", light("BrowLight", C("#ffffff"), brightness=1.2, range_=10, pulse=0.9),
       emitter("HeadFlare", C("#ffffff"), rate=10, lifetime=(0.4, 0.8), speed=(1, 3), sizes=((0, 0.7), (1, 0)),
               color2=_aurora(0.2), drag=2, **SPARK))
    # A column of light rising from its head into the sky.
    hp = p("Head")
    beam(a, "Head", add(hp, (0, 2 * K, 0)), "Head", add(hp, (0, 30 * K, 0)), _aurora(0.1), name="SkyColumn",
         width=(2.0, 0.1), transparency=((0, 0.4), (0.7, 0.8), (1, 1)), segments=4, color2=_aurora(0.6),
         texture=SPARKLE_TEXTURE, texture_speed=3)
    for i in range(0, 12, 3):
        sp = p(f"OrbitStar{i}A")
        trail(a, f"OrbitStar{i}A", add(sp, (0, 0.5, 0)), add(sp, (0, -0.5, 0)), C("#ffffff"), name=f"StarTrail{i}",
              lifetime=0.9, color2=_aurora(i / 12))
    # A spirit glow along the whole body, shifting through the aurora colours.
    for i in range(0, N + 1, 2):
        w = widths[i] * K
        fx(a, f"Seg{i}", _grad(emitter(f"SpiritGlow{i}", _aurora(i / N), texture=GLOW_TEXTURE, rate=1.2,
                                       lifetime=(1.4, 1.6), speed=(0, 0), sizes=((0, w * 1.8), (0.5, w * 2.5), (1, w * 1.8)),
                                       transparency=((0, 1), (0.5, 0.72), (1, 1)), lock=True, rot_speed=(-20, 20)),
                                *_grad_stops(i)))
    # The pearl: a little spinning galaxy.
    fx(a, "PearlCore",
       _grad(emitter("Galaxy", WHITE, texture=VORTEX_TEXTURE, rate=1.5, lifetime=(1.6, 1.6), speed=(0, 0),
                     sizes=((0, 3.4), (0.5, 4.2), (1, 3.4)), transparency=((0, 1), (0.3, 0.2), (0.7, 0.2), (1, 1)),
                     lock=True, rot_speed=(180, 240)), (0, WHITE), (0.4, _aurora(0.3)), (1, _aurora(0.8))),
       _grad(emitter("PearlGlow", WHITE, texture=GLOW_TEXTURE, rate=1.2, lifetime=(1.2, 1.2), speed=(0, 0),
                     sizes=((0, 4), (0.5, 5.5), (1, 4)), transparency=((0, 1), (0.5, 0.5), (1, 1)), lock=True),
             (0, WHITE), (1, _aurora(0.5))),
       emitter("PearlMotes", WHITE, rate=8, lifetime=(0.8, 1.4), speed=(1, 2.5), sizes=((0, 0.35), (1, 0)),
               color2=_aurora(0.6), drag=2, **SPARK),
       light("PearlLight", _aurora(0.4), brightness=1.8, range_=14, pulse=0.8))
    # Spirit fire flickering from its mouth, sparks crackling off the antlers, light trails from its eyes.
    fx(a, "Snout", _grad(emitter("SpiritFire", WHITE, texture=FIRE_TEXTURE, rate=12, lifetime=(0.3, 0.5),
                                 speed=(2, 5), spread=20, sizes=((0, 0.6), (0.3, 1.5), (1, 0)),
                                 transparency=((0, 0.2), (1, 1)), accel=(0, 3, 0), emit="Front"),
                         (0, WHITE), (0.3, _aurora(0.3)), (1, _aurora(0.75))))
    for s, S in SIDES:
        fx(a, f"Antler{S}2", _grad(emitter("AntlerSparks", WHITE, texture=FLAMESPARK_TEXTURE, rate=8,
                                           lifetime=(0.4, 0.8), speed=(2, 5), sizes=((0, 0.6), (1, 0)), spread=60,
                                           drag=2, rot_speed=(-300, 300)), (0, WHITE), (0.5, _aurora(0.4)),
                                   (1, _aurora(0.8))))
        ep = p(f"Eye{S}Iris")
        trail(a, f"Eye{S}Iris", add(ep, (0, 0.18, 0)), add(ep, (0, -0.18, 0)), C("#fff27a"), name=f"EyeTrail{S}",
              lifetime=0.45, color2=_aurora(0.3), transparency=((0, 0.1), (1, 1)))
    # Shooting stars falling around it.
    starfall = _grad(emitter("Starfall", WHITE, rate=5, lifetime=(1.2, 1.8), speed=(16, 24), spread=35,
                             sizes=((0, 0.7), (1, 0.25)), transparency=((0, 0), (0.8, 0.2), (1, 1)), emit="Bottom",
                             accel=(0, -6, 0), rot_speed=(0, 0), rot=(0, 0), texture=SPARKLE_TEXTURE),
                     (0, WHITE), (0.5, _aurora(0.2)), (1, _aurora(0.7)))
    starfall["props"]["Squash"] = [[0, 2.5], [1, 2.5]]
    fx(a, "StarfallSource", _orient(starfall, "VelocityParallel"))
    # An aurora sigil turning on the ground under it, sending out rings of light.
    fx(a, "SigilCore",
       _orient(_grad(emitter("Sigil", WHITE, texture=VORTEX_TEXTURE, rate=0.6, lifetime=(3, 3), speed=(0.01, 0.01),
                             spread=0, sizes=((0, 26), (1, 26)), transparency=((0, 1), (0.25, 0.4), (0.75, 0.4), (1, 1)),
                             lock=True, rot_speed=(25, 25)), (0, _aurora(0.1)), (0.5, _aurora(0.45)), (1, _aurora(0.85))),
               "VelocityPerpendicular"),
       _orient(_grad(emitter("SigilGlow", WHITE, texture=GLOW_TEXTURE, rate=0.8, lifetime=(2, 2), speed=(0.01, 0.01),
                             spread=0, sizes=((0, 28), (1, 28)), transparency=((0, 1), (0.5, 0.7), (1, 1)), lock=True),
                     (0, _aurora(0.3)), (1, _aurora(0.7))), "VelocityPerpendicular"),
       _orient(_grad(emitter("SigilRipple", WHITE, texture=SHOCK_TEXTURE, rate=0.5, lifetime=(2, 2), speed=(0.01, 0.01),
                             spread=0, sizes=((0, 8), (1, 34)), transparency=((0, 0.4), (1, 1)), lock=True),
                     (0, _aurora(0.2)), (1, _aurora(0.8))), "VelocityPerpendicular"))
    # Spirit orbs glowing, joined by constellation lines.
    for i in range(8):
        fx(a, f"SpiritOrb{i}", _grad(emitter(f"OrbGlow{i}", WHITE, texture=GLOW_TEXTURE, rate=1, lifetime=(1.2, 1.2),
                                             speed=(0, 0), sizes=((0, 2.4), (0.5, 3.2), (1, 2.4)),
                                             transparency=((0, 1), (0.5, 0.55), (1, 1)), lock=True),
                                     (0, WHITE), (1, _aurora(i / 8))))
        q0, q1 = p(f"SpiritOrb{i}"), p(f"SpiritOrb{(i + 1) % 8}")
        beam(a, f"SpiritOrb{i}", q0, f"SpiritOrb{(i + 1) % 8}", q1, _aurora(i / 8), name=f"Constellation{i}",
             width=(0.25, 0.25), transparency=((0, 0.3), (0.5, 0.6), (1, 0.3)), segments=2,
             color2=_aurora((i + 1) / 8), texture=SPARKLE_TEXTURE, texture_speed=1.5)
    fx(a, "SpiritOrb0", light("OrbLight0", _aurora(0.0), brightness=1.0, range_=10, pulse=1.0))
    fx(a, "SpiritOrb4", light("OrbLight4", _aurora(0.5), brightness=1.0, range_=10, pulse=1.2))
    # The tail is a comet: a spinning swirl of light and a spray of stars.
    fx(a, "TailFan1",
       _grad(emitter("CometSwirl", WHITE, texture=VORTEX_TEXTURE, rate=1.5, lifetime=(1.2, 1.2), speed=(0, 0),
                     sizes=((0, 4), (0.5, 5), (1, 4)), transparency=((0, 1), (0.4, 0.35), (1, 1)), lock=True,
                     rot_speed=(-220, -160)), (0, WHITE), (1, _aurora(0.95))),
       emitter("CometSpray", WHITE, rate=14, lifetime=(0.8, 1.4), speed=(2, 5), sizes=((0, 0.5), (1, 0)),
               color2=_aurora(0.95), spread=50, drag=1.5, **SPARK))
    pulse(a, *[f"Fin{i}" for i in range(0, N + 1, 2)], seconds=1.2)
    pulse(a, *[f"Scale{i}L" for i in range(1, N + 1, 2)], *[f"Scale{i}R" for i in range(0, N + 1, 2)], seconds=0.9)
    extras(a, attrs={"WalkSpeed": 16, "OrbitSpeed": 0.3, "Hover": 1.4, "HoverSpeed": 1.3},
           highlight=(_aurora(0.3), C("#e9fff6"), 1.0, 0.35))
    return a


ALL = [pebble_marmot, pika_puff, cliff_kid, snowshoe_hare, bighorn_ram, alpine_ibex, red_panda, peak_eagle,
       mountain_yak, geode_tortoise, snow_leopard, frostfang_alpha, little_yeti, sky_griffin, glacier_mammoth,
       aurora_dragon]
