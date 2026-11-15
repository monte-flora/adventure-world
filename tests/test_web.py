"""
The web-browser version: the music files, loading them, the word pictures we keep,
and main.py (which runs the game the way a browser needs).
"""

import asyncio
import importlib.util
import os

import pygame
import pytest

import game
from helpers import new_app, ok

WEB_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")


def load(path, name):
    """Import a .py file that isn't in a package (like web/build_web.py)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def music_folder(tmp_path_factory):
    """Make every tune into a sound file, the way web/build_web.py does."""
    folder = tmp_path_factory.mktemp("web_music")
    build_web = load(os.path.join(WEB_FOLDER, "build_web.py"), "build_web")
    build_web.make_music(str(folder))
    return folder


def test_every_tune_becomes_a_sound_file(music_folder):
    files = sorted(os.listdir(music_folder))
    names = sorted(os.path.splitext(f)[0] for f in files)
    ok(names == sorted(game.TUNES), "one sound file for every tune: %s" % files)
    for f in files:
        sound = pygame.mixer.Sound(os.path.join(music_folder, f))
        ok(sound.get_length() > 5, "%s plays for %.0f seconds" % (f, sound.get_length()))


def test_in_a_browser_the_music_comes_from_the_files(music_folder, monkeypatch):
    monkeypatch.setattr(game, "IN_BROWSER", True)
    monkeypatch.setattr(game, "WEB_MUSIC_FOLDER", str(music_folder))
    music = game.Music(enabled=True)
    ok(music.channel is not None, "the music has speakers to play on (pretend ones, in a test)")
    ok(set(music.tunes) == set(game.TUNES), "in a browser, every tune is loaded straight away, with no background work")


def test_a_missing_tune_just_stays_quiet(tmp_path, monkeypatch):
    monkeypatch.setattr(game, "IN_BROWSER", True)
    monkeypatch.setattr(game, "WEB_MUSIC_FOLDER", str(tmp_path))      # an empty folder
    music = game.Music(enabled=True)
    ok(music.tunes == {}, "no music files? no music, and no crash")
    music.play("home", True)


def test_words_are_drawn_once_and_kept():
    app = new_app()
    app.word_pictures.clear()
    for _ in range(3):
        app.text(app.screen, "Hello Hero", (10, 10), 24)
    ok(len(app.word_pictures) == 1, "the same words drawn 3 times are turned into pixels just once")
    app.text(app.screen, "Hello Hero", (10, 10), 24, alpha=80)
    kept = app.words("Hello Hero", 24, game.TEXT)
    ok(kept.get_alpha() in (None, 255), "fading words in and out doesn't fade the kept picture")
    ok(app.wrap("one two three four", 24, 60) == app.wrap("one two three four", 24, 60),
       "wrapping the same text gives the same lines every time")


def test_main_runs_the_game_the_browser_way(monkeypatch):
    main = load(os.path.join(os.path.dirname(WEB_FOLDER), "main.py"), "web_main")
    frames = []
    real_step = game.App.step

    def step(app, dt):
        real_step(app, dt)
        frames.append(app.state)
        if len(frames) >= 30:
            app.running = False                   # pretend the player quit

    monkeypatch.setattr(game.App, "step", step)
    asyncio.run(main.main())
    ok(len(frames) == 30 and frames[0] == "title", "main.py runs the game one picture at a time, from the title screen")


def test_in_a_browser_quitting_goes_back_to_the_title(monkeypatch):
    main = load(os.path.join(os.path.dirname(WEB_FOLDER), "main.py"), "web_main_2")
    games = []

    async def play(wanted):
        games.append(set(wanted))
        if len(games) == 2:
            monkeypatch.setattr(game, "IN_BROWSER", False)   # stop the test after the 2nd game

    monkeypatch.setattr(game, "IN_BROWSER", True)
    monkeypatch.setattr(main, "play", play)
    monkeypatch.setattr(main, "shortcuts_in_the_web_address", lambda: {"throne", "fps"})
    asyncio.run(main.main())
    ok(len(games) == 2, "quitting in a browser starts a new game instead of leaving an empty page")
    ok(games[1] == {"fps"}, "the new game starts at the title, not back in the throne room")
