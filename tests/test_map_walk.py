"""
The Hero's walking pictures on the world map: he faces the way he goes, his picture
changes with every step he takes, and he stands still when he stops.
"""

import pygame

from helpers import frames, new_app, ok, press

KEYS = {"down": pygame.K_DOWN, "up": pygame.K_UP, "left": pygame.K_LEFT, "right": pygame.K_RIGHT}


def open_field(world):
    """A field with field two steps away in every direction, so the Hero can walk any way."""
    near = [(0, 0), (1, 0), (2, 0), (-1, 0), (-2, 0), (0, 1), (0, 2), (0, -1), (0, -2)]
    for r in range(2, world.rows - 2):
        for c in range(2, world.cols - 2):
            if all(world.map[r + dr][c + dc] == "G" for dr, dc in near):
                return (r, c)


def test_hero_walks_and_stands_on_the_map():
    app = new_app()
    app.game.player.pos = open_field(app.game)
    frames(app, 30)
    ok(app.map_pose() == 0, "he starts out standing")
    for way, back in (("down", "up"), ("up", "down"), ("left", "right"), ("right", "left")):
        poses = []
        for key in (way, back):
            press(app, KEYS[key])
            ok(app.map_facing == key, "he faces the way he walks (%s)" % key)
            poses.append(app.map_pose())
            frames(app, 4)
            ok(app.map_pose() == poses[-1], "he keeps the same walking picture during one step")
        ok(sorted(poses) == [1, 2], "his 2 walking pictures take turns, one every step (%s)" % poses)
        frames(app, 60)
        ok(app.map_pose() == 0, "he stands still when he stops")


def test_hero_has_pictures_for_every_way():
    app = new_app()
    for way in ("down", "up", "left", "right"):
        for armor in ("", " armor"):
            pictures = app.map_walk[way + armor]
            ok(len(pictures) == 3, "a standing picture and 2 walking pictures for %s%s" % (way, armor))
            ok(all(p.get_size() == (48, 48) for p in pictures), "they're all the same size")
