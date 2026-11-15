"""
Tip bubbles (tutorial.py): each tip shows once, at the right moment, pointing at the thing
it's about. The game waits while you read it. ENTER closes it, S turns all tips off, and
TAB on the title screen turns them back on. The choice is saved for next time (settings.py).
A bubble never gets in the way of a fight or a story card.
"""

import importlib
import json
import os
import sys

import pygame
import pytest

import caves
import game
import rules
import settings
import tutorial
from conftest import GAME_FOLDER
from helpers import DT, click, frames, hold_keys, new_app, ok, press, start_game, tiles


@pytest.fixture(autouse=True)
def tips_on(monkeypatch):
    """Tips ON - as if you'd never played before. (conftest.py gives each test its own empty settings file.)"""
    monkeypatch.setattr(tutorial, "START_WITH_TIPS", True)


def wait_for_tip(app, seconds=4):
    """Let the game run until a tip bubble pops up. Returns the tip's name (None if none came)."""
    for _ in range(int(seconds / DT)):
        frames(app)
        if app.state == "tip":
            return app.bubble["name"]
    return None


def close_tip(app, key=pygame.K_RETURN):
    """Read the bubble for a moment (so the keys work), then press a key."""
    frames(app, int(game.TIP_READ_TIME / DT) + 2)
    press(app, key)


def only(app, name):
    """Pretend you've already seen every tip but this one, so it's the only one that can show."""
    app.tips.seen = {other for other in tutorial.TIPS if other != name}


def stand_on(app, spot):
    world = app.game
    world.player.pos = spot
    world.reveal()
    app.player_px = list(game.tile_px(spot))


def nearest(world, letter):
    return min(tiles(world, letter), key=lambda spot: (rules.distance(spot, world.start), spot))


def next_to(world, letter):
    """A square you can stand on, right next to the nearest one of these."""
    return next(spot for spot in world.neighbors(nearest(world, letter)))


def saved():
    with open(settings.SETTINGS_FILE) as file:
        return json.load(file)


# ===========================================================================
# Every tip can show
# ===========================================================================

def start_phase2(app):
    app.mode = "phase2"
    start_game(app)


MAP_SETUPS = {
    "walk":     lambda app, world, p: None,
    "pause":    lambda app, world, p: start_phase2(app),        # (Phase 2 only: it saves)
    "monster":  lambda app, world, p: world.monsters.append(rules.Monster("Zombie", world.neighbors(p.pos)[0])),
    "eat":      lambda app, world, p: (setattr(p, "health", p.max_health // 2), setattr(p, "food", 1)),
    "forest":   lambda app, world, p: stand_on(app, nearest(world, "F")),
    "path":     lambda app, world, p: stand_on(app, nearest(world, "R")),
    "map ice":  lambda app, world, p: stand_on(app, nearest(world, "I")),
    "reeds":    lambda app, world, p: stand_on(app, nearest(world, "B")),
    "vent":     lambda app, world, p: stand_on(app, nearest(world, "V")),
    "water":    lambda app, world, p: stand_on(app, next(spot for spot in tiles(world, "G")
                                                         if world.neighbors(spot, water=True))),
    "craft":    lambda app, world, p: setattr(p, "wood", rules.BOW_COST),
    "bow":      lambda app, world, p: (setattr(p, "has_bow", True), setattr(p, "arrows", 3)),
    "mine":     lambda app, world, p: stand_on(app, next_to(world, "M")),
    "landmark": lambda app, world, p: stand_on(app, next_to(world, "L")),
    "land":     lambda app, world, p: world.lands_seen.add("Ember Canyon"),
    "portal":   lambda app, world, p: stand_on(app, next_to(world, "P")),
}


@pytest.mark.parametrize("name", sorted(MAP_SETUPS))
def test_every_map_tip_can_show(name):
    app = new_app()
    only(app, name)
    MAP_SETUPS[name](app, app.game, app.game.player)
    ok(wait_for_tip(app) == name, "the %r tip should pop up" % name)
    ok(app.tip_target(app.bubble["where"]), "the %r tip should point at something on the screen" % name)
    frames(app, 3)                                  # and drawing it works


# A plain room: the floor is row 13, and you start on row 12 (S)
ROOM = ["##############",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        ".............#",
        ".............#",
        "..S..........#",
        "##############"]


def room_with(**rows):
    """The plain room, with some rows drawn differently: room_with(row12="..S..T.......#")"""
    drawing = list(ROOM)
    for row, line in rows.items():
        drawing[int(row[3:])] = line
    return drawing


CAVE_SETUPS = {
    "cave":         ROOM,
    "cave monster": room_with(row11="......#......#", row12="..S...#.z....#"),   # behind a wall, so it can't come close
    "ladder":       room_with(row10=".....H.......#", row11=".....H.......#", row12="..S..H.......#"),
    "vine":         room_with(row9="#....V.......#", row10=".....V.......#"),
    "swing":        room_with(row1="#....R.......#", row2="#....R.......#",
                              row3="#....R.......#", row4="#....R.......#", row5="#....R.......#",
                              row6="#....R.......#", row7="#....R.......#", row8="#....R.......#"),
    "wall":         room_with(row11=".....%.......#", row12="..S..%.......#"),
    "tunnel":       room_with(row11="....##########"),
    "cave ice":     room_with(row13="####III#######"),
    "diamond":      room_with(row12="..S..*.......#"),
    "dig":          room_with(row12="..S..B.......#"),
    "chest":        room_with(row12="..S..T.......#"),
    "exit":         room_with(row12="..S..E.......#"),
}


def go_into(app, drawing):
    """Climb down into a cave drawn right here in the test."""
    world = app.game
    cave = caves.Cave(world, world.start, "\n".join(drawing))
    world.cave = cave
    frames(app)                                     # the game sees the cave and climbs down into it
    return cave


@pytest.mark.parametrize("name", sorted(CAVE_SETUPS))
def test_every_cave_tip_can_show(name):
    app = new_app()
    only(app, name)
    go_into(app, CAVE_SETUPS[name])
    ok(wait_for_tip(app) == name, "the %r tip should pop up in the cave" % name)
    ok(app.tip_target(app.bubble["where"]), "the %r tip should point at something on the screen" % name)
    frames(app, 3)


def test_every_tip_has_a_moment_and_words():
    ok({name for name, moment in tutorial.MOMENTS} == set(tutorial.TIPS),
       "every tip in TIPS should have a moment in MOMENTS, and the other way round")
    ok(set(MAP_SETUPS) | set(CAVE_SETUPS) == set(tutorial.TIPS), "every tip should be tested above")


# ===========================================================================
# Each tip shows once
# ===========================================================================

def test_the_first_tip_points_at_you():
    app = new_app()
    ok(wait_for_tip(app) == "walk", "the very first tip says how to walk")
    you = pygame.Rect(game.tile_px(app.game.player.pos), (game.TILE, game.TILE)).move(-app.cam[0], -app.cam[1])
    ok(app.tip_target(app.bubble["where"]).colliderect(you), "it points at you")


def test_each_tip_shows_only_once_even_next_time_you_play():
    app = new_app()
    only(app, "walk")
    ok(wait_for_tip(app) == "walk", "the walking tip pops up")
    close_tip(app)
    ok(app.state == "play" and app.bubble is None, "ENTER closes it, and you can play")
    app.tip_turn = None                             # (so the next tip doesn't wait for a step)
    ok(wait_for_tip(app, seconds=3) is None, "it doesn't come back, even though it's still the first turn")
    start_game(app)
    ok(wait_for_tip(app, seconds=3) is None, "not in the next game either")
    ok("walk" in saved()["tips_seen"], "it's saved in settings.json")
    again = new_app()
    ok("walk" in again.tips.seen and wait_for_tip(again, seconds=3) is None, "and not next time you start the game")


def test_closing_one_tip_lets_the_next_one_come():
    app = new_app()
    stand_on(app, nearest(app.game, "F"))
    ok(wait_for_tip(app) == "walk", "walking comes first")
    close_tip(app, pygame.K_SPACE)
    ok(app.state == "play", "SPACE closes it too")
    frames(app, int(game.TIP_GAP / DT) + 30)
    ok(app.state == "play", "on the map, the next tip waits until you take a step...")
    press(app, pygame.K_z)                          # (Z waits a turn - that counts too)
    ok(wait_for_tip(app) == "forest", "...and then the forest tip comes")


def test_a_click_closes_a_tip():
    app = new_app()
    wait_for_tip(app)
    frames(app, int(game.TIP_READ_TIME / DT) + 2)
    click(app, (20, 20))
    ok(app.state == "play" and app.tips.on, "a click closes the bubble (and tips stay on)")


# ===========================================================================
# The game waits while you read - and you can't skip one by accident
# ===========================================================================

def test_a_cave_waits_while_a_tip_shows(monkeypatch):
    held = hold_keys(monkeypatch)
    app = new_app()
    only(app, "cave")
    cave = go_into(app, ROOM)
    ok(wait_for_tip(app) == "cave", "the cave tip pops up")
    x, clock = cave.you.x, cave.clock
    held.add(pygame.K_RIGHT)
    frames(app, 60)
    ok(cave.you.x == x and cave.clock == clock, "nothing moves while the tip shows, even holding RIGHT")
    close_tip(app)
    frames(app, 30)
    ok(cave.you.x > x, "close it, and you run again")


def test_the_keys_wait_a_moment_first():
    app = new_app()
    wait_for_tip(app)
    press(app, pygame.K_RETURN)
    ok(app.state == "tip", "pressing ENTER straight away doesn't close it: read it first!")
    close_tip(app)
    ok(app.state == "play", "a moment later, ENTER closes it")


def test_a_key_you_were_already_holding_doesnt_close_it(monkeypatch):
    held = hold_keys(monkeypatch)
    app = new_app()
    only(app, "cave")
    cave = go_into(app, ROOM)
    held.add(pygame.K_SPACE)                        # holding SPACE down when the tip pops up
    ok(wait_for_tip(app) == "cave", "the tip pops up")
    frames(app, int(game.TIP_READ_TIME / DT) + 2)
    for _ in range(5):
        press(app, pygame.K_SPACE)                  # the key repeats while you hold it down
    ok(app.state == "tip", "holding SPACE down doesn't close it")
    held.discard(pygame.K_SPACE)
    press(app, pygame.K_SPACE, up=True)             # let go...
    held.add(pygame.K_SPACE)
    height = cave.you.y
    press(app, pygame.K_SPACE)                      # ...and press it again
    ok(app.state == "cave", "let go and press it again, and it closes")
    frames(app, 10)
    ok(cave.you.y == height, "and that SPACE was for the tip, not a jump")


# ===========================================================================
# Turning tips off (and on again) - and it's remembered
# ===========================================================================

def test_S_turns_all_tips_off_and_it_is_remembered():
    app = new_app()
    stand_on(app, nearest(app.game, "F"))
    wait_for_tip(app)
    close_tip(app, pygame.K_s)
    ok(app.state == "play" and not app.tips.on, "S closes the bubble and turns tips off")
    ok(wait_for_tip(app, seconds=3) is None, "no more tips, even in the forest")
    ok(saved()["tips"] is False, "it's saved in settings.json")
    again = new_app()
    stand_on(again, nearest(again.game, "F"))
    ok(not again.tips.on and wait_for_tip(again, seconds=3) is None, "next time you play, tips are still off")


def test_clicking_no_more_tips_turns_them_off():
    app = new_app()
    wait_for_tip(app)
    frames(app, int(game.TIP_READ_TIME / DT) + 2)
    click(app, app.tip_off_button.center)
    ok(app.state == "play" and not app.tips.on, "clicking 'no more tips' turns them off")


def test_TAB_on_the_title_screen_switches_tips_on_and_off():
    app = game.App("Hero", seed=1, sound=False)
    app.tips.saw("walk")
    frames(app)
    press(app, pygame.K_TAB)
    ok(not app.tips.on and saved()["tips"] is False, "TAB turns tips off, and it's saved")
    click(app, app.tips_switch.center)
    ok(app.tips.on and saved()["tips"] is True, "a click on the switch turns them back on")
    ok(not app.tips.seen, "turning tips on shows them all again, from the start")
    app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="\t"))
    ok(app.name_input == "Hero", "TAB doesn't type anything into your name")
    start_game(app)
    ok(wait_for_tip(app, seconds=6) == "walk", "the first tip is back")


def test_the_tests_never_touch_your_real_settings():
    real = os.path.join(GAME_FOLDER, "settings.json")
    ok(os.environ["ADVENTURE_SETTINGS_FILE"] != real, "the tests (and games they start) save settings somewhere else")
    ok(os.environ["ADVENTURE_SETTINGS_FILE"] == settings.SETTINGS_FILE, "a game this test starts uses this test's file")
    ok(not os.path.exists(settings.SETTINGS_FILE), "each test starts with nothing saved (no tips from another test)")
    fresh = importlib.reload(settings)              # read settings.py again, the way a new game would
    ok(fresh.SETTINGS_FILE == os.environ["ADVENTURE_SETTINGS_FILE"], "settings.py saves there too")


def test_a_mixed_up_settings_file_is_ignored():
    with open(settings.SETTINGS_FILE, "w") as file:
        file.write("this isn't JSON {")
    ok(tutorial.TipBook().on, "the game starts fresh, with tips on")


class FakeBrowserStorage:
    def __init__(self):
        self.things = {}

    def getItem(self, name):
        return self.things.get(name)

    def setItem(self, name, value):
        self.things[name] = value

    def removeItem(self, name):
        self.things.pop(name, None)


def test_in_a_browser_tips_are_saved_in_the_browser(monkeypatch):
    storage = FakeBrowserStorage()
    fake_platform = type(sys)("platform")
    fake_platform.window = type(sys)("window")
    fake_platform.window.localStorage = storage
    monkeypatch.setitem(sys.modules, "platform", fake_platform)
    monkeypatch.setattr(settings, "IN_BROWSER", True)
    ok(tutorial.TipBook().on, "nothing saved yet: tips are on")
    tutorial.TipBook().turn_off()
    ok(json.loads(storage.things[settings.BROWSER_NAME])["tips"] is False, "turning them off saves it in the browser")
    ok(not tutorial.TipBook().on, "and next time, they're still off")


def test_in_a_browser_choices_saved_under_the_older_key_still_load(monkeypatch):
    storage = FakeBrowserStorage()
    storage.things[settings.OLD_BROWSER_NAME] = json.dumps({"tips": False})     # saved before the rename
    fake_platform = type(sys)("platform")
    fake_platform.window = type(sys)("window")
    fake_platform.window.localStorage = storage
    monkeypatch.setitem(sys.modules, "platform", fake_platform)
    monkeypatch.setattr(settings, "IN_BROWSER", True)
    ok(settings.OLD_BROWSER_NAME != settings.BROWSER_NAME, "new saves use a different key")
    ok(not tutorial.TipBook().on, "tips turned off under the older key are still off")
    settings.save(tips_seen=["walk"])
    ok(json.loads(storage.things[settings.BROWSER_NAME]) == {"tips": False, "tips_seen": ["walk"]},
       "the next save moves everything to the new key")
    ok(settings.OLD_BROWSER_NAME not in storage.things, "and the older key is gone")
    ok(not tutorial.TipBook().on, "next time, they load from the new key")


# ===========================================================================
# A bubble never gets in the way of a fight or a story card
# ===========================================================================

def test_tips_wait_for_the_story_cards():
    app = new_app(story=True)
    frames(app, int(3 / DT))
    ok(app.state == "story", "the story cards show first, not a tip")
    press(app, pygame.K_s)                          # skip the story
    ok(wait_for_tip(app, seconds=6) == "walk", "after the story, the first tip comes")


def test_tips_never_open_in_a_fight():
    app = new_app()
    world = app.game
    stand_on(app, nearest(world, "F"))
    monster = rules.Monster("Zombie", world.neighbors(world.player.pos)[0])
    world.monsters.append(monster)
    world.start_battle(monster)
    frames(app, int(3 / DT))
    ok(app.state == "battle" and app.bubble is None, "no bubble in a fight, even with tips waiting")
    for _ in range(60):
        if world.battle is None:
            break
        press(app, pygame.K_a)                      # A attacks
        frames(app, 30)
        press(app, pygame.K_SPACE)                  # the fight is over: back to the map
    ok(world.battle is None and app.state != "battle", "the fight ends")
    ok(wait_for_tip(app) is not None, "and then the tips come")


def test_no_tips_while_a_cave_monster_is_close():
    app = new_app()
    only(app, "cave")
    go_into(app, room_with(row12="..S.z........#"))
    ok(wait_for_tip(app, seconds=2) is None, "a monster right next to you: fight first, no tips")


def test_no_tips_while_you_fight_the_shadow_king():
    app = game.App("Hero", seed=4, sound=False, throne=True)
    start_game(app)
    ok(app.game.cave.is_throne_room, "we're in the throne room")
    ok(wait_for_tip(app, seconds=3) is None, "no tips while you fight the Shadow King")


# ===========================================================================
# The bubble is painted once, and the help screen talks about tips
# ===========================================================================

def test_a_bubble_is_painted_once_and_kept():
    app = new_app()
    wait_for_tip(app)
    picture, under = app.tip_picture("walk"), app.tip_frame
    frames(app, 10)
    ok(app.tip_picture("walk") is picture and len(app.tip_pictures) == 1, "the same bubble is used every frame")
    ok(under is not None and app.tip_frame is under, "and the paused game under it is painted only once")
    close_tip(app)
    ok(app.tip_frame is None, "closing the bubble lets go of that picture")


def test_the_help_screen_says_how_tips_work():
    app = new_app()
    app.tips.on = False
    press(app, pygame.K_h)
    ok(any("Tip bubbles are OFF" in text for text, size, color in app.word_pictures),
       "the help screen says if tips are on, and how to switch them")
