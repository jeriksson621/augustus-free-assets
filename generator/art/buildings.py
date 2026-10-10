"""Parametric isometric building painter driven by spec descriptions."""
import re

from PIL import Image, ImageDraw

from .core import Iso, rgb, shade, mix, jitter, seeded, outline_alpha
from . import terrain

TERRACOTTA = (178, 82, 50)
PLASTER = (226, 210, 176)
OCHRE = (204, 160, 96)
MARBLE = (232, 228, 218)
STONE = (168, 160, 146)
WOOD = (130, 90, 50)
CANVAS = (222, 206, 166)

COLOR_WORDS = {
    "red": (176, 56, 40), "blue": (60, 90, 170), "green": (60, 130, 60), "yellow": (220, 190, 70),
    "white": MARBLE, "marble": MARBLE, "gold": (220, 180, 60), "brown": (130, 90, 50), "grey": STONE,
    "gray": STONE, "purple": (130, 60, 130), "orange": (220, 130, 50), "black": (50, 45, 40),
}


def _word_color(desc, default):
    for w, c in COLOR_WORDS.items():
        if re.search(r"\b" + w + r"\b", desc):
            return c
    return default


def ground_base(iso, clim, seed, kind="dirt"):
    c = terrain.CLIMATES[clim]
    color = {"dirt": c["dirt"], "paving": (182, 172, 152), "grass": c["grass"], "sand": c["sand"]}[kind]
    t = terrain.textured_tile(color, seed, iso.n)
    iso.img.alpha_composite(t.img, (0, iso.h - 30 * iso.n))


def building(desc, tiles, top, seed, clim="central", group=""):
    """Paint a full iso canvas for a building image."""
    d = desc.lower()
    n = max(1, tiles)
    rise = max(0, top)
    iso = Iso(n, rise)
    rnd = seeded(group, desc, n, top, seed)

    # ground
    if any(k in d for k in ("farm", "crop", "field", "garden", "meadow")):
        ground_base(iso, clim, seed, "grass")
    elif any(k in d for k in ("plaza", "forum", "senate", "paved", "courtyard", "palace", "villa", "temple",
                              "governor", "market", "hippodrome", "colosseum", "amphitheat")):
        ground_base(iso, clim, seed, "paving")
    else:
        ground_base(iso, clim, seed, "dirt")

    if rise == 0 and not any(k in d for k in ("tent", "house", "home")):
        _flat_detail(iso, d, rnd)
        return iso

    m = 0.12 if n == 1 else 0.18
    u0, v0, u1, v1 = m, m, n - m, n - m
    usable = rise + 15 * n  # vertical room above the diamond middle
    style = _style(d)
    wall = _word_color(d, PLASTER)
    if style in ("temple", "oracle", "senate", "academy", "library", "basilica"):
        wall = MARBLE
    roof = TERRACOTTA if not re.search(r"\b(blue|green|purple|gold) roof", d) else _word_color(
        re.search(r"\b(\w+) roof", d).group(1), TERRACOTTA)

    if style == "tent":
        _tent(iso, n, d, rnd)
    elif style == "temple":
        h = min(max(14, rise * 0.45), 40)
        iso.box(u0, v0, u1, v1, 0, 4, STONE)
        iso.box(u0 + 0.15, v0 + 0.15, u1 - 0.15, v1 - 0.15, 4, h, MARBLE, outline=shade(MARBLE, 0.6))
        iso.column_row(u0 + 0.1, v1 - 0.05, u1 - 0.1, v1 - 0.05, 4, h, 4 + 2 * n, MARBLE)
        iso.column_row(u1 - 0.05, v0 + 0.1, u1 - 0.05, v1 - 0.1, 4, h, 2 + 2 * n, MARBLE)
        iso.gable_roof(u0 + 0.05, v0 + 0.05, u1 - 0.05, v1 - 0.05, h, min(rise - h, 6 + 5 * n), roof, along="u")
    elif style == "tower":
        h = min(rise + 10, 26 * n + 20)
        iso.box(u0, v0, u1, v1, 0, h, STONE, outline=shade(STONE, 0.55))
        for k in range(4):
            a = u0 + (u1 - u0) * (k + 0.15) / 4
            b = u0 + (u1 - u0) * (k + 0.55) / 4
            iso.box(a, v1 - 0.12, b, v1, h, h + 5, STONE)
            iso.box(u1 - 0.12, a - u0 + v0, u1, b - u0 + v0, h, h + 5, STONE)
    elif style == "field":
        _field(iso, n, d, rnd)
    elif style == "fountain":
        x, y = iso.pt(n / 2, n / 2)
        iso.box(u0 + 0.1, v0 + 0.1, u1 - 0.1, v1 - 0.1, 0, 4, STONE)
        iso.d.polygon(iso.diamond(u0 + 0.2, v0 + 0.2, u1 - 0.2, v1 - 0.2, 4), fill=rgb((70, 130, 210)))
        iso.cylinder(n / 2, n / 2, 0.08, 4, min(rise, 18), MARBLE)
    elif style == "well":
        iso.cylinder(n / 2, n / 2, 0.25, 0, 8, STONE)
        x, y = iso.pt(n / 2, n / 2, 8)
        iso.d.ellipse([x - 5, y - 2, x + 5, y + 2], fill=rgb((40, 70, 120)))
        iso.d.line([(x - 6, y), (x - 6, y - 12), (x + 6, y - 12), (x + 6, y)], fill=rgb(WOOD), width=2)
    elif style == "statue":
        iso.box(u0 + 0.25 * n, v0 + 0.25 * n, u1 - 0.25 * n, v1 - 0.25 * n, 0, 6 * n, STONE)
        x, y = iso.pt(n / 2, n / 2, 6 * n)
        hgt = min(rise + 10 * n, 14 + 14 * n)
        iso.d.rectangle([x - 2 * n, y - hgt, x + 2 * n, y], fill=rgb(MARBLE))
        iso.d.ellipse([x - 2 * n, y - hgt - 4 * n, x + 2 * n, y - hgt], fill=rgb(MARBLE))
        iso.d.line([(x - 2 * n, y - hgt * 0.7), (x - 5 * n, y - hgt * 0.95)], fill=rgb(MARBLE), width=max(1, n))
    elif style == "arena":
        _arena(iso, n, d, rise)
    elif style == "warehouse":
        h = min(rise, 18 + 4 * n)
        iso.box(u0, v0, u1, v1, 0, h, OCHRE, outline=shade(OCHRE, 0.5))
        iso.gable_roof(u0, v0, u1, v1, h, min(rise - h + 10, 10 + 2 * n), roof, along="u")
    elif style == "fort":
        _fort(iso, n, d, rise)
    elif style == "dock":
        iso.box(u0, v0, u1, v1, 0, 6, WOOD)
        h = min(rise, 20)
        iso.box(u0 + 0.3, v0 + 0.3, u1 - 0.3, v1 - 0.3, 6, h, PLASTER, outline=shade(PLASTER, 0.5))
        iso.gable_roof(u0 + 0.3, v0 + 0.3, u1 - 0.3, v1 - 0.3, h, 8, roof, along="v")
    elif style == "ruin":
        for _ in range(6 * n):
            a, b = rnd.uniform(0.1, n - 0.3), rnd.uniform(0.1, n - 0.3)
            iso.box(a, b, a + 0.2, b + 0.2, 0, rnd.randint(2, 8), (60, 50, 40))
    else:
        _house_like(iso, n, d, rise, wall, roof, rnd, style)
    return iso


def _style(d):
    table = [
        ("tent", ("tent",)),
        ("field", ("crop", "field", "vineyard", "orchard", "farm plot", "growth stage")),
        ("temple", ("temple", "oracle", "shrine", "pantheon")),
        ("tower", ("tower", "gatehouse")),
        ("fountain", ("fountain", "reservoir")),
        ("well", (" well",)),
        ("statue", ("statue", "obelisk", "column monument")),
        ("arena", ("amphitheat", "colosseum", "theater", "theatre", "hippodrome", "arena", "stage")),
        ("warehouse", ("warehouse", "granary", "barn")),
        ("fort", ("fort", "barracks", "parade", "military")),
        ("dock", ("dock", "wharf", "shipyard", "pier")),
        ("ruin", ("rubble", "ruin", "collapsed")),
        ("palace", ("palace", "villa", "governor", "senate", "forum", "academy", "library")),
        ("workshop", ("workshop", "mine", "quarry", "pit", "timber", "kiln")),
        ("insula", ("insula",)),
    ]
    for name, keys in table:
        if any(k in " " + d for k in keys):
            return name
    return "house"


def _house_like(iso, n, d, rise, wall, roof, rnd, style):
    m = 0.12 if n == 1 else 0.15
    if style == "insula":
        h = min(rise - 6, 14 + 12 * n)
        iso.box(m, m, n - m, n - m, 0, h, mix(wall, OCHRE, 0.3), outline=shade(wall, 0.5))
        iso.windows(m, n - m, n - m, 2, h - 2, max(2, n), 2 * n, (60, 40, 30), face="left")
        iso.windows(m, n - m, n - m, 2, h - 2, max(2, n), 2 * n, (50, 32, 24), face="right")
        iso.hip_roof(m, m, n - m, n - m, h, min(8, max(3, rise - h)), roof)
        return
    if style == "palace":
        h = min(max(10, rise * 0.55), 34)
        iso.box(m, m, n - m, n - m, 0, h * 0.75, wall, outline=shade(wall, 0.55))
        iso.windows(m, n - m, n - m, 2, h * 0.7, 1, 3 * n, (80, 60, 40), face="left")
        # courtyard roofs
        iso.hip_roof(m, m, n - m, n - m, h * 0.75, max(4, min(rise - h * 0.75, 6 + 3 * n)), roof)
        if n >= 2:
            iso.column_row(m + 0.1, n - m, n - m - 0.1, n - m, 0, h * 0.7, 3 * n, MARBLE, r=0.05)
        return
    if style == "workshop":
        h = min(max(10, rise * 0.6), 22)
        iso.box(m, m, n - m, n * 0.65, 0, h, mix(wall, WOOD, 0.3), outline=shade(wall, 0.5))
        iso.gable_roof(m, m, n - m, n * 0.65, h, min(8, max(3, rise - h)), roof, along="u")
        # yard with materials
        for k in range(2 * n):
            a = m + 0.2 + k * (n - 2 * m - 0.4) / max(1, 2 * n)
            iso.box(a, n * 0.72, a + 0.15, n * 0.85, 0, 4, (120, 100, 70))
        # chimney
        iso.box(n * 0.7, m + 0.1, n * 0.78, m + 0.2, h, min(rise + 6, h + 12), (110, 90, 80))
        return
    # small houses
    h = min(max(8, rise * 0.55), 10 + 8 * n)
    iso.box(m, m, n - m, n - m, 0, h, wall, outline=shade(wall, 0.5))
    iso.windows(m, n - m, n - m, 1, h, 1, 2 * n, (90, 60, 40), face="left")
    door = [iso.pt(n * 0.45, n - m, 0), iso.pt(n * 0.6, n - m, 0), iso.pt(n * 0.6, n - m, h * 0.6),
            iso.pt(n * 0.45, n - m, h * 0.6)]
    iso.d.polygon(door, fill=rgb((70, 45, 25)))
    roof_h = min(max(3, rise - h + 4), 6 + 4 * n)
    if "shack" in d or "hovel" in d:
        roof = (150, 120, 80)
        iso.gable_roof(m, m, n - m, n - m, h, roof_h, roof, along="v")
    else:
        iso.gable_roof(m, m, n - m, n - m, h, roof_h, roof, along="u" if rnd.random() < 0.5 else "v")


def _tent(iso, n, d, rnd):
    for i in range(n):
        for j in range(n):
            u0, v0 = i + 0.15, j + 0.15
            u1, v1 = i + 0.85, j + 0.85
            h = 12 + (4 if "large" in d else 0)
            col = jitter(CANVAS, 12, rnd)
            apex0 = iso.pt(u0 + 0.1, (v0 + v1) / 2, h)
            apex1 = iso.pt(u1 - 0.1, (v0 + v1) / 2, h)
            iso.d.polygon([iso.pt(u0, v0), iso.pt(u1, v0), apex1, apex0], fill=rgb(shade(col, 1.1)))
            iso.d.polygon([iso.pt(u0, v1), iso.pt(u1, v1), apex1, apex0], fill=rgb(shade(col, 0.85)))
            iso.d.polygon([iso.pt(u1, v0), iso.pt(u1, v1), apex1], fill=rgb(shade(col, 0.65)))
            if "patch" in d or "large" in d:
                x, y = iso.pt((u0 + u1) / 2, v1 - 0.15, h * 0.4)
                iso.d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=rgb((170, 130, 90)))


def _field(iso, n, d, rnd):
    stage = 0
    m = re.search(r"stage (\d)", d)
    if m:
        stage = int(m.group(1))
    crop = (200, 180, 60)
    if "vegetable" in d:
        crop = (90, 150, 60)
    elif "fruit" in d or "orchard" in d:
        crop = (60, 120, 50)
    elif "olive" in d:
        crop = (110, 130, 80)
    elif "vine" in d or "grape" in d:
        crop = (90, 60, 110)
    elif "pig" in d:
        crop = (190, 140, 120)
    soil = (120, 86, 50)
    iso.d.polygon(iso.diamond(0.05, 0.05, n - 0.05, n - 0.05), fill=rgb(soil))
    rows = 4 * n
    for r in range(rows):
        v = (r + 0.5) * n / rows
        iso.d.line([iso.pt(0.1, v, 0), iso.pt(n - 0.1, v, 0)], fill=rgb(shade(soil, 0.8)))
        if stage > 0:
            for k in range(3 * n):
                u = (k + 0.5) * n / (3 * n)
                x, y = iso.pt(u, v)
                hgt = 1 + stage
                iso.d.line([(x, y), (x, y - hgt)], fill=rgb(shade(crop, 0.8 + stage * 0.08)), width=2)


def _arena(iso, n, d, rise):
    cx, cy = iso.pt(n / 2, n / 2)
    rx, ry = n * 26, n * 13
    h = min(rise, 10 + 6 * n)
    iso.d.ellipse([cx - rx, cy - ry - h, cx + rx, cy + ry], fill=rgb(shade(STONE, 0.8)))
    iso.d.ellipse([cx - rx, cy - ry - h, cx + rx, cy + ry - h], fill=rgb(STONE))
    for k in range(4):
        f = 1 - k * 0.15
        iso.d.ellipse([cx - rx * f, cy - ry * f - h, cx + rx * f, cy + ry * f - h],
                      fill=rgb(shade((190, 120, 90) if k % 2 else STONE, 1.0 + k * 0.03)))
    iso.d.ellipse([cx - rx * 0.45, cy - ry * 0.45 - h + 4, cx + rx * 0.45, cy + ry * 0.45 - h + 4],
                  fill=rgb((210, 180, 120)))


def _fort(iso, n, d, rise):
    h = min(rise, 14 + 3 * n)
    m = 0.1
    iso.box(m, m, n - m, m + 0.25, 0, h, STONE, outline=shade(STONE, 0.5))
    iso.box(m, m, m + 0.25, n - m, 0, h, STONE, outline=shade(STONE, 0.5))
    iso.box(m, n - m - 0.25, n - m, n - m, 0, h, STONE, outline=shade(STONE, 0.5))
    iso.box(n - m - 0.25, m, n - m, n - m, 0, h, STONE, outline=shade(STONE, 0.5))
    iso.box(n / 2 - 0.4, n / 2 - 0.4, n / 2 + 0.4, n / 2 + 0.4, 0, h + 4, PLASTER, outline=shade(PLASTER, 0.5))
    iso.gable_roof(n / 2 - 0.4, n / 2 - 0.4, n / 2 + 0.4, n / 2 + 0.4, h + 4, 8, TERRACOTTA, along="u")


def _flat_detail(iso, d, rnd):
    n = iso.n
    if "pool" in d or "water" in d:
        iso.d.polygon(iso.diamond(0.2, 0.2, n - 0.2, n - 0.2), fill=rgb((70, 130, 210)))
    elif "plaza" in d or "paving" in d or "ground" in d:
        t = terrain.plaza_tile(rnd.randint(0, 5), n)
        iso.img.alpha_composite(t.img, (0, iso.h - 30 * n))


def frame_sprite(desc, w, h, frame, total, seed=0):
    """Generic small animation frame (smoke, flame, sparkle, worker...)."""
    d = desc.lower()
    img = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    rnd = seeded(desc, frame, seed)
    t = frame / max(1, total)
    if any(k in d for k in ("fire", "flame", "burn")):
        for k in range(6):
            x = w / 2 + rnd.uniform(-w / 4, w / 4)
            y = h - rnd.uniform(0, h * 0.6)
            r = rnd.uniform(2, max(3, w / 5))
            dr.ellipse([x - r, y - r * 1.6, x + r, y + r], fill=rgb(rnd.choice([(250, 200, 40), (240, 120, 30),
                                                                                   (220, 60, 20)])))
        for k in range(3):
            x = w / 2 + rnd.uniform(-w / 5, w / 5)
            y = h * 0.25 - k * 4
            dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=rgb((90, 90, 90)))
    elif any(k in d for k in ("smoke", "steam", "chimney")):
        for k in range(4):
            yy = h - (t * h + k * h / 4) % h
            r = 2 + (h - yy) / h * 4
            x = w / 2 + (k % 2) * 3 - 1.5
            dr.ellipse([x - r, yy - r, x + r, yy + r], fill=rgb((200 - k * 15, 200 - k * 15, 205 - k * 15)))
    elif any(k in d for k in ("water", "splash", "spray", "fountain")):
        for k in range(8):
            a = (k / 8 + t) % 1
            x = w / 2 + (a - 0.5) * w * 0.8
            y = h * 0.3 + (2 * a - 1) ** 2 * h * 0.5
            dr.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=rgb((150, 200, 250)))
    elif any(k in d for k in ("flag", "banner")):
        dr.line([(2, 0), (2, h - 1)], fill=rgb((90, 70, 40)), width=2)
        wave = [(3 + i, 2 + (h * 0.3) * 0.15 * __import__("math").sin(i * 0.5 + t * 6.28)) for i in range(w - 3)]
        col = _word_color(d, (180, 40, 30))
        for x, y in wave:
            dr.line([(x, y), (x, y + h * 0.35)], fill=rgb(col))
    else:
        # generic: little person working / moving object
        from . import figures
        im, ax, ay = figures.person((frame % 8), frame, tunic=_word_color(d, (150, 110, 70)), state="walk",
                                    scale=min(1.0, h / 46.0) if h < 46 else 1.0)
        img.alpha_composite(im.crop((0, 0, min(im.width, w), min(im.height, h))),
                            (max(0, (w - im.width) // 2), max(0, h - im.height)))
    return img
