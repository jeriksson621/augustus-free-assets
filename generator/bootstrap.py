"""Smoke-test data: placeholder text and solid-colour images, to validate file formats."""
import os
import sys

from PIL import Image as PImage, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import formats  # noqa: E402
import model_txt  # noqa: E402

out = sys.argv[1]
os.makedirs(out, exist_ok=True)

groups = {}
for g in range(0, 200):
    n = 700 if g == 130 else 260 if g in (28, 41) else 100
    groups[g] = ["%d.%d" % (g, i) for i in range(n)]
groups[9] = ["Augustus test"] + groups[9][1:]
formats.write_text_eng(os.path.join(out, "c3.eng"), groups)
msgs = {i: {"type": 2, "title": "Msg %d" % i, "content": "Placeholder %d" % i} for i in range(1, 300)}
formats.write_message_eng(os.path.join(out, "c3_mm.eng"), msgs)
model_txt.write(os.path.join(out, "c3_model.txt"))


def sprite(w, h, col):
    im = PImage.new("RGBA", (w, h), col + (255,))
    return formats.Image("sprite", im)


def iso(tiles, col, top=0):
    w = 60 * tiles - 2
    h = 30 * tiles + top
    im = PImage.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(w // 2, h - 30 * tiles), (w - 1, h - 15 * tiles), (w // 2, h - 1), (0, h - 15 * tiles)],
              fill=col + (255,))
    return formats.Image("iso", im, tiles=tiles, has_top=top > 0)


images = [formats.Image()]
group_ids = [0] * 300
for g in range(1, 255):
    group_ids[g] = len(images)
    col = ((g * 53) % 256, (g * 97) % 256, (g * 151) % 256)
    count = 120 if g != 16 else 400
    for i in range(count):
        if g in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
            images.append(iso(1, col))
        else:
            images.append(sprite(12, 12, col))
    while 6145 <= len(images) <= 6192:
        images.append(formats.Image())
images[group_ids[81]].anim = {"num_sprites": 1}
images += [formats.Image()] * (formats.MAIN_ENTRIES - len(images))
images = images[:formats.MAIN_ENTRIES]
size = formats.write_sg2(os.path.join(out, "c3.sg2"), os.path.join(out, "c3.555"), images, group_ids,
                         ["placeholder.bmp"], formats.MAIN_ENTRIES)
print("main data", size)
enemy = [formats.Image()] + [sprite(10, 20, (200, 50, 50)) for _ in range(800)]
formats.write_sg2(os.path.join(out, "goths.sg2"), os.path.join(out, "goths.555"), enemy, [0] * 300,
                  ["enemy.bmp"], formats.ENEMY_ENTRIES)
