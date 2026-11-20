"""
Drawing Phase 2's teen look (the values are in theme.py): the dusk over the map and the title screen's
name. phase2/__init__.py calls these only in Phase 2 (or with Phase 2 picked on the title).
"""

import math

import pygame

from phase2 import theme


def draw_dusk(app, surf):
    """A thin violet sky over the map's ground, under the Hero, the people and the monsters (Nightfall
    Hollow has its own dark, so the dusk is only on the first world)."""
    if app.game.world != 1:
        return
    alpha = theme.dusk_alpha(app.game)
    if alpha <= 0:
        return
    sky = getattr(app, "_phase2_dusk", None)
    if sky is None or sky.get_size() != surf.get_size() or sky.get_at((0, 0)).a != alpha:
        sky = app._phase2_dusk = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        sky.fill(theme.DUSK + (alpha,))
    surf.blit(sky, (0, 0))


def draw_map_dusk(app, rect):
    """The dusk over the little map in the panel, as the world grows dark. (What's drawn on it after this,
    like you and the waystones, stays bright.)"""
    alpha = theme.minimap_alpha(app.game)
    if alpha <= 0:
        return
    sky = pygame.Surface(rect.size, pygame.SRCALPHA)
    sky.fill(theme.DUSK + (alpha,))
    app.screen.blit(sky, rect)


def draw_title(app, top):
    """The name (with a violet glow), the subtitle and the goal, over a darker, violet sky."""
    s = app.screen
    shade = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    shade.fill(theme.DUSK + (110,))
    s.blit(shade, (0, 0))
    middle = s.get_width() // 2
    name = theme.GAME_NAME.upper()
    pulse = int(120 + 50 * math.sin(app.time * 2))
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3), (3, -3), (-3, 3)):
        app.text(s, name, (middle + dx, top + 84 + dy), 100, theme.VIOLET, "center", alpha=pulse)
    app.text(s, name, (middle, top + 84), 100, theme.GOLD, "center", shadow=True)
    app.text(s, theme.SUBTITLE.upper(), (middle, top + 146), 26, theme.EMBER, "center", shadow=True)
    app.text(s, theme.TAGLINE, (middle, top + 178), 22, theme.TEXT, "center", shadow=True)
