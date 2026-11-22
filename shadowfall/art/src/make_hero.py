"""The Hero, the Lanternbearer (docs/teen/art/ref/lanternbearer_concept.jpg): a midnight-blue hood up, the face
in shadow but for pale eyes, a long torn cloak, dark leather and chainmail, one steel pauldron and steel vambraces
on the sword arm, a blood-red sash, muddy boots, and an iron-caged lantern on the belt (the brightest thing on
screen; it swings). Side sheet 48x64 (caves, faces right) and top-down sheet 32x48 (the realm). Original art."""
import math

from sfart import Sheet, circle, ellipse, flash, line, outline, poly, poof, px, rect, save_png, surf

CLOAK = ("water0", "water1", "water2")  # shadow, base, light: deep midnight blue
SASH = ("ember1", "ember2")
SKIN = ("earth2", "earth3")
BOOT = ("earth0", "earth1")
LEATHER = ("earth0", "earth1", "earth2")
STEEL = ("ink4", "ink5", "ink6")
MAIL = ("ink2", "ink3")


def lantern(s, x, y, glow=True):
    """An iron-caged lantern hanging from (x, y): ring, cap, flame behind bars, base. ~7x11."""
    line(s, "ink4", (x, y), (x, y + 1))
    poly(s, "ink3", [(x - 2, y + 2), (x + 2, y + 2), (x + 3, y + 3), (x - 3, y + 3)])
    rect(s, "light0", x - 2, y + 4, 5, 5)
    if glow:
        rect(s, "light1", x - 1, y + 5, 3, 3)
        px(s, "ink7", x, y + 6)
    for bx in (x - 3, x + 3):
        line(s, "ink2", (bx, y + 4), (bx, y + 8))
    line(s, "ink3", (x, y + 4), (x, y + 4))
    rect(s, "ink3", x - 3, y + 9, 7, 2)


SUNFANG = [False]  # while True every sword drawn is Sunfang (the *_sunfang anims)


def sword(s, hx, hy, ang, length=20, runes=False):
    """A plain longsword, hilt at (hx, hy), pointing at ang (degrees, 0 = right, 90 = down)."""
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    tip = (hx + dx * length, hy + dy * length)
    line(s, "ink5", (hx + dx * 3, hy + dy * 3), tip, 3)
    line(s, "ink7", (hx + dx * 4 - dy, hy + dy * 4 + dx), (tip[0] - dy, tip[1] + dx))
    if runes or SUNFANG[0]:  # Sunfang: glowing runes down the fuller, a pale-gold edge
        line(s, "light0", (hx + dx * 4 + dy, hy + dy * 4 - dx), (tip[0] + dy, tip[1] - dx))
        for k in range(4, int(length) - 1, 3):
            px(s, "light1" if k % 2 else "ember3", hx + dx * k, hy + dy * k)
    line(s, "earth0", (hx - dx * 3, hy - dy * 3), (hx, hy), 2)
    px(s, "ink5", hx - dx * 4, hy - dy * 4)
    line(s, "ink4", (hx + dx * 2 - dy * 3, hy + dy * 2 + dx * 3), (hx + dx * 2 + dy * 3, hy + dy * 2 - dx * 3), 2)


def slash(s, cx, cy, r, a0, a1):
    """A swing arc (white-gold), drawn as stepped pixels."""
    for i in range(14):
        a = math.radians(a0 + (a1 - a0) * i / 13)
        for k in (0, 1):
            px(s, "light1" if k else "ink7", cx + math.cos(a) * (r - k), cy + math.sin(a) * (r - k))


def torn(x0, x1, y, n, depth, seed=0):
    """A ragged hem from (x0, y) to (x1, y): n teeth hanging down by up to depth."""
    pts = []
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        pts.append((x, y + (depth if (k + seed) % 2 else depth // 3) + ((k * 7 + seed) % 3) - 1))
    return pts


def leg(s, hip, foot, near):
    knee = ((hip[0] + foot[0]) / 2 + 2, (hip[1] + foot[1]) / 2)
    pants = "earth1" if near else "ink2"
    line(s, pants, hip, knee, 5)
    line(s, pants, knee, foot, 4)
    bt = BOOT[1] if near else BOOT[0]
    rect(s, bt, foot[0] - 2, foot[1] - 7, 5, 6)
    rect(s, bt, foot[0] - 2, foot[1] - 2, 7, 3)
    if near:
        rect(s, "earth0", foot[0] - 2, foot[1] - 7, 5, 1)  # boot cuff
        px(s, "earth2", foot[0] + 2, foot[1] - 1)          # mud
        px(s, "earth2", foot[0] - 1, foot[1] - 4)


def side(bob=0, front=(3, 0), back=(-3, 0), sway=0, scarf=0, hand=(9, 38), lamp=True,
         sword_ang=None, arc=None, crouch=0, lean=0, hood_back=0, lamp_hand=False):
    """One side-view frame. Feet offsets are from the standing spot; hand is the sword hand. sway streams the
    cloak back, scarf the sash tail. lamp_hand: the lantern is held up in the hand instead of on the belt."""
    s = surf(48, 64)
    cx, g = 24 + lean, 62
    hip = (24, 45 + bob + crouch)
    top = 22 + bob + crouch
    hem = 57 + bob + crouch // 2
    # the cloak's back half, behind everything: long, torn, streaming
    back_hem = torn(cx - 13 - sway * 2, cx - 1, hem - sway // 2, 5, 4, seed=sway)
    poly(s, CLOAK[0], [(cx - 5, top - 1), (cx + 1, top)] + back_hem[::-1] +
         [(cx - 12 - sway * 2, hem - 8 - sway), (cx - 9 - sway, top + 8)])
    line(s, CLOAK[1], (cx - 6, top + 2), (cx - 10 - sway * 2, hem - 6 - sway // 2))
    leg(s, hip, (24 + back[0], g + back[1]), False)
    # body: leather jerkin over chainmail, the mail skirt torn at the hem
    poly(s, MAIL[0], torn(cx - 5, cx + 6, hip[1] + 5, 4, 3, 1)[::-1] + [(cx - 5, top + 4), (cx + 6, top + 4)])
    for y in range(top + 5, hip[1] + 6, 2):
        for x in range(cx - 4 + (y // 2) % 2, cx + 6, 2):
            px(s, MAIL[1], x, y)
    poly(s, LEATHER[1], [(cx - 5, top + 2), (cx + 5, top + 2), (cx + 6, hip[1] - 4), (cx - 5, hip[1] - 4)])
    line(s, LEATHER[2], (cx + 4, top + 3), (cx + 5, hip[1] - 5))
    line(s, LEATHER[0], (cx - 4, top + 3), (cx + 4, hip[1] - 7), 1)  # cross strap
    leg(s, hip, (24 + front[0], g + front[1]), True)
    # blood-red sash with a fluttering tail, belt buckle
    rect(s, SASH[1], cx - 5, hip[1] - 6, 12, 4)
    rect(s, SASH[0], cx - 5, hip[1] - 3, 12, 1)
    poly(s, SASH[0], [(cx - 4, hip[1] - 4), (cx - 1, hip[1] - 3), (cx - 6 - scarf, hip[1] + 6 - scarf // 2),
                      (cx - 8 - scarf, hip[1] + 4 - scarf // 2)])
    px(s, "ink5", cx + 3, hip[1] - 4)
    # the lantern on the belt, swinging
    if lamp and not lamp_hand:
        lantern(s, cx + 6 - round(sway / 2), hip[1] - 3)
    # the cloak over the back shoulder
    poly(s, CLOAK[1], [(cx - 6, top - 1), (cx + 3, top - 1), (cx + 1, top + 6), (cx - 2, hem - 12),
                       (cx - 7 - sway, hem - 9 - sway // 2), (cx - 8 - sway, top + 6)])
    line(s, CLOAK[2], (cx - 7 - sway // 2, top + 4), (cx - 6 - sway, hem - 11))
    # hood, peak trailing back, face in shadow, pale eyes
    hy = 7 + bob + crouch
    hb = hood_back
    ellipse(s, CLOAK[1], cx - 8 - hb, hy, 17, 17)
    poly(s, CLOAK[1], [(cx - 7 - hb, hy + 3), (cx - 12 - hb - sway // 2, hy + 9), (cx - 5, hy + 11)])
    poly(s, CLOAK[0], [(cx - 9 - hb, hy + 10), (cx - 12 - hb - sway // 2, hy + 9), (cx - 4, hy + 16), (cx - 6, hy + 17)])
    line(s, CLOAK[2], (cx - 5 - hb, hy + 1), (cx + 3, hy + 1))
    line(s, CLOAK[2], (cx + 5, hy + 3), (cx + 8, hy + 7))
    ellipse(s, "ink0", cx + 1, hy + 5, 8, 11)
    ellipse(s, "ink1", cx + 3, hy + 8, 6, 8)
    px(s, "ink6", cx + 5, hy + 9)
    px(s, "ink7", cx + 6, hy + 9)
    for fx, fy in ((6, 10), (7, 11), (6, 11), (7, 12), (6, 13), (5, 14)):
        px(s, SKIN[0], cx + fx, hy + fy)
    px(s, SKIN[1], cx + 7, hy + 10)
    px(s, CLOAK[2], cx - 2, hy + 15)                   # cloak clasp
    # the sword arm: steel pauldron, vambrace, gloved hand
    sh = (cx + 4, top + 6)
    if lamp_hand:
        hx, hy2 = cx + hand[0] - 9 + 9, hand[1] + bob + crouch
    elif sword_ang is not None:
        hx, hy2 = cx + 2 + round(math.cos(math.radians(sword_ang)) * 3), top + 10 + round(math.sin(math.radians(sword_ang)) * 3)
    else:
        hx, hy2 = cx + hand[0] - 3, hand[1] + bob + crouch - 2
    el = ((sh[0] + hx) / 2 + 1, (sh[1] + hy2) / 2 + 1)
    line(s, LEATHER[1], sh, el, 4)
    line(s, STEEL[1], el, (hx, hy2), 4)
    line(s, STEEL[2], (el[0] + 1, el[1] - 1), (hx + 1, hy2 - 1))
    rect(s, LEATHER[1], hx - 1, hy2 - 1, 3, 3)
    # pauldron: a flat curved shoulder plate capping the arm, two lames below
    poly(s, STEEL[0], [(sh[0] - 4, sh[1] - 1), (sh[0] - 2, sh[1] - 4), (sh[0] + 2, sh[1] - 4), (sh[0] + 4, sh[1] - 2),
                       (sh[0] + 4, sh[1] + 1), (sh[0] - 4, sh[1] + 1)])
    line(s, STEEL[1], (sh[0] - 2, sh[1] - 3), (sh[0] + 2, sh[1] - 3))
    line(s, STEEL[2], (sh[0] - 1, sh[1] - 3), (sh[0] + 1, sh[1] - 3))
    line(s, STEEL[1], (sh[0] - 3, sh[1] - 1), (sh[0] + 3, sh[1] - 1))
    line(s, STEEL[0], (sh[0] - 3, sh[1] + 2), (sh[0] + 3, sh[1] + 2))
    px(s, STEEL[2], sh[0] + 3, sh[1] - 2)
    if lamp_hand:
        lantern(s, hx, hy2 + 1)
    if sword_ang is not None:
        sword(s, cx + 2, top + 10, sword_ang)
    s = outline(s)
    if arc:
        slash(s, cx + 2, top + 10, 22, *arc)
    return s


def crawl(i):
    """A low crawl under a ceiling (frame i of 4): on knees and one hand, head forward, cloak flat over the back,
    lantern hung low. Everything stays in the bottom 31 px of the frame (rows 33-63)."""
    s = surf(48, 64)
    g = 62
    st = (0, 1, 0, -1)[i]                              # the stride: near hand and far knee move opposite
    bob = (0, 0, 1, 0)[i]
    # far leg, knee down behind, boot trailing
    line(s, "ink2", (17, 49 + bob), (12 - st, g - 1), 4)
    rect(s, BOOT[0], 3 - st, g - 3, 9, 3)
    # body: low and long, leather over mail
    poly(s, MAIL[0], [(15, 46 + bob), (31, 44 + bob), (32, 52 + bob), (16, 54 + bob)])
    for x in range(17, 31, 2):
        px(s, MAIL[1], x, 52 + bob)
    poly(s, LEATHER[1], [(16, 45 + bob), (31, 43 + bob), (31, 49 + bob), (16, 51 + bob)])
    rect(s, SASH[1], 17, 48 + bob, 4, 4)
    # the lantern, swinging low under the belly
    lantern(s, 24 - st, 52 + bob)
    # near leg: thigh down to the knee on the ground, shin and boot back
    line(s, "earth1", (18, 50 + bob), (19 + st, g - 1), 5)
    line(s, "earth1", (19 + st, g - 1), (10 + st, g - 1), 4)
    rect(s, BOOT[1], 4 + st, g - 4, 8, 4)
    px(s, "earth2", 7 + st, g - 2)
    # far arm, on the ground ahead
    line(s, LEATHER[0], (31, 48 + bob), (36 - st, g - 1), 3)
    # the cloak flat over the back, torn hem trailing past the boots
    hem = torn(2, 18, 50 + bob, 4, 3, seed=i)
    poly(s, CLOAK[1], [(33, 40 + bob), (16, 42 + bob)] + hem + [(30, 47 + bob)])
    line(s, CLOAK[2], (31, 41 + bob), (14, 44 + bob))
    line(s, CLOAK[0], (18, 47 + bob), (4, 52 + bob))
    # hood low and forward, face in shadow, pale eyes
    ellipse(s, CLOAK[1], 31, 37 + bob, 12, 12)
    ellipse(s, "ink0", 36, 40 + bob, 7, 8)
    ellipse(s, "ink1", 38, 42 + bob, 4, 5)
    px(s, "ink6", 40, 43 + bob)
    px(s, "ink7", 41, 43 + bob)
    line(s, CLOAK[2], (32, 38 + bob), (38, 38 + bob))
    # near arm: pauldron, vambrace, gloved hand flat on the ground
    sh = (30, 46 + bob)
    hand = (40 + st * 2, g - 1)
    line(s, STEEL[1], sh, hand, 4)
    line(s, STEEL[2], (sh[0] + 1, sh[1] - 1), (hand[0], hand[1] - 2))
    rect(s, LEATHER[1], hand[0] - 1, hand[1] - 2, 4, 3)
    poly(s, STEEL[0], [(26, 45 + bob), (29, 42 + bob), (33, 43 + bob), (34, 47 + bob), (27, 48 + bob)])
    line(s, STEEL[2], (29, 43 + bob), (32, 43 + bob))
    return outline(s)


def side_sheet():
    sh = Sheet("hero_side", 48, 64, origin=[24, 63])
    sh.add("idle", [side(bob=b, sway=w, scarf=w, hand=(9, 38 + b)) for b, w in ((0, 0), (0, 1), (1, 1), (1, 0))], 4)
    run = []
    for i in range(6):
        a = i / 6 * 6.283
        f = (round(math.cos(a) * 8), -max(0, round(math.sin(a) * 4)))
        b = (round(-math.cos(a) * 8), -max(0, round(-math.sin(a) * 4)))
        run.append(side(bob=-abs(round(math.sin(a) * 1.5)), front=f, back=b, sway=3 + i % 2, scarf=4 + i % 3,
                        hand=(9, 36 + i % 2), lean=1))
    sh.add("run", run, 12)
    sh.add("jump", [side(bob=-1, front=(4, -5), back=(-3, -2), sway=-2, scarf=1, hand=(8, 34)),
                    side(bob=-2, front=(5, -7), back=(-4, -5), sway=1, scarf=3, hand=(9, 33)),
                    side(bob=-1, front=(3, -3), back=(-5, -1), sway=4, scarf=6, hand=(9, 31))], 10, False)
    sh.add("fall", [side(bob=-1, front=(3, -3), back=(-5, -1), sway=4 + k, scarf=6 + k, hand=(9, 31 - k))
                    for k in (0, 1)], 8)
    sh.add("land", [side(crouch=4, front=(5, 0), back=(-5, 0), sway=2, hand=(10, 40)),
                    side(crouch=2, front=(4, 0), back=(-4, 0), sway=1, hand=(9, 39))], 12, False)
    sh.add("attack", [side(sword_ang=-130, hand=(6, 40), lean=-1),
                      side(sword_ang=-40, arc=(-120, -20), hand=(6, 40), lean=2, front=(6, 0)),
                      side(sword_ang=30, arc=(-60, 40), hand=(6, 40), lean=2, front=(6, 0)),
                      side(sword_ang=70, hand=(7, 39), lean=1, front=(5, 0))], 14, False)
    sh.add("air_attack", [side(bob=-2, front=(4, -6), back=(-4, -4), sword_ang=-110, hand=(8, 33)),
                          side(bob=-2, front=(4, -6), back=(-4, -4), sword_ang=0, arc=(-90, 20), hand=(8, 33)),
                          side(bob=-2, front=(4, -6), back=(-4, -4), sword_ang=50, hand=(8, 33))], 14, False)
    sh.add("pogo", [side(bob=-3, front=(2, -8), back=(-3, -6), sword_ang=90, hand=(9, 30), sway=-3),
                    side(bob=-3, front=(2, -8), back=(-3, -6), sword_ang=90, arc=(60, 120), hand=(9, 30), sway=-4)], 12)
    SUNFANG[0] = True                      # the same swings with Sunfang in hand
    sh.add("attack_sunfang", [side(sword_ang=-130, hand=(6, 40), lean=-1),
                      side(sword_ang=-40, arc=(-120, -20), hand=(6, 40), lean=2, front=(6, 0)),
                      side(sword_ang=30, arc=(-60, 40), hand=(6, 40), lean=2, front=(6, 0)),
                      side(sword_ang=70, hand=(7, 39), lean=1, front=(5, 0))], 14, False)
    sh.add("air_attack_sunfang", [side(bob=-2, front=(4, -6), back=(-4, -4), sword_ang=-110, hand=(8, 33)),
                          side(bob=-2, front=(4, -6), back=(-4, -4), sword_ang=0, arc=(-90, 20), hand=(8, 33)),
                          side(bob=-2, front=(4, -6), back=(-4, -4), sword_ang=50, hand=(8, 33))], 14, False)
    sh.add("pogo_sunfang", [side(bob=-3, front=(2, -8), back=(-3, -6), sword_ang=90, hand=(9, 30), sway=-3),
                    side(bob=-3, front=(2, -8), back=(-3, -6), sword_ang=90, arc=(60, 120), hand=(9, 30), sway=-4)], 12)
    SUNFANG[0] = False
    sh.add("climb", [side(front=(4, -6 * (i % 2)), back=(2, -6 * ((i + 1) % 2)), hand=(8, 18 + 4 * (i % 2)),
                          lean=2, sway=-1) for i in range(4)], 8)
    sh.add("wall_slide", [side(front=(5, -3), back=(1, 0), hand=(4, 26), lean=3, sway=-3, scarf=-2)], 1)
    sh.add("dash", [side(front=(8, -2), back=(-9, -2), sway=8 + k, scarf=9 + k, lean=3, hand=(12, 34), hood_back=2)
                    for k in range(3)], 14, False)
    sh.add("swim", [side(bob=6, front=(8, -10 + 4 * (i % 2)), back=(-9, -10 + 4 * ((i + 1) % 2)), sway=6,
                         scarf=7, lamp=True, hand=(12, 34)) for i in range(4)], 8)
    sh.add("lantern_raise", [side(hand=(8, 30), lamp_hand=True), side(hand=(7, 20), lamp_hand=True),
                             side(hand=(6, 8), lamp_hand=True)], 10, False)
    sh.add("crawl", [crawl(i) for i in range(4)], 8)
    base = side()
    sh.add("hurt", [flash(base), side(lean=-3, sway=-3, hand=(8, 40))], 12, False)
    death = [side(crouch=4, lean=-2, hand=(8, 42)), side(crouch=8, front=(6, 0), back=(-6, 0), hand=(9, 46), lamp=True)]
    for k in range(4):
        f = poof(48, 64, k, seed=7)
        f.blit(lantern_only(), (0, 0))
        death.append(f)
    sh.add("death", death, 8, False)
    sh.save()


def lantern_only():
    s = surf(48, 64)
    lantern(s, 33, 50)
    return outline(s)


# --- top-down (48x56, feet at 24,54): down, up, side (right; the game flips for left) -------
# A lean ranger, about 1.45 tiles tall (body.py's "tall" figure): midnight hood and torn cloak, one bright
# steel pauldron and a vambrace on the sword arm, leather over mail, the blood-red sash, the sword held
# low, and the caged lantern in the other hand.
CELL, G = (48, 56), 54
NIGHT = ("ink1", "water0", "water1")       # the cloak: shadow, base, light (deep midnight blue)
RANGER = {"size": "tall", "hood": NIGHT, "cloak": NIGHT, "eyes": "ink7", "tunic": LEATHER, "cross": "earth0",
          "mail_hem": True, "skirt": 5, "sash": SASH, "pants": "earth0", "pants_far": "ink1", "boots": BOOT,
          "mud": "earth2", "sleeve": "ink3", "glove": "earth1", "vambrace": True, "pauldron": True,
          "clasp": "ink5"}
REST = {"down": 125, "up": 55, "side": 40}  # the sword's angle when it is only carried


def top(d, step=0, bob=0, sway=0, hem=0, sword_ang=None, arc=None, roll=None, lamp_up=0):
    cx = CELL[0] // 2
    if roll is not None:  # a tumbling cloak ball, the lantern glinting as it turns
        s = surf(*CELL)
        y = 30 - [0, 6, 6, 0][roll]
        ellipse(s, NIGHT[0], cx - 10, y, 20, 18)
        ellipse(s, NIGHT[1], cx - 9, y + 1, 17, 14)
        ellipse(s, NIGHT[2], cx - 7 + roll * 2 % 8, y + 3, 7, 3)
        rect(s, SASH[1], cx - 10 + (roll * 5) % 14, y + 8, 6, 3)
        rect(s, STEEL[2], cx - 2 + (roll * 3) % 7, y + 2, 3, 2)
        px(s, "light1", cx - 8 + (roll * 7) % 16, y + 12)
        px(s, "light0", cx - 7 + (roll * 7) % 16, y + 12)
        return outline(s)
    from body import SIZES, figure
    sh = G - sum(SIZES["tall"]) + bob + SIZES["tall"][0]
    main = off = None
    side_x = {"down": cx - 7, "up": cx + 7, "side": cx}[d]
    if sword_ang is not None:              # the sword arm reaches along the swing
        a = math.radians(sword_ang)
        main = (side_x + round(math.cos(a) * 5), sh + 5 + round(math.sin(a) * 5))
    if lamp_up:                            # the lantern lifted high in the other hand
        off = ({"down": cx + 8, "up": cx - 8, "side": cx + 5}[d], sh + 13 - lamp_up)
    s, A = figure(RANGER, d, CELL, G, step=step, bob=bob, sway=sway, main=main, off=off, hem=hem)
    hx, hy = A["main"]
    ox, oy = A["off"]
    if d == "side" and not lamp_up:        # at the back hip, over the cloak, swinging
        lantern(s, cx - 5 - sway, A["hip"] - 2)
    elif d == "up" and not lamp_up:        # carried in front: only its glow shows past the cloak
        lantern(s, ox - 1, oy + 1, glow=False)
        px(s, "light0", ox - 1, oy + 7)
    else:
        if lamp_up and d == "side":
            line(s, RANGER["sleeve"], (cx + 1, sh + 3), (ox, oy), 3)
            rect(s, RANGER["glove"], ox - 1, oy, 3, 2)
        lantern(s, ox + (1 if d == "down" else 0), oy + 1)
    sword(s, hx, hy + 1, REST[d] if sword_ang is None else sword_ang, 15)
    rect(s, RANGER["glove"], hx - 1, hy, 3, 2)
    s = outline(s)
    if arc:
        slash(s, cx, {"down": 36, "up": 26, "side": 34}[d] + bob, 17, *arc)
    return s


ATTACK = {"down": ((-150, 0), 60, 120), "up": ((-30, 0), -60, -120), "side": ((-100, 0), -20, 50)}
IDLE_T = ((0, 0), (0, 1), (1, 1), (1, 0))                         # bob, sway
WALK_T = ((2, 0, 1), (0, -1, 2), (-2, 0, -1), (0, -1, -2))        # step, bob, sway: the cloak waves


def top_sheet():
    sh = Sheet("hero_top", *CELL, origin=[CELL[0] // 2, G])
    for sun in (False, True):              # every sword-in-hand frame again with Sunfang's runes
        SUNFANG[0] = sun
        tag = "_sunfang" if sun else ""
        for d in ("down", "up", "side"):
            sh.add("idle_" + d + tag, [top(d, bob=b, sway=w, hem=i // 2) for i, (b, w) in enumerate(IDLE_T)], 4)
        for d in ("down", "up", "side"):
            sh.add("walk_" + d + tag, [top(d, step=st, bob=b, sway=w, hem=i)
                                       for i, (st, b, w) in enumerate(WALK_T)], 8)
        for d in ("down", "up", "side"):
            pre, a0, a1 = ATTACK[d]
            sh.add("attack_" + d + tag, [top(d, sword_ang=pre[0]), top(d, sword_ang=(a0 + a1) / 2, arc=(a0 - 60, a1), sway=2),
                                         top(d, sword_ang=a1, sway=1)], 14, False)
    SUNFANG[0] = False
    for d in ("down", "up", "side"):
        sh.add("roll_" + d, [top(d, roll=k) for k in range(4)], 14, False)
    sh.add("hurt", [flash(top("down")), top("down", sway=-2, bob=1)], 12, False)
    sh.add("lantern_raise", [top("down", lamp_up=k) for k in (4, 10, 16)], 10, False)
    sh.save()


# --- portrait (128x160): title screen and pause; 3/4 view, the lantern held low on the left ---
def dither(s, col, x0, y0, x1, y1, step=2):
    for y in range(y0, y1):
        for x in range(x0 + (y % step), x1, step):
            px(s, col, x, y)


def portrait():
    s = surf(128, 160)
    # cloak over the shoulders, folds falling
    poly(s, CLOAK[1], [(30, 92), (98, 92), (124, 132), (126, 160), (2, 160), (4, 132)])
    poly(s, CLOAK[0], [(30, 92), (40, 100), (22, 160), (2, 160), (4, 132)])
    for a, b in (((20, 120), (12, 160)), ((106, 118), (114, 160)), ((96, 110), (100, 160))):
        line(s, CLOAK[0], a, b, 2)
    line(s, CLOAK[2], (100, 100), (122, 136))
    line(s, CLOAK[2], (30, 98), (16, 130))
    # chest: chainmail at the collar, leather jerkin, cross strap, blood-red sash
    poly(s, MAIL[0], [(44, 108), (86, 108), (90, 160), (40, 160)])
    dither(s, MAIL[1], 44, 108, 90, 124)
    poly(s, LEATHER[1], [(46, 122), (86, 118), (90, 160), (40, 160)])
    line(s, LEATHER[2], (84, 120), (88, 158))
    line(s, LEATHER[0], (46, 124), (88, 152), 4)
    line(s, LEATHER[2], (48, 124), (88, 150))
    rect(s, "ink4", 64, 134, 4, 4)
    rect(s, SASH[1], 38, 150, 56, 7)
    rect(s, SASH[0], 38, 156, 56, 4)
    line(s, SASH[0], (50, 151), (60, 156))
    # hood: midnight blue, tall peak, deep opening
    ellipse(s, CLOAK[1], 24, 14, 80, 98)
    poly(s, CLOAK[1], [(46, 22), (58, 2), (72, 18)])
    poly(s, CLOAK[0], [(24, 60), (30, 100), (44, 112), (40, 70)])
    line(s, CLOAK[2], (58, 4), (40, 26))
    line(s, CLOAK[2], (62, 8), (88, 26), 2)
    line(s, CLOAK[2], (94, 36), (102, 64))
    line(s, CLOAK[0], (60, 12), (52, 30), 2)
    ellipse(s, CLOAK[0], 36, 30, 58, 80)
    ellipse(s, "ink0", 40, 34, 52, 74)
    # the face, 3/4 to the right, lit low from the lantern; brow in the hood's shadow
    poly(s, SKIN[0], [(52, 52), (84, 50), (88, 64), (86, 84), (78, 98), (66, 102), (56, 96), (50, 80)])
    poly(s, SKIN[1], [(74, 60), (84, 58), (86, 70), (82, 86), (76, 82), (78, 68)])
    poly(s, "earth1", [(50, 78), (56, 96), (66, 102), (60, 86), (54, 72)])
    dither(s, "earth1", 58, 90, 80, 100)                    # stubble
    poly(s, "earth1", [(52, 56), (62, 56), (60, 72), (64, 90), (66, 102), (56, 96), (50, 80)])
    poly(s, "ink1", [(48, 44), (90, 42), (90, 56), (82, 58), (70, 58), (58, 58), (48, 60)])  # hood shadow
    poly(s, "ink1", [(48, 60), (54, 58), (52, 84), (56, 96), (50, 90)])
    for ex in (60, 76):                                     # pale eyes
        rect(s, "ink4", ex - 1, 61, 9, 4)
        rect(s, "ink6", ex, 62, 7, 2)
        rect(s, "ink7", ex + 2, 62, 2, 2)
        line(s, "ink0", (ex - 1, 60), (ex + 7, 59), 2)          # brow
    line(s, "earth1", (72, 66), (70, 80))                   # nose
    line(s, SKIN[1], (74, 66), (75, 78))
    line(s, "earth1", (68, 82), (76, 82))
    line(s, "earth0", (64, 90), (76, 89))                   # mouth
    line(s, "earth1", (82, 62), (86, 80))                   # cheekbone
    # the clasp
    circle(s, "ink3", 50, 108, 5)
    circle(s, "ink5", 50, 108, 3)
    circle(s, "ink3", 50, 108, 1)
    # steel pauldron on the far shoulder, lames and rivets
    ellipse(s, STEEL[0], 84, 96, 40, 34)
    ellipse(s, STEEL[1], 86, 96, 34, 26)
    ellipse(s, STEEL[0], 88, 108, 34, 18)
    ellipse(s, STEEL[1], 88, 100, 32, 14)
    ellipse(s, STEEL[2], 96, 99, 14, 8)
    px(s, "ink7", 100, 101); px(s, "ink7", 101, 101)
    for k, y in enumerate((122, 130, 138)):
        poly(s, STEEL[0], [(88 + k * 2, y), (120 - k, y - 2), (122 - k, y + 6), (90 + k * 2, y + 7)])
        line(s, STEEL[1], (89 + k * 2, y + 1), (119 - k, y - 1))
        px(s, "ink3", 92 + k * 2, y + 3)
        px(s, "ember3", 108, y + 2)                         # rust
    # the lantern, held low on the left: iron cage, flame, glow on the cloak
    for y in range(98, 160):
        for x in range(0, 44):
            d = ((x - 18) ** 2 + (y - 130) ** 2) ** 0.5
            if d < 24 and (x + y) % (2 if d < 15 else 4) == 0 and s.get_at((x, y)).a:
                px(s, "light0" if d < 15 else "ember3", x, y)
    poly(s, "ink3", [(10, 116), (26, 116), (30, 120), (6, 120)])
    rect(s, "light0", 8, 120, 20, 22)
    rect(s, "light1", 12, 124, 12, 14)
    poly(s, "ink7", [(18, 126), (21, 132), (18, 136), (15, 132)])
    for bx in (8, 14, 21, 27):
        line(s, "ink2", (bx, 120), (bx, 141), 2)
    rect(s, "ink3", 6, 142, 24, 4)
    line(s, "ink4", (18, 108), (18, 115), 2)
    for gx, gy in ((32, 116), (36, 124), (34, 136), (4, 104), (38, 108)):
        px(s, "ember3", gx, gy)
    return outline(s)


def main():
    side_sheet()
    top_sheet()
    save_png(portrait(), "ui/hero_portrait.png")


if __name__ == "__main__":
    main()
