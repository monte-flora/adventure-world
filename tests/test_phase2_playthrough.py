"""
Phase 2, start to finish: can you really play it through? (run with: pixi run test)

The pieces of Phase 2 were built one by one. These tests put them together:

    1. THE CHAIN     every step of the main quest (and of every side quest) points at something
                     that is really there, and that you can really get to: no dead ends.
    2. THE WALK      one game, played from a new game to the ending and on, walking every step
                     with the game's own moves (ice slides, bridges, the boat, the Desert Gate).
    3. SAVING        slot 2 keeps everything, slots 1 and 3 stay as they were, and an old
                     one-file save still loads as slot 1.

Fights and caves are not played here (the caves have their own robot: pixi run test-all-caves):
a cave is entered for real and then left by its EXIT, and a monster is "beaten" the way a won
fight ends. Monsters are cleared off the map while walking, and you never get hurt.
"""

import collections
import json

import pytest

import phase2
import rules
from helpers import ok
from phase2 import Phase2Game, draw_people, hud, main_quest, monsters, people, quests, save, side_steps
from phase2_helpers import own_save_file  # noqa: F401  (used by pytest)
from test_phase2_main_quest import LANDS, ORDER

SEEDS = (1, 2, 3)


# ===========================================================================
# Walking, by the game's own rules
# ===========================================================================

def landing(game, pos, way, boat=False, bridges=False, blocked=(), level=None):
    """Where one step from pos takes you (rules.Game.move and slide, and the gates), or None if you can't."""
    dr, dc = rules.DIRECTIONS[way]
    spot = (pos[0] + dr, pos[1] + dc)
    if not game.in_bounds(spot) or spot in blocked:
        return None
    tile = game.tile(spot)
    gate = game.gate_at(spot)
    if gate:
        if (game.player.level if level is None else level) < gate[1]:
            return None
        return spot                             # it opens, and it's a path now
    if tile == "X" or (tile == "=" and not bridges) or (tile == "W" and not boat):
        return None
    while game.tile(spot) == "I":               # ice: you slide on until something stops you
        ahead = (spot[0] + dr, spot[1] + dc)
        if not game.in_bounds(ahead) or game.tile(ahead) not in rules.WALKABLE or game.gate_at(ahead):
            break
        spot = ahead
    return spot


def routes(game, start, boat=False, bridges=False, level=None, blocked=None):
    """Every square you can stop on from start: square -> (the square before, the way you stepped). Nearest first."""
    if blocked is None:
        blocked = {spot for _, spot in people.people_here(game)}
    came = {start: None}
    todo = collections.deque([start])
    while todo:
        pos = todo.popleft()
        for way in rules.DIRECTIONS:
            spot = landing(game, pos, way, boat, bridges, blocked, level)
            if spot is not None and spot not in came:
                came[spot] = (pos, way)
                todo.append(spot)
    return came


def path_to(game, spots, **can):
    """The steps [(way, where you land)] to the nearest of spots, or None."""
    came = routes(game, game.player.pos, **can)
    for spot in came:
        if spot in spots:
            path = []
            while came[spot]:
                before, way = came[spot]
                path.append((way, spot))
                spot = before
            return path[::-1]
    return None


def step(game, way, want):
    """One real step: game.do(way). It must take you where the rules say."""
    game.monsters = []                          # (no fights on the way: see the top of this file)
    game.player.health = game.player.max_health
    was = game.player.pos
    used = game.do(way)
    ok(used and game.player.pos == want and not game.battle and not getattr(game, "talk", None),
       "a step %s from %s lands on %s (it landed on %s)" % (way, was, want, game.player.pos))


def get_wood(game, n):
    """Walk to the nearest trees and chop until you carry n wood."""
    p = game.player
    for _ in range(60):
        if p.wood >= n:
            return
        if game.here != "F":
            go(game, set(rules.tiles_of(game.map, "F")), "find a forest to chop wood in")
        game.monsters = []
        game.do("chop")
    raise AssertionError("no way to get %d wood (you have %d)" % (n, p.wood))


def go(game, spots, why):
    """Walk to the nearest of spots, like a player has to: chop wood and fix a bridge, or build a boat,
    when there's no other way."""
    spots, p = set(spots), game.player
    for _ in range(8):
        path = path_to(game, spots, boat=p.has_boat)
        if path is not None:
            for way, want in path:
                step(game, way, want)
            return
        path = path_to(game, spots, boat=p.has_boat, bridges=True)
        if path is not None:                                    # over a broken bridge
            if game.world == 2 and not p.has_planks:            # (Nightfall Hollow: planks from the chest)
                go(game, {game.plank_chest}, "get to the chest with the planks")
                game.do("act")
                ok(p.has_planks, "the chest has the planks for the Shadow Bridge")
            elif game.world == 1 and p.wood < rules.BRIDGE_WOOD:
                get_wood(game, rules.BRIDGE_WOOD)
            else:
                for way, want in path:
                    bridge = game.tile(want) == "="
                    step(game, way, want)
                    if bridge:
                        break
            continue
        if not p.has_boat and path_to(game, spots, boat=True, bridges=True) is not None:
            get_wood(game, rules.BOAT_COST)
            shore = {s for s in routes(game, p.pos) if game.neighbors(s, water=True)}
            go(game, shore, "get to the water to build a boat")
            game.do("build_boat")
            ok(p.has_boat, "8 wood by the water builds a boat")
            continue
        break
    raise AssertionError("DEAD END: there's no way to %s (from %s, in %s)" % (why, p.pos, game.land_name(p.pos)))


def beside(spot):
    """The squares next to spot -> the way to step from there into spot."""
    return {(spot[0] - dr, spot[1] - dc): way for way, (dr, dc) in rules.DIRECTIONS.items()}


def meet(game, pid, *picks):
    """Walk up to someone, bump into them and talk it through, picking the choices with these words
    (or else one that starts a quest, or one not picked yet)."""
    who = people.person(pid)
    ok(people.shown(game, who), "%s is there to talk to" % pid)
    around = beside(game.people[pid])
    go(game, around, "walk up to %s" % who["name"])
    game.monsters = []
    game.do(around[game.player.pos])
    talk = game.talk
    ok(talk is not None and talk.person["id"] == pid, "walking into %s starts a talk" % who["name"])
    picks, tried = list(picks), set()
    for _ in range(80):
        if talk.done:
            break
        if talk.choices:
            texts = [talk.fill(choice["text"]) for choice in talk.choices]
            pick = next((pick for pick in picks if any(pick in text for text in texts)), None)
            hits = [i for i, text in enumerate(texts) if pick is not None and pick in text]
            if hits:
                picks.remove(pick)              # (each of the words is used once, in their order)
            else:                               # a choice that starts a quest, or the next one not picked yet
                hits = [i for i, choice in enumerate(talk.choices)
                        if any(effect.startswith("start_quest") for effect in choice.get("do", []))]
                hits += [i for i, text in enumerate(texts) if (id(talk.node), text) not in tried]
                hits += [len(texts) - 1]
            tried.add((id(talk.node), texts[hits[0]]))
            talk.choose(hits[0])
        else:
            talk.press()
    ok(talk.done, "the talk with %s comes to an end" % who["name"])
    game.talk = None


def beat(game, kind, land, n):
    """n monsters of that kind are beaten in that land, the way a won fight ends."""
    for _ in range(n):
        m = monsters.make_monster(kind, game.player.pos, land=land)
        game.monsters.append(m)
        game.monster_gone(m, True)


def through_the_cave(game, mine):
    """Climb down a Mine (for real) and come out of its EXIT door."""
    go(game, {mine}, "get to the Mine at %s" % (mine,))
    game.monsters = []
    game.do("act")
    ok(game.cave is not None and game.cave.mine_pos == mine, "SPACE on the Mine takes you down into its cave")
    game.cave.result = "exit"
    game.leave_cave()
    ok(game.cave is None, "and out again")


def do_goal(game, goal):
    """Make a main-quest step's goal happen, walking there first."""
    name, *args = goal.split(":")
    if name == "cave":
        mine = main_quest.target(game, "mine:" + args[0])
        ok(mine is not None, "there's a Mine in %s" % args[0])
        through_the_cave(game, mine)
    elif name == "defeat":
        land, kind, count = args[0], args[1], int(args[2])
        go(game, {s for s in routes(game, game.player.pos, boat=True, bridges=True) if game.land_name(s) == land},
           "walk into %s" % land)
        ok(game.land_name(game.player.pos) == land, "you're in %s" % land)
        beat(game, sorted(game.monster_plan[land])[0] if kind == "any" else kind, land, count)
    elif name == "lookout":
        tower = main_quest.target(game, "lookout:" + args[0])
        ok(tower is not None, "there's a lookout tower in %s" % args[0])
        go(game, {tower}, "get to the lookout tower in %s" % args[0])
        game.monsters = []
        game.do("act")
    elif name == "level":
        ok(game.player.level >= int(args[0]),
           "the quests before this one get you to level %s by themselves (you're level %d)" % (args[0], game.player.level))
        go(game, {s for s in routes(game, game.player.pos, boat=True, bridges=True)
                  if game.land_name(s) == "Sunscorch Desert"}, "walk through the Desert Gate")
    else:
        raise AssertionError("no test for goal %s" % goal)


def walk_chapter(game, qid):
    """Play one chapter of the main quest, on foot."""
    quest = quests.get(qid)
    if quests.status(game, qid) == "new":
        ok(qid == main_quest.data()["first"], "%s starts by itself when the chapter before it ends" % qid)
        meet(game, quest["giver"])
    ok(quests.status(game, qid) == "active", "%s has started" % qid)
    for _ in range(len(quest["steps"])):
        if quests.status(game, qid) != "active":
            break
        n = quests.step(game, qid)
        one = quest["steps"][n]
        ok(main_quest.target(game, one["to"]) is not None, "%s step %d: the quest log can point the way" % (qid, n + 1))
        if one.get("goal"):
            do_goal(game, one["goal"])
        else:
            meet(game, one["to"].split(":")[1])
        ok(quests.status(game, qid) == "done" or quests.step(game, qid) > n, "%s step %d gets done" % (qid, n + 1))
    ok(quests.status(game, qid) == "done", "%s is done" % qid)


# ===========================================================================
# 1. The chain: nothing the quests point at is missing or out of reach
# ===========================================================================

def reach_everything(game):
    """Every square you can stop on with a boat, the bridges fixed and the gates open: nobody in the way but
    the people who are always there (the ones who show up later don't block anything yet)."""
    always = {game.people[who["id"]] for who in people.all_people() if not who.get("show_if")}
    top = max([level for _, level in game.atlas.gates.values()] + [1])
    return routes(game, game.start, boat=True, bridges=True, level=top, blocked=always)


def can_bump(spot, reach):
    """Can you stop on a square next to spot? (Then you can walk into whoever stands there.)"""
    return any(s in reach for s in beside(spot))


def effects_of(node):
    """Every effect ("do") a talk node can run: its own, and its choices'."""
    found = []
    for variant in node if isinstance(node, list) else [node]:
        found += variant.get("do", [])
        for choice in variant.get("choices", []):
            found += choice.get("do", [])
    return found


def conditions_of(who):
    found = list(who.get("show_if", []))
    for node in who.get("talk", {}).values():
        for variant in node if isinstance(node, list) else [node]:
            found += variant.get("if", [])
            for choice in variant.get("choices", []):
                found += choice.get("if", [])
    return found


def quest_effects():
    """{quest id: {"start_quest", "advance_quest", ...}} from everybody's words."""
    found = collections.defaultdict(set)
    for who in people.all_people():
        for node in who.get("talk", {}).values():
            for effect in effects_of(node):
                name, *args = effect.split(":")
                if name in ("start_quest", "advance_quest", "finish_quest", "finish_quest_with"):
                    found[args[0]].add(name)
    return found


def quest_xp_before(qid):
    """The XP the chapters before this one give you (their rewards only: no fights, no caves)."""
    return sum(quests.get(q)["reward"].get("xp", 0) for q in ORDER[:ORDER.index(qid)])


def level_from(xp):
    level = 1
    while xp >= rules.XP_PER_LEVEL * level:
        xp -= rules.XP_PER_LEVEL * level
        level += 1
    return level


@pytest.mark.parametrize("seed", SEEDS)
def test_the_main_quest_has_no_dead_end(seed):
    game = Phase2Game("Hero", seed=seed)
    reach = reach_everything(game)
    on_foot = routes(game, game.start, blocked=set(game.people.values()))
    lands = [land[0] for land in game.atlas.lands]
    everyone = {who["id"]: who for who in people.all_people()}
    said = quest_effects()
    problems = []

    def check(fine, words):
        if not fine:
            problems.append(words)

    first = main_quest.data()["first"]
    check(main_quest.chapters() == ORDER, "the chapters run %s, not %s" % (main_quest.chapters(), ORDER))
    check(first == ORDER[0] and "start_quest" in said[first], "nobody's words start the first chapter (%s)" % first)
    rosa = everyone.get(quests.get(first)["giver"])
    check(rosa and not rosa.get("show_if") and can_bump(game.people[rosa["id"]], on_foot),
          "the one who starts it all (%s) isn't there, or you can't walk up to them" % quests.get(first)["giver"])

    for qid in ORDER:
        quest = quests.get(qid)
        where = "%s (%s)" % (qid, quest["title"])
        check(quest.get("giver") in everyone, "%s: its giver %r isn't a person" % (where, quest.get("giver")))
        if qid != ORDER[-1]:
            check(quest.get("next") == ORDER[ORDER.index(qid) + 1], "%s: the next chapter is %r" % (where, quest.get("next")))
            check(quest.get("relic"), "%s gives no Light Stone" % where)
        for key in quest.get("reward", {}):
            check(key in quests.REWARDS or key in quests.EXTRA_REWARDS, "%s: there's no reward called %r" % (where, key))
        talks = 0
        for n, one in enumerate(quest["steps"]):
            at = "%s step %d (%s)" % (qid, n + 1, one["text"])
            if one.get("to"):
                check(main_quest.target(game, one["to"]) is not None, "%s points at %r, which isn't there" % (at, one["to"]))
            goal = one.get("goal")
            if not goal:                                        # a step you do by talking to someone
                talks += 1
                kind, _, pid = (one.get("to") or "").partition(":")
                check(kind == "person" and pid in game.people, "%s: nobody to talk to (%r)" % (at, one.get("to")))
                if pid in game.people:
                    check(can_bump(game.people[pid], reach), "%s: you can't walk up to %s at %s" % (at, pid, game.people[pid]))
                    for condition in everyone[pid].get("show_if", []):      # hidden until their chapter starts
                        check(condition == "not:quest_new:" + qid,
                              "%s: %s only shows if %r, which this chapter doesn't make true" % (at, pid, condition))
                continue
            name, *args = goal.split(":")
            if name == "cave":
                mines = [m for m in game.cave_plan if game.tile(m) == "M" and game.land_name(m) == args[0]]
                check(mines, "%s: there's no Mine in %s" % (at, args[0]))
                check(any(m in reach for m in mines), "%s: you can't get to a Mine in %s" % (at, args[0]))
                check(all(game.cave_plan[m].strip() for m in mines), "%s: a Mine in %s has no cave under it" % (at, args[0]))
            elif name == "lookout":
                towers = [s for s in game.atlas.lookouts if game.land_name(s) == args[0]]
                check(towers, "%s: there's no lookout tower in %s" % (at, args[0]))
                check(any(s in reach for s in towers), "%s: you can't get onto a lookout tower in %s" % (at, args[0]))
            elif name == "defeat":
                land, kind, count = args[0], args[1], int(args[2])
                check(land in lands, "%s: there's no land called %s" % (at, land))
                planned = game.monster_plan.get(land, {})
                here = [m for m in game.monsters if m.land == land and (kind == "any" or m.kind == kind)]
                check(kind == "any" or kind in planned, "%s: no %s lives in %s (only %s)" % (at, kind, land, sorted(planned)))
                check(here, "%s: none of them is on the map in %s" % (at, land))    # (they come back, so 1 is enough)
                check(any(game.land_name(s) == land for s in reach), "%s: you can't walk into %s" % (at, land))
            elif name == "level":
                check(level_from(quest_xp_before(qid)) >= int(args[0]),
                      "%s: the chapters before it only get you to level %d" % (at, level_from(quest_xp_before(qid))))
            elif name == "portal":
                check(game.portal in reach, "%s: you can't get to the Portal at %s" % (at, game.portal))
            else:
                check(name in ("castle", "king"), "%s: nothing in the game makes the goal %r happen" % (at, goal))
        check(talks == 0 or "finish_quest" in said[qid] or "advance_quest" in said[qid],
              "%s has steps you do by talking, but nobody's words move it on" % where)

    # Gates: each opens at a level the main quest's own rewards reach before the chapter behind it
    for spot, (name, level) in game.atlas.gates.items():
        behind = game.land_name(spot)
        chapters = [q for q in ORDER[:-1] if any(behind in str(one.get("to")) for one in quests.get(q)["steps"])]
        check(can_bump(spot, routes(game, game.start, bridges=True, level=0, blocked=set(game.people.values()))),
              "you can't walk up to the %s at %s" % (name, spot))
        if chapters:
            check(level_from(quest_xp_before(chapters[0])) >= level,
                  "the %s needs level %d, but the quests before %s only get you to level %d"
                  % (name, level, chapters[0], level_from(quest_xp_before(chapters[0]))))

    # What walking needs: wood you can carry, a tree to chop, water to launch a boat from
    check(rules.MAX_WOOD >= max(rules.BRIDGE_WOOD, rules.BOAT_COST, rules.HILT_WOOD), "you can't carry the wood a boat needs")
    check(any(game.tile(s) == "F" for s in on_foot), "there's no forest you can walk to for wood")
    check(any(game.neighbors(s, water=True) for s in on_foot), "there's no shore you can walk to for a boat")
    # Ice never slides you onto somebody
    for pid, spot in game.people.items():
        for (r, c), way in beside(spot).items():
            check(not (game.in_bounds((r, c)) and game.tile((r, c)) == "I"), "ice slides you %s onto %s at %s" % (way, pid, spot))
    # Nobody who is always there stands where somebody else's square is the only way to them
    for pid, spot in game.people.items():
        check(can_bump(spot, reach), "you can't walk up to %s at %s (%s)" % (pid, spot, game.land_name(spot)))
    ok(not problems, "the main quest can be played to the end (seed %d):\n  " % seed + "\n  ".join(problems))


def test_the_way_to_the_end_after_the_portal():
    """Nightfall Hollow, the castle and the throne room are the classic ones: the Portal leads into them."""
    game = Phase2Game("Hero", seed=1)
    for qid in ORDER[:-1]:
        game.quest_state[qid] = {"status": "done", "step": 0}
    quests.start(game, ORDER[-1])
    ok(game.portal_open, "7 Light Stones open the Portal")
    game.player.pos = game.portal
    game.check_portal()
    ok(game.world == 2 and quests.step(game, ORDER[-1]) == 1, "through the Portal: Nightfall Hollow")
    game.monsters = []
    reach = routes(game, game.start, boat=True, bridges=True)
    shrines, mines = rules.tiles_of(game.map, "D"), rules.tiles_of(game.map, "M")
    ok(len(shrines) >= rules.BEACONS_NEEDED and all(s in reach for s in shrines), "the dark shrines can be reached")
    ok(len(mines) >= max(rules.SUNFANG_DIAMONDS, rules.SUN_SHARDS_NEEDED) and all(m in reach for m in mines),
       "the shadow Mines (a diamond and a Sun Shard each) can be reached")
    ok(all(game.cave_plan[m].strip() for m in mines), "and each has a cave under it")
    ok(game.plank_chest in routes(game, game.start) or game.player.has_boat, "the planks are on your side of the river")
    ok(any(game.tile(s) == "F" for s in reach), "there are trees for the Hilt's wood")
    ok(game.castle in reach, "the castle gate can be reached")


def side_quest_ids():
    return sorted(qid for qid, quest in quests.all_quests().items() if not quest.get("main"))


@pytest.mark.parametrize("seed", SEEDS)
def test_the_side_quests_have_no_dead_end(seed):
    game = Phase2Game("Hero", seed=seed)
    reach = reach_everything(game)
    lands = [land[0] for land in game.atlas.lands]
    everyone = {who["id"]: who for who in people.all_people()}
    all_ids = set(quests.all_quests())
    said = quest_effects()
    kinds = {kind for plan in game.monster_plan.values() for kind in plan}
    p = game.player
    most = {"wood": rules.MAX_WOOD, "food": p.max_food, "swords": rules.MAX_SWORDS}
    problems = []

    def check(fine, words):
        if not fine:
            problems.append(words)

    ok(len(side_steps.load_quests()) == 12, "12 side quests (and the 2 from stage 2b)")
    # Everybody's words: the quests, people, conditions and effects they name are real
    for who in everyone.values():
        for node in who.get("talk", {}).values():
            for effect in effects_of(node):
                name, *args = effect.split(":")
                check(name in people.EFFECTS, "%s's words do %r: there's no such effect" % (who["id"], effect))
                if name.endswith("_quest") or name == "finish_quest_with":
                    check(args[0] in all_ids, "%s's words do %r: there's no such quest" % (who["id"], effect))
                if name == "finish_quest_with" and args[0] in all_ids:
                    check(args[1] in quests.get(args[0]).get("choice_rewards", {}),
                          "%s's words do %r: the quest has no such reward" % (who["id"], effect))
                if name == "take":
                    check(int(args[1]) <= most.get(args[0], 10 ** 6),
                          "%s takes %s %s, but you can only carry %s" % (who["id"], args[1], args[0], most.get(args[0])))
        for condition in conditions_of(who):
            name, *args = condition[4:].split(":") if condition.startswith("not:") else condition.split(":")
            check(name in people.CONDITIONS, "%s checks %r: there's no such condition" % (who["id"], condition))
            if name.startswith("quest_") or name == "goal_count":
                check(args[0] in all_ids, "%s checks %r: there's no such quest" % (who["id"], condition))
            if name == "been_to":
                check(args[0] in lands, "%s checks %r: there's no such land" % (who["id"], condition))
            if name == "has":
                check(int(args[1]) <= most.get(args[0], 10 ** 6),
                      "%s wants %s %s, but you can only carry %s" % (who["id"], args[1], args[0], most.get(args[0])))
        spot = game.people.get(who["id"])
        check(spot is not None and can_bump(spot, reach), "you can't walk up to %s at %s" % (who["id"], spot))
        for condition in who.get("show_if", []):                 # someone who shows up later, in their own land
            if condition.startswith("been_to:") and spot:
                check(game.land_name(spot) == condition[8:] or condition[8:] in lands,
                      "%s waits for you to visit %s" % (who["id"], condition[8:]))

    for qid in side_quest_ids():
        quest = quests.get(qid)
        where = "%s (%s)" % (qid, quest["title"])
        giver = everyone.get(quest.get("giver"))
        check(giver is not None, "%s: its giver %r isn't a person" % (where, quest.get("giver")))
        check("start_quest" in said[qid], "%s: nobody's words start it" % where)
        check(said[qid] & {"finish_quest", "finish_quest_with"} or "advance_quest" in said[qid],
              "%s: nobody's words finish it" % where)
        goals = quest.get("goals") or [None] * len(quest["steps"])
        moved_by_words = sum(1 for goal in goals if goal is None)
        check(moved_by_words == 0 or said[qid] - {"start_quest"}, "%s: nobody's words move its steps on" % where)
        rewards = [quest["reward"]] if "reward" in quest else list(quest.get("choice_rewards", {}).values())
        check(rewards, "%s has no reward" % where)
        for reward in rewards:
            for key, amount in reward.items():
                check(key in quests.REWARDS or key in quests.EXTRA_REWARDS, "%s: there's no reward called %r" % (where, key))
                if key == "treasure":
                    check(amount in lands, "%s: its treasure map is of %r, which isn't a land" % (where, amount))
        for n, goal in enumerate(goals):
            if not goal:
                continue
            at = "%s step %d" % (qid, n + 1)
            if goal["kind"] == "beat":
                check(goal["monster"] in kinds, "%s: no %s lives anywhere" % (at, goal["monster"]))
                check(any(m.kind == goal["monster"] for m in game.monsters), "%s: no %s is on the map" % (at, goal["monster"]))
            elif goal["kind"] == "lookout":
                towers = [s for s in game.atlas.lookouts if game.land_name(s) == goal["land"]]
                check(any(s in reach for s in towers), "%s: no lookout tower you can get to in %s" % (at, goal["land"]))
            elif goal["kind"] == "chest":
                chests = [s for s in rules.tiles_of(game.map, "T") if game.land_name(s) == goal["land"]]
                check(any(s in reach for s in chests), "%s: no treasure chest you can get to in %s" % (at, goal["land"]))
    ok(not problems, "every side quest can be played to the end (seed %d):\n  " % seed + "\n  ".join(problems))


# ===========================================================================
# 2. The walk: one whole game, from a new game to the ending and on
# ===========================================================================

def test_a_whole_game_from_a_new_game_to_the_ending_and_on():
    game = Phase2Game("Hero", seed=1)
    game.story.clear()
    p = game.player

    for qid in ORDER[:-1]:                                  # the 7 Light Stones, one land after another
        walk_chapter(game, qid)
    ok(len(main_quest.relics(game)) == 7 and game.portal_open, "7 Light Stones wake the Portal")
    ok(quests.status(game, "main_portal") == "active", "and the last chapter starts")

    around = beside(game.portal)                            # (go() chops the wood and builds the boat)
    go(game, set(around), "row to the Portal's island")
    game.monsters = []
    game.do(around[p.pos])
    ok(game.world == 2, "stepping on the Portal takes you to Nightfall Hollow")
    game.story.clear()
    doing, _ = draw_people.quest_lines(game)                # (the quest log and the NEXT card, in Nightfall)
    ok([title for title, _, _ in doing] == [quests.get("main_portal")["title"]] and doing[0][1],
       "in Nightfall Hollow the quest log shows the last chapter and its step: %s" % doing)
    ok(hud.next_goal(game)["text"] == "Find the Shadow King's castle", "and the NEXT card says where to go")

    for shrine in rules.tiles_of(game.map, "D"):            # the 3 shrines
        go(game, {shrine}, "get to the shrine at %s" % (shrine,))
        game.monsters = []
        game.do("act")
    ok(len(game.beacons) == 3, "all 3 shrines are lit")

    for mine in rules.tiles_of(game.map, "M"):              # the 3 Mines: a diamond and a Sun Shard in each
        go(game, {mine}, "get to the Nightfall Mine at %s" % (mine,))
        game.monsters = []
        game.do("act")
        ok(game.cave is not None, "SPACE on a Nightfall Mine takes you down")
        game.found_diamond()
        game.found_sun_shard()
        game.cave.result = "exit"
        game.leave_cave()
        ok(game.cave is None, "and out again")
    ok(p.diamonds >= 3 and p.sun_shards >= 3, "3 diamonds and 3 Sun Shards")

    get_wood(game, rules.HILT_WOOD)                         # the Hilt
    game.monsters = []
    game.do("build_hilt")
    ok(p.has_hilt, "wood builds the Hilt")

    go(game, {game.castle}, "get to the Shadow Castle")     # over the Shadow Bridge (planks from the chest)
    ok(game.forging, "at the castle door the Sunfang is forged")
    game.finish_sunfang(False)
    ok(game.cave is not None and game.cave.is_castle, "and the castle opens")
    ok(quests.step(game, "main_portal") == 2, "the quest log moves on to the Shadow King")

    game.enter_castle_level(4)                              # (the 5 castle levels have their own tests)
    game.cave.result = "exit"
    game.leave_cave()
    ok(game.cave is not None and game.cave.is_throne_room, "past the last castle level is the throne room")
    game.beat_the_king()

    ok(game.king_beaten and quests.status(game, "main_portal") == "done", "the Shadow King is beaten")
    ok(game.world == 1 and p.pos == game.start, "you wake up at home, in the Kingdom")
    ok(not game.won and not game.over, "and the game goes on")
    game.story.clear()
    doing, done = draw_people.quest_lines(game)             # (what the screens show after the ending)
    ok(not doing and [title for title, _, _ in done] == [quests.get(qid)["title"] for qid in ORDER],
       "the quest log lists all 8 chapters as finished: %s" % done)
    ok(len(main_quest.relics(game)) == 7 and main_quest.current(game) is None, "you still have the 7 Light Stones")
    ok(hud.next_goal(game)["title"] == "The hero of all the lands", "the NEXT card says you did it all")
    ok(not any(main_quest.wants_you(game, pid) for pid in game.people), "and nobody has a main-quest '!' any more")

    meet(game, "mabel", "Any errands", "I'll take it", "Bye")   # free play: a side quest, on foot
    meet(game, "finn")
    meet(game, "mabel", "Bye")
    ok(quests.status(game, "mabel_letter") == "done", "a side quest can still be done after the ending")


# ===========================================================================
# 3. Saving: slot 2 keeps everything, and an old one-file save is slot 1
# ===========================================================================

def plain(value):
    """A value with its objects (the player, a sword, a monster...) turned into plain dicts, to compare two games."""
    if isinstance(value, dict):
        return {key: plain(v) for key, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return {plain(v) if not isinstance(v, tuple) else v for v in value}
    if hasattr(value, "__dict__"):
        return {"class": type(value).__name__, **plain(vars(value))}
    return value


def everything(game):
    """All that a save keeps of a game (all but the message log and which slot it's in)."""
    return {key: plain(value) for key, value in vars(game).items()
            if key not in save.NOT_SAVED and key != "save_slot"}


def a_game_in_the_middle(slot):
    """Two chapters in, two side quests on the go (one that counts monsters), away from home, with things.
    It's a new game in this slot (walking through home saves it there, by itself)."""
    game = phase2.new_game("Hero", 1, slot)
    game.story.clear()
    for qid in ORDER[:2]:
        walk_chapter(game, qid)
    meet(game, "mabel", "Any errands", "I'll take it", "Bye")
    meet(game, "ranger_ivy")
    beat(game, "Spider", "Whispering Woods", 2)
    go(game, {s for s in routes(game, game.player.pos) if game.land_name(s) == "Whispering Woods"}, "walk into the Woods")
    p = game.player
    game.gold, p.wood, p.food, p.arrows, p.health, p.lives = 77, 5, 4, 9, 11, 2
    game.play_time = 754.5
    return game


def test_slot_2_keeps_the_whole_game_and_leaves_slots_1_and_3_alone():
    other = phase2.new_game("Rosie", 2, 1)
    ok(save.save_game(other), "another game is saved in slot 1")
    with open(save.save_file(1), "rb") as file:
        slot_1 = file.read()

    game = a_game_in_the_middle(2)
    p = game.player
    ok(quests.status(game, "main_woods") == "done" and quests.status(game, "main_lake") == "active"
       and quests.status(game, "mabel_letter") == "active"
       and game.quest_state["ivy_spiders"] == {"status": "active", "step": 0, "count": 2},
       "(the game to save: main quest on chapter 3, two side quests on the go: %s)" % game.quest_state)
    ok(len(main_quest.relics(game)) == 2 and p.level >= 2 and p.xp > 0, "(2 Light Stones, and some XP)")
    was = everything(game)

    ok(save.save_game(game), "the game is saved in its slot, slot 2")
    ok(save.used_slots() == [1, 2], "slots 1 and 2 are used, slot 3 is not")
    back = save.load_game(2)
    ok(back is not None and back.save_slot == 2, "slot 2 loads, and knows it's slot 2")

    now = everything(back)
    ok(sorted(now) == sorted(was), "the loaded game has the same things: %s" % sorted(set(now) ^ set(was)))
    for key in sorted(was):
        if key != "messages":
            ok(now[key] == was[key], "%s is the same after loading\n  saved:  %r\n  loaded: %r" % (key, was[key], now[key]))

    q = back.player                                         # (and, by name, what the player would miss most)
    ok(back.quest_state == game.quest_state, "the quests: main and side, steps and counts")
    ok(main_quest.relics(back) == main_quest.relics(game), "the Light Stones")
    ok((back.gold, q.wood, q.food, q.arrows, q.health, q.lives) == (77, 5, 4, 9, 11, 2), "gold and things")
    ok((q.xp, q.level, len(q.swords)) == (p.xp, p.level, len(p.swords)), "XP, level and swords")
    ok(q.pos == p.pos and back.land_name(q.pos) == "Whispering Woods", "where you stand")
    ok(back.play_time == 754.5, "the play time")
    ok(back.people == game.people and back.people_talked == game.people_talked, "the people")
    ok(back.rng.getstate() == game.rng.getstate(), "even the dice")

    info = save.slot_info(2)                                # the slot list
    ok((info["name"], info["land"], info["level"], info["stones"], info["play_time"])
       == ("Hero", "Whispering Woods", p.level, 2, 754.5), "the slot list tells slot 2 right: %s" % info)
    with open(save.save_file(1), "rb") as file:
        ok(file.read() == slot_1, "slot 1's file is untouched")
    ok(save.slot_info(1)["name"] == "Rosie" and save.load_game(1).player.name == "Rosie", "slot 1 is still Rosie's game")
    ok(save.slot_info(3) == {"slot": 3, "empty": True} and save.load_game(3) is None, "slot 3 is still empty")

    walk_chapter(back, "main_lake")                         # and the loaded game plays on
    ok(len(main_quest.relics(back)) == 3, "the loaded game goes on: the 3rd Light Stone")
    ok(save.save_game(back) and save.slot_info(2)["stones"] == 3, "and it saves back into slot 2")
    with open(save.save_file(1), "rb") as file:
        ok(file.read() == slot_1, "slot 1's file is still untouched")


def test_an_old_one_file_save_loads_as_slot_1(own_save_file):
    game = a_game_in_the_middle(1)
    ok(save.save_game(game), "saved")
    ok(save.save_file(1) == str(own_save_file), "slot 1's file is the old one-and-only save file")

    data = json.loads(own_save_file.read_text())            # make it a save from before slots and play time
    del data["summary"]
    fields = data["game"]["$dict"]
    ok({"save_slot", "play_time"} <= {key for key, _ in fields}, "(a new save has save_slot and play_time)")
    data["game"]["$dict"] = [pair for pair in fields if pair[0] not in ("save_slot", "play_time")]
    own_save_file.write_text(json.dumps(data))

    ok(save.used_slots() == [1], "the old save shows up as slot 1")
    info = save.slot_info(1)
    ok(not info["empty"] and not info["broken"], "the slot list can read it: %s" % info)
    ok((info["name"], info["land"], info["level"], info["stones"], info["play_time"])
       == ("Hero", "Whispering Woods", game.player.level, 2, 0.0), "and fills in what it shows: %s" % info)

    back = save.load_game(1)
    ok(back is not None and back.save_slot == 1 and back.play_time == 0.0, "it loads as slot 1, with no play time yet")
    ok(back.quest_state == game.quest_state and main_quest.relics(back) == main_quest.relics(game),
       "with its quests and Light Stones")
    ok((back.gold, back.player.pos, back.player.xp) == (77, game.player.pos, game.player.xp), "and all the rest")
    ok(save.save_game(back) and "summary" in json.loads(own_save_file.read_text()), "saving it again makes it a new save")
    ok(save.used_slots() == [1], "still only slot 1")
