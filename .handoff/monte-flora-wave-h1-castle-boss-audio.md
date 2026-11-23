# H1 handoff (PAUSED 2026-11-22)

## Done (PR 1: castle key/door)
- shadowfall/boss/boss.gd: each castle door (D) is shut until you take its key (K, levels 1/3/5) or pull its
  lever (L, levels 2/4; detected by sword hit in hero.attack_hits or interact beside it). Shut door: grim line
  (`locked_line()`), every 2nd bump the level's `locked door says:` hint; sfx door_locked (falls back to "land").
  Open: "door_open" sfx (falls back to "pound"), shake 3 px, swing-open draw, 0.8 s, then next level/throne.
  Key and barred door drawn from tiles_castle (key, door). No level files changed (K/D/L already there).
- tests: test_castle_door_leads_on (blocks without key, opens with it), test_every_castle_door_is_locked.
- godot-test 217/217, pytest 749 passed.

## Next
2. Boss SFX (PR 2): add audio/render/render_sfx.py (FluidSynth layers: orchestra hit 55, taiko, timpani, choir,
   reverse cymbal + numpy noise whooshes) -> audio/sfx/<name>.ogg mono, faded ends. Names: boss_slash, boss_beam
   (Eclipse cast), boss_phase, boss_hit, boss_defeat, sunfang, door_open, door_locked. Add `Sfx.RECORDED` list;
   Audio.sfx_stream loads res://audio/sfx/<name>.ogg when there (return type AudioStream, keep NAMES synth for
   test_peaks). boss.gd `_sfx`: accept RECORDED names. Test: files exist, short, not looping, total small.
3. Boss tunes (PR 3): tunes.gd: keep "boss" = Blade, add "boss_eclipse", "boss_fall" (140 bpm, 8 bars, lead +
   dark_lead varied rhythm, beat 3+ different bars; tests in audio/tests enforce it), ORCHESTRA entries in
   render_music.py, render with `pixi run -e music render-music`. Victory sting: Shadowfall motif resolving to
   A major (brass), render to audio/sfx/victory.ogg. boss.gd MUSIC_LIKE: boss_b -> boss_eclipse; throne_fight
   emits music boss_c at _phase(3); Audio.intensity phase1 0, phase2 0.5 (1.0 while dark), phase3 0.8;
   play victory on "won".
- Nobody has listened to any sound (silent runs only).

## Asks for other owners
- caves/: K, D, + are not in CaveTiles (drawn/handled by boss.gd now); light shards (+) are never picked up in
  Godot. A `lever_pulled` signal from cave.gd would be cleaner than polling attack_hits.
