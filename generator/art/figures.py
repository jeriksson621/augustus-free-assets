"""Procedural walker / animal / vehicle sprites.

Direction d (0..7) screen headings: 0 up-right, 1 right, 2 down-right, 3 down,
4 down-left, 5 left, 6 up-left, 7 up (from src/widget/city_figure.c offsets).
Every sprite returns (image, anchor_x, anchor_y) where the anchor is the feet position.
"""
import math

from PIL import Image, ImageDraw

from .core import rgb, shade, outline_alpha

from . import theme

SKIN = theme.T["skin"]
HAIR = theme.T["hair"]
THEME = theme.NAME

# unit heading vectors on screen (x right, y down)
HEAD = {
    0: (0.89, -0.45), 1: (1, 0), 2: (0.89, 0.45), 3: (0, 1),
    4: (-0.89, 0.45), 5: (-1, 0), 6: (-0.89, -0.45), 7: (0, -1),
}


def _canvas(w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def person(d, frame, tunic=(180, 40, 30), legs=None, skin=SKIN, hair=HAIR, item=None,
           item_color=(120, 80, 40), helmet=None, cloak=None, scale=1.0, state="walk", frames=12,
           shield=None, skirt=True):
    """Draw a person. state: walk | death | fight | stand | work."""
    if THEME == "steampunk":
        # darker Victorian coats, keep the role colour as a sash/accent
        tunic = tuple(int(c * 0.55 + 30) for c in tunic)
        legs = legs or (48, 42, 40)
        if item in ("sword", "spear"):
            item = "staff" if item == "spear" else item
        if shield:
            shield = (150, 120, 60)
    elif THEME == "stoneage":
        # fur and hide clothing, clubs and stone spears
        tunic = tuple(int(c * 0.25 + f * 0.75) for c, f in zip(tunic, (140, 100, 60)))
        legs = legs or skin
        if item == "sword":
            item = "tool"
        if shield:
            shield = (120, 90, 60)
    W, H = int(30 * scale) + 4, int(40 * scale) + 6
    img, dr = _canvas(W, H)
    s = scale
    cx = W // 2
    feet = H - 3
    hx, hy = HEAD[d]
    facing_away = d in (0, 6, 7)
    side = 1 if hx > 0.1 else (-1 if hx < -0.1 else 0)
    legs = legs or shade(tunic, 0.55)

    if state == "death":
        # body falls over progressively (frames 0..7), ends lying on the ground
        t = min(1.0, frame / max(1, frames - 1))
        ang = t * 85 * (1 if side >= 0 else -1)
        body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(body)
        _draw_upright(bd, cx, feet, s, tunic, legs, skin, hair, 0, side, facing_away, None, item_color,
                      helmet, cloak, shield, skirt)
        body = body.rotate(ang, center=(cx, feet), resample=Image.NEAREST)
        if t > 0.6:
            pool = ImageDraw.Draw(img)
            r = int(5 * s * t)
            pool.ellipse([cx - r * 2, feet - r // 2, cx + r * 2, feet + r // 2], fill=rgb((120, 10, 10)))
        img.alpha_composite(body)
        return outline_alpha(img), cx, feet

    phase = (frame % frames) / frames * 2 * math.pi
    swing = math.sin(phase) if state == "walk" else 0
    if state == "fight":
        swing = math.sin(phase) * 1.2
    _draw_upright(dr, cx, feet, s, tunic, legs, skin, hair, swing, side, facing_away, item, item_color,
                  helmet, cloak, shield, skirt, fighting=(state == "fight"), d=d, frame=frame)
    return outline_alpha(img), cx, feet


def _draw_upright(dr, cx, feet, s, tunic, legs, skin, hair, swing, side, away, item, item_color,
                  helmet, cloak, shield, skirt, fighting=False, d=3, frame=0):
    leg_len = 11 * s
    hip_y = feet - leg_len
    body_h = 12 * s
    shoulder_y = hip_y - body_h
    head_r = 3.6 * s
    head_y = shoulder_y - head_r - 0.5
    stride = 4 * s * swing
    lift = abs(swing) * 1.5 * s
    # legs
    if side:
        l1 = (cx + stride, feet)
        l2 = (cx - stride, feet - lift)
    else:
        l1 = (cx - 2 * s, feet - max(0, swing) * 2 * s)
        l2 = (cx + 2 * s, feet - max(0, -swing) * 2 * s)
    w = max(2, int(2.4 * s))
    dr.line([(cx - (1 if side else 1.5) * s, hip_y), l2], fill=rgb(shade(legs, 0.8)), width=w)
    dr.line([(cx + (0 if side else 1.5) * s, hip_y), l1], fill=rgb(legs), width=w)
    # cloak behind
    if cloak and not away:
        dr.polygon([(cx - 5 * s, shoulder_y + 1), (cx + 5 * s, shoulder_y + 1), (cx + 6 * s, hip_y + 4 * s),
                    (cx - 6 * s, hip_y + 4 * s)], fill=rgb(shade(cloak, 0.8)))
    # torso (tunic)
    bw = 5 * s
    bottom = hip_y + (4 * s if skirt else 0)
    dr.polygon([(cx - bw * 0.8, shoulder_y), (cx + bw * 0.8, shoulder_y), (cx + bw, bottom), (cx - bw, bottom)],
               fill=rgb(tunic))
    dr.line([(cx - bw * 0.8, shoulder_y + 1), (cx - bw, bottom)], fill=rgb(shade(tunic, 1.2)))
    dr.line([(cx + bw * 0.8, shoulder_y + 1), (cx + bw, bottom)], fill=rgb(shade(tunic, 0.7)))
    dr.line([(cx - bw * 0.7, hip_y - 1), (cx + bw * 0.7, hip_y - 1)], fill=rgb(shade(tunic, 0.6)))
    if cloak and away:
        dr.polygon([(cx - 5 * s, shoulder_y), (cx + 5 * s, shoulder_y), (cx + 6 * s, hip_y + 4 * s),
                    (cx - 6 * s, hip_y + 4 * s)], fill=rgb(cloak))
    # arms
    arm = 3.5 * s * swing
    a_w = max(2, int(2 * s))
    if fighting:
        ax = cx + (side or 1) * 8 * s
        ay = shoulder_y - 2 * s * (1 + swing)
        dr.line([(cx + (side or 1) * 3 * s, shoulder_y + 2), (ax, ay)], fill=rgb(skin), width=a_w)
    else:
        dr.line([(cx - 4 * s, shoulder_y + 1), (cx - 4.5 * s - arm * (side or 0.5), shoulder_y + 8 * s)],
                fill=rgb(shade(skin, 0.85)), width=a_w)
        dr.line([(cx + 4 * s, shoulder_y + 1), (cx + 4.5 * s + arm * (side or 0.5), shoulder_y + 8 * s)],
                fill=rgb(skin), width=a_w)
    # head
    dr.ellipse([cx - head_r, head_y - head_r, cx + head_r, head_y + head_r], fill=rgb(skin))
    if away:
        dr.ellipse([cx - head_r, head_y - head_r, cx + head_r, head_y + head_r * 0.6], fill=rgb(hair))
    else:
        dr.chord([cx - head_r, head_y - head_r, cx + head_r, head_y + head_r * 0.4], 180, 360, fill=rgb(hair))
        if side:
            ex = cx + side * head_r * 0.45
            dr.point((ex, head_y), fill=rgb((20, 20, 20)))
        else:
            dr.point((cx - 1.3 * s, head_y), fill=rgb((20, 20, 20)))
            dr.point((cx + 1.3 * s, head_y), fill=rgb((20, 20, 20)))
    if THEME == "steampunk":
        # top hat (or brass helmet for soldiers) and goggles
        if helmet:
            dr.chord([cx - head_r - 0.5, head_y - head_r - 1, cx + head_r + 0.5, head_y + head_r * 0.3], 180, 360,
                     fill=rgb((196, 150, 58)))
            dr.ellipse([cx - 1.5, head_y - head_r - 3 * s, cx + 1.5, head_y - head_r], fill=rgb((196, 150, 58)))
        else:
            dr.rectangle([cx - head_r - 1.5, head_y - head_r * 0.6, cx + head_r + 1.5, head_y - head_r * 0.6 + 1],
                         fill=rgb((30, 26, 24)))
            dr.rectangle([cx - head_r * 0.75, head_y - head_r * 0.6 - 6 * s, cx + head_r * 0.75,
                          head_y - head_r * 0.6], fill=rgb((30, 26, 24)))
            dr.line([(cx - head_r * 0.75, head_y - head_r * 0.6 - 1), (cx + head_r * 0.75, head_y - head_r * 0.6 - 1)],
                    fill=rgb((150, 40, 30)))
        if not away:
            dr.point((cx - 1.3 * s, head_y), fill=rgb((196, 150, 58)))
            dr.point((cx + 1.3 * s, head_y), fill=rgb((196, 150, 58)))
        helmet = None
    elif THEME == "stoneage":
        # wild hair, bone necklace, no metal helmets
        dr.chord([cx - head_r - 1, head_y - head_r - 1.5, cx + head_r + 1, head_y + head_r * 0.2], 180, 360,
                 fill=rgb(HAIR))
        dr.line([(cx - 3 * s, shoulder_y + 2), (cx + 3 * s, shoulder_y + 2)], fill=rgb((235, 228, 210)))
        helmet = None
    if helmet:
        dr.chord([cx - head_r - 0.5, head_y - head_r - 1, cx + head_r + 0.5, head_y + head_r * 0.3], 180, 360,
                 fill=rgb(helmet))
        dr.line([(cx, head_y - head_r - 3 * s), (cx, head_y - head_r)], fill=rgb((170, 20, 20)), width=2)
    # held item
    hand = (cx + (side or 1) * 5 * s, shoulder_y + 8 * s)
    if item == "bucket":
        dr.rectangle([hand[0] - 2 * s, hand[1], hand[0] + 2 * s, hand[1] + 3 * s], fill=rgb((150, 110, 60)))
        dr.line([(hand[0] - 1 * s, hand[1] + 1), (hand[0] + 1 * s, hand[1] + 1)], fill=rgb((60, 120, 220)))
    elif item == "scroll":
        dr.rectangle([hand[0] - 1, hand[1] - 3 * s, hand[0] + 2, hand[1] + 1], fill=rgb((235, 225, 190)))
    elif item == "staff":
        dr.line([(hand[0], hand[1] + 4 * s), (hand[0] + side, hand[1] - 16 * s)], fill=rgb(item_color), width=2)
    elif item == "spear":
        tip = (hand[0] + (side or 1) * (6 * s if fighting else 1), hand[1] - 18 * s)
        dr.line([(hand[0], hand[1] + 4 * s), tip], fill=rgb((110, 80, 50)), width=2)
        dr.polygon([tip, (tip[0] - 2, tip[1] + 4), (tip[0] + 2, tip[1] + 4)], fill=rgb((200, 200, 210)))
    elif item == "sword":
        tip = (hand[0] + (side or 1) * 7 * s, hand[1] - 6 * s - (6 * s if fighting else 0))
        dr.line([hand, tip], fill=rgb((210, 210, 220)), width=2)
    elif item == "basket":
        dr.ellipse([hand[0] - 3 * s, hand[1] - 1, hand[0] + 3 * s, hand[1] + 4 * s], fill=rgb(item_color))
    elif item == "tool":
        dr.line([(hand[0], hand[1] + 3 * s), (hand[0] + (side or 1) * 3, hand[1] - 9 * s)],
                fill=rgb((110, 80, 50)), width=2)
        dr.rectangle([hand[0] + (side or 1) * 3 - 2, hand[1] - 11 * s, hand[0] + (side or 1) * 3 + 2,
                      hand[1] - 9 * s], fill=rgb((150, 150, 160)))
    elif item == "bag":
        dr.ellipse([hand[0] - 3 * s, hand[1] - 2 * s, hand[0] + 3 * s, hand[1] + 4 * s], fill=rgb(item_color))
    elif item == "torch":
        dr.line([hand, (hand[0], hand[1] - 8 * s)], fill=rgb((100, 70, 40)), width=2)
        dr.ellipse([hand[0] - 2, hand[1] - 12 * s, hand[0] + 2, hand[1] - 7 * s], fill=rgb((250, 180, 40)))
    if shield:
        sx = cx - (side or -1) * 4 * s
        dr.rounded_rectangle([sx - 3.5 * s, shoulder_y + 1, sx + 3.5 * s, hip_y + 3 * s], radius=2,
                             fill=rgb(shield), outline=rgb(shade(shield, 0.5)))
        dr.point((sx, (shoulder_y + hip_y) / 2 + 1), fill=rgb((230, 200, 60)))


def animal(kind, d, frame, state="walk", frames=12):
    colors = {
        "sheep": ((235, 232, 220), (60, 50, 40), 1.0),
        "wolf": ((120, 115, 110), (70, 65, 60), 1.0),
        "zebra": ((240, 240, 240), (30, 30, 30), 1.15),
        "lion": ((200, 150, 70), (140, 90, 30), 1.3),
        "horse": ((120, 80, 50), (60, 40, 25), 1.4),
    }
    body, dark, s = colors.get(kind, colors["sheep"])
    W, H = int(40 * s), int(30 * s) + 4
    img, dr = _canvas(W, H)
    cx, feet = W // 2, H - 3
    hx, hy = HEAD[d]
    side = 1 if hx > 0.1 else (-1 if hx < -0.1 else 0)
    phase = (frame % frames) / frames * 2 * math.pi
    swing = math.sin(phase) if state == "walk" else 0
    if state == "death":
        t = min(1.0, frame / max(1, frames - 1))
        dr.ellipse([cx - 10 * s, feet - 6 * s, cx + 10 * s, feet], fill=rgb(body))
        dr.ellipse([cx + 7 * s, feet - 6 * s, cx + 12 * s, feet - 1], fill=rgb(dark))
        if t > 0.5:
            dr.ellipse([cx - 12 * s, feet - 2, cx + 12 * s, feet + 2], fill=rgb((120, 10, 10)))
        return outline_alpha(img), cx, feet
    # body length along the heading
    bl = 9 * s * (abs(hx) * 0.9 + 0.35)
    by = feet - 8 * s
    leg = 6 * s
    for i, off in enumerate((-bl * 0.7, bl * 0.7)):
        sw = swing * (1 if i == 0 else -1) * 2.5 * s
        dr.line([(cx + off * (side or 0.3), by), (cx + off * (side or 0.3) + sw, feet)], fill=rgb(dark), width=2)
        dr.line([(cx + off * (side or 0.3) + 2, by), (cx + off * (side or 0.3) + 2 - sw, feet)],
                fill=rgb(shade(dark, 0.8)), width=2)
    dr.ellipse([cx - bl - 3 * s, by - 5 * s, cx + bl + 3 * s, by + 3 * s], fill=rgb(body))
    if kind == "zebra":
        for k in range(-3, 4):
            x = cx + k * 3 * s
            dr.line([(x, by - 4 * s), (x + 1, by + 2 * s)], fill=rgb(dark))
    head_x = cx + (side if side else 0) * (bl + 3 * s)
    head_y = by - (6 * s if hy >= 0 else 7 * s)
    dr.ellipse([head_x - 3 * s, head_y - 3 * s, head_x + 3 * s, head_y + 3 * s],
               fill=rgb(dark if kind in ("sheep",) else body))
    if kind == "lion":
        dr.ellipse([head_x - 4.5 * s, head_y - 4.5 * s, head_x + 4.5 * s, head_y + 4.5 * s],
                   fill=rgb(shade(dark, 0.9)))
        dr.ellipse([head_x - 2.5 * s, head_y - 2.5 * s, head_x + 2.5 * s, head_y + 2.5 * s], fill=rgb(body))
    return outline_alpha(img), cx, feet


def cart(d, load_color=None, load_kind=None, width=24):
    """Two-wheeled hand cart, optional load (pile of resource colour)."""
    W, H = 34, 26
    img, dr = _canvas(W, H)
    hx, hy = HEAD[d]
    cx, cy = W // 2, H - 8
    # cart box drawn as small iso box oriented along heading
    ax, ay = hx * 8, hy * 5
    bx, by = -hy * 6, hx * 3
    corners = [(cx + ax + bx, cy + ay + by), (cx + ax - bx, cy + ay - by),
               (cx - ax - bx, cy - ay - by), (cx - ax + bx, cy - ay + by)]
    top = [(x, y - 5) for x, y in corners]
    dr.polygon(corners, fill=rgb((110, 75, 40)))
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        dr.polygon([a, b, top[(i + 1) % 4], top[i]], fill=rgb((150 - i * 10, 100 - i * 6, 55)))
    dr.polygon(top, fill=rgb((90, 60, 30)))
    if load_color:
        tcx = sum(p[0] for p in top) / 4
        tcy = sum(p[1] for p in top) / 4
        dr.ellipse([tcx - 7, tcy - 6, tcx + 7, tcy + 2], fill=rgb(load_color))
        dr.ellipse([tcx - 4, tcy - 8, tcx + 3, tcy - 2], fill=rgb(shade(load_color, 1.2)))
    # wheels
    for sgn in (1, -1):
        wx, wy = cx + sgn * bx * 1.2, cy + sgn * by * 1.2 + 2
        dr.ellipse([wx - 3, wy - 4, wx + 3, wy + 4], fill=rgb((70, 45, 20)), outline=rgb((40, 25, 10)))
    return outline_alpha(img), cx, cy + 4


def ship(d, kind="trade", frame=0):
    W, H = 64, 52
    img, dr = _canvas(W, H)
    hx, hy = HEAD[d]
    cx, cy = W // 2, H - 14
    L = 22
    ax, ay = hx * L, hy * L * 0.5
    bx, by = -hy * 7, hx * 3.5
    hull = [(cx + ax, cy + ay), (cx - ax * 0.6 + bx, cy - ay * 0.6 + by), (cx - ax + bx * 0.6, cy - ay + by * 0.6),
            (cx - ax - bx * 0.6, cy - ay - by * 0.6), (cx - ax * 0.6 - bx, cy - ay * 0.6 - by)]
    col = {"trade": (120, 80, 40), "fishing": (140, 100, 50), "war": (90, 50, 30)}.get(kind, (120, 80, 40))
    dr.polygon([(x, y + 4) for x, y in hull], fill=rgb(shade(col, 0.6)))
    dr.polygon(hull, fill=rgb(col))
    if kind != "fishing" or True:
        mx, my = cx - ax * 0.1, cy - ay * 0.1
        dr.line([(mx, my), (mx, my - 26)], fill=rgb((80, 55, 30)), width=2)
        sail = (235, 225, 200) if kind != "war" else (170, 40, 30)
        dr.polygon([(mx - 9 - bx * 0.3, my - 24), (mx + 9 + bx * 0.3, my - 24), (mx + 8, my - 8), (mx - 8, my - 8)],
                   fill=rgb(sail))
    if kind == "war":
        for k in range(-2, 3):
            ox, oy = cx + ax * k / 5, cy + ay * k / 5
            dr.line([(ox, oy), (ox + bx * 1.8, oy + by * 1.8 + 4)], fill=rgb((60, 40, 20)))
    return outline_alpha(img), cx, cy
