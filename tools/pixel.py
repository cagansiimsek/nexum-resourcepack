"""Tiny native 32x32 pixel-art toolkit (no downscaling, no anti-aliasing).

Shapes are sets of (x, y) pixels. A sprite is drawn back to front, shaded with
upper-left light, then gets a 1-pixel dark contour and a <=16-colour palette.
"""
import math
from PIL import Image, ImageDraw

N = 32


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def col(c):
    return hexc(c) if isinstance(c, str) else tuple(int(v) for v in c)


def mix(a, b, t):
    a, b = col(a), col(b)
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))


def scale(c, k):
    c = col(c)
    return tuple(max(0, min(255, int(round(v * k)))) for v in c)


def ramp(base):
    """dark, mid-dark, base, light, highlight; shadows lean violet, lights lean warm."""
    b = col(base)
    return [mix(scale(b, 0.48), (36, 22, 52), 0.22), mix(scale(b, 0.74), (48, 30, 62), 0.08), b,
            mix(b, (255, 238, 196), 0.32), mix(b, (255, 250, 232), 0.62)]


# ---------------------------------------------------------------- masks
def m_rect(x0, y0, x1, y1):
    return {(x, y) for x in range(int(x0), int(x1) + 1) for y in range(int(y0), int(y1) + 1)}


def m_ell(x0, y0, x1, y1):
    """Filled ellipse inside the inclusive pixel box."""
    cx, cy = (x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2
    rx, ry = (x1 - x0 + 1) / 2, (y1 - y0 + 1) / 2
    out = set()
    for x in range(int(x0), int(x1) + 1):
        for y in range(int(y0), int(y1) + 1):
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0 + 0.08:
                out.add((x, y))
    return out


def m_circ(cx, cy, r):
    return {(x, y) for x in range(int(cx - r - 1), int(cx + r + 2)) for y in range(int(cy - r - 1), int(cy + r + 2))
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r * 0.8}


def m_poly(pts):
    im = Image.new('L', (N, N), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=255, outline=255)
    return {(x, y) for x in range(N) for y in range(N) if im.getpixel((x, y))}


def m_line(pts, w=1):
    out = set()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            out.add((x0, y0))
            if (x0, y0) == (x1, y1):
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy
    if w >= 2:
        out |= {(x + 1, y) for x, y in out}
    if w >= 3:
        out |= {(x, y + 1) for x, y in out}
    return out


def bez(p0, p1, p2, n=40):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


def m_tube(points, r0, r1):
    """Union of discs along a path, radius tapering r0 -> r1."""
    out = set()
    n = len(points) - 1
    for i, (x, y) in enumerate(points):
        r = r0 + (r1 - r0) * i / max(1, n)
        out |= m_circ(x, y, r) if r >= 0.75 else {(int(round(x)), int(round(y)))}
    return out


def m_leaf(p0, p1, w):
    """Pointed leaf / feather polygon from p0 (base) to p1 (tip) with max width w."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    pts_l, pts_r = [], []
    for t, k in ((0.15, 0.55), (0.35, 0.95), (0.6, 1.0), (0.82, 0.65)):
        cx, cy = x0 + dx * t, y0 + dy * t
        pts_l.append((cx + nx * w / 2 * k, cy + ny * w / 2 * k))
        pts_r.append((cx - nx * w / 2 * k, cy - ny * w / 2 * k))
    return m_poly([p0] + pts_l + [p1] + pts_r[::-1])


def edge(mask, p, d):
    return (p[0] + d[0], p[1] + d[1]) not in mask


# ---------------------------------------------------------------- sprite
class Spr:
    def __init__(self):
        self.c = {}

    def put(self, x, y, c):
        if 0 <= x < N and 0 <= y < N and c is not None:
            self.c[(int(x), int(y))] = col(c)

    def fill(self, mask, c):
        for p in mask:
            self.put(p[0], p[1], c)
        return mask

    def shade(self, mask, r, inner=True):
        """Pillow shading with light from the upper left."""
        for p in mask:
            ul = edge(mask, p, (0, -1)) or edge(mask, p, (-1, 0))
            dr = edge(mask, p, (0, 1)) or edge(mask, p, (1, 0))
            if dr and not ul:
                c = r[0]
            elif dr and ul:
                c = r[1]
            elif ul:
                c = r[3]
            elif inner and (edge(mask, p, (1, 1)) or edge(mask, p, (2, 0)) or edge(mask, p, (0, 2))):
                c = r[1]
            else:
                c = r[2]
            self.put(p[0], p[1], c)
        return mask

    def sphere(self, mask, r, cx, cy, rad):
        """Radial shading for round things: highlight upper left, shadow lower right."""
        lx, ly, lz = -0.55, -0.62, 0.56
        for (x, y) in mask:
            nx, ny = (x + .5 - cx) / max(rad, 1), (y + .5 - cy) / max(rad, 1)
            dd = nx * nx + ny * ny
            if dd > 1:
                nx, ny = nx / math.sqrt(dd), ny / math.sqrt(dd); dd = 1
            nz = math.sqrt(max(0.0, 1 - dd))
            i = nx * lx + ny * ly + nz * lz
            if edge(mask, (x, y), (1, 0)) or edge(mask, (x, y), (0, 1)):
                i -= 0.25
            c = r[0] if i < -0.08 else r[1] if i < 0.32 else r[2] if i < 0.8 else r[3]
            self.put(x, y, c)
        hx, hy = int(round(cx - rad * 0.45)), int(round(cy - rad * 0.45))
        for p in ((hx, hy), (hx + 1, hy), (hx, hy + 1)):
            if p in mask:
                self.put(p[0], p[1], r[4])
        return mask

    def get(self, x, y):
        return self.c.get((x, y))

    def shift(self, dx, dy):
        self.c = {(x + dx, y + dy): v for (x, y), v in self.c.items()}

    def bbox(self):
        xs = [p[0] for p in self.c]; ys = [p[1] for p in self.c]
        return min(xs), min(ys), max(xs), max(ys)

    def center(self):
        x0, y0, x1, y1 = self.bbox()
        self.shift((N - 1 - x1 - x0) // 2, (N - 1 - y1 - y0) // 2)

    def outline(self, dark=(26, 16, 30)):
        add = {}
        for x in range(N):
            for y in range(N):
                if (x, y) in self.c:
                    continue
                nb = [self.c[q] for q in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)) if q in self.c]
                if nb:
                    darkest = min(nb, key=sum)
                    add[(x, y)] = mix(scale(darkest, 0.32), dark, 0.45)
        self.c.update(add)

    def image(self, colours=16, center=True, outline=True):
        saved = dict(self.c)
        try:
            return self._image(colours, center, outline)
        finally:
            self.c = saved

    def _image(self, colours, center, outline):
        if center:
            self.center()
        if outline:
            self.outline()
        x0, y0, x1, y1 = self.bbox()
        assert x0 >= 1 and y0 >= 1 and x1 <= 30 and y1 <= 30, ('sprite touches edge', (x0, y0, x1, y1))
        im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        for (x, y), c in self.c.items():
            im.putpixel((x, y), c + (255,))
        used = {c for c in self.c.values()}
        if len(used) > colours:
            vis = list(self.c.items())
            sample = Image.new('RGB', (len(vis), 1)); sample.putdata([c for _, c in vis])
            pal = sample.quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            q = sample.quantize(palette=pal, dither=Image.Dither.NONE).convert('RGB')
            im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
            for i, ((x, y), _) in enumerate(vis):
                im.putpixel((x, y), q.getpixel((i, 0)) + (255,))
        return im
