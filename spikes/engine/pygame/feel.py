"""Game-feel logic for the engine spike: top-down walk and side-view jump. No graphics, so it is easy to test.

Units: pixels and seconds. One tile is 32 px (the art pick: 32-px tiles at 960x540). The level is a list of strings, '#' is solid.
"""
import math

TILE = 32

# --- top-down walk ---
WALK_SPEED = 160.0      # px/s (5 tiles a second, like phase2/smooth.py HERO_SPEED)
WALK_ACCEL = 1800.0      # px/s^2: reaches full speed in ~0.09 s
WALK_FRICTION = 2200.0

# --- side-view jump ---
RUN_SPEED = 192.0
RUN_ACCEL = 2400.0
AIR_ACCEL = 1600.0
GRAVITY = 1960.0
JUMP_SPEED = 600.0      # ~92 px high (just under 3 tiles)
JUMP_CUT = 0.45         # let go of jump early: upward speed is multiplied by this (short hop)
MAX_FALL = 720.0
COYOTE = 0.10           # you can still jump this long after walking off a ledge
BUFFER = 0.10           # a jump pressed this long before landing still happens

STEP = 1 / 240          # physics runs in fixed steps; a slow frame is cut up


def solid(level, px, py):
    col, row = math.floor(px / TILE), math.floor(py / TILE)
    if row < 0 or col < 0 or row >= len(level) or col >= len(level[0]):
        return True
    return level[row][col] == "#"


def _approach(v, target, rate, dt):
    if v < target:
        return min(target, v + rate * dt)
    return max(target, v - rate * dt)


class Body:
    """An axis-aligned box: x, y is the top-left corner."""

    def __init__(self, x, y, w=20, h=28):
        self.x, self.y, self.w, self.h = float(x), float(y), w, h
        self.vx = self.vy = 0.0
        self.on_floor = False
        self.coyote = 0.0
        self.buffer = 0.0
        self.jumps = 0

    def hits(self, level, x, y):
        e = 0.001
        for px in (x + e, x + self.w - e):
            for py in (y + e, y + self.h / 2, y + self.h - e):
                if solid(level, px, py):
                    return True
        return False

    def move(self, level, dx, dy):
        """Move, stopping flush against walls. Returns (hit_x, hit_y)."""
        hit_x = hit_y = False
        if dx:
            if self.hits(level, self.x + dx, self.y):
                hit_x = True
                if dx > 0:
                    self.x = math.floor((self.x + self.w + dx) / TILE) * TILE - self.w
                else:
                    self.x = math.floor((self.x + dx) / TILE + 1) * TILE
                self.vx = 0.0
            else:
                self.x += dx
        if dy:
            if self.hits(level, self.x, self.y + dy):
                hit_y = True
                if dy > 0:
                    self.y = math.floor((self.y + self.h + dy) / TILE) * TILE - self.h
                else:
                    self.y = math.floor((self.y + dy) / TILE + 1) * TILE
                self.vy = 0.0
            else:
                self.y += dy
        return hit_x, hit_y


def walk(body, level, ix, iy, dt):
    """Top-down: ix, iy in -1..1 (held keys). Diagonals are not faster."""
    n = math.hypot(ix, iy)
    if n > 1:
        ix, iy = ix / n, iy / n
    while dt > 1e-9:
        h = min(dt, STEP)
        dt -= h
        for axis, i in (("vx", ix), ("vy", iy)):
            v = getattr(body, axis)
            rate = WALK_ACCEL if i else WALK_FRICTION
            setattr(body, axis, _approach(v, i * WALK_SPEED, rate, h))
        body.move(level, body.vx * h, body.vy * h)


def platform(body, level, ix, jump_pressed, jump_held, dt):
    """Side view. jump_pressed is true on the frame the key went down."""
    if jump_pressed:
        body.buffer = BUFFER
    while dt > 1e-9:
        h = min(dt, STEP)
        dt -= h
        body.vx = _approach(body.vx, ix * RUN_SPEED, RUN_ACCEL if body.on_floor else AIR_ACCEL, h)
        if body.buffer > 0 and (body.on_floor or body.coyote > 0):
            body.vy = -JUMP_SPEED
            body.buffer = body.coyote = 0.0
            body.on_floor = False
            body.jumps += 1
        if not jump_held and body.vy < 0:
            body.vy *= JUMP_CUT ** (h * 60)     # short hop, frame-rate independent
        body.vy = min(MAX_FALL, body.vy + GRAVITY * h)
        body.move(level, body.vx * h, 0)
        _, hit_y = body.move(level, 0, body.vy * h)
        was = body.on_floor
        body.on_floor = hit_y and body.vy == 0 and body.hits(level, body.x, body.y + 0.5)
        if body.on_floor:
            body.coyote = COYOTE
        elif was:
            body.coyote = COYOTE
        else:
            body.coyote = max(0.0, body.coyote - h)
        body.buffer = max(0.0, body.buffer - h)
