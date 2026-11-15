"""
SAVING AND LOADING a Phase 2 game, so it can be played over several sittings.

There are 3 SAVE SLOTS, so 3 adventures can go on at once. The game saves by itself (into its own
slot) when you go into a house or a Mine, and when you close the window; P (the pause menu,
phase2/pause.py) saves when you want. "Load" on the title screen lists the slots.

On a computer each slot is a JSON file in your home folder:  ~/.adventure/phase2_save.json is
slot 1 (it's the file the game used before there were slots, so an old save just IS slot 1), and
phase2_save_2.json and phase2_save_3.json are slots 2 and 3. (The tests say ADVENTURE_SAVE_FILE=somewhere
else, so they never touch it.) In a web browser there are no files, so each slot is a key in the
browser's own storage ("localStorage"), like settings.py does: the old key for slot 1, then "_2", "_3".
A save from before the game was renamed (an older folder and key) still loads: it's read from there
until that slot is saved again, which moves it to the new place.

The whole game is written down, the way it is right then: the map (trees you chopped, houses you
built), you, the monsters, the quests... but not a cave or a fight you're in the middle of. (You
come back on the map, at the Mine.) Sets, tuples and the game's own objects (Player, Monster,
Quest, Tool) get a little label like {"$set": [...]}, so they come back as what they were.
"""

import base64
import datetime
import json
import os
import random
import sys

import rules

IN_BROWSER = sys.platform == "emscripten"
VERSION = 1
BROWSER_NAME = "adventure_phase2_save"
# The older save folder and key (from before the game was renamed): read them, so old saves still load
OLD_FOLDER = base64.b64decode("Lm5vYWhfYWR2ZW50dXJl").decode()
OLD_BROWSER_NAME = base64.b64decode("bm9haF9hZHZlbnR1cmVfcGhhc2UyX3NhdmU=").decode()
SLOTS = (1, 2, 3)
KEEP_MESSAGES = 30              # the message log keeps this many lines in the save
NOT_SAVED = {"rng", "cave", "battle", "effects", "messages", "power_offer"}   # put back fresh when you load
NOT_SAVED = NOT_SAVED | {"talk"}   # stage 2b: the talk you're in (phase2/people.py) isn't saved
NOT_SAVED = NOT_SAVED | {"skip_quit_save"}   # (the pause menu's Quit -> "Save first?" No)
CLASSES = {"Player": rules.Player, "Monster": rules.Monster, "Quest": rules.Quest, "Tool": rules.Tool}


def _slot_path(path, slot):
    if slot == 1:
        return path                       # slot 1 is the old one-and-only save file
    stem, ext = os.path.splitext(path)
    return "%s_%d%s" % (stem, slot, ext or ".json")


def save_file(slot=1):
    path = os.environ.get("ADVENTURE_SAVE_FILE") or os.path.join(os.path.expanduser("~"), ".adventure",
                                                                 "phase2_save.json")
    return _slot_path(path, slot)


def old_save_file(slot=1):
    """Where this slot was saved before the game was renamed (None when the tests pick the file)."""
    if os.environ.get("ADVENTURE_SAVE_FILE"):
        return None
    return _slot_path(os.path.join(os.path.expanduser("~"), OLD_FOLDER, "phase2_save.json"), slot)


def browser_name(slot=1, name=BROWSER_NAME):
    return name if slot == 1 else "%s_%d" % (name, slot)


def _forget_old(slot):
    """The slot is saved in the new place now: drop the older copy, so it can't come back."""
    try:
        if IN_BROWSER:
            storage = browser_storage()
            if storage.getItem(browser_name(slot, OLD_BROWSER_NAME)) is not None:
                storage.removeItem(browser_name(slot, OLD_BROWSER_NAME))
        elif old_save_file(slot) and os.path.exists(old_save_file(slot)):
            os.remove(old_save_file(slot))
    except (OSError, AttributeError, ImportError):
        pass


def slot_of(game):
    return getattr(game, "save_slot", 1)


def browser_storage():
    import platform                       # in a browser, pygbag's platform module can reach the web page
    return platform.window.localStorage


# ===========================================================================
# The game <-> plain JSON
# ===========================================================================

def _classes():
    from phase2 import world_map          # (here, so save.py and world.py can import each other)
    return dict(CLASSES, Atlas=world_map.Atlas)


class _Writer:
    def __init__(self):
        self.objects = []                 # every Player, Monster... once (a Quest can be in 2 places)
        self.numbers = {}                 # id(object) -> its number in self.objects
        self.kinds = {cls: name for name, cls in _classes().items()}

    def encode(self, value):
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, list):
            return [self.encode(v) for v in value]
        if isinstance(value, tuple):
            return {"$tuple": [self.encode(v) for v in value]}
        if isinstance(value, (set, frozenset)):
            return {"$set": sorted((self.encode(v) for v in value), key=repr)}
        if isinstance(value, dict):
            return {"$dict": [[self.encode(k), self.encode(v)] for k, v in value.items()]}
        kind = self.kinds.get(type(value))
        if kind is None:
            raise TypeError("save.py doesn't know how to save %r" % type(value).__name__)
        if id(value) not in self.numbers:
            self.numbers[id(value)] = len(self.objects)
            entry = {"class": kind}
            self.objects.append(entry)
            entry["fields"] = self.encode(vars(value))
        return {"$obj": self.numbers[id(value)]}


class _Reader:
    def __init__(self, objects):
        classes = _classes()
        self.raw = objects
        self.objects = [classes[entry["class"]].__new__(classes[entry["class"]]) for entry in objects]
        for thing, entry in zip(self.objects, objects):
            thing.__dict__.update(self.decode(entry["fields"]))

    def decode(self, value):
        if isinstance(value, list):
            return [self.decode(v) for v in value]
        if not isinstance(value, dict):
            return value
        if "$tuple" in value:
            return tuple(self.decode(v) for v in value["$tuple"])
        if "$set" in value:
            return {self.decode(v) for v in value["$set"]}
        if "$dict" in value:
            return {self.decode(k): self.decode(v) for k, v in value["$dict"]}
        if "$obj" in value:
            return self.objects[value["$obj"]]
        raise ValueError("a save can't have %r" % value)


def game_to_data(game):
    writer = _Writer()
    fields = {k: v for k, v in vars(game).items() if k not in NOT_SAVED}
    fields["messages"] = game.messages[-KEEP_MESSAGES:]
    data = {"version": VERSION, "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "summary": summary(game), "rng": writer.encode(game.rng.getstate())}
    data["game"] = writer.encode(fields)
    data["objects"] = writer.objects
    return data


def data_to_game(data):
    from phase2.world import Phase2Game
    if data.get("version") != VERSION:
        raise ValueError("a save from a different version of the game")
    reader = _Reader(data["objects"])
    game = Phase2Game.__new__(Phase2Game)
    game.__dict__.update(reader.decode(data["game"]))
    game.rng = random.Random()
    game.rng.setstate(reader.decode(data["rng"]))
    game.cave = game.battle = game.power_offer = None
    game.effects = []
    game.__dict__.setdefault("play_time", 0.0)    # (a save from before play time was counted)
    from phase2 import waystones               # stage 2a: waystones, lookouts, hidden chests, gates
    waystones.after_load(game)
    from phase2 import people             # stage 2b: fill in what an older save didn't have, place everyone
    people.after_load(game)
    from phase2 import main_quest         # stage 3a: the main quest
    main_quest.after_load(game)
    return game


# ===========================================================================
# Writing it down, and reading it back
# ===========================================================================

def summary(game):
    """What the slot list shows about a game: whose it is, where, what level, Light Stones, play time."""
    from phase2 import main_quest
    try:
        stones = len(main_quest.relics(game))
    except Exception:                          # noqa: BLE001  (a game that's only half set up)
        stones = 0
    land = game.land_name(game.player.pos) if game.world == 1 else "Nightfall Hollow"
    return {"name": game.player.name, "land": land or "the wild", "level": game.player.level,
            "stones": stones, "stones_needed": main_quest.relics_needed(),
            "play_time": getattr(game, "play_time", 0.0)}


def save_game(game, slot=None):
    """Save the game into its slot (or this one). Returns True if it worked (it never crashes the game if it didn't)."""
    slot = slot or slot_of(game)
    try:
        text = json.dumps(game_to_data(game), separators=(",", ":"))
        if IN_BROWSER:
            browser_storage().setItem(browser_name(slot), text)
            _forget_old(slot)
            return True
        path = save_file(slot)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".new", "w", encoding="utf-8") as file:
            file.write(text)
        os.replace(path + ".new", path)      # all at once, so a half-written save never replaces a good one
        _forget_old(slot)
        return True
    except Exception as problem:              # noqa: BLE001  (a save that fails must not stop the game)
        print("Couldn't save the game: %s" % problem)
        return False


def _read_text(slot=1):
    try:
        if IN_BROWSER:
            storage = browser_storage()
            text = storage.getItem(browser_name(slot))
            if not isinstance(text, str):
                text = storage.getItem(browser_name(slot, OLD_BROWSER_NAME))   # saved under the older key?
            return text if isinstance(text, str) else None
        for path in (save_file(slot), old_save_file(slot)):   # the older folder only if the new one has none
            if path and os.path.exists(path):
                with open(path, encoding="utf-8") as file:
                    return file.read()
        return None
    except (OSError, AttributeError, ImportError):
        return None


def has_save(slot=None):
    """Is there a save in this slot (or, with no slot, in any of them)?"""
    return any(_read_text(s) for s in ([slot] if slot else SLOTS))


def used_slots():
    return [slot for slot in SLOTS if _read_text(slot)]


def newest_slot():
    """The slot saved last (for python game.py --continue), or 1."""
    infos = [slot_info(slot) for slot in used_slots()]
    infos = [info for info in infos if info.get("saved_at")]
    return max(infos, key=lambda info: info["saved_at"])["slot"] if infos else 1


def slot_info(slot):
    """What the slot list shows: {"slot", "empty", "broken", "name", "land", "level", "stones",
    "stones_needed", "play_time", "saved_at"}. A save from before slots has no summary: the game is
    loaded once to find out."""
    text = _read_text(slot)
    if not text:
        return {"slot": slot, "empty": True}
    try:
        data = json.loads(text)
        info = data.get("summary")
        if info is None:
            info = summary(data_to_game(data))
        return dict(info, slot=slot, empty=False, broken=False, saved_at=data.get("saved_at"))
    except Exception:                          # noqa: BLE001  (an old or broken save)
        return {"slot": slot, "empty": False, "broken": True}


def load_game(slot=1):
    """The game saved in this slot, or None if there isn't one (or it can't be read)."""
    text = _read_text(slot)
    if not text:
        return None
    try:
        game = data_to_game(json.loads(text))
    except Exception as problem:              # noqa: BLE001  (an old or broken save: just start fresh)
        print("Couldn't load the saved game: %s" % problem)
        return None
    game.save_slot = slot
    game.log("Welcome back, %s! Your adventure goes on." % game.player.name, "quest")
    return game


def delete_save(slot=1):
    try:
        if IN_BROWSER:
            browser_storage().removeItem(browser_name(slot))
        elif os.path.exists(save_file(slot)):
            os.remove(save_file(slot))
    except (OSError, AttributeError, ImportError):
        pass
    _forget_old(slot)


def time_words(seconds):
    """Play time the way the slot list says it: "1 h 05 min", "12 min" or "under a minute"."""
    minutes = int(seconds // 60)
    if minutes >= 60:
        return "%d h %02d min" % (minutes // 60, minutes % 60)
    return "%d min" % minutes if minutes else "under a minute"


def date_words(saved_at):
    """The date saved, in the computer's own time: "Nov 13, 3:16 pm"."""
    try:
        when = datetime.datetime.fromisoformat(saved_at).astimezone()
    except (TypeError, ValueError):
        return ""
    return "%s %d, %d:%02d %s" % (when.strftime("%b"), when.day, (when.hour % 12) or 12, when.minute,
                                  "am" if when.hour < 12 else "pm")
