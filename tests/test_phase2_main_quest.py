"""
THE MAIN QUEST of Phase 2 (stage 3a): Rosa starts it, one Light Stone in every land (in the order the
gates and the monsters' levels go), the Portal opens with all 7, then Nightfall Hollow, the castle, the
Shadow King, and a short ending that takes you home to keep playing. All of it saves.
"""

import types

import pygame

import game as classic_game
import rules
import story
from helpers import frames, ok, press
from phase2 import Phase2Game, draw_people, main_quest, monsters, people, quests, save
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)

ORDER = ["main_home", "main_woods", "main_lake", "main_ruins", "main_frost", "main_desert", "main_swamp", "main_portal"]
LANDS = ["Home Meadow", "Whispering Woods", "The Great Lake", "Old Ruins", "Frost Peaks", "Sunscorch Desert",
         "Murk Swamp"]


def world(seed=1):
    game = Phase2Game("Hero", seed=seed)
    game.monsters = []
    game.story.clear()
    return game


def talk_through(game, pid):
    """Walk into someone and press ENTER until the talk ends (picking the first choice, if there are any)."""
    r, c = game.people[pid]
    for way, (dr, dc) in rules.DIRECTIONS.items():
        game.player.pos, game.player.facing = (r - dr, c - dc), way
        if people.bump(game, way):
            break
    talk = game.talk
    ok(talk is not None and talk.person["id"] == pid, "you talk to %s" % pid)
    for _ in range(40):
        if talk.done:
            break
        if talk.choices:
            talk.choose(0)
        else:
            talk.press()
    game.talk = None


def mine_in(game, land):
    return min(m for m in game.cave_plan if game.land_name(m) == land)


def do_goal(game, goal):
    """Make a step's goal happen, the way it happens in the game."""
    name, *args = goal.split(":")
    if name == "cave":
        mine = mine_in(game, args[0])
        game.player.pos = mine
        game.cave = types.SimpleNamespace(is_castle=False, result="exit", mine_pos=mine)
        game.leave_cave()
    elif name == "defeat":
        kind = "Spider" if args[1] == "any" else args[1]
        for _ in range(int(args[2])):
            m = monsters.make_monster(kind, game.start, land=args[0])
            game.monsters.append(m)
            game.monster_gone(m, True)
    elif name == "lookout":
        game.player.pos = min(s for s in game.atlas.lookouts if game.land_name(s) == args[0])
        game.climb_lookout()
    elif name == "level":
        while game.player.level < int(args[0]):
            game.gain_xp(game.player.xp_needed - game.player.xp)
    else:
        raise AssertionError("no test for goal %s" % goal)


def play_chapter(game, qid):
    """Do every step of a chapter: its goals, and talking to its people. Returns True if it's done."""
    if quests.status(game, qid) == "new" and qid == "main_home":
        talk_through(game, "guide_rosa")
    ok(quests.status(game, qid) == "active", "%s has started" % qid)
    for _ in range(len(quests.get(qid)["steps"])):
        if quests.status(game, qid) != "active":
            break
        n = quests.step(game, qid)
        one = quests.get(qid)["steps"][n]
        if one.get("goal"):
            do_goal(game, one["goal"])
        else:
            talk_through(game, one["to"].split(":")[1])
        ok(quests.status(game, qid) == "done" or quests.step(game, qid) > n, "%s step %d gets done" % (qid, n + 1))
    return quests.status(game, qid) == "done"


def all_relics(game):
    for qid in ORDER[:-1]:
        ok(play_chapter(game, qid), "%s is done" % qid)
    game.level_ups = []
    game.story.clear()


# ===========================================================================
# What it is
# ===========================================================================

def test_the_chapters_come_one_land_at_a_time():
    ok(main_quest.chapters() == ORDER, "7 Light Stones then the Portal, in order")
    ok(main_quest.relics_needed() == 7, "7 Light Stones")
    game = world()
    for qid, land in zip(ORDER, LANDS):
        quest = quests.get(qid)
        ok(quest["main"] and quest.get("relic"), "%s gives a Light Stone" % qid)
        giver = quest["giver"]
        ok(game.atlas.land_at(game.people[giver])[0] == land, "%s's Light Stone comes from %s" % (qid, land))
    ok(quests.all_quests()["farmer_wood"] and "main_home" in quests.all_quests(), "side quests and main quest together")


def test_the_order_matches_the_gates_and_the_monsters():
    game = world()
    gate_level = max(level for _, level in game.atlas.gates.values())
    desert = quests.get("main_desert")["steps"][0]
    ok(desert["goal"] == "level:%d" % gate_level, "the desert chapter waits for the Desert Gate's level")
    strongest = []
    for land in LANDS:
        mix = monsters.land_mix(land)
        strongest.append(max(monsters.LEVELS.get(kind, 2) for kind in mix))
    ok(strongest == sorted(strongest), "every land's monsters are as strong or stronger than the last: %s" % strongest)
    for qid in ORDER:
        for one in quests.get(qid)["steps"]:
            for land in LANDS:
                if one.get("goal", "").count(":") and land in one["goal"]:
                    ok(land in LANDS[:ORDER.index(qid) + 1], "%s only sends you to lands you've reached" % qid)


def test_a_new_game_tells_the_phase_2_story_and_rosa_starts_it():
    game = Phase2Game("Hero", seed=1)
    titles = [card[0] for card in game.story]
    ok("The seven Light Stones" in titles and "Sunfang" not in titles, "Phase 2's own opening cards")
    ok(all("Hero" in card[1] or "{name}" not in card[1] for card in game.story), "with your name filled in")
    ok(quests.active(game) == [], "no quests until you talk to someone")
    ok(draw_people.quest_mark(game, people.person("guide_rosa")) == "!", "a ! over Rosa")
    ok(draw_people.quest_mark(game, people.person("finn")) is None, "but not over Finn yet")
    game.monsters = []
    talk_through(game, "guide_rosa")
    ok(quests.status(game, "main_home") == "active", "Rosa starts chapter 1")
    ok("Mine" in quests.step_text(game, "main_home") and "steps away" in quests.step_text(game, "main_home"),
       "the quest log says which way to the Mine")
    ok(main_quest.relic_chapters()[0] == "main_home" and not main_quest.relics(game), "no Light Stones yet")
    ok(not people.shown(game, people.person("elder_oona")), "Elder Oona isn't there until Rosa sends you")


# ===========================================================================
# Every chapter: start -> finish -> reward
# ===========================================================================

def test_every_light_stone_can_be_won_and_gives_its_reward():
    game = world()
    for i, qid in enumerate(ORDER[:-1]):
        gold, food = game.gold, game.player.food
        xp_before = game.player.level * 1000 + game.player.xp
        ok(play_chapter(game, qid), "%s: done" % qid)
        reward = quests.get(qid)["reward"]
        ok(game.gold >= gold + reward["gold"], "%s: gold for it" % qid)
        ok(game.player.level * 1000 + game.player.xp > xp_before, "%s: XP for it" % qid)
        ok(len(main_quest.relics(game)) == i + 1, "%s: %d Light Stones" % (qid, i + 1))
        ok(any(card[0].startswith(quests.get(qid)["relic"][4:].title()[:3]) or "!" in card[0] for card in game.story),
           "%s: a story card" % qid)
        nxt = quests.get(qid)["next"]
        ok(quests.status(game, nxt) == "active", "%s: the next chapter starts" % qid)
        game.story.clear()
    ok([q for q in game.quests if q.description == main_quest.RELIC_QUEST][0].completed, "the panel says 7/7")


def test_steps_wait_for_the_right_land_and_kind():
    game = world()
    talk_through(game, "guide_rosa")
    do_goal(game, "cave:Whispering Woods")
    ok(quests.step(game, "main_home") == 0, "a cave in another land doesn't count")
    do_goal(game, "cave:Home Meadow")
    ok(quests.step(game, "main_home") == 1, "a Home Meadow cave does")
    game.quest_state["main_ruins"] = {"status": "active", "step": 1}
    do_goal(game, "defeat:Old Ruins:Zombie:2")
    ok(quests.step(game, "main_ruins") == 1, "Zombies aren't Skeletons")
    do_goal(game, "defeat:Old Ruins:Skeleton:2")
    ok(quests.step(game, "main_ruins") == 1 and "(2/3)" in quests.step_text(game, "main_ruins"), "2 of 3, it says")
    do_goal(game, "defeat:Old Ruins:Skeleton:1")
    ok(quests.step(game, "main_ruins") == 2, "the 3rd Skeleton does it")


def test_the_desert_step_is_done_at_once_if_you_are_strong_enough():
    game = world()
    do_goal(game, "level:4")
    quests.start(game, "main_desert")
    ok(quests.step(game, "main_desert") == 1, "already level 3: straight on to Juno")


def test_rosa_and_the_quest_log_say_where_to_go_next():
    game = world()
    for qid in ORDER[:2]:
        play_chapter(game, qid)
    text = main_quest.next_step(game)
    ok("Lakeside" in text and "steps away" in text, "Rosa's 'where next' points to Finn: %s" % text)
    ok(draw_people.quest_mark(game, people.person("finn")) == "!", "and there's a ! over Finn")
    doing, _ = draw_people.quest_lines(game)
    ok(doing[0][0].startswith("Light Stone 3"), "the main quest is first in the quest log")


# ===========================================================================
# The Portal, Nightfall Hollow, the Shadow King and the end
# ===========================================================================

def test_the_portal_stays_shut_without_all_7_light_stones():
    game = world()
    for quest in game.quests:
        quest.progress = quest.goal_count            # (Classic's quests don't open this Portal)
    for qid in ORDER[:6]:
        play_chapter(game, qid)
    ok(not game.portal_open, "6 Light Stones: still shut")
    game.player.pos = game.portal
    game.check_portal()
    ok(game.world == 1 and "7 Light Stones" in game.messages[-1][0], "it says what it needs")
    play_chapter(game, "main_swamp")
    ok(game.portal_open, "7 Light Stones: open")
    game.check_portal()
    ok(game.world == 2, "and through you go, to Nightfall Hollow")
    ok(quests.step(game, "main_portal") == 1, "the quest log says: find the castle")


def test_beating_the_shadow_king_ends_the_story_and_takes_you_home():
    game = world()
    all_relics(game)
    home_map = [row[:] for row in game.map]
    game.player.pos = game.portal
    game.check_portal()
    game.open_castle()
    ok(quests.step(game, "main_portal") == 2, "into the castle: now beat the Shadow King")
    game.cave = None
    game.king_quest = rules.Quest("Defeat the Shadow King", 1)
    game.story.clear()
    game.beat_the_king()
    titles = [card[0] for card in game.story]
    ok("The Shadow King falls" in titles and "The adventure goes on" in titles, "the ending cards")
    ok(not game.won and not game.over, "not over: you keep playing")
    ok(game.world == 1 and game.map == home_map and game.player.pos == game.start, "back home, the way you left it")
    ok(quests.status(game, "main_portal") == "done" and game.king_beaten, "the main quest is done")
    back = save.load_game()
    ok(back is not None and back.world == 1 and back.king_beaten, "and it's saved")
    back.player.pos = back.portal
    back.check_portal()
    ok(back.world == 1, "the Portal stays quiet now")
    back.monsters = []
    for way in ("up", "down"):
        back.do(way)
    ok(back.turn > game.turn - 1, "you play on")


def test_the_ending_is_only_in_phase_2():
    classic = rules.Game("Hero", seed=1)
    classic.king_quest = rules.Quest("Defeat the Shadow King", 1)
    classic.story.clear()
    classic.beat_the_king()
    ok(classic.won and [c[0] for c in classic.story] == [c[0] for c in story.THE_LIGHT_COMES_BACK],
       "Classic: you win, with the classic cards only")


def test_the_ending_in_the_window():
    app = classic_game.App("Hero", seed=1, sound=False, throne=True, phase2_mode="phase2")
    game = app.game
    game.monsters = []
    frames(app, 10)
    ok(game.cave and game.cave.is_throne_room, "in the throne room")
    game.cave.beaten_time = 0.01                     # as if you just beat him
    frames(app, 30)
    ok(app.state == "story" and game.king_beaten, "the ending cards show")
    for _ in range(12):
        if app.state != "story":
            break
        press(app, pygame.K_RETURN)
        frames(app, 3)
    frames(app, 30)
    ok(app.state == "play" and game.world == 1 and game.cave is None, "then you're home on the map")


# ===========================================================================
# Saving in the middle of it
# ===========================================================================

def test_save_and_load_keeps_the_main_quest_where_it_was():
    game = world()
    play_chapter(game, "main_home")
    talk_through(game, "elder_oona")
    do_goal(game, "defeat:Whispering Woods:any:2")
    ok(save.save_game(game), "saved")
    back = save.load_game()
    back.monsters = []
    ok(quests.step(back, "main_woods") == 1 and "(2/4)" in quests.step_text(back, "main_woods"),
       "still on the woods chapter, 2 of 4 monsters")
    ok(main_quest.relics(back) == ["the Dawn Stone"], "with the Dawn Stone")
    ok(people.shown(back, people.person("elder_oona")), "Oona is still there")
    do_goal(back, "defeat:Whispering Woods:any:2")
    ok(quests.step(back, "main_woods") == 2, "and the next 2 finish the step")
    ok(play_chapter(back, "main_woods"), "the chapter goes on after loading")


def test_saving_in_nightfall_hollow_keeps_the_way_home():
    game = world()
    all_relics(game)
    game.player.pos = game.portal
    game.check_portal()
    ok(save.save_game(game), "saved in Nightfall Hollow")
    back = save.load_game()
    ok(back.world == 2 and back.home_world and back.home_world["world"] == 1, "the home world is in the save")
    back.king_quest = rules.Quest("Defeat the Shadow King", 1)
    back.story.clear()
    back.beat_the_king()
    ok(back.world == 1 and back.map == game.home_world["map"], "and comes back after the end")


# ===========================================================================
# The main quest and the side quests (stage 3b) together
# ===========================================================================

def test_one_monster_counts_for_the_main_quest_and_a_side_quest_at_once():
    game = world()
    game.quest_state["main_frost"] = {"status": "active", "step": 1}       # defeat 3 Frost Wolves in Frost Peaks
    quests.start(game, "sven_wolves")                                     # Sven's side quest: beat 3 Frost Wolves
    do_goal(game, "defeat:Frost Peaks:Frost Wolf:2")
    ok(game.quest_state["main_frost"]["count"] == 2 and game.quest_state["sven_wolves"]["count"] == 2,
       "2 wolves: 2 for each quest, on the same counter")
    do_goal(game, "defeat:Frost Peaks:Frost Wolf:1")
    ok(quests.step(game, "main_frost") == 2, "the 3rd wolf moves the main quest on...")
    ok(quests.step(game, "sven_wolves") == 1, "...and Sven's side quest too")


def test_side_quest_words_never_hide_the_main_quest():
    game = world()
    do_goal(game, "level:3")
    game.quest_state["main_desert"] = {"status": "active", "step": 1}      # talk to Juno
    ok(quests.status(game, "juno_postcard") == "new", "Juno's postcard quest isn't started")
    talk_through(game, "juno")
    ok(quests.step(game, "main_desert") == 2, "Juno's main-quest words come first")
    talk_through(game, "juno")
    ok(quests.status(game, "juno_postcard") == "active", "then her postcard quest")
