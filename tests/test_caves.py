"""
Caves: your bigger body, monsters, digging, treasure chests, crumbly ledges, spikes
and lava, bouncy mushrooms, gems, how a cave looks (its theme), and which cave goes
under which Mine.

Most tests draw their own little cave right here, so it doesn't matter how the
real caves in caves.py look.
"""

import random

import pytest

import cave_files
import caves
import rules
from helpers import DT, cave_from, feet, new_world, ok, run

# A plain room: 14 rows, the floor is row 13, and you start on row 12 (S)
FLAT = ["##############",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        ".............#",
        ".............#",
        "..S..........#",
        "##############"]


def flat_with(row12, row11=None, extra=None):
    """The plain room, with row 12 (and maybe row 11, or other rows) drawn differently."""
    rows = list(FLAT)
    rows[12] = row12
    if row11:
        rows[11] = row11
    for r, line in (extra or {}).items():
        rows[r] = line
    return rows


def hand_drawn_number(text):
    """Which hand-drawn cave this is (0 = the first file in levels/caves), or None if it isn't one of them.
    A hand-drawn cave without a diamond has a treasure chest where the ore was, but it's the same cave."""
    for number, drawing in enumerate(caves.CAVE_LEVELS):
        if text in (drawing, caves.without_diamond(drawing)):
            return number
    return None


def mines_nearest_first(world):
    return sorted(world.cave_plan, key=lambda mine: (rules.distance(mine, world.start), mine))


# ===========================================================================
# Your body: how big you are and how high you jump
# ===========================================================================

def test_bigger_hero_stands_on_the_floor_and_jumps_2_blocks():
    world, cave = cave_from(FLAT)
    run(cave, 60)
    floor = 13 - caves.PLAYER_H
    ok(cave.you.on_ground and abs(cave.you.y - floor) < 1e-6,
       "the bigger Hero (%.2f x %.2f tiles) stands on the floor" % (caves.PLAYER_W, caves.PLAYER_H))
    start = top = cave.you.y
    for frame in range(60):
        cave.update(DT, {"jump": True, "jump_pressed": frame == 0})
        top = min(top, cave.you.y)
    ok(2.0 < start - top < 3.0, "full jump rises %.2f tiles: 2 blocks yes, 3 no" % (start - top))


# ===========================================================================
# Monsters
# ===========================================================================

def test_a_zombie_walks_over_and_hurts_you():
    world, cave = cave_from(flat_with("..S..z.......#"))      # 3 blocks away: close enough that it comes after you
    zombie = cave.monsters[0]
    start_x, health = zombie.x, world.player.health
    knocked = False
    for _ in range(600):
        cave.update(DT, {})
        if world.player.health < health:
            knocked = cave.you.safe_time > 0 and abs(cave.you.vx) > 0
            break
    ok(zombie.x < start_x and world.player.health < health,
       "a Zombie walks over and hurts you (health %d -> %d)" % (health, world.player.health))
    ok(knocked, "getting hit knocks you back and makes you blink")
    after_hit = world.player.health
    for _ in range(int(caves.SAFE_TIME * 60) - 10):
        cave.update(DT, {})
    ok(world.player.health == after_hit, "you can't be hurt again while blinking")


def test_jumping_on_a_spiders_head():
    world, cave = cave_from(flat_with("..S......x...#"))
    spider = cave.monsters[0]
    spider.speed, spider.reload = 0, 99
    cave.you.x, cave.you.y, cave.you.vy = spider.x + 0.1, spider.y - 2, 0
    health = spider.info.health
    for _ in range(60):
        cave.update(DT, {})
        if cave.you.vy < 0:
            break
    ok(spider.info.health == health - caves.STOMP_DAMAGE and cave.you.vy < 0,
       "jumping on a Spider's head hurts it by %d and bounces you up" % caves.STOMP_DAMAGE)


def test_swinging_your_sword_at_a_zombie():
    world, cave = cave_from(flat_with("..S.z........#"))
    zombie = cave.monsters[0]
    zombie.speed = 0
    cave.you.x = zombie.x - caves.PLAYER_W - 0.2
    cave.you.facing = 1
    run(cave, 5)
    health, durability = zombie.info.health, world.player.swords[0].durability
    run(cave, 1, use_pressed=True)
    ok(zombie.info.health < health and world.player.swords[0].durability == durability - 1,
       "X swings the sword: Zombie %d -> %d, sword wears down" % (health, zombie.info.health))
    for _ in range(30):
        run(cave, 25, use_pressed=True)
        if zombie in cave.monsters:
            cave.you.x = zombie.x - caves.PLAYER_W - 0.2      # stay right next to it
    ok(zombie not in cave.monsters and world.monster_quest.progress == 1 and world.player.xp > 0,
       "beating it counts for the quest and gives XP")


def overlap(a, b):
    """How much two bodies overlap side to side (0 = they don't)."""
    return max(0.0, (a.w + b.w) / 2 - abs(a.center[0] - b.center[0]))


def test_a_chasing_zombie_stops_next_to_you_instead_of_inside_you():
    world, cave = cave_from(flat_with("..S..z.......#"))
    zombie = cave.monsters[0]
    world.player.health = world.player.max_health = 999          # let it hit you as much as it likes
    worst = 0.0
    for _ in range(300):
        cave.you.vx = 0
        cave.you.x = 2.0                                          # you stand still (no knockback)
        cave.update(DT, {})
        worst = max(worst, overlap(zombie, cave.you))
    ok(worst < 0.25, "the Zombie stays next to you, not inside you (worst overlap %.2f blocks)" % worst)


def test_a_monster_inside_you_slides_out_and_your_sword_hits_it():
    world, cave = cave_from(flat_with("..S.z........#"))
    zombie = cave.monsters[0]
    zombie.speed = 0
    cave.you.safe_time = 99                                       # you're blinking, so it can't push you away
    cave.you.x = zombie.x                                         # right on top of it
    cave.you.facing = -1                                          # facing the wrong way, even
    health = zombie.info.health
    run(cave, 1, use_pressed=True)
    ok(zombie.info.health < health, "the sword hits a monster that's right on top of you (%d -> %d)"
       % (health, zombie.info.health))
    zombie.stunned = 0
    run(cave, 40)
    ok(overlap(zombie, cave.you) < caves.TOUCH_DEPTH + 0.05, "it slides back out of you (overlap %.2f)" % overlap(zombie, cave.you))


def test_a_skeleton_shoots_arrows_at_you():
    world, cave = cave_from(flat_with("..S.....k....#"))
    health = world.player.health
    run(cave, 300)
    ok(world.player.health < health, "a Skeleton shoots arrows at you (health %d -> %d)" % (health, world.player.health))


def test_an_ember_skull_flares_up_then_blows_up():
    world, cave = cave_from(flat_with("..S...c..BB..#", ".........BB..#"))
    skull = cave.monsters[0]
    health, saw_fuse = world.player.health, False
    for _ in range(400):
        cave.update(DT, {})
        saw_fuse = saw_fuse or skull.fuse is not None
    ok(saw_fuse and skull not in cave.monsters and world.player.health < health,
       "an Ember Skull flares up, then BOOM hurts you (health %d -> %d)" % (health, world.player.health))


def test_an_ember_skulls_blast_breaks_cracked_rock():
    world, cave = cave_from(flat_with("..S..c...BB..#"))
    skull = cave.monsters[0]
    skull.x, skull.fuse = 8.2, 0.01
    cave.you.x = 5.6
    run(cave, 5)
    ok(cave.map[12][9] == "." and cave.map[11][9] == ".", "an Ember Skull's blast breaks cracked rock next to it")


def test_monsters_turn_around_at_the_edge_of_a_ledge():
    world, cave = cave_from(flat_with("..S..........#", extra={8: "#....===.....#"}))
    zombie = cave.add_monster("Zombie", 7, 6)
    cave.you.x = 1
    run(cave, 600)
    ok(zombie.y < 8 and zombie in cave.monsters,
       "a Zombie walking on a ledge turns around at the edge instead of falling")


def wide_room(row12, extra=None):
    """A long, plain room (24 blocks wide), with row 12 drawn the way the test wants."""
    rows = ["#" * 24] + ["#" + "." * 22 + "#"] * 11 + [row12, "#" * 24]
    for r, line in (extra or {}).items():
        rows[r] = line
    return rows


def watch(cave, m, frames, **keys):
    """Run the cave and say how far left and right this monster's middle went."""
    xs = []
    for _ in range(frames):
        run(cave, 1, **keys)
        xs.append(m.center[0])
    return min(xs), max(xs)


def near_its_spot(m, low, high):
    return m.home - caves.PATROL_RANGE - 0.2 < low and high < m.home + caves.PATROL_RANGE + 0.2


def test_monsters_walk_back_and_forth_by_their_spot():
    world, cave = cave_from(wide_room("#.S.................z..#"))
    zombie = cave.monsters[0]
    low, high = watch(cave, zombie, 60 * 20)            # 20 seconds, with you far away
    ok(near_its_spot(zombie, low, high),
       "a Zombie stays within %g blocks of its spot (it went %+.1f to %+.1f)"
       % (caves.PATROL_RANGE, low - zombie.home, high - zombie.home))
    ok(high - low > 2 * caves.PATROL_RANGE - 1,
       "...and really walks back and forth (%.1f blocks from end to end)" % (high - low))


def test_a_patrol_turns_at_walls_and_lava():
    world, cave = cave_from(wide_room("#.S......~....z#.......#"))
    zombie = cave.monsters[0]
    low, high = watch(cave, zombie, 60 * 20)
    ok(zombie in cave.monsters and high < 15 and low > 10,
       "a Zombie between lava and a wall turns at both (it went from %.1f to %.1f)" % (low, high))


def test_monsters_only_come_after_you_when_you_are_close():
    world, cave = cave_from(wide_room("#.S.................z..#"))
    zombie = cave.monsters[0]
    cave.you.x = zombie.home - 5.5 - cave.you.w / 2       # 5.5 blocks away: it doesn't care
    low, high = watch(cave, zombie, 60 * 6)
    ok(near_its_spot(zombie, low, high) and world.player.health == world.player.max_health,
       "you 5.5 blocks away: the Zombie keeps patrolling (%+.1f to %+.1f from its spot)"
       % (low - zombie.home, high - zombie.home))
    health = world.player.health
    cave.you.x = zombie.center[0] - caves.CHASE_RANGE + 0.2 - cave.you.w / 2   # step in close: now it comes for you
    for _ in range(60 * 3):
        run(cave, 1)
        if world.player.health < health:
            break
    ok(world.player.health < health, "you %g blocks away: the Zombie comes after you and hurts you"
       % caves.CHASE_RANGE)
    cave.you.x, cave.you.safe_time = 2, 99                 # run far away again
    run(cave, 60 * 8)
    low, high = watch(cave, zombie, 60 * 8)
    ok(near_its_spot(zombie, low, high),
       "you ran away: the Zombie goes back to patrolling its spot (%+.1f to %+.1f)"
       % (low - zombie.home, high - zombie.home))


def test_monsters_only_see_you_on_their_own_level():
    ledge = "#" + "." * 11 + "=" * 5 + "." * 6 + "#"              # a ledge 2 blocks up, right next to the Zombie
    world, cave = cave_from(wide_room("#.S..........z.........#", extra={11: ledge}))
    zombie = cave.monsters[0]
    cave.you.x, cave.you.y = zombie.x + 1.5, 11 - caves.PLAYER_H    # up on the ledge, 1.5 blocks away
    low, high = watch(cave, zombie, 60 * 8)
    ok(feet(cave) == 11 and not zombie.chasing and near_its_spot(zombie, low, high),
       "you on a ledge 2 blocks up: the Zombie can't see you and keeps patrolling")
    cave.you.x, cave.you.y = zombie.x - 1.5, 13 - caves.PLAYER_H    # down on its floor, 1.5 blocks away
    health = world.player.health
    run(cave, 60 * 2)
    ok(world.player.health < health, "you jump down to its level: now it sees you and comes after you")


def test_monsters_above_you_dont_see_you():
    ledge = "#...." + "=" * 15 + "...#"                              # a long ledge 2 blocks up
    world, cave = cave_from(wide_room("#.S....................#", extra={11: ledge}))
    zombie = cave.add_monster("Zombie", 10, 12)                      # the Zombie patrols the ledge
    run(cave, 30)
    cave.you.x = zombie.x - 1                                         # you're right under it
    low, high = watch(cave, zombie, 60 * 6)
    ok(zombie.y + zombie.h == 11 and near_its_spot(zombie, low, high) and world.player.health == world.player.max_health,
       "a Zombie on a ledge 2 blocks above you doesn't come after you")


def test_a_skeleton_cant_see_you_above_or_below_it():
    ledge = "#" + "." * 8 + "=" * 14 + "#"
    world, cave = cave_from(wide_room("#.S.............k......#", extra={11: ledge}))
    skeleton = cave.monsters[0]
    for _ in range(60 * 3):
        cave.you.x, cave.you.y, cave.you.vy = skeleton.center[0] - 4, 11 - caves.PLAYER_H, 0   # on the ledge above it
        run(cave, 1)
    ok(skeleton.aim is None and not cave.arrows, "a Skeleton doesn't aim at you on a ledge above it")


def test_a_skeleton_draws_its_bow_before_its_first_arrow():
    world, cave = cave_from(wide_room("#.S.............k......#"))
    skeleton = cave.monsters[0]
    run(cave, 30)                                   # you're farther than SIGHT: it hasn't noticed you
    ok(skeleton.aim is None and not cave.arrows, "a Skeleton far away hasn't seen you yet")
    shots = []
    for frame in range(60 * 6):
        cave.you.x = skeleton.center[0] - 6         # stand 6 blocks away (it might have patrolled a bit)
        run(cave, 1)
        if frame == 0:
            ok(skeleton.aim is not None, "it sees you and starts drawing its bow")
        if cave.arrows:
            shots.append(frame + 1)
            cave.arrows = []
    first = shots[0] / 60
    ok(caves.SKELETON_AIM - 0.05 < first < caves.SKELETON_AIM + 0.1,
       "it waits %.2f s before its first arrow (SKELETON_AIM is %g s): time to get close!" % (first, caves.SKELETON_AIM))
    gap = (shots[1] - shots[0]) / 60
    ok(abs(gap - caves.ARROW_EVERY) < 0.1, "then it shoots every %.2f s, like ARROW_EVERY says" % gap)


# ===========================================================================
# Digging with your pickaxe
# ===========================================================================

def test_digging_through_a_cracked_wall():
    world, cave = cave_from(flat_with("..S..BB......#", "#....BB......#"))
    run(cave, 120, right=True)
    durability = world.player.pickaxe.durability
    run(cave, 1, use_pressed=True)
    ok(cave.map[11][5] == "." and cave.map[12][5] == "." and world.player.pickaxe.durability == durability,
       "X digs a 2-high cracked wall in one swing (the pickaxe doesn't wear down)")
    run(cave, 1, use_pressed=False)
    run(cave, 30, right=True)
    run(cave, 1, use_pressed=True)
    run(cave, 120, right=True)
    ok(cave.you.x > 7, "dig the next column too, and you can walk through")


def test_digging_down_through_the_floor():
    world, cave = cave_from(flat_with("..S..........#", extra={9: "#.....#BB#...#", 10: "#.....####...#"}))
    cave.you.x, cave.you.y = 7.1, 9 - caves.PLAYER_H
    run(cave, 20)
    was = cave.you.y
    run(cave, 1, use_pressed=True, down=True)
    run(cave, 60)
    ok(cave.map[9][7] == "." and cave.you.y > was + 0.5, "Down + X digs the floor under you and you drop through")


def test_mining_the_diamond_needs_a_pickaxe():
    world, cave = cave_from(flat_with("..S....*.....#", "#......#.....#"))
    world.player.pickaxe = None
    run(cave, 120, right=True)
    run(cave, 1, use_pressed=True)
    ok(cave.map[12][7] == "*" and any("need a pickaxe" in words for words, _ in world.messages),
       "no pickaxe: the ore won't budge, and it tells you why")
    world.player.pickaxe = rules.Tool("Pickaxe", 1)
    run(cave, 25)
    run(cave, 1, use_pressed=True)
    ok(world.player.diamonds == 1 and (0, 0) in world.cleared_mines and world.player.pickaxe is not None,
       "with a pickaxe: diamond mined, mine cleared - and even a nearly worn-out pickaxe doesn't break")


def test_the_pickaxe_lasts_forever():
    world, cave = cave_from(flat_with("..S..BBBBBBB.#", "#....BBBBBBB.#"))
    pickaxe = world.player.pickaxe = rules.Tool("Pickaxe", 1)   # even one that "should" break on the first dig
    for _ in range(10):
        run(cave, 1, use_pressed=False)
        run(cave, 30, right=True)
        run(cave, 1, use_pressed=True)
    dug = sum(cave.map[12][c] == "." for c in range(5, 12))
    ok(dug == 7 and world.player.pickaxe is pickaxe
       and pickaxe.durability == pickaxe.max_durability
       and not any("pickaxe broke" in words for words, _ in world.messages),
       "dig %d columns and the pickaxe is still like new" % dug)


# ===========================================================================
# Treasure chests
# ===========================================================================

def open_the_chest(world):
    world, cave = cave_from(flat_with("..S.T........#"), world)
    cave.you.x = 3.8
    run(cave, 5)
    monsters_before = len(cave.monsters)
    run(cave, 1, use_pressed=True)
    return cave, monsters_before


def test_x_opens_a_chest():
    world = new_world()
    cave, _ = open_the_chest(world)
    ok(cave.map[12][4] == "t" and any(kind == "loot" for _, kind in world.messages[-2:]),
       "X opens a chest and you get something: %r" % world.messages[-1][0])


def test_chests_hold_different_things_and_some_are_traps():
    seen = set()
    for seed in range(40):
        world = new_world(seed)
        world.rng = random.Random(seed)
        cave, monsters_before = open_the_chest(world)
        seen.add("trap" if len(cave.monsters) > monsters_before else world.messages[-1][0].split("!")[0])
    ok("trap" in seen and len(seen) >= 4, "chests hold different things, and some are traps: %s" % sorted(seen))


# ===========================================================================
# Crumbly ledges, spikes and lava
# ===========================================================================

def test_a_crumbly_ledge_falls_then_comes_back():
    world, cave = cave_from(flat_with("..S..........#", extra={10: "#....---.....#"}))
    cave.you.x, cave.you.y = 5.5, 10 - caves.PLAYER_H
    run(cave, 10)
    standing_on_it = cave.you.on_ground and cave.you.y < 10
    run(cave, int(caves.CRUMBLE_TIME * 60) - 15)
    still_on_it = cave.you.y < 10
    run(cave, 40)
    ok(standing_on_it and still_on_it and cave.you.y > 11,
       "a crumbly ledge holds you for %.1f s, then falls" % caves.CRUMBLE_TIME)
    run(cave, 240, right=True)
    ok(cave.map[10][5] == "-", "and it comes back a few seconds later")


@pytest.mark.parametrize("letter, damage, name", [("^", caves.SPIKE_DAMAGE, "spikes"), ("~", caves.LAVA_DAMAGE, "lava")])
def test_hazards_hurt_and_put_you_back_on_safe_ground(letter, damage, name):
    world, cave = cave_from(flat_with("..S...%s%s.....#" % (letter, letter)))
    health = world.player.health
    run(cave, 90, right=True)
    ok(health - world.player.health == damage and cave.you.x < 6,
       "%s: -%d health and you're put back on safe ground" % (name, damage))


# ===========================================================================
# Bouncy mushrooms and gems (in a tall cave)
# ===========================================================================

GROUND = caves.CAVE_HEIGHT - 2        # the row just above the floor, where you start


def tall_cave(ground_row, theme=None):
    """A tall cave (20 rows), with the row you stand on drawn your way."""
    rows = (["#" * 16] + ["#" + "." * 15] * (caves.CAVE_HEIGHT - 5) + ["." * 16] * 3 + ["#" * 16])
    rows[GROUND] = ground_row
    return ("theme: %s\n" % theme if theme else "") + "\n".join(rows)


def test_a_bouncy_mushroom_throws_you_up_high():
    world = new_world()
    cave = caves.Cave(world, (0, 0), tall_cave("..S...o........."))
    cave.you.x, cave.you.y = 5.9, GROUND - 5
    run(cave, 30)
    top = cave.you.y
    for _ in range(60):
        cave.update(DT, {})
        top = min(top, cave.you.y)
    height = GROUND - (top + caves.PLAYER_H)
    ok(height > 5, "a bouncy mushroom throws you up about %.1f blocks" % height)


def test_gems_give_xp_and_stay_collected():
    world = new_world()
    cave = caves.Cave(world, (0, 0), tall_cave("..S..$$$........"))
    xp, messages = world.player.xp, len(world.messages)
    run(cave, 120, right=True)
    ok(world.player.xp == xp + 3 * caves.GEM_XP and cave.map[GROUND][5:8] == list("...") and len(world.messages) == messages,
       "walking through 3 gems gives %d XP (without filling up the message log)" % (3 * caves.GEM_XP))
    ok(cave.changes.get((GROUND, 5)) == ".", "a collected gem stays collected")


# ===========================================================================
# How a cave looks: its theme
# ===========================================================================

def test_a_cave_can_start_with_a_theme_line():
    drawing = tall_cave("..S.............", theme="lava")
    ok(caves.level_theme(drawing) == "lava" and len(caves.parse_level(drawing)) == caves.CAVE_HEIGHT,
       "a cave can start with a 'theme:' line, and it isn't part of the map")


def test_every_hand_drawn_cave_has_a_real_theme():
    themes = [caves.level_theme(drawing) for drawing in caves.CAVE_LEVELS]
    ok(all(theme in caves.THEMES for theme in themes),
       "every hand-drawn cave looks like one of %s: %s" % (caves.THEMES, themes))


# ===========================================================================
# The cave plan: which cave goes under which Mine
# ===========================================================================

def test_every_mine_plays_a_cave_file():
    world = new_world()
    mines = mines_nearest_first(world)
    ok(len(mines) == sum(row.count("M") for row in world.map) and
       all(hand_drawn_number(world.cave_plan[mine]) is not None for mine in mines),
       "every one of the %d Mines plays a cave from a file in levels/caves" % len(mines))
    ok(rules.Game("Someone", seed=77).cave_plan == world.cave_plan, "a new game gives each Mine the same cave again")
    for spot, text in world.secret_mines.items():
        ok(text in caves.SECRET_CAVES, "the Secret Mine at %s plays a file in levels/secret" % (spot,))


def test_the_cave_files_go_from_the_nearest_mine_to_the_farthest():
    world = new_world()
    mines = mines_nearest_first(world)
    numbers = [hand_drawn_number(world.cave_plan[mine]) for mine in mines]
    files = len(caves.CAVE_LEVELS)
    ok(numbers == [i % files for i in range(len(mines))],
       "file 01 is under the nearest Mine, 02 under the next... and with more Mines than files they go round again")


def test_fewer_mines_than_cave_files_play_the_first_files():
    """A pretend map with 12 Mines in a row and 17 files: Mine i plays file i, so 13 to 17 are left over."""
    ok(len(caves.CAVE_LEVELS) == 17, "this test wants 17 cave files (found %d)" % len(caves.CAVE_LEVELS))
    home = (0, 0)
    mines = [(0, step) for step in range(1, 13)]
    plan = caves.plan_cave_files(list(reversed(mines)), home)
    ok([plan[mine] for mine in mines] == list(range(12)),
       "with 17 files and 12 Mines, Mine i plays file i: the classic map keeps caves 01 to 12")
    world = new_world()
    numbers = [hand_drawn_number(world.cave_plan[mine]) for mine in mines_nearest_first(world)]
    if len(numbers) == 12:
        ok(numbers == list(range(12)), "the classic map's 12 Mines play files 01 to 12, in order")


def test_more_mines_than_cave_files_use_the_files_again():
    """A pretend map with lots of Mines in a row: no cave is ever made up, the files just go round again."""
    files = len(caves.CAVE_LEVELS)
    home = (0, 0)
    mines = [(0, c) for c in range(1, 2 * files + 6)]            # nearest home first
    plan = caves.plan_caves(mines, home)
    ok(set(plan) == set(mines) and all(text in caves.CAVE_LEVELS for text in plan.values()),
       "%d Mines and %d files: every Mine still plays a file" % (len(mines), files))
    ok([caves.plan_cave_files(mines, home)[mine] for mine in mines] == [i % files for i in range(len(mines))],
       "counting from the nearest Mine: 01, 02 ... %02d, then 01 again" % files)
    ok(plan[mines[0]] == plan[mines[files]] == caves.CAVE_LEVELS[0], "Mine %d plays file 01 again" % (files + 1))
    few = mines[:5]
    numbers = [caves.plan_cave_files(few, home)[mine] for mine in few]
    ok(numbers == [0, 1, 2, 3, 4], "fewer Mines than files: Mine i plays file i, so the first 5 files: %s" % numbers)


def test_the_cave_pieces_are_gone():
    """Nothing in the game snaps a cave together any more: every cave is a file the editor can open."""
    for module in (caves, rules, cave_files):
        for name in ("CAVE_PIECES", "CAVE_STARTS", "CAVE_ENDS", "build_cave", "piece_rows", "game_pieces", "piece_names"):
            ok(not hasattr(module, name), "%s has no %s" % (module.__name__, name))
    world = new_world()
    files = caves.CAVE_LEVELS + caves.SECRET_CAVES
    for mine in list(world.cave_plan) + list(world.secret_mines):
        text = world.cave_text(mine)
        ok(any(text in (drawing, caves.without_diamond(drawing)) for drawing in files),
           "the cave under the Mine at %s comes from a file" % (mine,))


def test_caves_get_harder_every_few_steps_from_home():
    step = caves.CAVE_DISTANCE_STEP
    ok([caves.how_hard(d) for d in (0, step - 1, step, 2 * step - 1, 2 * step, 3 * step + 5)] == [1, 1, 2, 2, 3, 3],
       "caves get harder every %d steps from home" % step)


def test_the_mine_nearest_home_leads_to_the_first_hand_drawn_cave():
    world = new_world()
    mine = mines_nearest_first(world)[0]
    world.player.pos = mine
    world.do("act")
    first = caves.parse_level(caves.CAVE_LEVELS[0])
    ok(hand_drawn_number(world.cave_plan[mine]) == 0 and world.cave is not None
       and (world.cave.rows, world.cave.cols) == (len(first), len(first[0]))
       and world.cave.theme == caves.level_theme(caves.CAVE_LEVELS[0]),
       "the Mine nearest home leads to the first hand-drawn cave")


def test_come_back_later_and_your_changes_are_still_there():
    world = new_world()
    mine = mines_nearest_first(world)[0]
    world.cave_plan[mine] = "\n".join(flat_with("..S..B..T.zx.#"))    # this world's nearest Mine gets our cave
    world.player.pos = mine
    world.do("act")
    cave = world.cave
    rock, chest = cave.find("B"), cave.find("T")
    monsters = len(cave.monsters)
    cave.change(*rock, ".")                    # dig the cracked rock
    cave.change(*chest, "t")                   # open the chest
    cave.defeat(cave.monsters[0], True)        # beat a monster
    for _ in range(600):                       # walk back out the way you came in
        if not world.cave:
            break
        world.update_cave(DT, {"left": True})
    ok(world.cave is None, "you walk back out of the cave")
    world.do("act")
    cave = world.cave
    ok(cave.map[rock[0]][rock[1]] == "." and cave.map[chest[0]][chest[1]] == "t" and len(cave.monsters) == monsters - 1,
       "come back later: dug rock, opened chests and beaten monsters stay that way")


# ===========================================================================
# Smash every key for a while in the real caves: nothing should crash
# ===========================================================================

def mash_buttons(text, seed, seconds=90):
    """Press random buttons in this cave for a while, with monsters around. You can't lose."""
    world = new_world(seed)
    cave = world.cave = caves.Cave(world, (0, 0), text)
    world.player.max_health = world.player.health = 10 ** 6
    rng = random.Random(seed)
    controls = {}
    for frame in range(60 * seconds):
        if frame % 15 == 0:
            controls = {key: rng.random() < chance
                        for key, chance in (("right", .6), ("left", .25), ("jump", .5), ("down", .1))}
            controls["jump_pressed"] = controls["jump"]
            controls["use_pressed"] = rng.random() < .4
        else:
            controls["jump_pressed"] = controls["use_pressed"] = False
        cave.update(DT, controls)
        if cave.result:                        # you found a way out: back to safe ground, keep going
            cave.result = None
            cave.you.x, cave.you.y = cave.you.safe
    return world, cave


def still_inside(cave):
    return -1 <= cave.you.x <= cave.cols and cave.you.y <= cave.rows


@pytest.mark.parametrize("number", range(len(caves.CAVE_LEVELS)))
def test_button_mashing_in_a_hand_drawn_cave_never_crashes(number):
    world, cave = mash_buttons(caves.CAVE_LEVELS[number], number)
    ok(still_inside(cave),
       "hand-drawn cave %d: 90 s of random button mashing with monsters: no crash, still in the cave (%d monsters left, %d defeated)"
       % (number, len(cave.monsters), world.player.monsters_defeated))


def test_button_mashing_in_the_secret_cave_never_crashes():
    for i, text in enumerate(caves.SECRET_CAVES):
        world, cave = mash_buttons(text, len(caves.CAVE_LEVELS) + i)
        ok(still_inside(cave),
           "the Secret Mine's cave: 90 s of random button mashing with monsters: no crash, still in the cave (%d monsters left, %d defeated)"
           % (len(cave.monsters), world.player.monsters_defeated))
