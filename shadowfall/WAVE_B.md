# Wave B: the Godot rebuild, one line per worker

Base `phase-2`, each worker in its own worktree, PR into `phase-2`. Every PR: `pixi run godot-test` and `pixi run test` pass, and the worker touches only its folder (ownership table in [README.md](README.md)). Specs: `docs/teen/<area>/README.md`. Run B1–B8 and B-Art in parallel after B0; B9 last.

| Task | Owns | Goal | Acceptance |
|---|---|---|---|
| B1 Overworld | `overworld/` | Top-down realm from `levels/world/*.txt` on the 6×5 screen grid, 8-way hero (5.5 sq/s, roll), smooth camera, waystones as lanterns, map monsters, ability gates (`Y` `O` `K`), Nightfall as the 3×3 mirror of the centre | every land loads; a test walks Hearthvale to a Mine and `Scenes.goto("cave")` fires; gates stay shut until `Game.has_ability()` |
| B2 Caves | `caves/` | Cave scene for every letter in `levels/README.md` plus `C` checkpoints; side hero tuned to gameplay §4 (3.3-tile jump, coyote 6 f, buffer 8 f, R attack, DOWN+R pogo, dash/wall jump/double jump when owned); cave monsters; hazards; exit back to the overworld | all 17 caves + secret, shadow load with no unknown letter; feel tests for jump height, short hop, coyote, pogo; touching `E` returns to the overworld |
| B3 Light | `light/` | Gloom 0–1 → 4 stages (palette-swap shader), darkness with 3-ring light pools, hero lantern 130 px, crystals, `dark: yes` caves, stone pickup effect | stage per gloom value tested; shader runs in the web export; HUD never darkened |
| B4 Rules | `rules/` | Final names (below, once the user OKs them), hearts/heart shards, Lumen heal, sigils, forge tiers, Lost Light, shop, quests, dialogue from `phase2/data/*.json` | unit tests for each system; no XP, lives, food or sword wear anywhere |
| B5 UI | `ui/` | Title, pause (quest log, map, sigils, volume, remap), HUD (hearts, stones, gold), 3-line dialogue box, pixel font from `art/` | every screen opens from a test; remap changes `InputMap`; works at 960×540 ×1/×2 |
| B6 Audio | `audio/` | `Audio` autoload: buses, base/dark stems following `Game.gloom` (`AudioStreamSynchronized`), SFX, the audio rules (code-made or CC0 + `CREDITS-audio.md`) | stems switch with gloom in a test; web export plays sound (human check) |
| B7 Editor + robot | `tools/`, `editor.py`, `cave_solver.py`, `cave_files.py`, `levels/README.md` | New letters and headers (`C`, `<` `>`, `n`, `stone:`, `land:`, `needs:`, `dark:`) in the editor and the robot; `pixi run` task to play a cave in Godot | editor keeps new headers on save; robot honours `needs:`; pygame tests pass |
| B8 Castle + boss | `boss/` | 5 castle levels from `levels/castle/`, the Shadow King's 3 phases (Blade, Eclipse, Fall), Sunfang finale | each phase reachable in a scripted test; boss beatable by a scripted player |
| B-Art | `art/` | Shadowfall 32 palette, 32-px tilesets per theme, hooded wanderer with a lantern (top-down and side sheets + JSON), monsters, Shadow King, pixel font | palette/cell-size checker script passes on every sheet; sheets load as `SpriteFrames` |
| B-L Levels | `../levels/` (per land/folder) | Redraw the lands on the 6×5 grid, 7 Light Stone caves (`levels/stone/`), `land:`/`stone:`/`needs:` headers, `C` checkpoints | `pixi run test` (robot) passes; `godot-test` loads every file |
| B9 Integration | `core/`, cross-folder wiring | Join the screens into one playthrough, balance, the playthrough robot, itch.io page for the Godot build (user sets secrets) | a robot plays boot → first stone → back to the realm in CI |

## The 7 abilities (merged list; ids in `core/game.gd`, names in `rules/names.gd`)
The gameplay and levels reports each had 7; this keeps one per Light Stone, works in both views, and drops Grapple and Frostward (their gates move to Climb and Swim). The hero has a lantern from the start; the Sun stone's ability makes it flare.

| Stone (id) | Ability id | What it opens | Proposed epic names (stone · ability) |
|---|---|---|---|
| dawn | `dash` | gaps, the roll on the map | Dawnstone · **Wraithstep** |
| leaf | `climb` | wall jump on any wall, ivy cliffs `Y`, `%` walls | Thornheart · **Ironclaw** |
| crown | `pound` | cracked rock `B`, rubble `O` | Crown of Ash · **Kingsfall** |
| tide | `swim` | open water, sail | Drowned Pearl · **Tidebinder** |
| frost | `double_jump` | high ledges, Frost peaks | Wintermark · **Stormwing** |
| sun | `flare` | pitch-dark places, shadow thorns `K` `n` | Sunforge Ember · **Dawnbrand** |
| moon | `truesight` | secret walls `F`, hidden caves | Ravenmoon · **Veilsight** |

## Proposed epic names (user picks; all original)
| Now | Proposed |
|---|---|
| Hearthvale (home) | keep **Hearthvale**, or **Emberhold** |
| Whispering Woods | **the Weepingwold** |
| Old Ruins | **Hollowcrown** |
| Great Lake | **the Drowned Mere** |
| Frost Peaks | **the Wintermarch** |
| Sunscorch Desert | **the Cinder Wastes** |
| Murk Swamp | **the Mirefen** |
| Portal Island | **the Shadowgate** |
| Nightfall Hollow | keep, or **the Umbral Reach** |
| Shadow King, Shadowfall | kept (user) |
