"""The Hunt an Animal cast, in a blocky studded style. Each animal faces -Z.

Animals that share a body plan (canines, deer, boars, bears, bunnies) are built
from one template each, so every model keeps the same joints and proportions.
"""

from lib import (
    EYE, FIRE_TEXTURE, SIDES, SMOKE_TEXTURE, WHITE, Animal, add, angles, apply, hex_color as C, matmul,
)

MOUTH = C("#c92a3a")
TONGUE = C("#ff7d92")
PINK = C("#ffb0c4")
DETAIL = dict(material="SmoothPlastic", role="Accent", shadow=False)
NEON = dict(material="Neon", role="Glow", shadow=False)
GLASS = dict(material="Glass", transparency=0.2, reflectance=0.15, role="Glow")


def at(base, R, offset):
    return add(base, apply(R, offset))


def find(a, name):
    return next(p for p in a.parts if p["name"] == name)


def fx(a, name, *effects):
    find(a, name)["effects"].extend(effects)


# ---------------------------------------------------------- templates ----

def _bunny(a, fur, cream, inner=PINK, nose=C("#ff7fa6"), eye=None, ears=True, head_extra=None,
           tail=WHITE, tail_kw=None, ear_tip=None):
    a.oct("Body", (3.6, 3.0, 4.4), (0, 2.6, 0.8), fur, b=0.9, bottom=0.6)
    a.bevel("BellyLow", (3.66, 1.2, 3.8), (0, 1.7, 0.8), cream, b=0, bottom=0.63, role="Secondary")
    a.oct("Belly", (2.4, 1.9, 0.3), (0, 2.35, -1.45), cream, b=0.3, role="Secondary")
    a.tri("ChestTuft", (0, 1.55, -1.6), 1.1, 0.8, 0.4, cream, R=angles(0, 0, 180), role="Secondary")

    with a.bone("Head", "Body", (0, 3.8, -0.6)):
        a.oct("Head", (4.0, 3.4, 3.4), (0, 5.0, -1.0), fur, b=1.0, bottom=0.6)
        a.oct("Muzzle", (2.2, 1.3, 0.8), (0, 4.05, -2.75), cream, b=0.4, role="Secondary")
        a.bevel("Nose", (0.75, 0.5, 0.35), (0, 4.6, -3.18), nose, b=0.15, **DETAIL)
        a.box("NoseShine", (0.22, 0.12, 0.08), (-0.15, 4.72, -3.38), WHITE, **DETAIL)
        a.tri("Forelock", (0.35, 6.55, -2.3), 1.0, 0.8, 0.5, fur, R=angles(-20, 0, -20))
        for s, S in SIDES:
            a.box(f"Mouth{S}", (0.42, 0.1, 0.08), (0.18 * s, 4.1, -3.17), C("#5a2a3a"), rot=(0, 0, -30 * s),
                  **DETAIL)
            a.box(f"Tooth{S}", (0.34, 0.45, 0.14), (0.19 * s, 3.25, -3.0), WHITE, **DETAIL)
            a.eye2(f"Eye{S}", (1.05 * s, 5.35, -2.76), w=1.0, h=1.3, **({"iris": C("#6b4226")} | (eye or {})))
            a.box(f"Cheek{S}", (0.7, 0.4, 0.1), (1.55 * s, 4.35, -2.74), PINK, **DETAIL)
            a.tuft(f"CheekTuft{S}", (2.15 * s, 4.4, -1.3), (0.5, 1.0, 1.4), fur, R=angles(0, 25 * s, 0))
            if ears:
                tilt = angles(0, 0, -10 * s)
                ear_c = (1.0 * s, 8.3, -0.9)
                a.taper(f"Ear{S}", (1.15, 0.75), (0.85, 0.6), 3.8, ear_c, fur, R=matmul(tilt, angles(90, 0, 0)), r=0.45)
                a.box(f"InnerEar{S}", (0.55, 2.6, 0.1), at(ear_c, tilt, (0, -0.1, -0.33)), inner, R=tilt, **DETAIL)
                if ear_tip:
                    a.taper(f"EarTip{S}", (0.92, 0.64), (0.84, 0.58), 0.8, at(ear_c, tilt, (0, 1.55, 0)), ear_tip,
                            R=matmul(tilt, angles(90, 0, 0)), r=0.45, role="Accent")
        if head_extra:
            head_extra(a)

    for s, S in SIDES:
        with a.bone(f"LegF{S}", "Body", (0.95 * s, 1.6, -1.0)):
            a.post(f"LegF{S}", (1.0, 1.1, 1.0), (0.95 * s, 1.25, -1.0), fur, b=0.3)
            a.paw(f"PawF{S}", (0.95 * s, 0, -1.1), 1.1, 1.3, cream, h=0.85)
        with a.bone(f"LegB{S}", "Body", (1.6 * s, 2.2, 1.6)):
            a.oct(f"Haunch{S}", (1.3, 2.1, 2.5), (1.6 * s, 1.7, 1.6), fur, b=0.55)
            a.paw(f"FootB{S}", (1.55 * s, 0, 1.0), 1.25, 2.6, cream, h=0.6)

    if tail:
        with a.bone("Tail", "Body", (0, 2.8, 3.0)):
            a.oct("Tail", (1.5, 1.4, 1.1), (0, 2.8, 3.45), tail, b=0.5, **(tail_kw or dict(role="Secondary")))
            a.tri("TailTuft", (0, 3.3, 3.9), 0.8, 0.6, 0.5, tail, R=angles(-60, 0, 0),
                  **(tail_kw or dict(role="Secondary")))

    a.ride_height, a.ride_z = 4.1, 0.9

def _canine(a, fur, light, dark=None, inner=PINK, eye=None, snout="wolf", ear=(1.6, 2.0), brows=True,
            fangs=True, paws=None, head_extra=None, tail=None, brow_color=None, mask=True):
    """Wolf-shaped body. snout: 'wolf', 'fox' or 'cat'."""
    paws = paws or light
    eye = {"iris": C("#ffb52e")} | (eye or {})
    a.oct("Body", (4.2, 3.6, 7.2), (0, 4.6, 0.6), fur, b=1.0, bottom=0.7)
    a.bevel("Belly", (4.26, 1.4, 6.4), (0, 3.5, 0.7), light, b=0, bottom=0.73, role="Secondary")
    if dark:
        a.bevel("Saddle", (4.26, 1.8, 4.8), (0, 5.53, 1.3), dark, b=1.03, role="Secondary")
    a.oct("Chest", (3.8, 3.0, 1.4), (0, 4.4, -3.1), light, b=0.6, role="Secondary")
    for i, x in enumerate((-1.0, 0, 1.0)):
        a.tri(f"ChestTuft{i}", (x, 2.95, -3.4), 1.2, 1.0 - 0.2 * abs(x), 0.7, light, R=angles(0, 0, 180),
              role="Secondary")

    with a.bone("Head", "Body", (0, 6.0, -2.6)):
        a.post("Neck", (3.0, 2.4, 2.2), (0, 6.0, -2.7), fur, b=0.5)
        a.oct("Head", (4.4, 3.6, 3.8), (0, 7.4, -3.8), fur, b=1.0, bottom=0.6)
        if mask:
            a.bevel("FaceMask", (4.46, 1.5, 3.4), (0, 6.33, -3.85), light, b=0, bottom=0.63, role="Secondary")
        if snout == "wolf":
            a.taper("Snout", (2.6, 1.75), (2.2, 1.45), 2.4, (0, 6.6, -6.7), fur, r=0.3)
            a.taper("Jaw", (2.66, 0.85), (2.26, 0.75), 2.44, (0, 6.1, -6.7), light, r=0.3, role="Secondary")
            a.bevel("Nose", (1.1, 0.6, 0.5), (0, 7.1, -7.95), EYE, b=0.18, **DETAIL)
            a.box("NoseShine", (0.3, 0.15, 0.1), (-0.22, 7.3, -8.2), WHITE, **DETAIL)
            mouth_y, front = 6.2, -7.93
        elif snout == "fox":
            a.taper("Snout", (2.2, 1.5), (1.6, 1.1), 2.8, (0, 6.5, -6.9), fur, r=0.3)
            a.taper("Jaw", (2.26, 0.75), (1.66, 0.6), 2.84, (0, 6.1, -6.9), light, r=0.3, role="Secondary")
            a.bevel("Nose", (0.9, 0.55, 0.45), (0, 6.95, -8.3), EYE, b=0.16, **DETAIL)
            a.box("NoseShine", (0.25, 0.12, 0.1), (-0.18, 7.12, -8.54), WHITE, **DETAIL)
            mouth_y, front = 6.2, -8.3
        else:
            a.oct("Snout", (2.4, 1.3, 1.0), (0, 6.4, -6.1), light, b=0.45, role="Secondary")
            a.bevel("Nose", (0.6, 0.4, 0.2), (0, 6.85, -6.66), PINK, b=0.12, **DETAIL)
            mouth_y, front = 6.15, -6.62
        if fangs:
            a.box("Mouth", (1.7, 0.45, 0.25), (0, mouth_y - 0.1, front + 0.02), MOUTH, **DETAIL)
            a.box("Tongue", (0.8, 0.18, 0.6), (0.25, mouth_y - 0.32, front - 0.05), TONGUE, **DETAIL)
        for s, S in SIDES:
            if fangs:
                a.tri(f"Fang{S}", (0.55 * s, mouth_y + 0.07, front - 0.12), 0.36, 0.5, 0.12, WHITE,
                      R=angles(0, 0, 180), **DETAIL)
            else:
                a.box(f"Smile{S}", (0.45, 0.12, 0.08), (0.2 * s, mouth_y, front - 0.03), C("#5a2a3a"),
                      rot=(0, 0, 25 * s), **DETAIL)
            a.eye2(f"Eye{S}", (1.1 * s, 7.8, -5.76), w=1.05, h=1.25, lid=(brow_color or dark or fur) if brows else None,
                   lid_tilt=14 * s, lid_drop=0.08, **eye)
            if not brows:
                a.box(f"Cheek{S}", (0.7, 0.35, 0.1), (1.6 * s, 6.75, -5.74), PINK, **DETAIL)
            for i, y in enumerate((6.9, 6.1)):
                a.tuft(f"CheekTuft{i}{S}", (2.3 * s, y, -3.6), (0.55, 1.1, 1.6), light, R=angles(0, 25 * s, 0),
                       role="Secondary")
            R = angles(-6, 0, -12 * s)
            base = (1.3 * s, 9.1, -3.4)
            a.tri(f"Ear{S}", base, ear[0], ear[1], 0.7, fur, R=R)
            a.tri(f"InnerEar{S}", at(base, R, (0, 0.12, -0.37)), ear[0] * 0.6, ear[1] * 0.65, 0.1, inner, R=R,
                  **DETAIL)
            a.tri(f"EarTuft{S}", at(base, R, (0, 0.05, -0.44)), ear[0] * 0.34, ear[1] * 0.32, 0.1, WHITE, R=R,
                  **DETAIL)
        if head_extra:
            head_extra(a)

    for s, S in SIDES:
        with a.bone(f"LegF{S}", "Body", (1.35 * s, 3.9, -2.0)):
            a.post(f"LegF{S}", (1.4, 1.9, 1.4), (1.35 * s, 3.35, -2.0), fur, b=0.35)
            a.post(f"LowerLegF{S}", (1.2, 2.0, 1.25), (1.35 * s, 1.55, -2.05), paws, b=0.3, role="Secondary")
            a.paw(f"PawF{S}", (1.35 * s, 0, -2.3), 1.55, 1.9, paws, claws=C("#3a3a44"), h=0.75)
        with a.bone(f"LegB{S}", "Body", (1.4 * s, 4.2, 3.2)):
            a.oct(f"Thigh{S}", (1.7, 2.6, 2.3), (1.4 * s, 3.8, 3.2), fur, b=0.5)
            a.post(f"LowerLegB{S}", (1.2, 2.3, 1.25), (1.35 * s, 1.6, 3.4), paws, b=0.3, role="Secondary")
            a.paw(f"PawB{S}", (1.35 * s, 0, 3.15), 1.55, 1.9, paws, claws=C("#3a3a44"), h=0.75)

    if tail:
        tail(a)
    else:
        with a.bone("Tail", "Body", (0, 5.6, 4.1)):
            R = angles(-35, 0, 0)
            base = (0, 5.6, 4.1)
            a.taper("Tail", (1.9, 1.9), (1.3, 1.3), 2.6, at(base, R, (0, 0, 1.4)), fur, R=R, r=0.35)
            a.taper("TailTip", (1.1, 1.1), (1.9, 1.9), 1.8, at(base, R, (0, 0, 3.5)), light, R=R, r=0.35,
                    role="Secondary")

    a.ride_height, a.ride_z = 6.4, 0.8

def _deer(a, fur, light, hoof, hoof_mat=None, antlers=None, spots=None, spot_kw=None, inner=PINK,
          tail=WHITE, tail_kw=None, head_extra=None, iris=C("#6b4226")):
    a.oct("Body", (3.6, 3.2, 6.4), (0, 5.6, 0.4), fur, b=0.9, bottom=0.6)
    a.bevel("Belly", (3.66, 1.2, 5.8), (0, 4.55, 0.45), light, b=0, bottom=0.63, role="Secondary")
    a.oct("Chest", (3.0, 2.2, 0.4), (0, 5.2, -2.8), light, b=0.3, role="Secondary")
    if spots:
        kw = spot_kw or dict(role="Accent", material="SmoothPlastic", shadow=False)
        for s, S in SIDES:
            for i, (y, z) in enumerate([(6.3, -1.0 + 0.3 * s), (5.6, 0.5), (6.4, 1.6 - 0.3 * s), (5.7, 2.7)]):
                a.box(f"Spot{i}{S}", (0.14, 0.55, 0.7), (1.83 * s, y, z), spots, **kw)
        for i, (x, z) in enumerate([(0.5, -1.7), (-0.6, -0.3), (0.4, 1.1), (-0.4, 2.5)]):
            a.box(f"TopSpot{i}", (0.7, 0.14, 0.55), (x, 7.23, z), spots, **kw)

    with a.bone("Head", "Body", (0, 6.8, -2.2)):
        neck_R = matmul(angles(-12, 0, 0), angles(90, 0, 0))
        a.taper("Neck", (1.9, 2.0), (1.55, 1.65), 3.6, (0, 7.9, -2.5), fur, R=neck_R, r=0.35)
        a.box("Throat", (1.1, 2.2, 0.3), (0, 7.5, -3.3), light, rot=(-12, 0, 0), role="Secondary")
        a.oct("Head", (3.2, 2.8, 3.0), (0, 9.9, -3.2), fur, b=0.8, bottom=0.5)
        a.taper("Snout", (1.9, 1.4), (1.6, 1.15), 1.6, (0, 9.3, -5.3), fur, r=0.3)
        a.taper("Jaw", (1.96, 0.6), (1.66, 0.5), 1.64, (0, 8.8, -5.3), light, r=0.3, role="Secondary")
        a.bevel("Nose", (0.9, 0.5, 0.3), (0, 9.7, -6.1), C("#3a2a2a"), b=0.15, **DETAIL)
        a.box("NoseShine", (0.25, 0.12, 0.08), (-0.18, 9.85, -6.28), WHITE, **DETAIL)
        a.box("Smile", (0.5, 0.1, 0.08), (0, 9.0, -6.08), C("#5a2a3a"), **DETAIL)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (0.8 * s, 10.2, -4.76), w=0.9, h=1.1, iris=iris)
            a.tri(f"Lash{S}", (1.28 * s, 10.7, -4.78), 0.3, 0.38, 0.08, EYE, R=angles(0, 0, -40 * s), **DETAIL)
            a.box(f"Cheek{S}", (0.55, 0.3, 0.1), (1.25 * s, 9.35, -4.74), PINK, **DETAIL)
            ear_R = matmul(angles(0, 0, 20 * s), angles(0, -90 * s, 0))
            a.taper(f"Ear{S}", (0.55, 0.8), (0.35, 0.45), 1.9, (2.2 * s, 10.9, -2.9), fur, R=ear_R, r=0.45)
            a.box(f"InnerEar{S}", (1.1, 0.4, 0.1), (2.2 * s, 10.9, -3.2), inner, rot=(0, 0, 20 * s), **DETAIL)
        if antlers:
            antlers(a)
        if head_extra:
            head_extra(a)

    for s, S in SIDES:
        for z, F in ((-1.8, "F"), (2.6, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (1.1 * s, 4.4, z)):
                a.taper(f"Leg{F}{S}", (1.15, 1.2), (0.85, 0.9), 2.2, (1.1 * s, 3.3, z), fur, R=angles(-90, 0, 0),
                        r=0.3)
                a.post(f"LowerLeg{F}{S}", (0.8, 2.2, 0.85), (1.1 * s, 1.4, z), fur, b=0.25)
                a.box(f"Fetlock{F}{S}", (0.92, 0.3, 0.97), (1.1 * s, 0.78, z), light, role="Secondary")
                a.bevel(f"Hoof{F}{S}", (1.05, 0.62, 1.1), (1.1 * s, 0.31, z), hoof, b=0.2,
                        **({"material": hoof_mat, "role": "Glow"} if hoof_mat else {"role": "Accent"}))
                a.box(f"HoofSplit{F}{S}", (0.1, 0.45, 0.12), (1.1 * s, 0.3, z - 0.56), EYE, **DETAIL)

    with a.bone("Tail", "Body", (0, 6.8, 3.6)):
        if callable(tail):
            tail(a)
        else:
            a.taper("Tail", (0.7, 0.55), (1.0, 0.8), 1.4, (0, 6.9, 3.95), tail, R=angles(-65, 0, 0), r=0.4,
                    **(tail_kw or {"role": "Secondary"}))

    a.ride_height, a.ride_z = 7.2, 0.6

def _boar(a, fur, belly, snout, dark, tusk, tusk_kw=None, eye=None, mohawk=None, mohawk_kw=None, inner=PINK):
    a.oct("Body", (5.0, 4.2, 7.0), (0, 3.9, 0.5), fur, b=1.2, bottom=0.8)
    a.bevel("Belly", (5.06, 1.4, 6.2), (0, 2.5, 0.6), belly, b=0, bottom=0.83, role="Secondary")
    mohawk = mohawk or [dark]
    for i, (z, h) in enumerate([(-2.4, 1.3), (-1.2, 1.5), (0.0, 1.4), (1.2, 1.2), (2.4, 0.9)]):
        a.wedge(f"Mohawk{i}", (0.7, h, 1.4), (0, 6.0 + h / 2, z), mohawk[i % len(mohawk)],
                **(mohawk_kw or {"role": "Accent"}))

    with a.bone("Head", "Body", (0, 4.2, -2.6)):
        a.oct("Head", (5.0, 4.0, 3.6), (0, 4.4, -4.2), fur, b=1.1, bottom=0.7)
        a.taper("Snout", (3.0, 2.1), (2.8, 1.9), 1.4, (0, 3.7, -6.5), snout, r=0.3, role="Secondary")
        a.box("Mouth", (2.6, 0.3, 0.14), (0, 2.75, -6.03), MOUTH, **DETAIL)
        for s, S in SIDES:
            a.oct(f"Nostril{S}", (0.5, 0.7, 0.15), (0.6 * s, 3.7, -7.22), dark, b=0.15, **DETAIL)
            a.tooth(f"Tusk{S}", (1.5 * s, 2.75, -6.1), 0.55, 1.1, color=tusk, R=angles(0, 90, 0), up=True,
                    **(tusk_kw or {}))
            a.eye2(f"Eye{S}", (1.35 * s, 5.15, -6.06), w=1.0, h=1.1, lid=fur, lid_tilt=18 * s, lid_drop=0.12,
                   **({"iris": C("#8a4b2a")} | (eye or {})))
            a.tuft(f"CheekTuft{S}", (2.55 * s, 3.6, -3.4), (0.6, 1.2, 1.6), fur, R=angles(0, 25 * s, 0))
            R = matmul(angles(0, 0, -35 * s), angles(-10, 0, 0))
            base = (1.75 * s, 6.25, -3.6)
            a.tri(f"Ear{S}", base, 1.3, 1.4, 0.5, fur, R=R)
            a.tri(f"InnerEar{S}", at(base, R, (0, 0.1, -0.27)), 0.75, 0.85, 0.1, inner, R=R, **DETAIL)

    for s, S in SIDES:
        for z, F in ((-1.8, "F"), (2.8, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (1.6 * s, 2.2, z)):
                a.post(f"Leg{F}{S}", (1.35, 2.0, 1.35), (1.6 * s, 1.3, z), fur, b=0.35)
                a.bevel(f"Hoof{F}{S}", (1.5, 0.6, 1.5), (1.6 * s, 0.3, z), dark, b=0.2, role="Accent")
                a.box(f"HoofSplit{F}{S}", (0.12, 0.45, 0.12), (1.6 * s, 0.3, z - 0.76), EYE, **DETAIL)

    with a.bone("Tail", "Body", (0, 5.0, 4.0)):
        a.box("Tail", (0.4, 1.3, 0.4), (0, 5.2, 4.25), fur, rot=(-30, 0, 0))
        a.box("TailCurl", (0.4, 0.4, 0.9), (0, 5.85, 4.35), fur)

    a.ride_height, a.ride_z = 6.0, 0.6

def _bear(a, fur, muzzle, belly, inner, claws, angry=True, head_extra=None, nose=EYE, iris=C("#6b4226")):
    a.oct("Body", (6.0, 5.4, 7.6), (0, 5.0, 0.8), fur, b=1.8, bottom=1.0)
    a.bevel("Belly", (6.06, 1.6, 6.6), (0, 3.1, 0.9), belly, b=0, bottom=1.03, role="Secondary")
    a.oct("Chest", (4.2, 3.2, 0.4), (0, 4.6, -3.02), belly, b=0.5, role="Secondary")

    with a.bone("Head", "Body", (0, 6.6, -2.6)):
        a.oct("Head", (5.6, 4.8, 4.4), (0, 8.2, -3.8), fur, b=1.5, bottom=0.8)
        a.oct("Muzzle", (2.9, 1.9, 1.5), (0, 7.0, -6.55), muzzle, b=0.6, role="Secondary")
        a.oct("Nose", (1.3, 0.75, 0.45), (0, 7.62, -7.35), nose, b=0.25, **DETAIL)
        a.box("NoseShine", (0.35, 0.15, 0.1), (-0.3, 7.85, -7.6), WHITE, **DETAIL)
        a.box("Mouth", (1.2, 0.3, 0.12), (0, 6.5, -7.33), MOUTH, **DETAIL)
        a.box("Tongue", (0.5, 0.14, 0.3), (0, 6.36, -7.36), TONGUE, **DETAIL)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (1.4 * s, 8.8, -6.06), w=1.15, h=1.35, iris=iris,
                   lid=fur if angry else None, lid_tilt=16 * s, lid_drop=0.1)
            a.box(f"Cheek{S}", (0.8, 0.4, 0.1), (2.05 * s, 7.6, -6.04), PINK, **DETAIL)
            for i, y in enumerate((7.9, 6.9)):
                a.tuft(f"CheekTuft{i}{S}", (2.9 * s, y, -4.2), (0.6, 1.2, 1.8), fur, R=angles(0, 25 * s, 0))
            a.oct(f"Ear{S}", (1.7, 1.7, 0.9), (2.1 * s, 10.8, -3.4), fur, b=0.55)
            a.oct(f"InnerEar{S}", (0.95, 0.95, 0.12), (2.1 * s, 10.7, -3.86), inner, b=0.3, **DETAIL)
        if head_extra:
            head_extra(a)

    for s, S in SIDES:
        for z, F in ((-1.8, "F"), (3.4, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (2.0 * s, 3.5, z)):
                a.post(f"Leg{F}{S}", (1.9, 3.2, 1.9), (2.0 * s, 2.3, z), fur, b=0.5)
                a.paw(f"Paw{F}{S}", (2.0 * s, 0, z - 0.3), 2.3, 2.6, fur, claws=claws if F == "F" else None, h=0.8)

    with a.bone("Tail", "Body", (0, 6.2, 4.6)):
        a.oct("Tail", (1.3, 1.3, 0.9), (0, 6.2, 4.9), fur, b=0.4)

    a.ride_height, a.ride_z = 7.7, 0.9

def _fox_tails(a, colors, tips, fans, tip_kw=NEON, effects_on=None, length=4.2, width=1.4, plain=False):
    base = (0, 5.4, 4.1)
    for i, fan in enumerate(fans):
        with a.bone(f"Tail{i + 1}", "Body", base):
            R = matmul(angles(0, 0, -fan), angles(-50, 0, 0))
            color = colors[i % len(colors)]
            if plain:
                a.box(f"Tail{i + 1}", (width, width, length), at(base, R, (0, 0, length / 2 + 0.2)), color, R=R)
            else:
                a.bevel(f"Tail{i + 1}", (width, width, length), at(base, R, (0, 0, length / 2 + 0.2)), color,
                        b=0.4, bottom=0.4, R=R)
            effects = effects_on(i) if effects_on else None
            a.box(f"TailTip{i + 1}", (width + 0.06, width + 0.06, 1.4), at(base, R, (0, 0, length + 0.7)),
                  tips[i % len(tips)], R=R, effects=effects, **tip_kw)


def pixel_star(a, name, center, size, color, R=None, depth=0.14, kw=NEON):
    """Chunky 4-point star: a plus sign with a diamond in the middle."""
    R = R or angles(0, 0, 0)
    a.box(f"{name}A", (size, size * 0.3, depth), center, color, R=R, **kw)
    a.box(f"{name}B", (size * 0.3, size, depth), center, color, R=R, **kw)
    a.box(f"{name}C", (size * 0.45, size * 0.45, depth), center, color, R=matmul(R, angles(0, 0, 45)), **kw)


# ------------------------------------------------------------ Common ----

def rabbit():
    a = Animal("Rabbit", "Rabbit", "Common")
    _bunny(a, C("#c98d5c"), C("#fff3e3"), ear_tip=C("#8a5a3a"))
    return a


def puffhop():
    a = Animal("Puffhop", "Puffhop", "Common")
    fluff, light, pink, spring, pom = C("#c7b3ff"), C("#f3edff"), C("#ff9ecb"), C("#8a78d8"), C("#ff6fb8")

    a.bevel("Body", (5.0, 4.4, 4.6), (0, 2.8, 0), fluff, b=1.3, bottom=0.8)
    a.box("Belly", (2.4, 1.1, 0.2), (0, 1.35, -2.35), C("#e9dfff"), role="Secondary")
    for s, S in SIDES:
        a.box(f"CheekFluff{S}", (0.7, 1.6, 1.6), (2.6 * s, 2.6, -0.9), light, role="Secondary")
        a.box(f"SideFluff{S}", (0.7, 1.3, 1.4), (2.6 * s, 3.3, 1.0), light, role="Secondary")
        a.eye2(f"Eye{S}", (1.1 * s, 3.4, -2.36), w=1.15, h=1.45, iris=C("#7a4ad8"))
        a.box(f"Cheek{S}", (0.75, 0.4, 0.1), (1.75 * s, 2.55, -2.34), pink, **DETAIL)
        with a.bone(f"Ear{S}", "Body", (1.4 * s, 4.8, 0.3)):
            R = angles(0, 0, -25 * s)
            ear_c = (1.8 * s, 5.4, 0.3)
            a.bevel(f"Ear{S}", (1.1, 1.7, 0.7), ear_c, fluff, b=0.35, R=R)
            a.box(f"InnerEar{S}", (0.6, 1.1, 0.1), at(ear_c, R, (0, -0.1, -0.36)), pink, R=R, **DETAIL)
        with a.bone(f"Antenna{S}", "Body", (0.6 * s, 5.0, -0.6)):
            pts = [(0.6, 5.0), (0.95, 5.7), (0.6, 6.4), (0.95, 7.1), (0.75, 7.6)]
            pts = [(x * s, y, -0.6) for x, y in pts]
            for i in range(len(pts) - 1):
                a.beam(f"Spring{i}{S}", pts[i], pts[i + 1], 0.3, spring, material="SmoothPlastic",
                       role="Secondary")
            a.box(f"Pompom{S}", (0.85, 0.85, 0.85), (0.75 * s, 8.0, -0.6), pom, rot=(0, 45, 0), **NEON)
    a.box("Nose", (0.5, 0.35, 0.15), (0, 2.8, -2.38), pink, **DETAIL)
    a.box("Mouth", (0.6, 0.15, 0.1), (0, 2.45, -2.38), C("#7a4a6a"), **DETAIL)

    for s, S in SIDES:
        for z, F in ((-1.3, "F"), (1.3, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (1.4 * s, 0.8, z)):
                a.box(f"Foot{F}{S}", (1.2, 0.6, 1.4), (1.4 * s, 0.3, z - 0.1), light, role="Secondary")
    with a.bone("Tail", "Body", (0, 2.4, 2.3)):
        a.bevel("Tail", (1.4, 1.4, 0.9), (0, 2.4, 2.6), light, b=0.35, bottom=0.35, role="Secondary")

    a.ride_height, a.ride_z = 5.0, 0.3
    return a


# ---------------------------------------------------------- Uncommon ----

def deer():
    a = Animal("Deer", "Deer", "Uncommon")
    antler = C("#f2dcb8")

    def antlers(a):
        for s, S in SIDES:
            a.box(f"Antler{S}", (0.35, 1.6, 0.35), (0.85 * s, 12.05, -2.9), antler, rot=(0, 0, -10 * s),
                  role="Accent")
            a.box(f"AntlerBranch{S}", (0.3, 0.3, 1.0), (0.95 * s, 12.2, -3.4), antler, role="Accent")
            a.box(f"AntlerTip{S}", (0.45, 0.45, 0.45), (1.0 * s, 12.85, -2.9), antler, role="Accent")

    _deer(a, C("#c98a52"), C("#fff0db"), C("#4a3426"), antlers=antlers, spots=WHITE)
    return a


def mossback_tortle():
    a = Animal("MossbackTortle", "Mossback Tortle", "Uncommon")
    skin, shell, rim, moss = C("#8fd08a"), C("#8a6340"), C("#e6cf94"), C("#6cc04a")

    a.bevel("Shell", (6.0, 2.8, 6.6), (0, 3.2, 0.3), shell, b=1.3, role="Secondary")
    a.box("ShellRim", (6.4, 0.7, 7.0), (0, 2.0, 0.3), rim, role="Secondary")
    a.bevel("Moss", (6.1, 1.5, 6.4), (0, 3.9, 0.3), moss, b=1.33)
    for i, (x, z) in enumerate([(1.2, -1.2), (-1.0, 1.6)]):
        a.box(f"MossTuft{i}", (1.2, 0.5, 1.2), (x, 4.85, z), C("#58ad3c"))
    trees = [((0.9, 4.6, 1.2), 1.9, C("#3e9b3f")), ((-1.1, 4.6, -0.8), 1.5, C("#5cc44a"))]
    for i, (base, d, leaf) in enumerate(trees):
        a.box(f"Trunk{i}", (0.5, 1.4, 0.5), add(base, (0, 0.7, 0)), C("#7a5230"), role="Accent")
        a.bevel(f"Leaves{i}", (d, d * 0.85, d), add(base, (0, 1.4 + d * 0.4, 0)), leaf, b=0.4, bottom=0.3)
    a.box("MushroomStem", (0.4, 0.6, 0.4), (-0.6, 4.9, 1.9), WHITE, role="Accent")
    a.box("MushroomCap", (1.1, 0.5, 1.1), (-0.6, 5.4, 1.9), C("#ef4a44"), role="Accent")
    for i, (dx, dz) in enumerate([(0.2, -0.2), (-0.25, 0.15)]):
        a.box(f"MushroomDot{i}", (0.22, 0.1, 0.22), (-0.6 + dx, 5.68, 1.9 + dz), WHITE, **DETAIL)
    for i, (x, z, col) in enumerate([(1.4, -0.4, C("#ffd84a")), (-1.4, 0.6, C("#ff8fc8")), (0.2, -2.0, WHITE)]):
        a.box(f"Flower{i}", (0.4, 0.4, 0.4), (x, 4.8, z), col, **DETAIL)

    with a.bone("Head", "Body", (0, 2.6, -2.8)):
        a.box("Neck", (1.8, 1.6, 2.0), (0, 2.6, -3.4), skin)
        a.bevel("Head", (3.2, 2.8, 3.0), (0, 3.3, -5.0), skin, b=0.8, bottom=0.5)
        a.box("Smile", (1.0, 0.2, 0.1), (0, 2.6, -6.53), C("#3d6b3a"), **DETAIL)
        a.box("LeafStem", (0.15, 0.5, 0.15), (0.2, 4.95, -5.0), C("#3e7a2e"), **DETAIL)
        a.box("Leaf", (0.8, 0.12, 0.5), (0.6, 5.2, -5.0), C("#58ad3c"), rot=(0, 0, 20), **DETAIL)
        for s, S in SIDES:
            a.eye2(f"Eye{S}", (0.8 * s, 3.6, -6.56), w=0.95, h=1.15, iris=C("#3a7a2e"))
            a.box(f"Cheek{S}", (0.55, 0.3, 0.1), (1.25 * s, 2.85, -6.54), PINK, **DETAIL)

    for s, S in SIDES:
        for z, F in ((-2.0, "F"), (2.6, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (2.6 * s, 1.6, z)):
                a.box(f"Leg{F}{S}", (1.6, 1.4, 1.8), (2.6 * s, 0.7, z), skin)
    with a.bone("Tail", "Body", (0, 2.0, 3.6)):
        a.wedge("Tail", (0.8, 0.6, 1.4), (0, 1.9, 4.2), skin, rot=(0, 180, 0))

    a.ride_height, a.ride_z = 5.0, 0.3
    return a


# -------------------------------------------------------------- Rare ----

def boar():
    a = Animal("Boar", "Boar", "Rare")
    _boar(a, C("#9a6444"), C("#c9926b"), C("#f0a894"), C("#4a2e22"), C("#fff6dc"))
    return a


def wolf():
    a = Animal("Wolf", "Wolf", "Rare")
    _canine(a, C("#a3abbd"), C("#f4f6fb"), dark=C("#646c80"))
    return a


# -------------------------------------------------------------- Epic ----

def glowhorn_stag():
    a = Animal("GlowhornStag", "Glowhorn Stag", "Epic")
    glow, tip = C("#72f7ff"), C("#e6feff")

    def antlers(a):
        for s, S in SIDES:
            R = angles(0, 0, -18 * s)
            base = (0.85 * s, 11.2, -2.9)
            a.box(f"Antler{S}", (0.45, 3.0, 0.45), at(base, R, (0, 1.5, 0)), glow, R=R, **NEON,
                  effects=[Animal.sparkles(glow, rate=3, size=0.5, speed=(0.3, 0.8))] if s == 1 else None)
            a.box(f"AntlerBranchA{S}", (1.5, 0.38, 0.38), at(base, R, (0.7, 1.0, 0)), glow,
                  R=matmul(R, angles(0, 0, 30 * s)), **NEON)
            a.box(f"AntlerBranchB{S}", (0.38, 0.38, 1.4), at(base, R, (0, 2.0, -0.6)), glow,
                  R=matmul(R, angles(20, 0, 0)), **NEON)
            a.box(f"AntlerBranchC{S}", (1.3, 0.38, 0.38), at(base, R, (0.6, 2.6, 0)), glow,
                  R=matmul(R, angles(0, 0, 40 * s)), **NEON)
            for i, p in enumerate([(1.35, 1.4, 0), (0, 2.3, -1.25), (1.1, 3.05, 0), (0, 3.05, 0)]):
                a.box(f"AntlerTip{i}{S}", (0.5, 0.5, 0.5), at(base, R, (p[0] * s, p[1], p[2])), tip,
                      R=matmul(R, angles(0, 45, 0)), **NEON)

    _deer(a, C("#34408f"), C("#a9b5ff"), C("#1c2352"), antlers=antlers, spots=glow,
          spot_kw=dict(NEON), inner=C("#8fe9ff"), tail=tip, tail_kw=dict(NEON))
    fx(a, "Head", Animal.light(glow, brightness=1.6, range_=18, name="AntlerLight"))
    return a


def bear():
    a = Animal("Bear", "Bear", "Epic")
    _bear(a, C("#94603c"), C("#f0d2a8"), C("#c99b6e"), C("#e8b48a"), C("#fff4e0"))
    return a


def frostfang_wolf():
    a = Animal("FrostfangWolf", "Frostfang Wolf", "Epic")
    ice = C("#9eeaff")

    def head_extra(a):
        a.shard("HeadCrystal", (0, 9.1, -3.4), 0.7, 1.6, ice, R=angles(-10, 0, 0), **GLASS)
        fx(a, "Snout", Animal.sparkles(C("#e8fbff"), rate=7, size=0.6, lifetime=(0.5, 0.9), speed=(3, 5),
                                       spread=18, emit="Front", name="FrostBreath",
                                       transparency=((0, 0.3), (1, 1))))

    _canine(a, C("#e2f4ff"), WHITE, dark=C("#b5dcf5"), inner=C("#aee6ff"), brow_color=C("#4f7fae"),
            eye=dict(iris=C("#2fd2ff"), glow=True), head_extra=head_extra)
    a.bevel("FrostMane", (4.6, 2.2, 2.6), (0, 5.6, -2.4), C("#bfeaff"), b=0.7, bottom=0.5, role="Secondary")
    for i, (x, z, h, tilt) in enumerate([(0, -1.4, 2.2, (-15, 0, 10)), (0.5, 0.4, 2.6, (-10, 0, -15)),
                                         (-0.4, 2.0, 2.0, (-20, 0, 15)), (0.1, 3.4, 1.5, (-35, 0, 0))]):
        a.shard(f"IceSpike{i}", (x, 6.2, z), 0.8, h, ice, R=angles(*tilt), **GLASS)
    for part in a.parts:
        if part["name"].startswith("TailTip"):
            part.update(color=ice, material="Glass", transparency=0.2, reflectance=0.15, studs=False, role="Glow")
    a.root_effects.append(Animal.sparkles(WHITE, rate=3, size=0.4, speed=(0.2, 0.6), name="Snowflakes"))
    return a


def emberback_boar():
    a = Animal("EmberbackBoar", "Emberback Boar", "Epic")
    lava, hot, gold = C("#ff5a14"), C("#ff9a1f"), C("#ffd04a")
    _boar(a, C("#3b3036"), C("#57434a"), C("#6e5058"), C("#1e1719"), gold, tusk_kw=dict(material="Neon"),
          eye=dict(iris=hot, glow=True), mohawk=[lava, hot, gold, hot, lava], mohawk_kw=dict(NEON), inner=lava)
    for s, S in SIDES:
        for i, (y, z, rx, length) in enumerate([(4.8, -1.6, 30, 1.6), (3.9, -0.6, -35, 1.3), (4.9, 0.8, 25, 1.5),
                                                (3.8, 1.9, -30, 1.2), (4.6, 3.0, 35, 1.1)]):
            a.box(f"LavaCrack{i}{S}", (0.14, 0.3, length), (2.53 * s, y, z), lava, rot=(rx, 0, 0), **NEON)
    fx(a, "Body",
       Animal.sparkles(hot, rate=14, size=1.4, lifetime=(0.4, 0.8), speed=(2, 3.5), spread=15,
                       texture=FIRE_TEXTURE, name="BackFire", color2=lava, sizes=((0, 0.4), (0.3, 1.5), (1, 0))),
       Animal.light(hot, brightness=1.5, range_=14, name="LavaGlow"))
    fx(a, "Tail", Animal.sparkles(gold, rate=6, size=0.4, lifetime=(0.8, 1.4), speed=(0.5, 1),
                                  accel=(0, -2, 0), name="EmberTrail"))
    return a


# --------------------------------------------------------- Legendary ----

def moonbear():
    a = Animal("Moonbear", "Moonbear", "Legendary")
    moon, fur, belly = C("#fff1a0"), C("#2d2f73"), C("#4b4c9e")

    def head_extra(a):
        pixel_star(a, "ForeheadStar", (0, 10.1, -6.07), 0.8, moon)
        for s, S in SIDES:
            a.box(f"EarStar{S}", (0.4, 0.4, 0.14), (2.1 * s, 11.35, -3.84), moon, rot=(0, 0, 45), **NEON)

    _bear(a, fur, C("#b9b2ff"), belly, C("#9d8cff"), moon, angry=False, head_extra=head_extra)
    # A chunky pixel crescent moon on the chest.
    z = -3.22
    for name, size, pos in [("MoonA", (0.5, 1.5, 0.14), (-0.75, 4.6, z)), ("MoonB", (0.5, 2.5, 0.14), (-0.25, 4.6, z)),
                            ("MoonC", (0.6, 0.5, 0.14), (0.3, 5.6, z)), ("MoonD", (0.6, 0.5, 0.14), (0.3, 3.6, z))]:
        a.box(name, size, pos, moon, **NEON)
    fx(a, "Body", Animal.sparkles(moon, rate=4, size=0.5, speed=(0.3, 0.8), name="Stardust"),
       Animal.light(moon, brightness=1.2, range_=16, name="MoonGlow"))
    return a


def sandsnapper():
    a = Animal("Sandsnapper", "Sandsnapper", "Legendary")
    sand, stripe, belly, gem = C("#f0c266"), C("#d38b34"), C("#fff4d8"), C("#35e0d0")

    a.bevel("Body", (6.4, 4.6, 8.0), (0, 3.2, 0.2), sand, b=1.4)
    a.box("Belly", (6.5, 1.4, 7.6), (0, 1.6, 0.2), belly, role="Secondary",
          effects=[Animal.sparkles(C("#e8c98a"), rate=4, size=2, lifetime=(0.8, 1.3), speed=(0.3, 0.8),
                                   texture=SMOKE_TEXTURE, name="SandDust", light=0,
                                   transparency=((0, 0.55), (1, 1)), emit="Bottom", sizes=((0, 1), (1, 2.4)))])
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
        a.box("Gem", (0.8, 0.8, 0.8), (0, 5.95, -6.2), gem, rot=(0, 45, 0), **NEON,
              effects=[Animal.sparkles(gem, rate=2, size=0.4, speed=(0.2, 0.5))])
        for s, S in SIDES:
            a.box(f"Nostril{S}", (0.6, 0.2, 0.6), (0.9 * s, 5.22, -12.6), C("#6a4420"), **DETAIL)
            for i, z in enumerate((-8.6, -9.8, -11.0, -12.2)):
                a.tooth(f"Tooth{i}{S}", (2.45 * s, 3.52, z), 0.85, 0.7)
            for i, z in enumerate((-9.2, -10.4, -11.6)):
                a.tooth(f"LowTooth{i}{S}", (2.35 * s, 2.13, z), 0.8, 0.6, up=True)
            a.tooth(f"FrontTooth{S}", (0.9 * s, 3.52, -13.35), 0.7, 0.65, R=angles(0, 90, 0))
            a.tooth(f"LowFrontTooth{S}", (0.9 * s, 2.13, -13.05), 0.65, 0.55, R=angles(0, 90, 0), up=True)
            a.bevel(f"EyeBump{S}", (2.1, 1.9, 2.0), (1.9 * s, 6.25, -6.4), sand, b=0.5)
            a.eye2(f"Eye{S}", (1.9 * s, 6.2, -7.46), w=1.5, h=1.45, look=(-0.6 * s, 0), iris=C("#1fc8b8"))
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


def thunderhoof():
    a = Animal("Thunderhoof", "Thunderhoof", "Legendary")
    bolt, mane = C("#ffe23a"), C("#46d2ff")

    def antlers(a):
        for s, S in SIDES:
            for i, (x, y, rz, h) in enumerate([(1.0, 11.9, -35, 1.3), (1.35, 12.6, 35, 1.1), (1.7, 13.35, -35, 1.4)]):
                a.box(f"Bolt{i}{S}", (0.45, h, 0.45), (x * s, y, -2.9), bolt, rot=(0, 0, rz * s), **NEON)

    def head_extra(a):
        for i, (y, z) in enumerate([(8.2, -1.35), (9.4, -1.6), (11.1, -1.9)]):
            a.wedge(f"Mane{i}", (0.55, 1.3, 1.4), (0, y, z), mane, rot=(0, 180, 0), **NEON)

    def tail(a):
        a.box("TailBolt0", (0.45, 1.3, 0.45), (0, 7.2, 3.9), bolt, rot=(-35, 0, 0), **NEON)
        a.box("TailBolt1", (0.45, 1.1, 0.45), (0, 7.7, 4.6), bolt, rot=(35, 0, 0), **NEON)
        a.box("TailBolt2", (0.45, 1.3, 0.45), (0, 8.3, 5.3), bolt, rot=(-35, 0, 0), **NEON)

    _deer(a, C("#f6f8ff"), C("#cfe0ff"), bolt, hoof_mat="Neon", antlers=antlers, head_extra=head_extra,
          inner=C("#9fe6ff"), tail=tail)
    for s, S in SIDES:
        for i, (y, z, rx, length) in enumerate([(6.6, -0.5, 30, 1.4), (6.05, 0.35, -35, 1.2), (5.5, 1.2, 30, 1.4)]):
            a.box(f"Flash{i}{S}", (0.14, 0.45, length), (1.83 * s, y, z), bolt, rot=(rx, 0, 0), **NEON)
    fx(a, "Body", Animal.sparkles(bolt, rate=8, size=0.45, lifetime=(0.2, 0.5), speed=(3, 6), name="Sparks"))
    return a


def crystal_hare():
    a = Animal("CrystalHare", "Crystal Hare", "Legendary")
    fur, soft = C("#f4f0ff"), C("#ddd3ff")
    cyan, pink, core = C("#8ff0ff"), C("#ffa8ee"), C("#e4fdff")

    def head_extra(a):
        for s, S in SIDES:
            R = angles(-5, 0, -10 * s)
            base = (1.0 * s, 6.5, -0.9)
            a.shard(f"EarCrystal{S}", base, 1.0, 4.0, cyan, R=R, **GLASS,
                    effects=[Animal.sparkles(cyan, rate=3, size=0.5, speed=(0.2, 0.6), name="Chime",
                                             color2=pink)] if s == 1 else None)
            a.box(f"EarCore{S}", (0.3, 2.2, 0.3), at(base, R, (0, 1.3, 0)), core, R=R, **NEON)
            a.shard(f"EarSmall{S}", (1.7 * s, 6.3, -0.7), 0.6, 1.9, pink, R=angles(-5, 0, -38 * s), **GLASS)

    _bunny(a, fur, soft, eye=dict(iris=C("#8a5cff"), pupil=C("#2b1250")), ears=False, head_extra=head_extra,
           tail=None)
    for i, (base, h, col, tilt) in enumerate([((0.6, 4.0, 0.5), 1.9, cyan, (-20, 0, -22)),
                                              ((-0.7, 4.0, 1.1), 1.6, pink, (-30, 0, 25)),
                                              ((0.0, 3.9, 1.9), 1.2, cyan, (-50, 0, 0))]):
        a.shard(f"BackCrystal{i}", base, 0.8, h, col, R=angles(*tilt), **GLASS)
    with a.bone("Tail", "Body", (0, 2.8, 3.0)):
        a.shard("TailCrystal", (0, 2.8, 3.1), 0.9, 1.6, pink, R=angles(-65, 0, 0), **GLASS)
    return a


# ------------------------------------------------------------ Mythic ----

def voidwhisker():
    a = Animal("Voidwhisker", "Voidwhisker", "Mythic")
    fur, soft, void = C("#21133a"), C("#3c2465"), C("#b14dff")

    def head_extra(a):
        a.box("Rune", (0.6, 0.6, 0.14), (0, 8.75, -5.78), void, rot=(0, 0, 45), **NEON)
        a.box("Collar", (3.3, 0.5, 2.5), (0, 5.3, -2.7), void, **NEON)
        a.box("CollarGem", (0.8, 0.8, 0.3), (0, 4.9, -4.02), C("#ffd6ff"), rot=(0, 0, 45), **NEON)
        for s, S in SIDES:
            for i, dy in enumerate((0.25, -0.15)):
                a.beam(f"Whisker{i}{S}", (1.1 * s, 6.45 + dy * 0.5, -6.2), (2.8 * s, 6.45 + dy * 2.5, -5.9), 0.1,
                       C("#e3b8ff"), **NEON)

    def tail(a):
        with a.bone("Tail", "Body", (0, 5.4, 4.1)):
            pts = [(0, 5.4, 4.1), (0, 6.6, 5.4), (0, 8.4, 5.8), (0.3, 9.8, 5.0)]
            for i in range(3):
                a.beam(f"Tail{i}", pts[i], pts[i + 1], 0.9 - 0.1 * i, fur)
            a.box("TailWisp", (1.2, 1.4, 1.2), (0.35, 10.3, 4.7), void, rot=(0, 45, 0), **NEON,
                  effects=[Animal.sparkles(void, rate=6, size=0.5, speed=(0.3, 0.9), name="VoidSparks",
                                           color2=C("#ff9cf2"))])

    _canine(a, fur, soft, inner=void, snout="cat", ear=(2.0, 2.3), brows=False, fangs=False,
            eye=dict(white=C("#f08cff"), iris=None), head_extra=head_extra, tail=tail)
    find(a, "EyeR")["material"] = find(a, "EyeL")["material"] = "Neon"
    for part in a.parts:
        if part["name"].startswith("InnerEar"):
            part.update(material="Neon", role="Glow", studs=False)
    for s, S in SIDES:
        a.box(f"Orb{S}", (0.7, 0.7, 0.7), (3.4 * s, 7.8, 1.0 - 1.2 * s), void, rot=(45, 45, 0), **NEON)
    fx(a, "Body",
       Animal.sparkles(C("#3a1466"), rate=5, size=2, lifetime=(1.0, 1.6), speed=(0.2, 0.6),
                       texture=SMOKE_TEXTURE, name="ShadowWisps", light=0, transparency=((0, 0.5), (1, 1)),
                       sizes=((0, 1.2), (1, 2.6))),
       Animal.light(void, brightness=1.2, range_=12, name="VoidGlow"))
    return a


def phoenix_fox():
    a = Animal("PhoenixFox", "Phoenix Fox", "Mythic")
    fur, red, orange, yellow = C("#ff6b2c"), C("#ff3b1f"), C("#ff8c1a"), C("#ffd23f")

    def head_extra(a):
        for i, (x, h, rz, col) in enumerate([(0, 1.9, 0, yellow), (0.55, 1.4, -20, orange), (-0.55, 1.4, 20, red)]):
            a.wedge(f"Crest{i}", (0.5, h, 1.6), (x, 9.3 + h / 2, -3.3), col, rot=(0, 0, rz), **NEON)
        for s, S in SIDES:
            R = angles(0, 0, -12 * s)
            a.box(f"EarFlame{S}", (0.6, 0.8, 0.6), at((1.3 * s, 9.1, -3.4), R, (0, 2.5, 0)), yellow, R=R, **NEON)

    def tail(a):
        _fox_tails(a, [fur], [yellow, orange, yellow], (-30, 0, 30), effects_on=lambda i: [
            Animal.sparkles(orange, rate=10, size=1.2, lifetime=(0.4, 0.7), speed=(1.5, 2.5), spread=20,
                            texture=FIRE_TEXTURE, name="TailFire", color2=red,
                            sizes=((0, 0.4), (0.3, 1.2), (1, 0)))] if i == 1 else None)

    _canine(a, fur, C("#fff1dc"), snout="fox", ear=(1.9, 2.4), brows=False, fangs=False, paws=C("#6b2417"),
            head_extra=head_extra, tail=tail, eye=dict(iris=C("#ff9a1f")))
    for s, S in SIDES:
        with a.bone(f"Wing{S}", "Body", (2.0 * s, 5.8, -1.0)):
            R = matmul(angles(0, -15 * s, 0), angles(0, 0, 28 * s))
            a.box(f"Wing{S}", (2.8, 0.4, 1.6), at((2.0 * s, 5.8, -1.0), R, (1.4 * s, 0, 0)), orange, R=R, **NEON)
            a.box(f"WingInner{S}", (1.8, 0.45, 1.0), at((2.0 * s, 5.8, -1.0), R, (0.9 * s, 0.05, 0.5)), yellow,
                  R=R, **NEON)
    fx(a, "Body", Animal.sparkles(yellow, rate=5, size=0.4, speed=(0.5, 1.2), accel=(0, 2, 0), name="Embers",
                                  color2=red),
       Animal.light(orange, brightness=1.5, range_=14, name="FireGlow"))
    return a


def skyfin_whale():
    a = Animal("SkyfinWhale", "Skyfin Whale", "Mythic")
    sky, belly, cloud, gold = C("#79c5ff"), C("#f2fbff"), C("#ffffff"), C("#ffd46b")

    a.bevel("Body", (8.4, 7.0, 15.0), (0, 7.6, 0), sky, b=2.2, bottom=1.4,
            effects=[Animal.sparkles(gold, rate=3, size=0.7, speed=(0.2, 0.6), name="Stardust")])
    a.bevel("Belly", (8.46, 2.4, 13.4), (0, 5.27, -0.2), belly, b=0, bottom=1.43, role="Secondary")
    for i, (x, y, z, d) in enumerate([(3.2, 4.2, -4.0, 3.0), (-3.4, 4.4, -2.5, 2.6), (3.6, 4.4, 2.5, 3.2),
                                      (-3.0, 4.1, 3.8, 3.0), (0, 3.4, 0, 3.6), (1.5, 3.6, 5.8, 2.4),
                                      (-1.2, 3.5, -5.8, 2.4)]):
        a.bevel(f"Cloud{i}", (d, d * 0.8, d), (x, y, z), cloud, b=d * 0.2, role="Secondary")
    a.box("Smile", (4.0, 0.3, 0.14), (0, 6.6, -7.55), C("#2a4a7a"), **DETAIL)
    for s, S in SIDES:
        a.box(f"SmileCorner{S}", (0.3, 0.7, 0.14), (2.1 * s, 6.85, -7.55), C("#2a4a7a"), **DETAIL)
        a.eye2(f"Eye{S}", (2.6 * s, 8.5, -7.56), w=1.6, h=1.9, iris=C("#2a6fd6"))
        a.box(f"Cheek{S}", (1.0, 0.5, 0.1), (3.2 * s, 7.2, -7.56), PINK, **DETAIL)
    a.box("Blowhole", (1.2, 0.2, 0.8), (0, 11.12, -3.0), C("#4f9ee0"), **DETAIL,
          effects=[Animal.sparkles(cloud, rate=3, size=2, lifetime=(1.0, 1.6), speed=(4, 5), spread=12,
                                   texture=SMOKE_TEXTURE, name="CloudSpout", light=0,
                                   transparency=((0, 0.2), (1, 1)), accel=(0, -1, 0), sizes=((0, 1), (1, 3)))])
    for i, (x, z) in enumerate([(1.2, -1.2), (-1.3, 2.2), (0.9, 5.2)]):
        pixel_star(a, f"Star{i}", (x, 11.14, z), 0.9, gold, R=angles(-90, 0, 0))

    for s, S in SIDES:
        pivot = (4.0 * s, 6.5, -2.0)
        with a.bone(f"Fin{S}", "Body", pivot):
            R = matmul(angles(0, -20 * s, 0), angles(0, 0, -25 * s))
            a.bevel(f"Fin{S}", (5.0, 0.9, 2.8), at(pivot, R, (2.6 * s, 0, 0)), cloud, b=0.3, bottom=0.3, R=R)
            a.box(f"FinFeather{S}", (4.0, 0.8, 2.2), at(pivot, R, (2.2 * s, -0.2, 1.4)), C("#dff1ff"), R=R,
                  role="Secondary")
            a.box(f"FinFeatherSmall{S}", (3.0, 0.7, 1.8), at(pivot, R, (1.8 * s, -0.35, 2.6)), C("#c4e6ff"), R=R,
                  role="Secondary")

    with a.bone("Tail", "Body", (0, 8.0, 6.8)):
        a.bevel("Tail", (5.0, 4.0, 5.0), (0, 8.3, 9.2), sky, b=1.2, bottom=0.8, R=angles(-10, 0, 0),
                effects=[Animal.sparkles(cloud, rate=2, size=3, lifetime=(1.2, 1.8), speed=(0.2, 0.5),
                                         texture=SMOKE_TEXTURE, name="CloudTrail", light=0,
                                         transparency=((0, 0.4), (1, 1)))])
        for s, S in SIDES:
            R = matmul(angles(0, -25 * s, 0), angles(0, 0, 12 * s))
            base = (0, 9.2, 11.6)
            a.bevel(f"Fluke{S}", (5.2, 0.9, 3.0), at(base, R, (2.6 * s, 0, 0)), sky, b=0.3, bottom=0.3, R=R)
            a.box(f"FlukeTip{S}", (0.9, 0.9, 0.9), at(base, R, (5.3 * s, 0, 0.3)), gold, R=matmul(R, angles(0, 45, 0)),
                  **NEON)

    a.ride_height, a.ride_z = 11.1, -1.0
    return a


# ------------------------------------------------------------ Secret ----

def starlight_kitsune():
    a = Animal("StarlightKitsune", "Starlight Kitsune", "Secret")
    fur, soft, lilac, gold = C("#f8f4ff"), C("#e0d4ff"), C("#b58cff"), C("#fff3a0")
    rainbow = [C(h) for h in ("#ff6b9d", "#ff9b5e", "#ffd84d", "#8ef56b", "#5ef0d0", "#5cc8ff", "#7f8cff",
                              "#b57bff", "#f27bff")]

    def head_extra(a):
        pixel_star(a, "StarMark", (0, 8.75, -5.77), 0.8, C("#ff7be5"))
        pixel_star(a, "Crown", (0, 11.4, -3.8), 1.6, gold, depth=0.35)
        for s, S in SIDES:
            R = angles(0, 0, -12 * s)
            a.box(f"EarTip{S}", (0.6, 0.8, 0.6), at((1.3 * s, 9.1, -3.4), R, (0, 2.5, 0)), lilac, R=R, **NEON)

    def tail(a):
        _fox_tails(a, [fur, soft], rainbow, range(-64, 65, 16), length=4.0, width=1.2, plain=True)

    _canine(a, fur, soft, snout="fox", ear=(1.9, 2.4), brows=False, fangs=False, paws=lilac,
            eye=dict(iris=C("#8a5cff"), pupil=C("#2b1250")), head_extra=head_extra, tail=tail)
    for s, S in SIDES:
        a.box(f"Orbit{S}", (0.7, 0.7, 0.7), (3.4 * s, 8.0, 0.4 + 1.0 * s), gold, rot=(45, 45, 0), **NEON)
    fx(a, "Body", Animal.sparkles(C("#ff9cf2"), rate=8, size=0.5, speed=(0.4, 1.2), name="Starfall",
                                  color2=C("#7fe8ff")),
       Animal.light(C("#d9b8ff"), brightness=1.4, range_=16, name="StarGlow"))
    return a


# --------------------------------------------------------- Exclusive ----

def royal_griffin():
    a = Animal("RoyalGriffin", "Royal Griffin", "Exclusive")
    gold, deep, white, beak = C("#f2c14e"), C("#d99a2b"), C("#fffaf0"), C("#ffb52e")
    crown, red, blue = C("#ffd23a"), C("#d8283f"), C("#4fb4ff")
    shiny = dict(reflectance=0.25, role="Accent")

    a.bevel("Body", (5.2, 4.6, 8.4), (0, 5.4, 0.8), gold, b=1.4,
            effects=[Animal.sparkles(crown, rate=4, size=0.5, speed=(0.3, 0.8), name="RoyalSparkles")])
    a.box("Belly", (5.3, 1.1, 7.4), (0, 3.65, 1.0), C("#ffe39a"), role="Secondary")
    a.bevel("ChestFeathers", (4.8, 4.4, 1.8), (0, 5.6, -3.2), white, b=1.2, bottom=0.8, role="Secondary")
    a.bevel("Saddle", (4.0, 0.8, 3.2), (0, 8.0, 1.0), red, b=0.3, role="Accent")
    a.box("SaddleTrim", (4.3, 0.3, 3.5), (0, 7.65, 1.0), crown, **shiny)
    a.box("SaddleHorn", (0.6, 0.8, 0.6), (0, 8.6, -0.4), crown, **shiny)
    for s, S in SIDES:
        a.box(f"Drape{S}", (0.3, 2.2, 3.0), (2.65 * s, 6.8, 1.0), red, role="Accent")
        a.box(f"DrapeTrim{S}", (0.34, 0.3, 3.04), (2.66 * s, 5.75, 1.0), crown, **shiny)

    with a.bone("Head", "Body", (0, 7.2, -3.0)):
        a.box("Neck", (3.2, 3.0, 2.4), (0, 7.6, -3.4), white)
        a.bevel("Head", (4.2, 3.6, 3.8), (0, 9.6, -4.2), white, b=1.0, bottom=0.4)
        a.bevel("Beak", (2.2, 1.2, 2.0), (0, 9.1, -7.0), beak, b=0.4, role="Accent")
        a.box("LowerBeak", (1.8, 0.6, 1.6), (0, 8.3, -6.9), C("#e89a1e"), role="Accent")
        a.box("BeakHook", (1.2, 0.9, 0.6), (0, 8.5, -8.1), beak, role="Accent")
        for i, (x, y) in enumerate([(0, 11.9), (0.8, 11.7), (-0.8, 11.7)]):
            a.wedge(f"HeadFeather{i}", (0.6, 1.3, 1.8), (x, y, -2.6), deep, role="Secondary")
        a.box("Crown", (2.6, 0.8, 2.6), (0, 11.8, -4.4), crown, **shiny)
        a.tri("CrownPointF", (0, 12.2, -5.72), 0.8, 0.9, 0.3, crown, **shiny)
        a.box("CrownRuby", (0.5, 0.5, 0.14), (0, 11.8, -5.75), red, **NEON)
        for s, S in SIDES:
            a.tri(f"CrownPoint{S}", (1.32 * s, 12.2, -4.4), 0.8, 0.9, 0.3, crown, R=angles(0, 90, 0), **shiny)
            a.box(f"CrownSapphire{S}", (0.14, 0.45, 0.45), (1.34 * s, 11.8, -4.4), blue, **NEON)
            a.eye2(f"Eye{S}", (1.2 * s, 10.0, -6.16), w=1.05, h=1.25, iris=C("#ffb52e"))

    for s, S in SIDES:
        pivot = (2.4 * s, 7.4, -0.8)
        with a.bone(f"Wing{S}", "Body", pivot):
            R = matmul(angles(0, -10 * s, 0), angles(0, 0, 30 * s))
            a.bevel(f"Wing{S}", (6.0, 0.8, 2.6), at(pivot, R, (3.0 * s, 0.3, 0.4)), white, b=0.3, R=R)
            a.box(f"WingMid{S}", (5.0, 0.7, 2.2), at(pivot, R, (2.6 * s, 0, 1.9)), gold, R=R, role="Secondary")
            a.box(f"WingLow{S}", (3.8, 0.6, 1.8), at(pivot, R, (2.0 * s, -0.2, 3.2)), deep, R=R, role="Secondary")
            for i, (x, z, yaw) in enumerate([(6.4, -0.2, 8), (6.0, 0.8, 0), (5.4, 1.8, -10)]):
                a.box(f"Feather{i}{S}", (2.0, 0.5, 0.8), at(pivot, R, (x * s, 0.3 - 0.05 * i, z)), white,
                      R=matmul(R, angles(0, yaw * s, 0)))

    for s, S in SIDES:
        with a.bone(f"LegF{S}", "Body", (1.4 * s, 4.0, -2.2)):
            a.box(f"LegF{S}", (1.4, 1.6, 1.4), (1.4 * s, 3.3, -2.2), white)
            a.box(f"ShinF{S}", (1.0, 2.6, 1.0), (1.4 * s, 1.5, -2.2), beak, role="Accent")
            a.box(f"TalonF{S}", (1.6, 0.5, 1.8), (1.4 * s, 0.25, -2.5), beak, role="Accent")
            for i, dx in enumerate((-0.45, 0.45)):
                a.wedge(f"Claw{i}{S}", (0.4, 0.4, 0.6), (1.4 * s + dx, 0.2, -3.65), C("#5a3a1a"), **DETAIL)
        with a.bone(f"LegB{S}", "Body", (1.6 * s, 3.9, 3.4)):
            a.bevel(f"LegB{S}", (1.6, 3.6, 1.8), (1.6 * s, 2.1, 3.4), gold, b=0.4)
            a.box(f"PawB{S}", (1.8, 0.6, 2.2), (1.6 * s, 0.3, 3.1), gold)

    with a.bone("Tail", "Body", (0, 6.4, 5.0)):
        a.box("Tail", (0.6, 0.6, 3.0), (0, 6.0, 6.4), gold, rot=(25, 0, 0))
        a.bevel("TailTuft", (1.4, 1.4, 1.4), (0, 5.4, 8.0), deep, b=0.4, bottom=0.4, role="Secondary")

    a.ride_height, a.ride_z = 8.4, 1.0
    return a


ALL = [
    rabbit, puffhop, deer, mossback_tortle, boar, wolf, glowhorn_stag, bear, frostfang_wolf, emberback_boar,
    moonbear, sandsnapper, thunderhoof, crystal_hare, voidwhisker, phoenix_fox, skyfin_whale,
    starlight_kitsune, royal_griffin,
]
