"""
Little helpers the Phase 2 tests share (see phase2/ and PHASE2.md).

own_save_file: every Phase 2 test gets its own save file, so what one test saves can't change the next.
hold: hold a move key down for some frames (on the Phase 2 map the Hero walks while a key is held).
"""

import pytest

import game
import phase2
from helpers import frames, hold_keys, start_game

STEP = 12            # frames to walk one square: the Hero walks 5 squares a second (phase2/smooth.py)


@pytest.fixture(autouse=True)
def own_save_file(monkeypatch, tmp_path):
    path = tmp_path / "phase2_save.json"
    monkeypatch.setenv("ADVENTURE_SAVE_FILE", str(path))
    return path


def new_phase2_app(seed=1, story=False, monsters=False):
    """Pick Phase 2 on the title screen and start it."""
    app = game.App("Hero", seed=seed, sound=False)
    app.mode = "phase2"
    start_game(app, story=story, monsters=monsters)
    assert phase2.is_phase2(app.game)
    return app


def hold(app, monkeypatch, key, how_many=STEP):
    """Hold a move key down for some frames (STEP frames is one square), then let go."""
    held = hold_keys(monkeypatch)
    held.add(key)
    frames(app, how_many)
    held.clear()
