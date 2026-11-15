# Handoff (2026-11-14, 9:06 pm ET; 02:06 UTC 11-15)

## 8. Session state (read first)
- **Orca Run: `run_859805712553`.** No workers running. All PRs merged (#82-#88). Scratch worktrees removed.
- **Main checkout** is on `main` (clean except the user's cave 01 edit, kept local: the robot can't reach its diamond; user will fix in the editor). Backup of the old fight-pause work: `git stash list` (stash@{0}).
- `.pixi` was tracked as a self-symlink (#57); #87 untracked it and the env was rebuilt. If a checkout shows "too many levels of symbolic links", `rm .pixi && pixi install`.
- `~/try-phase2` = origin/phase-2 @ def7215 (17 caves). User's commands: editor `cd ~/try-phase2 && <main checkout>/.pixi/envs/default/bin/python editor.py`; play `... game.py --phase2`. If they save caves there, PR them into phase-2 when they say.

## Next: the teen version (TODO.md section "a teen version of Phase 2", T1-T5), all on `phase-2`
User's words (verbatim, 2026-11-15 ~02:00 UTC), after I proposed teen changes:
"Here are some action items we can start addressing with sub tasks
1. Lets refactor the game to make it more teenager friendly, including a darker theme. Lets give the game a cooler name. Related to this change, lets introduce a mechanism that light in the overworld slowly (very slow) is becoming darker as the Shadow King truly pulls light from the world. Lets flesh out the story more.
2. For all attacks, lets use R
3. Make the movement in the overworld smoothing rather than moving 1 square at a time, have the monsters roaming somewhat freely as well. Remove the random effects."

Plan (decide, don't grill): one worker per item, in their own worktrees, PRs into phase-2. Mind hot files (game.py):
- Wave 1 in parallel: **T1** (theme/name/story: phase2/ui.py, draw_hud.py, story data, title; avoid map movement code) and **T3** (keys: game.py key tables ~l.248-263 and on_battle ~l.1649, caves.py, castle/throne, tutorial TIPS, phase2 hints) and **T5** (small: rules.random_event / end_of_turn ~l.1784; skip in phase 2 only, or all).
- Wave 2 after T3/T5 merge: **T4** smooth movement + free-roaming monsters (big: game.py map loop, phase2/monsters.py, phase2/world.py; turn-based end_of_turn needs a real-time tick). Then **T2** darkening (draw_world.py overlay + main-quest link) after T1 (palette).
Facts found: R today = USE_KEYS in caves (game.py:262) and "Run" in map fights (game.py:1650; A/1 attack). F shoots. Phase 2 map monsters already visible (phase2/monsters.py), no surprise fights. "Random effects" = rules.random_event (thistle hurts, heals, armor).
Name: no name chosen yet; T1 worker proposes 3, picks one, user can change.

## Still waiting on the user
- Phase 2 itch.io page + `gh variable set ITCH_GAME_PHASE2 ...` (steps in git history of this file, PR #84).

## Gotchas
- Workers hit the ~120K context hook: restart them in the same worktree pointing at their .handoff/ notes. Tell them to use subagents and push WIP early.
- Stuck auto-merge (green PR not merging: two `tests` runs race): `gh run rerun <PR's pull_request Tests run id>`.
- Repo guard blocks force-push: merge origin/<base> instead of rebase.
- zsh: `$b:g...` modifiers bite in `origin/$b:file`; write `${b}`.
- Tests hard-code Icy Steps = 5, Lava Escape = 10; don't renumber caves.
- pixi in worktrees: `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests`.
- Branches: `main` Classic (merges publish to itch.io); `phase-2` bigger game (PRs go here); `phase-3` Godot prototype.
