Task: Phase 3, the first 3D prototype of Adventure World in Godot (monte-flora/adventure-world). Work on a branch off `origin/phase-3` and open your PR with base `phase-3` (NOT main).

First read AGENTS.md, HANDOFF.md and PHASE3.md (the look, the prototype scope and the rules). Follow AGENTS.md (decide, don't grill; be concise; times in US Eastern 12-hour).

Godot 4.7.2 is installed: `godot` (/opt/homebrew/bin/godot). Build the "First prototype" in PHASE3.md as a Godot project in `godot/`:
- Cartoony, chunky low-poly look in the spirit of late-90s 3D platformers, but ORIGINAL: no characters, levels, art, music or names from any existing game. The Hero is a young knight; monsters are this game's own (Zombie etc.). Art made from Godot primitives and flat/vertex-colored materials in code or .tscn; no downloaded assets.
- Hero: run with momentum, jump, a double or long jump, sword swing; orbit/follow camera. Keyboard (arrows/WASD, SPACE jump, A or J attack, Q/E camera) and mouse.
- Home Meadow hub: house, trees, pond, hills, floating platforms, diamonds to collect, a Mine entrance.
- One Zombie: patrols, chases within range, 3 sword hits or a stomp.
- Mine -> tiny cave: lava jumps, a lever that opens a gate, a diamond at the end, back out to the meadow.
- HUD: hearts and diamonds. Falling in lava or off the world costs a heart and respawns you.
- Simple placeholder sounds are optional (generated, not downloaded).

Also:
- `godot/README.md`: how to open and run it; a `game3d` task in pixi.toml (`godot --path godot`).
- Tests: `godot --headless --path godot --quit` loads with no script errors; a few headless GDScript logic tests (e.g. a `godot/tests/` runner script: collecting a diamond, the zombie taking 3 hits, the lever opening the gate) runnable from the command line; and a pytest wrapper `tests/test_godot_prototype.py` that runs them and SKIPS when `godot` isn't installed (so GitHub CI stays green). The existing pygame suite must still pass: `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests`.
- Look at your work: run it windowed and save a few screenshots (e.g. a debug flag that renders and saves `godot/screenshots/*.png` then quits), view them, and iterate on the look until it reads clearly as cartoony and fun. Commit 2–3 screenshots.
- TODO.md: mark the "First 3D prototype" line `[x] 2026-11-13` in your PR.

Scope: only `godot/`, `tests/test_godot_prototype.py`, pixi.toml (one task), TODO.md. Other workers are editing the pygame game in other worktrees.

Done = commit, push, open a PR into `phase-3` (body ends with the Claude Code line, include the screenshots; commits end with the Co-Authored-By line). Auto-merge merges it into phase-3 once green. Report: PR number, test results, the controls, what feels rough, and what you'd build next. A failing test you can't fix means the Task failed: report the output.
