"""SkyGrind combined resource pack v2.2.0 (2026-11-13): v2.1.0 byte for byte plus the four profession spirit pet models
(textures/item/spirit_<id>.png, models/item/spirit_<id>.json, items/spirit_<id>.json, drawn by tools/spirits.js).
Writes only inside this folder."""
from pathlib import Path
import hashlib, json, zipfile

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.1.0.zip'
NEW = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.2.0.zip'
IDS = ['wheat_sprite', 'ore_golem', 'wood_owl', 'forage_fox']
ADD = []
for i in IDS:
    ADD += [f'assets/grindcore/textures/item/spirit_{i}.png', f'assets/grindcore/models/item/spirit_{i}.json', f'assets/grindcore/items/spirit_{i}.json']
STAMP = (2026, 11, 13, 0, 0, 0)
META = {'pack': {'description': 'SkyGrind Combined Assets v2.2.0 | Java 1.21.4–1.21.11 | items, workstations, relics, automatons, profession spirits',
                 'pack_format': 46, 'supported_formats': [46, 75], 'min_format': [46, 0], 'max_format': [75, 0]}}
meta = (json.dumps(META, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
(ROOT / 'pack/pack.mcmeta').write_bytes(meta)
with zipfile.ZipFile(OLD) as src, zipfile.ZipFile(NEW, 'w', zipfile.ZIP_DEFLATED) as out:
    names = src.namelist()
    for a in ADD:
        assert a not in names, a
    for name in names:
        if name == 'pack.mcmeta':
            out.writestr(zipfile.ZipInfo(name, STAMP), meta, zipfile.ZIP_DEFLATED)
        else:
            out.writestr(src.getinfo(name), src.read(name), zipfile.ZIP_DEFLATED)  # keeps the old entry's own timestamp
    for a in ADD:
        out.writestr(zipfile.ZipInfo(a, STAMP), (ROOT / 'pack' / a).read_bytes(), zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(NEW) as z, zipfile.ZipFile(OLD) as o:
    assert z.testzip() is None
    for n in z.namelist():
        if n in o.namelist() and n != 'pack.mcmeta':
            assert z.read(n) == o.read(n), n
        if n.endswith('.json') or n.endswith('.mcmeta'):
            json.loads(z.read(n))
    assert all(a in z.namelist() for a in ADD)
    print(len(z.namelist()), 'entries;', len(ADD), 'spirit files present')
print('SHA-1', hashlib.sha1(NEW.read_bytes()).hexdigest())
