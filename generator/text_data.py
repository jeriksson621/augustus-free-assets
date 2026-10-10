"""Builds c3.eng / c3_mm.eng (+ editor copies) from the text specs."""
import json
import os

import formats

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.join(HERE, "specs")

# strings that the engine compares or requires verbatim
FORCED = {
    (1, 1): "New Game",  # core/locale.c language detection
    (9, 0): "Augustus",  # window title
}


def load_groups():
    groups = {}
    for name in ("text_a.json", "text_b.json"):
        path = os.path.join(SPECS, name)
        if not os.path.exists(path):
            continue
        for g, v in json.load(open(path)).items():
            if g.startswith("_"):
                continue
            n = int(v["count"])
            strings = v["strings"]
            groups[int(g)] = [strings.get(str(i), " ") or " " for i in range(n)]
    for (g, i), s in FORCED.items():
        lst = groups.setdefault(g, [])
        while len(lst) <= i:
            lst.append(" ")
        lst[i] = s
    # make sure every group from 0 up to the highest one exists (placeholders)
    top = max(groups) if groups else 0
    for g in range(top + 1):
        if g not in groups:
            groups[g] = [" "]
    # the patch check in game.c needs (2,6) distinct from (3,0)
    while len(groups[2]) < 7:
        groups[2].append("Difficulty")
    return groups


def load_messages():
    path = os.path.join(SPECS, "messages.json")
    msgs = {}
    free_from = 321
    if os.path.exists(path):
        data = json.load(open(path))
        free_from = data.get("_free_from", 321)
        for k, v in data.items():
            if k.startswith("_"):
                continue
            i = int(k)
            if i >= free_from:
                continue
            m = dict(v)
            img = m.get("image")
            m["image"] = img or {}
            msgs[i] = m
    # fill gaps below the Augustus range with a harmless placeholder
    for i in range(1, free_from):
        if i not in msgs:
            msgs[i] = {"type": 2, "message_type": 0, "x": 64, "y": 48, "width_blocks": 32, "height_blocks": 20,
                       "title": "Notice", "subtitle": " ", "content": "Nothing of note has happened."}
    return msgs


def write_all(out, starts):
    groups = load_groups()
    msgs = load_messages()
    for text, mm in (("c3.eng", "c3_mm.eng"), ("c3_map.eng", "c3_map_mm.eng")):
        formats.write_text_eng(os.path.join(out, text), groups)
        formats.write_message_eng(os.path.join(out, mm), msgs)
