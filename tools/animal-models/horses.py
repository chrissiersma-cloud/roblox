"""The five rideable horses: Pony, Brown Horse, Paint Horse, Black Stallion and Golden Mustang.

They share one horse body (the same as the Thunder Unicorn's, so all mounts move alike), and each gets its own
coat, markings, mane, tack and effects. Like the Dark Woods animals, the rarer the horse, the more effects:

    Pony           Common     caramel, a fluffy blond mane, a red blanket and a flower behind its ear
    BrownHorse     Rare       chestnut with white socks and a blaze, a western saddle with a lasso and bags
    PaintHorse     Epic       white with chestnut patches, a turquoise diamond blanket, a bandana, sparkly steps
    BlackStallion  Legendary  jet black with a long flowing mane and feathered hooves, crimson and gold tack,
                              golden hoof trails, snorting steam, rears up
    GoldenMustang  Mythic     gold with a shining cream mane, glowing golden hooves, sparkle trails everywhere
                              it runs, stars that circle it, rears up in a burst of sparkles

Faces -Z, +X is its right side and y = 0 is the ground. The AnimalFX script animates them (walk, gallop, an idle
action); the RideAttachment on the RootPart is the seat on the saddle.
"""

import math

from animals import DETAIL, PINK, find, fx, pixel_star
from dark_woods import GLOW, chain, emitter, extras, light, pulse, scale_animal, trail, unfight
from lib import SIDES, SMOKE_TEXTURE, SPARKLE_TEXTURE, WHITE, Animal, add, angles, apply, matmul, scale
from lib import hex_color as C

NECK_UP = (0, 0.788, -0.616)      # along the neck, towards the head
NECK_BACK = (0, 0.616, 0.788)     # out of the back (top) of the neck


def horse(a, H):
    """Builds the shared horse. H holds the colours and options of one horse (see the horses below)."""
    dy = H.get("dy", 0.0)             # negative = shorter legs (the pony)
    U = lambda x, y, z: (x, y + dy, z)
    coat, light_c = C(H["coat"]), C(H["light"])
    mane = [C(c) for c in H["mane"]]

    # -- body ---------------------------------------------------------------
    a.oct("Body", (3.8, 3.4, 7.2), U(0, 6.0, 0.4), coat, b=1.0, bottom=0.7)
    a.bevel("Belly", (3.86, 1.2, 6.4), U(0, 4.9, 0.45), light_c, b=0, bottom=0.73, role="Secondary")
    a.oct("Chest", (3.1, 2.6, 0.5), U(0, 5.9, -3.35), light_c, b=0.45, role="Secondary")
    a.oct("Withers", (2.4, 0.6, 1.6), U(0, 7.75, -2.2), coat, b=0.25)
    for i, (x, y, z, w, h, d) in enumerate(H.get("patches", ())):
        # Coat patches (the paint horse): thin plates on the flat sides and the top of the body.
        if abs(x) > 1:
            a.box(f"Patch{i}", (0.12, h, d), U(x, y, z), C(H["patch"]), role="Accent", shadow=False)
        else:
            a.box(f"Patch{i}", (w, 0.12, d), U(x, y, z), C(H["patch"]), role="Accent", shadow=False)

    tack(a, H, U)

    # -- head and neck --------------------------------------------------------
    with a.bone("Head", "Body", U(0, 7.2, -2.6)):
        neck_R = matmul(angles(-38, 0, 0), angles(90, 0, 0))
        a.taper("Neck", (2.3, 2.5), (1.8, 2.0), 4.4, U(0, 8.75, -3.6), coat, R=neck_R, r=0.35)
        a.box("Throat", (1.2, 2.6, 0.3), U(0, 8.25, -4.45), light_c, rot=(-38, 0, 0), role="Secondary")
        head_R = angles(-22, 0, 0)
        hc = U(0, 10.95, -5.35)
        hat = lambda x, y, z: add(hc, apply(head_R, (x, y, z)))
        a.oct("Head", (2.6, 3.0, 2.9), hc, coat, b=0.8, bottom=0.55, R=head_R)
        a.taper("Muzzle", (2.2, 1.5), (1.95, 1.3), 1.9, hat(0, -0.62, -2.2), C(H["muzzle"]), R=head_R, r=0.32,
                role="Secondary")
        nose = C(H.get("nose", "#3a2a2a"))
        for s, S in SIDES:
            a.box(f"Nostril{S}", (0.3, 0.36, 0.12), hat(0.48 * s, -0.4, -3.17), nose, R=head_R, **DETAIL)
        a.box("Smile", (0.7, 0.12, 0.1), hat(0, -0.98, -3.16), nose, R=head_R, **DETAIL)
        if H.get("blaze"):
            # A white star on the forehead and a stripe down the nose.
            a.box("BlazeStar", (0.55, 0.55, 0.1), hat(0, 1.25, -1.47), WHITE, R=matmul(head_R, angles(0, 0, 45)),
                  **DETAIL)
            a.box("Blaze", (0.32, 0.06, 1.75), hat(0, 0.15, -2.2), WHITE, R=head_R, **DETAIL)
        iris = C(H.get("iris", "#6b4226"))
        for s, S in SIDES:
            eye_R = matmul(head_R, angles(0, -14 * s, 0))
            a.eye2(f"Eye{S}", hat(0.66 * s, 0.68, -1.5), R=eye_R, w=1.0, h=1.2, iris=iris,
                   glow=H.get("glow_eyes", False))
            a.box(f"Brow{S}", (0.75, 0.16, 0.12), hat(0.7 * s, 1.42, -1.52), C(H.get("brow", "#2a1a14")),
                  R=matmul(eye_R, angles(0, 0, -14 * s)), **DETAIL)
            if H.get("lashes"):
                a.tri(f"Lash{S}", hat(1.12 * s, 1.22, -1.5), 0.3, 0.38, 0.08, C("#1b1420"),
                      R=matmul(eye_R, angles(0, 0, -40 * s)), **DETAIL)
            if H.get("cheeks", True):
                a.box(f"Cheek{S}", (0.5, 0.26, 0.1), hat(1.0 * s, -0.08, -1.49), PINK, R=eye_R, **DETAIL)
            ear_R = matmul(angles(0, 0, -16 * s), angles(78, 0, 0))
            ear_c = C(H.get("ear", H["coat"]))
            a.taper(f"Ear{S}", (0.75, 0.8), (0.3, 0.35), 1.6, hat(0.8 * s, 2.15, 0.55), ear_c, R=ear_R, r=0.4)
            a.box(f"InnerEar{S}", (0.34, 1.0, 0.1), hat(0.8 * s, 2.1, 0.17), C(H.get("inner_ear", "#f2a7b8")),
                  R=matmul(head_R, angles(0, 0, -16 * s)), **DETAIL)
        bridle(a, H, hat, head_R)
        forelock(a, H, hat, head_R, mane)
        if H.get("head_extra"):
            H["head_extra"](a, hat, head_R)
        mane_strands(a, H, U, mane)

    # -- legs ---------------------------------------------------------------
    hip = 4.7 + dy
    knee = 2.65 + dy * 0.5
    socks = H.get("socks", ())
    for s, S in SIDES:
        for z, F in ((-2.3, "F"), (2.7, "B")):
            with a.bone(f"Leg{F}{S}", "Body", (1.15 * s, hip, z)):
                upper = hip + 0.1 - (knee - 0.35)
                a.taper(f"Leg{F}{S}", (1.25, 1.3), (0.9, 0.95), upper, (1.15 * s, (hip + 0.1 + knee - 0.35) / 2, z),
                        coat, R=angles(-90, 0, 0), r=0.3)
                low_c = WHITE if f"{F}{S}" in socks else C(H.get("leg", H["dark"]))
                a.post(f"LowerLeg{F}{S}", (0.82, knee - 0.45, 0.88), (1.15 * s, (knee + 0.45) / 2, z), low_c, b=0.25)
                if H.get("feather"):
                    # Long hair around the fetlock (feathering), falling over the hoof.
                    fc = C(H["feather"])
                    a.box(f"Feather{F}{S}", (1.15, 0.7, 1.15), (1.15 * s, 0.85, z + 0.05), fc, rot=(0, 45, 0),
                          role="Secondary")
                    for k, (dx, dz) in enumerate(((0.38, 0.3), (-0.38, 0.3), (0, 0.46))):
                        a.wedge(f"FeatherTuft{k}{F}{S}", (0.5, 0.55, 0.42), (1.15 * s + dx, 0.52, z + dz), fc,
                                rot=(0, 180, 0), role="Secondary", shadow=False)
                else:
                    a.box(f"Fetlock{F}{S}", (0.92, 0.3, 0.97), (1.15 * s, 0.73, z), light_c if low_c != WHITE
                          else C("#e9e2d6"), role="Secondary")
                hoof_kw = dict(H.get("hoof_kw", {"role": "Accent"}))
                a.bevel(f"Hoof{F}{S}", (1.1, 0.58, 1.16), (1.15 * s, 0.29, z), C(H["hoof"]), b=0.18, **hoof_kw)
                if H.get("shoe"):
                    a.box(f"Shoe{F}{S}", (1.16, 0.12, 1.22), (1.15 * s, 0.07, z), C(H["shoe"]), role="Accent",
                          shadow=False, reflectance=0.2)

    # -- tail ----------------------------------------------------------------
    with a.bone("Tail", "Body", U(0, 7.0, 3.9)):
        long = H.get("tail_long", 1.0)
        pts = [U(0, 7.25, 4.2), U(0, 6.85, 4.95), U(0, 6.0, 5.4), U(0, 5.0, 5.6),
               U(0, 5.0 - 1.1 * long, 5.65)]
        chain(a, "Tail", pts, [0.7, 0.8, 0.8, 0.72], mane[0], role="Secondary")
        for sx, S in ((1, "R"), (-1, "L")):
            side = [add(p, (0.3 * sx, -0.1, 0.18 + 0.05 * k)) for k, p in enumerate(pts[1:])]
            chain(a, f"TailStrand{S}", side, [0.42, 0.45, 0.4], mane[1 % len(mane)], role="Secondary")
        tip = pts[-1]
        a.wedge("TailTip", (0.75, 0.7, 0.7), add(tip, (0, -0.55, 0.05)), mane[0], rot=(180, 0, 0), role="Secondary")
        if H.get("tail_glow"):
            a.box("TailShine", (0.24, 1.9 * long, 0.24), add(pts[3], (0, -0.5 * long, 0.3)), C(H["tail_glow"]),
                  **GLOW)

    a.ride_height, a.ride_z = 8.45 + dy, 0.25
    a.overhead = 13.4 + dy
    if H.get("extra"):
        H["extra"](a, U)
    scale_animal(a, H.get("k", 1.45))
    unfight(a, "Belly", "Chest", "Seat", "Blanket", "Throat", "Muzzle", d=0.04)


def mane_strands(a, H, U, mane):
    """The mane: a crest along the back of the neck, and strands of hair falling down one or both sides."""
    style = H.get("mane_style", "normal")
    length = {"fluffy": 0.9, "normal": 1.6, "flowing": 2.7}[style]
    n = 7
    for i in range(n):
        t = 2.4 - i * 4.4 / (n - 1)             # from the head (t = 2.4) down to the withers (t = -2.0)
        p = add(add(U(0, 9.43, -2.73), scale(NECK_UP, t)), scale(NECK_BACK, 0.22))
        c = mane[i % len(mane)]
        a.box(f"ManeCrest{i}", (0.95, 0.78, 0.72), p, c, rot=(-38, 0, 0), role="Secondary")
        half = 1.025 + 0.057 * (-t)             # the neck gets wider towards the body
        sides = (1, -1) if style in ("fluffy", "flowing") else (1,)
        for sx in sides:
            L = length * (1.0 if sx == 1 else 0.7) * (0.85 + 0.15 * ((i + (sx < 0)) % 2))
            top = add(p, (sx * (half - 0.25), 0.1, 0.0))
            a.box(f"ManeStrand{i}{'R' if sx > 0 else 'L'}", (0.36, L, 0.78), add(top, (sx * 0.12, -L / 2, 0.1)),
                  mane[(i + 1) % len(mane)] if sx < 0 else c, rot=(0, 0, -6 * sx), role="Secondary")
        if style == "fluffy":
            a.box(f"ManeFluff{i}", (1.3, 0.55, 0.62), add(p, scale(NECK_BACK, 0.25)), mane[(i + 1) % len(mane)],
                  rot=(-38, 0, 0), role="Secondary", shadow=False)
    if H.get("mane_glow"):
        for i in (1, 3, 5):
            t = 2.4 - i * 4.4 / (n - 1)
            p = add(add(U(0, 9.43, -2.73), scale(NECK_UP, t)), scale(NECK_BACK, 0.62))
            a.box(f"ManeShine{i}", (0.3, 0.3, 0.55), p, C(H["mane_glow"]), rot=(-38, 0, 0), **GLOW)


def forelock(a, H, hat, head_R, mane):
    style = H.get("mane_style", "normal")
    a.box("Forelock", (1.0, 0.7, 0.9), hat(0, 1.75, -0.6), mane[0], R=head_R, role="Secondary")
    drop = {"fluffy": 0.7, "normal": 0.9, "flowing": 1.3}[style]
    a.box("ForelockFringe", (0.8, drop, 0.3), hat(0.12, 1.65 - drop / 2, -1.25), mane[1 % len(mane)],
          R=matmul(head_R, angles(0, 0, 10)), role="Secondary")
    if style == "fluffy":
        a.box("ForelockFluff", (1.3, 0.6, 1.1), hat(0, 2.15, -0.3), mane[1 % len(mane)], R=head_R, role="Secondary")


def bridle(a, H, hat, head_R):
    b = C(H["bridle"])
    metal = C(H.get("metal", "#c9a24a"))
    a.box("NoseBand", (2.06, 0.24, 1.98), hat(0, -0.15, -2.1), b, R=head_R, **DETAIL)
    a.box("BrowBand", (2.66, 0.24, 0.3), hat(0, 1.4, -0.2), b, R=head_R, **DETAIL)
    for s, S in SIDES:
        a.box(f"CheekStrap{S}", (0.12, 2.3, 0.26), hat(1.32 * s, 0.1, -0.2), b, R=head_R, **DETAIL)
        a.cyl(f"Rosette{S}", 0.14, 0.5, hat(1.37 * s, -0.95, -0.2), metal, R=head_R, role="Accent", shadow=False,
              reflectance=0.2)
        a.box(f"Bit{S}", (0.12, 0.4, 0.4), hat(1.07 * s, -0.75, -1.6), metal, R=head_R, role="Accent", shadow=False)


def tack(a, H, U):
    """Saddle blanket, saddle, stirrups and girth (and, per horse, a pattern, conchos and a breast collar)."""
    T = H["tack"]
    bl, trim, sad, metal = C(T["blanket"]), C(T["trim"]), C(T["saddle"]), C(T.get("metal", "#c9a24a"))
    refl = 0.2 if T.get("shiny") else 0.0
    a.bevel("Blanket", (4.06, 0.3, 3.2), U(0, 7.72, 0.3), bl, b=0.12, role="Accent")
    for s, S in SIDES:
        a.box(f"BlanketFlap{S}", (0.22, 1.9, 3.2), U(2.0 * s, 6.85, 0.3), bl, role="Accent")
        a.box(f"BlanketTrim{S}", (0.26, 0.24, 3.3), U(2.02 * s, 5.95, 0.3), trim, role="Accent")
        if T.get("pattern") == "diamonds":
            for k, z in enumerate((-0.7, 0.3, 1.3)):
                a.box(f"Diamond{k}{S}", (0.12, 0.62, 0.62), U(2.13 * s, 6.85, z), trim,
                      rot=(45, 0, 0), role="Accent", shadow=False)
                a.box(f"DiamondDot{k}{S}", (0.14, 0.24, 0.24), U(2.15 * s, 6.85, z), C(T["dots"]),
                      rot=(45, 0, 0), role="Accent", shadow=False)
        elif T.get("pattern") == "stripes":
            for k, y in enumerate((6.35, 7.35)):
                a.box(f"Stripe{k}{S}", (0.24, 0.16, 3.24), U(2.02 * s, y, 0.3), C(T["dots"]), role="Accent",
                      shadow=False)
        else:
            a.box(f"BlanketTrimBack{S}", (0.26, 1.9, 0.22), U(2.02 * s, 6.85, 1.85), trim, role="Accent",
                  shadow=False)
            a.box(f"BlanketTrimFront{S}", (0.26, 1.9, 0.22), U(2.02 * s, 6.85, -1.25), trim, role="Accent",
                  shadow=False)
        # Stirrups.
        a.box(f"StirrupStrap{S}", (0.12, 2.0, 0.3), U(2.25 * s, 5.85, 0.2), sad, role="Accent", shadow=False)
        st = C(T.get("stirrup", T["saddle"]))
        a.box(f"Stirrup{S}", (0.5, 0.14, 0.8), U(2.32 * s, 4.75, 0.2), st, role="Accent", reflectance=refl)
        for z in (-0.35, 0.35):
            a.box(f"StirrupSide{S}{'F' if z < 0 else 'B'}", (0.5, 0.6, 0.12), U(2.32 * s, 5.0, 0.2 + z), st,
                  role="Accent", shadow=False)
        if T.get("conchos"):
            a.cyl(f"Concho{S}", 0.12, 0.55, U(2.2 * s, 7.5, -0.7), metal, role="Accent", shadow=False,
                  reflectance=0.3)
    a.bevel("Seat", (2.7, 0.55, 2.5), U(0, 8.12, 0.3), sad, b=0.2, role="Accent")
    a.bevel("Cantle", (2.5, 0.75, 0.45), U(0, 8.55, 1.45), sad, b=0.2, role="Accent")
    a.box("CantleTrim", (2.56, 0.16, 0.5), U(0, 8.95, 1.45), metal if T.get("shiny") else trim, role="Accent",
          shadow=False, reflectance=refl)
    a.bevel("Pommel", (1.6, 0.6, 0.45), U(0, 8.5, -0.85), sad, b=0.2, role="Accent")
    a.post("SaddleHorn", (0.4, 0.5, 0.4), U(0, 9.05, -0.85), C(T.get("horn", T["saddle"])), b=0.1, role="Accent")
    a.box("SaddleHornCap", (0.65, 0.18, 0.65), U(0, 9.35, -0.85), metal if T.get("shiny") else sad, role="Accent",
          reflectance=refl)
    a.box("Girth", (4.0, 0.4, 0.5), U(0, 4.4, 0.3), sad, role="Accent", shadow=False)
    if T.get("breast"):
        # A breast collar across the chest with a medallion.
        a.box("BreastCollar", (3.3, 0.36, 0.2), U(0, 6.55, -3.68), sad, role="Accent", shadow=False)
        for s, S in SIDES:
            a.box(f"BreastStrap{S}", (0.2, 0.36, 2.7), U(1.97 * s, 6.55, -2.25), sad, role="Accent", shadow=False)
        a.cyl("BreastMedal", 0.16, 0.95, U(0, 6.4, -3.82), metal, R=angles(0, 90, 0), role="Accent", reflectance=0.3)


# ------------------------------------------------------------------ horses ---

def pony():
    a = Animal("Pony", "Pony", "Common")

    def flower(a, hat, head_R):
        # A daisy tucked behind the left ear.
        c = hat(-1.15, 2.0, 0.55)
        for k in range(5):
            ang = math.radians(k * 72)
            a.box(f"Petal{k}", (0.3, 0.12, 0.22), add(c, apply(head_R, (0.22 * math.cos(ang), 0.22 * math.sin(ang), 0))),
                  WHITE, R=matmul(head_R, angles(0, 0, k * 72)), **DETAIL)
        a.box("FlowerHeart", (0.22, 0.22, 0.16), add(c, apply(head_R, (0, 0, -0.04))), C("#ffd23f"), R=head_R, **DETAIL)

    horse(a, dict(
        coat="#d9a066", light="#f2d2a2", dark="#b9824c", muzzle="#f2d8b4", mane=["#fff0b8", "#f2d27a"],
        mane_style="fluffy", hoof="#5a3a24", iris="#7a4a22", feather="#fff0b8", dy=-0.9, k=1.3,
        bridle="#a33a2a",
        tack=dict(blanket="#e0453a", trim="#ffffff", saddle="#8a5a2e", stirrup="#6b4424", pattern="stripes",
                  dots="#ffffff"),
        head_extra=flower,
    ))
    extras(a, attrs={"WalkSpeed": 10})
    return a


def brown_horse():
    a = Animal("BrownHorse", "Brown Horse", "Rare")

    def gear(a, U):
        # Saddlebags behind the saddle, a bedroll and a coiled lasso on the saddle.
        for s, S in SIDES:
            a.bevel(f"Saddlebag{S}", (0.5, 1.2, 1.1), U(2.05 * s, 7.1, 2.15), C("#7a4a24"), b=0.15, role="Accent")
            a.box(f"SaddlebagFlap{S}", (0.56, 0.5, 1.14), U(2.07 * s, 7.5, 2.15), C("#5c3518"), role="Accent",
                  shadow=False)
            a.box(f"SaddlebagBuckle{S}", (0.6, 0.18, 0.2), U(2.08 * s, 7.3, 2.15), C("#d4b06a"), role="Accent",
                  shadow=False)
        a.cyl("Bedroll", 3.0, 0.75, U(0, 8.25, 2.1), C("#3d6fb8"), role="Accent")
        for x in (-0.9, 0.9):
            a.cyl(f"BedrollTie{x > 0}", 0.16, 0.8, U(x, 8.25, 2.1), C("#5c3518"), role="Accent", shadow=False)
        # The lasso: a coil of rope hanging from the saddle horn, on the right.
        for k, r in enumerate((0.62, 0.55)):
            for i in range(10):
                ang = 2 * math.pi * i / 10
                p = U(2.32, 7.6 + r * math.sin(ang), -0.75 + r * math.cos(ang) + 0.06 * k)
                a.box(f"Lasso{k}_{i}", (0.18, 0.42, 0.18), p, C("#d9b06a") if i % 2 else C("#b88a45"),
                      rot=(math.degrees(-ang), 0, 0), role="Accent", shadow=False)

    horse(a, dict(
        coat="#9a4f24", light="#c47a44", dark="#7a3a18", muzzle="#c9875a", mane=["#3a1d10", "#56301a"],
        hoof="#3a2a20", iris="#5a3216", blaze=True, socks=("FL", "FR", "BL", "BR"), bridle="#4a2a14",
        tack=dict(blanket="#b8343a", trim="#f2e2c4", saddle="#6b3a1a", stirrup="#8a5a2e", pattern="stripes",
                  dots="#2b4f8f"),
        extra=gear,
    ))
    extras(a, attrs={"WalkSpeed": 12})
    return a


def paint_horse():
    a = Animal("PaintHorse", "Paint Horse", "Epic")
    patch = "#a8592c"

    def bandana(a, hat, head_R):
        # A red bandana with white dots around the neck, its knot point hanging down at the front.
        for k, y in enumerate((8.15, 7.85)):
            a.box(f"Bandana{k}", (2.5 - 0.3 * k, 0.4, 2.2 - 0.3 * k), (0, y, -3.75 - 0.15 * k), C("#e23d3d"),
                  rot=(-38, 0, 0), role="Accent")
        a.wedge("BandanaTip", (1.2, 0.95, 0.35), (0, 7.2, -4.75), C("#e23d3d"), rot=(-12, 0, 180), role="Accent")
        for k, (x, y, z) in enumerate(((-0.5, 7.5, -4.62), (0.4, 7.25, -4.66), (0, 6.95, -4.7))):
            a.box(f"BandanaDot{k}", (0.18, 0.18, 0.08), (x, y, z), WHITE, rot=(-12, 0, 0), **DETAIL)
        # A brown patch over one eye and a brown ear, like a real paint horse.
        a.box("EyePatch", (1.05, 1.3, 0.1), hat(0.75, 0.75, -1.46), C(patch), R=head_R, **DETAIL)

    patches = [(1.95, 5.9, -2.2, 0, 1.2, 1.6), (-1.95, 6.1, -1.6, 0, 1.4, 1.2), (1.95, 5.6, 2.6, 0, 1.6, 2.0),
               (-1.95, 5.8, 2.4, 0, 1.5, 2.4), (0.6, 7.77, 2.75, 1.6, 0, 1.5), (-0.5, 7.77, -2.45, 1.3, 0, 0.7)]
    horse(a, dict(
        coat="#f4f0e8", light="#ffffff", dark="#e2dcd2", leg="#f4f0e8", muzzle="#f2d8c8", mane=["#a8592c", "#f4f0e8"],
        hoof="#6b5a4a", iris="#3f7fbf", patches=patches, patch=patch, ear=patch, nose="#a8592c", lashes=True,
        bridle="#2b8f8f", metal="#d9dde8",
        tack=dict(blanket="#2bb0a8", trim="#ffffff", saddle="#8a5a2e", stirrup="#d9dde8", pattern="diamonds",
                  dots="#e23d3d", conchos=True, metal="#d9dde8"),
        head_extra=bandana, tail_long=1.1,
    ))
    # Sparkles on its hooves while it trots.
    for s, S in SIDES:
        hoof = find(a, f"HoofB{S}")["p"]
        trail(a, f"HoofB{S}", add(hoof, (0, 0.4, 0)), add(hoof, (0, -0.2, 0)), C("#c99bff"), name=f"HoofTrail{S}",
              lifetime=0.25, color2=WHITE, transparency=((0, 0.4), (1, 1)))
    extras(a, attrs={"WalkSpeed": 12})
    return a


def black_stallion():
    a = Animal("BlackStallion", "Black Stallion", "Legendary")
    gold = C("#ffcf3f")

    def crest(a, hat, head_R):
        # A golden star on the brow band, and a red plume between the ears.
        pixel_star(a, "BrowStar", hat(0, 1.4, -0.4), 0.7, gold, R=head_R,
                   kw=dict(material="SmoothPlastic", role="Accent", shadow=False))
        for k, (dx, h) in enumerate(((0, 1.3), (0.22, 1.0), (-0.22, 1.0))):
            a.wedge(f"Plume{k}", (0.3, h, 0.6), hat(dx, 2.6 + h / 2, -0.05), C("#c41f2c"),
                    R=matmul(head_R, angles(-15, 0, dx * 40)), role="Accent")

    horse(a, dict(
        coat="#1d1a24", light="#34303f", dark="#14121a", muzzle="#3a3646", mane=["#0f0d14", "#2a2438"],
        mane_style="flowing", hoof="#2a2a30", iris="#c9962e", brow="#0a080d", nose="#0a080d", feather="#0f0d14",
        shoe="#ffcf3f", cheeks=False, tail_long=1.5, mane_glow="#ffcf3f", k=1.55,
        bridle="#c41f2c", metal="#ffcf3f",
        tack=dict(blanket="#a3162a", trim="#ffcf3f", saddle="#14121a", stirrup="#ffcf3f", horn="#ffcf3f",
                  metal="#ffcf3f", shiny=True, conchos=True, breast=True),
        head_extra=crest,
    ))
    for s, S in SIDES:
        for F in ("F", "B"):
            hoof = find(a, f"Hoof{F}{S}")["p"]
            trail(a, f"Hoof{F}{S}", add(hoof, (0, 0.45, 0)), add(hoof, (0, -0.25, 0)), gold, name=f"HoofTrail{F}{S}",
                  lifetime=0.3, color2=C("#ff7a1a"), transparency=((0, 0.25), (1, 1)))
    fx(a, "Muzzle", emitter("Snort", C("#e8e8f0"), texture=SMOKE_TEXTURE, rate=1.2, lifetime=(0.5, 0.9),
                            speed=(1.5, 3), spread=20, sizes=((0, 0.4), (1, 1.4)), transparency=((0, 0.6), (1, 1)),
                            light=0, emit="Front", drag=2))
    for i in (1, 3, 5):
        fx(a, f"ManeShine{i}", emitter("ManeGlint", gold, texture=SPARKLE_TEXTURE, rate=2, lifetime=(0.6, 1.0),
                                        speed=(0.2, 0.6), sizes=((0, 0.35), (1, 0)),
                                        transparency=((0, 0), (1, 1))))
    extras(a, attrs={"WalkSpeed": 13}, highlight=(gold, gold, 1.0, 0.75))
    return a


def golden_mustang():
    a = Animal("GoldenMustang", "Golden Mustang", "Mythic")
    gold, cream, shine = C("#ffc93c"), C("#fff3c4"), C("#fffbe6")

    def stars(a, U):
        # Lucky stars on the flanks, and four little stars that circle it.
        for s, S in SIDES:
            pixel_star(a, f"FlankStar{S}", U(1.97 * s, 6.0, 2.4), 1.0, shine, R=angles(0, 90, 0))
        with a.bone("Orbit", "Body", U(0, 6.4, 0.4)):
            for i in range(4):
                ang = i * math.pi / 2 + math.pi / 4
                p = U(math.cos(ang) * 4.4, 6.6 + 0.4 * (i % 2), 0.4 + math.sin(ang) * 5.4)
                pixel_star(a, f"OrbitStar{i}", p, 0.9, shine if i % 2 else gold, R=angles(0, -math.degrees(ang), 0))

    def tiara(a, hat, head_R):
        a.box("Tiara", (1.5, 0.22, 0.3), hat(0, 1.55, -0.85), C("#ffe27a"), R=head_R, role="Accent",
              reflectance=0.25)
        a.box("TiaraGem", (0.35, 0.35, 0.18), hat(0, 1.75, -1.0), C("#ff4d6d"), R=matmul(head_R, angles(0, 0, 45)),
              **GLOW)

    horse(a, dict(
        coat="#f2b632", light="#ffd977", dark="#d99a1e", leg="#e8a826", muzzle="#ffe2a0",
        mane=["#fff3c4", "#ffe08a"], mane_style="flowing", hoof="#ffe27a", iris="#e2611a", lashes=True,
        nose="#a8601a", brow="#7a4a10", inner_ear="#ffb0c4", tail_long=1.4, mane_glow="#fffbe6",
        tail_glow="#fffbe6", feather="#fff3c4", hoof_kw=dict(material="Neon", role="Glow", shadow=False),
        bridle="#c41f2c", metal="#ffe27a",
        tack=dict(blanket="#d6243a", trim="#ffe27a", saddle="#fff3e0", stirrup="#ffe27a", horn="#ffe27a",
                  metal="#ffe27a", shiny=True, breast=True, pattern="diamonds", dots="#fffbe6"),
        head_extra=tiara, extra=stars,
    ))
    # Sparkle trails behind every hoof and the tail: it leaves sparkles wherever it runs.
    for s, S in SIDES:
        for F in ("F", "B"):
            hoof = find(a, f"Hoof{F}{S}")["p"]
            trail(a, f"Hoof{F}{S}", add(hoof, (0, 0.5, 0)), add(hoof, (0, -0.25, 0)), shine, name=f"HoofTrail{F}{S}",
                  lifetime=0.45, color2=gold, transparency=((0, 0.1), (1, 1)))
            fx(a, f"Hoof{F}{S}", emitter("HoofSparkles", shine, texture=SPARKLE_TEXTURE, rate=6, lifetime=(0.6, 1.1),
                                         speed=(0.5, 1.5), sizes=((0, 0.45), (1, 0)), transparency=((0, 0), (1, 1)),
                                         color2=gold, accel=(0, 1, 0)))
    tail = find(a, "TailTip")["p"]
    trail(a, "Tail0", add(find(a, "Tail0")["p"], (0, 0.4, 0)), tail, shine, name="TailTrail", lifetime=0.5,
          color2=gold, transparency=((0, 0.3), (1, 1)))
    fx(a, "Body",
       emitter("GoldenAura", shine, texture=SPARKLE_TEXTURE, rate=8, lifetime=(1.2, 2.0), speed=(0.4, 1.2),
               sizes=((0, 0.5), (1, 0)), transparency=((0, 0), (1, 1)), color2=gold, accel=(0, 1.2, 0)),
       light("GoldenLight", gold, brightness=1.4, range_=16, pulse=1.6))
    for i in (1, 3, 5):
        fx(a, f"ManeShine{i}", emitter("ManeSparkles", shine, texture=SPARKLE_TEXTURE, rate=3, lifetime=(0.6, 1.0),
                                        speed=(0.3, 0.8), sizes=((0, 0.4), (1, 0)),
                                        transparency=((0, 0), (1, 1))))
    pulse(a, "TailShine", "ManeShine1", "ManeShine3", "ManeShine5", seconds=1.2)
    extras(a, attrs={"WalkSpeed": 14, "OrbitSpeed": 0.4}, highlight=(gold, cream, 1.0, 0.6))
    return a


ALL = [pony, brown_horse, paint_horse, black_stallion, golden_mustang]
