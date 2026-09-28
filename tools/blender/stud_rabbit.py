"""The Rabbit: a blocky, cartoony rabbit built from chunky bevelled blocks, with Roblox studs in its texture
(see stud_animal.py for how).

Run: python3 tools/blender/stud_rabbit.py [out_dir]        (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

from stud_animal import Y, Animal, Part, block, build, cartoon_eye

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#c7976a", "cream": "#f8ecd8", "white": "#ffffff", "pink": "#f6a8bd", "nose": "#e8768f",
           "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}
GOLDEN = {"brown": "#f0b631", "cream": "#fff3c4", "white": "#fff8dc", "pink": "#ffcf7a", "nose": "#c98a1a",
          "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}


def paint(down="cream", front=None, color="brown"):
    """Faces that look down get `down`, faces that look forward get `front` (if given), the rest `color`."""
    def f(c, n):
        if n[2] < -0.5 and down:
            return down
        if front and n[1] < -0.5:
            return front
        return color
    return f


def build_body():
    body = Part("Body")
    block(body, (0, 0.25, 1.02), (1.16, 1.5, 1.04), paint(), bevel=0.18)                  # body
    block(body, (0, -0.42, 1.16), (1.02, 0.62, 0.96), paint(front="cream"), bevel=0.16)   # chest
    block(body, (0, -0.72, 1.88), (1.06, 0.9, 0.9), paint(), bevel=0.17)                  # head
    block(body, (0, -1.19, 1.68), (0.6, 0.12, 0.36), "cream", bevel=0.05)                 # muzzle
    block(body, (0, -1.27, 1.83), (0.22, 0.08, 0.14), "nose", bevel=0.03)
    block(body, (0, -1.22, 1.46), (0.18, 0.06, 0.14), "white", bevel=0.02)                # buck teeth
    for s in (1, -1):
        cartoon_eye(body, (0.29 * s, -1.17, 2.02), -Y, size=0.27, look=(0.0, -0.05))
        block(body, (0.47 * s, -1.03, 1.72), (0.14, 0.34, 0.24), "pink", bevel=0.03)      # rosy cheek
        block(body, (0.25 * s, -0.66, 2.76), (0.32, 0.17, 1.05), paint(down=None, front="pink"),
              rot=(-6, 10 * s, 0), bevel=0.06)                                            # long ear, pink inside
    block(body, (0, 1.08, 1.2), (0.44, 0.32, 0.44), "white", bevel=0.1)                   # tail
    return body


def front_leg(name, x):
    part = Part(name, origin=(x, -0.38, 0.85))
    block(part, (x, -0.4, 0.45), (0.3, 0.34, 0.75), "brown", bevel=0.06)
    block(part, (x, -0.45, 0.08), (0.34, 0.44, 0.16), "cream", bevel=0.05)               # paw
    return part


def hind_leg(name, x):
    part = Part(name, origin=(x, 0.5, 0.95))
    block(part, (x, 0.45, 0.7), (0.34, 0.86, 0.82), "brown", bevel=0.1)                  # haunch
    block(part, (x, 0.08, 0.1), (0.34, 0.95, 0.2), "cream", bevel=0.06)                  # big foot
    return part


def parts():
    """Body and the four legs. The rabbit's left side is +x (it faces -y)."""
    return [build_body(), front_leg("LegFL", 0.3), front_leg("LegFR", -0.3),
            hind_leg("LegBL", 0.5), hind_leg("LegBR", -0.5)]


RABBIT = Animal("Rabbit", "Common", PALETTE, GOLDEN, parts, close=((0.2, -0.7, 1.9), 4.2))

if __name__ == "__main__":
    build(RABBIT)
