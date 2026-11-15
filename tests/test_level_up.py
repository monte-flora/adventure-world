"""
Leveling up: the XP you need, the LEVEL UP! card, and what every power does.

When you get enough XP you go up a level, you are healed, and a LEVEL UP! card
lets you pick 1 of 3 powers (Stronger, Tougher, Sharpshooter, Tough armor,
Springy, Speedy, Lucky, Forager). These tests check the card, every power,
where XP comes from, and how the card shows up in the real game.

The caves here are drawn right in this file, so it doesn't matter how the
real caves in caves.py look.
"""

import random

import pygame

import caves
import game
import rules
from helpers import (DT, FakeDice, cave_from, click, frames, new_app, new_world, ok, press, run, steps,
                     tiles, walk_into_a_mine)


def total_xp(player):
    """All the XP you ever got: the XP for the levels you already have, plus what you have now."""
    return sum(rules.XP_PER_LEVEL * level for level in range(1, player.level)) + player.xp


# A long, flat cave, 40 blocks wide. You start at S, on the floor near the left.
WIDTH = 40
FLAT = (["#" * WIDTH]
        + ["#" + "." * (WIDTH - 2) + "#"] * 9
        + ["." * (WIDTH - 1) + "#"] * 2
        + ["..S" + "." * (WIDTH - 4) + "#",
           "#" * WIDTH])


def flat_cave_with(letter, column):
    """The flat cave, with one thing (a monster, a chest, ore, a door...) on the floor at this column."""
    rows = list(FLAT)
    floor = rows[-2]
    rows[-2] = floor[:column] + letter + floor[column + 1:]
    return rows


def where_is(cave, letter):
    """The first spot in a cave with this letter: (row, column)."""
    return next((r, c) for r, row in enumerate(cave.map) for c, tile in enumerate(row) if tile == letter)


# ===========================================================================
# Leveling up: you are healed, the XP you need grows, and cards wait in a line
# ===========================================================================

def test_leveling_up_heals_you_and_asks_you_to_pick_a_power():
    world = new_world()
    p = world.player
    p.health = 5
    world.gain_xp(rules.XP_PER_LEVEL)
    ok(p.level == 2 and p.xp == 0 and world.level_ups == [2],
       "%d XP gets you to level 2, and a LEVEL UP! card is waiting" % rules.XP_PER_LEVEL)
    ok(p.health == p.max_health == rules.START_HEALTH, "leveling up heals you fully, with no hidden +2 max health")
    ok(p.damage_bonus == 0, "and no hidden +1 damage (damage only comes from Stronger)")
    ok(any("LEVEL UP" in m and "power" in m for m, _ in world.messages[-2:])
       and not any("+2 max health" in m for m, _ in world.messages),
       "the log says to pick a power (no more '+2 max health, +1 damage')")

    world = new_world()
    world.player.level = 6
    world.player.powers = {}
    ok(world.player.damage_bonus == 0, "even at level 6 you hit no harder without Stronger")


def test_every_level_needs_more_xp():
    player = new_world().player
    needed = []
    for level in (1, 2, 3):
        player.level = level
        needed.append(player.xp_needed)
    ok(needed == [rules.XP_PER_LEVEL * 1, rules.XP_PER_LEVEL * 2, rules.XP_PER_LEVEL * 3],
       "the curve is XP_PER_LEVEL * level: 20, 40, 60... (got %s)" % needed)

    world = new_world()
    world.gain_xp(6 * rules.XP_PER_LEVEL)
    ok(world.player.level == 4 and world.player.xp == 0 and world.level_ups == [2, 3, 4],
       "6 x XP_PER_LEVEL from level 1 = levels 2, 3 and 4, three cards waiting")

    world = new_world()
    world.gain_xp(3 * rules.XP_PER_LEVEL + 5)
    ok(world.player.level == 3 and world.player.xp == 5 and world.level_ups == [2, 3],
       "one big XP gain that gives two levels queues two cards")


# ===========================================================================
# The 3 powers on the card
# ===========================================================================

def test_the_card_always_offers_three_different_powers():
    # One world is enough: the card only looks at your powers and the game's dice,
    # so every try gets new dice and a new, random set of powers.
    world = new_world()
    p = world.player
    pick_powers = random.Random(7)
    bad, seen, first = [], set(), set()
    for trial in range(3000):
        world.rng = random.Random(trial)
        p.powers = {}
        for name, info in rules.POWERS.items():
            top = info["limit"] if info["limit"] is not None else 6
            p.powers[name] = pick_powers.randint(0, top)
        choices = world.power_choices()
        seen |= set(choices)
        first.add(choices[0])
        want = min(rules.CARD_CHOICES, sum(not p.maxed(name) for name in rules.POWERS))
        if (len(choices) != want or len(set(choices)) != want or not set(choices) & set(rules.MAIN_POWERS)
                or any(p.maxed(name) for name in choices)):
            bad.append((dict(p.powers), choices))
    ok(not bad, "3000 random cards: always 3 different powers (2 if only 2 are left), never a maxed one, "
                "always Stronger or Tougher %s" % (bad[:1],))
    ok(seen == set(rules.POWERS), "every power shows up on some card")
    ok(len(first) >= 3, "Stronger/Tougher isn't always in slot 1 (slot 1 had %d different powers)" % len(first))


def test_maxed_powers_are_not_offered_again():
    world = new_world()
    p = world.player
    p.powers = {"Sharpshooter": 3, "Tough armor": 3, "Springy": 2, "Speedy": 2, "Lucky": 1, "Forager": 1}
    p.lives = rules.MAX_LIVES                    # a full set of lives: no Extra life either
    ok(sorted(world.power_choices()) == ["Stronger", "Tougher"],
       "when everything else is maxed, only Stronger and Tougher are offered")
    ok(all(p.maxed(name) for name in p.powers) and not p.maxed("Stronger"),
       "limits: Sharpshooter 3, Tough armor 3, Springy 2, Speedy 2, Lucky 1, Forager 1, Stronger none")
    ok(world.pick_power("Lucky") is False and p.power("Lucky") == 1, "you can't pick a maxed power again")


def test_the_card_is_rolled_once_with_the_game_dice():
    world1, world2 = new_world(5), new_world(5)
    ok([world1.power_choices() for _ in range(5)] == [world2.power_choices() for _ in range(5)],
       "the choices come from game.rng (same seed, same cards)")

    world = new_world()
    world.gain_xp(rules.XP_PER_LEVEL)
    offer = world.next_power_offer()
    ok(offer and world.next_power_offer() is offer, "the card's powers stay the same until you pick (rolled once)")
    world.pick_power(offer[0])
    ok(world.level_ups == [] and world.power_offer is None and world.next_power_offer() is None
       and world.player.power(offer[0]) == 1,
       "picking a power stores it on the player and closes the card")


# ===========================================================================
# What every power does
# ===========================================================================

def test_stronger_makes_every_hit_harder():
    # A fight on the world map. The dice: you hit (0.1), it isn't a big hit (0.99), the sword rolls 4.
    world = new_world()
    p = world.player
    p.powers = {"Stronger": 2}
    zombie = rules.Monster("Zombie", p.pos)
    world.start_battle(zombie)
    world.rng = FakeDice(rolls=[0.1, 0.99], ints=[4])
    world.battle_action("attack")
    ok(zombie.max_health - zombie.health == 4 + 2 * rules.STRONGER_DAMAGE - 1,
       "Stronger x2: a sword hit of 4 on a tough Zombie does 4 + 2 - 1 = 5")

    world = new_world()
    p = world.player
    p.level = 5
    zombie = rules.Monster("Zombie", p.pos)
    world.start_battle(zombie)
    world.rng = FakeDice(rolls=[0.1, 0.99], ints=[4])
    world.battle_action("attack")
    ok(zombie.max_health - zombie.health == 4 - 1, "level 5 without Stronger: still 4 - 1 = 3")

    world = new_world()
    p = world.player
    p.powers = {"Stronger": 2}
    world.rng = FakeDice(ints=[2])
    ok(world.arrow_damage() == 2 + 2 * rules.STRONGER_DAMAGE, "Stronger x2 adds 2 to arrows (2 + 2 = 4)")
    p.sunfang = True
    world.rng = FakeDice(ints=[6])
    ok(world.sunfang_damage() == 6 + 2 * rules.STRONGER_DAMAGE, "Stronger x2 adds 2 to Sunfang (6 + 2 = 8)")

    # In a cave: stand right next to a Zombie that doesn't move, and swing
    world = new_world()
    world.player.powers = {"Stronger": 1}
    world, cave = cave_from(flat_cave_with("z", 4), world)
    zombie = cave.monsters[0]
    zombie.speed = 0
    cave.you.x = zombie.x - caves.PLAYER_W - 0.2
    cave.you.facing = 1
    run(cave, 5)
    world.rng = FakeDice(ints=[4])
    health = zombie.info.health
    run(cave, 1, use_pressed=True)
    ok(health - zombie.info.health == 4 + rules.STRONGER_DAMAGE - 1,
       "in a cave, Stronger adds 1 to a sword hit (Zombie: 4 + 1 - 1 tough)")


def test_tougher_gives_you_more_health():
    world = new_world()
    p = world.player
    p.health = 20
    world.pick_power("Tougher")
    ok(p.max_health == rules.START_HEALTH + rules.TOUGHER_HEALTH and p.health == 20 + rules.TOUGHER_HEALTH,
       "Tougher: +4 max health, and those 4 are filled (20/25 -> 24/29)")
    world.pick_power("Tougher")
    ok(p.max_health == rules.START_HEALTH + 2 * rules.TOUGHER_HEALTH, "Tougher stacks: +8 after two picks")


def test_sharpshooter_arrows_hit_harder_and_you_carry_more():
    world = new_world()
    p = world.player
    p.has_bow = True
    p.wood = 100
    world.pick_power("Sharpshooter")
    world.rng = FakeDice(ints=[2])
    ok(world.arrow_damage() == 2 + rules.SHARP_DAMAGE and p.max_arrows == rules.MAX_ARROWS + rules.SHARP_ARROWS,
       "Sharpshooter: arrows hit +1 (2 -> 3) and you carry 20")
    world.pick_power("Sharpshooter")
    world.pick_power("Sharpshooter")
    for _ in range(10):
        world.build("arrows")
    most = rules.MAX_ARROWS + 3 * rules.SHARP_ARROWS
    ok(p.arrows == most and p.max_arrows == most and world.build_problem("arrows"),
       "Sharpshooter x3: 30 arrows, then 'can't carry any more'")

    world = new_world()
    p = world.player
    p.arrows = rules.MAX_ARROWS
    world.pick_power("Sharpshooter")
    world.give_loot("arrows", caves.CHEST_XP)
    ok(p.arrows == rules.MAX_ARROWS + rules.SHARP_ARROWS, "an arrow chest fills you past 15 with Sharpshooter")


def test_tough_armor_soaks_up_more():
    boosted = rules.ARMOR_POINTS + rules.ARMOR_BOOST
    world = new_world()
    p = world.player
    p.put_on_armor()
    p.hurt(2)
    world.pick_power("Tough armor")
    ok(p.max_armor == boosted and p.armor == rules.ARMOR_POINTS - 2 + rules.ARMOR_BOOST,
       "Tough armor: armor holds 9, and the armor you're wearing gets +3 (4 -> 7)")
    p.put_on_armor()
    ok(p.armor == boosted, "new armor starts at 9")
    p.hurt(5)
    world.give_loot("armor", caves.CHEST_XP)
    ok(p.armor == boosted, "an armor chest fixes it up to 9")

    twice = rules.ARMOR_POINTS + 2 * rules.ARMOR_BOOST
    world = new_world()
    p = world.player
    world.pick_power("Tough armor")
    world.pick_power("Tough armor")
    ok(p.armor == 0 and p.max_armor == twice, "no armor on: nothing to boost, but future armor holds 12")
    world.map[p.pos[0]][p.pos[1]] = "G"          # a lucky event on a field that finds armor
    thistles = rules.TILE_DANGER["G"]           # (a roll below this is a thistle, so roll just above it)
    world.rng = FakeDice(rolls=[thistles + 0.01, 0.0])
    world.random_event()
    ok(p.armor == twice and any("%d damage" % twice in m for m, _ in world.messages[-2:]),
       "armor found on the map holds 12 and says so")


def jump_height(springy):
    """Jump once in the flat cave. Returns (your jump speed, how many blocks high you got)."""
    world = new_world()
    world.player.powers = {"Springy": springy}
    world, cave = cave_from(FLAT, world)
    run(cave, 30)
    start = top = cave.you.y
    for frame in range(80):
        cave.update(DT, {"jump": True, "jump_pressed": frame == 0})
        top = min(top, cave.you.y)
    return cave.jump_speed(), start - top


def test_springy_jumps_higher():
    (speed0, high0), (speed1, high1), (speed2, high2) = jump_height(0), jump_height(1), jump_height(2)
    ok((speed0, speed1, speed2) == tuple(caves.JUMP_SPEED + n * caves.SPRINGY_JUMP for n in (0, 1, 2)),
       "Springy: jump speed 14 -> 15 -> 16")
    ok(2.0 < high0 < 3.0 and 2.6 < high1 < 3.0 and 3.0 < high2 < 3.4,
       "jump heights %.2f, %.2f, %.2f blocks (2 yes / 3 no, then about 2.8, then over 3)" % (high0, high1, high2))


def run_speed(speedy):
    """Run right in the flat cave for half a second. Returns (your run speed, how fast you really go)."""
    world = new_world()
    world.player.powers = {"Speedy": speedy}
    world, cave = cave_from(FLAT, world)
    run(cave, 30)
    run(cave, 30, right=True)
    return cave.run_speed(), cave.you.vx


def test_speedy_runs_faster():
    results = [run_speed(n) for n in (0, 1, 2)]
    want = [caves.RUN_SPEED + n * caves.SPEEDY_RUN for n in (0, 1, 2)]
    ok([speed for speed, _ in results] == want and all(abs(vx - w) < 1e-6 for (_, vx), w in zip(results, want)),
       "Speedy: you really run 6 -> 7 -> 8 tiles a second")


def test_speedy_and_springy_work_in_the_castle():
    world = new_world()
    world.player.powers = {"Speedy": 2, "Springy": 1}
    world.go_to_nightfall()
    world.player.sunfang = True
    world.open_castle()
    ok(world.cave.is_castle and world.cave.run_speed() == caves.RUN_SPEED + 2 * caves.SPEEDY_RUN
       and world.cave.jump_speed() == caves.JUMP_SPEED + caves.SPRINGY_JUMP,
       "Speedy and Springy work in the castle")


def ring_rate(lucky, tries=600):
    """Open a chest in a cave `tries` times, each with different dice. How often is there a diamond ring?"""
    chest = flat_cave_with("T", 4)
    world = new_world()        # one world is enough: every try gets a new player, new dice and a new cave
    rings = 0
    for seed in range(tries):
        world.player = rules.Player("Hero", world.start)
        world.player.powers = {"Lucky": 1} if lucky else {}
        world.rng = random.Random(seed)
        world, cave = cave_from(chest, world)
        cave.you.x = 3.8                       # right next to the chest
        run(cave, 3)
        run(cave, 1, use_pressed=True)
        rings += world.player.ring_hits > 0
    return rings / tries


def test_lucky_finds_more_diamond_rings():
    plain, lucky = ring_rate(False), ring_rate(True)
    ok(abs(plain - caves.RING_CHANCE) < 0.06 and abs(lucky - caves.LUCKY_RING_CHANCE) < 0.06,
       "Lucky: chests with a ring go from %.0f%% to %.0f%%" % (100 * plain, 100 * lucky))


def berry_rate(forager, tries=3000):
    """Search for food `tries` times. How often do you find berries?"""
    world = new_world()
    world.rng = random.Random(3)
    p = world.player
    p.powers = {"Forager": 1} if forager else {}
    found = 0
    for _ in range(tries):
        p.food = 0
        world.search_for_food()
        found += p.food
    return found / tries


def test_forager_finds_more_berries_and_carries_more():
    plain, forager = berry_rate(False), berry_rate(True)
    ok(abs(plain - rules.BERRY_CHANCE) < 0.03 and abs(forager - rules.FORAGER_BERRY_CHANCE) < 0.02,
       "Forager: berries %.0f%% -> %.0f%% of searches" % (100 * plain, 100 * forager))

    world = new_world()
    p = world.player
    world.pick_power("Forager")
    p.food = rules.MAX_FOOD
    world.rng = FakeDice(rolls=[0.0])
    ok(world.search_for_food() and p.food == p.max_food == rules.MAX_FOOD + rules.FORAGER_FOOD,
       "Forager: you can carry 4 food")
    ok(not world.search_for_food() and "full" in world.messages[-1][0], "...and then your pack is full")
    p.food = rules.MAX_FOOD
    world.give_loot("food", caves.CHEST_XP)
    ok(p.food == rules.MAX_FOOD + rules.FORAGER_FOOD, "a berry chest fills you up to 4 too")


# ===========================================================================
# Where XP comes from
# ===========================================================================

def test_xp_for_diamonds_and_quests():
    ore = flat_cave_with("*", 3)
    world, cave = cave_from(ore)
    xp = total_xp(world.player)
    cave.dig(*where_is(cave, "*"))
    ok(total_xp(world.player) - xp == rules.DIAMOND_XP
       and "+%d XP" % rules.DIAMOND_XP in " ".join(m for m, _ in world.messages[-3:]),
       "mining a diamond: +%d XP" % rules.DIAMOND_XP)

    world, cave = cave_from(ore)
    world.diamond_quest.progress = rules.DIAMONDS_NEEDED - 1
    xp = total_xp(world.player)
    cave.dig(*where_is(cave, "*"))
    ok(total_xp(world.player) - xp == rules.DIAMOND_XP + rules.QUEST_XP and world.diamond_quest.completed,
       "the last diamond finishes 'Mine %d diamonds': +%d + %d XP"
       % (rules.DIAMONDS_NEEDED, rules.DIAMOND_XP, rules.QUEST_XP))

    world = new_world()
    world.monster_quest.progress = rules.MONSTERS_TO_DEFEAT - 1
    spider = rules.Monster("Spider", (0, 0))
    xp = total_xp(world.player)
    world.monster_gone(spider, give_xp=True)
    ok(total_xp(world.player) - xp == spider.xp + rules.QUEST_XP,
       "the last monster finishes 'Defeat %d monsters': monster XP + %d" % (rules.MONSTERS_TO_DEFEAT, rules.QUEST_XP))


def test_xp_for_the_castle():
    world = new_world()
    world.go_to_nightfall()
    world.player.sunfang = True
    xp = total_xp(world.player)
    world.open_castle()
    ok(total_xp(world.player) - xp == rules.QUEST_XP, "'Find the castle': +%d XP" % rules.QUEST_XP)
    world.cave = None
    xp = total_xp(world.player)
    world.open_castle()
    ok(total_xp(world.player) - xp == 0, "going back into the castle gives no more")
    xp = total_xp(world.player)
    world.reach_throne()
    ok(total_xp(world.player) - xp == rules.QUEST_XP, "'Reach the throne room': +%d XP" % rules.QUEST_XP)


def walk_out_of(world, mine, drawing):
    """Go into this mine's cave (drawn with an EXIT door to the right) and run right until you're out."""
    world.player.pos = mine
    world.cave = caves.Cave(world, mine, "\n".join(drawing))
    for _ in range(120):
        if not world.cave:
            break
        world.update_cave(DT, {"right": True})
    return world.cave is None


def test_xp_for_walking_out_of_a_cave_exit():
    door = flat_cave_with("E", 4)
    world = new_world()
    mines = list(world.cave_plan)
    xp = total_xp(world.player)
    walk_out_of(world, mines[0], door)
    ok(total_xp(world.player) - xp == rules.EXIT_XP
       and any("+%d XP" % rules.EXIT_XP in m for m, _ in world.messages[-4:]),
       "walking out of a cave's EXIT door: +%d XP" % rules.EXIT_XP)
    xp = total_xp(world.player)
    walk_out_of(world, mines[0], door)
    ok(total_xp(world.player) - xp == 0, "the same cave's EXIT again: no more XP")
    xp = total_xp(world.player)
    walk_out_of(world, mines[1], door)
    ok(total_xp(world.player) - xp == rules.EXIT_XP, "a different cave's EXIT: +%d again" % rules.EXIT_XP)

    world.cave = caves.Cave(world, mines[2], "\n".join(door))
    world.cave.result = "left"
    xp = total_xp(world.player)
    world.leave_cave()
    ok(total_xp(world.player) - xp == 0, "walking back out the entrance gives no XP")


def test_chopping_trees_gives_no_xp():
    world = new_world()
    p = world.player
    tree = tiles(world, "F")[0]
    p.pos = tree
    xp = total_xp(p)
    for _ in range(20):
        if world.map[tree[0]][tree[1]] != "F":
            break
        world.chop_wood()
        p.wood = 0
    ok(world.map[tree[0]][tree[1]] == "G" and total_xp(p) == xp, "chopping a tree all the way down gives no XP")


def test_gold_coins_give_xp():
    world = new_world()
    xp = total_xp(world.player)
    world.give_loot("xp", caves.CHEST_XP)
    ok(total_xp(world.player) - xp == caves.CHEST_XP, "gold coins are still worth %d XP" % caves.CHEST_XP)


# ===========================================================================
# In the real game: the card pops up, pauses the game, waits for fights, comes twice
# ===========================================================================

def test_the_card_on_the_world_map():
    app = new_app()
    world, p = app.game, app.game.player
    frames(app, 3)
    world.gain_xp(rules.XP_PER_LEVEL)
    frames(app, 1)
    ok(app.state == "levelup" and len(world.power_offer) == rules.CARD_CHOICES,
       "world map: the LEVEL UP! card pops up right away")
    turn, pos = world.turn, p.pos
    press(app, pygame.K_RIGHT)
    press(app, pygame.K_SPACE)
    press(app, pygame.K_z)
    frames(app, 5)
    ok(app.state == "levelup" and world.turn == turn and p.pos == pos,
       "while it's up the game is paused (moving/waiting does nothing)")
    press(app, pygame.K_1)
    ok(app.state == "levelup", "a key pressed in the first half second doesn't count (so you can read the card)")
    frames(app, 30)
    picked = world.power_offer[1]
    press(app, pygame.K_2)
    ok(app.state == "play" and p.power(picked) == 1 and not world.level_ups,
       "press 2: you get %s and you're back on the map" % picked)

    # Two level-ups at once: two cards, one after the other
    world.gain_xp(p.xp_needed + (p.level + 1) * rules.XP_PER_LEVEL)
    frames(app, 1)
    levels = list(world.level_ups)
    ok(app.state == "levelup" and len(levels) == 2 and levels[1] == levels[0] + 1,
       "two level-ups at once: two cards waiting (levels %s)" % levels)
    frames(app, 40)
    press(app, pygame.K_1)
    ok(app.state == "levelup" and world.level_ups == [levels[1]] and world.power_offer,
       "after picking, the second card comes right away (level %d)" % levels[1])
    press(app, pygame.K_3)
    ok(app.state == "levelup", "the second card waits half a second too")
    frames(app, 40)
    click(app, app.card_rows[2].center)
    ok(app.state == "play" and not world.level_ups and sum(p.powers.values()) == 3,
       "clicking a power picks it too; back to the map")


def test_the_card_waits_until_the_fight_is_over():
    app = new_app()
    world, p = app.game, app.game.player
    frames(app, 3)
    p.xp = p.xp_needed - 1
    spider = rules.Monster("Spider", p.pos)
    spider.health = 1
    world.monsters = [spider]
    world.start_battle(spider)
    frames(app, 2)
    ok(app.state == "battle", "a fight starts")
    for _ in range(40):
        if world.battle.over:
            break
        press(app, pygame.K_1)                  # attack!
        frames(app, int(game.BATTLE_PAUSE / DT) + 1)   # wait out the pause before the next turn
    frames(app, 5)
    ok(world.battle.over and world.level_ups and app.state == "battle",
       "you win and level up, but the card waits while the fight box is up")
    ok(any("after the fight" in text for text, _ in world.battle.lines),
       "the fight box says you'll pick a power after the fight")
    frames(app, 30)
    press(app, pygame.K_SPACE)
    frames(app, 1)
    ok(app.state == "levelup" and app.card_return == "play", "close the fight: now the card pops up")
    frames(app, 40)
    press(app, pygame.K_1)
    ok(app.state == "play", "...and then back to the map")


def test_the_card_in_a_cave():
    app = new_app()
    world, p = app.game, app.game.player
    frames(app, 3)
    mine = min(world.diamond_mines, key=lambda spot: (steps(spot, world.start), spot))   # a cave with a diamond
    walk_into_a_mine(app, mine)
    ok(app.state == "cave", "in a cave")
    world.gain_xp(rules.XP_PER_LEVEL)
    frames(app, 1)
    ok(app.state == "levelup" and app.card_return == "cave", "in a cave the card pops up right away")
    clock = world.cave.clock
    frames(app, 30)
    ok(world.cave.clock == clock, "and the cave is paused (nothing moves)")
    press(app, pygame.K_3)
    frames(app, 2)
    ok(app.state == "cave" and world.cave.clock > clock, "pick one: back in the cave, and it starts moving again")

    # Dig up the cave's diamond when you're DIAMOND_XP away from the next level
    p.xp = p.xp_needed - rules.DIAMOND_XP
    world.cave.dig(*where_is(world.cave, "*"))
    frames(app, 1)
    ok(app.state == "levelup", "digging a diamond (+%d XP) can level you up right there in the cave" % rules.DIAMOND_XP)


def go_to_the_castle_door(app):
    """Go to Nightfall Hollow with Sunfang in your hand, ready to open the castle."""
    world = app.game
    world.go_to_nightfall()
    world.story.clear()
    world.take_effects()
    app.build_tiles()
    world.player.sunfang = True
    return world


def test_the_card_in_the_castle():
    app = new_app()
    frames(app, 3)
    world = go_to_the_castle_door(app)
    world.player.xp = world.player.xp_needed - 5   # 'Find the castle' (+QUEST_XP) is then enough for a level
    world.open_castle()
    for _ in range(60):
        frames(app, 1)
        if app.state == "story":
            press(app, pygame.K_RETURN)
        if app.state == "levelup":
            break
    ok(app.state == "levelup" and app.card_return == "cave" and world.cave and world.cave.is_castle,
       "castle: 'Find the castle' (+%d XP) levels you up, the card shows in the castle" % rules.QUEST_XP)
    frames(app, 40)
    press(app, pygame.K_1)
    frames(app, 1)
    ok(app.state == "cave" and world.cave.is_castle, "and you go back to the castle afterwards")


def test_no_card_when_you_are_out_of_health():
    app = new_app()
    world = app.game
    frames(app, 3)
    world.gain_xp(rules.XP_PER_LEVEL)
    world.player.health = 0
    frames(app, 2)
    ok(app.state != "levelup", "no card when you're out of health (game over instead)")


def test_no_card_after_you_win():
    app = new_app()
    frames(app, 3)
    world = go_to_the_castle_door(app)
    world.open_castle()
    world.pick_power("Stronger")
    world.cave = None
    world.reach_throne()
    world.level_ups.clear()
    world.player.xp = world.player.xp_needed - rules.QUEST_XP
    world.beat_the_king()
    world.story.clear()
    frames(app, 120)
    ok(world.won and world.level_ups and app.state == "end",
       "beating the Shadow King still gives +%d XP, but once you've won it goes to the end screen (no card)"
       % rules.QUEST_XP)


# ===========================================================================
# The side panel lists your powers, and the help screen opens
# ===========================================================================

def test_the_panel_lists_your_powers():
    app = new_app()
    p = app.game.player
    frames(app, 3)
    p.powers = {"Stronger": 3, "Tougher": 2, "Tough armor": 1, "Springy": 2, "Lucky": 1}
    p.max_health += 2 * rules.TOUGHER_HEALTH
    p.health = p.max_health
    p.put_on_armor()
    frames(app, 2)
    words = app.powers_text(p)
    want = "+%d dmg, +%d health, Tough armor, Springy x2" % (3 * rules.STRONGER_DAMAGE, 2 * rules.TOUGHER_HEALTH)
    ok(words.startswith(want), "panel words: %r" % words)
    fitted = app.fit(words, 20, 200)
    ok(fitted.endswith("...") and app.font(20).size(fitted)[0] <= 200, "long lists get cut with '...': %r" % fitted)
    ok(p.armor == rules.ARMOR_POINTS + rules.ARMOR_BOOST, "armor shows as 9 / 9 with Tough armor")
    press(app, pygame.K_h)
    ok(app.state == "help", "the help screen opens")
