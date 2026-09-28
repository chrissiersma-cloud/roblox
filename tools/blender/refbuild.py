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
from scipy import ndimage, sparse
from scipy.cluster.vq import kmeans2
from skimage import color

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

    def __init__(self, ref, size=1024, pad=6, flat=0):
        """flat: number of flat colors for the low-poly look (0 = keep the painted colors). The painted lines
        and shading strokes are removed and every spot gets the nearest of `flat` colors picked from the
        drawing, except inside a cell's `detail` area (eyes), which keeps the drawing."""
        self.ref, self.size, self.pad, self.flat = ref, size, pad, flat
        self.cells = {}

    def add(self, name, mask, keep=None, margin=14, band=9, dark=50, soft=False, detail=None, colors=None):
        """soft=True also adds a cell "<name>~soft": the same drawing without small details (spots, painted
        lines), for the faces that look forward, back, up or down. Those faces take their colors from a line
        in the drawing, and small details on that line would be smeared into stripes."""
        ys, xs = np.nonzero(mask)
        box = (max(xs.min() - margin, 0), max(ys.min() - margin, 0),
               min(xs.max() + margin, mask.shape[1]), min(ys.max() + margin, mask.shape[0]))
        self.cells[name] = {"mask": mask, "keep": keep, "box": box, "band": band, "dark": dark, "soft": False,
                            "res": 1.0, "detail": detail, "colors": colors}
        if soft:
            self.cells[name + "~soft"] = dict(self.cells[name], soft=True, res=0.5)
        return name

    def _layout(self, s):
        """Shelf packing at `s` texture pixels per wp; returns False if it does not fit."""
        x = y = shelf = 0
        order = sorted(self.cells, key=lambda n: -(self.cells[n]["box"][3] - self.cells[n]["box"][1]))
        for n in order:
            x0, y0, x1, y1 = self.cells[n]["box"]
            r = s * self.cells[n]["res"]
            w, h = int(np.ceil((x1 - x0) * r)) + 2 * self.pad, int(np.ceil((y1 - y0) * r)) + 2 * self.pad
            if x + w > self.size:
                x, y, shelf = 0, y + shelf, 0
            if w > self.size or y + h > self.size:
                return False
            self.cells[n]["rect"] = (x + self.pad, y + self.pad, w - 2 * self.pad, h - 2 * self.pad)
            x, shelf = x + w, max(shelf, h)
        return True

    def _fit(self, c, arr, resample=Image.LANCZOS):
        """A full-size working-image array cropped to the cell's box and resized to its rectangle."""
        x0, y0, x1, y1 = c["box"]
        rw, rh = c["rect"][2:]
        a = arr[y0:y1, x0:x1]
        if a.dtype == bool:
            return np.asarray(Image.fromarray(a.astype(np.uint8) * 255).resize((rw, rh), Image.BILINEAR),
                              np.float32) / 255
        return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((rw, rh), resample), np.float32)

    def _px(self, c, wp):
        """A size in working pixels as an odd number of texture pixels in this cell."""
        return max(3, int(wp * self.scale * c["res"])) | 1

    @staticmethod
    def _median(img, size):
        return np.stack([ndimage.median_filter(img[..., i], size=size) for i in range(3)], -1)

    @staticmethod
    def _palette(samples, k, merge):
        """k flat colors (Lab) for the samples. With merge, a color that is only a lighter or darker shade of
        a more common one (painted shading and highlights) is folded into it: flat, like low-poly art.
        Very dark colors (shadow strokes) are dropped too; real dark parts (hooves, nose, eyes) come back
        from the cell's `keep` and `detail` areas."""
        palette, labels = kmeans2(samples, k, minit="++", seed=7)
        target = np.arange(len(palette))
        if merge:
            light = np.nonzero(palette[:, 0] >= 35)[0]
            for j in np.nonzero(palette[:, 0] < 35)[0]:
                target[j] = light[np.argmin(((palette[light] - palette[j]) ** 2).sum(1))]
            counts = np.bincount(labels, minlength=len(palette))
            order = np.argsort(-counts)
            for j in order[1:]:
                for i in order:
                    if counts[i] <= counts[j]:
                        break
                    dl = abs(palette[i, 0] - palette[j, 0])
                    dc = np.hypot(palette[i, 1] - palette[j, 1], palette[i, 2] - palette[j, 2])
                    if target[j] == j and target[i] == i and dl < 22 and dc < 14:
                        target[j] = i
                        break
        return palette[target]

    def _quantize(self, img, palette_lab, smooth):
        lab = color.rgb2lab(np.clip(img, 0, 255) / 255)
        palette_lab = np.unique(palette_lab, axis=0)
        label = ((lab[..., None, :] - palette_lab[None, None]) ** 2).sum(-1).argmin(-1)
        # majority vote in a small window removes single stray pixels between two colors
        votes = np.stack([ndimage.uniform_filter((label == i).astype(np.float32), smooth)
                          for i in range(len(palette_lab))], -1)
        return color.lab2rgb(palette_lab)[votes.argmax(-1)] * 255

    def build(self, path):
        lo, hi = 0.05, 4.0
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if self._layout(mid) else (lo, mid)
        self.scale = lo
        self._layout(lo)
        drawn = {}
        for name, c in self.cells.items():
            clean = self.ref.clean(c["mask"], keep=c["keep"], band=c["band"], dark=c["dark"])
            drawn[name] = self._fit(c, clean)
        if self.flat:
            # the flat colors: k-means over the drawing (painted lines removed first), in Lab color space
            samples, palettes = [], {}
            for name, c in self.cells.items():
                if c["soft"]:
                    continue
                inside = self._fit(c, c["mask"]) > 0.5
                lab = color.rgb2lab(self._median(drawn[name], self._px(c, 17)) / 255)[inside].astype(float)
                if c["colors"]:                                   # this cell gets its own few colors
                    palettes[name] = self._palette(lab[::3], c["colors"], merge=False)
                else:
                    samples.append(lab)
            palette = self._palette(np.concatenate(samples)[::7], self.flat, merge=True)
        tex = np.zeros((self.size, self.size, 3), np.float32)
        for name, c in self.cells.items():
            rx, ry, rw, rh = c["rect"]
            img = drawn[name]
            own = palettes.get(name.split("~")[0], palette) if self.flat else None
            if self.flat:
                img = self._quantize(self._median(img, self._px(c, 17)), own, self._px(c, 11))
            if c["soft"]:
                size = self._px(c, 45)                                   # about 45 wp: wider than a spot or stroke
                soft = self._median(img, size)
                soft = self._quantize(soft, own, 3) if self.flat else \
                    ndimage.gaussian_filter(soft, sigma=(size / 6, size / 6, 0))
                img = soft
            # details that must stay as drawn: dark hooves and nose (keep) and eyes (detail)
            for zone in (c["keep"], c["detail"]):
                if zone is not None and (self.flat or c["soft"]):
                    d = ndimage.gaussian_filter(self._fit(c, zone), 1.0)[..., None]
                    img = img * (1 - d) + drawn[name] * d
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


def _ranks(totals):
    """0, 1, .., n-1 for every polygon, one after the other (the position of each corner in its polygon)."""
    return np.arange(totals.sum()) - np.repeat(np.cumsum(totals) - totals, totals)


class Piece:
    def __init__(self, name, mask, frame, atlas, cell, step=2.0, width=0.8, min_half=0.0, smooth=12, tris=2000,
                 inset=0.0, profile="round", bevel=0.3, bevel_max=18.0, sharp=None, soft=False, flat=False):
        """inset: how far (wp) inside the outline surfaces that face forward, back, up or down take their color
        from (a number, or a map the size of the working image). The edge of a drawing has outline strokes
        and rim light that would otherwise be stretched into stripes over those surfaces.
        profile/bevel/bevel_max: see refmodel.inflate. sharp: angle (degrees) above which edges are shaded
        hard, for the faceted low-poly look (None = smooth everywhere). flat: every face shaded flat, and
        faces lying in (almost) the same plane merged into big ones: the classic low-poly look."""
        self.flat = flat
        self.name, self.frame, self.atlas, self.cell, self.inset = name, frame, atlas, cell, inset
        self.soft = soft          # faces that don't look sideways use the "~soft" atlas cell (see Atlas.add)
        v, f = rm.inflate(mask, step=step, width=width, min_half=min_half, profile=profile, bevel=bevel,
                          bevel_max=bevel_max)
        v = frame.to_studs(v)
        v = taubin(v, f, iterations=smooth)
        a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        if np.einsum("ij,ij->i", a, np.cross(b, c)).sum() < 0:      # make the normals point outward
            f = f[:, ::-1]
        self.obj = new_object(name, v, f)
        self.decimate(tris)
        if sharp is not None:
            self.obj.data.set_sharp_from_angle(angle=math.radians(sharp))
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
        if self.flat:
            bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(5), verts=bm.verts[:], edges=bm.edges[:])
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
        bm.to_mesh(self.obj.data)
        bm.free()
        self.obj.data.validate()
        for p in self.obj.data.polygons:
            p.use_smooth = not self.flat

    def set_uv(self):
        """Planar projection from the side view. Every face corner gets its own UV, so a face that looks
        forward or up can take its color from further inside the drawing (and from the soft cell)."""
        mesh = self.obj.data
        co = np.zeros(len(mesh.vertices) * 3, np.float32)
        mesh.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3).astype(float)
        idx = np.zeros(len(mesh.loops), np.int32)
        mesh.loops.foreach_get("vertex_index", idx)
        if self.soft:
            pn = np.zeros(len(mesh.polygons) * 3, np.float32)
            mesh.polygons.foreach_get("normal", pn)
            starts = np.zeros(len(mesh.polygons), np.int32)
            mesh.polygons.foreach_get("loop_start", starts)
            totals = np.zeros(len(mesh.polygons), np.int32)
            mesh.polygons.foreach_get("loop_total", totals)
            poly_of_loop = np.empty(len(mesh.loops), np.int64)
            poly_of_loop[np.repeat(starts, totals) + _ranks(totals)] = np.repeat(np.arange(len(totals)), totals)
            n = pn.reshape(-1, 3)[poly_of_loop]
        else:
            vn = np.zeros(len(mesh.vertices) * 3, np.float32)
            mesh.vertices.foreach_get("normal", vn)
            n = vn.reshape(-1, 3)[idx]
        n = n.astype(float)
        p = co[idx]
        inset = self.inset
        if np.ndim(inset):
            x, y = self.frame.to_pixels(p)
            inset = inset[np.clip(y.astype(int), 0, inset.shape[0] - 1), np.clip(x.astype(int), 0, inset.shape[1] - 1)]
        side_on = (1 - np.abs(n[:, 0])) ** 1.5              # 0 = faces the side, 1 = faces front/back/up/down
        soft = self.soft & (np.abs(n[:, 0]) < 0.85)
        side_on = np.where(soft, 1.0, side_on)
        n2 = n[:, 1:] / np.maximum(np.linalg.norm(n[:, 1:], axis=1, keepdims=True), 1e-6)
        sample = p.copy()
        sample[:, 1:] -= n2 * (inset * side_on * self.frame.k)[:, None]
        x, y = self.frame.to_pixels(sample)
        uv = self.atlas.uv(self.cell, x, y)
        if self.soft:
            uv[soft] = self.atlas.uv(self.cell + "~soft", x[soft], y[soft])
        layer = mesh.uv_layers.new(name="UVMap")
        layer.data.foreach_set("uv", uv.astype(np.float32).ravel())

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


def lift_to_ground(objs):
    """Moves the objects up or down so the lowest point (the hooves) is exactly at z = 0. Returns the shift."""
    low = min(min(v.co.z for v in o.data.vertices) for o in objs)
    for o in objs:
        o.data.transform(Matrix.Translation((0, 0, -low)))
        o.data.update()
    return -low


def group(objs, name):
    """An empty named after the animal with the pieces under it: Studio's importer turns it into one Model."""
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    for o in objs:
        o.parent = root
    return root


def to_roblox(p):
    """Blender (x right, y forward, z up) to Roblox/glTF (x right, y up, facing -z)."""
    return [round(float(p[0]), 4), round(float(p[2]), 4), round(float(-p[1]), 4)]


def rig_info(objs, animal_id, display, rarity, pivots):
    """Rig data for the setup script: every piece's box (center and size, in Roblox coordinates) and every joint.
    pivots: {piece name: (parent name, pivot point in Blender coordinates)}; the root piece has parent None."""
    parts = {}
    for o in objs:
        co = np.array([to_roblox(v.co) for v in o.data.vertices])
        lo, hi = co.min(0), co.max(0)
        parts[o.name] = {"center": [round(float(c), 4) for c in (lo + hi) / 2],
                         "size": [round(float(s), 4) for s in hi - lo]}
    lo = np.min([np.array(p["center"]) - np.array(p["size"]) / 2 for p in parts.values()], axis=0)
    hi = np.max([np.array(p["center"]) + np.array(p["size"]) / 2 for p in parts.values()], axis=0)
    lo[1] = 0.0
    bones = []
    for name, (parent, pivot) in pivots.items():
        bone = {"name": name, "pivot": parts[name]["center"] if parent is None else to_roblox(pivot)}
        if parent:
            bone["parent"] = parent
        bones.append(bone)
    r = lambda v: [round(float(x), 4) for x in v]
    return {"id": animal_id, "display": display, "rarity": rarity,
            "root": {"center": r((lo + hi) / 2), "size": r(hi - lo)},
            "overhead": r((0, hi[1] + 1.0, (lo[2] + hi[2]) / 2)), "bones": bones, "parts": parts}


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
