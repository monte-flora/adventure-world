"""The realm's people, top-down like the hero (32x48 cells, feet at 16,46): hooded, grim, each with
one thing you know them by (the smith's hammer, the pedlar's pack, the knight's helm). One sheet per
look, people_<look>: idle_down/up/side and walk_down/up/side (side faces right; the game flips).
The look names are rules/data/people.json's 'look'. Original art."""
from make_hero import lantern, torn
from sfart import Sheet, ellipse, line, outline, poly, px, rect, surf

SKIN = ("earth2", "earth3")
STEEL = ("ink4", "ink5", "ink6")

# cloak (shadow, base, light), the garment under it, then extras
LOOKS = {
    "warden":   {"cloak": ("ink1", "ink2", "ink3"), "under": "ink3", "trim": "ember1", "spear": True, "mail": True},
    "smith":    {"cloak": ("earth0", "earth1", "earth2"), "under": "earth2", "trim": "ember2", "hood": False,
                 "apron": True, "hammer": True, "beard": "ink2"},
    "trader":   {"cloak": ("moss0", "moss1", "moss2"), "under": "earth1", "trim": "light0", "pack": True},
    "child":    {"cloak": ("earth1", "earth2", "earth3"), "under": "ink3", "trim": "ember1", "small": True},
    "elder":    {"cloak": ("shadow0", "shadow1", "ink3"), "under": "ink2", "trim": "ink6", "staff": True,
                 "hair": "ink6"},
    "ferryman": {"cloak": ("water0", "water1", "ink3"), "under": "ink2", "trim": "water3", "pole": True,
                 "lamp": True},
    "knight":   {"cloak": ("ember0", "ember1", "ember2"), "under": "ink4", "trim": "light0", "hood": False,
                 "helm": True, "mail": True},
    "hunter":   {"cloak": ("moss0", "moss1", "earth1"), "under": "earth1", "trim": "ink6", "fur": True,
                 "bow": True},
    "seer":     {"cloak": ("shadow0", "shadow1", "shadow2"), "under": "ink1", "trim": "light1", "candle": True},
    "watchman": {"cloak": ("ink1", "ink2", "ink4"), "under": "earth1", "trim": "ember1", "spear": True,
                 "lamp": True},
    "mourner":  {"cloak": ("ink0", "ink1", "ink2"), "under": "ink1", "trim": "ink5", "veil": True},
    "peasant":  {"cloak": ("earth0", "earth1", "earth3"), "under": "moss1", "trim": "earth3"},
    "pilgrim":  {"cloak": ("ink3", "ink4", "ink5"), "under": "ink2", "trim": "earth3", "staff": True},
}


def person(look, d, step=0, bob=0, sway=0):
    k = LOOKS[look]
    C = k["cloak"]
    s = surf(32, 48)
    cx = 16
    sm = 6 if k.get("small") else 0          # the child stands lower and narrower
    w = 9 if sm else 11
    t, h = 19 + bob + sm, 42 + bob
    if k.get("pole") and d != "up":          # the ferryman's pole, held upright behind him
        line(s, "earth1", (cx + 9, 2 + bob), (cx + 9, 44 + bob), 2)
    for i, fx in enumerate((-5, 2)):         # boots
        st = step if i == 0 else -step
        if d == "side":
            rect(s, "earth0" if i else "earth1", cx - 3 + st * 2, 42 + bob, 6, 4)
        else:
            fy = 41 + bob + (st if d == "down" else -st)
            rect(s, "earth1", cx + fx + (1 if sm else 0), fy, 4 - (1 if sm else 0), 5)
            rect(s, "earth0", cx + fx + (1 if sm else 0), fy, 4 - (1 if sm else 0), 1)
    if k.get("pack") and d != "down":        # the pedlar's pack, lashed high on the back
        bx = cx - 6 if d == "up" else cx - 11
        rect(s, "earth1", bx, t - 2, 12 if d == "up" else 8, 13)
        rect(s, "earth2", bx + 1, t - 1, 10 if d == "up" else 6, 2)
        line(s, "earth0", (bx, t + 5), (bx + (11 if d == "up" else 7), t + 5))
        px(s, "light0", bx + 2, t + 7)
    hem = torn(cx - w + sway, cx + w + sway, h - 3, 6, 3, seed=step + sway + len(look))
    poly(s, C[1], [(cx - 7, t), (cx + 7, t)] + hem[::-1])
    poly(s, C[0], [(cx - 7, t), (cx - 4, t)] + [(x, y) for x, y in hem[:3]][::-1])
    line(s, C[2], (cx + 5, t + 2), (cx + 8 + sway, h - 4))
    if d == "down":                          # the front: what they wear under the cloak
        poly(s, k["under"], [(cx - 4, t + 2), (cx + 4, t + 2)] + torn(cx + 4, cx - 4, h - 4, 3, 2))
        if k.get("mail"):
            for y in range(t + 6, h - 4, 2):
                for x in range(cx - 3 + (y // 2) % 2, cx + 4, 2):
                    px(s, "ink4", x, y)
        if k.get("apron"):
            rect(s, "earth0", cx - 4, t + 4, 8, h - t - 8)
            px(s, "ember3", cx - 1, t + 9); px(s, "ember2", cx + 1, t + 12)   # forge burns
        rect(s, k["trim"], cx - 4, t + 9, 8, 2)                                  # belt or sash
        if k.get("pack"):
            line(s, "earth0", (cx - 4, t + 1), (cx - 3, t + 8))
            line(s, "earth0", (cx + 4, t + 1), (cx + 3, t + 8))
            rect(s, "earth2", cx + 3, t + 11, 3, 3); px(s, "light0", cx + 4, t + 12)   # coin purse
    elif d == "side":
        rect(s, k["under"], cx + 1, t + 3, 5, 9)
        rect(s, k["trim"], cx, t + 9, 7, 2)
    else:
        line(s, C[0], (cx, t + 3), (cx + sway, h - 4), 2)
    if k.get("fur"):                         # a pale wolf-fur collar
        rect(s, "ink5", cx - 7, t - 1, 14, 3)
        px(s, "ink6", cx - 5, t - 1); px(s, "ink6", cx + 2, t)
    if k.get("bow") and d != "down":
        line(s, "earth2", (cx - 8, t - 3), (cx + 6, t + 16))
        line(s, "ink6", (cx - 6, t - 4), (cx + 8, t + 15))
    # the head
    hy = 3 + bob + sm
    hw = 14 if sm else 16
    hx = cx - hw // 2
    if k.get("helm"):                        # a closed steel helm, a slit for the eyes, a crest
        ellipse(s, STEEL[0], hx + 1, hy + 1, hw - 2, 16)
        ellipse(s, STEEL[1], hx + 2, hy + 2, hw - 5, 10)
        px(s, STEEL[2], hx + 5, hy + 4)
        line(s, k["trim"], (cx, hy - 2), (cx, hy + 3), 2)
        if d == "down":
            line(s, "ink0", (cx - 4, hy + 9), (cx + 3, hy + 9))
            line(s, "ink0", (cx, hy + 9), (cx, hy + 13))
            px(s, "ink6", cx - 2, hy + 9)
        elif d == "side":
            line(s, "ink0", (cx + 2, hy + 9), (cx + 7, hy + 9))
    elif k.get("hood", True):
        ellipse(s, C[1], hx, hy, hw, 17)
        poly(s, C[1], [(cx - 3, hy + 1), (cx + 3, hy + 1), (cx, hy - 2)])
        ellipse(s, C[2], hx + 3, hy + 1, 8, 3)
        if d == "down":
            ellipse(s, "ink0", cx - 5, hy + 5, 10, 11)
            ellipse(s, "ink1", cx - 4, hy + 8, 8, 7)
            if k.get("veil"):                 # the mourner: a grey veil, no eyes at all
                for y in range(hy + 6, hy + 15, 2):
                    line(s, "ink2", (cx - 3, y), (cx + 3, y))
            else:
                px(s, "ink6", cx - 2, hy + 9); px(s, "ink6", cx + 1, hy + 9)
                for fx, fy in ((-1, 12), (0, 12), (-1, 13), (0, 13)):
                    px(s, SKIN[0], cx + fx, hy + fy)
            if k.get("hair"):                 # the elder's white braids from under the hood
                line(s, k["hair"], (cx - 5, hy + 10), (cx - 5, hy + 18))
                line(s, k["hair"], (cx + 4, hy + 10), (cx + 4, hy + 18))
        elif d == "side":
            ellipse(s, "ink0", cx + 1, hy + 5, 8, 10)
            ellipse(s, "ink1", cx + 3, hy + 7, 5, 7)
            if not k.get("veil"):
                px(s, "ink6", cx + 6, hy + 9)
        else:
            line(s, C[0], (cx, hy + 5), (cx, hy + 15), 2)
    else:                                    # bare head: the smith, soot-dark hair and beard
        ellipse(s, SKIN[0], hx + 2, hy + 3, hw - 4, 14)
        ellipse(s, "ink1", hx + 2, hy + 2, hw - 4, 6)
        if d == "down":
            ellipse(s, SKIN[1], cx - 4, hy + 6, 8, 6)
            px(s, "ink0", cx - 2, hy + 8); px(s, "ink0", cx + 1, hy + 8)
            ellipse(s, k.get("beard", "ink2"), cx - 5, hy + 11, 10, 8)
        elif d == "side":
            px(s, "ink0", cx + 4, hy + 8)
            ellipse(s, k.get("beard", "ink2"), cx + 1, hy + 11, 7, 7)
        else:
            ellipse(s, "ink1", hx + 2, hy + 3, hw - 4, 10)
    if k.get("trim") and not k.get("helm"):
        px(s, k["trim"], cx, t)              # the clasp
    # what they carry (in the near hand)
    hand = {"down": (cx + 8, t + 9), "side": (cx + 6, t + 9), "up": (cx - 8, t + 9)}[d]
    if k.get("spear"):
        line(s, "earth1", (hand[0], 4 + bob), (hand[0], 44 + bob))
        poly(s, STEEL[1], [(hand[0] - 2, 6 + bob), (hand[0] + 2, 6 + bob), (hand[0], bob)])
        px(s, STEEL[2], hand[0], 2 + bob)
    if k.get("staff"):
        line(s, "earth1", (hand[0], 6 + bob), (hand[0], 44 + bob), 2)
        ellipse(s, "earth2", hand[0] - 2, 4 + bob, 5, 4)
    if k.get("hammer") and d != "up":
        line(s, "earth1", hand, (hand[0], hand[1] + 9), 2)
        rect(s, STEEL[0], hand[0] - 3, hand[1] + 8, 7, 5)
        line(s, STEEL[2], (hand[0] - 3, hand[1] + 8), (hand[0] + 3, hand[1] + 8))
    if k.get("candle") and d != "up":
        rect(s, "ink6", hand[0] - 1, hand[1] + 1, 3, 5)
        px(s, "light0", hand[0], hand[1] - 1); px(s, "light1", hand[0], hand[1])
    if k.get("lamp") and d != "up":
        lantern(s, hand[0] - (3 if k.get("spear") else 0), hand[1] + 1)
    return outline(s)


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


IDLE = ((0, 0), (0, 1), (1, 1), (1, 0))
WALK = ((2, 0, 1), (0, -1, 0), (-2, 0, -1), (0, -1, 0))


def main():
    for look in LOOKS:
        sh = Sheet("people_" + look, 32, 48, origin=[16, 46])
        for d in ("down", "up", "side"):
            sh.add("idle_" + d, [person(look, d, bob=b, sway=w) for b, w in IDLE], 3)
        for d in ("down", "up", "side"):
            sh.add("walk_" + d, [person(look, d, step=st, bob=b, sway=w) for st, b, w in WALK], 6)
        sh.save()
    sh = Sheet("people_hound", 32, 48, origin=[16, 46])
    for d in ("down", "up", "side"):
        sh.add("idle_" + d, [hound(d, bob=b) for b, _ in IDLE], 3)
    for d in ("down", "up", "side"):
        sh.add("walk_" + d, [hound(d, step=st, bob=b) for st, b, _ in WALK], 8)
    sh.save()


if __name__ == "__main__":
    import pygame
    pygame.init()
    main()
