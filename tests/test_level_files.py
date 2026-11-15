"""
The game's hand-drawn caves and castle levels live in the levels folder, one text file each,
so the cave editor can save over them. These tests check the files are all there and in shape.
(test_beatable_caves.py sends the robot through every one of them.)
"""

import os

import castle
import caves
import cave_files
from helpers import ok

GAME_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_game_reads_every_cave_and_castle_level_from_the_levels_folder():
    ok(len(caves.CAVE_LEVELS) == 12, "12 hand-drawn caves in levels/caves (found %d)" % len(caves.CAVE_LEVELS))
    ok(len(castle.CASTLE_LEVELS) == 5, "5 castle levels in levels/castle (found %d)" % len(castle.CASTLE_LEVELS))
    for path, text in caves.CAVE_LEVEL_FILES + castle.CASTLE_LEVEL_FILES:
        name = os.path.basename(path)
        ok(name[0].isdigit(), "%s starts with its number, so the levels stay in order" % name)
        ok(caves.level_setting(text, "name"), "%s says its name (name: ...)" % name)
        ok(cave_files.read_cave(text)[2] == [], "%s loads without anything to fix" % name)


def test_cave_files_stay_in_order_past_nine():
    numbers = [int(os.path.basename(path).split("_")[0]) for path, _ in caves.CAVE_LEVEL_FILES]
    ok(numbers == sorted(numbers), "caves are read in the order of their numbers: %s" % numbers)


def test_every_castle_level_says_what_its_locked_door_says():
    for name, text, riddle in castle.CASTLE_LEVELS:
        ok(riddle and riddle.startswith(("Locked!", "The throne room is locked!")), "%s: %r" % (name, riddle))
        ok("D" in "".join(caves.level_lines(text)), "%s has its locked door" % name)


def test_saving_a_cave_keeps_its_settings():
    text = caves.CAVE_LEVELS[10]            # The Lava Escape: it has "lava rises"
    theme, rows, _ = cave_files.read_cave(text)
    again = cave_files.cave_text(theme, rows, cave_files.settings_of(text))
    for setting in ("theme", "name", "lava rises", "about"):
        ok(caves.level_setting(again, setting) == caves.level_setting(text, setting), "keeps %s" % setting)


def test_the_web_version_gets_the_levels_folder():
    with open(os.path.join(GAME_FOLDER, "web", "build_web.py"), encoding="utf-8") as f:
        ok('GAME_FOLDERS = ["levels"]' in f.read(), "web/build_web.py copies the levels folder into the web page")


def test_in_cave_1_you_ride_the_lift_up_to_the_lever():
    """Cave 1's lever sits on a rock 5 blocks above the floor: too high to jump, so the
    up-and-down lift (the column of U's) is the only way up to it."""
    import cave_solver
    import robot
    path = os.path.join(GAME_FOLDER, "levels", "caves", "01_the_easy_moss_cave.txt")
    with open(path) as f:
        text = f.read()
    for no_lift in (False, True):
        cave = cave_solver.fresh_cave(text.replace("U", ".") if no_lift else text)
        moves, _, n = robot.search(cave, lambda cave: cave.gates_open(), robot.where(cave, caves.LEVER))
        if no_lift:
            ok(moves is None, "without the lift the robot can't get up to the lever (it tried %d moves)" % n)
        else:
            ok(moves is not None, "riding the lift, the robot pulls the lever")
