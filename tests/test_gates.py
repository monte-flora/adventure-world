"""
The gates of the home world: places you can't get to straight away.

    The Frosty Corner    the Icy River (~) and the Frost Wall close it in. Fix the broken
                         bridge (=) with 5 wood, or row across the lake. The Hunter's Lodge
                         is just over the bridge.
    The Watchtower       its door is locked. The key is in the chest deep in the woods.
                         From the top you can see the whole map.
    The Lighthouse       climb it, and every Mine that still has a diamond sparkles.
    The Secret Mine (S)  hidden deep in the woods. The Queen Oak gives you a hint.
                         It has a cave of its own, and it always has a diamond.

These tests find things by their letter, so they keep working when you change the map.
"""

import caves
import rules
import robot
from helpers import new_world, ok, tiles


def the(world, name):
    """Where the landmark (or the Hunter's Lodge) with this name is."""
    return next(spot for r in range(world.rows) for c in range(world.cols)
                for spot in [(r, c)] if world.tile_name(spot) == name)


def walk_on_foot(world):
    """Every square you can walk to from home, without a boat and without fixing the bridge."""
    found, todo = {world.start}, [world.start]
    while todo:
        for spot in world.neighbors(todo.pop()):
            if spot not in found:
                found.add(spot)
                todo.append(spot)
    return found


def frosty_corner(world):
    return [(r, c) for r in range(world.rows) for c in range(world.cols)
            if world.land_name((r, c)) == "Frosty Corner" and world.tile((r, c)) not in "WX="]


# ===========================================================================
# The Frosty Corner: the Icy River, the broken bridge and the Frost Wall
# ===========================================================================

def test_the_icy_river_runs_into_the_lake():
    world = new_world()
    ok(world.river and all(world.tile(spot) == "W" for spot in world.river), "the Icy River is water")
    ok(any(spot[0] == 0 for spot in world.river), "it starts at the top edge of the map")
    mouth = max(world.river)                        # the bottom end of the river
    ok(len(world.reach(mouth, water=True)) > len(world.river), "...and runs down into the lake, so you can row up it")
    ok(world.tile_name(mouth) == "Icy River", "it's called the Icy River")


def test_the_frosty_corner_is_closed_in():
    world = new_world()
    on_foot = walk_on_foot(world)
    corner = frosty_corner(world)
    ok(corner and not any(spot in on_foot for spot in corner),
       "you can't walk into the Frosty Corner until you fix the bridge (or row there)")
    ok(all(spot in world.mainland for spot in corner), "...but once the bridge is fixed you can walk everywhere in it")
    bridge = tiles(world, "=")
    ok(len(bridge) == 1 and world.land_name(bridge[0]) == "Frosty Corner", "there's one broken bridge, into the Frosty Corner")
    shore = [spot for spot in corner if any(world.tile(beside) == "W" and beside not in world.river
                                             for beside in world.neighbors(spot, water=True))]
    ok(shore, "you can also row across the lake and land on the Frosty Corner's shore")


def test_the_broken_bridge_needs_wood():
    world = new_world()
    bridge = tiles(world, "=")[0]
    world.player.pos = (bridge[0], bridge[1] - 1)                   # on the path, just before the bridge
    world.player.wood = rules.BRIDGE_WOOD - 1
    ok(not world.do("right") and world.player.pos != bridge, "without enough wood you can't get onto the broken bridge")
    ok("Bring %d wood" % rules.BRIDGE_WOOD in world.messages[-1][0], "...and you're told how much wood to bring")
    world.player.wood = rules.BRIDGE_WOOD + 2
    ok(world.do("right") and world.player.pos == bridge, "carrying %d wood, you walk onto the bridge..." % rules.BRIDGE_WOOD)
    ok(world.tile(bridge) == "#" and world.player.wood == 2, "...and fix it with %d of your wood" % rules.BRIDGE_WOOD)
    ok(world.do("right") and world.tile_name(world.player.pos) == "Hunter's Lodge",
       "just over the bridge is the Hunter's Lodge")
    ok(world.land_name(world.player.pos) == "Frosty Corner" and "Frosty Corner" in world.lands_seen,
       "the Hunter's Lodge is in the Frosty Corner")
    world.do("left")
    ok(world.tile(bridge) == "#" and world.player.wood == 2, "a fixed bridge stays fixed (no more wood needed)")


def test_the_frost_wall_tells_you_the_way_in():
    world = new_world()
    wall = [spot for spot in tiles(world, "X") if world.land_name(spot) == "Frosty Corner"
            and world.in_bounds((spot[0] + 1, spot[1])) and world.land_name((spot[0] + 1, spot[1])) != "Frosty Corner"]
    ok(len(wall) >= 5, "the Frost Wall closes the Frosty Corner from the south (%d rocks)" % len(wall))
    below = (wall[0][0] + 1, wall[0][1])
    world.player.pos = below
    ok(not world.do("up") and world.player.pos == below, "you can't climb the Frost Wall")
    ok("bridge" in world.messages[-1][0], "...but it tells you the way in: %r" % world.messages[-1][0])


def test_a_house_you_build_isnt_the_lodge():
    world = new_world()
    world.player.pos = tiles(world, "G")[0]
    world.map[world.player.pos[0]][world.player.pos[1]] = "H"
    ok(world.tile_name(world.player.pos) == "House", "a house you build is just a house")
    ok(world.tile_name(world.start) == "House", "...and so is home")


# ===========================================================================
# The Watchtower and its key
# ===========================================================================

def test_the_watchtower_is_locked_until_you_find_the_key():
    world = new_world()
    tower = the(world, "Watchtower")
    world.player.pos = tower
    before = set(world.seen)
    ok(not world.do("act") and world.seen == before, "the Watchtower is locked: you can't climb it")
    ok("woods" in world.messages[-1][0], "...and you get a hint where the key is: %r" % world.messages[-1][0])
    chest = next(spot for spot in tiles(world, "T") if world.land_name(spot) == "Whispering Woods")
    world.player.pos = chest
    world.do("act")
    ok(world.player.has_tower_key, "the chest deep in the woods has the Watchtower key")
    world.player.pos = tower
    ok(world.do("act"), "with the key, you climb the Watchtower")
    everywhere = {(r, c) for r in range(world.rows) for c in range(world.cols)}
    ok(world.seen == everywhere, "from the top of the Watchtower you can see the WHOLE map")


# ===========================================================================
# The Lighthouse
# ===========================================================================

def test_the_lighthouse_shows_every_diamond():
    world = new_world()
    lighthouse = the(world, "Lighthouse")
    ok(lighthouse not in world.mainland, "the Lighthouse is on an island: you row there")
    world.cleared_mines = {min(world.cave_plan)}
    world.player.pos = lighthouse
    ok(world.do("act") and world.lighthouse_lit, "you climb the Lighthouse and light its lamp")
    wanted = world.diamond_mines - world.cleared_mines - set(world.secret_mines)
    ok(world.glints == wanted, "every Mine that still has a diamond sparkles (%d of them)" % len(wanted))
    world.player.pos = world.start
    world.end_of_turn(moved=True)
    ok(world.glints == wanted, "...and they keep sparkling after you climb down")


# ===========================================================================
# The Secret Mine
# ===========================================================================

def test_the_secret_mine_has_its_own_cave():
    world = new_world()
    secret = tiles(world, "S")
    ok(len(secret) == 1 and set(world.secret_mines) == set(secret), "there's one Secret Mine on the map")
    spot = secret[0]
    ok(world.land_name(spot) == "Whispering Woods" and spot in world.mainland,
       "it's hidden in the Whispering Woods (and you can walk there)")
    ok(spot not in world.cave_plan, "it's not in the cave plan...")
    mines = tiles(world, "M")
    ok(world.cave_plan.keys() == set(mines), "...so the other %d Mines keep their caves" % len(mines))
    text = world.secret_mines[spot]
    ok("*" in text and spot in world.diamond_mines, "the Secret Mine always has a diamond")
    ok(text in caves.SECRET_CAVES and text not in world.cave_plan.values(),
       "its cave is a file of its own in levels/secret, not the same as any other cave")
    ok(rules.Game("Someone", seed=99).secret_mines == world.secret_mines, "every game gets the same secret cave")
    world.player.pos = spot
    world.do("act")
    ok(world.cave is not None and world.cave.mine_pos == spot, "press SPACE and you climb down into it")


def test_the_secret_cave_can_be_beaten():
    world = new_world()
    for spot, text in world.secret_mines.items():
        beaten, how = robot.beat(text)
        ok(beaten, "the cave under the Secret Mine at %s: %s" % (spot, how))
        ok(caves.level_theme(text), "it has a theme (a look) of its own")


def test_the_queen_oak_hints_at_the_secret_mine():
    world = new_world()
    world.player.pos = the(world, "Queen Oak")
    world.do("act")
    words = [text for text, kind in world.messages[-4:]]
    hint = [text for text in words if "mine door" in text]
    direction = rules.compass(world.player.pos, next(iter(world.secret_mines)))
    ok(hint and direction in hint[0], "from the Queen Oak you spot the Secret Mine, to the %s: %r" % (direction, words))
    ok(not set(world.secret_mines) & world.glints, "...but it never sparkles: it's a secret!")
