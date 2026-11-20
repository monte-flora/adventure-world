"""
Adventure World - graphics, sound and controls.

Run it with:
    python3 game.py

The rules of the game live in rules.py and the pixel art lives in sprites.py.
This file just draws everything and listens to the keyboard and mouse.
"""

import argparse
import math
import os
import random
import sys
import threading
from array import array

import pygame

import castle
import caves
import phase2
import rules
import sprites
import throne
import tutorial

# Playing in a web browser? (pygbag turns the game into a web page, and then Python says "emscripten")
IN_BROWSER = sys.platform == "emscripten"
WEB_MUSIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_music")

# ---------------------------------------------------------------------------
# Screen layout
# ---------------------------------------------------------------------------
TILE = 64
CAVE_SCALE = 5                      # in caves, pictures are drawn bigger (5 screen pixels per art pixel)
WALK_STEP = 0.5                     # in caves, the Hero's legs move to the next walking picture every half block he walks
BATTLE_PAUSE = 0.6                  # in a map fight, A (and R and E) wait this long (seconds) at the start and after every turn
MAP_STEP_TIME = 0.2                 # on the world map, the Hero shows a walking picture this long (seconds) after each step
CLIMB_STEP = 0.5                    # and on a ladder, his arms take turns every half block he climbs
WALL_STEP = 0.3                     # on a climbing wall (%), he goes hand over hand: a new picture every 0.3 blocks
_MAP = rules.parse_map(rules.WORLD_MAP)
MAP_W = TILE * len(_MAP[0])         # the whole world, in pixels
MAP_H = TILE * len(_MAP)
VIEW_COLS = 18                      # how many tiles you can see at once.
VIEW_ROWS = 11                      # The camera scrolls to show the rest!
VIEW_W = min(MAP_W, TILE * VIEW_COLS)
VIEW_H = min(MAP_H, TILE * VIEW_ROWS)
PANEL_W = 300
LOG_H = 132
WIDTH = VIEW_W + PANEL_W
HEIGHT = VIEW_H + LOG_H
FPS = 60

# Colors
BG = (22, 24, 34)
PANEL_BG = (34, 37, 52)
LOG_BG = (26, 28, 40)
CAVE_BG = (30, 26, 36)
# How each kind of cave looks: rock color, back wall, little crystal specks, and things floating in the air.
# (The crystal, lava and moss caves get the rest of their colors from CAVE_COLORS, below.)
CAVE_THEMES = {
    "stone":   {"rock": (82, 74, 90), "back": (30, 26, 36), "blobs": [(38, 33, 46), (45, 39, 53)],
                "specks": [(90, 230, 240), (200, 120, 255)], "motes": None},
    "crystal": {"rock": (58, 70, 108), "back": (16, 21, 40),       # snowflakes and sparkles drifting down
                "motes": ([(230, 244, 255), (230, 244, 255), (120, 235, 255)], "drift")},
    "lava":    {"rock": (58, 50, 52), "back": (31, 17, 15),        # embers rising
                "motes": ([(255, 150, 60), (255, 200, 90), (255, 110, 40)], "rise")},
    "moss":    {"rock": (82, 94, 80), "back": (24, 32, 28),        # glowing spores wandering about
                "motes": ([(130, 240, 214), (214, 246, 110)], "wander")},
    "castle":  {"rock": (78, 74, 100), "back": (32, 28, 46), "blobs": [], "specks": [(255, 190, 90), (190, 140, 255)],
                "motes": None},
    # The dark caves under the Mines in Nightfall Hollow: purple-black rock, violet wisps drifting about
    "shadow":  {"rock": (58, 46, 78), "back": (14, 10, 24), "blobs": [(22, 16, 36), (28, 20, 44)],
                "specks": [(190, 120, 255), (255, 214, 90)],
                "motes": ([(190, 120, 255), (150, 90, 220), (255, 214, 90)], "wander")},
}
# The back wall of a stone cave (paint_stone_back): every color is dark, so the rock in front stands out
STONE_BACK = {
    "layers": [(30, 26, 36), (36, 31, 43), (26, 22, 32), (41, 36, 48)],     # layers of rock
    "seam": (23, 19, 28), "crack": (17, 14, 21),
    "mortar": (22, 19, 27), "bricks": [(44, 38, 50), (40, 35, 46), (47, 41, 52)], "shine": (52, 46, 58),
    "wood": ((26, 19, 18), (45, 33, 27), (56, 42, 32)),                  # old wooden mine props
    "roots": (40, 30, 27),
    "pebbles": [(42, 37, 48), (46, 41, 52), (24, 20, 29)],
    "specks": [(60, 110, 120), (96, 70, 120)],                          # tiny crystals, glowing faintly
    "fossil": (50, 46, 52),
}
FOSSILS = [                                 # little fossils in the stone: a snail shell and a fish
    [".ooo.",
     "o...o",
     "o.o.o",
     "o..o.",
     ".oo.."],
    ["o..o.o.o..",
     ".oooooooo.",
     "o..o.o.o.o"],
]
BEACON_BRIGHTER = 30                # every lit beacon makes Nightfall Hollow this much less dark (out of 190)
LEDGE_WOOD = (150, 102, 56)         # the wooden ledges in caves...
CRUMBLY_WOOD = (176, 140, 96)       # ...and the crumbly ones (lighter, with cracks)
CAVE_LOOKS = 3                      # every kind of block comes in this many looks, so they don't all look the same
MOSS_GRASS = 0.6                    # how often grass grows on a rock top in a mossy cave (1 = on every one)
LEDGE_GRASS = 0.45                  # and how often on a ledge

# The moss, crystal and lava caves are painted in chunky pixels, like the gems and chests:
# one chunky pixel is ART_PIXEL x ART_PIXEL screen pixels, so a block is 16 of them across.
ART_PIXEL = 4
ROCK_PICTURE = 12                   # the rock is one big picture, this many blocks across and down, that repeats
HANGING = 0.55                      # how often something hangs from the roof (vines, roots, icicles...)
FLOOR_THINGS = 0.4                  # how often something grows on a rock top in an ice or lava cave
DRIPS = 0.05                        # how often water drips from a spot on the roof
LAVA_PICTURES = 16                  # the lava moves like a flip book with this many pages (8 a second)
DEEP_LAVA = (176, 46, 22)           # the dark red of deep lava, down at the bottom of a pool
CAVE_COLORS = {
    "moss": {
        # the back wall: far away (light), in between, and close up (dark), how wide its rocky teeth are,
        # and what hangs down far away
        "far": (48, 62, 54), "far_rock": (40, 53, 46), "middle": (32, 43, 37), "near": (24, 32, 28),
        "teeth": (8, 18), "far_hanging": "vines",
        # the rock: stone, its darker and lighter patches, cracks, edges and wet streaks
        "stone": (82, 94, 80), "dark": (72, 84, 71), "light": (92, 104, 89), "crack": (56, 66, 58),
        "edge": (52, 62, 54), "streak": (66, 82, 86),
        "patch": (50, 82, 46), "patch_light": (72, 112, 58),     # moss growing on the rock
        "glow": (130, 240, 214), "glow_dim": (92, 150, 134),     # little glowing specks
        "top": [(156, 212, 98), (104, 166, 66), (66, 120, 52)],   # moss on top: light, middle, dark
        "puddle": [(70, 190, 200), (160, 250, 240)],             # a glowing puddle and its shine
        # what grows on the floor and hangs from the roof (one is picked at random)
        "on_floor": ["grass", "grass", "grass", "fern", "mushrooms", "mushrooms", "sprout"],
        "on_roof": ["vine", "vine", "moss", "roots", "fern"],
        "plants": [(110, 190, 90), (84, 160, 70), (150, 210, 100)],
        "vine": [(54, 104, 48), (90, 160, 70), (130, 200, 90)],  # vine stem, leaves and new leaves
        "root": [(96, 66, 44), (128, 90, 58)],                   # roots coming through the roof
        "drip": (150, 220, 240),                                 # drops of water
    },
    "crystal": {
        "far": (36, 46, 80), "far_rock": (29, 38, 68), "middle": (23, 30, 55), "near": (16, 21, 40),
        "teeth": (4, 10), "far_hanging": None,                   # thin icicles far away
        "stone": (58, 70, 108), "dark": (51, 62, 97), "light": (67, 80, 120), "crack": (38, 47, 78),
        "edge": (32, 40, 68), "streak": (90, 120, 172),          # streaks of ice in the rock
        "patch": (84, 112, 162), "patch_light": (150, 188, 232), # frost on the rock
        "glow": (120, 235, 255), "glow_dim": (78, 136, 188),
        "top": [(240, 248, 255), (200, 224, 250), (128, 166, 222)],   # snow: white, pale and its blue shadow
        "icicles": [(176, 224, 252), (110, 168, 230)],           # little icicles hanging from the snow
        "puddle": [(120, 190, 236), (230, 250, 255)],            # a frozen puddle
        "on_floor": ["crystals", "crystals", "snow", "snow", "sparkle"],
        "on_roof": ["icicles", "icicles", "icicles", "crystals"],
        "drip": (190, 230, 255),
    },
    "lava": {
        "far": (72, 37, 28), "far_rock": (60, 31, 24), "middle": (45, 24, 20), "near": (31, 17, 15),
        "teeth": (10, 22), "far_hanging": "roots",
        # the rock is made of round stones: black lava rock, and some red-brown rock
        "cobbles": [(58, 50, 52), (66, 56, 56), (50, 43, 46), (86, 54, 46)],
        "stone": (58, 50, 52), "crack": (28, 21, 23), "edge": (22, 16, 18),
        "hot_cracks": [(170, 62, 28), (240, 124, 44)],           # cracks glowing hot between the stones
        "glow": (255, 150, 60), "glow_dim": (150, 70, 40),
        "top": [(196, 74, 58), (146, 44, 42), (96, 28, 32)],      # red moss
        "puddle": None,
        "on_floor": ["grass", "grass", "grass", "ember flowers", "pebbles"],
        "on_roof": ["moss", "moss", "roots", "roots", "vine"],
        "plants": [(170, 56, 44), (128, 40, 38), (206, 90, 60)],  # red grass
        "vine": [(90, 30, 30), (150, 46, 40), (200, 80, 56)],
        "root": [(40, 28, 27), (66, 46, 42)],
    },
}
# Swinging vines (R) in caves without their own vine colors: stem, leaves and new leaves
SWING_VINE_COLORS = {"stone": [(70, 140, 50), (100, 190, 70), (160, 230, 110)],
                     "crystal": [(64, 118, 112), (118, 190, 182), (200, 244, 240)],     # frosty
                     "shadow": [(70, 60, 104), (112, 96, 160), (170, 150, 220)],
                     "castle": [(120, 84, 50), (96, 140, 70), (150, 196, 100)]}
# Slippery ice (I) and the healing springs (u) look the same in all three of those caves.
# The ice is clear sky blue, brighter than the frost on the rock, with a shiny top: it's slippery!
ICE_COLORS = {"ice": (132, 210, 244), "deep": (96, 178, 232), "light": (190, 238, 255),
              "shine": (244, 252, 255), "edge": (50, 110, 180)}
SPRING_WATER = {"deep": (52, 150, 236), "water": (92, 204, 255), "light": (176, 240, 255),
                "shine": (250, 255, 255), "glow": (120, 220, 255)}
# The bowl of a healing spring, from the side (the bottom 8 rows of its block). r = rim, s = stone,
# d = shadow, . = inside, where the water goes. Its colors come from the cave's own rock.
SPRING_BOWL = [
    "rr............rr",
    "srr..........rrs",
    "ssr..........rss",
    "sssr........rsss",
    "ssssr......rssss",
    "dssssrrrrrrssssd",
    ".dssssssssssssd.",
    "..dddddddddddd..",
]
SPRING_FULL = 4                     # the water in a spring is this many chunky pixels deep when it's full
TEXT = (232, 234, 242)
DIM = (150, 156, 178)
YELLOW = (255, 214, 90)
ARMOR_COLOR = (200, 210, 228)       # silver
WATER_BLUE = (110, 215, 255)
ORANGE = (255, 150, 50)
RED = (240, 80, 80)
GREEN = (110, 220, 120)
KIND_COLORS = {
    "info": (222, 224, 234),
    "good": (120, 230, 130),
    "bad": (255, 120, 110),
    "loot": (110, 215, 255),
    "quest": (255, 214, 90),
}
NIGHT_MINIMAP_COLORS = {"H": (200, 140, 255), "F": (58, 48, 72), "G": (84, 70, 104), "W": (24, 26, 52), "C": (240, 170, 255), "M": (90, 90, 100),
                        "D": (120, 60, 60), "L": (255, 214, 90), "+": (176, 132, 82), "N": (200, 240, 255), "Q": (255, 220, 120), "X": (40, 36, 54), "=": (150, 98, 52), "#": (176, 132, 82), "T": (230, 176, 60)}
MINIMAP_COLORS = {"H": (214, 160, 96), "F": (40, 104, 44), "G": (112, 186, 92), "M": (128, 128, 138),
                  "W": (52, 108, 200), "P": (190, 110, 255), "R": (176, 132, 82), "X": (104, 98, 100),
                  "I": (186, 224, 246), "B": (70, 112, 82), "V": (214, 120, 70), "L": (255, 214, 90),
                  "T": (230, 176, 60), "+": (176, 132, 82), "=": (150, 98, 52), "#": (176, 132, 82),
                  "S": (128, 128, 138)}

# How the open ground looks in each land of the home world: its colour, and the two colours of the specks on it.
# Any land that isn't here has green grass (GRASS).
GRASS = [(86, 164, 74), (72, 146, 62), (104, 182, 88)]
LAND_GROUND = {
    "Frosty Corner":    [(228, 236, 246), (206, 218, 236), (248, 251, 255)],    # snow
    "Ember Canyon":     [(186, 122, 84), (166, 104, 72), (206, 142, 100)],      # hot red sand
    "Misty Marsh":      [(80, 128, 94), (68, 112, 84), (96, 144, 106)],         # dark, damp grass
    "Old Ruins":        [(124, 154, 96), (108, 138, 84), (142, 170, 110)],      # dry, faded grass
    "Whispering Woods": [(70, 142, 70), (58, 124, 60), (86, 158, 82)],          # shady grass
}
# The landmark (L) in each land, from sprites.py
LANDMARK_ART = {"Windmill": "WINDMILL", "Queen Oak": "QUEEN_OAK", "Watchtower": "WATCHTOWER", "Frost Peak": "FROST_PEAK",
                "Lighthouse": "LIGHTHOUSE", "Frog's Hut": "FROG_HUT", "Dragon Bones": "DRAGON_BONES"}
RED_ROCK = {"e": "m", "E": "M", "l": "o"}      # the grey rock, painted red for Ember Canyon
PATH_DIRT = [(164, 122, 78), (138, 100, 62), (192, 152, 104)]   # the path's dirt: middle, dark and light
PATH_EDGE = (120, 136, 72)          # trodden grass along the sides of the path
GRASS_TUFT = (66, 136, 56)          # the little tufts of grass in a field

# How each Mine looks on the map, so you can tell what kind of cave is down there:
# its rock, the pebbles and their shine, the sparkle by the door, and what grows on it
MINE_LOOKS = {
    "stone":   {"rock": (126, 126, 134), "pebble": (106, 106, 116), "shine": (158, 158, 168), "sparkle": (90, 230, 240)},
    "moss":    {"rock": (108, 122, 100), "pebble": (90, 104, 84), "shine": (140, 156, 128), "sparkle": (130, 240, 214),
                "moss": [(66, 120, 52), (104, 166, 66), (156, 212, 98)]},         # green moss: dark, middle, light
    "lava":    {"rock": (134, 102, 94), "pebble": (114, 82, 76), "shine": (166, 132, 120), "sparkle": (255, 170, 70),
                "moss": [(120, 24, 34), (178, 40, 48), (232, 92, 76)]},           # red moss
    "crystal": {"rock": (116, 128, 162), "pebble": (98, 110, 146), "shine": (156, 172, 206), "sparkle": (120, 235, 255),
                "ice": [(96, 176, 230), (176, 228, 255), (255, 255, 255)]},       # ice crystals: blue, pale, white
    "shadow":  {"rock": (66, 54, 88), "pebble": (50, 40, 70), "shine": (104, 88, 134), "sparkle": (255, 214, 90)},
}
ORE_DIAMOND = (90, 230, 240)        # diamond ore sparkles cyan...
ORE_SHARD = (255, 206, 80)          # ...and a Sun Shard glows gold

MOVE_KEYS = {
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
}

# In a cave, running and jumping read the keyboard every frame instead
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
JUMP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
UP_KEYS = (pygame.K_UP, pygame.K_w)          # these also climb ladders
SPACE_KEYS = (pygame.K_SPACE,)               # this jumps you off a ladder or a ledge
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
USE_KEYS = (pygame.K_r,)
SHOOT_KEYS = (pygame.K_f,)

TILE_HINTS = {
    "F": [("SPACE", "search for food"), ("T", "chop wood"), ("C", "craft: sword, pickaxe, house...")],
    "G": [("C", "craft a house here"), (None, "Open grass: no trees to chop")],
    "W": [("Arrows", "row your boat")],
    "M": [("SPACE", "explore the cave")],
    "H": [("SPACE", "rest and heal")],
    "N": [("SPACE", "talk to Wren the ghost")],
    "Q": [(None, "A lost lantern!")],
    "D": [(None, "A dark shrine: no healing"), ("SPACE", "light the beacon"), (None, "Beat its Guardian first")],
    "P": [("SPACE", "enter the Portal")],
    "R": [(None, "Monsters won't chase you"), (None, "Skeletons can't shoot you"), (None, "No bad luck (or good luck)")],
    "L": [("SPACE", "climb up and look around"), (None, "Monsters can't reach you here")],
    "T": [("SPACE", "open the treasure chest")],
    "+": [("SPACE", "read the sign")],
    "I": [(None, "Slippery ice: you slide"), (None, "until you bump into something")],
    "B": [(None, "Tall reeds: monsters can't see you"), (None, "Watch out for the mud!")],
    "V": [(None, "Steam vent! It puffs every %d turns" % rules.VENT_EVERY), (None, "A little wisp = about to blow")],
    "#": [(None, "The bridge over the Icy River")],
    "S": [("SPACE", "explore the secret cave")],
}
CAVE_HINTS = [("Arrows", "run left and right"), ("SPACE", "jump (hold = higher)"),
              ("R", "dig, open chests, fight"), ("F", "shoot", "C", "craft"),
              ("Down + R", "dig the floor"), ("Up/Down", "climb ladders, walls"),
              (None, "Walk out on the left to leave")]
# What looks like rock when we paint the cave: a secret wall (F) does, an iron gate (G) doesn't
LOOKS_SOLID = caves.SOLIDS.replace(caves.GATE, "") + caves.SECRET
CASTLE_THINGS = "EDKLlu+"           # doors, keys, levers, fountains and light shards (castle.py explains the letters)
CASTLE_HINTS = CAVE_HINTS[:2] + [("R", "dig, chests, levers, fight")] + CAVE_HINTS[3:-1] + [(None, "Find the key or the lever!")]
THRONE_THINGS = "nYS"               # in the throne room: the healing spring, his throne, and the door you came in by
THRONE_HINTS = [("Arrows", "run", "SPACE", "jump"), ("R", "Sunfang", "F", "shoot"), (None, "Glowing sword? Get away!"),
                (None, "Jump over his fireballs!"), (None, "Hurt? Up the ladder to heal")]
KING_SCALE = 6                      # the Shadow King is drawn this big (6 screen pixels per art pixel)

# Tip bubbles (the words, and when each one shows, are in tutorial.py)
TIP_W = 440                         # how wide a bubble is
TIP_BG = (38, 34, 54)               # the bubble's color (the same as the pop-up boxes)
TIP_DIM = (120, 120, 136)           # everything else gets this much darker while a tip shows
TIP_READ_TIME = 0.5                 # keys wait this long after a bubble opens, so you can't skip it by accident
TIP_GAP = 1.5                       # after you close a bubble, the next one waits at least this long
                                    # (and on the world map, until you've taken a step too)
TIP_LOOK_EVERY = 0.25               # how often the game checks if a tip fits (in seconds)
GAME_MODES = {"classic": "Classic", "phase2": "Phase 2", "continue": "Load"}   # the title screen's choice
TIP_CLOSE_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE)

# The picture for each level-up power on the LEVEL UP! card (a new power with no picture gets a star)
POWER_ICONS = {"Stronger": "sword", "Tougher": "heart", "Sharpshooter": "bow", "Tough armor": "shield",
               "Springy": "mushroom", "Speedy": "player", "Lucky": "ring", "Forager": "apple",
               "Extra life": "heart"}


# ---------------------------------------------------------------------------
# Little helpers
# ---------------------------------------------------------------------------

def make_sprite(art, scale):
    """Turn a grid of letters from sprites.py into a picture."""
    surf = pygame.Surface((len(art[0]) * scale, len(art) * scale), pygame.SRCALPHA)
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.fill(sprites.COLORS[ch], (x * scale, y * scale, scale, scale))
    return surf


def wear(art, overlay):
    """Put one letter picture on top of another (the "." squares let the bottom one show through)."""
    return ["".join(top if top != "." else bottom for bottom, top in zip(low, high))
            for low, high in zip(art, overlay)]


def recolor(art, swaps):
    """The same letter picture with some colours swapped, like {"e": "m"} (grey becomes rust red)."""
    return ["".join(swaps.get(ch, ch) for ch in row) for row in art]


def make_glow(radius, color):
    """A soft round glow, brightest in the middle."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for size, alpha in ((1.0, 30), (0.72, 45), (0.45, 70)):
        pygame.draw.circle(surf, color + (alpha,), (radius, radius), int(radius * size))
    return surf


def make_soft_glow(radius, color, strength=60):
    """Like make_glow, but fading out smoothly with no rings (for torches)."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    steps = 16
    for i in range(steps):
        t = i / steps
        pygame.draw.circle(surf, color + (int(strength * (t + 1 / steps) ** 1.3),), (radius, radius), int(radius * (1 - t)))
    return surf


def dot(surf, color, x, y, w=1, h=1):
    """Paint one chunky pixel, or a block of w x h of them. x and y count chunky pixels, not screen pixels."""
    surf.fill(color, (x * ART_PIXEL, y * ART_PIXEL, w * ART_PIXEL, h * ART_PIXEL))


def chunky(small):
    """Make a tiny picture ART_PIXEL times bigger, so every pixel becomes a crisp chunky pixel."""
    w, h = small.get_size()
    return pygame.transform.scale(small, (w * ART_PIXEL, h * ART_PIXEL))


def light_on_top(small, color, light):
    """Every pixel of this color with a different color just above it turns light,
    as if a light was shining down on it from above."""
    shape = pygame.mask.from_threshold(small, color, (1, 1, 1, 255))
    tops = shape.copy()
    tops.erase(shape, (0, 1))                       # rub out every pixel that has the same color above it
    tops.to_surface(small, setcolor=light, unsetcolor=None)


def art_bottom(art):
    """How many see-through rows are under a picture, so its feet can touch the ground."""
    for i, row in enumerate(reversed(art)):
        if row.strip("."):
            return i
    return 0


def pivot_image(image, pivot):
    """Pad a picture so the pivot point is right in the middle - then it can spin around that point."""
    w, h = image.get_size()
    px, py = pivot
    size = 2 * int(max(px, w - px, py, h - py)) + 2
    padded = pygame.Surface((size, size), pygame.SRCALPHA)
    padded.blit(image, (size // 2 - px, size // 2 - py))
    return padded


def whiten(surface):
    """A flashing-white copy of a sprite (used when something gets hit)."""
    copy = surface.copy()
    copy.fill((200, 200, 200), special_flags=pygame.BLEND_RGB_ADD)
    return copy


def darker(color, amount):
    """The same colour, a little darker."""
    return tuple(max(0, value - amount) for value in color)


def lerp(a, b, t):
    return a + (b - a) * t


def tile_px(pos):
    """Top-left pixel of a map tile."""
    return (pos[1] * TILE, pos[0] * TILE)


def tile_center(pos):
    return (pos[1] * TILE + TILE // 2, pos[0] * TILE + TILE // 2)


# ---------------------------------------------------------------------------
# Sound effects - made from math, so no sound files are needed!
# ---------------------------------------------------------------------------

class Sounds:
    # name: (notes, seconds per note, volume, wave). None = noise, 0 = silence
    RECIPES = {
        "step":    ([180], 0.03, 0.06, "square"),
        "pickup":  ([660, 880], 0.06, 0.18, "square"),
        "craft":   ([None, 880, 1175], 0.05, 0.18, "square"),
        "dig":     ([None], 0.06, 0.12, "square"),
        "hit":     ([None, None], 0.05, 0.25, "square"),
        "miss":    ([220, 160], 0.06, 0.15, "square"),
        "hurt":    ([320, 220, 150], 0.05, 0.2, "square"),
        "eat":     ([520, 0, 620], 0.04, 0.16, "square"),
        "heal":    ([440, 554, 659], 0.08, 0.25, "sine"),
        "diamond": ([988, 1319, 1568, 1976], 0.06, 0.18, "square"),
        "alert":   ([440, 0, 440, 0], 0.06, 0.18, "square"),
        "victory": ([523, 659, 784, 1047], 0.08, 0.2, "square"),
        "levelup": ([523, 659, 784, 1047, 1319, 1568], 0.07, 0.2, "square"),
        "quest":   ([784, 988, 1175, 1568], 0.1, 0.2, "sine"),
        "boom":    ([None] * 8, 0.06, 0.4, "square"),
        "win":     ([523, 523, 784, 784, 1047, 0, 1047, 1319], 0.12, 0.22, "square"),
        "lose":    ([392, 330, 262, 196], 0.18, 0.22, "sine"),
        "jump":    ([392, 587], 0.04, 0.1, "square"),
        "land":    ([None], 0.03, 0.08, "square"),
        "cave":    ([392, 330, 262, 196], 0.08, 0.18, "sine"),
        "door":    ([262, 330, 392, 523], 0.07, 0.18, "sine"),
        "portal":  ([196, 262, 330, 392, 523, 659, 784], 0.09, 0.2, "sine"),
        "page":    ([660, 880], 0.03, 0.08, "square"),
        "clang":   ([None, 1568, 1175], 0.05, 0.25, "square"),
        "sunfang": ([523, 659, 784, 1047, 1319, 1568, 2093], 0.09, 0.22, "sine"),
        "shoot":   ([1400, 1000], 0.025, 0.07, "square"),
        "chest":   ([392, 523, 659, 784], 0.06, 0.18, "square"),
        "fuse":    ([None] * 6, 0.05, 0.06, "square"),
        "stomp":   ([300, 150], 0.04, 0.22, "square"),
        "boing":   ([330, 495, 660], 0.04, 0.15, "sine"),
        "gem":     ([1319, 1760], 0.04, 0.12, "square"),
        "chop":    ([None, 160], 0.05, 0.22, "square"),
        "splash":  ([None, None, None], 0.04, 0.1, "square"),
        "bubble":  ([660, 990, 1320], 0.04, 0.12, "sine"),
        "crack":   ([None, 300, 200], 0.05, 0.22, "square"),
        "trap":    ([None, 1760, 1320], 0.025, 0.1, "square"),
        "whoosh":  ([None] * 5, 0.04, 0.08, "square"),          # a flame jet fires
        "steam":   ([None, None, 880, 1175], 0.04, 0.12, "sine"),  # a steam geyser throws you up
        "secret":  ([523, 784, 1047, 1568], 0.07, 0.16, "sine"),   # you found a secret passage
        "chip":    ([None, 2093, 1568], 0.03, 0.15, "square"),      # your sword is down to its last few hits
    }

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.rate, _, self.channels = pygame.mixer.get_init()
            for name, recipe in self.RECIPES.items():
                self.sounds[name] = self.make(*recipe)
        except Exception:
            self.sounds = {}    # no speakers? no problem - play silently

    def make(self, notes, note_len, volume, wave):
        samples = array("h")
        n = int(self.rate * note_len)
        noise = random.Random(1)
        for freq in notes:
            for i in range(n):
                t = i / self.rate
                fade = 1.0 - i / n
                if freq is None:
                    v = noise.uniform(-1, 1)
                elif freq == 0:
                    v = 0.0
                elif wave == "square":
                    v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                else:
                    v = math.sin(2 * math.pi * freq * t)
                value = int(v * fade * volume * 32767)
                for _ in range(self.channels):
                    samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled


# ---------------------------------------------------------------------------
# Background music - one tune for each place. Write your own!
# Each tune is a list of notes, one for every half beat: "C5" is the note C
# (in the 5th octave), "-" keeps the last note going, "." is a rest, and the
# "|" lines are just there to make it easier to read. Every voice in a tune
# should be the same length, so they stay together when the tune loops.
# Waves: "square" (beepy), "triangle" (soft), "sine" (smooth), "bell" (twinkly)
# Drums: k = kick, s = snare, h = hi-hat
# ---------------------------------------------------------------------------
MUSIC_VOLUME = 0.35
MUSIC_FADE = 0.9                    # seconds for one tune to fade into the next
INTRO_FADE = 1.5                    # seconds for the last intro card (and its tune) to fade into the world
TUNES = {
    # The spooky tune for the title and the first story cards: slow, low and in a minor key.
    # A music box twinkles over a deep bass, and a far-away drum goes "boom".
    "intro": {"tempo": 66, "voices": [
        ("triangle", 0.5, "D2 - - - - - - - | D2 - - - - - - - | A#1 - - - - - - - | A1 - - - - - - - |"
                          "D2 - - - - - - - | G1 - - - - - - - | D#2 - - - - - - - | A1 - - - - - - - |"),
        ("triangle", 0.4, ". . . . D4 - E4 - | F4 - - - E4 - D4 - | D4 - - - - - - - | C#4 - - - - - - - |"
                          "D4 - - - - - F4 - | G4 - - - A#4 - A4 - | G4 - - - - - D#4 - | E4 - - - C#4 - - - |"),
        ("bell", 0.2, "D5 . A4 . F5 . A4 . | D5 . A4 . E5 . C#5 . | D5 . A#4 . F5 . A#4 . | C#5 . A4 . E5 . A4 . |"
                      "D5 . A4 . F5 . A4 . | D5 . A#4 . G5 . A#4 . | D#5 . A#4 . G5 . A#4 . | C#5 . E5 . A5 . . . |")],
        "drums":          "k . . . . . . . | k . . . . . . . | k . . . . . . . | k . . . k . k . |" * 2},
    "home": {"tempo": 132, "voices": [
        ("triangle", 0.5, "E5 - G5 - C6 - B5 A5 | G5 - E5 - C5 - D5 E5 | F5 - A5 - G5 - E5 C5 | D5 - - - G4 - - - |"
                          "E5 - G5 - C6 - B5 A5 | G5 - E5 - C5 - E5 G5 | A5 - G5 F5 E5 - D5 - | C5 - - - . . . . |"),
        ("sine", 0.6,     "C3 . G3 . C3 . G3 . | A2 . E3 . A2 . E3 . | F2 . C3 . F2 . C3 . | G2 . D3 . G2 . D3 . |"
                          "C3 . G3 . C3 . G3 . | A2 . E3 . A2 . E3 . | F2 . C3 . G2 . D3 . | C3 . G3 . C3 . . . |")],
        "drums":          "k . h . s . h . | k . h . s . h . | k . h . s . h . | k . h . s . h h |" * 2},
    "stone": {"tempo": 84, "voices": [
        ("triangle", 0.45, "A4 - - - C5 - E5 - | D5 - - - B4 - - - | A4 - - - C5 - E5 - | G5 - F5 - E5 - - - |"
                           "F5 - - - E5 - D5 - | C5 - - - B4 - - - | A4 - C5 - B4 - G#4 - | A4 - - - . . . . |"),
        ("sine", 0.55,     "A2 - - - - - - - | F2 - - - - - - - | A2 - - - - - - - | E2 - - - - - - - |"
                           "D2 - - - - - - - | F2 - - - - - - - | E2 - - - - - - - | A2 - - - - - - - |")],
        "drums":           "h . . . . . . . |" * 8},
    "crystal": {"tempo": 100, "voices": [
        ("bell", 0.45, "E6 B5 G#5 B5 E6 B5 G#5 B5 | C#6 A5 E5 A5 C#6 A5 E5 A5 | D#6 B5 F#5 B5 D#6 B5 F#5 B5 | E6 B5 G#5 B5 E6 - - - |"
                       "C#6 A5 E5 A5 C#6 A5 E5 A5 | B5 G#5 E5 G#5 B5 G#5 E5 G#5 | A5 F#5 D#5 F#5 B5 F#5 D#5 F#5 | E5 - - - . . . . |"),
        ("sine", 0.5,  "E3 - - - - - - - | A2 - - - - - - - | B2 - - - - - - - | E3 - - - - - - - |"
                       "A2 - - - - - - - | E3 - - - - - - - | B2 - - - - - - - | E3 - - - - - - - |")]},
    "lava": {"tempo": 112, "voices": [
        ("square", 0.22, "D2 D2 . D2 D#2 . D2 . | D2 D2 . D2 F2 . D#2 . | D2 D2 . D2 D#2 . D2 . | C2 C2 . C2 D#2 . D2 . |" * 2),
        ("triangle", 0.45, "D4 - - - D#4 - F4 - | D4 - - - . . . . | F4 - G4 - D#4 - - - | D4 - - - . . . . |"
                           "A4 - - - G4 - F4 - | D#4 - - - F4 - - - | D4 - D#4 - C4 - - - | D4 - - - . . . . |")],
        "drums": "k . k . s . k k | k . k . s . . . |" * 4},
    "moss": {"tempo": 96, "voices": [
        ("sine", 0.5, "G5 - A5 - B5 - D6 - | E6 - D6 - B5 - - - | A5 - B5 - D6 - B5 - | A5 - G5 - E5 - - - |"
                      "G5 - A5 - B5 - D6 - | E6 - G6 - E6 - D6 - | B5 - A5 - G5 - A5 - | G5 - - - . . . . |"),
        ("triangle", 0.45, "G2 - D3 - G2 - D3 - | C3 - G3 - C3 - G3 - | G2 - D3 - G2 - D3 - | D3 - A3 - D3 - A3 - |"
                           "G2 - D3 - G2 - D3 - | C3 - G3 - C3 - G3 - | D3 - A3 - D3 - A3 - | G2 - D3 - G2 - . . |")],
        "drums": "h . . h . . h . |" * 8},
    "nightfall": {"tempo": 72, "voices": [
        ("triangle", 0.45, "C4 - - - D#4 - - - | G4 - - - F4 - - - | G#4 - - - G4 - - - | D#4 - - - D4 - - - |"
                           "C4 - - - D#4 - - - | G4 - - - C5 - - - | B4 - - - G4 - - - | C4 - - - - - - - |"),
        ("sine", 0.55, "C2 - - - - - - - | G#1 - - - - - - - | F2 - - - - - - - | G1 - - - - - - - |"
                       "C2 - - - - - - - | D#2 - - - - - - - | G1 - - - - - - - | C2 - - - - - - - |"),
        ("bell", 0.25, ". . . . . . G5 . | . . . . . . . . | . . . . . . D#5 . | . . . . . . . . |" * 2)]},
    "castle": {"tempo": 84, "voices": [
        ("square", 0.16, "D4 - F4 - A4 - G4 F4 | E4 - - - C#4 - - - | D4 - F4 - A4 - D5 - | C#5 - - - A4 - - - |"
                         "A#4 - A4 - G4 - F4 - | E4 - F4 - G4 - E4 - | D4 - - - A3 - - - | D4 - - - . . . . |"),
        ("square", 0.1,  "A3 - D4 - D4 - D4 - | A3 - - - A3 - - - | A3 - D4 - F4 - A4 - | E4 - - - E4 - - - |"
                         "F4 - F4 - D4 - D4 - | C#4 - D4 - E4 - C#4 - | A3 - - - E3 - - - | A3 - - - . . . . |"),
        ("sine", 0.55, "D2 - - - - - - - | A1 - - - - - - - | D2 - - - - - - - | A1 - - - - - - - |"
                       "A#1 - - - - - - - | A1 - - - - - - - | D2 - - - A1 - - - | D2 - - - - - - - |")],
        "drums": "k . . . . . . . |" * 8},
    # The fight with the Shadow King: fast and scary, with a bass that never stops running.
    "boss": {"tempo": 152, "voices": [
        ("square", 0.14, "E4 - G4 - B4 - E5 - | D#5 - - - B4 - - - | C5 - B4 - A4 - G4 - | F#4 - - - B3 - - - |"
                         "E4 - G4 - B4 - E5 - | G5 - F#5 - E5 - D#5 - | E5 - C5 - A4 - F#4 - | B4 - - - D#5 - - - |"),
        ("square", 0.12, "E2 E2 E3 E2 E2 E2 E3 E2 | B1 B1 B2 B1 B1 B1 B2 B1 | C2 C2 C3 C2 C2 C2 C3 C2 | B1 B1 B2 B1 B1 B1 B2 B1 |"
                         "E2 E2 E3 E2 E2 E2 E3 E2 | E2 E2 E3 E2 B1 B1 B2 B1 | A1 A1 A2 A1 A1 A1 A2 A1 | B1 B1 B2 B1 B1 B1 B2 B1 |"),
        ("sine", 0.45,   "E2 - - - - - - - | B1 - - - - - - - | C2 - - - - - - - | B1 - - - - - - - |"
                         "E2 - - - - - - - | E2 - - - B1 - - - | A1 - - - - - - - | B1 - - - - - - - |")],
        "drums": "k . h . s . h . | k . h k s . h . |" * 4},
}
TUNES.update(phase2.theme.TUNES)        # Phase 2's darker map tune (phase2/theme.py)
NOTE_STEPS = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}


def note_frequency(name):
    """'A4' is 440 Hz. Every step up the piano multiplies the frequency by the 12th root of 2."""
    letter, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE_STEPS[letter] + 12 * (octave - 4)) / 12)


class Music:
    """Plays a looping tune for the place you're in. The tunes are turned into sound in the
    background (it takes a moment), so the game doesn't have to wait."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.tunes = {}               # tune name -> ready-to-play sound
        self.playing = None
        self.channel = None
        self.started = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.rate, _, self.channels = pygame.mixer.get_init()
            pygame.mixer.set_reserved(2)          # channels 0 and 1 are just for music:
            self.channel = pygame.mixer.Channel(0)          # the tune that's playing now...
            self.old_channel = pygame.mixer.Channel(1)      # ...and the last one, fading away
            self.channel.set_volume(MUSIC_VOLUME)
            self.old_channel.set_volume(MUSIC_VOLUME)
        except Exception:
            self.channel = None                   # no speakers? then no music
        if self.enabled:
            self.start()

    def start(self):
        """Begin turning the tunes into sound (once), in the background."""
        if self.started or self.channel is None:
            return
        self.started = True
        if IN_BROWSER:                            # a web browser can't do work in the background,
            self.load_ready_made()                # so it plays tunes that were made ahead of time
            return
        threading.Thread(target=self.make_all, daemon=True).start()

    def load_ready_made(self):
        """In the browser: load the tunes from the web_music folder (made by web/build_web.py)."""
        for name in TUNES:
            path = os.path.join(WEB_MUSIC_FOLDER, name + ".ogg")
            if not os.path.exists(path):
                path = os.path.join(WEB_MUSIC_FOLDER, name + ".wav")
            try:
                self.tunes[name] = pygame.mixer.Sound(path)
            except Exception:
                pass                              # a tune that's missing just stays quiet

    def make_all(self):
        for name in TUNES:
            try:
                self.tunes[name] = pygame.mixer.Sound(buffer=self.make(TUNES[name]))
            except Exception:
                pass

    def make(self, tune):
        """Add up every voice and the drums, note by note, into one long sound."""
        step = 60.0 / tune["tempo"] / 2               # seconds in half a beat
        n = int(self.rate * step)
        voices = [(wave, volume, notes.replace("|", " ").split()) for wave, volume, notes in tune["voices"]]
        length = max(len(notes) for _, _, notes in voices) * n
        mix = [0.0] * length
        for wave, volume, notes in voices:
            i = 0
            while i < len(notes):
                note, steps = notes[i], 1
                while i + steps < len(notes) and notes[i + steps] == "-":
                    steps += 1                        # "-" keeps the note going
                if note not in (".", "-"):
                    self.add_note(mix, i * n, note_frequency(note), steps * n, wave, volume)
                i += steps
        drums = tune.get("drums", "").replace("|", " ").split()
        noise = random.Random(3)
        for i, hit in enumerate(drums):
            start = i * n
            for j in range(min(n, int(self.rate * (0.12 if hit == "k" else 0.05)))):
                fade = 1 - j / (self.rate * (0.12 if hit == "k" else 0.05))
                if start + j >= length:
                    break
                if hit == "k":                        # kick: a low thump that drops in pitch
                    v = math.sin(2 * math.pi * (110 - 60 * j / n) * j / self.rate) * 0.5
                elif hit == "s":
                    v = noise.uniform(-1, 1) * 0.25
                elif hit == "h":
                    v = noise.uniform(-1, 1) * 0.08
                else:
                    continue
                mix[start + j] += v * fade
        samples = array("h")
        for v in mix:
            value = int(max(-1.0, min(1.0, v * 0.6)) * 32767)
            for _ in range(self.channels):
                samples.append(value)
        return samples.tobytes()

    def add_note(self, mix, start, freq, n, wave, volume):
        attack = max(1, int(self.rate * 0.01))
        for j in range(n):
            if start + j >= len(mix):
                break
            t = j / self.rate
            phase = (freq * t) % 1.0
            if wave == "square":
                v = 1.0 if phase < 0.5 else -1.0
            elif wave == "triangle":
                v = 4 * abs(phase - 0.5) - 1
            else:
                v = math.sin(2 * math.pi * phase)
            if wave == "bell":
                envelope = math.exp(-5 * t)            # a bell rings, then fades away
            else:
                envelope = min(1.0, j / attack) * (1 - j / n) ** 0.5
            mix[start + j] += v * envelope * volume

    def play(self, name, sound_on, fade=MUSIC_FADE):
        """Called every frame with the tune for where you are. When the tune changes,
        the old one fades out while the new one fades in (that takes `fade` seconds)."""
        if self.channel is None:
            return
        if not (self.enabled and sound_on):
            if self.playing:
                self.fade_away(self.channel, 400)
                self.fade_away(self.old_channel, 400)
                self.playing = None
            return
        self.start()
        if name != self.playing and name in self.tunes:
            ms = int(fade * 1000)
            self.fade_away(self.channel, ms)                            # the old tune fades away...
            self.channel, self.old_channel = self.old_channel, self.channel   # (swap channels)
            self.channel.stop()                                         # a fresh start, at full music volume
            self.channel.set_volume(MUSIC_VOLUME)
            self.channel.play(self.tunes[name], loops=-1, fade_ms=ms)   # ...while the new one fades in
            self.playing = name

    def fade_away(self, channel, ms):
        """Fade out the tune on this channel. A tune that has only just started is still
        silent, and can't fade any quieter, so it simply stops."""
        if channel.get_volume() > 0:
            channel.fadeout(ms)
        else:
            channel.stop()

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled


# ---------------------------------------------------------------------------
# The sword-forging mini-game
# ---------------------------------------------------------------------------

class Forge:
    """A glowing marker slides back and forth. Strike 3 times: the gold zone is Perfect, the green zone Good.
    The marker gets faster after each strike. The strikes make the sword Great, normal or Cracked."""
    PAUSE = 0.7                # after a strike, a moment to see how it went
    END_TIME = 1.6             # after the last strike, a moment to see the sword

    def __init__(self, rng=random):
        self.rng = rng
        self.strikes = []          # "perfect", "good" or "miss", one for each strike so far
        self.pos = 0.0
        self.direction = 1
        self.speed = 1.15          # how fast the marker moves
        self.pause = 0.0           # > 0 just after a strike: the marker waits
        self.timer = 0.0           # time since the last strike
        self.enter_held = False    # True while the ENTER that opened the forge is still held down
        self.new_zone()

    def new_zone(self):
        self.zone_x = self.rng.uniform(0.05, 0.95 - rules.FORGE_GREEN)
        self.zone_w = rules.FORGE_GREEN
        self.gold_x = self.zone_x + (rules.FORGE_GREEN - rules.FORGE_GOLD) / 2
        self.gold_w = rules.FORGE_GOLD

    @property
    def finished(self):
        return len(self.strikes) >= rules.FORGE_STRIKES

    @property
    def ready(self):
        """Can you strike right now?"""
        return not self.finished and self.pause <= 0

    @property
    def quality(self):
        return rules.sword_quality(self.strikes) if self.finished else None

    def update(self, dt):
        self.timer += dt
        if self.finished:
            return
        if self.pause > 0:
            self.pause -= dt
            if self.pause <= 0:
                self.new_zone()
            return
        self.pos += self.direction * self.speed * dt
        if self.pos >= 1:
            self.pos, self.direction = 1.0, -1
        elif self.pos <= 0:
            self.pos, self.direction = 0.0, 1

    def strike(self):
        """Bring the hammer down. Returns "perfect", "good" or "miss" (or None if you can't strike now)."""
        if not self.ready:
            return None
        grade = rules.strike_grade(self.pos, self.zone_x)
        self.strikes.append(grade)
        self.speed *= rules.FORGE_SPEEDUP
        self.timer = 0.0
        if not self.finished:
            self.pause = self.PAUSE
        return grade

    @property
    def done(self):
        return self.finished and self.timer > self.END_TIME


# ---------------------------------------------------------------------------
# Forging Sunfang: the diamonds rise, then hit each key before its ring closes
# ---------------------------------------------------------------------------

class SunfangForge:
    RISE_TIME = 2.2        # the diamonds float up out of your pack
    BEAT_TIME = 1.4        # how long you have to press each key
    PAUSE_TIME = 0.55      # a breath between beats
    FINALE_TIME = 2.6      # the diamonds melt into Sunfang
    BEATS = 3                # the 3 steps: heat the blade, hammer it, cool it (a failed step comes again)
    STEPS = [("HEAT", "Heat the blade in the fire!"), ("HAMMER", "Hammer it on the anvil!"),
             ("COOL", "Plunge it in the water to cool it!")]
    KEYS = [(pygame.K_SPACE, "SPACE"), (pygame.K_LEFT, "LEFT"), (pygame.K_RIGHT, "RIGHT"), (pygame.K_UP, "UP")]

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.phase = "rise"
        self.phase_time = 0.0
        self.time = 0.0
        self.beats_done = 0
        self.misses = 0
        self.key = None            # (key code, name) you need to press right now
        self.message = ""
        self.last_strike = -9.0    # when the hammer last came down (for the animation)
        self.celebrated = False    # the big flash at the end has happened

    @property
    def perfect(self):
        return self.misses == 0

    @property
    def step(self):
        """(its name, what to do) for the step you're on: heat, hammer or cool."""
        return self.STEPS[min(self.beats_done, len(self.STEPS) - 1)]

    @property
    def done(self):
        return self.phase == "done"

    @property
    def ring(self):
        """How much of the ring is left around the key: 1 = just started, 0 = too late."""
        return max(0.0, 1 - self.phase_time / self.BEAT_TIME) if self.phase == "beat" else 0.0

    def update(self, dt):
        self.time += dt
        self.phase_time += dt
        if self.phase == "rise" and self.phase_time >= self.RISE_TIME:
            self.start_beat()
        elif self.phase == "beat" and self.phase_time >= self.BEAT_TIME:
            self.miss("Too slow!")
        elif self.phase == "pause" and self.phase_time >= self.PAUSE_TIME:
            if self.beats_done >= self.BEATS:
                self.phase, self.phase_time, self.message = "finale", 0.0, ""
            else:
                self.start_beat()
        elif self.phase == "finale" and self.phase_time >= self.FINALE_TIME:
            self.phase = "done"

    def start_beat(self):
        self.phase, self.phase_time = "beat", 0.0
        self.key = self.rng.choice(self.KEYS)
        self.message = ""

    def press(self, key):
        """Returns "hit", "miss", or None if no key is wanted right now."""
        if self.phase != "beat":
            return None
        if key == self.key[0]:
            self.beats_done += 1
            self.phase, self.phase_time = "pause", 0.0
            self.message = "CLANG!"
            self.last_strike = self.time
            return "hit"
        self.miss("Wrong key!")
        return "miss"

    def miss(self, why):
        self.misses += 1
        self.phase, self.phase_time = "pause", 0.0
        self.message = why + " Try that one again!"


# ---------------------------------------------------------------------------
# The app
# ---------------------------------------------------------------------------

class App:
    def __init__(self, player_name="", seed=None, sound=True, castle=False, throne=False, nightfall=False, phase2_mode=None):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Adventure World")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.sounds = Sounds(enabled=sound)
        self.music = Music(enabled=sound)
        self.fonts = {}
        self.word_pictures = {}       # (words, size, color) -> a picture of them, see words()
        self.wrapped = {}             # (text, size, width) -> its lines, see wrap()
        self.seed = seed
        self.skip_to_nightfall = nightfall  # play-test shortcut: start in Nightfall Hollow, just through the Portal
        self.skip_to_castle = castle        # play-test shortcut: start next to the Shadow King's castle
        self.skip_to_throne = throne        # play-test shortcut: start in the throne room, ready to fight him
        self.games_started = 0              # after the first game, the intro story is skipped
        self.in_intro = False               # True while the first story cards are showing
        self.name_input = player_name or "Hero"
        self.tips = tutorial.TipBook()      # which tips you've seen, and whether tips are on (it's saved)
        self.allow_tips = True              # the cave editor turns tips off while you test your cave
        self.tip_pictures = {}              # tip name -> its bubble, painted once (see tip_picture)
        self.tip_off_button = None          # where "no more tips" is in the bubble, so you can click it
        self.tip_frame = None               # the paused game under a bubble, painted once (see paint_under_tip)
        self.tips_switch = None             # where the tips switch is on the title screen
        self.panel_spots = {}               # where the food, wood... rows are in the side panel (for tips)
        self.state = "title"
        self.running = True
        self.time = 0.0
        # Classic or Phase 2 (see phase2/)? Load (mode "continue") lists the Phase 2 save slots, if one has a save
        self.modes = ["classic", "phase2"] + (["continue"] if phase2.has_save() else [])
        self.mode = "classic"
        self.save_slot = 1                  # the Phase 2 save slot (1-3) the next game loads from or saves into
        self.mode_buttons = {}              # where each choice is on the title screen, so you can click it

        self.load_art()
        pygame.display.set_icon(self.art["player"])
        pygame.key.set_repeat(220, 140)

        self.battle_box = pygame.Rect(0, 0, 760, 440)
        self.battle_box.center = (WIDTH // 2, HEIGHT // 2)
        self.overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.view = pygame.Surface((VIEW_W, VIEW_H))     # what the camera sees

        self.game = rules.Game(self.name_input, seed=seed)   # also the title background
        self.build_tiles()
        self.reset_visuals()
        if phase2_mode:                     # python game.py --phase2 (or --continue): straight into Phase 2
            self.mode = "continue" if phase2_mode == "continue" and "continue" in self.modes else "phase2"
            self.save_slot = phase2.newest_slot() if self.mode == "continue" else 1
            self.new_game()

    # ----- setup ------------------------------------------------------------

    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(None, size)
        return self.fonts[size]

    def load_art(self):
        self.art = {
            "player": make_sprite(sprites.PLAYER, 3),
            "player_big": make_sprite(sprites.PLAYER, 8),
            "player_title": make_sprite(sprites.PLAYER, 6),
            "tree": make_sprite(sprites.TREE, 3),
            "house": make_sprite(sprites.HOUSE, 4),
        }
        self.armored = wear(sprites.PLAYER, sprites.ARMOR)        # the Hero wearing his armor
        self.art["player_armor"] = make_sprite(self.armored, 3)
        self.art["player_big_armor"] = make_sprite(self.armored, 8)
        # In caves and the castle we see the Hero from the side (the SIDE_ pictures in sprites.py)
        self.side_view = {"stand": sprites.SIDE_STAND, "jump": sprites.SIDE_JUMP, "fall": sprites.SIDE_FALL,
                          "step 1": sprites.SIDE_STEP_1, "pass 1": sprites.SIDE_PASS_1,
                          "step 2": sprites.SIDE_STEP_2, "pass 2": sprites.SIDE_PASS_2}
        self.side_view_armored = {name: wear(art, sprites.ARMOR_SIDE) for name, art in self.side_view.items()}
        # On a ladder we see his back (the CLIMB_ pictures)
        self.climb_view = [sprites.CLIMB_1, sprites.CLIMB_2]
        self.climb_view_armored = [wear(art, sprites.ARMOR_BACK) for art in self.climb_view]
        # On a climbing wall we see his side, facing the wall, hands and boots gripping it (the WALL_ pictures)
        self.wall_view = {"hold": sprites.WALL_HOLD, "reach 1": sprites.WALL_1, "reach 2": sprites.WALL_2,
                          "slide": sprites.WALL_SLIDE}
        self.wall_view_armored = {name: wear(art, sprites.ARMOR_WALL) for name, art in self.wall_view.items()}
        # On the world map he walks like an old 8-bit hero: standing, then 2 walking pictures for each way
        # (left is the right-side picture flipped over)
        walks = {"down": ([sprites.PLAYER, sprites.WALK_DOWN_1, sprites.WALK_DOWN_2], sprites.ARMOR),
                 "up": ([sprites.BACK_STAND, sprites.WALK_UP_1, sprites.WALK_UP_2], sprites.ARMOR_BACK),
                 "right": ([sprites.SIDE_STAND, sprites.SIDE_STEP_1, sprites.SIDE_STEP_2], sprites.ARMOR_SIDE)}
        self.map_walk = {}
        for way, (pictures, armor) in walks.items():
            self.map_walk[way] = [make_sprite(art, 3) for art in pictures]
            self.map_walk[way + " armor"] = [make_sprite(wear(art, armor), 3) for art in pictures]
        for name in ("right", "right armor"):
            self.map_walk[name.replace("right", "left")] = [pygame.transform.flip(p, True, False)
                                                           for p in self.map_walk[name]]
        for icon in ("HEART", "SWORD", "PICKAXE", "APPLE", "DIAMOND", "SHIELD", "STAR"):
            self.art[icon.lower()] = make_sprite(getattr(sprites, icon), 3)
        self.art["boat"] = make_sprite(sprites.BOAT, 3)
        self.art["boat_icon"] = make_sprite(sprites.BOAT, 2)
        self.art["wood"] = make_sprite(sprites.WOOD, 3)
        self.art["bow"] = make_sprite(sprites.BOW, 3)
        self.art["craft_bow"] = make_sprite(sprites.BOW, 6)
        self.art["craft_sword"] = make_sprite(sprites.SWORD, 5)
        self.art["craft_pickaxe"] = make_sprite(sprites.PICKAXE, 5)
        self.art["dead_tree"] = make_sprite(sprites.DEAD_TREE, 3)
        # The lands of the home world: landmarks, snowy trees, rocks, signposts and chests
        for name, art in LANDMARK_ART.items():
            self.art[name] = make_sprite(getattr(sprites, art), 4)
        self.art["sails"] = make_sprite(sprites.WINDMILL_SAILS, 4)
        self.art["snowy_tree"] = make_sprite(sprites.SNOWY_TREE, 3)
        self.art["rock"] = make_sprite(sprites.BOULDER, 4)
        self.art["snowy_rock"] = make_sprite(sprites.SNOWY_ROCK, 4)
        self.art["red_rock"] = make_sprite(recolor(sprites.BOULDER, RED_ROCK), 4)
        self.art["ruin_wall"] = make_sprite(sprites.RUIN_WALL, 4)
        self.art["signpost"] = make_sprite(sprites.SIGNPOST, 4)
        self.art["bridge"] = make_sprite(sprites.BRIDGE, 4)
        self.art["broken_bridge"] = make_sprite(sprites.BROKEN_BRIDGE, 4)
        self.art["shrine"] = make_sprite(sprites.SHRINE, 4)
        self.art["dark_shrine"] = make_sprite(sprites.DARK_SHRINE, 4)
        self.art["lit_beacon"] = make_sprite(sprites.LIT_BEACON, 4)
        self.art["sun_shard"] = make_sprite(sprites.SUN_SHARD, 2)
        self.art["wren"] = make_sprite(sprites.WREN, 4)
        self.art["lantern"] = make_sprite(sprites.LANTERN, 4)
        self.art["sun_shard_big"] = make_sprite(sprites.SUN_SHARD, 6)
        self.art["castle"] = make_sprite(sprites.CASTLE, 4)
        self.art["king_big"] = make_sprite(sprites.SHADOW_KING, 8)
        self.art["sunfang_big"] = make_sprite(sprites.SUNFANG, 10)
        self.art["sunfang"] = make_sprite(sprites.SUNFANG, 2)
        self.art["castle_big"] = make_sprite(sprites.CASTLE, 12)
        self.art["shrine_big"] = make_sprite(sprites.SHRINE, 6)
        self.art["dead_tree_big"] = make_sprite(sprites.DEAD_TREE, 6)
        self.art["diamond_big"] = make_sprite(sprites.DIAMOND, 6)
        self.violet_glow = make_glow(120, (170, 90, 255))
        self.sun_glow = make_glow(120, (255, 210, 90))
        self.shard_suns = [make_glow(36 + 9 * shards, (255, 220, 120)) for shards in range(len(castle.CASTLE_LEVELS) + 1)]
        # darkness around you in Nightfall Hollow: every lit beacon makes it a little lighter (0 to 3 lit)
        self.nights = []
        for lit in range(rules.BEACONS_NEEDED + 1):
            night = pygame.Surface((VIEW_W * 2, VIEW_H * 2), pygame.SRCALPHA)
            for radius in range(VIEW_W, 0, -12):
                alpha = int((190 - BEACON_BRIGHTER * lit) * min(1.0, max(0.0, (radius - (300 + 60 * lit)) / 500)))
                pygame.draw.circle(night, (10, 4, 22, alpha), (VIEW_W, VIEW_H), radius)
            self.nights.append(night)
        self.night = self.nights[0]
        self.art["ring"] = make_sprite(sprites.RING, 3)
        self.art["mushroom"] = make_sprite(sprites.MUSHROOM, 4)
        self.art["gem"] = make_sprite(sprites.GEM, 4)
        self.small_glow = make_glow(22, (220, 160, 255))
        self.art["chest"] = make_sprite(sprites.CHEST, 4)
        self.art["chest_open"] = make_sprite(sprites.CHEST_OPEN, 4)
        self.cave_art = {}
        self.rock_pictures = {}             # the big rock picture of each cave look, painted the first time it's needed
        self.lava_pictures = []             # and the moving lava (painted the first time too)
        self.spring_pictures = {}           # and the healing springs of each look
        # The tools you hold in a cave, padded so they can swing around your hand
        self.held = {
            "pickaxe": pivot_image(make_sprite(sprites.PICKAXE, CAVE_SCALE), (3.5 * CAVE_SCALE, 7.2 * CAVE_SCALE)),
            "sword": pivot_image(make_sprite(sprites.SWORD, CAVE_SCALE), (1.0 * CAVE_SCALE, 6.8 * CAVE_SCALE)),
            "bow": pivot_image(make_sprite(sprites.BOW, CAVE_SCALE), (1.5 * CAVE_SCALE, 4.0 * CAVE_SCALE)),
            "sunfang": pivot_image(make_sprite(sprites.SUNFANG, 4), (2.0 * 4, 13.5 * 4)),
        }
        # The same, big, for map fights (the big player picture is drawn 8 screen pixels per art pixel)
        self.battle_held = {
            "sword": pivot_image(make_sprite(sprites.SWORD, 11), (1.0 * 11, 6.8 * 11)),
            "sunfang": pivot_image(make_sprite(sprites.SUNFANG, 7), (2.0 * 7, 13.5 * 7)),
        }
        self.monster_cache = {}

        self.shadow = pygame.Surface((36, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow, (0, 0, 0, 90), self.shadow.get_rect())
        self.dim_tile = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        self.dim_tile.fill((8, 8, 24, 120))
        self.glow = pygame.Surface((64, 64), pygame.SRCALPHA)
        for radius, alpha in ((30, 40), (22, 60), (14, 90)):
            pygame.draw.circle(self.glow, (200, 120, 255, alpha), (32, 32), radius)
        self.door_glow = make_glow(64, (255, 220, 140))
        self.gem_glow = make_glow(40, (120, 235, 255))
        self.lava_glow = make_glow(56, (255, 120, 40))
        self.spikes = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        for i in range(4):
            x = i * 16
            pygame.draw.polygon(self.spikes, (196, 196, 208), [(x + 1, TILE), (x + 8, TILE - 30), (x + 15, TILE)])
            pygame.draw.line(self.spikes, (240, 240, 250), (x + 8, TILE - 30), (x + 5, TILE - 4), 2)
        self.ledge = self.paint_ledge((150, 102, 56))
        self.crumbly = self.paint_ledge((176, 140, 96), cracks=True)
        self.stone_ledge = self.paint_stone_ledge()
        self.ladder = self.paint_ladder()
        self.art["window"] = self.paint_window()
        self.art["banner"] = self.paint_banner()
        self.art["torch"] = self.paint_torch()
        self.torch_glows = [make_soft_glow(radius, (255, 150, 60), 115) for radius in (92, 98, 104)]
        self.throne_glow = make_soft_glow(160, (180, 90, 255), 110)
        self.key_glow = make_glow(40, (255, 214, 90))
        self.shard_glow = make_glow(52, (255, 246, 200))
        self.water_glow = make_glow(46, (110, 200, 255))
        # The Shadow King in the throne room (purple, then red when he's angry), his sword and his fireballs
        self.king_pictures = [make_sprite(sprites.SHADOW_KING, KING_SCALE), make_sprite(sprites.ANGRY_SHADOW_KING, KING_SCALE)]
        self.king_glows = [make_soft_glow(130, (170, 90, 255), 90), make_soft_glow(140, (255, 50, 50), 110)]
        self.king_sword = pivot_image(make_sprite(sprites.SHADOW_SWORD, 5), (3.5 * 5, 21.5 * 5))   # spins around its grip
        self.warn_glow = make_glow(70, (255, 80, 80))
        self.wisp_glow = make_glow(34, (150, 210, 255))
        self.fireball_glow = make_glow(34, (190, 100, 255))
        self.light = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)     # the light coming back

    def monster_sprite(self, kind, scale, shadow=False):
        key = (kind, scale, shadow, phase2.is_phase2(self.game))
        if key not in self.monster_cache:
            art = sprites.MONSTER_ART.get(kind, sprites.ZOMBIE)
            image = phase2.monster_picture(self, kind, scale) or make_sprite(art, scale)    # (Phase 2: new art)
            if shadow:                              # a shadow monster: darker, with a purple glow
                image.fill((120, 96, 160), special_flags=pygame.BLEND_RGB_MULT)
                image.fill((26, 0, 40), special_flags=pygame.BLEND_RGB_ADD)
            self.monster_cache[key] = image
        return self.monster_cache[key]

    def build_tiles(self):
        """Paint each map tile once, with a little randomness so they all look different."""
        if phase2.build_tiles(self):            # Phase 2's big map paints each tile when it's first seen
            return
        self.tiles = {}
        self.land_of = {(r, c): self.game.land_name((r, c)) for r in range(self.game.rows) for c in range(self.game.cols)}
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                self.paint_tile(r, c)
        rng = random.Random(7)
        self.fog_tile = pygame.Surface((TILE, TILE))
        self.fog_tile.fill((14, 14, 24))
        for _ in range(6):
            self.fog_tile.fill((30, 30, 48), (rng.randint(0, 62), rng.randint(0, 62), 2, 2))

    def paint_tile(self, r, c):
        if phase2.paint_tile(self, r, c):               # Phase 2: the new lands, waystones, lookouts...
            return
        rng = random.Random(r * 1000 + c * 7 + 3)       # the same square always looks the same
        letter = self.game.map[r][c]
        surf = pygame.Surface((TILE, TILE))
        if self.game.world == 2:
            self.tiles[(r, c)] = self.paint_night_tile(letter, rng, (r, c))
            return
        land = self.land_of.get((r, c))
        ground = LAND_GROUND.get(land, GRASS)           # green grass, snow, red sand...
        if letter in "FGHPRLT+VX":
            self.paint_grass(surf, rng, ground)
        if letter == "G":                               # an open field: just grass, with some tufts and flowers
            tuft = GRASS_TUFT if ground == GRASS else darker(ground[1], 18)
            for _ in range(5):
                x, y = rng.randint(6, 54), rng.randint(10, 56)
                for dx in (-3, 0, 3):
                    pygame.draw.line(surf, tuft, (x + dx, y), (x + dx * 2, y - rng.randint(5, 9)), 2)
            for _ in range(rng.randint(0, 3) if land != "Frosty Corner" else 0):     # no flowers in the snow
                surf.fill(rng.choice([(255, 230, 90), (255, 255, 255), (240, 110, 140), (170, 150, 255)]),
                          (rng.randint(4, 56), rng.randint(6, 58), 3, 3))
        elif letter == "F":
            tree = self.art["snowy_tree" if land == "Frosty Corner" else "tree"]
            surf.blit(tree, (rng.randint(4, 12), rng.randint(4, 12)))
        elif letter == "L":
            surf.blit(self.art[self.game.tile_name((r, c))], (0, 0))
        elif letter == "T":
            surf.blit(self.art["chest"], (0, 4))
        elif letter == "+":
            surf.blit(self.art["signpost"], (0, 0))
        elif letter == "X":
            rock = {"Frosty Corner": "snowy_rock", "Ember Canyon": "red_rock", "Old Ruins": "ruin_wall"}.get(land, "rock")
            surf.blit(self.art[rock], (0, 0))
        elif letter == "I":
            self.paint_map_ice(surf, rng)
        elif letter == "B":
            self.paint_reeds(surf, rng)
        elif letter == "V":
            self.paint_vent(surf, rng)
        elif letter == "H":
            surf.blit(self.art["house"], (0, 0))
        elif letter in "MS":                            # a Mine (or the Secret Mine, hidden in the woods)
            self.paint_mine(surf, rng, self.mine_theme((r, c)))
            if letter == "S":                           # leaves hang over its door, so it's hard to spot
                for _ in range(16):
                    x, y = rng.randint(2, 58), rng.randint(0, 22)
                    pygame.draw.circle(surf, rng.choice([(40, 104, 44), (60, 140, 60), (30, 80, 36)]), (x, y), rng.randint(3, 6))
        elif letter == "W":
            surf.fill((52, 108, 200))
        elif letter in "=#":                            # the bridge over the Icy River (broken, or fixed)
            surf.fill((52, 108, 200))
            surf.blit(self.art["broken_bridge" if letter == "=" else "bridge"], (0, 0))
        elif letter == "R":
            self.paint_path(surf, rng, r, c, None if ground == GRASS else darker(ground[0], 30))
        elif letter == "P":
            pygame.draw.ellipse(surf, (70, 70, 84), (6, 18, 52, 36))
            pygame.draw.ellipse(surf, (112, 112, 128), (10, 20, 44, 30))
        self.tiles[(r, c)] = surf

    def paint_night_tile(self, letter, rng, pos=None):
        """Nightfall Hollow: purple-black grass, dead trees, black water, shrines and the castle."""
        surf = pygame.Surface((TILE, TILE))
        if letter == "W":
            surf.fill((16, 18, 36))
            return surf
        surf.fill((40, 32, 54))
        for _ in range(22):
            surf.fill(rng.choice([(54, 44, 70), (32, 26, 44)]), (rng.randint(0, 60), rng.randint(0, 60), 2, 4))
        if rng.random() < 0.3:                      # a tiny glowing flower
            surf.fill((190, 130, 240), (rng.randint(4, 56), rng.randint(40, 58), 3, 3))
        if letter == "F":
            surf.blit(self.art["dead_tree"], (rng.randint(4, 12), rng.randint(4, 12)))
        elif letter == "H":
            lit = pos in self.game.beacons
            surf.blit(self.art["lit_beacon" if lit else "shrine"], (0, 0))
        elif letter == "D":
            surf.blit(self.art["dark_shrine"], (0, 0))
        elif letter == "C":
            surf.blit(self.art["castle"], (0, 0))
        elif letter == "M":
            self.paint_mine(surf, rng, "shadow")
        elif letter == "X":                         # a black cliff: dark rock with a purple edge
            surf.fill((24, 20, 34))
            for _ in range(7):
                x, y = rng.randint(0, 50), rng.randint(0, 50)
                pygame.draw.ellipse(surf, rng.choice([(34, 28, 48), (18, 14, 28)]), (x, y, rng.randint(10, 18), rng.randint(8, 14)))
            surf.fill((70, 54, 100), (0, 0, TILE, 4))
        elif letter == "T":
            surf.blit(self.art["chest"], (0, 4))
        elif letter == "N":                         # Wren the ghost, glowing softly
            surf.blit(self.small_glow, (16, 16))
            ghost = self.art["wren"].copy()
            ghost.set_alpha(215)
            surf.blit(ghost, (0, 0))
        elif letter == "Q":                         # a lost lantern
            surf.blit(self.gem_glow, (12, 12))
            surf.blit(self.art["lantern"], (0, 0))
        elif letter == "+":
            surf.blit(self.art["signpost"], (0, 0))
        elif letter == "L":                         # a landmark, painted dark: the Black Lighthouse, the Dead Giant Tree
            picture = self.art["Lighthouse" if self.game.night_landmarks.get(pos) == "Black Lighthouse" else "Queen Oak"].copy()
            picture.fill((120, 100, 150), special_flags=pygame.BLEND_RGB_MULT)
            surf.blit(picture, (0, 0))
        elif letter in "=#":                        # the Shadow Bridge (broken, or fixed) over the black river
            surf.fill((16, 18, 36))
            surf.blit(self.art["broken_bridge" if letter == "=" else "bridge"], (0, 0))
            surf.fill((30, 20, 44), special_flags=pygame.BLEND_RGB_ADD)
        return surf

    def paint_path(self, surf, rng, r, c, edge=None):
        """The brown dirt path. It joins up with the path squares (and houses) next to it.
        edge: the colour along its sides (trodden grass, unless the ground here is snow or sand)."""
        dirt, dark, light = PATH_DIRT
        joins = [(dr, dc) for dr, dc in rules.DIRECTIONS.values()
                 if self.game.in_bounds((r + dr, c + dc)) and self.game.map[r + dr][c + dc] in "RH=#"]
        # a band of dirt from the middle out to every side that joins up - first the trodden grass, then the dirt
        for color, extra in ((edge or PATH_EDGE, 3), (dirt, 0)):
            pygame.draw.circle(surf, color, (32, 32), 15 + extra)
            for dr, dc in joins:
                for step in range(4, 37, 4):
                    pygame.draw.circle(surf, color, (32 + dc * step, 32 + dr * step), rng.randint(12, 14) + extra)
        # pebbles, and a few footprints, only on the dirt
        for _ in range(14):
            x, y = rng.randint(4, 58), rng.randint(4, 58)
            if surf.get_at((x, y))[:3] == dirt:
                pygame.draw.ellipse(surf, rng.choice([dark, light]), (x, y, rng.randint(3, 5), rng.randint(2, 4)))
        for _ in range(3):
            x, y = rng.randint(22, 38), rng.randint(22, 38)
            pygame.draw.ellipse(surf, (148, 108, 68), (x, y, 4, 6))
            pygame.draw.ellipse(surf, (148, 108, 68), (x + 6, y + 4, 4, 6))

    def paint_grass(self, surf, rng, ground=GRASS):
        """Grass with little specks (or snow, or sand: ground is its colour and its two speck colours)."""
        surf.fill(ground[0])
        for _ in range(26):
            color = rng.choice(ground[1:])
            surf.fill(color, (rng.randint(0, 60), rng.randint(0, 60), 2, 4))
        if rng.random() < 0.5:
            surf.fill(rng.choice([(255, 230, 90), (255, 255, 255), (240, 110, 140)]),
                      (rng.randint(4, 56), rng.randint(40, 58), 3, 3))

    def paint_map_ice(self, surf, rng):
        """Slippery ice: pale blue, with shiny streaks and a crack or two."""
        surf.fill((174, 214, 240))
        for _ in range(5):
            x, y = rng.randint(2, 48), rng.randint(4, 58)
            pygame.draw.line(surf, (236, 248, 255), (x, y), (x + rng.randint(8, 16), y - rng.randint(0, 4)), 2)
        x = rng.randint(10, 50)
        pygame.draw.lines(surf, (132, 182, 222), False, [(x, 0), (x + rng.randint(-8, 8), 30), (x + rng.randint(-12, 12), 63)], 1)

    def paint_reeds(self, surf, rng):
        """Tall reeds in the marsh, growing out of muddy puddles. Some have brown cattails on top."""
        surf.fill((78, 116, 88))
        for _ in range(5):
            pygame.draw.ellipse(surf, (60, 88, 80), (rng.randint(0, 48), rng.randint(0, 54), rng.randint(12, 18), 8))
        for _ in range(14):
            x, y = rng.randint(4, 60), rng.randint(22, 62)
            top = (x + rng.randint(-4, 4), y - rng.randint(14, 26))
            pygame.draw.line(surf, rng.choice([(122, 164, 72), (98, 142, 60)]), (x, y), top, 2)
            if rng.random() < 0.35:
                pygame.draw.ellipse(surf, (122, 84, 50), (top[0] - 2, top[1] - 4, 5, 9))

    def paint_vent(self, surf, rng):
        """A steam vent: a hot crack in the ground, glowing orange inside. (The steam is drawn every frame.)"""
        pygame.draw.ellipse(surf, (80, 46, 38), (14, 32, 36, 20))
        pygame.draw.ellipse(surf, (54, 30, 28), (18, 35, 28, 14))
        pygame.draw.ellipse(surf, (236, 116, 44), (24, 39, 16, 7))
        pygame.draw.ellipse(surf, (255, 190, 90), (28, 41, 8, 3))
        for _ in range(4):                             # a few pebbles around the crack
            surf.fill((140, 90, 66), (rng.randint(10, 52), rng.randint(28, 56), 4, 3))

    def mine_theme(self, pos):
        """What kind of cave is under this Mine: stone, crystal, lava or moss. The cave plan knows!"""
        cave_text = self.game.cave_plan.get(pos) or self.game.secret_mines.get(pos)
        return caves.level_theme(cave_text) if cave_text else "stone"

    def paint_mine(self, surf, rng, theme="stone"):
        """A Mine: a cave door in the rock. It looks like the cave inside, so you know what you'll find."""
        look = MINE_LOOKS.get(theme, MINE_LOOKS["stone"])
        surf.fill(look["rock"])
        for _ in range(9):
            x, y = rng.randint(0, 54), rng.randint(0, 54)
            pygame.draw.ellipse(surf, look["pebble"], (x, y, rng.randint(8, 14), rng.randint(6, 10)))
            surf.fill(look["shine"], (x + 2, y + 1, 3, 2))
        # cave entrance with wooden beams
        pygame.draw.ellipse(surf, (28, 22, 24), (18, 18, 28, 26))
        surf.fill((28, 22, 24), (18, 30, 28, 26))
        surf.fill((120, 78, 40), (13, 24, 6, 32))
        surf.fill((120, 78, 40), (45, 24, 6, 32))
        surf.fill((140, 92, 48), (11, 20, 42, 6))
        surf.fill(look["sparkle"], (rng.choice([6, 52]), rng.randint(8, 50), 3, 3))   # ore sparkle
        if theme == "lava":
            self.paint_mine_glow(surf, rng)
        if "moss" in look:
            self.paint_mine_moss(surf, rng, look["moss"])
        if "ice" in look:
            self.paint_mine_ice(surf, rng, look["ice"])

    def paint_mine_glow(self, surf, rng):
        """A red lava cave: the door glows hot from the lava deep inside."""
        surf.set_clip((19, 18, 26, 38))                        # only paint inside the door
        for i, color in enumerate([(66, 22, 20), (112, 32, 22), (170, 56, 26), (226, 104, 38), (255, 166, 66)]):
            width, height = 40 - i * 6, 32 - i * 5             # smaller and brighter, down near the lava
            pygame.draw.ellipse(surf, color, (32 - width // 2, 58 - height // 2, width, height))
        surf.set_clip(None)
        for _ in range(3):                                     # embers floating up
            surf.fill((255, 190, 90), (rng.randint(22, 41), rng.randint(28, 38), 2, 2))

    def paint_mine_moss(self, surf, rng, colors):
        """Moss growing all over the door: a lumpy blanket on top, and bits hanging down."""
        dark, middle, light = colors
        for x in range(9, 52, 5):                              # the blanket on the top beam
            pygame.draw.ellipse(surf, dark, (x, rng.randint(15, 18), rng.randint(8, 10), 9))
        for x in range(10, 52, 5):
            pygame.draw.ellipse(surf, middle, (x, rng.randint(14, 16), rng.randint(6, 8), 6))
            surf.fill(light, (x + 2, rng.randint(14, 16), 3, 2))
        for _ in range(8):                                     # wiggly bits of moss hanging from the beam
            x, y = rng.randint(12, 50), 24
            for _ in range(rng.randint(2, 6)):
                surf.fill(middle, (x, y, 2, 2))
                x, y = x + rng.choice([-1, 0, 0, 1]), y + 2
            surf.fill(dark, (x, y, 2, 1))
        for post_x in (13, 45):                                # moss climbing up the posts
            for _ in range(3):
                surf.fill(middle, (post_x + rng.randint(-1, 3), rng.randint(32, 54), 4, rng.randint(3, 6)))
        for _ in range(4):                                     # flat clumps of moss on the rock
            x, y = rng.choice([rng.randint(0, 5), rng.randint(53, 57)]), rng.randint(2, 54)
            pygame.draw.ellipse(surf, dark, (x, y + 1, 9, 4))
            pygame.draw.ellipse(surf, middle, (x + 1, y, 7, 3))
        for x in (rng.randint(3, 8), rng.randint(55, 60)):     # little tufts at the bottom
            for dx in (-2, 0, 2):
                pygame.draw.line(surf, middle, (x + dx, 63), (x + dx * 2, 63 - rng.randint(4, 7)), 2)

    def paint_mine_ice(self, surf, rng, colors):
        """A blue crystal cave: ice on the door, icicles, and crystals growing by the door."""
        blue, pale, white = colors
        surf.fill(pale, (10, 17, 44, 4))                       # ice on the top beam
        surf.fill(white, (12, 17, 38, 1))
        for x in range(12, 51, 4):                             # icicles hanging down
            length = rng.randint(3, 10)
            pygame.draw.polygon(surf, pale, [(x, 25), (x + 3, 25), (x + 1, 25 + length)])
        for _ in range(3):                                     # crystals twinkling deep inside
            surf.fill(blue, (rng.randint(22, 41), rng.randint(36, 52), 2, 2))
        for _ in range(6):                                     # frost on the rock
            surf.fill(white, (rng.randint(0, 62), rng.randint(0, 62), 2, 1))
        for x, height in ((3, 9), (7, 16), (11, 10), (53, 11), (57, 17), (61, 8)):   # two crystal clusters
            self.paint_crystal(surf, x, 62, height + rng.randint(-2, 2), colors)

    def paint_crystal(self, surf, x, bottom, height, colors):
        """One pointy ice crystal standing up from the ground."""
        blue, pale, white = colors
        top = bottom - height
        pygame.draw.polygon(surf, blue, [(x - 2, bottom), (x - 2, top + 3), (x, top), (x + 2, top + 3), (x + 2, bottom)])
        pygame.draw.polygon(surf, pale, [(x - 2, bottom), (x - 2, top + 3), (x, top), (x, bottom)])   # the light side
        surf.fill(white, (x - 1, top + 3, 1, max(1, height - 6)))                                     # a shine

    def reset_visuals(self):
        self.popups = []
        self.particles = []
        self.arrows = []
        self.battle_popups = []
        self.battle_buttons = []
        self.shake = 0.0
        self.flash = 0.0
        self.banner = None
        self.player_px = list(tile_px(self.game.player.pos))
        self.camera = self.camera_target()
        self.cam = (round(self.camera[0]), round(self.camera[1]))
        self.monster_px = {}
        self.map_facing = "down"        # the way the Hero looks on the world map
        self.map_steps = 0              # steps he took on the map: his walking picture changes every step
        self.map_step_time = 0.0        # counts down after each step: while it's above 0 he's still walking
        self.map_last_spot = self.game.player.pos
        self.forge = None
        self.forge_return = "play"
        self.story_return = "play"
        self.story_page = 0
        self.sunfang = None
        self.end_timer = None
        self.player_hit = 0.0
        self.monster_hit = 0.0
        self.lunge = 0.0
        self.battle_over_at = None
        self.battle_ready_at = 0.0          # in a map fight, A, R and E only work after this time (no mashing A)
        self.fade = 0.0                 # fades to black when you go in or out of a cave
        self.intro_fade = 0.0           # the last intro card fading away into the world
        self.last_card = None           # a picture of that card, to fade away
        self.motes = []                 # embers, sparkles and fireflies floating in a cave
        self.bats = []                  # bats flapping through the castle
        self.built_cave = None          # the cave whose blocks are painted, ready to draw
        self.squash = {}                # mushrooms squashed by a bounce: (r, c) -> time left
        self.walked = 0.0               # how far you've walked in caves (it picks your walking picture)
        self.walk_x = 0.0               # where you were last time we drew you
        self.climbed = 0.0              # how far you've climbed ladders and walls (it picks your climbing picture)
        self.climb_y = 0.0              # how high you were last time we drew you
        self.jump_was_held = False
        self.space_was_held = False
        self.use_was_held = False
        self.shoot_was_held = False
        self.return_state = "play"      # where the help screen goes back to
        self.card_return = "play"       # where the LEVEL UP! card goes back to
        self.craft_return = "play"      # where the Craft menu goes back to
        self.craft_flash = None         # (which row, when) - the row you just crafted lights up
        self.craft_pick = 0             # which row of the Craft menu is highlighted
        self.craft_rows = []            # where the Craft menu's rows are, so the mouse can pick them
        self.card_time = 0.0            # when the LEVEL UP! card opened
        self.card_rows = []             # where the powers are on the LEVEL UP! card, so you can click them
        self.bubble = None              # the tip bubble that's showing: its name, where it points, when it opened
        self.tip_return = "play"        # where a tip bubble goes back to
        self.tip_wait = TIP_GAP         # seconds until the game looks for a tip again
        self.tip_turn = None            # the turn the last tip closed on (on the map, the next one waits for a step)

    def new_game(self):
        name = self.name_input.strip() or "Adventurer"
        saved = phase2.load_game(self.save_slot) if self.mode == "continue" else None
        if saved:
            self.mode = "phase2"            # (playing again after this one starts a new Phase 2 game)
            self.continue_game(saved)
            return
        if self.mode in ("phase2", "continue"):
            self.game = phase2.new_game(name, self.seed, self.save_slot)
        else:
            self.game = rules.Game(name, seed=self.seed)
        if self.games_started:
            self.game.story.clear()         # playing again: you've already seen the intro
        self.games_started += 1
        if self.skip_to_throne:
            self.start_in_throne_room()
        elif self.skip_to_castle:
            self.start_next_to_castle()
        elif self.skip_to_nightfall:
            self.start_in_nightfall()
        self.in_intro = bool(self.game.story)   # the first story cards are coming, with their spooky tune
        phase2.set_caption(self.game)       # the window's name (Phase 2 has its own)
        self.build_tiles()                  # a new world: houses you built last time are gone
        self.reset_visuals()
        self.state = "play"

    def continue_game(self, saved):
        """Back into a saved Phase 2 game, on the map where you saved it."""
        self.game = saved
        self.game.story.clear()
        self.games_started += 1
        self.in_intro = False
        phase2.set_caption(self.game)
        self.build_tiles()
        self.reset_visuals()
        self.state = "play"

    def start_in_nightfall(self):
        """For play-testing (python game.py --nightfall): skip the home world and start in Nightfall Hollow,
        just through the Portal, with full food. Everything there (beacons, Sun Shards, the castle) is still to do."""
        game = self.game
        for quest in game.quests:
            quest.progress = quest.goal_count
        game.go_to_nightfall()
        game.take_effects()
        game.story.clear()
        game.player.food = game.player.max_food
        game.reveal()
        game.log("Play-test shortcut: you're in Nightfall Hollow!", "quest")

    def start_next_to_castle(self):
        """For play-testing (python game.py --castle): skip ahead to Nightfall Hollow, right next to
        the castle, with 3 diamonds and full food. Walk onto the castle to forge Sunfang and go in."""
        game = self.game
        for quest in game.quests:
            quest.progress = quest.goal_count
        game.go_to_nightfall()
        game.take_effects()
        game.story.clear()
        game.player.pos = min(game.neighbors(game.castle), key=lambda spot: spot[1])
        game.player.diamonds = rules.SUNFANG_DIAMONDS
        game.player.food = game.player.max_food
        game.monsters = [m for m in game.monsters if rules.distance(m.pos, game.castle) > 4]
        game.reveal()
        game.log("Play-test shortcut: the castle is right next to you!", "quest")

    def start_in_throne_room(self):
        """For play-testing (python game.py --throne): skip ahead to the throne room, with Sunfang,
        and fight the Shadow King straight away."""
        game = self.game
        self.start_next_to_castle()
        game.player.diamonds -= rules.SUNFANG_DIAMONDS          # as if you forged Sunfang...
        game.player.sunfang = True
        game.player.pos = game.castle
        game.open_castle()                                      # ...walked into the castle...
        game.take_effects()
        game.reach_throne()                                     # ...and through all 5 levels
        game.story.clear()
        game.log("Play-test shortcut: straight to the Shadow King!", "quest")

    # ----- main loop --------------------------------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.step(dt)
            pygame.display.flip()

    def step(self, dt):
        for event in pygame.event.get():
            self.handle_event(event)
        if not self.running and self.state != "title":
            phase2.on_quit(self.game)       # quitting: a Phase 2 game saves itself
        if phase2.paused(self):             # Phase 2's pause menu: nothing moves or ticks, the game is frozen
            phase2.draw_pause(self)
            return
        self.update(dt)
        self.draw()

    # ----- input --------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if self.state != "title" and phase2.pause_event(self, event):   # Phase 2: P or ESC pauses
            return
        if self.state != "title" and phase2.on_event(self, event):   # Phase 2: talking, the shop, the quest log
            return
        getattr(self, "on_" + self.state)(event)

    def on_title(self, event):
        if phase2.title_event(self, event):         # Phase 2's save slot list is open
            return
        if event.type == pygame.TEXTINPUT:
            if len(self.name_input) < 12 and event.text.isprintable():
                self.name_input += event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if not phase2.open_slots(self):     # Load / Phase 2: pick a save slot first
                    self.new_game()
            elif event.key == pygame.K_TAB:
                self.tips.switch()                # tip bubbles on or off
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):     # Classic, Phase 2 or Continue
                way = 1 if event.key == pygame.K_RIGHT else -1
                self.mode = self.modes[(self.modes.index(self.mode) + way) % len(self.modes)]
            elif event.key == pygame.K_ESCAPE:
                self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.tips_switch and self.tips_switch.collidepoint(event.pos):
                self.tips.switch()
            for mode, button in self.mode_buttons.items():
                if button.collidepoint(event.pos):
                    self.mode = mode

    def on_play(self, event):
        if phase2.on_play(self, event):         # Phase 2: the waystone travel list
            return
        if event.type != pygame.KEYDOWN or self.game.over:
            return
        key, game = event.key, self.game
        if key in MOVE_KEYS:
            direction = MOVE_KEYS[key]
            self.map_facing = direction         # he turns that way, even if something is in the way
            if not phase2.is_phase2(game):      # (Phase 2: he walks while the key is held, in update)
                game.do(direction)
        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            game.do("act")
        elif key == pygame.K_e:
            game.do("eat")
        elif key == pygame.K_z:
            game.do("wait")
        elif key == pygame.K_t:
            game.do("chop")
        elif key == pygame.K_f:
            game.do("shoot")
        elif key == pygame.K_c:
            self.open_craft("play")
        elif key == pygame.K_h:
            self.return_state = "play"
            self.state = "help"
        elif key == pygame.K_m:
            game.log("Sound on." if self.sounds.toggle() else "Sound off.")
        elif key == pygame.K_n:
            game.log("Music on." if self.music.toggle() else "Music off.")
        elif key == pygame.K_ESCAPE:
            self.running = False

    def on_cave(self, event):
        """Running and jumping are read every frame in cave_controls(). These are the other keys."""
        if event.type != pygame.KEYDOWN or self.game.over:
            return
        if event.key == pygame.K_e:
            self.game.eat()
        elif event.key == pygame.K_h:
            self.return_state = "cave"
            self.state = "help"
        elif event.key == pygame.K_c:
            self.open_craft("cave")
        elif event.key == pygame.K_m:
            self.game.log("Sound on." if self.sounds.toggle() else "Sound off.")
        elif event.key == pygame.K_n:
            self.game.log("Music on." if self.music.toggle() else "Music off.")
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    def cave_controls(self):
        keys = pygame.key.get_pressed()
        jump = any(keys[k] for k in JUMP_KEYS)
        use = any(keys[k] for k in USE_KEYS)
        shoot = any(keys[k] for k in SHOOT_KEYS)
        space = any(keys[k] for k in SPACE_KEYS)
        controls = {"left": any(keys[k] for k in LEFT_KEYS), "right": any(keys[k] for k in RIGHT_KEYS),
                    "up": any(keys[k] for k in UP_KEYS), "down": any(keys[k] for k in DOWN_KEYS), "jump": jump,
                    "jump_pressed": jump and not self.jump_was_held, "use_pressed": use and not self.use_was_held,
                    "shoot_pressed": shoot and not self.shoot_was_held,
                    "space_pressed": space and not self.space_was_held}
        self.jump_was_held, self.use_was_held, self.shoot_was_held = jump, use, shoot
        self.space_was_held = space
        return phase2.cave_controls(self, keys, controls)     # (Phase 2: R fights, G digs and opens)

    def on_battle(self, event):
        battle = self.game.battle
        if battle is None:
            self.state = "play"
            return
        action = None
        if event.type == pygame.KEYDOWN:
            action = phase2.battle_keys(self.game, {pygame.K_a: "attack", pygame.K_1: "attack",
                      pygame.K_r: "run", pygame.K_2: "run",
                      pygame.K_e: "eat", pygame.K_3: "eat",
                      pygame.K_SPACE: "continue", pygame.K_RETURN: "continue"}).get(event.key)   # (Phase 2: R attacks)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = "continue"
            for name, rect in self.battle_buttons:
                if rect.collidepoint(event.pos):
                    action = name
        if action is None:
            return
        if battle.over:
            # wait a moment so you can see how the fight ended
            if action == "continue" and self.time - (self.battle_over_at or self.time) > 0.4:
                self.game.close_battle()
                self.state = "play"
        elif action != "continue":
            if self.time < self.battle_ready_at:
                return                              # too soon: wait for the pause to end (mashing A does nothing)
            if action == "attack":
                self.lunge = 0.25
            phase2.battle_action(self.game, action, self.time)   # (Phase 2: Attack is a timing strike)
            self.battle_ready_at = self.time + BATTLE_PAUSE   # a short pause before your next turn

    # Everything you can craft, top to bottom in the Craft menu
    CRAFTS = ["house", "boat", "bow", "arrows", "sword", "pickaxe"]

    @property
    def crafts(self):
        """The rows of the Craft menu right now. In Nightfall Hollow there's one more: the Hilt of Sunfang."""
        return self.CRAFTS + (["hilt"] if self.game.world == 2 else [])

    def open_craft(self, back_to):
        """C opens the Craft menu - on the world map, or in a cave."""
        self.craft_return = back_to
        self.craft_flash = None
        self.craft_pick = 0                       # the highlight starts on the top row
        self.state = "craft"

    def on_craft(self, event):
        """The Craft menu: UP and DOWN (or the mouse) move the highlight, and ENTER (or a click) crafts.
        The arrow keys work the menu here, so you don't walk or jump. It stays open until Esc or C."""
        if event.type == pygame.MOUSEMOTION:
            row = self.craft_row_at(event.pos)
            if row is not None:
                self.craft_pick = row             # the mouse is over a row: light it up
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            row = self.craft_row_at(event.pos)
            if row is not None:
                self.craft_pick = row
                self.craft(row)                   # a click crafts it straight away
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_c):
                self.state = self.craft_return
                self.jump_was_held = self.use_was_held = self.shoot_was_held = True   # still holding UP? no jump
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.craft_pick = (self.craft_pick - 1) % len(self.crafts)   # % wraps: up from the top goes to the bottom
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.craft_pick = (self.craft_pick + 1) % len(self.crafts)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.craft(self.craft_pick)
                if self.state == "forge":
                    self.forge.enter_held = True  # ENTER strikes in the forge too: wait until you let go of it

    def craft_row_at(self, spot):
        """Which row of the Craft menu is at this spot on the screen (None if it's not on a row)."""
        return next((i for i, row in enumerate(self.craft_rows) if row.collidepoint(spot)), None)

    def craft(self, i):
        """Make the thing on row i of the Craft menu (or say why you can't yet)."""
        kind, game, in_cave = self.crafts[i], self.game, self.craft_return == "cave"
        if kind == "sword":
            self.start_forge("craft")             # the forging game, then back to this menu
            return
        if kind == "pickaxe":
            made = game.craft_pickaxe() if in_cave else game.do("craft_pickaxe")
        else:
            made = game.build(kind) if in_cave else game.do("build_" + kind)   # on the map, crafting takes a turn
        if made:
            self.craft_flash = (i, self.time)

    def on_levelup(self, event):
        """The LEVEL UP! card: press 1, 2 or 3 (or click one) to pick a power."""
        offer = self.game.power_offer or []
        choice = None
        if event.type == pygame.KEYDOWN:
            choice = {pygame.K_1: 0, pygame.K_KP1: 0, pygame.K_2: 1, pygame.K_KP2: 1,
                      pygame.K_3: 2, pygame.K_KP3: 2}.get(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            choice = next((i for i, row in enumerate(self.card_rows) if row.collidepoint(event.pos)), None)
        if choice is None or choice >= len(offer) or self.time - self.card_time < 0.5:
            return                              # (wait a moment first, so you can read the card)
        self.game.pick_power(offer[choice])
        if self.game.next_power_offer():        # leveled up twice? here's the next card
            self.card_time = self.time
        else:
            self.state = self.card_return
            self.jump_was_held = self.use_was_held = self.shoot_was_held = True

    def start_forge(self, back_to):
        """Open the sword-forging mini-game - on the world map, or in a cave."""
        problem = self.game.forge_problem()
        if problem:
            self.game.log(problem)
            return
        self.forge = Forge()
        self.forge_return = back_to
        self.state = "forge"

    def end_forge(self):
        self.forge = None
        self.state = self.forge_return
        self.jump_was_held = self.use_was_held = self.shoot_was_held = True   # SPACE was for the forge, not a jump

    def on_sunfang(self, event):
        if event.type != pygame.KEYDOWN or not self.sunfang:
            return
        result = self.sunfang.press(event.key)
        if result == "hit":
            self.sounds.play("clang")
            self.shake = 10
            for _ in range(2):
                self.burst(WIDTH // 2, HEIGHT // 2 + 150, random.choice([YELLOW, (255, 255, 255), ORANGE]), 26,
                           layer="screen", speed=420)
        elif result == "miss":
            self.sounds.play("miss")

    def on_story(self, event):
        """ENTER (or SPACE, or a click) shows the next story card. S (or ESC) skips them all."""
        pressed = event.type == pygame.MOUSEBUTTONDOWN or (
            event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER,
                                                           pygame.K_ESCAPE, pygame.K_s))
        if not pressed:
            return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_s):
            self.game.story.clear()
        elif self.game.story:
            self.game.story.pop(0)
            self.story_page += 1
            self.sounds.play("page")
        if not self.game.story:
            self.state = self.story_return
            self.story_page = 0
            self.jump_was_held = self.use_was_held = self.shoot_was_held = True

    def on_tip(self, event):
        """A tip bubble: ENTER, SPACE or a click closes it, and S turns tips off. The keys wait a
        moment first, so you can read it - and a key you were already holding down doesn't count."""
        bubble = self.bubble
        if event.type == pygame.KEYUP:
            bubble["held"].discard(event.key)     # you let go of it: now it counts
        if event.type not in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) or self.time - bubble["time"] < TIP_READ_TIME:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in bubble["held"]:
                return
            if event.key == pygame.K_s:
                self.tips.turn_off()
                self.close_tip()
            elif event.key in TIP_CLOSE_KEYS:
                self.close_tip()
        elif event.button == 1:
            if self.tip_off_button and self.tip_off_button.collidepoint(event.pos):
                self.tips.turn_off()              # you clicked "no more tips"
            self.close_tip()

    def open_tip(self, name, where):
        held = pygame.key.get_pressed()
        self.bubble = {"name": name, "where": where, "time": self.time,
                       "held": {key for key in TIP_CLOSE_KEYS + (pygame.K_s,) if held[key]}}
        self.tip_return = self.state
        self.tip_frame = None                     # (painted the first time the bubble is drawn)
        self.state = "tip"                        # the game waits while you read it
        self.sounds.play("page")

    def close_tip(self):
        self.tips.saw(self.bubble["name"])        # it won't show again
        self.bubble = self.tip_frame = None
        self.state = self.tip_return
        self.tip_wait = TIP_GAP                   # a little break before the next tip
        self.tip_turn = self.game.turn
        self.jump_was_held = self.use_was_held = self.shoot_was_held = self.space_was_held = True

    def on_forge(self, event):
        if event.type == pygame.KEYUP and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.forge.enter_held = False         # you let go of the ENTER that picked "Sword"
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_SPACE or (event.key == pygame.K_RETURN and not self.forge.enter_held):
            grade = self.forge.strike()
            if grade:
                self.sounds.play({"perfect": "clang", "good": "dig", "miss": "crack"}[grade])
        elif event.key == pygame.K_ESCAPE and not self.forge.strikes:   # you can stop before the first strike
            self.end_forge()

    def on_help(self, event):
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            self.state = self.return_state

    def on_end(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.new_game()
            elif event.key == pygame.K_ESCAPE:
                self.running = False

    # ----- update -------------------------------------------------------------

    def tune_here(self):
        """Which tune goes with where you are."""
        if self.state == "title" or (self.in_intro and self.game.story):
            return "intro"                  # the spooky tune, until the first story cards are over
        cave = self.game.cave
        if cave and cave.is_throne_room:                # once he's beaten, the light (and the home tune) comes back
            return "home" if cave.beaten_time is not None else "boss"
        if cave:
            return "castle" if cave.is_castle else cave.theme
        return "nightfall" if self.game.world == 2 else phase2.tune(self, "home")     # (Phase 2: its own map tune)

    def update(self, dt):
        self.time += dt
        game = self.game
        if self.in_intro and not game.story:        # the first story cards are over (or skipped):
            self.in_intro = False                   # fade from the last card into the world,
            self.last_card = self.screen.copy()     # and from the spooky tune into the home tune
            self.intro_fade = INTRO_FADE
        self.music.play(self.tune_here(), self.sounds.enabled, INTRO_FADE if self.intro_fade else MUSIC_FADE)
        if self.state == "cave":
            game.update_cave(dt, self.cave_controls())     # run and jump
        self.switch_views()
        for effect in game.take_effects():
            self.apply_effect(effect)

        # Slide characters smoothly between tiles
        if self.state == "play" and phase2.is_phase2(game):    # Phase 2's map runs in real time (phase2/smooth.py):
            keys = pygame.key.get_pressed()                     # he walks while a move key is held, monsters roam
            phase2.live_map(self, dt, {way for key, way in MOVE_KEYS.items() if keys[key]})
        if game.player.pos != self.map_last_spot:      # a new step: the next walking picture
            self.map_last_spot = game.player.pos
            self.map_steps += 1
            self.map_step_time = MAP_STEP_TIME
        self.map_step_time = max(0.0, self.map_step_time - dt)
        smooth = min(1.0, dt * 16)
        target = phase2.map_spot(self) or tile_px(game.player.pos)     # (Phase 2: anywhere, not only on a square)
        self.player_px[0] = lerp(self.player_px[0], target[0], smooth)
        self.player_px[1] = lerp(self.player_px[1], target[1], smooth)
        for m in game.monsters:
            target = phase2.map_spot(self, m) or tile_px(m.pos)
            spot = self.monster_px.setdefault(id(m), list(target))
            spot[0] = lerp(spot[0], target[0], smooth)
            spot[1] = lerp(spot[1], target[1], smooth)
        if game.cave:
            target = self.cave_camera_target()
            follow = min(1.0, dt * 8)
            self.camera = [lerp(self.camera[0], target[0], follow), lerp(self.camera[1], target[1], follow)]
        else:
            self.camera = self.camera_target()

        # Timers
        self.shake = max(0.0, self.shake - dt * 30)
        self.flash = max(0.0, self.flash - dt)
        self.player_hit = max(0.0, self.player_hit - dt)
        self.monster_hit = max(0.0, self.monster_hit - dt)
        self.lunge = max(0.0, self.lunge - dt)
        self.fade = max(0.0, self.fade - dt)
        self.intro_fade = max(0.0, self.intro_fade - dt)
        self.squash = {spot: t - dt for spot, t in self.squash.items() if t > dt}
        for item in self.popups + self.battle_popups + self.arrows:
            item["age"] += dt
        self.popups = [p for p in self.popups if p["age"] < 1.2]
        self.battle_popups = [p for p in self.battle_popups if p["age"] < 1.0]
        self.arrows = [a for a in self.arrows if a["age"] < 0.3]
        for p in self.particles:
            p["age"] += dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += p.get("gravity", 0) * dt
        self.particles = [p for p in self.particles if p["age"] < p["life"]]
        if self.banner:
            self.banner["age"] += dt
            if self.banner["age"] > 2.2:
                self.banner = None

        # The forging mini-game
        if self.state == "forge" and self.forge:
            self.forge.update(dt)
            if self.forge.done:
                game.finish_forge(self.forge.strikes)
                self.end_forge()
        game.check_chipped_swords()               # a sword down to its last few hits: a chip sound and a message

        # Forging Sunfang
        if self.state == "sunfang" and self.sunfang:
            self.sunfang.update(dt)
            if self.sunfang.phase == "finale" and not self.sunfang.celebrated:
                self.sunfang.celebrated = True
                self.sounds.play("sunfang")
                self.flash = 0.35
            if self.sunfang.done:
                game.finish_sunfang(self.sunfang.perfect)
                self.sunfang = None
                self.state = "play"

        # Switch between screens
        if self.state == "craft" and (game.battle or game.story or game.over or game.level_ups or game.forging
                                      or (self.craft_return == "cave") != bool(game.cave)):
            self.state = self.craft_return          # something happened (a monster attacks!): close the Craft menu
        if self.state in ("play", "cave") and game.story:   # a story card to show
            self.story_return = self.state
            self.state = "story"
        if self.state in ("play", "cave") and not game.battle and not game.over and game.next_power_offer():
            self.card_return = self.state           # you leveled up: pick a power! (after the fight, if you're in one)
            self.card_time = self.time
            self.state = "levelup"
        if self.state == "play" and game.forging and not game.story and not self.sunfang:
            self.sunfang = SunfangForge()       # the diamonds start to glow...
            self.state = "sunfang"
        if self.state in ("play", "cave"):
            if self.state == "play" and game.battle:
                self.state = "battle"
                self.battle_over_at = None
                self.battle_ready_at = self.time + BATTLE_PAUSE   # a short pause before your first turn
            elif game.over:
                if self.end_timer is None:
                    self.end_timer = 1.4
                self.end_timer -= dt
                if self.end_timer <= 0:
                    self.state = "end"
        elif self.state == "battle" and game.battle and game.battle.over:
            if self.battle_over_at is None:
                self.battle_over_at = self.time
                if game.battle.result in ("won", "exploded"):
                    x, y = self.battle_spot("monster")
                    self.burst(x + 64, y + 64, (200, 200, 210), 30, layer="battle")
        if self.state != "title":
            phase2.update_screens(self, dt)       # Phase 2: someone to talk to? (phase2/draw_people.py)
        self.look_for_tips(dt)
        if self.state == "end" and game.won and random.random() < 0.5:
            self.particles.append({
                "x": random.uniform(0, WIDTH), "y": -10, "vx": random.uniform(-30, 30),
                "vy": random.uniform(80, 160), "life": 5, "age": 0, "size": 6,
                "color": random.choice([YELLOW, GREEN, (110, 215, 255), (240, 110, 200)]),
                "layer": "screen"})

    def look_for_tips(self, dt):
        """A few times a second, see if a tip fits (tutorial.py says which). If one does, show it
        and wait. Never during a fight, a story card, a menu, a banner or a fade."""
        game = self.game
        self.tip_wait = max(0.0, self.tip_wait - dt)
        if self.state not in ("play", "cave") or self.tip_wait > 0 or not self.allow_tips:
            return
        if (game.battle or game.story or game.over or game.forging or self.banner or self.fade
                or self.intro_fade or (game.cave and self.built_cave is not game.cave)):
            return
        if not game.cave and game.turn == self.tip_turn:
            return                                # on the map, take a step before the next tip
        self.tip_wait = TIP_LOOK_EVERY
        for name, where in self.tips.due(game):
            if self.tip_target(where):            # only when you can see the thing it's about
                self.open_tip(name, where)
                return

    def tip_target(self, where):
        """Where the thing a tip is about is on the screen (a Rect), or None if it's off the screen."""
        game, (cam_x, cam_y) = self.game, self.cam
        if where[0] == "panel":
            return self.panel_spots.get(where[1])
        if where[0] == "you" and game.cave:
            you = game.cave.you
            spot = pygame.Rect(you.x * TILE - cam_x, you.y * TILE - cam_y, you.w * TILE, you.h * TILE)
        elif where[0] == "you":
            spot = pygame.Rect(self.player_px[0] - cam_x, self.player_px[1] - cam_y, TILE, TILE)
        else:
            r, c = where[1]
            spot = pygame.Rect(c * TILE - cam_x, r * TILE - cam_y, TILE, TILE)
        return spot if self.view.get_rect().contains(spot) else None

    def switch_views(self):
        """Climbing down into a cave, or back out to the world map."""
        game = self.game
        if game.cave and self.built_cave is not game.cave:
            self.build_cave_tiles(game.cave)    # paint a new cave (or the castle) before it's drawn
            self.camera = self.cave_camera_target()
            self.popups, self.particles, self.arrows = [], [], []
            self.fade = 0.4
        if self.state == "play" and game.cave:
            self.state = "cave"
            self.jump_was_held = True       # don't jump just because SPACE is still held down
            self.space_was_held = True
            self.use_was_held = True
            self.shoot_was_held = True
            return
        elif self.state == "cave" and not game.cave:
            self.state = "play"
            self.player_px = list(tile_px(game.player.pos))
            self.camera = self.camera_target()
        else:
            return
        self.popups, self.particles, self.arrows = [], [], []
        self.fade = 0.4

    def effect_px(self, e):
        """Where an effect happens, in pixels on the world map - or in the cave."""
        if "cave_xy" in e:
            return (e["cave_xy"][0] * TILE, e["cave_xy"][1] * TILE)
        return tile_center(e["pos"])

    def apply_effect(self, e):
        kind = e["type"]
        if kind == "sound":
            self.sounds.play(e["name"])
        elif kind == "popup":
            x, y = self.effect_px(e)
            self.popups.append({"x": x, "y": y - 20, "text": e["text"],
                                "color": KIND_COLORS.get(e["kind"], TEXT), "age": 0.0})
        elif kind == "shake":
            self.shake = max(self.shake, 3 + 2 * e["amount"])
            self.player_hit = 0.25
        elif kind == "new_world":                  # through the Portal!
            self.build_tiles()
            self.player_px = list(tile_px(self.game.player.pos))
            self.monster_px = {}
            self.popups, self.particles, self.arrows = [], [], []
            self.camera = self.camera_target()
            self.flash, self.fade = 0.35, 0.8
        elif kind == "knockout":                   # out of health: you lost a life and woke up somewhere safe
            self.banner = {"text": e.get("text", "KNOCKED OUT!"),
                           "sub": e.get("sub", "Back to the start of this level. Try again!"), "age": 0.0}
            self.popups, self.particles = [], []
            self.fade = 0.8
            if self.game.cave and self.built_cave is self.game.cave:
                self.camera = self.cave_camera_target()
            elif not self.game.cave:               # on the map: you woke up at a house (or a shrine)
                self.player_px = list(tile_px(self.game.player.pos))
                self.camera = self.camera_target()
        elif kind in ("castle_level", "land"):      # into a new level of the castle, or a new land
            self.banner = {"text": e["text"], "sub": e["sub"], "age": 0.0}
        elif kind == "lookout":                    # you climbed up a landmark: the fog lifts all around
            x, y = self.effect_px(e)
            self.burst(x, y - 20, (255, 236, 160), 26, speed=200)
        elif kind == "door_slam":                  # BANG! the throne room door slams shut behind you
            self.shake = 14
            r, c = self.game.cave.find("S")
            self.burst((c + 0.5) * TILE, (r + 1) * TILE, (150, 140, 160), 30, speed=200)
        elif kind == "king_angry":                 # half his health is gone: now he's ANGRY!
            self.banner = {"text": "HE'S ANGRY!", "sub": "Faster, and two fireballs at a time!", "age": 0.0}
            self.shake = 12
            self.flash = 0.2
        elif kind == "king_beaten":                # you beat him! he bursts into light
            x, y = self.effect_px(e)
            for color in (YELLOW, (255, 255, 255), ORANGE, (200, 120, 255)):
                self.burst(x, y, color, 40, speed=420)
            self.flash = 0.35
            self.shake = 20
        elif kind == "tile":
            self.paint_tile(*e["pos"])          # something new was built here...
            for dr, dc in rules.DIRECTIONS.values():
                spot = (e["pos"][0] + dr, e["pos"][1] + dc)
                if spot in self.tiles and self.game.map[spot[0]][spot[1]] == "R":
                    self.paint_tile(*spot)      # ...and the path next to it joins up with it
        elif kind == "beacon":                  # a beacon blazes: golden light pours out of the shrine
            x, y = self.effect_px(e)
            for color in (YELLOW, (255, 255, 255), ORANGE):
                self.burst(x, y - 10, color, 36, speed=360)
            self.flash = 0.3
        elif kind == "timber":                  # a tree falls: leaves and wood chips everywhere
            x, y = self.effect_px(e)
            self.burst(x, y - 10, (70, 150, 60), 30, speed=220)
            self.burst(x, y, (150, 102, 56), 14, speed=160)
            self.shake = max(self.shake, 6)
        elif kind == "sparkle":
            x, y = self.effect_px(e)
            self.burst(x, y, (120, 235, 255), 24)
            self.burst(x, y, (255, 255, 255), 10)
        elif kind == "arrow":
            self.arrows.append({"start": tile_center(e["start"]), "end": tile_center(e["end"]), "age": 0.0,
                                "fire": e.get("fire", False)})
        elif kind == "explosion":
            self.flash = 0.35
            self.shake = 16
            x, y = self.battle_spot("monster")
            self.burst(x + 64, y + 64, ORANGE, 40, layer="battle", speed=380)
            self.burst(x + 64, y + 64, YELLOW, 25, layer="battle", speed=300)
        elif kind == "rubble":
            x, y = self.effect_px(e)
            self.burst(x, y, (124, 114, 134), 16, speed=220)
            if e.get("ore"):
                self.burst(x, y, (120, 235, 255), 22, speed=260)
        elif kind == "boom":
            x, y = self.effect_px(e)
            self.burst(x, y, ORANGE, 40, speed=380)
            self.burst(x, y, YELLOW, 25, speed=300)
            self.flash = 0.25
            self.shake = 16
        elif kind == "poof":
            x, y = self.effect_px(e)
            self.burst(x, y, (220, 220, 232), 26, speed=200)
        elif kind == "bounce":
            x, y = self.effect_px(e)
            self.burst(x, y, (255, 255, 255), 8, speed=120)
            spot = (round(e["cave_xy"][1]), math.floor(e["cave_xy"][0]))
            self.squash[spot] = 0.25
        elif kind == "crumble":
            x, y = self.effect_px(e)
            self.burst(x, y, (176, 140, 96), 14, speed=120)
        elif kind == "pound":                       # SLAM! a ground pound
            x, y = self.effect_px(e)
            self.burst(x, y, (210, 204, 190), 22, speed=240)
            self.shake = max(self.shake, 8)
        elif kind == "battle_hit":
            who = e["target"]
            if who == "monster":
                self.monster_hit = 0.3
            else:
                self.player_hit = 0.3
            self.battle_popups.append({"who": who, "text": "-%d" % e["amount"], "color": RED, "age": 0.0})
        elif kind == "battle_miss":
            self.battle_popups.append({"who": e["target"], "text": "miss", "color": DIM, "age": 0.0})
        elif kind == "levelup":                 # golden sparkles (then the LEVEL UP! card pops up)
            cave = self.game.cave
            x, y = self.effect_px({"cave_xy": cave.center} if cave else {"pos": self.game.player.pos})
            self.burst(x, y, YELLOW, 40)

    def burst(self, x, y, color, count, layer="map", speed=160):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            v = random.uniform(speed * 0.3, speed)
            self.particles.append({"x": x, "y": y, "vx": math.cos(angle) * v, "vy": math.sin(angle) * v,
                                   "gravity": 200, "life": random.uniform(0.4, 0.9), "age": 0.0,
                                   "size": random.randint(3, 6), "color": color, "layer": layer})

    def camera_target(self):
        """The camera keeps the player in the middle, but stops at the edge of the world."""
        x = self.player_px[0] + TILE // 2 - VIEW_W // 2
        y = self.player_px[1] + TILE // 2 - VIEW_H // 2
        map_w, map_h = self.game.cols * TILE, self.game.rows * TILE      # Nightfall Hollow is a different size
        return [min(max(0, x), max(0, map_w - VIEW_W)), min(max(0, y), max(0, map_h - VIEW_H))]

    def cave_camera_target(self):
        """In a cave the camera looks a little ahead of you, the way you're facing."""
        cave = self.game.cave
        cx, cy = cave.center
        x = cx * TILE + cave.you.facing * TILE * 2 - VIEW_W / 2
        y = cy * TILE - VIEW_H / 2
        return [min(max(0, x), max(0, cave.cols * TILE - VIEW_W)),
                min(max(0, y), max(0, cave.rows * TILE - VIEW_H))]

    def on_screen(self, x, y):
        """Where a spot on the big world map shows up in the camera's view."""
        return (x - self.cam[0], y - self.cam[1])

    def battle_spot(self, who):
        """Top-left corner of the big battle sprites."""
        box = self.battle_box
        if who == "player":
            return (box.x + 110, box.y + 78)
        return (box.right - 110 - 128, box.y + 78)

    # ----- drawing: general ------------------------------------------------------

    def words(self, text, size, color):
        """A picture of some words. Turning letters into pixels is slow (most of all in a web
        browser), and the same words get drawn 60 times a second - so we keep the pictures."""
        key = (text, size, color)
        image = self.word_pictures.get(key)
        if image is None:
            if len(self.word_pictures) > 3000:      # lots of old words (timers, numbers)? start fresh
                self.word_pictures.clear()
            image = self.word_pictures[key] = self.font(size).render(text, True, color)
        return image

    def text(self, surf, text, pos, size=24, color=TEXT, anchor="topleft", shadow=False, alpha=None):
        image = self.words(text, size, color)
        rect = image.get_rect(**{anchor: pos})
        if shadow:
            surf.blit(self.words(text, size, (0, 0, 0)), rect.move(2, 2))
        if alpha is not None:
            image = image.copy()                     # fade a copy, so the kept picture stays bright
            image.set_alpha(alpha)
        surf.blit(image, rect)
        return rect

    def wrap(self, text, size, width):
        """Split text into lines that fit in width pixels (and remember the answer)."""
        key = (text, size, width)
        if key not in self.wrapped:
            if len(self.wrapped) > 1000:
                self.wrapped.clear()
            font = self.font(size)
            lines, line = [], ""
            for word in text.split():
                test = (line + " " + word).strip()
                if font.size(test)[0] <= width:
                    line = test
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)
            self.wrapped[key] = lines
        return list(self.wrapped[key])

    def key_box(self, surf, label, x, y):
        image = self.words(label, 20, TEXT)
        rect = pygame.Rect(x, y, image.get_width() + 12, 22)
        pygame.draw.rect(surf, phase2.color(self, "key", (70, 74, 102)), rect, border_radius=5)    # (Phase 2: darker)
        pygame.draw.rect(surf, phase2.color(self, "key_edge", (124, 130, 170)), rect, 1, border_radius=5)
        surf.blit(image, image.get_rect(center=rect.center))
        return rect.right

    def bar(self, surf, rect, fraction, color, back=(58, 60, 82)):
        rect = pygame.Rect(rect)
        back = phase2.color(self, "bar_back", back) if back == (58, 60, 82) else back     # (Phase 2: darker)
        pygame.draw.rect(surf, back, rect, border_radius=rect.h // 2)
        if fraction > 0:
            fill = rect.copy()
            fill.w = max(rect.h, int(rect.w * min(1.0, fraction)))
            pygame.draw.rect(surf, color, fill, border_radius=rect.h // 2)

    def health_color(self, fraction):
        if fraction > 0.6:
            return GREEN
        if fraction > 0.3:
            return YELLOW
        return RED

    def dim_screen(self, alpha):
        self.overlay.fill((0, 0, 0, alpha))
        self.screen.blit(self.overlay, (0, 0))

    def panel_box(self, rect, border=YELLOW):
        pygame.draw.rect(self.screen, phase2.color(self, "box", (38, 34, 54)), rect, border_radius=18)
        pygame.draw.rect(self.screen, border, rect, 3, border_radius=18)

    def draw(self):
        if self.state == "title":
            self.draw_title()
            return
        if self.state == "tip" and self.tip_frame:
            self.screen.blit(self.tip_frame, (0, 0))     # the game is paused, so the picture under the bubble
            self.draw_tip()                              # stays the same: just the bubble is drawn again
            return
        self.screen.fill(BG)
        self.cam = (round(self.camera[0]), round(self.camera[1]))
        if self.game.cave and self.built_cave is self.game.cave:
            self.draw_cave(self.view)
        else:
            self.draw_world(self.view)
        offset = (random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake))
        self.screen.blit(self.view, offset)
        self.draw_panel()
        self.draw_log()
        if self.banner:
            self.draw_banner()
        if self.state == "battle":
            self.draw_battle()
        elif self.state == "forge":
            self.draw_forge()
        elif self.state == "craft":
            self.draw_craft()
        elif self.state == "levelup":
            self.draw_levelup()
        elif self.state == "story":
            self.draw_story()
        elif self.state == "sunfang":
            self.draw_sunfang()
        elif self.state == "help":
            self.draw_help()
        elif self.state == "tip":
            self.paint_under_tip()
            self.draw_tip()
        elif self.state == "end":
            self.draw_end()
        phase2.draw_over(self)              # Phase 2: the waystone travel list
        phase2.draw_screens(self)                # Phase 2: talking, the shop, the quest log
        self.draw_particles(self.screen, "screen")
        if self.flash > 0:
            self.overlay.fill((255, 240, 200, int(220 * self.flash / 0.35)))
            self.screen.blit(self.overlay, (0, 0))
        if self.fade > 0:
            self.overlay.fill((0, 0, 0, int(255 * min(1.0, self.fade / 0.4))))
            self.screen.blit(self.overlay, (0, 0))
        if self.intro_fade > 0:             # the last story card melts away, and the world appears
            self.last_card.set_alpha(int(255 * self.intro_fade / INTRO_FADE))
            self.screen.blit(self.last_card, (0, 0))

    # ----- drawing: the map ------------------------------------------------------

    def draw_tiles(self, surf, fog=True):
        """Draw just the tiles the camera can see."""
        game = self.game
        cam_x, cam_y = self.cam
        first_r, first_c = cam_y // TILE, cam_x // TILE
        last_r = min(game.rows, (cam_y + surf.get_height()) // TILE + 1)
        last_c = min(game.cols, (cam_x + surf.get_width()) // TILE + 1)
        for r in range(first_r, last_r):
            for c in range(first_c, last_c):
                pos = (r, c)
                x, y = c * TILE - cam_x, r * TILE - cam_y
                if fog and pos not in game.seen:
                    surf.blit(self.fog_tile, (x, y))
                    continue
                surf.blit(self.tiles[pos], (x, y))
                letter = game.map[r][c]
                if letter == "W":
                    self.draw_water(surf, x, y, r, c)
                    if pos in game.sunken_chests:
                        self.draw_bubbles(surf, x, y, c)
                elif letter == "V":
                    self.draw_steam(surf, x, y, c)
                elif letter == "L" and game.tile_name(pos) == "Windmill":
                    sails = pygame.transform.rotate(self.art["sails"], -self.time * 40)     # the sails turn slowly
                    surf.blit(sails, sails.get_rect(center=(x + 31, y + 26)))
                elif letter == "P":
                    self.draw_portal(surf, x, y)
                elif letter in "MS" and pos in game.cleared_mines:
                    # a check mark: you already found this mine's diamond (dark edges, so it shows on moss and ice too)
                    check = [(x + 44, y + 12), (x + 49, y + 18), (x + 58, y + 5)]
                    pygame.draw.lines(surf, (20, 34, 24), False, check, 8)
                    pygame.draw.lines(surf, GREEN, False, check, 4)
                elif letter == "M" and pos in game.glints:
                    # you saw a sparkle over this Mine from a landmark: its diamond is still down there
                    surf.blit(self.gem_glow, self.gem_glow.get_rect(center=(x + 50, y + 12)))
                    self.draw_twinkle(surf, x + 50, y + 12, c)
                    self.draw_twinkle(surf, x + 12, y + 8, c + 1)
                elif letter in "MS" and pos in game.empty_mines:
                    # a grey X: you explored this cave, and there's no diamond in it
                    for color, width in (((40, 40, 48), 7), ((205, 205, 214), 3)):
                        pygame.draw.line(surf, color, (x + 46, y + 6), (x + 57, y + 17), width)
                        pygame.draw.line(surf, color, (x + 57, y + 6), (x + 46, y + 17), width)
                if fog and not game.is_visible(pos):
                    surf.blit(self.dim_tile, (x, y))

    def draw_world(self, surf):
        game = self.game
        self.draw_tiles(surf)
        phase2.draw_dusk(self, surf)                # Phase 2: a thin violet dusk over the ground (phase2/theme.py)
        if game.castle and game.castle in game.seen:      # the Shadow King's castle glows
            x, y = self.on_screen(*tile_px(game.castle))
            glow = pygame.transform.smoothscale(self.violet_glow, (int(150 + 16 * math.sin(self.time * 2)),) * 2)
            surf.blit(glow, glow.get_rect(center=(x + 32, y + 30)))
        bob = math.sin(self.time * 4)

        # Monsters you can see
        for m in game.monsters:
            if not (m.is_alive and game.is_visible(m.pos)):
                continue
            x, y = self.on_screen(*self.monster_px.get(id(m), tile_px(m.pos)))
            crisp = phase2.map_monster_scale(self, m.base_kind)     # Phase 2: new art fills the whole square
            sprite = self.monster_sprite(m.base_kind, crisp or 3, m.shadow)
            if phase2.faces_left(game, m):
                sprite = pygame.transform.flip(sprite, True, False)
            edge = 0 if crisp else 8
            if game.tile(m.pos) != "W":
                surf.blit(self.shadow, (x + 14, y + (56 if crisp else 52)))
            surf.blit(sprite, (x + edge, y + edge + math.sin(self.time * 3 + id(m) % 7) * 2))
            if m.health < m.max_health:
                self.bar(surf, (x + 12, y + 2, 40, 5), m.health / m.max_health, RED)

        phase2.draw_on_map(self, surf)          # Phase 2: the townsfolk
        # The player
        x, y = self.on_screen(*self.player_px)
        name = self.map_facing + (" armor" if game.player.has_armor else "")
        big = phase2.hero_map(self, name, self.map_pose())      # Phase 2: the Hero at 32 x 32 fills his square
        sprite = big or self.map_walk[name][self.map_pose()]
        if self.player_hit > 0 and int(self.time * 20) % 2 == 0:
            sprite = whiten(sprite)
        edge = 0 if big else 8
        if game.here == "W":                # rowing: the Hero sits in his boat
            surf.blit(sprite, (x + edge, y + (-12 if big else 2) + bob * 1.5))
            surf.blit(self.art["boat"], (x + 8, y + 36 + bob * 1.5))
        else:
            surf.blit(self.shadow, (x + 14, y + (56 if big else 52)))
            surf.blit(sprite, (x + edge, y + edge + bob * 1.5))

        # Arrows flying from skeletons
        for a in self.arrows:
            t = a["age"] / 0.3
            sx, sy = self.on_screen(*a["start"])
            ex, ey = self.on_screen(*a["end"])
            hx, hy = lerp(sx, ex, t), lerp(sy, ey, t)
            tx, ty = lerp(sx, ex, max(0, t - 0.25)), lerp(sy, ey, max(0, t - 0.25))
            if a.get("fire"):                           # a fire arrow from Nightfall Hollow
                self.draw_fire_arrow(surf, (tx, ty), (hx, hy))
                continue
            pygame.draw.line(surf, (230, 220, 200), (tx, ty), (hx, hy), 3)
            pygame.draw.circle(surf, (255, 255, 255), (int(hx), int(hy)), 3)

        self.draw_particles(surf, "map", self.cam)
        if game.world == 2:                         # Nightfall Hollow is dark around the edges
            px, py = self.on_screen(self.player_px[0] + TILE // 2, self.player_px[1] + TILE // 2)
            lit = min(len(game.beacons), len(self.nights) - 1)
            surf.blit(self.nights[lit], (px - VIEW_W, py - VIEW_H))
            if game.wisp:                           # the moon wisp: a little floating light you can follow
                wx, wy = self.on_screen(*tile_center(game.wisp))
                bob = math.sin(self.time * 4) * 5
                surf.blit(self.wisp_glow, (wx - 34, wy - 34 + bob))
                pygame.draw.circle(surf, (235, 250, 255), (int(wx), int(wy + bob)), 7)
                pygame.draw.circle(surf, (255, 255, 255), (int(wx), int(wy + bob)), 3)
        phase2.draw_map(self, surf)                 # Phase 2: the night sky, and "!" over monsters chasing you
        self.draw_popups(surf)

    def map_pose(self):
        """Which of the Hero's map pictures to show: 0 is standing, 1 and 2 take turns, one for every step.
        In his boat he just sits."""
        if self.game.here == "W":
            return 0
        target = phase2.map_spot(self) or tile_px(self.game.player.pos)
        sliding = abs(self.player_px[0] - target[0]) + abs(self.player_px[1] - target[1]) > 1
        if self.map_step_time > 0 or sliding:
            return 1 + self.map_steps % 2
        return 0

    def draw_popups(self, surf):
        """Floating numbers and words."""
        for p in self.popups:
            alpha = int(255 * max(0.0, 1 - p["age"] / 1.2))
            x, y = self.on_screen(p["x"], p["y"] - p["age"] * 34)
            self.text(surf, p["text"], (x, y), 28, p["color"], "center", shadow=True, alpha=alpha)

    # ----- drawing: caves ----------------------------------------------------------

    def build_cave_tiles(self, cave):
        """Paint each block of the cave once, the way build_tiles does for the world map."""
        self.built_cave = cave
        self.theme = CAVE_THEMES.get(cave.theme, CAVE_THEMES["stone"])
        self.motes = []
        # Ledges in this cave's look: mossy, icy or burnt. A few of each, so they don't all look the same.
        if cave.is_castle:
            self.cave_ledges, self.cave_crumblies = [self.ledge], [self.crumbly]
        else:
            self.cave_ledges = [self.paint_ledge(LEDGE_WOOD, theme=cave.theme, look=i) for i in range(CAVE_LOOKS)]
            self.cave_crumblies = [self.paint_ledge(CRUMBLY_WOOD, cracks=True, theme=cave.theme, look=i)
                                   for i in range(CAVE_LOOKS)]
        self.fire_glow = make_glow(44, (255, 130, 40))
        self.pool_glow = make_soft_glow(60, (255, 120, 40), 55)     # the warm light over a lava pool
        self.spring_stone = tuple(min(255, v + 40) for v in self.theme["rock"])   # healing springs: a bowl of cave rock
        chunky_look = cave.theme in CAVE_COLORS and not cave.is_castle
        if chunky_look:                             # the big rock picture that every block cuts its piece out of
            if cave.theme not in self.rock_pictures:
                self.rock_pictures[cave.theme] = self.paint_rock_picture(cave.theme)
            self.rock_picture = self.rock_pictures[cave.theme]
            if not self.lava_pictures:
                self.lava_pictures = self.paint_lava_pictures()
            if cave.theme not in self.spring_pictures:
                self.spring_pictures[cave.theme] = self.paint_spring_pictures(cave.theme)
        self.springs = self.spring_pictures.get(cave.theme) if chunky_look else None   # None: the old fountain (stone caves, castle)
        self.cave_tiles, self.cave_decor, self.crumbly_looks = {}, {}, {}
        for r in range(cave.rows):
            for c in range(cave.cols):
                self.paint_cave_tile(cave, r, c)
        cave.dirty.clear()
        self.find_drips(cave)
        self.mote_dots = {}

        # The back wall: a pattern that repeats, drawn behind everything
        self.bats = []
        self.build_castle_things(cave)
        rng = random.Random(cave.mine_pos[0] * 100 + cave.mine_pos[1])
        theme = self.theme
        if chunky_look:                             # rocky shapes far away, in chunky pixels
            self.cave_back = self.paint_cave_back(cave, rng)
        elif cave.theme == "stone" and not cave.is_castle:     # layers of old stone, bricks, fossils...
            self.cave_back = self.paint_stone_back(rng)
        else:
            self.cave_back = pygame.Surface((256, 256))
            self.cave_back.fill(theme["back"])
            if cave.is_castle:
                self.paint_castle_wall(self.cave_back)
            blobs = [rng.choice(theme["blobs"]) for _ in range(24 if theme["blobs"] else 0)]
            for color in blobs:
                x, y = rng.randint(0, 255), rng.randint(0, 255)
                w, h = rng.randint(20, 70), rng.randint(14, 40)
                for dx in (-256, 0, 256):           # draw it again past each edge so the pattern joins up
                    for dy in (-256, 0, 256):
                        pygame.draw.ellipse(self.cave_back, color, (x + dx, y + dy, w, h))

        # Daylight shining in through the way out (in the castle it's purple twilight)
        rows = [r for r in range(cave.rows) if cave.map[r][0] not in LOOKS_SOLID]
        self.daylight = None
        if rows:
            w, h = TILE * 3, TILE * len(rows)
            light = (200, 160, 255) if cave.is_castle else (255, 236, 180)
            self.daylight = pygame.Surface((w, h), pygame.SRCALPHA)
            for i in range(w):
                self.daylight.fill(light + (int(120 * (1 - i / w) ** 2),), (i, 0, 1, h))
            self.daylight_y = rows[0] * TILE

    def paint_cave_tile(self, cave, r, c):
        rng = random.Random(r * 1000 + c * 7 + cave.mine_pos[1])     # same tile, same look
        letter = cave.map[r][c]
        rock = self.theme["rock"]
        image = None
        if cave.is_castle and letter in "#BFM=":
            image = self.stone_ledge if letter == "=" else self.paint_bricks(cave, r, c, cracked=letter == "B")
        elif letter in "#FM":                       # a secret wall (F) and a steam geyser (M) are rock, too
            image = self.paint_rock(cave, r, c, rng, color=rock)
        elif letter == "B":
            image = self.paint_rock(cave, r, c, rng, color=tuple(min(255, v + 22) for v in rock), cracks=True)
        elif letter in "*s":
            image = self.paint_rock(cave, r, c, rng, color=rock, ore="shard" if letter == "s" else True)
        elif letter == "=":
            image = rng.choice(self.cave_ledges)
            if cave.tile(r + 1, c) == "V" and cave.theme in CAVE_COLORS:
                image = self.tie_vine_on(image)
        elif letter == "H":
            image = self.ladder
        elif letter == "V":
            tied = cave.tile(r - 1, c) == "=" and cave.theme in CAVE_COLORS     # tied on under a ledge (tie_vine_on)
            image = self.paint_vine(cave, rng, top=cave.tile(r - 1, c) != "V" and not tied)
        elif letter == "I":
            image = self.paint_ice(cave, r, c, rng)
        elif letter == "%":                         # a climbing wall: rock (or bricks) with handholds
            image = (self.paint_bricks(cave, r, c) if cave.is_castle else self.paint_rock(cave, r, c, rng, color=rock))
            self.add_handholds(image, rng)
        elif letter == "-":                         # drawn in draw_cave, so it can shake before it falls
            self.crumbly_looks[(r, c)] = rng.choice(self.cave_crumblies)
        if image:
            self.cave_tiles[(r, c)] = image
        else:
            self.cave_tiles.pop((r, c), None)
        self.decorate(cave, r, c, rng)

    def decorate(self, cave, r, c, rng):
        """Little things in the open air: plants, crystals, vines, icicles, or cobwebs in the castle.
        (Stone caves have none.)"""
        self.cave_decor.pop((r, c), None)
        if cave.is_castle:
            self.decorate_castle(cave, r, c, rng)
        elif cave.map[r][c] == "." and cave.theme in CAVE_COLORS:
            self.decorate_chunky(cave, r, c, rng)

    def paint_rock(self, cave, r, c, rng, color=(82, 74, 90), cracks=False, ore=False):
        """One block of rock in a stone cave. (Moss, crystal and lava caves paint theirs in chunky pixels.)"""
        if cave.theme in CAVE_COLORS:
            return self.paint_chunky_rock(cave, r, c, rng, cracks, ore)
        surf = pygame.Surface((TILE, TILE))
        surf.fill(color)
        light = tuple(min(255, v + 14) for v in color)
        dark = tuple(max(0, v - 14) for v in color)
        for _ in range(7):
            x, y = rng.randint(0, 52), rng.randint(0, 52)
            pygame.draw.ellipse(surf, rng.choice([dark, light]), (x, y, rng.randint(8, 16), rng.randint(6, 12)))
        if cracks:                                  # cracked rock: you can dig through it
            for start, points in (((32, 4), [(26, 18), (36, 30), (28, 44), (34, 60)]),
                                  ((6, 34), [(18, 30), (28, 38)]), ((58, 22), [(46, 28), (38, 26)])):
                pygame.draw.lines(surf, (40, 32, 40), False, [start] + points, 3)
        if ore:                                     # diamond ore (or a golden Sun Shard): dig it out!
            gem = ORE_SHARD if ore == "shard" else ORE_DIAMOND
            for x, y in ((14, 16), (40, 12), (26, 36), (46, 42), (12, 46)):
                pygame.draw.polygon(surf, gem, [(x, y - 6), (x + 6, y), (x, y + 6), (x - 6, y)])
                surf.fill((255, 255, 235), (x - 2, y - 3, 2, 2))
        def open_at(rr, cc):
            return cave.tile(rr, cc) not in LOOKS_SOLID
        above = cave.tile(r - 1, c)
        if above == "~":                            # a lava pool on top: the rock under it glows hot
            surf.fill((150, 52, 30), (0, 0, TILE, 8))
            surf.fill((214, 96, 38), (0, 0, TILE, 3))
        elif open_at(r - 1, c):                     # the top of a block you can stand on
            self.paint_rock_top(surf, color, rng, burnt=above == "!")
        if open_at(r + 1, c):
            surf.fill(tuple(max(0, v - 26) for v in color), (0, TILE - 5, TILE, 5))
        lava_top = int(TILE * caves.HAZARD_TOP["~"])
        for side, x in ((c - 1, 0), (c + 1, TILE - 4)):
            if open_at(r, side):                    # a shadow on the side of a block
                surf.fill(tuple(max(0, v - 20) for v in color), (x, 0, 4, TILE))
            if cave.tile(r, side) == "~":           # the side of a lava pool glows, down where the lava is
                glow = 0 if cave.tile(r - 1, side) == "~" else lava_top    # deep lava: all the way up
                surf.fill((168, 70, 36), (x, glow, 4, TILE - glow))
        if not ore and rng.random() < 0.08:         # a tiny crystal
            surf.fill(rng.choice(self.theme["specks"]), (rng.randint(8, 52), rng.randint(12, 52), 3, 3))
        return surf

    def paint_rock_top(self, surf, color, rng, burnt=False):
        """The top of a block you can stand on, in a stone cave: plain stone, sometimes with pebbles or a crack."""
        look = rng.randrange(CAVE_LOOKS)
        if burnt:                                   # a fire burns on top: black soot and glowing embers
            surf.fill((34, 24, 24), (0, 0, TILE, 7))
            surf.fill((62, 42, 38), (0, 7, TILE, 3))
            for x in (12, 30, 47):
                surf.fill((255, 130, 40), (x + rng.randint(-3, 3), 2, 3, 2))
            return
        surf.fill(tuple(min(255, v + 50) for v in color), (0, 0, TILE, 6))
        surf.fill(tuple(min(255, v + 26) for v in color), (0, 6, TILE, 3))
        if look == 1:
            for _ in range(3):
                pygame.draw.ellipse(surf, tuple(min(255, v + 70) for v in color), (rng.randint(4, 54), rng.randint(0, 2), 6, 4))
        elif look == 2:
            x = rng.randint(10, 50)
            pygame.draw.lines(surf, tuple(max(0, v - 30) for v in color), False, [(x, 0), (x + 3, 6), (x - 1, 12)], 2)

    # ----- drawing: caves in chunky pixels ---------------------------------------------
    # The moss, crystal and lava caves are painted in chunky pixels: dot() paints one, and chunky() makes
    # a tiny picture bigger. Their colors are in CAVE_COLORS at the top of this file.
    # Everything is painted once, when you go in, except the lava and the drops of water, which move.

    def paint_rock_picture(self, theme):
        """The rock of a cave is one big picture, ROCK_PICTURE blocks across and down, that repeats.
        Every block cuts its own piece out of it, so the rock flows from block to block with no lines in between."""
        look = CAVE_COLORS[theme]
        size = ROCK_PICTURE * TILE // ART_PIXEL        # how many chunky pixels across (and down)
        small = pygame.Surface((size, size))
        rng = random.Random(theme)                      # the same look is always painted the same way
        if "cobbles" in look:
            self.paint_cobbles(small, look, rng)
            return chunky(small)
        small.fill(look["stone"])
        # Everything stays inside the picture, so its edges still match up when it repeats.
        for _ in range(size // 2):                      # lighter and darker patches in the stone
            w, h = rng.randint(4, 12), rng.randint(3, 7)
            pygame.draw.ellipse(small, rng.choice([look["dark"], look["light"]]),
                                (rng.randint(0, size - w), rng.randint(0, size - h), w, h))
        for _ in range(size // 6):                      # cracks running down the stone
            x, y = rng.randint(4, size - 5), rng.randint(0, size - 14)
            points = [(x, y)]
            for _ in range(rng.randint(2, 4)):
                x, y = min(size - 1, max(0, x + rng.randint(-2, 2))), y + rng.randint(2, 3)
                points.append((x, y))
            pygame.draw.lines(small, look["crack"], False, points)
        for _ in range(size // 16):                     # streaks, where water runs down the rock (or froze)
            small.fill(look["streak"], (rng.randint(1, size - 2), rng.randint(0, size - 16), 1, rng.randint(5, 14)))
        for _ in range(size // 8):                      # patches of moss (or frost) on the rock
            x, y = rng.randint(0, size - 16), rng.randint(0, size - 12)
            for _ in range(rng.randint(2, 4)):
                w, h = rng.randint(4, 9), rng.randint(3, 6)
                pygame.draw.ellipse(small, look["patch"], (x + rng.randint(0, 6), y + rng.randint(0, 5), w, h))
        light_on_top(small, look["patch"], look["patch_light"])
        for _ in range(size // 5):                      # little specks that glow
            x, y = rng.randint(1, size - 2), rng.randint(1, size - 2)
            if rng.random() < 0.5:
                small.fill(look["glow_dim"], (x - 1, y, 3, 1))
                small.fill(look["glow_dim"], (x, y - 1, 1, 3))
            small.fill(look["glow"], (x, y, 1, 1))
        return chunky(small)

    def paint_cobbles(self, small, look, rng):
        """Rock made of round stones packed together, with dark gaps between them. Here and there the gaps glow hot."""
        size = small.get_width()
        small.fill(look["crack"])                       # the gaps between the stones
        for top in range(0, size, 6):                   # rows of stones
            x = -rng.randint(0, 6)
            while x < size:
                w, h = rng.randint(6, 10), rng.randint(5, 7)
                color = rng.choice(look["cobbles"])
                y = top + rng.randint(-1, 1)
                for dx in (-size, 0, size):             # past each edge too, so the pattern joins up
                    for dy in (-size, 0, size):
                        pygame.draw.ellipse(small, color, (x + dx, y + dy, w, h))
                x += w - 1
        for color in look["cobbles"]:                   # the light shines on the top of every stone
            light_on_top(small, color, tuple(min(255, v + 22) for v in color))
        gaps = pygame.mask.from_threshold(small, look["crack"], (1, 1, 1, 255))
        dim, bright = look["hot_cracks"]
        for _ in range(size // 14):                     # a few hot spots, where the gaps glow
            spot = pygame.Surface((size, size), pygame.SRCALPHA)
            x, y, radius = rng.randrange(size), rng.randrange(size), rng.randint(5, 10)
            for dx in (-size, 0, size):
                for dy in (-size, 0, size):
                    pygame.draw.circle(spot, (255, 255, 255), (x + dx, y + dy), radius)
            hot = gaps.overlap_mask(pygame.mask.from_surface(spot), (0, 0))
            hot.to_surface(small, setcolor=dim, unsetcolor=None)
            for _ in range(4):                          # the hottest bits, bright orange
                bx, by = (x + rng.randint(-3, 3)) % size, (y + rng.randint(-3, 3)) % size
                if gaps.get_at((bx, by)):
                    small.fill(bright, (bx, by, 1, 1))

    def paint_chunky_rock(self, cave, r, c, rng, cracks=False, ore=False):
        """One block of rock in chunky pixels: its piece of the big rock picture, then its edges."""
        look = CAVE_COLORS[cave.theme]
        surf = pygame.Surface((TILE, TILE))
        piece = ((c % ROCK_PICTURE) * TILE, (r % ROCK_PICTURE) * TILE, TILE, TILE)
        surf.blit(self.rock_picture, (0, 0), piece)
        if cracks:                                  # cracked rock is lighter, with big cracks: dig through it!
            surf.fill((30, 30, 30), special_flags=pygame.BLEND_RGB_ADD)
            small = pygame.Surface((16, 16), pygame.SRCALPHA)
            shine = tuple(min(255, v + 70) for v in look["stone"])
            for crack in ([(8, 0), (6, 4), (9, 8), (7, 12), (8, 15)], [(0, 9), (3, 8), (6, 10)], [(15, 5), (12, 7), (8, 6)]):
                pygame.draw.lines(small, shine, False, [(x + 1, y) for x, y in crack])   # a light edge along each crack
                pygame.draw.lines(small, look["edge"], False, crack)
            surf.blit(chunky(small), (0, 0))
        if ore:                                     # diamond ore (or a golden Sun Shard): dig it out!
            gem = ORE_SHARD if ore == "shard" else ORE_DIAMOND
            for x, y in ((3, 4), (10, 3), (6, 9), (12, 10), (3, 12)):
                for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                    dot(surf, gem, x + dx, y + dy)
                dot(surf, (255, 255, 235), x, y)

        def open_at(rr, cc):
            return cave.tile(rr, cc) not in LOOKS_SOLID
        if open_at(r + 1, c):                       # the underside of a roof: a dark edge
            dot(surf, look["edge"], 0, 15, 16, 1)
        lava_top = int(TILE * caves.HAZARD_TOP["~"])
        for side, x in ((c - 1, 0), (c + 1, 15)):
            if open_at(r, side):                    # a dark edge on an open side
                dot(surf, look["edge"], x, 0, 1, 16)
            if cave.tile(r, side) == "~":           # the side of a lava pool glows, down where the lava is
                glow = 0 if cave.tile(r - 1, side) == "~" else lava_top    # deep lava: all the way up
                surf.fill((168, 70, 36), (x * ART_PIXEL, glow, ART_PIXEL, TILE - glow))
        above = cave.tile(r - 1, c)
        if above == "~":                            # a lava pool on top: the rock under it glows hot
            surf.fill((150, 52, 30), (0, 0, TILE, 8))
            surf.fill((214, 96, 38), (0, 0, TILE, 4))
        elif open_at(r - 1, c):                     # the top of a block you can stand on
            self.paint_chunky_top(surf, cave, r, c, rng, burnt=above == "!")
        return surf

    def paint_chunky_top(self, surf, cave, r, c, rng, burnt=False):
        """The top of a block you can stand on: thick moss (or snow, or red moss), hanging over the edge."""
        look = CAVE_COLORS[cave.theme]
        if burnt:                                   # a fire burns on top: black soot and glowing embers
            dot(surf, (34, 24, 24), 0, 0, 16, 2)
            dot(surf, (62, 42, 38), 0, 2, 16, 1)
            for x in (3, 7, 12):
                dot(surf, (255, 130, 40), x + rng.randint(-1, 1), 0)
            return
        light, middle, dark = look["top"]
        drip, tip = look.get("icicles", (middle, dark))    # snow has little icicles hanging from it
        open_left, open_right = cave.tile(r, c - 1) not in LOOKS_SOLID, cave.tile(r, c + 1) not in LOOKS_SOLID
        for x in range(16):
            thick = rng.choice((2, 2, 3))
            length = rng.randint(1, 4) if rng.random() < 0.3 else 0
            if (x == 0 and open_left) or (x == 15 and open_right):
                length = rng.randint(3, 6)          # hanging over the side
            dot(surf, middle, x, 0, 1, thick)
            dot(surf, light, x, 0)
            dot(surf, dark, x, thick)               # the shadow underneath
            if length:
                dot(surf, drip, x, thick, 1, length)
                dot(surf, tip, x, thick + length)
        for _ in range(3):
            dot(surf, light, rng.randrange(16), 1)  # bright bits
        if look["puddle"] and rng.random() < 0.12:  # a glowing (or frozen) puddle
            water, shine = look["puddle"]
            x = rng.randint(1, 9)
            dot(surf, water, x, 0, 6, 1)
            dot(surf, water, x + 1, 1, 4, 1)
            dot(surf, shine, x + 1, 0, 2, 1)

    def paint_chunky_ledge(self, wood, cracks, theme, look):
        """A wooden ledge in chunky pixels, with moss (or snow, or red moss) on top and hanging down underneath.
        A crumbly ledge is lighter and cracked, with less on top, so you can tell them apart."""
        rng = random.Random(look * 31 + cracks)     # the same look is always painted the same way
        colors = CAVE_COLORS[theme]
        surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        if theme == "lava":                         # charred black wood
            wood = tuple(int(v * 0.55) for v in wood)
        light, dark = tuple(min(255, v + 30) for v in wood), tuple(max(0, v - 50) for v in wood)
        dot(surf, wood, 0, 0, 16, 3)                # the plank, 3 chunky pixels thick
        dot(surf, light, 0, 0, 16, 1)
        dot(surf, dark, 0, 3, 16, 1)                # and its shadow
        for x in ((5, 11), (3, 10), (7, 13))[look % 3]:
            dot(surf, dark, x, 1, 1, 2)             # the gaps between the planks
        if theme == "lava":                         # embers still glowing in the wood
            for _ in range(2 + look):
                dot(surf, (255, 130, 40), rng.randrange(16), rng.randint(1, 2))
        if cracks:                                  # crumbly: it breaks if you stand on it!
            crack = (255, 120, 40) if theme == "lava" else dark
            for x, y in ((2, 0), (3, 1), (2, 2), (9, 1), (8, 2), (13, 0), (14, 1), (13, 2)):
                dot(surf, crack, x, y)
            surf.fill((0, 0, 0, 0), (7 * ART_PIXEL, 3 * ART_PIXEL, 3 * ART_PIXEL, ART_PIXEL))   # a bit broken off
        else:
            for x in ((1, 14), (2, 12), (1, 8))[look % 3]:
                dot(surf, (70, 54, 40), x, 2)       # nails
        top, middle, tip = colors["top"]
        drip, drip_tip = colors.get("icicles", (middle, tip))
        for x in range(16):
            if cracks and rng.random() < 0.65:      # crumbly ledges only have a little on top
                continue
            dot(surf, top, x, 0)
            if rng.random() < 0.35:                 # hanging down under the ledge
                length = rng.randint(1, 3 + look)
                dot(surf, drip, x, 4, 1, length)
                dot(surf, drip_tip, x, 4 + length)
        if look == 2 and not cracks and theme == "moss":      # a fern hanging under it
            surf.blit(self.cave_sprite(sprites.HANGING_FERN, scale=ART_PIXEL), (2 * ART_PIXEL, 4 * ART_PIXEL))
        return surf

    def paint_cave_back(self, cave, rng):
        """The back wall, far behind you: rocky teeth hanging down from the roof and growing up from the floor,
        in three rows: far away (light), in between, and close up (dark).
        It moves at half speed, so it only has to be a bit more than half as tall as the cave.
        Across, the pattern repeats, so it never ends."""
        look = CAVE_COLORS[cave.theme]
        width = 128                                 # chunky pixels across (8 blocks)
        height = (cave.rows * TILE // 2 + VIEW_H // 2) // ART_PIXEL + 1
        small = pygame.Surface((width, height))
        small.fill(look["far"])
        for i in range(3):                          # tall rock pillars, far away
            x, thin = (i + rng.uniform(0.2, 0.8)) * width / 3, rng.randint(3, 6)
            pillar = [(x - thin * 2.5, 0), (x - thin, height * 0.4), (x - thin, height * 0.6), (x - thin * 2.5, height),
                      (x + thin * 2.5, height), (x + thin, height * 0.6), (x + thin, height * 0.4), (x + thin * 2.5, 0)]
            for dx in (-width, 0, width):           # past each edge too, so the pattern joins up
                pygame.draw.polygon(small, look["far_rock"], [(px + dx, py) for px, py in pillar])
        narrow, wide = look["teeth"]
        for color, longest, crowd in ((look["far_rock"], 0.36, 2.2), (look["middle"], 0.26, 1.7), (look["near"], 0.15, 1.2)):
            longest = int(height * longest)
            teeth = int(width / (narrow + wide) * crowd)     # thin teeth: more of them
            for i in range(teeth):
                x = (i + rng.uniform(0, 0.8)) * width / teeth
                for length, hanging in ((rng.randint(longest // 2, longest), True), (rng.randint(longest // 3, longest), False)):
                    w = rng.randint(narrow, wide)
                    tooth = [(x - w / 2, 0), (x + w / 2, 0), (x + w / 5, length * 0.55),
                             (x + rng.uniform(-1, 1), length), (x - w / 5, length * 0.6)]
                    for dx in (-width, 0, width):
                        if hanging:                  # a stalactite (or icicle), hanging from the roof
                            pygame.draw.polygon(small, color, [(px + dx, py) for px, py in tooth])
                        else:                        # a stalagmite, growing up from the floor
                            pygame.draw.polygon(small, color, [(px + dx, height - py) for px, py in tooth])
            if color == look["middle"] and look["far_hanging"]:     # vines or roots hanging far away
                thick = 2 if look["far_hanging"] == "roots" else 1
                for _ in range(8):
                    x, length = rng.randint(1, width - 4), rng.randint(10, longest + 10)
                    for y in range(length):
                        small.fill(color, (x + (y // 6) % 2, y, thick if y < length // 2 else 1, 1))
        speck = tuple((a + b) // 2 for a, b in zip(look["far"], look["glow_dim"]))
        for _ in range(height // 4):                # faint glowing specks far away
            small.fill(speck, (rng.randrange(width), rng.randrange(height), 1, 1))
        return chunky(small)

    def paint_stone_back(self, rng):
        """The back wall of a stone cave, in chunky pixels: layers of rock in a few dark shades, with cracks,
        pebbles, patches of old bricks and cobbles, old wooden mine props, roots, and here and there a fossil.
        It's painted once when you go in (the pattern repeats across and down), so it costs nothing to draw."""
        look = STONE_BACK
        width, height = 288, 176                    # chunky pixels (18 x 11 blocks), then it repeats
        small = pygame.Surface((width, height))
        small.fill(look["layers"][0])

        def px(color, x, y, w=1, h=1):              # paint a few chunky pixels, wrapping round the edges
            for dx in (0, -width):                  # (past the right or bottom edge: it shows up on the other side)
                for dy in (0, -height):
                    small.fill(color, (x % width + dx, y % height + dy, w, h))

        # Layers of rock, one on top of another, each with a wavy top edge (and a dark seam along it)
        layers, y = [], 0
        while y < height - 6:
            wave, bumps, phase = rng.uniform(0.8, 2.2), rng.choice((1, 2, 3)), rng.uniform(0, 6.3)
            tops = [y + round(wave * math.sin(phase + x * bumps * 2 * math.pi / width)) for x in range(width)]
            layers.append((tops, rng.choice(look["layers"])))
            y += rng.randint(8, 16)
        for i, (tops, color) in enumerate(layers):
            below = layers[i + 1][0] if i + 1 < len(layers) else [t + height for t in layers[0][0]]
            for x in range(width):
                px(color, x, tops[x], 1, max(1, below[x] - tops[x]))
        for tops, color in layers:
            for x in range(width):
                if rng.random() < 0.75:
                    px(look["seam"], x, tops[x])
        # Patches of old bricks and cobbles, as if miners built a wall here long ago
        for kind in ("bricks", "cobbles", "bricks", "cobbles", "bricks"):
            left, top = rng.randrange(width), rng.randrange(height)
            w, h = rng.randint(22, 40), rng.randint(12, 22)
            for yy in range(h):
                ragged = rng.randint(0, 3)          # the edges are broken, not straight
                for xx in range(ragged, w - rng.randint(0, 3)):
                    px(look["mortar"], left + xx, top + yy)
            if kind == "bricks":
                for row in range(0, h - 1, 3):
                    shift = 3 if (row // 3) % 2 else 0
                    for col in range(shift - 6, w, 6):
                        bw = 5 if col >= 0 else 5 + col
                        if bw > 0 and col + bw <= w - 2:
                            shade = rng.choice(look["bricks"])
                            px(shade, left + max(0, col) + 1, top + row + 1, bw - 1, 2)
                            px(look["shine"], left + max(0, col) + 1, top + row + 1, bw - 1, 1)
            else:
                for _ in range(w * h // 9):
                    cx, cy, size = rng.randint(1, w - 4), rng.randint(1, h - 4), rng.randint(2, 3)
                    px(rng.choice(look["bricks"]), left + cx, top + cy, size, size)
                    px(look["shine"], left + cx, top + cy, size - 1, 1)
        # Cracks: zig-zagging down a few pixels, sometimes splitting in two
        for _ in range(26):
            x, y = rng.randrange(width), rng.randrange(height)
            for _ in range(rng.randint(4, 14)):
                px(look["crack"], x, y)
                if rng.random() < 0.15:
                    px(look["crack"], x + rng.choice((-1, 1)), y + 1)
                x += rng.choice((-1, 0, 0, 1))
                y += 1
        # An old wooden prop that holds the roof up: two posts and a beam
        dark, wood, light = look["wood"]
        for left in (rng.randrange(0, width // 2 - 20), rng.randrange(width // 2, width - 20)):
            top, wide, tall = rng.randrange(height), rng.randint(12, 18), rng.randint(14, 22)
            px(dark, left, top, wide, 3)
            px(wood, left, top, wide, 2)
            px(light, left, top, wide, 1)
            for post in (1, wide - 3):
                px(dark, left + post, top + 3, 2, tall)
                px(wood, left + post, top + 3, 1, tall)
        for _ in range(4):                          # roots poking through from the ground far above
            x, y = rng.randrange(width), rng.randrange(height)
            for _ in range(rng.randint(6, 16)):
                px(look["roots"], x, y)
                if rng.random() < 0.12:
                    px(look["roots"], x + rng.choice((-1, 1)), y + 1)
                x += rng.choice((-1, 0, 0, 0, 1))
                y += 1
        # Pebbles, little crystal specks, and a fossil or two
        for _ in range(150):
            x, y = rng.randrange(width), rng.randrange(height)
            px(rng.choice(look["pebbles"]), x, y, rng.randint(1, 2), 1)
        for _ in range(18):
            px(rng.choice(look["specks"]), rng.randrange(width), rng.randrange(height))
        for _ in range(4):
            fossil = rng.choice(FOSSILS)
            x, y = rng.randrange(width), rng.randrange(height)
            for dy, line in enumerate(fossil):
                for dx, letter in enumerate(line):
                    if letter == "o":
                        px(look["fossil"], x + dx, y + dy)
        return chunky(small)

    def decorate_chunky(self, cave, r, c, rng):
        """Things in the open air: plants, mushrooms, crystals or ember flowers on the floor,
        and vines, roots, moss or icicles hanging from the roof."""
        look = CAVE_COLORS[cave.theme]
        below = cave.tile(r + 1, c)
        floor, roof = below == "#", cave.tile(r - 1, c) == "#"
        tall = roof and below == "."                # open air below too: things can hang down further
        danger_next_door = any(cave.tile(r, c + side) in caves.HAZARDS for side in (-1, 1))
        art = pygame.Surface((TILE, TILE * 2 if tall else TILE), pygame.SRCALPHA)
        if danger_next_door:                        # nothing grows right next to spikes, lava or fire,
            pass                                    # so they're easy to see
        elif floor and rng.random() < (MOSS_GRASS if cave.theme == "moss" else FLOOR_THINGS):
            self.grow_on_floor(art, look, rng)
        elif below in caves.LEDGES and "grass" in look["on_floor"] and rng.random() < LEDGE_GRASS:
            self.grow_tuft(art, look, rng, rng.randint(1, 11))
        if roof and rng.random() < HANGING:
            self.hang_from_roof(art, look, rng, tall)
        if art.get_bounding_rect().w:
            self.cave_decor[(r, c)] = art

    def grow_on_floor(self, art, look, rng):
        """Something on the floor. Which kinds a cave has is in its "on_floor" list in CAVE_COLORS."""
        kind = rng.choice(look["on_floor"])
        flip = rng.random() < 0.5
        x = rng.randint(0, 5) * ART_PIXEL           # where it goes (pictures are about 11 chunky pixels wide)
        if kind == "grass":
            self.grow_tuft(art, look, rng, rng.randint(1, 11))
        elif kind == "fern":
            art.blit(self.cave_sprite(sprites.FERN, flip=flip, scale=ART_PIXEL), (x, 8 * ART_PIXEL))
        elif kind == "mushrooms":                   # glowing mushrooms: blue, green or teal
            picture, color = rng.choice([(sprites.GLOW_MUSHROOMS, sprites.COLORS["q"]),
                                         (sprites.GREEN_MUSHROOMS, sprites.COLORS["j"]),
                                         (sprites.TEAL_MUSHROOMS, sprites.COLORS["t"])])
            self.glowing(art, picture, color, x, 8, flip)
        elif kind == "crystals":                    # glowing crystals: blue or teal
            picture, color = rng.choice([(sprites.BLUE_CRYSTALS, sprites.COLORS["q"]),
                                         (sprites.TEAL_CRYSTALS, sprites.COLORS["t"])])
            self.glowing(art, picture, color, x, 7, flip)
        elif kind == "ember flowers":
            self.glowing(art, sprites.EMBER_FLOWERS, (255, 150, 60), x, 8, flip)
        elif kind == "snow":                        # a lump of snow
            left, w = rng.randint(1, 9), rng.randint(4, 6)
            white, pale, shadow = look["top"]
            dot(art, pale, left, 14, w, 2)
            dot(art, white, left + 1, 13, w - 2, 2)
            dot(art, shadow, left, 15, w, 1)
        elif kind == "sparkle":                     # a little sparkle in the air
            sx, sy = rng.randint(3, 12), rng.randint(5, 11)
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                dot(art, look["glow"], sx + dx, sy + dy)
            dot(art, (255, 255, 255), sx, sy)
        elif kind == "pebbles":                     # dark pebbles, one of them still glowing
            for i in range(rng.randint(2, 4)):
                dot(art, rng.choice(look["cobbles"]), 2 + i * 3 + rng.randint(0, 1), 15, 2, 1)
            dot(art, look["hot_cracks"][1], rng.randint(3, 12), 15)
        elif kind == "sprout":                      # a little sprout, with glowing spores floating over it
            sx = rng.randint(3, 12)
            green, dark, new = look["plants"]
            dot(art, dark, sx, 13, 1, 3)
            dot(art, green, sx - 1, 13)
            dot(art, green, sx + 1, 12)
            dot(art, new, sx - 2, 12)
            dot(art, new, sx + 2, 11)
            for _ in range(3):
                dot(art, look["glow"], sx + rng.randint(-3, 3), rng.randint(5, 10))

    def glowing(self, art, picture, color, x, y, flip=False):
        """A letter picture from sprites.py with a soft glow behind it. x is in screen pixels, y in chunky pixels."""
        image = self.cave_sprite(picture, flip=flip, scale=ART_PIXEL)
        glow = self.soft_glow(color)
        art.blit(glow, glow.get_rect(center=(x + image.get_width() // 2, y * ART_PIXEL + image.get_height() // 2)))
        art.blit(image, (x, y * ART_PIXEL))

    def grow_tuft(self, art, look, rng, x):
        """A tuft of grass: a few blades, all different heights."""
        for i in range(rng.randint(3, 5)):
            height = rng.randint(2, 5)
            dot(art, rng.choice(look["plants"]), x + i, 16 - height, 1, height)

    def hang_from_roof(self, art, look, rng, tall):
        """Something hanging from the roof. Which kinds a cave has is in its "on_roof" list in CAVE_COLORS."""
        longest = 24 if tall else 14                # in chunky pixels (a block is 16)
        kind = rng.choice(look["on_roof"])
        if kind == "vine":                          # a thin vine with leaves on both sides
            stem, leaf, new_leaf = look["vine"]
            x, length = rng.randint(2, 13), rng.randint(6, longest)
            for y in range(length):
                if y and y % 4 == 0:
                    x = max(1, min(14, x + rng.choice((-1, 0, 1))))
                dot(art, stem, x, y)
                if y % 3 == 1:
                    side = 1 if y % 6 == 1 else -1
                    dot(art, leaf, x + side, y)
                    if rng.random() < 0.5:
                        dot(art, new_leaf, x + side, y - 1)
            dot(art, leaf, x - 1, length, 3, 1)     # a bunch of leaves at the end
            dot(art, new_leaf, x, length + 1)
        elif kind == "moss":                        # a curtain of moss
            light, middle, dark = look["top"]
            left = rng.randint(0, 6)
            for x in range(left, left + rng.randint(6, 10)):
                length = rng.randint(1, 3) + (rng.randint(0, 6) if rng.random() < 0.5 else 0)
                dot(art, middle, x, 0, 1, length)
                dot(art, dark, x, length)
                if rng.random() < 0.3:
                    dot(art, light, x, rng.randrange(length))
        elif kind == "roots":                       # tree roots growing down through the roof
            dark, light = look["root"]
            for x in (rng.randint(2, 5), rng.randint(9, 12)):      # two roots side by side
                length = rng.randint(6, longest // 2 + 5)
                for y in range(length):
                    if y % 3 == 2:
                        x = max(1, min(13, x + rng.choice((-1, 0, 1))))
                    dot(art, dark, x, y)
                    if y < length // 2:             # thick at the top, thin at the tip
                        dot(art, light, x + 1, y)
                    if y == length // 2:            # a thin root branching off
                        side = rng.choice((-1, 1))
                        for i in range(1, rng.randint(3, 5)):
                            dot(art, dark, x + side * i, y + i // 2)
                dot(art, look["vine"][1], x - 1, length - 1)   # a tiny leaf at the tip
        elif kind == "fern":                        # a fern hanging down
            art.blit(self.cave_sprite(sprites.HANGING_FERN, flip=rng.random() < 0.5, scale=ART_PIXEL),
                     (rng.randint(0, 4) * ART_PIXEL, 0))
        elif kind == "icicles":                     # a few icicles: wide at the top, pointy at the bottom
            ice, shadow = look["icicles"]
            white = look["top"][0]
            for _ in range(rng.randint(2, 4)):
                x, length = rng.randint(1, 13), rng.randint(3, longest // 2 + 2)
                for y in range(length):
                    if y < length // 2:             # the top half is 2 chunky pixels wide, with a shine
                        dot(art, ice, x, y, 2, 1)
                        dot(art, white, x, y)
                    else:
                        dot(art, ice if y < length - 1 else shadow, x + 1 if length % 2 else x, y)
        elif kind == "crystals":                    # glowing crystals growing down from the roof
            picture, color = rng.choice([(sprites.BLUE_CRYSTALS, sprites.COLORS["q"]),
                                         (sprites.TEAL_CRYSTALS, sprites.COLORS["t"])])
            image = pygame.transform.flip(self.cave_sprite(picture, scale=ART_PIXEL), rng.random() < 0.5, True)
            x = rng.randint(0, 5) * ART_PIXEL
            glow = self.soft_glow(color)
            art.blit(glow, glow.get_rect(center=(x + image.get_width() // 2, image.get_height() // 2)))
            art.blit(image, (x, 0))

    def soft_glow(self, color, radius=26, strength=70):
        """A soft glow around something shiny. Each one is made once and used again and again."""
        key = ("glow", color, radius, strength)
        if key not in self.cave_art:
            self.cave_art[key] = make_soft_glow(radius, color, strength)
        return self.cave_art[key]

    def find_drips(self, cave):
        """Spots on the roof where a drop of water drips down now and then (in caves that have "drip" in CAVE_COLORS)."""
        self.drips = []
        look = CAVE_COLORS.get(cave.theme, {})
        if "drip" not in look or cave.is_castle:
            return
        self.drip_color = look["drip"]
        rng = random.Random(cave.mine_pos[0] * 31 + cave.mine_pos[1])
        for r in range(1, cave.rows):
            for c in range(cave.cols):
                if cave.map[r][c] == "." and cave.tile(r - 1, c) == "#" and rng.random() < DRIPS:
                    floor = r                       # where the drop lands
                    while floor < cave.rows and cave.tile(floor, c) not in LOOKS_SOLID + caves.LEDGES:
                        floor += 1
                    if floor - r >= 2:              # only where it has a long way to fall
                        x = c * TILE + rng.randint(2, 13) * ART_PIXEL
                        self.drips.append((x, r * TILE, floor * TILE, rng.uniform(0, 4)))

    def draw_drips(self, surf):
        """Drops of water: each one grows on the roof, falls, and makes a tiny splash."""
        cam_x, cam_y = self.cam
        for x, top, bottom, start in self.drips:
            if not cam_x - 8 <= x <= cam_x + VIEW_W:
                continue
            t = (self.time + start) % 4.0           # a new drop every 4 seconds
            x -= cam_x
            if t < 1.0:                             # growing on the roof
                surf.fill(self.drip_color, (x, top - cam_y, ART_PIXEL, 1 + int(t * 5)))
                continue
            y = top + 900 * (t - 1.0) ** 2          # falling faster and faster
            if y < bottom - 8:
                surf.fill(self.drip_color, (x, y - cam_y, ART_PIXEL, 8))
            elif t - 1.0 < math.sqrt((bottom - top) / 900) + 0.2:     # just landed: splash!
                for dx in (-8, 8):
                    surf.fill(self.drip_color, (x + dx, bottom - cam_y - 8, ART_PIXEL, ART_PIXEL))

    def paint_lava_pictures(self):
        """The moving lava, painted ahead of time as LAVA_PICTURES pictures, like the pages of a flip book.
        Each one is 4 blocks wide, so the waves roll smoothly from one block to the next."""
        width = 4 * TILE // ART_PIXEL
        top = int(TILE * caves.HAZARD_TOP["~"]) // ART_PIXEL     # where the lava starts, in chunky pixels
        deep, middle, hot, white = DEEP_LAVA, (232, 84, 22), (255, 168, 48), (255, 236, 150)
        pictures = []
        for page in range(LAVA_PICTURES):
            turn = page / LAVA_PICTURES * 2 * math.pi
            small = pygame.Surface((width, 16), pygame.SRCALPHA)
            for x in range(width):
                # two waves added together, rolling along (each fits the picture a whole number of times)
                wave = math.sin(x / width * 2 * math.pi * 2 + turn) + 0.6 * math.sin(x / width * 2 * math.pi * 5 - turn * 2)
                y = top + 1 + round(wave)
                small.fill(middle, (x, y, 1, 16 - y))
                small.fill(deep, (x, 13, 1, 3))         # darker, deep down
                small.fill(hot, (x, y, 1, 2))           # the bright top of the lava
                if wave > 1.2:
                    small.fill(white, (x, y, 1, 1))     # the very hottest bits, on top of the waves
            for i in range(4):                          # bright blobs drifting along in the lava
                bx = (i * width // 4 + page * width // LAVA_PICTURES) % width
                small.fill(hot, (bx, 9 + (i * 3) % 4, 2, 1))
            pictures.append(chunky(small))
        return pictures

    def draw_chunky_lava(self, surf, x, y, c):
        """A lava pool in a moss, crystal or lava cave: one piece of the moving lava pictures, and now and then a splash."""
        look = CAVE_COLORS[self.game.cave.theme]
        top = y + int(TILE * caves.HAZARD_TOP["~"])
        surf.fill(look["edge"], (x, y, TILE, top - y))      # the far side of the pool: dark rock...
        surf.fill((120, 44, 26), (x, top - 2 * ART_PIXEL, TILE, 2 * ART_PIXEL))   # ...lit up red near the lava
        self.lava_lights.append((x + TILE // 2, top))       # its warm light is drawn after all the blocks
        page = self.lava_pictures[int(self.time * 8) % LAVA_PICTURES]
        surf.blit(page, (x, y), ((c % 4) * TILE, 0, TILE, TILE))
        self.lava_splash(surf, x, top, c)

    def lava_splash(self, surf, x, top, c):
        """Now and then, drops of lava jump up out of block c and fall back in."""
        t = (self.time * 0.45 + c * 0.37) % 1.0
        if t < 0.25:
            for i, side in enumerate((-1, 1, 0)):
                fly = t / 0.25
                dx = side * (6 + 10 * fly)
                dy = 28 * fly * (1 - fly) * (1.4 if side == 0 else 1)
                surf.fill((255, 200, 80), (x + 30 + dx, top - dy, ART_PIXEL, ART_PIXEL))

    def draw_chunky_rising_lava(self, surf, cave):
        """The rising lava in chunky pixels: the same moving lava pictures as the pools, all the way across,
        and deep red lava under them, down to the bottom of the screen."""
        cam_x, cam_y = self.cam
        lava_top = int(TILE * caves.HAZARD_TOP["~"])         # how far down a lava picture its lava starts
        y = (int(cave.lava_line * TILE) - lava_top) // ART_PIXEL * ART_PIXEL   # on the chunky pixel grid
        if cave.lava_wait > 0:                      # about to rise: it shakes up and down
            y += ART_PIXEL * round(math.sin(self.time * 18))
        y -= cam_y
        if y + lava_top >= VIEW_H:
            return
        surf.blit(self.pool_glow, self.pool_glow.get_rect(center=(VIEW_W // 2, y + lava_top)))
        page = self.lava_pictures[int(self.time * 8) % LAVA_PICTURES]
        width = page.get_width()                    # 4 blocks, lined up with the pools, so they match
        for x in range(-(cam_x % width), VIEW_W, width):
            surf.blit(page, (x, y))
        if y + TILE < VIEW_H:                       # deep lava below, with hot blobs drifting along slowly
            surf.fill(DEEP_LAVA, (0, y + TILE, VIEW_W, VIEW_H - y - TILE))
            for i in range(10):
                bx = (i * 131 + int(self.time * (6 + i % 3 * 4)) * ART_PIXEL - cam_x) % (VIEW_W + 64) - 32
                by = y + TILE + ART_PIXEL * (2 + (i * 7) % 11)
                surf.fill((214, 66, 24), (bx // ART_PIXEL * ART_PIXEL, by, 2 * ART_PIXEL, ART_PIXEL))
        first = cam_x // TILE
        for c in range(first, first + VIEW_W // TILE + 2):     # splashes, just like the pools
            self.lava_splash(surf, c * TILE - cam_x, y + lava_top, c)

    def paint_chunky_ice(self, cave, r, c, rng):
        """A block of slippery ice in chunky pixels: clear sky blue, with shiny streaks and a shiny top.
        Blocks of ice side by side join up into one long slab."""
        ice = ICE_COLORS
        surf = pygame.Surface((TILE, TILE))
        surf.fill(ice["ice"])
        dot(surf, ice["deep"], 0, 12, 16, 4)        # deeper down it's a darker blue...
        for x in range(0, 16, 2):
            dot(surf, ice["deep"], x + r % 2, 11)   # ...fading in, every other chunky pixel
        start = rng.randint(0, 6)
        for i in range(10):                         # a wide streak of shine, going up to the right
            dot(surf, ice["shine"], start + i, 13 - i)
            dot(surf, ice["light"], start + i + 1, 13 - i)
        for i in range(5):                          # and a thin one next to it
            dot(surf, ice["light"], start + 5 + i, 12 - i)
        for _ in range(2):                          # little bubbles frozen inside
            dot(surf, ice["light"], rng.randint(1, 14), rng.randint(8, 14))
        if cave.tile(r - 1, c) not in LOOKS_SOLID:     # the top: smooth and shiny. Slippery!
            dot(surf, ice["shine"], 0, 0, 16, 1)
            dot(surf, ice["light"], 0, 1, 16, 1)
            spark = rng.randint(2, 12)
            dot(surf, ice["shine"], spark, 2)       # a glint, just under the top
        elif cave.tile(r - 1, c) != "I":
            dot(surf, ice["edge"], 0, 0, 16, 1)
        for side, x in ((c - 1, 0), (c + 1, 15)):   # a dark edge, except next to more ice
            if cave.tile(r, side) != "I":
                dot(surf, ice["edge"], x, 0, 1, 16)
        if cave.tile(r + 1, c) != "I":
            dot(surf, ice["edge"], 0, 15, 16, 1)
        return surf

    def paint_spring_pictures(self, theme):
        """A healing spring in chunky pixels: a little bowl of the cave's own rock with glowing water in it.
        It's painted ahead of time with the water at every height (0 = empty, SPRING_FULL = full),
        because after you drink it fills up again slowly."""
        look = CAVE_COLORS[theme]
        bowl = {"r": tuple(min(255, v + 56) for v in look["stone"]),     # lighter than the rock, so you see it
                "s": tuple(min(255, v + 30) for v in look["stone"]), "d": look["edge"]}
        rim = 16 - len(SPRING_BOWL)                 # the top of the bowl, in chunky pixels
        bottom = rim + SPRING_FULL                  # the lowest row of water
        water = SPRING_WATER
        pictures = []
        for level in range(SPRING_FULL + 1):
            small = pygame.Surface((16, 16), pygame.SRCALPHA)
            surface = bottom + 1 - level            # the top of the water
            for y, row in enumerate(SPRING_BOWL, start=rim):
                left, right = len(row) - len(row.lstrip(".")), len(row.rstrip(".")) - 1    # the bowl's two sides
                for x, letter in enumerate(row):
                    if letter != ".":
                        small.fill(bowl[letter], (x, y, 1, 1))
                    elif left < x < right and surface <= y <= bottom:    # the water: light on top, deep blue below
                        color = water["light"] if y == surface else water["water"] if y < bottom else water["deep"]
                        small.fill(color, (x, y, 1, 1))
            light, middle, _ = look["top"]          # moss (or snow, or red moss) on the rim
            small.fill(middle, (0, rim - 1, 2, 1))
            small.fill(middle, (14, rim - 1, 2, 1))
            small.fill(light, (0, rim - 1, 1, 1))
            small.fill(light, (15, rim - 1, 1, 1))
            if level:
                small.fill(water["shine"], (6, surface, 2, 1))     # the water shines
            pictures.append(chunky(small))
        return pictures

    def draw_spring(self, surf, x, y, full):
        """A healing spring in a moss, crystal or lava cave. full: 1 = ready, 0 = just drunk from.
        When it's full it glows, and bubbles float up out of it."""
        level = int(full * SPRING_FULL)
        rim = 16 - len(SPRING_BOWL)                 # in chunky pixels
        if level == SPRING_FULL:
            glow = self.soft_glow(SPRING_WATER["glow"], radius=56, strength=110)
            surf.blit(glow, glow.get_rect(center=(x + TILE // 2, y + (rim + 2) * ART_PIXEL)))
        surf.blit(self.springs[level], (x, y))
        if level < SPRING_FULL:
            return
        for i in range(4):                          # bubbles floating up, wiggling, and popping
            t = (self.time * 0.7 + i / 4) % 1.0
            if t < 0.85:
                bx = 3 + i * 3 + (1 if int(t * 6) % 2 else 0)
                by = rim - int(t * 11)
                color = SPRING_WATER["light"] if t < 0.6 else SPRING_WATER["water"]
                surf.fill(color, (x + bx * ART_PIXEL, y + by * ART_PIXEL, ART_PIXEL, ART_PIXEL))
        glint = 3 + int(self.time * 3) % 10         # a glint moving across the water
        surf.fill(SPRING_WATER["shine"], (x + glint * ART_PIXEL, y + (rim + 1) * ART_PIXEL, ART_PIXEL, ART_PIXEL))
        t = self.time % 2.0                         # and now and then a little twinkle of magic over it
        if t < 0.3:
            size = 1 if t < 0.1 or t > 0.2 else 2
            sx, sy = x + (5 if int(self.time / 2) % 2 else 10) * ART_PIXEL, y + (rim - 5) * ART_PIXEL
            surf.fill(SPRING_WATER["shine"], (sx - (size - 1) * ART_PIXEL, sy, (2 * size - 1) * ART_PIXEL, ART_PIXEL))
            surf.fill(SPRING_WATER["shine"], (sx, sy - (size - 1) * ART_PIXEL, ART_PIXEL, (2 * size - 1) * ART_PIXEL))

    def mote_dot(self, color, fade):
        """One floating speck. They're made once for each color and brightness, and used again and again."""
        key = (color, int(fade * 8))
        if key not in self.mote_dots:
            speck = pygame.Surface((4, 4), pygame.SRCALPHA)
            speck.fill(color + (int(220 * key[1] / 8),))
            self.mote_dots[key] = speck
        return self.mote_dots[key]

    # ----- the Shadow King's castle -------------------------------------------------

    def paint_castle_wall(self, wall):
        """The castle's back wall: rows of dark stone bricks (the pattern repeats every 256 pixels)."""
        wall.fill((20, 17, 30))                         # the mortar between the bricks
        for row in range(16):
            for col in range(-1, 8):
                x = col * 32 + (16 if row % 2 else 0)
                shade = (col % 8 * 7 + row * 13) % 5 * 3     # bricks aren't all exactly the same color
                color = (32 + shade, 28 + shade, 46 + shade)
                wall.fill(color, (x + 1, row * 16 + 1, 30, 14))
                wall.fill(tuple(v + 7 for v in color), (x + 1, row * 16 + 1, 30, 2))

    def paint_bricks(self, cave, r, c, cracked=False):
        """One block of castle wall: 4 rows of stone bricks. Cracked bricks can be dug out."""
        def open_at(rr, cc):
            return cave.tile(rr, cc) not in LOOKS_SOLID
        base = self.theme["rock"]
        if not any(open_at(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            base = tuple(v - 14 for v in base)          # deep inside a thick wall: a little darker
        surf = pygame.Surface((TILE, TILE))
        surf.fill(tuple(v // 2 for v in base))          # mortar
        for i in range(4):
            row = r * 4 + i                             # which row of bricks this is in the whole castle
            shift = 16 if row % 2 else 0
            for j in range(-1, 2):
                x = j * 32 + shift
                col = (c * TILE + x) // 32              # ...and which brick in that row
                shade = (col * 7 + row * 13) % 5 * 4 - 8
                color = tuple(max(0, min(255, v + shade + (16 if cracked else 0))) for v in base)
                surf.fill(color, (x + 1, i * 16 + 1, 30, 14))
                surf.fill(tuple(min(255, v + 16) for v in color), (x + 1, i * 16 + 1, 30, 2))
                surf.fill(tuple(max(0, v - 16) for v in color), (x + 1, i * 16 + 13, 30, 2))
        if cracked:                                     # cracked bricks: dig through them!
            for start, points in (((30, 2), [(24, 18), (36, 32), (28, 46), (34, 62)]), ((4, 36), [(16, 30), (26, 38)])):
                pygame.draw.lines(surf, (30, 24, 34), False, [start] + points, 3)
        if open_at(r - 1, c):                           # the top of a wall you can stand on: smooth stone
            surf.fill(tuple(min(255, v + 44) for v in base), (0, 0, TILE, 6))
            surf.fill(tuple(min(255, v + 20) for v in base), (0, 6, TILE, 3))
        if open_at(r + 1, c):
            surf.fill(tuple(max(0, v - 30) for v in base), (0, TILE - 5, TILE, 5))
        if open_at(r, c - 1):
            surf.fill(tuple(max(0, v - 22) for v in base), (0, 0, 4, TILE))
        if open_at(r, c + 1):
            surf.fill(tuple(max(0, v - 22) for v in base), (TILE - 4, 0, 4, TILE))
        return surf

    def paint_stone_ledge(self):
        """A stone shelf sticking out of the castle wall."""
        surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        top, side, dark = (156, 150, 180), (118, 112, 142), (66, 60, 86)
        surf.fill(side, (0, 0, TILE, 14))
        surf.fill(top, (0, 0, TILE, 4))
        surf.fill(dark, (0, 14, TILE, 3))
        for x in (0, 32):                               # the seams between the stones
            surf.fill(dark, (x, 4, 2, 10))
        return surf

    def paint_window(self):
        """A tall castle window with the moon and stars outside."""
        w, h = 44, 92
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (110, 104, 136), (0, 0, w, h), border_top_left_radius=22, border_top_right_radius=22)
        glass = pygame.Surface((w - 12, h - 12), pygame.SRCALPHA)
        for y in range(h - 12):                         # the night sky, a little lighter near the bottom
            t = y / (h - 12)
            glass.fill((int(lerp(16, 50, t)), int(lerp(12, 28, t)), int(lerp(46, 96, t)), 255), (0, y, w - 12, 1))
        pygame.draw.circle(glass, (236, 232, 255), (21, 22), 11)       # the moon
        pygame.draw.circle(glass, (204, 198, 236), (18, 25), 3)
        pygame.draw.circle(glass, (214, 208, 244), (25, 18), 2)
        for sx, sy in ((5, 48), (24, 60), (11, 70), (26, 40), (8, 8)):
            glass.fill((255, 255, 255), (sx, sy, 2, 2))
        arch = pygame.Surface(glass.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(arch, (255, 255, 255, 255), arch.get_rect(), border_top_left_radius=16, border_top_right_radius=16)
        glass.blit(arch, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)  # round off the top corners
        surf.blit(glass, (6, 6))
        pygame.draw.line(surf, (40, 36, 54), (w // 2, 8), (w // 2, h - 6), 3)   # iron bars
        pygame.draw.line(surf, (40, 36, 54), (6, h // 2), (w - 6, h // 2), 3)
        surf.fill((136, 130, 162), (0, h - 6, w, 6))   # the window sill
        return surf

    def paint_banner(self):
        """A purple banner with the Shadow King's black crown on it."""
        surf = pygame.Surface((44, 104), pygame.SRCALPHA)
        gold, cloth, dark = (214, 172, 70), (112, 40, 152), (78, 24, 110)
        pygame.draw.polygon(surf, cloth, [(4, 4), (40, 4), (40, 102), (22, 88), (4, 102)])
        surf.fill(dark, (4, 4, 5, 92))
        surf.fill(dark, (35, 4, 5, 92))
        pygame.draw.lines(surf, gold, False, [(9, 78), (9, 88), (22, 78), (35, 88), (35, 78)], 2)
        crown = [(12, 52), (12, 38), (17, 45), (22, 34), (27, 45), (32, 38), (32, 52)]
        pygame.draw.polygon(surf, (24, 12, 34), crown)
        pygame.draw.polygon(surf, gold, crown, 1)
        surf.fill((210, 130, 255), (20, 44, 4, 4))     # a purple jewel
        surf.fill(gold, (0, 0, 44, 5))                  # the golden rod it hangs from
        surf.fill((250, 214, 110), (0, 0, 44, 2))
        return surf

    def paint_torch(self):
        """An iron torch holder on the wall (the fire is drawn every frame, so it can flicker)."""
        surf = pygame.Surface((16, 34), pygame.SRCALPHA)
        surf.fill((70, 68, 82), (4, 24, 8, 10))         # the plate on the wall
        surf.fill((122, 82, 46), (6, 6, 4, 22))         # the stick
        surf.fill((84, 82, 96), (2, 2, 12, 6))          # the iron cup
        surf.fill((120, 118, 132), (2, 2, 12, 2))
        return surf

    def build_castle_things(self, cave):
        """Find the windows (w), banners (f) and torches (i) on the castle walls."""
        self.wall_things, self.torches, self.moonbeams = [], [], []
        if not cave.is_castle:
            return
        for r, row in enumerate(cave.map):
            for c, letter in enumerate(row):
                x, y = c * TILE + TILE // 2, r * TILE
                if letter == "w":
                    window = self.art["window"]
                    self.wall_things.append((window, x - window.get_width() // 2, y + 4))
                    floor = next((rr for rr in range(r + 1, cave.rows) if cave.tile(rr, c) in LOOKS_SOLID + "="), cave.rows)
                    depth = floor * TILE - (y + 96)
                    if depth > TILE:                    # moonlight shining down to the floor
                        self.moonbeams.append((self.paint_moonbeam(depth), x - 20, y + 96))
                elif letter == "f":
                    self.wall_things.append((self.art["banner"], x - 22, y))
                elif letter == "i":
                    self.wall_things.append((self.art["torch"], x - 8, y + 24))
                    self.torches.append((x, y + 26))

    def paint_moonbeam(self, depth):
        """A soft slanted beam of moonlight under a window."""
        slant = depth * 0.35
        beam = pygame.Surface((int(40 + slant + 30), depth), pygame.SRCALPHA)
        for y in range(depth):
            t = y / depth
            left = slant * t
            width = 40 + 30 * t
            beam.fill((200, 190, 255, int(40 * (1 - 0.75 * t))), (left, y, width, 1))
        return beam

    def decorate_castle(self, cave, r, c, rng):
        """Cobwebs in the corners, chains on the ceiling and old bones on the floor."""
        if cave.map[r][c] != ".":
            return
        art = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        roof, floor = cave.tile(r - 1, c) == "#", cave.tile(r + 1, c) == "#"
        left, right = cave.tile(r, c - 1) == "#", cave.tile(r, c + 1) == "#"
        if roof and (left or right) and rng.random() < 0.8:          # a cobweb in the corner
            corner_x, step = (0, 1) if left else (TILE, -1)
            web = (210, 210, 226, 130)
            angles = [i / 4 * math.pi / 2 for i in range(5)]
            for a in angles:
                pygame.draw.line(art, web, (corner_x, 0), (corner_x + step * math.cos(a) * 42, math.sin(a) * 42), 1)
            for radius in (14, 26, 38):
                pygame.draw.lines(art, web, False, [(corner_x + step * math.cos(a) * radius, math.sin(a) * radius)
                                                    for a in angles], 1)
        elif roof and rng.random() < 0.12:                             # a chain hanging from the ceiling
            x, links = rng.randint(14, 50), rng.randint(3, 6)
            for i in range(links):
                pygame.draw.ellipse(art, (96, 94, 110), (x - 3, i * 8, 7, 10), 2)
        elif floor and rng.random() < 0.06:                            # some old bones (spooky!)
            x, bone = rng.randint(10, 34), (214, 208, 190)
            pygame.draw.line(art, bone, (x, TILE - 3), (x + 14, TILE - 6), 3)
            pygame.draw.circle(art, bone, (x + 24, TILE - 7), 7)
            art.fill((44, 36, 46), (x + 20, TILE - 9, 3, 3))
            art.fill((44, 36, 46), (x + 26, TILE - 9, 3, 3))
        if art.get_bounding_rect().w:
            self.cave_decor[(r, c)] = art

    def draw_castle_wall(self, surf):
        """Windows, moonbeams, banners, torch holders and the warm light around each torch."""
        cam_x, cam_y = self.cam
        def seen(x, y, w, h):
            return x < cam_x + VIEW_W and x + w > cam_x and y < cam_y + VIEW_H and y + h > cam_y
        for image, x, y in self.moonbeams + self.wall_things:
            if seen(x, y, *image.get_size()):
                surf.blit(image, (x - cam_x, y - cam_y))
        for i, (x, y) in enumerate(self.torches):
            if seen(x - 100, y - 100, 200, 200):
                glow = self.torch_glows[int(self.time * 9 + i * 3) % 3]
                surf.blit(glow, glow.get_rect(center=(x - cam_x, y - cam_y)))

    def draw_torch_fire(self, surf):
        cam_x, cam_y = self.cam
        for i, (x, y) in enumerate(self.torches):
            x, y = x - cam_x, y - cam_y
            if -20 < x < VIEW_W + 20 and -40 < y < VIEW_H + 20:
                flicker = math.sin(self.time * 13 + i * 2.1) * 3 + math.sin(self.time * 21 + i) * 2
                h = int(18 + flicker)
                lean = int(math.sin(self.time * 7 + i) * 2)
                pygame.draw.ellipse(surf, (255, 110, 30), (x - 7 + lean, y - h, 14, h + 4))
                pygame.draw.ellipse(surf, (255, 200, 80), (x - 4 + lean, y - h * 0.65, 8, h * 0.65 + 3))
                surf.fill((255, 250, 210), (x - 1 + lean, y - 5, 3, 4))

    def draw_trap(self, surf, x, y, c):
        """A spike trap: hidden in the floor... rattling... then SHING!"""
        cave = self.game.cave
        t = cave.clock % (caves.TRAP_DOWN + caves.TRAP_UP)
        if t >= caves.TRAP_DOWN:                        # up!
            rise = min(1.0, (t - caves.TRAP_DOWN) / 0.06)
            hidden = int(30 * (1 - rise))
            surf.blit(self.spikes, (x, y + hidden), (0, 0, TILE, TILE - hidden))
        elif t > caves.TRAP_DOWN - 0.35:                # about to pop up: the tips peek out and rattle
            surf.blit(self.spikes, (x + random.randint(-1, 1), y + 24), (0, 0, TILE, TILE - 24))
        surf.fill((96, 92, 110), (x, y + TILE - 6, TILE, 6))           # the metal plate
        for i in range(4):
            surf.fill((30, 26, 38), (x + i * 16 + 6, y + TILE - 5, 4, 3))

    def draw_castle_thing(self, surf, cave, letter, x, y, r, c):
        """Doors, keys, levers, fountains and light shards: things only the castle has (see castle.py)."""
        last = cave.last_level() if hasattr(cave, "last_level") else True
        if letter in "ED" and last:
            self.draw_throne_door(surf, x, y, locked=letter == "D")
        elif letter in "ED":
            self.draw_level_door(surf, x, y, cave.level + 2, locked=letter == "D", lever=cave.needs == "lever")
        elif letter == "K":
            self.draw_castle_key(surf, x, y, c)
        elif letter in "Ll":
            self.draw_lever(surf, x, y, pulled=letter == "l")
        elif letter == "+":
            self.draw_shard(surf, x, y, c)

    def draw_padlock(self, surf, cx, cy):
        """A big golden padlock: this door needs a key."""
        pygame.draw.arc(surf, (190, 186, 204), (cx - 11, cy - 22, 22, 26), 0, math.pi, 4)    # the shackle
        pygame.draw.rect(surf, (214, 172, 70), (cx - 15, cy - 9, 30, 24), border_radius=4)
        pygame.draw.rect(surf, (150, 112, 40), (cx - 15, cy - 9, 30, 24), 2, border_radius=4)
        pygame.draw.circle(surf, (40, 26, 20), (cx, cy), 4)                               # the keyhole
        surf.fill((40, 26, 20), (cx - 1, cy, 3, 9))

    def draw_level_door(self, surf, x, y, number, locked, lever):
        """The door to the next level: 2 blocks wide and 3 tall, standing on the D (locked) or E (open).
        A key door has a padlock. A lever door has iron bars that lift up when you pull the lever."""
        w, h = 112, 3 * TILE - 16
        left, top = x + TILE // 2 - w // 2, y + TILE - h
        arch = dict(border_top_left_radius=56, border_top_right_radius=56)
        pygame.draw.rect(surf, (116, 108, 140), (left - 9, top - 9, w + 18, h + 9), **arch)     # the stone arch
        pygame.draw.rect(surf, (78, 72, 100), (left - 9, top - 9, w + 18, h + 9), 3, **arch)
        if locked:
            pygame.draw.rect(surf, (88, 56, 40), (left, top, w, h), border_top_left_radius=50, border_top_right_radius=50)
            for px in range(left + 14, left + w, 14):       # wooden planks
                pygame.draw.line(surf, (60, 38, 28), (px, top + 8), (px, top + h - 1), 2)
            if lever:                                       # iron bars in front of the door
                for px in range(left + 10, left + w, 18):
                    surf.fill((70, 68, 84), (px, top + 12, 6, h - 12))
                    surf.fill((120, 118, 136), (px + 1, top + 12, 2, h - 12))
                surf.fill((70, 68, 84), (left, top + 50, w, 6))
            else:
                self.draw_padlock(surf, x + TILE // 2, top + 96)
        else:                                               # open: a dark passage with a soft purple light
            pulse = 0.5 + 0.5 * math.sin(self.time * 3)
            pygame.draw.rect(surf, (24, 16, 34), (left, top, w, h), border_top_left_radius=50, border_top_right_radius=50)
            glow = pygame.Surface((w - 24, h - 30), pygame.SRCALPHA)
            glow.fill((170, 110, 255, int(40 + 40 * pulse)))
            surf.blit(glow, (left + 12, top + 30))
            pygame.draw.polygon(surf, (88, 56, 40), [(left, top + 30), (left + 18, top + 40), (left + 18, top + h), (left, top + h)])
        self.text(surf, "LEVEL %d" % number, (x + TILE // 2, top - 12), 24, (226, 170, 255), "midbottom", shadow=True)

    def draw_castle_key(self, surf, x, y, c):
        """The key: big, golden, bobbing up and down, glinting so you can spot it from far away."""
        bob = math.sin(self.time * 3 + c) * 4
        cx, cy = x + TILE // 2, int(y + TILE // 2 + bob)
        surf.blit(self.key_glow, self.key_glow.get_rect(center=(cx, cy)))
        gold, dark = (240, 196, 70), (160, 116, 30)
        pygame.draw.circle(surf, gold, (cx - 14, cy), 13)       # the ring you hold
        pygame.draw.circle(surf, dark, (cx - 14, cy), 13, 3)
        pygame.draw.circle(surf, (60, 40, 20), (cx - 14, cy), 5)
        surf.fill(gold, (cx - 3, cy - 4, 32, 8))                # the long part
        surf.fill(dark, (cx - 3, cy + 2, 32, 2))
        surf.fill(gold, (cx + 18, cy + 4, 5, 10))               # the teeth
        surf.fill(gold, (cx + 25, cy + 4, 4, 7))
        self.draw_twinkle(surf, cx + 16, cy - 14, c)

    def draw_twinkle(self, surf, x, y, c):
        """A little white star that grows and shrinks."""
        t = (self.time * 1.3 + c * 0.37) % 1.0
        if t < 0.4:
            size = int(7 * math.sin(t / 0.4 * math.pi)) + 1
            pygame.draw.line(surf, (255, 255, 255), (x - size, y), (x + size, y), 2)
            pygame.draw.line(surf, (255, 255, 255), (x, y - size), (x, y + size), 2)

    def draw_lever(self, surf, x, y, pulled):
        """A big lever on the wall. Before you pull it, it glints. Pulled, it points down."""
        cx, cy = x + TILE // 2, y + 34
        if not pulled:
            surf.blit(self.key_glow, self.key_glow.get_rect(center=(cx, cy - 6)))
        plate = pygame.Rect(cx - 16, cy - 8, 32, 30)            # the iron plate on the wall
        surf.fill((70, 68, 84), plate.inflate(4, 4))
        surf.fill((146, 142, 164), plate)
        surf.fill((186, 182, 204), (plate.x, plate.y, plate.w, 4))
        for rx, ry in ((plate.x + 4, plate.y + 6), (plate.right - 7, plate.y + 6),
                       (plate.x + 4, plate.bottom - 7), (plate.right - 7, plate.bottom - 7)):
            surf.fill((70, 68, 84), (rx, ry, 3, 3))             # rivets
        end = (cx + 22, cy + 24) if pulled else (cx - 18, cy - 28)
        pygame.draw.line(surf, (70, 44, 24), (cx, cy + 8), end, 9)    # the handle
        pygame.draw.line(surf, (150, 102, 56), (cx, cy + 8), end, 5)
        pygame.draw.circle(surf, (120, 20, 30), end, 9)
        pygame.draw.circle(surf, (230, 60, 60), end, 7)
        pygame.draw.circle(surf, (255, 170, 170), (end[0] - 2, end[1] - 2), 2)
        if not pulled:
            self.draw_twinkle(surf, cx + 12, cy - 26, x)

    def draw_fountain(self, surf, x, y, full, stone=None):
        """A healing fountain: a stone bowl of glowing water. full: 1 = ready, 0 = just drunk from.
        stone: the colour of the bowl (in a cave it's made of the cave's own rock)."""
        cx, base = x + TILE // 2, y + TILE
        stone = stone or (150, 144, 172)
        dark = tuple(max(0, v - 58) for v in stone)
        surf.fill(dark, (cx - 8, base - 22, 16, 22))              # the stem
        if full >= 1:
            surf.blit(self.water_glow, self.water_glow.get_rect(center=(cx, base - 30)))
        bowl = pygame.Rect(cx - 30, base - 40, 60, 20)
        pygame.draw.ellipse(surf, stone, bowl)
        level = int(12 * full)
        if level:                                                 # the water inside
            pygame.draw.ellipse(surf, (90, 190, 255), (cx - 24, base - 38, 48, 4 + level))
        pygame.draw.ellipse(surf, dark, bowl, 3)
        if full >= 1:                                             # sparkling: ready to drink!
            for i in range(3):
                t = (self.time * 1.5 + i / 3) % 1.0
                pygame.draw.circle(surf, (210, 240, 255), (cx - 14 + i * 14, int(base - 40 - t * 22)), 2)

    def draw_shard(self, surf, x, y, c):
        """A light shard: a little crystal of sunlight, glowing and floating."""
        bob = math.sin(self.time * 2.5 + c) * 5
        cx, cy = x + TILE // 2, int(y + TILE // 2 + bob)
        pulse = 1 + 0.12 * math.sin(self.time * 5)
        glow = pygame.transform.smoothscale(self.shard_glow, (int(104 * pulse), int(104 * pulse)))
        surf.blit(glow, glow.get_rect(center=(cx, cy)))
        points = [(cx, cy - 18), (cx + 9, cy - 2), (cx + 3, cy + 16), (cx - 8, cy + 4)]
        pygame.draw.polygon(surf, (255, 236, 150), points)
        pygame.draw.polygon(surf, (255, 255, 230), [(cx, cy - 18), (cx + 9, cy - 2), (cx, cy)])
        pygame.draw.polygon(surf, (220, 170, 60), points, 2)
        self.draw_twinkle(surf, cx - 12, cy - 14, c)
        self.draw_twinkle(surf, cx + 14, cy + 8, c + 2)

    def draw_back_door(self, surf, cave):
        """Levels 2-5: the gap on the left is an open door back to the level before."""
        level = getattr(cave, "level", 0)
        if not level or not self.daylight:
            return
        cam_x, cam_y = self.cam
        x, y, h = -cam_x, self.daylight_y - cam_y, self.daylight.get_height()
        pygame.draw.rect(surf, (116, 108, 140), (x - 8, y - 14, TILE + 22, 14), border_top_right_radius=10)
        surf.fill((116, 108, 140), (x + TILE, y - 14, 14, h + 14))              # the door frame
        surf.fill((78, 72, 100), (x + TILE + 11, y - 14, 3, h + 14))
        pygame.draw.polygon(surf, (88, 56, 40), [(x + TILE + 14, y), (x + TILE + 30, y + 10),
                                                 (x + TILE + 30, y + h), (x + TILE + 14, y + h)])   # the open door
        self.text(surf, "< LEVEL %d" % level, (x + 10, y - 18), 22, (226, 170, 255), "bottomleft", shadow=True)

    def draw_throne_door(self, surf, x, y, locked=False, inside=False):
        """The great door of the throne room: 2 blocks wide and 3 tall, standing on the E (or the D while it's locked).
        inside=True: the same door from inside the throne room, slammed shut and barred."""
        pulse = 0.5 + 0.5 * math.sin(self.time * 2.5)
        w, h = 128, 3 * TILE
        left, top = x + TILE // 2 - w // 2, y + TILE - h
        surf.blit(self.throne_glow, self.throne_glow.get_rect(center=(x + TILE // 2, top + h // 2)))
        arch = dict(border_top_left_radius=64, border_top_right_radius=64)
        pygame.draw.rect(surf, (120, 112, 146), (left - 10, top - 10, w + 20, h + 10), **arch)    # the stone arch
        pygame.draw.rect(surf, (80, 74, 102), (left - 10, top - 10, w + 20, h + 10), 3, **arch)
        pygame.draw.rect(surf, (62, 32, 56), (left, top, w, h), border_top_left_radius=56, border_top_right_radius=56)
        for px in range(left + 16, left + w, 16):       # wooden planks
            pygame.draw.line(surf, (44, 22, 40), (px, top + 10), (px, top + h - 1), 2)
        for by in (top + 64, top + 144):                # iron bands with rivets
            surf.fill((54, 52, 66), (left, by, w, 8))
            for rx in range(left + 8, left + w, 20):
                surf.fill((120, 118, 136), (rx, by + 3, 3, 3))
        light = (210, int(120 + 70 * pulse), 255)       # purple light leaking out between the doors
        surf.fill(light, (left + w // 2 - 2, top + 16, 4, h - 16))
        surf.fill(light, (left + 6, top + h - 3, w - 12, 3))
        for hx in (left + w // 2 - 16, left + w // 2 + 16):   # door rings
            pygame.draw.circle(surf, (214, 172, 70), (hx, top + 112), 7, 2)
        if locked:                                      # a heavy chain and a padlock: find the key!
            for i in range(9):
                for sx in (1, -1):
                    pygame.draw.ellipse(surf, (150, 146, 162), (left + w // 2 + sx * (10 + i * 7) - 5, top + 96 + i * 5, 10, 7), 2)
            self.draw_padlock(surf, left + w // 2, top + 100)
        if inside:                                      # slammed shut, with a heavy iron bar across it
            surf.fill((70, 68, 84), (left - 14, top + 120, w + 28, 16))
            surf.fill((130, 128, 146), (left - 14, top + 120, w + 28, 3))
            return
        crown = [(-18, 12), (-18, -6), (-9, 3), (0, -10), (9, 3), (18, -6), (18, 12)]
        cx, cy = x + TILE // 2, top - 32
        pygame.draw.polygon(surf, (214, 172, 70), [(cx + a, cy + b) for a, b in crown])
        surf.fill((200, 120, 255), (cx - 3, cy, 6, 6))
        self.text(surf, "THRONE ROOM", (cx, cy - 14), 26, (226, 170, 255), "midbottom", shadow=True)

    # ----- the throne room: the Shadow King, his sword and his fireballs (throne.py) ---------

    def draw_throne_thing(self, surf, room, letter, x, y):
        if letter == "Y":
            self.draw_throne(surf, x, y)
        elif letter == "n":                             # the healing spring: its water goes down as you use it
            self.draw_fountain(surf, x, y, room.healing_left / throne.NOOK_HEALING)
            if room.healing_left:
                self.text(surf, "+%d" % room.healing_left, (x + TILE // 2, y + 2), 24, GREEN, "midtop", shadow=True)
        elif letter == "S":                             # the great door you came in by, slammed shut
            self.draw_throne_door(surf, x, y, inside=True)

    def draw_throne(self, surf, x, y):
        """The Shadow King's throne: tall and purple, with gold all around it."""
        cx, base = x + TILE // 2, y + TILE
        gold, velvet, dark = (214, 172, 70), (96, 40, 120), (44, 30, 56)
        back = [(cx - 52, base - 70), (cx - 52, base - 170), (cx - 26, base - 186), (cx, base - 206),
                (cx + 26, base - 186), (cx + 52, base - 170), (cx + 52, base - 70)]
        pygame.draw.polygon(surf, dark, back)                               # the tall back
        pygame.draw.polygon(surf, gold, back, 4)
        pygame.draw.polygon(surf, velvet, [(cx - 36, base - 78), (cx - 36, base - 160), (cx, base - 184),
                                           (cx + 36, base - 160), (cx + 36, base - 78)])
        pygame.draw.circle(surf, (200, 120, 255), (cx, base - 192), 6)     # a purple gem on top
        surf.fill(dark, (cx - 56, base - 62, 12, 62))                       # the legs
        surf.fill(dark, (cx + 44, base - 62, 12, 62))
        surf.fill(gold, (cx - 62, base - 76, 124, 14))                      # the seat
        surf.fill(gold, (cx - 66, base - 112, 12, 40))                      # the arm rests
        surf.fill(gold, (cx + 54, base - 112, 12, 40))

    def draw_king(self, surf, room):
        """The Shadow King: a purple glow (red when he's angry), his body, and his big sword."""
        king = room.king
        feet_x, feet_y = self.on_screen((king.x + king.w / 2) * TILE, (king.y + king.h) * TILE)
        under = art_bottom(sprites.SHADOW_KING) * KING_SCALE           # the see-through row under his feet
        pictures, glows = self.king_pictures, self.king_glows
        new_look = phase2.king_look(self)               # Phase 2: the new Shadow King (phase2/art.py)
        if new_look:
            pictures, glows, under = new_look
        if room.beaten_time is not None:                # beaten: he glows white, then melts away into light
            image = whiten(pictures[0])
            image.set_alpha(int(255 * max(0.0, room.beaten_time) / throne.VICTORY_TIME))
            surf.blit(image, image.get_rect(midbottom=(feet_x, feet_y + under)))
            return
        glow = glows[1 if king.angry else 0]
        surf.blit(glow, glow.get_rect(center=(feet_x, feet_y - king.h * TILE / 2)))
        if king.doing == "aim":                         # a fireball grows at his feet...
            grow = 1 - max(0.0, king.timer) / king.normal_or_angry(throne.THROW_WARNING)
            ball_x = (king.x + king.w / 2 + king.facing * (king.w / 2 + throne.FIREBALL_SIZE / 2)) * TILE
            x, y = self.on_screen(ball_x, (room.floor - throne.FIREBALL_HEIGHT) * TILE)
            self.draw_fireball(surf, x, y, 0.3 + 0.7 * grow)
        image = pictures[1 if king.angry else 0]
        if king.flash > 0:
            image = whiten(image)
        surf.blit(image, image.get_rect(midbottom=(feet_x, feet_y + under)))
        self.draw_king_sword(surf, king, feet_x, feet_y - king.h * TILE)
        if king.doing in ("warn", "aim") and int(self.time * 8) % 2 == 0:      # "!" over his head: watch out!
            self.text(surf, "!", (feet_x, feet_y - king.h * TILE - 8), 64, RED if king.doing == "warn" else (220, 150, 255),
                      "midbottom", shadow=True)

    def draw_king_sword(self, surf, king, cx, top):
        """His sword, in his front hand. It glows before he slashes, swings down, then gets stuck in the floor."""
        hand_x, hand_y = cx + king.facing * 52, top + 100
        raised = 0.0                                    # 1 = his arm is up over his head
        if king.doing == "warn":
            angle, raised = 35, 1.0
        elif king.doing == "slash":
            t = 1 - max(0.0, king.timer) / throne.SLASH_TIME
            angle, raised = lerp(35, -115, t), 1 - t
        elif king.doing == "stuck":
            angle = -115
        else:
            angle = -25 + math.sin(self.time * 2) * 4
        hand = (hand_x - king.facing * 12 * raised, hand_y - 48 * raised)
        image = self.king_sword
        if king.facing < 0:
            image = pygame.transform.flip(image, True, False)
            angle = -angle
        if king.doing == "warn":                        # GLOWING: he's about to slash!
            a = math.radians(angle)
            middle = (hand[0] - math.sin(a) * 55, hand[1] - math.cos(a) * 55)
            surf.blit(self.warn_glow, self.warn_glow.get_rect(center=middle))
            if int(self.time * 16) % 2 == 0:
                image = whiten(image)
        if king.doing == "slash":                       # a swoosh behind the blade
            for back in (1, 2, 3):
                ghost = pygame.transform.rotate(image, angle + king.facing * 22 * back)
                ghost.set_alpha(150 - 40 * back)
                surf.blit(ghost, ghost.get_rect(center=hand))
        turned = pygame.transform.rotate(image, angle)
        surf.blit(turned, turned.get_rect(center=hand))

    def draw_fireballs(self, surf, room):
        for ball in room.fireballs:
            x, y = self.on_screen(ball["x"] * TILE, ball["y"] * TILE)
            self.draw_fireball(surf, x, y)
            if random.random() < 0.6:                   # a trail of purple sparks
                self.particles.append({"x": ball["x"] * TILE, "y": ball["y"] * TILE + random.uniform(-10, 10),
                                       "vx": -ball["vx"] * 8, "vy": random.uniform(-40, 0), "gravity": -60,
                                       "life": 0.35, "age": 0.0, "size": random.randint(3, 5),
                                       "color": random.choice([(200, 120, 255), (120, 50, 170)]), "layer": "map"})

    def draw_fire_arrow(self, surf, tail, head):
        """Your fire arrow: a wooden shaft with a chunky, flickering flame wrapped around the tip."""
        (tx, ty), (hx, hy) = tail, head
        length = math.hypot(hx - tx, hy - ty) or 1
        dx, dy = (hx - tx) / length, (hy - ty) / length
        pygame.draw.line(surf, (150, 95, 50), (tx, ty), (hx, hy), 4)              # the wooden shaft
        flick = int(self.time * 18) % 2                                           # the flame flickers
        for back, size, color in ((14 + 3 * flick, 12, (240, 90, 40)), (8, 10, ORANGE), (3, 7, YELLOW)):
            cx, cy = hx - dx * back, hy - dy * back                               # chunky blocks of fire
            pygame.draw.rect(surf, color, (int(cx - size / 2), int(cy - size / 2) - flick * 2, size, size))
        pygame.draw.rect(surf, (255, 250, 220), (int(hx) - 2, int(hy) - 2, 5, 5)) # the white-hot tip

    def draw_fireball(self, surf, x, y, size=1.0):
        """A shadow fireball: dark purple fire with a hot violet edge."""
        r = max(2, int(15 * size * (1 + math.sin(self.time * 25 + x) * 0.1)))
        x, y = int(x), int(y)
        surf.blit(self.fireball_glow, self.fireball_glow.get_rect(center=(x, y)))
        pygame.draw.circle(surf, (200, 120, 255), (x, y), r + 3)
        pygame.draw.circle(surf, (60, 16, 90), (x, y), r)
        pygame.draw.circle(surf, (240, 200, 255), (x, y), max(1, r // 3))

    def draw_light_coming_back(self, surf, room):
        """You beat him! Warm light pours out of where he was standing and fills the room."""
        t = 1 - max(0.0, room.beaten_time) / throne.VICTORY_TIME
        king = room.king
        cx, cy = self.on_screen((king.x + king.w / 2) * TILE, (king.y + king.h / 2) * TILE)
        self.light.fill((255, 236, 170, int(170 * t)))
        for i in range(12):                             # rays of sunlight, turning slowly
            a = self.time * 0.5 + i * math.pi / 6
            far = 1200
            ray = [(cx, cy), (cx + math.cos(a - 0.07) * far, cy + math.sin(a - 0.07) * far),
                   (cx + math.cos(a + 0.07) * far, cy + math.sin(a + 0.07) * far)]
            pygame.draw.polygon(self.light, (255, 250, 220, int(90 * min(1.0, t * 3))), ray)
        surf.blit(self.light, (0, 0))

    def draw_king_bar(self, surf, room):
        """THE SHADOW KING and his health, across the top of the screen."""
        king = room.king
        angry = king.angry and king.is_alive
        w = 520
        x = (VIEW_W - w) // 2
        self.text(surf, "THE SHADOW KING" + ("  -  ANGRY!" if angry else ""), (VIEW_W // 2, 8), 34,
                  RED if angry else (226, 170, 255), "midtop", shadow=True)
        color = (190, 100, 255)
        if angry:
            color = (255, 150, 150) if int(self.time * 6) % 2 else RED
        pygame.draw.rect(surf, (20, 14, 30), (x - 3, 37, w + 6, 26), border_radius=13)
        self.bar(surf, (x, 40, w, 20), king.health / king.max_health, color)
        half = x + int(w * throne.ANGRY_AT)             # when his health gets to here, he gets angry
        pygame.draw.line(surf, TEXT, (half, 36), (half, 64), 2)

    def draw_bats(self, surf):
        """Every now and then a bat flaps across the castle."""
        cam_x, cam_y = self.cam
        if len(self.bats) < 3 and random.random() < 0.006:
            going = random.choice((-1, 1))
            self.bats.append({"x": cam_x + (VIEW_W + 30 if going < 0 else -30), "y": cam_y + random.uniform(40, VIEW_H * 0.45),
                              "vx": going * random.uniform(170, 250), "flap": random.uniform(0, 6)})
        for bat in self.bats:
            bat["x"] += bat["vx"] / 60
            bat["flap"] += 0.3
            x, y = bat["x"] - cam_x, bat["y"] - cam_y + math.sin(bat["flap"] * 0.35) * 12
            wing = math.sin(bat["flap"]) * 9
            for side in (-1, 1):
                pygame.draw.polygon(surf, (16, 10, 26), [(x, y), (x + side * 15, y - wing), (x + side * 8, y + 4)])
            pygame.draw.circle(surf, (16, 10, 26), (int(x), int(y + 1)), 5)
            surf.fill((255, 90, 90), (x - 3, y, 2, 2))
            surf.fill((255, 90, 90), (x + 1, y, 2, 2))
        self.bats = [bat for bat in self.bats if -60 < bat["x"] - cam_x < VIEW_W + 60]

    def paint_ladder(self):
        """A wooden ladder: two rails and four rungs."""
        surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        wood, dark, light = (150, 102, 56), (96, 62, 32), (190, 140, 84)
        for x in (12, 46):                          # the rails
            surf.fill(dark, (x, 0, 7, TILE))
            surf.fill(wood, (x + 1, 0, 5, TILE))
            surf.fill(light, (x + 1, 0, 1, TILE))
        for y in (6, 22, 38, 54):                   # the rungs
            surf.fill(dark, (17, y, 31, 6))
            surf.fill(wood, (17, y, 31, 4))
            surf.fill(light, (17, y, 31, 1))
        return surf

    def paint_vine(self, cave, rng, top=False):
        """A vine: a twisty green stem with leaves. You climb it just like a ladder.
        (Moss, crystal and lava caves use the chunky VINE pictures from sprites.py.)"""
        if cave.theme in CAVE_COLORS:
            return self.cave_sprite(sprites.VINE_TOP if top else sprites.VINE, flip=rng.random() < 0.5, scale=ART_PIXEL)
        surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        stem, dark, leaf, light = (70, 140, 50), (40, 90, 34), (100, 190, 70), (160, 230, 110)
        wiggle = rng.uniform(0, 6.28)
        points = [(32 + 7 * math.sin(wiggle + y / 9), y) for y in range(0, TILE + 1, 4)]
        pygame.draw.lines(surf, dark, False, [(x + 2, y) for x, y in points], 7)
        pygame.draw.lines(surf, stem, False, points, 5)
        for i, y in enumerate((8, 24, 40, 56)):                 # leaves, one on each side in turn
            x = 32 + 7 * math.sin(wiggle + y / 9)
            side = 1 if (i + rng.randint(0, 1)) % 2 else -1
            pygame.draw.ellipse(surf, leaf, (x + (2 if side > 0 else -16), y - 5, 14, 8))
            surf.fill(light, (x + (6 if side > 0 else -10), y - 3, 4, 2))
        if top:                                                 # where it's tied onto the branch above
            pygame.draw.ellipse(surf, dark, (22, -4, 20, 12))
            pygame.draw.ellipse(surf, stem, (24, -3, 16, 9))
        return surf

    def tie_vine_on(self, ledge):
        """A ledge with a vine hanging under it: the top of the vine is tied on just under the plank,
        so the vine reaches all the way up to the ledge."""
        ledge = ledge.copy()
        under = 4 * ART_PIXEL                       # the plank is the top 4 chunky pixels of the ledge
        vine = self.cave_sprite(sprites.VINE, scale=ART_PIXEL)
        ledge.blit(vine, (0, under), (0, under, TILE, TILE - under))
        knot = self.cave_sprite(sprites.VINE_TOP, scale=ART_PIXEL)
        ledge.blit(knot, (0, under), (0, 0, TILE, 4 * ART_PIXEL))      # the bunch of leaves where it's tied
        return ledge

    def paint_ice(self, cave, r, c, rng):
        """A block of slippery ice: pale blue, with white shine streaks (and frost on top).
        (Moss, crystal and lava caves paint theirs in chunky pixels.)"""
        if cave.theme in CAVE_COLORS:
            return self.paint_chunky_ice(cave, r, c, rng)
        top = cave.tile(r - 1, c) not in LOOKS_SOLID
        surf = pygame.Surface((TILE, TILE))
        surf.fill((150, 214, 244))
        pygame.draw.rect(surf, (96, 164, 214), (0, 0, TILE, TILE), 3)
        for _ in range(2):                                      # shine streaks
            x = rng.randint(6, 40)
            pygame.draw.line(surf, (226, 246, 255), (x, 54), (x + 16, 12), 4)
            pygame.draw.line(surf, (196, 234, 252), (x + 8, 56), (x + 20, 26), 2)
        for _ in range(5):                                      # little bubbles frozen inside
            surf.fill((206, 238, 255), (rng.randint(6, 56), rng.randint(14, 56), 3, 3))
        if top:                                                 # frost on top
            surf.fill((236, 250, 255), (0, 0, TILE, 7))
            for x in range(4, TILE, 12):
                surf.fill((236, 250, 255), (x, 7, 6, rng.randint(2, 6)))
        return surf

    def add_handholds(self, surf, rng):
        """Little bumps to hold on to: you can wall jump on this wall!"""
        for _ in range(5):
            x, y = rng.randint(6, 50), rng.randint(4, 52)
            pygame.draw.ellipse(surf, (40, 34, 44), (x, y + 2, 12, 8))
            pygame.draw.ellipse(surf, (206, 196, 168), (x, y, 12, 8))
            surf.fill((246, 240, 218), (x + 3, y + 1, 4, 2))

    def paint_ledge(self, color, cracks=False, theme="stone", look=0):
        """A wooden ledge. look picks one of a few different ones (0, 1 or 2).
        (Moss, crystal and lava caves paint theirs in chunky pixels, with moss, snow or red moss on top.)"""
        if theme in CAVE_COLORS:
            return self.paint_chunky_ledge(color, cracks, theme, look)
        rng = random.Random(look * 31 + cracks)    # the same look is always painted the same way
        surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        dark = tuple(max(0, v - 48) for v in color)
        surf.fill(color, (0, 0, TILE, 12))
        surf.fill(tuple(min(255, v + 28) for v in color), (0, 0, TILE, 3))
        surf.fill(dark, (0, 12, TILE, 3))
        for x in ((20, 42), (14, 38), (28, 50))[look % 3]:      # the gaps between the planks
            surf.fill(dark, (x, 0, 2, 12))
        if look:                                    # a line in the wood
            surf.fill(tuple(max(0, v - 22) for v in color), (rng.randint(4, 30), 7, rng.randint(10, 24), 1))
        if cracks:                                  # crumbly: it breaks if you stand on it!
            pygame.draw.lines(surf, dark, False, [(8, 0), (12, 6), (9, 12)], 2)
            pygame.draw.lines(surf, dark, False, [(52, 0), (48, 7), (54, 12)], 2)
            surf.fill(dark, (30, 13, 4, 4))
        else:
            for x in ((5, 56), (9, 52), (5, 33))[look % 3]:     # nails
                surf.fill((70, 54, 40), (x, 5, 3, 3))
        return surf

    def cave_sprite(self, art, flip=False, scale=CAVE_SCALE, shadow=False):
        key = (id(art), flip, scale, shadow)
        if key not in self.cave_art:
            image = phase2.cave_picture(art, scale) or make_sprite(art, scale)      # (Phase 2: 32 x 32 art)
            if shadow:                              # a shadow monster: darker, with a purple glow
                image.fill((120, 96, 160), special_flags=pygame.BLEND_RGB_MULT)
                image.fill((26, 0, 40), special_flags=pygame.BLEND_RGB_ADD)
            self.cave_art[key] = pygame.transform.flip(image, True, False) if flip else image
        return self.cave_art[key]

    def draw_body(self, surf, body, art, flash=False, bob=0.0, shadow=False):
        """Draw a picture standing on the bottom of a body (you, or a monster). Returns its top-left."""
        image = self.cave_sprite(art, flip=body.facing < 0, shadow=shadow)
        if flash:
            image = whiten(image)
        x, y = self.on_screen(body.x * TILE, body.y * TILE)
        left = x + body.w * TILE / 2 - image.get_width() / 2
        top = y + body.h * TILE + art_bottom(art) * phase2.art_pixel(art, CAVE_SCALE) - image.get_height() + bob
        surf.blit(image, (left, top))
        return left, top

    def draw_drawn_bow(self, surf, m):
        """A Skeleton that just saw you draws its bow: the string pulls back while it aims. Get ready!"""
        pull = 1 - m.aim / caves.SKELETON_AIM          # 0 = just started, 1 = about to shoot
        x, y = self.on_screen((m.x + m.w / 2 + 0.45 * m.facing) * TILE, (m.y + m.h * 0.55) * TILE)
        f, half = m.facing, 26
        bow = (170, 110, 60)
        pygame.draw.arc(surf, bow, (x - 22 if f > 0 else x - 2, y - half, 24, 2 * half),
                        -math.pi / 2 if f > 0 else math.pi / 2, math.pi / 2 if f > 0 else 3 * math.pi / 2, 4)
        back = x - f * (2 + 16 * pull)                  # where the string is pulled back to
        string = (240, 240, 240)
        pygame.draw.line(surf, string, (x, y - half), (back, y), 2)
        pygame.draw.line(surf, string, (x, y + half), (back, y), 2)
        pygame.draw.line(surf, (230, 220, 200), (back, y), (x + f * 14, y), 3)    # the arrow, ready to fly
        pygame.draw.circle(surf, (255, 255, 255), (int(x + f * 14), int(y)), 3)
        if int(self.time * 8) % 2 == 0 or pull > 0.7:  # a blinking "!" over its head
            self.text(surf, "!", (x - f * 0.45 * TILE, y - 0.8 * TILE), 44, ORANGE, "midbottom", shadow=True)

    def draw_cave(self, surf):
        cave = self.game.cave
        cam_x, cam_y = self.cam
        while cave.dirty:                           # something was dug out: repaint it and its neighbors
            r, c = cave.dirty.pop()
            for rr in range(max(0, r - 1), min(cave.rows, r + 2)):
                for cc in range(max(0, c - 1), min(cave.cols, c + 2)):
                    self.paint_cave_tile(cave, rr, cc)

        # The back wall moves at half speed, so it looks far away (a castle wall is right behind you)
        surf.fill(self.theme["back"])
        bw, bh = self.cave_back.get_size()
        speed = 1 if cave.is_castle else 2
        ox, oy = -(cam_x // speed) % bw, -(cam_y // speed) % bh
        for x in range(ox - bw, VIEW_W, bw):
            for y in range(oy - bh, VIEW_H, bh):
                surf.blit(self.cave_back, (x, y))
        if self.daylight:
            surf.blit(self.daylight, (-cam_x, self.daylight_y - cam_y))
        self.draw_castle_wall(surf)

        # Blocks and everything else in the cave - just the parts the camera can see
        self.lava_lights = []
        first_r, first_c = max(0, cam_y // TILE - 1), max(0, cam_x // TILE)   # -1: a long vine can hang down from above
        last_r = min(cave.rows, (cam_y + VIEW_H) // TILE + 3)      # +3: the great door is 3 blocks tall
        last_c = min(cave.cols, (cam_x + VIEW_W) // TILE + 2)
        for r in range(first_r, last_r):
            for c in range(first_c, last_c):
                x, y = c * TILE - cam_x, r * TILE - cam_y
                image = self.cave_tiles.get((r, c)) or self.cave_decor.get((r, c))
                if image:
                    surf.blit(image, (x, y))
                letter = cave.map[r][c]
                if letter == "o":
                    squash = self.squash.get((r, c), 0)
                    mushroom = self.art["mushroom"]
                    if squash:
                        mushroom = pygame.transform.scale(mushroom, (TILE + 10, int(TILE * (1 - squash))))
                    surf.blit(mushroom, mushroom.get_rect(midbottom=(x + TILE // 2, y + TILE)))
                elif letter == "$":
                    bob = math.sin(self.time * 4 + c) * 3
                    surf.blit(self.small_glow, self.small_glow.get_rect(center=(x + 32, y + 32 + bob)))
                    surf.blit(self.art["gem"], self.art["gem"].get_rect(center=(x + 32, y + 32 + bob)))
                elif letter == "-":
                    shake = random.randint(-2, 2) if (r, c) in cave.crumbling else 0
                    surf.blit(self.crumbly_looks.get((r, c), self.crumbly), (x + shake, y))
                elif letter == "^":
                    surf.blit(self.spikes, (x, y))
                elif letter == "~":
                    self.draw_lava(surf, x, y, c, deep=cave.tile(r - 1, c) == "~")
                elif letter == "!":
                    self.draw_fire(surf, x, y, c)
                elif letter in "Tt":
                    chest = self.art["chest" if letter == "T" else "chest_open"]
                    surf.blit(chest, (x, y + TILE + art_bottom(sprites.CHEST) * 4 - chest.get_height()))
                    if letter == "T" and int(self.time * 2 + c) % 3 == 0:
                        surf.fill((255, 255, 220), (x + 34, y + 30, 3, 3))      # a little glint
                elif letter in "*s":
                    for i in range(2):                                         # twinkling diamonds (and Sun Shards)
                        t = (self.time * 1.5 + i * 0.5 + c * 0.3) % 1.0
                        if t < 0.3:
                            sx, sy = x + (14, 46)[i], y + (16, 42)[i]
                            size = int(6 * math.sin(t / 0.3 * math.pi)) + 1
                            pygame.draw.line(surf, (255, 255, 255), (sx - size, sy), (sx + size, sy), 2)
                            pygame.draw.line(surf, (255, 255, 255), (sx, sy - size), (sx, sy + size), 2)
                elif letter == "A":
                    self.draw_trap(surf, x, y, c)
                elif letter == "u":                     # a healing spring (in the castle: a fountain)
                    full = 1 - cave.fountains.get((r, c), 0.0) / caves.FOUNTAIN_REFILL
                    if self.springs:
                        self.draw_spring(surf, x, y, full)
                    else:
                        self.draw_fountain(surf, x, y, full, stone=None if cave.is_castle else self.spring_stone)
                elif letter in "Gg":                    # an iron gate (g: opened by a lever)
                    self.draw_gate(surf, x, y, opened=letter == "g")
                elif letter == caves.JET:
                    self.draw_jet(surf, cave, x, y, r, c)
                elif letter == caves.GEYSER:
                    self.draw_geyser(surf, cave, x, y, c)
                elif letter in "Ll" and not cave.is_castle:  # a lever in a cave (the castle draws its own)
                    self.draw_lever(surf, x, y, pulled=letter == "l")
                elif cave.is_castle and letter in CASTLE_THINGS:
                    self.draw_castle_thing(surf, cave, letter, x, y, r, c)
                elif cave.is_throne_room and letter in THRONE_THINGS:
                    self.draw_throne_thing(surf, cave, letter, x, y)
                elif letter == "E":
                    self.draw_exit_door(surf, x, y)
        self.draw_platforms(surf, cave)
        self.draw_swings(surf, cave)
        for spot in self.lava_lights:               # lava pools light up the rock around them
            surf.blit(self.pool_glow, self.pool_glow.get_rect(center=spot))
        self.draw_drips(surf)
        if cave.is_castle:
            self.draw_back_door(surf, cave)

        self.draw_torch_fire(surf)

        # Monsters
        for m in cave.monsters:
            art = phase2.cave_monster_art(self, m.kind) or sprites.MONSTER_ART.get(m.kind, sprites.ZOMBIE)  # (Phase 2)
            flash = m.flash > 0
            if m.fuse is not None:                  # an Ember Skull about to blow - it flashes faster and faster!
                flash = flash or int(self.time * (6 + 14 * (1 - m.fuse / caves.FUSE_TIME))) % 2 == 0
            bob = 0.0
            if m.kind == "Ember Skull":             # it floats, wrapped in flickering fire
                bob = math.sin(self.time * 3 + m.x) * 4
                x, y = self.on_screen((m.x + m.w / 2) * TILE, (m.y + m.h / 2) * TILE)
                glow = self.torch_glows[int(self.time * 9 + m.x) % 3]
                surf.blit(glow, glow.get_rect(center=(x, y + bob)))
            left, top = self.draw_body(surf, m, art, flash=flash, shadow=m.info.shadow, bob=bob)
            if m.aim is not None and m.aim > 0 and m.stunned <= 0:
                self.draw_drawn_bow(surf, m)
            if m.info.health < m.info.max_health:
                x, _ = self.on_screen(m.x * TILE, 0)
                self.bar(surf, (x + m.w * TILE / 2 - 24, top - 4, 48, 6), m.info.health / m.info.max_health, RED)
        if cave.is_throne_room:                     # the Shadow King himself, and his fireballs
            self.draw_king(surf, cave)
            self.draw_fireballs(surf, cave)

        # Skeleton arrows
        for a in cave.arrows:
            x, y = self.on_screen(a["x"] * TILE, a["y"] * TILE)
            tail = x - 26 * (1 if a["vx"] > 0 else -1)
            yours = a.get("yours")                      # your arrows have a golden tip
            if yours and a.get("fire"):                 # ...and in Nightfall Hollow they're on fire!
                self.draw_fire_arrow(surf, (x - 36 * (1 if a["vx"] > 0 else -1), y), (x, y))
                if random.random() < 0.5:               # a trail of embers
                    self.particles.append({"x": a["x"] * TILE - 10 * caves.sign(a["vx"]), "y": a["y"] * TILE + random.uniform(-5, 5),
                                           "vx": -a["vx"] * 6, "vy": random.uniform(-50, -10), "gravity": -40,
                                           "life": 0.3, "age": 0.0, "size": random.randint(3, 5),
                                           "color": random.choice([ORANGE, YELLOW, (240, 90, 40)]), "layer": "map"})
                continue
            pygame.draw.line(surf, (200, 150, 80) if yours else (230, 220, 200), (tail, y), (x, y), 3)
            pygame.draw.circle(surf, YELLOW if yours else (255, 255, 255), (int(x), int(y)), 3)

        if cave.lava_line is not None:              # the diamond woke the lava up!
            self.draw_rising_lava(surf, cave)

        # You - blinking for a moment after you get hurt
        you = cave.you
        if you.on_ground and abs(you.x - self.walk_x) < 1:     # add up how far you walk, to move your legs
            self.walked += abs(you.x - self.walk_x)
        self.walk_x = you.x
        if (you.climbing or you.on_wall) and abs(you.y - self.climb_y) < 1:   # add up how far you climb, to move your arms
            self.climbed += abs(you.y - self.climb_y)
        self.climb_y = you.y
        if you.safe_time <= 0 or int(self.time * 16) % 2 == 0:
            if you.climbing:                            # on a ladder we see your back: your arms take turns
                step = int(self.climbed / CLIMB_STEP) % 2
                views = self.hero_views()
                art = (views.climb_view_armored if self.game.player.has_armor else views.climb_view)[step]
            else:                                       # everywhere else we see you from the side
                art = self.side_picture(you)
            if you.crawling:
                self.draw_crawling(surf, you, art)
            else:
                if you.pounding:                    # speed lines above a ground pound
                    x, y = self.on_screen((you.x + you.w / 2) * TILE, you.y * TILE)
                    for dx in (-18, -6, 6, 18):
                        pygame.draw.line(surf, (235, 235, 245), (x + dx, y - 40), (x + dx, y - 8), 3)
                facing = you.facing
                if you.climbing:                    # from behind you're never flipped (your arms take turns instead)
                    you.facing = 1
                left, top = self.draw_body(surf, you, art, flash=self.player_hit > 0)
                you.facing = facing
                if self.wall_sliding(you) and random.random() < 0.3:   # a little dust where your boots scrape the wall
                    self.burst((you.x + (you.w if you.wall_side > 0 else 0)) * TILE, (you.y + you.h) * TILE,
                               (150, 140, 130), 1, speed=50)
                if not (you.climbing or you.hanging or you.on_wall or self.wall_sliding(you)
                        or getattr(you, "swinging", None) is not None):
                    self.draw_tool(surf, you, left, top)     # (both hands are busy on a ladder or a wall)

        self.draw_particles(surf, "map", self.cam)
        self.draw_motes(surf)
        if cave.is_castle:
            self.draw_bats(surf)
        self.draw_popups(surf)
        if cave.is_throne_room:
            if cave.beaten_time is not None:
                self.draw_light_coming_back(surf, cave)
            self.draw_king_bar(surf, cave)

    def draw_crawling(self, surf, you, art):
        """Crawling: the Hero, squashed down low."""
        image = self.cave_sprite(art, flip=you.facing < 0)
        if self.player_hit > 0:
            image = whiten(image)
        w, h = image.get_size()
        low = pygame.transform.scale(image, (w + 10, int(h * 0.58)))
        x, y = self.on_screen((you.x + you.w / 2) * TILE, (you.y + you.h) * TILE)
        wiggle = math.sin(self.time * 16) * 2 if abs(you.vx) > 0.3 else 0
        surf.blit(low, low.get_rect(midbottom=(x + wiggle, y + art_bottom(art) * phase2.art_pixel(art, CAVE_SCALE) * 0.58)))

    def wall_sliding(self, you):
        """Sliding down a climbing wall (holding toward it while you fall)?"""
        return you.wall_time > 0 and you.vy > 0 and not (you.on_ground or you.on_wall or you.pounding or you.hanging)

    def hero_views(self):
        """The Hero's side, ladder and wall pictures: the ones load_art made, or Phase 2's 32 x 32 ones."""
        return phase2.hero_views(self) or self

    def side_picture(self, you):
        """Which side-view picture of you to draw: walking, jumping, falling or standing still."""
        views = self.hero_views()
        if you.pounding:
            name = "jump"                               # a ground pound: knees tucked
        elif you.hanging or getattr(you, "swinging", None) is not None:
            name = "fall"                               # hanging from a ledge (or a swinging vine): legs dangling
        elif you.on_wall:                               # on a climbing wall: hand over hand as you go
            if you.vy:
                step = int(self.climbed / WALL_STEP) % 4
                name = ["reach 1", "hold", "reach 2", "hold"][step]
            else:
                name = "hold"                           # holding still
            return (views.wall_view_armored if self.game.player.has_armor else views.wall_view)[name]
        elif self.wall_sliding(you):                    # sliding down a climbing wall, gripping it
            return (views.wall_view_armored if self.game.player.has_armor else views.wall_view)["slide"]
        elif not you.on_ground:
            name = "jump" if you.vy < 0 else "fall"     # going up: knees tucked. Coming down: legs stretched
        elif abs(you.vx) > 0.5:                         # walking (or crawling): a new picture every WALK_STEP blocks
            step = int(self.walked / WALK_STEP) % 4
            name = ["step 1", "pass 1", "step 2", "pass 2"][step]
        else:
            name = "stand"
        if self.game.player.has_armor:
            return views.side_view_armored[name]
        return views.side_view[name]

    def draw_motes(self, surf):
        """Embers rising in a lava cave, sparkles drifting in a crystal cave, fireflies in a mossy one."""
        if not self.theme["motes"]:
            return
        colors, how = self.theme["motes"]
        cam_x, cam_y = self.cam
        if len(self.motes) < 50 and random.random() < 0.5:
            y = cam_y + (VIEW_H + 10 if how == "rise" else random.uniform(0, VIEW_H))
            self.motes.append({"x": cam_x + random.uniform(0, VIEW_W), "y": y, "age": 0.0, "life": random.uniform(2, 4),
                               "vx": random.uniform(-12, 12), "vy": {"rise": -50, "drift": 8, "wander": 0}[how],
                               "color": random.choice(colors)})
        for m in self.motes:
            m["age"] += 1 / 60
            if how == "wander":
                m["vx"] += random.uniform(-6, 6); m["vy"] += random.uniform(-6, 6)
            m["x"] += m["vx"] / 60
            m["y"] += m["vy"] / 60
            fade = min(1.0, m["age"] * 2, (m["life"] - m["age"]) * 2)
            if fade > 0 and (how != "wander" or int(m["age"] * 3 + m["x"]) % 3):
                surf.blit(self.mote_dot(m["color"], fade), (m["x"] - cam_x, m["y"] - cam_y))
        self.motes = [m for m in self.motes if m["age"] < m["life"]]

    def draw_tool(self, surf, you, left, top):
        """Your pickaxe (or sword) in your hand. It swings when you press R."""
        tool = you.tool if you.swing > 0 else ("pickaxe" if self.game.player.pickaxe else None)
        if tool not in self.held:
            return
        # How each tool rests in his hand: 0 = as it's drawn in sprites.py, minus = tipped forward.
        # They point forward, low, so you can still see his face.
        resting = {"pickaxe": -70, "sword": -40, "sunfang": -40, "bow": 0}[tool]
        if tool == "bow":
            angle = 0                                   # holding the bow up to shoot
        elif you.swing > 0:
            t = 1 - you.swing / caves.SWING_TIME
            angle = lerp(85, -115, t / 0.45) if t < 0.45 else lerp(-115, resting, (t - 0.45) / 0.55)
        else:
            angle = resting + math.sin(self.time * 2) * 3
        image = self.held[tool]
        if you.facing < 0:
            image = pygame.transform.flip(image, True, False)
            angle = -angle
            hand = (left + 6 * CAVE_SCALE, top + 11.5 * CAVE_SCALE)     # his front hand in the side pictures
        else:
            hand = (left + 10 * CAVE_SCALE, top + 11.5 * CAVE_SCALE)
        turned = pygame.transform.rotate(image, angle)
        if tool == "sunfang":                               # Sunfang shines like the sun (brighter with light shards)
            sun = self.shard_suns[min(self.game.player.light_shards, len(self.shard_suns) - 1)]
            surf.blit(sun, sun.get_rect(center=hand))
        if tool in ("sword", "sunfang") and self.game.player.ring_hits:   # the diamond ring makes your sword glow
            surf.blit(self.gem_glow, self.gem_glow.get_rect(center=hand))
        surf.blit(turned, turned.get_rect(center=hand))

    def draw_lava(self, surf, x, y, c, deep=False):
        """A pool of lava sunk into the floor: its top is a little lower than the rock around it.
        deep=True is a block of lava with more lava on top of it: the deep part of a pool, all lava, no top."""
        if deep:
            self.draw_deep_lava(surf, x, y, c)
            return
        if self.game.cave.theme in CAVE_COLORS and not self.game.cave.is_castle:   # in chunky pixels
            self.draw_chunky_lava(surf, x, y, c)
            return
        top = y + int(TILE * caves.HAZARD_TOP["~"])
        if self.game.cave.is_castle:
            surf.blit(self.lava_glow, self.lava_glow.get_rect(center=(x + TILE // 2, top)))
        else:                                       # the far side of the pool: dark rock, lit up near the lava
            rim = tuple(max(0, v - 34) for v in self.theme["rock"])
            surf.fill(rim, (x, y, TILE, top - y))
            surf.fill(tuple(int(lerp(v, hot, 0.35)) for v, hot in zip(rim, (230, 90, 30))), (x, top - 8, TILE, 8))
            self.lava_lights.append((x + TILE // 2, top))    # its warm light is drawn after all the blocks
        wave = int(math.sin(self.time * 3 + c * 0.8) * 3)
        surf.fill((230, 80, 20), (x, top + wave, TILE, y + TILE - top - wave))
        surf.fill((255, 170, 50), (x, top + wave, TILE, 6))
        t = (self.time * 0.8 + c * 0.37) % 1.0                  # a bubble rising and popping
        if t < 0.6:
            pygame.draw.circle(surf, (255, 200, 90), (x + 16 + (c * 13) % 32, int(y + TILE - 8 - t * 30)), 3)

    def draw_deep_lava(self, surf, x, y, c):
        """Deep down in a pool: the same color as the bottom of the lava above, so the pool looks like one,
        with hot blobs drifting slowly along."""
        chunky_look = self.game.cave.theme in CAVE_COLORS and not self.game.cave.is_castle
        surf.fill(DEEP_LAVA if chunky_look else (230, 80, 20), (x, y, TILE, TILE))
        blob = (214, 66, 24) if chunky_look else (255, 140, 40)
        for i in range(2):
            bx = (int(self.time * (6 + i * 4)) * ART_PIXEL + c * 23 + i * 29) % TILE // ART_PIXEL * ART_PIXEL
            surf.fill(blob, (x + bx, y + ART_PIXEL * (3 + i * 6), min(2 * ART_PIXEL, TILE - bx), ART_PIXEL))

    def draw_rising_lava(self, surf, cave):
        """Lava rising up from the floor, covering everything below its top. Climb!"""
        if cave.theme in CAVE_COLORS and not cave.is_castle:     # in chunky pixels, like the lava pools
            self.draw_chunky_rising_lava(surf, cave)
            return
        cam_x, cam_y = self.cam
        top = int(cave.lava_line * TILE) - cam_y
        if top >= VIEW_H:
            return
        if cave.lava_wait > 0:                      # about to rise: it bubbles and glows
            top += int(math.sin(self.time * 18) * 3)
        surf.blit(self.pool_glow, self.pool_glow.get_rect(center=(VIEW_W // 2, top)))
        for x in range(0, VIEW_W, 8):
            wave = int(math.sin(self.time * 3 + (x + cam_x) * 0.04) * 4)
            surf.fill((230, 80, 20), (x, top + wave, 8, VIEW_H - top - wave))
            surf.fill((255, 170, 50), (x, top + wave, 8, 6))
        for i in range(12):                         # bubbles rising and popping
            t = (self.time * 0.9 + i * 0.37) % 1.0
            bx = (i * 97 - cam_x // 2) % VIEW_W
            pygame.draw.circle(surf, (255, 200, 90), (bx, int(top + 40 - t * 34)), 4)

    def draw_fire(self, surf, x, y, c):
        """A fire on the floor: flickering flames on burning logs. Jump over it!"""
        base = y + TILE - 6                                    # where the logs are
        middle = x + TILE // 2
        surf.blit(self.fire_glow, self.fire_glow.get_rect(center=(middle, base - 14)))
        pygame.draw.line(surf, (70, 40, 26), (x + 12, base + 4), (x + 52, base - 2), 7)    # two logs, crossed
        pygame.draw.line(surf, (92, 54, 32), (x + 12, base - 2), (x + 52, base + 4), 7)
        # three flames (the middle one is the biggest), each flickering in its own way
        for i, (dx, size) in enumerate(((-11, 0.7), (11, 0.75), (0, 1.0))):
            flicker = math.sin(self.time * (11 + 3 * i) + c * 1.7 + i * 2) * 0.12 + math.sin(self.time * 23 + i + c) * 0.06
            lean = int(math.sin(self.time * 6 + i + c) * 3)
            for color, shrink in (((235, 80, 30), 1.0), ((255, 160, 40), 0.66), ((255, 236, 150), 0.34)):
                h, w = 32 * size * shrink * (1 + flicker), 22 * size * shrink
                left, bottom = middle + dx - w / 2, base + 2
                pygame.draw.ellipse(surf, color, (left, bottom - h * 0.55, w, h * 0.55))
                pygame.draw.polygon(surf, color, [(left, bottom - h * 0.3), (middle + dx + lean, bottom - h),
                                                  (left + w, bottom - h * 0.3)])
        for i in range(3):                                     # sparks flying up
            t = (self.time * 1.1 + i / 3 + c * 0.31) % 1.0
            if t < 0.8:
                surf.fill((255, 200, 80), (middle + math.sin(t * 7 + i * 2 + c) * 10, base - 22 - t * 30, 3, 3))

    def draw_gate(self, surf, x, y, opened):
        """An iron gate: black bars with sharp tips. A lever (L) pulls them up into the rock."""
        dark, light = (40, 40, 52), (128, 128, 150)
        drop = 12 if opened else TILE                    # opened: only the tips poke down from above
        for i in range(5):
            bx = x + 6 + i * 12
            surf.fill(dark, (bx, y, 6, drop))
            surf.fill(light, (bx + 1, y, 2, drop))
            tip = y + drop
            pygame.draw.polygon(surf, dark, [(bx - 1, tip), (bx + 7, tip), (bx + 3, tip + 7)])
        if not opened:
            for bar_y in (y + 14, y + 42):               # two crossbars, with rivets
                surf.fill(dark, (x + 3, bar_y, TILE - 6, 6))
                surf.fill(light, (x + 3, bar_y, TILE - 6, 2))

    def draw_jet(self, surf, cave, x, y, r, c):
        """A flame jet: an iron nozzle in the floor. It fizzles... then FWOOSH, fire shoots up!"""
        if cave.traps_up():
            fx, fy, fw, fh = cave.flame(r, c)
            top, bottom = y + (fy - r) * TILE, y + TILE - 10
            middle = x + TILE // 2
            surf.blit(self.fire_glow, self.fire_glow.get_rect(center=(middle, (top + bottom) // 2)))
            for color, width in (((235, 80, 30), 40), ((255, 160, 40), 28), ((255, 236, 150), 14)):
                for i in range(10):                      # a column of flickering flame blobs
                    t = i / 9
                    wobble = math.sin(self.time * 19 + i * 1.3 + c) * 4 * t
                    w = width * (1 - 0.5 * t) * (1 + 0.12 * math.sin(self.time * 31 + i))
                    cy = bottom - t * (bottom - top)
                    pygame.draw.ellipse(surf, color, (middle - w / 2 + wobble, cy - 22, w, 44))
        elif cave.about_to_go_off():                     # about to fire: sparks spit out of the nozzle
            for i in range(4):
                surf.fill((255, 200, 80), (x + 26 + random.randint(-8, 8), y + TILE - 16 - random.randint(0, 14), 3, 3))
        surf.fill((40, 38, 48), (x + 10, y + TILE - 18, TILE - 20, 18))      # the nozzle
        surf.fill((130, 126, 146), (x + 12, y + TILE - 16, TILE - 24, 4))
        surf.fill((255, 120, 40), (x + 22, y + TILE - 18, TILE - 44, 3))     # a hot glow in its hole

    def draw_geyser(self, surf, cave, x, y, c):
        """A steam geyser: a hole in the rock. It hisses a little... then WHOOSH, a tall puff of steam!"""
        pygame.draw.ellipse(surf, (30, 26, 34), (x + 14, y - 2, TILE - 28, 12))     # the hole on top
        pygame.draw.ellipse(surf, (90, 84, 100), (x + 14, y - 2, TILE - 28, 12), 2)
        if cave.traps_up():
            puffs, height = 10, TILE * 6
        elif cave.about_to_go_off():
            puffs, height = 3, 30
        else:
            return
        if puffs > 3:
            puffs = 18
        for i in range(puffs):
            t = (self.time * 2.2 + i / puffs) % 1.0
            px = x + 32 + math.sin(self.time * 5 + i * 2 + c) * (4 + 12 * t)
            py = y - t * height
            radius = int(10 + 20 * t) if puffs > 3 else 5
            pygame.draw.circle(surf, (196, 200, 212), (int(px), int(py)), radius + 2)
            pygame.draw.circle(surf, (240, 242, 248), (int(px), int(py)), radius)

    def draw_platforms(self, surf, cave):
        """Moving platforms: ledges that slide along, with little arrows showing which way they go."""
        cam_x, cam_y = self.cam
        plank = self.cave_ledges[0] if self.cave_ledges else self.ledge
        for platform in cave.platforms:
            px, py = platform.where(cave.clock)
            left, top = int(px * TILE) - cam_x, int(py * TILE) - cam_y
            if left > VIEW_W or top > VIEW_H or left + platform.w * TILE < 0 or top + TILE < 0:
                continue
            for i in range(platform.w):
                surf.blit(plank, (left + i * TILE, top))
            middle = left + platform.w * TILE // 2
            base = top + 22
            surf.fill((70, 56, 40), (left + 4, base, platform.w * TILE - 8, 6))   # the beam underneath
            if not platform.moves():                      # too short a track: it stays put, so no arrows
                continue
            if platform.axis == "x":                      # < > : it slides side to side
                pygame.draw.polygon(surf, YELLOW, [(middle - 16, base + 3), (middle - 8, base - 3), (middle - 8, base + 9)])
                pygame.draw.polygon(surf, YELLOW, [(middle + 16, base + 3), (middle + 8, base - 3), (middle + 8, base + 9)])
            else:                                          # up and down
                pygame.draw.polygon(surf, YELLOW, [(middle - 6, base - 1), (middle, base - 8), (middle + 6, base - 1)])
                pygame.draw.polygon(surf, YELLOW, [(middle - 6, base + 7), (middle, base + 14), (middle + 6, base + 7)])

    def draw_swings(self, surf, cave):
        """Swinging vines (R): a leafy vine tied on under the rock, swinging from there."""
        cam_x, cam_y = self.cam
        look = CAVE_COLORS.get(cave.theme, {}).get("vine") or SWING_VINE_COLORS.get(cave.theme, SWING_VINE_COLORS["stone"])
        stem, leaf, new_leaf = look
        dark = tuple(v * 2 // 3 for v in stem)
        for swing in getattr(cave, "swings", ()):
            ax, ay = swing.x * TILE - cam_x, swing.y * TILE - cam_y
            reach = swing.length * TILE
            if ax + reach < 0 or ax - reach > VIEW_W or ay > VIEW_H or ay + reach < 0:
                continue
            dx, dy = math.sin(swing.angle), math.cos(swing.angle)
            tip = (ax + dx * reach, ay + dy * reach)
            pygame.draw.line(surf, dark, (ax, ay), tip, 9)
            pygame.draw.line(surf, stem, (ax, ay), tip, 5)
            steps = max(1, int(swing.length * 3))
            for i in range(1, steps + 1):               # leaves, one on each side in turn
                along = i / steps * reach - 6
                x, y = ax + dx * along, ay + dy * along
                side = 1 if i % 2 else -1
                lx, ly = x + dy * 9 * side, y - dx * 9 * side
                pygame.draw.ellipse(surf, leaf, (lx - 7, ly - 4, 14, 8))
                surf.fill(new_leaf, (lx - 2, ly - 2, 4, 2))
            pygame.draw.circle(surf, leaf, (int(tip[0]), int(tip[1])), 6)       # a bunch of leaves at the end
            pygame.draw.circle(surf, new_leaf, (int(tip[0]) - 2, int(tip[1]) - 2), 2)
            pygame.draw.ellipse(surf, dark, (ax - 11, ay - 4, 22, 12))          # where it's tied on
            pygame.draw.ellipse(surf, leaf, (ax - 8, ay - 3, 16, 8))

    def draw_exit_door(self, surf, x, y):
        pulse = 0.5 + 0.5 * math.sin(self.time * 3)
        surf.blit(self.door_glow, self.door_glow.get_rect(center=(x + 32, y + 34)))
        pygame.draw.rect(surf, (96, 62, 34), (x + 8, y + 4, 48, 60),
                         border_top_left_radius=22, border_top_right_radius=22)
        pygame.draw.rect(surf, (255, 226, int(130 + 60 * pulse)), (x + 15, y + 11, 34, 53),
                         border_top_left_radius=16, border_top_right_radius=16)
        self.text(surf, "EXIT", (x + 32, y - 2), 22, YELLOW, "midbottom", shadow=True)

    def draw_water(self, surf, x, y, r, c):
        for i in range(3):
            yy = y + 14 + i * 18
            shift = math.sin(self.time * 2 + c * 0.9 + r * 0.7 + i) * 6
            x0 = x + 10 + shift + (i % 2) * 14
            pygame.draw.line(surf, (70, 60, 120) if self.game.world == 2 else (120, 172, 240), (x0, yy), (x0 + 18, yy), 2)

    def draw_bubbles(self, surf, x, y, c):
        """Bubbles rising over a sunken chest, and a glint of gold under the water."""
        for i in range(4):
            t = (self.time * 0.6 + i * 0.25 + c * 0.1) % 1.0
            bx = x + 22 + i * 7 + math.sin(self.time * 3 + i) * 3
            by = y + 52 - t * 40
            pygame.draw.circle(surf, (214, 238, 255), (int(bx), int(by)), 2 + i % 2, 1)
        if int(self.time * 2 + c) % 3 == 0:
            surf.fill((255, 214, 90), (x + 30, y + 44, 4, 2))

    def draw_steam(self, surf, x, y, c):
        """A steam vent: a big puff on the turns it blows, and a little wisp the turn before, as a warning."""
        game = self.game
        if game.vent_puffing():
            puffs, height = 5, 46
        elif game.vent_puffing(game.turn + 1):
            puffs, height = 2, 14
        else:
            return
        for i in range(puffs):
            t = (self.time * 1.5 + i / puffs) % 1.0
            px = x + 32 + math.sin(self.time * 4 + i * 2 + c) * (3 + 6 * t)
            py = y + 40 - t * height
            radius = int(3 + 7 * t * (puffs / 5))
            pygame.draw.circle(surf, (238, 238, 242), (int(px), int(py)), max(2, radius))

    def draw_portal(self, surf, x, y):
        cx, cy = x + 32, y + 35
        is_open = self.game.portal_open
        if is_open:
            pulse = 1 + 0.15 * math.sin(self.time * 4)
            glow = pygame.transform.smoothscale(self.glow, (int(64 * pulse), int(64 * pulse)))
            surf.blit(glow, glow.get_rect(center=(cx, cy)))
        count = 8
        for i in range(count):
            angle = self.time * (3.0 if is_open else 0.7) + i * 2 * math.pi / count
            radius = 18 + (math.sin(self.time * 3 + i) * 3 if is_open else 0)
            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius * 0.55
            if is_open:
                color = (210, 100, 255) if i % 2 else (100, 230, 255)
            else:
                color = (124, 104, 156)
            pygame.draw.circle(surf, color, (int(px), int(py)), 4 if is_open else 3)

    def draw_particles(self, surf, layer, camera=(0, 0)):
        for p in self.particles:
            if p.get("layer", "map") == layer:
                size = p["size"]
                x, y = int(p["x"]) - camera[0], int(p["y"]) - camera[1]
                surf.fill(p["color"], (x - size // 2, y - size // 2, size, size))

    # ----- drawing: side panel and message log ------------------------------------

    def draw_panel(self):
        if phase2.draw_panel(self):         # Phase 2 has a panel of its own (phase2/draw_hud.py)
            return
        game, p = self.game, self.game.player
        x0 = VIEW_W
        s = self.screen
        s.fill(PANEL_BG, (x0, 0, PANEL_W, HEIGHT))
        pygame.draw.line(s, (60, 64, 90), (x0, 0), (x0, HEIGHT), 2)
        x = x0 + 18
        right = x0 + PANEL_W - 18

        self.text(s, p.name, (x, 16), 38, YELLOW, shadow=True)
        level = self.text(s, "Level %d" % p.level, (right, 22), 26, TEXT, "topright")
        lives = self.text(s, "x%d" % p.lives, (level.x - 14, 22), 26, (255, 120, 130), "topright")   # your lives
        s.blit(self.art["heart"], (lives.x - self.art["heart"].get_width() - 2, 18))
        self.panel_spots["lives"] = lives.union(pygame.Rect(lives.x - 30, 18, 30, 26))

        y = 60
        s.blit(self.art["heart"], (x, y))
        self.health_bar(s, (x + 32, y + 4, 150, 16), p)
        armor_text = self.text(s, "+%d" % p.armor, (right, y + 3), 24, ARMOR_COLOR, "topright") if p.has_armor else None
        self.text(s, "%d/%d" % (p.health, p.max_health), (armor_text.x - 4 if armor_text else right, y + 3), 24, TEXT, "topright")
        y += 30
        s.blit(self.art["star"], (x, y))
        self.bar(s, (x + 32, y + 6, 170, 12), p.xp / p.xp_needed, YELLOW)
        self.text(s, "%d/%d XP" % (p.xp, p.xp_needed), (right, y + 4), 20, DIM, "topright")
        y += 22
        said = self.text(s, "Powers:", (x, y), 20, DIM)       # the powers you picked when you leveled up
        powers = self.powers_text(p)
        self.text(s, self.fit(powers or "none yet", 20, right - said.right - 6), (said.right + 6, y), 20,
                  YELLOW if powers else DIM)

        y += 22
        self.text(s, "PACK", (x, y), 22, DIM)
        y += 22
        if p.sunfang:
            s.blit(self.art["sunfang"], (x, y))
            self.text(s, "Sunfang", (x + 34, y + 4), 24, YELLOW)
        else:
            s.blit(self.art["sword"], (x, y))
            self.text(s, "Swords", (x + 34, y + 4), 24)
        if p.ring_hits:                                  # a diamond ring on your sword
            s.blit(self.art["ring"], (x + 112, y))
            self.text(s, "x%d" % p.ring_hits, (x + 138, y + 4), 22, WATER_BLUE)
        if p.sunfang:
            self.text(s, "+%d!" % rules.PERFECT_BONUS if p.sunfang_perfect else "never breaks", (right, y + 4), 20,
                      YELLOW if p.sunfang_perfect else DIM, "topright")
        for i, sword in enumerate([] if p.sunfang else p.swords):     # Great swords in gold, Cracked ones in red
            color = RED if sword.low or sword.quality == "cracked" else YELLOW if sword.quality == "great" else None
            self.pips(s, right, y + 2 + i * 7, sword.durability, sword.max_durability, color)
        if not p.swords and not p.sunfang:
            self.text(s, "none!", (right, y + 4), 22, RED, "topright")
        y += 28
        s.blit(self.art["pickaxe"], (x, y))
        self.text(s, "Pickaxe", (x + 34, y + 4), 24)
        if p.pickaxe:
            self.text(s, "never breaks", (right, y + 4), 20, DIM, "topright")
        else:
            self.text(s, "none!", (right, y + 4), 22, RED, "topright")
        y += 28
        spot = lambda: pygame.Rect(x - 8, y - 1, right - x + 16, 26)     # one row of the panel, for tips
        self.panel_spots["food"] = spot()
        s.blit(self.art["apple"], (x, y))
        self.text(s, "Food", (x + 34, y + 4), 24)
        self.text(s, "%d / %d" % (p.food, p.max_food), (right, y + 4), 24, TEXT, "topright")
        y += 28
        self.panel_spots["wood"] = spot()
        s.blit(self.art["wood"], (x, y))
        self.text(s, "Wood", (x + 34, y + 4), 24)
        self.text(s, "%d / %d" % (p.wood, rules.MAX_WOOD), (right, y + 4), 24, TEXT, "topright")
        y += 28
        s.blit(self.art["boat_icon"], (x - 4, y + 8))
        self.text(s, "Boat", (x + 34, y + 4), 24)
        self.text(s, "yes" if p.has_boat else "none", (right, y + 4), 24, GREEN if p.has_boat else DIM, "topright")
        y += 28
        self.panel_spots["bow"] = spot()
        s.blit(self.art["bow"], (x, y))
        self.text(s, "Bow", (x + 34, y + 4), 24)
        if p.has_bow:
            self.text(s, "%d %sarrows" % (p.arrows, "fire " if p.fire_arrows else ""), (right, y + 4), 24,
                      (ORANGE if p.fire_arrows else TEXT) if p.arrows else RED, "topright")
        else:
            self.text(s, "none" if not p.arrows else "no bow (%d)" % p.arrows, (right, y + 4), 24, DIM, "topright")
        y += 28
        s.blit(self.art["diamond"], (x, y))
        self.text(s, "Diamonds", (x + 34, y + 4), 24)
        self.text(s, "%d" % p.diamonds, (right, y + 4), 24, (110, 215, 255), "topright")
        y += 28
        s.blit(self.art["shield"], (x, y))
        self.text(s, "Armor", (x + 34, y + 4), 24)
        if p.has_armor:
            self.text(s, "%d / %d" % (p.armor, p.max_armor), (right, y + 4), 24, ARMOR_COLOR, "topright")
        else:
            self.text(s, "none", (right, y + 4), 24, DIM, "topright")

        y += 42
        self.text(s, "QUESTS", (x, y), 22, DIM)
        y += 24
        for quest in game.quests:
            box = pygame.Rect(x, y + 1, 16, 16)
            pygame.draw.rect(s, GREEN if quest.completed else DIM, box, 2, border_radius=3)
            if quest.completed:
                pygame.draw.lines(s, GREEN, False, [(x + 3, y + 9), (x + 7, y + 13), (x + 14, y + 3)], 3)
            self.text(s, quest.description, (x + 26, y + 1), 22, GREEN if quest.completed else TEXT)
            self.text(s, "%d/%d" % (quest.progress, quest.goal_count), (right, y + 1), 22, DIM, "topright")
            y += 26
        if game.world == 2:
            if not game.castle_quest.completed:
                goal = "Castle: find it!"
            else:
                goal = "Throne room: found!" if game.throne_quest.completed else "Throne room: find it!"
                if game.cave and hasattr(game.cave, "goal") and not game.throne_quest.completed:
                    goal = game.cave.goal()             # in the castle: the key or lever of this level
                if game.cave and game.cave.is_throne_room:
                    goal = game.cave.goal()             # in the throne room: the Shadow King's health
                self.text(s, "Shards %d/%d" % (p.light_shards, len(castle.CASTLE_LEVELS)), (right, y + 2), 22,
                          (255, 236, 160), "topright")
            self.text(s, goal, (x, y + 2), 22, (210, 120, 255))
            if game.moon:
                y += 24
                self.text(s, "Moonrise! Follow the wisp" if game.wisp else "Moonrise! Stay near light",
                          (x, y + 2), 20, (170, 215, 255))
            if not p.sunfang and not game.cave:         # (in a cave there's no room: the hints need it)
                y = self.draw_sunfang_list(s, x, right, y + 28)
        else:
            portal = "OPEN - go find it!" if game.portal_open else "closed"
            self.text(s, "Portal: " + portal, (x, y + 2), 22, (210, 120, 255) if game.portal_open else DIM)

        y += 40
        self.panel_spots["here"] = pygame.Rect(x - 8, y - 5, right - x + 16, 26)
        if game.cave:
            here = "HERE: CAVE"
            if game.cave.is_castle:
                here = "HERE: CASTLE LEVEL %d/%d" % (game.cave.level + 1, len(castle.CASTLE_LEVELS)) \
                    if hasattr(game.cave, "level") else "HERE: CASTLE"
            if game.cave.is_throne_room:
                here = "HERE: THE THRONE ROOM"
            self.text(s, here, (x, y), 22, DIM)
            hints = CASTLE_HINTS if game.cave.is_castle else CAVE_HINTS
            if game.cave.is_throne_room:
                hints = THRONE_HINTS
        else:
            land = game.land_name(p.pos)
            self.text(s, "%s: %s" % (land.upper() if land else "HERE", game.tile_name(p.pos).upper()), (x, y), 22, DIM)
            hints = TILE_HINTS.get(game.here, [])
            if game.here == "W" and p.pos in game.sunken_chests:
                hints = hints + [("SPACE", "dive for the sunken chest")]
            if game.here == "F":                    # how much wood is left in this tree?
                hints = [(key, "chop wood (%d left)" % game.wood_left(p.pos) if key == "T" else words)
                         for key, words in hints]
            if game.here in "MS" and p.pos in game.cleared_mines:
                hints = [(None, "This mine is empty now")]
            elif game.here == "M" and p.pos in game.empty_mines:
                hints = hints + [(None, "No diamond in this one")]
        y += 26
        for key, words, *more in hints:
            end = self.key_box(s, key, x, y) if key else x - 8
            said = self.text(s, words, (end + 8, y + 3), 22)
            if more:                                # a second key on the same line
                end = self.key_box(s, more[0], said.right + 14, y)
                self.text(s, more[1], (end + 8, y + 3), 22)
            y += 28 if len(hints) < 7 else 26          # squeeze a long list in

        y = HEIGHT - 114
        self.text(s, "CONTROLS", (x, y), 22, DIM)
        y += 24
        end = self.key_box(s, "Arrows", x, y)
        self.text(s, "move", (end + 6, y + 3), 22)
        end = self.key_box(s, "E", x + 130, y)
        self.text(s, "eat", (end + 6, y + 3), 22)
        end = self.key_box(s, "Z", x + 200, y)
        self.text(s, "wait", (end + 6, y + 3), 22)
        y += 28
        end = self.key_box(s, "H", x, y)
        self.text(s, "help", (end + 6, y + 3), 22)
        end = self.key_box(s, "M", x + 72, y)
        self.text(s, "sound", (end + 6, y + 3), 22)
        if phase2.is_phase2(self.game):         # Phase 2: P (or Esc) opens the pause menu
            end = self.key_box(s, "P", x + 160, y)
            self.text(s, "pause", (end + 6, y + 3), 22)
        else:
            end = self.key_box(s, "Esc", x + 160, y)
            self.text(s, "title" if IN_BROWSER else "quit", (end + 6, y + 3), 22)   # a web page can't close itself
        y += 28
        end = self.key_box(s, "C", x, y)
        self.text(s, "craft", (end + 6, y + 3), 22)
        end = self.key_box(s, "F", x + 86, y)
        self.text(s, "shoot", (end + 6, y + 3), 22)
        end = self.key_box(s, "N", x + 170, y)
        self.text(s, "music", (end + 6, y + 3), 22)

    def powers_text(self, p):
        """Your level-up powers in a few words, like "+2 dmg, +4 health, Springy x2"."""
        words = []
        for name in rules.POWERS:
            times = p.power(name)
            if name == "Stronger" and times:
                words.append("+%d dmg" % p.strength_bonus)
            elif name == "Tougher" and times:
                words.append("+%d health" % (times * rules.TOUGHER_HEALTH))
            elif name == "Extra life":
                continue                          # your lives are on the panel already (the heart at the top)
            elif times:
                words.append(name if times == 1 else "%s x%d" % (name, times))
        return ", ".join(words)

    def fit(self, text, size, width):
        """Cut text short with "..." so it fits in width."""
        font = self.font(size)
        if font.size(text)[0] <= width:
            return text
        while text and font.size(text + "...")[0] > width:
            text = text[:-1]
        return text.rstrip(", ") + "..."

    def health_bar(self, surf, rect, p):
        """Your health in green (yellow, then red when it's low), and your armor in silver on the end."""
        rect = pygame.Rect(rect)
        total = p.max_health + (p.max_armor if p.has_armor else 0)
        pygame.draw.rect(surf, (58, 60, 82), rect, border_radius=rect.h // 2)
        if p.health > 0:
            fill = rect.copy()
            fill.w = max(rect.h, int(rect.w * p.health / total))
            pygame.draw.rect(surf, self.health_color(p.health / p.max_health), fill, border_radius=rect.h // 2)
        if p.has_armor:
            start = rect.x + int(rect.w * p.max_health / total)
            pygame.draw.rect(surf, ARMOR_COLOR, (start, rect.y, max(rect.h, int(rect.w * p.armor / total)), rect.h),
                             border_radius=rect.h // 2)
            pygame.draw.line(surf, (40, 40, 60), (start, rect.y), (start, rect.bottom - 1), 2)

    def draw_sunfang_list(self, s, x, right, y):
        """The Sunfang checklist: the Blade, the Hilt, the Sun Gem and the Beacons. Returns where to carry on."""
        game, p = self.game, self.game.player
        self.text(s, "SUNFANG", (x, y), 22, DIM)
        y += 24
        rows = [("Blade", min(p.diamonds, rules.SUNFANG_DIAMONDS), rules.SUNFANG_DIAMONDS),
                ("Hilt", int(p.has_hilt), 1),
                ("Sun Gem", min(p.sun_shards, rules.SUN_SHARDS_NEEDED), rules.SUN_SHARDS_NEEDED),
                ("Beacons", len(game.beacons), rules.BEACONS_NEEDED)]
        for name, have, need in rows:
            done = have >= need
            box = pygame.Rect(x, y + 1, 16, 16)
            pygame.draw.rect(s, GREEN if done else DIM, box, 2, border_radius=3)
            if done:
                pygame.draw.lines(s, GREEN, False, [(x + 3, y + 9), (x + 7, y + 13), (x + 14, y + 3)], 3)
            self.text(s, name, (x + 26, y + 1), 22, GREEN if done else TEXT)
            if need > 1:
                self.text(s, "%d/%d" % (have, need), (right, y + 1), 22, DIM, "topright")
            y += 24
        return y - 22

    def draw_minimap(self, x, top, width, bottom, show_view=True):
        """A tiny map of the places you have found. The box shows what's on screen."""
        if phase2.draw_minimap(self, x, top, width, bottom, show_view):     # Phase 2's big world
            return
        game, s = self.game, self.screen
        size = min(width // game.cols, (bottom - top - 22) // game.rows)
        if size < 2:
            return                          # no room for a map
        self.text(s, "MAP", (x, top), 22, DIM)
        y0 = top + 22
        s.fill((14, 14, 24), (x, y0, game.cols * size, game.rows * size))
        for r, c in game.seen:
            colors = NIGHT_MINIMAP_COLORS if game.world == 2 else MINIMAP_COLORS
            color = colors.get(game.map[r][c], DIM)
            if game.map[r][c] in "MS" and game.world == 1:     # a Mine's dot is the color of its rock
                color = MINE_LOOKS.get(self.mine_theme((r, c)), MINE_LOOKS["stone"])["rock"]
            if game.map[r][c] == "G" and self.land_of.get((r, c)) in LAND_GROUND:   # snow, red sand...
                color = LAND_GROUND[self.land_of[(r, c)]][0]
            if (r, c) in game.glints and (r, c) not in game.cleared_mines:          # a Mine that sparkled
                color = (120, 235, 255)
            s.fill(color, (x + c * size, y0 + r * size, size, size))
        if show_view:
            cam_box = pygame.Rect(x + self.cam[0] * size // TILE, y0 + self.cam[1] * size // TILE,
                                  VIEW_W * size // TILE, VIEW_H * size // TILE)
            pygame.draw.rect(s, (230, 232, 244), cam_box, 1)
        if int(self.time * 3) % 2 == 0:
            r, c = game.player.pos
            s.fill(YELLOW, (x + c * size - 1, y0 + r * size - 1, size + 2, size + 2))

    def pips(self, surf, right, y, value, maximum, color=None):
        """Little marks for how many more hits (or digs) a tool has left, lined up on the right."""
        gap = 12 if maximum <= 6 else 10 if maximum <= 16 else 6       # a Great sword's 24 pips squeeze in
        x = right - maximum * gap + 2
        for i in range(maximum):
            fill = (color or (215, 220, 230)) if i < value else (70, 72, 96)
            surf.fill(fill, (x + i * gap, y, gap - (3 if gap > 6 else 2), 5))

    def draw_log(self):
        if phase2.draw_log(self):           # Phase 2 has a message box of its own (phase2/draw_hud.py)
            return
        s = self.screen
        s.fill(LOG_BG, (0, VIEW_H, VIEW_W, LOG_H))
        pygame.draw.line(s, (60, 64, 90), (0, VIEW_H), (VIEW_W, VIEW_H), 2)
        lines = []
        recent = self.game.messages[-6:]
        for i, (message, kind) in enumerate(recent):
            newest = i == len(recent) - 1
            color = KIND_COLORS.get(kind, TEXT)
            if not newest:
                color = tuple(int(lerp(ch, 40, 0.35)) for ch in color)
            for line in self.wrap(message, 24, VIEW_W - 40 - (0 if self.game.cave else 180)):
                lines.append((line, color))
        lines = lines[-5:]
        y = VIEW_H + 12
        for line, color in lines:
            self.text(s, line, (20, y), 24, color)
            y += 23
        if not self.game.cave:
            self.draw_minimap(VIEW_W - 166, VIEW_H + 4, 150, VIEW_H + LOG_H - 2)

    def draw_banner(self):
        age = self.banner["age"]
        alpha = int(255 * min(1.0, age * 4, (2.2 - age) * 2))
        scale = 1 + max(0.0, 0.3 - age) * 2
        self.text(self.screen, self.banner["text"], (VIEW_W // 2, VIEW_H // 2 - 30), int(90 * scale),
                  YELLOW, "center", shadow=True, alpha=alpha)
        self.text(self.screen, self.banner["sub"], (VIEW_W // 2, VIEW_H // 2 + 30), 36,
                  TEXT, "center", shadow=True, alpha=alpha)

    # ----- drawing: tip bubbles ---------------------------------------------------

    def paint_under_tip(self):
        """When a tip opens: make everything dim except the thing it's about, and keep that picture.
        (The game is paused, so it doesn't change. Painting it once keeps the web version fast.)"""
        s, bubble = self.screen, self.bubble
        spot = self.tip_target(bubble["where"]) or pygame.Rect(VIEW_W // 2 - 32, VIEW_H // 2 - 32, TILE, TILE)
        room = 6 if bubble["where"][0] == "panel" else 20   # a little room around it (a panel row has its own)
        bubble["hole"] = hole = spot.inflate(room, room).clip(s.get_rect())
        keep = s.subsurface(hole).copy()                  # keep the thing it's about bright...
        s.fill(TIP_DIM, special_flags=pygame.BLEND_MULT)  # ...make everything darker...
        s.blit(keep, hole)                                # ...and put it back
        self.tip_frame = s.copy()

    def draw_tip(self):
        """The tip bubble, and a glowing ring around the thing it's about."""
        s, hole = self.screen, self.bubble["hole"]
        glow = int(4 + 3 * math.sin(self.time * 6))
        pygame.draw.rect(s, YELLOW, hole.inflate(glow, glow), 3, border_radius=12)
        picture, off_button = self.tip_picture(self.bubble["name"])
        box, tail = self.place_bubble(picture.get_size(), hole)
        s.blit(picture, box)
        pygame.draw.polygon(s, TIP_BG, tail)              # the tail covers the bubble's edge where they join
        pygame.draw.lines(s, YELLOW, False, tail, 3)
        self.tip_off_button = off_button.move(box.topleft)

    def tip_picture(self, name):
        """A tip's bubble, painted once and kept. Also says where "no more tips" is on it, for clicks."""
        words = phase2.tip_words(self.game, name, tutorial.TIPS[name])     # (Phase 2 names its own keys)
        if (name, words) not in self.tip_pictures:
            lines = self.wrap(words, 28, TIP_W - 40)
            picture = pygame.Surface((TIP_W, 96 + 28 * len(lines)), pygame.SRCALPHA)   # see-through corners
            pygame.draw.rect(picture, TIP_BG, picture.get_rect(), border_radius=16)
            pygame.draw.rect(picture, YELLOW, picture.get_rect(), 3, border_radius=16)
            picture.blit(self.art["star"], (16, 9))
            self.text(picture, "TIP", (48, 14), 26, YELLOW)
            y = 44
            for line in lines:
                self.text(picture, line, (20, y), 28, TEXT)
                y += 28
            y += 12
            end = self.key_box(picture, "ENTER", 20, y)
            said = self.text(picture, "OK", (end + 8, y + 3), 22)
            end = self.key_box(picture, "S", said.right + 36, y)
            said = self.text(picture, "no more tips", (end + 8, y + 3), 22, DIM)
            self.tip_pictures[name, words] = (picture, pygame.Rect(end - 30, y - 6, said.right - end + 38, 34))
        return self.tip_pictures[name, words]

    def place_bubble(self, size, hole):
        """Where a bubble goes: above the thing (or below it, if there's no room), or to the left of
        the side panel. Returns its box, and its tail: two corners on the box and the point by the thing."""
        box, gap = pygame.Rect((0, 0), size), 26
        if hole.left >= VIEW_W:                           # a row of the side panel
            box.midright = (hole.left - gap, hole.centery)
            box.clamp_ip(self.screen.get_rect().inflate(-16, -16))
            y = min(max(hole.centery, box.top + 30), box.bottom - 30)
            return box, [(box.right - 4, y - 14), (hole.left - 3, hole.centery), (box.right - 4, y + 14)]
        box.midbottom = (hole.centerx, hole.top - gap)
        above = box.top >= 8
        if not above:
            box.midtop = (hole.centerx, hole.bottom + gap)
        box.clamp_ip(self.view.get_rect().inflate(-16, -16))
        x = min(max(hole.centerx, box.left + 30), box.right - 30)
        if above:
            return box, [(x - 14, box.bottom - 4), (hole.centerx, hole.top - 3), (x + 14, box.bottom - 4)]
        return box, [(x - 14, box.top + 4), (hole.centerx, hole.bottom + 3), (x + 14, box.top + 4)]

    # ----- drawing: pop-up screens ---------------------------------------------------

    def draw_battle_sword(self, surf, p, left, top):
        """Your sword (or Sunfang) in your hand in a map fight, if you have one. It swings when you attack."""
        tool = "sunfang" if p.sunfang else ("sword" if p.swords else None)
        if tool is None:
            return
        resting = 10                        # held up and forward, ready to fight
        if self.lunge > 0:                  # Attack: a big swing down, then back to resting
            t = 1 - self.lunge / 0.25
            angle = lerp(85, -115, t / 0.45) if t < 0.45 else lerp(-115, resting, (t - 0.45) / 0.55)
        else:
            angle = resting + math.sin(self.time * 2) * 3
        hand = (left + 10 * 8, top + 11.5 * 8)          # his front hand in the big picture
        big = phase2.hero_fight(self, p.has_armor)      # (Phase 2: the hand of the 32 x 32 Hero)
        if big:
            hand = (left + big[1][0], top + big[1][1])
        turned = pygame.transform.rotate(self.battle_held[tool], angle)
        if p.ring_hits:                                 # the diamond ring makes your sword glow
            surf.blit(self.gem_glow, self.gem_glow.get_rect(center=hand))
        surf.blit(turned, turned.get_rect(center=hand))

    def draw_battle(self):
        battle = self.game.battle
        if battle is None:
            return
        m, p = battle.monster, self.game.player
        s = self.screen
        box = self.battle_box
        self.dim_screen(170)
        self.panel_box(box, RED if not battle.over else YELLOW)
        self.text(s, "A wild %s appears!" % m.kind, (box.centerx, box.y + 20), 44, YELLOW, "midtop", shadow=True)

        # The player (left)
        px, py = self.battle_spot("player")
        px += math.sin(self.lunge / 0.25 * math.pi) * 40 if self.lunge > 0 else 0
        sprite = self.art["player_big_armor" if p.has_armor else "player_big"]
        big = phase2.hero_fight(self, p.has_armor)      # Phase 2: the Hero at 32 x 32, just as big
        if big:
            sprite = big[0]
        if self.player_hit > 0:
            sprite = whiten(sprite)
            px += random.uniform(-6, 6)
        s.blit(pygame.transform.scale(self.shadow, (110, 22)), (px + 9, py + 118))
        bob = math.sin(self.time * 4) * 3
        s.blit(sprite, (px, py + bob))
        self.draw_battle_sword(s, p, px, py + bob)
        self.text(s, p.name, (px + 64, py + 146), 28, TEXT, "midtop")
        self.health_bar(s, (px - 6, py + 172, 140, 14), p)
        armor = "  +%d armor" % p.armor if p.has_armor else ""
        self.text(s, "%d/%d%s" % (p.health, p.max_health, armor), (px + 64, py + 190), 22, DIM, "midtop")
        if m.special == "drowns" and not battle.over:      # out on the water, in your boat
            boat = pygame.transform.scale(self.art["boat"], (128, 40))
            s.blit(boat, (px, py + 100 + math.sin(self.time * 3) * 3))

        # The monster (right)
        mx, my = self.battle_spot("monster")
        if not (battle.over and battle.result in ("won", "exploded")):
            sprite = pygame.transform.flip(self.monster_sprite(m.base_kind, 8, m.shadow), True, False)
            if self.monster_hit > 0:
                sprite = whiten(sprite)
                mx += random.uniform(-8, 8)
            if battle.fuse is not None and battle.fuse <= 1 and int(self.time * 8) % 2 == 0:
                sprite = whiten(sprite)       # an Ember Skull about to blow!
            s.blit(pygame.transform.scale(self.shadow, (110, 22)), (mx + 9, my + 118))
            s.blit(sprite, (mx, my + math.sin(self.time * 3 + 1) * 3))
        mx, my = self.battle_spot("monster")
        self.text(s, m.kind, (mx + 64, my + 146), 28, TEXT, "midtop")
        self.bar(s, (mx - 6, my + 172, 140, 14), m.health / m.max_health, RED)
        self.text(s, "%d/%d" % (m.health, m.max_health), (mx + 64, my + 190), 22, DIM, "midtop")
        if battle.fuse is not None and not battle.over:
            self.text(s, "FUSE: %d" % battle.fuse, (mx + 64, my - 4), 32, ORANGE, "midbottom", shadow=True)

        self.text(s, "VS", (box.centerx, box.y + 150), 56, RED, "center", shadow=True)

        # Floating damage numbers
        for pop in self.battle_popups:
            x, y = self.battle_spot(pop["who"])
            alpha = int(255 * max(0.0, 1 - pop["age"]))
            self.text(s, pop["text"], (x + 64, y + 10 - pop["age"] * 50), 48, pop["color"],
                      "center", shadow=True, alpha=alpha)
        self.draw_particles(s, "battle")

        # What just happened
        lines = []
        for text, kind in battle.lines[-2:]:
            for line in self.wrap(text, 24, box.w - 60):
                lines.append((line, KIND_COLORS.get(kind, TEXT)))
        y = box.y + 296
        for line, color in lines[-3:]:
            self.text(s, line, (box.centerx, y), 24, color, "midtop")
            y += 22

        # Buttons or the result
        self.battle_buttons = []
        if not battle.over:
            choices = [(action, key, words % p.food if "%d" in words else words) for action, key, words in
                       phase2.battle_buttons(self.game, [("attack", "A", "Attack"), ("run", "R", "Run away"),
                                                         ("eat", "E", "Eat (%d)")])]
            mouse = pygame.mouse.get_pos()
            ready = self.time >= self.battle_ready_at       # during the pause the buttons are dimmed
            for i, (action, key, label) in enumerate(choices):
                rect = pygame.Rect(0, 0, 210, 50)
                rect.center = (box.centerx + (i - 1) * 230, box.bottom - 44)
                hover = ready and rect.collidepoint(mouse)
                if not ready:
                    pygame.draw.rect(s, (40, 38, 58), rect, border_radius=12)
                    pygame.draw.rect(s, (80, 76, 110), rect, 2, border_radius=12)
                    self.text(s, "[%s]  %s" % (key, label), rect.center, 30, DIM, "center")
                    self.battle_buttons.append((action, rect))
                    continue
                pygame.draw.rect(s, (88, 80, 128) if hover else (62, 58, 92), rect, border_radius=12)
                pygame.draw.rect(s, YELLOW if hover else (130, 124, 180), rect, 2, border_radius=12)
                self.text(s, "[%s]  %s" % (key, label), rect.center, 30, TEXT, "center")
                self.battle_buttons.append((action, rect))
        else:
            words = {"won": ("VICTORY!", GREEN), "fled": ("You got away!", TEXT),
                     "exploded": ("BOOM!", ORANGE), "lost": ("Defeated...", RED),
                     "drowned": ("Glub, glub...", WATER_BLUE)}
            word, color = words.get(battle.result, ("", TEXT))
            self.text(s, word, (box.centerx, box.bottom - 66), 52, color, "center", shadow=True)
            alpha = int(160 + 95 * math.sin(self.time * 5))
            self.text(s, "Press SPACE to continue", (box.centerx, box.bottom - 28), 26, DIM, "center", alpha=alpha)
        phase2.draw_battle(self)                    # Phase 2: the timing bar

    def draw_sunfang(self):
        """The forging scene: the anvil, the three diamonds, the hammer, and the key to press."""
        f, s = self.sunfang, self.screen
        if not f:
            return
        self.overlay.fill((10, 4, 22, 235))
        s.blit(self.overlay, (0, 0))
        cx, cy = WIDTH // 2, HEIGHT // 2 - 40
        castle = self.art["castle_big"].copy()
        castle.set_alpha(70)
        s.blit(castle, castle.get_rect(center=(cx, cy - 120)))
        # the anvil
        anvil_y = cy + 190
        pygame.draw.polygon(s, (70, 70, 84), [(cx - 120, anvil_y), (cx + 120, anvil_y), (cx + 90, anvil_y + 30), (cx - 90, anvil_y + 30)])
        s.fill((52, 52, 64), (cx - 40, anvil_y + 30, 80, 50))
        s.fill((86, 86, 100), (cx - 130, anvil_y - 10, 260, 12))

        # where the diamonds are: rising, then circling closer with every strike, then melting together
        if f.phase == "rise":
            t = min(1.0, f.phase_time / f.RISE_TIME)
            radius, height = 140, lerp(anvil_y + 120, cy, t * (2 - t))
        elif f.phase == "finale":
            t = min(1.0, f.phase_time / 0.8)
            radius, height = lerp(140 - 25 * f.beats_done, 0, t), cy
        else:
            radius, height = 140 - 25 * f.beats_done, cy
        if f.phase != "finale" or f.phase_time < 0.8:
            glow = pygame.transform.smoothscale(self.gem_glow, (int(80 + 30 * f.beats_done),) * 2)
            for i in range(3):
                angle = f.time * (1.5 + f.beats_done * 0.7) + i * 2 * math.pi / 3
                x, y = cx + math.cos(angle) * radius, height + math.sin(angle) * radius * 0.4
                s.blit(glow, glow.get_rect(center=(x, y)))
                s.blit(self.art["diamond_big"], self.art["diamond_big"].get_rect(center=(x, y)))

        # the hammer swings around its handle and comes down on the anvil after each good strike
        since = f.time - f.last_strike
        swing = max(0.0, 1 - since / 0.35)
        hammer = pygame.Surface((180, 56), pygame.SRCALPHA)
        hammer.fill((120, 78, 40), (0, 20, 130, 16))
        hammer.fill((150, 150, 166), (124, 0, 56, 56))
        hammer.fill((190, 190, 206), (124, 0, 56, 10))
        turned = pygame.transform.rotate(pivot_image(hammer, (0, 28)), 120 + 62 * swing)   # 182 = down on the anvil
        s.blit(turned, turned.get_rect(center=(cx + 230, anvil_y - 34)))

        # the key to press, with its ring closing in
        if f.phase == "beat":
            ring = f.ring
            color = GREEN if ring > 0.5 else YELLOW if ring > 0.25 else RED
            pygame.draw.circle(s, color, (cx, cy - 250), int(34 + 70 * ring), 5)
            self.draw_key(s, f.key[1], (cx, cy - 250))
        if f.phase in ("beat", "pause") and f.beats_done < f.BEATS:
            name, words = f.step
            self.text(s, "Step %d of %d: %s" % (f.beats_done + 1, f.BEATS, name), (cx, cy - 330), 40,
                      (255, 190, 110), "center", shadow=True)
            self.text(s, words, (cx, cy - 295), 26, TEXT, "center")
        if f.message:
            self.text(s, f.message, (cx, cy - 170), 40, YELLOW if f.message == "CLANG!" else RED, "center", shadow=True)
        # how many beats are done
        for i in range(f.BEATS):
            done = i < f.beats_done
            pygame.draw.circle(s, (120, 235, 255) if done else (60, 60, 90), (cx - 75 + i * 50, anvil_y + 110), 12 if done else 9)
        if f.phase == "rise":
            self.text(s, "The diamonds are glowing...", (cx, cy - 250), 40, (210, 160, 255), "center", shadow=True)

        # the finale: Sunfang rises out of the light
        if f.phase in ("finale", "done") and f.phase_time > 0.8:
            t = min(1.0, (f.phase_time - 0.8) / 1.0)
            for i in range(12):                 # rays of light
                angle = f.time * 0.8 + i * math.pi / 6
                end = (cx + math.cos(angle) * 360 * t, cy + math.sin(angle) * 360 * t)
                pygame.draw.line(s, (255, 230, 150), (cx, cy), end, 3)
            s.blit(self.sun_glow, self.sun_glow.get_rect(center=(cx, cy)))
            s.blit(self.art["sunfang_big"], self.art["sunfang_big"].get_rect(center=(cx, cy - 20 * t)))
            self.text(s, "SUNFANG!", (cx, cy - 250), 84, YELLOW, "center", shadow=True)
            if f.perfect:
                self.text(s, "PERFECT FORGE!  +%d damage" % rules.PERFECT_BONUS, (cx, cy + 130), 36, GREEN, "center", shadow=True)
        self.draw_particles(s, "screen")

    def draw_key(self, surf, name, center):
        """A key to press: SPACE, or an arrow."""
        cx, cy = center
        box = pygame.Rect(0, 0, 150 if name == "SPACE" else 70, 64)
        box.center = center
        pygame.draw.rect(surf, (70, 74, 102), box, border_radius=12)
        pygame.draw.rect(surf, (200, 204, 230), box, 3, border_radius=12)
        if name == "SPACE":
            self.text(surf, "SPACE", center, 36, TEXT, "center")
            return
        tip = {"LEFT": (-1, 0), "RIGHT": (1, 0), "UP": (0, -1)}[name]
        points = [(0, -20), (16, 4), (6, 4), (6, 20), (-6, 20), (-6, 4), (-16, 4)]       # an arrow pointing up
        if tip == (-1, 0):
            points = [(y, -x) for x, y in points]
        elif tip == (1, 0):
            points = [(-y, x) for x, y in points]
        pygame.draw.polygon(surf, TEXT, [(cx + x, cy + y) for x, y in points])

    def draw_story(self):
        """A story card: a picture, a title, and a few sentences."""
        s, game = self.screen, self.game
        title, words, picture = game.story[0]
        self.overlay.fill((6, 4, 16, 225))
        s.blit(self.overlay, (0, 0))
        rng = random.Random(7)                          # twinkling stars
        for i in range(70):
            x, y = rng.randint(0, WIDTH), rng.randint(0, HEIGHT)
            if (self.time * 2 + i * 0.37) % 3 > 0.4:
                s.fill((200, 190, 255), (x, y, 2, 2))
        box = pygame.Rect(0, 0, 940, 620)
        box.center = (WIDTH // 2, HEIGHT // 2)
        self.panel_box(box, (170, 110, 255))
        self.draw_story_picture(picture, (box.centerx, box.y + 175))
        self.text(s, title, (box.centerx, box.y + 312), 54, YELLOW, "midtop", shadow=True)
        y = box.y + 380
        for line in self.wrap(words, 30, box.w - 120):
            self.text(s, line, (box.centerx, y), 30, TEXT, "midtop")
            y += 32
        total = self.story_page + len(game.story)
        alpha = int(160 + 95 * math.sin(self.time * 4))
        end = self.key_box(s, "ENTER", box.centerx - 190, box.bottom - 44)
        self.text(s, "next", (end + 8, box.bottom - 41), 24, TEXT, alpha=alpha)
        end = self.key_box(s, "S", box.centerx + 10, box.bottom - 44)
        self.text(s, "skip the story", (end + 8, box.bottom - 41), 24, YELLOW, alpha=alpha)
        self.text(s, "%d / %d" % (self.story_page + 1, total), (box.right - 30, box.bottom - 40), 24, DIM, "topright")

    def draw_story_picture(self, picture, middle):
        s, bob = self.screen, math.sin(self.time * 2) * 6
        def show(image, center, glow=None):
            if glow:
                s.blit(glow, glow.get_rect(center=center))
            s.blit(image, image.get_rect(center=center))
        cx, cy = middle
        if picture == "king":
            show(phase2.king_card(self) or self.art["king_big"], (cx, cy + bob), self.violet_glow)   # (Phase 2: new art)
        elif picture == "monsters":
            kinds = [kind for kind in rules.MONSTER_TYPES if kind not in ("Guardian", "Warden")]
            for i, kind in enumerate(kinds):
                x = cx + (i - (len(kinds) - 1) / 2) * 150
                show(self.monster_sprite(kind, 7), (x, cy + math.sin(self.time * 3 + i) * 8))
        elif picture == "sunfang":
            show(self.art["sunfang_big"], (cx, cy - 20 + bob), self.sun_glow)
            for i in range(3):
                show(self.art["diamond_big"], (cx + (i - 1) * 70, cy + 105 + math.sin(self.time * 3 + i) * 5))
        elif picture == "portal":
            show(phase2.hero_card(self) or self.art["player_title"], (cx - 120, cy + bob))
            for i in range(14):                         # the swirling Portal
                angle = self.time * 3 + i * 2 * math.pi / 14
                pygame.draw.circle(s, (210, 100, 255) if i % 2 else (100, 230, 255),
                                   (int(cx + 110 + math.cos(angle) * 70), int(cy + math.sin(angle) * 90)), 9)
        elif picture == "hollow":
            for i, art in enumerate(("dead_tree_big", "shrine_big", "dead_tree_big")):
                show(self.art[art], (cx + (i - 1) * 190, cy + (12 if i != 1 else 0)), self.violet_glow if i == 1 else None)
        elif picture == "castle":
            show(self.art["castle_big"], (cx, cy + bob), self.violet_glow)
        elif picture == "light":                        # the sun comes up, and the light is back!
            for i in range(12):
                a = self.time * 0.4 + i * math.pi / 6
                pygame.draw.line(s, (255, 214, 110), (cx, cy - 20), (cx + math.cos(a) * 190, cy - 20 + math.sin(a) * 125), 6)
            show(self.sun_glow, (cx, cy - 20))
            pygame.draw.circle(s, (255, 226, 120), (cx, cy - 20), 62)
            pygame.draw.circle(s, (255, 246, 200), (cx, cy - 20), 46)
            show(phase2.hero_card(self) or self.art["player_title"], (cx, cy + 70 + bob * 0.5))

    def craft_problem(self, kind):
        """Why you can't craft this right now - or None if you can."""
        game = self.game
        if kind == "sword":
            return game.forge_problem()
        if kind == "pickaxe":
            return game.pickaxe_problem()
        return game.build_problem(kind)

    def draw_craft(self):
        game, p, s = self.game, self.game.player, self.screen
        in_cave = self.craft_return == "cave"
        self.dim_screen(150)
        box = pygame.Rect(0, 0, 680, 640 + 80 * (len(self.crafts) - len(self.CRAFTS)))
        box.center = (WIDTH // 2, HEIGHT // 2)
        self.panel_box(box, GREEN)
        self.text(s, "Craft something!", (box.centerx, box.y + 18), 48, GREEN, "midtop", shadow=True)
        s.blit(self.art["wood"], (box.centerx - 84, box.y + 74))
        self.text(s, "You have %d wood" % p.wood, (box.centerx - 48, box.y + 76), 28, TEXT)
        costs = {"house": "%d wood" % rules.HOUSE_COST, "boat": "%d wood" % rules.BOAT_COST,
                 "bow": "%d wood" % rules.BOW_COST, "arrows": "%d wood" % rules.ARROW_COST,
                 "sword": "forge it!", "pickaxe": "%d wood" % rules.PICKAXE_CAVE_WOOD if in_cave else "free in the forest",
                 "hilt": "%d dead wood" % rules.HILT_WOOD}
        names = {"house": "House", "boat": "Boat", "bow": "Bow", "arrows": "%d arrows" % rules.ARROWS_PER_BUNDLE,
                 "sword": "Sword", "pickaxe": "Pickaxe", "hilt": "Hilt of Sunfang"}
        icons = {"house": self.art["house"], "boat": self.art["boat"], "bow": self.art["craft_bow"],
                 "arrows": self.art["bow"], "sword": self.art["craft_sword"], "pickaxe": self.art["craft_pickaxe"],
                 "hilt": self.art["wood"]}
        self.craft_rows = []
        for i, kind in enumerate(self.crafts):
            row = pygame.Rect(box.x + 28, box.y + 114 + i * 80, box.w - 56, 70)
            self.craft_rows.append(row)
            picked = i == self.craft_pick
            problem = self.craft_problem(kind)
            just_made = self.craft_flash and self.craft_flash[0] == i and self.time - self.craft_flash[1] < 0.6
            if just_made:
                color = (90, 150, 100)
            elif problem:
                color = (74, 68, 98) if picked else (50, 46, 66)
            else:
                color = (62, 110, 84) if picked else (44, 72, 58)
            pygame.draw.rect(s, color, row, border_radius=12)
            if picked:                            # the highlight: a yellow frame and a little arrow
                pygame.draw.rect(s, YELLOW, row, 3, border_radius=12)
                tip = row.x + 34 + math.sin(self.time * 6) * 3
                pygame.draw.polygon(s, YELLOW, [(tip - 18, row.centery - 13), (tip - 18, row.centery + 13), (tip, row.centery)])
            icon = icons[kind]
            s.blit(icon, icon.get_rect(center=(row.x + 92, row.centery)))
            self.text(s, "%s  -  %s" % (names[kind], costs[kind]), (row.x + 144, row.y + 8), 30, TEXT)
            if just_made:
                words = "Made it! Press ENTER again for another."
            elif problem:
                words = problem
            else:
                words = "Ready! Press ENTER (or click) to craft it." if picked else "Ready to craft!"
            self.text(s, words, (row.x + 144, row.y + 40), 22, YELLOW if just_made else DIM if problem else GREEN)
        self.text(s, "UP/DOWN or the mouse: pick    ENTER or click: craft    Esc or C: close",
                  (box.centerx, box.bottom - 30), 22, DIM, "midtop")

    def draw_levelup(self):
        """The LEVEL UP! card: pick 1 of 3 powers."""
        game, p, s = self.game, self.game.player, self.screen
        offer = game.power_offer or []
        if not offer or not game.level_ups:
            return
        self.dim_screen(150)
        box = pygame.Rect(0, 0, 700, 196 + 88 * len(offer))
        box.center = (WIDTH // 2, HEIGHT // 2)
        self.panel_box(box, YELLOW)
        self.text(s, "LEVEL UP!  Level %d" % game.level_ups[0], (box.centerx, box.y + 20), 60, YELLOW, "midtop", shadow=True)
        self.text(s, "You are fully healed. Pick a new power!", (box.centerx, box.y + 80), 28, TEXT, "midtop")
        mouse = pygame.mouse.get_pos()
        self.card_rows = []
        for i, name in enumerate(offer):
            row = pygame.Rect(box.x + 30, box.y + 124 + i * 88, box.w - 60, 76)
            self.card_rows.append(row)
            pygame.draw.rect(s, (92, 78, 40) if row.collidepoint(mouse) else (68, 60, 40), row, border_radius=12)
            self.key_box(s, str(i + 1), row.x + 14, row.centery - 11)
            icon = self.art[POWER_ICONS.get(name, "star")]
            if icon.get_height() < 30:
                icon = pygame.transform.scale_by(icon, 2)
            spot = icon.get_rect(center=(row.x + 92, row.centery))
            s.blit(icon, spot)
            if name == "Speedy":                     # whoosh lines behind the runner
                for dy in (-10, 0, 10):
                    pygame.draw.line(s, TEXT, (spot.x - 16, spot.centery + dy), (spot.x - 4, spot.centery + dy), 3)
            self.text(s, name, (row.x + 144, row.y + 10), 32, YELLOW)
            have, limit = p.power(name), rules.POWERS[name]["limit"]
            count = "you have %d" % have if have else "new!"
            if limit is not None:
                count += " (only once)" if limit == 1 else " (up to %d)" % limit
            self.text(s, count, (row.right - 16, row.y + 14), 22, DIM, "topright")
            self.text(s, rules.POWERS[name]["what"], (row.x + 144, row.y + 46), 24, TEXT)
        keys = "1, 2 or 3" if len(offer) == 3 else " or ".join(str(i + 1) for i in range(len(offer)))
        self.text(s, "Press %s (or click one)" % keys, (box.centerx, box.bottom - 38), 24, DIM, "midtop")

    FORGE_WORDS = {"perfect": ("PERFECT!", YELLOW), "good": ("Good", GREEN), "miss": ("Miss", RED)}
    SWORD_WORDS = {"great": ("A GREAT sword! +%d damage, %d hits" % (rules.GREAT_SWORD_BONUS, rules.GREAT_SWORD_DURABILITY),
                             YELLOW),
                   "normal": ("A new sword! %d hits" % rules.SWORD_DURABILITY, GREEN),
                   "cracked": ("CRACK! A cracked sword: %d hits" % rules.CRACKED_SWORD_DURABILITY, RED)}

    def draw_forge(self):
        forge = self.forge
        if forge is None:
            return
        s = self.screen
        self.dim_screen(150)
        box = pygame.Rect(0, 0, 660, 320)
        box.center = (WIDTH // 2, HEIGHT // 2)
        self.panel_box(box, ORANGE)
        self.text(s, "Forge a Sword!", (box.centerx, box.y + 18), 48, ORANGE, "midtop", shadow=True)
        self.text(s, "SPACE strikes. Gold is Perfect, green is Good. 3 strikes!", (box.centerx, box.y + 70),
                  24, TEXT, "midtop")
        # The 3 strikes so far: a dot for each, gold, green or red
        for i in range(rules.FORGE_STRIKES):
            cx = box.centerx + (i - 1) * 46
            if i < len(forge.strikes):
                word, color = self.FORGE_WORDS[forge.strikes[i]]
                pygame.draw.circle(s, color, (cx, box.y + 116), 13)
            else:
                pygame.draw.circle(s, (90, 80, 80), (cx, box.y + 116), 13, 3)
        bar = pygame.Rect(0, 0, 560, 40)
        bar.center = (box.centerx, box.y + 175)
        pygame.draw.rect(s, (60, 50, 50), bar, border_radius=10)
        if not forge.finished:
            zone = pygame.Rect(bar.x + int(forge.zone_x * bar.w), bar.y, int(forge.zone_w * bar.w), bar.h)
            pygame.draw.rect(s, (70, 200, 90), zone, border_radius=8)
            pygame.draw.rect(s, (140, 255, 150), zone, 2, border_radius=8)
            gold = pygame.Rect(bar.x + int(forge.gold_x * bar.w), bar.y, int(forge.gold_w * bar.w), bar.h)
            pygame.draw.rect(s, (240, 190, 50), gold, border_radius=5)
            pygame.draw.rect(s, (255, 240, 150), gold, 2, border_radius=5)
        mx = bar.x + int(forge.pos * bar.w)
        heat = (255, int(160 + 80 * math.sin(self.time * 20)), 60)
        pygame.draw.rect(s, heat, (mx - 6, bar.y - 10, 12, bar.h + 20), border_radius=5)
        if forge.finished:
            words, color = self.SWORD_WORDS[forge.quality]
            self.text(s, words, (box.centerx, box.bottom - 70), 36, color, "midtop", shadow=True)
        elif forge.strikes and forge.pause > 0:
            word, color = self.FORGE_WORDS[forge.strikes[-1]]
            self.text(s, word, (box.centerx, box.bottom - 72), 44, color, "midtop", shadow=True)
        elif not forge.strikes:
            self.text(s, "(Esc to stop)", (box.centerx, box.bottom - 50), 22, DIM, "midtop")

    def draw_help(self):
        s, p = self.screen, self.game.player
        self.dim_screen(180)
        box = pygame.Rect(0, 0, 1400, 800)
        box.center = (WIDTH // 2, HEIGHT // 2)
        self.panel_box(box)
        self.text(s, "How to Play", (box.centerx, box.y + 22), 52, YELLOW, "midtop", shadow=True)
        if phase2.is_phase2(self.game):     # Phase 2: the pause menu and the save slots (phase2/pause.py)
            self.text(s, "P: pause and save  -  3 save slots (Load)", (box.right - 36, box.y + 40), 24, GREEN, "topright")
        lines = [
            ("GOAL", YELLOW),
            ("Defeat %d monsters and mine %d diamonds." % (rules.MONSTERS_TO_DEFEAT, rules.DIAMONDS_NEEDED), TEXT),
            ("Then the Portal opens. It's on an island - you'll need a boat!", TEXT),
            ("", TEXT),
            ("PLACES", YELLOW),
            ("Forest: search for food, chop wood, and craft swords and pickaxes (C)", TEXT),
            ("Field: open grass - watch out for thistles! A good spot to build a house.", TEXT),
            ("Path: monsters won't chase you, Skeletons can't shoot you, and no bad luck.", TEXT),
            ("Mine: climb down into the cave. Not every cave has a diamond - explore!", TEXT),
            ("House: you heal a little every turn. Monsters can't get you here!", TEXT),
            ("Landmark: climb it (SPACE). Ice slides you, reeds hide you, vents puff!", TEXT),
            ("", TEXT),
            ("MONSTERS", YELLOW),
            ("Zombie: slow but tough.   Skeleton: shoots arrows from 2 tiles away.", TEXT),
            ("Ember Skull: blows up after 3 rounds - beat it fast or run!", TEXT),
            ("", TEXT),
            ("CAVES", YELLOW),
            ("Arrows run.  SPACE jumps - hold it down to jump higher.", TEXT),
            ("R: dig cracked rock and ore, open chests, swing your sword.  C: craft.", TEXT),
            ("Jump on monsters! Watch out for spikes, fire, lava and crumbly ledges.", TEXT),
            ("Diamond rings (in chests) power up your sword: +%d damage for %d hits."
             % (rules.RING_BONUS, rules.RING_HITS), TEXT),
            ("Dig out the diamond (if there is one), then go through the EXIT door.", TEXT),
            ("", TEXT),
            ("WOOD, HOUSES AND BOATS", YELLOW),
            ("T in the forest chops wood. Each tree has %d - then it falls down!" % rules.TREE_WOOD, TEXT),
            ("C opens the Craft menu: a house (%d wood), a boat (%d), a bow (%d), arrows (%d),"
             % (rules.HOUSE_COST, rules.BOAT_COST, rules.BOW_COST, rules.ARROW_COST), TEXT),
            ("a sword or a pickaxe. UP/DOWN picks, ENTER crafts (or click). It stays open!", TEXT),
            ("F shoots an arrow (fire arrows in Nightfall!).  Armor soaks up hits.", TEXT),
            ("Sea Serpents live in the lake. Beat them fast - they can smash your boat!", TEXT),
        ]
        lines = phase2.help_lines(self.game, lines)     # Phase 2: its own GOAL
        y = box.y + 84
        for line, color in lines:
            self.text(s, line, (box.x + 36, y), 24 if color == TEXT else 23, color)
            y += 24 if line else 16             # a blank line is a smaller gap, so the whole list fits

        # The right side: XP, leveling up, and every power you can pick
        x = box.x + 740
        pygame.draw.line(s, (70, 66, 96), (x - 28, box.y + 90), (x - 28, box.bottom - 60), 2)
        xp_lines = [
            ("XP AND LEVELING UP", YELLOW),
            ("You get XP for beating monsters, grabbing gems and gold coins,", TEXT),
            ("mining a diamond (+%d), walking out of a cave's EXIT door (+%d)"
             % (rules.DIAMOND_XP, rules.EXIT_XP), TEXT),
            ("and finishing a quest (+%d)." % rules.QUEST_XP, TEXT),
            ("Level 2 needs %d XP, then %d more for level 3, %d more for level 4..."
             % (rules.XP_PER_LEVEL, 2 * rules.XP_PER_LEVEL, 3 * rules.XP_PER_LEVEL), TEXT),
            ("Every level up heals you all the way, and you pick 1 of %d powers." % rules.CARD_CHOICES, TEXT),
            ("LIVES: out of health? Lose a life, wake up by the Mine or a house.", TEXT),
            ("", TEXT),
            ("POWERS", YELLOW),
        ]
        y = box.y + 84
        for line, color in xp_lines:
            self.text(s, line, (x, y), 24 if color == TEXT else 23, color)
            y += 24
        tight = phase2.is_phase2(self.game)     # Phase 2 squeezes this column: it ran over the last line
        for name, power in rules.POWERS.items():
            said = self.text(s, name, (x, y), 24, GREEN)
            limit = power["limit"]
            self.text(s, "any number of times" if limit is None else "only once" if limit == 1 else "up to %d times" % limit,
                      (said.right + 10, y + 2), 20, DIM)
            if p.power(name):
                self.text(s, "you have it" + (" x%d" % p.power(name) if p.power(name) > 1 else ""),
                          (box.right - 36, y + 2), 20, YELLOW, "topright")
            self.text(s, power["what"], (x + 20, y + 22), 22, TEXT)
            y += 37 if tight else 41
        moves = [("CAVE MOVES", YELLOW),
                 ("UP/DOWN at a ladder: climb it.  SPACE: jump off.", TEXT),
                 ("Just miss a ledge? You catch its edge and pull up.", TEXT),
                 ("DOWN in the air: ground pound (smashes cracked rock!)", TEXT),
                 ("Hold DOWN: crawl through low tunnels.", TEXT),
                 ("Climbing wall: hold UP to climb it. SPACE: wall jump!", TEXT)]
        for line, color in moves:
            self.text(s, line, (x, y), 23 if color == TEXT else 22, color)
            y += 22 if tight else 23
        self.text(s, "Press any key to keep playing.     Tip bubbles are %s: S in a bubble turns them off, "
                  "TAB on the title screen turns them on." % ("ON" if self.tips.on else "OFF"),
                  (box.centerx, box.bottom - 36), 24, DIM, "midtop")

    def draw_end(self):
        game, p = self.game, self.game.player
        s = self.screen
        self.dim_screen(190)
        stats = [("Turns", game.turn), ("Level", p.level),
                 ("Monsters defeated", p.monsters_defeated), ("Diamonds", p.diamonds)]
        if game.won and game.world == 2:            # you beat the Shadow King: the whole story is over!
            stats = [("Level", p.level), ("Monsters defeated", p.monsters_defeated),
                     ("Light shards", "%d / %d" % (p.light_shards, len(castle.CASTLE_LEVELS))),
                     ("Knocked out", game.knockouts), ("Shadow King fights", game.king_fights), ("Turns", game.turn)]
        stats = phase2.end_stats(game, stats)       # Phase 2: Light Stones, not diamonds
        box = pygame.Rect(0, 0, 620, 252 + 32 * len(stats))
        box.center = (WIDTH // 2, HEIGHT // 2)
        self.panel_box(box, GREEN if game.won else RED)
        if game.won and game.world == 2:
            self.text(s, "THE END", (box.centerx, box.y + 28), 90, YELLOW, "midtop", shadow=True)
            self.text(s, "%s beat the Shadow King, and the light came back!" % p.name, (box.centerx, box.y + 110),
                      30, TEXT, "midtop")
        elif game.won:
            self.text(s, "YOU WIN!", (box.centerx, box.y + 28), 90, YELLOW, "midtop", shadow=True)
            self.text(s, "%s escaped through the Portal!" % p.name, (box.centerx, box.y + 110), 30, TEXT, "midtop")
        else:
            self.text(s, "GAME OVER", (box.centerx, box.y + 28), 90, RED, "midtop", shadow=True)
            self.text(s, "%s was defeated..." % p.name, (box.centerx, box.y + 110), 30, TEXT, "midtop")
        y = box.y + 160
        for label, value in stats:
            self.text(s, label, (box.centerx - 20, y), 28, DIM, "topright")
            self.text(s, str(value), (box.centerx + 20, y), 28, TEXT)
            y += 32
        alpha = int(160 + 95 * math.sin(self.time * 5))
        self.text(s, "ENTER to play again     ESC to quit", (box.centerx, box.bottom - 40), 28, TEXT,
                  "midtop", alpha=alpha)

    def draw_title(self):
        s = self.screen
        # The camera drifts slowly over the world behind the title
        drift = self.time * 0.08
        self.cam = (round((MAP_W - VIEW_W) * (0.5 + 0.5 * math.sin(drift))),
                    round((MAP_H - VIEW_H) * (0.5 + 0.5 * math.sin(drift * 0.7))))
        self.draw_tiles(self.view, fog=False)
        zoom = max(WIDTH / VIEW_W, HEIGHT / VIEW_H)        # stretch the view to fill the window
        background = pygame.transform.scale(self.view, (int(VIEW_W * zoom), int(VIEW_H * zoom)))
        s.blit(background, background.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        self.dim_screen(150)
        top = (HEIGHT - 708) // 2                          # keep the title words in the middle

        if not phase2.draw_title(self, top):        # Phase 2 picked: its own name and goal (phase2/theme.py)
            self.text(s, "Adventure World", (WIDTH // 2, top + 90), 84, YELLOW, "center", shadow=True)
            tagline = "Explore. Fight monsters. Find diamonds. Escape through the Portal!"
            self.text(s, tagline, (WIDTH // 2, top + 150), 28, TEXT, "center")

        # The Hero and every monster in the game. Add a monster to MONSTER_TYPES and it shows up here too!
        cast = [(self.art["player_title"], self.name_input.strip() or "You")]
        cast += [(self.monster_sprite(kind, 6), kind) for kind in rules.MONSTER_TYPES if kind not in ("Guardian", "Warden")]
        gap = min(150, (WIDTH - 120) // len(cast))
        for i, (sprite, label) in enumerate(cast):
            middle = WIDTH // 2 + (i - (len(cast) - 1) / 2) * gap
            y = top + 210 + math.sin(self.time * 3 + i) * 8
            s.blit(sprite, (middle - sprite.get_width() / 2, y))
            self.text(s, label, (middle, top + 326), 22, YELLOW if i == 0 else TEXT, "center", shadow=True)

        self.text(s, "What's your name, adventurer?", (WIDTH // 2, top + 380), 32, TEXT, "center")
        box = pygame.Rect(0, 0, 380, 58)
        box.center = (WIDTH // 2, top + 432)
        pygame.draw.rect(s, (40, 42, 60), box, border_radius=12)
        pygame.draw.rect(s, YELLOW, box, 3, border_radius=12)
        name_rect = self.text(s, self.name_input, box.center, 44, TEXT, "center")
        if int(self.time * 2) % 2 == 0:
            pygame.draw.line(s, TEXT, (name_rect.right + 4, box.y + 12), (name_rect.right + 4, box.bottom - 12), 3)

        self.draw_mode_choice(top + 482)
        alpha = int(160 + 95 * math.sin(self.time * 4))
        self.text(s, "Press ENTER to start", (WIDTH // 2, top + 520), 40, GREEN, "center", shadow=True, alpha=alpha)
        self.text(s, "Arrow keys to move  -  H for help in the game", (WIDTH // 2, top + 570), 24, DIM, "center")

        # The tips switch: TAB (or a click) turns the tip bubbles on or off (see tutorial.py)
        words = "Tip bubbles: ON" if self.tips.on else "Tip bubbles: OFF"
        width = self.words("TAB", 20, TEXT).get_width() + 12 + 10 + self.words(words, 28, GREEN).get_width()
        x, y = WIDTH // 2 - width // 2, top + 610
        end = self.key_box(s, "TAB", x, y)
        said = self.text(s, words, (end + 10, y + 11), 28, GREEN if self.tips.on else DIM, "midleft")
        self.tips_switch = pygame.Rect(x, y, said.right - x, 22).inflate(16, 16)
        phase2.draw_slots(self)                             # Phase 2's save slot list, if it's open

    def draw_mode_choice(self, middle_y):
        """Classic, Phase 2 (and Continue, with a saved Phase 2 game): LEFT and RIGHT or a click picks one."""
        s, gap, width = self.screen, 16, 150
        x = WIDTH // 2 - (len(self.modes) * (width + gap) - gap) // 2
        self.mode_buttons = {}
        for mode in self.modes:
            box = pygame.Rect(x, middle_y - 17, width, 34)
            picked = mode == self.mode
            pygame.draw.rect(s, (70, 62, 30) if picked else (40, 42, 60), box, border_radius=10)
            pygame.draw.rect(s, YELLOW if picked else (90, 94, 124), box, 3 if picked else 2, border_radius=10)
            self.text(s, GAME_MODES[mode], box.center, 28, YELLOW if picked else DIM, "center")
            self.mode_buttons[mode] = box
            x += width + gap


def main():
    parser = argparse.ArgumentParser(description="Adventure World")
    parser.add_argument("--name", help="your player's name")
    parser.add_argument("--seed", type=int, help="random seed (same seed = same world)")
    parser.add_argument("--mute", action="store_true", help="start with sound off")
    parser.add_argument("--nightfall", action="store_true", help="play-test: start in Nightfall Hollow, just through the Portal")
    parser.add_argument("--castle", action="store_true", help="play-test: start right next to the Shadow King's castle")
    parser.add_argument("--throne", action="store_true", help="play-test: start in the throne room, fighting the Shadow King")
    parser.add_argument("--phase2", action="store_true", help="start a new Phase 2 game straight away (the bigger world)")
    parser.add_argument("--continue", dest="continue_save", action="store_true",
                        help="carry on with the saved Phase 2 game (a new one if there's no save)")
    args = parser.parse_args()

    phase2_mode = "continue" if args.continue_save else "phase2" if args.phase2 else None
    app = App(args.name or "", seed=args.seed, sound=not args.mute, castle=args.castle, throne=args.throne, nightfall=args.nightfall,
              phase2_mode=phase2_mode)
    app.run()
    pygame.quit()


if __name__ == "__main__":
    main()
