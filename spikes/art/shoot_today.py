"""Screenshots of today's art (the 'before' side): the Shadowfall map and a cave. No window opens.

    python spikes/art/shoot_today.py        -> docs/teen/art/before_map.png, before_cave.png
"""
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["ADVENTURE_SETTINGS_FILE"] = os.path.join(tempfile.mkdtemp(), "settings.json")
os.environ["ADVENTURE_SAVE_FILE"] = os.path.join(tempfile.mkdtemp(), "save.json")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "teen", "art")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
import pygame  # noqa: E402
import tutorial  # noqa: E402
tutorial.START_WITH_TIPS = False
import game  # noqa: E402
from helpers import frames, start_game, walk_into_a_mine  # noqa: E402


def shot(app, name):
    pygame.image.save(app.screen, os.path.join(OUT, name + ".png"))
    print("saved", name)


app = game.App("Hero", seed=1, sound=False)
app.mode = "phase2"
start_game(app, monsters=True)
frames(app, 120)
app.banner = None
shot(app, "before_map")

app = game.App("Hero", seed=1, sound=False)
app.mode = "phase2"
start_game(app)
walk_into_a_mine(app)
frames(app, 60)
shot(app, "before_cave")
