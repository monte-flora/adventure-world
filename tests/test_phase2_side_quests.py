"""
SIDE QUESTS in Phase 2 (stage 3b): about 2 in every village, from phase2/data/side_quests.json and
phase2/data/people_side.json. Every one can be played from start to reward here.
"""

import pygame

import rules
import sprites
from helpers import frames, ok, press
from phase2 import Phase2Game, draw_people, monsters, people, quests, save, side_steps
from phase2_helpers import own_save_file, new_phase2_app  # noqa: F401  (own_save_file is used by pytest)

VILLAGES = ("Meadowbrook", "Oakhollow", "Lakeside", "Snowcap", "Sandwell", "Bogwater")


def world(seed=1):
    game = Phase2Game("Hero", seed=seed)
    game.monsters = []
    game.lands_seen = {land[0] for land in game.atlas.lands}      # been everywhere: everyone shows up
    return game


def side_ids():
    return sorted(side_steps.load_quests())


def read_all(talk):
    for _ in range(30):
        if talk.done or talk.choices:
            return
        talk.press()


def talk(game, pid, *picks):
    """Stand next to someone and talk; pick the choices with these words (or the one that starts a quest)."""
    who = people.person(pid)
    ok(people.shown(game, who), "%s is there to talk to" % pid)
    r, c = game.people[pid]
    game.player.pos = (r, c - 1)
    t = people.start_talk(game, who)
    if t is None:
        return
    for _ in range(4):
        read_all(t)
        if t.done or not t.choices:
            break
        texts = [t.fill(ch["text"]) for ch in t.choices]
        if not picks:
            hits = [i for i, ch in enumerate(t.choices) if any(e.startswith("start_quest") for e in ch.get("do", []))]
        else:
            hits = [i for i, text in enumerate(texts) if any(pick in text for pick in picks)]
        if not hits:
            break
        t.choose(hits[0])
    game.talk = None


def beat(game, kind, n):
    for _ in range(n):
        m = monsters.make_monster(kind, (0, 0))
        game.monsters.append(m)
        game.monster_gone(m, True)


def climb(game, land):
    spot = [s for s in game.lookouts if game.atlas.land_at(s)[0] == land][0]
    game.player.pos = spot
    game.do("act")


def open_chest(game, land):
    spot = [s for s in game.found_chests if game.atlas.land_at(s)[0] == land and game.tile(s) == "T"][0]
    game.player.pos = spot
    game.do("act")
    game.do("wait")


# How to play each side quest: (what to do, from start to finish)
def play_bram(game):
    talk(game, "bram", "Any work", "Challenge accepted", "Bye")
    game.player.swords.append(rules.make_sword("great"))
    talk(game, "bram", "Bye")


def play_mabel(game):
    talk(game, "mabel", "Any errands", "I'll take it", "Bye")
    talk(game, "finn")
    talk(game, "mabel", "Bye")


def play_hazel(game):
    talk(game, "granny_hazel")
    game.player.food = 3
    talk(game, "granny_hazel", "Here you go")


def play_ivy(game):
    talk(game, "ranger_ivy")
    beat(game, "Spider", 4)
    talk(game, "ranger_ivy")


def play_marla(game):
    talk(game, "captain_marla")
    beat(game, "Sea Serpent", 2)
    talk(game, "captain_marla")


def play_lily(game):
    talk(game, "lily")
    talk(game, "finn")
    talk(game, "lily_boat_toy")
    talk(game, "lily")


def play_sven(game, choice="wool armor"):
    talk(game, "sven")
    beat(game, "Frost Wolf", 3)
    talk(game, "sven", choice)


def play_gus(game):
    talk(game, "gus")
    climb(game, "Frost Peaks")
    open_chest(game, "Frost Peaks")
    talk(game, "gus")


def play_juno(game):
    talk(game, "juno")
    talk(game, "pip")
    talk(game, "juno")


def play_zara(game):
    talk(game, "zara")
    beat(game, "Scorpion", 3)
    talk(game, "zara")


def play_bubbles(game, choice="Drink"):
    talk(game, "bubbles")
    game.player.wood, game.player.food = 5, 2
    talk(game, "bubbles", choice)


def play_wren(game):
    talk(game, "wren")
    talk(game, "hops_clue")
    talk(game, "sir_hops")
    talk(game, "wren")


PLAY = {"bram_great_sword": play_bram, "mabel_letter": play_mabel, "hazel_pie": play_hazel,
        "ivy_spiders": play_ivy, "marla_serpents": play_marla, "lily_boat": play_lily,
        "sven_wolves": play_sven, "gus_lookout": play_gus, "juno_postcard": play_juno,
        "zara_scorpions": play_zara, "bubbles_potion": play_bubbles, "wren_frog": play_wren}


# ===========================================================================
# The quests themselves
# ===========================================================================

def test_10_to_15_side_quests_about_2_in_every_village():
    ids = side_ids()
    ok(10 <= len(ids) <= 15, "10 to 15 side quests (%d)" % len(ids))
    ok(set(ids) == set(PLAY), "every side quest has a play-through in this test")
    game = world()
    per_village = {}
    for qid in ids:
        who = people.person(quests.get(qid)["giver"])
        per_village.setdefault(game.village_at(game.people[who["id"]], 4), []).append(qid)
    for village in VILLAGES:
        ok(len(per_village.get(village, [])) >= 2, "%s has 2 side quests (%s)" % (village, per_village.get(village)))
    rewards = set()
    for qid in ids:
        quest = quests.get(qid)
        for reward in [quest.get("reward", {})] + list(quest.get("choice_rewards", {}).values()):
            quests.check(qid, dict(quest, reward=reward))
            rewards |= set(reward)
    ok({"gold", "xp", "food", "arrows", "great_sword", "armor", "life", "treasure"} <= rewards, "every kind of reward")
    ok(sum(1 for q in ids if "treasure" in quests.get(q).get("reward", {})) >= 2, "2 point to a lookout's treasure")
    ok(sum(1 for q in ids if "choice_rewards" in quests.get(q)) >= 1, "a choice picks the reward")


def test_the_2_sample_quests_are_still_there():
    ok(quests.get("farmer_wood")["giver"] == "farmer_bo" and quests.get("lost_cat")["giver"] == "pip", "Bo's and Pip's")


def test_every_side_quest_from_start_to_reward():
    for qid in side_ids():
        game = world()
        game.player.food, game.player.arrows = 0, 0
        gold, xp, level, lives = game.gold, game.player.xp, game.player.level, game.player.lives
        PLAY[qid](game)
        ok(quests.status(game, qid) == "done", "%s: played to the end" % qid)
        ok(game.gold > gold or game.player.xp > xp or game.player.level > level or game.player.lives > lives,
           "%s: you get a reward" % qid)
        ok(quests.active(game) == [], "%s: no quest left half done" % qid)


def test_every_step_shows_in_order_in_the_quest_log():
    """Each step's words are in the log while you're on it, and the giver's name too."""
    game = world()
    seen = {qid: [] for qid in side_ids()}
    original = quests.advance

    def note(g, qid):
        if qid in seen:
            seen[qid].append(quests.step_text(g, qid))
        return original(g, qid)
    quests.advance = note
    try:
        for qid in side_ids():
            PLAY[qid](game)
    finally:
        quests.advance = original
    for qid, texts in seen.items():
        steps = quests.get(qid)["steps"]
        ok(texts == steps[:-1], "%s: went through every step in order (%s)" % (qid, texts))
    doing, done = draw_people.quest_lines(game)
    titles = {d[0] for d in done}
    ok({quests.get(q)["title"] for q in side_ids()} <= titles, "every side quest is in the finished list")


def test_the_quest_log_shows_a_side_quest_and_its_step():
    app = new_phase2_app()
    game = app.game
    game.lands_seen.add("Whispering Woods")
    talk(game, "ranger_ivy")
    doing, _ = draw_people.quest_lines(game)
    ok(("Too Many Spiders!", "Beat 4 Spiders", "Ranger Ivy") in doing, "it's in the log")
    frames(app, 5)
    press(app, pygame.K_q)
    frames(app, 2)
    ok(app.state == "people" and app.people_screen.kind == "quests", "Q opens the quest log")


def test_a_choice_gives_a_different_reward():
    a, b = world(), world()
    gold = a.gold
    play_sven(a, "wool armor")
    play_sven(b, "bag of gold")
    ok(a.player.has_armor and a.gold == gold, "the wool armor")
    ok(not b.player.has_armor and b.gold == gold + 50, "or the bag of gold")
    ok("sven_wolves:armor" in a.people_flags and "sven_wolves:gold" in b.people_flags, "the game remembers which")
    c, d = world(), world()
    lives = c.player.lives
    play_bubbles(c, "Drink")
    play_bubbles(d, "Sell")
    ok(c.player.lives == lives + 1 and c.gold == gold, "drink the potion: an extra life")
    ok(d.player.lives == lives and d.gold == gold + 60, "sell it: 60 gold")
    ok(c.player.wood == 0 and c.player.food == 0, "the potion used your wood and food")


def test_rewards_great_sword_life_and_treasure_map():
    game = world()
    swords = len(game.player.swords)
    play_marla(game)
    ok(len(game.player.swords) == swords + 1 and game.player.swords[-1].quality == "great", "a Great sword")
    game = world()
    hidden = [s for s in game.hidden_chests() if game.atlas.land_at(s)[0] == "Whispering Woods"]
    play_ivy(game)
    ok(any(s in game.found_chests for s in hidden), "Ivy's treasure map shows a hidden chest in the woods")
    game = world()
    lives = game.player.lives
    play_hazel(game)
    ok(game.player.lives == lives + 1, "Granny Hazel's lucky scarf: an extra life")


def test_beating_monsters_only_counts_the_right_kind_while_the_quest_is_on():
    game = world()
    beat(game, "Spider", 3)
    talk(game, "ranger_ivy")
    ok(quests.step(game, "ivy_spiders") == 0, "spiders beaten before the quest don't count")
    beat(game, "Zombie", 5)
    beat(game, "Spider", 3)
    ok(game.quest_state["ivy_spiders"]["count"] == 3 and quests.step(game, "ivy_spiders") == 0,
       "zombies don't count, 3 spiders do")
    night = monsters.make_monster("Spider", (0, 0), night=True)
    game.monster_gone(night, True)
    ok(quests.step(game, "ivy_spiders") == 1, "a night spider counts too: on to 'Tell Ranger Ivy'")


def test_the_lookout_quest_climbs_and_digs_with_the_real_keys():
    game = world()
    talk(game, "gus")
    ok(quests.step(game, "gus_lookout") == 0, "climb first")
    climb(game, "Frost Peaks")
    ok(quests.step(game, "gus_lookout") == 1, "climbing the Frost Peaks lookout does the first step")
    ok([s for s in game.found_chests if game.atlas.land_at(s)[0] == "Frost Peaks"], "it showed a Frost Peaks chest")
    game.do("wait")
    ok(quests.step(game, "gus_lookout") == 1, "the chest is still shut")
    open_chest(game, "Frost Peaks")
    ok(quests.step(game, "gus_lookout") == 2, "opening it does the second")


def test_saving_in_the_middle_of_a_side_quest():
    game = world()
    talk(game, "ranger_ivy")
    beat(game, "Spider", 2)
    talk(game, "lily")
    talk(game, "finn")
    ok(save.save_game(game), "it saves")
    back = save.load_game()
    back.monsters = []
    ok(back.quest_state["ivy_spiders"]["count"] == 2, "the 2 spiders you beat come back")
    ok(quests.step(back, "lily_boat") == 1, "so does how far you got with Lily's boat")
    beat(back, "Spider", 2)
    ok(quests.step(back, "ivy_spiders") == 1, "2 more spiders, and that step is done")
    talk(back, "lily_boat_toy")
    talk(back, "lily")
    ok(quests.status(back, "lily_boat") == "done", "and Lily's quest finishes after loading")


# ===========================================================================
# Who stands where
# ===========================================================================

def test_new_people_wait_in_their_land_and_classic_people_stay_put():
    fresh = Phase2Game("Hero", seed=1)
    ok(len(people.people_here(fresh)) <= 12, "at the start you only see the people from before")
    ok(not people.shown(fresh, people.person("zara")), "Zara shows up once you've been to the desert")
    fresh.lands_seen.add("Sunscorch Desert")
    ok(people.shown(fresh, people.person("zara")), "...and there she is")
    ok(not people.shown(fresh, people.person("sir_hops")), "lost things only show while a quest needs them")


def test_every_giver_stands_on_open_ground_away_from_monsters():
    game = Phase2Game("Hero", seed=1)
    reach = people.walk_reach(game, letters=rules.WALKABLE + "W=")
    new_ids = {who["id"] for who in side_steps._read(side_steps.PEOPLE_FILE)["people"]}
    side_people = [people.person(pid) for pid in sorted(new_ids)]
    givers = {quests.get(q)["giver"] for q in side_ids()}
    for who in side_people + [people.person(g) for g in givers]:
        pos = game.people[who["id"]]
        ok(game.tile(pos) in rules.WALKABLE, "%s stands on a walkable square" % who["id"])
        r, c = pos
        ok(any(s in reach for s in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1))), "you can get to %s" % who["id"])
        ok(all(monsters.steps(m.pos, pos) >= 2 for m in game.monsters), "no monster right next to %s" % who["id"])
    for g in givers:
        ok(game.village_at(game.people[g], 4), "%s lives in a village" % g)
        ok(monsters.is_safe(game, game.people[g]), "monsters never come to %s's square" % g)


def test_new_pictures_and_dialogue_parts():
    for who in people.all_people():
        ok(who["look"] in sprites.PEOPLE_ART, "%s has a picture" % who["id"])
    for name, art in side_steps.ART.items():
        ok(len(art) == 16 and all(len(row) == 16 for row in art), "%s is 16x16" % name)
        ok(set("".join(art)) <= set(sprites.COLORS) | {"."}, "%s uses known colors" % name)
    for who in people.all_people():
        for node in who["talk"].values():
            for variant in node if isinstance(node, list) else [node]:
                effects = list(variant.get("do", [])) + [e for ch in variant.get("choices", []) for e in ch.get("do", [])]
                for e in effects:
                    if e.startswith("finish_quest_with:"):
                        _, qid, choice = e.split(":")
                        ok(choice in quests.get(qid)["choice_rewards"], "%s: %s is a reward" % (who["id"], e))


def test_bram_and_mabel_keep_their_menus():
    game = world()
    t = people.start_talk(game, people.person("bram"))
    read_all(t)
    texts = [t.fill(ch["text"]) for ch in t.choices]
    ok(texts[0].startswith("Forge") and texts[-1] == "Bye, Bram!" and "Any work for me?" in texts, "Bram's menu")
    t = people.start_talk(game, people.person("mabel"))
    read_all(t)
    texts = [t.fill(ch["text"]) for ch in t.choices]
    ok(texts == ["Let me see your shop!", "Any errands?", "Bye, Mabel!"], "Mabel's menu")
