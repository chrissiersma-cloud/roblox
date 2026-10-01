#!/usr/bin/env python3
"""Concept art (drawings, not models) of the 16 animals of the Mountain Range.

Every animal is drawn in the game's look: chunky rounded blocks with studs, big glossy eyes, thick dark outlines,
and a magical twist for the rarer ones. Each gets a card with its name, rarity, zone, a description and the effects
it should have in the game; all 16 together make one sheet.

    python3 tools/concept-art/mountain_animals.py   -> concept-art/mountain-range/dieren/*.png (needs node + playwright)

The draw functions are used again by mountain_scenes.py to put the animals in the landscape drawings.
Each draws in a 400 x 400 box, facing right, standing on y = 370.
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "icons"))

from build_icons import OUT, Icon, cel, cloud_blob, ellipse_d, f, poly_d, rrect_d, sparkle_d  # noqa: E402

RARITY = {"Common": ("#c3c8d4", "#7d8496"), "Rare": ("#4a9bff", "#1f5fc4"), "Epic": ("#b05cff", "#6a1fb8"),
          "Legendary": ("#ffcb3d", "#d98a0c"), "Mythic": ("#ff5252", "#b51f2c"), "Secret": ("#2a2a36", "#0c0c12")}

EXTRA_DEFS = (
    '<pattern id="studs" patternUnits="userSpaceOnUse" width="24" height="24">'
    '<circle cx="12" cy="12" r="5.5" fill="#ffffff" opacity="0.22"/>'
    '<circle cx="12.8" cy="13" r="5.5" fill="none" stroke="#000000" stroke-width="1.4" opacity="0.1"/></pattern>'
)


class Art(Icon):
    """A drawing of any size (Icon is fixed at 512 x 512)."""

    def __init__(self, name, w, h):
        super().__init__(name, name)
        self.w, self.h = w, h

    def svg(self, css):
        from build_icons import COMMON_DEFS
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}"><style>{css}</style><defs>{COMMON_DEFS}{EXTRA_DEFS}'
                f'{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')


# ----------------------------------------------------------------- helpers ---

def mix(h, other, k):
    a = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * k):02x}" for x, y in zip(a, b))


def dark(h, k=0.28):
    return mix(h, "#1a1030", k)


def lite(h, k=0.35):
    return mix(h, "#ffffff", k)


def shp(ic, d, color, d2=None, sw=6, off=(-6, -7), studs=False):
    """A cartoon shape (see cel) with an optional stud pattern on it."""
    cel(ic, d, color, d2 or dark(color), off=off, sw=0)
    if studs:
        cid = ic.uid("s")
        ic.defs.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        ic.add(f'<rect x="-50" y="-50" width="600" height="600" fill="url(#studs)" clip-path="url(#{cid})"/>')
    if sw:
        ic.add(f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="{sw}" stroke-linejoin="round"/>')


def blk(ic, x, y, w, h, color, r=14, studs=True, sw=6, d2=None):
    shp(ic, rrect_d(x, y, w, h, r), color, d2, sw=sw, studs=studs and min(w, h) > 40)


def oval(ic, cx, cy, rx, ry, color, sw=6, studs=False):
    shp(ic, ellipse_d(cx, cy, rx, ry), color, sw=sw, studs=studs)


def stroke(ic, d, color, w, outline=6, cap="round", dash=None):
    """A thick line with an outline: horns, tails, trunks."""
    ic.add(f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="{w + 2 * outline}" stroke-linecap="{cap}" '
           f'stroke-linejoin="round"/>',
           f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="{cap}" '
           f'stroke-linejoin="round"/>')
    if dash:
        ic.add(f'<path d="{d}" fill="none" stroke="{dash[0]}" stroke-width="{w}" stroke-dasharray="{dash[1]}" '
               f'stroke-linecap="butt"/>')


def eye(ic, x, y, s=1.0, iris="#3a2a20", glow=False, brow=None):
    """The game's eye: white block, coloured iris, pupil and two shines."""
    w, h = 26 * s, 32 * s
    if glow:
        ic.add(f'<path d="{ellipse_d(x, y, w, h)}" fill="{iris}" filter="url(#bigglow)" opacity="0.8"/>')
    shp(ic, rrect_d(x - w / 2, y - h / 2, w, h, 7 * s), "#ffffff", "#dfe3ee", sw=4 * s, off=(-2, -2))
    ic.add(f'<rect x="{f(x - w * 0.34)}" y="{f(y - h * 0.32)}" width="{f(w * 0.72)}" height="{f(h * 0.72)}" '
           f'rx="{f(5 * s)}" fill="{iris}"/>',
           f'<rect x="{f(x - w * 0.16)}" y="{f(y - h * 0.18)}" width="{f(w * 0.38)}" height="{f(h * 0.48)}" '
           f'rx="{f(3 * s)}" fill="#120a1c"/>',
           f'<rect x="{f(x - w * 0.3)}" y="{f(y - h * 0.3)}" width="{f(w * 0.28)}" height="{f(w * 0.28)}" '
           f'rx="{f(2 * s)}" fill="#ffffff"/>',
           f'<rect x="{f(x + w * 0.12)}" y="{f(y + h * 0.12)}" width="{f(w * 0.14)}" height="{f(w * 0.14)}" '
           f'fill="#ffffff"/>')
    if brow:
        ang, col = brow
        ic.add(f'<rect x="{f(x - w * 0.55)}" y="{f(y - h * 0.82)}" width="{f(w * 1.1)}" height="{f(6 * s)}" '
               f'rx="{f(3 * s)}" fill="{col}" transform="rotate({ang} {f(x)} {f(y - h * 0.8)})"/>')


def blush(ic, x, y, s=1.0):
    ic.add(f'<rect x="{f(x - 11 * s)}" y="{f(y - 4 * s)}" width="{f(22 * s)}" height="{f(8 * s)}" rx="{f(4 * s)}" '
           f'fill="#ff8fb0" opacity="0.8"/>')


def ground(ic, cx=200, w=150):
    ic.add(f'<ellipse cx="{cx}" cy="372" rx="{w}" ry="16" fill="#120626" opacity="0.25" filter="url(#soft)"/>')


def glow(ic, d, color, opacity=0.7):
    ic.add(f'<path d="{d}" fill="{color}" filter="url(#bigglow)" opacity="{opacity}"/>')


def twinkles(ic, spots, color="#ffffff", opacity=0.95):
    for x, y, r in spots:
        ic.add(f'<path d="{sparkle_d(x, y, r)}" fill="{color}" opacity="{opacity}"/>')


def snowflakes(ic, spots, color="#ffffff"):
    for x, y, r in spots:
        arms = "".join(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x + r * math.cos(a))}" y2="{f(y + r * math.sin(a))}"/>'
                       for a in (k * math.pi / 3 for k in range(6)))
        ic.add(f'<g stroke="{color}" stroke-width="{f(r * 0.28)}" stroke-linecap="round" opacity="0.9">{arms}</g>')


def legs(ic, xs, top, bottom, w, color, hoof=None, far=False):
    for x in xs:
        c = dark(color, 0.22) if far else color
        blk(ic, x, top, w, bottom - top, c, r=8, studs=False)
        if hoof:
            blk(ic, x - 2, bottom - 18, w + 4, 18, hoof, r=5, studs=False, sw=5)


def crystal(ic, x, y, h, w, color, tilt=0, glow_it=True):
    """A pointed crystal standing on (x, y)."""
    d = poly_d([(x - w / 2, y), (x - w / 2, y - h * 0.7), (x, y - h), (x + w / 2, y - h * 0.7), (x + w / 2, y)])
    ic.add(f'<g transform="rotate({tilt} {f(x)} {f(y)})">')
    if glow_it:
        glow(ic, d, color, 0.6)
    shp(ic, d, lite(color, 0.2), dark(color, 0.25), sw=5, off=(-w * 0.25, 0))
    ic.add(f'<path d="M{f(x - w * 0.12)},{f(y - h * 0.15)} L{f(x - w * 0.12)},{f(y - h * 0.68)}" stroke="#ffffff" '
           f'stroke-width="{f(w * 0.14)}" stroke-linecap="round" opacity="0.8"/>', '</g>')


def fur_fringe(ic, x0, x1, y, depth, color, n=8):
    """A row of hanging hair tufts (yak skirt, yeti fur)."""
    w = (x1 - x0) / n
    pts = [(x0, y - 4)]
    for i in range(n):
        pts += [(x0 + w * (i + 0.5), y + depth * (0.8 + 0.2 * (i % 2))), (x0 + w * (i + 1), y)]
    pts.append((x1, y - 4))
    shp(ic, poly_d(pts), color, sw=5, off=(-3, -4))


# ----------------------------------------------------------------- animals ---
# Each returns (name, rarity, zone, description, effects).

def pebble_marmot(ic):
    fur, belly = "#b07a45", "#ecc995"
    ground(ic, 200, 120)
    blk(ic, 92, 300, 70, 34, dark(fur, 0.1), r=16)                       # tail
    blk(ic, 120, 190, 170, 170, fur, r=56)                                 # body
    blk(ic, 190, 238, 90, 112, belly, r=36, studs=False)
    blk(ic, 140, 340, 60, 30, dark(fur, 0.15), r=12, studs=False)         # feet
    blk(ic, 230, 340, 60, 30, dark(fur, 0.15), r=12, studs=False)
    for x in (222, 300):
        oval(ic, x, 132, 17, 16, dark(fur, 0.1))
        oval(ic, x, 134, 8, 8, "#e79aa6", sw=0)
    blk(ic, 205, 120, 125, 110, fur, r=40)                                 # head
    blk(ic, 275, 178, 70, 44, belly, r=18, studs=False)
    blk(ic, 322, 178, 20, 15, "#3a2418", r=6, studs=False, sw=3)
    ic.add('<rect x="318" y="206" width="16" height="12" rx="3" fill="#ffffff" stroke="#24123f" stroke-width="3"/>')
    eye(ic, 282, 160, 0.9)
    blush(ic, 252, 196)
    # The pebble it carries, and a smaller mossy one on its head with a sprout.
    oval(ic, 315, 265, 38, 30, "#9aa0ad", studs=False)
    oval(ic, 315, 248, 30, 12, "#7cc457", sw=4)
    blk(ic, 268, 252, 34, 24, fur, r=10, studs=False)
    oval(ic, 248, 108, 30, 18, "#9aa0ad", sw=5)
    oval(ic, 248, 98, 24, 8, "#7cc457", sw=4)
    stroke(ic, "M252,92 C254,76 262,70 270,68", "#5fae3e", 6, outline=3)
    oval(ic, 274, 68, 9, 6, "#7cc457", sw=3)
    return ("Pebble Marmot", "Common", "Pine Foothills",
            "A chubby marmot that collects shiny pebbles. It always carries its favourite one, and grows a little "
            "moss garden on its head.",
            "Pebbles roll out of its paws when it sits up; small dust puffs when it runs.")


def pika_puff(ic):
    fur, belly = "#c9a27a", "#f2dcc0"
    ground(ic, 205, 115)
    for x, y in ((150, 160), (262, 150)):
        oval(ic, x, y, 38, 36, dark(fur, 0.1))
        oval(ic, x, y + 2, 20, 19, "#f0a6b4", sw=0)
    shp(ic, rrect_d(105, 160, 210, 200, 95), fur, studs=True)
    shp(ic, rrect_d(165, 240, 110, 112, 52), belly)
    for x in (148, 236):
        blk(ic, x, 344, 40, 22, dark(fur, 0.12), r=10, studs=False)
    eye(ic, 170, 230, 0.9)
    eye(ic, 248, 228, 0.9)
    blk(ic, 199, 250, 20, 13, "#e46b8a", r=6, studs=False, sw=3)
    ic.add('<path d="M209,263 Q201,276 192,268 M209,263 Q217,276 226,268" fill="none" stroke="#24123f" '
           'stroke-width="4" stroke-linecap="round"/>')
    for sgn in (-1, 1):
        for dy in (-6, 6):
            x0 = 209 + sgn * 40
            ic.add(f'<line x1="{x0}" y1="{258 + dy}" x2="{x0 + sgn * 46}" y2="{252 + dy * 2}" stroke="#24123f" '
                   f'stroke-width="3" stroke-linecap="round"/>')
    blush(ic, 158, 262)
    blush(ic, 262, 262)
    # An edelweiss tucked behind its ear.
    for k in range(6):
        a = math.radians(k * 60)
        oval(ic, 292 + 16 * math.cos(a), 128 + 16 * math.sin(a), 11, 7, "#ffffff", sw=3)
    oval(ic, 292, 128, 8, 8, "#ffd23f", sw=3)
    return ("Pika Puff", "Common", "Pine Foothills",
            "A tiny, perfectly round pika that squeaks when you get close. It keeps flowers behind its ears for "
            "the winter.",
            "Bounces when it moves; little flower petals drift off it.")


def cliff_kid(ic):
    fur, horn = "#f3efe6", "#b9a690"
    ground(ic, 200, 130)
    legs(ic, (150, 236), 270, 360, 26, fur, hoof="#4a3a30", far=True)
    blk(ic, 110, 200, 180, 100, fur, r=34)
    legs(ic, (128, 258), 270, 365, 28, fur, hoof="#4a3a30")
    stroke(ic, "M118,214 C100,196 104,180 118,172", fur, 16, outline=5)   # tail
    blk(ic, 248, 116, 100, 96, fur, r=30)                                  # head
    blk(ic, 316, 160, 46, 44, lite(fur, 0.3), r=14, studs=False)
    blk(ic, 344, 170, 14, 11, "#a35a6a", r=4, studs=False, sw=3)
    for dx in (0, 22):
        stroke(ic, f"M{272 + dx},120 C{268 + dx},96 {280 + dx},84 {296 + dx},86", horn, 11, outline=4)
    shp(ic, rrect_d(214, 132, 52, 22, 11), lite(fur, 0.1), off=(-3, -3))   # floppy ear
    ic.add('<path d="M318,206 L330,236 L340,206 Z" fill="#e8e2d4" stroke="#24123f" stroke-width="4" '
           'stroke-linejoin="round"/>')                                     # beard
    eye(ic, 300, 150, 0.85)
    blush(ic, 284, 182)
    # Red collar with a golden bell.
    blk(ic, 246, 200, 54, 16, "#e23d3d", r=6, studs=False, sw=4)
    oval(ic, 272, 232, 14, 14, "#ffd23f", sw=4)
    ic.add('<circle cx="272" cy="238" r="3.5" fill="#24123f"/>')
    return ("Cliff Kid", "Common", "Pine Foothills",
            "A baby mountain goat that jumps from rock to rock without ever falling. Its little bell rings with "
            "every hop.",
            "Jumps instead of walking, with a tiny dust puff and a bell jingle on every landing.")


def snowshoe_hare(ic):
    fur, tip = "#f6f8fc", "#6fa8e6"
    ground(ic, 200, 135)
    oval(ic, 104, 262, 30, 28, "#ffffff")                                  # tail
    blk(ic, 108, 210, 180, 128, fur, r=52)
    blk(ic, 116, 320, 128, 42, lite(tip, 0.55), r=18, studs=False)        # the big snowshoe foot
    for x in (130, 160, 190, 220):
        ic.add(f'<line x1="{x}" y1="330" x2="{x}" y2="356" stroke="#24123f" stroke-width="3" opacity="0.35"/>')
    blk(ic, 262, 316, 34, 46, fur, r=12, studs=False)
    for x, r in ((246, -8), (282, 8)):
        ic.add(f'<g transform="rotate({r} {x + 16} 140)">')
        blk(ic, x, 30, 34, 120, fur, r=17, studs=False)
        blk(ic, x + 8, 44, 18, 80, "#f6c0cc", r=9, studs=False, sw=0)
        blk(ic, x, 30, 34, 34, tip, r=17, studs=False)
        ic.add('</g>')
    blk(ic, 236, 130, 112, 100, fur, r=40)
    eye(ic, 300, 168, 0.95, iris="#3f7fbf")
    blk(ic, 336, 190, 16, 12, "#ff8fb0", r=5, studs=False, sw=3)
    blush(ic, 290, 204)
    snowflakes(ic, [(70, 120, 12), (360, 80, 10), (90, 190, 8), (370, 270, 9)])
    return ("Snowshoe Hare", "Common", "Alpine Lakes",
            "Its huge snowshoe feet let it race over deep snow. In summer it is brown, but here it stays white "
            "all year, with frosty blue ear tips.",
            "Leaves a trail of footprints in the snow and kicks up snow puffs when it hops.")


def bighorn_ram(ic):
    fur, rump, horn = "#c4925e", "#f2e2c8", "#d9c2a0"
    ground(ic, 195, 150)
    legs(ic, (140, 240), 270, 360, 28, dark(fur, 0.05), hoof="#3a2a20", far=True)
    blk(ic, 86, 186, 214, 110, fur, r=34)
    blk(ic, 86, 210, 52, 80, rump, r=20, studs=False)
    blk(ic, 120, 262, 160, 30, rump, r=14, studs=False)
    legs(ic, (112, 256), 270, 365, 30, dark(fur, 0.05), hoof="#3a2a20")
    blk(ic, 250, 120, 104, 100, fur, r=30)
    blk(ic, 318, 168, 50, 48, rump, r=16, studs=False)
    blk(ic, 350, 176, 14, 12, "#3a2a20", r=4, studs=False, sw=3)
    eye(ic, 304, 154, 0.85, brow=(-10, "#5a3a20"))
    # The great curled horn, with red-rock stripes worn into it.
    d = "M274,128 C252,92 296,66 326,86 C356,106 344,152 312,156 C290,158 282,138 298,128"
    stroke(ic, d, horn, 30, outline=6, dash=("#b48a5c", "6 12"))
    ic.add(f'<path d="{d}" fill="none" stroke="#c4552e" stroke-width="5" stroke-dasharray="3 22" opacity="0.8"/>')
    for x, y, r in ((112, 362, 26), (150, 368, 20), (262, 366, 24)):
        oval(ic, x, y, r, r * 0.55, "#d98a5c", sw=0)
    return ("Bighorn Ram", "Rare", "Canyon Pass",
            "The king of the canyon walls. Its curled horns are striped with the red rock of the canyon, and when "
            "two rams clash you hear it echo through the whole pass.",
            "Red rock dust under its hooves; a head-butt shockwave as its idle action.")


def alpine_ibex(ic):
    fur, horn = "#8d7a62", "#b8a48a"
    ground(ic, 200, 140)
    legs(ic, (146, 236), 270, 360, 24, fur, hoof="#2e241c", far=True)
    blk(ic, 100, 194, 196, 98, fur, r=32)
    blk(ic, 110, 262, 170, 28, lite(fur, 0.35), r=12, studs=False)
    legs(ic, (122, 258), 270, 365, 26, fur, hoof="#2e241c")
    # Long ridged horns sweeping back over its body.
    d = "M290,124 C266,64 210,40 160,58"
    stroke(ic, d, horn, 26, outline=6)
    for k in range(7):
        t = 0.1 + k * 0.12
        x = (1 - t) ** 3 * 290 + 3 * (1 - t) ** 2 * t * 266 + 3 * (1 - t) * t ** 2 * 210 + t ** 3 * 160
        y = (1 - t) ** 3 * 124 + 3 * (1 - t) ** 2 * t * 64 + 3 * (1 - t) * t ** 2 * 40 + t ** 3 * 58
        ic.add(f'<circle cx="{f(x)}" cy="{f(y)}" r="9" fill="none" stroke="#7d6a52" stroke-width="4"/>')
    blk(ic, 258, 118, 96, 96, fur, r=28)
    blk(ic, 322, 164, 44, 46, lite(fur, 0.3), r=14, studs=False)
    blk(ic, 352, 172, 13, 11, "#2e241c", r=4, studs=False, sw=3)
    ic.add('<path d="M320,208 L332,256 L346,208 Z" fill="#5a4a3a" stroke="#24123f" stroke-width="4" '
           'stroke-linejoin="round"/>')
    eye(ic, 306, 150, 0.85, iris="#c98a2a")
    for k in range(5):   # edelweiss at the horn base
        a = math.radians(k * 72)
        oval(ic, 286 + 11 * math.cos(a), 112 + 11 * math.sin(a), 8, 5, "#ffffff", sw=3)
    oval(ic, 286, 112, 5, 5, "#ffd23f", sw=2)
    return ("Alpine Ibex", "Rare", "Canyon Pass",
            "Climbs straight up cliff faces that nothing else can. Its long ridged horns get one ring longer every "
            "year, and it wears an edelweiss as a trophy.",
            "Climbs walls; small pebbles tumble down behind it.")


def red_panda(ic):
    fur, black, white = "#d4582a", "#2e1a16", "#fff4e6"
    ground(ic, 200, 140)
    # The big ringed tail curling up behind.
    for k in range(6):
        cx, cy = 104 - 6 * k, 280 - 30 * k
        oval(ic, cx, cy, 30, 22, fur if k % 2 == 0 else "#f2c49a", sw=5)
    legs(ic, (150, 236), 290, 360, 26, black, far=True)
    blk(ic, 92, 226, 196, 88, fur, r=40)
    legs(ic, (124, 254), 290, 366, 28, black)
    for x in (258, 334):
        shp(ic, poly_d([(x, 172), (x + 18, 128), (x + 38, 172)]), fur, sw=5, off=(-3, -3))
        shp(ic, poly_d([(x + 9, 168), (x + 18, 142), (x + 28, 168)]), white, sw=0, off=(0, 0))
    blk(ic, 248, 150, 118, 98, fur, r=38)
    for x in (264, 330):
        oval(ic, x + 6, 210, 22, 16, white, sw=0)
    oval(ic, 306, 162, 26, 9, white, sw=0)
    blk(ic, 340, 210, 26, 26, white, r=10, studs=False, sw=4)
    blk(ic, 352, 210, 14, 11, black, r=4, studs=False, sw=3)
    eye(ic, 296, 192, 0.85, iris="#5a2a10")
    # Holding a bamboo sprig.
    stroke(ic, "M378,330 L392,226", "#7cc457", 12, outline=4)
    for y in (300, 262):
        ic.add(f'<line x1="{378 + (330 - y) * 0.13 - 8}" y1="{y}" x2="{378 + (330 - y) * 0.13 + 8}" y2="{y}" '
               f'stroke="#24123f" stroke-width="3"/>')
    shp(ic, "M390,240 C410,226 420,210 424,196 C406,204 394,220 390,240 Z", "#5fae3e", sw=4, off=(-2, -2))
    return ("Red Panda", "Rare", "Alpine Lakes",
            "Lives in the bamboo groves around the mountain lakes. It wraps its big ringed tail around itself to "
            "sleep, and it never lets go of its bamboo.",
            "Rolls into a ball with its tail when idle; little bamboo leaves fall around it.")


def peak_eagle(ic):
    body, head, gold = "#6b4a2e", "#f2e6cf", "#ffc93c"
    ic.add('<path d="M70,372 L110,320 L200,304 L300,316 L340,372 Z" fill="#8a8fa8" stroke="#24123f" '
           'stroke-width="6" stroke-linejoin="round"/>')                     # rock
    glow(ic, ellipse_d(206, 210, 120, 110), "#ffe28a", 0.45)
    shp(ic, "M150,330 L120,372 L176,372 Z M210,330 L196,372 L240,372 Z", dark(body, 0.2), sw=5)  # tail
    shp(ic, rrect_d(130, 150, 150, 190, 70), body, studs=True)
    # Folded wing with golden feather tips.
    wing = "M150,190 C200,170 270,200 270,250 L262,330 L236,312 L224,340 L198,316 L176,344 L160,300 Z"
    shp(ic, wing, dark(body, 0.1), sw=6)
    for x, y in ((262, 330), (224, 340), (176, 344)):
        shp(ic, poly_d([(x - 10, y - 20), (x, y), (x + 10, y - 20)]), gold, sw=4, off=(0, 0))
    blk(ic, 196, 74, 118, 106, head, r=38)
    shp(ic, "M300,112 L352,120 C362,132 356,150 340,152 L334,140 L300,140 Z", gold, sw=5)
    eye(ic, 268, 118, 0.85, iris="#ffb21c", brow=(14, "#24123f"))
    for x in (176, 230):
        stroke(ic, f"M{x},336 L{x},352", gold, 10, outline=4)
        for dx in (-12, 0, 12):
            stroke(ic, f"M{x},352 L{x + dx},362", gold, 6, outline=3)
    # Wind swirls.
    for cx, cy, r in ((90, 150, 28), (350, 230, 22), (110, 250, 18)):
        ic.add(f'<path d="M{cx - r},{cy} A{r},{r} 0 1,1 {cx},{cy + r} A{r * 0.5},{r * 0.5} 0 1,1 {cx},{cy}" '
               f'fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round" opacity="0.85"/>')
    return ("Peak Eagle", "Epic", "Canyon Pass",
            "Nests on the highest canyon pillar and rides the mountain winds. Its feathers are tipped with gold; "
            "it is said they bring good luck.",
            "Flies in circles above the canyon; wind swirls and golden feathers drift off when it flaps.")


def mountain_yak(ic):
    fur, light, horn = "#4a3426", "#6b4c38", "#efe6d2"
    ground(ic, 196, 165)
    legs(ic, (130, 250), 300, 360, 34, dark(fur, 0.1), hoof="#1e140e", far=True)
    blk(ic, 66, 170, 262, 150, fur, r=52)
    fur_fringe(ic, 66, 328, 300, 34, light, n=10)
    legs(ic, (100, 270), 300, 366, 36, fur, hoof="#1e140e")
    # Woven blanket with snow on top.
    blk(ic, 122, 156, 130, 74, "#c4302b", r=12, studs=False)
    for y, c in ((176, "#2bb0a8"), (200, "#ffd23f")):
        ic.add(f'<rect x="124" y="{y}" width="126" height="9" fill="{c}"/>')
    cloud_blob(ic, [(150, 152, 18), (180, 146, 22), (214, 150, 20), (240, 156, 14)], light="#ffffff",
               dark="#d6e2f2", sw=6)
    blk(ic, 280, 186, 96, 92, fur, r=32)
    fur_fringe(ic, 284, 372, 186, 22, light, n=5)
    for sgn, x in ((-1, 290), (1, 366)):
        stroke(ic, f"M{x},{200} C{x + sgn * 26},190 {x + sgn * 30},160 {x + sgn * 10},146", horn, 13, outline=5)
    blk(ic, 330, 236, 46, 38, light, r=14, studs=False)
    eye(ic, 342, 220, 0.8)
    # Golden bells on a red collar.
    blk(ic, 278, 270, 70, 16, "#c4302b", r=6, studs=False, sw=4)
    for x in (296, 326):
        shp(ic, f"M{x - 12},{304} Q{x - 12},{286} {x},{286} Q{x + 12},{286} {x + 12},{304} Z", "#ffd23f", sw=4,
            off=(-2, -2))
    return ("Mountain Yak", "Epic", "Alpine Lakes",
            "A huge shaggy yak that carries snow on its back all year round. Wranglers say its golden bells can be "
            "heard from the other side of the lake.",
            "Snow sprinkles off its back when it walks; its bells chime with a ring of light on every step.")


def geode_tortoise(ic):
    skin, stone, cry = "#8aa86a", "#8a8fa8", "#b46bff"
    ground(ic, 200, 150)
    for x in (110, 266):
        blk(ic, x, 320, 44, 48, skin, r=14, studs=False)
    blk(ic, 300, 248, 78, 62, skin, r=26)
    eye(ic, 346, 272, 0.75, iris="#5a2a8a")
    blush(ic, 336, 296, 0.8)
    shell = "M80,330 C80,200 140,156 210,156 C280,156 330,200 330,330 Z"
    shp(ic, shell, stone, studs=True)
    for x in (148, 248):
        ic.add(f'<path d="M{x},164 L{x - 14},330" stroke="#24123f" stroke-width="4" opacity="0.35"/>')
    # The cracked-open geode on top, full of glowing crystals.
    gd = "M140,206 C150,170 270,170 280,206 C262,220 156,220 140,206 Z"
    shp(ic, gd, "#3a1f5a", sw=5, off=(0, 0))
    for x, h, w, t, c in ((168, 66, 22, -14, cry), (196, 92, 28, -4, "#d9a6ff"), (226, 80, 26, 8, cry),
                          (252, 54, 20, 18, "#7fd8ff")):
        crystal(ic, x, 212, h, w, c, tilt=t)
    blk(ic, 80, 318, 252, 22, dark(stone, 0.15), r=10, studs=False)
    twinkles(ic, [(120, 120, 12), (290, 110, 14), (210, 70, 10)], color="#e9d6ff")
    return ("Geode Tortoise", "Epic", "Canyon Pass",
            "Hides in the caves of the canyon walls. Its shell is a stone geode that has cracked open, and the "
            "crystals inside glow brighter the older it gets.",
            "Its crystals pulse with purple light; crystal sparkles float up from its shell.")


def snow_leopard(ic):
    fur, ice = "#e6e8ee", "#5ee0ff"
    glow(ic, ellipse_d(200, 250, 170, 100), ice, 0.35)
    ground(ic, 200, 160)
    stroke(ic, "M86,250 C40,250 30,180 70,160 C96,148 110,170 96,186", fur, 34, outline=6)   # thick tail
    for x, y in ((52, 210), (66, 168), (96, 180)):
        ic.add(f'<circle cx="{x}" cy="{y}" r="8" fill="none" stroke="{ice}" stroke-width="5"/>')
    legs(ic, (140, 236), 270, 360, 30, fur, far=True)
    blk(ic, 70, 200, 236, 96, fur, r=44)
    legs(ic, (110, 262), 270, 366, 34, fur)
    # Glowing ice-blue rosettes.
    for x, y, r in ((110, 230, 11), (150, 252, 9), (190, 226, 12), (230, 254, 10), (262, 228, 9), (130, 274, 8)):
        ic.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{ice}" stroke-width="5" filter="url(#glow)"/>',
               f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="#24123f" stroke-width="2" opacity="0.4"/>')
    for x in (270, 338):
        oval(ic, x + 10, 148, 16, 14, fur, sw=5)
    blk(ic, 262, 144, 110, 96, fur, r=36)
    blk(ic, 330, 190, 44, 40, lite(fur, 0.4), r=14, studs=False)
    blk(ic, 352, 192, 16, 11, "#ff9eb5", r=4, studs=False, sw=3)
    eye(ic, 312, 180, 0.9, iris=ice, glow=True)
    twinkles(ic, [(370, 120, 12), (60, 120, 10), (330, 300, 9), (200, 160, 8)], color="#cff7ff")
    return ("Snow Leopard", "Legendary", "Frost Ridge",
            "The ghost of the mountains. You almost never see it coming: its frosty rosettes glow only when it "
            "wants to be seen.",
            "Glowing ice rosettes that pulse; a frost trail behind its paws; snowflakes swirl around it.")


def frostfang_wolf(ic):
    fur, ice = "#dfe9f5", "#7fe3ff"
    glow(ic, ellipse_d(220, 230, 170, 110), ice, 0.35)
    ground(ic, 200, 160)
    stroke(ic, "M96,226 C60,220 46,196 52,176", fur, 30, outline=6)       # tail
    crystal(ic, 52, 180, 34, 16, ice, tilt=-30)
    legs(ic, (140, 232), 270, 360, 26, fur, far=True)
    blk(ic, 82, 196, 214, 100, fur, r=36)
    legs(ic, (112, 256), 270, 366, 30, fur)
    # Ice crystal mane along its neck and back.
    for x, h, t in ((150, 40, -20), (182, 50, -12), (214, 58, -6), (246, 64, 0), (272, 56, 8)):
        crystal(ic, x, 204, h, 20, ice, tilt=t)
    for x in (282, 330):
        shp(ic, poly_d([(x, 150), (x + 16, 98), (x + 34, 150)]), fur, sw=5, off=(-3, -3))
    blk(ic, 266, 136, 104, 92, fur, r=26)
    blk(ic, 332, 176, 62, 44, lite(fur, 0.5), r=12, studs=False)
    blk(ic, 380, 176, 16, 13, "#24123f", r=5, studs=False, sw=2)
    for x in (342, 368):   # icicle fangs
        ic.add(f'<path d="M{x},218 L{x + 6},236 L{x + 12},218 Z" fill="{lite(ice, 0.4)}" stroke="#24123f" '
               f'stroke-width="3" stroke-linejoin="round"/>')
    eye(ic, 312, 170, 0.85, iris=ice, glow=True, brow=(16, "#24123f"))
    # Frost breath.
    cloud_blob(ic, [(390, 240, 14), (378, 256, 10), (398, 260, 9)], light="#ffffff", dark="#cfe6f5", sw=4)
    snowflakes(ic, [(60, 110, 10), (370, 90, 9), (110, 160, 7)], color="#e8fbff")
    return ("Frostfang Wolf", "Legendary", "Frost Ridge",
            "Leads its pack along the frozen ridge. Ice grows from its fur like a crown, and its breath freezes "
            "everything it touches.",
            "Frost breath when it howls; ice crystals on its back sparkle; frozen paw prints that slowly melt.")


def little_yeti(ic):
    fur, face, horn = "#f6f8fc", "#8fb3e6", "#c9cfe8"
    ground(ic, 205, 120)
    cloud_blob(ic, [(160, 190, 40), (250, 190, 40), (205, 160, 50), (150, 260, 50), (260, 260, 50),
                    (205, 300, 62), (205, 230, 70)], light="#ffffff", dark="#cdd8ea")
    for x in (148, 236):
        blk(ic, x, 340, 52, 30, face, r=12, studs=False)
    for x, t in ((174, -30), (240, 30)):
        stroke(ic, f"M{x},{122} C{x - 10 if t < 0 else x + 10},{96} {x - 4 if t < 0 else x + 4},{84} "
                   f"{x + (8 if t < 0 else -8)},{80}", horn, 12, outline=4)
    blk(ic, 160, 140, 92, 82, face, r=30, studs=False)
    eye(ic, 186, 174, 0.8, iris="#3a6fd8")
    eye(ic, 228, 174, 0.8, iris="#3a6fd8")
    ic.add('<path d="M188,204 Q207,218 226,204" fill="none" stroke="#24123f" stroke-width="4" stroke-linecap="round"/>',
           '<path d="M194,207 L198,215 L202,209 Z M212,209 L216,215 L220,207 Z" fill="#ffffff" stroke="#24123f" '
           'stroke-width="2"/>')
    blush(ic, 172, 196)
    blush(ic, 242, 196)
    # Holding up a big snowball.
    oval(ic, 290, 248, 40, 38, "#ffffff", studs=False)
    for x, y in ((262, 254), (312, 256)):
        oval(ic, x, y, 16, 14, face, sw=5)
    snowflakes(ic, [(80, 120, 12), (340, 120, 10), (90, 230, 8), (350, 330, 9)])
    return ("Little Yeti", "Legendary", "Frost Ridge",
            "Everyone thought the yeti was a legend, until wranglers found this little one. It throws snowballs "
            "at anyone who gets too close (and giggles).",
            "Throws snowballs that burst into snow puffs; little snowstorm swirls around it when it is happy.")


def sky_griffin(ic):
    body, head, gold, wing = "#e2a93a", "#ffffff", "#ffc93c", "#f6f2e8"
    glow(ic, ellipse_d(200, 200, 190, 150), "#ffe28a", 0.45)
    ground(ic, 200, 165)
    # Big wings raised behind.
    for k, (x, rot) in enumerate(((150, -14), (196, 6))):
        ic.add(f'<g transform="rotate({rot} {x} 210)">')
        feathers = "".join(f"L{f(x - 90 + 32 * i)},{f(60 + 14 * abs(i - 2.5))} " for i in range(6))
        d = f"M{x},214 L{x - 110},150 {feathers}L{x + 70},140 Z"
        shp(ic, d, wing if k else dark(wing, 0.08), sw=6)
        for i in range(6):
            fx, fy = x - 90 + 32 * i, 60 + 14 * abs(i - 2.5)
            shp(ic, poly_d([(fx - 10, fy + 26), (fx, fy), (fx + 10, fy + 26)]), gold, sw=4, off=(0, 0))
        ic.add('</g>')
    stroke(ic, "M90,250 C50,250 46,300 66,320", body, 14, outline=5)       # lion tail
    oval(ic, 66, 326, 16, 18, "#c47a1c", sw=5)
    legs(ic, (130, 232), 280, 360, 28, body, far=True)
    blk(ic, 80, 206, 220, 100, body, r=40)
    legs(ic, (106, 262), 280, 366, 30, body)
    for dx in (-12, 0, 12):
        stroke(ic, f"M{277 + dx * 0.4},360 L{277 + dx},372", gold, 6, outline=3)
    blk(ic, 252, 118, 104, 104, head, r=34)
    shp(ic, "M346,148 L390,156 C400,170 392,188 378,190 L370,176 L346,176 Z", gold, sw=5)
    shp(ic, poly_d([(262, 130), (238, 104), (278, 116)]), head, sw=5, off=(-2, -2))
    eye(ic, 312, 160, 0.9, iris="#ffb21c", brow=(14, "#24123f"))
    # Wind rings.
    for cx, cy, rx in ((330, 300, 46), (120, 120, 36)):
        ic.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{rx * 0.3}" fill="none" stroke="#ffffff" stroke-width="6" '
               f'opacity="0.85"/>')
    twinkles(ic, [(380, 90, 14), (40, 190, 10), (360, 240, 9)], color="#fff4b0")
    return ("Sky Griffin", "Mythic", "The Summit",
            "Half eagle, half lion, it guards the summit from its nest in the clouds. When it spreads its wings "
            "the whole mountain goes quiet.",
            "Golden aura; wind rings when it flaps; golden feathers drift down; it lands with a gust that blows "
            "snow away in a circle.")


def glacier_mammoth(ic):
    fur, ice = "#cfe3f2", "#7fe3ff"
    glow(ic, ellipse_d(200, 240, 180, 110), ice, 0.35)
    ground(ic, 196, 160)
    legs(ic, (128, 236), 300, 360, 40, dark(fur, 0.1), far=True)
    blk(ic, 70, 168, 236, 154, fur, r=60)
    fur_fringe(ic, 70, 306, 300, 30, lite(fur, 0.2), n=9)
    legs(ic, (96, 258), 300, 368, 42, fur)
    # Glacier crystals growing on its back.
    for x, h, t in ((120, 46, -14), (150, 66, -6), (182, 80, 0), (214, 62, 8), (240, 42, 14)):
        crystal(ic, x, 178, h, 24, ice, tilt=t)
    oval(ic, 262, 196, 30, 40, dark(fur, 0.08), sw=6)                     # ear
    blk(ic, 248, 132, 120, 128, fur, r=52)
    eye(ic, 318, 182, 0.85, iris="#2f7fbf")
    blush(ic, 302, 214)
    # Trunk curling up, and ice tusks.
    stroke(ic, "M346,232 C366,268 370,300 350,320 C336,334 322,324 330,310", fur, 30, outline=6)
    for k in range(4):
        ic.add(f'<line x1="{352 + k * 3}" y1="{254 + k * 18}" x2="{372 - k * 2}" y2="{252 + k * 18}" '
               f'stroke="#24123f" stroke-width="3" opacity="0.35"/>')
    d = "M318,246 C320,290 352,316 392,300"
    ic.add(f'<path d="{d}" fill="none" stroke="{ice}" stroke-width="22" filter="url(#glow)" opacity="0.7"/>')
    stroke(ic, d, lite(ice, 0.45), 16, outline=5)
    snowflakes(ic, [(70, 120, 12), (380, 110, 11), (60, 260, 8), (230, 90, 9)], color="#e8fbff")
    return ("Glacier Mammoth", "Mythic", "Frost Ridge",
            "A baby mammoth, frozen in the glacier for ten thousand years and woken up by the wranglers. A piece "
            "of the glacier still grows on its back.",
            "Glowing glacier crystals; every stomp freezes the ground in a ring of ice; snow falls around it.")


def aurora_dragon(ic):
    g = ic.grad([(0, "#5effb0"), (0.45, "#3fd6ff"), (1, "#b45cff")], 0, 0, 1, 0)
    # The long serpent body, made of aurora light.
    d = "M40,320 C90,250 150,350 200,280 C240,224 200,170 250,150 C300,130 320,190 300,226"
    ic.add(f'<path d="{d}" fill="none" stroke="{g}" stroke-width="80" stroke-linecap="round" filter="url(#bigglow)" '
           f'opacity="0.55"/>')
    stroke(ic, d, g, 46, outline=6)
    ic.add(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="8" stroke-dasharray="2 26" '
           f'stroke-linecap="round" opacity="0.9"/>')
    # Spines.
    for x, y, r in ((70, 278, -30), (122, 300, 10), (180, 282, -10), (214, 210, -40), (246, 140, -10)):
        shp(ic, poly_d([(x - 10, y), (x, y - 28), (x + 10, y)]), "#e9ddff", sw=4, off=(0, 0))
        _ = r
    # Head with antlers and flowing whiskers.
    blk(ic, 272, 186, 96, 72, "#4fd8e8", r=24)
    blk(ic, 340, 210, 50, 40, "#8cf0ff", r=14, studs=False)
    for x0 in (290, 316):
        stroke(ic, f"M{x0},190 L{x0 - 6},150 L{x0 - 22},132 M{x0 - 6},164 L{x0 + 12},146", "#ffe9a8", 9, outline=4)
    stroke(ic, "M386,236 C410,250 410,280 388,296", "#e9ddff", 6, outline=3)
    stroke(ic, "M372,248 C392,276 380,306 356,318", "#e9ddff", 6, outline=3)
    eye(ic, 322, 214, 0.85, iris="#ffe14d", glow=True, brow=(12, "#24123f"))
    for x, y in ((140, 334), (224, 262)):
        for dx in (-10, 0, 10):
            stroke(ic, f"M{x},{y} L{x + dx},{y + 18}", "#ffe9a8", 6, outline=3)
    twinkles(ic, [(60, 120, 14), (360, 70, 16), (180, 90, 10), (390, 340, 10), (110, 200, 8), (250, 330, 9)],
             color="#e9fff6")
    return ("Aurora Dragon", "Secret", "The Summit",
            "Only appears on the summit when the northern lights are out. Its body is made of the aurora itself; "
            "nobody has ever seen where it ends.",
            "Its body ripples with green, blue and purple light; stars glitter inside it; the sky turns to aurora "
            "when it appears, with a server-wide shout.")


ANIMALS = [pebble_marmot, pika_puff, cliff_kid, snowshoe_hare, bighorn_ram, alpine_ibex, red_panda, peak_eagle,
           mountain_yak, geode_tortoise, snow_leopard, frostfang_wolf, little_yeti, sky_griffin, glacier_mammoth,
           aurora_dragon]


# ------------------------------------------------------------------- cards ---

def wrap(text, n):
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > n:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + [cur]


def text(ic, x, y, s, size, fill="#ffffff", font="Fredoka", anchor="middle", weight=600, stroke=None, sw=0):
    st = f' stroke="{stroke}" stroke-width="{sw}" paint-order="stroke" stroke-linejoin="round"' if stroke else ""
    ic.add(f'<text x="{x}" y="{y}" font-family="{font}" font-weight="{weight}" font-size="{size}" '
           f'text-anchor="{anchor}" fill="{fill}"{st}>{s}</text>')


def card(draw):
    W, H = 800, 1080
    ic = Art(draw.__name__, W, H)
    tmp = Art("_", 400, 400)
    tmp.n = 5000
    name, rarity, zone, desc, effects = draw(tmp)
    ic.n = tmp.n
    main, deep = RARITY[rarity]
    secret = rarity == "Secret"
    frame = ic.grad([(0, lite(main, 0.15)), (1, deep)])
    ic.add(f'<rect x="0" y="0" width="{W}" height="{H}" rx="44" fill="{frame}"/>')
    # Art window.
    if secret:
        bg = ic.radial([(0, "#1d3a5a", 1), (0.6, "#140f2e", 1), (1, "#07060f", 1)], cy=0.45)
    else:
        bg = ic.radial([(0, lite(main, 0.7), 1), (0.65, lite(main, 0.25), 1), (1, main, 1)], cy=0.45)
    ic.add(f'<rect x="34" y="176" width="{W - 68}" height="580" rx="28" fill="{bg}" stroke="{OUT}" stroke-width="7"/>')
    cid = ic.uid("w")
    ic.defs.append(f'<clipPath id="{cid}"><rect x="34" y="176" width="{W - 68}" height="580" rx="28"/></clipPath>')
    ic.add(f'<g clip-path="url(#{cid})">')
    cx, cy = W / 2, 470
    wedges = []
    for i in range(16):
        a0, a1 = math.radians(i * 22.5 - 5), math.radians(i * 22.5 + 5)
        wedges.append(poly_d([(cx, cy), (cx + 900 * math.cos(a0), cy + 900 * math.sin(a0)),
                              (cx + 900 * math.cos(a1), cy + 900 * math.sin(a1))]))
    ic.add(f'<path d="{" ".join(wedges)}" fill="#ffffff" opacity="{0.05 if secret else 0.16}"/>')
    if secret:
        for k in range(60):
            x, y = (k * 137) % 730 + 34, (k * 89) % 560 + 180
            ic.add(f'<circle cx="{x}" cy="{y}" r="{1 + k % 3}" fill="#ffffff" opacity="0.7"/>')
    ic.add(f'<g transform="translate(116,186) scale(1.42)">', *tmp.body, '</g>', '</g>')
    ic.defs.extend(tmp.defs)
    # Name and rarity pill.
    text(ic, W / 2, 104, name, 76, font="Lilita", weight=400, stroke=OUT, sw=14)
    pw = 40 + 22 * len(rarity)
    ic.add(f'<rect x="{W / 2 - pw / 2}" y="122" width="{pw}" height="44" rx="22" fill="{main}" stroke="{OUT}" '
           f'stroke-width="6"/>')
    text(ic, W / 2, 156, rarity, 32, font="Lilita", weight=400, stroke=OUT, sw=7)
    # Info panel.
    ic.add(f'<rect x="34" y="774" width="{W - 68}" height="272" rx="24" fill="#fff8ec" stroke="{OUT}" stroke-width="6"/>')
    text(ic, 64, 818, f"Zone: {zone}", 30, fill=deep if not secret else "#5a3fb0", anchor="start", weight=700)
    y = 856
    for line in wrap(desc, 52):
        text(ic, 64, y, line, 24, fill="#4a3424", anchor="start", weight=500)
        y += 30
    y += 6
    for i, line in enumerate(wrap("In game: " + effects, 56)):
        text(ic, 64, y, line, 22, fill="#7a5a3a", anchor="start", weight=600)
        y += 27
    assert y < 1046, f"{name}: text runs off the card"
    return ic, (name, rarity, zone)


def main():
    import json
    import os
    import subprocess

    from build_icons import font_css
    from PIL import Image, ImageDraw, ImageFont

    css = font_css()
    out = HERE.parent.parent / "concept-art" / "mountain-range" / "dieren"
    build = HERE / "build" / "mountain"
    out.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)
    jobs, info = [], []
    for i, draw in enumerate(ANIMALS):
        ic, meta = card(draw)
        svg = build / f"{draw.__name__}.svg"
        svg.write_text(ic.svg(css))
        png = out / f"{i + 1:02d}-{meta[0].lower().replace(' ', '-')}.png"
        jobs.append({"svg": str(svg), "png": str(png), "w": ic.w, "h": ic.h})
        info.append((png, meta))
    (build / "animal_jobs.json").write_text(json.dumps(jobs))
    subprocess.run(["node", str(HERE / "render_svg.js"), str(build / "animal_jobs.json")], check=True,
                   env={**os.environ, "NODE_PATH": "/opt/node22/lib/node_modules"})

    # All 16 on one sheet.
    cw, ch, gap = 380, 513, 24
    sheet = Image.new("RGB", (4 * cw + 5 * gap, 4 * ch + 5 * gap + 120), "#1d1f2b")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(HERE.parent / "icons" / "build" / "fonts" / "Lilita.ttf"), 64)
    title = "Mountain Range - the 16 animals"
    d.text(((sheet.width - d.textlength(title, font=font)) / 2, 30), title, fill="#ffffff", font=font)
    for k, (png, _) in enumerate(info):
        im = Image.open(png).convert("RGBA").resize((cw, ch), Image.LANCZOS)
        sheet.paste(im, (gap + (k % 4) * (cw + gap), 120 + gap + (k // 4) * (ch + gap)), im)
    sheet.save(out.parent / "alle-dieren.png")
    for png, meta in info:
        print(f"{meta[1]:10} {meta[0]:16} {meta[2]:15} -> {png.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()
