"""
PHASE 2'S NEW ART, PART 2: everyone on the map drawn whole at 32 x 32 (one full map square), and new
32 x 32 pictures for 9 monsters. Classic keeps sprites.py's pictures, and so do the Skeleton and the Ember Skull.
"""

import hashlib

import pygame

import game
import phase2
import rules
import sprites
from helpers import frames, new_app, ok
from phase2 import art, people
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)

NEW_MONSTERS = ["Zombie", "Spider", "Sea Serpent", "Guardian", "Warden", "Slime", "Scorpion", "Frost Wolf", "Bog Lurker"]
OLD_MONSTERS = ["Skeleton", "Ember Skull"]
SKELETON, EMBER_SKULL = "cf85af6815f8", "f2ad7be0f078"       # fingerprint() of their sprites.py letters on 2026-11-13
LOOKS = ["farmer", "shopkeeper", "blacksmith", "guide", "wizard", "hunter", "kid", "cat", "villager", "fisher",
         "lost_bag", "frog", "toy_boat"]


def check_letters(name, picture, width=32, height=32):
    ok(len(picture) == height, "%s is %d rows tall" % (name, height))
    for row in picture:
        ok(len(row) == width, "every row of %s is %d wide" % (name, width))
        for letter in row:
            ok(letter == "." or letter in art.COLORS, "%s only uses letters in art.COLORS (not %r)" % (name, letter))


def same_picture(a, b):
    return a.get_size() == b.get_size() and pygame.image.tostring(a, "RGBA") == pygame.image.tostring(b, "RGBA")


def fingerprint(picture):
    return hashlib.sha1("\n".join(picture).encode()).hexdigest()[:12]


# ===========================================================================
# The people on the map
# ===========================================================================

def test_every_look_is_drawn_whole_at_32_x_32():
    looks = {who["look"] for who in people.all_people()} | set(art.MAP_ART) | set(LOOKS)
    for look in looks:
        ok(look in art.BIG_MAP_ART, "%s has a 32 x 32 picture" % look)
        check_letters("big " + look, art.BIG_MAP_ART[look])
        ok(art.big_picture(look).get_size() == (game.TILE, game.TILE), "%s fills one map square (64 pixels)" % look)
        letters = set("".join(art.BIG_MAP_ART[look])) - {"."}
        ok("k" in letters and len(letters) >= 6, "%s has a dark outline and a few shades" % look)
        ok(any(row.strip(".") for row in art.BIG_MAP_ART[look][-2:]), "%s stands on the bottom of its square" % look)
    ok(len({id(art.BIG_MAP_ART[look]) for look in LOOKS}) == 13, "13 different pictures")
    ok(art.BIG_MAP_ART["merchant"] is art.BIG_MAP_ART["shopkeeper"], "a merchant is a shopkeeper")
    ok(art.BIG_MAP_ART["mage"] is art.BIG_MAP_ART["wizard"], "a mage is a wizard")
    check_letters("the 32 x 32 Hero (an experiment)", art.BIG_HERO)


def test_a_look_with_no_big_picture_shows_its_small_one_just_as_big():
    sprites.PEOPLE_ART["test_only_look"] = sprites.CAT
    try:
        ok(art.big_picture("test_only_look").get_size() == (64, 64), "the old 16 x 16 picture, 4 pixels each")
    finally:
        del sprites.PEOPLE_ART["test_only_look"]


def test_people_on_the_map_are_the_big_pictures_at_the_corner_of_their_square():
    app = new_phase2_app()
    world = app.game
    world.monsters = []
    frames(app, 90)                                          # (the screen fades in when a game starts)
    seen = 0
    for who, pos in people.people_here(world):
        if who.get("pace") or sum(abs(a - b) for a, b in zip(pos, world.player.pos)) < 2:
            continue                                         # (someone pacing isn't at the corner of a square)
        x, y = app.on_screen(*game.tile_px(pos))
        if not app.screen.get_rect().contains(pygame.Rect(x, y - 2, 64, 68)):
            continue
        picture = art.big_picture(who["look"])
        if world.player.pos[1] < pos[1]:
            picture = pygame.transform.flip(picture, True, False)
        best = 0
        for bob in (-2, -1, 0, 1, 2):                        # they bob up and down a little
            same = total = 0
            for px in range(0, 64, 2):
                for py in range(0, 64, 2):
                    if picture.get_at((px, py)).a == 255:
                        total += 1
                        same += app.screen.get_at((int(x) + px, int(y) + py + bob))[:3] == picture.get_at((px, py))[:3]
            best = max(best, same / total)
        ok(best > 0.9, "%s's 32 x 32 picture is drawn at the corner of the square (%d%%)" % (who["id"], best * 100))
        seen += 1
    ok(seen >= 1, "someone was on the screen to check")


def test_classic_keeps_the_old_people():
    ok(len(sprites.PEOPLE_ART["farmer"]) == 16 and len(sprites.PEOPLE_ART["farmer"][0]) == 16,
       "sprites.py's people are still 16 x 16")
    ok(not hasattr(sprites, "BIG_MAP_ART") and not hasattr(sprites, "BIG_HERO"), "the big pictures aren't in sprites.py")
    for look in LOOKS:
        check_letters("small " + look, art.MAP_ART[look], 16, 16)      # the small ones are still there


# ===========================================================================
# The monsters
# ===========================================================================

def test_nine_monsters_have_a_new_32_x_32_picture():
    ok(sorted(art.MONSTER_ART) == sorted(NEW_MONSTERS), "the 9 new pictures (not the Skeleton or the Ember Skull)")
    for kind in NEW_MONSTERS:
        ok(kind in rules.MONSTER_TYPES or kind in sprites.MONSTER_ART, "%s is a monster in the game" % kind)
        picture = art.MONSTER_ART[kind]
        check_letters(kind, picture)
        letters = set("".join(picture)) - {"."}
        ok("k" in letters and len(letters) >= 5, "%s has a dark outline and a few shades" % kind)
        ok(any(row.strip(".") for row in picture[-2:]), "%s stands on the bottom of its picture" % kind)
        filled = sum(ch != "." for row in picture for ch in row)
        ok(filled >= 250, "%s fills a good part of its picture (%d pixels)" % (kind, filled))
    ok(len({fingerprint(art.MONSTER_ART[kind]) for kind in NEW_MONSTERS}) == 9, "9 different pictures")


def test_the_skeleton_and_the_ember_skull_are_unchanged():
    ok(fingerprint(sprites.SKELETON) == SKELETON, "the Skeleton's letters didn't change")
    ok(fingerprint(sprites.EMBER_SKULL) == EMBER_SKULL, "the Ember Skull's letters didn't change")
    app = new_phase2_app()
    for kind in OLD_MONSTERS:
        ok(phase2.monster_picture(app, kind, 3) is None, "Phase 2 has no new picture of the %s" % kind)
        for scale in (3, 8):
            ok(same_picture(app.monster_sprite(kind, scale), game.make_sprite(sprites.MONSTER_ART[kind], scale)),
               "in Phase 2 the %s is still its sprites.py picture (x%d)" % (kind, scale))


def test_phase_2_monsters_are_the_new_pictures_and_as_big_as_before():
    app = new_phase2_app()
    for kind in NEW_MONSTERS:
        for scale in (3, 6, 7, 8):                           # the map, the name screen, a story card, a fight
            picture = app.monster_sprite(kind, scale)
            ok(picture.get_size() == (16 * scale, 16 * scale), "%s x%d is as big on the screen as before" % (kind, scale))
            ok(not same_picture(picture, game.make_sprite(sprites.MONSTER_ART[kind], scale)), "and it's the new picture")
        ok(same_picture(app.monster_sprite(kind, 8), art.make(art.MONSTER_ART[kind], 4)),
           "in a fight the %s is its 32 x 32 picture, 4 pixels each" % kind)
        ok(app.monster_sprite(kind, 8) is app.monster_sprite(kind, 8), "the picture is only made once")


def test_shadow_monsters_are_still_tinted_dark_purple():
    app = new_phase2_app()
    for kind in NEW_MONSTERS:
        plain, shadow = app.monster_sprite(kind, 8), app.monster_sprite(kind, 8, True)
        ok(shadow.get_size() == plain.get_size(), "a Shadow %s is the same size" % kind)
        darker = total = 0
        for x in range(0, 128, 4):
            for y in range(0, 128, 4):
                a, b = plain.get_at((x, y)), shadow.get_at((x, y))
                ok(a.a == b.a, "and the same shape")
                if a.a and sum(a[:3]) > 150:
                    total += 1
                    darker += sum(b[:3]) < sum(a[:3]) and b.g <= a.g
        ok(total > 50 and darker == total, "a Shadow %s is darker, with less green (%d of %d spots)" % (kind, darker, total))


def test_classic_keeps_the_old_monsters():
    classic = new_app()
    ok(not phase2.is_phase2(classic.game), "a Classic game")
    for kind in sprites.MONSTER_ART:
        ok(phase2.monster_picture(classic, kind, 8) is None, "Classic: no new picture of the %s" % kind)
        for scale in (3, 8):
            ok(same_picture(classic.monster_sprite(kind, scale), game.make_sprite(sprites.MONSTER_ART[kind], scale)),
               "Classic's %s is its sprites.MONSTER_ART picture (x%d)" % (kind, scale))
        ok(len(sprites.MONSTER_ART[kind]) == 16 and len(sprites.MONSTER_ART[kind][0]) == 16, "which is still 16 x 16")


def test_one_app_shows_the_right_monsters_in_each_kind_of_game():
    app = new_phase2_app()
    new = app.monster_sprite("Zombie", 8)
    app.game = rules.Game("Hero", seed=1)                    # the same window, now playing Classic
    ok(same_picture(app.monster_sprite("Zombie", 8), game.make_sprite(sprites.ZOMBIE, 8)), "Classic: the old Zombie")
    ok(not same_picture(app.monster_sprite("Zombie", 8), new), "not the one left over from Phase 2")


def test_fights_and_hitboxes_did_not_change():
    app = new_phase2_app()
    ok(app.battle_spot("monster")[0] == app.battle_box.right - 110 - 128, "the fight's monster stands where it did")
    ok(app.monster_sprite("Zombie", 8).get_size() == (128, 128), "and is 128 pixels big, like before")
