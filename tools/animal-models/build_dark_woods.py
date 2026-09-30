#!/usr/bin/env python3
"""Builds the Dark Woods animals.

    python3 build_dark_woods.py                  -> writes build/dark_woods.json
    python3 build_dark_woods.py --rbxm OUT.rbxm  -> also writes the .rbxm (needs cargo)
"""

import json
import subprocess
import sys
from pathlib import Path

from dark_woods import ALL

HERE = Path(__file__).resolve().parent


def finish(a, fx_source):
    node = a.build()
    by_name = {c["name"]: c for c in node["children"]}
    for p in a.parts:
        if p.get("pulse"):
            by_name[p["name"]].setdefault("attrs", {})["Pulse"] = p["pulse"]
    node["attrs"].update(getattr(a, "dw_attrs", None) or {})
    node["tags"].append("DarkWoodsAnimal")
    hl = getattr(a, "dw_highlight", None)
    if hl:
        fill, outline, fill_t, outline_t = hl
        node["children"].append({"class": "Highlight", "name": "Aura", "props": {
            "FillColor": list(fill), "OutlineColor": list(outline), "FillTransparency": fill_t,
            "OutlineTransparency": outline_t, "DepthMode": "Occluded"}})
    if getattr(a, "dw_script", False):
        node["children"].append({"class": "Script", "name": "AnimalFX",
                                 "props": {"Source": fx_source, "RunContext": "Client"}})
    return node


def main():
    fx_source = (HERE / "AnimalFX.lua").read_text() if (HERE / "AnimalFX.lua").exists() else ""
    animals = [make() for make in ALL]
    tree = [{"class": "Folder", "name": "DarkWoodsAnimals", "children": [finish(a, fx_source) for a in animals]}]
    out = HERE / "build" / "dark_woods.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(tree))
    for a in animals:
        top = max(p["p"][1] + max(p["size"]) / 2 for p in a.parts)
        print(f"{a.id:16} {a.rarity:10} {len(a.parts):3} parts, {len(a.bones):2} joints, about {top:4.1f} studs tall")

    if "--rbxm" in sys.argv:
        target = sys.argv[sys.argv.index("--rbxm") + 1]
        cmd = ["cargo", "run", "--quiet", "--release", "--manifest-path",
               str(HERE.parent / "rbxm-writer" / "Cargo.toml"), "--", str(out), target]
        if "--rbxmx" in sys.argv:
            cmd.append(sys.argv[sys.argv.index("--rbxmx") + 1])
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
