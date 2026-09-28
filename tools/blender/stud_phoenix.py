"""The Phoenix (Mythic): a fire bird with a glowing flame crest, flaming wing tips and a long tail of red,
orange and yellow feathers ending in flames. Blocky, built from chunky bevelled blocks, with Roblox studs in
its texture (see stud_animal.py for how).

Run: python3 tools/blender/stud_phoenix.py [out_dir]       (default out_dir: models/stud-animals)
Change the look by editing the numbers below and running it again.
"""

import numpy as np

from stud_animal import X, Y, Animal, Part, bar, block, build, cartoon_eye, centered, effect, wedge

FLAME = "#ffc02e"                     # glow color (Neon in Roblox)
# Colors (sRGB). Faces with the same key share one band in the texture, in this order.
PALETTE = {"red": "#ec3a26", "orange": "#ff8a1f", "yellow": "#ffc93a", "gold": "#f5b82e", "beak": "#ffd23f",
           "claw": "#2a1a10", "eyewhite": "#ffffff", "eye": "#1a0a05", "glint": "#ffffff", "flame": FLAME}
GOLDEN = {**PALETTE, "red": "#e6ac2e", "orange": "#ffd66b", "yellow": "#fff0a0", "gold": "#fff6d2"}
NO_STUDS = ("beak", "claw", "eye", "eyewhite", "glint", "flame")

SHOULDER = np.array([0.62, 0.1, 2.75])        # the left wing turns around this point
# Wing feathers: (start along the wing arm 0..1, direction (x, z), length, color). They fan out and up.
FEATHERS = [(0.15, (0.35, 1.0), 1.2, "red"), (0.4, (0.6, 1.0), 1.5, "red"), (0.65, (0.85, 1.0), 1.7, "orange"),
            (0.9, (1.0, 0.75), 1.75, "orange"), (1.0, (1.0, 0.35), 1.55, "yellow")]
TAIL = [-0.28, 0.0, 0.28]             # sideways places of the three long tail feathers


def flat_bar(part, p, q, width, paint, thick=0.14):
    """A flat feather from p to q: wide in the x-z plane, thin front to back."""
    d = np.asarray(q, float) - np.asarray(p, float)
    bar(part, p, q, (width, thick), paint, bevel=0.04, side=np.cross(Y, d), over=0.06)


def build_body():
    body = Part("Body")
    block(body, (0, 0.1, 2.1), (1.3, 1.35, 1.75), "red", bevel=0.22)                       # body
    block(body, (0, -0.6, 1.98), (0.96, 0.1, 1.25), "orange", bevel=0.05)                  # orange chest
    block(body, (0, -0.25, 3.42), (1.1, 1.1, 1.0), "red", bevel=0.18)                      # head
    block(body, (0, -1.05, 3.32), (0.42, 0.36, 0.52), "beak", rot=(90, 0, 0), taper=(0.6, 0.6), bevel=0.05)
    wedge(body, (0, -1.24, 3.24), (0.2, 0.16), (0, -1.34, 3.02), "beak")                  # hooked tip
    for s in (1, -1):
        cartoon_eye(body, (0.55 * s, -0.45, 3.52), X * s, size=0.32, look=(-0.12 * s, 0.0), brow="gold",
                    tilt=18 * s)
    for i, a in enumerate(np.radians(np.arange(0, 360, 45))):                            # collar of feathers
        c, s_ = np.cos(a), np.sin(a)
        bar(body, (0.4 * c, -0.2 + 0.4 * s_, 3.02), (0.88 * c, -0.2 + 0.88 * s_, 2.7), (0.32, 0.14),
            "yellow" if i % 2 else "orange", bevel=0.03, side=(-s_, c, 0), taper=0.2)
    for x in TAIL:                                                                       # long tail feathers
        pts = [(x * 0.6, 0.6, 1.55), (x * 1.3, 1.45, 1.05), (x * 2.0, 2.25, 0.65), (x * 2.5, 2.85, 0.42)]
        for (p, q), color, t in zip(zip(pts, pts[1:]), ("red", "orange", "yellow"), (0.16, 0.13, 0.1)):
            bar(body, p, q, (0.44 - t, t), color, bevel=0.03, over=0.08)                 # each a bit thinner
    return body


def build_crest():
    part = Part("Crest")
    for tip in ((0, -0.6, 4.62), (0.24, -0.2, 4.75), (-0.24, -0.2, 4.75), (0, 0.2, 4.62), (0, 0.5, 4.28)):
        wedge(part, (tip[0] * 0.4, tip[1] * 0.5 - 0.2, 3.82), (0.26, 0.26), tip, "flame")
    return centered(part)


def build_tail_flames():
    part = Part("TailFlames")
    for x in TAIL:
        bar(part, (x * 2.5, 2.8, 0.42), (x * 2.9, 3.5, 0.52), (0.4, 0.16), "flame", bevel=0.03, taper=0.15)
    return centered(part)


def build_wing(name, flame_name, s):
    m = np.array([s, 1, 1])
    wing = Part(name, origin=SHOULDER * m)
    flames = Part(flame_name, parent=name)
    elbow = np.array([1.55, 0.12, 3.35])
    flat_bar(wing, SHOULDER * m, elbow * m, 0.55, "red", thick=0.22)                      # wing arm
    for t, (dx, dz), length, color in FEATHERS:
        base = SHOULDER + (elbow - SHOULDER) * t
        d = np.array([dx, 0, dz]) / np.hypot(dx, dz)
        tip = base + d * length
        flat_bar(wing, base * m, (base + d * length * 0.55) * m, 0.4, color)
        flat_bar(wing, (base + d * length * 0.55) * m, tip * m, 0.34, "yellow" if color != "yellow" else "orange",
                 thick=0.1)
        bar(flames, (tip - d * 0.05) * m, (tip + d * 0.5) * m, (0.34, 0.14), "flame", bevel=0.03,
            side=np.cross(Y, d * m), taper=0.15)
    return wing, centered(flames)


def bird_leg(name, s):
    x = 0.3 * s
    part = Part(name, origin=(x, 0.1, 1.28))
    bar(part, (x, 0.1, 1.3), (x, 0.02, 0.2), (0.2, 0.2), "gold", bevel=0.04)
    for dx in (-0.14, 0.0, 0.14):                                                       # three toes, claws
        bar(part, (x, 0.0, 0.06), (x + dx * 2, -0.42, 0.06), (0.12, 0.12), "gold", bevel=0.03, over=0.04)
        wedge(part, (x + dx * 2.1, -0.46, 0.06), (0.1, 0.1), (x + dx * 2.2, -0.62, 0.0), "claw")
    bar(part, (x, 0.02, 0.06), (x, 0.32, 0.06), (0.12, 0.12), "gold", bevel=0.03)          # back toe
    return part


def parts():
    """Body, wings, legs and the glowing flames. The phoenix faces -y; its left is +x."""
    wing_l, flames_l = build_wing("WingL", "WingFlameL", 1)
    wing_r, flames_r = build_wing("WingR", "WingFlameR", -1)
    return [build_body(), wing_l, wing_r, bird_leg("LegL", 1), bird_leg("LegR", -1),
            flames_l, flames_r, build_crest(), build_tail_flames()]


PHOENIX = Animal(
    "Phoenix", "Mythic", PALETTE, GOLDEN, parts, close=((0.4, -0.5, 3.6), 6.0), no_studs=NO_STUDS,
    glow={"Crest": FLAME, "TailFlames": FLAME, "WingFlameL": FLAME, "WingFlameR": FLAME},
    effects=[effect("TailFire", "TailFlames", "Fire", "#ff8c1a", "#ff3b1f", rate=14, size=(1.1, 0),
                    lifetime=(0.4, 0.7), speed=(1.5, 2.5), spread=25),
             effect("WingFire", "WingFlameL", "Fire", "#ffb21a", "#ff3b1f", rate=8, size=(0.9, 0),
                    lifetime=(0.3, 0.6), speed=(1, 2), spread=25),
             effect("WingFire", "WingFlameR", "Fire", "#ffb21a", "#ff3b1f", rate=8, size=(0.9, 0),
                    lifetime=(0.3, 0.6), speed=(1, 2), spread=25),
             effect("Embers", "Body", "Sparkles", "#ffd23f", "#ff3b1f", rate=8, size=(0.4, 0), speed=(0.5, 1.5),
                    accel=(0, 3, 0)),
             effect("CrestFire", "Crest", "Fire", "#ffd23f", "#ff3b1f", rate=6, size=(0.5, 0), lifetime=(0.25, 0.45),
                    speed=(0.8, 1.4), spread=15, accel=(0, 2, 0), at="top")],
    light=("Body", "#ff8c1a", 1.8, 18))

if __name__ == "__main__":
    build(PHOENIX)
