"""The prop editor (shadowfall/tools/realm_editor.py, `pixi run realm-editor`): a land file's props
round-trip, and placing, moving and deleting props changes only the `prop:` lines."""

import os
import sys

from conftest import GAME_FOLDER
from helpers import ok

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.join(GAME_FOLDER, "shadowfall", "tools"))
import realm_editor as re_  # noqa: E402

EMBERHOLD = os.path.join(GAME_FOLDER, "levels", "realm", "1_emberhold.txt")


def test_emberhold_props_round_trip():
    text = open(EMBERHOLD).read()
    props = re_.read_props(text)
    ok(len(props) > 20, "Emberhold has its props (%d)" % len(props))
    ok(re_.write_props(text, props) == text, "writing the same props back gives the same file")
    for name, _, _ in props:
        ok(re_.load_meta(name) is not None, "realm/props/%s.json exists" % name)


def test_place_move_delete_and_save(tmp_path):
    path = tmp_path / "land.txt"
    path.write_text("land: test\nat: 0 0\nhome: 1 1\nprop: oak 1 2\nGGGGG\nGHGGG\nGGGGG")
    ed = re_.RealmEditor(str(path))
    ed.zoom = 1.0
    ed.place((3 * 32 + 16, 2 * 32 + 16), "rocks")             # the middle of row 2, column 3
    ok(ed.props[-1] == ("rocks", 2, 3), "placed on the square: %s" % (ed.props[-1],))
    i = ed.prop_at((3 * 32 + 16, 2 * 32 + 8))
    ok(i == 1, "clicking the rocks finds them")
    ed.move(i, (4 * 32 + 16, int(1.5 * 32 + 16)))
    ok(ed.props[1] == ("rocks", 1.5, 4), "moved by half squares: %s" % (ed.props[1],))
    ed.delete(0)
    ed.save()
    text = path.read_text()
    ok(text == "land: test\nat: 0 0\nhome: 1 1\nprop: rocks 1.5 4\nGGGGG\nGHGGG\nGGGGG", "only prop lines changed:\n" + text)
    ok(re_.RealmEditor(str(path)).props == [("rocks", 1.5, 4)], "and it loads back")


def test_new_props_go_before_the_drawing(tmp_path):
    text = "land: x\nat: 0 0\nGG\nGG"
    out = re_.write_props(text, [("well", 0, 1)])
    ok(out == "land: x\nat: 0 0\nprop: well 0 1\nGG\nGG", out)
