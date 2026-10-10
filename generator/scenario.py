"""Custom scenarios (.map, classic unversioned format) and empire data (c32.emp).

Readers: src/game/file_io.c (pieces), src/scenario/scenario.c scenario_load_state (1720-byte
settings block for SCENARIO_LAST_UNVERSIONED), src/empire/object.c empire_object_load.
"""
import math
import os
import random
import struct

GRID = 162
TERRAIN_TREE, TERRAIN_ROCK, TERRAIN_WATER, TERRAIN_SHRUB = 1, 2, 4, 16
TERRAIN_ROAD, TERRAIN_MEADOW = 64, 2048
EDGE_LEFTMOST_TILE = 0x40

GROUP = {"tree": 4, "shrub": 2, "grass": 10, "water": 5, "rock": 239, "meadow": 138, "road": 112,
         "native": 183, "crops": 100, "empire_city": 174, "empire_trade": 175, "empire_distant": 176,
         "empire_foreign": 223}


def noise(x, y, scale, seed):
    def h(i, j):
        n = (i * 374761393 + j * 668265263 + seed * 1442695041) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0
    xs, ys = x / scale, y / scale
    x0, y0 = math.floor(xs), math.floor(ys)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = h(x0, y0), h(x0 + 1, y0), h(x0, y0 + 1), h(x0 + 1, y0 + 1)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


class Map:
    def __init__(self, size, seed):
        self.w = self.h = size
        self.seed = seed
        self.rnd = random.Random(seed)
        self.terrain = [[0] * size for _ in range(size)]

    def set(self, x, y, flag):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.terrain[y][x] = flag

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.terrain[y][x]
        return -1


def make_landscape(m, sea="north-east", forest=0.62, rocks=0.78, river=True):
    s = m.seed
    W, H = m.w, m.h
    for y in range(H):
        for x in range(W):
            t = 0
            if sea == "north-east":
                d = (x - W) ** 2 * 0.6 + (y + 6) ** 2
                if d < (W * 0.42) ** 2 + (noise(x, y, 7, s) - 0.5) * W * 14:
                    t = TERRAIN_WATER
            elif sea == "oasis":
                d = (x - W * 0.55) ** 2 + (y - H * 0.4) ** 2
                if d < (W * 0.12) ** 2 + (noise(x, y, 5, s) - 0.5) * W * 6:
                    t = TERRAIN_WATER
            if not t:
                f = noise(x, y, 9, s + 1) * 0.7 + noise(x, y, 3, s + 2) * 0.3
                r = noise(x, y, 6, s + 3)
                if f > forest:
                    t = TERRAIN_TREE
                elif r > rocks:
                    t = TERRAIN_ROCK
                elif f > forest - 0.06 and m.rnd.random() < 0.3:
                    t = TERRAIN_SHRUB
            m.terrain[y][x] = t
    if river:
        # a river winding from the west edge into the sea
        y = H * 0.25
        for x in range(0, W):
            y += (noise(x, 0, 6, s + 9) - 0.5) * 1.6
            yi = int(y)
            for dy in range(-1, 2):
                m.set(x, yi + dy, TERRAIN_WATER)
            if m.get(x, yi) == TERRAIN_WATER and x > W * 0.6 and m.get(x + 3, yi) == TERRAIN_WATER:
                pass
    # meadow along water
    for y in range(H):
        for x in range(W):
            if m.terrain[y][x] == 0:
                near = any(m.get(x + dx, y + dy) == TERRAIN_WATER for dx in (-2, 0, 2) for dy in (-2, 0, 2))
                if near and noise(x, y, 4, s + 5) > 0.45:
                    m.terrain[y][x] = TERRAIN_MEADOW


def clear_area(m, x0, y0, x1, y1):
    for y in range(max(0, y0), min(m.h, y1)):
        for x in range(max(0, x0), min(m.w, x1)):
            if m.terrain[y][x] != TERRAIN_WATER:
                m.terrain[y][x] = 0


def lay_road(m, pts, resources=True):
    path = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        x, y = ax, ay
        while (x, y) != (bx, by):
            if m.get(x, y) == TERRAIN_WATER:
                raise ValueError("road crosses water at %d,%d" % (x, y))
            path.append((x, y))
            if x != bx:
                x += 1 if bx > x else -1
            elif y != by:
                y += 1 if by > y else -1
    path.append(pts[-1])
    if resources:
        add_resource_patches(m, path)
    for x, y in path:
        m.set(x, y, TERRAIN_ROAD)


def _blob(m, cx, cy, r, flag, keep):
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = math.hypot(x - cx, y - cy) + (noise(x, y, 2, m.seed + 41) - 0.5) * 1.2
            if d <= r and (x, y) not in keep and m.get(x, y) not in (-1, TERRAIN_ROAD):
                m.set(x, y, flag)


def add_resource_patches(m, path):
    """Place meadow, rock, forest and pond patches near the road so every industry is buildable."""
    keep = set()
    for x, y in path:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                keep.add((x + dx, y + dy))
    kinds = ["meadow", "meadow", "rock", "trees", "pond", "meadow", "rock", "trees"]
    step = max(6, len(path) // 9)
    k = 0
    for i in range(step // 2, len(path) - 2, step):
        x, y = path[i]
        nx, ny = path[min(i + 1, len(path) - 1)]
        dx, dy = nx - x, ny - y
        side = 1 if k % 2 == 0 else -1
        px, py = -dy * side, dx * side  # perpendicular
        dist = 8 if kinds[k % len(kinds)] != "pond" else 7
        cx, cy = x + px * dist, y + py * dist
        kind = kinds[k % len(kinds)]
        if kind == "meadow":
            _blob(m, cx, cy, 4, TERRAIN_MEADOW, keep)
        elif kind == "rock":
            _blob(m, cx, cy, 2, TERRAIN_ROCK, keep)
        elif kind == "trees":
            _blob(m, cx, cy, 3, TERRAIN_TREE, keep)
        elif kind == "pond":
            _blob(m, cx, cy, 4, TERRAIN_MEADOW, keep)
            _blob(m, cx, cy, 2, TERRAIN_WATER, keep)
        k += 1


def encode_grids(m, starts):
    W, H = m.w, m.h
    grid_start = (GRID - H) // 2 * GRID + (GRID - W) // 2
    border = GRID - W
    images = [0] * (GRID * GRID)
    edge = [0] * (GRID * GRID)
    terrain = [0] * (GRID * GRID)
    rnd_grid = [0] * (GRID * GRID)
    rnd = random.Random(m.seed + 77)
    for y in range(H):
        for x in range(W):
            off = grid_start + x + y * GRID
            t = m.terrain[y][x]
            terrain[off] = t
            edge[off] = EDGE_LEFTMOST_TILE
            r = rnd.randint(0, 255)
            rnd_grid[off] = r
            if t == TERRAIN_TREE:
                ring = sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1) if m.get(x + dx, y + dy) == TERRAIN_TREE)
                ring2 = sum(1 for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)
                            if m.get(x + dx, y + dy) in (TERRAIN_TREE, TERRAIN_ROCK))
                density = 0 if ring < 9 else (1 if ring2 < 25 else 2)
                images[off] = starts[GROUP["tree"]] + density * 8 + (r & 7)
            elif t == TERRAIN_SHRUB:
                images[off] = starts[GROUP["shrub"]] + (r & 7)
            elif t == TERRAIN_ROCK:
                images[off] = starts[GROUP["rock"]] + (r & 7)
            elif t == TERRAIN_WATER:
                images[off] = starts[GROUP["water"]]
            elif t == TERRAIN_MEADOW:
                images[off] = starts[GROUP["meadow"]] + (r & 3)
            else:
                images[off] = starts[GROUP["grass"]] + (r & 7)
    out = bytearray()
    out += struct.pack("<%dH" % len(images), *images)
    out += bytes(edge)
    out += struct.pack("<%dH" % len(terrain), *terrain)
    out += bytes(GRID * GRID)  # bitfields: all 1x1
    out += bytes(rnd_grid)
    out += bytes(GRID * GRID)  # elevation
    out += struct.pack("<ii", 0x5EED, 0xC0FFEE)  # random_iv
    out += struct.pack("<ii", W // 2, H // 2)  # camera
    return bytes(out), grid_start, border


def settings_block(m, starts, grid_start, border, s):
    b = bytearray()

    def i16(*v):
        b.extend(struct.pack("<%dh" % len(v), *v))

    def i32(*v):
        b.extend(struct.pack("<%di" % len(v), *v))

    def u8(*v):
        b.extend(bytes(v))

    def raw(text, n):
        enc = text.encode("cp1252")[:n - 1]
        b.extend(enc + bytes(n - len(enc)))

    i16(s["start_year"], 0, s.get("empire", 0))
    b.extend(bytes(8))
    req = s.get("requests", [])
    for field in range(4):  # year, resource, amount, deadline
        for k in range(20):
            if k < len(req):
                i16(req[k][field])
            else:
                i16([0, 0, 0, 5][field])
    inv = s.get("invasions", [])
    for field in range(5):  # year, type, amount, from, attack_type
        for k in range(20):
            if k < len(inv):
                i16(inv[k][field])
            else:
                i16([0, 0, 0, 8, 0][field])
    b.extend(bytes(2))
    i32(s["funds"])
    i16(s.get("enemy", 0))
    b.extend(bytes(6))
    i32(m.w, m.h, grid_start, border)
    raw(s["brief"], 64)
    raw(s["briefing"], 522)
    u8(*([0] * 20))  # can comply
    i16(s.get("image", 0), 1 if s.get("open_play") else 0, s.get("rank", 0))
    herd = s.get("herd", [])
    i16(*[(herd[k][0] if k < len(herd) else -1) for k in range(4)])
    i16(*[(herd[k][1] if k < len(herd) else -1) for k in range(4)])
    i16(*([0] * 20))  # demand change years
    u8(*([0] * 80))  # month, resource, route, is_rise
    i16(*([0] * 20))  # price change years
    u8(*([0] * 80))
    i32(0, 0, 0, 0)  # gladiator revolt, emperor change
    i32(1, 1, 1, 1, 1, 1, 1)  # random events enabled (classic flags)
    fish = s.get("fish", [])
    i16(*[(fish[k][0] if k < len(fish) else -1) for k in range(8)])
    i16(*[(fish[k][1] if k < len(fish) else -1) for k in range(8)])
    u8(*[(req[k][4] if k < len(req) else 8) for k in range(20)])  # favour reward
    u8(*[(inv[k][5] if k < len(inv) else 0) for k in range(20)])  # invasion month
    u8(*[(req[k][5] if k < len(req) else 0) for k in range(20)])  # request month
    u8(*([0] * 20))  # state
    u8(*([0] * 20))  # visible
    u8(*([0] * 20))  # months to comply
    i32(1 if s.get("rome_wheat") else 0)
    i16(*([1] * 50))  # allowed buildings
    assert len(b) == 1572, len(b)
    w = s.get("win", {})
    i32(w.get("culture", 0), w.get("prosperity", 0), w.get("peace", 0), w.get("favor", 0))
    u8(*[1 if w.get(k) else 0 for k in ("culture", "prosperity", "peace", "favor")])
    i32(1 if w.get("time_limit") else 0, w.get("time_limit", 0), 1 if w.get("survival") else 0, w.get("survival", 0))
    i32(0, 0)  # earthquake severity/year
    i32(1 if w.get("population") else 0, w.get("population", 0))
    i16(-1, -1)  # earthquake point
    i16(*s["entry"])
    i16(*s["exit"])
    invp = s.get("invasion_points", [])
    i16(*[(invp[k][0] if k < len(invp) else -1) for k in range(8)])
    i16(*[(invp[k][1] if k < len(invp) else -1) for k in range(8)])
    i16(*s.get("river_entry", (-1, -1)))
    i16(*s.get("river_exit", (-1, -1)))
    i32(s.get("rescue_loan", 3000), 10, 20, 30)
    i32(starts[GROUP["native"]], starts[GROUP["native"]] + 2, starts[GROUP["crops"]])
    assert len(b) == 1704, len(b)
    u8(s.get("climate", 0), 1)
    b.extend(bytes(2))
    i32(0, 0)  # empire expansion
    u8(4, 4)  # distant battle travel months
    assert len(b) == 1718
    u8(0)  # open play scenario id
    b.extend(bytes(1720 - len(b)))
    return bytes(b)


def write_map(path, m, starts, settings):
    grids, grid_start, border = encode_grids(m, starts)
    block = settings_block(m, starts, grid_start, border, settings)
    with open(path, "wb") as f:
        f.write(grids)
        f.write(block)
        f.write(struct.pack("<i", 0))  # end marker
    assert os.path.getsize(path) == 211692


# ------------------------------------------------------------------ empire

def empire_object(type_, x, y, w, h, image, city_type=0, name_id=0, route=0, route_open=0, cost=0,
                  sells=(), buys=(), trade40=(), trade25=(), trade15=(), in_use=1):
    o = bytearray(64)
    o[0], o[1], o[2] = type_, in_use, 0
    struct.pack_into("<hhhhhh", o, 4, x, y, w, h, image, 0)
    o[17] = 4  # distant battle travel months
    struct.pack_into("<hh", o, 20, 0, 0)
    o[24], o[25], o[26], o[27] = city_type, name_id, route, route_open
    struct.pack_into("<h", o, 28, cost)
    for i, r in enumerate(sells[:10]):
        o[30 + i] = r
    for i, r in enumerate(buys[:8]):
        o[42 + i] = r
    o[50], o[51] = 0, 0

    def mask(rs):
        v = 0
        for r in rs:
            v |= 1 << r
        return v
    struct.pack_into("<HHH", o, 52, mask(trade40), mask(trade25), mask(trade15))
    return bytes(o)


def write_empire(path, starts):
    # legacy resource ids: 1 wheat 2 veg 3 fruit 4 olives 5 vines 6 meat 7 wine 8 oil 9 iron 10 timber
    # 11 clay 12 marble 13 weapons 14 furniture 15 pottery
    g = starts
    objs = [
        empire_object(1, 900, 480, 50, 50, g[GROUP["empire_city"]], city_type=1, name_id=4, route=0,
                      sells=(1, 2, 3, 7, 8, 13, 14, 15)),
        empire_object(1, 620, 360, 50, 50, g[GROUP["empire_trade"]], city_type=2, name_id=30, route=1, cost=500,
                      sells=(10, 8, 15, 9), buys=(7, 14, 1), trade25=(10, 8), trade15=(15, 9, 7, 14, 1)),
        empire_object(4, 760, 420, 0, 0, 0, route=1),
        empire_object(1, 1250, 640, 50, 50, g[GROUP["empire_trade"]], city_type=2, name_id=6, route=2, cost=800,
                      sells=(7, 12, 5, 4), buys=(1, 15, 13), trade25=(7, 12), trade15=(5, 4, 1, 15, 13)),
        empire_object(5, 1080, 560, 0, 0, 0, route=2),
        empire_object(1, 1050, 300, 50, 50, g[GROUP["empire_distant"]], city_type=0, name_id=12, route=0),
        empire_object(1, 1500, 250, 50, 50, g[GROUP["empire_foreign"]], city_type=4, name_id=38, route=0),
        empire_object(1, 400, 620, 50, 50, g[GROUP["empire_distant"]], city_type=0, name_id=7, route=0),
    ]
    data = b"".join(objs)
    data += bytes(12800 - len(data))
    header = bytearray(1280)
    struct.pack_into("<hh", header, 0, 500, 200)
    with open(path, "wb") as f:
        f.write(header)
        f.write(data)


# ------------------------------------------------------------------ scenarios

def write_all(out, starts):
    write_empire(os.path.join(out, "c32.emp"), starts)
    write_empire(os.path.join(out, "c3.emp"), starts)

    # 1. temperate river valley with goals
    m = Map(96, 1234)
    make_landscape(m, sea="north-east")
    clear_area(m, 20, 40, 70, 80)
    road = [(0, 60), (40, 60), (40, 95)]
    clear_area(m, 0, 58, 42, 63)
    clear_area(m, 38, 58, 43, 96)
    lay_road(m, road)
    write_map(os.path.join(out, "Tiber Valley.map"), m, starts, dict(
        start_year=-350, funds=8000, rescue_loan=5000, climate=0, image=1,
        brief="A fertile valley by the sea",
        briefing="Build a prosperous town in this green valley. Lay out housing along the road, bring water "
                 "from wells and fountains, feed your people from farms by the river, and keep the gods content.",
        win=dict(culture=20, prosperity=15, peace=20, favor=30, population=1500),
        entry=(0, 60), exit=(40, 95), herd=[(15, 15), (80, 80)],
        fish=[(85, 8), (90, 15), (75, 5)], invasion_points=[(0, 10), (95, 95)],
        river_entry=(0, 24), river_exit=(95, 5)))

    # 2. open play sandbox
    m = Map(80, 4321)
    make_landscape(m, sea="north-east", forest=0.68, rocks=0.82)
    clear_area(m, 10, 30, 60, 70)
    clear_area(m, 0, 38, 50, 43)
    clear_area(m, 45, 38, 50, 80)
    lay_road(m, [(0, 40), (47, 40), (47, 79)])
    write_map(os.path.join(out, "Open Fields.map"), m, starts, dict(
        start_year=-300, funds=20000, rescue_loan=10000, climate=0, image=4, open_play=True,
        brief="Free building, no objectives",
        briefing="Plenty of land and a generous treasury. There are no goals here: build the city you like.",
        entry=(0, 40), exit=(47, 79), herd=[(60, 70)], fish=[(72, 6), (76, 12)],
        river_entry=(0, 20), river_exit=(79, 4)))

    # 3. northern frontier (north climate) with a few barbarian raids
    m = Map(96, 777)
    make_landscape(m, sea="north-east", forest=0.58, rocks=0.76)
    clear_area(m, 15, 45, 65, 85)
    clear_area(m, 0, 63, 42, 68)
    clear_area(m, 38, 63, 43, 96)
    lay_road(m, [(0, 65), (40, 65), (40, 95)])
    write_map(os.path.join(out, "Northern Frontier.map"), m, starts, dict(
        start_year=-200, funds=6000, rescue_loan=4000, climate=1, image=7, enemy=0,
        brief="Hold the frontier against raiders",
        briefing="Wild tribes roam the forests beyond the river. Grow your settlement, raise walls and a fort, "
                 "and keep the peace for Rome.",
        win=dict(culture=15, prosperity=10, peace=30, favor=30, population=1000),
        invasions=[(4, 1, 6, 0, 0, 3), (8, 1, 10, 1, 0, 6)],
        entry=(0, 65), exit=(40, 95), herd=[(20, 20)], fish=[(85, 8), (90, 14)],
        invasion_points=[(5, 5), (95, 90)], river_entry=(0, 24), river_exit=(95, 5)))

    # 4. desert oasis (desert climate)
    m = Map(80, 99)
    make_landscape(m, sea="oasis", forest=0.75, rocks=0.74, river=False)
    clear_area(m, 5, 50, 70, 75)
    lay_road(m, [(0, 60), (79, 60)])
    write_map(os.path.join(out, "Desert Oasis.map"), m, starts, dict(
        start_year=-100, funds=7000, rescue_loan=4000, climate=2, image=10,
        brief="A trading post at an oasis",
        briefing="Caravans cross the desert past this oasis. Build a town that thrives on trade and water.",
        win=dict(culture=10, prosperity=20, peace=10, favor=25, population=800),
        entry=(0, 60), exit=(79, 60), herd=[(20, 20)]))


# ------------------------------------------------------------------ campaign

def campaign_settings(mission):
    """Settings for campaign mission 0..21 (0/1 introductory, then peaceful/military pairs)."""
    rank = mission if mission <= 1 else mission // 2 + 1
    military = mission >= 2 and mission % 2 == 1
    climate = [0, 0, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1][mission]
    size = min(120, 72 + rank * 4)
    pop = [150, 400][mission] if mission <= 1 else 600 + 450 * (rank - 2)
    goals = dict(population=pop)
    if mission >= 1:
        goals.update(culture=min(60, 5 + 5 * rank), prosperity=min(60, 5 + 5 * rank),
                     peace=min(60, 5 + 5 * rank), favor=min(70, 25 + 4 * rank))
    invasions = []
    if military:
        for k in range(min(5, 1 + rank // 2)):
            invasions.append((3 + k * 3, 1, 4 + rank * 2 + k * 2, k % 2, 0, (k * 4) % 12))
    return rank, military, climate, size, goals, invasions


def write_campaign_maps(out_dir, starts):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for mission in range(22):
        rank, military, climate, size, goals, invasions = campaign_settings(mission)
        m = Map(size, 5000 + mission * 37)
        make_landscape(m, sea="oasis" if climate == 2 else "north-east", forest=0.6 + (mission % 3) * 0.03,
                       rocks=0.76, river=climate != 2)
        mid = int(size * 0.62)
        clear_area(m, 10, mid - 22, size - 25, size - 8)
        clear_area(m, 0, mid - 2, mid + 3, mid + 3)
        clear_area(m, mid - 2, mid - 2, mid + 3, size)
        try:
            lay_road(m, [(0, mid), (mid, mid), (mid, size - 1)])
        except ValueError:
            clear_area(m, 0, mid - 3, size, size)
            for y in range(mid - 3, size):
                for x in range(size):
                    if m.terrain[y][x] == TERRAIN_WATER:
                        m.terrain[y][x] = 0
            lay_road(m, [(0, mid), (mid, mid), (mid, size - 1)])
        path = os.path.join(out_dir, "mission%02d.map" % mission)
        write_map(path, m, starts, dict(
            start_year=-400 + mission * 15, funds=4000 + 1000 * rank, rescue_loan=3000 + 500 * rank,
            climate=climate, image=mission % 16, enemy=[0, 0, 7, 8, 1, 2, 3, 4, 5, 6, 9][min(10, rank)],
            rank=rank, brief="Campaign mission %d" % (mission + 1),
            briefing="Govern this province well and meet the goals Rome has set for you.",
            win=goals, invasions=invasions,
            entry=(0, mid), exit=(mid, size - 1), herd=[(size // 5, size // 5)],
            fish=[(size - 8, 6), (size - 4, 12)] if climate != 2 else [],
            invasion_points=[(2, 2), (size - 2, size - 2)],
            river_entry=(0, size // 4) if climate != 2 else (-1, -1),
            river_exit=(size - 1, 4) if climate != 2 else (-1, -1)))
        paths.append(path)
    return paths
