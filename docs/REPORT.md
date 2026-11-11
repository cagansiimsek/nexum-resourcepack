# SkyGrind combined resource pack v2.0.0 (2026-11-12)

**Status: COMPLETE (static checks pass; not yet seen in a Minecraft client).**

**ZIP:** `Images/combined-resource-pack-2026-11-12/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.0.0.zip`
330 files, 283,853 bytes. SHA-1 `f69d80bbc332d23badcb7a276d8082b976483ade` (the value `server.properties`
`resource-pack-sha1` would need if the server ever hands the pack out). Full hashes: `validation.json`.

## What is inside (109 looks)
- **Carried over byte for byte (13):** combined v1.0.0 (artisan_bread, reinforced_cobblestone, caravan_silk,
  bakers_table, masons_bench, weavers_loom, plus pack.png); boss relics v0.2.0 (verdant_heart, blighted_vessel,
  molten_core, crown_of_exile); workstations phase 2 v0.1.0 (summoners_altar, smiths_forge, carpenters_bench).
  The builder checks every carried file is identical to its source ZIP.
- **New 3D workstation (1):** armourers_forge, 31 cuboids on a gilded-blackstone plinth (bench with helmet, armour
  stand with chestplate, shield rack, quench trough), same pipeline, palette and display transforms as the Smith
  and Carpenter. Geometry checks pass (all parts connected, no flickering faces).
- **New flat sprites (95):** one per item id in groups C to J of the needs list. Native 32x32, transparent,
  hard edges, at most 16 colours, 1-pixel margin, upper-left light, dark contour. Tools and swords use the
  hand-held pose; the rest use the normal item pose. Model key = item id (`grindcore:<id>`).

## How they were made
No image generator was available in this session, so every sprite is drawn by code (`sprites.py`,
`pixel.py`), the same procedural route used for the relics and phase-2 benches. Rebuild with
`& 'C:\Users\Çaan\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\build_combined.py`
(expected: PASS, 330 files, same SHA-1). Review copies of every sprite: `sprites/`; overview: `preview-new-items.png`.

## Not done on purpose
- **No `model:` lines in `items.yml`** (TEST or repo). The file says to add them only after the pack is installed;
  without the pack, players would see a missing-texture cube.
- **Workstations (smiths_forge, carpenters_bench, armourers_forge):** placed benches keep their stored block look;
  switching them needs the anchor-transition steps in `workstations-phase2-v0.1.0-2026-10-30/INTEGRATION-NOTES-FOR-CLAUDE.md`.
- No server, client, `server.properties` or pack hosting was touched. Not committed: this folder is new and
  untracked in the Skyblock repo (checked with `git status`), waiting for your OK.

## Owner decisions
1. **Summoner eggs:** two looks are now in the pack. The relics (verdant_heart etc.) were made in October as the
   proposed look for the four eggs; the needs list asked for spawn-egg style sprites, which are new
   (`grindcore:pasture_guardian_egg` etc.). Pick one per egg when wiring.
2. **Phase-2 workstations** (summoners_altar, smiths_forge, carpenters_bench) were still waiting for your visual
   approval; they are included so the pack is complete.
3. **Group J (armour and swords)** was optional; the sprites exist but change only the inventory/hand icon.
   Worn armour stays vanilla. Wire them only if you like them.
4. **Weakest reads** (redraw on request): feathered_crest (looks a bit like a leafy vegetable), shulker_carapace
   (a bit like a knit hat), duskshade (reads as grapes).

## Coverage of the needs list (row by row)
| Group | Item id | Result |
|---|---|---|
| A | smiths_forge | merged (phase 2 model, unchanged) |
| A | carpenters_bench | merged (phase 2 model, unchanged) |
| B | armourers_forge | built (3D model) |
| C | forest_t1_oak_logs, forest_t1_birch_logs | built (1 gold tier stud) |
| C | forest_t2_oak_logs, forest_t2_mangrove_logs, forest_t2_spruce_logs | built (2 studs) |
| C | forest_t3_oak_logs (moss), forest_t3_spruce_logs (frost) | built (3 studs) |
| C | forest_t4_oak_logs, forest_t4_dark_oak_logs (moss), forest_t4_pale_oak_logs (aether glow) | built (4 studs) |
| D | fieldmint, wild_fiber, heartroot, marsh_reed, ironbloom, embercap, crownpetal, duskshade | built |
| E | feathered_crest, pasture_tusk, pasture_hide (T1 green) | built |
| E | plague_ichor, blighted_bone, webbed_heart (T2 sickly green) | built |
| E | ash_core, molten_residue, cindered_skull (T3 ash and ember) | built |
| E | void_shard, shulker_carapace (T4 void purple) | built |
| F | pasture_guardian_egg, plaguebringer_egg, obsidian_colossus_egg, exiled_sovereign_egg | built (relic alternative also merged) |
| G | minion_farming (hoe), minion_mining (pick), minion_forestry (axe), minion_slaying (sword) | built |
| H | mining_pickaxe, forestry_axe, foraging_sickle | built (hand-held pose) |
| I | flour, iron_fittings, reinforced_components, treated_timber, wooden_framework, copper_fittings, copper_components, provision_pack, coal_briquette, gilded_fittings, conductive_assembly, gemmed_core | built |
| I | armour_plate_t1, _t2, _t3, _t4 | built (copper, iron, gold, sovereign) |
| I | reinforced_frame, seasoned_timber, hardened_timber, ancient_timber | built |
| I | weapon_grip, advanced_grip, hardened_grip, sovereign_grip | built |
| I | woven_cloth, reinforced_cloth, armour_lining, field_bandage, heartroot_wrap, warding_wrap | built |
| I | carrot_broth, hearty_stew, ironbloom_meal, embercap_meal, crownmeal | built |
| J | armour_t1..t4 helmet, chestplate, leggings, boots (16) | built (icon only) |
| J | copper_sword, iron_sword, gilded_sword, sovereign_sword | built (hand-held pose) |
| also | summoners_altar, verdant_heart, blighted_vessel, molten_core, crown_of_exile | merged unchanged |
| skipped | forestry trees, Capital buildings, currency icons, menu stone button | not item textures (list says so) |

All 96 listed ids exist in both the TEST catalog and the repo copy of `items.yml` (checked 2026-11-12).

## Validation (static only)
Strict JSON for every file; every item definition resolves to a model and every model texture exists in the
item atlas folder; no vanilla files overridden; PNG size/mode/alpha/colour/margin checks on all 95 sprites;
`pack.mcmeta` at the ZIP root with formats 46-75; exact file list and byte-equal re-read of the ZIP; two builds
give the same SHA-1; all 409 earlier files in `Images/` unchanged (hash list `preservation-before.sha256`).
**Not checked:** loading in a real Minecraft client, ViaVersion clients, Bedrock.

## Owner test (5 minutes; tracked as RP-01..04 in the vault Test Pile)
1. Minecraft Java 1.21.11 > Options > Resource Packs > Open Pack Folder; copy the ZIP in (do not unzip); select
   "SkyGrind Combined Assets v2.0.0" and remove older SkyGrind packs from the selected list.
2. In a creative single-player world with cheats:
   `/give @s minecraft:paper[minecraft:item_model="grindcore:minion_mining"] 1`
   `/give @s minecraft:paper[minecraft:item_model="grindcore:forest_t4_pale_oak_logs"] 1`
   `/give @s minecraft:paper[minecraft:item_model="grindcore:armourers_forge"] 1`
3. Expected: a bronze robot with a pickaxe, a pale log stack with four gold studs, a small armourer bench.
   A black-and-purple cube means the pack did not load.
