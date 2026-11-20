"""
THE WORLD GROWS DARK (phase2/gloom.py): in Phase 2 the Shadow King pulls the light out of the world, very
slowly. The dusk over the map and the little map gets thicker (never past a cap), every Light Stone pushes
it back, the game says so once, and it's all saved. Classic has none of it.
"""

import json

import pygame

import game
import phase2
import rules
from helpers import DT, frames, ok, start_game
from phase2 import Phase2Game, draw_theme, gloom, quests, save, theme
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)

MINUTE = 60


def world(seed=1):
    game = Phase2Game("Hero", seed=seed)
    game.monsters = []
    game.story.clear()
    return game


def get_a_light_stone(game, qid="main_home"):
    quests.start(game, qid)
    ok(quests.finish(game, qid), "the chapter is done: you get its Light Stone")


def said(game, words):
    return [m[0] for m in game.messages if words in m[0]]


def middle_of_map(app):
    surf = pygame.Surface((400, 300))
    app.draw_world(surf)
    return tuple(surf.get_at((200, 150)))[:3]


def little_map(app):
    """A spot on the little map (as the panel draws it), on a red screen."""
    app.screen.fill((255, 0, 0))
    ok(phase2.draw_minimap(app, 100, 100, 300, 400, show_view=False), "the little map is drawn")
    return tuple(app.screen.get_at((120, 140)))[:3]


# ===========================================================================
# How fast, and how far
# ===========================================================================

def test_a_new_game_starts_with_the_same_dusk_as_before():
    game = world()
    ok(game.gloom == 0.0 and not game.gloom_told, "no light is gone yet")
    ok(theme.dusk_alpha(game) == theme.DUSK_ALPHA == 96, "the map's dusk is the one it always had")
    ok(theme.minimap_alpha(game) == 0, "and the little map is as bright as ever")


def test_the_light_fades_very_slowly():
    game = world()
    gloom.pass_time(game, MINUTE)
    ok(abs(game.gloom - 1 / gloom.FULL_MINUTES) < 1e-9, "a minute of play: one minute's worth of dark")
    ok(theme.dusk_alpha(game) - theme.DUSK_ALPHA <= 1, "too little to see: a minute changes the dusk by 1 at most")
    ok(gloom.FULL_MINUTES >= 45, "it takes most of an hour (or more) to get as dark as it gets")
    gloom.pass_time(game, (gloom.FULL_MINUTES / 2 - 1) * MINUTE)
    ok(abs(game.gloom - 0.5) < 1e-9, "half the time: half way")
    ok(theme.dusk_alpha(game) == round((theme.DUSK_ALPHA + theme.DUSK_DARKEST) / 2), "and the dusk is half way too")
    before = theme.dusk_alpha(game)
    gloom.pass_time(game, 10 * MINUTE)
    ok(theme.dusk_alpha(game) > before, "it keeps getting darker")


def test_it_fades_as_you_play_in_the_real_game():
    app = new_phase2_app()
    frames(app, 60)
    ok(abs(app.game.gloom - 60 * DT / (gloom.FULL_MINUTES * MINUTE)) < 1e-9, "a second of play is a second of fading")
    now = app.game.gloom
    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p, mod=0, unicode="p"))
    ok(phase2.paused(app), "P pauses")
    frames(app, 60)
    ok(app.game.gloom == now, "the pause menu stops it, like the clock")


def test_there_is_a_cap_so_the_map_is_always_easy_to_see():
    game = world()
    gloom.pass_time(game, 10 * 60 * MINUTE)                 # ten hours!
    ok(game.gloom == 1.0, "the dark stops growing at 1.0")
    ok(theme.dusk_alpha(game) == theme.DUSK_DARKEST, "the dusk is as thick as it ever gets")
    ok(theme.DUSK_ALPHA < theme.DUSK_DARKEST <= 160, "which is darker than at the start, but far from black (255)")
    ok(0 < theme.minimap_alpha(game) <= 110, "the little map too")
    game.gloom = 99                                         # (a save somebody changed by hand)
    ok(theme.dusk_alpha(game) == theme.DUSK_DARKEST, "never thicker than the cap, whatever the number says")
    game.gloom = -5
    ok(theme.dusk_alpha(game) == theme.DUSK_ALPHA and theme.minimap_alpha(game) == 0, "and never thinner than the start")


# ===========================================================================
# The Light Stones, the hint, and the end
# ===========================================================================

def test_every_light_stone_pushes_the_dark_back():
    game = world()
    game.gloom = 0.8
    before = theme.dusk_alpha(game)
    get_a_light_stone(game)
    ok(abs(game.gloom - (0.8 - gloom.STONE_PUSH)) < 1e-9, "the Dawn Stone pushes the dark back")
    ok(theme.dusk_alpha(game) < before, "so the map is brighter")
    ok(said(game, "The Dawn Stone shines, and the dark pulls back"), "and the game says so")
    ok(0 < gloom.STONE_PUSH < 0.5, "a bit, not all of it: the Shadow King keeps pulling")
    gloom.pass_time(game, MINUTE)
    ok(game.gloom > 0.8 - gloom.STONE_PUSH, "(it goes on getting darker afterwards)")


def test_a_light_stone_never_makes_it_brighter_than_the_start():
    game = world()
    game.gloom = gloom.STONE_PUSH / 2
    get_a_light_stone(game)
    ok(game.gloom == 0.0 and theme.dusk_alpha(game) == theme.DUSK_ALPHA, "the dark is all pushed back, no further")
    fresh = world()
    get_a_light_stone(fresh)
    ok(fresh.gloom == 0.0 and not said(fresh, "the dark pulls back"), "no dark yet: nothing to push back, nothing said")


def test_the_game_says_once_when_it_gets_darker():
    game = world()
    gloom.pass_time(game, (gloom.NOTICE * gloom.FULL_MINUTES - 1) * MINUTE)
    ok(not said(game, "getting darker"), "not yet: you can't see it yet")
    gloom.pass_time(game, 2 * MINUTE)
    ok(len(said(game, "getting darker")) == 1 and game.gloom_told, "now it's darker: the game says why")
    ok("Shadow King" in said(game, "getting darker")[0] and "Light Stone" in said(game, "getting darker")[0],
       "it's the Shadow King, and the Light Stones push it back")
    gloom.pass_time(game, 20 * MINUTE)
    get_a_light_stone(game)
    gloom.pass_time(game, 20 * MINUTE)
    ok(len(said(game, "getting darker")) == 1, "only once")


def test_the_hint_waits_until_you_are_on_the_map():
    game = world()
    game.cave = object()                                    # down in a cave: the sky isn't there to see
    gloom.pass_time(game, gloom.FULL_MINUTES * MINUTE)
    ok(game.gloom == 1.0 and not said(game, "getting darker"), "darker, but nothing said in a cave")
    game.cave = None
    gloom.pass_time(game, 1)
    ok(said(game, "getting darker"), "back on the map: now it says so")


def test_beating_the_shadow_king_brings_the_light_back():
    game = world()
    game.gloom = 0.9
    game.king_quest = rules.Quest("Defeat the Shadow King", 1)
    game.beat_the_king()
    ok(game.king_beaten and game.gloom == 0.0, "the light he took comes back")
    gloom.pass_time(game, 60 * MINUTE)
    ok(game.gloom == 0.0 and theme.dusk_alpha(game) == theme.DUSK_ALPHA, "and it stays: nobody pulls it away now")


# ===========================================================================
# Saving
# ===========================================================================

def test_saving_and_loading_keeps_how_dark_it_is():
    game = world()
    gloom.pass_time(game, 40 * MINUTE)
    dark, alpha = game.gloom, theme.dusk_alpha(game)
    ok(game.gloom_told and save.save_game(game), "a dark game saves")
    back = save.load_game()
    ok(back.gloom == dark and back.gloom_told and theme.dusk_alpha(back) == alpha, "it's just as dark when you load it")
    gloom.pass_time(back, MINUTE)
    ok(back.gloom > dark and len(said(back, "getting darker")) <= 1, "it goes on from there, and doesn't say it twice")


def test_a_save_from_before_the_dark_still_loads(own_save_file):
    ok(save.save_game(world()), "a brand new game saves")
    data = json.loads(own_save_file.read_text())
    fields = dict((key, value) for key, value in data["game"]["$dict"])
    ok("gloom" not in fields and "gloom_told" not in fields, "(a game with no dark yet has nothing extra in its save)")
    back = save.load_game()
    ok(back.gloom == 0.0 and not back.gloom_told and theme.dusk_alpha(back) == theme.DUSK_ALPHA, "an old save starts with no dark")
    gloom.pass_time(back, MINUTE)
    ok(back.gloom > 0, "and then it grows")


# ===========================================================================
# What you see
# ===========================================================================

def test_the_map_and_the_little_map_get_darker():
    app = new_phase2_app()
    frames(app, 1)
    app.game.gloom = 0.0
    map_before, little_before = middle_of_map(app), little_map(app)
    ok(little_before != (255, 0, 0), "(the spot is on the little map)")
    app.game.gloom = 1.0
    map_dark, little_dark = middle_of_map(app), little_map(app)
    ok(sum(map_dark) < sum(map_before), "the map is darker when the light is gone")
    ok(sum(little_dark) < sum(little_before), "and so is the little map")
    ok(map_dark != theme.DUSK and sum(map_dark) > 0.5 * sum(map_before), "but you can still see the ground well")
    ok(sum(little_dark) > 0.5 * sum(little_before), "and the little map")
    app.game.gloom = 0.0
    ok(middle_of_map(app) == map_before and little_map(app) == little_before, "push it all back: bright again")


def test_what_is_marked_on_the_little_map_stays_bright():
    app = new_phase2_app()
    frames(app, 1)
    app.game.gloom = 1.0
    drawn = []
    real = draw_theme.draw_map_dusk
    draw_theme.draw_map_dusk = lambda a, rect: (drawn.append(rect.copy()), real(a, rect))[1]
    try:
        app.time = 0.0                                      # (you blink on the map: now you're shown)
        app.screen.fill((255, 0, 0))
        phase2.draw_minimap(app, 100, 100, 300, 400, show_view=False)
    finally:
        draw_theme.draw_map_dusk = real
    ok(len(drawn) == 1, "the dusk is drawn over the little map once")
    rect, pos = drawn[0], app.game.player.pos
    scale = rect.w / app.game.cols
    spot = (rect.x + int((pos[1] + 0.5) * scale), rect.y + int((pos[0] + 0.5) * scale))
    ok(tuple(app.screen.get_at(spot))[:3] == game.YELLOW, "your yellow dot is on top of the dusk, as bright as ever")


def test_the_real_game_draws_the_dusk_on_its_little_map(monkeypatch):
    app = new_phase2_app()
    drawn = []
    real = draw_theme.draw_map_dusk
    monkeypatch.setattr(draw_theme, "draw_map_dusk", lambda a, rect: (drawn.append(rect.copy()), real(a, rect))[1])
    app.game.gloom = 1.0
    frames(app, 1)
    ok(len(drawn) == 1 and drawn[0].y >= game.VIEW_H, "one frame of the real game: the dusk is on the little map under the map")
    spot = drawn[0].move(3, 3).topleft
    dark = tuple(app.screen.get_at(spot))[:3]
    app.game.gloom = 0.0
    frames(app, 1)
    ok(sum(dark) < sum(tuple(app.screen.get_at(spot))[:3]), "and it's darker there than with all the light")


def test_nightfall_hollow_keeps_its_own_dark():
    app = new_phase2_app()
    frames(app, 1)
    app.game.gloom = 1.0
    app.game.world = 2
    surf = pygame.Surface((400, 300))
    surf.fill((200, 200, 200))
    phase2.draw_dusk(app, surf)
    ok(tuple(surf.get_at((5, 5)))[:3] == (200, 200, 200), "no dusk is drawn in Nightfall Hollow")


# ===========================================================================
# Classic
# ===========================================================================

def test_classic_never_grows_dark(monkeypatch):
    app = game.App("Hero", seed=1, sound=False)
    start_game(app)
    frames(app, 2)
    moment, before = app.time, middle_of_map(app)
    called = []
    monkeypatch.setattr(gloom, "pass_time", lambda *a: called.append(a))
    monkeypatch.setattr(draw_theme, "draw_map_dusk", lambda *a: called.append(a))
    monkeypatch.setattr(draw_theme, "draw_dusk", lambda *a: called.append(a))
    frames(app, 120)
    app.draw_minimap(100, 100, 300, 400)
    ok(type(app.game) is rules.Game and not called, "Classic never asks about the dark")
    ok(not hasattr(app.game, "gloom") and not hasattr(app.game, "gloom_told"), "a Classic game has no dark to keep")
    ok(theme.dusk_alpha(app.game) == theme.DUSK_ALPHA, "(the knob says 'the start' for a game with no dark)")
    monkeypatch.undo()
    app.time = moment                                       # the same moment as before (water and grass move)
    ok(middle_of_map(app) == before, "and its map looks just the same")
