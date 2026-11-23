"""Placeholder pictures for every asset in shadowfall/realm/gemini/assets.json, so the whole pipeline
runs before any Gemini art exists. Each is plainly fake: simple shapes with white diagonal stripes.

    python shadowfall/tools/make_placeholders.py      # writes shadowfall/realm/gemini/placeholder/*.png

Props are drawn 4x the game size on flat magenta (like Gemini's), ground textures 512x512 (not
seamless: the import fixes that). Then `pixi run import-art --placeholders` makes the game art.
"""

import json
import os
import random

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEMINI = os.path.join(ROOT, "shadowfall", "realm", "gemini")
OUT = os.path.join(GEMINI, "placeholder")
MAGENTA = (255, 0, 255)
INK = (24, 20, 28)
GROUND = {"grass": (52, 74, 48), "dirt_road": (112, 74, 52), "cobblestone": (96, 92, 88),
          "mud": (62, 48, 38), "shallow_water": (54, 86, 92), "rocky_ground": (78, 76, 96),
          "cliff": (60, 58, 70), "deep_water": (34, 58, 76), "forest_floor": (40, 54, 38)}
GREEN, DARK, BARK, ROOF, WALL, STONE, IRON, FIRE = ((50, 92, 52), (34, 64, 52), (92, 62, 40), (60, 70, 120),
                                                    (200, 190, 160), (120, 118, 128), (40, 40, 48), (240, 150, 40))


def stripes(s, rect):
    """White diagonal hatching over what's drawn in rect: the 'this is a placeholder' mark."""
    mask = pygame.mask.from_threshold(s, MAGENTA, (1, 1, 1, 255))
    mask.invert()
    hatch = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    for x in range(-s.get_height(), s.get_width(), 24):
        pygame.draw.line(hatch, (255, 255, 255, 90), (x, s.get_height()), (x + s.get_height(), 0), 5)
    hatch_m = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    hatch.blit(hatch_m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(hatch, (0, 0))


def blob(s, color, rect, w=6):
    pygame.draw.ellipse(s, color, rect)
    pygame.draw.ellipse(s, INK, rect, w)


def box(s, color, rect, w=6):
    pygame.draw.rect(s, color, rect)
    pygame.draw.rect(s, INK, rect, w)


def tri(s, color, pts, w=6):
    pygame.draw.polygon(s, color, pts)
    pygame.draw.polygon(s, INK, pts, w)


def prop(name, w, h):
    s = pygame.Surface((w, h))
    s.fill(MAGENTA)
    m = 8                                         # margin, like Gemini's padding
    W, H = w - 2 * m, h - 2 * m
    X, Y = m, m
    if name in ("oak", "dead_tree"):
        box(s, BARK, (X + W * 0.4, Y + H * 0.55, W * 0.2, H * 0.45))
        if name == "oak":
            blob(s, GREEN, (X, Y, W, H * 0.7))
        else:
            for dx in (-0.3, 0.3):
                pygame.draw.line(s, BARK, (X + W * 0.5, Y + H * 0.6), (X + W * (0.5 + dx), Y + H * 0.1), 14)
    elif name == "pine":
        box(s, BARK, (X + W * 0.42, Y + H * 0.8, W * 0.16, H * 0.2))
        tri(s, DARK, [(X + W / 2, Y), (X, Y + H * 0.85), (X + W, Y + H * 0.85)])
    elif name == "bush":
        blob(s, GREEN, (X, Y, W, H))
    elif name in ("cottage_a", "cottage_b", "tavern", "smithy"):
        box(s, WALL if name != "smithy" else STONE, (X + W * 0.05, Y + H * 0.45, W * 0.9, H * 0.55))
        tri(s, ROOF if name != "cottage_b" else (130, 70, 50), [(X, Y + H * 0.5), (X + W / 2, Y), (X + W, Y + H * 0.5)])
        box(s, BARK, (X + W * 0.44, Y + H * 0.72, W * 0.12, H * 0.28))
        for fx in ((0.25, 0.7) if name != "cottage_b" else (0.62,)):
            box(s, (255, 210, 110), (X + W * fx, Y + H * 0.62, W * 0.1, H * 0.12), 4)
    elif name == "lamppost":
        box(s, IRON, (X + W * 0.4, Y + H * 0.15, W * 0.2, H * 0.85), 3)
        box(s, (255, 210, 110), (X + W * 0.1, Y, W * 0.8, H * 0.2), 4)
    elif name == "fence":
        for fx in (0.05, 0.45, 0.85):
            box(s, BARK, (X + W * fx, Y, W * 0.1, H))
        for fy in (0.25, 0.65):
            box(s, BARK, (X, Y + H * fy, W, H * 0.12))
    elif name == "well":
        tri(s, BARK, [(X, Y + H * 0.35), (X + W / 2, Y), (X + W, Y + H * 0.35)])
        blob(s, STONE, (X, Y + H * 0.5, W, H * 0.5))
    elif name == "cart":
        box(s, BARK, (X, Y, W, H * 0.6))
        for fx in (0.1, 0.6):
            blob(s, IRON, (X + W * fx, Y + H * 0.45, W * 0.3, H * 0.55))
    elif name == "rocks":
        for r in ((0, 0.3, 0.55, 0.7), (0.4, 0, 0.6, 1.0), (0.2, 0.55, 0.4, 0.45)):
            blob(s, STONE, (X + W * r[0], Y + H * r[1], W * r[2], H * r[3]))
    elif name == "flowers":
        for i in range(9):
            c = [(200, 50, 50), (240, 240, 230), (130, 90, 200)][i % 3]
            pygame.draw.circle(s, c, (X + W * (0.1 + 0.1 * i), Y + H * (0.3 + 0.4 * (i % 2))), W * 0.07)
    elif name == "fallen_log":
        box(s, BARK, (X, Y + H * 0.2, W, H * 0.8))
    elif name == "ruined_wall":
        box(s, STONE, (X, Y + H * 0.25, W * 0.7, H * 0.75))
        box(s, STONE, (X + W * 0.7, Y + H * 0.6, W * 0.3, H * 0.4))
    elif name == "waystone":
        tri(s, STONE, [(X + W * 0.2, Y + H), (X + W * 0.35, Y), (X + W * 0.75, Y + H * 0.05), (X + W * 0.85, Y + H)])
    elif name == "mine_mouth":
        blob(s, STONE, (X, Y, W, H * 1.3))
        pygame.draw.ellipse(s, INK, (X + W * 0.3, Y + H * 0.4, W * 0.4, H * 0.9))
    elif name in ("crag", "riven_boulder"):
        tri(s, STONE, [(X, Y + H), (X + W * 0.25, Y + H * 0.1), (X + W * 0.6, Y), (X + W, Y + H * 0.3), (X + W, Y + H)])
        if name == "riven_boulder":
            pygame.draw.line(s, INK, (X + W * 0.5, Y + H * 0.1), (X + W * 0.45, Y + H), 10)
    elif name == "ivy_cliff":
        box(s, STONE, (X, Y, W, H))
        for fx in (0.15, 0.45, 0.75):
            box(s, GREEN, (X + W * fx, Y, W * 0.15, H * 0.8), 3)
    elif name == "rubble_heap":
        for r in ((0, 0.45, 0.5, 0.55), (0.45, 0.4, 0.55, 0.6), (0.2, 0, 0.55, 0.6)):
            box(s, STONE, (X + W * r[0], Y + H * r[1], W * r[2], H * r[3]))
    elif name == "shadow_thorns":
        for dx in (-0.4, -0.15, 0.15, 0.4):
            pygame.draw.line(s, (60, 30, 80), (X + W * 0.5, Y + H), (X + W * (0.5 + dx), Y), 16)
    elif name == "campfire":
        blob(s, STONE, (X, Y + H * 0.5, W, H * 0.5))
        tri(s, FIRE, [(X + W * 0.3, Y + H * 0.75), (X + W / 2, Y), (X + W * 0.7, Y + H * 0.75)])
    stripes(s, s.get_rect())
    return s


def ground(name):
    rng = random.Random(name)
    base = GROUND[name]
    s = pygame.Surface((512, 512))
    s.fill(base)
    for _ in range(900):
        k = rng.uniform(-28, 28)
        c = tuple(max(0, min(255, int(v + k))) for v in base)
        r = rng.randint(3, 14)
        pygame.draw.circle(s, c, (rng.randint(0, 511), rng.randint(0, 511)), r)
    for x in range(-512, 512, 48):                # placeholder stripes
        pygame.draw.line(s, tuple(min(255, v + 18) for v in base), (x, 512), (x + 512, 0), 3)
    return s


def main():
    pygame.init()
    a = json.load(open(os.path.join(GEMINI, "assets.json")))
    os.makedirs(OUT, exist_ok=True)
    for n in a["ground"]:
        pygame.image.save(ground(n), os.path.join(OUT, (n if "_ground_" in n else "ground_" + n) + ".png"))
    for n, d in a["props"].items():
        w, h = d["size"]
        pygame.image.save(prop(n, w * 4, h * 4), os.path.join(OUT, n + ".png"))
    print("placeholders:", len(a["ground"]) + len(a["props"]))


if __name__ == "__main__":
    main()
