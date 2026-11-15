"""
THE TEST ROBOT - it plays a cave to check that it can be beaten.

It's the cave editor's robot (cave_solver.py): the same moves (run, jump, climb, dig ...),
it never gets hurt even once, and it ignores monsters. The tests give it one trick,
so it can get through long caves quickly:

It goes in steps: the diamond first, then the exit (in the castle: the key or the lever,
then the door). It uses the editor robot's map of how far (cave_solver.steps_to).

In the castle, it first gets the key (or pulls the lever), then goes through the door.
"""

import heapq

import castle
import cave_solver
import caves

TRIES = 400000          # how many moves it tries for each part of the way, before it gives up

WALLS = cave_solver.WALLS
steps_to = cave_solver.steps_to


def search(start, goal, goals, tries=TRIES):
    """Try moves from start until goal(cave) is true, trying the moves that get closer to goals first.
    Returns (the moves, the cave at the end, how many tries), or (None, None, tries) if it gave up."""
    how_far = cave_solver.how_far(start, steps_to(start, goals))      # (on a swinging vine: how high it could go)

    todo = [(how_far(start), 0, start, [])]
    seen = {cave_solver.fingerprint(start)}
    n = 0
    while todo and n < tries:
        _, _, cave, moves = heapq.heappop(todo)
        for move in cave_solver.MOVES:
            after = copy_cave(cave)
            cave_solver.do_move(after, move)
            n += 1
            if after.game.hurt or after.result == "left":
                continue                          # it got hurt, or walked back out: that doesn't count
            if goal(after):
                return moves + [move], after, n
            if after.result:
                continue
            key = cave_solver.fingerprint(after)
            if key in seen:
                continue                          # been here before, the same way
            seen.add(key)
            heapq.heappush(todo, (how_far(after) + cave_solver.HURRY * len(moves), n, after, moves + [move]))
    return None, None, n


def where(cave, letter):
    return [(r, c) for r, row in enumerate(cave.map) for c, tile in enumerate(row) if tile == letter]


def beat(text, tries=TRIES):
    """Can the robot beat this cave? Returns (True or False, what happened, in words)."""
    cave = cave_solver.fresh_cave(text)
    ores, exits = where(cave, "*"), where(cave, "E")
    if not exits:
        return False, "there's no exit door"
    legs = []
    levers = where(cave, caves.LEVER)
    if levers and not cave.gates_open():
        legs.append(("the lever", lambda cave: cave.gates_open(), levers))
    shards = where(cave, caves.SHARD)
    if shards:
        legs.append(("the Sun Shard", lambda cave: cave.got_shard, shards))
    if ores:
        legs.append(("the diamond", lambda cave: cave.got_diamond, ores))
    legs.append(("the exit", lambda cave: cave.result == "exit", exits))

    return play_the_legs(cave, legs, tries)


def play_the_legs(cave, legs, tries):
    """Go from one part of the way to the next: legs is a list of (its name, goal(cave), where it is)."""
    moves = 0
    for name, goal, goals in legs:
        found, cave, n = search(cave, goal, goals, tries)
        if found is None:
            return False, "the robot got stuck on the way to %s (it tried %d moves)" % (name, n)
        moves += len(found)
        cave.result = None
    return True, "about %d seconds of play" % (moves * cave_solver.FRAMES / 60)


# ===========================================================================
# The castle: in every level, first the key (or the lever), then the door
# ===========================================================================

class CastleRobot(cave_solver.Robot):
    """Pretends to be the game in the castle, too: light shards to pick up, and doors to the next level."""

    def __init__(self):
        super().__init__()
        self.player.light_shards = 0
        self.player.sunfang = True

    def enter_castle_level(self, *a, **k):
        pass                              # the robot stays in the level it's checking


def copy_cave(cave):
    """A copy of the cave (or castle level) to try a move in, playing the same kind of game."""
    after = cave_solver.copy_cave(cave)
    after.game = type(cave.game)()
    if hasattr(cave, "fountains"):
        after.fountains = dict(cave.fountains)
    return after


def beat_castle_level(level, tries=TRIES):
    """Can the robot get through this castle level (0 = level 1)? Returns (True or False, what happened)."""
    level_now = castle.Castle(CastleRobot(), (0, 0), {}, level)
    level_now.monsters = []
    legs = []
    if level_now.needs == "key" and where(level_now, caves.GATE) and where(level_now, caves.LEVER):
        legs.append(("the lever", lambda cave: cave.gates_open(), where(level_now, caves.LEVER)))
    if level_now.needs == "key":
        legs.append(("the key", lambda cave: cave.has_key or cave.door_open, where(level_now, "K")))
    elif level_now.needs == "lever":
        legs.append(("the lever", lambda cave: cave.door_open, where(level_now, "L")))
    legs.append(("the door", lambda cave: cave.result == "exit", where(level_now, "D") + where(level_now, "E")))
    return play_the_legs(level_now, legs, tries)
