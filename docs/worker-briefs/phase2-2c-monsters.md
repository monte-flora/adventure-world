Task: Phase 2 stage 2c, MONSTERS, for Adventure World (monte-flora/adventure-world).

Build PHASE2.md design point 4, in Phase 2 only (Classic's monsters and fights stay exactly as they are):
- No hidden random fights: every overworld monster is visible on the map. Read how Classic spawns and moves map monsters and starts fights (rules.Game, start_battle) and replace that for Phase2Game.
- Monsters per land (Phase2Game.land_at / the atlas): each land has its own mix and count (Home Meadow: few and weak; desert, swamp and peaks: tougher; a new kind or two with art in the sprites.py style is welcome). More come out at night: if the phase-2 map has no day/night, add a simple cycle (turn counter + darker tint). Nightfall keeps its moonrise.
- Behavior: patrol near a home spot, chase when you're within a few squares, give up and go back when you get away. They never enter houses, village squares (atlas.villages, if present when you rebase) or the path, so towns and the road are safe. Respawn slowly, away from you.
- Starting a fight: you touch them or they reach you. Walk into one from BEHIND (facing or moving away from you) = FIRST STRIKE (a free hit and a message). Monsters much weaker than your level run from you.
- The fight: keep the classic turn-based box, but Attack becomes a TIMING STRIKE: a marker sweeps a bar; press A in the zone. Perfect = extra damage, Good = normal, Miss = a weak hit. Reuse the forge's bar look. Keep the no-spamming pause (BATTLE_PAUSE in game.py). Running and eating as before.
- Tests: monsters visible and placed by land, patrol/chase/give-up, safe zones, first strike from behind, weak ones flee, timing zones -> damage, classic fights unchanged, save/load keeps monsters (or respawns them sensibly).

Owns: phase2/monsters.py, phase2/fight.py, phase2/draw_fight.py (or similar), monster art (new sprites.py functions OK). Do NOT edit levels/world/* (2a) or people/dialogue/shop/quests (2b).
