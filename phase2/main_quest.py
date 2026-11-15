"""
THE MAIN QUEST of Phase 2 (stage 3a): seven Light Stones, one in every land, wake the Portal.

It's all written down in phase2/data/main_quest.json: the chapters (quests with "main": true, one
after another, each with the relic you get), and the story cards. phase2/quests.py runs the chapters
like any other quest; this file adds what's special about the main quest:

- a new game has the Phase 2 story cards (not the classic ones); talking to Rosa starts chapter 1
- finishing a chapter gives its Light Stone (a story card) and starts the next chapter
- the Portal stays shut until you have all 7 Light Stones (Classic's diamonds don't open it here)
- the quest log and Rosa say which way to go next ("north-east, 23 steps away")
- after the Shadow King, a short ending, and then you're back home, with your game saved, to keep exploring

What it remembers is plain data (game.quest_state, game.king_beaten, game.home_world), so it saves by itself.
This file knows nothing about graphics, so it's easy to test.
"""

import json
import os

import rules

from phase2 import quests, theme

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "main_quest.json")
RELIC_QUEST = "Find the 7 Light Stones"
# What going through the Portal changes (rules.Game.go_to_nightfall), so the home world can come back after the end
HOME_KEYS = ("world", "map", "rows", "cols", "start", "castle", "portal", "cave_plan", "cleared_mines", "cave_changes",
             "exited_mines", "diamond_mines", "empty_mines", "shard_mines", "sunken_chests", "glints", "river",
             "lodges", "secret_mines", "tree_wood", "mainland", "landmarks", "monsters", "quests", "moon", "wisp",
             "wisp_hops", "beacons", "wren_quest", "wren_thanked")

_data = None


def data():
    global _data
    if _data is None:
        with open(DATA_FILE, encoding="utf-8") as file:
            _data = json.load(file)
    return _data


def chapters():
    """The main quest's chapters, in order: [quest id, ...]."""
    order, qid = [], data()["first"]
    while qid and qid not in order:
        order.append(qid)
        qid = quests.get(qid).get("next")
    return order


def relic_chapters():
    return [qid for qid in chapters() if quests.get(qid).get("relic")]


def relics(game):
    """The Light Stones you have, in order."""
    return [quests.get(qid)["relic"] for qid in relic_chapters() if quests.status(game, qid) == "done"]


def relics_needed():
    return len(relic_chapters())


def portal_ready(game):
    return len(relics(game)) >= relics_needed() and not getattr(game, "king_beaten", False)


def current(game):
    """The chapter you're on (its quest id), or None once it's all done."""
    for qid in chapters():
        if quests.status(game, qid) == "active":
            return qid
    return None


def story(name, **words):
    """Story cards from main_quest.json, with {relic}, {count} and {game} (theme.GAME_NAME) filled in ({name} is filled in by game.tell)."""
    words.setdefault("game", theme.GAME_NAME)
    cards = []
    for title, text, picture in data()["story"][name]:
        for key, value in words.items():
            title, text = title.replace("{%s}" % key, str(value)), text.replace("{%s}" % key, str(value))
        cards.append((title, text, picture))
    return cards


def line(name, game):
    return data()["story"][name].replace("{count}", str(len(relics(game))))


# ===========================================================================
# A new game, and a loaded one
# ===========================================================================

def set_up(game):
    """A new Phase 2 game: the Phase 2 story cards, a Light Stone counter on the panel, and chapter 1."""
    game.king_beaten = False
    game.home_world = None
    game.story = []
    game.tell(story("opening"))
    # Classic's welcome ("Defeat 5 monsters and mine 3 diamonds...") isn't this game's goal
    game.messages = [m for m in game.messages if not m[0].startswith(("Welcome, ", "Not every cave has a diamond"))]
    game.log("Welcome, %s! Find the 7 Light Stones, wake the Portal and stop the Shadow King!" % game.player.name, "quest")
    game.log("Talk to Rosa the Guide, next to your house. She knows where the first one is!", "quest")
    fix_panel_quests(game)                  # (chapter 1 starts when you first talk to Rosa: people.json)


def after_load(game):
    """A save from before stage 3a gets what the main quest needs. (Rosa starts chapter 1 when you talk to her.)"""
    if not hasattr(game, "king_beaten"):
        game.king_beaten = False
    if not hasattr(game, "home_world"):
        game.home_world = None
    if game.world == 1:
        fix_panel_quests(game)


def fix_panel_quests(game):
    """The panel's quests: Defeat 5 monsters and the Light Stones (Classic's "Mine 3 diamonds" doesn't open
    this Portal: Sunfang still needs diamonds, but you find them in Nightfall Hollow)."""
    relic_quest = next((q for q in game.quests if q.description == RELIC_QUEST), None)
    if relic_quest is None:
        relic_quest = rules.Quest(RELIC_QUEST, relics_needed())
        game.quests = [q for q in game.quests if q is not getattr(game, "diamond_quest", None)] + [relic_quest]
    relic_quest.progress = len(relics(game))


def main_words_first(everyone):
    """A person's words that move the main quest on (advance_quest/finish_quest a main chapter) go before
    anything else they say, so a side quest's words (people_side.json, put first) never hide them."""
    def moves_main(variant):
        return any(effect.split(":")[0] in ("advance_quest", "finish_quest") and effect.split(":")[1] in chapters()
                   for effect in variant.get("do", []))
    for who in everyone:
        start = who.get("talk", {}).get("start")
        if isinstance(start, list):
            who["talk"]["start"] = [v for v in start if moves_main(v)] + [v for v in start if not moves_main(v)]


# ===========================================================================
# Chapters
# ===========================================================================

def chapter_done(game, qid):
    """quests.finish() calls this when a main chapter is done: its Light Stone, then the next chapter."""
    quest = quests.get(qid)
    if quest.get("relic"):
        have = relics(game)
        game.log("You got %s! (%d of %d Light Stones)" % (quest["relic"], len(have), relics_needed()), "quest")
        game.tell(story("relic", relic=quest["relic"][0].upper() + quest["relic"][1:], count=len(have)))
        game.effect("land", text=quest["relic"].upper(), sub="%d of %d Light Stones" % (len(have), relics_needed()))
        if game.world == 1:
            fix_panel_quests(game)
        if len(have) >= relics_needed():
            game.log("All 7 Light Stones! The Portal on Portal Island is awake. Row out to it!", "quest")
            game.tell(story("all_relics"))
    if quest.get("next") and quests.status(game, quest["next"]) == "new":
        quests.start(game, quest["next"])


def wants_you(game, pid):
    """Is the main quest's step right now "go and talk to this person"? (They get a "!" over them.)"""
    first = data()["first"]
    if quests.status(game, first) == "new":
        return quests.get(first).get("giver") == pid           # Rosa starts it all
    qid = current(game)
    if qid is None:
        return False
    one = quests.get(qid)["steps"][quests.step(game, qid)]
    return isinstance(one, dict) and not one.get("goal") and one.get("to") == "person:" + pid


def next_step(game):
    """What to do next, in words (Rosa says it when you ask her where to go)."""
    qid = current(game)
    if quests.status(game, data()["first"]) == "new":
        return "Talk to Rosa the Guide, next to your house"
    if qid is None:
        return "You did it all! Now go wherever you like, and help anyone who still needs you"
    return quests.step_text(game, qid)


# ===========================================================================
# Which way to go
# ===========================================================================

def _land_box(game, land):
    for box in game.atlas.lands:
        if box[0] == land:
            return box
    return None


def target(game, to):
    """The square a step's "to" points at, or None."""
    kind, _, name = to.partition(":")
    here = game.player.pos
    if kind == "person":
        return getattr(game, "people", {}).get(name)
    if kind == "village":
        for village, spot, _ in game.atlas.villages:
            if village == name:
                return spot
        return None
    if kind == "portal":
        return game.portal
    if kind == "land":
        box = _land_box(game, name)
        if box is None:
            return None
        if game.land_name(here) == name:
            return here
        return ((box[1] + box[3]) // 2, (box[2] + box[4]) // 2)
    if kind in ("mine", "lookout"):
        if kind == "mine":
            mines = [m for m in game.cave_plan if game.tile(m) == "M" and game.land_name(m) == name]
            spots = [m for m in mines if m not in game.exited_mines] or mines    # one you haven't beaten yet
        else:
            spots = list(game.atlas.lookouts)
        spots = [s for s in spots if game.land_name(s) == name]
        return min(spots, key=lambda s: (rules.distance(here, s), s)) if spots else None
    return None


def where_words(game, to):
    """Which way to go, like "north-east, 23 steps away". None if there's no way to say (Nightfall Hollow...)."""
    if game.world != 1 or game.cave:
        return None
    spot = target(game, to)
    if spot is None:
        return None
    if spot == game.player.pos or rules.distance(spot, game.player.pos) <= 1:
        return "right here!"
    if to.startswith("land:") and game.land_name(game.player.pos) == to[5:]:
        return "you're there!"
    way = rules.compass(game.player.pos, spot)
    if way == "right here":
        return "close by!"
    return "%s, %d steps away" % (way, rules.distance(spot, game.player.pos))


# ===========================================================================
# The Portal, Nightfall Hollow and the end
# ===========================================================================

def at_portal(game):
    """You step onto the Portal (or press SPACE on it). Returns True if it takes you through."""
    if game.king_beaten:
        game.log(line("after_the_end", game), "quest")
        return False
    if not portal_ready(game):
        game.log(line("portal_shut", game), "quest")
        return False
    game.log("The seven Light Stones blaze, and the Portal swirls open and pulls you through!", "quest")
    return True


def leave_home(game):
    """Just before the Portal takes you to Nightfall Hollow: remember the home world, to come back to after the end."""
    game.home_world = {key: getattr(game, key) for key in HOME_KEYS if hasattr(game, key)}


def the_end(game):
    """You beat the Shadow King (Phase 2 only): the ending cards, then home, with the game saved."""
    if game.king_beaten:
        return
    quests.notice(game, "king")
    game.king_beaten = True
    game.tell(story("ending"))
    come_home(game)
    game.log("The adventure goes on! Explore anywhere, and help the people who still need you.", "quest")
    game.autosave()


def come_home(game):
    """Back to the home world, at your house, the way you left it."""
    home = getattr(game, "home_world", None)
    if not home:
        return False
    for key, value in home.items():
        setattr(game, key, value)
    game.home_world = None
    game.cave = None
    game.battle = None
    game.forging = False
    game.player.pos = game.start
    game.seen = set()
    game.reveal()
    fix_panel_quests(game)
    from phase2 import people
    people.keep_monsters_off(game)
    game.effect("new_world")
    return True
