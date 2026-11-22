"""The Shadow King, 192x256 (docs/teen/art/ref/shadow_king_concept.jpg): spiked black plate, a jagged iron crown with
a violet gem, a faceless helm with violet eyes, a violet crystal heart and belt gem, a torn violet-black cloak with
rune trim, a jagged black greatsword with a violet gem, a gauntlet trailing violet wisps, a soft violet aura.
Ink + the shadow ramp only; violet is the brightest thing on him. Never gory. Original art. Also a 160x200 portrait."""
import math
import random

from sfart import Sheet, circle, ellipse, flash, line, outline, poly, px, rect, save_png, surf

W, H = 192, 256
PLATE = ("ink0", "ink1", "ink2", "ink3", "ink4")   # black steel: deep .. edge glint
CLOAK = ("ink0", "shadow0", "shadow1")
VIOLET = ("shadow1", "shadow2")


def gem(s, x, y, w, h, spark=True):
    """A violet crystal (diamond), lit from the top left."""
    poly(s, "shadow0", [(x, y - h // 2 - 1), (x + w // 2 + 1, y), (x, y + h // 2 + 1), (x - w // 2 - 1, y)])
    poly(s, VIOLET[0], [(x, y - h // 2), (x + w // 2, y), (x, y + h // 2), (x - w // 2, y)])
    poly(s, VIOLET[1], [(x, y - h // 2), (x, y + h // 4), (x - w // 2 + 1, y)])
    if spark:
        px(s, "ink7", x - 1, y - h // 4)


def torn(x0, x1, y, n, depth, seed):
    rnd = random.Random(seed)
    pts = []
    for k in range(n + 1):
        pts.append((x0 + (x1 - x0) * k / n, y + (depth if k % 2 else rnd.randint(0, depth // 2)) + rnd.randint(-2, 2)))
    return pts


def runes(s, a, b, step=5):
    """A rune-trim band: a stitched violet line with small glyph marks along a cloak edge."""
    n = max(1, int(math.dist(a, b) / step))
    for k in range(n + 1):
        x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
        px(s, VIOLET[0], x, y)
        if k % 2:
            px(s, VIOLET[0], x + 1, y - 1)
            px(s, "ink3", x - 1, y + 1)


def spike(s, base, ang, length, w, col=PLATE[1], hi=PLATE[3]):
    a = math.radians(ang)
    nx, ny = -math.sin(a) * w, math.cos(a) * w
    tip = (base[0] + math.cos(a) * length, base[1] + math.sin(a) * length)
    poly(s, col, [(base[0] - nx, base[1] - ny), tip, (base[0] + nx, base[1] + ny)])
    line(s, hi, (base[0] - nx * 0.5, base[1] - ny * 0.5), tip)


def pauldron(s, x, y, side):
    """A huge spiked shoulder plate, three layers, three blades sweeping up and out."""
    ellipse(s, PLATE[1], x - 20, y - 12, 40, 30)
    ellipse(s, PLATE[2], x - 17, y - 11, 34, 20)
    ellipse(s, PLATE[1], x - 16, y - 4, 32, 14)
    line(s, PLATE[3], (x - 12, y - 9), (x + 10, y - 9))
    for k in range(2):
        poly(s, PLATE[1], [(x - 18 + k * 2, y + 8 + k * 7), (x + 18 - k * 2, y + 8 + k * 7),
                           (x + 15 - k * 2, y + 14 + k * 7), (x - 15 + k * 2, y + 14 + k * 7)])
        line(s, PLATE[3], (x - 15 + k * 2, y + 9 + k * 7), (x + 15 - k * 2, y + 9 + k * 7))
    for k, (sx, sp) in enumerate(((-6, 75), (4, 52), (12, 28))):
        spike(s, (x + side * sx, y - 8 + k * 2), -90 + side * sp, 26 - k * 4, 4, PLATE[2], PLATE[4])
    circle(s, PLATE[3], x + side * 9, y + 2, 3)
    circle(s, PLATE[1], x + side * 9, y + 2, 1)


def limb(s, a, b, w):
    line(s, PLATE[1], a, b, w)
    line(s, PLATE[2], a, b, w - 4)
    circle(s, PLATE[1], b[0], b[1], w // 2)
    line(s, PLATE[3], (a[0] - w // 3, a[1]), (b[0] - w // 3, b[1]))


def greatsword(s, hand, ang, length=118):
    """Jagged black greatsword: serrated blade, violet fuller, spiked crossguard with a violet gem."""
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    g = (hand[0] + dx * 10, hand[1] + dy * 10)          # guard
    tip = (hand[0] + dx * length, hand[1] + dy * length)
    pts_l, pts_r = [], []
    n = 7
    for k in range(n + 1):
        t = k / n
        w = 7 - 3 * t + (2 if k % 2 else 0)
        bx, by = g[0] + (tip[0] - g[0]) * t * 0.9, g[1] + (tip[1] - g[1]) * t * 0.9
        pts_l.append((bx + nx * w, by + ny * w))
        pts_r.append((bx - nx * (w - 1), by - ny * (w - 1)))
    poly(s, PLATE[1], pts_l + [tip] + pts_r[::-1])
    line(s, PLATE[3], pts_l[0], tip)
    line(s, VIOLET[0], (g[0] + dx * 8, g[1] + dy * 8), (g[0] + dx * (length - 34), g[1] + dy * (length - 34)), 2)
    # crossguard: two hooked spikes, gem in the middle
    for sd in (-1, 1):
        q = (g[0] + nx * sd * 15 - dx * 4, g[1] + ny * sd * 15 - dy * 4)
        poly(s, PLATE[2], [(g[0] - nx * sd * 2, g[1] - ny * sd * 2), q, (g[0] + dx * 4, g[1] + dy * 4)])
        line(s, PLATE[3], g, q)
    gem(s, g[0], g[1], 7, 9)
    line(s, PLATE[0], (hand[0] - dx * 12, hand[1] - dy * 12), hand, 4)        # grip
    circle(s, PLATE[2], hand[0] - dx * 14, hand[1] - dy * 14, 3)               # pommel
    return tip


def wisps(s, x, y, k, n=5, seed=0, scale=1.0):
    """Violet shadow-flame curling up off a hand."""
    rnd = random.Random(seed)
    for i in range(n):
        h = (10 + rnd.randint(0, 14)) * scale
        ox = rnd.randint(-8, 8) * scale
        for j in range(int(h)):
            t = j / max(1, h)
            wx = x + ox + math.sin(t * 5 + k + i) * 3 * scale
            col = VIOLET[1] if t < 0.3 else VIOLET[0] if t < 0.7 else "shadow0"
            px(s, col, wx, y - j)
            if t < 0.5:
                px(s, VIOLET[0], wx + 1, y - j)


def aura(s, cx, cy, r, seed=0):
    """Soft violet aura behind him: a sparse dither disc on clear pixels only."""
    for y in range(max(0, cy - r), min(H, cy + r)):
        for x in range(max(0, cx - r), min(W, cx + r)):
            d = math.hypot(x - cx, (y - cy) * 0.8)
            hsh = ((x * 73856093) ^ (y * 19349663) ^ seed) % 97
            if d < r and s.get_at((x, y)).a == 0 and hsh < (14 if d > r * 0.75 else 6):
                px(s, "shadow0", x, y)


def king(t=0.0, lift=0, arms=0.45, orb=1.0, eyes=True, blade=None, crown_glow=False, motes=0, seed=0):
    """t: sway phase; arms 0 (gauntlet low) .. 1 (raised high); orb: size of the violet flame in the gauntlet;
    blade: the greatsword's angle (degrees, 0 = right, 90 = down; default held low across the body)."""
    s = surf(W, H)
    cx, top = 96, 26 - lift
    sway = math.sin(t) * 3
    hem = 244 - lift
    # the cloak behind: torn, flaring wide, violet lining
    edge = torn(cx - 78 - sway, cx + 78 + sway, hem - 18, 12, 16, seed=int(t * 10) + 1)
    poly(s, CLOAK[1], [(cx - 30, top + 40), (cx + 30, top + 40), (cx + 70 + sway, top + 120)] + edge[::-1] +
         [(cx - 72 - sway, top + 110)])
    poly(s, CLOAK[0], [(cx - 30, top + 60), (cx - 26, top + 150), (cx - 44 - sway, hem - 20), (cx - 56 - sway, top + 120)])
    for x in (-58, 52):
        line(s, CLOAK[2], (cx + x * 0.8, top + 110), (cx + x + sway * (1 if x > 0 else -1), hem - 16))
    for x in (-44, 40):
        line(s, CLOAK[0], (cx + x * 0.8, top + 90), (cx + x * 1.1, hem - 10), 2)
    runes(s, (cx + 34, top + 46), (cx + 72 + sway, top + 122))
    runes(s, (cx - 34, top + 46), (cx - 74 - sway, top + 112))
    runes(s, (cx + 72 + sway, top + 126), (cx + 74 + sway, hem - 22))
    # legs: armored greaves and sabatons
    for sd in (-1, 1):
        x0 = cx + sd * 18
        poly(s, PLATE[1], [(x0 - 12, top + 124), (x0 + 12, top + 124), (x0 + 9, top + 152), (x0 - 9, top + 152)])
        for k in range(3):                                   # tasset lames
            line(s, PLATE[3], (x0 - 11 + k, top + 128 + k * 8), (x0 + 11 - k, top + 128 + k * 8))
        rect(s, PLATE[1], x0 - 8, top + 150, 16, hem - top - 162)
        rect(s, PLATE[2], x0 - 6, top + 152, 12, hem - top - 166)
        rect(s, PLATE[3], x0 - 6, top + 166, 10, 8)
        spike(s, (x0, top + 170), -90, 7, 3)
        line(s, PLATE[4], (x0 - 5, top + 180), (x0 - 5, hem - 16))
        poly(s, PLATE[1], [(x0 - 9, hem - 14), (x0 + 9, hem - 14), (x0 + 12 * sd + (0 if sd > 0 else 0), hem - 4),
                           (x0 - 9, hem - 4)])
    # tabard: torn violet-black strips between the legs
    poly(s, CLOAK[1], [(cx - 10, top + 124), (cx + 10, top + 124)] + torn(cx + 11, cx - 11, top + 192, 3, 10, seed=3))
    line(s, CLOAK[2], (cx - 2, top + 128), (cx - 3, top + 194))
    runes(s, (cx - 9, top + 130), (cx - 10, top + 186))
    runes(s, (cx + 9, top + 130), (cx + 10, top + 186))
    # torso: layered black plate, chevron ribs, crystal heart, belt with a gem
    poly(s, PLATE[1], [(cx - 28, top + 52), (cx + 28, top + 52), (cx + 24, top + 104), (cx + 16, top + 122),
                       (cx - 16, top + 122), (cx - 24, top + 104)])
    poly(s, PLATE[2], [(cx - 22, top + 54), (cx + 22, top + 54), (cx + 14, top + 88), (cx - 14, top + 88)])
    for k in range(4):
        y = top + 92 + k * 7
        line(s, PLATE[3], (cx - 18 + k, y), (cx, y + 5), 1)
        line(s, PLATE[3], (cx, y + 5), (cx + 18 - k, y), 1)
    for a in (-150, -30, 200, 20, 90):                     # cracks of light from the heart
        r = math.radians(a)
        line(s, VIOLET[0], (cx, top + 72), (cx + math.cos(r) * 14, top + 72 + math.sin(r) * 11))
    gem(s, cx, top + 72, 12, 16)
    rect(s, PLATE[2], cx - 20, top + 118, 40, 8)
    runes(s, (cx - 18, top + 122), (cx + 18, top + 122), 4)
    gem(s, cx, top + 122, 8, 10)
    # pauldrons
    pauldron(s, cx - 34, top + 54, -1)
    pauldron(s, cx + 34, top + 54, 1)
    # head: hood shadow, faceless helm, violet eyes, jagged crown with a violet gem
    ellipse(s, CLOAK[1], cx - 20, top + 14, 40, 44)
    ellipse(s, PLATE[1], cx - 15, top + 14, 30, 38)
    poly(s, PLATE[1], [(cx - 15, top + 34), (cx + 15, top + 34), (cx + 8, top + 54), (cx, top + 58), (cx - 8, top + 54)])
    line(s, PLATE[3], (cx - 10, top + 18), (cx - 13, top + 40))
    poly(s, PLATE[0], [(cx - 10, top + 28), (cx + 10, top + 28), (cx + 6, top + 50), (cx, top + 54), (cx - 6, top + 50)])
    line(s, PLATE[2], (cx, top + 16), (cx, top + 27), 2)
    for dx, hgt, w in ((-15, 14, 3), (-10, 20, 3), (-5, 16, 2), (0, 30, 4), (5, 16, 2), (10, 20, 3), (15, 14, 3)):
        spike(s, (cx + dx, top + 20), -90 + dx * 1.6, hgt, w, PLATE[2], PLATE[4] if dx == 0 else PLATE[3])
    rect(s, PLATE[2], cx - 17, top + 17, 34, 5)
    line(s, PLATE[3], (cx - 16, top + 17), (cx + 16, top + 17))
    gem(s, cx, top + 21, 6, 8, spark=crown_glow)
    if eyes:
        for sd in (-1, 1):
            ex = cx + sd * 5
            poly(s, VIOLET[1], [(ex - 3 * sd, top + 33), (ex + 4 * sd, top + 35), (ex + 3 * sd, top + 38), (ex - 3 * sd, top + 36)])
            px(s, "ink7" if crown_glow else "ink6", ex, top + 35)
    # the sword arm (his right, our left), the greatsword low across the body
    sh_r = (cx - 38, top + 66)
    ang = 115 if blade is None else blade
    hand_r = (cx - 40 + math.cos(math.radians(ang - 30)) * 16, top + 112 + math.sin(math.radians(ang - 30)) * 10)
    el_r = (sh_r[0] - 8, (sh_r[1] + hand_r[1]) / 2)
    limb(s, sh_r, el_r, 13)
    limb(s, el_r, hand_r, 12)
    greatsword(s, hand_r, ang, 92 if ang < -90 else 118)
    circle(s, PLATE[2], hand_r[0], hand_r[1], 6)
    # the gauntlet arm (his left, our right), raised, violet wisps off the fingers
    sh_l = (cx + 40, top + 66)
    el_l = (cx + 56, top + 92 - arms * 26)
    hand_l = (cx + 60, top + 84 - arms * 76)
    limb(s, sh_l, el_l, 13)
    limb(s, el_l, hand_l, 12)
    spike(s, el_l, 20, 9, 3)
    ellipse(s, PLATE[1], hand_l[0] - 7, hand_l[1] - 8, 14, 14)
    for k in range(4):                                     # clawed fingers
        line(s, PLATE[2], (hand_l[0] - 5 + k * 3, hand_l[1] - 6), (hand_l[0] - 6 + k * 3.5, hand_l[1] - 13), 2)
    line(s, PLATE[3], (hand_l[0] - 5, hand_l[1] - 6), (hand_l[0] + 5, hand_l[1] - 6))
    s = outline(s)
    wisps(s, hand_l[0], hand_l[1] - 14, t * 3, n=4 + int(orb * 2), seed=seed, scale=min(1.8, orb))
    if orb > 1.2:
        circle(s, "shadow0", hand_l[0], hand_l[1] - 20 - orb * 4, 4 + orb * 3)
        circle(s, VIOLET[0], hand_l[0], hand_l[1] - 20 - orb * 4, 2 + orb * 2.5)
        circle(s, VIOLET[1], hand_l[0] - 1, hand_l[1] - 21 - orb * 4, 1 + orb)
    aura(s, cx, top + 100, 92, seed)
    rnd = random.Random(seed)                              # motes of shadow rising
    for i in range(10 + motes):
        x = cx + rnd.randint(-80, 80)
        y = (rnd.randint(20, 230) - lift - int(t * 9)) % 230 + 10
        if s.get_at((x, y)).a == 0 or s.get_at((x, y))[:3] == (42, 15, 61):
            px(s, rnd.choice((VIOLET[0], VIOLET[1], "ink3")), x, y)
    return s


def dissolve(s, k, n):
    """Fade-out frame: pixels drop away in a stable pattern and become violet motes (no alpha)."""
    out = s.copy()
    rnd = random.Random(3)
    keep = 1 - (k + 1) / n
    for y in range(H):
        for x in range(W):
            if rnd.random() > keep and out.get_at((x, y)).a:
                out.set_at((x, y), (0, 0, 0, 0))
                if rnd.random() < 0.04:
                    px(out, VIOLET[0] if rnd.random() < 0.5 else "ink3", x, max(0, y - k * 6))
    return out


def sheet():
    sh = Sheet("shadow_king", W, H, origin=[96, 250])
    sh.add("idle", [king(t=i * 1.57, seed=i) for i in range(4)], 4)
    sh.add("float", [king(t=i * 1.57, lift=round(4 + math.sin(i * 1.57) * 4), seed=i + 4) for i in range(4)], 6)
    sh.add("cast", [king(arms=a, orb=o, crown_glow=g, seed=i + 8)
                    for i, (a, o, g) in enumerate(((0.3, 1, 0), (0.55, 1.3, 0), (0.8, 1.6, 0), (1, 2, 1), (1, 2.3, 1), (0.5, 1, 0)))],
           10, False)
    sh.add("summon", [king(arms=0.6 + 0.4 * math.sin(i), orb=1 + i * 0.2, motes=i * 6, seed=i + 14) for i in range(6)], 10, False)
    sh.add("blade", [king(blade=-120, arms=0.2, seed=20), king(blade=-40, arms=0.2, seed=21),
                     king(blade=40, arms=0.3, seed=22), king(blade=80, arms=0.3, seed=23)], 10, False)
    sh.add("hurt", [flash(king(), "ink7"), king(t=1, lift=-2)], 12, False)
    base = king()
    sh.add("fade_out", [dissolve(base, k, 8) for k in range(8)], 8, False)
    sh.save()


def portrait():
    """160x200 bust for the boss intro: crown, faceless helm, violet eyes, spiked pauldrons, the crystal heart."""
    global W, H
    W, H = 160, 200
    s = surf(W, H)
    cx = 80
    # hood and cloak behind, violet lining
    poly(s, CLOAK[1], [(26, 110), (134, 110), (158, 200), (2, 200)])
    for x0, x1 in ((30, 10), (130, 150)):
        line(s, CLOAK[2], (x0, 120), (x1, 198))
    runes(s, (24, 116), (4, 196))
    runes(s, (136, 116), (156, 196))
    ellipse(s, CLOAK[1], 38, 30, 84, 96)
    ellipse(s, CLOAK[0], 44, 40, 72, 80)
    # chest plate, chevrons, the crystal heart with cracks of light
    poly(s, PLATE[1], [(36, 132), (124, 132), (118, 200), (42, 200)])
    poly(s, PLATE[2], [(46, 136), (114, 136), (104, 172), (56, 172)])
    for k in range(3):
        y = 178 + k * 7
        line(s, PLATE[3], (48 + k, y), (cx, y + 6))
        line(s, PLATE[3], (cx, y + 6), (112 - k, y))
    for a in (-150, -30, 200, -20, 160, 90, -90):
        r = math.radians(a)
        line(s, VIOLET[0], (cx, 158), (cx + math.cos(r) * 26, 158 + math.sin(r) * 18))
    gem(s, cx, 158, 20, 28)
    # gorget and the helm: faceless, a T of black, violet eyes
    poly(s, PLATE[1], [(56, 112), (104, 112), (112, 136), (48, 136)])
    for k in range(2):
        line(s, PLATE[3], (54 - k * 2, 120 + k * 8), (106 + k * 2, 120 + k * 8))
    ellipse(s, PLATE[1], 52, 40, 56, 72)
    poly(s, PLATE[1], [(52, 80), (108, 80), (96, 118), (cx, 126), (64, 118)])
    ellipse(s, PLATE[2], 56, 44, 22, 50)
    line(s, PLATE[4], (60, 50), (56, 84))
    line(s, PLATE[3], (cx, 46), (cx, 66), 3)
    poly(s, PLATE[0], [(60, 68), (100, 68), (100, 76), (86, 80), (88, 112), (cx, 120), (72, 112), (74, 80), (60, 76)])
    for sd in (-1, 1):
        ex = cx + sd * 11
        poly(s, VIOLET[0], [(ex - 7 * sd, 69), (ex + 9 * sd, 72), (ex + 7 * sd, 78), (ex - 7 * sd, 75)])
        poly(s, VIOLET[1], [(ex - 5 * sd, 70), (ex + 6 * sd, 72), (ex + 5 * sd, 76), (ex - 5 * sd, 74)])
        rect(s, "ink7", ex - (2 if sd > 0 else 1), 72, 3, 2)
    # the crown: a band and jagged iron spikes, a violet gem at the brow
    for dx, hgt, w in ((-28, 22, 4), (-19, 36, 5), (-10, 28, 4), (0, 56, 6), (10, 28, 4), (19, 36, 5), (28, 22, 4)):
        spike(s, (cx + dx, 46), -90 + dx * 0.9, hgt, w, PLATE[2], PLATE[4] if dx == 0 else PLATE[3])
        if abs(dx) == 19:
            spike(s, (cx + dx + (4 if dx > 0 else -4), 30), -90 + dx * 2.5, 10, 2, PLATE[2], PLATE[3])
    rect(s, PLATE[2], cx - 32, 42, 64, 9)
    line(s, PLATE[3], (cx - 31, 42), (cx + 31, 42))
    line(s, PLATE[1], (cx - 31, 50), (cx + 31, 50))
    gem(s, cx, 47, 10, 14)
    # spiked pauldrons at the edges
    for sd in (-1, 1):
        px0 = cx + sd * 56
        ellipse(s, PLATE[1], px0 - 30, 112, 60, 44)
        ellipse(s, PLATE[2], px0 - 26, 114, 52, 28)
        line(s, PLATE[3], (px0 - 20, 118), (px0 + 20, 118))
        for k in range(2):
            line(s, PLATE[3], (px0 - 26 + k * 3, 146 + k * 10), (px0 + 26 - k * 3, 146 + k * 10))
            line(s, PLATE[1], (px0 - 26 + k * 3, 152 + k * 10), (px0 + 26 - k * 3, 152 + k * 10), 2)
        for k, (sx, sp, ln) in enumerate(((-14, 62, 34), (0, 40, 30), (12, 20, 22))):
            spike(s, (px0 + sd * sx, 116 + k * 2), -90 + sd * sp, ln, 6, PLATE[2], PLATE[4])
        circle(s, PLATE[3], px0 + sd * 12, 130, 5)
        circle(s, PLATE[1], px0 + sd * 12, 130, 2)
    s = outline(s)
    wisps(s, 148, 108, 1.0, n=6, seed=5, scale=1.6)
    wisps(s, 12, 112, 2.0, n=4, seed=9, scale=1.2)
    aura(s, cx, 100, 84, 2)
    W, H = 192, 256
    return s


def main():
    sheet()
    save_png(portrait(), "ui/shadow_king_portrait.png")


if __name__ == "__main__":
    main()
