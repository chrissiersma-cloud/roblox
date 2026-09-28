"""Shared toolkit for the blocky Create a Zoo animals with classic Roblox studs painted in their texture.

Every animal has its own small script (stud_deer.py, stud_fox.py, stud_owl.py, ...) that describes its
shape and colors and then calls `build(animal)`. Run one of those:
    python3 tools/blender/stud_fox.py [out_dir]             (default out_dir: models/stud-animals)
Needs: pip install bpy numpy pillow scipy                    (scipy is only used for the setup script)

For an animal with id <Id>, build() writes <Id>.blend, <Id>.glb, <Id>Studs.png, <Id>Studs_Golden.png and
<Id>.rig.json to out_dir, updates texture_bands.json and SetupZooAnimals.lua (which sets up every animal in
the folder) and draws previews/stud_<id>_views.png.

How an animal is made:
  1. Every part (body, legs, wings, ...) is built from chunky blocks with bevelled edges (block, bar,
     wedge), like parts built in Studio: a body block, a head block, a snout, ears, a tail. Big cartoon
     eyes (cartoon_eye) sit on the flat faces. Every face is exactly flat.
  2. Every face gets one flat color (brown, cream, ...) from where it is and which way it faces.
  3. Every face gets its own spot in the texture, all at the same scale, so every stud has the same size.
     Square studs sit in a grid centered on each face, rows running level; only studs that fit completely
     are painted, so bevels and thin faces stay plain.
  4. Faces with the same color are packed together, so every color has its own band in the texture
     (recolor a band to make a mutation, see the animal's GOLDEN colors).
The older helpers (ring, loft, leg, eyes) build smooth lofts from rows of rings; the blocks use them too.

Blender axes: +Z up, the animal faces -Y (the Front view), +X is its left side. 1 Blender unit = 1 stud.
"""

import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001  (bpy must come first)
import numpy as np
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import setup_script  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "models" / "stud-animals"
STUD = 0.4            # distance between studs in studs (a Roblox part has one stud per stud)
STUD_SIZE = 0.6       # the side of a (square) stud compared to that distance
MARGIN = 0.04         # studs keep at least this far (in studs) from the edges of a face
TEX = 1024            # texture size in pixels
PAD = 3               # extra pixels around every face in the texture, against color bleeding

X, Y, Z = np.eye(3)


class Animal:
    """What build() needs to know about an animal.
    palette, golden: {color key: "#rrggbb"}; the order is the order of the bands in the texture.
    no_studs: color keys painted flat (eyes, nose). parts: function returning the Parts: first the Body,
    then the parts that turn around their origin (legs, wings).
    close: (point, distance) for the close-up picture of the head.
    glow: {part name: "#rrggbb"}: parts that glow (Neon in Roblox, made by the setup script).
    shine: {part name: reflectance}: shiny metal parts (gold chains); they keep their texture.
    effects: particle effects for the setup script, see effect(). light: (part name, "#rrggbb", brightness, range)
    for a PointLight. wrap: lay the studs out in strips around round parts (for smooth, detailed animals)."""

    def __init__(self, id, rarity, palette, golden, parts, close, no_studs=("nose", "eye", "eyewhite", "glint"),
                 display=None, glow=None, shine=None, effects=(), light=None, wrap=False):
        self.wrap = wrap                                # studs wrap around round shapes (see make_islands)
        self.id, self.display, self.rarity = id, display or id, rarity
        self.palette, self.golden, self.no_studs = palette, golden, set(no_studs)
        self.parts, self.close = parts, close
        self.glow, self.shine, self.effects, self.light = glow or {}, shine or {}, list(effects), light


def effect(name, part, kind, color, color2=None, rate=5, size=(0.4, 0.0), lifetime=(0.6, 1.2), speed=(0.5, 1.5),
           spread=180, accel=(0, 0, 0), transparency=0.2, light_emission=1, at=None):
    """A particle effect for the setup script. kind: "Sparkles", "Fire" or "Smoke" (Roblox's own particle
    pictures). size: (at the start, at the end) in studs; accel: Roblox directions (y is up).
    part: the MeshPart (or "RootPart") it belongs to. It comes out of the whole part, or out of one spot when at is
    "bottom", "top" or "center" (of that part's box), like sparks from a hoof."""
    e = {"name": name, "part": part, "kind": kind, "color": rgb(color), "color2": rgb(color2 or color),
         "rate": rate, "size": list(size), "lifetime": list(lifetime), "speed": list(speed), "spread": spread,
         "accel": list(accel), "transparency": transparency, "lightEmission": light_emission}
    if at:
        e["spot"] = at
    return e


def rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


# ------------------------------------------------------------------ shapes ----

def unit(v):
    return v / np.linalg.norm(v)


def newell(pts):
    """Normal of a polygon (length = twice its area)."""
    n = np.zeros(3)
    for p, q in zip(pts, pts[1:] + pts[:1]):
        n += np.cross(p, q)
    return n


class Part:
    """One Blender object: vertices, flat faces and a color per face. `origin` becomes the object origin.
    parent: the part it is attached to (default: the Body), like a cuff that moves with its arm."""

    def __init__(self, name, origin=(0, 0, 0), parent=None):
        self.name, self.origin, self.parent = name, np.array(origin, float), parent
        self.verts, self.faces, self.colors = [], [], []
        self.bands, self.band_size = {}, {}           # side faces of lofts: face -> (band, place around the ring)

    def vert(self, p):
        self.verts.append(np.array(p, float))
        return len(self.verts) - 1

    def face(self, idx, inside, paint):
        """Adds a face turned away from the point `inside`. A face that is not flat becomes two triangles.
        paint: a color key, or a function (center, normal) -> color key. Returns how many faces it added."""
        pts = [self.verts[i] for i in idx]
        n = newell(pts)
        if np.dot(n, np.mean(pts, 0) - inside) < 0:
            idx, pts, n = idx[::-1], pts[::-1], -n
        if len(idx) == 4 and np.abs(np.dot(np.array(pts) - pts[0], unit(n))).max() > 1e-5:
            self.face(idx[:3], inside, paint)
            self.face([idx[0], idx[2], idx[3]], inside, paint)
            return 2
        color = paint(np.mean(pts, 0), unit(n)) if callable(paint) else paint
        self.faces.append(list(idx))
        self.colors.append(color)
        return 1


def ring(center, a, b, w, h, c, cb=None, segs=1):
    """Box outline with cut corners around `center`, in the plane of the directions a (width) and b (height).
    c: corner size on top, cb: at the bottom. segs: straight pieces per corner (1 = a 45 degree corner, more
    makes the corner round). Every corner piece points the same way whatever its size, so two rings with the
    same segs always join with flat faces."""
    cb = c if cb is None else cb
    x, y = w / 2, h / 2
    if segs == 1:
        corners = [(x, -y + cb), (x, y - c), (x - c, y), (-x + c, y), (-x, y - c), (-x, -y + cb), (-x + cb, -y),
                   (x - cb, -y)]
    else:
        corners = [(x, -y + cb)]
        for (cx, cy), r, start in (((x - c, y - c), c, 0), ((-x + c, y - c), c, 90), ((-x + cb, -y + cb), cb, 180),
                                   ((x - cb, -y + cb), cb, 270)):
            for k in range(segs + 1):
                t = math.radians(start + 90 * k / segs)
                corners.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        corners = corners[:-1]                          # the last point is the first one again
    center, a, b = (np.asarray(v, float) for v in (center, a, b))
    return [center + a * u + b * v for u, v in corners]


def square(center, a, b, w, h):
    center, a, b = (np.asarray(v, float) for v in (center, a, b))
    return [center + a * u + b * v for u, v in ((w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2), (-w / 2, -h / 2))]


def loft(part, rings, paint, caps=(True, True), tip=None):
    """Joins the rings with flat faces; caps close the first and last ring, tip ends in a point instead."""
    ids = [[part.vert(p) for p in r] for r in rings]
    centers = [np.mean(r, 0) for r in rings]
    n = len(rings[0])
    for i in range(len(rings) - 1):
        inside = (centers[i] + centers[i + 1]) / 2
        band = (ids[i][0], ids[i + 1][0])               # one band of faces all around, between two rings
        part.band_size[band] = n
        for j in range(n):
            k = (j + 1) % n
            if part.face([ids[i][j], ids[i][k], ids[i + 1][k], ids[i + 1][j]], inside, paint) == 1:
                part.bands[len(part.faces) - 1] = (band, j)
    if caps[0]:
        after = centers[1] if len(rings) > 1 else np.asarray(tip, float)
        part.face(ids[0], centers[0] + (after - centers[0]) * 0.01, paint)
    if tip is not None:
        t = part.vert(tip)
        for j in range(n):
            part.face([ids[-1][j], ids[-1][(j + 1) % n], t], centers[-1], paint)
    elif caps[1]:
        part.face(ids[-1], centers[-1] + (centers[-2] - centers[-1]) * 0.01, paint)


def slab(part, center, normal, w, h, depth, paint, corner=0.0, segs=1):
    """A thin box lying on a surface (eyes, nose): its front is `depth` above the surface at `center`.
    corner > 0 cuts its corners off, so it looks round (rounder with more segs)."""
    n = unit(np.asarray(normal, float))
    up = Z - np.dot(Z, n) * n
    up = unit(up) if np.linalg.norm(up) > 1e-3 else unit(-Y - np.dot(-Y, n) * n)
    side = np.cross(up, n)
    center = np.asarray(center, float)
    shape = ((lambda c: ring(c, side, up, w, h, corner, segs=segs)) if corner
             else (lambda c: square(c, side, up, w, h)))
    loft(part, [shape(center - n * 0.06), shape(center + n * depth)], paint)


def hit(part, origin, direction, faces=None):
    """Where a straight line from origin along direction first hits the part: (point, outward normal there).
    Handy for putting small things (eyes, teeth, a chain) exactly on a surface. faces: only look at these."""
    o, d = np.asarray(origin, float), unit(np.asarray(direction, float))
    best = None
    for fi in faces if faces is not None else range(len(part.faces)):
        pts = [part.verts[i] for i in part.faces[fi]]
        for k in range(1, len(pts) - 1):
            a, e1, e2 = pts[0], pts[k] - pts[0], pts[k + 1] - pts[0]
            p = np.cross(d, e2)
            det = np.dot(e1, p)
            if abs(det) < 1e-12:
                continue
            s = o - a
            u = np.dot(s, p) / det
            q = np.cross(s, e1)
            v = np.dot(d, q) / det
            t = np.dot(e2, q) / det
            if 0 <= u <= 1 and v >= 0 and u + v <= 1 and t > 1e-6 and (best is None or t < best[0]):
                best = (t, unit(newell(pts)))
    if best is None:
        raise ValueError(f"the line from {tuple(o)} does not hit {part.name}")
    return o + d * best[0], best[1]


def tube(part, points, sizes, paint, tip=None):
    """A square stick through the points (lightning bolts, whiskers): one straight piece per stretch, a little
    longer so the pieces overlap at the bends. sizes: thickness at every point. tip: end in a point there."""
    pts = [np.asarray(p, float) for p in points] + ([np.asarray(tip, float)] if tip is not None else [])
    last = len(pts) - 2
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        d = unit(q - p)
        a = unit(np.cross(d, Z)) if abs(d[2]) < 0.95 else X
        b = np.cross(a, d)
        start = square(p - (d * sizes[i] / 2 if i else 0), a, b, sizes[i], sizes[i])
        if tip is not None and i == last:
            loft(part, [start], paint, caps=(True, False), tip=q)       # the point, along its own stretch
        else:
            end = q + (d * sizes[i + 1] / 2 if i < last else 0)
            loft(part, [start, square(end, a, b, sizes[i + 1], sizes[i + 1])], paint)


def diamond(part, center, width, height, paint):
    """A gem: two pyramids back to back (floating orbs, crystals)."""
    center = np.asarray(center, float)
    band = square(center, unit(X + Y), unit(Y - X), width, width)
    for tip in (center + Z * height / 2, center - Z * height / 2):
        loft(part, [band], paint, caps=(False, False), tip=tip)


def turn(rings, pivot, axis, degrees):
    """Rings (lists of points) turned around the line through pivot along axis."""
    k, t = unit(np.asarray(axis, float)), math.radians(degrees)
    pivot = np.asarray(pivot, float)

    def one(p):
        v = np.asarray(p, float) - pivot
        return pivot + v * math.cos(t) + np.cross(k, v) * math.sin(t) + k * np.dot(k, v) * (1 - math.cos(t))
    return [[one(p) for p in r] for r in rings]


def scaled(parts, k):
    """Makes every part k times bigger (seen from the point on the ground under the middle of the animal)."""
    for part in parts:
        part.verts = [v * k for v in part.verts]
        part.origin = part.origin * k
    return parts


def centered(part):
    """Puts the origin of a part in the middle of its box (for parts that do not turn, like glowing bits)."""
    co = np.array(part.verts)
    part.origin = (co.min(0) + co.max(0)) / 2
    return part


def mirror(pts):
    return [np.asarray(p, float) * (-1, 1, 1) for p in pts]


def sides(rings, tip=None):
    """The left version (as given) and the mirrored right version of rings (and a tip)."""
    yield rings, tip
    yield [mirror(r) for r in rings], None if tip is None else mirror([tip])[0]


def plane_point(p0, n, y, z):
    """Point with the given y and z on the plane through p0 with normal n."""
    x = p0[0] - (n[1] * (y - p0[1]) + n[2] * (z - p0[2])) / n[0]
    return np.array([x, y, z])


def eyes(part, ring_a, ring_b, y, z, w=0.22, h=0.26, rim=None):
    """Black eyes with a small white glint on both side faces between two standing head rings.
    rim: color key of a thin border around each eye (for eyes on a dark patch of fur)."""
    a, b = ring_a[0], ring_b[0]                        # lower corners of the left side face
    n = unit(np.cross(ring_a[1] - a, b - a))
    for sign in (1, -1):
        nn, p0 = n * (sign, 1, 1), a * (sign, 1, 1)
        if rim:
            slab(part, plane_point(p0, nn, y, z), nn, w + 0.07, h + 0.07, 0.015, rim)
        slab(part, plane_point(p0, nn, y, z), nn, w, h, 0.03, "eye")
        slab(part, plane_point(p0, nn, y - 0.05, z + 0.06) + nn * 0.03, nn, 0.07, 0.07, 0.015, "glint")


def leg(name, x, y, top, rings, paint):
    """A leg from level rings (height, forward/back shift, width, depth, corner); its origin (the joint) is
    at (x, y, top)."""
    part = Part(name, origin=(x, y, top))
    loft(part, [ring((x, y + dy, z), X, Y, w, d, c) for z, dy, w, d, c in rings], paint)
    return part


# ------------------------------------------------------------------ blocks ----
# The blocky style: an animal is a stack of chunky blocks with bevelled edges, like parts built in Studio.

def rotation(rot):
    """A turn from (degrees around x, around y, around z): x tips the front up or down, y rolls to the side,
    z turns left or right. Done in the order x, y, z."""
    ax, ay, az = (math.radians(v) for v in rot)
    rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return rz @ ry @ rx


def block(part, center, size, paint, rot=(0, 0, 0), bevel=0.08, taper=(1.0, 1.0), shift=(0.0, 0.0), frame=None):
    """A block with bevelled edges. size: (width along x, depth along y, height along z) before turning.
    taper: the top is this much as wide (x) and deep (y) as the bottom; shift: the top is moved this far
    (x, y), for slanted blocks like snouts and legs. rot: see rotation(); or frame: the block's own
    (x, y, z) directions. All faces stay exactly flat."""
    a, b, up = frame if frame is not None else rotation(rot).T
    center, taper, shift = np.asarray(center, float), np.asarray(taper, float), np.asarray(shift, float)
    w, d, h = size
    e = min(bevel, w * min(1, taper[0]) / 4, d * min(1, taper[1]) / 4, h / 4)
    rings = []
    for z, inset in ((-h / 2, e), (-h / 2 + e, 0.0), (h / 2 - e, 0.0), (h / 2, e)):
        t = z / h + 0.5                                 # 0 at the bottom, 1 at the top
        k = 1 + (taper - 1) * t
        mid = center + up * z + a * shift[0] * t + b * shift[1] * t
        rings.append(ring(mid, a, b, w * k[0] - 2 * inset, d * k[1] - 2 * inset, e * (0.5 if inset else 1.0)))
    loft(part, rings, paint)


def bar(part, p, q, size, paint, bevel=0.05, side=None, taper=1.0, over=0.0):
    """A block from point p to point q (antlers, tails, feathers, whiskers). size: (width, thickness) across
    it; side: the direction of its width (default: x). taper: the q end is this much as thick. over: it
    reaches this far past both ends, so bars in a row overlap at the bends."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    up = unit(q - p)
    a = (X if side is None else np.asarray(side, float))
    a = a - np.dot(a, up) * up
    if np.linalg.norm(a) < 1e-3:
        a = Y - np.dot(Y, up) * up
    a = unit(a)
    length = np.linalg.norm(q - p) + 2 * over
    block(part, (p + q) / 2, (size[0], size[1], length), paint, bevel=bevel, taper=(taper, taper),
          frame=(a, np.cross(up, a), up))


def wedge(part, base, size, tip, paint, rot=(0, 0, 0)):
    """A point (horn, tooth, claw, spike, ear tip): a block-shaped base (x width, y depth) at `base` that
    narrows to the point `tip`."""
    turn_ = rotation(rot)
    loft(part, [square(base, turn_[:, 0], turn_[:, 1], size[0], size[1])], paint, caps=(True, False), tip=tip)


def face_axes(normal):
    """Directions on a face with this normal: (sideways, up)."""
    n = unit(np.asarray(normal, float))
    up = Z - np.dot(Z, n) * n
    up = unit(up) if np.linalg.norm(up) > 1e-3 else unit(-Y - np.dot(-Y, n) * n)
    return np.cross(up, n), up


def cartoon_eye(part, center, normal, size=0.36, look=(0.0, 0.0), pupil=(0.42, 0.62), brow=None, tilt=0.0,
                height=None):
    """A big cartoon eye on a flat face: a white block, a dark pupil (moved by `look`, as a part of the eye
    size), a small glint and, when brow is a color key, an eyebrow above it, turned by `tilt` degrees in the
    face. height: eye height (default: as high as it is wide)."""
    n = unit(np.asarray(normal, float))
    side, up = face_axes(n)
    center = np.asarray(center, float)
    h = height or size
    slab(part, center, n, size, h, 0.035, "eyewhite")
    p = center + n * 0.035 + side * look[0] * size + up * look[1] * h
    slab(part, p, n, size * pupil[0], h * pupil[1], 0.03, "eye")
    g = p + n * 0.03 + side * 0.1 * size + up * 0.16 * h
    slab(part, g, n, size * 0.15, size * 0.15, 0.02, "glint")
    if brow:
        t = math.radians(tilt)
        bs, bu = side * math.cos(t) + up * math.sin(t), up * math.cos(t) - side * math.sin(t)
        top = center + up * (h * 0.5 + size * 0.2)
        loft(part, [square(top - n * 0.06, bs, bu, size * 1.2, size * 0.26),
                    square(top + n * 0.08, bs, bu, size * 1.2, size * 0.26)], brow)


# ---------------------------------------------------------------- texture ----

def frame(n):
    """Directions on a face: t along a row of studs, b "up" (from one row to the next). Level on walls."""
    axis = X if abs(n[1]) >= 0.8 or abs(n[2]) >= 0.8 else Y
    t = unit(axis - np.dot(axis, n) * n)
    b = np.cross(n, t)
    key = b[2] if abs(b[2]) > 1e-4 else (-b[1] if abs(b[1]) > 1e-4 else -b[0])
    return (-t, -b) if key < 0 else (t, b)


class Island:
    """Faces that share one spot in the texture: flat neighbours with the same color and directions."""

    def __init__(self, color, polys, studs):
        self.color, self.polys, self.studs = color, polys, studs     # polys: (u, v) corner lists, in studs
        uv = np.concatenate(polys)
        self.lo, self.hi = uv.min(0), uv.max(0)
        # The stud grid is centered on the face: a stud in the middle when an odd number of whole studs fits
        # across, a gap in the middle when an even number fits. Only whole studs are painted (see whole_studs).
        size = self.hi - self.lo
        whole = np.floor((size - STUD_SIZE * STUD - 2 * MARGIN) / STUD) + 1
        self.grid = (self.lo + self.hi) / 2 + np.where((whole > 0) & (whole % 2 == 0), STUD / 2, 0.0)

    def pixel_size(self, density):
        return np.ceil((self.hi - self.lo) * density).astype(int) + 2 * PAD


def face_uv(part, fi):
    """(u, v) in studs of the corners of face fi, and a key for which faces can share an island."""
    pts = [part.verts[i] + part.origin for i in part.faces[fi]]
    n = unit(newell(pts))
    mirrored = np.mean(pts, 0)[0] < -1e-6              # right side: mirror image of the left side
    if mirrored:
        pts, n = mirror(pts), n * (-1, 1, 1)
    t, b = frame(n)
    uv = np.array([(np.dot(p, t), np.dot(p, b)) for p in pts])
    plane = np.dot(n, pts[0])
    return uv, (part.colors[fi], mirrored, *np.round(np.concatenate([t, b, [plane]]), 4))


def strips(part):
    """Runs of side faces next to each other in one loft band, all with the same color. A band that goes all the
    way around in one color is cut open where it is seen least (the face that looks most down, or back)."""
    by_band = {}
    for fi, (band, j) in part.bands.items():
        by_band.setdefault(band, {})[j] = fi
    runs = []
    for band, slots in by_band.items():
        n = part.band_size[band]
        color = lambda j: part.colors[slots[j]] if j in slots else None

        def hidden(j):
            nrm = unit(newell([part.verts[i] for i in part.faces[slots[j]]]))
            return -2 * nrm[2] + nrm[1]
        breaks = [j for j in range(n) if color(j) != color((j - 1) % n)]
        start = breaks[0] if breaks else (max(range(n), key=hidden) + 1) % n
        run = []
        for j in [(start + k) % n for k in range(n)] + [None]:
            if run and (j is None or color(j) != color(run[-1])):
                runs.append([slots[r] for r in run])
                run = []
            if j is not None and j in slots:
                run.append(j)
    return runs


def unfold(part, fis):
    """Lays faces that follow each other around a band flat in one piece, like peeling a label off a can: every
    face keeps its exact shape and size, and the studs run on across the folds."""
    polys, prev = [], None
    for fi in fis:
        pts = [part.verts[i] + part.origin for i in part.faces[fi]]
        t, b = frame(unit(newell(pts)))
        uv = np.array([(np.dot(p, t), np.dot(p, b)) for p in pts])
        if prev is not None:
            pf, puv = prev
            shared = [v for v in part.faces[fi] if v in part.faces[pf]]
            ia, ib = (part.faces[fi].index(v) for v in shared)
            ja, jb = (part.faces[pf].index(v) for v in shared)
            d0, d1 = uv[ib] - uv[ia], puv[jb] - puv[ja]
            turn_by = math.atan2(d1[1], d1[0]) - math.atan2(d0[1], d0[0])
            rot = np.array([[math.cos(turn_by), -math.sin(turn_by)], [math.sin(turn_by), math.cos(turn_by)]])
            uv = (uv - uv[ia]) @ rot.T + puv[ja]
        polys.append(uv)
        prev = (fi, uv)
    return polys


def make_islands(parts, no_studs, wrap=False):
    """Groups flat neighbouring faces with the same color, and returns the islands and, per face, its island.
    wrap: side faces of lofts are laid out in strips around the ring, so studs wrap around round shapes."""
    islands, owner = [], {}
    for pi, part in enumerate(parts):
        done = set()
        if wrap:
            for whole in strips(part):
                # Short pieces, laid straight: a long strip around a cone curves and would waste texture.
                pieces = max(1, math.ceil(len(whole) / 4))
                for run in np.array_split(whole, pieces):
                    run = [int(fi) for fi in run]
                    polys = unfold(part, run)
                    chord = polys[-1].mean(0) - polys[0].mean(0)
                    if np.linalg.norm(chord) > 1e-6:
                        a = -math.atan2(chord[1], chord[0])
                        rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
                        polys = [p @ rot.T for p in polys]
                    color = part.colors[run[0]]
                    for fi, uv in zip(run, polys):
                        owner[pi, fi] = (len(islands), uv)
                        done.add(fi)
                    islands.append(Island(color, polys, color not in no_studs))
        uvs, keys = zip(*(face_uv(part, fi) for fi in range(len(part.faces))))
        keys = [k if fi not in done else ("strip", fi) for fi, k in enumerate(keys)]
        group = list(range(len(part.faces)))

        def find(i):
            while group[i] != i:
                group[i] = group[group[i]]
                i = group[i]
            return i

        edges = {}
        for fi, f in enumerate(part.faces):
            for a, b in zip(f, f[1:] + f[:1]):
                edges.setdefault((min(a, b), max(a, b)), []).append(fi)
        for fs in edges.values():
            for f1 in fs:
                for f2 in fs:
                    if f1 < f2 and keys[f1] == keys[f2]:
                        group[find(f1)] = find(f2)
        members = {}
        for fi in range(len(part.faces)):
            if fi not in done:
                members.setdefault(find(fi), []).append(fi)
        for fis in members.values():
            color = part.colors[fis[0]]
            island = Island(color, [uvs[fi] for fi in fis], color not in no_studs)
            for fi in fis:
                owner[pi, fi] = (len(islands), uvs[fi])
            islands.append(island)
    return islands, owner


def pack(islands, density, order):
    """Shelf packing, one color after the other (each color starts on a new shelf). Returns the top-left
    pixel of every island and the used height, or None if it does not fit in the width."""
    spots, x, y, shelf = {}, 0, 0, 0
    bands = {}
    for color in order:
        group = sorted((i for i, isl in enumerate(islands) if isl.color == color),
                       key=lambda i: -islands[i].pixel_size(density)[1])
        if not group:
            continue
        if x > 0:
            x, y, shelf = 0, y + shelf, 0
        top = y
        for i in group:
            w, h = islands[i].pixel_size(density)
            if w > TEX:
                return None, None, None
            if x + w > TEX:
                x, y, shelf = 0, y + shelf, 0
            spots[i] = (x, y)
            x += w
            shelf = max(shelf, h)
        bands[color] = (top, y + shelf)
    return spots, y + shelf, bands


def layout(islands, order):
    """The largest texture scale (pixels per stud) at which everything fits."""
    missing = {isl.color for isl in islands} - set(order)
    if missing:
        raise ValueError(f"colors without a palette entry: {sorted(missing)}")
    lo, hi = 10.0, 400.0
    for _ in range(30):
        mid = (lo + hi) / 2
        spots, height, _ = pack(islands, mid, order)
        if spots is not None and height <= TEX:
            lo = mid
        else:
            hi = mid
    spots, _, bands = pack(islands, lo, order)
    return lo, spots, bands


def hex_srgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255


def stud_shade(du, dv, px):
    """How much lighter or darker each pixel is, for small square studs with bevelled edges (like the Roblox studs
    texture): lit from the top left, so the top and left edges are bright and the bottom and right edges dark,
    with a soft shadow below and to the right. du, dv: distance from the middle of the nearest stud, in studs."""
    side = STUD_SIZE * STUD
    s, bevel = side / 2, max(0.16 * side, 1.5 * px)     # half the side of a stud, and the width of its bevel
    edge = lambda d, limit: np.clip((limit - d) / px + 0.5, 0, 1)      # 1 inside, 0 outside, smooth
    m = np.maximum(np.abs(du), np.abs(dv))
    inside = edge(m, s)
    flat = edge(m, s - bevel)
    # which way the bevel faces: up/down where |dv| is bigger, left/right where |du| is bigger
    facing_u = np.where(np.abs(du) > np.abs(dv), np.sign(du), 0.0)
    facing_v = np.where(np.abs(du) > np.abs(dv), 0.0, np.sign(dv))
    light = -0.7 * facing_u + 0.9 * facing_v            # light from the top left
    shift = max(0.12 * side, px)
    shadow = edge(np.maximum(np.abs(du - shift), np.abs(dv + shift)), s) * (1 - inside)
    return (1 - 0.13 * shadow) * (1 + 0.03 * flat + (inside - flat) * 0.28 * light)


def inside_polys(pts, polys):
    """Which of the points (an (n, 2) array) lie inside one of the polygons (lists of (u, v) corners)."""
    x, y = pts[:, 0], pts[:, 1]
    found = np.zeros(len(pts), bool)
    for poly in polys:
        inside = np.zeros(len(pts), bool)
        for (x1, y1), (x2, y2) in zip(poly, np.roll(poly, -1, 0)):
            if y1 != y2:
                inside ^= ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1)
        found |= inside
    return found


def whole_studs(isl, iu, iv):
    """For the stud numbers iu, iv (along u and v) of every pixel: does that stud fit completely on the face?
    Studs that would be cut off by an edge are left out, so narrow faces and bevels stay plain."""
    u0, v0 = iu.min(), iv.min()
    cu, cv = np.meshgrid(np.arange(u0, iu.max() + 1), np.arange(v0, iv.max() + 1))
    centers = np.stack([isl.grid[0] + cu.ravel() * STUD, isl.grid[1] + cv.ravel() * STUD], 1)
    r = STUD_SIZE * STUD / 2 + MARGIN                  # half a stud and a small margin
    fits = np.ones(len(centers), bool)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        fits &= inside_polys(centers + (sx * r, sy * r), isl.polys)
    return fits.reshape(cu.shape)[iv - v0, iu - u0]


def paint_texture(islands, spots, bands, density, palette):
    """The texture: each island's flat color, covered with a regular grid of studs. Empty space in a band gets
    the band's color, so a whole band can be recolored at once."""
    studded = {isl.color for isl in islands if isl.studs}

    def color(name):
        # Colors with studs are at most 85% bright, so the light edges of the studs can still be lighter
        # (white studs would otherwise lose their light edges).
        c = hex_srgb(palette[name])
        return c * min(1.0, 0.85 / max(c.max(), 1e-6)) if name in studded else c

    img = np.zeros((TEX, TEX, 3))
    img[:] = color(next(iter(palette)))
    for name, (top, bottom) in bands.items():
        img[top:bottom] = color(name)
    px = 1 / density                                   # one pixel, in studs
    for i, isl in enumerate(islands):
        x0, y0 = spots[i]
        w, h = isl.pixel_size(density)
        base = color(isl.color)
        u = isl.lo[0] + (np.arange(w) + 0.5 - PAD) / density
        v = isl.hi[1] - (np.arange(h) + 0.5 - PAD) / density
        uu, vv = np.meshgrid(u, v)
        shade = np.ones_like(uu)
        if isl.studs:
            iu = np.round((uu - isl.grid[0]) / STUD).astype(int)
            iv = np.round((vv - isl.grid[1]) / STUD).astype(int)
            du, dv = uu - isl.grid[0] - iu * STUD, vv - isl.grid[1] - iv * STUD
            shade = np.where(whole_studs(isl, iu, iv), stud_shade(du, dv, px), 1.0)
        img[y0:y0 + h, x0:x0 + w] = np.clip(base[None, None] * shade[..., None], 0, 1)
    return Image.fromarray((img * 255 + 0.5).astype(np.uint8))


# ---------------------------------------------------------------- blender ----

def to_blender(animal, parts, owner, spots, islands, density, image):
    mat = bpy.data.materials.new(f"{animal.id}Studs")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.8
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    root = bpy.data.objects.new(animal.id, None)
    bpy.context.collection.objects.link(root)
    objs = []
    for pi, part in enumerate(parts):
        mesh = bpy.data.meshes.new(part.name)
        mesh.from_pydata([tuple(v - part.origin) for v in part.verts], [], part.faces)
        uv_layer = mesh.uv_layers.new(name="UVMap")
        for poly in mesh.polygons:
            ii, uv = owner[pi, poly.index]
            isl, (x0, y0) = islands[ii], spots[ii]
            for corner, li in zip(uv, poly.loop_indices):
                px = x0 + PAD + (corner[0] - isl.lo[0]) * density
                py = y0 + PAD + (isl.hi[1] - corner[1]) * density
                uv_layer.data[li].uv = (px / TEX, 1 - py / TEX)
        mesh.polygons.foreach_set("use_smooth", [False] * len(mesh.polygons))
        mesh.materials.append(mat)
        mesh.validate()
        obj = bpy.data.objects.new(part.name, mesh)
        obj.location = tuple(part.origin)
        obj.parent = root
        bpy.context.collection.objects.link(obj)
        objs.append(obj)
    return root, objs, mat


def stretch(objs, density):
    """How much the texture is stretched: the largest ratio between an edge in the texture and in 3D."""
    worst = 1.0
    for o in objs:
        mesh, uv = o.data, o.data.uv_layers[0].data
        co = lambda li: mesh.vertices[mesh.loops[li].vertex_index].co
        for poly in mesh.polygons:
            li = list(poly.loop_indices)
            for a, b in zip(li, li[1:] + li[:1]):
                l3 = (co(a) - co(b)).length
                l2 = (uv[a].uv - uv[b].uv).length * TEX / density
                if l3 > 1e-3:
                    worst = max(worst, l2 / l3, l3 / l2)
    return worst


def to_roblox(p):
    """Blender (the animal faces -y) to Roblox design coordinates (y up, the animal faces -z)."""
    return [round(float(-p[0]), 4), round(float(p[2]), 4), round(float(p[1]), 4)]


def rig_info(animal, parts):
    """Rig data for SetupZooAnimals.lua: every part's box (Roblox coordinates) and every joint.
    The first part is the root piece; every other part turns around its origin, attached to the first."""
    boxes = {}
    for part in parts:
        co = np.array([to_roblox(v) for v in part.verts])
        lo, hi = co.min(0), co.max(0)
        boxes[part.name] = {"center": [round(float(c), 4) for c in (lo + hi) / 2],
                            "size": [round(float(s), 4) for s in hi - lo]}
    lo = np.min([np.subtract(b["center"], np.divide(b["size"], 2)) for b in boxes.values()], 0)
    hi = np.max([np.add(b["center"], np.divide(b["size"], 2)) for b in boxes.values()], 0)
    lo[1] = 0.0
    body = parts[0].name
    bones = [{"name": body, "pivot": boxes[body]["center"]}]
    bones += [{"name": p.name, "pivot": to_roblox(p.origin), "parent": p.parent or body} for p in parts[1:]]
    r = lambda v: [round(float(x), 4) for x in v]
    info = {"id": animal.id, "display": animal.display, "rarity": animal.rarity,
            "root": {"center": r((lo + hi) / 2), "size": r(hi - lo)},
            "overhead": r((0, hi[1] + 1.0, (lo[2] + hi[2]) / 2)), "bones": bones, "parts": boxes}
    if animal.glow:
        info["glow"] = {name: rgb(color) for name, color in animal.glow.items()}
    if animal.shine:
        info["shine"] = animal.shine
    if animal.effects:
        info["effects"] = []
        for e in animal.effects:
            e = dict(e)
            spot = e.pop("spot", None)
            if spot:                                    # a point on the part's box, in Roblox coordinates
                box = info["root"] if e["part"] == "RootPart" else boxes[e["part"]]
                shift = {"bottom": -0.5, "center": 0.0, "top": 0.5}[spot] * box["size"][1]
                e["at"] = r(np.add(box["center"], (0, shift, 0)))
            info["effects"].append(e)
    if animal.light:
        part, color, brightness, range_ = animal.light
        info["light"] = {"part": part, "color": rgb(color), "brightness": brightness, "range": range_}
    return info


def glow_material(name, color):
    """A material that shines by itself, like Neon in Roblox (only in the .blend and the pictures)."""
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in hex_srgb(color)]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*(c * 0.3 for c in linear), 1)
    bsdf.inputs["Emission Color"].default_value = (*linear, 1)
    bsdf.inputs["Emission Strength"].default_value = 1.0
    return mat


def metal_material(name, image):
    """Shiny metal with the texture's colors (only in the .blend and the pictures)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Metallic"].default_value = 0.8
    bsdf.inputs["Roughness"].default_value = 0.3
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def export_glb(root, objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in [root] + objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_image_format="AUTO", export_materials="EXPORT")


# ----------------------------------------------------------------- renders ----

def setup_render(size=900, samples=48):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.82, 0.95, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    scene.world = world
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(40), 0, math.radians(-35)))
    bpy.context.object.data.energy = 2.4
    bpy.context.object.data.angle = math.radians(10)
    bpy.ops.mesh.primitive_plane_add(size=60)
    bpy.context.object.is_shadow_catcher = True
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    return cam


def render(cam, path, target, direction, ortho=None, distance=20, lens=60):
    d = Vector(direction).normalized()
    cam.location = Vector(target) + d * distance
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y" if abs(d.z) < 0.99 else "X").to_euler()
    if abs(d.z) >= 0.99:                               # straight down: head to the top of the picture
        cam.rotation_euler = (0, 0, math.pi)
    cam.data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam.data.ortho_scale = ortho
    else:
        cam.data.lens = lens
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def views(cam, out, animal, parts):
    """Front, side, 3/4, top and a close-up of the head, framed from the size of the animal."""
    co = np.array([v for p in parts for v in p.verts])
    lo, hi = co.min(0), co.max(0)
    h, length, width, cy = hi[2], hi[1] - lo[1], hi[0] - lo[0], (lo[1] + hi[1]) / 2
    big = max(h, length)
    shots = {"front": ((0, cy, h * 0.52), (0, -1, 0.02), dict(ortho=max(h, width) * 1.17)),
             "side": ((0, cy, h * 0.52), (1, 0, 0.02), dict(ortho=big * 1.24)),
             "34": ((0, cy, h * 0.5), (0.85, -1.0, 0.42), dict(distance=big * 2.26, lens=55)),
             "top": ((0, cy, 0), (0, 0, 1), dict(ortho=max(length, width) * 1.43)),
             "close": (animal.close[0], (0.9, -1.0, 0.35), dict(distance=animal.close[1], lens=55))}
    paths = {}
    for name, (target, direction, kw) in shots.items():
        paths[name] = out / f"r_{name}.png"
        render(cam, paths[name], target, direction, **kw)
    return paths, shots["34"]


def sheet(animal, paths, golden, tris, height, path):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    bg, panel = (26, 34, 44), (160, 200, 150)
    cell = 560
    canvas = Image.new("RGB", (20 + 3 * (cell + 20), 110 + 2 * (cell + 60)), bg)
    d = ImageDraw.Draw(canvas)
    tall = f"{height:.1f}".replace(".", ",").replace(",0", "")
    d.text((20, 18), f"{animal.display} (low-poly met noppen) - {tris} driehoekjes, ca. {tall} studs hoog",
           font=font, fill=(255, 255, 255))
    d.text((20, 54), "1 Blender-eenheid = 1 stud. Kijkt naar -Y (Front view in Blender).", font=small,
           fill=(200, 210, 220))
    items = [(paths["34"], "Schuin van voren"), (paths["side"], "Zijkant"), (paths["front"], "Voorkant"),
             (paths["top"], "Bovenkant"), (paths["close"], "Dichtbij: de noppen"), (golden, "Golden (andere textuur)")]
    for i, (p, label) in enumerate(items):
        x, y = 20 + (i % 3) * (cell + 20), 110 + (i // 3) * (cell + 60)
        im = Image.open(p).convert("RGBA")
        tile = Image.new("RGBA", im.size, panel + (255,))
        canvas.paste(Image.alpha_composite(tile, im).convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y + 40))
        d.text((x, y + 4), label, font=font, fill=(255, 255, 255))
    canvas.save(path)


# ------------------------------------------------------------------- build ----

def build(animal, out=None):
    """Builds one animal into `out` (see the top of this file). Returns the triangle count."""
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(out or (args[0] if args else OUT)).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"

    parts = animal.parts()
    islands, owner = make_islands(parts, animal.no_studs, animal.wrap)
    density, spots, bands = layout(islands, list(animal.palette))
    tris = sum(len(f) - 2 for p in parts for f in p.faces)
    print(f"{animal.id}: triangles {tris}, islands {len(islands)}, {density:.1f} pixels per stud")

    tex_path, gold_path = out / f"{animal.id}Studs.png", out / f"{animal.id}Studs_Golden.png"
    paint_texture(islands, spots, bands, density, animal.palette).save(tex_path)
    paint_texture(islands, spots, bands, density, animal.golden).save(gold_path)
    image = bpy.data.images.load(str(tex_path))
    image.pack()
    root, objs, mat = to_blender(animal, parts, owner, spots, islands, density, image)

    height = max(v[2] for p in parts for v in p.verts)
    print(f"{animal.id}: height {height:.2f} studs, stretching {stretch(objs, density):.4f} (1 = none)")
    (out / f"{animal.id}.rig.json").write_text(json.dumps(rig_info(animal, parts), indent=1))
    setup_script.write(out)
    export_glb(root, objs, out / f"{animal.id}.glb")
    for o in objs:
        if o.name in animal.glow:
            o.data.materials.clear()
            o.data.materials.append(glow_material(f"{o.name}Glow", animal.glow[o.name]))
        elif o.name in animal.shine:
            o.data.materials.clear()
            o.data.materials.append(metal_material(f"{o.name}Metal", image))
    bpy.context.preferences.filepaths.save_version = 0      # no .blend1 backup next to it
    bpy.ops.wm.save_as_mainfile(filepath=str(out / f"{animal.id}.blend"), compress=True)

    bands_path = out / "texture_bands.json"
    all_bands = json.loads(bands_path.read_text()) if bands_path.exists() else {}
    all_bands[animal.id] = {"pixels_per_stud": round(density, 2), "triangles": tris,
                            "bands": {c: {"top_row": int(a), "bottom_row": int(b)} for c, (a, b) in bands.items()}}
    bands_path.write_text(json.dumps(dict(sorted(all_bands.items())), indent=1) + "\n")

    # Previews (not saved in the .blend)
    work = out / f"_render_{animal.id}"
    work.mkdir(exist_ok=True)
    cam = setup_render()
    paths, (target, direction, kw) = views(cam, work, animal, parts)
    mat.node_tree.nodes["Image Texture"].image = bpy.data.images.load(str(gold_path))
    render(cam, work / "r_golden.png", target, direction, **kw)
    sheet(animal, paths, work / "r_golden.png", tris, height, REPO / "previews" / f"stud_{animal.id.lower()}_views.png")
    if "--keep-renders" not in sys.argv:
        for p in work.iterdir():
            p.unlink()
        work.rmdir()
    return tris
