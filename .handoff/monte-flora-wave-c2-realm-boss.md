# Handoff: Wave C2 (realm + boss look and feel), 2026-11-22

## Done (PRs into phase-2, auto-merge on green)
- #38 `monte-flora/c2-realm-art`: overworld drawn from `realm_<land>` sheets (overworld/realm_tiles.gd: ground+shore autotile, objects, canopy layer), hero_top sprite, map monsters per land (MapMonster.OF_LAND), banners from Names via WorldMap.REALM_ID/names_id(). Tests: test_realm_art_per_land, test_gate_art_opens_with_the_ability.
- #41 `monte-flora/c2-boss-art`: throne room hero_side sprite, tiles_castle walls/floor/platforms (_draw_solid), GloomLight on boss screen, ui/hud hearts, pixel font, lieutenant echo ghosts (ECHO_SHEET). Test: test_throne_art_in_place.
- Both include #37's commit until it merges. Check `gh pr checks 38` / `41`; pytest "tests" was slow to start.

## In flight: branch `monte-flora/c2-art-fixes` (this commit: only shot.gd + this file)
Goal 3: redraw weak monsters in shadowfall/art/src/make_monsters.py: ash_scarab (blob, needs a real beetle: domed shell split line, horn, 6 legs), cave_bat (wing is a flat triangle: needs scalloped membrane + finger bones), frost_matriarch (spider legs clip right edge; st=1 and move ph=1.6 clip), sand_wyrm (teeth read as a white box in attack: use jaws() with more, thinner teeth). Then fix every "clipped at the margin" note (run `SDL_AUDIODRIVER=dummy <python> shadowfall/art/src/make_monsters.py`; ~25 notes: cinder_drake all frames, frost_wolf, ember_imp, bog_wisp, ...). Rebuild, `sh shadowfall/tools/run_tests.sh --only=art` (ArtCheck), screenshot sheets.

## Next
- Goal 4 juice: overworld has no hit-stop/shake/particles yet. Spec docs/teen/gameplay §4 table: sword hit 3 f stop + shake 1px/4f + white flash 4 f (MapMonster already flashes); kill 6 f + 2px/6f + light motes (+ play the `poof` anim); hurt 10 f + 5px/12f + red edge. Camera: overworld cam uses smoothing 8; consider drag margins / look-ahead. Boss: ThroneFight already has hitstop/slowmo/shake events; add particles (sparks on clang, motes on kill) in boss.gd.
- Shake OFF switch: ask the coordinator for a ui/settings.gd accessibility value (not my folder).
- Asks for others: rules/names.gd could add realm ids (emberhold...) to LAND; LIEUTENANT names table (boss uses fallbacks).

## Gotchas
- A texture first `load()`ed inside a draw callback draws nothing (white/clear). Load in _ready.
- Screenshots: `art/src/shot.gd` (window render at 2x, silent).
