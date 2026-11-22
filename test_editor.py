"""
Tests for the cave editor: loading and saving, the checks, the editor's buttons,
Play it! and the "Can it be beaten?" robot.

Run them with:
    pixi run test-editor
Every test prints "ok". If something is broken you'll see which test and why.
Your real my_caves folder is never touched: the tests save into a temporary folder.
The game's own caves (the levels folder) aren't touched either: the tests save over copies.
"""

import os
import shutil
import sys
import tempfile
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")        # no window: the tests run invisibly
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import cave_files
import cave_solver
import caves
import castle
import rules

TEMP = tempfile.mkdtemp(prefix="my_caves_test_")
cave_files.MY_CAVES_FOLDER = TEMP

import editor   # noqa: E402  (after the temporary folder is set up)


def test(function):
    function()
    print("ok   ", function.__name__)
    return function


# ===========================================================================
# Loading and saving
# ===========================================================================

@test
def every_game_cave_loads_and_saves_the_same():
    for name, text in cave_files.game_caves():
        theme, rows, notes = cave_files.read_cave(text)
        assert rows == caves.level_lines(text), name
        assert theme == caves.level_theme(text), name
        assert notes == [], (name, notes)
        again = cave_files.read_cave(cave_files.cave_text(theme, rows))
        assert again == (theme, rows, []), name
        settings = cave_files.settings_of(text)                # "lava rises: yes" and the others are kept too
        assert cave_files.settings_of(cave_files.cave_text(theme, rows, settings)) == settings, name


@test
def the_game_cave_list_has_everything():
    found = cave_files.game_caves()
    assert len(found) == len(caves.CAVE_LEVELS) + len(castle.CASTLE_LEVELS) + len(caves.SHADOW_CAVES) + len(caves.SECRET_CAVES)
    names = [name for name, _ in found]
    assert "Castle level 1: The Gate and the Lava Moat" in names
    assert "Cave 2: The Vine Garden (moss)" in names
    assert not any("piece" in name.lower() for name in names), "the cave pieces are gone: every cave is a file"
    assert "Secret Mine: The Secret Mine (crystal)" in names
    assert dict(found)["Castle level 5: The Battlements"] == castle.CASTLE_LEVELS[4][1]
    levels = cave_files.game_levels()                      # the ones Save changes in the game: one file each
    assert len(levels) == len(caves.CAVE_LEVELS) + len(castle.CASTLE_LEVELS) + len(caves.SHADOW_CAVES) + len(caves.SECRET_CAVES)
    paths = {os.path.abspath(path) for _, path in levels}  # every cave file the game reads is in the list
    for folder in ("caves", "castle", "shadow", "secret"):
        for path, _ in caves.level_files(folder):
            assert os.path.abspath(path) in paths, path
    assert "Nightfall cave 1: The Whisper Hollow" in names
    assert all(cave_files.is_game_level(path) for _, path in levels)
    assert not cave_files.is_game_level(os.path.join(TEMP, "gem_cave.txt"))


@test
def saving_and_loading_a_cave():
    rows = cave_files.new_cave_rows()
    path = cave_files.save_cave("Lava Tower!", "lava", rows)
    assert path == os.path.join(TEMP, "lava_tower.txt")
    assert cave_files.load_cave(path) == ("lava", rows, [])
    assert ("lava tower", path) in cave_files.my_caves()
    with open(path) as f:
        assert f.read().startswith("theme: lava\n#####")


@test
def file_names_are_safe():
    assert cave_files.file_name("Lava Tower!") == "lava_tower.txt"
    assert cave_files.file_name("  ../../oops  ") == "oops.txt"
    assert cave_files.file_name("!!!") == "my_cave.txt"
    assert cave_files.nice_name("/x/y/lava_tower.txt") == "lava tower"


@test
def uneven_rows_get_filled_in():
    theme, rows, notes = cave_files.read_cave("theme: moss\n#####\n#S\n#####")
    assert theme == "moss" and rows == ["#####", "#S...", "#####"]
    assert notes and "filled them in" in notes[0]
    theme, rows, notes = cave_files.read_cave("theme: purple\n###")
    assert theme == "stone" and notes


@test
def no_theme_line_means_stone():
    assert cave_files.read_cave("###\n#S#\n###")[0] == "stone"


# ===========================================================================
# The checks
# ===========================================================================

def messages(rows, theme="moss"):
    return " | ".join(text for _, text in cave_files.check_cave(theme, rows))


@test
def a_new_cave_has_nothing_to_fix():
    assert cave_files.check_cave("moss", cave_files.new_cave_rows()) == []


@test
def missing_start_exit_and_diamond():
    rows = [row.replace("S", ".").replace("E", ".").replace("*", ".") for row in cave_files.new_cave_rows()]
    found = cave_files.check_cave("moss", rows)
    assert ("must", "No start yet! Put an S where the Hero climbs in.") in found
    assert "No exit door" in messages(rows) and "No diamond" in messages(rows)
    assert not cave_files.can_play("moss", rows)
    assert cave_files.can_play("moss", cave_files.new_cave_rows())


@test
def lava_belongs_in_the_floor():
    rows = cave_files.new_cave_rows()
    floor = len(rows) - 1
    good = rows[:floor] + [cave_files.put(rows[floor], 10, "~")]
    assert "Lava" not in messages(good)
    bad = list(rows)
    bad[5] = cave_files.put(bad[5], 10, "~")
    assert "Lava in the air (column 10)" in messages(bad)
    on_rock = list(rows)                                   # a pool set into the top of a rock block is fine
    on_rock[floor - 1] = cave_files.put(on_rock[floor - 1], 10, "~")
    assert "Lava" not in messages(on_rock)


@test
def lava_stacked_in_the_floor_is_a_deeper_pool():
    deep = ["##########",
            "#........#",
            "#S......E#",
            "##~##~~#~#",              # pools 1, 2 and 3 deep, with rock below and on their sides
            "#####~~#~#",
            "########~#",
            "##########"]
    assert "Lava" not in messages(deep), messages(deep)
    tower = ["##########",
             "#.....~..#",             # a stack of lava standing up in the air
             "#S....~.E#",
             "##########"]
    assert "Lava in the air (column 6)" in messages(tower), messages(tower)
    leaky = ["##########",
             "#........#",
             "#S......E#",
             "####~#####",
             "#...~....#",             # deep lava with air beside it would pour out
             "##########"]
    assert "Lava in the air (column 4)" in messages(leaky), messages(leaky)


@test
def squashed_monsters_and_start():
    rows = cave_files.new_cave_rows()
    rows[11] = cave_files.put(rows[11], 2, "#")             # rock right above the S
    rows[12] = cave_files.put(rows[12], 20, "z")
    rows[11] = cave_files.put(rows[11], 20, "#")
    found = messages(rows)
    assert "squashed under rock" in found
    assert "Zombie at column 20 is stuck in rock" in found


@test
def strange_letters():
    rows = cave_files.new_cave_rows()
    rows[5] = cave_files.put(rows[5], 5, "?")
    rows[5] = cave_files.put(rows[5], 6, "w")
    rows[5] = cave_files.put(rows[5], 7, "Q")
    found = messages(rows)
    assert "surprise monster" in found and "castle look" in found and "letters: Q" in found
    assert "castle look" not in messages(rows, "castle")


# ===========================================================================
# The editor itself (in an invisible window)
# ===========================================================================

ed = editor.Editor(sound=False)


def frame(*events):
    ed.step(1 / 60, list(events))


def middle_of(r, c):
    x, y = ed.on_screen(r, c)
    ts = editor.TILE * ed.zoom_level()
    return (int(x + ts / 2), int(y + ts / 2))


def click(r, c, button=1):
    pos = middle_of(r, c)
    frame(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button),
          pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=button))


def drag(a, b, button=1):
    frame(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=middle_of(*a), button=button),
          pygame.event.Event(pygame.MOUSEMOTION, pos=middle_of(*b), rel=(0, 0), buttons=(1, 0, 0)),
          pygame.event.Event(pygame.MOUSEBUTTONUP, pos=middle_of(*b), button=button))


def type_text(text):
    frame(*[pygame.event.Event(pygame.TEXTINPUT, text=letter) for letter in text])


def press(key):
    frame(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0))


def press_button(label):
    button = next(b for b in ed.buttons if b.label == label)
    pos = button.rect.center
    frame(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1),
          pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))


@test
def the_palette_has_every_block_drawn_by_the_game():
    frame()
    for letter in ed.palette_letters():
        assert letter in editor.BLOCKS, letter
        assert ed.icons[letter].get_width() > 10, letter
    assert set("zkcx") <= set(ed.palette_letters())
    assert "i" not in ed.palette_letters()                  # castle things only in the castle look


def see_through_pixels(picture):
    """How many pixels of a picture you could see through. (255 is solid. Shrinking a
    picture can leave it at 252 or so, which you can't see, so that still counts as solid.)"""
    w, h = picture.get_size()
    return sum(1 for x in range(w) for y in range(h) if picture.get_at((x, y)).a < 250)


def drawn_share(box):
    """How much of a box on the screen has something drawn in it: 0 = nothing, 1 = all of it."""
    w, h = box.get_size()
    drawn = sum(1 for x in range(w) for y in range(h) if tuple(box.get_at((x, y)))[:3] != editor.ICON_BG)
    return drawn / (w * h)


@test
def every_block_in_the_palette_has_a_picture():
    # On a Mac the chest, the ledges and the monsters once showed as empty boxes, because their
    # pictures came out see-through. (The tests' invisible window can't do that, so to check a
    # real Mac window too, run:  SDL_VIDEODRIVER=cocoa pixi run test-editor)
    for theme in cave_files.THEMES:
        ed.set_cave(theme, cave_files.new_cave_rows())
        frame()
        assert len(ed.palette_spots) == len(ed.palette_letters()), theme
        for letter, spot in ed.palette_spots:
            assert see_through_pixels(ed.icons[letter]) == 0, (theme, letter, "its picture has see-through holes")
            assert see_through_pixels(ed.icons[letter + "big"]) == 0, (theme, letter, "the mouse picture has holes")
            box = ed.screen.subsurface(spot.inflate(-8, -8))     # inside the box's border
            assert drawn_share(box) > 0.6, (theme, letter, "its box in the palette looks empty")
    ed.new_cave()


SHADOWFALL_CAVE = """theme: moss
name: The Lantern Road
stone: Dawnstone
land: the Weepingwold
needs: climb, pound
dark: yes
about: a test cave with every Shadowfall letter
############
#..........#
#..C.n.<.>.#
.S.......*E#
############
"""


@test
def the_editor_keeps_shadowfall_settings_when_it_saves():
    path = os.path.join(TEMP, "lantern_road.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(SHADOWFALL_CAVE)
    ed.open_file(path)
    ed.set_tile(1, 2, "C")                       # change something, then save
    ed.write(path)
    with open(path, encoding="utf-8") as f:
        saved = f.read()
    for line in ("stone: Dawnstone", "land: the Weepingwold", "needs: climb, pound", "dark: yes",
                 "name: The Lantern Road"):
        assert line in saved, (line, saved)
    assert "#.C........#" in saved and "#..C.n.<.>.#" in saved, saved
    ed.new_cave()


@test
def shadowfall_letters_are_in_the_palette_with_pictures():
    letters = "".join(group for _, group in editor.PALETTE)
    for letter in "C<>n":
        assert letter in letters and letter in editor.BLOCKS, letter
        assert letter in cave_files.EVERY_LETTER, letter
    assert "don't know" not in messages(["#####", "#.S.#", "#C<n#", "#####"])


@test
def the_checklist_knows_the_needs_line():
    rows = ["#######", "#.....#", "#.S.n*E", "#######"]
    tips = " | ".join(text for _, text in cave_files.check_cave("moss", rows, ["needs: climb, fly"]))
    assert "the power fly" in tips and "no flare" in tips, tips
    assert cave_files.check_cave("moss", rows, ["needs: flare, climb"]) == []
    assert "dark: should say yes or no" in " ".join(t for _, t in cave_files.check_cave("moss", rows, ["dark: maybe"]))
    assert cave_files.needs_of("needs: Climb, pound\n#") == {"climb", "pound"}
    assert cave_files.needs_of("needs: none\n#") == set()
    assert cave_files.needs_of("theme: moss\n#") is None


@test
def painting_rubbing_out_and_undo():
    ed.new_cave()
    type_text("B")
    assert ed.selected == "B"
    click(5, 10)
    assert ed.rows[5][10] == "B"
    click(5, 10, button=3)
    assert ed.rows[5][10] == "."
    press_button("Undo")
    assert ed.rows[5][10] == "B"
    press_button("Redo")
    assert ed.rows[5][10] == "."
    drag((6, 3), (6, 12))                                  # a fast drag leaves no gaps
    assert "".join(ed.rows[6][3:13]) == "B" * 10


@test
def only_one_start():
    ed.new_cave()
    type_text("S")
    click(12, 20)
    assert ed.rows[12][20] == "S"
    assert sum(row.count("S") for row in ed.rows) == 1
    assert abs(ed.cave.you.x - 20.1) < 0.01               # the Hero moved to the new start


@test
def monsters_show_up_where_you_paint_them():
    ed.new_cave()
    type_text("k")
    click(12, 15)
    assert [m.spawn for m in ed.cave.monsters] == [(12, 15)]
    click(12, 15, button=3)
    assert ed.cave.monsters == []


@test
def moving_platforms_follow_the_path_you_paint_and_rub_out():
    ed.new_cave()
    type_text("U")
    for r in (5, 6, 7, 8):                                 # a column of U's: one platform, riding up and down it
        click(r, 15)
    platforms = ed.cave.platforms
    assert len(platforms) == 1 and (platforms[0].low, platforms[0].high) == (5, 8)
    for r in (5, 6, 7, 8):
        click(r, 15, button=3)                             # rub it out: the platform is gone
    assert ed.cave.platforms == []
    type_text("P")
    drag((10, 4), (10, 12))                                # a row of P's: one platform, sliding along it
    assert len(ed.cave.platforms) == 1 and (ed.cave.platforms[0].low, ed.cave.platforms[0].high) == (4, 11)


@test
def the_editor_shows_where_a_platform_turns_around():
    ed.new_cave()
    type_text("P")
    drag((10, 4), (10, 9))                                 # P's from column 4 to 9
    ed.hover = None                                        # (no yellow mouse box on top)
    ed.draw()
    x0, y0 = ed.on_screen(10, 4)
    x1, _ = ed.on_screen(10, 10)
    ts = x1 - ed.on_screen(10, 9)[0]
    mid = int(y0 + ts * 0.225)
    near = lambda x, y: ed.screen.get_at((int(x), int(y)))[:3]
    assert near(x0 + ts * 0.07, mid) == editor.TURN_COLOR, "a red turn-around bar at the left end of the P's"
    assert near(x1 - ts * 0.07, mid) == editor.TURN_COLOR, "and at the right end"
    assert near((x0 + x1) / 2, mid) == editor.TRACK_COLOR, "and the yellow track between them"
    assert near(x1 + ts * 2, mid) != editor.TRACK_COLOR, "no track past the end"


@test
def the_checklist_warns_about_broken_platform_tracks():
    def tips(drawing):
        return " | ".join(text for _, text in cave_files.check_platforms(drawing))
    good = ["##########", "#........#", "#........#", "#...PPPP.#", "#.....U..#", "#.....U..#", "#.S......#", "##########"]
    assert tips(good) == "", tips(good)
    assert "can't move" in tips(["#####", "#.PP#", "#####"]), "2 P's can't slide anywhere"
    assert "can't move" in tips(["#####", "#.U.#", "#####"]), "1 row of U's can't go up or down"
    assert "squashes you" in tips(["#####", "#...#", "#.U.#", "#.U.#", "#...#", "#####"]), \
        "rock right above an up-down track: no room to ride it"
    assert "neat column" in tips(["######", "#....#", "#....#", "#.UU.#", "#.U..#", "#.U..#", "######"]), \
        "U's that aren't a neat box break into 2 platforms"
    found = cave_files.check_cave("moss", ["#####", "#.S.#", "#.PP#", "#####"])
    assert any("can't move" in text for _, text in found), "...and the checklist shows it"


@test
def castle_monsters_are_shadow_monsters():
    ed.new_cave()
    type_text("z")
    click(12, 15)
    assert not ed.cave.monsters[0].info.shadow               # a cave look: a normal Zombie
    while ed.theme != "castle":
        ed.next_theme()
    assert [m.info.kind for m in ed.cave.monsters] == ["Shadow Zombie"]   # the castle look: a Shadow Zombie
    press_button("Play it!")
    assert ed.playing and [m.info.kind for m in ed.app.game.cave.monsters] == ["Shadow Zombie"]   # and in "Play it!" too
    press(pygame.K_ESCAPE)
    assert not ed.playing
    frame()


@test
def box_fills_a_rectangle():
    ed.new_cave()
    type_text("=")
    press_button("Box")
    drag((3, 5), (4, 9))
    press_button("Box")
    assert all(ed.rows[r][c] == "=" for r in (3, 4) for c in range(5, 10))
    assert ed.rows[5][5] == "."


@test
def look_height_and_width():
    ed.new_cave()
    press_button("Look")                                   # moss comes just before castle
    assert ed.theme == "castle" and "i" in ed.palette_letters()
    press_button("Look")
    assert ed.theme == "stone" and "i" not in ed.palette_letters()
    before = ed.text_rows()
    press_button("Height")
    assert ed.height == 20 and ed.text_rows()[-1] == before[-1]
    press_button("Height")
    assert ed.text_rows() == before
    press_button("Wider")
    assert ed.width == len(before[0]) + editor.WIDER_BY
    assert all(len(row) == ed.width for row in ed.rows)
    press_button("Narrower")
    assert ed.text_rows() == before
    press_button("Zoom")
    frame()


@test
def save_with_a_name_and_open_it_again():
    ed.new_cave()
    type_text("$")
    click(8, 8)
    press_button("Save")
    assert ed.modal["kind"] == "name"
    type_text("Gem Cave")
    press(pygame.K_RETURN)
    path = os.path.join(TEMP, "gem_cave.txt")
    assert os.path.exists(path) and ed.path == path and not ed.unsaved()
    with open(path) as f:
        assert f.read() == cave_files.cave_text(ed.theme, ed.text_rows())
    saved = ed.text_rows()
    ed.new_cave()
    ed.open_file(path)
    assert ed.text_rows() == saved and ed.name == "gem cave"
    click(9, 9)                                            # change it and Save: no questions this time
    press_button("Save")
    assert ed.modal is None and cave_files.load_cave(path)[1] == ed.text_rows()


@test
def saving_over_another_cave_asks_first():
    ed.new_cave()
    press_button("Save")
    type_text("gem cave")
    press(pygame.K_RETURN)
    assert ed.modal["kind"] == "confirm"
    press(pygame.K_ESCAPE)                                 # No
    assert ed.modal is None and ed.path is None


@test
def open_list_loads_a_game_cave():
    ed.new_cave()
    press_button("Open")
    assert ed.modal["kind"] == "open"
    kind, name, value = next(item for item in ed.modal["items"] if item[0] == "level")
    ed.open_item(kind, name, value)
    assert ed.text_rows() == caves.level_lines(caves.CAVE_LEVELS[0])
    assert ed.path == caves.CAVE_LEVEL_FILES[0][0] and ed.name == "The Easy Moss Cave"
    press_button("Open")
    items = ed.modal["items"]
    assert not any(kind == "game" or "piece" in name.lower() for kind, name, _ in items), "no cave pieces in the list"
    opened = {os.path.abspath(value) for kind, _, value in items if kind == "level"}
    world = rules.Game("Hero", seed=1)                     # every cave the game plays is in the Open list
    played = set(world.cave_plan.values()) | set(world.secret_mines.values())
    for path, text in caves.CAVE_LEVEL_FILES + caves.SECRET_CAVE_FILES:
        if text in played or caves.without_diamond(text) in played:
            assert os.path.abspath(path) in opened, path
            played -= {text, caves.without_diamond(text)}
    assert not played, "a Mine plays a cave that isn't a file in the Open list"
    kind, name, value = next(item for item in items if item[1].startswith("Secret Mine"))
    ed.open_item(kind, name, value)
    assert ed.path == caves.SECRET_CAVE_FILES[0][0] and ed.name == "The Secret Mine"


@test
def saving_over_a_game_cave_asks_first_and_keeps_its_settings():
    real_folder = caves.LEVELS_FOLDER
    caves.LEVELS_FOLDER = os.path.join(TEMP, "levels")    # a copy of the game's caves, so the real ones stay safe
    try:
        os.makedirs(os.path.join(caves.LEVELS_FOLDER, "caves"))
        real = next(path for path, text in caves.CAVE_LEVEL_FILES if caves.level_setting(text, "lava rises") == "yes")
        path = shutil.copy(real, os.path.join(caves.LEVELS_FOLDER, "caves"))
        ed.open_file(path)
        assert ed.name == "The Lava Escape" and "lava rises: yes" in ed.settings
        click(3, 3)
        press_button("Save")
        assert ed.modal["kind"] == "confirm" and "in the game" in ed.modal["text"]
        press(pygame.K_ESCAPE)                             # No: nothing changes
        with open(path) as f, open(real) as g:
            assert f.read() == g.read()
        press_button("Save")
        press(pygame.K_RETURN)                             # Yes
        assert ed.modal is None and not ed.unsaved()
        with open(path) as f:
            text = f.read()
        assert caves.level_lines(text) == ed.text_rows()
        assert caves.level_setting(text, "lava rises") == "yes" and caves.level_setting(text, "name") == "The Lava Escape"
        assert caves.level_setting(text, "about")          # its notes are kept too
        click(4, 4)
        press_button("Save")                               # only asks once
        assert ed.modal is None and not ed.unsaved()
        press_button("Save as")                            # your own copy goes in my_caves, named after its file
        assert ed.modal["text"] == "The Lava Escape"
        ed.modal["text"] = ""
        type_text("my escape")
        press(pygame.K_RETURN)
        mine = os.path.join(TEMP, "my_escape.txt")
        assert ed.path == mine and ed.name == "my escape"
        assert caves.level_setting(open(mine).read(), "lava rises") == "yes"
        assert caves.level_setting(open(mine).read(), "name") is None
    finally:
        caves.LEVELS_FOLDER = real_folder


@test
def play_it_and_come_back():
    ed.new_cave()
    press_button("Play it!")
    assert ed.playing
    for _ in range(30):
        frame()
    assert ed.app.state == "cave" and ed.app.game.cave is not None
    press(pygame.K_ESCAPE)
    assert not ed.playing and ed.app.game is ed.world and ed.world.cave is ed.cave
    frame()


@test
def play_it_through_the_exit():
    ed.new_cave()
    press_button("Play it!")
    frame()
    ed.app.game.cave.result = "exit"                       # pretend the Hero walked through the door
    frame()
    assert not ed.playing and "EXIT" in ed.message


@test
def play_it_and_get_knocked_out():
    ed.new_cave()
    press_button("Play it!")
    frame()
    ed.app.game.player.health = 0
    frame()
    assert not ed.playing and "knocked out" in ed.message


@test
def play_it_needs_a_start():
    ed.new_cave()
    click(12, 2, button=3)                                 # rub out the S
    press_button("Play it!")
    assert not ed.playing and "No start" in ed.message


# ===========================================================================
# The robot
# ===========================================================================

LITTLE_CAVE = """theme: stone
################
#..............#
#..............#
#..............#
..............E#
..S......*.....#
################
"""

DIAMOND_UP_HIGH = """theme: stone
################
#........*.....#
#........#.....#
#........#.....#
#........#.....#
..S......#....E#
################
"""


@test
def the_robot_beats_an_easy_cave():
    result = cave_solver.check(LITTLE_CAVE)
    assert result["diamond"] and result["exit"] and result["trail"]
    assert cave_solver.say(result)[0].startswith("Yes!")


@test
def the_robot_says_when_the_diamond_is_too_high():
    result = cave_solver.check(DIAMOND_UP_HIGH, tries=4000)
    assert result["diamond"] is False and result["stuck_at"]
    assert "couldn't find a way to the diamond" in cave_solver.say(result)[0]


@test
def the_robot_button_in_the_editor():
    theme, rows, _ = cave_files.read_cave(LITTLE_CAVE)
    ed.set_cave(theme, rows)
    press_button("Can it be beaten?")
    assert ed.modal["kind"] == "robot"
    give_up = time.time() + 120
    while ed.robot and time.time() < give_up:
        frame()
        time.sleep(0.05)
    assert ed.modal["kind"] == "message", ed.modal
    assert ed.modal["lines"][0].startswith("Yes!"), ed.modal["lines"]
    assert ed.trail
    press(pygame.K_RETURN)
    assert ed.modal is None


print("All the cave editor tests passed!")
pygame.quit()
sys.exit(0)
