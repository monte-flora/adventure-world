# G2 handoff (2026-11-23)

## Done
- PR 1 (#68): painted gloom grade on realm props, painted ground, cave paintings; per-prop light kinds.
- PR 2: `--gloom=0..3` on the overworld `--shot` and a new cave `--shot` (cave.gd `_shot`); gloom 0/3 shots of
  Emberhold and the Vine Garden checked by eye (props/ground/painting darken smoothly, no banding).
  `prop:` docs moved to levels/README.md ("Props on the realm", kid-friendly); light/README.md has
  painted_material / track; shadowfall/realm/README.md has the light kinds table.

## Seen, not changed
- Stage 3 Emberhold: lamppost heads read grey (their LanternLight glow is faint at that tint); the painted cave torch greys too.
- tools/realm_editor.py docstring still says the format is in levels/realm/README.md (now a pointer).
