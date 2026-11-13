// Draws the Forage Bush (pack v2.3.0): the one bush every foraging spot of the Forestry islands shows.
// It replaces the look of the vanilla block minecraft:flowering_azalea (the block the server places at a spot), so it keeps that
// block's hit box: a wide top half and a thin stem. A leafy mound on a short trunk with gold, teal and violet berries.
// Writes assets/minecraft/blockstates/flowering_azalea.json, assets/grindcore/models/block/forage_bush.json,
// assets/grindcore/textures/block/forage_bush.png and previews/forage_bush.png. Deterministic: fixed seed, no dates.
// Usage: node tools/forage_bush.js
const fs = require('fs'), zlib = require('zlib'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const hex = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
let seed = 20261114; const rnd = () => { seed |= 0; seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };

// ---------- texture: 32 x 32, regions in pixels ----------
const TS = 32; const tex = new Uint8Array(TS * TS * 4);
const put = (x, y, c) => { const i = (y * TS + x) * 4; tex[i] = c[0]; tex[i + 1] = c[1]; tex[i + 2] = c[2]; tex[i + 3] = 255; };
const LEAF = [hex('#245C33'), hex('#2F7A3C'), hex('#3E9447'), hex('#5DB34F'), hex('#86CF5C')];
const REG = { leaf: [0, 0, 16, 16], deep: [16, 0, 16, 16], bark: [0, 16, 8, 8], gold: [8, 16, 4, 4], teal: [12, 16, 4, 4], violet: [16, 16, 4, 4] };
// leaves: clustered blobs of light on a mid green, a few dark gaps
for (const [name, bias] of [['leaf', 0], ['deep', -1]]) {
  const [ox, oy, w, h] = REG[name]; const v = [];
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) v.push(rnd());
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let s = 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) s += v[((y + dy + h) % h) * w + ((x + dx + w) % w)];
    const k = s / 9 * 0.6 + v[y * w + x] * 0.4; const idx = Math.max(0, Math.min(4, Math.floor(k * 5.4) + bias));
    put(ox + x, oy + y, LEAF[idx]);
  }
}
{ const [ox, oy, w, h] = REG.bark; const B = [hex('#4A3323'), hex('#5E4330'), hex('#3A2719')]; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) put(ox + x, oy + y, B[(x % 3 === 0 ? 2 : rnd() < 0.3 ? 1 : 0)]); }
for (const [name, base, hi, lo] of [['gold', '#E0B11E', '#FFE27A', '#A87A10'], ['teal', '#35C9BE', '#A6F2EA', '#1D8C86'], ['violet', '#B07CE8', '#E2C7FF', '#7446B0']]) {
  const [ox, oy] = REG[name]; for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) put(ox + x, oy + y, hex(x + y <= 1 ? hi : x + y >= 5 ? lo : base));
}

// ---------- elements (block units, the block is 0..16) ----------
const EL = [
  ['trunk', [6, 0, 6], [10, 6, 10], 'bark'], ['root_a', [5, 0, 7], [6, 2, 9], 'bark'], ['root_b', [10, 0, 7], [11, 2, 9], 'bark'],
  ['skirt', [4, 4, 4], [12, 8, 12], 'deep'],
  ['belly', [1, 7, 1], [15, 11, 15], 'deep'],
  ['wide_x', [0, 9, 3], [16, 12, 13], 'leaf'], ['wide_z', [3, 9, 0], [13, 12, 16], 'leaf'],
  ['shoulder', [2, 11, 2], [14, 14, 14], 'leaf'],
  ['head', [4, 13, 4], [12, 16, 12], 'leaf'],
  ['crown', [6, 15, 6], [10, 18, 10], 'leaf'],
  ['tuft_a', [1, 12, 9], [4, 15, 12], 'deep'], ['tuft_b', [11, 12, 2], [14, 15, 5], 'deep'],
  ['berry_1', [-1, 9, 5], [1, 11, 7], 'violet'], ['berry_2', [15, 9, 9], [17, 11, 11], 'gold'], ['berry_3', [8, 9, -1], [10, 11, 1], 'teal'], ['berry_4', [5, 9, 15], [7, 11, 17], 'violet'],
  ['berry_5', [2, 13, 4], [4, 15, 6], 'gold'], ['berry_6', [12, 13, 10], [14, 15, 12], 'teal'], ['berry_7', [7, 17, 7], [9, 19, 9], 'violet'], ['berry_8', [10, 15, 4], [12, 17, 6], 'gold'], ['berry_9', [4, 15, 10], [6, 17, 12], 'teal'],
];
const FACES = { north: ['x', 'y'], south: ['x', 'y'], east: ['z', 'y'], west: ['z', 'y'], up: ['x', 'z'], down: ['x', 'z'] };
const AX = { x: 0, y: 1, z: 2 };
function uv(regionName, w, h, n) { // a w x h pixel window inside the region, moved a little per face so repeats do not line up
  const [ox, oy, rw, rh] = REG[regionName]; const ww = Math.min(w, rw); const hh = Math.min(h, rh);
  const sx = (n * 5) % (rw - ww + 1); const sy = (n * 3) % (rh - hh + 1);
  const k = 16 / TS; return [(ox + sx) * k, (oy + sy) * k, (ox + sx + ww) * k, (oy + sy + hh) * k];
}
const elements = EL.map(([name, from, to, region], n) => {
  const faces = {};
  Object.entries(FACES).forEach(([f, [a, b]], fi) => { faces[f] = { uv: uv(region, to[AX[a]] - from[AX[a]], to[AX[b]] - from[AX[b]], n + fi), texture: '#0' }; });
  return { name, from, to, shade: true, faces };
});
const model = { parent: 'minecraft:block/block', render_type: 'minecraft:cutout', textures: { 0: 'grindcore:block/forage_bush', particle: 'grindcore:block/forage_bush' }, elements,
  display: { gui: { rotation: [30, 225, 0], translation: [0, -1, 0], scale: [0.55, 0.55, 0.55] }, ground: { translation: [0, 3, 0], scale: [0.25, 0.25, 0.25] }, fixed: { scale: [0.5, 0.5, 0.5] },
    thirdperson_righthand: { rotation: [75, 45, 0], translation: [0, 2.5, 0], scale: [0.375, 0.375, 0.375] }, firstperson_righthand: { rotation: [0, 45, 0], scale: [0.4, 0.4, 0.4] } } };
const blockstate = { variants: { '': { model: 'grindcore:block/forage_bush' } } };

// ---------- PNG ----------
const crcT = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crcT[n] = c >>> 0; }
const crc = (b) => { let c = 0xffffffff; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
function png(w, h, rgba) {
  const raw = Buffer.alloc((w * 4 + 1) * h); for (let y = 0; y < h; y++) { raw[y * (w * 4 + 1)] = 0; Buffer.from(rgba.buffer, rgba.byteOffset + y * w * 4, w * 4).copy(raw, y * (w * 4 + 1) + 1); }
  const chunk = (t, d) => { const len = Buffer.alloc(4); len.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t, 'ascii'), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([len, td, c]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}

// ---------- preview: the model as unit voxels, seen from two sides ----------
function preview() {
  const S = 10; const N = 24; const off = 3; const vox = new Map();
  EL.forEach(([, from, to, region], n) => { for (let x = from[0]; x < to[0]; x++) for (let y = from[1]; y < to[1]; y++) for (let z = from[2]; z < to[2]; z++) { const [ox, oy, rw, rh] = REG[region]; const i = ((oy + ((y * 3 + z + n) % rh)) * TS + ox + ((x * 5 + z * 2 + n) % rw)) * 4; vox.set(x + ',' + y + ',' + z, [tex[i], tex[i + 1], tex[i + 2]]); } });
  const W = N * 4 * S; const H = N * 3 * S; const img = new Uint8Array(W * 2 * H * 4);
  for (let i = 0; i < W * 2 * H; i++) { img[i * 4] = 38; img[i * 4 + 1] = 44; img[i * 4 + 2] = 56; img[i * 4 + 3] = 255; }
  const rect = (px, py, w, h, c) => { for (let y = Math.max(0, py); y < Math.min(H, py + h); y++) for (let x = Math.max(0, px); x < Math.min(W * 2, px + w); x++) { const i = (y * W * 2 + x) * 4; img[i] = c[0]; img[i + 1] = c[1]; img[i + 2] = c[2]; } };
  for (let view = 0; view < 2; view++) {
    const get = (x, y, z) => (view ? vox.get((15 - x) + ',' + y + ',' + (15 - z)) : vox.get(x + ',' + y + ',' + z));
    for (let s = -3 * off; s <= 3 * (N - off); s++) for (let x = -off; x < N - off; x++) for (let z = -off; z < N - off; z++) {
      const y = s - x - z; if (y < 0 || y > 20) continue; const c = get(x, y, z); if (!c) continue;
      const px = view * W + W / 2 + (x - z) * 2 * S; const py = H - 4 * S + (x + z - 2 * off) * S - (y + 1) * 2 * S - 12 * S;
      if (!get(x, y + 1, z)) rect(px - 2 * S, py, 4 * S, 2 * S, c);
      if (!get(x, y, z + 1)) rect(px - 2 * S, py + 2 * S, 2 * S, 2 * S, c.map((v) => Math.round(v * 0.74)));
      if (!get(x + 1, y, z)) rect(px, py + 2 * S, 2 * S, 2 * S, c.map((v) => Math.round(v * 0.56)));
    }
  }
  return png(W * 2, H, img);
}

// ---------- write and check ----------
const P = (p) => path.join(ROOT, p); const out = (p, data) => { fs.mkdirSync(path.dirname(P(p)), { recursive: true }); fs.writeFileSync(P(p), data); };
out('pack/assets/grindcore/textures/block/forage_bush.png', png(TS, TS, tex));
out('pack/assets/grindcore/models/block/forage_bush.json', JSON.stringify(model, null, 1) + '\n');
out('pack/assets/minecraft/blockstates/flowering_azalea.json', JSON.stringify(blockstate, null, 1) + '\n');
out('previews/forage_bush.png', preview());
let problems = 0;
for (const e of elements) { for (let a = 0; a < 3; a++) if (e.from[a] < -16 || e.to[a] > 32 || e.to[a] <= e.from[a]) { problems++; console.log('bad element ' + e.name); } for (const f of Object.values(e.faces)) if (f.uv.some((v) => v < 0 || v > 16)) { problems++; console.log('bad uv ' + e.name); } }
console.log(elements.length + ' elements, texture ' + TS + 'x' + TS + ', problems ' + problems);
process.exit(problems ? 1 : 0);
