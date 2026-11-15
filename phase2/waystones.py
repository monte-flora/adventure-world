"""
WAYSTONES, LOOKOUTS, HIDDEN CHESTS AND GATES - the Phase 2 world's own rules (stage 2a).

With no fog there's nothing to uncover, so the landmarks get new jobs:

- A WAYSTONE is a land's landmark (the L), and your home. Walk onto one and it lights up (it's
  unlocked). Stand on any lit waystone and press SPACE: a list of the lit ones opens, and you can
  travel to any of them (it takes one turn).
- A LOOKOUT is a wooden tower (a "lookout:" line in a land file). Climb it with SPACE and you spot
  the nearest hidden treasure chest: it shows up on the map and the minimap.
- Treasure chests (T) on the Phase 2 map are HIDDEN in the grass until a lookout spots them, or you
  step right onto one.
- A GATE ("gate:" line) is a rock in the way until you're strong enough: at that level it opens.
- Home is where the "home:" line says (not the last H), so villages can be anywhere.

WorldFeatures is mixed into Phase2Game (phase2/world.py). It knows nothing about graphics.
"""

import rules

HOME_NAME = "Home"
# What's in a chest in the new lands (the classic lands keep rules.MAP_CHEST_PRIZES)
CHEST_PRIZES = {"Frost Peaks": ["armor"], "Sunscorch Desert": ["armor", "arrows"], "Murk Swamp": ["food", "arrows"],
                "Home Meadow": ["food"]}
FEATURES = {"unlocked_waystones": set, "lookouts_climbed": set, "found_chests": set, "gates_open": set}


def after_load(game):
    """A save from before stage 2a has none of these: start them fresh."""
    for name, make in FEATURES.items():
        if not hasattr(game, name):
            setattr(game, name, make())
    if not game.unlocked_waystones:
        game.unlocked_waystones.add(game.start)
    game.travel_open = False


class WorldFeatures:
    """Waystones, lookouts, hidden chests and gates. Needs self.atlas (a world_map.Atlas)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unlocked_waystones = {self.start}      # spots of the waystones you've lit (home is lit from the start)
        self.lookouts_climbed = set()
        self.found_chests = set()                   # hidden chests you've spotted (or stepped on)
        self.gates_open = set()
        self.travel_open = False                    # True: the graphics show the travel list

    # ----- home -------------------------------------------------------------------------------

    def find_tile(self, letter, last=False):
        if letter == "H" and last and self.world == 1 and getattr(self.atlas, "home", None):
            return self.atlas.home                  # home is where the home: line says
        return super().find_tile(letter, last)

    # ----- what's where -----------------------------------------------------------------------

    @property
    def waystones(self):
        """{spot: name} of every waystone: home, and the landmark in each land."""
        if self.world != 1:
            return {}
        stones = {spot: self.tile_name(spot) for spot in self.landmarks if self.tile(spot) == "L"}
        stones[self.start] = HOME_NAME
        return stones

    @property
    def lookouts(self):
        return list(self.atlas.lookouts) if self.world == 1 else []

    def hidden_chests(self):
        """Treasure chests on the map that you haven't spotted yet."""
        if self.world != 1:
            return []
        return [spot for spot in rules.tiles_of(self.map, "T") if spot not in self.found_chests]

    def chest_hidden(self, pos):
        return self.world == 1 and self.tile(pos) == "T" and pos not in self.found_chests

    def gate_at(self, pos):
        """(name, level) if a closed gate is here."""
        if self.world != 1 or pos in self.gates_open:
            return None
        return self.atlas.gates.get(pos)

    def village_at(self, pos, how_far=3):
        for name, square, _ in getattr(self.atlas, "villages", []) if self.world == 1 else []:
            if rules.distance(pos, square) <= how_far:
                return name
        return None

    # ----- walking ----------------------------------------------------------------------------

    def move(self, direction):
        dr, dc = rules.DIRECTIONS[direction]
        ahead = (self.player.pos[0] + dr, self.player.pos[1] + dc)
        gate = self.in_bounds(ahead) and self.gate_at(ahead)
        if gate and not self.open_gate(ahead):
            self.player.facing = direction
            return False
        moved = super().move(direction)
        if moved and self.world == 1:
            self.arrive()
        return moved

    def arrive(self):
        here = self.player.pos
        stones = self.waystones
        if here in stones and here not in self.unlocked_waystones:
            self.unlocked_waystones.add(here)
            self.log("The %s waystone lights up! Press SPACE on any lit waystone to travel." % stones[here], "quest")
            self.popup(here, "waystone!", "quest")
            self.effect("tile", pos=here)
            self.sound("quest")
        if here in self.lookouts:
            self.log("A lookout tower! Press SPACE to climb it and look for hidden treasure.", "good")
        if self.chest_hidden(here):
            self.found_chests.add(here)             # you stumbled right onto a hidden chest
            self.effect("tile", pos=here)

    def open_gate(self, pos):
        name, level = self.atlas.gates[pos]
        if self.player.level < level:
            self.log("The %s is shut tight. It opens for heroes of level %d (you're level %d)."
                     % (name, level, self.player.level), "quest")
            return False
        self.gates_open.add(pos)
        self.map[pos[0]][pos[1]] = "R"
        self.effect("tile", pos=pos)
        self.log("The %s rumbles open for you, level %d hero!" % (name, self.player.level), "good")
        self.sound("quest")
        return True

    # ----- SPACE ------------------------------------------------------------------------------

    def tile_action(self):
        here = self.player.pos
        if self.world == 1 and here in self.lookouts:
            return self.climb_lookout()
        if self.world == 1 and here in self.unlocked_waystones:
            used = super().tile_action()            # still climb the landmark (or rest at home)
            if len(self.unlocked_waystones) > 1:
                self.travel_open = True
            else:
                self.log("Light more waystones (walk onto a land's landmark) to travel between them.")
            return used
        return super().tile_action()

    def climb_lookout(self):
        """Climb a lookout tower: the nearest hidden chest shows up on the map and the minimap."""
        here = self.player.pos
        self.lookouts_climbed.add(here)
        hidden = sorted(self.hidden_chests(), key=lambda spot: (rules.distance(spot, here), spot))
        self.effect("lookout", pos=here)
        if not hidden:
            self.log("You climb the lookout and look all around. No more hidden treasure anywhere!")
            return True
        spot = hidden[0]
        self.found_chests.add(spot)
        self.effect("tile", pos=spot)
        self.effect("sparkle", pos=spot)
        self.log("From the top of the lookout you spot a hidden chest, %s! It's on your map now."
                 % ("right here" if spot == here else "to the " + rules.compass(here, spot)), "loot")
        self.sound("pickup")
        return True

    # ----- travel -----------------------------------------------------------------------------

    def travel_choices(self):
        """[(name, spot), ...]: the lit waystones you can travel to from here, home first."""
        stones = self.waystones
        choices = [(stones[spot], spot) for spot in self.unlocked_waystones if spot in stones and spot != self.player.pos]
        return sorted(choices, key=lambda it: (it[0] != HOME_NAME, it[0], it[1]))

    def close_travel(self):
        self.travel_open = False

    def travel(self, spot):
        """Travel to a lit waystone. Returns True if you went (it takes a turn)."""
        self.travel_open = False
        if self.world != 1 or self.cave or self.battle or self.over:
            return False
        if spot not in self.unlocked_waystones or spot not in self.waystones or self.player.pos not in self.unlocked_waystones:
            return False
        self.player.pos = spot
        self.log("Whoosh! The waystones carry you to the %s." % self.waystones[spot], "good")
        self.effect("travel", pos=spot)
        self.sound("quest")
        self.reveal()
        self.check_new_land()
        self.end_of_turn(False)
        return True

    # ----- chests -----------------------------------------------------------------------------

    def open_map_chest(self):
        p = self.player
        if self.world != 1:
            return super().open_map_chest()
        land = self.land_name(p.pos)
        prizes = CHEST_PRIZES.get(land) or rules.MAP_CHEST_PRIZES.get(land, ["gold"])
        self.log("You open the treasure chest!", "loot")
        words = [self.map_prize(prize) for prize in prizes]
        self.popup(p.pos, "  ".join(words), "loot")
        self.map[p.pos[0]][p.pos[1]] = "G"
        self.found_chests.discard(p.pos)
        self.effect("tile", pos=p.pos)
        return True
