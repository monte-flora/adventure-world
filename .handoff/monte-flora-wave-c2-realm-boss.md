# Handoff: Wave C2 (realm + boss), 2026-11-22

## Done (merged into phase-2)
- #38 realm art, #41 boss art, #43 monster art fixes (ash_scarab + cave_bat redrawn, thin fangs, padded-canvas
  build() in art/src/make_monsters.py shifts each monster inside the 1-px margin: 0 clip notes),
  #44 juice (overworld/juice.gd: Juice.Shake + Juice.burst; overworld hit-stop/shake/poof/motes/red hurt edge/
  camera look-ahead; boss sparks via boss.gd _fx(); UiSettings.screen_shake saved under [access]).

## Next: task_6d102335ee18 (approved, ONE small PR into phase-2; may touch ui/pause.gd and rules/names.gd)
1. ui/pause.gd: a row for the screen-shake switch (UiSettings.screen_shake; save via UiSettings.save()).
   Look at how the SOUND tab rows work (ui/tests/test_ui.gd test_volume_steps_and_saves); add a ui test.
2. rules/names.gd: realm ids in LAND (emberhold, weepingwold, hollowcrown, drowned_mere, wintermarch,
   cinder_wastes, mirefen, shadowgate, umbral_reach: see MapMonster.OF_LAND), plus BOSS / SUNFANG /
   LIEUTENANT names (epic, original, LOTR/GoT tone, teen-safe). Use them in boss/ (boss uses fallbacks
   now: Castle.display("LIEUTENANT", id, ...), lieutenant ids in boss.gd ECHO_SHEET).
3. Redraw frost_matriarch in art/src/make_monsters.py (96 cell; only clip-fixed so far; looks like a blue
   blob + stick legs). Run: `cd shadowfall/art && SDL_VIDEODRIVER=dummy <py> src/make_monsters.py frost_matriarch`
   (py = /Users/montgomeryflora/noah-adventure/.pixi/envs/default/bin/python); must print no notes.
   Zoom contact sheet: a 4x pygame upscale of sheets/monster_frost_matriarch.png (script was in old scratchpad).
- Tests: `sh shadowfall/tools/run_tests.sh` (all) and pytest `<py> -m pytest -q -n auto tests`.
- Then worker_done to the coordinator (task_6d102335ee18, dispatch ctx_56753d91423b).

## Gotchas
- A texture first load()ed inside a draw callback draws nothing. Load in _ready.
- GDScript: `var x := m.hit()` on an untyped loop var fails to parse; type it.
- Hit-stop must not skip overworld cell checks (Lost Light pickup).
