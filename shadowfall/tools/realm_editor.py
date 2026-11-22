"""The prop editor: place, move and delete props (trees, houses, lampposts ...) on a realm land.

    pixi run realm-editor                                 # Emberhold
    pixi run realm-editor levels/realm/2_weepingwold.txt  # (or: python editor.py --realm <file>)

Pick a prop on the right. Left-click the map: put it there (on the nearest half square).
Drag a prop: move it. Right-click a prop: delete it. Arrows / mouse wheel: scroll. +/-: zoom.
S: save (only the `prop:` lines change; everything else in the file stays as you wrote it). ESC: quit.
The art comes from shadowfall/realm/props/ (pixi run import-art); levels/realm/README.md has the format.
"""

import json
import os
import sys

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")      # never any sound from a tool
import pygame  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROPS = os.path.join(ROOT, "shadowfall", "realm", "props")
ASSETS = os.path.join(ROOT, "shadowfall", "realm", "gemini", "assets.json")
DEFAULT = os.path.join(ROOT, "levels", "realm", "1_emberhold.txt")
TILE = 32
PANEL = 180
LETTER = {"G": (60, 84, 52), "F": (36, 62, 40), "R": (128, 92, 60), "X": (70, 66, 86), "W": (50, 80, 120),
          "H": (170, 130, 90), "M": (30, 26, 34), "L": (230, 200, 120), "Y": (60, 120, 60), "O": (120, 110, 100),
          "K": (110, 50, 120), "T": (200, 160, 60), "+": (200, 180, 140), ".": (20, 24, 40)}


# ----- the file: plain functions, so the tests need no window -----

def read_props(text):
    """[(name, row, col)] from a land file's `prop:` lines, in order."""
    out = []
    for line in text.splitlines():
        key, sep, val = line.partition(":")
        if sep and key.strip() == "prop":
            parts = val.split()
            if len(parts) == 3:
                try:
                    out.append((parts[0], float(parts[1]), float(parts[2])))
                except ValueError:
                    pass
    return out


def num(v):
    """12.0 -> '12', 12.5 -> '12.5'."""
    return str(int(v)) if float(v) == int(v) else ("%g" % v)


def write_props(text, props):
    """The file with its `prop:` lines replaced by props (where the first one was, else just before the
    drawing). Every other line stays exactly as it was."""
    lines = text.split("\n")
    new = ["prop: %s %s %s" % (n, num(r), num(c)) for n, r, c in props]
    out, placed = [], False
    for line in lines:
        key, sep, _ = line.partition(":")
        if sep and key.strip() == "prop":
            if not placed:
                out += new
                placed = True
            continue
        if not placed and line.strip() and ":" not in line:      # the drawing starts
            out += new
            placed = True
        out.append(line)
    if not placed:
        out += new
    return "\n".join(out)


def grid(text):
    return [line.strip() for line in text.splitlines() if line.strip() and ":" not in line]


def load_meta(name):
    p = os.path.join(PROPS, name + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def prop_rect(meta, row, col, zoom=1.0):
    """The prop's picture on the map, in map px at zoom (1.0 = game pixels)."""
    ax, ay = meta["anchor"]
    x, y = (col + 0.5) * TILE - ax, (row + 0.5) * TILE - ay
    return pygame.Rect(round(x * zoom), round(y * zoom), round(meta["size"][0] * zoom), round(meta["size"][1] * zoom))


def snap(v):
    return round(v * 2) / 2


class RealmEditor:
    def __init__(self, path=DEFAULT, size=(1180, 640)):
        self.path = path
        self.text = open(path).read()
        self.rows = grid(self.text)
        self.props = read_props(self.text)
        self.names = list(json.load(open(ASSETS))["props"])
        self.meta = {n: load_meta(n) for n in self.names}
        self.pick = self.names[0]
        self.zoom = 0.5
        self.scroll = [0, 0]
        self.drag = None
        self.saved = True
        self.size = size
        self.msg = "Pick a prop, click the map. Drag: move. Right-click: delete. S: save."
        self._art = {}

    # --- editing (what the mouse does; the tests call these) ---
    def to_cell(self, pos):
        x, y = (pos[0] + self.scroll[0]) / self.zoom / TILE - 0.5, (pos[1] + self.scroll[1]) / self.zoom / TILE - 0.5
        return snap(y), snap(x)

    def prop_at(self, pos):
        """Index of the top-most prop under a screen point, or None."""
        mx, my = pos[0] + self.scroll[0], pos[1] + self.scroll[1]
        best = None
        for i, (n, r, c) in enumerate(self.props):
            m = self.meta.get(n)
            if m and prop_rect(m, r, c, self.zoom).collidepoint(mx, my):
                if best is None or self.props[best][1] <= r:
                    best = i
        return best

    def place(self, pos, name=None):
        r, c = self.to_cell(pos)
        self.props.append((name or self.pick, r, c))
        self.saved = False

    def move(self, i, pos):
        r, c = self.to_cell(pos)
        self.props[i] = (self.props[i][0], r, c)
        self.saved = False

    def delete(self, i):
        del self.props[i]
        self.saved = False

    def save(self):
        self.text = write_props(self.text, self.props)
        with open(self.path, "w") as f:
            f.write(self.text)
        self.saved = True
        self.msg = "Saved %d props to %s" % (len(self.props), os.path.relpath(self.path, ROOT))

    # --- drawing ---
    def art(self, name):
        key = (name, self.zoom)
        if key not in self._art:
            p = os.path.join(PROPS, name + ".png")
            img = pygame.image.load(p).convert_alpha() if os.path.exists(p) else None
            if img:
                img = pygame.transform.scale(img, (max(1, round(img.get_width() * self.zoom)), max(1, round(img.get_height() * self.zoom))))
            self._art[key] = img
        return self._art[key]

    def draw(self, screen, font):
        screen.fill((16, 16, 22))
        s = TILE * self.zoom
        for r, row in enumerate(self.rows):
            for c, ch in enumerate(row):
                pygame.draw.rect(screen, LETTER.get(ch, (90, 90, 90)),
                                 (c * s - self.scroll[0], r * s - self.scroll[1], s + 1, s + 1))
        for n, r, c in sorted(self.props, key=lambda p: p[1]):
            m, img = self.meta.get(n), self.art(n)
            if m and img:
                rect = prop_rect(m, r, c, self.zoom).move(-self.scroll[0], -self.scroll[1])
                screen.blit(img, rect)
        w, h = screen.get_size()
        pygame.draw.rect(screen, (30, 28, 36), (w - PANEL, 0, PANEL, h))
        for i, n in enumerate(self.names):
            y = 8 + i * 30
            if n == self.pick:
                pygame.draw.rect(screen, (90, 80, 40), (w - PANEL + 4, y - 2, PANEL - 8, 28))
            screen.blit(font.render(n, True, (230, 225, 210)), (w - PANEL + 10, y + 4))
        screen.blit(font.render(self.msg + ("" if self.saved else "   (not saved)"), True, (240, 220, 140)), (8, h - 22))

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)
        pygame.display.set_caption("Prop editor: " + os.path.basename(self.path))
        font = pygame.font.SysFont(None, 22)
        clock = pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    return
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_s:
                        self.save()
                    elif e.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_MINUS):
                        self.zoom = min(2.0, self.zoom * 2) if e.key != pygame.K_MINUS else max(0.25, self.zoom / 2)
                    step = {pygame.K_LEFT: (-64, 0), pygame.K_RIGHT: (64, 0), pygame.K_UP: (0, -64), pygame.K_DOWN: (0, 64)}
                    if e.key in step:
                        self.scroll = [self.scroll[0] + step[e.key][0], self.scroll[1] + step[e.key][1]]
                if e.type == pygame.MOUSEWHEEL:
                    self.scroll = [self.scroll[0] - e.x * 32, self.scroll[1] - e.y * 32]
                if e.type == pygame.MOUSEBUTTONDOWN and e.button in (1, 3):
                    w = screen.get_width()
                    if e.pos[0] >= w - PANEL:
                        i = (e.pos[1] - 6) // 30
                        if 0 <= i < len(self.names):
                            self.pick = self.names[i]
                        continue
                    i = self.prop_at(e.pos)
                    if e.button == 3 and i is not None:
                        self.msg = "Deleted " + self.props[i][0]
                        self.delete(i)
                    elif e.button == 1 and i is not None:
                        self.drag = i
                    elif e.button == 1:
                        self.place(e.pos)
                        self.msg = "Put a %s at row %s, column %s" % (self.pick, num(self.props[-1][1]), num(self.props[-1][2]))
                if e.type == pygame.MOUSEMOTION and self.drag is not None:
                    self.move(self.drag, e.pos)
                if e.type == pygame.MOUSEBUTTONUP:
                    self.drag = None
            self.draw(screen, font)
            pygame.display.flip()
            clock.tick(30)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = os.path.abspath(argv[0]) if argv else DEFAULT
    RealmEditor(path).run()


if __name__ == "__main__":
    main()
