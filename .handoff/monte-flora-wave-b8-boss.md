# B8 Castle + boss: hand-off (PAUSED 2026-11-21, usage cap)

Branch `monte-flora/wave-b8-boss` (base `phase-2`). Only `shadowfall/boss/` touched (+ this file).

## Done
- `boss/throne_fight.gd` (ThroneFight): whole fight as pure data, ticked per frame (no physics engine).
  - Phase 1 Blade: glow 48 f -> slash -> stuck 1 s; fireballs x3 -> tired 0.9 s; leap -> shadow mark 42 f -> slam + 2 floor waves -> landed 0.9 s.
  - Phase 2 Eclipse: dark shader; vanish 36 f, shimmer 30 f, rise; exposed 1 s; echo of 2 random lieutenants of 7 (each its own telegraph + dodge); 3 homing shadow orbs (pogo/slash); spent 1.1 s.
  - Phase 3 Fall: floor -> 5 platforms + 2 one-way ledges over the void (pit = 1 heart + respawn); crown floats; beam with 36 f warning line; orb rain; after each beam the crown sinks low for 2 s: pogo it x3 -> Sunfang finale cut-scene -> won, `flags.shadow_king_beaten`, gloom 0.
  - Hurt only in punish windows (else his armour clangs). 90 HP, Sunfang 7 (+1 per light shard). His hits = 2 hearts. Juice events: hit-stop, shake, slow-mo on phase change.
- `boss/arena_hero.gd`: box-platformer hero with HeroSide's numbers, sword arc 3+6+8 f, DOWN+R pogo, Wraithstep dash (i-frames f2-f9).
- `boss/throne_bot.gd`: scripted player.
- `boss/castle.gd`: 5 levels from `levels/castle/` via Paths; door -> next level, last -> throne; Sunfang forged at the gate with 7 stones; `Castle.display()` reads names from `rules/names.gd` with fallbacks.
- `boss/boss.gd` screen: castle mode embeds B2's `cave.tscn` (sets `Scenes.args.file`) and watches the hero on `D`; throne mode draws placeholder art, `eclipse.gdshader` darkness (3 rings), a glow layer, HUD (hearts, 3-phase bar, captions), retry on loss.
- `boss/tests/test_boss.gd`: 9 tests; all passed before the last tuning round.

## In flight
- After making him hurtable only in punish windows and adding the dash, the bot wins all 20 seeds with 99 hearts but loses ~5-12 hearts, so `test_bot_beats_the_shadow_king` (5 hearts) FAILS now.
- Where hits land (20 seeds): p1 slash ~23 (cornered logic in `throne_bot._ground`, dash-through timing), p3 beam ~39 (bot dodge; `_dodge` is now locked per beam, still hit: trace why), p3 watch ~13 (void falls while chasing the crown).
- Debug tool used: a temp test tallying hearts lost by `p<phase> <state> <hazards near>` (deleted; quick to rewrite).

## Next
1. Fix the bot (above). Keep fight ~60 s for the bot.
2. `pixi run godot-test` (whole suite + boot) and pygame pytest; push; open PR into `phase-2`.
3. Asks for the report: B4 add `BOSS`, `SUNFANG`, `LIEUTENANT` (dict by id) to `rules/names.gd`; B2 castle `D` door/key handling (touching `D` counts as done for now); B6 sfx names used (boss_glow, boss_slash, boss_fire, boss_aim, boss_leap, boss_land, boss_shimmer, boss_beam, boss_hit, boss_phase, crown_hit, sunfang, clang, cut, pogo, hurt, forge) and music (castle, throne, boss_a, boss_b); B9 may swap ArenaHero for HeroSide.
