# Phase 2: a bigger Adventure World

Branch `phase-2`. Goal: take the foundations (caves, castle, Shadow King, art, editor, robot) and build a game that lasts **2–4 hours**. Classic stays playable: the title screen offers **Classic** or **Phase 2**.

Asked 2026-11-13. Calls made by the coordinator (change any of them in TODO.md or by asking):

## Rules for phase 2 work
- New code lives in `phase2/`. Classic code (`game.py`, `rules.py`, `caves.py`...) only gets small hooks, and **Classic must play exactly as before**: every existing test passes unchanged.
- Content is data, not code: the world map, people, dialogue and quests live in files (`levels/world/`, `phase2/data/`), so they're easy to edit.
- Every PR targets `phase-2` (not `main`) and auto-merges once green. **Never open a `phase-2` → `main` PR** unless the user asks, and then as a draft: a merge to `main` publishes to itch.io.
- Engine: pygame stays (see "Why pygame").

## The design
1. **World:** about 3–4× the classic map, in 6–7 lands (Home Meadow, Whispering Forest, the Great Lake, Frost Peaks, Sunscorch Desert, Murk Swamp, then Nightfall Hollow through the Portal). One big scrolling map, each land in its own file in `levels/world/`. Mines and their caves stay.
2. **No fog:** the whole map is visible. Landmarks become fast-travel waystones (unlock by visiting) and lookouts that point to secret treasure.
3. **People:** villages with townsfolk, a shopkeeper (spend gold), a blacksmith (the forge), a guide, quest givers. Dialogue boxes with choices; a quest log on Q.
4. **Monsters:** visible on the map, no hidden random fights. Each land has its own kinds; night brings more. They roam freely in real time, even while you stand still: they patrol near home and chase you (like cave monsters), so you can dodge them. The Hero walks smoothly too: hold a move key, and each square he crosses is one turn (`phase2/smooth.py`, `HERO_SPEED`). Touch one from behind = first strike; weak monsters flee a high-level Hero. Fights add a timing strike (like the forge marker) instead of plain A.
5. **Length:** a main quest across the lands to the Shadow King, plus 10–15 side quests; **saving and loading** so it can be played over several sittings.

## Stages (one PR or worker each)
1. **Base:** title-screen choice, `phase2/` package, world map loaded from files, no fog, save/load.
2. In parallel: **2a world map & lands**, **2b people, dialogue, shop, quest log**, **2c visible monsters & timing fights**.
3. **Quests & story** (2–3 PRs).
4. **Balance** + a robot test that plays through the main quest.

## Why pygame
The game is ~15k lines of Python, ~420 tests, a cave editor, a solver robot and a working web build (pygbag). A Godot port would rewrite all of it for features this game doesn't need. The limits on a longer game are content and code layout, which data files and the `phase2/` package fix.
