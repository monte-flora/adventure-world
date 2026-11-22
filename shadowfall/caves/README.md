# Caves (side view)

`cave.gd` builds a cave from a `levels/` text file; `hero_side.gd` is the Hero, `props.gd` the platforms
and swinging vines, `monster.gd` the monsters, `tiles.gd` which letter is what. The pygame game's
`caves.py` is the reference: every letter below plays the way it does there (numbers in brackets).

## Letter -> behaviour -> test

Tests are in `tests/test_cave_letters.gd` unless marked *toys* (`tests/test_cave_toys.gd`).

| Letter | Behaviour | Test |
|---|---|---|
| `#` `.` | rock is floor and wall; air is open | `test_hash_rock_blocks_and_dot_air_is_open` |
| `S` | you start here | `test_S_is_where_you_start` |
| `E` | touch it: back to the overworld, next to the Mine | *toys* `test_touching_E_returns_to_the_overworld`, `test_exit_goes_back_to_the_mine` |
| `B` | solid; R, G (dig) or Kingsfall breaks it | `test_B_cracked_rock_breaks_to_a_sword_strike`, *toys* `test_dig_cracked_rock`, `test_kingsfall_breaks_cracked_floor` |
| `*` | solid diamond ore; bump, strike or dig it: gold, or its Light Stone (`stone:`) | *toys* `test_stone_diamond_gives_its_ability` |
| `s` | solid Sun Shard ore, same as `*` | `test_s_sun_shard_ore_digs_out` |
| `=` | one-way ledge: jump up through, stand on it | `test_equals_ledge_jump_up_through_and_stand` |
| `-` | crumbly ledge: falls 0.9 s after you step on it, back after 3 s | *toys* `test_crumbly_ledge_falls_and_returns` |
| `^` | spikes: a heart, back to safe ground | *toys* `test_spikes_hurt_and_put_you_back` |
| `A` | spike trap: up 0.9 s, down 1.3 s (one clock with `J` `M`) | `test_A_spike_trap_hurts_only_when_up` |
| `!` | fire | `test_bang_fire_hurts` |
| `~` | lava pool | `test_tilde_lava_pool_hurts` |
| `lava rises: yes` | after `*` (or `T`): waits 2 s, rises 1 tile/s, stops below `E` | `test_lava_rises_waits_then_stops_below_the_exit` |
| `T` `$` | chest (10 gold), gem (1 gold) | *toys* `test_gems_and_chests_give_gold` |
| `o` | mushroom: throws you about 6 tiles | `test_o_mushroom_bounces_6_tiles`, *toys* `test_mushroom_bounces` |
| `M` | steam geyser: fizzles 0.4 s, then puffs 0.9 s: standing on it throws you about 7 tiles; steam drawn | `test_M_geyser_throws_you_7_tiles_when_it_puffs` |
| `J` | flame jet: its own block and 2 above burn while on | `test_J_flame_jet_burns_its_block_and_2_above` |
| `H` | ladder: UP/DOWN climb, SPACE jumps off; its top is a ledge, DOWN climbs down from it | `test_H_ladder_climb_stand_on_top_and_climb_down` |
| `V` | vine: like a ladder; jump into it and press UP | `test_V_vine_grab_in_the_air` |
| `%` | climbing wall: hold UP (and toward it) to climb, slide down, wall jump | `test_percent_climbing_wall_up_climbs`, `test_hero_feel.gd` `test_wall_jump_on_climbing_wall` |
| `I` | ice: you slide | `test_I_ice_slides` |
| `u` | healing spring: full hearts, then empty for 60 s | `test_u_healing_spring_heals_then_refills` |
| `F` | secret wall: looks like rock, walk through | *toys* `test_secret_wall_lets_you_through` |
| `L` `G` | R on a lever opens every iron gate | *toys* `test_lever_opens_the_gates` |
| `P` | platform slides along its row of P's (2 tiles/s) and carries you | `test_P_platform_carries_you`, *toys* `test_platforms_move` |
| `U` | platform rides its column of U's and lifts you | `test_U_platform_lifts_you` |
| `R` | swinging vine: jump into it, LEFT/RIGHT pump, SPACE lets go | `test_R_swinging_vine_grab_and_let_go` |
| `z` `k` `c` `x` | Zombie, Skeleton, Ember Skull, Spider: hurt on touch; R kills | `test_monsters_zkcx_hurt_on_touch`, *toys* `test_sword_kills_a_zombie` |
| `C` | lantern shrine: checkpoint, full hearts, save | *toys* `test_dying_wakes_you_at_the_checkpoint` |
| `>` `<` | one-way door: shut until touched from the arrow's side | `test_one_way_doors` |
| `n` | shadow thorns: hurt until the flare burns them | `test_n_thorns_hurt_until_the_flare` |
| `i` `w` `f` | torch, window, banner: just for looks | `test_decor_iwf_is_just_for_looks` |

Not cave letters: `K` `D` `+` are the castle's (`boss/`). The README has no water letter, so there is no swim yet.

Differences from pygame on purpose: 1 heart per hazard (teen hearts), no stomp (the down-strike pogo
replaces it), touching a chest opens it, bumping ore takes it (pygame needs the pickaxe).

## Art (`cave_art.gd`)
Everything is drawn from C2's `art/` sheets. Tiles: `tiles_<theme>` (stone if the theme has none); rock
(`#`, and `F` without collision) picks `solid_<bits>` from its neighbours and redraws when a neighbour
breaks. Letter -> tile is in `CaveArt.MAP_TILE` (in the TileMap) and `CaveArt.SPRITE` (drawn on top,
animated at the sheet's fps). Parallax: `art/parallax/<theme>_{far,back,mid,front}` at 0, 0.25, 0.5 and
1.4x; the front rocks only scroll sideways and are 60 % see-through so they never hide the floor.
Monsters: z `barrow_wight`, k `bone_crawler`, c `ember_imp`, x `cave_bat`; hurt = white flash, telegraph =
attack pose pulsing red. Hero: `hero_side`, animation from its state. Still drawn in code: shadow thorns
`n`, the `<` `>` markers, geyser steam, ropes, arrows.

## Juice (`cave_juice.gd`, gameplay §4, same numbers as the realm)
Sword hit: 3 f stop, shake 1 px/4 f, sparks, white flash. Kill: 6 f, 2/6, the monster's `poof` + light
motes. Hurt: 10 f (none on the last heart), 5/12, red screen edge, red hero flash. Kingsfall: shake 8/20 +
dust. Hard landing (> 8 t/s): dust. Broken rock: chips. Pogo and sent-back arrows: sparks. Shake uses
`Juice.Shake` (off with `UiSettings.screen_shake`). Hit-stop pauses the whole cave, trap clock included.

## The cave robot (`robot/cave_robot.gd`)

Plays a cave with real physics: it only presses the Hero's buttons. It plans a route over cells you
can stand in (walk, drop, jump, ride a mushroom or geyser, climb, sink through a crumbly ledge, dig
cracked rock on foot), does one move, sees where it really landed, and plans again. It pulls a lever
when a gate is in the way and waits out the trap clock under spikes and jets.
`tests/test_cave_robot.gd` has it beat stone 1 and 3 and classic 05, 07 and 12 (about 15 s).
Not yet: ropes, the dash and `%` wall climbs, so stone 2 and most classic caves are out of its reach.
