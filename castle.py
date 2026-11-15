"""
THE SHADOW KING'S CASTLE

The castle plays just like a cave - caves.py does all the running, jumping
and bumping - but game.py draws it as a spooky castle: stone bricks,
flickering torches, purple banners and moonlit windows.

The castle has 5 levels, and the door at the end of each one is LOCKED.
Find the key (or pull the lever) somewhere in the level to open it. The
locked door gives you a clue if you walk up to it. Behind the door of
level 5 is the throne room!

Each level also hides a healing fountain and a light shard. Light shards
make Sunfang glow brighter, and you'll want them when you meet the Shadow King...

If you get knocked out in here, you don't lose the game: the Shadow King's
magic throws you back to the start of the level with full health. Guards you
beat stay beaten, so you get a little farther every time.
"""


import caves

# ===========================================================================
# CASTLE SETTINGS - try changing these!
# ===========================================================================
# (How fast a healing fountain fills up again is FOUNTAIN_REFILL in caves.py: caves have healing springs too.)
SHARD_XP = 10              # every light shard you find is worth this much XP

# ===========================================================================
# THE CASTLE LEVELS - one text file each, in the levels/castle folder, in order (1 to 5).
# Open one in the cave editor (pixi run editor), change it and press Save.
# Each file starts with a few setting lines:
#   name: The Great Hall                 the level's name
#   locked door says: Locked! ...        what the locked door says when you don't have the key yet
# levels/README.md says what every letter means. The castle has a few of its own:
#   K = the key    L = a lever (press R next to it; G in Phase 2)    D = the locked door to the next level
#   + = a light shard    u = a healing fountain    i = torch, w = moonlit window, f = banner (just for looks)
# The gap in the left wall is the way back: in level 1 it's the castle gate, out
# into Nightfall Hollow. In the other levels it's the door back to the level before.
# ===========================================================================
CASTLE_LEVEL_FILES = caves.level_files("castle")
CASTLE_LEVELS = [
    # (its name, its drawing, what the locked door says when you don't have the key yet)
    (caves.level_setting(text, "name"), text, caves.level_setting(text, "locked door says"))
    for path, text in CASTLE_LEVEL_FILES
]


class Castle(caves.Cave):
    """One level of the castle: a cave with a locked door, a key or a lever, a fountain and a light shard."""
    is_castle = True
    SPRING = "fountain"                 # a healing spring in a cave, a healing fountain in the castle

    def __init__(self, game, gate, changes=None, level=0):
        self.level = level                  # 0 is level 1, 1 is level 2... (computers like to count from 0)
        self.name, drawing, self.riddle = CASTLE_LEVELS[level]
        super().__init__(game, gate, drawing, changes)
        self.needs = "key" if "K" in drawing else "lever" if "L" in drawing else None   # what opens the door
        self.door_open = not self.spots("D")
        self.has_key = self.needs == "key" and not self.spots("K") and not self.door_open
        self.at_door = False                # so the clue only shows once each time you walk up to the door

    def spots(self, letter):
        """Everywhere in this level that has this letter."""
        return [(r, c) for r, row in enumerate(self.map) for c, tile in enumerate(row) if tile == letter]

    def last_level(self):
        return self.level == len(CASTLE_LEVELS) - 1

    def goal(self):
        """What to do next in this level (the panel shows it)."""
        if self.door_open:
            return "Door: open!"
        if self.has_key:
            return "Key: got it!"
        return "%s: find it!" % (self.needs or "door").title()

    # ----- every frame ----------------------------------------------------------

    def update(self, dt, controls):
        super().update(dt, controls)                 # (the fountains fill up again in caves.py, like healing springs)
        if self.result == "exit" and not self.last_level():
            self.game.enter_castle_level(self.level + 1)               # through the door to the next level
        elif self.result == "left" and self.level > 0:
            self.game.enter_castle_level(self.level - 1, back=True)    # back the way you came

    def check_where_you_are(self):
        super().check_where_you_are()                # spikes, lava, gems, going through a door...
        if self.result:
            return
        you, at_door = self.you, False
        for r in you.rows():
            for c in you.cols():
                tile = self.tile(r, c)
                if tile == "K":
                    self.pick_up_key(r, c)
                elif tile == "+":
                    self.pick_up_shard(r, c)
                elif tile == "D":
                    at_door = True
        if at_door and not self.at_door:
            self.try_door()
        self.at_door = at_door

    # ----- keys, levers and doors -------------------------------------------------

    def pick_up_key(self, r, c):
        game = self.game
        self.change(r, c, ".")
        self.has_key = True
        game.log("You found the key! Now take it to the locked door.", "loot")
        game.sound("pickup")
        game.effect("sparkle", cave_xy=(c + 0.5, r + 0.5))
        game.effect("popup", cave_xy=(c + 0.5, r), text="KEY!", kind="loot")

    def try_door(self):
        """You walked up to the locked door."""
        game = self.game
        if self.has_key:
            self.has_key = False
            game.log("Click! The key turns in the lock, and the door swings open.", "good")
            self.open_door()
            return
        game.log(self.riddle, "quest")
        game.sound("miss")
        r, c = self.spots("D")[0]
        game.effect("popup", cave_xy=(c + 0.5, r - 2), text="LOCKED!", kind="bad")

    def lever_pulled(self, opened_gates):
        """A lever in the castle opens the locked door (and any iron gates, in caves.py)."""
        if self.needs == "lever" and not self.door_open:
            self.game.log("CLUNK! You pull the lever. Somewhere, a door creaks open...", "good")
            self.open_door()
        else:
            super().lever_pulled(opened_gates)

    def open_door(self):
        for r, c in self.spots("D"):
            self.change(r, c, "E")                   # an open door: walk into it to go through
        self.door_open = True
        self.game.sound("door")

    def stand_by_door(self):
        """You came back from the next level: you're standing just in front of this level's door."""
        r, c = (self.spots("E") or self.spots("D"))[0]
        you = self.you
        you.x, you.y = c - 1 + (1 - caves.PLAYER_W) / 2, r + 1 - caves.PLAYER_H
        you.facing = -1
        you.safe = (you.x, you.y)
        you.safe_time = caves.SAFE_TIME

    # ----- light shards (the healing fountains work like the springs in caves.py) ----------

    def pick_up_shard(self, r, c):
        game, p = self.game, self.game.player
        self.change(r, c, ".")
        p.light_shards += 1
        game.log("A light shard! Sunfang glows brighter. (%d of %d)" % (p.light_shards, len(CASTLE_LEVELS)), "loot")
        game.sound("diamond")
        game.effect("sparkle", cave_xy=(c + 0.5, r + 0.5))
        game.effect("popup", cave_xy=(c + 0.5, r), text="+%d XP" % SHARD_XP, kind="loot")
        game.gain_xp(SHARD_XP, quiet=True)
