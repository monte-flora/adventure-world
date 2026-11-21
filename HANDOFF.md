# Handoff (2026-11-21, 6:11 pm ET; 23:11 UTC)

## 8. Session state (read first)
- **Orca Run: `run_859805712553`.** Repo: public `monte-flora/adventure-world`. The old private repo is **archived** (2026-11-21, user's call): no commits or pushes; local `old` remotes have push disabled.
- **Repo-local git identity = the user's GitHub noreply address** (set in the main checkout's .git/config, so all worktrees share it). Every worker checks `git log --format=%ae` before pushing; the T4 leak was fixed by deleting a branch.
- **Teen T1-T5 all merged into phase-2** (T4 smooth movement PR #2, T2 darkening PR #3).
- **Teen refactor (user, 2026-11-21):** "completely refactor the game towards a teenage audience including the art style, gameplay mechanics, and music ... explore if another engine would be better for smoother 2D gameplay. I still want a top-down overworld with a side scrolling platformer with caves ... search for images of ... Shovel Knight, A Link to the Past, Hollow Knight. Keep everything at Opus 5.5 medium and leverage cheaper models where possible. Keep the current title of Shadowfall and the general theme of the Shadow King."
  - **Wave A done.** Reports in `docs/teen/<area>/README.md` on phase-2: audio #6, gameplay #7, art #8, levels #10, engine #11. If 8, 10 or 11 is still open, rerun its pull_request Tests run (the race).
  - **User decisions:**
    - engine **Godot 4.7**
    - **32-px art**
    - hero = **hooded wanderer with a lantern**
    - darkening stages as drawn
    - **our own pixel font**
    - cut XP, lives, food and sword wear
    - Nightfall = a 3x3 mirror of the map's centre
    - itch.io runs both builds for a while
  - **Main's defaults (user didn't object):** retune caves for the new jump; home = Hearthvale; one merged list of 7 abilities; checkpoints don't break for gems; dropped gold on Standard, off in Assist; smooth camera; fix the game.py vsync hitch. All are in TODO.md via PR #12.
  - Summary page shown to the user: chat-scratch `shadowfall-wave-a-3f9b.html`.
- **Workers running** (all Opus 5.5 medium; start workers with `coord-whoami start [--usage-override "<user words>"] -- <worker-start args> --model claude-opus-5-5 --effort medium`):
  - `ctx_7c8b883462ac` pixel font → `assets/fonts/`, PR into phase-2
  - `ctx_64edfa9c0d1e` **B0** Godot scaffold + CI in `shadowfall/`, PR into phase-2; it writes `shadowfall/WAVE_B.md` (the parallel task list)
  - `ctx_e9f0e97cae5a` game.py 59 fps vsync fix, PR into **main**
- Open TODO PR #12 (decisions).

## Next
1. Wait for mail. When B0 reports: read `shadowfall/WAVE_B.md`, then launch the 6-8 Wave B workers in parallel (one folder each; Opus 5.5 medium; tell them to use haiku/sonnet subagents). The game.py/caves.py hot-file rule doesn't apply inside `shadowfall/`; folder ownership does.
2. Reference games are for study only: no screenshots or assets in the public repo; everything original.

## Still waiting on the user
- The main checkout `levels/caves/05_green_lvl_1.txt` has merge-conflict markers (a stash-pop residue); the user's file, not touched.
- itch.io: secret `BUTLER_API_KEY` + variable `ITCH_GAME` on adventure-world, on a page whose address has no kid's name.
- Next pygame items after the refactor: Stage 4 balance, a robot that plays the main quest.

## Gotchas
- Workers hit the ~120K context hook: restart them in the same worktree pointing at their .handoff/ notes. Tell them to use subagents and push WIP early.
- Stuck auto-merge (green PR not merging: two `tests` runs race): `gh run rerun <PR's pull_request Tests run id>`.
- Repo guard blocks force-push: merge origin/<base> instead of rebase.
- zsh: `$b:g...` modifiers bite in `origin/$b:file`; write `${b}`.
- Tests hard-code Icy Steps = 5, Lava Escape = 10; don't renumber caves.
- pixi in worktrees: `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests`.
- Branches: `main` Classic (merges publish to itch.io); `phase-2` bigger game (PRs go here); `phase-3` Godot prototype.
