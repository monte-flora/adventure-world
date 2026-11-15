# Adventure World - to-do list

Everything we've asked for and agreed on, in the order it gets built.
`[ ]` = not started, `[~]` = being built now, `[x]` = done (with the date).

## Now: being built in parallel sessions (asked 2026-11-08)

- [~] Go public: new repo monte-flora/adventure-world, name removed
- [x] 2026-11-12 **Cave 4, Cave 9 and the 3 Nightfall caves redrawn in the kid's style** (asked 2026-11-12). 20 rows tall, with twists and turns, up and down, and a few minutes of play each: Cave 4 "The Old Mine Shaft" (up the shaft, back along the middle, dig to the lever, down through a gate in the floor), Cave 9 "The Deep Stone Maze" (the exit is locked: climb the wall, swing on vines, crawl to the lever, ride a steam geyser up to the diamond, ride back over the lava), and The Whisper Hollow, The Hollow Stair and The Shadow Stairs (easy to hard, each with a diamond and a harder Sun Shard). Stone caves get a new back wall: layers of rock, cracks, old bricks and cobbles, wooden mine props, roots and fossils.
- [x] 2026-11-11 **Lives.** You start with 3 (a heart and "x3" on the panel). Out of health in a cave: lose a life, wake up outside its Mine with full health. On the map or in Nightfall Hollow: wake up at the nearest house (Nightfall: the nearest shrine). In the castle: back to the start of that level. Out of lives: an "Out of lives!" card, then 3 new lives, keeping everything. A LEVEL UP! card can offer "Extra life" (up to 9).
- [x] 2026-11-11 **The pickaxe lasts forever.** Digging never wears it out or breaks it; the panel says "never breaks". Swords still break. You can still craft one if you somehow have none.

- [x] 2026-11-08 **Mine entrances match their cave.** On the home map, a Mine to a green moss cave looks mossy, a red lava cave's Mine has red moss, and a blue crystal cave's Mine has ice crystals.
- [x] 2026-11-08 **Editor icons.** The editor's palette shows a picture for every block, including chests, platforms and monsters (now some are blank).
- [x] 2026-11-08 **The kid's caves in the game.** The 4 caves in `my_caves` (blue lvl 1, green lvl 1 and 2, red lvl 1) become real caves under Mines, and a review of their design is used to redo the other hand-drawn caves to match.
- [x] 2026-11-08 **A bigger Shadow Castle.** 5 castle levels before the throne room, maybe a maze where you find the right path (decided in a grill first).
- [x] 2026-11-08 **Not every cave has a diamond at the end**, so it pays to explore the map.
- [x] 2026-11-08 **Craft menu without numbers.** Pick an item with the mouse, or move up and down with the arrow keys, then press ENTER to craft it.

- [x] 2026-11-08 **Spooky intro music.** The intro cards get their own mysterious, ominous tune. When the cards end, the screen fades into the home world as its music fades in.
- [x] 2026-11-08 **A new world map** (decided in a grill first). A huge lake with the Portal on an island in the middle, and a brown path that keeps you safe from bad luck but stays far from water and forests, so you have to leave it.

- [x] 2026-11-08 **Automatic tests on GitHub.** The tests live in the repo and run on every push and pull request (GitHub Actions), so a change can't quietly break the game.

- [x] 2026-11-08 **A walking animation in caves and the castle** (scoping first). A side-view (profile) Hero whose legs swing back and forth as he walks.
- [x] 2026-11-08 **Climbing a ladder shows the Hero from the back**, not facing us.
- [x] 2026-11-08 **Hold the sword and pickaxe lower** in the side view, so they don't cover the Hero's face.
- [x] 2026-11-11 **Walking on the world map, old-school style.** The Hero faces the way he walks (front, back or side) and his 2 walking pictures take turns, one every step, then he stands still when he stops. The pictures are `WALK_DOWN_`, `BACK_STAND` and `WALK_UP_` in `sprites.py` (the sides use the cave walk); `MAP_STEP_TIME` in `game.py`.
- [x] 2026-11-08 **Play it in a web browser** (PR #16). `pixi run -e web build-web` makes the page, and GitHub builds it for every PR. It's on itch.io as a Draft.
- [x] 2026-11-08 **New versions go to itch.io by themselves** (PR #17), once the `BUTLER_API_KEY` secret and the `ITCH_GAME` variable are set on GitHub (see web/README.md).
- [x] 2026-11-08 **More engaging caves** (PR #18: three "recipe" caves with vines, slippery ice, healing springs and rising lava), using ideas from two level-design articles: teach one thing at a time, side paths and secrets, gem trails, vertical sections, rests after hard parts, themes that change how a cave plays.
- [x] 2026-11-08 **A more engaging overworld** (PR #21: 7 lands, landmarks that lift the fog, secret chests, signposts; PR #22: the gates, the Frosty Corner and a Secret Mine): regions with their own feel, landmarks, secrets and reasons to explore the new lake map.
- [x] 2026-11-08 **New cave art for the green, blue and red caves** (PR #19, plus PR #20 for the vines, ice, springs and rising lava), in the style of the user's two example sheets: mossy walls, hanging vines and glowing mushrooms; ice bricks, icicles and crystals; black lava rock with glowing cracks, red moss and embers.
- [x] 2026-11-09 **A skippable tutorial** (PR #24). Tip bubbles that pause the game and point at what they explain, the first time it matters: walking, fights, eating, forests, the Craft menu, water, Mines, jumping, ladders, digging and more. ENTER, SPACE or a click closes a bubble, S means "no more tips", and TAB on the title screen turns them on or off. The words live in `TIPS` in `tutorial.py`.
- [x] 2026-11-09 **Save over the game's caves in the editor.** The 10 hand-drawn caves and the 5 castle levels are text files in `levels/`. Open one in the editor and Save changes it in the game (it asks first); Save as still makes your own copy in `my_caves`.
- [x] 2026-11-13 **No spamming A in map fights.** In a fight on the map, A (and R, E and the buttons) wait 0.6 s at the start and after every turn, with the buttons dimmed, so mashing A does nothing. `BATTLE_PAUSE` in `game.py`.
- [x] 2026-11-14 **Play-test shortcuts for each part.** `pixi run nightfall` starts in Nightfall Hollow; `pixi run castle` and `pixi run throne` (already there as `--castle`/`--throne`) start by the castle and at the boss.
- [x] 2026-11-11 **Level up 3 times slower.** `XP_PER_LEVEL` went from 20 to 60: 60 XP to level 2, then 120 more, then 180... (The first ask was 4 times slower; on 2026-11-11 the user chose 3 times.)
- [x] 2026-11-11 **Smarter cave and castle monsters.** They walk back and forth within 2 blocks of their spot, and only come after you once you're within 3 blocks (and no more than 2.5 blocks above or below them), then go back to patrolling when you get away. A Skeleton that sees you stops, draws its bow with a blinking "!", and waits 1.2 s before its first arrow. Settings: `PATROL_RANGE`, `CHASE_RANGE`, `CHASE_HEIGHT`, `SKELETON_AIM` in `caves.py`. (PR #27)
- [x] 2026-11-11 **Shadow monsters in the editor's castle levels.** With the castle look, monsters you paint (and in "Play it!") are Shadow monsters, like in the real castle. (PR #27)
- [x] 2026-11-11 **Monsters only see you on their own level.** Above or below a monster (on a ledge, a step or the floor under it), it can't see you: no chasing, and Skeletons don't aim. `SAME_LEVEL = 0.9` in `caves.py` (your feet must be this close to its feet). (PR #32)
- [x] 2026-11-11 **Pull requests merge by themselves** once the tests and the web version pass (`.github/workflows/auto-merge.yml`), then the branch is deleted and the new version goes to itch.io. Put the `hold` label on a pull request (or make it a draft) to stop it.

## Next: a teen version of Phase 2 (asked 2026-11-15, on `phase-2`)
- [ ] **T1 Teen look and name.** Darker theme across Phase 2 (palette, UI, music mood), a cooler game name (agent picks one, easy to change; note the choice), and a fuller story (Shadow King backstory and motive, lore, darker but kid-safe tone).
- [ ] **T2 The world grows dark.** The overworld light fades very slowly over the game as the Shadow King pulls light from the world (story-linked; tie to the main quest's Light Stones).
- [ ] **T3 R attacks everywhere.** Every attack uses R: map fights (Run moves off R, e.g. to X), cave sword swings, castle and throne. Update hints, tips, guide.
- [ ] **T4 Smooth overworld movement.** The Hero moves smoothly on the Phase 2 map instead of one square per step, and map monsters roam freely (not square by square).
- [ ] **T5 No random effects.** Remove `random_event` (thistle hurts, random heals, random armor) in Phase 2.

## From the play-test on 2026-11-07

- [x] 2026-11-07 **Skip the intro.** Press S on a story card to skip the rest of the cards.
- [x] 2026-11-07 **Restarting skips the intro.** After you die (or win) and press ENTER to play again, the intro cards don't show again.
- [x] 2026-11-07 **Climbing walls work like a ladder.** Touch a climbing wall (`%`) and hold UP to climb its face slowly, DOWN climbs down, SPACE jumps off. Wall jumps still work, and get easier.
- [x] 2026-11-07 **Replace the Creeper with the Ember Skull.** A floating skull wrapped in flames, with glowing eye sockets. Same trick: it drifts at you, its fire flares brighter, then BOOM. New name and picture everywhere (map, caves, fights, title screen, help, guide).
- [x] 2026-11-07 **Background music.** One looping tune per place: the home world, each cave look (stone, crystal, lava, moss), Nightfall Hollow and the castle. Made from math like the sound effects. N turns the music on and off; M still turns off all sound.
- [x] 2026-11-07 **Bug: a Creeper blast can bring you back to life** if it was your 5th monster (finishing the quest heals you after you've already died).
- [x] 2026-11-07 **A cave editor** (`pixi run editor`): a palette of every building block drawn with the game's real art, paint and rub out with the mouse, Box fill, Undo, the look (stone, crystal, lava, moss, castle), 14 or 20 rows tall, any width. Open any cave or piece to start from, Save into the `my_caves` folder (one text file per cave). **Play it!** drops you into your cave, a checklist warns about a missing S/E/* and lava in the air, and **Can it be beaten?** sends a robot through it. Your caves are editor-only for now (the Mines don't use them yet).

## Next: forging swords and pickaxes (agreed in the grill)

- [x] 2026-11-13 Forging stays free, anywhere in a forest or on solid ground in a cave.
- [x] 2026-11-13 The forge game is 3 hammer strikes. Each one is Perfect (a gold zone, 8% of the bar), Good (a green zone, 24%) or Miss. The marker gets 15% faster each strike.
- [x] 2026-11-13 **Sword quality:** at least 2 Perfect and no Miss makes a **Great sword** (+1 damage, 24 hits). 2 or more Misses makes a **Cracked sword** (4 hits). Anything else makes a normal sword (16 hits).
- [x] 2026-11-13 Every forge fills one of your 3 sword slots, so you can only forge again when a sword breaks.
- [ ] ~~**Pickaxes** use the same 3-strike game~~ (dropped 2026-11-11: pickaxes never break now): a Great pickaxe lasts 15 digs, a normal one 10. A crack gives nothing, and you can try again straight away. Free in the forest, 2 wood in a cave.
- [x] 2026-11-13 About 1 in 3 swords ~~and pickaxes~~ in chests are Great (pickaxes never break, so they have no quality).
- [x] 2026-11-13 Tools warn you at 3 uses left (a chip sound, a message, and the pips turn red). The panel shows Great tools in gold and Cracked ones in red.

## Then: new things in caves (agreed in the grill)

- [x] 2026-11-11 Moving platforms that slide side to side (`P`) or up and down (`U`), and carry you.
- [x] 2026-11-11 **Platform range** (asked 2026-11-11): the P's or U's you draw are exactly the track, so you choose where a platform turns around (it never wanders until it bumps into something). The editor draws each track with red turn-around bars, and the checklist warns about tracks that can't move.
- [x] 2026-11-11 **New level parts** (asked 2026-11-11): secret walls (`F`), levers (`L`) that open iron gates (`G`) in caves too, flame jets (`J`) and steam geysers (`M`). All in the editor's palette, and the robot knows them.
- [x] 2026-11-11 **A smarter robot.** Its map of how far knows you can't fly, can't drop down through a ledge, and never touches spikes, lava or fire. So it got through the 5 hand-edited levels it was stuck on, and the editor's "Can it be beaten?" uses the same map now.
- [x] 2026-11-11 **Cave 1's lift** (asked 2026-11-11): the U's by the lever are now a real up-and-down lift from the floor, and the step you could hop over from is gone, so you have to ride it up to the lever. The editor's robot now tries 400,000 moves, like the test robot.
- [x] 2026-11-13 Swinging vines (`R`): you grab one by jumping into it, pump LEFT/RIGHT to swing higher, and SPACE lets go. Two new pieces use them (swing over the spikes, two vines over the lava); the robot can swing too.
- [ ] Falling stalactites: they shake, then drop when you run under them.
- [ ] Water pools you swim in (no breath meter).
- [ ] About 2 new cave files for each (in `levels/caves/`, drawn in the editor), all checked by the solver. The old caves stay as they are.
- [x] 2026-11-13 **Every Mine plays a cave file; the cave pieces are gone** (asked 2026-11-13): every Mine plays a file from `levels/caves/` the editor can open (more Mines than files: the files go round again, nearest Mine first), the Secret Mine gets its own file (`levels/secret/`), and the piece-built caves and the editor's "Cave pieces" list are removed. The 2 swinging-vine pieces live on as demo caves in `my_caves/`; no Mine has a vine (`R`) yet.

## Done: the Sunfang quest in Nightfall Hollow (about 12-18 minutes of play)

- [x] 2026-11-11 A new Nightfall Hollow map: a black river splits it in two, with one broken Shadow Bridge. The straight walk to the castle is gone. The chest in the west holds old planks that fix the bridge.
- [x] 2026-11-11 The Portal swallows the diamonds you bring from home.
- [x] 2026-11-11 **Sunfang's parts:** the Blade (3 diamonds found in Nightfall Hollow), the Hilt (6 dead wood, in the Craft menu) and the Sun Gem (3 Sun Shards).
- [x] 2026-11-11 3 shadow Mines with hand-drawn dark caves (`levels/shadow`, a new spooky look), each with a diamond and a harder-to-reach Sun Shard, easy to hard. The robot checks them.
- [x] 2026-11-11 3 dark shrines, each guarded by a **Shadow Guardian** (24 health, hits for 3-5, stays put). Beat it, then SPACE lights the beacon. Dark shrines don't heal until they're lit.
- [x] 2026-11-11 Each lit beacon makes Nightfall Hollow a little brighter, and all 3 wake the forge at the castle gate.
- [x] 2026-11-11 The Sunfang forge is 3 steps: heat, hammer, cool. A failed step comes again.
- [x] 2026-11-11 A Sunfang checklist in the panel: Blade, Hilt, Sun Gem, Beacons.

## Next: more to do in Nightfall Hollow (the user wants them in this order, one pull request each)

- [x] 2026-11-11 **B. A lantern that grows.** You see 2 squares at first; each lit beacon adds 1 (up to 5). Shadow monsters near a lit beacon hit 1 less and move slower.
- [x] 2026-11-11 **D. Landmarks with secrets.** The Dead Giant Tree (west) and the Black Lighthouse (over the bridge): climb them (SPACE) to lift the fog and make the Mines sparkle (the lighthouse shows every Mine). Two signs point the way, and a hidden chest with a diamond ring is tucked between rocks in the south-east.
- [x] 2026-11-11 **C. Wren the ghost.** She waits near the start and has lost 3 lanterns (two on the west side, one in the north-east corner over the bridge). Bring them back for armor and a map hint.
- [x] 2026-11-11 **E. The Shadow Warden.** A tougher guardian (36 health, hits 4-6) stands in front of the bridge. You have to beat it to cross.
- [x] 2026-11-12 **F. Night events.** Every 40 turns the moon rises for 15 turns: shadow monsters notice you from 2 squares farther (not in beacon light, not on a shrine). A little wisp appears; follow it 3 hops and it leaves a gift (food, armor or gold). Gentle: no new monsters, no extra damage.
- [ ] **G. Treasure map.** Find map pieces; an X shows on the minimap where a chest is buried.
- [ ] **H. A way home** (only if the user asks): the Portal works both ways after the first beacon, and the home world gets something to do.

## Done: the Shadow King (part 6d), PR #14

- [x] 2026-11-08 A boss fight in the throne room (`throne.py`, start it with `--throne`) that lasts about a minute. He slashes his sword with a glowing warning first, throws shadow fireballs you jump over, and gets angrier at half health.
- [x] 2026-11-08 A healing nook he can't reach, with 10 health in total.
- [x] 2026-11-08 Losing wakes you by the throne room door with full health (changed from the castle entrance, since the castle now has 5 levels). He gets all his health back too.
- [x] 2026-11-08 The ending story: the light comes back, then THE END with your stats.

## Last: the guide (part 6e)

- [ ] A guide chapter about the story, Nightfall Hollow, the castle and the boss.
- [ ] Retake every screenshot, since many still show the old Hero and the all-forest map.
- [ ] Update the README.

## Done

- [x] 2026-11-12 **Stronger arrows, and fire arrows in Nightfall Hollow.** Arrows hit 3-5 (was 2-4) and 2-3 on the Shadow King (was 1-2). Stepping through the Portal turns them into fire arrows: +2 damage, a flame on the tip, "fire arrows" in the pack.
- [x] 2026-11-12 **Your sword in map fights.** In a fight on the map you hold your sword (or Sunfang), and it swings down when you attack. No sword, empty hands.

- [x] 2026-11-12 **Every cave is a file you can edit.** The 2 Mines that had caves snapped together from pieces now have their own files (`04_the_old_stone_cave.txt`, `09_the_old_stone_maze.txt`), so `levels/caves` has 12, one per Mine, and every Mine keeps the cave it had. The 3 Nightfall caves show in the editor's Open list too.

- [x] 2026-11-07 Pixi setup, bigger map with a camera, platformer caves, guide chapters, houses, boats, Sea Serpents
- [x] 2026-11-07 Story and Nightfall Hollow (6a), forging Sunfang (6b), the castle level (6c)
- [x] 2026-11-07 Fields and forests (8 wood per tree), fewer dead trees in Nightfall Hollow
- [x] 2026-11-07 XP level-up powers, lava pools in the floor, moss/ice/fire cave looks, the Hero as a knight
- [x] 2026-11-07 Ladders, ledge grab, ground pound, crawling, climbing walls, 8 new cave pieces
- [x] 2026-11-07 One Craft menu on C that stays open, slower leveling (20 XP), swords last 16 hits, pickaxes 10
