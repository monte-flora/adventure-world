"""
Shadowfall's cave letters and the "needs:" line, for the robot (cave_solver.py).

needs: lists the powers the robot may use. Without pound, cracked rock (B) is rock; without climb,
climbing walls (%) are; without truesight, secret walls (F) are; without flare, shadow thorns (n)
hurt. No needs: line = every power. A checkpoint (C) is air, and a one-way door (< >) is shut
until you touch it from the side its arrow points to.
"""

import cave_solver
from helpers import ok


def a_wall_of(letter, start="S", head=""):
    """A little cave: the start on the right, the diamond and exit on the left, a 3-tall wall between."""
    rows = ["############",
            "#....%s.....#" % letter,
            "#....%s.....#" % letter,
            ".E*..%s...%s.#" % (letter, start),
            "############"]
    return "theme: stone\n" + head + "\n".join(rows) + "\n"


def beaten(text):
    result = cave_solver.check(text, tries=20000, chest_tries=0, time_limit=60)
    return bool(result["diamond"] and result["exit"])


def test_needs_decides_which_walls_the_robot_can_get_through():
    for letter, power in (("B", "pound"), ("n", "flare"), ("F", "truesight")):
        ok(beaten(a_wall_of(letter)), "%s: no needs: line, so the robot may use every power" % letter)
        ok(beaten(a_wall_of(letter, head="needs: %s\n" % power)), "%s: needs: %s lets it through" % (letter, power))
        ok(not beaten(a_wall_of(letter, head="needs: dash\n")), "%s: without %s it is a wall" % (letter, power))


def test_climbing_walls_need_climb():
    text = "theme: stone\nneeds: POWER\n" + "\n".join([
        "#######",
        "#E*...#",
        "#####.#",
        "#####.#",
        "#####.#",
        "#.S..%#",
        "#######"]) + "\n"
    ok(cave_solver.robot_text(text.replace("POWER", "climb")).count("%") == 1, "with climb the climbing wall stays")
    ok("%" not in cave_solver.robot_text(text.replace("POWER", "pound")).split("\n", 2)[2], "without climb it is plain rock")


def test_a_checkpoint_is_air():
    ok(beaten(a_wall_of("C", head="needs: none\n")), "the robot walks past a checkpoint")


def test_one_way_doors_open_from_the_arrow_side():
    ok(beaten(a_wall_of(">")), "> opens from the right: the robot starts on the right")
    ok(not beaten(a_wall_of("<")), "< stays shut from the right")


def test_the_robot_says_which_powers_it_used():
    result = cave_solver.check(a_wall_of("B", head="needs: pound, climb\n"), tries=20000, chest_tries=0)
    ok(result["needs"] == ["climb", "pound"], result["needs"])
    ok("climb, pound" in cave_solver.say(result)[0], cave_solver.say(result))


def test_pixi_godot_cave_opens_shadowfall_in_that_cave():
    import importlib.util
    import os
    from conftest import GAME_FOLDER
    spec = importlib.util.spec_from_file_location("play_cave", os.path.join(GAME_FOLDER, "shadowfall", "tools", "play_cave.py"))
    play_cave = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(play_cave)
    command = play_cave.godot_command(os.path.join(GAME_FOLDER, "levels", "caves", "03_blue_lvl_1.txt"))
    ok(command[-2:] == ["--scene=cave", "--file=caves/03_blue_lvl_1.txt"], command)
    ok(command[-1] != "--file=" and "shadowfall" in command[2], command)
