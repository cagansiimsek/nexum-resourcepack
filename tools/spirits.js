// Draws the four "profession spirit" pet models (pack v2.2.0): wheat_sprite, ore_golem, wood_owl, forage_fox,
// and the eight v3.58 spirits (pack v2.6.0): harvest_hare, gem_beetle, bark_squirrel, petal_moth, battle_hound, bounty_raven,
// ember_drake, golden_dragon.
// Each spirit is a small cube model (about 10 units, centred on 8,8,8, face towards NORTH) with one 64x64 texture.
// Deterministic: fixed seed, no dates. Also renders isometric previews with a tiny software renderer.
// Usage: node tools/spirits.js   (writes textures, models, item definitions and previews)
const fs = require('fs'), zlib = require('zlib'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const TS = 64; // texture size
const hex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const sh = (c, k) => c.map(v => Math.max(0, Math.min(255, Math.round(v * k))));
const lighten = (c, k) => c.map(v => Math.round(v + (255 - v) * k));
let seed = 11; const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;

// ---------- element + texture painting ----------
const FACES = ['north', 'south', 'east', 'west', 'up', 'down'], FK = { north: 'n', south: 's', east: 'e', west: 'w', up: 'u', down: 'd' };
const GROUPS = { v: ['n', 's', 'e', 'w'], ns: ['n', 's'], ew: ['e', 'w'], a: ['n', 's', 'e', 'w', 'u', 'd'], nsew: ['n', 's', 'e', 'w'] };
// E(name, from, to, {c: base colour, rot: [axis, angle, origin], pat: fn(face,x,y,w,h), r: [[face, x, y, w, h, colour, flat?]]})
function E(name, from, to, o = {}) { return Object.assign({ name, from, to }, o); }
const sizeOf = e => [e.to[0] - e.from[0], e.to[1] - e.from[1], e.to[2] - e.from[2]];
function faceDims(e) { // pixel size of each face region
  const [sx, sy, sz] = sizeOf(e).map(Math.ceil);
  return { n: [sx, sy], s: [sx, sy], e: [sz, sy], w: [sz, sy], u: [sx, sz], d: [sx, sz] };
}
function netSize(e) { const [sx, sy, sz] = sizeOf(e).map(Math.ceil); return [2 * (sx + sz), sz + sy]; }
function netOffsets(e) { // top-left of each face inside the element's net
  const [sx, sy, sz] = sizeOf(e).map(Math.ceil);
  return { u: [sz, 0], d: [sz + sx, 0], w: [0, sz], n: [sz, sz], e: [sz + sx, sz], s: [2 * sz + sx, sz] };
}
function shade(f, c) { return { n: c, s: sh(c, 0.86), e: sh(c, 0.93), w: sh(c, 0.93), u: lighten(c, 0.14), d: sh(c, 0.68) }[f]; }

function buildSpirit(spec) {
  const px = new Uint8Array(TS * TS * 4), used = new Uint8Array(TS * TS);
  // shelf packing of the nets
  const order = spec.elements.map((e, i) => i).sort((a, b) => netSize(spec.elements[b])[1] - netSize(spec.elements[a])[1] || a - b);
  let sx = 0, sy = 0, rowH = 0;
  for (const i of order) {
    const e = spec.elements[i], [w, h] = netSize(e);
    if (sx + w > TS) { sx = 0; sy += rowH; rowH = 0; }
    if (sy + h > TS) throw new Error(spec.id + ': texture full at ' + e.name);
    e.at = [sx, sy]; sx += w; rowH = Math.max(rowH, h);
  }
  for (const e of spec.elements) {
    const dims = faceDims(e), offs = netOffsets(e); e.uv = {};
    for (const f of ['u', 'd', 'w', 'n', 'e', 's']) {
      const [fw, fh] = dims[f], ox = e.at[0] + offs[f][0], oy = e.at[1] + offs[f][1];
      e.uv[f] = [ox, oy, fw, fh];
      const flat = new Set(), over = {};
      for (const r of e.r || []) {
        const fs_ = GROUPS[r[0]] || [r[0]]; if (!fs_.includes(f)) continue;
        for (let y = 0; y < r[4]; y++) for (let x = 0; x < r[3]; x++) { const k = (r[2] + y) * 100 + (r[1] + x); over[k] = r[5]; if (r[6]) flat.add(k); else flat.delete(k); }
      }
      for (let y = 0; y < fh; y++) for (let x = 0; x < fw; x++) {
        const k = y * 100 + x;
        let c = over[k] || (e.pat && e.pat(f, x, y, fw, fh)) || (e.fc && e.fc[f]) || shade(f, e.c);
        if (over[k] === undefined && e.pat && e.pat(f, x, y, fw, fh)) { /* pattern pixel, noise below */ }
        const n = flat.has(k) ? 0 : Math.round((rnd() - 0.5) * 12), i = ((oy + y) * TS + ox + x) * 4;
        px[i] = Math.max(0, Math.min(255, c[0] + n)); px[i + 1] = Math.max(0, Math.min(255, c[1] + n)); px[i + 2] = Math.max(0, Math.min(255, c[2] + n)); px[i + 3] = 255;
        used[(oy + y) * TS + ox + x]++;
      }
    }
  }
  if (used.some(v => v > 1)) throw new Error(spec.id + ': overlapping UV regions');
  spec.px = px;
}

// ---------- JSON ----------
const r6 = v => Math.round(v * 1e5) / 1e5;
function modelJson(spec) {
  const faceName = { north: 'n', south: 's', east: 'e', west: 'w', up: 'u', down: 'd' };
  const elements = spec.elements.map(e => {
    const o = { name: e.name, from: e.from, to: e.to };
    if (e.rot) o.rotation = { angle: e.rot[1], axis: e.rot[0], origin: e.rot[2] };
    o.faces = {};
    for (const f of FACES) { const [x, y, w, h] = e.uv[faceName[f]]; o.faces[f] = { uv: [r6(x * 16 / TS), r6(y * 16 / TS), r6((x + w) * 16 / TS), r6((y + h) * 16 / TS)], texture: '#0' }; }
    return o;
  });
  const tex = 'grindcore:item/spirit_' + spec.id;
  return {
    credit: 'SkyGrind pack v2.2.0 profession spirits; procedural cuboid/pixel art (tools/spirits.js)',
    ambientocclusion: false, gui_light: 'front', texture_size: [TS, TS],
    textures: { '0': tex, particle: tex },
    elements,
    display: {
      gui: { rotation: [27, 205, 0], translation: [0, 0, 0], scale: [1.3, 1.3, 1.3] },
      ground: { rotation: [0, 0, 0], translation: [0, 3, 0], scale: [0.6, 0.6, 0.6] },
      fixed: { rotation: [0, 180, 0], translation: [0, 0, 0], scale: [1, 1, 1] },
      head: { rotation: [0, 180, 0], translation: [0, 12, 0], scale: [0.9, 0.9, 0.9] },
      thirdperson_righthand: { rotation: [75, 45, 0], translation: [0, 2.5, 0], scale: [0.45, 0.45, 0.45] },
      thirdperson_lefthand: { rotation: [75, 225, 0], translation: [0, 2.5, 0], scale: [0.45, 0.45, 0.45] },
      firstperson_righthand: { rotation: [0, 45, 0], translation: [0, 1, 0], scale: [0.5, 0.5, 0.5] },
      firstperson_lefthand: { rotation: [0, 225, 0], translation: [0, 1, 0], scale: [0.5, 0.5, 0.5] },
    },
  };
}
const itemJson = id => ({ model: { type: 'minecraft:model', model: 'grindcore:item/spirit_' + id } });

// ---------- PNG ----------
const crcT = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crcT[n] = c >>> 0; }
const crc = b => { let c = 0xffffffff; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
function png(w, h, rgba) {
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 4 + 1)] = 0; Buffer.from(rgba.buffer, rgba.byteOffset + y * w * 4, w * 4).copy(raw, y * (w * 4 + 1) + 1); }
  const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}

// ---------- preview renderer (orthographic, z-buffer, nearest-neighbour texture) ----------
function rotPt(p, rot) {
  if (!rot) return p;
  const [ax, ang, o] = rot, a = ang * Math.PI / 180, c = Math.cos(a), s = Math.sin(a), x = p[0] - o[0], y = p[1] - o[1], z = p[2] - o[2];
  let nx = x, ny = y, nz = z;
  if (ax === 'x') { ny = y * c - z * s; nz = y * s + z * c; } else if (ax === 'y') { nx = x * c + z * s; nz = -x * s + z * c; } else { nx = x * c - y * s; ny = x * s + y * c; }
  return [nx + o[0], ny + o[1], nz + o[2]];
}
const SHADE = { n: 0.8, s: 0.8, e: 0.6, w: 0.6, u: 1.0, d: 0.5 };
function renderView(spec, camDir, W, H, ppu, SS) {
  const w = W * SS, h = H * SS, scale = ppu * SS;
  const col = new Float32Array(w * h * 3), alpha = new Uint8Array(w * h), zb = new Float32Array(w * h).fill(1e9);
  const len = Math.hypot(...camDir), f = camDir.map(v => -v / len); // view direction (from camera to scene)
  const up0 = [0, 1, 0];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const norm = a => { const l = Math.hypot(...a); return a.map(v => v / l); };
  const right = norm(cross(f, up0)), up = cross(right, f);
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const C = [8, 8, 8];
  const proj = p => { const q = [p[0] - C[0], p[1] - C[1], p[2] - C[2]]; return [w / 2 + dot(q, right) * scale, h / 2 - dot(q, up) * scale, dot(q, f)]; };
  for (const e of spec.elements) {
    const [x0, y0, z0] = e.from, [x1, y1, z1] = e.to, sx = x1 - x0, sy = y1 - y0, sz = z1 - z0;
    const fd = { n: [[x1, y1, z0], [-sx, 0, 0], [0, -sy, 0]], s: [[x0, y1, z1], [sx, 0, 0], [0, -sy, 0]], e: [[x1, y1, z1], [0, 0, -sz], [0, -sy, 0]], w: [[x0, y1, z0], [0, 0, sz], [0, -sy, 0]], u: [[x0, y1, z0], [sx, 0, 0], [0, 0, sz]], d: [[x0, y0, z1], [sx, 0, 0], [0, 0, -sz]] };
    for (const fk of Object.keys(fd)) {
      const [o, u, v] = fd[fk], P0 = rotPt(o, e.rot), Pu = rotPt([o[0] + u[0], o[1] + u[1], o[2] + u[2]], e.rot), Pv = rotPt([o[0] + v[0], o[1] + v[1], o[2] + v[2]], e.rot);
      const a0 = proj(P0), au = proj(Pu), av = proj(Pv), ax = au[0] - a0[0], ay = au[1] - a0[1], bx = av[0] - a0[0], by = av[1] - a0[1], det = ax * by - ay * bx;
      if (Math.abs(det) < 1e-6) continue;
      const du = au[2] - a0[2], dv = av[2] - a0[2], [ux, uy, fw, fh] = e.uv[fk];
      const xs = [a0[0], a0[0] + ax, a0[0] + bx, a0[0] + ax + bx], ys = [a0[1], a0[1] + ay, a0[1] + by, a0[1] + ay + by];
      const minX = Math.max(0, Math.floor(Math.min(...xs))), maxX = Math.min(w - 1, Math.ceil(Math.max(...xs))), minY = Math.max(0, Math.floor(Math.min(...ys))), maxY = Math.min(h - 1, Math.ceil(Math.max(...ys)));
      for (let py = minY; py <= maxY; py++) for (let pxl = minX; pxl <= maxX; pxl++) {
        const qx = pxl + 0.5 - a0[0], qy = py + 0.5 - a0[1], s = (qx * by - qy * bx) / det, t = (ax * qy - ay * qx) / det;
        if (s < 0 || s >= 1 || t < 0 || t >= 1) continue;
        const z = a0[2] + s * du + t * dv, idx = py * w + pxl; if (z >= zb[idx]) continue;
        const tx = ux + Math.min(fw - 1, Math.floor(s * fw)), ty = uy + Math.min(fh - 1, Math.floor(t * fh)), ti = (ty * TS + tx) * 4;
        zb[idx] = z; alpha[idx] = 1; const k = SHADE[fk];
        col[idx * 3] = spec.px[ti] * k; col[idx * 3 + 1] = spec.px[ti + 1] * k; col[idx * 3 + 2] = spec.px[ti + 2] * k;
      }
    }
  }
  const out = new Uint8Array(W * H * 4), bg = [43, 46, 53];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    let r = 0, g = 0, b = 0, a = 0;
    for (let j = 0; j < SS; j++) for (let i = 0; i < SS; i++) { const idx = (y * SS + j) * w + x * SS + i; if (alpha[idx]) { r += col[idx * 3]; g += col[idx * 3 + 1]; b += col[idx * 3 + 2]; a++; } }
    const n = SS * SS, o = (y * W + x) * 4, cov = a / n;
    out[o] = Math.round(a ? (r / a) * cov + bg[0] * (1 - cov) : bg[0]); out[o + 1] = Math.round(a ? (g / a) * cov + bg[1] * (1 - cov) : bg[1]); out[o + 2] = Math.round(a ? (b / a) * cov + bg[2] * (1 - cov) : bg[2]); out[o + 3] = 255;
  }
  return out;
}
const VW = 288, VH = 288;
const VIEWS = [[-1, 0.9, -1], [1, 0.9, 1]];
function blit(dst, dw, src, sw, sh_, ox, oy) { for (let y = 0; y < sh_; y++) for (let x = 0; x < sw; x++) { const s = (y * sw + x) * 4, d = ((oy + y) * dw + ox + x) * 4; dst[d] = src[s]; dst[d + 1] = src[s + 1]; dst[d + 2] = src[s + 2]; dst[d + 3] = 255; } }

// ---------- the four creatures ----------
const EYE = hex('#2A1D14'), GLINT = hex('#F5EFE6');
const spirits = [];

// 1. Wheat sprite (Farming): golden sheaf, leaf hood, ear spikes, two dot eyes, leaf arms
{
  const GOLD = hex('#E3B341'), STRAW = hex('#F6DC8A'), BAND = hex('#9A6B1F'), LEAF = hex('#6FAE3D'), LEAFD = sh(LEAF, 0.78);
  const vein = (f, x, y, w, h) => (f === 'u' || f === 'd') ? (x === (w >> 1) ? LEAFD : null) : (y === (h >> 1) ? LEAFD : null);
  const stripes = (f, x, y, w, h) => (f === 'u' || f === 'd') ? null : (x % 3 === 0 ? STRAW : (y === h - 1 && f !== 'u' ? sh(GOLD, 0.82) : null));
  spirits.push({
    id: 'wheat_sprite', elements: [
      E('skirt', [5, 3, 5], [11, 4, 11], { c: GOLD, pat: stripes }),
      E('torso', [6, 4, 6], [10, 7, 10], { c: GOLD, pat: stripes }),
      E('band', [5.5, 5, 5.5], [10.5, 6, 10.5], { c: BAND, r: [['n', 1, 0, 3, 1, lighten(BAND, 0.35)], ['n', 2, 0, 1, 1, sh(BAND, 0.7)]] }),
      E('head', [5, 7, 5], [11, 10, 11], { c: STRAW, r: [['n', 1, 0, 1, 2, EYE, true], ['n', 4, 0, 1, 2, EYE, true], ['n', 2, 2, 2, 1, hex('#F2B987')]] }),
      E('collar', [4, 7, 4], [12, 8, 12], { c: LEAF, pat: vein }),
      E('hood left', [4, 8, 5], [5, 11, 11], { c: LEAF, rot: ['z', 22.5, [4.5, 8, 8]], pat: vein }),
      E('hood right', [11, 8, 5], [12, 11, 11], { c: LEAF, rot: ['z', -22.5, [11.5, 8, 8]], pat: vein }),
      E('hood back', [5, 8, 11], [11, 11, 12], { c: LEAF, rot: ['x', 22.5, [8, 8, 11.5]], pat: vein }),
      E('ear spike left', [6, 10, 6], [7, 13, 7], { c: GOLD, rot: ['z', 22.5, [6.5, 10, 6.5]], r: [['a', 0, 0, 1, 1, STRAW]] }),
      E('ear spike right', [9, 10, 6], [10, 13, 7], { c: GOLD, rot: ['z', -22.5, [9.5, 10, 6.5]], r: [['a', 0, 0, 1, 1, STRAW]] }),
      E('ear spike middle', [7.5, 10, 7.5], [8.5, 14, 8.5], { c: GOLD, r: [['a', 0, 0, 1, 1, STRAW]] }),
      E('ear spike back', [7.5, 10, 9.5], [8.5, 13, 10.5], { c: GOLD, rot: ['x', 22.5, [8, 10, 10]], r: [['a', 0, 0, 1, 1, STRAW]] }),
      E('leaf arm left', [3, 5, 7], [6, 6, 9], { c: LEAF, rot: ['z', 22.5, [6, 5.5, 8]], pat: vein }),
      E('leaf arm right', [10, 5, 7], [13, 6, 9], { c: LEAF, rot: ['z', -22.5, [10, 5.5, 8]], pat: vein }),
    ],
  });
}

// 2. Ore golem (Mining): chunky stone body, smaller head, stubby arms, short feet, aqua + gold ore flecks
{
  const ST = hex('#8A8F98'), DK = hex('#5B6068'), LT = hex('#B4B9C1'), AQ = hex('#5EE6E0'), GD = hex('#F2C14E'), AQL = lighten(AQ, 0.55);
  const crack = (f, x, y, w, h) => (f === 'd') ? null : ((x * 7 + y * 3 + (f.charCodeAt(0))) % 11 === 0 ? sh(ST, 0.85) : ((x * 5 + y * 11) % 17 === 0 ? LT : null));
  spirits.push({
    id: 'ore_golem', elements: [
      E('foot left', [4, 3, 6], [7, 4, 10], { c: DK }),
      E('foot right', [9, 3, 6], [12, 4, 10], { c: DK }),
      E('body', [4, 4, 5], [12, 9, 11], {
        c: ST, pat: crack, r: [
          ['n', 1, 1, 2, 2, AQ], ['n', 5, 3, 2, 1, GD], ['n', 0, 4, 8, 1, DK],
          ['s', 1, 1, 2, 2, GD], ['s', 5, 2, 1, 2, AQ], ['s', 0, 4, 8, 1, DK],
          ['e', 1, 1, 2, 2, AQ], ['e', 3, 3, 1, 2, GD], ['w', 2, 2, 2, 2, GD], ['w', 4, 1, 1, 2, AQ], ['v', 0, 4, 6, 1, DK],
          ['u', 5, 1, 2, 2, AQ], ['u', 1, 3, 1, 2, GD],
        ],
      }),
      E('head', [4.5, 9, 5], [11.5, 13, 11], {
        c: LT, pat: crack, r: [
          ['n', 0, 0, 7, 1, DK], ['n', 0, 1, 1, 3, ST], ['n', 6, 1, 1, 3, ST], ['n', 1, 1, 2, 2, AQ, true], ['n', 4, 1, 2, 2, AQ, true], ['n', 1, 1, 1, 1, AQL, true], ['n', 4, 1, 1, 1, AQL, true], ['n', 2, 3, 3, 1, DK],
          ['s', 4, 1, 2, 2, GD], ['e', 1, 1, 2, 2, GD], ['w', 3, 2, 1, 2, AQ], ['u', 1, 1, 2, 2, AQ], ['u', 4, 3, 1, 2, GD],
        ],
      }),
      E('arm left', [2.5, 4, 6], [4, 8, 10], { c: DK, pat: crack, r: [['n', 0, 3, 2, 1, ST], ['w', 1, 1, 1, 2, GD], ['w', 2, 2, 2, 1, AQ], ['u', 0, 0, 2, 4, ST]] }),
      E('arm right', [12, 4, 6], [13.5, 8, 10], { c: DK, pat: crack, r: [['n', 0, 3, 2, 1, ST], ['e', 1, 1, 1, 2, AQ], ['e', 2, 2, 2, 1, GD], ['u', 0, 0, 2, 4, ST]] }),
    ],
  });
}

// 3. Wood owl (Woodcutting): barrel body, big round eyes, orange beak, ear tufts, small wings, tiny feet
{
  const BARK = hex('#7A5230'), BD = hex('#4E331C'), CREAM = hex('#E9D5A7'), ORG = hex('#E8892B');
  const bark = (f, x, y, w, h) => (f === 'u' || f === 'd') ? ((x + y) % 4 === 0 ? sh(BARK, 0.85) : null) : (x % 3 === 1 && y % 2 === 0 ? sh(BARK, 0.82) : (y === h - 1 ? sh(BARK, 0.9) : null));
  const disc = (ox, oy) => [['n', ox, oy, 3, 3, CREAM, true], ['n', ox, oy, 1, 1, BARK], ['n', ox + 2, oy, 1, 1, BARK], ['n', ox, oy + 2, 1, 1, BARK], ['n', ox + 2, oy + 2, 1, 1, BARK], ['n', ox + 1, oy + 1, 1, 1, EYE, true]];
  spirits.push({
    id: 'wood_owl', elements: [
      E('foot left', [5, 3, 6], [7, 4, 9], { c: ORG }),
      E('foot right', [9, 3, 6], [11, 4, 9], { c: ORG }),
      E('body', [4, 4, 5], [12, 10, 11], {
        c: BARK, pat: bark, r: [
          ['n', 0, 0, 8, 1, BD], ...disc(0, 1), ...disc(5, 1),
          ['n', 1, 4, 6, 2, CREAM], ['n', 2, 5, 1, 1, sh(CREAM, 0.8)], ['n', 4, 4, 1, 1, sh(CREAM, 0.8)], ['n', 5, 5, 1, 1, sh(CREAM, 0.8)], ['n', 0, 4, 1, 2, BD], ['n', 7, 4, 1, 2, BD],
          ['s', 0, 0, 8, 1, BD], ['s', 1, 2, 6, 1, BD], ['s', 0, 5, 8, 1, BD],
          ['e', 1, 1, 4, 1, BD], ['w', 1, 1, 4, 1, BD], ['e', 2, 3, 3, 1, BD], ['w', 2, 3, 3, 1, BD],
        ],
      }),
      E('cap', [5, 10, 5], [11, 11, 11], { c: BD, fc: { u: BARK }, pat: (f, x, y) => f === 'u' && (x + y) % 3 === 0 ? sh(BARK, 0.8) : null }),
      E('beak', [7, 5, 4], [9, 6, 5], { c: ORG, r: [['n', 0, 0, 2, 1, sh(ORG, 0.85)]] }),
      E('tail', [6, 4, 11], [10, 8, 12], { c: BD, pat: (f, x, y) => (f === 'n' || f === 's') && x % 2 === 0 ? BARK : null }),
      E('ear tuft left', [5, 11, 5], [7, 13, 6], { c: BD, rot: ['z', 22.5, [6, 11, 5.5]], r: [['n', 0, 0, 1, 1, BARK]] }),
      E('ear tuft right', [9, 11, 5], [11, 13, 6], { c: BD, rot: ['z', -22.5, [10, 11, 5.5]], r: [['n', 1, 0, 1, 1, BARK]] }),
      E('wing left', [3, 6, 6], [4, 10, 9], { c: BD, rot: ['z', -22.5, [4, 10, 7.5]], pat: (f, x, y, w, h) => (f === 'n' || f === 's' || f === 'w' || f === 'e') && y % 2 === 1 ? BARK : null }),
      E('wing right', [12, 6, 6], [13, 10, 9], { c: BD, rot: ['z', 22.5, [12, 10, 7.5]], pat: (f, x, y, w, h) => (f === 'n' || f === 's' || f === 'w' || f === 'e') && y % 2 === 1 ? BARK : null }),
    ],
  });
}

// 4. Forage fox (Foraging): fox with white cheeks, dark ear tips, low body, bushy white-tipped tail, sprig and berry
{
  const OR = hex('#E0782B'), OD = hex('#A9521A'), WH = hex('#F5EFE6'), DK = hex('#3B2A20'), GR = hex('#5FA83A'), RD = hex('#C8372D');
  spirits.push({
    id: 'forage_fox', elements: [
      E('leg front left', [5, 3, 7], [7, 5, 9], { c: DK }),
      E('leg front right', [9, 3, 7], [11, 5, 9], { c: DK }),
      E('leg back left', [5, 3, 10], [7, 5, 12], { c: DK }),
      E('leg back right', [9, 3, 10], [11, 5, 12], { c: DK }),
      E('body', [5, 5, 7], [11, 9, 12], { c: OR, fc: { d: OD }, r: [['n', 1, 2, 4, 2, WH], ['s', 0, 3, 6, 1, OD], ['u', 2, 0, 2, 5, OD]] }),
      E('head', [4, 6, 3], [12, 11, 8], {
        c: OR, r: [
          ['n', 0, 3, 3, 2, WH], ['n', 5, 3, 3, 2, WH], ['n', 0, 2, 1, 1, WH], ['n', 7, 2, 1, 1, WH],
          ['n', 1, 1, 2, 2, DK, true], ['n', 5, 1, 2, 2, DK, true], ['n', 1, 1, 1, 1, GLINT, true], ['n', 5, 1, 1, 1, GLINT, true],
          ['n', 0, 0, 8, 1, OD], ['ew', 0, 3, 5, 2, WH], ['ew', 0, 0, 5, 1, OD], ['s', 0, 0, 8, 1, OD], ['u', 0, 0, 8, 1, OD],
        ],
      }),
      E('muzzle', [7, 6, 2], [9, 8, 3], { c: WH, r: [['n', 0, 0, 2, 1, DK, true], ['n', 0, 0, 1, 1, GLINT, true]] }),
      E('ear left', [4, 11, 4], [6, 13, 5], { c: OR, rot: ['z', 22.5, [5, 11, 4.5]], r: [['v', 0, 0, 2, 1, DK], ['u', 0, 0, 2, 1, DK], ['n', 0, 1, 2, 1, hex('#F0A06A')]] }),
      E('ear right', [10, 11, 4], [12, 13, 5], { c: OR, rot: ['z', -22.5, [11, 11, 4.5]], r: [['v', 0, 0, 2, 1, DK], ['u', 0, 0, 2, 1, DK], ['n', 0, 1, 2, 1, hex('#F0A06A')]] }),
      E('tail base', [6, 5, 12], [10, 8, 14], { c: OR, fc: { d: OD } }),
      E('tail mid', [6, 8, 12], [10, 11, 14], { c: OR }),
      E('tail tip', [6, 11, 12], [10, 13, 14], { c: WH, rot: ['x', -22.5, [8, 11, 13]] }),
      E('berry', [9, 5, 1], [11, 7, 2], { c: RD, r: [['n', 0, 0, 1, 1, lighten(RD, 0.5), true]] }),
      E('sprig', [10, 6, 2], [13, 8, 3], { c: GR, rot: ['z', 22.5, [10, 6, 2.5]], pat: (f, x, y, w, h) => (f === 'n' && x === y) ? sh(GR, 0.72) : null }),
    ],
  });
}

// ---------- pack v2.6.0: the eight v3.58 spirits (appended AFTER the first four, so their textures stay byte for byte) ----------
const dots2 = (ox, oy, c) => [['n', ox, oy, 1, 1, c, true], ['n', ox + 3, oy, 1, 1, c, true]];

// 5. Harvest hare (Farming tokens): sandy rabbit, tall pink-lined ears, cream belly, holds a carrot
{
  const FUR = hex('#C9A27C'), FD = hex('#9C7A57'), CR = hex('#F1E4CF'), PK = hex('#E9A2AB'), CA = hex('#EA8A2C'), LF = hex('#5FA83A');
  spirits.push({
    id: 'harvest_hare', elements: [
      E('foot left', [5, 3, 4], [7, 4, 8], { c: CR }),
      E('foot right', [9, 3, 4], [11, 4, 8], { c: CR }),
      E('body', [5, 4, 6], [11, 9, 11], { c: FUR, fc: { d: FD }, r: [['n', 1, 1, 4, 4, CR], ['u', 0, 0, 6, 1, FD]] }),
      E('head', [5.5, 8, 4], [10.5, 12, 8], {
        c: FUR, r: [...dots2(1, 1, EYE), ['n', 1, 1, 1, 1, EYE, true], ['n', 2, 2, 1, 1, PK, true], ['n', 1, 3, 3, 1, CR], ['ew', 0, 3, 4, 1, CR]],
      }),
      E('ear left', [6, 12, 5.5], [7.5, 16, 6.5], { c: FUR, rot: ['z', 22.5, [6.75, 12, 6]], r: [['n', 0, 1, 1, 3, PK], ['u', 0, 0, 2, 1, FD]] }),
      E('ear right', [8.5, 12, 5.5], [10, 16, 6.5], { c: FUR, rot: ['z', -22.5, [9.25, 12, 6]], r: [['n', 1, 1, 1, 3, PK], ['u', 0, 0, 2, 1, FD]] }),
      E('tail', [7, 5, 11], [9, 7, 12], { c: CR }),
      E('carrot', [10, 4, 3], [11.5, 8, 4.5], { c: CA, pat: (f, x, y) => (f !== 'u' && f !== 'd' && y % 2 === 1 && x === 0) ? sh(CA, 0.78) : null }),
      E('carrot leaves', [10, 8, 3], [11.5, 9.5, 4.5], { c: LF, rot: ['z', -22.5, [10.75, 8, 3.75]] }),
    ],
  });
}

// 6. Gem beetle (Mining tokens): glossy emerald shell with a split line, cyan gem on the back, dark head and six legs
{
  const SH = hex('#25B26A'), SD = hex('#157A47'), SL = hex('#8CF0B8'), DK = hex('#1F2629'), GEM = hex('#5FE9E2');
  const shell = (f, x, y, w, h) => f === 'u' && x === (w >> 1) ? SD : ((f === 'u' && (x + y) % 5 === 0) ? SL : null);
  const leg = (name, x0, z0) => E(name, [x0, 3, z0], [x0 + 1, 5, z0 + 1], { c: DK });
  spirits.push({
    id: 'gem_beetle', elements: [
      leg('leg front left', 3.5, 6), leg('leg mid left', 3.5, 8.5), leg('leg back left', 3.5, 11),
      leg('leg front right', 11.5, 6), leg('leg mid right', 11.5, 8.5), leg('leg back right', 11.5, 11),
      E('shell', [4.5, 4, 6], [11.5, 8, 12.5], { c: SH, fc: { d: DK }, pat: shell, r: [['v', 0, 3, 7, 1, SD], ['n', 1, 0, 2, 1, SL], ['e', 1, 0, 2, 1, SL]] }),
      E('head', [6, 4, 3.5], [10, 7, 6], { c: DK, r: [['n', 0, 0, 1, 1, GLINT, true], ['n', 3, 0, 1, 1, GLINT, true], ['n', 1, 2, 2, 1, sh(DK, 1.6)]] }),
      E('horn', [7.5, 6, 3], [8.5, 9, 4], { c: SD, rot: ['x', -22.5, [8, 6, 3.5]], r: [['a', 0, 0, 1, 1, SL]] }),
      E('gem', [7, 8, 8], [9, 9.5, 10], { c: GEM, r: [['n', 0, 0, 1, 1, lighten(GEM, 0.6), true], ['u', 0, 0, 1, 1, lighten(GEM, 0.6), true]] }),
    ],
  });
}

// 7. Bark squirrel (Forestry tokens): russet squirrel, cream cheeks and belly, big striped tail curling over, holds an acorn
{
  const RU = hex('#A35A2C'), RD = hex('#6E3A1C'), CR = hex('#EEDDBE'), AC = hex('#B07A3A'), CAP = hex('#6B4A26');
  const stripe = (f, x, y) => (f !== 'u' && f !== 'd' && y % 2 === 0) ? lighten(RU, 0.25) : null;
  spirits.push({
    id: 'bark_squirrel', elements: [
      E('foot left', [5, 3, 5], [7, 4, 8], { c: RD }),
      E('foot right', [9, 3, 5], [11, 4, 8], { c: RD }),
      E('body', [5.5, 4, 6], [10.5, 9, 10], { c: RU, r: [['n', 1, 1, 3, 4, CR]] }),
      E('head', [5.5, 9, 4.5], [10.5, 13, 8.5], { c: RU, r: [['n', 1, 1, 1, 1, EYE, true], ['n', 3, 1, 1, 1, EYE, true], ['n', 0, 2, 2, 2, CR], ['n', 3, 2, 2, 2, CR], ['n', 2, 2, 1, 1, RD, true]] }),
      E('ear left', [6, 13, 6], [7, 14.5, 7], { c: RU, r: [['u', 0, 0, 1, 1, RD]] }),
      E('ear right', [9, 13, 6], [10, 14.5, 7], { c: RU, r: [['u', 0, 0, 1, 1, RD]] }),
      E('tail base', [6, 4, 10], [10, 9, 13], { c: RU, pat: stripe }),
      E('tail top', [6, 9, 11], [10, 13, 14], { c: RU, pat: stripe }),
      E('tail curl', [6, 12, 9.5], [10, 15, 12], { c: lighten(RU, 0.15), rot: ['x', -22.5, [8, 12, 11]] }),
      E('acorn', [7, 5, 4], [9, 7, 5.5], { c: AC, r: [['n', 0, 0, 1, 1, lighten(AC, 0.35)]] }),
      E('acorn cap', [6.75, 7, 3.75], [9.25, 8, 5.75], { c: CAP, pat: (f, x, y) => (x + y) % 2 === 0 ? sh(CAP, 0.8) : null }),
    ],
  });
}

// 8. Petal moth (Foraging tokens): fluffy cream body, big black eyes, feathery antennae, pink wings with rose spots
{
  const BO = hex('#F2E3C6'), FU = hex('#FFF6E6'), WG = hex('#F2A3C2'), WD = hex('#C9628C'), WL = hex('#FAD3E3'), AN = hex('#B9875A');
  const wing = (f, x, y, w, h) => (f === 'n' || f === 's') ? ((x === 0 || y === 0 || x === w - 1 || y === h - 1) ? WD : ((x * 3 + y * 5) % 7 === 0 ? WL : null)) : null;
  spirits.push({
    id: 'petal_moth', elements: [
      E('body', [7, 4, 6], [9, 9, 10], { c: BO, pat: (f, x, y) => (f !== 'u' && f !== 'd' && y % 2 === 1) ? sh(BO, 0.88) : null }),
      E('fluff', [6.5, 8, 5.5], [9.5, 9.5, 8.5], { c: FU }),
      E('head', [6.5, 9, 4.5], [9.5, 11.5, 7], { c: FU, r: [['n', 0, 0, 1, 2, EYE, true], ['n', 2, 0, 1, 2, EYE, true], ['n', 0, 0, 1, 1, GLINT, true], ['n', 2, 0, 1, 1, GLINT, true]] }),
      E('antenna left', [6.5, 11.5, 5], [7.5, 14.5, 6], { c: AN, rot: ['z', 22.5, [7, 11.5, 5.5]], r: [['a', 0, 0, 1, 1, lighten(AN, 0.3)]] }),
      E('antenna right', [8.5, 11.5, 5], [9.5, 14.5, 6], { c: AN, rot: ['z', -22.5, [9, 11.5, 5.5]], r: [['a', 0, 0, 1, 1, lighten(AN, 0.3)]] }),
      E('wing upper left', [2, 7, 7], [7, 12, 8], { c: WG, rot: ['y', -22.5, [7, 9.5, 7.5]], pat: wing, r: [['ns', 1, 1, 2, 2, WD]] }),
      E('wing upper right', [9, 7, 7], [14, 12, 8], { c: WG, rot: ['y', 22.5, [9, 9.5, 7.5]], pat: wing, r: [['ns', 2, 1, 2, 2, WD]] }),
      E('wing lower left', [3, 4, 7.5], [7, 7.5, 8.5], { c: WL, rot: ['y', -22.5, [7, 6, 8]], pat: wing }),
      E('wing lower right', [9, 4, 7.5], [13, 7.5, 8.5], { c: WL, rot: ['y', 22.5, [9, 6, 8]], pat: wing }),
    ],
  });
}

// 9. Battle hound (Slaying XP): grey war dog with a red bandana, darker back, scarred muzzle, ears back
{
  const GR = hex('#8D8F98'), GD = hex('#5E6069'), GL = hex('#C4C6CC'), RED = hex('#C23B32'), NO = hex('#1E1C1F');
  const leg = (name, x0, z0) => E(name, [x0, 3, z0], [x0 + 1.5, 5, z0 + 1.5], { c: GD });
  spirits.push({
    id: 'battle_hound', elements: [
      leg('leg front left', 5, 6), leg('leg front right', 9.5, 6), leg('leg back left', 5, 10), leg('leg back right', 9.5, 10),
      E('body', [5, 5, 6], [11, 9, 12], { c: GR, fc: { u: GD }, r: [['n', 1, 1, 4, 3, GL]] }),
      E('head', [5.5, 7, 2.5], [10.5, 11.5, 6.5], { c: GR, r: [['n', 1, 1, 1, 1, EYE, true], ['n', 3, 1, 1, 1, EYE, true], ['n', 1, 0, 1, 1, GD], ['n', 3, 0, 1, 1, GD], ['u', 0, 0, 5, 2, GD]] }),
      E('snout', [6.5, 7, 1], [9.5, 9, 2.5], { c: GL, r: [['n', 1, 0, 1, 1, NO, true], ['n', 0, 1, 3, 1, sh(GL, 0.8)], ['u', 2, 0, 1, 2, hex('#B07A7A')]] }),
      E('ear left', [5.5, 11.5, 4], [6.5, 13, 5.5], { c: GD, rot: ['x', 22.5, [6, 11.5, 4.75]] }),
      E('ear right', [9.5, 11.5, 4], [10.5, 13, 5.5], { c: GD, rot: ['x', 22.5, [10, 11.5, 4.75]] }),
      E('bandana', [4.75, 7.5, 5.75], [11.25, 9, 7], { c: RED, r: [['n', 0, 0, 7, 1, lighten(RED, 0.25)], ['n', 3, 1, 1, 1, GLINT, true]] }),
      E('tail', [7.5, 8, 12], [8.5, 11.5, 13], { c: GR, rot: ['x', 22.5, [8, 8, 12.5]], r: [['u', 0, 0, 1, 1, GL]] }),
    ],
  });
}

// 10. Bounty raven (Token bonus): blue-black raven, gold eyes, grey beak holding a gold token coin
{
  const BK = hex('#2A2733'), BP = hex('#3C3557'), BG = hex('#4E4E58'), GO = hex('#F0C24A'), GOD = hex('#B8862A');
  const sheen = (f, x, y) => (f !== 'd' && (x + 2 * y) % 5 === 0) ? BP : null;
  spirits.push({
    id: 'bounty_raven', elements: [
      E('foot left', [6, 3, 7], [7, 4, 9], { c: BG }),
      E('foot right', [9, 3, 7], [10, 4, 9], { c: BG }),
      E('body', [5, 4, 6], [11, 9, 11], { c: BK, pat: sheen }),
      E('head', [5.5, 9, 4.5], [10.5, 12.5, 8.5], { c: BK, pat: sheen, r: [['n', 0, 1, 1, 1, GO, true], ['n', 4, 1, 1, 1, GO, true], ['ew', 0, 1, 1, 1, GO, true]] }),
      E('beak', [7, 9.5, 2.5], [9, 11, 4.5], { c: BG, r: [['u', 0, 0, 2, 1, sh(BG, 0.8)]] }),
      E('coin', [6.75, 8, 2.25], [9.25, 10.5, 2.75], { c: GO, r: [['ns', 1, 1, 1, 1, GOD, true], ['ns', 0, 0, 1, 1, lighten(GO, 0.5), true]] }),
      E('wing left', [4, 5, 6.5], [5, 9, 10.5], { c: BK, rot: ['z', -22.5, [5, 9, 8.5]], pat: (f, x, y) => y % 2 === 1 ? BP : null }),
      E('wing right', [11, 5, 6.5], [12, 9, 10.5], { c: BK, rot: ['z', 22.5, [11, 9, 8.5]], pat: (f, x, y) => y % 2 === 1 ? BP : null }),
      E('tail', [6.5, 5, 11], [9.5, 6, 14], { c: BK, rot: ['x', 22.5, [8, 5.5, 11]], pat: (f, x) => x % 2 === 0 ? BP : null }),
    ],
  });
}

// 11. Ember drake (Epic/Legendary, Slaying damage): red little dragon, glowing orange belly, cream horns, raised wings, flame tail
{
  const RD = hex('#B3321F'), RK = hex('#7A1F14'), OR = hex('#F28A2E'), YE = hex('#FFD24A'), HN = hex('#E9D8B0');
  const leg = (name, x0, z0) => E(name, [x0, 3, z0], [x0 + 1.5, 5, z0 + 2], { c: RK });
  const scales = (f, x, y) => (f !== 'd' && (x + y) % 3 === 0) ? sh(RD, 0.85) : null;
  spirits.push({
    id: 'ember_drake', elements: [
      leg('leg front left', 5.5, 6), leg('leg front right', 9, 6), leg('leg back left', 5.5, 9.5), leg('leg back right', 9, 9.5),
      E('body', [5, 5, 6], [11, 9, 12], { c: RD, fc: { d: OR }, pat: scales, r: [['n', 1, 0, 4, 4, OR], ['n', 2, 1, 2, 2, YE]] }),
      E('head', [6, 8, 3], [10, 11.5, 7], { c: RD, pat: scales, r: [['n', 0, 1, 1, 1, YE, true], ['n', 3, 1, 1, 1, YE, true], ['n', 1, 3, 2, 1, RK], ['ew', 0, 1, 1, 1, YE, true]] }),
      E('horn left', [6.5, 11, 5], [7.5, 13.5, 6], { c: HN, rot: ['x', 22.5, [7, 11, 5.5]] }),
      E('horn right', [8.5, 11, 5], [9.5, 13.5, 6], { c: HN, rot: ['x', 22.5, [9, 11, 5.5]] }),
      E('wing left', [1.5, 9, 6.5], [5, 10, 11], { c: RK, rot: ['z', -22.5, [5, 9.5, 8.75]], pat: (f, x) => f === 'u' && x % 2 === 0 ? OR : null }),
      E('wing right', [11, 9, 6.5], [14.5, 10, 11], { c: RK, rot: ['z', 22.5, [11, 9.5, 8.75]], pat: (f, x) => f === 'u' && x % 2 === 1 ? OR : null }),
      E('tail', [7, 6, 12], [9, 8, 15], { c: RD, pat: scales }),
      E('tail flame', [7, 6.5, 15], [9, 9, 16], { c: OR, r: [['a', 0, 0, 2, 1, YE, true]] }),
    ],
  });
}

// 12. Golden dragon (Epic/Legendary, sell money): sitting gold dragon, cream belly, emerald eyes, pale wings, on a small coin stack
{
  const GO = hex('#E4B22E'), GD = hex('#A87A16'), CR = hex('#F6E7B8'), EM = hex('#2FD07A'), WM = hex('#F3DC8C'), CO = hex('#F7CF57');
  const scales = (f, x, y) => (f !== 'd' && (x * 2 + y) % 4 === 0) ? sh(GO, 0.86) : null;
  spirits.push({
    id: 'golden_dragon', elements: [
      E('coins', [4.5, 3, 4.5], [11.5, 4, 11.5], { c: CO, pat: (f, x, y) => (x + y) % 3 === 0 ? sh(CO, 0.8) : null }),
      E('foot left', [5.5, 4, 5], [7.5, 5, 7.5], { c: GD }),
      E('foot right', [8.5, 4, 5], [10.5, 5, 7.5], { c: GD }),
      E('body', [5.5, 4.5, 6.5], [10.5, 10, 10.5], { c: GO, pat: scales, r: [['n', 1, 0, 3, 5, CR], ['n', 1, 1, 3, 1, sh(CR, 0.88)], ['n', 1, 3, 3, 1, sh(CR, 0.88)]] }),
      E('head', [5.5, 10, 4.5], [10.5, 13.5, 8.5], { c: GO, pat: scales, r: [['n', 1, 1, 1, 1, EM, true], ['n', 3, 1, 1, 1, EM, true], ['ew', 0, 1, 1, 1, EM, true]] }),
      E('snout', [6.5, 10, 3], [9.5, 12, 4.5], { c: GO, r: [['n', 0, 0, 1, 1, GD, true], ['n', 2, 0, 1, 1, GD, true], ['n', 0, 1, 3, 1, CR]] }),
      E('horn left', [6, 13, 6.5], [7, 15.5, 7.5], { c: CR, rot: ['x', 22.5, [6.5, 13, 7]], r: [['u', 0, 0, 1, 1, GD]] }),
      E('horn right', [9, 13, 6.5], [10, 15.5, 7.5], { c: CR, rot: ['x', 22.5, [9.5, 13, 7]], r: [['u', 0, 0, 1, 1, GD]] }),
      E('wing left', [2, 7.5, 9.5], [6, 13, 10.5], { c: WM, rot: ['z', 22.5, [6, 8, 10]], pat: (f, x, y, w, h) => (f === 'n' || f === 's') && (x === 0 || y === 0) ? GD : null }),
      E('wing right', [10, 7.5, 9.5], [14, 13, 10.5], { c: WM, rot: ['z', -22.5, [10, 8, 10]], pat: (f, x, y, w, h) => (f === 'n' || f === 's') && (x === w - 1 || y === 0) ? GD : null }),
      E('tail', [7, 4, 10.5], [9, 6, 14.5], { c: GO, pat: scales, r: [['u', 0, 0, 2, 1, CR]] }),
    ],
  });
}

// ---------- write everything ----------
const P = p => path.join(ROOT, p);
for (const d of ['pack/assets/grindcore/textures/item', 'pack/assets/grindcore/models/item', 'pack/assets/grindcore/items', 'previews/spirits']) fs.mkdirSync(P(d), { recursive: true });
const SHEET_ROWS = Math.ceil(spirits.length / 4) * 2; // 4 spirits per row, two views each (v2.6.0: 12 spirits, 6 rows)
const sheet = new Uint8Array(VW * 4 * VH * SHEET_ROWS * 4);
spirits.forEach((sp, i) => {
  buildSpirit(sp);
  fs.writeFileSync(P(`pack/assets/grindcore/textures/item/spirit_${sp.id}.png`), png(TS, TS, sp.px));
  fs.writeFileSync(P(`pack/assets/grindcore/models/item/spirit_${sp.id}.json`), JSON.stringify(modelJson(sp), null, 2) + '\n');
  fs.writeFileSync(P(`pack/assets/grindcore/items/spirit_${sp.id}.json`), JSON.stringify(itemJson(sp.id), null, 2) + '\n');
  const prev = new Uint8Array(VW * 2 * VH * 4);
  VIEWS.forEach((cam, v) => {
    const img = renderView(sp, cam, VW, VH, 16, 2);
    blit(prev, VW * 2, img, VW, VH, v * VW, 0);
    blit(sheet, VW * 4, img, VW, VH, (i % 4) * VW, (Math.floor(i / 4) * 2 + v) * VH);
  });
  fs.writeFileSync(P(`previews/spirits/spirit_${sp.id}.png`), png(VW * 2, VH, prev));
  console.log(sp.id, sp.elements.length, 'elements');
});
fs.writeFileSync(P('previews/spirits.png'), png(VW * 4, VH * SHEET_ROWS, sheet));

// ---------- validation ----------
let bad = 0;
for (const sp of spirits) {
  const m = JSON.parse(fs.readFileSync(P(`pack/assets/grindcore/models/item/spirit_${sp.id}.json`), 'utf8'));
  const it = JSON.parse(fs.readFileSync(P(`pack/assets/grindcore/items/spirit_${sp.id}.json`), 'utf8'));
  if (it.model.model !== 'grindcore:item/spirit_' + sp.id) { console.log('BAD item model key', sp.id); bad++; }
  for (const t of Object.values(m.textures)) if (!fs.existsSync(P('pack/assets/grindcore/textures/' + t.replace('grindcore:', '') + '.png'))) { console.log('MISSING texture', t); bad++; }
  if (m.elements.length > 20) { console.log('TOO MANY ELEMENTS', sp.id); bad++; }
  for (const e of m.elements) {
    if (e.rotation && ![-45, -22.5, 0, 22.5, 45].includes(e.rotation.angle)) { console.log('BAD ANGLE', sp.id, e.name); bad++; }
    for (const f of FACES) { const uv = e.faces[f] && e.faces[f].uv; if (!uv || uv.some(v => v < 0 || v > 16)) { console.log('BAD UV', sp.id, e.name, f); bad++; } }
  }
}
console.log(bad ? 'VALIDATION FAILED: ' + bad : 'validation ok');
