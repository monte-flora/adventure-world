# Shadowfall (Godot 4.7 rebuild)

The teen rebuild of Adventure World's Shadowfall, in Godot 4.7.2 (2D, Compatibility renderer, GDScript).
The pygame game in the repo root stays playable and on itch.io; this build ships as a separate web build for now.
Specs: `docs/teen/{engine,gameplay,levels,art,audio}/README.md`. Task list: [WAVE_B.md](WAVE_B.md).

## Run, test, export
Install Godot **4.7.2** (`brew install --cask godot` or godotengine.org; the pin is in `GODOT_VERSION`) so `godot` is on PATH.

| What | Command |
|---|---|
| Play | `pixi run shadowfall` (or `godot --path shadowfall`) |
| Jump to a screen | `godot --path shadowfall -- --scene=cave --file=caves/03_blue_lvl_1.txt` |
| Open the editor | `godot -e --path shadowfall` |
| Tests (headless) + boot check | `pixi run godot-test` (`sh shadowfall/tools/run_tests.sh --only=caves` for one area) |
| Web build → `shadowfall/build/web/` | `pixi run godot-web` (needs the 4.7.2 web export templates) |

CI: `godot-test` (in the Tests workflow) and `godot-web` (in the Web version workflow) run on every PR; auto-merge waits for both. The Godot build is **not** uploaded to itch.io.

## How it fits together
- **Settings:** 960×540 view, `canvas_items` stretch with integer scaling (smooth sub-pixel camera), nearest filter, 60 Hz physics with interpolation, `max_fps` 60, 32-px tiles (`LevelFile.TILE`).
- **Autoloads:** `Game` (`core/game.gd`: Light Stones, 7 abilities, gloom, hearts, gold, flags, save/load to `user://`), `Controls` (`core/controls.gd`: the input map, keyboard + gamepad, **R = attack**), `Scenes` (`core/scenes.gd`: `Scenes.goto("cave", {"file": ...})`, ESC pause), `Audio` (`audio/audio.gd`).
- **Screens:** `boot` → `title` → `overworld` ⇄ `cave`, `boss`; `ui/pause.tscn` sits on top. Each lives in its owner's folder.
- **Levels:** read at run time from the repo's `levels/` (the kid's text files, shared with pygame) by `LevelFile` (`core/level_file.gd`), which keeps every `key: value` header (new ones like `stone:`, `land:`, `needs:`, `dark:` included). An export copies `levels/` into `res://levels` and removes it after; never commit `shadowfall/levels/`.
- **Tests:** any `<area>/tests/test_*.gd` that `extends TestCase` (`tests/case.gd`); each `func test_*()` runs with a fresh `Game`, and `Scenes.goto` opens screens inside the test. Cut on purpose: XP, lives, food, sword wear.

## Folder ownership
One worker per folder; only touch your own. Need something in someone else's folder (a new autoload, a `Game` field, a screen in `Scenes.SCENES`)? Ask the coordinator.

| Folder | Owner | What's in it |
|---|---|---|
| `core/`, `tests/`, `project.godot`, `export_presets.cfg`, `GODOT_VERSION` | B0 (then B9) | boot, `Game`, `Controls`, `Scenes`, `Paths`, `LevelFile`, the test runner |
| `overworld/` | B1 | the top-down map from `levels/world/*.txt`, top-down hero, camera, waystones, map monsters, Nightfall mirror |
| `caves/` | B2 | the cave scene, tiles for every letter, side-view hero, cave monsters, hazards, checkpoints |
| `light/` | B3 | gloom stages, palette-swap shader, lantern and crystal lights |
| `rules/` | B4 | names (`rules/names.gd`), stats, sigils, forge, quests, shop, dialogue data |
| `ui/` | B5 | title, pause, HUD, dialogue box, menus, map screen, remapping |
| `audio/` | B6 | the `Audio` autoload, buses, music stems, SFX |
| `tools/` (+ `editor.py`, `cave_solver.py`, `cave_files.py` in the root) | B7 | the kid's editor and the cave robot for the new letters; `run_tests.sh`/`export_web.sh` stay B0's |
| `boss/` | B8 | castle levels from `levels/castle/`, the Shadow King |
| `art/` | B-Art | sprite sheets, tilesets, palette, pixel font |
| `../levels/` | level workers (B-L*) | the level text files; the pygame tests still run the robot on them |
