"""
CAVE EDITOR - draw your own caves, then play them!

Start it with:
    pixi run editor
or open one of your caves straight away:
    python editor.py my_caves/lava_tower.txt

HOW TO USE IT
  Pick a building block on the right (or type its letter), then:
    LEFT mouse button      paint it
    RIGHT mouse button     rub it out (paints air)
    Alt + click            pick up the block under the mouse
    Box                    drag out a whole rectangle of blocks
    Arrow keys, wheel      scroll around the cave
    Drag the window edge   make the editor bigger or smaller (it starts almost as big as your screen)
  Play it!                 drop into your cave and try it (ESC comes back here)
  Can it be beaten?        a robot tries your cave to see if it can be done
  Save                     puts your cave in the my_caves folder. Open one of the caves in
                           the game (levels folder) and Save changes it in the game!
  Save as                  saves a copy in my_caves, with a new name
  Polish                   gets your saved cave ready for Gemini to paint (levels/polish/<cave>/README.txt
                           says how). Press it again once Gemini's picture is in that folder: the game uses it!

Everything is drawn by the game itself (game.py), so your cave looks exactly
the way it will when you play it. Loading, saving and the checks live in
cave_files.py, and the robot lives in cave_solver.py.
"""

import argparse
import json
import math
import os
import subprocess
import sys
import threading
import time

import pygame

import cave_files
import cave_solver
import caves
import game
import rules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "shadowfall", "tools"))
import polish  # noqa: E402  (shadowfall/tools/polish.py: the map and prompt for Gemini, and the import)
from game import TILE, TEXT, DIM, YELLOW, GREEN, RED, ORANGE

# The editor's window can be bigger than the game's. These start the same as the
# game's sizes, and Editor.set_size() changes them when the window opens or is dragged.
VIEW_W, VIEW_H = game.VIEW_W, game.VIEW_H     # the part that shows the cave
WIDTH, HEIGHT = game.WIDTH, game.HEIGHT       # the whole window

# ===========================================================================
# SETTINGS - try changing these!
# ===========================================================================
BIG_WINDOW = True          # True = fill most of the screen. False = the same size as the game
SCREEN_MARGIN = (80, 160)  # room left for the menu bar and the dock (pixels across, pixels down)
SCROLL_SPEED = 16          # how fast the arrow keys scroll (pixels every frame)
WHEEL_BLOCKS = 2           # how many blocks one click of the mouse wheel scrolls
ZOOMS = [1.0, 0.75, 0.5]   # big (just like the game), medium and small
ZOOM_NAMES = {1.0: "big", 0.75: "medium", 0.5: "small"}
IDLE_FPS = 10              # how often the editor redraws while you're in another window
WIDER_BY = 4               # the Wider and Narrower buttons add or take away this many columns
MIN_WIDTH = 12
MAX_WIDTH = 400
UNDO_STEPS = 200           # how many changes Undo remembers
ICON = 42                  # how big the blocks are in the palette
ICON_BG = (24, 26, 38)     # the dark box behind each block in the palette
GRID_COLOR = (255, 255, 255, 36)
TRACK_COLOR = (255, 214, 90)    # a moving platform's track in the editor...
TURN_COLOR = (235, 70, 60)      # ...and the bars at its ends, where it turns around
BUTTON = (58, 62, 88)
BUTTON_HOVER = (78, 84, 118)
BUTTON_ON = (110, 96, 40)
PLAY_GREEN = (46, 128, 70)
ROBOT_BLUE = (48, 92, 150)
BOX_BG = (34, 37, 52)

# ===========================================================================
# THE BUILDING BLOCKS - every letter you can draw a cave with
# ===========================================================================
BLOCKS = {
    ".": ("Air", "Empty space. Paint air to rub things out (the right mouse button does it too)."),
    "#": ("Rock", "Solid rock. You can stand on it, but even a pickaxe can't break it."),
    "B": ("Cracked rock", "Dig through it with your pickaxe, or ground-pound it from above (DOWN in the air)."),
    "*": ("Diamond ore", "The diamond! Dig it out with your pickaxe. Every cave needs one."),
    "s": ("Sun Shard ore", "A golden Sun Shard, for Sunfang's gem. Dig it out like a diamond (Nightfall Hollow's shadow caves)."),
    "=": ("Ledge", "Stand on it. You can jump up through it from below."),
    "-": ("Crumbly ledge", "It shakes and falls a moment after you step on it, then comes back."),
    "H": ("Ladder", "Climb it with UP and DOWN. SPACE jumps off."),
    "V": ("Vine", "Like a ladder that hangs from a branch. Jump into it and press UP to grab it!"),
    "%": ("Climbing wall", "Hold UP to climb it like a ladder. SPACE jumps you off it: a wall jump!"),
    "o": ("Bouncy mushroom", "Land on it and it throws you about 6 blocks up!"),
    "I": ("Slippery ice", "Solid like rock, but slippery: you slide a little before you stop."),
    "^": ("Spikes", "Ouch! They hurt %d. Jump over them." % caves.SPIKE_DAMAGE),
    "A": ("Spike trap", "It pops up and down. Run across while it's down!"),
    "~": ("Lava", "Hot! It hurts %d. Draw it IN the floor row, as a pool to jump over (stack it for a deeper pool)." % caves.LAVA_DAMAGE),
    "!": ("Fire", "Flames on the floor. They hurt %d. Jump over them!" % caves.FIRE_DAMAGE),
    "F": ("Secret wall", "It looks just like rock, but you can walk right through it! Hide a secret room behind it."),
    "P": ("Moving platform", "Slides side to side, and carries you. Draw a row of P's: that's its track. "
                             "It turns around at the ends of the row, never past them. (1 or 2 P's: it stays put.)"),
    "U": ("Up-down platform", "Goes up and down, and carries you. Draw a column of U's: that's its track. "
                              "It turns around at the top and bottom U, never past them. (One row: it stays put.)"),
    "R": ("Swinging vine", "Draw a column of R's under rock: a vine that long hangs from the rock. Jump into it to grab it, "
                           "LEFT and RIGHT swing it higher, and SPACE lets go!"),
    "J": ("Flame jet", "Shoots fire %d blocks up, then stops (with the spike traps). Run past while it's off!" % caves.JET_TALL),
    "L": ("Lever", "Press R next to it: every iron gate in the cave opens. (In the castle it opens the door, too.)"),
    "G": ("Iron gate", "Solid bars, until you pull a lever (L). Put one in front of the diamond!"),
    "M": ("Steam geyser", "Rock with a hole in it. Stand on it: when it puffs, WHOOSH, it throws you about 7 blocks up!"),
    "$": ("Gem", "A glittering gem. Grab it for %d XP." % caves.GEM_XP),
    "T": ("Treasure chest", "Open it with R: food, tools, arrows... maybe even a diamond ring!"),
    "S": ("Start", "Where the Hero climbs in. Every cave needs one (and only one)."),
    "E": ("Exit door", "Walk in to finish the cave. Every cave needs one."),
    "u": ("Healing spring", "Walk into it when you're hurt: it heals you all the way. Then it fills up again."),
    "i": ("Torch", "Castle look only. A flickering torch on the wall, just for looks."),
    "w": ("Window", "Castle look only. A moonlit window, just for looks."),
    "f": ("Banner", "Castle look only. A purple banner, just for looks."),
    # Shadowfall's new blocks (the pygame game plays them as air; the robot knows them)
    "C": ("Checkpoint", "A lantern shrine. Walk past it to light it: you wake up here after a fall."),
    ">": ("One-way door >", "Shut until you touch it from the right (where the arrow points). Then it stays open: "
                            "a shortcut back at the end of a loop."),
    "<": ("One-way door <", "Shut until you touch it from the left (where the arrow points). Then it stays open."),
    "n": ("Shadow thorns", "Black thorns that hurt. The flare (the Sun stone's power) burns them away."),
}
MONSTER_HELP = {
    "z": "Walks at you and bites. Hit it with your sword (R), or jump on its head!",
    "k": "Shoots arrows at you from far away. Get close and hit it!",
    "c": "Comes at you, then goes BOOM! Hit it first, or run!",
    "x": "Hops around while it chases you.",
}
for _letter, _name in caves.CAVE_MONSTERS.items():      # monster names come from caves.py
    BLOCKS[_letter] = (_name, MONSTER_HELP.get(_letter, "A monster! Fight it with your sword (R)."))

# The palette: groups of blocks, 5 to a row
PALETTE = [
    ("Air and rock", ".#B*IF"),
    ("Ledges and climbing", "=-HV%oPURM"),
    ("Danger!", "^A~!J" + cave_files.THORNS),
    ("Gates, doors and lanterns", "LG" + cave_files.DOORS + cave_files.CHECKPOINT),
    ("Treasure, start and exit", "$TSEu"),
    ("Monsters", "".join(caves.CAVE_MONSTERS)),
    ("Castle things", cave_files.CASTLE_ONLY),
]
SHADOWFALL_BLOCKS = cave_files.CHECKPOINT + cave_files.DOORS + cave_files.THORNS


def draw_shadowfall_block(surface, letter, rect):
    """The game draws Shadowfall's new blocks as air, so the editor draws its own picture of them."""
    x, y, w, h = rect
    if letter == cave_files.CHECKPOINT:          # a lantern on a post
        pygame.draw.rect(surface, (70, 56, 44), (x + w * 0.45, y + h * 0.45, w * 0.1, h * 0.55))
        pygame.draw.circle(surface, (255, 200, 90), (x + w / 2, y + h * 0.35), w * 0.22)
        pygame.draw.circle(surface, (255, 245, 200), (x + w / 2, y + h * 0.35), w * 0.1)
    elif letter in cave_files.DOORS:             # a wooden door with an arrow on it
        pygame.draw.rect(surface, (96, 64, 40), (x + w * 0.12, y, w * 0.76, h))
        pygame.draw.rect(surface, (50, 34, 22), (x + w * 0.12, y, w * 0.76, h), max(1, int(w * 0.06)))
        tip, back = (x + w * 0.78, x + w * 0.28) if letter == ">" else (x + w * 0.22, x + w * 0.72)
        pygame.draw.polygon(surface, (240, 230, 200), [(tip, y + h / 2), (back, y + h * 0.25), (back, y + h * 0.75)])
    elif letter == cave_files.THORNS:            # dark purple thorns
        for k in range(3):
            left = x + w * k / 3
            pygame.draw.polygon(surface, (70, 30, 90), [(left, y + h), (left + w / 6, y + h * 0.15), (left + w / 3, y + h)])
            pygame.draw.line(surface, (150, 90, 190), (left + w / 6, y + h * 0.15), (left + w / 6, y + h * 0.6), 1)
TALL = "S" + "".join(caves.CAVE_MONSTERS)      # pictures taller than one block (the Hero and the monsters)


class PlayCave(caves.Cave):
    """A cave to try out. With the castle look it is a castle, so its monsters are shadow monsters, like in the game."""

    def __init__(self, world, mine_pos, text, castle=False):
        self.is_castle = castle             # set first: the monsters are made while the cave is built
        super().__init__(world, mine_pos, text)


class EditorCave(PlayCave):
    """A cave that doesn't mind having no start yet (the Hero just waits off the map)."""
    def find(self, letter):
        try:
            return super().find(letter)
        except ValueError:
            return (-50, -50)


class TestGame(rules.Game):
    """A game just for trying out one cave: when you walk out of it, you're back in the editor."""
    cave_result = None

    def leave_cave(self):
        self.cave_result = self.cave.result
        self.cave = None

    def castle_knockout(self):
        pass                                    # no castle gate to wake up at: getting knocked out ends the test


class Button:
    def __init__(self, label, rect, action, color=BUTTON, size=24, on=None):
        self.label, self.rect, self.action, self.color, self.size = label, pygame.Rect(rect), action, color, size
        self.on = on                            # for buttons that switch something on and off


class Editor:
    def __init__(self, path=None, sound=True):
        self.app = game.App(sound=sound)        # the game draws everything for us
        self.app.allow_tips = False             # no tip bubbles while you test your own cave
        pygame.display.set_caption("Cave Editor")
        self.game_screen = pygame.Surface((game.WIDTH, game.HEIGHT))   # "Play it!" draws the game here...
        self.game_overlay = self.app.overlay                          # ...then it is stretched to fit the window
        self.world = self.app.game              # the editor's cave lives in this game
        self.big_views = {}
        self.selected = "#"
        self.grid = True
        self.box_mode = False
        self.zoom = None                        # None = pick the zoom that fits the whole cave
        self.undo_list, self.redo_list = [], []
        self.stroke = None                      # what the mouse is painting right now
        self.dragging_bar = None
        self.modal = None                       # a box on top of everything: open, name, yes/no, message
        self.message, self.message_color, self.message_time = "", TEXT, 0.0
        self.robot = None                       # the "Can it be beaten?" robot while it thinks
        self.trail, self.stuck_at = [], None    # what the robot found
        self.playing = False
        self.running = True
        self.hover = None
        self.icons_theme = None
        self.palette_spots = []
        self.cam = [0, 0]
        self.set_size(*self.starting_size())
        if path:
            self.open_file(path)
        else:
            self.new_cave()

    # ----- the window -----------------------------------------------------------

    def starting_size(self):
        """As big as the screen allows (but never smaller than the game)."""
        if not BIG_WINDOW:
            return game.WIDTH, game.HEIGHT
        try:
            screen_w, screen_h = pygame.display.get_desktop_sizes()[0]
        except (AttributeError, IndexError, pygame.error):
            return game.WIDTH, game.HEIGHT
        return screen_w - SCREEN_MARGIN[0], screen_h - SCREEN_MARGIN[1]

    def set_size(self, w, h):
        """Make the window w by h. The cave part grows; the blocks panel and the buttons stay the same size."""
        global VIEW_W, VIEW_H, WIDTH, HEIGHT
        WIDTH, HEIGHT = max(w, game.WIDTH), max(h, game.HEIGHT)
        VIEW_W, VIEW_H = WIDTH - game.PANEL_W, HEIGHT - game.LOG_H
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.view = pygame.Surface((VIEW_W, VIEW_H))
        self.overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        if not self.playing:
            self.use_editor_screen()
        self.big_views = {}
        self.make_buttons()
        if hasattr(self, "rows"):
            self.clamp_camera()

    def use_editor_screen(self):
        self.app.screen, self.app.overlay = self.screen, self.overlay

    def use_game_screen(self):
        self.app.screen, self.app.overlay = self.game_screen, self.game_overlay

    def game_area(self):
        """Where the game goes in the window when you play your cave: as big as fits, in the middle."""
        scale = min(WIDTH / game.WIDTH, HEIGHT / game.HEIGHT)
        area = pygame.Rect(0, 0, round(game.WIDTH * scale), round(game.HEIGHT * scale))
        area.center = (WIDTH // 2, HEIGHT // 2)
        return area

    def to_game(self, event):
        """Mouse spots in the big window, turned into spots in the game's smaller picture."""
        if not hasattr(event, "pos"):
            return event
        area = self.game_area()
        x = (event.pos[0] - area.x) * game.WIDTH / area.w
        y = (event.pos[1] - area.y) * game.HEIGHT / area.h
        info = dict(event.__dict__, pos=(int(x), int(y)))
        return pygame.event.Event(event.type, info)

    # ----- the cave -----------------------------------------------------------

    def set_cave(self, theme, rows, name=None, path=None, source=None, settings=()):
        self.theme = theme
        self.rows = [list(row) for row in rows]
        self.name, self.path, self.source = name, path, source
        self.settings = list(settings)          # its other setting lines, like "lava rises: yes"
        self.ok_to_save_over = None             # a game cave you said yes to saving over
        self.saved = self.snapshot() if path else None
        self.undo_list, self.redo_list = [], []
        self.cam = [0, 0]
        self.hover = None
        self.clear_robot()
        self.rebuild()

    def new_cave(self):
        self.set_cave("moss", cave_files.new_cave_rows(), source="a new cave")
        self.say("A new cave! Paint with the left mouse button, rub out with the right one.")

    def snapshot(self):
        return (self.theme, tuple("".join(row) for row in self.rows))

    def unsaved(self):
        return self.snapshot() != self.saved

    def text_rows(self):
        return ["".join(row) for row in self.rows]

    @property
    def width(self):
        return len(self.rows[0])

    @property
    def height(self):
        return len(self.rows)

    def rebuild(self):
        """Paint the whole cave again (after loading it, or a new look or size)."""
        if self.icons_theme != self.theme:
            self.make_icons()
        self.cave = EditorCave(self.world, (0, 0), cave_files.cave_text(self.theme, self.text_rows(), self.settings),
                               castle=self.theme == "castle")
        self.cave.clock = caves.TRAP_DOWN * 0.6
        self.world.cave = self.cave
        self.app.build_cave_tiles(self.cave)
        self.app.motes = []
        self.needs_rebuild = False
        self.clamp_camera()

    def show_tile(self, r, c):
        """Show one changed block, without painting the whole cave again."""
        cave, letter = self.cave, self.rows[r][c]
        cave.monsters = [m for m in cave.monsters if m.spawn != (r, c)]
        if letter in caves.CAVE_MONSTERS:
            cave.map[r][c] = "."
            cave.add_monster(caves.CAVE_MONSTERS[letter], r, c, spawn=(r, c))
        else:
            cave.map[r][c] = letter
        if letter == "S":
            cave.you.x, cave.you.y = c + (1 - caves.PLAYER_W) / 2, r + 1 - caves.PLAYER_H
        elif not any("S" in row for row in self.rows):
            cave.you.x, cave.you.y = -50, -50               # no start: the Hero waits off the map
        if letter in caves.PLATFORMS or cave.platforms:     # moving platforms: read them all again from the drawing
            cave.platforms = caves.find_platforms([list(row) for row in self.rows])
            if letter in caves.PLATFORMS:
                cave.map[r][c] = "."
        if letter == caves.SWINGING_VINE or cave.swings:    # swinging vines too
            cave.swings = caves.find_swings([list(row) for row in self.rows])
            if letter == caves.SWINGING_VINE:
                cave.map[r][c] = "."
        cave.dirty.add((r, c))
        if c == 0 or self.theme == "castle":
            self.needs_rebuild = True                       # daylight and castle walls need a full repaint

    def set_tile(self, r, c, letter):
        if not (0 <= r < self.height and 0 <= c < self.width) or self.rows[r][c] == letter:
            return
        if letter in "SE":                                  # only one start and one exit: move the old one
            for rr, cc in cave_files.find_all(self.rows, letter):
                self.rows[rr][cc] = "."
                self.show_tile(rr, cc)
        self.rows[r][c] = letter
        self.show_tile(r, c)

    def remember(self):
        """Remember the cave before a change, so Undo can bring it back."""
        self.undo_list.append(self.snapshot())
        self.undo_list = self.undo_list[-UNDO_STEPS:]
        self.redo_list = []
        self.clear_robot()

    def go_back_to(self, snap):
        self.theme = snap[0]
        self.rows = [list(row) for row in snap[1]]
        self.rebuild()

    def undo(self):
        if not self.undo_list:
            return self.say("Nothing to undo.")
        self.redo_list.append(self.snapshot())
        self.go_back_to(self.undo_list.pop())
        self.clear_robot()

    def redo(self):
        if not self.redo_list:
            return self.say("Nothing to redo.")
        self.undo_list.append(self.snapshot())
        self.go_back_to(self.redo_list.pop())
        self.clear_robot()

    # ----- the buttons ---------------------------------------------------------

    def make_buttons(self):
        y1, y2 = VIEW_H + 10, VIEW_H + 52
        self.buttons = []

        def row(y, items, x=12):
            for label, w, action, *extra in items:
                self.buttons.append(Button(label, (x, y, w, 36), action, *extra))
                x += w + 8
            return x

        row(y1, [("New", 76, self.ask_new), ("Open", 84, self.ask_open), ("Save", 80, self.save),
                 ("Save as", 100, self.ask_name), ("Undo", 80, self.undo), ("Redo", 80, self.redo)])
        self.play_button = Button("Play it!", (580, y1, 150, 36), self.play, PLAY_GREEN, 28)
        self.robot_button = Button("Can it be beaten?", (738, y1, 210, 36), self.start_robot, ROBOT_BLUE)
        self.buttons += [self.play_button, self.robot_button]
        row(y2, [("Look", 170, self.next_theme), ("Height", 126, self.change_height),
                 ("Wider", 84, self.wider), ("Narrower", 110, self.narrower),
                 ("Box", 70, self.toggle_box, BUTTON, 24, lambda: self.box_mode),
                 ("Grid", 70, self.toggle_grid, BUTTON, 24, lambda: self.grid),
                 ("Zoom", 140, self.next_zoom), ("Polish", 96, self.polish)])

    def button_label(self, button):
        if button.label == "Look":
            return "Look: %s" % self.theme
        if button.label == "Height":
            return "Height: %d" % self.height
        if button.label == "Zoom":
            return "Zoom: %s" % ZOOM_NAMES[self.zoom_level()]
        return button.label

    # ----- palette pictures, painted by the game itself -------------------------

    def make_icons(self):
        """Build a little cave with every block in it, let the game draw it, and cut out each block."""
        letters = [letter for _, group in self.palette_groups() for letter in group]
        spacing, floor = 3, 7
        width = 2 + spacing * len(letters)
        rows = [["#"] * width] + [["#"] + ["."] * (width - 2) + ["#"] for _ in range(floor - 1)] + [["#"] * width]
        spots = {}
        for i, letter in enumerate(letters):
            c = 2 + spacing * i
            r = floor if letter == "~" else floor - 1
            rows[r][c] = letter
            spots[letter] = (r, c)
        sample = EditorCave(self.world, (0, 0), cave_files.cave_text(self.theme, ["".join(row) for row in rows], self.settings),
                            castle=self.theme == "castle")
        sample.clock = caves.TRAP_DOWN + 0.03            # spike traps halfway up, so they look different from spikes
        for platform in sample.platforms:                # moving platforms stand still for their picture (arrows and all)
            platform.where = lambda clock, p=platform: (float(p.c), float(p.r))
            platform.high = platform.low + 1
        self.world.cave = sample
        self.app.build_cave_tiles(sample)
        for spot in spots.values():                      # no grass, vines or cobwebs in the pictures: just the block
            self.app.cave_decor.pop(spot, None)
        self.app.motes = []                              # and no fireflies or sparkles flying in front of them
        # SRCALPHA keeps the picture solid. Without it, some computers (like a Mac) leave a see-through
        # hole wherever the game draws a sprite on it, and the chest, ledges and monsters look empty.
        picture = pygame.Surface((width * TILE, (floor + 1) * TILE), pygame.SRCALPHA)
        self.draw_game_cave(picture, (0, 0), sample)
        self.icons = {}
        for letter, (r, c) in spots.items():
            x, y, w, h = self.crop_box(letter)
            part = pygame.Rect(c * TILE + x, r * TILE + y, w, h).clip(picture.get_rect())
            image = picture.subsurface(part).copy()
            if letter == ".":
                pygame.draw.rect(image, (230, 230, 240), image.get_rect().inflate(-10, -10), 2, border_radius=6)
            if letter in SHADOWFALL_BLOCKS:
                draw_shadowfall_block(image, letter, image.get_rect())
            if letter == caves.SECRET:                   # a secret wall: rock with a question mark
                self.app.text(image, "?", (image.get_width() / 2, image.get_height() / 2), 44, (200, 170, 255),
                              "center", shadow=True)
            scale = min(ICON / image.get_width(), ICON / image.get_height())
            self.icons[letter] = pygame.transform.smoothscale(
                image, (max(1, round(image.get_width() * scale)), max(1, round(image.get_height() * scale))))
            self.icons[letter + "big"] = image                  # full size, for the mouse pointer
        self.icons_theme = self.theme
        self.app.motes = []

    def crop_box(self, letter):
        """Which part around a block to cut out for its palette picture."""
        if letter == "E" and self.theme == "castle":
            return (-50, -200, TILE + 100, 264)                # the great throne room door
        if letter == "E":
            return (-4, -20, TILE + 8, TILE + 20)               # the door, and EXIT written above it
        if letter in TALL:
            return (0, -22, TILE, TILE + 22)
        if letter == "w":
            return (0, 0, TILE, 100)
        return (0, 0, TILE, TILE)

    def palette_groups(self):
        return [(name, group) for name, group in PALETTE if group != cave_files.CASTLE_ONLY or self.theme == "castle"]

    def draw_game_cave(self, surface, cam, cave=None):
        """Let the game draw the cave onto any size of picture."""
        app = self.app
        if cave is not None:
            self.world.cave = cave
        old = game.VIEW_W, game.VIEW_H
        game.VIEW_W, game.VIEW_H = surface.get_size()      # the game only draws what fits in its view
        app.cam = (int(cam[0]), int(cam[1]))
        try:
            app.draw_cave(surface)
        finally:
            game.VIEW_W, game.VIEW_H = old
            self.world.cave = self.cave if hasattr(self, "cave") else cave

    # ----- zoom and scrolling ------------------------------------------------

    def zoom_level(self):
        if self.zoom:
            return self.zoom
        fits = [z for z in ZOOMS if self.height * TILE * z <= VIEW_H]   # the biggest that shows the whole height
        return fits[0] if fits else ZOOMS[-1]

    def next_zoom(self):
        now = self.zoom_level()
        self.zoom = ZOOMS[(ZOOMS.index(now) + 1) % len(ZOOMS)]
        self.clamp_camera()

    def seen_size(self):
        """How much of the cave fits on the screen, in game pixels."""
        z = self.zoom_level()
        return VIEW_W / z, VIEW_H / z

    def clamp_camera(self):
        seen_w, seen_h = self.seen_size()
        self.cam[0] = int(min(max(0, self.cam[0]), max(0, self.width * TILE - seen_w)))
        self.cam[1] = int(min(max(0, self.cam[1]), max(0, self.height * TILE - seen_h)))

    def tile_at(self, pos):
        """Which block of the cave is under the mouse (or None)."""
        x, y = pos
        if not (0 <= x < VIEW_W and 0 <= y < VIEW_H):
            return None
        z = self.zoom_level()
        r, c = int((y / z + self.cam[1]) // TILE), int((x / z + self.cam[0]) // TILE)
        if 0 <= r < self.height and 0 <= c < self.width:
            return (r, c)
        return None

    def on_screen(self, r, c):
        z = self.zoom_level()
        return ((c * TILE - self.cam[0]) * z, (r * TILE - self.cam[1]) * z)

    def scrollbars(self):
        """The bars at the bottom and right of the cave that show where you are."""
        seen_w, seen_h = self.seen_size()
        bars = {}
        if self.width * TILE > seen_w:
            track = pygame.Rect(0, VIEW_H - 12, VIEW_W, 12)
            w = max(40, VIEW_W * seen_w / (self.width * TILE))
            x = (VIEW_W - w) * self.cam[0] / (self.width * TILE - seen_w)
            bars["x"] = (track, pygame.Rect(x, VIEW_H - 11, w, 10))
        if self.height * TILE > seen_h:
            track = pygame.Rect(VIEW_W - 12, 0, 12, VIEW_H - 12)
            h = max(40, (VIEW_H - 12) * seen_h / (self.height * TILE))
            y = (VIEW_H - 12 - h) * self.cam[1] / (self.height * TILE - seen_h)
            bars["y"] = (track, pygame.Rect(VIEW_W - 11, y, 10, h))
        return bars

    def drag_bar(self, axis, pos):
        seen_w, seen_h = self.seen_size()
        track, thumb = self.scrollbars()[axis]
        if axis == "x":
            t = (pos[0] - thumb.w / 2) / max(1, VIEW_W - thumb.w)
            self.cam[0] = t * (self.width * TILE - seen_w)
        else:
            t = (pos[1] - thumb.h / 2) / max(1, VIEW_H - 12 - thumb.h)
            self.cam[1] = t * (self.height * TILE - seen_h)
        self.clamp_camera()

    # ----- the look, the height and the width -----------------------------------

    def next_theme(self, step=1):
        self.remember()
        themes = cave_files.THEMES
        self.theme = themes[(themes.index(self.theme) + step) % len(themes)]
        if self.selected in cave_files.CASTLE_ONLY and self.theme != "castle":
            self.selected = "#"
        self.rebuild()
        self.say("Now it looks like a %s cave." % self.theme if self.theme != "castle" else "Now it looks like the castle.")

    def change_height(self):
        """Switch between 14 and 20 rows tall. Rows are added or taken away just under the ceiling."""
        self.remember()
        heights = cave_files.HEIGHTS
        goal = next((h for h in heights if h > self.height), heights[0])
        if goal > self.height:
            added = goal - self.height
            edge = self.rows[1] if self.height > 2 else self.rows[0]
            for _ in range(added):
                self.rows.insert(1, [edge[0]] + ["."] * (self.width - 2) + [edge[-1]])
            self.say("Taller! I added %d rows near the top." % added)
        else:
            gone = self.height - goal
            del self.rows[1:1 + gone]
            self.say("Shorter! I took %d rows off the top (Undo puts them back)." % gone)
        self.cam[1] = 0
        self.rebuild()

    def wider(self):
        if self.width + WIDER_BY > MAX_WIDTH:
            return self.say("That's as wide as a cave can get!", ORANGE)
        self.remember()
        last = self.height - 1
        for r, row in enumerate(self.rows):
            fill = "#" if r in (0, last) else "."
            row[-1:-1] = [fill] * WIDER_BY                  # just before the right wall
        self.rebuild()
        self.say("Wider! %d more columns on the right." % WIDER_BY)

    def narrower(self):
        if self.width - WIDER_BY < MIN_WIDTH:
            return self.say("That's as narrow as a cave can get!", ORANGE)
        self.remember()
        for row in self.rows:
            del row[-1 - WIDER_BY:-1]
        self.rebuild()
        self.say("Narrower! %d columns gone from the right (Undo brings them back)." % WIDER_BY)

    def toggle_box(self):
        self.box_mode = not self.box_mode
        self.say("Box: drag out a rectangle of blocks." if self.box_mode else "Paint: one block at a time.")

    def toggle_grid(self):
        self.grid = not self.grid

    # ----- loading and saving ---------------------------------------------------

    def check_first(self, what, then):
        """If the cave has changes that aren't saved, ask before throwing them away."""
        if self.unsaved() and self.undo_list:
            self.modal = {"kind": "confirm", "text": "Your cave has changes that aren't saved. %s anyway?" % what,
                          "yes": then}
        else:
            then()

    def ask_new(self):
        self.check_first("Start a new cave", self.new_cave)

    def ask_open(self):
        items = [("header", "Your caves (in the my_caves folder)", None)]
        mine = cave_files.my_caves()
        items += [("mine", name, path) for name, path in mine] or [("note", "None yet: save one!", None)]
        items += [("header", "Caves in the game (Save changes them in the game!)", None)]
        items += [("level", name, path) for name, path in cave_files.game_levels()]
        self.modal = {"kind": "open", "items": items, "scroll": 0}

    def open_item(self, kind, name, value):
        def load():
            self.open_file(value)               # every cave in the list is a file: yours, or one of the game's
        self.modal = None
        self.check_first("Open another cave", load)

    def open_file(self, path):
        if not os.path.exists(path):                    # a new cave, with this name
            self.new_cave()
            self.name, self.path = cave_files.nice_name(path), os.path.abspath(path)
            return self.say("A new cave! Save puts it in %s" % path)
        try:
            theme, rows, notes = cave_files.load_cave(path)
            settings = cave_files.load_settings(path)
        except OSError as problem:
            self.new_cave()
            return self.say("I couldn't open %s (%s)." % (path, problem.strerror), RED)
        name = cave_files.nice_name(path)
        for line in settings:                   # the game's caves say their name inside: "name: The Vine Garden"
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip() or name
        self.set_cave(theme, rows, name=name, path=os.path.abspath(path), source=name, settings=settings)
        if notes:
            self.saved = None
        if cave_files.is_game_level(path) and not notes:
            notes = ["It's in the game: Save changes it there (Save as makes your own copy)."]
        self.say("Opened %s." % name + (" " + " ".join(notes) if notes else ""), ORANGE if notes else TEXT)

    def save(self):
        if not self.path:
            self.ask_name()
        elif cave_files.is_game_level(self.path) and self.ok_to_save_over != self.path:
            path = self.path

            def yes():
                self.ok_to_save_over = path     # only ask once for each cave
                self.write(path)
            self.modal = {"kind": "confirm", "yes": yes,
                          "text": "%s is in the game. Save over it? The game plays your new version "
                                  "the next time it starts. (Save as keeps the game's one as it is.)" % self.name}
        else:
            self.write(self.path)

    def ask_name(self):
        self.modal = {"kind": "name", "text": self.name or ""}
        pygame.key.start_text_input()

    def name_done(self):
        name = self.modal["text"].strip()
        if not name:
            return
        path = os.path.join(cave_files.MY_CAVES_FOLDER, cave_files.file_name(name))
        self.modal = None
        if self.path and cave_files.is_game_level(self.path):
            # your own copy of a game cave: it's named after its file, not "name: ..." inside it
            self.settings = [line for line in self.settings if not line.startswith("name:")]
        if os.path.exists(path) and path != self.path:
            self.modal = {"kind": "confirm", "text": "There's already a cave called '%s'. Save over it?"
                          % cave_files.nice_name(path), "yes": lambda: self.write(path)}
        else:
            self.write(path)

    def write(self, path):
        name = self.name if cave_files.is_game_level(path) else cave_files.nice_name(path)
        try:
            path = cave_files.write_cave(path, self.theme, self.text_rows(), self.settings)
        except OSError as problem:
            return self.say("I couldn't save it (%s)." % problem.strerror, RED)
        self.name, self.path, self.source = name, path, name
        self.saved = self.snapshot()
        if cave_files.is_game_level(path):
            self.say("Saved in the game! (%s) Start the game to play it." % cave_files.short_path(path), GREEN)
        else:
            self.say("Saved! It's in %s" % cave_files.short_path(path), GREEN)

    # ----- Polish: Gemini paints the cave ------------------------------------------

    def polish(self):
        """Make the map and prompt for Gemini, or bring in the picture Gemini made."""
        if not self.path or self.unsaved():
            return self.say("Save your cave first, then Polish it.", ORANGE)
        if polish.dropped(self.path):
            ok, message = polish.import_painting(self.path, self.text_rows())
            if not ok:
                return self.say(message, RED)
            polish.export(self.path, self.theme, self.text_rows(), self.settings)
            return self.say(message, GREEN)
        folder = polish.export(self.path, self.theme, self.text_rows(), self.settings)
        self.say("Ready for Gemini! Read README.txt in %s" % polish.short(folder), GREEN)

    # ----- Play it! ---------------------------------------------------------------

    def play(self):
        problems = [text for how_bad, text in cave_files.check_cave(self.theme, self.text_rows()) if how_bad == "must"]
        if problems:
            return self.say(problems[0], ORANGE)
        app = self.app
        test = TestGame(app.name_input or "Hero")
        test.story.clear()                      # no story cards: straight into the cave
        test.take_effects()
        cave = PlayCave(test, (0, 0), cave_files.cave_text(self.theme, self.text_rows(), self.settings),
                        castle=self.theme == "castle")
        test.cave = cave
        test.log("Testing your cave! Press ESC to go back to the editor.", "quest")
        app.game = test
        app.reset_visuals()
        app.state = "play"                      # the game sees the cave and climbs down into it
        self.playing = True
        self.use_game_screen()                  # the game draws at its own size; we stretch it to fit

    def play_step(self, dt, events):
        app, test = self.app, self.app.game
        for event in events:
            if event.type == pygame.QUIT:
                return self.stop_playing("Back in the editor.", then_quit=True)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return self.stop_playing("Back in the editor.")
            if event.type == pygame.VIDEORESIZE:
                self.set_size(event.w, event.h)
                continue
            app.handle_event(self.to_game(event))
        app.update(dt)
        if test.cave is None:
            if test.cave_result == "exit":
                return self.stop_playing("You made it through the EXIT! Nice cave!", GREEN)
            return self.stop_playing("You walked back out the way you came in.")
        if app.state == "end" or test.over:
            return self.stop_playing("The Hero got knocked out! Maybe make it a little easier?", ORANGE)
        app.draw()
        box = pygame.Rect(0, 0, 560, 34)
        box.midtop = (game.VIEW_W // 2, 8)
        self.panel(box, YELLOW, surface=self.game_screen)
        app.text(self.game_screen, "Testing your cave!  ESC = back to the editor", box.center, 24, YELLOW, "center")
        area = self.game_area()
        self.screen.fill(game.BG)
        if area.size == self.game_screen.get_size():
            self.screen.blit(self.game_screen, area)
        else:
            self.screen.blit(pygame.transform.smoothscale(self.game_screen, area.size), area)

    def stop_playing(self, message, color=TEXT, then_quit=False):
        if hasattr(self.app, "music"):
            self.app.music.play(None, False)    # the cave's music fades out...
        pygame.mixer.stop()                     # ...and no sounds are left playing in the editor
        self.app.game = self.world
        self.app.reset_visuals()
        self.app.state = "editor"
        self.playing = False
        self.use_editor_screen()
        pygame.display.set_caption("Cave Editor")
        self.rebuild()
        self.say(message, color)
        if then_quit:
            self.ask_quit()

    # ----- Can it be beaten? (the robot) ---------------------------------------------

    def start_robot(self):
        if not cave_files.can_play(self.theme, self.text_rows()):
            return self.say("Put a start (S) in first!", ORANGE)
        text = cave_files.cave_text(self.theme, self.text_rows(), self.settings)
        here = os.path.dirname(os.path.abspath(__file__))
        process = subprocess.Popen([sys.executable, os.path.join(here, "cave_solver.py"), "--json"], cwd=here,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.robot = {"process": process, "started": time.time(), "answer": None}
        threading.Thread(target=self.wait_for_robot, args=(self.robot, text), daemon=True).start()
        self.clear_robot(keep_running=True)
        self.modal = {"kind": "robot"}

    def wait_for_robot(self, robot, text):
        robot["answer"] = robot["process"].communicate(text)

    def stop_robot(self):
        if self.robot:
            self.robot["process"].kill()
        self.robot, self.modal = None, None
        self.say("The robot stopped.")

    def robot_finished(self):
        out, err = self.robot["answer"]
        self.robot = None
        try:
            result = json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            result = {"error": (err.strip().splitlines() or ["it didn't say why"])[-1]}
        if result.get("error"):
            self.modal = {"kind": "message", "lines": ["The robot got confused:", result["error"]]}
            return
        self.trail = result["trail"]
        self.stuck_at = result["stuck_at"]
        lines = cave_solver.say(result)
        if self.trail:
            lines.append("The yellow dots show the way the robot went.")
        if self.stuck_at:
            lines.append("The red X is the closest it got.")
        lines.append("(The robot doesn't count monsters: beating those is up to you!)")
        self.modal = {"kind": "message", "lines": lines,
                      "good": bool(result["diamond"] is not False and result["exit"] is not False)}

    def clear_robot(self, keep_running=False):
        self.trail, self.stuck_at = [], None
        if self.robot and not keep_running:
            self.robot["process"].kill()
            self.robot = None

    # ----- every frame ------------------------------------------------------------

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            # In another window (or hidden)? Then the editor rests, so it doesn't slow your computer down.
            fps = game.FPS if pygame.key.get_focused() or self.robot else IDLE_FPS
            dt = min(clock.tick(fps) / 1000.0, 0.1)
            self.step(dt, pygame.event.get())
            pygame.display.flip()
        if self.robot:
            self.robot["process"].kill()
        pygame.quit()

    def step(self, dt, events):
        if self.playing:
            return self.play_step(dt, events)
        self.app.time += dt                     # lava waves, twinkling diamonds and spike traps keep moving
        self.cave.clock += dt
        for event in events:
            self.handle(event)
        if self.robot and self.robot["answer"] is not None:
            self.robot_finished()
        if not self.modal:
            self.scroll_with_keys()
        if not self.playing:
            self.draw()

    def scroll_with_keys(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * SCROLL_SPEED
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * SCROLL_SPEED
        if dx or dy:
            z = self.zoom_level()
            self.cam[0] += dx / z
            self.cam[1] += dy / z
            self.clamp_camera()

    def say(self, text, color=TEXT):
        self.message, self.message_color, self.message_time = text, color, time.time()

    def ask_quit(self):
        if self.unsaved() and self.undo_list:
            self.modal = {"kind": "confirm", "text": "Your cave isn't saved. Quit anyway?", "yes": self.quit}
        else:
            self.quit()

    def quit(self):
        self.running = False

    # ----- the mouse and the keyboard -----------------------------------------------

    def handle(self, event):
        if event.type == pygame.QUIT:
            return self.ask_quit()
        if event.type == pygame.VIDEORESIZE:            # you dragged the window bigger or smaller
            return self.set_size(event.w, event.h)
        if self.modal:
            return self.handle_modal(event)
        mods = pygame.key.get_mods()
        command = mods & (pygame.KMOD_CTRL | pygame.KMOD_META)
        if event.type == pygame.KEYDOWN:
            if command and event.key == pygame.K_z:
                self.redo() if mods & pygame.KMOD_SHIFT else self.undo()
            elif command and event.key == pygame.K_y:
                self.redo()
            elif command and event.key == pygame.K_s:
                self.ask_name() if mods & pygame.KMOD_SHIFT else self.save()
            elif command and event.key == pygame.K_o:
                self.ask_open()
            elif command and event.key == pygame.K_n:
                self.ask_new()
            elif event.key == pygame.K_F5:
                self.play()
            elif event.key == pygame.K_ESCAPE:
                self.ask_quit()
        elif event.type == pygame.TEXTINPUT and not command:
            if event.text in self.palette_letters():        # type a block's letter to pick it
                self.pick(event.text)
        elif event.type == pygame.MOUSEWHEEL:
            if mods & pygame.KMOD_SHIFT:
                self.cam[1] -= event.y * WHEEL_BLOCKS * TILE
            else:
                self.cam[0] += (event.x - event.y) * WHEEL_BLOCKS * TILE
            self.clamp_camera()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 2, 3):
            self.mouse_down(event)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_move(event)
        elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
            self.mouse_up(event)

    def palette_letters(self):
        return "".join(group for _, group in self.palette_groups())

    def pick(self, letter):
        self.selected = letter
        self.say("%s (%s): %s" % (BLOCKS[letter][0], letter, BLOCKS[letter][1]))

    def mouse_down(self, event):
        pos = event.pos
        for button in self.buttons:
            if button.rect.collidepoint(pos) and event.button == 1:
                return button.action()
        for letter, rect in self.palette_spots:
            if rect.collidepoint(pos):
                return self.pick(letter)
        for axis, (track, thumb) in self.scrollbars().items():
            if track.collidepoint(pos):
                self.dragging_bar = axis
                return self.drag_bar(axis, pos)
        spot = self.tile_at(pos)
        if spot is None:
            return
        if event.button == 2 or pygame.key.get_mods() & pygame.KMOD_ALT:
            letter = self.rows[spot[0]][spot[1]]
            return self.pick(letter) if letter in BLOCKS else None
        letter = self.selected if event.button == 1 else "."
        self.remember()
        self.stroke = {"letter": letter, "last": spot, "start": spot}
        if not self.box_mode:
            self.set_tile(*spot, letter)

    def mouse_move(self, event):
        self.hover = self.tile_at(event.pos)
        if self.dragging_bar:
            return self.drag_bar(self.dragging_bar, event.pos)
        if self.stroke and self.hover and not self.box_mode:
            for r, c in line_between(self.stroke["last"], self.hover):     # no gaps when the mouse moves fast
                self.set_tile(r, c, self.stroke["letter"])
            self.stroke["last"] = self.hover

    def mouse_up(self, event):
        self.dragging_bar = None
        if not self.stroke:
            return
        if self.box_mode:
            spot = self.tile_at(event.pos) or self.stroke["last"]
            for r, c in box_between(self.stroke["start"], spot):
                self.set_tile(r, c, self.stroke["letter"])
        self.stroke = None
        if self.undo_list and self.undo_list[-1] == self.snapshot():
            self.undo_list.pop()                            # nothing changed after all
        if self.needs_rebuild:
            self.rebuild()

    # ----- boxes on top: open, name, yes/no and messages -------------------------------

    def modal_rect(self):
        sizes = {"open": (820, 620), "name": (620, 230), "confirm": (620, 210), "message": (760, 320),
                 "robot": (560, 170)}
        if self.modal["kind"] == "message":                 # just tall enough for its words
            lines = sum(len(self.app.wrap(words, 26 if i else 30, 760 - 48))
                        for i, words in enumerate(self.modal["lines"]))
            sizes["message"] = (760, 118 + lines * 28)
        rect = pygame.Rect((0, 0), sizes[self.modal["kind"]])
        rect.center = (WIDTH // 2, HEIGHT // 2)
        return rect

    def modal_buttons(self):
        rect, kind = self.modal_rect(), self.modal["kind"]
        y = rect.bottom - 56
        if kind == "confirm":
            return [("Yes", pygame.Rect(rect.centerx - 140, y, 120, 40)), ("No", pygame.Rect(rect.centerx + 20, y, 120, 40))]
        if kind == "name":
            return [("Save", pygame.Rect(rect.centerx - 140, y, 120, 40)), ("Cancel", pygame.Rect(rect.centerx + 20, y, 120, 40))]
        if kind == "message":
            return [("OK", pygame.Rect(rect.centerx - 60, y, 120, 40))]
        if kind == "robot":
            return [("Stop", pygame.Rect(rect.centerx - 60, y, 120, 40))]
        return [("Cancel", pygame.Rect(rect.right - 140, rect.top + 14, 120, 36))]

    def open_list_rows(self):
        """Where each line of the Open list is on the screen: (kind, name, value, rect)."""
        rect = self.modal_rect()
        top, bottom = rect.top + 64, rect.bottom - 16
        placed, y = [], top - self.modal["scroll"]
        for kind, name, value in self.modal["items"]:
            h = 40 if kind == "header" else 30
            line = pygame.Rect(rect.left + 20, y, rect.width - 40, h)
            if line.bottom > top and line.top < bottom:
                placed.append((kind, name, value, line))
            y += h
        self.modal["list_height"] = y + self.modal["scroll"] - top
        return placed

    def handle_modal(self, event):
        kind = self.modal["kind"]
        pressed = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pressed = next((label for label, rect in self.modal_buttons() if rect.collidepoint(event.pos)), None)
            if kind == "open" and not pressed:
                for item_kind, name, value, line in self.open_list_rows():
                    if line.collidepoint(event.pos) and item_kind in ("mine", "level"):
                        return self.open_item(item_kind, name, value)
        elif event.type == pygame.MOUSEWHEEL and kind == "open":
            rect = self.modal_rect()
            most = max(0, self.modal.get("list_height", 0) - (rect.height - 80))
            self.modal["scroll"] = min(max(0, self.modal["scroll"] - event.y * 40), most)
        elif event.type == pygame.TEXTINPUT and kind == "name":
            if len(self.modal["text"]) < 30:
                self.modal["text"] += event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pressed = {"confirm": "No", "name": "Cancel", "message": "OK", "robot": "Stop"}.get(kind, "Cancel")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                pressed = {"confirm": "Yes", "name": "Save", "message": "OK"}.get(kind)
            elif event.key == pygame.K_BACKSPACE and kind == "name":
                self.modal["text"] = self.modal["text"][:-1]
        if pressed == "Yes":
            then = self.modal["yes"]
            self.modal = None
            then()
        elif pressed == "Save":
            self.name_done()
        elif pressed == "Stop":
            self.stop_robot()
        elif pressed in ("No", "Cancel", "OK"):
            self.modal = None

    # ----- drawing -----------------------------------------------------------------

    def draw(self):
        screen = self.screen
        screen.fill(game.BG)
        self.draw_view()
        self.draw_palette()
        self.draw_bar()
        if self.modal:
            self.draw_modal()

    def draw_view(self):
        z = self.zoom_level()
        view = self.view
        if z == 1:
            self.draw_game_cave(view, self.cam)
        else:
            size = (math.ceil(VIEW_W / z), math.ceil(VIEW_H / z))
            if size not in self.big_views:
                self.big_views[size] = pygame.Surface(size)
            big = self.big_views[size]
            self.draw_game_cave(big, self.cam)
            # plain scale, not smoothscale: the pixel art looks the same, and it's about 6 times faster
            pygame.transform.scale(big, (VIEW_W, VIEW_H), view)
        ts = TILE * z

        # Outside the cave: darker, so you can see where it ends
        right, bottom = (self.width * TILE - self.cam[0]) * z, (self.height * TILE - self.cam[1]) * z
        shade = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        if right < VIEW_W:
            shade.fill((8, 8, 14, 220), (right, 0, VIEW_W - right, VIEW_H))
        if bottom < VIEW_H:
            shade.fill((8, 8, 14, 220), (0, bottom, min(right, VIEW_W), VIEW_H - bottom))

        # The grid, so you can count blocks
        first_c, first_r = int(self.cam[0] // TILE), int(self.cam[1] // TILE)
        if self.grid:
            for c in range(first_c, self.width + 1):
                x = (c * TILE - self.cam[0]) * z
                if x > VIEW_W:
                    break
                shade.fill(GRID_COLOR, (x, 0, 1, min(bottom, VIEW_H)))
            for r in range(first_r, self.height + 1):
                y = (r * TILE - self.cam[1]) * z
                if y > VIEW_H:
                    break
                shade.fill(GRID_COLOR, (0, y, min(right, VIEW_W), 1))
        view.blit(shade, (0, 0))

        # Letters the game doesn't draw here (a "?" from an old cave, castle things outside the castle)
        last_c, last_r = int(first_c + VIEW_W / ts + 2), int(first_r + VIEW_H / ts + 2)
        for r in range(first_r, min(self.height, last_r)):
            for c in range(first_c, min(self.width, last_c)):
                letter = self.rows[r][c]
                hidden = letter == "?" or (letter in cave_files.CASTLE_ONLY and self.theme != "castle") \
                    or letter not in cave_files.EVERY_LETTER
                if hidden:
                    x, y = self.on_screen(r, c)
                    self.app.text(view, letter, (x + ts / 2, y + ts / 2), int(ts * 0.7), ORANGE, "center", shadow=True)
                elif letter in SHADOWFALL_BLOCKS:
                    x, y = self.on_screen(r, c)
                    draw_shadowfall_block(view, letter, pygame.Rect(x, y, math.ceil(ts), math.ceil(ts)))
                elif letter == caves.SECRET:            # a secret wall looks like rock: mark it, just in the editor
                    x, y = self.on_screen(r, c)
                    self.app.text(view, "?", (x + ts / 2, y + ts / 2), int(ts * 0.6), (200, 170, 255), "center", shadow=True)

        self.draw_platform_tracks(view, ts)
        self.draw_robot_trail(view, ts)

        # The block under the mouse, and the box being dragged out
        if self.hover and not self.modal:
            spots = [self.hover]
            if self.stroke and self.box_mode:
                spots = list(box_between(self.stroke["start"], self.hover))
            letter = self.stroke["letter"] if self.stroke else self.selected
            ghost, (gx, gy, _, _) = self.ghost(letter, z), self.crop_box(letter)
            for r, c in spots[:2000]:
                x, y = self.on_screen(r, c)
                if ghost:
                    view.blit(ghost, (x + gx * z, y + gy * z))
            (r0, c0), (r1, c1) = spots[0], spots[-1]
            x0, y0 = self.on_screen(min(r0, r1), min(c0, c1))
            box = pygame.Rect(x0, y0, (abs(c1 - c0) + 1) * ts, (abs(r1 - r0) + 1) * ts)
            pygame.draw.rect(view, YELLOW, box, 3)

        for axis, (track, thumb) in self.scrollbars().items():
            pygame.draw.rect(view, (20, 20, 30), track)
            pygame.draw.rect(view, (170, 170, 200), thumb, border_radius=5)
        self.screen.blit(view, (0, 0))

    def draw_platform_tracks(self, view, ts):
        """Each moving platform's track: a yellow rail where it goes, and a red bar at each end where it
        turns around. A platform that can't move gets an orange box (the checklist says why)."""
        for p in self.cave.platforms:
            if p.axis == "x":
                x0, y0 = self.on_screen(p.r, p.low)
                x1 = x0 + (p.high + p.w - p.low) * ts
                y1 = y0 + ts * 0.45
            else:
                x0, y0 = self.on_screen(p.low, p.c)
                x1 = x0 + p.w * ts
                y1 = y0 + (p.high - p.low) * ts + ts * 0.45
            if not p.moves():
                pygame.draw.rect(view, ORANGE, (x0, y0, x1 - x0, y1 - y0), 2)
                continue
            bar = max(3, int(ts * 0.15))
            if p.axis == "x":
                mid = (y0 + y1) / 2
                pygame.draw.line(view, TRACK_COLOR, (x0, mid), (x1, mid), max(2, bar // 2))
                for x in (x0 + bar / 2, x1 - bar / 2):          # turn-around bars
                    pygame.draw.line(view, TURN_COLOR, (x, y0 - ts * 0.15), (x, y1 + ts * 0.15), bar)
            else:
                mid = (x0 + x1) / 2
                pygame.draw.line(view, TRACK_COLOR, (mid, y0), (mid, y1), max(2, bar // 2))
                for y in (y0 + bar / 2, y1 - bar / 2):
                    pygame.draw.line(view, TURN_COLOR, (x0 - ts * 0.15, y), (x1 + ts * 0.15, y), bar)

    def ghost(self, letter, z):
        """A see-through picture of a block, to show where it would go."""
        key = (letter, z, self.icons_theme)
        if getattr(self, "ghost_key", None) != key:
            big = self.icons.get(letter + "big")
            self.ghost_image = None
            if big:
                self.ghost_image = pygame.transform.smoothscale(
                    big, (max(1, int(big.get_width() * z)), max(1, int(big.get_height() * z))))
                self.ghost_image.set_alpha(150)
            self.ghost_key = key
        return self.ghost_image

    def draw_robot_trail(self, view, ts):
        def point(x, y):
            return ((x * TILE - self.cam[0]) * ts / TILE, (y * TILE - self.cam[1]) * ts / TILE)
        if len(self.trail) > 1:
            points = [point(x, y) for x, y in self.trail]
            pygame.draw.lines(view, (255, 214, 90), False, points, 2)
            for i, (x, y) in enumerate(points):
                if i % 3 == 0:
                    pygame.draw.circle(view, (255, 240, 160), (int(x), int(y)), 4)
        if self.stuck_at:
            x, y = point(*self.stuck_at)
            for dx in (-1, 1):
                pygame.draw.line(view, RED, (x - 12, y - 12 * dx), (x + 12, y + 12 * dx), 5)

    def panel(self, rect, border=YELLOW, fill=BOX_BG, surface=None):
        surface = surface or self.screen
        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(surface, border, rect, 2, border_radius=10)

    def draw_palette(self):
        app, screen = self.app, self.screen
        left = VIEW_W
        pygame.draw.rect(screen, game.PANEL_BG, (left, 0, WIDTH - left, VIEW_H))
        app.text(screen, "Building blocks", (left + 14, 8), 30, YELLOW)
        y = 36
        self.palette_spots = []
        mouse = pygame.mouse.get_pos()
        for name, group in self.palette_groups():
            app.text(screen, name, (left + 14, y), 19, DIM)
            y += 16
            for i, letter in enumerate(group):
                rect = pygame.Rect(left + 14 + (i % 5) * 55, y + (i // 5) * 49, 52, 46)
                chosen = letter == self.selected
                pygame.draw.rect(screen, ICON_BG, rect, border_radius=6)
                icon = self.icons.get(letter)
                if icon:
                    screen.blit(icon, icon.get_rect(center=rect.center))
                app.text(screen, letter, (rect.right - 3, rect.bottom - 1), 20, TEXT, "bottomright", shadow=True)
                border = YELLOW if chosen else (150, 156, 190) if rect.collidepoint(mouse) else (60, 64, 88)
                pygame.draw.rect(screen, border, rect, 3 if chosen else 1, border_radius=6)
                self.palette_spots.append((letter, rect))
            y += ((len(group) + 4) // 5) * 49 + 3

        # What the chosen block does
        y += 4
        box = pygame.Rect(left + 8, y, WIDTH - left - 16, 104)
        self.panel(box, (90, 96, 130))
        name, words = BLOCKS[self.selected]
        icon = self.icons.get(self.selected)
        if icon:
            screen.blit(icon, icon.get_rect(topleft=(box.x + 10, box.y + 8)))
        app.text(screen, name, (box.x + 62, box.y + 8), 28, YELLOW)
        app.text(screen, "letter:  %s" % self.selected, (box.x + 62, box.y + 32), 22, DIM)
        for i, line in enumerate(app.wrap(words, 20, box.width - 20)[:3]):
            app.text(screen, line, (box.x + 10, box.y + 56 + i * 16), 20, TEXT)

        # The checklist
        self.draw_checklist(pygame.Rect(left + 8, box.bottom + 8, WIDTH - left - 16, VIEW_H - box.bottom - 16))

    def draw_checklist(self, box):
        app, screen = self.app, self.screen
        self.panel(box, (90, 96, 130))
        app.text(screen, "Checklist", (box.x + 10, box.y + 8), 26, YELLOW)
        y = box.y + 34
        rows = self.text_rows()
        all_there = True
        for letter, words in (("S", "a start"), ("*", "a diamond"), ("E", "an exit")):
            have = any(letter in row for row in rows)
            all_there = all_there and have
            tick(screen, (box.x + 20, y + 8), have)
            app.text(screen, "%s (%s)" % (words, letter), (box.x + 36, y), 22, TEXT if have else ORANGE)
            y += 22
        tips = [text for how_bad, text in cave_files.check_cave(self.theme, rows, self.settings)
                if not any(word in text for word in ("No start", "No exit", "No diamond"))]
        for text in tips:
            for line in app.wrap(text, 19, box.width - 20):
                if y + 16 > box.bottom - 4:
                    return
                app.text(screen, line, (box.x + 10, y + 2), 19, ORANGE)
                y += 16
            y += 3
        if all_there and not tips and y + 18 < box.bottom:
            app.text(screen, "Everything looks good!", (box.x + 10, y + 4), 20, GREEN)

    def draw_bar(self):
        app, screen = self.app, self.screen
        pygame.draw.rect(screen, game.LOG_BG, (0, VIEW_H, WIDTH, HEIGHT - VIEW_H))
        mouse = pygame.mouse.get_pos()
        for button in self.buttons:
            disabled = (button.action == self.undo and not self.undo_list) or \
                       (button.action == self.redo and not self.redo_list)
            color = BUTTON_ON if button.on and button.on() else button.color
            if button.rect.collidepoint(mouse) and not disabled:
                color = tuple(min(255, v + 24) for v in color)
            pygame.draw.rect(screen, color, button.rect, border_radius=8)
            pygame.draw.rect(screen, (120, 126, 160), button.rect, 1, border_radius=8)
            app.text(screen, self.button_label(button), button.rect.center, button.size,
                     DIM if disabled else TEXT, "center")

        # Which cave this is
        x = 970
        title = (self.name or "Not saved yet") + ("  (changed)" if self.path and self.unsaved() else "")
        app.text(screen, app.fit(title, 30, WIDTH - x - 12), (x, VIEW_H + 10), 30, YELLOW)
        if self.path:
            where = cave_files.short_path(self.path) + ("  (in the game)" if cave_files.is_game_level(self.path) else "")
        else:
            where = "started from %s" % self.source if self.source else ""
        app.text(screen, app.fit(where, 20, WIDTH - x - 12), (x, VIEW_H + 40), 20, DIM)
        info = "%d wide, %d tall" % (self.width, self.height)
        if self.hover and self.hover[0] < self.height and self.hover[1] < self.width:
            r, c = self.hover
            letter = self.rows[r][c]
            info += "   |   row %d, column %d: %s" % (r, c, BLOCKS.get(letter, ("?",))[0])
        app.text(screen, info, (x, VIEW_H + 62), 20, DIM)

        # The latest message
        if self.message:
            app.text(screen, app.fit(self.message, 24, WIDTH - 24), (12, VIEW_H + 100), 24, self.message_color)

    def draw_modal(self):
        app, screen, kind = self.app, self.screen, self.modal["kind"]
        app.dim_screen(150)
        rect = self.modal_rect()
        self.panel(rect)
        if kind == "open":
            app.text(screen, "Open a cave", (rect.x + 20, rect.y + 16), 34, YELLOW)
            screen.set_clip(pygame.Rect(rect.x, rect.y + 60, rect.width, rect.height - 72))
            mouse = pygame.mouse.get_pos()
            for item_kind, name, value, line in self.open_list_rows():
                if item_kind == "header":
                    app.text(screen, name, (line.x, line.y + 14), 24, DIM)
                elif item_kind == "note":
                    app.text(screen, name, (line.x + 16, line.y + 6), 22, DIM)
                else:
                    if line.collidepoint(mouse):
                        pygame.draw.rect(screen, BUTTON_HOVER, line, border_radius=6)
                    app.text(screen, name, (line.x + 16, line.y + 6), 24, TEXT)
            screen.set_clip(None)
            shown, total = rect.height - 80, self.modal.get("list_height", 0)
            if total > shown:                           # a little bar: there's more if you scroll
                track = pygame.Rect(rect.right - 14, rect.top + 64, 6, shown)
                h = max(30, shown * shown / total)
                y = track.top + (shown - h) * self.modal["scroll"] / (total - shown)
                pygame.draw.rect(screen, (20, 20, 30), track, border_radius=3)
                pygame.draw.rect(screen, (170, 170, 200), (track.x, y, 6, h), border_radius=3)
                app.text(screen, "scroll for more", (rect.right - 24, rect.bottom - 8), 18, DIM, "bottomright")
        elif kind == "name":
            app.text(screen, "Name your cave:", (rect.x + 24, rect.y + 20), 32, YELLOW)
            field = pygame.Rect(rect.x + 24, rect.y + 64, rect.width - 48, 44)
            pygame.draw.rect(screen, (16, 18, 28), field, border_radius=6)
            cursor = "|" if int(time.time() * 2) % 2 else ""
            app.text(screen, self.modal["text"] + cursor, (field.x + 12, field.y + 10), 32, TEXT)
            if self.modal["text"].strip():
                app.text(screen, "It goes in my_caves/%s" % cave_files.file_name(self.modal["text"]),
                         (rect.x + 24, field.bottom + 8), 20, DIM)
        elif kind == "confirm":
            for i, line in enumerate(app.wrap(self.modal["text"], 28, rect.width - 48)):
                app.text(screen, line, (rect.x + 24, rect.y + 28 + i * 28), 28, TEXT)
        elif kind == "message":
            color = GREEN if self.modal.get("good") else ORANGE if "good" in self.modal else TEXT
            y = rect.y + 24
            for i, words in enumerate(self.modal["lines"]):
                for line in app.wrap(words, 26 if i else 30, rect.width - 48):
                    app.text(screen, line, (rect.x + 24, y), 26 if i else 30, color if i == 0 else TEXT)
                    y += 26 if i else 32
                y += 4
        elif kind == "robot":
            seconds = time.time() - self.robot["started"] if self.robot else 0
            dots = "." * (1 + int(seconds * 2) % 3)
            app.text(screen, "The robot is trying your cave" + dots, (rect.x + 24, rect.y + 24), 32, YELLOW)
            app.text(screen, "%d seconds so far (it can take up to a minute or two)" % seconds,
                     (rect.x + 24, rect.y + 62), 22, DIM)
        mouse = pygame.mouse.get_pos()
        for label, button in self.modal_buttons():
            color = BUTTON_HOVER if button.collidepoint(mouse) else BUTTON
            pygame.draw.rect(screen, color, button, border_radius=8)
            pygame.draw.rect(screen, (120, 126, 160), button, 1, border_radius=8)
            app.text(screen, label, button.center, 26, TEXT, "center")


# ===========================================================================
# Little helpers
# ===========================================================================

def line_between(a, b):
    """Every block on a straight line from a to b (so a fast mouse doesn't leave gaps)."""
    (r0, c0), (r1, c1) = a, b
    steps = max(abs(r1 - r0), abs(c1 - c0), 1)
    return [(round(r0 + (r1 - r0) * i / steps), round(c0 + (c1 - c0) * i / steps)) for i in range(steps + 1)]


def box_between(a, b):
    """Every block in the rectangle with corners a and b."""
    (r0, c0), (r1, c1) = a, b
    return [(r, c) for r in range(min(r0, r1), max(r0, r1) + 1) for c in range(min(c0, c1), max(c0, c1) + 1)]


def tick(surf, center, good):
    """A green tick or an orange cross."""
    x, y = center
    pygame.draw.circle(surf, GREEN if good else ORANGE, center, 8)
    if good:
        pygame.draw.lines(surf, (20, 40, 20), False, [(x - 4, y), (x - 1, y + 3), (x + 4, y - 3)], 2)
    else:
        pygame.draw.line(surf, (60, 30, 10), (x - 3, y - 3), (x + 3, y + 3), 2)
        pygame.draw.line(surf, (60, 30, 10), (x - 3, y + 3), (x + 3, y - 3), 2)


def main():
    parser = argparse.ArgumentParser(description="Cave Editor: draw your own caves!")
    parser.add_argument("cave", nargs="?", help="a cave to open (for example my_caves/lava_tower.txt)")
    parser.add_argument("--quiet", action="store_true", help="no sound")
    parser.add_argument("--realm", metavar="LAND", help="the prop editor for a realm land (levels/realm/...)")
    args = parser.parse_args()
    if args.realm:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "shadowfall", "tools"))
        import realm_editor
        realm_editor.main([args.realm])
        return
    Editor(args.cave, sound=not args.quiet).run()


if __name__ == "__main__":
    main()
