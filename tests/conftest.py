"""
Set-up that every test shares. pytest reads this file by itself, before any test runs.

- The game runs with no window and no sound (the "dummy" drivers), so the tests work
  anywhere, even on GitHub's computers, which have no screen and no speakers.
- The game's files (game.py, rules.py, caves.py ...) are one folder up, so Python looks there too.
- Saved caves go in a temporary folder, so the tests never touch your real my_caves folder.
  Saved settings (like "tips off") do too, so they never touch your real settings.json.
  Each test even gets its own empty settings file, so what one test saves can't change the next one.
- Tip bubbles start off, so they don't pause the other tests. test_tutorial.py turns them on.
"""

import os
import pathlib
import sys
import tempfile

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# Saved settings go in a temporary folder. It's an environment variable, so a game a test starts
# with "python game.py" (test_game_starts.py) uses it too.
os.environ["ADVENTURE_SETTINGS_FILE"] = os.path.join(tempfile.mkdtemp(prefix="settings_test_"), "settings.json")
# The same for the saved Phase 2 game (phase2/save.py), so no test reads or writes your real save
os.environ["ADVENTURE_SAVE_FILE"] = os.path.join(tempfile.mkdtemp(prefix="save_test_"), "phase2_save.json")

GAME_FOLDER = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GAME_FOLDER))

import cave_files  # noqa: E402  (after the game folder is on the path)
import settings  # noqa: E402
import tutorial  # noqa: E402

cave_files.MY_CAVES_FOLDER = tempfile.mkdtemp(prefix="my_caves_test_")
tutorial.START_WITH_TIPS = False      # tip bubbles would pause the game, so they're off (test_tutorial.py turns them on)


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch, tmp_path):
    """Every test gets its own empty settings file. Without this, a game started with "python game.py"
    could close a tip bubble, save "tips on", and then a later test would get tip bubbles it didn't expect."""
    own_file = str(tmp_path / "settings.json")
    monkeypatch.setattr(settings, "SETTINGS_FILE", own_file)
    monkeypatch.setenv("ADVENTURE_SETTINGS_FILE", own_file)    # and a game the test starts uses it too


def pytest_addoption(parser):
    parser.addoption("--all-caves", action="store_true",
                     help="send the robot into every cave on the map, not just a few (slow: about 10 minutes)")


def pytest_collection_modifyitems(config, items):
    """Tests marked all_caves only run with --all-caves. The others are left out ("deselected")."""
    if config.getoption("--all-caves"):
        return
    left_out = [item for item in items if item.get_closest_marker("all_caves")]
    if left_out:
        config.hook.pytest_deselected(items=left_out)
        items[:] = [item for item in items if not item.get_closest_marker("all_caves")]
