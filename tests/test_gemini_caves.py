"""gemini-caves (shadowfall/tools/gemini_caves.py): walks the caves with no painting, puts the map on the
clipboard as a picture, then the words, grabs the settled download into levels/polish/<cave>/ and runs
polish import. osascript, pbcopy, open and polish.py are faked: no browser or Godot ever runs here."""

import os
import sys
from types import SimpleNamespace

from conftest import GAME_FOLDER
from helpers import ok

sys.path.insert(0, os.path.join(GAME_FOLDER, "shadowfall", "tools"))
import gemini_caves as gc  # noqa: E402
import polish  # noqa: E402


def make_levels(tmp_path):
    lv = tmp_path / "levels"
    for sub, names in (("castle", ["1_gate"]), ("caves", ["02_b", "01_a"]), ("shadow", ["1_dark"]),
                       ("stone", ["1_vigil"]), ("secret", ["1_mine"]), ("world", ["01_home"])):
        (lv / sub).mkdir(parents=True)
        for n in names:
            (lv / sub / (n + ".txt")).write_text("theme: stone\n#.SE#\n")
    (lv / "polish").mkdir()
    return str(lv)


def fake_run(calls):
    """Records every command; a fake polish export makes the map and words, a fake import the painting."""
    def run_cmd(cmd, **kw):
        calls.append(cmd)
        out = os.path.dirname(cmd[-1]) if gc.THRONE in cmd[-1] else \
            gc.polish_dir(os.path.basename(cmd[-1])[:-4], os.path.dirname(os.path.dirname(cmd[-1])))
        if cmd[1:3] == [gc.POLISH, "import"]:
            open(os.path.join(out, "painted.webp"), "wb").write(b"webp")
        if cmd[1:3] == [gc.POLISH, "export"]:
            os.makedirs(out, exist_ok=True)
            open(os.path.join(out, "layout.png"), "wb").write(b"png")
            open(os.path.join(out, "prompt.txt"), "w").write("paint " + os.path.basename(out) + "\n")
        return SimpleNamespace(returncode=0)
    return run_cmd


def test_order_and_done(tmp_path):
    lv = make_levels(tmp_path)
    ok(gc.names(lv) == ["01_a", "02_b", "1_vigil", "1_mine", "1_dark", "1_gate"],
       "caves, stone, secret, shadow, castle; world maps are not caves (%s)" % gc.names(lv))
    os.makedirs(gc.polish_dir("01_a", lv))
    open(os.path.join(gc.polish_dir("01_a", lv), "painted.webp"), "wb").write(b"x")
    ok(gc.todo(lv)[0] == "02_b", "a painted cave is skipped")
    ok(gc.find("02", lv) == "02_b" and gc.find("1_", lv) is None, "a name by its start, if only one fits")


def test_export_keeps_your_prompt(tmp_path):
    lv = make_levels(tmp_path)
    path = os.path.join(lv, "caves", "01_a.txt")
    out = gc.polish_dir("01_a", lv)
    os.makedirs(out)
    open(os.path.join(out, "prompt.txt"), "w").write("my own words\n")
    calls = []
    gc.export("01_a", path, lv, fake_run(calls))
    ok(len(calls) == 1 and os.path.exists(os.path.join(out, "layout.png")), "no map yet: exported")
    ok(open(os.path.join(out, "prompt.txt")).read() == "my own words\n", "your prompt.txt stays")
    gc.export("01_a", path, lv, fake_run(calls))
    ok(len(calls) == 1, "map and words there: no export")


def test_run_loop(tmp_path, capsys):
    lv = make_levels(tmp_path)
    for n in ("02_b", "1_vigil", "1_mine", "1_dark"):          # leave 01_a and the castle to paint
        os.makedirs(gc.polish_dir(n, lv))
        open(os.path.join(gc.polish_dir(n, lv), "painted.webp"), "wb").write(b"x")
    d = tmp_path / "dl"
    d.mkdir()
    calls = []
    pics = iter(range(9))

    def wait(folder, before, since):
        p = d / ("Gemini_%d.PNG" % next(pics))
        p.write_bytes(b"img")
        return str(p)

    answers = iter(["", "n"])
    ok(gc.run(downloads=str(d), levels=lv, run_cmd=fake_run(calls), wait=wait, ask=lambda: next(answers)) == 0, "runs")
    kinds = [c[0] if c[0] != sys.executable else c[2] for c in calls]
    ok(kinds == ["export", "osascript", "open", "pbcopy", "import", "export", "osascript"], kinds)
    ok("«class PNGf»" in calls[1][2] and gc.polish_dir("01_a", lv) in calls[1][2], "the map, as a picture")
    ok(calls[2] == ["open", gc.gn.GEMINI_URL], "only the Gemini page, once")
    ok(os.listdir(d) == [] and os.path.exists(os.path.join(gc.polish_dir("01_a", lv), "from_gemini.png")),
       "the download moved into the cave's folder")
    ok(calls[4][-1] == os.path.join(lv, "caves", "01_a.txt"), "imported for its cave file")
    ok("1 still to paint" in capsys.readouterr().out, "the castle was skipped")


def test_redo(tmp_path, capsys):
    lv = make_levels(tmp_path)
    for n in gc.names(lv):
        os.makedirs(gc.polish_dir(n, lv))
        open(os.path.join(gc.polish_dir(n, lv), "painted.webp"), "wb").write(b"x")
    ok(gc.main(["--redo", "1_gate", "more banners"], levels=lv) == 0, "redo saved")
    ok(gc.todo(lv) == ["1_gate"], "only the redo is left")
    gc.main(["--list"], levels=lv)
    ok("redo     1_gate  (more banners)" in capsys.readouterr().out, "--list shows it")
    d = tmp_path / "dl"
    d.mkdir()
    calls = []
    p = d / "x.webp"
    p.write_bytes(b"img")
    gc.run(downloads=str(d), levels=lv, run_cmd=fake_run(calls), wait=lambda *a: str(p), ask=lambda: "")
    clip = [c for c in calls if c[0] == "pbcopy"]
    ok(len(clip) == 1, "one cave copied")
    ok(gc.clip_text("1_gate", lv, "more banners").endswith("Fix from last time: more banners\n"), "fix added")
    ok(gc.gn.redo_notes(os.path.join(lv, "polish")) == {}, "crossed off after import")
    ok("All 6 caves painted." in capsys.readouterr().out, "all done line")


def test_every_real_cave_gets_a_fitting_prompt():
    sys.path.insert(0, str(GAME_FOLDER))
    import cave_files
    for name, path in gc.caves():
        theme, rows, _ = cave_files.load_cave(path)
        text = polish.prompt(theme, cave_files.load_settings(path))
        ok(theme in polish.SCENE, "%s: a known look (%s)" % (name, theme))
        ok("the Umbral Reach" in text if "/shadow/" in path or "/castle/" in path else True, name + ": Umbral Reach")
        ok("Nightfall" in text if "/shadow/" in path else True, name + ": Nightfall mood")
        ok("Shadow King's black castle" in text if "/castle/" in path else True, name + ": the Shadow King's castle")
    ok(len(gc.caves()) >= 33, "every cave folder walked (%d)" % len(gc.caves()))


def test_the_throne_room_comes_last_and_keeps_its_words(tmp_path):
    lv = make_levels(tmp_path)
    t = tmp_path / "levels" / "polish" / gc.THRONE
    t.mkdir()
    (t / (gc.THRONE + ".txt")).write_text("theme: castle\n#..#\n")
    (t / "prompt.txt").write_text("the throne hall\n")
    ok(gc.names(lv)[-1] == gc.THRONE, "after the castle")
    calls = []
    gc.export(gc.THRONE, str(t / (gc.THRONE + ".txt")), lv, fake_run(calls))
    ok(len(calls) == 1 and (t / "layout.png").exists(), "its map is made in its own folder")
    ok((t / "prompt.txt").read_text() == "the throne hall\n", "its own words stay")


def test_the_real_throne_room_map():
    sys.path.insert(0, str(GAME_FOLDER))
    import cave_files
    path = dict(gc.caves())[gc.THRONE]
    theme, rows, _ = cave_files.load_cave(path)
    ok(theme == "castle" and len(rows) == 17 and all(len(r) == 30 for r in rows), "30 x 17 blocks: the 960x540 hall")
    words = open(os.path.join(os.path.dirname(path), "prompt.txt")).read()
    ok("Shadow King" in words and "throne" in words and "2752x1536" in words, "the throne hall's own words")
