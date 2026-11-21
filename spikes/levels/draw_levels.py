"""Draw the Wave A level-design figures into docs/teen/levels/ (pygame only, no window).

    python spikes/levels/draw_levels.py

- overworld.png: the proposed Shadowfall overworld, a 6 x 5 grid of screens.
- cave_01.png ... cave_03.png: side views of the 3 cave drafts in docs/teen/levels/drafts/,
  with the beats (teach, test, twist, finale, secret, checkpoints) marked over them.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "docs", "teen", "levels")
DRAFTS = os.path.join(OUT, "drafts")

INK = (230, 226, 240)
DIM = (150, 146, 170)
BG = (16, 14, 24)

# ---------------------------------------------------------------- overworld
LANDS = {  # code: (name, Light Stone, ability it gives, colour)
    "H": ("Hearthvale (Home Meadow)", "Dawn Stone", "Lantern", (88, 120, 70)),
    "W": ("Whispering Woods", "Leaf Stone", "Climb", (40, 84, 52)),
    "R": ("Old Ruins", "Crown Stone", "Pound", (112, 104, 92)),
    "L": ("The Great Lake", "Tide Stone", "Sail", (40, 74, 120)),
    "F": ("Frost Peaks", "Frost Stone", "Frostward", (150, 170, 190)),
    "D": ("Sunscorch Desert", "Sun Stone", "Sunflare", (170, 120, 60)),
    "S": ("Murk Swamp", "Moon Stone", "Moonsight", (70, 80, 64)),
    "P": ("Portal Island", None, None, (90, 60, 120)),
}
GRID = ["WWRRFF",
        "WHRLFF",
        "HHLPLD",
        "SSLLDD",
        "SSSDDD"]
SCREEN = (200, 120)          # pixels per overworld screen in the figure (one screen = 30 x 17 tiles of 32 px (960 x 540))
TOP, LEFT = 60, 40
# (row, col, text) of things in a screen
STONE_CAVES = {(2, 0): "1", (0, 0): "2", (0, 3): "3", (1, 3): "4", (0, 5): "5", (3, 5): "6", (4, 0): "7"}
SIDE_CAVES = [(1, 1), (2, 1), (0, 1), (1, 0), (0, 2), (1, 2), (2, 2), (3, 3), (1, 4), (1, 5), (2, 5), (4, 4),
              (4, 3), (3, 1), (4, 2)]
WAYSTONES = [(2, 1), (0, 1), (1, 2), (3, 2), (1, 4), (3, 4), (3, 0)]
SECRETS = [(0, 0), (4, 5)]
LANDMARKS = {(2, 1): "home", (0, 1): "Queen Oak", (0, 2): "Watchtower", (2, 4): "Lighthouse",
             (0, 4): "Frost Peak", (4, 4): "Dragon Bones", (4, 1): "Frog's Hut", (2, 3): "PORTAL"}
# gates: (row, col, side, ability) - a wall on that side of the screen until you have the ability
GATES = [(1, 0, "N", "Lantern"), (0, 0, "E", "Lantern"),          # Deepwood (A1) is pitch dark
         (0, 1, "E", "Climb"), (1, 1, "E", "Climb"),                # ivy cliffs up to the Ruins plateau
         (1, 2, "E", "Pound"),                                     # rubble on the old causeway to the north shore
         (0, 3, "S", "wall"), (0, 3, "E", "wall"),                 # sheer cliffs: no way down to the lake or the peaks
         (2, 2, "E", "Sail"), (1, 3, "E", "Sail"), (2, 2, "S", "Sail"),   # open water
         (1, 5, "S", "Frostward"), (2, 4, "E", "Frostward"), (2, 4, "S", "Frostward"),
         (3, 3, "E", "Frostward"), (3, 3, "S", "Frostward"),        # the heat of Sunscorch, all round
         (2, 0, "S", "Sunflare"), (2, 1, "S", "Sunflare"), (3, 1, "E", "Sunflare"), (4, 2, "N", "Sunflare"),
         (4, 3, "W", "Sunflare")]                                  # thorns all round the Murk
ROUTE = [(2, 1), (2, 0), (1, 0), (0, 0), (0, 1), (0, 2), (0, 3), (0, 2), (1, 2), (1, 3), (1, 4), (0, 4), (0, 5),
         (1, 5), (2, 5), (3, 5), (4, 5), (4, 4), (4, 3), (4, 2), (4, 1), (4, 0), (3, 0), (2, 0), (2, 1), (2, 2),
         (2, 3)]


def centre(r, c, dx=0, dy=0):
    return (LEFT + c * SCREEN[0] + SCREEN[0] // 2 + dx, TOP + r * SCREEN[1] + SCREEN[1] // 2 + dy)


def draw_overworld(font, small):
    w, h = LEFT * 2 + 6 * SCREEN[0] + 330, TOP + 5 * SCREEN[1] + 150
    s = pygame.Surface((w, h))
    s.fill(BG)
    s.blit(font.render("Shadowfall overworld (proposal): 6 x 5 screens, one screen = 30 x 17 tiles of 32 px (960 x 540)", True, INK), (LEFT, 18))
    for r, row in enumerate(GRID):
        for c, code in enumerate(row):
            rect = pygame.Rect(LEFT + c * SCREEN[0], TOP + r * SCREEN[1], SCREEN[0], SCREEN[1])
            pygame.draw.rect(s, LANDS[code][3], rect)
            pygame.draw.rect(s, BG, rect, 1)
            s.blit(small.render("%s%d" % ("ABCDEF"[c], r + 1), True, DIM), (rect.x + 4, rect.y + 3))
    # land names once, in their first screen
    seen = set()
    for r, row in enumerate(GRID):
        for c, code in enumerate(row):
            if code not in seen:
                seen.add(code)
                s.blit(small.render(LANDS[code][0].split(" (")[0], True, INK), (LEFT + c * SCREEN[0] + 30, TOP + r * SCREEN[1] + 3))
    # route
    pts = [centre(r, c, 0, 18) for r, c in ROUTE]
    pts = [(x + 3 * (i % 3), y + 3 * (i % 3)) for i, (x, y) in enumerate(pts)]
    pygame.draw.lines(s, (240, 210, 120), False, pts, 2)
    for r, c in WAYSTONES:
        x, y = centre(r, c, -70, 0)
        pygame.draw.polygon(s, (120, 220, 255), [(x, y - 9), (x + 6, y), (x, y + 9), (x - 6, y)])
    for (r, c), name in LANDMARKS.items():
        s.blit(small.render(name, True, (255, 240, 200)), centre(r, c, -40, -28))
    for (r, c), n in STONE_CAVES.items():
        x, y = centre(r, c, 40, -2)
        pygame.draw.circle(s, (255, 220, 90), (x, y), 13)
        s.blit(font.render(n, True, BG), (x - 5, y - 10))
    for i, (r, c) in enumerate(SIDE_CAVES):
        x, y = centre(r, c, 72, 30)
        pygame.draw.rect(s, (30, 26, 36), (x - 7, y - 7, 14, 14))
        pygame.draw.rect(s, INK, (x - 7, y - 7, 14, 14), 1)
    for r, c in SECRETS:
        s.blit(font.render("?", True, (255, 120, 200)), centre(r, c, -90, 20))
    colours = {"Lantern": (255, 200, 80), "Climb": (90, 220, 90), "Pound": (200, 160, 120), "Sail": (90, 170, 255),
               "Frostward": (220, 240, 255), "Sunflare": (255, 110, 60), "wall": (20, 18, 26)}
    for r, c, side, ability in GATES:
        x0, y0 = LEFT + c * SCREEN[0], TOP + r * SCREEN[1]
        x1, y1 = x0 + SCREEN[0], y0 + SCREEN[1]
        line = {"N": ((x0 + 20, y0), (x1 - 20, y0)), "S": ((x0 + 20, y1), (x1 - 20, y1)),
                "E": ((x1, y0 + 15), (x1, y1 - 15)), "W": ((x0, y0 + 15), (x0, y1 - 15))}[side]
        pygame.draw.line(s, colours[ability], *line, 7)
    # Portal
    x, y = centre(2, 3)
    pygame.draw.circle(s, (200, 120, 255), (x, y), 22, 4)
    # legend
    lx, ly = LEFT + 6 * SCREEN[0] + 24, TOP
    s.blit(font.render("Legend", True, INK), (lx, ly))
    rows = [("circle n", "Light Stone cave n (big, 3 checkpoints)"), ("square", "side cave (short: today's caves)"),
            ("diamond", "waystone (map + fast travel)"), ("?", "secret (Moonsight shows it)"),
            ("yellow line", "main route, Home to the Portal")]
    for i, (k, v) in enumerate(rows):
        s.blit(small.render("%-12s %s" % (k, v), True, DIM), (lx, ly + 28 + i * 18))
    s.blit(font.render("Gates (wall until you have it)", True, INK), (lx, ly + 130))
    for i, (ab, col) in enumerate(colours.items()):
        pygame.draw.line(s, col, (lx, ly + 166 + i * 22), (lx + 30, ly + 166 + i * 22), 7)
        src = [v[1] for v in LANDS.values() if v[2] == ab] or ["never: a cliff"]
        s.blit(small.render("%s (%s)" % (ab, src[0]), True, DIM), (lx + 40, ly + 158 + i * 22))
    s.blit(small.render("Moonsight (Moon Stone): shows secret walls and the", True, DIM), (lx, ly + 322))
    s.blit(small.render("hidden ? caves; all 7 Stones wake the Portal.", True, DIM), (lx, ly + 338))
    s.blit(small.render("Through the Portal: Nightfall Hollow, a dark mirror", True, DIM), (lx, ly + 368))
    s.blit(small.render("of screens C2-E4 (3 x 3), then the Shadow Castle.", True, DIM), (lx, ly + 384))
    y = TOP + 5 * SCREEN[1] + 16
    order = " -> ".join("%s (%s)" % (LANDS[k][1].split()[0], LANDS[k][2]) for k in "HWRLFDS")
    s.blit(small.render("Order: " + order + " -> Portal", True, INK), (LEFT, y))
    s.blit(small.render("Every gate is seen at least one land before its ability; each ability also opens shortcuts "
                        "(Climb: cliff Ruins->Home, Sail: Lake->Home, Sunflare: thorn path in the Woods).", True, DIM),
           (LEFT, y + 20))
    pygame.image.save(s, os.path.join(OUT, "overworld.png"))


# ---------------------------------------------------------------- caves
TILE_COLOURS = {"#": (58, 52, 72), ".": (22, 20, 32), "B": (120, 96, 70), "*": (120, 230, 255), "=": (170, 150, 110),
                "-": (200, 140, 90), "^": (220, 220, 230), "A": (230, 150, 150), "!": (255, 120, 40),
                "~": (255, 80, 20), "T": (230, 190, 60), "$": (120, 255, 160), "S": (90, 200, 255),
                "E": (255, 255, 255), "H": (160, 120, 60), "F": (90, 70, 100), "L": (255, 220, 0),
                "G": (140, 140, 160), "J": (255, 150, 60), "M": (200, 200, 220), "u": (80, 160, 255),
                "C": (255, 230, 120), "z": (120, 200, 90), "k": (230, 230, 210), "c": (255, 100, 60),
                "x": (160, 90, 200)}
# beats per draft: (first col, last col, first row, last row, label); rows/cols are the drawing's
BEATS = {
    "01": [(1, 27, 12, 18, "1 TEACH crumbly ledge over safe floor"), (30, 62, 12, 18, "2 TEST crumbly stones over spikes"),
           (88, 98, 2, 18, "3 TWIST crumbling climb (falls are safe)"), (24, 87, 2, 6, "4 FINALE low tunnel, back LEFT"),
           (1, 6, 2, 6, "SECRET false wall F, gem hint"), (8, 22, 6, 10, "LOOP lever opens gate: exit by start")],
    "02": [(1, 34, 1, 4, "1 TEACH cracked floor, safe room below"), (1, 35, 13, 18, "2 TEST double floor + spikes"),
           (1, 35, 21, 25, "3 TWIST dig sideways under spike traps"), (1, 35, 27, 35, "4 FINALE dig out the Crown Stone"),
           (1, 4, 6, 11, "SECRET false wall F"), (36, 38, 1, 35, "LOOP lever -> gate -> ladder to exit")],
    "03": [(1, 23, 10, 20, "1 TEACH geyser over a pillar"), (28, 60, 10, 20, "2 TEST geysers in a lava lake"),
           (69, 84, 1, 20, "3 TWIST geyser shaft, flame jets"), (80, 108, 6, 20, "4 FINALE Sun Stone, lava rises"),
           (22, 29, 21, 24, "SECRET cracked floor by checkpoint 1")],
}
BEAT_COLOURS = {"1": (90, 220, 120), "2": (240, 210, 90), "3": (255, 140, 60), "4": (255, 80, 120),
                "S": (255, 120, 220), "L": (120, 200, 255)}


def read_draft(path):
    head, rows = {}, []
    for line in open(path).read().splitlines():
        if ":" in line and not rows:
            k, v = line.split(":", 1)
            head[k.strip()] = v.strip()
        elif line:
            rows.append(line)
    return head, rows


def draw_cave(path, key, font, small):
    head, rows = read_draft(path)
    t = 10 if len(rows[0]) > 60 else 16
    w, h = len(rows[0]) * t + 40, len(rows) * t + 120
    s = pygame.Surface((max(w + 220, 900), h))
    s.fill(BG)
    s.blit(font.render("%s  -  %s, %s, needs: %s" % (head["name"], head.get("stone"), head["theme"], head.get("needs")),
                       True, INK), (20, 10))
    oy = 40
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            col = TILE_COLOURS.get(ch, (255, 0, 255))
            rect = (20 + c * t, oy + r * t, t, t)
            if ch in "#.":
                pygame.draw.rect(s, col, rect)
            else:
                pygame.draw.rect(s, TILE_COLOURS["." if ch not in "#B*=-~HFGMJ" else ch], rect)
                if ch in "$TSELCuzkcxA^!":
                    pygame.draw.rect(s, TILE_COLOURS["."], rect)
                    pygame.draw.circle(s, col, (rect[0] + t // 2, rect[1] + t // 2), t // 2 - 1)
                    if ch == "C":
                        s.blit(small.render("C", True, BG), (rect[0] + 1, rect[1] - 2))
    for i, (c0, c1, r0, r1, label) in enumerate(BEATS[key]):
        col = BEAT_COLOURS[label[0]]
        rect = pygame.Rect(20 + c0 * t, oy + r0 * t, (c1 - c0 + 1) * t, (r1 - r0 + 1) * t)
        pygame.draw.rect(s, col, rect, 2)
        img = small.render(label, True, col)
        s.blit(img, (rect.x + 3, rect.y + 2 + 14 * (i % 2 and rect.h > 60)))
    s.blit(small.render("Dots: S start (blue), E exit (white), C checkpoint (yellow, new letter), $ gem (green), T chest, "
                        "u spring, ^ spikes, monsters.  Boxes: the beats, in order 1-4.", True, DIM), (20, h - 60))
    s.blit(small.render("Drawn from docs/teen/levels/drafts/%s; the robot (cave_solver.py) checks it." % os.path.basename(path),
                        True, DIM), (20, h - 42))
    pygame.image.save(s, os.path.join(OUT, "cave_%s.png" % key))


def main():
    pygame.font.init()
    font = pygame.font.SysFont("dejavusans,arial", 18, bold=True)
    small = pygame.font.SysFont("dejavusans,arial", 13)
    draw_overworld(font, small)
    for name in sorted(os.listdir(DRAFTS)):
        if name.endswith(".txt"):
            draw_cave(os.path.join(DRAFTS, name), name[:2], font, small)


if __name__ == "__main__":
    main()
