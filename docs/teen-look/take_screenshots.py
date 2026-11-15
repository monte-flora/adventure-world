"""
Takes the teen-look screenshots: Phase 2's title, map + panel, talk box, story cards, Classic.
No window opens. From the game's folder:

    python docs/teen-look/take_screenshots.py after      # (or "before")

The pictures go in docs/teen-look/<before|after>/.
"""
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["ADVENTURE_SETTINGS_FILE"] = os.path.join(tempfile.mkdtemp(), "settings.json")
os.environ["ADVENTURE_SAVE_FILE"] = os.path.join(tempfile.mkdtemp(), "save.json")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "after")
os.makedirs(OUT, exist_ok=True)
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
import pygame
import tutorial
tutorial.START_WITH_TIPS = False
import game
from helpers import frames, press, start_game
from phase2 import people


def shot(app, name):
    pygame.image.save(app.screen, os.path.join(OUT, name + ".png"))
    print("saved", name)


def stand(app, pos):
    app.game.player.pos = pos
    app.player_px = list(game.tile_px(pos))
    app.camera = app.camera_target()


# 1. the title, Phase 2 picked
app = game.App("Hero", seed=1, sound=False)
app.mode = "phase2"
frames(app, 40)
shot(app, "01-title")

# 2. the first story card of a new Phase 2 game
app = game.App("Hero", seed=1, sound=False)
app.mode = "phase2"
start_game(app, story=True, monsters=True)
frames(app, 60)
shot(app, "02-intro-card")
while app.state == "story":
    press(app, pygame.K_SPACE); frames(app, 5)

# 3. the map and the panel
frames(app, 120)
app.banner = None
shot(app, "03-map-and-panel")

# 4. talking to Rosa
g = app.game
rosa = g.people["guide_rosa"]
spot = next(s for s in g.neighbors(rosa) if people.person_at(g, s) is None)
stand(app, spot)
frames(app, 20)
press(app, pygame.K_SPACE)
frames(app, 90)
shot(app, "04-talk-box")

# 5. Classic, to compare (must look as before)
app = game.App("Hero", seed=1, sound=False)
frames(app, 40)
shot(app, "05-classic-title")
start_game(app)
frames(app, 120)
shot(app, "06-classic-map")
