"""
Swinging vines (R): jump into one to grab it, pump LEFT and RIGHT to swing higher,
and SPACE lets go: you fly off with the swing's speed. The robot can use them too.

Every test draws its own little cave right here (except the ones about the two little vine caves in my_caves).
"""

import os

import pytest

import cave_files
import cave_solver
import caves
import editor
import robot
from helpers import cave_from, frames, new_app, ok, run

# A vine 6 blocks long hangs from the rock over a pit of spikes, too wide to jump
SPIKE_PIT = ["#######################",
             "#....######...........#",
             "#....######...........#",
             "#....######...........#",
             "#......R..............#",
             "#......R..............#",
             "#......R..............#",
             "#......R..............#",
             "#......R..............#",
             "#......R..............#",
             "#.....................#",
             "#.....................#",
             "#S...^^^^^^^^^^......E#",
             "#######################"]


def jump_into_the_vine(cave):
    """Run right, jump at the edge of the pit, and grab the vine."""
    you = cave.you
    for _ in range(80):
        jump = you.on_ground and you.x > 3.6
        run(cave, 1, right=True, jump=True, jump_pressed=jump, space_pressed=jump)
        if you.swinging is not None:
            return True
    return False


def pump(cave, frames_to_go):
    """Lean the way the vine is swinging (that's how you pump it higher). Returns how high it got."""
    swing, highest = cave.swings[0], 0.0
    for _ in range(frames_to_go):
        run(cave, 1, right=swing.spin > 0, left=swing.spin < 0)
        highest = max(highest, abs(swing.angle))
    return highest


def just_hang(cave, frames_to_go):
    swing, highest = cave.swings[0], 0.0
    for _ in range(frames_to_go):
        run(cave, 1)
        highest = max(highest, abs(swing.angle))
    return highest


def test_a_column_of_rs_is_one_vine_and_turns_into_air():
    world, cave = cave_from(SPIKE_PIT)
    ok(len(cave.swings) == 1, "one column of R's makes one swinging vine")
    swing = cave.swings[0]
    ok((swing.r, swing.c, swing.length) == (4, 7, 6), "it hangs from row 4, column 7, and is 6 blocks long")
    ok(all(cave.map[r][7] == "." for r in range(4, 10)), "the R's are air (you only bump into the vine itself)")
    ok(swing.angle == 0 and swing.spin == 0, "it starts hanging straight down")
    ok(caves.SWINGING_VINE not in "".join(caves.LADDERS), "it's not a climbing vine (V): those work like ladders")


def test_jumping_into_a_vine_grabs_it():
    world, cave = cave_from(SPIKE_PIT)
    you = cave.you
    run(cave, 30, right=True)
    ok(you.swinging is None, "walking along the floor doesn't grab it")
    world, cave = cave_from(SPIKE_PIT)
    ok(jump_into_the_vine(cave), "jumping into the vine grabs it")
    you, swing = cave.you, cave.swings[0]
    ok(swing.held and 1 <= you.grip <= swing.length, "your hands are on the vine (%.2f blocks down)" % you.grip)
    hand_x, hand_y = cave.hands()
    x, y = swing.point(you.grip)
    ok(abs(hand_x - x) < 0.01 and abs(hand_y - y) < 0.01, "and you hang right where you hold it")
    ok(swing.spin > 0, "your running jump got it swinging the way you were going")
    run(cave, 60)
    ok(you.swinging is not None and not you.on_ground and world.player.health == world.player.max_health,
       "you hang on safely over the spikes")


def test_pumping_left_and_right_swings_you_higher():
    world, cave = cave_from(SPIKE_PIT)
    jump_into_the_vine(cave)
    lazy = just_hang(cave, 240)
    world, cave = cave_from(SPIKE_PIT)
    jump_into_the_vine(cave)
    pumped = pump(cave, 240)
    ok(pumped > lazy + 0.3, "pumping swings higher (%.2f) than just hanging on (%.2f)" % (pumped, lazy))
    ok(pumped <= caves.SWING_MAX + 1e-6, "but never higher than SWING_MAX (%.2f)" % pumped)
    ok(pump(cave, 240) > caves.SWING_MAX - 0.1, "keep pumping and it goes as high as it can")


def test_space_lets_go_and_you_fly_off_with_the_swings_speed():
    world, cave = cave_from(SPIKE_PIT)
    jump_into_the_vine(cave)
    pump(cave, 300)
    you, swing = cave.you, cave.swings[0]
    for _ in range(300):                         # wait until you're swinging forward and up
        if swing.spin > 0 and 0.4 < swing.angle < 0.8:
            break
        pump(cave, 1)
    speed_x = you.grip * swing.spin * caves.math.cos(swing.angle)
    run(cave, 1, jump=True, jump_pressed=True, space_pressed=True)
    ok(you.swinging is None and not swing.held, "SPACE lets go of the vine")
    ok(you.vx > caves.RUN_SPEED and abs(you.vx - speed_x) < 1, "you fly off as fast as the vine swung (%.1f)" % you.vx)
    ok(you.vy < 0, "with a little hop up")
    run(cave, 10)
    ok(you.vx > caves.RUN_SPEED, "you keep that speed in the air, even without holding RIGHT (%.1f)" % you.vx)
    run(cave, 90)
    ok(you.on_ground and you.x > 16 and world.player.health == world.player.max_health,
       "and you land safely past the spikes (x = %.1f)" % you.x)
    ok(you.swing_wait == 0 and not you.flung, "after landing you run normally again")


def test_a_vine_you_let_go_of_swings_by_itself_then_hangs_still():
    world, cave = cave_from(SPIKE_PIT)
    jump_into_the_vine(cave)
    pump(cave, 120)
    run(cave, 1, down=True)
    swing = cave.swings[0]
    ok(cave.you.swinging is None, "DOWN just drops off the vine")
    ok(swing.angle or swing.spin, "the vine keeps swinging for a bit")
    run(cave, 600)
    ok(swing.angle == 0 and swing.spin == 0, "then it hangs still again")


def test_getting_hurt_knocks_you_off_the_vine():
    world, cave = cave_from(SPIKE_PIT)
    jump_into_the_vine(cave)
    cave.put_you_back(0)
    ok(cave.you.swinging is None and not cave.swings[0].held, "knocked back to safety: you let go of the vine")


def test_the_robot_can_swing_across_and_knows_it_needs_the_vine():
    text = "\n".join(SPIKE_PIT)
    result = cave_solver.check(text, tries=150000)
    ok(result["exit"], "the robot swings across the spikes to the exit: %s" % cave_solver.say(result))
    result = cave_solver.check(text.replace(caves.SWINGING_VINE, "."), tries=50000)
    ok(result["exit"] is False, "without the vine it can't get across")


def test_the_robot_knows_where_a_vine_can_take_you():
    cave = cave_solver.fresh_cave("\n".join(SPIKE_PIT))
    reach = cave.swings[0].reach()
    ok((9, 7) in reach and (7, 12) in reach and (7, 2) in reach, "the vine's reach covers its whole swing")
    far = cave_solver.steps_to(cave, [(12, 21)])
    ok(far[9][7] < cave_solver.FAR_AWAY, "so its map of how far has a way across")


# Two little caves to copy from, in the my_caves folder (they were cave pieces once)
SWING_CAVES = ["swing_over_the_spikes.txt", "two_vines_over_the_lava.txt"]


def swing_cave(file_name):
    with open(os.path.join(os.path.dirname(os.path.abspath(caves.__file__)), "my_caves", file_name), encoding="utf-8") as f:
        return f.read()


def test_there_are_little_caves_with_swinging_vines():
    ok(all(caves.SWINGING_VINE in "".join(caves.level_lines(swing_cave(name))) for name in SWING_CAVES),
       "%d little caves in my_caves use swinging vines" % len(SWING_CAVES))


@pytest.mark.parametrize("file_name", SWING_CAVES)
def test_every_swinging_vine_cave_can_be_beaten_and_needs_its_vines(file_name):
    text = swing_cave(file_name)
    beaten, how = robot.beat(text)
    ok(beaten, "%s: %s" % (file_name, how))
    rows = "\n".join(caves.level_lines(text))
    beaten, how = robot.beat(rows.replace(caves.SWINGING_VINE, "."), tries=40000)
    ok(not beaten, "without its vines %s can't be crossed" % file_name)


def test_the_editor_has_swinging_vines():
    ok(caves.SWINGING_VINE in "".join(group for _, group in editor.PALETTE), "the palette has swinging vines")
    ok(caves.SWINGING_VINE in editor.BLOCKS and caves.SWINGING_VINE in cave_files.EVERY_LETTER,
       "with a name and help words, and the editor knows the letter")
    floating = ["#####", "#...#", "#.R.#", "#.R.#", "#S..#", "#####"]
    problems = cave_files.check_cave("stone", floating)
    ok(any("hangs from nothing" in words for _, words in problems), "the checklist spots a vine with no rock above it")
    tied = ["#####", "#.R.#", "#.R.#", "#...#", "#S..#", "#####"]
    ok(not any("hangs from nothing" in words for _, words in cave_files.check_cave("stone", tied)),
       "a vine tied on under rock is fine")


def test_the_game_draws_swinging_vines_in_every_look():
    app = new_app()
    for theme in ("stone", "moss", "crystal", "lava"):
        world = app.game
        cave = caves.Cave(world, world.start, "theme: %s\n%s" % (theme, "\n".join(SPIKE_PIT)))
        world.cave = cave
        frames(app, 2)
        jump_into_the_vine(cave)
        frames(app, 2)                           # drawing you on the vine works too
        ok(cave.you.swinging is not None, "swinging in a %s cave" % theme)
