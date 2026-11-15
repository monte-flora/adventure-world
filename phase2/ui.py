"""One look for every Phase 2 box (pause, save slots, dialogue, shop, quest log, the L/B/H pages).

- the box: a dark fill (BOX_BG, from theme.py), a 3 px gold edge, round corners (the same as game.py's panel_box)
- the picked row: ROW_LIGHT with a gold edge
- the key hints at the bottom: key caps and dim words, in one wording everywhere:
      [UP][DOWN] pick   [ENTER] choose   [ESC] back
  ("back", never "closes" or "leave"; the key that opened a page closes it too, but ESC always does)
"""

import pygame

from phase2 import theme

BOX_BG = theme.BOX_BG           # (every colour is in phase2/theme.py)
ROW_LIGHT = theme.ROW_LIGHT
GOLD = theme.GOLD
DIM = theme.DIM
FRAME_BG = theme.FRAME_BG        # behind a face
FRAME_EDGE = theme.FRAME_EDGE

PICK = (("UP", "DOWN"), "pick")
BACK = ("ESC", "back")

CAP_GAP, WORD_GAP, PAIR_GAP = 4, 7, 24


def box(app, rect, edge=GOLD):
    pygame.draw.rect(app.screen, BOX_BG, rect, border_radius=18)
    pygame.draw.rect(app.screen, edge, rect, 3, border_radius=18)


def _caps(keys):
    return (keys,) if isinstance(keys, str) else tuple(keys)


def hints_width(app, pairs, size=22):
    width = 0
    for keys, words in pairs:
        for cap in _caps(keys):
            width += app.font(20).size(cap)[0] + 12 + CAP_GAP
        width += WORD_GAP - CAP_GAP + app.font(size).size(words)[0] + PAIR_GAP
    return width - PAIR_GAP if pairs else 0


def hints(app, pairs, pos, anchor="center", size=22, color=DIM, alpha=None):
    """A row of key hints: pairs is [(key or (key, key), words), ...]. pos is the middle of the row
    (anchor "center"), or its right or left end ("right", "left"). Returns the row's rect."""
    s = app.screen
    width = hints_width(app, pairs, size)
    x = pos[0] - width // 2 if anchor == "center" else pos[0] - width if anchor == "right" else pos[0]
    y = pos[1] - 11
    left = x
    for keys, words in pairs:
        for cap in _caps(keys):
            x = app.key_box(s, cap, x, y) + CAP_GAP
        said = app.text(s, words, (x - CAP_GAP + WORD_GAP, y + 3), size, color, alpha=alpha)
        x = said.right + PAIR_GAP
    return pygame.Rect(left, y, width, 22)


def face(app, look, rect, scale=None):
    """A person's face (phase2/art.py's portrait) in the little green frame the dialogue box uses."""
    from phase2 import art
    rect = pygame.Rect(rect)
    pygame.draw.rect(app.screen, FRAME_BG, rect, border_radius=max(4, rect.w // 14))
    pygame.draw.rect(app.screen, FRAME_EDGE, rect, 3 if rect.w > 60 else 2, border_radius=max(4, rect.w // 14))
    picture = art.portrait(look) if scale is None else art.portrait(look, scale)
    clip = app.screen.get_clip()
    app.screen.set_clip(rect.inflate(-4, -4))
    app.screen.blit(picture, picture.get_rect(center=rect.center).move(0, max(1, rect.h // 28)))
    app.screen.set_clip(clip)
