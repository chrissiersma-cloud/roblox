"""The Aurora Dragon's temple: an old eastern-style dragon temple that sank crooked into the side of the mountain.

Stone platforms, teal lacquered pillars with gold bands and brackets, two curved faceted roofs with upturned
eaves and golden dragon finials, a round moon gate that glows with the dragon's aurora colours, coiled dragon
guardian statues, stone lanterns, an altar inside where the dragon rests, and aurora crystals growing out of the
cracks. It is a ruin: one pillar broke and fell across the steps, a boulder from the mountain crashed through
the lower roof, a guardian lost its head, a lantern toppled, and snow has drifted over everything.

temple(rng) builds it upright in local coordinates (front = -Z, ground = y 0). sink(asset) tilts it back into
the mountain and lowers it, the way it is placed in the Frost Peak area.
"""

import math

import build_frost_kit as K
import facets as F
from build_frost_kit import DETAIL, GLOW, SNOW, SNOW_SHADE, C, boulder, emitter, light
from lib import add, aim, angles, apply, matmul, scale, sub

AURORA = ["#5effb0", "#3ff0d0", "#3fd6ff", "#5fa0ff", "#8a7bff", "#b45cff", "#ff6bd6"]

STONE, STONE_DARK, STONE_LIGHT = C("#9aa1b5"), C("#666d84"), C("#c6cbd8")
LACQUER, LACQUER_DARK = C("#1d6a73"), C("#14484f")
GOLD, GOLD_DARK = C("#f0c75a"), C("#b88c2c")
ROOF, ROOF_DARK = C("#33425f"), C("#252f47")
JADE, JADE_DARK = C("#7cc4b0"), C("#4f9483")

PT = 4.2                       # height of the top of the platform
W, D = 36.0, 26.0              # the hall: x from -18 to 18, z from -9 to 17
FRONT, BACK = -9.0, 17.0
COLS_Z = -14.0                 # the porch columns
COLS_X = (-17.0, -11.0, -5.5, 5.5, 11.0, 17.0)
COL_H = 12.5
HOLE = ((13.0, -11.0), 7.5)    # where the boulder broke through the lower roof (x, z), radius


def aurora(t):
    t = max(0.0, min(1.0, t))
    x = t * (len(AURORA) - 1)
    i = min(int(x), len(AURORA) - 2)
    c0, c1 = C(AURORA[i]), C(AURORA[i + 1])
    f = x - i
    return tuple(p + (q - p) * f for p, q in zip(c0, c1))


def hexstr(c):
    return "#" + "".join(f"{int(round(v * 255)):02x}" for v in c)


# ------------------------------------------------------------------ pieces ---

def snow_on(a, name, size, pos, rng, yaw=0.0):
    """A soft layer of snow on a flat top, with a smaller mound on it."""
    w, t, d = size
    a.box(name, (w, t, d), add(pos, (0, t / 2, 0)), SNOW, rot=(0, yaw, 0), **DETAIL)
    a.box(name + "Mound", (w * 0.6, t * 0.8, d * 0.6), add(pos, (rng.uniform(-0.15, 0.15) * w, t * 1.2, 0)),
          SNOW_SHADE if rng.random() < 0.3 else SNOW, rot=(0, yaw + rng.uniform(10, 30), 0), **DETAIL)


def icicles(a, start, end, y, rng, every=1.6, out=(0, 0, 0)):
    n = max(1, int(math.dist(start, end) / every))
    for k in range(n):
        if rng.random() < 0.35:
            continue
        p = add(add(start, scale(sub(end, start), (k + 0.5) / n)), out)
        h = rng.uniform(0.7, 2.0)
        a.wedge("Icicle", (0.35, h, 0.3), (p[0], y - h / 2, p[2]), K.ICE, rot=(180, rng.uniform(0, 180), 0), **DETAIL)


def crystals(a, base, rng, n=5, h=6.0, t=0.5, glow=True, tilt=22):
    """A cluster of aurora crystals growing out of a crack."""
    for k in range(n):
        hh = h * rng.uniform(0.45, 1.0)
        w = rng.uniform(0.7, 1.4) * h / 6
        yaw = rng.uniform(0, 90)
        R = angles(rng.uniform(-tilt, tilt), yaw, rng.uniform(-tilt, tilt))
        p = add(base, apply(R, (0, hh / 2, 0)))
        col = aurora(t + rng.uniform(-0.12, 0.12))
        if glow and k % 2 == 0:
            a.box("Crystal", (w, hh, w), p, col, R=R, material="Neon", collide=False, shadow=False, transparency=0.15)
        else:
            a.box("Crystal", (w, hh, w), p, col, R=R, collide=False)
        tip = add(base, apply(R, (0, hh + w * 0.45, 0)))
        a.box("CrystalTip", (w * 0.7, w * 0.7, w * 0.7), tip, aurora(t + 0.1), R=matmul(R, angles(45, 0, 45)), **DETAIL)
    if glow:
        a.parts[-1]["effects"] = [light(hexstr(aurora(t)), 1.4, 14),
                                  emitter("Glimmer", hexstr(aurora(t)), rate=2, lifetime=(1.5, 2.5), speed=(0.3, 0.8),
                                          size=((0, 0.4), (1, 0)))]


def pillar(a, x, z, rng, broken=False):
    """A lacquered pillar on a stone plinth with gold bands and a stack of brackets that holds the beam."""
    a.box("Plinth", (3.6, 1.0, 3.6), (x, PT + 0.5, z), STONE_LIGHT)
    a.box("PlinthTop", (3.0, 0.5, 3.0), (x, PT + 1.25, z), STONE, rot=(0, 45, 0), **DETAIL)
    h = 5.2 if broken else COL_H - 1.5
    a.octo("Pillar", (2.3, h, 2.3), (x, PT + 1.5 + h / 2, z), LACQUER)
    for y in ((PT + 2.1,) if broken else (PT + 2.1, PT + COL_H - 1.0)):
        a.octo("PillarBand", (2.6, 0.5, 2.6), (x, y, z), GOLD, **DETAIL)
    if broken:
        # Jagged break with snow in it.
        for k, yaw in enumerate((0, 90, 180)):
            a.wedge("PillarBreak", (2.0, rng.uniform(0.8, 1.8), 1.0), (x, PT + 1.5 + h + 0.5, z + (k - 1) * 0.6),
                    LACQUER_DARK, rot=(0, yaw, 0), **DETAIL)
        snow_on(a, "PillarSnow", (1.8, 0.4, 1.8), (x, PT + 1.5 + h - 0.1, z), rng)
        return
    top = PT + COL_H
    a.box("Bracket", (3.0, 0.7, 3.0), (x, top - 0.15, z), GOLD_DARK)
    a.box("BracketArm", (5.2, 0.6, 1.2), (x, top + 0.45, z), LACQUER_DARK, **DETAIL)
    a.box("BracketArm", (1.2, 0.6, 5.2), (x, top + 0.45, z), LACQUER_DARK, **DETAIL)
    for s in (-1, 1):
        a.box("BracketCap", (1.0, 0.5, 1.0), (x + s * 2.2, top + 0.95, z), GOLD, **DETAIL)
        a.box("BracketCap", (1.0, 0.5, 1.0), (x, top + 0.95, z + s * 2.2), GOLD, **DETAIL)


def fallen_pillar(a, rng):
    """The broken top of the pillar at x=11, lying across the steps."""
    p0 = (9.0, PT + 0.9, -17.5)
    p1 = (2.0, 2.0, -25.5)
    a.rod("FallenPillar", p0, p1, 2.3, LACQUER)
    mid = scale(add(p0, p1), 0.5)
    for f in (0.15, 0.85):
        a.rod("FallenBand", add(p0, scale(sub(p1, p0), f - 0.03)), add(p0, scale(sub(p1, p0), f + 0.03)), 2.6, GOLD,
              **DETAIL)
    a.box("FallenSnow", (math.dist(p0, p1) * 0.7, 0.4, 1.4), add(mid, (0, 1.25, 0)), SNOW, R=aim(sub(p1, p0)), **DETAIL)
    a.box("FallenBracket", (3.0, 0.7, 3.0), add(p1, (-1.2, -0.6, -1.4)), GOLD_DARK, rot=(25, 30, 60))


def rect_ring(w, d, y, lift, per_side, rng=None, sag=0.0):
    """Closed ring of points round a rectangle, sorted by angle from +X; corners lifted (upturned eaves) and the
    middle of each side sagging a little, like a curved temple roof."""
    pts = []
    corners = [(w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2), (-w / 2, -d / 2)]
    for k in range(4):
        x0, z0 = corners[k]
        x1, z1 = corners[(k + 1) % 4]
        n = per_side
        for j in range(n):
            u = j / n
            x, z = x0 + (x1 - x0) * u, z0 + (z1 - z0) * u
            c = abs(2 * u - 1)                       # 1 at the corners, 0 in the middle
            yy = y + lift * c ** 4 - sag * (1 - c ** 2)
            pts.append((x, yy, z))
    out = sorted(((math.degrees(math.atan2(p[2], p[0])) % 360, p) for p in pts), key=lambda t: t[0])
    # The rings must all start at angle 0: put the middle of the +X side there.
    if out[0][0] > 1e-6:
        out.insert(0, (0.0, (w / 2, y - sag, 0.0)))
    return out


def roof(a, name, rings, tile_below, rng, hole=None):
    """A faceted roof: tiles low down, snow higher up. `hole` = ((x, z), r) leaves a broken hole."""
    for p0, p1, p2 in F.surface(rings):
        cen = scale(add(add(p0, p1), p2), 1 / 3)
        if hole and math.hypot(cen[0] - hole[0][0], cen[2] - hole[0][1]) < hole[1]:
            continue
        if cen[1] < tile_below or rng.random() < 0.12:
            color = ROOF if rng.random() < 0.65 else ROOF_DARK
            nm = f"{name}Tiles"
        else:
            color = SNOW if rng.random() < 0.75 else SNOW_SHADE
            nm = f"{name}Snow"
        F.tri(a, nm, p0, p1, p2, color, thick=0.8)
    eave = [p for _, p in rings[0]]
    for p, q in zip(eave, eave[1:] + eave[:1]):
        if hole and min(math.hypot(v[0] - hole[0][0], v[2] - hole[0][1]) for v in (p, q)) < hole[1] - 1:
            continue
        a.rod(f"{name}Trim", add(p, (0, -0.3, 0)), add(q, (0, -0.3, 0)), 0.5, GOLD, octagon=False, **DETAIL)
        icicles(a, p, q, p[1] - 0.6, rng, every=2.2)
    # Hip ridges from the eave corners up to the top ring's corners, in gold.
    cz = sum(p[2] for p in eave) / len(eave)
    w0 = max(p[0] for p in eave)
    d0 = max(p[2] - cz for p in eave)
    top = [p for _, p in rings[-1]]
    w1 = max(p[0] for p in top)
    d1 = max(p[2] - cz for p in top)
    ytop = max(p[1] for p in top)
    for sx in (-1, 1):
        for sz in (-1, 1):
            c0 = next(p for p in eave if abs(p[0] - sx * w0) < 1e-6 and abs(p[2] - cz - sz * d0) < 1e-6)
            c1 = (sx * w1, ytop, cz + sz * d1)
            if hole and math.hypot(c0[0] - hole[0][0], c0[2] - hole[0][1]) < hole[1]:
                a.rod(f"{name}Hip", c1, add(c1, scale(sub(c0, c1), 0.45)), 0.7, GOLD_DARK, octagon=False)
                continue
            a.rod(f"{name}Hip", c0, c1, 0.7, GOLD_DARK, octagon=False)
            # Golden dragon finial curling up from the corner, with an aurora pearl.
            out = (sx * 0.8, 0, sz * 0.8)
            f0 = add(c0, (0, 0.3, 0))
            f1 = add(f0, add(out, (0, 1.4, 0)))
            f2 = add(f1, add(scale(out, 0.6), (0, 1.2, 0)))
            f3 = add(f2, add(scale(out, -0.5), (0, 0.8, 0)))
            a.rod(f"{name}Finial", f0, f1, 0.6, GOLD, octagon=False, **DETAIL)
            a.rod(f"{name}Finial", f1, f2, 0.5, GOLD, octagon=False, **DETAIL)
            a.rod(f"{name}Finial", f2, f3, 0.4, GOLD, octagon=False, **DETAIL)
            a.ball(f"{name}Pearl", 0.8, add(f3, (0, 0.3, 0)), aurora(0.3 + 0.2 * (sx + 1) + 0.1 * (sz + 1)), **GLOW)
            # A little bell under the corner.
            a.rod(f"{name}BellCord", add(c0, (0, -0.4, 0)), add(c0, (0, -1.6, 0)), 0.12, GOLD_DARK, octagon=False,
                  **DETAIL)
            a.octo(f"{name}Bell", (0.8, 0.9, 0.8), add(c0, (0, -2.0, 0)), GOLD, **DETAIL)
    a.box(f"{name}Ridge", (2 * w1 + 2.0, 1.0, max(1.4, 2 * d1 + 0.6)), (0, ytop + 0.4, cz), ROOF_DARK)
    a.box(f"{name}RidgeTrim", (2 * w1 + 2.4, 0.4, max(1.0, 2 * d1 + 0.2)), (0, ytop + 1.05, cz), GOLD, **DETAIL)
    a.box(f"{name}RidgeSnow", (2 * w1 + 1.0, 0.4, max(1.2, 2 * d1)), (0, ytop + 1.4, cz), SNOW, **DETAIL)
    return ytop + 1.0


def guardian(a, x, z, rng, headless=False):
    """A coiled stone dragon on a pedestal, with golden antlers and glowing aurora eyes."""
    a.box("Pedestal", (5.0, 3.0, 5.0), (x, 1.5, z), STONE_DARK)
    a.box("PedestalTop", (5.6, 0.6, 5.6), (x, 3.3, z), STONE_LIGHT)
    a.box("PedestalPanel", (3.6, 1.8, 0.2), (x, 1.6, z - 2.55), JADE_DARK, **DETAIL)
    prev = None
    for k in range(20):
        ang = math.radians(k * 38)
        r = 1.9 - k * 0.045
        p = (x + r * math.cos(ang), 4.2 + k * 0.36, z + r * math.sin(ang))
        if prev:
            a.rod("Coil", prev, p, 1.35 - k * 0.025, JADE if k % 2 else JADE_DARK, octagon=False)
            if k % 2 == 0:
                d = sub(p, prev)
                a.wedge("CoilFin", (0.2, 0.9, 1.0), add(scale(add(p, prev), 0.5), (0, 0.8, 0)), aurora(k / 20),
                        rot=(0, math.degrees(math.atan2(d[0], d[2])), 0), **DETAIL)
        prev = p
    neck = add(prev, (0, 1.6, -0.6))
    a.rod("Neck", prev, neck, 1.1, JADE)
    head = add(neck, (0, 0.6, -1.0))
    if headless:
        a.box("NeckBreak", (1.2, 0.5, 1.2), add(neck, (0, 0.3, 0)), JADE_DARK, rot=(20, 30, 10), **DETAIL)
        snow_on(a, "NeckSnow", (1.0, 0.3, 1.0), add(neck, (0, 0.5, 0)), rng)
        # The head lies in the snow next to the pedestal.
        head = (x - 3.6, 0.7, z - 2.2)
        tilt = angles(0, 50, 75)
    else:
        tilt = angles(0, 0, 0)

    def H(v):
        return add(head, apply(tilt, v))

    a.box("Head", (1.8, 1.4, 2.0), H((0, 0, 0)), JADE, R=tilt)
    a.box("Snout", (1.3, 0.9, 1.5), H((0, -0.2, -1.5)), JADE_DARK, R=tilt)
    a.box("Brow", (2.0, 0.4, 0.6), H((0, 0.75, -0.6)), JADE_DARK, R=tilt, **DETAIL)
    for s in (-1, 1):
        a.box("Eye", (0.35, 0.3, 0.2), H((s * 0.6, 0.35, -1.0)), aurora(0.25), R=tilt, **GLOW)
        a.rod("Antler", H((s * 0.5, 0.7, 0.3)), H((s * 1.1, 2.0, 0.9)), 0.3, GOLD, octagon=False, **DETAIL)
        a.rod("Antler", H((s * 1.1, 2.0, 0.9)), H((s * 1.0, 2.9, 1.6)), 0.25, GOLD, octagon=False, **DETAIL)
        a.rod("AntlerTine", H((s * 1.0, 1.7, 0.75)), H((s * 1.6, 2.2, 0.3)), 0.2, GOLD, octagon=False, **DETAIL)
        a.rod("Whisker", H((s * 0.55, -0.45, -2.2)), H((s * 1.7, -1.3, -2.6)), 0.12, GOLD, octagon=False, **DETAIL)
    a.ball("Pearl", 1.0, H((0, -0.6, -2.5)) if not headless else (x, 3.9, z - 2.0), aurora(0.55), **GLOW)
    snow_on(a, "PedestalSnow", (4.6, 0.4, 4.0), (x + 0.3, 3.6, z - 0.3), rng)


def stone_lantern(a, pos, rng, glow_t, toppled=False):
    """A stone lantern (base, post, firebox with an aurora flame, pointed roof with snow)."""
    R = angles(0, rng.uniform(0, 30), 82) if toppled else angles(0, rng.uniform(-6, 6), 0)
    base = add(pos, (0, 1.2, 0)) if toppled else pos

    def P(v):
        return add(base, apply(R, v))

    a.box("LanternBase", (2.6, 0.8, 2.6), P((0, 0.4, 0)), STONE_DARK, R=R)
    a.box("LanternPost", (1.0, 3.2, 1.0), P((0, 2.4, 0)), STONE, R=R)
    a.box("LanternShelf", (2.4, 0.5, 2.4), P((0, 4.2, 0)), STONE_LIGHT, R=R)
    for s in (-1, 1):
        a.box("LanternFrame", (0.4, 1.8, 2.0), P((s * 1.0, 5.35, 0)), STONE, R=R, **DETAIL)
    flame = a.box("LanternFlame", (1.1, 1.2, 1.1), P((0, 5.3, 0)), aurora(glow_t), R=R, **GLOW)
    if not toppled:
        flame["effects"] = [light(hexstr(aurora(glow_t)), 1.6, 16)]
    for k in range(4):
        Rk = matmul(R, angles(0, 90 * k, 0))
        a.wedge("LanternRoof", (3.2, 1.2, 1.6), add(base, apply(Rk, (0, 6.85, -0.8))), STONE_DARK, R=Rk)
    a.box("LanternKnob", (0.6, 0.8, 0.6), P((0, 7.8, 0)), STONE_LIGHT, R=R, **DETAIL)
    a.box("LanternSnow", (2.2, 0.35, 2.2), P((0, 7.5, 0)), SNOW, R=matmul(R, angles(0, 45, 0)), **DETAIL)


def moon_gate(a, gc):
    """The round doorway: a gold ring with stone corners, full of shimmering aurora light. gc = its centre."""
    rgate = 5.6
    n = 22
    for k in range(n):
        t0 = 2 * math.pi * k / n
        p = add(gc, (rgate * math.cos(t0), rgate * math.sin(t0), 0))
        a.box("GateRing", (2 * math.pi * rgate / n * 1.12, 1.2, 1.9), p, GOLD if k % 2 else GOLD_DARK,
              rot=(0, 0, math.degrees(t0) + 90))
    for sx in (-1, 1):
        for sy in (-1, 1):
            # Fill the corners between the square opening and the round ring with a turned block.
            a.box("GateCorner", (2.6, 2.6, 1.3), add(gc, (sx * 5.5, sy * 5.5, 0)), STONE, rot=(0, 0, 45))
    for k, (r, t, tr) in enumerate(((5.0, 0.15, 0.35), (3.9, 0.4, 0.3), (2.7, 0.65, 0.25), (1.4, 0.95, 0.15))):
        disc = a.cyl("Portal", 0.2, 2 * r, add(gc, (0, 0, -0.1 * k)), aurora(t), R=angles(0, 90, 0), material="Neon",
                     collide=False, shadow=False, transparency=tr)
    disc["effects"] = [
        light(hexstr(aurora(0.5)), 2.0, 26),
        emitter("Aurora", hexstr(aurora(0.2)), color2=hexstr(aurora(0.85)), rate=10, lifetime=(1.5, 3), speed=(0.5, 1.5),
                spread=40, size=((0, 0.8), (1, 0)), emit="Right")]
    a.box("GateSign", (6.0, 1.6, 0.3), add(gc, (0, 7.2, -0.9)), LACQUER_DARK, **DETAIL)
    a.box("GateSignGlyph", (4.6, 0.7, 0.1), add(gc, (0, 7.2, -1.05)), GOLD, **DETAIL)


def altar(a, c, rng):
    """The dragon's altar: a round dais with a glowing rune ring, the DragonSpawn spot, and a crystal heart."""
    x, y, z = c
    a.disc("Altar", 12, 1.2, (x, y + 0.6, z), STONE_LIGHT)
    a.disc("AltarRunes", 10.4, 0.2, (x, y + 1.25, z), aurora(0.5), material="Neon", collide=False, shadow=False,
           transparency=0.3)
    a.disc("AltarCenter", 7.0, 0.3, (x, y + 1.35, z), STONE, **DETAIL)
    spawn = a.box("DragonSpawn", (6, 1, 6), (x, y + 2.0, z), STONE, collide=False, shadow=False, transparency=1)
    spawn["attrs"] = {"Description": "where the Aurora Dragon rests"}
    crystals(a, (x, y + 0.5, z + 6.5), rng, n=7, h=9.0, t=0.6, tilt=18)


# ------------------------------------------------------------------ temple ---

def temple(rng):
    a = K.Asset("DragonTemple", "Temple", "Mountain", "ruined temple of the Aurora Dragon")

    # Platform: three stone tiers with darker edges, some blocks missing at the broken front corner.
    for k, (w, d, y0, y1) in enumerate(((46, 40, 0, 1.6), (42, 36, 1.6, 3.0), (38, 32, 3.0, PT))):
        zc = (FRONT + BACK) / 2 - 1.5
        a.box("Platform", (w, y1 - y0, d), (0, (y0 + y1) / 2, zc), STONE if k != 1 else STONE_DARK)
        a.box("PlatformLip", (w + 0.4, 0.35, d + 0.4), (0, y1 - 0.15, zc), STONE_LIGHT, **DETAIL)
        for j in range(int(w / 3)):
            if rng.random() < 0.3:
                x = -w / 2 + 1.5 + j * 3
                a.box("PlatformCrack", (0.25, (y1 - y0) * 0.8, 0.12), (x, (y0 + y1) / 2, zc - d / 2 - 0.25), STONE_DARK,
                      **DETAIL)
    for j in range(7):
        boulder(a, (rng.uniform(14, 22), rng.uniform(0.5, 1.5), rng.uniform(-22, -16)),
                (rng.uniform(1.2, 2.4), rng.uniform(0.9, 1.6), rng.uniform(1.2, 2.2)), rng, name="Rubble")

    # Front stairs with dragon balustrades.
    steps = 5
    for k in range(1, steps + 1):
        top = PT - k * PT / (steps + 1)
        z = -17.0 - (k - 0.5) * 1.9
        a.box("Step", (12, top, 1.9), (0, top / 2, z), STONE_LIGHT if k % 2 else STONE)
        if k % 2 == 0:
            snow_on(a, "StepSnow", (rng.uniform(3, 6), 0.25, 1.2), (rng.uniform(-3, 3), top, z + 0.2), rng)
    for s in (-1, 1):
        p0, p1 = (s * 6.7, PT + 1.6, -16.6), (s * 6.7, 1.6, -27.0)
        a.rod("Balustrade", p0, p1, 1.0, STONE_LIGHT, octagon=False)
        for f in (0.0, 0.5, 1.0):
            q = add(p0, scale(sub(p1, p0), f))
            a.box("BalusterPost", (1.4, q[1], 1.4), (q[0], q[1] / 2, q[2]), STONE)
        a.box("BalustradeHead", (1.4, 1.2, 1.8), add(p1, (0, 0.6, -0.8)), JADE)
        a.ball("BalustradePearl", 0.7, add(p1, (0, 0.6, -2.0)), aurora(0.3), **GLOW)

    # Porch pillars and the beam they carry (broken where the pillar fell).
    for x in COLS_X:
        pillar(a, x, COLS_Z, rng, broken=(x == 11.0))
    fallen_pillar(a, rng)
    beam_y = PT + COL_H + 1.6
    a.box("Beam", (20.5, 1.4, 1.6), (-8.25, beam_y, COLS_Z), LACQUER_DARK)
    a.box("BeamTrim", (20.7, 0.35, 1.8), (-8.25, beam_y - 0.6, COLS_Z), GOLD, **DETAIL)
    a.box("Beam", (6.5, 1.4, 1.6), (15.0, beam_y - 0.4, COLS_Z), LACQUER_DARK, rot=(0, 0, -8))
    a.box("BeamBroken", (5.0, 1.4, 1.6), (6.2, beam_y - 2.6, COLS_Z - 0.3), LACQUER_DARK, rot=(12, 8, 28))
    for x in (-15.0, -9.0, -3.0):
        a.box("BeamPanel", (4.0, 0.9, 0.2), (x, beam_y, COLS_Z - 0.85), aurora(0.2 + 0.1 * (x + 15) / 6), **DETAIL)
    a.box("PorchBeam", (1.6, 1.4, -COLS_Z + FRONT + 3), (-17.0, beam_y, (COLS_Z + FRONT) / 2), LACQUER_DARK)

    # The hall: stone walls with a lacquered top beam and bracket blocks under the eaves.
    wall_h = 13.0
    for x0, x1 in ((-18, -6.5), (6.5, 18)):
        a.box("FrontWall", (x1 - x0, wall_h, 1.4), ((x0 + x1) / 2, PT + wall_h / 2, FRONT), STONE)
    a.box("GateHeader", (13.0, wall_h - 12.5, 1.4), (0, PT + 12.5 + (wall_h - 12.5) / 2, FRONT), STONE)
    for s in (-1, 1):
        a.box("SideWall", (1.4, wall_h, BACK - FRONT), (s * 18, PT + wall_h / 2, (FRONT + BACK) / 2), STONE)
        # Lattice window glowing faintly.
        a.box("WindowGlow", (0.2, 5.0, 6.0), (s * 18.75, PT + 7.0, 2.0), aurora(0.45), material="Neon", collide=False,
              shadow=False, transparency=0.35)
        for j in range(5):
            a.box("Lattice", (0.3, 5.2, 0.3), (s * 18.85, PT + 7.0, -1.0 + j * 1.5), LACQUER_DARK, **DETAIL)
        for j in range(4):
            a.box("Lattice", (0.3, 0.3, 6.2), (s * 18.85, PT + 5.0 + j * 1.3, 2.0), LACQUER_DARK, **DETAIL)
    a.box("BackWall", (37.4, wall_h, 1.4), (0, PT + wall_h / 2, BACK), STONE)
    a.box("WallBeam", (39, 1.2, 1.8), (0, PT + wall_h + 0.6, FRONT), LACQUER_DARK)
    a.box("WallBeam", (39, 1.2, 1.8), (0, PT + wall_h + 0.6, BACK), LACQUER_DARK)
    for s in (-1, 1):
        a.box("WallBeam", (1.8, 1.2, BACK - FRONT + 1.8), (s * 18.5, PT + wall_h + 0.6, (FRONT + BACK) / 2), LACQUER_DARK)
    for j in range(10):
        x = -18 + j * 4
        a.box("EaveBracket", (1.2, 1.4, 1.2), (x, PT + wall_h + 1.9, FRONT - 0.4), GOLD_DARK, **DETAIL)
    for j in range(int(wall_h)):
        if rng.random() < 0.25:
            a.box("WallCrack", (0.25, rng.uniform(1.5, 3.5), 0.12), (rng.uniform(-17, 17), PT + rng.uniform(2, 11), FRONT - 0.72),
                  STONE_DARK, rot=(0, 0, rng.uniform(-25, 25)), **DETAIL)

    moon_gate(a, (0, PT + 6.4, FRONT))
    altar(a, (0, PT, 7.0), rng)

    # Lower roof (with the hole) and the upper storey with its own roof.
    lower = [rect_ring(54, 46, PT + 15.0, 3.4, 6), rect_ring(46, 38, PT + 16.6, 1.8, 5),
             rect_ring(36, 28, PT + 19.4, 0.6, 4), rect_ring(26, 18, PT + 22.0, 0.0, 3)]
    roof(a, "LowerRoof", lower, PT + 18.0, rng, hole=HOLE)
    up_y = PT + 21.0
    a.box("UpperStorey", (24, 8.0, 16), (0, up_y + 4.0, (FRONT + BACK) / 2 - 1.5), STONE_LIGHT)
    for s in (-1, 1):
        for j in range(4):
            a.box("UpperPillar", (1.2, 8.0, 1.2), (s * (3 + j * 3), up_y + 4.0, (FRONT + BACK) / 2 - 9.6), LACQUER,
                  **DETAIL)
    a.box("UpperGlow", (20, 4.0, 0.2), (0, up_y + 4.5, (FRONT + BACK) / 2 - 9.55), aurora(0.7), material="Neon",
          collide=False, shadow=False, transparency=0.35)
    a.box("UpperBeam", (25, 1.0, 17), (0, up_y + 8.4, (FRONT + BACK) / 2 - 1.5), LACQUER_DARK)
    upper = [rect_ring(34, 26, up_y + 9.6, 2.8, 5), rect_ring(26, 18, up_y + 11.4, 1.2, 4),
             rect_ring(17, 9, up_y + 14.2, 0.2, 3), rect_ring(11, 2.0, up_y + 16.2, 0.0, 2)]
    for ring in upper:
        for k, (deg, p) in enumerate(ring):
            ring[k] = (deg, (p[0], p[1], p[2] + (FRONT + BACK) / 2 - 1.5))
    top = roof(a, "UpperRoof", upper, up_y + 13.0, rng)
    # The aurora pearl on the ridge, held by two golden dragons.
    zc = (FRONT + BACK) / 2 - 1.5
    pearl = a.ball("RidgePearl", 2.4, (0, top + 2.0, zc), aurora(0.55), **GLOW)
    pearl["effects"] = [light(hexstr(aurora(0.55)), 1.8, 30),
                        emitter("PearlGlow", hexstr(aurora(0.4)), color2=hexstr(aurora(0.8)), rate=4, lifetime=(1, 2),
                                speed=(0.2, 0.6), size=((0, 1.2), (1, 0)))]
    for s in (-1, 1):
        prev = (s * 6.0, top + 0.4, zc)
        for k in range(5):
            ang = k * 0.7
            p = (s * (5.6 - k * 0.9), top + 0.9 + math.sin(ang) * 1.6, zc + math.cos(ang) * 0.4)
            a.rod("RidgeDragon", prev, p, 0.8 - k * 0.08, GOLD, octagon=False, **DETAIL)
            prev = p
        a.box("RidgeDragonHead", (1.2, 1.0, 1.4), add(prev, (-s * 0.4, 0.3, 0)), GOLD, **DETAIL)

    # The boulder that broke the lower roof, with broken rafters and tiles around the hole.
    hx, hz = HOLE[0]
    boulder(a, (hx + 0.5, PT + 14.5, hz + 1.0), (7.0, 6.0, 6.5), rng, name="FallenBoulder")
    for k in range(5):
        ang = rng.uniform(0, 2 * math.pi)
        p0 = (hx + math.cos(ang) * HOLE[1], PT + 16.5, hz + math.sin(ang) * HOLE[1])
        p1 = (hx + math.cos(ang) * (HOLE[1] - 3.5), PT + 14.5 + rng.uniform(-1, 1), hz + math.sin(ang) * (HOLE[1] - 3.5))
        a.rod("BrokenRafter", p0, p1, 0.6, LACQUER_DARK, octagon=False)
    for k in range(8):
        a.box("RoofTileChunk", (rng.uniform(1.2, 2.4), 0.5, rng.uniform(1.0, 2.0)),
              (hx + rng.uniform(-6, 6), rng.uniform(0.3, 1.0), hz - 10 + rng.uniform(-3, 3)), ROOF,
              rot=(rng.uniform(-30, 30), rng.uniform(0, 90), rng.uniform(-30, 30)), **DETAIL)

    # Guardians, lanterns and crystals outside.
    guardian(a, -12.0, -27.0, rng)
    guardian(a, 12.0, -27.0, rng, headless=True)
    stone_lantern(a, (-21.0, 0.0, -24.0), rng, 0.15)
    stone_lantern(a, (21.0, 0.0, -21.0), rng, 0.5, toppled=True)
    stone_lantern(a, (-13.0, 0.0, -31.5), rng, 0.85)
    crystals(a, (-20.5, PT - 1.6, -17.5), rng, n=6, h=7.0, t=0.2)
    crystals(a, (19.5, PT, 4.0), rng, n=5, h=8.0, t=0.75)
    crystals(a, (-9.0, PT + 22.2, -8.0), rng, n=4, h=5.0, t=0.45)
    crystals(a, (16.0, 0.0, -30.0), rng, n=4, h=4.5, t=0.95)

    # Snow drifted against the walls and over the platform.
    for x, z, w, d in ((-14, -11, 7, 3), (8, -11.5, 6, 3), (-19.5, 4, 3, 10), (19.5, -2, 3, 8), (0, -16.4, 22, 2.4),
                       (-16, -19, 8, 3), (17, -18, 5, 3)):
        y = PT if abs(z) < 16 else 1.6
        a.box("Drift", (w, 1.0, d), (x, y + 0.3, z), SNOW, rot=(rng.uniform(-6, 6), rng.uniform(-8, 8), 0), **DETAIL)
        a.box("DriftTop", (w * 0.7, 0.9, d * 0.6), (x, y + 0.9, z), SNOW_SHADE if rng.random() < 0.3 else SNOW,
              rot=(0, rng.uniform(-15, 15), 0), **DETAIL)
    icicles(a, (-19, 0, FRONT - 0.9), (19, 0, FRONT - 0.9), PT + wall_h, rng)

    # The mountain slid down over its left side and back: the temple is half buried.
    landslide(a, (-26.0, 0.0, -6.0), 13.0, 17.0, rng)
    landslide(a, (27.0, 0.0, 0.0), 10.0, 13.0, rng, name="LandslideRight")
    for k in range(4):
        boulder(a, (rng.uniform(-22, -12), PT + 17 + rng.uniform(0, 2), rng.uniform(-14, -4)),
                (rng.uniform(2.2, 3.6), rng.uniform(1.8, 2.6), rng.uniform(2.2, 3.4)), rng, name="RoofRock")
    return a


def landslide(a, center, radius, height, rng, name="Landslide"):
    """A faceted heap of rock and snow that slid off the mountain over part of the temple."""
    cx, cy, cz = center
    rings = []
    for f, h, n in ((1.0, -1.0, 16), (0.78, 0.4, 14), (0.52, 0.72, 11), (0.27, 0.92, 7)):
        row = []
        for k in range(n):
            d = 360.0 * (k + (rng.uniform(-0.25, 0.25) if k else 0)) / n
            r = radius * f * rng.uniform(0.85, 1.12)
            y = cy + (h * height if h > 0 else h) + (rng.uniform(-0.08, 0.08) * height if h > 0 else 0)
            row.append((d, (cx + r * math.cos(math.radians(d)), y, cz + r * math.sin(math.radians(d)))))
        rings.append(row)
    rings.append([(0.0, (cx + rng.uniform(-1, 1), cy + height, cz + rng.uniform(-1, 1)))])
    for p0, p1, p2 in F.surface(rings):
        n = F.normal_up(p0, p1, p2)
        if n is None:
            continue
        if n[1] > 0.72 or rng.random() < 0.25:
            color = SNOW if rng.random() < 0.7 else SNOW_SHADE
        else:
            color = rng.choice(K.ROCK[1:])
        F.tri(a, name, p0, p1, p2, color, thick=1.4)
    for k in range(6):
        ang = rng.uniform(0, 2 * math.pi)
        r = radius * rng.uniform(0.7, 1.05)
        boulder(a, (cx + r * math.cos(ang), cy + rng.uniform(0.2, 1.2), cz + r * math.sin(ang)),
                (rng.uniform(1.6, 3.2), rng.uniform(1.2, 2.4), rng.uniform(1.6, 3.0)), rng, name=f"{name}Rock")


def shift(a, d):
    """Move every part of an asset by d (used to cut single pieces out of the temple for the decal pack)."""
    for p in a.parts:
        p["p"] = add(p["p"], d)
    return a


def sink(a, pitch=9.0, roll=7.0, down=6.5):
    """Tilt the temple back into the mountain (its back, +Z, goes down) and lower it into the snow."""
    R = angles(pitch, 0, roll)
    for p in a.parts:
        p["p"] = add(apply(R, p["p"]), (0, -down, 0))
        p["R"] = matmul(R, p["R"])
    return a
