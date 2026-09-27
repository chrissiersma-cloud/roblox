"""Reference-driven modeling: turn a side-view drawing of an animal into 3D shapes.

The idea, step by step:
  1. Cut the animal out of the reference sheet (everything that is not the dark background).
  2. Split that outline into parts (body, legs, ears, antlers, ...) with hand-placed polygons.
  3. "Inflate" every flat part into 3D: each point inside the outline gets a thickness. We use a
     union of balls: every point on the middle line of the shape (the medial axis) carries a ball
     that just fits inside the outline. Seen from the side the balls fill the outline exactly, so the
     3D shape has exactly the drawn silhouette, and seen from the front it is nicely round.
  4. Marching cubes turns that volume into a triangle mesh.
  5. The drawing itself becomes the texture: every vertex looks up the color at its (x, y) spot in the
     side view (a planar projection), so patterns, eyes and shading match the reference.

Coordinates: "working pixels" (wp) are pixels of the cropped reference after upscaling by `scale`.
A mesh from `inflate` has vertices (side, img_x, img_y) in wp, side = 0 is the middle of the animal.
"""

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import measure, morphology


class Reference:
    def __init__(self, path, box, scale=4, background=(3, 28, 40)):
        """box = (left, top, right, bottom) in pixels of the original sheet."""
        im = Image.open(path).convert("RGB")
        w, h = box[2] - box[0], box[3] - box[1]
        self.scale = scale
        self.image = np.asarray(im.crop(box).resize((w * scale, h * scale), Image.LANCZOS)).astype(np.float32)
        self.h, self.w = self.image.shape[:2]
        dist = np.linalg.norm(self.image - np.array(background, np.float32), axis=2)
        self.alpha = np.clip((dist - 20) / 28, 0, 1)            # soft "how much animal is here"

    def silhouette(self, threshold=0.5, sigma=1.5, keep=None, fill=True):
        """Smooth boolean outline of the animal; keep = number of biggest pieces to keep."""
        m = ndimage.gaussian_filter(self.alpha, sigma) > threshold
        if fill:
            m = ndimage.binary_fill_holes(m)
        if keep:
            lab, n = ndimage.label(m)
            sizes = ndimage.sum(m, lab, range(1, n + 1))
            order = np.argsort(sizes)[::-1][:keep] + 1
            m = np.isin(lab, order)
        return m

    def polygon(self, points):
        img = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(img).polygon([tuple(p) for p in points], fill=1)
        return np.asarray(img, bool)

    def ellipse(self, center, radii, angle=0.0):
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        a = np.radians(angle)
        dx, dy = xx - center[0], yy - center[1]
        u = dx * np.cos(a) + dy * np.sin(a)
        v = -dx * np.sin(a) + dy * np.cos(a)
        return (u / radii[0]) ** 2 + (v / radii[1]) ** 2 <= 1

    def clean(self, mask, erode=4, band=9, dark=50, keep=None):
        """The drawing inside `mask`, with the outline stroke removed and everything outside filled with
        the nearest color inside. Used as texture, so edges of the mesh don't pick up background.
        Dark pixels within `band` wp of the edge count as outline (except inside `keep`, e.g. hooves)."""
        inner = ndimage.binary_erosion(mask, iterations=erode)
        edge_dist = ndimage.distance_transform_edt(mask)
        lum = self.image @ np.array([0.3, 0.59, 0.11], np.float32)
        outline = (edge_dist < band) & (lum < dark)
        if keep is not None:
            outline &= ~keep
        inner &= ~outline
        if not inner.any():
            inner = mask
        _, (iy, ix) = ndimage.distance_transform_edt(~inner, return_indices=True)
        out = self.image[iy, ix]
        # soften only the filled area a little so stretched regions don't show streaks
        blurred = ndimage.gaussian_filter(out, sigma=(3, 3, 0))
        return np.where(inner[..., None], out, blurred)


def tidy(mask, radius=2, min_size=200, keep_largest=False):
    """Removes thin slivers and crumbs from a mask."""
    m = ndimage.binary_opening(mask, structure=morphology.disk(radius))
    lab, n = ndimage.label(m)
    if n == 0:
        return m
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    if keep_largest:
        return lab == (np.argmax(sizes) + 1)
    return np.isin(lab, np.nonzero(sizes >= min_size)[0] + 1)


def _medial_balls(small):
    """Centers and radii (in cells) of the largest circles that fit inside the shape."""
    skel, dist = morphology.medial_axis(small, return_distance=True)
    ii, jj = np.nonzero(skel)
    return ii, jj, dist[ii, jj]


def _disks(shape, balls, value):
    """For every cell, the largest value(di, dj, r) over the medial circles that contain it."""
    out = np.zeros(shape, np.float32)
    for i, j, r in zip(*balls):
        R = int(np.ceil(r))
        i0, i1, j0, j1 = max(i - R, 0), min(i + R + 1, shape[0]), max(j - R, 0), min(j + R + 1, shape[1])
        di = (np.arange(i0, i1) - i)[:, None]
        dj = (np.arange(j0, j1) - j)[None, :]
        np.maximum(out[i0:i1, j0:j1], value(di, dj, r), out=out[i0:i1, j0:j1])
    return out


def height_field(small, step):
    """Round profile: half-thickness (in wp) of the union of balls. Outside the shape the value is minus
    the distance to it, so the result can be contoured at 0."""
    h2 = _disks(small.shape, _medial_balls(small), lambda di, dj, r: r * r - di * di - dj * dj)
    outside = ndimage.distance_transform_edt(~small) * step
    return np.where(small, np.sqrt(np.maximum(h2, 0)) * step, -outside)


def local_thickness(small, step, blur=10.0):
    """For every cell the radius (wp) of the largest circle inside the shape that covers it, smoothed so
    neighbouring parts (neck into body) blend instead of stepping."""
    R = _disks(small.shape, _medial_balls(small), lambda di, dj, r: np.where(di * di + dj * dj <= r * r, r, 0))
    s = blur / step
    num = ndimage.gaussian_filter(R * small, s)
    den = ndimage.gaussian_filter(small.astype(np.float32), s)
    return np.where(small, num / np.maximum(den, 1e-6), 0) * step


def inflate(mask, step=2.0, width=0.8, min_half=0.0, profile="round", bevel=0.3, bevel_max=18.0):
    """Mesh (verts, faces) of the inflated mask. Vertices are (side, img_x, img_y) in wp.

    profile "round": cross-sections are circles (squashed by `width`), good for antlers and ears.
    profile "box": flat sides and a flat rim with slanted edges, the blocky low-poly look. The half-width at
    a spot is `width` times the local thickness of the outline there (1 = square cross-sections), and the
    edges are cut off at 45 degrees over `bevel` times that half-width (at most `bevel_max` wp).
    `width` and `min_half` (smallest half-width in wp) may also be arrays the size of the working image."""
    ys, xs = np.nonzero(mask)
    pad = 4 * step
    y0, x0 = ys.min() - pad, xs.min() - pad
    gy = y0 + np.arange(int((ys.max() + pad - y0) / step) + 1) * step
    gx = x0 + np.arange(int((xs.max() + pad - x0) / step) + 1) * step
    GY, GX = np.meshgrid(gy, gx, indexing="ij")
    small = ndimage.map_coordinates(mask.astype(np.float32), [GY, GX], order=1, cval=0) > 0.5
    def sample(value):
        return ndimage.map_coordinates(np.asarray(value, np.float32), [GY, GX], order=1, mode="nearest") \
            if np.ndim(value) else value
    w, min_half = sample(width), sample(min_half)
    if profile == "box":
        # signed distance to the outline (positive inside), measured on the full-size mask for smooth rims
        m = np.pad(mask, int(pad) + 2)
        sd_full = ndimage.distance_transform_edt(m) - ndimage.distance_transform_edt(~m)
        sd = ndimage.map_coordinates(sd_full, [GY + int(pad) + 2, GX + int(pad) + 2], order=1, mode="nearest")
        half = np.maximum(w * local_thickness(small, step), min_half)
        half = ndimage.grey_dilation(half, size=3)            # so the rim reaches the outline everywhere
        b = np.minimum(bevel * half, bevel_max)
        xmax = half.max() + 3 * step
        side_grid = np.abs(np.arange(-xmax, xmax + step / 2, step, dtype=np.float32))[:, None, None]
        # a bevelled box: inside the outline, within the side walls, and inside the 45 degree corner cut
        field = np.minimum(np.minimum(sd[None], half[None] - side_grid),
                           (half[None] - b[None] + sd[None] - side_grid) / np.sqrt(2))
    else:
        outside = -ndimage.distance_transform_edt(~small) * step
        Hs = np.where(small, np.maximum(height_field(small, step) * w, min_half), outside)
        xmax = Hs.max() + 3 * step
        side_grid = np.abs(np.arange(-xmax, xmax + step / 2, step, dtype=np.float32))[:, None, None]
        field = Hs[None, :, :] - side_grid
    verts, faces, _, _ = measure.marching_cubes(field.astype(np.float32), level=0.0, spacing=(step, step, step))
    return np.stack([verts[:, 0] - xmax, x0 + verts[:, 2], y0 + verts[:, 1]], axis=1), faces


def soft_map(shape, base, spots):
    """Per-pixel value: `base`, blended towards value v near each spot ((x, y), radius, v)."""
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    out = np.full(shape, base, np.float32)
    for (cx, cy), r, v in spots:
        w = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))
        out = out * (1 - w) + v * w
    return out


def save_rgb(path, arr):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(path)


def overlay(ref, masks, path):
    """Debug picture: the reference with each mask tinted in its own color."""
    colors = [(255, 60, 60), (60, 255, 60), (60, 120, 255), (255, 220, 40), (255, 60, 255), (40, 255, 255),
              (255, 140, 0), (160, 80, 255), (255, 255, 255), (120, 255, 160)]
    out = ref.image.copy()
    for m, c in zip(masks, colors):
        out[m] = out[m] * 0.45 + np.array(c) * 0.55
    save_rgb(path, out)
