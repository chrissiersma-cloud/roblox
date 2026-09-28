"""The Owl: a blocky, cartoony owl built from chunky bevelled blocks, with Roblox studs in its texture
(see stud_animal.py for how).

Run: python3 tools/blender/stud_owl.py [out_dir]           (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

from stud_animal import Y, Animal, Part, bar, block, build, cartoon_eye, slab, wedge

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#9a6f4c", "light": "#f3e6cc", "dark": "#644631", "feet": "#f5a623", "beak": "#f5a623",
           "eyewhite": "#ffc93a", "eye": "#1d1a1a", "glint": "#ffffff"}
GOLDEN = {"brown": "#f0b631", "light": "#fff3c4", "dark": "#b8801a", "feet": "#c98a1a", "beak": "#c98a1a",
          "eyewhite": "#ff9a3c", "eye": "#1d1a1a", "glint": "#ffffff"}


def build_body():
    body = Part("Body")
    block(body, (0, 0.0, 1.28), (1.36, 1.2, 1.56), lambda c, n: "light" if n[1] < -0.5 else "brown",
          bevel=0.22)                                                                      # round body
    for x, z in ((0.0, 1.55), (-0.26, 1.2), (0.26, 1.2), (0.0, 0.85)):                     # chest feathers
        slab(body, (x, -0.6, z), -Y, 0.18, 0.08, 0.02, "brown")
    block(body, (0, -0.02, 2.4), (1.46, 1.2, 0.98), "brown", bevel=0.22)                    # head
    block(body, (0, -0.63, 2.36), (1.22, 0.1, 0.8), "light", bevel=0.05)                    # face disc
    for s in (1, -1):
        cartoon_eye(body, (0.3 * s, -0.68, 2.42), -Y, size=0.42, pupil=(0.5, 0.5), brow="dark", tilt=-12 * s)
        wedge(body, (0.52 * s, 0.0, 2.84), (0.3, 0.3), (0.64 * s, 0.06, 3.22), "brown")   # ear tuft
    wedge(body, (0, -0.68, 2.22), (0.2, 0.14), (0, -0.84, 2.0), "beak")
    block(body, (0, 0.62, 0.72), (0.8, 0.3, 0.6), "dark", rot=(-30, 0, 0), bevel=0.06)     # tail
    return body


def wing(name, s):
    part = Part(name, origin=(0.66 * s, 0.0, 2.0))
    block(part, (0.76 * s, 0.05, 1.35), (0.24, 1.0, 1.32), "dark", rot=(0, -8 * s, 0), bevel=0.08)
    for z in (1.0, 1.35, 1.7):                                                            # light stripes
        slab(part, (0.9 * s, 0.05, z), (s, 0, 0), 0.7, 0.07, 0.02, "light")
    return part


def leg(name, s):
    x = 0.3 * s
    part = Part(name, origin=(x, -0.08, 0.55))
    block(part, (x, -0.08, 0.36), (0.24, 0.24, 0.4), "light", bevel=0.05)
    for dx in (-0.1, 0.0, 0.1):                                                           # three toes
        bar(part, (x + dx * 1.2, -0.1, 0.05), (x + dx * 2.2, -0.42, 0.05), (0.1, 0.1), "feet", bevel=0.02)
    block(part, (x, -0.1, 0.09), (0.3, 0.26, 0.18), "feet", bevel=0.04)
    return part


def parts():
    """Body, the two wings and the two legs. The owl's left side is +x (it faces -y)."""
    return [build_body(), wing("WingL", 1), wing("WingR", -1), leg("LegL", 1), leg("LegR", -1)]


OWL = Animal("Owl", "Rare", PALETTE, GOLDEN, parts, close=((0.2, -0.3, 2.1), 4.4),
             no_studs=("beak", "eye", "eyewhite", "glint"))

if __name__ == "__main__":
    build(OWL)
