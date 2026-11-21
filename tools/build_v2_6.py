"""SkyGrind combined resource pack v2.6.0 (2026-11-21): v2.5.0 byte for byte plus the eight v3.58 spirit models.

v2.5.0 is the pack the server sends today (its SHA-1 is the one in server.properties). The new spirits (harvest_hare, gem_beetle,
bark_squirrel, petal_moth, battle_hound, bounty_raven, ember_drake, golden_dragon) are drawn by tools/spirits.js into pack/.
For each one this adds three files: the item definition, the model and the 64x64 texture. A file that already exists in v2.5.0
stops the build. Only pack.mcmeta is rewritten (the new version in its description).
    node tools/spirits.js
    python tools/build_v2_6.py
Writes only inside this folder: releases/...-v2.6.0.zip, pack/pack.mcmeta, docs/validation-v2.6.0.json."""
from pathlib import Path
import hashlib, json, struct, zipfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.5.0.zip'
BASE_SHA1 = '4e44ed9f73cebdf6b75a4028198477665d331018'
NEW = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.6.0.zip'
STAMP = (2026, 11, 21, 0, 0, 0)
SPIRITS = ['harvest_hare', 'gem_beetle', 'bark_squirrel', 'petal_moth', 'battle_hound', 'bounty_raven', 'ember_drake', 'golden_dragon']
META = {'pack': {'description': 'SkyGrind Combined Assets v2.6.0 | Java 1.21.4–1.21.11 | items, workstations, relics, automatons, profession spirits, forage bush, boss models, armour skins, accessories',
                 'pack_format': 46, 'supported_formats': [46, 75], 'min_format': [46, 0], 'max_format': [75, 0]}}

sha256 = lambda b: hashlib.sha256(b).hexdigest()
base_bytes = BASE.read_bytes()
assert hashlib.sha1(base_bytes).hexdigest() == BASE_SHA1, 'releases/ v2.5.0 is not the pack the server uses'
added = []
for s in SPIRITS:
    added += [f'assets/grindcore/items/spirit_{s}.json', f'assets/grindcore/models/item/spirit_{s}.json', f'assets/grindcore/textures/item/spirit_{s}.png']
data = {a: (ROOT / 'pack' / a).read_bytes() for a in added}
checks = []
with zipfile.ZipFile(BASE) as src:
    names = src.namelist()
    before = {n: sha256(src.read(n)) for n in names if not n.endswith('/')}
    clash = [a for a in added if a in before]
    assert not clash, ('these files exist in v2.5.0 already', clash)
    for a in added:
        if a.endswith('.json'):
            json.loads(data[a].decode('utf-8'))
        else:
            assert data[a][:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', data[a][16:24]) == (64, 64), a
    for s in SPIRITS:
        item = json.loads(data[f'assets/grindcore/items/spirit_{s}.json'])
        assert item['model']['model'] == f'grindcore:item/spirit_{s}', s
        model = json.loads(data[f'assets/grindcore/models/item/spirit_{s}.json'])
        assert set(model['textures'].values()) == {f'grindcore:item/spirit_{s}'}, s
    checks.append('every added JSON parses; every texture is a 64x64 PNG; every item names its model and every model its texture')
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
checks.append(f'{len(before) - 1} of {len(before)} v2.5.0 entries are byte for byte identical in v2.6.0; the only changed entry is pack.mcmeta')
zip_bytes = NEW.read_bytes()
report = {'base': BASE.name, 'base_sha1': BASE_SHA1, 'base_entries': len(names), 'pack': NEW.name, 'pack_entries': total,
          'pack_bytes': len(zip_bytes), 'pack_sha1': hashlib.sha1(zip_bytes).hexdigest(), 'added': added, 'changed': changed, 'checks': checks}
(ROOT / 'docs/validation-v2.6.0.json').write_text(json.dumps(report, indent=2) + '\n', 'utf-8')
print(total, 'entries;', len(added), 'added;', 'changed:', changed)
print('bytes', len(zip_bytes), 'SHA-1', report['pack_sha1'])
