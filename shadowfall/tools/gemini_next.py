"""pixi run gemini-next [name] [--list] [--downloads DIR]: make the realm's Gemini art one picture at a time.

For each prompt with no picture in realm/gemini/in/ yet: put STYLE.txt + the prompt on the clipboard,
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


def clip_text(name, gemini=GEMINI):
    style = open(os.path.join(gemini, "STYLE.txt")).read().strip()
    prompt = open(os.path.join(gemini, "prompts", name + ".txt")).read().strip()
    return style + "\n\n" + prompt + "\n"


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
            todo = [name]
        else:
            todo = [n for n in missing(gemini) if n not in skipped]
        if not todo:
            left = len(missing(gemini))
            if left:
                print("Done for now. %d still to make (pixi run gemini-next --list)." % left)
            else:
                print("All %d done." % len(prompt_names(gemini)))
            return 0
        cur = todo[0]
        left = len(missing(gemini))
        print("\n== %s  (%d left)" % (cur, left))
        run_cmd(["pbcopy"], input=clip_text(cur, gemini).encode(), check=True)
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
        r = run_cmd(["sh", IMPORT_ART, cur], check=False)
        if r.returncode != 0:
            print("import-art had a problem with %s (see above)." % cur)
        else:
            print("Made %s" % os.path.relpath(out_path(cur), os.path.dirname(SHADOWFALL)))
        made += 1
        if name:
            return 0


def main(argv):
    downloads = None
    if "--downloads" in argv:
        i = argv.index("--downloads")
        downloads = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if "--list" in argv:
        for n in prompt_names():
            print(("done     " if done_file(n) else "missing  ") + n)
        print("%d of %d done." % (len(prompt_names()) - len(missing()), len(prompt_names())))
        return 0
    name = argv[0] if argv else None
    if name and name not in prompt_names():
        print("No prompt called %s. Try: pixi run gemini-next --list" % name)
        return 1
    undo = cbreak()
    try:
        return run(name, downloads)
    except KeyboardInterrupt:
        print("\nBye.")
        return 0
    finally:
        undo()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
