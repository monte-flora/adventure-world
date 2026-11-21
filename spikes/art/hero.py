"""The Hero, teen look: a hooded wanderer (deep-blue cloak, red scarf, lantern). Original art.

Top-down frame 16x24 (stands on one 16x16 tile, head overlaps the tile above).
Side-view frame 24x32 (2 tiles tall, the platformer caves).
Bodies are letter grids; legs are drawn per frame, so walk cycles stay cheap to make.
"""
import pygame

from sf_art import P, grid, outline

KEY = {"h": "water1", "H": "water2", "L": "water3", "s": "earth3", "S": "earth4", "e": "ink0",
       "r": "ember1", "R": "ember2", "g": "light0", "G": "light1", "m": "ink5", "M": "ink6",
       "b": "earth1", "B": "earth2"}

TD_DOWN = [
    "................",
    ".....hhhhhh.....",
    "....hHHHHHHh....",
    "...hHHLLLLHHh...",
    "...hHLLLLLLHh...",
    "...hHHHHHHHHh...",
    "...hHSSSSSSHh...",
    "...hSSeSSeSSh...",
    "...hSSSSSSSSh...",
    "....hsSSSSsh....",
    "...rRRRRRRRRr...",
    "..hrRRRRRRRRrh..",
    ".hHHrrrRRrrrHHh.",
    ".hLHHHHhhHHHHLh.",
    ".hLHHHHhhHHHHLh.",
    ".SHHHHHhhHHHHHS.",
    ".gHHHHHhhHHHHHM.",
    ".GhHHHHhhHHHHhm.",
    ".g.hhhhhhhhhh.m.",
]
TD_UP = TD_DOWN[:5] + [
    "...hHHLLLLHHh...",
    "...hHHHLLHHHh...",
    "...hHHHHHHHHh...",
    "....hhHHHHhh....",
    "...rRRRRRRRRr...",
    "..hrrRRRRRRrrh..",
    ".hHHHHrRRrHHHHh.",
    ".hLHHHHrRHHHHLh.",
    ".hLHHHHHrHHHHLh.",
    ".SHHHHHHHHHHHHS.",
    ".mHHHHHHHHHHHHg.",
    ".mhHHHHHHHHHHhG.",
    ".m.hhhhhhhhhh.g.",
]
TD_RIGHT = [
    "................",
    ".....hhhhh......",
    "....hHHHHHh.....",
    "...hHLLLHHHh....",
    "...hLLLHHHHHh...",
    "...hHHHHHHSSh...",
    "...hHHHHHSSSS...",
    "...hHHHHHSSeS...",
    "...hhHHHHSSSS...",
    "....hhhhhsSs....",
    "....rRRRRRRr....",
    "..RRrRRRRRrr....",
    ".RR.hHHHHHHh....",
    ".R..hLHHHHHh....",
    "....hLHHHHHh....",
    "....hLHHHSSh....",
    "....hHHHHMmmmm..",
    "...ghhHHHHHh....",
    "..gGghhhhhh.....",
]

SV_BODY = [
    "........................",
    ".........hhhhh..........",
    "........hHHHHHh.........",
    ".......hHLLLHHHh........",
    "......hHLLHHHHHHh.......",
    "......hHLHHHHHHHh.......",
    "......hHHHHHHSSSSh......",
    "......hHHHHHSSSSSS......",
    "......hHHHHHSSSeSS......",
    "......hhHHHHSSSSSS......",
    ".......hhHHHhSSSs.......",
    ".....RRrRRRRRRRRr.......",
    "...RRRrrRRRRRRRRRr......",
    "..RR..hhHHHHHHHHh.......",
    "......hLHHHHHHHHh.......",
    "......hLHHHHHHHHHh......",
    "......hLHHHHHSSHHh......",
    "......hLHHHHHSSHh.......",
    "......hHHHHHHHHHh.......",
    ".....ghHHHHHHHHHh.......",
    "....gGghHHHHHHHHHh......",
    "....gGg.hhHHHHHHhh......",
    ".....g...hhhhhhhh.......",
]


def _leg(s, hip_x, hip_y, foot_x, foot_y, back=False):
    dark, mid = (P["earth0"], P["earth1"]) if back else (P["earth1"], P["earth2"])
    pygame.draw.line(s, mid, (hip_x, hip_y), (foot_x, foot_y), 2)
    pygame.draw.line(s, dark, (hip_x + 1, hip_y), (foot_x + 1, foot_y), 1)
    pygame.draw.rect(s, dark, (foot_x - 1, foot_y, 4, 2))


def top_down(direction, frame):
    """direction: down, up, right, left. frame 0-3 (0/2 standing tall, 1/3 a step and 1 px bob)."""
    rows = {"down": TD_DOWN, "up": TD_UP, "right": TD_RIGHT, "left": TD_RIGHT}[direction]
    body = grid(rows, KEY)
    s = pygame.Surface((16, 24), pygame.SRCALPHA)
    bob = 1 if frame in (1, 3) else 0
    if direction in ("down", "up"):
        lift = {0: (0, 0), 1: (2, 0), 2: (0, 0), 3: (0, 2)}[frame]
        for x, up in ((4, lift[0]), (9, lift[1])):
            pygame.draw.rect(s, P["earth2"], (x, 19, 3, 3 - up))
            pygame.draw.rect(s, P["earth1"], (x, 21 - up, 3, 1))
    else:
        step = {0: (0, 0), 1: (-2, 2), 2: (0, 0), 3: (2, -2)}[frame]
        _leg(s, 6, 19, 6 + step[0], 20, back=True)
        _leg(s, 8, 19, 8 + step[1], 20)
    s.blit(body, (0, -bob))
    s = outline(s)
    return pygame.transform.flip(s, True, False) if direction == "left" else s


def side_view(pose, frame=0):
    """pose: idle (2), run (4), jump (1), attack (2). Faces right; flip for left."""
    s = pygame.Surface((24, 32), pygame.SRCALPHA)
    bob = 0
    if pose == "idle":
        bob = frame % 2
        _leg(s, 10, 23, 10, 28, back=True)
        _leg(s, 14, 23, 14, 28)
    elif pose == "run":
        feet = [(6, 16, 0, 0), (9, 13, 2, 0), (16, 7, 0, 0), (13, 10, 0, 2)][frame]
        bob = 1 if frame in (1, 3) else 0
        _leg(s, 10, 23, feet[0], 28 - feet[2], back=True)
        _leg(s, 13, 23, feet[1], 28 - feet[3])
    elif pose == "jump":
        _leg(s, 10, 23, 8, 26, back=True)
        _leg(s, 13, 23, 16, 25)
    elif pose == "attack":
        _leg(s, 10, 23, 7, 28, back=True)
        _leg(s, 14, 23, 17, 28)
    s.blit(grid(SV_BODY, KEY), (0, bob))
    if pose == "attack":                       # the swing: blade + a 2-colour arc, no blur
        if frame == 0:
            pygame.draw.line(s, P["ink6"], (15, 4), (12, 15), 2)
        else:
            pygame.draw.arc(s, P["ink7"], (5, 3, 17, 24), -1.3, 1.3, 2)
            pygame.draw.arc(s, P["water4"], (3, 1, 19, 28), -1.1, 1.1, 1)
            pygame.draw.line(s, P["ink6"], (15, 16), (22, 16), 2)
    return outline(s)


def top_down_sheet():
    sheet = pygame.Surface((16 * 4, 24 * 4), pygame.SRCALPHA)
    for row, d in enumerate(("down", "up", "right", "left")):
        for f in range(4):
            sheet.blit(top_down(d, f), (16 * f, 24 * row))
    return sheet


SIDE_FRAMES = [("idle", 0), ("idle", 1), ("run", 0), ("run", 1), ("run", 2), ("run", 3),
               ("jump", 0), ("attack", 0), ("attack", 1)]


def side_sheet():
    sheet = pygame.Surface((24 * len(SIDE_FRAMES), 32), pygame.SRCALPHA)
    for i, (pose, f) in enumerate(SIDE_FRAMES):
        sheet.blit(side_view(pose, f), (24 * i, 0))
    return sheet
