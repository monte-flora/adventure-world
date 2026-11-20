"""
PHASE 2 MONSTERS (phase2/monsters.py, phase2/fight.py): you can see every monster on the map, each land
has its own, they patrol, chase and give up, never come into houses or onto the path, a sneak attack from
behind gets a first strike, weak ones run from you, and Attack in a fight is a timing strike.

They roam in real time: monsters.pass_time(world, seconds). (tests/test_phase2_smooth.py has more.)
"""

import math

import pygame

import game
import phase2
import rules
from helpers import DT, frames, new_app, ok, press
from phase2 import Phase2Game, fight, monsters, save, smooth
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)

PAUSE = int(game.BATTLE_PAUSE / DT) + 1


def a_world(seed=1):
    world = Phase2Game("Hero", seed=seed)
    world.story.clear()
    return world


def open_spot(world, near, how_far):
    """A grass square `how_far` steps from `near`, with grass all around it (room to walk)."""
    for spot in sorted(world.reach(near)):
        if monsters.steps(spot, near) == how_far and world.tile(spot) == "G" \
                and not monsters.is_safe(world, spot) and not world.monster_at(spot):
            return spot
    raise AssertionError("no open square")


def alone_with(world, kind, pos, **fields):
    m = monsters.make_monster(kind, pos, world.land_name(pos))
    for name, value in fields.items():
        setattr(m, name, value)
    world.monsters = [m]
    return m


def field_spot(world):
    """A square away from home with open grass all around it (painted, so it works on any map)."""
    for spot in sorted(world.reach(world.start)):
        r, c = spot
        if monsters.steps(spot, world.start) > 10 and 4 <= r < world.rows - 4 and 4 <= c < world.cols - 4 \
                and world.land_name(spot):
            for dr in range(-4, 5):
                for dc in range(-4, 5):
                    world.map[r + dr][c + dc] = "G"
            world.monsters = [m for m in world.monsters if monsters.steps(m.pos, spot) > 8]
            return spot
    raise AssertionError("no open field")


# ----- visible, and placed by land ---------------------------------------------------------

def test_every_land_has_its_own_monsters_and_you_can_see_them_all():
    world = a_world()
    ok(len(world.monsters) > 20 and all(world.is_visible(m.pos) for m in world.monsters),
       "lots of monsters, and every one is on a square you can see (no fog, no surprises)")
    by_land = {}
    for m in world.monsters:
        ok(world.land_name(m.pos) == m.land, "%s starts in its own land" % m.kind)
        by_land.setdefault(m.land, []).append(m)
    meadow = by_land.get("Home Meadow", [])
    ok(0 < len(meadow) <= 5 and all(m.level <= 1 for m in meadow), "Home Meadow: a few weak ones")
    ok({m.kind for m in by_land["Sunscorch Desert"]} <= {"Scorpion", "Ember Skull"}
       and any(m.kind == "Scorpion" for m in by_land["Sunscorch Desert"]), "Scorpions in the desert")
    ok(any(m.kind == "Bog Lurker" for m in by_land["Murk Swamp"]), "Bog Lurkers in the swamp")
    ok(any(m.kind == "Frost Wolf" for m in by_land["Frost Peaks"]), "Frost Wolves up in the snow")
    tough = sum(m.level for m in by_land["Sunscorch Desert"]) / len(by_land["Sunscorch Desert"])
    ok(tough > 2 * sum(m.level for m in meadow) / len(meadow), "the desert's monsters are much tougher")
    ok(all(monsters.steps(m.pos, world.start) >= monsters.HOME_SAFE for m in world.monsters), "none right by home")
    ok(all(not monsters.is_safe(world, m.pos) for m in world.monsters), "none on a house or the path")
    ok(all(world.tile(m.pos) == "W" for m in world.monsters if m.special == "drowns"), "Sea Serpents swim")


def test_new_kinds_have_pictures():
    import sprites
    for kind in monsters.NEW_KINDS:
        ok(kind in sprites.MONSTER_ART, "%s has a picture" % kind)
        m = monsters.make_monster(kind, (0, 0))
        ok(m.health == m.max_health > 0 and m.xp > 0, "%s can be fought" % kind)


# ----- patrol, chase, give up ----------------------------------------------------------------

def test_a_monster_patrols_near_its_home_when_you_are_far_away():
    world = a_world()
    home = field_spot(world)
    m = alone_with(world, "Spider", home)
    world.player.pos = open_spot(world, home, 8)     # near enough to see it, too far for it to chase you
    been = set()
    for _ in range(60):
        monsters.pass_time(world, 0.5)
        been.add(m.pos)
        ok(monsters.steps(m.pos, home) <= monsters.PATROL_RADIUS, "it stays near its home spot")
    ok(m.state == "patrol" and len(been) > 3, "patrolling: it wanders about")


def test_it_chases_you_when_you_come_close_then_gives_up_and_goes_home():
    world = a_world()
    home = field_spot(world)
    m = alone_with(world, "Frost Wolf", home, move_chance=1.0)
    world.player.pos = open_spot(world, home, 3)
    gap = math.dist(monsters.where(m), smooth.where(world))
    monsters.pass_time(world, 0.2)
    ok(m.state == "chase", "you're 3 squares away: it chases you")
    closer = gap - math.dist(m.xy, smooth.where(world))
    ok(abs(closer - monsters.RUN_SPEED * 0.2) < 0.01, "and runs straight at you (not a square at a time)")
    world.player.pos = world.start                   # you run home (far away, and in a house)
    monsters.pass_time(world, 0.2)
    ok(m.state != "chase", "it gives up")
    m.pos, m.state = open_spot(world, home, 4), "home"     # (it had wandered off a bit)
    monsters.pass_time(world, 4.0)
    ok(m.state == "patrol" and monsters.steps(m.pos, home) <= monsters.PATROL_RADIUS, "and walks back home")


def test_a_chasing_monster_that_reaches_you_starts_a_fight():
    world = a_world()
    home = field_spot(world)
    m = alone_with(world, "Frost Wolf", home, move_chance=1.0)
    world.player.pos = open_spot(world, home, 1)
    world.do("wait")
    ok(world.battle and world.battle.monster is m, "it steps onto you: a fight!")
    ok(isinstance(world.battle.bar, fight.StrikeBar), "a Phase 2 fight, with the timing bar")


def test_monsters_never_go_into_houses_villages_or_onto_the_path():
    world = a_world()
    path = [s for s in sorted(world.reach(world.start)) if world.tile(s) == "R"]
    for spot in path[:40] + [world.start]:
        for dr, dc in rules.DIRECTIONS.values():
            nxt = (spot[0] + dr, spot[1] + dc)
            if world.in_bounds(nxt) and world.tile(nxt) in "GF" and not monsters.is_safe(world, nxt):
                m = alone_with(world, "Frost Wolf", nxt, move_chance=1.0)
                world.player.pos = spot
                for _ in range(10):
                    monsters.pass_time(world, 0.2)
                    ok(not monsters.is_safe(world, m.pos), "it never steps on the path or a house")
                ok(m.state != "chase", "and it doesn't even chase you there")
                break
    world.safe_squares = {open_spot(world, field_spot(world), 1)}   # a village square (stage 2a/2b)
    square = next(iter(world.safe_squares))
    ok(monsters.is_safe(world, square), "village squares are safe too")


def test_village_squares_are_read_from_the_atlas():
    world = a_world()
    world.atlas.villages = {"Oakvale": {"squares": [(1, 2), (1, 3)]}, "Dune": (5, 5, 6, 6)}
    squares = monsters.village_squares(world)
    ok({(1, 2), (1, 3), (5, 5), (6, 6)} <= squares, "a village's squares, or its box")
    del world.atlas.villages


# ----- first strike, and weak ones run ---------------------------------------------------------

def test_walk_into_a_monster_from_behind_for_a_first_strike():
    world = a_world()
    home = field_spot(world)
    world.player.pos = home
    there = (home[0], home[1] + 1)
    m = alone_with(world, "Zombie", there, facing="right", move_chance=0.0)
    m.health = m.max_health = 50
    world.do("right")
    ok(world.battle and world.battle.monster is m, "you walked into it: a fight")
    ok(m.health < 50 and any("FIRST STRIKE" in t for t, _ in world.battle.lines), "from behind: a free hit first")


def test_walk_into_one_from_the_front_no_first_strike():
    world = a_world()
    home = field_spot(world)
    world.player.pos = home
    m = alone_with(world, "Zombie", (home[0], home[1] + 1), facing="left", move_chance=0.0)
    world.do("right")
    ok(world.battle and m.health == m.max_health, "face to face: a normal fight, no free hit")


def test_a_first_strike_can_win_the_fight():
    world = a_world()
    home = field_spot(world)
    world.player.pos = home
    m = alone_with(world, "Slime", (home[0] + 1, home[1]), facing="down", move_chance=0.0)
    m.health = 1
    world.do("down")
    ok(world.battle.result == "won" and m not in world.monsters, "one sneaky hit and it's gone")


def test_weak_monsters_run_from_a_strong_hero():
    world = a_world()
    home = field_spot(world)
    m = alone_with(world, "Slime", home, move_chance=1.0)
    world.player.pos = open_spot(world, home, 2)
    world.player.level = 1 + monsters.FLEE_LEVELS
    monsters.pass_time(world, 0.4)
    ok(m.state == "flee" and math.dist(m.xy, smooth.where(world)) > 3, "it runs away from you")
    world.player.level = 1
    m.pos, m.state = home, "patrol"
    monsters.pass_time(world, 0.2)
    ok(m.state == "chase", "a level 1 Hero: it comes after you")


def test_running_away_makes_it_leave_you_alone_for_a_bit():
    world = a_world()
    home = field_spot(world)
    m = alone_with(world, "Zombie", home, move_chance=0.0)
    world.start_battle(m)
    world.rng.random = lambda: 0.9                  # no swipe as you run
    world.battle_action("run")
    ok(world.battle.result == "fled" and m.calm > 0 and m.state == "home", "it lets you go")


# ----- night, and coming back -------------------------------------------------------------------

def test_more_monsters_come_out_at_night_and_go_at_dawn():
    world = a_world()
    day = len(world.monsters)
    world.turn = monsters.DAY_TURNS - 1
    world.do("wait")
    ok(monsters.is_night(world) and monsters.darkness(world) > 0, "night falls")
    ok(len(world.monsters) > day, "more monsters")
    world.turn = monsters.DAY_TURNS + monsters.NIGHT_TURNS - 1
    for m in world.monsters:
        m.state = "patrol"
    world.do("wait")
    ok(not monsters.is_night(world), "the sun comes up")
    ok(not any(m.night for m in world.monsters), "the night ones go away")


def test_a_beaten_monster_comes_back_later_away_from_you():
    world = a_world()
    m = next(m for m in world.monsters if m.land == "Home Meadow")
    count = len(world.monsters)
    world.start_battle(m)
    m.health = 1
    world.battle_action("attack")
    ok(len(world.monsters) == count - 1 and world.respawns, "it's gone, for now")
    world.turn += monsters.RESPAWN_TURNS
    world.close_battle()
    world.do("wait")
    back = [n for n in world.monsters if n.land == "Home Meadow" and n.kind == m.kind]
    ok(len(world.monsters) == count, "it came back")
    ok(all(monsters.steps(n.pos, world.player.pos) >= monsters.RESPAWN_AWAY for n in back[-1:]), "far from you")


def test_save_and_load_keeps_the_monsters():
    world = a_world()
    world.monsters[0].state, world.monsters[0].facing = "chase", "up"
    world.respawns.append(("Home Meadow", "Slime", 99))
    back = save.data_to_game(save.game_to_data(world))
    ok([(m.kind, m.pos, m.home, m.facing, m.state) for m in back.monsters]
       == [(m.kind, m.pos, m.home, m.facing, m.state) for m in world.monsters], "every monster, home and all")
    ok(back.respawns == world.respawns, "and the ones waiting to come back")
    back.do("wait")
    ok(back.turn == world.turn + 1, "and the game goes on")


def test_an_old_save_without_monster_homes_still_works():
    world = a_world()
    world.monsters = [rules.Monster("Spider", field_spot(world))]
    for name in ("respawns", "safe_squares", "monster_plan", "was_night"):
        delattr(world, name)
    for _ in range(5):
        world.do("wait")
    ok(hasattr(world.monsters[0], "home"), "the old monster gets a home spot")


def test_nightfall_keeps_its_classic_shadow_monsters():
    world = a_world()
    world.go_to_nightfall()
    ok(world.monsters and all(m.shadow for m in world.monsters), "shadow monsters in Nightfall Hollow")
    world.turn = rules.MOONRISE_EVERY - 1
    world.do("wait")
    ok(world.moon > 0, "and the moon still rises")


# ----- the timing strike --------------------------------------------------------------------------

def test_the_timing_bar_grades_where_the_marker_is():
    import random
    bar = fight.StrikeBar(random.Random(1))
    ok(bar.grade(bar.gold_x + bar.gold_w / 2) == "perfect", "gold: Perfect")
    ok(bar.grade(bar.zone_x + 0.01) == "good", "green: Good")
    ok(bar.grade(0.0 if bar.zone_x > 0.05 else 1.0) == "miss", "anywhere else: Miss")
    ok(bar.pos_at(0) == 0 and abs(bar.pos_at(1 / fight.STRIKE_SPEED) - 1) < 1e-9
       and bar.pos_at(2 / fight.STRIKE_SPEED) < 1e-9, "the marker sweeps there and back")


def test_perfect_hits_harder_than_good_and_a_miss_is_weak():
    hits = {}
    for grade in ("perfect", "good", "miss"):
        world = a_world()
        m = alone_with(world, "Zombie", field_spot(world))
        m.health = m.max_health = 999
        world.start_battle(m)
        world.rng.randint = lambda low, high: 4
        hits[grade] = fight.strike_damage(world, m, grade)
    ok(hits["perfect"] > hits["good"] > hits["miss"] == fight.WEAK_HIT, "Perfect > Good > Miss (%s)" % hits)


def test_pressing_r_in_a_fight_uses_the_timing_bar():
    app = new_phase2_app()
    world = app.game
    m = alone_with(world, "Zombie", field_spot(world), move_chance=0.0)
    m.health = m.max_health = 999
    world.player.health = world.player.max_health = 999
    world.player.pos = (m.pos[0], m.pos[1] - 1)
    world.start_battle(m)
    frames(app, PAUSE)
    bar = world.battle.bar
    bar.start, bar.zone_x, bar.gold_x = app.time, 0.0, 0.0     # the marker is at the left, in gold
    bar.new_zone = lambda: None
    press(app, pygame.K_r)
    ok(bar.last == "perfect" and any("PERFECT" in t for t, _ in world.battle.lines), "R in the gold: Perfect!")
    press(app, pygame.K_r)
    ok(len([t for t, _ in world.battle.lines if "PERFECT" in t]) == 1, "the no-spamming pause still works")
    frames(app, PAUSE)
    bar.zone_x = bar.gold_x = 0.7
    bar.start = app.time
    press(app, pygame.K_r)
    ok(bar.last == "miss" and any("weak hit" in t for t, _ in world.battle.lines), "R off the zone: a weak hit")
    frames(app, 5)                                   # and it draws


def test_classic_fights_are_unchanged():
    app = new_app()
    world = app.game
    ok(not phase2.is_phase2(world), "a classic game")
    m = rules.Monster("Zombie", world.neighbors(world.player.pos)[0])
    world.monsters.append(m)
    world.start_battle(m)
    ok(not hasattr(world.battle, "bar"), "no timing bar in Classic")
    calls = []
    world.battle_action = calls.append
    phase2.battle_action(world, "attack", 5.0)
    ok(calls == ["attack"], "A is the classic attack")
    ok(phase2.faces_left(world, m) == (world.player.pos[1] < m.pos[1]), "and monsters look at you like before")


def test_every_land_has_its_monster_mix_and_none_start_in_a_village():
    world = Phase2Game("Hero", seed=1)
    lands = {land[0] for land in world.atlas.lands}
    ok(lands <= set(monsters.LAND_MONSTERS), "every land has its own monster mix: %s" % sorted(lands - set(monsters.LAND_MONSTERS)))
    level = {land: max(monsters.LEVELS[kind] for kind in mix) for land, mix in monsters.LAND_MONSTERS.items()}
    middle = max(level[land] for land in ("Whispering Woods", "The Great Lake", "Old Ruins"))
    ok(level["Home Meadow"] < middle, "Home Meadow has only weak monsters")
    for tough in ("Frost Peaks", "Sunscorch Desert", "Murk Swamp"):
        ok(level[tough] > middle, "%s has tougher monsters than the middle lands" % tough)
    villages = world.atlas.villages
    ok(len(villages) >= 4, "the world has villages")
    for name, (r, c), _ in villages:
        square = {(r + dr, c + dc) for dr in range(-2, 3) for dc in range(-2, 3)}
        ok(square <= world.safe_squares, "%s's square is safe" % name)
        ok(not [m for m in world.monsters if m.pos in square], "no monster starts in %s" % name)
