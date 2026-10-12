"""Terrain tile painters (grass, water, shores, roads, walls, aqueducts, cliffs ...).

Tile-local coordinates: (u, v) in [0,1]^2 with the top corner at (0,0), right corner (1,0),
bottom corner (1,1), left corner (0,1). Edges: upper-right v=0, lower-right u=1,
lower-left v=1, upper-left u=0.
"""
import math
import re

from PIL import Image, ImageDraw, ImageFilter

from .core import Iso, rgb, shade, mix, jitter, seeded, footprint_mask, outline_alpha

EDGES = ("upper-right", "lower-right", "lower-left", "upper-left")
CORNERS = ("top", "right", "bottom", "left")

CLIMATES = {
    "central": {"grass": (88, 136, 52), "grass2": (104, 148, 60), "dirt": (150, 118, 72), "sand": (210, 190, 130),
                "water": (40, 92, 160), "rock": (128, 120, 108), "tree": (40, 96, 36), "meadow": (140, 160, 60)},
    "north": {"grass": (70, 118, 62), "grass2": (84, 130, 70), "dirt": (128, 104, 72), "sand": (186, 176, 140),
              "water": (36, 80, 130), "rock": (120, 120, 120), "tree": (30, 80, 50), "meadow": (110, 140, 70)},
    "desert": {"grass": (176, 156, 90), "grass2": (190, 168, 100), "dirt": (170, 130, 80), "sand": (226, 206, 150),
               "water": (40, 110, 160), "rock": (160, 130, 96), "tree": (90, 120, 50), "meadow": (150, 160, 70)},
}


from . import theme as _theme

if _theme.T.get("climate_tint"):
    for _c in CLIMATES.values():
        for _k, _f in _theme.T["climate_tint"].items():
            if _k in _c:
                _c[_k] = tuple(max(0, min(255, int(v * f))) for v, f in zip(_c[_k], _f))


def parse_context(desc):
    """Return (positive set, negative set) of directions from 'X at: a, b; no X at: c'."""
    pos, neg = set(), set()
    for part in desc.split(";"):
        part = part.strip()
        m = re.search(r"(no [\w /()-]+?|[\w /()-]+?) at: (.*)$", part)
        if not m:
            continue
        label, items = m.group(1), m.group(2)
        names = set()
        for it in items.split(","):
            it = it.strip().replace(" edge", "").replace(" corner", "")
            if it in EDGES or it in CORNERS:
                names.add(it)
        is_neg = label.startswith("no ") or label.startswith("none") or label.startswith("water")
        if "context:" in label:
            label = label.split("context:")[-1].strip()
        if label.startswith("water"):
            is_neg = True
        (neg if is_neg else pos).update(names)
    if "none at:" in desc:
        m = re.search(r"none at: ([^;]*)", desc)
        for it in m.group(1).split(","):
            it = it.strip().replace(" edge", "").replace(" corner", "")
            if it in EDGES or it in CORNERS:
                neg.add(it)
                pos.discard(it)
    return pos, neg


def tile_uv(x, y, n=1, w=None, h=None, base_y=0):
    """Pixel -> (u, v) for an n-tile canvas (diamond top at base_y)."""
    w = w or 60 * n - 2
    a = (x - w / 2) / (w / 2 / n)
    b = (y - base_y) / 15.0
    u = (a + b) / 2
    v = (b - a) / 2
    return u / n, v / n


def edge_dist(name, u, v):
    return {"upper-right": v, "lower-right": 1 - u, "lower-left": 1 - v, "upper-left": u}[name]


def corner_dist(name, u, v):
    cu, cv = {"top": (0, 0), "right": (1, 0), "bottom": (1, 1), "left": (0, 1)}[name]
    return math.hypot(u - cu, v - cv)


def noise2(x, y, seed=0):
    n = int(x) * 374761393 + int(y) * 668265263 + seed * 2147483647
    n = (n ^ (n >> 13)) * 1274126177
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def smooth_noise(x, y, scale, seed=0):
    xs, ys = x / scale, y / scale
    x0, y0 = math.floor(xs), math.floor(ys)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = noise2(x0, y0, seed)
    b = noise2(x0 + 1, y0, seed)
    c = noise2(x0, y0 + 1, seed)
    d = noise2(x0 + 1, y0 + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def textured_tile(base, seed, n=1, rise=0, variation=14, blotch=0.0, palette=None, world=None):
    """Flat textured ground tile. `world`: (wx, wy) pixel offset for seamless patches."""
    iso = Iso(n, rise)
    px = iso.img.load()
    mask = footprint_mask(n, iso.w, iso.h).load()
    rnd = seeded("tex", seed)
    ox, oy = world or (rnd.randint(0, 999), rnd.randint(0, 999))
    for y in range(iso.h):
        for x in range(iso.w):
            if not mask[x, y]:
                continue
            gx, gy = x + ox, y + oy
            t = smooth_noise(gx, gy, 6, seed % 7) * 0.6 + smooth_noise(gx, gy, 2.5, seed % 5 + 3) * 0.4
            f = 0.86 + t * 0.26
            c = shade(base, f)
            if blotch and smooth_noise(gx, gy, 9, 11) > 1 - blotch:
                c = shade(mix(base, (120, 110, 60), 0.35), f)
            if noise2(gx, gy, seed) < 0.08:
                c = jitter(c, variation, rnd)
            px[x, y] = rgb(c)
    return iso


def grass(clim, seed, n=1, world=None, kind="grass"):
    c = CLIMATES[clim]
    return textured_tile(c[kind if kind in c else "grass"], seed, n, world=world, blotch=0.12)


def _paint_region(iso, inside, color_fn):
    px = iso.img.load()
    mask = footprint_mask(iso.n, iso.w, iso.h).load()
    for y in range(iso.h):
        for x in range(iso.w):
            if mask[x, y]:
                u, v = tile_uv(x, y, iso.n, iso.w, iso.h, iso.base_y)
                r = inside(u, v, x, y)
                if r is not None:
                    px[x, y] = rgb(color_fn(r, u, v, x, y))


def water_tile(clim, frame, seed=0, n=1):
    base = CLIMATES[clim]["water"]
    iso = Iso(n)

    def col(r, u, v, x, y):
        t = math.sin((x * 0.35 + y * 0.9) + frame * math.pi / 3) * 0.5 + 0.5
        t2 = smooth_noise(x + frame * 2, y * 2, 5, 3)
        f = 0.9 + 0.12 * t * t2
        c = shade(base, f)
        if t > 0.93 and t2 > 0.55:
            c = shade(base, 1.35)
        return c

    _paint_region(iso, lambda u, v, x, y: 1, col)
    return iso


def land_field(pos, u, v, x, y, seed, edge_w=0.34, corner_r=0.42, wobble=0.08):
    """Signed distance-ish: >0 inside land."""
    best = -1.0
    jit = (smooth_noise(x, y, 4, seed) - 0.5) * 2 * wobble
    for p in pos:
        if p in EDGES:
            d = edge_w + jit - edge_dist(p, u, v)
        else:
            d = corner_r + jit - corner_dist(p, u, v)
        best = max(best, d)
    return best


def shore_tile(clim, desc, seed, fortified=False):
    pos, neg = parse_context(desc)
    c = CLIMATES[clim]
    iso = water_tile(clim, 0, seed)
    gr = grass(clim, seed)
    gpx = gr.img.load()

    def inside(u, v, x, y):
        f = land_field(pos, u, v, x, y, seed, wobble=0 if fortified else 0.08)
        return f if f > -0.07 else None

    def col(f, u, v, x, y):
        if fortified:
            if f > 0.06:
                return shade((170, 160, 140), 0.9 + 0.2 * noise2(x // 4, y // 3, 5))
            return (110, 100, 88) if f > -0.02 else shade(c["water"], 0.8)
        if f > 0.09:
            return gpx[x, y][:3]
        if f > 0.0:
            return shade(c["sand"], 0.92 + 0.12 * noise2(x, y, seed))
        return mix(c["water"], c["sand"], 0.45)

    _paint_region(iso, inside, col)
    return iso


def strip_shape(pos, u, v, width=0.22):
    """Road-like shape: centre hub plus strips to positive edges and filled positive corners."""
    inside = False
    if pos & set(EDGES):
        if abs(u - 0.5) < width and abs(v - 0.5) < width:
            inside = True
    for p in pos:
        if p == "upper-right" and abs(u - 0.5) < width and v <= 0.5 + width:
            inside = True
        elif p == "lower-left" and abs(u - 0.5) < width and v >= 0.5 - width:
            inside = True
        elif p == "upper-left" and abs(v - 0.5) < width and u <= 0.5 + width:
            inside = True
        elif p == "lower-right" and abs(v - 0.5) < width and u >= 0.5 - width:
            inside = True
        elif p in CORNERS and corner_dist(p, u, v) < 0.75:
            inside = True
    return inside


def road_tile(clim, desc, seed, paved=True):
    pos, neg = parse_context(desc)
    if not pos:
        pos = set()
    iso = grass(clim, seed)
    c = CLIMATES[clim]
    width = 0.3 if paved else 0.24
    lone = not (pos & set(EDGES))

    def inside(u, v, x, y):
        if lone:
            return 1 if (abs(u - 0.5) < width and abs(v - 0.5) < width) else None
        return 1 if strip_shape(pos, u, v, width) else None

    def col(r, u, v, x, y):
        if paved:
            # slab pattern in tile space
            su, sv = u * 6, v * 6
            edge = (su % 1 < 0.1) or (sv % 1 < 0.1)
            base = (168, 160, 148)
            f = 0.85 if edge else 0.95 + 0.1 * noise2(int(su), int(sv), seed)
            return shade(base, f)
        return shade(c["dirt"], 0.9 + 0.15 * smooth_noise(x, y, 3, seed))

    _paint_region(iso, inside, col)
    return iso


def chasm_tile(clim, desc, seed):
    pos, _ = parse_context(desc)
    iso = textured_tile(CLIMATES[clim]["dirt"], seed)

    def inside(u, v, x, y):
        jit = (smooth_noise(x, y, 3, seed) - 0.5) * 0.12
        if pos:
            return 1 if strip_shape(pos, u + jit, v - jit, 0.14) else None
        return 1 if math.hypot(u - 0.5, v - 0.5) < 0.2 + jit else None

    _paint_region(iso, inside, lambda r, u, v, x, y: shade((40, 30, 24), 0.8 + 0.4 * noise2(x, y, 9)))
    return iso


def cliff_tile(clim, desc, seed):
    """Elevation edge: grass where neighbours are as high, rock face towards lower sides."""
    pos, _ = parse_context(desc)
    c = CLIMATES[clim]
    rise = 20
    iso = Iso(1, rise)
    gr = grass(clim, seed)
    # base footprint: rock
    rock = textured_tile(c["rock"], seed + 1)
    iso.img.alpha_composite(rock.img, (0, rise))
    px = iso.img.load()
    gpx = gr.img.load()
    fallback = not pos or "fallback" in desc
    for y in range(30):
        for x in range(58):
            u, v = tile_uv(x, y)
            if not (-0.02 <= u <= 1.02 and -0.02 <= v <= 1.02):
                continue
            f = land_field(pos, u, v, x, y, seed, edge_w=0.55, corner_r=0.6, wobble=0.05) if not fallback else \
                0.35 - math.hypot(u - 0.5, v - 0.5)
            if f > 0:
                # raised plateau surface: draw shifted up by an amount proportional to f
                lift = int(min(rise, 6 + f * 40))
                yy = y + rise - lift
                if 0 <= yy < iso.h:
                    px[x, yy] = gpx[x, y]
                    # fill the face below the lifted surface
                    for k in range(yy + 1, y + rise + 1):
                        if px[x, k][3] == 0 or True:
                            t = (k - yy) / max(1, lift)
                            px[x, k] = rgb(shade(c["rock"], 0.6 + 0.35 * (1 - t) + 0.1 * noise2(x, k, seed)))
    return iso


def tree_tile(clim, seed, density, n=1):
    c = CLIMATES[clim]
    rise = [40, 45, 48, 50][density]
    iso = grass(clim, seed, n)
    big = Iso(n, rise)
    big.img.alpha_composite(iso.img, (0, rise))
    d = big.d
    rnd = seeded("tree", seed, density, clim)
    count = 1 + density // 2 + rnd.randint(0, 1)
    spots = [(rnd.uniform(0.3, 0.7), rnd.uniform(0.3, 0.7)) for _ in range(count)]
    spots.sort(key=lambda p: p[0] + p[1])
    leaf = shade(c["tree"], 1.0 - density * 0.06)
    for (u, v) in spots:
        x, y = big.pt(u, v)
        th = rnd.randint(8, 12)
        r = rnd.randint(9, 13) + density
        d.rectangle([x - 1, y - th, x + 1, y], fill=rgb((90, 60, 30)))
        cy = y - th - r * 0.6
        for k in range(5):
            ox = rnd.uniform(-r * 0.5, r * 0.5)
            oy = rnd.uniform(-r * 0.4, r * 0.3)
            rr = r * rnd.uniform(0.55, 0.8)
            d.ellipse([x + ox - rr, cy + oy - rr, x + ox + rr, cy + oy + rr], fill=rgb(jitter(leaf, 10, rnd)))
        d.ellipse([x - r * 0.5, cy - r * 0.7, x + r * 0.1, cy - r * 0.1], fill=rgb(shade(leaf, 1.25)))
    big.img = outline_alpha(big.img, (24, 40, 20)) if False else big.img
    return big


def shrub_tile(clim, seed):
    c = CLIMATES[clim]
    iso = grass(clim, seed)
    rnd = seeded("shrub", seed)
    for _ in range(4):
        u, v = rnd.uniform(0.25, 0.75), rnd.uniform(0.25, 0.75)
        x, y = iso.pt(u, v)
        r = rnd.randint(3, 5)
        iso.d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.5], fill=rgb(shade(c["tree"], rnd.uniform(0.9, 1.2))))
    return iso


def rock_tile(clim, seed, n=1):
    c = CLIMATES[clim]
    rise = {1: 20, 2: 40, 3: 55}[n]
    base = grass(clim, seed, n)
    iso = Iso(n, rise)
    iso.img.alpha_composite(base.img, (0, rise))
    rnd = seeded("rock", seed, n)
    count = {1: 3, 2: 6, 3: 9}[n]
    pts = sorted([(rnd.uniform(0.2, n - 0.2), rnd.uniform(0.2, n - 0.2)) for _ in range(count)],
                 key=lambda p: p[0] + p[1])
    for (u, v) in pts:
        x, y = iso.pt(u, v)
        r = rnd.randint(6, 10) + n * 3
        hgt = r * rnd.uniform(0.8, 1.4)
        poly = [(x - r, y), (x - r * 0.7, y - hgt * 0.7), (x - r * 0.1, y - hgt), (x + r * 0.6, y - hgt * 0.8),
                (x + r, y - hgt * 0.2), (x + r * 0.5, y + r * 0.25), (x - r * 0.4, y + r * 0.3)]
        iso.d.polygon(poly, fill=rgb(c["rock"]))
        iso.d.polygon([poly[0], poly[1], poly[2], (x, y - hgt * 0.3), poly[6]], fill=rgb(shade(c["rock"], 1.18)))
        iso.d.polygon([poly[3], poly[4], poly[5], (x, y - hgt * 0.3), poly[2]], fill=rgb(shade(c["rock"], 0.72)))
    return iso


def meadow_tile(clim, seed, deep=False):
    c = CLIMATES[clim]
    iso = textured_tile(mix(c["grass"], c["meadow"], 0.7 if deep else 0.45), seed, blotch=0.1)
    rnd = seeded("meadow", seed)
    for _ in range(10 if deep else 6):
        u, v = rnd.uniform(0.1, 0.9), rnd.uniform(0.1, 0.9)
        x, y = iso.pt(u, v)
        iso.d.point((x, y), fill=rgb(rnd.choice([(230, 210, 60), (240, 240, 230), (200, 80, 160)])))
    return iso


def wall_tile(desc, seed, rise=36, stone=(150, 146, 136)):
    pos, _ = parse_context(desc)
    # gatehouse-context descriptions name edges in prose
    for e in EDGES:
        if ("on " + e) in desc or ("and " + e) in desc or ("along the " + e) in desc:
            pos.add(e)
    iso = Iso(1, rise)
    base = textured_tile((120, 112, 96), seed)
    iso.img.alpha_composite(base.img, (0, rise))
    h = 30
    t = 0.2  # half thickness
    parts = []
    if "upper-left" in pos:
        parts.append((0, 0.5 - t, 0.5 - t, 0.5 + t))
    if "upper-right" in pos:
        parts.append((0.5 - t, 0, 0.5 + t, 0.5 - t))
    parts.append((0.5 - t - 0.04, 0.5 - t - 0.04, 0.5 + t + 0.04, 0.5 + t + 0.04))
    if "lower-right" in pos:
        parts.append((0.5 + t, 0.5 - t, 1, 0.5 + t))
    if "lower-left" in pos:
        parts.append((0.5 - t, 0.5 + t, 0.5 + t, 1))
    for (u0, v0, u1, v1) in parts:
        iso.box(u0, v0, u1, v1, 0, h, stone, outline=shade(stone, 0.5))
        # crenellations
        for k in range(3):
            a = u0 + (u1 - u0) * (k + 0.2) / 3
            b = u0 + (u1 - u0) * (k + 0.6) / 3
            iso.box(a, v1 - 0.08, b, v1, h, h + 4, stone)
    return iso


def aqueduct_tile(clim, desc, seed, water=True):
    pos, _ = parse_context(desc)
    over = None
    if "runs upper-right<->lower-left" in desc:
        pos = {"upper-right", "lower-left"}
    elif "runs upper-left<->lower-right" in desc:
        pos = {"upper-left", "lower-right"}
    if "straight piece running upper-right<->lower-left" in desc:
        pos = {"upper-right", "lower-left"}
    if "straight piece running upper-left<->lower-right" in desc:
        pos = {"upper-left", "lower-right"}
    if "PAVED road" in desc:
        over = "paved"
    elif "DIRT road" in desc:
        over = "dirt"
    rise = 28
    iso = Iso(1, rise)
    if over:
        ground = road_tile(clim, "context: road at: " + (
            "lower-right edge, upper-left edge" if "upper-right" in pos else "upper-right edge, lower-left edge"),
                           seed, paved=(over == "paved"))
    else:
        ground = grass(clim, seed)
    iso.img.alpha_composite(ground.img, (0, rise))
    stone = (196, 186, 160)
    t = 0.16
    z0, z1 = 18, 24
    parts = []
    if "upper-left" in pos:
        parts.append((0, 0.5 - t, 0.5, 0.5 + t))
    if "upper-right" in pos:
        parts.append((0.5 - t, 0, 0.5 + t, 0.5))
    parts.append((0.5 - t, 0.5 - t, 0.5 + t, 0.5 + t))
    if "lower-right" in pos:
        parts.append((0.5, 0.5 - t, 1, 0.5 + t))
    if "lower-left" in pos:
        parts.append((0.5 - t, 0.5, 0.5 + t, 1))
    for (u0, v0, u1, v1) in parts:
        # piers
        iso.box(u0 + (u1 - u0) * 0.35, v0 + (v1 - v0) * 0.35, u0 + (u1 - u0) * 0.65, v0 + (v1 - v0) * 0.65,
                0, z0, shade(stone, 0.9))
    for (u0, v0, u1, v1) in parts:
        iso.box(u0, v0, u1, v1, z0, z1, stone, outline=shade(stone, 0.6))
        # channel on top
        cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
        du, dv = (u1 - u0) / 2 * 0.95, (v1 - v0) / 2 * 0.95
        if du > dv:
            ch = [iso.pt(cu - du, cv - 0.06, z1), iso.pt(cu + du, cv - 0.06, z1), iso.pt(cu + du, cv + 0.06, z1),
                  iso.pt(cu - du, cv + 0.06, z1)]
        else:
            ch = [iso.pt(cu - 0.06, cv - dv, z1), iso.pt(cu + 0.06, cv - dv, z1), iso.pt(cu + 0.06, cv + dv, z1),
                  iso.pt(cu - 0.06, cv + dv, z1)]
        iso.d.polygon(ch, fill=rgb((60, 130, 220) if water else (120, 105, 80)))
    return iso


def plaza_tile(seed, n=1):
    iso = Iso(n)
    px = iso.img.load()
    mask = footprint_mask(n, iso.w, iso.h).load()
    colors = [(200, 190, 170), (176, 164, 146), (214, 206, 188)]
    for y in range(iso.h):
        for x in range(iso.w):
            if mask[x, y]:
                u, v = tile_uv(x, y, n, iso.w, iso.h, iso.base_y)
                gu, gv = int(u * n * 4), int(v * n * 4)
                c = colors[(gu + gv + seed) % 3] if (gu + gv) % 2 else colors[0]
                if (u * n * 4) % 1 < 0.08 or (v * n * 4) % 1 < 0.08:
                    c = shade(c, 0.8)
                px[x, y] = rgb(c)
    return iso


def garden_tile(clim, seed, n=1):
    iso = grass(clim, seed, n, kind="grass2")
    rnd = seeded("garden", seed, n)
    # paths
    path = [iso.pt(0, n / 2), iso.pt(n, n / 2)]
    iso.d.line(path, fill=rgb((196, 176, 130)), width=2)
    iso.d.line([iso.pt(n / 2, 0), iso.pt(n / 2, n)], fill=rgb((196, 176, 130)), width=2)
    for _ in range(5 * n * n):
        u, v = rnd.uniform(0.15, n - 0.15), rnd.uniform(0.15, n - 0.15)
        x, y = iso.pt(u, v)
        col = rnd.choice([(220, 60, 60), (240, 220, 80), (250, 250, 250), (200, 90, 200), (40, 110, 40)])
        iso.d.ellipse([x - 2, y - 1, x + 2, y + 1], fill=rgb(col))
    return iso


def flat_color_tile(color, seed=0, pattern=False, n=1):
    iso = Iso(n)
    iso.fill_ground(color)
    if pattern:
        iso.d.line([iso.pt(0, 0), iso.pt(1, 0), iso.pt(1, 1), iso.pt(0, 1), iso.pt(0, 0)],
                   fill=rgb(shade(color, 0.7)))
    return iso


def overlay_footprint_tile(color, part):
    """Flattened building footprint piece; part 0..3: top/left/right/plain edges outlined."""
    iso = Iso(1)
    iso.fill_ground(color)
    dark = rgb(shade(color, 0.6))
    edges = {0: [(0, 1), (1, 2)], 1: [(0, 1)], 2: [(1, 2)], 3: []}.get(part, [])
    corners = [iso.pt(0, 1), iso.pt(0, 0), iso.pt(1, 0), iso.pt(1, 1)]
    for a, b in edges:
        iso.d.line([corners[a], corners[b]], fill=dark, width=1)
    return iso


def flag_tile(clim, seed, color, orient):
    rise = 40
    iso = Iso(1, rise)
    iso.img.alpha_composite(grass(clim, seed).img, (0, rise))
    x, y = iso.pt(0.5, 0.5)
    iso.d.line([(x, y), (x, y - 36)], fill=rgb((90, 70, 40)), width=2)
    sgn = 1 if orient % 2 == 0 else -1
    iso.d.polygon([(x, y - 36), (x + sgn * 16, y - 31), (x, y - 26)], fill=rgb(color))
    return iso


def ramp_tile(clim, seed):
    rise = 20
    iso = Iso(2, rise)
    iso.img.alpha_composite(grass(clim, seed, 2).img, (0, rise))
    stone = (170, 160, 140)
    # sloped surface from v=0 (high) to v=2 (low)
    top = [iso.pt(0.2, 0.0, 20), iso.pt(1.8, 0.0, 20), iso.pt(1.8, 2, 0), iso.pt(0.2, 2, 0)]
    side = [iso.pt(1.8, 0.0, 0), iso.pt(1.8, 0.0, 20), iso.pt(1.8, 2, 0)]
    iso.d.polygon(side, fill=rgb(shade(stone, 0.65)))
    iso.d.polygon(top, fill=rgb(stone))
    for k in range(1, 8):
        v = k * 2 / 8
        iso.d.line([iso.pt(0.2, v, 20 - v * 10), iso.pt(1.8, v, 20 - v * 10)], fill=rgb(shade(stone, 0.8)))
    return iso
