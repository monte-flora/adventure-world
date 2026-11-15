"""
PIXEL ART for Adventure World.

Every picture is a grid of letters. Each letter is one pixel, and COLORS
says which color each letter means. A "." is see-through.

Want a gold knight? Change the "a" (steel blue) letters in PLAYER to "Y".
Want to draw a new monster? Copy a picture, change the letters, and add it
to MONSTER_ART at the bottom. Every row must be the same length!
"""

COLORS = {
    "k": (28, 26, 38),      # black outline
    "w": (245, 245, 240),   # white
    "s": (240, 196, 150),   # skin
    "h": (110, 66, 36),     # hair
    "b": (60, 110, 225),    # blue
    "B": (38, 58, 140),     # dark blue
    "g": (96, 200, 90),     # green
    "G": (46, 120, 52),     # dark green
    "r": (220, 50, 50),     # red
    "y": (255, 214, 64),    # yellow
    "o": (255, 140, 30),    # orange
    "c": (90, 230, 240),    # cyan
    "C": (30, 140, 170),    # dark cyan
    "n": (150, 98, 52),     # brown
    "N": (92, 58, 30),      # dark brown
    "e": (150, 150, 160),   # gray
    "E": (90, 90, 100),     # dark gray
    "l": (215, 220, 230),   # light gray
    "p": (170, 80, 220),    # purple
    "P": (70, 26, 100),     # dark purple
    "v": (220, 150, 255),   # violet glow
    "a": (104, 142, 180),   # steel blue (the Hero's knight armor)
    "A": (54, 84, 122),     # dark steel blue
    "i": (196, 218, 238),   # steel shine
    "R": (140, 28, 46),     # dark red
    "Y": (232, 172, 52),    # gold
    "m": (178, 90, 60),     # rust red (the rocks in Ember Canyon)
    "M": (118, 52, 38),     # dark rust red
    # Colors that glow in the dark, for the mushrooms and crystals in caves
    "q": (170, 230, 255),   # glowing pale blue
    "Q": (86, 156, 222),    # its shadow
    "j": (214, 246, 110),   # glowing lime green
    "J": (126, 180, 56),    # its shadow
    "t": (130, 240, 214),   # glowing teal
    "T": (54, 156, 144),    # its shadow
}

# ---------------------------------------------------------------------------
# Characters (16 x 16)
# ---------------------------------------------------------------------------

# The Hero, a little knight: a helmet with a red plume and a T-shaped visor,
# steel armor, a belt with a gold buckle and a red cape behind his legs.
# His sword hand is the lower right arm (the game draws his tool there).
PLAYER = [
    ".....rrR........",
    ".....kkrkkk.....",
    "....kiiaiaak....",
    "...kiiaaiaaAk...",
    "...kiaaaiaaAk...",
    "...kakkkkkkAk...",
    "...kaaakkaaAk...",
    "....kaakkaAk....",
    "..kkkkAAAAkkkk..",
    ".kiikaiaaaAkiik.",
    ".kaAkaiaaaAkaAk.",
    ".kaakNNyyNNkaak.",
    ".RkkkaaAaaAkkkR.",
    ".kRraaaRRaaarRk.",
    "..kREEEkkEEERk..",
    "..kkkkk..kkkkk..",
]

# Armor that the Hero puts on when he finds it. It's drawn ON TOP of PLAYER:
# a "." here means "show the Hero underneath", so it still fits if you recolor him.
# It gives him a red-and-gold kite shield and big silver shoulder plates.
ARMOR = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "..kkk...........",
    ".kwllk.....kkk..",
    "kkkkkkk...kwllk.",
    "kYYYYYk...kllek.",
    "kYRRrYk.........",
    "kYRRrYk.........",
    "kYRrrYk.........",
    ".kYrYk..........",
    ".kYrYk..........",
    "..kYk...........",
]

# ---------------------------------------------------------------------------
# The Hero from the side, for the caves and the Shadow Castle. He faces right
# (the game flips him when he walks left). They use the same letters as PLAYER,
# so if you recolor PLAYER, recolor these too!
# Every side picture has the same top half (helmet, arm and belt): only his
# legs and cape change. His front hand, at the bottom of his arm, holds his tool.
# ---------------------------------------------------------------------------

# Standing still
SIDE_STAND = [
    "......rrrR......",
    "...rrRkkkkk.....",
    "..rR.kiiaaak....",
    "..R.kiiaaaaak...",
    "....kiaaaakkkkk.",
    "....kAaaaaakAk..",
    ".....kAaaaaAk...",
    "...kkkkkkkkk....",
    "..rkaAkiiakAk...",
    ".rRkaAkiaakAk...",
    ".rRkNNkaaAkyk...",
    ".rRRkAAkaak.....",
    "..rRkAAkaak.....",
    "...RkAAkaak.....",
    "....kEEEkEEEk...",
    "....kkkkkkkkk...",
]

# Walking is 4 pictures, over and over: STEP_1, PASS_1, STEP_2, PASS_2.
# The near leg is light steel ("a"), the far leg is dark steel ("A"). Both legs
# are the same size (2 pixels wide, with a 3-pixel boot), and they cross:
# the near leg swings past IN FRONT of the far one, the far leg BEHIND the near one.
# Walk 1: his near leg steps out in front
SIDE_STEP_1 = [
    "......rrrR......",
    "...rrRkkkkk.....",
    "..rR.kiiaaak....",
    "..R.kiiaaaaak...",
    "....kiaaaakkkkk.",
    "....kAaaaaakAk..",
    ".....kAaaaaAk...",
    "...kkkkkkkkk....",
    "..rkaAkiiakAk...",
    ".rRkaAkiaakAk...",
    ".rRkNNkaaAkyk...",
    ".rRRkAAkaak.....",
    "..rkAAkkaak.....",
    "..RkAAk.kaak....",
    "..kEEEk.kEEEk...",
    "..kkkkk.kkkkk...",
]

# Walk 2: his far leg is planted, and his near foot lifts and swings past in front of it
SIDE_PASS_1 = [
    "......rrrR......",
    "...rrRkkkkk.....",
    "..rR.kiiaaak....",
    "..R.kiiaaaaak...",
    "....kiaaaakkkkk.",
    "....kAaaaaakAk..",
    ".....kAaaaaAk...",
    "...kkkkkkkkk....",
    "..rkaAkiiakAk...",
    ".rRkaAkiaakAk...",
    ".rRkNNkaaAkyk...",
    ".rRRkAkaak......",
    "..rRkAkkaak.....",
    "...RkAkEEEEk....",
    "....kEEEkkkk....",
    "....kkkkk.......",
]

# Walk 3: now his far leg steps out in front
SIDE_STEP_2 = [
    "......rrrR......",
    "...rrRkkkkk.....",
    "..rR.kiiaaak....",
    "..R.kiiaaaaak...",
    "....kiaaaakkkkk.",
    "....kAaaaaakAk..",
    ".....kAaaaaAk...",
    "...kkkkkkkkk....",
    "..rkaAkiiakAk...",
    ".rRkaAkiaakAk...",
    ".rRkNNkaaAkyk...",
    ".rRRkaakAAk.....",
    "..rkaakkAAk.....",
    "..Rkaak.kAAk....",
    "..kEEEk.kEEEk...",
    "..kkkkk.kkkkk...",
]

# Walk 4: his near leg is planted, and his far foot lifts and swings past behind it
SIDE_PASS_2 = [
    "......rrrR......",
    "...rrRkkkkk.....",
    "..rR.kiiaaak....",
    "..R.kiiaaaaak...",
    "....kiaaaakkkkk.",
    "....kAaaaaakAk..",
    ".....kAaaaaAk...",
    "...kkkkkkkkk....",
    "..rkaAkiiakAk...",
    ".rRkaAkiaakAk...",
    ".rRkNNkaaAkyk...",
    ".rRRkaakAk......",
    "..rRkaakAAk.....",
    "...RkaakEEEk....",
    "....kEEEkkkk....",
    "....kkkkk.......",
]

# Jumping up (and ground pounds): knees tucked
SIDE_JUMP = [
    "......rrrR......",
    "...rrRkkkkk.....",
    "..rR.kiiaaak....",
    "..R.kiiaaaaak...",
    "....kiaaaakkkkk.",
    "....kAaaaaakAk..",
    ".....kAaaaaAk...",
    "...kkkkkkkkk....",
    "..rkaAkiiakAk...",
    ".rRkaAkiaakAk...",
    ".rRkNNkaaAkyk...",
    ".rRRkaaaaaAk....",
    "rRRkAAkaaaaak...",
    "RR.kEEkkkaaEk...",
    "....kkk.kEEEk...",
    ".........kkk....",
]

# Falling down (and hanging from a ledge): legs stretched out
SIDE_FALL = [
    "......rrrR......",
    "...rrRkkkkk.....",
    "..rR.kiiaaak....",
    "..R.kiiaaaaak...",
    "....kiaaaakkkkk.",
    "....kAaaaaakAk..",
    ".....kAaaaaAk...",
    "...kkkkkkkkk....",
    "..rkaAkiiakAk...",
    ".rRkaAkiaakAk...",
    ".rRkNNkaaAkyk...",
    "..rRkaaaaaAk....",
    "..rRkAAkkaak....",
    "..rRkAAk.kaak...",
    "...RkEEk.kEEEk..",
    "....kkk...kkkk..",
]

# Armor for the side pictures, drawn ON TOP of each one (like ARMOR on PLAYER):
# the red-and-gold shield on his back and a big silver plate on his shoulder.
ARMOR_SIDE = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "kkkkk..kkkk.....",
    "kYYYk.kwwllk....",
    "kYRYk.kllllek...",
    "kYRYk..kkkkk....",
    ".kYk............",
    "..k.............",
    "................",
    "................",
    "................",
]

# ---------------------------------------------------------------------------
# The Hero from behind, climbing a ladder. It's the same helmet as PLAYER (with no
# visor: that's on the front!) and his red cape down his back. His arms and legs
# take turns: CLIMB_1, CLIMB_2, CLIMB_1, CLIMB_2... as he climbs.
# ---------------------------------------------------------------------------

# Climb 1: his left arm (on our left) reaches up for the next rung, his right foot steps up
CLIMB_1 = [
    ".....rrR........",
    ".kk..kkrkkk.....",
    "kaakkiiaiaak....",
    "kaAkiiaaiaaAk...",
    "kaAkiaaaiaaAk...",
    "kaAkaaaaaaaAk...",
    "kaAkAaaaaaaAk...",
    ".kaAkAAAAAAkkk..",
    ".kaakrRrrRrkiik.",
    "..kkrrRrrRrrkaAk",
    "...krrRrrRrrkaak",
    "...krrRrrRrrkAAk",
    "...kRrRrrRrRkkk.",
    "...kkaAk.kEEk...",
    "....kaAk.kkkk...",
    "....kEEk........",
]

# Climb 2: now his right arm reaches up, and his left foot steps up
CLIMB_2 = [
    ".....rrR........",
    ".....kkrkkk..kk.",
    "....kiiaiaakkaak",
    "...kiiaaiaaAkaAk",
    "...kiaaaiaaAkaAk",
    "...kaaaaaaaAkaAk",
    "...kAaaaaaaAkaAk",
    "..kkkAAAAAAkaAk.",
    ".kiikrRrrRrkaak.",
    "kaAkrrRrrRrrkk..",
    "kaakrrRrrRrrk...",
    "kAAkrrRrrRrrk...",
    ".kkkRrRrrRrRk...",
    "...kEEk.kaAkk...",
    "...kkkk.kaAk....",
    "........kEEk....",
]

# Armor for the climbing pictures, drawn ON TOP of them: his shield on his
# back, over the cape, and silver plates on both shoulders.
ARMOR_BACK = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".kkkk......kkkk.",
    "kwllkkkkkkkkwllk",
    ".kek.kYYYYk.kek.",
    ".....kYRrYk.....",
    ".....kYRrYk.....",
    "......kYYk......",
    ".......kk.......",
    "................",
    "................",
]

# ---------------------------------------------------------------------------
# The Hero on a climbing wall (%). The wall is on his right (the game flips him when
# it's on his left), and his gloves (E) and boots grip it. He climbs hand over
# hand: WALL_1, WALL_HOLD, WALL_2, WALL_HOLD... as he goes up or down. When he
# stops he holds still in WALL_HOLD, and WALL_SLIDE is him sliding down it.
# The near arm and leg are light steel ("a"), the far ones dark steel ("A").
# ---------------------------------------------------------------------------

# Climb 1: his near arm reaches up high and his near knee comes up
WALL_1 = [
    "...........kk...",
    "....rrrR..kEEk..",
    ".rrRkkkkk.kEEk..",
    "rR.kiiaaakkaak..",
    "R.kiiaaaaakaak..",
    "..kiaaaakkkaak..",
    "..kAaaaaakAkak..",
    "...kAaaaaAkkak..",
    ".kkkkkkkkkkak...",
    "..rkaaAiiaakkk..",
    ".rRkaaAiakkAEEk.",
    ".rRkNNNyNkAkkk..",
    ".rRRkaaaaaaak...",
    "..rRkAAkkkkaEEk.",
    "...RkAAk...kEEk.",
    "....kEEEk...kk..",
]
# Climb 2: now his far arm reaches up, and his far knee comes up
WALL_2 = [
    "...........kk...",
    "....rrrR..kEEk..",
    ".rrRkkkkk.kEEk..",
    "rR.kiiaaakkAAk..",
    "R.kiiaaaaakAAk..",
    "..kiaaaakkkAAk..",
    "..kAaaaaakAkAk..",
    "...kAaaaaAkkAk..",
    ".kkkkkkkkkkAk...",
    "..rkaaAiiaakkk..",
    ".rRkaaAiakkaEEk.",
    ".rRkNNNyNkakkk..",
    ".rRRkaaaaAAAk...",
    "..rRkaakkkkAEEk.",
    "...Rkaak...kEEk.",
    "....kEEEk...kk..",
]
# Holding on: both hands on the wall, knees bent, boots against it
WALL_HOLD = [
    "................",
    "....rrrR...kk...",
    ".rrRkkkkk.kEEk..",
    "rR.kiiaaakkEEk..",
    "R.kiiaaaaakaak..",
    "..kiaaaakkkaak..",
    "..kAaaaaakAkak..",
    "...kAaaaaAkkak..",
    ".kkkkkkkkkkkkk..",
    "..rkaaAiiakAEEk.",
    ".rRkaaAiakkAEEk.",
    ".rRkNNNyNkkkkk..",
    ".rRRkaaaaaaak...",
    "..rRkAAkkkkaEEk.",
    "...RkAAAAAk.kEk.",
    "....kkkkEEk.kk..",
]
# Sliding down: both arms up, gripping hard, legs straight and toes on the wall
WALL_SLIDE = [
    "..........kkk...",
    "....rrrR.kEEEk..",
    ".rrRkkkkkkEEEk..",
    "rR.kiiaaakaAAk..",
    "R.kiiaaaaakaAk..",
    "..kiaaaakkkaAk..",
    "..kAaaaaakAkaAk.",
    "...kAaaaaAkkaAk.",
    ".kkkkkkkkkkaAk..",
    "..rkaaAiiakkk...",
    ".rRkaaAiak......",
    ".rRkNNNyNk......",
    "rRRkaaaaaAk.....",
    "RR.kAAkkaaakk...",
    "...kAAk.kaaEEk..",
    "...kEEEk.kkkkk..",
]

# Armor for the climbing-wall pictures, drawn ON TOP of them: his shield on his
# back, over the cape, and the silver plate on his shoulder.
ARMOR_WALL = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "kkkkk.kkk.......",
    "kYYYkkwllk......",
    "kYRYk.klek......",
    "kYRYk.kkk.......",
    ".kYk............",
    "..k.............",
    "................",
    "................",
]


ZOMBIE = [
    "................",
    "....kkkkkkkk....",
    "...kggggggggk...",
    "...kgGggggGgk...",
    "...kgkrggkrgk...",
    "...kggggggggk...",
    "...kgGkkkkGgk...",
    "...kggggggggk...",
    "....kggggggk....",
    "..kkcccccccckk..",
    ".kgkcccCcccckgk.",
    ".kgkccccCccckgk.",
    "...kcccccccck...",
    "...kBBBBBBBBk...",
    "...kBBBkkBBBk...",
    "...kkkk..kkkk...",
]

SKELETON = [
    "................",
    ".....kkkkkk.....",
    "....kwwwwwwk....",
    "...kwwwwwwwwk...",
    "...kwkkwwkkwk...",
    "...kwkkwwkkwk...",
    "...kwwwkkwwwk...",
    "....kwkwkwkk....",
    ".....kkkkkk.....",
    "......kwwk......",
    "...kkwwwwwwkk...",
    "..kw.kwkkwk.wk..",
    "..kw.kwwwwk.wk..",
    ".....kwkkwk.....",
    ".....kw..wk.....",
    ".....kk..kk.....",
]

# A floating skull wrapped in flames. It drifts at you, its fire flares up... then BOOM!
EMBER_SKULL = [
    "......r...r.....",
    "...r..ro..ro..r.",
    "...ro.oyr.oyo.ro",
    "..rooyyoyyyoooor",
    "..ookkkkkkkkoor.",
    "..okwwwwwwwlkoo.",
    "..kwwwwwwwwwlk..",
    ".rkwkkkwwkkklkr.",
    ".okwkyokwkoykko.",
    "..kwkkkwwkkklk..",
    "..kwwwwkkwwwlk..",
    "...kwwwwwwwlk...",
    "...kwkwkwkwkk...",
    "....kwwwwwlk....",
    ".....kkkkkk.....",
    "....r.o..o.r....",
]

SPIDER = [
    "................",
    "................",
    "..e...kkkk...e..",
    "...e.kppppk.e...",
    "eeee.krpprk.eeee",
    "....kppppppk....",
    "..eekppppppkee..",
    ".e..kppppppk..e.",
    "e..eekppppkee..e",
    "...e..kkkk..e...",
    "..e..........e..",
    ".e............e.",
    "................",
    "................",
    "................",
    "................",
]



# A Sea Serpent pokes its head out of the water
SERPENT = [
    "................",
    "........GGGG....",
    ".......GggggG...",
    "......GgggkwgG..",
    "......GggggggG..",
    "......GgrrrrgG..",
    ".......GGggGG...",
    ".......GggG.....",
    "..GG..GggG......",
    ".GggGGggG.......",
    ".GgggggG...GG...",
    "..GGGGG...GggG..",
    "..........GgggG.",
    "cCcCcCcCcCcCcCcC",
    "CcCcCcCcCcCcCcCc",
    "................",
]

# ---------------------------------------------------------------------------
# The Hero walking around the world map, seen from above like an old 8-bit game.
# Each way has a standing picture and 2 walking pictures that take turns, one
# for every step: one arm swings forward while the other goes back, and one
# foot lifts up while the other is down.
# Going down we see his front (PLAYER), going up we see his back, and going
# left or right we see his side (SIDE_STAND, SIDE_STEP_1 and SIDE_STEP_2).
# ---------------------------------------------------------------------------

# Walking down, step 1: his left arm (on our left) swings back, his right arm forward,
# and his left foot lifts up
WALK_DOWN_1 = PLAYER[:8] + [
    "..kkkkAAAAkkkk..",
    ".kiikaiaaaAkiik.",
    ".kaAkaiaaaAkaAk.",
    ".kkkkNNyyNNkaak.",
    ".RkRkaaAaaAkaAk.",
    ".kRkEEEkRaaakkk.",
    "..kRkkkkREEERk..",
    "..kk....kkkkkk..",
]

# Walking down, step 2: the other arm and the other foot
WALK_DOWN_2 = PLAYER[:8] + [
    "..kkkkAAAAkkkk..",
    ".kiikaiaaaAkiik.",
    ".kaAkaiaaaAkaAk.",
    ".kaakNNyyNNkkkk.",
    ".kaAkaaAaaAkRkR.",
    ".kkkaaaRkEEEkRk.",
    "..kREEERkkkkRk..",
    "..kkkkkk....kk..",
]

# Standing still, seen from behind: the same helmet as PLAYER with no visor,
# and his red cape down his back
BACK_STAND = [
    ".....rrR........",
    ".....kkrkkk.....",
    "....kiiaiaak....",
    "...kiiaaiaaAk...",
    "...kiaaaiaaAk...",
    "...kaaaaaaaAk...",
    "...kAaaaaaaAk...",
    "....kAAAAAAk....",
    "..kkkkkkkkkkkk..",
    ".kiikrRrrRrkiik.",
    ".kaAkrRrrRrkaAk.",
    ".kaakrRrrRrkaak.",
    ".kkkkRrRrrRkkkk.",
    "...kaaAkkaaAk...",
    "...kEEEkkEEEk...",
    "...kkkkkkkkkk...",
]

# Walking up, step 1: his left arm swings back, and his left foot lifts up
WALK_UP_1 = BACK_STAND[:9] + [
    ".kiikrRrrRrkiik.",
    ".kaAkrRrrRrkaAk.",
    ".kkkkrRrrRrkaak.",
    "....kRrRrrRkaAk.",
    "...kEEEkkaaAkkk.",
    "...kkkkkkEEEk...",
    ".........kkkk...",
]

# Walking up, step 2: the other arm and the other foot
WALK_UP_2 = BACK_STAND[:9] + [
    ".kiikrRrrRrkiik.",
    ".kaAkrRrrRrkaAk.",
    ".kaakrRrrRrkkkk.",
    ".kaAkRrRrrRk....",
    ".kkkaaAkkEEEk...",
    "...kEEEkkkkkk...",
    "...kkkkk........",
]

# ---------------------------------------------------------------------------
# Boats and wood
# ---------------------------------------------------------------------------

# The Hero sits in this when he rows across the water (16 x 5)
BOAT = [
    "kkkkkkkkkkkkkkkk",
    "knnnnnnnnnnnnnnk",
    ".kNnnnnnnnnnnNk.",
    "..kNNNNNNNNNNk..",
    "...kkkkkkkkkk...",
]

# A diamond ring that powers up your sword (8 x 8)
RING = [
    "...cc...",
    "..cwcc..",
    "...cc...",
    "..yyyy..",
    ".y....y.",
    ".y....y.",
    "..yyyy..",
    "........",
]

# The Hero's bow (8 x 8)
BOW = [
    "....Nl..",
    "...n.l..",
    "..n..l..",
    ".n...l..",
    ".n...l..",
    "..n..l..",
    "...n.l..",
    "....Nl..",
]

# A log, for the side panel (8 x 8)
WOOD = [
    "........",
    "........",
    ".NNNNNN.",
    "NnnnnnyN",
    "NnnnnyNy",
    "NnnnnnyN",
    ".NNNNNN.",
    "........",
]

# ---------------------------------------------------------------------------
# Map decorations (16 x 16)
# ---------------------------------------------------------------------------

TREE = [
    "......kkkk......",
    "....kkGGGGkk....",
    "...kGGgGGGGGk...",
    "..kGgggGGgGGGk..",
    "..kGgggggGgGGk..",
    ".kGGgggggggGGGk.",
    ".kGgggGgggggGGk.",
    ".kGGggggggGgGGk.",
    "..kGGgggggggGk..",
    "...kkGGGGGGkk...",
    ".....kkNNkk.....",
    "......kNNk......",
    "......kNnk......",
    "......kNnk......",
    ".....kNNnnk.....",
    "................",
]

HOUSE = [
    "................",
    ".......kk.......",
    "......krrk......",
    ".....krrrrk.....",
    "....krrrrrrk....",
    "...krrrrrrrrk...",
    "..krrrrrrrrrrk..",
    ".kkkkkkkkkkkkkk.",
    "..knnnnnnnnnnk..",
    "..knyynnnnyynk..",
    "..knyynnnnyynk..",
    "..knnnnNNnnnnk..",
    "..knnnnNNnnnnk..",
    "..knnnnNNnnnnk..",
    "..kkkkkkkkkkkk..",
    "................",
]

# ---------------------------------------------------------------------------
# The lands of the home world: landmarks, rocks and signposts (16 x 16)
# ---------------------------------------------------------------------------

# The windmill by your home: its sails turn slowly (the game spins them)
WINDMILL = [
    "................",
    "................",
    "......kkkk......",
    ".....krrrrk.....",
    "....krrrrrrk....",
    "...kkkkkkkkkk...",
    "....klllllek....",
    "....kllnnlek....",
    "....kllnnlek....",
    "...klllllleek...",
    "...kllllllllek..",
    "...kllllllleek..",
    "..klllllNNlleek.",
    "..kllllNNNNleek.",
    "..kllllNNNNlleek",
    "..kkkkkkkkkkkkkk",
]

# The windmill's sails, drawn on top and turned by the game
WINDMILL_SAILS = [
    "kwwk.........kk.",
    "kwwwk.......kwwk",
    ".kwwwk.....kwwwk",
    "..kwwnk...knwwk.",
    "...kwwnk.knwwk..",
    "....kknnnnkk....",
    ".....knyynk.....",
    ".....knyynk.....",
    "....kknnnnkk....",
    "...kwwnk.knwwk..",
    "..kwwnk...knwwk.",
    ".kwwwk.....kwwwk",
    "kwwwk.......kwwk",
    "kwwk.........kk.",
    "................",
    "................",
]

# The Queen Oak: the oldest, biggest tree in the world, with golden leaves
QUEEN_OAK = [
    "....kkkkkkkk....",
    "..kkGgyGGgGGkk..",
    ".kGgggGgYgggGGk.",
    "kGgYgggGGggygGGk",
    "kGggggGgggggGGGk",
    "kGGgyggggGgggYGk",
    ".kGGggYggggGGGk.",
    "..kkGGGgGGGGkk..",
    "....kkNnNNkk....",
    "......kNnk......",
    "......kNnk......",
    "......kNnk......",
    "......kNnk......",
    ".....kNNnnk.....",
    "....kNNkknnk....",
    "...kkk....kkk...",
]

# The old Watchtower in the ruins, with a red flag on top
WATCHTOWER = [
    "........kk......",
    "........krrk....",
    "........krrrk...",
    "........kkkk....",
    "...k.k.kk.k.k...",
    "...kkkkkkkkkk...",
    "...keleleleek...",
    "....kelelelk....",
    "....klekkelk....",
    "....kelkkeek....",
    "....kleleelk....",
    "....kelelelk....",
    "...keleleleek...",
    "...klekkkkeek...",
    "...kelkNNkeek...",
    "..kkkkkkkkkkkk..",
]

# Frost Peak: a snowy mountain, the highest place in the world
FROST_PEAK = [
    ".......kk.......",
    "......kwwk......",
    ".....kwwwlk.....",
    "....kwwwwlek....",
    "....kwkwwlEk....",
    "...kwkekwleEk...",
    "...kkeeekeeEk...",
    "..keeeeeeeeEEk..",
    "..keeeeeeeeeEk..",
    ".keeeleeeeeeEEk.",
    ".keeeeeeleeeeEk.",
    "keeeeeeeeeeeeEEk",
    "keleeeeeeeeleeEk",
    "keeeeeeeeeeeeeEk",
    "kkkkkkkkkkkkkkkk",
    "................",
]

# The Lighthouse on its little island: red and white stripes, and a light at the top
LIGHTHOUSE = [
    "......kkkk......",
    ".....krrrrk.....",
    "....kkkkkkkk....",
    "....kyyyyyyk....",
    "....kkkkkkkk....",
    ".....kwwwek.....",
    ".....krrrRk.....",
    ".....krrrRk.....",
    "....kwwwwwek....",
    "....kwwNNwek....",
    "....krrNNrRk....",
    "....krrrrrRk....",
    "...kwwwwwwwek...",
    "...kwwwwwwwek...",
    "..kkkkkkkkkkkk..",
    "................",
]

# The Frog's Hut in the marsh, up on stilts, and the friendly frog who lives there
FROG_HUT = [
    "................",
    ".......kk.......",
    "......kGGk......",
    ".....kGgGGk.....",
    "....kGggGGGk....",
    "...kGgggGGGGk...",
    "..kkkkkkkkkkkk..",
    "...knnnnnnnnk...",
    "...knNnkknNnk...",
    "...knnnkknnnk...",
    "...kkkkkkkkkk...",
    "....kN....kN....",
    "....kN....kN.kk.",
    "....kN...kkgggk.",
    "....kN...kgkgkgk",
    "....kN...kggggk.",
]

# The bones of a dragon, from long, long ago
DRAGON_BONES = [
    "................",
    "................",
    "................",
    "..........kkkk..",
    ".........kwwwwk.",
    "........kwwkwwlk",
    "..k.k.k.kwwwwwwk",
    ".kwkwkwkkwwlkkk.",
    "kwlwlwlwlwwk....",
    ".kwkwkwkkwwk.kk.",
    "..kwkwkwk.kkkwk.",
    "...k.k.k....kk..",
    "................",
    "................",
    "................",
    "................",
]

# A wooden signpost
# The bridge over the Icy River: wooden planks with a rail on each side (the water shows through the dots)
BRIDGE = [
    "................",
    "................",
    "N....N....N....N",
    "NNNNNNNNNNNNNNNN",
    "kkkkkkkkkkkkkkkk",
    "nnhnnhnnhnnhnnhn",
    "nnhnnhnnhnnhnnhn",
    "nnhnnhnnhnnhnnhn",
    "nnhnnhnnhnnhnnhn",
    "nnhnnhnnhnnhnnhn",
    "nnhnnhnnhnnhnnhn",
    "kkkkkkkkkkkkkkkk",
    "NNNNNNNNNNNNNNNN",
    "N....N....N....N",
    "................",
    "................",
]

# ...and the same bridge, broken: a big hole in the middle, and one plank floating away
BROKEN_BRIDGE = [
    "................",
    "................",
    "N....N.........N",
    "NNNNNN.....NNNNN",
    "kkkkkkk....kkkkk",
    "nnhnnk.....knnhn",
    "nnhnnhk....knnhn",
    "nnhnnk......knhn",
    "nnhnnhk.....knhn",
    "nnhnnk.....knnhn",
    "nnhnnhk....knnhn",
    "kkkkkkk.....kkkk",
    "NNNNNN......NNNN",
    "N....N.........N",
    "......knnnk.....",
    "................",
]

SIGNPOST = [
    "................",
    "................",
    "..kkkkkkkkkkk...",
    "..knnnnnnnnnnk..",
    "..knNNnNNNnnnnk.",
    "..knnnnnnnnnnk..",
    "..kkkkkknkkkk...",
    "......knNk......",
    "......knNk......",
    "......knNk......",
    "......knNk......",
    "......knNk......",
    "......knNk......",
    ".....kknNkk.....",
    "................",
    "................",
]

# A big rock. The game colors it for each land: grey with snow, red in the canyon...
BOULDER = [
    "................",
    "................",
    "................",
    "......kkkk......",
    "....kkllllkk....",
    "...klleeeeeek...",
    "..kleeeeeeeeEk..",
    "..keleeeeeeeEk..",
    ".kleeeeeleeeeEk.",
    ".keeeeeeeeeeEEk.",
    "keeleeeeeeeeeEEk",
    "keeeeeeeeeeleEEk",
    "keeeeeeeeeeeeEEk",
    "kEeeeeeeeeeeEEEk",
    ".kkkkkkkkkkkkkk.",
    "................",
]

# A piece of an old broken castle wall, in the Old Ruins
RUIN_WALL = [
    "................",
    "................",
    "..kkk.....kkk...",
    "..klk.kk..klk...",
    "kkkekkllkkkekkk.",
    "klleleelleeleek.",
    "keeEkeeeEkeeeEk.",
    "kkkkkkkkkkkkkkk.",
    "klelekeeleklelk.",
    "keeEkeeEkeeeEEk.",
    "kkkkkkkkkkkkkkk.",
    "kleeleklleeleek.",
    "keeEkeeeEkeeEEk.",
    "kkkkkkkkkkkkkkk.",
    "................",
    "................",
]

# A tree with snow on top, in the Frosty Corner
SNOWY_TREE = [
    "......kkkk......",
    "....kkwwwwkk....",
    "...kwwwwwwwwk...",
    "..kwwwgGGgwwwk..",
    "..kwgggggGgGwk..",
    ".kwGgggggggGGwk.",
    ".kwgggGgggggGwk.",
    ".kGGggggggGgGGk.",
    "..kGGgggggggGk..",
    "...kkGGGGGGkk...",
    ".....kkNNkk.....",
    "......kNNk......",
    "......kNnk......",
    "......kNnk......",
    ".....kNNnnk.....",
    "................",
]

# A big rock with snow on top, in the Frosty Corner
SNOWY_ROCK = [
    "................",
    "................",
    "................",
    "......kkkk......",
    "....kkwwwwkk....",
    "...kwwwwwwwwk...",
    "..kwwweeeewwwk..",
    "..kwleeeeeeewk..",
    ".kweeeeeleeeewk.",
    ".kweeeeeeeeeEwk.",
    "kweleeeeeeeeeEwk",
    "kweeeeeeeeeleEwk",
    "keeeeeeeeeeeeEEk",
    "kEeeeeeeeeeeEEEk",
    ".kkkkkkkkkkkkkk.",
    "................",
]

# ---------------------------------------------------------------------------
# Icons for the side panel (8 x 8)
# ---------------------------------------------------------------------------

HEART = [
    ".rr..rr.",
    "rwrrrrrr",
    "rrrrrrrr",
    "rrrrrrrr",
    ".rrrrrr.",
    "..rrrr..",
    "...rr...",
    "........",
]

SWORD = [
    "......kl",
    ".....klk",
    "....klk.",
    ".n.klk..",
    "..nlk...",
    "..Nn....",
    ".N..n...",
    "N.......",
]

PICKAXE = [
    "..eeee..",
    ".e.n..e.",
    "e..n...e",
    "...n....",
    "...n....",
    "...n....",
    "...n....",
    "...N....",
]

APPLE = [
    "....n...",
    "...ng...",
    ".rrnrr..",
    "rrrrrrr.",
    "rwrrrrr.",
    "rrrrrrr.",
    ".rrrrr..",
    "..r.r...",
]

DIAMOND = [
    "........",
    "..cccc..",
    ".cwcccc.",
    "cwccccCc",
    ".cccccC.",
    "..cccC..",
    "...cC...",
    "........",
]

SHIELD = [
    ".eeeeee.",
    "ebbbbbbe",
    "ebbyybbe",
    "ebyyyybe",
    "ebbyybbe",
    ".ebbbbe.",
    "..ebbe..",
    "...ee...",
]

STAR = [
    "...yy...",
    "...yy...",
    "yyyyyyyy",
    ".yyyyyy.",
    "..yyyy..",
    ".yy..yy.",
    "yy....yy",
    "........",
]

# ---------------------------------------------------------------------------
# Cave things (16 x 16)
# ---------------------------------------------------------------------------

# A bouncy mushroom: land on it and BOING!
MUSHROOM = [
    "................",
    "................",
    "................",
    "................",
    ".....kkkkkk.....",
    "...kkrrwwrrkk...",
    "..krrrrwwrrrrk..",
    ".krwwrrrrrrwwrk.",
    ".krwwrrrrrrwwrk.",
    ".kkkkkkkkkkkkkk.",
    "....klllllllk...",
    "....klllllllk...",
    "....kllellllk...",
    "....klllllllk...",
    "....klllllllk...",
    "....kkkkkkkkk...",
]

# A glittering gem to grab in caves (8 x 8)
GEM = [
    "........",
    "...kk...",
    "..kwpk..",
    ".kwpppk.",
    ".kppppk.",
    "..kppk..",
    "...kk...",
    "........",
]

# ---------------------------------------------------------------------------
# Things growing in the caves (the game paints them 4 times bigger)
# ---------------------------------------------------------------------------

# Little mushrooms that glow in the dark. Just below, green and teal ones are made
# by swapping the q and Q letters for j and J, or t and T.
# (They're much smaller than the red bouncy mushroom, and you can walk right past them.)
GLOW_MUSHROOMS = [
    ".....qqq...",
    "....qwqqq..",
    "....QQQQQ..",
    ".qqq..l....",
    "qwqqq.l.qq.",
    "QQQQQ.lqwqq",
    "..l...lQQQQ",
    "..l...l..l.",
]
GREEN_MUSHROOMS = [row.replace("q", "j").replace("Q", "J") for row in GLOW_MUSHROOMS]
TEAL_MUSHROOMS = [row.replace("q", "t").replace("Q", "T") for row in GLOW_MUSHROOMS]

# Glowing crystals in the blue ice caves. The game turns them upside down to hang from the roof.
# Just below, teal ones are made by swapping q, Q and B for t, T and C.
BLUE_CRYSTALS = [
    "......w....",
    ".....qQB...",
    "..w..qQB...",
    ".qQB.qQB.w.",
    ".qQBqqQBqQB",
    ".qQBqQQBqQB",
    "qqQBQQQBQQB",
    "qQQBQQBBQB.",
    ".BBBBBBBBB.",
]
TEAL_CRYSTALS = [row.replace("q", "t").replace("Q", "T").replace("B", "C") for row in BLUE_CRYSTALS]

# Flowers that glow like embers, in the red lava caves
EMBER_FLOWERS = [
    "..y......y.",
    ".yoy....yoy",
    "..o..y...o.",
    "..R.yoy..R.",
    "..R..o..R..",
    "...R.R.R...",
    "....RRR....",
    ".....R.....",
]

# A fern on the cave floor
FERN = [
    ".j.......j.",
    "gGg..j..gGg",
    "..Gg.g.gG..",
    ".gGg.Gg.Gg.",
    "...gGGgGg..",
    "..gGgGGg...",
    "....GGG....",
    ".....G.....",
]

# A fern hanging down from the roof, or from under a ledge
HANGING_FERN = [
    "..G..G..G..",
    ".gGggGggGg.",
    ".gG.gGg.Gg.",
    "gG..gGg..Gg",
    "gG...Gg..Gg",
    "G...gG....G",
    "g....Gg...g",
    ".....G.....",
    ".....g.....",
]

# A vine you can climb (V): thick and bright, with big leaves, so it looks different
# from the thin dark vines that just hang from the roof. One picture is one block.
# The stem ends where it starts, so vine blocks join up when they're stacked.
# The top block has a bunch of leaves where the vine is tied on.
VINE_TOP = [
    ".gjj..jggG.jjg..",
    "GggjjgjjgGgjjggG",
    ".GGggjgjgjggGG..",
    "...GGGjggGGG....",
    "......jJgGG.....",
    ".......jJgG...jj",
    ".......jgJG.gjjg",
    ".......jggGGggGG",
    "......jggG..GG..",
    "......jJgG......",
    "jj....jgJG......",
    "ggjg.jggG.......",
    "GGggGjggG...jjg.",
    "..GG.jJgG.gjjgG.",
    ".....jgJGGggGG..",
    "......jggGGG....",
]
VINE = [
    "......jggG......",
    "gjj...jJgG......",
    "Gggjg.jgJG......",
    ".GGggG.jggG.....",
    "...GG..jggG.....",
    ".......jJgG...jj",
    ".......jgJG.gjjg",
    ".......jggGGggGG",
    "......jggG..GG..",
    "......jJgG......",
    "jj....jgJG......",
    "ggjg.jggG.......",
    "GGggGjggG...jjg.",
    "..GG.jJgG.gjjgG.",
    ".....jgJGGggGG..",
    "......jggGGG....",
]

CHEST = [
    "................",
    "................",
    "................",
    "..kkkkkkkkkkkk..",
    ".knnnnnnnnnnnnk.",
    ".knNnnnnnnnnNnk.",
    ".knnnnnnnnnnnnk.",
    ".kEEEEEyyEEEEEk.",
    ".kNNNNNyyNNNNNk.",
    ".knnnnnkknnnnnk.",
    ".knNnnnnnnnnNnk.",
    ".knnnnnnnnnnnnk.",
    ".knNnnnnnnnnNnk.",
    ".kEEEEEEEEEEEEk.",
    ".kkkkkkkkkkkkkk.",
    "................",
]

CHEST_OPEN = [
    "................",
    "..kkkkkkkkkkkk..",
    ".knnnnnnnnnnnnk.",
    ".knNnnnnnnnnNnk.",
    ".kNNNNNNNNNNNNk.",
    ".kkkkkkkkkkkkkk.",
    ".kNyywyyyyywyNk.",
    ".kEEEEEEEEEEEEk.",
    ".kNNNNNkkNNNNNk.",
    ".knnnnnnnnnnnnk.",
    ".knNnnnnnnnnNnk.",
    ".knnnnnnnnnnnnk.",
    ".knNnnnnnnnnNnk.",
    ".kEEEEEEEEEEEEk.",
    ".kkkkkkkkkkkkkk.",
    "................",
]

# ---------------------------------------------------------------------------
# Nightfall Hollow and the Shadow King
# ---------------------------------------------------------------------------

# The Shadow King himself (24 x 24): dark armor, a purple cape, and glowing eyes
SHADOW_KING = [
    "......k..k.kk.k..k......",
    ".....kPk.kPkkPk.kPk.....",
    ".....kPPkPPPPPPkPPk.....",
    ".....kvkkkkkkkkkkvk.....",
    "......kEEEEEEEEEEk......",
    "......kEkkkkkkkkEk......",
    "......kEkvvkkvvkEk......",
    "......kEkkkkkkkkEk......",
    ".......kEEEEEEEEk.......",
    "....kkkkEEEEEEEEkkkk....",
    "...kPPkEEEEvvEEEEkPPk...",
    "..kPPPkEEEEvvEEEEkPPPk..",
    "..kPPkEEEEEEEEEEEEkPPk..",
    ".kPPPkEEkkkkkkkkEEkPPPk.",
    ".kPPkkEEEEEEEEEEEEkkPPk.",
    ".kPPPkEEEEEEEEEEEEkPPPk.",
    ".kPPPkEEEEEkkEEEEEkPPPk.",
    ".kPPPkEEEEk..kEEEEkPPPk.",
    "kPPPPkEEEEk..kEEEEkPPPPk",
    "kPPPPkEEEk....kEEEkPPPPk",
    "kPPPPPkEEk....kEEkPPPPPk",
    "kPPPPPkkkk....kkkkPPPPPk",
    ".kkkkkkkkk....kkkkkkkkk.",
    "........................",
]

# When the Shadow King gets ANGRY, his purple turns red: it's the same picture,
# with every dark purple "P" swapped for dark red "R", and his violet eyes "v" for orange "o"
ANGRY_SHADOW_KING = [row.replace("P", "R").replace("v", "o") for row in SHADOW_KING]

# The Shadow King's big sword (it glows when he's about to slash!)
SHADOW_SWORD = [
    "...k...",
    "..kvk..",
    "..kvk..",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    ".kvPvk.",
    "kkkkkkk",
    "kYYYYYk",
    "kkkPkkk",
    "..kNk..",
    "..kNk..",
    "..kNk..",
    "..kYk..",
    "..kkk..",
]

# Sunfang, the sword made from three diamonds (16 x 16)
SUNFANG = [
    "..............kw",
    ".............kwy",
    "............kwyk",
    "...........kwyk.",
    "..........kwyk..",
    ".........kwyk...",
    "........kwyk....",
    ".......kwyk.....",
    "......kwyk......",
    "..k..kwyk.......",
    "..kckwyk........",
    "...kcck.........",
    "...kncck........",
    "..knk.kck.......",
    ".knk....k.......",
    "kyk.............",
]

# A twisted dead tree in Nightfall Hollow
DEAD_TREE = [
    "................",
    "....k......k....",
    "...ke.k...kek...",
    "....ke.k.kek....",
    ".k...kekeek..k..",
    ".ke...keek..kek.",
    "..ke..keek.kek..",
    "...keekeekeek...",
    ".....keeeek.....",
    "......keek......",
    "......keek......",
    "......keek......",
    ".....keeeek.....",
    "....keekkeek....",
    "................",
    "................",
]

# A glowing shrine: a safe place in Nightfall Hollow
SHRINE = [
    "................",
    ".......vv.......",
    "......vwvv......",
    ".....vwvvvv.....",
    "......vvvv......",
    ".......vv.......",
    "................",
    ".....kkkkkk.....",
    "....kllllllk....",
    ".....kelelk.....",
    ".....kleelk.....",
    ".....kelelk.....",
    ".....kleelk.....",
    "....kllllllk....",
    "...kkkkkkkkkk...",
    "................",
]

# A Shadow Guardian: a horned shadow knight with glowing violet eyes and a shield. It sits on a dark shrine.
GUARDIAN = [
    "................",
    "..k..kkkkkk..k..",
    "..kk.kEEEEk.kk..",
    "...kkkEEEEkkk...",
    "....kEEEEEEk....",
    "....kEkvvkEk....",
    "....kEkkkkEk....",
    "....kEEEEEEk....",
    "..kkkkEEEEkkkk..",
    ".kPPkEEvvEEkppk.",
    ".kPPkEEvvEEkppk.",
    ".kPPkEEEEEEkppk.",
    "..kkkkEEEEkkkk..",
    "....kEEkkEEk....",
    "....kEEk.kEEk...",
    "....kkkk.kkkk...",
]

# A dark shrine: the same stone as a glowing shrine, but cold and out. Beat its Guardian, then light it!
DARK_SHRINE = (["................"] * 5
               + [".......kk.......", "......kEEk......"]
               + [row.replace("l", "E").replace("e", "E") for row in SHRINE[7:]])

# A lit beacon: the shrine with a tall golden flame
LIT_BEACON = ([
    "................",
    ".......y........",
    "......yoy.......",
    ".....yowoy......",
    ".....yowoy......",
    "......yoy.......",
    ".......y........",
] + SHRINE[7:])

# A Sun Shard: a piece of the Sun Gem for Sunfang's hilt
SUN_SHARD = [
    "................",
    ".......kk.......",
    "......kyyk......",
    ".....kywwyk.....",
    "....kyywoyyk....",
    "...kyywoooyyk...",
    "...kywoooooyk...",
    "...kyyooooyyk...",
    "....kyyooyyk....",
    ".....kyyyyk.....",
    "......kyyk......",
    ".......kk.......",
    "................",
    "................",
    "................",
    "................",
]

# The Shadow Warden: a Guardian with burning red eyes and a dark red cape
WARDEN = [row.replace("P", "R").replace("v", "o") for row in GUARDIAN]

# Wren, a friendly ghost who lost her lanterns
WREN = [
    "................",
    ".....kkkkkk.....",
    "....kwwwwwwk....",
    "...kwwwwwwwwk...",
    "...kwkkwwkkwk...",
    "...kwkkwwkkwk...",
    "...kwwwwwwwwk...",
    "...kwwwkkwwwk...",
    "...kwwwwwwwwk...",
    "...kwwwwwwwwk...",
    "..kwwwwwwwwwwk..",
    "..kwwwwwwwwwwk..",
    "..kwwwwwwwwwwk..",
    "..kwwkwwwwkwwk..",
    "...k.kwwwwk.k...",
    "................",
]

# One of Wren's lost lanterns
LANTERN = [
    "................",
    ".......kk.......",
    "......k..k......",
    ".....kkkkkk.....",
    "....kyyyyyyk....",
    "....kywwwwyk....",
    "....kywwwwyk....",
    "....kyywwyyk....",
    "....kyyyyyyk....",
    ".....kkkkkk.....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]

# The Shadow King's castle
CASTLE = [
    "..k.k......k.k..",
    "..kkk......kkk..",
    "..kEk..k.k.kEk..",
    "..kEk..kkk.kEk..",
    "..kvk..kEk.kvk..",
    "..kEk..kvk.kEk..",
    ".kkEkkkkEkkkEkk.",
    ".kEEEEEEEEEEEEk.",
    ".kEvEEEEEEEEvEk.",
    ".kEEEEEkkEEEEEk.",
    ".kEEEEkPPkEEEEk.",
    ".kEvEEkPPkEEvEk.",
    ".kEEEEkPPkEEEEk.",
    ".kkkkkkkkkkkkkk.",
    "................",
    "................",
]


# ---------------------------------------------------------------------------
# Phase 2 monsters (phase2/monsters.py). They look right; the game flips them to look left.
# ---------------------------------------------------------------------------

# A little green Slime that wobbles around Home Meadow. The weakest monster of all.
SLIME = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "......kkkk......",
    "....kkggggkk....",
    "...kgggwggggk...",
    "..kggwwgggkwgk..",
    "..kgggggggkkgk..",
    ".kggggggggggggk.",
    ".kgGgggggggggGk.",
    ".kGGGgggggggGGk.",
    "..kkkkkkkkkkkk..",
    "................",
]

# A desert Scorpion: big pincers in front, its stinger curled up over its back.
SCORPION = [
    "................",
    "...kkk..........",
    "..koook.........",
    "..kok.ok........",
    "...k..ok........",
    "......ok........",
    ".......ok...k.k.",
    "........k..koko.",
    "...kkkkkkkk.kok.",
    "..koooooookkok..",
    ".koYoYoYooookkk.",
    ".koooooookrokok.",
    "..kkkkkkkkkkkok.",
    "..k.k.k.k.k..k..",
    ".k.k.k.k.k......",
    "................",
]

# A Frost Wolf from the snowy peaks: pale fur, icy blue eyes, and fast!
FROST_WOLF = [
    "................",
    "...........k.k..",
    "..........klkl..",
    "..........klllk.",
    ".........klllckk",
    "k........kllllkl",
    "lk.......klllkkk",
    ".lkkkkkkkklllk..",
    "..klllllllllk...",
    "..klllllllllk...",
    "..kllellllelk...",
    "..klk.klk.klk...",
    "..klk.klk.klk...",
    "..kk..kk..kk....",
    "................",
    "................",
]

# A Bog Lurker rises out of the swamp mud, dripping weeds. Tough: your hits do 1 less damage.
BOG_LURKER = [
    "................",
    "....kkkkkkk.....",
    "...kNnnnnnNk....",
    "..kNnyknnyknk...",
    "..kNnnnnnnnnk...",
    "..kNnkkkkknNk...",
    "..kGnnwnwnnGk...",
    ".kGgGNnnnNGgGk..",
    ".kGkGnnnnnGkGk..",
    ".kgkNnnGnnNkgk..",
    ".kGkNnGnnnNkGk..",
    "...kNnnnGnNk....",
    "...kNNnnnNNk....",
    "..kNNNNNNNNNk...",
    ".kNNNNNNNNNNNk..",
    "................",
]

# ---------------------------------------------------------------------------
# PEOPLE for Phase 2 (phase2/people.py puts them on the map; phase2/data/people.json says who
# looks like what). They face you, like the Hero on the map. Want a new look? Copy one, change the
# letters and add it to PEOPLE_ART below.
# ---------------------------------------------------------------------------

# A farmer in a big straw hat and blue overalls
FARMER = [
    "................",
    "......kkkk......",
    "....kkyyyykk....",
    "...kyyyyyyyyk...",
    ".kkYYYYYYYYYYkk.",
    "kyyyyyyyyyyyyyyk",
    ".kkksssssssskkk.",
    "...kskssssksk...",
    "...kssssssssk...",
    "...ksssRRsssk...",
    "..kkbrrrrrrbkk..",
    "..krbbbbbbbbrk..",
    "..ksbbbybbbbsk..",
    "...kbbbbbbbbk...",
    "...kbbbkkbbbk...",
    "..kNNNk..kNNNk..",
]

# The shopkeeper: hair in a bun, a green dress and a white apron
SHOPKEEPER = [
    "......kkkk......",
    ".....khhhhk.....",
    "....kkhhhhkk....",
    "...khhhhhhhhk...",
    "...khsssssshk...",
    "...khsksskshk...",
    "...khsssssshk...",
    "...kssssssssk...",
    "...ksssRRsssk...",
    "....kksssskk....",
    "...kkggggggkk...",
    "..kgggwwwwgggk..",
    "..ksggwwwwggsk..",
    "...kgwwwwwwgk...",
    "...kggggggggk...",
    "....kkk..kkk....",
]

# The blacksmith: bald, a big bushy beard, strong arms and a leather apron
BLACKSMITH = [
    "................",
    ".....kkkkkk.....",
    "....kssssssk....",
    "...kssssssssk...",
    "...kskssssksk...",
    "...kssssssssk...",
    "...ksNNNNNNsk...",
    "...kNNNRRNNNk...",
    "....kNNNNNNk....",
    ".kkkkkNNNNkkkkk.",
    "kssskEnnnnEksssk",
    "kssskEnnnnEksssk",
    ".kkkkEnnnnEkkkk.",
    "....kEnnnnEk....",
    "....kEEkkEEk....",
    "...kkkk..kkkk...",
]

# The guide: a green traveller's cap with a red feather, and a green tunic
GUIDE = [
    "...........r....",
    "......kkkk.r....",
    ".....kggggkr....",
    "....kgggggGk....",
    "...kggggggggk...",
    "..kkGGGGGGGGkk..",
    "...khsssssshk...",
    "...kskssssksk...",
    "...kssssssssk...",
    "...ksssRRsssk...",
    "....kkGGGGkk....",
    "..kgggnyyngggk..",
    "..ksggggggggsk..",
    "...kggggggggk...",
    "...kNNNkkNNNk...",
    "..kNNNk..kNNNk..",
]

# An old wizard: a tall purple hat with a star, and a long white beard
WIZARD = [
    ".......kk.......",
    "......kppk......",
    ".....kpppk......",
    ".....kpypppk....",
    "....kppppppk....",
    "..kkPPPPPPPPkk..",
    "...kssssssssk...",
    "...kskssssksk...",
    "...kwwsssswwk...",
    "...kwwwwwwwwk...",
    "..kpkwwwwwwkpk..",
    "..kppkwwwwkppk..",
    "..ksppkwwkppsk..",
    "...kpppppppPk...",
    "...kppppppppk...",
    "...kkkkkkkkkk...",
]

# A kid in a red cap and a yellow shirt (smaller than the grown-ups)
KID = [
    "................",
    "................",
    "................",
    "................",
    "......kkkk......",
    ".....krrrrk.....",
    "....krrrrrrkk...",
    "....khsssshk....",
    "....kskssksk....",
    "....kssRRssk....",
    ".....kyyyyk.....",
    "....kyyyyyyk....",
    "....ksyyyysk....",
    ".....kbbbbk.....",
    ".....kbkkbk.....",
    ".....kk..kk.....",
]

# A little orange cat, sitting
CAT = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "....k....k......",
    "...kok..kok.....",
    "...koooooook....",
    "...kokoookok....",
    "...kooorooook...",
    "....kooooook....",
    "...koowwwook....",
    "...koowwwook.kk.",
    "...koooooookok..",
    "....kkkkkkkk....",
]

# More townsfolk, made by changing the colors of the ones above
VILLAGER = [row.replace("h", "y").replace("g", "b").replace("G", "B") for row in SHOPKEEPER]
FISHER = [row.replace("y", "c").replace("Y", "C").replace("r", "o") for row in FARMER]

# Which picture goes with each "look" in phase2/data/people.json
PEOPLE_ART = {
    "farmer": FARMER,
    "shopkeeper": SHOPKEEPER,
    "blacksmith": BLACKSMITH,
    "guide": GUIDE,
    "wizard": WIZARD,
    "kid": KID,
    "cat": CAT,
    "villager": VILLAGER,
    "fisher": FISHER,
}

# Which picture to use for each monster in rules.MONSTER_TYPES
MONSTER_ART = {
    "Zombie": ZOMBIE,
    "Skeleton": SKELETON,
    "Ember Skull": EMBER_SKULL,
    "Spider": SPIDER,
    "Sea Serpent": SERPENT,
    "Guardian": GUARDIAN,
    "Warden": WARDEN,
    "Slime": SLIME,                 # (these four only live in Phase 2: phase2/monsters.py)
    "Scorpion": SCORPION,
    "Frost Wolf": FROST_WOLF,
    "Bog Lurker": BOG_LURKER,
}


def check_art():
    """Make sure every picture is a neat rectangle with known colors."""
    for name, art in list(globals().items()):
        if name.isupper() and isinstance(art, list):
            width = len(art[0])
            for i, row in enumerate(art):
                if len(row) != width:
                    raise ValueError("%s row %d is %d wide, expected %d" % (name, i, len(row), width))
                for ch in row:
                    if ch != "." and ch not in COLORS:
                        raise ValueError("%s uses unknown color letter '%s'" % (name, ch))


check_art()
