#!/usr/bin/env python3
"""Builds the zoo showpieces (Voidwhisker and Gorilla King), in the same format as the Dark Woods animals.

    python3 build_zoo_showpieces.py                  -> writes build/phoenix.json
    python3 build_zoo_showpieces.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
"""

import json
import subprocess
import sys
from pathlib import Path

from build_dark_woods import finish
from zoo_showpieces import ALL

HERE = Path(__file__).resolve().parent


def main():
    fx_source = (HERE / "AnimalFX.lua").read_text()
    animals = [make() for make in ALL]
    nodes = []
    for a in animals:
        node = finish(a, fx_source)
        node["tags"] = [t for t in node["tags"] if t != "DarkWoodsAnimal"] + [f"{a.rarity}Animal"]
        nodes.append(node)
    tree = [{"class": "Folder", "name": "ZooShowpieces", "children": nodes}]
    out = HERE / "build" / "zoo_showpieces.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(tree))
    for a in animals:
        top = max(p["p"][1] + max(p["size"]) / 2 for p in a.parts)
        print(f"{a.id:16} {a.rarity:10} {len(a.parts):3} parts, {len(a.bones):2} joints, about {top:4.1f} studs tall")
    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cargo", "run", "--quiet", "--release", "--manifest-path",
                        str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out), target], check=True)


if __name__ == "__main__":
    main()
