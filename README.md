# Adventure World

A 2D pixel-art adventure game in Python and pygame. Explore the map, fight
monsters, climb down into the Mines to find diamonds, chop wood to build houses
and a boat, then row to the Portal's island and step through into Nightfall Hollow,
the Shadow King's dark world!

You have 3 lives (the heart at the top of the panel). Run out of health in a cave and you wake up
outside its Mine; on the map, at the nearest house (in Nightfall Hollow, the nearest shrine); in the
castle, at the start of that level. Out of lives? You get 3 new ones and keep everything. Leveling up
can give you an Extra life (up to 9).

## Run it on a new computer

You need Python 3.7 or newer.

    git clone git@github.com:monte-flora/adventure-world.git ~/adventure-world
    cd ~/adventure-world
    python3 -m pip install -r requirements.txt
    python3 game.py

(Cloning into `~/adventure-world` keeps the paths in the guide correct.)

## Run it with pixi (no system Python needed)

[pixi](https://pixi.sh) installs its own Python and pygame inside this
folder (in `.pixi/`), so it never touches the Python on your computer.

    brew install pixi        # or: curl -fsSL https://pixi.sh/install.sh | sh
    pixi run game            # play (add options after: pixi run game --mute)
    pixi run guide           # open the code guide in your web browser
    pixi run game --castle   # play-test: start right next to the Shadow King's castle
    pixi run editor          # the cave editor: draw your own caves, then play them
    pixi run test-editor     # check that the cave editor still works

The first `pixi run` downloads everything; after that it starts right away.
`pixi.toml` lists what gets installed, and `pixi.lock` pins exact versions.

## Tip bubbles: a little tutorial while you play

The first time you find something new (a forest, a monster, a Mine, a ladder in a cave...),
the game stops for a moment and a bubble points at it and says how it works. Each tip
shows only once.

- ENTER, SPACE or a click closes a bubble.
- S in a bubble means "no more tips".
- On the title screen, TAB (or a click on "Tip bubbles: ON") turns tips on or off.
  Turning them back on shows every tip again, from the start. Good for a new player!

The game remembers your choice next time. On a computer it goes in `settings.json`, next
to `game.py` (delete it to start fresh). In a web browser, it goes in the browser's own storage.
The words and when each tip shows are in `tutorial.py`.

## How the code works - a guide for kids

Open `how_it_works/index.html` in a web browser. It explains the code with
pictures, from the game loop to how monsters chase you.

    open how_it_works/index.html          # Mac

## Draw your own caves: the cave editor

    pixi run editor                            # or: python editor.py
    pixi run editor my_caves/lava_tower.txt    # open one of your caves straight away
    pixi run editor levels/caves/03_blue_lvl_1.txt    # or one of the game's caves

Pick a building block on the right (or type its letter), then paint with the
**left** mouse button. The **right** button rubs blocks out. Everything is drawn
by the game itself, so your cave looks just the way it will when you play it.

- **Box**: drag out a whole rectangle of blocks. **Alt + click** picks up the block under the mouse.
- **Arrow keys** or the **mouse wheel** scroll around (hold Shift for up and down). **Zoom** shows more or less.
- **Look** changes how the cave looks: stone, crystal, lava, moss or castle.
  **Height** switches between 14 and 20 rows tall, and **Wider** / **Narrower** add or take away columns on the right.
- **Undo** and **Redo** (Ctrl+Z or Cmd+Z, and Ctrl+Shift+Z).
- **Open** loads one of your caves, or one of the game's caves or castle levels. Every cave the game plays is in the list.
- **Save** puts a new cave in the `my_caves` folder, one text file per cave.
  If you opened one of **the game's caves**, Save changes it in the game (it asks first):
  the next time you start the game, that Mine has your new cave. **Save as** makes your own copy instead.
- **Play it!** (or F5) drops you into your cave to try it. ESC brings you back to the editor.
- **Can it be beaten?** sends a robot into your cave. It tries thousands of moves to reach the diamond
  and then the exit, without ever getting hurt, and draws yellow dots along the way it found
  (or a red X where it got stuck). It ignores monsters: beating those is up to you!
  You can also run it yourself: `python cave_solver.py my_caves/lava_tower.txt`
- The **Checklist** shows what your cave still needs: a start (`S`), a diamond (`*`) and an exit (`E`).
  It also warns you about lava in the air, monsters stuck in rock and letters the game doesn't know.

### The game's caves: the `levels` folder

Every hand-drawn cave and castle level is a text file in `levels/` (`levels/README.md` says what
every letter means):

- `levels/caves/01_the_easy_moss_cave.txt` to `12_the_crystal_cave.txt`: one cave for each of the 12 Mines.
  Cave 01 goes under the Mine nearest home, the last one under the Mine farthest away. Keep them in order,
  from easiest to hardest.
- `levels/shadow/1_the_whisper_hollow.txt` to `3_the_shadow_throne_stairs.txt`: the 3 dark caves in Nightfall Hollow.
- `levels/castle/1_the_gate_and_the_lava_moat.txt` to `5_the_battlements.txt`: the Shadow Castle's 5 levels.

Change one in the editor and press Save, then start the game to play it. `pixi run test` sends the robot
through every one of them, so a cave nobody can beat is caught before it goes on GitHub (and itch.io).

### Every building block

| Letter | Block | What it does |
|:---:|---|---|
| `.` | Air | Empty space |
| `#` | Rock | Solid rock. You can stand on it, but even a pickaxe can't break it |
| `B` | Cracked rock | Dig through it with your pickaxe, or ground-pound it from above (DOWN in the air) |
| `*` | Diamond ore | The diamond! Dig it out with your pickaxe. Every cave needs one |
| `=` | Ledge | Stand on it. You can jump up through it from below |
| `-` | Crumbly ledge | It shakes and falls a moment after you step on it, then comes back |
| `H` | Ladder | Climb it with UP and DOWN. SPACE jumps off |
| `V` | Vine | Like a ladder that hangs from a branch. Jump into it and press UP to grab it, SPACE leaps to the next |
| `%` | Climbing wall | Hold UP to climb it like a ladder. SPACE jumps you off it: a wall jump! |
| `I` | Slippery ice | Solid like rock, but slippery: you slide a little before you stop |
| `o` | Bouncy mushroom | Land on it and it throws you about 6 blocks up |
| `^` | Spikes | They hurt 2. Jump over them |
| `A` | Spike trap | It pops up and down. Run across while it's down |
| `~` | Lava | It hurts 3. Draw it IN the floor row (the bottom row), as a pool to jump over |
| `!` | Fire | Flames on the floor. They hurt 2. Jump over them |
| `$` | Gem | Grab it for 2 XP |
| `T` | Treasure chest | Open it with R: food, tools, arrows... maybe even a diamond ring |
| `S` | Start | Where the Hero climbs in. Every cave needs one (and only one) |
| `E` | Exit door | Walk in to finish the cave. Every cave needs one |
| `u` | Healing spring | Walk into it when you're hurt: it heals you all the way, then slowly fills up again |
| `z` | Zombie | Walks at you and bites |
| `k` | Skeleton | Shoots arrows at you from far away |
| `c` | Ember Skull | Comes at you, then goes BOOM |
| `x` | Spider | Hops around while it chases you |
| `i` | Torch | Castle look only, just for looks |
| `w` | Window | Castle look only, just for looks |
| `f` | Banner | Castle look only, just for looks |

Movement facts for designing: the Hero is a bit less than 1 block wide and a bit more than 1 block tall,
jumps about 2 blocks high and 4 across, catches the edge of a wall up to 3 blocks high (ledge grab),
crawls through 1-block-tall tunnels (hold DOWN) and climbs ladders and climbing walls.
The gap in the left wall is the way back out of a cave.

## Tests: checking that nothing is broken

    pixi run test              # every test (a few minutes)
    pixi run test-all-caves    # every test, and the robot beats EVERY cave on the map (slow: about 10 minutes)
    pixi run test-editor       # just the cave editor's tests

The tests are in the `tests/` folder. Each one plays a little bit of the game, with no window and
no sound, and checks one thing at a time, like this:

    ok(you.climbing, "pressing UP at a ladder grabs it")

If something is broken, pytest shows which test failed and the message saying what should have happened.
There are tests for moving around in caves, the Craft menu, the map, the bow, rings, levelling up,
Nightfall Hollow and the castle. `test_game_starts.py` starts the game and the editor and plays for a
few hundred frames. `test_beatable_caves.py` sends a robot (`tests/robot.py`) into the caves. It has to
grab the diamond and reach the exit without getting hurt once (in the castle: find the key or pull the lever,
then go through the door). It ignores monsters: beating those is up to you!

If you change how the game works on purpose, a test may fail because it still expects the old way.
Then change the test to match, so it checks the new way.

### The green tick on GitHub

Every push and every pull request runs `pixi run test` on GitHub's computers
(see `.github/workflows/tests.yml`, and the **Actions** tab on GitHub).

- A **green tick** next to a commit or pull request means every test passed.
- A **red cross** means something broke. Click it, then **Details**, to see which test failed and why.
- A **yellow dot** means the tests are still running.

Every Monday it also runs `pixi run test-all-caves`. To run it any time: **Actions** > **Tests** >
**Run workflow**, and tick "Send the robot into every cave".

## Play it in a web browser

The game can also be a web page, so anyone can play it without installing anything:

    pixi run -e web build-web

That makes the page in `web/build/adventure/build/web/`, ready to upload to itch.io.
GitHub makes it too, for every pull request and every merge into `main`: look for
"adventure-web" under **Artifacts** on the run's page (**Actions** > **Web version**).
`web/README.md` says how to try it on your computer, what's different in a browser,
and how to put it on itch.io.

## The files
- `game.py`    - graphics, sounds, keyboard and mouse
- `main.py`    - starts the game in a web browser (see `web/README.md`)
- `web/`       - makes the web-browser version: `build_web.py` and `README.md`
- `rules.py`   - how the game works: the map, monsters, quests, fights
- `caves.py`   - the caves under each Mine: running, jumping, and which cave file each Mine plays
- `castle.py`  - the Shadow King's castle: keys, levers, locked doors and light shards
- `levels/`    - the game's hand-drawn caves and castle levels, one text file each (open them in the editor)
- `sprites.py` - the pixel art, drawn with letters
- `story.py`   - the story cards: change the words to tell the story your way
- `tutorial.py` - the tip bubbles: what each tip says, and when it pops up
- `settings.py` - remembers your choices (like "tips off") in `settings.json`, or in the web browser
- `editor.py`  - the cave editor: the palette of building blocks, painting, Play it!
- `cave_files.py` - loading, saving and checking the caves you draw (they go in `my_caves/`)
- `cave_solver.py` - the "Can it be beaten?" robot
- `test_editor.py` - tests for the cave editor (`pixi run test-editor`)
- `tests/` - tests for the whole game (`pixi run test`), and the robot that checks every cave can be beaten
- `terminal_version/adventure.py` - the earlier text-only version
  (no install needed: `python3 terminal_version/adventure.py`)

## Things to try changing
- Draw a new map: edit `WORLD_MAP` in `rules.py`. It can be any size - the
  camera scrolls to follow you, and the MAP in the side panel shows where you've been.
  `R` draws the brown path: monsters won't chase you on it, and nothing bad happens there
- Make a new land: add a line to `LANDS` in `rules.py` (its name, the box it covers, its landmark,
  and the words you see the first time you walk in). The letters at the top of `rules.py` draw rocks `X`,
  ice `I`, reeds `B`, steam vents `V`, landmarks `L`, chests `T` and signposts `+`. Make the vents puff
  more often with `VENT_EVERY`, or see farther from a landmark with `LOOKOUT_SIGHT`
- Change the gates: the Icy River `~` and the Frost Wall close in the Frosty Corner, and `BRIDGE_WOOD` in
  `rules.py` is how much wood fixes the broken bridge `=`. Hide a Secret Mine `S` anywhere: it gets a cave of
  its own, and it always has a diamond
- Keep strong monsters far from home (or bring them closer): `MONSTER_START_DISTANCE` in `rules.py`
- See more (or less) of the world at once: change `VIEW_COLS` and `VIEW_ROWS` in `game.py`
- Make a new monster: add a line to `MONSTER_TYPES` and `MONSTER_COUNTS` in `rules.py`,
  then draw it in `sprites.py` and add it to `MONSTER_ART`
- Draw a new cave: save it into `levels/caves/` with a number in front, like `11_my_cave.txt`
  (the first one goes under the Mine nearest home). Or open one there in the editor and change it.
  Try the cave recipe: a safe start, then the cave's ONE new thing where a mistake doesn't hurt, then the same
  thing harder, a rest by a healing spring `u`, a twist, the treasure... and a secret room, with gems that hint the way
- Make the lava rise! Add the line `lava rises: yes` under `theme: lava`, and the lava rises when you grab
  the diamond (or the chest in its place). How long it waits and how fast it rises: `LAVA_RISE_WAIT` and
  `LAVA_RISE_SPEED` in `caves.py`
- Make ice more (or less) slippery: `ICE_GRIP` in `caves.py` (smaller = more slippery), and make healing
  springs fill up faster with `FOUNTAIN_REFILL`
- Draw a new cave for the game: draw it in the editor, then save it in `levels/caves/` with the next number
  (like `13_my_cave.txt`). Every Mine plays one of those files: the Mine nearest home plays `01`, the next one `02`,
  and so on. More Mines than files? The files go round again (`levels/README.md` has the rule). Use `o` for a
  bouncy mushroom and `$` for a gem, and start a cave with `theme: lava` (or stone, crystal, moss)
- Make a lava pool: draw `~` IN the floor row (the bottom row of rock), so it's a hot pool to jump over.
  Draw `!` for a fire on the floor: it burns like spikes, so jump over the flames!
- Make fire hurt more or less: `FIRE_DAMAGE` in `caves.py`
- Grow more grass in mossy caves: `MOSS_GRASS` and `LEDGE_GRASS` in `game.py`
- Change how jumping feels: `JUMP_SPEED`, `GRAVITY` and `RUN_SPEED` in `caves.py`
- Put ladders and climbing walls in your caves: `H` is a ladder (UP/DOWN climb, SPACE jumps off) and
  `%` is a climbing wall (hold UP to climb it, SPACE to wall jump off it). A 1-block-tall gap is a tunnel you crawl through (hold DOWN)
- Change the new moves: `CLIMB_SPEED`, `WALL_JUMP_PUSH`, `LEDGE_REACH`, `POUND_DAMAGE` and `CRAWL_SPEED` in `caves.py`
- Change what's in treasure chests: `CHEST_LOOT` in `caves.py`
- Tell the story your way: change the words in `story.py`
- Change what the tip bubbles say: `TIPS` in `tutorial.py`. Write a new tip: give it words in `TIPS`,
  write a little "moment" that says when it fits, and add both to `MOMENTS`
- Write your own music: change the notes in `TUNES` in `game.py` (there's a tune for each place). N turns the music on and off
- Redraw the Shadow King's castle: open a level in `levels/castle/` in the editor. Use `A` for a spike trap
  that pops up and down, `i` for a torch, `w` for a moonlit window and `f` for a banner
- Make the spike traps faster or slower: `TRAP_DOWN` and `TRAP_UP` in `caves.py`
- Recolor your hero: change the letters in `PLAYER` in `sprites.py`
- Make it easier or harder: change `START_HEALTH`, `START_LIVES`, `MAX_LIVES`, `MONSTERS_TO_DEFEAT`, `DIAMONDS_NEEDED`
- Change the level-up powers: `POWERS` in `rules.py` (what each one does and how many times you can pick it),
  and the numbers just above it, like `TOUGHER_HEALTH`. Get more XP for diamonds, EXIT doors and quests
  with `DIAMOND_XP`, `EXIT_XP` and `QUEST_XP`
- Make building cheaper or pricier: `HOUSE_COST` and `BOAT_COST` in `rules.py`
- Make trees hold more (or less) wood before they fall down: `TREE_WOOD` in `rules.py`.
  On the map, `F` is a forest square and `G` is an open field
- Make armor stronger: `ARMOR_POINTS` in `rules.py`, and change how it looks with `ARMOR` in `sprites.py`
- Make arrows stronger or fly farther: `ARROW_DAMAGE` and `ARROW_RANGE` in `rules.py`
  (arrows hit 3-5; in Nightfall Hollow they burst into fire arrows, `FIRE_ARROW_BONUS` = +2 more)
- Make swords last longer (or shorter): `SWORD_DURABILITY` in `rules.py` (pickaxes never break)
- Level up faster or slower: `XP_PER_LEVEL` in `rules.py` (bigger = slower)
- Add something to the Craft menu (press C, pick a row with UP/DOWN or the mouse, then press ENTER
  or click it): `CRAFTS` and `draw_craft` in `game.py`
- Make diamond rings stronger: `RING_BONUS` and `RING_HITS` in `rules.py`, or more common: `RING_CHANCE` in `caves.py`
- Make Sunfang even stronger: `SUNFANG_DAMAGE` in `rules.py`, or give yourself longer to press
  each key when you forge it: `BEAT_TIME` in `SunfangForge` in `game.py`
