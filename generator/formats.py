"""Binary writers for the Caesar III data formats used by Augustus.

* .sg2 index + .555 pixel files (main graphics, enemy graphics)
* .eng text files (c3.eng string groups, c3_mm.eng messages)

Layouts follow the readers in Augustus' src/core/image.c and src/core/lang.c.
"""
import struct

HEADER_SIZE = 20680
ENTRY_SIZE = 64
MAIN_ENTRIES = 10000
ENEMY_ENTRIES = 801
MAX_GROUPS = 300
FOOTPRINT_WIDTH = 58
FOOTPRINT_HEIGHT = 30
FOOTPRINT_X_START = [28, 26, 24, 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2, 0,
                     0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
IMAGE_TYPE_ISOMETRIC = 30
TRANSPARENT_555 = 0x781F  # decodes to COLOR_SG2_TRANSPARENT (0xfff700ff)


def rgb_to_555(r, g, b):
    c = ((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3)
    if c == TRANSPARENT_555:
        c ^= 1  # never emit the colour key by accident
    return c


def _pixels_555(img):
    """Return (list of 555 colours or None for transparent) for an RGBA PIL image."""
    data = img.convert("RGBA").tobytes()
    out = []
    for i in range(0, len(data), 4):
        if data[i + 3] < 128:
            out.append(None)
        else:
            out.append(rgb_to_555(data[i], data[i + 1], data[i + 2]))
    return out


def encode_uncompressed(img):
    """Fast path using PIL band maths: little-endian RGB555 words."""
    from PIL import Image as PImage, ImageMath
    rgba = img.convert("RGBA")
    r, g, b, a = [band.convert("I") for band in rgba.split()]
    lo = ImageMath.lambda_eval(lambda e: (((e["g"] >> 3) & 7) << 5) | (e["b"] >> 3), g=g, b=b)
    hi = ImageMath.lambda_eval(lambda e: ((e["r"] >> 3) << 2) | (e["g"] >> 6), r=r, g=g)
    lo = lo.convert("L")
    hi = hi.convert("L")
    # transparent pixels -> colour key 0x781F
    mask = a.convert("L").point([255] * 128 + [0] * 128)
    lo.paste(0x1F, (0, 0), mask)
    hi.paste(0x78, (0, 0), mask)
    out = bytearray(len(lo.tobytes()) * 2)
    out[0::2] = lo.tobytes()
    out[1::2] = hi.tobytes()
    return bytes(out)


def encode_compressed(img):
    """RLE as read by convert_compressed(): 255,n = skip n transparent; n (<255) = n raw pixels."""
    px = _pixels_555(img)
    out = bytearray()
    i = 0
    n = len(px)
    # trailing transparency needs no encoding
    while n > 0 and px[n - 1] is None:
        n -= 1
    while i < n:
        if px[i] is None:
            run = 0
            while i < n and px[i] is None and run < 255:
                run += 1
                i += 1
            out += bytes((255, run))
        else:
            start = i
            while i < n and px[i] is not None and i - start < 254:
                i += 1
            run = i - start
            out.append(run)
            out += struct.pack("<%dH" % run, *px[start:i])
    return bytes(out)


def encode_footprint(img, tiles):
    """Isometric footprint: tiles in the order of convert_isometric_footprint()."""
    w = img.width
    rgba = img.convert("RGBA")
    pix = rgba.load()
    out = bytearray()
    x_start = (tiles - 1) * 30

    def tile(x0, y0):
        for y in range(FOOTPRINT_HEIGHT):
            xs = FOOTPRINT_X_START[y]
            for x in range(xs, FOOTPRINT_WIDTH - xs):
                r, g, b, a = pix[x0 + x, y0 + y]
                out.extend(struct.pack("<H", rgb_to_555(r, g, b)))

    for i in range(tiles):
        x = -30 * i + x_start
        y = 15 * i
        for _ in range(i + 1):
            tile(x, y)
            x += 60
    for i in range(tiles - 2, -1, -1):
        x = -30 * i + x_start
        y = 15 * (tiles * 2 - i - 2)
        for _ in range(i + 1):
            tile(x, y)
            x += 60
    assert w == 60 * tiles - 2
    return bytes(out)


class Image:
    """One slot in an sg2 file.

    kind: 'empty', 'sprite' (compressed), 'opaque' (uncompressed), 'iso' (isometric).
    For 'iso', `img` is the full canvas (width 60*tiles-2, height H) and has_top says
    whether the part above the footprint middle is stored as a compressed top.
    """

    def __init__(self, kind="empty", img=None, tiles=0, has_top=False, anim=None,
                 external=False, bitmap_id=0):
        self.kind = kind
        self.img = img
        self.tiles = tiles
        self.has_top = has_top
        self.anim = anim  # dict num_sprites, offset_x, offset_y, can_reverse, speed_id
        self.external = external
        self.bitmap_id = bitmap_id

    def encode(self):
        """Return (data, uncompressed_length, is_compressed, width, height)."""
        if getattr(self, "_enc", None) is None:
            self._enc = self._encode()
        return self._enc

    def _encode(self):
        if self.kind == "empty" or self.img is None:
            return b"", 0, 0, 0, 0
        w, h = self.img.size
        if self.kind == "sprite":
            d = encode_compressed(self.img)
            return d, len(d), 1, w, h
        if self.kind == "opaque":
            d = encode_uncompressed(self.img)
            return d, len(d), 0, w, h
        if self.kind == "iso":
            n = self.tiles
            fh = 30 * n
            base = self.img.crop((0, h - fh, w, h))
            foot = encode_footprint(base, n)
            if self.has_top:
                top = self.img.crop((0, 0, w, h - 15 * n))
                topd = encode_compressed(top)
                return foot + topd, len(foot), 0, w, h
            return foot, len(foot), 0, w, h
        raise ValueError(self.kind)


def _entry(offset, length, ulen, width, height, im, is_compressed):
    a = im.anim or {}
    num_sprites = a.get("num_sprites", 0)
    e = bytearray(ENTRY_SIZE)
    struct.pack_into("<iii", e, 0, offset, length, ulen)
    struct.pack_into("<HH", e, 20, width, height)
    struct.pack_into("<H", e, 30, num_sprites)
    struct.pack_into("<hh", e, 34, a.get("offset_x", 0), a.get("offset_y", 0))
    struct.pack_into("<b", e, 48, a.get("can_reverse", 0))
    e[50] = IMAGE_TYPE_ISOMETRIC if im.kind == "iso" else (1 if im.kind == "sprite" else 0)
    e[51] = is_compressed
    e[52] = 1 if im.external else 0
    e[53] = 1 if (im.kind == "iso" and im.has_top) else 0
    e[56] = im.bitmap_id
    e[58] = a.get("speed_id", 0)
    return bytes(e)


def write_sg2(sg2_path, data_path, images, group_ids, bitmaps, num_entries, external_dir=None):
    """images: list of Image (len == num_entries). group_ids: list of MAX_GROUPS ints.
    bitmaps: list of names (index = bitmap_id). External images are written to
    external_dir/<bitmap name>.555, one file per bitmap name."""
    assert len(images) == num_entries
    header = bytearray(80)
    struct.pack_into("<ii", header, 0, 0xd5, num_entries)
    groups = struct.pack("<%dH" % MAX_GROUPS, *group_ids)
    bm = bytearray(20000)
    for i, name in enumerate(bitmaps[:100]):
        raw = name.encode("ascii")[:199]
        bm[i * 200:i * 200 + len(raw)] = raw
    index = bytearray()
    data = bytearray(4)
    externals = {}
    ext_offsets = {}
    for i, im in enumerate(images):
        d, ulen, comp, w, h = im.encode()
        if i == 0:
            d = b""
        if im.external and d:
            buf = externals.setdefault(im.bitmap_id, bytearray())
            if id(im) not in ext_offsets:
                ext_offsets[id(im)] = len(buf) + 1
                buf += d
            index += _entry(ext_offsets[id(im)], len(d), ulen, w, h, im, comp)
        else:
            index += _entry(len(data), len(d), ulen, w, h, im, comp)
            data += d
    with open(sg2_path, "wb") as f:
        f.write(header)
        f.write(groups)
        f.write(bm)
        f.write(index)
    with open(data_path, "wb") as f:
        f.write(data)
    if externals:
        import os
        os.makedirs(external_dir, exist_ok=True)
        for bid, buf in externals.items():
            name = bitmaps[bid].rsplit(".", 1)[0] + ".555"
            with open(os.path.join(external_dir, name), "wb") as f:
                f.write(buf)
    return len(data)


# ---------------------------------------------------------------- text files

MAX_TEXT_ENTRIES = 1000
MAX_MESSAGE_ENTRIES = 400


def _enc(s):
    return s.encode("cp1252", errors="replace")


def write_text_eng(path, groups):
    """groups: dict group_id -> list of strings (index order)."""
    data = bytearray()
    entries = []
    for g in range(MAX_TEXT_ENTRIES):
        strings = groups.get(g)
        if not strings:
            entries.append((0, 0))
            continue
        entries.append((len(data), 1))
        for s in strings:
            s = s if s else " "
            data += _enc(s) + b"\0"
    header = bytearray(28)
    struct.pack_into("<ii", header, 0, MAX_TEXT_ENTRIES, len(data))
    with open(path, "wb") as f:
        f.write(header)
        for off, used in entries:
            f.write(struct.pack("<ii", off, used))
        f.write(data)
    assert len(data) <= 200000, "text data too large"


def write_message_eng(path, messages):
    """messages: dict id -> dict(type, message_type, x, y, width_blocks, height_blocks,
    image: {id,x,y}|None, title_x, title_y, subtitle_x, subtitle_y, video_x, video_y,
    urgent, video, title, subtitle, content)."""
    data = bytearray(b"\0" * 8)  # offset 0 means "no text"

    def add(s):
        if not s:
            return 0
        off = len(data)
        data.extend(_enc(s) + b"\0")
        return off

    index = bytearray()
    for i in range(MAX_MESSAGE_ENTRIES):
        m = messages.get(i)
        e = bytearray(80)
        if m:
            img = m.get("image") or {}
            struct.pack_into("<hh", e, 0, m.get("type", 2), m.get("message_type", 0))
            struct.pack_into("<hhhh", e, 6, m.get("x", 0), m.get("y", 0),
                             m.get("width_blocks", 30), m.get("height_blocks", 20))
            struct.pack_into("<hhh", e, 14, img.get("id", 0), img.get("x", 0), img.get("y", 0))
            struct.pack_into("<hhhh", e, 26, m.get("title_x", 0), m.get("title_y", 0),
                             m.get("subtitle_x", 0), m.get("subtitle_y", 0))
            struct.pack_into("<hh", e, 38, m.get("video_x", 0), m.get("video_y", 0))
            struct.pack_into("<i", e, 56, m.get("urgent", 0))
            struct.pack_into("<i", e, 60, add(m.get("video")))
            struct.pack_into("<iii", e, 68, add(m.get("title")), add(m.get("subtitle")),
                             add(m.get("content")))
        index += e
    assert len(index) == 32000
    header = bytearray(24)
    struct.pack_into("<ii", header, 0, MAX_MESSAGE_ENTRIES, len(data))
    with open(path, "wb") as f:
        f.write(header)
        f.write(index)
        f.write(data)
    assert len(data) <= 460000, "message data too large"
