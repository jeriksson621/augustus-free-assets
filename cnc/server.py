import json, math, random, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

W, H = 2400, 1800
TICK = 0.1
V = lambda inf, veh, bld, air: dict(inf=inf, veh=veh, bld=bld, air=air)  # damage multiplier per armor class (0 = can't target)
B = {  # buildings: cost, hp, size, build time(s), power, prereqs
 'cy':      dict(cost=0,    hp=3000, size=90, t=0,  pw=0,   pre=[]),
 'power':   dict(cost=300,  hp=800,  size=60, t=5,  pw=100, pre=[]),
 'refinery':dict(cost=1000, hp=1200, size=80, t=10, pw=-40, pre=['power']),
 'barracks':dict(cost=400,  hp=900,  size=60, t=6,  pw=-20, pre=['power']),
 'wall':    dict(cost=50,   hp=600,  size=20, t=1,  pw=0,   pre=['barracks']),
 'turret':  dict(cost=500,  hp=1000, size=40, t=6,  pw=-20, pre=['barracks'], rng=260, dmg=40, rof=12, vs=V(.6, 1, 1, 0), fx='shell'),
 'factory': dict(cost=1200, hp=1500, size=80, t=12, pw=-40, pre=['refinery']),
 'comm':    dict(cost=800,  hp=1000, size=60, t=8,  pw=-40, pre=['refinery']),
 'sam':     dict(cost=600,  hp=700,  size=40, t=6,  pw=-20, pre=['comm'], rng=320, dmg=55, rof=14, vs=V(0, 0, 0, 1), fx='missile'),
 'helipad': dict(cost=1000, hp=1000, size=60, t=10, pw=-20, pre=['comm']),
 'repair':  dict(cost=600,  hp=900,  size=60, t=7,  pw=-30, pre=['factory']),
 'tech':    dict(cost=1500, hp=1400, size=70, t=14, pw=-100, pre=['factory', 'comm']),
 'advpower':dict(cost=700,  hp=1200, size=70, t=8,  pw=220, pre=['tech']),
 'obelisk': dict(cost=1500, hp=1200, size=40, t=12, pw=-120, pre=['tech'], rng=340, dmg=220, rof=35, vs=V(1, 1, 1, 0), fx='laser'),
}
U = {  # units; cls = armor class
 'rifle':     dict(cost=100,  hp=120,  spd=3.0, rng=150, dmg=10, rof=8,  t=3,  at='barracks', r=7,  cls='inf', vs=V(1, .4, .4, .3), fx='bullet'),
 'flamer':    dict(cost=200,  hp=140,  spd=2.7, rng=90,  dmg=24, rof=5,  t=4,  at='barracks', r=7,  cls='inf', vs=V(1.6, .5, 1.3, 0), fx='flame'),
 'rocket':    dict(cost=300,  hp=100,  spd=2.6, rng=220, dmg=35, rof=20, t=5,  at='barracks', r=7,  cls='inf', vs=V(.35, 1, 1, 1), fx='rocket'),
 'engineer':  dict(cost=500,  hp=90,   spd=2.8, rng=0,   dmg=0,  rof=0,  t=5,  at='barracks', r=7,  cls='inf', vs=V(0, 0, 0, 0)),
 'commando':  dict(cost=1000, hp=200,  spd=3.2, rng=270, dmg=150, rof=22, t=10, at='barracks', r=7, cls='inf', vs=V(1, .25, 1.5, .2), fx='bullet', pre=['tech']),
 'buggy':     dict(cost=300,  hp=180,  spd=6.5, rng=150, dmg=11, rof=5,  t=4,  at='factory',  r=10, cls='veh', vs=V(1, .4, .3, .5), fx='bullet'),
 'tank':      dict(cost=800,  hp=500,  spd=4.0, rng=200, dmg=45, rof=15, t=8,  at='factory',  r=13, cls='veh', vs=V(.6, 1, .8, 0), fx='shell'),
 'artillery': dict(cost=700,  hp=220,  spd=2.6, rng=400, dmg=70, rof=38, t=8,  at='factory',  r=12, cls='veh', vs=V(1, .7, 1, 0), fx='arty', splash=45, pre=['comm']),
 'mammoth':   dict(cost=1700, hp=1400, spd=2.4, rng=220, dmg=65, rof=14, t=14, at='factory',  r=17, cls='veh', vs=V(.7, 1, 1, .8), fx='shell', pre=['tech']),
 'harvester': dict(cost=1400, hp=700,  spd=3.5, rng=0,   dmg=0,  rof=0,  t=10, at='factory',  r=14, cls='veh', vs=V(0, 0, 0, 0)),
 'orca':      dict(cost=1200, hp=320,  spd=6.0, rng=200, dmg=38, rof=16, t=10, at='helipad',  r=13, cls='air', vs=V(.5, 1, .8, .7), fx='missile', air=True),
}
import heapq
CELL = 20; GW, GH = W//CELL, H//CELL
lock = threading.Lock()
static = bytearray(GW*GH); grid = bytearray(GW*GH); gridkey = [None]

def gen_obstacles(field_centers, bases):
    obs = []
    tries = 0
    while len(obs) < 140 and tries < 4000:
        tries += 1
        kind = 'rock' if random.random() < .45 else 'tree'
        x, y = random.uniform(80, W-80), random.uniform(80, H-80)
        n = random.randint(5, 12) if kind == 'rock' else random.randint(3, 8)
        ang = random.uniform(0, 6.3); pts = []
        for _ in range(n):
            r = random.uniform(16, 28) if kind == 'rock' else random.uniform(11, 17)
            if all(math.hypot(x-bx, y-by) > 400 for bx, by in bases) and all(math.hypot(x-fx, y-fy) > 200 for fx, fy in field_centers) and 30 < x < W-30 and 30 < y < H-30:
                pts.append([round(x), round(y), round(r), kind])
            if kind == 'rock': ang += random.uniform(-.6, .6); x += math.cos(ang)*r*1.3; y += math.sin(ang)*r*1.3
            else: x += random.uniform(-22, 22); y += random.uniform(-22, 22)
        obs += pts
    return obs

def mark_circle(g, x, y, r):
    for cy in range(max(0, int((y-r)//CELL)-1), min(GH, int((y+r)//CELL)+2)):
        for cx in range(max(0, int((x-r)//CELL)-1), min(GW, int((x+r)//CELL)+2)):
            if math.hypot(cx*CELL+CELL/2-x, cy*CELL+CELL/2-y) < r+6: g[cy*GW+cx] = 1

def rebuild_grid():
    key = tuple(sorted(e['id'] for e in S['ents'].values() if e['b']))
    if key == gridkey[0]: return
    gridkey[0] = key; grid[:] = static
    for e in S['ents'].values():
        if e['b']:
            h = B[e['k']]['size']/2 + 4
            for cy in range(max(0, int((e['y']-h)//CELL)), min(GH, int((e['y']+h)//CELL)+1)):
                for cx in range(max(0, int((e['x']-h)//CELL)), min(GW, int((e['x']+h)//CELL)+1)):
                    grid[cy*GW+cx] = 1

def cell(x, y): return min(GW-1, max(0, int(x//CELL))), min(GH-1, max(0, int(y//CELL)))
def blocked(x, y):
    cx, cy = cell(x, y); return grid[cy*GW+cx]

def nearest_free(cx, cy):
    if not grid[cy*GW+cx]: return cx, cy
    for r in range(1, 25):
        best = None
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                if max(abs(dx), abs(dy)) != r: continue
                x, y = cx+dx, cy+dy
                if 0 <= x < GW and 0 <= y < GH and not grid[y*GW+x]:
                    d = dx*dx+dy*dy
                    if best is None or d < best[0]: best = (d, x, y)
        if best: return best[1], best[2]
    return cx, cy

def los(x0, y0, x1, y1):
    d = math.hypot(x1-x0, y1-y0); n = int(d/7)+1
    for i in range(1, n+1):
        t = i/n
        if blocked(x0+(x1-x0)*t, y0+(y1-y0)*t): return False
    return True

NB = [(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)]
def astar(sx, sy, gx, gy):
    s = cell(sx, sy); g = nearest_free(*cell(gx, gy))
    if grid[g[1]*GW+g[0]] == 0 and g != cell(gx, gy): gx, gy = g[0]*CELL+CELL/2, g[1]*CELL+CELL/2
    si, gi = s[1]*GW+s[0], g[1]*GW+g[0]
    openq = [(0, 0, si)]; came = {si: -1}; cost = {si: 0}; n = 0; best = (1e9, si)
    while openq and n < 9000:
        _, c, cur = heapq.heappop(openq); n += 1
        if cur == gi: break
        if c > cost[cur]: continue
        x, y = cur % GW, cur // GW
        hcur = math.hypot(x-g[0], y-g[1])
        if hcur < best[0]: best = (hcur, cur)
        for dx, dy, w in NB:
            nx, ny = x+dx, y+dy
            if not (0 <= nx < GW and 0 <= ny < GH): continue
            ni = ny*GW+nx
            if grid[ni] or (dx and dy and (grid[y*GW+nx] or grid[ny*GW+x])): continue
            nc = c + w
            if nc < cost.get(ni, 1e9):
                cost[ni] = nc; came[ni] = cur
                h = max(abs(nx-g[0]), abs(ny-g[1])) + .414*min(abs(nx-g[0]), abs(ny-g[1]))
                heapq.heappush(openq, (nc+h*1.05, nc, ni))
    end = gi if gi in came else best[1]
    pts = []; cur = end
    while cur != -1 and cur != si:
        pts.append((cur % GW*CELL+CELL/2, cur//GW*CELL+CELL/2)); cur = came[cur]
    pts.reverse()
    if end == gi: pts.append((gx, gy))
    # string-pull smoothing
    out = []; px, py = sx, sy; i = 0
    while i < len(pts):
        j = len(pts)-1
        while j > i and not los(px, py, *pts[j]): j -= 1
        out.append(pts[j]); px, py = pts[j]; i = j+1
    return out

def nav(e, x, y, spd):
    """Path-following move. Returns True on arrival."""
    key = cell(x, y)
    if blocked(e['x'], e['y']):  # inside an obstacle/building footprint: step out first
        fx, fy = nearest_free(*cell(e['x'], e['y']))
        move_to(e, fx*CELL+CELL/2, fy*CELL+CELL/2, spd); e['path'] = None
        return False
    if e.get('path') is None or (e.get('gk') != key and S['tick'] - e.get('pt', 0) > 4):
        e['path'] = [(x, y)] if los(e['x'], e['y'], x, y) else astar(e['x'], e['y'], x, y)
        e['gk'] = key; e['pt'] = S['tick']
    if not e['path']: e['path'] = None; return True
    wx, wy = e['path'][0]
    if move_to(e, wx, wy, spd):
        e['path'].pop(0)
        if not e['path']: e['path'] = None; return True
    # stuck detection
    lx, ly = e.get('last', (0, 0))
    e['stuck'] = e.get('stuck', 0)+1 if math.hypot(e['x']-lx, e['y']-ly) < spd*.25 else 0
    e['last'] = (e['x'], e['y'])
    if e['stuck'] > 12:
        e['stuck'] = 0; e['path'] = None
        if math.hypot(e['x']-x, e['y']-y) < 60: return True
    return False

def stop(e): e['path'] = None
nid = [1]
def new_id():
    nid[0] += 1; return nid[0]

def reset():
    global S
    S = dict(players=[None, None], ents={}, fields=[], winner=None, tick=0, mapv=random.randint(1, 10**9))
    random.seed()
    fcs = [(W/2, H/2), (500, 1400), (1900, 400), (1300, 300), (1100, 1500), (400, 500), (2000, 1300)]
    bases = [(250, 250), (W-250, H-250)]
    S['obs'] = gen_obstacles(fcs, bases)
    static[:] = bytes(GW*GH)
    for x, y, r, _ in S['obs']: mark_circle(static, x, y, r)
    gridkey[0] = None; grid[:] = static
    for (cx, cy) in fcs:
        for _ in range(40):
            fx, fy = cx+random.uniform(-140,140), cy+random.uniform(-110,110)
            if not blocked(fx, fy): S['fields'].append(dict(x=fx, y=fy, amt=500))
    for p, (x, y) in enumerate(bases):
        S['players'][p] = dict(credits=3000, joined=False, bq=None, ready=None, uq={'barracks': [], 'factory': [], 'helipad': []})
        add_b(p, 'cy', x, y)
        add_u(p, 'harvester', x+120 if p==0 else x-120, y)
        for i in range(3): add_u(p, 'rifle', x+60*i-60, y+(100 if p==0 else -100))

def add_b(p, kind, x, y):
    e = dict(id=new_id(), o=p, k=kind, b=1, x=x, y=y, hp=B[kind]['hp'], cd=0, tgt=None)
    S['ents'][e['id']] = e; return e

def add_u(p, kind, x, y):
    e = dict(id=new_id(), o=p, k=kind, b=0, x=x, y=y, hp=U[kind]['hp'], cd=0, tgt=None, mx=None, my=None, cargo=0, st='idle', force=False, am=False, hitby=None, path=None)
    S['ents'][e['id']] = e; return e

def power(p):
    prod = use = 0
    for e in S['ents'].values():
        if e['o'] == p and e['b']:
            pw = B[e['k']]['pw']
            if pw > 0: prod += pw
            else: use -= pw
    return prod, use

def has(p, kind):
    return any(e['o']==p and e['b'] and e['k']==kind for e in S['ents'].values())

def dist(a, b): return math.hypot(a['x']-b['x'], a['y']-b['y'])

def rad(e): return B[e['k']]['size']/2 if e['b'] else U[e['k']]['r']

def move_to(e, x, y, spd):
    dx, dy = x-e['x'], y-e['y']; d = math.hypot(dx, dy)
    if d <= spd: e['x'], e['y'] = x, y; return True
    e['x'] += dx/d*spd; e['y'] += dy/d*spd; return False

def command(p, c):
    pl = S['players'][p]; t = c.get('type')
    if S['winner'] is not None: return
    if t == 'build':
        k = c['what']
        if k in B and k != 'cy' and pl['bq'] is None and pl['ready'] is None and has(p, 'cy') and all(has(p, q) for q in B[k]['pre']) and pl['credits'] >= B[k]['cost']:
            pl['credits'] -= B[k]['cost']; pl['bq'] = [k, 0.0]
    elif t == 'place':
        k = pl['ready']
        if not k: return
        x, y = float(c['x']), float(c['y']); s = B[k]['size']
        if not (s/2 < x < W-s/2 and s/2 < y < H-s/2): return
        near = any(e['o']==p and e['b'] and dist(e, {'x':x,'y':y}) < 260 for e in S['ents'].values())
        clash = any(abs(e['x']-x) < rad(e)+s/2 and abs(e['y']-y) < rad(e)+s/2 for e in S['ents'].values() if e['b'] or not U[e['k']].get('air'))
        h = s/2
        clash = clash or any(static[cy*GW+cx] for cy in range(max(0, int((y-h)//CELL)), min(GH, int((y+h)//CELL)+1)) for cx in range(max(0, int((x-h)//CELL)), min(GW, int((x+h)//CELL)+1)))
        if near and not clash:
            add_b(p, k, x, y); pl['ready'] = None
    elif t == 'cancel':
        if pl['bq']: pl['credits'] += B[pl['bq'][0]]['cost']; pl['bq'] = None
        elif pl['ready']: pl['credits'] += B[pl['ready']]['cost']; pl['ready'] = None
    elif t == 'train':
        k = c['what']
        if k in U and has(p, U[k]['at']) and all(has(p, q) for q in U[k].get('pre', [])) and pl['credits'] >= U[k]['cost'] and len(pl['uq'][U[k]['at']]) < 10:
            pl['credits'] -= U[k]['cost']; pl['uq'][U[k]['at']].append([k, 0.0])
    elif t in ('move', 'attack', 'amove'):
        tg = S['ents'].get(c.get('target'))
        ids = c.get('ids', [])
        n = len(ids); cols = max(1, int(math.sqrt(n)))
        for i, uid in enumerate(ids):
            e = S['ents'].get(uid)
            if not e or e['o'] != p or e['b']: continue
            if e['k'] == 'harvester':
                if t != 'attack': e['st'] = 'manual'; e['mx'], e['my'] = c['x'], c['y']; stop(e)
                continue
            stop(e); e['am'] = (t == 'amove'); e['hitby'] = None
            if e['k'] == 'engineer':
                if t == 'attack' and tg and tg['o'] != p and tg['b'] and tg['k'] != 'wall': e['tgt'] = tg['id']; e['mx'] = None
                else: e['tgt'] = None; e['mx'], e['my'] = c['x'], c['y']; e['am'] = False
                continue
            if t == 'attack' and tg and tg['o'] != p:
                e['tgt'] = tg['id']; e['mx'] = None; e['force'] = True
            else:
                e['tgt'] = None; e['force'] = True
                e['mx'] = c['x'] + (i % cols - cols/2)*24; e['my'] = c['y'] + (i // cols - cols/2)*24
    elif t == 'sell':
        e = S['ents'].get(c.get('id'))
        if e and e['o']==p and e['b'] and e['k']!='cy':
            pl['credits'] += B[e['k']]['cost']//2; del S['ents'][e['id']]

def cls(e): return 'bld' if e['b'] else U[e['k']]['cls']
def spec(e): return B[e['k']] if e['b'] else U[e['k']]

def nearest_enemy(e, rng, vs):
    best, bd = None, rng
    for o in S['ents'].values():
        if o['o'] != e['o'] and vs[cls(o)] > 0 and not (o['b'] and o['k'] == 'wall' and not e['b']):
            d = dist(e, o) - rad(o)
            if d < bd: best, bd = o, d
    return best

def shoot(e, tgt):
    w = spec(e)
    if e['cd'] <= 0:
        tgt['hp'] -= w['dmg']*w['vs'][cls(tgt)]; e['cd'] = w['rof']; tgt['hitby'] = e['id']
        if w.get('splash'):
            for o in S['ents'].values():
                if o is not tgt and o['o'] != e['o'] and cls(o) != 'air' and dist(o, tgt) < w['splash']:
                    o['hp'] -= w['dmg']*.5*w['vs'][cls(o)]
        S['shots'].append([round(e['x']), round(e['y']), round(tgt['x']), round(tgt['y']), e['o'], w['fx']])

def fly(e, x, y, spd): return move_to(e, x, y, spd)

def step():
    S['tick'] += 1; S['shots'] = []
    if S['winner'] is not None: return
    rebuild_grid()
    for p, pl in enumerate(S['players']):
        prod, use = power(p); slow = 1.0 if prod >= use else 0.4
        if pl['bq']:
            pl['bq'][1] += TICK*slow / B[pl['bq'][0]]['t']
            if pl['bq'][1] >= 1: pl['ready'] = pl['bq'][0]; pl['bq'] = None
        for at, q in pl['uq'].items():
            if q:
                spawners = [e for e in S['ents'].values() if e['o']==p and e['b'] and e['k']==at]
                if not spawners: continue
                q[0][1] += TICK*slow / U[q[0][0]]['t']
                if q[0][1] >= 1:
                    k = q.pop(0)[0]; sp = spawners[0]; rebuild_grid()
                    if U[k].get('air'): u = add_u(p, k, sp['x'], sp['y'])
                    else:
                        fx, fy = nearest_free(*cell(sp['x'], sp['y'] + (B[at]['size']/2+15)*(1 if p==0 else -1)))
                        u = add_u(p, k, fx*CELL+CELL/2, fy*CELL+CELL/2)
                    if k != 'harvester': u['mx'], u['my'] = u['x'] + random.uniform(-40,40), u['y'] + (50 if p==0 else -50)
    for e in list(S['ents'].values()):
        if e['cd'] > 0: e['cd'] -= 1
        if e['b']:
            bs = B[e['k']]
            if 'dmg' in bs:
                prod, use = power(e['o'])
                if prod >= use:
                    t = nearest_enemy(e, bs['rng'], bs['vs'])
                    if t: shoot(e, t)
            elif e['k'] == 'repair' and S['tick'] % 3 == 0:
                for o in S['ents'].values():
                    if o['o'] == e['o'] and not o['b'] and U[o['k']]['cls'] != 'inf' and o['hp'] < U[o['k']]['hp'] and dist(o, e) < 75 and S['players'][o['o']]['credits'] >= 2:
                        o['hp'] = min(U[o['k']]['hp'], o['hp'] + 12); S['players'][o['o']]['credits'] -= 2
            continue
        u = U[e['k']]
        if e['k'] == 'harvester':
            harvest(e, u); continue
        tgt = S['ents'].get(e['tgt']) if e['tgt'] else None
        go = fly if u.get('air') else nav
        if e['k'] == 'engineer':
            if tgt and tgt['o'] != e['o']:
                if dist(e, tgt) - rad(tgt) <= 32:
                    tgt['o'] = e['o']; tgt['hitby'] = None; e['hp'] = 0  # captured!
                else: nav(e, tgt['x'], tgt['y'], u['spd'])
            else:
                e['tgt'] = None
                if e['mx'] is not None and nav(e, e['mx'], e['my'], u['spd']): e['mx'] = None
            continue
        if e['mx'] is not None and not e['am']:  # plain move: ignore enemies
            if go(e, e['mx'], e['my'], u['spd']): e['mx'] = None; e['force'] = False
            continue
        if tgt is None:
            tgt = nearest_enemy(e, u['rng'] + 60, u['vs'])
            att = S['ents'].get(e['hitby'] or -1)
            if tgt is None and att and att['o'] != e['o'] and u['vs'][cls(att)] > 0 and dist(e, att) < u['rng'] + 250: tgt = att  # return fire
            e['hitby'] = None
            if tgt: e['tgt'] = tgt['id']; e['force'] = False; stop(e)
        if tgt:
            if u['vs'][cls(tgt)] <= 0: e['tgt'] = None
            elif dist(e, tgt) - rad(tgt) <= u['rng']: shoot(e, tgt); stop(e)
            elif not e['force'] and dist(e, tgt) > u['rng'] + 260: e['tgt'] = None; stop(e)
            else: go(e, tgt['x'], tgt['y'], u['spd'])
        elif e['mx'] is not None:
            if go(e, e['mx'], e['my'], u['spd']): e['mx'] = None; e['am'] = False
    # separation
    us = [e for e in S['ents'].values() if not e['b']]
    for i, a in enumerate(us):
        for b in us[i+1:]:
            if U[a['k']].get('air') != U[b['k']].get('air'): continue
            if U[a['k']].get('air'):
                d = dist(a, b)
                if 0 < d < 26: a['x'] += (a['x']-b['x'])/d; a['y'] += (a['y']-b['y'])/d
                continue
            d = dist(a, b); m = rad(a)+rad(b)
            if 0 < d < m:
                push = (m-d)/2/d
                dx, dy = (a['x']-b['x'])*push, (a['y']-b['y'])*push
                if not blocked(a['x']+dx, a['y']+dy): a['x'] += dx; a['y'] += dy
                if not blocked(b['x']-dx, b['y']-dy): b['x'] -= dx; b['y'] -= dy
    for e in list(S['ents'].values()):
        e['x'] = min(max(e['x'], 5), W-5); e['y'] = min(max(e['y'], 5), H-5)
        if e['hp'] <= 0: del S['ents'][e['id']]
    S['fields'] = [f for f in S['fields'] if f['amt'] > 0]
    for p in (0, 1):
        if not any(e['o']==p and e['b'] and e['k'] != 'wall' for e in S['ents'].values()):
            S['winner'] = 1-p

def harvest(e, u):
    if e['st'] == 'manual':
        if nav(e, e['mx'], e['my'], u['spd']): e['st'] = 'idle'
        return
    if e['cargo'] >= 500 or (e['st'] == 'return'):
        refs = [r for r in S['ents'].values() if r['o']==e['o'] and r['b'] and r['k']=='refinery']
        if not refs: e['st'] = 'idle'; return
        r = min(refs, key=lambda r: dist(e, r)); e['st'] = 'return'
        if dist(e, r) < B['refinery']['size']/2 + 30:
            S['players'][e['o']]['credits'] += e['cargo']; e['cargo'] = 0; e['st'] = 'idle'; stop(e)
        else: nav(e, r['x'], r['y'], u['spd'])
        return
    if not S['fields']: return
    f = S['fields'] and min(S['fields'], key=lambda f: dist(e, f) + (0 if f is e.get('fld') else 15))
    e['fld'] = f
    if dist(e, f) < 8:
        take = min(10, f['amt'], 500-e['cargo']); f['amt'] -= take; e['cargo'] += take
        if e['cargo'] >= 500: e['st'] = 'return'
    else: nav(e, f['x'], f['y'], u['spd'])

def snapshot():
    pls = []
    for p, pl in enumerate(S['players']):
        prod, use = power(p)
        pls.append(dict(credits=int(pl['credits']), joined=conns[p] > 0, bq=pl['bq'], ready=pl['ready'], uq=pl['uq'], power=[prod, use]))
    return json.dumps(dict(
        players=pls, winner=S['winner'], mapv=S['mapv'], shots=S.get('shots', []),
        ents=[[e['id'], e['o'], e['k'], e['b'], round(e['x']), round(e['y']), int(e['hp']), e.get('cargo',0)] for e in S['ents'].values()],
        fields=[[round(f['x']), round(f['y']), f['amt']] for f in S['fields']]))

def loop():
    global SNAP
    while True:
        t0 = time.time()
        with lock: step(); SNAP = snapshot()
        cond_notify()
        time.sleep(max(0, TICK-(time.time()-t0)))

cv = threading.Condition()
conns = [0, 0]; seen = [0.0, 0.0]
def cond_notify():
    with cv: cv.notify_all()

class H_(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *a): pass
    def send(self, code, body, ctype='application/json'):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', len(b)); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send(200, open(__file__.replace('server.py', 'index.html'), 'rb').read(), 'text/html')
        elif self.path == '/map':
            with lock: self.send(200, json.dumps(dict(obs=S['obs'], mapv=S['mapv'])))
        elif self.path == '/join':
            with lock:
                for p in (0, 1):
                    # a slot is free when nobody has been streaming it for a few seconds
                    if conns[p] == 0 and time.time() - seen[p] > 4:
                        seen[p] = time.time()
                        return self.send(200, json.dumps(dict(pid=p, W=W, H=H, B=B, U=U)))
            self.send(200, json.dumps(dict(pid=-1, W=W, H=H, B=B, U=U)))
        elif self.path.startswith('/stream'):
            try: sp = int(self.path.split('pid=')[1])
            except Exception: sp = -1
            if sp in (0, 1):
                with lock: conns[sp] += 1
            try: self.stream()
            finally:
                if sp in (0, 1):
                    with lock: conns[sp] -= 1; seen[sp] = time.time()
        else: self.send(404, '')
    def stream(self):
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.send_header('Cache-Control', 'no-cache'); self.send_header('Connection', 'keep-alive'); self.end_headers()
        try:
            while True:
                with cv: cv.wait(1)
                self.wfile.write(('data: ' + SNAP + '\n\n').encode()); self.wfile.flush()
        except Exception: pass
    def do_POST(self):
        c = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        with lock:
            if c.get('type') == 'reset': reset()
            elif c.get('pid') in (0, 1): command(c['pid'], c)
        self.send(200, '{}')

reset(); SNAP = snapshot()
threading.Thread(target=loop, daemon=True).start()
if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8077
    print(f'C&C server on http://0.0.0.0:{port}')
    ThreadingHTTPServer(('0.0.0.0', port), H_).serve_forever()
