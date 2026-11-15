"""
SMOKE TESTS: does the game start, play and quit without crashing?

They play a bit like a real player (pressing keys for a few hundred frames, going down
into a cave, opening the Craft menu and the help screen), and the game draws every
frame into an invisible window. They don't check much: they make sure nothing crashes.
(The name comes from electronics: switch it on, and check no smoke comes out!)
"""

import os
import subprocess
import sys
import textwrap

import pygame

import cave_files
import caves
import game
from conftest import GAME_FOLDER
from helpers import DT, frames, hold_keys, ok, press, start_game, walk_into_a_mine

WALKING = [pygame.K_RIGHT, pygame.K_DOWN, pygame.K_LEFT, pygame.K_UP, pygame.K_d, pygame.K_s, pygame.K_a, pygame.K_w]


def answer_whatever_is_open(app):
    """A story card, a fight, a LEVEL UP! card...? Press the key that gets past it."""
    if app.state == "battle":
        press(app, pygame.K_a)                       # attack!
        press(app, pygame.K_SPACE)                   # and carry on when the fight is over
    elif app.state == "levelup":
        press(app, pygame.K_RETURN)                  # pick a power
    elif app.state in ("story", "help", "sunfang", "forge"):
        press(app, pygame.K_SPACE)
    elif app.state == "craft":
        press(app, pygame.K_ESCAPE)


def test_the_game_starts_plays_and_quits(monkeypatch):
    app = game.App("", seed=3, sound=False)
    frames(app, 30)
    ok(app.state == "title" and app.running, "the game starts on the title screen")

    # Type a name, then press ENTER
    for _ in range(12):
        press(app, pygame.K_BACKSPACE)
    for letter in "Knight":
        app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=letter))
    press(app, pygame.K_RETURN)
    ok(app.game.player.name == "Knight", "the name you typed is your hero's name")

    # The story cards (the intro), then the world map
    for _ in range(40):
        if app.state == "play":
            break
        press(app, pygame.K_SPACE)
        frames(app, 5)
    ok(app.state == "play", "after the story cards, you're on the world map (not %r)" % app.state)

    # Walk around for a few hundred frames: fights and level-ups can happen, that's fine
    for i in range(400):
        if i % 8 == 0:
            if app.state == "play":
                press(app, WALKING[(i // 8) % len(WALKING)])
            else:
                answer_whatever_is_open(app)
        frames(app)
    answer_whatever_is_open(app)
    ok(app.running, "the game is still running after walking around")

    # The Craft menu and the help screen on the world map
    app.game.monsters = []                       # no more fights, please
    if app.state != "play":
        answer_whatever_is_open(app)
    press(app, pygame.K_c)
    ok(app.state == "craft", "C opens the Craft menu")
    for key in (pygame.K_DOWN, pygame.K_DOWN, pygame.K_RETURN, pygame.K_UP, pygame.K_RETURN):
        press(app, key)
    answer_whatever_is_open(app)                  # (the Sword row opens the forge)
    frames(app, 10)
    for _ in range(50):
        if app.state == "play":
            break
        answer_whatever_is_open(app)
        frames(app, 10)
    press(app, pygame.K_h)
    ok(app.state == "help", "H opens the help screen")
    press(app, pygame.K_SPACE)
    ok(app.state == "play", "any key closes the help screen")

    # Down into a cave: run, jump and climb for a few hundred frames
    held = hold_keys(monkeypatch)
    cave = walk_into_a_mine(app)
    ok(app.state == "cave" and cave is not None, "walking into a Mine takes you into its cave")
    first_x = cave.you.x
    for i in range(300):
        held.clear()
        if (i // 60) % 2 == 0:
            held.add(pygame.K_RIGHT)
        elif cave.you.x > first_x + 1:          # back left, but not out through the way in
            held.add(pygame.K_LEFT)
        if i % 30 < 12:
            held.add(pygame.K_SPACE)             # jump (held down = higher)
        if i % 50 == 0:
            held.add(pygame.K_r)                 # swing your pickaxe or sword
        frames(app)
    held.clear()
    ok(app.running and app.game.cave is cave, "still running around in the cave")
    press(app, pygame.K_c)
    ok(app.state == "craft", "C opens the Craft menu in the cave too")
    press(app, pygame.K_DOWN)
    press(app, pygame.K_ESCAPE)
    ok(app.state == "cave", "Esc goes back to the cave")
    frames(app, 30)

    # Close the window
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    app.step(DT)
    ok(not app.running, "closing the window stops the game")


def test_the_nightfall_shortcut_starts_in_nightfall_hollow():
    """python game.py --nightfall: a play-test shortcut, just through the Portal."""
    app = game.App("Hero", seed=3, sound=False, nightfall=True)
    start_game(app)
    frames(app, 60)
    world = app.game
    ok(world.world == 2 and world.player.pos == world.start, "you start in Nightfall Hollow, by the Portal")
    ok(app.state == "play" and not world.cave, "on the map, ready to explore")


def test_the_castle_shortcut_starts_next_to_the_castle():
    """python game.py --castle: a play-test shortcut, right next to the Shadow King's castle."""
    app = game.App("Hero", seed=3, sound=False, castle=True)
    start_game(app)
    frames(app, 60)
    world = app.game
    ok(world.world == 2, "you start in Nightfall Hollow")
    ok(min(abs(world.player.pos[0] - world.castle[0]) + abs(world.player.pos[1] - world.castle[1]), 99) == 1,
       "right next to the castle")


def test_the_throne_shortcut_starts_the_boss_fight():
    """python game.py --throne: a play-test shortcut, straight to the fight with the Shadow King."""
    app = game.App("Hero", seed=3, sound=False, throne=True)
    start_game(app)
    frames(app, 60)
    world = app.game
    ok(world.cave and world.cave.is_throne_room and world.player.sunfang and not world.won,
       "you start in the throne room, with Sunfang")


# ===========================================================================
# Starting them the real way: python game.py and python editor.py
# ===========================================================================

def run_for_a_while(script, *arguments, tmp_path):
    """Start game.py or editor.py the way `pixi run game` does, press a few keys, then close the window.
    `script` is a little program that pretends to be you at the keyboard."""
    driver = tmp_path / "pretend_player.py"
    driver.write_text(textwrap.dedent(script))
    result = subprocess.run([sys.executable, str(driver), *arguments], cwd=GAME_FOLDER, capture_output=True,
                            text=True, timeout=120,
                            env={**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
    return result


def frames_played(result):
    """How many frames it ran before it closed (the pretend player prints it at the end)."""
    lines = [line for line in result.stdout.splitlines() if line.startswith("frames:")]
    return int(lines[-1].split(":")[1]) if lines else 0


PRETEND_PLAYER = """
    import sys
    import pygame
    sys.path.insert(0, ".")
    import {module}

    frame = 0
    real_step = {module}.{app}.step

    def step(self, *rest):
        # every frame: maybe press a key, then let the game do its frame
        global frame
        frame += 1
        for when, event in KEYS:
            if frame == when:
                pygame.event.post(event)
        real_step(self, *rest)

    def key(k):
        return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)

    KEYS = {keys}
    {module}.{app}.step = step
    sys.argv = [sys.argv[0]] + sys.argv[1:]
    {module}.main()
    print("frames:", frame)
"""


def test_python_game_py_starts_and_quits(tmp_path):
    keys = """[(10, key(pygame.K_RETURN))] + [(20 + 5 * i, key(pygame.K_SPACE)) for i in range(20)] + [
              (130 + 4 * i, key([pygame.K_RIGHT, pygame.K_DOWN][i % 2])) for i in range(20)] + [
              (220, key(pygame.K_c)), (230, key(pygame.K_ESCAPE)), (240, pygame.event.Event(pygame.QUIT))]"""
    result = run_for_a_while(PRETEND_PLAYER.format(module="game", app="App", keys=keys), "--mute", "--seed", "3",
                             tmp_path=tmp_path)
    ok(result.returncode == 0, "python game.py crashed:\n" + result.stdout[-2000:] + result.stderr[-3000:])
    ok(240 <= frames_played(result) <= 242, "the game ran until the window closed at frame 240: " + result.stdout[-300:])


def test_python_game_py_throne_starts_and_quits(tmp_path):
    keys = """[(10, key(pygame.K_RETURN)), (20, key(pygame.K_1))] + [
              (40 + 4 * i, key(pygame.K_r)) for i in range(20)] + [(200, pygame.event.Event(pygame.QUIT))]"""
    result = run_for_a_while(PRETEND_PLAYER.format(module="game", app="App", keys=keys), "--mute", "--throne",
                             tmp_path=tmp_path)
    ok(result.returncode == 0, "python game.py --throne crashed:\n" + result.stdout[-2000:] + result.stderr[-3000:])
    ok(200 <= frames_played(result) <= 202, "the fight ran until the window closed at frame 200: " + result.stdout[-300:])


def test_python_editor_py_starts_plays_and_quits(tmp_path):
    first = caves.CAVE_LEVELS[0]
    cave_file = tmp_path / "a_game_cave.txt"
    cave_file.write_text(cave_files.cave_text(caves.level_theme(first), caves.level_lines(first)))
    keys = """[(10, key(pygame.K_RIGHT)), (20, key(pygame.K_b)), (30, key(pygame.K_F5))] + [
              (120, key(pygame.K_ESCAPE)), (150, pygame.event.Event(pygame.QUIT))]"""
    result = run_for_a_while(PRETEND_PLAYER.format(module="editor", app="Editor", keys=keys), str(cave_file), "--quiet",
                             tmp_path=tmp_path)
    ok(result.returncode == 0, "python editor.py crashed:\n" + result.stdout[-2000:] + result.stderr[-3000:])
    ok(150 <= frames_played(result) <= 152, "the editor ran until the window closed at frame 150: " + result.stdout[-300:])
