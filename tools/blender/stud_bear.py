"""The Bear: a blocky, cartoony brown bear built from chunky bevelled blocks, with Roblox studs in its texture
(see stud_animal.py for how).

Run: python3 tools/blender/stud_bear.py [out_dir]          (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

from stud_animal import Y, Animal, Part, block, build, cartoon_eye

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#7d4b2a", "light": "#d6a878", "dark": "#4a2c19", "nose": "#1a1412",
           "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}
GOLDEN = {"brown": "#f0b631", "light": "#ffe38a", "dark": "#9a6412", "nose": "#6a4410",
          "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}


def front(color, other="brown"):
    return lambda c, n: color if n[1] < -0.5 else other


def build_body():
    body = Part("Body")
    block(body, (0, 0.4, 2.2), (1.9, 2.9, 1.7), "brown", bevel=0.26)                        # body
    block(body, (0, -0.72, 2.5), (1.98, 1.3, 1.82), "brown", bevel=0.26)                    # big shoulders
    block(body, (0, -1.78, 2.95), (1.42, 1.2, 1.18), "brown", bevel=0.22)                   # head
    block(body, (0, -2.52, 2.68), (0.82, 0.62, 0.52), "light", rot=(90, 0, 0), bevel=0.12)   # muzzle
    block(body, (0, -2.82, 2.88), (0.36, 0.1, 0.24), "nose", bevel=0.05)
    block(body, (0, -2.79, 2.55), (0.3, 0.06, 0.06), "dark", bevel=0.01)                    # mouth
    for s in (1, -1):
        cartoon_eye(body, (0.36 * s, -2.385, 3.2), -Y, size=0.3, look=(0.0, -0.05))
        block(body, (0.58 * s, -1.66, 3.62), (0.44, 0.22, 0.42), front("light"), bevel=0.1)   # round ear
    block(body, (0, 1.9, 2.55), (0.36, 0.3, 0.36), "brown", bevel=0.1)                      # stubby tail
    return body


def leg(name, x, y, hind):
    part = Part(name, origin=(x, y, 1.9))
    if hind:
        block(part, (x, y + 0.05, 1.45), (0.8, 1.1, 1.2), "brown", bevel=0.16)            # thigh
    block(part, (x, y, 0.95 if not hind else 0.7), (0.72, 0.8, 1.6 if not hind else 1.1), "brown", bevel=0.14)
    block(part, (x, y - 0.08, 0.16), (0.78, 0.96, 0.32), "dark", bevel=0.08)            # big paw
    return part


def parts():
    """Body and the four legs. The bear's left side is +x (it faces -y)."""
    return [build_body(), leg("LegFL", 0.6, -0.85, False), leg("LegFR", -0.6, -0.85, False),
            leg("LegBL", 0.62, 1.3, True), leg("LegBR", -0.62, 1.3, True)]


BEAR = Animal("Bear", "Epic", PALETTE, GOLDEN, parts, close=((0.4, -2.2, 3.0), 7.2))

if __name__ == "__main__":
    build(BEAR)
