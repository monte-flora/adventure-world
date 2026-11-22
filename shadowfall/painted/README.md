# P1 prototype: painted Emberhold (one screen)

A test of the idea "the background is one painted picture and the characters walk on it", to compare
with the tile map. Not the real map system; nothing else uses this folder.

- Play: `pixi run painted` (silent), or `godot --audio-driver Dummy --path shadowfall res://painted/painted.tscn`.
  Arrows/WASD walk, G talks to the person in front. `-- --shot=out.png --at=x,y` saves a screenshot and quits.
- `emberwick.json`: everything hand-made for the screen: the painted people to erase, collision rects and
  polygons, the foreground pieces (canopies, roofs, cliff top, cave arch, each with the y it sorts by), the
  6 people (from `rules/data/people.json`), the lights and the cave exit.
- `tools/clean_plate.py` (Pillow + numpy) remakes `emberwick_clean.png` and `emberwick_front.png` from the
  painting in `docs/teen/art/ref/`: the smooth light is diffused into each hole and the detail is cloned in
  8-px blocks from the best-matching nearby ground (never from houses, fences or trees).
- `painted_hero.gd` is `overworld/hero_top.gd` with pixel collision against the shapes; `flicker.gd` and
  the CanvasModulate are a stand-in for E1's dusk lights.
