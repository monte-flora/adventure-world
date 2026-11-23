# Handoff: paint every land (task_eefd0707008b), paused for the usage cap at 2026-11-23 ~7:2x pm ET

User's words: "Can we finish the rest of Emberhold too like the weepingwillow land or whatever and any other places on the main overworld map?" They loved the painted Emberhold.

## Done
- PR #78 (branch monte-flora/paint-ground-names): gemini-next `is_ground()`. `<land>_ground_<x>` counts as ground, and its texture keeps its full name (realm/ground/wintermarch_ground_snow.png). The same rule is in art_import.gd `ground_stem()` and make_placeholders.py. Test added. Watch it merge (gh pr checks 78).

## In flight: this branch (monte-flora/paint-emberhold-edges), WIP commit, no PR yet
- realm_ground.gd: roles (grass dirt_road cobblestone mud shallow_water deep_water rocky_ground cliff forest_floor ice) with FALLBACK.
  A land's `paint: <role> <texture>` line overrides a role. The atlas is a grid (COLS 8), and water textures come last (`water_first`): the shader ripples them with TIME.
  W is deep_water, or shallow_water next to land. X is cliff (a gate: X is rocky_ground), YOK are rocky_ground, F is forest_floor.
- realm_props.gd `scatter()` (drawing only, no footprints): a gate prop on every Y/O/K/gate: square (ivy_cliff, rubble_heap, shadow_thorns, riven_boulder), shown while shut (`refresh_gates` runs on Game.changed).
  It also puts a tree or crag on every other F/X square (checkerboard + nudge) from the land's `forest:` / `crags:` lines (defaults oak pine dead_tree / crag).
- realm_tiles.gd: X/Y/O/K in painted lands draw no tile. overworld.gd: `decor` dict, shaded with painted_material.
- world_map.gd: lands[id] gets "paint", "forest", "crags".
- New prompts, assets.json entries, placeholders and imported placeholder art: crag ivy_cliff rubble_heap shadow_thorns riven_boulder, ground_cliff ground_deep_water ground_forest_floor.
- Tests: test_gate_art (painted gates are props). test_props: 2 new tests.
  ONE FAILS: "water away from the shore is deep": the test pond (3,4) touches the bottom X row. Fix the test grid (a bigger pond, or check a square 2 away from land).
- The before shots are in the scratchpad (lost on restart: retake from origin/phase-2 if needed). After: B3 shows crags on the X wall and rubble on the O squares; it looks right.

## Next
1. Fix that test. Then run: pixi pytest (`/Users/montgomeryflora/noah-adventure/.pixi/envs/default/bin/python -m pytest -q -n auto tests`) and `sh shadowfall/tools/run_tests.sh`.
2. Take before/after shots (A3 15,42; B2 45,25; B3 52,40) into docs/teen/art/lands/ (small, sips -Z 960). Open the PR into phase-2.
3. The W strip seen from Emberhold belongs to the Mere: it gets painted with the Mere PR. In the Mere PR, also paint the sea (squares no land owns) as the Mere's deep water.
4. Lands in map order, 2 per PR: `ground: painted`, `paint:` lines with <land>_ground_* textures, `forest:`/`crags:` lines, land props + prop: lines (props with feet ONLY on squares already blocked, or walk-through props; collision must not change).
   make_placeholders.py needs a GROUND colour for each new ground name, and a shape (or "like") for each new prop.
5. Umbral Reach (nightfall): RealmGround is built only for realm "light", and scatter/painted() skip world.nightfall. It needs enabling.
6. test_realm_art_per_land needs a forest square outside painted lands. Once all the light lands are painted, change that check.
7. Final report: every new prompt, counted per land.
