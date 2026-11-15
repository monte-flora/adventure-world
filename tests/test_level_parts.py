"""
The new parts for caves and castle levels: secret walls (F), levers (L) and iron gates (G),
flame jets (J), steam geysers (M) and moving platforms (P side to side, U up and down).

Every test draws its own little cave right here.
"""

import caves
import cave_files
import robot
from helpers import cave_from, feet, ok, run


def test_a_secret_wall_looks_like_rock_but_you_walk_right_through_it():
    world, cave = cave_from(["##########",
                             "#........#",
                             "#.S..FF.E#",
                             "##########"])
    ok(not cave.is_solid(2, 5), "a secret wall isn't solid")
    run(cave, 120, right=True)
    ok(cave.result == "exit", "you walk through it to the exit")
    ok(cave.map[2][5] == "." and cave.map[2][6] == ".", "and the whole secret wall melts away")
    ok(cave.changes.get((2, 6)) == ".", "for good (it stays found when you come back)")


def test_a_lever_opens_every_iron_gate():
    rows = ["###########",
            "#.........#",
            "#.SL.G.G.E#",
            "###########"]
    world, cave = cave_from(rows)
    run(cave, 90, right=True)
    ok(cave.result is None and cave.you.x < 5, "an iron gate is solid: it stops you")
    world, cave = cave_from(rows)
    cave.you.facing = 1
    run(cave, 1, use_pressed=True)
    ok(cave.map[2][3] == "l", "R next to the lever pulls it")
    ok(cave.map[2][5] == "g" and cave.map[2][7] == "g" and cave.gates_open(), "and both gates open")
    run(cave, 120, right=True)
    ok(cave.result == "exit", "now you can walk through to the exit")


def test_a_flame_jet_only_hurts_while_it_fires():
    rows = ["##########",
            "#........#",
            "#........#",
            "#.S..J..E#",
            "##########"]
    world, cave = cave_from(rows)
    cave.clock = 0.0                                     # off: run right past it
    run(cave, 60, right=True)
    ok(cave.result == "exit" and world.player.health == world.player.max_health, "it's off: you run past it")
    world, cave = cave_from(rows)
    cave.clock = caves.TRAP_DOWN + 0.05                  # on: fire shoots up
    cave.you.x = 4.9
    cave.you.y = 1.5                                     # in the air, 2 blocks above the jet
    run(cave, 1)
    ok(world.player.health < world.player.max_health, "it's on: the fire reaches up and hurts you")


def test_a_steam_geyser_throws_you_way_up_while_it_puffs():
    world, cave = cave_from(["##########"] + ["#........#"] * 10 + ["#..S.....#", "###M######"])
    cave.clock = 0.0
    lowest = feet(cave)
    run(cave, 40)
    ok(feet(cave) == lowest, "standing on it while it's quiet: nothing happens")
    highest = lowest
    for _ in range(200):
        run(cave, 1)
        highest = min(highest, feet(cave))
    ok(lowest - highest > 6, "then WHOOSH: it throws you more than 6 blocks up (%.1f)" % (lowest - highest))


def test_a_platform_carries_you_side_to_side():
    world, cave = cave_from(["############",
                             "#..........#",
                             "#..........#",
                             "#.S.PPPPPP.#",
                             "#..........#",
                             "############"])
    ok(len(cave.platforms) == 1 and cave.platforms[0].w == 2, "a row of P's is one platform, 2 blocks wide")
    ok(cave.map[3][4] == ".", "(its letters turn into air)")
    platform = cave.platforms[0]
    ok((platform.low, platform.high) == (4, 8), "it slides along the P's: %s" % ((platform.low, platform.high),))
    cave.you.x, cave.you.y = 4.1, 3 - caves.PLAYER_H - 0.2
    run(cave, 10)
    ok(cave.you.on_ground and cave.you.riding == 0, "you land on it")
    x = cave.you.x
    run(cave, 60)
    ok(cave.you.on_ground and cave.you.x - x > 1.5, "and it carries you along (%.2f blocks)" % (cave.you.x - x))


def test_a_platform_carries_you_up_and_down():
    world, cave = cave_from(["##########",
                             "#........#",
                             "#........#",
                             "#....UU..#",
                             "#....UU..#",
                             "#.S..UU..#",
                             "#........#",
                             "##########"])
    platform = cave.platforms[0]
    ok(platform.axis == "y" and platform.w == 2 and (platform.low, platform.high) == (3, 5),
       "a 2-wide column of U's is one platform, riding from its top U to its bottom U: %s"
       % ((platform.low, platform.high),))
    cave.you.x, cave.you.y = 5.1, 3 - caves.PLAYER_H - 0.2
    run(cave, 10)
    heights = []
    for _ in range(240):
        run(cave, 1)
        heights.append(feet(cave))
        ok(cave.you.on_ground, "you stay on it the whole ride")
    ok(min(heights) < 3.3 and max(heights) > 4.7, "up to the top and back down: %.1f to %.1f" % (min(heights), max(heights)))


def test_you_draw_the_path_a_platform_rides():
    world, cave = cave_from(["############",
                             "#..........#",
                             "#...U......#",
                             "#...U.PPPP.#",
                             "#...U......#",
                             "#.S........#",
                             "############"])
    up, side = sorted(cave.platforms, key=lambda p: p.axis, reverse=True)
    ok(len(cave.platforms) == 2, "a column of U's is ONE platform, and so is a row of P's")
    ok(up.axis == "y" and (up.low, up.high) == (2, 4), "it goes up and down just the column you drew")
    ok(side.axis == "x" and side.w == 2 and (side.low, side.high) == (6, 8),
       "a 2-wide platform slides along just the row you drew")


def path_of(platform, seconds=20):
    """Everywhere a platform goes in some seconds: (smallest, biggest) top-left spot along its axis."""
    spots = [platform.where(t / 60)[0 if platform.axis == "x" else 1] for t in range(int(seconds * 60))]
    return min(spots), max(spots)


def test_a_platform_turns_around_at_the_ends_of_its_track_in_open_space():
    # Lots of open air on both sides: it still turns right at the ends of the P's
    world, cave = cave_from(["##########################",
                             "#........................#",
                             "#..........PPPPP.........#",
                             "#........................#",
                             "#.S......................#",
                             "##########################"])
    platform = cave.platforms[0]
    first, last = path_of(platform)
    ok((round(first, 3), round(last + platform.w, 3)) == (11, 16),
       "it covers just the P's, columns 11 to 15: %.2f to %.2f" % (first, last + platform.w))
    ends = [platform.where(t / 60)[0] for t in range(1200)]
    turns = [round(ends[i], 1) for i in range(1, len(ends) - 1) if (ends[i] - ends[i - 1]) * (ends[i + 1] - ends[i]) < 0]
    ok(turns and set(turns) <= {11.0, 14.0}, "and it only turns around at the two ends: %s" % sorted(set(turns)))


def test_a_platform_never_goes_past_the_end_of_its_track():
    # Same track, once with open air past its ends and once with rock right next to it: same ride
    rows = ["##############",
            "#............#",
            "#....PPPP....#",
            "#.S..........#",
            "##############"]
    walled = rows[:2] + ["#...#PPPP#...#"] + rows[3:]
    for drawing, what in ((rows, "open air"), (walled, "rock")):
        world, cave = cave_from(drawing)
        platform = cave.platforms[0]
        ok(path_of(platform) == (5, 7) and (platform.low, platform.high) == (5, 7),
           "with %s past the ends, it slides from column 5 to 7: %s" % (what, path_of(platform),))
    world, cave = cave_from(["##########", "#........#", "#...PP...#", "#.S......#", "##########"])
    ok(not cave.platforms[0].moves() and path_of(cave.platforms[0]) == (4, 4),
       "just 2 P's: no room to slide, so it stays put (it doesn't wander off until it bumps into something)")


def test_an_up_and_down_platform_turns_at_the_top_and_bottom_u():
    rows = ["##########",
            "#........#",
            "#........#",
            "#........#",
            "#....U...#",
            "#....U...#",
            "#....U...#",
            "#........#",
            "#........#",
            "#.S......#",
            "##########"]
    world, cave = cave_from(rows)
    platform = cave.platforms[0]
    ok(path_of(platform) == (4, 6), "lots of air above and below, but it rides just rows 4 to 6: %s"
       % (path_of(platform),))
    ok(all(platform.where(t / 60)[0] == 5 for t in range(600)), "(and it doesn't drift sideways)")
    world, cave = cave_from(rows[:3] + ["#....#...#"] + rows[4:7] + ["#....#...#"] + rows[8:])
    ok(path_of(cave.platforms[0]) == (4, 6), "rock right above and below: the same ride")
    world, cave = cave_from(["########", "#......#", "#......#", "#..UU..#", "#.S....#", "########"])
    ok(not cave.platforms[0].moves() and path_of(cave.platforms[0]) == (3, 3), "just one row of U's: it stays put")


def test_the_robot_knows_where_a_platform_goes():
    rows = ["####################",
            "#..................#",
            "#..................#",
            "#..................#",
            "#..............*E..#",
            "#...........=#######",
            "#.........U........#",
            "#.........U........#",
            "#.........U........#",
            "#.........U........#",
            "#.........U........#",
            "..S................#",
            "####################"]
    cave = cave_from(rows)[1]
    ok(set(cave.platforms[0].cells()) == {(r, 10) for r in range(6, 11)},
       "the robot's map counts just the U's as places a platform can hold you up")
    beaten, how = robot.beat("\n".join(rows))
    ok(beaten, "the robot rides the platform up to the top of its track, and jumps to the diamond: %s" % how)


def test_the_robot_pulls_the_lever_first():
    rows = ["####################",
            "#..................#",
            "#..........L.......#",
            "#.........===......#",
            "#..................#",
            "#..............#G#.#",
            "..S............#*#E#",
            "####################"]
    beaten, how = robot.beat("\n".join(rows))
    ok(beaten, "the robot pulls the lever, then digs out the diamond: %s" % how)


def test_the_robot_rides_platforms_and_times_jets_and_geysers():
    rows = ["########################",
            "#......................#",
            "#......................#",
            "#......................#",
            "#......................#",
            "#......................#",
            "#....................*E#",
            "#...................####",
            "#......................#",
            "#......................#",
            "#......................#",
            "#......................#",
            "..S.PPP.......J........#",
            "#####~~~~~~#######M#####"]
    beaten, how = robot.beat("\n".join(rows))
    ok(beaten, "the robot gets over the lava, past the jet and up the geyser: %s" % how)


def test_the_editor_knows_the_new_parts():
    for letter in "FGJMPUL":
        ok(letter in cave_files.EVERY_LETTER, "%s is a letter the editor knows" % letter)
    rows = ["#####", "#S.G#", "#####"]
    ok(any("no lever" in message for _, message in cave_files.check_cave("stone", rows)),
       "a gate without a lever gets a tip")
