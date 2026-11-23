# G2 handoff (paused by user, 2026-11-22)

## Done (PR 1, this branch)
- `light/painted_gloom.gdshaderinc` (+ `.gdshader`, CPU mirror `PaintedGloom.grade`): per gloom stage desaturate, shift violet, darken (calibrated to the palette swap's average ramp step).
- `GloomLight.painted_material` + `GloomLight.track(mat)` (keeps a material's `stage` uniform in step).
- Realm: props (+ front rows) use `painted_material` (`RealmProps.shade`); painted ground shader grades itself, overworld `light.track(ground.material)`. `RealmGround.color_at(px, stage)`.
- Caves: painting uses `painted_material` instead of the banding palette swap; `dark: yes` overlay already covers it.
- Prop lights: `RealmProps.LIGHTS` kinds (WINDOW/LAMP/FORGE/FIRE: energy, colour, flicker amount/speed) as `LanternLight` (brightens as dusk deepens); all under the hero's 176 px / 1.4.
- Tests: overworld/tests/test_props.gd (2 new), caves/tests/test_cave_painting.gd (1 new + 1 updated). `--only=overworld|caves|light` green locally.

## In flight / next
- Screenshots gloom 0 and 3 of Emberhold and the Vine Garden: `.handoff/g2_shot.gd.txt` (a `-s` SceneTree script) hung; probably autoload access or Scenes.goto under `-s`. Try instead adding `--gloom=N` to overworld `_shot` (Game.gloom = N/3) and the same for a cave shot, run with `--audio-driver Dummy` (not headless).
- Item 4: move the `prop:` line docs from `levels/realm/README.md` ("Props and the painted ground") into `levels/README.md`, kid-friendly; keep `shadowfall/realm/README.md` for the art pipeline; mention lights kinds there.
- Full `pixi run godot-test` + pytest not run locally (CI runs them).
- Update `light/README.md` with painted_material / track (not done).
