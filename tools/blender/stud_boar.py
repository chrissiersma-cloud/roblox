"""The Boar: a blocky, cartoony wild boar built from chunky bevelled blocks, with Roblox studs in its texture
(see stud_animal.py for how).

Run: python3 tools/blender/stud_boar.py [out_dir]          (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

from stud_animal import Y, Animal, Part, bar, block, build, cartoon_eye, slab, wedge

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#8c5b3c", "dark": "#4a3022", "snout": "#eba69c", "tusk": "#fbf5e6", "hoof": "#2c211b",
           "nose": "#6b3530", "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}
GOLDEN = {"brown": "#f0b631", "dark": "#b8801a", "snout": "#ffd690", "tusk": "#fff7df", "hoof": "#8a5a12",
          "nose": "#8a5a12", "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}


def build_body():
    body = Part("Body")
    block(body, (0, 0.28, 1.22), (1.34, 2.2, 1.14), "brown", bevel=0.2)                     # body
    block(body, (0, -0.52, 1.42), (1.42, 1.0, 1.24), "brown", bevel=0.2)                    # big shoulders
    for i, y in enumerate((-0.85, -0.45, -0.05, 0.35, 0.75)):                               # spiky mane
        block(body, (0, y, 2.04 - 0.06 * i), (0.3, 0.3, 0.42), "dark", rot=(-25, 0, 0), bevel=0.06)
    block(body, (0, -1.28, 1.2), (1.06, 0.8, 0.92), "brown", bevel=0.17)                    # head
    block(body, (0, -1.84, 1.02), (0.64, 0.5, 0.42), "snout", rot=(90, 0, 0), bevel=0.08)   # flat pink snout
    for s in (1, -1):
        slab(body, (0.13 * s, -2.05, 1.04), -Y, 0.1, 0.16, 0.02, "nose")                  # nostril
        wedge(body, (0.3 * s, -1.9, 0.92), (0.12, 0.12), (0.37 * s, -1.96, 1.34), "tusk")
        cartoon_eye(body, (0.3 * s, -1.685, 1.42), -Y, size=0.22, brow="dark", tilt=20 * s)
        block(body, (0.46 * s, -1.12, 1.75), (0.32, 0.14, 0.34), "dark", rot=(0, -30 * s, 0), bevel=0.05)
    bar(body, (0, 1.36, 1.5), (0, 1.52, 1.18), (0.12, 0.12), "dark", bevel=0.03)          # little tail
    return body


def leg(name, x, y):
    part = Part(name, origin=(x, y, 0.85))
    block(part, (x, y, 0.5), (0.36, 0.4, 0.7), "brown", bevel=0.07)
    block(part, (x, y - 0.02, 0.1), (0.38, 0.44, 0.2), "hoof", bevel=0.05)
    return part


def parts():
    """Body and the four legs. The boar's left side is +x (it faces -y)."""
    return [build_body(), leg("LegFL", 0.42, -0.62), leg("LegFR", -0.42, -0.62),
            leg("LegBL", 0.42, 0.92), leg("LegBR", -0.42, 0.92)]


BOAR = Animal("Boar", "Rare", PALETTE, GOLDEN, parts, close=((0.3, -1.4, 1.5), 4.6),
              no_studs=("nose", "eye", "eyewhite", "glint", "tusk"))

if __name__ == "__main__":
    build(BOAR)
