"""
DRAWING THE PHASE 2 WORLD (stage 2a): the new lands' looks, waystones, lookouts, gates, hidden
chests, the minimap of the big world and the travel list.

game.App calls these through phase2/__init__.py. They get the App itself ("app"), so they can use
its pictures and painters (app.art, app.paint_grass...). Nothing here changes how Classic looks:
each one does nothing unless the game is a Phase 2 game.

The pictures are grids of letters, like sprites.py (the letters are sprites.COLORS).
"""

import math
import random
import sys

import pygame

import rules
import sprites
from phase2 import ui

TILE = 64

# How the open ground looks in the new lands (colour, and the two colours of its specks), like LAND_GROUND in game.py
NEW_GROUND = {
    "Frost Peaks":      [(228, 236, 246), (206, 218, 236), (248, 251, 255)],    # snow
    "Sunscorch Desert": [(226, 198, 132), (206, 176, 112), (240, 216, 156)],    # hot yellow sand
    "Murk Swamp":       [(84, 112, 76), (70, 94, 64), (100, 128, 86)],          # dark, squelchy mud-grass
}
LOOKS_LIKE = {"Frost Peaks": "Frosty Corner"}       # a new land that paints its trees and rocks like a classic one
SWAMP_WATER = (60, 96, 84)
MINIMAP_BACK = (14, 14, 24)

# A wooden lookout tower on stilts, with a little roof
LOOKOUT = [
    "......kkkk......",
    "....kkRRRRkk....",
    "...kRRrrrrRRk...",
    "..kkkkkkkkkkkk..",
    "...knnnnnnnnk...",
    "...knkwwwwknk...",
    "...knnnnnnnnk...",
    "...kkkkkkkkkk...",
    "....kn....nk....",
    "....knk..knk....",
    "....kn.kk.nk....",
    "....kn.kk.nk....",
    "....knk..knk....",
    "....kn....nk....",
    "...kNNk..kNNk...",
    "................",
]
# A waystone: a standing stone with a rune. Lit ones glow cyan, others are dark.
WAYSTONE = [
    "......kkkk......",
    ".....kllllk.....",
    "....klecceek....",
    "....kleccEek....",
    "....kleeceek....",
    "....klecceek....",
    "....kleccEek....",
    "...kkkkkkkkkk...",
    "...kEEEEEEEEk...",
]
# The great gate in the canyon wall
GATE = [
    "kkkkkkkkkkkkkkkk",
    "kEEEEEEEEEEEEEEk",
    "kEkkkkkkkkkkkkEk",
    "kEknNnNnNnNnNkEk",
    "kEknNnNnNnNnNkEk",
    "kEknNnNnNnNnNkEk",
    "kEkkkkkkkkkkkkEk",
    "kEknNnNyyNnNnkEk",
    "kEknNnykkyNnNkEk",
    "kEknNnyyyyNnNkEk",
    "kEkkkkkkkkkkkkEk",
    "kEknNnNnNnNnNkEk",
    "kEknNnNnNnNnNkEk",
    "kEknNnNnNnNnNkEk",
    "kEkkkkkkkkkkkkEk",
    "kkkkkkkkkkkkkkkk",
]
# A cactus in the desert
CACTUS = [
    ".......kk.......",
    "......kgGk......",
    "......kgGk..kk..",
    "..kk..kgGk.kgGk.",
    ".kgGk.kgGk.kgGk.",
    ".kgGk.kgGkkkgGk.",
    ".kgGkkkgGgggGGk.",
    ".kgGggggGGGGGk..",
    "..kGGGGkgGkkk...",
    "...kkkkkgGk.....",
    "......kgGGk.....",
    "......kgGGk.....",
    ".....kkgGGkk....",
    "....kNNNNNNNk...",
    "................",
    "................",
]


def picture(art, scale=4, swaps=None):
    surf = pygame.Surface((len(art[0]) * scale, len(art) * scale), pygame.SRCALPHA)
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            ch = (swaps or {}).get(ch, ch)
            if ch != ".":
                surf.fill(sprites.COLORS[ch], (x * scale, y * scale, scale, scale))
    return surf


_ART = {}


def art(name):
    if not _ART:
        _ART.update({
            "lookout": picture(LOOKOUT),
            "waystone_lit": picture(WAYSTONE, 3),
            "waystone_dark": picture(WAYSTONE, 3, {"c": "E", "E": "k", "l": "e"}),
            "gate": picture(GATE),
            "cactus": picture(CACTUS, 3),
        })
    return _ART[name]


def _classic(app):
    """game.py itself (to share its table of ground colours), without importing it."""
    return sys.modules[type(app).__module__]


def is_world(app):
    game = getattr(app, "game", None)
    return getattr(game, "phase2", False) and game.world == 1


# ===========================================================================
# The map's tiles
# ===========================================================================

class LazyTiles(dict):
    """The big map has thousands of squares: each one is painted the first time it's on screen."""

    def __init__(self, app):
        super().__init__()
        self.app = app

    def __missing__(self, pos):
        self.app.paint_tile(*pos)
        return dict.__getitem__(self, pos)


def build_tiles(app):
    """Phase 2: set up the tiles to paint later (lazily). Returns True if it did."""
    game = getattr(app, "game", None)
    if not getattr(game, "phase2", False):
        return False
    ground = _classic(app).LAND_GROUND
    for land, colors in NEW_GROUND.items():          # the new lands' ground joins the classic table
        ground.setdefault(land, colors)               # (classic has no lands with these names)
    app.land_of = {(r, c): game.land_name((r, c)) for r in range(game.rows) for c in range(game.cols)}
    app.tiles = LazyTiles(app)
    rng = random.Random(7)
    app.fog_tile = pygame.Surface((TILE, TILE))
    app.fog_tile.fill((14, 14, 24))
    for _ in range(6):
        app.fog_tile.fill((30, 30, 48), (rng.randint(0, 62), rng.randint(0, 62), 2, 2))
    app.phase2_minimap = None
    return True


def paint_tile(app, r, c):
    """Paint one square of the Phase 2 world, or return False to let game.py paint it the classic way."""
    if not is_world(app) or getattr(app, "_phase2_painting", False):
        return False
    game, pos = app.game, (r, c)
    letter = game.map[r][c]
    land = app.land_of.get(pos)
    gate = game.gate_at(pos)
    base = letter
    if letter == "T" and game.chest_hidden(pos) or gate:
        base = "G"                                   # a hidden chest (or the gate) sits on plain ground
    if land == "Sunscorch Desert" and letter in "FX":
        base = "G"                                   # cacti and sandstone go on sand
    if land == "Murk Swamp" and letter == "F":
        base = "G"
    surf = _paint_classic(app, r, c, base, LOOKS_LIKE.get(land, land))
    rng = random.Random(r * 1000 + c * 7 + 11)
    if gate:
        surf.blit(art("gate"), (0, 0))
    elif land == "Sunscorch Desert" and letter == "F":
        surf.blit(art("cactus"), (rng.randint(4, 14), rng.randint(2, 12)))
    elif land == "Sunscorch Desert" and letter == "X":
        surf.blit(app.art["red_rock"], (0, 0))
    elif land == "Murk Swamp" and letter == "F":
        surf.blit(app.art["dead_tree"], (rng.randint(4, 12), rng.randint(4, 12)))
    elif land == "Murk Swamp" and letter == "W":
        surf.fill(SWAMP_WATER)
        for _ in range(5):                           # lily pads and scum
            x, y = rng.randint(6, 52), rng.randint(6, 52)
            pygame.draw.ellipse(surf, rng.choice([(70, 130, 70), (96, 120, 70)]), (x, y, rng.randint(6, 12), rng.randint(4, 8)))
    if pos in game.lookouts:
        surf.blit(art("lookout"), (0, 0))
    if pos in game.waystones:
        lit = pos in game.unlocked_waystones
        stone = art("waystone_lit" if lit else "waystone_dark")
        if lit:
            pygame.draw.circle(surf, (90, 230, 240), (10, 54), 9, 2)
        surf.blit(stone, (-14, 38))
    if letter == "T" and not game.chest_hidden(pos):
        pygame.draw.circle(surf, (255, 214, 90), (52, 12), 6, 2)    # a spotted chest: a little gold ring
    app.tiles[pos] = surf
    return True


def _paint_classic(app, r, c, letter, land):
    """Let game.py paint the square as if it had this letter and was in this land."""
    game, pos = app.game, (r, c)
    old_letter, old_land = game.map[r][c], app.land_of.get(pos)
    game.map[r][c], app.land_of[pos] = letter, land
    app._phase2_painting = True
    try:
        app.paint_tile(r, c)
    finally:
        app._phase2_painting = False
        game.map[r][c], app.land_of[pos] = old_letter, old_land
    return dict.__getitem__(app.tiles, pos) if isinstance(app.tiles, LazyTiles) else app.tiles[pos]


# ===========================================================================
# The minimap: the whole big world, squeezed into the little box
# ===========================================================================

def minimap_color(app, pos):
    game, classic = app.game, _classic(app)
    r, c = pos
    letter = game.map[r][c]
    land = app.land_of.get(pos)
    if game.gate_at(pos):
        return (150, 98, 52)
    if letter == "T" and game.chest_hidden(pos):
        letter = "G"
    if letter == "T":
        return (255, 214, 90)
    if land == "Murk Swamp" and letter == "W":
        return SWAMP_WATER
    color = classic.MINIMAP_COLORS.get(letter, classic.DIM)
    if letter in "MS":
        color = classic.MINE_LOOKS.get(app.mine_theme(pos), classic.MINE_LOOKS["stone"])["rock"]
    if letter in "GF" and land in classic.LAND_GROUND and not (letter == "F" and land not in NEW_GROUND):
        color = classic.LAND_GROUND[land][0]
        if letter == "F":
            color = tuple(max(0, v - 50) for v in color)
    if pos in game.glints and pos not in game.cleared_mines:
        color = (120, 235, 255)
    return color


def minimap_picture(app):
    """The whole world, one pixel a square (painted again only when something on it changes).
    The little map and the big map (phase2/draw_hud.py) both stretch this."""
    game = app.game
    key = (id(game), game.turn, len(game.found_chests), len(game.unlocked_waystones), len(game.gates_open))
    cached = getattr(app, "phase2_minimap", None)
    if not cached or cached[0] != key:
        small = pygame.Surface((game.cols, game.rows))
        for r in range(game.rows):
            for c in range(game.cols):
                small.set_at((c, r), minimap_color(app, (r, c)))
        cached = app.phase2_minimap = (key, small)
    return cached[1]


def draw_minimap(app, x, top, width, bottom, show_view=True):
    """The minimap of the big world (every square is less than 2 pixels, so it's drawn small and stretched).
    Returns True if it drew it."""
    if not is_world(app):
        return False
    game, s, classic = app.game, app.screen, _classic(app)
    small = minimap_picture(app)
    scale = min(width / game.cols, (bottom - top - 22) / game.rows)
    w, h = int(game.cols * scale), int(game.rows * scale)
    app.text(s, "MAP", (x, top), 22, classic.DIM)
    y0 = top + 22
    s.blit(pygame.transform.scale(small, (w, h)), (x, y0))

    def dot(pos, color, size=3):
        px, py = x + int((pos[1] + 0.5) * scale), y0 + int((pos[0] + 0.5) * scale)
        s.fill(color, (px - size // 2, py - size // 2, size, size))

    blink = int(app.time * 3) % 2 == 0
    for spot in game.waystones:
        dot(spot, (90, 230, 240) if spot in game.unlocked_waystones else (60, 70, 90), 3)
    for spot in game.found_chests:
        if game.tile(spot) == "T" and blink:
            dot(spot, (255, 214, 90), 4)
    if show_view:
        cam = pygame.Rect(x + int(app.cam[0] / TILE * scale), y0 + int(app.cam[1] / TILE * scale),
                          int(classic.VIEW_W / TILE * scale), int(classic.VIEW_H / TILE * scale))
        pygame.draw.rect(s, (230, 232, 244), cam, 1)
    if blink:
        dot(game.player.pos, classic.YELLOW, 4)
    return True


# ===========================================================================
# The travel list (SPACE on a lit waystone)
# ===========================================================================

def on_play(app, event):
    """The travel list takes the keys and the mouse while it's open. Returns True if it used the event."""
    game = getattr(app, "game", None)
    if not getattr(game, "travel_open", False):
        return False
    choices = game.travel_choices()
    if not choices:
        game.close_travel()
        return True
    pick = min(getattr(app, "travel_pick", 0), len(choices) - 1)
    rows = getattr(app, "travel_rows", [])
    if event.type == pygame.MOUSEMOTION:
        pick = next((i for i, row in enumerate(rows) if row.collidepoint(event.pos)), pick)
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        hit = next((i for i, row in enumerate(rows) if row.collidepoint(event.pos)), None)
        if hit is not None:
            go(app, choices[hit][1])
        elif rows and not app.travel_box.collidepoint(event.pos):
            game.close_travel()
    elif event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            game.close_travel()
        elif event.key in (pygame.K_UP, pygame.K_w):
            pick = (pick - 1) % len(choices)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            pick = (pick + 1) % len(choices)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            go(app, choices[pick][1])
    app.travel_pick = pick
    return True


def go(app, spot):
    """Travel there, and jump the camera with a quick fade (no sliding across the whole map)."""
    if app.game.travel(spot):
        app.player_px = [spot[1] * TILE, spot[0] * TILE]
        app.camera = app.camera_target()
        app.fade = 0.6
    app.travel_pick = 0


def draw_over(app):
    """Draw the travel list over everything, while it's open."""
    game = getattr(app, "game", None)
    if not getattr(game, "travel_open", False) or app.state != "play":
        return
    classic, s = _classic(app), app.screen
    choices = game.travel_choices()
    pick = min(getattr(app, "travel_pick", 0), max(0, len(choices) - 1))
    app.dim_screen(150)
    box = pygame.Rect(0, 0, 560, 124 + 58 * len(choices))
    box.center = (classic.WIDTH // 2, classic.HEIGHT // 2)
    app.travel_box = box
    app.panel_box(box, (90, 230, 240))
    app.text(s, "Travel by waystone", (box.centerx, box.y + 16), 44, (90, 230, 240), "midtop", shadow=True)
    ui.hints(app, [ui.PICK, ("ENTER", "go"), ui.BACK], (box.centerx, box.y + 78))
    app.travel_rows = []
    for i, (name, spot) in enumerate(choices):
        row = pygame.Rect(box.x + 24, box.y + 104 + i * 58, box.w - 48, 50)
        app.travel_rows.append(row)
        picked = i == pick
        pygame.draw.rect(s, (40, 92, 104) if picked else (36, 48, 66), row, border_radius=10)
        if picked:
            pygame.draw.rect(s, classic.YELLOW, row, 3, border_radius=10)
            tip = row.x + 22 + math.sin(app.time * 6) * 3
            pygame.draw.polygon(s, classic.YELLOW, [(tip - 12, row.centery - 10), (tip - 12, row.centery + 10), (tip, row.centery)])
        land = game.land_name(spot) or ""
        words = name if name == land or not land else "%s  (%s)" % (name, land)
        app.text(s, words, (row.x + 40, row.y + 11), 28, classic.TEXT)
        app.text(s, rules.compass(game.player.pos, spot), (row.right - 14, row.y + 15), 22, classic.DIM, "topright")
