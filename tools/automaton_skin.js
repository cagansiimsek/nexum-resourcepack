// Draws the Automaton skin (owner choice 2026-11-12: design A, "Chud pattern", a bronze robot with an Aether porthole face).
// A 64x64 classic player skin; the server shows it on the Minion Mannequin at 0.55 scale (about one block tall).
// Usage: node tools/automaton_skin.js   (writes pack/assets/grindcore/textures/entity/automaton.png and previews/automaton-skin.png)
const fs = require('fs'), zlib = require('zlib'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const W = 64, px = new Uint8Array(W * W * 4);
const hex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const C = { B: hex('#B8864B'), L: hex('#D9A866'), D: hex('#7A5530'), K: hex('#5E4022'), G: hex('#2E3A3F'), A: hex('#BFEFF0'), H: hex('#E6FFFF') };
let seed = 7; const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
function set(x, y, c, noise = true) {
  const n = noise && c !== C.A && c !== C.H ? Math.round((rnd() - 0.5) * 12) : 0, i = (y * W + x) * 4;
  px[i] = Math.max(0, Math.min(255, c[0] + n)); px[i + 1] = Math.max(0, Math.min(255, c[1] + n)); px[i + 2] = Math.max(0, Math.min(255, c[2] + n)); px[i + 3] = 255;
}
// A face of a cuboid: fill, then let draw(x, y) -> colour or null override per pixel.
function face(x0, y0, w, h, base, draw) { for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) set(x0 + x, y0 + y, (draw && draw(x, y, w, h)) || base); }
// The six faces of a cuboid net at (u, v) with width w, height h, depth d.
function box(u, v, w, h, d, f) {
  face(u + d, v, w, d, f.top || C.D, f.topDraw);
  face(u + d + w, v, w, d, f.bottom || C.K);
  face(u, v + d, d, h, f.side || C.D, f.sideDraw);
  face(u + d, v + d, w, h, f.front || C.B, f.frontDraw);
  face(u + d + w, v + d, d, h, f.side || C.D, f.sideDraw);
  face(u + d + w + d, v + d, w, h, f.back || C.B, f.backDraw);
}
const ring = (x, y, a, b) => (x === a || x === b || y === a || y === b) && x >= a && x <= b && y >= a && y <= b;
// Head: bronze helmet, round Aether porthole, valve wheel on top, ear bolts, grille at the back.
box(0, 0, 8, 8, 8, {
  top: C.B, side: C.B,
  topDraw: (x, y) => ring(x, y, 2, 5) ? C.K : (x === 3 || x === 4) && (y === 3 || y === 4) ? C.L : (y === 1 || y === 6) && (x === 3 || x === 4) ? C.K : null,
  frontDraw: (x, y) => {
    if (y === 0) return C.L;
    if ((x === 0 || x === 7) && (y === 1 || y === 6)) return C.K;
    const inR = x >= 1 && x <= 6 && y >= 1 && y <= 6, inI = x >= 2 && x <= 5 && y >= 2 && y <= 5;
    if (inI) { const corner = (x === 2 || x === 5) && (y === 2 || y === 5); if (corner) return C.G; return (x === 3 || x === 4) && (y === 3 || y === 4) ? C.H : C.A; }
    if (inR) return (x === 1 || x === 6) && (y === 1 || y === 6) ? C.B : C.K;
    if (y === 7) return C.D;
    return null;
  },
  sideDraw: (x, y) => y === 0 ? C.L : (x === 3 || x === 4) && (y === 3 || y === 4) ? C.K : y === 7 ? C.D : null,
  backDraw: (x, y) => y === 0 ? C.L : (x === 1 || x === 3 || x === 4 || x === 6) && y >= 2 && y <= 5 ? C.K : y === 7 ? C.D : null,
});
// Body: collar, gear plate with an Aether core, belt.
box(16, 16, 8, 12, 4, {
  top: C.D, side: C.D, front: C.B, back: C.B,
  frontDraw: (x, y) => {
    if (y === 0) return C.K;
    if ((x === 0 || x === 7) && y === 2) return C.K;
    if (y === 9) return C.K;
    if (x >= 1 && x <= 6 && y >= 2 && y <= 7) {
      if (x >= 3 && x <= 4 && y >= 4 && y <= 5) return y === 4 ? C.H : C.A;
      if (ring(x, y - 1, 2, 5) || ring(x, y, 2, 5)) return x >= 2 && x <= 5 ? C.K : C.D;
      return C.D;
    }
    return y === 1 ? C.L : null;
  },
  backDraw: (x, y) => y === 0 ? C.K : (x === 3 || x === 4) && y >= 1 && y <= 8 ? C.D : (x === 2 || x === 5) && (y === 3 || y === 6) ? C.K : y === 9 ? C.K : null,
});
// Arms: bronze shoulder caps, elbow band, dark hands.
const arm = { side: C.D, front: C.D, back: C.D, top: C.B,
  frontDraw: (x, y) => y <= 2 ? (y === 0 ? C.L : C.B) : y === 6 ? C.K : y >= 10 ? C.K : (y === 4 && (x === 1 || x === 2)) ? C.B : null,
  sideDraw: (x, y) => y <= 2 ? (y === 0 ? C.L : C.B) : y === 6 ? C.K : y >= 10 ? C.K : null };
arm.backDraw = arm.sideDraw;
box(40, 16, 4, 12, 4, arm); box(32, 48, 4, 12, 4, arm);
// Legs: bronze thigh plates, knee band, heavy feet.
const leg = { side: C.D, front: C.D, back: C.D, top: C.D,
  frontDraw: (x, y) => y >= 1 && y <= 4 ? (y === 1 ? C.L : C.B) : y === 5 ? C.K : y >= 10 ? C.K : null,
  sideDraw: (x, y) => y === 5 ? C.K : y >= 10 ? C.K : null };
leg.backDraw = leg.sideDraw;
box(0, 16, 4, 12, 4, leg); box(16, 48, 4, 12, 4, leg);

function png(w, h, rgba) {
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 4 + 1)] = 0; Buffer.from(rgba.buffer, y * w * 4, w * 4).copy(raw, y * (w * 4 + 1) + 1); }
  const crcT = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crcT[n] = c >>> 0; }
  const crc = b => { let c = 0xffffffff; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
  const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}
const out = path.join(ROOT, 'pack/assets/grindcore/textures/entity/automaton.png');
fs.writeFileSync(out, png(W, W, px));
// Preview: the skin sheet at 8x on a grey background.
const S = 8, P = new Uint8Array(W * S * W * S * 4);
for (let y = 0; y < W * S; y++) for (let x = 0; x < W * S; x++) { const s = ((y / S | 0) * W + (x / S | 0)) * 4, d = (y * W * S + x) * 4; const a = px[s + 3]; P[d] = a ? px[s] : 60; P[d + 1] = a ? px[s + 1] : 60; P[d + 2] = a ? px[s + 2] : 64; P[d + 3] = 255; }
fs.mkdirSync(path.join(ROOT, 'previews'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'previews/automaton-skin.png'), png(W * S, W * S, P));
console.log('wrote', out);
