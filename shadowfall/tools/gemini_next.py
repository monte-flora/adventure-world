"""pixi run gemini-next [name] [--list] [--redo NAME "what to fix"] [--downloads DIR]: make the realm's
Gemini art one picture at a time.

First the pictures on the redo list (realm/gemini/redo.txt, one "name: what to fix" per line; the fix is
added to the prompt and the line is crossed off once the new picture is imported), then each prompt with
no picture in realm/gemini/in/ yet: put STYLE.txt + the prompt on the clipboard,
open Gemini in the browser (once), wait for the picture to land in ~/Downloads, move it to
in/<name>.<ext> and run import_art.sh on it. macOS (pbcopy, open). It never touches the website
beyond opening it: no clicking, no scraping, no API, no keys.
"""

import os
import select
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SHADOWFALL = os.path.dirname(HERE)
GEMINI = os.path.join(SHADOWFALL, "realm", "gemini")
IMPORT_ART = os.path.join(HERE, "import_art.sh")
GEMINI_URL = "https://gemini.google.com/app"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
PARTIAL_EXTS = (".crdownload", ".part", ".download")


def prompt_names(gemini=GEMINI):
    names = [f[:-4] for f in os.listdir(os.path.join(gemini, "prompts")) if f.endswith(".txt")]
    return sorted(names, key=lambda n: (not n.startswith("ground_"), n))


def done_file(name, gemini=GEMINI):
    for ext in IMAGE_EXTS:
        p = os.path.join(gemini, "in", name + ext)
        if os.path.exists(p):
            return p
    return None


def missing(gemini=GEMINI):
    return [n for n in prompt_names(gemini) if not done_file(n, gemini)]


def redo_notes(gemini=GEMINI):
    """{name: what to fix} from redo.txt, in file order."""
    p = os.path.join(gemini, "redo.txt")
    notes = {}
    if os.path.exists(p):
        for line in open(p):
            if ":" in line and not line.lstrip().startswith("#"):
                n, note = line.split(":", 1)
                notes[n.strip()] = note.strip()
    return notes


def save_redo(notes, gemini=GEMINI):
    with open(os.path.join(gemini, "redo.txt"), "w") as f:
        f.writelines("%s: %s\n" % kv for kv in notes.items())


def todo(gemini=GEMINI):
    """Redos first, then the missing ones."""
    redo = [n for n in redo_notes(gemini) if n in prompt_names(gemini)]
    return redo + [n for n in missing(gemini) if n not in redo]


def full_name(name, gemini=GEMINI):
    """dirt_road -> ground_dirt_road (the name import-art uses also works)."""
    names = prompt_names(gemini)
    return name if name in names or "ground_" + name not in names else "ground_" + name


def clip_text(name, gemini=GEMINI, note=None):
    style = open(os.path.join(gemini, "STYLE.txt")).read().strip()
    prompt = open(os.path.join(gemini, "prompts", name + ".txt")).read().strip()
    fix = "\n\nFix from last time: " + note if note else ""
    return style + "\n\n" + prompt + fix + "\n"


def images_in(folder):
    out = {}
    for f in os.listdir(folder):
        p = os.path.join(folder, f)
        low = f.lower()
        if low.startswith(".") or low.endswith(PARTIAL_EXTS) or not low.endswith(IMAGE_EXTS):
            continue
        try:
            st = os.stat(p)
        except OSError:
            continue
        out[p] = (st.st_mtime, st.st_size)
    return out


def check_download(folder, before, since, sizes):
    """One look at the folder. A new picture counts once its size is the same as last look.
    before: {path: (mtime, size)} at the start; sizes: {path: size} from the last look (updated)."""
    for p, (mtime, size) in sorted(images_in(folder).items()):
        if p in before and mtime <= since:
            continue
        if size > 0 and sizes.get(p) == size:
            return p
        sizes[p] = size
    return None


def read_key():
    """n or q if one was pressed, else None. Needs a terminal in cbreak mode."""
    if sys.stdin.isatty() and select.select([sys.stdin], [], [], 0)[0]:
        c = sys.stdin.read(1).lower()
        if c in ("n", "q"):
            return c
    return None


def wait_download(folder, before, since, key=read_key, poll=0.5, sleep=time.sleep):
    """Returns the settled picture's path, or "n" / "q" if that key was pressed."""
    sizes = {}
    while True:
        k = key()
        if k:
            return k
        p = check_download(folder, before, since, sizes)
        if p:
            return p
        sleep(poll)


def move_in(src, name, gemini=GEMINI):
    old = done_file(name, gemini)
    while old:
        os.remove(old)
        old = done_file(name, gemini)
    ext = os.path.splitext(src)[1].lower()
    dst = os.path.join(gemini, "in", name + ext)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return dst


def out_path(name):
    sub = "ground" if name.startswith("ground_") else "props"
    return os.path.join(SHADOWFALL, "realm", sub, name + ".png")


def cbreak():
    """Put the terminal in cbreak mode so n/q work without Enter. Returns an undo function."""
    if not sys.stdin.isatty():
        return lambda: None
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    return lambda: termios.tcsetattr(fd, termios.TCSADRAIN, old)


def run(name=None, downloads=None, gemini=GEMINI, run_cmd=subprocess.run, wait=wait_download):
    downloads = downloads or os.path.expanduser("~/Downloads")
    opened = False
    skipped = set()
    made = 0
    while True:
        if name:
            queue = [name]
        else:
            queue = [n for n in todo(gemini) if n not in skipped]
        if not queue:
            left = len(todo(gemini))
            if left:
                print("Done for now. %d still to make (pixi run gemini-next --list)." % left)
            else:
                print("All %d done." % len(prompt_names(gemini)))
            return 0
        cur = queue[0]
        note = redo_notes(gemini).get(cur)
        left = len(todo(gemini))
        print("\n== %s%s  (%d left)" % (cur, "  (redo: %s)" % note if note else "", left))
        run_cmd(["pbcopy"], input=clip_text(cur, gemini, note).encode(), check=True)
        since = time.time()
        before = images_in(downloads)
        print("Copied. Paste into Gemini, send, then download the picture you like. (n = skip, q = quit)")
        if not opened:
            run_cmd(["open", GEMINI_URL], check=False)
            opened = True
        got = wait(downloads, before, since)
        if got == "q":
            print("Bye. %d made this time." % made)
            return 0
        if got == "n":
            print("Skipped %s." % cur)
            skipped.add(cur)
            if name:
                return 0
            continue
        dst = move_in(got, cur, gemini)
        print("Got it: in/%s" % os.path.basename(dst))
        # import-art knows ground textures without the prefix: ground_grass -> grass
        r = run_cmd(["sh", IMPORT_ART, cur.removeprefix("ground_")], check=False)
        if r.returncode != 0:
            print("import-art had a problem with %s (see above)." % cur)
        else:
            print("Made %s" % os.path.relpath(out_path(cur), os.path.dirname(SHADOWFALL)))
            notes = redo_notes(gemini)
            if notes.pop(cur, None) is not None:
                save_redo(notes, gemini)
        made += 1
        if name:
            return 0


def main(argv, gemini=GEMINI):
    downloads = None
    if "--downloads" in argv:
        i = argv.index("--downloads")
        downloads = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if "--redo" in argv:
        i = argv.index("--redo")
        if len(argv) < i + 3:
            print('Say what to fix: pixi run gemini-next --redo dirt_road "no stripes, even all over"')
            return 1
        name = full_name(argv[i + 1], gemini)
        if name not in prompt_names(gemini):
            print("No prompt called %s. Try: pixi run gemini-next --list" % name)
            return 1
        notes = redo_notes(gemini)
        notes[name] = argv[i + 2]
        save_redo(notes, gemini)
        print("On the redo list: %s (%s). Run pixi run gemini-next to make it." % (name, argv[i + 2]))
        return 0
    if "--list" in argv:
        notes = redo_notes(gemini)
        for n in prompt_names(gemini):
            if n in notes:
                print("redo     %s  (%s)" % (n, notes[n]))
            else:
                print(("done     " if done_file(n, gemini) else "missing  ") + n)
        print("%d of %d done." % (len(prompt_names(gemini)) - len(missing(gemini)), len(prompt_names(gemini))))
        return 0
    name = full_name(argv[0], gemini) if argv else None
    if name and name not in prompt_names(gemini):
        print("No prompt called %s. Try: pixi run gemini-next --list" % name)
        return 1
    undo = cbreak()
    try:
        return run(name, downloads, gemini)
    except KeyboardInterrupt:
        print("\nBye.")
        return 0
    finally:
        undo()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
