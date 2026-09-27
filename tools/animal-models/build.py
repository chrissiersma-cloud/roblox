#!/usr/bin/env python3
"""Builds all animal models.

    python3 build.py                 -> writes build/animals.json
    python3 build.py --rbxm OUT.rbxm -> also writes the .rbxm (needs cargo)
"""

import json
import subprocess
import sys
from pathlib import Path

from animals import ALL

HERE = Path(__file__).resolve().parent


def main():
    animals = [make() for make in ALL]
    tree = [{
        "class": "Folder", "name": "HuntAnimalModels",
        "children": [a.build() for a in animals],
    }]
    out = HERE / "build" / "animals.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(tree))
    for a in animals:
        print(f"{a.id:18} {a.rarity:10} {len(a.parts):3} parts, {len(a.bones):2} bones")

    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        subprocess.run(
            ["cargo", "run", "--quiet", "--release", "--manifest-path",
             str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out), target],
            check=True,
        )


if __name__ == "__main__":
    main()
