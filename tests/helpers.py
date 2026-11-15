"""
Little helpers the tests share, so every test can be short and easy to read.

    ok(something_true, "what it means")

checks one thing. If it isn't true, the test stops right there and prints what went wrong.
"""

import pygame

import caves
import game
import rules

DT = 1 / 60          # one frame: the game runs at 60 frames every second


def ok(condition, message):
    """Check one thing. If it isn't true, the test stops and says what should have happened."""
    assert condition, message


# ===========================================================================
# A world, with no monsters walking around (so nothing surprises a test)
# ===========================================================================

def new_world(seed=1):
    world = rules.Game("Hero", seed=seed)
    world.monsters = []
    return world


def tiles(world, letter):
    """Every spot on the world map with this letter, top-left first."""
    return [(r, c) for r in range(world.rows) for c in range(world.cols) if world.map[r][c] == letter]


def steps(a, b):
    """How many steps apart two spots on the map are (no going diagonally)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class FakeDice:
    """Pretend dice, so a test can choose what the game "rolls".
    random() gives the numbers in `rolls` one by one (then `rest`), randint() the numbers in `ints`."""

    def __init__(self, rolls=(), ints=(), rest=0.5):
        self.rolls, self.ints, self.rest = list(rolls), list(ints), rest

    def random(self):
        return self.rolls.pop(0) if self.rolls else self.rest

    def randint(self, low, high):
        return self.ints.pop(0) if self.ints else low

    def choice(self, things):
        return things[0]


# ===========================================================================
# Caves: draw a little one right in the test, then run and jump in it
# ===========================================================================

def cave_from(rows, world=None):
    """Make a cave from a drawing (a list of rows). Returns (the world, the cave)."""
    world = world or new_world()
    cave = caves.Cave(world, (0, 0), "\n".join(rows))
    world.cave = cave
    return world, cave


def run(cave, frames, **keys):
    """Play the cave for some frames, holding these keys (right=True, jump=True, ...).
    jump_pressed and space_pressed only count on the first frame, like a real key press."""
    for frame in range(frames):
        controls = dict(keys)
        if frame > 0:
            controls.pop("jump_pressed", None)
            controls.pop("space_pressed", None)
            controls.pop("use_pressed", None)
        cave.update(DT, controls)


def feet(cave):
    """How far down your feet are (the top of the cave is 0, every block is 1)."""
    return round(cave.you.y + cave.you.h, 3)


# ===========================================================================
# The whole game, with graphics (drawn into an invisible window)
# ===========================================================================

def new_app(seed=1, story=False, monsters=False):
    """Start the game, just like pressing ENTER on the title screen.
    story=False skips the story cards, and monsters=False takes the monsters off the map."""
    app = game.App("Hero", seed=seed, sound=False)
    start_game(app, story=story, monsters=monsters)
    return app


def start_game(app, story=False, monsters=False):
    """A new game in the same window (like playing again)."""
    app.new_game()
    if not story:
        app.game.story.clear()
    if not monsters:
        app.game.monsters = []
    return app.game


def frames(app, how_many=1):
    """Let the game run (and draw) for some frames."""
    for _ in range(how_many):
        app.step(DT)


def press(app, key, text="", up=False):
    """Press a key (or let go of it, with up=True), then run one frame."""
    kind = pygame.KEYUP if up else pygame.KEYDOWN
    app.handle_event(pygame.event.Event(kind, key=key, mod=0, unicode=text))
    app.step(DT)


def move_mouse(app, spot):
    app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=spot, rel=(0, 0), buttons=(0, 0, 0)))
    app.step(DT)


def click(app, spot, button=1):
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=spot, button=button))
    app.step(DT)
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=spot, button=button))
    app.step(DT)


class HeldKeys:
    """Pretend some keys are held down. In caves the game asks pygame which keys are held
    every frame, so a test swaps pygame.key.get_pressed for this (see hold_keys below)."""

    def __init__(self):
        self.held = set()

    def __getitem__(self, key):
        return key in self.held


def hold_keys(monkeypatch):
    """Returns a set: put keys in it to hold them down, take them out to let go."""
    keys = HeldKeys()
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: keys)
    return keys.held


def walk_into_a_mine(app, mine=None):
    """Stand on a Mine (the one nearest home if you don't say) and climb down into its cave."""
    world = app.game
    if mine is None:
        mine = min(tiles(world, "M"), key=lambda spot: (steps(spot, world.start), spot))
    world.player.pos = mine
    app.player_px = list(game.tile_px(mine))
    world.do("act")
    frames(app, 30)
    return world.cave
