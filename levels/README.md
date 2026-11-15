# The game's caves and castle levels

Every hand-drawn cave and castle level in the game is one text file here. The game reads them
when it starts, so a change you save shows up the next time you play.

- `caves/` - the caves under the Mines. Cave `01` goes under the Mine nearest home, and the
  last one under the Mine farthest away. Keep them in order, from the easiest to the hardest!
  There are 12, one for every Mine on the map.
- `secret/` - the cave under the Secret Mine in the Whispering Woods.
- `shadow/` - the 3 dark caves under the Mines in Nightfall Hollow, easiest first. Each has a diamond (`*`)
  and a harder-to-reach Sun Shard (`s`). The robot checks them with the others.
- `castle/` - the 5 levels of the Shadow Castle, from the gate (`1`) to the battlements (`5`).

## Which Mine plays which cave

Every Mine plays one of the files in `caves/`. The game never makes up a cave, so every cave you
meet in the game is a file you can open in the editor. The rule (`plan_cave_files` in `caves.py`):

- Count the Mines from the nearest to home to the farthest. The nearest plays `01`, the next `02`, and so on.
- **More Mines than files:** the files go round again. With 12 files and 17 Mines, Mines 13 to 17 play `01` to `05` again.
- **Fewer Mines than files:** the nearest Mine plays `01`, the farthest plays the last file, and the ones in between are spread out.
- A Secret Mine plays a file from `secret/`.

Want a new cave in the game? Draw it and save it here as the next number, like `caves/13_my_cave.txt`.

## Changing one

    pixi run editor levels/caves/03_blue_lvl_1.txt

Or start the editor (`pixi run editor`), press **Open** and pick one under "Caves in the game".
Paint your changes, then press **Save**. The editor asks once, "Save over it?", and then the
game has your new version. **Save as** makes your own copy in `my_caves` instead.

Then run the tests: `pixi run test` sends a robot through every cave and castle level here.
If it can't get through one, the test says which, before it goes on GitHub (and itch.io).

## What's in a file

The first lines are settings, then the drawing. Every row must be the same length.

    theme: crystal                   how it looks: stone, crystal, lava, moss, shadow (or castle)
    name: The Icy Steps              its name (the editor shows it)
    lava rises: yes                  the lava rises when you grab the diamond (or the chest instead)
    about: ...                       a note for people about the cave (the game ignores it)
    locked door says: Locked! ...    castle levels only: what the locked door says without the key

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
