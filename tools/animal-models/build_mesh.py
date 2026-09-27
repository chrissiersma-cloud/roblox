#!/usr/bin/env python3
"""Builds the animals as real meshes: one .glb per animal plus rig/metadata for the Studio setup script.

    python3 build_mesh.py [out_dir]
"""

import json
import sys
from pathlib import Path

import numpy as np

import animals
from lib import add, apply
from meshlib import MeshAnimal, mesh_groups, write_glb

HERE = Path(__file__).resolve().parent
animals.Animal = MeshAnimal  # the designs build single solids instead of multi-part blocks


def rig_data(animal, groups):
    lo = np.min([g["center"] - g["size"] / 2 for g in groups], axis=0)
    hi = np.max([g["center"] + g["size"] / 2 for g in groups], axis=0)
    lo[1] = 0.0
    root_center, root_size = (lo + hi) / 2, hi - lo
    main = {g["bone"]: g["name"] for g in groups if g.get("main")}
    bones = {}
    for bone, info in animal.bones.items():
        pivot = info["pivot"] if info["parent"] else [float(v) for v in next(g["center"] for g in groups
                                                                              if g["name"] == main[bone])]
        bones[bone] = {"parent": info["parent"], "pivot": [round(float(v), 4) for v in pivot], "main": main[bone]}
    r = lambda v: [round(float(x), 4) for x in v]
    return {
        "id": animal.id, "display": animal.display_name, "rarity": animal.rarity,
        "root": {"center": r(root_center), "size": r(root_size)},
        "ride": r((0, animal.ride_height or hi[1], animal.ride_z)),
        "overhead": r((0, (animal.overhead or hi[1]) + 1.2, root_center[2])),
        "bones": bones,
        "parts": [{
            "name": g["name"], "bone": g["bone"], "role": g["role"], "color": g["color"], "material": g["material"],
            "transparency": g["transparency"], "reflectance": g["reflectance"], "shadow": g["shadow"],
            "studs": g["studs"], "center": r(g["center"]), "size": r(g["size"]), "effects": g["effects"],
        } for g in groups],
        "rootEffects": animal.root_effects,
    }


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "build" / "meshes"
    out.mkdir(parents=True, exist_ok=True)
    rigs = []
    for make in animals.ALL:
        animal = make()
        groups = mesh_groups(animal)
        tris = write_glb(out / f"{animal.id}.glb", animal.id, groups)
        rigs.append(rig_data(animal, groups))
        print(f"{animal.id:18} {len(groups):3} meshes {tris:6} triangles")
    (out / "rigs.json").write_text(json.dumps(rigs, indent=1))


if __name__ == "__main__":
    main()
