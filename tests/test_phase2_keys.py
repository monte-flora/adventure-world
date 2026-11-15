"""
Phase 2's keys (phase2/keys.py): R is for fighting, everywhere.

- a fight on the map: R attacks, X runs (A and R still do it in Classic)
- a cave, the castle, the throne room: R swings your sword, G digs, opens chests and pulls levers
  (Classic's R still does all of it)
- the tips, the panel and the H page name the right keys
"""

import pygame

import caves
import castle
import game
import phase2
import rules
import tutorial
from phase2 import hud, keys
from phase2_helpers import new_phase2_app, own_save_file  # noqa: F401  (own_save_file: a fixture)
from helpers import DT, cave_from, frames, hold_keys, new_app, ok, press, run, walk_into_a_mine
from test_caves import flat_with
from test_no_a_spam import PAUSE


# ===========================================================================
# Fights on the map
# ===========================================================================

def a_fight(app, monkeypatch):
    world = app.game
    monster = rules.Monster("Zombie", world.neighbors(world.player.pos)[0])
    monster.health = 999
    world.player.health = world.player.max_health = 999
    world.monsters.append(monster)
    world.start_battle(monster)
    frames(app, 1)
    ok(app.state == "battle", "a fight starts")
    turns = []
    monkeypatch.setattr(phase2, "battle_action", lambda game, action, time: turns.append(action))
    return turns


def take_turn(app, key):
    frames(app, PAUSE)
    press(app, key)


def test_phase2_fight_r_attacks_and_x_runs(monkeypatch):
    app = new_phase2_app()
    turns = a_fight(app, monkeypatch)
    for key in (pygame.K_a, pygame.K_r, pygame.K_1, pygame.K_x, pygame.K_2, pygame.K_e):
        take_turn(app, key)
    ok(turns == ["attack", "attack", "run", "run", "eat"], "Phase 2: A does nothing, R/1 attack, X/2 run, E eats: %s" % turns)


def test_classic_fight_keys_are_unchanged(monkeypatch):
    app = new_app()
    turns = a_fight(app, monkeypatch)
    for key in (pygame.K_a, pygame.K_r, pygame.K_x, pygame.K_1, pygame.K_2):
        take_turn(app, key)
    ok(turns == ["attack", "run", "attack", "run"], "Classic: A/1 attack, R/2 run, X does nothing: %s" % turns)


def test_the_fight_buttons_name_the_keys():
    p2 = phase2.battle_buttons(new_phase2_app().game, None)
    ok([(a, k) for a, k, _ in p2] == [("attack", "R"), ("run", "X"), ("eat", "E")], "Phase 2's buttons say R, X, E")
    classic = object()
    ok(phase2.battle_buttons(rules.Game("Hero", seed=1), classic) is classic, "Classic keeps its own buttons")


def test_the_fight_buttons_draw_in_both_games(monkeypatch):
    for app in (new_phase2_app(), new_app()):
        a_fight(app, monkeypatch)
        frames(app, PAUSE)
        ok([name for name, _ in app.battle_buttons] == ["attack", "run", "eat"], "three buttons: attack, run, eat")


# ===========================================================================
# Caves: R swings, G digs, opens and pulls (in Phase 2)
# ===========================================================================

def next_to_a_zombie(world=None):
    world, cave = cave_from(flat_with("..S.z........#"), world)
    zombie = cave.monsters[0]
    zombie.speed = 0
    cave.you.x = zombie.x - caves.PLAYER_W - 0.2
    cave.you.facing = 1
    run(cave, 5)
    return world, cave, zombie


def test_attack_swings_the_sword_at_a_monster():
    world, cave, zombie = next_to_a_zombie()
    health = zombie.info.health
    run(cave, 1, attack_pressed=True)
    ok(zombie.info.health < health and cave.you.tool == "sword", "R (attack) swings the sword and hits the Zombie")


def test_grab_never_swings():
    world, cave, zombie = next_to_a_zombie()
    health = zombie.info.health
    run(cave, 1, grab_pressed=True)
    ok(zombie.info.health == health and cave.you.swing == 0, "G next to a monster (nothing to dig or open) doesn't fight")


def test_g_digs_and_r_does_not():
    world, cave = cave_from(flat_with("..S..BB......#", "#....BB......#"))
    run(cave, 120, right=True)
    run(cave, 1, attack_pressed=True)
    ok(cave.map[12][5] == "B" and cave.you.tool == "sword", "R next to cracked rock swings the sword: no digging")
    run(cave, 30)
    run(cave, 1, grab_pressed=True)
    ok(cave.map[11][5] == "." and cave.map[12][5] == ".", "G digs the cracked rock")


def test_g_digs_the_floor_with_down():
    world, cave = cave_from(flat_with("..S..........#", extra={9: "#.....#BB#...#", 10: "#.....####...#"}))
    cave.you.x, cave.you.y = 7.1, 9 - caves.PLAYER_H
    run(cave, 20)
    run(cave, 1, grab_pressed=True, down=True)
    ok(cave.map[9][7] == ".", "DOWN + G digs the floor")


def test_g_opens_a_chest_and_r_fights_next_to_it():
    world, cave = cave_from(flat_with("..ST.z.......#"))
    zombie = cave.monsters[0]
    zombie.speed = 0
    zombie.x = cave.you.x + caves.PLAYER_W + 0.1        # right on top of the chest, next to you
    cave.you.facing = 1
    run(cave, 5)
    chest, health = cave.find("T"), zombie.info.health
    run(cave, 1, attack_pressed=True)
    ok(cave.tile(*chest) == "T" and zombie.info.health < health, "R by a chest and a monster: it hits the monster")
    run(cave, 30)
    run(cave, 1, grab_pressed=True)
    ok(cave.tile(*chest) != "T", "G opens the chest")


def test_classic_use_still_does_everything():
    world, cave, zombie = next_to_a_zombie()
    health = zombie.info.health
    run(cave, 1, use_pressed=True)
    ok(zombie.info.health < health, "Classic's R (use) still swings the sword when there's nothing to open")


def has_a_lever(drawing):
    return "L" in "".join(line for line in drawing.splitlines() if ":" not in line)


def test_castle_r_fights_and_g_pulls_levers():
    from test_nightfall_and_castle import at_the_castle
    world = at_the_castle(sunfang=True)
    world.reach_castle()
    levels = [n for n, (name, drawing, says) in enumerate(castle.CASTLE_LEVELS) if has_a_lever(drawing)]
    ok(levels, "a castle level has a lever")
    room = castle.Castle(world, world.castle, level=levels[0])
    world.cave = room
    r, c = lever = room.find("L")
    room.monsters = []
    room.you.x, room.you.y = c + 0.5 - room.you.w / 2, r + 1 - room.you.h
    room.you.vx = room.you.vy = 0.0
    room.update(DT, {"attack_pressed": True})
    ok(room.tile(*lever) == "L" and room.you.swing > 0, "R by a lever swings, it doesn't pull")
    room.you.swing = 0
    room.update(DT, {"grab_pressed": True})
    ok(room.tile(*lever) != "L", "G pulls the lever")


def test_throne_r_swings_sunfang():
    from test_shadow_king import in_the_throne_room, put_king, stand
    world, room = in_the_throne_room()
    stand(room, 8.0)
    put_king(room, 8.0 + room.you.w + 0.3, doing="stuck")
    room.you.facing = 1
    room.update(DT, {"attack_pressed": True})
    ok(room.king.health < room.king.max_health and room.you.tool == "sunfang", "R swings Sunfang and hits the Shadow King")
    world, room = in_the_throne_room()
    stand(room, 8.0)
    put_king(room, 8.0 + room.you.w + 0.3, doing="stuck")
    room.you.facing = 1
    room.update(DT, {"grab_pressed": True})
    ok(room.king.health == room.king.max_health, "G doesn't swing at him")


# ===========================================================================
# The real keys, in the window: R and G in a Phase 2 cave, R in a Classic one
# ===========================================================================

def record_cave(cave, monkeypatch):
    calls = []
    monkeypatch.setattr(cave, "attack", lambda: calls.append("attack"))
    monkeypatch.setattr(cave, "use", lambda down=False, swing=True: calls.append("use" if swing else "grab"))
    return calls


def tap(app, held, key):
    held.add(key)
    frames(app)
    held.discard(key)
    frames(app)


def test_phase2_cave_keys(monkeypatch):
    held = hold_keys(monkeypatch)
    app = new_phase2_app()
    cave = walk_into_a_mine(app)
    ok(app.state == "cave", "in a Phase 2 cave")
    calls = record_cave(cave, monkeypatch)
    tap(app, held, pygame.K_r)
    tap(app, held, pygame.K_g)
    held.add(pygame.K_r)
    frames(app, 5)                                   # holding R only swings once
    ok(calls == ["attack", "grab", "attack"], "Phase 2: R attacks, G digs/opens: %s" % calls)


def test_classic_cave_keys(monkeypatch):
    held = hold_keys(monkeypatch)
    app = new_app()
    cave = walk_into_a_mine(app)
    calls = record_cave(cave, monkeypatch)
    tap(app, held, pygame.K_r)
    tap(app, held, pygame.K_g)
    ok(calls == ["use"], "Classic: R digs, opens and fights; G does nothing: %s" % calls)


# ===========================================================================
# The words: tips, the panel, the H page, the guide NPC
# ===========================================================================

def test_tips_name_phase2_keys():
    p2, classic = new_phase2_app().game, rules.Game("Hero", seed=1)
    ok("press R to attack" in phase2.tip_words(p2, "monster", tutorial.TIPS["monster"]), "Phase 2's fight tip says R")
    for name in ("chest", "dig", "diamond"):
        ok("press G" in phase2.tip_words(p2, name, tutorial.TIPS[name]), "Phase 2's %s tip says G" % name)
        ok(phase2.tip_words(classic, name, tutorial.TIPS[name]) == tutorial.TIPS[name], "Classic's %s tip is unchanged" % name)
    ok(phase2.tip_words(classic, "monster", tutorial.TIPS["monster"]) == tutorial.TIPS["monster"], "Classic says A")


def test_the_lever_message():
    world, cave = cave_from(flat_with("..S..........#"), new_phase2_app().game)
    cave.tips_shown = set()
    world.tips_seen = set()
    cave.tip("lever")
    ok(world.messages[-1][0] == keys.CAVE_TIPS["lever"] and "Press G" in world.messages[-1][0],
       "Phase 2's lever message says G")
    classic, cave = cave_from(flat_with("..S..........#"))
    classic.tips_seen = set()
    cave.tip("lever")
    ok(classic.messages[-1][0] == caves.TIPS["lever"], "Classic's lever message still says R")


def test_the_panel_and_h_page_name_r_and_g():
    app = new_phase2_app()
    walk_into_a_mine(app)
    lines = hud.here(app.game, {"tiles": game.TILE_HINTS, "cave": game.CAVE_HINTS, "castle": game.CASTLE_HINTS,
                                "throne": game.THRONE_HINTS})
    flat = [part for line in lines for part in line]
    ok("R" in flat and "fight" in flat and "G" in flat and "Down + G" in flat, "the cave panel: R fights, G digs")
    pages = dict(hud.all_keys())
    ok(("R", "attack (in the gold = PERFECT)") in pages["In a fight"] and ("X", "run away") in pages["In a fight"],
       "the H page has a fight section: R attacks, X runs")
    ok(("R", "swing your sword") in pages["In a cave"] and any(k == "G" for k, _ in pages["In a cave"]),
       "the H page: R swings in a cave, G digs and opens")
    ok(game.CAVE_HINTS[2] == ("R", "dig, open chests, fight"), "Classic's cave panel still says R digs and fights")


def test_the_panel_draws_in_a_phase2_cave_castle_and_throne():
    for table in keys.HINTS.values():
        ok(all(len(line) in (2, 4) for line in table), "every hint line has one or two keys")
    app = new_phase2_app()
    walk_into_a_mine(app)
    frames(app, 3)                                   # the panel draws with Phase 2's cave hints
    ok(app.state == "cave", "still in the cave after drawing the panel")
