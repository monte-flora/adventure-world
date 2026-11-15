Task: Phase 2 PAUSE MENU and SAVE SLOTS for Adventure World (monte-flora/adventure-world), a pygame game for a kid. PR into `phase-2`.

Setup: you are in a fresh Orca worktree. Run `git fetch origin && git checkout -b monte-flora/phase2-pause-save origin/phase-2`. Read AGENTS.md, PHASE2.md, TODO.md (Phase 2 section), phase2/save.py, phase2/world.py (autosave), phase2/__init__.py, and in game.py: the title screen (modes, "continue", new_game, continue_game), on_map/on_cave/on_battle key handling (ESC today quits at once), the main loop and how dt/time drives monsters, caves, fights, Nightfall and the day/night clock.

Today Phase 2 saves by itself (into a house or Mine, and on quit) to one file, and the title screen has "Continue". The user wants a real save feature and a pause before we build a robot playtest.

Build, for Phase 2 only (Classic must play exactly as before; every existing test passes unchanged):
1. PAUSE: P or ESC on the map, in a cave, in the castle or Nightfall, or in a map fight opens a pause menu over a dimmed, frozen game. Nothing moves or ticks while it's open: monsters, the day/night clock, cave timers, lava/stalactites, fight markers, music can keep playing quietly. Menu (UP/DOWN + ENTER, mouse, ESC/P closes): Resume; Save game; Save and go to the title; Quit (asks "Save first?" Yes / No / Back). Show the current land, level, Light Stones found and play time on it. While a dialogue box, shop, forge or a tip bubble is open, ESC keeps doing what it does there (closes it); P still pauses.
2. SAVE SLOTS: 3 slots. On the title screen, "Continue" becomes "Load" (only if any slot has a save) and opens a slot list: each slot shows the name, land, level, Light Stones (main quest progress), play time and date saved; an empty slot says "Empty". "Phase 2" (new game) asks which slot to use; picking a used one asks "Start over in this slot?" Delete a slot from the list (D, then confirm).
3. "Save game" writes the current slot and shows "Game saved!". Autosave keeps working, into the current slot. In a cave or the castle, save.py doesn't save the cave you're in: saving there puts you back on the map at that Mine when you load, so the menu says "Saved. You'll start outside this Mine." (do not try to save cave state).
4. Play time: count it (not while paused) and save it.
5. Old save: if ~/.adventure/phase2_save.json (or the browser's old key) exists, it becomes slot 1 once, without losing it.
6. Web build: slots go in the browser's localStorage the way save.py already does (one key per slot). It must still build (`build-web` check).
7. Help screen (H) and how_it_works/ guide: mention P to pause and the save slots. Add a tutorial tip (tutorial.py TIPS) the first time Phase 2 starts: "Press P to pause and save."

Tests (ADVENTURE_SAVE_FILE or a temp dir, never the real home folder): pause freezes monsters, clock and play time; resume continues; save/load round-trip per slot, 3 slots independent; delete; old save migrates to slot 1; saving in a cave loads at the Mine; ESC in Classic still does what it did; the pause menu choices (including Quit -> Save first?).

Owns: phase2/save.py, a new phase2/pause.py (menu logic + drawing), the small hooks in game.py (keys, title screen, main loop freeze), phase2/world.py if needed, tutorial.py TIPS, help text, how_it_works/, tests. Keep game.py changes small and in Phase-2-only branches.

TODO.md: in the Phase 2 section, before the Stage 4 line, add "- [x] 2026-11-13 **Pause and save slots:** <one-line summary>" (asked 2026-11-13).

Run all tests: `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests` (pixi run doesn't work in worktrees). All must pass. Also start the game once for a few seconds to be sure it doesn't crash (`SDL_VIDEODRIVER=dummy` is fine). Don't touch the main checkout (it has the user's uncommitted work).

Commit (message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`), push, open a PR with base `phase-2` (NEVER main; never phase-2 -> main). PR body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Don't merge by hand; auto-merge does it when green. If it sits green but open, re-run its PR `Tests` run (`gh run rerun <id>`).

Done = PR open, full suite passing locally. Report with worker_done: PR number, test count, the keys and menus as the player sees them. A failing test you can't fix = the Task failed; report it and don't push.
