"""
PEOPLE in the Phase 2 world: who lives where, talking to them, and what their words can do.

Everyone is written down in phase2/data/people.json (that file says how). When a game starts,
place() puts each person on the map: on the square their "place" says, or on the nearest open
square in the same land if that one isn't free (so redrawing a land never strands anyone). Nobody
stands where they would block the way to somewhere else.

Walk into someone (or press SPACE next to them) and you talk: game.talk is then a
dialogue.Conversation, and phase2/draw_people.py shows it.

Their dialogue can check CONDITIONS and do EFFECTS (see the two lists below). Stage 3 can add
more: CONDITIONS["name"] = function(talk, *args) -> True/False, EFFECTS["name"] = function(talk, *args).

What the game remembers (plain data, so phase2/save.py saves it by itself):
    game.gold           your gold coins
    game.people_talked  the ids of everyone you've talked to
    game.people_flags   little notes the dialogue can set and check ("set_flag:...", "flag:...")
    game.quest_state    how far you got in every quest (phase2/quests.py)
    game.shop_stock     what's left in every shop (phase2/shop.py)
    game.people         where everyone stands (worked out again when you load on the home world,
                        in case people.json changed)

This file knows nothing about graphics, so it's easy to test.
"""

import collections
import json
import os

import rules

from phase2 import dialogue, quests, shop, world_map

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "people.json")
OPEN_GROUND = "GB"             # people stand on grass or reeds (a path square only if there's nothing else)
TALK_FROM = "GRBFI"             # SPACE talks to someone next to you from these squares (on a Mine it climbs down...)

_people = None


def all_people():
    """Everyone in people.json, as a list. (Read once, then remembered.)"""
    global _people
    if _people is None:
        with open(DATA_FILE, encoding="utf-8") as file:
            _people = json.load(file)["people"]
        from phase2 import side_steps                   # stage 3b: side-quest people (people_side.json)
        side_steps.register()
        _people = side_steps.add_people(_people)
        from phase2 import main_quest                   # stage 3a: main-quest words come first
        main_quest.main_words_first(_people)
        ids = [p["id"] for p in _people]
        if len(set(ids)) != len(ids):
            raise ValueError("Two people in people.json (or people_side.json) have the same id")
    return _people


def person(pid):
    for p in all_people():
        if p["id"] == pid:
            return p
    raise KeyError("There's nobody called %r in people.json" % pid)


# ===========================================================================
# Setting up, and putting everyone on the map
# ===========================================================================

def set_up(game):
    """A new Phase 2 game: no quests yet, full shops, a little gold, and everyone on the map."""
    game.gold = shop.start_gold()
    game.people_talked = set()
    game.people_flags = set()
    game.quest_state = {}
    game.shop_stock = {}
    game.talk = None
    place(game)


def after_load(game):
    """A game just came back from a save: fill in anything an older save didn't have, and place everyone."""
    for name, empty in (("gold", shop.start_gold), ("people_talked", set), ("people_flags", set),
                        ("quest_state", dict), ("shop_stock", dict)):
        if not hasattr(game, name):
            setattr(game, name, empty())
    game.talk = None
    if game.world == 1:
        place(game)                           # (people.json may have changed since it was saved)
    elif not hasattr(game, "people"):
        game.people = {}


_origins = {}


def land_origins(folder=None):
    """Every land's top-left corner on the big map (its "at:" line): name -> (row, col)."""
    key = folder or world_map.WORLD_FOLDER
    if key not in _origins:
        found = {}
        for path in world_map.land_files(folder):
            with open(path, encoding="utf-8") as file:
                settings, _ = world_map.read_land(file.read(), path)
            found[settings["name"]] = (settings["top"], settings["left"])
        _origins[key] = found
    return _origins[key]


def wanted_spot(game, who):
    """The square a person's "place" points at on the big map (it might not be open ground), and its land.

    "place" is either {"village": "Meadowbrook", "row": 1, "col": -2}: that many squares from the village's
    open square (atlas.villages, from the "village:" lines in levels/world/), or
    {"land": "Home Meadow", "row": 4, "col": 5}: a square in that land's own file (row 0, column 0 is its top-left)."""
    place_ = who["place"]
    dr, dc = place_.get("row", 0), place_.get("col", 0)
    if "village" in place_:
        for name, (r, c), land in getattr(game.atlas, "villages", []):
            if name == place_["village"]:
                return (r + dr, c + dc), land
        raise ValueError("%s lives in the village %r, but there's no village with that name"
                         % (who["name"], place_["village"]))
    land = place_["land"]
    origin = land_origins().get(land)
    if origin is None:                        # (a test's own little map: use the land's top-left square)
        box = [l for l in game.atlas.lands if l[0] == land]
        if not box:
            raise ValueError("%s lives in %r, but there's no land with that name" % (who["name"], land))
        origin = (box[0][1], box[0][2])
    return (origin[0] + dr, origin[1] + dc), land


def walk_reach(game, blocked=(), letters=rules.WALKABLE):
    """Every square you can walk to from home (no boat), if nobody can walk through `blocked`.
    A gate (stage 2a: rock until you're strong enough) counts as open: it opens one day."""
    gates = getattr(game.atlas, "gates", {})
    seen, todo = {game.start}, collections.deque([game.start])
    while todo:
        r, c = todo.popleft()
        for dr, dc in rules.DIRECTIONS.values():
            spot = (r + dr, c + dc)
            if (spot not in seen and spot not in blocked and game.in_bounds(spot)
                    and (game.map[spot[0]][spot[1]] in letters or spot in gates)):
                seen.add(spot)
                todo.append(spot)
    return seen


def place(game):
    """Put everyone on the map: game.people = {person id: (row, col)}."""
    game.people = {}
    reach = walk_reach(game)
    taken = {game.start}
    for who in all_people():
        want, land = wanted_spot(game, who)
        spot = free_spot(game, land, want, reach, taken)
        if spot is None:                      # (a land you can only get to by boat)
            by_boat = {s for s in walk_reach(game, letters=rules.WALKABLE + "W=") if game.map[s[0]][s[1]] != "W"}
            spot = free_spot(game, land, want, by_boat - taken, taken, check_way=False)
        if spot is None:
            raise ValueError("There's no open ground for %s in %s" % (who["name"], land))
        game.people[who["id"]] = spot
        taken.add(spot)
        reach = reach - {spot}
    keep_monsters_off(game)


def free_spot(game, land, want, reach, taken, check_way=True):
    """The nearest open, reachable square to want, in that land, where standing doesn't block the way."""
    for ground in (OPEN_GROUND, OPEN_GROUND + "R"):
        for spot in sorted(reach, key=lambda s: (rules.distance(s, want), s)):
            here = game.atlas.land_at(spot)
            if (spot in taken or game.map[spot[0]][spot[1]] not in ground or here is None or here[0] != land
                    or any(rules.distance(spot, t) < 2 for t in taken if t != game.start)):
                continue
            if not check_way or len(walk_reach(game, taken | {spot})) == len(reach) - 1:   # nobody gets cut off
                return spot
    return None


def keep_monsters_off(game):
    """Stage 2c's monsters never step on (or start on) a person's square."""
    spots = set(getattr(game, "people", {}).values())
    if not spots or game.world != 1:
        return
    if hasattr(game, "safe_squares"):
        game.safe_squares = set(game.safe_squares) | spots
    game.monsters = [m for m in game.monsters if tuple(m.pos) not in spots]


# ===========================================================================
# Who's where
# ===========================================================================

def shown(game, who):
    """Can you see this person right now? (Only on the home world, and only if their "show_if" is true.)"""
    if game.world != 1 or who["id"] not in getattr(game, "people", {}):
        return False
    talk = Talk(game, who)
    return all(talk.check(c) for c in who.get("show_if", []))


def people_here(game):
    """[(person, (row, col)), ...] for everyone you can see."""
    return [(who, game.people[who["id"]]) for who in all_people() if shown(game, who)]


def person_at(game, pos):
    for who, spot in people_here(game):
        if spot == pos:
            return who
    return None


def next_to(game):
    """Someone right next to you (the one you're facing first), or None."""
    p = game.player
    ways = [p.facing] + [w for w in rules.DIRECTIONS if w != p.facing]
    for way in ways:
        dr, dc = rules.DIRECTIONS[way]
        who = person_at(game, (p.pos[0] + dr, p.pos[1] + dc))
        if who:
            return who
    return None


def bump(game, direction):
    """You walk into someone: you talk instead of moving. Returns True if there was someone there."""
    if game.cave or game.battle or game.world != 1:
        return False
    dr, dc = rules.DIRECTIONS[direction]
    who = person_at(game, (game.player.pos[0] + dr, game.player.pos[1] + dc))
    if who is None:
        return False
    game.player.facing = direction
    start_talk(game, who)
    return True


def talk_next_to(game):
    """SPACE next to someone: talk to them. Returns True if there was someone."""
    if game.cave or game.battle or game.world != 1:
        return False
    who = next_to(game)
    if who is None:
        return False
    start_talk(game, who)
    return True


def start_talk(game, who):
    talk = Talk(game, who)
    game.talk = dialogue.Conversation(who, talk.check, talk.run, talk.words)
    game.talk.talk = talk
    game.people_talked.add(who["id"])
    if game.talk.done:                     # they had nothing to say
        game.talk = None
    return game.talk


# ===========================================================================
# What their words can check and do
# ===========================================================================

class Talk:
    """One person's words: the conditions they check and the effects they do."""

    def __init__(self, game, who):
        self.game = game
        self.who = who
        self.first_time = who["id"] not in getattr(game, "people_talked", set())

    def check(self, condition):
        flip = condition.startswith("not:")
        if flip:
            condition = condition[4:]
        name, *args = condition.split(":")
        if name not in CONDITIONS:
            raise ValueError("%s's words check %r, but there's no condition called that" % (self.who["name"], name))
        return bool(CONDITIONS[name](self, *args)) != flip

    def run(self, effect, conversation=None):
        name, *args = effect.split(":")
        if name not in EFFECTS:
            raise ValueError("%s's words do %r, but there's no effect called that" % (self.who["name"], name))
        EFFECTS[name](self, conversation, *args)

    def words(self):
        """The {words} a page can have in it."""
        game, p = self.game, self.game.player
        words = {"name": p.name, "gold": game.gold, "wood": p.wood, "food": p.food, "arrows": p.arrows,
                 "person": self.who["name"], "first_mine": first_mine_words(game),
                 "repair_price": shop.repair_price(), "repair_problem": shop.repair_problem(game) or ""}
        for word, find in WORDS.items():          # more {words} (stage 3: the main quest's next step...)
            words[word] = find(game)
        return words


def amount_of(game, what):
    if what == "gold":
        return game.gold
    if what == "swords":
        return len(game.player.swords)
    return getattr(game.player, what)


def _take(game, what, n):
    if what == "gold":
        game.gold -= n
    else:
        setattr(game.player, what, getattr(game.player, what) - n)


def _open(talk, conversation, what):
    conversation.then = (what, talk.who["id"])     # draw_people.py opens it once the talk ends
    conversation.end()


def _main_next(game):
    from phase2 import main_quest
    return main_quest.next_step(game)


def _relic_count(game):
    from phase2 import main_quest
    return len(main_quest.relics(game))


WORDS = {                                   # {word}: function(game) -> what it says
    "main_next": _main_next,                # the main quest's next step, and which way to go
    "relics": _relic_count,                 # how many Light Stones you have
}

CONDITIONS = {
    "first_time": lambda t: t.first_time,
    "quest_new": lambda t, q: quests.status(t.game, q) == "new",
    "quest_active": lambda t, q: quests.status(t.game, q) == "active",
    "quest_done": lambda t, q: quests.status(t.game, q) == "done",
    "quest_step": lambda t, q, n: quests.step(t.game, q) == int(n),
    "quest_at_least": lambda t, q, n: (quests.status(t.game, q) == "done"
                                       or (quests.step(t.game, q) or 0) >= int(n) and quests.status(t.game, q) == "active"),
    "has": lambda t, what, n: amount_of(t.game, what) >= int(n),
    "flag": lambda t, name: name in t.game.people_flags,
    "can_repair": lambda t: shop.repair_problem(t.game) is None,
}

EFFECTS = {
    "start_quest": lambda t, c, q: quests.start(t.game, q),
    "advance_quest": lambda t, c, q: quests.advance(t.game, q),
    "finish_quest": lambda t, c, q: quests.finish(t.game, q),
    "give": lambda t, c, what, n: quests.give_reward(t.game, {what: int(n)}),
    "take": lambda t, c, what, n: _take(t.game, what, int(n)),
    "set_flag": lambda t, c, name: t.game.people_flags.add(name),
    "open": _open,                          # open:shop or open:forge
    "repair": lambda t, c: shop.repair(t.game),
}


def first_mine_words(game):
    """Where the Mine nearest home is, in words, like "south-east of your house, 6 steps away"."""
    mines = [spot for spot in game.cave_plan if game.map[spot[0]][spot[1]] == "M"]
    if not mines:
        return "out there somewhere"
    mine = min(mines, key=lambda m: (rules.distance(m, game.start), m))
    way = rules.compass(game.start, mine)
    if way == "right here":
        return "right next to your house"
    return "%s of your house, %d steps away" % (way, rules.distance(mine, game.start))


# ===========================================================================
# The blacksmith's anvil, and gold
# ===========================================================================

def smith_next_to(game):
    """Is a blacksmith standing right next to you?"""
    if game.world != 1 or game.cave:
        return False
    return any(who.get("role") == "smith" and rules.distance(spot, game.player.pos) == 1
               for who, spot in people_here(game))


def anvil_problem(game):
    """At the blacksmith's anvil you can forge anywhere (not just in the forest)."""
    if game.battle or game.over:
        return "Not now!"
    if len(game.player.swords) >= rules.MAX_SWORDS:
        return "You can only carry %d swords." % rules.MAX_SWORDS
    return None


def gold_coins(game, words, xp):
    """Gold coins in a chest (rules.give_loot's "+N XP") are real gold in Phase 2: you get both."""
    if words == "+%d XP" % xp:
        game.gold += xp
        game.log("You put %d gold coins in your pouch. You have %d gold." % (xp, game.gold), "loot")
        return "+%d gold" % xp
    return words
