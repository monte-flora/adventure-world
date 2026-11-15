"""
SIDE QUESTS for Phase 2 (stage 3b): the little jobs townsfolk give you, about 2 in every village.

They are written down in two files, so they're easy to change:

    phase2/data/side_quests.json   the quests (quests.py reads them next to quests.json)
    phase2/data/people_side.json   new quest givers and lost things (people.py reads them next to
                                   people.json), and extra words for people who live there already

A side quest is like the ones in quests.json, but a step can also be a GOAL the game checks by
itself (no talking needed). Then it's {"text": ..., "goal": {...}} instead of plain words:

    {"kind": "beat", "monster": "Spider", "count": 4}   beat 4 Spiders (anywhere, day or night)
    {"kind": "lookout", "land": "Frost Peaks"}          climb a lookout tower in that land
    {"kind": "chest", "land": "Frost Peaks"}            open a hidden treasure chest in that land

When a goal is done, the quest goes on to its next step by itself.

A reward can give more than quests.py's gold, XP, food, arrows and wood:

    "great_sword": 1    a Great sword            "armor": 1    new armor, on at once
    "life": 1           an extra life            "treasure": "Murk Swamp"   shows you the hidden
                                                                            chest a lookout there sees

A quest with "choice_rewards" lets you pick: the words do "finish_quest_with:quest:choice".

people_side.json:
    "people":    new people, written like the ones in people.json
    "more_talk": {person id: {"start": [variants tried before their own], "nodes": {new nodes},
                  "choices": {node: [choices put in before their last choice]}}}

Conditions the words can check here: "been_to:Land" (you've walked in that land),
"has_great" (you carry a Great sword) and "goal_count:quest:n" (you beat n monsters for it).

The game remembers how many monsters you beat for a quest in its quest_state entry ("count"),
so it saves with everything else. This file knows nothing about graphics.
"""

import copy
import json
import os

import rules

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
QUEST_FILE = os.path.join(DATA, "side_quests.json")
PEOPLE_FILE = os.path.join(DATA, "people_side.json")
GOALS = ("beat", "lookout", "chest")

# Two little pictures for things you find lying around (sprites.PEOPLE_ART gets them).
LOST_BAG = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "......kkkk......",
    ".....kNNNNk.....",
    "......kYYk......",
    ".....knnnnk.....",
    "....knnnnnnk....",
    "...knnYnnnnnk...",
    "...knnnnnnYnk...",
    "...knnnnnnnnk...",
    "....knnnnnnk....",
    ".....kkkkkk.....",
    "................",
]
FROG = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "....kkk..kkk....",
    "...kwkgkkgwkk...",
    "...kkkggggkkk...",
    "...kggggggggk...",
    "..kgggrrrrgggk..",
    "..kggggggggggk..",
    "..kGgjjjjjjgGk..",
    ".kgGkjjjjjjkGgk.",
    ".kgk.kkkkkk.kgk.",
    "..k..........k..",
    "................",
]
TOY_BOAT = [
    "................",
    "................",
    "................",
    ".......k........",
    ".......kk.......",
    ".......kwk......",
    ".......kwwk.....",
    ".......kwwwk....",
    ".......kwwwwk...",
    ".......kkkkkkk..",
    "..kkkkkkkkkkkkk.",
    "..krrrrrrrrrrk..",
    "...krrrrrrrrk...",
    "....kkkkkkkk....",
    "................",
    "................",
]
ART = {"lost_bag": LOST_BAG, "frog": FROG, "toy_boat": TOY_BOAT}


# ===========================================================================
# Reading the files
# ===========================================================================

def _read(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def load_quests():
    """The side quests, made to look like quests.json's: "steps" are words, and "goals" says which
    steps the game checks by itself (None: the dialogue moves it on)."""
    found = {}
    for qid, quest in _read(QUEST_FILE)["quests"].items():
        quest = dict(quest)
        steps, goals = [], []
        for n, step in enumerate(quest.get("steps", [])):
            if isinstance(step, str):
                steps.append(step)
                goals.append(None)
                continue
            goal = step.get("goal")
            if goal and goal.get("kind") not in GOALS:
                raise ValueError("Side quest %r, step %d: there's no goal called %r (only %s)"
                                 % (qid, n + 1, goal.get("kind"), ", ".join(GOALS)))
            steps.append(step["text"])
            goals.append(goal)
        quest["steps"], quest["goals"], quest["side"] = steps, goals, True
        found[qid] = quest
    return found


def add_people(everyone):
    """people.py's list of everyone, with the side-quest people and words added (a new list)."""
    data = _read(PEOPLE_FILE)
    everyone = copy.deepcopy(everyone)
    by_id = {who["id"]: who for who in everyone}
    for pid, more in data.get("more_talk", {}).items():
        if pid not in by_id:
            raise ValueError("people_side.json adds words for %r, but there's nobody called that" % pid)
        talk = by_id[pid]["talk"]
        start = talk["start"] if isinstance(talk["start"], list) else [talk["start"]]
        talk["start"] = list(more.get("start", [])) + start
        for name, node in more.get("nodes", {}).items():
            if name in talk:
                raise ValueError("people_side.json: %s already has a node called %r" % (pid, name))
            talk[name] = node
        for name, choices in more.get("choices", {}).items():
            for variant in talk[name] if isinstance(talk[name], list) else [talk[name]]:
                old = variant.setdefault("choices", [])
                variant["choices"] = old[:-1] + list(choices) + old[-1:]
    return everyone + list(data.get("people", []))


# ===========================================================================
# Goals the game checks by itself
# ===========================================================================

def _goal(game, qid):
    from phase2 import quests
    n = quests.step(game, qid)
    if n is None:
        return None
    goals = quests.get(qid).get("goals") or []
    return goals[n] if n < len(goals) else None


def _land_spots(game, land, spots):
    return [s for s in spots if (game.atlas.land_at(s) or (None,))[0] == land]


def goal_done(game, qid, goal):
    entry = game.quest_state[qid]
    kind = goal["kind"]
    if kind == "beat":
        return entry.get("count", 0) >= goal["count"]
    if kind == "lookout":
        return bool(_land_spots(game, goal["land"], game.lookouts_climbed))
    if kind == "chest":
        if "chests" not in entry:               # the chests that are still shut when this step starts
            entry["chests"] = _land_spots(game, goal["land"], rules.tiles_of(game.map, "T"))
        return not entry["chests"] or any(game.tile(s) != "T" for s in entry["chests"])
    return False


def check(game):
    """After every turn: any side quest whose goal is done goes on to its next step."""
    from phase2 import quests
    if game.world != 1:
        return
    for qid in quests.active(game):
        goal = _goal(game, qid)
        if goal and goal_done(game, qid, goal):
            entry = game.quest_state[qid]
            entry.pop("count", None)
            entry.pop("chests", None)
            quests.advance(game, qid)
            after = _goal(game, qid)
            if after and after["kind"] == "chest":     # make sure you can see the chest to dig up
                show_chest(game, after["land"], "You spot a hidden chest in %s, to the %s. Go and dig it up!")


def monster_beaten(game, monster):
    """A monster is beaten: it counts for every side quest that wants that kind."""
    from phase2 import quests
    kind = getattr(monster, "base_kind", monster.kind)
    for qid in quests.active(game):
        goal = _goal(game, qid)
        if goal and goal["kind"] == "beat" and goal["monster"] == kind:
            done = quests.count_up(game, qid)          # (the same counter the main quest uses)
            if done < goal["count"]:
                game.log("%s: %d of %d %ss beaten." % (quests.get(qid)["title"], done, goal["count"],
                                                       kind), "quest")
    check(game)


# ===========================================================================
# More rewards
# ===========================================================================

def give_great_sword(game, n):
    p = game.player
    got = 0
    for _ in range(n):
        if len(p.swords) < rules.MAX_SWORDS:
            p.swords.append(rules.make_sword("great"))
            got += 1
    return ("a Great sword" if got == 1 else "%d Great swords" % got) if got else "a Great sword (no room to carry it!)"


def give_armor(game, n):
    game.player.put_on_armor()
    return "new armor"


def give_life(game, n):
    p = game.player
    p.lives = min(rules.MAX_LIVES, p.lives + n)
    return "an extra life" if n == 1 else "%d extra lives" % n


def show_chest(game, land, words):
    """Show the hidden chest nearest a lookout in that land. Returns its spot (None: none left)."""
    towers = _land_spots(game, land, game.lookouts) or [game.player.pos]
    hidden = _land_spots(game, land, game.hidden_chests())
    if not hidden:
        return None
    spot = min(hidden, key=lambda s: (min(rules.distance(s, t) for t in towers), s))
    game.found_chests.add(spot)
    game.effect("tile", pos=spot)
    game.effect("sparkle", pos=spot)
    game.log(words % (land, rules.compass(game.player.pos, spot)), "loot")
    return spot


def give_treasure(game, land):
    if show_chest(game, land, "A treasure map! It shows a hidden chest in %s, to the %s. It's on your map now.") is None:
        return "a treasure map (but every chest in %s is found already)" % land
    return "a treasure map of %s" % land


EXTRA_REWARDS = {"great_sword": give_great_sword, "armor": give_armor, "life": give_life, "treasure": give_treasure}


def finish_with(talk, conversation, qid, choice):
    """A choice in the words picks the reward: "finish_quest_with:quest:choice"."""
    from phase2 import quests
    rewards = quests.get(qid).get("choice_rewards", {})
    if choice not in rewards:
        raise ValueError("Quest %r has no reward called %r" % (qid, choice))
    talk.game.people_flags.add("%s:%s" % (qid, choice))
    quests.finish(talk.game, qid, reward=rewards[choice])


# ===========================================================================
# Plugging in (quests.py and people.py call this once)
# ===========================================================================

_ready = False


def register():
    global _ready
    if _ready:
        return
    _ready = True
    import sprites
    from phase2 import people, quests
    for name, art in ART.items():
        sprites.PEOPLE_ART.setdefault(name, art)
    quests.EXTRA_REWARDS.update(EXTRA_REWARDS)
    people.CONDITIONS.update({
        "been_to": lambda t, land: land in t.game.lands_seen,
        "has_great": lambda t: any(s.quality == "great" for s in t.game.player.swords),
        "goal_count": lambda t, q, n: t.game.quest_state.get(q, {}).get("count", 0) >= int(n),
    })
    people.EFFECTS["finish_quest_with"] = finish_with
