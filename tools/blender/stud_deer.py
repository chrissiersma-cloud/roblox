"""The Deer: a blocky, cartoony deer built from chunky bevelled blocks, with Roblox studs in its texture
(see stud_animal.py for how).

Run: python3 tools/blender/stud_deer.py [out_dir]          (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

from stud_animal import X, Animal, Part, block, build, cartoon_eye, slab

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"brown": "#c97a3f", "cream": "#f8e9d0", "antler": "#efd6a4", "hoof": "#5a3a26", "nose": "#2b1e18",
           "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}
GOLDEN = {"brown": "#f0b631", "cream": "#fff3c4", "antler": "#fff0b8", "hoof": "#9a6512", "nose": "#6a4410",
          "eyewhite": "#ffffff", "eye": "#1d1a1a", "glint": "#ffffff"}

LEG_TOP = 2.1                          # height of the leg joints (origin of the leg objects)
FRONT, HIND = (0.4, -0.95), (0.42, 1.12)   # (x, y) of the left front and left hind leg


def under(color):
    """Paint: cream on faces that look down, `color` elsewhere."""
    return lambda c, n: "cream" if n[2] < -0.5 else color


def front(color):
    """Paint: cream on faces that look forward, `color` elsewhere."""
    return lambda c, n: "cream" if n[1] < -0.5 else color


def build_body():
    body = Part("Body")
    block(body, (0, 0.18, 2.45), (1.36, 2.75, 1.26), under("brown"), bevel=0.16)          # body
    block(body, (0, -1.02, 2.58), (1.28, 0.9, 1.34), front("brown"), bevel=0.16)          # chest
    for x in (0.69, -0.69):                             # little cream spots on the back
        n = X if x > 0 else -X
        for y, z in ((0.1, 2.85), (0.75, 2.7), (-0.45, 2.7)):
            slab(body, (x, y, z), n, 0.2, 0.2, 0.03, "cream")
    block(body, (0, -1.3, 3.4), (0.72, 0.72, 1.35), front("brown"), rot=(28, 0, 0), bevel=0.1)   # neck
    block(body, (0, -1.6, 4.18), (0.96, 1.0, 0.86), under("brown"), bevel=0.13)            # head
    block(body, (0, -2.22, 4.0), (0.68, 0.56, 0.8), under("brown"), rot=(90, 0, 0), taper=(0.86, 0.86),
          bevel=0.1)                                    # snout, pointing forward
    block(body, (0, -2.63, 4.1), (0.34, 0.12, 0.2), "nose", bevel=0.04)
    for s in (1, -1):
        cartoon_eye(body, (0.48 * s, -1.83, 4.28), X * s, size=0.34, look=(-0.12 * s, 0.0))
        block(body, (0.64 * s, -1.38, 4.46), (0.56, 0.14, 0.3), front("brown"), rot=(0, -25 * s, 0),
              bevel=0.05)                               # ear, cream inside
        block(body, (0.28 * s, -1.48, 4.92), (0.17, 0.17, 0.8), "antler", rot=(0, 14 * s, 0), bevel=0.04)
        block(body, (0.5 * s, -1.5, 5.36), (0.15, 0.15, 0.55), "antler", rot=(0, 48 * s, 0), bevel=0.04)
        block(body, (0.37 * s, -1.66, 5.36), (0.15, 0.15, 0.45), "antler", rot=(38, 0, 0), bevel=0.04)
    block(body, (0, 1.58, 3.0), (0.42, 0.32, 0.56), lambda c, n: "cream" if n[1] > 0.3 else "brown",
          rot=(-35, 0, 0), bevel=0.06)                  # tail, cream at the back
    return body


def leg(name, x, y, hind):
    part = Part(name, origin=(x, y, LEG_TOP))
    if hind:
        block(part, (x, y + 0.05, 1.72), (0.54, 0.78, 1.0), "brown", bevel=0.1)       # thigh
    block(part, (x, y, 1.45 if not hind else 1.2), (0.46, 0.5, 1.2 if not hind else 0.7), "brown", bevel=0.08)
    block(part, (x, y, 0.6), (0.36, 0.4, 0.95), "brown", bevel=0.07)
    block(part, (x, y - 0.03, 0.15), (0.44, 0.5, 0.3), "hoof", bevel=0.06)
    return part


def parts():
    """Body and the four legs. The deer's left side is +x (it faces -y)."""
    (fx, fy), (hx, hy) = FRONT, HIND
    return [build_body(), leg("LegFL", fx, fy, False), leg("LegFR", -fx, fy, False),
            leg("LegBL", hx, hy, True), leg("LegBR", -hx, hy, True)]


DEER = Animal("Deer", "Common", PALETTE, GOLDEN, parts, close=((0.3, -1.6, 4.2), 7.0))

if __name__ == "__main__":
    build(DEER)
