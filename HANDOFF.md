# Handoff (2026-11-23, 3:55 pm ET; 20:55 UTC)

## 8. Session state (read first)
- **Restart:** a fresh chat in `~/noah-adventure` reads this file, `AGENTS.md` and `TODO.md`. No `/coord-main`, no grafite-coord kit (user, 2026-11-22: "For this particular projects, let separate ourselves from grafite-coord"). Hooks are off via `.claude/settings.json` (committed) and `~/noah-adventure/.claude/settings.local.json` (local).
- **Orca Run:** `run_859805712553` (bind: `orca orchestration run-use --id run_859805712553`). **No workers running.** Paused by the user ("Pause on this work", 2026-11-23 ~00:01 UTC): G2 and H1, both with merged part-a PRs and `.handoff/` notes in their worktrees.
- **All PRs merged** (latest #68). `phase-2` has the Godot game (Shadowfall) in `shadowfall/` and the pygame Phase 2.
- **Main checkout** `~/noah-adventure` on `main`: the user's dirty `levels/caves/01_the_easy_moss_cave.txt` and a conflicted `levels/caves/05_green_lvl_1.txt` (stash-pop residue). The user's files: don't touch.
- **Play copy** `~/try-shadowfall` = detached `origin/phase-2` at #66 (update: `git fetch && git checkout --detach origin/phase-2 && godot --headless --path shadowfall --import`). It holds the user's untracked `levels/polish/17_the_fire_mountain/` (map + prompt, no painting yet); backup of polish folders in `~/polish-backup-1755`. Python for it: `/Users/montgomeryflora/noah-adventure/.pixi/envs/default/bin/python`.
- **Concept/target images** (the user's) in `~/orca/workspaces/noah-adventure/refs/` and committed in `docs/teen/art/ref/`.

## The user's words (verbatim, UTC)
- 2026-11-21: "For any answers about gameplay or naming, we want whatever is most bad ass, epic, and engaging. Heavily take inspiration from Lord of the Rings and Game of Thrones."
- 2026-11-21: "this is an incredibly low priority project, so once we get to 50%, pause this project until the 5-hr window resests" (they override it at times: "Start it now, don't wait for the reset").
- 2026-11-22: "Have the agent turn off the music while its developing the game so I can listen to my own music"
- 2026-11-22: "We want a character as close to this as we can get" (Lanternbearer, Shadow King concepts).
- 2026-11-22: "What if we re-design the game such the background is a static element, so it can have a polish, handraw, mixed pixel size look and that characters move around on it?"
- 2026-11-22: "It'd be cool to still have some kind of cave level editor ... once we save it, we ask the AI to polish it" then "Go with option 1" (hand-off to the Gemini web UI; no API, no keys, never automate the site).
- 2026-11-22: "Would it be better to just describe the base layer and provide a PNG with the rough location of where the road is and then we could have it create repeatable textures like trees, houses, lampposts that you place?" then "Go ahead, start it now".
- 2026-11-22 (E2 only): "Just for the redesign, use Fable 5.2 with medium effort".

## Waiting on the user
- **Gemini images:** realm textures + props (prompts in `~/try-shadowfall/shadowfall/realm/gemini/prompts/`, style line in `STYLE.txt`, save to `gemini/in/<name>.png`, then `PATH=<main>/.pixi/envs/default/bin:$PATH sh shadowfall/tools/import_art.sh`), and the Fire Mountain cave painting (`polish.py import levels/caves/17_the_fire_mountain.txt`). When happy, PR their images into `phase-2`.
- Realm direction: painted (recommended; G1 textures + props path is built) vs tiles (E1 shadows/cliffs/props paused) vs mix. Not decided.
- Godot itch.io page (secrets are the user's).

## Next (when the user says go)
1. Resume **G2** in `~/orca/workspaces/noah-adventure/wave-g2-darkening-painted` (read its `.handoff/monte-flora-wave-g2-darkening-painted.md`): gloom screenshots, docs, full test run.
2. Resume **H1** in `.../wave-h1-castle-boss-audio` (`.handoff/monte-flora-wave-h1-castle-boss-audio.md`): boss SFX, 3-phase boss tunes, victory sting.
3. After the user's Gemini images: import, screenshot Emberhold, tune house lights, PR the images.
4. Later list in `TODO.md`.

## How main runs workers (plain Orca)
- Start: `orca orchestration worker-start --spec-file <spec> --task-title "<t>" --agent claude --worktree new-top-level --name <n> --base-branch origin/phase-2 --repo path:/Users/montgomeryflora/noah-adventure --run run_859805712553 --model claude-opus-5-5 --effort medium --json`. Restart in place: `--worktree path:<worktree>` (no `--repo`). Model: Opus 5.5 medium unless the user says otherwise.
- Every brief carries: own folders only; names from `rules/names.gd`; the tone quote; **silent runs** (Godot `--audio-driver Dummy`/`--headless`, pygame `SDL_AUDIODRIVER=dummy`); haiku/sonnet subagents; never end a turn while waiting on CI (`gh pr checks N --watch`); noreply git identity, no force-push, no TODO/HANDOFF edits; small non-draft PRs into `phase-2`; `.handoff/<branch>.md` + ask for restart at ~120K (workers hit it fast: restart them in the same worktree).
- Mail: `orca orchestration check --run run_859805712553 --wait --types worker_done,question,escalation --timeout-ms 7000000 --format | grep -v _keepalive` in the background (2-h tool cap: re-arm).
- Usage: `orca account list --json` -> `result.rateLimits.claude.session.usedPercent` (`resetsAt` ms). At 50 %: tell workers to push WIP + `.handoff/` and stop, or for a short gap a blocking `until [ $(date +%H%M) -ge HHMM ]; do sleep 60; done`.
- Done worker: `orca orchestration worker-release --dispatch <id>`; remove a clean merged worktree with `git worktree remove --force`.

## Gotchas
- Stuck auto-merge (green PR not merging, the two `tests` runs race): `gh run rerun <the PR's pull_request Tests run id>`.
- A fresh Godot checkout needs `godot --headless --path shadowfall --import` once (else "Paths not declared").
- The scratchpad under /private/tmp is wiped between days: keep specs in files you can rebuild.
- Repo guard blocks force-push: merge, don't rebase. Tests hard-code Icy Steps = 5, Lava Escape = 10: don't renumber caves.
- Merges into `main` publish the Classic game to itch.io; PRs into `main` need the user's OK.
- Branches: `main` Classic; `phase-2` the bigger game + Shadowfall (Godot); `phase-3` the old Godot prototype.
