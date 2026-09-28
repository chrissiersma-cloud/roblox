"""A low-poly Deer with classic Roblox studs painted in its texture, built from scratch in Blender.

Run: python3 tools/blender/stud_deer.py [out_dir]          (default out_dir: models/stud-deer)
Needs: pip install bpy numpy pillow scipy                    (scipy is only used for the setup script)

Writes Deer.blend, Deer.glb, DeerStuds.png, DeerStuds_Golden.png, SetupZooAnimals.lua and texture_bands.json
to out_dir, and previews/stud_deer_views.png. Change the look by editing the numbers below and running it again.

How it is made:
  1. Every part (body, neck, head, legs, ...) is a loft: a row of flat rings (boxes with 45 degree corners)
     joined by big flat faces. All rings of one loft face the same way, so every face is exactly flat.
  2. Every face gets one flat color (brown, cream, ...) from where it is and which way it faces.
  3. Every face gets its own spot in the texture, all at the same scale, so every stud has the same size.
     The studs sit in a grid in the middle of each face, rows running level. Faces of the same ring have
     the same height, so their rows line up all around a leg or the body; the right side is the mirror
     image of the left side.
  4. Faces with the same color are packed together, so every color has its own band in the texture
     (recolor a band to make a mutation, see GOLDEN).

Blender axes: +Z up, the deer faces -Y (the Front view), +X is its left side. 1 Blender unit = 1 stud.
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
STUD = 0.5            # distance between studs in studs: half the size of the studs on a Roblox part
STUD_SIZE = 0.6       # stud diameter compared to that distance
TEX = 1024            # texture size in pixels
PAD = 3               # extra pixels around every face in the texture, against color bleeding

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#a86a3d", "cream": "#f0dcb6", "white": "#fbf8f1", "antler": "#d9b98c",
           "hoof": "#4a2f21", "nose": "#4a2f21", "eye": "#161211", "glint": "#ffffff"}
GOLDEN = {"brown": "#e6ac2e", "cream": "#ffe38a", "white": "#fff6d2", "antler": "#fff0b8",
          "hoof": "#8a5a12", "nose": "#8a5a12", "eye": "#161211", "glint": "#ffffff"}
NO_STUDS = {"nose", "eye", "glint"}

X, Y, Z = np.eye(3)


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
    """One Blender object: vertices, flat faces and a color per face. `origin` becomes the object origin."""

    def __init__(self, name, origin=(0, 0, 0)):
        self.name, self.origin = name, np.array(origin, float)
        self.verts, self.faces, self.colors = [], [], []

    def vert(self, p):
        self.verts.append(np.array(p, float))
        return len(self.verts) - 1

    def face(self, idx, inside, paint):
        """Adds a face turned away from the point `inside`. A face that is not flat becomes two triangles.
        paint: a color key, or a function (center, normal) -> color key."""
        pts = [self.verts[i] for i in idx]
        n = newell(pts)
        if np.dot(n, np.mean(pts, 0) - inside) < 0:
            idx, pts, n = idx[::-1], pts[::-1], -n
        if len(idx) == 4 and np.abs(np.dot(np.array(pts) - pts[0], unit(n))).max() > 1e-5:
            self.face(idx[:3], inside, paint)
            self.face([idx[0], idx[2], idx[3]], inside, paint)
            return
        color = paint(np.mean(pts, 0), unit(n)) if callable(paint) else paint
        self.faces.append(list(idx))
        self.colors.append(color)


def ring(center, a, b, w, h, c, cb=None):
    """Box outline with 45 degree corners around `center`, in the plane of the directions a (width) and
    b (height). c: corner size on top, cb: at the bottom."""
    cb = c if cb is None else cb
    x, y = w / 2, h / 2
    corners = [(x, -y + cb), (x, y - c), (x - c, y), (-x + c, y), (-x, y - c), (-x, -y + cb), (-x + cb, -y),
               (x - cb, -y)]
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
        for j in range(n):
            k = (j + 1) % n
            part.face([ids[i][j], ids[i][k], ids[i + 1][k], ids[i + 1][j]], inside, paint)
    if caps[0]:
        part.face(ids[0], centers[0] + (centers[1] - centers[0]) * 0.01, paint)
    if tip is not None:
        t = part.vert(tip)
        for j in range(n):
            part.face([ids[-1][j], ids[-1][(j + 1) % n], t], centers[-1], paint)
    elif caps[1]:
        part.face(ids[-1], centers[-1] + (centers[-2] - centers[-1]) * 0.01, paint)


def slab(part, center, normal, w, h, depth, paint):
    """A thin box lying on a surface (eyes, nose): its front is `depth` above the surface at `center`."""
    n = unit(np.asarray(normal, float))
    up = Z - np.dot(Z, n) * n
    up = unit(up) if np.linalg.norm(up) > 1e-3 else unit(-Y - np.dot(-Y, n) * n)
    side = np.cross(up, n)
    center = np.asarray(center, float)
    loft(part, [square(center - n * 0.06, side, up, w, h), square(center + n * depth, side, up, w, h)], paint)


def mirror(pts):
    return [np.asarray(p, float) * (-1, 1, 1) for p in pts]


def plane_point(p0, n, y, z):
    """Point with the given y and z on the plane through p0 with normal n."""
    x = p0[0] - (n[1] * (y - p0[1]) + n[2] * (z - p0[2])) / n[0]
    return np.array([x, y, z])


# -------------------------------------------------------------------- deer ----

FRONT_Y, HIND_Y = -1.05, 1.3          # where the legs stand
LEG_X = 0.45                           # how far the legs stand from the middle
LEG_TOP = 2.3                          # height of the leg joints (origin of the leg objects)
HOOF = 0.38                            # hooves are below this height

# Legs, from the top (inside the body) down: (height, forward/back shift, width, depth, corner).
FRONT_LEG = [(2.55, 0.00, 0.60, 0.62, 0.15),
             (1.90, 0.00, 0.62, 0.66, 0.15),       # upper leg, just below the chest
             (1.40, -0.02, 0.52, 0.56, 0.12),
             (1.08, -0.04, 0.54, 0.58, 0.12),      # knee
             (0.80, -0.02, 0.48, 0.52, 0.10),
             (0.40, 0.00, 0.50, 0.54, 0.10),       # ankle
             (0.33, 0.00, 0.56, 0.62, 0.10),       # hoof
             (0.00, -0.03, 0.58, 0.66, 0.10)]
HIND_LEG = [(2.70, -0.02, 0.62, 0.76, 0.16),
            (2.20, 0.02, 0.74, 0.92, 0.20),        # thigh, bulging out of the body a little
            (1.60, 0.10, 0.60, 0.70, 0.15),
            (1.08, 0.18, 0.52, 0.56, 0.12),        # hock, bent back
            (0.80, 0.10, 0.48, 0.52, 0.10),
            (0.40, 0.02, 0.50, 0.54, 0.10),        # ankle
            (0.33, 0.00, 0.56, 0.62, 0.10),        # hoof
            (0.00, -0.03, 0.58, 0.66, 0.10)]


def body_paint(c, n):
    if n[2] < -0.45:
        return "cream"                                  # belly
    if n[1] < -0.35 and c[2] < 3.1:
        return "cream"                                  # chest
    return "brown"


def neck_paint(c, n):
    return "cream" if n[1] < -0.3 and c[2] < 4.1 else "brown"     # throat


def head_paint(c, n):
    return "cream" if n[2] < -0.5 else "brown"         # chin


def ear_paint(c, n):
    return "cream" if n[1] < -0.6 else "brown"         # inside of the ear


def tail_paint(c, n):
    return "white" if n[2] < -0.2 else "brown"         # white under the tail


def leg_paint(c, n):
    return "hoof" if c[2] < HOOF else "brown"


def sides(pts, tip=None):
    """The left version (as given) and the mirrored right version of rings (and a tip)."""
    yield pts, tip
    yield [mirror(r) for r in pts], None if tip is None else mirror([tip])[0]


def build_body():
    body = Part("Body")
    # Body: rings standing across the deer, from the rump (back, +y) to the chest (front, -y).
    # (y, center height, width, height, top corner, bottom corner)
    rings = [(2.04, 2.86, 0.90, 0.76, 0.26, 0.24),
             (1.92, 2.78, 1.36, 1.24, 0.38, 0.36),      # round rump
             (1.62, 2.70, 1.72, 1.50, 0.44, 0.42),      # hips
             (1.05, 2.66, 1.70, 1.46, 0.44, 0.44),
             (0.30, 2.64, 1.62, 1.42, 0.42, 0.44),      # waist
             (-0.50, 2.70, 1.68, 1.54, 0.42, 0.44),
             (-1.08, 2.80, 1.64, 1.58, 0.42, 0.40),     # shoulders
             (-1.55, 2.90, 1.30, 1.26, 0.36, 0.34)]
    loft(body, [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings], body_paint)

    # Neck: level rings going up and forward, from inside the chest to inside the head.
    rings = [(2.70, -1.18, 1.00, 1.02, 0.26),
             (3.30, -1.44, 0.92, 0.94, 0.24),
             (3.85, -1.64, 0.84, 0.86, 0.22),
             (4.35, -1.80, 0.80, 0.82, 0.20)]
    loft(body, [ring((0, y, z), X, Y, w, d, c) for z, y, w, d, c in rings], neck_paint, caps=(False, False))

    # Head: rings standing across the head, from the back of the head to the snout.
    rings = [(-1.38, 4.56, 0.90, 0.84, 0.26, 0.24),
             (-1.62, 4.61, 1.10, 1.04, 0.30, 0.28),     # widest: forehead
             (-1.98, 4.56, 1.06, 0.98, 0.28, 0.28),     # eyes
             (-2.36, 4.38, 0.84, 0.76, 0.22, 0.22),
             (-2.72, 4.20, 0.66, 0.58, 0.16, 0.14)]     # snout
    head = [ring((0, y, zc), X, Z, w, h, c, cb) for y, zc, w, h, c, cb in rings]
    loft(body, head, head_paint)

    # Eyes (black, with a small white glint) on the sides of the head, nose on the front of the snout.
    a, b = head[1][0], head[2][0]                      # lower corners of the left side face
    n = unit(np.cross(head[1][1] - a, b - a))
    for sign in (1, -1):
        nn, p0 = n * (sign, 1, 1), a * (sign, 1, 1)
        slab(body, plane_point(p0, nn, -1.82, 4.58), nn, 0.22, 0.26, 0.03, "eye")
        slab(body, plane_point(p0, nn, -1.87, 4.64) + nn * 0.03, nn, 0.07, 0.07, 0.015, "glint")
    slab(body, (0, rings[-1][0], rings[-1][1] + 0.08), -Y, 0.32, 0.18, 0.05, "nose")

    # Ears: big flat leaves pointing out and up, the inside facing forward.
    out = unit(np.array([0.85, 0.22, 0.5]))
    flat = unit(np.cross(Z, out))                     # the thin direction of the ear
    across = unit(np.cross(out, flat))
    base = np.array([0.40, -1.46, 4.88])
    ear = [square(base, across, flat, 0.34, 0.12), square(base + out * 0.30, across, flat, 0.50, 0.11),
           square(base + out * 0.58, across, flat, 0.38, 0.09)]
    for pts, tip in sides(ear, base + out * 0.86):
        loft(body, pts, ear_paint, caps=(True, False), tip=tip)

    # Antlers: a main beam going up and out, a tine forward and a tine outward, all with blunt ends.
    for beam in [[(0.28, -1.66, 5.00, 0.26), (0.40, -1.64, 5.35, 0.24), (0.56, -1.66, 5.62, 0.22),
                  (0.66, -1.74, 5.98, 0.16)],
                 [(0.39, -1.66, 5.30, 0.21), (0.41, -1.86, 5.50, 0.19), (0.43, -2.02, 5.72, 0.15)],
                 [(0.56, -1.66, 5.56, 0.21), (0.76, -1.62, 5.72, 0.18), (0.94, -1.60, 5.90, 0.15)]]:
        for r, _ in sides([square(p[:3], X, Y, p[3], p[3]) for p in beam]):
            loft(body, r, "antler")

    # Tail: a short tuft sticking out and up at the back, white underneath.
    rings = [(1.95, 3.10, 0.46, 0.34), (2.24, 3.32, 0.44, 0.32), (2.42, 3.54, 0.32, 0.24)]
    loft(body, [ring((0, y, z), X, Z, w, h, 0.09) for y, z, w, h in rings], tail_paint)
    return body


def build_leg(name, x, y, rings):
    leg = Part(name, origin=(x, y, LEG_TOP))
    loft(leg, [ring((x, y + dy, z), X, Y, w, d, c) for z, dy, w, d, c in rings], leg_paint)
    return leg


def build_parts():
    """Body and the four legs. The deer's left side is +x (it faces -y)."""
    return [build_body(), build_leg("LegFL", LEG_X, FRONT_Y, FRONT_LEG), build_leg("LegFR", -LEG_X, FRONT_Y, FRONT_LEG),
            build_leg("LegBL", LEG_X + 0.03, HIND_Y, HIND_LEG), build_leg("LegBR", -LEG_X - 0.03, HIND_Y, HIND_LEG)]


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

    def __init__(self, color, polys):
        self.color, self.polys = color, polys          # polys: (u, v) corner lists, in studs
        uv = np.concatenate(polys)
        self.lo, self.hi = uv.min(0), uv.max(0)
        self.centers = self._studs() if color not in NO_STUDS else np.zeros((0, 2))

    def _studs(self):
        """Stud centers: a grid in the middle of the face; studs whose middle is off the face are left out."""
        size = self.hi - self.lo
        count = np.floor(size / STUD + 0.4).astype(int)
        count[(count == 0) & (size >= 0.5 * STUD_SIZE * STUD)] = 1
        if (count == 0).any():
            return np.zeros((0, 2))
        mid = (self.lo + self.hi) / 2
        axes = [mid[i] + (np.arange(count[i]) - (count[i] - 1) / 2) * STUD for i in (0, 1)]
        grid = np.array([(u, v) for u in axes[0] for v in axes[1]])
        margin = 0.15 * STUD_SIZE * STUD
        keep = np.zeros(len(grid), bool)
        for poly in self.polys:
            keep |= inside_convex(poly, grid, margin)
        return grid[keep]

    def pixel_size(self, density):
        return np.ceil((self.hi - self.lo) * density).astype(int) + 2 * PAD


def inside_convex(poly, pts, margin):
    poly = np.asarray(poly)
    area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, np.roll(poly, -1, 0)))
    ok = np.ones(len(pts), bool)
    for p, q in zip(poly, np.roll(poly, -1, 0)):
        e = q - p
        if np.hypot(*e) < 1e-9:
            continue
        cross = (e[0] * (pts[:, 1] - p[1]) - e[1] * (pts[:, 0] - p[0])) / np.hypot(*e)
        ok &= (cross if area > 0 else -cross) >= margin
    return ok


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


def make_islands(parts):
    """Groups flat neighbouring faces with the same color, and returns the islands and, per face, its island."""
    islands, owner = [], {}
    for pi, part in enumerate(parts):
        uvs, keys = zip(*(face_uv(part, fi) for fi in range(len(part.faces))))
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
            members.setdefault(find(fi), []).append(fi)
        for fis in members.values():
            island = Island(part.colors[fis[0]], [uvs[fi] for fi in fis])
            for fi in fis:
                owner[pi, fi] = (len(islands), uvs[fi])
            islands.append(island)
    return islands, owner


def pack(islands, density):
    """Shelf packing, one color after the other (each color starts on a new shelf). Returns the top-left
    pixel of every island and the used height, or None if it does not fit in the width."""
    order = list(PALETTE)
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


def layout(islands):
    """The largest texture scale (pixels per stud) at which everything fits."""
    lo, hi = 10.0, 400.0
    for _ in range(30):
        mid = (lo + hi) / 2
        spots, height, _ = pack(islands, mid)
        if spots is not None and height <= TEX:
            lo = mid
        else:
            hi = mid
    spots, _, bands = pack(islands, lo)
    return lo, spots, bands


def hex_srgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255


def paint_texture(islands, spots, bands, density, palette):
    """The texture: each island's flat color with its studs (lit from above: bright rim on top, shadow below).
    Empty space in a band gets the band's color, so a whole band can be recolored at once."""
    img = np.zeros((TEX, TEX, 3))
    img[:] = hex_srgb(palette["brown"])
    for color, (top, bottom) in bands.items():
        img[top:bottom] = hex_srgb(palette[color])
    r = STUD_SIZE * STUD / 2
    px = 1 / density                                   # one pixel, in studs
    for i, isl in enumerate(islands):
        x0, y0 = spots[i]
        w, h = isl.pixel_size(density)
        base = hex_srgb(palette[isl.color])
        cols = np.arange(w) + 0.5
        rows = np.arange(h) + 0.5
        u = isl.lo[0] + (cols - PAD) / density
        v = isl.hi[1] - (rows - PAD) / density
        uu, vv = np.meshgrid(u, v)
        shade = np.ones_like(uu)
        if len(isl.centers):
            # nearest stud for every pixel
            d2 = np.full(uu.shape, np.inf)
            du = np.zeros_like(uu)
            dv = np.zeros_like(uu)
            for cu, cv in isl.centers:
                a, b = uu - cu, vv - cv
                dd = a * a + b * b
                closer = dd < d2
                d2[closer], du[closer], dv[closer] = dd[closer], a[closer], b[closer]
            dist = np.sqrt(d2)
            edge = lambda d, r0: np.clip((r0 - d) / (1.5 * px) + 0.5, 0, 1)     # 1 inside, 0 outside
            shadow = edge(np.hypot(du, dv + 0.09 * r), r * 1.04) * (1 - edge(dist, r))
            top = edge(dist, r)
            rim = top * (1 - edge(dist, r * 0.78))
            up = np.clip(dv / np.maximum(dist, 1e-6), -1, 1)
            shade = (1 - 0.24 * shadow) * (1 + top * (0.05 + rim * (0.32 * np.clip(up, 0, 1)
                                                                      - 0.16 * np.clip(-up, 0, 1))))
        img[y0:y0 + h, x0:x0 + w] = np.clip(base[None, None] * shade[..., None], 0, 1)
    return Image.fromarray((img * 255 + 0.5).astype(np.uint8))


# ---------------------------------------------------------------- blender ----

def to_blender(parts, owner, spots, islands, density, image):
    mat = bpy.data.materials.new("DeerStuds")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.8
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    root = bpy.data.objects.new("Deer", None)
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
    """Blender (deer faces -y) to Roblox design coordinates (y up, the deer faces -z)."""
    return [round(float(-p[0]), 4), round(float(p[2]), 4), round(float(p[1]), 4)]


def rig_info(parts):
    """Rig data for SetupZooAnimals.lua: every part's box (Roblox coordinates) and every joint."""
    boxes = {}
    for part in parts:
        co = np.array([to_roblox(v) for v in part.verts])
        lo, hi = co.min(0), co.max(0)
        boxes[part.name] = {"center": [round(float(c), 4) for c in (lo + hi) / 2],
                            "size": [round(float(s), 4) for s in hi - lo]}
    lo = np.min([np.subtract(b["center"], np.divide(b["size"], 2)) for b in boxes.values()], 0)
    hi = np.max([np.add(b["center"], np.divide(b["size"], 2)) for b in boxes.values()], 0)
    lo[1] = 0.0
    bones = [{"name": "Body", "pivot": boxes["Body"]["center"]}]
    bones += [{"name": p.name, "pivot": to_roblox(p.origin), "parent": "Body"} for p in parts[1:]]
    r = lambda v: [round(float(x), 4) for x in v]
    return {"id": "Deer", "display": "Deer", "rarity": "Common",
            "root": {"center": r((lo + hi) / 2), "size": r(hi - lo)},
            "overhead": r((0, hi[1] + 1.0, (lo[2] + hi[2]) / 2)), "bones": bones, "parts": boxes}


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


def render(cam, path, target, direction, ortho=None, distance=20, lens=60, up=(0, 0, 1)):
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


def views(cam, out):
    shots = [("front", (0, 0, 3.1), (0, -1, 0.02), dict(ortho=7.0)),
             ("side", (0, 0, 3.1), (1, 0, 0.02), dict(ortho=7.4)),
             ("34", (0, -0.1, 3.0), (0.85, -1.0, 0.42), dict(distance=13.5, lens=55)),
             ("top", (0, 0, 0), (0, 0, 1), dict(ortho=7.4)),
             ("close", (0.3, -1.6, 4.4), (0.9, -1.0, 0.35), dict(distance=6.5, lens=55))]
    paths = {}
    for name, target, direction, kw in shots:
        paths[name] = out / f"r_{name}.png"
        render(cam, paths[name], target, direction, **kw)
    return paths


def sheet(paths, golden, tris, path):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    bg, panel = (26, 34, 44), (160, 200, 150)
    cell = 560
    canvas = Image.new("RGB", (20 + 3 * (cell + 20), 110 + 2 * (cell + 60)), bg)
    d = ImageDraw.Draw(canvas)
    d.text((20, 18), f"Deer (low-poly met noppen) - {tris} driehoekjes, ca. 6 studs hoog", font=font,
           fill=(255, 255, 255))
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


# -------------------------------------------------------------------- main ----

def main(out):
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"

    parts = build_parts()
    islands, owner = make_islands(parts)
    density, spots, bands = layout(islands)
    tris = sum(len(f) - 2 for p in parts for f in p.faces)
    print(f"triangles {tris}, islands {len(islands)}, {density:.1f} pixels per stud")

    tex_path, gold_path = out / "DeerStuds.png", out / "DeerStuds_Golden.png"
    paint_texture(islands, spots, bands, density, PALETTE).save(tex_path)
    paint_texture(islands, spots, bands, density, GOLDEN).save(gold_path)
    image = bpy.data.images.load(str(tex_path))
    image.pack()
    root, objs, mat = to_blender(parts, owner, spots, islands, density, image)

    height = max(v[2] for p in parts for v in p.verts)
    print(f"height {height:.2f} studs, stretching {stretch(objs, density):.4f} (1 = none)")
    (out / "Deer.rig.json").write_text(json.dumps(rig_info(parts), indent=1))
    setup_script.write(out)
    (out / "Deer.rig.json").unlink()
    export_glb(root, objs, out / "Deer.glb")
    bpy.context.preferences.filepaths.save_version = 0      # no Deer.blend1 backup next to it
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "Deer.blend"), compress=True)

    # Previews (not saved in the .blend)
    work = out / "_render"
    work.mkdir(exist_ok=True)
    cam = setup_render()
    paths = views(cam, work)
    gold = bpy.data.images.load(str(gold_path))
    mat.node_tree.nodes["Image Texture"].image = gold
    render(cam, work / "r_golden.png", (0, -0.1, 3.0), (0.85, -1.0, 0.42), distance=13.5, lens=55)
    previews = REPO / "previews"
    sheet(paths, work / "r_golden.png", tris, previews / "stud_deer_views.png")
    if "--keep-renders" not in sys.argv:
        for p in work.iterdir():
            p.unlink()
        work.rmdir()
    with open(out / "texture_bands.json", "w") as f:
        json.dump({"pixels_per_stud": round(density, 2), "triangles": tris,
                   "bands": {c: {"top_row": int(a), "bottom_row": int(b)} for c, (a, b) in bands.items()}}, f, indent=1)
    return tris, bands


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(Path(args[0]).resolve() if args else REPO / "models" / "stud-deer")
