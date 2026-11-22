"""The top-down body kit: one lean, long-legged figure drawn from a spec (palette, headgear, hair, beard,
armour, cloak), seen from the front (down), the back (up) or the side (faces right; the game flips).
The Lanternbearer (make_hero.py) and every person (make_people.py) are built from it, so they share
proportions and anchors. figure() returns the frame (no outline yet) and the anchors gear hangs from.
Original art."""
from sfart import line, poly, px, rect, surf

STEEL = ("ink3", "ink4", "ink5", "ink6", "ink7")   # darkest -> the glint
# head, torso, legs (px). std = the realm's people; tall = the Lanternbearer; small = a child.
SIZES = {"std": (10, 13, 15), "tall": (11, 16, 19), "small": (9, 9, 9)}


def torn(x0, x1, y, n, depth, seed=0):
    """A ragged hem from (x0, y) to (x1, y): n teeth hanging down by up to depth."""
    pts = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts.append((x, y + (depth if (i + seed) % 2 else depth // 3) + ((i * 7 + seed) % 3) - 1))
    return pts


def _row(s, col, cx, y, w):
    rect(s, col, cx - w // 2, y, w, 1)


def _head_w(i, h):
    return 5 if i in (0, h - 1) else (7 if i == 1 or i >= h - 3 else 9)


def _head(s, k, d, cx, top, h):
    """The bare head (skin, hair, beard, face), then whatever is worn on it."""
    skin = k.get("skin", ("earth2", "earth3"))
    hair, style, beard = k.get("hair"), k.get("style", "short"), k.get("beard")
    eye = top + 5
    for i in range(h):
        _row(s, skin[1], cx, top + i, _head_w(i, h))
    if d == "up":
        if hair and style != "tonsure":
            for i in range(h - 1):
                _row(s, hair, cx, top + i, _head_w(i, h))
        elif hair:                                   # a tonsure: a ring of hair round a bare crown
            for i in range(3, h - 2):
                _row(s, hair, cx, top + i, _head_w(i, h))
        if hair and style == "long":
            rect(s, hair, cx - 4, top + h - 1, 9, 4)
        if hair and style == "bun":
            rect(s, hair, cx - 2, top - 2, 5, 3)
        return
    side = d == "side"
    # shadow on the side away from the light (top-left)
    rect(s, skin[0], cx + 3, top + 3, 2, h - 5)
    if side:
        px(s, skin[1], cx + 5, eye + 1)              # the nose
        px(s, "ink0", cx + 2, eye)
        rect(s, skin[1], cx + 3, top + 3, 2, h - 5)
        rect(s, skin[0], cx - 1, top + 4, 2, h - 6)
    else:
        px(s, "ink0", cx - 2, eye)
        px(s, "ink0", cx + 2, eye)
        px(s, skin[0], cx, eye + 1)
    if hair:
        rows = 3 if style != "tonsure" else 0
        for i in range(rows):
            _row(s, hair, cx, top + i, _head_w(i, h))
        if style == "tonsure":
            for i in range(2, 5):
                px(s, hair, cx - 4, top + i)
                px(s, hair, cx + 4 if not side else cx - 3, top + i)
        if side:                                     # the back of the head
            for i in range(3, h - 3):
                rect(s, hair, cx - 4, top + i, 3 if i < 6 else 2, 1)
        else:
            for i in (3, 4):
                px(s, hair, cx - 4, top + i)
                px(s, hair, cx + 4, top + i)
        if style == "long":
            rect(s, hair, cx - 5, top + 3, 2, h)
            if not side:
                rect(s, hair, cx + 4, top + 3, 2, h)
        if style == "bun":
            rect(s, hair, cx - 2 - (3 if side else 0), top - 2, 5, 3)
    if beard:
        x0, w = (cx - 1, 6) if side else (cx - 3, 7)
        rect(s, beard, x0, top + 7, w, h - 7)
        rect(s, beard, x0 + 1, top + h, w - 2, 1 + k.get("beard_len", 1))
        if not side:
            px(s, skin[0], cx, top + 7)              # the mouth, a gap in the beard
            px(s, beard, cx - 4, top + 6)
            px(s, beard, cx + 4, top + 6)


def _hood(s, k, d, cx, top, h, sway=0):
    """A hood: a peak, the face in its shadow, pale eyes; the lower face catches the light."""
    C = k["hood"]
    skin = k.get("skin", ("earth2", "earth3"))
    eyes = k.get("eyes", "ink6")
    if d == "side":
        for i in range(-1, h + 1):
            w = 7 if i == -1 else (9 if i in (0, h) else 10)
            rect(s, C[1], cx - 5, top + i, w, 1)
        rect(s, C[1], cx - 6, top + 2, 1, 5)                      # the peak trails back
        px(s, C[1], cx - 7 - (1 if sway > 0 else 0), top + 4)
        rect(s, C[0], cx - 5, top + h - 2, 5, 3)
        line(s, C[2], (cx - 3, top - 1), (cx + 1, top - 1))
        px(s, C[2], cx + 3, top)
        rect(s, "ink0", cx + 1, top + 3, 4, 2)                    # the opening
        rect(s, "ink1", cx + 1, top + 5, 4, 1)
        px(s, eyes, cx + 3, top + 5)
        rect(s, skin[0], cx + 1, top + 6, 4, h - 7)
        rect(s, skin[1], cx + 3, top + 6, 2, h - 8)
        px(s, skin[1], cx + 5, top + 6)                           # the nose
        if k.get("veil"):
            rect(s, "ink2", cx + 1, top + 4, 4, h - 5)
        return
    for i in range(-2, h + 1):
        w = 3 if i == -2 else (7 if i == -1 else (9 if i == 0 else 11))
        _row(s, C[1], cx, top + i, w)
    rect(s, C[0], cx + 3, top + 2, 3, h - 1)                      # the shaded side
    line(s, C[2], (cx - 3, top - 1), (cx - 1, top - 1))
    line(s, C[2], (cx - 5, top + 1), (cx - 5, top + 4))
    if d == "up":
        line(s, C[0], (cx, top), (cx, top + h))                   # the seam
        px(s, C[2], cx - 3, top + 2)
        return
    _row(s, "ink0", cx, top + 3, 5)
    _row(s, "ink0", cx, top + 4, 7)
    _row(s, "ink1", cx, top + 5, 7)
    px(s, eyes, cx - 2, top + 5)
    px(s, eyes, cx + 2, top + 5)
    for i in range(6, h):
        _row(s, "ink1", cx, top + i, 7 if i < h - 1 else 5)
        _row(s, skin[0], cx, top + i, 5 if i < h - 1 else 3)
    rect(s, skin[1], cx - 2, top + 6, 2, 2)
    if k.get("veil"):                                             # a mourner's veil: no face at all
        for i in range(4, h):
            _row(s, "ink2" if i % 2 else "ink3", cx, top + i, 7 if i < h - 1 else 5)


def _hat(s, k, d, cx, top, h, sway=0):
    kind, col = k.get("head"), k.get("head_col", ("earth0", "earth1", "earth2"))
    side = d == "side"
    S = STEEL
    if kind == "kettle":                              # a foot soldier's kettle helm: dome and wide brim
        for i, w in ((-2, 5), (-1, 7), (0, 9), (1, 9)):
            _row(s, S[2], cx, top + i, w)
        rect(s, S[3], cx - 3, top - 1, 3, 2)
        px(s, S[4], cx - 2, top - 1)
        _row(s, S[3], cx, top + 2, 13)
        _row(s, S[1], cx, top + 3, 13)
        if d != "up":
            _row(s, "ink1", cx, top + 4, 9)
    elif kind == "nasal":                             # a steel cap with a nose bar over a mail coif
        coif = "ink3"
        if d == "up":
            for i in range(3, h + 1):
                _row(s, coif, cx, top + i, 9)
        else:
            rect(s, coif, cx - 4, top + 4, 2 if side else 1, h - 4)
            if not side:
                rect(s, coif, cx + 4, top + 4, 1, h - 4)
            _row(s, coif, cx, top + h - 1, 7)
            _row(s, coif, cx, top + h, 9)
        for i, w in ((-1, 5), (0, 7), (1, 9), (2, 9), (3, 9)):
            _row(s, S[2], cx, top + i, w)
        rect(s, S[3], cx - 3, top, 3, 2)
        px(s, S[4], cx - 2, top)
        _row(s, S[1], cx, top + 3, 9)
        if d != "up":
            rect(s, S[3], cx + (4 if side else 0), top + 4, 1, 3)
    elif kind == "great":                             # a knight's great helm: a slit, breaths, a plume
        for i in range(-1, h + 1):
            _row(s, S[2], cx, top + i, 7 if i in (-1, h) else 9)
        rect(s, S[3], cx - 3, top, 3, 3)
        px(s, S[4], cx - 2, top)
        rect(s, S[1], cx + 3, top + 1, 2, h - 1)
        _row(s, S[1], cx, top + h, 7)
        if d == "down":
            rect(s, "ink0", cx - 3, top + 4, 7, 1)
            rect(s, S[3], cx, top + 5, 1, h - 5)
            for i in (6, 8):
                px(s, "ink0", cx - 2, top + i)
                px(s, "ink0", cx + 2, top + i)
        elif side:
            rect(s, "ink0", cx + 1, top + 4, 4, 1)
            px(s, "ink0", cx + 3, top + 6)
            px(s, "ink0", cx + 3, top + 8)
        plume = k.get("plume", "ember2")
        if side:
            poly(s, plume, [(cx + 1, top - 2), (cx - 2, top - 5), (cx - 6 - sway, top - 3), (cx - 7 - sway, top + 2),
                            (cx - 4, top - 1)])
        else:
            rect(s, plume, cx - 1, top - 5, 3, 5)
            px(s, plume, cx + 2 + sway, top - 4)
            px(s, plume, cx - 2, top - 2)
    elif kind == "wide":                              # a traveller's hat: low crown, wide soft brim
        for i, w in ((-3, 5), (-2, 7), (-1, 7), (0, 7)):
            _row(s, col[1], cx, top + i, w)
        rect(s, col[2], cx - 3, top - 2, 2, 2)
        _row(s, k.get("band", col[0]), cx, top + 1, 7)
        _row(s, col[1], cx, top + 2, 15)
        _row(s, col[0], cx, top + 3, 13)
        px(s, col[2], cx - 6, top + 2)
        px(s, col[2], cx - 5, top + 2)
        if d != "up":
            _row(s, "ink1", cx, top + 4, 9)
    elif kind == "straw":                             # a fen-man's straw cone
        for n, i in enumerate(range(-3, 4)):
            _row(s, col[2] if n % 2 else col[1], cx, top + i, 3 + n * 2)
        if d != "up":
            _row(s, "ink1", cx, top + 4, 9)
    elif kind == "fur":                               # a northman's fur cap with ear flaps
        for i, w in ((-2, 7), (-1, 9), (0, 11), (1, 11), (2, 11)):
            _row(s, col[1], cx, top + i, w)
        for x, y in ((-3, -1), (1, -2), (3, 0), (-1, 1), (4, 2), (-4, 2)):
            px(s, col[2], cx + x, top + y)
        rect(s, col[0], cx - 5, top + 3, 2, 4)
        if not side:
            rect(s, col[0], cx + 4, top + 3, 2, 4)
        if d == "up":
            for i in range(3, 6):
                _row(s, col[1], cx, top + i, 9)
    elif kind == "cap":                               # a woodsman's cap and feather
        for i, w in ((-1, 7), (0, 9), (1, 9), (2, 9)):
            _row(s, col[1], cx, top + i, w)
        rect(s, col[2], cx - 3, top - 1, 3, 1)
        _row(s, col[0], cx, top + 2, 9 if not side else 11)
        line(s, k.get("feather", "ink6"), (cx + 3, top), (cx + 5 + sway, top - 4))


def figure(k, d, cell=(32, 48), g=46, step=0, bob=0, sway=0, main=None, off=None, hem=0):
    """One frame. step: -2..2 along the walk; bob: px the body sinks (breath); sway: the cloak's swing.
    main / off: where the weapon hand and the other hand are, if not hanging at the side (x, y).
    Returns (surface, anchors): anchors = top, sh, hip, cx, main, off (the two hands)."""
    s = surf(*cell)
    cx = cell[0] // 2
    hh, tl, ll = SIZES[k.get("size", "std")]
    top = g - (hh + tl + ll) + bob
    sh, hip = top + hh, top + hh + tl
    T = k.get("tunic", ("earth0", "earth1", "earth2"))
    C = k.get("cloak")
    pants, boots = k.get("pants", "ink2"), k.get("boots", ("earth0", "earth1"))
    skin = k.get("skin", ("earth2", "earth3"))
    sleeve = k.get("sleeve", T[1])
    glove = k.get("glove", skin[1])
    small = k.get("size") == "small"
    hw = 4 if small else 5                           # half the torso
    robe = k.get("robe")
    skirt = (g - 5 - hip) if robe else k.get("skirt", 3)
    hem_y = g - 3 - k.get("cloak_up", 0)
    side = d == "side"
    arm_len = tl - 2
    sw = (1 if step > 0 else -1 if step < 0 else 0)

    def cloak_back():
        if not C:
            return
        if side:
            pts = torn(cx - 11 - sway * 2, cx - 1, hem_y - 3 - abs(sway), 5, 4, seed=hem)
            poly(s, C[1], [(cx - 4, sh), (cx + 1, sh), (cx + 1, hip)] + pts[::-1] + [(cx - 8 - sway, hip - 2)])
            poly(s, C[0], [(cx - 1, sh + 4), (cx + 1, hip)] + pts[2:][::-1])
            line(s, C[2], (cx - 5, sh + 3), (cx - 9 - sway * 2, hem_y - 5 - abs(sway)))
        else:
            pts = torn(cx - 11 + sway, cx + 11 + sway, hem_y - 4, 8, 4, seed=hem)
            poly(s, C[1], [(cx - 7, sh), (cx + 7, sh), (cx + 11 + sway, hip + 2)] + pts[::-1] + [(cx - 11 + sway, hip + 2)])
            poly(s, C[0], [(cx + 2, sh), (cx + 7, sh), (cx + 11 + sway, hip + 2)] + pts[5:][::-1])
            line(s, C[2], (cx - 8, sh + 3), (cx - 11 + sway, hem_y - 5))
            if d == "up":
                line(s, C[0], (cx - 1, sh + 2), (cx - 1 + sway, hem_y - 4))
                line(s, C[2], (cx - 6, sh + 2), (cx - 8 + sway, hem_y - 5))
                line(s, C[2], (cx - 3, sh + 6), (cx - 4 + sway, hem_y - 6))

    def legs():
        if side:
            for near in (False, True):
                dx = (step if near else -step) * 2
                col = pants if near else k.get("pants_far", "ink1")
                lift = 1 if step == 0 and bob < 0 and not near else 0
                line(s, col, (cx - 1, hip), (cx - 1 + dx, g - 5 - lift), 4)
                bt = boots[1] if near else boots[0]
                rect(s, bt, cx - 3 + dx, g - 5 - lift, 5, 5)
                rect(s, bt, cx + 2 + dx, g - 3 - lift, 2, 3)
                if near:
                    rect(s, boots[0], cx - 3 + dx, g - 5, 5, 1)
                    px(s, k.get("mud", boots[0]), cx + 1 + dx, g - 1)
            return
        for i, x0 in enumerate((cx - 4, cx + 1)):
            st = step if i == 0 else -step
            lift = max(0, st) if d == "down" else max(0, -st)
            drop = 1 if (st < 0 if d == "down" else st > 0) else 0
            w = 3 if small else 4
            rect(s, pants, x0, hip - 1, w, g - 4 - lift - hip)
            rect(s, boots[1], x0, g - 5 - lift, w, 5 + drop)
            rect(s, boots[0], x0, g - 5 - lift, w, 1)
            px(s, k.get("mud", boots[1]), x0 + (0 if i else w - 1), g - 1 - lift + drop)

    def torso():
        if side:
            rect(s, T[1], cx - 3, sh, 7, tl + skirt)
            rect(s, T[0], cx - 3, sh + 1, 2, tl + skirt - 1)
            rect(s, T[2], cx + 3, sh + 1, 1, tl - 4)
        else:
            rect(s, T[1], cx - hw, sh, hw * 2 + 1, tl + skirt)
            rect(s, T[0], cx + hw - 1, sh + 1, 2, tl + skirt - 1)
            rect(s, T[2], cx - hw, sh + 1, 1, tl - 4)
            if not robe and skirt > 1 and d == "down":
                rect(s, T[0], cx, hip + 1, 1, skirt - 1)           # the tunic splits over the legs
        x0, w = (cx - 3, 7) if side else (cx - hw, hw * 2 + 1)
        chest = k.get("chest")
        if chest == "mail":
            for y in range(sh + 1, hip + skirt):
                for x in range(x0 + (y % 2), x0 + w, 2):
                    px(s, "ink4", x, y)
        elif chest == "plate":                        # a steel breastplate, lit top-left
            rect(s, STEEL[2], x0, sh, w, tl - 3)
            rect(s, STEEL[1], x0 + w - 2, sh + 1, 2, tl - 4)
            rect(s, STEEL[3], x0 + 1, sh + 1, 3 if not side else 2, 3)
            px(s, STEEL[4], x0 + 1, sh + 1)
            rect(s, STEEL[1], x0, sh + tl - 4, w, 1)
        elif chest == "apron" and d != "up":          # a smith's leather apron, forge burns
            rect(s, "earth0", x0 + 1, sh + 2, w - 2, tl + skirt - 3)
            px(s, "ember3", x0 + 3, sh + 6)
            px(s, "ember2", x0 + 5, sh + 9)
        elif chest == "tabard":                       # a knight's tabard over mail
            tb = k.get("tabard", ("ember1", "ember2"))
            rect(s, tb[1], x0 + (2 if not side else 1), sh, w - (4 if not side else 2), tl + skirt)
            rect(s, tb[0], x0 + w - 4 if not side else x0 + 1, sh + 1, 2 if not side else 1, tl + skirt - 1)
            if d == "down":
                rect(s, k.get("trim", "light0"), cx - 1, sh + 3, 3, 1)   # a small sun on the breast
                rect(s, k.get("trim", "light0"), cx, sh + 2, 1, 3)
        if k.get("straps") and d == "down":           # pack straps over the shoulders
            rect(s, k["straps"], cx - hw + 1, sh, 1, tl - 3)
            rect(s, k["straps"], cx + hw - 1, sh, 1, tl - 3)
        if k.get("cross") and d != "up":              # a ranger's baldric
            line(s, k["cross"], (x0 + 1, sh + 1), (x0 + w - 2, hip - 4))
        if k.get("mail_hem") and not robe:            # mail under the jerkin, torn at the hem
            for y in range(hip + 1, hip + skirt):
                for x in range(x0, x0 + w):
                    px(s, "ink3" if (x + y) % 2 else "ink2", x, y)
            for x in range(x0 + (hem % 2), x0 + w, 3):
                px(s, "ink2", x, hip + skirt)
        belt = k.get("belt")
        if belt:
            rect(s, belt, x0, hip - 2, w, 2)
            if d == "down":
                px(s, k.get("buckle", "ink5"), cx, hip - 2)
        sash = k.get("sash")                          # a wide sash with a tail that swings
        if sash:
            rect(s, sash[1], x0, hip - 3, w, 3)
            rect(s, sash[0], x0, hip - 1, w, 1)
            if d == "down":
                poly(s, sash[1], [(cx - 4, hip - 1), (cx - 2, hip - 1), (cx - 2 - sway, hip + 6), (cx - 4 - sway, hip + 5)])
                px(s, sash[0], cx - 3 - sway, hip + 6)
            elif side:
                poly(s, sash[1], [(cx - 3, hip - 2), (cx - 2, hip), (cx - 6 - sway * 2, hip + 5), (cx - 7 - sway * 2, hip + 3)])
            else:
                poly(s, sash[0], [(cx + 2, hip - 1), (cx + 4, hip - 1), (cx + 4 + sway, hip + 6), (cx + 2 + sway, hip + 5)])
        if k.get("fur"):                              # a wolf-fur collar
            rect(s, "ink5", x0 - 1, sh - 1, w + 2, 3)
            for x in range(x0, x0 + w, 3):
                px(s, "ink6", x, sh - 1)

    def arm(x, hand, is_main):
        """One arm from the shoulder at x down to its hand."""
        at = hand or (x, sh + arm_len + (sw if is_main else -sw) * (0 if side else 1))
        col = k.get("sleeve_main", sleeve) if is_main else sleeve
        if hand:
            line(s, col, (x, sh + 2), at, 3)
        else:
            rect(s, col, x - 1, sh + 1, 3, at[1] - sh - 1)
            rect(s, T[0] if col == T[1] else col, x + 1, sh + 2, 1, at[1] - sh - 3)
        if is_main and k.get("vambrace"):             # steel on the sword arm
            mid = ((x + at[0]) / 2, (sh + 2 + at[1]) / 2)
            line(s, STEEL[2], mid, at, 3)
            line(s, STEEL[3], (mid[0] - 1, mid[1]), (at[0] - 1, at[1] - 1))
        rect(s, glove, at[0] - 1, at[1], 3, 2)
        return at

    def pauldron(x, w=5):                             # one bright steel shoulder, two lames
        rect(s, STEEL[1], x - 2, sh - 2, w, 7)
        rect(s, STEEL[2], x - 2, sh - 2, w, 5)
        rect(s, STEEL[3], x - 2, sh - 2, w - 1, 3)
        rect(s, STEEL[4], x - 1, sh - 2, w - 3, 1)
        px(s, STEEL[4], x - 2, sh - 1)
        rect(s, STEEL[1], x - 2, sh + 1, w, 1)
        px(s, "ink0", x + w - 4, sh + 3)              # a rivet

    A = {"cx": cx, "top": top, "sh": sh, "hip": hip, "g": g}
    if d == "down":
        cloak_back()
        legs()
        torso()
        A["main"] = arm(cx - hw - 2, main, True)
        A["off"] = arm(cx + hw + 2, off, False)
        if k.get("pauldron"):
            pauldron(cx - hw - 2)
        if C:                                         # the cloak's collar on the shoulders
            rect(s, C[1], cx + hw - 1, sh - 1, 4, 3)
            rect(s, C[0], cx + hw, sh + 1, 3, 1)
            if not k.get("pauldron"):
                rect(s, C[1], cx - hw - 2, sh - 1, 4, 3)
            px(s, k.get("clasp", "ink5"), cx, sh)
    elif d == "up":
        legs()
        torso()
        A["main"] = arm(cx + hw + 2, main, True)
        A["off"] = arm(cx - hw - 2, off, False)
        cloak_back()
        if k.get("pauldron"):
            pauldron(cx + hw + 2)
    else:
        cloak_back()
        legs()
        torso()
        A["off"] = off or (cx + 2 + sw * 3, sh + arm_len)
        A["main"] = arm(cx, main or (cx - sw * 3, sh + arm_len), True)   # swings against the near leg
        if C:
            rect(s, C[1], cx - 4, sh - 1, 5, 3)
        if k.get("pauldron"):
            pauldron(cx - 1, 6)
    _head(s, k, d, cx, top, hh)
    if k.get("hood"):
        _hood(s, k, d, cx, top, hh, sway)
    elif k.get("head"):
        _hat(s, k, d, cx, top, hh, sway)
    return s, A
