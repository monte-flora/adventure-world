"""
THE PAUSE MENU and THE SAVE SLOTS (Phase 2 only).

P (or ESC) on the map, in a cave, in the castle or Nightfall Hollow, or in a map fight opens the
pause menu over the game, dimmed and frozen: nothing moves or ticks while it's open (game.App.step
doesn't call update() at all), and the music plays on quietly.

    Resume                     back to the game
    Save game                  saves into this game's slot ("Game saved!")
    Save and go to the title
    Quit                       asks "Save first?"  Yes / No / Back

UP/DOWN and ENTER (or the mouse) pick; ESC or P closes it. While a dialogue box, the shop, the forge
or a tip bubble is open, ESC still closes that (P still pauses).

On the title screen, ENTER on "Load" (or on "Phase 2", once any slot has a save) opens the slot
list: 3 slots, each with its name, land, level, Light Stones, play time and the date it was saved.
D deletes a slot (after a "Sure?").

The saving itself is in save.py. Nothing here imports game.py: its helpers come from the App's module.
"""

import sys

import pygame

import rules
from phase2 import main_quest, save, theme, ui

MENU = [("resume", "Resume"), ("save", "Save game"), ("title", "Save and go to the title"), ("quit", "Quit")]
QUIT_MENU = [("yes", "Yes"), ("no", "No"), ("back", "Back")]
SURE_MENU = [("yes", "Yes"), ("no", "No")]
PAUSE_STATES = ("play", "cave", "battle", "people", "tip", "forge")   # where P pauses
ESC_STATES = ("play", "cave", "battle")                               # where ESC pauses too
QUIET = 0.35                    # the music plays this loud (of its normal loudness) while paused
UP_KEYS = (pygame.K_UP, pygame.K_w, pygame.K_LEFT)        # (LEFT/RIGHT for Yes / No side by side)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT)
PICK_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
BOX_BG = theme.BOX_BG            # (phase2/theme.py)
ROW_LIGHT = theme.ROW_LIGHT


def _g(app):
    """game.py (it may be called __main__, so we find it from the App)."""
    return sys.modules[type(app).__module__]


def _is_phase2(game):
    return getattr(game, "phase2", False)


class Menu:
    """A list of choices: which one is lit, and where each one is (for the mouse)."""

    def __init__(self, page, rows, row=0):
        self.page = page
        self.rows = rows
        self.row = row
        self.spots = []                 # [(rect, row number)] where the rows were drawn
        self.message = None

    def key(self, key):
        """UP/DOWN move the light. Returns the picked choice for ENTER, else None."""
        if key in UP_KEYS:
            self.row = (self.row - 1) % len(self.rows)
        elif key in DOWN_KEYS:
            self.row = (self.row + 1) % len(self.rows)
        elif key in PICK_KEYS:
            return self.rows[self.row][0]
        return None

    def mouse(self, event):
        """Hover lights a row, a click picks it. Returns the picked choice, else None."""
        for rect, number in self.spots:
            if rect.collidepoint(event.pos):
                self.row = number
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    return self.rows[number][0]
        return None


def pick(menu, event):
    if event.type == pygame.KEYDOWN:
        return menu.key(event.key)
    if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN) and hasattr(event, "pos"):
        return menu.mouse(event)
    return None


# ===========================================================================
# The pause menu
# ===========================================================================

def is_open(app):
    return getattr(app, "pause_menu", None) is not None


def wants_pause(app, event):
    """Does this key open the pause menu? (Phase 2 only.)"""
    game = app.game
    if event.type != pygame.KEYDOWN or not _is_phase2(game) or game.over:
        return False
    if event.key == pygame.K_p:
        return app.state in PAUSE_STATES
    if event.key == pygame.K_ESCAPE:
        return app.state in ESC_STATES and not getattr(game, "travel_open", False)
    return False


def open_menu(app):
    app.pause_menu = Menu("menu", MENU)
    app.pause_frame = app.screen.copy()          # the frozen game under the menu
    _music_volume(app, QUIET)


def close(app):
    app.pause_menu = None
    app.pause_frame = None
    _music_volume(app, 1.0)


def _music_volume(app, part):
    music = getattr(app, "music", None)
    channel = getattr(music, "channel", None)
    if channel is not None:
        loud = _g(app).MUSIC_VOLUME * part
        channel.set_volume(loud)
        music.old_channel.set_volume(loud)


def on_event(app, event):
    """Returns True if the pause menu used this event (or it opened the menu)."""
    if not is_open(app):
        if wants_pause(app, event):
            open_menu(app)
            return True
        return False
    menu = app.pause_menu
    if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
        if menu.page == "quit":
            app.pause_menu = Menu("menu", MENU, row=3)
        else:
            close(app)
        return True
    choice = pick(menu, event)
    if choice:
        choose(app, choice)
    return True


def save_words(game, saved):
    """What the menu says after Save game."""
    if not saved:
        return "Couldn't save the game!"
    if game.cave:
        place = "the castle" if game.cave.is_castle else "this Mine"
        return "Saved. You'll start outside %s." % place
    return "Game saved!"


def save_now(game):
    """Save, even in a fight (the fight itself isn't saved: you load on the map, next to the monster)."""
    if game.over:
        return False
    return save.save_game(game)


def choose(app, choice):
    game, menu = app.game, app.pause_menu
    if choice == "resume":
        close(app)
    elif choice == "save":
        menu.message = save_words(game, save_now(game))
    elif choice == "title":
        save_now(game)
        close(app)
        go_to_title(app)
    elif choice == "quit":
        app.pause_menu = Menu("quit", QUIT_MENU)
    elif choice == "yes":
        save_now(game)
        app.running = False
    elif choice == "no":
        game.skip_quit_save = True              # (closing doesn't save by itself this time)
        app.running = False
    elif choice == "back":
        app.pause_menu = Menu("menu", MENU, row=3)


def go_to_title(app):
    """Back to the title screen, with a classic world drifting behind it (like when the game starts)."""
    app.name_input = app.game.player.name
    app.game = rules.Game(app.name_input, seed=app.seed)
    app.state = "title"
    app.in_intro = False
    app.build_tiles()
    app.reset_visuals()
    refresh_modes(app)


def refresh_modes(app):
    """Load is on the title screen only while a slot has a save."""
    app.modes = ["classic", "phase2"] + (["continue"] if save.has_save() else [])
    if app.mode not in app.modes:
        app.mode = "phase2"


def info_lines(game):
    p = game.player
    land = game.land_name(p.pos) if game.world == 1 else "Nightfall Hollow"
    where = land or "the wild"
    if game.cave:
        where += " (in the castle)" if game.cave.is_castle else " (in a cave)"
    return ["%s  -  Level %d" % (where, p.level),
            "Light Stones: %d of %d" % (len(main_quest.relics(game)), main_quest.relics_needed()),
            "Play time: %s" % save.time_words(getattr(game, "play_time", 0.0))]


def draw(app):
    """The frozen game, dimmed, with the menu over it."""
    G, s, menu = _g(app), app.screen, app.pause_menu
    if app.pause_frame:
        s.blit(app.pause_frame, (0, 0))
    app.dim_screen(150)
    box = pygame.Rect(0, 0, 560, 520)
    box.center = (G.WIDTH // 2, G.HEIGHT // 2)
    app.panel_box(box)
    if menu.page == "quit":
        app.text(s, "Quit", (box.centerx, box.y + 26), 56, G.YELLOW, "midtop", shadow=True)
        app.text(s, "Save first?", (box.centerx, box.y + 110), 36, G.TEXT, "midtop")
        top = box.y + 190
    else:
        app.text(s, "Paused", (box.centerx, box.y + 26), 56, G.YELLOW, "midtop", shadow=True)
        y = box.y + 92
        for line in info_lines(app.game):
            app.text(s, line, (box.centerx, y), 26, G.DIM, "midtop")
            y += 28
        top = box.y + 190
    menu.spots = []
    for number, (_, words) in enumerate(menu.rows):
        row = pygame.Rect(box.x + 60, top + number * 52, box.width - 120, 44)
        lit = number == menu.row
        if lit:
            pygame.draw.rect(s, ROW_LIGHT, row, border_radius=10)
            pygame.draw.rect(s, G.YELLOW, row, 2, border_radius=10)
        app.text(s, words, row.center, 32, G.YELLOW if lit else G.TEXT, "center")
        menu.spots.append((row, number))
    if menu.message:
        app.text(s, menu.message, (box.centerx, box.bottom - 78), 28, G.GREEN, "midtop")
    ui.hints(app, [ui.PICK, ("ENTER", "choose"), ui.BACK], (box.centerx, box.bottom - 28))


# ===========================================================================
# The save slots, on the title screen
# ===========================================================================

class SlotList:
    def __init__(self, kind):
        self.kind = kind                # "load" or "new"
        self.infos = [save.slot_info(slot) for slot in save.SLOTS]
        used = [i for i, info in enumerate(self.infos) if not info["empty"]]
        empty = [i for i, info in enumerate(self.infos) if info["empty"]]
        self.row = (used or [0])[0] if kind == "load" else (empty or [0])[0]
        self.spots = []
        self.sure = None                # a Menu asking "Start over?" or "Delete?", and its slot
        self.message = None

    @property
    def slot(self):
        return self.infos[self.row]["slot"]

    @property
    def info(self):
        return self.infos[self.row]


def slots_open(app):
    return getattr(app, "slot_list", None) is not None


def open_slots(app):
    """ENTER on the title screen. Returns True if it opened the slot list (else the game just starts)."""
    if app.mode == "continue" and save.has_save():
        app.slot_list = SlotList("load")
        return True
    if app.mode == "phase2":
        if not save.has_save():
            app.save_slot = 1                   # every slot is empty: just start, in slot 1
            return False
        app.slot_list = SlotList("new")
        return True
    return False


def title_event(app, event):
    """A key or click on the title screen while the slot list is open. True if it was ours."""
    if not slots_open(app):
        return False
    slots = app.slot_list
    if slots.sure:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_n):
            slots.sure = None
            return True
        choice = "yes" if event.type == pygame.KEYDOWN and event.key == pygame.K_y else pick(slots.sure, event)
        if choice == "yes":
            confirmed(app, slots)
        elif choice == "no":
            slots.sure = None
        return True
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            app.slot_list = None
        elif event.key in UP_KEYS:
            slots.row = (slots.row - 1) % len(slots.infos)
        elif event.key in DOWN_KEYS:
            slots.row = (slots.row + 1) % len(slots.infos)
        elif event.key in PICK_KEYS:
            picked(app, slots)
        elif event.key == pygame.K_d and not slots.info["empty"]:
            slots.sure = Menu("delete", SURE_MENU, row=1)
    elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN) and hasattr(event, "pos"):
        for rect, number in slots.spots:
            if rect.collidepoint(event.pos):
                slots.row = number
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    picked(app, slots)
    return True                                  # (typing doesn't change your name while the list is open)


def picked(app, slots):
    info = slots.info
    if slots.kind == "load":
        if info["empty"]:
            slots.message = "That slot is empty."
        elif info.get("broken"):
            slots.message = "That save can't be read. D deletes it."
        else:
            start(app, info["slot"], "continue")
    elif info["empty"]:
        start(app, info["slot"], "phase2")
    else:
        slots.sure = Menu("start over", SURE_MENU, row=1)


def confirmed(app, slots):
    """Yes to "Start over in this slot?" or "Delete this slot?"."""
    page, slots.sure = slots.sure.page, None
    if page == "start over":
        save.delete_save(slots.slot)
        start(app, slots.slot, "phase2")
        return
    save.delete_save(slots.slot)
    slots.infos[slots.row] = save.slot_info(slots.slot)
    slots.message = "Slot %d is empty now." % slots.slot
    refresh_modes(app)
    if slots.kind == "load" and not save.has_save():
        app.slot_list = None                     # nothing left to load


def start(app, slot, mode):
    app.slot_list = None
    app.save_slot = slot
    app.mode = mode
    app.new_game()


def slot_words(info):
    """The 2 lines a slot shows in the list."""
    if info["empty"]:
        return "Empty", ""
    if info.get("broken"):
        return "A save that can't be read", ""
    first = "%s  -  %s  -  Level %d" % (info["name"], info["land"], info["level"])
    second = "Light Stones: %d of %d   -   played %s   -   saved %s" % (
        info["stones"], info["stones_needed"], save.time_words(info["play_time"]), save.date_words(info["saved_at"]))
    return first, second


def draw_slots(app):
    if not slots_open(app):
        return
    G, s, slots = _g(app), app.screen, app.slot_list
    app.dim_screen(170)
    box = pygame.Rect(0, 0, 900, 560)
    box.center = (G.WIDTH // 2, G.HEIGHT // 2)
    app.panel_box(box)
    title = "Load a game" if slots.kind == "load" else "Which slot for your new game?"
    app.text(s, title, (box.centerx, box.y + 24), 48, G.YELLOW, "midtop", shadow=True)
    slots.spots = []
    for number, info in enumerate(slots.infos):
        row = pygame.Rect(box.x + 40, box.y + 100 + number * 110, box.width - 80, 96)
        lit = number == slots.row
        pygame.draw.rect(s, ROW_LIGHT if lit else BOX_BG, row, border_radius=12)
        pygame.draw.rect(s, G.YELLOW if lit else theme.LIST_EDGE, row, 3 if lit else 2, border_radius=12)
        app.text(s, "Slot %d" % info["slot"], (row.x + 20, row.y + 14), 30, G.YELLOW if lit else G.DIM)
        first, second = slot_words(info)
        app.text(s, first, (row.x + 130, row.y + 14), 32, G.TEXT if not info["empty"] else G.DIM)
        if second:
            app.text(s, second, (row.x + 130, row.y + 54), 24, G.DIM)
        slots.spots.append((row, number))
    if slots.message:
        app.text(s, slots.message, (box.centerx, box.bottom - 82), 26, G.GREEN, "midtop")
    ui.hints(app, [ui.PICK, ("ENTER", "load" if slots.kind == "load" else "start here"), ("D", "delete"), ui.BACK],
             (box.centerx, box.bottom - 30))
    if slots.sure:
        draw_sure(app, slots)


def draw_sure(app, slots):
    G, s, sure = _g(app), app.screen, slots.sure
    question = ("Start over in this slot?" if sure.page == "start over" else "Delete slot %d?" % slots.slot)
    app.dim_screen(120)                 # the slot rows behind it go dark: only this box matters now
    box = pygame.Rect(0, 0, 520, 256)
    box.center = (G.WIDTH // 2, G.HEIGHT // 2)
    app.panel_box(box, G.RED)
    ui.hints(app, [(("LEFT", "RIGHT"), "pick"), ("ENTER", "choose"), ui.BACK], (box.centerx, box.bottom - 28))
    app.text(s, question, (box.centerx, box.y + 28), 36, G.TEXT, "midtop")
    app.text(s, "The saved game in it will be gone.", (box.centerx, box.y + 72), 24, G.DIM, "midtop")
    sure.spots = []
    for number, (_, words) in enumerate(sure.rows):
        row = pygame.Rect(box.centerx - 190 + number * 200, box.y + 140, 180, 50)
        lit = number == sure.row
        pygame.draw.rect(s, ROW_LIGHT if lit else BOX_BG, row, border_radius=10)
        pygame.draw.rect(s, G.YELLOW if lit else theme.LIST_EDGE, row, 2, border_radius=10)
        app.text(s, words, row.center, 32, G.YELLOW if lit else G.TEXT, "center")
        sure.spots.append((row, number))
