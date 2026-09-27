"""The Hunt an Animal cast, in a blocky studded style. Each animal faces -Z."""

from lib import (
    EYE, SIDES, WHITE, Animal, add, angles, apply, hex_color as C,
)

MOUTH = C("#c92a3a")
TONGUE = C("#ff7d92")
PINK = C("#ffb0c4")
DETAIL = dict(material="SmoothPlastic", role="Accent", shadow=False)


def at(base, R, offset):
    return add(base, apply(R, offset))


# ------------------------------------------------------------ Common ----

def rabbit():
    a = Animal("Rabbit", "Rabbit", "Common")
    fur, cream = C("#c98d5c"), C("#fff3e3")

    a.bevel("Body", (3.6, 3.0, 4.4), (0, 2.6, 0.8), fur, b=0.8)
    a.box("Belly", (2.4, 1.9, 0.2), (0, 2.35, -1.45), cream, role="Secondary")

    with a.bone("Head", "Body", (0, 3.8, -0.6)):
        a.bevel("Head", (4.0, 3.4, 3.4), (0, 5.0, -1.0), fur, b=0.9)
        a.box("Muzzle", (2.0, 1.1, 0.4), (0, 4.0, -2.8), cream, role="Secondary")
        a.box("Nose", (0.7, 0.45, 0.2), (0, 4.5, -3.05), C("#ff7fa6"), **DETAIL)
        for s, S in SIDES:
            a.box(f"Tooth{S}", (0.36, 0.5, 0.14), (0.2 * s, 3.25, -2.9), WHITE, **DETAIL)
            a.block_eye(f"Eye{S}", (1.05 * s, 5.3, -2.76), w=0.95, h=1.25)
            a.box(f"Cheek{S}", (0.7, 0.4, 0.1), (1.5 * s, 4.35, -2.74), PINK, **DETAIL)
            R = angles(0, 0, -10 * s)
            ear_c = (1.0 * s, 8.25, -0.9)
            a.bevel(f"Ear{S}", (1.0, 3.4, 0.7), ear_c, fur, b=0.35, R=R)
            a.box(f"InnerEar{S}", (0.55, 2.5, 0.1), at(ear_c, R, (0, -0.2, -0.36)), PINK, R=R, **DETAIL)

    for s, S in SIDES:
        with a.bone(f"LegF{S}", "Body", (0.95 * s, 1.3, -1.0)):
            a.box(f"PawF{S}", (1.0, 1.3, 1.1), (0.95 * s, 0.65, -1.0), cream, role="Secondary")
        with a.bone(f"LegB{S}", "Body", (1.6 * s, 2.2, 1.6)):
            a.bevel(f"Haunch{S}", (1.2, 2.0, 2.4), (1.6 * s, 1.6, 1.6), fur, b=0.4)
            a.box(f"FootB{S}", (1.2, 0.6, 2.4), (1.55 * s, 0.3, 1.0), cream, role="Secondary")

    with a.bone("Tail", "Body", (0, 2.8, 3.0)):
        a.bevel("Tail", (1.4, 1.4, 1.0), (0, 2.8, 3.45), WHITE, b=0.35, bottom=0.35, role="Secondary")

    a.ride_height, a.ride_z = 4.1, 0.9
    return a


# -------------------------------------------------------------- Rare ----

def wolf():
    a = Animal("Wolf", "Wolf", "Rare")
    fur, dark, white = C("#a3abbd"), C("#646c80"), C("#f4f6fb")

    a.bevel("Body", (4.2, 3.6, 7.2), (0, 4.6, 0.6), fur, b=1.0)
    a.box("Belly", (4.3, 1.0, 6.4), (0, 3.3, 0.8), white, role="Secondary")
    a.bevel("Saddle", (4.3, 1.7, 4.6), (0, 5.62, 1.3), dark, b=1.05, role="Secondary")
    a.bevel("Chest", (3.8, 3.0, 1.4), (0, 4.4, -3.1), white, b=0.6, bottom=0.6, role="Secondary")

    with a.bone("Head", "Body", (0, 6.0, -2.6)):
        a.box("Neck", (3.0, 2.4, 2.2), (0, 6.0, -2.7), fur)
        a.bevel("Head", (4.4, 3.6, 3.8), (0, 7.4, -3.8), fur, b=1.0)
        a.bevel("Snout", (2.6, 1.7, 2.4), (0, 6.55, -6.7), fur, b=0.5)
        a.box("Jaw", (2.7, 0.6, 2.2), (0, 5.95, -6.65), white, role="Secondary")
        a.box("Nose", (1.1, 0.6, 0.5), (0, 7.1, -7.95), EYE, **DETAIL)
        a.box("Mouth", (1.9, 0.36, 0.14), (0, 6.3, -7.93), MOUTH, **DETAIL)
        for s, S in SIDES:
            a.tooth(f"Fang{S}", (0.6 * s, 6.3, -7.99), 0.45, 0.55, R=angles(0, 90, 0))
            a.block_eye(f"Eye{S}", (1.1 * s, 7.8, -5.76), w=1.0, h=1.2)
            a.box(f"Brow{S}", (1.25, 0.3, 0.2), (1.1 * s, 8.65, -5.78), dark, rot=(0, 0, 16 * s), **DETAIL)
            a.box(f"CheekFluff{S}", (0.6, 1.4, 1.8), (2.3 * s, 6.5, -3.6), white, role="Secondary")
            R = angles(0, 0, -12 * s)
            base = (1.3 * s, 9.1, -3.4)
            a.tri(f"Ear{S}", base, 1.6, 2.0, 0.7, fur, R=R)
            a.tri(f"InnerEar{S}", at(base, R, (0, 0.12, -0.37)), 0.95, 1.3, 0.1, PINK, R=R, **DETAIL)

    for s, S in SIDES:
        for z, F in ((-2.0, "F"), (3.2, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (1.35 * s, 3.2, z)):
                a.box(f"Leg{F}{S}", (1.3, 3.0, 1.3), (1.35 * s, 1.9, z), fur)
                a.box(f"Paw{F}{S}", (1.5, 0.7, 1.9), (1.35 * s, 0.35, z - 0.25), white, role="Secondary")

    with a.bone("Tail", "Body", (0, 5.6, 4.1)):
        R = angles(-35, 0, 0)
        base = (0, 5.6, 4.1)
        a.bevel("Tail", (1.5, 1.5, 3.6), at(base, R, (0, 0, 1.9)), fur, b=0.45, bottom=0.45, R=R)
        a.bevel("TailTip", (1.56, 1.56, 1.2), at(base, R, (0, 0, 3.9)), white, b=0.47, bottom=0.47, R=R,
                role="Secondary")

    a.ride_height, a.ride_z = 6.4, 0.8
    return a


# --------------------------------------------------------- Legendary ----

def sandsnapper():
    a = Animal("Sandsnapper", "Sandsnapper", "Legendary")
    sand, stripe, belly = C("#f0c266"), C("#d38b34"), C("#fff4d8")

    a.bevel("Body", (6.4, 4.6, 8.0), (0, 3.2, 0.2), sand, b=1.4)
    a.box("Belly", (6.5, 1.4, 7.6), (0, 1.6, 0.2), belly, role="Secondary")
    for i, z in enumerate((-1.4, 1.8)):
        a.bevel(f"Stripe{i}", (6.52, 3.26, 1.1), (0, 3.93, z), stripe, b=1.43, role="Secondary")
    for i, z in enumerate((-2.6, -0.2, 2.2)):
        a.wedge(f"BackSpike{i}", (0.6, 1.2, 1.6), (0, 6.1, z), WHITE, role="Accent")

    with a.bone("Head", "Body", (0, 3.8, -3.6)):
        a.bevel("Head", (6.0, 3.8, 4.4), (0, 3.9, -5.8), sand, b=1.2)
        a.bevel("Snout", (5.4, 1.7, 5.6), (0, 4.35, -10.6), sand, b=0.7)
        a.box("SnoutStripe", (5.46, 1.0, 0.9), (0, 4.5, -8.9), stripe, role="Secondary")
        a.box("MouthInside", (5.0, 1.5, 5.4), (0, 2.85, -10.4), MOUTH, material="SmoothPlastic", role="Accent")
        a.box("Tongue", (2.4, 0.25, 3.4), (0, 2.25, -10.0), TONGUE, **DETAIL)
        a.box("Jaw", (5.2, 1.1, 5.4), (0, 1.6, -10.4), sand)
        a.box("JawBelly", (5.1, 0.3, 5.1), (0, 1.02, -10.3), belly, role="Secondary")
        for s, S in SIDES:
            a.box(f"Nostril{S}", (0.6, 0.2, 0.6), (0.9 * s, 5.22, -12.6), C("#6a4420"), **DETAIL)
            for i, z in enumerate((-8.6, -9.8, -11.0, -12.2)):
                a.tooth(f"Tooth{i}{S}", (2.45 * s, 3.52, z), 0.85, 0.7)
            for i, z in enumerate((-9.2, -10.4, -11.6)):
                a.tooth(f"LowTooth{i}{S}", (2.35 * s, 2.13, z), 0.8, 0.6, up=True)
            a.tooth(f"FrontTooth{S}", (0.9 * s, 3.52, -13.35), 0.7, 0.65, R=angles(0, 90, 0))
            a.tooth(f"LowFrontTooth{S}", (0.9 * s, 2.13, -13.05), 0.65, 0.55, R=angles(0, 90, 0), up=True)
            a.bevel(f"EyeBump{S}", (2.1, 1.9, 2.0), (1.9 * s, 6.25, -6.4), sand, b=0.5)
            a.block_eye(f"Eye{S}", (1.9 * s, 6.2, -7.46), w=1.5, h=1.45, look=(-0.6 * s, 0))
            a.box(f"Brow{S}", (1.8, 0.42, 0.3), (1.9 * s, 7.15, -7.45), stripe, rot=(0, 0, 14 * s), **DETAIL)
            a.wedge(f"Horn{S}", (0.55, 1.4, 1.8), (1.9 * s, 7.85, -5.9), stripe, role="Secondary")

    for s, S in SIDES:
        for z, F in ((-2.4, "F"), (2.6, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (3.0 * s, 2.4, z)):
                a.box(f"Leg{F}{S}", (1.8, 1.8, 2.0), (3.5 * s, 1.5, z), sand)
                a.box(f"Foot{F}{S}", (2.4, 0.7, 2.8), (3.8 * s, 0.35, z - 0.3), sand)
                for i, dx in enumerate((-0.6, 0.6)):
                    a.wedge(f"Claw{i}{F}{S}", (0.55, 0.5, 0.8), (3.8 * s + dx, 0.25, z - 2.1), WHITE, **DETAIL)

    with a.bone("Tail", "Body", (0, 3.0, 4.2)):
        a.bevel("Tail", (5.0, 3.6, 4.2), (0, 2.9, 6.1), sand, b=1.1)
        a.bevel("TailStripe", (5.12, 3.66, 0.9), (0, 2.93, 6.6), stripe, b=1.13, role="Secondary")
        a.bevel("TailMid", (3.4, 2.6, 4.0), (0, 2.35, 10.0), sand, b=0.8)
        a.box("TailEnd", (2.2, 1.7, 3.4), (0, 1.95, 13.6), sand)
        a.wedge("TailTip", (2.1, 1.6, 2.4), (0, 1.9, 16.5), sand, rot=(0, 180, 0))
        for i, (y, z) in enumerate(((5.2, 5.8), (4.1, 9.8))):
            a.wedge(f"TailSpike{i}", (0.5, 0.9, 1.2), (0, y, z), WHITE, role="Accent")

    a.ride_height, a.ride_z = 5.5, 0.2
    return a


ALL = [rabbit, wolf, sandsnapper]
