"""
The end of the adventure: through the Portal to Nightfall Hollow, forging
Sunfang at the castle gate, and the Shadow King's castle.

These tests check the game's rules (what you need to get in, what happens
when you get knocked out...), not exactly where things are on the map or in
the castle, so you can redraw them and the tests still work.
"""

import random
from collections import Counter

import pygame

import castle
import caves
import game
import rules
import story
import throne
from helpers import DT, cave_from, frames, hold_keys, new_app, new_world, ok, press, run, tiles


# ===========================================================================
# Little helpers for this file
# ===========================================================================

def finish_the_quests(world):
    """Pretend you already beat the monsters and found the diamonds back home."""
    for quest in world.quests:
        quest.progress = quest.goal_count


def step_onto(world, spot):
    """Stand right next to a spot on the map, then take one step onto it.
    (On land if there's room. If the only way there is across the water, you get a boat.)"""
    beside = []
    for direction, (dr, dc) in rules.DIRECTIONS.items():
        here = (spot[0] - dr, spot[1] - dc)
        if world.in_bounds(here) and world.tile(here) in rules.WALKABLE + "W":
            beside.append((world.tile(here) == "W", here, direction))
    ok(beside, "there's a way to walk onto %s" % (spot,))
    water, here, direction = min(beside)
    world.player.has_boat = world.player.has_boat or water
    world.player.pos = here
    return world.do(direction)


def in_nightfall_hollow(world):
    """Finish the quests and go through the Portal, with no monsters and no story cards."""
    finish_the_quests(world)
    world.go_to_nightfall()
    world.monsters = []
    world.story.clear()
    return world


def light_the_beacons(world):
    """Pretend you beat the 3 Shadow Guardians and lit their beacons."""
    for shrine in tiles(world, "D"):
        world.beacons.add(shrine)
        world.map[shrine[0]][shrine[1]] = "H"
    world.monsters = [m for m in world.monsters if m.special != "guardian"]


def at_the_castle(diamonds=0, sunfang=False, ready=True):
    """Standing on the castle in Nightfall Hollow. ready=True: the beacons are lit, and you have the Hilt
    and the Sun Gem too (diamonds are the Blade), so only the Blade can be missing."""
    world = in_nightfall_hollow(new_world())
    world.player.diamonds = diamonds
    world.player.sunfang = sunfang
    if ready:
        light_the_beacons(world)
        world.player.has_hilt = True
        world.player.sun_shards = rules.SUN_SHARDS_NEEDED
    world.player.pos = world.castle
    return world


def inside_the_castle():
    """With Sunfang, in through the castle gate (the story cards are already read)."""
    world = at_the_castle(sunfang=True)
    world.reach_castle()
    world.story.clear()
    return world, world.cave


def titles(cards):
    return [card[0] for card in cards]


def read_the_cards(app, key=pygame.K_RETURN):
    """Press a key through every story card. Returns the titles of the cards you saw."""
    seen = []
    for _ in range(20):
        if app.state != "story":
            break
        seen.append(app.game.story[0][0] if app.game.story else None)
        press(app, key)
    return seen


def pick_a_power(app):
    """If a LEVEL UP! card is showing, wait a moment (so it can be read) and pick the first power."""
    if app.state == "levelup":
        frames(app, 40)
        press(app, pygame.K_1, "1")


def monsters_as_planned(world, counts, shadow):
    """Every land monster in `counts` is on the map. Sea Serpents only live in lakes that are
    big enough (rules.BIG_LAKE), so a world with small lakes can have fewer of them."""
    kinds = Counter(m.base_kind for m in world.monsters)
    for kind, count in counts.items():
        lives_in_water = rules.MONSTER_TYPES[kind]["special"] == "drowns"
        if kinds[kind] > count or (kinds[kind] < count and not lives_in_water):
            return False
    lakes = world.big_lakes()
    return (all(m.shadow == shadow for m in world.monsters)
            and all(m.pos in lakes for m in world.monsters if m.special == "drowns"))


def camera_inside_the_world(app):
    cx, cy = app.camera
    world = app.game
    return (0 <= cx <= max(0, world.cols * game.TILE - game.VIEW_W)
            and 0 <= cy <= max(0, world.rows * game.TILE - game.VIEW_H))


# ===========================================================================
# The Portal and Nightfall Hollow
# ===========================================================================

def test_a_new_game_starts_with_the_story():
    world = rules.Game("Hero", seed=1)
    ok(titles(world.story) == titles(story.INTRO) and any("Hero" in words for _, words, _ in world.story),
       "a new game starts with %d story cards, with your name in them" % len(story.INTRO))


def test_the_home_world_has_its_monsters():
    world = rules.Game("Hero", seed=2)
    ok(monsters_as_planned(world, rules.MONSTER_COUNTS, shadow=False),
       "%d monsters on the home world (as many as MONSTER_COUNTS says), and none are shadow monsters"
       % len(world.monsters))


def test_the_open_portal_takes_you_to_nightfall_hollow():
    world = new_world()
    finish_the_quests(world)
    world.story.clear()
    step_onto(world, world.portal)
    hollow = rules.parse_map(rules.NIGHTFALL_MAP)
    ok(world.world == 2 and not world.won and (world.rows, world.cols) == (len(hollow), len(hollow[0])),
       "the open Portal takes you to Nightfall Hollow (%d x %d) - it doesn't end the game" % (world.cols, world.rows))
    ok(world.tile_name(world.player.pos) == "Shrine" and world.player.pos == world.start,
       "you arrive at a glowing shrine")
    ok(titles(world.story) == titles(story.THROUGH_THE_PORTAL), "story cards tell you where you are")
    ok(all(m.kind.startswith("Shadow ") for m in world.monsters)
       and monsters_as_planned(world, rules.NIGHTFALL_MONSTER_COUNTS, shadow=True),
       "%d shadow monsters live there (as many as NIGHTFALL_MONSTER_COUNTS says)" % len(world.monsters))
    ok(world.portal is None and not tiles(world, "P"), "there's no way back through the Portal")
    ok(set(world.cave_plan) == set(tiles(world, "M")) and len(world.cave_plan) == 3
       and all(caves.level_theme(text) == "shadow" for text in world.cave_plan.values()),
       "the 3 Mines have dark shadow caves")
    ok(world.castle in world.reach(world.start), "the castle can be reached on foot (in case you lose your boat)")


def test_shadow_monsters_are_tougher():
    shadow, normal = rules.Monster("Zombie", (0, 0), shadow=True), rules.Monster("Zombie", (0, 0))
    ok(shadow.max_health > normal.max_health and shadow.damage[1] == normal.damage[1] + 1 and shadow.xp > normal.xp,
       "shadow monsters are tougher: %d vs %d health" % (shadow.max_health, normal.max_health))


def test_shrines_heal_you_and_dead_forests_have_wood():
    world = in_nightfall_hollow(new_world())
    world.player.health = 10
    world.do("wait")
    ok(world.player.health == 10 + rules.HOUSE_HEAL, "shrines heal you a little every turn, like houses")
    forest = next(spot for spot in tiles(world, "F") if spot in world.mainland)
    world.player.pos = forest
    world.do("chop")
    ok(world.player.wood > 0, "you can chop wood in the dead forest")


def test_the_castle_gates_stay_sealed_without_diamonds():
    world = in_nightfall_hollow(new_world())
    before = len(world.messages)
    step_onto(world, world.castle)
    ok(not world.won and not world.forging and world.cave is None
       and any("asleep" in text for text, _ in world.messages[before:]),
       "reaching the castle with no beacons lit: the forge sleeps and the gates stay sealed")


def test_the_story_cards_at_the_start_of_the_game():
    app = game.App("Hero", seed=5, sound=False)
    app.new_game()
    frames(app, 5)
    ok(app.state == "story", "the game opens with the story")
    read_the_cards(app, pygame.K_RETURN)
    ok(app.state == "play" and not app.game.story, "ENTER goes through the cards and starts the game")


def test_going_through_the_portal_in_the_app():
    app = new_app(seed=5)
    world = app.game
    finish_the_quests(world)
    step_onto(world, world.portal)
    frames(app, 10)
    every_spot = {(r, c) for r in range(world.rows) for c in range(world.cols)}
    ok(app.state == "story" and set(app.tiles) == every_spot,
       "through the Portal: new tiles are painted, and the story continues")
    press(app, pygame.K_ESCAPE)
    ok(app.state == "play" and not world.story, "ESC skips the story cards")
    world.monsters = []
    frames(app, 60)
    ok(camera_inside_the_world(app), "the camera stays inside the smaller world")

    # Walk up to the castle (it's near the edge of the world, so the camera has to stop there)
    before = len(world.messages)
    step_onto(world, world.castle)
    frames(app, 60)
    ok(camera_inside_the_world(app), "...even over by the castle")
    ok(app.state == "play" and not world.won and world.cave is None
       and any("asleep" in text for text, _ in world.messages[before:]),
       "in the app, the sealed gates just tell you what you need")


# ===========================================================================
# Forging Sunfang
# ===========================================================================

def test_wrong_keys_and_waiting_too_long_are_misses():
    forge = game.SunfangForge(random.Random(1))
    for _ in range(int(forge.RISE_TIME * 60) + 2):
        forge.update(DT)
    ok(forge.phase == "beat" and forge.key is not None, "after the diamonds rise, the first key appears")
    wrong = next(key for key, _ in forge.KEYS if key != forge.key[0])
    ok(forge.press(wrong) == "miss" and forge.beats_done == 0 and not forge.perfect,
       "the wrong key is a miss (and spoils the Perfect Forge)")
    for _ in range(int(forge.PAUSE_TIME * 60) + 2):
        forge.update(DT)
    ok(forge.phase == "beat", "...and that beat comes again")
    for _ in range(int(forge.BEAT_TIME * 60) + 2):
        forge.update(DT)
    ok(forge.phase == "pause" and "slow" in forge.message and forge.beats_done == 0, "waiting too long is a miss too")


def test_good_strikes_make_a_perfect_forge():
    forge = game.SunfangForge(random.Random(2))
    hits = 0
    for frame in range(60 * 20):
        forge.update(DT)
        if forge.phase == "beat" and forge.phase_time > 0.3:
            hits += forge.press(forge.key[0]) == "hit"
        if forge.done:
            break
    ok(forge.done and hits == forge.BEATS and forge.perfect,
       "%d good strikes, then the finale: a Perfect Forge (%.1f seconds)" % (forge.BEATS, frame / 60))


def test_sunfang_is_forged_at_the_castle_gate():
    world = at_the_castle(diamonds=rules.SUNFANG_DIAMONDS - 1)
    world.reach_castle()
    ok(not world.forging and not world.won and world.cave is None and "Blade" in world.messages[-1][0],
       "with only %d diamonds (an unfinished Blade) the gates stay sealed" % (rules.SUNFANG_DIAMONDS - 1))

    world = at_the_castle(diamonds=rules.SUNFANG_DIAMONDS)
    world.reach_castle()
    ok(world.forging and world.cave is None and titles(world.story) == titles(story.FORGE_SUNFANG),
       "with %d diamonds: the forge story begins (you can't go in until Sunfang is forged)" % rules.SUNFANG_DIAMONDS)
    world.story.clear()
    world.finish_sunfang(perfect=True)
    p = world.player
    ok(p.sunfang and p.sunfang_perfect and p.diamonds == 0 and not world.forging,
       "Sunfang is forged from the %d diamonds" % rules.SUNFANG_DIAMONDS)
    ok(not world.won and world.cave and world.cave.is_castle and world.story[0][0] == story.SUNFANG_DONE[0][0],
       "'Sunfang is yours!', then the gates open and you go inside the castle")


def test_sunfang_in_a_fight():
    world = at_the_castle()
    p = world.player
    p.sunfang = True
    swords, wear = len(p.swords), p.swords[0].durability
    zombie = rules.Monster("Zombie", p.pos, shadow=True)
    world.start_battle(zombie)
    damages = []
    for seed in range(200):
        world.rng = random.Random(seed)
        damages.append(world.player_attack(zombie))
    hitting = [d for d in damages if d]
    low, high = rules.SUNFANG_DAMAGE
    ok(min(hitting) >= low - 1 and max(hitting) <= high - 1 and len(p.swords) == swords and p.swords[0].durability == wear,
       "Sunfang hits a Shadow Zombie for %d-%d (tough -1) and never wears out" % (min(hitting), max(hitting)))
    ok(abs(len(hitting) / len(damages) - rules.SUNFANG_HIT_CHANCE) < 0.07,
       "and it hits %d%% of the time" % (100 * len(hitting) / len(damages)))

    p.sunfang_perfect = True
    world.rng = random.Random(1)
    perfect = [d for d in (world.player_attack(zombie) for _ in range(200)) if d]
    ok(min(perfect) >= low - 1 + rules.PERFECT_BONUS, "a Perfect Forge hits %d harder" % rules.PERFECT_BONUS)

    p.ring_hits = 1
    world.rng = random.Random(3)
    damage = 0
    while not damage:
        damage = world.player_attack(zombie)
    ok(p.ring_hits == 0 and damage >= low - 1 + rules.PERFECT_BONUS + rules.RING_BONUS,
       "a diamond ring powers up Sunfang too")


def test_swinging_sunfang_in_a_cave():
    world, cave = cave_from(["##############"] + ["#............#"] * 9 +
                            ["..............",
                             "..............",
                             "..S.z........#",
                             "##############"])
    world.player.sunfang = True
    zombie = cave.monsters[0]
    zombie.speed = 0
    wear = world.player.swords[0].durability
    you = cave.you
    you.x, you.facing = zombie.x - caves.PLAYER_W - 0.2, 1
    run(cave, 5)
    health = zombie.info.health
    run(cave, 1, use_pressed=True)
    hit = health - zombie.info.health
    ok(hit >= rules.SUNFANG_DAMAGE[0] - 1 and you.tool == "sunfang" and world.player.swords[0].durability == wear,
       "in a cave you swing Sunfang (%d damage, no wear)" % hit)


def test_forging_sunfang_in_the_app():
    app = new_app(seed=5)
    world = in_nightfall_hollow(app.game)
    world.player.diamonds = rules.SUNFANG_DIAMONDS
    light_the_beacons(world)
    world.player.has_hilt, world.player.sun_shards = True, rules.SUN_SHARDS_NEEDED
    frames(app, 5)
    world.player.pos = world.castle
    world.reach_castle()
    frames(app, 5)
    ok(app.state == "story", "at the gate, the story cards come first")
    read_the_cards(app)
    frames(app, 3)
    ok(app.state == "sunfang", "then the forging scene starts")

    frame = 0
    while app.state == "sunfang" and frame < 60 * 30:
        forge = app.sunfang
        if forge and forge.phase == "beat" and forge.phase_time > 0.45:
            press(app, forge.key[0])            # the right key, every time
        else:
            frames(app, 1)
        frame += 1
    ok(world.player.sunfang and world.player.sunfang_perfect, "forged in the app with a Perfect Forge (%.1f s)" % (frame / 60))
    ok(app.state == "story" and world.story[0][0] == story.SUNFANG_DONE[0][0], "then 'Sunfang is yours!'")

    read_the_cards(app)
    frames(app, 120)
    ok(app.state in ("cave", "levelup"), "'Find the castle' gives XP (a LEVEL UP! card only if it's enough for a level)")
    pick_a_power(app)
    frames(app, 5)
    ok(app.state == "cave" and world.cave and world.cave.is_castle and not world.won,
       "and the gates open: you're inside the castle")


# ===========================================================================
# The Shadow King's castle
# ===========================================================================

def test_going_into_the_castle_with_sunfang():
    world = at_the_castle(sunfang=True)
    world.reach_castle()
    inside = world.cave
    ok(isinstance(inside, castle.Castle) and inside.is_castle and not world.won,
       "with Sunfang, the castle tile takes you inside the castle")
    ok([q.description for q in world.quests] == ["Find the castle", "Reach the throne room"] and world.quests[0].completed,
       "the castle quest is done and a new one starts: Reach the throne room")
    ok(titles(world.story) == titles(story.AT_THE_CASTLE), "the first time in, the gates-open story card plays")
    names = sorted(m.name for m in inside.monsters)
    ok(names and all(m.info.shadow and m.name.startswith("Shadow ") for m in inside.monsters),
       "the guards are shadow monsters: %s" % ", ".join(names))

    r, c = inside.find("S")
    zombie = inside.add_monster("Zombie", r, c)
    ok(zombie.info.max_health == round(rules.MONSTER_TYPES["Zombie"]["health"] * rules.SHADOW_BOOST)
       and zombie.w == caves.MONSTER_SIZE["Zombie"][0],
       "a Shadow Zombie has %d health and is the size of a Zombie" % zombie.info.max_health)
    ok(not rules.Game("Hero", seed=1).new_monster("Zombie").shadow, "monsters in caves back home are still normal")


def test_the_castle_is_drawn_as_a_castle():
    world, inside = inside_the_castle()
    r, c = inside.find("S")
    ok(inside.theme == "castle" and len({len(row) for row in inside.map}) == 1,
       "the castle is a %d x %d drawing with the castle theme" % (inside.cols, inside.rows))
    ok(inside.map[r][0] not in caves.SOLIDS, "there's a gap in the left wall by the start: the castle gate")


def test_knocked_out_in_the_castle_you_start_again():
    world, inside = inside_the_castle()
    guard = inside.monsters[0]
    inside.defeat(guard, give_xp=True)
    other_guards = list(inside.monsters)
    start = (inside.you.x, inside.you.y)

    inside.you.x += 3
    inside.you.safe = (inside.you.x, inside.you.y)
    world.player.health = 1
    inside.hurt_you(3, inside.you.x + 1)
    ok(world.player.is_alive and world.player.health == world.player.max_health and not world.over,
       "knocked out in the castle: you wake up with full health")
    ok((inside.you.x, inside.you.y) == start and inside.you.vx == 0 and inside.you.safe_time > 0,
       "...back at the castle gate (no knockback, a moment to get ready)")
    ok(world.knockouts == 1 and titles(world.story) == titles(story.KNOCKED_OUT),
       "the first time, a story card explains what happened")
    ok(world.cave is inside and guard not in inside.monsters and inside.monsters == other_guards,
       "the guard you beat stays beaten (and the others are still there)")

    world.story.clear()
    world.player.health = 1
    inside.you.safe_time = 0
    inside.put_you_back(5)
    ok(world.player.health == world.player.max_health and world.knockouts == 2 and not world.story,
       "the next time, no story card - just try again")


def test_walking_out_of_the_gate_and_back_in():
    world, inside = inside_the_castle()
    guard = inside.monsters[0]
    inside.defeat(guard, give_xp=True)
    left = len(inside.monsters)
    inside.result = "left"
    world.update_cave(DT, {})
    ok(world.cave is None and not world.won and world.player.pos == world.castle
       and "castle gate" in world.messages[-1][0],
       "walk out of the gate and you're back outside the castle")
    world.reach_castle()
    ok(world.cave and world.cave.is_castle and not world.story and len(world.cave.monsters) == left
       and guard.spawn not in [m.spawn for m in world.cave.monsters] and len(world.quests) == 2,
       "go back in: no story again, and the guard you beat is still gone")


def test_each_door_leads_to_the_next_level_and_the_last_to_the_throne_room():
    world, inside = inside_the_castle()
    ok(inside.level == 0 and not inside.door_open, "you always come in at level 1, and its door is locked")
    inside.result = "exit"                       # as if you went through its door
    world.update_cave(DT, {})
    ok(world.cave and world.cave.is_castle and world.cave.level == 1 and not world.won,
       "through the door of level 1, you're in level 2 (not in the throne room yet)")

    world.enter_castle_level(len(castle.CASTLE_LEVELS) - 1)
    world.story.clear()
    world.cave.result = "exit"                   # through the door of the last level
    world.update_cave(DT, {})
    ok(isinstance(world.cave, throne.ThroneRoom) and world.throne_quest.completed and not world.won,
       "through the great door of the last level: you're in the throne room (the fight with the Shadow King is next)")


def test_a_normal_cave_knockout_costs_a_life():
    world = new_world()
    mine = next(iter(world.cave_plan))
    world.player.pos = mine
    world.enter_cave()
    world.player.health = 1
    world.cave.hurt_you(5, None)
    ok(world.player.is_alive and not world.over and world.cave is None and world.player.pos == mine
       and world.player.lives == rules.START_LIVES - 1,
       "in a normal cave, running out of health costs a life: you wake up outside the Mine")


def test_the_castle_in_the_app(monkeypatch):
    app = new_app(seed=5)
    world = in_nightfall_hollow(app.game)
    world.player.sunfang = True                 # (forging it in the app is checked above)
    world.player.pos = world.castle
    world.reach_castle()
    seen = []
    for _ in range(60 * 5):
        seen += read_the_cards(app, pygame.K_SPACE)
        pick_a_power(app)
        frames(app, 1)
        if app.state == "cave" and not world.story:
            break
    ok(app.state == "cave" and world.cave and world.cave.is_castle, "in the app: read the cards, and you're inside the castle")
    ok(story.AT_THE_CASTLE[0][0] in seen, "the gates-open card was shown on the way in")
    frames(app, 30)
    ok(app.built_cave is world.cave and app.torches and app.wall_things and app.tune_here() == "castle",
       "inside, the castle is painted with torches, banners and windows, and plays the castle tune")

    world.player.health = 1
    world.cave.you.safe_time = 0
    world.cave.hurt_you(4, None)
    frames(app, 5)
    ok(app.banner and app.banner["text"] == "KNOCKED OUT!" and app.state == "story",
       "knocked out: a big KNOCKED OUT! banner, then the story card")
    read_the_cards(app, pygame.K_SPACE)
    ok(app.state == "cave", "...and then you're back in the castle")

    # The last level: stand just in front of the great door (no guards in the way: this checks the door,
    # not the fighting. Finding every key is up to the robot, in test_beatable_caves.py)
    world.enter_castle_level(len(castle.CASTLE_LEVELS) - 1)
    for _ in range(60 * 5):                      # read the last level's story card
        frames(app, 1)
        read_the_cards(app, pygame.K_SPACE)
        if app.state == "cave" and not world.story:
            break
    inside = world.cave
    inside.monsters.clear()
    r, c = inside.spots("D")[0]
    inside.you.x, inside.you.y = c - 1.5, r + 1 - caves.PLAYER_H
    held = hold_keys(monkeypatch)
    held.add(pygame.K_RIGHT)
    frames(app, 30)
    ok(world.cave is inside and not world.won and inside.riddle in [text for text, kind in world.messages],
       "without the key, the great door stays locked and gives you a clue")
    inside.open_door()                           # as if you had the key
    inside.you.x, inside.you.y = c - 1.5, r + 1 - caves.PLAYER_H     # back in front of it
    for _ in range(120):
        pick_a_power(app)                        # (the throne room quest's XP might level you up)
        frames(app, 1)
        if isinstance(world.cave, throne.ThroneRoom) and app.state == "cave":
            break
    ok(isinstance(world.cave, throne.ThroneRoom) and app.state == "cave" and app.built_cave is world.cave
       and not world.won, "walk into the great door: you're in the throne room, ready to fight the Shadow King")
