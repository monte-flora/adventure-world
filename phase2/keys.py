"""
PHASE 2's KEYS: R is for fighting, everywhere.

- A fight on the map: R (or 1) attacks, X (or 2) runs away, E (or 3) eats.
- A cave, the castle, the Shadow King: R swings your sword (or Sunfang), and only that.
  G does what R did as well in Classic: dig (DOWN + G digs the floor), open chests, pull levers.
- F still shoots your bow, everywhere: it's the ranged attack, and R is the up-close one.

Classic keeps its keys (A attacks and R runs in a fight; R digs, opens and fights in a cave).
The words that name these keys (tips, the panel's key hints) are here too, so they say the same thing.
"""

import pygame

ATTACK_KEYS = (pygame.K_r,)
GRAB_KEYS = (pygame.K_g,)            # dig, open a chest, pull a lever

BATTLE_KEYS = {pygame.K_r: "attack", pygame.K_1: "attack",
               pygame.K_x: "run", pygame.K_2: "run",
               pygame.K_e: "eat", pygame.K_3: "eat",
               pygame.K_SPACE: "continue", pygame.K_RETURN: "continue"}
BATTLE_BUTTONS = [("attack", "R", "Attack"), ("run", "X", "Run away"), ("eat", "E", "Eat (%d)")]

# The tip bubbles (tutorial.TIPS) that name a different key in Phase 2
TIPS = {
    "monster": "A monster! Walk into it to start a fight. In a fight, press R to attack!",
    "diamond": "A diamond! Stand next to it and press G to dig it out.",
    "dig":     "Cracked rock! Stand next to it and press G to dig. DOWN and G digs the floor.",
    "chest":   "A treasure chest! Walk up to it and press G to open it.",
}
# ...and the cave's own first-time messages (caves.TIPS)
CAVE_TIPS = {
    "lever": "A lever! Press G next to it to pull it.",
}

# The panel's key hints in a cave, the castle and the throne room (game.py has Classic's)
CAVE_HINTS = [("Arrows", "run left and right"), ("SPACE", "jump (hold = higher)"),
              ("R", "fight", "G", "dig, open"), ("F", "shoot", "C", "craft"),
              ("Down + G", "dig the floor"), ("Up/Down", "climb ladders, walls"),
              (None, "Walk out on the left to leave")]
CASTLE_HINTS = CAVE_HINTS[:2] + [("R", "fight", "G", "chests, levers")] + CAVE_HINTS[3:-1] + [(None, "Find the key or the lever!")]
THRONE_HINTS = [("Arrows", "run", "SPACE", "jump"), ("R", "Sunfang", "F", "shoot"), (None, "Glowing sword? Get away!"),
                (None, "Jump over his fireballs!"), (None, "Hurt? Up the ladder to heal")]
HINTS = {"cave": CAVE_HINTS, "castle": CASTLE_HINTS, "throne": THRONE_HINTS}


def cave_controls(app, keys, controls):
    """In a cave: R (Classic's "use") becomes attack_pressed, and G grab_pressed. caves.Cave.update reads them."""
    controls["attack_pressed"] = controls.pop("use_pressed")
    grab = any(keys[k] for k in GRAB_KEYS)
    controls["grab_pressed"] = grab and not getattr(app, "grab_was_held", False)
    app.grab_was_held = grab
    return controls
