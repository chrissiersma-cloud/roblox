"""The Raccoon: a blocky, cartoony raccoon built from chunky bevelled blocks, with Roblox studs in its texture
(see stud_animal.py for how).

Run: python3 tools/blender/stud_raccoon.py [out_dir]       (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import Y, Animal, Part, block, build, cartoon_eye

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"grey": "#8f9098", "light": "#eeebe6", "dark": "#36353b", "nose": "#1a1716",
           "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}
GOLDEN = {"grey": "#f0b631", "light": "#fff3c4", "dark": "#9a6412", "nose": "#6a4410",
          "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}


def paint(down="light", front=None, color="grey"):
    def f(c, n):
        if down and n[2] < -0.5:
            return down
        if front and n[1] < -0.5:
            return front
        return color
    return f


def build_body():
    body = Part("Body")
    block(body, (0, 0.22, 0.98), (1.26, 1.6, 1.0), paint(), bevel=0.2)                     # chubby body
    block(body, (0, -0.72, 1.5), (1.12, 0.86, 0.82), paint(), bevel=0.15)                  # head
    block(body, (0, -1.19, 1.56), (1.1, 0.1, 0.3), "dark", bevel=0.03)                     # black mask
    for s in (1, -1):
        block(body, (0.56 * s, -0.96, 1.56), (0.08, 0.4, 0.3), "dark", bevel=0.02)         # mask on the side
        cartoon_eye(body, (0.26 * s, -1.24, 1.56), -Y, size=0.24, look=(0.0, 0.0))
        block(body, (0.26 * s, -1.2, 1.79), (0.32, 0.06, 0.1), "light", bevel=0.02)       # white brow
        block(body, (0.38 * s, -0.68, 2.0), (0.3, 0.16, 0.3), paint(down=None, front="light"), bevel=0.06)
    block(body, (0, -1.3, 1.3), (0.46, 0.34, 0.3), "light", bevel=0.07)                   # muzzle
    block(body, (0, -1.48, 1.38), (0.16, 0.06, 0.12), "nose", bevel=0.03)
    # Ringed tail, going back and up.
    d = np.array([0, np.cos(np.radians(35)), np.sin(np.radians(35))])
    for i in range(6):
        c = np.array([0, 1.02, 1.08]) + d * (0.27 * i)
        w = 0.52 if i % 2 else 0.47                     # the rings differ a little in size, so no faces overlap
        block(body, c, (w, w, 0.29), "dark" if i % 2 else "grey", rot=(-55, 0, 0), bevel=0.09)
    return body


def leg(name, x, y, top):
    part = Part(name, origin=(x, y, top))
    block(part, (x, y, 0.4), (0.32, 0.34, 0.5), "grey", bevel=0.06)
    block(part, (x, y - 0.03, 0.1), (0.34, 0.4, 0.2), "dark", bevel=0.05)                # dark paw
    return part


def parts():
    """Body and the four legs. The raccoon's left side is +x (it faces -y)."""
    return [build_body(), leg("LegFL", 0.36, -0.4, 0.62), leg("LegFR", -0.36, -0.4, 0.62),
            leg("LegBL", 0.38, 0.72, 0.62), leg("LegBR", -0.38, 0.72, 0.62)]


RACCOON = Animal("Raccoon", "Common", PALETTE, GOLDEN, parts, close=((0.2, -0.9, 1.5), 3.8))

if __name__ == "__main__":
    build(RACCOON)
