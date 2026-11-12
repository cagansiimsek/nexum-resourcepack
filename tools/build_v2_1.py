"""SkyGrind combined resource pack v2.1.0 (2026-11-12): v2.0.0 byte for byte plus the Automaton skin
(textures/entity/automaton.png, drawn by tools/automaton_skin.js). Writes only inside this folder."""
from pathlib import Path
import hashlib, json, zipfile

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.0.0.zip'
NEW = ROOT / 'releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.1.0.zip'
SKIN = 'assets/grindcore/textures/entity/automaton.png'
STAMP = (2026, 11, 12, 0, 0, 0)
META = {'pack': {'description': 'SkyGrind Combined Assets v2.1.0 | Java 1.21.4–1.21.11 | items, workstations, relics, automatons',
                 'pack_format': 46, 'supported_formats': [46, 75], 'min_format': [46, 0], 'max_format': [75, 0]}}
meta = (json.dumps(META, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
(ROOT / 'pack/pack.mcmeta').write_bytes(meta)
with zipfile.ZipFile(OLD) as src, zipfile.ZipFile(NEW, 'w', zipfile.ZIP_DEFLATED) as out:
    names = src.namelist()
    assert SKIN not in names
    for name in names:
        data = meta if name == 'pack.mcmeta' else src.read(name)
        out.writestr(zipfile.ZipInfo(name, STAMP), data, zipfile.ZIP_DEFLATED)
    out.writestr(zipfile.ZipInfo(SKIN, STAMP), (ROOT / 'pack' / SKIN).read_bytes(), zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(NEW) as z:
    assert z.testzip() is None
    print(len(z.namelist()), 'entries; skin present:', SKIN in z.namelist())
print('SHA-1', hashlib.sha1(NEW.read_bytes()).hexdigest())
