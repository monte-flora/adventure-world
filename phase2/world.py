"""
THE PHASE 2 GAME - the classic game (rules.Game) on a bigger world, with no fog, that saves itself.

Everything else (caves, Nightfall Hollow, the castle, the Shadow King) is the classic game's.
Later stages add people, quests and visible monsters here, not in rules.py.
"""

import rules
import story

from phase2 import fight, keys, main_quest, monsters, people, quests, save, side_steps, smooth, world_map
from phase2.waystones import WorldFeatures


class Phase2Game(WorldFeatures, rules.Game):      # WorldFeatures: waystones, lookouts, gates (waystones.py)
    phase2 = True
    cave_tips = keys.CAVE_TIPS                       # caves' first-time messages that name Phase 2's keys (G for levers)
    live = False                                     # True once the map runs in real time (smooth.live: the real game)
    hero_xy = None                                   # the Hero's middle on the map, [x, y] in squares (smooth.where)
    bump = None                                      # what he's pushing against: (which way, from which square)
    gloom = 0.0                                      # how much light the Shadow King has taken, 0.0 to 1.0 (gloom.py)
    gloom_told = False                               # has the game said "it's getting darker" yet?

    def __init__(self, player_name="Hero", seed=None, atlas=None):
        self.atlas = atlas or world_map.load()      # the big map, from the land files in levels/world/
        self.save_slot = 1                           # which of the 3 save slots this game saves into (save.py)
        self.play_time = 0.0                         # seconds played (not counting the pause menu)
        super().__init__(player_name, seed=seed)
        people.set_up(self)                          # townsfolk, quests, the shops and your gold
        main_quest.set_up(self)                      # stage 3a: the story, and the main quest's first chapter

    def world_map(self):
        """The hook rules.Game.__init__ calls for its map: ours is stitched from the land files."""
        return [row[:] for row in self.atlas.grid]

    def land_at(self, pos):
        if self.world != 1:
            return None
        return self.atlas.land_at(pos)

    # ----- no fog: you can see the whole world -----------------------------------------

    def is_visible(self, pos):
        return True

    def reveal(self):
        if len(self.seen) < self.rows * self.cols:
            self.seen = {(r, c) for r in range(self.rows) for c in range(self.cols)}

    # ----- saving by itself ---------------------------------------------------------------

    def autosave(self):
        """Save the game (see save.py). It never stops the game, even if saving doesn't work."""
        if self.over or self.battle:
            return False
        return save.save_game(self)

    def enter_cave(self):
        self.autosave()                         # saved on the map, just before you climb down
        return super().enter_cave()

    # ----- monsters you can see (monsters.py) and timing fights (fight.py) -------------------
    # The home world only: Nightfall Hollow keeps its classic shadow monsters and its moonrise.

    def spawn_monsters(self, counts, shadow=False):
        if self.world == 1 and not shadow:
            monsters.spawn_all(self)            # every land its own mix, each with a home spot
            people.keep_monsters_off(self)      # nobody spawns on (or walks onto) a person
            return self.monsters
        return super().spawn_monsters(counts, shadow)

    def move_monsters(self):
        if self.battle:
            return                              # a fight started this turn (you walked into one)
        if self.world != 1:
            super().move_monsters()
        elif not self.live:                     # a robot or a test playing turn by turn: a turn's worth of time.
            monsters.pass_time(self, monsters.TURN_SECONDS)     # (The real game: pass_time, every frame.)

    def archers_shoot(self):
        if not self.battle and self.world != 1:     # (at home Skeletons shoot by the clock: monsters.pass_time)
            super().archers_shoot()

    # ----- the map in real time (smooth.py): the Hero walks smoothly and the monsters roam ----------

    def walk(self, dx, dy, dt):
        """The Hero walks for dt seconds (dx, dy: -1, 0 or 1). Walk into a monster and the fight starts."""
        moved = smooth.walk(self, dx, dy, dt)
        if moved and self.world == 1 and not self.battle:
            monster = monsters.touch(self)
            if monster and self.battle and monsters.behind(self, monster):
                fight.first_strike(self, monster)       # ...from behind: a free hit!
        return moved

    def pass_time(self, dt):
        """The home map's monsters roam for dt seconds. (Nightfall Hollow's move when you take a step.)"""
        if self.world == 1 and not (self.battle or self.cave or self.over):
            monsters.pass_time(self, dt)

    def random_event(self):
        """Phase 2 has no random effects: no thistles that hurt, no random heals, no armor out of nowhere."""

    def end_of_turn(self, moved):
        super().end_of_turn(moved)
        if self.world == 1 and not self.won:
            monsters.turn_passed(self)          # night and day, beaten monsters coming back
            side_steps.check(self)              # side-quest goals done this turn

    def move(self, direction):
        if people.bump(self, direction):        # someone is there: you talk to them instead
            return False
        dr, dc = rules.DIRECTIONS[direction]
        target = self.monster_at((self.player.pos[0] + dr, self.player.pos[1] + dc))
        moved = super().move(direction)
        if moved and target and target.is_alive and target.pos == self.player.pos and self.here not in rules.SAFE:
            self.start_battle(target)           # you walked into it...
            if self.battle and monsters.from_behind(target, direction):
                fight.first_strike(self, target)    # ...from behind: a free hit!
        if moved and self.here == "H":          # in at a house (or a shrine in Nightfall Hollow)
            self.autosave()
        return moved

    def start_battle(self, monster):
        if self.battle:
            return                              # already fighting
        super().start_battle(monster)
        self.battle.bar = fight.StrikeBar(self.rng)
        self.battle.grade = None

    def player_attack(self, monster):
        return fight.strike_damage(self, monster, fight.take_grade(self))

    def battle_action(self, action):
        b = self.battle
        super().battle_action(action)
        if b and b.result == "fled" and hasattr(b.monster, "calm"):
            b.monster.calm, b.monster.state = monsters.CALM_SECONDS, "home"   # it lets you go for a bit

    def monster_gone(self, monster, give_xp):
        super().monster_gone(monster, give_xp)
        if self.world == 1:
            monsters.beaten(self, monster)      # it comes back, slowly
            quests.monster_beaten(self, monster)        # it counts for the main quest and the side quests

    # ----- the main quest (phase2/main_quest.py): what its steps wait for --------------------

    def leave_cave(self):
        cave = self.cave
        super().leave_cave()
        if self.world == 1 and not cave.is_castle and cave.result == "exit":
            quests.notice(self, "cave", self.land_name(cave.mine_pos))

    def climb_lookout(self):
        climbed = super().climb_lookout()
        quests.notice(self, "lookout", self.land_name(self.player.pos))
        return climbed

    def gain_xp(self, amount, quiet=False):
        result = super().gain_xp(amount, quiet)
        if getattr(self, "quest_state", None):
            quests.notice(self, "level")
        return result

    @property
    def portal_open(self):
        if not hasattr(self, "quest_state"):        # (rules.Game.__init__, before the quests are set up)
            return False
        return main_quest.portal_ready(self)

    def check_portal(self):
        if main_quest.at_portal(self):
            self.go_to_nightfall()

    def go_to_nightfall(self):
        main_quest.leave_home(self)             # the home world comes back after the end
        quests.notice(self, "portal")
        super().go_to_nightfall()

    def open_castle(self):
        super().open_castle()
        quests.notice(self, "castle")

    def beat_the_king(self):
        """You beat the Shadow King! In Phase 2 the story ends, and then you go home and keep playing."""
        if self.king_beaten:
            return
        self.king_quest.advance()
        self.log("You defeated the Shadow King! The light is coming back!", "quest")
        self.quest_xp()
        self.sound("win")
        self.tell(story.THE_LIGHT_COMES_BACK)
        main_quest.the_end(self)

    # ----- people (phase2/people.py) -------------------------------------------------------

    def tile_action(self):
        if self.here in people.TALK_FROM and people.talk_next_to(self):   # SPACE next to someone: talk
            return False
        return super().tile_action()

    def forge_problem(self):
        if people.smith_next_to(self):          # at the blacksmith's anvil you can forge anywhere
            return people.anvil_problem(self)
        return super().forge_problem()

    def give_loot(self, kind, xp):
        return people.gold_coins(self, super().give_loot(kind, xp), xp)
