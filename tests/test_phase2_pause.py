"""
THE PAUSE MENU and THE SAVE SLOTS (phase2/pause.py, phase2/save.py): P or ESC pauses Phase 2 and
freezes it; the menu saves, goes to the title or quits; the title screen has 3 save slots.
"""

import json

import pygame

import game
import phase2
import rules
from helpers import frames, ok, press, walk_into_a_mine
from phase2 import Phase2Game, pause, save
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)


def pick(app, choice):
    """Move the menu's light to this choice and press ENTER."""
    menu = app.pause_menu
    while menu.rows[menu.row][0] != choice:
        press(app, pygame.K_DOWN)
    press(app, pygame.K_RETURN)


def a_game(name="Hero", wood=0, slot=1):
    world = Phase2Game(name, seed=1)
    world.player.wood = wood
    world.save_slot = slot
    return world


# ===========================================================================
# Pausing
# ===========================================================================

def test_P_and_ESC_pause_the_map_and_nothing_moves():
    app = new_phase2_app()
    frames(app, 5)
    for key in (pygame.K_p, pygame.K_ESCAPE):
        press(app, key)
        ok(app.pause_menu is not None and app.running, "%s pauses (and doesn't quit)" % pygame.key.name(key))
        game_now, turn, time, played = app.game, app.game.turn, app.time, app.game.play_time
        spot = app.game.player.pos
        press(app, pygame.K_RIGHT)
        press(app, pygame.K_LEFT)
        frames(app, 60)
        ok(app.game.player.pos == spot and app.game.turn == turn, "the arrow keys work the menu: you don't walk")
        ok(app.time == time and app.game.play_time == played, "the clock and the play time stop")
        ok(app.game is game_now and app.state == "play", "the game is just frozen")
        press(app, key)
        ok(app.pause_menu is None, "the same key closes it again")
        frames(app, 10)
        ok(app.time > time and app.game.play_time > played, "and time goes on again")


def test_a_cave_freezes_while_paused(own_save_file):
    app = new_phase2_app()
    cave = walk_into_a_mine(app)
    ok(cave is not None and app.state == "cave", "in a cave")
    frames(app, 5)
    press(app, pygame.K_ESCAPE)
    ok(app.pause_menu is not None, "ESC pauses in a cave")
    clock, you = cave.clock, (cave.you.x, cave.you.y)
    monsters = [(m.x, m.y) for m in cave.monsters]
    frames(app, 90)
    ok(cave.clock == clock and (cave.you.x, cave.you.y) == you, "the cave's clock (traps, lava) stops")
    ok([(m.x, m.y) for m in cave.monsters] == monsters, "and its monsters stand still")
    pick(app, "resume")
    ok(app.pause_menu is None, "Resume goes back to the cave")
    frames(app, 5)
    ok(cave.clock > clock, "and the cave goes on")


def test_a_map_fight_freezes_while_paused():
    app = new_phase2_app()
    world = app.game
    monster = rules.Monster("Zombie", world.neighbors(world.player.pos)[0])
    world.monsters = [monster]
    world.start_battle(monster)
    frames(app, 3)
    ok(app.state == "battle", "a fight")
    press(app, pygame.K_p)
    time = app.time
    press(app, pygame.K_a)
    frames(app, 60)
    ok(app.time == time and monster.health == monster.max_health, "the timing bar stops, and A doesn't attack")
    press(app, pygame.K_ESCAPE)
    ok(app.pause_menu is None and app.state == "battle", "back in the fight")


def test_classic_never_pauses(own_save_file):
    app = game.App("Hero", seed=1, sound=False)
    app.new_game()
    app.game.story.clear()
    frames(app, 3)
    press(app, pygame.K_p)
    ok(getattr(app, "pause_menu", None) is None and app.running, "P does nothing in Classic")
    press(app, pygame.K_ESCAPE)
    ok(not app.running and not own_save_file.exists(), "and ESC quits at once, just like before")


def test_ESC_still_closes_the_travel_list_but_P_pauses():
    app = new_phase2_app()
    app.game.travel_open = True
    ok(not pause.wants_pause(app, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)),
       "ESC with the travel list open closes the list, not pause")
    ok(pause.wants_pause(app, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)), "P still pauses")
    app.game.travel_open = False
    app.state = "people"
    ok(not pause.wants_pause(app, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)),
       "ESC in a dialogue box or the shop closes it")
    ok(pause.wants_pause(app, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)), "P pauses there too")


def test_the_menu_shows_where_you_are_and_draws():
    app = new_phase2_app()
    app.game.play_time = 125
    press(app, pygame.K_p)
    lines = pause.info_lines(app.game)
    ok("Level 1" in lines[0] and "Home" in lines[0], "the land and the level: %r" % lines[0])
    ok(lines[1].startswith("Light Stones: 0 of"), "the Light Stones")
    ok(lines[2] == "Play time: 2 min", "the play time")
    frames(app, 3)
    ok([words for _, words in app.pause_menu.rows] == ["Resume", "Save game", "Save and go to the title", "Quit"],
       "the 4 choices")
    row, number = app.pause_menu.spots[1]
    app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=row.center, rel=(0, 0), buttons=(0, 0, 0)))
    ok(app.pause_menu.row == 1, "the mouse lights a row")


# ===========================================================================
# The menu's choices
# ===========================================================================

def test_save_game(own_save_file):
    app = new_phase2_app()
    app.game.player.wood = 4
    press(app, pygame.K_p)
    pick(app, "save")
    ok(app.pause_menu.message == "Game saved!" and own_save_file.exists(), "Save game saves into slot 1")
    ok(save.load_game(1).player.wood == 4, "with your wood")


def test_saving_in_a_cave_loads_at_the_mine(own_save_file):
    app = new_phase2_app()
    cave = walk_into_a_mine(app)
    mine = app.game.player.pos
    own_save_file.unlink()
    press(app, pygame.K_p)
    pick(app, "save")
    ok(app.pause_menu.message == "Saved. You'll start outside this Mine.", "it says where you'll start")
    back = save.load_game(1)
    ok(back.cave is None and back.player.pos == mine and app.game.cave is cave, "the load is on the map at the Mine")


def test_save_and_go_to_the_title(own_save_file):
    app = new_phase2_app()
    press(app, pygame.K_p)
    pick(app, "title")
    ok(app.state == "title" and app.pause_menu is None and own_save_file.exists(), "saved, and on the title screen")
    ok("continue" in app.modes and not phase2.is_phase2(app.game), "Load is there now")
    frames(app, 3)


def test_quit_asks_save_first(own_save_file):
    app = new_phase2_app()
    press(app, pygame.K_p)
    pick(app, "quit")
    ok(app.pause_menu.page == "quit", "Quit asks: Save first?")
    pick(app, "back")
    ok(app.pause_menu.page == "menu" and app.running, "Back goes back to the menu")
    pick(app, "quit")
    pick(app, "no")
    ok(not app.running and not own_save_file.exists(), "No quits without saving")

    app = new_phase2_app()
    press(app, pygame.K_p)
    pick(app, "quit")
    pick(app, "yes")
    ok(not app.running and own_save_file.exists(), "Yes saves, then quits")


# ===========================================================================
# Save slots
# ===========================================================================

def test_three_slots_are_separate(own_save_file):
    for slot in save.SLOTS:
        ok(save.save_game(a_game("Kid%d" % slot, wood=slot, slot=slot)), "slot %d saves" % slot)
    for slot in save.SLOTS:
        back = save.load_game(slot)
        ok(back.player.wood == slot and back.save_slot == slot, "slot %d loads its own game" % slot)
    save.delete_save(2)
    ok(save.used_slots() == [1, 3] and save.load_game(2) is None, "deleting slot 2 leaves 1 and 3")
    ok(save.slot_info(2)["empty"], "slot 2 says Empty")
    info = save.slot_info(3)
    ok(info["name"] == "Kid3" and info["level"] == 1 and info["stones"] == 0 and info["saved_at"], "slot 3's summary")


def test_play_time_is_saved(own_save_file):
    world = a_game()
    world.play_time = 3725
    save.save_game(world)
    ok(save.load_game().play_time == 3725, "play time comes back")
    ok(save.time_words(3725) == "1 h 02 min" and save.time_words(30) == "under a minute", "and reads nicely")


def test_an_old_save_is_slot_1(own_save_file):
    data = save.game_to_data(a_game("Old", wood=6))
    del data["summary"]                          # a save from before there were slots
    own_save_file.write_text(json.dumps(data))
    info = save.slot_info(1)
    ok(not info["empty"] and info["name"] == "Old", "the old save file shows up as slot 1")
    ok(save.load_game(1).player.wood == 6 and own_save_file.exists(), "it loads, and the file is still there")


def test_in_a_browser_each_slot_is_a_key(monkeypatch, own_save_file):
    storage = {}

    class Storage:
        def setItem(self, key, value):
            storage[key] = value

        def getItem(self, key):
            return storage.get(key)

        def removeItem(self, key):
            storage.pop(key, None)

    monkeypatch.setattr(save, "IN_BROWSER", True)
    monkeypatch.setattr(save, "browser_storage", Storage)
    save.save_game(a_game(slot=1))
    save.save_game(a_game(slot=3))
    ok(set(storage) == {save.BROWSER_NAME, save.BROWSER_NAME + "_3"}, "slot 1 keeps the old key, slot 3 its own")
    ok(save.used_slots() == [1, 3] and not own_save_file.exists(), "no files")


# ===========================================================================
# The title screen
# ===========================================================================

def test_load_opens_the_slot_list(own_save_file):
    save.save_game(a_game("Two", wood=2, slot=2))
    app = game.App("Someone", sound=False)
    ok("continue" in app.modes and game.GAME_MODES["continue"] == "Load", "Load is on the title screen")
    app.mode = "continue"
    press(app, pygame.K_RETURN)
    ok(app.slot_list is not None and app.slot_list.slot == 2 and app.state == "title",
       "ENTER on Load opens the slot list, on the first saved slot")
    frames(app, 2)
    ok(pause.slot_words(app.slot_list.infos[0]) == ("Empty", ""), "an empty slot says Empty")
    first, second = pause.slot_words(app.slot_list.infos[1])
    ok(first.startswith("Two  -  Home") and "Level 1" in first and "Light Stones: 0 of " in second and "saved" in second,
       "a used slot shows the name, land, level, Light Stones, play time and date")
    press(app, pygame.K_RETURN)
    ok(app.state == "play" and app.game.player.wood == 2 and app.game.save_slot == 2, "ENTER loads slot 2")


def test_delete_a_slot_from_the_list(own_save_file):
    save.save_game(a_game(slot=1))
    save.save_game(a_game(slot=3))
    app = game.App("Hero", sound=False)
    app.mode = "continue"
    press(app, pygame.K_RETURN)
    press(app, pygame.K_d)
    ok(app.slot_list.sure is not None, "D asks: delete?")
    press(app, pygame.K_n)
    ok(save.has_save(1), "N keeps it")
    press(app, pygame.K_d)
    press(app, pygame.K_y)
    ok(not save.has_save(1) and save.has_save(3) and app.slot_list.infos[0]["empty"], "Y deletes slot 1")
    press(app, pygame.K_DOWN)
    press(app, pygame.K_DOWN)
    press(app, pygame.K_d)
    press(app, pygame.K_RETURN)                  # ("No" is lit first)
    ok(save.has_save(3), "ENTER on No keeps it")
    press(app, pygame.K_d)
    press(app, pygame.K_LEFT)
    press(app, pygame.K_RETURN)
    ok(not save.has_save() and app.slot_list is None and "continue" not in app.modes,
       "the last one deleted: the list closes and Load is gone")


def test_a_new_phase_2_game_picks_a_slot(own_save_file):
    save.save_game(a_game("Old", wood=9, slot=1))
    app = game.App("Hero", sound=False)
    app.mode = "phase2"
    press(app, pygame.K_RETURN)
    ok(app.slot_list.kind == "new" and app.slot_list.slot == 2, "Phase 2 asks which slot, an empty one lit")
    press(app, pygame.K_UP)
    press(app, pygame.K_RETURN)
    ok(app.slot_list.sure.page == "start over", "a used slot asks: Start over in this slot?")
    press(app, pygame.K_ESCAPE)
    ok(app.slot_list.sure is None and app.state == "title", "ESC: no")
    press(app, pygame.K_RETURN)
    press(app, pygame.K_y)
    ok(app.state != "title" and app.game.save_slot == 1 and app.game.player.wood == 0, "Yes starts a new game in slot 1")
    ok(not save.has_save(1), "and the old game there is gone")


def test_slot_list_escape_and_drawing(own_save_file):
    save.save_game(a_game())
    app = game.App("Hero", sound=False)
    app.mode = "continue"
    press(app, pygame.K_RETURN)
    frames(app, 2)
    row, number = app.slot_list.spots[2]
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=row.center, button=1))
    ok(app.slot_list.message == "That slot is empty.", "clicking an empty slot to load says it's empty")
    press(app, pygame.K_ESCAPE)
    ok(app.slot_list is None and app.running and app.state == "title", "ESC closes the list (and doesn't quit)")


def test_autosave_goes_into_the_current_slot(own_save_file):
    save.save_game(a_game(slot=1))
    app = game.App("Hero", sound=False)
    app.mode = "phase2"
    press(app, pygame.K_RETURN)
    press(app, pygame.K_RETURN)                  # slot 2 (empty) is lit
    world = app.game
    world.story.clear()
    world.monsters = []
    world.player.pos = (world.start[0], world.start[1] + 1)
    world.do("left")
    ok(save.has_save(2) and world.save_slot == 2, "walking into home saves into slot 2")


def test_the_pause_tip_is_phase_2_only():
    import tutorial
    ok(tutorial.TIPS["pause"] == "Press P to pause and save.", "the tip's words")
    ok(tutorial.phase2_started(rules.Game("Hero", seed=1)) is None, "never in Classic")
    ok(tutorial.phase2_started(a_game()) == ("you",), "in Phase 2")
