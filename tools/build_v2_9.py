"""SkyGrind combined resource pack v2.9.0 (2026-11-22): v2.8.0 byte for byte plus item icons for the 14 new v3.59 items.

Six Silk Road items (cart_patch_kit, saffron_spice, imperial_silk, damascus_bar, clockwork_gear, sovereign_relic) and eight
Masonry items (mortar, cut_stone, stone_foundation, dressed_slate, reinforced_masonry, polished_marble, carved_obsidian,
runed_keystone). tools/items_v29.js draws them into pack/: per item the definition (model id grindcore:<id>), the
item/generated model and a 32x32 texture. A file that already exists in v2.8.0 stops the build. Only pack.mcmeta is rewritten.
    node tools/items_v29.js
    python tools/build_v2_9.py
Writes only inside this folder: releases/...-v2.9.0.zip, pack/pack.mcmeta, docs/validation-v2.9.0.json."""
from pathlib import Path
import hashlib, json, struct, zipfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.8.0.zip'
BASE_SHA1 = '2a45c2a6af7c846fc1fad133dd41612dabac0150'  # docs/validation-v2.8.0.json
NEW = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.9.0.zip'
STAMP = (2026, 11, 22, 0, 0, 0)
ITEMS = ['cart_patch_kit', 'saffron_spice', 'imperial_silk', 'damascus_bar', 'clockwork_gear', 'sovereign_relic',
         'mortar', 'cut_stone', 'stone_foundation', 'dressed_slate', 'reinforced_masonry', 'polished_marble', 'carved_obsidian', 'runed_keystone']
META = {'pack': {'description': 'SkyGrind Combined Assets v2.9.0 | Java 1.21.4–1.21.11 | items, workstations, relics, automatons, profession spirits, forage bush, boss and Silk Road models, armour skins, accessories',
                 'pack_format': 46, 'supported_formats': [46, 75], 'min_format': [46, 0], 'max_format': [75, 0]}}

sha256 = lambda b: hashlib.sha256(b).hexdigest()
assert hashlib.sha1(BASE.read_bytes()).hexdigest() == BASE_SHA1, 'releases/ v2.8.0 is not the v2.8.0 build'
added = []
for i in ITEMS:
    added += [f'assets/grindcore/items/{i}.json', f'assets/grindcore/models/item/{i}.json', f'assets/grindcore/textures/item/{i}.png']
data = {a: (ROOT / 'pack' / a).read_bytes() for a in added}
checks = []
with zipfile.ZipFile(BASE) as src:
    names = src.namelist()
    before = {n: sha256(src.read(n)) for n in names if not n.endswith('/')}
    clash = [a for a in added if a in names]
    assert not clash, ('these files exist in v2.8.0 already', clash)
    for a in added:
        if a.endswith('.json'):
            json.loads(data[a].decode('utf-8'))
        else:
            assert data[a][:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', data[a][16:24]) == (32, 32), a
    for i in ITEMS:
        item = json.loads(data[f'assets/grindcore/items/{i}.json'])
        assert item['model'] == {'type': 'minecraft:model', 'model': f'grindcore:item/{i}'}, i
        model = json.loads(data[f'assets/grindcore/models/item/{i}.json'])
        assert model == {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'grindcore:item/{i}'}}, i
    checks.append('every added JSON parses; every texture is a 32x32 PNG; every item names its model and every model its texture')
    meta = (json.dumps(META, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    with zipfile.ZipFile(NEW, 'w', zipfile.ZIP_DEFLATED) as out:
        for name in names:
            if name == 'pack.mcmeta':
                out.writestr(zipfile.ZipInfo(name, STAMP), meta, zipfile.ZIP_DEFLATED)
            else:
                out.writestr(src.getinfo(name), src.read(name), zipfile.ZIP_DEFLATED)  # keeps the old entry's own timestamp
        for a in added:
            out.writestr(zipfile.ZipInfo(a, STAMP), data[a], zipfile.ZIP_DEFLATED)
(ROOT / 'pack/pack.mcmeta').write_bytes(meta)

with zipfile.ZipFile(NEW) as z:
    assert z.testzip() is None
    after = {n: sha256(z.read(n)) for n in before}
    for a in added:
        assert z.read(a) == data[a], a
    total = len(z.namelist())
changed = sorted(n for n in before if before[n] != after[n])
assert changed == ['pack.mcmeta'], changed
assert total == len(names) + len(added), (total, len(names), len(added))
checks.append(f'{len(before) - 1} of {len(before)} v2.8.0 entries are byte for byte identical in v2.9.0; the only changed entry is pack.mcmeta')
zip_bytes = NEW.read_bytes()
report = {'base': BASE.name, 'base_sha1': BASE_SHA1, 'base_entries': len(names), 'pack': NEW.name, 'pack_entries': total,
          'pack_bytes': len(zip_bytes), 'pack_sha1': hashlib.sha1(zip_bytes).hexdigest(),
          'model_ids': [f'grindcore:{i}' for i in ITEMS], 'added': added, 'changed': changed, 'checks': checks}
(ROOT / 'docs/validation-v2.9.0.json').write_text(json.dumps(report, indent=2) + '\n', 'utf-8')
print(total, 'entries;', len(added), 'added;', 'changed:', changed)
print('bytes', len(zip_bytes), 'SHA-1', report['pack_sha1'])
