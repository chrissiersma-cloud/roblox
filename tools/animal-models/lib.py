"""Small toolkit for building rigged, part-based Roblox animal models.

Coordinates are in studs. Every animal faces -Z (Roblox's LookVector), +X is
its right side and y = 0 is the ground. Rotations use CFrame.Angles order
(degrees), so mirroring a part to the other side means negating ry and rz.
"""

import math
from contextlib import contextmanager

# ---------------------------------------------------------------- math ----

IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def matmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def transpose(m):
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


def apply(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def angles(x=0.0, y=0.0, z=0.0):
    """Same as CFrame.Angles(math.rad(x), math.rad(y), math.rad(z))."""
    x, y, z = (math.radians(a) for a in (x, y, z))
    rx = ((1, 0, 0), (0, math.cos(x), -math.sin(x)), (0, math.sin(x), math.cos(x)))
    ry = ((math.cos(y), 0, math.sin(y)), (0, 1, 0), (-math.sin(y), 0, math.cos(y)))
    rz = ((math.cos(z), -math.sin(z), 0), (math.sin(z), math.cos(z), 0), (0, 0, 1))
    return matmul(matmul(rx, ry), rz)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def scale(a, k):
    return tuple(x * k for x in a)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    length = math.sqrt(sum(x * x for x in a))
    return tuple(x / length for x in a)


def facing(normal, up=(0, 1, 0)):
    """Rotation whose local Z axis points along `normal` (for flat decals)."""
    back = unit(normal)
    if abs(sum(b * u for b, u in zip(back, up))) > 0.99:
        up = (0, 0, -1)
    right = unit(cross(up, back))
    real_up = cross(back, right)
    return tuple((right[i], real_up[i], back[i]) for i in range(3))


def aim(direction, roll_up=(0, 1, 0)):
    """Rotation whose local X axis points along `direction` (for cylinders)."""
    x = unit(direction)
    if abs(sum(a * b for a, b in zip(x, roll_up))) > 0.99:
        roll_up = (0, 0, -1)
    z = unit(cross(x, roll_up))
    y = cross(z, x)
    return tuple((x[i], y[i], z[i]) for i in range(3))


def surface(center, radii, direction):
    """Point and outward normal on an ellipsoid surface in `direction`."""
    d = unit(direction)
    t = 1 / math.sqrt(sum((d[i] / (radii[i] / 2)) ** 2 for i in range(3)))
    point = add(center, scale(d, t))
    normal = unit(tuple((point[i] - center[i]) / (radii[i] / 2) ** 2 for i in range(3)))
    return point, normal


def direction(yaw, pitch, side=1):
    """Unit vector: yaw degrees from the front (-Z) towards `side`, pitch up."""
    y, p = math.radians(yaw), math.radians(pitch)
    return (math.sin(y) * math.cos(p) * side, math.sin(p), -math.cos(y) * math.cos(p))


def hex_color(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def cframe(rotation, position):
    return [*position, *rotation[0], *rotation[1], *rotation[2]]


def inverse(rotation, position):
    rt = transpose(rotation)
    return rt, scale(apply(rt, position), -1)


def compose(a, b):
    (ra, pa), (rb, pb) = a, b
    return matmul(ra, rb), add(apply(ra, pb), pa)


SIDES = ((1, "R"), (-1, "L"))

# ------------------------------------------------------------- animals ----

WHITE = hex_color("#ffffff")
EYE = hex_color("#1b1420")
BLUSH = hex_color("#ff9ab3")

SPARKLE_TEXTURE = "rbxasset://textures/particles/sparkles_main.dds"
FIRE_TEXTURE = "rbxasset://textures/particles/fire_main.dds"
SMOKE_TEXTURE = "rbxasset://textures/particles/smoke_main.dds"


class Animal:
    def __init__(self, animal_id, display_name, rarity):
        self.id = animal_id
        self.display_name = display_name
        self.rarity = rarity
        self.parts = []
        self.bones = {"Body": {"parent": None, "pivot": None}}
        self.current_bone = "Body"
        self.ride_height = None
        self.ride_z = 0.0
        self.overhead = None
        self.root_effects = []

    # -- rig ---------------------------------------------------------------

    @contextmanager
    def bone(self, name, parent, pivot):
        """Parts added inside this block move with a Motor6D joint at `pivot`."""
        assert name not in self.bones, name
        self.bones[name] = {"parent": parent, "pivot": pivot}
        previous, self.current_bone = self.current_bone, name
        try:
            yield
        finally:
            self.current_bone = previous

    # -- parts -------------------------------------------------------------

    def _part(self, shape, name, size, pos, color, rot=None, R=None, material=None,
              role="Primary", transparency=0.0, reflectance=0.0, shadow=None, effects=None, studs=None):
        if R is None:
            R = angles(*rot) if rot else IDENTITY
        if material is None:
            material = "Plastic" if shape in ("block", "wedge") else "SmoothPlastic"
        if studs is None:
            studs = material == "Plastic" and min(size) >= 0.3
        if material == "Neon" and role == "Primary":
            role = "Glow"
        if shadow is None:
            shadow = size[0] * size[1] * size[2] > 0.6 and transparency < 0.5
        assert all(p["name"] != name for p in self.parts), f"{self.id}: duplicate part {name}"
        part = {
            "name": name, "shape": shape, "size": tuple(size), "R": R, "p": tuple(pos),
            "color": color, "material": material, "role": role, "transparency": transparency,
            "reflectance": reflectance, "shadow": shadow, "bone": self.current_bone, "studs": studs,
            "effects": effects or [],
        }
        self.parts.append(part)
        return part

    def ell(self, name, size, pos, color, **kw):
        """Ellipsoid (Part with a Sphere SpecialMesh), the main building block."""
        return self._part("ellipsoid", name, size, pos, color, **kw)

    def ball(self, name, diameter, pos, color, **kw):
        return self._part("ball", name, (diameter,) * 3, pos, color, **kw)

    def box(self, name, size, pos, color, **kw):
        return self._part("block", name, size, pos, color, **kw)

    def wedge(self, name, size, pos, color, **kw):
        return self._part("wedge", name, size, pos, color, **kw)

    def cyl(self, name, length, diameter, pos, color, **kw):
        """Cylinder whose axis is local X (use R=aim(dir) to point it)."""
        return self._part("cylinder", name, (length, diameter, diameter), pos, color, **kw)

    def rod(self, name, start, end, diameter, color, **kw):
        """Cylinder between two points."""
        length = math.dist(start, end)
        mid = scale(add(start, end), 0.5)
        return self.cyl(name, length, diameter, mid, color, R=aim(sub(end, start)), **kw)

    def tri(self, name, base, width, height, thick, color, R=IDENTITY, **kw):
        """Upright triangle (two wedges) standing on `base`, facing -Z before R."""
        parts = []
        for sgn, suffix in ((-1, "A"), (1, "B")):
            pos = add(base, apply(R, (sgn * width / 4, height / 2, 0)))
            rot = matmul(R, angles(0, 90 if sgn < 0 else -90, 0))
            parts.append(self.wedge(f"{name}{suffix}", (thick, height, width / 2), pos, color, R=rot, **kw))
        return parts

    def shard(self, name, base, width, height, color, R=IDENTITY, tip=0.45, cross=False, **kw):
        """Crystal: a square prism with a pointed top, turned 45 degrees."""
        R = matmul(R, angles(0, 45, 0))
        body_h = height * (1 - tip)
        self.box(name, (width, body_h, width), add(base, apply(R, (0, body_h / 2, 0))), color, R=R, **kw)
        top = add(base, apply(R, (0, body_h, 0)))
        for i, turn in enumerate((0, 90) if cross else (0,)):
            self.tri(f"{name}Tip{i}", top, width, height * tip, width * 0.999, color,
                     R=matmul(R, angles(0, turn, 0)), **kw)

    def bevel(self, name, size, pos, color, b=0.6, R=IDENTITY, bottom=0.0, **kw):
        """Block with chamfered long edges along local Z (b = top bevel, bottom = lower bevel)."""
        w, h, d = size
        core_h = h - b - bottom
        core_y = (bottom - b) / 2
        at = lambda x, y, z: add(pos, apply(R, (x, y, z)))
        main = self.box(name, (w, core_h, d), at(0, core_y, 0), color, R=R, **kw)
        if b > 0:
            self.box(f"{name}Top", (w - 2 * b, b, d), at(0, h / 2 - b / 2, 0), color, R=R, **kw)
            for sgn, S in ((-1, "L"), (1, "R")):
                self.wedge(f"{name}Bevel{S}", (d, b, b), at(sgn * (w / 2 - b / 2), h / 2 - b / 2, 0), color,
                           R=matmul(R, angles(0, -90 * sgn, 0)), **kw)
        if bottom > 0:
            self.box(f"{name}Bottom", (w - 2 * bottom, bottom, d), at(0, -h / 2 + bottom / 2, 0), color, R=R, **kw)
            for sgn, S in ((-1, "L"), (1, "R")):
                self.wedge(f"{name}BevelLow{S}", (d, bottom, bottom), at(sgn * (w / 2 - bottom / 2), -h / 2 + bottom / 2, 0),
                           color, R=matmul(matmul(R, angles(0, 0, 180)), angles(0, 90 * sgn, 0)), **kw)
        return main

    def tooth(self, name, top, width, height, color=WHITE, R=IDENTITY, up=False, **kw):
        """Sawtooth tooth (single wedge) hanging from `top`; its triangle faces +-X before R."""
        flip = angles(0, 0, 0) if up else angles(0, 0, 180)
        pos = add(top, apply(R, (0, height / 2 if up else -height / 2, 0)))
        kw.setdefault("material", "SmoothPlastic")
        kw.setdefault("role", "Accent")
        kw.setdefault("shadow", False)
        return self.wedge(name, (0.2, height, width), pos, color, R=matmul(R, flip), **kw)

    def block_eye(self, name, pos, R=IDENTITY, w=1.0, h=1.2, pupil=EYE, white=WHITE, look=(0, 0), glow=False):
        """Flat blocky eye facing local -Z: white, pupil and a shine."""
        at = lambda x, y, z: add(pos, apply(R, (x, y, z)))
        detail = dict(material="SmoothPlastic", role="Eye", shadow=False)
        self.box(f"{name}", (w, h, 0.12), pos, white, R=R, **detail)
        px, py = look[0] * w * 0.18, -h * 0.06 + look[1] * h * 0.15
        pupil_mat = dict(detail, material="Neon") if glow else detail
        self.box(f"{name}Pupil", (w * 0.62, h * 0.74, 0.14), at(px, py, -0.02), pupil, R=R, **pupil_mat)
        self.box(f"{name}Shine", (w * 0.26, w * 0.26, 0.16), at(px - w * 0.12, py + h * 0.17, -0.04), WHITE, R=R,
                 **detail)

    def on_surface(self, name, center, radii, yaw, pitch, size, color, side=1, sink=0.35, twist=0,
                   shape="ellipsoid", **kw):
        """A flat piece stuck onto the surface of an ellipsoid (twist spins it in place)."""
        point, normal = surface(center, radii, direction(yaw, pitch, side))
        pos = sub(point, scale(normal, size[2] * sink))
        R = matmul(facing(normal), angles(0, 0, twist))
        return self._part(shape, name, size, pos, color, R=R, **kw)

    def brows(self, center, radii, yaw=30, pitch=8, color=EYE, width=0.14, lift=22, spread=13, angry=8):
        """Little angled eyebrows above the eyes (for aggressive animals)."""
        for side, S in SIDES:
            inner, n1 = surface(center, radii, direction(yaw - spread, pitch + lift - angry, side))
            outer, n2 = surface(center, radii, direction(yaw + spread, pitch + lift + angry, side))
            self.rod(f"Brow{S}", add(inner, scale(n1, 0.02)), add(outer, scale(n2, 0.02)), width, color,
                     role="Accent", shadow=False)

    # -- common features ---------------------------------------------------

    def eyes(self, center, radii, yaw=30, pitch=8, size=(0.55, 0.7, 0.28), color=EYE,
             shine=True, material="SmoothPlastic", role="Eye", pupil=None, spread=0.0):
        for side, S in SIDES:
            c = (center[0] + spread * side, center[1], center[2])
            point, normal = surface(c, radii, direction(yaw, pitch, side))
            R = facing(normal)
            right, up = (R[0][0], R[1][0], R[2][0]), (R[0][1], R[1][1], R[2][1])
            pos = sub(point, scale(normal, size[2] * 0.3))
            self.ell(f"Eye{S}", size, pos, color, R=R, material=material, role=role, shadow=False)
            front = add(pos, scale(normal, size[2] * 0.42))
            if pupil:
                self.ell(f"Pupil{S}", (size[0] * 0.28, size[1] * 0.8, size[2] * 0.3), front, pupil[0],
                         R=R, material=pupil[1], role="Eye", shadow=False)
            if shine:
                big = add(add(front, scale(up, size[1] * 0.2)), scale(right, size[0] * 0.18))
                self.ball(f"EyeShine{S}", size[0] * 0.36, big, WHITE, role="Eye", shadow=False)
                small = add(add(front, scale(up, -size[1] * 0.2)), scale(right, -size[0] * 0.2))
                self.ball(f"EyeShineSmall{S}", size[0] * 0.16, small, WHITE, role="Eye", shadow=False)

    def cheeks(self, center, radii, yaw=52, pitch=-12, size=(0.42, 0.26, 0.1), color=BLUSH):
        for side, S in SIDES:
            self.on_surface(f"Cheek{S}", center, radii, yaw, pitch, size, color, side=side,
                            role="Accent", shadow=False, transparency=0.15)

    # -- effects -----------------------------------------------------------

    @staticmethod
    def sparkles(color, rate=4, size=0.35, lifetime=(0.8, 1.4), speed=(0.5, 1.5), spread=180,
                 texture=SPARKLE_TEXTURE, name="Sparkles", light=1, accel=(0, 0, 0), color2=None,
                 transparency=((0, 0.2), (1, 1)), drag=0, rot=(0, 360), emit="Top", sizes=None):
        color2 = color2 or color
        return {
            "class": "ParticleEmitter", "name": name,
            "props": {
                "EmissionDirection": emit,
                "Texture": texture, "Rate": rate, "Lifetime": list(lifetime), "Speed": list(speed),
                "SpreadAngle": [spread, spread], "LightEmission": light, "LightInfluence": 0,
                "Size": [list(k) for k in sizes] if sizes else [[0, size], [1, 0]],
                "Transparency": [list(t) for t in transparency],
                "Color": [[0, *color], [1, *color2]], "Acceleration": list(accel),
                "Drag": drag, "Rotation": list(rot), "RotSpeed": [-90, 90],
            },
        }

    @staticmethod
    def light(color, brightness=1.5, range_=10, name="Glow"):
        return {"class": "PointLight", "name": name,
                "props": {"Color": list(color), "Brightness": brightness, "Range": range_, "Shadows": False}}

    # -- output ------------------------------------------------------------

    def build(self):
        """Returns the instance tree for rbxm-writer."""
        pid = lambda name: f"{self.id}.{name}"

        # One main part per bone; the rest of that bone's parts weld to it.
        main = {}
        for part in self.parts:
            main.setdefault(part["bone"], part)
        for bone, info in self.bones.items():
            assert bone in main, f"{self.id}: bone {bone} has no parts"
            if info["parent"]:
                assert info["parent"] in self.bones, f"{self.id}: unknown parent {info['parent']}"

        # Hitbox = bounding box of everything visible.
        lo, hi = [1e9] * 3, [-1e9] * 3
        for part in self.parts:
            half = scale(part["size"], 0.5)
            for corner in ((sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)):
                point = add(part["p"], apply(part["R"], tuple(c * h for c, h in zip(corner, half))))
                lo = [min(a, b) for a, b in zip(lo, point)]
                hi = [max(a, b) for a, b in zip(hi, point)]
        lo[1] = 0.0
        hit_size = tuple(round(h - l, 3) for l, h in zip(lo, hi))
        hit_pos = tuple((l + h) / 2 for l, h in zip(lo, hi))
        root_cf = (IDENTITY, hit_pos)

        children = []
        body_main = main["Body"]
        root_attachments = [
            {"class": "Attachment", "name": "RideAttachment",
             "props": {"CFrame": cframe(IDENTITY, sub((0, self.ride_height or hi[1], self.ride_z), hit_pos))}},
            {"class": "Attachment", "name": "OverheadAttachment",
             "props": {"CFrame": cframe(IDENTITY, sub((0, (self.overhead or hi[1]) + 1.2, lo[2] * 0.5 + hi[2] * 0.5), hit_pos))}},
        ]
        children.append({
            "class": "Part", "name": "RootPart", "id": pid("RootPart"),
            "attrs": {"Role": "Hitbox"},
            "props": {
                "Size": list(hit_size), "CFrame": cframe(*root_cf), "Transparency": 1,
                "Anchored": True, "CanCollide": False, "CanTouch": True, "CanQuery": True,
                "CastShadow": False, "Massless": False,
                "PivotOffset": cframe(IDENTITY, (0, -hit_pos[1], 0)),
                "TopSurface": "Smooth", "BottomSurface": "Smooth",
            },
            "children": root_attachments + self.root_effects,
        })

        for part in self.parts:
            cf = (part["R"], part["p"])
            props = {
                "Size": [round(v, 4) for v in part["size"]], "CFrame": cframe(*cf),
                "Color": list(part["color"]), "Material": part["material"],
                "Anchored": False, "CanCollide": False, "CanTouch": False, "CanQuery": False,
                "Massless": True, "CastShadow": part["shadow"],
            }
            surface_type = "Studs" if part["studs"] else "Smooth"
            for face in ("Top", "Bottom", "Front", "Back", "Left", "Right"):
                props[f"{face}Surface"] = surface_type
            if part["transparency"]:
                props["Transparency"] = part["transparency"]
            if part["reflectance"]:
                props["Reflectance"] = part["reflectance"]
            kids = []
            if part["shape"] == "ellipsoid":
                kids.append({"class": "SpecialMesh", "name": "Mesh", "props": {"MeshType": "Sphere"}})
            elif part["shape"] == "ball":
                props["Shape"] = "Ball"
            elif part["shape"] == "cylinder":
                props["Shape"] = "Cylinder"

            bone = part["bone"]
            if part is main[bone]:
                info = self.bones[bone]
                if info["parent"] is None:
                    parent_cf, parent_id, pivot = root_cf, pid("RootPart"), part["p"]
                else:
                    parent_part = main[info["parent"]]
                    parent_cf, parent_id, pivot = (parent_part["R"], parent_part["p"]), pid(parent_part["name"]), info["pivot"]
                joint = (IDENTITY, pivot)
                kids.append({
                    "class": "Motor6D", "name": "Root" if info["parent"] is None else bone,
                    "props": {
                        "Part0": {"ref": parent_id}, "Part1": {"ref": pid(part["name"])},
                        "C0": cframe(*compose(inverse(*parent_cf), joint)),
                        "C1": cframe(*compose(inverse(*cf), joint)),
                    },
                })
            else:
                owner = main[bone]
                kids.append({
                    "class": "Weld", "name": "Weld",
                    "props": {
                        "Part0": {"ref": pid(owner["name"])}, "Part1": {"ref": pid(part["name"])},
                        "C0": cframe(*compose(inverse(owner["R"], owner["p"]), cf)),
                    },
                })
            kids.extend(part["effects"])
            children.append({
                "class": "WedgePart" if part["shape"] == "wedge" else "Part",
                "name": part["name"], "id": pid(part["name"]),
                "attrs": {"Role": part["role"]},
                "props": props, "children": kids,
            })

        return {
            "class": "Model", "name": self.id,
            "attrs": {"AnimalId": self.id, "DisplayName": self.display_name, "Rarity": self.rarity},
            "tags": ["HuntAnimalModel"],
            "props": {"PrimaryPart": {"ref": pid("RootPart")}},
            "children": children,
        }
