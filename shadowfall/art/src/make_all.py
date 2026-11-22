"""Rebuild every asset in shadowfall/art:  python shadowfall/art/src/make_all.py"""
import json
import os

import make_font
import make_hero
import make_king
import make_monsters
import make_tiles
from sfart import ART, HEX, NAMES, P, gloom_lut, px, save_png, surf


def palette():
    """palette.png (32x1, index order), palette.json (name -> hex) and gloom_lut.png (32x4: row =
    gloom stage, column = source index, pixel = the colour it becomes) for B3's shader."""
    s = surf(32, 1)
    for i, n in enumerate(NAMES):
        px(s, n, i, 0)
    save_png(s, "palette.png")
    lut = surf(32, 4)
    for st in range(4):
        for i, j in enumerate(gloom_lut(st)):
            px(lut, P[NAMES[j]], i, st)
    save_png(lut, "gloom_lut.png")
    with open(os.path.join(ART, "palette.json"), "w") as fh:
        json.dump({"names": NAMES, "hex": HEX}, fh, indent=1)
        fh.write("\n")


def main():
    palette()
    make_hero.main()
    make_king.main()
    make_monsters.main()
    make_tiles.main()
    make_font.main()


if __name__ == "__main__":
    main()
