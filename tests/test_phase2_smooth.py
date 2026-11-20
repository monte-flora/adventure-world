"""
SMOOTH WALKING AND ROAMING MONSTERS ON THE PHASE 2 MAP (phase2/smooth.py, phase2/monsters.py):
hold a move key and the Hero walks a little every frame (not a square at a time), rock and water stop
him, a step onto a square still does what it did (a house, a Mine, ice, a turn passes), monsters roam
all the time and one that touches you starts the fight. Classic still plays a square at a time.
"""

import math

import pygame

import game
import phase2
import rules
from helpers import DT, frames, hold_keys, new_app, ok, press, steps, tiles
from phase2 import monsters, save, smooth
from phase2_helpers import STEP, hold, own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)
from test_phase2_monsters import a_world, alone_with, field_spot, open_spot


def on_a_field(world):
    """Put the Hero in the middle of an open field (9 squares of grass each way). Returns his square."""
    world.player.pos = field_spot(world)
    return world.player.pos


def said(world, words):
    return sum(words in text for text, _ in world.messages)


# ----- the Hero walks smoothly ------------------------------------------------------------------

def test_hold_a_key_and_the_hero_walks_a_little_every_frame(monkeypatch):
    app = new_phase2_app()
    world = app.game
    r, c = on_a_field(world)
    frames(app, 2)
    press(app, pygame.K_RIGHT)
    ok(world.player.pos == (r, c) and app.map_facing == "right", "a key press turns him: it isn't a whole step")
    held = hold_keys(monkeypatch)
    held.add(pygame.K_RIGHT)
    xs = [smooth.where(world)[0]]
    for _ in range(STEP):
        frames(app)
        xs.append(smooth.where(world)[0])
    ok(all(abs(b - a - smooth.HERO_SPEED * DT) < 1e-6 for a, b in zip(xs, xs[1:])), "a little every frame")
    ok(world.player.pos == (r, c + 1), "and in %d frames he's on the next square" % STEP)
    held.clear()
    frames(app, 30)
    ok(smooth.where(world)[0] == xs[-1], "let go and he stops")
    ok(abs(app.player_px[0] - (xs[-1] - 0.5) * game.TILE) < 1, "and he's drawn right where he is")
    hold(app, monkeypatch, pygame.K_UP, 5)
    ok(world.player.pos == (r, c + 1) and smooth.where(world)[1] % 1 != 0.5 and app.map_facing == "up",
       "he can stop anywhere on a square, not only in the middle")


def test_two_keys_walk_diagonally_at_the_same_speed(monkeypatch):
    app = new_phase2_app()
    world = app.game
    on_a_field(world)
    frames(app, 2)
    start = list(smooth.where(world))
    held = hold_keys(monkeypatch)
    held.update({pygame.K_d, pygame.K_s})
    frames(app, STEP)
    x, y = smooth.where(world)
    ok(x > start[0] and y > start[1] and abs(math.dist((x, y), start) - 1) < 0.01, "right and down, one square far")


def test_every_square_walked_is_a_turn_and_standing_still_is_not(monkeypatch):
    app = new_phase2_app()
    world = app.game
    on_a_field(world)
    frames(app, 2)
    turn = world.turn
    hold(app, monkeypatch, pygame.K_LEFT, 3 * STEP)
    ok(world.turn == turn + 3, "3 squares walked: 3 turns")
    frames(app, 120)
    ok(world.turn == turn + 3, "standing still: no turns pass")
    world.turn = monsters.DAY_TURNS - 1
    hold(app, monkeypatch, pygame.K_RIGHT)
    ok(monsters.is_night(world), "walk long enough and night falls, as before")
    press(app, pygame.K_z)
    ok(world.turn == monsters.DAY_TURNS + 1, "and Z still waits a turn")


def test_a_robot_still_walks_a_whole_square():
    world = a_world()
    r, c = on_a_field(world)
    world.monsters = []
    ok(world.do("right") and world.player.pos == (r, c + 1), "game.do walks one square")
    ok(smooth.where(world) == smooth.middle((r, c + 1)), "to the middle of it")


# ----- things in the way ------------------------------------------------------------------------------

def test_rock_stops_him_and_says_so_once(monkeypatch):
    app = new_phase2_app()
    world = app.game
    r, c = on_a_field(world)
    world.map[r][c + 2] = "X"
    frames(app, 2)
    hold(app, monkeypatch, pygame.K_RIGHT, 60)
    x = smooth.where(world)[0]
    ok(world.player.pos == (r, c + 1) and c + 1.5 < x <= c + 2 - smooth.HALF, "he stops at the rock, not in it")
    ok(said(world, "rock is in the way") == 1, "and the game says what's in the way, once")
    hold(app, monkeypatch, pygame.K_RIGHT, 10)
    ok(said(world, "rock is in the way") == 2 and smooth.where(world)[0] == x, "push again: it says so again")


def test_water_stops_him_until_he_has_a_boat(monkeypatch):
    app = new_phase2_app()
    world = app.game
    r, c = on_a_field(world)
    world.map[r + 1][c] = "W"
    frames(app, 2)
    hold(app, monkeypatch, pygame.K_DOWN, 30)
    ok(world.player.pos == (r, c) and said(world, "can't swim") == 1, "no boat: the water stops him")
    world.player.has_boat = True
    hold(app, monkeypatch, pygame.K_DOWN, 30)
    ok(world.player.pos == (r + 1, c) and world.here == "W", "with a boat he rows out")


def test_he_slides_along_a_wall_and_round_a_corner(monkeypatch):
    app = new_phase2_app()
    world = app.game
    r, c = on_a_field(world)
    for cc in range(c - 1, c + 3):
        world.map[r - 1][cc] = "X"                  # a wall of rock above him, with a gap at c + 3
    frames(app, 2)
    held = hold_keys(monkeypatch)
    held.update({pygame.K_UP, pygame.K_RIGHT})
    frames(app, STEP)
    x, y = smooth.where(world)
    ok(x > c + 1 and r + smooth.HALF <= y < r + 0.5, "up and right along a wall: he slides right")
    ok(said(world, "rock is in the way") == 0, "(sliding isn't a bump)")
    held.clear()
    world.hero_xy = [c + 2.95, r + 0.5]             # right under the wall's corner, a bit short of the gap
    hold(app, monkeypatch, pygame.K_UP, STEP)
    ok(world.player.pos == (r - 1, c + 3), "up at the corner: he steps round it and through the gap")


def test_a_slow_frame_cannot_jump_through_a_rock():
    world = a_world()
    r, c = on_a_field(world)
    world.monsters = []
    world.map[r][c + 2] = "X"
    world.walk(1, 0, 0.9)                           # (4.5 squares' worth of walking in one go)
    ok(world.player.pos == (r, c + 1) and smooth.where(world)[0] <= c + 2 - smooth.HALF, "he still stops at it")


def test_the_edge_of_the_world_stops_him():
    world = a_world()
    world.monsters = []
    world.player.pos = next(spot for spot in sorted(world.reach(world.start)) if spot[1] == 0)
    world.walk(-1, 0, 0.5)
    x, y = smooth.where(world)
    ok(smooth.HALF <= x < 0.5 and world.player.pos[1] == 0, "he can't walk off the map")
    world.walk(-1, 0, 0.1)
    ok(said(world, "edge of the world") == 1, "and the game says so")


# ----- stepping onto a square still does what it did -----------------------------------------------------

def test_walking_into_a_house_is_safe_and_saves(monkeypatch):
    app = new_phase2_app()
    world = app.game
    r, c = on_a_field(world)
    world.map[r][c + 1] = "H"
    frames(app, 2)
    saves = []
    monkeypatch.setattr(world, "autosave", lambda: saves.append(world.player.pos))
    hold(app, monkeypatch, pygame.K_RIGHT)
    ok(world.here == "H" and said(world, "safe at home") == 1, "he walks in: safe at home")
    ok(saves == [(r, c + 1)], "and the game saves")


def test_walk_onto_a_mine_and_space_climbs_down(monkeypatch):
    app = new_phase2_app()
    world = app.game
    mine = min(tiles(world, "M"), key=lambda spot: (steps(spot, world.start), spot))
    way, (dr, dc) = next((way, d) for way, d in rules.DIRECTIONS.items()
                         if smooth.passable(world, (mine[0] - d[0], mine[1] - d[1])))
    world.player.pos = (mine[0] - dr, mine[1] - dc)
    frames(app, 2)
    hold(app, monkeypatch, {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "up": pygame.K_UP,
                            "down": pygame.K_DOWN}[way])
    ok(world.player.pos == mine, "he walks onto the Mine")
    press(app, pygame.K_SPACE)
    frames(app, 30)
    ok(world.cave is not None and app.state == "cave", "and SPACE climbs down into its cave")


def test_ice_still_slides_him_all_the_way(monkeypatch):
    app = new_phase2_app()
    world = app.game
    r, c = on_a_field(world)
    for cc in range(c + 1, c + 4):
        world.map[r][cc] = "I"
    frames(app, 2)
    hold(app, monkeypatch, pygame.K_RIGHT)
    ok(world.player.pos == (r, c + 4) and smooth.where(world) == smooth.middle((r, c + 4)),
       "one step onto the ice and he slides to the far side")


def test_he_walks_smoothly_in_nightfall_hollow_too(monkeypatch):
    app = new_phase2_app()
    world = app.game
    world.go_to_nightfall()
    world.story.clear()
    world.monsters = []
    frames(app, 30)
    r, c = world.player.pos
    way, (dr, dc) = next((way, d) for way, d in rules.DIRECTIONS.items()
                         if world.tile((r + d[0], c + d[1])) in "GFR")
    turn = world.turn
    hold(app, monkeypatch, {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "up": pygame.K_UP,
                            "down": pygame.K_DOWN}[way], STEP // 2)
    ok(world.player.pos == (r, c) and smooth.where(world) != smooth.middle((r, c)), "half a square...")
    hold(app, monkeypatch, {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "up": pygame.K_UP,
                            "down": pygame.K_DOWN}[way], STEP // 2)
    ok(world.player.pos == (r + dr, c + dc) and world.turn == turn + 1, "...and the other half: a step, a turn")


# ----- monsters roam freely ---------------------------------------------------------------------------

def test_monsters_roam_while_you_stand_still_and_not_square_by_square():
    app = new_phase2_app()
    world = app.game
    home = on_a_field(world)
    den = open_spot(world, home, 8)                 # (too far away for it to chase you)
    m = alone_with(world, "Spider", den)
    turn, spots = world.turn, [list(monsters.where(m))]
    for _ in range(600):
        frames(app)
        spots.append(list(m.xy))
    hops = [math.dist(a, b) for a, b in zip(spots, spots[1:])]
    top = monsters.ROAM_SPEED * m.move_chance * DT
    ok(max(hops) <= top + 1e-6 and sum(hops) > 2, "it walks about, a little every frame")
    ok(any(xy != smooth.middle(smooth.square(xy)) for xy in spots), "anywhere on a square, not only its middle")
    ok(0 in hops, "and stands still now and then")
    ok(all(monsters.steps(smooth.square(xy), den) <= monsters.PATROL_RADIUS for xy in spots), "near its home")
    ok(m.pos == smooth.square(m.xy), "its square is the one its middle is in")
    ok(world.turn == turn and world.player.pos == home, "and all that while you stood still: no turn passed")


def test_a_monster_that_touches_you_starts_the_fight():
    app = new_phase2_app()
    world = app.game
    home = on_a_field(world)
    m = alone_with(world, "Frost Wolf", open_spot(world, home, 3))
    waited = 0
    while app.state != "battle" and waited < 120:
        frames(app)
        waited += 1
    ok(app.state == "battle" and world.battle.monster is m, "it runs at you and the fight starts")
    ok(waited * DT < 3 / monsters.RUN_SPEED + 0.2 and world.player.pos == home, "in under a second: you never moved")
    ok(math.dist(m.xy, smooth.where(world)) < monsters.TOUCH + 0.1, "it came right up to you")


def test_walk_into_one_from_behind_for_a_first_strike_but_not_from_the_front():
    for facing, sneaky in (("right", True), ("left", False), ("up", False)):
        world = a_world()
        r, c = on_a_field(world)
        m = alone_with(world, "Zombie", (r, c + 2), facing=facing)
        m.health = m.max_health = 50
        for _ in range(40):
            if world.battle:
                break
            world.walk(1, 0, DT)                    # (only you move here: it doesn't turn round)
        ok(world.battle and world.battle.monster is m, "you walked into it: a fight")
        ok(smooth.where(world)[0] < c + 2, "as soon as you touch it")
        ok((m.health < 50) == sneaky, "it looks %s: %s" % (facing, "a first strike!" if sneaky else "no free hit"))


def test_nothing_touches_you_on_the_path_and_a_sea_serpent_only_in_your_boat():
    world = a_world()
    r, c = on_a_field(world)
    m = alone_with(world, "Zombie", (r, c + 1), state="chase")
    m.xy = [c + 1.1, r + 0.5]
    world.map[r][c] = "R"
    monsters.pass_time(world, 0.5)
    ok(not world.battle and m.state != "chase", "on the path: it can't touch you, and gives up")
    world.map[r][c], world.map[r][c + 1] = "G", "W"
    m = alone_with(world, "Sea Serpent", (r, c + 1), state="chase")
    m.xy = [c + 1.1, r + 0.5]
    ok(monsters.touch(world) is None, "on the shore: the Sea Serpent can't get you")
    world.map[r][c] = "W"
    ok(monsters.touch(world) is m and world.battle, "in your boat it can")


def test_it_leaves_you_alone_for_a_bit_after_you_run():
    world = a_world()
    r, c = on_a_field(world)
    m = alone_with(world, "Zombie", (r, c + 1))
    world.start_battle(m)
    world.rng.random = lambda: 0.9                  # no swipe as you run
    world.battle_action("run")
    world.close_battle()
    monsters.pass_time(world, monsters.CALM_SECONDS - 0.5)
    ok(not world.battle and m.state != "chase", "it lets you go...")
    monsters.pass_time(world, 3.0)
    ok(world.battle, "...but not for long, if you stay")


def test_monsters_keep_off_each_other():
    world = a_world()
    r, c = on_a_field(world)
    world.player.pos = (r, c - 3)
    world.monsters = [monsters.make_monster("Frost Wolf", (r + dr, c + 1), "Home Meadow") for dr in (-1, 0, 1)]
    for _ in range(12):
        monsters.pass_time(world, 0.05)
        if world.battle:
            break
        gaps = [math.dist(a.xy, b.xy) for a in world.monsters for b in world.monsters if a is not b]
        ok(min(gaps) >= monsters.CROWD - 1e-6, "three chase you, and none walks into another")


def test_a_skeleton_keeps_its_distance_and_shoots_by_the_clock():
    world = a_world()
    r, c = on_a_field(world)
    m = alone_with(world, "Skeleton", (r, c + 3))
    world.player.health = world.player.max_health = 99
    world.rng.random = lambda: 0.0                  # every shot hits
    monsters.pass_time(world, 3.0)
    ok(not world.battle and math.dist(m.xy, smooth.where(world)) >= monsters.ARCHER_GAP - 0.01,
       "it comes close, but not onto you")
    ok(99 - world.player.health == 3, "and shoots about once a second (not once a turn)")


def test_save_and_load_keep_where_everyone_is():
    world = a_world()
    r, c = on_a_field(world)
    m = alone_with(world, "Spider", (r, c + 3))
    world.live, world.hero_xy, m.xy = True, [c + 0.25, r + 0.75], [c + 3.5, r + 0.2]
    back = save.data_to_game(save.game_to_data(world))
    ok(smooth.where(back) == [c + 0.25, r + 0.75] and monsters.where(back.monsters[0]) == [c + 3.5, r + 0.2],
       "the Hero and the monsters come back right where they stood")
    ok(back.live is False and back.do("wait"), "and the game goes on")


# ----- Classic is unchanged ---------------------------------------------------------------------------

def test_classic_still_walks_a_square_for_every_key_press(monkeypatch):
    app = new_app(monsters=True)
    world = app.game
    ok(not phase2.is_phase2(world) and phase2.map_spot(app) is None and phase2.live_map(app, DT, {"right"}) is False,
       "a classic game: no smooth walking")
    world.monsters = world.monsters[:6]
    r, c = spot = world.player.pos
    key, (dr, dc) = next((key, rules.DIRECTIONS[way]) for key, way in game.MOVE_KEYS.items()
                         if world.tile((r + rules.DIRECTIONS[way][0], c + rules.DIRECTIONS[way][1])) in "GFR")
    turn, were = world.turn, [m.pos for m in world.monsters]
    held = hold_keys(monkeypatch)
    held.add(key)
    frames(app, 60)
    ok(world.player.pos == spot and world.turn == turn, "a held key alone does nothing: Classic walks on key presses")
    ok([m.pos for m in world.monsters] == were, "and nothing moves until you do")
    held.clear()
    press(app, key)
    ok(world.player.pos == (r + dr, c + dc) and world.turn == turn + 1, "one key press: one whole square, one turn")
    frames(app, 30)
    ok(app.player_px == list(game.tile_px(world.player.pos)), "drawn on his square")
    for _ in range(10):
        world.do("wait")
        if world.battle:
            break
    ok(all(isinstance(n, int) for m in world.monsters for n in m.pos) and [m.pos for m in world.monsters] != were,
       "the monsters hop a square at a time, when you take a turn")
    ok(not any(hasattr(m, "xy") for m in world.monsters) and "hero_xy" not in vars(world), "nothing smooth in Classic")
