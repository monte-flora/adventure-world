# Handoff (2026-11-24, 2:40 pm ET; 19:40 UTC)

## 8. Session state (read first)
- **Restart:** a fresh chat in `~/noah-adventure` reads this file, `AGENTS.md` and `TODO.md`. Plain Orca, no grafite-coord kit (user, 2026-11-22). Hooks off via `.claude/settings.json` (committed) and `~/noah-adventure/.claude/settings.local.json` (local).
- **Orca Run:** `run_859805712553` (bind: `orca orchestration run-use --id run_859805712553`).
- **Worker running:** `ctx_98f8f8c232b5` **animated dialogue faces** in `~/orca/workspaces/noah-adventure/animated-faces` (spec `~/orca/workspaces/noah-adventure/specs/animated-faces.md`), PR into `phase-2`. When it reports: release it, update the play copy, run its importer on the user's seer GIF `~/Desktop/Gemini_Generated_Gif_k3l1h9k3l1h9k3l1.gif` into the play copy (not committed), show the user.
- **Done 2026-11-23/24 (all merged into `phase-2`):** G2b gloom shots + docs (#72); H1 boss SFX (#70), 3-phase boss tunes + victory sting (#74); `gemini-next` helper (#73) + ground import fix (#75) + redo list (#76) + land ground rule (#78); `gemini-caves` (#79) + painted throne hall (#80); every overworld land painted (#81-83, #86, #87); Gemini characters prompt set, `import-characters`, `hero-compare`, `gemini-next --set characters` (#84) + dialogue face slot (#85); small props 1.5x (#88).
- **Main checkout** `~/noah-adventure` on `main`: the user's dirty `levels/caves/01_the_easy_moss_cave.txt` and conflicted `levels/caves/05_green_lvl_1.txt` (stash-pop residue). The user's files: don't touch.
- **Play copy** `~/try-shadowfall` = detached `origin/phase-2` (#88). It holds the user's Gemini art, NOT committed: `shadowfall/realm/gemini/in/*` (106 sources), the imported `shadowfall/realm/ground/*` + `props/*` (183 modified files), `shadowfall/realm/gemini/redo.txt` (git-ignored), `shadowfall/realm/gemini/rejected/`, `levels/polish/17_the_fire_mountain/`. Update with `git fetch && git checkout --detach origin/phase-2 && godot --headless --path shadowfall --import` (git keeps local mods; if it aborts on a file identical to the target, `git checkout -- <file>` first). Python: `/Users/montgomeryflora/noah-adventure/.pixi/envs/default/bin/python`.
- **Storyline draft** (user wants to edit it): `~/orca/workspaces/noah-adventure/storyline/docs/teen/story/STORYLINE.md`, branch `monte-flora/storyline`, uncommitted. 47 "(new)" beats, 18 "(doc)" beats, 12 numbered open questions (land order Mere vs Hollowcrown; Sunken Bell name; Ashen Gate/Stair; lieutenant fights per stone cave; the King's name; hero's secret; ending; Shadowgate open/sealed; lieutenants' pasts; castle taunts; Sunfang's origin; finale cameos).

## The user's words (verbatim, UTC)
- 2026-11-21: "For any answers about gameplay or naming, we want whatever is most bad ass, epic, and engaging. Heavily take inspiration from Lord of the Rings and Game of Thrones."
- 2026-11-21: "this is an incredibly low priority project, so once we get to 50%, pause this project until the 5-hr window resests" (overrides: "keep going", "Start it now").
- 2026-11-22: "Have the agent turn off the music while its developing the game so I can listen to my own music"
- 2026-11-22: "It'd be cool to still have some kind of cave level editor ... once we save it, we ask the AI to polish it" then "Go with option 1" (Gemini web UI by hand; no API, no keys, never automate the site).
- 2026-11-23: "Build option 1" (gemini-next); "The new game design looks amazing!"; "Can we finish the rest of Emberhold too like the weepingwillow land ... and any other places on the main overworld map?"; "Yes, start with portraits, villagers and the hero test".
- 2026-11-24: "I've hit my image generation limit until tomorrow, so characters and caves will have to wait"; "yes, start 1 and 4" (animated faces + this handoff).

## Waiting on the user
- **Gemini images** (in `~/try-shadowfall`, always `--downloads ~/gemini-drop`: macOS blocks Terminal from ~/Downloads):
  - realm: `pixi run gemini-next --downloads ~/gemini-drop`: 106/106, 1 redo queued (shadowgate_ground_black_stone came out as swamp mud).
  - characters: `pixi run gemini-next --set characters --downloads ~/gemini-drop`: 0/43 (2 portraits, 20 faces, 20 villagers, `hero_walk_down` test). After the hero test: `pixi run hero-compare`, show `shadowfall/art/sheets/candidates/hero_compare.png`; user decides if Gemini does the hero.
  - caves: `pixi run gemini-caves --downloads ~/gemini-drop`: 1/34 (map image on the clipboard, Enter, then the words).
  - When happy: PR their images into `phase-2` (they are the user's art; ask first).
- Storyline edits / answers to the 12 questions.
- Godot itch.io page (secrets are the user's).

## Next
1. Animated faces worker report (above).
2. Review each new batch of user images: duplicates (`cmp`), ground on magenta, props without magenta, pink edges, and tile 2x2 for seams/banding (Gemini repeats the previous picture when a chat is reused: tell the user "new chat per picture").
3. Small art fixes in TODO (lamppost glow; grey lamppost heads / cave torch at gloom 3).
4. Fold the user's storyline choices into `rules/data/*.json`, level `says:` lines, boss lines.

## How main runs workers (plain Orca)
- Start: `orca orchestration worker-start --spec-file <spec> --task-title "<t>" --agent claude --worktree new-top-level --name <n> --base-branch origin/phase-2 --repo path:/Users/montgomeryflora/noah-adventure --run run_859805712553 --model claude-opus-5-5 --effort medium --json`. Restart in place: `--worktree path:<worktree>` and **no** `--name`/`--repo`/`--base-branch` (they're creation-only options; error otherwise). Keep specs in `~/orca/workspaces/noah-adventure/specs/` (scratchpad is wiped daily).
- Every brief carries: own folders only; names from `rules/names.gd`; the tone quote; silent runs; haiku/sonnet subagents; **never end a turn while waiting on tests or CI** (workers still do it: nudge them); noreply git identity, no force-push, no TODO/HANDOFF edits; small non-draft PRs into `phase-2`; `.handoff/<branch>.md` + restart at ~120K.
- Mail: `orca orchestration check --run run_859805712553 --wait --types worker_done,question,escalation --timeout-ms 7000000 --format | grep -v _keepalive` in the background. "Worker stopped without reporting" after a pause is expected.
- Usage: `orca account list --json` -> `result.rateLimits.claude.session.usedPercent` (`resetsAt` ms). At 50 %: message workers to push WIP + `.handoff/` and stop; resume with a message after the reset (or on "keep going").
- Done worker: `orca orchestration worker-release --dispatch <id>`.

## Gotchas
- Stuck auto-merge (green PR not merging; the two `tests` runs race): `gh run rerun <the PR's pull_request Tests run id>`. Almost every PR needs it.
- Local pytest always shows 2 `test_web` errors (Homebrew ffmpeg lacks libvorbis); CI is fine.
- A fresh Godot checkout needs `godot --headless --path shadowfall --import` once. Screenshot: `godot --audio-driver Dummy --path shadowfall -- --scene=overworld --shot=<png> [--cell=col,row] [--gloom=0..3]` (quits by itself; macOS has no `timeout`). Throne fight: `-- --scene=boss`; castle level: `--castle=N`.
- zsh: unquoted `$VAR` lists don't word-split (use arrays); `===` at line start is a zsh error.
- Repo guard blocks force-push: merge, don't rebase. Tests hard-code Icy Steps = 5, Lava Escape = 10: don't renumber caves.
- Merges into `main` publish the Classic game to itch.io; PRs into `main` need the user's OK (TODO/HANDOFF-only PRs have been fine).
- Branches: `main` Classic; `phase-2` the bigger game + Shadowfall (Godot); `phase-3` the old Godot prototype.
