"""
NEW PIXEL ART for Phase 2: the townsfolk (on the map, and big faces for the dialogue box) and a
new Shadow King. Classic keeps the pictures in sprites.py: nothing here is used in a Classic game.

Like sprites.py, every picture is a grid of letters and COLORS says which color each letter means
(a "." is see-through). COLORS has every color from sprites.py, plus more shades, so each color
can have a light side and a dark side. The light comes from the top left.

    BIG_MAP_ART     one 32 x 32 picture of each "look", whole (the map: 64 pixels, one full square)
                                                             in art_big.py, art_people_a.py and art_people_b.py
    MONSTER_ART     a 32 x 32 picture of 9 monsters           in art_monsters_a.py and art_monsters_b.py
                    (the Skeleton and the Ember Skull keep their sprites.py pictures)
    MAP_ART         one 16 x 16 picture for each look (the old small ones: a little icon)
    PORTRAITS       one 32 x 32 face for each look (the dialogue box)        in art_big.py
    KING, ANGRY_KING, KING_BIG       the Shadow King (36 x 36)               in art_big.py

Want a new look? Draw it whole at 32 x 32 and add it to BIG_MAP_ART, and draw a 32 x 32 face in
art_big.py and add it to PORTRAITS. tools/art_preview.py saves pictures of everything (docs/art-refresh/).
"""

import sys

import pygame

import sprites

COLORS = dict(sprites.COLORS)
COLORS.update({
    "S": (255, 224, 190),   # skin, in the light
    "d": (206, 150, 110),   # skin, in the shade
    "u": (178, 120, 82),    # dark skin
    "U": (130, 84, 56),     # dark skin, in the shade
    "3": (226, 128, 118),   # pink (cheeks and mouths)
    "f": (156, 228, 128),   # light green
    "F": (26, 78, 46),      # deep green
    "I": (126, 166, 246),   # light blue
    "D": (24, 34, 88),      # navy blue
    "x": (246, 112, 98),    # light red
    "X": (88, 16, 34),      # deep red
    "W": (255, 240, 160),   # pale yellow
    "O": (176, 118, 34),    # dark gold
    "z": (200, 154, 100),   # tan
    "Z": (56, 36, 24),      # darkest brown
    "V": (118, 48, 162),    # middle purple
    "2": (200, 96, 255),    # bright purple (gems)
    "L": (246, 222, 255),   # the white-hot middle of a glow
    "K": (56, 54, 74),      # charcoal (dark armor)
    "1": (40, 38, 54),      # armor in the shade
})

# ---------------------------------------------------------------------------
# The people on the map (16 x 16). Each one holds something that says what they do.
# ---------------------------------------------------------------------------

# A farmer: a straw hat with a red band, a blue shirt and a pitchfork
FARMER = [
    "................",
    ".....kkkkkk.....",
    "....kWyyyyYk....",
    "....kyyyyyYk....",
    "..kkkrrrrrRkkk..",
    ".kWyyyyyyyyyYOk.",
    "..kkSssssssdkk..",
    "w.wksskssksdk...",
    "w.wkssssssddk...",
    "eee.kss33sdk....",
    ".nkIIbbbbbbBBk..",
    ".nskIbbbbbbBkdk.",
    ".nkkNNNYYNNNkk..",
    ".n.knnnnnnnNk...",
    ".n.knnNkknnNk...",
    ".n.kZZk..kZZk...",
]

# The merchant (the "shopkeeper" look): an old woman in a green hat, with a huge pack, a bedroll and a cane
SHOPKEEPER = [
    "................",
    ".kkkkkk.........",
    "kzznnnNkkkkk....",
    "kznNnnNkfgGGk...",
    "kkkkkkfggggGGGk.",
    "kznnnkkkkkkkkkk.",
    "kznnnklSssssdlk.",
    "knnYnklskssksek.",
    "knnnnkkss33sdk..",
    "kNnnnkfkkkkkGk.k",
    "kNnnnkfgGGggGFkn",
    ".kNnnksgGGggGFsn",
    ".kkkkkfgGGggGFkn",
    "....kfggGGggGGFn",
    "....kfgGGGGgGGFn",
    "....kkkkkkkkkkkn",
]

# The blacksmith: a big man with a bushy beard, a red shirt, a leather apron and a hammer
BLACKSMITH = [
    "................",
    "....kkkkkkkk....",
    "...kNhhhhhhNk...",
    "...khhhhhhhNk...",
    "...khSsssssdk...",
    "...ksskssksdk...",
    "...kNssssssNk...",
    "...kNNh33hNNk...",
    ".kkkkNNhhNNkkkk.",
    "kxrrkznNNnzkrrRk",
    "kSsskzznnnnkssdk",
    "kSsdkznnnnnksddk",
    "kSsskznnnnnkssdk",
    "kleekznnnnNkkkk.",
    "keeEkkBBkBBk....",
    "kkkkZZZk.kZZZk..",
]

# The guide: a green cap with a red feather, a red scarf and a map of the world
GUIDE = [
    "..........kk....",
    ".....kkkkkxrk...",
    "....kfggggkRk...",
    "...kfggggggGk...",
    "..kkGGGGGGGGkk..",
    "...khSssssdhk...",
    "...khskssksNk...",
    "...kSsssssddk...",
    "....kss33sdk....",
    "..kkfgxrrRgGkk..",
    ".kfgkwwwwwwkgGk.",
    ".kSskwNNwrwkssk.",
    "..kkkwwwNwwkkk..",
    "...kgkkkkkkGk...",
    "...kNNNkkNNNk...",
    "..kZZZk..kZZZk..",
]

# The mage (the "wizard" look): a tall purple hat, a long white beard and a staff with a green gem
WIZARD = [
    "......kk.....kk.",
    ".....kVpk...kfjk",
    "....kVpppk..kjTk",
    "....kVppPk...kn.",
    "...kV2222Pk...n.",
    ".kVVppppppPPk.n.",
    "..kkwwsswwkk..n.",
    "...kskssksk...n.",
    "...kwwsddwlk..n.",
    "..kVwwwwwwlPk.n.",
    ".kVpkwwwwlkpPsn.",
    ".kVppkwwwlkpPkn.",
    ".kVpppkwlkppPkn.",
    ".kVppp2k2pppPkn.",
    ".kVVpppppppPPkn.",
    ".kkkkkkkkkkkkkn.",
]

# A hunter: a green hood and cape, a bow in one hand and a quiver of arrows on the back
HUNTER = [
    "................",
    ".....kkkkkk.....",
    "....kfggggGk.l..",
    "...kfgggggGGkln.",
    "...kfgGGGGGGknN.",
    "n..kgGssssdGkNk.",
    "ln.kgGskskdGkk..",
    "l.nkgGGssdGGk...",
    "l.nkgGFFFFFGFk..",
    "l.skgGNzzznGGFk.",
    "l.nkgGzNzznGGFk.",
    "l.nkgGNNYNNGGFk.",
    "ln.kgFznkznGFFk.",
    "n..kFFNNkNNFFFk.",
    "...kFkZZkZZkFFk.",
    "....kkkkkkkkkkk.",
]

# A kid in a red cap and a yellow shirt, with a red balloon (smaller than the grown-ups)
KID = [
    "................",
    "............kk..",
    "...........kxrk.",
    "...........krRk.",
    ".....kkkkkk.kk..",
    "....kxrrrrRk.E..",
    "..kRRrrrrrRk.E..",
    "..kkkSssssdk.E..",
    "....kskssksk.E..",
    "....ks3ss3sk.E..",
    ".....kssssk..E..",
    "....kWyyyyYkks..",
    "...kskyyyyYk....",
    "....kkIbbBkk....",
    ".....kIkkBk.....",
    ".....kk..kk.....",
]

# A little orange cat, sitting
CAT = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "...k.....k......",
    "..kok...kok.....",
    "..kyokkkkoOk....",
    "..kyooooooOk....",
    "..kookookoOk....",
    "..kooo33ooOk....",
    "...kowwwwOk..kk.",
    "..kyowwwwoOk.kok",
    "..kyowwwwoOkkoOk",
    "..koooooooOkoOk.",
    "...kkkkkkkkkkk..",
]

# A villager: long yellow hair, a blue dress and a basket of apples
VILLAGER = [
    "................",
    ".....kkkkkk.....",
    "....kWyyyyYk....",
    "...kWyyyyyyYk...",
    "...kySsssssYk...",
    "...kyskssksYk...",
    "...kYssssssYk...",
    "...kYsss33sdYk..",
    "..kkYYkkkkYYkk..",
    ".kIbbwwwwwwbbBk.",
    ".kSkIbbbbbbBkdk.",
    ".kskkrxkgkrxksk.",
    "..kkzzzzzzzNkk..",
    "..kIkznznznNkBk.",
    "..kIbkkkkkkbBk..",
    "..kkkkkkkkkkkk..",
]

# A fisher: a blue hat, a yellow raincoat, a fishing rod and today's fish
FISHER = [
    "..............n.",
    ".....kkkkkk...nl",
    "....kIbbbbBk..nl",
    "...kIbbbbbbBk.nl",
    "..kkBBBBBBBBkknl",
    "...keSssssdek.nl",
    "...kesksskdek.nc",
    "...kessssssek.n.",
    "....kks33skk..n.",
    ".k.kWyyyyyyyYkn.",
    ".kskWyyOyyyyYsn.",
    "kckkyyyOyyyYYkn.",
    "kCckyyyOyyyYYkn.",
    "kcCkkBBkkBBkk.n.",
    "k.k.kEEkkEEk..n.",
    "....kkkk.kkk..n.",
]

# Things you find lying around on the side quests: a lost bag, a frog and a toy boat
LOST_BAG = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "......kkkk......",
    ".....kNNNNk.....",
    "......kYYk......",
    ".....kznnnk.....",
    "....kznnnnNk....",
    "...kznYnnnnNk...",
    "...kznnnnnYNk...",
    "...knnnnnnNNk...",
    "....kNNNNNNk....",
    ".....kkkkkk.....",
    "................",
]
FROG = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "....kkk..kkk....",
    "...kwkfkkgwkk...",
    "...kkkfgggkkk...",
    "...kfggggggGk...",
    "..kfggrrrrggGk..",
    "..kggggggggGGk..",
    "..kGgjjjjjjgGk..",
    ".kgGkjjjjjJkGgk.",
    ".kgk.kkkkkk.kGk.",
    "..k..........k..",
    "................",
]
TOY_BOAT = [
    "................",
    "................",
    "................",
    ".......k........",
    ".......kk.......",
    ".......kwk......",
    ".......kwwk.....",
    ".......kwwlk....",
    ".......kwwwlk...",
    ".......kkkkkkk..",
    "..kkkkkkkkkkkkk.",
    "..kxrrrrrrrrRk..",
    "...krrrrrrRRk...",
    "....kkkkkkkk....",
    "................",
    "................",
]

# Which picture goes with each "look" in phase2/data/people.json ("merchant" and "mage" are other
# names for the shopkeeper and the wizard)
MAP_ART = {
    "farmer": FARMER,
    "shopkeeper": SHOPKEEPER,
    "merchant": SHOPKEEPER,
    "blacksmith": BLACKSMITH,
    "guide": GUIDE,
    "wizard": WIZARD,
    "mage": WIZARD,
    "hunter": HUNTER,
    "kid": KID,
    "cat": CAT,
    "villager": VILLAGER,
    "fisher": FISHER,
    "lost_bag": LOST_BAG,
    "frog": FROG,
    "toy_boat": TOY_BOAT,
}

# ---------------------------------------------------------------------------
# Turning the letters into pictures
# ---------------------------------------------------------------------------

from phase2.art_big import ANGRY_KING, BIG_PEOPLE, KING, KING_BIG, PORTRAITS   # noqa: E402  (the big pictures)

from phase2.art_monsters_a import MONSTERS_A   # noqa: E402
from phase2.art_monsters_b import MONSTERS_B   # noqa: E402
from phase2.art_people_a import PEOPLE_A       # noqa: E402
from phase2.art_people_b import BIG_HERO, PEOPLE_B   # noqa: E402,F401  (BIG_HERO: an experiment, tools/art_preview.py)

# Everyone on the map, whole, at 32 x 32 (2 screen pixels each: 64 pixels, one full map square)
BIG_MAP_ART = dict(BIG_PEOPLE)
BIG_MAP_ART.update(PEOPLE_A)
BIG_MAP_ART.update(PEOPLE_B)
BIG_MAP_ART["merchant"] = BIG_MAP_ART["shopkeeper"]
BIG_MAP_ART["mage"] = BIG_MAP_ART["wizard"]

# Phase 2's monsters at 32 x 32. A monster that isn't here keeps its sprites.py picture
# (the Skeleton and the Ember Skull: they're good as they are).
MONSTER_ART = dict(MONSTERS_A)
MONSTER_ART.update(MONSTERS_B)

BIG_SCALE = 2                   # a 32 x 32 person on the map: 64 pixels, one map square
KING_SCALE = 4                  # the new king has more pixels, so each is smaller: the same size as the Hero's
KING_CARD_SCALE = 5             # ...and a little bigger on story cards
PORTRAIT_SCALE = 5              # a 32 x 32 face fills the dialogue box's 160 x 160 space
GLOW = (190, 110, 255)          # his eyes and gems glow purple,
ANGRY_GLOW = (255, 130, 40)     # and like fire when he's angry
GLOW_PAD = 20                   # room around the king for that glow

_pictures = {}


def make(art, scale):
    """Turn a grid of letters into a picture (like game.make_sprite, with this file's colors)."""
    surf = pygame.Surface((len(art[0]) * scale, len(art) * scale), pygame.SRCALPHA)
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.fill(COLORS[ch], (x * scale, y * scale, scale, scale))
    return surf


def map_art(look):
    """The 16 x 16 letters for a look. A look with no new picture yet keeps its sprites.py one."""
    return MAP_ART.get(look) or sprites.PEOPLE_ART.get(look, FARMER)


def map_picture(look, scale):
    """Someone's small 16 x 16 picture (the map shows big_picture now)."""
    key = ("map", look, scale)
    if key not in _pictures:
        _pictures[key] = make(map_art(look), scale)
    return _pictures[key]


def big_picture(look, scale=BIG_SCALE):
    """Someone on the map, whole, at 32 x 32: one full map square. A look with no big picture yet shows
    its small one, just as big."""
    key = ("big", look, scale)
    if key not in _pictures:
        if look in BIG_MAP_ART:
            _pictures[key] = make(BIG_MAP_ART[look], scale)
        else:
            _pictures[key] = make(map_art(look), scale * 2)
    return _pictures[key]


def monster_picture(app, kind, scale):
    """A monster's new picture in a Phase 2 game, or None (a Classic game, or a monster that keeps its old
    picture). `scale` is the one for the old 16 x 16 pictures, so the monster is as big on the screen as it
    was: the 32 x 32 art gets half of it. Half of an odd scale isn't a whole number of pixels, so that
    picture is painted twice as big and shrunk smoothly."""
    if kind not in MONSTER_ART or not is_phase2(getattr(app, "game", None)):
        return None
    if scale % 2 == 0:
        return make(MONSTER_ART[kind], scale // 2)
    size = len(MONSTER_ART[kind][0]) * scale // 2
    return pygame.transform.smoothscale(make(MONSTER_ART[kind], scale), (size, size))


def portrait(look, scale=PORTRAIT_SCALE):
    """The big face for the dialogue box: 160 x 160 pixels. A look with no face yet shows its map picture."""
    key = ("face", look, scale)
    if key not in _pictures:
        if look in PORTRAITS:
            _pictures[key] = make(PORTRAITS[look], scale)
        else:
            _pictures[key] = make(map_art(look), scale * 2)
    return _pictures[key]


def soft_glow(radius, color, strength):
    """A soft round light that fades out smoothly (the same as game.make_soft_glow)."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    steps = 16
    for i in range(steps):
        t = i / steps
        pygame.draw.circle(surf, color + (int(strength * (t + 1 / steps) ** 1.3),), (radius, radius), int(radius * (1 - t)))
    return surf


def glowing(art, scale, color, pad=GLOW_PAD):
    """A picture with a little light over every white-hot pixel ("L", or "W" when he's angry): his eyes and gems.
    There's `pad` see-through pixels on the left, the right and the top, and none under his feet."""
    body = make(art, scale)
    surf = pygame.Surface((body.get_width() + 2 * pad, body.get_height() + pad), pygame.SRCALPHA)
    surf.blit(body, (pad, pad))
    light = soft_glow(pad - 4, color, 60)
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch in "LW":
                surf.blit(light, light.get_rect(center=(pad + x * scale + scale // 2, pad + y * scale + scale // 2)))
    return surf


def is_phase2(game):
    from phase2.world import Phase2Game
    return isinstance(game, Phase2Game)


def king_look(app):
    """The Shadow King in the throne room, in a Phase 2 game:
    ([his picture, his angry picture], [his glow, his angry glow], how many pixels are under his feet).
    None in a Classic game, which keeps sprites.SHADOW_KING. His size in the fight's rules (throne.KING_W
    and KING_H) is the same for both: only the picture changes."""
    if not is_phase2(getattr(app, "game", None)):
        return None
    if "king" not in _pictures:
        _pictures["king"] = ([glowing(KING, KING_SCALE, GLOW), glowing(ANGRY_KING, KING_SCALE, ANGRY_GLOW)],
                             [soft_glow(150, (170, 90, 255), 105), soft_glow(160, (255, 60, 40), 125)], 0)
    return _pictures["king"]


def king_card(app):
    """The Shadow King on a story card in a Phase 2 game (None in Classic): bigger, and holding his sword."""
    if not is_phase2(getattr(app, "game", None)):
        return None
    if "king card" not in _pictures:
        _pictures["king card"] = glowing(KING_BIG, KING_CARD_SCALE, GLOW)
    return _pictures["king card"]


def check_art():
    """Make sure every picture is a neat rectangle with known colors (like sprites.check_art)."""
    from phase2 import art_big, art_monsters_a, art_monsters_b, art_people_a, art_people_b
    for module in (sys.modules[__name__], art_big, art_monsters_a, art_monsters_b, art_people_a, art_people_b):
        for name, art in list(vars(module).items()):
            if name.isupper() and isinstance(art, list) and art and isinstance(art[0], str):
                width = len(art[0])
                for i, row in enumerate(art):
                    if len(row) != width:
                        raise ValueError("%s row %d is %d wide, expected %d" % (name, i, len(row), width))
                    for ch in row:
                        if ch != "." and ch not in COLORS:
                            raise ValueError("%s uses unknown color letter '%s'" % (name, ch))


check_art()
