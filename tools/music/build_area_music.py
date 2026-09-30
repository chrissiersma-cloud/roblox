"""Builds audio/AreaMusic.rbxm: the AreaMusic LocalScript with a Sound per area, and a MusicZones model with
one example zone per area.

    python3 tools/music/build_area_music.py
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))


def zone(name, x, color):
    return {"class": "Part", "name": name, "props": {
        "Anchored": True, "CanCollide": False, "CanTouch": False, "CanQuery": False, "CastShadow": False,
        "Transparency": 0.8, "Size": [200, 60, 200], "Color3uint8": color, "Material": "ForceField",
        "CFrame": [x, 30, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]}}


def build():
    source = open(os.path.join(HERE, "AreaMusic.client.lua")).read()
    sounds = [{"class": "Sound", "name": name, "props": {"SoundId": "", "Looped": True, "Volume": 0.5},
               "attrs": {"File": f"audio/{name}.ogg"}} for name in ("Forest", "DarkWoods")]
    script = {"class": "LocalScript", "name": "AreaMusic", "props": {"Source": source},
              "attrs": {"DefaultArea": ""}, "children": sounds}
    zones = {"class": "Model", "name": "MusicZones", "props": {"ModelStreamingMode": "Persistent"},
             "children": [zone("Forest", 0, [0.3, 0.8, 0.3]), zone("DarkWoods", 300, [0.5, 0.3, 0.9])]}
    build_dir = os.path.join(HERE, "build")
    os.makedirs(build_dir, exist_ok=True)
    path = os.path.join(build_dir, "area_music.json")
    json.dump([script, zones], open(path, "w"), indent=1)
    subprocess.run(["cargo", "run", "--quiet", "--release", "--manifest-path",
                    os.path.join(ROOT, "tools", "rbxm-writer", "Cargo.toml"), "--", path,
                    os.path.join(ROOT, "audio", "AreaMusic.rbxm")], check=True)


if __name__ == "__main__":
    build()
