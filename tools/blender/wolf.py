"""Prototype: the Wolf, built in Blender. Run: python3 wolf.py <out_dir>"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zoo_blender as zb  # noqa: E402

COAT = [(0.0, "#f3eee6"), (0.22, "#dedfe1"), (0.5, "#a3a8b1"), (0.75, "#6c717b"), (1.0, "#3e424a")]


def coat(p, n):
    x, y, z = p
    if y < -2.25 and z > 1.0:                                   # tail
        t = 0.35 + 0.45 * zb.smooth(-0.3, 0.8, n.z)
        return zb.ramp(COAT, 0.95 if z < 1.85 else t)
    if y > 2.75:                                                # head
        t = 0.3 + 0.55 * zb.smooth(-0.2, 0.8, n.z)
        if y > 3.7 or n.z < -0.25 or (abs(n.x) > 0.55 and z < 4.45):
            t = 0.08
        return zb.ramp(COAT, t)
    if z < 2.45:                                                # legs
        outer = n.x * (1 if x > 0 else -1) > 0.3
        return zb.ramp(COAT, 0.12 + 0.18 * zb.smooth(0.4, 2.4, z) + (0.12 if outer else 0))
    t = 0.25 + 0.55 * zb.smooth(-0.3, 0.9, n.z) + 0.2 * zb.smooth(3.0, 4.2, z)
    if n.z < -0.35:
        t = 0.05
    if y > 1.5 and n.y > 0.3 and z < 3.9:
        t = 0.08
    return zb.ramp(COAT, t)


def build():
    zb.reset()
    nodes = {
        "chest": ((0, 1.4, 3.05), (1.0, 1.3)), "withers": ((0, 2.05, 3.55), (0.85, 1.0)),
        "belly": ((0, 0.3, 3.25), (0.9, 1.02)), "loin": ((0, -0.8, 3.38), (0.78, 0.82)),
        "pelvis": ((0, -1.75, 3.35), (0.82, 0.9)), "neck": ((0, 2.55, 4.05), (0.7, 0.76)),
        "head": ((0, 3.0, 4.45), (0.64, 0.6)), "skull": ((0, 3.42, 4.5), (0.6, 0.52)),
        "muzzle": ((0, 3.98, 4.3), (0.34, 0.3)), "nose": ((0, 4.42, 4.3), (0.2, 0.17)),
        "t0": ((0, -2.4, 3.6), (0.26, 0.26)), "t1": ((0, -3.05, 3.2), (0.38, 0.38)),
        "t2": ((0, -3.45, 2.45), (0.36, 0.36)), "t3": ((0, -3.55, 1.75), (0.2, 0.2)), "t4": ((0, -3.5, 1.35), (0.06, 0.06)),
    }
    edges = [("chest", "withers"), ("chest", "belly"), ("belly", "loin"), ("loin", "pelvis"), ("withers", "neck"),
             ("neck", "head"), ("head", "skull"), ("skull", "muzzle"), ("muzzle", "nose"), ("pelvis", "t0"),
             ("t0", "t1"), ("t1", "t2"), ("t2", "t3"), ("t3", "t4")]
    for s, S in ((1, "R"), (-1, "L")):
        nodes.update({
            f"sh{S}": ((0.55 * s, 1.75, 2.95), (0.4, 0.45)), f"el{S}": ((0.52 * s, 1.7, 1.9), (0.26, 0.28)),
            f"wr{S}": ((0.5 * s, 1.75, 0.7), (0.17, 0.17)), f"paw{S}": ((0.5 * s, 1.95, 0.1), (0.23, 0.14)),
            f"hip{S}": ((0.6 * s, -1.75, 3.1), (0.5, 0.6)), f"kn{S}": ((0.58 * s, -1.3, 2.1), (0.32, 0.34)),
            f"hk{S}": ((0.55 * s, -2.0, 1.15), (0.17, 0.18)), f"ft{S}": ((0.53 * s, -1.85, 0.45), (0.15, 0.15)),
            f"bpaw{S}": ((0.53 * s, -1.6, 0.1), (0.22, 0.14)),
        })
        edges += [("chest", f"sh{S}"), (f"sh{S}", f"el{S}"), (f"el{S}", f"wr{S}"), (f"wr{S}", f"paw{S}"),
                  ("pelvis", f"hip{S}"), (f"hip{S}", f"kn{S}"), (f"kn{S}", f"hk{S}"), (f"hk{S}", f"ft{S}"),
                  (f"ft{S}", f"bpaw{S}")]
    body = zb.skin_body("WolfBody", nodes, edges, subdiv=2)
    zb.paint(body, coat)
    parts = [body]

    nose, _, _ = zb.stick(body, "Nose", (0, 4.45, 4.35), (0, 1, 0.35), (0.17, 0.12, 0.11))
    parts.append(zb.paint(nose, zb.solid("#161416"), noise=0))
    for s in (1, -1):
        eye, loc, normal = zb.stick(body, f"Eye{s}", (0.3 * s, 3.62, 4.62), (0.55 * s, 0.75, 0.3), (0.1, 0.1, 0.1), sink=0.5)
        zb.paint(eye, lambda p, n, c=eye.location: zb.hex_rgb("#d99a22"), noise=0)
        pupil = zb.blob(f"Pupil{s}", loc + normal * 0.03, (0.05, 0.05, 0.05))
        glint = zb.blob(f"Glint{s}", loc + normal * 0.06 + zb.Vector((0, 0, 0.035)), (0.022, 0.022, 0.022))
        zb.paint(pupil, zb.solid("#0e0c0b"), noise=0)
        zb.paint(glint, zb.solid("#ffffff"), noise=0)
        base, _ = zb.surface(body, (0.36 * s, 3.25, 4.6), (0.2 * s, -0.1, 1))
        ear = zb.horn(f"Ear{s}", [base - zb.Vector((0, 0, 0.1)), base + zb.Vector((0.06 * s, -0.02, 0.4)),
                                  base + zb.Vector((0.14 * s, -0.06, 0.82))], [(0.3, 0.11), (0.2, 0.08), (0.01, 0.01)])
        zb.paint(ear, lambda p, n: zb.ramp(COAT, 0.9 if n.y < 0.1 else 0.4))
        inner = zb.horn(f"InnerEar{s}", [base + zb.Vector((0, 0.07, -0.02)), base + zb.Vector((0.06 * s, 0.05, 0.36)),
                                         base + zb.Vector((0.12 * s, 0.02, 0.7))], [(0.19, 0.04), (0.12, 0.03), (0.01, 0.01)])
        zb.paint(inner, zb.solid("#e8d2cb"), noise=0)
        parts += [eye, pupil, glint, ear, inner]
        for i, (target, d, sweep) in enumerate([((0.45 * s, 3.1, 4.1), (s, 0.2, -0.3), (0.3 * s, -1, -0.2)),
                                                ((0.5 * s, 2.7, 3.85), (s, 0.1, -0.2), (0.2 * s, -1, -0.4)),
                                                ((0.55 * s, 2.3, 3.4), (s, 0.3, -0.4), (0.2 * s, -0.8, -0.6))]):
            t = zb.tuft(body, f"Ruff{i}{s}", target, d, sweep, 0.55, 0.28)
            zb.paint(t, lambda p, n: zb.ramp(COAT, 0.2))
            parts.append(t)
        for x0, y0 in ((0.5, 2.1), (0.53, -1.45)):
            for dx in (-0.1, 0.0, 0.1):
                claw = zb.horn("Claw", [(x0 * s + dx, y0 + 0.02, 0.1), (x0 * s + dx * 1.2, y0 + 0.22, 0.02)],
                               [0.04, 0.006], sides=6)
                zb.paint(claw, zb.solid("#2a2628"), noise=0)
                parts.append(claw)
    for i, (target, d) in enumerate([((0, 2.1, 2.6), (0, 0.4, -1)), ((0.3, 1.9, 2.55), (0.3, 0.4, -1)),
                                     ((-0.3, 1.9, 2.55), (-0.3, 0.4, -1))]):
        t = zb.tuft(body, f"ChestTuft{i}", target, d, (0, -0.2, -1), 0.45, 0.3)
        zb.paint(t, lambda p, n: zb.ramp(COAT, 0.05))
        parts.append(t)
    return zb.join(parts, "Wolf")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    wolf = build()
    zb.bake_texture(wolf, size=1024)
    zb.export_glb(wolf, str(out / "Wolf.glb"))
    print("triangles", sum(len(p.vertices) - 2 for p in wolf.data.polygons))
    zb.preview(str(out / "wolf_preview.png"), target=(0, 0.4, 2.6), distance=15, angle=-50, height=0.22)
