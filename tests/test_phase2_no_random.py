"""T5: Phase 2 has no random effects (thistles that hurt, random heals, random armor). Classic keeps them."""

import rules
from phase2.world import Phase2Game


def forest_spot(world):
    for r, row in enumerate(world.map):
        for c, t in enumerate(row):
            if t == "F" and not world.monster_at((r, c)):
                return (r, c)
    raise AssertionError("no forest square")


def a_game(cls, **kw):
    world = cls("Hero", seed=3, **kw)
    world.story.clear()
    world.monsters = []                     # nothing around to hurt or bother you
    world.player.pos = forest_spot(world)   # the forest is where random things happen most
    world.player.health = world.player.max_health - 3     # room for a random heal to show
    return world


def test_phase2_never_has_a_random_event():
    world = a_game(Phase2Game)
    world.rng.random = lambda: 0.0          # every roll would hurt you (or heal you) in Classic
    health, armor = world.player.health, world.player.has_armor
    for _ in range(500):
        world.end_of_turn(moved=True)
    assert world.player.health == health and world.player.has_armor == armor
    ouches = {line for lines in rules.LAND_INJURIES.values() for line in lines}
    ouches |= {line for lines in rules.INJURIES.values() for line in lines} | set(rules.HEALS)
    assert not [text for text, _ in world.messages if text in ouches]


def test_classic_still_has_random_events(monkeypatch):
    calls = []
    monkeypatch.setattr(rules.Game, "random_event", lambda self: calls.append(self.turn))
    world = a_game(rules.Game)
    for _ in range(10):
        world.end_of_turn(moved=True)
    assert len(calls) == 10


def test_classic_thistle_still_hurts():
    world = a_game(rules.Game)
    world.rng.random = lambda: 0.0
    health = world.player.health
    world.random_event()
    assert world.player.health < health
