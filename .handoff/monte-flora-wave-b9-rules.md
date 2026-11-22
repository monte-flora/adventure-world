# B9 handoff (branch monte-flora/wave-b9-rules, off phase-2 at the time of writing)

Done and merged: #25 (the test runner fails on errors, LevelFile.all), #27 (playthrough robot core/tests/test_playthrough.gd,
the realm from levels/realm when present), #28 (HUD and GloomLight in overworld and caves), #30 (save at C and on a Stone, M mute, Game.save_path for tests).

Next, in order (coordinator task_22fb8a1d6565), one small PR each:
1. Wire rules/vitals.gd into caves/cave.gd and overworld/overworld.gd:
   - hurts: hero.hurt now lowers Game.hearts directly; route the damage through Vitals.hurt().
   - death: call Vitals.die({"scene":..,"file":..,"x":..,"y":..}). The cave wakes at its checkpoint (_wake_at_checkpoint);
     the overworld at respawn (the last waystone, _on_hurt). Lost Light: draw and touch it at `where`, then Vitals.recover_lost_light().
   - Lumen: Vitals.lumen_hit() on a sword hit (cave _attack, overworld _on_swing); a LumenHeal (rules/lumen_heal.gd) step on the
     "heal" action (Q), held while standing still.
   - test in core/tests/test_wiring.gd: you can lose on the path (hearts reach 0, you respawn, the gold becomes a Lost Light, you get it back).
2. ui/pause.gd: the quest tab reads Quests.log_entries() (check the name in rules/quests.gd) and the sigil tab reads Sigils.slots()/worn()/owned(), with Names.QUEST/SIGIL.
3. After BL's levels PR merges: merge origin/phase-2 and run --only=playthrough. any_stone must be true and the robot must take the Dawnstone.
   Locally it worked with `git checkout origin/monte-flora/wave-bl-levels -- levels/realm levels/stone`.
Rules: silent runs only (godot --headless; pygame SDL_AUDIODRIVER=dummy), never open the game in a browser. Skip shop, dialogue and balance.
Tests: sh shadowfall/tools/run_tests.sh; pytest via /Users/montgomeryflora/noah-adventure/.pixi/envs/default/bin/python -m pytest -q -n auto tests.
