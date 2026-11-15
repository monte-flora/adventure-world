"""
Game RULES for Adventure World.

This file knows nothing about graphics. It only keeps track of the world:
where everything is, health, items, quests and fights. The pictures, sounds
and keyboard live in game.py.

Splitting them up means you can change how the game LOOKS without breaking
how it WORKS - and the other way around.

Try changing the settings below to make your own version of the game!
"""

import random

import castle
import caves
import story
import throne

# ===========================================================================
# THE WORLD MAP - edit it to make your own world!
#   H = House (safe)   F = Forest   G = Field (open grass)   M = Mine   P = Portal   W = Water
#   R = Path (the brown dirt path: monsters won't chase you on it, and nothing bad happens there)
#   X = Rock (nobody can walk through it)   I = Ice (you slide!)   B = Reeds (monsters can't see you)
#   V = Steam vent (it puffs every 3rd turn)   L = Landmark (climb it with SPACE to look around)
#   T = Treasure chest   O = Bubbles in the water (row over them and dive!)   + = Signpost
#   ~ = The Icy River (water)   = = Broken bridge (walk onto it carrying 5 wood to fix it)   S = The Secret Mine
# The map is split into LANDS (see LANDS below): snow in the Frosty Corner, red rock in Ember Canyon...
# It can be any size - the camera scrolls to follow you.
# Home is the LAST H (reading left to right, top to bottom): you start there. Any other H is a rest house.
# The Portal is on the island in the middle of the big lake: you'll need a boat to get there!
# The path loops around the lake, far from the water and the trees - leave it to chop wood or find berries.
# ===========================================================================
WORLD_MAP = """
F F F F F F F F F F F F G X G G X X G X X X G X X G X G ~ X X X F F F I I I I F
F G T F F F F F F F F G X G G G X G G G L G G G X G G G ~ X L X G G G I X I I F
F S G F F F F F F F F G G G M G G X G G G G X G G X G G ~ G G G G G G I I T I F
F F F F F G G G G G G G G G G G G G G G G G G G G G G G ~ G G G G G G I I X X F
F F F F G G G G G G G G G R R R R R R R R R R R R R G G ~ G G G G G G G G G G F
F F F G G G G G + R R R R R G G G G G G G G G G G R R R = H G G G M G G F F F F
F F F G G G R R R R G G G G G G G G G G G G G G G G G G ~ G G G G G G G G F F G
F F F G G R R G G G G G G G G G G G G F F F G G G G G G ~ G G G G G + G G G G G
F F F G G R G G G G G G G G G G G W W W W W G G G G G G ~ G G G G G G G G G G G
F G F G G R G G G G G G G W W W W W W W W W W W W G F F ~ G G F F G G G G G G F
F F F G G R G G F F W W W W W W W W W W W W W W W W W W ~ G G G G G G G I I F F
F F F G G R G G F W W W W W W W W W W W W W W W W W W W W W G G G G G G G G F F
F F F M G R G G F W W W W W W W W W W W W W W W W G L W W W W G G G G G G F F F
F G F G G R G M G W W W W W W W W W F G G G W W W W W W W W W W G F G G G F F F
G L G G G R G G G W W W W W W W W G G G G M G W W W W W W W W W G F G G G G F F
F G F G G R G G G G W W W W W W W G G P G G G W W W W W W W W W G G G G G G G G
F F F G G R G G G G W W W W W W W G F G G G F W W W W W W W W F F X X G G M G X
F F F G G R G G G G W W T W W W W W G G G F W W W W W W W W X X X X X X X X X X
F F F G G R R G G G G W W W W W W W W W W W W W W W W W W G G G G G G R G B B B
F F F G M G R G G G G W W W O W W W W W W W W W W W W W G G G G G G R R G B B F
F F G G G G R G G G G G W W W W W W W W W W W W W W W G G G G G G R R G B B B F
F F G G G G R R G G G G G G W W W W W W W W W W W G G G G G G G R R + B B B F B
G G G G L G G R G G M G G G F F F G G G G G G G G G G G G G G R R G B B B F F B
G G G G G G + R R G G G G G G G G G M G G G G G G G G G G G R R G B B B B B F B
G G G G G G G H R R R G G G G G G G G G G G G G G G G G R R R G G B B B B B B B
F F F F G G G G G G R R R R R R R R R R R R R R R R R R R G G G B B B B F B B B
F F F F F G G G G G G G G G G G G G G G G G + G G G G G G G G M G F B B B B F B
F F F F F F G G G G G G M G X X G V G G M G G X X G V G X X G G B F B B L B B B
F F F F F F G G G G G G G X X G G G X G V G X X G G L G G X X G B B B B B B F B
F F F F F F G G G G G G G X X X G V X X G G G X V G G X X X X G B B B F B B B B
"""

# ===========================================================================
# NIGHTFALL HOLLOW - the Shadow King's dark world, on the other side of the Portal
#   H = glowing shrine (safe)   F = dead forest   G = dead grass   W = black water   C = the castle
#   D = dark shrine (a Shadow Guardian sits on it: beat it, then press SPACE to light the beacon)
#   M = a shadow Mine (a dark cave with a diamond and a Sun Shard)   X = black cliff   T = a chest
#   L = a landmark (Dead Giant Tree, Black Lighthouse): climb it with SPACE to look around   + = a signpost
#   N = Wren the ghost (SPACE talks to her)   Q = a lost lantern (walk onto it to pick it up)
#   = = the broken Shadow Bridge (the black river splits the land in two: the chest on the west side has the planks)
# You arrive at the first H.
# ===========================================================================
NIGHTFALL_MAP = """
H G G F F G G F F G G G W W G G F F G G G G F F G G G G
G F F F G G G G F G G G W W G G G F G G D G G G F F G G
G F N G G M G G F F G G X W G F G G G G G G G F F G Q G
G G G G G G G G + G F G W W G G G G G G G G G G G G G G
F F G G D G G F F G G G W X G G G F F G G G G G G F G G
F G G G G G G G G G G G W W G G M G G G G G G G G G G G
G G F F G G G G W W G G W W G G G G G F F G L G G G G G
G G F L G G G G W W G G X W G G G G G G G G G G G G G G
G G G G G G G G G G H G W W G H G G G G G G G G F F G G
G G G G G G G G G G G G = = G G + G G G G G G G G G G G
G G G G G G G G G Q G G W W G G G G G F F G G G G G G G
G T G G F F G G G G G G W X G G G G G G G G G X X X G G
G G G G F F G G G G G G W W G G G G G G G G G X T X G G
G G F G G G G G G G G G W W G G G G G D G G G G G G G G
G G F F G G G G G G G G X W G G G G G G G G G G G G M G
G G G G G G G G G G G G W W G G G G F F G G G G G G G G
G G G Q G G G G G G G G W W G G G G G G G G G G G G H G
G G G G G G G G G G G G W W G G G G G G G G G G G G G C
"""

TILE_NAMES = {"H": "House", "F": "Forest", "G": "Field", "M": "Mine", "P": "Portal", "W": "Water", "C": "Castle",
              "R": "Path", "X": "Rock", "I": "Ice", "B": "Reeds", "V": "Steam Vent", "L": "Landmark",
              "T": "Treasure Chest", "+": "Signpost", "=": "Broken Bridge", "#": "Bridge", "S": "Secret Mine"}
NIGHTFALL_NAMES = {"H": "Shrine", "F": "Dead Forest", "G": "Dead Grass", "M": "Shadow Mine", "W": "Black Water",
                   "C": "Castle", "D": "Dark Shrine", "X": "Black Cliff", "T": "Treasure Chest",
                   "=": "Broken Shadow Bridge", "#": "Shadow Bridge", "L": "Landmark", "+": "Signpost",
                   "N": "Wren the Ghost", "Q": "Lost Lantern"}
WALKABLE = "HFGMPCRIBVLT+#SDNQ"   # every letter except W (water: you need a boat), X (rock: nobody gets through)
                               # and = (the broken bridge: fix it first!)
SAFE = "HL"                    # monsters can't reach you in a house, or up on a landmark

# Chance something bad happens when you walk onto a tile. (On the path, nothing happens - good or bad!)
TILE_DANGER = {"F": 0.15, "M": 0.25, "G": 0.05, "B": 0.05}

# ===========================================================================
# THE LANDS of the home world. Each one has its own look, its own landmark (the L on the map)
# and one new thing to learn. A square belongs to the first land whose box it's in.
#   name, top row, left column, bottom row, right column, its landmark, what you hear the first time you get there
# ===========================================================================
LANDS = [
    ("Portal Island",    13, 17, 17, 22, None,
     "The Portal hums in the middle of the lake."),
    ("Frosty Corner",     0, 28, 17, 39, "Frost Peak",
     "Brrr! Snow everywhere. On the ice you slide until you bump into something!"),
    ("Old Ruins",         0, 11,  3, 27, "Watchtower",
     "Broken walls of an old castle. Skeletons hide here - bring your bow!"),
    ("Whispering Woods",  0,  0,  2, 10, "Queen Oak",          # the woods have 2 boxes: the top corner...
     "The trees whisper... Chop wood, find berries, and forge swords here."),
    ("Whispering Woods",  0,  0, 21,  4, "Queen Oak",          # ...and the strip down the west side
     "The trees whisper... Chop wood, find berries, and forge swords here."),
    ("Misty Marsh",      18, 32, 29, 39, "Frog's Hut",
     "Tall reeds hide you, so monsters can't chase you. Mind the mud!"),
    ("Ember Canyon",     26, 13, 29, 31, "Dragon Bones",
     "Hot red rocks! The steam vents puff every 3rd turn. Watch for the little wisp!"),
    ("Home Meadow",      19,  0, 29, 12, "Windmill",
     "Your home meadow. Follow the path to find your first Mine!"),
    ("The Great Lake",    0,  0, 29, 39, "Lighthouse",          # everything else: the lake and its shores
     "A huge lake. Build a boat to reach the islands - and the Portal!"),
]
LANDMARK_SIGHT = 6        # you can see a landmark through the fog from this many squares away
LOOKOUT_SIGHT = 7         # climb a landmark (SPACE) and the fog lifts this far around it
VENT_EVERY = 3            # a steam vent puffs every 3rd turn...
VENT_DAMAGE = 2           # ...and hurts this much if you're standing on it

# The first time you step onto one of these, you're told how it works (see first_time_tip).
# Each one is: the tile's letter -> (the tip's name, its words, the color it is in the message log)
FIRST_TIME_TIPS = {
    "R": ("path", "You found the path! Monsters won't chase you here, and nothing bad happens.", "good"),
    "I": ("ice", "Whee! On ice you slide until you bump into something.", "quest"),
    "B": ("reeds", "You hide in the tall reeds. Monsters can't see you in here!", "good"),
    "V": ("vent", "A steam vent! It puffs every %d turns. When you see a little wisp, it's about to blow!"
          % VENT_EVERY, "quest"),
}

# Where each kind of monster likes to live. About half of them start out in their land, the rest roam anywhere.
# (They still start far enough from home - see MONSTER_START_DISTANCE below.)
MONSTER_LANDS = {"Spider": "Whispering Woods", "Skeleton": "Old Ruins", "Ember Skull": "Ember Canyon",
                 "Zombie": "Misty Marsh"}
IN_THEIR_LAND = 0.5

# The treasure chests (T) on the map, by the land they're in. Each one opens only once.
MAP_CHEST_PRIZES = {"Whispering Woods": ["key", "food"], "Frosty Corner": ["armor"], "The Great Lake": ["bow", "arrows"]}
MAP_CHEST_GOLD = 10       # gold coins in a chest are worth this much XP
BRIDGE_WOOD = 5           # walk onto the broken bridge carrying this much wood, and you fix it
HEAL_EVENT_CHANCE = 0.12
SIGHT_RADIUS = 2          # how far you can see through the fog
# In Nightfall Hollow your lantern starts small, and every lit beacon makes it bigger (index = beacons lit)
LANTERN_RADIUS = [2, 3, 4, 5]
BEACON_LIGHT = 4          # shadow monsters this close to a lit beacon are weaker: they hit 1 less and move slower
MOONRISE_EVERY = 40       # in Nightfall Hollow the moon rises every 40 turns...
MOONRISE_TURNS = 15       # ...and stays up this long
MOON_CHASE = 2            # under the moon, shadow monsters notice you this much farther away (not in the light)
WISP_HOPS = 3             # follow a moon wisp this many times and it leaves a gift
WISP_GIFTS = ["food", "armor", "gold"]
WREN_LANTERNS = 3         # Wren the ghost has lost this many lanterns
LIGHT_SLOWDOWN = 0.5      # ...they move only this much as often

# ===========================================================================
# PLAYER SETTINGS
# ===========================================================================
START_HEALTH = 25
START_LIVES = 3           # you start with this many lives (the hearts at the top of the panel)
MAX_LIVES = 9             # the "Extra life" power can't give you more than this many
MAX_SWORDS = 3
MAX_FOOD = 3
SWORD_DURABILITY = 16     # hits before a sword breaks
GREAT_SWORD_DURABILITY = 24   # a Great sword (forged with 2 Perfect strikes and no Miss) lasts longer...
GREAT_SWORD_BONUS = 1     # ...and hits 1 harder
CRACKED_SWORD_DURABILITY = 4  # a Cracked sword (2 or more Misses at the forge) breaks quickly
GREAT_CHEST_CHANCE = 1 / 3    # about 1 sword in 3 that you find in a chest is a Great sword
LOW_USES = 3              # a sword with this many hits left chips: a sound, a message, and its pips turn red
FORGE_STRIKES = 3         # the forge game: 3 hammer strikes...
FORGE_GOLD = 0.08         # ...Perfect in the gold zone (8% of the bar)...
FORGE_GREEN = 0.24        # ...Good in the green zone around it (24% of the bar), and Miss anywhere else
FORGE_SPEEDUP = 1.15      # the glowing metal moves 15% faster after every strike
PICKAXE_DURABILITY = 10   # unused now: a pickaxe never breaks (digging never wears it down)
PICKAXE_CAVE_WOOD = 2     # in a cave there are no trees, so a pickaxe costs this much wood
FOOD_HEAL = 3
BERRY_CHANCE = 0.75       # searching the forest finds berries 75 times out of 100
REST_HEAL = 4
HOUSE_HEAL = 1            # health you get back every turn you spend in a house
ARMOR_POINTS = 6          # how much damage your armor soaks up before it breaks
SUNFANG_DIAMONDS = 3      # Sunfang is forged from this many diamonds (the Blade), at the Shadow King's castle
HILT_WOOD = 6             # the Hilt is carved from this much dead wood (in the Craft menu, in Nightfall Hollow)
NIGHT_LANDMARKS = ["Dead Giant Tree", "Black Lighthouse"]   # Nightfall Hollow's landmarks, west to east
SUN_SHARDS_NEEDED = 3     # the Sun Gem is made of this many Sun Shards (one hides in each shadow Mine)
BEACONS_NEEDED = 3        # light all of the dark shrines, and the forge at the castle gate wakes up
SUNFANG_DAMAGE = (6, 9)   # Sunfang hits this hard (smallest, biggest) - and it never breaks
SUNFANG_HIT_CHANCE = 0.85 # in a fight, Sunfang hits 85 times out of 100
PERFECT_BONUS = 1         # a Perfect Forge makes Sunfang hit 1 harder
RING_HITS = 5             # a diamond ring powers up your sword for this many hits...
RING_BONUS = 3            # ...and each of those hits does this much extra damage
MAX_RING_HITS = 15        # find more rings and the power adds up, to this many hits
XP_PER_LEVEL = 60         # 60 XP gets you from level 1 to level 2, then 120 more to level 3, 180 to level 4, ...

# ===========================================================================
# XP - where it comes from
# (Monsters: their "xp" in MONSTER_TYPES below. Gems and gold coins: GEM_XP and CHEST_XP in caves.py.)
# ===========================================================================
DIAMOND_XP = 10           # mining a diamond
EXIT_XP = 5               # walking out of a cave's EXIT door (only the first time for each cave)
QUEST_XP = 15             # finishing a quest

# ===========================================================================
# LEVEL UP POWERS - try changing these!
# When you level up you are fully healed, and you pick 1 of 3 powers.
#   what  : what it does (the LEVEL UP! card shows this)
#   limit : how many times you can pick it (None = as many times as you like)
# When you have a power as many times as its limit, it isn't offered any more.
# ===========================================================================
STRONGER_DAMAGE = 1       # Stronger: every sword, Sunfang and arrow hit does this much more damage
TOUGHER_HEALTH = 4        # Tougher: this much more max health (and you get it right away)
SHARP_DAMAGE = 1          # Sharpshooter: your arrows hit this much harder...
SHARP_ARROWS = 5          # ...and you can carry this many more arrows
ARMOR_BOOST = 3           # Tough armor: your armor soaks up this much more damage
FORAGER_BERRY_CHANCE = 0.9    # Forager: searching the forest finds berries 90 times out of 100...
FORAGER_FOOD = 1          # ...and you can carry this much more food
# Springy, Speedy and Lucky change the caves, so their numbers are in caves.py:
# SPRINGY_JUMP, SPEEDY_RUN and LUCKY_RING_CHANCE.

POWERS = {
    "Stronger":     {"what": "+%d damage with your sword, Sunfang and arrows" % STRONGER_DAMAGE, "limit": None},
    "Tougher":      {"what": "+%d max health" % TOUGHER_HEALTH, "limit": None},
    "Sharpshooter": {"what": "arrows hit +%d harder, and you carry %d more" % (SHARP_DAMAGE, SHARP_ARROWS), "limit": 3},
    "Tough armor":  {"what": "armor soaks up %d more damage before it breaks" % ARMOR_BOOST, "limit": 3},
    "Springy":      {"what": "jump higher in caves and the castle", "limit": 2},
    "Speedy":       {"what": "run faster in caves and the castle", "limit": 2},
    "Lucky":        {"what": "%d out of 100 chests hide a diamond ring" % round(caves.LUCKY_RING_CHANCE * 100), "limit": 1},
    "Extra life":   {"what": "+1 life (up to %d lives)" % MAX_LIVES, "limit": None},
    "Forager":      {"what": "find berries %d times out of 100, and carry %d more food"
                             % (round(FORAGER_BERRY_CHANCE * 100), FORAGER_FOOD), "limit": 1},
}
MAIN_POWERS = ["Stronger", "Tougher"]     # every LEVEL UP! card has one of these on it
CARD_CHOICES = 3                          # how many powers the LEVEL UP! card lets you pick from

# ===========================================================================
# WOOD, BUILDING AND BOATS (press T in the forest to chop wood, C to craft)
# ===========================================================================
WOOD_PER_CHOP = (1, 2)    # chopping a tree gives you this much wood (smallest, biggest)
TREE_WOOD = 8             # every tree has this much wood in it. Chop it all and the tree is gone!
MAX_WOOD = 12             # how much wood you can carry
HOUSE_COST = 5            # wood you need to build a house
BOAT_COST = 8             # wood you need to build a boat
BOW_COST = 3              # wood you need to carve a bow (it never breaks)
ARROW_COST = 2            # wood for a bundle of arrows...
ARROWS_PER_BUNDLE = 5     # ...with this many arrows in it
MAX_ARROWS = 15           # how many arrows you can carry
ARROW_RANGE = 3           # on the world map, your arrows fly this many squares
ARROW_DAMAGE = (3, 5)     # how much an arrow hurts (smallest, biggest)
FIRE_ARROW_BONUS = 2      # in Nightfall Hollow your arrows burst into flame: they hit this much harder
SHIPWRECK_CHANCE = 0.08   # each round of a fight, the chance a Sea Serpent smashes your boat (8 out of 100)
DROWN_DAMAGE = (4, 6)     # how much it hurts when your boat sinks!

# ===========================================================================
# QUESTS
# ===========================================================================
MONSTERS_TO_DEFEAT = 5
DIAMONDS_NEEDED = 3

# ===========================================================================
# MONSTERS - add your own! Copy a line and change the numbers.
#   health      : how many hits it can take
#   damage      : (smallest, biggest) hit it can do
#   move_chance : how often it moves (0 = never, 1 = every turn)
#   xp          : experience you get for beating it
#   special     : "tough"    - your hits do 1 less damage
#                 "archer"   - shoots arrows from 2 tiles away
#                 "explodes" - blows up after 3 rounds of fighting!
#                 "drowns"   - lives in the water and can smash your boat!
#                 None       - nothing special
# ===========================================================================
MONSTER_TYPES = {
    "Zombie":   {"health": 12, "damage": (1, 3), "move_chance": 0.25, "xp": 4, "special": "tough"},
    "Skeleton": {"health": 7,  "damage": (1, 2), "move_chance": 0.50, "xp": 5, "special": "archer"},
    "Ember Skull": {"health": 6, "damage": (5, 7), "move_chance": 0.60, "xp": 6, "special": "explodes"},
    "Spider":   {"health": 5,  "damage": (1, 2), "move_chance": 0.80, "xp": 3, "special": None},
    "Sea Serpent": {"health": 10, "damage": (2, 3), "move_chance": 0.60, "xp": 7, "special": "drowns"},
    # The Shadow Guardian sits on a dark shrine and never leaves it (move_chance 0). It's only made as a shadow
    # monster, so: 16 x 1.5 = 24 health, and it hits for 3-5. It isn't in any monster counts below.
    "Guardian": {"health": 16, "damage": (2, 4), "move_chance": 0.0, "xp": 12, "special": "guardian"},
    # The Shadow Warden stands in front of the Shadow Bridge (shadow: 36 health, hits 4-6). Beat it to cross.
    "Warden": {"health": 24, "damage": (3, 5), "move_chance": 0.0, "xp": 25, "special": "warden"},
}

MONSTER_COUNTS = {"Zombie": 9, "Skeleton": 6, "Ember Skull": 5, "Spider": 15, "Sea Serpent": 4}
NIGHTFALL_MONSTER_COUNTS = {"Zombie": 4, "Skeleton": 3, "Ember Skull": 3, "Spider": 6, "Sea Serpent": 2}
SHADOW_BOOST = 1.5        # shadow monsters in Nightfall Hollow have this much more health and XP (and hit 1 harder)
BIG_LAKE = 10             # Sea Serpents only live in lakes at least this many squares big
CHASE_DISTANCE = 3        # monsters this close will come after you (but not while you're on the path)

# How many squares from home each kind of monster starts out (on the home map).
# Weak monsters live near home, strong ones farther away. Any kind not listed here: 5 squares.
MONSTER_START_DISTANCE = {"Zombie": 5, "Spider": 5, "Skeleton": 12, "Ember Skull": 18, "Sea Serpent": 5}

DIRECTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

INJURIES = {
    "F": [
        "You trip over a root and scrape your knee.",
        "A falling branch hits you on the shoulder.",
        "A snake slithers out and nips your ankle!",
    ],
    "M": [
        "You stumble into a sharp rock.",
        "You walk too close to a patch of lava!",
        "A swarm of bats knocks you over!",
    ],
    "G": [
        "You step on a thistle. Ouch!",
        "You trip over a stone hidden in the grass.",
        "A thorny weed scratches your leg.",
    ],
    "B": [
        "Squelch! Your boot gets stuck in the mud and you fall over.",
        "You slip on a muddy log.",
    ],
}
# In some lands the open ground is snow or hot sand, so bad luck there sounds different
LAND_INJURIES = {
    "Frosty Corner": ["You slip on the snow and land on your bottom!", "A snowball falls off a branch onto your head!"],
    "Ember Canyon": ["Ouch! The hot sand burns your toes.", "A hot pebble rolls onto your foot!"],
}
HEALS = [
    "You find a fresh spring and take a drink.",
    "A calming breeze soothes your wounds.",
    "A glowing butterfly lands on you... you feel better.",
    "You crush some herbs and feel revitalized.",
]


# ===========================================================================
# Game objects
# ===========================================================================

class Tool:
    """A sword (wears out as you use it) or a pickaxe (lasts forever).
    A sword's quality is "great", "normal" or "cracked"."""

    def __init__(self, name, durability, quality="normal"):
        self.name = name
        self.durability = durability
        self.max_durability = durability
        self.quality = quality
        self.chipped = False             # True when it just got down to LOW_USES (the game then warns you)

    def use(self):
        """Wear the tool down by 1. Returns True if it just broke."""
        self.durability -= 1
        if self.durability == LOW_USES:
            self.chipped = True
        return self.durability <= 0

    @property
    def low(self):
        return 0 < self.durability <= LOW_USES


SWORD_USES = {"great": GREAT_SWORD_DURABILITY, "normal": SWORD_DURABILITY, "cracked": CRACKED_SWORD_DURABILITY}


def make_sword(quality="normal"):
    return Tool("Sword", SWORD_USES[quality], quality)


def strike_grade(pos, zone_x):
    """One hammer strike at the forge. zone_x is where the green zone starts; the gold zone is in its middle.
    Returns "perfect", "good" or "miss"."""
    gold_x = zone_x + (FORGE_GREEN - FORGE_GOLD) / 2
    if gold_x <= pos <= gold_x + FORGE_GOLD:
        return "perfect"
    if zone_x <= pos <= zone_x + FORGE_GREEN:
        return "good"
    return "miss"


def sword_quality(strikes):
    """The 3 strikes make the sword: 2 Perfect and no Miss is Great, 2 Misses is Cracked, anything else normal."""
    if strikes.count("miss") >= 2:
        return "cracked"
    if strikes.count("perfect") >= 2 and "miss" not in strikes:
        return "great"
    return "normal"


class Player:
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos
        self.health = START_HEALTH
        self.max_health = START_HEALTH
        self.lives = START_LIVES         # health runs out: lose a life and wake up somewhere safe
        self.level = 1
        self.xp = 0
        self.swords = [make_sword()]
        self.pickaxe = Tool("Pickaxe", PICKAXE_DURABILITY)
        self.food = 1
        self.diamonds = 0
        self.armor = 0                   # armor soaks up damage until it breaks
        self.wood = 0
        self.has_boat = False
        self.has_bow = False
        self.arrows = 0
        self.ring_hits = 0               # powered-up sword hits left from a diamond ring
        self.has_tower_key = False       # the old key to the Watchtower (it's in a chest deep in the woods)
        self.lanterns = 0                # Wren's lost lanterns you picked up
        self.sun_shards = 0              # Sun Shards from the shadow Mines (3 make the Sun Gem)
        self.has_hilt = False            # the Hilt, carved from dead wood in Nightfall Hollow
        self.has_planks = False          # the old planks from the chest in the west: they fix the Shadow Bridge
        self.sunfang = False             # forged at the castle gate from 3 diamonds
        self.sunfang_perfect = False     # forged with a Perfect Forge: +1 damage
        self.light_shards = 0            # found in the castle: they make Sunfang glow brighter
        self.fire_arrows = False         # your arrows burst into flame in Nightfall Hollow: they hit harder
        self.facing = "right"            # the way you last walked: that's where your arrows go
        self.monsters_defeated = 0
        self.powers = {}                 # the level-up powers you picked: name -> how many times

    @property
    def is_alive(self):
        return self.health > 0

    @property
    def xp_needed(self):
        return XP_PER_LEVEL * self.level

    def power(self, name):
        """How many times you picked this level-up power (0 if you never picked it)."""
        return self.powers.get(name, 0)

    def maxed(self, name):
        """True when you have this power as many times as you can."""
        if name == "Extra life":
            return self.lives >= MAX_LIVES   # you can always get more lives, up to MAX_LIVES
        limit = POWERS[name]["limit"]
        return limit is not None and self.power(name) >= limit

    @property
    def strength_bonus(self):
        """Extra damage on every sword, Sunfang and arrow hit. Only the Stronger power gives it."""
        return self.power("Stronger") * STRONGER_DAMAGE

    @property
    def damage_bonus(self):
        """Extra damage on a sword hit: the Stronger power, and +1 if the sword in your hand is a Great sword."""
        great = not self.sunfang and self.swords and self.swords[0].quality == "great"
        return self.strength_bonus + (GREAT_SWORD_BONUS if great else 0)

    @property
    def max_armor(self):
        """How much damage your armor soaks up when it's new (Tough armor makes it more)."""
        return ARMOR_POINTS + self.power("Tough armor") * ARMOR_BOOST

    @property
    def max_arrows(self):
        return MAX_ARROWS + self.power("Sharpshooter") * SHARP_ARROWS

    @property
    def max_food(self):
        return MAX_FOOD + self.power("Forager") * FORAGER_FOOD

    def heal(self, amount):
        if not self.is_alive:
            return 0                     # no healing brings you back once you're defeated
        before = self.health
        self.health = min(self.max_health, self.health + amount)
        return self.health - before

    @property
    def has_armor(self):
        return self.armor > 0

    def put_on_armor(self):
        self.armor = self.max_armor

    def hurt(self, amount):
        """Your armor soaks up the damage first. Returns how much the armor took."""
        soaked = min(self.armor, amount)
        self.armor -= soaked
        self.health = max(0, self.health - (amount - soaked))
        return soaked


class Monster:
    def __init__(self, kind, pos, shadow=False):
        info = MONSTER_TYPES[kind]
        self.base_kind = kind                   # which picture to draw
        self.kind = "Shadow " + kind if shadow else kind
        self.shadow = shadow
        self.pos = pos
        boost = SHADOW_BOOST if shadow else 1
        self.health = self.max_health = round(info["health"] * boost)
        low, high = info["damage"]
        self.damage = (low + 1, high + 1) if shadow else (low, high)
        self.move_chance = info["move_chance"]
        self.xp = round(info["xp"] * boost)
        self.special = info["special"]

    @property
    def is_alive(self):
        return self.health > 0


class Quest:
    def __init__(self, description, goal_count):
        self.description = description
        self.goal_count = goal_count
        self.progress = 0

    @property
    def completed(self):
        return self.progress >= self.goal_count

    def advance(self):
        """Add one to the quest. Returns True the moment it is completed."""
        if self.completed:
            return False
        self.progress += 1
        return self.completed


class Battle:
    def __init__(self, monster):
        self.monster = monster
        self.fuse = 3 if monster.special == "explodes" else None
        self.result = None      # becomes "won", "fled", "exploded", "drowned" or "lost"
        self.lines = []         # what happened in this fight

    @property
    def over(self):
        return self.result is not None


# ===========================================================================
# The game
# ===========================================================================

def parse_map(text):
    return [line.split() for line in text.strip().splitlines()]


def tiles_of(grid, letter):
    """Every spot on a map (a list of rows) with this letter, reading left to right, top to bottom."""
    return [(r, c) for r, row in enumerate(grid) for c, tile in enumerate(row) if tile == letter]


def a_or_an(name):
    """'A Zombie', but 'An Ember Skull'."""
    return ("An " if name[0] in "AEIOU" else "A ") + name


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def compass(here, there):
    """Which way to go from here to there: "north", "south-east", "west"..."""
    dr, dc = there[0] - here[0], there[1] - here[1]
    up_down = "north" if dr < -2 else "south" if dr > 2 else ""
    sideways = "west" if dc < -2 else "east" if dc > 2 else ""
    return "-".join(word for word in (up_down, sideways) if word) or "right here"


class Game:
    def __init__(self, player_name="Hero", seed=None):
        self.rng = random.Random(seed)
        self.map = parse_map(WORLD_MAP)
        self.rows = len(self.map)
        self.cols = len(self.map[0])
        self.world = 1                  # 1 = home, 2 = Nightfall Hollow
        self.sunken_chests = self.swap_letters("O", "W")     # bubbles: a sunken chest down in the water
        self.river = self.swap_letters("~", "W")             # the Icy River is water too (you can row up it)
        self.landmarks = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.map[r][c] == "L"]
        self.start = self.find_tile("H", last=True)     # home is the last house on the map
        self.lodges = {(r, c) for r in range(self.rows) for c in range(self.cols)
                       if self.map[r][c] == "H" and (r, c) != self.start}     # the Hunter's Lodge (a rest house)
        self.portal = self.find_tile("P")
        mines = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.map[r][c] == "M"]
        self.cave_plan = caves.plan_caves(mines, self.start)     # every Mine has its own cave
        self.mainland = self.reach(self.start)                  # everywhere you can walk to without a boat
        # Not every cave has a diamond! In the others, a treasure chest sits where the diamond ore was.
        self.diamond_mines = caves.pick_diamond_mines(self.cave_plan, self.start, self.mainland)
        for mine in mines:
            if mine not in self.diamond_mines:
                self.cave_plan[mine] = caves.without_diamond(self.cave_plan[mine])
        # The Secret Mine gets a cave of its own, from a file in levels/secret. It's not in the cave plan,
        # so the other Mines keep their caves. And it ALWAYS has a diamond!
        self.secret_mines = {}
        for i, spot in enumerate((r, c) for r in range(self.rows) for c in range(self.cols) if self.map[r][c] == "S"):
            self.secret_mines[spot] = caves.SECRET_CAVES[i % len(caves.SECRET_CAVES)]
            self.diamond_mines.add(spot)
        self.lighthouse_lit = False     # climb the Lighthouse, and every Mine with a diamond sparkles

        self.player = Player(player_name, self.start)
        self.lands_seen = {self.land_name(self.start)}     # the lands you've been to (you start at home)
        self.glints = set()             # Mines you saw sparkle from a landmark: they still have a diamond
        self.forging = False            # True while Sunfang is being forged (the graphics play the scene)
        self.beacons = set()            # the dark shrines you lit in Nightfall Hollow
        self.night_landmarks = {}       # Nightfall Hollow's landmarks: spot -> name
        self.plank_chest = None         # the chest in the west that holds the bridge planks
        self.wren_quest = None          # "Find Wren's lanterns" (starts when you talk to her)
        self.moon = 0                   # turns of moonrise left in Nightfall Hollow (0 = the moon is down)
        self.wisp = None                # the little moon wisp to follow (a spot on the map)
        self.wisp_hops = 0
        self.wren_thanked = False       # you brought her the lanterns and got your reward
        self.shard_mines = set()        # the shadow Mines that have a Sun Shard in their cave
        self.castle = None
        self.knockouts = 0              # how many times you got knocked out in the castle
        self.lives_lost = 0             # how many lives you lost (anywhere)
        self.out_of_lives = 0           # how many times you ran out of lives (and got 3 new ones)
        self.king_fights = 0            # how many times you fought the Shadow King (THE END shows it)
        self.castle_levels_seen = set() # castle levels you've been to (each one has a story card the first time)
        self.tips_seen = set()          # cave tips you've already been told (ladders, tunnels...)
        self.pickaxe_cave_wood = PICKAXE_CAVE_WOOD
        self.monsters = self.spawn_monsters(MONSTER_COUNTS)
        self.monster_quest = Quest("Defeat %d monsters" % MONSTERS_TO_DEFEAT, MONSTERS_TO_DEFEAT)
        self.diamond_quest = Quest("Mine %d diamonds" % DIAMONDS_NEEDED, DIAMONDS_NEEDED)
        self.quests = [self.monster_quest, self.diamond_quest]

        self.turn = 1
        self.won = False
        self.battle = None
        self.cave = None        # the cave you're exploring, if you're in one
        self.cleared_mines = set()   # mines whose diamond you already found
        self.empty_mines = set()     # mines you explored all the way to the EXIT: no diamond in there
        self.exited_mines = set()    # mines whose cave you walked out of through the EXIT door (for EXIT_XP)
        self.cave_changes = {}       # for each mine: what you dug, opened and beat in its cave
        self.tree_wood = {}          # wood left in the trees you started chopping: (row, col) -> wood
        self.level_ups = []          # levels you reached that still need a LEVEL UP! card (pick a power)
        self.power_offer = None      # the powers on the LEVEL UP! card that's showing
        self.messages = []      # (text, kind) - shown in the message log
        self.effects = []       # things for the graphics to animate
        self.seen = set()       # tiles you have discovered
        self.story = []         # story cards waiting to be shown
        self.tell(story.INTRO)
        self.reveal()
        self.log("Welcome, %s! Defeat %d monsters and mine %d diamonds, then reach the Portal."
                 % (player_name, MONSTERS_TO_DEFEAT, DIAMONDS_NEEDED), "quest")
        self.log("Not every cave has a diamond - explore to find them!", "quest")

    # ----- messages and effects ---------------------------------------------

    def log(self, text, kind="info"):
        """kind is one of: info, good, bad, loot, quest"""
        self.messages.append((text, kind))

    def effect(self, effect_type, **data):
        data["type"] = effect_type
        self.effects.append(data)

    def sound(self, name):
        self.effect("sound", name=name)

    def popup(self, pos, text, kind):
        if self.cave and pos == self.player.pos:
            # In a cave, things pop up over you, not over the Mine on the world map
            self.effect("popup", cave_xy=self.cave.center, text=text, kind=kind)
        else:
            self.effect("popup", pos=pos, text=text, kind=kind)

    def tell(self, cards):
        """Queue up story cards for the graphics to show. {name} becomes your name."""
        name = self.player.name
        for title, words, picture in cards:
            self.story.append((title.replace("{name}", name), words.replace("{name}", name), picture))

    def take_effects(self):
        effects, self.effects = self.effects, []
        return effects

    # ----- map helpers --------------------------------------------------------

    def find_tile(self, letter, last=False):
        """Where the first letter (or the last one) is, reading left to right, top to bottom."""
        spots = [(r, c) for r, row in enumerate(self.map) for c, tile in enumerate(row) if tile == letter]
        if not spots:
            raise ValueError("The map needs a '%s' tile" % letter)
        return spots[-1] if last else spots[0]

    def swap_letters(self, old, new):
        """Change every `old` letter on the map into `new`. Returns the spots that changed."""
        spots = {(r, c) for r in range(self.rows) for c in range(self.cols) if self.map[r][c] == old}
        for r, c in spots:
            self.map[r][c] = new
        return spots

    def tile(self, pos):
        return self.map[pos[0]][pos[1]]

    def tile_name(self, pos):
        if self.tile(pos) == "L" and self.world == 2:
            return self.night_landmarks.get(pos, "Landmark")
        if self.tile(pos) == "L":
            name, top, left, bottom, right, landmark, words = self.land_at(pos)
            return landmark                         # a landmark is called by its own name, like "Windmill"
        if self.tile(pos) == "H" and pos in self.lodges:
            return "Hunter's Lodge"
        if self.tile(pos) == "W" and pos in self.river:
            return "Icy River"
        if self.world == 2 and self.tile(pos) == "H" and pos in self.beacons:
            return "Lit Beacon"
        return (NIGHTFALL_NAMES if self.world == 2 else TILE_NAMES)[self.tile(pos)]

    def land_at(self, pos):
        """Which land this square is in (its line in LANDS). Nightfall Hollow has no lands: None."""
        if self.world != 1:
            return None
        for land in LANDS:
            name, top, left, bottom, right = land[:5]
            if top <= pos[0] <= bottom and left <= pos[1] <= right:
                return land
        return None

    def land_name(self, pos):
        land = self.land_at(pos)
        return land[0] if land else None

    @property
    def here(self):
        return self.tile(self.player.pos)

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols

    def neighbors(self, pos, water=False, bridges=False):
        """The squares next to pos you can walk to - or swim to, if water=True.
        bridges=True counts broken bridges too (you can fix them and walk across)."""
        spots = [(pos[0] + dr, pos[1] + dc) for dr, dc in DIRECTIONS.values()]
        allowed = "W" if water else WALKABLE + ("=" if bridges else "")
        return [p for p in spots if self.in_bounds(p) and self.tile(p) in allowed]

    def reach(self, start, water=False):
        """Every square you can get to from start (on land, or on water if water=True)."""
        found, todo = {start}, [start]
        while todo:
            for spot in self.neighbors(todo.pop(), water, bridges=True):
                if spot not in found:
                    found.add(spot)
                    todo.append(spot)
        return found

    def big_lakes(self):
        """All the water squares in lakes that are big enough for Sea Serpents."""
        water = {(r, c) for r in range(self.rows) for c in range(self.cols) if self.map[r][c] == "W"}
        lakes = set()
        while water:
            lake = self.reach(water.pop(), water=True)
            water -= lake
            if len(lake) >= BIG_LAKE:
                lakes |= lake
        return lakes

    @property
    def sight_radius(self):
        """How far you can see: in Nightfall Hollow it grows with every beacon you light."""
        if self.world == 2:
            return LANTERN_RADIUS[min(len(self.beacons), len(LANTERN_RADIUS) - 1)]
        return SIGHT_RADIUS

    def in_light(self, pos):
        """True if pos is close to a lit beacon (shadow monsters are weaker there)."""
        return self.world == 2 and any(self.close_to(pos, beacon, BEACON_LIGHT) for beacon in self.beacons)

    def is_visible(self, pos):
        dr = pos[0] - self.player.pos[0]
        dc = pos[1] - self.player.pos[1]
        return dr * dr + dc * dc <= self.sight_radius * self.sight_radius + 1

    def reveal(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.is_visible((r, c)):
                    self.seen.add((r, c))
        for spot in self.landmarks:                 # landmarks are so big you can see them from far away
            if self.close_to(spot, self.player.pos, LANDMARK_SIGHT):
                self.seen.add(spot)

    def close_to(self, a, b, how_far):
        """True if a is within how_far squares of b (in a circle, like how far you can see)."""
        dr, dc = a[0] - b[0], a[1] - b[1]
        return dr * dr + dc * dc <= how_far * how_far + 1

    def spawn_monsters(self, counts, shadow=False):
        land = [(r, c) for r in range(self.rows) for c in range(self.cols)
                if self.map[r][c] in "FGMB" and distance((r, c), self.start) >= 5]
        lakes = sorted(spot for spot in self.big_lakes() if distance(spot, self.start) >= 5)
        self.rng.shuffle(land)
        self.rng.shuffle(lakes)
        monsters = []
        for kind, count in counts.items():
            spots = lakes if MONSTER_TYPES[kind]["special"] == "drowns" else land   # water monsters live in lakes
            far = MONSTER_START_DISTANCE.get(kind, 5) if self.world == 1 else 5   # strong monsters start far from home
            likes = MONSTER_LANDS.get(kind) if self.world == 1 else None          # the land it likes to live in
            for i in range(count):
                can_go = [s for s in reversed(spots) if distance(s, self.start) >= far]
                if likes and i < count * IN_THEIR_LAND:                           # this one starts in its own land
                    can_go = [s for s in can_go if self.land_name(s) == likes] or can_go
                spot = can_go[0] if can_go else None
                if spot:
                    spots.remove(spot)
                    monsters.append(Monster(kind, spot, shadow))
        return monsters

    def monster_at(self, pos):
        for monster in self.monsters:
            if monster.is_alive and monster.pos == pos:
                return monster
        return None

    @property
    def over(self):
        return self.won or not self.player.is_alive

    @property
    def portal_open(self):
        return all(q.completed for q in self.quests)

    # ----- the player's turn --------------------------------------------------

    def do(self, action):
        """Do one action. Returns True if it used up a turn.

        action: "up", "down", "left", "right", "wait", "act", "eat", "craft_pickaxe",
                "chop", "shoot", "build_house", "build_boat", "build_bow", "build_arrows"
        ("act" means: do the main thing for this tile - search, explore the cave or rest.)
        """
        if self.battle or self.cave or self.over:
            return False
        moved = False
        if action in DIRECTIONS:
            used = moved = self.move(action)
        elif action == "wait":
            used = True
        elif action == "act":
            used = self.tile_action()
        elif action == "eat":
            self.eat()
            used = False            # eating is a free action
        elif action == "craft_pickaxe":
            used = self.craft_pickaxe()
        elif action == "chop":
            used = self.chop_wood()
        elif action == "shoot":
            used = self.shoot()
        elif action in ("build_house", "build_boat", "build_bow", "build_arrows", "build_hilt"):
            used = self.build(action[6:])
        else:
            used = False
        if used:
            self.end_of_turn(moved)
        return used

    def move(self, direction):
        self.player.facing = direction
        dr, dc = DIRECTIONS[direction]
        new_pos = (self.player.pos[0] + dr, self.player.pos[1] + dc)
        if not self.in_bounds(new_pos):
            self.log("That's the edge of the world!")
            return False
        if self.tile(new_pos) == "X":
            if self.land_name(new_pos) == "Old Ruins":
                self.log("An old stone wall is in the way.")
            elif self.land_name(new_pos) == "Frosty Corner" and self.land_name(self.player.pos) != "Frosty Corner":
                self.log("The Frost Wall! It's much too icy to climb. Fix the old bridge in the north - or row across the lake!")
            else:
                self.log("A big rock is in the way. Go around it!")
            return False
        if self.tile(new_pos) == "=" and not self.fix_bridge(new_pos):
            return False
        if self.tile(new_pos) == "W":
            if not self.player.has_boat:
                self.log("You can't swim! Craft a boat (C) to cross the water.")
                return False
            if self.here != "W":
                self.log("You push your boat into the water and start rowing.")
            self.sound("splash")
        elif self.here == "W":
            self.log("You pull your boat up onto the shore.")
        self.player.pos = new_pos
        self.sound("step")
        self.reveal()
        self.slide(dr, dc)
        self.check_new_land()
        p = self.player
        if self.here == "H" and self.tile_name(p.pos) == "Hunter's Lodge":
            self.log("The Hunter's Lodge! It's warm inside, and monsters can't reach you here.", "good")
        elif self.here == "Q":
            self.pick_up_lantern()
        elif self.here == "N":
            self.log("Wren the ghost! Press SPACE to talk to her.", "quest")
        elif self.here == "D":
            self.log("A dark shrine. It's cold here, and nothing heals you. A Shadow Guardian lives on it!"
                     if self.monster_at(p.pos) else "The Guardian is gone. Press SPACE to light the beacon!", "quest")
        elif self.here == "H":
            self.log("The shrine glows softly. Monsters can't reach you here." if self.world == 2
                     else "You're safe at home. Monsters can't reach you here.", "good")
        elif self.here == "P":
            self.check_portal()
        elif self.here == "C":
            self.reach_castle()
        elif self.here == "L" and self.tile_name(p.pos) == "Watchtower" and not p.has_tower_key:
            self.log("The Watchtower! Its door is locked. Is the key hidden somewhere?", "quest")
        elif self.here == "L":
            self.log("The %s! Press SPACE to climb up and look around. Monsters can't reach you up there."
                     % self.tile_name(p.pos), "good")
        elif self.here == "S" and p.pos not in self.cleared_mines:
            self.log("An old mine door, hidden deep in the woods! Press SPACE to climb down.", "loot")
        elif self.here == "T":
            self.log("A treasure chest! Press SPACE to open it.", "loot")
        elif self.here == "+":
            self.log("A signpost. Press SPACE to read it.")
        elif self.here == "W" and p.pos in self.sunken_chests:
            self.log("Bubbles! Something shiny is down there. Press SPACE to dive for it.", "loot")
        self.first_time_tip()
        return True

    def slide(self, dr, dc):
        """On ice you keep sliding the same way, until you bump into something or the ice ends."""
        slid = False
        while self.here == "I":
            ahead = (self.player.pos[0] + dr, self.player.pos[1] + dc)
            if not self.in_bounds(ahead) or self.tile(ahead) not in WALKABLE or self.monster_at(ahead):
                break                                   # bump! (water, rock, a monster or the edge)
            self.player.pos = ahead
            self.reveal()
            slid = True
        if slid:
            self.sound("splash")

    def first_time_tip(self):
        """The first time you step onto something new, you're told how it works (FIRST_TIME_TIPS)."""
        if self.here in FIRST_TIME_TIPS and self.world == 1:
            name, words, kind = FIRST_TIME_TIPS[self.here]
            if name not in self.tips_seen:
                self.tips_seen.add(name)                # only tell you the first time
                self.log(words, kind)

    def check_new_land(self):
        """The first time you walk into a land, its name pops up and you hear what's special there."""
        land = self.land_at(self.player.pos)
        if land is None or land[0] in self.lands_seen:
            return
        name, top, left, bottom, right, landmark, words = land
        self.lands_seen.add(name)
        self.effect("land", text=name.upper(), sub="You found a new land!")
        self.log("%s: %s" % (name, words), "quest")
        self.sound("quest")

    def tile_action(self):
        if self.here == "F":
            return self.search_for_food()
        if self.here in "MS":
            return self.enter_cave()
        if self.here == "H":
            return self.rest()
        if self.here == "D":
            return self.light_beacon()
        if self.here == "N":
            return self.talk_to_wren()
        if self.here == "P":
            self.check_portal()
        if self.here == "C":
            self.reach_castle()
        if self.here == "G":
            self.log("Just open grass here. Look for berries in a forest - or craft a house (C)!")
        if self.here == "R":
            self.log("A quiet path. Nothing to find here - the trees and the water are off the path.")
        if self.here == "L":
            return self.climb_landmark()
        if self.here == "T":
            return self.open_map_chest()
        if self.here == "+":
            self.read_sign()
        if self.here == "W" and self.player.pos in self.sunken_chests:
            return self.dive()
        return False

    # ----- landmarks, signposts and treasure ----------------------------------------

    def climb_landmark(self):
        """Climb up a landmark and look around: the fog lifts, and Mines that still have a diamond sparkle.
        The Watchtower is locked (you need its key), but from the top you see the WHOLE map.
        From the Lighthouse you see a sparkle over EVERY Mine that still has a diamond."""
        here, p = self.player.pos, self.player
        name = self.tile_name(here)
        if name == "Watchtower" and not p.has_tower_key:
            self.log("The Watchtower door is locked tight. The key must be hidden somewhere... deep in the woods?", "quest")
            return False
        everywhere = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        around = [spot for spot in everywhere if self.close_to(spot, here, LOOKOUT_SIGHT)]
        if name == "Watchtower":
            self.seen.update(everywhere)
            self.log("You unlock the Watchtower with the old key and climb to the very top. You can see the WHOLE world!", "quest")
        else:
            self.seen.update(around)
            self.log("You climb up the %s and look all around." % name, "good")
        if name.endswith("Lighthouse"):
            self.lighthouse_lit = True
            around = everywhere
            self.log("The %s lamp shines over the whole land. Every Mine with a diamond in it sparkles!" % name, "quest")
        secret = set(self.secret_mines)              # the Secret Mine never sparkles: it's a secret!
        sparkles = [spot for spot in around if spot in self.diamond_mines and spot not in self.cleared_mines | secret]
        self.glints.update(sparkles)
        if name == "Queen Oak":
            for spot in secret - self.cleared_mines:
                self.log("From up in the Queen Oak you spot an old mine door, deep in the woods to the %s!"
                         % compass(here, spot), "loot")
        if sparkles:
            self.log("You spot a sparkle over %s - a diamond is still down there!"
                     % ("a Mine" if len(sparkles) == 1 else "%d Mines" % len(sparkles)), "loot")
            for spot in sparkles:
                self.effect("sparkle", pos=spot)
        else:
            self.log("No sparkles over the Mines around here.")
        self.effect("lookout", pos=here)
        self.sound("pickup")
        return True

    def read_sign(self):
        """A signpost points the way to the 3 nearest lands (to their landmarks)."""
        here = self.player.pos
        if self.world == 2:                         # Nightfall Hollow: where the landmarks are, and a hint about the chest
            ways = ["%s: %s" % (name, compass(here, spot)) for spot, name in sorted(self.night_landmarks.items(), key=lambda it: it[1])]
            hidden = [spot for spot in tiles_of(self.map, "T") if spot != self.plank_chest]
            if hidden:
                ways.append("a chest hides in the rocks to the %s" % compass(here, hidden[0]))
            self.log("The sign says...  " + ".   ".join(ways) + ". Climb a landmark (SPACE) to see far!", "quest")
            return
        my_land = self.land_name(here)
        others = sorted((distance(spot, here), spot) for spot in self.landmarks if self.land_name(spot) != my_land)
        ways = ["%s: %s" % (self.land_name(spot), compass(here, spot)) for _, spot in others[:3]]
        self.log("The sign says...  " + ".   ".join(ways) + ".", "quest")

    def open_map_chest(self):
        """Open a treasure chest on the map. What's inside depends on the land it's in."""
        p = self.player
        if self.world == 2 and p.pos != self.plank_chest:       # the hidden chest in the rocks: a diamond ring!
            self.log("You squeeze into the rocks and open the hidden chest!", "loot")
            self.popup(p.pos, self.map_prize("ring"), "loot")
            self.map[p.pos[0]][p.pos[1]] = "G"
            self.effect("tile", pos=p.pos)
            return True
        if self.world == 2:                         # the chest in the west of Nightfall Hollow holds the bridge planks
            p.has_planks = True
            self.log("You open the chest... old wooden PLANKS! They'd fix the broken Shadow Bridge.", "loot")
            self.popup(p.pos, "+planks", "loot")
            self.sound("pickup")
            self.map[p.pos[0]][p.pos[1]] = "G"
            self.effect("tile", pos=p.pos)
            return True
        prizes = MAP_CHEST_PRIZES.get(self.land_name(p.pos), ["gold"])
        self.log("You open the treasure chest!", "loot")
        words = [self.map_prize(prize) for prize in prizes]
        self.popup(p.pos, "  ".join(words), "loot")
        self.map[p.pos[0]][p.pos[1]] = "G"          # the chest is empty now: just grass is left
        self.effect("tile", pos=p.pos)
        return True

    def map_prize(self, prize):
        """Give one prize from a chest on the map. Returns the words to pop up."""
        p = self.player
        if prize == "key":
            p.has_tower_key = True
            self.sound("pickup")
            self.log("An old iron KEY! It has a little tower on it... the Watchtower in the Old Ruins!", "loot")
            return "+key"
        if prize == "bow" and not p.has_bow:
            p.has_bow = True
            self.sound("pickup")
            self.log("A BOW! Press F to shoot it.", "loot")
            return "+bow"
        if prize == "ring":
            return self.give_ring()
        if prize == "bow":                          # you already have a bow: arrows instead
            prize = "arrows"
        return self.give_loot(prize, MAP_CHEST_GOLD)    # food, arrows, armor... or gold if your pack is full

    def fix_bridge(self, pos):
        """Walk onto the broken bridge carrying enough wood, and you fix it. Returns True if you can walk on."""
        p = self.player
        if self.world == 2:                         # the Shadow Bridge: the planks from the chest in the west fix it
            if not p.has_planks:
                self.log("The Shadow Bridge is broken! You need old planks to fix it. Is there a chest on this side "
                         "of the river?", "quest")
                return False
            self.map[pos[0]][pos[1]] = "#"
            self.effect("tile", pos=pos)
            self.log("Bang, bang, bang! You nail the old planks down. The Shadow Bridge holds!", "good")
            self.sound("pickup")
            return True
        if p.wood < BRIDGE_WOOD:
            self.log("The old bridge is broken! Bring %d wood to fix it (you have %d)." % (BRIDGE_WOOD, p.wood))
            return False
        p.wood -= BRIDGE_WOOD
        self.map[pos[0]][pos[1]] = "#"
        self.effect("tile", pos=pos)
        self.log("Bang, bang, bang! You fix the old bridge with %d wood. Now you can cross the Icy River!"
                 % BRIDGE_WOOD, "good")
        self.popup(pos, "-%d wood" % BRIDGE_WOOD, "good")
        self.sound("pickup")
        return True

    def dive(self):
        """Dive down from your boat to the sunken chest under the bubbles."""
        pos = self.player.pos
        self.sunken_chests.discard(pos)
        self.log("SPLASH! You dive down and find a sunken chest at the bottom of the lake!", "loot")
        self.popup(pos, self.map_prize("ring"), "loot")
        self.sound("splash")
        return True

    def wood_left(self, pos):
        """How much wood is left in the tree at pos."""
        return self.tree_wood.get(pos, TREE_WOOD)

    def chop_wood(self):
        p = self.player
        if self.here != "F":
            self.log("You need to be in the forest to chop wood.")
            return False
        if p.wood >= MAX_WOOD:
            self.log("You can't carry any more wood.")
            return False
        left = self.wood_left(p.pos)
        got = min(MAX_WOOD - p.wood, self.rng.randint(*WOOD_PER_CHOP), left)
        p.wood += got
        self.tree_wood[p.pos] = left - got
        self.popup(p.pos, "+%d wood" % got, "loot")
        self.sound("chop")
        if left - got > 0:
            self.log("Chop, chop! You get %d wood. This tree has %d left." % (got, left - got), "loot")
            return True
        # TIMBER! That was the last of the wood: the tree falls and an open field is left
        del self.tree_wood[p.pos]
        self.map[p.pos[0]][p.pos[1]] = "G"
        self.effect("tile", pos=p.pos)              # tell the graphics to paint the field
        self.effect("timber", pos=p.pos)
        self.log("TIMBER! You get %d wood, and the tree falls down. Only open grass is left." % got, "loot")
        return True

    def build_problem(self, kind):
        """Why you can't build a "house", "boat", "bow" or "arrows" right now - or None if you can."""
        p = self.player
        if self.cave and kind in ("house", "boat"):
            return "You can't build that down here in a cave."
        if kind == "house":
            if self.here not in "FG":
                return "Houses go on a Forest or Field square."
            if p.wood < HOUSE_COST:
                return "You need %d wood (you have %d)." % (HOUSE_COST, p.wood)
        elif kind == "hilt":
            if self.world != 2:
                return "You can only carve this in Nightfall Hollow."
            if p.has_hilt:
                return "You already carved the Hilt."
            if p.wood < HILT_WOOD:
                return "You need %d dead wood (you have %d)." % (HILT_WOOD, p.wood)
        elif kind == "bow":
            if p.has_bow:
                return "You already have a bow."
            if p.wood < BOW_COST:
                return "You need %d wood (you have %d)." % (BOW_COST, p.wood)
        elif kind == "arrows":
            if p.arrows >= p.max_arrows:
                return "You can't carry any more arrows."
            if p.wood < ARROW_COST:
                return "You need %d wood (you have %d)." % (ARROW_COST, p.wood)
        else:
            if self.world == 2:
                return "The black water is too stormy to row across."
            if p.has_boat:
                return "You already have a boat."
            if not self.neighbors(p.pos, water=True):
                return "Stand next to the water to build a boat."
            if p.wood < BOAT_COST:
                return "You need %d wood (you have %d)." % (BOAT_COST, p.wood)
        return None

    def shoot(self):
        """Shoot an arrow the way you last walked. It hits the first monster it reaches."""
        p = self.player
        if not p.has_bow:
            self.log("You need a bow. Make one out of wood (press C).")
            return False
        if p.arrows <= 0:
            self.log("You're out of arrows! Make more out of wood (press C).")
            return False
        p.arrows -= 1
        dr, dc = DIRECTIONS[p.facing]
        spot = end = p.pos
        target = None
        for _ in range(ARROW_RANGE):
            spot = (spot[0] + dr, spot[1] + dc)
            if not self.in_bounds(spot):
                break
            end = spot
            target = self.monster_at(spot)
            if target:
                break
        self.effect("arrow", start=p.pos, end=end, fire=p.fire_arrows)
        self.sound("shoot")
        if not target:
            self.log("Your arrow flies off and misses.")
            return True
        damage = self.arrow_damage(target.special)
        target.health = max(0, target.health - damage)
        self.popup(target.pos, "-%d" % damage, "bad")
        if target.is_alive:
            self.log("Your %sarrow hits the %s for %d damage!" % ("fire " if p.fire_arrows else "", target.kind, damage), "good")
        else:
            self.log("Your %sarrow defeats the %s!" % ("fire " if p.fire_arrows else "", target.kind), "quest")
            self.sound("victory")
            self.monster_gone(target, give_xp=True)
        return True

    def arrow_damage(self, special=None):
        p = self.player
        damage = self.rng.randint(*ARROW_DAMAGE) + p.strength_bonus + p.power("Sharpshooter") * SHARP_DAMAGE
        if p.fire_arrows:
            damage += FIRE_ARROW_BONUS
        return max(1, damage - 1) if special == "tough" else damage

    def build(self, kind):
        problem = self.build_problem(kind)
        if problem:
            self.log(problem)
            return False
        p = self.player
        if kind == "house":
            p.wood -= HOUSE_COST
            self.map[p.pos[0]][p.pos[1]] = "H"
            self.tree_wood.pop(p.pos, None)       # a house replaces the tree
            self.effect("tile", pos=p.pos)        # tell the graphics to paint the new house
            self.log("You build a cozy little house! Monsters can't get you in here.", "good")
        elif kind == "hilt":
            p.wood -= HILT_WOOD
            p.has_hilt = True
            self.log("You carve the HILT of Sunfang out of dead wood!", "good")
        elif kind == "bow":
            p.wood -= BOW_COST
            p.has_bow = True
            self.log("You carve a bow! Press F to shoot - make arrows with C.", "good")
        elif kind == "arrows":
            p.wood -= ARROW_COST
            p.arrows = min(p.max_arrows, p.arrows + ARROWS_PER_BUNDLE)
            self.log("You make a bundle of arrows. You have %d now." % p.arrows, "good")
        else:
            p.wood -= BOAT_COST
            p.has_boat = True
            self.log("You build a boat! Walk into the water to row across.", "good")
        self.popup(p.pos, "+" + kind, "loot")
        self.sound("craft")
        return True

    def eat(self):
        p = self.player
        if p.food == 0:
            self.log("You have no food! Search the forest for berries.")
        elif p.health == p.max_health:
            self.log("You're already at full health - save it for later.")
        else:
            p.food -= 1
            healed = p.heal(FOOD_HEAL)
            self.log("You eat some berries and recover %d health." % healed, "good")
            self.popup(p.pos, "+%d" % healed, "good")
            self.sound("eat")

    def search_for_food(self):
        p = self.player
        if p.food >= p.max_food:
            self.log("Your pack is already full of food.")
            return False
        if self.rng.random() < (FORAGER_BERRY_CHANCE if p.power("Forager") else BERRY_CHANCE):
            self.player.food += 1
            self.log("You find some wild berries!", "loot")
            self.popup(self.player.pos, "+1 food", "loot")
            self.sound("pickup")
        else:
            self.log("You searched for a while but didn't find anything.")
        return True

    def pickaxe_problem(self):
        """Why you can't make a pickaxe right now - or None if you can."""
        p = self.player
        if p.pickaxe:
            return "You already have a pickaxe."
        if self.cave:
            if p.wood < PICKAXE_CAVE_WOOD:
                return "In a cave a pickaxe needs %d wood (you have %d)." % (PICKAXE_CAVE_WOOD, p.wood)
        elif self.here != "F":
            return "Make it in the forest (free), or with %d wood in a cave." % PICKAXE_CAVE_WOOD
        return None

    def craft_pickaxe(self):
        problem = self.pickaxe_problem()
        if problem:
            self.log(problem)
            return False
        if self.cave:
            self.player.wood -= PICKAXE_CAVE_WOOD
        self.player.pickaxe = Tool("Pickaxe", PICKAXE_DURABILITY)
        self.log("You crafted a new pickaxe!", "loot")
        self.popup(self.player.pos, "+pickaxe", "loot")
        self.sound("craft")
        return True

    def forge_problem(self):
        """Returns a reason you can't forge a sword right now, or None if you can."""
        if self.battle or self.over:
            return "Not now!"
        if self.cave:                                   # you can forge in a cave too
            if not self.cave.you.on_ground:
                return "Stand on solid ground to forge a sword."
        elif self.here != "F":
            return "You need to be in the forest (or a cave) to forge a sword."
        if len(self.player.swords) >= MAX_SWORDS:
            return "You can only carry %d swords." % MAX_SWORDS
        return None

    def finish_forge(self, strikes):
        """Called by the graphics after the forging mini-game, with the 3 strikes ("perfect", "good" or "miss").
        Every forge makes a sword - how good it is depends on the strikes."""
        quality = sword_quality(strikes)
        self.player.swords.append(make_sword(quality))
        if quality == "great":
            self.log("PERFECT! You forged a GREAT sword: +%d damage, %d hits!" % (GREAT_SWORD_BONUS, GREAT_SWORD_DURABILITY),
                     "loot")
            self.popup(self.player.pos, "+GREAT sword", "loot")
            self.sound("diamond")
        elif quality == "cracked":
            self.log("CRACK! The blade cracked. It will only last %d hits." % CRACKED_SWORD_DURABILITY, "bad")
            self.popup(self.player.pos, "+cracked sword", "bad")
            self.sound("crack")
        else:
            self.log("You forged a new sword! (%d hits)" % SWORD_DURABILITY, "loot")
            self.popup(self.player.pos, "+sword", "loot")
            self.sound("craft")
        if not self.cave:
            self.end_of_turn(False)             # on the world map, forging takes a turn

    # ----- caves ---------------------------------------------------------------

    def enter_cave(self):
        pos = self.player.pos
        if pos in self.cleared_mines:
            self.log("This mine is empty now - you already found its diamond.")
            return False
        self.cave = caves.Cave(self, pos, self.cave_text(pos), self.cave_changes.setdefault(pos, {}))
        if pos in self.empty_mines:
            self.log("You climb back down. There's no diamond in this cave, but you can still explore it.")
        else:
            self.log("You climb down into the dark cave. Is there a diamond down here? Explore and find the EXIT!")
        self.sound("cave")
        return False            # the turn ends when you come back out

    def cave_text(self, pos):
        """The cave under a Mine (or under the Secret Mine)."""
        return self.cave_plan.get(pos) or self.secret_mines[pos]

    def update_cave(self, dt, controls):
        """Called by the graphics every frame while you're in a cave."""
        if not self.cave or self.over:
            return
        cave = self.cave
        cave.update(dt, controls)
        if self.cave is cave and cave.result:     # (knocked out, you're already back outside)
            self.leave_cave()

    def leave_cave(self):
        cave, self.cave = self.cave, None
        if cave.is_castle:
            if cave.result == "exit":
                self.reach_throne()
                return
            self.log("You slip back out through the castle gate.")
        elif cave.result == "exit":
            self.log("You climb out of the cave and back into the daylight.", "good")
            if cave.mine_pos not in self.exited_mines:     # XP for the EXIT door, once for every cave
                self.exited_mines.add(cave.mine_pos)
                self.log("You found the way through! +%d XP" % EXIT_XP, "loot")
                self.popup(self.player.pos, "+%d XP" % EXIT_XP, "loot")
                self.gain_xp(EXIT_XP, quiet=True)
            if cave.mine_pos not in self.diamond_mines and cave.mine_pos not in self.empty_mines:
                self.empty_mines.add(cave.mine_pos)        # a grey X on the map, so you don't look in it twice
                self.log("No diamond in that cave... try another Mine!")
        else:
            self.log("You head back out of the cave the way you came in.")
        self.sound("door")
        self.end_of_turn(False)

    def new_monster(self, kind, shadow=False):
        """A monster for a cave (caves.py keeps track of where it is).
        In Nightfall Hollow (and in the Shadow King's castle) it's a shadow monster."""
        return Monster(kind, None, shadow=shadow or self.world == 2)

    def give_loot(self, kind, xp):
        """You opened a treasure chest! Returns the words to pop up over it."""
        p = self.player
        self.sound("pickup")
        if kind == "food" and p.food < p.max_food:
            p.food += 1
            self.log("The chest is full of berries! +1 food", "loot")
            return "+1 food"
        if kind == "sword" and len(p.swords) < MAX_SWORDS:
            if self.rng.random() < GREAT_CHEST_CHANCE:      # about 1 in 3 is a Great sword
                p.swords.append(make_sword("great"))
                self.log("A GREAT sword! It glows gold: +%d damage, %d hits." % (GREAT_SWORD_BONUS, GREAT_SWORD_DURABILITY),
                         "loot")
                return "+GREAT sword"
            p.swords.append(make_sword())
            self.log("A shiny new sword!", "loot")
            return "+sword"
        if kind == "arrows" and p.arrows < p.max_arrows:
            p.arrows = min(p.max_arrows, p.arrows + ARROWS_PER_BUNDLE)
            self.log("A bundle of arrows! You have %d now." % p.arrows, "loot")
            return "+%d arrows" % ARROWS_PER_BUNDLE
        if kind == "pickaxe" and not p.pickaxe:         # pickaxes never break, so usually it's gold instead
            p.pickaxe = Tool("Pickaxe", PICKAXE_DURABILITY)
            self.log("A brand-new pickaxe!", "loot")
            return "+pickaxe"
        if kind == "armor" and p.armor < p.max_armor:
            new = not p.has_armor
            p.put_on_armor()
            self.log("You found ARMOR! It soaks up %d damage before it breaks." % p.max_armor if new
                     else "Shiny! Your armor is as good as new.", "loot")
            return "+armor"
        # Anything else (or your pack is already full): gold coins worth some XP
        self.log("Gold coins! They're worth %d XP." % xp, "loot")
        self.gain_xp(xp)
        return "+%d XP" % xp

    def check_chipped_swords(self):
        """A sword that just got down to its last few hits chips: you hear it, and a message tells you."""
        for sword in self.player.swords:
            if sword.chipped:
                sword.chipped = False
                self.log("Your sword is chipped! Only %d hits left." % sword.durability, "bad")
                self.sound("chip")

    def give_ring(self):
        """A diamond ring! It fits onto your sword and makes your next few hits stronger."""
        p = self.player
        p.ring_hits = min(MAX_RING_HITS, p.ring_hits + RING_HITS)
        self.log("A DIAMOND RING! It fits onto your sword: your next %d hits do +%d damage."
                 % (p.ring_hits, RING_BONUS), "loot")
        self.sound("diamond")
        return "+diamond ring"

    def ring_power(self):
        """The extra damage from a diamond ring on your sword. It wears out a little with every hit."""
        p = self.player
        if p.ring_hits <= 0 or not (p.swords or p.sunfang):
            return 0
        p.ring_hits -= 1
        if p.ring_hits == 0:
            self.log("Your diamond ring's power is all used up.")
        return RING_BONUS

    def found_diamond(self):
        p = self.player
        p.diamonds += 1
        self.log("You found a DIAMOND! +%d XP" % DIAMOND_XP, "loot")
        self.popup(p.pos, "+1 diamond", "loot")
        self.sound("diamond")
        self.gain_xp(DIAMOND_XP, quiet=True)
        if self.diamond_quest.advance():
            self.log("Quest complete: %s!" % self.diamond_quest.description, "quest")
            self.sound("quest")
            self.quest_xp()
            self.after_quest()

    def rest(self):
        p = self.player
        if p.health == p.max_health:
            self.log("You're not tired right now.")
            return False
        healed = p.heal(REST_HEAL)
        self.log(("You rest by the glowing shrine and recover %d health." if self.world == 2
                  else "You take a nap at home and recover %d health.") % healed, "good")
        self.popup(p.pos, "+%d" % healed, "good")
        self.sound("heal")
        return True

    def check_portal(self):
        if self.portal_open:
            self.log("The Portal swirls open and pulls you through!", "quest")
            self.go_to_nightfall()
        else:
            needs = [q.description.lower() for q in self.quests if not q.completed]
            self.log("The Portal flickers but stays closed. You still need to " +
                     " and ".join(needs) + ".", "quest")

    def go_to_nightfall(self):
        """Through the Portal into the Shadow King's world. There's no way back!"""
        p = self.player
        self.world = 2
        self.map = parse_map(NIGHTFALL_MAP)
        self.rows, self.cols = len(self.map), len(self.map[0])
        self.start = self.find_tile("H")
        self.castle = self.find_tile("C")
        self.portal = None
        p.pos = self.start
        self.seen = set()
        self.cave_plan, self.cleared_mines, self.cave_changes = {}, set(), {}
        self.exited_mines = set()
        self.diamond_mines, self.empty_mines, self.shard_mines = set(), set(), set()
        self.sunken_chests, self.glints = set(), set()
        self.river, self.lodges, self.secret_mines = set(), set(), {}
        self.tree_wood = {}
        self.mainland = self.reach(self.start)
        # The Portal swallows the diamonds you brought: you need fresh ones, found here
        swallowed, p.diamonds = p.diamonds, 0
        p.sun_shards, p.has_hilt, p.has_planks, p.lanterns = 0, False, False, 0
        self.wren_quest, self.wren_thanked = None, False
        self.beacons = set()
        self.moon, self.wisp, self.wisp_hops = 0, None, 0
        # The landmarks (west to east: the Dead Giant Tree, then the Black Lighthouse) and the chest with the planks
        self.landmarks = sorted(tiles_of(self.map, "L"), key=lambda spot: spot[1])
        self.night_landmarks = dict(zip(self.landmarks, NIGHT_LANDMARKS))
        self.plank_chest = min(tiles_of(self.map, "T"), key=lambda spot: spot[1])
        # Every Mine is a dark shadow cave with a diamond and a Sun Shard. The nearest Mine to the start gets
        # the easiest cave, the farthest gets the hardest.
        mines = sorted(tiles_of(self.map, "M"), key=lambda mine: (distance(mine, self.start), mine))
        self.cave_plan = {mine: caves.SHADOW_CAVES[min(i, len(caves.SHADOW_CAVES) - 1)] for i, mine in enumerate(mines)}
        self.diamond_mines, self.shard_mines = set(mines), set(mines)
        self.monsters = self.spawn_monsters(NIGHTFALL_MONSTER_COUNTS, shadow=True)
        for shrine in tiles_of(self.map, "D"):          # a Shadow Guardian sits on every dark shrine
            self.monsters.append(Monster("Guardian", shrine, shadow=True))
        bridge = min(tiles_of(self.map, "="), key=lambda spot: spot[1])
        self.monsters.append(Monster("Warden", (bridge[0], bridge[1] - 1), shadow=True))    # it guards the bridge
        if swallowed:
            self.log("The Portal swallowed your %d diamond%s! You'll have to find new ones here."
                     % (swallowed, "" if swallowed == 1 else "s"), "bad")
        self.castle_quest = Quest("Find the castle", 1)
        self.quests = [self.castle_quest]
        self.reveal()
        self.log("Welcome to Nightfall Hollow. Find the Shadow King's castle!", "quest")
        p.fire_arrows = True                        # the Portal's magic sets your arrows alight
        self.log("Your arrows burst into flame! Fire arrows hit +%d harder." % FIRE_ARROW_BONUS, "good")
        self.log("A black river cuts the land in two. Light the 3 dark shrines and find the parts of Sunfang!", "quest")
        self.sound("portal")
        self.effect("new_world")
        self.tell(story.THROUGH_THE_PORTAL)

    def reach_castle(self):
        if self.won or self.forging:
            return
        p = self.player
        if not p.sunfang:
            if len(self.beacons) < BEACONS_NEEDED:
                self.log("The castle gate forge is cold and asleep. Light all %d dark shrines to wake it! (%d lit)"
                         % (BEACONS_NEEDED, len(self.beacons)), "quest")
                return
            missing = self.missing_parts()
            if missing:
                self.log("The forge is awake! But Sunfang still needs: %s." % ", ".join(missing), "quest")
                return
            self.forging = True                 # the graphics play the forging scene, then call finish_sunfang()
            self.log("Your diamonds are glowing...", "quest")
            self.sound("portal")
            self.tell(story.FORGE_SUNFANG)
            return
        self.open_castle()

    def missing_parts(self):
        """The parts of Sunfang you still need: the Blade, the Hilt and the Sun Gem."""
        p = self.player
        missing = []
        if p.diamonds < SUNFANG_DIAMONDS:
            missing.append("the Blade (%d more diamond%s)" % (SUNFANG_DIAMONDS - p.diamonds,
                                                             "" if SUNFANG_DIAMONDS - p.diamonds == 1 else "s"))
        if not p.has_hilt:
            missing.append("the Hilt (craft it from %d wood)" % HILT_WOOD)
        if p.sun_shards < SUN_SHARDS_NEEDED:
            missing.append("the Sun Gem (%d more Sun Shard%s)" % (SUN_SHARDS_NEEDED - p.sun_shards,
                                                                 "" if SUN_SHARDS_NEEDED - p.sun_shards == 1 else "s"))
        return missing

    def light_beacon(self):
        """SPACE on a dark shrine whose Guardian is gone: the beacon lights up, and the land gets brighter."""
        p = self.player
        if self.monster_at(p.pos):
            self.log("The Shadow Guardian won't let you!", "bad")
            return False
        self.map[p.pos[0]][p.pos[1]] = "H"              # it's a glowing shrine now: it heals you, and it's safe
        self.beacons.add(p.pos)
        self.effect("tile", pos=p.pos)
        self.effect("beacon", pos=p.pos)
        around = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.close_to((r, c), p.pos, LOOKOUT_SIGHT)]
        self.seen.update(around)                        # the light shows you the land around it
        self.reveal()                                   # (and your lantern grew: you see farther now)
        self.sound("sunfang")
        if len(self.beacons) >= BEACONS_NEEDED:
            self.log("The last beacon blazes! Far away, the forge at the castle gate wakes up!", "quest")
        else:
            self.log("The beacon blazes! Nightfall Hollow is a little brighter, and your lantern grows. (%d of %d lit)"
                     % (len(self.beacons), BEACONS_NEEDED), "quest")
        self.quest_xp()
        return True

    def pick_up_lantern(self):
        """Walk onto one of Wren's lost lanterns."""
        p = self.player
        p.lanterns += 1
        self.map[p.pos[0]][p.pos[1]] = "G"
        self.effect("tile", pos=p.pos)
        self.popup(p.pos, "+lantern", "loot")
        self.sound("pickup")
        self.log("A lost lantern, still glowing! (%d of %d)" % (p.lanterns, WREN_LANTERNS), "loot")
        if self.wren_quest and self.wren_quest.advance():
            self.log("That's all of Wren's lanterns! Take them back to her.", "quest")
            self.sound("quest")

    def talk_to_wren(self):
        """SPACE next to Wren: she asks for her lanterns, then thanks you with armor and a map hint."""
        p = self.player
        if self.wren_thanked:
            self.log("Wren: \"Thank you, %s! Light the shrines and chase away the dark!\"" % p.name, "good")
            return False
        if self.wren_quest is None:
            self.wren_quest = Quest("Find Wren's lanterns", WREN_LANTERNS)
            self.wren_quest.progress = min(p.lanterns, WREN_LANTERNS)
            self.quests.append(self.wren_quest)
            self.log("Wren: \"Oh! Someone who isn't a monster! I lost my %d lanterns in the dark. Will you find them? "
                     "They glow, so look in the far corners.\"" % WREN_LANTERNS, "quest")
            self.sound("quest")
            return False
        if not self.wren_quest.completed:
            self.log("Wren: \"%d of my lanterns are still out there. Look in the far corners!\""
                     % (WREN_LANTERNS - self.wren_quest.progress), "quest")
            return False
        self.wren_thanked = True
        p.lanterns = 0
        p.put_on_armor()
        for spot in tiles_of(self.map, "M") + tiles_of(self.map, "D") + tiles_of(self.map, "H"):
            self.seen.update((spot[0] + dr, spot[1] + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                             if self.in_bounds((spot[0] + dr, spot[1] + dc)))
        self.log("Wren: \"My lanterns! Thank you! Take this armor, and I'll show you where the Mines and shrines are.\"",
                 "quest")
        self.popup(p.pos, "+armor", "loot")
        self.sound("quest")
        self.quest_xp()
        return True

    def found_sun_shard(self):
        p = self.player
        p.sun_shards += 1
        self.log("You found a SUN SHARD! (%d of %d)" % (p.sun_shards, SUN_SHARDS_NEEDED), "loot")
        self.popup(p.pos, "+1 sun shard", "loot")
        self.sound("diamond")
        self.gain_xp(DIAMOND_XP, quiet=True)
        if p.sun_shards == SUN_SHARDS_NEEDED:
            self.log("Three Sun Shards shine together: you have the SUN GEM!", "quest")

    def finish_sunfang(self, perfect):
        """Called by the graphics when the forging scene is over."""
        p = self.player
        p.diamonds -= SUNFANG_DIAMONDS
        p.sun_shards, p.has_hilt = 0, False
        p.sunfang = True
        p.sunfang_perfect = perfect
        self.forging = False
        self.log("PERFECT FORGE! Sunfang glows extra bright (+%d damage)." % PERFECT_BONUS if perfect
                 else "You forged Sunfang! It never breaks.", "quest")
        self.tell(story.SUNFANG_DONE)
        self.open_castle()

    def open_castle(self):
        """In through the castle gate! (You can walk back out of it on the left.)"""
        if self.castle_quest.advance():         # the first time
            self.throne_quest = Quest("Reach the throne room", 1)
            self.quests.append(self.throne_quest)
            self.log("The castle gates creak open... The door ahead is locked: find its key!", "quest")
            self.quest_xp()
        else:
            self.log("You go back into the castle.")
        self.enter_castle_level(0)              # you always come in at level 1 (doors you opened stay open)

    def enter_castle_level(self, level, back=False):
        """Into one of the castle's 5 levels. back=True: you came back from the level after it."""
        changes = self.cave_changes.setdefault(("castle", level), {})   # every level remembers what you changed
        self.cave = castle.Castle(self, self.castle, changes, level)
        if back:
            self.cave.stand_by_door()           # back where you went through its door
        name = castle.CASTLE_LEVELS[level][0]
        self.effect("castle_level", text="LEVEL %d" % (level + 1), sub=name)
        self.sound("door")
        if level not in self.castle_levels_seen:        # the first time you get to a level
            self.castle_levels_seen.add(level)
            self.log("Castle level %d: %s" % (level + 1, name), "quest")
            self.tell(story.CASTLE_LEVEL_CARDS[level])

    def castle_knockout(self):
        """Beaten in the castle? You lose a life, and the Shadow King's magic throws you back to the start
        of this level (not out of the castle: the doors you opened and the guards you beat stay that way)."""
        p = self.player
        p.health = p.max_health
        self.knockouts += 1
        last = self.lose_life()
        self.cave.back_to_start()
        self.sound("lose")
        lives = "%d %s left." % (p.lives, "life" if p.lives == 1 else "lives")
        if last:
            lives = "Out of lives - here are %d new ones!" % p.lives
        if self.cave.is_throne_room:            # beaten by the Shadow King: back to the door, and he's healed too
            self.king_fights += 1
            self.log("Everything goes dark... You wake up by the door with full health. But the Shadow King "
                     "has all his health back too. Try again! %s" % lives, "bad")
            self.effect("knockout", sub="Back to the door. The Shadow King is healed too! " + lives)
            return
        self.log("Everything goes dark... You wake up at the start of this level with full health. Try again! "
                 + lives, "bad")
        self.effect("knockout", sub="Back to the start of this level. " + lives)
        if self.knockouts == 1:
            self.tell(story.KNOCKED_OUT)

    def reach_throne(self):
        """Through the great door at the end of level 5, into the throne room!"""
        if self.throne_quest.advance():         # the first time
            self.log("You opened the door of the throne room! (Light shards: %d of %d)"
                     % (self.player.light_shards, len(castle.CASTLE_LEVELS)), "quest")
            self.quest_xp()
            self.king_quest = Quest("Defeat the Shadow King", 1)
            self.quests.append(self.king_quest)
        self.cave = throne.ThroneRoom(self, self.castle)
        self.king_fights += 1
        self.log("BANG! The great door slams shut behind you. The Shadow King rises from his throne...", "bad")
        self.log("When his sword glows, get away! Jump over his fireballs. Hurt? Climb up to the healing nook.",
                 "quest")
        self.sound("boom")
        self.effect("door_slam")
        self.effect("castle_level", text="THE SHADOW KING", sub="The door slams shut behind you!")

    def beat_the_king(self):
        """You beat the Shadow King! The light comes back, and the story ends."""
        self.king_quest.advance()
        self.log("You defeated the Shadow King! The light is coming back!", "quest")
        self.quest_xp()
        self.won = True
        self.sound("win")
        self.tell(story.THE_LIGHT_COMES_BACK)

    def sunfang_damage(self, special=None):
        p = self.player
        damage = self.rng.randint(*SUNFANG_DAMAGE) + p.strength_bonus + (PERFECT_BONUS if p.sunfang_perfect else 0)
        return max(1, damage - 1) if special == "tough" else damage

    def quest_xp(self):
        """Every quest you finish is worth QUEST_XP."""
        self.battle_line("+%d XP for finishing a quest!" % QUEST_XP, "loot")
        self.gain_xp(QUEST_XP, quiet=True)

    def after_quest(self):
        if self.portal_open:
            self.log("All quests done! The Portal is open - go find it!", "quest")

    # ----- the world's turn ---------------------------------------------------

    def end_of_turn(self, moved):
        if self.won:
            return
        self.turn += 1
        if moved:
            self.random_event()
        self.night_events(moved)
        if not self.player.is_alive:
            return
        if self.here == "H" and self.player.heal(HOUSE_HEAL):
            self.popup(self.player.pos, "+%d" % HOUSE_HEAL, "good")     # houses heal you a little every turn
        self.move_monsters()
        self.archers_shoot()
        self.steam_vents()
        if not self.player.is_alive:
            return
        monster = self.monster_at(self.player.pos)
        if monster and self.here not in SAFE and self.player.is_alive:
            self.start_battle(monster)

    def night_events(self, moved):
        """Nightfall Hollow: every MOONRISE_EVERY turns the moon rises for a while. Shadows wander farther,
        but a friendly wisp appears: follow it and it leaves a gift. Shrines and beacons stay safe."""
        if self.world != 2:
            return
        if self.moon:
            self.moon -= 1
            if self.moon == 0:
                self.wisp = None
                self.log("The moon sets. The land is calm again.", "info")
        elif self.turn % MOONRISE_EVERY == 0:
            self.moon = MOONRISE_TURNS
            self.wisp_hops = 0
            self.wisp = self.wisp_spot(self.player.pos)
            self.sound("quest")
            self.log("The moon rises! Shadows wander farther. Stay near a shrine or a beacon, "
                     "or follow the little wisp!" if self.wisp else
                     "The moon rises! Shadows wander farther. Stay near a shrine or a beacon!", "quest")
        if self.wisp and self.player.pos == self.wisp and moved:
            self.follow_wisp()

    def wisp_spot(self, near):
        """A free grass square 3 or 4 steps from `near` that you can walk to (or None)."""
        walkable = self.reach(near)
        spots = [pos for pos in sorted(walkable) if 3 <= abs(pos[0] - near[0]) + abs(pos[1] - near[1]) <= 4
                 and self.tile(pos) == "G" and not self.monster_at(pos)]
        return self.rng.choice(spots) if spots else None

    def follow_wisp(self):
        """You caught up with the wisp: it hops on, and after WISP_HOPS hops it leaves a gift."""
        p = self.player
        self.wisp_hops += 1
        if self.wisp_hops < WISP_HOPS:
            self.wisp = self.wisp_spot(p.pos)
            self.sound("pickup")
            self.popup(p.pos, "follow!", "loot")
            if self.wisp is None:
                self.moon = min(self.moon, 1)
            return
        self.wisp = None
        self.log("The wisp twinkles and leaves a gift in the moonlight!", "loot")
        words = self.give_loot(self.rng.choice(WISP_GIFTS), MAP_CHEST_GOLD)
        self.popup(p.pos, words, "loot")

    def chase_distance(self):
        """How far away shadow monsters notice you: farther under the moon, but not in the light of a beacon."""
        under_moon = self.moon and not self.in_light(self.player.pos)
        return CHASE_DISTANCE + (MOON_CHASE if under_moon else 0)

    def vent_puffing(self, turn=None):
        """True on the turns the steam vents puff (every VENT_EVERY turns)."""
        return (self.turn if turn is None else turn) % VENT_EVERY == 0

    def steam_vents(self):
        """Standing on a steam vent when it puffs? Ouch!"""
        if self.here == "V" and self.vent_puffing():
            self.log("WHOOSH! Hot steam puffs out of the vent!", "bad")
            self.hurt_player(VENT_DAMAGE)

    def hurt_player(self, amount):
        p = self.player
        had_armor = p.has_armor
        p.hurt(amount)
        self.popup(p.pos, "-%d" % amount, "bad")
        if had_armor and not p.has_armor:
            self.log("CRACK! Your armor broke.", "bad")
            self.sound("crack")
        self.effect("shake", amount=amount)
        self.sound("hurt")
        if not p.is_alive and self.cave and self.cave.is_castle:
            self.castle_knockout()              # in the castle: lose a life, start this level again
        elif not p.is_alive:
            self.knocked_out()

    def lose_life(self):
        """Take away one life. Out of lives? It's not over: you get START_LIVES new ones (and keep your things).
        Returns True if that was your last life."""
        p = self.player
        p.lives -= 1
        self.lives_lost += 1
        if p.lives > 0:
            return False
        p.lives = START_LIVES
        self.out_of_lives += 1
        self.tell(story.OUT_OF_LIVES)
        return True

    def nearest_house(self, pos):
        """The closest house you can walk to (in Nightfall Hollow: the closest shrine). Home if there's none."""
        houses = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.map[r][c] == "H"]
        walk = self.reach(pos)
        near = [h for h in houses if h in walk] or houses or [self.start]
        return min(near, key=lambda h: (distance(pos, h), h))

    def knocked_out(self):
        """Out of health in a cave or on the map: lose a life and wake up with full health.
        In a cave you wake up outside its Mine. On the map, at the nearest house (or shrine)."""
        p = self.player
        last = self.lose_life()
        p.health = p.max_health
        if self.battle and self.battle.result is None:
            self.battle.result = "lost"
        if self.cave:                           # out of the cave, next to the Mine you climbed down
            self.cave = None
            where, sub = "next to the Mine", "You wake up outside the Mine."
        else:
            p.pos = self.nearest_house(p.pos)
            self.reveal()
            where = "at the shrine" if self.world == 2 else "at the house"
            sub = "You wake up %s." % where
        self.log("Everything goes dark... You wake up %s with full health. Lives left: %d"
                 % (where, p.lives), "bad")
        self.sound("lose")
        if last:
            self.effect("knockout", text="OUT OF LIVES!", sub="But heroes never give up! %d new lives." % p.lives)
        else:
            self.effect("knockout", sub="%s %d %s left." % (sub, p.lives, "life" if p.lives == 1 else "lives"))

    def random_event(self):
        p = self.player
        if self.here == "R":
            return                                  # on the path nothing happens, good or bad
        danger = TILE_DANGER.get(self.here, 0)
        roll = self.rng.random()
        if roll < danger:
            ouches = INJURIES[self.here]
            if self.here == "G" and self.land_name(p.pos) in LAND_INJURIES:
                ouches = LAND_INJURIES[self.land_name(p.pos)]      # snow or hot sand instead of thistles
            self.log(self.rng.choice(ouches), "bad")
            self.hurt_player(1)
        elif roll < danger + HEAL_EVENT_CHANCE and self.here in "FGM":
            self.log(self.rng.choice(HEALS), "good")
            if p.heal(1):
                self.popup(p.pos, "+1", "good")
            if not p.has_armor and self.rng.random() < 0.3:
                p.put_on_armor()
                self.log("You found ARMOR! It soaks up %d damage before it breaks." % p.max_armor, "loot")
                self.popup(p.pos, "+armor", "loot")
                self.sound("pickup")

    def move_monsters(self):
        target = self.player.pos
        player_safe = self.here in SAFE         # in a house (or up on a landmark) nothing can get you
        on_path = self.here == "R"              # on the path monsters don't chase you (but they can still bump into you)
        hidden = self.here == "B"               # in the tall reeds monsters can't see you
        for m in self.monsters:
            if not m.is_alive or self.rng.random() >= m.move_chance:
                continue
            if m.shadow and self.in_light(m.pos) and self.rng.random() >= LIGHT_SLOWDOWN:
                continue                            # the light slows shadow monsters down
            if m.special == "drowns":
                options = self.neighbors(m.pos, water=True)     # it can only swim...
                hunting = self.here == "W"                      # ...so it only comes after your boat
            else:
                options = [p for p in self.neighbors(m.pos) if self.tile(p) not in "HPLDNQ"]
                hunting = not (player_safe or on_path or hidden)
            if m.special == "archer":
                options = [p for p in options if p != target]   # archers keep their distance
            if not options:
                continue
            if hunting and distance(m.pos, target) <= (self.chase_distance() if m.shadow else CHASE_DISTANCE):
                best = min(distance(p, target) for p in options)
                options = [p for p in options if distance(p, target) == best]
            m.pos = self.rng.choice(options)

    def archers_shoot(self):
        if self.here in SAFE + "RB":            # Skeletons can't shoot you in a house, on a landmark, on the path or in reeds
            return
        for m in self.monsters:
            if not (m.is_alive and m.special == "archer"):
                continue
            d = distance(m.pos, self.player.pos)
            if 1 <= d <= 2 and self.is_visible(m.pos) and self.rng.random() < 0.35:
                self.effect("arrow", start=m.pos, end=self.player.pos)
                self.log("%s shoots an arrow at you!" % a_or_an(m.kind), "bad")
                self.hurt_player(1)
                if not self.player.is_alive:
                    return

    # ----- battles ------------------------------------------------------------

    def start_battle(self, monster):
        self.battle = Battle(monster)
        self.log("%s attacks!" % a_or_an(monster.kind), "bad")
        self.sound("alert")
        tips = {
            "tough": "Zombies are tough - your hits do 1 less damage.",
            "archer": "The Skeleton drops its bow and fights up close!",
            "explodes": "It's hissing! Beat it before the fuse runs out!",
            "drowns": "It's circling your boat! Beat it fast, before it smashes the boat!",
            "warden": "The Shadow Warden guards the bridge. Beat it to cross!",
            "guardian": "A Shadow Guardian! Beat it, then you can light its beacon.",
        }
        if monster.special in tips:
            self.battle.lines.append((tips[monster.special], "info"))

    def battle_line(self, text, kind="info"):
        if self.battle:
            self.battle.lines.append((text, kind))
        self.log(text, kind)

    def player_attack(self, monster):
        """Returns the damage dealt to the monster."""
        p = self.player
        if p.sunfang:                                   # Sunfang never breaks, and rarely misses
            if self.rng.random() >= SUNFANG_HIT_CHANCE:
                self.battle_line("Sunfang flashes past... you missed!")
                self.effect("battle_miss", target="monster")
                self.sound("miss")
                return 0
            damage = self.sunfang_damage(monster.special) + self.ring_power()
            self.battle_line("Sunfang blazes! It hits for %d damage!" % damage, "good")
            return damage
        if not p.swords:
            self.battle_line("No sword - you punch it for 1 damage!")
            return 1
        if self.rng.random() >= 0.7:
            self.battle_line("You missed!")
            self.effect("battle_miss", target="monster")
            self.sound("miss")
            return 0
        damage = self.rng.randint(2, 6) + p.damage_bonus
        if monster.special == "tough":
            damage = max(1, damage - 1)
        bonus = self.ring_power()
        damage += bonus
        self.battle_line("Your sword hits for %d damage!%s" % (damage, " The diamond ring glows!" if bonus else ""), "good")
        if p.swords[0].use():
            p.swords.pop(0)
            self.battle_line("Your sword broke! Swords left: %d" % len(p.swords), "bad")
        self.check_chipped_swords()
        return damage

    def battle_action(self, action):
        """action: "attack", "run" or "eat" """
        b = self.battle
        if not b or b.over:
            return
        m = b.monster
        p = self.player

        if action == "attack":
            damage = self.player_attack(m)
            if damage:
                m.health = max(0, m.health - damage)
                self.effect("battle_hit", target="monster", amount=damage)
                self.sound("hit")
        elif action == "run":
            if self.rng.random() < 0.5:
                damage = self.rng.randint(1, 2)
                self.battle_line("The %s swipes at you as you run!" % m.kind, "bad")
                self.hurt_player(damage)
                self.effect("battle_hit", target="player", amount=damage)
            if b.result is None:
                spots = self.neighbors(p.pos) + (self.neighbors(p.pos, water=True) if p.has_boat else [])
                p.pos = self.rng.choice([s for s in spots if s != m.pos] or spots or [p.pos])
                self.reveal()
                self.battle_line("You escaped to the %s!" % self.tile_name(p.pos))
                b.result = "fled"
            else:
                b.result = "lost"
            return
        elif action == "eat":
            if p.food == 0 or p.health == p.max_health:
                self.eat()          # explains why not; doesn't use your turn
                return
            self.eat()
        else:
            return

        # The monster's turn
        if m.is_alive:
            if b.fuse is not None:
                b.fuse -= 1
                if b.fuse <= 0:
                    damage = self.rng.randint(*m.damage)
                    m.health = 0
                    self.battle_line("BOOM! The %s explodes for %d damage!" % (m.kind, damage), "bad")
                    self.effect("explosion", pos=m.pos)
                    self.sound("boom")
                    self.hurt_player(damage)
                    self.effect("battle_hit", target="player", amount=damage)
                    b.result = b.result or "exploded"     # ("lost" if the blast knocked you out)
                    self.monster_gone(m, give_xp=False)
                else:
                    self.battle_line("The fuse burns... %d!" % b.fuse, "bad")
            else:
                if self.rng.random() < 0.6:
                    damage = self.rng.randint(*m.damage)
                    if m.shadow and m.special not in ("guardian", "warden") and self.in_light(m.pos):
                        damage = max(1, damage - 1)         # the beacon's light weakens it
                    self.battle_line("The %s hits you for %d damage!" % (m.kind, damage), "bad")
                    self.hurt_player(damage)
                    self.effect("battle_hit", target="player", amount=damage)
                else:
                    self.battle_line("The %s misses!" % m.kind)
                if m.special == "drowns" and b.result is None and self.rng.random() < SHIPWRECK_CHANCE:
                    self.battle_line("CRASH! The %s smashes your boat to pieces!" % m.kind, "bad")
                    self.drown(b)               # a Sea Serpent can sink your boat
        elif b.result is None:
            b.result = "won"
            self.battle_line("You defeated the %s!" % m.kind, "quest")
            self.sound("victory")
            self.monster_gone(m, give_xp=True)

        if not p.is_alive:
            b.result = "lost"

    def drown(self, battle):
        p = self.player
        damage = self.rng.randint(*DROWN_DAMAGE)
        self.battle_line("Glub, glub... you sink under the water!", "bad")
        self.hurt_player(damage)
        self.effect("battle_hit", target="player", amount=damage)
        if battle.result == "lost":
            return                              # knocked out: you already woke up at a house
        battle.result = "drowned"
        if p.is_alive:
            p.has_boat = False
            p.pos = self.nearest_shore(p.pos)
            self.reveal()
            self.battle_line("You lose your boat and wash up on the shore.", "bad")

    def nearest_shore(self, pos):
        """The closest square you can walk home from (never a little island)."""
        found, todo = {pos}, [pos]
        while todo:
            spot = todo.pop(0)
            if spot in self.mainland:
                return spot
            for dr, dc in DIRECTIONS.values():
                nxt = (spot[0] + dr, spot[1] + dc)
                if self.in_bounds(nxt) and nxt not in found:
                    found.add(nxt)
                    todo.append(nxt)
        return self.start

    def monster_gone(self, monster, give_xp):
        if monster in self.monsters:
            self.monsters.remove(monster)
        if monster.special == "warden":
            self.log("The Shadow Warden crumbles away. The way to the bridge is open!", "quest")
        self.player.monsters_defeated += 1
        if give_xp:
            self.gain_xp(monster.xp)
        if self.monster_quest.advance():
            self.log("Quest complete: %s! You are fully healed." % self.monster_quest.description, "quest")
            self.player.heal(self.player.max_health)
            self.sound("quest")
            self.quest_xp()
            self.after_quest()

    # ----- XP and leveling up -----------------------------------------------------

    def gain_xp(self, amount, quiet=False):
        p = self.player
        p.xp += amount
        if not quiet:
            self.battle_line("+%d XP" % amount, "loot")
        while p.xp >= p.xp_needed:
            p.xp -= p.xp_needed
            p.level += 1
            p.heal(p.max_health)                  # leveling up heals you all the way...
            self.level_ups.append(p.level)        # ...and you get to pick a power (game.py shows the card)
            self.battle_line("LEVEL UP! You are level %d and fully healed. Pick a new power%s!"
                             % (p.level, " after the fight" if self.battle else ""), "quest")
            self.effect("levelup")
            self.sound("levelup")

    def power_choices(self):
        """CARD_CHOICES different powers for a LEVEL UP! card, picked at random from the ones
        you can still get. One of them is always one of the MAIN_POWERS (Stronger or Tougher)."""
        p = self.player
        can_get = [name for name in POWERS if not p.maxed(name)]
        main = [name for name in can_get if name in MAIN_POWERS]
        choices = [self.rng.choice(main)] if main else []
        others = [name for name in can_get if name not in choices]
        how_many = max(0, min(len(others), CARD_CHOICES - len(choices)))
        choices += self.rng.sample(others, how_many)
        self.rng.shuffle(choices)                 # so Stronger or Tougher isn't always number 1
        return choices

    def next_power_offer(self):
        """The powers on the LEVEL UP! card that should show now - or None if no card is waiting."""
        if self.level_ups and self.power_offer is None:
            self.power_offer = self.power_choices() or None
            if self.power_offer is None:          # you already have every power there is!
                self.level_ups.clear()
        return self.power_offer

    def pick_power(self, name):
        """You picked a power on the LEVEL UP! card. Returns False if you can't have it."""
        p = self.player
        if p.maxed(name):
            return False
        p.powers[name] = p.power(name) + 1
        if name == "Extra life":
            p.lives += 1
        if name == "Tougher":
            p.max_health += TOUGHER_HEALTH
            p.heal(TOUGHER_HEALTH)
        if name == "Tough armor" and p.has_armor:
            p.armor += ARMOR_BOOST                # the armor you're wearing gets tougher too
        if self.level_ups:
            self.level_ups.pop(0)
        self.power_offer = None
        self.log("You picked %s: %s!" % (name, POWERS[name]["what"]), "good")
        self.sound("craft")
        return True

    def close_battle(self):
        """Called by the graphics when the player has seen how the fight ended."""
        self.battle = None
