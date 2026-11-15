"""
DRAWING PHASE 2'S SIDE PANEL AND MESSAGE BOX (what they show is decided in phase2/hud.py).

The side panel, top to bottom:
    the hero card      your name, lives, level, health and XP
    the NEXT card      what to do next, an arrow and how far, and the 7 Light Stones filling in
    the pack           an icon for each thing you have (hold the mouse over one to see what it does)
    the "here" card    where you are, and the keys that do something right here
    H keys, P pause    the rest of the keys are on the H page

The bottom: a message box (the newest message is big and glows, older ones are small under it)
and the map, with a gold pin where the NEXT card says to go. Big news also pops up over the map.

Keys: L the message log, B the big map, H every key. The mouse: hover for a tooltip, click the
NEXT card for your quests, the map for the big map, the message box for the log.

game.py calls draw_panel and draw_log (through phase2/__init__.py); the rest hangs on hooks that
were already there. Nothing here imports game.py: its helpers come from the module the App is in.
"""

import math
import sys

import pygame

import sprites
from phase2 import draw_people, draw_world, hud, people, theme, ui

CARD = theme.CARD             # a card on the panel
CARD_EDGE = theme.CARD_EDGE
SLOT = theme.SLOT             # a square in the pack
BOX_BG = theme.BOX_BG           # the message box and the pop-up pages (like the other Phase 2 boxes)
GOLD = theme.GOLD
CYAN = (110, 215, 255)
SOCKET = [(74, 78, 108), (50, 53, 76), (40, 42, 62)]       # a Light Stone you don't have yet
TONES = {"bad": (240, 80, 80), "gold": (255, 214, 90), "full": (110, 220, 120), "blue": (110, 215, 255),
         "silver": (200, 210, 228), "fire": (255, 150, 50), "dim": (150, 156, 178)}
MAP_W = 190                     # room for the little map, right of the message box
SLOT_H = 54
PER_ROW = 4

# Little pictures, written like the ones in sprites.py (the letters are sprites.COLORS;
# a, b, c in STONE are swapped for each Light Stone's own three colours)
STONE = [
    "..kkkk..",
    ".kabbbk.",
    "kabbbbck",
    "kbbbbcck",
    ".kbbcck.",
    "..kbck..",
    "...kk...",
    "........",
]
ARROW = [
    "....y...",
    "....yy..",
    "yyyyyyy.",
    "yyyyyyyy",
    "yyyyyyy.",
    "....yy..",
    "....y...",
    "........",
]
ARROW_SLANT = [                 # pointing south-east
    ".y......",
    "yyy.....",
    ".yyy...y",
    "..yyy.yy",
    "...yyyyy",
    "....yyyy",
    "...yyyyy",
    "..yyyyyy",
]
KEY = [
    "........",
    ".yy.....",
    "y..y....",
    "y..yyyyy",
    ".yy..Y.Y",
    "........",
    "........",
    "........",
]
HILT = [
    "...ee...",
    "...ee...",
    ".yyyyyy.",
    "...nn...",
    "...NN...",
    "...nn...",
    "...yy...",
    "........",
]
PLANKS = [
    "........",
    "nnnnnnnn",
    "NnnNnnnN",
    "........",
    "nnnnnnnn",
    "nNnnnNnn",
    "........",
    "........",
]
TALK = [
    ".wwwwww.",
    "wwwwwwww",
    "wkwkwkww",
    "wwwwwwww",
    ".wwwwww.",
    "..ww....",
    ".w......",
    "........",
]
BANG = [
    "...rr...",
    "...rr...",
    "...rr...",
    "...rr...",
    "...rr...",
    "........",
    "...rr...",
    "........",
]
COIN = [
    "..YYYY..",
    ".YyyyyY.",
    "YyyYYyyY",
    "YyyYyyyY",
    "YyyYyyyY",
    "YyyYYyyY",
    ".YyyyyY.",
    "..YYYY..",
]


def _g(app):
    """game.py (it may be called __main__, so we find it from the App)."""
    return sys.modules[type(app).__module__]


class State:
    """What the HUD remembers between frames (it hangs on the App as app.hud)."""

    def __init__(self):
        self.feed = hud.Feed()
        self.spots = {}             # name -> where it is on screen (for the mouse)
        self.mouse = (-1, -1)
        self.pinned = None          # a pack item you clicked: its tooltip stays (good for touch screens)
        self.screen = None          # "log", "map" or "keys" while one of those pages is open
        self.back = "play"          # where the page goes back to
        self.scroll = 0             # how far up the message log is scrolled (in lines)
        self.fits = {}              # (text, size, width) -> the text cut short to fit
        self.pictures = {}          # little pictures, made once
        self.big_map = None         # (key, picture) of the big map


def state(app):
    if not isinstance(app.__dict__.get("hud"), State):
        app.hud = State()
    return app.hud


# ===========================================================================
# Little pictures
# ===========================================================================

def _picture(art, scale, swaps=None):
    surf = pygame.Surface((len(art[0]) * scale, len(art) * scale), pygame.SRCALPHA)
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch != ".":
                color = (swaps or {}).get(ch) or sprites.COLORS[ch]
                surf.fill(color, (x * scale, y * scale, scale, scale))
    return surf


def icon(app, name):
    """A little picture by name: one of ours, or one of the game's (app.art)."""
    pictures = state(app).pictures
    if name not in pictures:
        own = {"key": KEY, "hilt": HILT, "planks": PLANKS, "talk": TALK, "bang": BANG, "coin": COIN}
        if name in own:
            pictures[name] = _picture(own[name], 3)
        elif name == "lantern":
            pictures[name] = _picture(sprites.LANTERN, 2)
        elif name == "light_shard":
            pictures[name] = app.art["sun_shard"]
        elif name == "chest":
            pictures[name] = _picture(sprites.CHEST, 2)
        elif name == "waystone":
            pictures[name] = draw_world.art("waystone_lit")
        elif name == "stone":
            pictures[name] = stone_picture(app, 0, True)
        elif name == "mini_heart":
            pictures[name] = _picture(sprites.HEART, 2)
        else:
            pictures[name] = app.art.get(name) or app.art["star"]
    return pictures[name]


def stone_picture(app, i, have):
    """Light Stone number i (0 is the first): glowing in its own colour, or an empty socket."""
    pictures = state(app).pictures
    key = ("stone", i, have)
    if key not in pictures:
        light, middle, dark = hud.STONE_COLORS[i % len(hud.STONE_COLORS)] if have else SOCKET
        swaps = {"a": light, "b": middle, "c": dark}
        if not have:
            swaps["k"] = SOCKET[0]
        pictures[key] = _picture(STONE, 3, swaps)
    return pictures[key]


def arrow_picture(app, way):
    """A gold arrow pointing one of hud.WAYS (two pictures, turned a quarter at a time so they stay crisp)."""
    pictures = state(app).pictures
    key = ("arrow", way)
    if key not in pictures:
        i = hud.WAYS.index(way)
        base = _picture(ARROW_SLANT if i % 2 else ARROW, 3)
        pictures[key] = pygame.transform.rotate(base, -90 * (i // 2))
    return pictures[key]


def small(app, name, size=24):
    """A game picture squeezed into a little square (for the powers)."""
    pictures = state(app).pictures
    key = ("small", name, size)
    if key not in pictures:
        pictures[key] = pygame.transform.scale(app.art.get(name) or app.art["star"], (size, size))
    return pictures[key]


def fit(app, text, size, width):
    """app.fit, remembered (cutting words to fit measures them over and over: slow in a browser)."""
    fits = state(app).fits
    key = (text, size, width)
    if key not in fits:
        if len(fits) > 600:
            fits.clear()
        fits[key] = app.fit(text, size, width)
    return fits[key]


def card(s, rect, edge=CARD_EDGE, fill=CARD, width=1):
    pygame.draw.rect(s, fill, rect, border_radius=10)
    pygame.draw.rect(s, edge, rect, width, border_radius=10)


def mix(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


# ===========================================================================
# The side panel
# ===========================================================================

def draw_panel(app):
    G = _g(app)
    s, st = app.screen, state(app)
    x0 = G.VIEW_W
    s.fill(theme.PANEL_BG, (x0, 0, G.PANEL_W, G.HEIGHT))
    pygame.draw.line(s, theme.DIVIDER, (x0, 0), (x0, G.HEIGHT), 2)
    st.spots = {}
    app.panel_spots = {}
    x, w = x0 + 12, G.PANEL_W - 24
    y = hero_card(app, x, 10, w)
    y = goal_card(app, x, y + 8, w)
    y = pack_card(app, x, y + 10, w)
    foot = G.HEIGHT - 38
    here_card(app, x, y + 10, w, foot - 6)
    footer(app, x, foot, w)


def hero_card(app, x, y, w):
    G = _g(app)
    s, p, st = app.screen, app.game.player, state(app)
    box = pygame.Rect(x, y, w, 112)
    card(s, box)
    left, right = box.x + 12, box.right - 12
    # Level, in a pill on the right; your lives next to it (little hearts, or "x7" when there are lots)
    words = "Level %d" % p.level
    pill = pygame.Rect(0, 0, app.font(24).size(words)[0] + 18, 26)
    pill.topright = (right, box.y + 10)
    pygame.draw.rect(s, theme.BAR_BACK, pill, border_radius=13)
    pygame.draw.rect(s, GOLD, pill, 2, border_radius=13)
    app.text(s, words, pill.center, 24, G.TEXT, "center")
    heart = icon(app, "mini_heart")
    if p.lives <= 3:
        lives = pygame.Rect(0, 0, p.lives * 18, 16)
        lives.midright = (pill.x - 8, pill.centery)
        for i in range(p.lives):
            s.blit(heart, (lives.x + i * 18, lives.y))
    else:
        count = app.text(s, "x%d" % p.lives, (pill.x - 8, pill.centery), 24, (255, 120, 130), "midright")
        s.blit(heart, (count.x - 19, pill.centery - 8))
        lives = count.union(pygame.Rect(count.x - 19, pill.centery - 8, 16, 16))
    st.spots["lives"] = app.panel_spots["lives"] = lives.inflate(8, 10)
    room = lives.x - 8 - left
    size = next((size for size in (36, 30, 24) if app.font(size).size(p.name)[0] <= room), 24)
    app.text(s, fit(app, p.name, size, room), (left, pill.centery), size, GOLD, "midleft", shadow=True)
    # Health
    y = box.y + 46
    s.blit(app.art["heart"], (left, y))
    numbers = app.text(s, "%d/%d" % (p.health, p.max_health), (right, y + 3), 24, G.TEXT, "topright")
    if p.has_armor:
        numbers = numbers.union(app.text(s, "+%d" % p.armor, (numbers.x - 6, y + 3), 24, G.ARMOR_COLOR, "topright"))
    bar = pygame.Rect(left + 32, y + 3, numbers.x - 10 - (left + 32), 18)
    app.health_bar(s, bar, p)
    st.spots["health"] = pygame.Rect(left, y - 2, right - left, 28)
    # XP
    y += 32
    s.blit(app.art["star"], (left, y - 2))
    numbers = app.text(s, "%d/%d XP" % (p.xp, p.xp_needed), (right, y + 4), 20, G.DIM, "topright")
    app.bar(s, (left + 32, y + 5, numbers.x - 10 - (left + 32), 12), p.xp / p.xp_needed, GOLD)
    st.spots["xp"] = pygame.Rect(left, y - 2, right - left, 26)
    return box.bottom


def goal_card(app, x, y, w):
    """The NEXT card. Its height fits what it says. Returns its bottom."""
    G = _g(app)
    s, game, st = app.screen, app.game, state(app)
    goal = hud.next_goal(game)
    left, inner = x + 12, w - 24
    lines = app.wrap(goal["text"], 26, inner)[:3]
    height = 40 + (22 if goal["title"] else 0) + 26 * len(lines) + 6
    height += 24 if goal["count"] else 0
    height += 30 if goal["where"] else 0
    height += 24 if goal["alert"] else 0
    height += 22 * len(goal["checks"]) + (6 if goal["checks"] else 0)
    show_stones = not game.cave and game.world == 1     # (in Nightfall Hollow they've done their job)
    height += 40 if show_stones else 0
    height += 22 if goal["more"] else 0
    box = pygame.Rect(x, y, w, height + 6)
    card(s, box, GOLD, theme.CARD, 2)
    st.spots["goal"] = box
    # "NEXT", and Q for the quests
    s.blit(app.art["star"], (left - 2, box.y + 8))
    app.text(s, "NEXT", (left + 28, box.y + 11), 26, GOLD, shadow=True)
    if not game.cave:
        said = app.text(s, "quests", (box.right - 12, box.y + 13), 20, G.DIM, "topright")
        app.key_box(s, "Q", said.x - 30, box.y + 10)
    y = box.y + 40
    if goal["title"]:
        app.text(s, fit(app, goal["title"], 20, inner), (left, y), 20, G.DIM)
        y += 22
    for line in lines:
        app.text(s, line, (left, y), 26, G.TEXT)
        y += 26
    y += 6
    if goal["count"]:
        done, need = goal["count"]
        for i in range(need):
            spot = (left + 8 + i * 20, y + 9)
            pygame.draw.circle(s, G.GREEN if i < done else (70, 72, 96), spot, 7)
            pygame.draw.circle(s, (28, 26, 38), spot, 7, 2)
        app.text(s, "%d of %d" % (done, need), (left + need * 20 + 10, y + 1), 22, G.DIM)
        y += 24
    if goal["where"]:
        if goal["way"]:
            picture = arrow_picture(app, goal["way"])
            nudge = math.sin(app.time * 4) * 2              # the arrow nods the way to go
            dx, dy = math.cos(hud.WAYS.index(goal["way"]) * math.pi / 4), math.sin(hud.WAYS.index(goal["way"]) * math.pi / 4)
            s.blit(picture, (left + nudge * dx, y + nudge * dy))
            app.text(s, fit(app, goal["where"], 22, inner - 32), (left + 32, y + 4), 22, CYAN)
        else:
            app.text(s, fit(app, goal["where"], 22, inner), (left, y + 4), 22, G.GREEN)
        y += 30
    if goal["alert"]:
        app.text(s, goal["alert"], (left, y + 2), 20, (170, 215, 255))
        y += 24
    for name, have, need in goal["checks"]:
        done = have >= need
        tick = pygame.Rect(left, y + 2, 16, 16)
        pygame.draw.rect(s, G.GREEN if done else G.DIM, tick, 2, border_radius=3)
        if done:
            pygame.draw.lines(s, G.GREEN, False, [(left + 3, y + 10), (left + 7, y + 14), (left + 14, y + 4)], 3)
        app.text(s, name, (left + 26, y + 2), 22, G.GREEN if done else G.TEXT)
        if need > 1:
            app.text(s, "%d/%d" % (have, need), (box.right - 12, y + 2), 22, G.DIM, "topright")
        y += 22
    y += 6 if goal["checks"] else 0
    if show_stones:
        have, total = hud.stones(game)
        gap = (inner - 34 - total * 24) // max(1, total - 1)
        for i in range(total):
            picture = stone_picture(app, i, i < have)
            bob = math.sin(app.time * 3 + i) * 1.5 if i < have else 0
            s.blit(picture, (left + i * (24 + gap), y + 6 + bob))
        app.text(s, "%d/%d" % (have, total), (box.right - 12, y + 10), 22, GOLD if have else G.DIM, "topright")
        st.spots["stones"] = pygame.Rect(left, y + 2, inner, 34)
        y += 40
    if goal["more"]:
        app.text(s, "+ %d side quest%s" % (goal["more"], "" if goal["more"] == 1 else "s"), (left, y), 20, G.DIM)
    return box.bottom


def pack_card(app, x, y, w):
    """An icon for every thing you have, 4 to a row, then your powers. Returns the bottom."""
    G = _g(app)
    s, game, st = app.screen, app.game, state(app)
    items = hud.pack(game)
    app.text(s, "PACK", (x + 2, y), 20, G.DIM)
    y += 20
    gap = 6
    slot_w = (w - gap * (PER_ROW - 1)) // PER_ROW
    for i, item in enumerate(items):
        slot = pygame.Rect(x + (i % PER_ROW) * (slot_w + gap), y + (i // PER_ROW) * (SLOT_H + gap), slot_w, SLOT_H)
        name = "item:" + item["id"]
        over = slot.collidepoint(st.mouse) or st.pinned == name
        tone = TONES.get(item["tone"])
        pygame.draw.rect(s, mix(SLOT, (255, 255, 255), 0.12) if over else SLOT, slot, border_radius=8)
        edge = tone if item["tone"] in ("bad", "gold") else CARD_EDGE
        if item["tone"] == "bad" and int(app.time * 2) % 2:
            edge = mix(edge, SLOT, 0.5)                 # no sword, or it's about to break: it blinks
        pygame.draw.rect(s, GOLD if over else edge, slot, 2, border_radius=8)
        picture = icon(app, item["icon"])
        s.blit(picture, picture.get_rect(center=(slot.centerx - (8 if item["count"] else 0), slot.centery - 4)))
        if item["bar"]:                                 # a sword: how many hits it has left
            have, most = item["bar"]
            app.bar(s, (slot.x + 7, slot.bottom - 10, slot.w - 14, 5), have / most, tone or (215, 220, 230))
        if item["count"]:
            app.text(s, item["count"], (slot.right - 5, slot.bottom - (14 if item["bar"] else 4)), 24,
                     tone or G.TEXT, "bottomright", shadow=True)
        st.spots[name] = slot
        if item["id"] in ("food", "wood", "bow"):       # the tip bubbles point at these (tutorial.py)
            app.panel_spots[item["id"]] = slot
    rows = (len(items) + PER_ROW - 1) // PER_ROW
    y += rows * (SLOT_H + gap)
    mine = hud.powers(game)
    if mine:
        y += 2
        said = app.text(s, "POWERS", (x + 2, y + 5), 20, G.DIM)
        px = said.right + 8
        for name, times, what in mine:
            picture = small(app, G.POWER_ICONS.get(name, "star"))
            spot = pygame.Rect(px, y, 26 + (app.font(20).size("x%d" % times)[0] + 2 if times > 1 else 0), 26)
            if spot.right > x + w:
                break
            s.blit(picture, (px + 1, y + 1))
            if times > 1:
                app.text(s, "x%d" % times, (px + 27, y + 7), 20, GOLD)
            st.spots["power:" + name] = spot
            px = spot.right + 6
        y += 28
    return y


def here_card(app, x, y, w, bottom):
    """Where you are, and the keys that do something here. It sits on `bottom`, and never goes above y."""
    G = _g(app)
    s, game = app.screen, app.game
    hints = {"tiles": G.TILE_HINTS, "cave": G.CAVE_HINTS, "castle": G.CASTLE_HINTS, "throne": G.THRONE_HINTS}
    keys = hud.here(game, hints)
    step = 28 if len(keys) < 7 else 25
    box = pygame.Rect(x, y, w, min(bottom - y, 34 + step * len(keys) + 6))
    if box.h < 34:
        return
    box.bottom = bottom                                 # it sits at the bottom, so the keys are always in one place
    card(s, box)
    app.panel_spots["here"] = pygame.Rect(box.x, box.y, box.w, 30)
    left = box.x + 10
    app.text(s, fit(app, hud.place(game), 20, w - 20), (left, box.y + 9), 20, G.DIM)
    y = box.y + 34
    for line in keys:
        if y + step > box.bottom:
            break
        if len(line) == 4:                              # two keys on one line (the cave lists)
            end = app.key_box(s, line[0], left, y)
            said = app.text(s, line[1], (end + 7, y + 3), 22)
            end = app.key_box(s, line[2], said.right + 12, y)
            app.text(s, line[3], (end + 7, y + 3), 22)
        else:
            key, words, tone = line
            hot = tone == "hot"
            if hot:                                     # the one to notice glows softly
                glow = pygame.Rect(box.x + 4, y - 3, box.w - 8, 28)
                pygame.draw.rect(s, mix(CARD, GOLD, 0.16 + 0.08 * math.sin(app.time * 4)), glow, border_radius=8)
            end = app.key_box(s, key, left, y) if key else left - 7
            app.text(s, fit(app, words, 22, box.right - 8 - end - 7), (end + 7, y + 3), 22,
                     GOLD if hot else G.TEXT if key else G.DIM)
        y += step


def footer(app, x, y, w):
    """H (every key) and P (pause), small, at the very bottom."""
    G = _g(app)
    s, st = app.screen, state(app)
    px = x + 2
    for key, words in hud.footer_keys():
        end = app.key_box(s, key, px, y + 4)
        said = app.text(s, words, (end + 6, y + 7), 22, G.DIM)
        st.spots["key:" + key] = pygame.Rect(px - 2, y, said.right - px + 6, 30)
        px = said.right + 22


# ===========================================================================
# The bottom: the message box, the little map and the toasts
# ===========================================================================

def draw_log(app):
    G = _g(app)
    s, game, st = app.screen, app.game, state(app)
    s.fill(theme.LOG_BG, (0, G.VIEW_H, G.VIEW_W, G.LOG_H))
    pygame.draw.line(s, theme.DIVIDER, (0, G.VIEW_H), (G.VIEW_W, G.VIEW_H), 2)
    with_map = not game.cave
    box = pygame.Rect(8, G.VIEW_H + 8, G.VIEW_W - 16 - (MAP_W if with_map else 0), G.LOG_H - 16)
    draw_messages(app, box)
    if with_map:
        draw_little_map(app, pygame.Rect(box.right + 10, G.VIEW_H + 6, MAP_W - 12, G.LOG_H - 12))
    draw_toasts(app)


def draw_messages(app, box):
    """The newest message, big, with its picture; older ones small under it."""
    G = _g(app)
    s, game, st = app.screen, app.game, state(app)
    feed = st.feed
    st.spots["log"] = box
    messages = game.messages
    newest_kind = messages[-1][1] if messages else "info"
    color = G.KIND_COLORS.get(newest_kind, G.TEXT)
    glow = feed.glow()
    pygame.draw.rect(s, mix(BOX_BG, color, 0.10 * glow), box, border_radius=12)
    pygame.draw.rect(s, mix(CARD_EDGE, color, glow), box, 2 + (1 if glow > 0.6 else 0), border_radius=12)
    if not messages:
        return
    text, kind = messages[-1]
    left = box.x + 70
    width = box.right - 16 - left
    lines = app.wrap(text, 30, width)[:3]
    slide = slide_in(app)
    # its picture, in a badge that hops when the message is new
    badge = pygame.Rect(box.x + 12, box.y + 10, 46, 46)
    badge.y -= int(abs(math.sin(feed.age() * 9)) * 6 * max(0.0, 1 - feed.age() / 0.7))
    pygame.draw.rect(s, mix(theme.BAR_BACK, color, 0.25), badge, border_radius=10)
    pygame.draw.rect(s, color, badge, 2, border_radius=10)
    picture = icon(app, hud.icon_for(text, kind))
    s.blit(picture, picture.get_rect(center=badge.center))
    y = box.y + 10 + int((1 - slide) * 12)
    for line in lines:
        app.text(s, line, (left, y), 30, color, alpha=None if slide >= 1 else int(255 * slide))
        y += 30
    # older ones: one small line each, as many as fit
    y = box.y + 10 + 30 * len(lines) + 6
    for old, old_kind in reversed(messages[-4:-1]):
        if y + 20 > box.bottom - 6:
            break
        faded = mix(G.KIND_COLORS.get(old_kind, G.TEXT), BOX_BG, 0.45)
        pygame.draw.circle(s, faded, (left + 5, y + 9), 3)
        app.text(s, fit(app, old, 22, width - 70), (left + 16, y), 22, faded)
        y += 21
    if len(messages) > 1:                               # L: read the old ones
        end = app.key_box(s, "L", box.right - 62, box.bottom - 30)
        app.text(s, "log", (end + 5, box.bottom - 27), 20, G.DIM)


def slide_in(app):
    """How far the newest message has slid in (1 = all the way). Under a card or a menu the message
    clock stands still, so there it's just shown."""
    return state(app).feed.slide() if app.state in hud.LIVE_STATES else 1.0


def map_spot(rect, scale, pos):
    return rect.x + int((pos[1] + 0.5) * scale), rect.y + int((pos[0] + 0.5) * scale)


def draw_little_map(app, area):
    """The whole world, small, with a gold pin where to go next. Nightfall Hollow keeps the classic map."""
    G = _g(app)
    s, game, st = app.screen, app.game, state(app)
    if not draw_world.is_world(app):
        app.draw_minimap(area.x, area.y - 2, area.w, area.bottom)
        return
    small = draw_world.minimap_picture(app)
    scale = min(area.w / game.cols, area.h / game.rows)
    rect = pygame.Rect(0, 0, int(game.cols * scale), int(game.rows * scale))
    rect.center = area.center
    over = rect.collidepoint(st.mouse)
    s.blit(pygame.transform.scale(small, rect.size), rect)
    draw_map_marks(app, rect, scale, 3)
    cam = pygame.Rect(rect.x + int(app.cam[0] / draw_world.TILE * scale), rect.y + int(app.cam[1] / draw_world.TILE * scale),
                      int(G.VIEW_W / draw_world.TILE * scale), int(G.VIEW_H / draw_world.TILE * scale))
    pygame.draw.rect(s, (230, 232, 244), cam, 1)
    pygame.draw.rect(s, GOLD if over else CARD_EDGE, rect.inflate(4, 4), 2, border_radius=4)
    app.key_box(s, "B", rect.x + 2, rect.y + 2)
    st.spots["map"] = rect


def draw_map_marks(app, rect, scale, dot):
    """Waystones, treasure you spotted, the pin for what's next, and you."""
    G = _g(app)
    s, game = app.screen, app.game

    def mark(pos, color, size):
        x, y = map_spot(rect, scale, pos)
        s.fill((20, 20, 30), (x - size // 2 - 1, y - size // 2 - 1, size + 2, size + 2))
        s.fill(color, (x - size // 2, y - size // 2, size, size))

    blink = int(app.time * 3) % 2 == 0
    for spot in game.waystones:
        mark(spot, (90, 230, 240) if spot in game.unlocked_waystones else (70, 80, 100), dot)
    for spot in game.found_chests:
        if game.tile(spot) == "T":
            mark(spot, GOLD, dot + 1)
    target = hud.next_goal(game)["target"]
    if target and target != game.player.pos:
        draw_pin(app, map_spot(rect, scale, target), dot)
    if blink or dot > 3:
        mark(game.player.pos, (255, 255, 255) if blink else GOLD, dot + 1)


def draw_pin(app, spot, dot, still=False):
    """The gold pin for where to go next: it hops, and a ring spreads out from it (still: it just sits there)."""
    s = app.screen
    x, y = spot
    size = dot + 3
    hop = 0 if still else int(abs(math.sin(app.time * 4)) * 3)
    ring = (app.time * 1.2) % 1.0
    if not still:
        pygame.draw.circle(s, mix(GOLD, (60, 50, 20), ring), (x, y), int(size + ring * size * 2.5), 1)
    points = [(x, y - hop), (x - size, y - size * 2 - hop), (x + size, y - size * 2 - hop)]
    pygame.draw.polygon(s, GOLD, points)
    pygame.draw.polygon(s, (60, 40, 10), points, 1)
    pygame.draw.circle(s, GOLD, (x, y - size * 2 - hop), size)
    pygame.draw.circle(s, (60, 40, 10), (x, y - size * 2 - hop), size, 1)
    pygame.draw.circle(s, (255, 250, 220), (x, y - size * 2 - hop), max(1, size // 2))


def draw_toasts(app):
    """Big news (a quest, treasure, a level up) pops up at the top of the map for a few seconds."""
    G = _g(app)
    s, st = app.screen, state(app)
    if app.state not in hud.LIVE_STATES:
        return
    cave = app.game.cave
    y = 96 if cave and getattr(cave, "is_throne_room", False) else 14      # under the Shadow King's name and bar
    room = G.VIEW_W - 160
    for text, kind, solid in st.feed.showing():
        color = G.KIND_COLORS.get(kind, G.TEXT)
        size = 28 if app.font(28).size(text)[0] <= room else 24             # long news: smaller letters first,
        words = fit(app, text, size, room)                                  # and only then "..."
        width = app.font(size).size(words)[0] + 70
        pill = pygame.Rect(0, 0, width, 42)
        pill.midtop = (G.VIEW_W // 2, y - int((1 - solid) * 10))
        picture = icon(app, hud.icon_for(text, kind))
        if picture.get_height() > 30:
            picture = small(app, hud.icon_for(text, kind), 28) if hud.icon_for(text, kind) in app.art else picture
        target = s
        if solid < 1:                                   # fading in or out: paint it on glass first
            target = pygame.Surface(pill.size, pygame.SRCALPHA)
            pill = pill.copy()
            where, pill.topleft = pill.topleft, (0, 0)
        pygame.draw.rect(target, BOX_BG, pill, border_radius=21)
        pygame.draw.rect(target, color, pill, 3, border_radius=21)
        target.blit(picture, picture.get_rect(center=(pill.x + 30, pill.centery)))
        app.text(target, words, (pill.x + 54, pill.centery + 1), size, color, "midleft")
        if target is not s:
            target.set_alpha(int(255 * solid))
            s.blit(target, where)
        y += 50


# ===========================================================================
# Every frame, and the keys and the mouse
# ===========================================================================

def update(app, dt):
    st, game = state(app), app.game
    live = app.state in hud.LIVE_STATES and not game.story
    if live:
        before = st.feed.newest_at
        new = st.feed.take(game.messages)
        if any(hud.is_toast(text, kind) for text, kind in new) and before is not None:
            app.sounds.play("page")                     # a soft sound with a toast, so you look up
    elif app.state == "levelup":
        st.feed.take(game.messages, skip=hud.CARD_NEWS)  # the LEVEL UP! card says it: no toast after it too
    st.feed.update(dt, live)
    if st.screen and app.state != "people":
        st.screen = None                                # something else took over (a fight, a story card)


def spot_at(app, pos):
    st = state(app)
    for name, rect in st.spots.items():
        if name != "goal" and rect.collidepoint(pos):
            return name
    return "goal" if "goal" in st.spots and st.spots["goal"].collidepoint(pos) else None


def open_page(app, kind):
    st = state(app)
    st.screen, st.back, st.scroll, st.pinned = kind, app.state, 0, None
    app.people_screen = draw_people.Screen("hud")       # ("people" pauses the game under a Phase 2 page)
    app.state = "people"
    app.sounds.play("page")


def close_page(app):
    st = state(app)
    st.screen = None
    app.people_screen = None
    app.state = st.back


def on_event(app, event):
    """Keys and clicks for the HUD. Returns True if it used the event."""
    st, game = state(app), app.game
    if st.screen and app.state == "people" and getattr(app.people_screen, "kind", None) == "hud":
        page_event(app, event)
        return True
    if app.state not in ("play", "cave") or game.over or getattr(game, "travel_open", False):
        return False
    if event.type == pygame.MOUSEMOTION:
        st.mouse = event.pos
        return False
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        st.mouse = event.pos
        name = spot_at(app, event.pos)
        action = hud.CLICKS.get(name)
        if action == "quests" and game.cave:
            action = None                               # (the quest log opens on the map)
        if action == "quests":
            draw_people.open_screen(app, "quests")
        elif action:
            open_page(app, action)
        elif name and name.split(":")[0] in ("item", "power"):
            st.pinned = None if st.pinned == name else name
        else:
            st.pinned = None
            return False
        return True
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_l:
            open_page(app, "log")
        elif event.key == pygame.K_b and draw_world.is_world(app) and not game.cave:
            open_page(app, "map")
        elif event.key == pygame.K_h:
            open_page(app, "keys")
        else:
            st.pinned = None
            return False
        return True
    return False


def page_event(app, event):
    st = state(app)
    if event.type == pygame.MOUSEMOTION:
        st.mouse = event.pos
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        close_page(app)
    elif event.type == pygame.MOUSEWHEEL and st.screen == "log":
        st.scroll = max(0, st.scroll + event.y * 2)
    elif event.type == pygame.KEYDOWN:
        if st.screen == "log" and event.key in (pygame.K_UP, pygame.K_w, pygame.K_PAGEUP):
            st.scroll += 3
        elif st.screen == "log" and event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_PAGEDOWN):
            st.scroll = max(0, st.scroll - 3)
        elif st.screen == "keys" and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            back = st.back
            close_page(app)
            app.return_state = back                     # on to the big How to Play page
            app.state = "help"
        elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE,
                           pygame.K_l, pygame.K_b, pygame.K_h, pygame.K_q):
            close_page(app)


# ===========================================================================
# The pages: the message log (L), the big map (B), every key (H); and the tooltip
# ===========================================================================

def draw_screens(app):
    """Draws our page if one is open (returns True), else the tooltip under the mouse."""
    st = state(app)
    if st.screen and app.state == "people" and getattr(app.people_screen, "kind", None) == "hud":
        {"log": draw_log_page, "map": draw_big_map, "keys": draw_keys_page}[st.screen](app)
        return True
    if app.state in ("play", "cave") and not getattr(app.game, "travel_open", False):
        draw_tooltip(app)
    return False


def page_box(app, w, h, title, edge=GOLD):
    G = _g(app)
    app.dim_screen(160)
    box = pygame.Rect(0, 0, w, h)
    box.center = (G.WIDTH // 2, G.HEIGHT // 2)
    pygame.draw.rect(app.screen, BOX_BG, box, border_radius=18)
    pygame.draw.rect(app.screen, edge, box, 3, border_radius=18)
    app.text(app.screen, title, (box.centerx, box.y + 16), 48, edge, "midtop", shadow=True)
    return box


def draw_log_page(app):
    G = _g(app)
    s, st = app.screen, state(app)
    box = page_box(app, 980, 660, "Messages")
    rows = []                                           # (line, colour, the message's picture or None)
    for text, kind in hud.log_lines(app.game.messages):
        color = G.KIND_COLORS.get(kind, G.TEXT)
        for i, line in enumerate(app.wrap(text, 26, box.w - 130)):
            rows.append((line, color, hud.icon_for(text, kind) if i == 0 else None))
    fits = (box.h - 150) // 28
    st.scroll = max(0, min(st.scroll, len(rows) - fits))
    last = len(rows) - st.scroll
    y = box.y + 84
    for n, (line, color, picture) in enumerate(rows[max(0, last - fits):last]):
        newest = st.scroll == 0 and n >= min(fits, len(rows)) - 1
        if picture:
            pygame.draw.circle(s, color, (box.x + 52, y + 10), 5)
        app.text(s, line, (box.x + 72, y), 26, color if picture or newest else mix(color, BOX_BG, 0.25))
        y += 28
    if len(rows) > fits:                                # a little bar: where you are in the list
        track = pygame.Rect(box.right - 26, box.y + 84, 6, fits * 28)
        pygame.draw.rect(s, theme.BAR_BACK, track, border_radius=3)
        size = max(30, track.h * fits // len(rows))
        top = track.y + (track.h - size) * (len(rows) - fits - st.scroll) // max(1, len(rows) - fits)
        pygame.draw.rect(s, GOLD, (track.x, top, 6, size), border_radius=3)
    ui.hints(app, [(("UP", "DOWN"), "older and newer"), ui.BACK], (box.centerx, box.bottom - 30))


def draw_big_map(app):
    """The whole world, big: the lands and villages by name, waystones, treasure, people who need you,
    the gold pin for what's next, and you."""
    G = _g(app)
    s, game, st = app.screen, app.game, state(app)
    scale = min((G.WIDTH - 120) // game.cols, (G.HEIGHT - 150) // game.rows)
    box = page_box(app, game.cols * scale + 48, game.rows * scale + 112, "The Map", (90, 230, 240))
    rect = pygame.Rect(box.x + 24, box.y + 66, game.cols * scale, game.rows * scale)
    small = draw_world.minimap_picture(app)
    key = (id(small), scale)
    if not st.big_map or st.big_map[0] != key:
        st.big_map = (key, pygame.transform.scale(small, rect.size))
    s.blit(st.big_map[1], rect)
    pygame.draw.rect(s, (20, 20, 30), rect.inflate(4, 4), 2)
    for who, spot in people.people_here(game):
        if draw_people.quest_mark(game, who):           # someone with a quest for you
            bang(app, map_spot(rect, scale, spot))
    taken = []                                          # where names already are, so no two sit on each other
    for village, spot, _ in game.atlas.villages:
        x, y = map_spot(rect, scale, spot)
        label = pygame.Rect(0, 0, app.font(22).size(village)[0] + 12, 20)
        label.midtop = (x, y + scale * 2)
        pygame.draw.rect(s, (28, 26, 40), label, border_radius=6)
        app.text(s, village, label.center, 22, (255, 236, 190), "center")
        taken.append(label)
    for name, top, left, bottom, right in [land[:5] for land in game.atlas.lands]:
        x, y = map_spot(rect, scale, ((top + bottom) / 2 - 0.5, (left + right) / 2 - 0.5))
        size = app.font(28).size(name)
        for nudge in (0, -34, 34, -68, 68, -102, 102):  # the first spot nothing else is on
            label = pygame.Rect(0, 0, size[0] + 8, size[1] + 4)
            label.center = (x, y + nudge)
            label.clamp_ip(rect)
            if label.collidelist(taken) < 0:
                break
        taken.append(label)
        app.text(s, name, label.center, 28, (255, 255, 255), "center", shadow=True)
    draw_map_marks(app, rect, scale, 5)
    goal = hud.next_goal(game)
    if goal["target"] and goal["target"] != game.player.pos:
        x, y = map_spot(rect, scale, goal["target"])
        app.text(s, "NEXT", (x, y - 34), 22, GOLD, "midbottom", shadow=True)
    x, y = map_spot(rect, scale, game.player.pos)
    app.text(s, "YOU", (x, y + 8), 20, (255, 255, 255), "midtop", shadow=True)
    # what the dots mean
    y = box.bottom - 26
    x = box.x + 30
    for color, words in (((255, 255, 255), "you"), ("pin", "go here next"), ("!", "someone needs you"),
                         ((90, 230, 240), "waystone (lit)"), ((70, 80, 100), "waystone (not lit yet)"),
                         (GOLD, "treasure")):
        if color == "pin":
            draw_pin(app, (x + 6, y + 9), 3, still=True)
        elif color == "!":
            bang(app, (x + 6, y))
        else:
            pygame.draw.rect(s, (20, 20, 30), (x - 1, y - 7, 14, 14))
            pygame.draw.rect(s, color, (x, y - 6, 12, 12))
        said = app.text(s, words, (x + 20, y), 22, G.TEXT, "midleft")
        x = said.right + 24
    ui.hints(app, [ui.BACK], (box.right - 30, y), "right")


def bang(app, spot):
    """A gold "!" on the big map: someone here has a quest for you."""
    pygame.draw.circle(app.screen, (40, 30, 10), spot, 9)
    pygame.draw.circle(app.screen, GOLD, spot, 7)
    app.text(app.screen, "!", (spot[0], spot[1] + 1), 22, (60, 40, 10), "center")


def draw_keys_page(app):
    G = _g(app)
    s = app.screen
    box = page_box(app, 1040, 520, "Every Key")
    have, total = hud.stones(app.game)
    app.text(s, "Find the %d Light Stones, wake the Portal, and beat the Shadow King!" % total,
             (box.centerx, box.y + 76), 28, G.TEXT, "midtop")
    column = (box.w - 80) // 3
    for i, (heading, keys) in enumerate(hud.all_keys()):
        x, y = box.x + 44 + i * column, box.y + 130
        app.text(s, heading, (x, y), 30, G.ORANGE)
        y += 42
        for key, words in keys:
            end = app.key_box(s, key, x, y)
            app.text(s, words, (end + 10, y + 2), 24, G.TEXT)
            y += 36
    ui.hints(app, [("ENTER", "the big How to Play page"), ui.BACK], (box.centerx, box.bottom - 30))


def draw_tooltip(app):
    """A little box of words for the thing under the mouse (or the pack item you clicked)."""
    G = _g(app)
    s, st = app.screen, state(app)
    name = st.pinned if st.pinned in st.spots else spot_at(app, st.mouse)
    if name is None:
        return
    words = hud.tooltip(app.game, name)
    if not words:
        return
    title, text = words
    lines = app.wrap(text, 24, 300)
    width = max([app.font(28).size(title)[0]] + [app.font(24).size(line)[0] for line in lines]) + 28
    box = pygame.Rect(0, 0, width, 44 + 26 * len(lines) + 8)
    spot = st.spots[name]
    if spot.x >= G.VIEW_W:                              # on the panel: the box goes to its left
        box.topright = (min(spot.x, G.VIEW_W + 8) - 10, spot.y)
    else:                                               # at the bottom: the box goes above it
        box.midbottom = (spot.centerx, spot.y - 10)
    box.clamp_ip(pygame.Rect(6, 6, G.WIDTH - 12, G.HEIGHT - 12))
    pygame.draw.rect(s, (28, 26, 40), box, border_radius=12)
    pygame.draw.rect(s, GOLD, box, 2, border_radius=12)
    app.text(s, title, (box.x + 14, box.y + 10), 28, GOLD)
    y = box.y + 42
    for line in lines:
        app.text(s, line, (box.x + 14, y), 24, G.TEXT)
        y += 26
