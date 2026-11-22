# Handoff: Wave E1 atmosphere (branch monte-flora/e1-lighting) — PAUSED 2026-11-22

User's call (via coordinator): merge the lighting PR, then stop; they are prototyping a painted static
background for Emberwick to compare against tiles. Task brief: Wave E1 (coordinator has it verbatim).

## Done (PR into phase-2)
- `light/realm_light.gd` (RealmLight): CanvasModulate tint per gloom stage (#8a86b8 → #6c6899 → #4b4775 → #2e2c4d),
  `RealmLight.glow()` warm PointLight2D (shared radial GradientTexture2D, add blend), `has_light()`.
- `light/flicker.gd` (Flicker): FastNoiseLite energy + scale wobble on its parent PointLight2D. For E2 (hero, people).
- `GloomLight.tinted`: overworld drops the stage-3 ink overlay (tint does it); caves unchanged.
- `overworld.gd`: `entities` Node2D (y_sort) holds objects TileMapLayer (y_sort), hero, people, monsters;
  lights on hero/people (skipped if E2's rig already has a PointLight2D), houses, lit waystones.
- Tests: `light/tests/test_realm_light.gd`, `test_dusk_lights_and_y_sort`. Web export builds; not run in a browser.
- Refs: `docs/teen/art/ref/overworld_target_{a,b_characters}.jpg`; shots `docs/teen/art/e1/`.

## Next (not started), one small PR each
1. Shadows: Shadow_Overlays TileMapLayer, runtime-drawn semi-transparent tiles offset bottom-right for trees, cliffs, houses.
2. Cliffs/paths: rocky cliff tiles (cracks, ivy) in `art/src/make_tiles.py`; path edges via TileSet terrain (match sides, 16 tiles) +
   debris/footprint overlay. Palette extension → `art/palette.json` + ArtCheck (it asserts 32 colours today).
3. Props: scattered decor (flowers, shrubs, logs, rocks), bigger y-sorted houses with CPUParticles2D chimney smoke + window glow, cave mouth vines.
4. HUD (`ui/hud*`): framed pixel panels, heart/coin icons with dark outline/drop shadow.
5. Vignette + soft bloom: CanvasLayer screen shader (Compatibility has no 2D WorldEnvironment glow).
- Check web perf of PointLight2D in a real browser (not done).
