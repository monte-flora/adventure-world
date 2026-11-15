"""
PHASE 2'S NEW ART, PART 3: the Hero himself at 32 x 32 (the map, map fights, caves and the throne room), the new
monster pictures in caves, and crisp monsters on the map. Only pictures change: Classic keeps sprites.py's
Hero and monsters, and nobody's body (the box that bumps into things) changes size.
"""

import pygame

import caves
import game
import phase2
import rules
import sprites
from helpers import cave_from, frames, new_app, ok
from phase2 import art, hero
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)

ROOM = ["####################",
        "#..................#",
        "#..................#",
        "#S...............E.#",
        "####################"]
NEW_MONSTERS = ["Zombie", "Spider", "Slime", "Scorpion", "Frost Wolf", "Bog Lurker"]    # the ones with a new picture
CAVE_MONSTERS = ["Zombie", "Spider"]                    # the ones of them that live in caves
POSES = ["front stand", "walk down 1", "walk down 2", "back stand", "walk up 1", "walk up 2", "climb 1", "climb 2",
         "side stand", "side step 1", "side pass 1", "side step 2", "side pass 2", "side jump", "side fall",
         "wall hold", "wall reach 1", "wall reach 2", "wall slide"]


def same_picture(a, b):
    return a.get_size() == b.get_size() and pygame.image.tostring(a, "RGBA") == pygame.image.tostring(b, "RGBA")


def in_a_cave(app, kinds=()):
    """Put this app's game in a little cave, with these monsters in it."""
    world, cave = cave_from(ROOM, app.game)
    cave.monsters = []
    for i, kind in enumerate(kinds):
        cave.add_monster(kind, 3, 4 + 2 * i)
    app.build_cave_tiles(cave)
    app.cam, app.time = (0, 0), 1.0
    cave.you.on_ground = True                   # (standing on the floor, not falling onto it)
    return cave


def drawn_in_cave(app):
    """Draw the cave once. Returns the letters of everything draw_body drew: (monsters, the Hero)."""
    seen = []
    draw_body = app.draw_body
    app.draw_body = lambda surf, body, letters, **more: (seen.append((body, letters)), draw_body(surf, body, letters, **more))[1]
    app.draw_cave(pygame.Surface((game.VIEW_W, game.VIEW_H)))
    app.draw_body = draw_body
    you = app.game.cave.you
    return [letters for body, letters in seen if body is not you], [letters for body, letters in seen if body is you]


# ===========================================================================
# The letters
# ===========================================================================

def test_every_hero_pose_has_a_32_x_32_picture():
    ok(sorted(hero.POSES) == sorted(POSES), "The Hero has a picture for every pose he had: %s" % ", ".join(POSES))
    pictures = dict(hero.POSES)
    pictures.update(hero.OVERLAYS)
    ok(len(hero.OVERLAYS) == 4, "and his armor has 4 pictures to wear on top (front, side, back, wall)")
    for name, picture in pictures.items():
        ok(len(picture) == 32, "%s is 32 rows tall" % name)
        for row in picture:
            ok(len(row) == 32, "every row of %s is 32 wide" % name)
            for letter in row:
                ok(letter == "." or letter in art.COLORS, "%s only uses letters in art.COLORS (not %r)" % (name, letter))
    for name, picture in hero.POSES.items():
        ok(sum(letter != "." for row in picture for letter in row) > 250, "%s is a whole knight, not a scrap" % name)
    ok(len({"\n".join(picture) for picture in hero.POSES.values()}) == len(POSES), "and no 2 poses are the same picture")


def test_the_cave_pictures_have_the_same_names_as_the_old_ones():
    app = new_app()
    for view in ("side_view", "side_view_armored", "wall_view", "wall_view_armored"):
        ok(sorted(getattr(hero.VIEWS, view)) == sorted(getattr(app, view)), "%s has every pose of the old one" % view)
    ok(len(hero.VIEWS.climb_view) == len(app.climb_view) == 2, "and the ladder has its 2 pictures")
    for name, letters in hero.VIEWS.side_view.items():
        ok(hero.VIEWS.side_view_armored[name] != letters, "with armor on, side %s looks different" % name)
        ok(game.art_bottom(letters) == 2 * game.art_bottom(app.side_view[name]),
           "side %s has his feet at the same height as the old picture" % name)
    for name, letters in hero.VIEWS.wall_view.items():
        ok(game.art_bottom(letters) == 2 * game.art_bottom(app.wall_view[name]), "wall %s too" % name)


def test_the_old_hero_is_untouched():
    ok(len(sprites.PLAYER) == 16 and len(sprites.SIDE_STAND) == 16 and len(sprites.CLIMB_1) == 16,
       "sprites.py still has the 16 x 16 Hero")
    ok(not hero.is_big(sprites.SIDE_STAND) and not hero.is_big(sprites.ZOMBIE), "and they aren't mixed up with the new ones")


# ===========================================================================
# The map
# ===========================================================================

def test_hero_on_the_map_is_32_x_32_and_fills_his_square():
    app = new_phase2_app()
    for way in ("down", "up", "left", "right"):
        for name in (way, way + " armor"):
            for pose in range(3):
                picture = phase2.hero_map(app, name, pose)
                ok(picture.get_size() == (64, 64), "%s %d: 64 pixels, one map square" % (name, pose))
                ok(picture is phase2.hero_map(app, name, pose), "and only made once")
        ok(not same_picture(phase2.hero_map(app, way, 0), phase2.hero_map(app, way + " armor", 0)),
           "his armor shows when he faces %s" % way)
    ok(same_picture(phase2.hero_map(app, "left", 0), pygame.transform.flip(phase2.hero_map(app, "right", 0), True, False)),
       "facing left is facing right, flipped over")
    ok(same_picture(phase2.hero_map(app, "down", 0), art.make(hero.FRONT_STAND, 2)), "2 pixels a square: crisp")
    frames(app, 3)
    asked = []
    hero_map = phase2.hero_map
    phase2.hero_map = lambda *args: (asked.append(args[1:]), hero_map(*args))[1]
    try:
        app.draw()
    finally:
        phase2.hero_map = hero_map
    ok(len(asked) == 1 and asked[0][0] in ("down", "up", "left", "right"), "the map draws the new Hero: %r" % (asked,))


def test_classic_keeps_the_old_hero():
    app = new_app()
    ok(phase2.hero_map(app, "down", 0) is None and phase2.hero_fight(app, False) is None, "Classic: no new Hero on the map or in fights")
    ok(phase2.hero_views(app) is None and phase2.hero_card(app) is None, "nor in caves or on story cards")
    ok(app.hero_views() is app, "its caves use the pictures load_art made")
    ok(app.side_view["stand"] is sprites.SIDE_STAND and app.climb_view[0] is sprites.CLIMB_1, "the 16 x 16 ones of sprites.py")
    ok(same_picture(app.map_walk["down"][0], game.make_sprite(sprites.PLAYER, 3)), "on the map he's the old 48 pixel Hero")
    ok(same_picture(app.art["player_big"], game.make_sprite(sprites.PLAYER, 8)), "and in a fight too")
    in_a_cave(app, ["Zombie", "Spider", "Skeleton"])
    monsters, you = drawn_in_cave(app)
    ok(monsters == [sprites.MONSTER_ART[kind] for kind in ("Zombie", "Spider", "Skeleton")], "Classic caves: sprites.MONSTER_ART")
    ok(you == [sprites.SIDE_STAND], "and the old Hero")
    ok(phase2.map_monster_scale(app, "Zombie") is None, "Classic map monsters keep their size")


# ===========================================================================
# Caves and the throne room
# ===========================================================================

def test_hero_in_a_phase_2_cave_is_the_new_picture_just_as_big():
    app = new_phase2_app()
    cave = in_a_cave(app)
    monsters, you = drawn_in_cave(app)
    ok(you == [hero.VIEWS.side_view["stand"]], "standing in a cave he's the 32 x 32 side picture")
    app.game.player.armor = 1
    ok(drawn_in_cave(app)[1] == [hero.VIEWS.side_view_armored["stand"]], "with his armor on top when he wears it")
    app.game.player.armor = 0
    cave.you.climbing = True
    ok(drawn_in_cave(app)[1][0] in hero.VIEWS.climb_view, "on a ladder: his back")
    cave.you.climbing = False
    cave.you.on_wall = True
    ok(drawn_in_cave(app)[1] == [hero.VIEWS.wall_view["hold"]], "on a climbing wall: gripping it")
    cave.you.on_wall = False
    old = app.cave_sprite(sprites.SIDE_STAND)
    for letters in list(hero.VIEWS.side_view.values()) + hero.VIEWS.climb_view + list(hero.VIEWS.wall_view_armored.values()):
        ok(app.cave_sprite(letters).get_size() == old.get_size() == (80, 80), "every cave picture is 80 pixels, like before")
    ok(same_picture(app.cave_sprite(hero.VIEWS.side_view["stand"], flip=True),
                    pygame.transform.flip(app.cave_sprite(hero.VIEWS.side_view["stand"]), True, False)), "he still turns around")


def test_hero_stands_on_the_floor_where_the_old_one_did():
    spots = []
    for app, letters in ((new_app(), sprites.SIDE_STAND), (new_phase2_app(), hero.VIEWS.side_view["stand"])):
        cave = in_a_cave(app)
        spots.append(app.draw_body(pygame.Surface((game.VIEW_W, game.VIEW_H)), cave.you, letters))
    ok(spots[0] == spots[1], "the new picture is drawn at the same spot as the old one: %r" % (spots,))


def test_phase_2_caves_show_the_new_monsters():
    app = new_phase2_app()
    in_a_cave(app, CAVE_MONSTERS + ["Skeleton", "Ember Skull"])
    monsters, _ = drawn_in_cave(app)
    ok(monsters[:len(CAVE_MONSTERS)] == [art.MONSTER_ART[kind] for kind in CAVE_MONSTERS], "Phase 2 caves draw art.MONSTER_ART")
    ok(monsters[len(CAVE_MONSTERS):] == [sprites.SKELETON, sprites.EMBER_SKULL], "the Skeleton and the Ember Skull keep theirs")
    for kind in NEW_MONSTERS:
        new, old = app.cave_sprite(art.MONSTER_ART[kind]), app.cave_sprite(sprites.MONSTER_ART[kind])
        ok(new.get_size() == old.get_size(), "the new %s is as big in a cave as the old one" % kind)
        ok(not same_picture(new, old), "and it's the new picture")
    shadow = app.cave_sprite(art.MONSTER_ART["Zombie"], shadow=True)
    ok(not same_picture(shadow, app.cave_sprite(art.MONSTER_ART["Zombie"])), "shadow monsters are still tinted")


def test_bodies_did_not_change():
    ok((caves.PLAYER_W, caves.PLAYER_H) == (0.8, 1.15), "your body in a cave is the size it was")
    sizes = []
    for app in (new_app(), new_phase2_app()):
        cave = in_a_cave(app, CAVE_MONSTERS + ["Skeleton"])
        sizes.append([(cave.you.w, cave.you.h)] + [(m.kind, m.w, m.h) for m in cave.monsters])
    ok(sizes[0] == sizes[1], "Phase 2 bodies (you and the monsters) are the same size as Classic's")
    ok(game.CAVE_SCALE == 5 and game.TILE == 64, "and the cave is drawn as big as before")


def test_the_throne_room_shows_the_new_hero():
    app = game.App("Hero", seed=1, sound=False, throne=True, phase2_mode="phase2")
    app.new_game()
    app.game.story.clear()
    frames(app, 5)
    ok(app.game.cave is not None and app.game.cave.is_throne_room, "we're in the throne room")
    _, you = drawn_in_cave(app)
    ok(you and all(hero.is_big(letters) for letters in you), "and the Hero is his 32 x 32 picture there")


# ===========================================================================
# Map fights and map monsters
# ===========================================================================

def test_hero_in_a_map_fight_is_the_new_picture_just_as_big():
    app = new_phase2_app()
    picture, hand = phase2.hero_fight(app, False)
    ok(picture.get_size() == app.art["player_big"].get_size() == (128, 128), "128 pixels, like the old one")
    ok(same_picture(picture, art.make(hero.FRONT_STAND, 4)), "the 32 x 32 front picture, 4 pixels a square")
    ok(not same_picture(phase2.hero_fight(app, True)[0], picture), "his armor shows")
    column, row = int(hand[0] // 4), int(hand[1] // 4)
    ok(hero.FRONT_STAND[row][column] != ".", "his sword is put in his hand, not in the air")
    world = app.game
    world.start_battle(rules.Monster("Zombie", world.player.pos))
    app.state = "battle"
    app.draw()
    px, py = app.battle_spot("player")
    ok(app.screen.get_at((int(px) + 64, int(py) + 64))[:3] in [tuple(color[:3]) for color in art.COLORS.values()],
       "and the fight draws him")


def test_new_monsters_are_crisp_on_the_map():
    app = new_phase2_app()
    for kind in NEW_MONSTERS + ["Sea Serpent", "Guardian", "Warden"]:
        scale = phase2.map_monster_scale(app, kind)
        ok(scale == 4, "the %s is drawn at 64 pixels on the map" % kind)
        ok(same_picture(app.monster_sprite(kind, scale), art.make(art.MONSTER_ART[kind], 2)),
           "its 32 x 32 picture, 2 whole pixels a square (not shrunk and soft)")
    for kind in ("Skeleton", "Ember Skull"):
        ok(phase2.map_monster_scale(app, kind) is None, "the %s keeps its old picture and size" % kind)
    world = app.game
    spot = next(p for p in ((world.player.pos[0], world.player.pos[1] + d) for d in (1, -1, 2, -2))
                if world.tile(p) in rules.WALKABLE)
    world.monsters = [rules.Monster("Zombie", spot)]
    asked = []
    monster_sprite = app.monster_sprite
    app.monster_sprite = lambda kind, scale, shadow=False: (asked.append((kind, scale)), monster_sprite(kind, scale, shadow))[1]
    app.draw()
    ok(("Zombie", 4) in asked, "the map asks for the crisp picture")
