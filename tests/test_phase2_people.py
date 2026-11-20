"""
PEOPLE in Phase 2 (stage 2b): townsfolk on the map, talking with choices, the shop, the blacksmith,
the quest log on Q, the 2 sample quests, and saving all of it.
"""

import pygame

import rules
import sprites
from helpers import frames, ok, press
from phase2 import Phase2Game, dialogue, draw_people, people, quests, save, shop
from phase2_helpers import hold, own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)


def world(seed=1):
    game = Phase2Game("Hero", seed=seed)
    game.monsters = []
    return game


def stand_next_to(game, pid, way="right"):
    """Put the Hero on the square next to someone, so walking `way` bumps into them."""
    r, c = game.people[pid]
    dr, dc = rules.DIRECTIONS[way]
    game.player.pos = (r - dr, c - dc)
    game.player.facing = way


def read_all(talk):
    """Press ENTER until the talk shows its choices (or ends)."""
    for _ in range(30):
        if talk.done or talk.choices:
            return
        talk.press()


def choose(talk, words):
    read_all(talk)
    texts = [talk.fill(c["text"]) for c in talk.choices]
    hits = [i for i, text in enumerate(texts) if words in text]
    assert hits, "no choice with %r in %s" % (words, texts)
    talk.choose(hits[0])


def talk_to(game, pid, way="right"):
    stand_next_to(game, pid, way)
    game.do(way)
    ok(game.talk is not None and game.talk.person["id"] == pid, "walking into %s starts a talk" % pid)
    return game.talk


# ===========================================================================
# Who lives where
# ===========================================================================

def test_everyone_stands_on_open_ground_you_can_walk_to():
    game = world()
    reach = people.walk_reach(game, letters=rules.WALKABLE + "W=")      # (on foot, or with a boat)
    ok(8 <= len(people.people_here(game)) <= 12, "8 to 12 people at the start")
    home = [who for who, pos in people.people_here(game) if game.atlas.land_at(pos)[0] == "Home Meadow"]
    ok(len(home) >= 3, "at least 3 people in Home Meadow")
    for pid, pos in game.people.items():
        who = people.person(pid)
        ok(game.tile(pos) in rules.WALKABLE, "%s stands on a walkable square" % pid)
        ok(game.atlas.land_at(pos)[0] == people.wanted_spot(game, who)[1], "%s is in their own land" % pid)
        r, c = pos
        open_next = [s for s in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)) if s in reach]
        ok(open_next, "you can get to %s" % pid)
    blocked = set(game.people.values())
    everyone_out = people.walk_reach(game, blocked)
    ok(len(everyone_out) == len(people.walk_reach(game) - blocked), "nobody blocks the way anywhere")


def test_every_look_has_a_picture_and_there_are_6_kinds_at_least():
    looks = {who["look"] for who in people.all_people()}
    ok(looks <= set(sprites.PEOPLE_ART), "every look is in sprites.PEOPLE_ART")
    for need in ("farmer", "shopkeeper", "blacksmith", "guide", "wizard", "kid"):
        ok(need in sprites.PEOPLE_ART, "there's a %s" % need)


def test_every_dialogue_uses_known_conditions_effects_and_nodes():
    for who in people.all_people():
        nodes = who["talk"]
        ok("start" in nodes, "%s's talk has a start" % who["id"])
        for name, node in nodes.items():
            for variant in node if isinstance(node, list) else [node]:
                checks = list(variant.get("if", [])) + list(who.get("show_if", []))
                effects = list(variant.get("do", []))
                gos = [variant.get("next")]
                for choice in variant.get("choices", []):
                    checks += choice.get("if", [])
                    effects += choice.get("do", [])
                    gos.append(choice.get("go"))
                for c in checks:
                    ok(c.replace("not:", "").split(":")[0] in people.CONDITIONS, "%s: condition %s" % (who["id"], c))
                for e in effects:
                    ok(e.split(":")[0] in people.EFFECTS, "%s: effect %s" % (who["id"], e))
                    if e.split(":")[0].endswith("_quest"):
                        quests.get(e.split(":")[1])
                for go in gos:
                    ok(go is None or go in nodes, "%s: node %s goes to %s, which is there" % (who["id"], name, go))


def test_nobody_in_nightfall_hollow():
    game = world()
    game.world = 2
    ok(people.people_here(game) == [], "townsfolk stay on the home world")


# ===========================================================================
# Talking
# ===========================================================================

def test_walking_into_someone_talks_instead_of_moving_and_space_works_too():
    game = world()
    talk = talk_to(game, "guide_rosa")
    spot = game.player.pos
    ok(game.player.pos == spot and game.turn == 1, "you don't move, and no turn goes by")
    ok("Rosa" in talk.text and "Hero" in talk.text, "she says hello, with your name filled in")
    ok(talk.shown == "", "the words type out: nothing yet")
    talk.update(0.2)
    ok(0 < len(talk.shown) < len(talk.text), "a few letters later, some of it")
    talk.press()
    ok(talk.shown == talk.text, "ENTER shows the whole page at once")
    game.talk = None
    game.do("act")
    ok(game.talk and game.talk.person["id"] == "guide_rosa", "SPACE next to her talks too")
    ok("again" in game.talk.text, "the second time, she says hi again")


def test_choices_go_where_they_say():
    game = world()
    talk = talk_to(game, "guide_rosa")
    read_all(talk)
    ok(len(talk.choices) == 4, "Rosa has 4 choices")
    talk.move(1)
    ok(talk.choice == 1, "DOWN moves the highlight")
    talk.press()
    ok("Mine" in talk.text and "steps away" in talk.text, "'Where should I go?' points to the first Mine")
    read_all(talk)
    choose(talk, "Bye")
    ok(talk.done, "Bye ends the talk")


def test_the_dialogue_box_with_the_keys_and_the_mouse(monkeypatch):
    app = new_phase2_app()
    game = app.game
    game.monsters = []
    stand_next_to(game, "guide_rosa")
    frames(app, 5)
    hold(app, monkeypatch, pygame.K_RIGHT)          # walk into her
    frames(app, 2)
    ok(app.state == "people" and app.people_screen.kind == "talk", "the dialogue box opens")
    for _ in range(8):
        if game.talk.choices:
            break
        press(app, pygame.K_RETURN)
        frames(app, 60)
    ok(game.talk.choices, "her choices show")
    frames(app, 1)
    row, i = app.people_screen.rows[3]
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=row.center))
    frames(app, 2)
    ok(app.state == "play" and game.talk is None, "clicking 'Bye' closes it, back to the map")


# ===========================================================================
# The shop and the blacksmith
# ===========================================================================

def item(kind, sell=False):
    return next(i for i in (shop.sell_list() if sell else shop.buy_list()) if i["id"] == kind)


def test_buying_costs_gold_and_you_cant_overspend():
    game = world()
    game.gold = 25
    swords = len(game.player.swords)
    worked, _ = shop.buy(game, "mabel", item("sword"))
    ok(worked and game.gold == 5 and len(game.player.swords) == swords + 1, "a sword: 20 gold down, 1 sword up")
    ok(shop.stock_left(game, "mabel", item("sword")) == 2, "the shop has one fewer")
    worked, why = shop.buy(game, "mabel", item("sword"))
    ok(not worked and game.gold == 5 and "20 gold" in why, "5 gold isn't enough for another")
    food = game.player.food
    ok(shop.buy(game, "mabel", item("food"))[0] and game.player.food == food + 1 and game.gold == 1, "berries")
    game.gold = 100
    game.player.food = game.player.max_food
    ok(not shop.buy(game, "mabel", item("food"))[0] and game.gold == 100, "no buying food with a full pack")
    ok(shop.buy(game, "mabel", item("armor"))[0] and game.player.has_armor, "armor")
    game.shop_stock["mabel"]["bow"] = 0
    ok(shop.buy(game, "mabel", item("bow"))[1] == "Sold out!", "sold out")


def test_selling_wood_and_a_spare_sword():
    game = world()
    game.gold, game.player.wood = 0, 3
    ok(shop.sell(game, item("wood", True))[0] and game.gold == 1 and game.player.wood == 2, "sell a wood")
    ok(not shop.sell(game, item("sword", True))[0], "you can't sell your only sword")
    game.player.swords.append(rules.make_sword("cracked"))
    ok(shop.sell(game, item("sword", True))[0] and len(game.player.swords) == 1, "a spare sword sells")
    ok(game.player.swords[0].quality == "normal", "...the one with the fewest hits left")


def test_the_shop_screen_buys_with_enter():
    app = new_phase2_app()
    game = app.game
    game.monsters, game.gold = [], 50
    stand_next_to(game, "mabel")
    frames(app, 5)
    press(app, pygame.K_RIGHT)
    for _ in range(8):
        if game.talk and game.talk.choices:
            break
        press(app, pygame.K_RETURN)
        frames(app, 60)
    press(app, pygame.K_RETURN)                     # "Let me see your shop!"
    frames(app, 2)
    ok(app.state == "people" and app.people_screen.kind == "shop", "the shop opens")
    food = game.player.food
    press(app, pygame.K_RETURN)                     # Berries
    frames(app, 2)
    ok(game.gold == 46 and game.player.food == food + 1, "ENTER buys the highlighted thing")
    press(app, pygame.K_ESCAPE)
    frames(app, 2)
    ok(app.state == "play", "ESC leaves the shop")


def test_the_blacksmith_opens_the_forge_and_repairs_swords():
    app = new_phase2_app()
    game = app.game
    game.monsters = []
    stand_next_to(game, "bram")
    ok(game.here != "F" and game.forge_problem() is None, "next to Bram you can forge, out of the forest")
    talk = people.start_talk(game, people.person("bram"))
    sword = game.player.swords[0]
    sword.durability = 3
    game.gold = 20
    choose(talk, "Fix my sword")
    ok(sword.durability == sword.max_durability and game.gold == 20 - shop.repair_price(), "Bram fixes it for gold")
    read_all(talk)
    game.gold = 0
    sword.durability = 2
    choose(talk, "Fix my sword")
    ok(sword.durability == 2 and "costs" in talk.text, "no gold, no repair (he says why)")
    read_all(talk)
    choose(talk, "Forge")
    ok(talk.done and talk.then == ("forge", "bram"), "'Forge a sword' ends the talk...")
    frames(app, 2)
    ok(app.state == "forge" and app.forge is not None, "...and opens the classic forging game")


# ===========================================================================
# Quests
# ===========================================================================

def test_the_farmers_wood_quest_from_start_to_reward():
    game = world()
    talk = talk_to(game, "farmer_bo")
    choose(talk, "I'll do it")
    ok(quests.status(game, "farmer_wood") == "active", "the quest starts")
    game.talk = None
    game.player.wood = 4
    talk = talk_to(game, "farmer_bo")
    ok("4" in talk.text, "Bo says how much wood you have")
    game.talk, game.player.wood, gold, xp = None, 11, game.gold, game.player.xp
    talk = talk_to(game, "farmer_bo")
    choose(talk, "Here you go")
    ok(quests.status(game, "farmer_wood") == "done", "10 wood finishes it")
    ok(game.player.wood == 1 and game.gold == gold + 25 and game.player.xp > xp, "wood down, gold and XP up")


def test_the_lost_cat_quest_from_start_to_reward():
    game = world()
    ok(people.shown(game, people.person("whiskers")) and not people.shown(game, people.person("whiskers_home")),
       "Whiskers is in the woods, not at home")
    talk = talk_to(game, "pip")
    choose(talk, "Of course")
    ok(quests.step(game, "lost_cat") == 0, "Pip asks you to find her")
    game.talk = None
    talk = talk_to(game, "whiskers", "down")
    read_all(talk)
    ok(quests.step(game, "lost_cat") == 1, "finding Whiskers is the next step")
    ok(not people.shown(game, people.person("whiskers")) and people.shown(game, people.person("whiskers_home")),
       "she runs home")
    game.talk, gold, food = None, game.gold, game.player.food
    game.player.food = 0
    talk = talk_to(game, "pip")
    ok(quests.status(game, "lost_cat") == "done" and game.gold == gold + 15 and game.player.food == 1,
       "back at Pip's: done, with gold and a snack")


def test_quest_framework_steps_and_rewards():
    game = world()
    ok(not quests.advance(game, "lost_cat") and not quests.finish(game, "lost_cat"), "nothing before it starts")
    ok(quests.start(game, "lost_cat") and not quests.start(game, "lost_cat"), "it starts only once")
    ok(quests.step_text(game, "lost_cat").startswith("Find"), "the first step")
    quests.advance(game, "lost_cat")
    gold = game.gold
    quests.advance(game, "lost_cat")
    ok(quests.status(game, "lost_cat") == "done" and game.gold == gold + 15, "past the last step it's done")
    ok(quests.finished(game) == ["lost_cat"] and quests.active(game) == [], "it's in the finished list")


def test_the_quest_log_on_q():
    app = new_phase2_app()
    game = app.game
    quests.start(game, "farmer_wood")
    quests.start(game, "lost_cat")
    quests.finish(game, "lost_cat")
    doing, done = draw_people.quest_lines(game)
    ok(doing == [("Wood for the Winter", "Bring Farmer Bo 10 wood (chop trees with T)", "Farmer Bo")], "doing now")
    ok([d[0] for d in done] == ["Whiskers Is Lost"], "finished")
    frames(app, 5)
    press(app, pygame.K_q)
    frames(app, 2)
    ok(app.state == "people" and app.people_screen.kind == "quests", "Q opens the quest log")
    press(app, pygame.K_q)
    frames(app, 2)
    ok(app.state == "play", "Q closes it")


# ===========================================================================
# Saving, gold coins
# ===========================================================================

def test_quests_shop_and_who_you_talked_to_are_saved():
    game = world()
    game.gold = 33
    quests.start(game, "farmer_wood")
    shop.buy(game, "mabel", item("sword"))
    talk_to(game, "guide_rosa")
    ok(save.save_game(game), "it saves (even in the middle of a talk)")
    back = save.load_game()
    ok(back.gold == 13 and quests.status(back, "farmer_wood") == "active", "gold and quests come back")
    ok(back.shop_stock == {"mabel": {"sword": 2}}, "the shop's stock comes back")
    ok(back.people_talked == {"guide_rosa"} and back.talk is None, "who you talked to (not the talk itself)")
    ok(back.people == game.people, "everyone stands where they did")


def test_an_older_save_without_people_still_loads():
    game = world()
    data = save.game_to_data(game)
    fields = data["game"]["$dict"]
    data["game"]["$dict"] = [kv for kv in fields if kv[0] not in ("gold", "quest_state", "shop_stock",
                                                                 "people_talked", "people_flags")]
    back = save.data_to_game(data)
    ok(back.gold == shop.start_gold() and back.quest_state == {} and back.people, "filled in fresh")


def test_gold_coins_in_a_chest_are_gold():
    game = world()
    game.player.food = game.player.max_food
    gold = game.gold
    words = game.give_loot("food", 10)            # a full pack: gold coins instead
    ok(words == "+10 gold" and game.gold == gold + 10, "gold coins go in your pouch")


def test_dialogue_ends_when_nodes_run_out():
    who = {"name": "Test", "talk": {"start": {"say": ["One", "Two"], "next": "more"},
                                    "more": [{"if": ["no"], "say": ["hidden"]}, {"say": ["{x}!"]}]}}
    talk = dialogue.Conversation(who, lambda c: c != "no", lambda e, conv: None, {"x": "Three"})
    seen = []
    while not talk.done:
        seen.append(talk.text)
        talk.press()
        talk.press()
    ok(seen == ["One", "Two", "Three!"], "pages in order, the hidden one skipped, {words} filled in")


def test_people_on_open_ground_and_monsters_stay_off_them():
    """Everyone stands on walkable, reachable ground; stage 2c's monsters never start or step there."""
    from phase2 import monsters
    for seed in (1, 2, 3):
        game = Phase2Game("Hero", seed=seed)
        reach = people.walk_reach(game, letters=rules.WALKABLE + "W=")
        spots = set(game.people.values())
        for spot in spots:
            assert game.tile(spot) in rules.WALKABLE and spot in reach
            assert monsters.is_safe(game, spot)
        assert not any(tuple(m.pos) in spots for m in game.monsters)
        game.monsters = game.spawn_monsters({})
        assert not any(tuple(m.pos) in spots for m in game.monsters)
        for _ in range(30):
            monsters.pass_time(game, 0.5)
            assert not any(tuple(m.pos) in spots for m in game.monsters)
