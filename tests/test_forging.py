"""The forge game: 3 hammer strikes make a Great, normal or Cracked sword. Chests hide Great swords too,
and a sword warns you when it's down to its last few hits."""

import random

import pygame

import game
import rules
from helpers import frames, new_app, new_world, ok, press


def test_strike_zones():
    zone = 0.3
    gold = zone + (rules.FORGE_GREEN - rules.FORGE_GOLD) / 2
    ok(rules.strike_grade(gold + rules.FORGE_GOLD / 2, zone) == "perfect", "the middle of the gold zone is Perfect")
    ok(rules.strike_grade(zone + 0.01, zone) == "good", "the green zone outside the gold is Good")
    ok(rules.strike_grade(zone + rules.FORGE_GREEN - 0.01, zone) == "good", "both sides of the gold are Good")
    ok(rules.strike_grade(zone - 0.01, zone) == "miss" and rules.strike_grade(zone + rules.FORGE_GREEN + 0.01, zone) == "miss",
       "outside the green zone is a Miss")
    ok(rules.FORGE_GOLD == 0.08 and rules.FORGE_GREEN == 0.24, "gold is 8% of the bar, green 24%")


def test_sword_quality():
    ok(rules.sword_quality(["perfect", "perfect", "good"]) == "great", "2 Perfect, no Miss: Great")
    ok(rules.sword_quality(["perfect", "perfect", "perfect"]) == "great", "3 Perfect: Great")
    ok(rules.sword_quality(["perfect", "perfect", "miss"]) == "normal", "a Miss spoils a Great sword")
    ok(rules.sword_quality(["miss", "good", "miss"]) == "cracked", "2 Misses: Cracked")
    ok(rules.sword_quality(["good", "good", "good"]) == "normal", "all Good: a normal sword")
    ok(rules.make_sword("great").durability == 24 and rules.make_sword().durability == 16
       and rules.make_sword("cracked").durability == 4, "Great lasts 24 hits, normal 16, Cracked 4")


def test_great_sword_hits_harder():
    p = new_world().player
    p.swords = [rules.make_sword()]
    normal = p.damage_bonus
    p.swords = [rules.make_sword("great")]
    ok(p.damage_bonus == normal + rules.GREAT_SWORD_BONUS, "the Great sword in your hand hits +1 harder")
    ok(p.strength_bonus == normal, "but it doesn't make arrows or Sunfang stronger")


def test_three_strikes_get_faster_and_forge_a_sword():
    forge = game.Forge(random.Random(1))
    speeds = []
    for grade in ("perfect", "perfect", "good"):
        while not forge.ready:
            forge.update(0.05)
        speeds.append(forge.speed)
        forge.pos = forge.gold_x + 0.01 if grade == "perfect" else forge.zone_x + 0.01
        ok(forge.strike() == grade, "the strike is %s" % grade)
        ok(forge.strike() is None, "you can't strike again straight away")
    ok(speeds[1] == speeds[0] * rules.FORGE_SPEEDUP and abs(speeds[2] - speeds[0] * rules.FORGE_SPEEDUP ** 2) < 1e-9,
       "the marker is 15% faster after each strike")
    ok(forge.finished and forge.quality == "great" and not forge.done, "3 strikes and it's a Great sword")
    forge.update(forge.END_TIME + 0.1)
    ok(forge.done, "after a moment the forge closes")
    world = new_world()
    world.player.swords = []
    world.finish_forge(forge.strikes)
    ok(len(world.player.swords) == 1 and world.player.swords[0].quality == "great", "you get the Great sword")
    world.finish_forge(["miss", "miss", "good"])
    ok(world.player.swords[-1].quality == "cracked" and world.player.swords[-1].durability == 4,
       "even a bad forge makes a sword - a Cracked one")


def test_forging_fills_a_sword_slot():
    world = new_world()
    world.player.pos = next(spot for spot in world.mainland if world.map[spot[0]][spot[1]] == "F")
    world.player.swords = [rules.make_sword() for _ in range(rules.MAX_SWORDS - 1)]
    ok(world.forge_problem() is None, "a free slot: you can forge (for free, in the forest)")
    world.finish_forge(["good"] * 3)
    ok(len(world.player.swords) == rules.MAX_SWORDS and "carry" in (world.forge_problem() or ""),
       "all %d slots full: no more forging until a sword breaks" % rules.MAX_SWORDS)


def test_about_one_in_three_chest_swords_is_great():
    world = new_world(seed=4)
    great = 0
    for _ in range(600):
        world.player.swords = []
        world.give_loot("sword", 5)
        great += world.player.swords[0].quality == "great"
    ok(150 < great < 250, "about 1 in 3 chest swords is Great (%d of 600)" % great)


def test_a_sword_warns_you_at_three_hits_left():
    world = new_world()
    sword = rules.make_sword()
    world.player.swords = [sword]
    sounds = lambda: [e["name"] for e in world.effects if e["type"] == "sound"]
    while sword.durability > rules.LOW_USES + 1:
        sword.use()
    world.check_chipped_swords()
    ok("chip" not in sounds() and not sword.low, "no warning yet with 4 hits left")
    sword.use()
    world.check_chipped_swords()
    ok("chip" in sounds() and sword.low and "chipped" in world.messages[-1][0],
       "at 3 hits left: a chip sound and a message")
    world.effects.clear()
    world.check_chipped_swords()
    ok("chip" not in sounds(), "it warns you only once")


def test_forge_game_in_the_app_and_the_panel():
    app = new_app()
    world, p = app.game, app.game.player
    p.pos = next(spot for spot in world.mainland if world.map[spot[0]][spot[1]] == "F")
    p.swords = []
    app.start_forge("play")
    ok(app.state == "forge", "the forge opens in the forest")
    for _ in range(rules.FORGE_STRIKES):
        while not app.forge.ready:
            frames(app)
        app.forge.pos = app.forge.gold_x + 0.01
        press(app, pygame.K_SPACE, " ")
    frames(app, 150)
    ok(app.state == "play" and p.swords and p.swords[0].quality == "great", "3 Perfect strikes: a Great sword")

    def panel_pixels(sword, color):
        p.swords = [sword]
        app.draw()
        panel = app.screen.subsurface((game.VIEW_W, 0, game.PANEL_W, game.HEIGHT))
        return sum(panel.get_at((x, y))[:3] == color for x in range(0, game.PANEL_W, 1) for y in range(0, 400))

    normal, great, cracked = rules.make_sword(), rules.make_sword("great"), rules.make_sword("cracked")
    ok(panel_pixels(great, game.YELLOW) > panel_pixels(normal, game.YELLOW), "the panel shows a Great sword in gold")
    ok(panel_pixels(cracked, game.RED) > panel_pixels(normal, game.RED), "and a Cracked one in red")
    while normal.durability > rules.LOW_USES:
        normal.use()
    ok(panel_pixels(normal, game.RED) > panel_pixels(rules.make_sword(), game.RED), "a sword's pips turn red at 3 hits left")
