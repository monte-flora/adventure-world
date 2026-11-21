"""Makes every sample PNG in docs/teen/art/. No window opens. From the repo folder:

    python spikes/art/shoot_today.py      # the 'before' screenshots (today's game)
    python spikes/art/make_samples.py     # the teen-art samples + before/after
"""
import os

import pygame

import hero
import scenes
from sf_art import NATIVE, P, RAMPS, PALETTE, gloom_lut, label, rgb, save, scaled

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "teen", "art"))
BG = P["ink2"]


def board(w, h):
    s = pygame.Surface((w, h))
    s.fill(BG)
    return s


def palette_png():
    sw, gap = 40, 4
    s = board(32 * sw + 20, 26 + 5 * (sw + 22))
    label(s, "Shadowfall 32: ramps dark -> light (ink, moss, earth, water, ember, light, shadow)", (10, 6), 22)
    x = 10
    for name, ramp in RAMPS.items():
        for c in ramp:
            pygame.draw.rect(s, rgb(c), (x, 28, sw - gap, sw))
            label(s, c[1:], (x, 28 + sw + 2), 14)
            x += sw
    for stage in range(1, 4):
        y = 28 + stage * (sw + 22) + 10
        label(s, f"gloom {stage}: every colour remapped to a darker, greyer, more violet palette colour", (10, y - 12), 16)
        lut = gloom_lut(stage)
        for i, c in enumerate(PALETTE):
            pygame.draw.rect(s, lut[rgb(c)], (10 + i * sw, y + 4, sw - gap, sw - 10))
    save(s, "palette.png")


def hero_png():
    td, sv = hero.top_down_sheet(), hero.side_sheet()
    k = 6
    s = board(sv.get_width() * k + 40, td.get_height() * k + sv.get_height() * k + 110)
    label(s, "Hero, top-down 16x24: rows down / up / right / left, 4-frame walk (8 fps)", (20, 10), 24)
    s.blit(scaled(td, k), (20, 36))
    y = 36 + td.get_height() * k + 30
    label(s, "Hero, side view 24x32: idle x2, run x4, jump, attack x2 (anticipation, swing)", (20, y - 24), 24)
    s.blit(scaled(sv, k), (20, y))
    for i in range(4):                                     # the same frames at 1x and 2x, as in game
        s.blit(scaled(td, 2), (td.get_width() * 6 + 60, 36))
    s.blit(td, (td.get_width() * 6 + 60 + td.get_width() * 2 + 20, 36))
    label(s, "2x and 1x", (td.get_width() * 6 + 60, 36 + td.get_height() * 2 + 6), 20)
    save(s, "hero.png")
    save(td, "hero_topdown_16x24.png")                     # engine-ready sheets (1x, transparent)
    save(sv, "hero_side_24x32.png")


def king_png():
    scene = scenes.throne_scene()
    s = board(NATIVE[0] * 2 + 96 * 3 + 60, NATIVE[1] * 2 + 50)
    label(s, "The Shadow King: one silhouette, two violet eyes, rim light from the dying sun (sample at 2x; sprite 96x128 at 3x)", (20, 10), 22)
    s.blit(scaled(scene, 2), (20, 36))
    s.blit(scaled(scenes.shadow_king(), 3), (NATIVE[0] * 2 + 40, 36 + 80))
    save(s, "shadow_king.png")


def overworld_png():
    sheet = scenes.tileset_sheet()
    world = scenes.overworld()
    scenes.hud(world)
    s = board(sheet.get_width() * 4 + NATIVE[0] * 2 + 60, NATIVE[1] * 2 + 50)
    label(s, "Overworld kit (16x16 tiles at 4x)", (20, 10), 22)
    s.blit(scaled(sheet, 4), (20, 36))
    label(s, "grass x3 / path x2 / water 2 frames / shore", (20, 36 + 4 * 64 + 4), 18)
    label(s, "cliff top / cliff face x2 / cast shadow", (20, 36 + 4 * 64 + 22), 18)
    x = sheet.get_width() * 4 + 40
    label(s, "Sample screen 480x270 at 2x: high ground lighter, 2-tile cliff face, cast shadows, y-sorted", (x, 10), 22)
    s.blit(scaled(world, 2), (x, 36))
    save(s, "overworld_tiles.png")
    return world


def cave_png():
    layers = scenes.cave_layers()
    cell = (NATIVE[0] // 2, NATIVE[1] // 2)
    s = board(3 * cell[0] + 40, 2 * (cell[1] + 24) + 20)
    comp = pygame.Surface(NATIVE)
    for i, (name, layer) in enumerate(layers):
        alone = pygame.Surface(NATIVE)
        alone.fill(P["ink3"] if i else P["ink0"])
        alone.blit(layer, (0, 0))
        comp.blit(layer, (0, 0))
        x, y = 10 + (i % 3) * (cell[0] + 10), 10 + (i // 3) * (cell[1] + 24)
        label(s, f"{i + 1}. {name}", (x, y), 18)
        s.blit(pygame.transform.scale(alone, cell), (x, y + 16))
    x, y = 10 + 2 * (cell[0] + 10), 10 + (cell[1] + 24)
    label(s, "6. lit: darkness + banded light pools", (x, y), 18)
    s.blit(pygame.transform.scale(scenes.cave_scene(), cell), (x, y + 16))
    save(s, "cave_layers.png")
    save(scenes.cave_scene(), "cave_scene.png", scale=2)


def darkening_png(world):
    s = board(NATIVE[0] * 2 + 30, NATIVE[1] * 2 + 70)
    names = ["gloom 0: dusk (a new game)", "gloom 1", "gloom 2", "gloom 3: his night (+ lantern light)"]
    for st in range(4):
        img = scenes.overworld(gloom_lut(st))
        if st == 3:
            img = scenes.cave_lighting(img, [(208, 180, 120)], darkness=110)
        scenes.hud(img)
        x, y = 10 + (st % 2) * (NATIVE[0] + 10), 10 + (st // 2) * (NATIVE[1] + 26)
        label(s, names[st], (x, y), 20)
        s.blit(img, (x, y + 18))
    save(s, "darkening.png")


def before_after_png(world):
    cave = scenes.cave_scene()
    w, h = 720, 405
    s = board(2 * w + 30, 2 * (h + 30) + 10)
    pairs = [("before_map.png", world, "map"), ("before_cave.png", cave, "cave")]
    for row, (name, after, what) in enumerate(pairs):
        before = pygame.image.load(os.path.join(OUT, name))
        y = 10 + row * (h + 30)
        label(s, f"today: {what} (64-px tiles, side panel)", (10, y), 22)
        label(s, f"teen sample: {what} (16-px tiles, 480x270, HUD in view)", (20 + w, y), 22)
        bw = int(before.get_width() * h / before.get_height())
        s.blit(pygame.transform.smoothscale(before, (min(bw, w), h)) if bw <= w else
               pygame.transform.smoothscale(before, (w, int(before.get_height() * w / before.get_width()))), (10, y + 22))
        s.blit(pygame.transform.scale(after, (w, h)), (20 + w, y + 22))
    save(s, "before_after.png")


if __name__ == "__main__":
    palette_png()
    hero_png()
    king_png()
    world = overworld_png()
    cave_png()
    darkening_png(world)
    before_after_png(world)
