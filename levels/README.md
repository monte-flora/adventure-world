# The game's caves and castle levels

Every hand-drawn cave and castle level in the game is one text file here. The game reads them
when it starts, so a change you save shows up the next time you play.

- `caves/` - the caves under the Mines. Cave `01` goes under the Mine nearest home, and the
  last one under the Mine farthest away. Keep them in order, from the easiest to the hardest!
  There are 17: the classic map has 12 Mines (they play `01` to `12`), and the big Phase 2 map has 17.
- `secret/` - the cave under the Secret Mine in the Whispering Woods.
- `shadow/` - the 3 dark caves under the Mines in Nightfall Hollow, easiest first. Each has a diamond (`*`)
  and a harder-to-reach Sun Shard (`s`). The robot checks them with the others.
- `castle/` - the 5 levels of the Shadow Castle, from the gate (`1`) to the battlements (`5`).
- `world/` - the Phase 2 world map: one file for every land, stitched into one big map (see
  "The Phase 2 world map" at the bottom).

## Which Mine plays which cave

Every Mine plays one of the files in `caves/`. The game never makes up a cave, so every cave you
meet in the game is a file you can open in the editor. The rule (`plan_cave_files` in `caves.py`):

- Count the Mines from the nearest to home to the farthest. The nearest plays `01`, the next `02`, and so on.
- **More Mines than files:** the files go round again: after the last file, the next Mine plays `01` again.
- **Fewer Mines than files:** the last files are left over. The classic map's 12 Mines play `01` to `12`, so `13` to `17` are only in Phase 2 (under the far Mines in Frost Peaks and Sunscorch Desert).
- A Secret Mine plays a file from `secret/`.

Want a new cave in the game? Draw it and save it here as the next number, like `caves/18_my_cave.txt`.

## Changing one

    pixi run editor levels/caves/03_blue_lvl_1.txt

Or start the editor (`pixi run editor`), press **Open** and pick one under "Caves in the game".
Paint your changes, then press **Save**. The editor asks once, "Save over it?", and then the
game has your new version. **Save as** makes your own copy in `my_caves` instead.

To play one in Shadowfall (the Godot rebuild): `pixi run godot-cave levels/caves/03_blue_lvl_1.txt`
(a cave in `my_caves/` works too).

Then run the tests: `pixi run test` sends a robot through every cave and castle level here.
If it can't get through one, the test says which, before it goes on GitHub (and itch.io).

## Polish a cave with Gemini

Make Gemini paint a picture behind your cave (Shadowfall only; the blocks you stand on stay the same).

1. Save your cave in the editor, then press **Polish**. It makes the folder `levels/polish/<cave>/`
   with a map of your cave (`layout.png`), the words for Gemini (`prompt.txt`) and the steps (`README.txt`).
2. In Gemini, drag in `layout.png`, paste all of `prompt.txt`, and send it.
3. Download Gemini's picture into that folder (any name, .png, .jpg or .webp), then press **Polish** again.
   It shrinks the picture into `painted.webp`, and the cave plays with it behind the blocks.

Not happy with it? Ask Gemini again, or change `prompt.txt`. Delete `painted.webp` to go back to the
normal look. Without the editor: `python shadowfall/tools/polish.py export|import levels/caves/<cave>.txt`.

## What's in a file

The first lines are settings, then the drawing. Every row must be the same length.

    theme: crystal                   how it looks: stone, crystal, lava, moss, shadow (or castle)
    name: The Icy Steps              its name (the editor shows it)
    lava rises: yes                  the lava rises when you grab the diamond (or the chest instead)
    about: ...                       a note for people about the cave (the game ignores it)
    locked door says: Locked! ...    castle levels only: what the locked door says without the key

Shadowfall (the Godot rebuild, `shadowfall/`) reads these too. The pygame game skips them.

    stone: Dawnstone                 which Light Stone the diamond (*) holds, so which power it gives
    land: the Weepingwold            which land's Mines play this cave
    needs: climb, pound              the powers the robot may use to beat it (see below)
    dark: yes                        pitch dark: you need your lantern

**needs:** lists powers by their ids: `dash`, `climb`, `pound`, `swim`, `double_jump`, `flare`,
`truesight` (`needs: none` = no powers). The robot (`cave_solver.py`, and `pixi run test`) then only uses
those: without `pound`, cracked rock `B` is plain rock to it; without `climb`, climbing walls `%` are;
without `truesight`, secret walls `F` are; without `flare`, shadow thorns `n` hurt like spikes. With no
`needs:` line it may use every power. The pygame game has no dash, swim or double jump, so the robot never
uses those: it has to beat the cave without them. The editor keeps all these lines when it saves.

## The letters

| Letter | What it is |
|---|---|
| `#` | rock (stone bricks in the castle) |
| `.` | air |
| `B` | cracked rock: dig it with your pickaxe, or ground pound it |
| `*` | diamond ore |
| `s` | Sun Shard ore: dig it out like a diamond (only the dark shadow caves in `shadow/` have one) |
| `=` | ledge: jump up through it |
| `-` | crumbly ledge: it falls when you stand on it! |
| `^` | spikes |
| `A` | spike trap: it pops up and down! |
| `!` | fire: jump over the flames! |
| `~` | lava: draw it IN the floor row, so it's a hot pool sunk into the ground (stack it 2 or 3 tall, with rock around it, for a deeper pool) |
| `T` | treasure chest |
| `$` | a glittering gem (grab it for XP) |
| `S` | start |
| `E` | exit door |
| `o` | bouncy mushroom |
| `H` | ladder (UP and DOWN climb it, SPACE jumps off) |
| `V` | vine (like a ladder hanging from a branch: jump into it and press UP) |
| `%` | climbing wall (slide down it, then SPACE to wall jump!) |
| `I` | slippery ice |
| `u` | healing spring (a healing fountain in the castle) |
| `F` | secret wall: looks just like rock, but you walk right through it (the editor shows a `?` on it) |
| `L` | lever: press R next to it, and every iron gate opens (in the castle it opens the locked door too) |
| `G` | iron gate: solid bars until you pull a lever |
| `J` | flame jet: shoots fire 3 blocks up, then stops (it goes with the spike traps) |
| `M` | steam geyser: rock with a hole. Stand on it: when it puffs, it throws you about 7 blocks up! |
| `P` | moving platform, side to side: draw a row of P's. That row is its track: a 2-wide platform slides from one end to the other and turns around right at the ends, never past them. Just 1 or 2 P's: it stays put |
| `U` | moving platform, up and down: draw a column of U's (as wide as you like). That column is its track: the platform rides from the top U to the bottom U and turns around there, never past them. Leave 2 blocks of air above the top U, so you fit on it. Just one row of U's: it stays put |
| `R` | swinging vine (R for rope): draw a column of R's right under rock. A vine that long hangs from the rock. Jump into it to grab it, press LEFT and RIGHT to swing higher, and SPACE lets go: you fly off as fast as you swung! |
| `z` `k` `c` `x` | Zombie, Skeleton, Ember Skull, Spider |
| `K` | castle: the key |
| `D` | castle: the locked door to the next level (in level 5, the throne room's great door) |
| `+` | castle: a light shard |
| `i` `w` `f` | castle: torch, moonlit window, banner (just for looks) |
| `C` | Shadowfall: a checkpoint (lantern shrine). You wake up here after a fall. The pygame game plays it as air |
| `>` `<` | Shadowfall: a one-way door. Shut until you touch it from the side the arrow points to (the right for `>`), then open for good: a shortcut back at the end of a loop. The pygame game plays it as air |
| `n` | Shadowfall: shadow thorns. They hurt, until the flare (the Sun stone's power) burns them. The pygame game plays it as air |

## Moving platform tracks

The P's or U's you draw are exactly where a platform goes, so you decide where it turns around.
Air or rock past the end of the track doesn't change anything.

    #..........#        a short side-to-side track: the platform slides 2 blocks and back
    #...PPPP...#
    #..........#        a tall up-and-down track: from row 1 down to row 4 and back up
    #.U........#
    #.U........#        In the editor, a yellow line shows each track, with a red bar at
    #.U........#        each end where the platform turns around. The checklist tells you
    #.U........#        about a track too short to move, or U's that aren't a neat column.

The gap in the left wall is the way back out. In the castle it's the gate (level 1) or the
door back to the level before.

## Tips the robot taught us

- The Hero jumps up 2 blocks, not 3: every ledge or step should be at most 2 above the one before.
  A moving platform (P or U) at its lowest should be at most 2 above the floor, too.
- In a low tunnel (4 or 5 blocks tall), keep spikes, spike traps and lava pools 2 wide: 3 is too far
  to jump with the roof that close.
- Start and end a P track 1 block past the spikes or lava under it, so you can step on and off over safe ground.
- A shelf you get up to with a mushroom or a steam geyser needs a gap at one end, so you can drop back down
  (you can't drop through a ledge).
- Very long U tracks are slow: for a deep shaft, a ladder is better.
- A swinging vine's bottom should be at most 3 blocks above the floor you jump from, and 2 or 3 blocks
  out from the edge, so you can jump into it. A vine 6 to 8 blocks long swings you across about 10 blocks.

## Props on the realm

The realm files (`realm/`, the Godot game) can stand painted pictures on the land: trees, cottages,
lampposts, a campfire. Each one is a `prop:` line in the land's file:

    prop: oak 12 30                  an oak with its foot on row 12, column 30
    prop: cottage_a 24.5 48          a half square up (decimals move it part of a square)

- The name is a picture in `shadowfall/realm/props/` (the full list: `shadowfall/realm/gemini/assets.json`).
- Its foot (the bottom middle of the part you bump into) stands on the middle of the square.
- Write one line for each prop. Rows and columns are the land's own, like `mine:` and `gate:`.
- A prop never covers a Mine, waystone, house, chest, sign or Portal (`M S L H T + P`).
- It replaces the tree, house or Mine tile under it.
- In a `ground: painted` land the trees come only from props (an `F` still tells monsters where the forest is).
- Windows, lampposts, the smithy's forge and campfires glow, and glow brighter as the Shadow King's dark
  falls on the realm. Everything else fades to grey and violet with the gloom.
- Easiest: place them with the prop editor, `pixi run realm-editor`. Pick a prop on the right, click the map to
  put it there, drag it to move it, right-click to delete it, and press S to save.

## The Phase 2 world map

Phase 2 (`pixi run game2`, or pick it on the title screen) plays on a big map made of the files in
`world/`, one for every land. The game stitches them together when it starts. Each file looks like this:

    name: Home Meadow                the land's name (it pops up the first time you walk in)
    at: 28 0                         where its top-left corner goes on the big map: row, then column
    landmark: Windmill               the name of its landmark (the L), if it has one
    says: Your home meadow. ...      what you're told the first time you get there
    about: ...                       a note for people (the game ignores it)
    home: 13 13                      where you start (just one land has this; it must be on an H)
    village: Meadowbrook 6 24        a village: its name, then the middle of its open square
    lookout: 18 9                    a lookout tower (put it on open ground)
    gate: Desert Gate 16 0 3         a gate: its name, where it is (draw an X there), the level that opens it
    GFFGGGGGGGGGGFGG
    FFFFFGGGGGGGGGGG                 the drawing, one letter per square, with no spaces
    WWWWWWWWWW=WWWWW

- The letters are the classic map's (the list is at the top of `rules.py`): `G` grass, `F` forest,
  `W` water, `X` rock, `R` path, `M` Mine, `H` house, `L` landmark, `T` chest, `+` signpost, `P` the Portal,
  `=` a broken bridge (5 wood fixes it), `~` the Icy River, `B` reeds, `I` ice, `V` steam vent...
- A `.` means "not this land": the square belongs to another land's file. So a land can have any shape.
- Two lands can't draw the same square (the game says which ones do). Squares no land draws are open water.
- The numbers in `home:`, `village:`, `lookout:` and `gate:` are the land's OWN rows and columns: row 0,
  column 0 is the top-left letter of its drawing (not the big map's). You can have many villages, lookouts
  and gates. A village is a few houses (H) around an open square of grass or path; people move in later.
- Home is the house the `home:` line points at. Every other `H` is a rest house.
- Each land's landmark (`L`) is a **waystone**: walk onto it and it lights up. On any lit waystone (or at
  home) SPACE opens a list of the lit ones, and you can travel to any of them. Draw just one `L` per land.
- A lookout: climb it with SPACE and you spot the nearest hidden chest. Chests (`T`) are hidden in the grass
  until a lookout spots them or you step on one. What's inside depends on the land.
- A gate is solid rock until you reach its level; then it opens for good.
- A landmark needs its picture in `sprites.py` (and `LANDMARK_ART` in `game.py`). New lands can borrow one.
- Mines get caves the same way as on the classic map: the cave files from nearest home outward, one for each
  of the 17 Mines (see "Which Mine plays which cave" above). Keep every Mine reachable (the tests check).

The lands open up in an order: from home you can walk to the Whispering Woods, the Old Ruins and the lake
shores. Fix the old bridge over the Icy River for Frost Peaks, and the log bridge over the Murk River for
Murk Swamp (or row there). The Desert Gate opens Sunscorch Desert at level 3. Row out to Portal Island.
