"""Faceted low-poly surfaces out of WedgeParts.

Every triangle is two wedges (the usual Roblox trick), so a mountain can be a real faceted shape with slopes,
ridges and a sharp peak instead of a stack of blocks. A surface is a list of closed rings of points around the
centre (outside to inside); neighbouring rings are stitched together with triangles, even when they have a
different number of points, so a ring high on the mountain can use fewer, bigger facets than one at the foot.
"""

import math

from lib import add, cross, scale, sub, unit


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def tri(asset, name, a, b, c, color, thick=1.2, **kw):
    """Triangle a-b-c as two wedges. The wedges are `thick` studs thick and sit under the face (on the side away
    from the sky), so the top of the surface is exactly the triangle."""
    ab, ac, bc = sub(b, a), sub(c, a), sub(c, b)
    abd, acd, bcd = dot(ab, ab), dot(ac, ac), dot(bc, bc)
    if abd > acd and abd > bcd:
        c, a = a, c
    elif acd > bcd and acd > abd:
        a, b = b, a
    ab, ac, bc = sub(b, a), sub(c, a), sub(c, b)
    n = cross(ac, ab)
    if dot(n, n) < 1e-9:
        return 0
    right = unit(n)
    up = unit(cross(bc, right))
    back = unit(bc)
    height = abs(dot(ab, up))
    if height < 0.05:
        return 0
    down = right if right[1] < 0 else scale(right, -1)       # thickness goes under the face
    off = scale(down, thick / 2)
    for pa, length, axes in (((a, b), abs(dot(ab, back)), (right, up, back)),
                             ((a, c), abs(dot(ac, back)), (scale(right, -1), up, scale(back, -1)))):
        if length < 0.05:
            continue
        mid = add(scale(add(*pa), 0.5), off)
        R = tuple((axes[0][i], axes[1][i], axes[2][i]) for i in range(3))
        asset.wedge(name, (thick, height, length), mid, color, R=R, **kw)
    return 2


def normal_up(a, b, c):
    n = cross(sub(b, a), sub(c, a))
    if dot(n, n) < 1e-9:
        return None
    n = unit(n)
    return n if n[1] >= 0 else scale(n, -1)


def stitch(outer, inner):
    """Triangles between two closed rings of points [(deg, (x, y, z)), ...] sorted by angle from 0."""
    out = []
    i = j = 0
    na, nb = len(outer), len(inner)

    def ang(row, k, n):
        return row[k % n][0] + 360.0 * (k // n)

    while i < na or j < nb:
        a_next = ang(outer, i + 1, na) if i < na else math.inf
        b_next = ang(inner, j + 1, nb) if j < nb else math.inf
        if a_next <= b_next:
            out.append((outer[i % na][1], inner[j % nb][1], outer[(i + 1) % na][1]))
            i += 1
        else:
            out.append((outer[i % na][1], inner[j % nb][1], inner[(j + 1) % nb][1]))
            j += 1
    return out


def surface(rings):
    """All triangles of a surface made of rings (outside to inside)."""
    tris = []
    for k in range(len(rings) - 1):
        tris += stitch(rings[k], rings[k + 1])
    return tris
