# Teen Shadowfall: gameplay spec (Wave A, W-A3)

**Recommendation.** Keep the two views and the Shadow King story. Make both views real-time. The overworld plays like an action-adventure: free 8-way walking, a sword arc, a roll, and items that open new paths. The caves become a tight side-view platformer with a 3-tile jump, a down-strike pogo, a dash and abilities that gate rooms. Cut the turn-based map fight, XP levels, lives, food and sword wear. Seven lieutenants guard the 7 Light Stones, and each stone gives one ability that works in **both** views. The gloom keeps growing, and every stone pushes it back for good. Assist options sit in the menu and carry no penalty.

The numbers below are engine-agnostic (tiles, seconds, frames at a fixed 60 fps). `spikes/gameplay/feel.py` holds them, `play.py` lets you feel them, and `check_feel.py` measures them (all pass, see §4).

## 1. What the references teach (study only; nothing copied)

| Principle | Seen in | What we take | Source |
|---|---|---|---|
| Full control: every hit avoidable "until the last second"; jump cut on release | Hollow Knight | jump cut, no slide-y run, telegraphs ≥ 0.4 s | [Game Informer: making of HK](https://www.gameinformer.com/2018/10/16/the-making-of-hollow-knight) |
| Dash cancels vertical motion; 1 air dash, reset by landing / wall / pogo | HK | same reset rule | [Fextralife: dash](https://hollowknight.wiki.fextralife.com/Mothwing+Cloak), [wall jump](https://hollowknight.wiki.fextralife.com/Mantis+Claw) |
| Heal by spending meter gained from hits (11 per hit, 33 per heal, ~0.9 s channel) | HK | the Lumen meter: 3 hits = 1 heal, 0.9 s | [Fextralife: Soul](https://hollowknight.wiki.fextralife.com/Soul), [wiki: Focus](https://hollowknight.wiki/w/Focus) |
| Death leaves a ghost holding your money; die again before you reach it and the money is gone | HK, Shovel Knight (~25% as bags) | "Lost Light" holds your gold (Assist can turn it off) | [Fextralife: Shade](https://hollowknight.wiki.fextralife.com/Shade), [Wikipedia: SK](https://en.wikipedia.org/wiki/Shovel_Knight) |
| Charms: 3 notches at start, 11 max, swapped only at a bench | HK | Sigils: 3 slots, 6 max, swapped at a lantern | [Fextralife: Charms](https://hollowknight.wiki.fextralife.com/Charms) |
| The map is bought, then filled in as you explore; pins mark places | HK | each cave's map fills in as you go (no quill needed); pins | [Cornifer](https://hollowknight.wiki.fextralife.com/Cornifer), [Map & Quill](https://hollowknight.wiki.fextralife.com/Map+and+Quill) |
| Abilities gate areas (dash → gaps, claw → shafts, wings → high areas, tear → acid) | HK | 7 abilities, each with a visible gate tile | [Fextralife: Abilities](https://hollowknight.wiki.fextralife.com/Abilities) |
| Down-thrust pogo is the core verb; bounce chains as set pieces | Shovel Knight | DOWN+R in the air = down strike | [Kotaku: modernizing NES design](https://kotaku.com/how-shovel-knights-developers-modernized-nes-game-desig-1829767941) |
| Jump ~4.5 tiles on a 15-tile-tall screen (~30% of the screen); gaps sit a few tiles under the max | SK | jump = 3.3 tiles on an ~11-tile-tall view (same ~30%) | [Plague mobility design](https://www.gamedeveloper.com/design/shovel-knight-plague-of-shadows-mobility-design), [Breaking the NES](https://www.gamedeveloper.com/design/breaking-the-nes-for-shovel-knight) |
| ~26 rooms per stage; ~5 enemies + ~5 objects; teach a mechanic, then twist it; no one-off mechanics; the stage prepares you for its boss | SK | the cave rule in §8 (levels worker owns layouts) | [Specter level-design deep dive](https://www.yachtclubgames.com/blog/specter-of-torment-level-design-deep-dive-1-5) |
| Bosses: 3–4 attacks, early ones simpler, design doc before code; secondary motion makes them readable | SK | boss rules in §6 | [Game Developer: SK bosses](https://www.gamedeveloper.com/design/how-yacht-club-games-created-shovel-knight-s-baz-mole-knight-and-king-knight-bosses) |
| Walk 1.5 px/frame (~5.6 tiles/s at 16 px); boots dash 2.7× walk; spin charge 48 frames; hurt blink 58 frames | A Link to the Past | overworld numbers in §3 | [movement guide](https://gamertagmythras.com/blog/zelda-a-link-to-the-past/alttp-movement-speed-guide), [zelda3 decompile](https://github.com/snesrev/zelda3/blob/master/src/player.c) |
| Items open the world (glove → rocks, flippers → water, hammer → pegs); heart pieces in secrets | ALttP | ability gates + heart shards on the overworld | [Zelda Dungeon: items](https://zeldadungeon.net/wiki/A_Link_to_the_Past_Items), [heart pieces](https://www.zeldadungeon.net/Zelda03HeartContainers.php) |
| Coyote 0.1 s, apex half-gravity, air control ×0.65, dash 0.15 s, 3-frame freeze on dash | Celeste (feel baseline) | coyote 6 f, apex ×0.6, air ×0.67 | [Celeste Player.cs](https://github.com/NoelFB/Celeste/blob/master/Source/Player/Player.cs), [Celeste & Forgiveness](https://maddymakesgames.com/articles/celeste_and_forgiveness/) |
| Hit-stop scales with damage and is capped | Sakurai | hit 3 f, kill 6 f, hurt 10 f | [Sakurai on hitstop](https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/) |

From the images: Shovel Knight's overworld is a node map whose fog lifts as stages fall, and its HUD is a thin strip with only health and gold. Hollow Knight's area map draws rooms as outlined corridors, marks NPCs and benches with icons, and greys out the parts you haven't explored. Both ideas carry into §7 and the cave map.

## 2. Current mechanics: keep, change, cut

| Now (phase-2) | Verdict | Teen version |
|---|---|---|
| Cave platformer (`caves.py`: run 6, jump 2.45 tiles, coyote 0.1, buffer 0.12, wall jump on `%` only, ledge hang, crawl, ladders, vines, ice, platforms, geysers, jets, lava rise) | **Keep + retune** | numbers in §4. Wall jump on any wall once you have the Grip ability. The level toys all stay. |
| Ground pound (DOWN in the air) | **Change** | becomes the down strike (DOWN+R): pogo off enemies, spikes and lamps. The Quake ability adds a heavy slam that breaks cracked floors. |
| Map fight box + timing bar (`phase2/fight.py`) | **Cut** | real-time sword on the map. The timing bar moves to the forge only. |
| Smooth map walking, monsters roam, chase and give up (`smooth.py`, `monsters.py`) | **Keep** | add contact damage, knockback and telegraphed attacks |
| XP, level-up cards, `POWERS` | **Cut / change** | the powers become Sigils (§5). Growth comes from heart shards, forge tiers, sigils and abilities. |
| Lives, game over, food, sword durability, armor points | **Cut** | checkpoints + Lost Light, the Lumen heal, a sword that never breaks |
| 7 Light Stones, gloom 0→1 over 60 min, each stone −0.25 (`gloom.py`, `main_quest.py`) | **Keep + extend** | gloom tiers and a falling cap (§7) |
| Waystones, villages, shop, forge, quests, save | **Keep** | waystones become lanterns: checkpoint, heal, fast travel |
| Shadow King: glow → slash → sword stuck = punish, floor fireballs, angry at 50% (`throne.py`) | **Keep as phase 1** | + 2 new phases (§6) |
| Nightfall Hollow (3 shadow caves), castle (5 levels), Sunfang | **Keep** | Sunfang is forged from the 7 stones at the castle gate |

## 3. Controls (R = attack everywhere; every key can be remapped)

| Action | Keyboard | Gamepad (Xbox / PS) | Side view | Overworld |
|---|---|---|---|---|
| Move | Arrows | L-stick, D-pad | run, climb | 8-way walk |
| Jump | SPACE (hold = higher) | A / ✕ | jump, wall jump, double jump | talk / read (contextual) |
| **Attack** | **R** (UP+R up, DOWN+R down strike in the air) | X / □ | sword | sword arc; hold 0.8 s to spin |
| Dash / roll | SHIFT | RB or RT / R1 or R2 | dash | roll (i-frames) |
| Shoot | F | Y / △ | bow | bow |
| Interact | G | B / ○ | dig, chest, lever | open, push |
| Heal (hold) | Q | LB / L1 | Lumen heal | Lumen heal |
| Tool | E | LT / L2 | grapple / lantern | grapple / lantern |
| Map · Pause | TAB · ESC | View · Menu | cave map | world map |

An input buffer covers jump (8 f), attack (6 f) and dash (6 f). The stick dead zone is 0.25, and the stick runs at full speed past 0.6. There is no analog walk speed in side view.

## 4. Feel numbers

**Side view, measured by `check_feel.py`** (the formula is g = 2h/t², v₀ = 2h/t).

| Move | Setting | Measured |
|---|---|---|
| Run | 7.5 t/s; 0→max 6 f; stop 5 f; air accel ×0.67 | 6 f / 5 f ✓ |
| Full jump | h 3.4, t_apex 0.38 s → g 47.1, v₀ 17.9; fall gravity ×1.6; apex (\|vy\|<2.5, held) ×0.6; max fall 20 | **3.29 tiles**, 0.70 s airtime ✓ (clears 3 blocks) |
| Short hop | release while rising: vy ×0.45 | 1.48 tiles on a 4-frame tap ✓ (clears 1 block) |
| Running jump | flat ground | 5.4 tiles of gap ✓ |
| Coyote / buffer | 6 f / 8 f | n/a |
| Double jump (ability) | +2.25 tiles at any time in the air | 5.4 tiles total ✓ |
| Dash (ability) | 30 t/s for 11 f, no gravity, 21 f cooldown, 1 per airtime | 5.1 tiles ✓ |
| Wall slide / wall jump | slide 4.5 t/s; jump (9 out, 15 up); 8 f no steer back | n/a |
| Attack R | 2 f startup, 5 f active, 8 f recovery (0.25 s); reach 1.5 tiles | n/a |
| Down strike / pogo | on hit: vy −15.5; resets the air dash and double jump | 2.46 tiles ✓ |
| Recoil | a grounded side hit pushes you back 3 t/s for 4 f (the Steady sigil removes it) | n/a |
| Hurt | knockback (7 away, 9 up); 12 f no control; **i-frames 60 f** with flicker | n/a |

**Overworld**, in map squares:

| | Value |
|---|---|
| Walk | 5.5 sq/s (now 5.0); diagonals normalized; 0→max 5 f, stop 3 f |
| Sword arc | 3 + 6 + 8 f; reach 1.25 sq; 100° arc |
| Spin | hold R 48 f (walk ×0.6 while charging); 360°, 1.5 sq reach, 2× damage |
| Roll (Dash ability) | 17.5 sq/s for 12 f = 3.5 sq; i-frames f2–f9; 27 f cooldown |
| Enemy hit | knockback 1.5 sq over 6 f (heavy enemies 0.5) |
| You hurt | knockback 2 sq, 10 f lock, 60 f i-frames |

**Juice (both views).** Hit-stop freezes the game for a few frames. Shake is in base-resolution pixels, falls off linearly and has an OFF switch.

| Event | Hit-stop | Shake (px, frames) | Other |
|---|---|---|---|
| Sword hits | 3 f | 1, 4 | enemy flashes white 4 f |
| Kill | 6 f | 2, 6 | burst of light motes |
| You get hurt | 10 f | 5, 12 | screen edge pulses red; rumble 0.3 for 150 ms |
| Heavy slam / boss lands | 0 | 8, 20 | rumble 0.6 |
| Boss phase change | 20 f | 6, 30 | slow-mo ×0.5 for 0.4 s |

## 5. Health, heal, death, growth

| System | Spec |
|---|---|
| Hearts | 5 at start, 10 max. 4 heart shards = +1 heart (20 shards hidden in secrets and side quests). Bosses hit for 2, others for 1. |
| Lumen heal | The meter holds 3 charges. 3 sword hits fill 1 charge; an arrow hit fills ⅓ of that. Hold Q for 54 f standing still to heal 1 heart. A hit cancels the heal and wastes the charge. |
| Checkpoints | **Lanterns**: full heal, save, swap sigils, the map updates, enemies come back. One at each cave mouth and one before each boss door. **Ember posts** between them (respawn only) every 3–5 rooms, so no section is longer than about 90 s. Waystones count as lanterns. |
| Death | You wake at the last checkpoint. Your gold stays at the death spot as a **Lost Light**; touch it to get the gold back. Die again first and that gold is gone. Pits cost 1 heart and drop you at the last safe ground (as `FALL_DAMAGE` does now). |
| Sword | Never breaks. The forge (keep its timing bar) raises damage from 2 to 3, 4 and 5 using sun ore from caves; a Perfect forge adds a +5% crit. Sunfang (dmg 7) is the last tier. |
| Sigils | 3 slots, then +1 at stones 2, 4 and 6 (6 max), swapped at lanterns. From the old powers: Keen Edge (+1 dmg, 3 slots), Hardy (+1 heart, 2), Springstep (+0.5 tile jump, 1), Swiftfoot (run 8.5, 1), Fortune (+50% gold and rings, 1), Forager (heal charges fill 33% faster, 1), Sharpshooter (arrows +1 dmg and +10 ammo, 2), Long Edge (+25% reach, 2), Steady (no recoil, half knockback, 1), Lantern Heart (+1 heal charge, 2). |

## 6. Enemies and bosses

HP is in sword hits at forge tier 1 (damage 2). Every attack has a telegraph.

| Enemy | View | HP | Behaviour | Telegraph | Counter |
|---|---|---|---|---|---|
| Slime | both | 1 | hops toward you | squash 20 f | anything |
| Spider | both | 2 | side: drops on a thread; top: lunge | rear-up 24 f | pogo, roll aside |
| Zombie | both | 3 | slow walk, grab lunge | arms up 30 f | hit, back off |
| Skeleton | both | 2 | keeps 4–7 tiles away; arrows 9 t/s every 2.2 s | bow glow 1.2 s (now) | **R reflects arrows** |
| Ember Skull | both | 1 | floats in, flares 1.5 s, blast 2.2 tiles | flare | pogo it before it flares, or dash away |
| Sea Serpent | top | 3 | surfaces, spits | ripples 40 f | hit it while it's up |
| Scorpion | both | 4 | shield in front, tail strike | tail raise 24 f | hit after the strike or from behind |
| Frost Wolf | top | 3 | packs of 2–3: circle, then lunge | crouch 20 f | roll through the lunge |
| Bog Lurker | both | 5 | waits under the mud, then rises | bubbles 40 f | the Lantern shows it |
| Shade Wraith | both | 4 | gloom tier ≥ 2, at night only; drifts through walls; only hurt in light | fades in 30 f | Lantern / light zones |

Gloom tier 3 adds **shadow-touched** elites: a purple rim, +50% HP, telegraphs 20% shorter.

**Boss rules.** Each phase has at most 3 attacks. Telegraphs are ≥ 30 f (≥ 20 f when angry), and every attack leaves a punish window of ≥ 0.8 s. A boss has a 2-heart hit, a health bar split into phases, and a lantern at the door, so a retry takes under 10 s. A first-time teen should win in 2–6 tries. The boss uses its dungeon's ability or toy, so the cave prepares you for it.

| Stone · land | Lieutenant (original) | Attacks | Phase 2 twist | Gives |
|---|---|---|---|---|
| Dawn · Home Meadow | **Thornwarden**, a bramble stag | charge (lowered antlers 36 f), thorn burst, stomp | the arena edges grow thorns | Dash |
| Leaf · Whispering Woods | **Loom Widow** | ceiling drop, web shot (sticky floor), spawns 2 spiderlings | cuts her threads and swings | Grapple Thread |
| Tide · Great Lake | **Bellwarden**, a drowned bell-keeper | toll wave (jump it), water spout columns, bell slam | the room floods half-way | Tide Charm (swim, dive) |
| Crown · Old Ruins | **Rust Regent**, an empty armor on a throne | shield wall (hit from above or behind), lance thrust, armor rain | splits into 3 animated pieces | Grip (wall jump on any wall) |
| Frost · Frost Peaks | **Rime Matriarch**, a great wolf | ice-floor dash, frost breath cone, howl brings 2 wolves | the floor becomes all ice | Skyhop (double jump) |
| Sun · Sunscorch Desert | **Glass Wyrm** | burrow and erupt (sand ripples 40 f), glass shard arc, tail sweep | cracked glass pillars to smash | Quake (heavy slam, breaks cracked stone) |
| Moon · Murk Swamp | **Mire Lantern**, a lure in the dark | lights out (only its lure glows), mud grab, wisp swarm | you must carry your Lantern | Dawn Lantern (lights, burns shadow thorns) |

**The Shadow King** (`throne.py` today) has 3 phases and 90 HP at Sunfang damage. Each light shard from the castle still adds +1 damage.

1. **Blade (100–60%).** Today's fight: glow 0.8 s → slash → sword stuck 1.0 s (the punish window) → pull out; floor fireballs to jump over.
2. **Eclipse (60–30%).** The room goes dark, and you see only your lantern's circle and his glowing eyes. He shadow-steps (vanish 36 f, then a floor shimmer for 30 f before he comes up). Each time he calls an echo of 2 lieutenants' signature attacks, chosen at random. His shadow orbs can be pogoed.
3. **Fall (30–0%).** The floor breaks into platforms over the void, so the fight turns vertical. His crown floats free: pogo it 3 times while he sweeps a beam (a 36 f warning line). The last blow is a Sunfang strike in a short cut-scene.

## 7. The progression loop

```
            ┌──────────── overworld (top-down, free roam, secrets, side quests) ─────────────┐
            │  find a land's Deep (main cave) ──► side-view rooms: ember posts, map fills in │
            │        ▲                                   │                                   │
 new paths ◄┤        │                                   ▼                                   │
 + old caves│  ability opens gates in BOTH views ◄── lieutenant ──► Light Stone              │
 re-opened  │                                                            │                   │
            └─ gloom pushed back · land lit · new NPCs/shop stock ◄──────┘                   │
 7 stones ──► Portal ──► Nightfall Hollow (3 shadow caves, all abilities) ──► castle (5 levels) ──► Shadow King
```

| Tier | Open lands (any order inside a tier) | Needs |
|---|---|---|
| 1 | Home Meadow (tutorial) | n/a |
| 2 | Whispering Woods, Great Lake | Dash |
| 3 | Old Ruins, Frost Peaks | Grapple (Ruins) / Tide (Peaks) |
| 4 | Sunscorch Desert, Murk Swamp | Grip + Skyhop |

Each land has one **Deep** (the dungeon: about 12–20 rooms, 1 lieutenant) and 1–2 small **Mines** (1–3 rooms: a heart shard, a sigil or sun ore). The **map** uses a different rule in each view. The overworld stays fully visible, as it is now. A cave map fills in room by room, and a "?" pin marks a gate you can't pass yet. Roughly 40% of secrets need an ability you get later, so you come back.

**Darkening world.** Gloom grows to 1.0 in **90 min** of play (now 60). Each stone pushes it back 0.25 **and** lowers the cap by 0.1, so with 7 stones it can't pass 0.3. It ends at 0 when the King falls.

| Gloom | Effect |
|---|---|
| < 0.25 | normal |
| 0.25 | nights last 1.5× longer; +25% monsters at night |
| 0.5 | Shade Wraiths appear at night; shadow thorns block 1–2 side paths (the Lantern burns them) |
| 0.75 | shadow-touched elites; even daytime is dim (the art worker owns the look) |

A land whose stone you hold stays lit: no wraiths, no elites, and its lanterns glow.

## 8. Difficulty and Assist

The **Standard** mode is aimed at ages 12–16. A cave room teaches its toy where failing is safe, then tests it. There is no instant death except pits (1 heart). A section between checkpoints takes ≤ 90 s.

**Assist** opens from the pause menu at any time, has no penalty and no badge, and each switch works alone:

| Setting | Options |
|---|---|
| Damage taken | 100% · 50% · none |
| I-frames | 1.0 s · 1.5 s |
| Game speed | 100 · 90 · 80 · 70% |
| Pogo stance | off · on (hold DOWN in the air to pogo, no R) |
| Air dashes | 1 · unlimited |
| Lost Light | on · off (keep your gold) |
| Gloom | on · paused |
| Boss | normal · "skip fight" offered after 5 losses |

**Accessibility** settings sit apart from Assist and are always offered: screen shake full/low/off, flashes low, rumble on/off, hold-to-toggle for heal and charge.

## 9. Wave B gameplay tasks (one file each, no file shared by two tasks)

Rules: every task owns its module and its own test file. Its tuning numbers sit at the top of that module with kid-editable comments, as now. G0 lands first and on its own, and it is the only shared contract. G20 wires everything together last. The names give the pygame path; a Godot build uses the same name with `.gd`. A task may *read* G0 but never edits it; changes to it go through the coordinator.

| ID | Task | Owns | Needs | Size |
|---|---|---|---|---|
| G0 | Gameplay contract: actions, event names (hit/kill/hurt/pogo/heal/checkpoint), body fields, units | `gameplay/contract.py` | none | S |
| G1 | Input: keyboard, gamepad, remap, buffers, dead zone | `gameplay/input_map.py` | G0 | M |
| G2 | Juice: hit-stop, shake, flash, rumble, accessibility switches | `gameplay/juice.py` | G0 | S |
| G3 | Side body: run, jump, coyote, buffer, wall, dash, double jump, swim (port `spikes/gameplay/feel.py`) | `gameplay/side_body.py` | G0 | M |
| G4 | Side combat: sword boxes, down strike/pogo, recoil, hurt, i-frames, arrow reflect | `gameplay/side_combat.py` | G0 | M |
| G5 | Overworld body + combat: walk, roll, sword arc, spin, bow; removes the fight box | `gameplay/top_play.py` | G0 | M |
| G6 | Vitals: hearts, shards, Lumen heal, Lost Light | `gameplay/vitals.py` | G0 | S |
| G7 | Checkpoints: lanterns, ember posts, respawn, enemy reset | `gameplay/checkpoints.py` | G0 | S |
| G8 | Abilities + gate tiles (both views), item-get | `gameplay/abilities.py` | G0 | M |
| G9 | Progression: tiers, stone order, gloom tiers and cap, lit lands | `gameplay/progression.py` | G0 | S |
| G10 | Sigils: slots, costs, effects as modifiers | `gameplay/sigils.py` | G0 | S |
| G11 | Cave map: fill-in, pins, "?" gate marks | `gameplay/cave_map.py` | G0 | S |
| G12 | Side enemies A: Slime, Spider, Zombie, Skeleton, Ember Skull | `gameplay/enemies_side_a.py` | G0 | M |
| G13 | Side enemies B: Scorpion, Bog Lurker, Shade Wraith, elites | `gameplay/enemies_side_b.py` | G0 | M |
| G14 | Overworld enemies: all 10 kinds' top-down AI | `gameplay/enemies_top.py` | G0 | M |
| G15 | Bosses 1–3: Thornwarden, Loom Widow, Bellwarden | `gameplay/bosses_early.py` | G0 | L |
| G16 | Bosses 4–5: Rust Regent, Rime Matriarch | `gameplay/bosses_mid.py` | G0 | L |
| G17 | Bosses 6–7: Glass Wyrm, Mire Lantern | `gameplay/bosses_late.py` | G0 | L |
| G18 | Shadow King, 3 phases | `gameplay/shadow_king.py` | G0 | M |
| G19 | Assist + difficulty settings | `gameplay/assist.py` | G0 | S |
| G20 | Robot reach table for the new moves (levels and solver share it) | `gameplay/reach.py` | G3 | S |
| G21 | Integration: wire G1–G20 into the game loop, one worker, last | the main loop | all | M |

## 10. Open questions for the user

1. **Cut** XP levels, lives, food and sword wear, and replace them with sigils, checkpoints and the Lumen heal? (My pick: yes.)
2. The jump grows from 2.45 to **3.3 tiles**, which means every current cave needs retuning. Rebuild the caves with the new numbers, or keep the old jump? (My pick: the new jump; the levels worker retunes.)
3. Does Standard mode drop your gold as a Lost Light when you die, or keep it with no penalty? (My pick: Lost Light on, and Assist can turn it off.)
4. Should Assist offer "skip fight" after 5 boss losses? (My pick: yes.)
5. Add a harder post-game mode (fewer ember posts, ×2 damage)? (My pick: later, not in Wave B.)

## 11. Not verified

- No human has played the numbers yet. `check_feel.py` checks only the math, and `play.py` ran headless for 120 frames with no gamepad attached.
- No source gave Hollow Knight's or Shovel Knight's physics numbers (run, gravity, dash distance, i-frames, hit-stop); fan wikis also blocked fetches, so those rows are design picks, not copies. The Hollow Knight heal time (0.89 s) and attack cooldown (0.41 s) come from wiki search snippets. The Link to the Past values come from a third-party guide and the decompile.
- I did not check whether the 7-ability gating can be beaten (a robot pass is G20 + the levels worker), and I did not check how the overworld roll interacts with the current `smooth.py` collision.
- Durations: ~5–6 h is an estimate (7 Deeps × ~25 min + overworld), not timed.
