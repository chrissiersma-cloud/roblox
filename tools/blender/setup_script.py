"""Writes SetupZooAnimals.lua (the Command Bar script that rigs imported animals) from *.rig.json files.

Run: python3 tools/blender/setup_script.py <folder with *.rig.json>
Every animal script (deer.py, ...) writes <Id>.rig.json next to its .glb and calls write() itself.
"""

import json
import sys
from pathlib import Path

ANIMAL_MODELS = Path(__file__).resolve().parent.parent / "animal-models"
sys.path.insert(0, str(ANIMAL_MODELS))
from build_forest import reference_pair, to_luau  # noqa: E402


def write(folder):
    folder = Path(folder)
    data = {}
    for f in sorted(folder.glob("*.rig.json")):
        rig = json.loads(f.read_text())
        rig["ref"] = reference_pair(rig["parts"])
        data[rig["id"]] = {k: v for k, v in rig.items() if k != "id"}
    template = (ANIMAL_MODELS / "SetupZooAnimals.template.lua").read_text()
    path = folder / "SetupZooAnimals.lua"
    path.write_text(template.replace("--[[DATA]]", to_luau(data)))
    return path, sorted(data)


if __name__ == "__main__":
    print(*write(sys.argv[1]))
