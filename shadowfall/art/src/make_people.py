"""The realm's people, top-down, built on the same lean figure as the hero (body.py) but a head shorter
(32x48 cells, feet at 16,46). No two look alike: villagers in earth and rust browns, travellers in forest
green, fighters in steel grey, river folk in faded blue; helms, hats, bare heads with hair and beards.
One sheet per look, people_<look>: idle_down/up/side and walk_down/up/side (side faces right; the game
flips). The look names are rules/data/people.json's 'look'.

What they carry is not drawn on them: each item is its own sheet, gear_<item>, with the same cells and
animations, drawn from the figure's hand, shoulder and hip anchors. overworld/entity.gd lays the sheets
of a person's 'gear' over the body, so one body sheet makes many different people. Original art."""
from body import figure
from make_hero import lantern
from sfart import Sheet, ellipse, line, outline, poly, px, rect, surf

EARTH = ("earth0", "earth1", "earth2")
RUST = ("earth1", "earth2", "earth3")
GREEN = ("moss0", "moss1", "moss2")
GREY = ("ink2", "ink3", "ink4")
PALE = ("ink3", "ink4", "ink5")
BLUE = ("water1", "water2", "water3")
BLACK = ("ink0", "ink1", "ink2")
VIOLET = ("shadow0", "shadow1", "shadow2")
DARK_SKIN, FAIR_SKIN = ("earth1", "earth2"), ("earth3", "earth4")

LOOKS = {
    # fighters: steel grey, helms and plate
    "warden":   {"head": "nasal", "hair": "earth1", "style": "long", "chest": "plate", "tunic": GREY,
                 "cloak": GREY, "belt": "ember1", "pants": "ink2", "clasp": "light0"},
    "knight":   {"head": "great", "chest": "tabard", "tunic": PALE, "sleeve": "ink4", "glove": "ink5",
                 "belt": "earth0", "pants": "ink3", "boots": ("ink3", "ink4")},
    "watchman": {"head": "kettle", "hair": "earth1", "beard": "earth1", "chest": "mail", "tunic": RUST,
                 "belt": "earth0", "pants": "ink2"},
    "northman": {"head": "fur", "head_col": PALE, "hair": "ink6", "beard": "ink6", "beard_len": 3,
                 "skin": FAIR_SKIN, "chest": "mail", "tunic": GREY, "fur": True, "cloak": PALE, "cloak_up": 4,
                 "belt": "earth1", "pants": "ink3"},
    "deserter": {"hair": "earth1", "beard": "earth1", "chest": "plate",
                 "tunic": BLACK, "sleeve": "ink2", "mail_hem": True, "pants": "ink1", "mud": "earth2"},
    # villagers: earth and rust browns, bare heads
    "smith":    {"hair": "ink1", "beard": "ink1", "beard_len": 3, "skin": DARK_SKIN, "chest": "apron",
                 "tunic": RUST, "sleeve": "earth2", "belt": "earth0", "pants": "earth0"},
    "peasant":  {"hair": "earth1", "tunic": RUST, "belt": "earth0", "pants": "moss1", "mud": "earth2"},
    "child":    {"size": "small", "hair": "earth1", "tunic": ("ember0", "ember1", "ember2"),
                 "pants": "earth1", "skirt": 2},
    "elder":    {"hair": "ink6", "style": "bun", "robe": True, "tunic": EARTH, "cloak": PALE, "cloak_up": 6,
                 "belt": "earth3"},
    "woodsman": {"head": "cap", "head_col": GREEN, "feather": "ember3", "hair": "earth2", "beard": "earth2",
                 "tunic": GREEN, "sleeve": "earth1", "belt": "earth1", "pants": "earth0"},
    "bogger":   {"head": "straw", "head_col": ("earth2", "earth3", "earth4"), "beard": "ink5", "beard_len": 2,
                 "skin": DARK_SKIN, "tunic": EARTH, "sleeve": "moss1", "pants": "moss0", "mud": "moss2"},
    # travellers: forest green and road-worn rust, hats, packs
    "trader":   {"head": "wide", "head_col": GREEN, "band": "light0", "hair": "earth3", "style": "long",
                 "tunic": GREEN, "straps": "earth0", "belt": "earth2", "buckle": "light0", "pants": "earth0"},
    "wayfarer": {"head": "wide", "head_col": EARTH, "band": "ember1", "skin": DARK_SKIN, "tunic": PALE,
                 "cloak": ("ember0", "earth1", "earth2"), "straps": "earth0", "belt": "earth0", "pants": "ink2"},
    "hunter":   {"hood": GREEN, "eyes": "ink7", "fur": True, "tunic": EARTH, "cross": "earth0",
                 "cloak": GREEN, "cloak_up": 5, "belt": "earth0", "pants": "earth0"},
    # river folk: faded blue
    "ferryman": {"head": "wide", "head_col": ("water0", "water1", "water2"), "beard": "ink5", "beard_len": 2,
                 "tunic": BLUE, "sleeve": "water1", "belt": "earth1", "pants": "ink2"},
    "fisher":   {"hair": "earth0", "style": "long", "skin": DARK_SKIN, "tunic": BLUE, "robe": True,
                 "sleeve": "water2", "belt": "earth3"},
    # the few who keep their hoods up, and a monk
    "seer":     {"hood": VIOLET, "eyes": "light1", "robe": True, "tunic": VIOLET, "belt": "light0"},
    "mourner":  {"hood": BLACK, "veil": True, "robe": True, "tunic": BLACK, "cloak": BLACK},
    "pilgrim":  {"hair": "earth1", "style": "tonsure", "robe": True, "tunic": PALE, "belt": "earth3"},
}

STEEL = ("ink4", "ink5", "ink6")
# item -> where it hangs: main / off = that hand; back = on the back (behind the body when they face you)
GEAR = {"spear": "main", "staff": "main", "hammer": "main", "axe": "main", "shield": "off", "torch": "off",
        "lantern": "off", "candle": "off", "sword_back": "back", "bow": "back", "pack": "back"}
LIT = ("torch", "lantern", "candle")       # these give light: the JSON says where the flame is


def gear(item, d, A, flick=0):
    """One frame of an item on a clear cell, from the figure's anchors A. Returns (frame, flame x y or None)."""
    s = surf(32, 48)
    cx, top, sh, hip, g = A["cx"], A["top"], A["sh"], A["hip"], A["g"]
    hx, hy = A["main"]
    ox, oy = A["off"]
    flame = None
    lean = 6 if d == "side" else 0           # from the side a long shaft rests back on the shoulder
    if item == "spear":                      # ash shaft, a leaf blade over the head
        tx = hx - lean
        line(s, "earth1", (tx, top - 2), (hx + lean // 3, g - 1))
        poly(s, STEEL[1], [(tx - 2, top - 2), (tx + 2, top - 2), (tx, top - 7)])
        px(s, STEEL[2], tx, top - 5)
        rect(s, "ember1", tx - 1, top - 1, 3, 1)
    elif item == "staff":                    # a walking staff, gnarled at the top
        tx = hx - lean
        line(s, "earth1", (tx, top + 3), (hx + lean // 3, g - 1), 2)
        rect(s, "earth2", tx - 2, top, 4, 4)
        px(s, "earth3", tx - 1, top + 1)
    elif item in ("hammer", "axe"):          # held low, head down
        line(s, "earth1", (hx, hy), (hx, hy + 8), 2)
        if item == "hammer":
            rect(s, STEEL[0], hx - 3, hy + 7, 7, 4)
            rect(s, STEEL[2], hx - 3, hy + 7, 7, 1)
        else:
            poly(s, STEEL[1], [(hx, hy + 5), (hx + 5, hy + 3), (hx + 5, hy + 10), (hx, hy + 9)])
            line(s, STEEL[2], (hx + 5, hy + 4), (hx + 5, hy + 9))
    elif item == "shield":                   # a round shield, iron rim and boss, a red field
        w = 5 if d == "side" else 9
        x0 = ox - w // 2 + (1 if d == "side" else 0)
        ellipse(s, STEEL[0], x0, oy - 7, w, 11)
        ellipse(s, "ember1", x0 + 1, oy - 6, w - 2, 9)
        rect(s, STEEL[2], x0 + w // 2, oy - 3, 1 if d == "side" else 2, 2)
        px(s, "ember2", x0 + 2, oy - 5)
    elif item == "torch":                    # held up; the flame leaps
        line(s, "earth1", (ox, oy + 1), (ox, oy - 6), 2)
        rect(s, "ember2", ox - 2, oy - 10 - flick, 4, 4 + flick)
        rect(s, "ember3", ox - 1, oy - 9, 3, 3)
        px(s, "light0", ox - 1, oy - 8)
        px(s, "light1", ox, oy - 8)
        px(s, "ember3", ox - flick, oy - 11 - flick)
        flame = (ox, oy - 8)
    elif item == "lantern":
        lantern(s, ox, oy + 1)
        flame = (ox, oy + 7)
    elif item == "candle":
        rect(s, "ink6", ox - 1, oy - 1, 3, 5)
        rect(s, "earth2", ox - 2, oy + 3, 5, 1)
        px(s, "light0", ox, oy - 2)
        px(s, "light1", ox, oy - 3 - flick)
        flame = (ox, oy - 2)
    elif item == "sword_back":               # a sheathed longsword slung across the back
        if d == "side":
            a, b = (cx - 5, sh - 3), (cx - 7, hip + 5)
        else:
            m = 1 if d == "up" else -1
            a, b = (cx - 6 * m, sh - 4), (cx + 6 * m, hip + 5)
        line(s, "earth0", a, b, 2)
        px(s, STEEL[1], b[0], b[1] + 1)
        line(s, STEEL[1], (a[0] - 2, a[1] + 1), (a[0] + 2, a[1] + 1))
        rect(s, "earth2", a[0], a[1] - 3, 1, 3)
        px(s, STEEL[2], a[0], a[1] - 4)
    elif item == "bow":                      # a yew bow and a quiver of grey-fletched arrows
        if d == "side":
            for y in range(sh - 5, hip + 6):
                px(s, "earth2", cx - 7 - (2 if abs(y - sh - 3) < 5 else 1 if abs(y - sh - 3) < 8 else 0), y)
            line(s, "ink6", (cx - 6, sh - 5), (cx - 6, hip + 5))
            rect(s, "earth1", cx - 5, sh - 1, 2, 8)
            px(s, "ink6", cx - 5, sh - 3)
        else:
            m = 1 if d == "up" else -1
            line(s, "earth2", (cx - 8 * m, sh - 5), (cx + 8 * m, hip + 4), 2)
            line(s, "ink6", (cx - 6 * m, sh - 6), (cx + 9 * m, hip + 2))
            line(s, "earth1", (cx + 4 * m, sh - 4), (cx + 1 * m, sh + 5), 3)
            for k in (0, 2):
                px(s, "ink6", cx + (5 + k) * m, sh - 6)
    elif item == "pack":                     # a bulky pack, a bedroll lashed on top, a tin cup
        if d == "side":
            rect(s, "earth1", cx - 10, sh, 7, 12)
            rect(s, "earth0", cx - 10, sh + 8, 7, 1)
            rect(s, "moss1", cx - 10, sh - 4, 8, 4)
            px(s, "moss2", cx - 9, sh - 3)
            px(s, STEEL[1], cx - 10, sh + 10)
        else:
            rect(s, "earth1", cx - 6, sh - 1, 13, 13)
            rect(s, "earth2", cx - 5, sh, 11, 2)
            rect(s, "earth0", cx - 6, sh + 7, 13, 1)
            rect(s, "moss1", cx - 9, sh - 5, 19, 4)
            rect(s, "moss2", cx - 9, sh - 5, 19, 1)
            for x in (cx - 5, cx + 5):
                rect(s, "earth0", x, sh - 5, 1, 4)
            rect(s, STEEL[1], cx + 7, sh + 8, 2, 3)
    return outline(s), flame


IDLE = ((0, 0), (0, 1), (1, 1), (1, 0))                         # bob, sway
WALK = ((2, 0, 1), (0, -1, 0), (-2, 0, -1), (0, -1, 0))         # step, bob, sway
DIRS = ("down", "up", "side")


def person(look, d, step=0, bob=0, sway=0):
    return outline(figure(LOOKS[look], d, step=step, bob=bob, sway=sway, hem=len(look))[0])


def gear_sheet(item):
    """gear_<item>: the people's animations, the item alone. 'light' is the flame's place in the cell."""
    sh = Sheet("gear_" + item, 32, 48, origin=[16, 46])
    ref = LOOKS["peasant"]                  # every grown person has the same anchors
    light = {}
    for d in DIRS:
        fr = [gear(item, d, figure(ref, d, bob=b)[1], i % 2) for i, (b, _) in enumerate(IDLE)]
        sh.add("idle_" + d, [f for f, _ in fr], 3)
        if fr[0][1]:
            light[d] = list(fr[0][1])
    for d in DIRS:
        sh.add("walk_" + d, [gear(item, d, figure(ref, d, step=st, bob=b)[1], i % 2)[0]
                             for i, (st, b, _) in enumerate(WALK)], 6)
    sh.extra = {"slot": GEAR[item]}
    if light:
        sh.extra["light"] = light
    sh.save()


def hound(d, step=0, bob=0):
    """Ash, the lost hound: a lean grey wolfhound, low to the ground."""
    s = surf(32, 48)
    G = ("ink2", "ink3", "ink4")
    if d == "side":
        for lx, ph in ((9, step), (13, -step), (20, -step), (24, step)):
            rect(s, G[0], lx + ph, 38 + bob, 2, 8)
        ellipse(s, G[1], 7, 29 + bob, 21, 11)
        ellipse(s, G[2], 9, 30 + bob, 15, 3)
        ellipse(s, G[1], 20, 21 + bob, 9, 9)                  # head
        rect(s, G[1], 26, 24 + bob, 5, 4)                     # the long snout
        px(s, "ink0", 30, 24 + bob)
        poly(s, G[0], [(21, 22 + bob), (24, 20 + bob), (23, 27 + bob)])   # a folded ear
        px(s, "light0", 26, 23 + bob)
        line(s, G[1], (7, 31 + bob), (2, 26 + bob - step), 2)            # tail
    else:
        for lx in (11, 19):
            rect(s, G[0], lx, 38 + bob + (step if lx == 11 else -step), 3, 8)
        ellipse(s, G[1], 9, 24 + bob, 14, 18)
        ellipse(s, G[2], 11, 25 + bob, 6, 4)
        if d == "down":
            ellipse(s, G[1], 10, 16 + bob, 12, 11)
            poly(s, G[0], [(10, 17 + bob), (13, 16 + bob), (10, 23 + bob)])
            poly(s, G[0], [(22, 17 + bob), (19, 16 + bob), (22, 23 + bob)])
            ellipse(s, G[2], 13, 22 + bob, 6, 7)
            px(s, "light0", 13, 20 + bob); px(s, "light0", 18, 20 + bob)
            px(s, "ink0", 15, 27 + bob); px(s, "ink0", 16, 27 + bob)
        else:
            ellipse(s, G[1], 10, 16 + bob, 12, 10)
            poly(s, G[0], [(10, 17 + bob), (13, 16 + bob), (10, 23 + bob)])
            poly(s, G[0], [(22, 17 + bob), (19, 16 + bob), (22, 23 + bob)])
            line(s, G[1], (16, 40 + bob), (16 + step, 45), 2)
    return outline(s)


def main():
    for look in LOOKS:
        sh = Sheet("people_" + look, 32, 48, origin=[16, 46])
        for d in DIRS:
            sh.add("idle_" + d, [person(look, d, bob=b, sway=w) for b, w in IDLE], 3)
        for d in DIRS:
            sh.add("walk_" + d, [person(look, d, step=st, bob=b, sway=w) for st, b, w in WALK], 6)
        sh.save()
    for item in GEAR:
        gear_sheet(item)
    sh = Sheet("people_hound", 32, 48, origin=[16, 46])
    for d in DIRS:
        sh.add("idle_" + d, [hound(d, bob=b) for b, _ in IDLE], 3)
    for d in DIRS:
        sh.add("walk_" + d, [hound(d, step=st, bob=b) for st, b, _ in WALK], 8)
    sh.save()


if __name__ == "__main__":
    main()
