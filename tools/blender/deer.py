"""The Deer, modeled from its side view on the Forest Biome reference sheet.

Run: python3 tools/blender/deer.py tools/blender/reference/forest_side_views.webp <out_dir> [--debug]
(reference/forest_3_4_views.webp, the sheet with the animals at an angle, is only used on the check picture.)
(--debug only writes deer_parts.png, the reference with every part tinted, to check the part outlines.)
Coordinates below are working pixels: the sheet crop (40, 105)-(340, 335) enlarged 4x.
"""

import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refmodel as rm  # noqa: E402

BOX = (40, 105, 340, 335)
GROUND = 866          # hoof bottoms (wp)
FRONT_CUT = 645       # front legs start below this line
BACK_CUT = 705       # hind legs start below this line: above it is the thigh, part of the body


def parts(ref):
    full = ref.silhouette(keep=1)
    antler_zone = ref.polygon([(640, 0), (1100, 0), (1100, 215), (990, 238), (930, 248), (900, 250), (880, 256),
                               (862, 262), (840, 258), (826, 246), (800, 214), (760, 196), (640, 196)])
    # the gaps between the tines are real holes, so this outline is not hole-filled
    antler = rm.tidy(ref.silhouette(fill=False) & antler_zone & ~ref.ellipse((797, 259), (37, 50), angle=-18))
    ear = rm.tidy(ref.ellipse((797, 259), (34, 47), angle=-18) & full & ~antler, radius=3, keep_largest=True)
    # The drawing shows two antlers: one sweeping back (3 tines) and one sweeping forward. Each becomes one
    # side of the head, so the side view is still exactly the drawing and each antler has 3 tines like in
    # the 3/4 picture.
    split = ref.polygon([(640, 0), (868, 0), (868, 150), (862, 262), (640, 262)])
    antler_back = rm.tidy(antler & split, keep_largest=True)
    antler_front = rm.tidy(antler & ~split, keep_largest=True)

    # The darker area between the hind legs in the drawing is the thigh of the far hind leg. Both thighs
    # stay in the body (one wide block at the back, like the 3/4 picture); the legs start below them.
    back_legs = ref.polygon([(140, BACK_CUT), (440, BACK_CUT), (440, 900), (140, 900)])
    front_legs = ref.polygon([(585, FRONT_CUT), (820, FRONT_CUT), (820, 900), (585, 900)])
    near_back_zone = ref.polygon([(140, 600), (266, 600), (266, 900), (140, 900)])
    front_a_zone = ref.polygon([(585, 560), (694, 560), (694, 645), (696, 700), (697, 740), (700, 900), (585, 900)])

    leg_back_a = full & back_legs & near_back_zone
    leg_back_b = full & back_legs & ~near_back_zone
    leg_front_a = full & front_legs & front_a_zone
    leg_front_b = full & front_legs & ~front_a_zone
    # every leg continues up into the body, so it has no seam where it meets the belly
    leg_back_a |= full & ref.polygon([(188, BACK_CUT + 5), (252, BACK_CUT + 5), (250, 630), (195, 630)])
    leg_back_b |= full & ref.polygon([(282, BACK_CUT + 5), (345, BACK_CUT + 5), (340, 630), (290, 630)])
    leg_front_a |= full & ref.polygon([(618, FRONT_CUT + 5), (694, FRONT_CUT + 5), (688, 565), (628, 565)])
    leg_front_b |= full & ref.polygon([(708, FRONT_CUT + 20), (770, FRONT_CUT + 20), (765, 575), (715, 575)])

    body = full & ~antler & ~ear & ~back_legs & ~front_legs
    body |= full & ref.polygon([(762, 318), (800, 280), (838, 256), (852, 266), (842, 322), (782, 336)])  # head under ear
    body &= ~ref.polygon([(640, 0), (1100, 0), (1100, 150), (900, 235), (862, 250), (835, 250), (800, 205), (640, 205)])
    body = rm.tidy(body, radius=3, keep_largest=True)
    # dark paint that is not an outline stroke: hooves and nose
    keep = ref.polygon([(0, 822), (1200, 822), (1200, 920), (0, 920)]) | ref.ellipse((1008, 347), (22, 16))
    return {
        "keep": keep, "full": full, "body": body, "ear": ear, "antler": antler, "antler_back": antler_back,
        "antler_front": antler_front,
        "leg_front_a": leg_front_a, "leg_front_b": leg_front_b, "leg_back_a": leg_back_a, "leg_back_b": leg_back_b,
    }


def build(ref, out):
    import refbuild as rb  # needs bpy
    from zoo_blender import reset

    reset()
    p = parts(ref)
    frame = rb.Frame(ground=GROUND, height_studs=9.0, top=35, center_x=600)
    # Low-poly look: a handful of flat colors instead of the painted lines and shading (the eye stays drawn)
    atlas = rb.Atlas(ref, flat=6)
    atlas.add("ear", p["ear"], keep=p["keep"])
    atlas.add("body", p["body"], keep=p["keep"], soft=True, detail=ref.ellipse((905, 305), (30, 28)))
    for key in ("leg_front_a", "leg_front_b", "leg_back_a", "leg_back_b"):
        atlas.add(key, p[key], keep=p["keep"], soft=True)
    for key in ("antler_back", "antler_front"):
        atlas.add(key, p[key], band=12, dark=115, colors=2)      # pale antlers have a thick dark outline
    mat = rb.material("DeerCoat", atlas.build(str(out / "DeerCoat.png")))
    k = frame.k

    # Blocky low-poly look like the reference: flat sides, a flat back and chest, bevelled edges, few big
    # flat-shaded faces. The outlines are redrawn with straight edges first (rm.simplify).
    # Width = how wide (seen from the front) compared to how thick the outline is there (1 = square),
    # checked against the front and back views of the turnaround.
    width = rm.soft_map(p["full"].shape, 0.82, [((770, 470), 70, 0.85), ((890, 315), 60, 1.05),
                                                ((995, 345), 28, 0.95), ((215, 480), 30, 0.8)])
    inset = rm.soft_map(p["full"].shape, 28, [((1012, 347), 18, 6)])     # keep the black nose tip on the nose
    # The hindquarters (both thighs) are one wide block down to where the hind legs start, as wide as the body,
    # so the legs sit under the thighs instead of sticking out of them.
    thighs = ndimage.gaussian_filter(ref.polygon([(165, 575), (325, 575), (310, 720), (165, 720)]).astype(np.float32),
                                     18) * 98
    body = rb.Piece("Body", rm.simplify(p["body"], 5), frame, atlas, "body", step=2.0, width=width,
                    min_half=thighs, smooth=3, tris=1600, inset=inset, profile="box", bevel=0.25, bevel_max=18,
                    soft=True, flat=True)
    legs = {}
    for key, name, side in (("leg_front_a", "LegFL", -54), ("leg_front_b", "LegFR", 54),
                            ("leg_back_a", "LegBR", 54), ("leg_back_b", "LegBL", -54)):
        leg = rb.Piece(name, rm.simplify(p[key], 4), frame, atlas, key, step=1.5, width=1.05, smooth=3, tris=220,
                       inset=10, profile="box", bevel=0.25, bevel_max=8, soft=True, flat=True)
        legs[name] = leg.transform(rb.pose(rb.Vector((0, 0, 0)), move=(side * k, 0, 0)))

    ear = rb.Piece("Ear", rm.simplify(p["ear"], 3), frame, atlas, "ear", step=1.0, width=0.25, min_half=2.5,
                   smooth=8, tris=80, inset=4, flat=True)
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

    antlers = []
    for key, sign in (("antler_back", 1), ("antler_front", -1)):
        a = rb.Piece(key, rm.simplify(p[key], 2.5), frame, atlas, key, step=1.0, width=1.0, smooth=8, tris=450,
                     inset=6, flat=True)
        antlers.append(a.deform(spread(sign)))

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
    rb.render(cam, str(out / "r_34.png"), (0, 0.4, 4.6), (0.75, 1.0, 0.25), distance=17, lens=55)
    rb.render(cam, str(out / "r_back34.png"), (0, -0.3, 4.2), (0.9, -0.85, 0.4), distance=19, lens=55)


def bpy_scene_size(w, h):
    import bpy
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = w, h


def sheet(ref, out, ref34=None):
    """Reference next to the model, for checking. ref34: the 3/4 reference sheet (optional)."""
    from PIL import Image, ImageDraw, ImageFont
    navy, green, panel = (3, 28, 40), (56, 92, 62), (14, 22, 30)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    ref_img = Image.fromarray(ref.image.clip(0, 255).astype("uint8"))

    def on_bg(path, color):
        im = Image.open(path).convert("RGBA")
        return Image.alpha_composite(Image.new("RGBA", im.size, color + (255,)), im).convert("RGB")

    W, top_h, view = 1860, 690, 450
    canvas = Image.new("RGB", (W, 60 + top_h + 70 + view + 20), panel)
    d = ImageDraw.Draw(canvas)
    for i, (img, label) in enumerate(((ref_img, "Jouw plaatje (zijaanzicht)"),
                                      (on_bg(out / "r_side.png", navy), "3D-model (zelfde hoek)"))):
        x = 20 + i * 920
        canvas.paste(img.resize((900, top_h), Image.LANCZOS), (x, 60))
        d.text((x, 14), label, font=font, fill=(255, 255, 255))
    views = [(on_bg(out / n, green), label) for n, label in (("r_34.png", "3D: schuin voor"),
                                                             ("r_front.png", "3D: van voren"),
                                                             ("r_back34.png", "3D: schuin achter"))]
    if ref34:
        views.insert(0, (Image.open(ref34).convert("RGB").crop((60, 150, 265, 355)), "Jouw plaatje (schuin)"))
    y = 60 + top_h + 70
    for i, (img, label) in enumerate(views):
        x = 20 + i * (view + 15)
        canvas.paste(img.resize((view, view), Image.LANCZOS), (x, y))
        d.text((x, y - 42), label, font=font, fill=(255, 255, 255))
    canvas.save(out / "deer_check.png")


if __name__ == "__main__":
    ref = rm.Reference(sys.argv[1], BOX)
    out = Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if "--debug" in sys.argv:
        p = parts(ref)
        rm.overlay(ref, [p[k] for k in ("body", "ear", "antler_back", "antler_front", "leg_front_a", "leg_front_b",
                                       "leg_back_a", "leg_back_b")], str(out / "deer_parts.png"))
    else:
        frame, objs = build(ref, out)
        renders(frame, out)
        sheet(ref, out, Path(__file__).resolve().parent / "reference" / "forest_3_4_views.webp")
