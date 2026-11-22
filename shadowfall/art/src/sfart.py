"""Shadowfall art kit: the Shadowfall 32 palette, a sheet packer and pixel helpers (pygame).

Every asset in shadowfall/art is drawn by code in this folder (all original). Rebuild:
    python shadowfall/art/src/make_all.py
Spec: docs/teen/art/README.md (sizes doubled for the 32-px tile pick).
"""
import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

pygame.init()

ART = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TILE = 32

# Shadowfall 32 (same as spikes/art/sf_art.py). Ramps run dark -> light.
RAMPS = {
    "ink":    ["#0b0a12", "#1a1626", "#2b2540", "#463d5e", "#6b6187", "#9c93b0", "#d6d0e0", "#f4f1ea"],
    "moss":   ["#12261f", "#1f4031", "#2f6142", "#4f8a4b", "#8bbd5a"],
    "earth":  ["#2a1b17", "#4a2f25", "#74482f", "#a8703f", "#d9a95f"],
    "water":  ["#0f1d33", "#1b3557", "#2c5a85", "#4a8fb8", "#8fd0e0"],
    "ember":  ["#3d0f1f", "#7a1c2e", "#c23a3a", "#f0784a"],
    "light":  ["#f7c64a", "#fff2a8"],
    "shadow": ["#2a0f3d", "#5a1f78", "#a04ce0"],
}
NAMES = [f"{n}{i}" for n, r in RAMPS.items() for i in range(len(r))]
HEX = [c for r in RAMPS.values() for c in r]
assert len(HEX) == 32 and len(set(HEX)) == 32


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


P = {n: rgb(c) for n, c in zip(NAMES, HEX)}
SET = set(P.values())


def c(name):
    """A palette colour by name ('moss2'); passes tuples through."""
    return P[name] if isinstance(name, str) else name


def surf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


# --- drawing (never anti-aliased, so only palette colours land) ---------------------------
def rect(s, col, x, y, w, h):
    pygame.draw.rect(s, c(col), (round(x), round(y), round(w), round(h)))


def px(s, col, x, y):
    x, y = round(x), round(y)
    if 0 <= x < s.get_width() and 0 <= y < s.get_height():
        s.set_at((x, y), c(col))


def ellipse(s, col, x, y, w, h):
    pygame.draw.ellipse(s, c(col), (round(x), round(y), max(1, round(w)), max(1, round(h))))


def circle(s, col, x, y, r):
    pygame.draw.circle(s, c(col), (round(x), round(y)), max(1, round(r)))


def poly(s, col, pts):
    pygame.draw.polygon(s, c(col), [(round(a), round(b)) for a, b in pts])


def line(s, col, a, b, w=1):
    pygame.draw.line(s, c(col), (round(a[0]), round(a[1])), (round(b[0]), round(b[1])), w)


def grid(rows, key, s=None, ox=0, oy=0):
    """Letter rows -> pixels ('.' clear). key maps a letter to a palette name."""
    if s is None:
        s = surf(max(len(r) for r in rows), len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                px(s, key[ch], ox + x, oy + y)
    return s


def outline(s, col="ink0"):
    """The 1-px ink outline rule: every clear pixel touching a filled one (4-way) turns ink."""
    w, h = s.get_size()
    out = s.copy()
    m = pygame.mask.from_surface(s, 1)
    for y in range(h):
        for x in range(w):
            if m.get_at((x, y)):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and m.get_at((nx, ny)):
                    out.set_at((x, y), c(col))
                    break
    return out


def recolour(s, mapping):
    """Swap palette colours by name: {'water2': 'moss2'}."""
    out = s.copy()
    arr = pygame.PixelArray(out)
    for a, b in mapping.items():
        arr.replace(c(a), c(b))
    del arr
    return out


def flash(s, col="ink7"):
    """Hurt frame: every filled pixel one colour (a flash, never alpha)."""
    out = s.copy()
    m = pygame.mask.from_surface(s, 1)
    for y in range(s.get_height()):
        for x in range(s.get_width()):
            if m.get_at((x, y)):
                out.set_at((x, y), c(col))
    return out


def poof(w, h, k, n=4, seed=1):
    """Smoke poof frame k of n (defeated monsters burst into smoke, never gore)."""
    import random
    rnd = random.Random(seed)
    s = surf(w, h)
    cx, cy = w / 2, h * 0.6
    for i in range(7):
        a = rnd.random() * 6.283
        d = (k + 1) / n * min(w, h) * 0.35
        r = max(1, min(w, h) * (0.16 - 0.035 * k))
        import math
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.7 - k * 2
        circle(s, "ink5" if k < 2 else "ink4", x, y, r)
        circle(s, "ink6" if k < 2 else "ink5", x - r * 0.3, y - r * 0.3, r * 0.5)
    if k == 0:
        circle(s, "ink7", cx, cy, min(w, h) * 0.15)
    return s


# --- the gloom LUT (B3's palette-swap shader reads gloom_lut.png) ---------------------------
def gloom_lut(stage):
    """Index -> index for gloom stage 0..3 (spikes/art/sf_art.py rule: one ramp step darker per
    stage; at 3, moss/earth/water drop into the ink ramp; accents never change)."""
    accents = set(RAMPS["light"] + RAMPS["ember"][2:] + RAMPS["shadow"])
    out = []
    for name, ramp in RAMPS.items():
        for i, col in enumerate(ramp):
            if stage == 0 or col in accents:
                o = col
            elif stage == 3 and name in ("moss", "earth", "water"):
                o = RAMPS["ink"][max(1, i)]
            else:
                o = ramp[max(0, i - stage)] if name != "ink" else ramp[max(0, i - (stage + 1) // 2)]
            out.append(HEX.index(o))
    return out


# --- sheets ---------------------------------------------------------------------------------
class Sheet:
    """One PNG + one JSON: rows = animations, columns = frames, a fixed cell size.
    JSON: {"image", "cell": [w, h], "origin": [x, y], "anims": {name: {row, col, frames, fps, loop}}}.
    Several short anims (tiles) may share a row; `col` says where each starts."""

    def __init__(self, name, w, h, origin=None, cols=None, kind="sprite"):
        self.name, self.w, self.h, self.kind = name, w, h, kind
        self.origin = origin or [w // 2, h]
        self.cols = cols
        self.anims = []  # (name, frames, fps, loop)

    def add(self, name, frames, fps=8, loop=True):
        for f in frames:
            assert f.get_size() == (self.w, self.h), (self.name, name, f.get_size())
        assert name not in [a[0] for a in self.anims], name
        self.anims.append((name, list(frames), fps, loop))

    def save(self, folder="sheets"):
        cols = self.cols or max(len(a[1]) for a in self.anims)
        meta, row, col = {}, 0, 0
        for name, frames, fps, loop in self.anims:
            n = len(frames)
            assert n <= cols, (self.name, name)
            if col + n > cols:
                row, col = row + 1, 0
            meta[name] = {"row": row, "col": col, "frames": n, "fps": fps, "loop": loop}
            col += n
            if self.cols is None:
                row, col = row + 1, 0
        rows = row + (1 if col else 0)
        img = surf(cols * self.w, rows * self.h)
        for name, frames, _, _ in self.anims:
            m = meta[name]
            for i, f in enumerate(frames):
                img.blit(f, ((m["col"] + i) * self.w, m["row"] * self.h))
        check_palette(img, self.name)
        d = os.path.join(ART, folder)
        os.makedirs(d, exist_ok=True)
        pygame.image.save(img, os.path.join(d, self.name + ".png"))
        doc = {"image": self.name + ".png", "kind": self.kind, "cell": [self.w, self.h],
               "origin": self.origin, "anims": meta}
        with open(os.path.join(d, self.name + ".json"), "w") as fh:
            json.dump(doc, fh, indent=1)
            fh.write("\n")
        print(f"  {folder}/{self.name}.png  {img.get_width()}x{img.get_height()}  {len(meta)} anims")


def check_palette(img, what):
    w, h = img.get_size()
    for y in range(h):
        for x in range(w):
            p = img.get_at((x, y))
            assert p.a in (0, 255), f"{what}: alpha {p.a} at {x},{y}"
            assert p.a == 0 or (p.r, p.g, p.b) in SET, f"{what}: off-palette {tuple(p)} at {x},{y}"


def save_png(img, rel):
    check_palette(img, rel)
    path = os.path.join(ART, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(img, path)
    print("  " + rel)
