"""
CAN EVERY CAVE BE BEATEN?

A robot (robot.py) plays each cave. It has to dig out the diamond (if the cave has one)
and then walk through the EXIT door, without getting hurt even once. It ignores the
monsters: beating those is up to you!

Checked every time:
- every hand-drawn cave in CAVE_LEVELS (the levels/caves folder),
  except a level whose file says "robot check: later" (still being worked on),
- the 3 shadow caves under the Mines in Nightfall Hollow (levels/shadow): dig out the Sun Shard, then the
  diamond, then walk through the exit,
- every level of the Shadow King's castle (castle.py): get the key (or pull the lever),
  then go through the door,
- the cave under the Secret Mine (levels/secret).

Every Mine plays one of those files, so that's every cave in the game. Some Mines have a treasure chest
where the diamond ore was. To check every Mine's cave just the way the game plays it, too (it's slow!):
    pixi run test-all-caves
"""

import pytest

import castle
import caves
import rules
import robot
from helpers import ok, steps

# The same Mine always gets the same cave, whatever the seed, so any world will do.
WORLD = rules.Game("Hero", seed=1)
MINES = sorted(WORLD.cave_plan, key=lambda mine: (steps(mine, WORLD.start), mine))     # nearest home first


def skip_if_checked_later(text):
    """A level whose file says "robot check: later" is still being worked on: the robot skips it for now.
    Take that line out (or fix the level in the editor) to check it again."""
    if caves.level_setting(text, "robot check") == "later":
        pytest.skip("%s says \"robot check: later\"" % caves.level_setting(text, "name"))


def mine_name(mine):
    diamond = "diamond" if mine in WORLD.diamond_mines else "no diamond"
    return "Mine at row %d, column %d (%s)" % (mine[0], mine[1], diamond)


@pytest.mark.parametrize("number", range(len(caves.CAVE_LEVELS)), ids=lambda n: "hand-drawn cave %d" % n)
def test_hand_drawn_cave_can_be_beaten(number):
    skip_if_checked_later(caves.CAVE_LEVELS[number])
    beaten, how = robot.beat(caves.CAVE_LEVELS[number])
    ok(beaten, "hand-drawn cave %d in CAVE_LEVELS: %s" % (number, how))


@pytest.mark.parametrize("number", range(len(caves.SHADOW_CAVES)), ids=lambda n: "shadow cave %d" % (n + 1))
def test_shadow_cave_can_be_beaten(number):
    """Each one has a diamond AND a Sun Shard (harder to reach): the robot digs out both, then leaves."""
    text = caves.SHADOW_CAVES[number]
    ok(caves.level_theme(text) == "shadow" and "*" in text and caves.SHARD in text,
       "shadow cave %d is a shadow-look cave with a diamond and a Sun Shard" % (number + 1))
    beaten, how = robot.beat(text)
    ok(beaten, "shadow cave %d: %s" % (number + 1, how))


@pytest.mark.parametrize("level", range(len(castle.CASTLE_LEVELS)),
                         ids=lambda level: "castle level %d, %s" % (level + 1, castle.CASTLE_LEVELS[level][0]))
def test_castle_level_can_be_beaten(level):
    skip_if_checked_later(castle.CASTLE_LEVELS[level][1])
    beaten, how = robot.beat_castle_level(level)
    ok(beaten, "castle level %d (%s): %s" % (level + 1, castle.CASTLE_LEVELS[level][0], how))


@pytest.mark.parametrize("number", range(len(caves.SECRET_CAVES)), ids=lambda n: "secret cave %d" % (n + 1))
def test_secret_cave_can_be_beaten(number):
    text = caves.SECRET_CAVES[number]
    skip_if_checked_later(text)
    ok("*" in text, "the Secret Mine's cave has a diamond")
    beaten, how = robot.beat(text)
    ok(beaten, "the cave under the Secret Mine (levels/secret): %s" % how)


@pytest.mark.all_caves            # only with --all-caves (pixi run test-all-caves)
@pytest.mark.parametrize("mine", MINES, ids=mine_name)
def test_the_cave_under_every_mine_can_be_beaten_the_way_the_game_plays_it(mine):
    """The same files again, but as the game hands them out: a Mine without a diamond has a chest instead."""
    text = WORLD.cave_text(mine)
    skip_if_checked_later(text)
    beaten, how = robot.beat(text)
    ok(beaten, "the cave under the %s: %s" % (mine_name(mine), how))


def test_the_robot_can_tell_when_a_cave_cant_be_beaten():
    """The robot must not just say yes to everything: here the exit is up on a wall too high to jump."""
    too_high = ["##########",
                "#.......E#",
                "#.......##",
                "#........#",
                "#........#",
                "#........#",
                "..S......#",
                "##########"]
    beaten, how = robot.beat("\n".join(too_high), tries=20000)
    ok(not beaten, "the robot should say this cave can't be beaten, but it said: %s" % how)
