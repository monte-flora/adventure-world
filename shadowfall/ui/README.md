# ui/ (B5): title, HUD, text box, pause

| File | What | How other areas use it |
|---|---|---|
| `title.tscn` | logo, Continue / New journey / Quit; applies saved settings once per run | `Scenes.goto("title")` |
| `hud.tscn` | hearts, Light Stones, gold; reads `Game` every frame; layer 50 (above light, never darkened) | `add_child(preload("res://ui/hud.tscn").instantiate())` in a play screen |
| `dialogue_box.tscn` | 3-line text box, pages long text, `*word*` = important word (light0) | `box.say("Warden", "...")`, `await box.finished` |
| `pause.tscn` | JOURNEY (resume, save+quit, quest log) · MAP · SIGILS · SOUND · CONTROLS (remap) | opened by `Scenes.pause()` |
| `style.gd` | `UiStyle`: palette, fonts, frame, `name_of(table, id)` from `rules/names.gd` | |
| `settings.gd` | `UiSettings`: 3 volumes (10% steps), remapped keys, `user://shadowfall_settings.cfg` | |
| `fonts/` | copies of `assets/fonts/` (the web export can't reach outside `res://`); a test checks they match | |

Data the pause screen reads until `rules/` has it: `rules/quests.gd` static `log_entries()` → `[{title, text, done}]`,
`rules/sigils.gd` static `slots()` / `equipped()`; else `Game.flags` `quests` `{id: "active"|"done"}`, `sigils` `[ids]`,
`map_screen` `[x, y]`, `map_seen` `[[x, y], ...]`. Names: `Names.STONE`, and `Names.QUEST` / `Names.SIGIL` when B4 adds them.
