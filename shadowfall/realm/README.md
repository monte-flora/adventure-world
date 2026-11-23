# shadowfall/realm: the realm's painted art (G1)

Painted (Gemini) art for the overworld, outside `art/` because it is not limited to the Shadowfall 32
palette (`art/art_check.gd` checks only `art/`).

| Folder | What |
|---|---|
| `gemini/` | the prompt pack: `STYLE.txt`, `prompts/*.txt`, `assets.json` (sizes, footprints, lights), `README.txt` (the steps), `in/` (your Gemini pictures), `placeholder/` (striped stand-ins). Has a `.gdignore`: Godot never imports these big pictures. |
| `props/` | `<name>.png` + `<name>.json`, made by `pixi run import-art` (`tools/art_import.gd`) |
| `ground/` | `<name>.png`, 256 × 256 seamless ground textures |

Prop JSON: `size` [w, h]; `foot` [x, y, w, h] the rect you bump into (empty = walk through); `anchor` [x, y]
the point that sits on the map spot (bottom middle of the foot); `base` the y it sorts by; `lights`
[[x, y, radius]]; `front` rows from the top always drawn over the hero; `placeholder`; `keep` (true = the
next import keeps your hand edits). All in the PNG's pixels (1 = one game pixel, 32 = a square).

Placing props (`prop:` lines): "Props on the realm" in `levels/README.md`.

In the game (`overworld/realm_props.gd`): every prop sprite uses `GloomLight.painted_material` (a smooth
gloom grade, `light/painted_gloom.gdshaderinc`), and so does the painted ground (its shader includes it;
the overworld calls `light.track(ground.material)`). Each `lights` point is a `LanternLight` of the prop's
kind (`RealmProps.LIGHTS`, default WINDOW):

| Kind | Props | Energy | Colour | Flicker (amount, speed) |
|---|---|---|---|---|
| WINDOW | cottage_a, cottage_b, tavern | 0.55 | `#f7c64a` | 0.08, 3 |
| LAMP | lamppost | 0.8 | `#ffc56a` | 0.1, 5 |
| FORGE | smithy | 0.9 | `#f0784a` | 0.2, 7 |
| FIRE | campfire | 1.0 | `#f0784a` | 0.3, 10 |

Screenshot a land at a gloom stage: `godot --path shadowfall --audio-driver Dummy -- --scene=overworld --shot=/abs/x.png --gloom=3 [--cell=c,r]`.
