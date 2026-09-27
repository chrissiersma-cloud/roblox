#!/usr/bin/env python3
"""Builds the forest animals: one .glb per animal (one mesh per bone, one shared texture) and rigs.json.

    python3 build_forest.py [out_dir]
"""

import json
import struct
import sys
from pathlib import Path

import numpy as np

import forest
from meshlib import _png

HERE = Path(__file__).resolve().parent


def write_glb(path, beast):
    meshes = beast.bone_meshes()
    width, height, rgba = beast.texture_rgba()
    png = _png(width, height, rgba)
    bin_data = bytearray()
    views, accessors, gmeshes, nodes = [], [], [], []

    def view(data, target=None):
        while len(bin_data) % 4:
            bin_data.append(0)
        v = {"buffer": 0, "byteOffset": len(bin_data), "byteLength": len(data)}
        if target:
            v["target"] = target
        bin_data.extend(data)
        views.append(v)
        return len(views) - 1

    def accessor(array, kind, component=5126, target=34962, minmax=False):
        dtype = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[component]
        array = np.ascontiguousarray(array, dtype=dtype)
        acc = {"bufferView": view(array.tobytes(), target), "componentType": component,
               "count": int(array.size if kind == "SCALAR" else len(array)), "type": kind}
        if minmax:
            acc["min"] = array.min(axis=0).tolist()
            acc["max"] = array.max(axis=0).tolist()
        accessors.append(acc)
        return len(accessors) - 1

    image_view = view(png)
    info = {}
    for bone, (pos, nrm, uv, faces) in meshes.items():
        lo, hi = pos.min(axis=0), pos.max(axis=0)
        center = (lo + hi) / 2
        index_type = 5123 if len(pos) < 65536 else 5125
        prim = {
            "attributes": {
                "POSITION": accessor(pos - center, "VEC3", minmax=True),
                "NORMAL": accessor(nrm / np.linalg.norm(nrm, axis=1, keepdims=True), "VEC3"),
                "TEXCOORD_0": accessor(uv, "VEC2"),
            },
            "indices": accessor(faces.reshape(-1), "SCALAR", component=index_type, target=34963),
            "material": 0,
        }
        gmeshes.append({"name": bone, "primitives": [prim]})
        nodes.append({"name": bone, "mesh": len(gmeshes) - 1, "translation": [float(v) for v in center]})
        info[bone] = {"center": center, "size": hi - lo, "triangles": len(faces)}
    nodes.append({"name": beast.id, "children": list(range(len(nodes)))})
    gltf = {
        "asset": {"version": "2.0", "generator": "Create a Zoo animal generator"},
        "scene": 0, "scenes": [{"name": beast.id, "nodes": [len(nodes) - 1]}],
        "nodes": nodes, "meshes": gmeshes,
        "materials": [{"name": f"{beast.id}Coat", "pbrMetallicRoughness": {
            "baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 0.85}}],
        "textures": [{"source": 0, "sampler": 0}],
        "samplers": [{"magFilter": 9729, "minFilter": 9729, "wrapS": 33071, "wrapT": 33071}],
        "images": [{"bufferView": image_view, "mimeType": "image/png", "name": f"{beast.id}Coat"}],
        "accessors": accessors, "bufferViews": views, "buffers": [{"byteLength": 0}],
    }
    while len(bin_data) % 4:
        bin_data.append(0)
    gltf["buffers"][0]["byteLength"] = len(bin_data)
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_data)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(bin_data), 0x004E4942) + bytes(bin_data))
    return info


def rig(beast, info):
    r = lambda v: [round(float(x), 4) for x in v]
    lo = np.min([i["center"] - i["size"] / 2 for i in info.values()], axis=0)
    hi = np.max([i["center"] + i["size"] / 2 for i in info.values()], axis=0)
    lo[1] = 0.0
    bones = []
    for name, b in beast.bones.items():
        pivot = b["pivot"] if b["parent"] else info[name]["center"]
        bones.append({"name": name, "parent": b["parent"], "pivot": r(pivot)})
    return {
        "id": beast.id, "display": beast.display_name, "rarity": beast.rarity,
        "root": {"center": r((lo + hi) / 2), "size": r(hi - lo)},
        "overhead": r((0, (beast.overhead or hi[1]) + 1.0, (lo[2] + hi[2]) / 2)),
        "bones": bones,
        "parts": {name: {"center": r(i["center"]), "size": r(i["size"])} for name, i in info.items()},
    }


def to_luau(value, indent=1):
    tab = "\t"
    if isinstance(value, dict):
        items = []
        for k, v in value.items():
            key = k if k.isidentifier() else f'["{k}"]'
            items.append(f"{tab * indent}{key} = {to_luau(v, indent + 1)},")
        return "{\n" + "\n".join(items) + f"\n{tab * (indent - 1)}}}"
    if isinstance(value, (list, tuple)):
        if all(isinstance(v, (int, float)) for v in value):
            return "{ " + ", ".join(repr(float(v)) for v in value) + " }"
        return "{\n" + "\n".join(f"{tab * indent}{to_luau(v, indent + 1)}," for v in value) + f"\n{tab * (indent - 1)}}}"
    if isinstance(value, str):
        return '"' + value.replace('"', '\\"') + '"'
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    return repr(value)


def reference_pair(parts):
    """Two parts far apart horizontally, used to find how Studio turned the model."""
    names = list(parts)
    best, pair = -1.0, (names[0], names[-1])
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ca, cb = np.array(parts[a]["center"]), np.array(parts[b]["center"])
            d = float(np.hypot(*(ca - cb)[[0, 2]]))
            if d > best:
                best, pair = d, (a, b)
    return list(pair)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "build" / "forest"
    out.mkdir(parents=True, exist_ok=True)
    rigs = []
    for make in forest.ALL:
        beast = make()
        info = write_glb(out / f"{beast.id}.glb", beast)
        rigs.append(rig(beast, info))
        tris = sum(i["triangles"] for i in info.values())
        print(f"{beast.id:14} {beast.rarity:7} {len(info):2} meshes {tris:6} triangles")
    (out / "rigs.json").write_text(json.dumps(rigs, indent=1))
    for r in rigs:
        r["ref"] = reference_pair(r["parts"])
        r["bones"] = [{k: v for k, v in b.items() if v is not None} for b in r["bones"]]
    data = {r["id"]: {k: v for k, v in r.items() if k != "id"} for r in rigs}
    template = (HERE / "SetupZooAnimals.template.lua").read_text()
    (out / "SetupZooAnimals.lua").write_text(template.replace("--[[DATA]]", to_luau(data)))


if __name__ == "__main__":
    main()
