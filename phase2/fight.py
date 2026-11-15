"""
FIGHTS IN PHASE 2 - the classic fight box, but Attack is a TIMING STRIKE.

A marker sweeps back and forth along a bar (like the forge's). Press R when it's in the zone:
  gold  = PERFECT: extra damage
  green = GOOD: a normal hit
  else  = MISS: a weak hit (it still does a little)
Running and eating work like before, and so does the short pause between turns (BATTLE_PAUSE in game.py).

Walk into a monster from behind and you get a FIRST STRIKE: a free hit before the fight even starts.
This file knows nothing about graphics: draw_fight.py draws the bar.
"""

import math

import rules

STRIKE_GREEN = 0.28             # the green zone is 28% of the bar...
STRIKE_GOLD = 0.09              # ...with a gold zone in its middle (9% of the bar)
STRIKE_SPEED = 0.9              # the marker crosses the bar this many times a second
PERFECT_BONUS = 1.5             # a Perfect strike does 1.5x the damage (and at least 2 more)
WEAK_HIT = 1                    # a Miss still does this much
GRADE_WORDS = {"perfect": "PERFECT!", "good": "Good hit!", "miss": "Miss..."}


class StrikeBar:
    """The timing bar in a fight. Where the marker is depends only on the clock, so it's easy to test."""

    def __init__(self, rng, start=0.0):
        self.rng = rng
        self.start = start            # the clock time the marker started sweeping
        self.last = None              # the last strike's grade ("perfect", "good" or "miss")
        self.new_zone()

    def new_zone(self):
        self.zone_x = round(self.rng.uniform(0.05, 0.95 - STRIKE_GREEN), 3)
        self.zone_w = STRIKE_GREEN
        self.gold_x = self.zone_x + (STRIKE_GREEN - STRIKE_GOLD) / 2
        self.gold_w = STRIKE_GOLD

    def pos_at(self, time):
        """0.0 (left) to 1.0 (right): the marker bounces from end to end."""
        t = max(0.0, time - self.start) * STRIKE_SPEED % 2
        return t if t <= 1 else 2 - t

    def grade(self, pos):
        if self.gold_x <= pos <= self.gold_x + self.gold_w:
            return "perfect"
        if self.zone_x <= pos <= self.zone_x + self.zone_w:
            return "good"
        return "miss"

    def strike(self, time):
        """Press R now: how good was it? Then the zone moves for next time."""
        self.last = self.grade(self.pos_at(time))
        self.new_zone()
        self.start = time
        return self.last


def strike_damage(game, monster, grade):
    """How hard a timing strike hits. Uses up a hit of your sword (but a Miss doesn't).
    Returns the damage (always at least WEAK_HIT: even a Miss does a little)."""
    p = game.player
    if grade == "miss":
        game.battle_line("Miss... a weak hit for %d." % WEAK_HIT)
        game.sound("miss")
        return WEAK_HIT
    if p.sunfang:
        damage = game.sunfang_damage(monster.special) + game.ring_power()
        name = "Sunfang blazes"
    elif not p.swords:
        damage, name = 1, "You punch it"
    else:
        damage = game.rng.randint(2, 6) + p.damage_bonus
        if monster.special == "tough":
            damage = max(1, damage - 1)
        damage += game.ring_power()
        name = "Your sword hits"
    if grade == "perfect":
        damage = max(damage + 2, math.ceil(damage * PERFECT_BONUS))
    game.battle_line("%s%s for %d damage!" % ("PERFECT! " if grade == "perfect" else "", name, damage), "good")
    if p.swords and not p.sunfang:
        if p.swords[0].use():
            p.swords.pop(0)
            game.battle_line("Your sword broke! Swords left: %d" % len(p.swords), "bad")
        game.check_chipped_swords()
    return damage


def first_strike(game, monster):
    """You sneaked up from behind: a free Good hit before the fight starts. Might even win it!"""
    b = game.battle
    game.battle_line("FIRST STRIKE! You sneak up behind the %s!" % monster.kind, "good")
    damage = strike_damage(game, monster, "good")
    monster.health = max(0, monster.health - damage)
    game.effect("battle_hit", target="monster", amount=damage)
    game.sound("hit")
    if not monster.is_alive:
        b.result = "won"
        game.battle_line("You defeated the %s!" % monster.kind, "quest")
        game.sound("victory")
        game.monster_gone(monster, give_xp=True)


def battle_action(game, action, time):
    """A key in a fight. Phase 2: Attack is graded by the timing bar first. Classic: just the classic action."""
    b = game.battle
    bar = getattr(b, "bar", None)
    if action == "attack" and bar is not None and not b.over:
        b.grade = bar.strike(time)
    game.battle_action(action)


def take_grade(game):
    """The grade of the strike that's happening (Good if nothing graded it, like a test or a robot)."""
    b = game.battle
    grade = getattr(b, "grade", None) or "good"
    if b is not None:
        b.grade = None
    return grade
