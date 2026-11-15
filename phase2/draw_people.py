"""
THE PICTURES AND KEYS for Phase 2's people: townsfolk on the map, the dialogue box, the shop and
the quest log (Q).

game.py calls the 4 functions at the top (through phase2/__init__.py). While one of these screens
is open, game.App's state is "people" and app.people_screen says which one:

    "talk"     the dialogue box: a portrait, the words typing out, ENTER or SPACE goes on,
               UP/DOWN and ENTER (or the mouse) pick a choice
    "shop"     buy and sell: UP/DOWN pick, ENTER buys or sells, LEFT/RIGHT switch Buy and Sell, ESC leaves
    "quests"   the quest log: what you're doing, and what you finished

The rules (who says what, prices, quests) are in people.py, dialogue.py, shop.py and quests.py.
Nothing here imports game.py: its helpers come from the module the App is in.
"""

import math
import sys

import pygame

import sprites
from phase2 import art, people, quests, shop, theme, ui

COIN = (250, 204, 60)
COIN_DARK = (176, 128, 30)
BOX_BG = theme.BOX_BG            # (phase2/theme.py)
ROW_LIGHT = theme.ROW_LIGHT
SOLD_OUT = (110, 108, 124)
PACE = 9                        # people who pace walk this many pixels to each side


def _g(app):
    """game.py (it may be called __main__, so we find it from the App)."""
    return sys.modules[type(app).__module__]


def _sprite(art, scale):
    surf = pygame.Surface((len(art[0]) * scale, len(art) * scale), pygame.SRCALPHA)
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.fill(sprites.COLORS[ch], (x * scale, y * scale, scale, scale))
    return surf


def picture(app, look, scale):
    return art.big_picture(look, scale)             # the new 32 x 32 pictures (phase2/art.py)


class Screen:
    def __init__(self, kind, who=None):
        self.kind = kind
        self.who = who
        self.tab = "buy"
        self.row = 0
        self.message = None
        self.rows = []                # [(rect, what it does)] for the mouse
        self.opened = 0.0


# ===========================================================================
# The 4 hooks game.py calls
# ===========================================================================

def on_event(app, event):
    """A key or a click. Returns True if it was ours (game.py then does nothing else with it)."""
    if app.state == "people":
        screen = getattr(app, "people_screen", None)
        if screen is None:
            app.state = "play"
            return True
        {"talk": talk_event, "shop": shop_event, "quests": quests_event}[screen.kind](app, screen, event)
        return True
    if (app.state == "play" and event.type == pygame.KEYDOWN and event.key == pygame.K_q
            and not app.game.over and not app.game.cave and not getattr(app.game, "travel_open", False)):
        open_screen(app, "quests")
        return True
    return False


def update(app, dt):
    game = app.game
    if app.state == "play" and getattr(game, "talk", None) and not game.battle and not game.over:
        open_screen(app, "talk", game.talk.person)
    if app.state != "people":
        return
    screen = app.people_screen
    if screen.kind == "talk":
        talk = game.talk
        if talk is None:
            close(app)
            return
        before = len(talk.shown)
        talk.update(dt)
        if len(talk.shown) > before and len(talk.shown) % 4 == 0:
            app.sounds.play("step")                 # a little tick as the words type out
        if talk.done:
            end_talk(app, talk)


def draw_on_map(app, surf):
    """The townsfolk on the world map (before the Hero, so he walks in front of them), and your gold."""
    game = app.game
    G = _g(app)
    for who, pos in people.people_here(game):
        x, y = app.on_screen(*G.tile_px(pos))
        if x < -G.TILE or y < -G.TILE or x > surf.get_width() or y > surf.get_height():
            continue
        art = picture(app, who["look"], 2)               # 32 x 32, 2 pixels each: one full map square
        seed = sum(map(ord, who["id"]))
        near = sum(abs(a - b) for a, b in zip(pos, game.player.pos)) == 1
        dx = 0
        if who.get("pace") and not near:                 # pacing a little, back and forth
            dx = PACE * math.sin(app.time * 0.9 + seed)
            if math.cos(app.time * 0.9 + seed) < 0:
                art = pygame.transform.flip(art, True, False)
            bob = abs(math.sin(app.time * 6 + seed)) * -3
        else:
            if game.player.pos[1] < pos[1]:
                art = pygame.transform.flip(art, True, False)
            bob = math.sin(app.time * 2 + seed) * 1.5
        surf.blit(app.shadow, (x + 14 + dx, y + 56))
        surf.blit(art, (x + dx, y + bob))
        mark = quest_mark(game, who)
        if mark:                                         # "!" over someone with a quest for you
            cx, cy = x + 32 + dx, y - 6 + math.sin(app.time * 4) * 3
            pygame.draw.circle(surf, (40, 30, 10), (int(cx), int(cy)), 13)
            pygame.draw.circle(surf, COIN, (int(cx), int(cy)), 11)
            app.text(surf, mark, (cx, cy + 1), 28, (60, 40, 10), "center")
        elif near:                                       # right next to you: "..." (they want to talk)
            bubble = pygame.Rect(0, 0, 38, 22)
            bubble.midbottom = (x + 32 + dx, y + 6)
            pygame.draw.rect(surf, (250, 250, 245), bubble, border_radius=10)
            pygame.draw.rect(surf, (28, 26, 38), bubble, 2, border_radius=10)
            for i in range(3):
                pygame.draw.circle(surf, (28, 26, 38), (bubble.x + 10 + i * 9, bubble.centery), 2)
    if game.world == 1:
        draw_gold(app, surf, (14, 14))


def draw_screens(app):
    if app.state != "people" or getattr(app, "people_screen", None) is None:
        return
    screen = app.people_screen
    {"talk": draw_talk, "shop": draw_shop, "quests": draw_quests}[screen.kind](app, screen)


# ===========================================================================
# Opening and closing
# ===========================================================================

def open_screen(app, kind, who=None):
    app.people_screen = Screen(kind, who)
    app.people_screen.opened = app.time
    app.people_return = "play"
    app.state = "people"
    app.sounds.play("page")


def close(app):
    app.people_screen = None
    app.game.talk = None
    app.state = getattr(app, "people_return", "play")


def end_talk(app, talk):
    then = talk.then
    app.game.talk = None
    close(app)
    if then and then[0] == "shop":
        open_screen(app, "shop", people.person(then[1]))
    elif then and then[0] == "forge":
        app.start_forge("play")                 # the classic forging game, at the blacksmith's anvil


def quest_mark(game, who):
    """"!" if this person has a quest for you that you haven't started yet."""
    from phase2 import main_quest
    if main_quest.wants_you(game, who["id"]):            # the main quest says: go and talk to them
        return "!"
    for qid, quest in quests.all_quests().items():
        if quest.get("giver") == who["id"] and quests.status(game, qid) == "new" and not quest.get("main"):
            return "!"
    return None


# ===========================================================================
# The dialogue box
# ===========================================================================

def talk_box(app):
    G = _g(app)
    return pygame.Rect(30, G.VIEW_H - 236, G.VIEW_W - 60, 216)


def talk_event(app, screen, event):
    talk = app.game.talk
    if talk is None:
        close(app)
        return
    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            talk.press()
        elif event.key in (pygame.K_UP, pygame.K_w):
            talk.move(-1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            talk.move(1)
        elif event.key == pygame.K_ESCAPE:
            talk.end()                          # walk away (nothing happens)
            talk.then = None
        else:
            return
    elif event.type == pygame.MOUSEMOTION:
        for rect, i in screen.rows:
            if rect.collidepoint(event.pos):
                talk.choice = i
        return
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for rect, i in screen.rows:
            if rect.collidepoint(event.pos) and talk.choices:
                talk.choose(i)
                break
        else:
            talk.press()
    else:
        return
    if talk.done:
        end_talk(app, talk)


def draw_talk(app, screen):
    G = _g(app)
    s, talk = app.screen, app.game.talk
    if talk is None:
        return
    who = talk.person
    box = talk_box(app)
    pygame.draw.rect(s, BOX_BG, box, border_radius=18)
    pygame.draw.rect(s, G.YELLOW, box, 3, border_radius=18)
    # the portrait, in a little frame
    frame = pygame.Rect(box.x + 18, box.y + 22, 172, 172)
    pygame.draw.rect(s, theme.FRAME_BG, frame, border_radius=12)
    pygame.draw.rect(s, theme.FRAME_EDGE, frame, 3, border_radius=12)
    face = art.portrait(who["look"])                # the big face, 160 x 160 (phase2/art.py)
    s.blit(face, face.get_rect(center=frame.center).move(0, 6))
    left = frame.right + 24
    choices = talk.choices
    column = pygame.Rect(box.right - 440, box.y + 14, 426, box.h - 28)    # the choices, on the right
    app.text(s, who["name"], (left, box.y + 16), 34, G.YELLOW, shadow=True)
    width = (column.x if choices else box.right) - left - 30
    y = box.y + 58
    full = app.wrap(talk.text, 30, width)        # wrap the whole page, then show what's typed so far
    left_to_show = len(talk.shown)
    for line in full:
        part = line[:max(0, left_to_show)]
        left_to_show -= len(line) + 1
        app.text(s, part, (left, y), 30, G.TEXT)
        y += 30
    screen.rows = []
    if choices:
        pygame.draw.line(s, theme.DIVIDER, (column.x - 12, column.y + 6), (column.x - 12, column.bottom - 6), 2)
        step = 42 if len(choices) <= 3 else 40          # (4 choices: a little closer, so the keys still fit)
        top = column.centery - (step * len(choices) + 26) // 2
        ui.hints(app, [ui.PICK, ("ENTER", "choose")], (column.centerx, top + step * len(choices) + 14))
        for i, choice in enumerate(choices):
            row = pygame.Rect(column.x, top + i * step, column.w, step - 4)
            picked = i == talk.choice
            if picked:
                pygame.draw.rect(s, ROW_LIGHT, row, border_radius=10)
                pygame.draw.rect(s, G.YELLOW, row, 2, border_radius=10)
            words = app.fit(talk.fill(choice["text"]), 28, row.w - 40)
            app.text(s, ("> " if picked else "  ") + words, (row.x + 10, row.centery), 28,
                     G.YELLOW if picked else G.TEXT, "midleft")
            screen.rows.append((row, i))
    elif not talk.typing and int(app.time * 2) % 2 == 0:
        ui.hints(app, [("ENTER", "next")], (box.right - 24, box.bottom - 26), "right")


# ===========================================================================
# The shop
# ===========================================================================

def shop_items(screen):
    return shop.buy_list(screen.who) if screen.tab == "buy" else shop.sell_list()


def shop_event(app, screen, event):
    game = app.game
    items = shop_items(screen)
    act = None
    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            close(app)
        elif event.key in (pygame.K_UP, pygame.K_w):
            screen.row = (screen.row - 1) % len(items)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            screen.row = (screen.row + 1) % len(items)
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d, pygame.K_TAB):
            switch_tab(screen)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            act = screen.row
    elif event.type == pygame.MOUSEMOTION:
        for rect, what in screen.rows:
            if rect.collidepoint(event.pos) and isinstance(what, int):
                screen.row = what
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for rect, what in screen.rows:
            if rect.collidepoint(event.pos):
                if what in ("buy", "sell"):
                    if what != screen.tab:
                        switch_tab(screen)
                elif what == "leave":
                    close(app)
                else:
                    screen.row = act = what
    if act is not None and app.state == "people":
        item = items[act]
        if screen.tab == "buy":
            worked, words = shop.buy(game, screen.who["id"], item)
        else:
            worked, words = shop.sell(game, item)
        screen.message = (words, worked)
        if not worked:
            app.sounds.play("miss")


def switch_tab(screen):
    screen.tab = "sell" if screen.tab == "buy" else "buy"
    screen.row = 0
    screen.message = None


def draw_shop(app, screen):
    G = _g(app)
    s, game = app.screen, app.game
    app.dim_screen(150)
    box = pygame.Rect(0, 0, 900, 600)
    box.center = (G.VIEW_W // 2, G.VIEW_H // 2 + 20)
    ui.box(app, box)
    ui.face(app, screen.who["look"], (box.x + 24, box.y + 20, 80, 80), 2)       # the shopkeeper's face
    app.text(s, screen.who["name"], (box.x + 120, box.y + 24), 40, G.YELLOW, shadow=True)
    draw_gold(app, s, (box.right - 190, box.y + 28))
    screen.rows = []
    for i, tab in enumerate(("buy", "sell")):
        rect = pygame.Rect(box.x + 120 + i * 150, box.y + 70, 140, 38)
        on = tab == screen.tab
        pygame.draw.rect(s, ROW_LIGHT if on else theme.SLOT, rect, border_radius=10)
        if on:
            pygame.draw.rect(s, G.YELLOW, rect, 2, border_radius=10)
        app.text(s, tab.capitalize(), rect.center, 30, G.YELLOW if on else G.DIM, "center")
        screen.rows.append((rect, tab))
    y = box.y + 130
    for i, item in enumerate(shop_items(screen)):
        row = pygame.Rect(box.x + 24, y, box.w - 48, 54)
        if screen.tab == "buy":
            problem = shop.buy_problem(game, screen.who["id"], item)
            left = shop.stock_left(game, screen.who["id"], item)
        else:
            problem, left = shop.sell_problem(game, item), None
        picked = i == screen.row
        if picked:
            pygame.draw.rect(s, ROW_LIGHT, row, border_radius=10)
            pygame.draw.rect(s, G.YELLOW, row, 2, border_radius=10)
        color = G.TEXT if problem is None else G.DIM if picked else SOLD_OUT     # (grey on the lit row: lighter)
        app.text(s, item["name"], (row.x + 16, row.centery), 32, G.YELLOW if picked and not problem else color,
                 "midleft")
        app.text(s, item["says"], (row.x + 260, row.centery), 24, G.DIM, "midleft")
        if left is not None:
            app.text(s, "sold out" if left == 0 else "%d left" % left, (row.x + 520, row.centery), 24,
                     G.RED if left == 0 else G.DIM, "midleft")
        draw_coin(s, (row.right - 120, row.centery))
        app.text(s, ("%d" if screen.tab == "buy" else "+%d") % item["price"], (row.right - 100, row.centery), 32,
                 COIN, "midleft")
        screen.rows.append((row, i))
        y += 60
    if screen.message:
        words, worked = screen.message
        app.text(s, words, (box.centerx, box.bottom - 80), 28, G.GREEN if worked else G.RED, "center")
    ui.hints(app, [ui.PICK, ("ENTER", screen.tab), (("LEFT", "RIGHT"), "buy or sell"), ui.BACK],
             (box.centerx, box.bottom - 30))


def draw_coin(surf, center, r=10):
    pygame.draw.circle(surf, COIN_DARK, center, r)
    pygame.draw.circle(surf, COIN, center, r - 2)
    pygame.draw.line(surf, COIN_DARK, (center[0], center[1] - r + 5), (center[0], center[1] + r - 5), 2)


def draw_gold(app, surf, topleft):
    G = _g(app)
    rect = pygame.Rect(topleft, (150, 36))
    pygame.draw.rect(surf, (28, 26, 38), rect, border_radius=12)
    pygame.draw.rect(surf, COIN_DARK, rect, 2, border_radius=12)
    draw_coin(surf, (rect.x + 20, rect.centery), 11)
    app.text(surf, "%d gold" % app.game.gold, (rect.x + 40, rect.centery + 1), 28, G.YELLOW, "midleft")


# ===========================================================================
# The quest log (Q)
# ===========================================================================

def quests_event(app, screen, event):
    if event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE, pygame.K_RETURN,
                                                       pygame.K_KP_ENTER, pygame.K_SPACE):
        close(app)
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        close(app)


def quest_lines(game):
    """What the quest log shows: [(title, step words, giver's name)], for active and finished quests."""
    def giver(quest):
        try:
            return people.person(quest["giver"])["name"]
        except KeyError:
            return None
    doing = [(quests.get(q)["title"], quests.step_text(game, q), giver(quests.get(q))) for q in quests.active(game)]
    done = [(quests.get(q)["title"], None, giver(quests.get(q))) for q in quests.finished(game)]
    return doing, done


def draw_quests(app, screen):
    G = _g(app)
    s, game = app.screen, app.game
    app.dim_screen(160)
    box = pygame.Rect(0, 0, 900, 620)
    box.center = (G.WIDTH // 2, G.HEIGHT // 2)       # in the middle of the window, like the L, B and H pages
    ui.box(app, box)
    app.text(s, "Quests", (box.centerx, box.y + 16), 48, G.YELLOW, "midtop", shadow=True)
    doing, done = quest_lines(game)
    y = box.y + 90
    app.text(s, "Doing now", (box.x + 40, y), 32, G.ORANGE)
    y += 40
    if not doing:
        app.text(s, "No quests yet. Talk to people: some of them need your help!", (box.x + 60, y), 26, G.DIM)
        y += 36
    for title, step, giver in doing:
        app.text(s, title + ("   (from %s)" % giver if giver else ""), (box.x + 60, y), 30, G.TEXT)
        y += 32
        for line in app.wrap(step or "", 26, box.w - 140):
            app.text(s, "- " + line, (box.x + 84, y), 26, G.YELLOW)
            y += 28
        y += 10
    y += 14
    app.text(s, "Finished", (box.x + 40, y), 32, G.GREEN)
    y += 40
    if not done:
        app.text(s, "None yet.", (box.x + 60, y), 26, G.DIM)
    for title, _, giver in done:
        if y > box.bottom - 80:
            break
        app.text(s, "v  " + title, (box.x + 60, y), 28, G.GREEN)
        y += 32
    ui.hints(app, [ui.BACK], (box.centerx, box.bottom - 30))
