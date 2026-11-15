"""
The Craft menu (press C): UP and DOWN (or W and S, or the mouse) move the highlight,
and ENTER (or a click) crafts the highlighted row. The number keys don't do anything any more.

Also: the sword-forging game, crafting in a cave, and how much XP a level takes.
"""

import pygame

import game
import rules
from helpers import (click, frames, hold_keys, move_mouse, new_app, new_world, ok, press, steps, tiles,
                     walk_into_a_mine)

ROWS = game.App.CRAFTS          # the rows of the Craft menu, top to bottom


def picked(app):
    """The row that's highlighted."""
    return ROWS[app.craft_pick]


def highlight(app, kind):
    """Press DOWN until this row is highlighted."""
    for _ in range(len(ROWS)):
        if picked(app) == kind:
            break
        press(app, pygame.K_DOWN)
    ok(picked(app) == kind, "DOWN moves the highlight to %s" % kind)


def craft(app, kind):
    """Highlight this row, then press ENTER to craft it."""
    highlight(app, kind)
    press(app, pygame.K_RETURN, "\r")


def row_spot(app, kind):
    """The middle of a row of the menu, for the mouse."""
    return app.craft_rows[ROWS.index(kind)].center


def in_the_forest(wood=30):
    """A new game, standing in a forest a little way from home (with land below it), with some wood."""
    app = new_app(seed=5)
    world = app.game
    forest = next(spot for spot in tiles(world, "F")
                  if steps(spot, world.start) > 2 and (spot[0] + 1, spot[1]) in world.neighbors(spot))
    world.player.pos = forest
    app.player_px = list(game.tile_px(forest))
    world.player.wood = wood
    world.player.arrows = 0
    frames(app, 5)
    return app, forest


# A little empty cave, drawn right here, so it doesn't matter what the real caves look like
LITTLE_CAVE = ["############",
               "#..........#",
               "#..........#",
               "#..........#",
               "#..........#",
               "..S........#",
               "############"]


def in_a_little_cave(app):
    """Climb down a Mine into LITTLE_CAVE, and land on its floor."""
    world = app.game
    mine = tiles(world, "M")[0]
    world.cave_plan[mine] = "\n".join(LITTLE_CAVE)
    cave = walk_into_a_mine(app, mine)
    frames(app, 60)
    return cave


def forge_a_sword(app, key=pygame.K_SPACE, text=" "):
    """Play the forging game: 3 times, wait until the marker is in the green zone (not the gold), then strike."""
    for _ in range(3000):
        forge = app.forge
        if forge is None or app.state != "forge":
            break
        good = rules.strike_grade(forge.pos, forge.zone_x) == "good" and (
            forge.zone_x + 0.01 <= forge.pos <= forge.zone_x + forge.zone_w - 0.01)
        if forge.ready and good:
            press(app, key, text)
        else:
            frames(app)


def a_sure_strike(forge):
    """Line the marker up with the middle of the green zone (just off the gold), so the next strike is Good."""
    forge.pos = forge.zone_x + 0.02


# ===========================================================================
# Opening the menu and moving the highlight
# ===========================================================================

def test_c_opens_the_craft_menu():
    app, forest = in_the_forest()
    press(app, pygame.K_b, "b")
    ok(app.state == "play", "B doesn't open anything any more")
    press(app, pygame.K_c, "c")
    ok(app.state == "craft" and app.craft_pick == 0, "C opens the menu with the highlight on the top row (House)")
    ok(len(app.craft_rows) == len(ROWS), "the menu remembers where its %d rows are, for the mouse" % len(ROWS))


def test_the_arrow_keys_move_the_highlight_not_you():
    app, forest = in_the_forest()
    world, p = app.game, app.game.player
    press(app, pygame.K_c, "c")
    where, turn = p.pos, world.turn
    press(app, pygame.K_DOWN)
    ok(picked(app) == "boat", "DOWN moves the highlight to Boat")
    press(app, pygame.K_s, "s")
    press(app, pygame.K_DOWN)
    ok(picked(app) == "arrows", "S and DOWN move it on to Arrows")
    press(app, pygame.K_UP)
    press(app, pygame.K_w, "w")
    ok(picked(app) == "boat", "UP and W move it back up to Boat")
    press(app, pygame.K_UP)
    press(app, pygame.K_UP)
    ok(picked(app) == "pickaxe", "UP from the top wraps around to the bottom row (Pickaxe)")
    press(app, pygame.K_DOWN)
    ok(picked(app) == "house", "DOWN from the bottom wraps around to the top row (House)")
    for key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
        press(app, key)
    ok(p.pos == where and world.turn == turn and app.state == "craft",
       "on the map, none of the arrow keys walked you anywhere (no turns went by)")
    ok(p.wood == 30 and world.tile(forest) == "F", "moving the highlight doesn't craft anything")


def test_the_number_keys_dont_craft_any_more():
    app, forest = in_the_forest()
    p = app.game.player
    press(app, pygame.K_c, "c")
    for key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_KP4):
        press(app, key)
    ok(p.wood == 30 and p.arrows == 0 and app.state == "craft" and picked(app) == "house",
       "the number keys 1-6 don't craft (or move the highlight) any more")


def test_enter_crafts_the_highlighted_row():
    app, forest = in_the_forest()
    p = app.game.player
    where = p.pos
    press(app, pygame.K_c, "c")
    for _ in range(3):
        press(app, pygame.K_DOWN)
    press(app, pygame.K_RETURN, "\r")
    ok(p.arrows == rules.ARROWS_PER_BUNDLE and p.wood == 30 - rules.ARROW_COST and app.state == "craft",
       "ENTER on Arrows makes %d arrows, and the menu stays open" % rules.ARROWS_PER_BUNDLE)
    press(app, pygame.K_KP_ENTER, "\r")
    ok(p.arrows == 2 * rules.ARROWS_PER_BUNDLE, "the keypad ENTER works too")
    ok(p.pos == where, "crafting with ENTER didn't move you")


# ===========================================================================
# The mouse
# ===========================================================================

def test_the_mouse_highlights_rows_and_a_click_crafts():
    app, forest = in_the_forest()
    p = app.game.player
    p.pickaxe = None                    # so crafting one by mistake would show
    press(app, pygame.K_c, "c")
    wood = p.wood
    move_mouse(app, row_spot(app, "pickaxe"))
    ok(picked(app) == "pickaxe" and p.pickaxe is None and p.wood == wood,
       "moving the mouse over Pickaxe highlights it, without crafting")
    move_mouse(app, (app.craft_rows[0].x - 40, app.craft_rows[0].y))
    ok(picked(app) == "pickaxe", "moving the mouse off the rows leaves the highlight where it was")
    press(app, pygame.K_UP)
    ok(picked(app) == "sword", "after the mouse, UP still moves the highlight (to Sword)")
    had_bow = p.has_bow
    click(app, row_spot(app, "bow"))
    ok(not had_bow and p.has_bow and picked(app) == "bow" and p.wood == wood - rules.BOW_COST and app.state == "craft",
       "a click on Bow highlights it and crafts it right away")
    click(app, (app.craft_rows[-1].centerx, app.craft_rows[-1].bottom + 60))
    click(app, row_spot(app, "house"), button=3)
    ok(p.wood == wood - rules.BOW_COST and picked(app) == "bow" and app.game.tile(forest) == "F",
       "a click below the rows, or a right-click, doesn't craft anything")


def test_a_row_you_cant_craft_yet_says_why():
    app, forest = in_the_forest()
    world = app.game
    press(app, pygame.K_c, "c")
    world.player.pickaxe = rules.Tool("Pickaxe", rules.PICKAXE_DURABILITY)
    move_mouse(app, row_spot(app, "pickaxe"))
    problem = app.craft_problem("pickaxe")
    ok(problem and picked(app) == "pickaxe", "you can highlight Pickaxe even though you can't make it: %r" % problem)
    before = len(world.messages)
    press(app, pygame.K_RETURN, "\r")
    ok(len(world.messages) > before and world.messages[-1][0] == problem and app.state == "craft",
       "ENTER on it shows why not, and the menu stays open")


# ===========================================================================
# Crafting things in the forest, one after the other
# ===========================================================================

def test_crafting_in_the_forest():
    app, forest = in_the_forest(wood=12)
    world, p = app.game, app.game.player
    press(app, pygame.K_c, "c")
    craft(app, "arrows")
    craft(app, "arrows")
    ok(app.state == "craft" and p.arrows == 2 * rules.ARROWS_PER_BUNDLE and p.wood == 12 - 2 * rules.ARROW_COST,
       "make arrows twice in a row - the menu stays open (%d arrows)" % p.arrows)
    p.pickaxe = None
    craft(app, "pickaxe")
    ok(p.pickaxe and p.pickaxe.durability == rules.PICKAXE_DURABILITY and app.state == "craft",
       "Pickaxe + ENTER makes a pickaxe in the forest (free) - it lasts %d digs" % rules.PICKAXE_DURABILITY)
    turn = world.turn
    craft(app, "sword")
    ok(app.state == "forge", "Sword + ENTER starts the sword-forging game")
    press(app, pygame.K_RETURN, up=True)
    forge_a_sword(app)
    ok(app.state == "craft", "after the forge game you're back in the Craft menu")
    ok(len(p.swords) == 2 and all(sword.durability == rules.SWORD_DURABILITY for sword in p.swords),
       "a strike in the green zone forges a new sword - swords last %d hits" % rules.SWORD_DURABILITY)
    ok(world.turn == turn + 1, "on the world map, forging takes a turn")
    craft(app, "house")
    ok(world.tile(forest) == "H" and app.state == "craft", "House + ENTER builds a house, and the menu is still open")


def test_forging_only_works_in_a_forest_or_a_cave():
    world = new_world()
    world.player.pos = next(spot for spot in tiles(world, "M") if spot in world.mainland)
    ok("forest (or a cave)" in (world.forge_problem() or ""),
       "anywhere else on the map, it tells you where you can forge")


def test_holding_enter_down_doesnt_strike_the_metal():
    app, forest = in_the_forest()
    p = app.game.player
    p.swords = []
    press(app, pygame.K_c, "c")
    craft(app, "sword")
    ok(app.state == "forge" and app.forge.enter_held, "ENTER on Sword opens the forge game")
    press(app, pygame.K_RETURN, "\r")
    press(app, pygame.K_RETURN, "\r")      # key repeat: you're still holding it
    ok(app.state == "forge" and not app.forge.strikes, "holding ENTER down doesn't strike the metal by mistake")
    press(app, pygame.K_RETURN, up=True)
    ok(not app.forge.enter_held, "once you let go of ENTER ...")
    forge_a_sword(app, pygame.K_RETURN, "\r")
    ok(len(p.swords) == 1, "... a new ENTER press strikes it: you forged a sword")
    ok(app.state == "craft" and picked(app) == "sword", "back in the menu, still on Sword")


# ===========================================================================
# Closing the menu, and monsters
# ===========================================================================

def test_closing_the_craft_menu():
    app, forest = in_the_forest()
    p = app.game.player
    where = p.pos
    press(app, pygame.K_c, "c")
    press(app, pygame.K_DOWN)
    press(app, pygame.K_DOWN)
    press(app, pygame.K_ESCAPE)
    ok(app.state == "play" and app.running, "Esc closes the menu (and doesn't quit the game)")
    press(app, pygame.K_c, "c")
    ok(app.state == "craft" and app.craft_pick == 0, "opening it again starts back on the top row")
    press(app, pygame.K_c, "c")
    ok(app.state == "play", "C closes it too")
    press(app, pygame.K_DOWN)
    ok(p.pos != where, "with the menu closed, the arrow keys walk you again")


def test_a_monster_attack_closes_the_craft_menu():
    app = new_app(seed=5)
    world = app.game
    fields = tiles(world, "G")
    field = next(spot for spot in fields if (spot[0], spot[1] + 1) in fields)
    world.player.pos = field
    app.player_px = list(game.tile_px(field))
    world.player.wood = 12
    zombie = rules.Monster("Zombie", (field[0], field[1] + 1))
    zombie.move_chance = 1.0
    world.monsters = [zombie]
    press(app, pygame.K_c, "c")
    craft(app, "arrows")                   # on the map, crafting takes a turn: the zombie gets a move
    frames(app, 5)
    ok(app.state == "battle", "a monster attacks while you craft: the menu closes and the fight starts")


# ===========================================================================
# In a cave
# ===========================================================================

def test_crafting_in_a_cave():
    app = new_app(seed=5)
    world, p = app.game, app.game.player
    in_a_little_cave(app)
    p.wood, p.arrows, p.pickaxe = 5, 0, None
    turn = world.turn
    press(app, pygame.K_c, "c")
    ok(app.state == "craft" and app.craft_return == "cave", "C opens the Craft menu in a cave")
    craft(app, "arrows")
    craft(app, "pickaxe")
    ok(p.arrows == rules.ARROWS_PER_BUNDLE and p.pickaxe and p.wood == 5 - rules.ARROW_COST - rules.PICKAXE_CAVE_WOOD
       and world.turn == turn,
       "in a cave: arrows and a pickaxe (it costs %d wood down here), and no turns go by" % rules.PICKAXE_CAVE_WOOD)
    p.wood = rules.ARROW_COST - 1
    craft(app, "arrows")
    ok("You need %d wood" % rules.ARROW_COST in world.messages[-1][0] and p.arrows == rules.ARROWS_PER_BUNDLE,
       "with too little wood it tells you how much you need")
    craft(app, "house")
    ok("cave" in world.messages[-1][0] and app.state == "craft", "you can't build a house in a cave")
    press(app, pygame.K_ESCAPE)
    ok(app.state == "cave", "Esc goes back to the cave")


def test_the_craft_menu_keeps_you_still_in_a_cave(monkeypatch):
    held = hold_keys(monkeypatch)      # in a cave the game reads the keys you're HOLDING every frame
    app = new_app(seed=5)
    p = app.game.player
    cave = in_a_little_cave(app)
    ok(app.state == "cave" and cave.you.on_ground, "standing on the cave floor")
    p.wood, p.pickaxe = 6, None
    press(app, pygame.K_c, "c")
    held.update({pygame.K_UP, pygame.K_RIGHT})
    x, y = cave.you.x, cave.you.y
    for key in (pygame.K_DOWN, pygame.K_DOWN, pygame.K_DOWN, pygame.K_UP, pygame.K_w, pygame.K_s, pygame.K_s,
                pygame.K_DOWN, pygame.K_DOWN):
        press(app, key)
    frames(app, 30)
    ok((cave.you.x, cave.you.y) == (x, y), "UP and RIGHT held down in the menu: you didn't run, jump or climb")
    ok(picked(app) == "pickaxe", "and the highlight went down to Pickaxe")
    press(app, pygame.K_RETURN, "\r")
    ok(p.pickaxe and (cave.you.x, cave.you.y) == (x, y), "ENTER makes a pickaxe in the cave, and you still stand still")
    held.discard(pygame.K_RIGHT)       # still holding UP...
    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))
    ok(app.state == "cave", "Esc goes back to the cave")
    lowest = cave.you.y
    for _ in range(20):
        frames(app)
        lowest = min(lowest, cave.you.y)
    ok(lowest > y - 0.05, "the UP you held in the menu doesn't make you jump when it closes (top %.2f, floor %.2f)"
       % (lowest, y))
    held.clear()
    frames(app)
    held.add(pygame.K_UP)
    for _ in range(20):
        frames(app)
        lowest = min(lowest, cave.you.y)
    ok(lowest < y - 0.5, "let go and press UP again: now you jump (up to %.2f)" % lowest)


def test_forging_a_sword_in_a_cave(monkeypatch):
    held = hold_keys(monkeypatch)
    app = new_app(seed=5)
    world, p = app.game, app.game.player
    cave = in_a_little_cave(app)
    ok(app.state == "cave" and cave.you.on_ground, "standing in a cave")
    p.swords = [rules.Tool("Sword", 1)]
    turn = world.turn
    press(app, pygame.K_c, "c")
    craft(app, "sword")
    ok(app.state == "forge", "C, then Sword + ENTER, opens the forge right there in the cave")
    held.add(pygame.K_SPACE)           # you hold SPACE down for a moment as you strike
    for _ in range(rules.FORGE_STRIKES):
        frames(app, 50)
        a_sure_strike(app.forge)
        press(app, pygame.K_SPACE, " ")
    frames(app, 120)
    ok(len(p.swords) == 2 and p.swords[-1].durability == rules.SWORD_DURABILITY,
       "a good strike forges a new %d-hit sword" % rules.SWORD_DURABILITY)
    ok(app.state == "craft" and world.cave is not None and world.turn == turn,
       "and you're back in the Craft menu, in the cave (no world-map turn passes)")
    y = cave.you.y
    press(app, pygame.K_ESCAPE)
    lowest = y
    for _ in range(20):
        frames(app)
        lowest = min(lowest, cave.you.y)
    ok(app.state == "cave" and lowest > y - 0.05, "the SPACE you pressed for the forge doesn't make you jump")
    held.clear()
    cave.you.vy, cave.you.on_ground = -10, False
    ok("solid ground" in (world.forge_problem() or ""), "you can't forge in mid-air")
    cave.you.on_ground = True
    p.swords = [rules.Tool("Sword", 8)] * rules.MAX_SWORDS
    ok("carry" in (world.forge_problem() or ""), "you still can't carry more than %d swords" % rules.MAX_SWORDS)


# ===========================================================================
# Levels
# ===========================================================================

def test_each_level_needs_more_xp():
    world = new_world()
    world.gain_xp(rules.XP_PER_LEVEL - 1)
    ok(world.player.level == 1, "%d XP is not enough for level 2" % (rules.XP_PER_LEVEL - 1))
    world.gain_xp(1)
    ok(world.player.level == 2 and world.player.xp_needed == 2 * rules.XP_PER_LEVEL,
       "%d XP: level 2, and level 3 needs %d more" % (rules.XP_PER_LEVEL, 2 * rules.XP_PER_LEVEL))
