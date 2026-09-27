"""Organic low-poly modeling for the Create a Zoo animals.

Shapes are convex hulls of ellipsoids ("blobs"), capsule chains (legs, necks,
tails) and cones (ears, antlers, claws). Colors come from a small gradient
texture: every animal has a few color ramps (rows), and each vertex picks a
spot on a ramp, so a coat can fade from a light belly to a dark back.

Each bone of the rig becomes one mesh; all meshes share one texture.
"""

import math
from contextlib import contextmanager

import numpy as np
from scipy.spatial import ConvexHull

ROW_H = 8
TEX_W = 128


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rot(x=0.0, y=0.0, z=0.0):
    """Same as CFrame.Angles (degrees)."""
    x, y, z = (math.radians(a) for a in (x, y, z))
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return rx @ ry @ rz


def frame_z(direction):
    """Rotation whose local +Z points along `direction`."""
    z = np.asarray(direction, float)
    z /= np.linalg.norm(z)
    up = np.array([0, 1, 0.0]) if abs(z[1]) < 0.95 else np.array([1, 0, 0.0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z], axis=1)


def ellipsoid_samples(center, radii, R=None, n_lat=8, n_lon=14):
    """Points and outward normals on an ellipsoid surface."""
    rx, ry, rz = radii
    pts, nrm = [], []
    for i in range(n_lat + 1):
        phi = math.pi * i / n_lat
        ring = [0] if i in (0, n_lat) else range(n_lon)
        for j in ring:
            th = 2 * math.pi * j / n_lon + (math.pi / n_lon if i % 2 else 0)
            d = np.array([math.sin(phi) * math.cos(th), math.cos(phi), math.sin(phi) * math.sin(th)])
            pts.append(d * (rx, ry, rz))
            nrm.append(d / np.array((rx, ry, rz)))
    pts, nrm = np.array(pts), np.array(nrm)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    if R is not None:
        pts, nrm = pts @ R.T, nrm @ R.T
    return pts + np.asarray(center, float), nrm


def hull_mesh(points, normals):
    """Indexed convex hull with the given per-point normals (smooth shading)."""
    hull = ConvexHull(points)
    used = np.unique(hull.simplices)
    remap = -np.ones(len(points), int)
    remap[used] = np.arange(len(used))
    center = points[used].mean(axis=0)
    faces = []
    for tri in hull.simplices:
        a, b, c = points[tri]
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-10:
            continue
        faces.append(remap[tri] if np.dot(n, a - center) > 0 else remap[tri[[0, 2, 1]]])
    return points[used], normals[used], np.array(faces)


class Paint:
    """Which ramp (row) a solid uses, and where on the ramp each vertex lands (0..1)."""

    def __init__(self, row, t=0.5):
        self.row, self.t = row, t

    def values(self, positions, normals, along=None):
        if callable(self.t):
            return np.array([self.t(p, n) for p, n in zip(positions, normals)], float)
        if self.t == "along":
            return along
        return np.full(len(positions), float(self.t))


class Beast:
    def __init__(self, animal_id, display_name, rarity, ramps):
        self.id, self.display_name, self.rarity = animal_id, display_name, rarity
        self.ramps = ramps          # {row name: [(t, "#hex"), ...]}
        self.rows = list(ramps)
        self.bones = {"Body": {"parent": None, "pivot": None}}
        self.current = "Body"
        self.meshes = {}            # bone -> list of (positions, normals, uvs, faces)
        self.overhead = None

    # -- rig --------------------------------------------------------------

    @contextmanager
    def bone(self, name, parent, pivot):
        assert name not in self.bones, name
        self.bones[name] = {"parent": parent, "pivot": tuple(pivot)}
        previous, self.current = self.current, name
        try:
            yield
        finally:
            self.current = previous

    # -- solids -----------------------------------------------------------

    def _paint(self, paint):
        if isinstance(paint, str):
            return Paint(paint)
        if isinstance(paint, tuple):
            return Paint(*paint)
        return paint

    def _add(self, points, normals, paint, along=None):
        pos, nrm, faces = hull_mesh(points, normals)
        paint = self._paint(paint)
        if along is not None:
            along = along[self._last_used]
        t = np.clip(paint.values(pos, nrm, along), 0, 1)
        row = self.rows.index(paint.row)
        uv = np.stack([(0.5 + t * (TEX_W - 1)) / TEX_W, np.full(len(t), (row + 0.5) * ROW_H)], axis=1)
        self.meshes.setdefault(self.current, []).append([pos, nrm, uv, faces])
        return pos, nrm

    def blob(self, spheres, paint, n_lat=9, n_lon=16):
        """Convex hull of ellipsoids: [(center, radii[, R]), ...]."""
        pts, nrm = [], []
        for s in spheres:
            center, radii = s[0], s[1]
            radii = (radii,) * 3 if np.isscalar(radii) else radii
            p, n = ellipsoid_samples(center, radii, s[2] if len(s) > 2 else None, n_lat, n_lon)
            pts.append(p)
            nrm.append(n)
        self._last_used = None
        pos, nrm, faces = hull_mesh(np.concatenate(pts), np.concatenate(nrm))
        return self._store(pos, nrm, faces, paint)

    def _store(self, pos, nrm, faces, paint, along=None):
        paint = self._paint(paint)
        t = np.clip(paint.values(pos, nrm, along), 0, 1)
        row = self.rows.index(paint.row)
        uv = np.stack([(0.5 + t * (TEX_W - 1)) / TEX_W, np.full(len(t), (row + 0.5) * ROW_H)], axis=1)
        self.meshes.setdefault(self.current, []).append([pos, nrm, uv, faces])
        return pos, nrm

    def ball(self, center, radius, paint, n_lat=7, n_lon=12):
        return self.blob([(center, radius)], paint, n_lat, n_lon)

    def chain(self, points, paint, n_lat=7, n_lon=12, squash=None):
        """Capsule chain through [(point, radius), ...]; paint t can be 'along' (0 at start, 1 at end)."""
        pts = [np.asarray(p, float) for p, _ in points]
        lengths = [0.0]
        for a, b in zip(pts, pts[1:]):
            lengths.append(lengths[-1] + np.linalg.norm(b - a))
        total = lengths[-1] or 1.0
        for i in range(len(points) - 1):
            (p0, r0), (p1, r1) = points[i], points[i + 1]
            samples, normals, along = [], [], []
            for p, r, l in ((p0, r0, lengths[i]), (p1, r1, lengths[i + 1])):
                radii = (r, r, r) if squash is None else (r * squash[0], r * squash[1], r)
                R = frame_z(pts[i + 1] - pts[i])
                sp, sn = ellipsoid_samples(p, radii, R, n_lat, n_lon)
                samples.append(sp)
                normals.append(sn)
                along.append(np.full(len(sp), l / total))
            points_all, normals_all, along_all = map(np.concatenate, (samples, normals, along))
            hull = ConvexHull(points_all)
            used = np.unique(hull.simplices)
            # Recompute "along" for every hull vertex by projecting on the segment.
            seg = pts[i + 1] - pts[i]
            proj = np.clip(((points_all[used] - pts[i]) @ seg) / max(seg @ seg, 1e-9), 0, 1)
            along_used = (lengths[i] + proj * (lengths[i + 1] - lengths[i])) / total
            pos, nrm, faces = hull_mesh(points_all, normals_all)
            self._store(pos, nrm, faces, paint, along_used)

    def cone(self, base, tip, radius, paint, tip_radius=0.02, squash=(1.0, 1.0), n=10):
        """Cone (or frustum) from base to tip; squash flattens the cross-section."""
        base, tip = np.asarray(base, float), np.asarray(tip, float)
        R = frame_z(tip - base)
        pts, nrm = [], []
        for c, r in ((base, radius), (tip, tip_radius)):
            for j in range(n):
                a = 2 * math.pi * j / n
                d = np.array([math.cos(a) * squash[0], math.sin(a) * squash[1], 0])
                pts.append(c + R @ (d * r))
                nrm.append(R @ np.array([math.cos(a) / squash[0], math.sin(a) / squash[1], 0.3]))
        pts, nrm = np.array(pts), np.array(nrm)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        pos, nrm2, faces = hull_mesh(pts, nrm)
        along = np.clip(((pos - base) @ (tip - base)) / max((tip - base) @ (tip - base), 1e-9), 0, 1)
        return self._store(pos, nrm2, faces, paint, along)

    def eye(self, center, radius, iris=None, direction=(0, 0, -1), pupil="Dark", shine="White"):
        """Glossy eye: dark ball (optionally with a colored iris) and a white glint."""
        d = np.asarray(direction, float)
        d /= np.linalg.norm(d)
        c = np.asarray(center, float)
        if iris:
            self.ball(c, radius, iris)
            self.ball(c + d * radius * 0.45, radius * 0.6, pupil)
        else:
            self.ball(c, radius, pupil)
        up = np.array([0, 1, 0.0])
        side = np.cross(up, d)
        self.ball(c + d * radius * 0.8 + up * radius * 0.35 + side * radius * 0.3, radius * 0.32, shine, 5, 8)

    def spots(self, surface, count, radius, paint, rng, where=lambda p, n: True, flat=0.35):
        """Small flat patches stuck on a solid's surface (returned by blob())."""
        pos, nrm = surface
        choices = [i for i in range(len(pos)) if where(pos[i], nrm[i])]
        for i in rng.choice(choices, size=min(count, len(choices)), replace=False):
            r = radius * rng.uniform(0.75, 1.25)
            R = frame_z(nrm[i])
            self.blob([(pos[i] - nrm[i] * r * flat * 0.3, (r, r * rng.uniform(0.7, 1.0), r * flat), R)], paint, 4, 8)

    # -- output -----------------------------------------------------------

    def texture_rgba(self):
        height = 1
        while height < ROW_H * len(self.rows):
            height *= 2
        px = bytearray(TEX_W * height * 4)
        for r, name in enumerate(self.rows):
            stops = [(t, hex_rgb(c)) for t, c in self.ramps[name]]
            for x in range(TEX_W):
                t = x / (TEX_W - 1)
                if t <= stops[0][0]:
                    col = stops[0][1]
                elif t >= stops[-1][0]:
                    col = stops[-1][1]
                else:
                    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
                        if t0 <= t <= t1:
                            k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                            col = tuple(round(a + (b - a) * k) for a, b in zip(c0, c1))
                            break
                for y in range(r * ROW_H, (r + 1) * ROW_H):
                    i = (y * TEX_W + x) * 4
                    px[i:i + 4] = bytes((*col, 255))
        for y in range(len(self.rows) * ROW_H, height):
            px[y * TEX_W * 4:(y + 1) * TEX_W * 4] = px[(y - 1) * TEX_W * 4:y * TEX_W * 4]
        return TEX_W, height, px

    def bone_meshes(self):
        """{bone: (positions, normals, uvs(0..1), faces)} merged per bone."""
        _, height, _ = self.texture_rgba()
        out = {}
        for bone, parts in self.meshes.items():
            pos, nrm, uv, faces, offset = [], [], [], [], 0
            for p, n, u, f in parts:
                pos.append(p)
                nrm.append(n)
                u = u.copy()
                u[:, 1] /= height
                uv.append(u)
                faces.append(f + offset)
                offset += len(p)
            out[bone] = tuple(map(np.concatenate, (pos, nrm, uv, faces)))
        return out
