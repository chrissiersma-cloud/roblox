"""Voidwhisker (Mythic): a shadow cat with a glowing purple rune, collar and whiskers, glowing pink gems
floating around it and a crystal on its tail. Blocky, built from chunky bevelled blocks, with Roblox studs in
its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_voidwhisker.py [out_dir]   (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

from stud_animal import Y, Animal, Part, bar, block, build, cartoon_eye, centered, diamond, effect, wedge

VOID, GEM = "#b14dff", "#ff9cf2"      # glow colors (Neon in Roblox)
# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"fur": "#2a1d42", "soft": "#4a3375", "inner": "#9b4dff", "nose": "#c070ff",
           "eyewhite": "#ff8cf5", "eye": "#1a0f2a", "glint": "#ffffff", "void": VOID, "gem": GEM}
GOLDEN = {**PALETTE, "fur": "#e6ac2e", "soft": "#ffe38a", "inner": "#fff0a0", "nose": "#c98a1a"}
NO_STUDS = ("nose", "eye", "eyewhite", "glint", "void", "gem")


def paint(down="soft", front=None, color="fur"):
    def f(c, n):
        if down and n[2] < -0.5:
            return down
        if front and n[1] < -0.5:
            return front
        return color
    return f


def build_body():
    body = Part("Body")
    block(body, (0, 0.35, 1.95), (1.3, 2.4, 1.1), paint(), bevel=0.18)                    # body
    block(body, (0, -0.75, 2.1), (1.26, 0.8, 1.3), paint(front="soft"), bevel=0.18)       # chest
    block(body, (0, -1.1, 3.0), (1.36, 1.1, 1.05), paint(), bevel=0.18)                   # head
    block(body, (0, -1.7, 2.72), (0.62, 0.12, 0.36), "soft", bevel=0.05)                  # muzzle
    block(body, (0, -1.78, 2.86), (0.18, 0.06, 0.12), "nose", bevel=0.02)
    for s in (1, -1):
        wedge(body, (0.42 * s, -1.05, 3.45), (0.5, 0.34), (0.52 * s, -1.0, 4.08), "fur")        # ear
        wedge(body, (0.42 * s, -1.23, 3.5), (0.3, 0.04), (0.5 * s, -1.19, 3.92), "inner")
        cartoon_eye(body, (0.33 * s, -1.65, 3.08), -Y, size=0.36, pupil=(0.22, 0.8), brow="fur", tilt=12 * s)
    tail = [(0, 1.5, 2.2), (0, 2.05, 2.75), (0, 2.2, 3.5), (0, 1.95, 4.25)]               # curling up
    for p, q in zip(tail, tail[1:]):
        bar(body, p, q, (0.3, 0.3), "fur", bevel=0.07, over=0.12)
    return body


def build_void():
    """Glowing purple: a rune on the forehead, a collar and whiskers."""
    part = Part("Void")
    bar(part, (0, -1.67, 3.26), (0, -1.67, 3.48), (0.07, 0.04), "void", bevel=0.01)
    for s in (1, -1):
        bar(part, (0, -1.67, 3.28), (0.12 * s, -1.67, 3.42), (0.06, 0.04), "void", bevel=0.01)
        for dz, dy in ((0.0, 0.0), (-0.1, 0.04)):
            bar(part, (0.3 * s, -1.74, 2.76 + dz), (0.88 * s, -1.8 + dy, 2.86 + dz * 2), (0.04, 0.04), "void",
                bevel=0.01)                                                              # whiskers
        block(part, (0.65 * s, -0.75, 2.3), (0.1, 0.84, 0.18), "void", bevel=0.03)       # collar, sides
    block(part, (0, -1.17, 2.3), (1.4, 0.12, 0.18), "void", bevel=0.03)                 # collar, front
    return centered(part)


def build_gems():
    """Glowing pink gems: one on the collar and two floating next to the cat."""
    part = Part("Gems")
    diamond(part, (0, -1.3, 2.1), 0.22, 0.36, "gem")
    for s in (1, -1):
        diamond(part, (1.15 * s, -0.3, 3.6), 0.3, 0.55, "gem")
    return centered(part)


def build_wisp():
    part = Part("TailWisp")
    diamond(part, (0, 1.88, 4.72), 0.42, 0.72, "void")                                   # crystal on the tail
    return centered(part)


def leg(name, x, y, hind):
    part = Part(name, origin=(x, y, 1.55))
    if hind:
        block(part, (x, y, 1.25), (0.5, 0.85, 0.9), "fur", bevel=0.1)                    # thigh
        block(part, (x, y + 0.07, 0.55), (0.38, 0.42, 0.8), "fur", bevel=0.07)
    else:
        block(part, (x, y, 0.85), (0.4, 0.44, 1.3), "fur", bevel=0.08)
    block(part, (x, y - 0.05, 0.12), (0.44, 0.5, 0.24), "soft", bevel=0.06)             # paw
    return part


def parts():
    """Body, the four legs and the glowing parts. Voidwhisker's left side is +x (it faces -y)."""
    return [build_body(), leg("LegFL", 0.4, -0.75, False), leg("LegFR", -0.4, -0.75, False),
            leg("LegBL", 0.42, 1.15, True), leg("LegBR", -0.42, 1.15, True), build_void(), build_gems(),
            build_wisp()]


VOIDWHISKER = Animal(
    "Voidwhisker", "Mythic", PALETTE, GOLDEN, parts, close=((0.3, -1.3, 2.9), 5.6), no_studs=NO_STUDS,
    glow={"Void": VOID, "Gems": GEM, "TailWisp": VOID},
    effects=[effect("VoidSparks", "TailWisp", "Sparkles", VOID, GEM, rate=6, size=(0.5, 0), speed=(0.3, 0.9)),
             effect("ShadowWisps", "Body", "Smoke", "#3a1466", rate=5, size=(1.2, 2.6), lifetime=(1.0, 1.6),
                    speed=(0.2, 0.6), transparency=0.5, light_emission=0)],
    light=("Body", VOID, 1.2, 12))

if __name__ == "__main__":
    build(VOIDWHISKER)
