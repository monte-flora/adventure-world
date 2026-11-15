"""
PHASE 2'S SIDE PANEL AND MESSAGE BOX (phase2/hud.py decides what shows, phase2/draw_hud.py draws it).

The panel shows only what matters now: the things you have (nothing says "none"), a NEXT card from
the main quest with the 7 Light Stones, and the keys that do something where you stand. The newest
message glows for a few seconds, and big news pops up over the map as a toast. L opens the message
log, B the big map, H every key. Classic keeps its own panel.
"""

import pygame

import game
import phase2
import rules
from helpers import click, frames, move_mouse, new_app, ok, press, walk_into_a_mine
from phase2 import draw_hud, hud, main_quest, people, quests
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)

HINTS = {"tiles": game.TILE_HINTS, "cave": game.CAVE_HINTS, "castle": game.CASTLE_HINTS, "throne": game.THRONE_HINTS}


def new_world():
    world = phase2.new_game("Hero", seed=1)
    world.monsters = []
    world.story.clear()
    return world


def stand_next_to(world, pid):
    """Stand on an open square right next to this person, looking at them."""
    spot = world.people[pid]
    for way, (dr, dc) in rules.DIRECTIONS.items():
        here = (spot[0] - dr, spot[1] - dc)
        if world.in_bounds(here) and world.tile(here) in "GR" and people.person_at(world, here) is None:
            world.player.pos, world.player.facing = here, way
            return here
    raise AssertionError("no open square next to %s" % pid)


def ids(world):
    return [item["id"] for item in hud.pack(world)]


# ===========================================================================
# The pack: only what you have
# ===========================================================================

def test_a_new_pack_shows_only_the_three_things_you_have():
    world = new_world()
    ok(ids(world) == ["sword", "pickaxe", "food"], "a new hero has a sword, a pickaxe and 1 food: nothing else shows")
    food = hud.pack(world)[2]
    ok(food["count"] == "1" and food["icon"] == "apple", "the food shows how many you have")
    ok(not any("none" in (value or "").lower() for item in hud.pack(world) for value in (item["name"], item["count"])),
       "nothing in the pack says 'none'")


def test_things_show_up_when_you_get_them_and_go_when_they_run_out():
    world = new_world()
    p = world.player
    p.wood, p.has_bow, p.arrows, p.has_boat, p.diamonds, p.ring_hits = 4, True, 7, True, 2, 3
    p.armor = p.max_armor
    ok(ids(world) == ["sword", "pickaxe", "food", "wood", "bow", "boat", "armor", "diamonds", "ring"],
       "everything you have, in the same order every time")
    by_id = {item["id"]: item for item in hud.pack(world)}
    ok(by_id["wood"]["count"] == "4" and by_id["bow"]["count"] == "7" and by_id["diamonds"]["count"] == "2",
       "with how many of each")
    p.food = p.wood = p.diamonds = 0
    ok("food" not in ids(world) and "wood" not in ids(world) and "diamonds" not in ids(world),
       "when something runs out, it leaves the pack")
    p.arrows = 0
    bow = next(item for item in hud.pack(world) if item["id"] == "bow")
    ok(bow["tone"] == "bad" and bow["count"] == "0", "a bow with no arrows stays, in red")


def test_no_sword_is_shown_in_red_because_it_matters():
    world = new_world()
    world.player.swords = []
    sword = hud.pack(world)[0]
    ok(sword["id"] == "sword" and sword["tone"] == "bad" and sword["name"] == "No sword!",
       "no sword: the slot stays, red, and says so")
    world.player.swords = [rules.make_sword("great"), rules.make_sword()]
    sword = hud.pack(world)[0]
    ok(sword["name"] == "Great sword" and sword["tone"] == "gold" and sword["count"] == "x2"
       and sword["bar"] == (rules.GREAT_SWORD_DURABILITY, rules.GREAT_SWORD_DURABILITY),
       "a Great sword is gold, with a bar for its hits and x2 for a spare")
    world.player.swords[0].durability = rules.LOW_USES
    ok(hud.pack(world)[0]["tone"] == "bad", "a sword about to break turns red")


def test_every_item_and_power_has_words_for_the_mouse():
    world = new_world()
    p = world.player
    p.wood, p.has_bow, p.arrows, p.has_boat, p.diamonds, p.ring_hits, p.has_tower_key = 4, True, 7, True, 2, 3, True
    p.armor, p.lanterns, p.has_planks, p.has_hilt, p.sun_shards, p.light_shards = p.max_armor, 1, True, True, 2, 1
    p.powers = {"Stronger": 2, "Springy": 1, "Extra life": 1}
    for item in hud.pack(world):
        title, words = hud.tooltip(world, "item:" + item["id"])
        ok(title == item["name"] and len(words) > 10, "%s has a tooltip" % item["id"])
    ok([name for name, times, what in hud.powers(world)] == ["Stronger", "Springy"],
       "your powers show (extra lives are the hearts at the top)")
    ok(hud.tooltip(world, "power:Stronger")[0] == "Stronger x2", "a power's tooltip says how many times you picked it")
    for name in ("lives", "health", "xp", "goal", "stones", "map", "log"):
        ok(hud.tooltip(world, name), "%s has a tooltip" % name)
    ok(hud.tooltip(world, "nothing") is None, "nothing under the mouse: no tooltip")


# ===========================================================================
# The NEXT card
# ===========================================================================

def test_a_new_game_says_talk_to_rosa():
    world = new_world()
    goal = hud.next_goal(world)
    ok("Rosa" in goal["text"], "before the main quest starts, NEXT says to talk to Rosa")
    ok(goal["target"] == world.people["guide_rosa"], "and the pin is on Rosa")
    ok(hud.stones(world) == (0, 7), "0 of the 7 Light Stones")
    ok("Defeat 5 monsters" not in goal["text"], "not Classic's quest")


def test_next_follows_the_main_quest_in_few_words():
    world = new_world()
    quests.start(world, "main_home")
    goal = hud.next_goal(world)
    ok(goal["text"] == "Beat the cave under a Mine in Home Meadow", "the step, without what's in (brackets)")
    ok(goal["title"] == "Light Stone 1: The Dawn Stone", "with the chapter's name over it")
    ok(world.tile(goal["target"]) == "M" and world.land_name(goal["target"]) == "Home Meadow",
       "the pin is on a Mine in Home Meadow")
    ok(goal["way"] in hud.WAYS and goal["steps"] == rules.distance(goal["target"], world.player.pos)
       and "steps away" in goal["where"], "with an arrow and how many steps")
    quests.advance(world, "main_home")
    ok("Rosa" in hud.next_goal(world)["text"], "the next step: back to Rosa")


def test_next_counts_monsters_and_light_stones():
    world = new_world()
    quests.start(world, "main_home")
    while quests.status(world, "main_home") == "active":
        quests.advance(world, "main_home")
    ok(hud.stones(world) == (1, 7), "the Dawn Stone: 1 of 7")
    quests.advance(world, "main_woods")                 # talked to Elder Oona: now defeat 4 monsters
    goal = hud.next_goal(world)
    ok(goal["count"] == (0, 4) and "(" not in goal["text"], "a defeat step shows 0 of 4 as dots, not in the words")
    quests.count_up(world, "main_woods")
    ok(hud.next_goal(world)["count"] == (1, 4), "and counts up")


def test_next_when_you_are_right_there_has_no_arrow():
    world = new_world()
    stand_next_to(world, "guide_rosa")
    goal = hud.next_goal(world)
    ok(goal["way"] is None and goal["where"] == "right here!", "next to Rosa: 'right here!', and no arrow")


def test_next_counts_your_side_quests():
    world = new_world()
    ok(hud.next_goal(world)["more"] == 0, "no side quests yet")
    side = next(qid for qid, quest in quests.all_quests().items() if not quest.get("main"))
    quests.start(world, side)
    ok(hud.next_goal(world)["more"] == 1, "one side quest going: the card says so")


def test_next_after_the_last_chapter():
    world = new_world()
    for qid in main_quest.chapters():
        world.quest_state[qid] = {"status": "done", "step": 0}
    ok("You did it all" in hud.next_goal(world)["text"], "the main quest is done: the card says so")


def test_short_leaves_out_the_brackets():
    ok(hud.short("Cross the Icy River to Snowcap (fix the old bridge with 5 wood, or row) and talk to Hilda")
       == "Cross the Icy River to Snowcap and talk to Hilda", "what's in brackets is left out")
    ok(hud.short("Defeat 3 Skeletons in the Old Ruins (bring your bow!)") == "Defeat 3 Skeletons in the Old Ruins",
       "at the end too")


def test_the_arrow_points_the_right_way():
    here = (10, 10)
    ok(hud.way_to(here, (10, 30)) == "east" and hud.way_to(here, (10, 2)) == "west", "east and west")
    ok(hud.way_to(here, (2, 10)) == "north" and hud.way_to(here, (30, 10)) == "south", "north is up the map")
    ok(hud.way_to(here, (0, 20)) == "north-east" and hud.way_to(here, (20, 0)) == "south-west", "and the corners")


# ===========================================================================
# The "here" card: the keys that matter where you stand
# ===========================================================================

def test_at_home_the_only_key_is_space_to_rest():
    world = new_world()
    ok(hud.here(world, HINTS) == [("SPACE", "rest and heal", "plain")], "in your house: SPACE rests. That's all.")
    ok(hud.place(world) == "HOME MEADOW: HOUSE", "and it says where you are")


def test_next_to_someone_space_talks():
    world = new_world()
    stand_next_to(world, "guide_rosa")
    keys = hud.here(world, HINTS)
    ok(keys[0] == ("SPACE", "talk to Rosa", "hot"), "next to Rosa: SPACE talks to her, first and lit up")
    ok(sum(1 for key, words, tone in keys if key == "SPACE") == 1, "and SPACE is only there once")


def test_hurt_with_food_shows_eat():
    world = new_world()
    ok(not any(key == "E" for key, words, tone in hud.here(world, HINTS)), "at full health: no E")
    world.player.health = world.player.max_health // 2
    ok(("E", "eat (1 food)", "hot") in hud.here(world, HINTS), "hurt, with food: E eat, lit up")
    world.player.food = 0
    ok(not any(key == "E" for key, words, tone in hud.here(world, HINTS)), "hurt with no food: no E")


def test_never_more_than_four_lines_on_the_map():
    world = new_world()
    p = world.player
    forest = next((r, c) for r in range(world.rows) for c in range(world.cols) if world.map[r][c] == "F")
    p.pos, p.health, p.has_bow, p.arrows = forest, 1, True, 5
    world.monsters = [world.new_monster("Zombie")]
    world.monsters[0].pos = (forest[0], forest[1] + 2)
    keys = hud.here(world, HINTS)
    ok(len(keys) == hud.MAX_KEYS, "hurt, in a forest, with a bow and a monster near: still only %d lines" % hud.MAX_KEYS)
    ok(keys[0][0] == "E", "and the one that matters most is first")
    ok(any(key == "T" and "chop wood" in words for key, words, tone in keys), "T chops wood here")


def test_shoot_shows_only_with_a_monster_near():
    world = new_world()
    p = world.player
    p.has_bow, p.arrows = True, 5
    ok(not any(key == "F" for key, words, tone in hud.here(world, HINTS)), "no monster near: no F")
    world.monsters = [world.new_monster("Zombie")]
    world.monsters[0].pos = (p.pos[0], p.pos[1] + 3)
    ok(any(key == "F" for key, words, tone in hud.here(world, HINTS)), "a monster 3 squares away: F shoot")


def test_the_footer_has_help_and_pause():
    ok(hud.footer_keys() == [("H", "keys"), ("P", "pause")], "H for every key, P for the pause menu")
    everything = [key for heading, keys in hud.all_keys() for key, words in keys]
    for key in ("Arrows", "SPACE", "E", "T", "C", "F", "Z", "R", "Q", "B", "L", "H", "P", "M", "N"):
        ok(key in everything, "the H page lists %s" % key)


# ===========================================================================
# Messages: the newest glows, big news pops up
# ===========================================================================

def test_the_newest_message_glows_then_fades():
    feed = hud.Feed()
    messages = [("Hello!", "info")]
    ok(feed.take(messages) == [("Hello!", "info")] and feed.glow() == 1.0, "a new message glows")
    ok(feed.slide() == 0.0, "and starts to slide in")
    feed.update(hud.SLIDE_TIME)
    ok(feed.slide() == 1.0 and 0.9 < feed.glow() < 1.0, "it's in place after a moment, still glowing")
    feed.update(hud.FRESH_TIME)
    ok(feed.glow() == 0.0, "after %g seconds the glow is gone" % hud.FRESH_TIME)
    messages.append(("Ouch!", "bad"))
    ok(feed.take(messages) == [("Ouch!", "bad")] and feed.glow() == 1.0, "the next message glows again")
    ok(feed.take(messages) == [], "and is only new once")


def test_big_news_pops_up_and_little_news_does_not():
    ok(hud.is_toast("New quest: Light Stone 1: The Dawn Stone!", "quest"), "a quest pops up")
    ok(hud.is_toast("You put 12 gold coins in your pouch. You have 22 gold.", "loot"), "so does treasure")
    ok(not hud.is_toast("Chop, chop! You get 2 wood. This tree has 4 left.", "loot"), "chopping wood doesn't")
    ok(not hud.is_toast("+5 XP", "loot"), "nor a few XP")
    ok(not hud.is_toast("You walk into a wall.", "info") and not hud.is_toast("Ouch!", "bad"), "nor plain news")


def test_a_toast_stays_a_few_seconds():
    feed = hud.Feed()
    feed.take([("New quest: Wood for the Winter!", "quest")])
    ok([text for text, kind, solid in feed.showing()] == ["New quest: Wood for the Winter!"], "the toast shows")
    feed.update(1.0)
    ok(feed.showing()[0][2] == 1.0, "solid while it stays")
    feed.update(hud.TOAST_TIME - 1.0 - hud.TOAST_FADE / 2)
    ok(0 < feed.showing()[0][2] < 1, "it fades at the end")
    feed.update(hud.TOAST_FADE)
    ok(feed.showing() == [], "and is gone after %g seconds" % hud.TOAST_TIME)


def test_the_clock_stops_while_you_are_not_playing():
    feed = hud.Feed()
    feed.take([("New quest: Wood for the Winter!", "quest")])
    feed.update(60.0, live=False)
    ok(len(feed.showing()) == 1 and feed.glow() == 1.0, "under a story card or a menu nothing gets older")


def test_new_news_is_never_late():
    feed = hud.Feed()
    messages = [("Quest one!", "quest"), ("Quest two!", "quest")]
    feed.take(messages)
    feed.update(0.5)
    messages += [("Quest three!", "quest")]
    feed.take(messages)
    ok(len(feed.showing()) == hud.TOASTS_AT_ONCE, "only %d toasts at once" % hud.TOASTS_AT_ONCE)
    feed.update(hud.TOAST_FADE + 0.01)
    ok([text for text, kind, solid in feed.showing()] == ["Quest two!", "Quest three!"],
       "the oldest hurries off to make room")


def test_a_new_game_starts_the_feed_again():
    feed = hud.Feed()
    feed.take([("One", "quest"), ("Two", "quest")])
    ok(feed.take([("A new game", "quest")]) == [("A new game", "quest")], "a new list of messages starts fresh")
    ok([text for text, kind, solid in feed.showing()] == ["A new game"], "with only its own toasts")


def test_every_message_gets_a_picture():
    ok(hud.icon_for("You put 12 gold coins in your pouch.", "loot") == "coin", "gold: a coin")
    ok(hud.icon_for("You got the Dawn Stone! (1 of 7 Light Stones)", "quest") == "stone", "a Light Stone: a gem")
    ok(hud.icon_for("You open the treasure chest!", "loot") == "chest", "a chest")
    ok(hud.icon_for("New quest: A Letter for Finn!", "quest") == "star", "a quest: a star")
    ok(hud.icon_for("Ouch! The Zombie hits you.", "bad") == "bang", "bad news: a red !")
    ok(hud.icon_for("You eat some berries.", "good") == "heart" and hud.icon_for("Sound off.", "info") == "talk",
       "good news: a heart; plain words: a speech bubble")


def test_the_log_keeps_the_last_messages():
    messages = [("Message %d" % i, "info") for i in range(200)]
    lines = hud.log_lines(messages)
    ok(len(lines) == hud.LOG_LINES and lines[-1][0] == "Message 199", "the newest %d, oldest first" % hud.LOG_LINES)


# ===========================================================================
# In the game (drawn into an invisible window)
# ===========================================================================

def test_the_welcome_is_about_the_light_stones():
    app = new_phase2_app()
    words = " ".join(text for text, kind in app.game.messages)
    ok("7 Light Stones" in words and "Rosa" in words, "Phase 2 welcomes you with its own goal")
    ok("Defeat 5 monsters" not in words and "mine 3 diamonds" not in words, "not Classic's")
    lines = phase2.help_lines(app.game, [("GOAL", 1), ("Defeat 5 monsters and mine 3 diamonds.", 2), ("Then...", 2), ("", 2)])
    ok("7 Light Stones" in lines[1][0] and len(lines) == 4, "and the How to Play page says the same")
    classic = rules.Game("Hero", seed=1)
    ok("Defeat 5 monsters" in classic.messages[0][0], "Classic's welcome is as it was")
    ok(phase2.help_lines(classic, lines) is lines, "and so is its How to Play page")


def test_the_panel_draws_and_the_tips_can_find_their_spots():
    app = new_phase2_app()
    frames(app, 10)
    ok({"lives", "here", "food"} <= set(app.panel_spots), "the tip bubbles can still point at the food, lives and place")
    ok("wood" not in app.panel_spots and "item:wood" not in app.hud.spots, "no wood yet: no wood slot")
    app.game.player.wood = 3
    frames(app, 2)
    ok("wood" in app.panel_spots, "with wood, there is one")
    panel = pygame.Rect(game.VIEW_W, 0, game.PANEL_W, game.HEIGHT)
    ok(all(panel.contains(spot) for name, spot in app.hud.spots.items() if name not in ("log", "map")),
       "everything on the panel is inside the panel")
    bottom = pygame.Rect(0, game.VIEW_H, game.VIEW_W, game.LOG_H)
    ok(bottom.contains(app.hud.spots["log"]) and bottom.contains(app.hud.spots["map"]),
       "the message box and the little map are inside the bottom strip")


def test_a_full_pack_still_fits():
    app = new_phase2_app()
    p = app.game.player
    p.wood, p.has_bow, p.arrows, p.has_boat, p.diamonds, p.ring_hits, p.has_tower_key = 12, True, 20, True, 9, 5, True
    p.armor, p.lanterns, p.has_planks, p.has_hilt, p.sun_shards, p.light_shards = p.max_armor, 3, True, True, 2, 4
    p.powers = {name: 1 for name in rules.POWERS}
    p.health = 3
    quests.start(app.game, "main_home")
    frames(app, 5)
    panel = pygame.Rect(game.VIEW_W, 0, game.PANEL_W, game.HEIGHT)
    ok(all(panel.contains(spot) for name, spot in app.hud.spots.items() if name not in ("log", "map")),
       "with everything in the pack, it all stays on the panel")
    slots = [spot for name, spot in app.hud.spots.items() if name.startswith("item:")]
    ok(len(slots) == len(hud.pack(app.game)) and all(a.collidelist(slots[i + 1:]) < 0 for i, a in enumerate(slots)),
       "every item has its own slot")
    ok(app.panel_spots["here"].top >= max(slot.bottom for slot in slots), "and the keys card is under the pack")


def test_l_opens_the_message_log():
    app = new_phase2_app()
    frames(app, 5)
    press(app, pygame.K_l)
    ok(app.state == "people" and app.hud.screen == "log", "L opens the message log (the game waits under it)")
    turn = app.game.turn
    press(app, pygame.K_RIGHT)
    ok(app.game.turn == turn and app.hud.screen == "log", "the arrow keys don't walk while it's open")
    press(app, pygame.K_UP)
    frames(app, 3)
    press(app, pygame.K_l)
    ok(app.state == "play" and app.hud.screen is None, "L again closes it")
    press(app, pygame.K_RIGHT)
    ok(app.game.turn == turn + 1, "and you can walk again")


def test_b_opens_the_big_map_and_h_every_key():
    app = new_phase2_app()
    frames(app, 5)
    press(app, pygame.K_b)
    ok(app.hud.screen == "map" and app.state == "people", "B opens the big map")
    frames(app, 3)
    press(app, pygame.K_ESCAPE)
    ok(app.state == "play" and not phase2.paused(app), "ESC closes it (and doesn't pause)")
    press(app, pygame.K_h)
    ok(app.hud.screen == "keys", "H opens the page of every key")
    frames(app, 3)
    press(app, pygame.K_RETURN)
    ok(app.state == "help", "ENTER there goes on to the big How to Play page")
    press(app, pygame.K_SPACE)
    ok(app.state == "play", "and any key comes back to the game")


def test_in_a_cave_the_log_works_and_the_game_waits():
    app = new_phase2_app()
    walk_into_a_mine(app)
    ok(app.state == "cave", "in a cave")
    frames(app, 30)
    ok(hud.next_goal(app.game)["text"] == "Find the EXIT door", "NEXT says to find the EXIT door")
    ok(len(hud.here(app.game, HINTS)) == len(game.CAVE_HINTS), "and the keys card has every cave move")
    press(app, pygame.K_b)
    ok(app.state == "cave", "B does nothing down here (there's no map)")
    press(app, pygame.K_l)
    you = (app.game.cave.you.x, app.game.cave.you.y)
    frames(app, 30)
    ok(app.state == "people" and (app.game.cave.you.x, app.game.cave.you.y) == you, "L: the log, and the cave waits")
    press(app, pygame.K_ESCAPE)
    ok(app.state == "cave", "ESC goes back to the cave")


def test_p_still_pauses():
    app = new_phase2_app()
    frames(app, 5)
    press(app, pygame.K_p)
    ok(phase2.paused(app), "P opens the pause menu, as before")
    press(app, pygame.K_p)
    ok(not phase2.paused(app) and app.state == "play", "and closes it")
    press(app, pygame.K_l)
    press(app, pygame.K_p)
    ok(phase2.paused(app), "P pauses with the message log open too")
    press(app, pygame.K_p)
    ok(app.hud.screen == "log", "and the log is still there after")


def test_the_mouse_shows_a_tooltip_and_clicks_open_pages():
    app = new_phase2_app()
    frames(app, 5)
    move_mouse(app, app.hud.spots["item:food"].center)
    ok(draw_hud.spot_at(app, app.hud.mouse) == "item:food", "the mouse is over the food")
    frames(app, 2)
    click(app, app.hud.spots["goal"].center)
    ok(app.state == "people" and app.people_screen.kind == "quests", "a click on the NEXT card opens the quest log")
    press(app, pygame.K_q)
    click(app, app.hud.spots["map"].center)
    ok(app.hud.screen == "map", "a click on the little map opens the big one")
    click(app, (20, 20))
    ok(app.state == "play", "and a click closes it")
    click(app, app.hud.spots["log"].center)
    ok(app.hud.screen == "log", "a click on the message box opens the log")
    press(app, pygame.K_ESCAPE)
    click(app, app.hud.spots["item:food"].center)
    ok(app.hud.pinned == "item:food", "a click on a pack item keeps its tooltip up (for touch screens)")
    frames(app, 2)
    press(app, pygame.K_RIGHT)
    ok(app.hud.pinned is None, "until you do something else")


def test_news_from_a_talk_pops_up_when_the_talk_is_over():
    app = new_phase2_app()
    frames(app, 5)
    app.hud.feed.toasts.clear()
    press(app, pygame.K_q)                              # a Phase 2 page is open: you're not playing
    app.game.log("New quest: Wood for the Winter!", "quest")
    frames(app, 30)
    ok(app.hud.feed.showing() == [], "while a page is open, the toast waits")
    press(app, pygame.K_q)
    frames(app, 2)
    ok([text for text, kind, solid in app.hud.feed.showing()] == ["New quest: Wood for the Winter!"],
       "back on the map, it pops up")
    frames(app, int(hud.TOAST_TIME * 60) + 5)
    ok(app.hud.feed.showing() == [], "and goes away by itself")


def test_a_level_up_card_is_its_own_news():
    app = new_phase2_app()
    frames(app, 5)
    app.hud.feed.toasts.clear()
    app.game.gain_xp(app.game.player.xp_needed)
    frames(app, 5)
    ok(app.state == "levelup", "the LEVEL UP! card is up")
    frames(app, 40)
    ok(draw_hud.slide_in(app) == 1.0, "and the message box under it shows its words (nothing is half slid in)")
    press(app, pygame.K_1)
    frames(app, 2)
    ok(app.state == "play" and not any("LEVEL UP" in text for text, kind, solid in app.hud.feed.showing()),
       "after you pick a power, no late LEVEL UP toast")


def test_classic_keeps_its_own_panel():
    app = new_app()
    frames(app, 10)
    ok(not phase2.draw_panel(app) and not phase2.draw_log(app), "Classic draws its own panel and message log")
    ok("hud" not in app.__dict__, "and never makes a Phase 2 HUD")
    ok({"food", "wood", "bow", "here", "lives"} <= set(app.panel_spots), "its panel rows are where they were")
    press(app, pygame.K_h)
    ok(app.state == "help", "H is the classic How to Play page")
    press(app, pygame.K_SPACE)
    press(app, pygame.K_l)
    press(app, pygame.K_b)
    ok(app.state == "play", "and L and B do nothing")
