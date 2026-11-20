"""
PHASE 2 - a bigger Adventure World (see PHASE2.md).

The title screen offers Classic or Phase 2. Phase 2 is the classic game (game.App draws it, and
its caves, castle and Shadow King are the classic ones) on a world of its own:

- world_map.py  the big map, stitched from one text file per land in levels/world/
- world.py      Phase2Game: rules.Game on that map, with no fog, saving by itself
- save.py       saving to a JSON file (or the browser's storage) and loading it back, in 3 save slots
- pause.py      the pause menu (P or ESC: Resume, Save, Save and go to the title, Quit) and the slot list
- monsters.py   monsters you can see on the map: each land its own, they roam freely (patrol and chase),
                night and day
- smooth.py     the Hero walks smoothly on the map while a move key is held (not a square at a time)
- fight.py      the timing strike in fights, and the first strike from behind
- draw_fight.py drawing the timing bar, the night sky and what monsters are up to
- theme.py      the teen look: the game's name (GAME_NAME), every colour, the dusk over the map, the
                map tune; draw_theme.py draws the dusk and the title's name
- waystones.py  waystones (fast travel), lookouts, hidden chests and gates on the big map
- draw_world.py how the new lands, waystones, lookouts and the travel list look
- people.py     townsfolk (phase2/data/people.json), what they say (dialogue.py), the shop (shop.py),
                quests (quests.py); draw_people.py draws them, the dialogue box, the shop and the quest log
- main_quest.py the main quest (phase2/data/main_quest.json): a Light Stone in every land, the Portal,
                the Shadow King, and an ending that takes you home to keep playing
- keys.py       Phase 2's keys: R attacks everywhere (fights, caves, castle, throne); G digs, opens, pulls
- hud.py        what the side panel and the message box show: only the things you have, a NEXT card,
                the keys that matter here, messages that glow and pop up; draw_hud.py draws it, and
                the message log (L), the big map (B) and the page of every key (H)

game.py only calls the few functions below. Nothing in phase2/ imports game.py.
"""

import pygame

from phase2 import draw_fight, draw_theme, draw_world, fight, keys, monsters, pause, save, smooth, theme
from phase2.world import Phase2Game

has_save = save.has_save
newest_slot = save.newest_slot


def new_game(player_name, seed=None, slot=1):
    game = Phase2Game(player_name, seed=seed)
    game.save_slot = slot
    return game


def load_game(slot=1):
    """The Phase 2 game saved in this slot, or None."""
    return save.load_game(slot)


def is_phase2(game):
    return isinstance(game, Phase2Game)


def on_quit(game):
    """The window is closing (or ESC): a Phase 2 game saves itself."""
    if is_phase2(game) and not getattr(game, "skip_quit_save", False):   # (Quit -> "Save first?" No)
        game.autosave()


# ----- the keys (phase2/keys.py): R attacks everywhere in Phase 2 -----

def battle_keys(game, classic):
    """Which key does what in a map fight: {key: action}. Phase 2: R attacks, X runs."""
    return keys.BATTLE_KEYS if is_phase2(game) else classic


def battle_buttons(game, classic):
    """The fight's buttons: [(action, key, words), ...]."""
    return keys.BATTLE_BUTTONS if is_phase2(game) else classic


def cave_controls(app, pressed, controls):
    """A cave's keys this frame. Phase 2: R only fights and G digs, opens and pulls."""
    return keys.cave_controls(app, pressed, controls) if is_phase2(app.game) else controls


def tip_words(game, name, classic):
    """A tip bubble's words: Phase 2 names its own keys in a few of them."""
    return keys.TIPS.get(name, classic) if is_phase2(game) else classic


def battle_action(game, action, time):
    """A key in a map fight. Phase 2 grades Attack with the timing bar first; Classic is unchanged."""
    if is_phase2(game):
        fight.battle_action(game, action, time)
    else:
        game.battle_action(action)


def draw_battle(app):
    if is_phase2(app.game):
        draw_fight.draw_strike_bar(app)


def draw_map(app, surf):
    if is_phase2(app.game):
        draw_fight.draw_map(app, surf)


def faces_left(game, monster):
    """Draw this map monster looking left? (Classic: they always look at you.)"""
    if is_phase2(game):
        return draw_fight.faces_left(game, monster)
    return game.player.pos[1] < monster.pos[1]


# ----- the map in real time (phase2/smooth.py): the Hero walks smoothly and monsters roam freely -----

def live_map(app, dt, held):
    """One frame on a Phase 2 map: he walks the way the held move keys say (`held`: "left", "up"...),
    and the monsters roam. Returns False in Classic (a key press is a whole step there)."""
    if not is_phase2(app.game):
        return False
    smooth.live(app, dt, held)
    return True


def map_spot(app, monster=None):
    """Where the Hero (or this monster) is on a Phase 2 map, in pixels: anywhere, not only on a square.
    None in Classic."""
    if not is_phase2(app.game):
        return None
    x, y = monsters.where(monster) if monster else smooth.where(app.game)
    return ((x - 0.5) * 64, (y - 0.5) * 64)


# ----- drawing the Phase 2 world (draw_world.py). Each does nothing in a classic game. -----

def build_tiles(app):
    """Returns True if it set up the map's tiles (lazily: the big map is painted as you see it)."""
    return draw_world.build_tiles(app)


def paint_tile(app, r, c):
    """Returns True if it painted this square (the new lands, waystones, lookouts, gates, hidden chests)."""
    return draw_world.paint_tile(app, r, c)


def draw_minimap(app, x, top, width, bottom, show_view=True):
    return draw_world.draw_minimap(app, x, top, width, bottom, show_view)


def on_play(app, event):
    """Returns True if the travel list used this key or click."""
    return draw_world.on_play(app, event)


def draw_over(app):
    draw_world.draw_over(app)


# ----- people, dialogue, the shop and the quest log (stage 2b: phase2/draw_people.py) -----

def on_event(app, event):
    """A key or click for a Phase 2 screen (talking, the shop, the quest log). True if it was ours."""
    if not is_phase2(app.game):
        return False
    from phase2 import draw_hud, draw_people
    if draw_hud.on_event(app, event):       # the HUD: L the message log, B the big map, H every key, the mouse
        return True
    if app.state not in ("play", "people"):
        return False
    return draw_people.on_event(app, event)


def update_screens(app, dt):
    if is_phase2(app.game):
        app.game.play_time = getattr(app.game, "play_time", 0.0) + dt     # (not while paused: no update then)
        from phase2 import draw_hud, draw_people
        draw_people.update(app, dt)
        draw_hud.update(app, dt)            # new messages glow and pop up


def draw_on_map(app, surf):
    if is_phase2(app.game):
        from phase2 import draw_people
        draw_people.draw_on_map(app, surf)


def draw_screens(app):
    if is_phase2(app.game):
        from phase2 import draw_hud, draw_people
        if not draw_hud.draw_screens(app):  # the message log, the big map, every key; or the mouse's tooltip
            draw_people.draw_screens(app)


# ----- the side panel and the message box (phase2/hud.py, phase2/draw_hud.py) -----

def draw_panel(app):
    """Returns True if it drew Phase 2's side panel (Classic draws its own)."""
    if not is_phase2(app.game):
        return False
    from phase2 import draw_hud
    draw_hud.draw_panel(app)
    return True


def draw_log(app):
    """Returns True if it drew Phase 2's message box and map (Classic draws its own)."""
    if not is_phase2(app.game):
        return False
    from phase2 import draw_hud
    draw_hud.draw_log(app)
    return True


def help_lines(game, lines):
    """The How to Play page's lines: in Phase 2 the GOAL is the 7 Light Stones, not Classic's quests."""
    if not is_phase2(game):
        return lines
    return [lines[0],
            ("Find the 7 Light Stones, one in every land. Press Q for your quests.", lines[1][1]),
            ("The Portal wakes up (take a boat to its island). Beat the Shadow King!", lines[2][1])] + [
                (words.replace("Field: open grass", "Field: open ground"), color) for words, color in lines[3:]]


TAGLINE = theme.TAGLINE         # under the title (phase2/theme.py has the name, the colours, the dusk)


# ----- the teen look (phase2/theme.py, drawn by draw_theme.py). Each gives Classic its own value. -----
def color(app, name, classic):
    """A colour game.py draws with: Phase 2's darker one (theme.COLORS[name]) or Classic's."""
    return theme.COLORS[name] if is_phase2(getattr(app, "game", None)) else classic


def tune(app, name):
    """The tune to play: Phase 2's map has its own darker one; everything else is Classic's."""
    if name == "home" and is_phase2(app.game) and app.state != "title" and not app.game.cave:
        return theme.MAP_TUNE
    return name


def draw_dusk(app, surf):
    if is_phase2(app.game):
        draw_theme.draw_dusk(app, surf)


def draw_title(app, top):
    """Phase 2 (or Load) picked on the title: its own name, goal and darker sky. False: Classic's title."""
    if app.mode == "classic":
        return False
    draw_theme.draw_title(app, top)
    return True


def set_caption(game):
    """The window's name: Phase 2's name in a Phase 2 game, Classic's in Classic."""
    pygame.display.set_caption(theme.GAME_NAME if is_phase2(game) else theme.CLASSIC_NAME)


def end_stats(game, stats):
    """The numbers on the Game Over box: Phase 2 counts Light Stones, not Classic's diamonds."""
    if not is_phase2(game):
        return stats
    from phase2 import hud
    return [("Light Stones", "%d of %d" % hud.stones(game)) if label == "Diamonds" else (label, value)
            for label, value in stats]


# ----- the new art (phase2/art.py) -----

def king_look(app):
    """Phase 2's Shadow King in the throne room: (pictures, glows, pixels under his feet). None in Classic."""
    from phase2 import art
    return art.king_look(app)


def monster_picture(app, kind, scale):
    """Phase 2's new picture of a monster, as big as its old one at `scale`. None in Classic, and for a
    monster that keeps its old picture (the Skeleton and the Ember Skull)."""
    from phase2 import art
    return art.monster_picture(app, kind, scale)


def king_card(app):
    """Phase 2's Shadow King on a story card. None in Classic."""
    from phase2 import art
    return art.king_card(app)


# ----- the pause menu and the save slots (phase2/pause.py) -----

def pause_event(app, event):
    """P or ESC opens the pause menu; while it's open it gets every key and click. True if it was ours."""
    return pause.on_event(app, event)


def paused(app):
    return pause.is_open(app)


def draw_pause(app):
    pause.draw(app)


def open_slots(app):
    """ENTER on the title screen: True if it opened the slot list (Load, or Phase 2 with a save somewhere)."""
    return pause.open_slots(app)


def title_event(app, event):
    return pause.title_event(app, event)


def draw_slots(app):
    pause.draw_slots(app)


# The Hero at 32 x 32, new monster art in caves and crisp map monsters (phase2/hero.py). Each gives None in Classic.

def hero_views(app):
    """The Hero's 32 x 32 cave pictures (side, ladder, wall)."""
    from phase2 import hero
    return hero.views(app)


def hero_map(app, name, pose):
    """The Hero on the map: 64 pixels, drawn at the corner of his square."""
    from phase2 import hero
    return hero.map_picture(app, name, pose)


def hero_fight(app, armored):
    """The Hero in a map fight, and where his sword hand is: (picture, hand)."""
    from phase2 import hero
    picture = hero.fight_picture(app, armored)
    return (picture, hero.fight_hand(app)) if picture else None


def hero_card(app):
    """The Hero on a story card."""
    from phase2 import hero
    return hero.card_picture(app)


def cave_picture(letters, scale):
    """The picture of 32 x 32 cave art, as big as 16 x 16 art at `scale`. None for the old art."""
    from phase2 import hero
    return hero.cave_picture(letters, scale)


def art_pixel(letters, scale):
    """How big one square of a cave picture is: `scale`, or half of it for 32 x 32 art."""
    from phase2 import hero
    return hero.art_pixel(letters, scale)


def cave_monster_art(app, kind):
    """A monster's new letters in a Phase 2 cave."""
    from phase2 import hero
    return hero.cave_monster_art(app, kind)


def map_monster_scale(app, kind):
    """The scale that draws a new monster crisp on the map (64 pixels)."""
    from phase2 import hero
    return hero.map_monster_scale(app, kind)
