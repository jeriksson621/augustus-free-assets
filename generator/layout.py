"""Assigns absolute image indices to groups, honouring engine constraints."""
import formats

RESERVED = [(0, 0), (15, 22), (4922, 5017), (6145, 6192)]  # dummy, arrow buttons, desert camels, skipped
CAMEL_START = 4922
# groups that must be laid out back-to-back in this order
CHAINS = [[78, 168, 169, 170], [184, 185]]
# group -> (base group, offset) aliases without own images
ALIASES = {196: (19, 15)}
# group -> latest allowed start
MAX_START = {111: 5545}
# holes inside groups that other groups may reuse: group -> (from, to) offsets
HOLES = {97: (128, 695)}


class Allocator:
    def __init__(self, size):
        self.free = [(1, size - 1)]
        for a, b in RESERVED:
            self.take(a, b)

    def take(self, a, b):
        out = []
        for (x, y) in self.free:
            if y < a or x > b:
                out.append((x, y))
                continue
            if x < a:
                out.append((x, a - 1))
            if y > b:
                out.append((b + 1, y))
        self.free = out

    def release(self, a, b):
        self.free.append((a, b))
        self.free.sort()

    def alloc(self, count, limit=None):
        for (x, y) in self.free:
            if y - x + 1 >= count and (limit is None or x <= limit):
                self.take(x, x + count - 1)
                return x
        raise RuntimeError("no room for %d images" % count)


def assign(groups):
    """groups: dict gid -> count. Returns dict gid -> start index."""
    alloc = Allocator(formats.MAIN_ENTRIES)
    starts = {}
    # terrain black must sit at ids 1..5
    alloc.take(1, 5)
    starts[1] = 1
    chained = {g for c in CHAINS for g in c}
    order = sorted(g for g in groups if g not in ALIASES and g != 1)
    # constrained groups first so they get early slots
    order.sort(key=lambda g: (g not in MAX_START, groups[g] < 600, g))
    for g in order:
        if g in starts:
            continue
        chain = next((c for c in CHAINS if c[0] == g), None)
        if g in chained and not chain:
            continue
        members = chain or [g]
        total = sum(groups.get(m, 0) for m in members)
        s = alloc.alloc(total, MAX_START.get(g))
        for m in members:
            starts[m] = s
            s += groups.get(m, 0)
        if g in HOLES:
            a, b = HOLES[g]
            alloc.release(starts[g] + a, starts[g] + b)
    for g, (base, off) in ALIASES.items():
        starts[g] = starts[base] + off
    return starts
