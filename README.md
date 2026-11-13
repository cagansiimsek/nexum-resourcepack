# SkyGrind Resource Pack

The Java Edition resource pack for the SkyGrind (Nexum) server: custom item and block looks for GrindCore items.

- **Version:** 2.2.0 (2026-11-13), Minecraft Java 1.21.4 to 1.21.11 (pack format 46 to 75)
- **Contents:** 109 looks. 13 carried over unchanged (artisan bread, reinforced cobblestone, caravan silk, the Baker, Mason and Weaver benches, the boss relics, the Smith and Carpenter benches, the Summoner's Altar) and 96 new (the Armourer's Forge 3D model and 95 flat 32x32 item sprites). Added since: the Automaton skin (v2.1.0, an entity texture) and four 3D profession spirit pet models (v2.2.0: `spirit_wheat_sprite`, `spirit_ore_golem`, `spirit_wood_owl`, `spirit_forage_fox`, each a cube model of about 10 units with its own 64x64 texture).
- **Model keys:** every look is named after its GrindCore item id, for example `grindcore:forest_t1_oak_logs`. The server sets it with `model: grindcore:<id>` in `items.yml`.
- **Not covered:** Bedrock (Geyser) players; they need a separate pack.

## Try it

Put `releases/SkyGrind-Combined-Assets-1.21.4-1.21.11-v2.2.0.zip` in your resource pack folder (do not unzip it) and run in a creative world:

```
/give @s minecraft:paper[minecraft:item_model="grindcore:forest_t1_oak_logs"] 1
/give @s minecraft:paper[minecraft:item_model="grindcore:spirit_forage_fox"] 1
```

## How the server uses it

1. Attach the release ZIP to a GitHub Release (tag `v2.2.0`) and copy its direct download link.
2. In `server.properties`: `resource-pack=<that link>`, `resource-pack-sha1=<the SHA-1 of the ZIP>`, optionally `resource-pack-prompt` and `require-resource-pack=true`. Restart the server.
3. A new version gets a new tag, a new link and a new SHA-1. The file name carries the version, so players never keep a stale copy.

SHA-1 of the 2.2.0 ZIP: `fbb372f904127c62e467ec122bc07449b27feae1` (the 2.0.0 ZIP was `f69d80bbc332d23badcb7a276d8082b976483ade`)

## Layout

| Folder | What |
|---|---|
| `pack/` | the unpacked pack (what is inside the ZIP) |
| `releases/` | the built ZIP of each version |
| `tools/` | the scripts that drew and built the sprites, the Armourer's Forge, the Automaton skin and the spirits (`spirits.js` draws them and renders the previews, `build_v2_2.py` builds the ZIP) (they need the older pack sources they carry over from, so they are a record, not a one-command rebuild) |
| `previews/sprites/` | one preview PNG per sprite |
| `previews/spirits/` | isometric previews of the four spirits (`previews/spirits.png` is the sheet) |
| `docs/` | the build report and validation record |

## Notes

- Visuals only: the pack changes no items, recipes or behaviour.
- The armour sprites change the inventory and hand icon only; worn armour keeps its vanilla look.
- The sprites were drawn by code, so they are simple. Weakest reads: feathered crest, shulker carapace, duskshade (redraw on request).
- Placed Carpenter's Bench and Armourer's Forge stay normal blocks on the island; only their item icon uses the pack.
