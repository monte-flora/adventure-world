"""
QUESTS for Phase 2: the side quests people give you, and the main quest's chapters
(phase2/data/main_quest.json, with "main": true: see phase2/main_quest.py).

Every quest is written down in phase2/data/quests.json:

    "farmer_wood": {
        "title": "Wood for the Winter",          what the quest log (Q) calls it
        "giver": "farmer_bo",                    who gives it (a person's id in people.json)
        "steps": ["Bring Farmer Bo 10 wood"],    what to do, one step after another
        "reward": {"gold": 25, "xp": 15, "food": 1}
    }

The game only remembers how far you got: game.quest_state = {quest id: {"status": ..., "step": n}}
("active" or "done"). That's plain data, so it saves by itself (phase2/save.py).

    start(game, id)     the quest begins (step 0)
    advance(game, id)   on to the next step (after the last step, it's finished)
    finish(game, id)    done! You get the reward.

People start, advance and finish quests in their dialogue (see phase2/people.py).

A step can also be {"text": "Defeat 3 Skeletons", "goal": "defeat:Old Ruins:Skeleton:3", "to": "land:Old Ruins"}:
the goal finishes the step by itself when it happens (GOALS, at the bottom, says which there are;
phase2/world.py calls notice() when one happens), and "to" adds which way to go in the quest log.
This file knows nothing about graphics, so it's easy to test.
"""

import json
import os

import rules

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "quests.json")
MAIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "main_quest.json")   # stage 3a
REWARDS = ("gold", "xp", "food", "arrows", "wood")      # what a reward can give you
EXTRA_REWARDS = {}      # more kinds of reward: name -> function(game, amount) -> words (side_steps.py)

_quests = None


def all_quests():
    """Every quest in quests.json: id -> its details. (Read once, then remembered.)"""
    global _quests
    if _quests is None:
        with open(DATA_FILE, encoding="utf-8") as file:
            _quests = json.load(file)
        from phase2 import side_steps                   # stage 3b: the side quests (side_quests.json)
        side_steps.register()
        _quests.update(side_steps.load_quests())
        with open(MAIN_FILE, encoding="utf-8") as file:         # stage 3a: the main quest's chapters
            _quests.update(json.load(file)["quests"])
        for qid, quest in _quests.items():
            check(qid, quest)
    return _quests


def check(qid, quest):
    """Say clearly what's wrong with a quest written wrong in quests.json."""
    for key in ("title", "steps"):
        if key not in quest:
            raise ValueError("Quest %r in quests.json needs a %r" % (qid, key))
    if not quest["steps"]:
        raise ValueError("Quest %r needs at least one step" % qid)
    for n, one in enumerate(quest["steps"]):
        if isinstance(one, dict):
            if "text" not in one:
                raise ValueError("Quest %r: step %d needs a 'text'" % (qid, n + 1))
            if one.get("goal") and one["goal"].split(":")[0] not in GOALS:
                raise ValueError("Quest %r: step %d has a goal %r, but there's no goal like that (only %s)"
                                 % (qid, n + 1, one["goal"], ", ".join(GOALS)))
    for what in quest.get("reward", {}):
        if what not in REWARDS and what not in EXTRA_REWARDS:
            raise ValueError("Quest %r: a reward can't give %r (only %s)" % (qid, what, ", ".join(REWARDS)))


def get(qid):
    if qid not in all_quests():
        raise KeyError("There's no quest called %r in quests.json" % qid)
    return all_quests()[qid]


def state(game):
    if not hasattr(game, "quest_state"):
        game.quest_state = {}
    return game.quest_state


# ----- how far you got ---------------------------------------------------------------

def status(game, qid):
    """'new' (not started), 'active' or 'done'."""
    return state(game).get(qid, {}).get("status", "new")


def step(game, qid):
    """Which step of an active quest you're on (0 is the first). None if it isn't active."""
    entry = state(game).get(qid)
    return entry["step"] if entry and entry["status"] == "active" else None


def step_text(game, qid):
    n = step(game, qid)
    if n is None:
        return None
    one = get(qid)["steps"][n]
    if not isinstance(one, dict):
        return one
    text = one["text"]
    goal = one.get("goal") or ""
    if goal.startswith("defeat:"):
        text += " (%d/%s)" % (state(game)[qid].get("count", 0), goal.split(":")[3])
    if one.get("to"):
        from phase2 import main_quest
        where = main_quest.where_words(game, one["to"])
        if where:
            text += ": " + where
    return text


def step_goal(game, qid):
    """The goal of the step you're on (like "cave:Home Meadow"), or None (a step people's words finish)."""
    n = step(game, qid)
    if n is None:
        return None
    one = get(qid)["steps"][n]
    return one.get("goal") if isinstance(one, dict) else None


def active(game):
    """The quests you're doing (the main quest first)."""
    doing = [qid for qid, entry in state(game).items() if entry["status"] == "active"]
    return sorted(doing, key=lambda qid: not get(qid).get("main"))


def finished(game):
    return [qid for qid, entry in state(game).items() if entry["status"] == "done"]


# ----- changing it ---------------------------------------------------------------------

def start(game, qid):
    """The quest begins. Returns False if it already started (or is done)."""
    quest = get(qid)
    if status(game, qid) != "new":
        return False
    state(game)[qid] = {"status": "active", "step": 0}
    game.log("New quest: %s! (Press Q to see your quests.)" % quest["title"], "quest")
    notice(game, "level")                    # (a "get to level N" step you've already done is done at once)
    return True


def advance(game, qid):
    """On to the next step. After the last step, the quest is finished (and you get the reward)."""
    entry = state(game).get(qid)
    if not entry or entry["status"] != "active":
        return False
    steps = get(qid)["steps"]
    if entry["step"] + 1 >= len(steps):
        return finish(game, qid)
    entry["step"] += 1
    entry["count"] = 0
    game.log("Quest: %s" % step_text(game, qid), "quest")
    notice(game, "level")                    # a "get to level N" step you've already done is done at once
    return True


def finish(game, qid, reward=None):
    """The quest is done: you get the reward (or `reward`, if a choice picked it). False if it wasn't active."""
    entry = state(game).get(qid)
    if not entry or entry["status"] != "active":
        return False
    entry["status"] = "done"
    entry["step"] = len(get(qid)["steps"])
    quest = get(qid)
    got = give_reward(game, quest.get("reward", {}) if reward is None else reward)
    game.log("Quest done: %s!%s" % (quest["title"], (" You get " + got + ".") if got else ""), "quest")
    game.popup(game.player.pos, "Quest done!", "loot")
    game.sound("diamond")
    if quest.get("main"):
        from phase2 import main_quest
        main_quest.chapter_done(game, qid)    # stage 3a: the relic, and the next chapter
    return True


def give_reward(game, reward):
    """Hand out a reward like {"gold": 25, "xp": 15}. Returns what you got, in words."""
    p = game.player
    words = []
    for what, amount in reward.items():
        if what in EXTRA_REWARDS:
            words.append(EXTRA_REWARDS[what](game, amount))
            continue
        if what == "gold":
            game.gold = getattr(game, "gold", 0) + amount
        elif what == "food":
            amount = min(amount, p.max_food - p.food)
            p.food += amount
        elif what == "arrows":
            amount = min(amount, p.max_arrows - p.arrows)
            p.arrows += amount
        elif what == "wood":
            amount = min(amount, rules.MAX_WOOD - p.wood)
            p.wood += amount
        if what == "xp":
            words.append("%d XP" % amount)
        elif amount:
            words.append("%d %s" % (amount, what))
    if reward.get("xp"):
        game.gain_xp(reward["xp"])           # last, so the LEVEL UP! card comes after the words
    return ", ".join(words)


# ----- goals that are done by themselves (stage 3a) -----------------------------------------
# A step can be {"text": ..., "goal": "cave:Home Meadow"}: when that happens, the step is done.
# phase2/world.py calls notice() when something happens: notice(game, "cave", "Home Meadow").

def _matches_land(goal_args, what):
    return goal_args[0] == what[0] if goal_args and what else not goal_args


def _defeat(game, qid, args, what):
    land, kind, count = args[0], args[1], int(args[2])
    if what[0] != land or kind not in ("any", what[1]):
        return False
    done = count_up(game, qid)
    if done < count:
        game.log("%s: %d of %d %s beaten." % (get(qid)["title"], done, count,
                                              "monsters" if kind == "any" else kind + "s"), "quest")
        return False
    return True


def count_up(game, qid):
    """One more for the step a quest is on (monsters beaten...): the one counter every quest uses,
    kept in its quest_state entry ("count"), so it saves. Returns the new count."""
    entry = state(game)[qid]
    entry["count"] = entry.get("count", 0) + 1
    return entry["count"]


def monster_beaten(game, monster):
    """A map monster is beaten (phase2/world.py): it counts for the main quest's defeat:LAND:KIND:N
    steps (on the map) and for the side quests' "beat" goals (phase2/side_steps.py)."""
    kind = getattr(monster, "base_kind", monster.kind)
    if not game.cave:
        notice(game, "defeat", getattr(monster, "land", None) or game.land_name(monster.pos), kind)
    from phase2 import side_steps
    side_steps.monster_beaten(game, monster)


GOALS = {
    # name: function(game, quest id, the goal's words after the name, what happened) -> is the step done?
    "cave": lambda game, qid, args, what: _matches_land(args, what),          # cave:LAND
    "lookout": lambda game, qid, args, what: _matches_land(args, what),       # lookout:LAND
    "defeat": _defeat,                                                        # defeat:LAND:KIND:N (KIND: any)
    "level": lambda game, qid, args, what: game.player.level >= int(args[0]),  # level:N
    "portal": lambda game, qid, args, what: True,
    "castle": lambda game, qid, args, what: True,
    "king": lambda game, qid, args, what: True,
}


def notice(game, event, *what):
    """Something happened ("cave", "defeat", "lookout", "level", "portal", "castle", "king"):
    every quest whose step is waiting for it goes on. Returns the quests that went on."""
    went_on = []
    for qid in active(game):
        goal = step_goal(game, qid)
        if not goal:
            continue
        name, *args = goal.split(":")
        if name == event and GOALS[name](game, qid, args, what):
            went_on.append(qid)
    for qid in went_on:
        advance(game, qid)
    return went_on
