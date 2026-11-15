"""SkyGrind combined resource pack v2.4.0 (2026-11-15): v2.3.0 byte for byte plus the boss models.
The bosses (Plaguebringer, Obsidian Colossus, Exiled Sovereign and the three thrones) are drawn by the BetterModel plugin, which
writes its own pack (plugins/BetterModel/build.zip, namespace `bettermodel`). The server sends only ONE pack, so without these
files the bosses show as purple and black boxes. This script copies every `assets/bettermodel/` entry of that build.zip into the
combined pack. BetterModel uses shortened (obfuscated) file names: when a boss model is added or changed, take the new build.zip
from the server and build a new pack version.
    python tools/build_v2_4.py <path to BetterModel build.zip>
Writes only inside this folder."""
from pathlib import Path
import hashlib, json, sys, zipfile

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.3.0.zip'
NEW = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.4.0.zip'
BM = Path(sys.argv[1])
PREFIX = 'assets/bettermodel/'
STAMP = (2026, 11, 15, 0, 0, 0)
META = {'pack': {'description': 'SkyGrind Combined Assets v2.4.0 | Java 1.21.4–1.21.11 | items, workstations, relics, automatons, profession spirits, forage bush, boss models',
                 'pack_format': 46, 'supported_formats': [46, 75], 'min_format': [46, 0], 'max_format': [75, 0]}}
meta = (json.dumps(META, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
(ROOT / 'pack/pack.mcmeta').write_bytes(meta)
with zipfile.ZipFile(OLD) as src, zipfile.ZipFile(BM) as bm, zipfile.ZipFile(NEW, 'w', zipfile.ZIP_DEFLATED) as out:
    names = src.namelist()
    add = sorted(n for n in bm.namelist() if n.startswith(PREFIX) and not n.endswith('/'))
    other = [n for n in bm.namelist() if not n.startswith(PREFIX) and not n.endswith('/') and n not in ('pack.mcmeta', 'pack.png')]
    assert not other, other[:5]            # the boss pack must hold nothing outside its own namespace
    assert add and not any(n.startswith(PREFIX) for n in names)
    for name in names:
        if name == 'pack.mcmeta':
            out.writestr(zipfile.ZipInfo(name, STAMP), meta, zipfile.ZIP_DEFLATED)
        else:
            out.writestr(src.getinfo(name), src.read(name), zipfile.ZIP_DEFLATED)  # keeps the old entry's own timestamp
    for a in add:
        data = bm.read(a)
        out.writestr(zipfile.ZipInfo(a, STAMP), data, zipfile.ZIP_DEFLATED)
        target = ROOT / 'pack' / a
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
with zipfile.ZipFile(NEW) as z, zipfile.ZipFile(OLD) as o, zipfile.ZipFile(BM) as bm:
    assert z.testzip() is None
    old = set(o.namelist())
    for n in z.namelist():
        if n in old and n != 'pack.mcmeta':
            assert z.read(n) == o.read(n), n
        elif n.startswith(PREFIX):
            assert z.read(n) == bm.read(n), n
    print(len(z.namelist()), 'entries;', len(add), 'boss model files added')
print('SHA-1', hashlib.sha1(NEW.read_bytes()).hexdigest())
