"""Shadowfall monster sheets (all original, drawn by code). Run: python make_monsters.py
One sheet per monster: move 4 (8 fps), attack 3 (10 fps), hurt 2 (12 fps), poof 4 (10 fps).
Sizes are doubled for the 32-px tile: small 32, big 64, mini-boss 96. Facing right, origin bottom-centre.
Every body is a silhouette drawn in one colour, then auto-shaded 3 steps (light top-left) by shade()."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfart import *  # noqa: E402,F401,F403

sin, cos, pi = math.sin, math.cos, math.pi
W = "ink7"  # scratch colour for silhouettes
CELL = [32]  # width of the cell being drawn (sets shade() thickness; the canvas is padded)


# --- helpers -------------------------------------------------------------------------------
def shade(t, cols, d=None, dl=None):
    """Recolour a silhouette: shadow on its lower-right edge, light on its upper-left edge."""
    w, h = t.get_size()
    d = d or max(1, CELL[0] // 32)
    dl = dl or max(1, CELL[0] // 48)
    m = pygame.mask.from_surface(t, 1)

    def g(x, y):
        return 0 <= x < w and 0 <= y < h and m.get_at((x, y))
    out = surf(w, h)
    for y in range(h):
        for x in range(w):
            if m.get_at((x, y)):
                k = 0 if not g(x + d, y + d) else 2 if not g(x - dl, y - dl) else 1
                out.set_at((x, y), c(cols[k]))
    return out


def part(s, cols, fn, **kw):
    t = surf(*s.get_size())
    fn(t)
    s.blit(shade(t, cols, **kw), (0, 0))


def over(s, fn):
    """Draw fn only where s is already filled (stripes, moss, cracks)."""
    t = surf(*s.get_size())
    fn(t)
    m = pygame.mask.from_surface(s, 1)
    for y in range(s.get_height()):
        for x in range(s.get_width()):
            p = t.get_at((x, y))
            if p.a and m.get_at((x, y)):
                s.set_at((x, y), p)


def limb(t, a, b, w, col=W):
    r = max(1, (w - 1) // 2)
    line(t, col, a, b, max(1, round(w)))
    circle(t, col, a[0], a[1], r)
    circle(t, col, b[0], b[1], r)


def chain(t, pts, rs, col=W):
    for (x, y), r in zip(pts, rs):
        circle(t, col, x, y, r)
    for i in range(len(pts) - 1):
        line(t, col, pts[i], pts[i + 1], max(1, round(rs[i] + rs[i + 1])))


def rock(t, cx, cy, w, h, seed=0, n=9, col=W):
    r = random.Random(seed)
    poly(t, col, [(cx + cos(2 * pi * i / n) * w / 2 * r.uniform(.78, 1),
                   cy + sin(2 * pi * i / n) * h / 2 * r.uniform(.78, 1)) for i in range(n)])


def jaws(s, hx, hy, L, T, o, cols, inner="ink0", teeth="ink7", gap=7, nt=3, tw=2, tl=3):
    """Side-view jaws facing right; o = how open (0..1)."""
    g = round(o * gap)
    if g:
        poly(s, inner, [(hx, hy - 1), (hx + L, hy - 1), (hx + L - 2, hy + g + 1), (hx, hy + g + 1)])
    part(s, cols, lambda t: ellipse(t, W, hx - 3, hy + g, L + 3, max(2, T * .8)))
    part(s, cols, lambda t: ellipse(t, W, hx - 4, hy - T, L + 4, T + 1))
    if o > .4:
        for j in range(nt):
            x = hx + 2 + j * (L - 3) // nt
            poly(s, teeth, [(x, hy), (x + tw, hy), (x + tw / 2, hy + tl)])
            poly(s, teeth, [(x + 1, hy + g), (x + 1 + tw, hy + g), (x + 1 + tw / 2, hy + g - tl)])
    else:
        line(s, "ink0", (hx + 2, hy + 1), (hx + L - 2, hy + 1))


def build(name, w, h, fn, seed=1):
    """Draw every frame on a canvas padded left, right and above, then shift the whole monster (one offset for all
    frames, so it never jitters) to keep it inside the 1-px outline margin, and crop."""
    P = w // 4
    keys = [(k * pi / 2, None) for k in range(4)] + [(.6, i) for i in range(3)]
    raw = {}
    CELL[0] = w
    OFF[:] = [P, P]
    for ph, st in keys:
        raw[ph, st] = surf(w + 2 * P, h + P + 2)
        fn(raw[ph, st], ph, st)
        pygame.draw.rect(raw[ph, st], (0, 0, 0, 0), (0, P + h, w + 2 * P, 2))  # the ground hides what sinks below it
    OFF[:] = [0, 0]
    box = raw[keys[0]].get_bounding_rect()
    for t in raw.values():
        box.union_ip(t.get_bounding_rect())

    def fit(lo, hi, n):  # content spans [lo, hi) on the canvas; the cell's inside is [P+1, P+n-1)
        if lo < P + 1 and hi <= P + n - 1:
            return min(P + 1 - lo, P + n - 1 - hi)
        if hi > P + n - 1 and lo >= P + 1:
            return -min(hi - (P + n - 1), lo - (P + 1))
        return 0
    sx, sy = fit(box.left, box.right, w), fit(box.top, box.bottom, h)

    def fr(ph, st=None):
        s = raw[ph, st].subsurface((P - sx, P - sy, w, h)).copy()
        n0 = pygame.mask.from_surface(s, 1).count()
        if n0 != pygame.mask.from_surface(raw[ph, st], 1).count():
            print(f"  note: {name} st={st} ph={ph:.1f} too big for the cell")
        for r in ((0, 0, w, 1), (0, h - 1, w, 1), (0, 0, 1, h), (w - 1, 0, 1, h)):
            pygame.draw.rect(s, (0, 0, 0, 0), r)
        if pygame.mask.from_surface(s, 1).count() != n0:
            print(f"  note: {name} st={st} ph={ph:.1f} clipped at the margin")
        return outline(s)
    mv = [fr(k * pi / 2) for k in range(4)]
    sh = Sheet(name, w, h)
    sh.add("move", mv, 8)
    sh.add("attack", [fr(.6, i) for i in range(3)], 10, False)  # keys above must match
    sh.add("hurt", [flash(mv[0]), mv[0]], 12, False)
    sh.add("poof", [poof(w, h, k, 4, seed) for k in range(4)], 10, False)
    sh.save()
    return mv


# --- map monsters -------------------------------------------------------------------------
def thornling(s, ph, st):
    lean = (-1, 1, 1)[st] if st is not None else 0
    cy = 15 + (1 if st in (0, 1) else 0) - (round(abs(sin(ph))) if st is None else 0)
    sw = round(sin(ph) * 3) if st is None else 0
    for i, hx in enumerate((12, 20)):
        o = sw * (1 - 2 * i)
        fy = 30 if o <= 0 else 28
        part(s, ("earth1", "earth2", "earth3"),
             lambda t, hx=hx, o=o, fy=fy: limb(t, (hx + lean // 2, cy + 6), (hx + o + lean // 2, fy), 3))
    cx = 16 + lean
    for a in range(10, 360, 36):
        if 240 < a < 300:
            continue
        r = math.radians(a)
        ln = 6 if st == 1 else 5
        nx, ny = -sin(r), -cos(r)
        p = (cx + cos(r) * 8, cy - sin(r) * 8)
        tip = (cx + cos(r) * (8 + ln), cy - sin(r) * (8 + ln))
        poly(s, "earth4" if a < 200 else "earth2", [(p[0] + nx * 2, p[1] + ny * 2), (p[0] - nx * 2, p[1] - ny * 2), tip])
    part(s, ("moss1", "moss2", "moss3"), lambda t: [circle(t, W, cx + dx, cy + dy, r) for dx, dy, r in
         ((-6, 1, 6), (0, -4, 7), (5, 0, 6), (-1, 4, 6), (-7, -3, 4))])
    rect(s, "ember3", cx + 2, cy - 3, 2, 2)
    rect(s, "ember3", cx + 6, cy - 3, 2, 2)
    if st == 1:
        rect(s, "ink0", cx + 2, cy + 2, 7, 4)
        for x, y in ((3, 2), (6, 2), (4, 5), (7, 5)):
            px(s, "earth4", cx + x, cy + y)
    else:
        line(s, "ink0", (cx + 2, cy + 3), (cx + 8, cy + 3))


def barrow_wight(s, ph, st):
    bob = round(sin(ph)) if st is None else 0
    ln = (-2, 2, 1)[st] if st is not None else 0
    pts = [(16 + ln, 3 + bob), (23 + ln, 9 + bob), (26, 27 + bob)]
    for i in range(6, -1, -1):
        pts.append((6 + i * 3.3, 26 + bob + round(2 * sin(ph + i * 1.3))))
    pts.append((9 + ln, 9 + bob))
    cl = ("ink2", "ink3", "ink4")
    part(s, cl, lambda t: (poly(t, W, pts), circle(t, W, 16 + ln, 10 + bob, 7)))
    ellipse(s, "ink0", 16 + ln, 7 + bob, 8, 9)
    rect(s, "shadow2", 18 + ln, 10 + bob, 2, 1)
    rect(s, "shadow2", 21 + ln, 10 + bob, 2, 1)
    hand = ((17, 17), (30, 17), (27, 20))[st] if st is not None else (23, 19 + round(sin(ph)))
    part(s, cl, lambda t: limb(t, (19 + ln, 15 + bob), (hand[0], hand[1] + bob), 3))
    for dy in (-2, 0, 2):
        line(s, "ink6", (hand[0], hand[1] + bob + dy // 2), (hand[0] + 2, hand[1] + bob + dy), 1)


def mere_lurker(s, ph, st):
    step = (2.7, 3.3, 3.0)[st] if st is not None else 2.9
    amp = 7 if st == 0 else 5
    o = (0, 1, .5)[st] if st is not None else .2 + .2 * (sin(ph) > 0)
    sp = []
    for i in range(14):
        sp.append((9 + i * step, 40 + amp * sin(ph + i * .55) * (1 - i / 14 * .7) - (3 if st == 1 else 0)))
    rs = [2 + min(i, 9) * .7 for i in range(14)]
    rs[10:] = [8.5, 8.5, 8.5, 8.5]
    ts = rs[:]
    fin = "shadow1"
    for i in range(3, 12):
        x, y = sp[i]
        poly(s, fin, [(x - 3, y - rs[i] + 1), (x + 1, y - rs[i] - 6), (x + 4, y - rs[i] + 1)])
    x0, y0 = sp[0]
    poly(s, fin, [(x0 + 2, y0), (x0 - 6, y0 - 9), (x0 - 4, y0), (x0 - 6, y0 + 9)])
    part(s, ("water1", "water2", "water3"), lambda t: chain(t, sp[:13], ts[:13]))
    hx, hy = sp[13]
    jaws(s, hx + 1, hy, 10, 7, o, ("water1", "water2", "water3"), gap=8)
    circle(s, "light0", hx + 1, hy - 5, 2)
    px(s, "ink0", hx + 2, hy - 5)


def quad(s, ph, st, K):
    hnd = K.get("hound")
    th = K["th"]
    c0 = 3 if st == 0 else 0
    b = 0 if st is not None else -round(abs(cos(ph)))
    hd = (-3, 4, 1)[st] if st is not None else 0
    by = 26 + c0 + b
    hx, hy = 48 + hd, by + 2 + (2 if st == 0 else 0)
    far, near = K["far"], K["body"]

    def leg(i, hip, isfar, po):
        p = ph + po
        fwd = 0 if st is None else (4 if st == 1 and hip > 30 else 0)
        sx = round(sin(p) * 7) if st is None else 0
        lift = round(max(0, cos(p)) * 6) if st is None else 0
        fx, fy = hip + sx + fwd, 59 - lift
        kx = (hip + fx) / 2 + (-2 if hip > 30 else 3)
        ky = (by + th + 59 - lift) / 2 + 1
        a = (hip, by + th - 4)
        part(s, far if isfar else near, lambda t: (limb(t, a, (kx, ky), 6 if not hnd else 5),
             limb(t, (kx, ky), (fx, fy - 1), 4 if not hnd else 3), ellipse(t, W, fx - 3, fy - 2, 8, 4)))
    for hip, isfar, po in ((18, 1, 0), (42, 1, pi)):
        leg(0, hip, isfar, po)
    # tail
    tp = [(14 - i * 1.3, by + 4 + i * (1.3 if hnd else .6) + sin(ph + i * .6) * 2) for i in range(6)]
    tr = [3 - i * .4 for i in range(6)] if hnd else [2.5 + i * .5 for i in range(6)]
    part(s, far, lambda t: chain(t, tp, tr))
    # ridge / mane
    for x in range(20, 46, 5 if hnd else 6):
        sz = 6 if hnd else 5
        poly(s, K["mane"][0], [(x, by + 4), (x + 2, by - sz + (0 if hnd else 1)), (x + 5, by + 4)])
    part(s, near, lambda t: (ellipse(t, W, 13, by, 33, th), ellipse(t, W, 33, by - 2, 15, th + 3),
                             ellipse(t, W, 11, by + 1, 14, th)))
    if hnd:
        for x in range(21, 45, 6):
            poly(s, K["mane"][1], [(x, by + 2), (x + 2, by - 4), (x + 4, by + 2)])
    # neck + head
    part(s, near, lambda t: limb(t, (40, by + th / 2), (hx, hy), th - 2))
    if hnd:
        poly(s, K["mane"][0], [(hx - 4, hy - 4), (hx - 17, hy - 11), (hx - 14, hy - 8), (hx - 18, hy - 4), (hx - 2, hy - 1)])
    else:
        poly(s, far[1], [(hx - 1, hy - 5), (hx + 1, hy - 12), (hx + 4, hy - 5)])
    part(s, near, lambda t: ellipse(t, W, hx - 7, hy - 6, 14, 12))
    o = (0, 1, .5)[st] if st is not None else 0
    jaws(s, hx + 2, hy + 1, 10, 5, o, near, teeth=K["teeth"], gap=6, tw=1, tl=3)
    if not hnd:
        poly(s, near[1], [(hx - 6, hy - 4), (hx - 3, hy - 13), (hx + 0, hy - 5)])
        poly(s, near[2], [(hx - 5, hy - 5), (hx - 3, hy - 11), (hx - 2, hy - 5)])
    rect(s, K["eye"], hx + 1, hy - 3, 3, 2)
    for hip, isfar, po in ((22, 0, pi), (46, 0, 0)):
        leg(0, hip, isfar, po)
    if hnd:
        for i in range(4):
            circle(s, "shadow1", 22 + i * 7 + 2 * sin(ph + i), by - 5 - 2 * ((i + round(ph)) % 2), 2)
        circle(s, "shadow1", tp[-1][0] - 1, tp[-1][1] - 2, 3)


WOLF = dict(body=("ink4", "ink5", "ink6"), far=("ink3", "ink4", "ink5"), mane=("ink7", "ink7"),
            eye="water4", teeth="ink7", th=17)
HOUND = dict(body=("shadow0", "shadow1", "shadow2"), far=("shadow0", "shadow0", "shadow1"),
             mane=("shadow1", "shadow2"), eye="light1", teeth="ink6", th=13, hound=1)


def frost_wolf(s, ph, st):
    quad(s, ph, st, WOLF)


def umbral_hound(s, ph, st):
    quad(s, ph, st, HOUND)


def ash_scarab(s, ph, st):
    """Horned ash beetle: domed shell with a glowing seam, pronotum plate, rhino horn, 6 jointed legs."""
    dx = (-2, 1, 0)[st] if st is not None else 0
    bob = -round(abs(sin(ph))) if st is None else 0
    tilt = (3, -2, 0)[st] if st is not None else 0  # + = head down
    by = 24 + bob

    def legs(far):
        cols = ("ink1", "ink1", "ink2") if far else ("ink2", "ink3", "ink4")
        for i, hx in enumerate((9, 14, 19)):
            p = ph + i * 2.1 + (pi if far else 0)
            o = round(sin(p) * 2) if st is None else (-1 if st == 0 else 1)
            lift = 1 if (st is None and cos(p) > .5) else 0
            hip = (hx + dx + far, by - 1)
            knee = (hx + dx + far + (i - 1) * 3 + o, by + 2 - lift)
            foot = (hx + dx + far + (i - 1) * 4 + o, 30 - lift)
            part(s, cols, lambda t, hip=hip, knee=knee, foot=foot: (limb(t, hip, knee, 2), limb(t, knee, foot, 1)))
            px(s, cols[2], knee[0] + (1 if i else -1), knee[1] + 2)  # leg spur
    legs(1)
    if st == 1:  # shell cracks open on the charge: ember wings fan out behind
        poly(s, "ember2", [(8 + dx, 15), (3 + dx, 4), (14 + dx, 2), (20 + dx, 12)])
        poly(s, "ember3", [(9 + dx, 13), (6 + dx, 6), (13 + dx, 4), (18 + dx, 11)])
        line(s, "ember1", (8 + dx, 14), (6 + dx, 6))
    part(s, ("ink1", "ink2", "ink2"), lambda t: ellipse(t, W, 6 + dx, by - 3, 17, 6))
    lift = 2 if st == 1 else 0
    part(s, ("ink3", "ink4", "ink5"), lambda t: (ellipse(t, W, 3 + dx, 9 + bob - lift, 20, 30),
         rect(t, (0, 0, 0, 0), 0, by - lift, 32, 12)))

    def seam(t):  # elytra split line and ember cracks in the ash
        pygame.draw.arc(t, c("ink1"), (round(5 + dx + OFF[0]), round(11 + bob - lift + OFF[1]), 17, 26), .3, 2.6, 1)
        for x, y, x2, y2 in ((8, 18, 11, 21), (11, 21, 10, 23), (15, 16, 17, 20), (17, 20, 19, 20)):
            line(t, "ember2", (x + dx, y + bob - lift), (x2 + dx, y2 + bob - lift))
        px(t, "ember3", 11 + dx, 21 + bob - lift)
        px(t, "ember3", 17 + dx, 20 + bob - lift)
        line(t, "ink5", (7 + dx, 14 + bob - lift), (11 + dx, 11 + bob - lift))
    over(s, seam)
    hb = by + tilt // 2  # head base

    def head(t):
        ellipse(t, W, 19 + dx, hb - 11, 8, 10)  # pronotum
        ellipse(t, W, 24 + dx, hb - 6 + tilt // 2, 5, 5)  # head
        ty = hb - 17 + tilt * 2
        poly(t, W, [(25 + dx, hb - 6), (25 + dx, hb - 9), (27 + dx, ty + 4), (29 + dx, ty), (29 + dx, ty + 5),
                    (28 + dx, hb - 7), (29 + dx, hb - 4)])  # horn, curving forward
    part(s, ("ink2", "ink3", "ink5"), head)
    line(s, "ink1", (22 + dx, hb - 10), (22 + dx, hb - 3))
    rect(s, "ember3", 26 + dx, hb - 4 + tilt // 2, 2, 1)
    px(s, "ink4", 29 + dx, hb - 1 + tilt // 2)  # mandible
    legs(0)


def bog_wisp(s, ph, st):
    dx = (-1, 3, 1)[st] if st is not None else 0
    bob = 2 * sin(ph) if st is None else 0
    big = 1.3 if st == 1 else 1
    sp = [(17 + dx - i * 1.9, 14 + bob + i * 1.5 + sin(ph + i * .8) * 2 * i / 7) for i in range(8)]
    part(s, ("moss2", "moss3", "moss4"), lambda t: chain(t, sp, [7 * big - i * .8 for i in range(8)]))
    x, y = sp[0]
    circle(s, "light1", x - 2, y - 2, 3)
    for ex in (3, 7):
        rect(s, "ink0", x + ex, y - 2, 2, 3)
        px(s, "light1", x + ex, y - 2)
    if st == 1:
        rect(s, "ink0", x + 3, y + 3, 6, 3)
        line(s, "ink0", (x + 2, y - 5), (x + 5, y - 3))
        line(s, "ink0", (x + 10, y - 5), (x + 7, y - 3))
    else:
        rect(s, "ink0", x + 4, y + 3, 3, 1)
    for k in range(3):
        a = ph * 1.5 + k * 2.1
        px(s, "light1", 15 + dx + cos(a) * 11, 14 + sin(a) * 9)


# --- cave monsters --------------------------------------------------------------------------
def cave_bat(s, ph, st):
    """Cave bat, front view, wings spread: arm + three finger bones, scalloped membrane, big ears."""
    a = (1, -.5, .3)[st] if st is not None else cos(ph)
    dx, dy = ((-1, -1), (0, 3), (0, 1))[st] if st is not None else (0, round(-a * 1.5))
    cx, cy = 16 + dx, 16 + dy

    def wing(sg, cols, bone):
        al = .1 + .6 * a  # angle above horizontal, pointing out

        def at(p, ang, L):
            return (p[0] + sg * cos(ang) * L, p[1] - sin(ang) * L)
        sh = (cx + sg * 3, cy - 2)
        wr = at(sh, al + .3, 6)
        tips = [at(wr, al + .35, 5), at(wr, al - .3, 6), at(wr, al - 1.0, 5)]
        hip = (cx + sg * 2, cy + 5)
        edge = [sh, wr, tips[0]]
        for t0, t1 in zip(tips, tips[1:] + [hip]):
            m = ((t0[0] + t1[0]) / 2, (t0[1] + t1[1]) / 2)
            edge += [(m[0] + (wr[0] - m[0]) * .35, m[1] + (wr[1] - m[1]) * .35), t1]
        part(s, cols, lambda t: poly(t, W, edge))
        line(s, bone, sh, wr)
        for tp in tips:
            line(s, bone, wr, tp)
        px(s, "ink6", wr[0], wr[1] - 1)  # thumb claw
    wing(-1, ("ink2", "ink3", "ink4"), "ink5")
    wing(1, ("ink2", "ink3", "ink4"), "ink5")
    part(s, ("ink3", "ink4", "ink5"), lambda t: (ellipse(t, W, cx - 4, cy - 3, 9, 10), circle(t, W, cx, cy - 5, 4),
         poly(t, W, [(cx - 4, cy - 6), (cx - 5, cy - 12), (cx - 1, cy - 8)]),
         poly(t, W, [(cx + 4, cy - 6), (cx + 5, cy - 12), (cx + 1, cy - 8)])))
    px(s, "ember1", cx - 4, cy - 10)
    px(s, "ember1", cx + 4, cy - 10)
    over(s, lambda t: [px(t, "ink5", cx - 2 + k, cy + k % 2 * 2) for k in range(5)])
    for fx in (-2, 1):  # clawed feet
        line(s, "ink2", (cx + fx, cy + 6), (cx + fx, cy + 8))
    for ex in (-2, 1):
        rect(s, "ember3", cx + ex, cy - 6, 2, 1)
    px(s, "ink1", cx, cy - 4)  # snout
    if st == 1:
        rect(s, "ink0", cx - 2, cy - 3, 5, 3)
        px(s, "ink7", cx - 2, cy - 3)
        px(s, "ink7", cx - 2, cy - 2)
        px(s, "ink7", cx + 2, cy - 3)
        px(s, "ink7", cx + 2, cy - 2)


def gloom_slime(s, ph, st):
    u = sin(ph) if st is None else 0
    w, h, dx, lift = 20 - 3 * u, 13 + 3 * u, 0, 2 * max(u, 0)
    if st is not None:
        w, h, dx = ((25, 9, -1), (26, 15, 3), (21, 12, 1))[st]
    x = 16 - w / 2 + dx
    top = 30 - h - lift
    part(s, ("water1", "water2", "water3"), lambda t: (ellipse(t, W, x, top, w, h * 1.5),
         rect(t, (0, 0, 0, 0), 0, 30 - lift, 32, 4)))
    over(s, lambda t: [circle(t, "water4", x + w * .25, top + 3, 1), px(t, "water4", x + w * .25 + 2, top + 2),
                       circle(t, "water3", x + w * .5, top + h * .7, 1), px(t, "water4", x + w * .7, top + h * .8)])
    ex = x + w * .55
    for e in (0, 5):
        rect(s, "light1", ex + e, top + 3, 3, 3)
        px(s, "ink0", ex + e + 1, top + 4)
    if st == 1:
        ellipse(s, "ink0", ex, top + 8, 9, 4)
    else:
        line(s, "ink0", (ex + 1, top + 8), (ex + 7, top + 8))


def bone_crawler(s, ph, st):
    dx = (-1, 2, 1)[st] if st is not None else 0
    bob = -round(abs(sin(ph))) if st is None else 0
    gx = lambda x: x + dx
    for i, (hx, far) in enumerate(((7, 1), (12, 0), (17, 1), (21, 0))):
        p = ph + pi * (i % 2)
        o = round(sin(p) * 2) if st is None else 0
        lift = 2 * (cos(p) > .3) if st is None else 0
        fx, fy = hx + (hx - 14) // 2 + o + 1, 30 - lift
        if st is not None and i == 3:
            fx, fy = (hx + 4, 17) if st == 0 else (hx + 6 + dx, 26) if st == 1 else (hx + 6, 24)
        kx, ky = hx + (fx - hx) * .4 + (2 if hx > 14 else -2), 10 - (3 if st == 0 and i == 3 else 0)
        col = "ink3" if far else "ink5"
        pygame.draw.lines(s, c(col), False, [(gx(x) + OFF[0], y + OFF[1]) for x, y in ((hx, 17 + bob), (kx, ky), (fx, fy))], 1)
        px(s, "ink6" if not far else "ink4", gx(kx), ky)
    part(s, ("ink4", "ink5", "ink6"), lambda t: ellipse(t, W, gx(5), 11 + bob, 14, 11))
    over(s, lambda t: [line(t, "ink3", (gx(8 + k * 3), 13 + bob), (gx(8 + k * 3), 20 + bob)) for k in range(3)])
    part(s, ("ink5", "ink6", "ink7"), lambda t: ellipse(t, W, gx(17), 10 + bob, 11, 10))
    g = 3 if st == 1 else 0
    part(s, ("ink5", "ink5", "ink6"), lambda t: rect(t, W, gx(21), 19 + bob + g, 8, 3))
    for e in (20, 25):
        rect(s, "ink0", gx(e), 13 + bob, 3, 3)
        px(s, "ember3", gx(e + 1), 14 + bob)
    for k in range(4):
        px(s, "ink7", gx(21 + k * 2), 19 + bob + g)
        px(s, "ink0", gx(22 + k * 2), 20 + bob + g)


def ember_imp(s, ph, st):
    lean = (-1, 1, 0)[st] if st is not None else 0
    bob = -round(abs(sin(ph))) if st is None else 0
    sw = round(sin(ph) * 3) if st is None else 0
    fl = round(sin(ph) * 3)
    poly(s, "ember1", [(13 + lean, 17 + bob), (5, 10 - fl + bob), (9, 12 + bob), (8, 18 + bob), (13 + lean, 19 + bob)])
    tp = [(12 + lean - i * 1.6, 21 + bob - i * 1.3 + sin(ph + i) * 1.5) for i in range(5)]
    part(s, ("ember1", "ember2", "ember2"), lambda t: chain(t, tp, [1.5] * 5))
    circle(s, "light0", tp[-1][0] - 1, tp[-1][1] - 2, 2)
    px(s, "light1", tp[-1][0] - 1, tp[-1][1] - 2)
    for i, hx in enumerate((14, 19)):
        o = sw * (1 - 2 * i)
        part(s, ("ember1", "ember1", "ember2"), lambda t, hx=hx, o=o: limb(t, (hx + lean, 22 + bob), (hx + o + lean, 29 if o <= 0 else 27), 3))
    part(s, ("ember1", "ember2", "ember3"), lambda t: (ellipse(t, W, 11 + lean, 13 + bob, 11, 11), circle(t, W, 18 + lean, 9 + bob, 5)))
    for hx, hy in ((15, 5), (20, 5)):
        poly(s, "light0", [(hx + lean, hy + bob + 1), (hx + lean - 1, hy + bob - 3), (hx + lean + 2, hy + bob)])
    rect(s, "light1", 20 + lean, 8 + bob, 3, 2)
    px(s, "ink0", 22 + lean, 9 + bob)
    line(s, "ink0", (20 + lean, 12 + bob), (23 + lean, 12 + bob))
    hand = ((12, 12), (24, 14), (21, 19))[st] if st is not None else (24 - sw, 20 + bob)
    part(s, ("ember1", "ember2", "ember3"), lambda t: limb(t, (19 + lean, 16 + bob), hand, 3))
    if st is not None:
        r = (2, 4, 1)[st]
        cx_, cy_ = (hand[0] + (4 if st == 1 else 0), hand[1] - 2)
        circle(s, "light0", cx_, cy_, r)
        circle(s, "light1", cx_, cy_, max(1, r - 2))


def ice_mite(s, ph, st):
    dx = (-2, 4, 1)[st] if st is not None else 0
    bob = -round(abs(sin(ph))) if st is None else 0
    up = 2 if st == 0 else 0
    for i, hx in enumerate((10, 15, 20)):
        o = round(sin(ph + i * 2.1) * 2) if st is None else 0
        f = 30 if o < 1 else 28
        part(s, ("water2", "water2", "water3"), lambda t, hx=hx, o=o, f=f: limb(t, (hx + dx, 21), (hx + 4 + o + dx, f), 2))
        px(s, "ink7", hx + 4 + o + dx, f)
    sp = 6 if st == 1 else 4
    for k, x in enumerate((9, 13, 17)):
        poly(s, "ink6" if k else "ink7", [(x + dx, 14 + bob - up), (x + 2 + dx, 14 - sp - 1 - k % 2 * 2 + bob - up), (x + 4 + dx, 14 + bob - up)])
    part(s, ("water2", "water3", "water4"), lambda t: (ellipse(t, W, 7 + dx, 12 + bob - up, 18, 14), circle(t, W, 25 + dx, 19 + bob - up, 4)))
    over(s, lambda t: [line(t, "ink6", (10 + dx + k * 4, 15 + bob - up), (11 + dx + k * 4, 21 + bob)) for k in range(3)])
    rect(s, "shadow2", 24 + dx, 17 + bob - up, 2, 2)
    rect(s, "shadow2", 27 + dx, 18 + bob - up, 2, 2)
    m = 4 if st == 1 else 1
    poly(s, "ink7", [(27 + dx, 22 + bob - up), (30, 24 + bob + m), (28 + dx, 25 + bob)])
    poly(s, "ink7", [(24 + dx, 23 + bob - up), (26 + dx, 27 + bob + m), (27 + dx, 24 + bob)])


def sand_wyrm(s, ph, st):
    lean, rise = ((-5, -4), (5, 8), (3, 3))[st] if st is not None else (0, round(sin(ph) * 2))
    sw = 5 * sin(ph) if st is None else 0
    part(s, ("earth2", "earth3", "earth4"), lambda t: ellipse(t, W, 4, 53, 46, 12))
    pts = [(18 + 23 * (i / 9) + lean * (i / 9) ** 2 + sw * (i / 9), 56 - 36 * (i / 9) + rise * (i / 9)) for i in range(10)]
    rs = [10 - 2.2 * i / 9 for i in range(10)]
    # frill behind head
    hx, hy = pts[-1]
    for k in range(3):
        poly(s, "earth4", [(hx - 3, hy - 4 + k * 3), (hx - 12, hy - 8 + k * 5), (hx - 3, hy + 1 + k * 3)])
    part(s, ("earth1", "earth2", "earth3"), lambda t: chain(t, pts, rs))

    def rings(t):
        for i in range(1, 9):
            (x0, y0), (x1, y1) = pts[i - 1], pts[i + 1]
            nx, ny = (y1 - y0), -(x1 - x0)
            n = math.hypot(nx, ny) or 1
            r = rs[i] + 1
            line(t, "earth1", (pts[i][0] - nx / n * r, pts[i][1] - ny / n * r), (pts[i][0] + nx / n * r, pts[i][1] + ny / n * r))
    over(s, rings)
    part(s, ("earth1", "earth2", "earth3"), lambda t: ellipse(t, W, hx - 8, hy - 7, 17, 13))
    o = (0, 1, .6)[st] if st is not None else .3 + .2 * (sin(ph) > 0)
    jaws(s, hx + 2, hy, 13, 6, o, ("earth1", "earth2", "earth3"), inner="ember2", gap=9, nt=4, tw=1, tl=4)
    circle(s, "light1", hx + 1, hy - 5, 2)
    px(s, "ink0", hx + 2, hy - 5)
    if st == 1:
        for i in range(5):
            circle(s, "earth4", 6 + i * 9, 58 - (i % 2) * 2, 1)


def mire_toad(s, ph, st):
    u = sin(ph) if st is None else 0
    ox = (-1, -2, -4, -2)[st + 1] if st is not None else -1
    oy = -round(max(u, 0) * 5)
    sq = 2 if u < 0 or st == 0 else 0
    M = ("moss1", "moss2", "moss3")
    air = u > 0
    part(s, M, lambda t: ellipse(t, W, 4 + ox - (2 if air else 0), 23 + oy + (-4 if air else 0), 12 + (2 if air else 0), 7 if not air else 4))
    part(s, M, lambda t: (ellipse(t, W, 5 + ox, 11 + oy + sq, 22, 16 - sq), ellipse(t, W, 17 + ox, 11 + oy + sq, 12, 12 - sq),
                          ellipse(t, W, 6 + ox, 16 + oy + sq, 10, 12 - sq)))
    part(s, M, lambda t: limb(t, (22 + ox, 22 + oy), (25 + ox + (3 if air else 0), 29 + oy * 0 - (3 if air else 0)), 3))
    if st == 0:
        part(s, ("earth3", "earth4", "earth4"), lambda t: ellipse(t, W, 19 + ox, 20 + oy, 9, 8))
    over(s, lambda t: [circle(t, "earth3", 9 + ox + k * 4, 14 + oy + sq + (k % 2) * 3, 1) for k in range(4)])
    ex, ey = 22 + ox, 8 + oy + sq
    part(s, M, lambda t: circle(t, W, ex + 2, ey + 2, 4))
    circle(s, "light0", ex + 3, ey + 2, 2)
    px(s, "ink0", ex + 4, ey + 2)
    line(s, "ink0", (ex - 4, ey + 11), (ex + 7, ey + 9))
    if st == 1:
        line(s, "ember2", (ex + 5, ey + 10), (28, ey + 10), 2)
        circle(s, "ember2", 27, ey + 10, 2)


def shade_(s, ph, st):
    dx = (-1, 2, 1)[st] if st is not None else 0
    bob = round(sin(ph) * 1) if st is None else 0
    sp = [(19 + dx - i * 1.8, 11 + bob + i * 1.8 + sin(ph + i * .7) * 2 * i / 8) for i in range(9)]
    for i, (hx, hy) in enumerate(((20, 14), (18, 16))):
        far = i == 0
        tgt = ((17, 6), (27, 15 - i * 3), (26, 17 + i * 2))[st] if st is not None else (27 - i * 3, 17 + round(sin(ph + i) * 2) + 2 * i)
        a = (hx + dx, hy + bob)
        part(s, ("shadow0", "shadow0", "shadow1") if far else ("shadow0", "shadow1", "shadow2"), lambda t, a=a, tgt=tgt: limb(t, a, tgt, 3))
        for dy in (-2, 0, 2):
            line(s, "shadow2", tgt, (tgt[0] + 2, tgt[1] + dy), 1)
    part(s, ("shadow0", "shadow1", "shadow2"), lambda t: chain(t, sp, [6.5 - i * .7 for i in range(9)]))
    hx, hy = sp[0]
    poly(s, "shadow1", [(hx - 4, hy - 4), (hx - 5, hy - 9), (hx - 1, hy - 6)])
    poly(s, "shadow1", [(hx + 3, hy - 4), (hx + 6, hy - 9), (hx + 5, hy - 3)])
    ellipse(s, "ink0", hx - 1, hy - 3, 9, 7)
    h = 2 if st == 1 else 1
    rect(s, "light1", hx + 1, hy - 1, 3, h)
    rect(s, "light1", hx + 5, hy - 1, 3, h)


# --- mini-bosses (96x96) -------------------------------------------------------------------
def stone_warden(s, ph, st):
    b = -round(abs(sin(ph)) * 2) if st is None else (3, 0, 1)[st]
    lg = ("ink2", "ink3", "ink4")
    RK = ("ink3", "ink4", "ink5")
    for i, hx in enumerate((37, 56)):
        o = round(sin(ph) * 6) * (1 - 2 * i) if st is None else 0
        lift = round(max(0, cos(ph + i * pi)) * 5) if st is None else 0
        fx = hx + o
        part(s, lg if i == 0 else RK, lambda t, hx=hx, fx=fx, lift=lift: (limb(t, (hx, 60 + b), (fx, 82 - lift), 14),
             rock(t, fx + 2, 87 - lift, 24, 10, 3 + i)))
    part(s, RK, lambda t: (rock(t, 48, 54 + b, 34, 22, 5), rock(t, 48, 40 + b, 44, 36, 1)))
    part(s, RK, lambda t: rock(t, 56, 18 + b + (2 if st == 0 else 0), 24, 22, 8))
    hy = 18 + b + (2 if st == 0 else 0)
    rect(s, "ember3", 59, hy - 1, 4, 3)
    rect(s, "ember3", 66, hy - 1, 4 if st != 1 else 3, 3)
    line(s, "ink0", (58, hy + 7), (69, hy + 7))
    poly(s, "ember3", [(46, 40 + b), (52, 46 + b), (46, 53 + b), (40, 46 + b)])
    poly(s, "light1", [(46, 43 + b), (49, 46 + b), (46, 49 + b), (43, 46 + b)])

    def arm(sx, sy, hand, cols, seed):
        el = ((sx + hand[0]) / 2 - 3, (sy + hand[1]) / 2 + 6)
        part(s, cols, lambda t: (limb(t, (sx, sy), el, 12), limb(t, el, hand, 11), rock(t, hand[0], hand[1] + 2, 20, 18, seed)))
    sw = round(sin(ph) * 7) if st is None else 0
    far_h = (36 - sw, 58 + b) if st is None else ((34, 14), (70, 80), (66, 70))[st]
    near_h = (66 + sw, 58 + b) if st is None else ((60, 8), (84, 82), (80, 70))[st]
    arm(30, 30 + b, far_h, lg, 11)
    part(s, RK, lambda t: rock(t, 31, 32 + b, 20, 18, 2))
    part(s, RK, lambda t: rock(t, 66, 32 + b, 22, 20, 4))
    arm(66, 32 + b, near_h, RK, 12)
    over(s, lambda t: ([line(t, "ink2", a, bb) for a, bb in
                        (((40, 28 + b), (44, 36 + b)), ((54, 56 + b), (58, 62 + b)), ((60, 42 + b), (56, 48 + b)), ((52, 12 + b), (55, 18 + b)))],
                       [circle(t, "moss3", x, y + b, 3) for x, y in ((36, 30), (63, 28), (50, 24), (44, 60))],
                       [circle(t, "moss2", x, y + b, 2) for x, y in ((39, 32), (66, 30), (53, 26))]))
    if st == 1:
        for i, (x, y) in enumerate(((78, 90), (86, 88), (90, 92), (72, 91), (92, 84))):
            circle(s, "ink5" if i % 2 else "ink4", x, y, 3)


def frost_matriarch(s, ph, st):
    b = round(sin(ph * 2) * 0) + (-round(abs(sin(ph)) * 2) if st is None else (3, 0, 1)[st])
    fw = (0, 4, 2)[st] if st is not None else 0
    LG = ("water1", "water2", "water3")
    FG = ("water1", "water1", "water2")
    hips = [(66, 0), (62, 1), (56, 2), (50, 3)]
    feet = [(84, 0), (72, 0), (36, 0), (14, 0)]

    def legs(idx, cols, off):
        for i in idx:
            hxx, _ = hips[i]
            p = ph + pi * (i % 2) + off
            fx = feet[i][0] + (round(sin(p) * 5) if st is None else 0) + (fw if i == 0 else 0)
            lift = round(max(0, cos(p)) * 7) if st is None else 0
            fy = 90 - lift
            if st is not None and i == 0:
                fy = (66, 90, 80)[st]
                fx = feet[0][0] + (-6 if st == 0 else fw)
            kx = hxx + (fx - hxx) * .4 + (4 if i == 0 else 0)
            ky = 34 + 3 * i - (lift if lift else 0) - (8 if (st == 0 and i == 0) else 0)
            part(s, cols, lambda t, hxx=hxx, kx=kx, ky=ky, fx=fx, fy=fy: (limb(t, (hxx, 56 + b), (kx, ky), 7),
                 limb(t, (kx, ky), (fx, fy), 5), poly(t, W, [(fx - 2, fy - 2), (fx + 1, fy + 2), (fx + 3, fy - 2)])))
    legs((1, 3), FG, pi * .5)
    ab = (st == 0) * 4
    part(s, ("water2", "water3", "water4"), lambda t: ellipse(t, W, 6, 26 + b - ab, 46, 38))
    over(s, lambda t: (poly(t, "shadow2", [(28, 40 + b - ab), (34, 40 + b - ab), (31, 47 + b - ab), (34, 54 + b - ab), (28, 54 + b - ab), (31, 47 + b - ab)]),
                       [circle(t, "ink7", x, y + b - ab, 2) for x, y in ((14, 44), (20, 34), (40, 36), (44, 50), (22, 58))],
                       [line(t, "water4", (10, 48 + b - ab), (18, 32 + b - ab))]))
    part(s, ("water2", "water3", "water4"), lambda t: (ellipse(t, W, 48, 44 + b, 28, 24), circle(t, W, 72 + fw // 2, 54 + b, 11)))
    for k in range(4):
        x = 52 + k * 7
        poly(s, "ink7" if k % 2 else "water4", [(x, 48 + b), (x + 3, 36 + b - k % 2 * 4 - (k == 1) * 3), (x + 6, 48 + b)])
    hx = 74 + fw // 2
    for ex, ey, r in ((3, 0, 2), (8, -1, 2), (6, 4, 1), (11, 3, 1)):
        circle(s, "shadow2", hx + ex, 50 + b + ey, r)
    px(s, "light1", hx + 3, 49 + b)
    px(s, "light1", hx + 8, 48 + b)
    sp = 6 if st == 1 else 2
    for k in (0, 1):
        poly(s, "ink7", [(hx + 6 + k * 7 - sp * k + 0, 60 + b), (hx + 9 + k * 7 - sp * k, 60 + b), (hx + 8 + k * 7 + sp * (k - 0), 70 + b + (4 if st == 1 else 0))])
    legs((0, 2), LG, 0)


def cinder_drake(s, ph, st):
    a = cos(ph) if st is None else (1, -.3, .3)[st]
    b = round(abs(sin(ph)) * -2) if st is None else (0, 0, 0)[st]
    sw = round(sin(ph) * 6) if st is None else 0
    hdx, hdy = ((-5, 0), (2, 6), (-1, 2))[st] if st is not None else (0, round(sin(ph) * 1))
    BD = ("ember1", "ember2", "ember3")
    DK = ("ember0", "ember0", "ember1")

    def wing(ox, oy, cols, k):
        wr = (40 + ox, 20 + oy - a * 12 * k)
        tips = [(10 + ox, 24 + oy - a * 20 * k), (18 + ox, 42 + oy - a * 8 * k), (32 + ox, 52 + oy - a * 3 * k)]
        sh_ = (48 + ox, 42 + oy + b)
        part(s, cols, lambda t: poly(t, W, [sh_, wr] + tips))
        for tp_ in tips:
            line(s, "ember3" if cols is BD else "ember1", wr, tp_)
        part(s, cols, lambda t: limb(t, sh_, wr, 4))
    wing(8, -2, DK, .8)
    # far legs
    for hx, o in ((34, -sw), (58, sw)):
        part(s, DK, lambda t, hx=hx, o=o: (limb(t, (hx, 62 + b), (hx + 5 + o // 2, 76), 10), limb(t, (hx + 5 + o // 2, 76), (hx + o, 91), 7)))
    # tail
    tp = [(26 - i * 2.4, 56 + b + i * 1.6 + sin(ph + i * .6) * 3) for i in range(8)]
    part(s, BD, lambda t: chain(t, tp, [7 - i * .75 for i in range(8)]))
    poly(s, "ember3", [(tp[-1][0] - 1, tp[-1][1] - 3), (tp[-1][0] - 8, tp[-1][1] - 1), (tp[-1][0] - 1, tp[-1][1] + 4)])
    # neck + body
    hx, hy = 72 + hdx, 26 + hdy + (-3 if st == 0 else 0)
    nk = [(58, 46 + b), (64 + hdx * .3, 36 + b + hdy * .4), (hx - 2, hy + 3)]
    part(s, BD, lambda t: chain(t, nk, [9, 7, 6.5]))
    part(s, BD, lambda t: (ellipse(t, W, 18, 40 + b, 50, 30), ellipse(t, W, 44, 38 + b, 24, 28)))
    over(s, lambda t: [line(t, "light0", (30 + k * 3, 56 + b + (k % 2)), (62 - 2 * k, 66 + b), 2) for k in range(1)] +
        [ellipse(t, "light0", 36 + k * 8, 62 + b, 8, 9) for k in range(3)])
    # head
    part(s, BD, lambda t: ellipse(t, W, hx - 8, hy - 7, 18, 14))
    for k in range(2):
        poly(s, "light0", [(hx - 4 - k * 4, hy - 6), (hx - 16 - k * 4, hy - 12 - k * 2), (hx - 8 - k * 4, hy - 3)])
    o = (0, 1, .4)[st] if st is not None else 0
    jaws(s, hx + 3, hy + 1, 12, 5, o, BD, inner="ember0", teeth="light0", gap=7, nt=3)
    rect(s, "light1", hx + 1, hy - 3, 3, 2)
    px(s, "ink0", hx + 3, hy - 3)
    if st == 0:
        circle(s, "ember3", hx + 8, hy + 1, 2)
    if st in (1, 2):
        fx, fy = hx + 14, hy + 1 + (2 if st == 1 else 0)
        L = 93 - fx
        if st == 1:
            poly(s, "ember3", [(fx, fy - 2), (fx + L, fy - 10), (fx + L, fy + 8), (fx, fy + 4)])
            poly(s, "light0", [(fx, fy - 1), (fx + L - 2, fy - 6), (fx + L - 2, fy + 5), (fx, fy + 3)])
            poly(s, "light1", [(fx, fy), (fx + L - 5, fy - 2), (fx + L - 5, fy + 2), (fx, fy + 2)])
        else:
            for i in range(3):
                circle(s, "ember3" if i != 1 else "light0", fx + 1 + i * 3, fy - 3 + i * 3 - (i % 2) * 4, 2 - i % 2)
    # near legs
    for hx2, o in ((40, sw), (64, -sw)):
        part(s, BD, lambda t, hx2=hx2, o=o: (limb(t, (hx2, 62 + b), (hx2 + 5 + o // 2, 76), 11), limb(t, (hx2 + 5 + o // 2, 76), (hx2 + o, 90), 7),
                                           ellipse(t, W, hx2 + o - 3, 88, 13, 4)))
        for k in range(3):
            px(s, "light0", hx2 + o + 8 + k * 0, 88 + k)
    wing(0, 0, BD, 1)


MONSTERS = [
    ("thornling", 32, 32, thornling), ("barrow_wight", 32, 32, barrow_wight), ("mere_lurker", 64, 64, mere_lurker),
    ("frost_wolf", 64, 64, frost_wolf), ("ash_scarab", 32, 32, ash_scarab), ("bog_wisp", 32, 32, bog_wisp),
    ("umbral_hound", 64, 64, umbral_hound),
    ("cave_bat", 32, 32, cave_bat), ("gloom_slime", 32, 32, gloom_slime), ("bone_crawler", 32, 32, bone_crawler),
    ("ember_imp", 32, 32, ember_imp), ("ice_mite", 32, 32, ice_mite), ("sand_wyrm", 64, 64, sand_wyrm),
    ("mire_toad", 32, 32, mire_toad), ("shade", 32, 32, shade_),
    ("stone_warden", 96, 96, stone_warden), ("frost_matriarch", 96, 96, frost_matriarch), ("cinder_drake", 96, 96, cinder_drake),
]


def main(only=None):
    frames = {}
    for i, (n, w, h, fn) in enumerate(MONSTERS):
        if only and n not in only:
            continue
        frames[n] = build("monster_" + n, w, h, fn, seed=i + 1)
    return frames


if __name__ == "__main__":
    main(sys.argv[1:] or None)
