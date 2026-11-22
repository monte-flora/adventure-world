"""Generate levels/realm/*.txt: the 6x5-screen realm (30x17 tiles per screen) + the Umbral Reach.
Run from the worktree root. Then run realm_check.py."""
import random, os, json, sys

SW, SH, NC, NR = 30, 17, 6, 5
H, W = SH * NR, SW * NC
OUT = "levels/realm"
STONE = json.load(open(os.path.join(os.path.dirname(__file__), "stone_files.json")))  # land -> file

SCREENS = {  # land -> screens
    "emberhold": "A3 B2 B3", "weepingwold": "A1 A2 B1", "hollowcrown": "C1 C2 D1",
    "drowned_mere": "C3 C4 D2 D3 D4 E3", "wintermarch": "E1 E2 F1 F2",
    "cinder_wastes": "D5 E4 E5 F3 F4 F5", "mirefen": "A4 A5 B4 B5 C5",
}
ORDER = ["emberhold", "weepingwold", "hollowcrown", "drowned_mere", "wintermarch", "cinder_wastes", "mirefen"]
BASE = {"emberhold": "G", "weepingwold": "G", "hollowcrown": "G", "drowned_mere": "W",
        "wintermarch": "G", "cinder_wastes": "G", "mirefen": "B"}

def scr(name):
    ci, ri = "ABCDEF".index(name[0]), int(name[1]) - 1
    return ri * SH, ci * SW

grid = [["W"] * W for _ in range(H)]
owner = [[None] * W for _ in range(H)]
for land, s in SCREENS.items():
    for n in s.split():
        r0, c0 = scr(n)
        for r in range(r0, r0 + SH):
            for c in range(c0, c0 + SW):
                grid[r][c], owner[r][c] = BASE[land], land

def rect(r0, c0, r1, c1, ch, land=None):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r][c] = ch
            if land:
                owner[r][c] = land

# walls on every boundary between two lands (2 thick: one tile each side)
for r in range(H):
    for c in range(W):
        o = owner[r][c]
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W and owner[rr][cc] != o:
                grid[r][c] = "X"
# outer edge of the realm: rock
for r in range(H):
    grid[r][0] = grid[r][W - 1] = "X"
for c in range(W):
    grid[0][c] = grid[H - 1][c] = "X"

# ---- Drowned Mere: water, with a shore walk (west shore, top strip, corner, north shore) and islands
rect(34, 62, 66, 69, "G")            # west shore (C3, C4)
rect(35, 62, 37, 95, "G")            # top strip of C3 + corner of D3
rect(19, 90, 37, 95, "G")            # west strip of D2
rect(19, 90, 24, 117, "G")           # north shore (D2)
rect(39, 99, 47, 113, "G", "shadowgate")   # the Shadowgate island (its own land)
rect(41, 104, 45, 108, "X", "shadowgate"); rect(42, 105, 44, 107, "G", "shadowgate")
grid[43][106] = "P"; grid[45][106] = "X"     # the Portal in a ring of standing stones; gate tile below
rect(40, 130, 45, 141, "G")          # E3 island
rect(55, 99, 61, 110, "G")           # D4 island
rect(26, 122, 32, 135, "G")          # Wintermarch landing shore is drawn below (E2)

# ---- gates and open passages (both tiles of the 2-thick wall)
def cut_v(row0, row1, col, ch):      # a passage through a vertical wall at col|col+1
    rect(row0, col, row1, col + 1, ch)
def cut_h(col0, col1, row, ch):      # through a horizontal wall at row|row+1
    rect(row, col0, row + 1, col1, ch)

cut_h(10, 15, 33, "G")      # Weepingwold A2 | Emberhold A3
cut_h(40, 45, 16, "R")      # Weepingwold B1 | Emberhold B2
cut_v(24, 28, 29, "R")      # Weepingwold A2 | Emberhold B2
cut_v(23, 27, 59, "Y")      # Emberhold B2 | Hollowcrown C2: ivy cliff (climb)
cut_v(6, 10, 59, "Y")       # Weepingwold B1 | Hollowcrown C1: ivy cliff (climb)
cut_v(40, 44, 59, "O")      # Emberhold B3 | Mere C3: rubble (pound)
cut_h(100, 104, 16, "O")    # Hollowcrown D1 | Mere D2: rubble on the causeway (pound)
cut_h(75, 79, 33, "O")      # Hollowcrown C2 | Mere C3: rubble shortcut (pound)
cut_h(125, 130, 33, "W")    # Mere E3 | Wintermarch E2: open water (swim)
cut_h(10, 14, 50, "K")      # Emberhold A3 | Mirefen A4: shadow thorns (flare)
cut_h(40, 44, 50, "K")      # Emberhold B3 | Mirefen B4: shadow thorns (flare)
cut_v(74, 78, 89, "K")      # Mirefen C5 | Cinder D5: shadow thorns (flare)
GATES = [  # X tiles that open with an ability (not a letter of their own)
    ("Ashen Stair", 33, 165, "double_jump"), ("Ashen Stair", 34, 165, "double_jump"),
    ("Portal Stair", 45, 106, "truesight"),
]
# Wintermarch: water bay on its south edge so the swim lands on the shore
rect(28, 122, 32, 135, "G"); rect(33, 124, 33, 131, "W")
rect(34, 125, 38, 130, "W")

# ---- terrain detail (seeded, only on base ground, never on the gate lanes)
rnd = random.Random(7)
def sprinkle(land, ch, n, size=(1, 3)):
    cells = [(r, c) for r in range(H) for c in range(W) if owner[r][c] == land and grid[r][c] == BASE[land]]
    for _ in range(n):
        r, c = rnd.choice(cells)
        h, w = rnd.randint(*size), rnd.randint(*size)
        for rr in range(r, min(r + h, H)):
            for cc in range(c, min(c + w, W)):
                if owner[rr][cc] == land and grid[rr][cc] == BASE[land]:
                    grid[rr][cc] = ch
sprinkle("emberhold", "F", 25); sprinkle("weepingwold", "F", 160, (2, 4))
sprinkle("hollowcrown", "X", 30, (1, 2)); sprinkle("hollowcrown", "F", 10)
sprinkle("wintermarch", "I", 30, (2, 5)); sprinkle("wintermarch", "X", 30, (1, 3))
sprinkle("cinder_wastes", "X", 40, (1, 2)); sprinkle("cinder_wastes", "V", 25, (1, 1))
sprinkle("mirefen", "W", 35, (2, 4)); sprinkle("mirefen", "G", 30, (2, 3)); sprinkle("mirefen", "F", 15)
# Hollowcrown's broken ring wall round the Watch of Kings (D1)
for c in range(96, 116):
    if c % 5: grid[3][c] = grid[13][c] = "X"
for r in range(3, 14):
    if r % 4: grid[r][96] = grid[r][115] = "X"
# Emberhold: a path from the woods gate down past the waystone to home and the rubble gate
rect(18, 42, 46, 43, "R"); rect(42, 43, 42, 58, "R"); rect(25, 31, 26, 58, "R")
rect(37, 3, 38, 41, "R")

PLACES = {  # land -> list of (kind, row, col, text)
    "emberhold": [("L", 22, 44, None), ("home", 44, 46, None), ("village", 44, 50, "Emberwick"),
                  ("M", 40, 8, STONE["emberhold"]), ("M", 47, 54, "caves/01_the_easy_moss_cave.txt"),
                  ("M", 20, 34, "caves/02_the_vine_garden.txt"), ("T", 47, 4, None), ("+", 32, 42, None)],
    "weepingwold": [("L", 25, 15, None), ("M", 8, 50, STONE["weepingwold"]), ("S", 4, 5, "secret/1_the_secret_mine.txt"),
                    ("M", 10, 20, "caves/03_blue_lvl_1.txt"), ("M", 28, 6, "caves/05_green_lvl_1.txt"), ("T", 2, 27, None)],
    "hollowcrown": [("L", 24, 66, None), ("M", 8, 105, STONE["hollowcrown"]), ("M", 5, 70, "caves/04_the_old_stone_cave.txt"),
                    ("M", 28, 82, "caves/09_the_old_stone_maze.txt"), ("T", 30, 64, None)],
    "drowned_mere": [("L", 21, 110, None), ("M", 64, 65, STONE["drowned_mere"]), ("M", 42, 137, "caves/10_green_lvl_2.txt"),
                     ("M", 58, 105, "caves/12_the_crystal_cave.txt"), ("T", 60, 100, None)],
    "shadowgate": [],
    "wintermarch": [("L", 30, 128, None), ("M", 5, 170, STONE["wintermarch"]), ("M", 6, 130, "caves/06_the_icy_steps.txt"),
                    ("M", 25, 160, "caves/13_the_frozen_falls.txt"), ("M", 12, 140, "caves/16_the_glacier_crossing.txt"), ("T", 14, 175, None)],
    "cinder_wastes": [("L", 38, 165, None), ("M", 78, 130, STONE["cinder_wastes"]), ("M", 55, 170, "caves/07_red_lvl_1.txt"),
                      ("M", 56, 130, "caves/08_the_lava_cave.txt"), ("M", 78, 170, "caves/11_the_lava_escape.txt"),
                      ("M", 75, 100, "caves/17_the_fire_mountain.txt"), ("T", 82, 155, None)],
    "mirefen": [("L", 55, 42, None), ("M", 80, 8, STONE["mirefen"]), ("M", 76, 75, "caves/14_the_scorching_swings.txt"),
                ("M", 58, 10, "caves/15_the_icicle_tunnels.txt"), ("T", 70, 50, None)],
}
for land, ps in PLACES.items():
    for kind, r, c, _ in ps:
        assert owner[r][c] == land, (land, kind, r, c, owner[r][c])
        if kind in ("home",):
            grid[r][c] = "H"
        elif kind == "village":
            for dr, dc in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
                grid[r + dr][c + dc] = "H"
            grid[r][c] = "R"
        else:
            grid[r][c] = kind
        for dr in (-1, 0, 1):              # clear ground round every place
            for dc in (-1, 0, 1):
                if (dr or dc) and grid[r + dr][c + dc] in "XFWIVB" and owner[r + dr][c + dc] == land:
                    grid[r + dr][c + dc] = "G"

# Weepingwold's Light Stone Mine sits past the Riven Gap: a gap only a dash crosses
rect(6, 48, 10, 52, "X"); rect(7, 49, 9, 51, "G"); grid[8][50] = "M"
GATES.append(("Riven Gap", 10, 50, "dash"))

TEXT = {
    "emberhold": dict(file="1_emberhold.txt", landmark="The Ember Beacon",
        says="The last hearth fire of the realm still burns here. Light the beacon and find the first Light Stone.",
        about="Home. Open from the start: the Weepingwold. Ivy cliffs (Y) to Hollowcrown, rubble (O) to the Mere, thorns (K) to the Mirefen: you see all three from here."),
    "weepingwold": dict(file="2_weepingwold.txt", landmark="The Grieving Oak", dark="A1",
        says="The trees weep black sap. Something old sleeps under their roots.",
        about="Deepwood (A1) is dark. The Secret Mine is in the Deepwood. Ivy cliff (Y) on the east edge up to Hollowcrown."),
    "hollowcrown": dict(file="3_hollowcrown.txt", landmark="The Watch of Kings",
        says="Broken towers of a fallen kingdom. Its crown was never found.",
        about="Up the ivy cliffs. The Watch of Kings is the ring wall in D1. Rubble (O) on the causeway south to the Mere."),
    "drowned_mere": dict(file="4_drowned_mere.txt", landmark="The Drowned Lighthouse",
        says="A whole city lies under this black water. The bells still ring below.",
        about="A lake round the Shadowgate. Walk the west and north shores; swim for the islands and the bay to the Wintermarch."),
    "shadowgate": dict(file="5_shadowgate.txt", landmark=None,
        says="The Gate the Shadow King came through. Seven stones wake it.",
        about="The island in the middle of the Mere (D3). The Portal (P) sits in a ring of standing stones: truesight shows the way in."),
    "wintermarch": dict(file="6_wintermarch.txt", landmark="The Frozen Throne",
        says="Wind and ice. The old kings of winter watch from the peaks.",
        about="Swim the bay from the Mere. The Ashen Stair (F2, south edge) is a ledge too high without a double jump."),
    "cinder_wastes": dict(file="7_cinder_wastes.txt", landmark="The Wyrm's Ribs",
        says="Ash falls like snow. The ground is hot under your boots.",
        about="Down the Ashen Stair from the Wintermarch. Steam vents (V). Thorns (K) on the west edge to the Mirefen."),
    "mirefen": dict(file="8_mirefen.txt", landmark="The Hanged Witch's Hut",
        says="Mist, reeds and black pools. Lights move out there that are not lanterns.",
        about="Behind shadow thorns (K) from Emberhold and the Cinder Wastes. The last Light Stone is in the far south west."),
}

def screens_of(land):
    return SCREENS.get(land, "D3")

def write_land(land):
    cells = [(r, c) for r in range(H) for c in range(W) if owner[r][c] == land]
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    bottom, right = max(r for r, _ in cells), max(c for _, c in cells)
    t = TEXT[land]
    lines = ["land: " + land, "at: %d %d" % (top, left), "screens: " + screens_of(land)]
    if t.get("landmark"):
        lines.append("landmark: " + t["landmark"])
    lines += ["says: " + t["says"], "about: " + t["about"]]
    if t.get("dark"):
        lines.append("dark: " + t["dark"])
    for kind, r, c, text in PLACES[land]:
        if kind == "home":
            lines.append("home: %d %d" % (r - top, c - left))
        elif kind == "village":
            lines.append("village: %s %d %d" % (text, r - top, c - left))
        elif kind in "MS":
            lines.append("mine: %s %d %d" % (text, r - top, c - left))
    for name, r, c, ability in GATES:
        if owner[r][c] == land:
            lines.append("gate: %s %d %d %s" % (name, r - top, c - left, ability))
    for r in range(top, bottom + 1):
        lines.append("".join(grid[r][c] if owner[r][c] == land else "." for c in range(left, right + 1)))
    open(os.path.join(OUT, t["file"]), "w").write("\n".join(lines) + "\n")

os.makedirs(OUT, exist_ok=True)
for land in TEXT:
    write_land(land)
json.dump({"grid": ["".join(r) for r in grid], "owner": [[o for o in row] for row in owner],
           "places": PLACES, "gates": GATES}, open(os.path.join(os.path.dirname(__file__), "realm.json"), "w"))

# ---- the Umbral Reach: the 3x3 mirror of C2-E4 (same footprint, other terrain)
RH, RW = 3 * SH, 3 * SW
u = [["X" if r in (0, RH - 1) or c in (0, RW - 1) else "G" for c in range(RW)] for r in range(RH)]
rnd = random.Random(13)
for _ in range(120):
    r, c = rnd.randint(2, RH - 4), rnd.randint(2, RW - 4)
    ch = rnd.choice("FFXBW")
    for rr in range(r, r + rnd.randint(1, 3)):
        for cc in range(c, c + rnd.randint(1, 3)):
            u[rr][cc] = ch
# the mirror of the Mere: a dead black lake ring round the centre, crossed by 4 causeways
for r in range(SH - 2, 2 * SH + 2):
    for c in range(SW - 2, 2 * SW + 2):
        if not (SH + 1 <= r <= 2 * SH - 2 and SW + 1 <= c <= 2 * SW - 2):
            u[r][c] = "W"
for r in range(SH - 2, 2 * SH + 2):
    u[r][44] = u[r][45] = "#"
for c in range(SW - 2, 2 * SW + 2):
    u[25][c] = u[26][c] = "#"
for r in range(SH + 1, 2 * SH - 1):
    for c in range(SW + 1, 2 * SW - 1):
        u[r][c] = "G"
rect_u = lambda r0, c0, r1, c1, ch: [u[r].__setitem__(c, ch) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
UPL = [("P", 25, 38, None), ("C", 22, 45, None), ("L", 28, 50, None),
       ("M", 8, 10, "shadow/1_the_whisper_hollow.txt"), ("M", 8, 80, "shadow/2_the_hollow_stair.txt"),
       ("M", 44, 12, "shadow/3_the_shadow_throne_stairs.txt"), ("T", 44, 80, None)]
for kind, r, c, _ in UPL:
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if u[r + dr][c + dc] in "XFWB":
                u[r + dr][c + dc] = "G"
    u[r][c] = kind
lines = ["land: umbral_reach", "world: umbral_reach", "at: %d %d" % (SH, 2 * SW), "mirror: C2 D2 E2 C3 D3 E3 C4 D4 E4",
         "landmark: The Weeping Throne",
         "says: The same land, drowned in shadow. The castle of the Shadow King stands where the Gate stood.",
         "about: Nightfall's place. The 3 x 3 mirror of the screens round the Shadowgate. You arrive at the Portal (P); the castle (C) is the Shadow King's (castle/1 to 5).",
         "dark: yes", "castle: castle/1_the_gate_and_the_lava_moat.txt 22 45"]
for kind, r, c, text in UPL:
    if kind == "M":
        lines.append("mine: %s %d %d" % (text, r, c))
lines += ["".join(row) for row in u]
open(os.path.join(OUT, "9_umbral_reach.txt"), "w").write("\n".join(lines) + "\n")
json.dump(["".join(r) for r in u], open(os.path.join(os.path.dirname(__file__), "umbral.json"), "w"))
print("ok")
