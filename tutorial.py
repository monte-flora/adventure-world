"""
Tips: little bubbles that explain the game, the first time you find something new.

Each tip has:
  - a name, like "forest"
  - its words (in TIPS, just below - try changing them!)
  - a "moment": a little check that says when the tip fits, like "you're standing in a forest".
    It says WHERE the tip should point, or None if it's not time for that tip yet.

A few times a second, game.py asks TipBook.due() which tips fit right now. It shows the
first one in a bubble that points at the thing it's about, and the game waits while you
read it. ENTER (or SPACE, or a click) closes it, and S says "no more tips".

Every tip shows only once. The game remembers which ones you've seen, and whether tips
are on, even after you close it (see settings.py). On the title screen, TAB turns tips
on or off. Turning them back on shows them all again, from the start.
"""

import math

import caves
import rules
import settings

START_WITH_TIPS = True      # tips are on for a new player (until you turn them off)

# ===========================================================================
# THE WORDS IN EACH BUBBLE
# Keep them short: a bubble only has room for about 3 lines.
# ===========================================================================
TIPS = {
    # On the world map
    "walk":     "This is you! Press the ARROW keys to walk around. Press H any time for help.",
    "monster":  "A monster! Walk into it to start a fight. In a fight, press A to attack!",
    "eat":      "Ouch, you're hurt! Press E to eat some food and feel better.",
    "forest":   "A forest! Press T to chop wood, and SPACE to look for berries to eat.",
    "craft":    "You have wood! Press C to open the Craft menu and make things with it.",
    "bow":      "You have a bow! Press F to shoot an arrow the way you're facing.",
    "water":    "Water! You can't swim. Craft a boat (C) with %d wood, then walk into the water to row."
                % rules.BOAT_COST,
    "mine":     "A Mine! Walk onto it and press SPACE to climb down into its cave.",
    "landmark": "A landmark! Walk onto it and press SPACE to climb up and look far away.",
    "land":     "A new land! Its name is up here. Every land has a landmark to climb. Can you find them all?",
    "portal":   "The Portal! Beat %d monsters and mine %d diamonds, and it opens. It's your way out!"
                % (rules.MONSTERS_TO_DEFEAT, rules.DIAMONDS_NEEDED),
    "path":     rules.FIRST_TIME_TIPS["R"][1],      # these four are the same words as in the message log
    "map ice":  rules.FIRST_TIME_TIPS["I"][1],
    "reeds":    rules.FIRST_TIME_TIPS["B"][1],
    "vent":     rules.FIRST_TIME_TIPS["V"][1],
    # In a cave
    "cave":     "You're in a cave! ARROWS run and SPACE jumps (hold it to jump higher). "
                "Walk out on the left to leave.",
    "cave monster": "A monster! Jump on its head, or stand next to it and press R to swing your sword.",
    "diamond":  "A diamond! Stand next to it and press R to dig it out.",
    "dig":      "Cracked rock! Stand next to it and press R to dig. DOWN and R digs the floor.",
    "chest":    "A treasure chest! Walk up to it and press R to open it.",
    "exit":     "The EXIT door! Walk through it when you're done exploring.",
    "ladder":   caves.TIPS["ladder"],               # and these six are the cave's own tips
    "vine":     caves.TIPS["vine"],
    "wall":     caves.TIPS["wall"],
    "tunnel":   caves.TIPS["tunnel"],
    "cave ice": caves.TIPS["ice"],
    "swing":    caves.TIPS["swing"],
}

NEAR = 4                    # in a cave, a ladder, chest or door gets a tip when it's this many blocks away
TOO_CLOSE = 3               # a cave monster this close? You're busy fighting: no tips until it's gone

# ===========================================================================
# WHERE A TIP CAN POINT
#   ("you",)              you - on the map, or in a cave
#   ("map", (row, col))   a square on the world map
#   ("cave", (row, col))  a block in the cave
#   ("panel", "food")     a part of the side panel: "food", "wood", "bow" or "here"
# ===========================================================================


def nearest_on_map(game, letters, how_far):
    """The nearest square with one of these letters that you've seen, no more than how_far squares away."""
    r0, c0 = game.player.pos
    found = [(rules.distance((r, c), (r0, c0)), (r, c))
             for r in range(r0 - how_far, r0 + how_far + 1) for c in range(c0 - how_far, c0 + how_far + 1)
             if game.in_bounds((r, c)) and game.map[r][c] in letters and (r, c) in game.seen]
    return ("map", min(found)[1]) if found else None


def nearest_in_cave(cave, is_it, how_far=NEAR):
    """The nearest block in the cave where is_it(row, col) is True, no more than how_far blocks from you."""
    x, y = cave.center
    best = None
    for r in range(int(y) - how_far, int(y) + how_far + 1):
        for c in range(int(x) - how_far, int(x) + how_far + 1):
            if 0 <= r < cave.rows and 0 <= c < cave.cols and is_it(r, c):
                far = (c + 0.5 - x) ** 2 + (r + 0.5 - y) ** 2
                if best is None or far < best[0]:
                    best = (far, (r, c))
    return ("cave", best[1]) if best else None


def block(letters):
    """A check for nearest_in_cave: is this block one of these letters?"""
    return lambda cave: nearest_in_cave(cave, lambda r, c: cave.map[r][c] in letters)


def low_tunnel(cave):
    """A gap only one block high, with rock above and below: you have to crawl through it."""
    return nearest_in_cave(cave, lambda r, c: not cave.is_solid(r, c) and cave.is_solid(r - 1, c)
                           and cave.is_solid(r + 1, c), how_far=2)


def swinging_vine_nearby(cave):
    """A swinging vine (R) close by: point at the bottom of it."""
    x, y = cave.center
    near = []
    for swing in getattr(cave, "swings", ()):
        tip_x, tip_y = swing.point(swing.length)
        far = math.hypot(tip_x - x, tip_y - y)
        if far <= NEAR + 1:
            near.append((far, (min(int(tip_y), cave.rows - 1), int(tip_x))))
    return ("cave", min(near)[1]) if near else None


def monster_distance(cave, m):
    x, y = cave.center
    return ((m.x + m.w / 2 - x) ** 2 + (m.y + m.h / 2 - y) ** 2) ** 0.5


# ===========================================================================
# THE MOMENTS: when does each tip fit? Each one says where to point, or None.
# ===========================================================================

# ----- on the world map ------------------------------------------------------

def at_the_start(game):
    return ("you",) if game.turn == 1 else None


def monster_in_sight(game):
    near = [(rules.distance(m.pos, game.player.pos), m.pos) for m in game.monsters
            if m.is_alive and game.is_visible(m.pos)]
    return ("map", min(near)[1]) if near else None


def hurt_with_food(game):
    p = game.player
    return ("panel", "food") if p.health <= p.max_health // 2 and p.food > 0 else None


def in_a_forest(game):
    return ("you",) if game.here == "F" else None


def got_wood(game):
    return ("panel", "wood") if game.player.wood >= rules.BOW_COST else None    # a bow is the cheapest thing


def got_a_bow(game):
    return ("panel", "bow") if game.player.has_bow and game.player.arrows else None


def water_next_to_you(game):
    if game.player.has_boat:
        return None
    water = game.neighbors(game.player.pos, water=True)
    return ("map", water[0]) if water else None


def mine_nearby(game):
    return nearest_on_map(game, "M", 3)


def landmark_in_sight(game):
    return nearest_on_map(game, "L", rules.LANDMARK_SIGHT)


def new_land(game):
    return ("panel", "here") if game.world == 1 and len(game.lands_seen) > 1 else None


def portal_in_sight(game):
    return nearest_on_map(game, "P", 4) if game.world == 1 else None


def standing_on(letter):
    """A moment for one of the map's first-time tips: you're standing on this kind of square."""
    return lambda game: ("you",) if game.world == 1 and game.here == letter else None


# ----- in a cave -------------------------------------------------------------

def just_came_in(cave):
    return ("you",) if not cave.is_castle else None


def cave_monster_nearby(cave):
    near = [(monster_distance(cave, m), m) for m in cave.monsters if monster_distance(cave, m) < 7]
    if not near:
        return None
    m = min(near, key=lambda pair: pair[0])[1]
    return ("cave", (int(m.y + m.h / 2), int(m.x + m.w / 2)))


def on_the_map(moment):
    """This moment only happens on the world map."""
    return lambda game: None if game.cave else moment(game)


def in_a_cave(moment):
    """This moment only happens in a cave (it's given the cave, not the game)."""
    return lambda game: moment(game.cave) if game.cave else None


# Every tip and its moment, the most important first. When two tips fit at once, the
# higher one shows first, and the other one waits its turn.
MOMENTS = [
    ("walk",         on_the_map(at_the_start)),
    ("cave",         in_a_cave(just_came_in)),
    ("monster",      on_the_map(monster_in_sight)),
    ("cave monster", in_a_cave(cave_monster_nearby)),
    ("eat",          hurt_with_food),                    # on the map and in caves
    ("forest",       on_the_map(in_a_forest)),
    ("path",         on_the_map(standing_on("R"))),
    ("map ice",      on_the_map(standing_on("I"))),
    ("reeds",        on_the_map(standing_on("B"))),
    ("vent",         on_the_map(standing_on("V"))),
    ("water",        on_the_map(water_next_to_you)),
    ("craft",        on_the_map(got_wood)),
    ("bow",          got_a_bow),
    ("mine",         on_the_map(mine_nearby)),
    ("landmark",     on_the_map(landmark_in_sight)),
    ("land",         on_the_map(new_land)),
    ("portal",       on_the_map(portal_in_sight)),
    ("ladder",       in_a_cave(block("H"))),
    ("vine",         in_a_cave(block("V"))),
    ("swing",        in_a_cave(swinging_vine_nearby)),
    ("wall",         in_a_cave(block(caves.CLIMB_WALL))),
    ("tunnel",       in_a_cave(low_tunnel)),
    ("cave ice",     in_a_cave(block(caves.ICE))),
    ("diamond",      in_a_cave(block("*"))),
    ("dig",          in_a_cave(block("B"))),
    ("chest",        in_a_cave(block("T"))),
    ("exit",         in_a_cave(block("E"))),
]


# ===========================================================================
# THE TIP BOOK: which tips you've seen, and whether tips are on
# ===========================================================================

class TipBook:
    def __init__(self):
        saved = settings.load()
        self.on = saved.get("tips", START_WITH_TIPS)
        self.seen = set(saved.get("tips_seen", []))

    def due(self, game):
        """Every tip that fits right now and you haven't seen yet, most important first: (name, where)."""
        if not self.on:
            return
        cave = game.cave
        if cave and cave.is_throne_room:
            return                                  # never while you fight the Shadow King
        if cave and any(monster_distance(cave, m) < TOO_CLOSE for m in cave.monsters):
            return                                  # a monster is right there: fight first, read later
        for name, moment in MOMENTS:
            if name not in self.seen:
                where = moment(game)
                if where:
                    yield name, where

    def saw(self, name):
        """You read this tip (and closed it): it won't show again."""
        self.seen.add(name)
        self.save()

    def turn_off(self):
        """S in a bubble: no more tips."""
        self.on = False
        self.save()

    def switch(self):
        """TAB on the title screen: tips on or off. Turning them on shows every tip again."""
        self.on = not self.on
        if self.on:
            self.seen.clear()
        self.save()

    def save(self):
        settings.save(tips=self.on, tips_seen=sorted(self.seen))
