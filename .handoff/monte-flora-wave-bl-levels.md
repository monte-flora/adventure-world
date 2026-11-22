# BL Levels hand-off (paused 2026-11-21, usage cap)

## Done (pushed, no PR yet)
- `levels/realm/`: 6x5-screen realm (180x85), 8 land files + `9_umbral_reach.txt` (3x3 mirror), README with format. Godot only: `levels/world/` left for pygame (its tests pin ~110x76 and old names). `realm_check.py`: realm OK (gating order, waystone >=2 screens from stone Mine, all mines reachable).
- `levels/stone/` 1,2,3,4,6: robot OK. Headers `stone:` `land:` `needs:` (`dark:` on 2,7), `C` checkpoints.
- `land:` + `needs:` (climb if `%`) on all 17 caves, secret, shadow (`dark: yes`), castle.
- pygame pytest: 733 passed (before caves 2/4/5/7 landed; pygame doesn't read stone/ or realm/). Godot: a temp test loaded every file in caves/secret/shadow/castle/stone/realm OK (not committed; copy in `.handoff/bl-tools/test_bl_tmp.gd`).

## In flight
- `levels/stone/5_the_wintermarch_climb.txt`: robot STUCK at (71, 24), lever not reached.
- `levels/stone/7_the_mirefen_maw.txt`: robot STUCK at (31, 11), lever not reached.

## Next
1. Fix 5 and 7 until `.pixi/envs/default/bin/python .handoff/bl-tools/check_stone.py levels/stone/*.txt` all OK.
2. `python3 .handoff/bl-tools/realm_check.py` prints "realm OK"; rerun pytest + godot-test.
3. Drop `.handoff/bl-tools/` from the branch, open PR into phase-2, worker_done.

## Asks for the report
- B1: read `levels/realm/`, not `levels/world/`. `O` = rubble there.
- B0/B9: `LevelFile.settings` keeps only the last repeated key (`mine:`, `gate:`); add stone + realm to `test_every_level_file_loads`.
- B7: robot to cover `levels/stone/` (C as air). `C` not added to pygame-read castle/shadow files (pygame doesn't know `C`).
