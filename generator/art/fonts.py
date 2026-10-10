"""Bitmap font glyphs for GROUP_FONT (10 fonts x 134 glyphs).

Glyph index for byte c in a font = image_offset + CHAR_TO_FONT_IMAGE_DEFAULT[c] - 1
(src/graphics/font.c). The advance is the glyph image's full width + letter spacing, and
ASCII glyphs are drawn with no vertical offset, so each glyph is a full-height cell.
"""
from PIL import Image, ImageDraw, ImageFont

CHAR_TO_FONT_IMAGE_DEFAULT = [
    0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x01,
    0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x3F, 0x40, 0x00, 0x00, 0x41, 0x00, 0x4A, 0x43, 0x44, 0x42, 0x46, 0x4E, 0x45, 0x4F, 0x4D,
    0x3E, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x48, 0x49, 0x00, 0x47, 0x00, 0x4B,
    0x00, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29,
    0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x34, 0x00, 0x00, 0x00, 0x00, 0x50,
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
    0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x81, 0x00, 0x00, 0x00, 0x6E, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x6F, 0x00, 0x00, 0x00,
    0x00, 0x7F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x82, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80,
    0x72, 0x70, 0x71, 0x71, 0x69, 0x83, 0x6D, 0x65, 0x74, 0x6A, 0x73, 0x73, 0x77, 0x75, 0x76, 0x76,
    0x00, 0x6C, 0x7A, 0x78, 0x79, 0x79, 0x7B, 0x00, 0x84, 0x7E, 0x7C, 0x7D, 0x6B, 0x33, 0x00, 0x68,
    0x53, 0x52, 0x54, 0x51, 0x51, 0x85, 0x67, 0x65, 0x57, 0x56, 0x58, 0x55, 0x5B, 0x5A, 0x5C, 0x59,
    0x00, 0x66, 0x5F, 0x5E, 0x60, 0x60, 0x5D, 0x00, 0x86, 0x63, 0x62, 0x64, 0x61, 0x19, 0x00, 0x19,
]

GLYPHS_PER_FONT = 134
FONT_DIR = "/usr/share/fonts/truetype/"

# name, image_offset, letter_spacing, line_height, style
FONTS = [
    ("NORMAL_PLAIN", 0, 1, 11, "normal", "plain"),
    ("NORMAL_BLACK", 134, 0, 11, "normal", "black"),
    ("NORMAL_WHITE", 268, 0, 11, "normal", "white"),
    ("NORMAL_RED", 402, 0, 11, "normal", "red"),
    ("LARGE_PLAIN", 536, 1, 23, "large", "plain"),
    ("LARGE_BLACK", 670, 0, 23, "large", "black"),
    ("LARGE_BROWN", 804, 0, 24, "large", "brown"),
    ("SMALL_PLAIN", 938, 1, 9, "small", "plain"),
    ("NORMAL_GREEN", 1072, 0, 11, "normal", "green"),
    ("NORMAL_BROWN", 1206, 0, 11, "normal", "brown"),
]

# size class -> (ttf path, point size, cell height, baseline row)
SIZES = {
    "normal": (FONT_DIR + "dejavu/DejaVuSans-Bold.ttf", 11, 14, 10),
    "large": (FONT_DIR + "dejavu/DejaVuSerif-Bold.ttf", 20, 28, 22),
    "small": (FONT_DIR + "dejavu/DejaVuSansCondensed-Bold.ttf", 9, 11, 8),
}

COLORS = {
    "plain": ((255, 255, 255), None),
    "black": ((24, 20, 16), None),
    "white": ((250, 248, 240), (40, 32, 24)),
    "red": ((200, 24, 16), None),
    "brown": ((96, 56, 20), None),
    "green": ((24, 128, 32), None),
}


def glyph_chars():
    """glyph number (1-based) -> character to draw."""
    out = {}
    for c in range(0x20, 0x100):
        m = CHAR_TO_FONT_IMAGE_DEFAULT[c]
        if m and m not in out:
            out[m] = bytes([c]).decode("cp1252", errors="replace")
    return out


_font_cache = {}


def _font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def render_glyph(ch, size_class, style, large_brown=False):
    path, pt, cell_h, baseline = SIZES[size_class]
    font = _font(path, pt)
    fg, shadow = COLORS[style]
    is_accented = ch.encode("cp1252", errors="replace")[0] >= 0x80 and ch != "\u00e7"
    extra = {"normal": 3, "large": 5, "small": 2}[size_class] if is_accented else 0
    if large_brown:
        cell_h += 1
    h = cell_h + extra
    if is_accented:
        # no descender rows: the engine shifts these up by (height - line_height)
        h = baseline + 1 + extra
    ascent, descent = font.getmetrics()
    adv = int(round(font.getlength(ch)))
    w = max(2, adv + (1 if shadow else 0))
    mask = Image.new("1", (w + 4, h + 4), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    # place baseline at row `baseline + extra`
    d.text((1, baseline + extra - ascent + 2), ch, font=font, fill=1)
    mask = mask.crop((1, 2, 1 + w, 2 + h))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (w - 1, h - 1), shadow + (255,))
        img.paste(sh, (1, 1), mask.crop((0, 0, w - 1, h - 1)))
    col = Image.new("RGBA", (w, h), fg + (255,))
    img.paste(col, (0, 0), mask)
    if style == "brown":
        # golden highlight on the upper half for large titles
        px = img.load()
        for y in range(h):
            for x in range(w):
                if px[x, y][3] and y < h * 0.45 and px[x, y][:3] == fg:
                    px[x, y] = (140, 90, 30, 255)
    return img


def all_font_images():
    """List of 1340 PIL images in GROUP_FONT order."""
    chars = glyph_chars()
    images = []
    for name, offset, spacing, line_h, size_class, style in FONTS:
        assert offset == len(images)
        for m in range(1, GLYPHS_PER_FONT + 1):
            ch = chars.get(m)
            if ch is None or ch == " ":
                images.append(Image.new("RGBA", (4, 2), (0, 0, 0, 0)))
            else:
                images.append(render_glyph(ch, size_class, style, large_brown=(name == "LARGE_BROWN")))
    return images


if __name__ == "__main__":
    import sys
    imgs = all_font_images()
    # preview sheet
    sheet = Image.new("RGBA", (800, 400), (200, 180, 140, 255))
    x, y = 4, 4
    for i, im in enumerate(imgs):
        if x + im.width > 796:
            x = 4
            y += 26
        if y > 380:
            break
        sheet.alpha_composite(im, (x, y))
        x += im.width + 1
    sheet.save(sys.argv[1])
