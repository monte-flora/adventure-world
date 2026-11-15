Task: Phase 2 stage 3a, THE MAIN QUEST AND STORY, for Adventure World (monte-flora/adventure-world), a pygame game for a kid. PR into `phase-2`.

Setup: you are in a fresh Orca worktree. Run `git fetch origin && git checkout -b monte-flora/phase2-3a-main-quest origin/phase-2`. Read AGENTS.md, PHASE2.md, TODO.md (Phase 2 section), phase2/__init__.py, phase2/world.py, phase2/waystones.py (gates), phase2/people.py, phase2/dialogue.py, phase2/quests.py, phase2/data/*.json, levels/world/*.txt, story.py, and how Classic reaches Nightfall Hollow, the castle and the Shadow King (game.py, castle.py, throne.py).

Build a main quest that carries the Hero across the lands to the Shadow King, about 1.5-2.5 hours of play with the side quests:
- A story opening in Home Meadow (the guide Rosa or a new elder) that says what's wrong and what to do. Story cards in the classic story.py style.
- One relic or token per land (Home Meadow, Whispering Woods, Great Lake, Frost Peaks, Sunscorch Desert, Murk Swamp, Old Ruins; Portal Island is the end). Each comes from that land's village and a task there: a Mine/cave to beat, a monster to defeat, a person to help, a lookout to climb. Use what's already in the game; no new cave files needed (cave reuse is fine).
- The order follows the gates and level gates 2a made (e.g. the Desert Gate at level 3), so levels rise naturally. A clear "where to go next" step in the quest log (Q) and from the guide.
- With all relics, the Portal opens to Nightfall Hollow, then the classic castle and Shadow King (reuse them). A short ending scene for Phase 2 after the Shadow King, with the save kept so you can keep exploring.
- The main quest is data where possible: put it in phase2/data/main_quest.json (or quests.json entries with "main": true); story text in data too.

Ownership (another worker, 3b, builds side quests at the same time):
- You OWN: phase2/quests.py (engine changes, including any new step kinds you need), a new phase2/main_quest.py if useful, phase2/data/quests.json, phase2/data/main_quest.json, story cards for Phase 2, Portal/ending hooks in phase2/world.py, main-quest dialogue on existing people in phase2/data/people.json.
- 3b OWNS phase2/data/side_quests.json and phase2/data/people_side.json and the code that loads them (small additions to quests.py/people.py). Keep your quests.py changes additive so the merge is easy. Don't write side quests.
- Don't change levels/world/* map tiles except to add a needed marker; tell the coordinator if you must.
- Classic must play exactly as before; every existing test passes unchanged.

Tests: each relic step can be done (start -> finish -> reward), the order matches the gates, the Portal stays shut without all relics and opens with them, save/load keeps quest progress mid-quest, the ending triggers after the Shadow King in Phase 2 only.

TODO.md: replace the line "- [ ] **Stage 3, quests and story:** ..." with two lines: "- [x] 2026-11-13 **Stage 3a, the main quest:** <one-line summary>" and "- [ ] **Stage 3b, side quests:** 10-15 side quests, about 2 per village."

Run all tests: `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests` (pixi run doesn't work in worktrees). All must pass. Don't touch the main checkout (it has the user's uncommitted work).

Commit (message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`), push, open a PR with base `phase-2` (NEVER main; never phase-2 -> main). PR body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Don't merge by hand; auto-merge does it when green. If it sits green but open, re-run its PR `Tests` run (`gh run rerun <id>`).

Done = PR open, full suite passing locally. Report with worker_done: PR number, test count, the relic list in order with levels, and anything 3b should know (step kinds you added, how to give items). A failing test you can't fix = the Task failed; report it and don't push.
