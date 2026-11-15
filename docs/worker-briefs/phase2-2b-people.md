Task: Phase 2 stage 2b, PEOPLE, for Adventure World (monte-flora/adventure-world).

Build PHASE2.md design point 3:
- NPCs on the phase-2 map, drawn as pixel-art people in the sprites.py style (at least 6 looks: farmer, shopkeeper, blacksmith, guide, old wizard, a kid), standing or pacing a little. Walk into one (or SPACE next to it) to talk.
- Data-driven dialogue (phase2/data/people.json or .py: name, look, place = land name + local row/col, lines). A dialogue box with a portrait, typewriter text, ENTER/SPACE to go on, choices (UP/DOWN + ENTER, or mouse). Condition/effect hooks so stage 3 can gate lines on quest state and give items, XP or gold.
- A SHOP (shopkeeper): buy food, arrows, a sword, armor with gold; sell extra wood and loot. A BLACKSMITH who opens the existing forge (start_forge) and can repair a sword for gold.
- A GUIDE in Home Meadow who explains the controls and points to the first Mine.
- A QUEST LOG on Q listing active and finished quests. Build the quest framework (phase2/quests.py: id, title, steps, giver, reward; start/advance/finish; saved). Add 2 small sample side quests to prove it (e.g. bring the farmer 10 wood; find the kid's lost cat in the Woods). Stage 3 writes the real quests.
- Place 8-12 people: at least 3 in Home Meadow, the rest in other lands near houses. Stage 2a is redrawing the lands in parallel and adding `village:` header lines (atlas.villages): if atlas.villages exists when you rebase, use those squares; until then use spots by existing houses. A test checks every person stands on a walkable, reachable tile.
- Saving: quests, shop state, who you've talked to.
- Tests: talking, choices, a purchase (gold down, item up, can't overspend), the blacksmith opening the forge, the quest log, sample quests start -> finish -> reward, save/load round-trip, placement.

Owns: phase2/people.py, phase2/dialogue.py, phase2/shop.py, phase2/quests.py, phase2/data/, phase2/draw_people.py (or similar), NPC art (new functions in sprites.py are OK; don't change existing ones). Do NOT edit levels/world/* (2a) or monster/fight code (2c).
