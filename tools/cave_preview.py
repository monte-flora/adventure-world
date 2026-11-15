"""Save a picture (PNG) of whole caves, with the game's real art and no window.

    python tools/cave_preview.py                          the 5 far caves (13-17) into docs/new-caves/
    python tools/cave_preview.py levels/caves/06*.txt     any caves you name
    python tools/cave_preview.py --out somewhere --scale 1 levels/caves/*.txt

Each picture is named like its cave file (13_the_frozen_falls.png)."""
import glob
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("ADVENTURE_SETTINGS_FILE", os.path.join(tempfile.mkdtemp(), "settings.json"))   # never the real ones
os.environ.setdefault("ADVENTURE_SAVE_FILE", os.path.join(tempfile.mkdtemp(), "save.json"))
GAME_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GAME_FOLDER)

import pygame   # noqa: E402
import caves    # noqa: E402
import game     # noqa: E402

NEW_CAVES = ("13", "14", "15", "16", "17")


def draw_cave_picture(app, text, scale):
    """The whole cave as one picture: traps down and platforms a bit along, like in the editor."""
    cave = caves.Cave(app.game, (0, 0), text)
    cave.clock = caves.TRAP_DOWN * 0.6
    app.game.cave = cave
    app.build_cave_tiles(cave)
    app.motes = []
    picture = pygame.Surface((cave.cols * game.TILE, cave.rows * game.TILE))
    view = game.VIEW_W, game.VIEW_H
    game.VIEW_W, game.VIEW_H = picture.get_size()      # draw_cave only draws what fits in the view
    app.cam = (0, 0)
    try:
        app.draw_cave(picture)
    finally:
        game.VIEW_W, game.VIEW_H = view
    if scale != 1:
        size = int(picture.get_width() * scale), int(picture.get_height() * scale)
        picture = pygame.transform.smoothscale(picture, size)
    return picture


def main(args):
    out, scale, paths = os.path.join(GAME_FOLDER, "docs", "new-caves"), 0.5, []
    while args:
        arg = args.pop(0)
        if arg == "--out":
            out = args.pop(0)
        elif arg == "--scale":
            scale = float(args.pop(0))
        else:
            paths.append(arg)
    if not paths:
        folder = os.path.join(GAME_FOLDER, "levels", "caves")
        paths = sorted(p for p in glob.glob(os.path.join(folder, "*.txt")) if os.path.basename(p)[:2] in NEW_CAVES)
    os.makedirs(out, exist_ok=True)
    app = game.App("Hero", seed=1, sound=False)
    app.allow_tips = False
    for path in paths:
        with open(path, encoding="utf-8") as cave_file:
            picture = draw_cave_picture(app, cave_file.read(), scale)
        name = os.path.splitext(os.path.basename(path))[0] + ".png"
        pygame.image.save(picture, os.path.join(out, name))
        print("saved", os.path.join(out, name), picture.get_size())


if __name__ == "__main__":
    main(sys.argv[1:])
