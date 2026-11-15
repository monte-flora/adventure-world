Task: Phase 2 stage 3b, SIDE QUESTS, for Adventure World (monte-flora/adventure-world), a pygame game for a kid. PR into `phase-2`.

Setup: you are in a fresh Orca worktree. Run `git fetch origin && git checkout -b monte-flora/phase2-3b-side-quests origin/phase-2`. Read AGENTS.md, PHASE2.md, TODO.md (Phase 2 section), phase2/people.py, phase2/dialogue.py, phase2/quests.py, phase2/shop.py, phase2/waystones.py (lookouts, hidden chests), phase2/monsters.py, phase2/data/*.json, levels/world/*.txt (6 villages: Meadowbrook, Oakhollow, Lakeside, Snowcap, Sandwell, Bogwater).

Build 10-15 side quests, about 2 per village, fun and short (5-10 minutes each) for a kid: fetch and craft (wood, food, a forged sword), find something lost in another land, beat N monsters of a land's kind, climb a lookout and dig up its treasure, deliver a letter between villages, escort or "follow the clue" chains, one or two with a dialogue choice that changes the reward. Rewards: gold, XP, food, arrows, a Great sword, armor, an extra life; at least two point to a lookout treasure. Kind, funny townsfolk dialogue.

Ownership (another worker, 3a, builds the main quest at the same time):
- You OWN: phase2/data/side_quests.json (all side quests), phase2/data/people_side.json (any new quest-giver people), and the small loader code so quests.py and people.py also read those files (additive changes only), new step kinds you need for side quests (put them in a new phase2/side_steps.py if you can, registered from quests.py with a small hook), and their tests.
- 3a OWNS phase2/quests.py's main structure, phase2/data/quests.json, main_quest.json, people.json and story. Don't edit people.json or quests.json; the 2 sample quests there stay. Keep quests.py/people.py edits to a few lines so the merge with 3a is easy. Don't write main-quest content.
- Don't change levels/world/* tiles. Don't change monster or fight code beyond reading counts.
- Classic must play exactly as before; every existing test passes unchanged.

Tests: every side quest can go start -> each step -> finish -> reward in a test game; every giver stands on a walkable, reachable tile away from monsters (reuse the existing placement test); quests show in the quest log; save/load mid-quest keeps progress; a choice quest gives different rewards per choice.

TODO.md: 3a is splitting the Stage 3 line into 3a and 3b. If you finish first, replace "- [ ] **Stage 3, quests and story:** ..." with "- [ ] **Stage 3a, the main quest.**" and "- [x] 2026-11-13 **Stage 3b, side quests:** <one-line summary>". If 3a already merged, just mark the 3b line `[x] 2026-11-13`. In a TODO conflict keep both sides.

Before you push, `git fetch origin` and rebase on origin/phase-2 in case 3a merged; resolve conflicts keeping both sides, and rerun all tests.

Run all tests: `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests` (pixi run doesn't work in worktrees). All must pass. Don't touch the main checkout (it has the user's uncommitted work).

Commit (message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`), push, open a PR with base `phase-2` (NEVER main; never phase-2 -> main). PR body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Don't merge by hand; auto-merge does it when green. If it sits green but open, re-run its PR `Tests` run (`gh run rerun <id>`).

Done = PR open, full suite passing locally. Report with worker_done: PR number, test count, a table of the quests (village, giver, what to do, reward). A failing test you can't fix = the Task failed; report it and don't push.
