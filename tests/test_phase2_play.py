"""
SMOKE TEST for Phase 2: a game starts on the big map and plays for a few hundred frames,
down a cave and back, through the Portal, to the castle and the Shadow King, all with the classic parts.
"""

import pygame

import game
import phase2
from helpers import frames, hold_keys, ok, press, walk_into_a_mine
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)
from test_game_starts import WALKING, answer_whatever_is_open


def test_phase_2_starts_and_plays_for_a_few_hundred_frames(monkeypatch):
    app = game.App("Hero", seed=3, sound=False)
    press(app, pygame.K_RIGHT)
    press(app, pygame.K_RETURN)
    for _ in range(40):
        if app.state == "play":
            break
        press(app, pygame.K_SPACE)
        frames(app, 5)
    ok(app.state == "play" and phase2.is_phase2(app.game), "after the story cards, you're on the Phase 2 map")
    held = hold_keys(monkeypatch)                   # on the Phase 2 map he walks while a key is held
    for i in range(400):
        if i % 8 == 0:
            held.clear()
            if app.state == "play":
                held.add(WALKING[(i // 8) % len(WALKING)])
                press(app, WALKING[(i // 8) % len(WALKING)])
            else:
                answer_whatever_is_open(app)
        frames(app)
    ok(app.running and app.game.turn > 1, "still running after walking around")


def test_down_a_cave_and_back_out():
    app = new_phase2_app()
    cave = walk_into_a_mine(app)
    ok(cave is not None and app.state == "cave", "into a cave under a Mine")
    frames(app, 120)
    app.game.cave.result = "exit"
    frames(app, 60)
    ok(app.game.cave is None and app.state == "play", "and back out onto the big map")


def test_through_the_portal_to_the_castle_and_the_king():
    app = game.App("Hero", seed=1, sound=False, castle=True, phase2_mode="phase2")
    ok(phase2.is_phase2(app.game) and app.game.world == 2, "--phase2 --castle: Nightfall Hollow, by the castle")
    frames(app, 60)
    app = game.App("Hero", seed=1, sound=False, throne=True, phase2_mode="phase2")
    world = app.game
    ok(world.cave and world.cave.is_throne_room, "--phase2 --throne: in the throne room")
    frames(app, 200)
    ok(app.running, "the Shadow King fight runs in Phase 2")
