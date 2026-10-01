#!/usr/bin/env python3
"""Frost Peak area: the whole circular mountain area, built from the Frost Peak kit.

Modelled on the first mountain of the reference picture, turned into a big circle (about 660 studs across):

  * The Mountain in the middle: five rings of snow-capped basalt cliffs, each higher and smaller than the last
    (20, 42, 66, 100 and 135 studs high), with pines on every ring and a faceted snowy peak on top (about 215).
    Waterfalls pour from ring to ring into pools in three places around it.
  * A wooden path with stairs climbs along the cliffs from the entrance bridge to a cave in the mountain, with
    lanterns and fences.
  * A turquoise river runs in a ring around the mountain, with ice floes and rope bridges.
  * The Valley around it: pine forest, a frozen lake, a campfire, a round walking path with lanterns and fences,
    two rivers running out to the rim with rope bridges over them.
  * The Rim: a wall of tall snowy cliffs around the whole circle, with two big waterfalls, and one entrance under
    a stone arch at the south (+Z).

    python3 tools/frost-peak-kit/build_frost_area.py                  -> build/area.json and build/area_world.json
    python3 tools/frost-peak-kit/build_frost_area.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
"""

import copy
import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_frost_kit as K  # noqa: E402
from build_frost_kit import (DETAIL, DIRT, ROCK, ROCK_LIGHT, SNOW, SNOW_SHADE, WATER, WATER_DEEP,  # noqa: E402
                             WATER_LIGHT, WOOD, WOOD_DARK, Asset, boulder, column, make_kit, pine_tree)
from lib import add, angles, apply, cframe, compose, inverse, matmul  # noqa: E402
from build_kit import viewer_parts  # noqa: E402

TIERS = [(150, 20), (118, 42), (88, 66), (62, 100), (40, 135)]   # (edge radius, top height)
RIVER = (160, 188)                                                # inner and outer radius of the ring river
PATH_R = 215
RIM = 292
OUTER = 330
RADIAL_RIVERS = (20.0, 160.0)                                     # degrees; 90 is the entrance (+Z, south)
FALL_CHAINS = (150.0, 230.0, 310.0)
# Extra single falls (ring, angle, width): staggered so the mountain has water everywhere, like the picture.
EXTRA_FALLS = [(0, 60, 12), (0, 120, 10), (0, 190, 14), (0, 270, 11), (0, 350, 12), (0, 20, 9),
               (1, 75, 10), (1, 115, 12), (1, 200, 9), (1, 285, 11), (1, 10, 10),
               (2, 105, 9), (2, 175, 10), (2, 260, 9), (2, 30, 8),
               (3, 95, 8), (3, 200, 8), (3, 40, 7), (4, 130, 7), (4, 280, 7)]
STAIRS = [(0, 90.0), (1, 45.0), (2, 0.0)]                         # (tier climbed from, start angle)
CAVE_ANGLE = 330.0


def polar(r, deg, y=0.0):
    t = math.radians(deg)
    return (r * math.cos(t), y, r * math.sin(t))


def _heading(yaw):
    v = apply(angles(0, yaw, 0), (0, 0, -1))
    return v[0], v[2]


def yaw_facing(deg):
    """Yaw that turns a model's front (-Z) to point outward at this angle."""
    t = math.radians(deg)
    want = (math.cos(t), math.sin(t))
    for cand in (math.degrees(math.atan2(-want[0], -want[1])), math.degrees(math.atan2(want[0], -want[1])),
                 math.degrees(math.atan2(-want[0], want[1])), math.degrees(math.atan2(want[0], want[1]))):
        h = _heading(cand)
        if abs(h[0] - want[0]) < 1e-6 and abs(h[1] - want[1]) < 1e-6:
            return cand
    raise AssertionError("yaw_facing")


def yaw_along(deg):
    """Yaw that lines a model's local X up with the tangent (direction of increasing angle) at this angle."""
    return yaw_facing(deg) + 90.0 if _x_ok(yaw_facing(deg) + 90.0, deg) else yaw_facing(deg) - 90.0


def _x_ok(yaw, deg):
    v = apply(angles(0, yaw, 0), (1, 0, 0))
    t = math.radians(deg)
    return abs(v[0] + math.sin(t)) < 1e-6 and abs(v[2] - math.cos(t)) < 1e-6


def ang_dist(a, b):
    return abs((a - b + 180) % 360 - 180)


class Area:
    """Everything placed in the area: (group, asset, position, yaw, scale, lod)."""

    def __init__(self):
        self.items = []

    def put(self, group, asset, pos, yaw=0.0, k=1.0, lod=False):
        self.items.append((group, asset, pos, yaw, k, lod))


# ---------------------------------------------------------------- pieces ---

def ring_boxes(a, name, r_in, r_out, y, h, color, n, **kw):
    """A flat ring made of n boxes."""
    rm = (r_in + r_out) / 2
    seg = 2 * math.pi * rm / n * 1.06
    for i in range(n):
        deg = 360 * (i + 0.5) / n
        a.box(name, (seg, h, r_out - r_in), polar(rm, deg, y), color, rot=(0, yaw_along(deg), 0), **kw)


def dodecagon(a, name, r, y0, y1, color, **kw):
    """A 12-sided prism (three squares turned 30 degrees apart) from y0 to y1."""
    side = 2 * r * math.cos(math.radians(15))
    for k in range(3):
        a.box(name, (side, y1 - y0, side), (0, (y0 + y1) / 2, 0), color, rot=(0, k * 30, 0), **kw)


def edge_radius(i, deg):
    """The cliff edge of ring i wobbles in and out, so the mountain looks wild instead of like a cake."""
    r = TIERS[i][0]
    t = math.radians(deg)
    return r * (1 + 0.075 * math.sin(3 * t + 1.1 * i) + 0.045 * math.sin(5 * t + 2.3 * i) + 0.025 * math.sin(9 * t))


def min_radius(i):
    return min(edge_radius(i, d) for d in range(0, 360, 2))


def tier(i, rng, gaps):
    top = TIERS[i][1]
    low = TIERS[i - 1][1] if i else 0.0
    a = Asset(f"Tier{i + 1}", "Mountain", "Mountain", f"mountain ring {i + 1}")
    core = min_radius(i) - 3
    a.cyl("Rock", top - low + 0.5, 2 * core, (0, (low + top) / 2 - 0.5, 0), ROCK[1], R=angles(0, 0, 90))
    a.cyl("Snow", 0.8, 2 * core - 1, (0, top - 0.2, 0), SNOW, R=angles(0, 0, 90))
    circ = 2 * math.pi * TIERS[i][0]
    n = int(circ / 5.2)
    for j in range(n):
        deg = 360 * (j + rng.uniform(-0.15, 0.15)) / n
        if any(ang_dist(deg, g) < w for g, w in gaps):
            continue
        edge = edge_radius(i, deg)
        r = edge
        first = True
        # Columns from the edge inwards until they reach the solid core (more rows where the edge bulges out).
        while first or r > core + 2:
            w = rng.uniform(5.0, 6.8)
            h = (top - low) + 1.2 + rng.uniform(-1.5, 4.0 if first else 2.0)
            x, _, z = polar(r - w * 0.3, deg + rng.uniform(-0.4, 0.4))
            yaw = yaw_along(deg) + rng.uniform(-8, 8)
            if first:
                column(a, (x, low - 1, z), w, rng.uniform(5.5, 7.5), h, rng, yaw=yaw, name="Cliff", lite=True)
            else:
                # Inner columns hardly show: one block with a snow top is enough.
                d = rng.uniform(5.5, 7.5)
                a.box("CliffInner", (w, h, d), (x, low - 1 + h / 2, z), rng.choice(ROCK[1:]),
                      rot=(rng.uniform(-3, 3), yaw, rng.uniform(-3, 3)))
                if rng.random() < 0.6:
                    a.box("CliffInnerSnow", (w * 0.92, 0.7, d * 0.92), (x, low - 1 + h + 0.3, z), SNOW,
                          rot=(0, yaw + rng.uniform(-10, 10), 0), collide=False)
            r -= 5.5
            first = False
    return a


def peak(rng):
    a = Asset("Peak", "Mountain", "Peak", "the snowy peak")
    r5, y = TIERS[-1]
    levels = 8
    for j in range(levels):
        f = 1 - j / levels
        s = 66 * f + 6
        hh = 11.5
        yy = y + j * 10
        for k in range(2):
            a.box("PeakRock", (s * (1 - 0.12 * k), hh, s * (0.85 - 0.1 * k)), (rng.uniform(-2, 2), yy + hh / 2, rng.uniform(-2, 2)),
                  rng.choice(ROCK[1:]) if j < 4 else ROCK_LIGHT,
                  rot=(rng.uniform(-4, 4), j * 23 + k * 40, rng.uniform(-4, 4)))
        if j >= 2:
            # Snow on the shoulders, more the higher it gets.
            for k in range(3 if j < 5 else 4):
                ang = rng.uniform(0, 360)
                p = add((0, yy + hh, 0), polar(s * 0.28, ang))
                a.box("PeakSnow", (s * 0.55, 1.6 + j * 0.3, s * 0.4), p, SNOW if k % 2 == 0 else SNOW_SHADE,
                      rot=(rng.uniform(-14, 14), rng.uniform(0, 90), rng.uniform(-14, 14)), collide=False)
    top = y + levels * 10
    a.box("Spire", (7, 14, 6), (0, top + 6, 0), ROCK_LIGHT, rot=(4, 20, -6))
    a.box("SpireSnow", (6.4, 8, 5.4), (0, top + 11, 0), SNOW, rot=(4, 35, -6), collide=False)
    a.box("SpireTip", (3.4, 6, 3), (0.4, top + 16, 0), SNOW, rot=(8, 60, 4), collide=False)
    return a


def big_fall(upper, deg, width, rng, pool=True):
    """A wide waterfall over the cliff of tier `upper`, like the falls in the picture: a turquoise stream on the
    tier's top running out from the cliff behind it, the falling sheet with flowing sparkles and white streaks,
    foam and mist at the foot, and a pool on the tier below."""
    top = TIERS[upper][1]
    low = TIERS[upper - 1][1] if upper else 0.0
    H = top - low + 1.0
    edge = edge_radius(upper, deg) + 1.2
    name = f"Fall{upper}_{int(deg)}"
    a = Asset(name, "Water", "Mountain", "wide waterfall over a cliff ring")
    yaw = yaw_facing(deg)

    def at(out, up, side=0.0):
        """A point `out` studs outward from the cliff edge, `up` above the foot, `side` along the cliff."""
        return add(polar(edge + out, deg, low + up), apply(angles(0, yaw, 0), (side, 0, 0)))

    a.box("FallBack", (width + 1.2, H, 1.0), at(-0.3, H / 2), K.WATER_DEEP, rot=(0, yaw, 0), collide=False,
          shadow=False)
    a.box("Fall", (width, H, 1.0), at(0.4, H / 2), WATER, rot=(0, yaw, 0), collide=False, shadow=False,
          transparency=0.12,
          effects=K.flow_beam(name, "Flow", (0, H / 2, -0.7), (0, -H / 2, -0.7), width, speed=1.8))
    for j in range(int(width / 2.2)):
        x = -width / 2 + 1.1 + j * 2.2 + rng.uniform(-0.4, 0.4)
        hh = H * rng.uniform(0.45, 0.95)
        a.box("Streak", (rng.uniform(0.35, 0.7), hh, 0.2), at(1.0, H - hh / 2 - rng.uniform(0, 2), x),
              K.WATER_LIGHT if j % 2 else K.ICE_LIGHT, rot=(0, yaw, 0), **DETAIL)
    a.box("Lip", (width + 0.8, 1.0, 3.0), at(-0.2, H - 0.2), K.WATER_LIGHT, rot=(-25, yaw, 0), **DETAIL)
    # The stream on top of the tier, from the next cliff inward to the edge.
    if upper + 1 < len(TIERS):
        inner = edge_radius(upper + 1, deg) + 1.0
        L = edge - inner + 1.5
        mid = polar((edge + inner) / 2, deg, top + 0.55)
        a.box("Stream", (width * 0.85, 0.5, L), mid, WATER, rot=(0, yaw, 0), collide=False, shadow=False)
        a.box("StreamDeep", (width * 0.4, 0.52, L), mid, K.WATER_DEEP, rot=(0, yaw, 0), **DETAIL)
        for j in range(int(L / 5)):
            p = polar(inner + 2 + j * 5 + rng.uniform(-1, 1), deg + rng.uniform(-1, 1), top + 0.85)
            a.box("Ripple", (rng.uniform(1.2, 3), 0.1, 0.35), p, K.WATER_LIGHT, rot=(0, yaw + 90, 0), **DETAIL)
    # Foot: foam, mist and a pool.
    for j in range(int(width / 1.6)):
        a.octo("Foam", (rng.uniform(1.6, 2.6), rng.uniform(0.8, 1.4), rng.uniform(1.6, 2.4)),
               at(1.8 + rng.uniform(0, 1.5), 0.5, rng.uniform(-width / 2, width / 2)), SNOW, yaw=rng.uniform(0, 45),
               **DETAIL)
    a.parts[-1]["effects"] = [
        K.emitter("Mist", "#ffffff", texture=K.SMOKE, rate=5, lifetime=(1.5, 3), speed=(1, 3), spread=70,
                  size=((0, 3), (1, 8)), transparency=((0, 0.6), (1, 1)), light_=0.2, accel=(0, 1.2, 0)),
        K.emitter("Spray", "#e8fbff", rate=8, lifetime=(0.6, 1.2), speed=(3, 6), spread=50,
                  size=((0, 0.5), (1, 0)), accel=(0, -8, 0))]
    if pool:
        c = at(width * 0.45, 0.3)
        a.disc("Pool", width * 1.5, 0.5, c, WATER, collide=False, shadow=False)
        a.disc("PoolDeep", width * 0.8, 0.52, add(c, (0, 0.01, 0)), K.WATER_DEEP, **DETAIL)
        for j in range(7):
            ang = j * 360 / 7 + rng.uniform(-15, 15)
            a.box("PoolRock", (rng.uniform(2, 3.5), rng.uniform(1.2, 2), rng.uniform(2, 3)),
                  add(c, polar(width * 0.75, ang, 0.6)), rng.choice(ROCK[1:]),
                  rot=(rng.uniform(-10, 10), rng.uniform(0, 90), rng.uniform(-10, 10)))
            a.box("PoolRockSnow", (2.2, 0.5, 2.0), add(c, polar(width * 0.75, ang, 1.6)), SNOW,
                  rot=(0, rng.uniform(0, 90), 0), **DETAIL)
        for j in range(3):
            a.box("Floe", (rng.uniform(1.5, 3), 0.35, rng.uniform(1.5, 2.5)),
                  add(c, polar(rng.uniform(1, width * 0.5), rng.uniform(0, 360), 0.45)), K.ICE_LIGHT,
                  rot=(0, rng.uniform(0, 90), 0), **DETAIL)
    return a


def stairs(i, start_deg, rng):
    """Wooden stairs that climb along the outside of tier i+1's cliff, from tier i's top to tier i+1's top.
    Returns the angle where they end."""
    base = TIERS[i][1] if i >= 0 else 0.0
    top = TIERS[i + 1][1]
    a = Asset(f"Stairs{i + 1}", "Paths", "Mountain", "wooden stairs up the cliff")
    rad = max(edge_radius(i + 1, start_deg - d) for d in range(0, 30, 2)) + 4.6
    steps = int(top - base)
    tread = 1.55
    dtheta = math.degrees(tread / rad)
    for s in range(steps):
        deg = start_deg - s * dtheta
        hgt = (s + 1) * (top - base) / steps
        a.box("Step", (tread * 1.04, hgt, 6.0), polar(rad, deg, base + hgt / 2), WOOD if s % 2 else K.WOOD_LIGHT,
              rot=(0, yaw_along(deg), 0))
        if s % 5 == 0:
            post = polar(rad + 3.1, deg, base + hgt + 1.5)
            a.box("RailPost", (0.5, 3.0, 0.5), post, WOOD_DARK, **DETAIL)
            if s + 5 < steps:
                nxt_deg = start_deg - (s + 5) * dtheta
                nxt = polar(rad + 3.1, nxt_deg, base + (s + 6) * (top - base) / steps + 3.0)
                a.rod("Rail", add(post, (0, 1.5, 0)), nxt, 0.35, WOOD, octagon=False, **DETAIL)
        if s % 4 == 2:
            a.box("StepSnow", (tread * 0.8, 0.15, rng.uniform(1.5, 3)), polar(rad + rng.uniform(-2, 2), deg,
                                                                              base + hgt + 0.08), SNOW,
                  rot=(0, yaw_along(deg), 0), **DETAIL)
    return a, start_deg - steps * dtheta


def path_arc(name, r, y, d0, d1, width, rng, fences=None):
    """A dirt path along a circle from angle d0 to d1 (degrees), with snow along its edges. `r` can also be a
    function of the angle, for paths that follow a wavy cliff edge."""
    a = Asset(name, "Paths", "Valley", "path")
    rad = r if callable(r) else (lambda deg: r)
    length = abs(math.radians(d1 - d0)) * rad((d0 + d1) / 2)
    n = max(1, int(length / 4))
    for j in range(n):
        deg = d0 + (d1 - d0) * (j + 0.5) / n
        r = rad(deg)
        seg = abs(math.radians(d1 - d0)) * r / n
        a.box("Path", (seg * 1.15, 0.3, width), polar(r, deg, y + 0.15), DIRT, rot=(0, yaw_along(deg), 0),
              collide=False)
        if j % 2 == 0:
            side = rng.choice((-1, 1))
            a.box("PathSnow", (rng.uniform(2, 4), 0.35, 1.2), polar(r + side * width / 2, deg, y + 0.2), SNOW,
                  rot=(0, yaw_along(deg) + rng.uniform(-15, 15), 0), **DETAIL)
    return a


def river_ring(rng):
    a = Asset("RingRiver", "Water", "Valley", "river around the mountain")
    r0, r1 = RIVER
    ring_boxes(a, "Water", r0 + 2, r1 - 2, 0.3, 0.6, WATER, 90, collide=False, shadow=False)
    ring_boxes(a, "WaterDeep", r0 + 9, r1 - 9, 0.32, 0.62, WATER_DEEP, 90, **DETAIL)
    ring_boxes(a, "Bank", r0 - 1, r0 + 2.4, 0.6, 1.2, SNOW_SHADE, 90, collide=False)
    ring_boxes(a, "Bank", r1 - 2.4, r1 + 1, 0.6, 1.2, SNOW_SHADE, 90, collide=False)
    for j in range(40):
        deg = rng.uniform(0, 360)
        a.box("Ripple", (rng.uniform(2, 5), 0.1, 0.35), polar(rng.uniform(r0 + 4, r1 - 4), deg, 0.66), WATER_LIGHT,
              rot=(0, yaw_along(deg) + rng.uniform(-10, 10), 0), **DETAIL)
    return a


def radial_river(deg, rng):
    a = Asset("Stream", "Water", "Valley", "river from the ring river to the rim")
    r0, r1 = RIVER[1] - 2, RIM + 2
    length = r1 - r0
    mid = polar((r0 + r1) / 2, deg)
    yaw = yaw_facing(deg)
    a.box("Water", (16, 0.6, length), add(mid, (0, 0.3, 0)), WATER, rot=(0, yaw, 0), collide=False, shadow=False)
    a.box("WaterDeep", (7, 0.62, length), add(mid, (0, 0.31, 0)), WATER_DEEP, rot=(0, yaw, 0), **DETAIL)
    t = math.radians(deg)
    side_vec = (-math.sin(t), 0, math.cos(t))
    for s in (-1, 1):
        a.box("Bank", (2.4, 1.2, length), add(mid, (s * 9 * side_vec[0], 0.6, s * 9 * side_vec[2])), SNOW_SHADE,
              rot=(0, yaw, 0), collide=False)
        for j in range(6):
            p = add(polar(r0 + 8 + j * (length - 16) / 5, deg), (s * 9.5 * side_vec[0], 0, s * 9.5 * side_vec[2]))
            boulder(a, p, (rng.uniform(1.4, 2.4),) * 3, rng, name="BankRock")
    return a


def rim(rng):
    a = Asset("Rim", "Rim", "Rim", "the cliffs around the area")
    n = int(2 * math.pi * (RIM + 10) / 6.4)
    for j in range(n):
        deg = 360 * j / n
        if ang_dist(deg, 90) < 4.5:
            continue          # the entrance
        tall = 34 + 22 * (0.5 + 0.5 * math.sin(math.radians(deg) * 5 + 1.3)) + rng.uniform(-4, 6)
        x, _, z = polar(RIM + 12, deg)
        column(a, (x, -1, z), rng.uniform(6.2, 8.0), 8, tall, rng, yaw=yaw_along(deg) + rng.uniform(-10, 10),
               name="RimCliff", lite=True)
        if j % 2 == 0 and not any(ang_dist(deg, d) < 3 for d in RADIAL_RIVERS):
            x, _, z = polar(RIM + 1, deg + rng.uniform(-1, 1))
            column(a, (x, -1, z), rng.uniform(5, 6.5), 6, rng.uniform(10, 20), rng,
                   yaw=yaw_along(deg) + rng.uniform(-10, 10), name="RimFoot", lite=True)
    # Ground beyond the rim, so the edge never shows.
    ring_boxes(a, "OuterGround", RIM + 18, OUTER + 40, 8, 18, ROCK[1], 60)
    ring_boxes(a, "OuterSnow", RIM + 18, OUTER + 40, 17.2, 0.6, SNOW, 60, collide=False)
    return a


def scatter_points(rng, count, r0, r1, gap, ok):
    pts = []
    tries = 0
    while len(pts) < count and tries < count * 40:
        tries += 1
        r = math.sqrt(rng.uniform(r0 * r0, r1 * r1))
        deg = rng.uniform(0, 360)
        x, _, z = polar(r, deg)
        if not ok(r, deg):
            continue
        if any((x - px) ** 2 + (z - pz) ** 2 < gap * gap for px, pz in pts):
            continue
        pts.append((x, z))
    return pts


# ----------------------------------------------------------------- build ---

def build():
    rng = random.Random(2026)
    kit = {a.name: a for a in make_kit()}
    area = Area()

    # Pine variants (light versions, so a whole forest stays playable on phones).
    pines = []
    for v, (h, w, tiers) in enumerate(((10, 5, 4), (14, 6.5, 4), (17, 7.5, 5), (22, 9, 5), (28, 9.5, 6))):
        a = Asset(f"Pine{v}", "Trees", "Valley", "snowy pine")
        pine_tree(a, random.Random(100 + v), h, w, tiers, lite=True)
        pines.append(a)

    # Ground.
    g = Asset("Ground", "Ground", "Valley", "snowy ground")
    g.cyl("Ground", 4, OUTER * 2 + 120, (0, -2, 0), SNOW_SHADE, R=angles(0, 0, 90))
    for j in range(80):
        p = polar(math.sqrt(rng.uniform(RIVER[1] ** 2, (RIM - 6) ** 2)), rng.uniform(0, 360), 0.15)
        g.octo("SnowPatch", (rng.uniform(6, 14), 0.3, rng.uniform(6, 14)), p, SNOW, yaw=rng.uniform(0, 45), **DETAIL)
    area.put("Ground", g, (0, 0, 0))

    # The mountain.
    gaps_for = {i: [] for i in range(len(TIERS))}
    for deg in FALL_CHAINS:
        for i in range(len(TIERS)):
            gaps_for[i].append((deg, 3.2))
    for i, deg, w in EXTRA_FALLS:
        gaps_for[i].append((deg, math.degrees(w * 0.45 / TIERS[i][0])))
    end_angles = {}
    for i, start in STAIRS:
        st, end = stairs(i, start, rng)
        end_angles[i] = end
        area.put("Paths", st, (0, 0, 0))
        gaps_for[i + 1].append((end + 1.0, 4.5))
    gaps_for[0].append((90.0, 3.0))
    for i in range(len(TIERS)):
        area.put("Mountain", tier(i, rng, gaps_for[i]), (0, 0, 0))
    area.put("Mountain", peak(rng), (0, 0, 0))
    for deg in FALL_CHAINS:
        for upper in range(len(TIERS)):
            area.put("Water", big_fall(upper, deg, 16 - 2 * upper, rng, pool=upper > 0), (0, 0, 0))
    for i, deg, w in EXTRA_FALLS:
        area.put("Water", big_fall(i, deg, w, rng, pool=i > 0), (0, 0, 0))

    # Paths on the mountain: from the entrance bridge to the first stairs, then along each ring to the next
    # stairs, and on the third ring to the cave.
    area.put("Paths", path_arc("BaseLanding", 155, 0, 90, 90.5, 6, rng), (0, 0, 0))
    for i, start in STAIRS:
        y = TIERS[i + 1][1]

        def ledge_r(deg, j=i + 1):
            # Along the outer edge of the ring's top, but never into the cliff above.
            return max(edge_radius(j, deg) - 6.0, edge_radius(j + 1, deg) + 4.5)

        nxt = STAIRS[i + 1][1] if i + 1 < len(STAIRS) else CAVE_ANGLE - 360 + 6
        area.put("Paths", path_arc(f"Ledge{i + 1}", ledge_r, y, end_angles[i] - 2, nxt + 2, 6, rng), (0, 0, 0))
        for deg in (end_angles[i] - 4, (end_angles[i] + nxt) / 2):
            area.put("Paths", kit["LanternPost"], polar(ledge_r(deg) + 3.5, deg, y), yaw_facing(deg) + 90)
        # A fence along the drop side of the ledge path, like the wooden fence in the picture.
        deg = end_angles[i] - 8
        while deg > nxt + 6:
            area.put("Paths", kit["WoodFence"], polar(ledge_r(deg) + 3.6, deg, y), yaw_along(deg))
            deg -= math.degrees(12.6 / ledge_r(deg))
    cave_r, cave_y = edge_radius(3, CAVE_ANGLE) + 3.5, TIERS[2][1]
    area.put("Decor", kit["CaveEntrance"], polar(cave_r, CAVE_ANGLE, cave_y), yaw_facing(CAVE_ANGLE), 1.35)
    area.put("Decor", kit["Campfire"], polar(TIERS[3][0] + 14, CAVE_ANGLE + 14, cave_y), 0.0, 0.9)

    # The ring river with bridges and ice floes.
    area.put("Water", river_ring(rng), (0, 0, 0))
    for deg in (90.0, 200.0, 290.0):
        area.put("Paths", kit["RopeBridge"], polar(sum(RIVER) / 2, deg), yaw_facing(deg), 1.05)
    for j in range(12):
        deg = rng.uniform(0, 360)
        if min(ang_dist(deg, b) for b in (90, 200, 290)) < 8:
            continue
        area.put("Water", kit["IceFloes"], polar(rng.uniform(RIVER[0] + 6, RIVER[1] - 6), deg, 0.2), rng.uniform(0, 360),
                 rng.uniform(1.0, 1.6))

    # Streams out to the rim, with a waterfall from the rim cliffs at the end of each, and a bridge where the
    # valley path crosses.
    for deg in RADIAL_RIVERS:
        area.put("Water", radial_river(deg, rng), (0, 0, 0))
        area.put("Water", kit["WaterfallTall"], polar(RIM + 3, deg), yaw_facing(deg + 180), 1.7)
        area.put("Paths", kit["RopeBridge"], polar(PATH_R, deg), yaw_facing(deg) + 90, 0.9)

    # The valley path, with fences on the inside and lanterns.
    def on_river(deg, width_deg=4.5):
        return any(ang_dist(deg, d) < width_deg for d in RADIAL_RIVERS)

    segs = []
    d = 0.0
    while d < 360:
        if not on_river(d + 3):
            segs.append(d)
        d += 6
    for d0 in segs:
        area.put("Paths", path_arc("ValleyPath", PATH_R, 0, d0, d0 + 6.2, 7, rng), (0, 0, 0))
    for j, d0 in enumerate(segs):
        if j % 3 == 0 and not on_river(d0 + 3, 8):
            area.put("Paths", kit["WoodFence"], polar(PATH_R - 5.5, d0 + 3), yaw_along(d0 + 3))
        if j % 5 == 1 and not on_river(d0 + 3, 8):
            area.put("Paths", kit["LanternPost"], polar(PATH_R + 5, d0 + 3), yaw_facing(d0 + 3) + 90)
    # Entrance: the arch in the rim, a signpost, lanterns, and the path to the river bridge.
    ep = Asset("EntrancePath", "Paths", "Valley", "path from the entrance to the bridge")
    for j in range(int((RIM + 14 - RIVER[1]) / 6)):
        r = RIVER[1] + 3 + j * 6
        ep.box("Path", (7, 0.3, 6.4), polar(r, 90, 0.15), DIRT, rot=(0, yaw_facing(90), 0), collide=False)
    area.put("Paths", ep, (0, 0, 0))
    area.put("Decor", kit["StoneArch"], polar(RIM + 6, 90), yaw_along(90), 1.4)
    area.put("Decor", kit["SignPost"], polar(RIM - 14, 96), 30.0)
    for s in (-1, 1):
        area.put("Paths", kit["LanternPost"], polar(RIM - 6, 90 + s * 2.6), yaw_facing(90) + 90 * s)

    # The frozen lake, a campfire by the path, mist on the river.
    area.put("Water", kit["FrozenLake"], polar(254, 128), 0.0, 1.3)
    area.put("Decor", kit["Campfire"], polar(PATH_R + 18, 62), 20.0)
    for deg in (40, 140, 250, 330):
        area.put("Decor", kit["MistPatch"], polar(sum(RIVER) / 2, deg, 0.4), rng.uniform(0, 360), 1.6)

    # Forest in the valley.
    def valley_ok(r, deg):
        if abs(r - PATH_R) < 8:
            return False
        if on_river(deg, math.degrees(14 / r)):
            return False
        if ang_dist(deg, 90) < math.degrees(9 / r):
            return False
        x, _, z = polar(r, deg)
        lake = polar(254, 128)
        if (x - lake[0]) ** 2 + (z - lake[2]) ** 2 < 32 ** 2:
            return False
        fire = polar(PATH_R + 18, 62)
        if (x - fire[0]) ** 2 + (z - fire[2]) ** 2 < 10 ** 2:
            return False
        return True

    for x, z in scatter_points(rng, 140, RIVER[1] + 6, RIM - 8, 9.5, valley_ok):
        area.put("Trees", rng.choice(pines), (x, 0, z), rng.uniform(0, 360), rng.uniform(0.85, 1.25), lod=True)
    for x, z in scatter_points(rng, 110, RIVER[1] + 4, RIM - 4, 6, valley_ok):
        item = kit[rng.choice(["Boulder", "BoulderLarge", "RockPile", "SnowDrift", "GrassTufts", "SnowyBush",
                               "Pebbles", "PineSapling"])]
        area.put("Decor", item, (x, 0, z), rng.uniform(0, 360), rng.uniform(0.9, 1.3))
    # Pines and rocks on the mountain rings.
    for i in range(len(TIERS)):
        r_out = max(edge_radius(i, d) for d in range(0, 360, 4)) - 6
        r_in = min_radius(i + 1) + 4 if i + 1 < len(TIERS) else 0
        y = TIERS[i][1]
        if i + 1 >= len(TIERS):
            continue

        def tier_ok(r, deg, i=i):
            # The ring's top runs from the cliff above (plus room for the ledge path) to this ring's own edge.
            if not edge_radius(i + 1, deg) + 9 < r < edge_radius(i, deg) - (13 if 1 <= i <= 3 else 5):
                return False
            if any(ang_dist(deg, f) < 7 for f in FALL_CHAINS):
                return False
            if any(j in (i, i + 1) and ang_dist(deg, f) < math.degrees((w + 6) / max(r, 1)) for j, f, w in EXTRA_FALLS):
                return False
            if i in end_angles and ang_dist(deg, end_angles[i] - 10) < 26:
                return False
            if i == 2 and ang_dist(deg, CAVE_ANGLE) < 16:
                return False
            return True

        count = int(math.pi * (r_out ** 2 - r_in ** 2) / 650)
        for x, z in scatter_points(rng, count, r_in, r_out, 7.0, tier_ok):
            area.put("Trees", rng.choice(pines[:4]), (x, y, z), rng.uniform(0, 360), rng.uniform(0.8, 1.15), lod=True)
        for x, z in scatter_points(rng, count // 3, r_in, r_out, 6, tier_ok):
            area.put("Decor", kit[rng.choice(["SnowDrift", "Boulder", "RockPile"])], (x, y, z), rng.uniform(0, 360))

    area.put("Rim", rim(rng), (0, 0, 0))
    for deg in (0, 72, 144, 216, 288):
        area.put("Decor", kit["SnowfallZone"], polar(150, deg, 40), 0.0, 3.0)
    return area


# ---------------------------------------------------------------- output ---

def remap(effects, suffix, k):
    """Copies a part's effects with unique ids (several copies of one model in one file) and scaled attachments."""
    out = copy.deepcopy(effects)

    def walk(node):
        if "id" in node:
            node["id"] = node["id"] + suffix
        for key, val in node.get("props", {}).items():
            if isinstance(val, dict) and "ref" in val:
                val["ref"] = val["ref"] + suffix
        if node.get("class") == "Attachment" and "CFrame" in node.get("props", {}):
            cf = node["props"]["CFrame"]
            node["props"]["CFrame"] = [cf[0] * k, cf[1] * k, cf[2] * k] + cf[3:]
        for child in node.get("children", []):
            walk(child)
    for e in out:
        walk(e)
    return out


def model_node(asset, pos, yaw, k, uid, lod):
    Ry = angles(0, yaw, 0)
    kids = []
    prim = f"Area.{uid}.1"
    for i, p in enumerate(asset.parts, start=1):
        R = matmul(Ry, p["R"])
        world = add(pos, apply(Ry, tuple(c * k for c in p["p"])))
        props = {
            "Size": [round(v * k, 4) for v in p["size"]], "CFrame": cframe(R, world), "Color": list(p["color"]),
            "Material": p["material"], "Anchored": True, "CanCollide": p["collide"], "CanTouch": p["collide"],
            "CanQuery": p["collide"] or i == 1, "CastShadow": p["shadow"], "TopSurface": "Smooth",
            "BottomSurface": "Smooth",
        }
        if p["transparency"]:
            props["Transparency"] = p["transparency"]
        if p["shape"] == "ball":
            props["Shape"] = "Ball"
        elif p["shape"] == "cylinder":
            props["Shape"] = "Cylinder"
        if i == 1:
            props["PivotOffset"] = cframe(*compose(inverse(R, world), (Ry, pos)))
        kids.append({"class": "WedgePart" if p["shape"] == "wedge" else "Part", "name": p["name"],
                     **({"id": prim} if i == 1 else {}), "props": props,
                     "children": remap(p["effects"], f"#{uid}", k)})
    props = {"PrimaryPart": {"ref": prim}}
    if lod:
        props["LevelOfDetail"] = "StreamingMesh"
    return {"class": "Model", "name": asset.name, "props": props, "children": kids}


def main():
    area = build()
    groups = {}
    for uid, (group, asset, pos, yaw, k, lod) in enumerate(area.items):
        groups.setdefault(group, []).append(model_node(asset, pos, yaw, k, uid, lod or asset.category in
                                                       ("Trees", "Cliffs")))
    total = sum(len(asset.parts) for _, asset, *_ in area.items)
    entrance = {"class": "Part", "name": "EntranceSpawn", "id": "Area.Entrance", "attrs": {
        "Description": "where players arrive: just inside the arch, facing the mountain"}, "props": {
        "Size": [6, 1, 6], "CFrame": cframe(angles(0, yaw_facing(270), 0), polar(RIM - 20, 90, 0.5)), "Anchored": True,
        "CanCollide": False, "CanTouch": False, "CanQuery": False, "Transparency": 1}}
    order = ["Ground", "Mountain", "Rim", "Water", "Paths", "Trees", "Decor"]
    tree = [{"class": "Model", "name": "FrostPeakArea",
             "attrs": {"Diameter": OUTER * 2, "Description": "The Frost Peak mountain area, built from the FrostPeakKit"},
             "props": {"PrimaryPart": {"ref": "Area.Entrance"}},
             "children": [entrance] + [{"class": "Folder", "name": g, "children": groups[g]} for g in order]}]
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    (out / "area.json").write_text(json.dumps(tree))
    for g in order:
        n = sum(len(a.parts) for gg, a, *_ in area.items if gg == g)
        print(f"{g:9} {len(groups[g]):5} models {n:6} parts")
    print(f"total {total} parts")

    parts = viewer_parts([], [(a, pos, yaw, k) for _, a, pos, yaw, k, _ in area.items
                              if a.name not in ("SnowfallZone",)])
    env = {"sky": [[0, "#3f8fef"], [0.55, "#86c2ff"], [1, "#d8efff"]], "fog": ["#d8efff", 500, 1500],
           "sun": {"dir": [-0.45, 1.0, 0.5], "intensity": 2.6}, "hemi": ["#ffffff", "#9fb4d0", 1.5],
           "bloom": [0.45, 0.5, 0.85]}
    shots = {
        "overview": {"camera": {"pos": [120, 260, 560], "target": [0, 60, 0], "fov": 52},
                     "shadow": {"center": [0, 0, 0], "radius": 360}},
        "image": {"camera": {"pos": [70, 75, 300], "target": [-10, 80, -20], "fov": 60},
                  "shadow": {"center": [0, 0, 120], "radius": 260}},
        "entrance": {"camera": {"pos": [6, 12, 318], "target": [0, 40, 100], "fov": 64},
                     "shadow": {"center": [0, 0, 240], "radius": 120}},
        "path": {"camera": {"pos": list(polar(PATH_R + 2, 110, 7)), "target": [0, 60, 0], "fov": 66},
                 "shadow": {"center": list(polar(PATH_R, 110)), "radius": 120}},
        "falls": {"camera": {"pos": list(polar(240, 160, 60)), "target": list(polar(60, 150, 70)), "fov": 58},
                  "shadow": {"center": list(polar(120, 150)), "radius": 160}},
        "cave": {"camera": {"pos": list(polar(130, 340, 95)), "target": list(polar(60, 330, 76)), "fov": 60},
                 "shadow": {"center": list(polar(80, 330)), "radius": 90}},
        "top": {"camera": {"pos": [0, 760, 1], "target": [0, 0, 0], "fov": 52},
                "shadow": {"center": [0, 0, 0], "radius": 360}},
    }
    (out / "area_world.json").write_text(json.dumps({"env": env, "parts": parts, "models": [], "texts": [],
                                                     "sprites": [], "shots": shots}))
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cargo", "run", "--quiet", "--release", "--manifest-path",
                        str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "area.json"), target],
                       check=True)


if __name__ == "__main__":
    main()
