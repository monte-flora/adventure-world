"""
SAVING AND LOADING Phase 2: it saves by itself in a house, at a Mine and when you quit,
and the saved game comes back just the way it was.
"""

import json

import pygame

import game
import rules
from helpers import frames, ok, press, walk_into_a_mine
from phase2 import Phase2Game, save
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)


def played_a_bit():
    """A Phase 2 game with things changed: you walked, chopped, crafted, beat monsters..."""
    world = Phase2Game("Hero", seed=4)
    p = world.player
    p.pos, p.wood, p.food, p.arrows, p.has_bow, p.xp = (10, 45), 9, 2, 6, True, 33
    p.swords.append(rules.make_sword("great"))
    p.powers["Stronger"] = 1
    world.monster_quest.progress = 3
    world.map[2][2] = "G"                                  # a tree chopped down
    world.tree_wood[(3, 3)] = 4
    world.cleared_mines.add(next(iter(world.cave_plan)))
    world.cave_changes[(1, 1)] = {(2, 3): "."}
    world.turn = 77
    return world


def test_saving_and_loading_gives_back_the_same_game():
    world = played_a_bit()
    ok(save.save_game(world), "it saves")
    back = save.load_game()
    ok(isinstance(back, Phase2Game), "it loads a Phase 2 game")
    for name in ("map", "rows", "cols", "start", "portal", "turn", "cave_plan", "diamond_mines", "cleared_mines",
                 "tree_wood", "cave_changes", "lands_seen", "seen", "landmarks", "lodges", "river", "secret_mines"):
        ok(getattr(back, name) == getattr(world, name), "the game's %s comes back the same" % name)
    ok(vars(back.player).keys() == vars(world.player).keys(), "the player has all their things")
    for name, value in vars(world.player).items():
        if name not in ("swords", "pickaxe"):
            ok(getattr(back.player, name) == value, "the player's %s comes back the same" % name)
    ok([vars(s) for s in back.player.swords] == [vars(s) for s in world.player.swords], "both swords, the Great one too")
    ok(vars(back.player.pickaxe) == vars(world.player.pickaxe), "and the pickaxe")
    ok([(m.kind, m.pos, m.health) for m in back.monsters] == [(m.kind, m.pos, m.health) for m in world.monsters],
       "every monster, where it was")
    ok(back.quests[0] is back.monster_quest and back.monster_quest.progress == 3, "the quests (still one quest, not two)")
    ok(back.land_name((50, 100)) == "Sunscorch Desert", "the lands come back too")
    ok(back.rng.random() == world.rng.random(), "even the dice roll the same")
    ok(back.cave is None and back.battle is None, "you come back on the map")


def test_a_loaded_game_plays_on():
    save.save_game(played_a_bit())
    world = save.load_game()
    world.monsters = []
    for way in ("down", "left", "up", "right", "down"):
        world.do(way)
    ok(world.turn > 77, "turns go on after loading")
    world.go_to_nightfall()
    ok(world.world == 2 and len(world.seen) == world.rows * world.cols, "and the Portal still works")
    ok(save.save_game(world) and save.load_game().world == 2, "Nightfall Hollow saves too")


def test_it_saves_when_you_go_into_a_house(own_save_file):
    world = Phase2Game("Hero", seed=1)
    world.monsters = []
    world.player.pos = (world.start[0], world.start[1] + 1)
    ok(not own_save_file.exists(), "nothing is saved yet")
    world.do("left")
    ok(world.here == "H" and own_save_file.exists(), "walking into home saves the game")
    ok(json.loads(own_save_file.read_text())["version"] == save.VERSION, "it's a JSON file")


def test_it_saves_when_you_go_into_a_Mine(own_save_file):
    app = new_phase2_app()
    cave = walk_into_a_mine(app)
    ok(cave is not None and own_save_file.exists(), "climbing down into a Mine saves first")
    back = save.load_game()
    ok(back.cave is None and back.player.pos == app.game.player.pos, "the save is on the map, at the Mine")


def test_it_saves_when_you_quit(own_save_file):
    app = new_phase2_app()
    app.game.player.wood = 5
    press(app, pygame.K_ESCAPE)
    ok(app.running and app.pause_menu, "ESC in Phase 2 opens the pause menu now (phase2/pause.py)")
    app.handle_event(pygame.event.Event(pygame.QUIT))
    frames(app)
    ok(not app.running and own_save_file.exists(), "closing the window quits, and the game is saved")
    ok(save.load_game().player.wood == 5, "with your wood")


def test_the_classic_game_never_saves(own_save_file):
    app = game.App("Hero", seed=1, sound=False)
    app.new_game()
    app.game.story.clear()
    app.game.monsters = []
    walk_into_a_mine(app)
    app.game.cave = None
    app.state = "play"
    press(app, pygame.K_ESCAPE)
    ok(not own_save_file.exists(), "Classic plays exactly as before: no save file")


def test_in_a_browser_it_saves_in_the_browser(monkeypatch, own_save_file):
    class Storage(dict):
        def setItem(self, key, value):
            self[key] = value

        def getItem(self, key):
            return self.get(key)

        def removeItem(self, key):
            self.pop(key, None)

    storage = Storage()
    monkeypatch.setattr(save, "IN_BROWSER", True)
    monkeypatch.setattr(save, "browser_storage", lambda: storage)
    ok(not save.has_save(), "no save in the browser yet")
    ok(save.save_game(played_a_bit()), "it saves")
    ok(save.BROWSER_NAME in storage and not own_save_file.exists(), "in the browser's storage, not a file")
    ok(save.load_game().turn == 77, "and loads back")
    save.delete_save()
    ok(not save.has_save(), "and can be deleted")

    def no_storage():
        raise ImportError("no browser here")

    monkeypatch.setattr(save, "browser_storage", no_storage)
    ok(save.save_game(played_a_bit()) is False and save.load_game() is None, "no storage? it just doesn't save")


def test_a_save_from_before_the_rename_still_loads(monkeypatch, tmp_path):
    monkeypatch.delenv("ADVENTURE_SAVE_FILE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))                       # a pretend home folder
    old = tmp_path / save.OLD_FOLDER / "phase2_save_2.json"
    old.parent.mkdir()
    old.write_text(json.dumps(save.game_to_data(played_a_bit())))
    ok(save.has_save(2) and save.load_game(2).turn == 77, "an old save in the older folder loads")
    ok(save.save_game(save.load_game(2)), "and saves again")
    ok((tmp_path / ".adventure" / "phase2_save_2.json").exists() and not old.exists(),
       "into the new folder, and the older copy is gone")
    ok(save.load_game(2).turn == 77, "still the same game")


def test_a_browser_save_from_before_the_rename_still_loads(monkeypatch, own_save_file):
    class Storage(dict):
        def setItem(self, key, value):
            self[key] = value

        def getItem(self, key):
            return self.get(key)

        def removeItem(self, key):
            self.pop(key, None)

    storage = Storage({save.OLD_BROWSER_NAME: json.dumps(save.game_to_data(played_a_bit()))})
    monkeypatch.setattr(save, "IN_BROWSER", True)
    monkeypatch.setattr(save, "browser_storage", lambda: storage)
    ok(save.has_save(1) and save.load_game(1).turn == 77, "a save under the older key loads")
    ok(save.save_game(save.load_game(1)), "and saves again")
    ok(list(storage) == [save.BROWSER_NAME], "under the new key only: %s" % list(storage))
    ok(save.BROWSER_NAME == "adventure_phase2_save", "the new key")


def test_a_save_that_cant_be_written_doesnt_stop_the_game(monkeypatch, tmp_path):
    blocker = tmp_path / "a_file"
    blocker.write_text("")
    monkeypatch.setenv("ADVENTURE_SAVE_FILE", str(blocker / "save.json"))     # a folder that can't exist
    app = new_phase2_app()
    world = app.game
    world.player.pos = (world.start[0], world.start[1] + 1)
    world.do("left")
    frames(app, 3)
    ok(app.running and world.here == "H", "the game goes on")
