"""
GAME FEEL SPIKE for teen Shadowfall (Wave A, gameplay). Not game code: a test bed for the numbers in
docs/teen/gameplay/README.md, so they can be felt (play.py) and checked (check_feel.py).

Units: 1 tile = 1.0, time in seconds, a fixed step of 1/60 s (one "frame"). y grows DOWN, like the screen.
This file knows nothing about graphics.
"""
import math

FRAME = 1 / 60

# --- Running ---------------------------------------------------------------
RUN_MAX = 7.5            # tiles/s
GROUND_ACCEL = 75.0      # 0 -> RUN_MAX in 0.10 s (6 frames)
GROUND_DECEL = 110.0     # RUN_MAX -> 0 in ~4 frames
AIR_ACCEL = 50.0
AIR_DECEL = 35.0
# --- Jumping (set by height and time to apex: g = 2h/t^2, v0 = 2h/t) ------
JUMP_HEIGHT = 3.4        # tiles (formula; ~3.3 measured at 60 fps): clears a 3-tile wall
JUMP_APEX_TIME = 0.38    # s
GRAVITY = 2 * JUMP_HEIGHT / JUMP_APEX_TIME ** 2      # ~45 tiles/s^2
JUMP_SPEED = 2 * JUMP_HEIGHT / JUMP_APEX_TIME        # ~17.1 tiles/s
FALL_MULT = 1.6          # falling is heavier than rising: snappy, not floaty
APEX_SPEED = 2.5         # |vy| below this with jump held = "hang" at the top...
APEX_MULT = 0.6          # ...gravity x0.6 there
JUMP_CUT = 0.45          # let go of jump while rising: vy x0.45 (short hop)
MAX_FALL = 20.0
COYOTE_FRAMES = 6        # jump still works 6 frames after leaving a ledge
BUFFER_FRAMES = 8        # a jump pressed 8 frames before landing still fires
DOUBLE_JUMP_HEIGHT = 2.25
# --- Dash ------------------------------------------------------------------
DASH_SPEED = 30.0
DASH_FRAMES = 11         # 11 frames x 30/60 = 5.5 tiles
DASH_COOLDOWN = 21       # frames, from dash start's end
# --- Walls -------------------------------------------------------------------
WALL_SLIDE = 4.5
WALL_JUMP_X = 9.0
WALL_JUMP_Y = 15.0
WALL_JUMP_LOCK = 8       # frames you can't steer back toward the wall
# --- Attack (R) --------------------------------------------------------------
ATTACK_STARTUP, ATTACK_ACTIVE, ATTACK_RECOVERY = 2, 5, 8     # 15 frames = 0.25 s
ATTACK_REACH = 1.5       # tiles in front (or below, for the down strike)
POGO_SPEED = 15.5        # down strike on something: bounce up ~2.7 tiles
RECOIL_SPEED = 3.0       # a grounded side hit pushes you back a little
RECOIL_FRAMES = 4
# --- Getting hurt ------------------------------------------------------------
HURT_X, HURT_Y = 7.0, 9.0
HURT_LOCK = 12           # frames with no control
IFRAMES = 60             # 1.0 s, flicker
# --- Juice -------------------------------------------------------------------
HITSTOP = {"hit": 3, "kill": 6, "hurt": 10, "boss_phase": 20}          # frames frozen
SHAKE = {"hit": (1, 4), "kill": (2, 6), "hurt": (5, 12), "slam": (8, 20)}  # (pixels, frames)

PLAYER_W, PLAYER_H = 0.75, 1.4


def approach(v, target, step):
    return min(v + step, target) if v < target else max(v - step, target)


class Body:
    """The player in a side-view room. solid(tx, ty) -> bool says which tiles are rock."""

    def __init__(self, x, y, solid, has_dash=True, has_double=True, has_wall=True):
        self.x, self.y = x, y            # feet middle
        self.vx = self.vy = 0.0
        self.solid = solid
        self.has_dash, self.has_double, self.has_wall = has_dash, has_double, has_wall
        self.on_ground = False
        self.facing = 1
        self.coyote = 0
        self.buffer = 0
        self.jump_held = False
        self.rising = False              # a jump that can still be cut short
        self.air_dash = True
        self.double = True
        self.dash = 0
        self.dash_cd = 0
        self.wall = 0                    # -1 / 1: touching a wall on that side, in the air
        self.lock = 0                    # frames of no steering (wall jump, hurt)
        self.attack = 0                  # frames into the swing (0 = none)
        self.attack_dir = "side"
        self.iframes = 0
        self.hitstop = 0
        self.shake = (0, 0)
        self.recoil = 0

    # --- events ---------------------------------------------------------------
    def juice(self, kind):
        self.hitstop = max(self.hitstop, HITSTOP.get(kind, 0))
        if kind in SHAKE:
            self.shake = max(self.shake, SHAKE[kind])

    def pogo(self):
        """The down strike touched an enemy, a hazard or a pogo object."""
        self.vy = -POGO_SPEED
        self.air_dash = self.double = True
        self.juice("hit")

    def hurt(self, from_x):
        if self.iframes:
            return False
        side = 1 if self.x >= from_x else -1
        self.vx, self.vy = HURT_X * side, -HURT_Y
        self.lock, self.iframes, self.dash = HURT_LOCK, IFRAMES, 0
        self.juice("hurt")
        return True

    def attack_box(self):
        """The sword's box (left, top, right, bottom) while the swing is active, else None."""
        if not ATTACK_STARTUP < self.attack <= ATTACK_STARTUP + ATTACK_ACTIVE:
            return None
        if self.attack_dir == "down":
            return (self.x - 0.6, self.y, self.x + 0.6, self.y + ATTACK_REACH)
        if self.attack_dir == "up":
            return (self.x - 0.6, self.y - PLAYER_H - ATTACK_REACH, self.x + 0.6, self.y - PLAYER_H)
        x0 = self.x + self.facing * PLAYER_W / 2
        x1 = x0 + self.facing * ATTACK_REACH
        return (min(x0, x1), self.y - PLAYER_H, max(x0, x1), self.y - 0.2)

    # --- one frame ----------------------------------------------------------------
    def step(self, move=0, up=False, down=False, jump_pressed=False, jump_held=False,
             dash_pressed=False, attack_pressed=False):
        if self.hitstop:
            self.hitstop -= 1
            return
        if self.shake[1]:
            self.shake = (self.shake[0], self.shake[1] - 1)
        self.iframes = max(0, self.iframes - 1)
        self.lock = max(0, self.lock - 1)
        self.dash_cd = max(0, self.dash_cd - 1)
        self.jump_held = jump_held
        if jump_pressed:
            self.buffer = BUFFER_FRAMES
        if move and not self.lock:
            self.facing = move

        # attack
        if attack_pressed and not self.attack:
            self.attack = 1
            self.attack_dir = "down" if down and not self.on_ground else "up" if up else "side"
        elif self.attack:
            self.attack = 0 if self.attack >= ATTACK_STARTUP + ATTACK_ACTIVE + ATTACK_RECOVERY else self.attack + 1

        # dash
        if dash_pressed and self.has_dash and not self.dash and not self.dash_cd and (self.on_ground or self.air_dash):
            self.dash = DASH_FRAMES
            if not self.on_ground:
                self.air_dash = False
        if self.dash:
            self.dash -= 1
            self.vx, self.vy = DASH_SPEED * self.facing, 0.0
            if not self.dash:
                self.dash_cd = DASH_COOLDOWN
                self.vx = RUN_MAX * self.facing
        else:
            self._steer(move)
            self._jump(move)
            self._fall()
        self._move()

    def _steer(self, move):
        if self.recoil:
            self.recoil -= 1
            return
        if self.lock:
            return
        target = move * RUN_MAX
        if self.on_ground:
            rate = GROUND_ACCEL if move and (self.vx * move >= 0) else GROUND_DECEL
        else:
            rate = AIR_ACCEL if move else AIR_DECEL
        self.vx = approach(self.vx, target, rate * FRAME)

    def _jump(self, move):
        if self.buffer:
            self.buffer -= 1
            if self.on_ground or self.coyote:
                self.vy, self.buffer, self.coyote = -JUMP_SPEED, 0, 0
                self.on_ground, self.rising = False, True
            elif self.wall and self.has_wall:
                self.vy, self.vx = -WALL_JUMP_Y, -self.wall * WALL_JUMP_X
                self.facing, self.lock, self.buffer = -self.wall, WALL_JUMP_LOCK, 0
                self.rising = True
            elif self.has_double and self.double and self.buffer == BUFFER_FRAMES - 1:
                self.vy = -math.sqrt(2 * GRAVITY * DOUBLE_JUMP_HEIGHT)
                self.double, self.buffer, self.rising = False, 0, True
        if self.rising and self.vy < -APEX_SPEED and not self.jump_held:
            self.vy *= JUMP_CUT          # let go early: a short hop (once per jump)
            self.rising = False

    def _fall(self):
        g = GRAVITY
        if self.vy > 0:
            g *= FALL_MULT
        elif abs(self.vy) < APEX_SPEED and self.jump_held:
            g *= APEX_MULT
        self.vy = min(self.vy + g * FRAME, MAX_FALL)
        if self.wall and self.has_wall and self.vy > WALL_SLIDE:
            self.vy = WALL_SLIDE

    def _box_hits(self, x, y):
        l, r = x - PLAYER_W / 2, x + PLAYER_W / 2 - 1e-6
        t, b = y - PLAYER_H, y - 1e-6
        return any(self.solid(tx, ty) for tx in range(math.floor(l), math.floor(r) + 1)
                   for ty in range(math.floor(t), math.floor(b) + 1))

    def _move(self):
        was_ground = self.on_ground
        nx = self.x + self.vx * FRAME
        if self._box_hits(nx, self.y):
            nx = (math.floor(nx + PLAYER_W / 2) - PLAYER_W / 2) if self.vx > 0 else (math.floor(nx - PLAYER_W / 2) + 1 + PLAYER_W / 2)
            self.vx = 0.0
        self.x = nx
        ny = self.y + self.vy * FRAME
        self.on_ground = False
        if self._box_hits(self.x, ny):
            if self.vy > 0:
                ny = math.floor(ny)
                self.on_ground = True
                self.air_dash = self.double = True
            else:
                ny = math.floor(ny - PLAYER_H) + 1 + PLAYER_H
            self.vy = 0.0
        self.y = ny
        if was_ground and not self.on_ground and self.vy >= 0:
            self.coyote = COYOTE_FRAMES
        elif self.coyote and not self.on_ground:
            self.coyote -= 1
        if self.on_ground:
            self.coyote = 0
        side = 0
        if not self.on_ground:
            for s in (-1, 1):
                if self._box_hits(self.x + s * 0.05, self.y):
                    side = s
        self.wall = side
