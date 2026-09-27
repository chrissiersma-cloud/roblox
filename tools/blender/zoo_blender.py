"""Blender toolkit for the Create a Zoo animals (run with the `bpy` module, Blender 5).

Bodies are built with the Skin modifier: a stick "skeleton" of vertices with a
radius per vertex gets a skin, then Subdivision Surface makes it smooth and
organic. Coat colors are painted per vertex by rules (belly light, back dark,
noise for fur), then baked with ambient occlusion into one texture per animal.

Blender axes: +Z up, the animal faces +Y, +X is its right side. The glTF
exporter turns that into Roblox's Y up / facing -Z.
"""

import math
import random

import bpy  # noqa: I001  (bpy must come first: it makes bmesh and mathutils importable)
import bmesh
import numpy as np
from mathutils import Vector


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def hex_rgb(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]


def smooth(edge0, edge1, x):
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def ramp(stops, t):
    """stops: [(t, "#hex"), ...] -> linear RGB."""
    t = min(1.0, max(0.0, t))
    stops = [(s, hex_rgb(c)) for s, c in stops]
    if t <= stops[0][0]:
        return stops[0][1]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return [a + (b - a) * k for a, b in zip(c0, c1)]
    return stops[-1][1]


# ---------------------------------------------------------------- shapes ----

def skin_body(name, nodes, edges, subdiv=2, smooth_iter=0):
    """nodes: {key: ((x, y, z), (rx, rz))}; edges: [(key, key), ...] forming a tree."""
    keys = list(nodes)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([nodes[k][0] for k in keys], [(keys.index(a), keys.index(b)) for a, b in edges], [])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    skin = obj.modifiers.new("Skin", "SKIN")
    skin.use_smooth_shade = True
    skin.branch_smoothing = 0.6
    for i, k in enumerate(keys):
        rx, rz = nodes[k][1]
        mesh.skin_vertices[0].data[i].radius = (rx, rz)
    mesh.skin_vertices[0].data[0].use_root = True
    sub = obj.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = sub.render_levels = subdiv
    if smooth_iter:
        sm = obj.modifiers.new("Smooth", "SMOOTH")
        sm.iterations = smooth_iter
        sm.factor = 0.5
    apply_all(obj)
    return obj


def apply_all(obj):
    bpy.context.view_layer.objects.active = obj
    for m in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    for p in obj.data.polygons:
        p.use_smooth = True


def blob(name, center, radii, rot=(0, 0, 0), subdiv=3):
    """Smooth ellipsoid (subdivided cube, so it reads as a sculpted shape)."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=1, location=center,
                                         rotation=[math.radians(a) for a in rot])
    obj = bpy.context.object
    obj.name = name
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.shade_smooth()
    return obj


def horn(name, points, radii, sides=10):
    """Tapered tube along points (ears, claws, antlers, tails)."""
    bm = bmesh.new()
    rings = []
    pts = [Vector(p) for p in points]
    for i, (p, r) in enumerate(zip(pts, radii)):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        a = d.cross(up).normalized()
        b = d.cross(a).normalized()
        rx, ry = (r, r) if not isinstance(r, tuple) else r
        rings.append([bm.verts.new(p + a * math.cos(t) * rx + b * math.sin(t) * ry)
                      for t in (2 * math.pi * j / sides for j in range(sides))])
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(sides):
            bm.faces.new((r0[j], r0[(j + 1) % sides], r1[(j + 1) % sides], r1[j]))
    bm.faces.new(list(reversed(rings[0])))
    tip = bm.verts.new(pts[-1] + (pts[-1] - pts[-2]).normalized() * 0.001)
    for j in range(sides):
        bm.faces.new((rings[-1][j], rings[-1][(j + 1) % sides], tip))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = True
    return obj


def mirror_x(obj):
    """Duplicate an object mirrored to the other side (x -> -x)."""
    copy = obj.copy()
    copy.data = obj.data.copy()
    bpy.context.collection.objects.link(copy)
    copy.data.transform(np.diag([-1.0, 1.0, 1.0, 1.0]).tolist())
    copy.data.flip_normals()
    copy.name = obj.name.replace("R", "L", 1) if "R" in obj.name else obj.name + "L"
    return copy


def surface(obj, target, direction):
    """Point and normal where a ray coming from `direction` (outside) towards `target` hits obj."""
    d = Vector(direction).normalized()
    origin = Vector(target) + d * 20
    ok, loc, normal, _ = obj.ray_cast(origin, -d)
    if not ok:
        raise ValueError(f"no surface of {obj.name} near {target} from {tuple(direction)}")
    return loc, normal


def stick(obj, name, target, direction, radii, sink=0.35):
    """Ellipsoid pressed onto obj's surface (eyes, noses, spots)."""
    loc, normal = surface(obj, target, direction)
    center = loc - normal * min(radii) * sink
    b = blob(name, center, radii)
    return b, loc, normal


def tuft(obj, name, target, direction, sweep, length, width):
    """Fur tuft: a flat cone growing out of obj's surface, swept towards `sweep`."""
    loc, normal = surface(obj, target, direction)
    tip = loc + (normal * 0.45 + Vector(sweep).normalized()).normalized() * length
    mid = loc.lerp(tip, 0.45) + normal * length * 0.08
    return horn(name, [loc - normal * width * 0.4, mid, tip], [(width, width * 0.45), (width * 0.7, width * 0.3),
                                                                 (0.01, 0.01)], sides=8)


# ---------------------------------------------------------------- paint ----

def paint(obj, color_fn, seed=0, noise=0.035):
    """Per-vertex colors from color_fn(position, normal) -> linear RGB, with a little fur noise."""
    mesh = obj.data
    attr = mesh.color_attributes.get("Col") or mesh.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    rng = random.Random(seed)
    for v in mesh.vertices:
        c = color_fn(v.co, v.normal)
        k = 1 + rng.uniform(-noise, noise)
        attr.data[v.index].color = (c[0] * k, c[1] * k, c[2] * k, 1.0)
    return obj


def solid(color):
    rgb = hex_rgb(color)
    return lambda p, n: rgb


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    return obj


# ----------------------------------------------------------------- bake ----

def bake_texture(obj, size=1024, ao_strength=0.55):
    """UV unwrap, bake vertex colors + ambient occlusion into one image, and use it as the material."""
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64

    def bake(kind, target):
        mat = bpy.data.materials.new(f"{obj.name}_bake")
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        col = nt.nodes.new("ShaderNodeVertexColor")
        col.layer_name = "Col"
        # Fine fur grain: stretched noise that darkens and lightens the coat a little.
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 38.0
        noise.inputs["Detail"].default_value = 10.0
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (1.0, 1.0, 4.0)
        coord = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        grain = nt.nodes.new("ShaderNodeMapRange")
        grain.inputs["To Min"].default_value = 0.82
        grain.inputs["To Max"].default_value = 1.12
        nt.links.new(noise.outputs["Fac"], grain.inputs["Value"])
        mix = nt.nodes.new("ShaderNodeVectorMath")
        mix.operation = "MULTIPLY"
        nt.links.new(col.outputs["Color"], mix.inputs[0])
        nt.links.new(grain.outputs["Result"], mix.inputs[1])
        nt.links.new(mix.outputs["Vector"], bsdf.inputs["Base Color"])
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = target
        nt.nodes.active = tex
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        if kind == "DIFFUSE":
            scene.render.bake.use_pass_direct = False
            scene.render.bake.use_pass_indirect = False
            scene.render.bake.use_pass_color = True
        bpy.ops.object.bake(type=kind, margin=8)

    color = bpy.data.images.new(f"{obj.name}_color", size, size)
    ao = bpy.data.images.new(f"{obj.name}_ao", size, size)
    bake("DIFFUSE", color)
    bake("AO", ao)
    c = np.array(color.pixels[:]).reshape(-1, 4)
    a = np.array(ao.pixels[:]).reshape(-1, 4)[:, :1]
    c[:, :3] *= (1 - ao_strength) + ao_strength * a
    final = bpy.data.images.new(f"{obj.name}Coat", size, size)
    final.pixels[:] = c.reshape(-1)
    final.file_format = "PNG"
    final.pack()

    mat = bpy.data.materials.new(f"{obj.name}Coat")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.8
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = final
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return final


# --------------------------------------------------------------- render ----

def preview(path, target=(0, 0, 2.5), distance=16, angle=35, height=0.25, size=900, samples=48):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.62, 0.78, 0.95, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    scene.world = world
    bpy.ops.mesh.primitive_plane_add(size=80)
    ground = bpy.context.object
    gm = bpy.data.materials.new("Ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.42, 0.14, 1)
    ground.data.materials.append(gm)
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10), rotation=(math.radians(50), 0, math.radians(140)))
    bpy.context.object.data.energy = 3.2
    bpy.context.object.data.angle = math.radians(8)
    a = math.radians(angle)
    loc = Vector(target) + Vector((math.sin(a) * distance, math.cos(a) * distance, distance * height))
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.rotation_euler = (Vector(target) - loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.view_settings.view_transform = "Standard"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def export_glb(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_image_format="AUTO")
