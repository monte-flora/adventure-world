"""
Phase 2's look in one place: the game's name, every colour of its boxes and panel, the dusk over the
map, and its own map tune. Change a value here and the whole of Phase 2 changes. Classic never reads this.

The name: change GAME_NAME (and SUBTITLE) to rename Phase 2 everywhere (title screen, window, story).
Other names we thought of are in NAME_IDEAS.

The dusk: the Phase 2 map is drawn under a thin violet sky (DUSK, at DUSK_ALPHA), so the lands look like
the last hour before night, while the Hero, people and monsters (drawn on top) stay bright. dusk_alpha(game)
is the one place to ask how dark it is, so the world can grow darker as the story goes on.
"""

GAME_NAME = "Shadowfall"
SUBTITLE = "The Hero and the Seven Light Stones"
TAGLINE = "The Shadow King is stealing the light. Find the 7 Light Stones before it's gone!"
NAME_IDEAS = ("Shadowfall", "The Last Light", "Nightfall Rising")
CLASSIC_NAME = "Adventure World"

# ----- colours -----------------------------------------------------------------------------------
TEXT = (232, 230, 242)
DIM = (150, 146, 178)
GOLD = (255, 204, 92)               # titles, the NEXT card, the picked row's edge
EMBER = (255, 138, 72)              # warm light against the dark: the title glow
VIOLET = (150, 112, 230)            # the Shadow King's colour: page edges, the title's shadow

BOX_BG = (20, 18, 32)               # every box: dialogue, shop, quest log, pause, pages
ROW_LIGHT = (54, 42, 84)            # the picked row in a list
PANEL_BG = (14, 13, 22)             # the side panel
LOG_BG = (11, 10, 18)               # the message box under the map
CARD = (26, 24, 40)                 # the cards in the panel
CARD_EDGE = (56, 48, 86)
SLOT = (34, 30, 52)                 # a pack slot
DIVIDER = (44, 40, 66)
FRAME_BG = (52, 62, 92)             # behind a face in the dialogue box (dusky blue)
FRAME_EDGE = (10, 9, 16)
KEY_FILL = (44, 40, 68)             # a key cap, like [ENTER]
KEY_EDGE = (112, 102, 156)
BAR_BACK = (40, 36, 58)             # behind the health and XP bars
LIST_EDGE = (78, 72, 108)           # an unpicked row's edge (pause menu, save slots)

# Classic's colour -> this colour, for the few boxes game.py draws itself (game.py asks phase2.color)
COLORS = {"box": BOX_BG, "key": KEY_FILL, "key_edge": KEY_EDGE, "bar_back": BAR_BACK}

# ----- the dusk over the map ---------------------------------------------------------------------
DUSK = (26, 16, 64)
DUSK_ALPHA = 96                     # 0 = bright day, 255 = black. 96: dusky, every path still easy to see


def dusk_alpha(game):
    """How thick the dusk over the Phase 2 map is (0-255). One value for now; the world may darken later."""
    return DUSK_ALPHA


# ----- music: a darker map tune (game.py adds it to its TUNES) -------------------------------------
MAP_TUNE = "dusk"
TUNES = {
    # Phase 2's map: the home tune's bounce, but in A minor and a bit slower, with a low pulse under it.
    "dusk": {"tempo": 112, "voices": [
        ("triangle", 0.45, "A4 - C5 - E5 - D5 C5 | B4 - G4 - E4 - G4 B4 | C5 - E5 - D5 - C5 A4 | B4 - - - E4 - - - |"
                           "A4 - C5 - E5 - D5 C5 | B4 - G4 - E4 - A4 B4 | C5 - B4 A4 G#4 - A4 B4 | A4 - - - . . . . |"),
        ("sine", 0.6,      "A2 . E3 . A2 . E3 . | G2 . D3 . G2 . D3 . | F2 . C3 . F2 . C3 . | E2 . B2 . E2 . B2 . |"
                           "A2 . E3 . A2 . E3 . | G2 . D3 . G2 . D3 . | F2 . C3 . E2 . B2 . | A2 . E3 . A2 . . . |"),
        ("bell", 0.12,     ". . . . E6 . . . | . . . . D6 . . . | . . . . C6 . . . | . . . . B5 . . . |"
                           ". . . . E6 . . . | . . . . D6 . . . | . . . . E6 . . . | . . . . A5 . . . |")],
        "drums":           "k . h . s . h . | k . h . s . h . | k . h . s . h . | k . h . s . k . |" * 2},
}
