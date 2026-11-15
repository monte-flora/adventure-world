"""
Takes the screenshots in this folder: every Phase 2 screen, one after the other, to check they all look
like one game (the same boxes, colors, key hints and words). No window opens (the "dummy" video driver).
From the game's folder:

    pixi run python docs/cohesion/take_screenshots.py

(or any Python that has pygame). The pictures are written next to this file.
Give it some names to take only those scenes:  ... take_screenshots.py shop pages
"""
import os
import sys
import tempfile
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["ADVENTURE_SETTINGS_FILE"] = os.path.join(tempfile.mkdtemp(), "settings.json")     # never your real settings
os.environ["ADVENTURE_SAVE_FILE"] = os.path.join(tempfile.mkdtemp(), "save.json")             # or your real saves
OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(OUT))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
import pygame
import tutorial
tutorial.START_WITH_TIPS = False
import game
import rules
from helpers import frames, press, start_game, walk_into_a_mine
from phase2 import main_quest, people, quests, save
from phase2.world import Phase2Game

SCENES = []


def scene(function):
    SCENES.append(function)
    return function


def shot(app, name):
    if app.intro_fade or app.fade:      # a picture taken while the game fades in comes out dark: finish the fade
        app.intro_fade = app.fade = 0
        app.draw()
    pygame.image.save(app.screen, os.path.join(OUT, name + ".png"))
    print("saved", name)


def new(seed=1, monsters=False, settle=0):
    app = game.App("Hero", seed=seed, sound=False)
    app.mode = "phase2"
    start_game(app, story=False, monsters=monsters)
    frames(app, 30 + settle)
    return app


def quiet(app):
    """Let the banners and toasts from setting the scene up go away."""
    app.banner = None
    app.hud.feed.take(app.game.messages)
    app.hud.feed.toasts.clear()
    app.hud.feed.newest_at = -99


def stand(app, pos):
    app.game.player.pos = pos
    app.player_px = list(game.tile_px(pos))
    app.camera = app.camera_target()


def next_to(app, pid):
    """Stand next to someone, facing them."""
    g = app.game
    r, c = g.people[pid]
    for way, (dr, dc) in rules.DIRECTIONS.items():
        spot = (r - dr, c - dc)
        if spot in g.neighbors((r, c)) and people.person_at(g, spot) is None:
            stand(app, spot)
            g.player.facing = way
            app.map_facing = way
            return way
    raise ValueError("nowhere to stand next to " + pid)


def talk_to(app, pid):
    """Walk into someone, so the dialogue box opens."""
    way = next_to(app, pid)
    frames(app, 5)
    quiet(app)
    press(app, {"up": pygame.K_UP, "down": pygame.K_DOWN, "left": pygame.K_LEFT, "right": pygame.K_RIGHT}[way])
    frames(app, 120)
    return app.game.talk


def to_choices(app):
    for _ in range(12):
        talk = app.game.talk
        if talk is None or talk.choices:
            break
        press(app, pygame.K_RETURN)
        frames(app, 120)


def pick_choice(app, words):
    talk = app.game.talk
    texts = [talk.fill(c["text"]) for c in talk.choices]
    number = next(i for i, text in enumerate(texts) if words in text)
    while talk.choice != number:
        press(app, pygame.K_DOWN)
    press(app, pygame.K_RETURN)
    frames(app, 5)


def skip_story(app):
    for _ in range(20):
        if app.state != "story":
            break
        press(app, pygame.K_RETURN)
        frames(app, 5)


def mid_game(app, chapters=2, step_on=True):
    """A few chapters of the main quest done, and a full pack."""
    g, p = app.game, app.game.player
    order = main_quest.chapters()
    quests.start(g, order[0])
    for qid in order[:chapters]:
        while quests.status(g, qid) == "active":
            quests.advance(g, qid)
    if step_on and chapters < len(order):
        quests.advance(g, order[chapters])
    g.story.clear()
    g.level_ups.clear()
    p.level, p.xp, p.max_health, p.health = 4, 95, 33, 21
    p.lives = 5
    p.swords = [rules.make_sword("great"), rules.make_sword()]
    p.swords[0].durability = 9
    p.food, p.wood, p.has_bow, p.arrows, p.has_boat = 3, 9, True, 12, True
    p.armor = p.max_armor
    p.diamonds, p.ring_hits = 2, 5
    p.powers = {"Stronger": 2, "Tougher": 1, "Springy": 1}
    g.gold = 87
    frames(app, 5)
    skip_story(app)
    while app.state == "levelup":
        frames(app, 40)
        press(app, pygame.K_1)
    quiet(app)


# ----- the title screen and the save slots ------------------------------------------------

@scene
def title():
    old = Phase2Game("Hero", seed=1)
    old.monsters = []
    old.save_slot = 1
    order = main_quest.chapters()
    quests.start(old, order[0])
    for qid in order[:3]:
        while quests.status(old, qid) == "active":
            quests.advance(old, qid)
    old.player.level, old.play_time = 5, 3 * 3600 + 25 * 60
    save.save_game(old)
    other = Phase2Game("Daddy", seed=2)
    other.save_slot, other.play_time = 3, 14 * 60
    save.save_game(other)
    app = game.App("Hero", sound=False)
    app.mode = "phase2"
    frames(app, 40)
    shot(app, "01-title")
    press(app, pygame.K_RETURN)
    frames(app, 3)
    shot(app, "02-slots-new-game")
    press(app, pygame.K_UP)
    press(app, pygame.K_RETURN)
    frames(app, 3)
    shot(app, "03-slots-start-over")
    press(app, pygame.K_ESCAPE)
    press(app, pygame.K_ESCAPE)
    app.mode = "continue"
    press(app, pygame.K_RETURN)
    frames(app, 3)
    shot(app, "04-slots-load")
    press(app, pygame.K_d)
    frames(app, 3)
    shot(app, "05-slots-delete")
    press(app, pygame.K_ESCAPE)
    press(app, pygame.K_ESCAPE)
    for number in (1, 3):
        save.delete_save(number)


@scene
def story():
    app = game.App("Hero", seed=1, sound=False)
    app.mode = "phase2"
    start_game(app, story=True, monsters=False)
    frames(app, 90)
    shot(app, "06-story-card")
    skip_story(app)
    frames(app, 200)
    shot(app, "07-new-game")


# ----- the pause menu ---------------------------------------------------------------------

@scene
def pause():
    app = new(seed=2)
    mid_game(app)
    app.game.play_time = 47 * 60
    frames(app, 30)
    press(app, pygame.K_p)
    frames(app, 3)
    shot(app, "08-pause")
    press(app, pygame.K_DOWN)
    press(app, pygame.K_RETURN)
    frames(app, 3)
    shot(app, "09-pause-saved")
    for _ in range(2):
        press(app, pygame.K_DOWN)
    press(app, pygame.K_RETURN)
    frames(app, 3)
    shot(app, "10-pause-quit")


# ----- the panel in every land, messages and toasts ---------------------------------------

@scene
def lands():
    app = new(seed=2)
    mid_game(app, chapters=3)
    g = app.game
    seen = []
    squares = [(r, c) for r in range(g.rows) for c in range(g.cols)]
    for spot in squares:
        land = g.land_name(spot)
        if land and land not in seen:
            seen.append(land)
    for number, land in enumerate(seen):
        spots = [s for s in squares if g.land_name(s) == land and g.neighbors(s) and s in g.neighbors(g.neighbors(s)[0])
                 and people.person_at(g, s) is None]
        middle = (sum(s[0] for s in spots) / len(spots), sum(s[1] for s in spots) / len(spots))
        stand(app, min(spots, key=lambda s: (s[0] - middle[0]) ** 2 + (s[1] - middle[1]) ** 2))
        g.monsters = []
        frames(app, 5)
        quiet(app)
        g.messages.clear()
        g.log("You walk into %s." % land, "info")
        frames(app, 60)
        shot(app, "11-land-%d-%s" % (number + 1, land.lower().replace(" ", "-").replace("'", "")))
    beside = [s for s in g.neighbors(g.portal) if s != g.portal]      # next to the Portal, to see its picture
    if beside:
        stand(app, beside[0])
        frames(app, 5)
        quiet(app)
        frames(app, 30)
        shot(app, "11-portal")
    stones = sorted(g.waystones)                                      # the waystone travel list
    if len(stones) > 1:
        g.unlocked_waystones.update(stones)
        stand(app, g.start if g.start in stones else stones[0])
        g.travel_open = True
        frames(app, 5)
        quiet(app)
        frames(app, 5)
        shot(app, "11-waystones")


@scene
def messages():
    app = new(seed=2)
    mid_game(app)
    g = app.game
    g.messages.clear()
    g.log("You find some wild berries!", "loot")
    g.log("A Spider scuttles away from you.", "info")
    g.gold += 12
    g.log("You open the treasure chest!", "loot")
    g.log("You put 12 gold coins in your pouch. You have %d gold." % g.gold, "loot")
    frames(app, 25)
    shot(app, "12-message-and-toast")
    frames(app, 300)
    g.gain_xp(200)
    frames(app, 20)
    shot(app, "13-level-up")


# ----- people: talking, the shop, the blacksmith, the quest log ---------------------------

@scene
def talk():
    app = new()
    talk_to(app, "guide_rosa")
    shot(app, "14-talk-rosa")
    to_choices(app)
    shot(app, "15-talk-choices")
    press(app, pygame.K_ESCAPE)
    frames(app, 10)
    skip_story(app)
    frames(app, 40)
    shot(app, "16-after-a-talk")
    for number, pid in enumerate(("farmer_bo", "pip", "elder_oona", "eldon", "finn", "whiskers")):
        app = new()
        if talk_to(app, pid) is None:
            print("   (no talk with %s)" % pid)
            continue
        shot(app, "17-talk-%d-%s" % (number + 1, pid.replace("_", "-")))


@scene
def shop():
    app = new()
    app.game.gold = 50
    app.game.player.wood = 6
    app.game.player.swords.append(rules.make_sword())
    talk_to(app, "mabel")
    to_choices(app)
    shot(app, "18-talk-mabel")
    pick_choice(app, "shop")
    frames(app, 10)
    shot(app, "19-shop-buy")
    press(app, pygame.K_RETURN)
    frames(app, 5)
    shot(app, "20-shop-bought")
    press(app, pygame.K_RIGHT)
    frames(app, 5)
    shot(app, "21-shop-sell")
    app.game.gold = 0
    press(app, pygame.K_LEFT)
    press(app, pygame.K_DOWN)
    press(app, pygame.K_RETURN)
    frames(app, 5)
    shot(app, "22-shop-no-gold")


@scene
def blacksmith():
    app = new()
    g = app.game
    g.gold = 20
    g.player.wood = 8
    g.player.swords[0].durability = 3
    talk_to(app, "bram")
    to_choices(app)
    shot(app, "23-talk-bram")
    pick_choice(app, "Fix my sword")
    frames(app, 120)
    shot(app, "24-bram-fixed-it")
    to_choices(app)
    pick_choice(app, "Forge")
    frames(app, 30)
    shot(app, "25-forge")


@scene
def quest_log():
    app = new()
    press(app, pygame.K_q)
    frames(app, 5)
    shot(app, "26-quests-none-yet")
    app = new(seed=2)
    mid_game(app, chapters=3)
    g = app.game
    for qid in quests.all_quests():
        if not qid.startswith("main_") and quests.status(g, qid) is None and len(quests.active(g)) < 4:
            quests.start(g, qid)
    g.story.clear()
    frames(app, 5)
    skip_story(app)
    quiet(app)
    press(app, pygame.K_q)
    frames(app, 5)
    shot(app, "27-quests")


# ----- the pages: L, B, H and How to Play -------------------------------------------------

@scene
def pages():
    app = new(seed=2)
    mid_game(app)
    g = app.game
    for words, kind in (("You find some wild berries!", "loot"), ("A Spider scuttles away from you.", "info"),
                        ("Chop, chop! You get 2 wood. This tree has 4 left.", "loot"),
                        ("Ouch! A Zombie hits you for 4.", "bad"), ("You eat some food. Yum!", "good")):
        g.log(words, kind)
    frames(app, 300)
    press(app, pygame.K_l)
    frames(app, 5)
    shot(app, "28-page-log-L")
    press(app, pygame.K_l)
    press(app, pygame.K_b)
    frames(app, 5)
    shot(app, "29-page-map-B")
    press(app, pygame.K_b)
    press(app, pygame.K_h)
    frames(app, 5)
    shot(app, "30-page-keys-H")
    press(app, pygame.K_RETURN)
    frames(app, 5)
    shot(app, "31-how-to-play")
    press(app, pygame.K_ESCAPE)
    press(app, pygame.K_c)
    frames(app, 5)
    shot(app, "32-craft")


# ----- caves, fights, Nightfall Hollow, the castle and the Shadow King --------------------

@scene
def cave():
    app = new()
    quests.start(app.game, main_quest.chapters()[0])
    app.game.story.clear()
    frames(app, 5)
    skip_story(app)
    quiet(app)
    walk_into_a_mine(app)
    frames(app, 80)
    shot(app, "33-cave")
    press(app, pygame.K_h)
    frames(app, 5)
    shot(app, "34-cave-keys-H")
    press(app, pygame.K_h)
    press(app, pygame.K_p)
    frames(app, 3)
    shot(app, "35-cave-pause")


@scene
def fight():
    app = new()
    g, p = app.game, app.game.player
    m = g.new_monster("Zombie")
    m.pos = next(s for s in g.neighbors(p.pos) if g.tile(s) == "G")
    g.monsters = [m]
    quiet(app)
    g.start_battle(m)
    frames(app, 60)
    press(app, pygame.K_a)
    frames(app, 50)
    shot(app, "36-fight")
    press(app, pygame.K_p)
    frames(app, 3)
    shot(app, "37-fight-pause")


@scene
def nightfall():
    app = game.App("Hero", seed=1, sound=False, castle=True, phase2_mode="phase2")
    app.game.story.clear()
    frames(app, 60)
    skip_story(app)
    frames(app, 60)
    quiet(app)
    app.game.log("A cold wind blows. The castle is close!", "quest")
    frames(app, 40)
    shot(app, "38-nightfall")
    press(app, pygame.K_h)
    frames(app, 5)
    shot(app, "39-nightfall-keys-H")
    press(app, pygame.K_h)
    press(app, pygame.K_q)
    frames(app, 5)
    shot(app, "40-nightfall-quests")
    press(app, pygame.K_q)
    g = app.game
    g.player.pos = g.castle
    g.do("act") if g.cave is None else None
    frames(app, 30)
    for _ in range(6):
        if app.state in ("story", "sunfang"):
            shot(app, "41-castle-%s" % app.state)
            break
        frames(app, 20)
    for _ in range(40):
        if app.state == "cave":
            break
        press(app, pygame.K_RETURN)
        press(app, pygame.K_a)
        frames(app, 20)
    frames(app, 80)
    shot(app, "42-castle")


@scene
def king():
    app = game.App("Hero", seed=1, sound=False, throne=True, phase2_mode="phase2")
    g = app.game
    frames(app, 40)
    skip_story(app)
    frames(app, 120)
    shot(app, "43-shadow-king")
    press(app, pygame.K_p)
    frames(app, 3)
    shot(app, "44-shadow-king-pause")
    press(app, pygame.K_p)
    g.cave.beaten_time = 0.01                       # as if you just beat him
    frames(app, 30)
    number = 0
    while app.state == "story" and number < 12:
        frames(app, 60)
        number += 1
        shot(app, "45-ending-card-%d" % number)
        press(app, pygame.K_RETURN)
        frames(app, 5)
    frames(app, 120)
    shot(app, "46-home-after-the-king")
    press(app, pygame.K_q)
    frames(app, 5)
    shot(app, "47-quests-after-the-king")
    press(app, pygame.K_q)
    press(app, pygame.K_p)
    frames(app, 3)
    shot(app, "48-pause-after-the-king")


@scene
def game_over():
    app = new(seed=2)
    mid_game(app)
    g = app.game
    g.player.lives = 0
    g.player.health = 0
    app.state = "end"
    frames(app, 30)
    shot(app, "49-game-over")


@scene
def classic():
    app = game.App("Hero", seed=1, sound=False)
    start_game(app)
    frames(app, 120)
    shot(app, "50-classic-is-unchanged")
    press(app, pygame.K_h)
    frames(app, 5)
    shot(app, "51-classic-how-to-play")


if __name__ == "__main__":
    wanted = sys.argv[1:]
    for function in SCENES:
        if wanted and function.__name__ not in wanted:
            continue
        try:
            function()
        except Exception:
            print("!! %s stopped:" % function.__name__)
            traceback.print_exc()
