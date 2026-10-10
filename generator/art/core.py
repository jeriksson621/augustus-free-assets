"""Core drawing helpers for procedurally generated isometric art.

Coordinate conventions for an isometric canvas of `n` tiles and `rise` pixels:
width = 60n - 2, height = 30n + rise. The footprint diamond occupies the bottom 30n rows.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

TRANSPARENT = (0, 0, 0, 0)


def rgb(c, a=255):
    return (c[0], c[1], c[2], a)


def clamp(v):
    return max(0, min(255, int(v)))


def shade(c, f):
    """f > 1 lightens, f < 1 darkens."""
    if f >= 1:
        return tuple(clamp(x + (255 - x) * (f - 1)) for x in c[:3])
    return tuple(clamp(x * f) for x in c[:3])


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def jitter(c, amount, rnd):
    d = rnd.randint(-amount, amount)
    return tuple(clamp(x + d) for x in c[:3])


def new(w, h, color=TRANSPARENT):
    return Image.new("RGBA", (w, h), color)


class Iso:
    """Isometric canvas helper."""

    def __init__(self, tiles, rise=0):
        self.n = tiles
        self.w = 60 * tiles - 2
        self.h = 30 * tiles + rise
        self.rise = rise
        self.img = new(self.w, self.h)
        self.d = ImageDraw.Draw(self.img)
        self.base_y = self.h - 30 * tiles  # y of the diamond's top vertex

    # ground point from tile-space coordinates (0..n along each axis)
    # u runs from the top vertex towards the right vertex, v from the top vertex to the left.
    def pt(self, u, v, z=0):
        x = self.w / 2 + (u - v) * (self.w / 2) / self.n
        y = self.base_y + (u + v) * 15 - z
        return (x, y)

    def diamond(self, u0=0, v0=0, u1=None, v1=None, z=0):
        u1 = self.n if u1 is None else u1
        v1 = self.n if v1 is None else v1
        return [self.pt(u0, v0, z), self.pt(u1, v0, z), self.pt(u1, v1, z), self.pt(u0, v1, z)]

    def fill_ground(self, color, rnd=None, noise=0, palette=None):
        mask = self.ground_mask()
        self.img.paste(rgb(color), (0, 0), mask)
        if rnd and (noise or palette):
            speckle(self.img, mask, color, noise, rnd, palette=palette)

    def ground_mask(self):
        return footprint_mask(self.n, self.w, self.h)

    def box(self, u0, v0, u1, v1, z0, z1, wall, roof=None, outline=None, left_f=0.85, right_f=0.62, roof_f=1.08):
        """Axis-aligned box; draws the two visible walls and the top."""
        roof = roof or wall
        # visible walls: the 'v1' face (front-left) and 'u1' face (front-right)
        left = [self.pt(u0, v1, z0), self.pt(u1, v1, z0), self.pt(u1, v1, z1), self.pt(u0, v1, z1)]
        right = [self.pt(u1, v0, z0), self.pt(u1, v1, z0), self.pt(u1, v1, z1), self.pt(u1, v0, z1)]
        top = [self.pt(u0, v0, z1), self.pt(u1, v0, z1), self.pt(u1, v1, z1), self.pt(u0, v1, z1)]
        self.d.polygon(left, fill=rgb(shade(wall, left_f)), outline=rgb(outline) if outline else None)
        self.d.polygon(right, fill=rgb(shade(wall, right_f)), outline=rgb(outline) if outline else None)
        self.d.polygon(top, fill=rgb(shade(roof, roof_f)), outline=rgb(outline) if outline else None)
        return left, right, top

    def gable_roof(self, u0, v0, u1, v1, z, height, color, along="u", overhang=0.0):
        """Pitched roof; ridge runs along the given axis."""
        o = overhang
        u0, v0, u1, v1 = u0 - o, v0 - o, u1 + o, v1 + o
        if along == "u":
            vm = (v0 + v1) / 2
            r0, r1 = self.pt(u0, vm, z + height), self.pt(u1, vm, z + height)
            front = [self.pt(u0, v1, z), self.pt(u1, v1, z), r1, r0]  # slope facing viewer-left
            back = [self.pt(u0, v0, z), self.pt(u1, v0, z), r1, r0]
            gable = [self.pt(u1, v0, z), self.pt(u1, v1, z), r1]
            self.d.polygon(back, fill=rgb(shade(color, 1.1)))
            self.d.polygon(front, fill=rgb(shade(color, 0.92)))
            self.d.polygon(gable, fill=rgb(shade(color, 0.7)))
            self.d.line([r0, r1], fill=rgb(shade(color, 1.25)))
        else:
            um = (u0 + u1) / 2
            r0, r1 = self.pt(um, v0, z + height), self.pt(um, v1, z + height)
            front = [self.pt(u1, v0, z), self.pt(u1, v1, z), r1, r0]  # slope facing viewer-right
            back = [self.pt(u0, v0, z), self.pt(u0, v1, z), r1, r0]
            gable = [self.pt(u0, v1, z), self.pt(u1, v1, z), r1]
            self.d.polygon(back, fill=rgb(shade(color, 1.1)))
            self.d.polygon(front, fill=rgb(shade(color, 0.72)))
            self.d.polygon(gable, fill=rgb(shade(color, 0.9)))
            self.d.line([r0, r1], fill=rgb(shade(color, 1.25)))

    def hip_roof(self, u0, v0, u1, v1, z, height, color):
        uc, vc = (u0 + u1) / 2, (v0 + v1) / 2
        du = (u1 - u0) / 2
        dv = (v1 - v0) / 2
        k = min(du, dv)
        a = self.pt(uc - (du - k), vc, z + height)
        b = self.pt(uc + (du - k), vc, z + height) if du >= dv else self.pt(uc, vc + (dv - k), z + height)
        if du < dv:
            a = self.pt(uc, vc - (dv - k), z + height)
        c00, c10, c11, c01 = self.pt(u0, v0, z), self.pt(u1, v0, z), self.pt(u1, v1, z), self.pt(u0, v1, z)
        if du >= dv:
            self.d.polygon([c00, c10, b, a], fill=rgb(shade(color, 1.12)))
            self.d.polygon([c01, c11, b, a], fill=rgb(shade(color, 0.92)))
            self.d.polygon([c10, c11, b], fill=rgb(shade(color, 0.72)))
        else:
            self.d.polygon([c00, c01, b, a], fill=rgb(shade(color, 1.12)))
            self.d.polygon([c10, c11, b, a], fill=rgb(shade(color, 0.72)))
            self.d.polygon([c01, c11, b], fill=rgb(shade(color, 0.92)))

    def cylinder(self, u, v, r, z0, z1, color):
        cx, cy0 = self.pt(u, v, z0)
        _, cy1 = self.pt(u, v, z1)
        rx, ry = r * 30, r * 15
        self.d.rectangle([cx - rx, cy1, cx + rx, cy0], fill=rgb(shade(color, 0.8)))
        self.d.rectangle([cx - rx, cy1, cx, cy0], fill=rgb(shade(color, 0.95)))
        self.d.ellipse([cx - rx, cy0 - ry, cx + rx, cy0 + ry], fill=rgb(shade(color, 0.8)))
        self.d.ellipse([cx - rx, cy1 - ry, cx + rx, cy1 + ry], fill=rgb(shade(color, 1.1)))

    def column_row(self, u0, v0, u1, v1, z0, z1, count, color, r=0.06):
        for i in range(count):
            t = (i + 0.5) / count
            self.cylinder(u0 + (u1 - u0) * t, v0 + (v1 - v0) * t, r, z0, z1, color)

    def dome(self, u, v, r, z, color):
        cx, cy = self.pt(u, v, z)
        rx = r * 30
        self.d.pieslice([cx - rx, cy - rx, cx + rx, cy + rx], 180, 360, fill=rgb(shade(color, 0.95)))
        self.d.pieslice([cx - rx, cy - rx, cx, cy + rx * 0.2], 180, 270, fill=rgb(shade(color, 1.12)))
        self.d.ellipse([cx - rx, cy - rx * 0.25, cx + rx, cy + rx * 0.25], fill=rgb(shade(color, 0.85)))

    def windows(self, u0, v1, u1, z0, z1, rows, cols, color, face="left"):
        """Small dark windows on the front-left (v=v1) face or front-right (u=u1) face."""
        for r in range(rows):
            for c in range(cols):
                t0 = (c + 0.3) / cols
                t1 = (c + 0.7) / cols
                zz0 = z0 + (z1 - z0) * (r + 0.3) / rows
                zz1 = z0 + (z1 - z0) * (r + 0.75) / rows
                if face == "left":
                    a, b = u0 + (u1 - u0) * t0, u0 + (u1 - u0) * t1
                    poly = [self.pt(a, v1, zz0), self.pt(b, v1, zz0), self.pt(b, v1, zz1), self.pt(a, v1, zz1)]
                else:
                    a, b = u0 + (u1 - u0) * t0, u0 + (u1 - u0) * t1  # here u0/u1 are v-range
                    poly = [self.pt(v1, a, zz0), self.pt(v1, b, zz0), self.pt(v1, b, zz1), self.pt(v1, a, zz1)]
                self.d.polygon(poly, fill=rgb(color))


FOOTPRINT_X_START = [28, 26, 24, 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2, 0,
                     0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
_mask_cache = {}


def footprint_mask(n, w=None, h=None):
    """Exact pixel mask of the footprint diamond (matching the sg2 tile layout)."""
    w = w or 60 * n - 2
    h = h or 30 * n
    key = (n, w, h)
    if key in _mask_cache:
        return _mask_cache[key].copy()
    m = Image.new("L", (w, h), 0)
    px = m.load()
    y_base = h - 30 * n
    x_start = (n - 1) * 30
    tiles = []
    for i in range(n):
        x = -30 * i + x_start
        for j in range(i + 1):
            tiles.append((x + 60 * j, 15 * i))
    for i in range(n - 2, -1, -1):
        x = -30 * i + x_start
        for j in range(i + 1):
            tiles.append((x + 60 * j, 15 * (n * 2 - i - 2)))
    for tx, ty in tiles:
        for yy in range(30):
            xs = FOOTPRINT_X_START[yy]
            for xx in range(xs, 58 - xs):
                px[tx + xx, y_base + ty + yy] = 255
    _mask_cache[key] = m
    return m.copy()


def speckle(img, mask, base, amount, rnd, density=0.35, palette=None):
    """Add per-pixel noise to masked area."""
    px = img.load()
    mk = mask.load() if mask else None
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if mk is not None and not mk[x, y]:
                continue
            if rnd.random() < density:
                if palette:
                    c = palette[rnd.randrange(len(palette))]
                else:
                    c = jitter(base, amount, rnd)
                px[x, y] = rgb(c)


def outline_alpha(img, color=(30, 24, 18)):
    """Draw a 1px dark outline around opaque pixels (in place)."""
    a = img.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(3))
    edge = Image.new("RGBA", img.size, rgb(color))
    base = Image.new("RGBA", img.size, TRANSPARENT)
    base.paste(edge, mask=grown)
    base.alpha_composite(img)
    return base


def binarize_alpha(img, threshold=110):
    """RLE images only support on/off transparency; pre-compose soft edges."""
    r, g, b, a = img.split()
    a = a.point(lambda v: 255 if v >= threshold else 0)
    return Image.merge("RGBA", (r, g, b, a))


def seeded(*keys):
    h = 0
    for k in keys:
        for ch in str(k):
            h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return random.Random(h)
