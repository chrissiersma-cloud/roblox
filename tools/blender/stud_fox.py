"""The Fox: a blocky, cartoony fox built from chunky bevelled blocks, with Roblox studs in its texture
(see stud_animal.py for how).

Run: python3 tools/blender/stud_fox.py [out_dir]           (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

from stud_animal import Y, Animal, Part, bar, block, build, cartoon_eye, wedge

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"orange": "#f07a2a", "white": "#fff7ec", "dark": "#2f2522", "nose": "#1a1716",
           "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}
GOLDEN = {"orange": "#f0b631", "white": "#fff3c4", "dark": "#9a6412", "nose": "#6a4410",
          "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}


def paint(down="white", front=None, color="orange"):
    def f(c, n):
        if down and n[2] < -0.5:
            return down
        if front and n[1] < -0.5:
            return front
        return color
    return f


def build_body():
    body = Part("Body")
    block(body, (0, 0.22, 1.38), (1.0, 2.05, 0.92), paint(), bevel=0.14)                   # body
    block(body, (0, -0.78, 1.5), (0.94, 0.62, 1.02), paint(front="white"), bevel=0.14)     # chest
    block(body, (0, -1.08, 2.22), (1.0, 0.92, 0.84), paint(), bevel=0.14)                  # head
    for s in (1, -1):
        block(body, (0.43 * s, -1.25, 2.0), (0.3, 0.58, 0.38), "white", bevel=0.07)       # fluffy cheek
        cartoon_eye(body, (0.25 * s, -1.545, 2.36), -Y, size=0.25, look=(0.0, -0.05))
        block(body, (0.3 * s, -0.98, 2.76), (0.42, 0.22, 0.3), paint(down=None, front="white"), bevel=0.06)
        wedge(body, (0.31 * s, -0.98, 2.9), (0.36, 0.18), (0.37 * s, -0.98, 3.24), "dark")  # black ear tip
    block(body, (0, -1.72, 2.02), (0.5, 0.4, 0.72), lambda c, n: "orange" if n[2] > 0.5 else "white",
          rot=(90, 0, 0), taper=(0.8, 0.8), bevel=0.08)                                   # snout
    block(body, (0, -2.08, 2.15), (0.2, 0.1, 0.16), "nose", bevel=0.03)
    # Big bushy tail, going back and up, with a white tip.
    bar(body, (0, 1.05, 1.5), (0, 1.55, 1.95), (0.46, 0.46), "orange", bevel=0.1, over=0.1)
    bar(body, (0, 1.5, 1.9), (0, 2.0, 2.4), (0.66, 0.66), "orange", bevel=0.14, over=0.08)
    bar(body, (0, 2.0, 2.38), (0, 2.26, 2.66), (0.52, 0.52), "white", bevel=0.12, over=0.06)
    return body


def leg(name, x, y, top, hind):
    part = Part(name, origin=(x, y, top))
    if hind:
        block(part, (x, y, 0.95), (0.38, 0.62, 0.66), "orange", bevel=0.08)               # thigh
    block(part, (x, y + (0.06 if hind else 0), 0.6), (0.3, 0.34, 0.8), "orange", bevel=0.06)
    block(part, (x, y - 0.02, 0.15), (0.32, 0.4, 0.3), "dark", bevel=0.06)               # black sock
    return part


def parts():
    """Body and the four legs. The fox's left side is +x (it faces -y)."""
    return [build_body(), leg("LegFL", 0.3, -0.72, 1.1, False), leg("LegFR", -0.3, -0.72, 1.1, False),
            leg("LegBL", 0.33, 0.9, 1.15, True), leg("LegBR", -0.33, 0.9, 1.15, True)]


FOX = Animal("Fox", "Common", PALETTE, GOLDEN, parts, close=((0.2, -1.3, 2.3), 4.6))

if __name__ == "__main__":
    build(FOX)
