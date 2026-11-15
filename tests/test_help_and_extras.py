"""
The help screen (press H), eating in a cave, skipping the story, the Ember Skull,
and the music.
"""

import pygame

import caves
import game
import rules
import sprites
import story
from helpers import frames, hold_keys, new_app, new_world, ok, press, walk_into_a_mine


# ===========================================================================
# The help screen (H), in a cave
# ===========================================================================

def in_a_cave(monkeypatch):
    """A new game, standing in the cave under the Mine nearest home (no keys held down)."""
    hold_keys(monkeypatch)
    app = new_app()
    walk_into_a_mine(app)
    ok(app.state == "cave", "walked into a Mine: in the cave (%s)" % app.state)
    return app


def read_the_help_screen(app, monkeypatch):
    """Draw the help screen once, and write down every line of words and every line it draws.
    Returns a list like [("words", text, (x, y), size), ("line", start, end), ...] in drawing order."""
    drawn = []
    draw_words, draw_line = app.text, pygame.draw.line

    def spy_words(surf, text, pos, size=24, *rest, **kw):
        drawn.append(("words", text, pos, size))
        return draw_words(surf, text, pos, size, *rest, **kw)

    def spy_line(surf, color, start, end, *rest, **kw):
        drawn.append(("line", tuple(start), tuple(end)))
        return draw_line(surf, color, start, end, *rest, **kw)

    with monkeypatch.context() as patch:
        patch.setattr(app, "text", spy_words)
        patch.setattr(pygame.draw, "line", spy_line)
        frames(app, 1)
    # only what the help screen drew: everything from its "How to Play" title on
    title = next(i for i, thing in enumerate(drawn) if thing[0] == "words" and thing[1] == "How to Play")
    return drawn[title:]


def test_h_opens_the_help_screen_in_a_cave_and_any_key_closes_it(monkeypatch):
    app = in_a_cave(monkeypatch)
    press(app, pygame.K_h)
    ok(app.state == "help", "H opens the help screen in a cave")
    press(app, pygame.K_SPACE)
    ok(app.state == "cave" and app.game.cave is not None, "any key goes back to the cave")


def test_the_help_screen_explains_the_craft_menu(monkeypatch):
    app = in_a_cave(monkeypatch)
    press(app, pygame.K_h)
    words = [thing[1] for thing in read_the_help_screen(app, monkeypatch) if thing[0] == "words"]
    ok(any("Craft menu" in line for line in words), "the help screen tells you about the Craft menu")
    ok(any("UP/DOWN picks" in line and "ENTER crafts" in line and "click" in line for line in words),
       "it says UP/DOWN picks, ENTER (or a click) crafts")
    ok(not any("Press 1" in line or "1-6" in line for line in words), "no more 'press 1-6' on the help screen")


def test_the_help_screens_left_column_fits(monkeypatch):
    app = in_a_cave(monkeypatch)
    press(app, pygame.K_h)
    drawn = read_the_help_screen(app, monkeypatch)
    words = [thing for thing in drawn if thing[0] == "words"]
    left_x = words[1][2][0]                                  # the first line under the title starts the left column
    left = [(text, pos, size) for _, text, pos, size in words if pos[0] == left_x]
    divider_x = next(start[0] for kind, start, end in (t for t in drawn if t[0] == "line")
                     if start[0] == end[0] and start[0] > left_x)      # the line down the middle
    too_wide = [text for text, (x, y), size in left if x + app.font(size).size(text)[0] > divider_x - 4]
    ok(not too_wide, "every left-column line fits before the middle divider %r" % too_wide)
    press_any = next(pos[1] for _, text, pos, size in words if text.startswith("Press any key"))
    lowest = max(y + size for text, (x, y), size in left)
    ok(lowest <= press_any, "the left column ends above 'Press any key' (%d vs %d)" % (lowest, press_any))


def test_e_eats_in_a_cave(monkeypatch):
    app = in_a_cave(monkeypatch)
    p = app.game.player
    p.food, p.health = 2, p.max_health - 10
    health = p.health
    press(app, pygame.K_e)
    ok(p.food == 1 and p.health > health, "E eats in a cave: health %d, food %d" % (p.health, p.food))


# ===========================================================================
# The story cards at the start
# ===========================================================================

def test_s_skips_the_story_and_playing_again_has_no_intro():
    app = new_app(seed=5, story=True)
    frames(app, 1)
    ok(app.state == "story" and len(app.game.story) == len(story.INTRO),
       "a new game starts with the %d intro cards" % len(story.INTRO))
    press(app, pygame.K_s)
    ok(app.state == "play" and not app.game.story, "S skips the whole story")
    app.game.player.health = 0
    frames(app, 200)
    press(app, pygame.K_RETURN)
    ok(app.state == "play" and not app.game.story, "play again after dying: no intro this time")


# ===========================================================================
# The Ember Skull (it took the Creeper's place)
# ===========================================================================

def test_the_ember_skull_took_the_creepers_place():
    ok("Ember Skull" in sprites.MONSTER_ART and "Creeper" not in sprites.MONSTER_ART
       and "Creeper" not in rules.MONSTER_TYPES, "the Creeper is gone; the Ember Skull is in its place")
    ok(caves.CAVE_MONSTERS["c"] == "Ember Skull" and rules.MONSTER_TYPES["Ember Skull"]["special"] == "explodes",
       "c in a cave is an Ember Skull, and it still explodes")
    ok(rules.a_or_an("Ember Skull") == "An Ember Skull", "the log says 'An Ember Skull attacks!'")


def test_a_deadly_blast_is_game_over_even_if_it_finishes_a_quest():
    world = new_world()
    world.monster_quest.progress = world.monster_quest.goal_count - 1     # one more monster finishes the quest
    p = world.player
    p.health, p.swords = 3, []
    skull = rules.Monster("Ember Skull", p.pos)
    skull.health, skull.damage = 999, (9, 9)
    world.monsters = [skull]
    world.start_battle(skull)
    world.battle.fuse = 1                       # it's about to blow up!
    for _ in range(5):
        if world.battle.over:
            break
        world.battle_action("attack")
    ok(p.is_alive and not world.over and p.lives == rules.START_LIVES - 1 and world.battle.result == "lost",
       "a blast that defeats you costs a life, even if it finishes a quest")


# ===========================================================================
# Music
# ===========================================================================

def test_every_voice_in_a_tune_is_the_same_length():
    def notes(line):
        return len(line.replace("|", " ").split())

    lengths = {name: {notes(voice[2]) for voice in tune["voices"]} | ({notes(tune["drums"])} if tune.get("drums") else set())
               for name, tune in game.TUNES.items()}
    uneven = [name for name, sizes in lengths.items() if len(sizes) != 1]
    ok(not uneven, "every voice in every tune is the same length, so they loop together %r" % uneven)


def test_there_is_a_tune_for_every_place():
    places = {"home", "nightfall", "castle"} | set(caves.THEMES)
    ok(places <= set(game.TUNES), "a tune for home, each cave look, Nightfall Hollow and the castle (missing: %s)"
       % sorted(places - set(game.TUNES)))


def test_the_music_matches_where_you_are(monkeypatch):
    hold_keys(monkeypatch)
    app = new_app(seed=5)
    ok(app.tune_here() == "home", "home world: the home tune")
    walk_into_a_mine(app)
    ok(app.game.cave is not None and app.tune_here() == app.game.cave.theme,
       "in a cave: that cave's tune (%s)" % app.tune_here())
