// Draws the 14 item icons of the v3.59 round (pack v2.9.0): six Silk Road items and eight Masonry items.
// Native 32x32 pixel art in the style of tools/pixel.py (upper-left light, a 1-pixel dark contour, <=16 colours), ported to Node
// because Pillow is not installed. Block-like items are drawn as small 2:1 isometric cubes, like reinforced_cobblestone.
// Writes, per id: assets/grindcore/items/<id>.json, models/item/<id>.json (item/generated) and textures/item/<id>.png in pack/,
// plus the review sheet previews/items-v2.9.png. Deterministic: no randomness, no dates.
// Usage: node tools/items_v29.js
const fs = require('fs'), zlib = require('zlib'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const N = 32;

// ---------------------------------------------------------------- colours
const hex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const col = c => (typeof c === 'string' ? hex(c) : c.map(v => Math.round(v)));
const mix = (a, b, t) => { a = col(a); b = col(b); return a.map((v, i) => Math.round(v * (1 - t) + b[i] * t)); };
const scale = (c, k) => col(c).map(v => Math.max(0, Math.min(255, Math.round(v * k))));
// dark, mid-dark, base, light, highlight; shadows lean violet, lights lean warm (same as pixel.py ramp)
const ramp = b => [mix(scale(b, 0.48), [36, 22, 52], 0.22), mix(scale(b, 0.74), [48, 30, 62], 0.08), col(b), mix(b, [255, 238, 196], 0.32), mix(b, [255, 250, 232], 0.62)];
const hash = (x, y, s = 0) => { let h = (x * 374761393 + y * 668265263 + s * 2147483647) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };

const WOOD = ramp('#9C6C3A'), IRON = ramp('#9EA4AA'), GOLD = ramp('#DEAC34'), BRASS = ramp('#C8973A'), COPPER = ramp('#B0703A');

// ---------------------------------------------------------------- masks (Sets of "x,y")
const K = (x, y) => x + ',' + y;
const P = k => k.split(',').map(Number);
const inb = (x, y) => x >= 0 && y >= 0 && x < N && y < N;
function mask(fn) { const m = new Set(); for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) if (fn(x, y)) m.add(K(x, y)); return m; }
const rect = (x0, y0, x1, y1) => mask((x, y) => x >= x0 && x <= x1 && y >= y0 && y <= y1);
const ell = (x0, y0, x1, y1) => { const cx = (x0 + x1 + 1) / 2, cy = (y0 + y1 + 1) / 2, rx = (x1 - x0 + 1) / 2, ry = (y1 - y0 + 1) / 2; return mask((x, y) => ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.08); };
const circ = (cx, cy, r) => mask((x, y) => (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r * 0.8);
function poly(pts) { // pixel centres inside the polygon, plus its edges
  const m = mask((x, y) => { const px = x + 0.5, py = y + 0.5; let ins = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) { const [xi, yi] = pts[i], [xj, yj] = pts[j]; if ((yi > py) !== (yj > py) && px < (xj - xi) * (py - yi) / (yj - yi) + xi) ins = !ins; } return ins; });
  return m;
}
function line(pts, w = 1) {
  const out = new Set();
  for (let i = 0; i + 1 < pts.length; i++) {
    let [x0, y0] = pts[i].map(Math.round); const [x1, y1] = pts[i + 1].map(Math.round);
    const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1; let err = dx + dy;
    for (;;) { out.add(K(x0, y0)); if (x0 === x1 && y0 === y1) break; const e2 = 2 * err; if (e2 >= dy) { err += dy; x0 += sx; } if (e2 <= dx) { err += dx; y0 += sy; } }
  }
  if (w >= 2) for (const k of [...out]) { const [x, y] = P(k); out.add(K(x + 1, y)); }
  if (w >= 3) for (const k of [...out]) { const [x, y] = P(k); out.add(K(x, y + 1)); }
  return out;
}
function tube(a, b, r) { const out = new Set(); const n = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) * 2); for (let i = 0; i <= n; i++) { const t = i / n; for (const k of circ(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, r)) out.add(k); } return out; }
const union = (...ms) => { const o = new Set(); for (const m of ms) for (const k of m) o.add(k); return o; };
const minus = (a, b) => new Set([...a].filter(k => !b.has(k)));
const inter = (a, b) => new Set([...a].filter(k => b.has(k)));
const edge = (m, x, y, dx, dy) => !m.has(K(x + dx, y + dy));

// ---------------------------------------------------------------- sprite
class Spr {
  constructor() { this.c = new Map(); }
  put(x, y, c) { if (inb(x, y) && c) this.c.set(K(x, y), col(c)); }
  fill(m, c) { for (const k of m) { const [x, y] = P(k); this.put(x, y, c); } return m; }
  shade(m, r) { // pixel.py shade(): light from the upper left
    for (const k of m) {
      const [x, y] = P(k);
      const ul = edge(m, x, y, 0, -1) || edge(m, x, y, -1, 0), dr = edge(m, x, y, 0, 1) || edge(m, x, y, 1, 0);
      let c;
      if (dr && !ul) c = r[0]; else if (dr && ul) c = r[1]; else if (ul) c = r[3];
      else if (edge(m, x, y, 1, 1) || edge(m, x, y, 2, 0) || edge(m, x, y, 0, 2)) c = r[1]; else c = r[2];
      this.put(x, y, c);
    }
    return m;
  }
  sphere(m, r, cx, cy, rad) { // pixel.py sphere(): radial shading for round things
    const lx = -0.55, ly = -0.62, lz = 0.56;
    for (const k of m) {
      const [x, y] = P(k); let nx = (x + 0.5 - cx) / rad, ny = (y + 0.5 - cy) / rad; let dd = nx * nx + ny * ny;
      if (dd > 1) { const s = Math.sqrt(dd); nx /= s; ny /= s; dd = 1; }
      let i = nx * lx + ny * ly + Math.sqrt(Math.max(0, 1 - dd)) * lz;
      if (edge(m, x, y, 1, 0) || edge(m, x, y, 0, 1)) i -= 0.25;
      this.put(x, y, i < -0.08 ? r[0] : i < 0.32 ? r[1] : i < 0.8 ? r[2] : r[3]);
    }
    const hx = Math.round(cx - rad * 0.45), hy = Math.round(cy - rad * 0.45);
    for (const [x, y] of [[hx, hy], [hx + 1, hy], [hx, hy + 1]]) if (m.has(K(x, y))) this.put(x, y, r[4]);
    return m;
  }
  bbox() { let x0 = N, y0 = N, x1 = -1, y1 = -1; for (const k of this.c.keys()) { const [x, y] = P(k); x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); } return [x0, y0, x1, y1]; }
  center() { const [x0, y0, x1, y1] = this.bbox(); const dx = Math.floor((N - 1 - x1 - x0) / 2), dy = Math.floor((N - 1 - y1 - y0) / 2); const n = new Map(); for (const [k, v] of this.c) { const [x, y] = P(k); n.set(K(x + dx, y + dy), v); } this.c = n; }
  outline(dark = [26, 16, 30]) {
    const add = [];
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
      if (this.c.has(K(x, y))) continue;
      const nb = [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]].map(([a, b]) => this.c.get(K(a, b))).filter(Boolean);
      if (nb.length) { const d = nb.reduce((a, b) => (a[0] + a[1] + a[2] <= b[0] + b[1] + b[2] ? a : b)); add.push([K(x, y), mix(scale(d, 0.32), dark, 0.45)]); }
    }
    for (const [k, v] of add) this.c.set(k, v);
  }
  quantize(n = 16) { // merge the least used colour into its nearest neighbour until <= n remain
    const key = c => c.join(',');
    for (;;) {
      const count = new Map(); for (const v of this.c.values()) count.set(key(v), (count.get(key(v)) || 0) + 1);
      if (count.size <= n) return;
      const cs = [...count.keys()].map(s => s.split(',').map(Number));
      let best = null;
      for (let i = 0; i < cs.length; i++) for (let j = 0; j < cs.length; j++) if (i !== j) {
        const d = (cs[i][0] - cs[j][0]) ** 2 * 3 + (cs[i][1] - cs[j][1]) ** 2 * 4 + (cs[i][2] - cs[j][2]) ** 2 * 2;
        const cost = d * count.get(key(cs[i]));
        if (!best || cost < best[0]) best = [cost, cs[i], cs[j]];
      }
      const from = key(best[1]); for (const [k, v] of this.c) if (key(v) === from) this.c.set(k, best[2]);
    }
  }
  image() {
    this.center(); this.outline(); this.quantize(16);
    const [x0, y0, x1, y1] = this.bbox();
    if (x0 < 1 || y0 < 1 || x1 > 30 || y1 > 30) throw new Error('sprite touches edge ' + [x0, y0, x1, y1]);
    const px = new Uint8Array(N * N * 4);
    for (const [k, v] of this.c) { const [x, y] = P(k); const i = (y * N + x) * 4; px[i] = v[0]; px[i + 1] = v[1]; px[i + 2] = v[2]; px[i + 3] = 255; }
    return px;
  }
}

// ---------------------------------------------------------------- isometric block (2:1), like reinforced_cobblestone
// columns cx-hw .. cx+hw-1; ty = top row of the top face; h = side height in rows.
// paint(face, u, v, x, y) returns a colour or null; face is 'top' | 'left' | 'right'.
function iso(s, cx, ty, hw, h, paint) {
  const mid = ty + (hw >> 1);
  const faces = { top: new Set(), left: new Set(), right: new Set() };
  for (let i = 0; i < 2 * hw; i++) {
    const x = cx - hw + i, k = Math.min(i, 2 * hw - 1 - i);
    for (let y = mid - (k >> 1) - 1; y <= mid + (k >> 1); y++) faces.top.add(K(x, y));
    for (let y = mid + (k >> 1) + 1; y <= mid + (k >> 1) + h; y++) faces[i < hw ? 'left' : 'right'].add(K(x, y));
  }
  for (const f of ['top', 'left', 'right']) for (const kk of faces[f]) {
    const [x, y] = P(kk); const i = x - (cx - hw), k = Math.min(i, 2 * hw - 1 - i);
    let u, v;
    if (f === 'top') { const p = (i - (hw - 0.5)) / hw, q = (y + 0.5 - mid) / (hw / 2 + 0.5); u = (1 + p + q) / 2; v = (1 - p + q) / 2; }
    else { u = f === 'left' ? i : i - hw; v = y - (mid + (k >> 1) + 1); }
    s.put(x, y, paint(f, u, v, x, y, faces[f]));
  }
  return faces;
}
// default face colour from a ramp: top light, left base, right dark; rim pixels brighter / darker
function faceTone(r, f, x, y, m) {
  if (f === 'top') return edge(m, x, y, 0, -1) ? r[4] : r[3];
  if (f === 'left') return edge(m, x, y, -1, 0) ? r[3] : edge(m, x, y, 0, 1) ? r[1] : r[2];
  return edge(m, x, y, 1, 0) || edge(m, x, y, 0, 1) ? r[0] : r[1];
}
const stepTone = (r, c, d) => r[Math.max(0, Math.min(4, r.findIndex(q => q.join() === c.join()) + d))];

// ================================================================ Silk Road
function cart_patch_kit() {
  const s = new Spr(); const HEAD = ramp('#B07A44'), ROPE = ramp('#D8C08A');
  // mallet resting behind the planks: wooden handle, iron-banded wooden head
  s.shade(rect(21, 9, 22, 18), ramp('#7A5030'));
  const head = rect(17, 3, 27, 8); s.shade(head, HEAD);
  for (const x of [18, 26]) for (let y = 3; y <= 8; y++) s.put(x, y, y === 3 ? IRON[4] : y === 8 ? IRON[0] : IRON[2]);
  // two timber planks with grain and light end grain
  for (const [x0, y0, x1, y1] of [[3, 17, 23, 21], [7, 22, 27, 26]]) {
    const m = rect(x0, y0, x1, y1); s.shade(m, WOOD);
    for (let x = x0 + 2; x < x1; x++) for (const y of [y0 + 1, y0 + 3]) if (hash(x, y, 21) > (y === y0 + 1 ? 0.45 : 0.35)) s.put(x, y, WOOD[1]);
    for (let y = y0 + 1; y < y1; y++) s.put(x0, y, WOOD[4]);
  }
  // twine binding the planks into a bundle
  for (let y = 16; y <= 27; y++) { if (y > 21 && y < 22) continue; s.put(10, y, y % 2 ? ROPE[3] : ROPE[2]); s.put(11, y, y % 2 ? ROPE[1] : ROPE[2]); }
  // iron L-bracket laid on top, with rivet holes
  const br = union(rect(14, 12, 16, 23), rect(14, 21, 23, 23)); s.shade(br, IRON);
  for (const [x, y] of [[15, 14], [15, 18], [19, 22], [22, 22]]) s.put(x, y, IRON[0]);
  // three nails
  for (const [x, y] of [[4, 9], [7, 11], [4, 13]]) { s.put(x - 1, y, IRON[3]); s.put(x, y, IRON[4]); s.put(x + 1, y, IRON[1]); s.put(x, y + 1, IRON[2]); s.put(x, y + 2, IRON[1]); }
  return s;
}

function saffron_spice() {
  const s = new Spr(); const CLOTH = ramp('#C9A46A'), RED = ramp('#D8482A'), ORA = ramp('#F08A24');
  const bag = ell(6, 12, 25, 28); s.sphere(bag, CLOTH, 15.5, 20.5, 9.5);
  for (const k of bag) { const [x, y] = P(k); if ((x + y * 2) % 5 === 0 && hash(x, y, 3) > 0.5) s.put(x, y, stepTone(CLOTH, s.c.get(k), -1)); }
  // gathered neck and red cord
  const neck = poly([[11, 9], [21, 9], [19, 14], [13, 14]]); s.shade(neck, CLOTH);
  s.fill(line([[11, 13], [21, 13]]), RED[1]); s.fill(line([[12, 12], [20, 12]]), RED[2]);
  s.fill(line([[20, 13], [23, 17], [22, 19]]), RED[1]);
  // a heap of saffron threads spilling from the mouth
  const heap = ell(10, 5, 22, 11); s.shade(heap, RED);
  const threads = [[[12, 7], [9, 4]], [[14, 6], [13, 3]], [[16, 6], [17, 3]], [[18, 7], [21, 4]], [[20, 8], [24, 5]], [[11, 9], [7, 7]]];
  threads.forEach(([a, b], i) => s.fill(line([a, b]), i % 2 ? ORA[3] : RED[3]));
  for (const k of heap) { const [x, y] = P(k); if (hash(x, y, 7) > 0.72) s.put(x, y, ORA[2 + (hash(x, y, 9) > 0.5 ? 1 : 0)]); }
  // loose threads beside the pouch
  s.fill(line([[25, 26], [28, 23]]), RED[3]); s.fill(line([[26, 27], [29, 26]]), ORA[3]);
  return s;
}

function imperial_silk() {
  const s = new Spr(); const CR = ramp('#B4122E');
  // three folded layers of crimson silk, each with a gold border, bottom to top
  const layers = [[4, 22], [6, 16], [8, 10]];
  for (const [x0, y0] of layers) {
    const body = poly([[x0, y0 + 3], [x0 + 6, y0], [x0 + 21, y0 + 2], [x0 + 21, y0 + 6], [x0 + 15, y0 + 9], [x0, y0 + 7]]);
    s.shade(body, CR);
    // shimmer: a diagonal light streak and soft sheen
    for (const k of body) { const [x, y] = P(k); const d = (x - x0) - (y - y0) * 2; if (d >= 7 && d <= 8) s.put(x, y, CR[4]); else if (d >= 5 && d <= 10 && hash(x, y, 2) > 0.45) s.put(x, y, CR[3]); }
    // gold trim along the folded front edge
    s.fill(inter(body, line([[x0, y0 + 6], [x0 + 15, y0 + 8], [x0 + 21, y0 + 5]])), GOLD[3]);
    s.fill(inter(body, line([[x0 + 1, y0 + 5], [x0 + 15, y0 + 7]])), GOLD[1]);
  }
  // gold embroidered dots on the top layer
  for (const [x, y] of [[14, 12], [18, 13], [22, 13], [16, 14], [20, 15]]) s.put(x, y, GOLD[4]);
  // a draped tail hanging over the front
  const tail = poly([[22, 18], [27, 16], [28, 27], [25, 29], [23, 26]]); s.shade(tail, CR);
  s.fill(inter(tail, line([[25, 18], [26, 27]])), GOLD[2]);
  return s;
}

function damascus_bar() {
  const s = new Spr(); const ST = ramp('#8C939E');
  const front = poly([[3, 25], [7, 16], [25, 16], [29, 25]]);
  const top = poly([[7, 16], [10, 11], [22, 11], [25, 16]]);
  const tone = (x, y) => { const w = Math.sin(y * 1.25 + 2.1 * Math.sin(x * 0.42 + y * 0.18)); return w > 0.45 ? 3 : w > -0.2 ? 2 : w > -0.7 ? 1 : 0; };
  for (const k of top) { const [x, y] = P(k); s.put(x, y, ST[Math.min(4, tone(x, y) + 1)]); }
  for (const k of front) { const [x, y] = P(k); let t = tone(x, y); if (edge(front, x, y, 0, 1) || edge(front, x, y, 1, 0)) t = 0; else if (edge(front, x, y, -1, 0)) t = Math.max(t, 2); s.put(x, y, ST[t]); }
  // bright bevel between top and front, highlight on the top edge
  for (let x = 8; x <= 24; x++) s.put(x, 16, ST[4]);
  for (const k of top) { const [x, y] = P(k); if (edge(top, x, y, 0, -1)) s.put(x, y, ST[4]); }
  return s;
}

function gearMask(cx, cy, r, teeth, hole, phase = 0) {
  return mask((x, y) => {
    const dx = x + 0.5 - cx, dy = y + 0.5 - cy, d = Math.hypot(dx, dy); if (d <= hole) return false;
    if (d <= r) return true;
    if (d > r + 2.3) return false;
    const a = (Math.atan2(dy, dx) / (2 * Math.PI) * teeth + phase + 10) % 1; return a < 0.5;
  });
}
function clockwork_gear() {
  const s = new Spr();
  const small = gearMask(22, 9.5, 4.6, 8, 1.4, 0.25); s.shade(small, COPPER);
  const big = gearMask(13.5, 18.5, 8.4, 10, 2.2);
  // spoke windows in the big gear
  const win = mask((x, y) => { const dx = x + 0.5 - 13.5, dy = y + 0.5 - 18.5, d = Math.hypot(dx, dy); if (d < 3.6 || d > 6.4) return false; const a = ((Math.atan2(dy, dx) / (2 * Math.PI) * 4 + 0.125) % 1 + 1) % 1; return a > 0.3; });
  const g = minus(big, win);
  for (const k of small) if (g.has(k) || win.has(k) || big.has(k)) s.c.delete(k);
  s.shade(g, BRASS);
  for (const k of win) s.put(...P(k), [42, 30, 26]); // see-through windows show the dark behind
  // the windows show the small gear where they overlap it
  for (const k of win) if (small.has(k)) s.put(...P(k), COPPER[1]);
  // centre axle and a highlight ring
  for (const k of circ(13, 18, 1.2)) s.put(...P(k), IRON[2]);
  for (const k of g) { const [x, y] = P(k); const d = Math.hypot(x + 0.5 - 13.5, y + 0.5 - 18.5); if (d > 6.8 && d < 7.6 && x + y < 31) s.put(x, y, BRASS[4]); }
  return s;
}

function sovereign_relic() {
  const s = new Spr(); const JADE = ramp('#2FB57E');
  // crown points on top
  for (const [x, h] of [[11, 4], [16, 6], [21, 4]]) { const m = poly([[x - 2, 11], [x, 11 - h], [x + 2, 11]]); s.shade(m, GOLD); s.put(x, 11 - h, GOLD[4]); }
  // gold medallion with a jade heart
  const disc = circ(16, 18, 9); s.sphere(disc, GOLD, 16.5, 18.5, 9.5);
  const ring = minus(circ(16, 18, 6.6), circ(16, 18, 5.8)); s.fill(ring, GOLD[1]);
  const jade = circ(16, 18, 5); s.sphere(jade, JADE, 16.5, 18.5, 5.5);
  // small jade studs on the rim, rune cross in the jade
  for (const [x, y] of [[8, 18], [24, 18], [16, 26], [16, 10]]) { s.put(x, y, JADE[3]); s.put(x + 1, y, JADE[1]); }
  for (const k of union(line([[16, 15], [16, 21]]), line([[13, 18], [19, 18]]))) s.put(...P(k), [214, 255, 226]);
  // glow: a pale halo just outside the disc and two four-point sparkles touching it
  const halo = minus(circ(16, 18, 10.2), union(disc, s.c.keys()));
  for (const k of halo) { const [x, y] = P(k); if (y > 9 && (x + y) % 2 === 0) s.put(x, y, [255, 236, 150]); }
  for (const [x, y] of [[5, 9], [27, 26]]) { s.put(x, y, [255, 252, 220]); for (const [a, b] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) s.put(x + a, y + b, [255, 222, 120]); }
  s.fill(line([[25, 11], [26, 12]]), [255, 222, 120]); s.fill(line([[25, 12], [26, 11]]), [255, 222, 120]);
  return s;
}

// ================================================================ Masonry
function mortar() {
  const s = new Spr(); const GREY = ramp('#9A9A94'), TUB = ramp('#7C5634');
  const tub = poly([[4, 17], [28, 17], [25, 29], [7, 29]]); s.shade(tub, TUB);
  for (const k of tub) { const [x, y] = P(k); if ((y === 21 || y === 25) && !edge(tub, x, y, -1, 0) && !edge(tub, x, y, 1, 0)) s.put(x, y, IRON[1]); }
  const mud = ell(4, 13, 27, 20); s.shade(mud, GREY);
  for (const k of mud) { const [x, y] = P(k); const h = hash(x, y, 5); if (h > 0.82) s.put(x, y, GREY[3]); else if (h < 0.12) s.put(x, y, GREY[1]); }
  // rim of the tub in front of the mortar
  s.fill(inter(tub, line([[4, 18], [28, 18]])), TUB[3]);
  // trowel stuck in the mortar
  const blade = poly([[9, 16], [15, 9], [19, 12], [13, 17]]); s.shade(blade, IRON);
  s.fill(line([[17, 10], [20, 7]]), IRON[1]);
  s.shade(tube([21, 6], [26, 1.5], 1.0), WOOD);
  return s;
}

const STONE = ramp('#A09A8C');
function cut_stone() {
  const s = new Spr();
  iso(s, 16, 3, 13, 13, (f, u, v, x, y, m) => {
    let c = faceTone(STONE, f, x, y, m);
    // a chiselled border just inside each face
    if (f === 'top' && (u < 0.1 || v < 0.1 || u > 0.9 || v > 0.9) && !edge(m, x, y, 0, -1)) c = STONE[2];
    if (f !== 'top' && (v === 1 || (f === 'left' ? u === 1 : u === 11))) c = stepTone(STONE, faceTone(STONE, f, x, y, m), 1);
    if (hash(x, y, 11) > 0.94 && !edge(m, x, y, 0, -1)) c = stepTone(STONE, c, -1);
    // tooled lines on the sides
    if (f !== 'top' && v > 2 && v < 12 && u > 1 && u < 11 && (u * 3 + v) % 9 === 0) c = stepTone(STONE, c, -1);
    return c;
  });
  return s;
}

function stone_foundation() {
  const s = new Spr(); const ST = ramp('#8A867E'), MORT = [196, 190, 176], QUOIN = ramp('#B8864B');
  iso(s, 16, 3, 13, 14, (f, u, v, x, y, m) => {
    let c = faceTone(ST, f, x, y, m);
    if (f === 'top') { if (!edge(m, x, y, 0, -1) && (Math.abs(u - 0.5) < 0.04 || (Math.abs(v - 0.5) < 0.04 && u < 0.5))) c = MORT; return c; }
    const row = Math.floor(v / 5), lu = f === 'left' ? u : 12 - u;
    // a big tan corner stone at the front edge, alternating heights
    const quoin = lu >= (row % 2 ? 9 : 7);
    if (quoin) { c = faceTone(QUOIN, f, x, y, m); if (v % 5 === 4 || lu === (row % 2 ? 9 : 7)) c = QUOIN[0]; return c; }
    if (v % 5 === 4 && v < 13) return MORT;
    if ((lu + (row % 2) * 3) % 6 === 0) return MORT;
    if (hash(x, y, 4) > 0.85) c = stepTone(ST, c, -1);
    return c;
  });
  return s;
}

function dressed_slate() {
  const s = new Spr(); const SL = ramp('#363A46');
  const paint = (f, u, v, x, y, m) => {
    let c = faceTone(SL, f, x, y, m);
    if (f === 'top' && !edge(m, x, y, 0, -1) && (u < 0.09 || v < 0.09)) c = SL[4]; // chamfered back edges
    if (f === 'top' && !edge(m, x, y, 0, -1) && (u > 0.93 || v > 0.93)) c = SL[2];
    if (f === 'top' && Math.abs(u - 0.55 + Math.sin(v * 9) * 0.04) < 0.03 && v > 0.2 && v < 0.8) c = SL[2]; // natural cleft line
    if (f !== 'top' && v === 0) c = stepTone(SL, c, 2);
    return c;
  };
  iso(s, 15, 15, 12, 4, paint); // lower tile
  iso(s, 17, 7, 12, 4, paint); // upper tile, offset
  return s;
}

function reinforced_masonry() {
  const s = new Spr(); const ST = ramp('#7E8288');
  iso(s, 16, 3, 13, 14, (f, u, v, x, y, m) => {
    let c = faceTone(ST, f, x, y, m);
    if (f === 'top') {
      if (Math.abs(u - 0.5) < 0.07 && !edge(m, x, y, 0, -1)) return faceTone(IRON, 'top', x, y, m); // iron strap over the top
      if (!edge(m, x, y, 0, -1) && Math.abs(v - 0.5) < 0.04) c = ST[2];
      return c;
    }
    const band = v === 2 || v === 3 || v === 10 || v === 11;
    const strap = f === 'right' ? (u >= 5 && u <= 7) : false;
    if (band || strap) { c = faceTone(IRON, f, x, y, m); if ((band && v % 2 === 0 && u % 4 === 1) || (strap && u === 6 && v % 4 === 1)) c = IRON[4]; return c; }
    if (v === 7) return ST[0];
    if ((u + (v > 7 ? 3 : 0)) % 6 === 0) return ST[0];
    return c;
  });
  return s;
}

function polished_marble() {
  const s = new Spr(); const MB = ramp('#E6E2DA'), VEIN = [128, 126, 140];
  iso(s, 16, 3, 13, 13, (f, u, v, x, y, m) => {
    let c = faceTone(MB, f, x, y, m);
    // thin grey veins, one wandering line per face
    const vein = f === 'top' ? Math.abs(v - (0.62 + 0.07 * Math.sin(u * 11))) < 0.045 && u > 0.12
      : f === 'left' ? Math.round(2 + 0.75 * u + 1.2 * Math.sin(u * 0.8)) === v
      : Math.round(9 - 0.55 * u + Math.sin(u * 1.1)) === v;
    if (vein && !edge(m, x, y, 0, -1)) c = f === 'right' ? scale(VEIN, 0.82) : VEIN;
    // glossy streak on the top, a soft gleam on the left face
    if (f === 'top' && Math.abs(u - 0.3) < 0.045 && v > 0.12 && v < 0.5) c = [255, 255, 255];
    if (f === 'left' && v - u === 5 && u > 0 && u < 5) c = MB[4];
    return c;
  });
  return s;
}

const OBS = ramp('#2E2440'), VIOLET = [178, 96, 236], VIO_HI = [226, 184, 255];
function carved_obsidian() {
  const s = new Spr();
  const glyphL = new Set(['2,3', '3,3', '4,3', '5,3', '6,3', '7,3', '8,3', '9,3', '2,4', '9,4', '2,5', '5,5', '6,5', '9,5', '2,6', '5,6', '6,6', '9,6', '2,7', '9,7', '2,8', '3,8', '4,8', '5,8', '6,8', '7,8', '8,8', '9,8', '5,9', '6,9', '5,10', '6,10']);
  iso(s, 16, 3, 13, 13, (f, u, v, x, y, m) => {
    let c = faceTone(OBS, f, x, y, m);
    if (hash(x, y, 13) > 0.88 && !edge(m, x, y, 0, -1)) c = [90, 62, 128];
    if (f === 'top' && !edge(m, x, y, 0, -1) && Math.abs(Math.abs(u - 0.5) + Math.abs(v - 0.5) - 0.28) < 0.04) c = VIOLET;
    if (f !== 'top') { const lu = f === 'left' ? u : 12 - u; if (glyphL.has(K(lu, v - (f === 'left' ? 0 : 0)))) c = f === 'left' ? VIO_HI : VIOLET; }
    return c;
  });
  return s;
}

function runed_keystone() {
  const s = new Spr(); const LAPIS = ramp('#2F62D8');
  const top = poly([[5, 6], [9, 3], [29, 3], [25, 6]]);
  const side = poly([[25, 6], [29, 3], [25, 26], [21, 29]]);
  const front = poly([[5, 6], [25, 6], [21, 29], [9, 29]]);
  s.fill(top, OBS[3]); for (const k of top) { const [x, y] = P(k); if (edge(top, x, y, 0, -1)) s.put(x, y, OBS[4]); }
  s.fill(side, OBS[0]);
  s.shade(front, OBS);
  for (const k of front) { const [x, y] = P(k); if (hash(x, y, 17) > 0.88 && !edge(front, x, y, 0, 1)) s.put(x, y, [76, 58, 104]); }
  // glowing lapis rune: a ring, a vertical stave and two chevrons
  const rune = union(minus(circ(15, 15, 4.4), circ(15, 15, 3.2)), line([[15, 9], [15, 25]]), line([[12, 21], [15, 24], [18, 21]]), line([[12, 9], [15, 11], [18, 9]]));
  const glow = new Set(); for (const k of rune) { const [x, y] = P(k); for (const [a, b] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (front.has(K(x + a, y + b)) && !rune.has(K(x + a, y + b))) glow.add(K(x + a, y + b)); }
  s.fill(inter(glow, front), LAPIS[1]);
  s.fill(inter(rune, front), LAPIS[3]);
  for (const k of circ(15, 15, 1.1)) s.put(...P(k), [200, 226, 255]);
  return s;
}

const ITEMS = [
  ['cart_patch_kit', cart_patch_kit], ['saffron_spice', saffron_spice], ['imperial_silk', imperial_silk], ['damascus_bar', damascus_bar],
  ['clockwork_gear', clockwork_gear], ['sovereign_relic', sovereign_relic],
  ['mortar', mortar], ['cut_stone', cut_stone], ['stone_foundation', stone_foundation], ['dressed_slate', dressed_slate],
  ['reinforced_masonry', reinforced_masonry], ['polished_marble', polished_marble], ['carved_obsidian', carved_obsidian], ['runed_keystone', runed_keystone],
];

// ---------------------------------------------------------------- PNG
const crcT = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crcT[n] = c >>> 0; }
const crc = b => { let c = 0xffffffff; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
function png(w, h, rgba) {
  const raw = Buffer.alloc((w * 4 + 1) * h); for (let y = 0; y < h; y++) Buffer.from(rgba.buffer, rgba.byteOffset + y * w * 4, w * 4).copy(raw, y * (w * 4 + 1) + 1);
  const chunk = (t, d) => { const len = Buffer.alloc(4); len.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t, 'ascii'), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([len, td, c]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}

// ---------------------------------------------------------------- preview sheet with a tiny 3x5 label font
const FONT = { a: '010101111101101', b: '110101110101110', c: '011100100100011', d: '110101101101110', e: '111100110100111', f: '111100110100100', g: '011100101101011', h: '101101111101101', i: '111010010010111', j: '001001001101010', k: '101101110101101', l: '100100100100111', m: '101111111101101', n: '110101101101101', o: '010101101101010', p: '110101110100100', q: '010101101011001', r: '110101110101101', s: '011100010001110', t: '111010010010010', u: '101101101101111', v: '101101101101010', w: '101101111111101', x: '101101010101101', y: '101101010010010', z: '111001010100111', _: '000000000000111' };
function sheet(icons) {
  const Z = 5, cols = 7, cw = 32 * Z + 16, chh = 32 * Z + 30, W = cols * cw, H = Math.ceil(icons.length / cols) * chh;
  const img = new Uint8Array(W * H * 4);
  for (let i = 0; i < W * H; i++) { img[i * 4] = 44; img[i * 4 + 1] = 46; img[i * 4 + 2] = 52; img[i * 4 + 3] = 255; }
  const put = (x, y, c) => { if (x < 0 || y < 0 || x >= W || y >= H) return; const i = (y * W + x) * 4; img[i] = c[0]; img[i + 1] = c[1]; img[i + 2] = c[2]; };
  icons.forEach(([id, px], n) => {
    const ox = (n % cols) * cw + 8, oy = Math.floor(n / cols) * chh + 6;
    for (let y = 0; y < 32 * Z; y++) for (let x = 0; x < 32 * Z; x++) { const j = (Math.floor(y / Z) * 32 + Math.floor(x / Z)) * 4; if (px[j + 3]) put(ox + x, oy + y, [px[j], px[j + 1], px[j + 2]]); }
    [...id].forEach((ch, ci) => { const g = FONT[ch]; if (!g) return; for (let r = 0; r < 5; r++) for (let c = 0; c < 3; c++) if (g[r * 3 + c] === '1') for (let a = 0; a < 2; a++) for (let b = 0; b < 2; b++) put(ox + ci * 8 + c * 2 + a, oy + 32 * Z + 8 + r * 2 + b, [230, 226, 214]); });
  });
  return png(W, H, img);
}

// ---------------------------------------------------------------- write
const out = (p, data) => { const f = path.join(ROOT, p); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, data); };
const icons = [];
for (const [id, draw] of ITEMS) {
  const px = draw().image(); icons.push([id, px]);
  out(`pack/assets/grindcore/textures/item/${id}.png`, png(N, N, px));
  out(`pack/assets/grindcore/models/item/${id}.json`, JSON.stringify({ parent: 'minecraft:item/generated', textures: { layer0: `grindcore:item/${id}` } }, null, 2) + '\n');
  out(`pack/assets/grindcore/items/${id}.json`, JSON.stringify({ model: { type: 'minecraft:model', model: `grindcore:item/${id}` } }, null, 2) + '\n');
  const colours = new Set(); for (let i = 0; i < px.length; i += 4) if (px[i + 3]) colours.add(px[i] + ',' + px[i + 1] + ',' + px[i + 2]);
  console.log(id.padEnd(20), 'colours', colours.size);
}
out('previews/items-v2.9.png', sheet(icons));
console.log(ITEMS.length + ' icons, previews/items-v2.9.png');
