"""
The world map: forests and fields, chopping trees, houses, armor, boats and
Sea Serpents, rowing out to the Portal, and the camera that follows you around.

These tests find places by their letter (F = Forest, G = Field, M = Mine,
W = Water, P = Portal, R = Path, H = House) instead of using spots on the map,
so they keep working when you change the map.

The map: a big lake with the Portal's island in the middle, and a brown path (R)
that goes around the lake like a horseshoe, far from the water and the trees. Its two
ends lead to the Frosty Corner: the broken bridge (=) and the Frost Wall. On the path
monsters don't chase you, Skeletons can't shoot you, and no bad (or good) luck happens.
"""

import collections

import game
import rules
from helpers import FakeDice, frames, new_app, new_world, ok, tiles, walk_into_a_mine


def boat_trip(world, start, goal):
    """The moves ("up", "left", ...) that get you from start to goal the shortest way,
    walking on land and rowing on water (so you need a boat). None if there's no way there."""
    came_from = {start: None}
    todo = collections.deque([start])
    while todo:
        spot = todo.popleft()
        for direction, (dr, dc) in rules.DIRECTIONS.items():
            nxt = (spot[0] + dr, spot[1] + dc)
            if world.in_bounds(nxt) and world.tile(nxt) in rules.WALKABLE + "W" and nxt not in came_from:
                came_from[nxt] = (spot, direction)
                todo.append(nxt)
    if goal not in came_from:
        return None
    moves = []
    while came_from[goal]:
        goal, direction = came_from[goal]
        moves.append(direction)
    return moves[::-1]


def big_lake(world):
    """The water squares of the biggest lake."""
    water, lakes = set(tiles(world, "W")), []
    while water:
        lakes.append(world.reach(water.pop(), water=True))
        water -= lakes[-1]
    return max(lakes, key=len)


def on_the_mainland(world, letter):
    """Every spot with this letter that you can walk to from home (no boat needed)."""
    return [spot for spot in tiles(world, letter) if spot in world.mainland]


# ===========================================================================
# The map
# ===========================================================================

def test_the_map_is_a_rectangle():
    world = new_world()
    ok(all(len(row) == world.cols for row in world.map),
       "every row of the map is %d squares long, so it's a rectangle" % world.cols)


def test_the_portal_is_on_an_island():
    world = new_world()
    ok(world.portal not in world.mainland, "the Portal can't be reached on foot")
    ok(boat_trip(world, world.start, world.portal) is not None, "...but it can by boat (it's on an island)")


def test_there_is_wood_and_mines_on_the_mainland():
    world = new_world()
    ok(tiles(world, "F") and tiles(world, "G"), "the map has forest squares and open fields")
    ok(on_the_mainland(world, "F"), "there's a forest you can walk to from home (you need its wood for a boat)")
    mines = on_the_mainland(world, "M")
    ok(len(mines) >= rules.DIAMONDS_NEEDED, "there are plenty of Mines you can walk to (%d)" % len(mines))


def test_every_mine_has_its_own_cave():
    world = new_world()
    mines = tiles(world, "M")
    ok(len(set(world.cave_plan.values())) == len(mines), "every one of the %d Mines has its own cave" % len(mines))


def test_you_start_in_the_last_house():
    world = new_world()
    ok(world.start == tiles(world, "H")[-1] == world.player.pos,
       "you start at home: the last H on the map (any other H is a rest house)")


def test_one_big_lake_with_islands_in_it():
    world = new_world()
    water = set(tiles(world, "W"))
    lake = big_lake(world)
    cut_off = water - lake
    ok(len(lake) >= rules.BIG_LAKE and cut_off <= world.river and len(cut_off) < rules.BIG_LAKE,
       "all the water is one big lake (%d squares), big enough for Sea Serpents - except the top of the Icy River,"
       " above the bridge (%d squares, too small for Sea Serpents)" % (len(lake), len(cut_off)))
    land = {(r, c) for r in range(world.rows) for c in range(world.cols) if world.map[r][c] not in "WX"}
    islands = land - world.mainland
    ok(world.reach(world.portal) <= islands and len(islands) < 40,
       "you can walk everywhere from home, except a few islands in the lake (%d squares), like the Portal's" % len(islands))
    ok(all(boat_trip(world, world.start, spot) for spot in islands), "...and you can row to every one of them")
    on_island = [world.tile(spot) for spot in world.reach(world.portal)]
    ok(on_island.count("M") == 1 and "F" in on_island, "the Portal's island has a Mine and some trees too")


# ===========================================================================
# The path (R): a brown horseshoe around the lake
# ===========================================================================

def squares_around(world, spot, how_far):
    """Every square in a little box around spot, how_far squares out (diagonals too)."""
    return [(r, c) for r in range(spot[0] - how_far, spot[0] + how_far + 1)
            for c in range(spot[1] - how_far, spot[1] + how_far + 1) if world.in_bounds((r, c))]


def next_to(world, spot):
    return [(spot[0] + dr, spot[1] + dc) for dr, dc in rules.DIRECTIONS.values() if world.in_bounds((spot[0] + dr, spot[1] + dc))]


def test_the_path_is_a_horseshoe_around_the_lake():
    world = new_world()
    path = set(tiles(world, "R"))
    joins = {square: sum(spot in path for spot in next_to(world, square)) for square in path}
    ends = [square for square in path if joins[square] == 1]
    along, todo = {ends[0]}, [ends[0]]                  # walk along the path from one end
    while todo:
        for spot in next_to(world, todo.pop()):
            if spot in path and spot not in along:
                along.add(spot)
                todo.append(spot)
    ok(len(ends) == 2 and set(joins.values()) == {1, 2} and along == path,
       "the path is one long line with 2 ends, like a horseshoe (%d squares, %d ends)" % (len(path), len(ends)))
    by_the_end = [world.tile(spot) for end in ends for spot in next_to(world, end)]
    frost_wall = [spot for end in ends for spot in next_to(world, end)
                  if world.tile(spot) == "X" and world.land_name(spot) == "Frosty Corner"]
    ok("=" in by_the_end and frost_wall, "one end of the path is at the broken bridge, the other at the Frost Wall")
    # walk from the corner of the map without stepping on the path (or the bridge): you never get to the lake
    lake = big_lake(world)
    corner, todo = {(0, 0)}, [(0, 0)]
    while todo:
        for spot in next_to(world, todo.pop()):
            if spot not in corner and spot not in path and world.tile(spot) not in "WX=":
                corner.add(spot)
                todo.append(spot)
    ok(not any(spot in lake for square in corner for spot in next_to(world, square)),
       "the path, the Icy River and the Frost Wall go all the way around the lake")
    ok(all(any(spot in path or world.tile(spot) in "=#" for spot in next_to(world, house)) for house in tiles(world, "H")),
       "every house is right next to the path (or the bridge)")


def test_the_path_stays_far_from_water_and_trees():
    world = new_world()
    bridges = tiles(world, "=")
    for spot in tiles(world, "R"):
        if any(rules.distance(spot, bridge) <= 2 for bridge in bridges):
            continue                                    # the path runs right up to the bridge over the Icy River
        near = [world.tile(square) for square in squares_around(world, spot, 2)]
        ok("W" not in near and "F" not in near,
           "no water or trees within 2 squares of the path at %s - you have to leave the path to find them" % (spot,))


def test_you_can_see_the_mines_from_the_path():
    world = new_world()
    for mine in on_the_mainland(world, "M"):
        if world.land_name(mine) == "Frosty Corner":
            continue                                    # the Frosty Corner is wild: no path in there
        world.player.pos = mine
        ok(not any(world.tile(spot) == "R" for spot in next_to(world, mine)),
           "the Mine at %s doesn't touch the path: you step off onto the grass to go in" % (mine,))
        ok(any(world.is_visible(spot) for spot in tiles(world, "R")),
           "...but you can see the Mine at %s from the path" % (mine,))


def test_strong_monsters_start_far_from_home():
    for seed in range(20):
        world = rules.Game("Hero", seed=seed)
        for monster in world.monsters:
            far = rules.MONSTER_START_DISTANCE.get(monster.kind, 5)
            ok(rules.distance(monster.pos, world.start) >= far and world.tile(monster.pos) != "R",
               "%s starts %d squares from home (it should be %d or more), and not on the path"
               % (monster.kind, rules.distance(monster.pos, world.start), far))


# ===========================================================================
# Walking on the path
# ===========================================================================

def a_path_square(world, *room):
    """A path square with walkable squares at these (row, column) steps away from it."""
    return next(spot for spot in tiles(world, "R")
                if all(world.in_bounds((spot[0] + dr, spot[1] + dc)) and
                       world.tile((spot[0] + dr, spot[1] + dc)) in "FGMR" for dr, dc in room))


def test_nothing_happens_on_the_path():
    world = new_world()
    world.player.pos = tiles(world, "R")[0]
    world.player.health = 10
    for roll in (0.0, 0.05, 0.1):          # on a forest or a field these would hurt you, or heal you
        world.rng = FakeDice(rolls=[roll, 0.0])
        world.random_event()
    ok(world.player.health == 10 and not world.player.has_armor, "on the path nothing happens: no injuries, no heals, no armor")


def test_fields_have_thistles():
    world = new_world()
    world.player.pos = tiles(world, "G")[0]
    world.player.health = 10
    world.rng = FakeDice(rolls=[0.01])
    world.random_event()
    ok(world.player.health == 9 and world.messages[-1][0] in rules.INJURIES["G"],
       "a bad roll on a field hurts you: %r" % world.messages[-1][0])


def test_monsters_dont_chase_you_on_the_path():
    world = new_world()
    you = a_path_square(world, (0, 1), (0, 2), (-1, 2))
    world.player.pos = you
    for under_you, chases in (("R", False), ("G", True)):
        world.map[you[0]][you[1]] = under_you
        spider = rules.Monster("Spider", (you[0], you[1] + 2))     # 2 squares to your right
        world.monsters = [spider]
        world.rng = FakeDice()                  # it moves, to the first square it picks
        world.move_monsters()
        closer = rules.distance(spider.pos, you) < 2
        ok(closer == chases, "a Spider 2 squares away %s when you're on the %s"
           % ("comes after you" if chases else "doesn't come after you", rules.TILE_NAMES[under_you]))


def test_skeletons_cant_shoot_you_on_the_path():
    world = new_world()
    you = a_path_square(world, (0, 2))
    world.player.pos = you
    for under_you, hurt in (("R", 0), ("G", 1)):
        world.map[you[0]][you[1]] = under_you
        world.monsters = [rules.Monster("Skeleton", (you[0], you[1] + 2))]
        world.player.health = 10
        world.rng = FakeDice(rest=0.0)          # it always gets a shot... if it's allowed to shoot
        world.archers_shoot()
        ok(world.player.health == 10 - hurt, "on the %s a Skeleton's arrow does %d damage" % (rules.TILE_NAMES[under_you], hurt))


def test_a_monster_can_still_bump_into_you_on_the_path():
    world = new_world()
    you = a_path_square(world, (1, 0))
    world.player.pos = you
    world.monsters = [rules.Monster("Spider", (you[0] + 1, you[1]))]   # right below you
    world.rng = FakeDice()                      # it wanders up... onto your square
    world.end_of_turn(moved=False)
    ok(world.battle is not None, "monsters don't chase you on the path, but one can still walk into you by chance")


def test_you_cant_build_a_house_on_the_path():
    world = new_world()
    world.player.pos = tiles(world, "R")[0]
    world.player.wood = rules.HOUSE_COST
    ok(not world.do("build_house") and world.tile(world.player.pos) == "R", "you can't build a house on the path")


def test_the_first_step_onto_the_path_tells_you_about_it():
    world = new_world()
    step = next(d for d, (dr, dc) in rules.DIRECTIONS.items()
                if world.tile((world.start[0] + dr, world.start[1] + dc)) == "R")
    world.do(step)
    ok(any("path" in words.lower() for words, kind in world.messages[-2:]), "stepping onto the path tells you what it does")


# ===========================================================================
# Chopping trees: T in a forest gives you wood, until the tree falls down
# ===========================================================================

def test_chopping_wood():
    world = new_world()
    forest = tiles(world, "F")[0]
    world.player.pos = forest
    turn = world.turn
    world.rng = FakeDice(ints=[2])
    world.do("chop")
    ok(world.player.wood == 2 and world.turn == turn + 1, "T in the forest chops wood (+2) and takes a turn")
    world.player.pos = tiles(world, "M")[0]
    world.do("chop")
    ok(world.player.wood == 2 and "forest" in world.messages[-1][0], "you can only chop wood in the forest")
    world.player.pos = forest
    world.player.wood = rules.MAX_WOOD
    world.do("chop")
    ok(world.player.wood == rules.MAX_WOOD and "carry" in world.messages[-1][0],
       "you can carry at most %d wood" % rules.MAX_WOOD)


def test_a_tree_falls_when_its_wood_runs_out():
    world = new_world()
    tree = tiles(world, "F")[0]
    world.player.pos = tree
    total = chops = 0
    while world.tile(tree) == "F" and chops < 20:
        world.player.wood = 0
        world.chop_wood()
        total += world.player.wood
        chops += 1
    ok(total == rules.TREE_WOOD and world.tile(tree) == "G",
       "a tree gives exactly %d wood (%d chops), then it falls and leaves a field" % (total, chops))
    ok(tree not in world.tree_wood and any(e["type"] == "timber" for e in world.effects), "...with a TIMBER! effect")
    ok(not world.chop_wood() and "forest" in world.messages[-1][0], "you can't chop wood in a field")
    world.player.food = 0
    world.tile_action()
    ok(world.player.food == 0 and "grass" in world.messages[-1][0], "SPACE in a field says there's nothing to find")


def test_a_half_chopped_tree_keeps_the_rest_of_its_wood():
    world = new_world()
    tree = tiles(world, "F")[0]
    world.player.pos = tree
    world.player.wood = rules.MAX_WOOD - 1
    world.chop_wood()
    ok(world.player.wood == rules.MAX_WOOD and world.wood_left(tree) == rules.TREE_WOOD - 1,
       "with a nearly full pack you only take what fits - the rest stays in the tree")
    world.player.wood = 0
    world.chop_wood()
    ok(world.wood_left(tree) < rules.TREE_WOOD - 1,
       "chop it again later and it keeps counting down (%d left)" % world.wood_left(tree))


def test_dead_trees_in_nightfall_hollow_fall_too():
    world = new_world()
    world.go_to_nightfall()
    world.story.clear()
    world.monsters = []
    dead_tree = tiles(world, "F")[0]
    world.player.pos = dead_tree
    chops = 0
    while world.tile(dead_tree) == "F" and chops < 20:
        world.player.wood = 0
        world.chop_wood()
        chops += 1
    ok(world.tile(dead_tree) == "G" and world.tile_name(dead_tree) == "Dead Grass",
       "a dead tree in Nightfall Hollow falls too, leaving Dead Grass")


def test_monsters_can_start_out_in_the_fields():
    world = new_world()
    everywhere = world.spawn_monsters({"Spider": world.rows * world.cols})    # a monster on every square they can use
    ok(any(world.tile(monster.pos) == "G" for monster in everywhere), "monsters can start out in the fields")


# ===========================================================================
# Houses: build one with wood, and it heals you a little every turn
# ===========================================================================

def test_building_a_house_in_the_forest():
    world = new_world()
    forest = tiles(world, "F")[0]
    world.player.pos = forest
    world.player.wood = rules.HOUSE_COST - 1
    ok(not world.do("build_house") and "wood" in world.build_problem("house"), "not enough wood: no house")
    world.player.wood = rules.HOUSE_COST
    ok(world.do("build_house") and world.tile(forest) == "H" and world.player.wood == 0
       and any(e["type"] == "tile" for e in world.take_effects()),
       "with %d wood: the forest square becomes a house" % rules.HOUSE_COST)
    ok(new_world().tile(forest) == "F", "a new game has the forest back (built houses don't carry over)")


def test_a_house_heals_you_every_turn():
    world = new_world()
    forest = tiles(world, "F")[0]
    world.player.pos = forest
    world.player.wood = rules.HOUSE_COST
    world.do("build_house")
    world.player.health = 10
    for _ in range(3):
        world.do("wait")
    ok(world.player.health == 10 + 3 * rules.HOUSE_HEAL,
       "every turn in a house heals %d (10 -> %d after 3 turns)" % (rules.HOUSE_HEAL, world.player.health))
    world.player.pos = tiles(world, "M")[0]
    world.player.health = 10
    world.do("wait")
    ok(world.player.health == 10, "...but not outside")


def test_houses_go_on_forests_and_fields():
    world = new_world()
    field = tiles(world, "G")[0]
    world.player.pos = field
    world.player.wood = rules.HOUSE_COST
    ok(world.build("house") and world.tile(field) == "H", "you can build a house on a field")
    tree = tiles(world, "F")[0]
    world.player.pos = tree
    world.chop_wood()                       # start chopping this tree...
    world.player.wood = rules.HOUSE_COST
    ok(world.build("house") and tree not in world.tree_wood, "...or on a forest square (the half-chopped tree is gone)")
    world.player.pos = tiles(world, "M")[0]
    world.player.wood = rules.HOUSE_COST
    ok(world.build_problem("house") == "Houses go on a Forest or Field square.", "but not on a Mine")


# ===========================================================================
# Armor soaks up hits until it breaks
# ===========================================================================

def test_armor_soaks_up_hits():
    p = rules.Player("Hero", (0, 0))
    p.put_on_armor()
    ok(p.armor == rules.ARMOR_POINTS and p.max_health == rules.START_HEALTH,
       "armor gives %d armor points (no more +2 max health)" % rules.ARMOR_POINTS)
    p.hurt(rules.ARMOR_POINTS - 2)
    ok(p.armor == 2 and p.health == rules.START_HEALTH,
       "armor soaks up hits first (%d damage: armor %d -> 2, health untouched)"
       % (rules.ARMOR_POINTS - 2, rules.ARMOR_POINTS))
    p.hurt(5)
    ok(p.armor == 0 and not p.has_armor and p.health == rules.START_HEALTH - 3,
       "when it runs out it's gone, and the rest hurts you (-3)")


def test_armor_breaks_and_a_chest_fixes_it():
    world = new_world()
    world.player.put_on_armor()
    world.hurt_player(rules.ARMOR_POINTS)
    ok(not world.player.has_armor and any("armor broke" in text for text, kind in world.messages),
       "the game tells you when your armor breaks")
    world.player.put_on_armor()
    world.player.armor = 1
    world.give_loot("armor", 5)
    ok(world.player.armor == rules.ARMOR_POINTS, "a chest with armor fixes your armor up")


# ===========================================================================
# Boats: build one next to the water, then row across
# ===========================================================================

def test_building_a_boat_and_rowing_out():
    world = new_world()
    shore = next(spot for spot in sorted(world.mainland) if world.neighbors(spot, water=True))
    inland = next(spot for spot in sorted(world.mainland) if not world.neighbors(spot, water=True))
    world.player.pos = inland
    world.player.wood = rules.MAX_WOOD
    ok("next to the water" in world.build_problem("boat"), "you have to stand next to water to build a boat")
    world.player.pos = shore
    water = world.neighbors(shore, water=True)[0]
    way = next(d for d, (dr, dc) in rules.DIRECTIONS.items() if (shore[0] + dr, shore[1] + dc) == water)
    ok(not world.do(way) and world.player.pos == shore, "no boat: you can't go on the water")
    ok(world.do("build_boat") and world.player.has_boat and world.player.wood == rules.MAX_WOOD - rules.BOAT_COST,
       "build a boat for %d wood" % rules.BOAT_COST)
    ok(world.do(way) and world.here == "W", "with a boat you row out onto the water")


def test_rowing_to_the_portal_island_takes_you_through():
    world = new_world()
    for quest in world.quests:
        quest.progress = quest.goal_count
    world.player.has_boat = True
    moves = boat_trip(world, world.start, world.portal)
    for move in moves:
        world.do(move)
    ok(world.world == 2, "with the quests done and a boat, you can row to the Portal island and go through (%d moves)"
       % len(moves))


# ===========================================================================
# Sea Serpents live in the big lakes, and can smash your boat
# ===========================================================================

def a_sea_serpent_fight():
    """A new game where you're out in your boat, fighting a Sea Serpent (and no other monsters)."""
    world = rules.Game("Hero", seed=1)
    world.story.clear()
    serpent = next(m for m in world.monsters if m.special == "drowns")
    world.monsters = [serpent]
    world.player.pos = serpent.pos
    world.player.has_boat = True
    world.start_battle(serpent)
    return world, serpent


def test_sea_serpents_stay_in_the_big_lakes():
    world = rules.Game("Hero", seed=3)
    serpents = [m for m in world.monsters if m.special == "drowns"]
    lakes = world.big_lakes()
    ok(len(serpents) == rules.MONSTER_COUNTS["Sea Serpent"] and all(m.pos in lakes for m in serpents),
       "%d Sea Serpents, all in the big lakes" % len(serpents))
    for _ in range(80):
        world.do("wait")
    ok(all(world.tile(m.pos) == "W" for m in serpents), "after 80 turns they're still in the water")


def test_a_sea_serpent_can_smash_your_boat():
    world, serpent = a_sea_serpent_fight()
    world.player.swords = []
    world.player.health = 20
    world.rng = FakeDice(rolls=[0.99, 0.5])                            # it misses, and the boat is fine
    world.battle_action("attack")
    ok(world.battle.result is None and world.player.has_boat, "most rounds your boat is fine")
    world.rng = FakeDice(rolls=[0.99, rules.SHIPWRECK_CHANCE / 2])     # it misses, then CRASH
    world.battle_action("attack")
    ok(world.battle.result == "drowned" and not world.player.has_boat and world.player.pos in world.mainland
       and world.player.health < 20 and serpent in world.monsters,
       "but sometimes it smashes your boat: hurt, boat lost, washed up on the main shore (%s)" % (world.player.pos,))


def test_beating_a_sea_serpent_counts_for_the_monster_quest():
    world, serpent = a_sea_serpent_fight()
    serpent.health = 1
    world.rng = FakeDice(rolls=[0.1], ints=[3])                         # your sword hits
    world.battle_action("attack")
    ok(world.battle.result == "won" and world.monster_quest.progress == 1,
       "beat it and it counts for the monster quest")


def test_rowing_away_from_a_sea_serpent():
    world, serpent = a_sea_serpent_fight()
    world.rng = FakeDice(rolls=[0.9])                                   # it doesn't get a swipe at you
    world.battle_action("run")
    ok(world.battle.result == "fled" and world.player.pos != serpent.pos, "you can row away from a Sea Serpent")


# ===========================================================================
# In the game window
# ===========================================================================

def test_back_on_the_map_after_a_cave():
    app = new_app(seed=5)
    world = app.game
    cave = walk_into_a_mine(app)
    ok(app.state == "cave", "climb down a Mine and you're in its cave")
    cave.result = "left"
    frames(app, 5)
    ok(app.state == "play" and world.cave is None, "walk back out the way you came: you're on the world map again")
    tree = tiles(world, "F")[0]
    world.player.pos = tree
    world.chop_wood()
    frames(app, 3)
    ok(app.state == "play", "back on the map, the panel still draws (chop wood, %d left)" % world.wood_left(tree))


def camera_problem(app):
    """What's wrong with the camera right now (None if nothing is)."""
    world = app.game
    farthest_x = max(0, world.cols * game.TILE - game.VIEW_W)    # any further right and you'd see past the map
    farthest_y = max(0, world.rows * game.TILE - game.VIEW_H)    # any further down, the same
    x, y = app.cam
    if not (0 <= x <= farthest_x and 0 <= y <= farthest_y):
        return "the camera at (%d, %d) shows past the edge of the map" % (x, y)
    you_x, you_y = app.on_screen(*game.tile_px(world.player.pos))
    if not (0 <= you_x <= game.VIEW_W - game.TILE and 0 <= you_y <= game.VIEW_H - game.TILE):
        return "you're at (%d, %d), not on the screen" % (you_x, you_y)
    return None


def test_the_camera_follows_you_across_the_map():
    app = new_app(seed=3)
    world = app.game
    world.player.max_health = world.player.health = 10 ** 6   # nothing on the way can stop you
    world.player.has_boat = True
    frames(app, 40)
    ok(camera_problem(app) is None, "at home, the camera shows you and nothing past the map (%s)" % camera_problem(app))
    moves = boat_trip(world, world.start, world.portal)
    for step, move in enumerate(moves, 1):
        world.do(move)
        frames(app, 6)
        problem = camera_problem(app)
        ok(problem is None, "step %d of %d on the way to the Portal: %s" % (step, len(moves), problem))
    ok(world.player.pos == world.portal, "you made it all the way to the Portal, and the camera kept up")
