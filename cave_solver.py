"""
CAN IT BE BEATEN? - a robot that plays your cave to see if it can be done.

The robot tries thousands and thousands of moves (run, jump, climb, dig...),
always trying the ones that get it closer to the diamond first, and then to
the exit. It never takes any damage, and it ignores monsters: beating those
is up to you!

Check a saved cave:
    python cave_solver.py my_caves/lava_tower.txt

The cave editor runs this for you when you press "Can it be beaten?".
"""

import copy
import heapq
import json
import math
import random
import sys
import time

import caves

# ===========================================================================
# SETTINGS - how hard the robot tries
# ===========================================================================
TRIES = 400000          # how many moves it tries before it gives up (the same as the test robot)
CHEST_TRIES = 60000     # ...and for each treasure chest
TIME_LIMIT = 120        # it gives up after this many seconds, too
FRAMES = 9              # every move lasts this many frames (60 frames = 1 second)
DT = 1 / 60
HURRY = 0.12            # bigger = the robot rushes toward its goal (faster, but it can miss tricky ways)
DIG_STEPS = 3           # on the map of how far, cracked rock in the way counts as this many steps
FAR_AWAY = 10 ** 9      # for a block you can't get to from here at all

WALLS = set(caves.SOLIDS) - set(caves.DIGGABLE)       # rock it can't get through
NO_GO = set("^~!")                                   # spikes, lava and fire: the robot never touches them
JUMP_ROWS = 3           # on the map, you can jump up into a block this high above the ground (1 = standing on it)
MUSHROOM_ROWS = 4       # a bouncy mushroom throws you this many blocks higher than a jump
AIR_STEPS = 4           # ...and a running jump carries you this many blocks sideways over a gap


class Pickaxe:
    """The robot's pickaxe never breaks."""
    durability = max_durability = 99

    def use(self):
        return False


class Robot:
    """Pretends to be the game, so a cave can be played without any graphics."""
    def __init__(self):
        self.player = type("Player", (), {
            "is_alive": True, "pickaxe": Pickaxe(), "swords": [], "damage_bonus": 0, "sunfang": False,
            "sunfang_perfect": False, "has_bow": False, "arrows": 0, "ring_hits": 0, "health": 10,
            "max_health": 10, "power": lambda self, name: 0})()
        self.rng = random.Random(0)
        self.hurt = 0                    # the robot is careful: any move that hurts doesn't count
        self.tips_seen = set()
        self.cleared_mines = set()
        self.pickaxe_cave_wood = 2

    def sound(self, *a, **k): pass
    def log(self, *a, **k): pass
    def effect(self, *a, **k): pass
    def found_diamond(self, *a, **k): pass
    def found_sun_shard(self, *a, **k): pass
    def monster_gone(self, *a, **k): pass
    def gain_xp(self, *a, **k): pass
    def give_ring(self, *a, **k): pass
    def ring_power(self, *a, **k): return 0
    def arrow_damage(self, *a, **k): return 1
    def sunfang_damage(self, *a, **k): return 1
    def give_loot(self, *a, **k): return ""

    def hurt_player(self, amount):
        self.hurt += amount

    def new_monster(self, kind, shadow=False):
        return type("Monster", (), {"kind": kind, "base_kind": kind, "health": 5, "max_health": 5,
                                    "damage": (1, 2), "move_chance": 0.5, "xp": 1, "special": None,
                                    "is_alive": True, "shadow": False})()


# Every move the robot can make: run left or right (or stand still), jump (a tap or held down),
# swing the pickaxe, dig down, and climb up or down (ladders, crawling, ground pounds)
MOVES = ([(run, jump, None, None) for run in ("right", "left", None) for jump in ("tap", "hold", None)]
         + [(None, None, "use", None), (None, None, "dig_down", None)]
         + [(run, None, None, climb) for climb in ("up", "down") for run in (None, "right", "left")])


def controls(move, frame):
    run, jump, use, climb = move
    tap = jump == "tap" and frame == 0               # "hold" keeps holding a jump from the move before
    return {"right": run == "right", "left": run == "left", "jump": jump is not None,
            "jump_pressed": tap, "space_pressed": tap, "use_pressed": use is not None and frame == 0,
            "up": climb == "up", "down": use == "dig_down" or climb == "down"}


def do_move(cave, move):
    for frame in range(FRAMES):
        cave.update(DT, controls(move, frame))
        if cave.result:
            return


def copy_cave(cave):
    """A copy of the cave to try a move in, without changing the real one."""
    new = copy.copy(cave)
    new.map = [row[:] for row in cave.map]
    new.you = copy.copy(cave.you)
    new.you.cave = new
    new.crumbling, new.fallen, new.changes = dict(cave.crumbling), dict(cave.fallen), dict(cave.changes)
    new.dirty, new.monsters, new.arrows, new.game = set(), [], [], Robot()
    new.swings = [copy.copy(swing) for swing in getattr(cave, "swings", ())]
    return new


def fingerprint(cave):
    """Two tries that end up the same way only need to be explored once."""
    you = cave.you
    timed = getattr(cave, "traps", None) or getattr(cave, "jets", None) or getattr(cave, "geysers", None)
    traps = round((cave.clock % (caves.TRAP_DOWN + caves.TRAP_UP)) * 5) if timed else 0
    platforms = tuple(tuple(round(v * 4) for v in p.where(cave.clock)) for p in getattr(cave, "platforms", ()))
    moves = tuple(getattr(you, name, None) for name in ("on_ground", "facing", "climbing", "hanging",
                                                        "crawling", "pounding", "on_wall", "swinging", "flung"))
    # swinging vines: how far out each one is, and how fast it's going (a vine hanging still is all zeros)
    swings = tuple((round(swing.angle * 8), round(swing.spin * 2)) for swing in getattr(cave, "swings", ()))
    flying = round(you.vx / 2) if getattr(you, "flung", False) else 0
    return (round(you.x * 4), round(you.y * 4), round(you.vy / 2), cave.got_diamond, cave.got_shard, moves,
            tuple(sorted(cave.changes.items())), tuple(sorted(cave.fallen)), traps, platforms, you.riding,
            swings, flying)


def how_high(cave, r, c, rides=(), holds=()):
    """How far up in the air this block is: 1 = right on the ground (or on a ladder, a vine
    or by a climbing wall), 2 = one block above the ground, and so on. Over a bouncy mushroom
    it counts as lower, because the mushroom throws you way up (and so does a steam geyser).
    rides: the blocks a moving platform goes through. You can stand on those, too.
    holds: the blocks a swinging vine swings through. You can hang on in those."""
    tile = cave.tile(r, c)
    if tile in caves.SOLIDS or tile in caves.LADDERS or (r, c) in rides or (r, c) in holds:
        return 0
    for rr in (r, r + 1):                 # by a climbing wall, or just over its top (you pull yourself up)
        if caves.CLIMB_WALL in (cave.tile(rr, c - 1), cave.tile(rr, c + 1)):
            return 0
    k = 1
    while r + k < cave.rows:
        below = cave.tile(r + k, c)
        if below in caves.SOLIDS or below in caves.LEDGES or below in caves.LADDERS or (r + k, c) in rides:
            return k - MUSHROOM_ROWS if below in "o" + caves.GEYSER else k
        k += 1
    return FAR_AWAY                       # nothing below but a deep hole


def steps_to(cave, goals):
    """A map of how far: for every block in the cave, how many steps to the nearest goal,
    going AROUND rock, spikes, lava and fire. So the robot heads for the way through, not
    straight at a wall. Cracked rock counts as a few extra steps (it has to dig through it),
    and a ledge (=) is a one-way door: you can jump up through it, but not drop down through it.
    It knows you can't fly, too: you can only go UP into a block that's at most a jump above
    something to stand on (or a ladder, a vine or a climbing wall to hold), and a jump only
    carries you a few blocks sideways (AIR_STEPS) before you have to land again.
    (It works backwards from the goals, so it also counts how many sideways steps in the air
    you've already used: far[r][c][used].)"""
    rides = {spot for platform in getattr(cave, "platforms", ()) for spot in platform.cells()}
    holds = {spot for swing in getattr(cave, "swings", ()) for spot in swing.reach()}
    height = [[how_high(cave, r, c, rides, holds) for c in range(cave.cols)] for r in range(cave.rows)]

    def used_after(used, rr, cc, r, c):
        """Sideways air steps used after going from (rr, cc) into (r, c), or None if you can't."""
        if height[r][c] <= JUMP_ROWS:
            return 0                      # near the ground (or on a ladder): all your air steps back
        if rr == r + 1:
            return None                   # too high up in the air to jump to
        if rr == r - 1:
            return max(0, used - 1)       # falling: you can steer a little on the way down
        return used + 1 if used < AIR_STEPS else None

    far = [[[FAR_AWAY] * (AIR_STEPS + 1) for _ in range(cave.cols)] for _ in range(cave.rows)]
    todo = []
    for r, c in goals:
        for used in range(AIR_STEPS + 1):
            far[r][c][used] = 0
            todo.append((0, r, c, used))
    heapq.heapify(todo)
    while todo:
        so_far, r, c, now = heapq.heappop(todo)
        if so_far > far[r][c][now]:
            continue                      # we already found a shorter way here
        for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            # from (rr, cc) you step into (r, c)
            if not (0 <= rr < cave.rows and 0 <= cc < cave.cols):
                continue
            tile = cave.map[rr][cc]
            if tile in WALLS or tile in NO_GO:
                continue
            if rr == r - 1 and cave.map[r][c] == "=":
                continue                  # you can't drop down through a ledge
            step = DIG_STEPS if tile in caves.DIGGABLE else 1
            for used in range(AIR_STEPS + 1):
                if used_after(used, rr, cc, r, c) == now and so_far + step < far[rr][cc][used]:
                    far[rr][cc][used] = so_far + step
                    heapq.heappush(todo, (so_far + step, rr, cc, used))
    return [[spot[0] for spot in row] for row in far]


SWING_KEEN = 10         # on a swinging vine, every bit it could still swing higher counts as this many steps


def how_far(start, far):
    """How far a cave is from the goals, on the map of how far (far). On a swinging vine it counts from
    the best block the vine can swing to, plus a bit for how much higher it could still swing:
    so the robot learns to pump the vine higher before it lets go."""
    reach = [min((far[r][c] for r, c in swing.reach() if 0 <= r < start.rows and 0 <= c < start.cols),
                 default=FAR_AWAY)
             for swing in getattr(start, "swings", ())]

    def distance(cave):
        you = cave.you
        if getattr(you, "swinging", None) is not None:
            swing = cave.swings[you.swinging]
            top = math.cos(swing.angle) - swing.spin ** 2 * you.grip / (2 * caves.SWING_GRAVITY)
            higher = max(0.0, caves.SWING_MAX - math.acos(max(-1.0, min(1.0, top))))
            return min(reach[you.swinging] + SWING_KEEN * higher, 1000)
        x, y = cave.center
        r = min(max(int(y), 0), cave.rows - 1)
        c = min(max(int(x), 0), cave.cols - 1)
        return min(far[r][c], 1000)
    return distance


def search(start, goal, goals, tries, deadline):
    """Find moves from start until goal(cave) is true, trying moves that get closer to the goals first.
    Returns (moves, the cave at the end, tries used, closest cave, moves to the closest cave, gave up?).
    "Gave up" means it ran out of tries (or time) before it had tried every way."""
    far = steps_to(start, goals)
    distance = how_far(start, far)

    heap = [(distance(start), 0, start, [])]
    seen = {fingerprint(start)}
    closest, closest_distance, closest_moves, n = start, distance(start), [], 0
    while heap and n < tries and time.time() < deadline:
        _, _, cave, moves = heapq.heappop(heap)
        for move in MOVES:
            nxt = copy_cave(cave)
            do_move(nxt, move)
            n += 1
            if nxt.game.hurt or nxt.result == "left":
                continue
            if goal(nxt):
                return moves + [move], nxt, n, nxt, moves + [move], False
            if nxt.result:
                continue
            key = fingerprint(nxt)
            if key in seen:
                continue
            seen.add(key)
            d = distance(nxt)
            if d < closest_distance:
                closest, closest_distance, closest_moves = nxt, d, moves + [move]
            heapq.heappush(heap, (d + HURRY * len(moves), n, nxt, moves + [move]))
    return None, None, n, closest, closest_moves, bool(heap)


def fresh_cave(text):
    cave = caves.Cave(Robot(), (0, 0), text)
    cave.monsters = []                   # the robot ignores monsters
    return cave


def check(text, tries=TRIES, chest_tries=CHEST_TRIES, time_limit=TIME_LIMIT):
    """Can the cave be beaten? Returns a dictionary with what the robot found out."""
    deadline = time.time() + time_limit
    start = fresh_cave(text)
    ores = [(r, c) for r, row in enumerate(start.map) for c, tile in enumerate(row) if tile == "*"]
    shards = [(r, c) for r, row in enumerate(start.map) for c, tile in enumerate(row) if tile == caves.SHARD]
    exits = [(r, c) for r, row in enumerate(start.map) for c, tile in enumerate(row) if tile == "E"]
    result = {"diamond": None, "exit": None, "seconds": 0.0, "tries": 0, "trail": [], "stuck_at": None,
              "chests": [], "gave_up": False}

    legs = []
    levers = [(r, c) for r, row in enumerate(start.map) for c, tile in enumerate(row) if tile == caves.LEVER]
    if levers and not start.gates_open():
        legs.append(("lever", lambda cave: cave.gates_open(), levers))
    if shards:
        legs.append(("sun shard", lambda cave: cave.got_shard, shards))
    if ores:
        legs.append(("diamond", lambda cave: cave.got_diamond, ores))
    if exits:
        legs.append(("exit", lambda cave: cave.result == "exit", exits))
    cave, all_moves, stuck_moves = start, [], []
    for name, goal, target in legs:
        moves, end, n, closest, closest_moves, gave_up = search(cave, goal, target, tries, deadline)
        result["tries"] += n
        result[name] = moves is not None
        if moves is None:
            result["stuck_at"] = [round(v, 2) for v in closest.center]
            result["gave_up"] = gave_up
            stuck_moves = closest_moves                 # the trail shows how close it got
            break
        all_moves += moves
        cave = end
        cave.result = None
    result["seconds"] = round(len(all_moves) * FRAMES / 60, 1)

    # Walk the moves again from the start, to draw the way the robot went
    replay = fresh_cave(text)
    for move in all_moves + stuck_moves:
        do_move(replay, move)
        result["trail"].append([round(v, 2) for v in replay.center])
        if replay.result:
            replay.result = None

    # Can every treasure chest be reached?
    for r, row in enumerate(start.map):
        for c, tile in enumerate(row):
            if tile == "T":
                moves, _, n, _, _, gave_up = search(fresh_cave(text), lambda cave, r=r, c=c: cave.map[r][c] == "t",
                                                    [(r, c)], chest_tries, deadline)
                result["chests"].append({"row": r, "column": c, "ok": moves is not None, "gave_up": gave_up})
    return result


def say(result):
    """The robot's answer in words."""
    lines = []
    if result.get("lever") is False:
        lines.append("I couldn't find a way to pull the lever, so the iron gates stay shut.")
        if result["gave_up"]:
            lines.append("(I ran out of tries, so maybe there IS a way I didn't find.)")
        return lines
    if result["diamond"] is None and result["exit"] is None:
        return ["There's no diamond and no exit to look for!"]
    if result["diamond"] is False:
        lines.append("I couldn't find a way to the diamond.")
    elif result["exit"] is False:
        lines.append("I got the diamond, but couldn't find a way to the exit.")
    elif result["diamond"] and result["exit"]:
        lines.append("Yes! The Hero can grab the diamond and reach the exit (about %d seconds)." % result["seconds"])
    elif result["exit"]:
        lines.append("The Hero can reach the exit (about %d seconds). There's no diamond yet." % result["seconds"])
    elif result["diamond"]:
        lines.append("The Hero can grab the diamond (about %d seconds). There's no exit yet." % result["seconds"])
    if result["gave_up"]:
        lines.append("(I ran out of tries, so maybe there IS a way I didn't find.)")
    elif result["diamond"] is False or result["exit"] is False:
        lines.append("I tried every way I could, so it really can't be done yet.")
    chests = result["chests"]
    if chests:
        reached = sum(chest["ok"] for chest in chests)
        maybe = sum(chest.get("gave_up", False) for chest in chests)
        lines.append("Treasure chests: %d of %d can be reached%s." % (
            reached, len(chests), " (I ran out of tries on %d)" % maybe if maybe else ""))
    return lines


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--json":     # the cave editor sends the cave and reads the answer
        text = sys.stdin.read()
        try:
            result = check(text)
        except Exception as problem:                   # tell the editor instead of crashing
            result = {"error": "%s: %s" % (type(problem).__name__, problem)}
        print(json.dumps(result))
        return
    if len(sys.argv) < 2:
        print(__doc__)
        return
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()
    print("Thinking...")
    started = time.time()
    result = check(text)
    for line in say(result):
        print(line)
    print("(%d tries in %.0f seconds)" % (result["tries"], time.time() - started))


if __name__ == "__main__":
    main()
