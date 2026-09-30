"""The Dark Woods animals (Critter Woods: Deep Woods and Heart), in the same blocky studded style as
animals.py. Each animal faces -Z, +X is its right side and y = 0 is the ground.

Rarer animals get real effects on top of the model: Trails that streak behind them while they run, Beams,
Highlights, rising smoke and spores, pulsing Neon, lights, and parts that orbit, hover or flap. The
moving bits are driven by the AnimalFX script (RunContext = Client), which reads these model attributes:

    FlapSpeed, FlapAngle   wings (joints named Wing*) flap up and down
    Hover, HoverSpeed      the whole body bobs up and down on the Root joint (the hitbox stays put)
    OrbitSpeed             the joint named Orbit spins around (orbiting orbs, rings, shards)
    TailSway               the Tail joint swings from side to side (degrees)

and the "Pulse" attribute (seconds) on Neon parts and lights, which makes them glow brighter and dimmer.
"""

import math

from lib import EYE, FIRE_TEXTURE, SIDES, SMOKE_TEXTURE, SPARKLE_TEXTURE, WHITE, Animal, add, aim, angles, apply, \
    cframe, compose, cross, hex_color as C, inverse, matmul, scale, sub, unit, IDENTITY

from animals import DETAIL, MOUTH, NEON, PINK, TONGUE, _canine, _deer, at, find, fx, pixel_star

GLOW = dict(material="Neon", role="Glow", shadow=False, studs=False)


# ------------------------------------------------------------- helpers ---

def scale_animal(a, k):
    """Scales the whole model (parts, joints, ride point) by k."""
    for p in a.parts:
        p["size"] = tuple(v * k for v in p["size"])
        p["p"] = tuple(v * k for v in p["p"])
    for bone in a.bones.values():
        if bone["pivot"] is not None:
            bone["pivot"] = tuple(v * k for v in bone["pivot"])
    if a.ride_height:
        a.ride_height *= k
    a.ride_z *= k
    if a.overhead:
        a.overhead *= k


def attach(a, part_name, world_pos, name, R=IDENTITY):
    """Attachment inside a part, placed at a world position. Returns its ref id."""
    part = find(a, part_name)
    rid = f"{a.id}.{name}"
    local = compose(inverse(part["R"], part["p"]), (R, world_pos))
    part["effects"].append({"class": "Attachment", "name": name, "id": rid, "props": {"CFrame": cframe(*local)}})
    return rid


def trail(a, part_name, p0, p1, color, name="Trail", lifetime=0.5, color2=None, width=None, light=1.0,
          transparency=((0, 0.2), (1, 1))):
    """Trail that streaks behind the part while the animal moves (p0/p1 = its two edges, in world space)."""
    r0 = attach(a, part_name, p0, f"{name}A")
    r1 = attach(a, part_name, p1, f"{name}B")
    color2 = color2 or color
    find(a, part_name)["effects"].append({"class": "Trail", "name": name, "props": {
        "Attachment0": {"ref": r0}, "Attachment1": {"ref": r1}, "Lifetime": lifetime, "LightEmission": light,
        "LightInfluence": 0, "FaceCamera": False, "MinLength": 0.05,
        "Color": [[0, *color], [1, *color2]], "Transparency": [list(t) for t in transparency],
        **({"WidthScale": [[0, 1], [1, width]]} if width is not None else {}),
    }})


def beam(a, part0, p0, part1, p1, color, name="Beam", width=(1, 1), curve=(0, 0), transparency=((0, 0.3), (1, 0.3)),
         light=1.0, segments=10, R0=IDENTITY, R1=IDENTITY, color2=None, texture=None, texture_speed=0,
         face_camera=True):
    r0 = attach(a, part0, p0, f"{name}A", R=R0)
    r1 = attach(a, part1, p1, f"{name}B", R=R1)
    color2 = color2 or color
    props = {
        "Attachment0": {"ref": r0}, "Attachment1": {"ref": r1}, "Width0": width[0], "Width1": width[1],
        "CurveSize0": curve[0], "CurveSize1": curve[1], "Segments": segments, "FaceCamera": face_camera,
        "LightEmission": light, "LightInfluence": 0, "Color": [[0, *color], [1, *color2]],
        "Transparency": [list(t) for t in transparency],
    }
    if texture:
        props.update(Texture=texture, TextureSpeed=texture_speed, TextureMode="Wrap", TextureLength=2)
    find(a, part0)["effects"].append({"class": "Beam", "name": name, "props": props})


def emitter(name, color, texture=SMOKE_TEXTURE, rate=4, lifetime=(1, 2), speed=(0.5, 1), spread=180,
            sizes=((0, 0.5), (1, 0)), transparency=((0, 0.3), (1, 1)), light=1.0, accel=(0, 0, 0), drag=0,
            color2=None, emit="Top", rot=(0, 360), rot_speed=(-60, 60), lock=False, zoffset=0):
    color2 = color2 or color
    return {"class": "ParticleEmitter", "name": name, "props": {
        "Texture": texture, "Rate": rate, "Lifetime": list(lifetime), "Speed": list(speed),
        "SpreadAngle": [spread, spread], "LightEmission": light, "LightInfluence": 0 if light else 1,
        "Size": [list(s) for s in sizes], "Transparency": [list(t) for t in transparency],
        "Color": [[0, *color], [1, *color2]], "Acceleration": list(accel), "Drag": drag,
        "EmissionDirection": emit, "Rotation": list(rot), "RotSpeed": list(rot_speed),
        "LockedToPart": lock, "ZOffset": zoffset,
    }}


def light(name, color, brightness=1.5, range_=12, pulse=None):
    node = Animal.light(color, brightness=brightness, range_=range_, name=name)
    if pulse:
        node["attrs"] = {"Pulse": pulse}
    return node


def pulse(a, *names, seconds=1.4):
    for n in names:
        find(a, n)["pulse"] = seconds


def plate(a, name, p0, p1, width, thick, color, up=(0, 1, 0), **kw):
    """Flat plate from p0 to p1 (a wing membrane strip); `width` runs sideways, `thick` along `up`."""
    import math as _m
    length = _m.dist(p0, p1)
    return a.box(name, (length, thick, width), scale(add(p0, p1), 0.5), color, R=aim(sub(p1, p0), roll_up=up), **kw)


def ground_ring(a, name, center, radius, color, n=16, size=(0.5, 0.12, 1.4), transparency=0.0):
    """Flat ring of neon bits on the ground around an animal (put it in the Orbit joint to make it spin)."""
    for i in range(n):
        ang = i * 2 * math.pi / n
        pos = add(center, (math.cos(ang) * radius, 0, math.sin(ang) * radius))
        a.box(f"{name}{i}", size, pos, color, rot=(0, -math.degrees(ang), 0), transparency=transparency, **GLOW)


def near(a, part_name, dy=0.25):
    """Two points just above and below a part's center (edges for a Trail)."""
    p = find(a, part_name)["p"]
    return add(p, (0, dy, 0)), add(p, (0, -dy, 0))


def seg(a, name, p, q, t, color, ext=0.5, **kw):
    """Square beam from p to q that runs a little past both ends, so chains of beams have no gaps at the bends."""
    d = unit(sub(q, p))
    e = t * ext
    return a.beam(name, sub(p, scale(d, e)), add(q, scale(d, e)), t, color, **kw)


def knuckle(a, name, p, before, after, t, color, **kw):
    """Joint block where two beams meet, turned halfway between both directions."""
    d = unit(add(unit(sub(p, before)), unit(sub(after, p))))
    return a.box(name, (t, t, t), p, color, R=aim(d), **kw)


def chain(a, name, pts, thickness, color, **kw):
    """Beams through a list of points, with joint blocks at every bend."""
    for i in range(len(pts) - 1):
        seg(a, f"{name}{i}", pts[i], pts[i + 1], thickness[i], color, **kw)
        if i > 0:
            knuckle(a, f"{name}Joint{i}", pts[i], pts[i - 1], pts[i + 1], (thickness[i - 1] + thickness[i]) / 2 * 1.02,
                    color, **kw)


_PIECES = ("", "Top", "Bottom", "BevelL", "BevelR", "BevelLowL", "BevelLowR")


def unfight(a, *names, d=0.03):
    """Grows overlay pieces (a belly, saddle or mask over the body) by `d` on every side. Otherwise their faces lie
    exactly on the body's faces, and Roblox shows flickering stripes there (z-fighting)."""
    for name in names:
        group = [p for p in a.parts if p["name"] in {name + s for s in _PIECES}]
        R = find(a, name)["R"]
        cols = [tuple(R[i][j] for i in range(3)) for j in range(3)]
        lo, hi = [1e9] * 3, [-1e9] * 3
        for p in group:
            half = scale(p["size"], 0.5)
            for corner in ((x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)):
                q = add(p["p"], apply(p["R"], tuple(c * h for c, h in zip(corner, half))))
                for j in range(3):
                    v = sum(q[i] * cols[j][i] for i in range(3))
                    lo[j], hi[j] = min(lo[j], v), max(hi[j], v)
        center = [(l + h) / 2 for l, h in zip(lo, hi)]
        k = [(h - l + 2 * d) / (h - l) for l, h in zip(lo, hi)]
        for p in group:
            local = [sum(p["p"][i] * cols[j][i] for i in range(3)) - center[j] for j in range(3)]
            new = [center[j] + local[j] * k[j] for j in range(3)]
            p["p"] = tuple(sum(cols[j][i] * new[j] for j in range(3)) for i in range(3))
            # Scale each of the part's own axes by the factor of the group axis it lines up with.
            size = []
            for m in range(3):
                axis = tuple(p["R"][i][m] for i in range(3))
                j = max(range(3), key=lambda j: abs(sum(axis[i] * cols[j][i] for i in range(3))))
                size.append(p["size"][m] * k[j])
            p["size"] = tuple(size)


def extras(a, attrs=None, highlight=None, script=True):
    a.dw_attrs = attrs or {}
    a.dw_highlight = highlight
    a.dw_script = script


# ------------------------------------------------------------ Common ----

def mossback_toad():
    a = Animal("MossbackToad", "Mossback Toad", "Common")
    green, dark, cream, moss, moss2 = C("#7aa843"), C("#587f30"), C("#e3eba0"), C("#2f8a3c"), C("#46a846")
    red = C("#e04a3c")

    a.oct("Body", (5.4, 2.8, 5.2), (0, 2.0, 0.4), green, b=1.0, bottom=0.6)
    a.bevel("Belly", (5.46, 1.0, 4.6), (0, 1.1, 0.3), cream, b=0, bottom=0.63, role="Secondary")
    a.oct("Moss", (4.6, 0.7, 4.4), (0, 3.55, 0.7), moss, b=0.3, role="Secondary")
    for i, (x, z, w) in enumerate([(-1.4, -0.4, 1.3), (1.2, 0.2, 1.1), (0.2, 1.9, 1.2), (1.5, 2.1, 0.8)]):
        a.box(f"MossTuft{i}", (w, 0.5, w), (x, 4.0, z), moss2, rot=(0, 20 * i, 0), role="Secondary")
    for i, (x, z) in enumerate([(-2.72, -0.3), (2.72, 1.2), (-2.72, 1.6)]):
        a.box(f"Wart{i}", (0.12, 0.5, 0.6), (x, 2.3, z), dark, **DETAIL)
    # Tiny toadstool growing on its back.
    a.post("ShroomStem", (0.5, 1.0, 0.5), (-0.9, 4.35, 1.4), C("#f7f1e3"), b=0.12, role="Accent")
    a.oct("ShroomCap", (1.9, 0.7, 1.9), (-0.9, 5.05, 1.4), red, b=0.3, role="Accent")
    for i, (x, z) in enumerate([(-1.3, 1.1), (-0.5, 1.8), (-0.8, 0.9)]):
        a.box(f"ShroomDot{i}", (0.3, 0.1, 0.3), (x, 5.43, z), WHITE, **DETAIL)

    with a.bone("Head", "Body", (0, 2.4, -1.8)):
        a.oct("Head", (5.0, 2.2, 2.6), (0, 2.5, -2.6), green, b=0.8, bottom=0.5)
        a.bevel("Chin", (4.6, 0.7, 2.2), (0, 1.55, -2.6), cream, b=0, bottom=0.3, role="Secondary")
        a.box("Mouth", (4.0, 0.14, 0.1), (0, 1.95, -3.92), C("#2e4a1c"), **DETAIL)
        for s, S in SIDES:
            a.box(f"MouthEnd{S}", (0.14, 0.45, 0.1), (2.0 * s, 2.1, -3.9), C("#2e4a1c"), **DETAIL)
            a.oct(f"EyeBump{S}", (1.9, 1.7, 1.8), (1.45 * s, 3.95, -2.6), green, b=0.5)
            a.eye2(f"Eye{S}", (1.45 * s, 4.05, -3.51), w=1.35, h=1.4, iris=C("#e0a81c"))
            a.box(f"Cheek{S}", (0.7, 0.35, 0.1), (2.0 * s, 2.55, -3.92), PINK, **DETAIL)
            a.box(f"Nostril{S}", (0.25, 0.15, 0.1), (0.4 * s, 3.1, -3.92), C("#2e4a1c"), **DETAIL)

    for s, S in SIDES:
        with a.bone(f"LegF{S}", "Body", (1.9 * s, 1.6, -1.4)):
            a.post(f"LegF{S}", (0.9, 1.3, 0.9), (2.1 * s, 0.95, -1.8), green, b=0.25)
            a.paw(f"PawF{S}", (2.2 * s, 0, -2.2), 1.3, 1.3, dark, h=0.45, toes=3)
        with a.bone(f"LegB{S}", "Body", (2.4 * s, 1.8, 1.6)):
            a.oct(f"Thigh{S}", (1.6, 1.6, 2.8), (2.75 * s, 1.25, 1.7), green, b=0.5)
            a.paw(f"FootB{S}", (3.0 * s, 0, 0.9), 1.7, 2.4, dark, h=0.45, toes=3)

    a.ride_height, a.ride_z = 4.3, 0.4
    unfight(a, "Belly", "Chin", "Moss")
    extras(a, script=False)
    return a


def shroom_snail():
    a = Animal("ShroomSnail", "Shroom Snail", "Common")
    skin, sole, gill, red = C("#d8c3a5"), C("#efe0c8"), C("#f2e2c8"), C("#e04a3c")

    a.bevel("Body", (3.0, 1.4, 7.4), (0, 0.7, 0.9), skin, b=0.5)
    a.box("Sole", (3.1, 0.34, 7.0), (0, 0.15, 0.9), sole, role="Secondary")
    a.wedge("TailTip", (2.6, 1.0, 1.8), (0, 0.5, 5.4), skin, rot=(0, 180, 0))
    a.oct("Neck", (2.4, 3.0, 2.2), (0, 2.0, -2.3), skin, b=0.6)
    # The shell is a big spotted toadstool.
    a.oct("Gills", (5.0, 0.6, 5.0), (0, 1.7, 1.6), gill, b=0.2, role="Secondary")
    for i, x in enumerate((-1.5, -0.5, 0.5, 1.5)):
        a.box(f"Gill{i}", (0.12, 0.3, 4.4), (x, 1.62, 1.6), C("#d9c3a2"), **DETAIL)
    a.oct("Cap", (6.2, 1.6, 6.2), (0, 2.75, 1.6), red, b=0.6, bottom=0.4)
    a.oct("CapUpper", (4.6, 1.2, 4.6), (0, 4.15, 1.6), red, b=0.5)
    a.oct("CapPeak", (2.8, 0.7, 2.8), (0, 5.05, 1.6), red, b=0.3)
    a.box("CapShine", (1.8, 0.14, 0.5), (-0.6, 4.78, 0.5), C("#ff7a66"), rot=(0, -20, 0), **DETAIL)
    for i, (x, z) in enumerate([(3.12, 0.9), (3.12, 2.6), (-3.12, 0.5), (-3.12, 2.3)]):
        a.box(f"SideSpot{i}", (0.12, 0.7, 0.8), (x, 2.75, z), WHITE, **DETAIL)
    for i, x in enumerate((0.0, 1.5, -1.5)):
        a.box(f"FrontSpot{i}", (0.8, 0.7, 0.12), (x, 2.75, -1.52), WHITE, **DETAIL)
    for i, (x, z) in enumerate([(1.1, 0.8), (-1.1, 2.5), (1.0, 2.6), (-1.1, 0.7)]):
        a.box(f"TopSpot{i}", (0.7, 0.12, 0.7), (x, 4.78, z), WHITE, **DETAIL)
    a.box("PeakSpot", (0.8, 0.12, 0.8), (0, 5.43, 1.6), WHITE, **DETAIL)

    with a.bone("Head", "Body", (0, 2.8, -2.4)):
        a.oct("Head", (2.8, 2.2, 2.4), (0, 3.9, -2.7), skin, b=0.7, bottom=0.4)
        a.box("Smile", (0.9, 0.14, 0.1), (0, 3.35, -3.92), C("#8a5a4a"), **DETAIL)
        for s, S in SIDES:
            a.beam(f"Stalk{S}", (0.6 * s, 4.7, -2.8), (1.0 * s, 6.3, -3.1), 0.36, skin)
            a.oct(f"EyeBall{S}", (1.1, 1.1, 1.0), (1.05 * s, 6.55, -3.15), skin, b=0.3)
            a.eye2(f"Eye{S}", (1.05 * s, 6.55, -3.67), w=0.85, h=0.95)
            a.box(f"Cheek{S}", (0.55, 0.3, 0.1), (0.95 * s, 3.65, -3.92), PINK, **DETAIL)

    # A glowing slime trail on the ground behind it while it moves.
    trail(a, "Sole", (-1.1, 0.05, 4.2), (1.1, 0.05, 4.2), C("#9ff5ff"), name="SlimeTrail", lifetime=3.0,
          color2=C("#5ef0d0"), light=0.8, transparency=((0, 0.35), (0.7, 0.6), (1, 1)))
    a.ride_height, a.ride_z = 5.5, 1.6
    extras(a, script=False)
    return a


# ---------------------------------------------------------- Uncommon ----

def duskbat():
    a = Animal("Duskbat", "Duskbat", "Uncommon")
    fur, belly, wing, bone_c = C("#4a3a6a"), C("#6a5a8a"), C("#3a2d57"), C("#5f4c86")
    y = 6.0

    a.oct("Body", (2.8, 2.8, 2.6), (0, y, 0.3), fur, b=0.8, bottom=0.6)
    a.oct("Belly", (1.9, 1.7, 0.3), (0, y - 0.3, -1.0), belly, b=0.4, role="Secondary")
    a.tuft("ChestFluff", (0, y - 1.0, -0.9), (1.4, 0.6, 0.6), belly, role="Secondary")
    a.box("Nose", (0.5, 0.3, 0.12), (0, y + 0.05, -1.06), C("#2a1f3a"), **DETAIL)
    for s, S in SIDES:
        a.eye2(f"Eye{S}", (0.62 * s, y + 0.5, -1.04), w=0.75, h=0.9, iris=C("#ffcc4a"))
        a.tri(f"Fang{S}", (0.3 * s, y - 0.45, -1.1), 0.28, 0.4, 0.1, WHITE, R=angles(0, 0, 180), **DETAIL)
        a.box(f"Cheek{S}", (0.45, 0.25, 0.1), (1.0 * s, y - 0.1, -1.05), PINK, **DETAIL)
        R = angles(0, 0, -14 * s)
        base = (0.8 * s, y + 1.3, -0.1)
        a.tri(f"Ear{S}", base, 1.1, 1.7, 0.45, fur, R=R)
        a.tri(f"InnerEar{S}", at(base, R, (0, 0.1, -0.25)), 0.6, 1.0, 0.1, PINK, R=R, **DETAIL)
        a.box(f"Foot{S}", (0.4, 0.6, 0.4), (0.6 * s, y - 1.65, 0.6), C("#2a1f3a"), **DETAIL)

        pivot = (1.3 * s, y + 0.3, 0.2)
        with a.bone(f"Wing{S}", "Body", pivot):
            a.box(f"Wing{S}", (3.2, 0.18, 2.4), add(pivot, (1.65 * s, 0, 0.3)), wing, studs=False)
            a.box(f"WingOuter{S}", (2.4, 0.16, 1.8), add(pivot, (4.3 * s, 0.05, 0.0)), wing, studs=False)
            a.box(f"WingTip{S}", (0.4, 0.3, 0.4), add(pivot, (5.45 * s, 0.1, -0.8)), bone_c)
            a.beam(f"Finger0{S}", add(pivot, (0.1 * s, 0.1, -0.7)), add(pivot, (5.4 * s, 0.1, -0.8)), 0.22, bone_c)
            a.beam(f"Finger1{S}", add(pivot, (3.0 * s, 0.1, -0.6)), add(pivot, (4.2 * s, 0.1, 0.9)), 0.16, bone_c)
            for i, x in enumerate((1.0, 2.4, 3.6, 4.8)):
                a.tri(f"Scallop{i}{S}", add(pivot, (x * s, 0, 1.4 if x < 3 else 0.85)), 1.0, 0.6, 0.16, wing,
                      R=angles(90, 0, 0), studs=False)
            # Short dusky streaks behind the wing tips while it flies.
            trail(a, f"WingTip{S}", add(pivot, (5.45 * s, 0.1, -0.6)), add(pivot, (5.45 * s, 0.1, -1.0)),
                  C("#b89cff"), name=f"WingTrail{S}", lifetime=0.3, color2=C("#4a3a6a"), light=0.6)

    a.ride_height, a.ride_z = y + 1.5, 0.3
    extras(a, attrs={"FlapSpeed": 14, "FlapAngle": 38, "Hover": 0.6, "HoverSpeed": 3})
    return a


def night_hedgehog():
    a = Animal("NightHedgehog", "Night Hedgehog", "Uncommon")
    spikes, cream, brown, glow = C("#4a3d33"), C("#e8d5b5"), C("#6b5646"), C("#5ef0ff")

    a.oct("Body", (4.2, 3.2, 5.2), (0, 2.3, 0.6), spikes, b=1.2, bottom=0.6,
          effects=[light("SpikeGlow", glow, brightness=1.0, range_=10, pulse=1.8)])
    a.bevel("Belly", (3.4, 0.9, 4.4), (0, 1.05, 0.5), cream, b=0, bottom=0.4, role="Secondary")
    n = 0
    for z in (-1.4, -0.5, 0.4, 1.3, 2.2):
        for x in (-1.8, -0.9, 0.0, 0.9, 1.8):
            if abs(x) > 1.5 and z < -1:
                continue
            base_y = 3.9 - max(0.0, abs(x) - 0.9)
            R = angles(32 + 8 * (z > 1), 0, -x * 20)
            h = 1.5 if abs(x) < 1 else 1.2
            a.shard(f"Spike{n}", (x, base_y - 0.3, z), 0.6, h, spikes, R=R)
            a.box(f"SpikeTip{n}", (0.3, 0.3, 0.3), at((x, base_y - 0.3, z), R, (0, h - 0.05, 0)), glow, R=R, **GLOW)
            if n % 3 == 0:
                find(a, f"SpikeTip{n}")["pulse"] = 1.8
            n += 1

    with a.bone("Head", "Body", (0, 2.2, -1.4)):
        a.oct("Head", (3.0, 2.4, 2.4), (0, 2.1, -2.3), cream, b=0.8, bottom=0.5)
        a.taper("Snout", (1.4, 1.0), (0.9, 0.7), 1.2, (0, 1.75, -3.9), cream, r=0.3)
        a.bevel("Nose", (0.6, 0.45, 0.35), (0, 1.9, -4.55), EYE, b=0.12, **DETAIL)
        a.box("NoseShine", (0.18, 0.1, 0.06), (-0.12, 2.02, -4.74), WHITE, **DETAIL)
        a.box("Smile", (0.5, 0.1, 0.08), (0, 1.45, -4.53), C("#5a2a3a"), **DETAIL)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (0.72 * s, 2.45, -3.52), w=0.72, h=0.9)
            a.box(f"Cheek{S}", (0.45, 0.25, 0.1), (1.05 * s, 1.95, -3.52), PINK, **DETAIL)
            a.oct(f"Ear{S}", (0.75, 0.75, 0.4), (1.15 * s, 3.25, -2.0), brown, b=0.2)

    for s, S in SIDES:
        for z, F in ((-1.2, "F"), (2.0, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (1.2 * s, 1.0, z)):
                a.post(f"Leg{F}{S}", (0.7, 0.8, 0.7), (1.25 * s, 0.6, z), brown, b=0.2)
                a.paw(f"Paw{F}{S}", (1.3 * s, 0, z - 0.2), 0.9, 1.0, brown, h=0.35, toes=3)

    a.ride_height, a.ride_z = 4.8, 0.6
    extras(a)
    return a


# -------------------------------------------------------------- Rare ----

def glowmoth():
    a = Animal("Glowmoth", "Glowmoth", "Rare")
    body_c, fluff, wing1, wing2, edge = C("#5a4a7a"), C("#efe6ff"), C("#3b2f5e"), C("#4a3b70"), C("#2a2046")
    cyan, gold = C("#9ff5ff"), C("#ffd166")
    y = 7.0

    a.oct("Body", (2.2, 2.2, 2.4), (0, y, 0), body_c, b=0.6,
          effects=[light("MothGlow", cyan, brightness=1.2, range_=12, pulse=2.2)])
    a.tuft("Collar", (0, y + 0.2, -0.9), (2.6, 1.2, 0.9), fluff, role="Secondary")
    a.taper("Abdomen", (1.9, 1.9), (0.9, 0.9), 3.4, (0, y - 0.4, 2.7), body_c, R=angles(12, 0, 0), r=0.35)
    for i, z in enumerate((1.8, 2.8, 3.8)):
        a.box(f"Stripe{i}", (1.9 - 0.3 * i, 0.3, 0.35), (0, y + 0.45 - 0.22 * i, z), fluff, rot=(12, 0, 0),
              role="Secondary")
    with a.bone("Head", "Body", (0, y + 0.2, -1.2)):
        a.oct("Head", (1.9, 1.7, 1.4), (0, y + 0.3, -1.7), body_c, b=0.45)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (0.5 * s, y + 0.45, -2.42), w=0.8, h=0.95, iris=C("#8a5cff"))
            a.beam(f"Antenna{S}", (0.4 * s, y + 1.1, -1.9), (1.3 * s, y + 2.9, -2.9), 0.16, C("#8f7fb8"))
            a.box(f"AntennaTip{S}", (0.35, 0.35, 0.35), (1.35 * s, y + 3.0, -2.95), gold, **GLOW)
            find(a, f"AntennaTip{S}")["pulse"] = 1.1
            for i, (x, z) in enumerate(((0.6, -0.6), (0.7, 0.4))):
                a.beam(f"Leg{i}{S}", (x * s, y - 0.9, z), ((x + 0.4) * s, y - 2.2, z - 0.2), 0.14, edge)

    for s, S in SIDES:
        pivot = (1.0 * s, y + 0.3, -0.2)
        Rw = matmul(angles(0, -8 * s, 0), angles(0, 0, 14 * s))
        with a.bone(f"Wing{S}", "Body", pivot):
            a.box(f"Wing{S}", (4.8, 0.16, 3.6), at(pivot, Rw, (2.6 * s, 0, -0.5)), wing1, R=Rw, studs=False)
            a.box(f"WingEdge{S}", (4.9, 0.14, 0.4), at(pivot, Rw, (2.65 * s, 0.02, -2.2)), edge, R=Rw, **DETAIL)
            a.box(f"WingBand{S}", (4.6, 0.18, 0.7), at(pivot, Rw, (2.6 * s, 0.01, 1.0)), C("#6a5a9a"), R=Rw,
                  **DETAIL)
            a.box(f"WingTip{S}", (0.6, 0.2, 0.6), at(pivot, Rw, (5.05 * s, 0.02, -2.2)), cyan, R=Rw, **GLOW)
            a.box(f"LowWing{S}", (3.2, 0.16, 2.8), at(pivot, Rw, (1.9 * s, -0.04, 2.4)), wing2, R=Rw, studs=False)
            a.box(f"LowTail{S}", (1.0, 0.16, 1.4), at(pivot, Rw, (2.6 * s, -0.05, 4.2)), wing2, R=Rw, studs=False)
            # Glowing eye spots: a cyan ring with a dark middle, and a gold spot on the low wing.
            a.box(f"EyeSpot{S}", (1.5, 0.2, 1.5), at(pivot, Rw, (3.3 * s, 0.03, -0.6)), cyan, R=Rw, **GLOW)
            a.box(f"EyeSpotCore{S}", (0.7, 0.24, 0.7), at(pivot, Rw, (3.3 * s, 0.04, -0.6)), wing1, R=Rw, **DETAIL)
            a.box(f"GoldSpot{S}", (0.8, 0.2, 0.8), at(pivot, Rw, (2.2 * s, -0.01, 2.6)), gold, R=Rw, **GLOW)
            pulse(a, f"EyeSpot{S}", f"GoldSpot{S}", seconds=1.6)
            # Glowing moth dust that drifts down from the wings.
            find(a, f"Wing{S}")["effects"].append(emitter(
                "MothDust", cyan, texture=SPARKLE_TEXTURE, rate=5, lifetime=(1.5, 2.5), speed=(0.2, 0.6),
                sizes=((0, 0.18), (0.5, 0.28), (1, 0)), transparency=((0, 0.1), (1, 1)),
                accel=(0, -1.2, 0), drag=1.5, color2=gold, emit="Bottom"))
            trail(a, f"WingTip{S}", at(pivot, Rw, (5.05 * s, 0.02, -1.9)), at(pivot, Rw, (5.05 * s, 0.02, -2.5)),
                  cyan, name=f"WingTrail{S}", lifetime=0.45, color2=C("#8a5cff"))

    a.ride_height, a.ride_z = y + 1.4, 0.5
    unfight(a, "WingBandL", "WingBandR", "EyeSpotCoreL", "EyeSpotCoreR", d=0.02)
    extras(a, attrs={"FlapSpeed": 8, "FlapAngle": 32, "Hover": 0.8, "HoverSpeed": 1.8})
    return a


def hollow_badger():
    a = Animal("HollowBadger", "Hollow Badger", "Rare")
    grey, dark, black, white, snout = C("#5a5a66"), C("#3a3a44"), C("#232329"), C("#f2f2f5"), C("#e4e2ea")
    dirt = C("#7a5a3a")

    a.oct("Body", (4.8, 3.4, 7.2), (0, 3.1, 0.7), grey, b=1.1, bottom=0.6)
    a.bevel("Belly", (4.86, 1.1, 6.4), (0, 1.95, 0.7), dark, b=0, bottom=0.63, role="Secondary")
    a.box("BackStripe", (1.3, 0.2, 5.6), (0, 4.82, 0.4), C("#b9b9c4"), role="Secondary")
    for s, S in SIDES:
        a.box(f"Flank{S}", (0.12, 1.2, 4.6), (2.42 * s, 3.3, 0.9), dark, **DETAIL)

    with a.bone("Head", "Body", (0, 3.4, -2.5)):
        a.oct("Head", (3.8, 3.0, 3.2), (0, 3.5, -3.6), black, b=0.9, bottom=0.5)
        a.box("HeadStripe", (1.2, 0.2, 3.0), (0, 5.02, -3.5), white, role="Secondary")
        a.box("FaceStripe", (1.2, 2.0, 0.2), (0, 4.0, -5.22), white, role="Secondary")
        a.taper("Snout", (1.9, 1.3), (1.3, 0.9), 1.5, (0, 2.95, -5.8), snout, r=0.3, role="Secondary")
        a.bevel("Nose", (0.8, 0.5, 0.35), (0, 3.2, -6.62), EYE, b=0.14, **DETAIL)
        a.box("NoseShine", (0.2, 0.1, 0.06), (-0.15, 3.33, -6.82), WHITE, **DETAIL)
        a.box("Mouth", (0.7, 0.12, 0.08), (0, 2.45, -6.55), C("#5a2a3a"), **DETAIL)
        for s, S in SIDES:
            a.box(f"CheekWhite{S}", (0.2, 1.3, 2.2), (1.92 * s, 3.1, -3.9), white, role="Secondary")
            a.eye2(f"Eye{S}", (0.95 * s, 3.85, -5.22), w=0.8, h=0.95, iris=C("#6b4226"), lid=black, lid_tilt=10 * s)
            a.oct(f"Ear{S}", (1.0, 0.9, 0.5), (1.55 * s, 5.0, -3.0), black, b=0.25)
            a.box(f"EarRim{S}", (0.8, 0.2, 0.52), (1.55 * s, 5.4, -3.0), white, **DETAIL)

    for s, S in SIDES:
        for z, F, w in ((-1.9, "F", 1.9), (3.1, "B", 1.6)):
            with a.bone(f"Leg{F}{S}", "Body", (1.7 * s, 2.2, z)):
                a.post(f"Leg{F}{S}", (1.5, 1.8, 1.5), (1.75 * s, 1.2, z), black, b=0.4)
                a.paw(f"Paw{F}{S}", (1.8 * s, 0, z - 0.3), w, 1.9, black, claws=WHITE if F == "F" else None, h=0.6)
            if F == "F":
                # Kicked-up dust at the digging claws, and dirt streaks behind them while it runs.
                find(a, f"Paw{F}{S}")["effects"].append(emitter(
                    "DigDust", C("#9a7a52"), rate=3, lifetime=(0.8, 1.4), speed=(1, 2), spread=40,
                    sizes=((0, 0.6), (1, 1.8)), transparency=((0, 0.45), (1, 1)), light=0, accel=(0, -2, 0),
                    drag=2, emit="Back"))
                trail(a, f"Paw{F}{S}", (1.8 * s, 0.1, z - 1.1), (1.8 * s, 0.55, z - 1.1), dirt,
                      name=f"DirtTrail{S}", lifetime=0.35, light=0, transparency=((0, 0.3), (1, 1)))

    with a.bone("Tail", "Body", (0, 3.6, 4.2)):
        a.oct("Tail", (1.2, 1.0, 1.4), (0, 3.7, 4.6), C("#b9b9c4"), b=0.35, role="Secondary")

    a.ride_height, a.ride_z = 5.0, 0.7
    unfight(a, "Belly")
    extras(a, script=False)
    return a


# -------------------------------------------------------------- Epic ----

def barkling():
    a = Animal("Barkling", "Barkling", "Epic")
    bark, groove, cut, ring = C("#6b4424"), C("#4a2e1c"), C("#e0b276"), C("#b8844c")
    leaf, leaf2, leaf3, moss = C("#3f8a3c"), C("#58a84a"), C("#2f7a38"), C("#4f9e4a")
    eye, firefly = C("#ffd166"), C("#fff27a")

    a.oct("Body", (4.4, 5.0, 4.4), (0, 4.3, 0), bark, b=1.1, bottom=0.9,
          effects=[light("EyeLight", eye, brightness=1.2, range_=10, pulse=1.3)])
    for i, (x, z, h) in enumerate([(2.22, -0.8, 3.6), (2.22, 0.9, 2.8), (-2.22, -0.3, 3.4), (-2.22, 1.2, 2.4),
                                   (0.9, 2.22, 3.2), (-0.8, 2.22, 2.6)]):
        size = (0.14, h, 0.35) if abs(x) > 2 else (0.35, h, 0.14)
        a.box(f"Groove{i}", size, (x, 4.2, z), groove, **DETAIL)
    a.oct("CutTop", (3.8, 0.3, 3.8), (0, 6.82, 0), cut, b=0.12, role="Secondary")
    a.oct("CutRing", (2.2, 0.34, 2.2), (0, 6.86, 0), ring, b=0.12, **DETAIL)
    a.box("MossFront", (2.6, 0.6, 0.3), (-0.5, 2.3, -2.25), moss, role="Secondary")
    a.post("ShroomStem", (0.4, 0.8, 0.4), (2.3, 3.5, 0.6), C("#f7f1e3"), b=0.1, role="Accent")
    a.oct("ShroomCap", (1.4, 0.5, 1.4), (2.3, 4.0, 0.6), C("#e04a3c"), b=0.2, role="Accent")

    # Face: glowing eyes under bark brows and a wooden grin.
    for s, S in SIDES:
        a.box(f"Eye{S}", (0.9, 1.0, 0.2), (0.85 * s, 5.2, -2.25), eye, **GLOW)
        find(a, f"Eye{S}")["pulse"] = 1.3
        a.box(f"Pupil{S}", (0.35, 0.45, 0.24), (0.85 * s - 0.1 * s, 5.1, -2.28), C("#6b3a10"), **DETAIL)
        a.box(f"Brow{S}", (1.3, 0.35, 0.4), (0.85 * s, 5.95, -2.28), groove, rot=(0, 0, -12 * s), role="Accent")
        a.tooth(f"Tooth{S}", (0.35 * s, 3.85, -2.3), 0.4, 0.4, color=cut, R=angles(0, 0, 0))
    a.box("Mouth", (1.8, 0.45, 0.2), (0, 3.95, -2.25), C("#2a1a10"), **DETAIL)
    for s, S in SIDES:
        a.box(f"MouthEnd{S}", (0.35, 0.3, 0.2), (1.0 * s, 4.15, -2.25), C("#2a1a10"), **DETAIL)

    # Leaf crown: chunky leaf blocks turned every which way.
    for i, (x, y, z, w, h, rx, ry, rz, col) in enumerate([
            (0, 7.5, 0, 3.4, 1.4, 0, 20, 0, leaf), (1.2, 7.9, -0.8, 2.0, 1.2, 15, 40, -12, leaf2),
            (-1.3, 7.8, -0.5, 2.0, 1.2, -10, 10, 18, leaf2), (0.4, 8.3, 1.1, 2.2, 1.2, 12, 60, 10, leaf3),
            (-0.6, 8.6, -0.1, 1.8, 1.2, -8, 30, -8, leaf2), (1.5, 7.4, 1.2, 1.6, 1.0, 20, 5, -20, leaf3),
            (-1.6, 7.3, 1.1, 1.6, 1.0, -18, 50, 22, leaf)]):
        a.box(f"Leaf{i}", (w, h, w), (x, y, z), col, rot=(rx, ry, rz), role="Secondary",
              effects=[emitter("FallingLeaves", C("#6fcf5a"), rate=1.5, lifetime=(2.5, 3.5), speed=(0.5, 1),
                               sizes=((0, 0.45), (1, 0.35)), transparency=((0, 0.1), (0.8, 0.2), (1, 1)), light=0,
                               accel=(0.3, -1.5, 0), drag=0.8, color2=C("#d9b84a"), rot_speed=(-120, 120))]
              if i == 0 else None)

    for s, S in SIDES:
        pivot = (2.1 * s, 4.9, 0)
        with a.bone(f"Arm{S}", "Body", pivot):
            elbow = (3.4 * s, 5.6, -0.4)
            hand = (4.0 * s, 6.9, -0.9)
            a.rod(f"Arm{S}", pivot, elbow, 0.75, bark)
            a.rod(f"Forearm{S}", elbow, hand, 0.6, bark)
            a.rod(f"Twig{S}", hand, (4.7 * s, 7.6, -1.1), 0.35, bark)
            a.rod(f"Twig2{S}", hand, (3.6 * s, 7.8, -1.2), 0.3, bark)
            a.box(f"HandLeaf{S}", (0.9, 0.5, 0.9), (4.75 * s, 7.8, -1.1), leaf2, rot=(20, 30, 10 * s))
        with a.bone(f"Leg{S}", "Body", (1.1 * s, 1.8, 0)):
            a.post(f"Leg{S}", (1.4, 1.5, 1.4), (1.2 * s, 1.05, 0.1), groove, b=0.35)
            for j, yaw in enumerate((-30, 20, 80 * s)):
                R = angles(0, yaw, 0)
                a.wedge(f"Root{j}{S}", (0.7, 0.6, 1.3), add((1.2 * s, 0.3, 0.1), apply(R, (0, 0, -0.9))), groove,
                        R=R)

    # Three fireflies that orbit its leafy head.
    with a.bone("Orbit", "Body", (0, 8.0, 0)):
        for i in range(3):

            ang = i * 2 * math.pi / 3
            pos = (math.cos(ang) * 3.4, 8.0 + 0.6 * math.sin(ang * 2), math.sin(ang) * 3.4)
            a.box(f"Firefly{i}", (0.35, 0.35, 0.35), pos, firefly, rot=(45, 45, 0), **GLOW,
                  effects=[light("FireflyLight", firefly, brightness=0.8, range_=6)] if i == 0 else None)
            trail(a, f"Firefly{i}", add(pos, (0, 0.15, 0)), add(pos, (0, -0.15, 0)), firefly,
                  name=f"FireflyTrail{i}", lifetime=0.5, color2=C("#b8ff6a"))

    a.ride_height, a.ride_z = 7.0, 0
    extras(a, attrs={"OrbitSpeed": 1.4})
    return a


# --------------------------------------------------------- Legendary ----

def wisp_lynx():
    a = Animal("WispLynx", "Wisp Lynx", "Legendary")
    fur, light_c, dark, wisp = C("#5a6b86"), C("#cdd8e6"), C("#3d4a60"), C("#9ff5ff")

    def head_extra(a):
        for s, S in SIDES:
            R = angles(-6, 0, -12 * s)
            tip = at((1.3 * s, 9.1, -3.4), R, (0, 2.5, 0))
            a.box(f"EarTuft{S}", (0.3, 1.3, 0.3), add(tip, (0.1 * s, 0.55, 0)), C("#1f2533"), R=R, role="Accent")
            a.box(f"TuftGlow{S}", (0.42, 0.42, 0.42), add(tip, (0.2 * s, 1.3, 0)), wisp, R=R, **GLOW)
            find(a, f"TuftGlow{S}")["pulse"] = 1.2
            trail(a, f"TuftGlow{S}", add(tip, (0.2 * s, 1.5, 0)), add(tip, (0.2 * s, 1.1, 0)), wisp,
                  name=f"TuftTrail{S}", lifetime=0.6, color2=C("#5ea8ff"))
            for i, y in enumerate((6.3, 5.6)):
                a.tuft(f"Ruff{i}{S}", (2.55 * s, y, -3.9), (0.5, 1.2, 1.6), light_c, R=angles(0, 35 * s, -15 * s),
                       role="Secondary")

    def tail(a):
        with a.bone("Tail", "Body", (0, 5.6, 4.1)):
            R = angles(-30, 0, 0)
            a.bevel("Tail", (1.5, 1.5, 1.8), at((0, 5.6, 4.1), R, (0, 0, 1.0)), fur, b=0.4, bottom=0.4, R=R)
            a.bevel("TailTip", (1.56, 1.56, 0.8), at((0, 5.6, 4.1), R, (0, 0, 2.2)), C("#1f2533"), b=0.4,
                    bottom=0.4, R=R, role="Accent")

    _canine(a, fur, light_c, dark=dark, snout="cat", ear=(1.8, 2.5), brows=False, fangs=False, paws=light_c,
            eye=dict(iris=wisp, pupil=C("#16324a")), head_extra=head_extra, tail=tail, mask=True)
    for part in a.parts:
        if part["name"] in ("EyeLIris", "EyeRIris"):
            part.update(material="Neon", role="Glow")
    for s, S in SIDES:
        for i, (y, z) in enumerate([(5.6, -1.2), (4.8, 0.2), (5.8, 1.4), (4.9, 2.6), (5.4, 3.6)]):
            a.box(f"Spot{i}{S}", (0.12, 0.45, 0.6), (2.12 * s, y, z), dark, **DETAIL)
    # Ghostly: the fur is a little see-through.
    for part in a.parts:
        if part["role"] in ("Primary", "Secondary"):
            part["transparency"] = 0.18
    fx(a, "Body",
       emitter("WispSmoke", wisp, rate=6, lifetime=(1.2, 2.0), speed=(0.4, 1.0), sizes=((0, 0.8), (1, 2.2)),
               transparency=((0, 0.55), (1, 1)), accel=(0, 1.5, 0), drag=1, color2=C("#5ea8ff")),
       light("WispGlow", wisp, brightness=1.0, range_=12, pulse=2.0))
    # Three wisps that circle around it.
    with a.bone("Orbit", "Body", (0, 6.0, 0.6)):
        for i in range(3):
            ang = i * 2 * math.pi / 3
            pos = (math.cos(ang) * 4.6, 6.0 + math.sin(ang * 2) * 1.2, 0.6 + math.sin(ang) * 5.4)
            a.box(f"Wisp{i}", (0.55, 0.55, 0.55), pos, wisp, rot=(45, 45, 0), **GLOW,
                  effects=[emitter("WispFlame", wisp, rate=10, lifetime=(0.4, 0.7), speed=(0.5, 1.2), spread=20,
                                   sizes=((0, 0.6), (1, 0)), transparency=((0, 0.2), (1, 1)), color2=C("#5ea8ff"),
                                   accel=(0, 2, 0))])
            trail(a, f"Wisp{i}", add(pos, (0, 0.25, 0)), add(pos, (0, -0.25, 0)), wisp, name=f"WispTrail{i}",
                  lifetime=0.7, color2=C("#5ea8ff"))
    unfight(a, "Belly", "FaceMask", "Chest")
    unfight(a, "Saddle", d=0.04)  # the fur is see-through, so even its inner faces must not line up with the body
    extras(a, attrs={"OrbitSpeed": 1.1, "TailSway": 18},
           highlight=(wisp, wisp, 0.82, 0.35))
    return a


def moonraven():
    a = Animal("Moonraven", "Moonraven", "Legendary")
    black, sheen, beak, moon, pale = C("#1f1a2e"), C("#3b2d57"), C("#4a4a58"), C("#e8eeff"), C("#b9c8ff")

    a.oct("Body", (3.2, 3.6, 4.4), (0, 4.6, 0.5), black, b=1.0, bottom=0.8,
          effects=[light("MoonGlow", pale, brightness=1.4, range_=14, pulse=2.4)])
    a.oct("Chest", (2.6, 2.8, 0.5), (0, 4.5, -1.9), sheen, b=0.6, role="Secondary")
    # Glowing silver crescent moon on its chest.
    z = -2.2
    for name, size, pos in [("MoonA", (0.4, 1.2, 0.14), (-0.6, 4.5, z)), ("MoonB", (0.4, 1.9, 0.14), (-0.2, 4.5, z)),
                            ("MoonC", (0.5, 0.4, 0.14), (0.25, 5.3, z)), ("MoonD", (0.5, 0.4, 0.14), (0.25, 3.7, z))]:
        a.box(name, size, pos, moon, **GLOW)
        find(a, name)["pulse"] = 2.4
    for i, x in enumerate((0.0, -0.9, 0.9)):
        R = angles(18, x * 16, 0)
        a.box(f"TailFeather{i}", (0.9, 0.3, 3.0), at((x * 0.6, 3.6, 2.5), R, (0, 0, 1.3)), black, R=R)
        a.box(f"TailSheen{i}", (0.5, 0.32, 1.1), at((x * 0.6, 3.6, 2.5), R, (0, 0.02, 2.3)), sheen, R=R, **DETAIL)

    with a.bone("Head", "Body", (0, 6.0, -1.2)):
        a.oct("Head", (2.6, 2.4, 2.6), (0, 7.1, -1.6), black, b=0.7)
        a.taper("Beak", (1.2, 0.9), (0.45, 0.35), 1.9, (0, 6.8, -3.7), beak, r=0.25, role="Accent")
        a.box("BeakHook", (0.4, 0.5, 0.4), (0, 6.55, -4.55), beak, role="Accent")
        a.box("BeakLine", (1.1, 0.08, 1.6), (0, 6.72, -3.5), C("#2a2a36"), **DETAIL)
        for i, (x, h) in enumerate([(0, 1.2), (0.45, 0.9), (-0.45, 0.9)]):
            a.wedge(f"Crest{i}", (0.35, h, 1.1), (x, 8.3 + h / 2, -1.2), black, rot=(0, 180, 0))
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (0.9 * s, 7.4, -2.92), w=0.85, h=0.95, iris=pale, pupil=C("#1b1430"))
            a.box(f"Brow{S}", (0.9, 0.25, 0.2), (0.9 * s, 8.05, -2.92), sheen, rot=(0, 0, 10 * s), **DETAIL)

    for s, S in SIDES:
        pivot = (1.6 * s, 5.8, -0.6)
        with a.bone(f"Wing{S}", "Body", pivot):
            a.bevel(f"Wing{S}", (0.5, 3.0, 4.4), (1.85 * s, 4.8, 1.0), black, b=0.2)
            a.box(f"WingSheen{S}", (0.54, 0.9, 3.6), (1.87 * s, 5.7, 0.9), sheen, role="Secondary")
            for i, (y, length) in enumerate([(3.7, 2.6), (4.15, 2.2), (4.6, 1.8)]):
                a.box(f"Primary{i}{S}", (0.45, 0.45, length), (1.75 * s, y, 3.0 + length / 2), black, rot=(10, 0, 0))
        with a.bone(f"Leg{S}", "Body", (0.7 * s, 2.6, 0.6)):
            a.post(f"Leg{S}", (0.4, 3.0, 0.4), (0.7 * s, 1.6, 0.6), beak, b=0.1, role="Accent")
            for j, yaw in enumerate((-25, 0, 25)):
                R = angles(0, yaw, 0)
                a.box(f"Toe{j}{S}", (0.25, 0.25, 1.1), add((0.7 * s, 0.13, 0.6), apply(R, (0, 0, -0.5))), beak, R=R,
                      role="Accent")
            a.box(f"BackToe{S}", (0.25, 0.25, 0.7), (0.7 * s, 0.13, 1.1), beak, role="Accent")

    # A soft beam of moonlight falls on it from above.
    beam(a, "Body", (0, 26, 0.5), "Body", (0, 4.5, 0.5), pale, name="Moonbeam", width=(9, 5),
         transparency=((0, 1), (0.25, 0.82), (1, 0.7)), light=1, segments=2, color2=moon)
    # Falling dark feathers.
    fx(a, "Body", emitter("Feathers", C("#2c2440"), rate=1.2, lifetime=(2.5, 3.5), speed=(0.3, 0.8),
                          sizes=((0, 0.5), (1, 0.4)), transparency=((0, 0.1), (0.8, 0.3), (1, 1)), light=0,
                          accel=(0.4, -1.2, 0), drag=1, rot_speed=(-180, 180), color2=C("#3b2d57")))
    # Three moon shards circle around it, leaving silver streaks.
    with a.bone("Orbit", "Body", (0, 5.5, 0.4)):
        for i in range(3):
            ang = i * 2 * math.pi / 3
            pos = (math.cos(ang) * 3.8, 5.8 + math.sin(ang * 2) * 0.9, 0.4 + math.sin(ang) * 3.8)
            a.shard(f"MoonShard{i}", pos, 0.7, 1.7, pale, R=angles(20, i * 50, 15), cross=True, **GLOW)
            trail(a, f"MoonShard{i}", add(pos, (0, 0.9, 0)), add(pos, (0, 0.2, 0)), moon, name=f"ShardTrail{i}",
                  lifetime=0.8, color2=C("#8a7dff"))

    a.ride_height, a.ride_z = 7.0, 0.4
    unfight(a, "WingSheenL", "WingSheenR", d=0.02)
    extras(a, attrs={"OrbitSpeed": 0.9}, highlight=(pale, C("#cdd6ff"), 1.0, 0.25))
    return a


# ------------------------------------------------------------ Mythic ----

def umbra_panther():
    a = Animal("UmbraPanther", "Umbra Panther", "Mythic")
    fur, soft, dark, void, violet = C("#1d1a26"), C("#2a2536"), C("#141119"), C("#b861ff"), C("#e3b8ff")
    k = 1.2

    def tail(a):
        with a.bone("Tail", "Body", (0, 5.4, 4.1)):
            pts = [(0, 5.4, 4.1), (0, 5.0, 6.2), (0, 5.6, 8.0), (0, 7.2, 9.0), (0, 8.6, 8.6)]
            chain(a, "Tail", pts, [1.0 - 0.12 * i for i in range(4)], fur)
            a.box("TailTip", (0.8, 0.8, 0.8), (0, 8.9, 8.4), void, rot=(45, 0, 45), **GLOW)

    def head_extra(a):
        a.box("Brand", (0.6, 0.6, 0.14), (0, 8.6, -5.78), void, rot=(0, 0, 45), **GLOW)

    _canine(a, fur, soft, dark=dark, snout="cat", ear=(1.7, 2.1), brows=True, fangs=True, paws=fur,
            eye=dict(white=violet, iris=None, pupil=C("#3a1466")), head_extra=head_extra, tail=tail,
            brow_color=dark)
    find(a, "EyeR")["material"] = find(a, "EyeL")["material"] = "Neon"
    for part in a.parts:
        if part["name"].startswith("InnerEar"):
            part.update(material="Neon", role="Glow", studs=False, color=void)
    # Glowing purple rosettes on its flanks and back.
    n = 0
    for s, S in SIDES:
        for (y, z, w) in [(5.4, -1.3, 0.6), (4.6, 0.0, 0.5), (5.6, 1.1, 0.6), (4.7, 2.3, 0.5), (5.3, 3.4, 0.5)]:
            a.box(f"Rosette{n}", (0.14, w, w), (2.12 * s, y, z), void, **GLOW)
            find(a, f"Rosette{n}")["pulse"] = 1.8
            n += 1
    for (x, z) in [(0.8, -1.5), (-0.7, 0.2), (0.6, 1.8), (-0.5, 3.1)]:
        a.box(f"Rosette{n}", (0.6, 0.14, 0.6), (x, 6.43, z), void, **GLOW)
        find(a, f"Rosette{n}")["pulse"] = 1.8
        n += 1
    # A spinning ring of shadow on the ground and two orbs circling it.
    with a.bone("Orbit", "Body", (0, 5.0, 0.6)):
        ground_ring(a, "ShadowRing", (0, 0.06, 0.6), 6.0, void, n=20, size=(0.45, 0.1, 1.6), transparency=0.3)
        for i, ang in enumerate((0, math.pi)):
            pos = (math.cos(ang) * 4.4, 7.4, 0.6 + math.sin(ang) * 4.4)
            a.box(f"ShadowOrb{i}", (0.8, 0.8, 0.8), pos, void, rot=(45, 45, 0), **GLOW)
    scale_animal(a, k)

    fx(a, "Body",
       emitter("ShadowSmoke", C("#2a1640"), rate=8, lifetime=(1.2, 2.0), speed=(0.3, 0.9), sizes=((0, 1.4), (1, 3.4)),
               transparency=((0, 0.45), (1, 1)), light=0, accel=(0, 1.2, 0), drag=1, color2=C("#0d0a14")),
       emitter("VoidEmbers", void, texture=SPARKLE_TEXTURE, rate=5, lifetime=(1, 1.8), speed=(0.5, 1.5),
               sizes=((0, 0.35), (1, 0)), transparency=((0, 0.1), (1, 1)), accel=(0, 2.5, 0), color2=violet),
       light("VoidGlow", void, brightness=1.6, range_=16, pulse=1.8))
    for i in range(2):
        fx(a, f"ShadowOrb{i}", emitter("OrbSmoke", C("#2a1640"), rate=12, lifetime=(0.6, 1.0), speed=(0.2, 0.5),
                                       sizes=((0, 1.0), (1, 0.2)), transparency=((0, 0.3), (1, 1)), light=0))
        trail(a, f"ShadowOrb{i}", *near(a, f"ShadowOrb{i}", 0.4), void, name=f"OrbTrail{i}", lifetime=0.8,
              color2=C("#3a1466"))
    for s, S in SIDES:
        # Violet streaks behind its eyes while it sprints.
        trail(a, f"Eye{S}", *near(a, f"Eye{S}", 0.3), violet, name=f"EyeTrail{S}", lifetime=0.4, color2=void)
        fx(a, f"PawF{S}", emitter("ShadowStep", C("#2a1640"), rate=3, lifetime=(0.5, 0.9), speed=(0.2, 0.6),
                                  sizes=((0, 1.0), (1, 2.0)), transparency=((0, 0.5), (1, 1)), light=0, emit="Bottom"))
    trail(a, "TailTip", *near(a, "TailTip", 0.4), void, name="TailTrail", lifetime=0.6, color2=C("#3a1466"))
    unfight(a, "Belly", "Saddle", "FaceMask", "Chest")
    extras(a, attrs={"OrbitSpeed": 0.8, "TailSway": 20}, highlight=(void, void, 1.0, 0.15))
    return a


def mossking_elk():
    a = Animal("MosskingElk", "Mossking Elk", "Mythic")
    fur, light_c, hoof, moss, moss2 = C("#5b4a33"), C("#8a7658"), C("#2a2018"), C("#3f8a3c"), C("#58a84a")
    wood, glow, glow2, flower = C("#6b4424"), C("#5ef0ff"), C("#bdfbff"), C("#ff9ec4")
    k = 1.6
    tips = []

    def antlers(a):
        for s, S in SIDES:
            base = (0.9 * s, 11.2, -2.9)
            p1 = (2.0 * s, 12.8, -2.4)
            p2 = (3.6 * s, 14.2, -1.6)
            p3 = (4.0 * s, 16.0, -2.4)
            p4 = (2.4 * s, 15.2, -3.4)
            p5 = (4.9 * s, 14.4, -0.4)
            for i, (u, v) in enumerate([(base, p1), (p1, p2), (p2, p3), (p1, p4), (p2, p5)]):
                a.rod(f"Antler{i}{S}", u, v, 0.45 - 0.05 * i, wood, role="Accent")
            for i, tip in enumerate((p3, p4, p5)):
                a.box(f"Shroom{i}{S}", (0.9, 0.35, 0.9), add(tip, (0, 0.1, 0)), glow, **GLOW)
                a.box(f"ShroomTop{i}{S}", (0.5, 0.25, 0.5), add(tip, (0, 0.36, 0)), glow2, **GLOW)
                find(a, f"Shroom{i}{S}")["pulse"] = 1.6 + 0.3 * i
            tips.append(p3)
            for i, (pt, rot) in enumerate([(p1, 20), (p2, -30)]):
                a.box(f"AntlerLeaf{i}{S}", (0.8, 0.2, 0.5), add(pt, (0.3 * s, 0.1, 0)), moss2, rot=(0, rot, 20 * s))

    def head_extra(a):
        a.box("Beard", (1.4, 1.4, 0.8), (0, 8.2, -4.2), moss, role="Secondary")
        a.box("BeardTip", (0.9, 0.8, 0.6), (0, 7.3, -4.13), moss2, role="Secondary")

    _deer(a, fur, light_c, hoof, antlers=antlers, head_extra=head_extra, iris=C("#2a6f7a"), tail=light_c)
    for part in a.parts:
        if part["name"] in ("EyeLIris", "EyeRIris"):
            part.update(material="Neon", role="Glow", color=glow)
    # Moss mantle over its shoulders and back, with a few tufts hanging down.
    a.bevel("MossMantle", (3.9, 1.0, 4.6), (0, 7.45, -0.6), moss, b=0.35, role="Secondary")
    for s, S in SIDES:
        for i, (z, h) in enumerate([(-2.0, 1.4), (-0.6, 1.8), (0.9, 1.2)]):
            a.box(f"MossDrape{i}{S}", (0.3, h, 1.1), (1.95 * s, 7.2 - h / 2, z), moss, role="Secondary")
    for i, (x, z) in enumerate([(-0.9, -1.8), (0.8, -0.3), (-0.4, 1.0)]):
        a.box(f"MossTuft{i}", (1.1, 0.5, 1.1), (x, 8.05, z), moss2, rot=(0, 30 * i, 0), role="Secondary")
    a.post("BackShroomStem", (0.35, 0.7, 0.35), (0.9, 8.2, 0.9), C("#e8f7f5"), b=0.1, role="Accent")
    a.box("BackShroom", (1.0, 0.35, 1.0), (0.9, 8.6, 0.9), glow, **GLOW)
    # A ring of little glowing flowers that slowly turns around it.
    with a.bone("Orbit", "Body", (0, 5.0, 0.4)):
        for i in range(12):
            ang = i * 2 * math.pi / 12
            pos = (math.cos(ang) * 5.0, 0.15, 0.4 + math.sin(ang) * 6.2)
            a.box(f"Bloom{i}", (0.45, 0.2, 0.45), pos, flower if i % 2 else glow2, rot=(0, 45, 0), **GLOW)
            a.box(f"BloomLeaf{i}", (0.8, 0.08, 0.3), add(pos, (0, -0.08, 0)), moss2, rot=(0, -math.degrees(ang), 0),
                  **DETAIL)
    scale_animal(a, k)

    fx(a, "Body",
       emitter("Spores", glow, texture=SPARKLE_TEXTURE, rate=6, lifetime=(3, 4.5), speed=(0.3, 0.8),
               sizes=((0, 0.25), (0.5, 0.4), (1, 0)), transparency=((0, 0.2), (1, 1)), accel=(0, 0.8, 0), drag=0.5,
               color2=C("#b8ff6a")),
       light("MossLight", glow, brightness=1.4, range_=20, pulse=2.2))
    for s, S in SIDES:
        fx(a, f"Shroom0{S}", light("AntlerLight", glow, brightness=1.2, range_=12, pulse=1.6),
           emitter("AntlerSpores", glow2, texture=SPARKLE_TEXTURE, rate=3, lifetime=(2, 3), speed=(0.2, 0.6),
                   sizes=((0, 0.3), (1, 0)), transparency=((0, 0.2), (1, 1)), accel=(0, 1, 0), drag=0.5))
        for F in ("F", "B"):
            fx(a, f"Hoof{F}{S}", emitter("MossStep", moss2, rate=2, lifetime=(0.6, 1.0), speed=(0.5, 1.2), spread=60,
                                         sizes=((0, 0.6), (1, 1.2)), transparency=((0, 0.4), (1, 1)), light=0,
                                         emit="Bottom", accel=(0, -1, 0)))
    # A glowing arch of life energy between the two antler tops.
    t0, t1 = (scale(tips[0], k)), (scale(tips[1], k))
    beam(a, "Shroom0R", add(t0, (0, 0.8, 0)), "Shroom0L", add(t1, (0, 0.8, 0)), glow, name="LifeArc",
         width=(0.5, 0.5), curve=(4, -4), transparency=((0, 0.2), (0.5, 0.05), (1, 0.2)), segments=24,
         R0=angles(0, 0, 90), R1=angles(0, 0, 90), color2=C("#b8ff6a"), texture=SPARKLE_TEXTURE, texture_speed=1.5)
    unfight(a, "Belly", "Chest", "Jaw")
    # The smile from _deer sits flush with the front of the jaw; move it out a little so it doesn't flicker.
    smile = find(a, "Smile")
    smile["p"] = add(smile["p"], (0, 0, -0.05))
    extras(a, attrs={"OrbitSpeed": 0.35}, highlight=(glow, glow, 1.0, 0.55))
    return a


# ------------------------------------------------------------ Secret ----

def _lerp(p, q, t):
    return tuple(a + (b - a) * t for a, b in zip(p, q))


def membrane(a, name, apex, b, c, color, strips=3, **kw):
    """Fills the triangle apex-b-c with flat plates (a wing membrane)."""
    normal = unit(cross(sub(b, apex), sub(c, apex)))
    if normal[1] < 0:
        normal = tuple(-v for v in normal)
    edge = math.dist(b, c)
    for i in range(strips):
        p = _lerp(b, c, (i + 0.5) / strips)
        w = edge / strips * 1.1
        plate(a, f"{name}{i}o", _lerp(apex, p, 0.36), p, w, 0.12, color, up=normal, **kw)
        plate(a, f"{name}{i}i", apex, _lerp(apex, p, 0.42), w * 0.45, 0.12, color, up=normal, **kw)


def nightshade_drake():
    a = Animal("NightshadeDrake", "Nightshade Drake", "Secret")
    body, dark, plate_c, horn = C("#1f3a3a"), C("#16302f"), C("#2a4a48"), C("#cfe9e6")
    glow, glow2, membrane_c, inner = C("#5ef0b0"), C("#7dffc4"), C("#123030"), C("#0c2222")
    y = 8.0

    # ---- body: chest, shoulders, hips, scales and a glowing heart ----
    a.oct("Body", (3.8, 3.2, 6.0), (0, y, 0.4), body, b=1.0, bottom=0.8)
    a.oct("Chest", (3.4, 2.8, 1.8), (0, y + 0.1, -2.5), body, b=0.9, bottom=0.7)
    a.oct("Hips", (3.2, 2.6, 2.2), (0, y - 0.1, 3.2), body, b=0.8, bottom=0.6)
    for s, S in SIDES:
        a.oct(f"Shoulder{S}", (1.3, 1.8, 2.2), (1.85 * s, y + 0.45, -1.3), body, b=0.45)
        for row, yy in enumerate((y - 0.35, y + 0.35)):
            for i, z in enumerate((-1.6, -0.7, 0.2, 1.1, 2.0, 2.9)):
                zz = z + 0.45 * row
                if row == 1 and i == 0:
                    continue  # this one would sit inside the shoulder
                col = plate_c if (i + row) % 2 else dark
                a.box(f"Scale{row}{i}{S}", (0.12, 0.5, 0.7), (1.92 * s, yy, zz), col, **DETAIL)
    a.bevel("Belly", (2.4, 0.4, 6.8), (0, y - 1.5, 0.3), glow, b=0.12, bottom=0.12, **GLOW)
    find(a, "Belly")["pulse"] = 1.5
    for i, z in enumerate((-2.8, -2.0, -1.2, -0.4, 0.4, 1.2, 2.0, 2.8, 3.6)):
        a.box(f"BellyPlate{i}", (2.9 - 0.08 * abs(i - 4), 0.35, 0.55), (0, y - 1.66, z), plate_c, **DETAIL)
    # A glowing heart crystal set in the chest.
    a.box("HeartFrame", (1.3, 1.3, 0.3), (0, y + 0.1, -3.42), horn, rot=(0, 0, 45), role="Accent")
    a.box("Heart", (0.9, 0.9, 0.4), (0, y + 0.1, -3.48), glow2, rot=(0, 0, 45), **GLOW)
    find(a, "Heart")["pulse"] = 0.9
    # Dorsal ridge along the back.
    for i, z in enumerate((-2.4, -1.4, -0.4, 0.6, 1.6, 2.6, 3.6)):
        h = 1.4 - 0.1 * abs(i - 2)
        a.wedge(f"BackSpike{i}", (0.45, h, 1.0), (0, y + 1.55 + h / 2, z), dark, rot=(0, 180, 0), role="Accent")
        a.box(f"SpikeGlow{i}", (0.26, 0.26, 0.26), (0, y + 1.6 + h, z + 0.4), glow, **GLOW)

    # ---- neck and head ----
    with a.bone("Head", "Body", (0, y + 1.0, -2.8)):
        neck = [(0, y + 0.7, -2.9), (0, y + 1.8, -3.9), (0, y + 2.8, -4.7), (0, y + 3.5, -5.4)]
        for i in range(3):
            seg(a, f"Neck{i}", neck[i], neck[i + 1], 1.9 - 0.2 * i, body)
            if i > 0:
                knuckle(a, f"NeckJoint{i}", neck[i], neck[i - 1], neck[i + 1], 1.95 - 0.2 * i, body)
            mid = _lerp(neck[i], neck[i + 1], 0.5)
            d = unit(sub(neck[i + 1], neck[i]))
            under = scale((0, d[2], -d[1]), (1.9 - 0.2 * i) / 2 - 0.12)
            seg(a, f"Throat{i}", add(neck[i], under), add(neck[i + 1], under), 0.5, glow, **GLOW)
            a.wedge(f"NeckSpike{i}", (0.35, 0.9, 0.8), add(mid, (0, 1.05 - 0.1 * i, 0.3)), dark, rot=(-35, 180, 0),
                    role="Accent")
        a.oct("Skull", (2.6, 1.9, 2.6), (0, y + 3.7, -5.9), body, b=0.6, bottom=0.4)
        a.box("Brow", (2.9, 0.45, 0.9), (0, y + 4.45, -6.7), dark, rot=(-10, 0, 0), role="Accent")
        a.taper("Snout", (2.0, 1.1), (1.4, 0.8), 2.4, (0, y + 3.55, -8.4), body, r=0.3)
        a.box("SnoutRidge", (0.5, 0.25, 2.2), (0, y + 4.15, -8.2), dark, role="Accent")
        a.wedge("NoseHorn", (0.35, 0.6, 0.7), (0, y + 4.5, -9.1), horn, role="Accent")
        a.box("MouthGlow", (1.5, 0.45, 2.2), (0, y + 2.95, -8.1), glow, **GLOW)
        find(a, "MouthGlow")["pulse"] = 0.8
        a.taper("Jaw", (1.8, 0.45), (1.2, 0.35), 2.4, (0, y + 2.45, -8.0), dark, R=angles(10, 0, 0), r=0.3,
                role="Secondary")
        for i, (x, zz) in enumerate([(0, -8.9), (0.35, -8.6), (-0.35, -8.6)]):
            a.wedge(f"ChinSpike{i}", (0.25, 0.5, 0.5), (x, y + 1.95, zz + 1.4), dark, rot=(180, 0, 0), role="Accent")
        for s, S in SIDES:
            for i, z in enumerate((-7.4, -8.1, -8.8)):
                a.tooth(f"Tooth{i}{S}", (0.62 * s, y + 3.05, z), 0.26, 0.4)
                a.tooth(f"LowTooth{i}{S}", (0.52 * s, y + 2.72, z + 0.1), 0.22, 0.32, up=True)
            a.box(f"Nostril{S}", (0.3, 0.2, 0.2), (0.42 * s, y + 3.8, -9.62), glow, **GLOW)
            a.eye2(f"Eye{S}", (0.95 * s, y + 4.05, -7.12), w=0.85, h=0.6, iris=glow2, pupil=C("#062019"),
                   lid=dark, lid_tilt=22 * s, lid_drop=0.12)
            # Big horns swept back, cheek horns, and fins behind the jaw.
            h0, h1, h2, h3 = (0.8 * s, y + 4.4, -5.9), (1.25 * s, y + 5.2, -4.6), (1.5 * s, y + 5.6, -3.2), \
                (1.45 * s, y + 6.3, -2.1)
            chain(a, f"Horn{S}_", [h0, h1, h2, h3], [0.55, 0.4, 0.26], horn, role="Accent")
            a.box(f"HornTip{S}", (0.32, 0.32, 0.32), h3, glow, rot=(45, 0, 45), **GLOW)
            seg(a, f"CheekHorn{S}", (1.25 * s, y + 3.4, -6.0), (2.1 * s, y + 3.85, -4.7), 0.3, horn, role="Accent")
            seg(a, f"BrowHorn{S}", (0.9 * s, y + 4.6, -6.9), (1.4 * s, y + 5.1, -6.5), 0.22, horn, role="Accent")
            for i, (yy, rz) in enumerate([(y + 3.4, -25), (y + 2.8, -45)]):
                a.wedge(f"Fin{i}{S}", (0.18, 1.2, 1.5), (1.45 * s, yy, -5.2), dark, rot=(0, 180, rz * s), role="Accent")
                a.box(f"FinGlow{i}{S}", (0.2, 0.12, 1.2), (1.6 * s, yy + 0.55, -5.0), glow, rot=(0, 0, rz * s), **GLOW)
        for i, z in enumerate((-5.4, -6.2)):
            a.wedge(f"Crest{i}", (0.3, 0.7, 0.8), (0, y + 4.75 + 0.2 * i, z + 0.5), dark, rot=(0, 180, 0), role="Accent")

    # ---- wings: arm, thumb claw, four fingers with glowing veins, full membranes and a glowing edge ----
    for s, S in SIDES:
        pivot = (1.8 * s, y + 1.3, -1.0)
        with a.bone(f"Wing{S}", "Body", pivot):
            elbow = add(pivot, (3.0 * s, 2.2, 0.6))
            wrist = add(pivot, (6.0 * s, 3.0, 0.2))
            fingers = [add(pivot, (12.5 * s, 1.6, 0.6)), add(pivot, (11.8 * s, 0.2, 3.4)),
                       add(pivot, (9.6 * s, -0.8, 5.8)), add(pivot, (6.4 * s, -1.2, 6.6))]
            root = add(pivot, (0.2 * s, -0.6, 4.4))
            # Raise the whole wing a little (dihedral) so it reads well from the ground.
            Rw = angles(0, 0, 18 * s)
            lift = lambda v: add(pivot, apply(Rw, sub(v, pivot)))
            elbow, wrist, root = lift(elbow), lift(wrist), lift(root)
            fingers = [lift(f) for f in fingers]
            seg(a, f"UpperArm{S}", pivot, elbow, 0.85, body)
            seg(a, f"Forearm{S}", elbow, wrist, 0.65, body)
            knuckle(a, f"Elbow{S}", elbow, pivot, wrist, 0.8, body)
            a.box(f"Knuckle{S}", (0.7, 0.7, 0.7), wrist, dark, rot=(45, 0, 45), role="Accent")
            a.wedge(f"Thumb{S}", (0.3, 0.8, 0.6), add(wrist, (0.1 * s, 0.6, -0.5)), horn, rot=(-30, 0, 0), role="Accent")
            a.wedge(f"ElbowSpike{S}", (0.3, 0.8, 0.7), add(elbow, (0, 0.6, 0.2)), dark, rot=(0, 180, 0), role="Accent")
            for i, f in enumerate(fingers):
                seg(a, f"Finger{i}{S}", wrist, f, 0.36 - 0.04 * i, body, ext=0.8)
                seg(a, f"Vein{i}{S}", add(wrist, (0, -0.2, 0)), add(f, (0, -0.2, 0)), 0.1, glow, **GLOW)
            a.box(f"WingTip{S}", (0.5, 0.5, 0.5), fingers[0], glow, rot=(45, 0, 45), **GLOW)
            find(a, f"WingTip{S}")["pulse"] = 1.2
            # Membranes: the fan between the fingers, then the part between the last finger and the body.
            pts = fingers + [root]
            for i in range(4):
                membrane(a, f"Membrane{i}{S}", wrist, pts[i], pts[i + 1], membrane_c, **DETAIL)
            membrane(a, f"MembraneIn{S}", elbow, wrist, root, inner, strips=2, **DETAIL)
            membrane(a, f"MembraneBase{S}", pivot, elbow, root, inner, strips=2, **DETAIL)
            # Glowing trailing edge.
            for i in range(4):
                seg(a, f"Edge{i}{S}", pts[i], pts[i + 1], 0.12, glow, ext=1.0, **GLOW)

    # ---- tail: six segments with spikes, a glowing underside and a spade blade ----
    with a.bone("Tail", "Body", (0, y, 3.6)):
        pts = [(0, y, 3.6), (0, y - 0.3, 5.8), (0, y - 1.0, 7.8), (0.3, y - 1.9, 9.6), (0.8, y - 2.9, 11.1),
               (1.4, y - 3.8, 12.3), (1.9, y - 4.4, 13.2)]
        for i in range(6):
            t = 1.6 - 0.22 * i
            seg(a, f"Tail{i}", pts[i], pts[i + 1], t, body)
            if i > 0:
                knuckle(a, f"TailJoint{i}", pts[i], pts[i - 1], pts[i + 1], t + 0.12, body)
            mid = _lerp(pts[i], pts[i + 1], 0.5)
            seg(a, f"TailGlow{i}", add(pts[i], (0, -t / 2, 0)), add(pts[i + 1], (0, -t / 2 + 0.1, 0)), 0.22, glow,
                   **GLOW)
            a.wedge(f"TailSpike{i}", (0.3, 0.8 - 0.08 * i, 0.9), add(mid, (0, t / 2 + 0.3, 0)), dark, rot=(0, 180, 0),
                    role="Accent")
        a.shard("TailBlade", (2.0, y - 4.6, 13.4), 1.3, 2.4, glow, R=angles(-120, 0, 25), cross=True, **GLOW)
        find(a, "TailBlade")["pulse"] = 1.2
        for s, S in SIDES:
            a.wedge(f"BladeFin{S}", (0.15, 1.4, 1.2), (1.9 + 0.6 * s, y - 4.3, 13.1), dark, rot=(0, 180, 30 * s),
                    role="Accent")

    # ---- legs ----
    for s, S in SIDES:
        with a.bone(f"LegB{S}", "Body", (1.5 * s, y - 0.6, 2.6)):
            a.oct(f"Thigh{S}", (1.4, 2.2, 2.2), (1.75 * s, y - 1.1, 2.7), body, b=0.4)
            seg(a, f"Shin{S}", (1.75 * s, y - 2.0, 3.1), (1.75 * s, y - 3.4, 2.3), 0.8, dark)
            a.box(f"Foot{S}", (1.0, 0.4, 1.4), (1.75 * s, y - 3.65, 1.9), dark)
            for j, dx in enumerate((-0.35, 0, 0.35)):
                a.wedge(f"Talon{j}{S}", (0.22, 0.35, 0.6), (1.75 * s + dx, y - 3.72, 1.1), horn, rot=(0, 0, 0),
                        role="Accent")
            a.wedge(f"Spur{S}", (0.2, 0.3, 0.5), (1.75 * s, y - 3.5, 2.75), horn, rot=(0, 180, 0), role="Accent")
        # Front legs built the same way as the hind legs, so it stands on four strong legs.
        with a.bone(f"LegF{S}", "Body", (1.5 * s, y - 0.6, -2.2)):
            a.oct(f"FrontThigh{S}", (1.4, 2.2, 2.2), (1.75 * s, y - 1.1, -2.1), body, b=0.4)
            seg(a, f"FrontShin{S}", (1.75 * s, y - 2.0, -1.7), (1.75 * s, y - 3.4, -2.5), 0.8, dark)
            a.box(f"FrontFoot{S}", (1.0, 0.4, 1.4), (1.75 * s, y - 3.65, -2.9), dark)
            for j, dx in enumerate((-0.35, 0, 0.35)):
                a.wedge(f"FrontTalon{j}{S}", (0.22, 0.35, 0.6), (1.75 * s + dx, y - 3.72, -3.7), horn, role="Accent")
            a.wedge(f"FrontSpur{S}", (0.2, 0.3, 0.5), (1.75 * s, y - 3.5, -2.05), horn, rot=(0, 180, 0), role="Accent")

    # ---- soul flames that circle around it ----
    with a.bone("Orbit", "Body", (0, y, 0.4)):
        for i in range(3):
            ang = i * 2 * math.pi / 3
            pos = (math.cos(ang) * 7.0, y + 0.8 + math.sin(ang * 2) * 1.2, 0.4 + math.sin(ang) * 7.0)
            a.box(f"SoulFlame{i}", (0.6, 0.6, 0.6), pos, glow2, rot=(45, 45, 0), **GLOW)

    scale_animal(a, 1.3)

    # ---- effects ----
    fx(a, "Body",
       emitter("ShadowWisps", C("#0f2626"), rate=7, lifetime=(1.4, 2.2), speed=(0.3, 0.8), sizes=((0, 1.6), (1, 3.6)),
               transparency=((0, 0.45), (1, 1)), light=0, accel=(0, 0.8, 0), drag=1, color2=C("#060d0d")),
       light("DrakeGlow", glow, brightness=1.8, range_=18, pulse=1.5))
    fx(a, "Heart", light("HeartLight", glow2, brightness=1.2, range_=10, pulse=0.9))
    fx(a, "MouthGlow", emitter("GhostFire", glow2, texture=FIRE_TEXTURE, rate=14, lifetime=(0.35, 0.6), speed=(2, 3.5),
                               spread=15, sizes=((0, 0.5), (0.4, 1.1), (1, 0)), transparency=((0, 0.1), (1, 1)),
                               color2=C("#1f8a6a"), emit="Front"))
    for i in range(3):
        fx(a, f"SoulFlame{i}", emitter("SoulFire", glow, texture=FIRE_TEXTURE, rate=12, lifetime=(0.3, 0.5),
                                       speed=(0.8, 1.5), spread=15, sizes=((0, 0.8), (1, 0)),
                                       transparency=((0, 0.1), (1, 1)), color2=C("#1f8a6a"), accel=(0, 2, 0)))
        trail(a, f"SoulFlame{i}", *near(a, f"SoulFlame{i}", 0.3), glow, name=f"SoulTrail{i}", lifetime=0.9,
              color2=C("#1f8a6a"))
    for s, S in SIDES:
        trail(a, f"WingTip{S}", *near(a, f"WingTip{S}", 0.4), glow, name=f"WingTrail{S}", lifetime=0.8,
              color2=C("#123030"))
    trail(a, "TailBlade", *near(a, "TailBlade", 0.5), glow, name="TailTrail", lifetime=0.7, color2=C("#123030"))
    fx(a, "TailBlade", light("TailLight", glow, brightness=1.0, range_=8, pulse=1.2))
    # Crackling energy arc between the two horn tips.
    hr, hl = find(a, "HornTipR")["p"], find(a, "HornTipL")["p"]
    beam(a, "HornTipR", hr, "HornTipL", hl, glow2, name="HornArc", width=(0.35, 0.35), curve=(1.8, -1.8),
         transparency=((0, 0.1), (0.5, 0), (1, 0.1)), segments=20, R0=angles(0, 0, 90), R1=angles(0, 0, 90),
         texture=SPARKLE_TEXTURE, texture_speed=3, color2=glow)

    a.ride_height, a.ride_z = (y + 2.2) * 1.3, 0.4 * 1.3
    extras(a, attrs={"FlapSpeed": 3.2, "FlapAngle": 22, "Hover": 1.0, "HoverSpeed": 1.3, "OrbitSpeed": 1.2,
                     "TailSway": 12},
           highlight=(glow, glow, 0.9, 0.15))
    return a


ALL = [mossback_toad, shroom_snail, duskbat, night_hedgehog, glowmoth, hollow_badger, barkling, wisp_lynx, moonraven,
       umbra_panther, mossking_elk, nightshade_drake]
