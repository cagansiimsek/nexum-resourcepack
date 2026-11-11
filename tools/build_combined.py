"""SkyGrind combined resource pack v2.0.0 (2026-11-12).

Merges, byte for byte, the three existing packs (combined v1.0.0, boss relics v0.2.0,
phase-2 workstations v0.1.0), adds the Armourer's Forge cuboid model and the native
32x32 item sprites from sprites.py, validates everything and writes one ZIP.
Writes only inside this folder. Never touches a server, client or items.yml.
"""
from pathlib import Path
import hashlib, io, json, sys, zipfile
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import sprites, armourer, pipeline as P  # noqa: E402

IMAGES = ROOT.parent
VERSION = '2.0.0'
NAME = f'SkyGrind-Combined-Assets-1.21.4-1.21.11-v{VERSION}'
SOURCES = [
    ('combined v1.0.0', IMAGES / 'combined-resource-pack-2026-10-11/SkyGrind-Combined-Assets-1.21.4-1.21.11-v1.0.0.zip'),
    ('boss relics v0.2.0', IMAGES / 'boss-relics-v0.2.0-2026-10-30/SkyGrind-Boss-Relics-1.21.4-1.21.11-v0.2.0.zip'),
    ('workstations phase 2 v0.1.0', IMAGES / 'workstations-phase2-v0.1.0-2026-10-30/SkyGrind-Phase2-Workstations-Java1.21.4-1.21.11-v0.1.0.zip'),
]
GROUPS = {
    'forestry': ['forest_t1_oak_logs', 'forest_t1_birch_logs', 'forest_t2_oak_logs', 'forest_t2_mangrove_logs',
                 'forest_t2_spruce_logs', 'forest_t3_oak_logs', 'forest_t3_spruce_logs', 'forest_t4_oak_logs',
                 'forest_t4_dark_oak_logs', 'forest_t4_pale_oak_logs'],
    'herbs': ['fieldmint', 'wild_fiber', 'heartroot', 'marsh_reed', 'ironbloom', 'embercap', 'crownpetal', 'duskshade'],
    'drops': ['feathered_crest', 'pasture_tusk', 'pasture_hide', 'plague_ichor', 'blighted_bone', 'webbed_heart', 'ash_core',
              'molten_residue', 'cindered_skull', 'void_shard', 'shulker_carapace'],
    'eggs': ['pasture_guardian_egg', 'plaguebringer_egg', 'obsidian_colossus_egg', 'exiled_sovereign_egg'],
    'automatons': ['minion_farming', 'minion_mining', 'minion_forestry', 'minion_slaying'],
    'tools': ['mining_pickaxe', 'forestry_axe', 'foraging_sickle'],
    'parts': ['flour', 'iron_fittings', 'reinforced_components', 'treated_timber', 'wooden_framework', 'copper_fittings',
              'copper_components', 'provision_pack', 'coal_briquette', 'gilded_fittings', 'conductive_assembly', 'gemmed_core',
              'armour_plate_t1', 'armour_plate_t2', 'armour_plate_t3', 'armour_plate_t4', 'reinforced_frame', 'seasoned_timber',
              'hardened_timber', 'ancient_timber', 'weapon_grip', 'advanced_grip', 'hardened_grip', 'sovereign_grip',
              'woven_cloth', 'reinforced_cloth', 'armour_lining', 'field_bandage', 'heartroot_wrap', 'warding_wrap',
              'carrot_broth', 'hearty_stew', 'ironbloom_meal', 'embercap_meal', 'crownmeal'],
    'gear': [f'armour_t{t}_{p}' for t in (1, 2, 3, 4) for p in ('helmet', 'chestplate', 'leggings', 'boots')]
            + ['copper_sword', 'iron_sword', 'gilded_sword', 'sovereign_sword'],
}
META = {'pack': {'description': 'SkyGrind Combined Assets v2.0.0 | Java 1.21.4–1.21.11 | items, workstations, relics',
                 'pack_format': 46, 'supported_formats': [46, 75], 'min_format': [46, 0], 'max_format': [75, 0]}}
STAMP = (2026, 11, 12, 0, 0, 0)


def jbytes(v):
    return (json.dumps(v, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def png_bytes(im):
    buf = io.BytesIO(); im.save(buf, format='PNG', optimize=True); return buf.getvalue()


def main():
    files, origin = {}, {}

    def add(path, data, src):
        if path in files and files[path] != data:
            raise SystemExit(f'COLLISION with different bytes: {path} ({origin[path]} vs {src})')
        files[path] = data; origin.setdefault(path, src)

    # 1. Existing packs, byte for byte (their README/pack.mcmeta are replaced by ours).
    carried = {}
    for label, zpath in SOURCES:
        with zipfile.ZipFile(zpath) as z:
            assert z.testzip() is None, zpath
            for n in z.namelist():
                if n.endswith('/') or n in ('README.md', 'pack.mcmeta'):
                    continue
                add(n, z.read(n), label); carried[n] = label

    # 2. Armourer's Forge cuboid model.
    model, checks = armourer.main()
    apack = armourer.ROOT / 'pack'
    for p in sorted(apack.rglob('*')):
        if p.is_file():
            add(p.relative_to(apack).as_posix(), p.read_bytes(), 'armourers_forge (new)')

    # 3. Native 32x32 sprites.
    built = sprites.build_all()
    listed = [k for ids in GROUPS.values() for k in ids]
    assert sorted(listed) == sorted(built), (set(listed) ^ set(built))
    sprite_stats, review = {}, ROOT / 'sprites'
    review.mkdir(exist_ok=True)
    for group, ids in GROUPS.items():
        for k in ids:
            im = built[k].image()
            data = png_bytes(im)
            (review / f'{k}.png').write_bytes(data)
            tex = f'grindcore:item/{group}/{k}'
            parent = 'minecraft:item/handheld' if k in sprites.HANDHELD else 'minecraft:item/generated'
            add(f'assets/grindcore/textures/item/{group}/{k}.png', data, 'sprite (new)')
            add(f'assets/grindcore/models/item/{k}.json', jbytes({'parent': parent, 'textures': {'layer0': tex}}), 'sprite (new)')
            add(f'assets/grindcore/items/{k}.json', jbytes({'model': {'type': 'minecraft:model', 'model': f'grindcore:item/{k}'}}), 'sprite (new)')
            sprite_stats[k] = {'group': group, 'parent': parent,
                               'opaque_colours': len({px[:3] for px in im.get_flattened_data() if px[3]}),
                               'alpha': sorted(set(im.getchannel('A').get_flattened_data())), 'bounds': list(im.getbbox()),
                               'sha256': hashlib.sha256(data).hexdigest()}

    add('pack.mcmeta', jbytes(META), 'v2.0.0')
    add('README.md', (ROOT / 'PACK-README.md').read_bytes(), 'v2.0.0')

    # 4. Static validation.
    errors = []
    item_defs = sorted(n for n in files if n.startswith('assets/grindcore/items/') and n.endswith('.json'))
    for n in files:
        if n.endswith('.json') or n.endswith('.mcmeta'):
            P.strict(files[n].decode('utf-8'))
        assert not n.startswith('/') and '..' not in n and '\\' not in n, n
        assert not n.startswith('assets/minecraft/'), f'vanilla override: {n}'
    chains = {}
    for n in item_defs:
        key = n.rsplit('/', 1)[1][:-5]
        d = json.loads(files[n])
        m = d['model']; assert m['type'] == 'minecraft:model', n
        mpath = 'assets/grindcore/models/' + m['model'].split(':', 1)[1] + '.json'
        if mpath not in files:
            errors.append(f'{key}: missing model {mpath}'); continue
        model_j = json.loads(files[mpath])
        texs = []
        for ref in model_j.get('textures', {}).values():
            ns, path = ref.split(':', 1)
            tpath = f'assets/{ns}/textures/{path}.png'
            if ns == 'grindcore':
                if tpath not in files:
                    errors.append(f'{key}: missing texture {tpath}')
                elif not path.startswith('item/'):
                    errors.append(f'{key}: texture outside item atlas dir {path}')
                else:
                    Image.open(io.BytesIO(files[tpath])).verify()
                texs.append(tpath)
        chains[key] = {'model': mpath, 'textures': sorted(set(texs)), 'source': origin[n]}
    for k, st in sprite_stats.items():
        im = Image.open(io.BytesIO(files[f"assets/grindcore/textures/item/{st['group']}/{k}.png"]))
        if im.size != (32, 32) or im.mode != 'RGBA': errors.append(f'{k}: size/mode {im.size} {im.mode}')
        if st['alpha'] != [0, 255]: errors.append(f'{k}: alpha {st["alpha"]}')
        if st['opaque_colours'] > 16: errors.append(f'{k}: {st["opaque_colours"]} colours')
        l, t, r, b = st['bounds']
        if l < 1 or t < 1 or r > 31 or b > 31: errors.append(f'{k}: touches edge {st["bounds"]}')
    for n, label in carried.items():
        if files[n] != zipfile.ZipFile(dict(SOURCES)[label]).read(n): errors.append(f'not byte-equal: {n}')
    if errors:
        raise SystemExit('VALIDATION FAILED:\n' + '\n'.join(errors))

    # 5. ZIP (deterministic order and timestamps), then re-read and compare.
    archive = ROOT / f'{NAME}.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(files):
            info = zipfile.ZipInfo(n, date_time=STAMP); info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, files[n])
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert sorted(z.namelist()) == sorted(files) and 'pack.mcmeta' in z.namelist()
        assert all(z.read(n) == files[n] for n in files)

    # 6. Preview sheet of every model key in the pack.
    preview(built, model)

    raw = archive.read_bytes()
    result = {'status': 'PASS', 'validation': 'static only; Minecraft client not launched', 'version': VERSION,
              'zip': archive.name, 'zip_files': len(files), 'zip_bytes': len(raw),
              'zip_sha1': hashlib.sha1(raw).hexdigest(), 'zip_sha256': hashlib.sha256(raw).hexdigest(),
              'metadata': META['pack'], 'model_keys': len(chains),
              'keys_by_source': {s: sorted(k for k, c in chains.items() if c['source'] == s) for s in sorted({c['source'] for c in chains.values()})},
              'armourer_geometry': {'elements': len(model['elements']), **checks},
              'sprites': sprite_stats, 'chains': chains}
    (ROOT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status', 'zip', 'zip_files', 'zip_bytes', 'zip_sha1', 'model_keys')}, indent=1))
    print({s: len(v) for s, v in result['keys_by_source'].items()})


def preview(built, model):
    cols, cell = 10, 112
    ids = [k for ids in GROUPS.values() for k in ids]
    rows = (len(ids) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell, rows * (cell + 16) + 300), (32, 35, 41))
    d = ImageDraw.Draw(sheet)
    for i, k in enumerate(ids):
        im = built[k].image()
        x, y = (i % cols) * cell, (i // cols) * (cell + 16)
        big = im.resize((96, 96), Image.Resampling.NEAREST)
        sheet.paste(big, (x + 8, y + 8), big)
        d.text((x + 6, y + 106), k[:18], fill=(226, 220, 206))
    iso = Image.open(armourer.ROOT / 'previews/armourers_forge-isometric.png').resize((280, 280))
    y0 = rows * (cell + 16) + 10
    sheet.paste(iso, (10, y0), iso)
    d.text((300, y0 + 20), "armourers_forge (3D model, 31 cuboids)", fill=(226, 220, 206))
    d.text((300, y0 + 40), "All sprites: native 32 x 32, transparent, <=16 colours", fill=(164, 169, 175))
    sheet.save(ROOT / 'preview-new-items.png')


if __name__ == '__main__':
    main()
