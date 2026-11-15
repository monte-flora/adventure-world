"""
THE PHASE 2 WORLD MAP: one text file per land in levels/world/, stitched into one big map.
Stage 2a drew the real big world: 8 land files (Home Meadow in the middle-west, the woods and the
ruins in the north, the Great Lake with Portal Island, Frost Peaks, Sunscorch Desert and Murk Swamp).
(The waystones, lookouts, villages and gates are tested in test_phase2_waystones.py.) And there's no fog: you can see the whole world, on the minimap too.
"""

import pytest

import game
import rules
from helpers import frames, ok
from phase2 import Phase2Game, world_map
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)


@pytest.fixture(scope="module")
def atlas():
    return world_map.load()


def test_every_land_file_loads(atlas):
    files = world_map.land_files()
    ok(len(files) >= 7 and len(atlas.lands) == len(files), "one land for every file: %d files" % len(files))
    names = [land[0] for land in atlas.lands]
    for name in ("Home Meadow", "Whispering Woods", "The Great Lake", "Portal Island", "Frost Peaks",
                 "Sunscorch Desert", "Murk Swamp"):
        ok(name in names, "the world has %s" % name)


def test_the_map_is_much_bigger_than_the_classic_one(atlas):
    classic = rules.parse_map(rules.WORLD_MAP)
    ok(atlas.rows * atlas.cols >= 2 * len(classic) * len(classic[0]),
       "at least twice the classic map: %d x %d" % (atlas.cols, atlas.rows))
    ok(all(len(row) == atlas.cols for row in atlas.grid), "every row of the big map is the same length")


def test_the_map_is_3_to_4_times_the_classic_one(atlas):
    classic = rules.parse_map(rules.WORLD_MAP)
    times = atlas.rows * atlas.cols / (len(classic) * len(classic[0]))
    ok(100 <= atlas.cols <= 120 and 70 <= atlas.rows <= 80, "about 110 x 76: %d x %d" % (atlas.cols, atlas.rows))
    ok(times >= 3, "at least 3 times the classic map (%.1f times)" % times)


def test_a_phase_2_game_is_on_the_big_map(atlas):
    world = Phase2Game("Hero", seed=1)
    ok((world.rows, world.cols) == (atlas.rows, atlas.cols), "the game plays on the big map")
    ok(world.tile(world.start) == "H" and world.portal, "it has a home and a Portal")
    ok(world.land_name((50, 100)) == "Sunscorch Desert" and world.land_name((65, 20)) == "Murk Swamp",
       "the new lands are where their files say")
    new_land = [spot for spot in world.mainland if world.land_name(spot) in ("Frost Peaks", "Murk Swamp")]
    ok(len(new_land) > 300, "you can walk into the new lands from home (over the old bridges)")
    mines = [spot for spot in world.cave_plan if spot in world.mainland]
    ok(len(world.cave_plan) > 12 and len(mines) > 12, "more Mines than the classic map, each with a cave")
    ok(len(world.diamond_mines & world.mainland) >= rules.DIAMONDS_NEEDED, "enough diamonds to finish")


def test_walking_into_a_new_land_says_its_name():
    world = Phase2Game("Hero", seed=1)
    world.monsters = []
    world.player.pos, world.player.level = (44, 72), 3     # at the Desert Gate, strong enough to open it
    world.do("right")
    ok("Sunscorch Desert" in world.lands_seen, "you found the desert")
    ok(any(e["type"] == "land" and e["text"] == "SUNSCORCH DESERT" for e in world.effects), "its name pops up")


def test_land_files_drawn_wrong_say_what_is_wrong():
    land = "name: Test\nat: 0 0\nGG\nGG\n"
    stitch = world_map.stitch
    with pytest.raises(world_map.WorldMapError, match="both draw"):
        stitch([("a.txt", land), ("b.txt", land.replace("Test", "Other"))])
    with pytest.raises(world_map.WorldMapError, match="letters"):
        stitch([("a.txt", "name: Test\nat: 0 0\nGZ\n")])
    with pytest.raises(world_map.WorldMapError, match="at:"):
        stitch([("a.txt", "name: Test\nGG\n")])
    with pytest.raises(world_map.WorldMapError, match="same length"):
        stitch([("a.txt", "name: Test\nat: 0 0\nGG\nG\n")])
    atlas = stitch([("a.txt", "name: A\nat: 0 0\nG.\n"), ("b.txt", "name: B\nat: 1 1\nH\n")])
    ok(atlas.grid == [["G", "W"], ["W", "H"]], "dots and gaps are open water")
    ok(atlas.land_at((0, 1)) is None and atlas.land_at((1, 1))[0] == "B", "a square is in the land that drew it")


# ===========================================================================
# No fog
# ===========================================================================

def test_no_fog_in_phase_2():
    world = Phase2Game("Hero", seed=1)
    everywhere = {(r, c) for r in range(world.rows) for c in range(world.cols)}
    ok(world.seen == everywhere, "you can see the whole map from the start")
    ok(world.is_visible((world.rows - 1, world.cols - 1)), "even the far corner")
    world.go_to_nightfall()
    ok(len(world.seen) == world.rows * world.cols, "Nightfall Hollow has no fog either")


def fogged_pixels(app):
    """Paint the fog bright pink, draw a frame, and count the pink pixels on screen."""
    pink = (255, 0, 255)
    app.fog_tile.fill(pink)
    app.dim_tile.fill(pink)
    app.dim_tile.set_alpha(255)
    frames(app, 1)
    pixels = 0
    for x in range(0, game.VIEW_W, 8):
        for y in range(0, game.VIEW_H, 8):
            pixels += app.screen.get_at((x, y))[:3] == pink
    return pixels


def test_no_fog_is_drawn_in_phase_2_but_classic_keeps_its_fog():
    app = new_phase2_app()
    app.game.player.pos = (12, 12)
    app.player_px = list(game.tile_px((12, 12)))
    app.camera = app.camera_target()
    frames(app, 100)
    ok(fogged_pixels(app) == 0, "Phase 2: no fog on the map")
    classic = game.App("Hero", seed=1, sound=False)
    classic.new_game()
    classic.game.story.clear()
    classic.game.monsters = []
    frames(classic, 100)                                 # (the last story card fades away)
    ok(fogged_pixels(classic) > 50, "Classic still has its fog")


def test_the_minimap_shows_the_whole_big_world():
    app = new_phase2_app()
    frames(app, 2)
    world = app.game
    size = min(150 / world.cols, (game.LOG_H - 6 - 22) / world.rows)
    ok(size >= 1, "the big map is squeezed into the minimap box (%.2f pixels a square)" % size)
    x, y0 = game.VIEW_W - 166, game.VIEW_H + 4 + 22
    far = (world.rows - 1, world.cols - 1)                 # the far corner of the desert
    color = app.screen.get_at((x + int(far[1] * size), y0 + int(far[0] * size)))[:3]
    ok(color != (14, 14, 24), "the far corner is drawn on the minimap (not dark)")
