"""
The lands of the home world: each one has its own look, a landmark (L), and one new thing.

    Frosty Corner     ice (I) slides you until you bump into something
    Misty Marsh       reeds (B) hide you, so monsters can't chase you
    Ember Canyon      rocks (X) and steam vents (V) that puff every 3rd turn
    Old Ruins         broken walls (X) and Skeletons

Plus treasure chests (T), a sunken chest under bubbles (O) and signposts (+).
These tests find things by their letter, so they keep working when you change the map.
"""

import game
import rules
from helpers import FakeDice, frames, new_app, new_world, ok, tiles


def walk_to(world, spot):
    """Stand right next to spot (on a square you can walk on), and return the way you'd step onto it."""
    for direction, (dr, dc) in rules.DIRECTIONS.items():
        beside = (spot[0] - dr, spot[1] - dc)
        if world.in_bounds(beside) and world.tile(beside) in "GR":
            world.player.pos = beside
            return direction
    raise AssertionError("nowhere to stand next to %s" % (spot,))


# ===========================================================================
# The lands and their landmarks
# ===========================================================================

def test_every_land_has_its_landmark():
    world = new_world()
    names = {world.land_name(spot) for spot in world.landmarks}
    wanted = {land[0] for land in rules.LANDS if land[5]}
    ok(names == wanted, "every land has one landmark on the map: %s" % sorted(wanted - names))
    ok(all(world.tile_name(spot) == world.land_at(spot)[5] for spot in world.landmarks),
       "a landmark is called by its own name, like 'Windmill'")
    ok(world.land_name(world.start) == "Home Meadow", "you start at home, in the Home Meadow")


def test_you_can_see_a_landmark_from_far_away():
    world = new_world()
    windmill = next(spot for spot in world.landmarks if world.tile_name(spot) == "Windmill")
    world.seen = set()
    world.player.pos = (windmill[0], windmill[1] + rules.LANDMARK_SIGHT)      # far away, in the fog
    world.reveal()
    ok(windmill in world.seen, "you can see the Windmill from %d squares away" % rules.LANDMARK_SIGHT)
    ok((windmill[0], windmill[1] + 1) not in world.seen, "...but not the grass right next to it")


def test_climbing_a_landmark_lifts_the_fog_and_shows_diamonds():
    world = new_world()
    world.player.has_tower_key = True               # the Watchtower is locked without it (see test_gates.py)
    diamonds = world.diamond_mines - set(world.secret_mines)       # the Secret Mine never sparkles
    for spot in world.landmarks:
        name = world.tile_name(spot)
        world.player.pos = spot
        world.seen, world.glints = set(), set()
        ok(world.do("act"), "climbing the %s takes a turn" % name)
        far = [s for s in world.seen if world.close_to(s, spot, rules.LOOKOUT_SIGHT) and not world.close_to(s, spot, 2)]
        ok(far, "from the %s you can see far around" % name)
        nearby = {m for m in diamonds if world.close_to(m, spot, rules.LOOKOUT_SIGHT)}
        ok(world.glints == (diamonds if name == "Lighthouse" else nearby),
           "from the %s you see a sparkle over the Mines %s that have a diamond"
           % (name, "everywhere" if name == "Lighthouse" else "nearby"))
    world.glints = set()
    for spot in world.landmarks:
        if world.tile_name(spot) != "Lighthouse":
            world.player.pos = spot
            world.climb_landmark()
    ok(world.glints, "some Mines with a diamond can be spotted from a landmark (%d)" % len(world.glints))


def test_monsters_cant_reach_you_on_a_landmark():
    world = new_world()
    landmark = world.landmarks[0]
    world.player.pos = landmark
    world.monsters = [rules.Monster("Spider", landmark)]            # even if one is right there...
    world.end_of_turn(moved=False)
    ok(world.battle is None, "monsters can't attack you up on a landmark")
    nearby = rules.Monster("Spider", (landmark[0] + 1, landmark[1]))
    world.monsters = [nearby]
    world.rng = FakeDice(rest=0.0)
    for _ in range(10):
        world.move_monsters()
    ok(nearby.pos != landmark, "...and they never climb onto one")


def test_the_first_time_you_walk_into_a_land():
    world = new_world()
    canyon = next(spot for spot in tiles(world, "G") if world.land_name(spot) == "Ember Canyon")
    step = walk_to(world, canyon)
    world.lands_seen.discard("Ember Canyon")
    if world.land_name(world.player.pos) == "Ember Canyon":
        world.player.pos = (canyon[0] - 1, canyon[1])                 # stand just outside it
        step = "down"
    world.take_effects()
    world.do(step)
    banners = [e for e in world.take_effects() if e["type"] == "land"]
    ok(banners and banners[0]["text"] == "EMBER CANYON", "walking into Ember Canyon shows its name")
    ok(any("Ember Canyon" in words for words, kind in world.messages[-3:]), "...and tells you what's special there")


# ===========================================================================
# Ice, reeds, rocks and steam vents
# ===========================================================================

def test_you_slide_on_ice():
    world = new_world()
    # find a spot on solid ground, next to the ice, where you'd slide more than one square
    for ice in tiles(world, "I"):
        for step, (dr, dc) in rules.DIRECTIONS.items():
            before, after = (ice[0] - dr, ice[1] - dc), (ice[0] + dr, ice[1] + dc)
            if world.tile(before) in "GR" and world.tile(after) in rules.WALKABLE:
                stop = ice                              # where you should end up: slide on until the ice ends
                while world.tile(stop) == "I" and world.tile((stop[0] + dr, stop[1] + dc)) in rules.WALKABLE:
                    stop = (stop[0] + dr, stop[1] + dc)
                world.player.pos = before
                world.do(step)
                ok(world.player.pos == stop, "one step onto the ice slides you all the way to %s" % (stop,))
                return
    ok(False, "the map needs some ice you can slide across")


def slide_spots(world, start):
    """Everywhere you can get to from start, walking and sliding (no boat)."""
    found, todo = {start}, [start]
    while todo:
        spot = todo.pop()
        for dr, dc in rules.DIRECTIONS.values():
            nxt = (spot[0] + dr, spot[1] + dc)
            if not world.in_bounds(nxt) or world.tile(nxt) not in rules.WALKABLE:
                continue
            while world.tile(nxt) == "I":
                ahead = (nxt[0] + dr, nxt[1] + dc)
                if not world.in_bounds(ahead) or world.tile(ahead) not in rules.WALKABLE:
                    break
                nxt = ahead
            if nxt not in found:
                found.add(nxt)
                todo.append(nxt)
    return found


def test_the_ice_never_traps_you():
    world = new_world()
    for r, c in tiles(world, "="):
        world.map[r][c] = "#"                           # you fixed the bridge into the Frosty Corner
    places = slide_spots(world, world.start)
    stuck = [spot for spot in places if world.tile(spot) == "I" and world.start not in slide_spots(world, spot)]
    ok(not stuck, "wherever you stop on the ice, you can always get back home: %s" % stuck[:3])
    icy_chests = [chest for chest in tiles(world, "T") if world.land_name(chest) == "Frosty Corner"]
    ok(icy_chests and all(chest in places for chest in icy_chests), "you can slide your way to the frozen chest")


def test_reeds_hide_you_from_monsters():
    world = new_world()
    reeds = next(spot for spot in tiles(world, "B")
                 if all(world.tile((spot[0], spot[1] + dc)) in rules.WALKABLE for dc in (1, 2)))
    world.player.pos = reeds
    for under_you, chases in (("B", False), ("G", True)):
        world.map[reeds[0]][reeds[1]] = under_you
        spider = rules.Monster("Spider", (reeds[0], reeds[1] + 2))     # 2 squares to your right
        world.monsters = [spider]
        world.rng = FakeDice()                  # it moves, to the first square it picks
        world.move_monsters()
        ok((rules.distance(spider.pos, reeds) < 2) == chases, "a Spider %s you when you're in the %s"
           % ("comes after" if chases else "can't find", rules.TILE_NAMES[under_you]))


def test_mud_in_the_reeds():
    world = new_world()
    world.player.pos = tiles(world, "B")[0]
    world.player.health = 10
    world.rng = FakeDice(rolls=[0.01])
    world.random_event()
    ok(world.player.health == 9 and world.messages[-1][0] in rules.INJURIES["B"], "the mud in the reeds can trip you up")


def test_you_cant_walk_through_rock():
    world = new_world()
    rock = tiles(world, "X")[0]
    step = walk_to(world, rock)
    here = world.player.pos
    ok(not world.do(step) and world.player.pos == here, "a rock is in the way: you stay where you are")
    ok(rock not in world.mainland, "nobody can ever stand on a rock")


def test_steam_vents_puff_every_few_turns():
    world = new_world()
    world.player.pos = tiles(world, "V")[0]
    hurt = []
    for turn in range(1, 3 * rules.VENT_EVERY + 1):
        world.player.health = 20
        world.turn = turn - 1
        world.end_of_turn(moved=False)
        hurt.append(world.player.health < 20)
    ok(hurt.count(True) == 3 and all(hurt[i] == ((i + 1) % rules.VENT_EVERY == 0) for i in range(len(hurt))),
       "standing on a steam vent hurts on every %d-th turn, and only then: %s" % (rules.VENT_EVERY, hurt))
    world.turn = rules.VENT_EVERY - 1
    ok(world.vent_puffing(world.turn + 1), "the turn before it puffs, you can tell it's about to blow (the wisp)")


def test_snow_and_sand_have_their_own_bad_luck():
    world = new_world()
    for land in rules.LAND_INJURIES:
        world.player.pos = next(spot for spot in tiles(world, "G") if world.land_name(spot) == land)
        world.rng = FakeDice(rolls=[0.01])
        world.random_event()
        ok(world.messages[-1][0] in rules.LAND_INJURIES[land], "bad luck in the %s: %r" % (land, world.messages[-1][0]))


# ===========================================================================
# Treasure: chests, the sunken chest and signposts
# ===========================================================================

def test_treasure_chests_on_the_map():
    world = new_world()
    for chest in tiles(world, "T"):
        world.player.pos = chest
        world.player.food, world.player.armor, world.player.has_bow, world.player.has_tower_key = 0, 0, False, False
        ok(world.do("act") and world.tile(chest) == "G", "the chest in the %s opens, and then it's gone"
           % world.land_name(chest))
        prizes = rules.MAP_CHEST_PRIZES[world.land_name(chest)]
        p = world.player
        got = {"food": p.food > 0, "armor": p.has_armor, "bow": p.has_bow, "arrows": p.arrows > 0, "gold": True,
               "key": p.has_tower_key}
        ok(all(got[prize] for prize in prizes), "the %s chest gives you %s" % (world.land_name(chest), prizes))
    ok(not world.do("act"), "an opened chest can't be opened again")


def test_the_sunken_chest():
    world = new_world()
    ok(len(world.sunken_chests) == 1, "there's a sunken chest in the lake")
    bubbles = next(iter(world.sunken_chests))
    ok(world.tile(bubbles) == "W", "...under the water (you need a boat to get there)")
    world.player.pos = bubbles
    ok(world.do("act") and world.player.ring_hits == rules.RING_HITS and not world.sunken_chests,
       "row over the bubbles and press SPACE: you dive and find a diamond ring")


def test_signposts_point_the_way():
    world = new_world()
    for sign in tiles(world, "+"):
        world.player.pos = sign
        world.do("act")
        words = world.messages[-1][0]
        ok(words.count(":") == 3 and any(d in words for d in ("north", "south", "east", "west")),
           "the signpost at %s names 3 lands and which way they are: %r" % (sign, words))


# ===========================================================================
# Monsters live in their own lands
# ===========================================================================

def test_monsters_live_in_their_lands():
    for seed in range(5):
        world = rules.Game("Hero", seed=seed)
        for kind, land in rules.MONSTER_LANDS.items():
            them = [m for m in world.monsters if m.kind == kind]
            at_home = [m for m in them if world.land_name(m.pos) == land]
            ok(len(at_home) >= len(them) * rules.IN_THEIR_LAND,
               "at least half of the %ss start in the %s (%d of %d)" % (kind, land, len(at_home), len(them)))


# ===========================================================================
# The pictures
# ===========================================================================

def test_every_land_has_its_own_look():
    app = new_app()
    frames(app, 2)
    world = app.game
    snow = next(spot for spot in tiles(world, "G") if world.land_name(spot) == "Frosty Corner")
    grass = next(spot for spot in tiles(world, "G") if world.land_name(spot) == "The Great Lake")
    ok(app.tiles[snow].get_at((1, 1)) != app.tiles[grass].get_at((1, 1)), "the Frosty Corner's fields are snowy, not green")
    for spot in world.landmarks + tiles(world, "X") + tiles(world, "I") + tiles(world, "B") + tiles(world, "V"):
        ok(spot in app.tiles, "the %s at %s has a picture" % (world.tile_name(spot), spot))
    world.player.pos = world.landmarks[0]
    world.seen.update(world.landmarks)
    app.state = "play"
    frames(app, 3)                   # draws the windmill's sails, steam, bubbles and the panel without a crash
