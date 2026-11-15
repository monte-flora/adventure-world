"""The Hero at 32 x 32 in a Phase 2 game: which picture to draw, and how big.

The letters are in phase2/art_hero_front.py, art_hero_side.py and art_hero_back.py. A Classic game never
comes here: it keeps the 16 x 16 Hero of sprites.py. Only the pictures change: his body in a cave (the box
that bumps into walls and monsters) is the same size as before, and every picture is as big on the screen
as the old one, except on the map, where he fills his square like the people do.
"""

import pygame

from phase2 import art
from phase2.art_hero_back import ARMOR_BACK, ARMOR_FRONT, BACK_STAND, CLIMB_1, CLIMB_2, WALK_UP_1, WALK_UP_2
from phase2.art_hero_front import FRONT_STAND, WALK_DOWN_1, WALK_DOWN_2
from phase2.art_hero_side import ARMOR_SIDE, ARMOR_WALL, SIDE, WALL

MAP_SCALE = 2                   # on the map: 64 pixels, one full map square (like the people)
FIGHT_SCALE = 4                 # in a map fight: 128 pixels, as big as the old Hero
CARD_SCALE = 3                  # on a story card: 96 pixels, as big as the old Hero
FIGHT_HAND = (23.5, 23)         # where his sword hand is in the front picture (in art squares)


def wear(letters, overlay):
    """Put one letter picture on top of another (like game.wear)."""
    return ["".join(top if top != "." else bottom for bottom, top in zip(low, high))
            for low, high in zip(letters, overlay)]


class Views:
    """The Hero in a cave, with the same names as the game's own 16 x 16 pictures (game.App.load_art)."""
    side_view = dict(SIDE)
    side_view_armored = {name: wear(letters, ARMOR_SIDE) for name, letters in SIDE.items()}
    climb_view = [CLIMB_1, CLIMB_2]
    climb_view_armored = [wear(letters, ARMOR_BACK) for letters in climb_view]
    wall_view = dict(WALL)
    wall_view_armored = {name: wear(letters, ARMOR_WALL) for name, letters in WALL.items()}


VIEWS = Views()

# Walking on the map: standing, then 2 walking pictures for each way (left is right, flipped over)
MAP_WALK = {"down": ([FRONT_STAND, WALK_DOWN_1, WALK_DOWN_2], ARMOR_FRONT),
            "up": ([BACK_STAND, WALK_UP_1, WALK_UP_2], ARMOR_BACK),
            "right": ([SIDE["stand"], SIDE["step 1"], SIDE["step 2"]], ARMOR_SIDE)}
FRONT_ARMORED = wear(FRONT_STAND, ARMOR_FRONT)

# Every pose, by name (for the tests and tools/art_preview.py)
POSES = {"front stand": FRONT_STAND, "walk down 1": WALK_DOWN_1, "walk down 2": WALK_DOWN_2,
         "back stand": BACK_STAND, "walk up 1": WALK_UP_1, "walk up 2": WALK_UP_2,
         "climb 1": CLIMB_1, "climb 2": CLIMB_2}
POSES.update({"side " + name: letters for name, letters in SIDE.items()})
POSES.update({"wall " + name: letters for name, letters in WALL.items()})
OVERLAYS = {"armor front": ARMOR_FRONT, "armor side": ARMOR_SIDE, "armor back": ARMOR_BACK,
            "armor wall": ARMOR_WALL}

_big = {}                       # every 32 x 32 picture a cave can draw, by id (so we can tell them from the old ones)
_pictures = {}


def _remember(letters):
    _big[id(letters)] = letters


for _view in (VIEWS.side_view, VIEWS.side_view_armored, VIEWS.wall_view, VIEWS.wall_view_armored):
    for _letters in _view.values():
        _remember(_letters)
for _letters in VIEWS.climb_view + VIEWS.climb_view_armored + list(art.MONSTER_ART.values()):
    _remember(_letters)


def is_big(letters):
    """Is this one of Phase 2's 32 x 32 pictures?"""
    return id(letters) in _big


def picture(letters, scale):
    """A 32 x 32 picture, `scale` screen pixels per square. 2.5 is fine: it's painted at 5 and every other
    screen pixel is kept, so the edges stay crisp."""
    if scale == int(scale):
        return art.make(letters, int(scale))
    twice = art.make(letters, int(scale * 2))
    return pygame.transform.scale(twice, (twice.get_width() // 2, twice.get_height() // 2))


def cave_picture(letters, scale):
    """A cave picture of a 32 x 32 Hero or monster, as big as an old 16 x 16 one at `scale`. None for old art."""
    return picture(letters, scale / 2) if is_big(letters) else None


def art_pixel(letters, scale):
    """How big one square of this picture is in a cave: half as big for 32 x 32 art."""
    return scale / 2 if is_big(letters) else scale


def views(app):
    """The Hero's cave pictures in a Phase 2 game, or None."""
    return VIEWS if art.is_phase2(getattr(app, "game", None)) else None


def _cached(key, letters, scale, flip=False):
    if key not in _pictures:
        image = art.make(letters, scale)
        _pictures[key] = pygame.transform.flip(image, True, False) if flip else image
    return _pictures[key]


def map_picture(app, name, pose):
    """The Hero on the map. `name` is the way he faces, like "left" or "down armor". None in Classic."""
    if not art.is_phase2(getattr(app, "game", None)):
        return None
    way = name.split()[0]
    pictures, armor = MAP_WALK["right" if way == "left" else way]
    letters = pictures[pose]
    if name.endswith("armor"):
        letters = wear(letters, armor)
    return _cached(("map", name, pose), letters, MAP_SCALE, flip=way == "left")


def fight_picture(app, armored):
    """The Hero in a map fight (128 pixels, like the old one). None in Classic."""
    if not art.is_phase2(getattr(app, "game", None)):
        return None
    return _cached(("fight", armored), FRONT_ARMORED if armored else FRONT_STAND, FIGHT_SCALE)


def fight_hand(app):
    """Where his sword hand is in the fight picture, in screen pixels from its top left. None in Classic."""
    if not art.is_phase2(getattr(app, "game", None)):
        return None
    return FIGHT_HAND[0] * FIGHT_SCALE, FIGHT_HAND[1] * FIGHT_SCALE


def card_picture(app):
    """The Hero on a story card. None in Classic."""
    if not art.is_phase2(getattr(app, "game", None)):
        return None
    return _cached(("card",), FRONT_STAND, CARD_SCALE)


def cave_monster_art(app, kind):
    """The letters of a monster's new picture in a Phase 2 cave. None in Classic, or if it keeps its old one."""
    if not art.is_phase2(getattr(app, "game", None)):
        return None
    return art.MONSTER_ART.get(kind)


def map_monster_scale(app, kind):
    """A monster with a new picture is drawn crisp on the map: 64 pixels, a whole square (the scale to ask
    monster_sprite for). None in Classic, or for a monster that keeps its old picture."""
    if art.is_phase2(getattr(app, "game", None)) and kind in art.MONSTER_ART:
        return 2 * art.BIG_SCALE
    return None
