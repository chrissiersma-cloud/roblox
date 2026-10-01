#!/usr/bin/env python3
"""Frost Peak area: the whole circular mountain area, built from the Frost Peak kit.

Modelled on the first mountain of the reference picture, turned into a big circle (about 660 studs across):

  * The Mountain in the middle is one faceted shape (triangles made of wedges, see facets.py): five rings of
    leaning, ridged cliffs with snowy benches between them (tops at 20, 42, 66, 100 and 135 studs), and a jagged
    peak with four ridges up to about 240. Basalt columns stand against the cliffs here and there, pines grow on
    every ring, and wide waterfalls pour from ring to ring into pools.
  * Wooden stairs on posts climb the cliffs from the ground ring by ring, with fenced paths and lanterns between
    them, past a cave to the Aurora Dragon's temple (dragon_temple.py), which sank crooked into the cliff.
  * A turquoise river runs in a ring around the mountain, with ice floes and rope bridges.
  * The Valley around it: pine forest, a frozen lake, a campfire, a round walking path with lanterns and fences,
    two rivers running out to the rim with rope bridges over them.
  * The Rim: a ring of faceted snowy mountains around the whole circle, with basalt columns at their foot, two
    waterfalls where the rivers end, and one entrance pass with a stone arch at the south (+Z).

    python3 tools/frost-peak-kit/build_frost_area.py                  -> build/area.json and build/area_world.json
    python3 tools/frost-peak-kit/build_frost_area.py --rbxm OUT.rbxm  -> also writes the area .rbxm (needs cargo)
                                                     --temple OUT.rbxm -> also writes the temple on its own
"""

import copy
import functools
import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_frost_kit as K  # noqa: E402
import facets as F  # noqa: E402
import dragon_temple  # noqa: E402
from build_frost_kit import (DETAIL, DIRT, ROCK, ROCK_LIGHT, SNOW, SNOW_SHADE, WATER, WATER_DEEP,  # noqa: E402
                             WATER_LIGHT, WOOD, WOOD_DARK, Asset, boulder, make_kit, pine_tree)
from lib import add, angles, apply, cframe, compose, inverse, matmul, scale  # noqa: E402
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
               (2, 105, 9), (2, 175, 10), (2, 30, 8),
               (3, 95, 8), (3, 200, 8), (3, 40, 7), (4, 130, 7), (4, 280, 7)]
STAIRS = [(-1, 101.0), (0, 90.0), (1, 45.0), (2, 50.0)]           # (ring climbed from, -1 = ground; start angle)
CAVE_ANGLE = 330.0
TEMPLE_ANGLE = 268.0                                              # the Aurora Dragon's sunken temple
STEP_RISE, STEP_TREAD = 1.0, 1.7


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
    """Yaw that lines a model's local X up with the tangent (direction of increasing angle) at this angle.
    (With the front turned outward, local X already runs along the circle.)"""
    yaw = yaw_facing(deg)
    v = apply(angles(0, yaw, 0), (1, 0, 0))
    t = math.radians(deg)
    assert abs(v[0] + math.sin(t)) < 1e-6 and abs(v[2] - math.cos(t)) < 1e-6
    return yaw


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


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def stair_span(i):
    """Degrees that the stairs from ring i to ring i+1 cover (they run clockwise from their start angle)."""
    h = TIERS[i + 1][1] - (TIERS[i][1] if i >= 0 else 0.0)
    return math.degrees(h / STEP_RISE * STEP_TREAD / (TIERS[i + 1][0] + 8))


def calm(i, deg):
    """1 where cliff i must be steep and smooth (waterfalls, stairs, the cave), 0 elsewhere."""
    near = 99.0
    for f in FALL_CHAINS:
        near = min(near, ang_dist(deg, f) - 3)
    for j, f, w in EXTRA_FALLS:
        if j == i:
            near = min(near, ang_dist(deg, f) - math.degrees(w * 0.6 / TIERS[i][0]))
    for j, start in STAIRS:
        if j + 1 == i:
            mid = start - stair_span(j) / 2
            near = min(near, ang_dist(deg, mid) - stair_span(j) / 2 - 2)
    if i == 3:
        near = min(near, ang_dist(deg, CAVE_ANGLE) - 7, ang_dist(deg, TEMPLE_ANGLE) - 24)
    if i == 4:
        near = min(near, ang_dist(deg, TEMPLE_ANGLE) - 20)
    return 1.0 - smoothstep(near / 4.0)


def run(i, deg):
    """How far the foot of cliff i sticks out past its top edge: cliffs lean back, more on the ridges."""
    t = math.radians(deg)
    h = TIERS[i][1] - (TIERS[i - 1][1] if i else 0.0)
    wild = h * (0.12 + 0.2 * (0.5 + 0.5 * math.sin(7 * t + 1.3 * i)) * (0.6 + 0.4 * math.sin(3 * t + 0.6)))
    if i >= 3:
        wild *= 1.7               # the high cliffs lean back more, so they flow into the peak
    return 1.6 + (wild - 1.6) * (1 - calm(i, deg))


@functools.lru_cache(maxsize=None)
def edge_radius(i, deg):
    """Top edge of cliff ring i. The bulges line up from ring to ring, so they read as ridges running down one
    mountain instead of a stack of rings."""
    r = TIERS[i][0]
    t = math.radians(deg)
    e = r * (1 + 0.07 * math.sin(3 * t + 0.6) + 0.045 * math.sin(5 * t + 1.9) + 0.02 * math.sin(9 * t + i)
             + 0.015 * math.sin(4 * t + 2 * i))
    if i == 0:
        return min(e, RIVER[0] - 10 - run(0, deg))
    if i == 3:
        # The cliff gives way where the temple sank into it.
        e -= 8.0 * (1 - smoothstep((ang_dist(deg, TEMPLE_ANGLE) - 8) / 16))
    return min(e, edge_radius(i - 1, deg) - run(i, deg) - 10)


def min_radius(i):
    return min(edge_radius(i, d) for d in range(0, 360, 2))


def foot_radius(i, deg):
    return edge_radius(i, deg) + run(i, deg)


def bench_y(i):
    """Walking height on top of ring i (the snow lies a little above the rock)."""
    return TIERS[i][1] + 0.7


def ring_angles(n, rng, jitter=0.3):
    out = [0.0]
    for k in range(1, n):
        out.append((k + rng.uniform(-jitter, jitter)) * 360.0 / n)
    return out


def shade(rng, nu, y, peak=False, cap=False):
    """Colour of one facet from how flat it is: snow on flat facets, rock on steep ones, and streaks between.
    Above the snow line (`cap`) almost everything is snow, with only the steepest crags showing rock."""
    if cap:
        if nu > 0.2 or rng.random() < 0.55:
            return SNOW if rng.random() < 0.75 else SNOW_SHADE
        return rng.choice((ROCK_LIGHT, ROCK[2], K.SNOW_BLUE))
    if nu > 0.8:
        return SNOW if rng.random() < 0.7 else SNOW_SHADE
    if nu > 0.55:
        return rng.choice((SNOW_SHADE, K.SNOW_BLUE, ROCK_LIGHT))
    if peak and nu > 0.3 and rng.random() < 0.45:
        return rng.choice((SNOW_SHADE, K.SNOW_BLUE))          # snow streaks down the peak
    if y > 150 and rng.random() < 0.3:
        return ROCK_LIGHT
    return rng.choice(ROCK[1:]) if rng.random() < 0.8 else ROCK[0]


def snow_line(base, deg):
    """Height of the snow line on the peak: it dips down along the ridges and gullies, so the cap is jagged."""
    t = math.radians(deg)
    return base + 9 * math.sin(3 * t + 0.4) + 5 * math.sin(7 * t + 1.3) + 3 * math.sin(13 * t)


def facet_asset(name, group, rings, rng, peak_from=None, thick=1.4, snow_from=None):
    a = Asset(name, group, "Mountain", "faceted surface")
    for p0, p1, p2 in F.surface(rings):
        n = F.normal_up(p0, p1, p2)
        if n is None:
            continue
        nu = n[1]
        y = (p0[1] + p1[1] + p2[1]) / 3
        deg = math.degrees(math.atan2(p0[2] + p1[2] + p2[2], p0[0] + p1[0] + p2[0])) % 360
        cap = snow_from is not None and y > snow_line(snow_from, deg) + rng.uniform(-3, 3)
        color = shade(rng, nu, y, peak=peak_from is not None and y > peak_from, cap=cap)
        F.tri(a, "Snow" if color in (SNOW, SNOW_SHADE, K.SNOW_BLUE) else "Rock", p0, p1, p2, color, thick=thick)
    return a


def mountain(rng):
    """The mountain as one faceted shape: for every ring a leaning, ridged cliff (foot, a zig-zag middle row
    that gives the basalt-like vertical facets, and the top edge), a rounded snowy lip, a snowy bench that
    drifts up against the next cliff, and above the last ring a tall jagged peak."""
    rings = []
    for i, (r, top) in enumerate(TIERS):
        low = TIERS[i - 1][1] if i else 0.0
        h = top - low
        n = int(2 * math.pi * r / 6.0)
        degs = ring_angles(n, rng)
        foot_y = low - 0.8 if i == 0 else low + 1.4                 # the next cliff's foot is buried in drift
        rings.append([(d, polar(foot_radius(i, d), d, foot_y)) for d in degs])
        for frac, zig in ((0.35, 1.3), (0.72, 1.0)):
            row = []
            for k, d in enumerate(ring_angles(n, rng, 0.15)):
                c = calm(i, d)
                rr = edge_radius(i, d) + run(i, d) * (1 - frac) + (1 - c) * zig * (1 if k % 2 else -1) * rng.uniform(0.6, 1.2)
                row.append((d, polar(rr, d, low + h * frac + (1 - c) * rng.uniform(-1.2, 1.2))))
            rings.append(row)
        rings.append([(d, polar(edge_radius(i, d) + rng.uniform(-0.2, 0.3), d, top + rng.uniform(-0.3, 0.5)))
                      for d in degs])
        rings.append([(d, polar(edge_radius(i, d) - 2.2, d, top + 0.55)) for d in ring_angles(n, rng)])
        if i + 1 < len(TIERS):
            row = []
            for d in ring_angles(max(12, int(n * 0.8)), rng):
                rr = (edge_radius(i, d) - 2.2 + foot_radius(i + 1, d)) / 2
                row.append((d, polar(rr, d, top + 0.6 + rng.uniform(0, 0.5))))
            rings.append(row)
    y4 = TIERS[-1][1]
    rings += peak_rings(lambda d: edge_radius(4, d), y4, rng)
    return facet_asset("Mountain", "Mountain", rings, rng, peak_from=y4 + 10, snow_from=y4 + 30)


def peak_rings(base_r, y0, rng, k=1.0):
    """The peak: rings that shrink fast and rise faster (k scales the height), with jagged heights so the top has
    several crags. base_r(deg) is the radius of the peak's foot at height y0."""
    rings = []
    for f, rise, n in ((0.88, 5, 40), (0.76, 22, 36), (0.63, 41, 30), (0.5, 59, 26), (0.38, 74, 20),
                       (0.26, 86, 14), (0.14, 95, 9)):
        row = []
        for j, d in enumerate(ring_angles(n, rng, 0.25)):
            t = math.radians(d)
            # Four ridges run down from the summit, so the peak has shoulders instead of being a cone.
            ridge = 1 + 0.32 * max(0.0, math.cos(2 * (t - 0.5))) ** 3 + 0.18 * max(0.0, math.cos(2 * t + 1.9)) ** 3
            spike = rng.uniform(-4, 7) * (rise / 95) if j % 2 else rng.uniform(-3, 2)
            row.append((d, polar(base_r(d) * f * ridge * rng.uniform(0.93, 1.07), d, y0 + (rise + spike) * k)))
        rings.append(row)
    rings.append([(0.0, (1.5, y0 + 102 * k, -1.0))])
    return rings


def basalt(i, rng, gaps):
    """Clusters of basalt columns standing against the cliffs here and there, like in the picture."""
    a = Asset(f"Basalt{i + 1}", "Mountain", "Mountain", f"basalt columns on ring {i + 1}")
    low = TIERS[i - 1][1] if i else 0.0
    h = TIERS[i][1] - low
    n = int(2 * math.pi * TIERS[i][0] / 34)
    for j in range(n):
        deg = 360 * (j + rng.uniform(-0.3, 0.3)) / n
        if calm(i, deg) > 0.01 or any(ang_dist(deg, g) < w + 3 for g, w in gaps):
            continue
        for k in range(rng.randint(3, 5)):
            d = deg + (k - 2) * math.degrees(3.4 / TIERS[i][0]) + rng.uniform(-0.3, 0.3)
            w = rng.uniform(2.6, 3.8)
            hh = h * rng.uniform(0.45, 0.85)
            base = low - (0.8 if i == 0 else -1.0)
            x, _, z = polar(foot_radius(i, d) - run(i, d) * (hh / h) * 0.6 - 0.8, d)
            yaw = yaw_along(d) + rng.uniform(-12, 12)
            col = rng.choice(ROCK[1:])
            a.box("Column", (w, hh, w * 0.9), (x, base + hh / 2, z), col, rot=(rng.uniform(-3, 3), yaw, rng.uniform(-3, 3)))
            a.box("ColumnFacet", (w * 0.75, hh * 0.98, w * 0.75), (x, base + hh / 2, z), ROCK[0], rot=(0, yaw + 45, 0), **DETAIL)
            a.wedge("ColumnTop", (w * 0.95, 0.9, w * 0.85), (x, base + hh + 0.45, z), ROCK_LIGHT, rot=(0, yaw + 180 * (k % 2), 0), **DETAIL)
            a.box("ColumnSnow", (w * 0.8, 0.5, w * 0.7), (x, base + hh + 0.55, z), SNOW, rot=(0, yaw + 10, 0), **DETAIL)
    return a


def waterfall(name, H, width, stream, rng, pool=True):
    """A wide waterfall like the falls in the picture, in its own coordinates: the cliff face is at z = 0 with
    the water falling down its front (-Z) from height H to the ground (y = 0). The sheet is split in strands
    with flowing sparkles, there is foam, mist and spray at the foot, a pool with rocks and ice in front, and
    (when `stream` > 0) a turquoise stream that runs `stream` studs back over the top of the cliff."""
    a = Asset(name, "Water", "Mountain", f"waterfall {H:.0f} studs high and {width:.0f} wide")

    def at(out, up, side=0.0):
        return (side, up, -out)

    a.box("FallBack", (width + 1.6, H, 1.2), at(-0.5, H / 2), K.WATER_DEEP, collide=False, shadow=False)
    # Strands of different widths, a little in front of each other, lighter at the top where the water is thin.
    x = -width / 2
    j = 0
    while x < width / 2 - 0.8:
        sw = min(rng.uniform(1.8, 3.6), width / 2 - x)
        hh = H * rng.uniform(0.9, 1.0)
        out = rng.uniform(0.3, 0.9)
        a.box("Fall", (sw, hh, 0.9), at(out, H - hh / 2, x + sw / 2), WATER, collide=False, shadow=False,
              transparency=0.1,
              effects=K.flow_beam(f"{name}{j}", "Flow", (0, hh / 2, -0.6), (0, -hh / 2, -0.6), sw, speed=1.5 + 0.2 * (j % 3)))
        a.box("FallTop", (sw * 0.98, H * 0.22, 0.95), at(out + 0.05, H - H * 0.11, x + sw / 2), WATER_LIGHT, **DETAIL)
        a.box("Streak", (0.35, hh * rng.uniform(0.4, 0.8), 0.2),
              at(out + 0.5, H * rng.uniform(0.35, 0.6), x + sw * rng.uniform(0.25, 0.75)), K.ICE_LIGHT, **DETAIL)
        x += sw
        j += 1
    a.box("Lip", (width + 0.6, 1.2, 3.2), at(-0.6, H - 0.3), WATER_LIGHT, rot=(-28, 0, 0), **DETAIL)
    if stream > 0:
        mid = (0, H - 0.15, stream / 2)
        a.box("Stream", (width * 0.8, 0.5, stream), mid, WATER, collide=False, shadow=False)
        a.box("StreamDeep", (width * 0.35, 0.52, stream), mid, K.WATER_DEEP, **DETAIL)
        for s in (-1, 1):
            a.box("StreamBank", (1.4, 0.9, stream), add(mid, (s * width * 0.42, 0.1, 0)), SNOW, **DETAIL)
        for k in range(int(stream / 4)):
            a.box("Ripple", (rng.uniform(1.2, 2.6), 0.1, 0.35),
                  (rng.uniform(-0.15, 0.15) * width, H + 0.13, stream - 2 - k * 4), WATER_LIGHT, rot=(0, 90, 0), **DETAIL)
    # Foot: round white foam, mist and spray.
    for k in range(int(width / 1.4)):
        a.ball("Foam", rng.uniform(1.8, 3.0), at(1.4 + rng.uniform(0, 1.6), 0.5, rng.uniform(-width / 2, width / 2)),
               SNOW if k % 3 else K.ICE_LIGHT, **DETAIL)
    a.parts[-1]["effects"] = [
        K.emitter("Mist", "#ffffff", texture=K.SMOKE, rate=6, lifetime=(1.5, 3), speed=(1, 3), spread=70,
                  size=((0, 3), (1, 9)), transparency=((0, 0.55), (1, 1)), light_=0.2, accel=(0, 1.2, 0)),
        K.emitter("Spray", "#e8fbff", rate=10, lifetime=(0.6, 1.2), speed=(3, 6), spread=50,
                  size=((0, 0.5), (1, 0)), accel=(0, -8, 0))]
    if pool:
        c = at(width * 0.5 + 1, 0.15)
        a.disc("Pool", width * 1.5, 0.6, c, WATER, collide=False, shadow=False)
        a.disc("PoolDeep", width * 0.8, 0.62, add(c, (0, 0.01, 0)), K.WATER_DEEP, **DETAIL)
        a.disc("PoolRim", width * 1.5 + 2.4, 0.5, add(c, (0, -0.05, 0)), SNOW_SHADE, **DETAIL)
        for k in range(6):
            ang = k * 60 + rng.uniform(-20, 20)
            p = add(c, polar(width * 0.78, ang, 0.5))
            boulder(a, p, (rng.uniform(2, 3.2), rng.uniform(1.4, 2.0), rng.uniform(2, 3)), rng, name="PoolRock")
        for k in range(3):
            a.box("Floe", (rng.uniform(1.5, 3), 0.35, rng.uniform(1.5, 2.5)),
                  add(c, polar(rng.uniform(1, width * 0.5), rng.uniform(0, 360), 0.35)), K.ICE_LIGHT,
                  rot=(0, rng.uniform(0, 90), 0), **DETAIL)
    return a


def big_fall(area, upper, deg, width, rng, pool=True):
    """Puts a waterfall over cliff `upper` at this angle, with its stream running back to the next cliff."""
    top = TIERS[upper][1]
    low = TIERS[upper - 1][1] if upper else 0.0
    base = low - 0.6 if upper == 0 else low + 0.9
    H = top - base + 1.2
    edge = edge_radius(upper, deg) + run(upper, deg) * 0.55 + 0.9
    stream = edge - foot_radius(upper + 1, deg) + 1.0 if upper + 1 < len(TIERS) else 0.0
    a = waterfall(f"Fall{upper}_{int(deg)}", H, width, stream, rng, pool)
    area.put("Water", a, polar(edge, deg, base), yaw_facing(deg))


def stair_flight(a, base, top, at, yaw_at, landing_in, rng, W=4.6):
    """Wooden stairs on posts: open plank steps on two stringers, posts with braces down to the ground, a rope
    railing on the open side, a foot stone and a landing at the top. `at(s, side, y)` gives the world point at
    step s (counted along the run), `side` studs to the open side, at height y; `yaw_at(s)` turns a part's X
    along the run. The landing reaches `landing_in` studs back from the stairs' centre line."""
    steps = int(round((top - base) / STEP_RISE))
    rise = (top - base) / steps
    rail = []
    for s in range(steps):
        y = base + (s + 1) * rise
        yaw = yaw_at(s)
        a.box("Step", (STEP_TREAD * 0.92, 0.45, W), at(s, 0, y - 0.22), WOOD if s % 2 else K.WOOD_LIGHT, rot=(0, yaw, 0))
        if s % 3 == 1:
            a.box("StepSnow", (STEP_TREAD * 0.7, 0.18, rng.uniform(1.2, 2.2)), at(s, 1.2, y + 0.05), SNOW,
                  rot=(0, yaw, 0), **DETAIL)
        for side in (-1, 1):
            if s + 1 < steps:
                a.rod("Stringer", at(s, side * (W / 2 - 0.3), y - 0.75), at(s + 1, side * (W / 2 - 0.3), y + rise - 0.75),
                      0.55, WOOD_DARK, octagon=False)
        if s % 4 == 0:
            post_top = y - 0.8
            if post_top - base > 1.2:
                a.box("Post", (0.7, post_top - base + 0.6, 0.7), at(s, W / 2 - 0.3, (post_top + base - 0.6) / 2), WOOD_DARK)
                a.rod("Brace", at(s, W / 2 - 0.3, base + 0.4), at(s + 3, W / 2 - 0.3, post_top - 0.2), 0.35, WOOD,
                      octagon=False, **DETAIL)
        if s % 3 == 0 or s == steps - 1:
            a.box("RailPost", (0.45, 3.2, 0.45), at(s, W / 2 + 0.1, y + 1.4), WOOD_DARK, **DETAIL)
            a.box("RailCap", (0.65, 0.3, 0.65), at(s, W / 2 + 0.1, y + 3.0), SNOW, **DETAIL)
            rail.append(at(s, W / 2 + 0.1, y + 2.7))
    for p0, p1 in zip(rail, rail[1:]):
        a.rod("Rope", p0, p1, 0.22, K.ROPE, octagon=False, **DETAIL)
        mid = add(scale((add(p0, p1)), 0.5), (0, -1.0, 0))
        a.rod("Rope", add(p0, (0, -1.0, 0)), mid, 0.18, K.ROPE, octagon=False, **DETAIL)
        a.rod("Rope", mid, add(p1, (0, -1.0, 0)), 0.18, K.ROPE, octagon=False, **DETAIL)
    # Landing at the top, reaching back over the cliff edge.
    s = steps - 0.5
    lat = (W / 2 - landing_in) / 2
    a.box("Landing", (STEP_TREAD * 2.4, 0.5, W / 2 + landing_in), at(s, lat, top - 0.25), WOOD, rot=(0, yaw_at(s), 0))
    for side in (-1, 1):
        a.box("LandingBeam", (0.5, 0.6, W / 2 + landing_in), at(s + side, lat, top - 0.75), WOOD_DARK,
              rot=(0, yaw_at(s), 0))
    a.box("FootStone", (STEP_TREAD * 2.2, 0.8, W + 1), at(-1, 0, base + 0.1), ROCK[2], rot=(0, yaw_at(0), 0))
    return steps


def stairs(i, start_deg, rng):
    """Stairs that climb along the foot of cliff i+1 from ring i to ring i+1. Returns the asset and the angle
    where they end."""
    base = bench_y(i) - 0.3 if i >= 0 else 0.0
    top = TIERS[i + 1][1] + 0.5
    a = Asset(f"Stairs{i + 1}", "Paths", "Mountain", "wooden stairs up the cliff")
    dth = math.degrees(STEP_TREAD / (foot_radius(i + 1, start_deg) + 3.4))

    def deg_at(s):
        return start_deg - s * dth

    def at(s, side, y):
        d = deg_at(s)
        return polar(foot_radius(i + 1, d) + 3.4 + side, d, y)

    end_deg = deg_at(int(round((top - base) / STEP_RISE)))
    landing_in = foot_radius(i + 1, end_deg) - edge_radius(i + 1, end_deg) + 5.9
    steps = stair_flight(a, base, top, at, lambda s: yaw_along(deg_at(s)), landing_in, rng)
    return a, deg_at(steps)


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


# The rim: mountains all around the valley. Rows of (radius offset from RIM, base height, extra height).
RIM_ROWS = [(-30, 0.0, 0.0), (-16, 1.0, 2.5), (-5, 3.0, 4.0), (3, 24.0, 14.0), (18, 46.0, 26.0), (42, 74.0, 46.0),
            (76, 66.0, 30.0), (125, 38.0, 14.0), (180, 8.0, 4.0)]


def rim_gap(deg, floor=0.25):
    """0 in the entrance pass, `floor` where the two streams cut into the rim, 1 elsewhere."""
    m = smoothstep((ang_dist(deg, 90) - 1.5) / 10.0)
    for d in RADIAL_RIVERS:
        m = min(m, floor + (1 - floor) * smoothstep((ang_dist(deg, d) - 2.0) / 6.0))
    return m


def rim_height(k, deg, rng=None):
    off, base, extra = RIM_ROWS[k]
    t = math.radians(deg)
    n = 0.5 + 0.5 * math.sin(5 * t + 1.3 + k) * math.cos(3 * t + 0.4 * k)
    y = base + extra * n
    if rng is not None and k >= 4:
        y += rng.uniform(-0.25, 0.35) * extra          # jagged crests
    if k == 0:
        return y
    if k <= 2:
        return y * rim_gap(deg, 0.0)
    gap = rim_gap(deg)
    return y * gap if ang_dist(deg, 90) < 14 else y * (0.55 + 0.45 * gap)


def ground_y(r, deg):
    """Height of the ground in the valley (it rises into the rim mountains near the edge)."""
    for k in range(len(RIM_ROWS) - 1):
        r0, r1 = RIM + RIM_ROWS[k][0], RIM + RIM_ROWS[k + 1][0]
        if r < r0:
            return 0.0
        if r <= r1:
            t = (r - r0) / (r1 - r0)
            return rim_height(k, deg) * (1 - t) + rim_height(k + 1, deg) * t
    return rim_height(len(RIM_ROWS) - 1, deg)


def rim(rng):
    rings = []
    for k, (off, _, _) in enumerate(RIM_ROWS):
        r = RIM + off
        n = 144 if k < 6 else 96 if k < 8 else 72
        row = []
        for j, d in enumerate(ring_angles(n, rng, 0.0 if k < 3 else 0.25)):
            row.append((d, polar(r + (rng.uniform(-2, 2) if k >= 3 else 0), d, rim_height(k, d, rng) - (0.4 if k == 0 else 0))))
        rings.append(row)
    a = facet_asset("RimMountains", "Rim", rings, rng, peak_from=40, thick=1.6)
    # Basalt columns at the foot of the rim cliffs, like on the mountain.
    for j in range(80):
        deg = rng.uniform(0, 360)
        if ang_dist(deg, 90) < 12 or any(ang_dist(deg, d) < 6 for d in RADIAL_RIVERS):
            continue
        for k in range(rng.randint(2, 4)):
            d = deg + (k - 1.5) * 1.0
            r = RIM + 2 + rng.uniform(-1, 2)
            hh = ground_y(r, d) + rng.uniform(-6, 4)
            if hh < 6:
                continue
            w = rng.uniform(3, 4.4)
            x, _, z = polar(r - 3, d)
            yaw = yaw_along(d) + rng.uniform(-12, 12)
            a.box("Column", (w, hh, w * 0.9), (x, hh / 2 - 0.5, z), rng.choice(ROCK[1:]), rot=(rng.uniform(-3, 3), yaw, 0))
            a.wedge("ColumnTop", (w * 0.95, 0.9, w * 0.85), (x, hh, z), ROCK_LIGHT, rot=(0, yaw + 180 * (k % 2), 0), **DETAIL)
            a.box("ColumnSnow", (w * 0.8, 0.5, w * 0.7), (x, hh + 0.1, z), SNOW, rot=(0, yaw + 10, 0), **DETAIL)
    return a


def ground_at(x, z):
    return ground_y(math.hypot(x, z), math.degrees(math.atan2(z, x)) % 360)


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

    # The mountain: one faceted shape, basalt columns on the cliffs, and waterfalls from ring to ring.
    area.put("Mountain", mountain(rng), (0, 0, 0))
    for i in range(len(TIERS)):
        area.put("Mountain", basalt(i, rng, []), (0, 0, 0))
    for deg in FALL_CHAINS:
        for upper in range(len(TIERS)):
            big_fall(area, upper, deg, 16 - 2 * upper, rng, pool=upper > 0)
    for i, deg, w in EXTRA_FALLS:
        big_fall(area, i, deg, w, rng, pool=i > 0)

    # Stairs from the ground up the cliffs, a path along each ring to the next stairs, and on the third ring to
    # the cave.
    end_angles = {}
    for i, start in STAIRS:
        st, end = stairs(i, start, rng)
        end_angles[i] = end
        area.put("Paths", st, (0, 0, 0))
        y0 = bench_y(i) if i >= 0 else 0.0
        area.put("Paths", kit["LanternPost"], polar(foot_radius(i + 1, start + 3) + 7.5, start + 3, y0 - 0.4),
                 yaw_facing(start + 3) + 90)
    area.put("Paths", path_arc("BaseLanding", lambda d: foot_radius(0, d) + 4.5, 0, 88, STAIRS[0][1] + 2, 6, rng),
             (0, 0, 0))
    for k in range(len(STAIRS) - 1):
        i = STAIRS[k][0]
        j = i + 1
        y = bench_y(j) + 0.1

        def ledge_r(deg, j=j):
            # Along the outer edge of the ring's top, but never into the cliff above.
            return max(edge_radius(j, deg) - 6.0, foot_radius(j + 1, deg) + 4.5)

        # On ring 2 the path goes on past the next stairs to the cave.
        nxt = TEMPLE_ANGLE - 360 + 19 if j == 2 else STAIRS[k + 1][1]
        if nxt >= end_angles[i] - 6:
            continue
        area.put("Paths", path_arc(f"Ledge{j}", ledge_r, y, end_angles[i] - 2, nxt + 2, 6, rng), (0, 0, 0))
        area.put("Paths", kit["LanternPost"], polar(ledge_r((end_angles[i] + nxt) / 2) + 3.5,
                                                   (end_angles[i] + nxt) / 2, y - 0.5), yaw_facing((end_angles[i] + nxt) / 2) + 90)
        # A fence along the drop side of the ledge path, like the wooden fence in the picture.
        deg = end_angles[i] - 8
        while deg > nxt + 6:
            area.put("Paths", kit["WoodFence"], polar(ledge_r(deg) + 3.6, deg, y - 0.5), yaw_along(deg))
            deg -= math.degrees(12.6 / ledge_r(deg))
    # The Aurora Dragon's temple, sunk crooked into the cliff of ring 3: its front steps end at the edge of ring 2.
    tpl = dragon_temple.sink(dragon_temple.temple(random.Random(77)))
    area.put("Temple", tpl, polar(edge_radius(2, TEMPLE_ANGLE) - 30.5, TEMPLE_ANGLE, bench_y(2) - 0.7),
             yaw_facing(TEMPLE_ANGLE))
    cave_r, cave_y = foot_radius(3, CAVE_ANGLE) + 2.0, bench_y(2) - 0.6
    area.put("Decor", kit["CaveEntrance"], polar(cave_r, CAVE_ANGLE, cave_y), yaw_facing(CAVE_ANGLE), 1.35)
    fire_deg = CAVE_ANGLE + 12
    area.put("Decor", kit["Campfire"], polar((edge_radius(2, fire_deg) - 2 + foot_radius(3, fire_deg)) / 2, fire_deg,
                                             bench_y(2) - 0.3), 0.0, 0.9)

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
        area.put("Water", kit["WaterfallTall"], polar(RIM - 1, deg, -0.3), yaw_facing(deg + 180),
                 (ground_y(RIM + 3, deg) + 0.8) / 24)
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
    area.put("Decor", kit["SignPost"], polar(RIM - 14, 96, ground_y(RIM - 14, 96)), 30.0)
    for s in (-1, 1):
        area.put("Paths", kit["LanternPost"], polar(RIM - 6, 90 + s * 2.6, ground_y(RIM - 6, 90 + s * 2.6)),
                 yaw_facing(90) + 90 * s)

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
        area.put("Trees", rng.choice(pines), (x, ground_at(x, z) - 0.3, z), rng.uniform(0, 360), rng.uniform(0.85, 1.25),
                 lod=True)
    for x, z in scatter_points(rng, 110, RIVER[1] + 4, RIM - 4, 6, valley_ok):
        item = kit[rng.choice(["Boulder", "BoulderLarge", "RockPile", "SnowDrift", "GrassTufts", "SnowyBush",
                               "Pebbles", "PineSapling"])]
        area.put("Decor", item, (x, ground_at(x, z) - 0.2, z), rng.uniform(0, 360), rng.uniform(0.9, 1.3))
    # Pines and rocks on the mountain rings.
    for i in range(len(TIERS)):
        r_out = max(edge_radius(i, d) for d in range(0, 360, 4)) - 6
        r_in = min_radius(i + 1) + 4 if i + 1 < len(TIERS) else 0
        y = bench_y(i) - 0.4
        if i + 1 >= len(TIERS):
            continue

        def tier_ok(r, deg, i=i):
            # The ring's top runs from the cliff above (plus room for the ledge path) to this ring's own edge.
            if not foot_radius(i + 1, deg) + 4 < r < edge_radius(i, deg) - (13 if 1 <= i <= 3 else 5):
                return False
            if any(ang_dist(deg, f) < 7 for f in FALL_CHAINS):
                return False
            if any(j in (i, i + 1) and ang_dist(deg, f) < math.degrees((w + 6) / max(r, 1)) for j, f, w in EXTRA_FALLS):
                return False
            if i - 1 in end_angles and ang_dist(deg, end_angles[i - 1] - 10) < 26:
                return False
            if i == 2 and (ang_dist(deg, CAVE_ANGLE) < 16 or ang_dist(deg, TEMPLE_ANGLE) < 24):
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
                     **({"id": prim} if i == 1 else {}), **({"attrs": p["attrs"]} if p.get("attrs") else {}),
                     "props": props,
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
    order = ["Ground", "Mountain", "Temple", "Rim", "Water", "Paths", "Trees", "Decor"]
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
           "sun": {"dir": [-0.45, 1.0, 0.5], "intensity": 2.6}, "hemi": ["#ffffff", "#8fa3c4", 1.15],
           "bloom": [0.3, 0.45, 0.9]}
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
        "temple": {"camera": {"pos": list(polar(150, TEMPLE_ANGLE + 8, 88)), "target": list(polar(66, TEMPLE_ANGLE, 76)),
                   "fov": 50}, "shadow": {"center": list(polar(70, TEMPLE_ANGLE)), "radius": 70}},
        "temple_close": {"camera": {"pos": list(polar(112, TEMPLE_ANGLE - 14, 74)),
                                    "target": list(polar(70, TEMPLE_ANGLE, 74)), "fov": 55},
                         "shadow": {"center": list(polar(70, TEMPLE_ANGLE)), "radius": 50}},
        "top": {"camera": {"pos": [0, 760, 1], "target": [0, 0, 0], "fov": 52},
                "shadow": {"center": [0, 0, 0], "radius": 360}},
    }
    (out / "area_world.json").write_text(json.dumps({"env": env, "parts": parts, "models": [], "texts": [],
                                                     "sprites": [], "shots": shots}))
    # The temple on its own (upright, so it can be placed anywhere), with a preview scene.
    tpl = dragon_temple.temple(random.Random(77))
    (out / "temple.json").write_text(json.dumps([model_node(tpl, (0, 0, 0), 0.0, 1.0, "T", False)]))
    ground = [{"n": "Ground", "s": "block", "z": [140, 2, 140], "cf": [0, -1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
               "c": list(SNOW_SHADE), "m": "SmoothPlastic", "t": 0, "r": 0, "st": False, "sh": True}]
    (out / "temple_world.json").write_text(json.dumps({
        "env": env, "parts": ground + viewer_parts([], [(tpl, (0, 0, 0), 0.0, 1.0)]), "models": [], "texts": [],
        "sprites": [], "shots": {
            "front": {"camera": {"pos": [-38, 22, -68], "target": [0, 13, -4], "fov": 50},
                      "shadow": {"center": [0, 0, 0], "radius": 60}},
            "side": {"camera": {"pos": [52, 30, -40], "target": [0, 14, 0], "fov": 50},
                     "shadow": {"center": [0, 0, 0], "radius": 60}}}}))
    if "--temple" in sys.argv:
        target = sys.argv[sys.argv.index("--temple") + 1]
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cargo", "run", "--quiet", "--release", "--manifest-path",
                        str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "temple.json"), target],
                       check=True)
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cargo", "run", "--quiet", "--release", "--manifest-path",
                        str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out / "area.json"), target],
                       check=True)


if __name__ == "__main__":
    main()
