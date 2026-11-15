"""
The new things from the cave recipe: vines, slippery ice, healing springs and lava
that rises when you grab the treasure. And the three caves drawn with the recipe.

Most tests draw their own little cave right here, so it doesn't matter how the
real caves in caves.py look.
"""

import pytest

import cave_solver
import caves
import robot
from helpers import cave_from, feet, ok, run

# ===========================================================================
# Vines (V): like a ladder that hangs from a branch
# ===========================================================================

VINES = ["##############",
         "#............#",
         "#..====......#",
         "#...V...V....#",
         "#...V...V....#",
         "#...V...V....#",
         "#...V...V....#",
         "#............#",
         "..S..........#",
         "##############"]


def test_jumping_into_a_vine_and_climbing_it():
    world, cave = cave_from(VINES)
    you = cave.you
    you.x = 4.1
    run(cave, 5)
    ok(not you.climbing, "standing under a vine (it doesn't reach the floor)")
    run(cave, 1, jump=True, jump_pressed=True)
    run(cave, 12, up=True, jump=True)
    ok(you.climbing, "jump up into the vine and hold UP: you grab it")
    low = feet(cave)
    run(cave, 20, up=True)
    ok(you.climbing and feet(cave) < low - 1, "hold UP and you climb it (feet from %.2f to %.2f)" % (low, feet(cave)))
    ok("vine" in world.tips_seen, "the game tells you how vines work the first time")


def test_leaping_from_one_vine_to_the_next():
    world, cave = cave_from(VINES)
    you = cave.you
    you.x, you.y = 4.1, 4.0
    run(cave, 1, up=True)
    ok(you.climbing, "on the first vine")
    run(cave, 1, right=True, space_pressed=True, jump_pressed=True, jump=True)
    ok(not you.climbing and you.vx > 0, "SPACE leaps off it, to the side you hold")
    grabbed = False
    for _ in range(60):                # keep holding SPACE for a long leap, and UP to catch the vine
        run(cave, 1, right=you.x < 7.6, up=True, jump=True)
        if you.climbing and abs(you.x + you.w / 2 - 8.5) < 0.3:
            grabbed = True
            break
    ok(grabbed, "hold UP in the air and you catch the next vine (x = %.2f)" % you.x)


# ===========================================================================
# Slippery ice (I)
# ===========================================================================

def slide_after_running(floor):
    """Run at full speed along a floor of this letter, let go, and see how far you slide before you stop."""
    rows = ["#" * 40] + ["#" + "." * 38 + "#"] * 6 + ["..S" + "." * 36 + "#", "#" * 40]
    rows[-1] = "#" + floor * 38 + "#"
    world, cave = cave_from(rows)
    you = cave.you
    run(cave, 5)
    run(cave, 90, right=True)
    ok(abs(you.vx - caves.RUN_SPEED) < 0.01, "running at full speed (%.2f)" % you.vx)
    let_go = you.x
    run(cave, 120)
    ok(abs(you.vx) < 0.01, "you stop in the end")
    return you.x - let_go


def test_ice_is_slippery():
    on_rock = slide_after_running("#")
    on_ice = slide_after_running("I")
    ok(on_rock < 0.5, "on rock you stop almost at once (%.2f blocks)" % on_rock)
    ok(2 < on_ice < 4, "on ice you slide on for 2 to 4 blocks (%.2f)" % on_ice)


def test_ice_is_solid_and_tells_you_it_is_slippery():
    world, cave = cave_from(["######", "#....#", "#....#", "..S..#", "IIIIII"])
    run(cave, 30)
    ok(cave.you.on_ground and feet(cave) == 4.0, "you stand on ice like on rock")
    ok("ice" in world.tips_seen, "and the game tells you it's slippery")


# ===========================================================================
# Healing springs (u)
# ===========================================================================

SPRING = ["##########",
          "#........#",
          "#........#",
          "..S..u...#",
          "##########"]


def test_a_healing_spring_heals_you_then_fills_up_again():
    world, cave = cave_from(SPRING)
    p = world.player
    p.health = 2
    run(cave, 60, right=True)
    ok(p.health == p.max_health, "walk into the spring: it heals you all the way (%d)" % p.health)
    ok(cave.fountains[(3, 5)] > 0, "now it's empty for a while")
    p.health = 2
    run(cave, 60, left=True)
    ok(p.health == 2 and cave.you.x < 4, "walk back past the empty spring: it doesn't heal you")
    cave.fountains[(3, 5)] = 0.01
    run(cave, 5)
    run(cave, 40, right=True)
    ok(p.health == p.max_health, "once it fills up again, it heals you again")


# ===========================================================================
# Lava that rises when you grab the treasure ("lava rises: yes")
# ===========================================================================

RISING = ["theme: lava",
          "lava rises: yes",
          "############",
          "#.........E#",
          "#........###",
          "#........H.#",
          "#........H.#",
          "#........H.#",
          "#........H.#",
          "#........H.#",
          "..S...T*.H.#",
          "############"]


def test_setting_lines_are_not_part_of_the_drawing():
    text = "\n".join(RISING)
    ok(caves.level_setting(text, "lava rises") == "yes" and caves.level_theme(text) == "lava",
       "the lines at the top are settings")
    ok(len(caves.level_lines(text)) == 10, "and they aren't rows of the cave")


def test_grabbing_the_diamond_wakes_the_lava():
    world, cave = cave_from(RISING)
    ok(cave.lava_rises and cave.lava_line is None, "the lava sleeps until you grab the diamond")
    cave.you.x, cave.you.y = 9.1, 2 - caves.PLAYER_H      # wait up by the exit, where it can't reach you
    cave.dig(8, 7)
    ok(cave.lava_line is not None, "you dig out the diamond: the lava wakes up!")
    start = cave.lava_line
    run(cave, int(caves.LAVA_RISE_WAIT * 60) - 10)
    ok(cave.lava_line == start, "it waits a moment first, so you can get ready")
    run(cave, 70)
    ok(start - cave.lava_line > 0.6, "then it rises (%.2f blocks)" % (start - cave.lava_line))
    run(cave, 60 * 20)
    ok(cave.lava_line == 2, "it stops just below the exit (%.2f)" % cave.lava_line)


def test_the_rising_lava_never_knocks_you_out():
    world, cave = cave_from(RISING)
    p = world.player
    p.health = 1
    you = cave.you
    you.x = 5.1
    run(cave, 5)
    cave.dig(8, 7)
    run(cave, 60 * 4)                  # stand still on the floor: the lava catches you
    ok(p.is_alive and p.health == 1, "caught by the lava, but never knocked out (health %d)" % p.health)
    ok(cave.lava_line > cave.rows - 1, "the lava sank back down to the floor (%.2f)" % cave.lava_line)
    ok(abs(you.x - 5.1) < 0.6 and you.on_ground, "and you try again from where you were when it woke up")


def test_in_a_cave_without_a_diamond_the_chest_in_its_place_wakes_the_lava():
    world, cave = cave_from(caves.without_diamond("\n".join(RISING)).split("\n"))
    ok(cave.lava_treasure == (8, 7), "the chest where the diamond was (the one nearest the exit)")
    cave.open_chest(8, 6)
    ok(cave.lava_line is None, "opening the other chest doesn't wake the lava")
    cave.open_chest(8, 7)
    ok(cave.lava_line is not None, "the big treasure does!")


def test_lava_only_rises_in_caves_that_say_so():
    world, cave = cave_from(RISING[:1] + RISING[2:])
    cave.dig(8, 7)
    ok(cave.lava_line is None, "no 'lava rises: yes' line, so the lava stays put")


# ===========================================================================
# The three caves drawn with the recipe
# ===========================================================================

RECIPE_CAVES = {"The Vine Garden": ("V", 1), "The Icy Steps": ("I", 5), "The Lava Escape": ("lava rises", 10)}




@pytest.mark.parametrize("name", RECIPE_CAVES)
def test_recipe_caves_have_their_new_thing_and_a_spring(name):
    new_thing, place = RECIPE_CAVES[name]
    text = caves.CAVE_LEVELS[place]
    ok(caves.level_setting(text, "name") == name, "%s is number %d in CAVE_LEVELS" % (name, place))
    has_it = caves.level_setting(text, new_thing) == "yes" if " " in new_thing else new_thing in text
    ok(has_it, "%s has its new thing (%s)" % (name, new_thing))
    if caves.level_setting(text, "spring check") != "later":    # its file says "spring check: later"
        ok("u" in "".join(caves.level_lines(text)), "%s has a healing spring to rest at" % name)


@pytest.mark.parametrize("name", RECIPE_CAVES)
def test_the_secret_room_in_a_recipe_cave_can_be_reached(name):
    """The robot gets to the secret chest (the one farthest from the exit), and then out of the cave."""
    text = caves.CAVE_LEVELS[RECIPE_CAVES[name][1]]
    cave = cave_solver.fresh_cave(text)
    exits = robot.where(cave, "E")
    far = max(robot.where(cave, "T"), key=lambda spot: min(abs(spot[0] - r) + abs(spot[1] - c) for r, c in exits))
    legs = [("the secret chest", lambda cv: cv.map[far[0]][far[1]] == "t", [far]),
            ("the exit", lambda cv: cv.result == "exit", exits)]
    beaten, how = robot.play_the_legs(cave, legs, robot.TRIES)
    ok(beaten, "%s: %s" % (name, how))


def test_the_lava_escape_can_be_beaten_without_a_diamond_too():
    """Under a Mine without a diamond, a chest wakes the lava. The robot still climbs out in time."""
    text = caves.without_diamond(caves.CAVE_LEVELS[RECIPE_CAVES["The Lava Escape"][1]])
    cave = cave_solver.fresh_cave(text)
    r, c = cave.lava_treasure
    legs = [("the big chest", lambda cv: cv.map[r][c] == "t", [(r, c)]),
            ("the exit", lambda cv: cv.result == "exit", robot.where(cave, "E"))]
    beaten, how = robot.play_the_legs(cave, legs, robot.TRIES)
    ok(beaten, "the Lava Escape without its diamond: %s" % how)
