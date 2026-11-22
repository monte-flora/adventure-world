"""Polish a cave with Gemini: the editor's "Polish" button, and the import step.

    python shadowfall/tools/polish.py export levels/caves/03_blue_lvl_1.txt
    python shadowfall/tools/polish.py import levels/caves/03_blue_lvl_1.txt

export writes levels/polish/<cave>/: layout.png (the cave as a clear map, 2752x1536), legend.png (what
the colours mean), prompt.txt (paste it into Gemini) and README.txt (the 3 steps).
import takes the picture you saved there from Gemini (any .png/.jpg/.webp) and makes painted.webp:
the cave's own size (32 px a block, so 1 painted pixel = 1 game pixel), under 1 MB for the web build.
It needs Godot (it does the WebP); the picture you dropped in is removed once painted.webp is made.
Shadowfall (caves/cave.gd) paints levels/polish/<cave>/painted.* behind the cave's blocks.
"""

import os
import re
import shutil
import subprocess
import sys

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")      # never any sound from a tool
import pygame  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POLISH_DIR = os.path.join(ROOT, "levels", "polish")
NAMES_GD = os.path.join(ROOT, "shadowfall", "rules", "names.gd")
SHADOWFALL = os.path.join(ROOT, "shadowfall")
SIZE = (2752, 1536)                      # Gemini's 16:9 size
TILE = 32                                # Shadowfall's block, in game pixels
MAX_BYTES = 1_000_000                    # painted.webp stays under this
IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".webp")
OURS = ("layout.png", "legend.png", "painted.webp")

# Letter -> what the map shows (levels/README.md has every letter).
SOLID = "#BG%I<>F*sMo"                   # rock, and blocks that sit in it like rock
LEDGE = "="
CRUMBLY = "-"
HAZARD = {"^": "spikes", "A": "spikes", "~": "lava", "!": "fire", "J": "fire", "n": "thorns"}
MARK = {"S": "start", "E": "exit", "C": "shrine"}
ROCK = (24, 20, 28)
AIR = (226, 222, 208)
GRID = (196, 192, 180)
LEDGE_LINE = (24, 20, 28)
COLOUR = {"spikes": (214, 40, 40), "lava": (255, 128, 0), "fire": (255, 200, 0), "thorns": (150, 60, 200),
          "start": (40, 170, 60), "exit": (230, 180, 30), "shrine": (40, 150, 230)}

# The look -> the place, in words for the painter. Grim epic fantasy, all our own.
SCENE = {
    "stone": "an ancient delved mine of cut granite, rotting timber props and rusted chains",
    "moss": "a drowned, moss-choked cavern of roots, dripping stone and broken carvings",
    "crystal": "a frozen cavern of pale blue ice crystals, frost and cold mist",
    "lava": "a volcanic forge-cavern of black basalt, glowing magma seams and ember haze",
    "shadow": "a lightless hollow of black stone veined with faint violet, where something old sleeps",
    "castle": "the vaults of a fallen fortress: worn flagstones, iron gates and torn banners",
}


def cave_key(cave_path):
    """levels/caves/03_blue_lvl_1.txt -> 03_blue_lvl_1 (the folder name in levels/polish/)."""
    return os.path.splitext(os.path.basename(cave_path))[0]


def folder(cave_path):
    return os.path.join(POLISH_DIR, cave_key(cave_path))


def cell_rect(r, c, rows, size=SIZE):
    """Where block (r, c) is on the map: the cave is stretched to fill the whole picture."""
    w, h = size
    x0, x1 = c * w // len(rows[0]), (c + 1) * w // len(rows[0])
    y0, y1 = r * h // len(rows), (r + 1) * h // len(rows)
    return pygame.Rect(x0, y0, x1 - x0, y1 - y0)


def what(letter):
    if letter in SOLID:
        return "rock"
    if letter == LEDGE:
        return "ledge"
    if letter == CRUMBLY:
        return "crumbly"
    return HAZARD.get(letter) or MARK.get(letter) or "air"


def layout(rows, size=SIZE):
    """The cave as a map Gemini can follow: rock dark, air light, ledges outlined, hazards coloured,
    start/exit/shrine as small icons, a thin grid. No text in it (text tempts Gemini to copy it)."""
    pic = pygame.Surface(size)
    pic.fill(AIR)
    for r, row in enumerate(rows):
        for c, letter in enumerate(row):
            box, kind = cell_rect(r, c, rows, size), what(letter)
            if kind == "rock":
                pic.fill(ROCK, box)
            elif kind in ("spikes", "lava", "fire", "thorns"):
                pic.fill(COLOUR[kind], box)
    edge = max(1, size[1] // 400)
    for r in range(len(rows) + 1):                      # the grid, under the outlines and icons
        y = min(r * size[1] // len(rows), size[1] - 1)
        pygame.draw.line(pic, GRID, (0, y), (size[0], y), 1)
    for c in range(len(rows[0]) + 1):
        x = min(c * size[0] // len(rows[0]), size[0] - 1)
        pygame.draw.line(pic, GRID, (x, 0), (x, size[1]), 1)
    for r, row in enumerate(rows):
        for c, letter in enumerate(row):
            box, kind = cell_rect(r, c, rows, size), what(letter)
            if kind in ("ledge", "crumbly"):                # a thin bar along the top of the block
                bar = pygame.Rect(box.x, box.y, box.w, max(4, box.h // 4))
                pygame.draw.rect(pic, (120, 110, 100), bar)
                pygame.draw.rect(pic, LEDGE_LINE, bar, edge * 2)
                if kind == "crumbly":
                    for x in range(bar.x + bar.w // 3, bar.right - 1, max(2, bar.w // 3)):
                        pygame.draw.line(pic, LEDGE_LINE, (x, bar.y), (x, bar.bottom), edge * 2)
            elif kind in MARK.values():
                icon(pic, kind, box)
    return pic


def icon(pic, kind, box):
    size = max(6, min(box.w, box.h) * 2 // 3)
    mid = box.center
    if kind == "start":
        pygame.draw.circle(pic, COLOUR[kind], mid, size // 2)
    elif kind == "exit":                                   # a door: tall, round top
        door = pygame.Rect(0, 0, size * 2 // 3, size)
        door.center = mid
        pygame.draw.rect(pic, COLOUR[kind], door, border_top_left_radius=door.w // 2,
                         border_top_right_radius=door.w // 2)
    else:                                                  # the shrine: a diamond
        h = size // 2
        pygame.draw.polygon(pic, COLOUR[kind], [(mid[0], mid[1] - h), (mid[0] + h, mid[1]),
                                                (mid[0], mid[1] + h), (mid[0] - h, mid[1])])


def legend():
    """A small strip that says what the map's colours mean (for you, not for Gemini)."""
    pygame.font.init()
    font = pygame.font.Font(None, 40)
    items = [("rock", ROCK), ("open air", AIR), ("ledge", (120, 110, 100))] + \
            [(k, COLOUR[k]) for k in ("spikes", "lava", "fire", "thorns", "start", "exit", "shrine")]
    strip = pygame.Surface((SIZE[0], 80))
    strip.fill((60, 56, 64))
    x = 24
    for label, colour in items:
        pygame.draw.rect(strip, colour, (x, 20, 40, 40))
        pygame.draw.rect(strip, (0, 0, 0), (x, 20, 40, 40), 2)
        text = font.render(label, True, (240, 236, 224))
        strip.blit(text, (x + 52, 40 - text.get_height() // 2))
        x += 52 + text.get_width() + 48
    return strip


def land_names():
    """The lands' names from rules/names.gd (the one list of names): {"emberhold": "Emberhold", ...}."""
    try:
        with open(NAMES_GD, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return {}
    block = re.search(r"const LAND := \{(.*?)\}", text, re.S)
    return dict(re.findall(r'"(\w+)":\s*"([^"]+)"', block.group(1))) if block else {}


def header(settings, key):
    for line in settings:
        if line.split(":", 1)[0].strip() == key:
            return line.split(":", 1)[1].strip()
    return ""


def prompt(theme, settings):
    """A short prompt to paste into Gemini next to layout.png."""
    land = header(settings, "land")
    land = land_names().get(land, land)
    place = SCENE.get(theme, SCENE["stone"]) + (", deep in %s" % land if land else "")
    dark = header(settings, "dark") == "yes"
    light = ("Almost no light: deep black shadows, a faint cold glow, but keep the open air a little lighter "
             "than the rock so the paths still read." if dark else
             "Moody light: dim torch glow and cold shafts of light, deep shadows in the corners.")
    return "\n".join([
        "Repaint this map as a painted pixel-art cave backdrop for a 2D side-view fantasy game.",
        "",
        "Place: %s." % place,
        "Mood: grim, epic and ancient, like a war-torn realm of old kingdoms. Original art, teen-safe, no gore.",
        light,
        "",
        "Keep the layout exactly: dark = solid rock, light = open cave air. Every wall, ledge, tunnel and "
        "opening stays exactly where the map shows it; do not move, add or close any of them.",
        "Outlined bars are thin stone ledges. Red = spikes, orange = lava, yellow = fire, purple = black "
        "thorns. Green dot = the way in, gold door = the way out, blue diamond = a small lantern shrine.",
        "",
        "No characters, creatures, people, text, letters, numbers, UI or grid lines (remove the grid).",
        "Same size and shape as the map: 2752x1536, 16:9, the whole frame filled edge to edge.",
        "Crisp pixel art, chunky pixels, limited dark palette, strong silhouettes.",
    ]) + "\n"


README = """\
Polish this cave with Gemini (3 steps)

1. Open Gemini (gemini.google.com) and drag layout.png from this folder into the chat.
2. Open prompt.txt, copy all of it, paste it into the chat and send it.
3. Download the picture Gemini makes into this folder. Call it painted.png
   (any .png, .jpg or .webp works). Then press Polish in the editor again:
   it shrinks the picture into painted.webp for the game.

Don't like it? Ask Gemini to try again, or change the words in prompt.txt.
legend.png says what each colour on the map means.
"""


def export(cave_path, theme, rows, settings):
    """Write layout.png, legend.png, prompt.txt and README.txt. Returns the folder."""
    out = folder(cave_path)
    os.makedirs(out, exist_ok=True)
    pygame.image.save(layout(rows), os.path.join(out, "layout.png"))
    pygame.image.save(legend(), os.path.join(out, "legend.png"))
    for name, text in (("prompt.txt", prompt(theme, settings)), ("README.txt", README)):
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(text)
    return out


def dropped(cave_path):
    """The newest picture you saved in the cave's folder (not one we made), or None."""
    out = folder(cave_path)
    if not os.path.isdir(out):
        return None
    pics = [os.path.join(out, f) for f in os.listdir(out)
            if f.lower().endswith(IMAGE_TYPES) and f not in OURS]
    return max(pics, key=os.path.getmtime) if pics else None


def import_painting(cave_path, rows, godot=None):
    """Turn the picture you dropped in into painted.webp (the cave's size, under 1 MB).
    Returns (ok, message)."""
    src = dropped(cave_path)
    if not src:
        return False, "No picture yet: save Gemini's picture in %s" % short(folder(cave_path))
    godot = godot or os.environ.get("GODOT", "godot")
    if not shutil.which(godot):
        return False, "I need Godot to shrink the picture (see shadowfall/README.md)."
    dst = os.path.join(folder(cave_path), "painted.webp")
    w, h = len(rows[0]) * TILE, len(rows) * TILE
    result = subprocess.run([godot, "--headless", "--audio-driver", "Dummy", "--path", SHADOWFALL,
                             "--script", "res://tools/polish_import.gd", "--", src, dst, str(w), str(h),
                             str(MAX_BYTES)], capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        return False, "I couldn't read that picture: %s" % (result.stdout + result.stderr).strip()[-200:]
    os.remove(src)
    return True, "Painted! %s is in the game now (%d KB)." % (cave_key(cave_path), os.path.getsize(dst) // 1024)


def short(path):
    return os.path.relpath(path, ROOT)


def main(argv):
    if len(argv) != 3 or argv[1] not in ("export", "import"):
        print(__doc__)
        return 1
    sys.path.insert(0, ROOT)
    import cave_files
    theme, rows, _ = cave_files.load_cave(argv[2])
    if argv[1] == "export":
        print("Made", short(export(argv[2], theme, rows, cave_files.load_settings(argv[2]))))
        return 0
    ok, message = import_painting(argv[2], rows)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
