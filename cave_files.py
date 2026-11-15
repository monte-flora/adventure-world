"""
CAVE FILES - loading, saving and checking the caves you draw in the cave editor.

Your caves are saved in the my_caves folder, one text file for each cave.
Open one in any text editor and you'll see it's drawn with the same letters
as the caves in caves.py:

    theme: moss
    ##########
    #........#
    ..S...*E.#
    ##########

This file knows nothing about graphics (editor.py draws everything), so it's
easy to test.
"""

import os
import re

import castle
import caves

# ===========================================================================
# SETTINGS
# ===========================================================================
MY_CAVES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_caves")
THEMES = ["stone", "crystal", "lava", "moss", "castle"]     # how a cave can look (the Look button goes through these)
KNOWN_LOOKS = THEMES + ["shadow"]                           # the dark caves of Nightfall Hollow open in the editor too
HEIGHTS = [14, 20]                                          # how tall a cave can be
CASTLE_ONLY = "iwf"                                         # torches, windows and banners: castle look only
MONSTERS = caves.CAVE_MONSTERS                              # z, k, c and x
EVERY_LETTER = ".#B*s=-HV%I^A~!o$TSEu" + "FGgJMPUR" + "".join(MONSTERS) + CASTLE_ONLY + "?" + "KLlD+"   # the last ones: castle.py

# A brand new cave: rock all around, a way in on the left, a diamond and an exit on the right
NEW_CAVE_WIDTH = 40
NEW_CAVE_HEIGHT = 14


# ===========================================================================
# Turning a cave drawing into rows, and back again
# ===========================================================================

def read_cave(text):
    """Split a cave drawing into its look ("theme") and its rows.
    Returns (theme, rows, notes): notes says if anything had to be fixed."""
    theme = caves.level_theme(text)
    rows = [row for row in caves.level_lines(text) if row]
    notes = []
    if not rows:
        return theme, new_cave_rows(), ["That cave was empty, so here's a new one."]
    width = max(len(row) for row in rows)
    if any(len(row) != width for row in rows):
        rows = [row.ljust(width, ".") for row in rows]
        notes.append("Some rows were shorter than others, so I filled them in with air.")
    if theme not in KNOWN_LOOKS:
        notes.append("I don't know the look '%s', so it's stone now." % theme)
        theme = "stone"
    return theme, rows, notes


def cave_text(theme, rows, settings=()):
    """The whole cave as text, ready to save (or to play). settings are any other setting
    lines the cave has, like "lava rises: yes" or "name: The Vine Garden"."""
    return "theme: %s\n%s%s\n" % (theme, "".join(line + "\n" for line in settings), "\n".join(rows))


def settings_of(text):
    """A cave drawing's setting lines, all but its look ("theme: ..."), so they're kept when it's saved."""
    lines = [line.strip() for line in text.strip().splitlines() if ":" in line]
    return [line for line in lines if not line.startswith("theme:")]


def new_cave_rows(width=NEW_CAVE_WIDTH, height=NEW_CAVE_HEIGHT):
    """A brand new, nearly empty cave with a start, a diamond and an exit."""
    rows = ["#" * width]
    for r in range(1, height - 1):
        way_in = r >= height - 4                       # the gap in the left wall is the way back out
        rows.append(("." if way_in else "#") + "." * (width - 2) + "#")
    rows.append("#" * width)
    floor = height - 2
    rows[floor] = put(rows[floor], 2, "S")
    rows[floor] = put(rows[floor], width - 8, "*")
    rows[floor] = put(rows[floor], width - 4, "E")
    return rows


def put(row, c, letter):
    return row[:c] + letter + row[c + 1:]


# ===========================================================================
# Saving and loading your caves
# ===========================================================================

def file_name(name):
    """Turn a cave's name into a file name: "Lava Tower!" becomes "lava_tower.txt"."""
    simple = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return (simple or "my_cave") + ".txt"


def nice_name(path):
    """Turn a file name back into a name: "lava_tower.txt" becomes "lava tower"."""
    return os.path.splitext(os.path.basename(path))[0].replace("_", " ")


def save_cave(name, theme, rows, folder=None, settings=()):
    """Save a cave in the my_caves folder. Returns where it went."""
    folder = folder or MY_CAVES_FOLDER
    return write_cave(os.path.join(folder, file_name(name)), theme, rows, settings)


def write_cave(path, theme, rows, settings=()):
    """Save a cave in exactly this file (a cave in my_caves, or one of the game's own caves)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(cave_text(theme, rows, settings))
    return path


def load_cave(path):
    """Read a saved cave. Returns (theme, rows, notes), like read_cave."""
    with open(path, encoding="utf-8") as f:
        return read_cave(f.read())


def load_settings(path):
    """The setting lines of a saved cave (see settings_of)."""
    with open(path, encoding="utf-8") as f:
        return settings_of(f.read())


def is_game_level(path):
    """Is this file one of the game's own caves or castle levels (in the levels folder)?"""
    folder = os.path.abspath(caves.LEVELS_FOLDER) + os.sep
    return bool(path) and os.path.abspath(path).startswith(folder)


def short_path(path):
    """Where a cave file is, from the game's folder: "levels/caves/03_blue_lvl_1.txt"."""
    return os.path.relpath(path, os.path.dirname(os.path.abspath(__file__))).replace(os.sep, "/")


def my_caves(folder=None):
    """Every cave you saved: a list of (name, path), A to Z."""
    folder = folder or MY_CAVES_FOLDER
    if not os.path.isdir(folder):
        return []
    files = sorted(f for f in os.listdir(folder) if f.endswith(".txt"))
    return [(nice_name(f), os.path.join(folder, f)) for f in files]


def game_levels():
    """Every cave the game plays (the Mines, the castle, Nightfall and the Secret Mine), one file each in the
    levels folder: a list of (name, path).
    Open one in the editor and Save changes it in the game."""
    found = []
    for i, (path, text) in enumerate(caves.CAVE_LEVEL_FILES):
        found.append(("Cave %d: %s (%s)" % (i + 1, caves.level_setting(text, "name", nice_name(path)),
                                             caves.level_theme(text)), path))
    for i, (path, text) in enumerate(castle.CASTLE_LEVEL_FILES):
        found.append(("Castle level %d: %s" % (i + 1, caves.level_setting(text, "name", nice_name(path))), path))
    for i, (path, text) in enumerate(caves.SHADOW_CAVE_FILES):
        found.append(("Nightfall cave %d: %s" % (i + 1, caves.level_setting(text, "name", nice_name(path))), path))
    for path, text in caves.SECRET_CAVE_FILES:
        found.append(("Secret Mine: %s (%s)" % (caves.level_setting(text, "name", nice_name(path)),
                                               caves.level_theme(text)), path))
    return found


def game_caves():
    """Every cave and castle level in the game: a list of (name, text)."""
    levels = []
    for name, path in game_levels():
        with open(path, encoding="utf-8") as f:
            levels.append((name, f.read()))
    return levels


# ===========================================================================
# CHECKS - things to fix before (or after) you play your cave
# ===========================================================================

def find_all(rows, letters):
    return [(r, c) for r, row in enumerate(rows) for c, letter in enumerate(row) if letter in letters]


def is_rock(rows, r, c):
    return 0 <= r < len(rows) and 0 <= c < len(rows[0]) and rows[r][c] in caves.SOLIDS


def check_cave(theme, rows):
    """Look for problems. Returns a list of (how_bad, message):
    "must" = you have to fix it before you can play, "tip" = the cave works, but you might want to fix it."""
    problems = []
    starts, exits, ores = find_all(rows, "S"), find_all(rows, "E"), find_all(rows, "*")
    if not starts:
        problems.append(("must", "No start yet! Put an S where the Hero climbs in."))
    elif len(starts) > 1:
        problems.append(("tip", "There are %d starts (S). Only the first one is used." % len(starts)))
    if not exits:
        problems.append(("tip", "No exit door (E) yet. The only way out is back the way you came in."))
    if not ores:
        problems.append(("tip", "No diamond ore (*) yet. Every cave needs a diamond to find!"))

    # Lava is a hot pool sunk into the floor: it goes in the bottom row, or in the top of a rock block.
    # Lava stacked on lava makes a deeper pool: under its top, the pool needs rock (or more lava) on both sides.
    floor = len(rows) - 1

    def holds_lava(r, c):
        return is_rock(rows, r, c) or (0 <= c < len(rows[0]) and rows[r][c] == "~")

    floating = sorted({c for r, c in find_all(rows, "~")
                       if (r != floor and not holds_lava(r + 1, c))
                       or (r > 0 and rows[r - 1][c] == "~" and not (holds_lava(r, c - 1) and holds_lava(r, c + 1)))})
    if floating:
        problems.append(("tip", "Lava in the air (column %s). Draw lava IN the floor row, as a pool."
                         % ", ".join(str(c) for c in floating[:4])))

    # The Hero and most monsters are a bit taller than one block: rock right above them squashes them
    for r, c in starts[:1]:
        if is_rock(rows, r - 1, c):
            problems.append(("tip", "The Hero's start is squashed under rock. Leave air above the S."))
    for r, c in find_all(rows, "".join(MONSTERS)):
        name = MONSTERS[rows[r][c]]
        tall = caves.MONSTER_SIZE.get(name, (0.8, 1.1))[1] > 1
        if tall and is_rock(rows, r - 1, c):
            problems.append(("tip", "The %s at column %d is stuck in rock. Leave air above it." % (name, c)))

    # Iron gates need a lever to open them
    if find_all(rows, caves.GATE) and not find_all(rows, caves.LEVER):
        problems.append(("tip", "There's an iron gate (G) but no lever (L) to open it."))
    if find_all(rows, caves.LEVER) and not find_all(rows, caves.GATE) and theme != "castle":
        problems.append(("tip", "There's a lever (L) but no iron gate (G) for it to open."))

    problems += check_platforms(rows)
    for swing in caves.find_swings([list(row) for row in rows]):
        if swing.r > 0 and not is_rock(rows, swing.r - 1, swing.c):
            problems.append(("tip", "The swinging vine at column %d hangs from nothing. "
                             "Put rock right above its top R." % swing.c))

    if find_all(rows, "?"):
        problems.append(("tip", "A ? isn't a block any more (it was a surprise monster in old caves). In your cave it's just air."))
    if theme != "castle" and find_all(rows, CASTLE_ONLY):
        problems.append(("tip", "Torches, windows and banners only show up in the castle look."))
    strange = sorted({letter for row in rows for letter in row if letter not in EVERY_LETTER})
    if strange:
        problems.append(("tip", "I don't know these letters: %s. They work like air." % " ".join(strange)))
    return problems


def check_platforms(rows):
    """Tips about moving-platform tracks: the P's and U's are exactly where a platform goes."""
    problems = []
    platforms = caves.find_platforms([list(row) for row in rows])
    for p in platforms:
        where = "column %d, row %d" % (p.c, p.r)
        if not p.moves():
            if p.axis == "x":
                problems.append(("tip", "The platform at %s can't move: draw 3 or more P's in a row." % where))
            else:
                problems.append(("tip", "The up-down platform at %s can't move: draw 2 or more rows of U's." % where))
        elif p.axis == "y" and any(is_rock(rows, p.low - k, cc) for k in range(1, caves.PLATFORM_ROOM + 1)
                                   for cc in range(p.c, p.c + p.w)):
            problems.append(("tip", "The up-down platform at %s squashes you at the top. "
                             "Leave %d blocks of air above the U's." % (where, caves.PLATFORM_ROOM)))
    ups = [p for p in platforms if p.axis == "y"]
    for a in ups:                         # U's that don't make a neat box fall apart into more platforms
        for b in ups:
            if b.low == a.high + 1 and b.c < a.c + a.w and a.c < b.c + b.w:
                problems.append(("tip", "The U's at column %d aren't a neat column, so they make 2 platforms. "
                                 "Make every row of U's the same width." % b.c))
    return problems


def can_play(theme, rows):
    """You can play a cave as soon as it has a start."""
    return not any(how_bad == "must" for how_bad, _ in check_cave(theme, rows))
