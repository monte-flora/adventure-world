"""
DRAWING the Phase 2 extras: the timing bar in a fight, and on the map the night sky and what each
monster is up to ("!" when it chases you, sweat drops when it runs away).

game.py calls these with its App (the window). Nothing here imports game.py: the App is passed in,
and its own helpers (app.text, app.screen...) do the drawing, so it looks like the rest of the game.
"""

import math

import pygame

from phase2 import monsters

GREEN = (70, 200, 90)
GREEN_EDGE = (140, 255, 150)
GOLD = (240, 190, 50)
GOLD_EDGE = (255, 240, 150)
GRADE_COLORS = {"perfect": (255, 214, 64), "good": (110, 230, 120), "miss": (170, 160, 190)}
NIGHT_SKY = (12, 14, 46)
NIGHT_ALPHA = 150               # how dark deep night is (0-255)
WORD_TIME = 0.8                 # the "PERFECT!" word shows this long after a strike


def draw_strike_bar(app):
    """Under the VS in the fight box: the bar, its green and gold zones, and the sweeping marker.
    It's dim during the short pause between turns (A doesn't work then)."""
    from phase2 import fight
    battle = app.game.battle
    bar_info = getattr(battle, "bar", None)
    if battle is None or bar_info is None or battle.over:
        return
    s, box = app.screen, app.battle_box
    ready = app.time >= app.battle_ready_at
    bar = pygame.Rect(0, 0, 250, 26)
    bar.center = (box.centerx, box.y + 214)
    pygame.draw.rect(s, (60, 50, 50), bar, border_radius=8)
    zone = pygame.Rect(bar.x + int(bar_info.zone_x * bar.w), bar.y, int(bar_info.zone_w * bar.w), bar.h)
    gold = pygame.Rect(bar.x + int(bar_info.gold_x * bar.w), bar.y, int(bar_info.gold_w * bar.w), bar.h)
    pygame.draw.rect(s, GREEN, zone, border_radius=6)
    pygame.draw.rect(s, GREEN_EDGE, zone, 2, border_radius=6)
    pygame.draw.rect(s, GOLD, gold, border_radius=4)
    pygame.draw.rect(s, GOLD_EDGE, gold, 2, border_radius=4)
    if not ready:                                        # the pause: everything dimmed
        shade = pygame.Surface(bar.size, pygame.SRCALPHA)
        shade.fill((20, 18, 30, 150))
        s.blit(shade, bar.topleft)
    mx = bar.x + int(bar_info.pos_at(app.time) * bar.w)
    heat = (255, int(160 + 80 * math.sin(app.time * 20)), 60) if ready else (120, 110, 120)
    pygame.draw.rect(s, heat, (mx - 4, bar.y - 7, 8, bar.h + 14), border_radius=4)
    since = app.time - bar_info.start
    if bar_info.last and since < WORD_TIME:
        word = fight.GRADE_WORDS[bar_info.last]
        app.text(s, word, (box.centerx, bar.bottom + 8), 34, GRADE_COLORS[bar_info.last], "midtop", shadow=True)
    else:
        app.text(s, "R in the gold = PERFECT!", (box.centerx, bar.bottom + 12), 20, (170, 166, 200), "midtop")


def faces_left(game, m):
    """Which way to draw a monster on the map. The pictures look right; flip them to look left.
    Phase 2 monsters look the way they last walked (so you can sneak up behind them)."""
    facing = getattr(m, "facing", None)
    if facing is None or game.world != 1:
        return game.player.pos[1] < m.pos[1]             # the classic way: they always look at you
    if facing in ("left", "right"):
        return facing == "left"
    return getattr(m, "looks_left", False)               # up or down: keep looking the same way


def draw_map(app, surf):
    """The night sky over the map, then a "!" over monsters that chase you and sweat over ones that flee."""
    game = app.game
    if game.world != 1:
        return
    dark = monsters.darkness(game)
    if dark > 0:
        sky = getattr(app, "_phase2_sky", None)
        if sky is None or sky.get_size() != surf.get_size():
            sky = app._phase2_sky = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        sky.fill(NIGHT_SKY + (int(NIGHT_ALPHA * dark),))
        surf.blit(sky, (0, 0))
    for m in game.monsters:
        state = getattr(m, "state", None)
        if not m.is_alive or state not in ("chase", "flee"):
            continue
        x, y = app.on_screen(*app.monster_px.get(id(m), (m.pos[1] * 64, m.pos[0] * 64)))
        if state == "chase":
            bob = math.sin(app.time * 10) * 2
            app.text(surf, "!", (x + 32, y - 6 + bob), 34, (255, 80, 70), "midtop", shadow=True)
        else:
            for i in range(2):                           # sweat drops: it's scared of you!
                dx = (-14, 16)[i]
                dy = (app.time * 30 + i * 9) % 14
                pygame.draw.circle(surf, (140, 210, 255), (int(x + 32 + dx), int(y + 6 + dy)), 4)
    if dark > 0.5:                                       # a little moon in the corner
        pygame.draw.circle(surf, (235, 235, 210), (surf.get_width() - 50, 46), 20)
        pygame.draw.circle(surf, NIGHT_SKY, (surf.get_width() - 40, 40), 17)
