Task: Phase 2, stage 1 (the base) for Adventure World (monte-flora/adventure-world). Work on a branch off `origin/phase-2`, and open your PR with base `phase-2` (NOT main).

First read AGENTS.md, HANDOFF.md, TODO.md and PHASE2.md (the design and the rules for phase 2 work). Follow AGENTS.md (decide, don't grill; be concise; times in US Eastern 12-hour).

Build stage 1 of PHASE2.md:
1. Title screen offers **Classic** or **Phase 2** (keys/mouse, like the rest of the title screen). Also a `--phase2` command-line flag (and a `pixi run game2` task) that starts Phase 2 directly.
2. A `phase2/` package. Phase 2 reuses the classic App, caves, castle, throne, art and tutorial through small hooks; the phase-2 world lives in `phase2/` (e.g. a Game subclass or a world object). Choose the cleanest seam; keep hooks in game.py/rules.py minimal.
3. The phase-2 world map loads from text files in `levels/world/` (one per land, stitched into one big scrolling map; document the format in levels/README.md). For this stage a starter map is enough: e.g. the classic map split into land files plus 1–2 new placeholder lands so the map is clearly bigger. Stage 2a will draw the real lands.
4. **No fog** in Phase 2: everything is visible (the minimap too). Classic keeps its fog.
5. **Save and load** for Phase 2: autosave on entering a house, a Mine and on quit; "Continue" on the title screen when a save exists. JSON in a user folder (respect the web build: localStorage or skip saving gracefully under emscripten).
6. Phase 2 still plays end to end with today's systems (caves, Nightfall, castle, boss) so later stages can build on it.

Constraints: Classic must play exactly as before. Every existing test passes unchanged (don't edit existing tests except to fix an import). Add tests in `tests/test_phase2_*.py`: the title choice, map loading/size, no fog, save/load round-trip, a Phase 2 game starts and runs a few hundred frames. TODO.md: mark the stage 1 line `[x] 2026-11-13` in your PR.

Tests: `pixi run test` may fail in a worktree (.pixi is a symlink); use `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests`. All tests must pass. Also check the web build still works if you can (`pixi run -e web build-web`), or at least that nothing you added breaks under emscripten.

Done = commit, push, open a PR into `phase-2` (body ends with the Claude Code line; commits end with the Co-Authored-By line). Auto-merge will merge it into phase-2 once green. Report: PR number, test count, the seam you chose (how Phase 2 plugs into game.py/rules.py), the map file format, what you assumed. A failing suite you can't fix means the Task failed: report the output.
