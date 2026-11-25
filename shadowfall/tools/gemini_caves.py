"""pixi run gemini-caves [name] [--list] [--redo NAME "what to fix"] [--downloads DIR]: paint the caves
with Gemini, one at a time.

Walks every cave with no levels/polish/<cave>/painted.* yet (caves, stone, secret, shadow, castle, then
the throne room: levels/polish/throne_room/throne_room.txt is its map, prompt.txt its words), the
redo list (levels/polish/redo.txt, "name: what to fix") first. For each: makes the map and words
(polish.py export; a prompt.txt you edited is kept), puts the map on the clipboard as a picture, opens
Gemini (once), then on Enter puts the words on the clipboard, waits for the painting to land in
~/Downloads, moves it into levels/polish/<cave>/ and runs polish.py import. macOS (osascript, pbcopy,
open). It never touches the website beyond opening it: no clicking, no scraping, no API, no keys.
Uses gemini_next.py's download watcher and redo list.
"""

import os
import shutil
import subprocess
import sys
import time

import gemini_next as gn

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEVELS = os.path.join(ROOT, "levels")
POLISH = os.path.join(HERE, "polish.py")
FOLDERS = ("caves", "stone", "secret", "shadow", "castle")     # this order
THRONE = "throne_room"                                          # boss/boss.gd THRONE_ROOM, last
PAINTED = ("painted.webp", "painted.png", "painted.jpg", "painted.jpeg")   # caves/cave_art.gd PAINTED


def caves(levels=LEVELS):
    """[(name, path)] for every cave file, folder by folder, sorted inside each."""
    out = []
    for sub in FOLDERS:
        d = os.path.join(levels, sub)
        if os.path.isdir(d):
            out += [(f[:-4], os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".txt")]
    throne = os.path.join(levels, "polish", THRONE, THRONE + ".txt")
    return out + [(THRONE, throne)] if os.path.exists(throne) else out


def polish_dir(name, levels=LEVELS):
    return os.path.join(levels, "polish", name)


def is_done(name, levels=LEVELS):
    return any(os.path.exists(os.path.join(polish_dir(name, levels), p)) for p in PAINTED)


def names(levels=LEVELS):
    return [n for n, _ in caves(levels)]


def todo(levels=LEVELS):
    """Redos first, then the caves with no painting."""
    redo = [n for n in gn.redo_notes(os.path.join(levels, "polish")) if n in names(levels)]
    return redo + [n for n in names(levels) if not is_done(n, levels) and n not in redo]


def find(name, levels=LEVELS):
    """A cave by its name or by the start of it (17 -> 17_the_fire_mountain), or None."""
    hits = [n for n in names(levels) if n == name] or [n for n in names(levels) if n.startswith(name)]
    return hits[0] if len(hits) == 1 else None


def export(name, path, levels=LEVELS, run_cmd=subprocess.run):
    """polish.py export when the map or the words are missing. A prompt.txt that is there stays as it is."""
    out = polish_dir(name, levels)
    keep = os.path.join(out, "prompt.txt")
    if os.path.exists(os.path.join(out, "layout.png")) and os.path.exists(keep):
        return
    old = open(keep, encoding="utf-8").read() if os.path.exists(keep) else None
    run_cmd([sys.executable, POLISH, "export", path], check=False)
    if old is not None:
        with open(keep, "w", encoding="utf-8") as f:
            f.write(old)


def copy_picture(png, run_cmd=subprocess.run):
    """The picture on the clipboard (as a picture, so Cmd+V in Gemini pastes it). A .jpg goes as JPEG."""
    kind = "JPEG" if png.lower().endswith((".jpg", ".jpeg")) else "PNGf"
    script = 'set the clipboard to (read (POSIX file "%s") as «class %s»)' % (png.replace('"', '\\"'), kind)
    run_cmd(["osascript", "-e", script], check=True)


def clip_text(name, levels=LEVELS, note=None):
    words = open(os.path.join(polish_dir(name, levels), "prompt.txt"), encoding="utf-8").read().strip()
    return words + ("\n\nFix from last time: " + note if note else "") + "\n"


def ask_enter(ask=input):
    """Enter = go on; n = skip; q = quit."""
    try:
        a = ask().strip().lower()
    except EOFError:
        return "q"
    return a if a in ("n", "q") else ""


def move_in(src, name, levels=LEVELS):
    dst = os.path.join(polish_dir(name, levels), "from_gemini" + os.path.splitext(src)[1].lower())
    shutil.move(src, dst)
    return dst


def run(name=None, downloads=None, levels=LEVELS, run_cmd=subprocess.run, wait=gn.wait_download, ask=input):
    downloads = downloads or os.path.expanduser("~/Downloads")
    path = dict(caves(levels))
    redo_dir = os.path.join(levels, "polish")
    opened = False
    skipped = set()
    made = 0
    while True:
        queue = [name] if name else [n for n in todo(levels) if n not in skipped]
        if not queue:
            left = len(todo(levels))
            print("Done for now. %d still to paint (pixi run gemini-caves --list)." % left if left
                  else "All %d caves painted." % len(path))
            return 0
        cur = queue[0]
        note = gn.redo_notes(redo_dir).get(cur)
        print("\n== %s%s  (%d left)" % (cur, "  (redo: %s)" % note if note else "", len(todo(levels))))
        export(cur, path[cur], levels, run_cmd)
        since = time.time()
        before = gn.images_in(downloads)
        copy_picture(os.path.join(polish_dir(cur, levels), "layout.png"), run_cmd)
        if not opened:
            run_cmd(["open", gn.GEMINI_URL], check=False)
            opened = True
        print("Paste the map into Gemini (Cmd+V), then press Enter here. (n = skip, q = quit)")
        got = ask_enter(ask)
        if not got:
            run_cmd(["pbcopy"], input=clip_text(cur, levels, note).encode(), check=True)
            print("Paste the words and send; download the painting you like. (n = skip, q = quit)")
            undo = gn.cbreak()
            try:
                got = wait(downloads, before, since)
            finally:
                undo()
        if got == "q":
            print("Bye. %d painted this time." % made)
            return 0
        if got == "n":
            print("Skipped %s." % cur)
            skipped.add(cur)
            if name:
                return 0
            continue
        move_in(got, cur, levels)
        r = run_cmd([sys.executable, POLISH, "import", path[cur]], check=False)
        if r.returncode != 0:
            print("polish import had a problem with %s (see above)." % cur)
        else:
            print("Painted %s" % cur)
            notes = gn.redo_notes(redo_dir)
            if notes.pop(cur, None) is not None:
                gn.save_redo(notes, redo_dir)
        made += 1
        if name:
            return 0


def main(argv, levels=LEVELS):
    downloads = None
    if "--downloads" in argv:
        i = argv.index("--downloads")
        downloads = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if "--redo" in argv:
        i = argv.index("--redo")
        if len(argv) < i + 3:
            print('Say what to fix: pixi run gemini-caves --redo 03_blue_lvl_1 "more ice on the walls"')
            return 1
        cur = find(argv[i + 1], levels)
        if not cur:
            print("No cave called %s. Try: pixi run gemini-caves --list" % argv[i + 1])
            return 1
        redo_dir = os.path.join(levels, "polish")
        notes = gn.redo_notes(redo_dir)
        notes[cur] = argv[i + 2]
        os.makedirs(redo_dir, exist_ok=True)
        gn.save_redo(notes, redo_dir)
        print("On the redo list: %s (%s). Run pixi run gemini-caves to paint it." % (cur, argv[i + 2]))
        return 0
    if "--list" in argv:
        notes = gn.redo_notes(os.path.join(levels, "polish"))
        for n in names(levels):
            if n in notes:
                print("redo     %s  (%s)" % (n, notes[n]))
            else:
                print(("done     " if is_done(n, levels) else "missing  ") + n)
        print("%d of %d painted." % (sum(is_done(n, levels) for n in names(levels)), len(names(levels))))
        return 0
    cur = find(argv[0], levels) if argv else None
    if argv and not cur:
        print("No cave called %s. Try: pixi run gemini-caves --list" % argv[0])
        return 1
    try:
        return run(cur, downloads, levels)
    except KeyboardInterrupt:
        print("\nBye.")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
