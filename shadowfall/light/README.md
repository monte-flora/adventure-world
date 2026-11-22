# light/ (B3): the dark and the light

Rules from `docs/teen/art/README.md` (Lighting, Darkening world). Play-test: `godot --path shadowfall res://light/demo.tscn`
(arrows move the lantern, `0`–`3` set the gloom stage, `D` toggles the dark, `T` takes a Light Stone).

## Use it in a screen
```gdscript
var light := GloomLight.new()
light.dark = GloomLight.is_dark(level)          # `dark: yes` header
add_child(light)
map.material = light.world_material             # world tiles + backgrounds only, never characters
light.follow(hero)                              # the lantern, 130 px
light.add_crystal(self, pos)                    # 36 px pool (any glowing thing)
```
Put the HUD on a `CanvasLayer` with `layer >= GloomLight.HUD_LAYER` (100); the dark draws on layer 50, so the HUD is never darkened.

| What | How |
|---|---|
| Gloom stage | `Game.gloom_stage()` (0..3) each frame → `stage` uniform of `palette_swap.gdshader` |
| Palette swap | `GloomLut`: Shadowfall 32 × 4 stages (32×4 LUT texture), same rule as `spikes/art/sf_art.py`. Off-palette colours move by their nearest colour's step |
| Darkness | `darkness.gdshader` on a full-screen rect: `ink0` at 75% (dark place) or 50% (stage 3), cut by up to 16 `LightPool`s in 3 hard rings (45/72/100% → 0, ⅓, ⅔ of the dark), merged by the lowest dark |
| Light Stone | `Game.stone_taken` → a light burst from the lantern clears the dark for ~1 s, plus a `light1` flash |
| Tests | `light/tests/test_light.gd`; `test_render_shaders_on_the_gpu` reads real pixels when run without `--headless` |
