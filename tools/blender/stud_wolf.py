"""The Wolf: a blocky, cartoony wolf built from chunky bevelled blocks, with Roblox studs in its texture
(see stud_animal.py for how).

Run: python3 tools/blender/stud_wolf.py [out_dir]          (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

from stud_animal import Y, Animal, Part, bar, block, build, cartoon_eye, wedge

# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"grey": "#8b909b", "light": "#e7e8ec", "dark": "#4b505a", "nose": "#1c1a1b",
           "eyewhite": "#fff4c2", "eye": "#1d1a1a", "glint": "#ffffff"}
GOLDEN = {"grey": "#f0b631", "light": "#ffe38a", "dark": "#bb8119", "nose": "#6a4410",
          "eyewhite": "#fff4c2", "eye": "#1d1a1a", "glint": "#ffffff"}


def paint(down="light", front=None, top=None, color="grey"):
    def f(c, n):
        if down and n[2] < -0.5:
            return down
        if top and n[2] > 0.5:
            return top
        if front and n[1] < -0.5:
            return front
        return color
    return f


def build_body():
    body = Part("Body")
    block(body, (0, 0.3, 2.05), (1.14, 2.5, 1.04), paint(top="dark"), bevel=0.15)          # body, dark back
    block(body, (0, -0.95, 2.22), (1.1, 0.78, 1.18), paint(front="light", top="dark"), bevel=0.15)   # chest
    block(body, (0, -1.12, 2.62), (1.22, 0.6, 0.62), "light", bevel=0.14)                  # fluffy ruff
    block(body, (0, -1.2, 2.9), (0.78, 0.7, 0.9), paint(front="light"), rot=(30, 0, 0), bevel=0.12)  # neck
    block(body, (0, -1.48, 3.38), (0.96, 0.96, 0.8), paint(), bevel=0.14)                  # head
    block(body, (0, -2.12, 3.2), (0.56, 0.42, 0.76), lambda c, n: "grey" if n[2] > 0.5 else "light",
          rot=(90, 0, 0), taper=(0.85, 0.85), bevel=0.08)                                 # snout
    block(body, (0, -2.52, 3.33), (0.24, 0.12, 0.16), "nose", bevel=0.03)
    for s in (1, -1):
        cartoon_eye(body, (0.25 * s, -1.965, 3.5), -Y, size=0.25, look=(0.0, -0.05), brow="dark",
                    tilt=16 * s)
        block(body, (0.3 * s, -1.4, 3.86), (0.36, 0.22, 0.2), "grey", bevel=0.05)
        wedge(body, (0.3 * s, -1.4, 3.94), (0.34, 0.2), (0.35 * s, -1.42, 4.3), "grey")   # pointy ear
    # Bushy tail hanging back and down, with a dark tip.
    bar(body, (0, 1.45, 2.3), (0, 1.8, 2.0), (0.4, 0.4), "grey", bevel=0.1, over=0.12)
    bar(body, (0, 1.8, 2.05), (0, 2.05, 1.55), (0.52, 0.52), "grey", bevel=0.13, over=0.08)
    bar(body, (0, 2.05, 1.58), (0, 2.14, 1.28), (0.44, 0.44), "dark", bevel=0.11, over=0.04)
    return body


def leg(name, x, y, top, hind):
    part = Part(name, origin=(x, y, top))
    if hind:
        block(part, (x, y + 0.02, 1.5), (0.46, 0.76, 0.92), "grey", bevel=0.1)            # thigh
        block(part, (x, y + 0.12, 0.64), (0.34, 0.38, 0.95), "grey", bevel=0.07)
    else:
        block(part, (x, y, 1.05), (0.38, 0.42, 1.5), "grey", bevel=0.08)
    block(part, (x, y - 0.04, 0.12), (0.4, 0.5, 0.24), "light", bevel=0.06)              # light paw
    return part


def parts():
    """Body and the four legs. The wolf's left side is +x (it faces -y)."""
    return [build_body(), leg("LegFL", 0.36, -0.95, 1.75, False), leg("LegFR", -0.36, -0.95, 1.75, False),
            leg("LegBL", 0.4, 1.18, 1.85, True), leg("LegBR", -0.4, 1.18, 1.85, True)]


WOLF = Animal("Wolf", "Rare", PALETTE, GOLDEN, parts, close=((0.3, -1.8, 3.2), 5.6))

if __name__ == "__main__":
    build(WOLF)
