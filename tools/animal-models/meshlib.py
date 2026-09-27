"""Turns the animal designs into real 3D meshes (.glb) for Roblox Studio's 3D Importer.

Every building block becomes one smooth convex solid (chamfered box, octagonal
prism, ellipsoid, ...). Solids with the same bone, color and material are
merged into one mesh, so a whole animal is only a few dozen MeshParts.
"""

import json
import math
import struct
import zlib

import numpy as np
from scipy.spatial import ConvexHull

from lib import IDENTITY, Animal, add, angles, apply, matmul

# ------------------------------------------------------------ design ----


class MeshAnimal(Animal):
    """Same design API as Animal, but multi-part helpers become single solids."""

    def _part(self, shape, name, size, pos, color, rot=None, R=None, chamfer=None, **kw):
        part = super()._part(shape, name, size, pos, color, rot=rot, R=R, **kw)
        if shape == "block":
            part["chamfer"] = chamfer if chamfer is not None else max(0.02, min(0.28, 0.14 * min(size)))
        return part

    def bevel(self, name, size, pos, color, b=0.6, R=IDENTITY, bottom=0.0, **kw):
        part = self._part("prism", name, size, pos, color, R=R, **kw)
        w, h, d = size
        part["prism"] = (min(b, w / 2, h / 2), min(bottom, w / 2, h / 2), max(0.03, min(0.3, 0.12 * min(size))))
        return part

    def taper(self, name, back, front, length, pos, color, R=IDENTITY, r=0.3, **kw):
        part = self._part("taper", name, (max(back[0], front[0]), max(back[1], front[1]), length), pos, color,
                          R=R, **kw)
        part["taper"] = (tuple(back), tuple(front), r)
        return part

    def tri(self, name, base, width, height, thick, color, R=IDENTITY, **kw):
        return self._part("triangle", name, (width, height, thick), add(base, apply(R, (0, height / 2, 0))), color,
                          R=R, **kw)

    def shard(self, name, base, width, height, color, R=IDENTITY, tip=0.45, cross=False, **kw):
        part = self._part("shard", name, (width, height, width), base, color, R=matmul(R, angles(0, 45, 0)), **kw)
        part["tip"] = tip
        return part


# ----------------------------------------------------------- meshing ----

def rounded_rect(w, h, rt, rb, seg):
    """Cross-section points: a w x h rectangle with rounded (seg > 1) or chamfered corners."""
    rt, rb = min(rt, w / 2, h / 2), min(rb, w / 2, h / 2)
    pts = []
    for cx, cy, r, a0 in ((w / 2 - rt, h / 2 - rt, rt, 90), (w / 2 - rb, -h / 2 + rb, rb, 0),
                          (-w / 2 + rb, -h / 2 + rb, rb, -90), (-w / 2 + rt, h / 2 - rt, rt, 180)):
        for i in range(seg + 1):
            a = math.radians(a0 - 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _sections(back, front, length, ce, make):
    """Points for a solid swept along Z from `back` (+Z) to `front` (-Z) with slightly rounded ends."""
    pts = []
    for z, size in ((length / 2, back), (-length / 2, front)):
        inner = z - math.copysign(ce, z)
        pts += [(x, y, inner) for x, y in make(*size)]
        pts += [(x * max(0.0, 1 - 2 * ce / max(size[0], 1e-6)), y * max(0.0, 1 - 2 * ce / max(size[1], 1e-6)), z)
                for x, y in make(*size)]
    return pts


def _hull_points(part):
    """Points (local space) whose convex hull is the solid."""
    shape = part["shape"]
    w, h, d = part["size"]
    if shape == "block":
        c = min(part["chamfer"], w / 2.01, h / 2.01, d / 2.01)
        pts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    pts += [(sx * (w / 2 - c), sy * h / 2, sz * (d / 2 - c)),
                            (sx * w / 2, sy * (h / 2 - c), sz * (d / 2 - c)),
                            (sx * (w / 2 - c), sy * (h / 2 - c), sz * d / 2)]
        return pts
    if shape == "prism":
        bt, bb, ce = part["prism"]
        ce = min(ce, d / 2.01)
        seg = 2 if max(bt, bb) > 0.45 else 1
        return _sections((w, h), (w, h), d, ce, lambda sw, sh: rounded_rect(sw, sh, bt, bb, seg))
    if shape == "taper":
        back, front, r = part["taper"]
        ce = max(0.03, min(0.25, 0.1 * min(min(back), min(front), d)))
        make = lambda sw, sh: rounded_rect(sw, sh, r * min(sw, sh), r * min(sw, sh), 2)
        return _sections(back, front, d, ce, make)
    if shape == "triangle":
        return [(x, y, z * d / 2) for z in (-1, 1) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (0, h / 2))]
    if shape == "wedge":
        return [(sx * w / 2, y, z) for sx in (-1, 1) for y, z in ((-h / 2, -d / 2), (-h / 2, d / 2), (h / 2, d / 2))]
    if shape == "shard":
        body = h * (1 - part["tip"])
        pts = [(sx * w / 2, y, sz * w / 2) for sx in (-1, 1) for sz in (-1, 1) for y in (0, body)]
        return pts + [(0, h, 0)]
    if shape in ("ellipsoid", "ball"):
        if shape == "ball":
            w = h = d = min(w, h, d)
        pts = [(0, h / 2, 0), (0, -h / 2, 0)]
        n_lat, n_lon = 7, 14
        for i in range(1, n_lat):
            phi = math.pi * i / n_lat
            for j in range(n_lon):
                th = 2 * math.pi * j / n_lon
                pts.append((w / 2 * math.sin(phi) * math.cos(th), h / 2 * math.cos(phi), d / 2 * math.sin(phi) * math.sin(th)))
        return pts
    if shape == "cylinder":
        r = min(h, d) / 2
        return [(x, r * math.cos(2 * math.pi * j / 16), r * math.sin(2 * math.pi * j / 16))
                for x in (-w / 2, w / 2) for j in range(16)]
    raise ValueError(shape)


def _smooth_normal(part, p):
    """Vertex normal for round solids (local space); None means use the flat face normal."""
    shape = part["shape"]
    w, h, d = part["size"]
    if shape in ("ellipsoid", "ball"):
        if shape == "ball":
            w = h = d = min(w, h, d)
        n = np.array([p[0] / (w / 2) ** 2, p[1] / (h / 2) ** 2, p[2] / (d / 2) ** 2])
        return n / np.linalg.norm(n)
    return None


def solid(part):
    """Triangles of one part in model space: (positions[n*3,3], normals[n*3,3])."""
    local = np.array(_hull_points(part), dtype=float)
    hull = ConvexHull(local)
    R = np.array(part["R"], dtype=float)
    p = np.array(part["p"], dtype=float)
    center = local.mean(axis=0)
    positions, normals = [], []
    for tri in hull.simplices:
        a, b, c = local[tri]
        n = np.cross(b - a, c - a)
        length = np.linalg.norm(n)
        if length < 1e-9:
            continue
        n /= length
        if np.dot(n, a - center) < 0:
            b, c = c, b
            n = -n
        cylinder_side = part["shape"] == "cylinder" and abs(n[0]) < 0.5
        for v in (a, b, c):
            vn = _smooth_normal(part, v)
            if cylinder_side:
                vn = np.array([0.0, v[1], v[2]]) / max(1e-9, math.hypot(v[1], v[2]))
            positions.append(R @ v + p)
            normals.append(R @ (vn if vn is not None else n))
    return np.array(positions), np.array(normals)


def stud_uvs(positions, normals):
    """Box-projected UVs in stud units (one texture tile per stud)."""
    uv = np.zeros((len(positions), 2))
    for i in range(0, len(positions), 3):
        n = np.abs(normals[i:i + 3].mean(axis=0))
        axis = int(np.argmax(n))
        u_axis, v_axis = [(2, 1), (0, 2), (0, 1)][axis]
        uv[i:i + 3, 0] = positions[i:i + 3, u_axis]
        uv[i:i + 3, 1] = positions[i:i + 3, v_axis]
    return uv


# ------------------------------------------------------------ groups ----

def _hex(color):
    return "".join(f"{round(c * 255):02x}" for c in color)


def mesh_groups(animal):
    """Merge parts that share bone, color and material into one mesh each."""
    groups = {}
    order = []
    for part in animal.parts:
        glow = part["material"] in ("Neon", "Glass")
        key = (part["bone"], _hex(part["color"]), part["material"], round(part["transparency"], 2),
               round(part["reflectance"], 2), part["role"], part["studs"] and not glow)
        if key not in groups:
            groups[key] = {"parts": [], "key": key}
            order.append(key)
        groups[key]["parts"].append(part)

    result = []
    names = {}
    for key in order:
        bone, color, material, transparency, reflectance, role, studs = key
        base = f"{bone}_{role}"
        names[base] = names.get(base, 0) + 1
        name = base if names[base] == 1 else f"{base}{names[base]}"
        pos, nrm = zip(*(solid(p) for p in groups[key]["parts"]))
        pos, nrm = np.concatenate(pos), np.concatenate(nrm)
        lo, hi = pos.min(axis=0), pos.max(axis=0)
        result.append({
            "name": name, "bone": bone, "role": role, "color": color, "material": material,
            "transparency": transparency, "reflectance": reflectance, "studs": studs,
            "shadow": any(p["shadow"] for p in groups[key]["parts"]),
            "effects": [e for p in groups[key]["parts"] for e in p["effects"]],
            "positions": pos, "normals": nrm, "center": (lo + hi) / 2, "size": hi - lo,
        })
    # The main group of each bone (the one the joint attaches to) is its largest mesh.
    for bone in animal.bones:
        members = [g for g in result if g["bone"] == bone]
        main = max(members, key=lambda g: float(np.prod(np.maximum(g["size"], 0.05))))
        main["main"] = True
    return result


# -------------------------------------------------------------- glTF ----

def _png(width, height, rgba):
    raw = b"".join(b"\x00" + bytes(rgba[y * width * 4:(y + 1) * width * 4]) for y in range(height))
    chunk = lambda tag, data: struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def stud_texture(size=128):
    """One stud per tile: transparent except a soft shadow ring and a highlight (overlays the part color)."""
    px = bytearray(size * size * 4)
    c = size / 2
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            r = math.hypot(dx, dy) / size
            # White where transparent, so the texture works both as an overlay (Roblox shows the part
            # color through it) and when multiplied with the material color (glTF viewers).
            a, v = 0, 255
            if 0.27 < r < 0.33:
                v, a = (255, 90) if dx + dy < 0 else (150, 90)
            elif r <= 0.27 and (dx + dy) < -size * 0.12:
                v, a = 255, 40
            i = (y * size + x) * 4
            px[i:i + 4] = bytes((v, v, v, a))
    return _png(size, size, px)


def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def write_glb(path, animal_id, groups, with_studs=True):
    bin_data = bytearray()
    buffer_views, accessors, meshes, nodes, materials = [], [], [], [], []
    material_index = {}

    def add_view(data, target=None):
        while len(bin_data) % 4:
            bin_data.append(0)
        view = {"buffer": 0, "byteOffset": len(bin_data), "byteLength": len(data)}
        if target:
            view["target"] = target
        bin_data.extend(data)
        buffer_views.append(view)
        return len(buffer_views) - 1

    def add_accessor(array, kind, minmax=False):
        array = np.ascontiguousarray(array, dtype=np.float32)
        acc = {"bufferView": add_view(array.tobytes(), 34962), "componentType": 5126, "count": len(array),
               "type": kind}
        if minmax:
            acc["min"] = array.min(axis=0).tolist()
            acc["max"] = array.max(axis=0).tolist()
        accessors.append(acc)
        return len(accessors) - 1

    texture = None
    images, textures, samplers = [], [], []
    if with_studs:
        images.append({"bufferView": add_view(stud_texture()), "mimeType": "image/png", "name": "Studs"})
        samplers.append({"wrapS": 10497, "wrapT": 10497, "magFilter": 9729, "minFilter": 9987})
        textures.append({"source": 0, "sampler": 0})
        texture = 0

    for g in groups:
        mkey = (g["color"], g["material"], g["studs"], g["transparency"])
        if mkey not in material_index:
            rgb = [_srgb_to_linear(int(g["color"][i:i + 2], 16) / 255) for i in (0, 2, 4)]
            mat = {"name": f"{g['material']}_{g['color']}", "pbrMetallicRoughness": {
                "baseColorFactor": rgb + [1 - g["transparency"]], "metallicFactor": 0.0, "roughnessFactor": 0.6}}
            if g["studs"] and texture is not None:
                mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": texture}
            if g["material"] == "Neon":
                mat["emissiveFactor"] = rgb
            if g["transparency"] > 0:
                mat["alphaMode"] = "BLEND"
            material_index[mkey] = len(materials)
            materials.append(mat)
        center = g["center"]
        pos = g["positions"] - center
        attributes = {"POSITION": add_accessor(pos, "VEC3", minmax=True),
                      "NORMAL": add_accessor(g["normals"], "VEC3")}
        attributes["TEXCOORD_0"] = add_accessor(stud_uvs(g["positions"], g["normals"]), "VEC2")
        meshes.append({"name": g["name"], "primitives": [{"attributes": attributes,
                                                           "material": material_index[mkey]}]})
        nodes.append({"name": g["name"], "mesh": len(meshes) - 1, "translation": [float(v) for v in center]})

    root = {"name": animal_id, "children": list(range(len(nodes)))}
    nodes.append(root)
    gltf = {
        "asset": {"version": "2.0", "generator": "Create a Zoo animal generator"},
        "scene": 0, "scenes": [{"name": animal_id, "nodes": [len(nodes) - 1]}],
        "nodes": nodes, "meshes": meshes, "materials": materials, "accessors": accessors,
        "bufferViews": buffer_views, "buffers": [{"byteLength": len(bin_data)}],
    }
    if images:
        gltf.update(images=images, textures=textures, samplers=samplers)
    while len(bin_data) % 4:
        bin_data.append(0)
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(bin_data)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(bin_data), 0x004E4942) + bytes(bin_data))
    return sum(len(g["positions"]) // 3 for g in groups)
