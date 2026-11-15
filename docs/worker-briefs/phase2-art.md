Task: NEW ART FOR THE PHASE 2 PEOPLE AND THE SHADOW KING for Adventure World (monte-flora/adventure-world), a pygame pixel-art game for a kid. PR into `phase-2`.

Inspiration from the user (look at both):
- `<attachments>`/art/npc-inspiration.jpg : 5 townsfolk (merchant: old woman with a huge rolled-up backpack and a cane; blacksmith: big bearded man, apron, hammer; mage: tall hat, long white beard, staff with a green gem; hunter: green hood and cape, bow and quiver; farmer: straw hat, pitchfork). Chunky outlines, 3-4 shades per color, soft drop shadow, readable faces, strong silhouettes.
- `<attachments>`/art/shadow-king-inspiration.jpg : the Shadow King as a dark armored knight, spiked crown, faceless dark helm with glowing purple eyes, glowing purple gems on the chest and belt, a tattered purple cape, a jagged sword, purple smoke and a glow behind him.
Use them as inspiration only: draw your own original art in the game's own way, don't trace or import those images.

How art works today: sprites.py holds every picture as rows of letters (one letter = one palette color), and game.py make_sprite(art, scale) turns it into a surface. Map tiles are 64 px; people are 16x16 at scale 4 (sprites.PEOPLE_ART, drawn by phase2/draw_people.py, which also draws the dialogue portrait). The Shadow King is sprites.SHADOW_KING (24 wide) at KING_SCALE 6 in the throne fight (throne.py, game.py ~lines 1023, 1094, 3712), plus "king_big" at scale 8 on story cards.

Build:
1. PEOPLE: redraw every Phase 2 look (farmer, shopkeeper/merchant, blacksmith, guide, wizard/mage, kid, cat, villager, fisher, plus any looks 3a/3b added, and add a hunter look) with the inspiration's qualities at map size: a dark outline, 3-4 shades per color, a light from top-left, clear faces, a prop that says the job (backpack, hammer, staff, bow, pitchfork). Keep them readable at 16x16 x4 on a 64 px tile, matching the world's pixel size. ALSO make a bigger PORTRAIT for each look (about 32x32 or 40x40, head and shoulders, more detail and expression) for the dialogue box.
2. SHADOW KING (Phase 2 only): a new, more detailed sprite (about 36x36 to 40x40, drawn at scale 4 so it's about the same size on screen as now but with much more detail, and the same pixel size as the Hero), with the angry variant (as ANGRY_SHADOW_KING does), a glowing aura (game.py has make_soft_glow) and glowing eyes and gems; a matching big version for the Phase 2 story/ending cards. Keep his hitbox and fight rules exactly as they are (art only).
3. A preview sheet: a script (e.g. tools/art_preview.py) that renders old vs new side by side, plus one EXPERIMENT for the user to judge: two of the people drawn at 32x32 at scale 2 on a map tile next to the 16x16 world, so they can see how mixed pixel sizes look. Save the PNGs in docs/art-refresh/ and list them in the PR body.

Rules:
- Classic must look and play exactly as before: put the new art in a new file (e.g. phase2/art.py or sprites_phase2.py) and use it only when the game is Phase 2. Don't change existing sprites in sprites.py. Every existing test passes unchanged.
- COORDINATION: another worker (branch monte-flora/phase2-hud, PR coming) is redesigning the Phase 2 side panel and message box, and may restyle the dialogue box. Don't edit the panel, the message log or the dialogue box layout. For portraits, expose a function like portrait(look) -> surface, and only change the one line in phase2/draw_people.py that picks the portrait picture. Keep game.py edits to the Shadow King picture lines, in Phase-2-only branches. Before pushing: `git fetch origin && git rebase origin/phase-2`, keep both sides in conflicts, rerun all tests.
- Tests: every look has a map sprite and a portrait of the right size, only palette letters that exist, the new king art keeps the same hitbox, Classic still uses the old art.

TODO.md: in the Phase 2 section, before the Stage 4 line, add "- [x] 2026-11-13 **New art for people and the Shadow King (Phase 2):** <one-line summary>" (asked 2026-11-13).

Setup: you are in a fresh Orca worktree. Run `git fetch origin && git checkout -b monte-flora/phase2-art origin/phase-2`. Read AGENTS.md, sprites.py (the PEOPLE section and SHADOW_KING), game.py make_sprite, phase2/draw_people.py, throne.py.

Run all tests: `<main checkout>/.pixi/envs/default/bin/python -m pytest -q -n auto tests` (pixi run doesn't work in worktrees). All must pass. Start the game for a few seconds to be sure it doesn't crash. Don't touch the main checkout (it has the user's uncommitted work).

Commit (message ends with `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`), push, open a PR with base `phase-2` (NEVER main; never phase-2 -> main). PR body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Don't merge by hand; auto-merge does it when green. If it sits green but open, re-run its PR `Tests` run.

Done = PR open, full suite passing, preview PNGs in docs/art-refresh/. Report with worker_done: PR number, test count, the preview paths, and your honest view of the 32x32-at-scale-2 experiment. A failing test you can't fix = the Task failed; report it and don't push.
