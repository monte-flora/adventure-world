"""
THE PHASE 2 WORLD MAP - one text file for every land, stitched into one big map.

The files are in levels/world/ (levels/README.md explains how to write one). Each says where
its top-left corner goes on the big map ("at: row column"), and draws its squares with the same
letters as the classic map in rules.py. A "." means "not this land", so a land can have any shape.
Squares no land covers are deep water.

A land file can also say where things are, in its own rows and columns (row 0, column 0 is its
top-left corner): "home:", "village:", "gate:" and "lookout:" (see levels/README.md).

This file knows nothing about graphics, so it's easy to test.
"""

import os

WORLD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "levels", "world")
NOT_HERE = "."                  # in a land file: this square belongs to another land
EMPTY = "W"                     # squares no land covers are water
MAP_LETTERS = "FGXIBLTSMR+=HWOPV~#C"   # the letters a land may use (the classic map's letters)
MANY = ("village", "gate", "lookout")    # header lines a land can have more than once


class WorldMapError(ValueError):
    """A land file is drawn wrong. The message says which file and what's wrong."""


class Atlas:
    """The big map, and which land every square is in.

    grid: the rows of letters (a list of lists, like rules.parse_map gives)
    lands: one tuple per land, shaped like the lines of rules.LANDS:
           (name, top, left, bottom, right, landmark, what you hear the first time you get there)
    land_index: for every square, its land's number in `lands` (None: no land, open water)
    home: where you start (a land's "home:" line), or None (then it's the last H, like the classic map)
    villages: [(name, (row, col) of its open square, land name), ...]
    gates: {(row, col): (name, level)}: a rock in the way until you reach that level
    lookouts: [(row, col), ...]: lookout towers (climb one with SPACE to spot hidden treasure)
    """

    def __init__(self, grid, lands, land_index, home=None, villages=(), gates=None, lookouts=()):
        self.grid = grid
        self.lands = lands
        self.land_index = land_index
        self.home = home
        self.villages = list(villages)
        self.gates = dict(gates or {})
        self.lookouts = list(lookouts)

    @property
    def rows(self):
        return len(self.grid)

    @property
    def cols(self):
        return len(self.grid[0])

    def land_at(self, pos):
        r, c = pos
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return None
        i = self.land_index[r][c]
        return None if i is None else self.lands[i]


def read_land(text, where="a land file"):
    """One land file -> (settings, rows). Settings are the "name: ..." lines at the top."""
    settings, rows = {}, []
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        key, colon, value = line.partition(":")
        if colon and not rows and key.strip().isalpha():
            key = key.strip().lower()
            if key in MANY:
                settings.setdefault(key, []).append(value.strip())
            else:
                settings[key] = value.strip()
        else:
            rows.append(line)
    if "name" not in settings:
        raise WorldMapError("%s needs a 'name:' line" % where)
    try:
        top, left = (int(n) for n in settings.get("at", "").split())
    except ValueError:
        raise WorldMapError("%s needs an 'at: row column' line, like 'at: 0 40'" % where) from None
    if top < 0 or left < 0:
        raise WorldMapError("%s: 'at:' can't be below 0" % where)
    if not rows:
        raise WorldMapError("%s has no drawing" % where)
    if any(len(row) != len(rows[0]) for row in rows):
        raise WorldMapError("%s: every row must be the same length" % where)
    bad = sorted({letter for row in rows for letter in row if letter not in MAP_LETTERS + NOT_HERE})
    if bad:
        raise WorldMapError("%s uses letters the map doesn't know: %s" % (where, " ".join(bad)))
    settings["top"], settings["left"] = top, left
    _read_places(settings, rows, where)
    return settings, rows


def _numbers_at_the_end(text, how_many, line, where):
    """"Meadowbrook 6 24" -> ("Meadowbrook", [6, 24]). The name can have spaces in it."""
    words = text.split()
    try:
        numbers = [int(w) for w in words[len(words) - how_many:]]
    except ValueError:
        numbers = []
    if len(numbers) != how_many or len(words) < how_many:
        raise WorldMapError("%s: can't read '%s'" % (where, line))
    return " ".join(words[:len(words) - how_many]), numbers


def _read_places(settings, rows, where):
    """The home:, village:, gate: and lookout: lines -> spots in the land's own rows and columns."""
    def spot(r, c, line):
        if not (0 <= r < len(rows) and 0 <= c < len(rows[0])) or rows[r][c] == NOT_HERE:
            raise WorldMapError("%s: '%s' is outside the land" % (where, line))
        return r, c

    if "home" in settings:
        _, (r, c) = _numbers_at_the_end(settings["home"], 2, "home: " + settings["home"], where)
        settings["home"] = spot(r, c, "home: " + settings["home"])
        if rows[r][c] != "H":
            raise WorldMapError("%s: home must be on a house (H)" % where)
    villages, gates, lookouts = [], [], []
    for text in settings.get("village", []):
        line = "village: " + text
        name, (r, c) = _numbers_at_the_end(text, 2, line, where)
        if not name:
            raise WorldMapError("%s: a village needs a name: '%s'" % (where, line))
        villages.append((name, spot(r, c, line)))
    for text in settings.get("gate", []):
        line = "gate: " + text
        name, (r, c, level) = _numbers_at_the_end(text, 3, line, where)
        gates.append((name or "Gate", spot(r, c, line), level))
    for text in settings.get("lookout", []):
        line = "lookout: " + text
        _, (r, c) = _numbers_at_the_end(text, 2, line, where)
        lookouts.append(spot(r, c, line))
    settings["village"], settings["gate"], settings["lookout"] = villages, gates, lookouts


def land_files(folder=None):
    folder = folder or WORLD_FOLDER
    return [os.path.join(folder, name) for name in sorted(os.listdir(folder)) if name.endswith(".txt")]


def stitch(lands_text):
    """[(file name, text), ...] -> an Atlas. Two lands can't both draw the same square."""
    pieces = [(name,) + read_land(text, name) for name, text in lands_text]
    if not pieces:
        raise WorldMapError("There are no land files")
    rows = max(s["top"] + len(drawing) for _, s, drawing in pieces)
    cols = max(s["left"] + len(drawing[0]) for _, s, drawing in pieces)
    grid = [[EMPTY] * cols for _ in range(rows)]
    land_index = [[None] * cols for _ in range(rows)]
    lands, home, villages, gates, lookouts = [], None, [], {}, []
    for name, s, drawing in pieces:
        i = len(lands)
        spots = []
        for dr, row in enumerate(drawing):
            for dc, letter in enumerate(row):
                if letter == NOT_HERE:
                    continue
                r, c = s["top"] + dr, s["left"] + dc
                if land_index[r][c] is not None:
                    raise WorldMapError("%s and %s both draw the square at row %d, column %d"
                                        % (os.path.basename(name), lands[land_index[r][c]][0], r, c))
                grid[r][c] = letter
                land_index[r][c] = i
                spots.append((r, c))
        if not spots:
            raise WorldMapError("%s has no squares (it's all dots)" % name)
        top, bottom = min(r for r, _ in spots), max(r for r, _ in spots)
        left, right = min(c for _, c in spots), max(c for _, c in spots)
        lands.append((s["name"], top, left, bottom, right, s.get("landmark") or None, s.get("says", "")))

        def big(spot):                       # the land's own row and column -> the big map's
            return s["top"] + spot[0], s["left"] + spot[1]
        if "home" in s:
            if home is not None:
                raise WorldMapError("%s: only one land can have a 'home:' line" % os.path.basename(name))
            home = big(s["home"])
        villages += [(village, big(spot), s["name"]) for village, spot in s["village"]]
        gates.update({big(spot): (gate, level) for gate, spot, level in s["gate"]})
        lookouts += [big(spot) for spot in s["lookout"]]
    return Atlas(grid, lands, land_index, home, villages, gates, lookouts)


def load(folder=None):
    """Read every land file in levels/world/ and stitch them into one big map."""
    texts = []
    for path in land_files(folder):
        with open(path, encoding="utf-8") as file:
            texts.append((os.path.basename(path), file.read()))
    return stitch(texts)
