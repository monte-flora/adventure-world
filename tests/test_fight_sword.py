"""In a fight on the map, you hold your sword (or Sunfang) - and swing it when you attack."""

import pygame

import game
import rules
from helpers import ok


def fight_picture(app, lunge=0.0):
    app.lunge = lunge
    app.screen.fill((0, 0, 0))
    app.draw_battle()
    return pygame.image.tobytes(app.screen, "RGB")


def test_you_hold_your_sword_in_a_map_fight():
    app = game.App("Hero", seed=3, sound=False)
    world = app.game
    world.start_battle(rules.Monster("Zombie", world.player.pos))
    app.state = "battle"
    app.time = 0.0
    with_sword = fight_picture(app)
    swinging = fight_picture(app, 0.15)
    world.player.swords = []
    without = fight_picture(app)
    ok(with_sword != without, "with a sword, you hold it in the fight; without one, your hands are empty")
    world.player.sunfang = True
    ok(fight_picture(app) not in (with_sword, without), "after the forge you hold Sunfang instead")
    ok(swinging != with_sword, "when you attack, the sword swings")
