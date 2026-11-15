"""
THE THRONE ROOM - where you fight the Shadow King!

The throne room plays just like the castle (caves.py does all the running and
jumping, and game.py draws it), but the monster in here is MUCH bigger.
When you come in, the great door slams shut behind you. No running away!

How the Shadow King fights:
  1. He walks toward you.
  2. His sword GLOWS. That's your warning: get out of the way!
  3. ...because then he SLASHES. After a slash his sword is stuck in the floor
     for a moment. That's the best time to hit him with Sunfang!
  4. When you're far away, his hand glows and he throws shadow fireballs along
     the floor. Jump over them!
  5. At half health he gets ANGRY: he's faster, his warnings are shorter, and
     he throws two fireballs at a time.

Sunfang hurts him the most, and every light shard you found in the castle makes
it hit him harder. Arrows only scratch him. Jumping on his head does nothing at all!

Up the ladder is a healing nook he can't reach, with a healing spring in it.
The spring has 10 health in it, in all - so use it wisely.

If he knocks you out, you wake up by the door with full health. But he gets
all his health back too (and the spring fills up again). Try again!
"""

import math

import caves

# ===========================================================================
# THE SHADOW KING - try changing these!
# ===========================================================================
KING_HEALTH = 80           # Sunfang hits for 6-9, so that's about 11 hits
SLASH_DAMAGE = 5           # his big shadow sword
FIREBALL_DAMAGE = 3        # his shadow fireballs
ARROW_DAMAGE = (2, 3)      # even fire arrows only singe him (smallest, biggest)...
SHARD_BONUS = 1            # ...but every light shard you found makes Sunfang hit him this much harder
KING_SAFE_TIME = 1.0       # after you hit him he blinks, and nothing can hurt him for this long (just like you!)
SLIDE_BACK = 6.0           # how hard a hit pushes him back (but not while his sword is stuck in the floor)

# How he fights. The ones with two numbers are (normal, angry).
KING_SPEED = (2.0, 3.0)        # how fast he walks, in tiles per second
SLASH_WARNING = (0.8, 0.55)    # his sword glows this long before he slashes
SLASH_TIME = 0.25              # the slash itself
SLASH_REACH = 2.0              # how far in front of him his sword reaches
STUCK_TIME = (1.0, 0.7)        # after a slash, his sword is stuck in the floor this long...
PULL_OUT_TIME = 0.4            # ...then he needs this long to pull it out, before he attacks again (back off!)
THROW_WARNING = (0.7, 0.5)     # his hand glows this long before he throws a fireball
FIREBALLS = (1, 2)             # how many fireballs he throws at a time
FIREBALL_GAP = 0.7             # seconds between two fireballs
FIREBALL_SPEED = (6.0, 7.0)    # how fast they fly, in tiles per second
FIREBALL_SIZE = 0.5            # how big they are, in tiles
FIREBALL_HEIGHT = 0.45         # how high above the floor they fly (low, so you can jump over them)
ANGRY_AT = 0.5                 # he gets angry when he's down to half his health
FAR_AWAY = 5.0                 # if you're farther away than this, he throws fireballs at you...
TOO_CLOSE = 2.0                # ...but if you're closer than this, he slashes instead (a fireball would land right on you)
MAX_WALK = 2.5                 # if he walks this long and still can't reach you, he throws fireballs
START_WAIT = 2.0               # when the fight starts, he waits this long (get ready!)
KING_W, KING_H = 1.5, 2.0      # how big he is, in tiles. You can only just jump over him!

# THE HEALING NOOK
NOOK_HEALING = 10              # the healing spring has this much health in it, in all
NOOK_HEAL_EVERY = 0.35         # standing in the nook, by the spring, heals you 1 health this often
UP_HIGH = 3.0                  # he can't reach you if your feet are this high above the floor

VICTORY_TIME = 2.5             # when you beat him, the light pours out for this long, then the story ends

# ===========================================================================
# THE THRONE ROOM - draw your own! It uses the castle's letters (see castle.py), and:
#   n = the healing spring in the nook (up the ladder, too high for him to reach)
#   Y = the Shadow King's throne (he starts the fight standing in front of it)
#   S = where you start, in front of the great door you came in through
# It is 18 blocks wide and 11 tall, so the whole room fits on the screen.
# ===========================================================================
THRONE_ROOM = """
theme: castle
##################
#...f..w...w..f..#
#................#
####.............#
#.........i......#
#.n.....i.....i..#
####H............#
#...H............#
#...H.===.===....#
#.S.H..........Y.#
##################
"""


class ShadowKing(caves.Body):
    """The Shadow King himself. He isn't like the other monsters: he has his own way of fighting.

    What he's doing (self.doing) is one of:
      "wait"     standing still (at the start, or while you're up in the nook)
      "walk"     walking toward you
      "warn"     his sword is glowing: he's about to slash!
      "slash"    swinging his sword
      "stuck"    his sword is stuck in the floor: hit him now!
      "aim"      his hand is glowing: he's about to throw a fireball
      "beaten"   you beat him!
    """

    def __init__(self, room, x, y):
        super().__init__(room, x, y, KING_W, KING_H)
        self.health = self.max_health = KING_HEALTH
        self.angry = False
        self.doing = "wait"
        self.timer = START_WAIT       # how long until he's done with what he's doing
        self.facing = -1
        self.flash = 0.0              # flashes white when you hit him
        self.safe_time = 0.0          # nothing can hurt him for this long
        self.fireballs_left = 0       # fireballs he still has to throw
        self.attacks = 0              # how many times he attacked. Every 3rd time he throws fireballs
        self.threw_last = False       # did he just throw fireballs? (he never does it twice in a row)

    @property
    def is_alive(self):
        return self.health > 0

    def normal_or_angry(self, numbers):
        """Most of his numbers come in pairs: (normal, angry)."""
        return numbers[1] if self.angry else numbers[0]

    def sword_box(self):
        """Where his sword hits when he slashes: (x, y, width, height) in front of him."""
        x = self.x + self.w if self.facing > 0 else self.x - SLASH_REACH
        return (x, self.y - 0.4, SLASH_REACH, self.h + 0.4)


class ThroneRoom(caves.Cave):
    """The throne room: the castle's last room, where you fight the Shadow King."""
    is_castle = True                  # it's drawn just like the castle
    is_throne_room = True

    def __init__(self, game, gate):
        super().__init__(game, gate, THRONE_ROOM)
        r, c = self.find("Y")
        self.floor = r + 1                            # where his feet are (the top of the floor blocks)
        self.king_start = (c + 0.5 - KING_W / 2, self.floor - KING_H)   # in front of his throne
        self.king = ShadowKing(self, *self.king_start)
        self.fireballs = []
        self.healing_left = NOOK_HEALING              # how much health is left in the healing spring
        self.heal_timer = 0.0
        self.beaten_time = None                       # counts down after you beat him, then the story ends
        self.told = set()                             # things the game already told you about

    def goal(self):
        """What the panel says."""
        king = self.king
        if not king.is_alive:
            return "Shadow King: beaten!"
        return "Shadow King: %d/%d" % (king.health, king.max_health)

    def tell_once(self, name, text, kind="quest"):
        if name not in self.told:
            self.told.add(name)
            self.game.log(text, kind)

    def up_high(self):
        """Are you up in the nook (or the top of its ladder)? He can't reach you there."""
        return self.you.y + self.you.h <= self.floor - UP_HIGH + caves.EPS

    def gap(self):
        """How much space there is between him and you."""
        king, you = self.king, self.you
        return max(0.0, abs(you.center[0] - king.center[0]) - (king.w + you.w) / 2)

    # ----- every frame ----------------------------------------------------------

    def update(self, dt, controls):
        if self.beaten_time is not None:              # you beat him: the light is coming back...
            self.beaten_time -= dt
            if self.beaten_time <= 0 and not self.game.won:
                self.game.beat_the_king()             # ...and then the story ends
        super().update(dt, controls)

    def step(self, dt, controls):
        super().step(dt, controls)                    # you, your arrows (there are no other monsters in here)
        if self.result or not self.game.player.is_alive:
            return
        self.move_king(dt)
        self.move_fireballs(dt)
        self.heal_in_nook(dt)

    # ----- the Shadow King ------------------------------------------------------------

    def move_king(self, dt):
        king, you, game = self.king, self.you, self.game
        king.flash = max(0.0, king.flash - dt)
        king.safe_time = max(0.0, king.safe_time - dt)
        king.timer -= dt
        if not king.is_alive:
            king.vx = 0.0
            return
        if king.doing in ("wait", "walk", "warn", "aim"):
            king.facing = caves.sign(you.center[0] - king.center[0])     # he always turns to face you

        if king.doing == "stuck" and king.timer <= 0:
            king.doing, king.timer = "wait", PULL_OUT_TIME   # he pulls his sword out of the floor
        elif king.doing == "wait" and king.timer <= 0:
            self.next_move()
        elif king.doing == "walk":
            if self.up_high():
                self.next_move()                      # you climbed up out of reach
            elif self.gap() <= SLASH_REACH - 0.5:
                king.doing, king.timer = "warn", king.normal_or_angry(SLASH_WARNING)
                game.sound("alert")                   # his sword starts to glow...
            elif king.timer <= 0:
                self.start_throwing()                 # he can't catch you: fireballs!
        elif king.doing == "warn" and king.timer <= 0:
            king.doing, king.timer = "slash", SLASH_TIME
            game.sound("clang")
        elif king.doing == "slash":
            if you.touches(*king.sword_box()) and you.safe_time <= 0:
                game.log("The Shadow King's sword hits you!", "bad")
                self.hurt_you(SLASH_DAMAGE, king.center[0])
                return                                # (if that knocked you out, everything starts again)
            if king.timer <= 0:
                king.doing, king.timer = "stuck", king.normal_or_angry(STUCK_TIME)
                game.effect("pound", cave_xy=(king.center[0] + king.facing * (king.w / 2 + 1), self.floor))
        elif king.doing == "aim" and king.timer <= 0:
            self.throw_fireball()

        # Walking, and sliding back when you hit him
        want = king.facing * king.normal_or_angry(KING_SPEED) if king.doing == "walk" else 0.0
        king.vx = caves.approach(king.vx, want, 20 * dt)
        king.fall(dt)
        king.move_x(king.vx * dt)
        king.move_y(king.vy * dt)

        # Bumping into him doesn't hurt: he's just too big to walk through
        if you.touches_body(king):
            if you.vy > 0 and you.y + you.h <= king.y + 0.5:
                you.vy, you.pounding = -caves.STOMP_BOUNCE, False     # boing! his armor is too hard
                game.sound("stomp")
                self.tell_once("stomp", "Your boots bounce off his shadow armor! Only Sunfang and arrows hurt him.")
            else:
                side = caves.sign(you.center[0] - king.center[0])    # push you out, back to his side you came from
                you.move_x((king.center[0] + side * (king.w + you.w) / 2 - you.center[0]))
                you.vx = 0.0

    def next_move(self):
        """He's done with what he was doing. What next? Fireballs every 3rd time, or when you're
        far away (but never two times in a row, and never when you're right next to him).
        The rest of the time he walks up to you and slashes."""
        king = self.king
        if self.up_high():                            # you're up in the nook: he can't reach you!
            king.doing, king.timer = "wait", 0.5
            self.tell_once("nook", "The Shadow King can't reach you up here! He waits for you to come down...")
            return
        king.attacks += 1
        if (king.attacks % 3 == 0 or self.gap() > FAR_AWAY) and not king.threw_last and self.gap() >= TOO_CLOSE:
            self.start_throwing()
        else:
            king.threw_last = False
            king.doing, king.timer = "walk", MAX_WALK

    def start_throwing(self):
        king = self.king
        king.threw_last = True
        king.doing, king.timer = "aim", king.normal_or_angry(THROW_WARNING)
        king.fireballs_left = king.normal_or_angry(FIREBALLS)
        self.game.sound("fuse")                       # his hand starts to glow...

    def throw_fireball(self):
        king = self.king
        x = king.center[0] + king.facing * (king.w / 2 + FIREBALL_SIZE / 2)
        self.fireballs.append({"x": x, "y": self.floor - FIREBALL_HEIGHT,
                               "vx": king.facing * king.normal_or_angry(FIREBALL_SPEED)})
        self.game.sound("shoot")
        king.fireballs_left -= 1
        if king.fireballs_left > 0:
            king.timer = FIREBALL_GAP                 # another one is coming!
        else:
            king.doing, king.timer = "wait", 0.6

    def move_fireballs(self, dt):
        you, half = self.you, FIREBALL_SIZE / 2
        for ball in list(self.fireballs):
            ball["x"] += ball["vx"] * dt
            front = ball["x"] + half * caves.sign(ball["vx"])
            if self.is_solid(math.floor(ball["y"]), math.floor(front)):
                self.fireballs.remove(ball)           # splat! it hit the wall
                self.game.effect("poof", cave_xy=(ball["x"], ball["y"]))
            elif you.safe_time <= 0 and you.touches(ball["x"] - half, ball["y"] - half, FIREBALL_SIZE, FIREBALL_SIZE):
                self.fireballs.remove(ball)
                self.game.log("A shadow fireball hits you! Jump over them!", "bad")
                self.hurt_you(FIREBALL_DAMAGE, ball["x"] - ball["vx"])
                return                                # (if that knocked you out, everything starts again)

    def hurt_king(self, damage, from_x):
        king, game = self.king, self.game
        king.health = max(0, king.health - damage)
        king.flash = 0.25
        king.safe_time = KING_SAFE_TIME
        if king.doing != "stuck":                     # he can't slide back while his sword is stuck
            king.vx = SLIDE_BACK * caves.sign(king.center[0] - from_x)
        game.effect("popup", cave_xy=(king.center[0], king.y), text="-%d" % damage, kind="bad")
        game.sound("hit")
        if not king.is_alive:
            self.beat_him()
        elif not king.angry and king.health <= king.max_health * ANGRY_AT:
            king.angry = True                         # half his health is gone: now he's ANGRY!
            game.log("The Shadow King ROARS! Now he's angry: faster, and two fireballs at a time!", "bad")
            game.sound("boom")
            game.effect("king_angry")

    def beat_him(self):
        king, game = self.king, self.game
        king.doing = "beaten"
        self.fireballs = []
        self.beaten_time = VICTORY_TIME
        game.log("Sunfang blazes! The Shadow King cracks like ice... and bursts into light!", "quest")
        game.sound("sunfang")
        game.effect("king_beaten", cave_xy=king.center)

    # ----- you fight back ----------------------------------------------------------------

    def use(self, down=False):
        """R swings Sunfang. If he's in reach, it hits him!"""
        you, king, p = self.you, self.king, self.game.player
        if you.swing > 0:
            return
        reach_x = you.x + you.w if you.facing > 0 else you.x - caves.SWORD_REACH
        if not (king.is_alive and king.touches(reach_x, you.y - 0.1, caves.SWORD_REACH, you.h + 0.2)):
            super().use(down)                         # a swing at nothing
            return
        you.swing = caves.SWING_TIME
        you.tool = "sunfang" if p.sunfang else "sword" if p.swords else "fist"
        if king.safe_time > 0:
            self.game.sound("miss")                   # too soon: he's still flashing from your last hit
            return
        self.hurt_king(self.swing_damage(), you.center[0])

    def swing_damage(self):
        """How hard your swing hits him. Sunfang's light burns him, and every light shard makes it burn more."""
        game, p = self.game, self.game.player
        if p.sunfang:
            return game.sunfang_damage() + game.ring_power() + p.light_shards * SHARD_BONUS
        return 1                                      # an ordinary sword (or your fist) only scratches him

    def move_arrows(self, dt):
        """Your arrows can hit him too (they only scratch him, though)."""
        king = self.king
        for arrow in list(self.arrows):
            if arrow.get("yours") and king.is_alive and king.touches(arrow["x"] - 0.15, arrow["y"] - 0.05, 0.3, 0.1):
                self.arrows.remove(arrow)
                if king.safe_time > 0:
                    self.game.sound("miss")
                else:
                    self.hurt_king(self.game.rng.randint(*ARROW_DAMAGE), arrow["x"] - arrow["vx"])
        super().move_arrows(dt)

    # ----- the healing nook ------------------------------------------------------------

    def by_the_spring(self):
        """Are you standing in the nook, next to the healing spring? (Anywhere in the nook counts.)"""
        you = self.you
        r, c = self.find("n")
        return abs(you.center[0] - (c + 0.5)) < 1.2 and abs(you.y + you.h - (r + 1)) < 0.1

    def heal_in_nook(self, dt):
        you, game, p = self.you, self.game, self.game.player
        if not self.by_the_spring():
            self.heal_timer = 0.0
            return
        if self.healing_left <= 0:
            self.tell_once("empty", "The healing spring is empty now. Go and beat him!")
            return
        if p.health >= p.max_health:
            self.tell_once("spring", "A healing spring! It has %d health in it, in all. Come back when you're hurt."
                           % self.healing_left)
            return
        self.heal_timer -= dt
        if self.heal_timer <= 0:
            self.heal_timer = NOOK_HEAL_EVERY
            self.healing_left -= p.heal(1)
            r, c = self.find("n")
            game.effect("popup", cave_xy=(c + 0.5, r), text="+1", kind="good")
            game.sound("heal")

    # ----- knocked out -----------------------------------------------------------------

    def back_to_start(self):
        """Knocked out: you wake up by the door. But he gets all his health back, and the spring fills up again."""
        super().back_to_start()
        self.king = ShadowKing(self, *self.king_start)
        self.fireballs = []
        self.arrows = []
        self.healing_left = NOOK_HEALING
        self.heal_timer = 0.0
