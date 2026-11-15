"""In a fight on the map, mashing A doesn't work: there's a short pause at the start and after every turn."""

import pygame

import game
import rules
from helpers import DT, frames, new_app, ok, press

PAUSE = int(game.BATTLE_PAUSE / DT) + 1               # frames, a little more than the pause


def a_fight():
    """A fight with a tough Zombie, and a list of every turn you really took."""
    app = new_app()
    world = app.game
    monster = rules.Monster("Zombie", world.neighbors(world.player.pos)[0])
    monster.health = 999                               # it won't die, so the fight keeps going
    world.player.health = world.player.max_health = 999   # and neither will you
    world.monsters.append(monster)
    world.start_battle(monster)
    frames(app, 1)
    ok(app.state == "battle", "a fight starts")
    turns = []
    world.battle_action = turns.append                 # count the turns instead of playing them
    return app, turns


def test_a_does_nothing_right_when_the_fight_starts():
    app, turns = a_fight()
    press(app, pygame.K_a)
    ok(turns == [] and app.lunge == 0, "A at once does nothing: the fight just started")
    frames(app, PAUSE)
    press(app, pygame.K_a)
    ok(turns == ["attack"], "after the short pause, A attacks")


def test_mashing_a_only_attacks_once_per_pause():
    app, turns = a_fight()
    frames(app, PAUSE)
    for _ in range(PAUSE - 2):
        press(app, pygame.K_a)                         # mash, mash, mash (one press every frame)
    ok(turns == ["attack"], "mashing A: only the first press attacks, the rest are too soon")
    frames(app, PAUSE)
    press(app, pygame.K_r)
    ok(turns == ["attack", "run"], "after the pause, the next turn works (R, E and the buttons wait too)")
