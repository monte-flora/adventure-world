"""
SMOOTH WALKING ON THE PHASE 2 MAP - hold a move key and the Hero walks, a little every frame.

- The Hero has a spot on the map that isn't a whole square: game.hero_xy = [x, y], his middle, in
  squares. game.player.pos is still the square his middle is in, so the rest of the game works as before.
- When his middle crosses into the next square, that is one step: game.do(direction) runs, with all a
  step does (the boat, a new land, a house, the Portal, ice...) and a turn passes (food, day and night).
- Rock, water (with no boat), people, shut gates and broken bridges are in the way: he slides along
  them. Push straight into one and it's a bump: the game says what's there, or you talk to them, or
  the gate opens.
- The map's monsters roam at the same time (monsters.pass_time), and touching one starts the fight.

game.do("left") still walks one whole square: robots and tests play that way.
This file knows nothing about graphics, so it's easy to test.
"""

import math

import rules

from phase2 import people

HERO_SPEED = 5.0        # the Hero walks this many squares a second
HALF = 0.3              # he (and a monster) is this wide from the middle to a side, in squares
GAP = 0.001             # he stops this far from what's in the way
STEP = 0.05             # nothing moves for longer than this at once (seconds): a slow frame is cut up


# ===========================================================================
# Spots on the map: [x, y] in squares. Square (row, col) has its middle at [col + 0.5, row + 0.5].
# ===========================================================================

def middle(pos):
    return [pos[1] + 0.5, pos[0] + 0.5]


def square(xy):
    return (math.floor(xy[1]), math.floor(xy[0]))


def slide(xy, dx, dy, free, half=HALF):
    """Move a box (its middle at xy) by dx, then by dy (each less than a square). It stops at the side
    of a square that isn't free(pos), so it slides along walls. Returns its new [x, y]."""
    x, y = xy
    if dx:
        x = _push(x, y, dx, lambda col, row: free((row, col)), half)
    if dy:
        y = _push(y, x, dy, lambda row, col: free((row, col)), half)
    return [x, y]


def _push(a, b, d, free, half):
    """Along one line: from a to a + d, with the box reaching `half` either side of b the other way."""
    new = a + d
    front = math.floor(new + half if d > 0 else new - half)
    for other in range(math.floor(b - half), math.floor(b + half) + 1):
        if not free(front, other):
            return front - half - GAP if d > 0 else front + 1 + half + GAP
    return new


# ===========================================================================
# The Hero
# ===========================================================================

def where(game):
    """The Hero's middle, [x, y] in squares. If something else moved him (a robot's step, a waystone,
    a fight he ran from, a cave), he stands in the middle of his new square."""
    xy = getattr(game, "hero_xy", None)
    if xy is None or square(xy) != tuple(game.player.pos):
        xy = game.hero_xy = middle(game.player.pos)
    return xy


def passable(game, pos):
    """Can the Hero walk onto this square? (The same things stop a whole step: Game.move.)"""
    if not game.in_bounds(pos):
        return False
    letter = game.tile(pos)
    if letter == "W":
        return game.player.has_boat
    if letter in "X=":                              # rock, a broken bridge
        return False
    return not (game.world == 1 and (game.gate_at(pos) or people.person_at(game, pos)))


def go(game, way, far):
    """The Hero walks `far` squares (less than one) this way. Returns how far he got."""
    xy = where(game)
    here = game.player.pos
    dr, dc = rules.DIRECTIONS[way]
    new = slide(xy, dc * far, dr * far, lambda pos: passable(game, pos))
    if square(new) != here:                         # his middle crosses into the next square: one step
        game.do(way)                                # everything a step does, and a turn passes
        if game.player.pos == here:                 # (something stopped him after all)
            new = xy
        elif game.player.pos != square(new):        # he slid on the ice, or went through the Portal
            new = middle(game.player.pos)
    game.hero_xy = new
    return abs(new[0] - xy[0]) + abs(new[1] - xy[1])


def walk(game, dx, dy, dt):
    """The Hero walks for dt seconds. dx and dy are -1, 0 or 1: the move keys that are held.
    Returns True if he got anywhere."""
    if not (dx or dy) or game.battle or game.cave or game.over:
        game.bump = None
        return False
    got = 0.0
    while dt > 0 and not (game.battle or game.cave or game.over):
        far = HERO_SPEED * min(dt, STEP) * (0.7071 if dx and dy else 1.0)
        dt -= STEP
        if dx:
            got += go(game, "right" if dx > 0 else "left", far)
        if dy and not (game.battle or game.cave or game.over):
            got += go(game, "down" if dy > 0 else "up", far)
    if got > 0 or (dx and dy):
        game.bump = None
        return got > 0
    return push(game, "right" if dx > 0 else "left" if dx else "down" if dy > 0 else "up", far)


def push(game, way, far):
    """One key is held and he can't get any farther. Round a corner if that's all it is; if not it's a
    bump (once for each push): the game says what's there, you talk to them, the gate opens..."""
    xy, here = where(game), game.player.pos
    dr, dc = rules.DIRECTIONS[way]
    if passable(game, (here[0] + dr, here[1] + dc)):        # only a corner is in the way: step round it
        off = (here[0] + 0.5 - xy[1]) if dc else (here[1] + 0.5 - xy[0])
        side = ("down" if off > 0 else "up") if dc else ("right" if off > 0 else "left")
        return go(game, side, min(far, abs(off))) > 0
    if game.bump != (way, here):
        game.bump = (way, here)
        game.do(way)
    return False


# ===========================================================================
# One frame of the map (game.App.update calls it, through phase2.live_map)
# ===========================================================================

WAYS = ("left", "right", "up", "down")


def live(app, dt, held):
    """The map in real time for one frame: the Hero walks the way the held move keys say, and the
    monsters roam. `held` is the ways whose keys are down ("left", "up"...)."""
    game = app.game
    game.live = True                                # (monsters roam by the clock now, not by the turn)
    if game.battle or game.cave or game.over or game.story or getattr(game, "travel_open", False):
        return
    dx = ("right" in held) - ("left" in held)
    dy = ("down" in held) - ("up" in held)
    going = [way for way, on in zip(WAYS, (dx < 0, dx > 0, dy < 0, dy > 0)) if on]
    if going:
        if app.map_facing not in going:             # he looks the way he walks (the key pressed last)
            app.map_facing = going[0]
        game.player.facing = app.map_facing
    game.walk(dx, dy, dt)
    game.pass_time(dt)
