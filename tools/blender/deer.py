"""The Deer, modeled from its side view on the Forest Biome reference sheet.

Run: python3 tools/blender/deer.py tools/blender/reference/forest_side_views.webp <out_dir> [--debug]
(--debug only writes deer_parts.png, the reference with every part tinted, to check the part outlines.)
Coordinates below are working pixels: the sheet crop (40, 105)-(340, 335) enlarged 4x.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refmodel as rm  # noqa: E402

BOX = (40, 105, 340, 335)
GROUND = 866          # hoof bottoms (wp)
FRONT_CUT = 645       # front legs start below this line
BACK_CUT = 650


def parts(ref):
    full = ref.silhouette(keep=1)
    antler_zone = ref.polygon([(640, 0), (1100, 0), (1100, 215), (990, 238), (930, 248), (900, 250), (880, 256),
                               (862, 262), (840, 258), (826, 246), (800, 214), (760, 196), (640, 196)])
    # the gaps between the tines are real holes, so this outline is not hole-filled
    antler = rm.tidy(ref.silhouette(fill=False) & antler_zone & ~ref.ellipse((797, 259), (37, 50), angle=-18))
    ear = rm.tidy(ref.ellipse((797, 259), (34, 47), angle=-18) & full & ~antler, radius=3, keep_largest=True)

    back_legs = ref.polygon([(140, BACK_CUT), (300, 640), (440, 628), (440, 900), (140, 900)])
    front_legs = ref.polygon([(585, FRONT_CUT), (820, FRONT_CUT), (820, 900), (585, 900)])
    near_back_zone = ref.polygon([(140, 600), (300, 600), (300, 640), (262, 700), (262, 900), (140, 900)])
    front_a_zone = ref.polygon([(585, 560), (694, 560), (694, 645), (696, 700), (697, 740), (700, 900), (585, 900)])

    leg_back_a = full & back_legs & near_back_zone
    leg_back_b = full & back_legs & ~near_back_zone
    leg_front_a = full & front_legs & front_a_zone
    leg_front_b = full & front_legs & ~front_a_zone
    # every leg continues up into the body, so it has no seam where it meets the belly
    leg_back_a |= full & ref.polygon([(190, BACK_CUT + 5), (292, BACK_CUT - 6), (280, 560), (205, 560)])
    leg_back_b |= full & ref.polygon([(275, 700), (325, 660), (360, 600), (300, 590), (270, 640)])
    leg_front_a |= full & ref.polygon([(618, FRONT_CUT + 5), (694, FRONT_CUT + 5), (688, 565), (628, 565)])
    leg_front_b |= full & ref.polygon([(708, FRONT_CUT + 20), (770, FRONT_CUT + 20), (765, 575), (715, 575)])

    body = full & ~antler & ~ear & ~back_legs & ~front_legs
    body |= full & ref.polygon([(762, 318), (800, 280), (838, 256), (852, 266), (842, 322), (782, 336)])  # head under ear
    body &= ~ref.polygon([(640, 0), (1100, 0), (1100, 150), (900, 235), (862, 250), (835, 250), (800, 205), (640, 205)])
    body = rm.tidy(body, radius=3, keep_largest=True)
    # dark paint that is not an outline stroke: hooves and nose
    keep = ref.polygon([(0, 822), (1200, 822), (1200, 920), (0, 920)]) | ref.ellipse((1008, 347), (22, 16))
    return {
        "keep": keep, "full": full, "body": body, "ear": ear, "antler": antler,
        "leg_front_a": leg_front_a, "leg_front_b": leg_front_b, "leg_back_a": leg_back_a, "leg_back_b": leg_back_b,
    }


def build(ref, out):
    import refbuild as rb  # needs bpy
    from zoo_blender import reset

    reset()
    p = parts(ref)
    frame = rb.Frame(ground=GROUND, height_studs=9.0, top=35, center_x=600)
    atlas = rb.Atlas(ref)
    for key in ("body", "ear", "leg_front_a", "leg_front_b", "leg_back_a", "leg_back_b"):
        atlas.add(key, p[key], keep=p["keep"])
    atlas.add("antler", p["antler"], band=12, dark=115)      # pale antlers have a thick dark outline
    mat = rb.material("DeerCoat", atlas.build(str(out / "DeerCoat.png")))
    k = frame.k

    # thickness seen from the front, measured on the front view of the turnaround (1 = round)
    width = rm.soft_map(p["full"].shape, 0.85, [((770, 470), 70, 0.9), ((890, 315), 60, 1.35), ((995, 345), 28, 1.0),
                                                ((215, 480), 30, 0.65)])
    inset = rm.soft_map(p["full"].shape, 28, [((1012, 347), 18, 6)])     # keep the black nose tip on the nose
    body = rb.Piece("Body", p["body"], frame, atlas, "body", step=2.5, width=width, smooth=15, tris=7000, inset=inset)
    # legs are slimmer at the top, so they tuck into the body without a crease
    rows = np.interp(np.arange(p["full"].shape[0]), [560, 660, 730], [0.75, 0.95, 1.15])
    leg_width = np.repeat(rows[:, None], p["full"].shape[1], axis=1)
    legs = {}

    def tuck(side):
        """Legs stand straight below the belly and lean in towards the middle inside the body."""
        def fn(v):
            img_y = frame.ground - v[:, 2] / k
            return np.stack([v[:, 0] + side * k * np.interp(img_y, [560, 665], [0.5, 1.0]), v[:, 1], v[:, 2]], 1)
        return fn

    for key, name, side in (("leg_front_a", "LegFL", -62), ("leg_front_b", "LegFR", 62),
                            ("leg_back_a", "LegBR", 60), ("leg_back_b", "LegBL", -60)):
        leg = rb.Piece(name, p[key], frame, atlas, key, step=1.5, width=leg_width, smooth=10, tris=900, inset=12)
        legs[name] = leg.deform(tuck(side))

    ear = rb.Piece("Ear", p["ear"], frame, atlas, "ear", step=1.0, width=0.25, min_half=2.5, smooth=8, tris=400, inset=4)
    ear_pose = rb.pose(rb.pixel_point(frame, 812, 292), rotate=(0, 50, 32), move=(50 * k, 0, 0), scale=1.3)
    ears = [ear.copy("EarR").transform(ear_pose), ear.transform(rb.mirror(ear_pose))]

    # Seen from the front the antlers grow outward from the head and then turn up (a lyre shape), and
    # tines further forward or back sit further out. The side view stays exactly the drawing.
    base = rb.pixel_point(frame, 860, 255)

    def spread(sign):
        def fn(v):
            dz = np.maximum(v[:, 2] - base.z, 0) / k
            dy = np.abs(v[:, 1] - base.y) / k
            out = 50 + 150 * (1 - np.exp(-dz / 70)) + 0.15 * dy
            return np.stack([v[:, 0] + sign * out * k, v[:, 1], v[:, 2]], 1)
        return fn

    antler = rb.Piece("Antler", p["antler"], frame, atlas, "antler", step=1.0, width=1.0, smooth=8, tris=2000, inset=6)
    antlers = [antler.copy("AntlerR").deform(spread(1)), antler.deform(spread(-1))]

    objs = [rb.join([body.obj] + [e.obj for e in ears] + [a.obj for a in antlers], "Body", mat)]
    for name, leg in legs.items():
        objs.append(rb.join([leg.obj], name, mat))
    rb.export_glb(objs, str(out / "Deer.glb"))
    print("triangles", rb.triangles(objs))
    return frame, objs


def renders(frame, out):
    import refbuild as rb
    k = frame.k
    cam = rb.setup_render(size=(1200, 920), samples=48)
    # side view, framed exactly like the reference crop (1200 x 920 wp around (600, 460))
    target = (0, (600 - frame.cx) * k, (frame.ground - 460) * k)
    rb.render(cam, str(out / "r_side.png"), target, (1, 0, 0), ortho=1200 * k)
    bpy_scene_size(1000, 1000)
    rb.render(cam, str(out / "r_front.png"), (0, 0, 4.6), (0, 1, 0.04), ortho=10.5)
    rb.render(cam, str(out / "r_34.png"), (0, 0.2, 4.4), (0.85, 1.0, 0.3), distance=21, lens=55)
    rb.render(cam, str(out / "r_back34.png"), (0, 0.0, 4.4), (0.9, -0.85, 0.42), distance=21, lens=55)


def bpy_scene_size(w, h):
    import bpy
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = w, h


def sheet(ref, out):
    """Reference next to the model, for checking."""
    from PIL import Image, ImageDraw, ImageFont
    navy, green, panel = (3, 28, 40), (56, 92, 62), (14, 22, 30)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    ref_img = Image.fromarray(ref.image.clip(0, 255).astype("uint8"))

    def on_bg(path, color):
        im = Image.open(path).convert("RGBA")
        return Image.alpha_composite(Image.new("RGBA", im.size, color + (255,)), im).convert("RGB")

    W, top_h, view = 1860, 690, 600
    canvas = Image.new("RGB", (W, 60 + top_h + 70 + view + 20), panel)
    d = ImageDraw.Draw(canvas)
    for i, (img, label) in enumerate(((ref_img, "Jouw plaatje (zijaanzicht)"),
                                      (on_bg(out / "r_side.png", navy), "3D-model in Blender (zelfde hoek)"))):
        x = 20 + i * 920
        canvas.paste(img.resize((900, top_h), Image.LANCZOS), (x, 60))
        d.text((x, 14), label, font=font, fill=(255, 255, 255))
    y = 60 + top_h + 70
    for i, (name, label) in enumerate((("r_34.png", "Schuin van voren"), ("r_front.png", "Van voren"),
                                       ("r_back34.png", "Schuin van achteren"))):
        x = 20 + i * 610
        canvas.paste(on_bg(out / name, green).resize((view, view), Image.LANCZOS), (x, y))
        d.text((x, y - 44), label, font=font, fill=(255, 255, 255))
    canvas.save(out / "deer_check.png")


if __name__ == "__main__":
    ref = rm.Reference(sys.argv[1], BOX)
    out = Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if "--debug" in sys.argv:
        p = parts(ref)
        rm.overlay(ref, [p[k] for k in ("body", "ear", "antler", "leg_front_a", "leg_front_b", "leg_back_a",
                                       "leg_back_b")], str(out / "deer_parts.png"))
    else:
        frame, objs = build(ref, out)
        renders(frame, out)
        sheet(ref, out)
