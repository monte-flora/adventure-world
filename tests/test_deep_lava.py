"""
Deep lava pools: lava drawn 2 or 3 blocks tall in the floor is one deeper pool.
Only its top block has the moving lava surface; the blocks under it are deep lava,
with no gap between them. It hurts just like lava, the rising lava still works,
and the robot still never touches it.
"""

import pygame
import pytest

import cave_solver
import caves
import game
from helpers import DT, cave_from, new_app, ok, run

POOLS = ["####################",
         "#..................#",
         "#..................#",
         "#S...............E.#",
         "###~####~~####~~####",       # pools 1, 2 and 3 deep
         "########~~####~~####",
         "##############~~####",
         "####################"]


def test_lava_under_lava_hurts_from_the_top_of_its_block():
    world, cave = cave_from(POOLS)
    ok(cave.hazard_top(4, 3) == caves.HAZARD_TOP["~"], "the top of a pool starts a little way down its block")
    ok(cave.hazard_top(5, 8) == 0 and cave.hazard_top(6, 14) == 0,
       "deep lava under the top is lava all the way up its block")
    ok(cave.hazard_top(4, 8) == caves.HAZARD_TOP["~"], "the top block of a deep pool is like any pool")


@pytest.mark.parametrize("column", [3, 8, 14])
def test_falling_in_a_deep_pool_hurts_like_lava(column):
    world, cave = cave_from(POOLS)
    health = world.player.health
    cave.you.x, cave.you.y, cave.you.vx = column + 0.5 - cave.you.w / 2, 3 - cave.you.h, 0.0
    cave.you.safe_time = 0
    for _ in range(60):
        run(cave, 1)
        if world.player.health < health:
            break
    ok(health - world.player.health == caves.LAVA_DAMAGE,
       "falling in the pool at column %d hurts %d (it hurt %d)" % (column, caves.LAVA_DAMAGE, health - world.player.health))


def test_a_monster_falls_in_a_deep_pool():
    world, cave = cave_from(POOLS)
    cave.monsters = []
    cave.you.x = 12.1                                      # far away, so it doesn't come after you
    m = cave.add_monster("Zombie", 3, 8)                   # right over the 2-deep pool
    run(cave, 60)
    ok(m not in cave.monsters, "a monster that falls in the deep pool is beaten")


def draw(theme):
    app = new_app()
    world, cave = cave_from(["theme: %s" % theme] + POOLS, app.game)
    app.game.cave = cave
    app.build_cave_tiles(cave)
    app.cam = (0, 0)
    app.time = 1.0
    surf = pygame.Surface((game.VIEW_W, game.VIEW_H))
    app.draw_cave(surf)
    return surf


def lava_colored(color):
    return color[0] > 150 and color[0] > color[1] + 60


@pytest.mark.parametrize("theme", ["stone", "lava", "moss"])
def test_only_the_top_of_a_deep_pool_has_a_surface(theme):
    surf = draw(theme)
    T = game.TILE
    for c in (8, 9, 14, 15):
        x = c * T + T // 2
        top = surf.get_at((x, 4 * T + 2))
        ok(not lava_colored(top), "%s cave: the top block of the pool at column %d shows rock above its lava %s"
           % (theme, c, top))
        deepest = 6 if c >= 14 else 5
        for y in range(5 * T, (deepest + 1) * T, 2):     # every pixel down the deep part is lava: no gaps
            ok(lava_colored(surf.get_at((x, y))), "%s cave: deep lava in column %d at y=%d is all lava (%s)"
               % (theme, c, y, surf.get_at((x, y))))
    ok(not all(lava_colored(surf.get_at((3 * T + T // 2, y))) for y in range(5 * T, 6 * T, 2)),
       "%s cave: the 1-deep pool has rock under it, not more lava" % theme)


def test_rising_lava_rises_over_deep_pools():
    rows = ["theme: lava", "lava rises: yes"] + POOLS
    world, cave = cave_from(rows)
    cave.you.x, cave.you.y = 12.1, 3 - caves.PLAYER_H
    cave.start_rising_lava()
    start = cave.lava_line
    run(cave, int(caves.LAVA_RISE_WAIT * 60) + 60)
    ok(cave.lava_line < start - 0.5, "the lava still rises in a cave with deep pools (%.2f to %.2f)" % (start, cave.lava_line))


def test_the_robot_never_touches_a_deep_pool():
    ok("~" in cave_solver.NO_GO, "lava is somewhere the robot never goes")
    text = "\n".join(POOLS[:3] + ["#S.......*.......E.#"] + POOLS[4:])
    result = cave_solver.check(text, time_limit=60)
    ok(result["exit"] is not None, "the robot gets past pools 1, 2 and 3 deep")
    cave = cave_solver.fresh_cave(text)
    for x, y in result["trail"]:
        ok(cave.tile(int(y), int(x)) != "~", "the robot's trail never goes in the lava (%.2f, %.2f)" % (x, y))
