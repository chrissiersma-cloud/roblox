"""Blender side of the reference-driven animals: meshes from `refmodel.inflate`, texture atlas, glb, renders.

A model is a list of Piece objects. Every piece comes from one inflated outline, gets smoothed and
simplified, receives UVs from its spot in the side view (planar projection), and is then posed:
moved to the side (legs), tilted outward (ears, antlers) or mirrored to the other side.

Blender axes: +Z up, the animal faces +Y, +X is its right side. The glTF exporter turns that into
Roblox's Y up / facing -Z.
"""

import math

import bpy  # noqa: I001  (bpy must come first: it makes bmesh and mathutils importable)
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from PIL import Image
from scipy import sparse

import refmodel as rm


class Frame:
    """Maps working pixels (wp) of the reference to studs."""

    def __init__(self, ground, height_studs, top, center_x):
        self.ground = ground
        self.k = height_studs / (ground - top)
        self.cx = center_x

    def to_studs(self, v):
        return np.stack([v[:, 0] * self.k, (v[:, 1] - self.cx) * self.k, (self.ground - v[:, 2]) * self.k], 1)

    def to_pixels(self, p):
        return p[:, 1] / self.k + self.cx, self.ground - p[:, 2] / self.k


class Atlas:
    """One square texture with a cell per piece. Each cell holds that piece's part of the drawing, cleaned
    with the piece's own outline, so pieces that overlap in the side view (an ear over the head, two legs
    next to each other) keep their own colors."""

    def __init__(self, ref, size=1024, pad=6):
        self.ref, self.size, self.pad = ref, size, pad
        self.cells = {}

    def add(self, name, mask, keep=None, margin=14, band=9, dark=50):
        ys, xs = np.nonzero(mask)
        box = (max(xs.min() - margin, 0), max(ys.min() - margin, 0),
               min(xs.max() + margin, mask.shape[1]), min(ys.max() + margin, mask.shape[0]))
        self.cells[name] = {"mask": mask, "keep": keep, "box": box, "band": band, "dark": dark}
        return name

    def _layout(self, s):
        """Shelf packing at `s` texture pixels per wp; returns False if it does not fit."""
        x = y = shelf = 0
        order = sorted(self.cells, key=lambda n: -(self.cells[n]["box"][3] - self.cells[n]["box"][1]))
        for n in order:
            x0, y0, x1, y1 = self.cells[n]["box"]
            w, h = int(np.ceil((x1 - x0) * s)) + 2 * self.pad, int(np.ceil((y1 - y0) * s)) + 2 * self.pad
            if x + w > self.size:
                x, y, shelf = 0, y + shelf, 0
            if w > self.size or y + h > self.size:
                return False
            self.cells[n]["rect"] = (x + self.pad, y + self.pad, w - 2 * self.pad, h - 2 * self.pad)
            x, shelf = x + w, max(shelf, h)
        return True

    def build(self, path):
        lo, hi = 0.05, 4.0
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if self._layout(mid) else (lo, mid)
        self.scale = lo
        self._layout(lo)
        tex = np.zeros((self.size, self.size, 3), np.float32)
        for c in self.cells.values():
            x0, y0, x1, y1 = c["box"]
            rx, ry, rw, rh = c["rect"]
            img = self.ref.clean(c["mask"], keep=c["keep"], band=c["band"], dark=c["dark"])[y0:y1, x0:x1]
            img = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((rw, rh), Image.LANCZOS),
                             np.float32)
            # the padding repeats the edge of the cell, so texture filtering never mixes in a neighbour
            img = np.pad(img, ((self.pad, self.pad), (self.pad, self.pad), (0, 0)), mode="edge")
            tex[ry - self.pad:ry + rh + self.pad, rx - self.pad:rx + rw + self.pad] = img
        Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)).save(path)
        return path

    def uv(self, name, x, y):
        c = self.cells[name]
        x0, y0, x1, y1 = c["box"]
        rx, ry, rw, rh = c["rect"]
        px = rx + np.clip((x - x0) / (x1 - x0), 0, 1) * rw
        py = ry + np.clip((y - y0) / (y1 - y0), 0, 1) * rh
        return np.stack([px / self.size, 1 - py / self.size], 1)


def taubin(verts, faces, iterations=12, lam=0.5, mu=-0.53):
    """Smooths the stair steps of marching cubes without shrinking the shape."""
    n = len(verts)
    e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    e = np.concatenate([e, e[:, ::-1]])
    adj = sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    adj.data[:] = 1
    deg = np.asarray(adj.sum(1)).ravel()
    deg[deg == 0] = 1
    v = verts.copy()
    for _ in range(iterations):
        for f in (lam, mu):
            v = v + f * (adj @ v / deg[:, None] - v)
    return v


def new_object(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(verts))
    mesh.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    mesh.loops.add(len(faces) * 3)
    mesh.loops.foreach_set("vertex_index", faces.astype(np.int32).ravel())
    mesh.polygons.add(len(faces))
    mesh.polygons.foreach_set("loop_start", np.arange(0, len(faces) * 3, 3, dtype=np.int32))
    mesh.update()
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


class Piece:
    def __init__(self, name, mask, frame, atlas, cell, step=2.0, width=0.8, min_half=0.0, smooth=12, tris=2000,
                 inset=0.0):
        """inset: how far (wp) inside the outline surfaces that face forward, back, up or down take their color
        from (a number, or a map the size of the working image). The edge of a drawing has outline strokes
        and rim light that would otherwise be stretched into stripes over those surfaces."""
        self.name, self.frame, self.atlas, self.cell, self.inset = name, frame, atlas, cell, inset
        v, f = rm.inflate(mask, step=step, width=width, min_half=min_half)
        v = frame.to_studs(v)
        v = taubin(v, f, iterations=smooth)
        a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        if np.einsum("ij,ij->i", a, np.cross(b, c)).sum() < 0:      # make the normals point outward
            f = f[:, ::-1]
        self.obj = new_object(name, v, f)
        self.decimate(tris)
        self.set_uv()

    def decimate(self, tris):
        n = len(self.obj.data.polygons)
        if n > tris:
            m = self.obj.modifiers.new("Decimate", "DECIMATE")
            m.ratio = tris / n
            bpy.context.view_layer.objects.active = self.obj
            bpy.ops.object.modifier_apply(modifier=m.name)
        bm = bmesh.new()
        bm.from_mesh(self.obj.data)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(self.obj.data)
        bm.free()
        self.obj.data.validate()
        for p in self.obj.data.polygons:
            p.use_smooth = True

    def set_uv(self):
        mesh = self.obj.data
        co = np.zeros(len(mesh.vertices) * 3, np.float32)
        mesh.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3).astype(float)
        n = np.zeros(len(mesh.vertices) * 3, np.float32)
        mesh.vertices.foreach_get("normal", n)
        n = n.reshape(-1, 3).astype(float)
        inset = self.inset
        if np.ndim(inset):
            x, y = self.frame.to_pixels(co)
            inset = inset[np.clip(y.astype(int), 0, inset.shape[0] - 1), np.clip(x.astype(int), 0, inset.shape[1] - 1)]
        side_on = (1 - np.abs(n[:, 0])) ** 1.5              # 0 = faces the side, 1 = faces front/back/up/down
        n2 = n[:, 1:] / np.maximum(np.linalg.norm(n[:, 1:], axis=1, keepdims=True), 1e-6)
        sample = co.copy()
        sample[:, 1:] -= n2 * (inset * side_on * self.frame.k)[:, None]
        uv = self.atlas.uv(self.cell, *self.frame.to_pixels(sample))
        idx = np.zeros(len(mesh.loops), np.int32)
        mesh.loops.foreach_get("vertex_index", idx)
        layer = mesh.uv_layers.new(name="UVMap")
        layer.data.foreach_set("uv", uv[idx].astype(np.float32).ravel())

    def copy(self, name):
        other = Piece.__new__(Piece)
        other.name, other.frame, other.atlas, other.cell = name, self.frame, self.atlas, self.cell
        other.obj = self.obj.copy()
        other.obj.data = self.obj.data.copy()
        other.obj.name = name
        bpy.context.collection.objects.link(other.obj)
        return other

    def deform(self, fn):
        """Move every vertex: fn gets an (n, 3) array in studs and returns the new positions."""
        mesh = self.obj.data
        co = np.zeros(len(mesh.vertices) * 3, np.float32)
        mesh.vertices.foreach_get("co", co)
        mesh.vertices.foreach_set("co", np.asarray(fn(co.reshape(-1, 3).astype(float)), np.float32).ravel())
        mesh.update()
        return self

    def transform(self, matrix):
        self.obj.data.transform(matrix)
        self.obj.data.update()
        return self


def pixel_point(frame, x, y, side=0.0):
    """A point given in working pixels (and side offset in wp) as a Blender Vector in studs."""
    p = frame.to_studs(np.array([[side, x, y]], float))[0]
    return Vector(p)


def pose(pivot, rotate=(0, 0, 0), move=(0, 0, 0), shear_out=0.0, scale=1.0):
    """Matrix: scale about the pivot, shear sideways with height above the pivot (x += shear_out * dz),
    then rotate about the pivot (XYZ Euler, degrees), then move (studs)."""
    shear = Matrix.Identity(4)
    shear[0][2] = shear_out
    shear = shear @ Matrix.Scale(scale, 4)
    rot = Matrix.Rotation(math.radians(rotate[2]), 4, "Z") @ Matrix.Rotation(math.radians(rotate[1]), 4, "Y") \
        @ Matrix.Rotation(math.radians(rotate[0]), 4, "X")
    return Matrix.Translation(Vector(move) + pivot) @ rot @ shear @ Matrix.Translation(-pivot)


def mirror(matrix):
    """The same pose on the other side of the animal (for pieces that are symmetric left/right)."""
    s = Matrix.Scale(-1, 4, Vector((1, 0, 0)))
    return s @ matrix @ s


def material(name, texture_path):
    img = bpy.data.images.load(texture_path)
    img.pack()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Specular IOR Level"].default_value = 0.1
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "EXTEND"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def join(objs, name, mat):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = obj.data.name = name
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def export_glb(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_image_format="AUTO", export_materials="EXPORT")


def triangles(objs):
    return sum(len(o.data.polygons) for o in objs)


# ---------------------------------------------------------------- renders ----

def setup_render(size=(1000, 1000), samples=64):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.75, 0.82, 0.95, 1)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10), rotation=(math.radians(40), 0, math.radians(125)))
    sun = bpy.context.object
    sun.data.energy = 2.2
    sun.data.angle = math.radians(12)
    bpy.ops.mesh.primitive_plane_add(size=60)
    ground = bpy.context.object
    ground.is_shadow_catcher = True
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    return cam


def render(cam, path, target, direction, distance=None, ortho=None, lens=60):
    """direction: unit-ish vector from the target towards the camera."""
    d = Vector(direction).normalized()
    cam.location = Vector(target) + d * (distance or 30)
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lens
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
