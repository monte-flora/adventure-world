"""
PHASE 2's TEEN LOOK (phase2/theme.py): a cooler name in one place, darker boxes and panel, a dusk over the
map, a darker map tune, and a fuller story. Classic looks and sounds just like before.
"""

import json
import os

import pygame

import game
import phase2
import rules
from conftest import GAME_FOLDER
from helpers import frames, ok, start_game
from phase2 import main_quest, theme
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)


def caption_after(app):
    return pygame.display.get_caption()[0]


def test_the_name_is_in_one_place_and_on_the_title_and_window():
    ok(theme.GAME_NAME == "Shadowfall" and theme.GAME_NAME in theme.NAME_IDEAS and len(theme.NAME_IDEAS) == 3,
       "the name, and the 3 we thought of, live in phase2/theme.py")
    app = game.App("Hero", seed=1, sound=False)
    app.mode = "phase2"
    said = []
    real = app.text
    app.text = lambda surf, words, *a, **k: (said.append(words), real(surf, words, *a, **k))[1]
    frames(app, 2)
    ok(theme.GAME_NAME.upper() in said and "Adventure World" not in said, "Phase 2 picked: its name on the title")
    start_game(app)
    ok(caption_after(app) == theme.GAME_NAME, "the window says it too")


def test_classic_keeps_its_own_name():
    app = game.App("Hero", seed=1, sound=False)
    said = []
    real = app.text
    app.text = lambda surf, words, *a, **k: (said.append(words), real(surf, words, *a, **k))[1]
    frames(app, 2)
    ok("Adventure World" in said and theme.GAME_NAME.upper() not in said, "Classic's title is unchanged")
    start_game(app)
    ok(type(app.game) is rules.Game and caption_after(app) == theme.CLASSIC_NAME, "and so is its window")


def test_renaming_changes_the_story_too(monkeypatch):
    ok(any(theme.GAME_NAME in text for _, text, _ in main_quest.story("opening")), "the opening says the name")
    monkeypatch.setattr(theme, "GAME_NAME", "Test Name")
    ok(any("Test Name" in text for _, text, _ in main_quest.story("opening")), "change it in one place: the story follows")


def test_phase_2_boxes_are_darker_and_classic_boxes_are_not():
    classic = game.App("Hero", seed=1, sound=False)
    start_game(classic)
    p2 = new_phase2_app()
    for name, before in (("box", (38, 34, 54)), ("key", (70, 74, 102)), ("key_edge", (124, 130, 170))):
        ok(phase2.color(classic, name, before) == before, "Classic keeps its %s colour" % name)
        ok(phase2.color(p2, name, before) == theme.COLORS[name] != before, "Phase 2 has its own %s colour" % name)
    for app, want in ((classic, (38, 34, 54)), (p2, theme.BOX_BG)):
        app.screen.fill((255, 0, 0))
        box = pygame.Rect(100, 100, 300, 200)
        app.panel_box(box)
        ok(tuple(app.screen.get_at(box.center))[:3] == want, "the box is filled with %s" % (want,))


def middle_of_map(app):
    surf = pygame.Surface((400, 300))
    app.draw_world(surf)
    return tuple(surf.get_at((200, 150)))[:3]


def test_the_dusk_is_only_over_the_phase_2_map(monkeypatch):
    p2 = new_phase2_app()
    frames(p2, 1)
    with_dusk = middle_of_map(p2)
    monkeypatch.setattr(theme, "dusk_alpha", lambda game: 0)
    without = middle_of_map(p2)
    ok(with_dusk != without and sum(with_dusk) < sum(without), "the dusk makes the Phase 2 map darker")
    monkeypatch.setattr(theme, "dusk_alpha", lambda game: 255)
    ok(middle_of_map(p2) == theme.DUSK, "dusk_alpha is the one knob for how dark it is (for later)")
    classic = game.App("Hero", seed=1, sound=False)
    start_game(classic)
    frames(classic, 1)
    middle_of_map(classic)
    ok(not hasattr(classic, "_phase2_dusk"), "no dusk in Classic")


def test_phase_2_map_has_its_own_tune_and_classic_keeps_home():
    ok(theme.MAP_TUNE in game.TUNES, "the dusk tune is one of the game's tunes")
    p2 = new_phase2_app()
    frames(p2, 1)
    ok(p2.tune_here() == theme.MAP_TUNE, "the Phase 2 map plays the dusk tune")
    classic = game.App("Hero", seed=1, sound=False)
    start_game(classic)
    frames(classic, 1)
    ok(classic.tune_here() == "home", "Classic's map still plays home")


def test_the_story_has_a_backstory_and_fits_on_its_cards():
    titles = [card[0] for card in main_quest.story("opening")]
    for title in ("Two worlds", "The Shadow King", "A hundred cold years", "The seven Light Stones", "Rosa the Guide"):
        ok(title in titles, "the opening has '%s'" % title)
    ok(titles[-1] == "Rosa the Guide", "and it ends by sending you to Rosa")
    ending = [card[0] for card in main_quest.story("ending")]
    ok(ending[0] == "One sun for two worlds" and ending[-1] == "The adventure goes on", "the ending tells what happens")
    app = new_phase2_app()
    data = json.load(open(os.path.join(GAME_FOLDER, "phase2", "data", "main_quest.json")))
    pictures = {"king", "monsters", "sunfang", "portal", "hollow", "castle", "light"}
    for name, cards in data["story"].items():
        if isinstance(cards, str):
            continue
        for title, text, picture in main_quest.story(name, relic="the Dawn Stone", count=1):
            ok(picture in pictures, "%s has a picture" % title)
            words = text.replace("{name}", "Hero")
            ok(len(app.wrap(words, 30, 940 - 120)) <= 6, "'%s' fits on its card" % title)
            ok("{" not in words, "'%s' has every word filled in" % title)


def test_people_tell_the_lore_in_their_last_lines():
    data = json.load(open(os.path.join(GAME_FOLDER, "phase2", "data", "people.json")))
    people = {p["id"]: p for p in data["people"]}
    for pid, word in (("elder_oona", "Portal"), ("sir_rowan", "Light Stones"), ("finn", "Portal Island")):
        last = people[pid]["talk"]["start"][-1]
        ok("if" not in last and any(word in line for line in last["say"]), "%s tells some of the old story" % pid)
