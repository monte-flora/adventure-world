"""
Moving around in a cave: ladders, climbing walls, wall jumps, ledge grabs,
ground pounds and crawling through tunnels.

Every test draws its own little cave right here, so it doesn't matter how
the real caves in caves.py look.
"""

import caves
import sprites
import pygame

from helpers import cave_from, feet, frames, hold_keys, new_app, ok, run, walk_into_a_mine

LADDER = ["##############",
          "#............#",
          "#.............",
          "#......H######",
          "#......H.....#",
          "#......H.....#",
          "#......H.....#",
          "#......H.....#",
          "..S....H.....#",
          "##############"]


def test_climbing_a_ladder():
    world, cave = cave_from(LADDER)
    you = cave.you
    you.x = 7.1
    run(cave, 5)
    ok(not you.climbing and you.on_ground, "standing at the foot of a ladder")
    run(cave, 1, up=True, jump=True, jump_pressed=True)
    ok(you.climbing and you.buffer == 0, "pressing UP at a ladder grabs it (no jump)")
    run(cave, 120, up=True, jump=True)
    ok(not you.climbing and you.on_ground and feet(cave) == 3.0,
       "hold UP: you climb to the top and stand on the top rung (feet at %.2f)" % feet(cave))
    run(cave, 20, right=True)
    ok(you.on_ground and you.x > 8 and feet(cave) == 3.0, "...then walk off onto the platform")


def test_climbing_down_and_jumping_off_a_ladder():
    world, cave = cave_from(LADDER)
    you = cave.you
    you.x = 7.1
    run(cave, 5)
    run(cave, 1, up=True, jump=True, jump_pressed=True)
    run(cave, 120, up=True, jump=True)                     # up at the top
    you.x = 7.1
    run(cave, 3)
    run(cave, 30, down=True)
    ok(you.climbing and feet(cave) > 3.5, "DOWN on the top rung climbs back down")
    run(cave, 1, right=True, space_pressed=True, jump_pressed=True, jump=True)
    ok(not you.climbing and you.vy < 0 and you.vx > 0, "SPACE jumps off the ladder (to the side you hold)")
    run(cave, 120)
    ok(you.on_ground and feet(cave) == 9.0, "and you land on the floor")


def test_up_still_jumps_away_from_ladders():
    world, cave = cave_from(LADDER)
    you = cave.you
    you.x = 3.1
    run(cave, 5)
    run(cave, 1, up=True, jump=True, jump_pressed=True)
    ok(you.vy < 0 and not you.climbing, "away from ladders, UP still jumps")


def test_monsters_stand_on_top_rungs():
    world, cave = cave_from(LADDER)
    zombie = cave.add_monster("Zombie", 2, 8)
    zombie.x = 7.1
    zombie.y = 3 - zombie.h - 0.5
    for _ in range(60):
        cave.step(1 / 60, {})
    ok(abs(zombie.y + zombie.h - 3.0) < 0.01, "a monster can stand on a ladder's top rung")


def test_getting_hit_knocks_you_off_a_ladder():
    world, cave = cave_from(LADDER)
    you = cave.you
    you.x = 7.1
    run(cave, 3)
    run(cave, 10, up=True)
    cave.hurt_you(1, you.x + 1)
    ok(not you.climbing, "a monster's hit knocks you off a ladder")


# ===========================================================================
# Climbing walls (%): slide down them, wall jump off them, climb them
# ===========================================================================

CHIMNEY = ["##########",
           "#........#",
           "#........#",
           "#..%.%####",
           "#..%.%...#",
           "#..%.%...#",
           "#..%.%...#",
           "#..%.%...#",
           "#..%.%...#",
           "..S%.%...#",
           "##########"]


def test_sliding_and_wall_jumping():
    world, cave = cave_from(CHIMNEY)
    you = cave.you
    you.x, you.y, you.vy = 4.1, 3.5, 5
    run(cave, 10, right=True)
    ok(you.vy <= caves.WALL_SLIDE + 1e-6 and you.wall_side == 1, "holding toward a climbing wall, you slide down it slowly")
    run(cave, 1, right=True, jump=True, jump_pressed=True, space_pressed=True)
    ok(you.vx < 0 and you.vy < 0, "SPACE: wall jump, away from the wall")


def test_wall_jumping_up_a_chimney():
    world, cave = cave_from(CHIMNEY)
    you = cave.you
    you.x, you.y, you.vx, you.vy = 4.1, 9 - caves.PLAYER_H, 0, 0
    highest = 99
    for _ in range(600):          # bounce between the two walls: hold toward the wall you're on, and jump
        toward = "right" if you.x > 4.0 else "left"
        controls = {toward: True, "jump": True}
        if you.wall_time > 0 or you.on_ground:
            controls.update(jump_pressed=True, space_pressed=True)
        if you.wall_push > 0:
            controls = {"jump": True}
        cave.update(1 / 60, controls)
        highest = min(highest, you.y + you.h)
    ok(highest < 4, "you can climb up a chimney of climbing walls (your feet got up to %.1f)" % highest)


def test_plain_rock_is_not_a_climbing_wall():
    world, cave = cave_from(["########",
                             "#......#",
                             "#......#",
                             "#..#####",
                             "#..#...#",
                             "#..#...#",
                             "#..#...#",
                             "..S#...#",
                             "########"])
    you = cave.you
    you.x, you.y, you.vy = 2.1, 4.0, 5
    run(cave, 10, right=True)
    ok(you.vy > caves.WALL_SLIDE + 0.5 or you.on_ground, "normal rock walls don't slow you down - no wall jumps there")


CLIMBING_WALL = ["##########",
                 "#........#",
                 "#........#",
                 "#....#####",
                 "#....%####",
                 "#....%####",
                 "#....%####",
                 "#....%####",
                 "#....%####",
                 "..S..%####",
                 "##########"]
CLIMBING_WALL_TO_THE_TOP = CLIMBING_WALL[:3] + ["#....%####"] + CLIMBING_WALL[4:]


def grab_the_wall(drawing):
    world, cave = cave_from(drawing)
    cave.you.x = 4.0
    run(cave, 5)
    run(cave, 20, right=True)
    run(cave, 1, up=True, jump=True, jump_pressed=True)
    return cave


def test_climbing_a_climbing_wall():
    cave = grab_the_wall(CLIMBING_WALL)
    you = cave.you
    ok(you.on_wall == 1 and you.buffer == 0, "UP next to a climbing wall grabs it (no jump)")
    run(cave, 200, up=True, jump=True)
    ok(you.on_wall == 1 and you.y > 3.5, "plain rock above the climbing wall: you stop there (y %.1f)" % you.y)

    cave = grab_the_wall(CLIMBING_WALL_TO_THE_TOP)
    run(cave, 200, up=True, jump=True)
    ok(not cave.you.on_wall and cave.you.on_ground and feet(cave) == 3.0,
       "climb all the way up and you pull yourself onto the top (feet at %.2f)" % feet(cave))


def test_jumping_and_climbing_down_off_a_climbing_wall():
    cave = grab_the_wall(CLIMBING_WALL_TO_THE_TOP)
    you = cave.you
    run(cave, 40, up=True, jump=True)
    run(cave, 1, space_pressed=True, jump_pressed=True, jump=True)
    ok(not you.on_wall and you.vx < 0 and you.vy < 0, "SPACE jumps off the climbing wall")
    run(cave, 120)
    ok(you.on_ground and feet(cave) == 10.0, "and you land back on the floor")

    cave = grab_the_wall(CLIMBING_WALL_TO_THE_TOP)
    run(cave, 30, up=True, jump=True)
    run(cave, 60, down=True)
    ok(not cave.you.on_wall and cave.you.on_ground and feet(cave) == 10.0, "DOWN climbs back down to the floor")


def test_climbing_wall_pictures(monkeypatch):
    """On a climbing wall the Hero goes hand over hand as he moves, holds still when he stops,
    grips the wall when he slides down it, and puts his tool away (so it can't poke into the wall)."""
    keys = hold_keys(monkeypatch)
    app = new_app()
    walk_into_a_mine(app)
    world, cave = cave_from(CLIMBING_WALL_TO_THE_TOP, world=app.game)
    app.reset_visuals()
    you = cave.you
    you.x = 4.0
    frames(app, 5)
    you.x, you.on_ground = 5 - you.w, False      # right up against the wall
    app.game.cave.grab_wall(1)
    climbing = {id(sprites.WALL_1), id(sprites.WALL_2), id(sprites.WALL_HOLD)}

    def picture(*held):
        keys.clear()
        keys.update(held)
        frames(app, 1)                           # one frame: you move, and the game draws you
        return app.side_picture(you)

    seen = []
    for _ in range(30):                          # climb up
        seen.append(picture(pygame.K_UP))
    ok(you.on_wall, "still on the wall")
    ok(all(id(art) in climbing for art in seen), "climbing the wall uses the WALL_ pictures")
    ok(sprites.WALL_1 in seen and sprites.WALL_2 in seen and sprites.WALL_HOLD in seen,
       "climbing, his hands take turns (WALL_1, WALL_HOLD, WALL_2...)")
    changes = sum(a is not b for a, b in zip(seen, seen[1:]))
    ok(3 <= changes <= 20, "the pictures change as he climbs, but not every frame (%d changes)" % changes)

    still = []
    for _ in range(30):                          # let go of the keys: hold still
        still.append(picture())
    ok(you.on_wall and all(art is sprites.WALL_HOLD for art in still), "stopped on the wall, he holds still")

    seen = []
    for _ in range(20):                          # climb down: the hands move again
        seen.append(picture(pygame.K_DOWN))
    ok(sprites.WALL_1 in seen and sprites.WALL_2 in seen, "climbing down, his hands take turns too")

    you.on_wall, you.ladder_wait, you.buffer = 0, 0.3, 0.0   # let go, and slide down holding toward the wall
    you.y, you.vy = 6.0, 3.0                     # (low down, so he doesn't catch the top edge)
    tools = []                                   # (and count how often his tool gets drawn)
    monkeypatch.setattr(app, "draw_tool", lambda *args: tools.append(args))
    for _ in range(8):
        art = picture(pygame.K_RIGHT)
    ok(not tools, "his hands are busy on the wall: no tool poking into it")
    ok(you.wall_side == 1 and not you.on_wall and art is sprites.WALL_SLIDE, "sliding down the wall, he grips it")

    app.game.player.armor = 3                    # and with his armor on, it's the same pictures with armor
    ok(app.side_picture(you) == app.wall_view_armored["slide"], "armor: the sliding picture wears it too")


# ===========================================================================
# Ledge grab: jump at a wall that's a bit too high, and you catch its edge
# ===========================================================================

WALL_3_HIGH = ["##########",
               "#........#",
               "#........#",
               "#........#",
               "#........#",
               "#....#####",
               "#....#####",
               "..S..#####",
               "##########"]
WALL_4_HIGH = ["##########",
               "#........#",
               "#........#",
               "#........#",
               "#....#####",
               "#....#####",
               "#....#####",
               "..S..#####",
               "##########"]


def jump_at_the_wall(drawing, stop_when_hanging=False):
    """Run at the wall and jump. Returns the cave, and whether you caught the edge."""
    world, cave = cave_from(drawing)
    cave.you.x = 3.9
    run(cave, 5)
    run(cave, 1, right=True, jump=True, jump_pressed=True)
    caught = False
    for _ in range(90):
        cave.update(1 / 60, {"right": True, "jump": True})
        caught = caught or bool(cave.you.hanging)
        if caught and stop_when_hanging:
            break
    return cave, caught


def test_ledge_grab():
    cave, caught = jump_at_the_wall(WALL_3_HIGH)
    ok(caught, "jump at a wall 3 blocks high (too high to jump onto): you catch its edge")
    ok(cave.you.on_ground and feet(cave) == 5.0 and cave.you.x > 5,
       "...and pull yourself up on top (feet at %.2f)" % feet(cave))


def test_letting_go_of_a_ledge():
    cave, caught = jump_at_the_wall(WALL_3_HIGH, stop_when_hanging=True)
    run(cave, 2, down=True)
    run(cave, 60)
    ok(not cave.you.hanging and cave.you.on_ground and feet(cave) == 8.0, "DOWN lets go of the ledge")


def test_a_wall_4_blocks_high_is_too_high():
    cave, caught = jump_at_the_wall(WALL_4_HIGH)
    ok(not caught and feet(cave) == 8.0, "a wall 4 blocks high is too high to catch")


# ===========================================================================
# Ground pound: press DOWN in the air
# ===========================================================================

def test_ground_pound_smashes_cracked_rock():
    world, cave = cave_from(["##########",
                             "#........#",
                             "#........#",
                             "#........#",
                             "#........#",
                             "#..BB....#",
                             "#........#",
                             "..S......#",
                             "##########"])
    world.player.pickaxe = None
    cave.you.x, cave.you.y = 3.1, 1.0
    run(cave, 3)
    run(cave, 1, down=True)
    run(cave, 30, down=True)
    ok(cave.map[5][3] == "." and feet(cave) == 8.0, "a ground pound smashes cracked rock (no pickaxe needed) and keeps going down")


def test_ground_pound_on_a_monster():
    world, cave = cave_from(["##########",
                             "#........#",
                             "#........#",
                             "#........#",
                             "#........#",
                             "#........#",
                             "..S...z..#",
                             "##########"])
    zombie = cave.monsters[0]
    zombie.speed = 0
    health = zombie.info.health
    cave.you.x, cave.you.y = zombie.x, 1.0
    run(cave, 2)
    run(cave, 1, down=True)
    run(cave, 20)
    ok(health - zombie.info.health >= caves.POUND_DAMAGE - 1 and zombie.stunned > 0.3,
       "a ground pound on a monster: %d damage, and it's dizzy" % (health - zombie.info.health))


# ===========================================================================
# Crawling: hold DOWN to fit through a tunnel 1 block tall
# ===========================================================================

TUNNEL = ["############",
          "#..........#",
          "#..........#",
          "#..........#",
          "#...####...#",
          "#...####...#",
          "#...####...#",
          "..S.........",
          "############"]


def test_crawling_through_a_tunnel():
    world, cave = cave_from(TUNNEL)
    you = cave.you
    you.x = 2.1
    run(cave, 5)
    run(cave, 30, right=True)
    ok(you.x + you.w < 4.05, "standing up, you can't fit under the low wall")
    run(cave, 110, right=True, down=True)
    ok(you.x > 7.5 and you.crawling, "hold DOWN: you crawl through the 1-block tunnel")
    run(cave, 12, right=True)
    ok(not you.crawling and you.h == caves.PLAYER_H,
       "and stand up again when there's room (x %.1f, crawling %s)" % (you.x, you.crawling))


def test_no_standing_or_jumping_in_a_tunnel():
    world, cave = cave_from(TUNNEL)
    you = cave.you
    you.x, you.y, you.h, you.crawling = 5.0, 8 - caves.CRAWL_H, caves.CRAWL_H, True
    run(cave, 10)
    ok(you.crawling, "let go of DOWN in the tunnel: you stay crawling (no room to stand)")
    run(cave, 1, jump=True, jump_pressed=True)
    run(cave, 5)
    ok(you.on_ground and you.crawling, "...and you can't jump in there")


# ===========================================================================
# The Hero's walking pictures (sprites.py)
# ===========================================================================

def test_walking_legs_are_the_same_size():
    """Standing and stepping, his near leg (light steel "a") and far leg (dark steel "A") are the
    same size, and every walking picture has its legs in a different place."""
    import sprites
    for name in ("SIDE_STAND", "SIDE_STEP_1", "SIDE_STEP_2"):
        legs = getattr(sprites, name)[11:]
        near, far = sum(row.count("a") for row in legs), sum(row.count("A") for row in legs)
        ok(near == far, "%s: near leg %d pixels, far leg %d pixels: they should match" % (name, near, far))
    walk = [sprites.SIDE_STEP_1, sprites.SIDE_PASS_1, sprites.SIDE_STEP_2, sprites.SIDE_PASS_2]
    ok(len({tuple(art[11:]) for art in walk}) == 4, "the 4 walking pictures all have different legs")
