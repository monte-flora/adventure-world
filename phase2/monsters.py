"""
MONSTERS ON THE PHASE 2 MAP - you can see every one of them, so there are no surprise fights.

- Every land has its own mix (LAND_MONSTERS): a few weak Slimes in Home Meadow, Scorpions in the
  desert, Frost Wolves up in the peaks, Bog Lurkers in the swamp...
- A monster PATROLS near its home spot. Get within CHASE_DISTANCE squares and it CHASES you.
  Get GIVE_UP_DISTANCE away (or reach a safe square) and it gives up and walks back home.
- Safe squares: houses, the path, landmarks, signposts and village squares. Monsters never step on them.
- Monsters much weaker than you (FLEE_LEVELS levels below you) run away from you.
- Walk into a monster from BEHIND (it's facing away from you) and you get a FIRST STRIKE.
- At NIGHT more monsters come out (and go home at dawn). Beaten monsters come back slowly, far from you.

The home world only: Nightfall Hollow keeps its classic shadow monsters (and its moonrise).
This file knows nothing about graphics, so it's easy to test.
"""

import math

import rules

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
CHASE_SPEED = 0.85              # a chasing monster moves on this share of turns (at least its usual speed)
FLEE_LEVELS = 3                 # a monster this many levels below you runs away
CALM_TURNS = 5                  # after you run from a fight, the monster leaves you alone this long

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
    m.calm = 0
    return m


def get_ready(m):
    """An older monster (from a classic spawn, or an old save) gets what a Phase 2 monster needs."""
    if not hasattr(m, "home"):
        m.home, m.land, m.night, m.facing, m.state, m.calm = m.pos, None, False, "left", "patrol", 0
        m.looks_left = True
        m.level = LEVELS.get(m.base_kind, 2)
    return m


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
# Every turn
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


def think(game, m):
    """What is this monster doing this turn? patrol, chase, flee or walk back home."""
    you = game.player.pos
    near = steps(m.pos, you)
    sees_you = not player_hidden(game) and (m.special != "drowns" or game.here == "W")
    if m.calm > 0:
        m.calm -= 1
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


def step_to(game, m, pos):
    dr, dc = pos[0] - m.pos[0], pos[1] - m.pos[1]
    m.facing = {(-1, 0): "up", (1, 0): "down", (0, -1): "left", (0, 1): "right"}.get((dr, dc), m.facing)
    m.pos = pos
    if dc:
        m.looks_left = dc < 0                    # (the picture keeps looking this way while it walks up or down)


def move_one(game, m):
    think(game, m)
    you = game.player.pos
    speed = max(m.move_chance, CHASE_SPEED) if m.state in ("chase", "flee") else m.move_chance
    if game.rng.random() >= speed:
        return
    taken = {o.pos for o in game.monsters if o is not m and o.is_alive}
    options = [s for s in game.neighbors(m.pos, water=m.special == "drowns")
               if can_stand(game, m, s) and s not in taken]
    if m.special == "archer" or m.state in ("flee", "home", "patrol"):
        options = [s for s in options if s != you]      # only a chasing monster steps onto you
    if not options:
        return
    if m.state == "chase":
        best = min(steps(s, you) for s in options)
        options = [s for s in options if steps(s, you) == best]
    elif m.state == "flee":
        best = max(steps(s, you) for s in options)
        options = [s for s in options if steps(s, you) == best]
    elif m.state == "home":
        best = min(steps(s, m.home) for s in options)
        options = [s for s in options if steps(s, m.home) == best]
    else:                                                # patrol: wander, but stay near home
        options = [s for s in options if steps(s, m.home) <= PATROL_RADIUS] or options
    step_to(game, m, game.rng.choice(sorted(options)))


def move_all(game):
    get_world_ready(game)
    for m in list(game.monsters):
        if m.is_alive:
            move_one(game, get_ready(m))


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
    """You walked into it going `direction`: it's from behind if it faces (or walked) the same way."""
    return getattr(m, "facing", None) == direction
