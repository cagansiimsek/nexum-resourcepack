"""SkyGrind combined resource pack v2.10.0 (2026-11-22): v2.7.0 with its BetterModel part replaced by the freshly generated one.

BetterModel builds its own pack (`plugins/BetterModel/build.zip` on the server) from the .bbmodel files. v2.10.0 adds the new
models of the v3.59 round (Bramble-Spur, Feral Chick, the five Silk Road route bosses, Tian-Long's halberd and dragon form, five
caravans) next to the six older boss models. Everything outside `assets/bettermodel/` is v2.7.0 byte for byte; only pack.mcmeta
is rewritten.
    python tools/build_v2_8.py <path to BetterModel build.zip>
Writes only inside this folder: releases/...-v2.10.0.zip, pack/pack.mcmeta, docs/validation-v2.10.0.json."""
from pathlib import Path
import hashlib, json, sys, zipfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.9.0.zip'
NEW = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.10.0.zip'
BM = Path(sys.argv[1])
STAMP = (2026, 11, 22, 0, 0, 0)
PREFIX = 'assets/bettermodel/'
META = {'pack': {'description': 'SkyGrind Combined Assets v2.10.0 | Java 1.21.4–1.21.11 | items, workstations, relics, automatons, profession spirits, forage bush, boss and Silk Road models, armour skins, accessories',
                 'pack_format': 46, 'supported_formats': [46, 75], 'min_format': [46, 0], 'max_format': [75, 0]}}
sha = lambda b: hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(BASE) as src, zipfile.ZipFile(BM) as bm:
    base_names = src.namelist()
    kept = [n for n in base_names if not n.startswith(PREFIX)]
    old_bm = [n for n in base_names if n.startswith(PREFIX) and not n.endswith('/')]
    new_bm = [n for n in bm.namelist() if n.startswith(PREFIX) and not n.endswith('/')]
    for n in new_bm:
        if n.endswith('.json'):
            json.loads(bm.read(n).decode('utf-8'))
    before = {}
    meta = (json.dumps(META, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    with zipfile.ZipFile(NEW, 'w', zipfile.ZIP_DEFLATED) as out:
        for n in kept:
            if n == 'pack.mcmeta':
                out.writestr(zipfile.ZipInfo(n, STAMP), meta, zipfile.ZIP_DEFLATED)
            elif not n.endswith('/'):
                b = src.read(n); before[n] = sha(b)
                out.writestr(src.getinfo(n), b, zipfile.ZIP_DEFLATED)
        for n in sorted(new_bm):
            out.writestr(zipfile.ZipInfo(n, STAMP), bm.read(n), zipfile.ZIP_DEFLATED)
(ROOT / 'pack/pack.mcmeta').write_bytes(meta)
with zipfile.ZipFile(NEW) as z:
    assert z.testzip() is None
    changed = sorted(n for n in before if sha(z.read(n)) != before[n])
    total = len(z.namelist())
assert changed == [], changed
data = NEW.read_bytes()
report = {'base': BASE.name, 'pack': NEW.name, 'entries': total, 'bettermodel_old': len(old_bm), 'bettermodel_new': len(new_bm),
          'changed_outside_bettermodel': changed, 'bytes': len(data), 'sha1': hashlib.sha1(data).hexdigest()}
(ROOT / 'docs/validation-v2.10.0.json').write_text(json.dumps(report, indent=2) + '\n', 'utf-8')
print(json.dumps(report))
