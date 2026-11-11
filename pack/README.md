# SkyGrind combined Java resource pack v2.0.0 (2026-11-12)

One pack with every SkyGrind custom look made so far. Java 1.21.11 (format range 46-75, so 1.21.4 to 1.21.11).
Select this ZIP in Options > Resource Packs without extracting it. Use it instead of the older SkyGrind packs
(it already contains them); do not stack it with the boss-relic or workstation candidate packs.

Contents
- Carried over unchanged (byte for byte): artisan_bread, reinforced_cobblestone, caravan_silk, bakers_table,
  masons_bench, weavers_loom (combined v1.0.0); verdant_heart, blighted_vessel, molten_core, crown_of_exile
  (boss relics v0.2.0); summoners_altar, smiths_forge, carpenters_bench (workstations phase 2 v0.1.0).
- New: armourers_forge (3D workstation model) and 95 flat 32x32 item sprites, one per item id of the
  2026-11-12 texture needs list. The model key of each new sprite equals its GrindCore item id:
  `grindcore:<item id>`, e.g. `grindcore:forest_t1_oak_logs`, `grindcore:minion_mining`.

Quick look in a creative test world:
/give @s minecraft:paper[minecraft:item_model="grindcore:forest_t1_oak_logs"] 1
/give @s minecraft:paper[minecraft:item_model="grindcore:minion_mining"] 1
/give @s minecraft:paper[minecraft:item_model="grindcore:armourers_forge"] 1

Visuals only: no items, recipes, behaviour or vanilla textures are changed. Armour sprites change the inventory
and hand icon only; worn armour keeps its vanilla look. Bedrock/Geyser is not covered.
