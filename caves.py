"""
CAVES for Adventure World.

When you explore a Mine, you climb down into a cave and the game turns
sideways: now you run and JUMP, like a platform game. Dig through cracked
rock, open treasure chests, fight monsters, and mine the diamond - if this cave has one!

Like rules.py, this file knows nothing about graphics. It only keeps track
of where everything is, how fast it's moving, and what it bumps into.
game.py draws it.

Distances are in TILES (one block = 1) and time is in SECONDS.
"""

import math
import os
import random

# ===========================================================================
# HOW JUMPING FEELS - try changing these!
# ===========================================================================
RUN_SPEED = 6.0        # tiles per second
RUN_ACCEL = 45.0       # how quickly you speed up on the ground (bigger = snappier)
AIR_ACCEL = 30.0       # how well you can steer in the air
GRAVITY = 40.0         # how hard you fall
JUMP_SPEED = 14.0      # how hard you jump: 14 gets you up 2 blocks, but not 3
SPEEDY_RUN = 1.0       # the Speedy power (pick it when you level up) adds this to RUN_SPEED
SPRINGY_JUMP = 1.0     # the Springy power adds this to JUMP_SPEED: 15 jumps about 2.8 blocks high, 16 about 3.2
SHORT_HOP = 2.5        # let go of jump early and gravity gets this many times stronger
MAX_FALL = 18.0        # the fastest you can fall
COYOTE_TIME = 0.1      # you can still jump this long after running off a ledge
JUMP_BUFFER = 0.12     # a jump you press this long before landing still counts

PLAYER_W = 0.8         # the size of your body, in tiles
PLAYER_H = 1.15

# ===========================================================================
# OUCH!
# ===========================================================================
FALL_DAMAGE = 1        # falling down a deep hole
SPIKE_DAMAGE = 2
LAVA_DAMAGE = 3
FIRE_DAMAGE = 2        # touching a fire (red lava caves have fires on the floor)
DIZZY_TIME = 0.6       # after falling in a hole or a hazard you can't move for this long
SAFE_TIME = 1.0        # after you get hurt you blink, and nothing can hurt you again for this long
KNOCKBACK = 7.0        # how far monsters knock you back

# ===========================================================================
# FIGHTING AND DIGGING (press R)
# ===========================================================================
SWING_TIME = 0.35      # how long one swing of your sword or pickaxe takes
SWORD_REACH = 1.0      # how far in front of you your sword reaches
TOUCH_DEPTH = 0.15     # a monster that's after you stops once it's this far into you (enough to bump you)
PUSH_APART = 6.0       # how fast a monster slides back out if it ends up inside you (blocks a second)
STOMP_DAMAGE = 3       # damage for jumping on a monster's head
STOMP_BOUNCE = 11.0    # how high you bounce off it
BOUNCE_SPEED = 22.0    # bouncy mushrooms throw you this hard: about 6 blocks up!
GEM_XP = 2             # every glittering gem you grab is worth this much XP
SHOOT_SPEED = 14.0     # your arrows fly this fast (press F)
SHOOT_TIME = 0.4       # and you can shoot one this often
CRUMBLE_TIME = 0.9     # crumbly ledges fall this long after you step on them...
CRUMBLE_BACK = 3.0     # ...and come back this long after that
TRAP_DOWN = 1.3        # spike traps (A) hide in the floor this long...
TRAP_UP = 0.9          # ...then pop up for this long. Run across while they're down!

# ===========================================================================
# LADDERS AND NEW MOVES - try changing these too!
# ===========================================================================
CLIMB_SPEED = 4.0      # how fast you climb a ladder (H) with UP and DOWN
WALL_CLIMB_SPEED = 3.0 # hold UP next to a climbing wall (%) and you climb it this fast
WALL_SLIDE = 2.5       # hold toward a climbing wall and you slide down it this slowly...
WALL_JUMP_PUSH = 6.5   # ...then SPACE jumps you off it, this hard away from the wall
WALL_JUMP_TIME = 0.18  # just after a wall jump you can't steer for this long
LEDGE_REACH = 0.45     # how close your hands must get to a ledge's edge to catch it
HANG_TIME = 0.2        # you hang on a ledge this long, then pull yourself up (or press UP or SPACE)
POUND_SPEED = 22.0     # a ground pound (press DOWN in the air) slams down this fast
POUND_DAMAGE = 5       # landing a ground pound on a monster hurts it this much...
POUND_STUN = 1.0       # ...and makes it dizzy for this long
CRAWL_H = 0.6          # how tall you are when you crawl (hold DOWN): you fit through 1-block tunnels
CRAWL_SPEED = 3.0      # and how fast you crawl

# ===========================================================================
# VINES, ICE, HEALING SPRINGS AND RISING LAVA - try changing these too!
# ===========================================================================
ICE_GRIP = 6.0         # on slippery ice (I) you speed up and slow down this slowly (on rock it's RUN_ACCEL)
FOUNTAIN_REFILL = 60.0 # after you drink from a healing spring (u), it takes this many seconds to fill up again
LAVA_RISE_WAIT = 2.0   # with "lava rises: yes", the lava starts rising this long after you grab the diamond...
LAVA_RISE_SPEED = 1.0  # ...and rises this many blocks every second. Climb to the exit, quick!

# ===========================================================================
# SECRET WALLS, LEVERS AND GATES, FLAME JETS, STEAM GEYSERS AND MOVING PLATFORMS
# Flame jets and geysers go off together with the spike traps: TRAP_DOWN off, then TRAP_UP on.
# ===========================================================================
JET_TALL = 3           # a flame jet (J) shoots fire this many blocks up (its own block, and 2 above it)
GEYSER_SPEED = 24.0    # a steam geyser (M) throws you this hard while it puffs: about 7 blocks up!
WARNING_TIME = 0.4     # flame jets and geysers fizzle this long before they go off
PLATFORM_SPEED = 2.0   # moving platforms go this many blocks a second (P side to side, U up and down)
PLATFORM_WIDTH = 2     # a platform that slides along a row of P's is this many blocks wide
PLATFORM_ROOM = 2      # air blocks you need above an up-and-down track's top, to fit on the platform (the editor checks)
PLATFORM_CATCH = 0.08  # a platform coming up under your feet still catches you if they're this far into it
SWING_GRAVITY = 30.0   # a swinging vine (R) swings this hard: bigger = faster swings
SWING_PUMP = 12.0      # hold LEFT or RIGHT the way you're swinging, and you swing this much higher
SWING_MAX = 1.0        # the highest a vine can swing, to each side (1.0 is about 57 degrees)
SWING_DRAG = 0.1       # a vine you hang on slows down a tiny bit...
SWING_SETTLE = 1.5     # ...and one you let go of slows down fast, then hangs still
SWING_HOP = 4.0        # SPACE lets go with a little hop, on top of the swing's speed
SWING_WAIT = 0.35      # just let go of a vine: don't grab one again for this long
SWING_HANDS = 0.2      # how far below the top of your head your hands hold the vine

TIPS = {               # what the game tells you the first time you find something new
    "ladder": "A ladder! Press UP to climb it, and SPACE to jump off.",
    "vine": "A vine! Jump into it and press UP to grab it. SPACE leaps off to the next one.",
    "wall": "A climbing wall! Hold UP to climb it, and SPACE to jump off it.",
    "tunnel": "Too low to walk through! Hold DOWN to crawl.",
    "ice": "Slippery ice! You slide a little before you stop.",
    "secret": "A secret passage! Some rock is only pretend. What else is hiding in here?",
    "lever": "A lever! Press R next to it to pull it.",
    "gate": "An iron gate! Find the lever that opens it.",
    "jet": "A flame jet! It shoots fire up, then stops. Run past while it's off!",
    "geyser": "A steam geyser! Stand on it and wait: WHOOSH, it throws you way up!",
    "platform": "A moving platform! Hop on and ride it.",
    "swing": "A swinging vine! Jump into it to grab it. Press LEFT and RIGHT to swing higher, and SPACE to let go!",
}

# ===========================================================================
# MONSTERS IN CAVES
# Their health, damage and XP come from MONSTER_TYPES in rules.py.
# How fast they walk comes from their move_chance (a speedy monster is fast here too).
# ===========================================================================
CAVE_MONSTERS = {"z": "Zombie", "k": "Skeleton", "c": "Ember Skull", "x": "Spider"}
MONSTER_SIZE = {"Zombie": (0.8, 1.15), "Skeleton": (0.75, 1.15),
                "Ember Skull": (0.8, 1.0), "Spider": (1.0, 0.7)}
HOPPERS = {"Spider"}   # monsters that hop around while they chase you

# HOW MONSTERS GUARD THEIR SPOT - try changing these!
PATROL_RANGE = 2.0     # a monster walks back and forth this many blocks to each side of where it started
CHASE_RANGE = 3.0      # it only comes after you when you're this many blocks away (or closer)...
SAME_LEVEL = 0.9       # ...and on its level: your feet this close to its feet. Above it or below it, it can't see you!
SIGHT = 7.0            # a Skeleton can see you this far away (on its level, too)
SKELETON_AIM = 1.2     # when a Skeleton first sees you, it draws its bow this long before the first arrow...
ARROW_SPEED = 9.0      # ...then shoots arrows this fast...
ARROW_EVERY = 2.2      # ...this often
FUSE_TIME = 1.5        # an Ember Skull flares up this long before it blows up
BLAST_RADIUS = 2.2     # how close you have to be to get hurt by the BOOM

# ===========================================================================
# TREASURE CHESTS - what might be inside? (bigger number = more likely)
# ===========================================================================
CHEST_LOOT = [("food", 3), ("sword", 2), ("pickaxe", 2), ("armor", 1), ("xp", 2), ("arrows", 2), ("trap", 2)]
CHEST_XP = 5           # gold coins are worth this much XP
RING_CHANCE = 0.33     # and 33 chests out of 100 also hide a diamond ring for your sword!
LUCKY_RING_CHANCE = 0.5    # with the Lucky power (pick it when you level up) it's 50 out of 100

# ===========================================================================
# THE CAVES - drawn by hand, one text file each, in the levels/caves folder.
# Open one in the cave editor (pixi run editor), change it and press Save:
# the game plays your new cave the next time it starts.
# (You can open them in any text editor too. levels/README.md says what every letter means.)
#
# The file names start with a number. Cave 01 goes under the Mine closest to home, 02 under
# the next one, and so on. So keep them in order, from the easiest to the hardest!
# EVERY Mine plays one of these files (plan_caves, further down, has the rule): a map with
# more Mines than files uses the files again, 01 first.
# The kid drew four of them in the cave editor (blue lvl 1, green lvl 1 and 2, red lvl 1).
# Three follow the CAVE RECIPE, six steps and a secret:
#   1. come in (a safe start)   2. learn the cave's one new thing, where a mistake doesn't hurt
#   3. try it again, harder     4. rest (gems and a healing spring)   5. a twist (the new thing + an old one)
#   6. the treasure (the diamond, or a chest)   + a secret room, with gems that hint the way
# ===========================================================================
LEVELS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels")


def level_files(kind):
    """Every drawing in the levels/<kind> folder ("caves" or "castle"), in the order of their
    file names. Returns a list of (path, text)."""
    folder = os.path.join(LEVELS_FOLDER, kind)
    found = []
    for name in sorted(f for f in os.listdir(folder) if f.endswith(".txt")):
        with open(os.path.join(folder, name), encoding="utf-8") as f:
            found.append((os.path.join(folder, name), f.read()))
    return found


CAVE_LEVEL_FILES = level_files("caves")
CAVE_LEVELS = [text for path, text in CAVE_LEVEL_FILES]
# The 3 dark "shadow" caves under the Mines in Nightfall Hollow, easiest first (levels/shadow folder).
# Each has a diamond (*) and a harder-to-reach Sun Shard (s).
SHADOW_CAVE_FILES = level_files("shadow")
SHADOW_CAVES = [text for path, text in SHADOW_CAVE_FILES]
# The cave under the Secret Mine (levels/secret folder). It always has a diamond (*).
SECRET_CAVE_FILES = level_files("secret")
SECRET_CAVES = [text for path, text in SECRET_CAVE_FILES]

CAVE_DISTANCE_STEP = 10    # every 10 steps farther from home, the caves get harder
CAVE_HEIGHT = 20           # a tall cave has this many rows (a low one has 14)
THEMES = ["stone", "crystal", "lava", "moss"]           # how a cave looks

SHARD = "s"                # Sun Shard ore (shadow caves in Nightfall Hollow): dig it out like a diamond
SOLIDS = "#B*so%IGM"       # tiles you can't walk through
DIGGABLE = "B*s"           # tiles your pickaxe can break
SECRET = "F"               # a secret wall: it looks just like rock, but you can walk right through it
GATE, OPEN_GATE = "G", "g"     # an iron gate, and one that a lever (L) opened
LEVER, PULLED_LEVER = "L", "l"
JET = "J"                  # a flame jet: fire shoots up out of it, then stops
GEYSER = "M"               # a steam geyser (M for mist): a block that throws you way up while it puffs
PLATFORMS = {"P": "x", "U": "y"}   # moving platforms: P slides side to side, U goes up and down
SWINGING_VINE = "R"        # a swinging vine (R for rope): a column of R's hangs from the rock above the top one
LEDGES = "=-"              # tiles you can stand on, but jump up through
LADDERS = "HV"             # ladders and vines: the top of one works like a ledge, too
ICE = "I"                  # slippery!
CLIMB_WALL = "%"           # the only walls you can wall jump on
HAZARDS = {"^": SPIKE_DAMAGE, "~": LAVA_DAMAGE, "A": SPIKE_DAMAGE, "!": FIRE_DAMAGE, "J": FIRE_DAMAGE}
HAZARD_TOP = {"^": 0.55, "~": 0.3, "A": 0.55, "!": 0.5, "J": 0.6}   # how far down the tile the hazard starts
HAZARD_NAMES = {"^": "spikes", "A": "spikes", "~": "lava", "!": "fire", "J": "flame jet"}
OUCH = {"^": "Ouch! Spikes!", "A": "Ouch! Spikes!", "~": "Hot hot HOT! You touched the lava!",
        "!": "Ouch! Fire! Jump over the flames!", "J": "Ouch! A flame jet! Run past while it's off."}
TIMED = "AJM"              # spike traps, flame jets and geysers: they all go off together

EPS = 1e-6                 # a tiny number, so touching a wall doesn't count as being inside it


def level_lines(text):
    """The rows of a cave drawing, without its setting lines (like "theme: lava")."""
    return [line.strip() for line in text.strip().splitlines() if ":" not in line]


def level_setting(text, name, default=None):
    """What a setting line at the top of a cave drawing says: "theme: lava" gives "lava"."""
    for line in text.strip().splitlines():
        if line.strip().startswith(name + ":"):
            return line.split(":", 1)[1].strip()
    return default


def level_theme(text):
    return level_setting(text, "theme", "stone")


def parse_level(text):
    rows = [list(line) for line in level_lines(text)]
    if len({len(row) for row in rows}) != 1:
        raise ValueError("Every row of a cave must be the same length")
    return rows


def how_hard(distance_from_home):
    """1 = easy, 2 = medium, 3 = hard. The farther from home, the harder the cave."""
    return min(3, 1 + distance_from_home // CAVE_DISTANCE_STEP)


def plan_cave_files(mines, home):
    """Which cave file goes under which Mine. Returns {mine: number}: 0 is the first file in levels/caves.

    THE RULE: every Mine plays a cave from a file in levels/caves, so the editor can open every one.
    - As many Mines as files (the map today): the nearest Mine gets file 01, the next one 02, and so on.
    - More Mines than files: the files go round again. Count the Mines from the nearest to the
      farthest: 01, 02, ... up to the last file, then 01, 02, ... once more.
    - Fewer Mines than files: the nearest Mine gets file 01, the farthest gets the last file,
      and the Mines in between get files spread out in between.
    The game never makes up a cave: to get a new cave, draw a new file."""
    def steps_from_home(mine):
        return abs(mine[0] - home[0]) + abs(mine[1] - home[1])
    by_distance = sorted(mines, key=lambda mine: (steps_from_home(mine), mine))
    files = len(CAVE_LEVELS)
    if not files:
        raise ValueError("There are no cave files in levels/caves: every Mine needs one")
    if len(by_distance) >= files:
        return {mine: i % files for i, mine in enumerate(by_distance)}
    return {mine: 0 if len(by_distance) == 1 else round(i * (files - 1) / (len(by_distance) - 1))
            for i, mine in enumerate(by_distance)}


def plan_caves(mines, home):
    """Give every Mine on the map a cave from a file (plan_cave_files has the rule). Returns {mine: cave}."""
    return {mine: CAVE_LEVELS[number] for mine, number in plan_cave_files(mines, home).items()}


def approach(value, target, step):
    """Move value toward target, but by no more than step."""
    if value < target:
        return min(value + step, target)
    return max(value - step, target)


def sign(value):
    return 1 if value > 0 else -1


# ===========================================================================
# DIAMONDS - not every cave has one! Explore the map to find the ones that do.
# The same Mine always gets the same answer, just like it always gets the same cave.
# In a cave without a diamond, a treasure chest sits where the diamond ore was.
# ===========================================================================
DIAMOND_CHANCE = {1: 0.5, 2: 0.25, 3: 0.2}   # how likely an easy, medium and hard cave is to have a diamond
DIAMOND_MINES_ON_LAND = 5    # at least this many Mines you can walk to (no boat needed) always have one


def steps_between(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def pick_diamond_mines(plan, home, can_walk_to):
    """Which Mines have a diamond in their cave? Returns a set of Mines."""
    # Mines you can walk to, nearest first (a cave drawn without diamond ore can't have a diamond)
    walkable = sorted((mine for mine in plan if mine in can_walk_to and "*" in plan[mine]),
                      key=lambda mine: (steps_between(mine, home), mine))
    chosen = set(walkable[:1])            # the Mine nearest home always has one, so your first trip pays off
    for mine in plan:
        roll = random.Random("diamond at %d,%d" % mine).random()       # the same Mine always rolls the same
        if "*" in plan[mine] and roll < DIAMOND_CHANCE[how_hard(steps_between(mine, home))]:
            chosen.add(mine)
    # Always enough diamonds to finish the game: if there aren't, the nearest Mines get one too
    for mine in walkable:
        if sum(other in chosen for other in walkable) >= DIAMOND_MINES_ON_LAND:
            break
        chosen.add(mine)
    return chosen


def without_diamond(text):
    """The same cave, but a treasure chest sits where the diamond ore was."""
    return text.replace("*", "T")


# ===========================================================================
# Bodies: anything that falls and bumps into walls - you, and the monsters
# ===========================================================================

class Body:
    def __init__(self, cave, x, y, w, h):
        self.cave = cave
        self.x, self.y = x, y             # the top-left corner of the body
        self.w, self.h = w, h
        self.vx = 0.0                     # speed: + is right, - is left
        self.vy = 0.0                     # speed: + is down, - is up
        self.facing = 1                   # 1 = right, -1 = left
        self.on_ground = False
        self.standing_on = []             # the tiles under your feet
        self.riding = None                # the moving platform you're standing on (its number)

    @property
    def center(self):
        return (self.x + self.w / 2, self.y + self.h / 2)

    def rows(self):
        return range(math.floor(self.y), math.floor(self.y + self.h - EPS) + 1)

    def cols(self):
        return range(math.floor(self.x), math.floor(self.x + self.w - EPS) + 1)

    def touches(self, x, y, w, h):
        """Does this body overlap the box at x, y with width w and height h?"""
        return self.x < x + w and x < self.x + self.w and self.y < y + h and y < self.y + self.h

    def touches_body(self, other):
        return self.touches(other.x, other.y, other.w, other.h)

    def move_x(self, dx):
        """Returns True if you bumped into a wall."""
        cave = self.cave
        self.x += dx
        if dx > 0:
            c = math.floor(self.x + self.w - EPS)
            if any(cave.is_solid(r, c) for r in self.rows()):
                self.x = c - self.w
                self.vx = 0.0
                return True
        elif dx < 0:
            c = math.floor(self.x)
            if any(cave.is_solid(r, c) for r in self.rows()):
                self.x = c + 1
                self.vx = 0.0
                return True
        return False

    def move_y(self, dy):
        """Returns how fast you were falling if you just landed, otherwise 0."""
        cave = self.cave
        old_feet = self.y + self.h
        self.y += dy
        was_on_ground = self.on_ground
        self.on_ground = False
        self.standing_on = []
        self.riding = None
        if dy > 0:
            r = math.floor(self.y + self.h - EPS)
            for c in self.cols():
                tile = cave.tile(r, c)
                # Ledges (and the top rung of a ladder) only hold you up if you come down on them from above
                ledge = tile in LEDGES or (cave.ladder_top(r, c) and not getattr(self, "climbing", False))
                if tile in SOLIDS or (ledge and old_feet <= r + EPS):
                    self.standing_on.append((r, c))
            if self.standing_on:
                landed = 0.0 if was_on_ground else self.vy
                self.y = r - self.h
                self.vy = 0.0
                self.on_ground = True
                return landed
            platform = self.platform_under(old_feet)
            if platform is not None:          # landed on a moving platform (it holds you up like a ledge)
                landed = 0.0 if was_on_ground else self.vy
                self.y = cave.platform_spot(platform)[1] - self.h
                self.vy = 0.0
                self.on_ground = True
                self.riding = platform
                return landed
        elif dy < 0:
            r = math.floor(self.y)
            if any(cave.is_solid(r, c) for c in self.cols()):
                self.y = r + 1                   # bonk! hit your head
                self.vy = 0.0
        return 0.0

    def platform_under(self, old_feet):
        """A moving platform you just came down onto from above (which one: its number), or None.
        Only you ride platforms: monsters walk around them."""
        cave = self.cave
        if self is not cave.you:
            return None
        feet = self.y + self.h
        for i in range(len(cave.platforms)):
            x, y = cave.platform_spot(i)
            if old_feet <= y + PLATFORM_CATCH and feet >= y and self.x < x + cave.platforms[i].w and x < self.x + self.w:
                return i
        return None

    def fall(self, dt, gravity=GRAVITY):
        self.vy = min(MAX_FALL, self.vy + gravity * dt)


class Explorer(Body):
    """You!"""
    def __init__(self, cave, x, y):
        super().__init__(cave, x, y, PLAYER_W, PLAYER_H)
        self.coyote = 0.0                 # time left to jump after leaving the ground
        self.buffer = 0.0                 # time left on a jump you pressed early
        self.safe = (x, y)                # the last place you stood on solid ground
        self.dizzy = 0.0                  # time left before you can move again
        self.safe_time = 0.0              # time left before you can be hurt again
        self.swing = 0.0                  # time left on a swing of your sword or pickaxe
        self.tool = None                  # what you're swinging: "pickaxe", "sword" or "fist"
        self.bounced = False              # thrown up by a mushroom (that always goes full height)
        self.reload = 0.0                 # time until you can shoot another arrow
        self.climbing = False             # on a ladder?
        self.ladder_col = None            # ...which column the ladder is in
        self.ladder_wait = 0.0            # just jumped off a ladder: don't grab it again straight away
        self.hanging = 0                  # hanging from a ledge: 1 = it's on your right, -1 = on your left
        self.ledge = None                 # the block you're hanging from
        self.hang_time = 0.0
        self.hang_wait = 0.0              # just let go of a ledge: don't catch it again straight away
        self.crawling = False             # holding DOWN on the ground
        self.pounding = False             # slamming down in a ground pound
        self.wall_side = 0                # sliding down a climbing wall: which side it's on
        self.wall_time = 0.0              # you can still wall jump for this long after sliding
        self.wall_push = 0.0              # flying away from a wall after a wall jump
        self.on_wall = 0                  # climbing a climbing wall: 1 = it's on your right, -1 = on your left
        self.down_was_held = False
        self.swinging = None              # hanging on a swinging vine: which one (its number)
        self.grip = 0.0                   # ...and how far down it your hands are
        self.swing_wait = 0.0             # just let go of a vine: don't grab one again straight away
        self.flung = False                # flying off a vine: you keep its speed until you land


class CaveMonster(Body):
    def __init__(self, cave, info, x, y, spawn=None):
        w, h = MONSTER_SIZE.get(info.base_kind, (0.8, 1.1))
        super().__init__(cave, x + (1 - w) / 2, y + 1 - h, w, h)
        self.info = info                  # the rules.Monster: health, damage, xp, special
        self.kind = info.base_kind        # which picture to draw ("Zombie" - even for a Shadow Zombie)
        self.name = info.kind             # what to call it ("Shadow Zombie")
        self.spawn = spawn                # which tile it started on, so it stays gone once beaten
        self.speed = info.move_chance * 5
        self.direction = -1
        self.facing = -1
        self.home = self.center[0]        # the middle of its patrol: it walks PATROL_RANGE to each side
        self.chasing = False              # are you close enough that it's coming after you?
        self.fuse = None                  # an Ember Skull's countdown to BOOM
        self.aim = None                   # a Skeleton drawing its bow: time until its first arrow (None = hasn't seen you)
        self.reload = 0.0                 # a Skeleton's time until its next arrow
        self.flash = 0.0                  # flashes white when you hit it
        self.stunned = 0.0                # knocked back after a hit


class Platform:
    """A moving platform: a few ledge blocks in a row that slide back and forth on their own.
    Where it is only depends on the cave's clock, so it always goes the same way."""
    def __init__(self, r, c, w, axis, low, high):
        self.r, self.c, self.w = r, c, w      # where it's drawn in the cave file (its left end)
        self.axis = axis                      # "x" = side to side, "y" = up and down
        self.low, self.high = low, high       # how far it goes: columns for "x", rows for "y"

    def moves(self):
        """Does it go anywhere? (Too short a track, and it stays put.)"""
        return self.high > self.low

    def where(self, clock):
        """The top-left corner of the platform at this time: (x, y)."""
        start = self.c if self.axis == "x" else self.r
        span = self.high - self.low
        if span <= 0:
            return float(self.c), float(self.r)
        # It starts where it's drawn, going right (or down), and turns around at each end
        trip = (start - self.low + PLATFORM_SPEED * clock) % (2 * span)
        spot = self.low + (trip if trip <= span else 2 * span - trip)
        return (spot, float(self.r)) if self.axis == "x" else (float(self.c), spot)

    def cells(self):
        """Every block it passes through (the robot's map uses them as places to stand)."""
        if self.axis == "x":
            return [(self.r, c) for c in range(self.low, self.high + self.w)]
        return [(r, c) for r in range(self.low, self.high + 1) for c in range(self.c, self.c + self.w)]


def find_platforms(rows):
    """Turn the P's and U's in the drawing into moving platforms, and put air there instead.
    The letters you draw ARE the track: a platform rides along them and turns around at their ends,
    never past them (open space or rock past the end doesn't matter).
    - A row of P's: a platform PLATFORM_WIDTH wide slides from one end of the row to the other.
      Just 1 or 2 P's: there's no room to slide, so it stays put (a ledge you can't jump through).
    - A column of U's: a platform as wide as the column goes from its top row to its bottom row.
      Just one row of U's: it stays put."""
    platforms = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            letter = row[c]
            if letter not in PLATFORMS:
                c += 1
                continue
            w = 1
            while c + w < len(row) and row[c + w] == letter:
                w += 1
            if letter == "P":
                size = min(w, PLATFORM_WIDTH)
                platforms.append(Platform(r, c, size, "x", c, c + w - size))
                for i in range(w):
                    row[c + i] = "."
            else:
                tall = 1                  # how far the column of U's goes down
                while r + tall < len(rows) and all(rows[r + tall][cc] == "U" for cc in range(c, c + w)):
                    tall += 1
                platforms.append(Platform(r, c, w, "y", r, r + tall - 1))
                for rr in range(r, r + tall):
                    for cc in range(c, c + w):
                        rows[rr][cc] = "."
            c += w
    return platforms


class Swing:
    """A swinging vine: it hangs from the rock above the top R, and is as long as the column of R's.
    angle: 0 = hanging straight down, + = swung out to the right. spin: how fast the angle changes."""
    def __init__(self, r, c, length):
        self.r, self.c, self.length = r, c, length
        self.x, self.y = c + 0.5, float(r)        # where it's tied on: the middle of the top R's top edge
        self.angle = 0.0
        self.spin = 0.0
        self.held = False

    def point(self, along, angle=None):
        """The spot this far down the vine (in blocks): (x, y)."""
        angle = self.angle if angle is None else angle
        return self.x + along * math.sin(angle), self.y + along * math.cos(angle)

    def settle(self, dt):
        """Nobody on it: it swings back and forth by itself, slower and slower, until it hangs still."""
        self.spin += -SWING_GRAVITY / self.length * math.sin(self.angle) * dt
        self.spin *= max(0.0, 1 - SWING_SETTLE * dt)
        self.angle += self.spin * dt
        if abs(self.angle) < 0.01 and abs(self.spin) < 0.05:
            self.angle = self.spin = 0.0

    def reach(self):
        """Every block the vine can swing through (the robot's map counts them as places to hold on)."""
        spots = set()
        steps = 24
        for i in range(-steps, steps + 1):
            angle = SWING_MAX * 1.15 * i / steps
            along = 1.0
            while along <= self.length + 0.01:
                x, y = self.point(along, angle)
                spots.add((math.floor(y), math.floor(x)))
                along += 0.25
        return spots


def find_swings(rows):
    """Turn every column of R's in the drawing into a swinging vine, and put air there instead."""
    swings = []
    for r, row in enumerate(rows):
        for c, letter in enumerate(row):
            if letter != SWINGING_VINE or (r > 0 and rows[r - 1][c] == SWINGING_VINE):
                continue
            length = 1
            while r + length < len(rows) and rows[r + length][c] == SWINGING_VINE:
                length += 1
            swings.append(Swing(r, c, length))
    for swing in swings:
        for rr in range(swing.r, swing.r + swing.length):
            rows[rr][swing.c] = "."
    return swings


# ===========================================================================
# The cave
# ===========================================================================

class Cave:
    is_castle = False                     # castle.py makes a special cave: the Shadow King's castle
    is_throne_room = False                # and throne.py makes the room where you fight the Shadow King

    def __init__(self, game, mine_pos, level_text, changes=None):
        self.game = game
        self.mine_pos = mine_pos          # which Mine on the world map you came from
        self.map = parse_level(level_text)
        self.platforms = find_platforms(self.map)     # moving platforms (their P and U become air)
        self.swings = find_swings(self.map)           # swinging vines (their R's become air)
        self.theme = level_theme(level_text)
        self.rows = len(self.map)
        self.cols = len(self.map[0])
        # In a cave where the lava rises: taking this treasure wakes the lava (found before last time's changes)
        self.lava_treasure = self.treasure_by_the_exit() if level_setting(level_text, "lava rises") == "yes" else None
        # Things you changed last time (dug rock, opened chests, beaten monsters) stay changed
        self.changes = changes if changes is not None else {}
        for (r, c), letter in self.changes.items():
            self.map[r][c] = letter

        r, c = self.find("S")
        self.you = Explorer(self, c + (1 - PLAYER_W) / 2, r + 1 - PLAYER_H)
        self.monsters = []
        for r, row in enumerate(self.map):
            for c, letter in enumerate(row):
                if letter in CAVE_MONSTERS:
                    row[c] = "."
                    self.add_monster(CAVE_MONSTERS[letter], r, c, spawn=(r, c))
        self.arrows = []                  # Skeleton arrows flying through the air
        self.crumbling = {}               # crumbly ledges about to fall: (r, c) -> time left
        self.fallen = {}                  # crumbly ledges that fell: (r, c) -> time until they're back
        self.dirty = set()                # tiles that changed, so game.py can repaint them
        self.clock = 0.0                  # seconds since you came in: spike traps go up and down with it
        self.traps = [(r, c) for r, row in enumerate(self.map) for c, letter in enumerate(row) if letter == "A"]
        self.jets = [(r, c) for r, row in enumerate(self.map) for c, letter in enumerate(row) if letter == JET]
        self.geysers = [(r, c) for r, row in enumerate(self.map) for c, letter in enumerate(row) if letter == GEYSER]
        self.got_diamond = False
        self.got_shard = False            # a Sun Shard dug out of a shadow cave
        self.result = None                # becomes "exit" or "left"
        self.tips_shown = set()
        # Healing springs: seconds until each one is full again (0 = ready to drink)
        self.fountains = {(r, c): 0.0 for r, row in enumerate(self.map)
                          for c, letter in enumerate(row) if letter == "u"}
        self.told_fountain = False
        # Rising lava: only in caves whose drawing says "lava rises: yes"
        self.lava_rises = level_setting(level_text, "lava rises") == "yes"
        self.lava_line = None             # how high the rising lava is (None = it isn't rising)
        self.lava_wait = 0.0              # how long until it starts rising
        self.lava_restart = None          # where you start the climb again if it catches you

    # ----- map helpers --------------------------------------------------------

    def find(self, letter):
        for r, row in enumerate(self.map):
            for c, tile in enumerate(row):
                if tile == letter:
                    return (r, c)
        raise ValueError("Every cave needs an '%s'" % letter)

    def tile(self, r, c):
        if c < 0:
            return "."                    # past the left edge is the way out
        if r < 0 or c >= self.cols:
            return "#"                    # the ceiling and the far wall
        if r >= self.rows:
            return "."                    # below the bottom is a deep hole
        return self.map[r][c]

    def is_solid(self, r, c):
        return self.tile(r, c) in SOLIDS

    def change(self, r, c, letter, forever=True):
        self.map[r][c] = letter
        self.dirty.add((r, c))
        if forever:
            self.changes[(r, c)] = letter

    @property
    def center(self):
        return self.you.center

    def traps_up(self):
        """Are the spike traps up right now? They all go up and down together."""
        return self.clock % (TRAP_DOWN + TRAP_UP) >= TRAP_DOWN

    def about_to_go_off(self):
        """Flame jets and geysers fizzle just before they go off, so you can see it coming."""
        return not self.traps_up() and self.clock % (TRAP_DOWN + TRAP_UP) >= TRAP_DOWN - WARNING_TIME

    def hurts(self, tile):
        """How much a tile hurts if you touch it (spike traps and flame jets only hurt while they're on)."""
        if tile in "AJ" and not self.traps_up():
            return 0
        return HAZARDS.get(tile, 0)

    def flame(self, r, c):
        """The fire shooting up out of a flame jet: (x, y, w, h), up to JET_TALL blocks, stopped by rock."""
        top = r
        while top > r - JET_TALL + 1 and not self.is_solid(top - 1, c):
            top -= 1
        return (c + 0.2, top + 0.1, 0.6, r + 1 - top - 0.1)

    def platform_spot(self, i):
        """Where moving platform number i is right now: (x, y) of its top-left corner."""
        return self.platforms[i].where(self.clock)

    def add_monster(self, kind, r, c, spawn=None):
        monster = CaveMonster(self, self.game.new_monster(kind, shadow=self.is_castle), c, r, spawn)
        self.monsters.append(monster)
        return monster

    # ----- every frame ----------------------------------------------------------

    def update(self, dt, controls):
        """controls: left, right, down, jump (held down), jump_pressed and use_pressed (just pressed)"""
        if controls.get("jump_pressed"):
            self.you.buffer = JUMP_BUFFER
        if controls.get("use_pressed") and self.you.dizzy <= 0:
            self.use(controls.get("down"))
        if controls.get("shoot_pressed") and self.you.dizzy <= 0:
            self.shoot_arrow()
        for spot in self.fountains:                  # the healing springs slowly fill up again
            self.fountains[spot] = max(0.0, self.fountains[spot] - dt)
        dt = min(dt, 0.05)
        steps = max(1, math.ceil(dt * 120))      # small steps, so nothing skips through a wall
        for _ in range(steps):
            self.step(dt / steps, controls)
            if self.result or not self.game.player.is_alive:
                return

    def step(self, dt, controls):
        were_up = self.traps_up()
        riding = self.you.riding if self.you.on_ground else None
        before = self.platform_spot(riding) if riding is not None else None
        self.clock += dt
        if self.traps_up() and not were_up:
            if any(abs(c - self.you.x) < 9 for r, c in self.traps):
                self.game.sound("trap")              # SHING! the spike traps pop up
            if any(abs(c - self.you.x) < 9 for r, c in self.jets):
                self.game.sound("whoosh")            # FWOOSH! the flame jets fire
        if riding is not None:
            self.ride(riding, before)
        for swing in self.swings:
            if not swing.held:
                swing.settle(dt)
        self.move_you(dt, controls)
        if self.result or not self.game.player.is_alive:
            return
        for monster in list(self.monsters):
            self.move_monster(monster, dt)
        self.move_arrows(dt)
        self.update_ledges(dt)
        if self.lava_line is not None:
            self.raise_lava(dt)

    def ride(self, i, before):
        """You're standing on a moving platform: it carries you along."""
        you = self.you
        x, y = self.platform_spot(i)
        you.move_x(x - before[0])                 # a wall in the way? Then the platform slides out from under you
        if y < before[1]:
            you.move_y(y - before[1])             # up we go (bonk if the ceiling is in the way)
        else:
            you.y += y - before[1]                # down we go
        you.on_ground, you.riding = True, i

    # ----- you ------------------------------------------------------------------

    def run_speed(self):
        """How fast you run. Every Speedy power (from leveling up) makes you faster."""
        return RUN_SPEED + SPEEDY_RUN * self.game.player.power("Speedy")

    def jump_speed(self):
        """How hard you jump. Every Springy power (from leveling up) makes you jump higher."""
        return JUMP_SPEED + SPRINGY_JUMP * self.game.player.power("Springy")

    def move_you(self, dt, controls):
        you = self.you
        you.safe_time = max(0.0, you.safe_time - dt)
        you.swing = max(0.0, you.swing - dt)
        you.reload = max(0.0, you.reload - dt)
        for timer in ("ladder_wait", "hang_wait", "wall_time", "wall_push", "swing_wait"):
            setattr(you, timer, max(0.0, getattr(you, timer) - dt))
        if you.dizzy > 0:
            you.dizzy = max(0.0, you.dizzy - dt)
            controls = {}                         # too dizzy to move!
        left, right = bool(controls.get("left")), bool(controls.get("right"))
        up, down = bool(controls.get("up")), bool(controls.get("down"))
        down_pressed = down and not you.down_was_held
        you.down_was_held = down
        # SPACE jumps you off a ladder or a ledge (UP just climbs)
        space = controls.get("space_pressed", controls.get("jump_pressed") and not up)

        # On a swinging vine? Swing!
        if you.swinging is not None:
            self.swing_on(dt, left, right, down, space)
            self.give_tips(0)
            self.check_where_you_are()
            return

        # On a ladder, or hanging from a ledge? Then you move differently
        if not you.climbing and not you.hanging and self.can_grab_ladder(up, down):
            self.grab_ladder()
        if not you.climbing and not you.hanging and not you.on_wall:
            side = self.wall_to_grab(up)
            if side:
                self.grab_wall(side)
        if you.on_wall:
            self.climb_wall(dt, left, right, up, down, space)
            self.check_where_you_are()
            return
        if you.climbing:
            self.climb(dt, left, right, up, down, space)
            self.check_where_you_are()
            return
        if you.hanging:
            self.hang(dt, left, right, up, down, space)
            self.check_where_you_are()
            return

        # Crawl (hold DOWN on the ground), or ground pound (press DOWN in the air)
        self.crawl_or_stand(down)
        if down_pressed and not you.on_ground and not you.crawling and not you.pounding:
            you.pounding = True
            you.vx, you.vy = 0.0, POUND_SPEED
            self.game.sound("stomp")

        # Running
        want = (int(right) - int(left)) * (CRAWL_SPEED if you.crawling else self.run_speed())
        if want:
            you.facing = sign(want)
        if you.pounding:
            want = 0.0
        flying = you.flung and not you.on_ground and (not want or (sign(want) == sign(you.vx) and abs(you.vx) > abs(want)))
        if you.wall_push <= 0 and not flying:     # just after a wall jump (or off a vine) you fly on
            accel = RUN_ACCEL if you.on_ground else AIR_ACCEL
            if you.on_ground and self.on_ice():
                accel = ICE_GRIP                  # whee! slippery ice: it's hard to speed up, and hard to stop
            you.vx = approach(you.vx, want, accel * dt)

        # Holding toward a climbing wall while you fall? You slide down it slowly
        side = sign(want) if want else 0
        sliding = side and not you.on_ground and you.vy > 0 and not you.pounding and self.touching_wall(side, CLIMB_WALL)
        if sliding:
            you.wall_side, you.wall_time = side, 0.12

        # Jumping - from the ground, or off a climbing wall
        you.coyote = COYOTE_TIME if you.on_ground else max(0.0, you.coyote - dt)
        you.buffer = max(0.0, you.buffer - dt)
        if you.buffer > 0 and you.coyote > 0 and not you.pounding:
            if not you.crawling or self.room_to_stand():      # no jumping in a low tunnel!
                self.stand_up()
                you.vy = -self.jump_speed()
                you.buffer = you.coyote = 0.0
                you.on_ground = False
                self.game.sound("jump")
        elif you.buffer > 0 and you.wall_time > 0 and not you.on_ground:
            you.vy = -self.jump_speed()           # WALL JUMP!
            you.vx = -you.wall_side * WALL_JUMP_PUSH
            you.facing = -you.wall_side
            you.wall_push, you.wall_time, you.buffer = WALL_JUMP_TIME, 0.0, 0.0
            self.game.sound("jump")

        # Falling - let go of jump early for a little hop (but a mushroom bounce always goes all the way up)
        if you.vy >= 0:
            you.bounced = False
        short_hop = you.vy < 0 and not controls.get("jump") and not you.bounced
        if not you.pounding:                      # a ground pound falls at its own speed
            you.fall(dt, GRAVITY * (SHORT_HOP if short_hop else 1))
        if sliding:
            you.vy = min(you.vy, WALL_SLIDE)
        you.move_x(you.vx * dt)
        landed = you.move_y(you.vy * dt)
        if you.on_ground:
            you.flung = False
        if you.pounding and you.on_ground:
            self.pound_lands()
        elif landed > 6:
            self.game.sound("land")

        # Only just missed a ledge? Catch its edge!
        if side and not you.on_ground and you.vy > -2 and not you.pounding and not you.crawling and you.hang_wait <= 0:
            self.catch_ledge(side)

        if you.on_ground and any(self.tile(*spot) == "o" for spot in you.standing_on):
            you.vy = -BOUNCE_SPEED                    # BOING! a bouncy mushroom
            you.on_ground = False
            you.bounced = True
            self.game.sound("boing")
            self.game.effect("bounce", cave_xy=(you.center[0], you.y + you.h))
        elif you.on_ground and self.traps_up() and any(self.tile(*spot) == GEYSER for spot in you.standing_on):
            you.vy = -GEYSER_SPEED                    # WHOOSH! a steam geyser
            you.on_ground = False
            you.bounced = True
            self.game.sound("steam")
            self.game.effect("bounce", cave_xy=(you.center[0], you.y + you.h))

        if you.on_ground:
            middle = math.floor(you.x + you.w / 2)
            under = math.floor(you.y + you.h + EPS)
            if ((self.tile(under, middle) in SOLIDS + "=" or self.ladder_top(under, middle))
                    and self.tile(under - 1, middle) not in HAZARDS):
                # remember the middle of this block, away from the edge (and not on a spike trap)
                you.safe = (middle + (1 - you.w) / 2, you.y + you.h - PLAYER_H)
            for spot in you.standing_on:
                if self.tile(*spot) == "-" and spot not in self.crumbling:
                    self.crumbling[spot] = CRUMBLE_TIME
        if not you.on_ground and not you.pounding and not you.crawling and you.swing_wait <= 0:
            vine = self.vine_to_grab()            # jumped (or fell) into a swinging vine? Grab it!
            if vine is not None:
                self.grab_swing(vine)
        self.give_tips(side)
        self.check_where_you_are()

    def on_ice(self):
        """Are you standing on slippery ice?"""
        return any(self.tile(*spot) == ICE for spot in self.you.standing_on)

    def give_tips(self, side):
        """The first time you find a ladder, a vine, ice, a climbing wall or a low tunnel, say how to use it."""
        you = self.you
        middle = math.floor(you.x + you.w / 2)
        for r in you.rows():
            if self.tile(r, middle) == "H":
                self.tip("ladder")
            elif self.tile(r, middle) == "V":
                self.tip("vine")
        if you.on_ground and self.on_ice():
            self.tip("ice")
        if you.on_ground and you.riding is not None:
            self.tip("platform")
        if you.swinging is not None or any(abs(swing.x - x) < 4 and swing.y - 1 < y < swing.y + swing.length + 3
                                           for swing in self.swings for x, y in [you.center]):
            self.tip("swing")
        if any(self.tile(*spot) == GEYSER for spot in you.standing_on):
            self.tip("geyser")
        x, y = you.center
        if any(abs(c + 0.5 - x) < 4 and abs(r + 0.5 - y) < 3 for r, c in self.jets):
            self.tip("jet")
        near = [self.tile(r, c) for r in you.rows() for c in range(math.floor(x) - 1, math.floor(x) + 2)]
        if LEVER in near:
            self.tip("lever")
        if GATE in near:
            self.tip("gate")
        if side and self.touching_wall(side, CLIMB_WALL):
            self.tip("wall")
        if side and you.on_ground and not you.crawling and self.touching_wall(side):
            front = math.floor(you.x + you.w + 0.05) if side > 0 else math.floor(you.x - 0.05)
            feet = math.floor(you.y + you.h - EPS)
            if not self.is_solid(feet, front) and self.is_solid(feet - 1, front):
                self.tip("tunnel")

    def tip(self, name):
        seen = getattr(self.game, "tips_seen", self.tips_shown)   # once a game (or once a cave)
        if name not in seen:
            seen.add(name)
            self.game.log(TIPS[name], "quest")

    # ----- ladders ----------------------------------------------------------------

    def ladder_top(self, r, c):
        """The top rung of a ladder (or the top of a vine) works like a ledge: you can stand on it."""
        return self.tile(r, c) in LADDERS and self.tile(r - 1, c) not in LADDERS

    def can_grab_ladder(self, up, down):
        """UP grabs a ladder (or vine) you're touching. DOWN grabs it too, or climbs down from its top."""
        you = self.you
        if you.ladder_wait > 0 or you.pounding or not (up or down):
            return False
        c = math.floor(you.x + you.w / 2)
        touching = any(self.tile(r, c) in LADDERS for r in you.rows())
        on_top = you.on_ground and self.tile(math.floor(you.y + you.h + EPS), c) in LADDERS
        if up:
            return touching
        return on_top or (touching and not you.on_ground)

    def grab_ladder(self):
        you = self.you
        if you.crawling and not self.room_to_stand():
            return
        self.stand_up()
        c = math.floor(you.x + you.w / 2)
        you.climbing, you.ladder_col = True, c
        you.x = c + (1 - you.w) / 2               # hands on the middle of the ladder
        you.vx = you.vy = 0.0
        you.buffer = 0.0                          # pressing UP to grab a ladder isn't a jump
        you.on_ground = False

    def climb(self, dt, left, right, up, down, space):
        you = self.you
        if space:                                 # leap off the ladder
            you.climbing = False
            you.ladder_wait = 0.3
            you.vy = -self.jump_speed() * 0.85
            you.vx = (int(right) - int(left)) * self.run_speed()
            if you.vx:
                you.facing = sign(you.vx)
            self.game.sound("jump")
            return
        if left != right:
            you.facing = 1 if right else -1       # look around while you hang on
        you.vx = 0.0
        you.vy = (int(down) - int(up)) * CLIMB_SPEED
        going_up = you.vy < 0
        you.move_y(you.vy * dt)
        if you.on_ground:                         # climbed all the way down to the floor
            you.climbing = False
            return
        c = you.ladder_col
        if not any(self.tile(r, c) in LADDERS for r in you.rows()):
            you.climbing = False                  # off the end of the ladder
            top = math.ceil(you.y + you.h - EPS)
            if going_up and self.tile(top, c) in LADDERS:
                you.y = top - you.h               # climbed off the top: stand on the top rung
                you.vy = 0.0
                you.on_ground = True

    # ----- swinging vines -----------------------------------------------------------

    def hands(self):
        you = self.you
        return you.x + you.w / 2, you.y + SWING_HANDS

    def fits(self, x, y):
        """Would your body fit here, with no rock in the way?"""
        you = self.you
        return not any(self.is_solid(r, c) for r in range(math.floor(y), math.floor(y + you.h - EPS) + 1)
                       for c in range(math.floor(x), math.floor(x + you.w - EPS) + 1))

    def vine_to_grab(self):
        """A swinging vine going through your body (its number), or None."""
        you = self.you
        for i, swing in enumerate(self.swings):
            along = 0.5
            while along <= swing.length + 0.01:
                x, y = swing.point(along)
                if you.x - 0.1 <= x <= you.x + you.w + 0.1 and you.y <= y <= you.y + you.h:
                    return i
                along += 0.25
        return None

    def grab_swing(self, i):
        """Grab vine number i where your hands are, and keep going the way you were going."""
        you, swing = self.you, self.swings[i]
        hx, hy = self.hands()
        grip = min(swing.length, max(1.0, math.hypot(hx - swing.x, hy - swing.y)))
        x, y = swing.point(grip)
        if not self.fits(x - you.w / 2, y - SWING_HANDS):
            return
        if not any(other.held for other in self.swings):
            tangent = you.vx * math.cos(swing.angle) - you.vy * math.sin(swing.angle)
            swing.spin = 0.6 * swing.spin + 0.4 * tangent / grip     # your run (or jump) gets it swinging
        swing.held = True
        you.swinging, you.grip = i, grip
        you.x, you.y = x - you.w / 2, y - SWING_HANDS
        you.climbing, you.hanging, you.on_wall, you.pounding, you.flung = False, 0, 0, False, False
        you.buffer = 0.0
        you.on_ground = False
        self.game.sound("land")

    def swing_on(self, dt, left, right, down, space):
        """Hanging on a swinging vine: LEFT and RIGHT pump it higher, SPACE lets go (DOWN just drops)."""
        you = self.you
        swing = self.swings[you.swinging]
        if space or down:
            self.let_go_of_vine(hop=space)
            return
        push = int(right) - int(left)
        if push:
            you.facing = push
        grip = you.grip
        accel = -SWING_GRAVITY / grip * math.sin(swing.angle)
        pumping = push and abs(swing.angle) < SWING_MAX and (sign(swing.spin) == push or abs(swing.spin) < 0.3)
        if pumping:
            accel += push * SWING_PUMP / grip     # leaning into the swing: higher and higher!
        spin = (swing.spin + accel * dt) * (1 - SWING_DRAG * dt)
        if pumping:                               # ...but never higher than SWING_MAX
            top = math.sqrt(max(0.0, 2 * SWING_GRAVITY / grip * (math.cos(swing.angle) - math.cos(SWING_MAX))))
            spin = max(-top, min(top, spin)) if abs(swing.spin) <= top else max(-abs(swing.spin), min(abs(swing.spin), spin))
        angle = swing.angle + spin * dt
        if abs(angle) > SWING_MAX:                # as high as it goes: it stops there, then swings back
            angle, spin = math.copysign(SWING_MAX, angle), 0.0
        x, y = swing.point(grip, angle)
        if self.fits(x - you.w / 2, y - SWING_HANDS):
            swing.angle, swing.spin = angle, spin
        else:
            swing.spin = -0.3 * spin              # bonk! you bumped into rock: bounce back a little
            x, y = swing.point(grip)
        you.x, you.y = x - you.w / 2, y - SWING_HANDS
        you.vx = grip * swing.spin * math.cos(swing.angle)     # how fast you're going (you keep it when you let go)
        you.vy = -grip * swing.spin * math.sin(swing.angle)
        you.on_ground = False

    def let_go_of_vine(self, hop=True):
        you = self.you
        if you.swinging is None:
            return
        self.swings[you.swinging].held = False
        you.swinging = None
        you.swing_wait = SWING_WAIT
        if hop:
            you.vy -= SWING_HOP
            you.bounced = True                    # fly all the way up, even after you let go of SPACE
            self.game.sound("jump")
        you.flung = True
        if you.vx:
            you.facing = sign(you.vx)

    # ----- climbing walls ----------------------------------------------------------

    def wall_to_grab(self, up):
        """UP next to a climbing wall grabs it. Returns which side it's on (0 = none)."""
        you = self.you
        if not up or you.ladder_wait > 0 or you.pounding:
            return 0
        for side in (you.facing, -you.facing):
            if self.touching_wall(side, CLIMB_WALL):
                return side
        return 0

    def grab_wall(self, side):
        you = self.you
        if you.crawling and not self.room_to_stand():
            return
        self.stand_up()
        c = math.floor(you.x + you.w + 0.05) if side > 0 else math.floor(you.x - 0.05)
        you.x = c - you.w if side > 0 else c + 1   # right up against the wall
        you.on_wall, you.facing = side, side
        you.vx = you.vy = 0.0
        you.buffer = 0.0                          # pressing UP to grab a wall isn't a jump
        you.on_ground = False

    def climb_wall(self, dt, left, right, up, down, space):
        you = self.you
        side = you.on_wall
        c = math.floor(you.x + you.w + 0.05) if side > 0 else math.floor(you.x - 0.05)
        if space:                                 # WALL JUMP: leap away from the wall
            you.on_wall, you.ladder_wait = 0, 0.25
            you.vy = -self.jump_speed()
            you.vx = -side * WALL_JUMP_PUSH
            you.facing = -side
            you.wall_push = WALL_JUMP_TIME
            self.game.sound("jump")
            return
        if (left if side > 0 else right) and not up:  # pushing away from the wall: let go
            you.on_wall, you.ladder_wait = 0, 0.25
            return
        you.vx = 0.0
        you.vy = (int(down) - int(up)) * WALL_CLIMB_SPEED
        above = self.tile(math.floor(you.y - 0.05), c)
        if you.vy < 0 and above in SOLIDS and above != CLIMB_WALL:
            you.vy = 0.0                          # plain rock above: you can't climb any higher
        going_up = you.vy < 0
        you.move_y(you.vy * dt)
        if you.on_ground:                         # climbed all the way down to the floor
            you.on_wall = 0
            return
        if not self.touching_wall(side, CLIMB_WALL):
            you.on_wall = 0                       # off the end of the wall
            top = math.ceil(you.y + you.h - EPS)
            if going_up and self.is_solid(top, c) and not self.is_solid(top - 1, c) and not self.is_solid(top - 2, c):
                you.x = c + (1 - you.w) / 2       # climbed to the top: pull yourself up onto it
                you.y = top - you.h
                you.vy = 0.0
                you.on_ground = True

    # ----- walls, ledges, ground pounds and crawling -------------------------------

    def touching_wall(self, side, kinds=SOLIDS):
        """Is there a wall (one of these kinds of tiles) right next to you on this side?"""
        you = self.you
        c = math.floor(you.x + you.w + 0.05) if side > 0 else math.floor(you.x - 0.05)
        return any(self.tile(r, c) in kinds for r in you.rows())

    def catch_ledge(self, side):
        """Grab the edge of a block whose top is right by your hands."""
        you = self.you
        c = math.floor(you.x + you.w + 0.05) if side > 0 else math.floor(you.x - 0.05)
        for r in (math.floor(you.y), math.floor(you.y) + 1):
            room_on_top = not self.is_solid(r - 1, c) and not self.is_solid(r - 2, c) and self.tile(r - 1, c) not in HAZARDS
            if (self.is_solid(r, c) and self.tile(r, c) != "o" and room_on_top and abs(r - you.y) <= LEDGE_REACH):
                you.hanging, you.ledge = side, (r, c)
                you.vx = you.vy = 0.0
                you.y = r - 0.15                  # hands on the edge
                you.hang_time = 0.0
                you.facing = side
                return True
        return False

    def hang(self, dt, left, right, up, down, space):
        you = self.you
        r, c = you.ledge
        you.vx = you.vy = 0.0
        you.hang_time += dt
        toward = right if you.hanging > 0 else left
        away = left if you.hanging > 0 else right
        if down or away or not self.is_solid(r, c):   # let go (or someone dug the ledge away)
            you.hanging, you.hang_wait = 0, 0.3
            return
        if up or space or (toward and you.hang_time >= HANG_TIME):
            you.hanging = 0                       # pull yourself up onto the ledge
            you.x = c + (1 - you.w) / 2
            you.y = r - you.h
            you.on_ground = True
            you.buffer = 0.0
            self.game.sound("land")

    def pound_lands(self):
        """SLAM! A ground pound breaks cracked rock under you (no pickaxe needed)."""
        you, game = self.you, self.game
        cracked = [spot for spot in you.standing_on if self.tile(*spot) == "B"]
        game.effect("pound", cave_xy=(you.center[0], you.y + you.h))
        if cracked:
            for r, c in cracked:
                self.change(r, c, ".")
                game.effect("rubble", cave_xy=(c + 0.5, r + 0.5), ore=False)
            game.sound("dig")
            you.on_ground = False
            you.vy = POUND_SPEED * 0.5            # keep smashing down through the hole
        else:
            you.pounding = False
            game.sound("land")

    def crawl_or_stand(self, down):
        you = self.you
        if down and you.on_ground and not you.crawling:
            you.y += you.h - CRAWL_H              # duck down, keeping your feet on the floor
            you.h, you.crawling = CRAWL_H, True
        elif you.crawling and not (down and you.on_ground) and self.room_to_stand():
            self.stand_up()

    def stand_up(self):
        you = self.you
        if you.crawling:
            you.y -= PLAYER_H - you.h
            you.h, you.crawling = PLAYER_H, False

    def room_to_stand(self):
        """Is there room above you to stand up? (Not in a low tunnel!)"""
        you = self.you
        feet = you.y + you.h
        rows = range(math.floor(feet - PLAYER_H), math.floor(feet - EPS) + 1)
        return not any(self.is_solid(r, c) for r in rows for c in you.cols())

    def let_go(self):
        """Stop climbing, hanging, pounding and crawling (when you get knocked about)."""
        you = self.you
        you.climbing, you.hanging, you.pounding, you.wall_push, you.on_wall = False, 0, False, 0.0, 0
        if you.swinging is not None:
            self.let_go_of_vine(hop=False)
        you.flung = False
        if you.crawling and self.room_to_stand():
            self.stand_up()

    def check_where_you_are(self):
        you, game = self.you, self.game
        if you.y > self.rows + 1:
            game.log("You fell down a deep hole!", "bad")
            self.put_you_back(FALL_DAMAGE)
            return
        if you.x + you.w / 2 < 0:
            self.result = "left"                 # walked back out the entrance
            return
        if self.traps_up():                      # the fire shooting up out of a flame jet
            for r, c in self.jets:
                if abs(c - you.x) < 2 and you.touches(*self.flame(r, c)):
                    game.log(OUCH[JET], "bad")
                    self.put_you_back(self.hurts(JET))
                    return
        for r in you.rows():
            for c in you.cols():
                tile = self.tile(r, c)
                top = self.hazard_top(r, c)
                if self.hurts(tile) and you.touches(c, r + top, 1, 1 - top):
                    game.log(OUCH.get(tile, "Ouch!"), "bad")
                    self.put_you_back(self.hurts(tile))
                    return
                if tile == "E":
                    self.result = "exit"
                    return
                if tile == "u":
                    self.drink(r, c)
                if tile == SECRET:
                    self.find_secret(r, c)
                if tile == "$":
                    self.change(r, c, ".")             # a gem! it stays collected
                    game.effect("sparkle", cave_xy=(c + 0.5, r + 0.5))
                    game.effect("popup", cave_xy=(c + 0.5, r), text="+%d XP" % GEM_XP, kind="loot")
                    game.sound("gem")
                    game.gain_xp(GEM_XP, quiet=True)

    def put_you_back(self, damage):
        you = self.you
        self.let_go()
        self.stand_up()
        you.x, you.y = you.safe
        if not self.room_to_stand():              # the safe spot is in a low tunnel: crawl there
            you.y += PLAYER_H - CRAWL_H
            you.h, you.crawling = CRAWL_H, True
        you.vx = you.vy = 0.0
        you.dizzy = DIZZY_TIME
        if damage > 0:
            self.hurt_you(damage, None)

    def hurt_you(self, damage, from_x):
        """from_x: where the hit came from, to knock you the other way (None = no knockback)."""
        you = self.you
        if you.safe_time > 0:
            return
        self.game.hurt_player(damage)
        if self.you is not you:
            return                               # knocked out: you're starting again at the entrance
        you.safe_time = SAFE_TIME
        if from_x is not None:
            self.let_go()                        # a big hit knocks you off ladders and ledges
            you.vx = KNOCKBACK * sign(you.center[0] - from_x)
            you.vy = -6.0
            you.dizzy = max(you.dizzy, 0.25)

    def back_to_start(self):
        """Start again at the entrance (in the castle, when you get knocked out)."""
        r, c = self.find("S")
        self.you = Explorer(self, c + (1 - PLAYER_W) / 2, r + 1 - PLAYER_H)
        self.you.dizzy = DIZZY_TIME
        self.you.safe_time = SAFE_TIME * 2       # a moment to get ready

    # ----- pressing R: open, dig or swing ------------------------------------------

    def use(self, down=False):
        you, game, p = self.you, self.game, self.game.player
        if you.swing > 0:
            return
        front = math.floor(you.x + you.w + 0.3) if you.facing > 0 else math.floor(you.x - 0.3)

        # A lever right here? Pull it!
        lever = self.lever_in_reach()
        if lever:
            self.pull_lever(*lever)
            return

        # A treasure chest right here?
        for r in you.rows():
            for c in list(you.cols()) + [front]:
                if self.tile(r, c) == "T":
                    self.open_chest(r, c)
                    return

        # Something to dig? (hold DOWN to dig the floor under your feet)
        if down:
            under = math.floor(you.y + you.h + EPS)
            spots = [(under, c) for c in you.cols() if self.tile(under, c) in DIGGABLE]
        else:
            spots = [(r, front) for r in you.rows() if self.tile(r, front) in DIGGABLE]
        if spots:
            you.swing = SWING_TIME
            if not p.pickaxe:
                you.tool = "fist"
                game.log("You need a pickaxe to dig here. Craft one with C (it takes %d wood in a cave)." % getattr(game, "pickaxe_cave_wood", 2))
                game.sound("miss")
                return
            you.tool = "pickaxe"
            for r, c in spots:
                self.dig(r, c)            # the pickaxe never wears out
            return

        # Otherwise, swing your sword
        you.swing = SWING_TIME
        you.tool = "sunfang" if p.sunfang else "sword" if p.swords else "fist"
        # The sword hits in front of you, and any monster right on top of you too
        reach_x = you.x if you.facing > 0 else you.x - SWORD_REACH
        hits = [m for m in self.monsters if m.touches(reach_x, you.y - 0.1, you.w + SWORD_REACH, you.h + 0.2)]
        if not hits:
            game.sound("miss")
            return
        bonus = game.ring_power()                # a diamond ring on your sword hits harder
        for monster in hits:
            if p.sunfang:                        # Sunfang hits hard, and never breaks
                damage = game.sunfang_damage(monster.info.special) + bonus
            elif p.swords:
                damage = game.rng.randint(2, 6) + p.damage_bonus + bonus
                if monster.info.special == "tough":
                    damage = max(1, damage - 1)
                if bonus:
                    game.effect("sparkle", cave_xy=monster.center)
            else:
                damage = 1                       # no sword - just a punch!
            self.hurt_monster(monster, damage, you.center[0])
        if p.swords and not p.sunfang and p.swords[0].use():
            p.swords.pop(0)
            game.log("Your sword broke! Swords left: %d" % len(p.swords), "bad")

    def shoot_arrow(self):
        """Press F: shoot an arrow the way you're facing."""
        you, game, p = self.you, self.game, self.game.player
        if you.reload > 0:
            return
        if not p.has_bow or p.arrows <= 0:
            game.log("You need a bow and arrows. Craft them out of wood (press C)."
                     if not p.has_bow else "You're out of arrows!")
            you.reload = SHOOT_TIME * 3
            return
        p.arrows -= 1
        you.reload = you.swing = SHOOT_TIME
        you.tool = "bow"
        x, y = you.center
        self.arrows.append({"x": x + 0.5 * you.facing, "y": y - 0.1, "vx": SHOOT_SPEED * you.facing, "yours": True,
                            "fire": p.fire_arrows})
        game.sound("shoot")

    def dig(self, r, c):
        game = self.game
        letter = self.tile(r, c)
        self.change(r, c, ".")
        game.effect("rubble", cave_xy=(c + 0.5, r + 0.5), ore=letter in "*s")
        game.sound("dig")
        if letter in "*s":
            if letter == "*":
                self.got_diamond = True
                game.found_diamond()
            else:
                self.got_shard = True
                game.found_sun_shard()
            game.effect("sparkle", cave_xy=(c + 0.5, r + 0.5))
            # The Mine is "empty" once all its ore is gone (a shadow cave has a diamond AND a Sun Shard)
            if not any(tile in "*s" for row in self.map for tile in row):
                game.cleared_mines.add(self.mine_pos)
        if (r, c) == self.lava_treasure and self.lava_line is None:
            self.start_rising_lava()

    # ----- secret walls, levers and gates -----------------------------------------------

    def find_secret(self, r, c):
        """You walked into a secret wall! It and all the secret wall touching it melt away, for good."""
        game = self.game
        todo, found = [(r, c)], []
        while todo:
            rr, cc = todo.pop()
            if self.tile(rr, cc) != SECRET or not (0 <= rr < self.rows and 0 <= cc < self.cols):
                continue
            self.change(rr, cc, ".")
            found.append((rr, cc))
            todo += [(rr + 1, cc), (rr - 1, cc), (rr, cc + 1), (rr, cc - 1)]
        game.log(TIPS["secret"], "quest")
        game.sound("secret")
        for rr, cc in found[:12]:
            game.effect("sparkle", cave_xy=(cc + 0.5, rr + 0.5))

    def lever_in_reach(self):
        """A lever you're standing at (or right in front of you): (r, c), or None."""
        you = self.you
        front = math.floor(you.x + you.w + 0.3) if you.facing > 0 else math.floor(you.x - 0.3)
        for r in you.rows():
            for c in list(you.cols()) + [front]:
                if self.tile(r, c) == LEVER:
                    return (r, c)
        return None

    def pull_lever(self, r, c):
        """CLUNK! Every iron gate in the cave opens (and in the castle, the locked door too)."""
        game = self.game
        self.change(r, c, PULLED_LEVER)
        self.you.swing, self.you.tool = SWING_TIME, None
        game.sound("clang")
        game.effect("popup", cave_xy=(c + 0.5, r), text="CLUNK!", kind="loot")
        gates = [(rr, cc) for rr, row in enumerate(self.map) for cc, letter in enumerate(row) if letter == GATE]
        for rr, cc in gates:
            self.change(rr, cc, OPEN_GATE)
        if gates:
            game.sound("door")
        self.lever_pulled(bool(gates))

    def lever_pulled(self, opened_gates):
        if opened_gates:
            self.game.log("CLUNK! You pull the lever... and the iron gates creak open!", "good")
        else:
            self.game.log("CLUNK! You pull the lever. Hmm, nothing happened.", "quest")

    def gates_open(self):
        """No closed iron gates left (the robot checks this)."""
        return not any(GATE in row for row in self.map)

    def hazard_top(self, r, c):
        """How far down block (r, c) its hazard starts. Lava stacked under more lava is a deep pool:
        it's lava all the way up, so it hurts from the very top of its block."""
        tile = self.tile(r, c)
        if tile == "~" and self.tile(r - 1, c) == "~":
            return 0.0
        return HAZARD_TOP.get(tile, 0.0)

    # ----- healing springs and rising lava --------------------------------------------

    SPRING = "spring"                            # the castle calls it a fountain

    def drink(self, r, c):
        """Walk into a healing spring (u) when you're hurt, and it heals you all the way."""
        game, p = self.game, self.game.player
        if self.fountains.get((r, c), 0) > 0:
            return                                   # still filling up
        if p.health >= p.max_health:
            if not self.told_fountain:
                self.told_fountain = True
                game.log("A healing %s! Come back and drink from it when you're hurt." % self.SPRING, "quest")
            return
        healed = p.heal(p.max_health)
        self.fountains[(r, c)] = FOUNTAIN_REFILL
        game.log("Glug, glug... the %s heals you! It will take a while to fill up again." % self.SPRING, "good")
        game.sound("heal")
        game.effect("popup", cave_xy=(c + 0.5, r), text="+%d" % healed, kind="good")
        game.effect("sparkle", cave_xy=(c + 0.5, r + 0.5))

    def treasure_by_the_exit(self):
        """The diamond ore (or the chest in its place) nearest the exit door: the cave's big treasure."""
        exits = [(r, c) for r, row in enumerate(self.map) for c, tile in enumerate(row) if tile == "E"]
        treasure = [(r, c) for r, row in enumerate(self.map) for c, tile in enumerate(row) if tile in "*T"]
        if not exits or not treasure:
            return None
        return min(treasure, key=lambda spot: min(abs(spot[0] - r) + abs(spot[1] - c) for r, c in exits))

    def start_rising_lava(self, warn=True):
        """The treasure woke up the lava! It waits a moment, then rises from the floor."""
        self.lava_line = self.rows - 1 + HAZARD_TOP["~"]     # the top of the lava, down in the floor
        self.lava_wait = LAVA_RISE_WAIT
        self.lava_stop = min([r for r, row in enumerate(self.map) if "E" in row] or [0]) + 1
        if self.lava_restart is None:
            self.lava_restart = self.you.safe                # if the lava catches you, you start again here
        if warn:
            self.game.log("RUMBLE... The lava is waking up! Climb to the exit, quick!", "bad")
            self.game.sound("boom")
            self.game.effect("shake", amount=2)

    def raise_lava(self, dt):
        """Every moment, the lava creeps a little higher. Don't let it catch you!"""
        if self.lava_wait > 0:
            self.lava_wait -= dt
            return
        self.lava_line = max(self.lava_stop, self.lava_line - LAVA_RISE_SPEED * dt)   # it stops just below the exit
        for m in list(self.monsters):                 # monsters caught in it are gone
            if m.y + m.h > self.lava_line + 0.3:
                self.monsters.remove(m)
                self.game.effect("poof", cave_xy=m.center)
        you = self.you
        if you.y + you.h > self.lava_line + 0.2 and you.safe_time <= 0:
            # Caught! The lava sinks back down, and you try the climb again from where you got the diamond.
            # It never knocks you out: you always get another try.
            self.game.log("Hot hot HOT! The lava sinks back down... try the climb again!", "bad")
            self.start_rising_lava(warn=False)
            you.safe = self.lava_restart
            self.put_you_back(min(LAVA_DAMAGE, self.game.player.health - 1))

    def open_chest(self, r, c):
        game = self.game
        self.change(r, c, "t")
        if (r, c) == self.lava_treasure and self.lava_line is None:
            self.start_rising_lava()
        self.you.swing = SWING_TIME
        self.you.tool = None
        game.sound("chest")
        game.effect("sparkle", cave_xy=(c + 0.5, r + 0.5))
        total = sum(weight for _, weight in CHEST_LOOT)
        roll = game.rng.uniform(0, total)
        for kind, weight in CHEST_LOOT:
            roll -= weight
            if roll <= 0:
                break
        if kind == "trap":
            game.log("It's a trap! A Spider jumps out of the chest!", "bad")
            game.sound("alert")
            spider = self.add_monster("Spider", r, c)
            spider.vy = -9.0
            self.you.safe_time = max(self.you.safe_time, 0.8)   # a moment to get ready
        else:
            text = game.give_loot(kind, CHEST_XP)
            game.effect("popup", cave_xy=(c + 0.5, r), text=text, kind="loot")
        ring_chance = LUCKY_RING_CHANCE if game.player.power("Lucky") else RING_CHANCE
        if game.rng.random() < ring_chance:            # a diamond ring, too!
            game.effect("popup", cave_xy=(c + 0.5, r - 0.6), text=game.give_ring(), kind="loot")
            game.effect("sparkle", cave_xy=(c + 0.5, r))

    # ----- monsters -----------------------------------------------------------------

    def danger_ahead(self, body, direction):
        """Is there a hole or a hazard right in front of this body?"""
        look = 0.1 + body.vx ** 2 / 50              # fast monsters need to look farther ahead to stop in time
        front = math.floor(body.x + body.w + look) if direction > 0 else math.floor(body.x - look)
        feet = math.floor(body.y + body.h - EPS)
        ahead, below = self.tile(feet, front), self.tile(feet + 1, front)
        return (ahead in HAZARDS or below in HAZARDS
                or (below not in SOLIDS + LEDGES and not self.ladder_top(feet + 1, front)))

    def move_monster(self, m, dt):
        you, game = self.you, self.game
        m.flash = max(0.0, m.flash - dt)
        m.stunned = max(0.0, m.stunned - dt)
        m.reload = max(0.0, m.reload - dt)
        dx = you.center[0] - m.center[0]
        dy = you.center[1] - m.center[1]
        level = abs((you.y + you.h) - (m.y + m.h)) < SAME_LEVEL    # standing on the same floor as it?
        sees = level and abs(dx) < SIGHT and self.can_see(m, you)
        m.chasing = sees and abs(dx) <= CHASE_RANGE
        special = m.info.special
        want = 0.0

        if m.stunned > 0:
            pass                                  # still flying back from your hit
        elif special == "archer" and sees:
            m.facing = m.direction = sign(dx)     # it stops and turns to you...
            if m.aim is None:
                m.aim = SKELETON_AIM              # ...and starts drawing its bow (game.py draws it, with a "!")
            m.aim = max(0.0, m.aim - dt)
            if m.aim <= 0 and m.reload <= 0 and abs(dy) < 1.5:
                self.shoot(m)
        elif special == "explodes" and m.fuse is not None:
            m.fuse -= dt
            if math.hypot(dx, dy) > BLAST_RADIUS + 1.5:
                m.fuse = None                     # you got away - it calms down
            elif m.fuse <= 0:
                self.explode(m)
                return
        else:
            if special == "archer":
                m.aim = None                      # it lost you: next time it has to draw its bow again
            want = self.monster_walk(m, dx)
            if special == "explodes" and m.chasing and math.hypot(dx, dy) < 1.5:
                m.fuse = FUSE_TIME                # it starts to hiss...
                game.sound("fuse")
                want = 0.0
            if m.kind in HOPPERS and m.chasing and m.on_ground and game.rng.random() < 1.5 * dt:
                m.vy = -11.0
            m.facing = m.direction

        m.vx = approach(m.vx, want, (10 if m.stunned > 0 else 25) * dt)
        m.fall(dt)
        if m.move_x(m.vx * dt) and want and m.on_ground:
            if m.chasing:
                m.vy = -10.0                      # hop up after you
            else:
                m.direction *= -1
        m.move_y(m.vy * dt)

        # Fell in a hole or into something nasty?
        if m.y > self.rows + 1:
            self.monsters.remove(m)
            return
        for r in m.rows():
            for c in m.cols():
                tile = self.tile(r, c)
                top = self.hazard_top(r, c)
                if self.hurts(tile) and m.touches(c, r + top, 1, 1 - top):
                    game.log("The %s fell in the %s!" % (m.name, HAZARD_NAMES.get(tile, "trap")), "good")
                    self.defeat(m, give_xp=True)
                    return

        # Standing inside you (you walked into it, or it landed on you)? It slides back out, so you can hit it
        if m.touches_body(you) and not (you.vy > 0 and you.y + you.h <= m.y + 0.5):
            overlap = (m.w + you.w) / 2 - abs(m.center[0] - you.center[0])
            if overlap > TOUCH_DEPTH:
                away = sign(m.center[0] - you.center[0]) if m.center[0] != you.center[0] else you.facing
                m.move_x(away * min(overlap - TOUCH_DEPTH, PUSH_APART * dt))

        # Bumping into you
        if m.touches_body(you) and game.player.is_alive:
            if you.vy > 0 and you.y + you.h <= m.y + 0.5:
                game.sound("stomp")
                pound = you.pounding                 # a ground pound hits much harder than a jump
                you.vy, you.pounding = -STOMP_BOUNCE, False
                damage = (POUND_DAMAGE if pound else STOMP_DAMAGE) - (1 if special == "tough" else 0)
                self.hurt_monster(m, damage, you.center[0])
                if pound and m in self.monsters:
                    m.stunned = POUND_STUN
            elif special == "explodes":
                if m.fuse is None:
                    m.fuse = FUSE_TIME
                    game.sound("fuse")
            else:
                self.hurt_you(game.rng.randint(*m.info.damage), m.center[0])

    def monster_walk(self, m, dx):
        """How fast a monster wants to walk: after you if you're close, otherwise back and forth by its spot."""
        if m.chasing:
            if abs(dx) > 0.3:
                m.direction = sign(dx)
            if abs(dx) < (m.w + self.you.w) / 2 - TOUCH_DEPTH:
                return 0.0                        # touching you: it stops there, it doesn't walk right into you
            if m.on_ground and self.danger_ahead(m, m.direction):
                return 0.0                        # it won't jump in a hole or lava for you: it waits at the edge
            return m.direction * m.speed
        away = m.center[0] - m.home
        if abs(away) > PATROL_RANGE + 0.1:        # wandered off (it chased you): walk back home
            m.direction = -sign(away)
        elif away * m.direction >= PATROL_RANGE:  # the end of its patrol: turn around
            m.direction *= -1
        if m.on_ground and self.danger_ahead(m, m.direction):
            if abs(away) > PATROL_RANGE + 0.1:
                m.home = m.center[0]              # it can't get home from here, so it guards this spot now
            m.direction *= -1                     # turn around at the edge
            return 0.0
        return m.direction * m.speed

    def can_see(self, m, you):
        """No rock in the way between the monster and you (looking along the monster's row)."""
        r = math.floor(m.center[1])
        start, end = sorted((math.floor(m.center[0]), math.floor(you.center[0])))
        return not any(self.is_solid(r, c) for c in range(start, end + 1))

    def hurt_monster(self, m, damage, from_x):
        game = self.game
        m.info.health = max(0, m.info.health - damage)
        m.flash = 0.25
        m.stunned = max(m.stunned, 0.3)
        m.vx = 5.0 * sign(m.center[0] - from_x)
        m.vy = -4.0
        game.effect("popup", cave_xy=(m.center[0], m.y), text="-%d" % damage, kind="bad")
        game.sound("hit")
        if not m.info.is_alive:
            self.defeat(m, give_xp=True)

    def defeat(self, m, give_xp):
        if m not in self.monsters:
            return
        self.monsters.remove(m)
        if m.spawn:
            self.changes[m.spawn] = "."           # it stays beaten if you come back
        self.game.effect("poof", cave_xy=m.center)
        self.game.log("You defeated the %s!" % m.name, "quest")
        self.game.sound("victory")
        self.game.monster_gone(m.info, give_xp=give_xp)

    def shoot(self, m):
        m.reload = ARROW_EVERY
        x, y = m.center
        self.arrows.append({"x": x + 0.4 * m.facing, "y": y - 0.1, "vx": ARROW_SPEED * m.facing,
                            "damage": m.info.damage})
        self.game.sound("shoot")

    def move_arrows(self, dt):
        you = self.you
        for arrow in list(self.arrows):
            arrow["x"] += arrow["vx"] * dt
            x, y = arrow["x"], arrow["y"]
            if self.is_solid(math.floor(y), math.floor(x)) or not 0 <= x <= self.cols:
                self.arrows.remove(arrow)
            elif arrow.get("yours"):
                hit = next((m for m in self.monsters if m.touches(x - 0.15, y - 0.05, 0.3, 0.1)), None)
                if hit:                                   # your arrow hits a monster!
                    self.arrows.remove(arrow)
                    self.hurt_monster(hit, self.game.arrow_damage(hit.info.special), x - arrow["vx"])
            elif you.touches(x - 0.15, y - 0.05, 0.3, 0.1):
                self.arrows.remove(arrow)
                if you.safe_time <= 0:
                    self.game.log("A Skeleton's arrow hits you!", "bad")
                self.hurt_you(self.game.rng.randint(*arrow["damage"]), x - arrow["vx"])

    def explode(self, m):
        game, you = self.game, self.you
        x, y = m.center
        game.effect("boom", cave_xy=(x, y))
        game.sound("boom")
        game.log("BOOM! The %s exploded!" % m.name, "bad")
        if math.hypot(you.center[0] - x, you.center[1] - y) < BLAST_RADIUS:
            self.hurt_you(game.rng.randint(*m.info.damage), x)
            you.vy = -9.0
        # The blast breaks cracked rock nearby
        for r in range(math.floor(y - BLAST_RADIUS), math.floor(y + BLAST_RADIUS) + 1):
            for c in range(math.floor(x - BLAST_RADIUS), math.floor(x + BLAST_RADIUS) + 1):
                if self.tile(r, c) == "B" and math.hypot(c + 0.5 - x, r + 0.5 - y) < BLAST_RADIUS:
                    self.change(r, c, ".")
                    game.effect("rubble", cave_xy=(c + 0.5, r + 0.5), ore=False)
        self.defeat(m, give_xp=False)

    # ----- crumbly ledges -------------------------------------------------------------

    def update_ledges(self, dt):
        for spot in list(self.crumbling):
            self.crumbling[spot] -= dt
            if self.crumbling[spot] <= 0:
                del self.crumbling[spot]
                r, c = spot
                self.change(r, c, "_", forever=False)     # "_" is a ledge that fell
                self.fallen[spot] = CRUMBLE_BACK
                self.game.effect("crumble", cave_xy=(c + 0.5, r + 0.2))
                self.game.sound("dig")
        for spot in list(self.fallen):
            self.fallen[spot] -= dt
            r, c = spot
            in_the_way = any(body.touches(c, r, 1, 1) for body in [self.you] + self.monsters)
            if self.fallen[spot] <= 0 and not in_the_way:
                del self.fallen[spot]
                self.change(r, c, "-", forever=False)
