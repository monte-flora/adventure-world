"""
MONSTERS ON THE PHASE 2 MAP - you can see every one of them, so there are no surprise fights.

- Every land has its own mix (LAND_MONSTERS): a few weak Slimes in Home Meadow, Scorpions in the
  desert, Frost Wolves up in the peaks, Bog Lurkers in the swamp...
- Monsters ROAM FREELY, all the time (not a square at a time, and not only when you move): pass_time.
- A monster PATROLS near its home spot. Get within CHASE_DISTANCE squares and it CHASES you.
  Get GIVE_UP_DISTANCE away (or reach a safe square) and it gives up and walks back home.
  One that TOUCHES you starts a fight.
- Safe squares: houses, the path, landmarks, signposts and village squares. Monsters never step on them.
- Monsters much weaker than you (FLEE_LEVELS levels below you) run away from you.
- Walk into a monster from BEHIND (it's facing away from you) and you get a FIRST STRIKE.
- At NIGHT more monsters come out (and go home at dawn). Beaten monsters come back slowly, far from you.

The home world only: Nightfall Hollow keeps its classic shadow monsters (and its moonrise).
This file knows nothing about graphics, so it's easy to test.
"""

import math

import rules

from phase2 import smooth

# ===========================================================================
# THE KINDS of monster. The classic ones (rules.MONSTER_TYPES) plus a few that only live in Phase 2.
#   level: how strong it is. If you're FLEE_LEVELS levels above it, it runs from you.
# ===========================================================================
NEW_KINDS = {
    "Slime":      {"health": 4,  "damage": (1, 1), "move_chance": 0.45, "xp": 2, "special": None},
    "Scorpion":   {"health": 9,  "damage": (2, 4), "move_chance": 0.55, "xp": 6, "special": None},
    "Frost Wolf": {"health": 10, "damage": (2, 3), "move_chance": 0.80, "xp": 6, "special": None},
    "Bog Lurker": {"health": 14, "damage": (2, 4), "move_chance": 0.35, "xp": 8, "special": "tough"},
}
LEVELS = {"Slime": 1, "Spider": 1, "Zombie": 2, "Sea Serpent": 3, "Skeleton": 3,
          "Scorpion": 4, "Frost Wolf": 4, "Ember Skull": 5, "Bog Lurker": 5}

# ===========================================================================
# WHO LIVES WHERE: the mix in each of the 8 lands of levels/world/ (stage 2a's land names).
# The numbers are for a land of LAND_SIZE squares: a bigger land gets more (up to 2x), a smaller one fewer.
# ===========================================================================
LAND_MONSTERS = {
    "Home Meadow":      {"Slime": 1, "Spider": 1},                      # home: few and weak (it is big: x2)
    "Portal Island":    {"Slime": 1},
    "Whispering Woods": {"Spider": 4, "Zombie": 2, "Slime": 1},         # the middle lands
    "The Great Lake":   {"Sea Serpent": 3, "Spider": 2, "Zombie": 2},
    "Old Ruins":        {"Skeleton": 4, "Zombie": 2},
    "Frost Peaks":      {"Frost Wolf": 5, "Skeleton": 2},               # the tough lands
    "Sunscorch Desert": {"Scorpion": 5, "Ember Skull": 3},              # (Ember Skulls in its red canyon)
    "Murk Swamp":       {"Bog Lurker": 4, "Zombie": 2, "Spider": 2},
}
OTHER_LAND = {"Spider": 2, "Zombie": 1}        # a land none of the words match
LAND_SIZE = 150
VILLAGE_REACH = 2               # a village (atlas.villages) is safe this many squares around its middle
HOME_SAFE = 5                   # no monster starts this close to home

PATROL_RADIUS = 3               # a patrolling monster stays this close to its home spot
CHASE_DISTANCE = 4              # it chases you when you're this close (steps)...
GIVE_UP_DISTANCE = 7            # ...and gives up when you get this far away...
LEASH = 10                      # ...or when it's this far from home
FLEE_LEVELS = 3                 # a monster this many levels below you runs away
CALM_SECONDS = 3.0              # after you run from a fight, the monster leaves you alone this long

RUN_SPEED = 4.25                # a chasing (or fleeing) monster goes this many squares a second: you walk 5, so you can
                                # just outrun it
ROAM_SPEED = 2.5                # patrolling or walking home: this many, times its move_chance (a Bog Lurker is slow)
REST = (0.5, 2.5)               # a patrolling monster stands still this long between walks (seconds: shortest, longest)
TOUCH = 0.7                     # a monster this close to you (middle to middle, in squares) is touching you: a fight!
CROWD = 0.6                     # monsters don't walk closer to each other than this
ARCHER_GAP = 1.5                # a Skeleton stops this far from you (it shoots)...
ARROW_SECONDS = 1.0             # ...and the Skeletons near you get a chance to shoot this often
AWAKE = 14                      # only monsters this close to you (steps) patrol: nobody can see the others
TURN_SECONDS = 0.2              # a robot or a test that plays turn by turn (game.do): monsters get this long a turn

RESPAWN_TURNS = 40              # a beaten monster comes back this many turns later...
RESPAWN_AWAY = 8                # ...at least this far from you
NOT_ON = "HPLDNQR+="            # monsters never step on these (houses, the Portal, landmarks, the path, signposts...)

DAY_TURNS = 90                  # the day lasts this many turns...
NIGHT_TURNS = 30                # ...then night this many
NIGHT_EXTRA = 0.5               # at night every land gets this many more monsters (half as many again)
DUSK_TURNS = 6                  # the sky gets darker (and lighter at dawn) over this many turns


def kind_info(kind):
    return NEW_KINDS.get(kind) or rules.MONSTER_TYPES[kind]


def make_monster(kind, pos, land=None, night=False, facing="left"):
    """A map monster. It's a rules.Monster (so fights, saving and drawing all work the same), with a home."""
    info = kind_info(kind)
    m = rules.Monster.__new__(rules.Monster)
    m.base_kind = m.kind = kind
    m.shadow = False
    m.pos = m.home = pos
    m.health = m.max_health = info["health"]
    m.damage = tuple(info["damage"])
    m.move_chance = info["move_chance"]
    m.xp = info["xp"]
    m.special = info["special"]
    m.level = LEVELS.get(kind, 2)
    m.land = land
    m.night = night               # it came out for the night (it goes home at dawn)
    m.facing = facing             # which way it looks: walk into it from behind for a first strike!
    m.looks_left = facing == "left"
    m.state = "patrol"            # "patrol", "chase", "home" (walking back) or "flee"
    m.calm = 0                    # seconds left of leaving you alone
    m.goal = None                 # where it's patrolling to ([x, y] in squares), and
    m.rest = 0.0                  # how much longer it stands still first (seconds)
    return m


def get_ready(m):
    """An older monster (from a classic spawn, or an old save) gets what a Phase 2 monster needs."""
    if not hasattr(m, "home"):
        m.home, m.land, m.night, m.facing, m.state, m.calm = m.pos, None, False, "left", "patrol", 0
        m.looks_left = True
        m.level = LEVELS.get(m.base_kind, 2)
    return m


def where(m):
    """A monster's middle, [x, y] in squares. If something else moved it (m.pos), it's in the middle of that square."""
    xy = getattr(m, "xy", None)
    if xy is None or smooth.square(xy) != tuple(m.pos):
        xy = m.xy = smooth.middle(m.pos)
    return xy


def land_mix(name):
    return LAND_MONSTERS.get(name, OTHER_LAND)


def steps(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ===========================================================================
# Where monsters may go
# ===========================================================================

def village_squares(game):
    """The squares of every village (stage 2a/2b may give the atlas villages): monsters stay out."""
    villages = getattr(getattr(game, "atlas", None), "villages", None) or ()
    if isinstance(villages, dict):
        villages = villages.values()
    squares = set()
    for v in villages:
        if isinstance(v, tuple) and len(v) == 3 and isinstance(v[1], tuple):
            (r, c), reach = v[1], VILLAGE_REACH    # stage 2a: (name, middle of its square, land)
            squares.update((rr, cc) for rr in range(r - reach, r + reach + 1) for cc in range(c - reach, c + reach + 1))
            continue
        if isinstance(v, tuple) and len(v) == 2 and all(isinstance(n, int) for n in v):
            squares.add(v)                       # just a square
            continue
        spots = getattr(v, "squares", None) or (v.get("squares") if isinstance(v, dict) else None)
        if spots:
            squares.update(tuple(s) for s in spots)
            continue
        box = getattr(v, "box", None) or (v if isinstance(v, (tuple, list)) and len(v) == 4 else None)
        if box:
            top, left, bottom, right = box
            squares.update((r, c) for r in range(top, bottom + 1) for c in range(left, right + 1))
    return squares


def is_safe(game, pos):
    """Monsters never come here: houses, the path, landmarks, signposts and villages."""
    return game.tile(pos) in NOT_ON or pos in game.safe_squares


def can_stand(game, m, pos):
    if not game.in_bounds(pos) or is_safe(game, pos):
        return False
    letter = game.tile(pos)
    if m.special == "drowns":
        return letter == "W"                     # Sea Serpents only swim
    return letter in rules.WALKABLE


# ===========================================================================
# Putting monsters on the map
# ===========================================================================

def land_squares(game):
    """Land name -> [squares a monster could start on], and the lake squares in each land."""
    ground, water = {}, {}
    lakes = game.big_lakes()
    for r in range(game.rows):
        for c in range(game.cols):
            land = game.land_name((r, c))
            if not land or steps((r, c), game.start) < HOME_SAFE or is_safe(game, (r, c)):
                continue
            letter = game.map[r][c]
            if letter in "FGMBIV":
                ground.setdefault(land, []).append((r, c))
            elif letter == "W" and (r, c) in lakes:
                water.setdefault(land, []).append((r, c))
    return ground, water


def land_counts(game, ground):
    """Land name -> {kind: how many} for the day."""
    plan = {}
    for land, spots in ground.items():
        scale = min(2.0, max(0.5, len(spots) / LAND_SIZE))
        plan[land] = {kind: max(1, round(n * scale)) for kind, n in land_mix(land).items()}
    return plan


def spawn(game, land, kind, ground, water, night=False, away_from=None):
    """Put one monster of this kind in this land (or None if there's no room)."""
    spots = water.get(land, []) if kind_info(kind)["special"] == "drowns" else ground.get(land, [])
    taken = {m.pos for m in game.monsters if m.is_alive}
    spots = [s for s in spots if s not in taken and s != game.player.pos
             and (away_from is None or steps(s, away_from) >= RESPAWN_AWAY)]
    if not spots:
        return None
    m = make_monster(kind, game.rng.choice(spots), land, night, game.rng.choice(list(rules.DIRECTIONS)))
    game.monsters.append(m)
    return m


def get_world_ready(game):
    """What the game needs to keep track of monsters (an older save may not have it yet)."""
    if not hasattr(game, "respawns"):
        game.respawns = []                       # (land, kind, the turn it comes back)
        game.was_night = is_night(game)
    if not hasattr(game, "safe_squares"):
        game.safe_squares = village_squares(game)
    if not hasattr(game, "monster_plan"):
        game.monster_plan = land_counts(game, land_squares(game)[0])


def spawn_all(game):
    """Every land's monsters for the day. Returns the list (the game keeps it in game.monsters)."""
    game.monsters = []
    game.respawns, game.was_night = [], False
    game.safe_squares = village_squares(game)
    ground, water = land_squares(game)
    game.monster_plan = land_counts(game, ground)
    for land in sorted(game.monster_plan):
        for kind, count in game.monster_plan[land].items():
            if kind_info(kind)["special"] == "drowns" and not water.get(land):
                continue                         # no lake big enough here
            for _ in range(count):
                spawn(game, land, kind, ground, water)
    return game.monsters


# ===========================================================================
# Day and night
# ===========================================================================

def time_of_day(turn):
    """(is it night?, how dark: 0.0 day ... 1.0 deep night)."""
    t = turn % (DAY_TURNS + NIGHT_TURNS)
    if t >= DAY_TURNS:                                   # night: darker and darker, then deep night
        return True, min(1.0, (t - DAY_TURNS + 1) / DUSK_TURNS)
    if turn > DAY_TURNS and t < DUSK_TURNS:              # dawn: lighter and lighter
        return False, 1 - (t + 1) / DUSK_TURNS
    return False, 0.0


def is_night(game):
    return game.world == 1 and time_of_day(game.turn)[0]


def darkness(game):
    return time_of_day(game.turn)[1] if game.world == 1 else 0.0


def dusk(game):
    """Night falls: more monsters come out."""
    game.log("The sun goes down. More monsters come out at night! Stay near the path and the houses.", "bad")
    game.sound("alert")
    ground, water = land_squares(game)
    for land in sorted(game.monster_plan):
        extra = math.ceil(sum(game.monster_plan[land].values()) * NIGHT_EXTRA)
        kinds = [k for k in game.monster_plan[land] if kind_info(k)["special"] != "drowns" or water.get(land)]
        for _ in range(extra if kinds else 0):
            spawn(game, land, game.rng.choice(sorted(kinds)), ground, water, night=True, away_from=game.player.pos)


def dawn(game):
    """The sun comes up: the night monsters go away (unless one is chasing you right now)."""
    game.log("The sun comes up. The night monsters creep away.", "good")
    game.monsters = [m for m in game.monsters
                     if not (getattr(m, "night", False) and m.state != "chase")]


# ===========================================================================
# All the time (pass_time), and every turn (turn_passed)
# ===========================================================================

def respawn(game):
    """Beaten monsters come back after a while, far from you."""
    due = [r for r in game.respawns if r[2] <= game.turn]
    if not due:
        return
    game.respawns = [r for r in game.respawns if r[2] > game.turn]
    ground, water = land_squares(game)
    for land, kind, _ in due:
        if not spawn(game, land, kind, ground, water, away_from=game.player.pos):
            game.respawns.append((land, kind, game.turn + RESPAWN_TURNS // 2))    # no room: try again later


def beaten(game, monster):
    """A day monster you beat comes back RESPAWN_TURNS later (night ones don't)."""
    land = getattr(monster, "land", None)
    if land and not getattr(monster, "night", False):
        game.respawns.append((land, monster.base_kind, game.turn + RESPAWN_TURNS))


def player_hidden(game):
    """Monsters can't see you on a safe square (a house, the path, a village...) or in the tall reeds."""
    p = game.player.pos
    return is_safe(game, p) or game.tile(p) == "B"


def think(game, m, dt):
    """What is this monster doing now? patrol, chase, flee or walk back home. (dt: seconds since last time.)"""
    you = game.player.pos
    near = steps(m.pos, you)
    sees_you = not player_hidden(game) and (m.special != "drowns" or game.here == "W")
    if m.calm > 0:
        m.calm -= dt
        m.state = "home" if m.state in ("chase", "flee") else m.state
        return
    if game.player.level >= m.level + FLEE_LEVELS and near <= CHASE_DISTANCE and sees_you:
        m.state = "flee"
    elif m.state == "flee" and near > CHASE_DISTANCE:
        m.state = "home"
    elif m.state == "chase":
        if not sees_you or near > GIVE_UP_DISTANCE or steps(m.pos, m.home) > LEASH:
            m.state = "home"                     # it gives up and goes back
    elif near <= CHASE_DISTANCE and sees_you and steps(m.pos, m.home) <= LEASH:
        m.state = "chase"
    if m.state == "home" and steps(m.pos, m.home) <= PATROL_RADIUS:
        m.state = "patrol"


def patrol_goal(game, m):
    """Somewhere near home to wander to: the middle of a square it can stand on (or None)."""
    r, c = m.home
    reach = range(-PATROL_RADIUS, PATROL_RADIUS + 1)
    spots = [(r + dr, c + dc) for dr in reach for dc in reach if abs(dr) + abs(dc) <= PATROL_RADIUS]
    spots = [s for s in spots if can_stand(game, m, s)]
    return smooth.middle(game.rng.choice(spots)) if spots else None


def stand_still(game, m):
    m.goal = None
    m.rest = REST[0] + game.rng.random() * (REST[1] - REST[0])


def roam(game, m, dt, others):
    """One monster for dt seconds (a short time): it thinks, then walks: straight at you, away from you,
    home, or to a spot near home. It slides along what it can't stand on."""
    think(game, m, dt)
    xy, you = where(m), smooth.where(game)
    speed = RUN_SPEED
    if m.state == "chase":
        goal = you
    elif m.state == "flee":
        goal = [2 * xy[0] - you[0], 2 * xy[1] - you[1]]         # straight away from you
    else:
        speed = ROAM_SPEED * m.move_chance
        if m.state == "home":
            goal = smooth.middle(m.home)
        else:                                                    # patrol: wander, but stay near home
            m.rest = getattr(m, "rest", 0.0) - dt
            if m.rest > 0:
                return
            goal = m.goal = getattr(m, "goal", None) or patrol_goal(game, m)
    dx, dy = (goal[0] - xy[0], goal[1] - xy[1]) if goal else (0, 0)
    far = math.hypot(dx, dy)
    if far < 0.05:                                               # it's there (or has nowhere to go)
        stand_still(game, m)
        return
    go = min(far, speed * dt) / far
    new = smooth.slide(xy, dx * go, dy * go, lambda pos: can_stand(game, m, pos))
    gap = math.dist(new, you)
    keep_off = ARCHER_GAP if m.special == "archer" else 0 if m.state == "chase" else TOUCH
    if new == xy or (gap < keep_off and gap < math.dist(xy, you)) or any(
            o is not m and math.dist(new, o.xy) < min(CROWD, math.dist(xy, o.xy)) for o in others):
        if m.state == "patrol":                                  # something's in the way: try somewhere else
            stand_still(game, m)
        return                                   # (only a chasing monster walks into you, and never a Skeleton)
    if abs(dx) >= abs(dy):
        m.facing = "left" if dx < 0 else "right"
        m.looks_left = dx < 0                    # (the picture keeps looking this way while it walks up or down)
    else:
        m.facing = "up" if dy < 0 else "down"
    m.xy, m.pos = new, smooth.square(new)


def touch(game):
    """Is a monster touching you? Then the fight starts (not on a safe square: a house, the path...).
    Returns the monster. A Sea Serpent only gets you in your boat, and nothing else does there."""
    if game.battle or game.here in rules.SAFE or is_safe(game, game.player.pos):
        return None
    you = smooth.where(game)
    for m in game.monsters:
        if m.is_alive and steps(m.pos, game.player.pos) <= 1 and getattr(m, "calm", 0) <= 0 \
                and (m.special == "drowns") == (game.here == "W") and math.dist(where(m), you) < TOUCH:
            game.start_battle(m)
            return m
    return None


def pass_time(game, dt):
    """The map's monsters live for dt seconds: they roam, chase and flee, one that touches you starts a
    fight, and Skeletons shoot."""
    get_world_ready(game)
    for m in game.monsters:
        where(get_ready(m))
    while dt > 0 and not game.battle and game.player.is_alive:
        step = min(dt, smooth.STEP)
        dt -= step
        awake = [m for m in game.monsters                       # (one far away walks home first, then sleeps)
                 if m.is_alive and (m.state != "patrol" or steps(m.pos, game.player.pos) <= AWAKE)]
        for m in awake:
            roam(game, m, step, awake)
        if touch(game):
            return
        game.arrow_clock = getattr(game, "arrow_clock", 0.0) + step
        if game.arrow_clock >= ARROW_SECONDS:
            game.arrow_clock = 0.0
            rules.Game.archers_shoot(game)


def turn_passed(game):
    """Called at the end of every turn on the home map: night and day, monsters coming back."""
    get_world_ready(game)
    night = is_night(game)
    if night and not game.was_night:
        dusk(game)
    elif game.was_night and not night:
        dawn(game)
    game.was_night = night
    respawn(game)


# ===========================================================================
# Touching a monster
# ===========================================================================

def from_behind(m, direction):
    """You walked into it going `direction`: it's from behind if it faces (or walks) the same way."""
    return getattr(m, "facing", None) == direction


def behind(game, m):
    """Are you behind it? (It's looking away from you.)"""
    you, it = smooth.where(game), where(m)
    dx, dy = it[0] - you[0], it[1] - you[1]
    way = ("left" if dx < 0 else "right") if abs(dx) >= abs(dy) else ("up" if dy < 0 else "down")
    return from_behind(m, way)
