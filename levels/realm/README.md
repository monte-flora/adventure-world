# The realm (Shadowfall, the Godot game)

The teen game's overworld: 6 × 5 screens, each 30 × 17 squares (one 960 × 540 view at 32 px), so 180 × 85 squares in all.
One file per land, stitched like `../world/` (which the pygame Phase 2 map still uses; this folder is Godot only).
`9_umbral_reach.txt` is Nightfall's place: its own 3 × 3 map, the mirror of the 9 screens round the Shadowgate.

```
      A            B            C            D            E            F
 1  Weepingwold  Weepingwold  Hollowcrown  Hollowcrown  Wintermarch  Wintermarch
 2  Weepingwold  Emberhold    Hollowcrown  Mere         Wintermarch  Wintermarch
 3  Emberhold    Emberhold    Mere         SHADOWGATE   Mere         Cinder
 4  Mirefen      Mirefen      Mere         Mere         Cinder       Cinder
 5  Mirefen      Mirefen      Mirefen      Cinder       Cinder       Cinder
```

## The order (each Light Stone opens the next land)

| # | Land | Stone cave (`../stone/`) | Ability | Opens |
|---|---|---|---|---|
| 1 | Emberhold (home) | 1 | dash | the Riven Gap to the Weepingwold's stone Mine |
| 2 | Weepingwold | 2 | climb | ivy cliffs `Y` up to Hollowcrown |
| 3 | Hollowcrown | 3 | pound | rubble `O` on the causeways to the Drowned Mere |
| 4 | Drowned Mere | 4 | swim | open water `W`: the islands and the bay to the Wintermarch |
| 5 | Wintermarch | 5 | double_jump | the Ashen Stair down to the Cinder Wastes |
| 6 | Cinder Wastes | 6 | flare | shadow thorns `K` round the Mirefen |
| 7 | Mirefen | 7 | truesight | the Portal Stair on the Shadowgate island |

All 3 kinds of gate letter (`Y` `O` `K`) border Emberhold, so you see them from the start.

## What's in a file

    land: emberhold                  the land's id (display names live in shadowfall/rules/names.gd)
    at: 17 0                         its top-left square on the realm: row, then column
    screens: A3 B2 B3                the screens it covers
    landmark: The Ember Beacon       the name of its waystone (the one L)
    says: ...                        what you're told the first time you get there
    about: ...                       a note for people
    dark: A1                         screens that are pitch dark (the lantern only)
    home: 27 46                      where you start (Emberhold only; on an H)
    village: Emberwick 27 50         a village: name, then the middle of its square
    mine: stone/1_the_crumbling_vigil.txt 23 8     the cave under the Mine (M or S) at that square
    gate: Riven Gap 10 50 dash       a rock (X) that opens with that ability
    ground: painted                  draw this land with the painted ground textures (shadowfall/realm/ground/)
    prop: oak 12 30                  a prop (a tree, house, lamppost ...): its name, then row and column

Numbers are the land's own rows and columns (row 0, column 0 = its top-left letter). `mine:` and `gate:` can repeat.
The Umbral Reach also has `world: umbral_reach`, `mirror:` (the screens it mirrors) and `castle:` (the castle's first level).

## The letters

The `../world/` letters (`G` grass, `F` forest, `X` rock, `W` water, `R` path, `H` house, `L` waystone, `M` Mine,
`S` Secret Mine, `T` chest, `+` signpost, `P` the Portal, `I` ice, `B` reeds, `V` steam vent, `#` bridge, `C` castle),
plus the ability gates: `Y` ivy cliff (climb), `O` rubble (pound), `K` shadow thorns (flare). Open water needs swim.
`.` means "not this land". Here `O` is rubble, not the pygame map's bubbles.

## Props and the painted ground

How to put trees, houses and lampposts on a land: "Props on the realm" in `../README.md`.
How the art is made: `shadowfall/realm/README.md`.
