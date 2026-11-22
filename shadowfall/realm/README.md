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
