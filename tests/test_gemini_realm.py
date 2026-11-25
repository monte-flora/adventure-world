"""gemini-realm (shadowfall/tools/gemini_realm.py): one realm screen as one Gemini painting. Godot
(the layout and the WebP), osascript, pbcopy and open are faked: no browser or Godot runs here."""

import json
import os
import sys
from types import SimpleNamespace

from conftest import GAME_FOLDER
from helpers import ok

sys.path.insert(0, os.path.join(GAME_FOLDER, "shadowfall", "tools"))
import gemini_realm as gr  # noqa: E402

INFO = {"screen": "B3", "land": "emberhold", "land_name": "Emberhold",
        "props": {"cottage_a": 3, "cottage_b": 2, "campfire": 1, "mirefen_mire_crag": 2, "lamppost": 4},
        "gates": {"O": 5}, "roles": {"grass": 300, "dirt_road": 60, "gate": 5},
        "legend": [["grass", [98, 150, 72]], ["dirt_road", [196, 154, 96]], ["ice", [204, 232, 246]],
                   ["gate", [230, 0, 200]]]}


def make_levels(tmp_path):
    lv = tmp_path / "levels"
    (lv / "realm").mkdir(parents=True)
    (lv / "realm" / "1_emberhold.txt").write_text(
        "land: emberhold\nat: 17 0\nvillage: Emberwick 27 50\nvillage: Far Place 2 2\npainted_screen: B3\nGG\n")
    return str(lv)


def fake_run(calls):
    """A fake Godot: realm_layout writes the map and its notes, polish_import the WebP."""
    def run_cmd(cmd, **kw):
        calls.append(cmd)
        if "res://tools/realm_layout.tscn" in cmd:
            out = cmd[-1]
            open(os.path.join(out, "layout.png"), "wb").write(b"png")
            json.dump(INFO, open(os.path.join(out, "layout.json"), "w"))
        if "res://tools/polish_import.gd" in cmd:
            open(cmd[cmd.index("--") + 2], "wb").write(b"webp")
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    return run_cmd


def test_export_writes_the_map_legend_and_words(tmp_path):
    lv = make_levels(tmp_path)
    calls = []
    out = gr.export("b3", lv, fake_run(calls))
    ok(out == os.path.join(lv, "polish", "realm_B3"), "levels/polish/realm_B3")
    ok(calls[0][-2:] == ["B3", out], "Godot draws the B3 layout into the folder")
    for f in ("layout.png", "legend.png", "prompt.txt", "README.txt"):
        ok(os.path.exists(os.path.join(out, f)), "%s is made" % f)
    words = open(os.path.join(out, "prompt.txt")).read()
    ok("Emberwick" in words and "Far Place" not in words, "names the village on this screen only")
    for want in ("timber cottages", "campfire", "lampposts", "crags", "magenta", "tan = a worn dirt road",
                 "No characters", "2752x1536", "not isometric", "style picture"):
        ok(want in words, "the words say %r" % want)
    ok("ice" not in words and "mirefen" not in words, "only the ground there; crag kinds in plain words")
    open(os.path.join(out, "prompt.txt"), "w").write("my words\n")
    gr.export("B3", lv, fake_run(calls))
    ok(open(os.path.join(out, "prompt.txt")).read() == "my words\n", "your prompt.txt stays")


def test_import_makes_the_screen_sized_webp(tmp_path, monkeypatch):
    lv = make_levels(tmp_path)
    monkeypatch.setattr(gr.polish.shutil, "which", lambda g: "/bin/godot")
    out = gr.folder("B3", lv)
    os.makedirs(out)
    good, why = gr.import_painting("B3", lv, run_cmd=fake_run([]))
    ok(not good and "No picture" in why, "nothing to import yet")
    open(os.path.join(out, "Gemini_1.png"), "wb").write(b"img")
    calls = []
    good, why = gr.import_painting("B3", lv, run_cmd=fake_run(calls))
    ok(good, why)
    cmd = calls[0]
    ok(cmd[cmd.index("--") + 3:cmd.index("--") + 5] == ["960", "544"], "the screen's own size, 1 px a game px")
    ok(os.path.exists(os.path.join(out, "painted.webp")), "painted.webp is made")
    ok(not os.path.exists(os.path.join(out, "Gemini_1.png")), "the dropped picture is cleared away")


def test_run_pastes_map_then_style_then_words(tmp_path):
    lv = make_levels(tmp_path)
    style = tmp_path / "mockup.jpg"
    style.write_bytes(b"jpg")
    d = tmp_path / "dl"
    d.mkdir()
    calls = []

    def wait(folder, before, since):
        p = d / "Gemini_x.png"
        p.write_bytes(b"img")
        return str(p)

    got = []
    rc = gr.run("B3", str(style), str(d), lv, fake_run(calls), wait, ask=lambda: "",
                importer=lambda s, levels: got.append(s) or (True, "ok"))
    ok(rc == 0 and got == ["B3"], "imported B3")
    clip = [c for c in calls if c[0] in ("osascript", "pbcopy")]
    ok("layout.png" in clip[0][2] and "PNGf" in clip[0][2], "first the map, as a picture")
    ok("mockup.jpg" in clip[1][2] and "JPEG" in clip[1][2], "then the style picture")
    ok(clip[2] == ["pbcopy"], "then the words")
    ok(os.path.exists(os.path.join(gr.folder("B3", lv), "from_gemini.png")), "the download moved in")
    ok(["open", gr.gn.GEMINI_URL] in calls, "Gemini opened (and nothing else done on the site)")
