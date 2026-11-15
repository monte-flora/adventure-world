"""
Arrows hit a little harder now (3-5), and once you step through the Portal into
Nightfall Hollow they burst into FIRE ARROWS: they hit even harder, and you can see
the flame on them - in the shadow caves, on the dark map and in the throne room.
"""

import rules
import throne
from helpers import DT, FakeDice, cave_from, frames, new_app, new_world, ok, run, tiles, walk_into_a_mine
from test_bow_and_rings import FLAT, archer, next_to
from test_nightfall_and_castle import in_nightfall_hollow


def test_arrows_hit_a_little_harder():
    world = new_world()
    ok(rules.ARROW_DAMAGE == (3, 5), "an arrow hits 3-5 (it was 2-4)")
    world.rng = FakeDice(ints=[3])
    ok(world.arrow_damage() == 3, "the smallest arrow hit is 3")
    world.rng = FakeDice(ints=[5])
    ok(world.arrow_damage() == 5, "the biggest arrow hit is 5")
    world.rng = FakeDice(ints=[3])
    ok(world.arrow_damage("tough") == 2, "tough monsters still take 1 less")
    ok(throne.ARROW_DAMAGE == (2, 3), "arrows hit the Shadow King for 2-3 (it was 1-2)")


def test_arrows_turn_into_fire_arrows_in_nightfall_hollow():
    world = new_world()
    ok(not world.player.fire_arrows, "at home your arrows are plain arrows")
    in_nightfall_hollow(world)
    ok(world.player.fire_arrows, "through the Portal they become fire arrows")
    ok(any("burst into flame" in words for words, *_ in world.messages), "and the game tells you so")
    world.rng = FakeDice(ints=[3])
    ok(world.arrow_damage() == 3 + rules.FIRE_ARROW_BONUS, "a fire arrow hits %d harder" % rules.FIRE_ARROW_BONUS)


def test_a_fire_arrow_on_the_dark_map():
    world = in_nightfall_hollow(new_world())
    p = archer(world, arrows=2)
    world.map[p.pos[0]][p.pos[1] + 1] = world.map[p.pos[0]][p.pos[1] + 2] = "G"
    zombie = world.new_monster("Zombie", shadow=True)
    zombie.pos = next_to(p.pos, 2)
    world.monsters = [zombie]
    health = zombie.health
    world.take_effects()
    world.rng = FakeDice(ints=[3], rest=0.99)
    world.do("shoot")
    ok(zombie.health == health - (3 - 1 + rules.FIRE_ARROW_BONUS), "a fire arrow hits a shadow Zombie for 4 (3, -1 tough, +2 fire)")
    arrow = next(e for e in world.take_effects() if e["type"] == "arrow")
    ok(arrow["fire"], "the arrow flying over the map is on fire")
    ok("fire arrow" in world.messages[-1][0] or any("fire arrow" in m for m, *_ in world.messages[-3:]),
       "the message says it was a fire arrow")


def shoot_a_zombie_in_a_cave(world):
    world, cave = cave_from(FLAT[:12] + ["..S......z...#"] + FLAT[13:], world)
    p = world.player
    p.has_bow, p.arrows = True, 3
    zombie = cave.monsters[0]
    zombie.speed = 0
    health = zombie.info.health
    cave.you.facing = 1
    world.rng = FakeDice(ints=[3])
    cave.update(DT, {"shoot_pressed": True})
    flying = list(cave.arrows)
    run(cave, 60)
    return flying, health - zombie.info.health


def test_fire_arrows_in_a_cave_hit_harder():
    plain, plain_hit = shoot_a_zombie_in_a_cave(new_world())
    fire, fire_hit = shoot_a_zombie_in_a_cave(in_nightfall_hollow(new_world()))
    ok(not plain[0].get("fire") and fire[0]["fire"], "only the Nightfall arrow is a fire arrow")
    ok(fire_hit == plain_hit + rules.FIRE_ARROW_BONUS, "fire arrows hit %d harder (%d vs %d)" % (rules.FIRE_ARROW_BONUS, fire_hit, plain_hit))


def test_the_pack_says_fire_arrows(monkeypatch):
    app = new_app()
    in_nightfall_hollow(app.game)
    app.game.player.has_bow, app.game.player.arrows = True, 7
    said = []
    real_text = app.text

    def text(surf, words, *rest, **more):
        said.append(words)
        return real_text(surf, words, *rest, **more)
    monkeypatch.setattr(app, "text", text)
    frames(app, 2)
    ok("7 fire arrows" in said, "the pack shows your fire arrows")


def test_a_fire_arrow_is_drawn_in_a_shadow_cave():
    app = new_app()
    world = in_nightfall_hollow(app.game)
    cave = walk_into_a_mine(app)
    world.player.has_bow, world.player.arrows = True, 5
    cave.you.reload = 0
    cave.update(DT, {"shoot_pressed": True})
    ok(cave.arrows and cave.arrows[-1]["fire"], "you shoot a fire arrow in a shadow cave")
    frames(app, 3)                                  # drawing it (and its embers) works
