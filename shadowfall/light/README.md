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
painting.material = light.painted_material      # painted (Gemini) art: a smooth grade, no banding
light.track(my_shader_material)                 # keeps another shader's `stage` uniform in step
```
Put the HUD on a `CanvasLayer` with `layer >= GloomLight.HUD_LAYER` (100); the dark draws on layer 50, so the HUD is never darkened.

| What | How |
|---|---|
| Gloom stage | `Game.gloom_stage()` (0..3) each frame → `stage` uniform of `palette_swap.gdshader` |
| Palette swap | `GloomLut`: Shadowfall 32 × 4 stages (32×4 LUT texture), same rule as `spikes/art/sf_art.py`. Off-palette colours move by their nearest colour's step |
| Painted gloom | `painted_material` (`painted_gloom.gdshader`, `#include "painted_gloom.gdshaderinc"`): per stage desaturate, shift violet, darken by the palette swap's average step. For art off the Shadowfall 32 (realm props, painted ground, cave paintings), where the swap bands. CPU mirror for tests: `PaintedGloom.grade(color, stage)` |
| `track(mat)` | a shader that grades itself (e.g. the realm's painted ground includes `painted_gloom.gdshaderinc`) gets its `stage` uniform set with the others in `refresh()` |
| Darkness | `darkness.gdshader` on a full-screen rect: `ink0` at 75% (dark place) or 50% (stage 3), cut by up to 16 `LightPool`s in 3 hard rings (45/72/100% → 0, ⅓, ⅔ of the dark), merged by the lowest dark |
| Light Stone | `Game.stone_taken` → a light burst from the lantern clears the dark for ~1 s, plus a `light1` flash |
| Tests | `light/tests/test_light.gd`; `test_render_shaders_on_the_gpu` reads real pixels when run without `--headless` |

## The realm at dusk (Wave E1)
The overworld uses Godot's own 2D lights; caves and the boss keep `GloomLight`'s darkness.
```gdscript
var dusk := RealmLight.new(); add_child(dusk)             # CanvasModulate: TINT[Game.gloom_stage()]
RealmLight.glow(node, Vector2(0, -8), 72.0, 0.8)          # warm PointLight2D + Flicker
var f := Flicker.new(); my_point_light.add_child(f)       # firelight on any PointLight2D (E2: hero, people)
```
| What | How |
|---|---|
| Tint | `CanvasModulate` on layer 0: stage 0 `#8a86b8` (dusk) → 1 `#6c6899` → 2 `#4b4775` → 3 `#2e2c4d`. The HUD (layer ≥ 100) is never tinted |
| Lights | `PointLight2D`, add blend, one shared 128-px radial `GradientTexture2D`, gold `#ffc56a`. Work in the Compatibility renderer and the web export |
| Flicker | `FastNoiseLite` 1-D noise on `energy` (±22 %) and `texture_scale` (±4 %), its own seed per light |
| Stage 3 | the overworld sets `GloomLight.tinted = true`: no ink overlay there, the tint does it; the palette swap still runs |

Screenshot a gloom stage (silent window, not headless): `godot --path shadowfall --audio-driver Dummy -- --scene=cave --file=caves/02_the_vine_garden.txt --shot=/abs/x.png --gloom=3` (`--scene=overworld` works too).
