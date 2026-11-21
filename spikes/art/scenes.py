"""Overworld tiles, the cave with parallax, and the Shadow King. All procedural, all original."""
import math
import random

import pygame

import hero
from sf_art import NATIVE, P, TILE, drop_shadow, grid, outline

W, H = NATIVE


def rim(sprite, colour, dx=-1, dy=-1):
    """Rim light: filled pixels whose (dx,dy) neighbour is clear get the light colour."""
    w, h = sprite.get_size()
    out = sprite.copy()
    for y in range(h):
        for x in range(w):
            if sprite.get_at((x, y)).a:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or not sprite.get_at((nx, ny)).a:
                    out.set_at((x, y), colour)
    return out


def speckle(s, rng, colours, n):
    for _ in range(n):
        s.set_at((rng.randrange(s.get_width()), rng.randrange(s.get_height())), P[rng.choice(colours)])


# --- overworld tiles (16x16, max 4 colours each) -----------------------------------------------
def t_grass(seed, flowers=False):
    rng = random.Random(seed)
    s = pygame.Surface((TILE, TILE))
    s.fill(P["moss2"])
    for _ in range(5):                                     # tufts: 2-px "v" in the light green
        x, y = rng.randrange(1, 15), rng.randrange(2, 15)
        s.set_at((x, y), P["moss3"]); s.set_at((x + 1, y - 1), P["moss3"])
    speckle(s, rng, ["moss1"], 4)
    if flowers:
        for _ in range(3):
            x, y = rng.randrange(1, 15), rng.randrange(1, 15)
            s.set_at((x, y), P[rng.choice(["light0", "ink6", "ember3"])])
    return s


def t_path(seed):
    rng = random.Random(seed)
    s = pygame.Surface((TILE, TILE))
    s.fill(P["earth2"])
    speckle(s, rng, ["earth3"], 7)
    speckle(s, rng, ["earth1"], 5)
    return s


def t_water(seed, frame=0):
    rng = random.Random(seed)
    s = pygame.Surface((TILE, TILE))
    s.fill(P["water2"])
    for _ in range(3):
        x, y = rng.randrange(0, 12), rng.randrange(1, 15)
        pygame.draw.line(s, P["water3"], ((x + frame) % 16, y), ((x + frame) % 16 + 3, y))
    speckle(s, rng, ["water1"], 4)
    return s


def t_shore():
    s = t_water(7)
    pygame.draw.rect(s, P["earth3"], (0, 0, 16, 3))
    pygame.draw.line(s, P["water4"], (0, 3), (15, 3))      # foam line
    for x in range(0, 16, 3):
        s.set_at((x, 4), P["water3"])
    return s


def t_cliff_top(seed, lip=False):
    """High ground reads lighter: moss3 base, moss4 tufts, and a lit lip on the edge row."""
    rng = random.Random(seed)
    s = pygame.Surface((TILE, TILE))
    s.fill(P["moss3"])
    for _ in range(5):
        x, y = rng.randrange(1, 15), rng.randrange(2, 15)
        s.set_at((x, y), P["moss4"]); s.set_at((x + 1, y - 1), P["moss4"])
    speckle(s, rng, ["moss2"], 5)
    if lip:
        pygame.draw.line(s, P["moss4"], (0, 14), (15, 14))
        pygame.draw.line(s, P["moss2"], (0, 15), (15, 15))
    return s


def t_cliff_face(seed, row):
    rng = random.Random(seed)
    s = pygame.Surface((TILE, TILE))
    s.fill(P["earth1"] if row == 0 else P["earth0"])
    for x in range(0, 16, 4):                               # vertical strata
        off = rng.randrange(4)
        pygame.draw.line(s, P["earth2"] if row == 0 else P["earth1"], (x + off, 0), (x + off, 15))
    if row == 0:
        pygame.draw.line(s, P["ink0"], (0, 0), (15, 0))
    return s


def t_ground_shadow(seed):
    """The tile under a cliff: grass with a 4-px cast shadow (depth cue)."""
    s = t_grass(seed)
    sh = pygame.Surface((16, 4), pygame.SRCALPHA)
    sh.fill((*P["ink0"], 120))
    s.blit(sh, (0, 0))
    return s


TREE = [
    "..........aaaa..........",
    ".......aaabbbbaa........",
    ".....aabbbcccbbbaa......",
    "....abbcccdddccbbba.....",
    "...abbccdddddccbbbaa....",
    "..abbcccddddcccbbbbba...",
    "..abccccdddcccbbbbbba...",
    ".abbcccccccccbbbbbbbba..",
    ".abbbccccccbbbbbbbbbba..",
    "abbbbbbcccbbbbbbbbbabba.",
    "abbcbbbbbbbbbbbbbaabbba.",
    "abcccbbbbbbbbbbbaabbbba.",
    "abbcbbbbbbbbbbbaaabbbaa.",
    ".abbbbbbbbbbbaaaaabbaa..",
    ".aabbbbbbbaaaaaaaaaaa...",
    "..aaabbbaaaaaaaaaaaa....",
    "....aaaaaaa.aaaaaa......",
    "........aatta...........",
    "..........tt............",
    "..........tT............",
    ".........tTTt...........",
]


def tree():
    s = grid(TREE, {"a": "moss0", "b": "moss1", "c": "moss2", "d": "moss3", "t": "earth1", "T": "earth2"})
    return outline(s)


def rock():
    s = grid(["...aaaa...", "..abbbba..", ".abccbbba.", ".abcbbbbaa", "abbbbbbbba", ".aaaaaaaa."],
             {"a": "ink2", "b": "ink3", "c": "ink5"})
    return outline(s)


def waystone(lit=True):
    s = grid(["..aa..", ".abba.", ".abca.", ".abba.", ".acba.", ".abba.", ".abba.", "aabbaa", "aaaaaa"],
             {"a": "ink2", "b": "ink4", "c": "shadow2" if lit else "ink3"})
    return outline(s)


def gloomling(frame=0):
    """Overworld monster: a small shadow creature with bright eyes. Original. 14x12."""
    s = grid(["....aaaaa.....", "..aabbbbbaa...", ".abbbbbbbbba..", ".abbcbbbcbba..", "abbbcbbbcbbba.",
              "abbbbbbbbbbba.", "abbbbbbbbbbbba", ".abbbbbbbbbba.", ".abababababa..",
              "..a.a.a.a.a..." if frame else ".a.a.a.a.a.a.."],
             {"a": "shadow0", "b": "shadow1", "c": "light1"})
    return outline(s)


def tileset_sheet():
    """The overworld kit on one sheet, 16x16 grid (trees 24x21 on a 2x2 cell)."""
    tiles = [t_grass(1), t_grass(2), t_grass(3, True), t_path(4), t_path(5), t_water(6), t_water(6, 2),
             t_shore(), t_cliff_top(8), t_cliff_face(9, 0), t_cliff_face(10, 1), t_ground_shadow(11)]
    sheet = pygame.Surface((16 * 8, 16 * 4), pygame.SRCALPHA)
    for i, t in enumerate(tiles):
        sheet.blit(t, (16 * (i % 8), 16 * (i // 8)))
    sheet.blit(tree(), (0, 32))
    sheet.blit(rock(), (35, 37))
    sheet.blit(waystone(), (53, 36))
    sheet.blit(gloomling(), (67, 38))
    sheet.blit(gloomling(1), (83, 38))
    return sheet


def overworld(lut=None):
    """A 480x270 sample screen: meadow, a raised plateau with a 2-tile cliff face, a lake.
    lut: a gloom stage remap for the world (tiles, trees, rocks). Characters never get it."""
    from sf_art import apply_lut
    rng = random.Random(3)
    s = pygame.Surface(NATIVE)
    cols, rows = W // TILE, H // TILE + 1
    cliff_row = 5
    for r in range(rows):
        for c in range(cols):
            x, y = c * TILE, r * TILE
            lake = c >= 19 and r >= 11
            if r < cliff_row:
                t = t_cliff_top(c * 31 + r, lip=r == cliff_row - 1)
            elif r in (cliff_row, cliff_row + 1) and not 12 <= c <= 13:
                t = t_cliff_face(c * 7 + r, r - cliff_row)
            elif r == cliff_row + 2 and not 12 <= c <= 13:
                t = t_ground_shadow(c + r)
            elif lake:
                t = t_water(c * 13 + r)
            elif c >= 19 and r == 10:
                t = t_shore()
            elif 12 <= c <= 13 or r == 11 and c < 13:
                t = t_path(c * 3 + r)
            else:
                t = t_grass(c * 17 + r, flowers=rng.random() < 0.12)
            s.blit(t, (x, y))
    for c in (12, 13):                                      # stairs cut into the cliff
        for r in (cliff_row, cliff_row + 1):
            for k in range(0, 16, 4):
                pygame.draw.line(s, P["earth3"], (c * 16, r * 16 + k), (c * 16 + 15, r * 16 + k))
                pygame.draw.line(s, P["earth1"], (c * 16, r * 16 + k + 2), (c * 16 + 15, r * 16 + k + 2))
    world_kit = (lambda spr: apply_lut(spr, lut)) if lut else (lambda spr: spr)
    if lut:
        s = apply_lut(s, lut)
    things = [(world_kit(tree()), x, y) for x, y in ((20, 2), (70, -6), (300, 4), (380, -2), (40, 150), (110, 200),
                                          (250, 120), (60, 230))]
    things += [(world_kit(rock()), 200, 214), (world_kit(rock()), 330, 150), (waystone(), 236, 40)]
    things += [(gloomling(), 150, 140), (gloomling(1), 280, 220)]
    things += [(hero.top_down("down", 1), 200, 166)]
    for spr, x, y in sorted(things, key=lambda t: t[2] + t[0].get_height()):   # y-sort = depth
        drop_shadow(s, x + 2, y + spr.get_height() - 3, spr.get_width() - 4)
        s.blit(spr, (x, y))
    return s


# --- HUD: minimal, inside the play view ---------------------------------------------------------
FONT3x5 = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
           "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
           "8": "111101111101111", "9": "111101111001111", "/": "001001010100100", "x": "000101010101000"}


def tiny_text(s, text, x, y, colour):
    for ch in text:
        bits = FONT3x5[ch]
        for i, b in enumerate(bits):
            if b == "1":
                s.set_at((x + i % 3, y + i // 3), colour)
        x += 4


HEART = [".aa.aa.", "abbabba", "abbbbba", ".abbba.", "..aba..", "...a..."]


def hud(s, hearts=3, of=4, stones=3):
    for i in range(of):
        full = i < hearts
        h = grid(HEART, {"a": "ink0", "b": "ember2" if full else "ink2"})
        s.blit(h, (6 + i * 9, 6))
    st = outline(grid([".a.", "aba", ".a."], {"a": "shadow1", "b": "light1"}))
    s.blit(st, (6, 15))
    tiny_text(s, f"{stones}/7", 13, 16, P["ink6"])


# --- the cave: 5 parallax layers + banded lights ------------------------------------------------
def dither_gradient(size, colours):
    s = pygame.Surface(size)
    w, h = size
    band = h / len(colours)
    for y in range(h):
        i = min(int(y / band), len(colours) - 1)
        s.fill(P[colours[i]], (0, y, w, 1))
        if i + 1 < len(colours) and y > (i + 1) * band - 4:   # 4-row checker dither at each seam
            for x in range(y % 2, w, 2):
                s.set_at((x, y), P[colours[i + 1]])
    return s


def jagged(s, colour, rng, base_y, height, step, top=False):
    pts = [(0, 0 if top else H)]
    x = 0
    while x <= W + step:
        tip = rng.randint(height // 3, height)
        pts += [(x, base_y), (x + step // 2, base_y - tip if not top else base_y + tip)]
        x += step
    pts += [(W + step, base_y), (W + step, 0 if top else H)]
    pygame.draw.polygon(s, P[colour], pts)


def cave_layers(scroll=0):
    rng = random.Random(5)
    far = dither_gradient(NATIVE, ["ink0", "ink1", "shadow0"])
    l1 = pygame.Surface(NATIVE, pygame.SRCALPHA)          # far rock, 0.25x
    jagged(l1, "ink1", rng, 30, 50, 34, top=True)
    jagged(l1, "ink1", rng, 250, 80, 46)
    pygame.draw.rect(l1, P["water0"], (330, 40, 6, 220))   # a far waterfall, barely there
    l2 = pygame.Surface(NATIVE, pygame.SRCALPHA)          # mid pillars, 0.5x
    for x in (40, 170, 300, 420):
        pygame.draw.rect(l2, P["ink2"], (x, 0, 28, H))
        pygame.draw.line(l2, P["ink3"], (x, 0), (x, H))
        for k in range(3):
            pygame.draw.line(l2, P["moss0"], (x + 6 + k * 7, 0), (x + 4 + k * 7, 30 + k * 11))
    play = pygame.Surface(NATIVE, pygame.SRCALPHA)        # the play layer, 1x
    solid = set()
    for c in range(W // 16):
        for r in (15, 16):
            solid.add((c, r))
    for c, r, n in ((3, 11, 6), (12, 8, 5), (21, 12, 7), (24, 6, 6)):
        for k in range(n):
            solid.add((c + k, r))
    for c in range(0, 3):
        for r in range(0, 15):
            solid.add((c, r))
    for (c, r) in solid:
        x, y = c * 16, r * 16
        pygame.draw.rect(play, P["ink3"], (x, y, 16, 16))
        rr = random.Random(c * 97 + r)
        for _ in range(3):
            pygame.draw.line(play, P["ink2"], (x + rr.randrange(16), y + rr.randrange(4, 16)),
                             (x + rr.randrange(16), y + rr.randrange(4, 16)))
        if (c, r - 1) not in solid:                       # lit top edge + moss with drips
            pygame.draw.rect(play, P["moss3"], (x, y, 16, 2))
            pygame.draw.line(play, P["moss4"], (x, y), (x + 15, y))
            for d in range(rr.randrange(3)):
                dx = rr.randrange(16)
                pygame.draw.line(play, P["moss2"], (x + dx, y + 2), (x + dx, y + 3 + rr.randrange(4)))
        if (c - 1, r) not in solid:
            pygame.draw.line(play, P["ink4"], (x, y), (x, y + 15))
        if (c + 1, r) not in solid:
            pygame.draw.line(play, P["ink0"], (x + 15, y), (x + 15, y + 15))
        if (c, r + 1) not in solid and r < 15:
            pygame.draw.line(play, P["ink0"], (x, y + 15), (x + 15, y + 15))
    for r in range(8, 15):                                 # a ladder
        pygame.draw.line(play, P["earth2"], (12 * 16 + 2, r * 16), (12 * 16 + 2, r * 16 + 15))
        pygame.draw.line(play, P["earth2"], (12 * 16 + 12, r * 16), (12 * 16 + 12, r * 16 + 15))
        pygame.draw.line(play, P["earth3"], (12 * 16 + 2, r * 16 + 8), (12 * 16 + 12, r * 16 + 8))
    crystal = outline(grid(["..a..", ".aba.", ".abA.", "abbBa", "abBBa", ".aaa."],
                           {"a": "water2", "b": "water4", "B": "water3", "A": "ink7"}))
    for x, y in ((90, 170), (395, 186), (410, 84)):
        play.blit(crystal, (x, y - 6))
    chest = outline(grid(["aaaaaaaaaa", "abbbbbbbba", "accccccca.", "abbbgbbbba", "abbbbbbbba", "aaaaaaaaaa"],
                         {"a": "earth1", "b": "earth2", "c": "earth3", "g": "light0"}))
    play.blit(chest, (420, 186))
    crawler = outline(rim(grid(["....aaaa....", "..aabbbbaa..", ".abbbbbbbba.", "abbcbbbbcbba",
                                "abbbbbbbbbba", ".a.a.aa.a.a."], {"a": "shadow0", "b": "shadow1", "c": "light1"}),
                          P["shadow2"]))
    play.blit(crawler, (360, 186))
    play.blit(hero.side_view("run", 1), (150, 208))
    fg = pygame.Surface(NATIVE, pygame.SRCALPHA)          # foreground silhouettes, 1.4x
    pygame.draw.polygon(fg, P["ink0"], [(W - 70, H), (W - 40, 200), (W - 20, 215), (W, 180), (W, H)])
    pygame.draw.polygon(fg, P["ink0"], [(60, 0), (70, 30), (78, 12), (90, 46), (100, 0)])
    for k in range(4):
        pygame.draw.line(fg, P["ink0"], (250 + k * 9, 0), (246 + k * 9, 20 + k * 9), 2)
    return [("far 0x", far), ("back rock 0.25x", l1), ("mid 0.5x", l2), ("play 1x", play), ("front 1.4x", fg)]


def cave_lighting(scene, lights, darkness=190):
    """Darkness over everything, cut by banded light pools (3 rings each, no smooth fall-off).
    Pools merge by taking the lowest darkness per pixel, so two lights never cut each other."""
    dark = pygame.Surface(NATIVE, pygame.SRCALPHA)
    dark.fill((*P["ink0"], darkness))
    for (x, y, r) in lights:
        pool = pygame.Surface(NATIVE, pygame.SRCALPHA)
        pool.fill((*P["ink0"], darkness))
        for k, a in ((1.0, darkness * 2 // 3), (0.72, darkness // 3), (0.45, 0)):
            pygame.draw.circle(pool, (*P["ink0"], a), (x, y), int(r * k))
        dark.blit(pool, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    scene.blit(dark, (0, 0))
    return scene


def cave_scene():
    s = pygame.Surface(NATIVE)
    for _, layer in cave_layers():
        s.blit(layer, (0, 0))
    s = cave_lighting(s, [(162, 220, 130), (93, 168, 40), (398, 184, 34), (413, 82, 30), (366, 192, 26)])
    hud(s)                                                 # the HUD is never darkened
    return s


# --- the Shadow King --------------------------------------------------------------------------
def shadow_king():
    """96x128 silhouette: crown of 5 thorns, horned helm, a cloak that frays into smoke. Original."""
    s = pygame.Surface((96, 128), pygame.SRCALPHA)
    body = P["ink0"]
    pygame.draw.polygon(s, body, [(48, 22), (62, 32), (74, 40), (80, 70), (90, 122), (78, 112), (70, 127),
                                  (60, 112), (48, 126), (36, 112), (26, 127), (18, 112), (6, 122), (16, 70),
                                  (22, 40), (34, 32)])
    pygame.draw.ellipse(s, body, (36, 12, 24, 26))         # head
    for i, (x, h) in enumerate(((36, 8), (42, 14), (48, 18), (54, 14), (60, 8))):   # crown thorns
        pygame.draw.polygon(s, body, [(x - 3, 16), (x, 16 - h), (x + 3, 16)])
    pygame.draw.polygon(s, body, [(36, 20), (24, 6), (34, 16)])                      # horns
    pygame.draw.polygon(s, body, [(60, 20), (72, 6), (62, 16)])
    pygame.draw.line(s, body, (86, 30), (86, 127), 3)                                 # his staff
    pygame.draw.polygon(s, body, [(76, 56), (88, 52), (88, 58), (78, 62)])            # the hand on it
    pygame.draw.circle(s, body, (86, 24), 6)
    s = rim(s, P["ember1"], -1, -1)                       # rim light from the red sky behind
    s = rim(s, P["ember2"], 0, -1)
    pygame.draw.circle(s, P["shadow1"], (86, 24), 4)       # the orb that ate the light
    pygame.draw.circle(s, P["shadow2"], (86, 24), 2)
    for x in (43, 52):                                     # the eyes: the one accent
        pygame.draw.rect(s, P["shadow2"], (x, 25, 3, 2))
        s.set_at((x + 1, 25), P["ink7"])
    pygame.draw.line(s, P["shadow1"], (48, 40), (48, 100))  # a sliver of violet inside the cloak
    return s


def throne_scene():
    rng = random.Random(9)
    s = dither_gradient(NATIVE, ["shadow0", "ink1", "ember0", "ember1", "ember2"])
    pygame.draw.circle(s, P["ember2"], (240, 150), 62)     # a dying sun behind his head: a halo
    pygame.draw.circle(s, P["ember3"], (240, 150), 48)
    pygame.draw.circle(s, P["light0"], (240, 150), 34)
    back = pygame.Surface(NATIVE, pygame.SRCALPHA)
    x = 0
    while x < W:                                           # far castle spires, uneven
        h, w = rng.randint(20, 70), rng.choice((10, 14, 18))
        if abs(x - 240) > 70:
            pygame.draw.rect(back, P["ink1"], (x, 210 - h, w, h + 80))
            pygame.draw.polygon(back, P["ink1"], [(x - 2, 210 - h), (x + w // 2, 192 - h), (x + w + 2, 210 - h)])
        x += w + rng.randint(8, 40)
    s.blit(back, (0, 0))
    pygame.draw.rect(s, P["ink0"], (0, 236, W, 40))       # the ground he stands on
    k = shadow_king()
    s.blit(k, (240 - 48, 236 - 126))
    for _ in range(40):                                    # smoke motes rising off the cloak
        x, y = rng.randint(190, 290), rng.randint(90, 236)
        s.set_at((x, y), P[rng.choice(["shadow1", "shadow0", "ink1"])])
    s.blit(hero.side_view("idle"), (90, 206))
    return s
