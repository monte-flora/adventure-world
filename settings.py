"""
How the game remembers your choices, like "tips off", for next time you play.

On a computer they go in a little file called settings.json, next to game.py.
(You can open it and read it. Delete it, and the game forgets everything.)

In a web browser there are no files, so they go in the browser's own storage
(called "localStorage"). Each browser keeps its own.

The settings are written in JSON, a way of writing down lists and labels that
lots of programs can read. They look like this:
    {"tips": true, "tips_seen": ["walk", "forest"]}
"""

import base64
import json
import os
import sys

IN_BROWSER = sys.platform == "emscripten"
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
# The tests say ADVENTURE_SETTINGS_FILE=somewhere else, so they never change your real settings
SETTINGS_FILE = os.environ.get("ADVENTURE_SETTINGS_FILE") or SETTINGS_FILE
BROWSER_NAME = "adventure_settings"      # the label they're kept under in the browser
# The older save key (from before the game was renamed): read it once, so old choices aren't lost
OLD_BROWSER_NAME = base64.b64decode("bm9haF9hZHZlbnR1cmVfc2V0dGluZ3M=").decode()


def browser_storage():
    import platform                           # in a browser, pygbag's platform module can reach the web page
    return platform.window.localStorage


def load():
    """Everything you chose last time, as a dictionary. Nothing saved yet? Then it's empty: {}"""
    try:
        if IN_BROWSER:
            storage = browser_storage()
            text = storage.getItem(BROWSER_NAME)
            if text is None:
                text = storage.getItem(OLD_BROWSER_NAME)  # saved under the older key? Use that
        else:
            with open(SETTINGS_FILE) as file:
                text = file.read()
        saved = json.loads(text) if isinstance(text, str) else {}
    except (OSError, ValueError, AttributeError, ImportError):
        return {}                             # no settings yet (or they got mixed up): start fresh
    return saved if isinstance(saved, dict) else {}


def save(**changes):
    """Remember some choices, like  save(tips=False). The ones you don't mention stay as they were."""
    saved = load()
    saved.update(changes)
    text = json.dumps(saved, indent=1, sort_keys=True)
    try:
        if IN_BROWSER:
            storage = browser_storage()
            storage.setItem(BROWSER_NAME, text)
            if storage.getItem(OLD_BROWSER_NAME) is not None:
                storage.removeItem(OLD_BROWSER_NAME)  # it's under the new key now
        else:
            with open(SETTINGS_FILE, "w") as file:
                file.write(text + "\n")
    except (OSError, AttributeError, ImportError):
        pass                                  # can't save here? Never mind - the game still works
