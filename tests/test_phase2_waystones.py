"""
PHASE 2 STAGE 2a, THE WORLD: the big map's lands open up in an order, every Mine can be reached,
villages, waystones (fast travel), lookouts that spot hidden chests, and gates.
"""

import pygame
import pytest

import caves
import game
import rules
from helpers import click, frames, ok, press
from phase2 import Phase2Game, draw_world, save, waystones, world_map
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)

NEW_LANDS = ("Home Meadow", "Whispering Woods", "Old Ruins", "The Great Lake", "Portal Island", "Frost Peaks",
             "Sunscorch Desert", "Murk Swamp")


@pytest.fixture(scope="module")
def atlas():
    return world_map.load()


@pytest.fixture
def world():
    world = Phase2Game("Hero", seed=1)
    world.monsters = []
    world.story.clear()
    return world


def reach(world, boat=False, gates=False, bridges=True):
    """Every square you can get to from home: on foot, over the old bridges (if you fix them),
    through the gates (if you're strong enough) and over water (if you have a boat)."""
    allowed = rules.WALKABLE + ("=" if bridges else "") + ("W" if boat else "")
    found, todo = {world.start}, [world.start]
    while todo:
        r, c = todo.pop()
        for dr, dc in rules.DIRECTIONS.values():
            spot = (r + dr, c + dc)
            if spot in found or not world.in_bounds(spot):
                continue
            if world.tile(spot) in allowed or (gates and spot in world.atlas.gates):
                found.add(spot)
                todo.append(spot)
    return found


def lands_in(world, spots):
    return {world.land_name(spot) for spot in spots} - {None}


# ===========================================================================
# The lands, and the order they open up in
# ===========================================================================

def test_the_world_has_its_lands(atlas):
    names = [land[0] for land in atlas.lands]
    for name in NEW_LANDS:
        ok(name in names, "the world has %s" % name)
    ok(len(set(names)) >= 6, "6 or more lands")


def test_every_land_can_be_reached_from_home(world):
    everything = reach(world, boat=True, gates=True)
    ok(lands_in(world, everything) == set(NEW_LANDS), "with a boat, fixed bridges and the gates open, every land")


def test_the_lands_open_up_in_an_order(world):
    first = lands_in(world, reach(world, bridges=False))
    ok({"Home Meadow", "Whispering Woods", "Old Ruins", "The Great Lake"} <= first,
       "from the start you can walk to the woods, the ruins and the lake shores")
    ok(not first & {"Frost Peaks", "Murk Swamp", "Sunscorch Desert", "Portal Island"},
       "but not across the rivers, through the gate or out to the island")
    bridges = lands_in(world, reach(world))
    ok({"Frost Peaks", "Murk Swamp"} <= bridges, "fix the old bridges, and Frost Peaks and Murk Swamp open up")
    ok("Sunscorch Desert" not in lands_in(world, reach(world, boat=True)), "the desert is behind the gate, even by boat")
    ok("Sunscorch Desert" in lands_in(world, reach(world, gates=True)), "the Desert Gate opens the desert")
    ok("Portal Island" in lands_in(world, reach(world, boat=True)) and world.portal in reach(world, boat=True),
       "row out to Portal Island and its Portal")


def test_every_mine_can_be_reached_and_has_a_cave(world):
    everything = reach(world, boat=True, gates=True)
    mines = rules.tiles_of(world.map, "M")
    ok(len(mines) >= 12 and set(mines) == set(world.cave_plan), "%d Mines, each with a cave" % len(mines))
    ok(all(mine in everything for mine in mines), "you can get to every Mine")
    files = set(caves.CAVE_LEVELS) | {caves.without_diamond(text) for text in caves.CAVE_LEVELS}
    ok(all(text in files for text in world.cave_plan.values()), "every Mine plays a cave file: the game never makes one up")
    numbers = caves.plan_cave_files(mines, world.start)          # {mine: which file}, nearest home first
    ok(set(numbers.values()) == set(range(len(caves.CAVE_LEVELS))) and len(caves.CAVE_LEVELS) == 17,
       "the 17 hand-drawn caves are all under Mines")
    nearest_first = sorted(mines, key=lambda mine: (abs(mine[0] - world.start[0]) + abs(mine[1] - world.start[1]), mine))
    ok([numbers[mine] for mine in nearest_first] == [i % 17 for i in range(len(mines))],
       "Mine i plays file i, nearest Mine first (the files go round again if there are more Mines than files)")
    ok(len(mines) == 17 and len(set(numbers.values())) == len(mines),
       "every one of the %d Phase 2 Mines plays a different cave file" % len(mines))
    looks = {"Frost Peaks": "crystal", "Sunscorch Desert": "lava"}
    for mine in nearest_first[12:]:                              # the 5 farthest Mines play the 5 newest caves
        land, look = world.land_name(mine), caves.level_theme(caves.CAVE_LEVELS[numbers[mine]])
        ok(looks.get(land) == look, "cave %d is under a Mine in %s and looks like it (%s)" % (numbers[mine] + 1, land, look))
    ok(all(text in caves.SECRET_CAVES for text in world.secret_mines.values()), "a Secret Mine plays a file from levels/secret")
    ok(len(world.diamond_mines & world.mainland) >= rules.DIAMONDS_NEEDED, "enough diamonds you can walk to")
    for spot in world.landmarks + list(world.atlas.lookouts) + [world.start]:
        ok(spot in everything, "%s at %s can be reached" % (world.tile_name(spot), spot))


def test_home_is_where_the_home_line_says(world, atlas):
    ok(world.start == atlas.home == world.player.pos, "you start at home")
    ok(world.tile(world.start) == "H" and world.land_name(world.start) == "Home Meadow", "home is a house in Home Meadow")
    ok(world.start not in world.lodges, "home isn't a rest house")


# ===========================================================================
# Villages
# ===========================================================================

def test_villages_are_read_from_the_land_files(world, atlas):
    ok(len(atlas.villages) >= 4, "at least 4 villages: %s" % [v[0] for v in atlas.villages])
    ok(len({land for _, _, land in atlas.villages}) >= 4, "in at least 4 lands")
    everything = reach(world, boat=True, gates=True)
    for name, (r, c), land in atlas.villages:
        ok(world.land_name((r, c)) == land, "%s is in %s" % (name, land))
        square = [(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
        ok(all(world.tile(s) in rules.WALKABLE and world.tile(s) != "H" for s in square),
           "%s has an open square to walk on" % name)
        ok((r, c) in everything, "you can get to %s" % name)
        houses = [(rr, cc) for rr in range(r - 3, r + 4) for cc in range(c - 3, c + 4) if world.tile((rr, cc)) == "H"]
        ok(len(houses) >= 3, "%s has a few houses around its square" % name)
        ok(world.village_at((r, c)) == name, "the game knows you're in %s" % name)


def test_village_and_place_lines_drawn_wrong_say_what_is_wrong():
    stitch = world_map.stitch
    with pytest.raises(world_map.WorldMapError, match="can't read"):
        stitch([("a.txt", "name: A\nat: 0 0\nvillage: Town\nGG\n")])
    with pytest.raises(world_map.WorldMapError, match="outside"):
        stitch([("a.txt", "name: A\nat: 0 0\nvillage: Town 5 5\nGG\n")])
    with pytest.raises(world_map.WorldMapError, match="home"):
        stitch([("a.txt", "name: A\nat: 0 0\nhome: 0 0\nGG\n")])
    atlas = stitch([("a.txt", "name: A\nat: 2 3\nvillage: Little Town 0 1\nlookout: 1 0\ngate: Big Gate 1 1 4\nhome: 0 0\nHG\nGX\n")])
    ok(atlas.villages == [("Little Town", (2, 4), "A")], "a village's name can have spaces, and its spot is on the big map")
    ok(atlas.lookouts == [(3, 3)] and atlas.gates == {(3, 4): ("Big Gate", 4)} and atlas.home == (2, 3),
       "lookouts, gates and home too")


# ===========================================================================
# Waystones and travel
# ===========================================================================

def walk_onto(world, spot):
    """Stand next to spot and step onto it."""
    for direction, (dr, dc) in rules.DIRECTIONS.items():
        start = (spot[0] - dr, spot[1] - dc)
        if world.in_bounds(start) and world.tile(start) in rules.WALKABLE:
            world.player.pos = start
            world.do(direction)
            return
    raise AssertionError("no way onto %s" % (spot,))


def test_walking_onto_a_landmark_lights_its_waystone(world):
    stones = world.waystones
    ok(len(stones) >= 7 and stones[world.start] == "Home", "every land's landmark is a waystone, and home")
    ok(world.unlocked_waystones == {world.start}, "only home is lit at the start")
    oak = next(spot for spot, name in stones.items() if name == "Queen Oak")
    walk_onto(world, oak)
    ok(world.player.pos == oak and oak in world.unlocked_waystones, "the Queen Oak's waystone lights up")
    ok(any("waystone lights up" in text for text, _ in world.messages), "and you're told")


def test_space_on_a_lit_waystone_opens_the_travel_list_and_you_can_travel(world):
    oak = next(spot for spot, name in world.waystones.items() if name == "Queen Oak")
    walk_onto(world, oak)
    world.do("act")
    ok(world.travel_open, "SPACE on the Queen Oak opens the travel list")
    ok(world.travel_choices() == [("Home", world.start)], "you can go home")
    turn = world.turn
    ok(world.travel(world.start), "and travel there")
    ok(world.player.pos == world.start and not world.travel_open and world.turn == turn + 1,
       "you're home, the list is closed, and it took a turn")
    far = next(spot for spot, name in world.waystones.items() if name == "Dragon Bones")
    ok(not world.travel(far), "you can't travel to a waystone you haven't lit")


def test_you_can_only_travel_from_a_lit_waystone(world):
    oak = next(spot for spot, name in world.waystones.items() if name == "Queen Oak")
    world.unlocked_waystones.add(oak)
    world.player.pos = (world.start[0], world.start[1] + 3)
    ok(not world.travel(oak) and world.player.pos != oak, "not from the middle of a field")


def test_the_travel_list_works_with_keys_and_the_mouse():
    app = new_phase2_app()
    app.allow_tips = False
    world = app.game
    world.monsters = []
    stones = {name: spot for spot, name in world.waystones.items()}
    world.unlocked_waystones |= {stones["Queen Oak"], stones["Frost Peak"]}
    press(app, pygame.K_SPACE)                          # at home: rest, and open the list
    ok(world.travel_open, "SPACE at home opens the travel list")
    frames(app, 2)
    ok(len(app.travel_rows) == 2, "a row for each lit waystone")
    press(app, pygame.K_DOWN)
    press(app, pygame.K_UP)
    press(app, pygame.K_DOWN)
    ok(world.player.pos == world.start, "the arrow keys move the highlight, not you")
    ok([name for name, _ in world.travel_choices()] == ["Frost Peak", "Queen Oak"], "the list is in ABC order")
    press(app, pygame.K_RETURN)
    ok(world.player.pos == stones["Queen Oak"], "ENTER travels to the picked row: the Queen Oak")
    ok(app.player_px == list(game.tile_px(world.player.pos)), "the camera jumps there (no slide across the map)")
    press(app, pygame.K_SPACE)
    frames(app, 2)
    press(app, pygame.K_ESCAPE)
    ok(not world.travel_open and app.running, "Esc closes the list (and doesn't quit)")
    press(app, pygame.K_SPACE)
    frames(app, 2)
    home_row = app.travel_rows[0]
    click(app, home_row.center)
    ok(world.player.pos == world.start, "a click on a row travels there")


# ===========================================================================
# Lookouts and hidden chests
# ===========================================================================

def test_chests_are_hidden_until_a_lookout_spots_one(world):
    chests = rules.tiles_of(world.map, "T")
    ok(len(chests) >= 6 and world.hidden_chests() == chests, "the map's chests start hidden: %d" % len(chests))
    lookout = world.atlas.lookouts[0]
    walk_onto(world, lookout)
    ok(any("lookout tower" in text for text, _ in world.messages), "you're told it's a lookout")
    ok(world.do("act"), "SPACE climbs it")
    nearest = min(chests, key=lambda spot: (rules.distance(spot, lookout), spot))
    ok(world.found_chests == {nearest} and not world.chest_hidden(nearest), "the nearest chest is spotted")
    world.do("act")
    ok(len(world.found_chests) == 2, "climb again: the next nearest one")


def test_stepping_onto_a_hidden_chest_finds_it_and_it_opens(world):
    chest = next(spot for spot in world.hidden_chests() if world.land_name(spot) == "Frost Peaks")
    walk_onto(world, chest)
    ok(chest in world.found_chests, "you stumbled onto it")
    world.do("act")
    ok(world.tile(chest) == "G" and world.player.has_armor, "it opens: armor, in Frost Peaks")


def test_a_spotted_chest_shows_on_the_map_and_minimap():
    app = new_phase2_app()
    world = app.game
    chest = world.hidden_chests()[0]
    hidden = app.tiles[chest].copy()
    ok(draw_world.minimap_color(app, chest) != (255, 214, 90), "a hidden chest isn't on the minimap")
    world.found_chests.add(chest)
    world.effect("tile", pos=chest)
    frames(app, 2)
    ok(draw_world.minimap_color(app, chest) == (255, 214, 90), "a spotted one is gold on the minimap")
    ok(pygame.image.tobytes(app.tiles[chest], "RGB") != pygame.image.tobytes(hidden, "RGB"), "and drawn on the map")


# ===========================================================================
# Gates
# ===========================================================================

def test_the_desert_gate_opens_at_its_level(world):
    gate, (name, level) = next(iter(world.atlas.gates.items()))
    ok(world.tile(gate) == "X" and name == "Desert Gate" and level >= 2, "the Desert Gate is a rock in the way")
    world.player.pos = (gate[0], gate[1] - 1)
    world.player.level = level - 1
    ok(not world.do("right") and world.player.pos != gate, "too weak: it stays shut")
    ok(any("level %d" % level in text for text, _ in world.messages), "it says what level opens it")
    world.player.level = level
    world.do("right")
    ok(world.player.pos == gate and world.tile(gate) == "R" and gate in world.gates_open, "strong enough: it opens")


# ===========================================================================
# Saving
# ===========================================================================

def test_saving_keeps_the_lit_waystones_found_chests_and_open_gates(world):
    stones = {name: spot for spot, name in world.waystones.items()}
    world.unlocked_waystones |= {stones["Frost Peak"], stones["Lighthouse"]}
    chest = world.hidden_chests()[0]
    world.found_chests.add(chest)
    gate = next(iter(world.atlas.gates))
    world.gates_open.add(gate)
    ok(save.save_game(world), "it saves")
    back = save.load_game()
    for name in ("unlocked_waystones", "found_chests", "gates_open", "lookouts_climbed"):
        ok(getattr(back, name) == getattr(world, name), "the %s come back" % name)
    ok(back.atlas.villages == world.atlas.villages and back.atlas.home == world.atlas.home, "and the villages")
    ok(not back.travel_open, "the travel list is closed when you come back")


def test_an_older_save_without_waystones_still_loads(world):
    data = save.game_to_data(world)
    back = save.data_to_game(data)
    for name in waystones.FEATURES:
        delattr(back, name)
    waystones.after_load(back)
    ok(back.unlocked_waystones == {back.start} and back.found_chests == set(), "it starts them fresh")
