#!/usr/bin/env python3
"""Combine screenshots into one contact sheet: sheet.py OUT.png IMG... (scaled to half size)."""
import sys
from PIL import Image

out, files = sys.argv[1], sys.argv[2:]
cols = 2 if len(files) > 1 else 1
w, h = 640, 480
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), (0, 0, 0))
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    im.thumbnail((w, h))
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
