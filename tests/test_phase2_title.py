"""
PHASE 2 ON THE TITLE SCREEN: Classic or Phase 2 (and Continue, when there's a saved game).
LEFT and RIGHT (or a click) pick one, ENTER starts it. python game.py --phase2 skips the choice.
"""

import os
import sys

import pygame

import game
import phase2
import rules
from conftest import GAME_FOLDER
from helpers import click, frames, ok, press
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)


def test_ENTER_still_starts_the_classic_game():
    app = game.App("Hero", seed=1, sound=False)
    frames(app, 3)
    ok(app.modes == ["classic", "phase2"] and app.mode == "classic", "Classic is picked to start with")
    press(app, pygame.K_RETURN)
    ok(type(app.game) is rules.Game, "ENTER starts the classic game, just like before")


def test_RIGHT_picks_phase_2():
    app = game.App("Hero", seed=1, sound=False)
    press(app, pygame.K_RIGHT)
    ok(app.mode == "phase2", "RIGHT picks Phase 2")
    press(app, pygame.K_RIGHT)
    ok(app.mode == "classic", "and it goes round again")
    press(app, pygame.K_LEFT)
    press(app, pygame.K_RETURN)
    ok(phase2.is_phase2(app.game) and app.state in ("story", "play"), "ENTER starts Phase 2")
    ok(app.name_input == "Hero", "the arrow keys don't type in your name")


def test_a_click_picks_a_mode():
    app = game.App("Hero", seed=1, sound=False)
    frames(app, 2)                                   # the title is drawn, so the buttons have a place
    ok(set(app.mode_buttons) == {"classic", "phase2"}, "a button for each mode")
    click(app, app.mode_buttons["phase2"].center)
    ok(app.mode == "phase2", "clicking Phase 2 picks it")
    click(app, app.mode_buttons["classic"].center)
    ok(app.mode == "classic", "clicking Classic picks it again")


def test_continue_shows_up_when_there_is_a_save(own_save_file):
    ok("continue" not in game.App("Hero", sound=False).modes, "no save: no Continue")
    app = new_phase2_app()
    app.game.player.pos = (5, 50)
    app.game.player.wood = 7
    ok(app.game.autosave(), "the game saves")
    app = game.App("Someone", sound=False)
    ok(app.modes[-1] == "continue", "with a save, Continue is on the title screen")
    frames(app, 2)
    ok("continue" in app.mode_buttons, "and it has a button")
    press(app, pygame.K_LEFT)
    ok(app.mode == "continue", "LEFT from Classic goes round to Continue")
    press(app, pygame.K_RETURN)
    ok(app.slot_list is not None, "Continue (now called Load) opens the save slot list (phase2/pause.py)")
    press(app, pygame.K_RETURN)
    p = app.game.player
    ok(app.state == "play" and phase2.is_phase2(app.game), "ENTER on the saved slot goes straight back onto the map")
    ok(p.pos == (5, 50) and p.wood == 7 and p.name == "Hero", "right where you saved, with your things")


def test_a_broken_save_starts_a_new_phase_2_game(own_save_file):
    own_save_file.write_text("{not json")
    app = game.App("Hero", sound=False)
    ok("continue" in app.modes, "there's a file, so Continue shows")
    app.mode = "continue"
    app.new_game()
    ok(phase2.is_phase2(app.game) and app.game.turn == 1, "it can't be read, so a new Phase 2 game starts")


def test_the_phase2_flag_starts_phase_2(monkeypatch):
    app = game.App("Hero", seed=1, sound=False, phase2_mode="phase2")
    ok(app.state != "title" and phase2.is_phase2(app.game), "App(phase2_mode='phase2') skips the title")
    made = {}

    class FakeApp:
        def __init__(self, *args, **kwargs):
            made.update(kwargs)

        def run(self):
            pass

    monkeypatch.setattr(game, "App", FakeApp)
    monkeypatch.setattr(sys, "argv", ["game.py", "--phase2"])
    game.main()
    ok(made["phase2_mode"] == "phase2", "python game.py --phase2 asks for Phase 2")
    monkeypatch.setattr(sys, "argv", ["game.py", "--continue"])
    game.main()
    ok(made["phase2_mode"] == "continue", "python game.py --continue asks for the saved game")
    monkeypatch.setattr(sys, "argv", ["game.py"])
    game.main()
    ok(made["phase2_mode"] is None, "plain python game.py shows the title screen")


def test_pixi_has_a_game2_task():
    with open(os.path.join(GAME_FOLDER, "pixi.toml"), encoding="utf-8") as f:
        ok('game2 = { cmd = "python game.py --phase2"' in f.read(), "pixi run game2 starts Phase 2")
