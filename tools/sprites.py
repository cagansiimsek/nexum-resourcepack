"""Item sprite designs for the 2026-11-12 texture needs list (groups C-J).

Every sprite is drawn natively on a 32x32 grid by the helpers in pixel.py.
Deterministic: no randomness outside fixed seeds.
"""
import math
import random
from pixel import (Spr, ramp, mix, scale, col, m_rect, m_ell, m_circ, m_poly, m_line, m_tube, m_leaf, bez, edge)

GOLD = ramp((222, 172, 52))
BRONZE = ramp((176, 118, 58))
IRON = ramp((158, 164, 170))
LEATHER = ramp((126, 78, 46))
WOOD = ramp((156, 108, 58))
TIER_GLOW = {1: (122, 196, 84), 2: (164, 196, 58), 3: (240, 120, 40), 4: (178, 96, 236)}


def pips(s, tier, x=2, y=2):
    """Tier mark: 1-4 small gold studs in the upper left (stack counts sit lower right)."""
    for i in range(tier):
        px = x + i * 4
        s.put(px, y, GOLD[4]); s.put(px + 1, y, GOLD[3]); s.put(px, y + 1, GOLD[3]); s.put(px + 1, y + 1, GOLD[1])


# ============================================================== C. logs
def logs(bark, wood, ring, tier, deco=(), seed=1):
    s = Spr(); br = ramp(bark); wr = ramp(wood); rg = col(ring)
    rng = random.Random(seed)

    def log(cx, cy, r=5, d=3):
        ext = set()
        for k in range(1, d + 1):
            ext |= m_circ(cx + k, cy - k, r)
        s.shade(ext, br)
        for (x, y) in ext:
            if (x + y) % 3 == 0 and not edge(ext, (x, y), (0, -1)) and not edge(ext, (x, y), (1, 0)):
                s.put(x, y, br[1])
            if 'birch' in deco and (x * 5 + y * 3) % 11 == 0:
                s.put(x, y, (40, 38, 34)); s.put(x + 1, y - 1, (40, 38, 34))
        top_edge = [p for p in ext if edge(ext, p, (0, -1)) or edge(ext, p, (-1, -1))]
        for (x, y) in top_edge:
            if 'moss' in deco and (x * 7 + y * 3) % 3 != 0:
                s.put(x, y, (96, 150, 62) if (x + y) % 2 else (70, 118, 50))
            if 'frost' in deco and (x * 5 + y) % 2 == 0:
                s.put(x, y, (226, 238, 244))
        if 'glow' in deco:
            for _ in range(4):
                x, y = rng.choice(sorted(ext))
                s.put(x, y, (150, 246, 232))
        face = m_circ(cx, cy, r)
        for (x, y) in face:
            d2 = math.hypot(x - cx, y - cy)
            if edge(face, (x, y), (1, 0)) or edge(face, (x, y), (0, 1)):
                c = br[0]
            elif edge(face, (x, y), (-1, 0)) or edge(face, (x, y), (0, -1)):
                c = br[1]
            elif abs(d2 - (r - 2.4)) < 0.55 or d2 < 0.8:
                c = rg
            elif (x - cx) + (y - cy) < -3:
                c = wr[3]
            elif (x - cx) + (y - cy) > 3:
                c = wr[1]
            else:
                c = wr[2]
            s.put(x, y, c)

    log(8, 23); log(19, 23); log(13, 13)
    pips(s, tier, 2, 2)
    return s


# ============================================================== D. herbs
def herb(kind):
    s = Spr()
    green = ramp((96, 164, 72)); stem = (70, 120, 52)
    if kind == 'fieldmint':
        mint = ramp((104, 200, 128))
        s.fill(m_line([(16, 29), (16, 20), (15, 12), (16, 5)], 2), stem)
        for y, sz in ((22, 7), (15, 6), (9, 5)):
            L = s.shade(m_leaf((16, y + 1), (16 - sz - 3, y - 2), 5), mint)
            R = s.shade(m_leaf((17, y + 1), (17 + sz + 3, y - 2), 5), mint)
            s.fill(m_line([(15, y + 1), (16 - sz, y - 1)]), mint[1])
            s.fill(m_line([(18, y + 1), (17 + sz, y - 1)]), mint[1])
        s.shade(m_ell(13, 2, 19, 6), mint); s.put(15, 3, mint[4])
    elif kind == 'wild_fiber':
        fib = [(204, 190, 112), (168, 170, 82), (140, 150, 70), (220, 206, 140)]
        for i, (bx, tx) in enumerate(((11, 5), (13, 9), (15, 13), (17, 18), (19, 23), (21, 27), (14, 16), (18, 11))):
            pts = bez((bx, 29), (16 + (bx - 16) * 0.2, 17), (tx, 3 + (i % 3)))
            s.fill(m_line(pts[::4] + [pts[-1]], 1), fib[i % 4])
        s.shade(m_rect(12, 16, 20, 19), LEATHER)
        s.fill(m_line([(12, 17), (20, 17)]), LEATHER[3])
    elif kind == 'heartroot':
        red = ramp((196, 46, 66))
        s.fill(m_line([(16, 9), (16, 13)], 2), stem)
        s.shade(m_leaf((16, 10), (8, 3), 5), green); s.shade(m_leaf((17, 10), (25, 4), 5), green)
        heart = m_circ(12, 17, 4.6) | m_circ(20, 17, 4.6) | m_poly([(7, 18), (25, 18), (16, 28)])
        s.sphere(heart, red, 15, 18, 9)
        for p in ((11, 16), (12, 15), (19, 15)):
            s.put(*p, red[4])
        s.fill(m_line([(16, 27), (15, 30)]), (150, 92, 60))
        s.fill(m_line([(13, 25), (10, 29)]), (150, 92, 60))
        s.fill(m_line([(19, 25), (22, 29)]), (150, 92, 60))
    elif kind == 'marsh_reed':
        blade = ramp((112, 156, 70)); head = ramp((128, 76, 42))
        s.fill(m_line(bez((14, 29), (9, 18), (4, 9))[::5] + [(4, 9)], 2), blade[1])
        s.fill(m_line(bez((18, 29), (24, 20), (27, 13))[::5] + [(27, 13)], 2), blade[2])
        s.fill(m_line([(12, 29), (12, 2)], 1), blade[3]); s.fill(m_line([(19, 29), (20, 6)], 1), blade[2])
        s.shade(m_ell(10, 6, 14, 17), head); s.shade(m_ell(18, 10, 22, 21), head)
        s.put(11, 7, head[4]); s.put(19, 11, head[4])
    elif kind == 'ironbloom':
        steel = ramp((164, 180, 196)); core = ramp((86, 84, 96))
        s.fill(m_line([(16, 29), (16, 15)], 2), (78, 100, 82))
        s.shade(m_leaf((16, 24), (8, 19), 5), ramp((104, 132, 110)))
        s.shade(m_leaf((17, 22), (25, 17), 5), ramp((104, 132, 110)))
        for (px, py) in ((16, 5), (9, 9), (23, 9), (11, 16), (21, 16)):
            pet = m_leaf((16, 11), (px, py), 6)
            s.shade(pet, steel)
        s.sphere(m_circ(16, 11, 2.4), core, 16, 11, 2.4)
        s.put(15, 10, (230, 236, 244))
    elif kind == 'embercap':
        ember = ramp((226, 82, 34)); stalk = ramp((222, 202, 160))
        s.shade(m_poly([(13, 18), (19, 18), (20, 28), (12, 28)]), stalk)
        cap = {p for p in m_ell(4, 5, 27, 24) if p[1] <= 16}
        s.shade(cap, ember)
        s.fill(m_rect(6, 16, 25, 17), (128, 46, 30))
        for (x, y) in ((10, 9), (16, 7), (21, 10), (13, 13), (19, 14), (8, 13), (24, 14)):
            s.put(x, y, (255, 214, 84)); s.put(x + 1, y, (255, 178, 60))
        s.put(15, 6, (255, 236, 160))
    elif kind == 'crownpetal':
        gold = ramp((236, 184, 52))
        s.fill(m_line([(16, 29), (16, 17)], 2), stem)
        s.shade(m_leaf((16, 25), (8, 20), 5), green); s.shade(m_leaf((17, 24), (25, 19), 5), green)
        crown = m_poly([(7, 18), (7, 8), (10, 12), (13, 4), (16, 11), (19, 4), (22, 12), (25, 8), (25, 18), (21, 20), (11, 20)])
        s.shade(crown, gold)
        s.fill(m_rect(8, 16, 24, 17), gold[1])
        s.put(16, 14, (156, 64, 182)); s.put(17, 14, (110, 40, 140)); s.put(16, 13, (214, 140, 236))
        for p in ((7, 8), (13, 4), (19, 4), (25, 8)):
            s.put(*p, gold[4])
    elif kind == 'duskshade':
        bell = ramp((112, 58, 156)); leaf = ramp((62, 96, 70))
        s.fill(m_line(bez((9, 29), (8, 6), (24, 6))[::4] + [(24, 6)], 2), (58, 84, 58))
        s.shade(m_leaf((9, 24), (2, 18), 5), leaf); s.shade(m_leaf((10, 20), (17, 15), 5), leaf)
        for (bx, by) in ((14, 9), (20, 8), (25, 11)):
            b = m_poly([(bx - 1, by), (bx + 1, by), (bx + 3, by + 6), (bx - 3, by + 6)])
            s.shade(b, bell)
            for x in range(bx - 3, bx + 4):
                s.put(x, by + 6, bell[3])
        for (x, y) in ((7, 13), (9, 12), (8, 15)):
            s.sphere(m_circ(x, y, 1.2), ramp((60, 30, 84)), x, y, 1.2)
    return s


# ============================================================== E. drops
def drop(kind):
    s = Spr()
    if kind == 'feathered_crest':
        cream = ramp((232, 226, 200)); tip = ramp((112, 174, 72))
        for base, end in (((14, 26), (5, 6)), ((18, 26), (27, 6)), ((16, 26), (16, 2))):
            f = m_leaf(base, end, 7)
            s.shade(f, cream)
            bx, by = base; ex, ey = end
            for (x, y) in f:
                t = ((x - bx) * (ex - bx) + (y - by) * (ey - by)) / ((ex - bx) ** 2 + (ey - by) ** 2)
                if t > 0.55:
                    s.put(x, y, tip[2] if not edge(f, (x, y), (1, 0)) else tip[0])
                if 0.5 < t < 0.56 or 0.8 < t < 0.86:
                    s.put(x, y, tip[1])
            s.fill(m_line([base, end]), (150, 128, 90))
        s.shade(m_ell(12, 23, 20, 28), GOLD)
        s.put(16, 25, (196, 46, 66))
    elif kind == 'pasture_tusk':
        ivory = ramp((236, 226, 196))
        path = bez((8, 27), (10, 8), (26, 4))
        t = m_tube(path, 3.6, 0.6)
        s.shade(t, ivory)
        for i in (14, 22, 30):
            x, y = path[i]
            s.put(int(x), int(y), ivory[1])
        wrap = m_tube(path[:6], 4.0, 3.8)
        s.shade(wrap, ramp((92, 154, 64)))
        s.fill(m_line([(5, 26), (11, 25)]), (60, 104, 44)); s.fill(m_line([(5, 23), (11, 22)]), (60, 104, 44))
    elif kind == 'pasture_hide':
        hide = ramp((156, 108, 66))
        pelt = m_poly([(7, 6), (12, 8), (20, 8), (25, 6), (26, 12), (23, 16), (26, 25), (20, 26), (16, 24), (12, 26), (6, 25),
                       (9, 16), (6, 12)])
        s.shade(pelt, hide)
        for (x, y) in pelt:
            if (x * 3 + y * 5) % 7 == 0 and not edge(pelt, (x, y), (1, 0)):
                s.put(x, y, hide[3])
        for y in (14, 15):
            for x in range(8, 25):
                if (x, y) in pelt:
                    s.put(x, y, (110, 170, 72) if y == 14 else (78, 130, 54))
    elif kind == 'plague_ichor':
        glass = ramp((190, 214, 206)); ich = ramp((156, 196, 44))
        bulb = m_circ(16, 20, 8)
        s.sphere(bulb, glass, 16, 20, 8)
        s.shade(m_rect(13, 6, 19, 12), glass)
        liquid = {p for p in m_circ(16, 20, 6.4) if p[1] >= 17}
        s.sphere(liquid, ich, 16, 22, 6)
        for x in range(10, 23):
            if (x, 17) in liquid:
                s.put(x, 17, ich[4])
        for p in ((13, 21), (18, 23), (16, 19)):
            s.put(*p, (222, 244, 128))
        s.shade(m_rect(12, 3, 20, 6), ramp((150, 104, 62)))
        s.put(11, 16, glass[4]); s.put(11, 17, glass[4])
    elif kind == 'blighted_bone':
        bone = ramp((222, 214, 186))
        b = m_tube([(9 + i * 0.5, 23 - i * 0.5) for i in range(29)], 2.0, 2.0)
        b |= m_circ(7, 22, 2.6) | m_circ(10, 25, 2.6) | m_circ(22, 7, 2.6) | m_circ(25, 10, 2.6)
        s.shade(b, bone)
        for (x, y) in ((12, 19), (13, 19), (18, 13), (19, 12), (19, 13), (8, 24), (24, 9), (23, 8)):
            s.put(x, y, (132, 164, 58))
        for (x, y) in ((13, 20), (18, 12), (9, 23)):
            s.put(x, y, (80, 96, 40))
    elif kind == 'webbed_heart':
        red = ramp((150, 30, 48))
        heart = m_circ(11, 12, 6) | m_circ(21, 12, 6) | m_poly([(5, 14), (27, 14), (16, 28)])
        s.sphere(heart, red, 14, 14, 11)
        web = (226, 230, 216)
        for line in ([(5, 9), (27, 22)], [(8, 25), (25, 6)], [(16, 6), (16, 28)], [(4, 15), (28, 15)]):
            for p in m_line(line):
                if p in heart:
                    s.put(*p, web)
        for p in ((10, 9), (11, 9), (20, 20), (12, 21)):
            s.put(*p, (168, 210, 70))
    elif kind == 'ash_core':
        ash = ramp((118, 110, 108))
        ball = m_circ(16, 16, 10)
        s.sphere(ball, ash, 16, 16, 10)
        for path in ([(16, 16), (10, 9), (8, 8)], [(16, 16), (24, 12), (26, 10)], [(16, 16), (15, 24), (12, 26)],
                     [(16, 16), (22, 22)]):
            s.fill(m_line(path), (236, 112, 32))
        s.fill(m_circ(16, 16, 1.6), (255, 206, 84)); s.put(16, 16, (255, 244, 190))
    elif kind == 'molten_residue':
        rock = ramp((72, 58, 58)); lava = (236, 106, 30)
        blob = m_circ(11, 20, 7) | m_circ(21, 19, 7) | m_circ(16, 12, 6)
        s.shade(blob, rock)
        for path in ([(7, 20), (12, 17), (16, 13)], [(16, 13), (21, 18), (25, 19)], [(12, 17), (14, 24)]):
            s.fill(m_line(path), lava)
        for p in ((12, 17), (16, 13), (21, 18)):
            s.put(*p, (255, 200, 70))
        s.fill(m_line([(14, 25), (14, 28)]), lava); s.put(14, 29, (255, 200, 70))
    elif kind == 'cindered_skull':
        skull = ramp((128, 112, 100))
        head = m_circ(16, 13, 10) | m_rect(10, 18, 22, 26)
        s.shade(head, skull)
        for ex in (10, 18):
            eye = m_ell(ex, 12, ex + 4, 17)
            s.fill(eye, (36, 20, 18)); s.put(ex + 2, 14, (255, 150, 40)); s.put(ex + 2, 15, (236, 92, 26))
        s.fill(m_poly([(16, 18), (14, 21), (18, 21)]), (44, 28, 24))
        for x in range(11, 22, 2):
            s.put(x, 24, (52, 34, 30))
        s.fill(m_line([(19, 4), (21, 9), (24, 10)]), (236, 112, 32))
        s.fill(m_line([(8, 9), (11, 7)]), (236, 112, 32))
    elif kind == 'void_shard':
        v = ramp((146, 72, 208))
        shard = m_poly([(16, 2), (24, 12), (19, 29), (11, 25), (8, 11)])
        s.shade(shard, v)
        left = m_poly([(16, 2), (8, 11), (11, 25), (15, 16)])
        for p in left:
            if p in shard and not edge(shard, p, (-1, 0)):
                s.put(*p, v[3])
        s.fill(m_line([(16, 2), (15, 16), (19, 29)]), v[1])
        s.fill(m_line([(14, 10), (14, 17)], 2), (236, 196, 255))
        sm = m_poly([(25, 20), (28, 23), (25, 27), (23, 23)])
        s.shade(sm, v)
    elif kind == 'shulker_carapace':
        sh = ramp((156, 98, 156))
        shell = {p for p in m_ell(4, 5, 27, 34) if p[1] <= 24}
        s.shade(shell, sh)
        for y in (11, 17):
            for x in range(4, 28):
                if (x, y) in shell and not edge(shell, (x, y), (-1, 0)) and not edge(shell, (x, y), (1, 0)):
                    s.put(x, y, sh[1])
        for x in range(5, 27):
            if (x, 22) in shell:
                s.put(x, 22, (50, 30, 54)); s.put(x, 23, sh[0])
        for x in range(7, 25, 4):
            s.put(x, 8, sh[4])
    return s


# ============================================================== F. eggs
def egg(base, spot, extra=None):
    s = Spr(); r = ramp(base)
    shape = m_ell(8, 9, 24, 29) | m_ell(10, 3, 22, 21)
    s.sphere(shape, r, 16, 17, 11)
    rng = random.Random(base[0] * 7 + base[1])
    spots = [(12, 8), (19, 10), (10, 16), (16, 14), (21, 18), (13, 22), (18, 25), (11, 26), (22, 24), (15, 5)]
    for (x, y) in spots:
        if (x, y) in shape:
            s.put(x, y, spot); s.put(x + 1, y, mix(spot, base, 0.4))
            if (x, y + 1) in shape:
                s.put(x, y + 1, mix(spot, base, 0.55))
    if extra == 'crown':
        g = GOLD
        crown = m_poly([(11, 8), (11, 4), (13, 6), (16, 3), (19, 6), (21, 4), (21, 8)])
        s.shade(crown, g); s.put(16, 5, (210, 60, 80))
    if extra == 'cracks':
        s.fill(m_line([(12, 12), (14, 15), (12, 18)]), (255, 126, 36))
        s.fill(m_line([(20, 20), (18, 23), (20, 26)]), (255, 126, 36))
    return s


# ============================================================== G. automatons
def automaton(tool, accent):
    s = Spr(); bz = ramp((192, 134, 62)); ac = col(accent)
    draw_tool_small(s, tool)
    s.shade(m_rect(9, 26, 11, 28), bz); s.shade(m_rect(14, 26, 16, 28), bz)
    body = m_rect(7, 17, 18, 26)
    s.shade(body, bz)
    gear = m_circ(12, 21, 2.3)
    s.fill(gear, bz[1]); s.put(12, 21, ac); s.put(11, 20, ac)
    for (x, y) in ((12, 18), (12, 24), (9, 21), (15, 21)):
        s.put(x, y, bz[0])
    s.shade(m_circ(19, 20, 1.6), bz)
    head = m_rect(6, 6, 19, 16) - {(6, 6), (19, 6), (6, 16), (19, 16)}
    s.shade(head, bz)
    face = m_rect(8, 9, 17, 14)
    s.fill(face, (62, 48, 44))
    for ex in (9, 14):
        s.fill(m_rect(ex, 10, ex + 2, 12), ac); s.put(ex, 10, mix(ac, (255, 255, 255), 0.6))
    s.fill(m_rect(11, 13, 14, 13), bz[1])
    s.fill(m_line([(12, 5), (12, 3)]), bz[0]); s.shade(m_circ(12, 2, 1.2) | {(12, 2)}, ramp(accent))
    s.fill(m_rect(4, 9, 5, 12), bz[1]); s.put(3, 10, bz[0]); s.put(3, 11, bz[0])
    return s


def draw_tool_small(s, tool):
    wood = ramp((150, 102, 56))
    s.fill(m_line([(19, 25), (27, 6)], 2), wood[2])
    s.fill(m_line([(20, 25), (28, 6)]), wood[1])
    if tool == 'hoe':
        s.shade(m_rect(22, 4, 29, 6), IRON); s.shade(m_rect(22, 6, 23, 9), IRON)
    elif tool == 'pick':
        pick = m_tube(bez((20, 9), (25, 2), (29, 9)), 1.1, 0.7)
        s.shade(pick, IRON)
    elif tool == 'axe':
        s.shade(m_poly([(25, 3), (30, 2), (30, 12), (25, 10)]), IRON)
        s.fill(m_line([(30, 3), (30, 11)]), IRON[4])
    elif tool == 'sword':
        blade = m_line([(20, 22), (28, 3)], 2)
        s.shade(blade, IRON)
        s.shade(m_line([(17, 20), (24, 23)], 2), GOLD)


# ============================================================== H. tools
def handle(s, a, b, wrap=True):
    wood = ramp((150, 102, 56))
    s.shade(m_line([a, b], 3), wood)
    if wrap:
        ax, ay = a
        s.shade(m_line([(ax, ay), (ax + 5, ay - 5)], 3), LEATHER)
        for i in range(0, 5, 2):
            s.put(ax + i + 1, ay - i, LEATHER[3])


def tool(kind):
    s = Spr()
    if kind == 'pickaxe':
        handle(s, (5, 27), (20, 12))
        head = m_tube(bez((5, 8), (24, 4), (27, 25)), 2.4, 1.4)
        s.shade(head, IRON)
        s.shade(m_circ(20, 11, 2.6), BRONZE)
        s.put(19, 10, BRONZE[4])
    elif kind == 'axe':
        handle(s, (6, 28), (22, 12))
        blade = m_poly([(9, 11), (10, 5), (14, 2), (18, 3), (21, 7), (16, 12), (12, 14)])
        s.shade(blade, IRON)
        s.fill(m_line([(9, 11), (10, 5), (14, 2)]), IRON[4])
        s.fill(m_line([(10, 12), (11, 6), (14, 3)]), IRON[3])
        s.shade(m_poly([(18, 6), (22, 4), (26, 8), (22, 13), (18, 11)]), IRON)
        s.shade(m_rect(18, 8, 22, 12), BRONZE)
        s.put(19, 9, BRONZE[4]); s.put(21, 11, BRONZE[0])
    elif kind == 'sickle':
        handle(s, (6, 28), (13, 21))
        blade = m_tube(bez((13, 21), (31, 12), (21, 3)), 2.2, 0.6) | m_tube(bez((21, 3), (15, 3), (11, 8)), 1.0, 0.5)
        s.shade(blade, IRON)
        s.shade(m_circ(13, 21, 2.2), BRONZE)
    return s


# ============================================================== I. parts and food
def bowl(content, garnish=(), steam=False):
    s = Spr(); w = ramp((150, 100, 56)); c = ramp(content)
    body = {p for p in m_ell(4, 10, 27, 29) if p[1] >= 18}
    s.shade(body, w)
    rim = m_ell(4, 13, 27, 22)
    s.fill(rim, w[3])
    inner = m_ell(6, 14, 25, 21)
    s.shade(inner, c)
    for (x, y, k) in garnish:
        s.put(x, y, k)
    for x in range(8, 24, 5):
        s.put(x, 25, w[1])
    if steam:
        for (x, y) in ((11, 11), (12, 10), (11, 9), (12, 8), (19, 10), (20, 9), (19, 8), (20, 7)):
            s.put(x, y, (232, 232, 236))
    return s


def roll(cloth, stripe=None, mark=None, leaf=None):
    s = Spr(); r = ramp(cloth)
    tail = m_poly([(12, 20), (28, 24), (27, 28), (11, 24)])
    s.shade(tail, r)
    for x in range(14, 27, 4):
        s.put(x, 23 + (x - 14) // 4, r[1])
    body = m_circ(12, 16, 8)
    s.sphere(body, r, 12, 16, 8)
    for rad in (5.2, 2.6):
        for p in m_circ(12, 16, rad) - m_circ(12, 16, rad - 1):
            s.put(*p, r[1])
    s.put(12, 16, r[0])
    if stripe:
        for p in m_line([(13, 22), (27, 26)]):
            s.put(*p, stripe)
    if mark == 'rune':
        for p in ((20, 23), (21, 22), (22, 23), (21, 24), (23, 25), (24, 24), (25, 25)):
            s.put(*p, (86, 150, 236))
    if leaf:
        s.shade(m_leaf((16, 10), (24, 3), 4), ramp(leaf))
    return s


def grip(wrap, guard, pommel, gem=None):
    s = Spr(); wr = ramp(wrap); gr = ramp(guard); pr = ramp(pommel)
    s.shade(m_line([(22, 10), (26, 6)], 3), IRON)
    s.shade(m_line([(9, 23), (20, 12)], 3), wr)
    for i in range(0, 11, 2):
        s.put(10 + i, 22 - i, wr[0])
    s.shade(m_line([(16, 9), (24, 17)], 3), gr)
    s.sphere(m_circ(7, 25, 2.6), pr, 7, 25, 2.6)
    if gem:
        s.put(7, 25, gem); s.put(6, 24, mix(gem, (255, 255, 255), 0.5))
        s.put(20, 13, gem)
    return s


def timber(wood, bands=None, glow=None, tar=False):
    s = Spr(); r = ramp(wood)
    beam = m_poly([(4, 22), (22, 4), (28, 10), (10, 28)])
    s.shade(beam, r)
    for k in range(3):
        for p in m_line([(7 + k * 2, 22 + k * 2), (22 + k * 2, 7 + k * 2)]):
            if p in beam:
                s.put(*p, r[1])
    end = m_poly([(4, 22), (10, 28), (8, 30), (2, 24)])
    s.fill(end, mix(r[3], (230, 200, 150), 0.3))
    for p in ((5, 25), (6, 26), (7, 27)):
        s.put(*p, r[1])
    if tar:
        for p in m_line([(8, 21), (21, 8)]):
            if p in beam:
                s.put(*p, mix(r[3], (255, 236, 190), 0.35))
        for (x, y) in ((12, 23), (12, 24), (19, 16), (19, 17), (19, 18)):
            s.put(x, y, (40, 30, 26))
    if bands:
        b = ramp(bands)
        for c in (-8, 8):
            band = {(x, y) for (x, y) in beam if c <= x - y <= c + 2}
            s.shade(band, b)
    if glow:
        for p in ((15, 15), (16, 14), (14, 18), (19, 13)):
            s.put(*p, glow)
    return s


def plate(metal, trim, tier):
    s = Spr(); m = ramp(metal); t = ramp(trim)
    shape = m_poly([(6, 5), (26, 5), (27, 18), (16, 29), (5, 18)])
    s.shade(shape, m)
    for p in m_line([(16, 6), (16, 27)]):
        s.put(*p, m[3])
    for p in m_line([(17, 6), (17, 26)]):
        s.put(*p, m[1])
    for (x, y) in ((8, 8), (24, 8), (8, 17), (24, 17)):
        s.put(x, y, t[3]); s.put(x + 1, y + 1, t[0])
    top = m_rect(6, 5, 26, 6)
    s.shade(top, t)
    return s


def cloth_stack(cloth, accent=None, quilt=False, patches=False):
    s = Spr(); r = ramp(cloth)
    for i, y in enumerate((20, 14, 8)):
        layer = m_poly([(5, y + 3), (14, y - 1), (27, y + 3), (18, y + 7)]) | m_poly([(5, y + 3), (18, y + 7), (18, y + 9), (5, y + 5)]) | m_poly([(18, y + 7), (27, y + 3), (27, y + 5), (18, y + 9)])
        s.shade(layer, r)
        for p in m_line([(5, y + 4), (18, y + 8), (27, y + 4)]):
            s.put(*p, r[1])
        if accent:
            for p in m_line([(9, y + 5), (18, y + 9)]) if i < 2 else m_line([(9, y + 1), (20, y + 5)]):
                if p in layer:
                    s.put(*p, accent)
        if quilt and i == 2:
            for p in m_line([(9, y + 1), (18, y + 5)]) | m_line([(14, y + 4), (22, y)]):
                if p in layer:
                    s.put(*p, r[0])
        if patches and i == 2:
            s.fill(m_rect(15, y + 1, 18, y + 3), LEATHER[2]); s.put(15, y + 1, LEATHER[3])
    return s


def fittings(metal):
    s = Spr(); m = ramp(metal)
    bracket = m_rect(5, 6, 10, 26) | m_rect(5, 21, 22, 26)
    s.shade(bracket, m)
    for (x, y) in ((7, 9), (7, 15), (12, 23), (18, 23)):
        s.put(x, y, m[0]); s.put(x + 1, y, m[0]); s.put(x, y - 1, m[4])
    nut = m_poly([(19, 6), (24, 6), (27, 10), (24, 14), (19, 14), (16, 10)])
    s.shade(nut, m)
    s.fill(m_circ(21.5, 10, 1.6), m[0])
    bolt = m_rect(14, 15, 16, 19)
    s.shade(bolt, m)
    return s


def gear_part(metal, extra):
    s = Spr(); m = ramp(metal)
    teeth = set()
    for k in range(8):
        a = k * math.pi / 4
        teeth |= m_rect(13 + round(9 * math.cos(a)) - 1, 13 + round(9 * math.sin(a)) - 1, 13 + round(9 * math.cos(a)) + 1, 13 + round(9 * math.sin(a)) + 1)
    g = m_circ(13, 13, 7.5) | teeth
    s.shade(g, m)
    s.fill(m_circ(13, 13, 2.4), m[0]); s.put(12, 12, (30, 22, 26))
    if extra == 'plate':
        s.shade(m_rect(18, 20, 28, 28), IRON); s.put(20, 22, IRON[0]); s.put(26, 26, IRON[0])
    if extra == 'coil':
        coil = m_rect(19, 18, 27, 28)
        s.shade(coil, ramp((196, 110, 60)))
        for y in range(19, 28, 2):
            for x in range(19, 28):
                s.put(x, y, ramp((196, 110, 60))[1])
    return s


def frame(wood, corners=None):
    s = Spr(); r = ramp(wood)
    outer = m_rect(4, 4, 27, 27) - m_rect(8, 8, 23, 23)
    s.shade(outer, r)
    brace = m_line([(8, 22), (22, 8)], 3)
    s.shade(brace, r)
    for p in ((8, 8), (23, 23)):
        s.put(*p, r[0])
    if corners:
        c = ramp(corners)
        for (x, y) in ((4, 4), (23, 4), (4, 23), (23, 23)):
            s.shade(m_rect(x, y, x + 4, y + 4), c); s.put(x + 2, y + 2, c[0])
    return s


def sack(cloth, fill):
    s = Spr(); r = ramp(cloth)
    body = m_poly([(10, 11), (22, 11), (27, 19), (27, 27), (24, 29), (8, 29), (5, 27), (5, 19)])
    s.shade(body, r)
    for p in ((9, 16), (10, 17), (23, 16), (22, 17), (12, 27), (20, 27)):
        s.put(*p, r[1])
    ruff = m_poly([(10, 4), (13, 7), (16, 3), (19, 7), (22, 4), (22, 9), (10, 9)])
    s.shade(ruff, r)
    s.shade(m_ell(12, 2, 20, 6) & m_rect(0, 0, 31, 6), ramp(fill))
    s.shade(m_rect(11, 9, 21, 11), ramp((176, 132, 72)))
    s.put(12, 10, (220, 180, 110))
    wheat = ramp((214, 166, 64))
    s.fill(m_line([(16, 26), (16, 16)]), wheat[1])
    for y in (17, 20, 23):
        s.put(15, y, wheat[3]); s.put(17, y, wheat[3]); s.put(14, y - 1, wheat[2]); s.put(18, y - 1, wheat[2])
    s.put(16, 15, wheat[3])
    return s


def pack():
    s = Spr()
    body = m_rect(5, 10, 26, 28) - {(5, 10), (26, 10), (5, 28), (26, 28)}
    s.shade(body, LEATHER)
    s.shade(m_rect(5, 10, 26, 16), ramp((150, 96, 56)))
    s.fill(m_rect(14, 15, 17, 18), GOLD[2]); s.put(14, 15, GOLD[4])
    loaf = m_ell(7, 3, 17, 10)
    s.shade(loaf, ramp((214, 160, 82)))
    for x in (9, 12, 15):
        s.put(x, 5, (150, 96, 46))
    s.shade(m_rect(19, 4, 23, 10), ramp((196, 70, 52)))
    s.fill(m_line([(8, 20), (8, 27)]), LEATHER[0]); s.fill(m_line([(23, 20), (23, 27)]), LEATHER[0])
    return s


def briquettes():
    s = Spr(); r = ramp((58, 52, 56))
    for (x, y) in ((4, 18), (15, 18), (9, 9)):
        b = m_rect(x, y, x + 11, y + 8) - {(x, y), (x + 11, y), (x, y + 8), (x + 11, y + 8)}
        s.shade(b, r)
        for k in range(x + 2, x + 10, 3):
            s.put(k, y + 4, r[0])
    for p in ((7, 22), (18, 25), (13, 12)):
        s.put(*p, (236, 112, 40))
    s.put(19, 21, (255, 196, 80))
    return s


def coil():
    s = Spr(); cu = ramp((204, 114, 62)); rod = IRON
    s.shade(m_line([(5, 26), (26, 5)], 3), rod)
    for i in range(6):
        cx, cy = 9 + i * 2.6, 22 - i * 2.6
        s.shade(m_ell(cx - 3, cy - 3, cx + 2, cy + 2) - m_circ(cx - 0.5, cy - 0.5, 1.2), cu)
    for (x, y) in ((5, 26), (26, 5)):
        s.sphere(m_circ(x, y, 2.6), ramp((214, 40, 36)), x, y, 2.6)
        s.put(x - 1, y - 1, (255, 150, 140))
    return s


def gem_core():
    s = Spr()
    ring = m_circ(16, 16, 11) - m_circ(16, 16, 7.4)
    s.shade(ring, GOLD)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        s.shade(m_circ(16 + 9 * math.cos(a), 16 + 9 * math.sin(a), 1.6), ramp((60, 200, 190)))
    s.sphere(m_circ(16, 16, 6.5), ramp((70, 200, 212)), 16, 16, 6.5)
    s.fill(m_line([(13, 13), (16, 11)]), (210, 255, 250))
    return s


# ============================================================== J. armour and swords
ARMOUR = {1: ((204, 112, 62), (80, 164, 142)), 2: ((166, 172, 178), (176, 122, 62)),
          3: ((238, 190, 62), (190, 50, 64)), 4: ((70, 60, 78), (184, 100, 232))}


def armour(piece, tier):
    s = Spr(); base, trim = ARMOUR[tier]; m = ramp(base); t = ramp(trim)
    if piece == 'helmet':
        shape = m_poly([(6, 22), (6, 12), (9, 7), (14, 5), (18, 5), (23, 7), (26, 12), (26, 22)]) - m_rect(10, 16, 22, 23)
        s.shade(shape, m)
        for p in m_line([(16, 5), (16, 15)], 2):
            s.put(*p, t[2] if p[0] == 16 else t[1])
        s.fill(m_rect(6, 14, 9, 15), t[2]); s.fill(m_rect(23, 14, 26, 15), t[1])
    elif piece == 'chestplate':
        shape = m_poly([(4, 7), (12, 7), (13, 10), (19, 10), (20, 7), (28, 7), (28, 15), (24, 15), (24, 27), (8, 27), (8, 15), (4, 15)])
        s.shade(shape, m)
        s.fill(m_line([(13, 11), (16, 14), (19, 11)]), t[2])
        s.fill(m_rect(9, 22, 23, 23), t[2]); s.fill(m_rect(9, 23, 23, 23), t[1])
        s.fill(m_line([(16, 15), (16, 21)]), m[1])
    elif piece == 'leggings':
        shape = m_rect(7, 5, 24, 10) | m_rect(7, 10, 14, 28) | m_rect(17, 10, 24, 28)
        s.shade(shape, m)
        s.fill(m_rect(7, 7, 24, 8), t[2]); s.put(15, 7, t[4]); s.put(16, 7, t[4])
        s.fill(m_rect(8, 18, 13, 18), m[1]); s.fill(m_rect(18, 18, 23, 18), m[1])
    elif piece == 'boots':
        for ox in (0, 14):
            b = m_rect(5 + ox, 9, 12 + ox, 24) | m_rect(3 + ox, 20, 12 + ox, 25)
            s.shade(b, m)
            s.fill(m_rect(5 + ox, 10, 12 + ox, 11), t[2])
            s.fill(m_rect(3 + ox, 24, 12 + ox, 25), m[0])
    return s


def sword(tier):
    s = Spr(); base, trim = ARMOUR[tier]
    blade_c = base if tier != 4 else (96, 86, 108)
    b = ramp(blade_c); t = ramp(trim)
    blade = m_poly([(10, 19), (25, 4), (28, 3), (27, 6), (12, 21)])
    s.shade(blade, b)
    s.fill(m_line([(12, 19), (25, 6)]), b[4] if tier != 4 else (200, 150, 250))
    s.shade(m_line([(6, 17), (14, 25)], 2), t)
    s.shade(m_line([(5, 26), (10, 21)], 2), LEATHER)
    s.sphere(m_circ(4, 27, 1.8), t, 4, 27, 1.8)
    return s


# ============================================================== catalogue
WOODS = {
    'oak': ((112, 86, 52), (190, 152, 96), (148, 112, 66)),
    'birch': ((218, 216, 208), (216, 196, 134), (176, 150, 96)),
    'mangrove': ((92, 72, 54), (124, 56, 50), (92, 40, 38)),
    'spruce': ((64, 42, 22), (136, 100, 60), (102, 72, 40)),
    'dark_oak': ((62, 46, 28), (86, 58, 30), (60, 40, 20)),
    'pale_oak': ((96, 88, 88), (236, 224, 220), (200, 188, 186)),
}


def build_all():
    S = {}
    L = lambda w, tier, deco=(), seed=1: logs(*WOODS[w], tier, deco, seed)
    S['forest_t1_oak_logs'] = L('oak', 1)
    S['forest_t1_birch_logs'] = L('birch', 1, ('birch',))
    S['forest_t2_oak_logs'] = logs((92, 68, 40), (180, 140, 86), (132, 98, 56), 2)
    S['forest_t2_mangrove_logs'] = L('mangrove', 2)
    S['forest_t2_spruce_logs'] = L('spruce', 2)
    S['forest_t3_oak_logs'] = L('oak', 3, ('moss',))
    S['forest_t3_spruce_logs'] = L('spruce', 3, ('frost',))
    S['forest_t4_oak_logs'] = logs((84, 62, 38), (170, 126, 70), (120, 84, 44), 4, ('moss',), 4)
    S['forest_t4_dark_oak_logs'] = L('dark_oak', 4, ('moss',))
    S['forest_t4_pale_oak_logs'] = L('pale_oak', 4, ('glow',), 9)
    for k in ('fieldmint', 'wild_fiber', 'heartroot', 'marsh_reed', 'ironbloom', 'embercap', 'crownpetal', 'duskshade'):
        S[k] = herb(k)
    for k in ('feathered_crest', 'pasture_tusk', 'pasture_hide', 'plague_ichor', 'blighted_bone', 'webbed_heart',
              'ash_core', 'molten_residue', 'cindered_skull', 'void_shard', 'shulker_carapace'):
        S[k] = drop(k)
    S['pasture_guardian_egg'] = egg((96, 156, 70), (255, 236, 150))
    S['plaguebringer_egg'] = egg((86, 96, 44), (196, 246, 74))
    S['obsidian_colossus_egg'] = egg((40, 28, 58), (255, 132, 40), 'cracks')
    S['exiled_sovereign_egg'] = egg((112, 52, 150), (255, 214, 96), 'crown')
    S['minion_farming'] = automaton('hoe', (126, 214, 84))
    S['minion_mining'] = automaton('pick', (110, 214, 240))
    S['minion_forestry'] = automaton('axe', (226, 170, 70))
    S['minion_slaying'] = automaton('sword', (240, 74, 64))
    S['mining_pickaxe'] = tool('pickaxe')
    S['forestry_axe'] = tool('axe')
    S['foraging_sickle'] = tool('sickle')
    # I. parts and food
    S['flour'] = sack((232, 222, 196), (248, 246, 238))
    S['iron_fittings'] = fittings((160, 166, 172))
    S['reinforced_components'] = gear_part((150, 156, 164), 'plate')
    S['treated_timber'] = timber((98, 66, 42), tar=True)
    S['wooden_framework'] = frame((168, 120, 66))
    S['copper_fittings'] = fittings((206, 116, 64))
    S['copper_components'] = gear_part((206, 116, 64), 'coil')
    S['provision_pack'] = pack()
    S['coal_briquette'] = briquettes()
    S['gilded_fittings'] = fittings((230, 182, 56))
    S['conductive_assembly'] = coil()
    S['gemmed_core'] = gem_core()
    for tier in (1, 2, 3, 4):
        S[f'armour_plate_t{tier}'] = plate(*ARMOUR[tier], tier)
    S['reinforced_frame'] = frame((150, 104, 56), (160, 166, 172))
    S['seasoned_timber'] = timber((176, 128, 72))
    S['hardened_timber'] = timber((120, 80, 44), bands=(150, 156, 164))
    S['ancient_timber'] = timber((84, 58, 40), bands=(230, 182, 56), glow=(150, 246, 232))
    S['weapon_grip'] = grip((126, 78, 46), (150, 102, 56), (150, 102, 56))
    S['advanced_grip'] = grip((110, 66, 40), (160, 166, 172), (160, 166, 172))
    S['hardened_grip'] = grip((156, 46, 46), (176, 118, 58), (176, 118, 58))
    S['sovereign_grip'] = grip((60, 44, 70), (230, 182, 56), (230, 182, 56), (176, 92, 236))
    S['woven_cloth'] = cloth_stack((232, 222, 196))
    S['reinforced_cloth'] = cloth_stack((220, 206, 176), accent=(126, 78, 46), patches=True)
    S['armour_lining'] = cloth_stack((176, 128, 84), quilt=True)
    S['field_bandage'] = roll((238, 234, 224))
    S['heartroot_wrap'] = roll((238, 228, 220), stripe=(196, 46, 66), leaf=(96, 164, 72))
    S['warding_wrap'] = roll((232, 232, 236), stripe=(86, 150, 236), mark='rune')
    S['carrot_broth'] = bowl((236, 136, 52), [(10, 16, (255, 170, 60)), (11, 16, (200, 90, 30)), (18, 17, (255, 170, 60)),
                                               (19, 17, (200, 90, 30)), (14, 18, (90, 160, 60)), (21, 15, (90, 160, 60))], steam=True)
    S['hearty_stew'] = bowl((140, 82, 44), [(10, 16, (196, 120, 70)), (11, 17, (196, 120, 70)), (17, 16, (226, 196, 120)),
                                              (20, 18, (90, 150, 60)), (14, 19, (180, 70, 50)), (22, 16, (226, 196, 120))], steam=True)
    S['ironbloom_meal'] = bowl((116, 156, 104), [(12, 16, (190, 204, 220)), (13, 16, (230, 236, 244)), (12, 17, (150, 166, 186)),
                                                  (18, 17, (190, 204, 220)), (19, 16, (230, 236, 244)), (16, 19, (86, 84, 96))])
    S['embercap_meal'] = bowl((196, 120, 70), [(11, 16, (226, 82, 34)), (12, 16, (255, 214, 84)), (18, 18, (226, 82, 34)),
                                                (19, 18, (255, 214, 84)), (15, 17, (226, 82, 34))], steam=True)
    S['crownmeal'] = bowl((236, 196, 92), [(12, 15, (255, 236, 150)), (16, 16, (156, 64, 182)), (19, 17, (255, 236, 150)),
                                            (14, 18, (96, 164, 72)), (21, 15, (255, 236, 150))], steam=True)
    for tier in (1, 2, 3, 4):
        for piece in ('helmet', 'chestplate', 'leggings', 'boots'):
            S[f'armour_t{tier}_{piece}'] = armour(piece, tier)
    S['copper_sword'] = sword(1); S['iron_sword'] = sword(2); S['gilded_sword'] = sword(3); S['sovereign_sword'] = sword(4)
    return S


HANDHELD = {'mining_pickaxe', 'forestry_axe', 'foraging_sickle', 'copper_sword', 'iron_sword', 'gilded_sword', 'sovereign_sword'}
