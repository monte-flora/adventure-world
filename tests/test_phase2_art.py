"""
PHASE 2'S NEW ART (phase2/art.py and art_big.py): the townsfolk on the map, their big faces for the
dialogue box, and the new Shadow King. Classic keeps the old pictures in sprites.py.
"""

import pygame

import game
import phase2
import rules
import sprites
import throne
from helpers import frames, new_app, ok
from phase2 import art, art_big, draw_people, people
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)


def all_looks():
    return {who["look"] for who in people.all_people()} | set(art.MAP_ART)


def check_letters(name, picture, width, height):
    ok(len(picture) == height, "%s is %d rows tall" % (name, height))
    for row in picture:
        ok(len(row) == width, "every row of %s is %d wide" % (name, width))
        for letter in row:
            ok(letter == "." or letter in art.COLORS, "%s only uses letters in art.COLORS (not %r)" % (name, letter))


# ===========================================================================
# The people
# ===========================================================================

def test_every_look_has_a_map_picture_and_a_face_of_the_right_size():
    looks = all_looks()
    for need in ("farmer", "shopkeeper", "merchant", "blacksmith", "guide", "wizard", "mage", "hunter", "kid", "cat",
                 "villager", "fisher"):
        ok(need in looks, "there's a %s" % need)
    for look in looks:
        ok(look in art.MAP_ART, "%s has a new map picture" % look)
        ok(look in art.PORTRAITS, "%s has a big face" % look)
        check_letters(look, art.MAP_ART[look], 16, 16)
        check_letters(look + "'s face", art.PORTRAITS[look], 32, 32)
        ok(art.map_picture(look, 3).get_size() == (48, 48), "on the map %s is as big as the Hero" % look)
        ok(art.portrait(look).get_size() == (160, 160), "%s's face fills the dialogue box's 160 x 160" % look)
    for name, picture in art_big.BIG_PEOPLE.items():
        check_letters("big " + name, picture, 32, 32)


def test_the_new_colors_are_only_in_the_new_file():
    for letter, color in sprites.COLORS.items():
        ok(art.COLORS[letter] == color, "art.COLORS keeps every color of sprites.COLORS")
    ok(len(art.COLORS) > len(sprites.COLORS), "and it has more shades")
    ok("S" not in sprites.COLORS and "2" not in sprites.COLORS, "sprites.COLORS didn't get the new letters")
    art.check_art()


def test_every_person_has_3_shades_and_a_dark_outline():
    for look in ("farmer", "shopkeeper", "blacksmith", "guide", "wizard", "hunter", "kid", "villager", "fisher"):
        letters = set("".join(art.MAP_ART[look])) - {"."}
        ok("k" in letters, "%s has a dark outline" % look)
        ok(letters & set("Ss") and "d" in letters, "%s's face has a light side and a shaded side" % look)
        ok(len(letters) >= 8, "%s uses plenty of shades" % look)


def test_a_look_with_no_new_picture_keeps_its_old_one():
    sprites.PEOPLE_ART["test_only_look"] = sprites.CAT
    try:
        ok(art.map_art("test_only_look") is sprites.CAT, "the map shows its sprites.py picture")
        ok(art.portrait("test_only_look").get_size() == (160, 160), "and its face is that picture, as big as a face")
    finally:
        del sprites.PEOPLE_ART["test_only_look"]


def test_talking_shows_the_big_face():
    app = new_phase2_app()
    world = app.game
    who, pos = people.people_here(world)[0]
    for way, (dr, dc) in rules.DIRECTIONS.items():           # walk into them from an open square
        stand = (pos[0] - dr, pos[1] - dc)
        if world.tile(stand) in rules.WALKABLE and stand not in world.people.values():
            world.player.pos = stand
            world.do(way)
            break
    frames(app, 90)                                          # (the screen fades in when a game starts)
    ok(app.state == "people" and app.people_screen.kind == "talk", "the dialogue box is open")
    box = draw_people.talk_box(app)
    frame = pygame.Rect(box.x + 18, box.y + 22, 172, 172)     # the portrait's frame in draw_people.draw_talk
    face = art.portrait(who["look"])
    spot = face.get_rect(center=frame.center).move(0, 6)
    same = total = 0
    for x in range(0, 160, 5):
        for y in range(0, 150, 5):
            if face.get_at((x, y)).a == 255:
                total += 1
                same += app.screen.get_at((spot.x + x, spot.y + y))[:3] == face.get_at((x, y))[:3]
    ok(total > 300 and same == total, "the big 32 x 32 face is drawn in the frame (%d of %d spots)" % (same, total))


# ===========================================================================
# The Shadow King
# ===========================================================================

def test_the_new_king_is_bigger_art_with_the_same_hitbox():
    check_letters("the king", art.KING, 36, 36)
    check_letters("the angry king", art.ANGRY_KING, 36, 36)
    check_letters("the king's story card", art.KING_BIG, 44, 36)
    ok((throne.KING_W, throne.KING_H) == (1.5, 2.0), "his size in the fight's rules didn't change")
    ok(art.KING[-1].strip("."), "his feet are on the bottom row, so they touch the floor")
    old_size = len(sprites.SHADOW_KING[0]) * game.KING_SCALE
    ok(len(art.KING[0]) * art.KING_SCALE == old_size, "he's as wide on the screen as before (144 pixels)")
    ok(len(art.KING) * art.KING_SCALE >= throne.KING_H * game.TILE, "and at least as tall as his hitbox")
    ok(art.KING_SCALE == 4, "his pixels are the same size as the Hero's in a cave")
    ok(art.ANGRY_KING != art.KING, "the angry king looks different")
    ok(not set("".join(art.ANGRY_KING)) & set("PVp2vL"), "with no purple left: it all turned red and fiery")
    ok(any("L" in row for row in art.KING), "his eyes and gems have a white-hot middle, which glows")


def test_classic_keeps_the_old_king_and_phase_2_gets_the_new_one():
    classic = new_app()
    ok(phase2.king_look(classic) is None and phase2.king_card(classic) is None, "Classic: no new king")
    ok(classic.king_pictures[0].get_size() == (144, 144), "Classic's king picture is the old one")
    ok(classic.art["king_big"].get_size() == (192, 192), "and so is its story card")
    app = new_phase2_app()
    pictures, glows, under = phase2.king_look(app)
    ok(len(pictures) == 2 and len(glows) == 2 and under == 0, "Phase 2: a calm and an angry king, each with a glow")
    wide, tall = pictures[0].get_size()
    ok(wide == 144 + 2 * art.GLOW_PAD and tall == 144 + art.GLOW_PAD, "the new picture, with room for his glow")
    ok(pictures[0].get_at((wide // 2, tall - 2)).a == 255 or pictures[0].get_at((wide // 2 - 20, tall - 2)).a == 255,
       "nothing see-through under his feet")
    ok(phase2.king_card(app).get_width() == 44 * art.KING_CARD_SCALE + 2 * art.GLOW_PAD, "and a story card with his sword")


def test_the_phase_2_throne_room_draws_the_new_king_with_the_same_rules():
    def fight(phase2_mode):
        app = game.App("Hero", seed=1, sound=False, throne=True, phase2_mode=phase2_mode)
        app.new_game()
        frames(app, 30)
        return app
    classic, new = fight(None), fight("phase2")
    old_king, new_king = classic.game.cave.king, new.game.cave.king
    ok(phase2.is_phase2(new.game) and not phase2.is_phase2(classic.game), "one of each game")
    ok((new_king.w, new_king.h) == (old_king.w, old_king.h) == (throne.KING_W, throne.KING_H), "the same hitbox")
    ok(new_king.max_health == old_king.max_health, "and the same health")
    new_king.angry = True
    frames(new, 5)                                        # the angry picture draws too
    new_king.flash = 0.2
    frames(new, 2)
    new.draw_story_picture("king", (400, 300))            # the story card: the new king in Phase 2,
    classic.draw_story_picture("king", (400, 300))        # the old one in Classic
