"""
SAVE PICTURES OF PHASE 2'S NEW ART, next to the old art, in docs/art-refresh/.

    python tools/art_preview.py            (or, in a worktree: <main checkout>/.pixi/envs/default/bin/python ...)

It needs no window. It saves:

    people_map.png          every look on the map: the old picture over the new one
    portraits.png           the dialogue box's face: old (the map picture, blown up) over new (32 x 32)
    shadow_king.png         the old and new Shadow King, calm and angry, and the story card picture
    experiment_mixed.png    AN EXPERIMENT: 2 people drawn at 32 x 32 (small pixels) next to the same
                            2 people at 16 x 16 (the world's chunky pixels), on the real map
    game_talk.png           the real game: talking to someone
    people_map_32.png       everyone on the map: old, the 16 x 16 from part 1, and whole at 32 x 32 (now in the game)
    monsters.png            every monster, old over new: in a fight, on the map, and as a shadow monster
    hero_32.png             THE FIRST TRY at the Hero at 32 x 32, next to the new people and monsters
    hero_old_new.png        the Hero, old over new: on the map, in a fight and every cave pose, with and without armor
    game_map_32.png         the real game: the map with the 32 x 32 Hero, the 32 x 32 people and the new monsters
    game_fight_hero.png     the real game: a map fight with the 32 x 32 Hero
    game_cave_hero.png      the real game: a cave in Classic (old Hero, old monsters) over Phase 2 (new ones)
    game_throne.png         the real game: the Shadow King's throne room (calm, then angry)
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault("ADVENTURE_SAVE_FILE", os.path.join(ROOT, ".art_preview_save.json"))   # never touch a real save

import pygame  # noqa: E402

import caves  # noqa: E402
import game  # noqa: E402
import rules  # noqa: E402
import sprites  # noqa: E402
from phase2 import art, hero, people  # noqa: E402

OUT = os.path.join(ROOT, "docs", "art-refresh")
GRASS = (86, 164, 74)
DARK = (38, 34, 54)
NIGHT = (30, 22, 44)
WHITE = (245, 245, 240)
YELLOW = (255, 214, 64)
LOOKS = ["farmer", "shopkeeper", "blacksmith", "guide", "wizard", "hunter", "kid", "cat", "villager", "fisher",
         "lost_bag", "frog", "toy_boat"]


def old_art(look):
    people.all_people()                 # (this also adds the side quests' pictures to sprites.PEOPLE_ART)
    return sprites.PEOPLE_ART.get(look)


def words(surf, text, spot, size=22, color=WHITE, anchor="midtop"):
    font = pygame.font.Font(None, size)
    image = font.render(text, True, color)
    surf.blit(image, image.get_rect(**{anchor: spot}))


def save(surf, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    pygame.image.save(surf, path)
    print("saved", os.path.relpath(path, ROOT))


def people_map():
    """Old over new, as big as on the map (x3) and twice that."""
    cell = 112
    sheet = pygame.Surface((90 + cell * len(LOOKS), 300))
    sheet.fill(GRASS)
    words(sheet, "old", (45, 60), 30)
    words(sheet, "new", (45, 190), 30)
    for i, look in enumerate(LOOKS):
        x = 90 + i * cell
        words(sheet, look, (x + cell // 2, 6), 20)
        old = old_art(look)
        if old:
            sheet.blit(game.make_sprite(old, 6), (x + 8, 28))
        else:
            words(sheet, "(new look)", (x + cell // 2, 70), 18)
        sheet.blit(art.map_picture(look, 6), (x + 8, 158))
        if old:
            sheet.blit(game.make_sprite(old, 3), (x + 32, 128 - 4))            # the real size on the map
        sheet.blit(art.map_picture(look, 3), (x + 32, 252))
    save(sheet, "people_map.png")


def portraits():
    """The dialogue box's face: it was the 16 x 16 map picture x10, now it's a 32 x 32 face x5."""
    cell = 176
    cols = 7
    rows = (len(LOOKS) + cols - 1) // cols
    sheet = pygame.Surface((60 + cell * cols, rows * (2 * cell + 30)))
    sheet.fill(DARK)
    for i, look in enumerate(LOOKS):
        x, y = 60 + (i % cols) * cell, (i // cols) * (2 * cell + 30)
        words(sheet, look, (x + cell // 2, y + 4), 22, YELLOW)
        for row, face in enumerate((game.make_sprite(old_art(look), 10) if old_art(look) else None,
                                    art.portrait(look))):
            frame = pygame.Rect(x + 2, y + 26 + row * cell, 172, 172)
            pygame.draw.rect(sheet, (96, 150, 86), frame, border_radius=12)
            pygame.draw.rect(sheet, (28, 26, 38), frame, 3, border_radius=12)
            if face:
                sheet.blit(face, face.get_rect(center=frame.center).move(0, 6))
        if i % cols == 0:
            words(sheet, "old", (30, y + 100), 26)
            words(sheet, "new", (30, y + 100 + cell), 26)
    save(sheet, "portraits.png")


def shadow_king():
    sheet = pygame.Surface((1500, 330))
    sheet.fill(NIGHT)
    old_glows = [game.make_soft_glow(130, (170, 90, 255), 90), game.make_soft_glow(140, (255, 50, 50), 110)]
    new_glows = [art.soft_glow(150, (170, 90, 255), 105), art.soft_glow(160, (255, 60, 40), 125)]
    things = [
        ("old", game.make_sprite(sprites.SHADOW_KING, 6), old_glows[0]),
        ("old, angry", game.make_sprite(sprites.ANGRY_SHADOW_KING, 6), old_glows[1]),
        ("NEW", art.glowing(art.KING, art.KING_SCALE, art.GLOW), new_glows[0]),
        ("NEW, angry", art.glowing(art.ANGRY_KING, art.KING_SCALE, art.ANGRY_GLOW), new_glows[1]),
        ("old story card", game.make_sprite(sprites.SHADOW_KING, 8), game.make_glow(120, (170, 90, 255))),
        ("NEW story card", art.glowing(art.KING_BIG, art.KING_CARD_SCALE, art.GLOW), game.make_glow(120, (170, 90, 255))),
    ]
    x = 0
    for label, image, glow in things:
        middle = x + 125
        sheet.blit(glow, glow.get_rect(center=(middle, 180)))
        sheet.blit(image, image.get_rect(midbottom=(middle, 300)))
        words(sheet, label, (middle, 8), 26, YELLOW)
        x += 250
    save(sheet, "shadow_king.png")


def phase2_app(throne=False):
    app = game.App("Hero", seed=1, sound=False, throne=throne, phase2_mode="phase2")
    app.new_game()
    app.game.story.clear()
    for _ in range(5):
        app.step(1 / 60)
    return app


def experiment():
    """2 people at 32 x 32 (x2 on the screen: small pixels) next to the same 2 at 16 x 16 (x3: the world's pixels)."""
    app = phase2_app()
    world = app.game
    world.monsters = []
    r0, c0 = world.player.pos
    spot = None
    for dr in (0, -1, 1, -2, 2, -3, 3):             # 4 open squares of the same ground in a row, near the Hero
        for dc in (1, -5, 2, -6, 3, -7):
            run = [(r0 + dr, c0 + dc + i) for i in range(4)]
            ground = {world.tile(p) for p in run}
            if (len(ground) == 1 and ground <= set("GF") and world.player.pos not in run
                    and not set(run) & set(world.people.values())):
                spot = spot or run
    for _ in range(3):
        app.step(1 / 60)
    screen = app.screen
    pictures = [("16 x 16", art.map_picture("farmer", 3), 8), ("32 x 32", art.make(art.BIG_PEOPLE["farmer"], 2), 0),
                ("16 x 16", art.map_picture("wizard", 3), 8), ("32 x 32", art.make(art.BIG_PEOPLE["wizard"], 2), 0)]
    left = top = None
    for pos, (label, image, inset) in zip(spot, pictures):
        x, y = app.on_screen(*game.tile_px(pos))
        screen.blit(app.shadow, (x + 14, y + 52))
        screen.blit(image, (x + inset, y + inset - (4 if inset == 0 else 0)))
        words(screen, label, (x + 32, y + 66), 18)
        left, top = (x, y) if left is None else (left, top)
    crop = pygame.Rect(left - 200, top - 150, 660, 370).clip(screen.get_rect())
    save(pygame.transform.scale(screen.subsurface(crop), (crop.w * 2, crop.h * 2)), "experiment_mixed.png")


def game_talk():
    app = phase2_app()
    world = app.game
    world.monsters = []
    who, pos = people.people_here(world)[0]
    for way, (dr, dc) in rules.DIRECTIONS.items():
        stand = (pos[0] - dr, pos[1] - dc)
        if world.tile(stand) in rules.WALKABLE and stand not in world.people.values():
            world.player.pos = stand
            world.do(way)
            break
    for _ in range(240):
        app.step(1 / 60)
    save(app.screen, "game_talk.png")


def game_throne():
    app = phase2_app(throne=True)
    for _ in range(90):
        app.step(1 / 60)
    calm = app.screen.copy()
    king = app.game.cave.king
    king.health = king.max_health // 2 - 1          # half his health: he gets angry
    king.angry = True
    for _ in range(60):
        app.step(1 / 60)
    both = pygame.Surface((calm.get_width() * 2, calm.get_height()))
    both.blit(calm, (0, 0))
    both.blit(app.screen, (calm.get_width(), 0))
    save(pygame.transform.smoothscale(both, (both.get_width() // 2, both.get_height() // 2)), "game_throne.png")


MONSTERS = ["Zombie", "Skeleton", "Ember Skull", "Spider", "Sea Serpent", "Guardian", "Warden", "Slime", "Scorpion",
            "Frost Wolf", "Bog Lurker"]


def tinted(image):
    """A shadow monster's colors (the same as game.App.monster_sprite)."""
    image = image.copy()
    image.fill((120, 96, 160), special_flags=pygame.BLEND_RGB_MULT)
    image.fill((26, 0, 40), special_flags=pygame.BLEND_RGB_ADD)
    return image


def new_monster(kind, scale):
    """A monster in Phase 2 at the old pictures' `scale` (the Skeleton and the Ember Skull keep their old picture)."""
    return art.monster_picture(phase2_app.shared, kind, scale) or game.make_sprite(sprites.MONSTER_ART[kind], scale)


def people_map_32():
    """Old, the 16 x 16 of part 1, and the 32 x 32 that's on the map now: at their real size, and twice that."""
    cell = 140
    sheet = pygame.Surface((130 + cell * len(LOOKS), 520))
    sheet.fill(GRASS)
    rows = [("old", 30), ("16 x 16", 130), ("32 x 32", 230), ("32 x 32,", 372)]
    for label, y in rows:
        words(sheet, label, (65, y + 20), 26)
    words(sheet, "(Classic)", (65, 76), 18)
    words(sheet, "(part 1)", (65, 176), 18)
    words(sheet, "NOW", (65, 276), 22, YELLOW)
    words(sheet, "twice as big", (65, 418), 18)
    for i, look in enumerate(LOOKS):
        x = 130 + i * cell
        words(sheet, look, (x + cell // 2, 6), 20)
        old = old_art(look)
        if old:
            sheet.blit(game.make_sprite(old, 3), (x + 46, 38))
        sheet.blit(art.map_picture(look, 3), (x + 46, 138))
        sheet.blit(art.big_picture(look, 2), (x + 38, 230))
        sheet.blit(art.big_picture(look, 4), (x + 6, 372))
    save(sheet, "people_map_32.png")


def monsters():
    """Old over new: in a fight (128 pixels), on the map (48 pixels) on grass and rock, and as a shadow monster."""
    cell = 150
    sheet = pygame.Surface((110 + cell * len(MONSTERS), 610))
    sheet.fill(DARK)
    sheet.fill(GRASS, (0, 330, sheet.get_width(), 140))
    for label, y in (("old", 80), ("NEW", 220), ("on the map:", 340), ("old", 362), ("NEW", 424), ("shadow:", 486),
                     ("old", 510), ("NEW", 558)):
        words(sheet, label, (55, y), 24, YELLOW if label == "NEW" else WHITE)
    for i, kind in enumerate(MONSTERS):
        x = 110 + i * cell
        same = kind not in art.MONSTER_ART
        words(sheet, kind, (x + cell // 2, 6), 20, YELLOW)
        if same:
            words(sheet, "(kept)", (x + cell // 2, 22), 16)
        old = sprites.MONSTER_ART[kind]
        sheet.blit(game.make_sprite(old, 8), (x + 11, 40))
        sheet.blit(new_monster(kind, 8), (x + 11, 180))
        sheet.blit(game.make_sprite(old, 3), (x + 51, 344))
        sheet.blit(new_monster(kind, 3), (x + 51, 408))
        sheet.blit(tinted(game.make_sprite(old, 3)), (x + 20, 492))
        sheet.blit(tinted(new_monster(kind, 3)), (x + 20, 548))
        sheet.blit(tinted(new_monster(kind, 6)), (x + 72, 492))
    save(sheet, "monsters.png")


def hero_32():
    """THE FIRST TRY: the Hero whole at 32 x 32 (2 pixels each) next to the 32 x 32 people and the new monsters."""
    sheet = pygame.Surface((1180, 430))
    sheet.fill(GRASS)
    words(sheet, "Before: the Hero was 16 x 16 (48 pixels)", (300, 8), 26, YELLOW)
    words(sheet, "The first try: the Hero at 32 x 32 (64 pixels)", (880, 8), 26, YELLOW)
    small, big = game.make_sprite(sprites.PLAYER, 3), art.make(art.BIG_HERO, 2)
    for left, hero in ((20, small), (600, big)):
        line = [hero, art.big_picture("farmer"), art.big_picture("wizard"), art.big_picture("kid"),
                new_monster("Zombie", 3), new_monster("Frost Wolf", 3), new_monster("Skeleton", 3)]
        for i, image in enumerate(line):
            spot = image.get_rect(midbottom=(left + 40 + i * 78, 130))
            sheet.blit(image, spot)
    pygame.draw.line(sheet, DARK, (590, 40), (590, 420), 3)
    words(sheet, "bigger, to see the pixels:", (300, 150), 22)
    words(sheet, "bigger, to see the pixels:", (880, 150), 22)
    sheet.blit(game.make_sprite(sprites.PLAYER, 12), (60, 190))
    sheet.blit(art.big_picture("farmer", 6), (300, 190))
    sheet.blit(art.make(art.BIG_HERO, 8), (630, 160))
    sheet.blit(art.big_picture("farmer", 6), (920, 190))
    save(sheet, "hero_32.png")


def hero_old_new():
    """The Hero, old (16 x 16) over new (32 x 32): on the map, in a fight, and every pose in a cave."""
    app = phase2_app.shared
    sheet = pygame.Surface((1500, 950))
    sheet.fill(GRASS)
    words(sheet, "The Hero: the old 16 x 16 picture over the new 32 x 32 one (Phase 2)", (750, 8), 30, YELLOW)
    # On the map and in a fight
    words(sheet, "on the map (old 48 pixels, new 64: a whole square)", (300, 44), 22)
    words(sheet, "in a map fight (128 pixels, both)", (1050, 44), 22)
    ways = ["down", "up", "right", "left", "down armor", "up armor", "right armor"]
    for i, name in enumerate(ways):
        old = app.map_walk[name][i % 3]
        new = hero.map_picture(app, name, i % 3)
        sheet.blit(old, old.get_rect(midbottom=(60 + i * 80, 130)))
        sheet.blit(new, new.get_rect(midbottom=(60 + i * 80, 210)))
    for i, armored in enumerate((False, True)):
        old = game.make_sprite(app.armored if armored else sprites.PLAYER, 8)
        sheet.blit(old, (760 + i * 140, 70))
        sheet.blit(hero.fight_picture(app, armored), (1060 + i * 140, 70))
    words(sheet, "old", (900, 204), 22)
    words(sheet, "new", (1200, 204), 22)
    # In a cave: every pose, 80 pixels, old over new, then both again with armor
    words(sheet, "in a cave (80 pixels, both: the new one is 2.5 screen pixels a square)", (750, 232), 22)
    names = ([("side_view", name) for name in app.side_view] + [("wall_view", name) for name in app.wall_view]
             + [("climb_view", 0), ("climb_view", 1)])
    for row, (views, armor, label) in enumerate(((app, "", "old"), (hero.VIEWS, "", "new"),
                                                 (app, "_armored", "old, armor"), (hero.VIEWS, "_armored", "new, armor"))):
        y = 262 + row * 110
        words(sheet, label, (48, y + 30), 20)
        for i, (view, name) in enumerate(names):
            sheet.blit(app.cave_sprite(getattr(views, view + armor)[name]), (100 + i * 106, y))
            if row == 3:
                words(sheet, "%s %s" % (view.split("_")[0], name + 1 if view == "climb_view" else name), (140 + i * 106, y + 84), 18)
    # The cave size, close up: why the 32 x 32 picture is painted at 5 and every other pixel kept
    stand = hero.VIEWS.side_view["stand"]
    close = [("old: 16 x 16, 5 pixels a square", app.cave_sprite(sprites.SIDE_STAND)),
             ("new: 2.5 a square, crisp (in the game)", app.cave_sprite(stand)),
             ("new: 2.5 a square, smoothed (not used)", pygame.transform.smoothscale(art.make(stand, 5), (80, 80))),
             ("new: 3 a square, 96 pixels (too big for the tunnels)", art.make(stand, 3))]
    for i, (label, image) in enumerate(close):
        big = pygame.transform.scale(image, (image.get_width() * 2, image.get_height() * 2))
        sheet.blit(big, big.get_rect(midbottom=(200 + i * 370, 916)))
        words(sheet, label, (200 + i * 370, 922), 20)
    save(sheet, "hero_old_new.png")


def little_cave(app, kinds):
    """Put this app's game in a little cave with these monsters in it, and draw it."""
    rows = ["######################",
            "#....................#",
            "#....................#",
            "#S.................E.#",
            "######################"]
    world = app.game
    cave = caves.Cave(world, (0, 0), "\n".join(rows))
    world.cave = cave
    cave.monsters = []
    for i, kind in enumerate(kinds):
        cave.add_monster(kind, 3, 4 + 2 * i)
    app.build_cave_tiles(cave)
    app.cam, app.time = (0, 0), 1.0
    cave.you.on_ground = True
    surf = pygame.Surface((game.VIEW_W, game.VIEW_H))
    app.draw_cave(surf)
    world.cave = None
    return surf.subsurface((0, 0, min(game.VIEW_W, len(rows[0]) * game.TILE), len(rows) * game.TILE)).copy()


def game_cave_hero():
    """A cave in a Classic game (the old Hero and monsters) over the same cave in Phase 2 (the new ones)."""
    kinds = ["Zombie", "Spider", "Skeleton", "Ember Skull", "Zombie", "Spider"]
    classic = game.App("Hero", seed=1, sound=False)
    classic.new_game()
    old, new = little_cave(classic, kinds), little_cave(phase2_app(), kinds)
    both = pygame.Surface((old.get_width(), old.get_height() * 2 + 60))
    both.fill(DARK)
    words(both, "Classic: the 16 x 16 Hero and monsters", (both.get_width() // 2, 6), 24, YELLOW)
    both.blit(old, (0, 30))
    words(both, "Phase 2: the 32 x 32 Hero and monsters, just as big (the Skeleton and Ember Skull keep theirs)",
          (both.get_width() // 2, old.get_height() + 36), 24, YELLOW)
    both.blit(new, (0, old.get_height() + 60))
    save(both, "game_cave_hero.png")


def game_fight_hero():
    """A map fight in Phase 2: the 32 x 32 Hero with his sword in his hand."""
    app = phase2_app()
    app.tips.on = False
    world = app.game
    world.monsters = []
    world.start_battle(rules.Monster("Zombie", world.player.pos))
    app.state = "battle"
    for _ in range(30):
        app.step(1 / 60)
    app.draw()
    save(app.screen.subsurface(app.battle_box.clip(app.screen.get_rect())).copy(), "game_fight_hero.png")


def game_map_32():
    """The real map: the Hero by the townsfolk, with some of the new monsters put next to them."""
    app = phase2_app()
    app.tips.on = False                                  # (no tip bubble over the picture; this isn't saved)
    world = app.game
    here = people.people_here(world)
    near = lambda p: sum(abs(p[0] - q[0]) + abs(p[1] - q[1]) <= 4 for _, q in here)     # noqa: E731
    who, pos = max(here, key=lambda one: near(one[1]))      # the one with the most neighbors
    world.player.pos = next(p for p in ((pos[0] + 1, pos[1] - 1), (pos[0] + 1, pos[1] + 1), (pos[0] - 1, pos[1] - 1))
                            if world.tile(p) in rules.WALKABLE and p not in world.people.values())
    world.monsters = []
    kinds = [kind for kind in MONSTERS if kind in rules.MONSTER_TYPES and kind != "Sea Serpent"]
    taken = set(world.people.values()) | {world.player.pos}
    spots = [(pos[0] + dr, pos[1] + dc) for dr in (2, -2, 3, -3, 1, -1) for dc in range(-4, 5)]
    spots = [p for p in spots if world.tile(p) in rules.WALKABLE and p not in taken]
    for kind, spot in zip(kinds, spots):
        world.monsters.append(rules.Monster(kind, spot, shadow=kind == "Spider"))
    app.monster_px.clear()
    for _ in range(240):                                 # (the screen fades in when a game starts)
        app.step(1 / 60)
        for m, spot in zip(world.monsters, spots):       # (hold them still for the picture)
            m.pos = spot
    app.draw()
    x, y = app.on_screen(*game.tile_px(pos))
    crop = pygame.Rect(x - 320, y - 230, 704, 520).clip(app.screen.get_rect())
    save(pygame.transform.scale(app.screen.subsurface(crop), (crop.w * 2, crop.h * 2)), "game_map_32.png")


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    phase2_app.shared = phase2_app()        # (a Phase 2 game, to ask for its monsters' pictures)
    people_map_32()
    monsters()
    hero_32()
    hero_old_new()
    game_map_32()
    game_fight_hero()
    game_cave_hero()
    people_map()
    portraits()
    shadow_king()
    experiment()
    game_talk()
    game_throne()
    save_file = os.environ["ADVENTURE_SAVE_FILE"]
    for path in (save_file, save_file + ".tmp"):
        if path.startswith(ROOT) and os.path.exists(path):
            os.remove(path)


if __name__ == "__main__":
    main()
