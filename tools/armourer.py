"""Armourer's Forge cuboid model in the Phase 2 workstation style (same pipeline, palette and transforms)."""
from pathlib import Path
import random
import numpy as np
from PIL import Image, ImageDraw
import pipeline as P

ROOT = Path(__file__).resolve().parent / 'armourer'
P.ROOT = ROOT; P.PACK = ROOT / 'pack'; P.SIZE = 256
KEY = 'armourers_forge'
PALETTE = {'oak': (154, 105, 53), 'oak_end': (164, 117, 64), 'spruce': (102, 70, 43),
           'iron': (53, 56, 59), 'steel': (152, 164, 164), 'bronze': (150, 109, 56), 'gold': (206, 156, 46),
           'stone': (61, 66, 66), 'stone_top': (79, 85, 82), 'basalt': (43, 46, 51),
           'basin': (44, 70, 68), 'shield': (128, 38, 40), 'coal': (40, 33, 31), 'ember': (231, 103, 27)}


def pixel_tile(material, width, height, seed, face):
    rng = random.Random(seed); base = np.array(PALETTE[material]); im = Image.new('RGBA', (width, height))
    for y in range(height):
        for x in range(width):
            v = rng.choice((-3, 0, 0, 0, 2, 3))
            if x == 0 or y == 0: v += 8
            if x == width - 1 or y == height - 1: v -= 10
            if material in ('oak', 'spruce'):
                v += -13 if x % 7 == 0 else 5 if x % 7 == 1 else 0
            elif material == 'oak_end':
                r = max(abs(x - width // 2), abs(y - height // 2)); v += -15 if r % 4 == 0 else 3
            elif material in ('stone', 'stone_top', 'basalt'):
                v += 4 if (x // 4 + y // 3) % 3 == 0 else -3
                if material == 'basalt' and y % 9 == 0: v -= 10
                if material == 'basalt' and (x * 7 + y * 3 + seed) % 23 == 0:
                    im.putpixel((x, y), (196, 150, 52, 255)); continue  # gilded blackstone flecks
            elif material == 'ember':
                v += 18 if (x // 2 + y // 2) % 3 == 0 else -24 if (x + y) % 6 == 0 else 0
            elif material == 'coal':
                if (x + 2 * y + seed) % 8 < 2: im.putpixel((x, y), (210, 78, 23, 255)); continue
            elif material in ('iron', 'steel', 'bronze', 'gold'):
                v += 8 if y == 1 else -5 if x % 9 == 0 else 0
                if material == 'gold' and (x + y) % 5 == 0: v += 14
            im.putpixel((x, y), tuple(int(z) for z in np.clip(base + v, 0, 255)) + (255,))
    d = ImageDraw.Draw(im)
    if material == 'shield' and face == 'north' and width >= 5 and height >= 5:
        cx = width // 2
        d.line([(cx, 1), (cx, height - 2)], fill=(214, 170, 64, 255))
        d.line([(1, height // 3), (width - 2, height // 3)], fill=(214, 170, 64, 255))
    if material == 'basin' and face == 'up' and width > 3 and height > 3:
        d.line([(1, height // 2), (width - 2, height // 2)], fill=(95, 135, 119, 255))
    return im


def displays(parts):
    pts = []
    for p in parts:
        e = {'from': p['from'], 'to': p['to']}
        if p['rot']: e['rotation'] = {'axis': p['rot'][0], 'angle': p['rot'][1], 'origin': p['origin']}
        pts.extend(P.local_vertices(e))
    projected = (np.array(pts) - 8) @ P.rotation(27, 205).T
    lo, hi = projected.min(axis=0), projected.max(axis=0)
    s = round(13.6 / max((hi - lo)[:2]), 5); t = np.round(-(lo + hi) / 2 * s, 5).tolist(); t[2] = 0
    return {'gui': {'rotation': [27, 205, 0], 'translation': t, 'scale': [s] * 3},
            'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [.3] * 3},
            'fixed': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [1] * 3},
            'head': {'rotation': [0, 180, 0], 'translation': [0, 13, 0], 'scale': [.6] * 3},
            'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2.5, 0], 'scale': [.28] * 3},
            'thirdperson_lefthand': {'rotation': [75, 225, 0], 'translation': [0, 2.5, 0], 'scale': [.28] * 3},
            'firstperson_righthand': {'rotation': [0, 45, 0], 'translation': [0, 1, 0], 'scale': [.32] * 3},
            'firstperson_lefthand': {'rotation': [0, 225, 0], 'translation': [0, 1, 0], 'scale': [.32] * 3}}


P.pixel_tile = pixel_tile
P.displays = displays


def geometry():
    m = P.Relic(KEY); B = m.box
    # Gilded blackstone plinth (the item's base material) with a gold band.
    B('Gilded blackstone plinth', (1, 0, 2), (15, 1.5, 14), 'basalt', 'stone_top')
    B('Front gold band', (1, .4, 1.8), (15, 1.1, 2), 'gold')
    # Left: heavy stone workbench with an iron top, a helmet in progress and a hammer.
    B('Bench left pier', (1.5, 1.5, 4), (3.5, 7, 12), 'stone')
    B('Bench right pier', (7, 1.5, 4), (9, 7, 12), 'stone')
    B('Stored plate stack', (3.5, 1.5, 5), (7, 2.6, 11), 'steel')
    B('Bench iron top', (1, 7, 3.5), (9.5, 8.5, 12.5), 'iron', 'steel')
    B('Bench gold edge', (1.5, 7.5, 3.3), (9, 8.1, 3.5), 'gold')
    B('Helmet rim', (2.7, 8.5, 5.7), (7.3, 9, 10.3), 'gold')
    B('Helmet dome', (3, 9, 6), (7, 11.5, 10), 'steel')
    B('Helmet visor', (3.3, 9.3, 5.6), (6.7, 10.4, 6), 'iron')
    B('Helmet crest', (4.6, 11.5, 6.3), (5.4, 12.6, 9.7), 'gold')
    B('Hammer handle', (7.2, 8.5, 5.2), (7.8, 9.1, 9.4), 'oak')
    B('Hammer head', (6.6, 8.5, 4.3), (8.4, 9.6, 5.2), 'steel')
    # Back: spruce rack with a crimson kite shield.
    B('Rack left post', (1.5, 1.5, 12.5), (2.5, 13, 13.5), 'spruce')
    B('Rack right post', (8, 1.5, 12.5), (9, 13, 13.5), 'spruce')
    B('Rack top rail', (1.3, 13, 12.4), (9.2, 14, 13.6), 'spruce')
    B('Kite shield', (3.4, 8.5, 12.5), (7.1, 12.8, 12.9), 'shield')
    B('Kite shield point', (4.5, 7.4, 12.5), (6, 8.5, 12.9), 'shield')
    B('Shield hook', (5, 12.8, 12.6), (5.5, 13, 12.8), 'iron')
    B('Shield gold boss', (4.8, 10, 12.2), (5.7, 10.9, 12.5), 'gold')
    # Right: oak armour stand with a gilded chestplate and steel pauldrons.
    B('Stand oak base', (10, 1.5, 6), (14.5, 2.3, 10.5), 'oak', 'oak_end')
    B('Stand oak post', (11.75, 2.3, 7.75), (12.75, 7, 8.75), 'oak')
    B('Chestplate body', (10.3, 7, 6.8), (14.2, 12, 9.7), 'gold')
    B('Chestplate steel breast', (11, 8, 6.5), (13.5, 11.5, 6.8), 'steel')
    B('Left pauldron', (9.6, 10.8, 6.5), (10.3, 12.4, 10), 'steel')
    B('Right pauldron', (14.2, 10.8, 6.5), (14.9, 12.4, 10), 'steel')
    B('Stand head peg', (11.9, 12, 7.9), (12.6, 13.4, 8.6), 'oak', 'oak_end')
    # Front right: quench trough with water and a cooling ember tray.
    B('Quench trough', (10, 1.5, 2.4), (14.8, 4, 5.6), 'spruce')
    B('Quench water', (10.5, 4, 2.9), (14.3, 4.2, 5.1), 'basin')
    B('Trough iron band', (9.8, 2.6, 2.2), (15, 3.1, 2.4), 'iron')
    B('Ember tray', (3.8, 2.6, 5.6), (6.6, 3, 10.4), 'ember')
    return m


def main():
    model, sheet = P.export(geometry())
    checks = P.geometry_checks(model)
    prev = ROOT / 'previews'; prev.mkdir(parents=True, exist_ok=True)
    big = P.render(model, sheet, 480); big.save(prev / f'{KEY}-isometric.png')
    gui = P.render(model, sheet, 256, gui=True)
    gui.save(prev / f'{KEY}-gui.png')
    for n in (16, 32):
        P.render(model, sheet, n * 8, gui=True).resize((n, n), Image.Resampling.BOX).save(prev / f'{KEY}-inventory-{n}x{n}.png')
    return model, checks


if __name__ == '__main__':
    import json
    model, checks = main()
    print(json.dumps({'elements': len(model['elements']), 'checks': checks}, indent=1))
