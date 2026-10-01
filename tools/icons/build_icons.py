#!/usr/bin/env python3
"""Draws the shop icons (game passes and developer products) as cartoon vector art and renders them to PNG.

Every icon is 512 x 512, the size Roblox asks for. Game pass icons are shown as a circle on the store page,
so everything important stays inside the middle circle; the background fills the corners for square displays.

    python3 tools/icons/build_icons.py            -> icons/*.png and icons/preview.png (needs node + playwright)

The fonts (Lilita One and Fredoka, both SIL Open Font License) are downloaded on the first run.
"""

import base64
import json
import math
import subprocess
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BUILD = HERE / "build"
OUT_DIR = ROOT / "icons"

FONTS = {
    "Lilita": "https://raw.githubusercontent.com/google/fonts/main/ofl/lilitaone/LilitaOne-Regular.ttf",
    "Fredoka": "https://raw.githubusercontent.com/google/fonts/main/ofl/fredoka/Fredoka%5Bwdth%2Cwght%5D.ttf",
}

OUT = "#24123f"          # outline colour
GOLD = ("#ffd23f", "#e88f12", "#fff3a8")     # base, shadow, light
WHITE = "#ffffff"


# ------------------------------------------------------------------ basics ---

def font_css():
    css = []
    for name, url in FONTS.items():
        path = BUILD / "fonts" / f"{name}.ttf"
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, path)
        data = base64.b64encode(path.read_bytes()).decode()
        css.append(f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{data}) format('truetype');}}")
    return "".join(css)


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def ellipse_d(cx, cy, rx, ry):
    return (f"M{f(cx - rx)},{f(cy)} a{f(rx)},{f(ry)} 0 1,0 {f(2 * rx)},0 a{f(rx)},{f(ry)} 0 1,0 {f(-2 * rx)},0 Z")


def rrect_d(x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    return (f"M{f(x + r)},{f(y)} H{f(x + w - r)} Q{f(x + w)},{f(y)} {f(x + w)},{f(y + r)} V{f(y + h - r)} "
            f"Q{f(x + w)},{f(y + h)} {f(x + w - r)},{f(y + h)} H{f(x + r)} Q{f(x)},{f(y + h)} {f(x)},{f(y + h - r)} "
            f"V{f(y + r)} Q{f(x)},{f(y)} {f(x + r)},{f(y)} Z")


def poly_d(points):
    return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in points) + " Z"


def star_d(cx, cy, r_out, r_in, n=5, rot=-90):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly_d(pts)


def sparkle_d(x, y, r):
    """A four-pointed twinkle."""
    k = r * 0.22
    return (f"M{f(x)},{f(y - r)} Q{f(x + k)},{f(y - k)} {f(x + r)},{f(y)} Q{f(x + k)},{f(y + k)} {f(x)},{f(y + r)} "
            f"Q{f(x - k)},{f(y + k)} {f(x - r)},{f(y)} Q{f(x - k)},{f(y - k)} {f(x)},{f(y - r)} Z")


class Icon:
    def __init__(self, name, title):
        self.name, self.title = name, title
        self.defs, self.body, self.n = [], [], 0

    def uid(self, prefix):
        self.n += 1
        return f"{prefix}{self.n}"

    def add(self, *parts):
        self.body.extend(parts)

    def grad(self, stops, x1=0, y1=0, x2=0, y2=1):
        gid = self.uid("g")
        s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
        self.defs.append(f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>')
        return f"url(#{gid})"

    def radial(self, stops, cx=0.5, cy=0.5, r=0.5):
        gid = self.uid("r")
        s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
        self.defs.append(f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>')
        return f"url(#{gid})"

    def svg(self, css):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
                f'<style>{css}</style><defs>{COMMON_DEFS}{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')


COMMON_DEFS = (
    '<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>'
    '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="7" result="b"/>'
    '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    '<filter id="bigglow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="16"/></filter>'
)


def cel(ic, d, base, dark, off=(-10, -12), highlight=None, sw=10, stroke=OUT, fill_rule="nonzero"):
    """A cartoon shape: the shadow colour, the base colour shifted up-left over it (that leaves a shadow along
    the bottom-right edge), an optional highlight, and a thick outline on top."""
    cid = ic.uid("c")
    ic.defs.append(f'<clipPath id="{cid}"><path d="{d}" clip-rule="{fill_rule}"/></clipPath>')
    ic.add(f'<path d="{d}" fill="{dark}" fill-rule="{fill_rule}"/>',
           f'<g clip-path="url(#{cid})"><path d="{d}" fill="{base}" fill-rule="{fill_rule}" '
           f'transform="translate({off[0]},{off[1]})"/>{highlight or ""}</g>')
    if sw:
        ic.add(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" '
               f'stroke-linecap="round" fill-rule="{fill_rule}"/>')


def outline(ic, d, sw=10, stroke=OUT):
    ic.add(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" '
           f'stroke-linecap="round"/>')


def shine(d, opacity=0.55):
    return f'<path d="{d}" fill="#ffffff" opacity="{opacity}"/>'


def shadow(ic, cx, cy, rx, ry, opacity=0.3):
    ic.add(f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="#120626" opacity="{opacity}" '
           f'filter="url(#soft)"/>')


def sparkles(ic, spots, color=WHITE, opacity=0.95):
    for x, y, r in spots:
        ic.add(f'<path d="{sparkle_d(x, y, r)}" fill="{color}" opacity="{opacity}"/>')


def background(ic, inner, outer, rays=0.13, center=(256, 236), ray_color=WHITE):
    bg = ic.radial([(0, inner, 1), (1, outer, 1)], cx=center[0] / 512, cy=center[1] / 512, r=0.62)
    ic.add(f'<rect width="512" height="512" fill="{bg}"/>')
    cx, cy = center
    wedges = []
    for i in range(18):
        a0, a1 = math.radians(i * 20 - 5), math.radians(i * 20 + 5)
        wedges.append(poly_d([(cx, cy), (cx + 520 * math.cos(a0), cy + 520 * math.sin(a0)),
                              (cx + 520 * math.cos(a1), cy + 520 * math.sin(a1))]))
    fade = ic.radial([(0, ray_color, rays), (0.75, ray_color, rays * 0.5), (1, ray_color, 0)],
                     cx=cx / 512, cy=cy / 512, r=0.7)
    ic.add(f'<path d="{" ".join(wedges)}" fill="{fade}"/>')
    vignette = ic.radial([(0.55, "#000000", 0), (1, "#0b0420", 0.45)], r=0.72)
    ic.add(f'<rect width="512" height="512" fill="{vignette}"/>')


def label(ic, text, x, y, size, fill=None, rot=0, sw=None, stroke=OUT, font="Lilita", spacing=0):
    """Big chunky text with a thick outline, a drop shadow and a glossy two-tone fill."""
    fill = fill or ic.grad([(0, "#fffbe0"), (0.42, "#ffe14d"), (0.58, "#ffb81c"), (1, "#ff8a00")])
    sw = sw or size * 0.15
    common = (f'font-family="{font}" font-size="{size}" text-anchor="middle" letter-spacing="{spacing}" '
              f'stroke-linejoin="round" paint-order="stroke"')
    ic.add(f'<g transform="rotate({rot} {x} {y})">',
           f'<text x="{x}" y="{y + size * 0.07}" {common} fill="{stroke}" stroke="{stroke}" '
           f'stroke-width="{sw}">{text}</text>',
           f'<text x="{x}" y="{y}" {common} fill="{fill}" stroke="{stroke}" stroke-width="{sw}">{text}</text>',
           '</g>')


# ----------------------------------------------------------------- objects ---

def coin_face(ic, cx, cy, r, emblem="star"):
    """A gold coin seen from the front."""
    cel(ic, ellipse_d(cx, cy, r, r), GOLD[0], GOLD[1], off=(-r * 0.1, -r * 0.12), sw=max(6, r * 0.11))
    inner = ellipse_d(cx, cy, r * 0.72, r * 0.72)
    ic.add(f'<path d="{inner}" fill="none" stroke="{GOLD[1]}" stroke-width="{f(r * 0.07)}"/>')
    if emblem == "star":
        ic.add(f'<path d="{star_d(cx + r * 0.03, cy + r * 0.05, r * 0.46, r * 0.2)}" fill="{GOLD[1]}"/>',
               f'<path d="{star_d(cx, cy, r * 0.46, r * 0.2)}" fill="#fff2a0"/>')
    ic.add(f'<path d="M{f(cx - r * 0.62)},{f(cy - r * 0.2)} A{f(r * 0.66)},{f(r * 0.66)} 0 0,1 {f(cx - r * 0.1)},'
           f'{f(cy - r * 0.68)}" fill="none" stroke="#ffffff" stroke-width="{f(r * 0.12)}" stroke-linecap="round" '
           f'opacity="0.7"/>')


def coin_flat(ic, cx, cy, rx, t=None, sw=7):
    """A gold coin lying flat (seen from above at an angle): the edge, then the top."""
    ry = rx * 0.42
    t = t if t is not None else rx * 0.28
    side = (f"M{f(cx - rx)},{f(cy)} V{f(cy + t)} A{f(rx)},{f(ry)} 0 0,0 {f(cx + rx)},{f(cy + t)} V{f(cy)} "
            f"A{f(rx)},{f(ry)} 0 0,0 {f(cx - rx)},{f(cy)} Z")
    ic.add(f'<path d="{side}" fill="{GOLD[1]}" stroke="{OUT}" stroke-width="{sw}" stroke-linejoin="round"/>')
    for k in range(1, 6):
        x = cx - rx + 2 * rx * k / 6
        dy = ry * math.sqrt(max(0, 1 - ((x - cx) / rx) ** 2))
        ic.add(f'<line x1="{f(x)}" y1="{f(cy + dy + 2)}" x2="{f(x)}" y2="{f(cy + dy + t - 2)}" stroke="#b86a08" '
               f'stroke-width="{f(rx * 0.06)}"/>')
    top = ellipse_d(cx, cy, rx, ry)
    ic.add(f'<path d="{top}" fill="{GOLD[0]}" stroke="{OUT}" stroke-width="{sw}"/>',
           f'<path d="{ellipse_d(cx, cy, rx * 0.7, ry * 0.7)}" fill="none" stroke="{GOLD[1]}" '
           f'stroke-width="{f(rx * 0.07)}"/>',
           f'<path d="{ellipse_d(cx - rx * 0.25, cy - ry * 0.3, rx * 0.32, ry * 0.18)}" fill="#ffffff" opacity="0.6"/>')


def coin_stack(ic, cx, bottom, rx, n, jitter=None):
    t = rx * 0.28
    jitter = jitter or [0] * n
    for i in range(n):
        coin_flat(ic, cx + jitter[i % len(jitter)], bottom - i * (t + 1), rx, t)


def money_bag(ic, cx, cy, w, h, emblem="paw", bag=("#f0c27a", "#bf7f36"), tie="#e23d3d"):
    W, H = w, h
    body = (f"M{f(cx - 0.17 * W)},{f(cy - 0.4 * H)} C{f(cx - 0.66 * W)},{f(cy - 0.18 * H)} {f(cx - 0.62 * W)},"
            f"{f(cy + 0.5 * H)} {f(cx)},{f(cy + 0.5 * H)} C{f(cx + 0.62 * W)},{f(cy + 0.5 * H)} {f(cx + 0.66 * W)},"
            f"{f(cy - 0.18 * H)} {f(cx + 0.17 * W)},{f(cy - 0.4 * H)} Z")
    top = (f"M{f(cx - 0.16 * W)},{f(cy - 0.38 * H)} L{f(cx - 0.34 * W)},{f(cy - 0.62 * H)} Q{f(cx - 0.16 * W)},"
           f"{f(cy - 0.54 * H)} {f(cx)},{f(cy - 0.66 * H)} Q{f(cx + 0.16 * W)},{f(cy - 0.54 * H)} {f(cx + 0.34 * W)},"
           f"{f(cy - 0.62 * H)} L{f(cx + 0.16 * W)},{f(cy - 0.38 * H)} Z")
    cel(ic, top, bag[0], bag[1], off=(-6, -6))
    cel(ic, body, bag[0], bag[1], off=(-0.07 * W, -0.06 * H),
        highlight=shine(ellipse_d(cx - 0.26 * W, cy - 0.05 * H, 0.09 * W, 0.16 * H), 0.45))
    cel(ic, rrect_d(cx - 0.22 * W, cy - 0.46 * H, 0.44 * W, 0.11 * H, 0.05 * H), tie, "#a3202a", off=(-3, -3), sw=8)
    if emblem == "paw":
        px, py, s = cx, cy + 0.12 * H, 0.2 * W
        ic.add(f'<g fill="{bag[1]}">'
               f'<path d="{ellipse_d(px, py + s * 0.25, s * 0.55, s * 0.45)}"/>'
               + "".join(f'<path d="{ellipse_d(px + dx * s, py + dy * s, s * 0.2, s * 0.25)}"/>'
                         for dx, dy in ((-0.62, -0.42), (-0.22, -0.72), (0.22, -0.72), (0.62, -0.42)))
               + '</g>')


def clover(ic, cx, cy, s, rot=0, colors=("#4ee36b", "#1f9a3a"), sw=9, stem=True):
    leaves = []
    for k in range(4):
        a = rot + 45 + 90 * k
        leaf = (f"M0,0 C{f(-s * 0.95)},{f(-s * 0.35)} {f(-s * 0.8)},{f(-s * 1.18)} {f(-s * 0.27)},{f(-s * 1.08)} "
                f"C{f(-s * 0.09)},{f(-s * 1.05)} 0,{f(-s * 0.92)} 0,{f(-s * 0.84)} "
                f"C0,{f(-s * 0.92)} {f(s * 0.09)},{f(-s * 1.05)} {f(s * 0.27)},{f(-s * 1.08)} "
                f"C{f(s * 0.8)},{f(-s * 1.18)} {f(s * 0.95)},{f(-s * 0.35)} 0,0 Z")
        leaves.append(f'<path d="{leaf}" transform="translate({f(cx)},{f(cy)}) rotate({f(a)})"/>')
    if stem:
        ic.add(f'<path d="M{f(cx)},{f(cy)} C{f(cx + s * 0.25)},{f(cy + s * 0.6)} {f(cx + s * 0.55)},'
               f'{f(cy + s * 0.95)} {f(cx + s * 0.95)},{f(cy + s * 1.2)}" fill="none" stroke="{OUT}" '
               f'stroke-width="{f(s * 0.24 + sw)}" stroke-linecap="round"/>',
               f'<path d="M{f(cx)},{f(cy)} C{f(cx + s * 0.25)},{f(cy + s * 0.6)} {f(cx + s * 0.55)},'
               f'{f(cy + s * 0.95)} {f(cx + s * 0.95)},{f(cy + s * 1.2)}" fill="none" stroke="{colors[1]}" '
               f'stroke-width="{f(s * 0.24)}" stroke-linecap="round"/>')
    ic.add(f'<g stroke="{OUT}" stroke-width="{sw * 2}" stroke-linejoin="round" fill="{OUT}">{"".join(leaves)}</g>')
    ic.add(f'<g fill="{colors[1]}">{"".join(leaves)}</g>')
    cid = ic.uid("c")
    ic.defs.append(f'<clipPath id="{cid}">{"".join(leaves)}</clipPath>')
    ic.add(f'<g clip-path="url(#{cid})"><g fill="{colors[0]}" transform="translate({f(-s * 0.1)},{f(-s * 0.12)})">'
           f'{"".join(leaves)}</g>')
    for k in range(4):   # veins and a shine on every leaf
        a = math.radians(rot + 45 + 90 * k - 90)
        x2, y2 = cx + math.cos(a) * s * 0.8, cy + math.sin(a) * s * 0.8
        ic.add(f'<line x1="{f(cx)}" y1="{f(cy)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{colors[1]}" '
               f'stroke-width="{f(s * 0.07)}" stroke-linecap="round" opacity="0.8"/>')
        hx, hy = cx + math.cos(a - 0.35) * s * 0.62, cy + math.sin(a - 0.35) * s * 0.62
        ic.add(f'<ellipse cx="{f(hx)}" cy="{f(hy)}" rx="{f(s * 0.13)}" ry="{f(s * 0.08)}" fill="#ffffff" '
               f'opacity="0.55" transform="rotate({f(math.degrees(a) + 90)} {f(hx)} {f(hy)})"/>')
    ic.add('</g>')


def cloud_blob(ic, puffs, light="#eef1ff", dark="#a3afe2", sw=9, lit=(0.28, 0.32)):
    """A fluffy cloud from overlapping circles: one outline around all of them, and each puff lit from the
    top-left so the puffs stand out from each other without lines between them."""
    union = "".join(f'<path d="{ellipse_d(x, y, r, r)}"/>' for x, y, r in puffs)
    ic.add(f'<g fill="{OUT}">' + "".join(f'<path d="{ellipse_d(x, y, r + sw / 2, r + sw / 2)}"/>'
                                         for x, y, r in puffs) + '</g>')
    ic.add(f'<g fill="{dark}">{union}</g>')
    cid = ic.uid("c")
    ic.defs.append(f'<clipPath id="{cid}">{union}</clipPath>')
    ic.add(f'<g clip-path="url(#{cid})"><g fill="{light}">'
           + "".join(f'<path d="{ellipse_d(x - r * lit[0], y - r * lit[1], r * 0.92, r * 0.92)}"/>' for x, y, r in puffs)
           + '</g></g>')


def rope_path(ic, d, width=24, color="#f2c14e", dark="#c98a24"):
    """A twisted rope along a path: outline, rope colour, darker twist marks and a light thread."""
    ic.add(f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="{width + 12}" stroke-linecap="round" '
           f'stroke-linejoin="round"/>',
           f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
           f'stroke-linejoin="round"/>',
           f'<path d="{d}" fill="none" stroke="{dark}" stroke-width="{width}" stroke-dasharray="7 13" '
           f'stroke-linejoin="round"/>',
           f'<path d="{d}" fill="none" stroke="#fff6c8" stroke-width="{width * 0.2}" stroke-dasharray="10 10" '
           f'stroke-linecap="round" opacity="0.8" transform="translate(-2,-4)"/>')


def die(ic, cx, cy, s, rot, pips, color=("#ffffff", "#c9cfe8")):
    """A die (rounded cube) seen from the front with a little depth."""
    ic.add(f'<g transform="rotate({rot} {cx} {cy})">')
    d = rrect_d(cx - s / 2, cy - s / 2, s, s, s * 0.22)
    depth = rrect_d(cx - s / 2 + s * 0.1, cy - s / 2 + s * 0.12, s, s, s * 0.22)
    cel(ic, depth, "#9aa3c8", "#7a83aa", off=(0, 0))
    cel(ic, d, color[0], color[1], off=(-s * 0.06, -s * 0.07))
    spots = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
             4: [(-1, -1), (1, -1), (-1, 1), (1, 1)], 5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
             6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}[pips]
    for x, y in spots:
        ic.add(f'<circle cx="{f(cx + x * s * 0.26)}" cy="{f(cy + y * s * 0.26)}" r="{f(s * 0.09)}" '
               f'fill="{"#e2323c" if pips == 1 else OUT}"/>')
    ic.add('</g>')


def bolt_d(x, y, s, rot=0):
    """A chunky lightning bolt, about s tall, its top at (x, y)."""
    pts = [(0.15, 0), (0.62, 0), (0.42, 0.36), (0.72, 0.36), (0.2, 1.0), (0.34, 0.52), (0.04, 0.52)]
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return poly_d([(x + (px * s * 0.62) * c - (py * s) * sn, y + (px * s * 0.62) * sn + (py * s) * c)
                   for px, py in pts])


def bolt(ic, x, y, s, rot=0, color="#ffe14d", glow=True, sw=8):
    d = bolt_d(x, y, s, rot)
    if glow:
        ic.add(f'<path d="{d}" fill="{color}" filter="url(#bigglow)" opacity="0.9"/>')
    cel(ic, d, color, "#ff9f1a", off=(-s * 0.04, -s * 0.03), sw=sw)


# ------------------------------------------------------------------- icons ---

def zoo_income():
    ic = Icon("2xZooIncome", "2x Zoo Income")
    background(ic, "#8af59a", "#0a7a3c")
    sparkles(ic, [(96, 110, 18), (420, 96, 22), (440, 300, 14), (70, 300, 12)])
    shadow(ic, 256, 410, 170, 26)
    coin_stack(ic, 118, 380, 54, 5, jitter=[0, 4, -3, 5, 0])
    coin_stack(ic, 396, 386, 50, 4, jitter=[0, -4, 3, 0])
    money_bag(ic, 256, 248, 250, 290)
    coin_face(ic, 150, 196, 40)
    coin_face(ic, 372, 210, 34)
    label(ic, "2X", 256, 448, 158, rot=-6)
    return ic


def lucky_wrangler():
    ic = Icon("LuckyWrangler", "Lucky Wrangler")
    background(ic, "#a6ecff", "#1767c4")
    sparkles(ic, [(92, 120, 20), (424, 110, 16), (434, 250, 12), (86, 270, 12)])
    shadow(ic, 256, 420, 170, 24)
    # The lasso loop: back half, the clover, then the front half, so the loop goes around it.
    loop = ellipse_d(256, 232, 168, 150)
    back = "M88,232 A168,150 0 0,1 424,232"
    front = "M424,232 A168,150 0 0,1 88,232"
    rope_path(ic, back)
    clover(ic, 250, 222, 92, rot=8)
    rope_path(ic, front)
    # Honda knot and the tail of the rope.
    rope_path(ic, "M372,350 C410,380 430,420 468,430", width=22)
    cel(ic, rrect_d(352, 326, 50, 36, 12), "#d99a3a", "#a86a1e", off=(-4, -4), sw=8)
    die(ic, 142, 400, 86, -14, 6)
    die(ic, 248, 418, 72, 10, 5)
    _ = loop
    return ic


def vip():
    ic = Icon("VIP", "VIP")
    background(ic, "#e7a6ff", "#4a1592")
    sparkles(ic, [(88, 92, 22), (430, 120, 18), (440, 330, 14), (74, 340, 14), (380, 52, 10)], color="#fff4b0")
    shadow(ic, 256, 300, 150, 18, 0.25)
    # Crown.
    pts = [(132, 250), (124, 118), (196, 172), (256, 92), (316, 172), (388, 118), (380, 250)]
    crown = poly_d(pts)
    cel(ic, crown, GOLD[0], GOLD[1], off=(-12, -12),
        highlight=shine("M150,140 L196,182 L176,236 L148,236 Z", 0.45))
    for x, y, r in ((124, 112, 17), (256, 84, 20), (388, 112, 17)):
        cel(ic, ellipse_d(x, y, r, r), GOLD[0], GOLD[1], off=(-4, -4), sw=8)
    cel(ic, rrect_d(122, 222, 268, 54, 16), "#ffc22e", "#d97c0c", off=(-8, -8))
    for x, color, dark in ((178, "#ff4d6d", "#b5163a"), (256, "#4dc3ff", "#1474c4"), (334, "#5ee35e", "#1e9a3a")):
        cel(ic, f"M{x},236 L{x + 16},249 L{x},262 L{x - 16},249 Z", color, dark, off=(-3, -3), sw=6)
    # VIP on a ribbon.
    ribbon = "M66,330 L118,318 L108,350 L118,382 L66,394 L82,362 Z M446,330 L394,318 L404,350 L394,382 L446,394 L430,362 Z"
    cel(ic, ribbon, "#c2185b", "#7a0e3a", off=(0, 0))
    cel(ic, "M104,312 Q256,286 408,312 L408,394 Q256,368 104,394 Z", "#ff3d7f", "#b5164f", off=(0, -10))
    label(ic, "VIP", 256, 386, 128, spacing=4)
    return ic


def big_backpack():
    ic = Icon("BigBackpack", "Big Backpack")
    background(ic, "#8ff7e4", "#0a7c78")
    sparkles(ic, [(90, 110, 18), (430, 96, 20), (440, 250, 12), (76, 300, 12)])
    shadow(ic, 256, 446, 150, 22)
    leather, dark = "#c47a3c", "#8d4c1f"
    # Things sticking out of the top: a coil of rope and coins.
    for i, (x, y) in enumerate(((330, 120), (362, 138), (300, 130))):
        coin_face(ic, x, y, 30)
    ic.add(f'<path d="{ellipse_d(196, 128, 52, 34)}" fill="none" stroke="{OUT}" stroke-width="30"/>',
           f'<path d="{ellipse_d(196, 128, 52, 34)}" fill="none" stroke="#e8b45a" stroke-width="18"/>',
           f'<path d="{ellipse_d(196, 128, 52, 34)}" fill="none" stroke="#b7802f" stroke-width="18" '
           f'stroke-dasharray="6 12"/>')
    # Handle, body, side pockets, flap, front pocket, straps and buckles.
    outline(ic, "M222,140 C222,96 290,96 290,140", sw=26)
    ic.add('<path d="M222,140 C222,96 290,96 290,140" fill="none" stroke="#8d4c1f" stroke-width="14" '
           'stroke-linecap="round"/>')
    cel(ic, rrect_d(92, 230, 70, 150, 26), leather, dark, off=(-8, -8))
    cel(ic, rrect_d(350, 230, 70, 150, 26), leather, dark, off=(-8, -8))
    cel(ic, rrect_d(126, 140, 260, 300, 60), leather, dark, off=(-16, -16),
        highlight=shine(rrect_d(150, 166, 26, 120, 13), 0.3))
    cel(ic, "M126,206 Q126,140 196,140 L316,140 Q386,140 386,206 L386,250 Q256,292 126,250 Z", "#d68d48", dark,
        off=(-10, -10))
    ic.add('<path d="M140,240 Q256,280 372,240" fill="none" stroke="#f3c48a" stroke-width="5" '
           'stroke-dasharray="12 9" stroke-linecap="round"/>')
    cel(ic, rrect_d(166, 300, 180, 116, 34), "#d68d48", dark, off=(-10, -10))
    ic.add('<path d="M184,318 H328" fill="none" stroke="#f3c48a" stroke-width="5" stroke-dasharray="12 9" '
           'stroke-linecap="round"/>')
    for x in (196, 316):
        cel(ic, rrect_d(x - 15, 206, 30, 120, 8), "#6b3a17", "#4a250c", off=(-4, -4), sw=8)
        cel(ic, rrect_d(x - 22, 284, 44, 34, 8), GOLD[0], GOLD[1], off=(-4, -4), sw=8)
        ic.add(f'<rect x="{x - 9}" y="294" width="18" height="14" rx="4" fill="#6b3a17"/>')
    # +50 badge.
    cel(ic, star_d(392, 392, 84, 64, n=12), "#ff4d4d", "#c41f2c", off=(-8, -8))
    label(ic, "+50", 392, 414, 66)
    return ic


def unicorn_head(ic):
    """The Thunder Unicorn's head and neck, facing right, with its storm cloud mane and golden horn."""
    coat, coat_dark, light = "#6a7cf0", "#3f4fb4", "#b9c4ff"
    neck = ("M150,520 C150,440 158,370 186,310 C202,272 214,236 222,206 L330,214 C330,262 318,300 304,332 "
            "C294,384 302,450 322,520 Z")
    head = ("M206,214 C204,172 232,140 280,136 C322,132 356,150 378,182 C396,206 414,236 424,262 "
            "C434,288 422,316 394,322 C366,328 340,322 320,312 C300,302 284,300 268,302 C236,304 210,264 206,214 Z")
    # The mane: one big storm cloud flowing down the back of the neck, blown back by the wind.
    low = [(142, 346, 48), (100, 374, 36), (130, 400, 52), (84, 430, 38), (124, 456, 56), (76, 486, 44),
           (160, 488, 50), (110, 520, 60)]
    high = [(250, 142, 30), (226, 152, 32), (204, 178, 34), (186, 214, 40), (150, 222, 26), (168, 254, 42),
            (128, 268, 30), (154, 298, 46), (112, 320, 32), (136, 330, 34)]
    cloud_blob(ic, low, light="#c5cbe8", dark="#7b84b8", lit=(0.2, 0.24))
    cloud_blob(ic, high, light="#e9ecfb", dark="#9aa4d6", lit=(0.2, 0.24))
    for x, y, sz, r in ((70, 236, 70, -24), (40, 360, 66, -12), (36, 470, 56, -20)):
        bolt(ic, x, y, sz, rot=r, sw=6)
    cel(ic, neck, coat, coat_dark, off=(-14, -10))
    cel(ic, head, coat, coat_dark, off=(-12, -12),
        highlight=shine("M236,190 C248,160 280,150 310,152 C286,162 262,178 252,206 Z", 0.35))
    muzzle = ("M360,236 C392,226 424,246 428,276 C432,306 410,326 382,324 C356,322 336,304 336,276 "
              "C336,256 344,242 360,236 Z")
    cel(ic, muzzle, light, "#8f9be6", off=(-8, -8))
    ic.add(f'<path d="{ellipse_d(398, 276, 9, 12)}" fill="#33307a"/>',
           '<path d="M372,304 Q390,314 408,304" fill="none" stroke="#33307a" stroke-width="6" stroke-linecap="round"/>')
    ear = "M232,168 C218,126 226,94 240,72 C260,96 272,126 266,166 Z"
    cel(ic, ear, coat, coat_dark, off=(-6, -6))
    ic.add('<path d="M238,154 C232,126 236,106 242,94 C252,112 256,132 252,154 Z" fill="#4fd6ff" filter="url(#glow)"/>')
    # Horn: a golden spiral, crackling with electricity at the tip.
    horn = "M264,150 L366,22 L302,166 Z"
    ic.add(f'<path d="{horn}" fill="#ffe14d" filter="url(#bigglow)" opacity="0.6"/>')
    cel(ic, horn, "#ffd23f", "#e88f12", off=(-4, -6), sw=9)
    for t in (0.22, 0.42, 0.6, 0.76):
        ax, ay = 264 + (366 - 264) * t, 150 + (22 - 150) * t
        bx, by = 302 + (366 - 302) * t, 166 + (22 - 166) * t
        ic.add(f'<path d="M{f(ax)},{f(ay)} L{f(bx)},{f(by - 10)}" stroke="#c96a0a" stroke-width="6" '
               f'stroke-linecap="round"/>')
    for d in ("M366,22 L392,36 L382,48 L410,58", "M366,22 L344,8 L352,0", "M366,22 L398,10 L404,22 L428,14"):
        ic.add(f'<path d="{d}" fill="none" stroke="#4fd6ff" stroke-width="7" stroke-linejoin="round" '
               f'stroke-linecap="round" filter="url(#glow)"/>',
               f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="3" stroke-linejoin="round" '
               f'stroke-linecap="round"/>')
    ic.add(f'<path d="{sparkle_d(366, 22, 30)}" fill="#ffffff" filter="url(#glow)"/>')
    # Forelock, in front of the horn's base.
    cloud_blob(ic, [(254, 148, 30), (228, 158, 30), (210, 186, 28), (276, 140, 22)])
    # Eye: big, glossy, electric blue.
    cel(ic, ellipse_d(318, 214, 34, 40), "#ffffff", "#d7def5", off=(-4, -4), sw=8)
    ic.add(f'<path d="{ellipse_d(324, 220, 25, 31)}" fill="#26b8f0"/>',
           f'<path d="{ellipse_d(324, 226, 25, 24)}" fill="#4fd6ff"/>',
           f'<path d="{ellipse_d(326, 222, 13, 18)}" fill="#141033"/>',
           f'<path d="{ellipse_d(314, 206, 9, 10)}" fill="#ffffff"/>',
           f'<path d="{ellipse_d(334, 236, 5, 5)}" fill="#ffffff"/>',
           '<path d="M286,186 Q300,170 324,172" fill="none" stroke="#141033" stroke-width="7" stroke-linecap="round"/>',
           '<path d="M288,198 L274,190 M296,188 L286,176" stroke="#141033" stroke-width="6" stroke-linecap="round"/>',
           f'<path d="{ellipse_d(352, 262, 16, 9)}" fill="#ff8ccf" opacity="0.7"/>')


def thunder_unicorn():
    ic = Icon("ThunderUnicorn", "Thunder Unicorn")
    background(ic, "#5d6cff", "#120c3a", rays=0.1, center=(286, 200))
    # Lightning in the sky behind.
    for x, y, s, r in ((62, 40, 150, 12), (410, 250, 120, -18), (40, 250, 90, 20)):
        ic.add(f'<path d="{bolt_d(x, y, s, r)}" fill="#fff7c2" opacity="0.35" filter="url(#glow)"/>')
    sparkles(ic, [(452, 110, 16), (130, 96, 12), (468, 214, 10)], color="#bff3ff")
    ic.add('<g transform="translate(-24,18)">')
    unicorn_head(ic)
    ic.add('</g>')
    # Storm clouds in front, along the bottom.
    cloud_blob(ic, [(300, 500, 50), (360, 470, 44), (420, 490, 50), (480, 470, 46), (250, 520, 44)],
               light="#6f78c2", dark="#3a3f86", lit=(0.25, 0.35))
    bolt(ic, 420, 300, 92, rot=12, sw=7)
    label(ic, "5X", 340, 430, 104, rot=-8)
    return ic


def auto_sell():
    ic = Icon("AutoSell", "Auto-Sell")
    background(ic, "#ffd98a", "#d4500b")
    sparkles(ic, [(84, 96, 18), (436, 104, 20), (446, 300, 12), (66, 300, 12)])
    shadow(ic, 256, 380, 120, 20)
    # Two circular arrows around a big coin.
    cx, cy, r = 256, 226, 150

    def arc(a0, a1):
        p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
        p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
        return f"M{f(p0[0])},{f(p0[1])} A{r},{r} 0 0,1 {f(p1[0])},{f(p1[1])}", p1, a1

    for a0, a1 in ((200, 330), (20, 150)):
        d, (ex, ey), a = arc(a0, a1)
        ic.add(f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="44" stroke-linecap="round"/>',
               f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="28" stroke-linecap="round"/>')
        t = math.radians(a + 90)   # direction of travel at the end
        n = math.radians(a)
        tip = (ex + 34 * math.cos(t), ey + 34 * math.sin(t))
        b1 = (ex + 34 * math.cos(n), ey + 34 * math.sin(n))
        b2 = (ex - 34 * math.cos(n), ey - 34 * math.sin(n))
        cel(ic, poly_d([tip, b1, b2]), "#ffffff", "#d6dbe8", off=(0, 0), sw=12)
    coin_face(ic, cx, cy, 106)
    # AUTO on a green "on" switch.
    cel(ic, rrect_d(104, 372, 304, 92, 46), "#3ddc6e", "#159447", off=(-8, -8))
    cel(ic, ellipse_d(360, 418, 34, 34), "#ffffff", "#d6dbe8", off=(-4, -4), sw=8)
    label(ic, "AUTO", 220, 442, 72, fill="#ffffff", sw=12)
    return ic


def coin_pack(size_name, colors, art):
    ic = Icon(f"Coins{size_name}", f"Coin Pack {size_name}")
    background(ic, *colors)
    art(ic)
    # Size badge.
    w = 104 if len(size_name) == 1 else 140
    cel(ic, rrect_d(256 - w / 2, 404, w, 76, 38), "#ffffff", "#d6dbe8", off=(-6, -6))
    label(ic, size_name, 256, 466, 70, sw=12)
    return ic


def pack_s(ic):
    sparkles(ic, [(110, 120, 16), (404, 120, 14)])
    shadow(ic, 256, 378, 130, 22)
    coin_stack(ic, 176, 354, 52, 3, jitter=[0, 3, -2])
    coin_stack(ic, 336, 356, 48, 2, jitter=[0, -3])
    coin_face(ic, 258, 236, 78)
    coin_face(ic, 168, 190, 40)


def pack_m(ic):
    sparkles(ic, [(96, 110, 18), (420, 100, 18), (440, 280, 12)])
    shadow(ic, 256, 384, 160, 24)
    coin_stack(ic, 120, 370, 50, 4, jitter=[0, 3, -3, 2])
    coin_stack(ic, 394, 372, 48, 3, jitter=[0, -3, 2])
    money_bag(ic, 256, 236, 220, 260, emblem="paw")
    coin_face(ic, 360, 206, 36)


def pack_l(ic):
    sparkles(ic, [(86, 96, 20), (430, 92, 20), (446, 260, 14), (66, 250, 12)], color="#fff4b0")
    shadow(ic, 256, 396, 180, 26)
    wood, wood_dark = "#b9662e", "#7f3d17"
    # Open lid (behind), a heap of gold, the chest and its iron bands.
    cel(ic, "M120,214 L136,104 Q256,70 376,104 L392,214 Z", wood, wood_dark, off=(-10, -10))
    cel(ic, "M150,196 L160,124 Q256,98 352,124 L362,196 Z", "#5b2a10", "#3e1a08", off=(0, 0), sw=6)
    heap = "M110,262 C120,200 170,170 214,186 C238,150 290,150 312,184 C350,170 398,196 404,262 Z"
    cel(ic, heap, GOLD[0], GOLD[1], off=(-10, -10))
    for x, y, r in ((170, 214, 30), (226, 190, 32), (288, 192, 30), (344, 220, 30), (256, 232, 34), (198, 246, 28),
                    (318, 248, 28)):
        coin_face(ic, x, y, r)
    cel(ic, f'M{f(250)},{f(176)} L274,150 L298,176 L274,202 Z', "#ff4d6d", "#b5163a", off=(-4, -4), sw=7)
    cel(ic, rrect_d(104, 250, 304, 150, 22), wood, wood_dark, off=(-12, -12),
        highlight=shine(rrect_d(124, 268, 20, 100, 10), 0.3))
    for x in (150, 362):
        cel(ic, rrect_d(x - 14, 250, 28, 150, 6), "#8a8fa8", "#5b5f78", off=(-4, -4), sw=8)
    cel(ic, rrect_d(104, 250, 304, 26, 8), "#8a8fa8", "#5b5f78", off=(-4, -4), sw=8)
    cel(ic, rrect_d(232, 286, 48, 56, 12), GOLD[0], GOLD[1], off=(-5, -5), sw=8)
    ic.add('<path d="M256,304 L256,326" stroke="#24123f" stroke-width="8" stroke-linecap="round"/>')


def pack_xl(ic):
    sparkles(ic, [(80, 92, 22), (436, 88, 22), (450, 250, 14), (60, 240, 14), (256, 46, 14)], color="#fff4b0")
    shadow(ic, 256, 404, 190, 26)
    # A mine cart, overflowing with gold, gems and sparkles.
    heap = "M96,230 C100,150 170,110 230,128 C260,86 330,94 352,140 C400,138 428,190 420,234 Z"
    cel(ic, heap, GOLD[0], GOLD[1], off=(-10, -10))
    for x, y, r in ((146, 186, 32), (204, 156, 34), (262, 142, 30), (318, 160, 32), (372, 196, 30), (240, 200, 34),
                    (300, 214, 30), (176, 222, 28), (350, 230, 26)):
        coin_face(ic, x, y, r)
    for x, y, c, cd in ((222, 118, "#4dc3ff", "#1474c4"), (330, 124, "#ff4d6d", "#b5163a"),
                        (120, 218, "#5ee35e", "#1e9a3a")):
        cel(ic, f"M{x},{y - 22} L{x + 20},{y} L{x},{y + 22} L{x - 20},{y} Z", c, cd, off=(-4, -4), sw=7)
    cart = "M76,224 L436,224 L404,382 L108,382 Z"
    cel(ic, cart, "#d0473a", "#8f2219", off=(-12, -12), highlight=shine("M96,240 L130,240 L146,330 L120,330 Z", 0.3))
    cel(ic, rrect_d(66, 214, 380, 30, 10), "#8a8fa8", "#5b5f78", off=(-5, -5), sw=9)
    for x in (156, 356):
        ic.add(f'<path d="M{x},244 L{x - (8 if x < 256 else -8)},382" stroke="{OUT}" stroke-width="20"/>',
               f'<path d="M{x},244 L{x - (8 if x < 256 else -8)},382" stroke="#8a8fa8" stroke-width="10"/>')
    for x in (160, 352):
        cel(ic, ellipse_d(x, 392, 40, 40), "#5b5f78", "#3a3d52", off=(-6, -6))
        cel(ic, ellipse_d(x, 392, 16, 16), GOLD[0], GOLD[1], off=(-3, -3), sw=7)


def income_boost():
    ic = Icon("2xIncomeBoost", "2x Income Boost")
    background(ic, "#ffa07a", "#b3101e")
    # Speed lines.
    for y, x0, w in ((120, 30, 90), (200, 20, 70), (300, 30, 80)):
        ic.add(f'<path d="M{x0},{y} H{x0 + w}" stroke="#ffffff" stroke-width="12" stroke-linecap="round" '
               f'opacity="0.45"/>')
    sparkles(ic, [(436, 84, 20), (452, 250, 12)])
    shadow(ic, 236, 380, 120, 20)
    # Stopwatch with half the dial filled: 30 minutes.
    cx, cy, r = 236, 226, 122
    cel(ic, rrect_d(cx - 26, cy - r - 46, 52, 34, 10), "#c9cfe8", "#8a8fa8", off=(-4, -4), sw=9)
    cel(ic, rrect_d(cx - 14, cy - r - 18, 28, 26, 6), "#c9cfe8", "#8a8fa8", off=(-3, -3), sw=8)
    cel(ic, f"M{cx + 76},{cy - 104} L{cx + 104},{cy - 128} L{cx + 122},{cy - 108} L{cx + 96},{cy - 84} Z",
        "#c9cfe8", "#8a8fa8", off=(-3, -3), sw=8)
    cel(ic, ellipse_d(cx, cy, r, r), GOLD[0], GOLD[1], off=(-12, -12))
    cel(ic, ellipse_d(cx, cy, r * 0.8, r * 0.8), "#ffffff", "#dfe3f0", off=(-6, -6), sw=8)
    ic.add(f'<path d="M{cx},{cy} L{cx},{f(cy - r * 0.8)} A{f(r * 0.8)},{f(r * 0.8)} 0 0,1 {cx},{f(cy + r * 0.8)} Z" '
           f'fill="#ff5a4d" opacity="0.85"/>')
    for k in range(12):
        a = math.radians(k * 30)
        r0, r1 = r * (0.62 if k % 3 == 0 else 0.68), r * 0.76
        ic.add(f'<line x1="{f(cx + r0 * math.sin(a))}" y1="{f(cy - r0 * math.cos(a))}" '
               f'x2="{f(cx + r1 * math.sin(a))}" y2="{f(cy - r1 * math.cos(a))}" stroke="{OUT}" '
               f'stroke-width="{8 if k % 3 == 0 else 5}" stroke-linecap="round"/>')
    ic.add(f'<path d="M{cx},{cy} L{cx},{cy - 70}" stroke="{OUT}" stroke-width="12" stroke-linecap="round"/>',
           f'<path d="M{cx},{cy} L{cx},{cy + 62}" stroke="{OUT}" stroke-width="9" stroke-linecap="round"/>',
           f'<circle cx="{cx}" cy="{cy}" r="13" fill="{OUT}"/>')
    label(ic, "30 MIN", 236, 104, 42, fill="#ffffff", sw=10, font="Lilita")
    label(ic, "2X", 360, 440, 150, rot=-8)
    return ic


def eyes(ic, cx, cy, dx, r):
    for sx in (-1, 1):
        x = cx + sx * dx
        ic.add(f'<path d="{ellipse_d(x, cy, r, r * 1.2)}" fill="#1b1033"/>',
               f'<path d="{ellipse_d(x - r * 0.3, cy - r * 0.4, r * 0.38, r * 0.38)}" fill="#ffffff"/>')


def bear_head(ic, cx, cy, s):
    fur, dark, snout = "#b06d3d", "#7c4421", "#f2d0a4"
    for sx in (-1, 1):
        cel(ic, ellipse_d(cx + sx * s * 0.36, cy - s * 0.36, s * 0.17, s * 0.17), fur, dark, off=(-4, -4), sw=8)
        ic.add(f'<path d="{ellipse_d(cx + sx * s * 0.36, cy - s * 0.36, s * 0.08, s * 0.08)}" fill="#e7a07a"/>')
    cel(ic, ellipse_d(cx, cy, s * 0.5, s * 0.46), fur, dark, off=(-s * 0.06, -s * 0.07))
    cel(ic, ellipse_d(cx, cy + s * 0.16, s * 0.22, s * 0.16), snout, "#d9a874", off=(-3, -3), sw=7)
    ic.add(f'<path d="{ellipse_d(cx, cy + s * 0.09, s * 0.08, s * 0.055)}" fill="#1b1033"/>',
           f'<path d="M{f(cx - s * 0.07)},{f(cy + s * 0.2)} Q{f(cx)},{f(cy + s * 0.26)} {f(cx + s * 0.07)},'
           f'{f(cy + s * 0.2)}" fill="none" stroke="#1b1033" stroke-width="4" stroke-linecap="round"/>')
    eyes(ic, cx, cy - s * 0.06, s * 0.18, s * 0.055)


def deer_head(ic, cx, cy, s):
    fur, dark, snout = "#e0a35e", "#b06d2c", "#fff1dc"
    for sx in (-1, 1):   # antlers
        d = (f"M{f(cx + sx * s * 0.14)},{f(cy - s * 0.36)} L{f(cx + sx * s * 0.3)},{f(cy - s * 0.78)} "
             f"M{f(cx + sx * s * 0.24)},{f(cy - s * 0.62)} L{f(cx + sx * s * 0.48)},{f(cy - s * 0.74)} "
             f"M{f(cx + sx * s * 0.28)},{f(cy - s * 0.74)} L{f(cx + sx * s * 0.2)},{f(cy - s * 0.94)}")
        ic.add(f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="{f(s * 0.12 + 9)}" stroke-linecap="round"/>',
               f'<path d="{d}" fill="none" stroke="#8a5530" stroke-width="{f(s * 0.12)}" stroke-linecap="round"/>')
        ear = (f"M{f(cx + sx * s * 0.3)},{f(cy - s * 0.2)} C{f(cx + sx * s * 0.6)},{f(cy - s * 0.4)} "
               f"{f(cx + sx * s * 0.78)},{f(cy - s * 0.22)} {f(cx + sx * s * 0.66)},{f(cy - s * 0.08)} "
               f"C{f(cx + sx * s * 0.54)},{f(cy + s * 0.02)} {f(cx + sx * s * 0.38)},{f(cy - s * 0.02)} "
               f"{f(cx + sx * s * 0.3)},{f(cy - s * 0.2)} Z")
        cel(ic, ear, fur, dark, off=(-3, -3), sw=8)
    head = (f"M{f(cx)},{f(cy - s * 0.42)} C{f(cx + s * 0.4)},{f(cy - s * 0.42)} {f(cx + s * 0.42)},{f(cy)} "
            f"{f(cx + s * 0.24)},{f(cy + s * 0.32)} C{f(cx + s * 0.14)},{f(cy + s * 0.5)} {f(cx - s * 0.14)},"
            f"{f(cy + s * 0.5)} {f(cx - s * 0.24)},{f(cy + s * 0.32)} C{f(cx - s * 0.42)},{f(cy)} {f(cx - s * 0.4)},"
            f"{f(cy - s * 0.42)} {f(cx)},{f(cy - s * 0.42)} Z")
    cel(ic, head, fur, dark, off=(-s * 0.05, -s * 0.06))
    cel(ic, ellipse_d(cx, cy + s * 0.3, s * 0.17, s * 0.14), snout, "#e8cfae", off=(-3, -3), sw=7)
    ic.add(f'<path d="{ellipse_d(cx, cy + s * 0.25, s * 0.07, s * 0.05)}" fill="#1b1033"/>')
    for x, y in ((-0.2, -0.28), (0.04, -0.3), (0.22, -0.2)):   # spots
        ic.add(f'<path d="{ellipse_d(cx + x * s, cy + y * s, s * 0.04, s * 0.04)}" fill="#fff1dc"/>')
    eyes(ic, cx, cy, s * 0.16, s * 0.06)


def fox_head(ic, cx, cy, s):
    fur, dark, white = "#ff8a3d", "#c9521a", "#ffffff"
    for sx in (-1, 1):
        ear = poly_d([(cx + sx * s * 0.12, cy - s * 0.3), (cx + sx * s * 0.42, cy - s * 0.74),
                      (cx + sx * s * 0.5, cy - s * 0.16)])
        cel(ic, ear, fur, dark, off=(-3, -3), sw=8)
        ic.add(f'<path d="{poly_d([(cx + sx * s * 0.26, cy - s * 0.3), (cx + sx * s * 0.41, cy - s * 0.6), (cx + sx * s * 0.44, cy - s * 0.26)])}" fill="#3a1a12"/>')
    head = (f"M{f(cx - s * 0.5)},{f(cy - s * 0.18)} Q{f(cx)},{f(cy - s * 0.52)} {f(cx + s * 0.5)},{f(cy - s * 0.18)} "
            f"Q{f(cx + s * 0.44)},{f(cy + s * 0.16)} {f(cx)},{f(cy + s * 0.44)} Q{f(cx - s * 0.44)},{f(cy + s * 0.16)} "
            f"{f(cx - s * 0.5)},{f(cy - s * 0.18)} Z")
    cheeks = (f"M{f(cx - s * 0.48)},{f(cy - s * 0.08)} Q{f(cx - s * 0.2)},{f(cy - s * 0.02)} {f(cx)},{f(cy + s * 0.12)} "
              f"Q{f(cx + s * 0.2)},{f(cy - s * 0.02)} {f(cx + s * 0.48)},{f(cy - s * 0.08)} Q{f(cx + s * 0.4)},"
              f"{f(cy + s * 0.18)} {f(cx)},{f(cy + s * 0.44)} Q{f(cx - s * 0.4)},{f(cy + s * 0.18)} "
              f"{f(cx - s * 0.48)},{f(cy - s * 0.08)} Z")
    cel(ic, head, fur, dark, off=(-s * 0.05, -s * 0.06), highlight=f'<path d="{cheeks}" fill="{white}"/>')
    ic.add(f'<path d="{ellipse_d(cx, cy + s * 0.38, s * 0.07, s * 0.05)}" fill="#1b1033"/>')
    eyes(ic, cx, cy - s * 0.06, s * 0.18, s * 0.055)


def lucky_herd():
    ic = Icon("LuckyHerd", "Lucky Herd")
    background(ic, "#ff9de2", "#7a1677", center=(256, 300))
    # A rainbow behind the hill.
    for i, c in enumerate(("#ff4d4d", "#ff9f1a", "#ffe14d", "#4ee36b", "#4dc3ff", "#a36bff")):
        r = 236 - i * 22
        ic.add(f'<path d="M{256 - r},372 A{r},{r} 0 0,1 {256 + r},372" fill="none" stroke="{c}" '
               f'stroke-width="23" opacity="0.9"/>')
    sparkles(ic, [(74, 86, 18), (448, 84, 20), (452, 220, 12), (60, 210, 12)], color="#fff4b0")
    # The herd, glowing gold because Legendary animals are coming.
    ic.add('<ellipse cx="256" cy="300" rx="190" ry="110" fill="#fff3a0" opacity="0.75" filter="url(#bigglow)"/>')
    bear_head(ic, 140, 316, 118)
    fox_head(ic, 372, 318, 112)
    deer_head(ic, 256, 280, 132)
    # The hill in front of them.
    cel(ic, "M-10,380 C80,334 180,350 256,356 C340,362 430,340 522,370 L522,522 L-10,522 Z", "#6fe06a", "#2e9e3e",
        off=(0, -12))
    # A megaphone shouting it out to the server, and the x3 clover.
    ic.add('<g transform="rotate(-18 110 112)">')
    cel(ic, "M66,96 L140,62 L140,162 L66,128 Z", "#ff4d6d", "#b5163a", off=(-4, -4))
    cel(ic, rrect_d(44, 92, 28, 40, 8), "#c9cfe8", "#8a8fa8", off=(-3, -3), sw=8)
    cel(ic, ellipse_d(142, 112, 17, 52), "#ffffff", "#d6dbe8", off=(-3, -3), sw=8)
    for r in (34, 58):
        ic.add(f'<path d="M{160 + r * 0.3},{112 - r} Q{160 + r},{112} {160 + r * 0.3},{112 + r}" fill="none" '
               f'stroke="{OUT}" stroke-width="18" stroke-linecap="round"/>',
               f'<path d="M{160 + r * 0.3},{112 - r} Q{160 + r},{112} {160 + r * 0.3},{112 + r}" fill="none" '
               f'stroke="#ffffff" stroke-width="9" stroke-linecap="round"/>')
    ic.add('</g>')
    clover(ic, 392, 410, 66, rot=12, stem=False)
    label(ic, "x3", 392, 438, 82, fill="#ffffff", sw=13)
    return ic


ICONS = [
    ("pass", zoo_income), ("pass", lucky_wrangler), ("pass", vip), ("pass", big_backpack),
    ("pass", thunder_unicorn), ("pass", auto_sell),
    ("product", lambda: coin_pack("S", ("#a8f59a", "#2a8f36"), pack_s)),
    ("product", lambda: coin_pack("M", ("#9ad8ff", "#1554b8"), pack_m)),
    ("product", lambda: coin_pack("L", ("#e2b0ff", "#5a1aa8"), pack_l)),
    ("product", lambda: coin_pack("XL", ("#ffe08a", "#d4400f"), pack_xl)),
    ("product", income_boost), ("product", lucky_herd),
]


def main():
    css = font_css()
    BUILD.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)
    jobs, made = [], []
    for kind, make in ICONS:
        ic = make()
        svg = BUILD / f"{ic.name}.svg"
        svg.write_text(ic.svg(css))
        jobs.append({"svg": str(svg), "png": str(BUILD / f"{ic.name}@2x.png"), "size": 1024})
        made.append((kind, ic))
    (BUILD / "jobs.json").write_text(json.dumps(jobs))
    subprocess.run(["node", str(HERE / "render.js"), str(BUILD / "jobs.json")], check=True,
                   env={**__import__("os").environ, "NODE_PATH": "/opt/node22/lib/node_modules"})

    from PIL import Image, ImageDraw, ImageFont
    tiles = []
    for (kind, ic), job in zip(made, jobs):
        big = Image.open(job["png"]).convert("RGBA")
        icon = big.resize((512, 512), Image.LANCZOS)
        icon.save(OUT_DIR / f"{ic.name}.png")
        tiles.append((kind, ic.title, icon))
        print(f"{kind:8} {ic.title:18} -> icons/{ic.name}.png")

    # Preview sheet: every icon as Roblox shows a game pass (a circle) or a product (a rounded square).
    cell, pad = 300, 30
    sheet = Image.new("RGB", (6 * cell + pad, 2 * (cell + 60) + pad), "#1d1f2b")
    font = ImageFont.truetype(str(BUILD / "fonts" / "Fredoka.ttf"), 26)
    draw = ImageDraw.Draw(sheet)
    for i, (kind, title, icon) in enumerate(tiles):
        row, col = i // 6, i % 6
        x, y = pad + col * cell, pad + row * (cell + 60)
        small = icon.resize((cell - pad, cell - pad), Image.LANCZOS)
        mask = Image.new("L", small.size, 0)
        md = ImageDraw.Draw(mask)
        if kind == "pass":
            md.ellipse((0, 0, small.width - 1, small.height - 1), fill=255)
        else:
            md.rounded_rectangle((0, 0, small.width - 1, small.height - 1), radius=40, fill=255)
        sheet.paste(small, (x, y), mask)
        tw = draw.textlength(title, font=font)
        draw.text((x + (cell - pad - tw) / 2, y + cell - pad + 12), title, fill="#ffffff", font=font)
    sheet.save(OUT_DIR / "preview.png")
    print("-> icons/preview.png")


if __name__ == "__main__":
    main()
