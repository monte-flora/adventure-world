"""
The Sunfang quest in Nightfall Hollow.

The black river splits the land in two, with one broken bridge. On the west side: the start, the first
Mine, the first dark shrine and a chest with old planks. Over the bridge: the other two Mines, the other
two dark shrines (each guarded by a Shadow Guardian) and the castle.

Sunfang = the Blade (3 diamonds found here) + the Hilt (6 dead wood, Craft menu) + the Sun Gem (3 Sun Shards).
The forge at the castle gate wakes only after all 3 beacons are lit.

These tests check the rules (and walk the whole quest like a player), not exactly where things are drawn,
so you can redraw the map and they still work (as long as the river still splits it in two).
"""

import random

import pytest

import caves
import rules
from helpers import new_world, ok, tiles
from test_nightfall_and_castle import in_nightfall_hollow, light_the_beacons

P = rules.DIRECTIONS


def hollow(diamonds=0):
    """Just through the Portal, no wandering monsters (the Guardians stay on their shrines)."""
    world = new_world()
    world.player.diamonds = diamonds
    for quest in world.quests:
        quest.progress = quest.goal_count
    world.go_to_nightfall()
    world.story.clear()
    world.monsters = [m for m in world.monsters if m.special in ("guardian", "warden")]
    world.player.max_health = world.player.health = 500      # nothing in these tests should end the game
    return world


def dry_reach(world, start=None, blocked=""):
    """Every square you can walk to WITHOUT fixing the broken bridge (land only)."""
    start = start or world.start
    found, todo = {start}, [start]
    while todo:
        for spot in world.neighbors(todo.pop(), bridges=False):
            if spot not in found and world.tile(spot) not in blocked:
                found.add(spot)
                todo.append(spot)
    return found


def path(world, goal):
    """The steps (up, down, left, right) from where you stand to the goal. Dark shrines are never walked
    over on the way (a Guardian sits on each), and the broken bridge counts as walkable (you'll fix it)."""
    start = world.player.pos
    came, todo = {start: None}, [start]
    while todo:
        here = todo.pop(0)
        if here == goal:
            break
        for name, (dr, dc) in P.items():
            spot = (here[0] + dr, here[1] + dc)
            if spot in came or not world.in_bounds(spot):
                continue
            if world.tile(spot) in rules.WALKABLE + "=" and (world.tile(spot) != "D" or spot == goal):
                came[spot] = (here, name)
                todo.append(spot)
    ok(goal in came, "there's a way from %s to %s" % (start, goal))
    steps = []
    while came[goal]:
        goal, name = came[goal][0], came[goal][1]
        steps.append(name)
    return steps[::-1]


def walk(world, goal):
    for name in path(world, goal):
        before = world.player.pos
        world.do(name)
        ok(world.player.pos != before, "the step %s from %s worked: %s" % (name, before, world.messages[-1][0]))
        while world.battle:
            fight(world)


def fight(world):
    """Swing at whatever is in your way, until the fight is over."""
    for _ in range(200):
        if not world.battle or world.battle.over:
            break
        world.battle_action("attack")
    world.close_battle()


def dig_everything(world):
    cave = world.cave
    ore = [(r, c) for r, row in enumerate(cave.map) for c, tile in enumerate(row) if tile in "*s"]
    for r, c in ore:
        cave.dig(r, c)
    return ore


def leave(world):
    world.cave.result = "exit"
    world.leave_cave()


# ===========================================================================
# The map
# ===========================================================================

def test_the_map_has_three_mines_three_dark_shrines_and_a_chest():
    world = hollow()
    ok(len(tiles(world, "M")) == 3, "3 Mines")
    ok(len(tiles(world, "D")) == 3 == rules.BEACONS_NEEDED, "3 dark shrines (one beacon each)")
    ok(len(tiles(world, "T")) == 2 and len(tiles(world, "=")) >= 1, "the planks chest and a hidden chest, and a broken bridge")
    ok(tiles(world, "H") and world.tile_name(tiles(world, "H")[0]) == "Shrine",
       "and glowing shrines to rest at")
    ok(world.tile_name(tiles(world, "D")[0]) == "Dark Shrine", "the dark shrines are called that")


def test_the_castle_is_behind_the_river_so_the_bridge_is_the_only_way():
    world = hollow()
    dry = dry_reach(world)
    ok(world.castle not in dry, "without fixing the bridge you can't walk to the castle (no more straight line!)")
    mines = sorted(tiles(world, "M"), key=lambda mine: rules.distance(mine, world.start))
    shrines = sorted(tiles(world, "D"), key=lambda spot: rules.distance(spot, world.start))
    ok(mines[0] in dry and shrines[0] in dry and world.plank_chest in dry,
       "the first Mine, the first dark shrine and the chest are on your side of the river")
    ok(all(spot not in dry for spot in mines[1:] + shrines[1:]),
       "the other Mines and dark shrines are over the bridge")
    everything = world.reach(world.start)
    ok(world.castle in everything and all(spot in everything for spot in mines + shrines),
       "...and with the bridge fixed, every Mine, dark shrine and the castle can be reached")


def test_you_cant_row_across_the_black_water():
    world = hollow()
    world.player.wood = 12
    problem = world.build_problem("boat")
    ok(problem and "stormy" in problem, "no boat in Nightfall Hollow: %s" % problem)


# ===========================================================================
# The chest, the planks and the bridge
# ===========================================================================

def test_the_chest_has_the_planks_that_fix_the_bridge():
    world = hollow()
    bridge = min(tiles(world, "="))
    beside = (bridge[0], bridge[1] - 1)
    world.player.pos = beside
    ok(not world.do("right") and world.tile(bridge) == "=" and world.player.pos == beside,
       "without planks the broken bridge stops you")
    ok("planks" in world.messages[-1][0], "...and says what you need: %s" % world.messages[-1][0])
    walk(world, world.plank_chest)
    world.do("act")
    ok(world.player.has_planks and world.plank_chest not in tiles(world, "T"), "the chest holds old planks (and is empty now)")
    walk(world, beside)
    world.do("right")
    ok(world.tile(bridge) == "#" and world.player.pos == bridge, "with the planks, you fix the bridge and walk on")


# ===========================================================================
# The Shadow Guardians and their beacons
# ===========================================================================

def test_a_shadow_guardian_sits_on_each_dark_shrine_and_never_leaves():
    world = hollow()
    guardians = [m for m in world.monsters if m.special == "guardian"]
    ok(sorted(m.pos for m in guardians) == sorted(tiles(world, "D")), "a Guardian on every dark shrine")
    guardian = guardians[0]
    ok(guardian.kind == "Shadow Guardian" and guardian.max_health == 24 and guardian.damage == (3, 5),
       "a Shadow Guardian has 24 health and hits for 3-5 (it has %d health, hits for %s)"
       % (guardian.max_health, guardian.damage))
    where = [m.pos for m in guardians]
    for _ in range(150):
        world.do("wait")
    ok([m.pos for m in guardians] == where, "they stay on their shrines")


def test_beat_the_guardian_then_light_the_beacon():
    world = hollow()
    shrine = min(tiles(world, "D"), key=lambda spot: rules.distance(spot, world.start))
    steps = path(world, shrine)
    for name in steps[:-1]:
        world.do(name)
    world.do(steps[-1])                         # the last step: onto the dark shrine
    ok(world.here == "D" and world.beacons == set() and world.player.pos == shrine,
       "you stand on the dark shrine, and the beacon isn't lit yet")
    ok(world.battle is not None and world.battle.monster.pos == shrine, "its Guardian attacks!")
    fight_target = world.battle.monster
    ok(world.here not in rules.SAFE, "a dark shrine doesn't keep monsters away")
    world.rng = random.Random(3)
    fight(world)
    ok(not fight_target.is_alive, "you beat the Shadow Guardian")
    world.player.health = 5
    world.do("wait")
    ok(world.player.health == 5, "the shrine is still dark: no healing before it's lit")
    ok(world.do("act") and shrine in world.beacons and world.tile(shrine) == "H"
       and world.tile_name(shrine) == "Lit Beacon", "SPACE lights the beacon (the shrine glows now)")
    world.do("wait")
    ok(world.player.health > 5 and world.here in rules.SAFE, "and a lit shrine heals you, and is safe")


def test_each_beacon_makes_the_land_a_little_brighter():
    import game
    app_nights = game.BEACON_BRIGHTER
    ok(app_nights > 0, "every beacon takes %d away from the darkness" % app_nights)
    a = game.App("Hero", seed=1, sound=False)
    ok(len(a.nights) == rules.BEACONS_NEEDED + 1, "a darkness picture for 0, 1, 2 and 3 lit beacons")
    centre = lambda night, radius: night.get_at((game.VIEW_W + radius, game.VIEW_H))[3]
    ok(all(centre(a.nights[i], 340) >= centre(a.nights[i + 1], 340) for i in range(3))
       and centre(a.nights[0], 340) > centre(a.nights[3], 340),
       "each darkness is lighter than the last")
    ok(centre(a.nights[3], 560) < centre(a.nights[0], 560), "even the edge of the screen gets lighter")


# ===========================================================================
# The Portal, the shadow caves and the Sun Shards
# ===========================================================================

def test_the_portal_swallows_the_diamonds_you_bring():
    world = hollow(diamonds=3)
    ok(world.player.diamonds == 0, "you arrive with no diamonds (the Portal swallowed them)")
    ok(any("swallowed" in text for text, _ in world.messages), "and the game says so")


def test_every_shadow_mine_has_a_diamond_and_a_harder_to_reach_sun_shard():
    world = hollow()
    ok(world.diamond_mines == set(tiles(world, "M")) == world.shard_mines, "every Mine has both")
    mines = sorted(tiles(world, "M"), key=lambda mine: rules.distance(mine, world.start))
    for mine in mines:
        text = world.cave_plan[mine]
        ok("*" in text and caves.SHARD in text and caves.level_theme(text) == "shadow",
           "the cave under %s is a shadow cave with a diamond and a Sun Shard" % (mine,))
    ok([world.cave_plan[m] for m in mines] == caves.SHADOW_CAVES, "the nearest Mine has the easiest cave")
    ok(len(set(caves.SHADOW_CAVES)) == 3, "three different caves")


def test_digging_out_the_ore_gives_the_diamond_and_the_sun_shard():
    world = hollow()
    mine = min(tiles(world, "M"), key=lambda spot: rules.distance(spot, world.start))
    world.player.pos = mine
    world.do("act")
    cave = world.cave
    ok(cave is not None, "you climb down into the shadow cave")
    diamond = [(r, c) for r, row in enumerate(cave.map) for c, tile in enumerate(row) if tile == "*"][0]
    shard = [(r, c) for r, row in enumerate(cave.map) for c, tile in enumerate(row) if tile == caves.SHARD][0]
    cave.dig(*diamond)
    ok(world.player.diamonds == 1 and world.player.sun_shards == 0 and mine not in world.cleared_mines,
       "the diamond is yours, but the Mine isn't empty: a Sun Shard is still down there")
    leave(world)
    world.do("act")
    ok(world.cave is not None, "so you can climb back down")
    cave = world.cave
    cave.dig(*shard)
    ok(world.player.sun_shards == 1 and world.player.diamonds == 1 and mine in world.cleared_mines,
       "the Sun Shard is yours, and now the Mine is empty")
    leave(world)
    ok(world.do("act") is False and world.cave is None, "you can't go back down an empty Mine")


# ===========================================================================
# The parts of Sunfang
# ===========================================================================

def test_the_hilt_is_carved_from_dead_wood_in_the_craft_menu():
    world = hollow()
    p = world.player
    p.wood = rules.HILT_WOOD - 1
    ok("%d" % rules.HILT_WOOD in world.build_problem("hilt"), "not enough wood: %s" % world.build_problem("hilt"))
    p.wood = rules.HILT_WOOD
    ok(world.do("build_hilt") and p.has_hilt and p.wood == 0, "%d dead wood make the Hilt" % rules.HILT_WOOD)
    ok(world.build_problem("hilt") and "already" in world.build_problem("hilt"), "you only need one")
    home = new_world()
    ok("Nightfall" in home.build_problem("hilt"), "you can't carve it at home")


def test_the_craft_menu_shows_the_hilt_only_in_nightfall_hollow():
    from helpers import new_app
    app = new_app(seed=2)
    ok("hilt" not in app.crafts, "no Hilt row at home")
    in_nightfall_hollow(app.game)
    ok(app.crafts[-1] == "hilt" and len(app.crafts) == len(app.CRAFTS) + 1, "a Hilt row in Nightfall Hollow")


def test_the_forge_sleeps_until_all_three_beacons_are_lit_then_wants_all_the_parts():
    world = hollow()
    p = world.player
    p.pos = world.castle
    p.diamonds, p.has_hilt, p.sun_shards = 3, True, 3
    world.reach_castle()
    ok(not world.forging and "asleep" in world.messages[-1][0], "everything in your pack, but the forge is asleep")
    shrines = sorted(tiles(world, "D"))
    for shrine in shrines[:2]:
        world.beacons.add(shrine)
    world.reach_castle()
    ok(not world.forging and "asleep" in world.messages[-1][0], "two beacons: still asleep")
    light_the_beacons(world)
    p.diamonds = 2
    world.reach_castle()
    ok(not world.forging and "Blade" in world.messages[-1][0], "awake, but the Blade needs a 3rd diamond")
    p.diamonds, p.has_hilt = 3, False
    world.reach_castle()
    ok(not world.forging and "Hilt" in world.messages[-1][0], "awake, but there's no Hilt")
    p.has_hilt, p.sun_shards = True, 2
    world.reach_castle()
    ok(not world.forging and "Sun Gem" in world.messages[-1][0], "awake, but the Sun Gem needs a 3rd Sun Shard")
    p.sun_shards = 3
    world.reach_castle()
    ok(world.forging, "with the Blade, the Hilt, the Sun Gem and 3 beacons: the forge starts")
    world.story.clear()
    world.finish_sunfang(perfect=False)
    ok(p.sunfang and p.diamonds == 0 and not p.has_hilt and p.sun_shards == 0,
       "Sunfang is forged from the parts")


def test_the_forge_has_three_steps_and_a_failed_step_comes_again():
    import game
    forge = game.SunfangForge(random.Random(1))
    ok([name for name, _ in forge.STEPS] == ["HEAT", "HAMMER", "COOL"] and forge.BEATS == 3, "heat, hammer, cool")
    for _ in range(int(forge.RISE_TIME * 60) + 2):
        forge.update(1 / 60)
    ok(forge.step[0] == "HEAT", "the first step is heat")
    wrong = next(key for key, _ in forge.KEYS if key != forge.key[0])
    forge.press(wrong)
    ok(forge.beats_done == 0 and forge.step[0] == "HEAT", "a miss: the same step again")
    for _ in range(int(forge.PAUSE_TIME * 60) + 2):
        forge.update(1 / 60)
    forge.press(forge.key[0])
    ok(forge.beats_done == 1 and forge.step[0] == "HAMMER", "then the hammer")


# ===========================================================================
# The whole quest, played like a robot player would
# ===========================================================================

def test_the_whole_quest_can_be_played_from_the_portal_to_the_castle():
    world = hollow(diamonds=3)
    p = world.player
    start, castle = world.start, world.castle
    mines = sorted(tiles(world, "M"), key=lambda mine: rules.distance(mine, start))
    shrines = sorted(tiles(world, "D"), key=lambda spot: rules.distance(spot, start))

    # 1. the west: the chest (planks), some dead wood for the Hilt, the first Mine and the first dark shrine
    walk(world, world.plank_chest)
    world.do("act")
    ok(p.has_planks, "the planks from the chest")
    forest = min((spot for spot in tiles(world, "F") if spot in dry_reach(world)),
                 key=lambda spot: rules.distance(spot, p.pos))
    while p.wood < rules.HILT_WOOD:
        walk(world, forest)
        world.do("chop")
        forest = min((spot for spot in tiles(world, "F") if spot in dry_reach(world) and spot != forest),
                     key=lambda spot: rules.distance(spot, p.pos))
    ok(world.do("build_hilt") and p.has_hilt, "the Hilt")

    def do_mine(mine):
        walk(world, mine)
        world.do("act")
        ok(world.cave is not None, "down into the Mine at %s" % (mine,))
        dig_everything(world)
        leave(world)

    def do_shrine(shrine):
        beaten = world.player.monsters_defeated
        walk(world, shrine)                     # (walk fights the Guardian that attacks you on the shrine)
        ok(world.player.monsters_defeated == beaten + 1 and world.player.is_alive, "you beat the Guardian")
        ok(world.do("act") and shrine in world.beacons, "the beacon is lit")

    do_mine(mines[0])
    do_shrine(shrines[0])
    ok(castle not in dry_reach(world), "the castle is still across the river")

    # 2. over the bridge: the other two Mines and dark shrines
    for mine, shrine in zip(mines[1:], shrines[1:]):
        do_mine(mine)
        do_shrine(shrine)
    ok(any(world.tile(spot) == "#" for spot in [(r, c) for r in range(world.rows) for c in range(world.cols)]),
       "the bridge got fixed on the way")
    ok(p.diamonds == 3 and p.sun_shards == 3 and p.has_hilt and len(world.beacons) == 3,
       "the Blade, the Sun Gem, the Hilt and 3 beacons")

    # 3. the castle: the forge wakes, and Sunfang is forged
    walk(world, castle)
    ok(world.forging, "at the castle gate the forge starts")
    world.story.clear()
    world.finish_sunfang(perfect=True)
    ok(p.sunfang and world.cave is not None and world.cave.is_castle, "Sunfang is forged and you go into the castle")
    ok(world.player.is_alive, "and you're still alive")


# ===========================================================================
# The lantern: it starts small and every lit beacon makes it bigger
# ===========================================================================

def how_many_squares_you_see(world):
    return sum(world.is_visible((r, c)) for r in range(world.rows) for c in range(world.cols))


def test_the_lantern_grows_with_every_beacon():
    world = hollow()
    world.player.pos = (9, 6)
    radii, seen = [], []
    for shrine in sorted(tiles(world, "D")):
        radii.append(world.sight_radius)
        seen.append(how_many_squares_you_see(world))
        world.beacons.add(shrine)
    radii.append(world.sight_radius)
    seen.append(how_many_squares_you_see(world))
    ok(radii == rules.LANTERN_RADIUS and radii[0] <= 2, "the lantern starts tiny and grows: %s" % radii)
    ok(seen == sorted(set(seen)), "you see more squares with every beacon: %s" % seen)
    ok(new_world().sight_radius == rules.SIGHT_RADIUS, "at home nothing changed")


def test_lighting_a_beacon_lets_you_see_farther_right_away():
    world = hollow()
    shrine = sorted(tiles(world, "D"))[0]
    world.monsters = []
    world.player.pos = shrine
    before = len(world.seen)
    ok(world.light_beacon(), "the beacon lights")
    ok(len(world.seen) > before and world.sight_radius == rules.LANTERN_RADIUS[1], "and the lantern is bigger")


def test_shadow_monsters_are_weaker_and_slower_in_the_light_of_a_beacon():
    world = hollow()
    shrine = sorted(tiles(world, "D"))[0]
    world.monsters = []
    near = (shrine[0], shrine[1] + 1)
    far = (17, 27 - 3)
    ok(not world.in_light(near), "no beacon lit: no light")
    world.beacons.add(shrine)
    ok(world.in_light(near) and not world.in_light(far), "near a lit beacon there's light, far away there isn't")
    hits = {}
    for where in (near, far):
        monster = rules.Monster("Zombie", where, shadow=True)
        world.player.pos = where
        world.player.armor = 0
        total = 0
        for seed in range(60):
            world.rng = random.Random(seed)
            world.player.health = 500
            world.start_battle(monster)
            monster.health = 99
            before = world.player.health
            world.battle_action("attack")
            total += before - world.player.health
            world.battle = None
        hits[where] = total
    ok(hits[near] < hits[far], "the light weakens them: %d damage in the light vs %d outside" % (hits[near], hits[far]))
    slow = rules.Monster("Zombie", near, shadow=True)
    normal = rules.Monster("Zombie", far, shadow=True)
    world.monsters = [slow, normal]
    world.player.pos = (9, 6)
    moved = {id(slow): 0, id(normal): 0}
    for seed in range(300):
        world.rng = random.Random(seed)
        slow.pos, normal.pos = near, far
        world.move_monsters()
        moved[id(slow)] += slow.pos != near
        moved[id(normal)] += normal.pos != far
    ok(moved[id(slow)] < moved[id(normal)], "and slower: it moved %d times in the light, %d outside"
       % (moved[id(slow)], moved[id(normal)]))


# ===========================================================================
# Landmarks with secrets: the Dead Giant Tree, the Black Lighthouse, signs and a hidden chest
# ===========================================================================

def test_there_are_two_landmarks_two_signs_and_a_hidden_chest():
    world = hollow()
    ok(sorted(world.night_landmarks.values()) == ["Black Lighthouse", "Dead Giant Tree"], "two landmarks")
    west, east = sorted(world.night_landmarks, key=lambda spot: spot[1])
    ok(world.tile_name(west) == "Dead Giant Tree" and world.tile_name(east) == "Black Lighthouse"
       and west in dry_reach(world) and east not in dry_reach(world),
       "the tree is on the west side, the lighthouse over the bridge")
    ok(len(tiles(world, "+")) == 2, "two signposts")
    hidden = [spot for spot in tiles(world, "T") if spot != world.plank_chest][0]
    ok(hidden in world.reach(world.start) and sum(world.tile((hidden[0] + dr, hidden[1] + dc)) == "X"
                                                   for dr, dc in P.values()) >= 2,
       "the hidden chest is tucked between rocks, and you can still get to it")


def test_climbing_a_landmark_lifts_the_fog_and_makes_the_mines_sparkle():
    world = hollow()
    tree = [spot for spot, name in world.night_landmarks.items() if name == "Dead Giant Tree"][0]
    world.player.pos = tree
    world.seen = set()
    ok(world.do("act") and len(world.seen) > 40, "climbing the tree lifts the fog around it")
    nearby = [m for m in tiles(world, "M") if world.close_to(m, tree, rules.LOOKOUT_SIGHT)]
    ok(nearby and all(m in world.glints for m in nearby), "the Mines you can see from up there sparkle")
    ok(world.here in rules.SAFE, "monsters can't reach you on a landmark")
    lighthouse = [spot for spot, name in world.night_landmarks.items() if name == "Black Lighthouse"][0]
    world.player.pos = lighthouse
    world.do("act")
    ok(all(m in world.glints for m in tiles(world, "M")), "the Black Lighthouse makes EVERY Mine sparkle")


def test_the_signs_point_to_the_landmarks_and_the_hidden_chest():
    world = hollow()
    world.player.pos = tiles(world, "+")[0]
    world.do("act")
    words = world.messages[-1][0]
    ok("Dead Giant Tree" in words and "Black Lighthouse" in words and "chest" in words, "the sign says: %s" % words)


def test_the_hidden_chest_has_a_diamond_ring():
    world = hollow()
    hidden = [spot for spot in tiles(world, "T") if spot != world.plank_chest][0]
    world.player.has_planks = True          # (it's over the bridge)
    walk(world, hidden)
    world.do("act")
    ok(world.player.ring_hits > 0 and hidden not in tiles(world, "T"),
       "a diamond ring for your sword")


# ===========================================================================
# The Shadow Warden at the bridge
# ===========================================================================

def test_the_shadow_warden_stands_in_front_of_the_bridge_and_must_be_beaten():
    world = hollow()
    wardens = [m for m in world.monsters if m.special == "warden"]
    ok(len(wardens) == 1, "one Shadow Warden")
    warden = wardens[0]
    bridge = min(tiles(world, "="), key=lambda spot: spot[1])
    ok(warden.pos == (bridge[0], bridge[1] - 1) and warden.kind == "Shadow Warden", "it stands right in front of the bridge")
    ok(warden.max_health == 36 and warden.damage == (4, 6) and warden.max_health > 24,
       "it's tougher than a Guardian: %d health, hits %s" % (warden.max_health, warden.damage))
    for _ in range(100):
        world.do("wait")
    ok(warden.pos == (bridge[0], bridge[1] - 1), "it never leaves its post")
    # You can't get to the bridge without bumping into it
    world.player.has_planks = True
    world.rng = random.Random(4)
    beaten = world.player.monsters_defeated
    walk(world, world.castle)                       # (walk() fights whatever attacks you on the way)
    ok(world.player.monsters_defeated > beaten and not warden.is_alive, "you had to beat the Warden to get to the bridge")
    ok(any("Warden crumbles" in text for text, _ in world.messages), "and the game says it's gone")


# ===========================================================================
# Wren the ghost and her lost lanterns
# ===========================================================================

def wren_spot(world):
    return tiles(world, "N")[0]


def test_wren_the_ghost_asks_for_three_lost_lanterns():
    world = hollow()
    ok(len(tiles(world, "N")) == 1 and world.tile_name(wren_spot(world)) == "Wren the Ghost", "Wren waits near the start")
    ok(len(tiles(world, "Q")) == rules.WREN_LANTERNS, "%d lost lanterns lie around" % rules.WREN_LANTERNS)
    far = [spot for spot in tiles(world, "Q") if spot not in dry_reach(world)]
    ok(far, "at least one is over the river, in a far corner")
    world.player.pos = wren_spot(world)
    world.do("act")
    quest = world.wren_quest
    ok(quest and quest.goal_count == rules.WREN_LANTERNS and quest in world.quests
       and quest.description == "Find Wren's lanterns", "she gives you a quest, and it shows in your quest list")
    world.do("act")
    ok(len(world.quests) == 2 and "lanterns are still out there" in world.messages[-1][0], "asking again doesn't add another")


def test_picking_up_lanterns_and_giving_them_to_wren_gets_armor_and_a_map_hint():
    world = hollow()
    p = world.player
    p.has_planks = True
    world.player.pos = wren_spot(world)
    world.do("act")
    for lantern in sorted(tiles(world, "Q")):
        walk(world, lantern)
        ok(world.tile(lantern) == "G", "the lantern at %s is picked up" % (lantern,))
    ok(p.lanterns == 3 and world.wren_quest.completed, "all 3 lanterns, the quest is done")
    walk(world, wren_spot(world))
    p.armor = 0
    world.seen = set()
    world.do("act")
    ok(world.wren_thanked and p.has_armor and p.lanterns == 0, "Wren thanks you with armor")
    ok(all(any(abs(s[0] - m[0]) <= 1 and abs(s[1] - m[1]) <= 1 for s in world.seen) for m in tiles(world, "M") + tiles(world, "D")),
       "and shows you where every Mine and dark shrine is")
    p.armor = 0
    ok(world.do("act") is False and not p.has_armor, "she only rewards you once")


def test_lanterns_found_before_meeting_wren_still_count():
    world = hollow()
    lantern = min(tiles(world, "Q"), key=lambda spot: rules.distance(spot, world.start))
    walk(world, lantern)
    walk(world, wren_spot(world))
    world.do("act")
    ok(world.wren_quest.progress == 1, "the lantern you already found counts")


# ---- night events: moonrise and the wisp (idea F) ----------------------------------------------

def moonrise(world):
    """Skip ahead to the turn the moon rises."""
    world.turn = rules.MOONRISE_EVERY - 1
    world.end_of_turn(False)


def test_the_moon_rises_every_40_turns_and_sets_again():
    world = hollow()
    ok(world.moon == 0 and world.wisp is None, "the moon starts down")
    moonrise(world)
    ok(world.moon == rules.MOONRISE_TURNS and world.wisp is not None, "the moon rises and a wisp appears")
    for _ in range(rules.MOONRISE_TURNS):
        world.end_of_turn(False)
    ok(world.moon == 0 and world.wisp is None, "the moon sets and the wisp fades")
    ok("calm again" in world.messages[-1][0], "it says the land is calm again")


def test_no_moonrise_at_home():
    world = new_world()
    world.turn = rules.MOONRISE_EVERY - 1
    world.end_of_turn(False)
    ok(world.moon == 0 and world.wisp is None, "the moon only rises in Nightfall Hollow")


def test_the_wisp_is_near_and_on_grass_you_can_walk_to():
    for seed in range(15):
        world = hollow()
        world.rng = random.Random(seed)
        moonrise(world)
        spot, here = world.wisp, world.player.pos
        ok(world.tile(spot) == "G", "the wisp sits on grass")
        ok(3 <= abs(spot[0] - here[0]) + abs(spot[1] - here[1]) <= 4, "3 or 4 squares away")
        ok(spot in dry_reach(world), "you can walk to it")


def test_following_the_wisp_three_times_leaves_a_gift():
    world = hollow()
    moonrise(world)
    p = world.player
    world.moon = 99
    p.xp = 0
    p.armor = 0
    p.food = 0
    got = []
    for hop in range(rules.WISP_HOPS):
        ok(world.wisp is not None, "the wisp is waiting (hop %d)" % hop)
        got.append(world.wisp)
        walk(world, world.wisp)
    ok(world.wisp is None, "the wisp is gone after the last hop")
    ok(len(set(got)) == rules.WISP_HOPS, "it hopped to new spots")
    ok(p.xp > 0 or p.has_armor or p.food > 0, "it left a gift")
    ok(world.moon > 0, "(the moon is still up)")


def test_monsters_notice_you_from_farther_under_the_moon_but_not_in_beacon_light():
    world = hollow()
    ok(world.chase_distance() == rules.CHASE_DISTANCE, "normal chase distance with the moon down")
    moonrise(world)
    ok(world.chase_distance() == rules.CHASE_DISTANCE + rules.MOON_CHASE, "farther under the moon")
    world.beacons.add(world.player.pos)
    ok(world.chase_distance() == rules.CHASE_DISTANCE, "but beacon light keeps you safe")


def test_a_shadow_monster_comes_closer_under_the_moon():
    world = hollow()
    p = world.player
    spot = next(s for s in sorted(dry_reach(world)) if abs(s[0] - p.pos[0]) + abs(s[1] - p.pos[1]) == 4 and world.tile(s) == "G"
                and world.tile(s) not in rules.SAFE)
    m = rules.Monster("Zombie", spot, shadow=True)
    m.move_chance = 1
    world.monsters = [m]
    world.moon = 5
    before = rules.distance(m.pos, p.pos)
    world.move_monsters()
    ok(rules.distance(m.pos, p.pos) < before, "it heads for you")
