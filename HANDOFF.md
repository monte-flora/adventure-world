# Handoff (2026-11-14, 11:20 pm ET; 04:20 UTC 11-15)

## 8. Session state (read first)
- **Orca Run: `run_859805712553`.** No workers running (all settled; finished ones may still show kept-open, release them).
- **The repo moved.** New PUBLIC repo `monte-flora/adventure-world` (created 2026-11-15 ~04:00 UTC): one fresh commit per branch (main, phase-2, phase-3), no history, author = the user's GitHub noreply address. The old private repo (`old` remote) is the archive: never push to it again (its Actions minutes ran out; overage billed). Don't archive/delete it unless the user says.
- **Local checkouts now track the new repo:** in the main checkout, `~/try-phase2`, `~/try-phase3`: `origin` = adventure-world, `old` = the private repo. Main checkout is on `main` = origin/main (c26d0b9). Old worktrees under orca/workspaces (teen-*, public-scrub, phase2-*) are on old history: remove them; new workers start fresh off origin/<branch>.
- **The user's local edits, kept (don't revert):** main checkout `levels/caves/01_the_easy_moss_cave.txt`; `~/try-phase2` `levels/caves/05_green_lvl_1.txt` (cave body = the user's; only the about line was changed to the name-free text). Shared git stash: stash@{0}/{1} = copies of those two edits made during the move (can drop), stash@{2} = old fight-pause backup.
- **Name rule (public repo):** the hero is "the Hero", Classic = "Adventure World", Phase 2 = "Shadowfall", Phase 3 = "Adventure World 3D". Nothing in the repo may contain the kid's name, local user paths, or emails: check with `git grep -i -E '<name>|<user>|@' ` before every PR (the scrub PR #93 lists the exact pattern in its body on the old repo).
- **Teen version on phase-2:** T1 look/name/story (#92), T3 R attacks (#91), T5 no random effects (#90) merged. Mark T1/T3/T5 `[x] 2026-11-14` in main's TODO.md if not yet. Also mark "Go public" `[x] 2026-11-15`.
- The user played nothing yet; told them: `cd ~/try-phase2 && <main checkout>/.pixi/envs/default/bin/python game.py --phase2`.

## Next
1. **User must do (never us):** on adventure-world, set secret `BUTLER_API_KEY` and variables `ITCH_GAME` (and `ITCH_GAME_PHASE2` when that page exists). Warn: Actions logs are public on a public repo, and the current itch.io page slug contains the kid's name, so suggest a new name-free itch.io page/slug (or rename it) before setting `ITCH_GAME`. Until set, web.yml just skips the upload.
2. Check the first CI runs on adventure-world pass (tests ×2, build-web) and auto-merge works (workflow token permissions are set in auto-merge.yml).
3. **T4** smooth overworld movement + free-roaming monsters (big; game.py map loop, phase2/monsters.py, phase2/world.py; turn-based end_of_turn needs a real-time tick). One worker, new worktree off origin/phase-2 of the NEW repo, PR into phase-2.
4. Then **T2** world slowly darkening (T1 left a hook: `dusk_alpha` in phase2/theme.py; minimap not dimmed yet).
5. Still open: Stage 4 balance + a robot that plays the main quest.

## The user's words (UTC 2026-11-15)
- ~02:00: the teen list (T1-T5 in TODO.md): "1. Lets refactor the game to make it more teenager friendly, including a darker theme. Lets give the game a cooler name. Related to this change, lets introduce a mechanism that light in the overworld slowly (very slow) is becoming darker as the Shadow King truly pulls light from the world. Lets flesh out the story more. 2. For all attacks, lets use R 3. Make the movement in the overworld smoothing rather than moving 1 square at a time, have the monsters roaming somewhat freely as well. Remove the random effects."
- ~03:00: "Once there is a early prototype that I can play, share the python command for me to run" (done).
- ~03:10, on running out of Actions minutes: "Make the repo public, but remove [the kid]'s name from it"; chose: new public repo (fresh history), hero = "the Hero".

## Gotchas
- Workers hit the ~120K context hook: restart them in the same worktree pointing at their .handoff/ notes. Tell them to use subagents and push WIP early.
- Stuck auto-merge (green PR not merging: two `tests` runs race): `gh run rerun <PR's pull_request Tests run id>`.
- Repo guard blocks force-push: merge origin/<base> instead of rebase.
- zsh: `$b:g...` modifiers bite in `origin/$b:file`; write `${b}`.
- Tests hard-code Icy Steps = 5, Lava Escape = 10; don't renumber caves.
- pixi in worktrees: `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests`.
- Branches: `main` Classic (merges publish to itch.io); `phase-2` bigger game (PRs go here); `phase-3` Godot prototype.
