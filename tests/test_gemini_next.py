"""gemini-next (shadowfall/tools/gemini_next.py): picks the next missing prompt, spots a finished
download in a folder (not a half-done one), moves it into in/<name>.<ext> and runs import-art.
pbcopy, open and import_art.sh are faked: no browser ever opens here."""

import os
import sys
import time
from types import SimpleNamespace

from conftest import GAME_FOLDER
from helpers import ok

sys.path.insert(0, os.path.join(GAME_FOLDER, "shadowfall", "tools"))
import gemini_next as gn  # noqa: E402


def make_gemini(tmp_path, names):
    g = tmp_path / "gemini"
    (g / "prompts").mkdir(parents=True)
    (g / "in").mkdir()
    (g / "STYLE.txt").write_text("STYLE\n")
    for n in names:
        (g / "prompts" / (n + ".txt")).write_text("draw " + n + "\n")
    return str(g)


def test_next_missing_order_ground_first(tmp_path):
    g = make_gemini(tmp_path, ["oak", "ground_mud", "bush", "ground_grass"])
    ok(gn.missing(g) == ["ground_grass", "ground_mud", "bush", "oak"], "ground_* first, then sorted")
    open(os.path.join(g, "in", "ground_grass.webp"), "wb").write(b"x")
    ok(gn.missing(g)[0] == "ground_mud", "a done prompt is skipped")
    ok(gn.clip_text("oak", g) == "STYLE\n\ndraw oak\n", "STYLE, blank line, prompt")


def test_download_detection(tmp_path):
    d = tmp_path / "dl"
    d.mkdir()
    (d / "old.png").write_bytes(b"old")
    before = gn.images_in(str(d))
    since = time.time() + 1  # anything older than this that was there before is ignored
    sizes = {}
    ok(gn.check_download(str(d), before, since, sizes) is None, "an old file is not new")
    (d / "pic.png.crdownload").write_bytes(b"half")
    (d / "notes.txt").write_text("hi")
    ok(gn.check_download(str(d), before, since, sizes) is None, "partial and non-image files ignored")
    (d / "pic.png").write_bytes(b"ab")
    ok(gn.check_download(str(d), before, since, sizes) is None, "first look: size not settled yet")
    (d / "pic.png").write_bytes(b"abcd")
    ok(gn.check_download(str(d), before, since, sizes) is None, "still growing")
    ok(gn.check_download(str(d), before, since, sizes) == str(d / "pic.png"), "settled file picked")


def test_wait_download_keys(tmp_path):
    d = tmp_path / "dl"
    d.mkdir()
    ok(gn.wait_download(str(d), {}, 0, key=lambda: "q", sleep=lambda s: None) == "q", "q quits")
    keys = iter([None, None, "n"])
    ok(gn.wait_download(str(d), {}, 0, key=lambda: next(keys), sleep=lambda s: None) == "n", "n skips")


def test_move_in_replaces_old(tmp_path):
    g = make_gemini(tmp_path, ["oak"])
    open(os.path.join(g, "in", "oak.png"), "wb").write(b"old")
    src = tmp_path / "Gemini_Image.JPEG"
    src.write_bytes(b"new")
    dst = gn.move_in(str(src), "oak", g)
    ok(dst == os.path.join(g, "in", "oak.jpeg"), "renamed to in/oak.jpeg (%s)" % dst)
    ok(not src.exists() and not os.path.exists(os.path.join(g, "in", "oak.png")), "moved, old one gone")
    ok(open(dst, "rb").read() == b"new", "the new picture")


def fake_run(calls):
    def run_cmd(cmd, **kw):
        calls.append(cmd)
        return SimpleNamespace(returncode=0)
    return run_cmd


def test_run_loop_and_name_pick(tmp_path, capsys):
    g = make_gemini(tmp_path, ["oak", "ground_grass", "bush"])
    d = tmp_path / "dl"
    d.mkdir()
    calls = []
    answers = iter(["pic1", "n", "pic2"])

    def wait(folder, before, since):
        a = next(answers)
        if a == "n":
            return a
        p = d / (a + ".png")
        p.write_bytes(b"img")
        return str(p)

    ok(gn.run(downloads=str(d), gemini=g, run_cmd=fake_run(calls), wait=wait) == 0, "runs")
    ok(sorted(os.listdir(os.path.join(g, "in"))) == ["ground_grass.png", "oak.png"], "bush skipped")
    ok([c[-1] for c in calls if c[0] == "sh"] == ["ground_grass", "oak"], "each one imported")
    ok(sum(c[0] == "open" for c in calls) == 1, "Gemini opened once")
    ok(calls[1] == ["open", gn.GEMINI_URL], "only the Gemini page")
    ok("1 still to make" in capsys.readouterr().out, "says what is left")

    calls.clear()
    p = d / "redo.png"
    p.write_bytes(b"again")
    gn.run("oak", downloads=str(d), gemini=g, run_cmd=fake_run(calls), wait=lambda *a: str(p))
    ok(open(os.path.join(g, "in", "oak.png"), "rb").read() == b"again", "name pick redoes oak")
    ok([c[-1] for c in calls if c[0] == "sh"] == ["oak"], "imports oak")

    p = d / "b.png"
    p.write_bytes(b"b")
    gn.run("bush", downloads=str(d), gemini=g, run_cmd=fake_run([]), wait=lambda *a: str(p))
    gn.run(downloads=str(d), gemini=g, run_cmd=fake_run([]), wait=lambda *a: "q")
    ok("All 3 done." in capsys.readouterr().out, "All N done line")
