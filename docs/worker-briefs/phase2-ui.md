Task: REDESIGN THE PHASE 2 SIDE PANEL AND BOTTOM MESSAGE BOX for Adventure World (monte-flora/adventure-world), a pygame pixel-art game for a kid. PR into `phase-2`.

The user (the kid's parent) wants you to BE CREATIVE. Their words: re-design the right-hand side and the bottom. Make a more interactive, more intuitive menu. Make the dialogue/message box easier to read and more engaging: "I honestly forget it's there most of the time." But do NOT make it overwhelming: this is for a young kid.

Screenshot of today's Phase 2 screen: `<attachments>`/ui/current-phase2-screen.png (read it). What it shows:
- Right panel: name, hearts x lives, level, health bar, XP bar, "Powers", a PACK list of 9 rows (swords pips, pickaxe, food, wood, boat, bow, diamonds, armor) mostly saying "none", QUESTS (two checkboxes with counts), "Portal: closed", a place hint ("HOME MEADOW: HOUSE  SPACE rest and heal"), then a CONTROLS grid of 12 keys at the bottom. It's a wall of small text, much of it "none".
- Bottom: a dark strip with 2 lines of yellow log text on the left (easy to miss) and a minimap on the right.
- Top-left: a gold counter.
- Bug to fix while you're there: the welcome line says "Defeat 5 monsters and mine 3 diamonds, then reach the Portal" and the panel lists the Classic quest "Defeat 5 monsters", but Phase 2's real goal is the 7 Light Stones (phase2/main_quest.py, data/main_quest.json). Also "Esc quit" will change: a pause menu (P/Esc) is being built right now by another worker.

Ideas you may use or beat (your call, keep it calm and readable):
- Show only what matters now: hide "none" items, group the pack as icons with numbers (an inventory bar), show controls contextually (the 2-3 keys that matter here, e.g. "SPACE talk" next to a person) and put the full list behind H.
- A clear "Next:" goal card from the quest log (Light Stones as 7 little gems that fill in), with an arrow or a pin on the minimap toward the goal.
- Messages: bigger, friendlier text with icons, newest one highlighted then fading, a short pop-up "toast" for loot/level-ups, maybe a speech-bubble or portrait for people talking; a way to scroll back (e.g. L for the log).
- Mouse hover/click on panel items for a tooltip (what a thing does, how to get it).
- A bigger minimap you can open (M is sound today; pick free keys, check game.py).
Keep the pixel-art look (sprites.py style, existing fonts/colors in settings.py). Readable at the default window size and in the web build.

Scope and rules:
- Phase 2 only. Classic must look and play exactly as before; every existing test passes unchanged. Put the new UI in new files (e.g. phase2/hud.py, phase2/draw_hud.py) and hook it from game.py with small Phase-2-only branches.
- COORDINATION: another worker (branch monte-flora/phase2-pause-save, PR coming) is editing game.py's key handling, title screen and main loop right now. Build your UI in your own new files first. Keep your game.py hooks to the drawing calls (draw_panel / message log / minimap) and as small as possible. Before you push, `git fetch origin` and rebase on origin/phase-2; if the pause-save PR has merged, keep both sides in conflicts and make sure P/Esc pause still works and shows in your contextual controls. If it hasn't merged yet when you're ready, ask the coordinator (orchestration ask) before pushing.
- Don't change levels/, monster/fight rules, or quest logic (reading quest state is fine).

Evidence: take screenshots of the new panel and bottom in a few situations (new game in Home Meadow; next to a person; with lots of items mid-game; a loot message/level-up; in a cave if you touched cave UI) with the window driver (or SDL_VIDEODRIVER=dummy + pygame.image.save of the screen surface), save them under docs/ui-redesign/ in the PR, and list them in the PR body. Add tests for the new HUD logic (what shows when, the hidden empty items, the Next goal text, message timing) without a window.

TODO.md: in the Phase 2 section, before the Stage 4 line, add "- [x] 2026-11-13 **New side panel and message box (Phase 2):** <one-line summary>" (asked 2026-11-13).

Run all tests: `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests` (pixi run doesn't work in worktrees). All must pass. Start the game for a few seconds to be sure it doesn't crash. Don't touch the main checkout (it has the user's uncommitted work).

Commit (message ends with `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`), push, open a PR with base `phase-2` (NEVER main; never phase-2 -> main). PR body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Don't merge by hand; auto-merge does it when green. If it sits green but open, re-run its PR `Tests` run (`gh run rerun <id>`).

Done = PR open, full suite passing locally, screenshots in the PR. Report with worker_done: PR number, test count, the screenshot paths, and a short list of what changed and why. A failing test you can't fix = the Task failed; report it and don't push.
