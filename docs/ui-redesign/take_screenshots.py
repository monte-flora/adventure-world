"""
Takes the screenshots in this folder: Phase 2's side panel and message box in a few situations.
No window opens (the "dummy" video driver). From the game's folder:

    pixi run python docs/ui-redesign/take_screenshots.py

(or any Python that has pygame). The pictures are written next to this file.
"""
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["ADVENTURE_SETTINGS_FILE"] = os.path.join(tempfile.mkdtemp(), "settings.json")     # never your real settings
os.environ["ADVENTURE_SAVE_FILE"] = os.path.join(tempfile.mkdtemp(), "save.json")             # or your real save
OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(OUT))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
import pygame
import tutorial
tutorial.START_WITH_TIPS = False
import game
import rules
from helpers import frames, press, move_mouse, start_game, walk_into_a_mine
from phase2 import people, quests

def shot(app, name):
    pygame.image.save(app.screen, os.path.join(OUT, name + ".png"))
    print("saved", name)

def new(seed=1, monsters=True, settle=0):
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

# 1. a new game in Home Meadow
app = new()
frames(app, 20)
shot(app, "01-new-game-home-meadow")
frames(app, 300)
shot(app, "02-new-game-a-few-seconds-later")

# 2. next to a person (Rosa)
g = app.game
rosa = g.people["guide_rosa"]
spot = next(s for s in g.neighbors(rosa) if people.person_at(g, s) is None)
stand(app, spot)
g.player.facing = "up"
g.log("You walk over to Rosa the Guide.")
frames(app, 40)
shot(app, "03-next-to-a-person")
press(app, pygame.K_SPACE)
frames(app, 90)
for _ in range(8):
    if app.state != "people":
        break
    press(app, pygame.K_RETURN)
    frames(app, 40)
if app.state == "people":
    press(app, pygame.K_ESCAPE)
frames(app, 10)
while app.state == "story":
    press(app, pygame.K_SPACE); frames(app, 5)
frames(app, 30)
shot(app, "04-quest-started-toast")

# 3. mid-game with lots of items
app = new(seed=2)
g, p = app.game, app.game.player
quests.start(g, "main_home")
for qid in ("main_home", "main_woods"):
    while quests.status(g, qid) == "active":
        quests.advance(g, qid)
g.story.clear(); g.level_ups.clear()
quests.advance(g, "main_lake")      # talk to Finn done: now "beat the cave at the Great Lake"
p.level, p.xp, p.max_health, p.health = 4, 95, 33, 14
p.lives = 5
p.swords = [rules.make_sword("great"), rules.make_sword()]
p.swords[0].durability = 9
p.food, p.wood, p.has_bow, p.arrows, p.has_boat = 3, 9, True, 12, True
p.armor = p.max_armor
p.diamonds, p.ring_hits = 2, 5
p.powers = {"Stronger": 2, "Tougher": 1, "Springy": 1}
g.gold = 87
forest = min((s for s in [(r, c) for r in range(g.rows) for c in range(g.cols)] if g.map[s[0]][s[1]] == "F" and g.land_name(s) == "Whispering Woods"), key=lambda s: rules.distance(s, g.start))
stand(app, forest)
frames(app, 5); quiet(app)
g.messages.clear()
g.log("You find some wild berries!", "loot")
g.log("A Spider scuttles away from you.", "info")
g.log("Chop, chop! You get 2 wood. This tree has 4 left.", "loot")
frames(app, 60)
shot(app, "05-mid-game-lots-of-items")
slot = app.hud.spots["item:sword"]
move_mouse(app, slot.center)
frames(app, 5)
shot(app, "06-hover-tooltip-on-the-sword")
move_mouse(app, (300, 300))

# 4. loot message + toast
g.gold += 12
g.log("You open the treasure chest!", "loot")
g.log("You put 12 gold coins in your pouch. You have %d gold." % g.gold, "loot")
frames(app, 25)
shot(app, "07-loot-message-and-toast")
frames(app, 300)
g.gain_xp(200)
frames(app, 20)
shot(app, "08-level-up")
while app.state == "levelup":
    frames(app, 40); press(app, pygame.K_1)
frames(app, 30)

# 5. pages: big map, log, keys
frames(app, 300)
press(app, pygame.K_b); frames(app, 5)
shot(app, "09-big-map-B")
press(app, pygame.K_b)
press(app, pygame.K_l); frames(app, 5)
shot(app, "10-message-log-L")
press(app, pygame.K_l)
press(app, pygame.K_h); frames(app, 5)
shot(app, "11-every-key-H")
press(app, pygame.K_h)

# 6. in a cave
app = new(seed=1, monsters=False)
quests.start(app.game, "main_home")
app.game.story.clear()
frames(app, 5); quiet(app)
walk_into_a_mine(app)
frames(app, 80)
shot(app, "12-in-a-cave")
app.game.player.health = 9
app.game.log("Ouch! A Zombie hits you for 4.", "bad")
frames(app, 20)
shot(app, "13-in-a-cave-hurt")

# 7. Nightfall Hollow
app = game.App("Hero", seed=1, sound=False, castle=True, phase2_mode="phase2")
app.game.story.clear()
frames(app, 60)
while app.state == "story":
    press(app, pygame.K_SPACE); frames(app, 5)
frames(app, 60)
quiet(app)
app.game.log("A cold wind blows. The castle is close!", "quest")
frames(app, 40)
shot(app, "14-nightfall-hollow")

# 8. a fight on the map, and a tip bubble pointing at the pack
app = new(seed=1, monsters=False)
g, p = app.game, app.game.player
m = g.new_monster("Zombie")
spot = next(s for s in g.neighbors(p.pos) if g.tile(s) == "G")
m.pos = spot
g.monsters = [m]
quiet(app)
g.start_battle(m)
frames(app, 60)
press(app, pygame.K_a); frames(app, 50)
shot(app, "15-a-fight")
app = new(seed=1, monsters=False)
app.tips.on = True
app.tips.seen = set(n for n in tutorial.TIPS if n != "eat")
p = app.game.player
p.health = 8
stand(app, next(s for s in app.game.neighbors(p.pos) if app.game.tile(s) in "GR"))
quiet(app)
app.game.turn += 1
frames(app, 240)
shot(app, "16-a-tip-points-at-the-food")

# Classic, to compare (must look as before)
app = game.App("Hero", seed=1, sound=False)
start_game(app)
frames(app, 120)
shot(app, "17-classic-is-unchanged")
