"""
The fight with the Shadow King, in the throne room (throne.py).

These tests check how the fight works: his sword glows before he slashes, you can
jump over his fireballs, he can't reach the healing nook, losing puts you back by the
door, and beating him ends the story. A pretend player (a little robot) also fights
him for real, with the real jumping and running, to check that he can be beaten.
"""

import pygame

import caves
import game
import rules
import story
import throne
from helpers import DT, FakeDice, frames, hold_keys, ok, start_game


# ===========================================================================
# Little helpers for this file
# ===========================================================================

def in_the_throne_room(shards=0):
    """With Sunfang, through the castle and the great door: the fight is about to start."""
    world = rules.Game("Hero", seed=4)
    for quest in world.quests:
        quest.progress = quest.goal_count
    world.go_to_nightfall()
    world.monsters = []
    world.player.sunfang = True
    world.player.light_shards = shards
    world.open_castle()
    world.reach_throne()
    world.story.clear()
    world.level_ups.clear()
    world.take_effects()
    return world, world.cave


def play(world, seconds, player=None, **keys):
    """Play the fight for some seconds. Either hold these keys, or let `player` pick the keys every frame."""
    for frame in range(round(seconds * 60)):
        if world.won:
            return
        held = player(world.cave) if player else dict(keys)
        if frame > 0 and not player:
            held.pop("jump_pressed", None)
            held.pop("use_pressed", None)
        world.update_cave(DT, held)


def stand(room, x):
    """Put the Hero on the floor of the throne room, with his left side at x."""
    room.you.x, room.you.y = x, room.floor - room.you.h
    room.you.vx = room.you.vy = 0.0


def put_king(room, x, doing="wait", timer=1.0):
    king = room.king
    king.x, king.y, king.vx = x, room.floor - king.h, 0.0
    king.doing, king.timer = doing, timer


def in_the_nook(room):
    """Put the Hero up in the healing nook, right on the spring."""
    r, c = room.find("n")
    room.you.x, room.you.y = c + 0.5 - room.you.w / 2, r + 1 - room.you.h
    room.you.vx = room.you.vy = 0.0


def a_careful_player(room):
    """The pretend player. It knows how he fights:
    jump over fireballs, run away from the glowing sword, and hit him while his sword is stuck."""
    you, king = room.you, room.king
    toward = caves.sign(king.center[0] - you.center[0])
    keys = {}
    if not you.on_ground and you.vy < 0:
        keys["jump"] = True                                     # hold SPACE for a high jump
    for ball in room.fireballs:                                 # a fireball coming? jump over it!
        coming = (ball["x"] - you.center[0]) * ball["vx"] < 0
        gap = abs(ball["x"] - you.center[0]) - you.w / 2 - throne.FIREBALL_SIZE / 2
        if coming and you.on_ground and 0 <= gap / abs(ball["vx"]) < 0.35:
            keys["jump"] = keys["jump_pressed"] = True
    if king.doing in ("warn", "slash") and room.gap() < throne.SLASH_REACH + 0.7:
        keys["left" if toward > 0 else "right"] = True          # his sword is glowing: get away!
    elif king.doing == "stuck" or (king.doing == "wait" and not room.fireballs):
        if room.gap() > 0.6:
            keys["right" if toward > 0 else "left"] = True      # run up to him...
        elif you.swing <= 0 and king.safe_time <= 0:
            you.facing = toward
            keys["use_pressed"] = True                          # ...and hit him with Sunfang!
    return keys


# ===========================================================================
# Into the throne room
# ===========================================================================

def test_the_great_door_slams_shut_behind_you():
    world, room = in_the_throne_room()
    ok(isinstance(room, throne.ThroneRoom) and room.is_castle and room.is_throne_room and not world.won,
       "through the great door, you're in the throne room (drawn like the castle)")
    ok([q.description for q in world.quests][-1] == "Defeat the Shadow King" and not world.king_quest.completed,
       "a new quest: Defeat the Shadow King")
    ok(not world.story, "no story card: the fight just starts")
    ok(room.king.is_alive and room.king.health == throne.KING_HEALTH, "he has all his health")
    play(world, 3, left=True)
    ok(world.cave is room and room.result is None and room.you.x >= 1,
       "the door slammed shut: walking left doesn't get you out")


def test_the_throne_room_fits_on_the_screen():
    world, room = in_the_throne_room()
    ok((room.cols, room.rows) == (game.VIEW_COLS, game.VIEW_ROWS),
       "the whole throne room fits on the screen, so you can always see him")


# ===========================================================================
# How he fights
# ===========================================================================

def test_his_sword_glows_before_he_slashes():
    world, room = in_the_throne_room()
    stand(room, 8.0)
    put_king(room, 10.0)
    room.you.safe_time = 0
    health = world.player.health
    seen = []
    for _ in range(round(3 * 60)):
        world.update_cave(DT, {})
        seen.append((room.king.doing, world.player.health))
        if world.player.health < health:
            break
    doing = [d for d, _ in seen]
    ok("slash" in doing, "standing right in front of him, he slashes")
    warned = doing[:doing.index("slash")].count("warn") * DT
    ok(warned >= throne.SLASH_WARNING[0] - 2 * DT, "his sword glows for %.2f seconds first" % warned)
    ok(all(h == health for d, h in seen if d != "slash"), "the glow doesn't hurt you: only the slash does")
    ok(health - world.player.health == throne.SLASH_DAMAGE, "the slash hits for %d" % throne.SLASH_DAMAGE)


def test_run_away_from_the_glowing_sword():
    world, room = in_the_throne_room()
    stand(room, 8.0)
    put_king(room, 10.0)
    room.you.safe_time = 0
    play(world, 1, player=lambda room: {"left": room.king.doing in ("warn", "slash")})
    ok(room.king.doing in ("slash", "stuck", "wait"), "he slashed...")
    ok(world.player.health == world.player.max_health, "...but you ran away in time, so he missed")


def test_after_a_slash_his_sword_is_stuck():
    world, room = in_the_throne_room()
    put_king(room, 10.0, doing="slash", timer=throne.SLASH_TIME)
    stand(room, 3.0)
    play(world, throne.SLASH_TIME + 0.05)
    ok(room.king.doing == "stuck", "after the slash, his sword is stuck in the floor")
    play(world, throne.STUCK_TIME[0] - 0.1)
    ok(room.king.doing == "stuck", "...for %.1f seconds: that's the time to hit him!" % throne.STUCK_TIME[0])


def test_jump_over_his_fireballs():
    # Stand still: the fireball hits you
    world, room = in_the_throne_room()
    stand(room, 3.0)
    put_king(room, 13.0)
    room.you.safe_time = 0
    room.start_throwing()
    play(world, 2.5)
    ok(world.player.max_health - world.player.health == throne.FIREBALL_DAMAGE,
       "a fireball hits you for %d if you don't jump" % throne.FIREBALL_DAMAGE)

    # Jump just before it gets to you: it flies under you and splats on the wall
    world, room = in_the_throne_room()
    stand(room, 3.0)
    put_king(room, 13.0)
    room.you.safe_time = 0
    room.start_throwing()

    def jumper(room):
        ball = room.fireballs[0] if room.fireballs else None
        if ball and room.you.on_ground and ball["x"] - room.you.center[0] < 1.6:
            return {"jump": True, "jump_pressed": True}
        return {"jump": not room.you.on_ground}
    for _ in range(round(3.5 * 60)):
        world.update_cave(DT, jumper(world.cave))
        if not room.fireballs and room.king.doing != "aim":
            break
    ok(world.player.health == world.player.max_health, "jump over it and it misses you")
    ok(not room.fireballs, "...and it splats on the wall")
    ball_top = room.floor - throne.FIREBALL_HEIGHT - throne.FIREBALL_SIZE / 2
    ok(room.floor - ball_top < 1, "fireballs fly low (%.2f blocks off the floor), so you can jump over them"
       % (room.floor - ball_top))


def test_he_never_throws_fireballs_twice_in_a_row():
    world, room = in_the_throne_room()
    stand(room, 1.5)
    put_king(room, 14.5)
    moves = []                                         # everything he starts doing, in order
    for _ in range(round(20 * 60)):
        before = room.king.doing
        world.update_cave(DT, {})
        stand(room, 1.5)                               # (you stay far away, and nothing hurts you)
        room.you.safe_time = 1
        if room.king.doing != before and room.king.doing in ("aim", "walk"):
            moves.append(room.king.doing)
    ok(moves.count("aim") >= 3, "far away, he throws fireballs at you (%s)" % moves)
    ok("aim aim" not in " ".join(moves), "...but never twice in a row: he walks up to you in between (%s)" % moves)


def test_he_gets_angry_at_half_health():
    world, room = in_the_throne_room()
    king = room.king
    stand(room, 3.0)
    put_king(room, 12.0)
    room.hurt_king(king.max_health // 2 - 1, 20.0)
    ok(not king.angry, "not angry yet, with more than half his health")
    king.safe_time = 0
    room.hurt_king(1, 20.0)
    ok(king.angry, "at half health he gets ANGRY")
    ok(any(e["type"] == "king_angry" for e in world.take_effects()), "...and the game shows it (a HE'S ANGRY! banner)")
    ok(king.normal_or_angry(throne.KING_SPEED) > throne.KING_SPEED[0]
       and king.normal_or_angry(throne.SLASH_WARNING) < throne.SLASH_WARNING[0],
       "angry, he's faster and his sword glows for less time")
    put_king(room, 12.0)
    room.you.safe_time = 5
    room.start_throwing()
    thrown, flying = 0, 0
    for _ in range(round(2 * 60)):
        world.update_cave(DT, {})
        thrown += max(0, len(room.fireballs) - flying)
        flying = len(room.fireballs)
    ok(thrown == throne.FIREBALLS[1] == 2, "angry, he throws two fireballs at a time (he threw %d)" % thrown)


# ===========================================================================
# Hurting him
# ===========================================================================

def hit_him_once(shards=0):
    world, room = in_the_throne_room(shards)
    world.rng = FakeDice()                              # Sunfang always rolls its smallest hit
    stand(room, 8.0)
    put_king(room, 8.0 + room.you.w + 0.3, doing="stuck")
    room.you.facing = 1
    room.update(DT, {"use_pressed": True})
    return world, room


def test_sunfang_hurts_him_and_light_shards_make_it_hurt_more():
    world, room = hit_him_once(shards=0)
    plain = room.king.max_health - room.king.health
    ok(plain == rules.SUNFANG_DAMAGE[0], "Sunfang hits him for %d" % plain)
    world, room = hit_him_once(shards=3)
    ok(room.king.max_health - room.king.health == plain + 3 * throne.SHARD_BONUS,
       "with 3 light shards, Sunfang hits him %d harder" % (3 * throne.SHARD_BONUS))


def test_he_blinks_after_a_hit():
    world, room = hit_him_once()
    health = room.king.health
    room.you.swing = 0
    room.update(DT, {"use_pressed": True})
    ok(room.king.health == health and room.king.safe_time > 0, "hit him again straight away: he's still blinking")


def test_arrows_only_scratch_him():
    world, room = in_the_throne_room()
    world.player.has_bow, world.player.arrows = True, 3
    stand(room, 4.0)
    put_king(room, 12.0, doing="stuck", timer=5)
    room.you.facing = 1
    room.update(DT, {"shoot_pressed": True})
    play(world, 1)
    lost = room.king.max_health - room.king.health
    ok(throne.ARROW_DAMAGE[0] <= lost <= throne.ARROW_DAMAGE[1], "an arrow hurts him a little (%d)" % lost)


def test_jumping_on_his_head_does_nothing():
    world, room = in_the_throne_room()
    put_king(room, 8.0, doing="stuck", timer=5)
    room.you.x, room.you.y = 8.3, room.king.y - room.you.h - 1.0
    room.you.vy = 5.0
    play(world, 0.3)
    ok(room.king.health == room.king.max_health, "stomping on him doesn't hurt him")
    ok(room.you.y + room.you.h <= room.king.y + 0.5, "...you just bounce off his armor")


# ===========================================================================
# The healing nook
# ===========================================================================

def test_the_healing_nook_is_out_of_his_reach():
    world, room = in_the_throne_room()
    king = room.king
    in_the_nook(room)
    you = room.you
    ok(room.up_high(), "the nook is up high")
    # His sword can't reach you there, wherever he stands on the floor, facing either way
    for tenth in range(10, (room.cols - 1) * 10):
        king.x = tenth / 10
        for facing in (1, -1):
            king.facing = facing
            ok(not you.touches(*king.sword_box()), "his sword can't reach the nook (from x=%.1f)" % king.x)
    # His fireballs fly far below it
    top_of_ball = room.floor - throne.FIREBALL_HEIGHT - throne.FIREBALL_SIZE / 2
    ok(you.y + you.h < top_of_ball - 2, "his fireballs fly far below the nook")


def test_the_nook_heals_10_in_all_and_he_cant_get_you():
    world, room = in_the_throne_room()
    p = world.player
    p.health = 5
    in_the_nook(room)
    put_king(room, 6.0)
    room.you.safe_time = 0
    for _ in range(round(15 * 60)):
        before = p.health
        world.update_cave(DT, {})
        ok(p.health >= before, "nothing hurts you in the nook")
    ok(p.health == 5 + throne.NOOK_HEALING and room.healing_left == 0,
       "the spring heals you %d in all, and then it's empty (you have %d)" % (throne.NOOK_HEALING, p.health))
    ok(room.king.y + room.king.h == room.floor and room.king.doing == "wait",
       "he stays down on the floor, waiting for you")


# ===========================================================================
# Losing and winning
# ===========================================================================

def test_losing_puts_you_back_by_the_door():
    world, room = in_the_throne_room()
    p = world.player
    stand(room, 8.0)
    room.hurt_king(room.king.max_health // 2 + 5, 0.0)              # he's angry, and half beaten...
    room.healing_left = 3                                           # ...and you used most of the spring
    world.take_effects()
    put_king(room, 10.0, doing="slash", timer=throne.SLASH_TIME)
    room.king.facing = -1
    room.you.safe_time = 0
    p.health = 1
    play(world, 0.1)
    you, king = room.you, room.king
    r, c = room.find("S")
    ok(world.cave is room and not world.over, "knocked out by the Shadow King: you're still in the throne room")
    ok(p.health == p.max_health and abs(you.x - (c + (1 - you.w) / 2)) < 0.01,
       "you wake up by the door, with full health")
    ok(king.health == king.max_health and not king.angry and room.healing_left == throne.NOOK_HEALING,
       "...but he has all his health back, and the healing spring fills up again")
    ok(world.knockouts == 1 and world.king_fights == 2 and not world.story,
       "it counts as another fight (and there's no story card: just try again)")
    effects = world.take_effects()
    ok(any(e["type"] == "knockout" and "door" in e.get("sub", "") for e in effects), "a KNOCKED OUT! banner says so")


def test_a_careful_player_can_beat_him():
    world, room = in_the_throne_room()
    took = 0
    for frame in range(3 * 60 * 60):                    # 3 minutes is lots of time
        world.update_cave(DT, a_careful_player(world.cave))
        if world.won:
            took = frame * DT
            break
    ok(world.won, "the pretend player beats the Shadow King (he has %d health left)" % world.cave.king.health)
    ok(world.king_quest.completed and [card[0] for card in world.story] == [c[0] for c in story.THE_LIGHT_COMES_BACK],
       "the quest is done, and the ending cards are coming (it took %.0f seconds)" % took)


def test_light_shards_make_the_fight_shorter():
    times = []
    for shards in (0, 5):
        world, room = in_the_throne_room(shards)
        world.rng = FakeDice()
        for frame in range(3 * 60 * 60):
            world.update_cave(DT, a_careful_player(world.cave))
            if world.won:
                break
        times.append(frame)
    ok(times[1] < times[0], "with all 5 light shards he's beaten faster (%.0f s instead of %.0f s)"
       % (times[1] * DT, times[0] * DT))


def test_beating_him_in_the_game(monkeypatch):
    app = game.App("Hero", seed=4, sound=False, throne=True)
    world = start_game(app)
    world.level_ups.clear()
    frames(app, 5)
    room = world.cave
    ok(app.state == "cave" and isinstance(room, throne.ThroneRoom), "the --throne shortcut starts in the throne room")
    ok(world.player.sunfang, "...with Sunfang in your hand")
    ok(app.tune_here() == "boss", "the boss tune plays")

    said = []
    real_text = app.text

    def text(surf, words, *rest, **more):
        said.append(words)
        return real_text(surf, words, *rest, **more)
    monkeypatch.setattr(app, "text", text)
    frames(app, 1)
    ok("THE SHADOW KING" in said, "his name and health bar are across the top of the screen")

    # One last hit with Sunfang...
    room.king.health = 1
    stand(room, 8.0)
    put_king(room, 8.0 + room.you.w + 0.3, doing="stuck", timer=5)
    room.you.facing, room.you.safe_time = 1, 5
    held = hold_keys(monkeypatch)
    held.add(pygame.K_r)
    frames(app, 2)
    held.clear()
    ok(not room.king.is_alive and room.beaten_time is not None and not world.won, "he's beaten! the light pours out...")
    frames(app, 2)
    ok(app.tune_here() == "home", "...and the happy tune from home comes back")

    # ...then the ending cards...
    seen = []
    for _ in range(round((throne.VICTORY_TIME + 1) * 60)):
        frames(app, 1)
        if app.state == "story":
            break
    for _ in range(10):
        if app.state != "story":
            break
        seen.append(world.story[0][0])
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
        frames(app, 1)
    ok(seen == [card[0] for card in story.THE_LIGHT_COMES_BACK], "the ending cards: %s" % seen)

    # ...then THE END, with your stats
    frames(app, 120)
    ok(app.state == "end" and world.won, "then the end screen")
    said.clear()
    frames(app, 1)
    for words in ("THE END", "Level", "Monsters defeated", "Light shards", "Knocked out", "Shadow King fights"):
        ok(words in said, "THE END screen shows '%s'" % words)
