Task: Phase 2 stage 2a, THE WORLD, for Adventure World (monte-flora/adventure-world).

Build PHASE2.md design points 1 and 2:
- Redraw levels/world/ into the real big world: 6-7 lands with their own feel (Home Meadow, Whispering Woods, the Great Lake with Portal Island, Frost Peaks, Sunscorch Desert, Murk Swamp; fold in or keep Old Ruins / Ember Canyon / Misty Marsh / Frosty Corner as you judge). About 3-4x the classic map area (today the stitched map is 70x45; aim for roughly 100x70 to 120x80). Paths, rivers, bridges, mountain passes and gates so the lands open up in an order, using things that exist (boat, gates, levels). Every Mine still leads to a cave (caves.plan_caves spreads cave files over Mines); keep all 12 cave Mines reachable.
- A VILLAGE in at least 4 lands: a few houses (H) around an open square. Add a `village: <Name> <row> <col>` header line per village (local coords of its square) to the land file format, parse it into the atlas (e.g. atlas.villages), and document it in levels/README.md. Stage 2b puts people there.
- With no fog, landmarks become WAYSTONES: walking onto one unlocks it; at any unlocked waystone, SPACE opens a fast-travel list (keys + mouse). Lookouts: climbing one (SPACE) marks the nearest secret chest on the minimap.
- New terrain looks per land if needed (sand, snow, swamp water...), drawn in your own phase2 drawing module in the sprites.py style.
- Tests: map size, every land reachable from the start (pathfinding over walkable tiles, with a boat where needed), every Mine reachable, villages parsed and on walkable squares, waystone unlock + travel, lookout marks a chest, save/load keeps unlocked waystones.

Owns: levels/world/*, phase2/world_map.py, new phase2/waystones.py and phase2/draw_world.py (or similar), the Phase 2 section of levels/README.md. Do NOT write people, dialogue, shops, quests (2b) or monster/fight changes (2c).
Note: 2b places people by (land, local row, col). If your redraw moves things, 2b's placement test will tell whoever merges second to fix positions.
