"""
The bow and arrows (craft them with C, shoot with F), and diamond rings from
treasure chests that power up your sword for a few hits.
"""

import random

import caves
import rules
from helpers import DT, FakeDice, cave_from, new_world, ok, run, tiles

# A plain cave room. Each test puts something on the floor row (row 12): a Zombie, a chest...
FLAT = (["##############"] + ["#............#"] * 9 +
        ["..............", "..............", "..S..........#", "##############"])


def room_with(floor_row, world=None):
    """The plain room with row 12 drawn your way. Returns (the world, the cave)."""
    return cave_from(FLAT[:12] + [floor_row] + FLAT[13:], world)


def open_field(world):
    """A field square on the world map with field below it and room to shoot to the right."""
    return next((r, c) for r, c in tiles(world, "G")
                if c + rules.ARROW_RANGE + 1 < world.cols and r + 2 < world.rows and world.map[r + 1][c] == "G")


def archer(world, arrows):
    """You, on an open field with a bow and some arrows, facing right."""
    p = world.player
    p.pos, p.has_bow, p.arrows, p.facing = open_field(world), True, arrows, "right"
    return p


def next_to(spot, steps_right):
    return (spot[0], spot[1] + steps_right)


# ===========================================================================
# Crafting a bow and arrows
# ===========================================================================

def test_crafting_a_bow():
    world = new_world()
    p = world.player
    p.wood = 0
    ok("wood" in world.build_problem("bow"), "no wood: no bow")
    p.wood = rules.BOW_COST + rules.ARROW_COST * 4
    ok(world.do("build_bow") and p.has_bow and p.wood == rules.ARROW_COST * 4, "a bow costs %d wood" % rules.BOW_COST)
    ok("already" in world.build_problem("bow"), "you only need one bow")


def test_crafting_arrows_until_the_quiver_is_full():
    world = new_world()
    p = world.player
    bundles = rules.MAX_ARROWS // rules.ARROWS_PER_BUNDLE      # how many bundles fill your quiver
    p.arrows, p.wood = 0, rules.ARROW_COST * (bundles + 1)
    for _ in range(bundles + 1):
        world.do("build_arrows")
    ok(p.arrows == rules.MAX_ARROWS and p.wood == rules.ARROW_COST,
       "arrows come %d to a bundle, up to %d (bundle number %d is refused)"
       % (rules.ARROWS_PER_BUNDLE, rules.MAX_ARROWS, bundles + 1))
    p.wood = 9
    ok("carry" in world.build_problem("arrows"), "a full quiver can't take more")


# ===========================================================================
# Shooting on the world map (F)
# ===========================================================================

def test_no_bow_no_shooting():
    world = new_world()
    world.player.pos = open_field(world)
    turn = world.turn
    ok(not world.do("shoot") and "bow" in world.messages[-1][0] and world.turn == turn,
       "no bow: F tells you to make one (and doesn't use a turn)")


def test_an_arrow_hits_a_zombie_2_squares_away():
    world = new_world()
    p = archer(world, arrows=2)
    zombie = rules.Monster("Zombie", next_to(p.pos, 2))
    world.monsters = [zombie]
    health, turn = zombie.health, world.turn
    world.rng = FakeDice(ints=[4], rest=0.99)            # the arrow rolls a 4
    world.do("shoot")
    ok(zombie.health == health - 3 and p.arrows == 1 and world.turn == turn + 1,
       "F hits a Zombie 2 squares away (4 damage, -1 for tough), uses an arrow and a turn")


def test_a_monster_too_far_away_is_out_of_range():
    world = new_world()
    p = archer(world, arrows=1)
    spider = rules.Monster("Spider", next_to(p.pos, rules.ARROW_RANGE + 1))
    world.monsters = [spider]
    world.do("shoot")
    ok(spider.health == spider.max_health and "misses" in "".join(words for words, _ in world.messages[-3:]),
       "a monster %d squares away is out of range" % (rules.ARROW_RANGE + 1))


def test_arrows_go_the_way_you_last_walked_and_can_finish_a_monster():
    world = new_world()
    p = archer(world, arrows=1)
    world.do("down")
    ok(p.facing == "down", "your arrows go the way you last walked")
    spider = rules.Monster("Spider", (p.pos[0] + 1, p.pos[1]))
    spider.health = 2
    world.monsters = [spider]
    world.rng = FakeDice(ints=[3])
    world.do("shoot")
    ok(spider not in world.monsters and world.monster_quest.progress == 1 and p.xp > 0,
       "an arrow can finish off a monster: it counts for the quest and gives XP")


def test_chests_can_have_arrows():
    world = new_world()
    world.player.arrows = 0
    world.give_loot("arrows", 5)
    ok(world.player.arrows == rules.ARROWS_PER_BUNDLE, "chests can have a bundle of arrows")


# ===========================================================================
# Shooting in a cave (F)
# ===========================================================================

def test_shooting_arrows_in_a_cave():
    world, cave = room_with("..S......z...#")
    p = world.player
    p.has_bow, p.arrows = True, 3
    zombie = cave.monsters[0]
    zombie.speed = 0
    health = zombie.info.health
    cave.you.facing = 1
    cave.update(DT, {"shoot_pressed": True})
    cave.update(DT, {"shoot_pressed": True})
    ok(p.arrows == 2 and len(cave.arrows) == 1, "in a cave F shoots one arrow (a quick second press waits for the bow)")
    run(cave, 60)
    ok(zombie.info.health < health and not cave.arrows,
       "the arrow flies across and hits the Zombie (%d -> %d)" % (health, zombie.info.health))
    cave.you.facing, cave.you.reload = -1, 0
    cave.update(DT, {"shoot_pressed": True})
    run(cave, 60)
    ok(not cave.arrows and p.arrows == 1, "an arrow that hits a wall just stops")


def test_no_bow_in_a_cave():
    world, cave = room_with("..S......z...#")
    cave.update(DT, {"shoot_pressed": True})
    ok(not cave.arrows and "bow" in world.messages[-1][0], "no bow in a cave: nothing happens, and it tells you why")


# ===========================================================================
# Diamond rings: your sword's next few hits do extra damage
# ===========================================================================

def test_rings_add_up_to_a_limit():
    world = new_world()
    p = world.player
    world.give_ring()
    ok(p.ring_hits == rules.RING_HITS, "a diamond ring powers up your sword for %d hits" % rules.RING_HITS)
    for _ in range(rules.MAX_RING_HITS // rules.RING_HITS + 2):
        world.give_ring()
    ok(p.ring_hits == rules.MAX_RING_HITS, "more rings add up, to at most %d hits" % rules.MAX_RING_HITS)


def test_a_ring_in_a_world_map_fight():
    world = new_world()
    p = world.player
    p.ring_hits = 2
    zombie = rules.Monster("Zombie", p.pos)
    world.start_battle(zombie)
    world.rng = FakeDice(rolls=[0.1, 0.99], ints=[4])     # you hit (with a 4), the Zombie misses
    world.battle_action("attack")
    ok(zombie.max_health - zombie.health == 4 - 1 + rules.RING_BONUS and p.ring_hits == 1
       and any("glows" in line for line, _ in world.battle.lines),
       "in a fight, a ringed sword hits a Zombie for %d more (4 - 1 tough + %d = %d) and uses one charge"
       % (rules.RING_BONUS, rules.RING_BONUS, 4 - 1 + rules.RING_BONUS))
    world.rng = FakeDice(rolls=[0.95, 0.99])              # you miss
    world.battle_action("attack")
    ok(p.ring_hits == 1, "a miss doesn't use up the ring")
    world.close_battle()
    p.swords = []
    spider = rules.Monster("Spider", p.pos)
    world.start_battle(spider)
    world.rng = FakeDice(rolls=[0.99])
    world.battle_action("attack")
    ok(p.ring_hits == 1 and spider.max_health - spider.health == 1, "a punch (no sword) doesn't use it either")


def test_a_ring_in_a_cave():
    world, cave = room_with("..S.z........#")
    p = world.player
    p.ring_hits = 1
    zombie = cave.monsters[0]
    zombie.speed = 0
    cave.you.x, cave.you.facing = zombie.x - caves.PLAYER_W - 0.2, 1
    run(cave, 5)
    world.rng = FakeDice(ints=[4])
    health = zombie.info.health
    run(cave, 1, use_pressed=True)
    ok(health - zombie.info.health == 4 + rules.RING_BONUS - 1 and p.ring_hits == 0,
       "in a cave the ring adds %d to a sword hit (Zombie: 4 + %d - 1 tough)" % (rules.RING_BONUS, rules.RING_BONUS))
    ok(any("used up" in words for words, _ in world.messages), "and it tells you when the ring's power is used up")


def test_swinging_at_nothing_keeps_the_ring():
    world, cave = room_with("..S..........#")
    world.player.ring_hits = 3
    cave.you.facing = 1
    run(cave, 5)
    run(cave, 1, use_pressed=True)
    ok(world.player.ring_hits == 3, "swinging at nothing doesn't use it up")


def test_about_a_third_of_chests_have_a_ring():
    world = new_world()
    rings, chests = 0, 600
    for seed in range(chests):
        world.player = rules.Player("Hero", world.start)      # a brand-new you for every chest
        world.rng = random.Random(seed)
        world, cave = room_with("..S.T........#", world)
        cave.you.x = 3.8
        run(cave, 3)
        run(cave, 1, use_pressed=True)
        rings += world.player.ring_hits > 0
    ok(abs(rings / chests - caves.RING_CHANCE) < 0.06,
       "about %d chests in 100 have a diamond ring (%d of %d = %.0f%%)"
       % (round(caves.RING_CHANCE * 100), rings, chests, 100 * rings / chests))
