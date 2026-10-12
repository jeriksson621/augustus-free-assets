#!/usr/bin/env python3
"""Generate a complete, original Caesar III-compatible data set for Augustus.

usage: generate.py OUTPUT_DIR
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
if "--theme" in sys.argv:
    _i = sys.argv.index("--theme")
    os.environ["AUG_THEME"] = sys.argv[_i + 1]
    del sys.argv[_i:_i + 2]

import formats  # noqa: E402
import layout  # noqa: E402
import model_txt  # noqa: E402
from art import core, terrain, buildings, figures, fonts  # noqa: E402
from art import ui  # noqa: E402
import text_data  # noqa: E402
import scenario  # noqa: E402

SPECS = os.path.join(HERE, "specs")


def load_specs():
    groups = {}
    extra = {}
    for name in ("img_terrain.json", "img_buildings.json", "img_figures.json", "img_ui.json"):
        path = os.path.join(SPECS, name)
        if not os.path.exists(path):
            print("missing spec", name)
            continue
        data = json.load(open(path))
        for k, v in data.items():
            if k.startswith("_"):
                extra.setdefault(k, []).append(v)
                continue
            gid = v["id"]
            if gid in groups:
                # keep the larger definition
                if v["count"] <= groups[gid]["count"]:
                    continue
            v["name"] = k
            v["source"] = name
            groups[gid] = v
    return groups, extra


def entry_for(spec, offset):
    for e in spec["entries"]:
        if e["from"] <= offset <= e["to"]:
            return e
    return {"kind": "sprite", "w": 8, "h": 8, "desc": "unused", "from": offset, "to": offset}


# ------------------------------------------------------------------ figures

OUTFITS = {
    "GROUP_FIGURE_LABOR_SEEKER": dict(tunic=(150, 130, 100), item="staff"),
    "GROUP_FIGURE_BATHHOUSE_WORKER": dict(tunic=(70, 140, 200), item="bucket"),
    "GROUP_FIGURE_PRIEST": dict(tunic=(240, 236, 220), cloak=(200, 160, 60), item="staff"),
    "GROUP_FIGURE_ACTOR": dict(tunic=(200, 60, 160), item="scroll"),
    "GROUP_FIGURE_LION_TAMER": dict(tunic=(120, 80, 40), item="staff"),
    "GROUP_FIGURE_TAX_COLLECTOR": dict(tunic=(60, 70, 150), item="bag", item_color=(200, 170, 60)),
    "GROUP_FIGURE_SCHOOL_CHILD": dict(tunic=(220, 200, 120), item="scroll", scale=0.75),
    "GROUP_FIGURE_MARKET_LADY": dict(tunic=(200, 120, 160), item="basket", item_color=(170, 120, 60)),
    "GROUP_FIGURE_CARTPUSHER": dict(tunic=(140, 110, 70)),
    "GROUP_FIGURE_MIGRANT": dict(tunic=(160, 140, 110), item="bag", item_color=(140, 110, 80)),
    "GROUP_FIGURE_ENGINEER": dict(tunic=(220, 180, 60), item="tool"),
    "GROUP_FIGURE_GLADIATOR": dict(tunic=(150, 60, 40), helmet=(190, 190, 200), item="sword", shield=(160, 40, 30)),
    "GROUP_FIGURE_CRIMINAL": dict(tunic=(80, 70, 60), item="torch"),
    "GROUP_FIGURE_BARBER": dict(tunic=(230, 230, 230), item="tool"),
    "GROUP_FIGURE_PREFECT": dict(tunic=(190, 40, 30), helmet=(180, 180, 190), item="sword"),
    "GROUP_FIGURE_HOMELESS": dict(tunic=(120, 110, 100)),
    "GROUP_FIGURE_PREFECT_WITH_BUCKET": dict(tunic=(190, 40, 30), helmet=(180, 180, 190), item="bucket"),
    "GROUP_FIGURE_TOWER_SENTRY": dict(tunic=(150, 40, 30), helmet=(180, 180, 190), item="spear"),
    "GROUP_FIGURE_DELIVERY_BOY": dict(tunic=(200, 170, 110), item="basket", scale=0.8),
    "GROUP_FIGURE_DOCTOR_SURGEON": dict(tunic=(240, 240, 240), item="bag", item_color=(120, 70, 40)),
    "GROUP_FIGURE_PATRICIAN": dict(tunic=(245, 240, 230), cloak=(130, 40, 120)),
    "GROUP_FIGURE_MISSIONARY": dict(tunic=(110, 80, 50), item="staff"),
    "GROUP_FIGURE_TEACHER_LIBRARIAN": dict(tunic=(70, 110, 70), item="scroll"),
    "GROUP_FIGURE_CAESAR_LEGIONARY": dict(tunic=(120, 40, 120), helmet=(200, 200, 210), item="sword",
                                          shield=(120, 40, 120)),
    "GROUP_BUILDING_FORT_JAVELIN": dict(tunic=(170, 50, 30), helmet=(190, 190, 200), item="spear"),
    "GROUP_BUILDING_FORT_LEGIONARY": dict(tunic=(180, 40, 30), helmet=(200, 200, 210), item="sword",
                                          shield=(170, 40, 30)),
    "GROUP_FIGURE_FORT_MOUNTED": dict(tunic=(170, 50, 30), helmet=(190, 190, 200), item="spear"),
    "GROUP_FIGURE_CHARIOTEER": dict(tunic=(60, 120, 200), helmet=(200, 180, 60)),
}

ANIMAL = {"GROUP_FIGURE_SHEEP": "sheep", "GROUP_FIGURE_WOLF": "wolf", "GROUP_FIGURE_ZEBRA": "zebra",
          "GROUP_FIGURE_LION": "lion", "GROUP_FIGURE_HIPPODROME_HORSE_1": "horse",
          "GROUP_FIGURE_HIPPODROME_HORSE_2": "horse"}

RESOURCE_COLORS = [(200, 180, 60), (90, 150, 60), (200, 60, 60), (110, 130, 80), (90, 50, 110), (190, 120, 110),
                   (120, 70, 120), (180, 160, 60), (220, 220, 220), (90, 90, 100), (140, 100, 60), (170, 90, 60),
                   (150, 150, 160), (120, 80, 50), (180, 110, 70), (100, 160, 200)]


def classify_frame(desc, offset, e):
    """Return (state, direction, frame, frames) for a figure sprite from its description."""
    d = desc.lower()
    rel = offset - e["from"]
    if any(k in d for k in ("corpse", "dying", "death", "dead")):
        n = e["to"] - e["from"] + 1
        if "d + 8" in d or "+ d" in d:
            return "death", rel % 8, rel // 8, max(1, n // 8)
        return "death", 2, rel, n
    state = "walk"
    if any(k in d for k in ("fight", "attack", "melee", "throw", "shoot", "riot", "gesture")):
        state = "fight"
    if any(k in d for k in ("graz", "resting", "standing", "idle")):
        state = "stand"
    if "d + 8" in d or "+ d" in d or "direction" in d:
        m = re.search(r"frame\(0\.\.(\d+)\)", d)
        frames = int(m.group(1)) + 1 if m else 12
        return state, rel % 8, rel // 8, frames
    return state, rel % 8, rel // 8, 12


def figure_image(gname, offset, e):
    desc = e.get("desc", "")
    d = desc.lower()
    kind = None
    if gname in ANIMAL:
        kind = ANIMAL[gname]
    state, direction, frame, frames = classify_frame(desc, offset, e)
    if kind:
        img, ax, ay = figures.animal(kind, direction, frame, state=state if state != "fight" else "walk",
                                     frames=frames)
    elif "camel" in d:
        img, ax, ay = figures.animal("horse", direction, frame)
    elif gname in ("GROUP_FIGURE_CARTPUSHER_CART", "GROUP_FIGURE_CARTPUSHER_CART_MULTIPLE_FOOD",
                   "GROUP_FIGURE_CARTPUSHER_CART_MULTIPLE_RESOURCE", "GROUP_FIGURE_MIGRANT_CART",
                   "GROUP_FIGURE_TRADE_CARAVAN", "GROUP_FIGURE_HIPPODROME_CART_1", "GROUP_FIGURE_HIPPODROME_CART_2"):
        if gname == "GROUP_FIGURE_TRADE_CARAVAN" and "cart" not in d:
            img, ax, ay = figures.animal("horse", direction, frame)
        else:
            res = (offset // 8) % len(RESOURCE_COLORS)
            empty = "empty" in d and offset < 8
            img, ax, ay = figures.cart(offset % 8, None if empty else RESOURCE_COLORS[res])
    elif gname == "GROUP_FIGURE_SHIP":
        k = "fishing" if "fish" in d else "trade"
        if "war" in d:
            k = "war"
        img, ax, ay = figures.ship(offset % 8, k)
    elif gname in ("GROUP_FIGURE_MISSILE",):
        img, ax, ay = ui.missile(desc, offset)
    elif gname.startswith("GROUP_FIGURE_FLOTSAM") or gname == "GROUP_FIGURE_SHIPWRECK":
        img, ax, ay = ui.debris(desc, offset)
    elif gname in ("GROUP_FIGURE_EXPLOSION", "GROUP_GOD_BOLT", "GROUP_PLAGUE_SKULL", "GROUP_FIGURE_SEAGULLS",
                   "GROUP_FIGURE_FORT_FLAGS", "GROUP_FIGURE_FORT_STANDARD_ICONS", "GROUP_FIGURE_FORT_STANDARD_POLE",
                   "GROUP_FIGURE_MAP_FLAG_FLAGS", "GROUP_FIGURE_MAP_FLAG_ICONS", "GROUP_FIGURE_BALLISTA",
                   "GROUP_FIGURE_LION_TAMER_WHIP"):
        img, ax, ay = ui.effect_sprite(gname, desc, offset, e)
    else:
        outfit = dict(OUTFITS.get(gname, {}))
        if not outfit:
            col = buildings._word_color(d, (140, 120, 90))
            outfit = dict(tunic=col)
        if "mounted" in d or "horse" in d and "fort" in gname.lower():
            img, ax, ay = figures.animal("horse", direction, frame, state="walk" if state != "death" else "death")
        else:
            img, ax, ay = figures.person(direction, frame, state=state, frames=frames, **outfit)
    w, h = e.get("w"), e.get("h")
    return formats.Image("sprite", img, anim={"num_sprites": 1, "offset_x": ax, "offset_y": ay})


# ------------------------------------------------------------------ terrain

def terrain_image(gname, offset, e, clim):
    desc = e.get("desc", "")
    seed = offset * 7 + hash(gname) % 1000
    n = e.get("tiles") or 1
    if gname == "GROUP_TERRAIN_BLACK":
        return iso_img(terrain.flat_color_tile((0, 0, 0)))
    if gname == "GROUP_TERRAIN_SHRUB":
        return iso_img(terrain.shrub_tile(clim, offset))
    if gname == "GROUP_TERRAIN_UGLY_GRASS":
        c = terrain.CLIMATES[clim]
        return iso_img(terrain.textured_tile(core.mix(c["grass"], c["dirt"], 0.5), offset, blotch=0.3))
    if gname == "GROUP_TERRAIN_TREE":
        return iso_img(terrain.tree_tile(clim, offset, min(3, offset // 8)))
    if gname == "GROUP_TERRAIN_WATER":
        if offset < 8:
            return iso_img(terrain.water_tile(clim, offset % 6))
        return iso_img(terrain.shore_tile(clim, desc, offset))
    if gname == "GROUP_TERRAIN_WATER_SHORE":
        if "context" in desc or "land" in desc:
            d2 = desc
            m = re.search(r"land (along|only at) ([\w -]+?)(?:$|;|,)", desc)
            if m:
                d2 = "context: land (shore) at: " + m.group(2).replace(" and ", ", ")
            return iso_img(terrain.shore_tile(clim, d2, offset, fortified=True))
        return iso_img(terrain.water_tile(clim, 0))
    if gname == "GROUP_TERRAIN_EARTHQUAKE":
        return iso_img(terrain.chasm_tile(clim, desc, offset))
    if gname in ("GROUP_TERRAIN_GRASS_1", "GROUP_TERRAIN_GRASS_2"):
        kind = "grass" if gname.endswith("_1") else "grass2"
        if offset < 8:
            return iso_img(terrain.grass(clim, offset + (100 if kind == "grass2" else 0), kind=kind))
        # patches: 8..23 (2x2 x4), 24..41 (3x3 x2), 42..57 (4x4)
        if offset < 24:
            size, base, idx = 2, 8 + ((offset - 8) // 4) * 4, (offset - 8) % 4
        elif offset < 42:
            size, base, idx = 3, 24 + ((offset - 24) // 9) * 9, (offset - 24) % 9
        else:
            size, base, idx = 4, 42, offset - 42
        dy, dx = divmod(idx, size)
        world = (base * 97 + (dx - dy) * 30, base * 53 + (dx + dy) * 15)
        return iso_img(terrain.grass(clim, base, world=world, kind=kind))
    if gname in ("GROUP_TERRAIN_ELEVATION_ROCK", "GROUP_TERRAIN_ROCK"):
        return iso_img(terrain.rock_tile(clim, offset, n), top=True)
    if gname == "GROUP_TERRAIN_ELEVATION":
        return iso_img(terrain.cliff_tile(clim, desc, offset), top=True)
    if gname == "GROUP_BUILDING_WALL":
        return iso_img(terrain.wall_tile(desc, offset), top=True)
    if gname == "GROUP_TERRAIN_ROAD":
        return iso_img(terrain.road_tile(clim, desc, offset, paved=offset < 49))
    if gname == "GROUP_BUILDING_AQUEDUCT":
        return iso_img(terrain.aqueduct_tile(clim, desc, offset, water=offset < 15), top=True)
    if gname == "GROUP_TERRAIN_OVERLAY":
        block, part = divmod(offset, 4)
        cols = [(150, 140, 120), (170, 120, 100), (110, 140, 190), (140, 120, 170), (140, 190, 230), (160, 170, 210),
                (60, 110, 210), (90, 100, 200)]
        return iso_img(terrain.overlay_footprint_tile(cols[block % 8], part))
    if gname == "GROUP_TERRAIN_FLAT_TILE":
        return iso_img(terrain.flat_color_tile((255, 255, 255)))
    if gname == "GROUP_TERRAIN_PLAZA":
        return iso_img(terrain.plaza_tile(offset, n))
    if gname == "GROUP_TERRAIN_GARDEN":
        return iso_img(terrain.garden_tile(clim, offset, n))
    if gname == "GROUP_TERRAIN_MEADOW":
        return iso_img(terrain.meadow_tile(clim, offset, deep=offset >= 8))
    if gname == "GROUP_TERRAIN_DESIRABILITY":
        t = offset / 9
        col = core.mix((190, 30, 20), (40, 90, 220), t) if offset != 4 else (200, 200, 120)
        return iso_img(terrain.flat_color_tile(col, pattern=True))
    if gname == "GROUP_TERRAIN_ACCESS_RAMP":
        return iso_img(terrain.ramp_tile(clim, offset), top=True)
    if gname == "GROUP_TERRAIN_ENTRY_EXIT_FLAGS":
        col = (40, 160, 50) if offset < 4 else (190, 40, 30)
        return iso_img(terrain.flag_tile(clim, offset, col, offset % 4), top=True)
    if gname == "GROUP_OVERLAY_COLUMN":
        cols = [(70, 170, 70), (200, 200, 60), (230, 140, 40), (200, 50, 40)]
        return formats.Image("sprite", ui.column_part(offset % 3, cols[min(3, offset // 3)]))
    if gname == "GROUP_TERRAIN_RUBBLE":
        return iso_img(buildings.building("rubble collapsed ruin", 1, 6, offset, clim), top=True)
    return None


def iso_img(iso, top=False, anim=None):
    return formats.Image("iso", iso.img, tiles=iso.n, has_top=top or iso.rise > 0, anim=anim)


# ------------------------------------------------------------------ build

class Builder:
    def __init__(self, specs, starts):
        self.specs = specs
        self.starts = starts
        self.cache = {}

    def group_images(self, gid, clim):
        spec = self.specs[gid]
        gname = spec["name"]
        key = (gid, clim if self.climate_dependent(spec) else None)
        if key in self.cache:
            return self.cache[key]
        out = []
        anim_pending = {}
        for off in range(spec["count"]):
            e = entry_for(spec, off)
            try:
                im = self.paint(gname, spec, off, e, clim, out)
            except Exception as ex:  # keep going; report
                print("  paint error %s+%d: %s" % (gname, off, ex))
                im = formats.Image("sprite", core.new(4, 4, (255, 0, 255, 255)))
            out.append(im)
        self.fix_animation_offsets(spec, out)
        self.cache[key] = out
        return out

    def climate_dependent(self, spec):
        return spec["source"] in ("img_terrain.json", "img_buildings.json")

    def paint(self, gname, spec, off, e, clim, prior):
        src = spec["source"]
        kind = e.get("kind", "sprite")
        if src == "img_ui.json":
            return ui.ui_image(gname, spec, off, e)
        if src == "img_terrain.json":
            im = terrain_image(gname, off, e, clim)
            if im is not None:
                return im
        if src == "img_figures.json" or (kind == "sprite" and gname in ("GROUP_BUILDING_FORT_JAVELIN",
                                                                         "GROUP_BUILDING_FORT_LEGIONARY")):
            return figure_image(gname, off, e)
        # buildings and remaining terrain
        if kind == "iso":
            iso = buildings.building(e.get("desc", ""), e.get("tiles") or 1, e.get("top") or 0, off, clim, gname)
            anim = None
            if e.get("anim"):
                anim = dict(e["anim"])
                anim["_pending"] = True
            return formats.Image("iso", iso.img, tiles=iso.n, has_top=True, anim=anim)
        if kind == "sprite":
            w, h = max(1, e.get("w") or 20), max(1, e.get("h") or 20)
            idx = off - e["from"]
            total = e["to"] - e["from"] + 1
            img = buildings.frame_sprite(e.get("desc", ""), w, h, idx, total, off)
            return formats.Image("sprite", img)
        if kind == "opaque":
            return ui.ui_image(gname, spec, off, e)
        return formats.Image()

    def fix_animation_offsets(self, spec, images):
        """Place animation frames on their base image (canvas coordinates)."""
        for i, im in enumerate(images):
            a = im.anim
            if not a or not a.get("_pending"):
                continue
            a.pop("_pending")
            if "sprite_offset_x" in a:
                a["offset_x"] = a.pop("sprite_offset_x")
                a["offset_y"] = a.pop("sprite_offset_y", 0)
                continue
            n = a.get("num_sprites", 0)
            fw = fh = 0
            for k in range(1, n + 1):
                if i + k < len(images) and images[i + k].img is not None:
                    fw = max(fw, images[i + k].img.width)
                    fh = max(fh, images[i + k].img.height)
            W, H = im.img.size
            a["offset_x"] = max(0, (W - fw) // 2)
            a["offset_y"] = max(0, min(H - fh, (H - 15 * im.tiles) // 2 - fh // 2))


def build_main(builder, clim_name, specs, starts, editor=False):
    images = [formats.Image() for _ in range(formats.MAIN_ENTRIES)]
    for gid, spec in specs.items():
        if gid in layout.ALIASES:
            continue
        s = starts[gid]
        imgs = builder.group_images(gid, clim_name)
        hole = layout.HOLES.get(gid)
        for off, im in enumerate(imgs):
            if hole and hole[0] <= off <= hole[1]:
                continue
            images[s + off] = im
    # desert camels at fixed ids
    for k in range(96):
        d, f = k % 8, k // 8
        img, ax, ay = figures.animal("horse", d, f)
        images[layout.CAMEL_START + k] = formats.Image("sprite", img, anim={"num_sprites": 1, "offset_x": ax,
                                                                            "offset_y": ay})
    for k, im in enumerate(ui.arrow_images()):
        images[15 + k] = formats.Image("opaque", im)
    images[0] = formats.Image()
    group_ids = [0] * formats.MAX_GROUPS
    for gid, s in starts.items():
        group_ids[gid] = s
    return images, group_ids


ENEMY_FILES = ["goths", "Etruscan", "carthage", "Greek", "egyptians", "Persians", "Phoenician", "celts", "Gaul",
               "North African"]
ENEMY_COLORS = {"goths": (110, 90, 60), "Etruscan": (60, 100, 160), "carthage": (160, 120, 40),
                "Greek": (60, 80, 170), "egyptians": (220, 210, 160), "Persians": (130, 50, 110),
                "Phoenician": (120, 40, 100), "celts": (60, 120, 60), "Gaul": (90, 110, 60),
                "North African": (200, 170, 110)}


def build_enemy(name, espec):
    col = ENEMY_COLORS[name]
    images = [formats.Image() for _ in range(formats.ENEMY_ENTRIES)]
    for off in range(201, formats.ENEMY_ENTRIES):
        e = entry_for(espec, off)
        d = e.get("desc", "").lower()
        state, direction, frame, frames = classify_frame(e.get("desc", ""), off, e)
        if name == "celts" and 449 <= off <= 544:
            direction = (direction + 1) % 8
        native = off < 297 or ("native" in d and off < 449)
        if "elephant" in d and name == "carthage":
            img, ax, ay = figures.animal("horse", direction, frame, state="death" if state == "death" else "walk")
        else:
            outfit = dict(tunic=(150, 110, 70) if native else col,
                          helmet=None if native or off < 449 else (150, 150, 150),
                          item="spear" if (native or "spear" in d or "throw" in d or "javelin" in d) else "sword",
                          shield=None if native else core.shade(col, 0.7),
                          skin=(170, 120, 80) if native else figures.SKIN)
            if "archer" in d or "bow" in d:
                outfit["item"] = "staff"
            img, ax, ay = figures.person(direction, frame, state=state, frames=frames, **outfit)
        images[off] = formats.Image("sprite", img, anim={"num_sprites": 1, "offset_x": ax, "offset_y": ay})
    return images


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    specs, extra = load_specs()
    counts = {gid: s["count"] for gid, s in specs.items()}
    for gid in layout.ALIASES:
        counts.pop(gid, None)
    starts = layout.assign(counts)
    used = sum(counts.values())
    print("groups:", len(specs), "images:", used)
    json.dump({specs[g]["name"]: s for g, s in sorted(starts.items())}, open(os.path.join(out, "layout.json"), "w"),
              indent=1)

    # text
    text_data.write_all(out, starts)
    model_txt.write(os.path.join(out, "c3_model.txt"))
    print("text done %.1fs" % (time.time() - t0))

    builder = Builder(specs, starts)
    for clim, sg2, dat in (("central", "c3", "c3"), ("north", "c3_north", "c3_north"),
                           ("desert", "c3_south", "c3_south")):
        images, group_ids = build_main(builder, clim, specs, starts)
        if clim == "central":
            sizes = []
            for gid, sp in specs.items():
                if gid in layout.ALIASES:
                    continue
                tot = sum(len(im.encode()[0]) for im in builder.group_images(gid, clim) if not im.external)
                sizes.append((tot, sp["name"]))
            sizes.sort(reverse=True)
            print("largest groups:", ", ".join("%s=%dK" % (n, t // 1024) for t, n in sizes[:15]))
        size = formats.write_sg2(os.path.join(out, sg2 + ".sg2"), os.path.join(out, dat + ".555"), images, group_ids,
                                 ui.BITMAPS, formats.MAIN_ENTRIES, external_dir=os.path.join(out, "555"))
        print("%s: %d bytes of pixel data (limit 12100000) %.1fs" % (sg2, size, time.time() - t0))
        assert size <= 12100000, "main graphics too large"
        # editor graphics share the same layout
        ed = {"c3": "c3map", "c3_north": "c3map_north", "c3_south": "c3map_south"}[sg2]
        formats.write_sg2(os.path.join(out, ed + ".sg2"), os.path.join(out, ed + ".555"), images, group_ids,
                          ui.BITMAPS, formats.MAIN_ENTRIES, external_dir=os.path.join(out, "555"))

    espec = extra.get("_ENEMY_FILE", [{"entries": []}])[0]
    for name in ENEMY_FILES:
        imgs = build_enemy(name, espec)
        size = formats.write_sg2(os.path.join(out, name + ".sg2"), os.path.join(out, name + ".555"), imgs,
                                 [0] * formats.MAX_GROUPS, ["enemy.bmp"], formats.ENEMY_ENTRIES)
        assert size <= 2400000, "enemy graphics too large"
    print("enemies done %.1fs" % (time.time() - t0))

    scenario.write_all(out, starts)
    print("all done %.1fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
