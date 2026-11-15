"""
Lives: you start with 3. When your health runs out you lose a life and wake up
somewhere safe with full health:
  - in a cave: outside its Mine, on the world map
  - on the map (at home or in Nightfall Hollow, even in a fight): at the nearest house (Nightfall: shrine)
  - in the castle: at the start of that level
Out of lives? An "Out of lives!" card, then 3 new lives, and you keep everything.
A LEVEL UP! card can offer "Extra life" (up to MAX_LIVES).
"""

import pygame

import rules
import story
from helpers import frames, new_app, new_world, ok, press, tiles, walk_into_a_mine
from test_nightfall_and_castle import in_nightfall_hollow, inside_the_castle, titles


def far_from_houses(world):
    """A walkable square with no house on it, a good few steps from the nearest one."""
    houses = tiles(world, "H")
    walk = world.reach(world.start)
    spots = [s for s in walk if world.tile(s) in "GF" and min(rules.distance(s, h) for h in houses) >= 4]
    return min(spots)


def test_you_start_with_3_lives():
    world = new_world()
    ok(world.player.lives == rules.START_LIVES == 3, "you start with 3 lives")


def test_out_of_health_in_a_cave_puts_you_outside_the_mine():
    app = new_app()
    world = app.game
    frames(app, 3)
    cave = walk_into_a_mine(app)
    mine = cave.mine_pos
    world.player.health = 1
    cave.you.safe_time = 0
    cave.hurt_you(5, None)
    ok(world.cave is None and world.player.pos == mine, "knocked out in a cave: you're on the map, at its Mine")
    ok(world.player.health == world.player.max_health and world.player.lives == 2 and not world.over,
       "with full health and 1 life less (2 left)")
    frames(app, 5)
    ok(app.state == "play" and app.banner and "2 lives" in app.banner["sub"], "the map shows, with a banner")


def test_out_of_health_on_the_map_takes_you_to_the_nearest_house():
    world = new_world()
    p = world.player
    p.pos = far_from_houses(world)
    nearest = min(tiles(world, "H"), key=lambda h: rules.distance(p.pos, h))
    p.health = 1
    world.hurt_player(3)
    ok(p.pos == nearest and world.tile(p.pos) == "H", "knocked out on the map: you wake up at the nearest house")
    ok(p.health == p.max_health and p.lives == 2 and not world.over, "with full health and 2 lives left")


def test_knocked_out_in_a_map_fight():
    world = new_world()
    p = world.player
    p.pos = far_from_houses(world)
    zombie = rules.Monster("Zombie", p.pos)
    zombie.damage = (99, 99)
    world.monsters = [zombie]
    p.health = 1
    world.start_battle(zombie)
    for _ in range(20):
        if world.battle.over:
            break
        world.battle_action("attack")
    ok(world.battle.result == "lost" and world.tile(p.pos) == "H" and p.health == p.max_health and p.lives == 2,
       "beaten in a fight: 'Defeated...', then you wake up at the nearest house")


def test_out_of_health_in_nightfall_takes_you_to_the_nearest_shrine():
    world = in_nightfall_hollow(new_world())
    p = world.player
    shrines = tiles(world, "H")
    p.pos = max(world.reach(world.start), key=lambda s: min(rules.distance(s, h) for h in shrines))
    nearest = min((h for h in shrines if h in world.reach(p.pos)), key=lambda h: rules.distance(p.pos, h))
    p.health = 1
    world.hurt_player(3)
    ok(p.pos == nearest and world.tile(p.pos) == "H", "knocked out in Nightfall Hollow: you wake up at the nearest shrine")
    ok(p.health == p.max_health and p.lives == 2, "with full health and 2 lives left")


def test_knocked_out_in_the_castle_costs_a_life():
    world, inside = inside_the_castle()
    world.player.health = 1
    inside.hurt_you(3, None)
    ok(world.cave is inside and world.player.lives == 2 and world.player.health == world.player.max_health,
       "in the castle you lose a life and start the level again")


def test_out_of_lives_gives_you_3_new_ones_and_you_keep_your_things():
    world = new_world()
    p = world.player
    p.lives, p.diamonds, p.wood = 1, 2, 7
    world.story.clear()
    p.health = 1
    world.hurt_player(3)
    ok(p.lives == rules.START_LIVES and p.is_alive and not world.over, "out of lives: 3 new lives, not game over")
    ok(p.diamonds == 2 and p.wood == 7, "you keep everything you found")
    ok(titles(world.story) == titles(story.OUT_OF_LIVES) and world.out_of_lives == 1, "an 'Out of lives!' card")
    ok(any(e["type"] == "knockout" and e.get("text") == "OUT OF LIVES!" for e in world.effects), "and a banner")


def test_level_up_can_give_an_extra_life():
    world = new_world()
    p = world.player
    ok("Extra life" in rules.POWERS, "Extra life is one of the level-up powers")
    ok(world.pick_power("Extra life") and p.lives == 4, "pick it: +1 life")
    p.lives = rules.MAX_LIVES
    ok(p.maxed("Extra life") and not world.pick_power("Extra life") and p.lives == rules.MAX_LIVES,
       "you can't have more than %d lives" % rules.MAX_LIVES)
    for _ in range(30):
        ok("Extra life" not in world.power_choices(), "a full set of lives: Extra life isn't on the card")


def test_extra_life_on_the_card_in_the_app():
    app = new_app()
    world = app.game
    frames(app, 3)
    world.rng.choice = lambda options: options[0]
    world.rng.sample = lambda options, k: [o for o in options if o == "Extra life"][:k] + \
        [o for o in options if o != "Extra life"][:k - 1]
    world.rng.shuffle = lambda options: options.sort(key=lambda o: o != "Extra life")
    world.gain_xp(rules.XP_PER_LEVEL)
    frames(app, 40)
    ok(app.state == "levelup" and world.power_offer[0] == "Extra life", "the card offers Extra life first")
    press(app, pygame.K_1, "1")
    frames(app, 2)
    ok(world.player.lives == 4 and app.state == "play", "press 1: you have 4 lives")
