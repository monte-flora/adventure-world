# Adventure World: rules for agents

This is a pygame game for kids. A parent builds it with their kid. Repo: monte-flora/adventure-world, base branch `main`.
Read `HANDOFF.md` to see where things stand, and `TODO.md` for everything still open.

## How we work
- **TODO.md is the one to-do list.** Add each new ask to it before you build it. Mark an item `[~]` while you build it and `[x] YYYY-MM-DD` once it is verified.
- **Commit or push only when the user asks.** Once the user OKs a change, commit it, push it and open a PR.
- **Never merge by hand.** `.github/workflows/auto-merge.yml` merges a PR when all of its checks are green: `tests` ×2 and `build-web`. It then deletes the branch and publishes the game to itch.io. To stop a merge, add the `hold` label or open the PR as a draft. Merge by hand (`gh pr merge N --merge --delete-branch`) only if the workflow skips a green PR and the user says to.
- **Keep the user's hand edits** to level files and settings (for example `START_HEALTH`). A dirty `levels/` file is the user's work, so don't revert it.
- **Decide, don't grill.** Act on your recommended choice and note what you assumed. Ask only when the decision really is the user's.
- **Be very concise.** Give times in US Eastern, 12-hour am/pm.
- **Context limit** (every Orca session; user-level hook): 120K finish the step, 150K or a milestone restart from files (`coord.yaml` `restart`: main says "Ready. Type /clear, then /coord-main", same chat; a worker asks the coordinator), 180K only the hand-off runs; never `/compact`.
- **The itch.io page stays Restricted.** Never enter API keys, tokens or passwords.
- **Parallel work:** run one agent per worktree. Two agents never edit the same files at once (`game.py`, `caves.py` and `rules.py` are hot spots). Only the coordinating agent edits TODO.md, unless the task's PR owns that edit.

## Commands (pixi)
- `pixi run game`: play the game. Play-test shortcuts: `pixi run nightfall` (Nightfall Hollow), `pixi run castle` (next to the castle), `pixi run throne` (the boss).
- `pixi run editor`: open the cave editor.
- `pixi run test`: run the full pytest suite (about 420 tests). It must pass after any code change.
- `pixi run test-all-caves`: same, and a robot also beats every cave (slow).
- `pixi run test-editor`
- `pixi run -e web build-web`: build the web version.
- In a worktree without `.pixi`, use `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n 8 tests`.

## Map of the code
- `game.py`: the main loop, the map, map fights (`on_battle`, `draw_battle`), the panel, lives and Nightfall.
- `caves.py`: cave play, monsters and `plan_caves`: every Mine plays a file from `levels/caves/`, nearest home first, and the files go round again when there are more Mines than files (`plan_cave_files` has the rule). No cave is built by code.
- `castle.py`, `throne.py` (the Shadow King), `rules.py` (stats and crafting), `sprites.py` (pixel art), `story.py`, `tutorial.py` (`TIPS`), `settings.py`.
- `levels/caves/`: caves named `NN_name.txt`, one per Mine: 12 in Classic (`main`), 17 on `phase-2`. `levels/secret/` has the Secret Mine's cave, `levels/shadow/` has the 3 Nightfall caves and `levels/castle/` has 5 castle levels. The format is in `levels/README.md`, and `cave_files.py` loads them.
- `editor.py`: the editor saves over the game's levels or into `my_caves/`. `cave_solver.py` is the robot that checks a cave can be beaten.
- `how_it_works/`: the guide for the player.
- `web/`: the browser build.
- `tests/`: the test suite.
