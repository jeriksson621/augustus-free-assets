"""User-interface images: panels, buttons, icons, backgrounds, portraits, empire map."""
import math
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import formats
from .core import rgb, shade, mix, seeded, outline_alpha, new
from . import fonts, terrain

BITMAPS = ["placeholder.bmp"]

PARCHMENT = (222, 200, 150)
STONE_UI = (146, 132, 108)
BRONZE = (176, 128, 64)
DARK = (48, 36, 24)
GOLD = (214, 172, 66)
RED = (170, 40, 30)
SEA = (52, 98, 150)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def bitmap_id(name):
    if name not in BITMAPS:
        BITMAPS.append(name)
    return BITMAPS.index(name)


# --------------------------------------------------------------- textures

def periodic_noise(x, y, period, scale, seed):
    """Smooth value noise that repeats every `period` pixels."""
    cells = max(1, int(round(period / scale)))
    xs, ys = x / period * cells, y / period * cells
    x0, y0 = int(math.floor(xs)), int(math.floor(ys))
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def h(i, j):
        return terrain.noise2(i % cells, j % cells, seed)
    a, b, c, d = h(x0, y0), h(x0 + 1, y0), h(x0, y0 + 1), h(x0 + 1, y0 + 1)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def seamless_texture(w, h, base, period, seed=0, strength=0.22, grain=0.06):
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = periodic_noise(x, y, period, 20, seed) * 0.6 + periodic_noise(x, y, period, 6, seed + 1) * 0.4
            g = terrain.noise2(x % period, y % period, seed + 2) - 0.5
            px[x, y] = rgb(shade(base, 1 - strength / 2 + t * strength + g * grain))
    return img


def texture(w, h, base, seed=0):
    return seamless_texture(w, h, base, max(w, h), seed)


def bevel(img, light=1.3, dark=0.55, width=2, box=None):
    px = img.load()
    x0, y0, x1, y1 = box or (0, 0, img.width, img.height)
    for i in range(width):
        f_l = light - (light - 1) * i / width
        f_d = dark + (1 - dark) * i / width
        for x in range(x0 + i, x1 - i):
            px[x, y0 + i] = rgb(shade(px[x, y0 + i][:3], f_l))
            px[x, y1 - 1 - i] = rgb(shade(px[x, y1 - 1 - i][:3], f_d))
        for y in range(y0 + i, y1 - i):
            px[x0 + i, y] = rgb(shade(px[x0 + i, y][:3], f_l))
            px[x1 - 1 - i, y] = rgb(shade(px[x1 - 1 - i, y][:3], f_d))
    return img


def frame_border(img, color=DARK):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width - 1, img.height - 1], outline=rgb(color))
    return img


# --------------------------------------------------------------- icons

def _font(size):
    return ImageFont.truetype(FONT_PATH, size)


def icon(name, size, color=None):
    """Return an RGBA pictogram of the named thing, roughly size x size."""
    s = size
    img = new(s, s)
    d = ImageDraw.Draw(img)
    c = color

    def E(x0, y0, x1, y1, col, **kw):
        d.ellipse([x0 * s, y0 * s, x1 * s, y1 * s], fill=rgb(col), **kw)

    def R(x0, y0, x1, y1, col):
        d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=rgb(col))

    def P(pts, col):
        d.polygon([(x * s, y * s) for x, y in pts], fill=rgb(col))

    def L(pts, col, w=1):
        d.line([(x * s, y * s) for x, y in pts], fill=rgb(col), width=max(1, int(w * s / 24)))

    n = name
    if n in ("wheat", "grain", "crops", "food"):
        for k in range(4):
            x = 0.3 + k * 0.13
            L([(x, 0.9), (x + 0.05, 0.3)], (150, 120, 40), 2)
            E(x - 0.02, 0.15, x + 0.12, 0.45, c or (226, 190, 70))
    elif n in ("vegetables", "vegetable"):
        E(0.15, 0.4, 0.55, 0.85, (230, 120, 40))
        E(0.45, 0.35, 0.85, 0.85, (120, 170, 60))
        L([(0.35, 0.4), (0.3, 0.15)], (60, 140, 40), 3)
    elif n == "fruit":
        E(0.15, 0.35, 0.55, 0.8, (210, 40, 40))
        E(0.45, 0.3, 0.85, 0.75, (240, 170, 40))
        L([(0.35, 0.35), (0.4, 0.15)], (90, 60, 30), 2)
    elif n in ("olives", "olive"):
        for (x, y) in ((0.3, 0.4), (0.5, 0.55), (0.6, 0.3), (0.35, 0.65)):
            E(x - 0.1, y - 0.13, x + 0.1, y + 0.13, (90, 110, 50))
        L([(0.15, 0.2), (0.85, 0.8)], (70, 100, 40), 2)
    elif n in ("vines", "grapes", "grape"):
        for (x, y) in ((0.4, 0.35), (0.6, 0.35), (0.5, 0.5), (0.35, 0.55), (0.65, 0.55), (0.5, 0.7)):
            E(x - 0.1, y - 0.1, x + 0.1, y + 0.1, (100, 50, 130))
        L([(0.5, 0.25), (0.55, 0.08)], (70, 100, 40), 2)
    elif n == "meat":
        E(0.15, 0.25, 0.75, 0.75, (180, 70, 60))
        E(0.3, 0.35, 0.6, 0.6, (230, 170, 160))
        L([(0.7, 0.6), (0.9, 0.85)], (240, 240, 230), 3)
    elif n == "fish":
        P([(0.1, 0.5), (0.4, 0.3), (0.75, 0.5), (0.4, 0.7)], (120, 150, 190))
        P([(0.72, 0.5), (0.92, 0.32), (0.92, 0.68)], (100, 130, 170))
        E(0.22, 0.44, 0.28, 0.5, (20, 20, 20))
    elif n in ("wine", "amphora"):
        P([(0.4, 0.15), (0.6, 0.15), (0.75, 0.45), (0.6, 0.9), (0.4, 0.9), (0.25, 0.45)], c or (150, 60, 50))
        L([(0.38, 0.25), (0.28, 0.35)], (120, 50, 40), 2)
        L([(0.62, 0.25), (0.72, 0.35)], (120, 50, 40), 2)
    elif n in ("oil", "jar"):
        E(0.2, 0.3, 0.8, 0.9, (200, 170, 80))
        R(0.4, 0.12, 0.6, 0.35, (180, 150, 60))
    elif n in ("iron", "ore"):
        P([(0.15, 0.7), (0.3, 0.35), (0.6, 0.25), (0.85, 0.5), (0.7, 0.85)], (90, 90, 100))
        P([(0.3, 0.35), (0.6, 0.25), (0.55, 0.5)], (150, 150, 160))
    elif n in ("timber", "logs", "wood"):
        for k, y in enumerate((0.55, 0.35)):
            R(0.15, y, 0.85, y + 0.2, (140, 95, 50))
            E(0.75, y, 0.95, y + 0.2, (200, 160, 100))
    elif n == "clay":
        P([(0.15, 0.8), (0.3, 0.4), (0.7, 0.35), (0.85, 0.8)], (180, 100, 60))
    elif n == "marble":
        P([(0.15, 0.4), (0.5, 0.25), (0.85, 0.4), (0.5, 0.55)], (245, 245, 240))
        P([(0.15, 0.4), (0.5, 0.55), (0.5, 0.85), (0.15, 0.7)], (210, 210, 205))
        P([(0.5, 0.55), (0.85, 0.4), (0.85, 0.7), (0.5, 0.85)], (180, 180, 175))
    elif n in ("weapons", "sword"):
        L([(0.2, 0.85), (0.75, 0.15)], (200, 200, 215), 3)
        L([(0.25, 0.6), (0.45, 0.8)], (150, 110, 50), 3)
        if n == "weapons":
            E(0.45, 0.45, 0.9, 0.9, (170, 40, 30))
            E(0.62, 0.62, 0.73, 0.73, GOLD)
    elif n in ("furniture", "chair"):
        R(0.25, 0.15, 0.35, 0.85, (130, 80, 40))
        R(0.25, 0.5, 0.75, 0.6, (150, 95, 50))
        R(0.65, 0.5, 0.75, 0.85, (130, 80, 40))
    elif n in ("pottery", "vase"):
        P([(0.35, 0.15), (0.65, 0.15), (0.6, 0.3), (0.8, 0.55), (0.62, 0.9), (0.38, 0.9), (0.2, 0.55), (0.4, 0.3)],
          (200, 110, 60))
        L([(0.25, 0.55), (0.75, 0.55)], (40, 30, 20), 2)
    elif n in ("denarii", "coins", "money", "financial"):
        for (x, y) in ((0.35, 0.6), (0.6, 0.5), (0.45, 0.35)):
            E(x - 0.18, y - 0.13, x + 0.18, y + 0.13, GOLD, outline=rgb((140, 100, 30)))
    elif n in ("people", "population", "plebs"):
        for x in (0.3, 0.55, 0.75):
            E(x - 0.08, 0.2, x + 0.08, 0.36, (220, 170, 120))
            P([(x - 0.12, 0.85), (x - 0.08, 0.4), (x + 0.08, 0.4), (x + 0.12, 0.85)], c or (170, 60, 40))
    elif n in ("patrician",):
        E(0.42, 0.15, 0.58, 0.33, (220, 170, 120))
        P([(0.3, 0.9), (0.4, 0.38), (0.6, 0.38), (0.7, 0.9)], (245, 240, 230))
        L([(0.4, 0.4), (0.62, 0.9)], (130, 40, 120), 2)
    elif n in ("labor", "workers", "hammer"):
        L([(0.25, 0.85), (0.6, 0.35)], (130, 90, 50), 3)
        R(0.5, 0.18, 0.8, 0.38, (150, 150, 160))
    elif n in ("military", "helmet", "security"):
        P([(0.2, 0.7), (0.25, 0.35), (0.5, 0.18), (0.75, 0.35), (0.8, 0.7), (0.65, 0.7), (0.65, 0.45), (0.35, 0.45),
           (0.35, 0.7)], (200, 200, 210))
        L([(0.5, 0.18), (0.5, 0.05)], (190, 30, 30), 4)
    elif n in ("imperial", "eagle"):
        P([(0.5, 0.2), (0.62, 0.35), (0.95, 0.3), (0.65, 0.55), (0.55, 0.85), (0.45, 0.85), (0.35, 0.55), (0.05, 0.3),
           (0.38, 0.35)], GOLD)
    elif n in ("ratings", "column"):
        R(0.38, 0.25, 0.62, 0.8, (235, 230, 220))
        R(0.28, 0.18, 0.72, 0.26, (235, 230, 220))
        R(0.25, 0.8, 0.75, 0.88, (210, 205, 195))
        for x in (0.43, 0.5, 0.57):
            L([(x, 0.28), (x, 0.78)], (190, 185, 175), 1)
    elif n in ("trade", "ship"):
        P([(0.1, 0.6), (0.9, 0.6), (0.75, 0.8), (0.25, 0.8)], (130, 85, 45))
        L([(0.5, 0.6), (0.5, 0.12)], (90, 60, 30), 2)
        P([(0.5, 0.15), (0.8, 0.5), (0.5, 0.5)], (240, 230, 210))
    elif n in ("health", "snake", "doctor"):
        L([(0.5, 0.1), (0.5, 0.9)], (130, 90, 50), 3)
        for k in range(4):
            y = 0.2 + k * 0.17
            L([(0.35, y), (0.65, y + 0.08), (0.35, y + 0.16)], (60, 140, 60), 2)
    elif n in ("education", "scroll", "school", "briefing"):
        R(0.25, 0.2, 0.75, 0.8, (240, 225, 180))
        E(0.18, 0.12, 0.32, 0.3, (200, 180, 130))
        E(0.68, 0.7, 0.82, 0.88, (200, 180, 130))
        for k in range(4):
            L([(0.33, 0.33 + k * 0.11), (0.67, 0.33 + k * 0.11)], (90, 70, 50), 1)
    elif n in ("entertainment", "mask", "theater"):
        E(0.18, 0.15, 0.82, 0.85, (240, 220, 160))
        E(0.32, 0.35, 0.44, 0.45, (40, 30, 20))
        E(0.56, 0.35, 0.68, 0.45, (40, 30, 20))
        d.arc([0.3 * s, 0.45 * s, 0.7 * s, 0.75 * s], 20, 160, fill=rgb((40, 30, 20)), width=max(1, s // 16))
    elif n in ("religion", "temple"):
        P([(0.1, 0.35), (0.5, 0.12), (0.9, 0.35)], c or (240, 235, 225))
        for x in (0.2, 0.37, 0.54, 0.71):
            R(x, 0.38, x + 0.08, 0.78, (230, 225, 215))
        R(0.1, 0.78, 0.9, 0.88, (210, 205, 195))
    elif n in ("chief", "bust", "advisor"):
        E(0.33, 0.12, 0.67, 0.5, (230, 225, 215))
        P([(0.2, 0.9), (0.3, 0.55), (0.7, 0.55), (0.8, 0.9)], (230, 225, 215))
    elif n in ("exit", "return", "back", "arrow_back", "undo"):
        d.arc([0.2 * s, 0.25 * s, 0.8 * s, 0.85 * s], 200, 20, fill=rgb(c or (240, 230, 200)), width=max(2, s // 8))
        P([(0.08, 0.48), (0.32, 0.4), (0.25, 0.65)], c or (240, 230, 200))
    elif n in ("question", "help"):
        d.text((s * 0.3, s * 0.05), "?", font=_font(int(s * 0.8)), fill=rgb(c or (250, 240, 200)))
    elif n in ("close", "cancel", "x"):
        L([(0.25, 0.25), (0.75, 0.75)], c or (200, 30, 20), 4)
        L([(0.75, 0.25), (0.25, 0.75)], c or (200, 30, 20), 4)
    elif n in ("ok", "check", "start", "proceed"):
        L([(0.2, 0.55), (0.42, 0.78), (0.82, 0.25)], c or (40, 160, 40), 4)
    elif n in ("up",):
        P([(0.5, 0.2), (0.85, 0.75), (0.15, 0.75)], c or (240, 230, 200))
    elif n in ("down",):
        P([(0.5, 0.8), (0.85, 0.25), (0.15, 0.25)], c or (240, 230, 200))
    elif n in ("left",):
        P([(0.2, 0.5), (0.75, 0.15), (0.75, 0.85)], c or (240, 230, 200))
    elif n in ("right",):
        P([(0.8, 0.5), (0.25, 0.15), (0.25, 0.85)], c or (240, 230, 200))
    elif n in ("house", "housing"):
        P([(0.15, 0.5), (0.5, 0.2), (0.85, 0.5)], (180, 70, 50))
        R(0.25, 0.5, 0.75, 0.85, (230, 210, 170))
        R(0.45, 0.62, 0.57, 0.85, (90, 60, 40))
    elif n in ("water", "fountain", "aqueduct"):
        P([(0.5, 0.12), (0.78, 0.6), (0.5, 0.88), (0.22, 0.6)], (60, 130, 220))
        E(0.22, 0.42, 0.78, 0.88, (60, 130, 220))
        E(0.36, 0.5, 0.48, 0.62, (180, 220, 250))
    elif n in ("shovel", "clear"):
        L([(0.75, 0.1), (0.45, 0.55)], (130, 90, 50), 3)
        P([(0.3, 0.5), (0.55, 0.6), (0.4, 0.9), (0.2, 0.75)], (160, 160, 170))
    elif n in ("road", "roads"):
        P([(0.35, 0.1), (0.65, 0.1), (0.9, 0.9), (0.1, 0.9)], (170, 160, 140))
        for y in (0.3, 0.55, 0.8):
            L([(0.5, y - 0.08), (0.5, y + 0.05)], (240, 240, 230), 2)
    elif n in ("forum", "administration", "government", "senate"):
        P([(0.1, 0.35), (0.5, 0.15), (0.9, 0.35)], (200, 80, 50))
        for x in (0.2, 0.42, 0.64):
            R(x, 0.38, x + 0.14, 0.78, (230, 225, 210))
        R(0.1, 0.78, 0.9, 0.88, GOLD)
    elif n in ("industry", "commerce", "workshop"):
        icon_img = icon("amphora", s)
        img.alpha_composite(icon_img.resize((int(s * 0.7), int(s * 0.7))), (0, int(s * 0.3)))
        L([(0.55, 0.85), (0.85, 0.35)], (130, 90, 50), 3)
        R(0.75, 0.15, 0.95, 0.35, (150, 150, 160))
    elif n in ("engineering", "crane"):
        L([(0.3, 0.9), (0.3, 0.15), (0.85, 0.3)], (140, 100, 50), 3)
        L([(0.75, 0.28), (0.75, 0.65)], (60, 50, 40), 1)
        R(0.68, 0.65, 0.82, 0.78, (150, 150, 160))
    elif n in ("eye", "goto", "problem"):
        E(0.1, 0.3, 0.9, 0.7, (240, 240, 230))
        E(0.35, 0.33, 0.65, 0.67, (60, 110, 180))
        E(0.45, 0.43, 0.55, 0.57, (10, 10, 10))
    elif n in ("message", "messages", "letter"):
        R(0.15, 0.25, 0.85, 0.75, (240, 225, 180))
        L([(0.15, 0.25), (0.5, 0.55), (0.85, 0.25)], (120, 90, 60), 1)
        E(0.43, 0.48, 0.57, 0.62, RED)
    elif n in ("compass", "north"):
        E(0.1, 0.1, 0.9, 0.9, (220, 200, 150))
        P([(0.5, 0.15), (0.6, 0.5), (0.5, 0.85), (0.4, 0.5)], RED)
        d.text((s * 0.38, s * 0.02), "N", font=_font(max(6, int(s * 0.35))), fill=rgb(DARK))
    elif n in ("rotate_left", "ccw"):
        d.arc([0.15 * s, 0.15 * s, 0.85 * s, 0.85 * s], 40, 300, fill=rgb((240, 230, 200)), width=max(2, s // 8))
        P([(0.62, 0.05), (0.85, 0.25), (0.55, 0.32)], (240, 230, 200))
    elif n in ("rotate_right", "cw"):
        d.arc([0.15 * s, 0.15 * s, 0.85 * s, 0.85 * s], 240, 140, fill=rgb((240, 230, 200)), width=max(2, s // 8))
        P([(0.38, 0.05), (0.15, 0.25), (0.45, 0.32)], (240, 230, 200))
    elif n in ("globe", "empire", "map"):
        E(0.1, 0.1, 0.9, 0.9, SEA)
        P([(0.3, 0.25), (0.55, 0.2), (0.6, 0.45), (0.4, 0.55), (0.25, 0.45)], (110, 150, 70))
        P([(0.55, 0.6), (0.8, 0.55), (0.75, 0.8), (0.6, 0.8)], (170, 150, 80))
    elif n in ("grass",):
        for k in range(6):
            x = 0.15 + k * 0.13
            L([(x, 0.85), (x + 0.05, 0.35)], (80, 150, 50), 2)
    elif n in ("tree", "trees", "forest"):
        R(0.45, 0.55, 0.55, 0.9, (100, 70, 40))
        E(0.2, 0.1, 0.8, 0.65, (50, 120, 40))
    elif n in ("shrub",):
        E(0.15, 0.4, 0.85, 0.85, (70, 130, 50))
    elif n in ("rock", "rocks"):
        P([(0.1, 0.85), (0.3, 0.4), (0.55, 0.25), (0.85, 0.5), (0.9, 0.85)], (130, 125, 115))
    elif n in ("meadow",):
        icon_img = icon("grass", s)
        img.alpha_composite(icon_img)
        E(0.3, 0.3, 0.42, 0.42, (240, 220, 60))
        E(0.6, 0.4, 0.72, 0.52, (240, 240, 240))
    elif n in ("earthquake",):
        L([(0.5, 0.05), (0.4, 0.35), (0.6, 0.55), (0.45, 0.95)], (60, 40, 30), 4)
    elif n in ("elevation", "hill"):
        P([(0.05, 0.85), (0.4, 0.25), (0.6, 0.45), (0.75, 0.35), (0.95, 0.85)], (140, 120, 90))
    elif n in ("brush",):
        for r in (0.15, 0.3, 0.45):
            d.rectangle([(0.5 - r) * s, (0.5 - r) * s, (0.5 + r) * s, (0.5 + r) * s], outline=rgb((240, 230, 200)))
    elif n in ("native", "hut"):
        P([(0.15, 0.85), (0.5, 0.15), (0.85, 0.85)], (170, 130, 80))
        R(0.42, 0.6, 0.58, 0.85, (60, 40, 20))
    elif n in ("flag", "entry", "invasion", "herd", "points"):
        L([(0.3, 0.9), (0.3, 0.1)], (100, 70, 40), 2)
        P([(0.3, 0.1), (0.85, 0.25), (0.3, 0.42)], c or RED)
    elif n in ("lock",):
        d.arc([0.3 * s, 0.1 * s, 0.7 * s, 0.6 * s], 180, 360, fill=rgb((150, 120, 60)), width=max(2, s // 8))
        R(0.22, 0.4, 0.78, 0.9, BRONZE)
    elif n in ("bullet",):
        P([(0.5, 0.05), (0.95, 0.5), (0.5, 0.95), (0.05, 0.5)], BRONZE)
        P([(0.5, 0.25), (0.75, 0.5), (0.5, 0.75), (0.25, 0.5)], GOLD)
    elif n in ("sea_route",):
        icon_img = icon("ship", s)
        img.alpha_composite(icon_img)
    elif n in ("land_route", "camel", "caravan"):
        E(0.2, 0.35, 0.75, 0.65, (190, 150, 90))
        E(0.62, 0.15, 0.85, 0.38, (190, 150, 90))
        for x in (0.28, 0.4, 0.55, 0.67):
            L([(x, 0.6), (x, 0.92)], (150, 110, 60), 2)
    elif n in ("fort", "castle"):
        R(0.15, 0.4, 0.85, 0.85, (170, 160, 140))
        for x in (0.15, 0.4, 0.65):
            R(x, 0.3, x + 0.1, 0.4, (170, 160, 140))
        R(0.42, 0.6, 0.58, 0.85, (60, 40, 30))
    elif n in ("standard", "legion"):
        L([(0.5, 0.95), (0.5, 0.1)], (110, 80, 40), 2)
        R(0.3, 0.25, 0.7, 0.5, RED)
        E(0.4, 0.05, 0.6, 0.2, GOLD)
    elif n in ("swords", "battle"):
        L([(0.15, 0.85), (0.85, 0.15)], (210, 210, 220), 3)
        L([(0.85, 0.85), (0.15, 0.15)], (210, 210, 220), 3)
    else:
        E(0.2, 0.2, 0.8, 0.8, c or BRONZE)
    return img


ICON_WORDS = [
    ("wheat", "wheat"), ("vegetable", "vegetables"), ("fruit", "fruit"), ("olive", "olives"), ("vine", "vines"),
    ("grape", "vines"), ("meat", "meat"), ("fish", "fish"), ("wine", "wine"), ("oil", "oil"), ("iron", "iron"),
    ("timber", "timber"), ("clay", "clay"), ("marble", "marble"), ("weapon", "weapons"), ("furniture", "furniture"),
    ("pottery", "pottery"), ("denarii", "denarii"), ("coins", "denarii"), ("financial", "denarii"),
    ("labor", "labor"), ("military", "military"), ("imperial", "imperial"), ("ratings", "ratings"),
    ("trade", "trade"), ("population", "people"), ("health", "health"), ("education", "education"),
    ("entertainment", "entertainment"), ("religion", "religion"), ("temple", "religion"), ("chief", "chief"),
    ("return to city", "exit"), ("question", "help"), ("help", "help"), ("check", "ok"), ("ok ", "ok"),
    ("cancel", "close"), ("close", "close"), ("red x", "close"), ("scroll up", "up"), ("arrow up", "up"),
    ("scroll down", "down"), ("arrow down", "down"), ("housing", "house"), ("water", "water"),
    ("clear land", "shovel"), ("shovel", "shovel"), ("road", "road"), ("administration", "forum"),
    ("government", "forum"), ("industry", "industry"), ("security", "military"), ("engineering", "engineering"),
    ("undo", "undo"), ("eye", "eye"), ("problem", "eye"), ("start", "ok"), ("proceed", "ok"),
    ("message", "message"), ("north", "compass"), ("counter-clockwise", "rotate_left"),
    ("clockwise", "rotate_right"), ("briefing", "briefing"), ("advisors", "chief"), ("empire", "globe"),
    ("back", "exit"), ("expand sidebar", "left"), ("collapse sidebar", "right"), ("grass", "grass"),
    ("trees", "tree"), ("shrub", "shrub"), ("rocks", "rock"), ("meadow", "meadow"), ("earthquake", "earthquake"),
    ("elevation", "elevation"), ("brush", "brush"), ("native", "native"), ("entry/exit", "flag"),
    ("invasion", "flag"), ("herd", "flag"), ("attributes", "briefing"), ("requests", "briefing"),
    ("padlock", "lock"), ("bullet", "bullet"), ("patrician", "patrician"), ("plebeian", "people"),
    ("people", "people"), ("go to legion", "standard"), ("return to fort", "fort"), ("at fort", "fort"),
    ("empire service", "eagle"), ("getting goods", "right"),
]


def icon_for(desc):
    d = desc.lower()
    for word, name in ICON_WORDS:
        if word in d:
            return name
    return None


def state_of(desc):
    d = desc.lower()
    for s in ("disabled", "pressed", "selected", "hover", "focused", "highlight"):
        if s in d:
            return {"selected": "pressed", "focused": "hover", "highlight": "hover"}.get(s, s)
    return "normal"


def button(w, h, icon_name, state, base=STONE_UI, seed=0, icon_scale=0.8):
    col = base
    if state == "hover":
        col = shade(base, 1.18)
    elif state == "pressed":
        col = shade(base, 0.85)
    elif state == "disabled":
        col = mix(base, (128, 128, 128), 0.7)
    img = seamless_texture(w, h, col, max(w, h), seed + 7, strength=0.15)
    if state == "pressed":
        bevel(img, light=0.6, dark=1.3)
    else:
        bevel(img)
    frame_border(img)
    if icon_name:
        sz = int(min(w, h) * icon_scale)
        ic = icon(icon_name, sz)
        if state == "disabled":
            ic = ic.convert("LA").convert("RGBA")
        off = 1 if state == "pressed" else 0
        img.alpha_composite(ic, ((w - sz) // 2 + off, (h - sz) // 2 + off))
    return img


# --------------------------------------------------------------- panels

def panel_tiles(grid, inner=False, seed=0):
    """Render a grid x grid tiles (16px) panel, return list of tile images row-major."""
    size = grid * 16
    period = (grid - 2) * 16
    base = (64, 52, 40) if inner else PARCHMENT
    img = Image.new("RGBA", (size, size))
    fill = seamless_texture(period, period, base, period, seed, strength=0.18 if not inner else 0.25)
    for y in range(0, size, period):
        for x in range(0, size, period):
            img.paste(fill, (x + 16 - period if x == 0 else x - period + 16, y + 16 - period if y == 0 else y - period + 16))
    # simpler: tile the fill from (16,16)
    for y in range(-period, size, period):
        for x in range(-period, size, period):
            img.paste(fill, (16 + x, 16 + y))
    d = ImageDraw.Draw(img)
    if inner:
        # sunken: dark top/left, light bottom/right
        d.rectangle([0, 0, size - 1, size - 1], outline=rgb((24, 18, 12)))
        for i in range(1, 4):
            d.line([(i, i), (size - 1 - i, i)], fill=rgb(shade(base, 0.55 + i * 0.1)))
            d.line([(i, i), (i, size - 1 - i)], fill=rgb(shade(base, 0.55 + i * 0.1)))
            d.line([(i, size - 1 - i), (size - 1 - i, size - 1 - i)], fill=rgb(shade(base, 1.5 - i * 0.1)))
            d.line([(size - 1 - i, i), (size - 1 - i, size - 1 - i)], fill=rgb(shade(base, 1.5 - i * 0.1)))
    else:
        border = (120, 84, 46)
        for i in range(0, 7):
            f = 1.25 - i * 0.07 if i < 3 else 0.75 + (i - 3) * 0.08
            col = shade(border, f)
            d.rectangle([i, i, size - 1 - i, size - 1 - i], outline=rgb(col))
        d.rectangle([0, 0, size - 1, size - 1], outline=rgb((30, 20, 10)))
        d.rectangle([7, 7, size - 8, size - 8], outline=rgb(shade(PARCHMENT, 0.7)))
        # gold studs at the corners
        for (x, y) in ((3, 3), (size - 13, 3), (3, size - 13), (size - 13, size - 13)):
            d.ellipse([x + 2, y + 2, x + 8, y + 8], fill=rgb(GOLD), outline=rgb((110, 80, 30)))
    tiles = []
    for ty in range(grid):
        for tx in range(grid):
            tiles.append(img.crop((tx * 16, ty * 16, tx * 16 + 16, ty * 16 + 16)))
    return tiles


_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def label_piece(h, part, state):
    """Stone label pieces: part 0 left, 1 middle, 2 right (16 x h)."""
    base = {"normal": (170, 150, 112), "hover": (196, 176, 130), "dim": (140, 130, 112)}[state]
    img = seamless_texture(16, h, base, 16, 3, strength=0.12)
    d = ImageDraw.Draw(img)
    d.line([(0, 0), (15, 0)], fill=rgb(shade(base, 1.3)))
    d.line([(0, 1), (15, 1)], fill=rgb(shade(base, 1.15)))
    d.line([(0, h - 1), (15, h - 1)], fill=rgb(shade(base, 0.45)))
    d.line([(0, h - 2), (15, h - 2)], fill=rgb(shade(base, 0.7)))
    if part == 0:
        d.line([(0, 0), (0, h - 1)], fill=rgb(shade(base, 1.3)))
        d.line([(1, 1), (1, h - 2)], fill=rgb(shade(base, 1.15)))
        d.line([(0, 0), (0, h - 1)], fill=rgb((40, 30, 20)))
    if part == 2:
        d.line([(15, 0), (15, h - 1)], fill=rgb((40, 30, 20)))
        d.line([(14, 1), (14, h - 2)], fill=rgb(shade(base, 0.6)))
    d.line([(0, 0), (15, 0)], fill=rgb((40, 30, 20)))
    d.line([(0, h - 1), (15, h - 1)], fill=rgb((40, 30, 20)))
    return img


def border_piece(idx):
    """Bordered button pieces (transparent interior). order TL, T, TR, R, BR, B, BL, L."""
    focused = idx >= 8
    i = idx % 8
    col = (230, 190, 80) if focused else (120, 90, 50)
    img = new(16, 16)
    d = ImageDraw.Draw(img)
    c1, c2 = rgb(shade(col, 1.2)), rgb(shade(col, 0.6))
    if i in (0, 1, 2):
        d.line([(0, 0), (15, 0)], fill=c1)
        d.line([(0, 1), (15, 1)], fill=c2)
    if i in (4, 5, 6):
        d.line([(0, 15), (15, 15)], fill=c2)
        d.line([(0, 14), (15, 14)], fill=c1)
    if i in (0, 6, 7):
        d.line([(0, 0), (0, 15)], fill=c1)
        d.line([(1, 0), (1, 15)], fill=c2)
    if i in (2, 3, 4):
        d.line([(15, 0), (15, 15)], fill=c2)
        d.line([(14, 0), (14, 15)], fill=c1)
    # trim corners so pieces join cleanly
    if i == 0:
        d.rectangle([2, 2, 15, 15], fill=(0, 0, 0, 0))
    if i == 2:
        d.rectangle([0, 2, 13, 15], fill=(0, 0, 0, 0))
    if i == 4:
        d.rectangle([0, 0, 13, 13], fill=(0, 0, 0, 0))
    if i == 6:
        d.rectangle([2, 0, 15, 13], fill=(0, 0, 0, 0))
    return img


# --------------------------------------------------------------- scenes

def sky_gradient(w, h, top=(110, 160, 220), bottom=(230, 220, 190)):
    g = Image.new("RGBA", (1, 256))
    for y in range(256):
        g.putpixel((0, y), rgb(mix(top, bottom, y / 255)))
    return g.resize((w, h), Image.BILINEAR)


def hills(img, y0, amp, color, seed, step=0.006, layers=1):
    w, h = img.size
    d = ImageDraw.Draw(img)
    pts = [(0, h)]
    for x in range(0, w + 8, 8):
        t = terrain.smooth_noise(x * step * 100, 0, 37, seed) * 0.7 + terrain.smooth_noise(x * step * 100, 0, 9,
                                                                                            seed + 1) * 0.3
        pts.append((x, y0 - t * amp))
    pts.append((w, h))
    d.polygon(pts, fill=rgb(color))


def temple_silhouette(d, x, y, w, h, color, cols=6):
    d.rectangle([x, y - h * 0.12, x + w, y], fill=rgb(shade(color, 0.85)))
    for k in range(cols):
        cx = x + w * (k + 0.5) / cols
        d.rectangle([cx - w * 0.03, y - h * 0.8, cx + w * 0.03, y - h * 0.12], fill=rgb(color))
    d.rectangle([x - w * 0.03, y - h * 0.9, x + w * 1.03, y - h * 0.78], fill=rgb(color))
    d.polygon([(x - w * 0.05, y - h * 0.9), (x + w / 2, y - h * 1.25), (x + w * 1.05, y - h * 0.9)],
              fill=rgb(shade(color, 1.1)))


def city_scene(w, h, seed, theme="city"):
    """Painterly Roman landscape used for backgrounds and vignettes."""
    rnd = seeded("scene", seed, theme)
    sunset = theme in ("evening", "war")
    top = (90, 130, 200) if not sunset else (110, 70, 90)
    bottom = (240, 220, 180) if not sunset else (240, 160, 90)
    img = sky_gradient(w, h, top, bottom)
    d = ImageDraw.Draw(img)
    # sun / clouds
    sx, sy = rnd.uniform(0.6, 0.9) * w, rnd.uniform(0.12, 0.3) * h
    r = h * 0.06
    d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=rgb((255, 240, 190)))
    for _ in range(5):
        cx, cy = rnd.uniform(0, w), rnd.uniform(0.05, 0.35) * h
        for k in range(4):
            rr = rnd.uniform(0.02, 0.05) * w
            d.ellipse([cx + k * rr * 0.8 - rr, cy - rr * 0.5, cx + k * rr * 0.8 + rr, cy + rr * 0.5],
                      fill=rgb((250, 248, 240) if not sunset else (240, 190, 160)))
    hills(img, h * 0.55, h * 0.18, (120, 140, 150), seed + 1)
    hills(img, h * 0.65, h * 0.12, (100, 130, 80), seed + 2)
    if theme in ("sea", "city"):
        d.rectangle([0, h * 0.72, w, h], fill=rgb(SEA))
        for k in range(60):
            x, y = rnd.uniform(0, w), rnd.uniform(0.73, 1.0) * h
            d.line([(x, y), (x + rnd.uniform(5, 20), y)], fill=rgb((120, 170, 220)))
    hills(img, h * 0.78, h * 0.08, (90, 120, 60), seed + 3)
    # city on the near hill
    base_y = h * 0.74
    for k in range(rnd.randint(6, 12)):
        bx = rnd.uniform(0.05, 0.9) * w
        bw = rnd.uniform(0.04, 0.09) * w
        bh = rnd.uniform(0.04, 0.1) * h
        wall = rnd.choice([(232, 220, 190), (220, 200, 160), (240, 236, 226)])
        d.rectangle([bx, base_y - bh, bx + bw, base_y + h * 0.05], fill=rgb(wall))
        d.polygon([(bx - bw * 0.05, base_y - bh), (bx + bw / 2, base_y - bh - bh * 0.35),
                   (bx + bw * 1.05, base_y - bh)], fill=rgb((180, 80, 50)))
        for wx in range(3):
            d.rectangle([bx + bw * (0.15 + wx * 0.28), base_y - bh * 0.6, bx + bw * (0.27 + wx * 0.28),
                         base_y - bh * 0.35], fill=rgb((90, 60, 40)))
    temple_silhouette(d, w * rnd.uniform(0.3, 0.55), base_y - h * 0.02, w * 0.18, h * 0.22, (245, 240, 230))
    if theme == "war":
        for k in range(30):
            x = rnd.uniform(0, w)
            y = h * rnd.uniform(0.82, 0.95)
            d.line([(x, y), (x, y - h * 0.05)], fill=rgb((80, 60, 40)), width=2)
            d.polygon([(x, y - h * 0.05), (x + 8, y - h * 0.045), (x, y - h * 0.04)], fill=rgb(RED))
    d.rectangle([0, h * 0.92, w, h], fill=rgb((80, 110, 50)))
    img = img.filter(ImageFilter.SMOOTH)
    return img


def vignette(w, h, desc, seed):
    """Small framed picture with a themed icon in the foreground."""
    img = city_scene(w, h, seed, "city" if seed % 3 else "evening")
    name = icon_for(desc)
    if name:
        sz = int(min(w, h) * 0.55)
        img.alpha_composite(outline_alpha(icon(name, sz)), (w - sz - 6, h - sz - 6))
    bevel(img, width=2)
    frame_border(img)
    return img


def portrait(w, h, desc, seed):
    rnd = seeded("portrait", desc, seed)
    bg = rnd.choice([(120, 90, 60), (90, 100, 120), (110, 120, 80), (130, 100, 110)])
    img = seamless_texture(w, h, bg, max(w, h), seed)
    d = ImageDraw.Draw(img)
    d.ellipse([w * 0.05, h * 0.0, w * 0.95, h * 0.9], fill=rgb(shade(bg, 1.25)))
    dl = desc.lower()
    tunic = (170, 50, 40)
    for word, col in (("prefect", (180, 40, 30)), ("engineer", (210, 170, 60)), ("priest", (240, 236, 220)),
                      ("doctor", (240, 240, 240)), ("teacher", (70, 110, 70)), ("tax", (60, 70, 150)),
                      ("market", (200, 120, 160)), ("actor", (200, 60, 160)), ("gladiator", (150, 60, 40)),
                      ("criminal", (80, 70, 60)), ("barbarian", (110, 90, 60)), ("enemy", (110, 90, 60)),
                      ("native", (150, 110, 70)), ("legion", (180, 40, 30)), ("patrician", (240, 236, 226)),
                      ("camel", (190, 150, 90)), ("sheep", (235, 232, 220)), ("wolf", (120, 115, 110)),
                      ("ship", (130, 85, 45))):
        if word in dl:
            tunic = col
            break
    skin = rnd.choice([(220, 170, 125), (200, 150, 105), (180, 130, 90)])
    if any(k in dl for k in ("sheep", "wolf", "camel", "zebra", "lion", "horse")):
        d.ellipse([w * 0.15, h * 0.3, w * 0.85, h * 0.85], fill=rgb(tunic))
        d.ellipse([w * 0.5, h * 0.2, w * 0.9, h * 0.5], fill=rgb(shade(tunic, 0.8)))
    elif "ship" in dl or "boat" in dl:
        ic = icon("ship", int(w * 0.9))
        img.alpha_composite(ic, (int(w * 0.05), int(h * 0.3)))
    else:
        d.polygon([(w * 0.08, h), (w * 0.2, h * 0.68), (w * 0.8, h * 0.68), (w * 0.92, h)], fill=rgb(tunic))
        d.rectangle([w * 0.4, h * 0.5, w * 0.6, h * 0.7], fill=rgb(skin))
        d.ellipse([w * 0.27, h * 0.18, w * 0.73, h * 0.6], fill=rgb(skin))
        d.chord([w * 0.25, h * 0.14, w * 0.75, h * 0.48], 180, 360, fill=rgb((70, 45, 25)))
        d.ellipse([w * 0.37, h * 0.36, w * 0.43, h * 0.4], fill=rgb((30, 20, 10)))
        d.ellipse([w * 0.57, h * 0.36, w * 0.63, h * 0.4], fill=rgb((30, 20, 10)))
        d.line([(w * 0.44, h * 0.5), (w * 0.56, h * 0.5)], fill=rgb((120, 60, 50)))
        if any(k in dl for k in ("prefect", "legion", "soldier", "gladiator", "sentry", "javelin", "mounted")):
            d.chord([w * 0.24, h * 0.1, w * 0.76, h * 0.45], 180, 360, fill=rgb((190, 190, 200)))
            d.rectangle([w * 0.47, h * 0.02, w * 0.53, h * 0.15], fill=rgb(RED))
    bevel(img, width=2)
    frame_border(img)
    return img


def god_portrait(w, h, god, selected):
    colors = [(200, 170, 60), (60, 110, 180), (160, 120, 180), (170, 50, 40), (220, 120, 150)]
    syms = ["wheat", "water", "trade", "military", "fruit"]
    img = portrait(w, h, "god %d" % god, god)
    d = ImageDraw.Draw(img)
    d.rectangle([2, h - 26, w - 3, h - 3], fill=rgb(colors[god]))
    ic = icon(syms[god], 22)
    img.alpha_composite(ic, ((w - 22) // 2, h - 25))
    if selected:
        d.rectangle([0, 0, w - 1, h - 1], outline=rgb(GOLD), width=3)
    return img


def empire_map(w=2000, h=1000):
    """Procedural world map: central sea surrounded by land masses."""
    small = Image.new("RGBA", (w // 4, h // 4))
    px = small.load()
    sw, sh = small.size
    for y in range(sh):
        for x in range(sw):
            nx, ny = x / sw, y / sh
            # inland sea in the middle-south, ocean at far west
            sea = math.exp(-(((nx - 0.5) / 0.32) ** 2 + ((ny - 0.58) / 0.13) ** 2))
            sea += math.exp(-(((nx - 0.82) / 0.08) ** 2 + ((ny - 0.35) / 0.08) ** 2)) * 0.8
            sea += max(0, 0.12 - nx) * 6
            n = terrain.smooth_noise(x, y, 18, 4) * 0.6 + terrain.smooth_noise(x, y, 6, 5) * 0.4
            v = sea + (n - 0.5) * 0.7
            if v > 0.45:
                px[x, y] = rgb(shade(SEA, 0.9 + n * 0.2))
            else:
                elev = terrain.smooth_noise(x, y, 10, 9)
                if ny > 0.75 + (n - 0.5) * 0.1:
                    base = (206, 180, 120)  # desert south
                elif ny < 0.25:
                    base = (90, 120, 80)  # northern forests
                else:
                    base = (130, 150, 80)
                if elev > 0.72:
                    base = (150, 130, 110)
                px[x, y] = rgb(shade(base, 0.85 + n * 0.3))
    img = small.resize((w, h), Image.BICUBIC).filter(ImageFilter.SMOOTH_MORE)
    d = ImageDraw.Draw(img)
    rnd = seeded("empire")
    # mountain marks and trees
    for _ in range(500):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        c = img.getpixel((int(x), int(y)))
        if c[2] > c[1]:
            continue
        if rnd.random() < 0.4:
            d.polygon([(x - 8, y + 6), (x, y - 8), (x + 8, y + 6)], fill=rgb((120, 105, 90)),
                      outline=rgb((80, 70, 60)))
        else:
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=rgb((60, 100, 50)))
    # parchment tint and border
    tint = Image.new("RGBA", (w, h), (230, 210, 160, 50))
    img.alpha_composite(tint)
    return img


def mission_map(w, h, seed):
    img = seamless_texture(w, h, (220, 196, 146), 64, seed)
    d = ImageDraw.Draw(img)
    rnd = seeded("missionmap", seed)
    pts = [(0, h * 0.75)]
    for x in range(0, w + 20, 20):
        pts.append((x, h * (0.65 + 0.1 * terrain.smooth_noise(x, 0, 60, seed))))
    pts += [(w, h), (0, h)]
    d.polygon(pts, fill=rgb((130, 160, 190)))
    for _ in range(40):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h * 0.6)
        d.polygon([(x - 7, y + 5), (x, y - 7), (x + 7, y + 5)], outline=rgb((120, 90, 60)))
    d.rectangle([0, 0, w - 1, h - 1], outline=rgb((110, 80, 50)), width=4)
    return img


def column_part(part, color):
    if part == 0:  # capital
        img = new(48, 20)
        d = ImageDraw.Draw(img)
        d.rectangle([6, 8, 41, 13], fill=rgb(shade(color, 1.1)))
        d.ellipse([2, 4, 14, 16], fill=rgb(color))
        d.ellipse([34, 4, 46, 16], fill=rgb(color))
        d.rectangle([4, 0, 44, 5], fill=rgb(shade(color, 1.2)))
        return outline_alpha(img)
    if part == 1:
        img = new(26, 13)
        d = ImageDraw.Draw(img)
        d.rectangle([4, 0, 21, 12], fill=rgb(color))
        d.rectangle([4, 0, 8, 12], fill=rgb(shade(color, 1.25)))
        d.rectangle([17, 0, 21, 12], fill=rgb(shade(color, 0.7)))
        return img
    img = new(42, 24)
    d = ImageDraw.Draw(img)
    d.ellipse([0, 8, 41, 23], fill=rgb(shade(color, 0.8)))
    d.ellipse([2, 4, 39, 18], fill=rgb(color))
    return outline_alpha(img)


RESOURCE_ORDER = ["none", "wheat", "vegetables", "fruit", "olives", "vines", "meat", "wine", "oil", "iron",
                  "timber", "clay", "marble", "weapons", "furniture", "pottery", "denarii", "fish"]


# --------------------------------------------------------------- dispatch

def ui_image(gname, spec, off, e):
    if gname == "GROUP_FONT":
        return formats.Image("sprite", font_image(off))
    im = _ui_image(gname, spec, off, e)
    # large pictures go to external files to respect the 12.1 MB main data limit
    frequent = gname in ("GROUP_SIDE_PANEL", "GROUP_PANEL_WINDOWS_DESERT", "GROUP_TOP_MENU") or (
        gname == "GROUP_PANEL_WINDOWS" and off <= 13)
    if im.kind == "opaque" and not im.external and not frequent and im.img is not None and \
            im.img.width * im.img.height >= 4000:
        im.external = True
        im.bitmap_id = bitmap_id(gname.lower() + ".bmp")
    return im


def _num(v, default):
    return v if isinstance(v, int) and v > 0 else default


def _ui_image(gname, spec, off, e):
    w, h = _num(e.get("w"), 16), _num(e.get("h"), 16)
    kind = e.get("kind", "sprite")
    desc = e.get("desc", "")
    dl = desc.lower()
    ext = bool(e.get("external"))
    img = None

    if gname == "GROUP_FONT":
        return formats.Image("sprite", font_image(off))
    if gname == "GROUP_DIALOG_BACKGROUND":
        return formats.Image("opaque", cached("outer", lambda: panel_tiles(12, False, 1))[off])
    if gname == "GROUP_SUNKEN_TEXTBOX_BACKGROUND":
        return formats.Image("opaque", cached("inner", lambda: panel_tiles(7, True, 2))[off])
    if gname == "GROUP_BORDERED_BUTTON":
        return formats.Image("sprite", border_piece(off))
    if gname == "GROUP_PANEL_BUTTON":
        if off <= 8 or 40 <= off <= 48:
            base = 0 if off <= 8 else 40
            k = off - base
            state = ["normal", "hover", "dim"][k // 3]
            return formats.Image("opaque", label_piece(25 if base == 0 else 20, k % 3, state))
        if off == 37 or off == 39:
            s = 20 if off == 37 else 25
            im = new(s, s)
            dd = ImageDraw.Draw(im)
            dd.ellipse([1, 1, s - 2, s - 2], fill=rgb(BRONZE), outline=rgb((90, 60, 30)))
            dd.ellipse([s * 0.25, s * 0.2, s * 0.55, s * 0.45], fill=rgb(shade(BRONZE, 1.4)))
            return formats.Image("sprite", im)
        return formats.Image("opaque", label_piece(16, 1, "normal"))
    if gname == "GROUP_TOP_MENU":
        if off == 14:
            im = seamless_texture(w, h, (30, 24, 20), 40, 9, strength=0.2)
            bevel(im, light=0.6, dark=1.4, width=2)
            return formats.Image("opaque", im)
        im = cached("topbar", lambda: seamless_texture(192, 24, (150, 120, 80), 192, 4, strength=0.2))
        tile = im.crop(((off % 8) * 24, 0, (off % 8) * 24 + 24, 24))
        dd = ImageDraw.Draw(tile)
        dd.line([(0, 0), (23, 0)], fill=rgb((210, 180, 120)))
        dd.line([(0, 23), (23, 23)], fill=rgb((50, 36, 20)))
        dd.line([(0, 22), (23, 22)], fill=rgb((90, 66, 40)))
        return formats.Image("opaque", tile)
    if gname == "GROUP_SIDE_PANEL":
        im = seamless_texture(w, h, (124, 108, 86), 64, off, strength=0.25)
        dd = ImageDraw.Draw(im)
        dd.rectangle([0, 0, w - 1, h - 1], outline=rgb((40, 30, 20)))
        dd.line([(1, 0), (1, h)], fill=rgb((170, 150, 120)))
        if off in (2, 3, 4, 5):
            # decorative relief: carved laurel stripes
            for y in range(10, h, 40):
                dd.line([(6, y), (w - 6, y)], fill=rgb((90, 76, 60)))
                dd.line([(6, y + 1), (w - 6, y + 1)], fill=rgb((160, 140, 110)))
                if w > 60:
                    dd.ellipse([w / 2 - 8, y + 8, w / 2 + 8, y + 24], outline=rgb((90, 76, 60)), width=2)
        return formats.Image("opaque", im)
    if gname == "GROUP_RESOURCE_ICONS" or gname == "GROUP_EMPIRE_RESOURCES":
        name = RESOURCE_ORDER[off] if off < len(RESOURCE_ORDER) else "none"
        ic = outline_alpha(icon(name, 22)) if name != "none" else new(24, 24)
        im = new(24, 24)
        im.alpha_composite(ic.crop((0, 0, 24, 24)), (1, 1))
        if gname == "GROUP_EMPIRE_RESOURCES":
            bg = seamless_texture(24, 24, PARCHMENT, 24, off)
            bg.alpha_composite(im)
            return formats.Image("opaque", bg)
        return formats.Image("sprite", im)
    if gname == "GROUP_RATINGS_COLUMN":
        if off == 0:
            im = new(54, 20)
            dd = ImageDraw.Draw(im)
            dd.rectangle([0, 6, 53, 19], fill=rgb((200, 195, 185)), outline=rgb((90, 85, 75)))
            dd.rectangle([6, 0, 47, 7], fill=rgb((220, 215, 205)), outline=rgb((90, 85, 75)))
            return formats.Image("sprite", im)
        if off == 1:
            im = new(32, 1)
            for x in range(32):
                im.putpixel((x, 0), rgb(shade((236, 232, 222), 0.75 + 0.35 * abs(math.sin(x / 32 * math.pi * 3)))))
            return formats.Image("sprite", im)
        im = column_part(0, (236, 232, 222)).resize((66, 26))
        return formats.Image("sprite", im)
    if gname == "GROUP_POPULATION_GRAPH_BAR":
        im = Image.new("RGBA", (w, h))
        dd = ImageDraw.Draw(im)
        dd.rectangle([0, 0, w - 1, h - 1], fill=rgb((180, 60, 40)))
        if w > 3:
            dd.line([(0, 0), (0, h)], fill=rgb((230, 120, 90)))
            dd.line([(w - 1, 0), (w - 1, h)], fill=rgb((120, 30, 20)))
        return formats.Image("sprite", im)
    if gname == "GROUP_BULLET":
        return formats.Image("sprite", icon("bullet", 10))
    if gname == "GROUP_LABOR_PRIORITY_LOCK":
        return formats.Image("sprite", outline_alpha(icon("lock", 14)))
    if gname in ("GROUP_EMPIRE_CITY", "GROUP_EMPIRE_CITY_TRADE", "GROUP_EMPIRE_CITY_DISTANT_ROMAN",
                 "GROUP_EMPIRE_FOREIGN_CITY"):
        return formats.Image("sprite", empire_city_icon(gname, w, h))
    if gname in ("GROUP_EMPIRE_BATTLE", "GROUP_EMPIRE_ROMAN_ARMY", "GROUP_EMPIRE_ENEMY_ARMY"):
        name = {"GROUP_EMPIRE_BATTLE": "swords", "GROUP_EMPIRE_ROMAN_ARMY": "standard",
                "GROUP_EMPIRE_ENEMY_ARMY": "flag"}[gname]
        col = (40, 40, 40) if "ENEMY" in gname else None
        return formats.Image("sprite", outline_alpha(icon(name, min(w, h) - 2, col)))
    if gname == "GROUP_EMPIRE_TRADE_ROUTE_TYPE":
        return formats.Image("sprite", outline_alpha(icon("ship" if off == 0 else "land_route", min(w, h))).resize(
            (w, h)))
    if gname in ("GROUP_EMPIRE_TRADE_LAND", "GROUP_EMPIRE_TRADE_SEA"):
        im = new(5, 5)
        ImageDraw.Draw(im).ellipse([0, 0, 4, 4], fill=rgb((150, 80, 40) if "LAND" in gname else (30, 60, 140)))
        return formats.Image("sprite", im)
    if gname == "GROUP_EMPIRE_PANELS":
        if off in (0, 1, 2, 4, 5):
            im = seamless_texture(w, h, BRONZE, 86, off, strength=0.2)
            bevel(im)
            if off == 2:
                ImageDraw.Draw(im).ellipse([4, 4, 11, 11], fill=rgb(GOLD))
            return formats.Image("opaque", im)
        if off == 3:
            return formats.Image("opaque", bevel(seamless_texture(w, h, (120, 100, 76), 70, 3)))
        if off in (6, 7):
            im = outline_alpha(icon("eagle", 78))
            if off == 7:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            out = new(w, h)
            out.alpha_composite(im, ((w - im.width) // 2, h - im.height))
            return formats.Image("sprite", out)
        im = seamless_texture(w, h, PARCHMENT, 90, 8)
        bevel(im, width=3)
        frame_border(im)
        return formats.Image("sprite", im)
    if gname == "GROUP_EMPIRE_MAP":
        return formats.Image("opaque", cached("empire_map", lambda: empire_map(w, h)), external=True,
                             bitmap_id=bitmap_id("empire_map.bmp"))
    if gname == "GROUP_OVERLAY_COLUMN":
        pass
    if gname == "GROUP_BIG_PEOPLE":
        return formats.Image("opaque", portrait(w, h, desc, off))
    if gname == "GROUP_PANEL_WINDOWS" and 16 <= off <= 25:
        return formats.Image("opaque", god_portrait(w, h, (off - 16) % 5, off >= 21))
    if gname in ("GROUP_FORT_FORMATIONS",):
        im = button(w, h, None, "normal", seed=off)
        dd = ImageDraw.Draw(im)
        pts = formation_points(off)
        for (x, y) in pts:
            dd.ellipse([x * w - 2, y * h - 2, x * w + 2, y * h + 2], fill=rgb(RED))
        return formats.Image("opaque", im)
    if gname == "GROUP_SELECT_MISSION_BUTTON":
        im = new(44, 44)
        dd = ImageDraw.Draw(im)
        col = [(170, 40, 30), (230, 90, 50), (40, 140, 40)][off]
        dd.ellipse([4, 4, 39, 39], fill=rgb(col), outline=rgb(GOLD), width=3)
        if off == 2:
            im.alpha_composite(icon("ok", 30, (250, 250, 230)), (7, 7))
        return formats.Image("sprite", im)
    if gname == "GROUP_TRADE_AMOUNT":
        im = new(7, 7)
        ImageDraw.Draw(im).polygon([(0, 0), (6, 0), (6, 3), (3, 6), (0, 3)], fill=rgb(BRONZE), outline=rgb(DARK))
        return formats.Image("sprite", im)
    if gname == "GROUP_SELECT_MISSION":
        return formats.Image("opaque", mission_map(w, h, off), external=True, bitmap_id=bitmap_id("select_mission.bmp"))
    if gname in ("GROUP_MAIN_MENU_BACKGROUND", "GROUP_ADVISOR_BACKGROUND", "GROUP_SELECT_MISSION_BACKGROUND",
                 "GROUP_CCK_BACKGROUND", "GROUP_INTERMEZZO_BACKGROUND", "GROUP_LOGO"):
        variant = {"GROUP_MAIN_MENU_BACKGROUND": 1, "GROUP_ADVISOR_BACKGROUND": 2, "GROUP_SELECT_MISSION_BACKGROUND": 3,
                   "GROUP_CCK_BACKGROUND": 4, "GROUP_LOGO": 5}.get(gname, 10 + off % 6)
        theme = ["city", "sea", "evening", "city", "war", "city"][variant % 6]
        key = ("bg", variant, w, h)

        def make():
            im = city_scene(w, h, variant, theme)
            if gname == "GROUP_LOGO":
                dd = ImageDraw.Draw(im)
                f = _font(64)
                dd.text((w / 2 + 3, h * 0.2 + 3), "AUGUSTUS", font=f, fill=rgb((40, 20, 10)), anchor="mm")
                dd.text((w / 2, h * 0.2), "AUGUSTUS", font=f, fill=rgb(GOLD), anchor="mm")
            return formats.Image("opaque", im, external=True, bitmap_id=bitmap_id(gname.lower() + ".bmp"))
        return cached(key, make)
    if gname in ("GROUP_RATINGS_BACKGROUND", "GROUP_SCENARIO_IMAGE", "GROUP_MESSAGE_IMAGES", "GROUP_WIN_GAME_BACKGROUND",
                 "GROUP_LOADING_SCREEN", "GROUP_CONFIG") or (gname in ("GROUP_PANEL_WINDOWS",
                                                                       "GROUP_PANEL_WINDOWS_DESERT") and w >= 100):
        if gname == "GROUP_PANEL_WINDOWS" and off == 13:
            return formats.Image("opaque", bevel(seamless_texture(w, h, (120, 100, 76), 64, 13)))
        if gname == "GROUP_PANEL_WINDOWS" and off == 14:
            im = seamless_texture(w, h, PARCHMENT, 64, 14)
            dd = ImageDraw.Draw(im)
            for y in range(4, h, 20):
                dd.line([(8, y), (w - 8, y)], fill=rgb(shade(PARCHMENT, 0.8)))
            return formats.Image("opaque", im)
        im = vignette(w, h, desc, off * 3 + len(gname))
        if ext:
            return formats.Image("opaque", im, external=True, bitmap_id=bitmap_id(gname.lower() + ".bmp"))
        return formats.Image("opaque", im)

    # buttons and icons in general
    name = icon_for(desc)
    state = state_of(desc)
    if gname == "GROUP_ADVISOR_ICONS":
        state = "pressed" if off >= 13 else "normal"
    if kind == "opaque" or "button" in dl:
        base = STONE_UI
        if gname == "GROUP_ADVISOR_ICONS":
            base = (150, 120, 80)
        im = button(w, h, name, state, base=base, seed=off)
        if ext:
            return formats.Image("opaque", im, external=True, bitmap_id=bitmap_id(gname.lower() + ".bmp"))
        return formats.Image("opaque", im)
    # small sprite icons
    if gname == "GROUP_MESSAGE_ICON" and 14 <= off <= 17:
        im = new(w, h)
        col = RED if off in (16, 17) else (240, 225, 180)
        dd = ImageDraw.Draw(im)
        if off in (14, 16):
            dd.rectangle([2, 2, w - 3, h - 3], fill=rgb((240, 225, 180)), outline=rgb(DARK))
            dd.ellipse([w / 2 - 3, h / 2 - 3, w / 2 + 3, h / 2 + 3], fill=rgb(col if off == 16 else (170, 40, 30)))
        else:
            dd.rectangle([2, 4, w - 3, h - 3], fill=rgb((250, 240, 210)), outline=rgb(DARK))
            dd.line([(5, 7), (w - 6, 7)], fill=rgb(col if off == 17 else (110, 90, 60)))
        return formats.Image("sprite", im)
    if name:
        ic = outline_alpha(icon(name, min(w, h) - 2))
        im = new(w, h)
        im.alpha_composite(ic, ((w - ic.width) // 2, (h - ic.height) // 2))
        return formats.Image("sprite", im)
    im = seamless_texture(w, h, STONE_UI, max(w, h), off)
    bevel(im)
    return formats.Image("sprite" if kind == "sprite" else "opaque", im)


def formation_points(off):
    if off == 0:
        return [(0.5, 0.2 + 0.12 * k) for k in range(6)]
    if off == 1:
        return [(0.3 + 0.13 * (k % 4), 0.3 + 0.13 * (k // 4)) for k in range(12)]
    if off in (2, 5):
        rows = 2 if off == 2 else 1
        return [(0.15 + 0.14 * (k % 6), 0.4 + 0.18 * (k // 6)) for k in range(6 * rows)]
    if off in (3, 6):
        cols = 2 if off == 3 else 1
        return [(0.4 + 0.18 * (k // 6), 0.15 + 0.14 * (k % 6)) for k in range(6 * cols)]
    rnd = seeded("mop")
    return [(rnd.uniform(0.15, 0.85), rnd.uniform(0.15, 0.85)) for _ in range(10)]


def empire_city_icon(gname, w, h):
    im = new(w, h)
    d = ImageDraw.Draw(im)
    roof = {"GROUP_EMPIRE_CITY": (190, 50, 40), "GROUP_EMPIRE_CITY_TRADE": (200, 150, 50),
            "GROUP_EMPIRE_CITY_DISTANT_ROMAN": (130, 60, 120), "GROUP_EMPIRE_FOREIGN_CITY": (140, 110, 70)}[gname]
    if gname == "GROUP_EMPIRE_FOREIGN_CITY":
        for (x, y) in ((0.3, 0.7), (0.6, 0.75), (0.45, 0.5)):
            d.polygon([(x * w - 9, y * h), (x * w, y * h - 14), (x * w + 9, y * h)], fill=rgb(roof),
                      outline=rgb(DARK))
    else:
        d.rectangle([w * 0.15, h * 0.45, w * 0.85, h * 0.85], fill=rgb((210, 200, 180)), outline=rgb(DARK))
        for x in (0.15, 0.4, 0.65):
            d.rectangle([w * x, h * 0.38, w * (x + 0.12), h * 0.46], fill=rgb((210, 200, 180)), outline=rgb(DARK))
        d.polygon([(w * 0.3, h * 0.45), (w * 0.5, h * 0.25), (w * 0.7, h * 0.45)], fill=rgb(roof), outline=rgb(DARK))
        d.line([(w * 0.5, h * 0.25), (w * 0.5, h * 0.05)], fill=rgb(DARK), width=2)
        d.polygon([(w * 0.5, h * 0.05), (w * 0.72, h * 0.1), (w * 0.5, h * 0.16)], fill=rgb(roof))
    return outline_alpha(im)


_font_images = None


def font_image(off):
    global _font_images
    if _font_images is None:
        _font_images = fonts.all_font_images()
    if off < len(_font_images):
        return _font_images[off]
    return new(4, 2)


def arrow_images():
    """Absolute ids 15..22: up, up pressed, down, down pressed, left, left pressed, right, right pressed."""
    out = []
    for name in ("up", "down", "left", "right"):
        for st in ("normal", "pressed"):
            out.append(button(24, 24, name, st, seed=3))
    return out


# --------------------------------------------------------------- figure effects

def missile(desc, offset):
    d = desc.lower()
    ang = (offset % 16) / 16 * 2 * math.pi
    img = new(24, 24)
    dr = ImageDraw.Draw(img)
    L = 9 if "arrow" in d else 11
    dx, dy = math.cos(ang) * L, math.sin(ang) * L * 0.6
    dr.line([(12 - dx, 12 - dy), (12 + dx, 12 + dy)], fill=rgb((110, 80, 50)), width=2)
    dr.ellipse([12 + dx - 1.5, 12 + dy - 1.5, 12 + dx + 1.5, 12 + dy + 1.5], fill=rgb((200, 200, 210)))
    return img, 12, 12


def debris(desc, offset):
    img = new(30, 20)
    dr = ImageDraw.Draw(img)
    rnd = seeded("debris", offset)
    for _ in range(3):
        x, y = rnd.randint(4, 22), rnd.randint(4, 14)
        dr.rectangle([x, y, x + rnd.randint(4, 8), y + 2], fill=rgb((120, 80, 40)))
    return img, 15, 12


def effect_sprite(gname, desc, offset, e):
    w, h = max(4, e.get("w") or 24), max(4, e.get("h") or 24)
    img = new(w, h)
    dr = ImageDraw.Draw(img)
    rnd = seeded(gname, offset)
    if "EXPLOSION" in gname or "BOLT" in gname:
        for _ in range(8):
            x, y = rnd.uniform(0, w), rnd.uniform(0, h)
            r = rnd.uniform(2, w / 4)
            dr.ellipse([x - r, y - r, x + r, y + r], fill=rgb(rnd.choice([(250, 220, 80), (250, 140, 40),
                                                                           (255, 255, 200)])))
        return img, w // 2, h - 2
    if "SKULL" in gname:
        dr.ellipse([w * 0.2, h * 0.1, w * 0.8, h * 0.7], fill=rgb((235, 230, 210)))
        dr.ellipse([w * 0.3, h * 0.3, w * 0.45, h * 0.45], fill=rgb((20, 20, 20)))
        dr.ellipse([w * 0.55, h * 0.3, w * 0.7, h * 0.45], fill=rgb((20, 20, 20)))
        return img, w // 2, h - 2
    if "SEAGULL" in gname:
        x, y = w / 2, h / 2
        wing = math.sin(offset * 1.3) * 4
        dr.line([(x - 6, y - wing), (x, y), (x + 6, y - wing)], fill=rgb((245, 245, 245)), width=2)
        return img, w // 2, h // 2
    if "BALLISTA" in gname:
        dr.rectangle([w * 0.3, h * 0.5, w * 0.7, h * 0.8], fill=rgb((120, 80, 40)))
        dr.line([(w * 0.15, h * 0.45), (w * 0.85, h * 0.45)], fill=rgb((90, 60, 30)), width=3)
        return img, w // 2, h - 2
    if "FLAG" in gname or "STANDARD" in gname:
        dr.line([(w // 2, 0), (w // 2, h - 1)], fill=rgb((90, 70, 40)), width=2)
        if "ICON" in gname:
            dr.ellipse([w * 0.2, h * 0.2, w * 0.8, h * 0.8], fill=rgb(GOLD))
        else:
            t = math.sin(offset * 0.8) * 2
            dr.polygon([(w // 2, 1), (w - 2, 3 + t), (w // 2, h * 0.5)], fill=rgb(RED))
        return img, w // 2, h - 1
    if "WHIP" in gname:
        dr.line([(2, h - 2), (w - 2, 2 + (offset % 4))], fill=rgb((80, 50, 30)), width=1)
        return img, 2, h - 2
    dr.ellipse([2, 2, w - 2, h - 2], fill=rgb((200, 200, 200)))
    return img, w // 2, h - 2
