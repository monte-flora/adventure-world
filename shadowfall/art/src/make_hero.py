"""The Hero: a hooded wanderer with a lantern (deep-blue cloak, ember scarf, gold lantern).
Side sheet 48x64 (caves, faces right) and top-down sheet 32x48 (the realm). Original art."""
import math

from sfart import Sheet, circle, ellipse, flash, line, outline, poly, poof, px, rect, surf

CLOAK = ("water1", "water2", "water3")  # shadow, base, light
SCARF = ("ember1", "ember2")
SKIN = ("earth2", "earth3")
BOOT = ("earth0", "earth1")


def lantern(s, x, y, glow=True):
    """Hangs from (x, y): ring, cap, glass, base. ~6x10."""
    line(s, "ink4", (x, y), (x, y + 2))
    rect(s, "ink3", x - 3, y + 2, 7, 2)
    rect(s, "light0", x - 2, y + 4, 5, 5)
    if glow:
        rect(s, "light1", x - 1, y + 5, 3, 3)
    rect(s, "ink3", x - 3, y + 9, 7, 2)


def sword(s, hx, hy, ang, length=20):
    """Hilt at (hx, hy), pointing at angle ang (degrees, 0 = right, 90 = down)."""
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    tip = (hx + dx * length, hy + dy * length)
    line(s, "ink6", (hx + dx * 3, hy + dy * 3), tip, 3)
    line(s, "ink7", (hx + dx * 4 - dy, hy + dy * 4 + dx), (tip[0] - dy, tip[1] + dx))
    line(s, "earth1", (hx - dx * 3, hy - dy * 3), (hx, hy), 2)
    line(s, "light0", (hx + dx * 2 - dy * 3, hy + dy * 2 + dx * 3), (hx + dx * 2 + dy * 3, hy + dy * 2 - dx * 3), 2)


def slash(s, cx, cy, r, a0, a1):
    """A swing arc (white-gold), drawn as stepped pixels."""
    for i in range(14):
        a = math.radians(a0 + (a1 - a0) * i / 13)
        for k in (0, 1):
            px(s, "light1" if k else "ink7", cx + math.cos(a) * (r - k), cy + math.sin(a) * (r - k))


def leg(s, hip, foot, col):
    knee = ((hip[0] + foot[0]) / 2 + 2, (hip[1] + foot[1]) / 2)
    line(s, col, hip, knee, 5)
    line(s, col, knee, foot, 4)
    rect(s, BOOT[1] if col == CLOAK[1] else BOOT[0], foot[0] - 2, foot[1] - 2, 7, 4)


def side(bob=0, front=(3, 0), back=(-3, 0), sway=0, scarf=0, hand=(9, 38), lamp=True,
         sword_ang=None, arc=None, crouch=0, lean=0, hood_back=0):
    """One side-view frame. Feet offsets are from the standing spot; hand is the lantern hand."""
    s = surf(48, 64)
    cx, g = 24 + lean, 62
    hip = (24, 46 + bob + crouch)
    # back leg, back cloak, scarf tail
    leg(s, hip, (24 + back[0], g + back[1]), CLOAK[0])
    top = 23 + bob + crouch
    hem = 52 + bob + crouch // 2
    tail = [(cx - 3, top + 2), (cx - 12 - scarf, top + 4 + scarf // 2), (cx - 16 - scarf, top + 9 - scarf // 3),
            (cx - 9, top + 6)]
    poly(s, SCARF[0], tail)
    poly(s, CLOAK[1], [(cx - 6, top), (cx + 7, top), (cx + 10, hem - 2), (cx + 4, hem), (cx - 9 - sway, hem + 1),
                       (cx - 11 - sway, hem - 3)])
    poly(s, CLOAK[0], [(cx - 6, top + 2), (cx - 2, top + 3), (cx - 3, hem), (cx - 9 - sway, hem + 1),
                       (cx - 11 - sway, hem - 3)])
    line(s, CLOAK[2], (cx + 6, top + 2), (cx + 8, hem - 4), 2)
    # front leg
    leg(s, hip, (24 + front[0], g + front[1]), CLOAK[1])
    # belt
    rect(s, "earth1", cx - 6, hip[1] - 9, 13, 2)
    px(s, "light0", cx + 3, hip[1] - 9)
    # hood
    hy = 9 + bob + crouch
    ellipse(s, CLOAK[1], cx - 8 - hood_back, hy, 17, 16)
    poly(s, CLOAK[1], [(cx - 8 - hood_back, hy + 6), (cx - 13 - hood_back, hy + 2), (cx - 6, hy + 2)])
    ellipse(s, CLOAK[2], cx - 5, hy + 1, 9, 4)
    ellipse(s, "ink1", cx + 1, hy + 5, 8, 9)
    px(s, SKIN[1], cx + 7, hy + 10)
    px(s, SKIN[0], cx + 6, hy + 12)
    rect(s, "light1", cx + 5, hy + 8, 2, 1)
    # scarf wrap
    rect(s, SCARF[1], cx - 6, top - 1, 14, 3)
    rect(s, SCARF[0], cx - 6, top + 1, 6, 2)
    # lantern arm (front)
    sh = (cx + 4, top + 5)
    hx, hy2 = cx + hand[0] - 9 + 9, hand[1] + bob + crouch
    line(s, CLOAK[1], sh, (hx, hy2), 4)
    rect(s, SKIN[1], hx - 1, hy2 - 1, 3, 3)
    if lamp:
        lantern(s, hx, hy2 + 1)
    if sword_ang is not None:
        sword(s, cx + 2, top + 10, sword_ang)
    s = outline(s)
    if arc:
        slash(s, cx + 2, top + 10, 22, *arc)
    return s


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
    sh.add("climb", [side(front=(4, -6 * (i % 2)), back=(2, -6 * ((i + 1) % 2)), hand=(8, 18 + 4 * (i % 2)),
                          lean=2, sway=-1) for i in range(4)], 8)
    sh.add("wall_slide", [side(front=(5, -3), back=(1, 0), hand=(4, 26), lean=3, sway=-3, scarf=-2)], 1)
    sh.add("dash", [side(front=(8, -2), back=(-9, -2), sway=8 + k, scarf=9 + k, lean=3, hand=(12, 34), hood_back=2)
                    for k in range(3)], 14, False)
    sh.add("swim", [side(bob=6, front=(8, -10 + 4 * (i % 2)), back=(-9, -10 + 4 * ((i + 1) % 2)), sway=6,
                         scarf=7, lamp=True, hand=(12, 34)) for i in range(4)], 8)
    sh.add("lantern_raise", [side(hand=(8, 30)), side(hand=(7, 20)), side(hand=(6, 8))], 10, False)
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


# --- top-down (32x48): down, up, side (right; the game flips for left) ---------------------
def top(d, step=0, bob=0, sway=0, hand=0, sword_ang=None, arc=None, roll=None, lamp_up=0):
    s = surf(32, 48)
    cx = 16
    if roll is not None:  # a tumbling cloak ball
        y = 26 - [0, 6, 6, 0][roll]
        ellipse(s, CLOAK[1], 6, y, 20, 18)
        ellipse(s, CLOAK[2], 9 + roll * 2 % 8, y + 3, 7, 5)
        rect(s, SCARF[1], 6 + (roll * 5) % 14, y + 8, 6, 3)
        return outline(s)
    feet = (step, -step)
    # feet
    for i, fx in enumerate((-4, 3)):
        if d != "side":
            rect(s, BOOT[1], cx + fx, 42 + bob + (feet[i] if d != "up" else -feet[i]), 4, 4)
        else:
            rect(s, BOOT[i], cx - 2 + feet[i] * 2, 43 + bob, 5, 3)
    # cloak body
    t, h = 20 + bob, 43 + bob
    poly(s, CLOAK[1], [(cx - 7, t), (cx + 7, t), (cx + 10 + sway, h), (cx - 10 + sway, h)])
    poly(s, CLOAK[0], [(cx - 7, t), (cx - 3, t), (cx - 4 + sway, h), (cx - 10 + sway, h)])
    line(s, CLOAK[2], (cx + 5, t + 2), (cx + 8 + sway, h - 2), 1)
    # head / hood
    hy = 5 + bob
    ellipse(s, CLOAK[1], cx - 8, hy, 16, 17)
    ellipse(s, CLOAK[2], cx - 5, hy + 1, 8, 4)
    if d == "down":
        ellipse(s, "ink1", cx - 5, hy + 6, 10, 9)
        rect(s, "light1", cx - 3, hy + 9, 2, 1)
        rect(s, "light1", cx + 1, hy + 9, 2, 1)
        px(s, SKIN[1], cx, hy + 12)
    elif d == "side":
        ellipse(s, "ink1", cx, hy + 5, 8, 9)
        rect(s, "light1", cx + 4, hy + 8, 2, 1)
        px(s, SKIN[1], cx + 7, hy + 11)
    else:
        line(s, CLOAK[0], (cx, hy + 6), (cx, hy + 15), 2)
    # scarf
    rect(s, SCARF[1], cx - 7, 20 + bob, 14, 3)
    if d == "up":
        poly(s, SCARF[0], [(cx - 2, 22 + bob), (cx + 2, 22 + bob), (cx + 1 + sway, 33 + bob), (cx - 2 + sway, 32 + bob)])
    elif d == "side":
        poly(s, SCARF[0], [(cx - 6, 21 + bob), (cx - 12 - sway, 24 + bob), (cx - 10 - sway, 27 + bob)])
    # lantern hand
    if d == "down":
        lx, ly = cx + 10, 30 + bob + hand - lamp_up
    elif d == "side":
        lx, ly = cx + 8, 31 + bob + hand - lamp_up
    else:
        lx, ly = cx - 10, 30 + bob + hand - lamp_up
    rect(s, SKIN[1], lx - 1, ly - 2, 3, 3)
    lantern(s, lx, ly)
    if sword_ang is not None:
        sx, sy = {"down": (cx - 6, 32), "up": (cx + 6, 22), "side": (cx + 4, 30)}[d]
        sword(s, sx, sy + bob, sword_ang, 14)
    s = outline(s)
    if arc:
        sx, sy = {"down": (16, 30), "up": (16, 22), "side": (16, 30)}[d]
        slash(s, sx, sy, 15, *arc)
    return s


ATTACK = {"down": ((-150, 0), 60, 120), "up": ((-30, 0), -60, -120), "side": ((-100, 0), -20, 50)}


def top_sheet():
    sh = Sheet("hero_top", 32, 48, origin=[16, 46])
    for d in ("down", "up", "side"):
        sh.add("idle_" + d, [top(d, bob=b, sway=w) for b, w in ((0, 0), (0, 1), (1, 1), (1, 0))], 4)
    for d in ("down", "up", "side"):
        sh.add("walk_" + d, [top(d, step=st, bob=b, sway=w, hand=hd)
                             for st, b, w, hd in ((2, 0, 1, 0), (0, -1, 0, 1), (-2, 0, -1, 0), (0, -1, 0, 1))], 8)
    for d in ("down", "up", "side"):
        sh.add("roll_" + d, [top(d, roll=k) for k in range(4)], 14, False)
    for d in ("down", "up", "side"):
        pre, a0, a1 = ATTACK[d]
        sh.add("attack_" + d, [top(d, sword_ang=pre[0]), top(d, sword_ang=(a0 + a1) / 2, arc=(a0 - 60, a1)),
                               top(d, sword_ang=a1)], 14, False)
    sh.add("hurt", [flash(top("down")), top("down", sway=-2)], 12, False)
    sh.add("lantern_raise", [top("down", lamp_up=k) for k in (4, 10, 16)], 10, False)
    sh.save()


def main():
    side_sheet()
    top_sheet()


if __name__ == "__main__":
    main()
