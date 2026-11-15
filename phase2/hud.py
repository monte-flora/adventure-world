"""
WHAT PHASE 2'S SIDE PANEL AND MESSAGE BOX SHOW (phase2/draw_hud.py draws it).

The classic panel is a long list, and most of it says "none". This one shows only what matters now:

    pack(game)             the things you have, as icons with a number. What you don't have isn't there.
    next_goal(game)        the "NEXT" card: the main quest's step in a few words, which way to go
                           and how far, and how many of the 7 Light Stones you have
    here(game, hints)      where you are, and the 2-4 keys that do something right here
                           ("SPACE talk to Rosa" next to her, "E eat" when you're hurt...)
    footer_keys()          H (every key) and P (pause): the rest of the keys are behind H
    Feed                   the messages: the newest one glows for a few seconds, and the big ones
                           (quests, treasure, level ups) also pop up as a "toast" over the map
    tooltip(game, name)    the words for the thing under the mouse

Keys: L opens the message log, B the big map, H every key (and Q the quests, as before).

This file knows nothing about graphics, so it's easy to test.
"""

import math
import re
import sys

import rules

from phase2 import keys as phase2_keys, main_quest, people, quests

# ----- settings: try changing these! ------------------------------------------------------
FRESH_TIME = 5.0            # the newest message glows this long (seconds)
SLIDE_TIME = 0.25           # ...and slides in this fast
TOAST_TIME = 3.5            # a toast stays this long
TOAST_FADE = 0.5            # ...and takes this long to fade away at the end
TOASTS_AT_ONCE = 2          # more than this wait their turn
TOAST_KINDS = ("quest", "loot")
# Little finds that happen all the time don't get a toast (they already pop up over the Hero)
ROUTINE = ("+", "Chop, chop", "TIMBER", "You find some wild berries")
CARD_NEWS = ("LEVEL UP!",)  # news the LEVEL UP! card shows itself: no toast when that card is up
MAX_KEYS = 4                # how many lines the "here" card shows on the map
LOG_LINES = 60              # how far back the message log (L) goes
FAR_MONSTER = 5             # "F shoot" shows when a monster is this close
LIVE_STATES = ("play", "cave", "battle")     # the message clock only ticks while you're playing

STONE_COLORS = [            # the 7 Light Stones, in the main quest's order: (light, middle, dark)
    ((255, 240, 170), (255, 196, 70), (200, 120, 30)),      # Dawn: gold
    ((190, 250, 150), (96, 200, 90), (46, 120, 52)),        # Leaf: green
    ((170, 230, 255), (60, 150, 235), (38, 80, 170)),       # Tide: blue
    ((240, 200, 255), (170, 80, 220), (96, 40, 140)),       # Crown: purple
    ((240, 250, 255), (170, 230, 255), (86, 156, 222)),     # Frost: ice
    ((255, 220, 150), (255, 140, 30), (190, 70, 20)),       # Sun: orange
    ((230, 236, 250), (150, 160, 200), (84, 90, 130)),      # Moon: silver
]
WAYS = ["east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"]


# ===========================================================================
# The pack: only what you have
# ===========================================================================

def _item(key, icon, name, tip, count=None, tone="plain", bar=None):
    return {"id": key, "icon": icon, "name": name, "tip": tip, "count": count, "tone": tone, "bar": bar}


def pack(game):
    """The things in your pack, in order: [{"id", "icon", "name", "count", "tone", "bar", "tip"}, ...].
    Things you don't have are left out. No sword (or no pickaxe) IS shown, in red: that matters."""
    p = game.player
    items = []
    if p.sunfang:
        items.append(_item("sword", "sunfang", "Sunfang", "The sword of light (R swings it). It never breaks."
                           + (" A Perfect Forge: +%d damage!" % rules.PERFECT_BONUS if p.sunfang_perfect else ""),
                           tone="gold"))
    elif p.swords:
        sword = p.swords[0]
        name = {"great": "Great sword", "cracked": "Cracked sword"}.get(sword.quality, "Sword")
        tone = "bad" if sword.low or sword.quality == "cracked" else "gold" if sword.quality == "great" else "plain"
        tip = "R swings it. %d hits left, then it breaks." % sword.durability
        if len(p.swords) > 1:
            tip += " You have %d more." % (len(p.swords) - 1)
        tip += " Make a new one: press C in a forest, or ask a blacksmith."
        items.append(_item("sword", "sword", name, tip, "x%d" % len(p.swords) if len(p.swords) > 1 else None,
                           tone, (sword.durability, sword.max_durability)))
    else:
        items.append(_item("sword", "sword", "No sword!", "You have no sword! Make one: press C in a forest, "
                           "or buy one in a shop.", "!", "bad"))
    if p.pickaxe:
        items.append(_item("pickaxe", "pickaxe", "Pickaxe", "Digs cracked rock and ore in caves (press G). "
                           "It never breaks."))
    else:
        items.append(_item("pickaxe", "pickaxe", "No pickaxe!", "You have no pickaxe! Make one: press C in a forest.",
                           "!", "bad"))
    if p.food:
        items.append(_item("food", "apple", "Food", "Press E to eat and get health back. You can carry %d. "
                           "Find berries with SPACE in a forest, or buy them." % p.max_food,
                           str(p.food), "full" if p.food >= p.max_food else "plain"))
    if p.wood:
        items.append(_item("wood", "wood", "Wood", "For the Craft menu (C): a bow is %d wood, a house %d, a boat %d. "
                           "Chop trees with T. You can carry %d."
                           % (rules.BOW_COST, rules.HOUSE_COST, rules.BOAT_COST, rules.MAX_WOOD),
                           str(p.wood), "full" if p.wood >= rules.MAX_WOOD else "plain"))
    if p.has_bow:
        fire = "fire " if p.fire_arrows else ""
        tip = ("Press F to shoot the way you're facing. %d %sarrows left." % (p.arrows, fire) if p.arrows
               else "No arrows left!") + " Make arrows in the Craft menu (C), or buy them."
        items.append(_item("bow", "bow", "Bow", tip, str(p.arrows), "fire" if p.fire_arrows and p.arrows
                           else "plain" if p.arrows else "bad"))
    elif p.arrows:
        items.append(_item("bow", "bow", "Arrows (no bow)", "You have %d arrows, but no bow to shoot them! "
                           "Carve one in the Craft menu (C), or buy one." % p.arrows, str(p.arrows), "dim"))
    if p.has_boat:
        items.append(_item("boat", "boat_icon", "Boat", "Walk onto water and you row. Watch out for Sea Serpents!"))
    if p.has_armor:
        items.append(_item("armor", "shield", "Armor", "Soaks up hits before they hurt you: %d of %d left."
                           % (p.armor, p.max_armor), str(p.armor), "silver"))
    if p.diamonds:
        items.append(_item("diamonds", "diamond", "Diamonds", "From deep in the caves. Sunfang, the sword of light, "
                           "is forged from %d of them." % rules.SUNFANG_DIAMONDS, str(p.diamonds), "blue"))
    if p.ring_hits:
        items.append(_item("ring", "ring", "Diamond ring", "It's on your sword: +%d damage for %d more hits."
                           % (rules.RING_BONUS, p.ring_hits), "x%d" % p.ring_hits, "blue"))
    if p.has_tower_key:
        items.append(_item("key", "key", "Old key", "An old iron key with a little tower on it. "
                           "It opens the Watchtower!"))
    if p.lanterns:
        items.append(_item("lanterns", "lantern", "Lanterns", "Wren the ghost lost these. Bring them back to her!",
                           str(p.lanterns)))
    if p.has_planks:
        items.append(_item("planks", "planks", "Planks", "Old wooden planks. They fix the broken Shadow Bridge."))
    if not p.sunfang:
        if p.has_hilt:
            items.append(_item("hilt", "hilt", "Hilt", "The handle for Sunfang, carved from dead wood."))
        if p.sun_shards:
            items.append(_item("shards", "sun_shard", "Sun Shards", "%d make the Sun Gem for Sunfang."
                               % rules.SUN_SHARDS_NEEDED, "%d/%d" % (p.sun_shards, rules.SUN_SHARDS_NEEDED), "gold"))
    if p.light_shards:
        items.append(_item("light", "light_shard", "Light Shards", "Found in the castle. They make Sunfang glow brighter.",
                           str(p.light_shards), "gold"))
    return items


def powers(game):
    """The level-up powers you picked: [(name, how many times, what it does)]. (Lives are shown as hearts.)"""
    p = game.player
    return [(name, p.power(name), rules.POWERS[name]["what"]) for name in rules.POWERS
            if p.power(name) and name != "Extra life"]


# ===========================================================================
# The NEXT card
# ===========================================================================

def short(text):
    """A quest step in fewer words: what's in (brackets) is left out. The quest log (Q) has it all."""
    return re.sub(r"\s+", " ", re.sub(r"\s*\([^)]*\)", "", text)).strip()


def stones(game):
    """(how many Light Stones you have, how many there are)."""
    return len(main_quest.relics(game)), main_quest.relics_needed()


def _goal(text, **more):
    goal = {"title": None, "text": text, "count": None, "to": None, "target": None, "where": None,
            "way": None, "steps": None, "checks": [], "alert": None, "more": 0}
    goal.update(more)
    return goal


def next_goal(game):
    """What to do next, for the NEXT card:
        title    the chapter ("Light Stone 2: The Leaf Stone"), or None
        text     the step, in a few words
        count    (done, needed) for "defeat 4 monsters" steps, else None
        target   the square to go to (for the pin on the map), or None
        where    "north-east, 23 steps away" / "right here!" / None
        way      one of WAYS for the arrow, or None        steps   how far, or None
        checks   [(name, have, need)]: the Sunfang list in Nightfall Hollow
        alert    a line that can't wait ("Moonrise! Stay near light"), or None
        more     how many side quests you're doing too"""
    cave = game.cave
    if cave:
        if cave.is_throne_room or cave.is_castle:
            text = cave.goal() if hasattr(cave, "goal") else "Find the way on!"
            title = "The throne room" if cave.is_throne_room else "The Shadow King's castle"
            return _goal(text, title=title)
        return _goal("Find the EXIT door", title="In the cave")
    side = len([qid for qid in quests.active(game) if not quests.get(qid).get("main")])
    if game.world == 2:
        return _nightfall_goal(game, side)
    first = main_quest.data()["first"]
    if quests.status(game, first) == "new":
        goal = _goal("Talk to Rosa the Guide, next to your house", title="Start here", to="person:guide_rosa")
    else:
        qid = main_quest.current(game)
        if qid is None:
            return _goal("You did it all! Go wherever you like", title="The hero of all the lands", more=side)
        quest = quests.get(qid)
        step = quest["steps"][quests.step(game, qid)]
        if not isinstance(step, dict):
            step = {"text": step}
        goal = _goal(short(step["text"]), title=quest["title"], to=step.get("to"))
        need = (step.get("goal") or "").split(":")
        if need[0] == "defeat":
            goal["count"] = (quests.state(game)[qid].get("count", 0), int(need[3]))
    goal["more"] = side
    if goal["to"]:
        goal["target"] = main_quest.target(game, goal["to"])
        goal["where"] = main_quest.where_words(game, goal["to"])
        if goal["target"] and goal["target"] != game.player.pos:
            goal["steps"] = rules.distance(goal["target"], game.player.pos)
            if goal["steps"] > 1:
                goal["way"] = way_to(game.player.pos, goal["target"])
                if (goal["where"] or "").endswith("steps away"):       # the words say what the arrow shows
                    goal["where"] = "%s, %d steps away" % (goal["way"], goal["steps"])
    return goal


def _nightfall_goal(game, side):
    p = game.player
    if not game.castle_quest.completed:
        text = "Find the Shadow King's castle"
    elif not getattr(game, "throne_quest", None) or not game.throne_quest.completed:
        text = "Get to the throne room"
    else:
        text = "Defeat the Shadow King!"
    goal = _goal(text, title="Nightfall Hollow", more=side)
    if game.moon:
        goal["alert"] = "Moonrise! Follow the wisp" if game.wisp else "Moonrise! Stay near light"
    if not p.sunfang:
        goal["checks"] = [("Blade", min(p.diamonds, rules.SUNFANG_DIAMONDS), rules.SUNFANG_DIAMONDS),
                          ("Hilt", int(p.has_hilt), 1),
                          ("Sun Gem", min(p.sun_shards, rules.SUN_SHARDS_NEEDED), rules.SUN_SHARDS_NEEDED),
                          ("Beacons", len(game.beacons), rules.BEACONS_NEEDED)]
    return goal


def way_to(here, there):
    """Which of the 8 WAYS points from here to there (rows go down the map, so south is +row)."""
    angle = math.atan2(there[0] - here[0], there[1] - here[1])          # 0 = east, a quarter turn = south
    return WAYS[int(round(angle / (math.pi / 4))) % 8]


# ===========================================================================
# The "here" card: where you are, and the keys that do something right now
# ===========================================================================

def pause_key():
    """("P", "pause") once Phase 2 has its pause menu (phase2/pause.py), else what ESC does."""
    try:
        from phase2 import pause  # noqa: F401
        return ("P", "pause")
    except ImportError:
        return ("Esc", "title" if sys.platform == "emscripten" else "quit")     # a web page can't close itself


def footer_keys():
    return [("H", "keys"), pause_key()]


def place(game):
    """Where you are, in capitals: "HOME MEADOW: HOUSE"."""
    cave = game.cave
    if cave:
        if cave.is_throne_room:
            return "THE THRONE ROOM"
        if cave.is_castle:
            return "CASTLE LEVEL %d" % (cave.level + 1) if hasattr(cave, "level") else "THE CASTLE"
        return "IN THE CAVE"
    land = game.land_name(game.player.pos) or ("Nightfall Hollow" if game.world == 2 else "Here")
    return "%s: %s" % (land.upper(), game.tile_name(game.player.pos).upper())


def monster_near(game, how_far=FAR_MONSTER):
    here = game.player.pos
    return any(m.is_alive and rules.distance(m.pos, here) <= how_far for m in game.monsters)


def here(game, hints):
    """The keys that matter where you stand: [(key, words, tone)]. key None is a line with no key;
    tone "hot" is the one to notice (someone to talk to, food when you're hurt).

    hints is game.py's tables: {"tiles": TILE_HINTS, "cave": CAVE_HINTS, "castle": ..., "throne": ...}.
    In a cave you get the whole list (you need every move down there), on the map at most MAX_KEYS."""
    p = game.player
    hurt = p.health <= p.max_health // 2
    eat = [("E", "eat (%d food)" % p.food, "hot")] if hurt and p.food else []
    cave = game.cave
    if cave:
        hints = phase2_keys.HINTS           # (Phase 2's own: R fights, G digs and opens)
        table = hints["throne"] if cave.is_throne_room else hints["castle"] if cave.is_castle else hints["cave"]
        return eat + [tuple(line) + ("plain",) if len(line) == 2 else tuple(line) for line in table]
    keys = []
    who = people.next_to(game) if game.world == 1 else None
    talking = who is not None and game.here in people.TALK_FROM
    if talking:
        keys.append(("SPACE", "talk to " + who["name"].split(" the ")[0], "hot"))
    tile = list(hints["tiles"].get(game.here, []))
    if game.here == "G":                    # Phase 2's fields are snow, sand and swamp too: not always grass
        tile = [(key, words.replace("Open grass", "Open ground")) for key, words in tile]
    if game.here == "W" and p.pos in game.sunken_chests:
        tile.append(("SPACE", "dive for the sunken chest"))
    if game.here == "F":
        tile = [(key, "chop wood (%d left)" % game.wood_left(p.pos) if key == "T" else words) for key, words in tile]
    if game.here in "MS" and p.pos in game.cleared_mines:
        tile = [(None, "This mine is empty now")]
    elif game.here == "M" and p.pos in game.empty_mines:
        tile.append((None, "No diamond in this one"))
    if game.world == 1 and p.pos in getattr(game, "lookouts", []):
        tile = [("SPACE", "climb the lookout")]
    elif game.world == 1 and p.pos in getattr(game, "unlocked_waystones", ()) and len(game.unlocked_waystones) > 1:
        tile = [("SPACE", "travel by waystone")] + [line for line in tile if line[0] != "SPACE"]
    if talking:
        tile = [line for line in tile if line[0] != "SPACE"]        # SPACE talks, here
    keys += eat
    keys += [(key, words, "plain") for key, words in tile if key]
    if p.has_bow and p.arrows and monster_near(game):
        keys.append(("F", "shoot an arrow", "plain"))
    room = MAX_KEYS - len(keys)
    keys += [(None, words, "plain") for key, words in tile if not key][:max(0, min(room, 2))]
    return keys[:MAX_KEYS]


def all_keys():
    """Every key, for the H page: [(heading, [(key, words), ...]), ...]."""
    return [
        ("On the map", [("Arrows", "walk"), ("SPACE", "talk, rest, open, climb, go in"), ("E", "eat food"),
                        ("T", "chop wood (in a forest)"), ("C", "the Craft menu"), ("F", "shoot an arrow"),
                        ("Z", "wait a turn")]),
        ("In a fight", [("R", "attack (in the gold = PERFECT)"), ("X", "run away"), ("E", "eat food")]),
        ("In a cave", [("Arrows", "run"), ("SPACE", "jump (hold = higher)"), ("R", "swing your sword"),
                       ("G", "dig, open chests, pull levers"), ("Down + G", "dig the floor"), ("F", "shoot an arrow"),
                       ("Up/Down", "climb ladders and walls"), ("E", "eat food"), ("C", "the Craft menu")]),
        ("Any time", [("Q", "your quests"), ("B", "the big map"), ("L", "old messages"), ("H", "this page"),
                      pause_key(), ("M", "sound on or off"), ("N", "music on or off")]),
    ]


# ===========================================================================
# Messages: the newest one glows, the big ones pop up as toasts
# ===========================================================================

ICON_WORDS = [                  # the first word found in a message picks its picture
    ("light stone", "stone"), ("level up", "star"), ("gold", "coin"), ("diamond", "diamond"), ("berries", "apple"),
    ("food", "apple"), ("wood", "wood"), ("timber", "wood"), ("arrow", "bow"), ("bow", "bow"), ("sword", "sword"),
    ("pickaxe", "pickaxe"), ("armor", "shield"), ("chest", "chest"), ("waystone", "waystone"), ("xp", "star"),
]
KIND_ICONS = {"quest": "star", "loot": "chest", "good": "heart", "bad": "bang", "info": "talk"}


def icon_for(text, kind):
    """The little picture next to a message: from its words (gold: a coin), else from its kind."""
    if kind in ("loot", "quest"):
        low = text.lower()
        for word, icon in ICON_WORDS:
            if word in low:
                return icon
    return KIND_ICONS.get(kind, "talk")


def is_toast(text, kind):
    """Does this message pop up over the map too? Quests, level ups and real treasure do."""
    if kind not in TOAST_KINDS:
        return False
    return not (kind == "loot" and text.startswith(ROUTINE))


class Feed:
    """Remembers when each message came, so the newest can glow and the big ones can pop up.
    Its clock only ticks while you're playing (not under a story card or a menu), so nothing is missed."""

    def __init__(self):
        self.clock = 0.0
        self.seen = 0               # how many of game.messages we've looked at
        self.source = None          # the list we looked at (a new game has a new one)
        self.newest_at = None       # when the newest message came
        self.toasts = []            # [{"text", "kind", "age"}], oldest first

    def take(self, messages, skip=()):
        """Look for new messages. Returns the new ones: [(text, kind)].
        Ones that start with a word in `skip` get no toast (a card on screen is saying it already)."""
        if messages is not self.source or len(messages) < self.seen:
            self.source, self.seen, self.toasts, self.newest_at = messages, 0, [], None
        new = messages[self.seen:]
        self.seen = len(messages)
        if new:
            self.newest_at = self.clock
            for text, kind in new:
                if is_toast(text, kind) and not (skip and text.startswith(skip)):
                    self.toasts.append({"text": text, "kind": kind, "age": 0.0})
            self.toasts = self.toasts[-6:]              # a flood of news: only the last few
            for old in self.toasts[:-TOASTS_AT_ONCE]:   # ...and the ones in the way hurry off, so news is never late
                old["age"] = max(old["age"], TOAST_TIME - TOAST_FADE)
        return new

    def update(self, dt, live=True):
        if not live:
            return
        self.clock += dt
        for toast in self.toasts[:TOASTS_AT_ONCE]:      # the ones showing get older; the rest wait
            toast["age"] += dt
        self.toasts = [t for t in self.toasts if t["age"] < TOAST_TIME]

    def age(self):
        """Seconds since the newest message came (a big number if there are none)."""
        return 999.0 if self.newest_at is None else self.clock - self.newest_at

    def glow(self):
        """1 when a message has just come, fading to 0 after FRESH_TIME."""
        return max(0.0, min(1.0, 1.0 - self.age() / FRESH_TIME))

    def slide(self):
        """0 as the newest message starts to slide in, 1 once it's in place."""
        return max(0.0, min(1.0, self.age() / SLIDE_TIME))

    def showing(self):
        """The toasts on screen now: [(text, kind, how see-through: 1 = solid)]."""
        out = []
        for toast in self.toasts[:TOASTS_AT_ONCE]:
            left = TOAST_TIME - toast["age"]
            out.append((toast["text"], toast["kind"], max(0.0, min(1.0, toast["age"] / 0.2, left / TOAST_FADE))))
        return out


def log_lines(messages, n=LOG_LINES):
    """The last n messages, oldest first, for the message log (L)."""
    return list(messages[-n:])


# ===========================================================================
# The mouse: what's under it, and what a click does
# ===========================================================================

CLICKS = {"goal": "quests", "stones": "quests", "map": "map", "log": "log", "key:H": "keys"}


def tooltip(game, name):
    """(title, words) for the thing under the mouse, or None."""
    p = game.player
    if name.startswith("item:"):
        for item in pack(game):
            if item["id"] == name[5:]:
                return item["name"], item["tip"]
        return None
    if name.startswith("power:"):
        for power, times, what in powers(game):
            if power == name[6:]:
                return power + (" x%d" % times if times > 1 else ""), what[0].upper() + what[1:] + "."
        return None
    have, total = stones(game)
    words = {
        "lives": ("Lives: %d" % p.lives, "Out of health? You lose a life and wake up somewhere safe."),
        "health": ("Health: %d of %d" % (p.health, p.max_health), "Eat food (E) or rest in a house to get it back."),
        "xp": ("Level %d" % p.level, "%d more XP to level %d. Beat monsters, finish quests and explore caves."
               % (p.xp_needed - p.xp, p.level + 1)),
        "goal": ("What to do next", "Click here (or press Q) to see all your quests."),
        "stones": ("Light Stones: %d of %d" % (have, total), "One in every land. All %d wake the Portal!" % total),
        "map": ("The map", "The gold pin is where to go next. Click (or press B) for the big map."),
        "log": ("Messages", "Click (or press L) to read the old ones."),
        "key:H": ("Every key", "Click (or press H) to see all the keys."),
    }
    return words.get(name)
