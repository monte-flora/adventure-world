"""
THE WORLD GROWS DARK (Phase 2): the Shadow King pulls the light out of the world, very slowly.

game.gloom says how much light he has taken: 0.0 (none: the dusk a new game starts with) to 1.0 (as dark
as it ever gets). It grows a tiny bit every second you play, and every Light Stone you find pushes it
back. theme.dusk_alpha turns it into how thick the dusk over the map and the little map is, and
theme.DUSK_DARKEST is the cap, so every path is always easy to see. Beat the Shadow King and the light
comes back for good.

It's a plain number on the game, so it saves by itself. This file knows nothing about graphics.
"""

FULL_MINUTES = 60           # with no Light Stones, the world is as dark as it gets after this many minutes of play
STONE_PUSH = 0.25           # each Light Stone pushes the dark back this much (1.0 is all the way)
NOTICE = 0.3                # this dark, the game says so (once)


def pass_time(game, seconds):
    """You played for this many seconds: the world gets a tiny bit darker (never darker than 1.0)."""
    if game.king_beaten or game.over:
        return
    game.gloom = min(1.0, game.gloom + seconds / (FULL_MINUTES * 60))
    on_the_map = game.world == 1 and not (game.cave or game.battle)
    if game.gloom >= NOTICE and not game.gloom_told and on_the_map:
        game.gloom_told = True
        game.log("It's getting darker... The Shadow King is pulling the light out of the world! "
                 "Every Light Stone you find pushes the dark back.", "bad")


def stone_found(game, relic):
    """A Light Stone pushes the dark back."""
    if game.gloom > 0:
        game.log("%s shines, and the dark pulls back a little." % (relic[0].upper() + relic[1:]), "good")
    game.gloom = max(0.0, game.gloom - STONE_PUSH)


def light_returns(game):
    """The Shadow King is beaten: all the light he took comes back (and pass_time stops)."""
    game.gloom = 0.0
