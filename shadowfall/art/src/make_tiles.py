"""32-px tilesets: one cave/castle set per theme, one realm set per land, and 4 cave parallax
layers per theme (960x540). Tiles get no outline (style guide). Original art."""
import math
import zlib
import random

from sfart import Sheet, TILE, circle, ellipse, line, poly, px, rect, save_png, surf

T = TILE

# --- cave themes: rock ramp dark->light (4), accent, a lit-lip colour, the back-wall colour ---------
CAVE = {
    "stone":   dict(rock=("ink1", "ink2", "ink3", "ink4"), acc="moss3", lip="ink5", wall="ink1"),
    "moss":    dict(rock=("moss0", "moss1", "moss2", "moss3"), acc="moss4", lip="moss4", wall="moss0"),
    "crystal": dict(rock=("ink1", "ink2", "ink3", "ink4"), acc="water4", lip="water3", wall="ink1"),
    "lava":    dict(rock=("earth0", "earth1", "ember1", "earth2"), acc="ember3", lip="ember2", wall="earth0"),
    "frost":   dict(rock=("water1", "water2", "ink5", "ink6"), acc="ink7", lip="ink7", wall="water0"),
    "sand":    dict(rock=("earth1", "earth2", "earth3", "earth4"), acc="light0", lip="earth4", wall="earth0"),
    "swamp":   dict(rock=("moss0", "earth1", "moss1", "moss2"), acc="shadow2", lip="moss3", wall="moss0"),
    "shadow":  dict(rock=("ink0", "shadow0", "ink2", "shadow1"), acc="shadow2", lip="shadow2", wall="ink0"),
    "castle":  dict(rock=("ink1", "ink2", "ink3", "ink5"), acc="ember2", lip="ink5", wall="ink1", bricks=True),
}


def speckle(s, cols, n, seed, x0=0, y0=0, w=T, h=T, size=1):
    r = random.Random(seed)
    for _ in range(n):
        rect(s, r.choice(cols), x0 + r.randrange(w - size + 1), y0 + r.randrange(h - size + 1), size, size)


def solid(th, mask, seed=0):
    """mask bits: N1 E2 S4 W8 set when that neighbour is solid too. Open sides get edges."""
    r0, r1, r2, r3 = th["rock"]
    s = surf(T, T)
    rect(s, r1, 0, 0, T, T)
    if th.get("bricks"):
        for y in range(0, T, 8):
            line(s, r0, (0, y + 7), (T, y + 7))
            off = 0 if (y // 8) % 2 else 8
            for x in range(off, T, 16):
                line(s, r0, (x, y), (x, y + 7))
            line(s, r2, (0, y), (T, y))
    else:
        speckle(s, (r0, r2), 26, seed + mask, size=2)
        speckle(s, (r0,), 10, seed + mask + 99, size=3)
    if not mask & 1:  # open top: lit lip
        rect(s, th["lip"], 0, 0, T, 2)
        rect(s, r3, 0, 2, T, 3)
        speckle(s, (th["acc"],), 4, seed + 5, 0, 0, T, 2, 2)
    if not mask & 4:
        rect(s, r0, 0, T - 3, T, 3)
    if not mask & 8:
        rect(s, r2, 0, 0, 2, T)
    if not mask & 2:
        rect(s, r0, T - 2, 0, 2, T)
    return s


def cave_set(name, th):
    r0, r1, r2, r3 = th["rock"]
    acc = th["acc"]
    sh = Sheet("tiles_" + name, T, T, origin=[0, 0], cols=16, kind="tileset")
    for m in range(16):
        sh.add(f"solid_{m}", [solid(th, m)], 1, False)
    s = solid(th, 0, 7)
    rect(s, "ink0", 0, 0, T, T)
    s = solid(th, 15, 3)
    for a, b in (((4, 4), (14, 15)), ((14, 15), (11, 27)), ((14, 15), (27, 10)), ((20, 13), (26, 24))):
        line(s, "ink0", a, b, 2)
    sh.add("cracked", [s], 1, False)                                           # B
    for nm, gem in (("ore_diamond", ("water3", "water4", "ink7")), ("ore_sun", ("light0", "light1", "ember3"))):
        s = solid(th, 15, 11)
        for gx, gy in ((7, 8), (20, 18), (12, 23)):                             # * s
            poly(s, gem[0], [(gx, gy - 4), (gx + 4, gy), (gx, gy + 4), (gx - 4, gy)])
            px(s, gem[2], gx - 1, gy - 1)
            px(s, gem[1], gx, gy - 2)
        sh.add(nm, [s], 1, False)
    s = surf(T, T)                                                              # = ledge
    rect(s, r2, 0, 0, T, 6)
    rect(s, th["lip"], 0, 0, T, 2)
    rect(s, r0, 0, 6, T, 2)
    for x in (3, 27):
        rect(s, r1, x, 8, 2, 4)
    sh.add("ledge", [s], 1, False)
    c2 = s.copy()                                                               # - crumbly ledge
    for x in (7, 16, 24):
        line(c2, "ink0", (x, 0), (x + 2, 7))
    sh.add("ledge_crumbly", [c2], 1, False)

    def spikes(h):
        s = surf(T, T)
        for i in range(4):
            x = i * 8
            poly(s, "ink5", [(x, T), (x + 4, T - h), (x + 8, T)])
            line(s, "ink7", (x + 4, T - h), (x + 2, T - 2))
            line(s, "ink3", (x + 5, T - h + 2), (x + 7, T - 1))
        return s
    sh.add("spikes", [spikes(14)], 1, False)                                    # ^
    sh.add("spike_trap", [spikes(4), spikes(9), spikes(14), spikes(9)], 6)     # A

    def thorns():                                                               # n shadow thorns: a black
        s = surf(T, T)                                                          # bramble wall, violet barbs
        rect(s, "ink0", 0, 0, T, T)
        rng = random.Random(41)
        for a, b in (((0, 6), (32, 14)), ((0, 24), (32, 18)), ((4, 0), (12, 32)), ((22, 0), (28, 32)),
                     ((0, 30), (18, 2)), ((14, 32), (32, 4))):
            line(s, "shadow0", a, b, 3)
            line(s, "shadow1", a, b, 1)
        for _ in range(22):                                                     # barbs, tip lit
            x, y = rng.randrange(1, T - 1), rng.randrange(1, T - 1)
            dx, dy = rng.choice(((3, -2), (-3, -2), (2, 3), (-2, 3), (3, 1), (-3, 1)))
            line(s, "ink4", (x, y), (x + dx, y + dy))
            px(s, "shadow2", x + dx, y + dy)
        for x, y in ((9, 11), (24, 23), (17, 6)):                               # a faint violet heart-glow
            px(s, "shadow2", x, y)
            px(s, "ink7", x, y - 1)
        return s
    sh.add("thorns", [thorns()], 1, False)                                      # n

    def flame(k, h=22, w=T):
        s = surf(T, T)
        for i, (col, sc) in enumerate((("ember1", 1.0), ("ember2", 0.75), ("ember3", 0.5), ("light1", 0.25))):
            hh = h * sc * (1 + 0.15 * math.sin(k * 1.7 + i))
            cx = w / 2 + math.sin(k * 2.1 + i) * 2
            poly(s, col, [(cx - w * sc * 0.42, T), (cx + math.sin(k + i) * 3, T - hh), (cx + w * sc * 0.42, T)])
        return s
    sh.add("fire", [flame(k) for k in range(4)], 8)                             # !

    def lava(k):
        s = surf(T, T)
        rect(s, "ember2", 0, 0, T, T)
        rect(s, "ember1", 0, T - 10, T, 10)
        for i in range(4):
            x = (i * 9 + k * 3) % T
            rect(s, "ember3", x, 3 + (i % 2) * 4, 5, 2)
        for x in range(0, T, 8):
            rect(s, "light0", (x + k * 2) % T, 0, 4, 2)
        return s
    sh.add("lava", [lava(k) for k in range(4)], 4)                              # ~

    def chest(open_):
        s = surf(T, T)
        rect(s, "ink0", 3, 11, 26, 20)
        rect(s, "earth2", 4, 12, 24, 18)
        rect(s, "earth3", 4, 12, 24, 3)
        rect(s, "earth1", 4, 20, 24, 2)
        for x in (4, 26):
            rect(s, "ink4", x, 12, 2, 18)
        rect(s, "light0", 14, 18, 4, 5)
        if open_:
            rect(s, "ink0", 3, 4, 26, 9)
            rect(s, "earth1", 4, 5, 24, 7)
            rect(s, "light1", 6, 12, 20, 2)
            speckle(s, ("light0", "light1"), 6, 3, 6, 8, 20, 4)
        return s
    sh.add("chest", [chest(False), chest(True)], 1, False)                      # T

    def gem(k):
        s = surf(T, T)
        cy = 16 + (1 if k in (1, 2) else 0)
        poly(s, "ink0", [(16, cy - 9), (25, cy), (16, cy + 9), (7, cy)])
        poly(s, acc if acc not in ("ink7",) else "water4", [(16, cy - 8), (24, cy), (16, cy + 8), (8, cy)])
        poly(s, "ink7", [(16, cy - 8), (20, cy - 4), (16, cy)])
        if k == 2:
            px(s, "light1", 24, cy - 8)
            px(s, "light1", 23, cy - 9)
        return s
    sh.add("gem", [gem(k) for k in range(4)], 6)                                # $

    s = surf(T, T)                                                              # E exit door (top tile of 2)
    rect(s, r0, 2, 0, 28, T)
    rect(s, "ink0", 6, 4, 20, T - 4)
    ellipse(s, "ink0", 6, 0, 20, 12)
    rect(s, "earth1", 8, 6, 16, T - 6)
    ellipse(s, "earth1", 8, 2, 16, 10)
    line(s, "earth0", (16, 4), (16, T))
    px(s, "light0", 20, 20)
    sh.add("door", [s], 1, False)

    def mush(k):
        s = surf(T, T)
        rect(s, "ink6", 13, 18, 6, 14)
        h = 12 if k == 0 else 9
        ellipse(s, "ember2", 3, 20 - h, 26, h + 4)
        ellipse(s, "ember3", 8, 21 - h, 10, 4)
        for x in (8, 16, 22):
            px(s, "ink7", x, 24 - h + (x % 3))
        return s
    sh.add("mushroom", [mush(0), mush(1)], 6, False)                            # o

    s = surf(T, T)                                                              # H ladder
    for x in (6, 24):
        rect(s, "earth2", x, 0, 3, T)
        rect(s, "earth3", x, 0, 1, T)
    for y in (4, 12, 20, 28):
        rect(s, "earth1", 6, y, 21, 3)
        rect(s, "earth3", 6, y, 21, 1)
    sh.add("ladder", [s], 1, False)

    def vine(seed):
        s = surf(T, T)
        for x0 in (11, 19):
            for y in range(0, T, 2):
                line(s, "moss2", (x0 + math.sin((y + seed) / 4) * 2, y), (x0 + math.sin((y + seed + 2) / 4) * 2, y + 2), 2)
        speckle(s, ("moss3", "moss4"), 7, seed, 6, 0, 20, T, 2)
        return s
    sh.add("vine", [vine(1)], 1, False)                                         # V
    sh.add("rope", [vine(5)], 1, False)                                         # R
    s = solid(th, 15, 21)                                                       # % climbing wall
    for y in range(2, T, 6):
        line(s, r3, (4, y), (27, y + 2), 2)
        line(s, r0, (4, y + 2), (27, y + 4))
    sh.add("climb_wall", [s], 1, False)
    s = surf(T, T)                                                              # I ice
    rect(s, "water3", 0, 0, T, T)
    rect(s, "water4", 0, 0, T, 4)
    rect(s, "ink7", 0, 0, T, 1)
    line(s, "ink7", (5, 9), (12, 16))
    line(s, "water2", (18, 20), (28, 28))
    rect(s, "water2", 0, T - 3, T, 3)
    sh.add("ice", [s], 1, False)

    def spring(k):
        s = surf(T, T)
        rect(s, r2, 2, 20, 28, 12)
        rect(s, th["lip"], 2, 20, 28, 2)
        ellipse(s, "water2", 5, 21, 22, 6)
        for i in range(3):
            y = 16 - ((k * 4 + i * 6) % 14)
            circle(s, "water4" if i % 2 else "ink7", 10 + i * 6, y, 1 + (i == 1))
        return s
    sh.add("spring", [spring(k) for k in range(4)], 6)                          # u

    def lever(on):
        s = surf(T, T)
        rect(s, "ink3", 8, 24, 16, 8)
        rect(s, "ink5", 8, 24, 16, 2)
        end = (24, 10) if on else (8, 10)
        line(s, "earth2", (16, 26), end, 3)
        circle(s, "ember2" if not on else "moss3", *end, 3)
        return s
    sh.add("lever", [lever(False), lever(True)], 1, False)                      # L

    def gate(open_):
        s = surf(T, T)
        if open_:
            rect(s, "ink3", 0, 0, T, 5)
            for x in range(3, T, 8):
                rect(s, "ink4", x, 0, 3, 5)
            return s
        rect(s, "ink3", 0, 0, T, 3)
        rect(s, "ink3", 0, 18, T, 3)
        for x in range(3, T, 8):
            rect(s, "ink4", x, 0, 3, T)
            rect(s, "ink6", x, 0, 1, T)
        return s
    sh.add("gate", [gate(False), gate(True)], 1, False)                         # G

    s = solid(th, 15, 31)                                                       # J flame jet nozzle
    rect(s, "ink3", 8, 0, 16, 10)
    rect(s, "ink0", 12, 0, 8, 6)
    rect(s, "ember2", 13, 1, 6, 3)
    sh.add("flame_jet", [s], 1, False)
    sh.add("flame", [flame(k, 30, 20) for k in range(4)], 10)

    def geyser(k):
        s = solid(th, 15, 41)
        ellipse(s, "ink0", 8, 0, 16, 8)
        if k:
            for i in range(k * 2):
                circle(s, "ink6", 12 + (i * 5) % 9, 2 - i, 2)
        return s
    sh.add("geyser", [geyser(k) for k in range(3)], 6)                          # M
    s = surf(T, T)                                                              # P U platform piece
    rect(s, "earth1", 0, 0, T, 10)
    rect(s, "earth3", 0, 0, T, 2)
    rect(s, "earth0", 0, 8, T, 2)
    for x in (2, 28):
        rect(s, "ink4", x, 2, 2, 6)
    sh.add("platform", [s], 1, False)

    def checkpoint(lit, k=0):                                                   # C a lantern post
        s = surf(T, T)
        rect(s, "ink3", 14, 8, 4, 24)
        rect(s, "ink3", 8, 29, 16, 3)
        rect(s, "ink4", 14, 6, 10, 2)
        rect(s, "ink3", 19, 8, 7, 2)
        rect(s, "light0" if lit else "ink2", 20, 10, 5, 7)
        if lit:
            rect(s, "light1", 21, 11 + k % 2, 3, 4)
        rect(s, "ink3", 19, 17, 7, 2)
        return s
    sh.add("checkpoint", [checkpoint(False)], 1, False)
    sh.add("checkpoint_lit", [checkpoint(True, k) for k in range(2)], 4)

    def crystal(k):
        s = surf(T, T)
        hi = "water4" if name != "shadow" else "shadow2"
        lo = "water2" if name != "shadow" else "shadow1"
        for x, h, w in ((9, 18, 7), (16, 26, 8), (23, 14, 6)):
            poly(s, lo, [(x - w / 2, T), (x - w / 2, T - h + 4), (x, T - h), (x + w / 2, T - h + 4), (x + w / 2, T)])
            line(s, hi, (x - 1, T - h + 2), (x - 1, T - 2))
        px(s, "ink7", 15 + k, 8 - k)
        return s
    sh.add("crystal", [crystal(0), crystal(1)], 3)

    def torch(k):
        s = surf(T, T)
        rect(s, "earth1", 14, 14, 4, 12)
        rect(s, "ink3", 12, 12, 8, 3)
        f = flame(k, 12, 10)
        s.blit(f, (0, -20))
        return s
    sh.add("torch", [torch(k) for k in range(4)], 8)                            # i
    s = surf(T, T)                                                              # w moonlit window
    rect(s, r0, 6, 2, 20, 28)
    ellipse(s, r0, 6, 0, 20, 10)
    rect(s, "water1", 9, 6, 14, 22)
    ellipse(s, "water1", 9, 2, 14, 10)
    circle(s, "ink6", 19, 9, 3)
    line(s, r2, (16, 3), (16, 28), 2)
    line(s, r2, (9, 16), (23, 16), 2)
    sh.add("window", [s], 1, False)
    s = surf(T, T)                                                              # f banner
    rect(s, "ink4", 4, 1, 24, 2)
    poly(s, "ember1", [(7, 3), (25, 3), (25, 28), (16, 23), (7, 28)])
    poly(s, "ember2", [(9, 3), (13, 3), (13, 24), (9, 26)])
    circle(s, "light0", 16, 12, 3)
    sh.add("banner", [s], 1, False)
    s = surf(T, T)                                                              # K key
    circle(s, "light0", 10, 16, 6)
    circle(s, "ink1", 10, 16, 3)
    rect(s, "light0", 15, 15, 13, 3)
    rect(s, "light0", 22, 18, 2, 4)
    rect(s, "light0", 26, 18, 2, 5)
    px(s, "light1", 8, 12)
    sh.add("key", [s], 1, False)

    def shard(k):
        s = surf(T, T)                                                          # + light shard
        poly(s, "light0", [(16, 6 - k), (21, 16), (16, 26 + k), (11, 16)])
        poly(s, "light1", [(16, 9 - k), (18, 16), (16, 22 + k), (14, 16)])
        return s
    sh.add("light_shard", [shard(k) for k in (0, 1, 2, 1)], 6)
    s = surf(T, T)                                                              # back wall (behind the play layer)
    rect(s, th["wall"], 0, 0, T, T)
    speckle(s, (r0,), 12, 77, size=2)
    sh.add("back_wall", [s], 1, False)
    # a few decor pieces
    s = surf(T, T)
    for i, (x, h) in enumerate(((5, 10), (12, 16), (20, 8), (26, 12))):
        poly(s, r2, [(x - 3, 0), (x + 3, 0), (x, h)])
        px(s, th["lip"], x - 1, 1)
    sh.add("stalactite", [s], 1, False)
    s = surf(T, T)
    for x in range(1, T, 4):
        h = 4 + (x * 7) % 9
        line(s, acc if name in ("moss", "swamp") else r3, (x, T), (x + 1, T - h))
    sh.add("tuft", [s], 1, False)
    s = surf(T, T)
    ellipse(s, "ink6", 6, 20, 12, 10)
    for dx in (8, 13):
        rect(s, "ink0", dx, 23, 3, 3)
    rect(s, "ink6", 20, 27, 10, 3)
    rect(s, "ink5", 18, 25, 3, 7)
    sh.add("skull", [s], 1, False)
    sh.save()


# --- realm (top-down) tilesets, one per land -------------------------------------------------------
LAND = {
    "emberhold":    dict(g=("moss2", "moss3", "moss4"), p=("earth2", "earth3", "earth4"), tree=("moss1", "moss2", "moss3"), acc="light0", w="water"),
    "weepingwold":  dict(g=("moss1", "moss2", "moss3"), p=("earth1", "earth2", "earth3"), tree=("moss0", "moss1", "moss2"), acc="moss4", w="water"),
    "hollowcrown":  dict(g=("moss1", "earth2", "moss2"), p=("ink3", "ink4", "ink5"), tree=("moss0", "moss1", "earth2"), acc="ink6", w="water"),
    "drowned_mere": dict(g=("moss2", "moss3", "water3"), p=("earth3", "earth4", "ink6"), tree=("moss1", "moss2", "moss3"), acc="water4", w="water"),
    "wintermarch":  dict(g=("ink5", "ink6", "ink7"), p=("ink4", "ink5", "ink6"), tree=("moss0", "moss1", "ink6"), acc="ink7", w="ice"),
    "cinder_wastes": dict(g=("earth2", "earth3", "earth4"), p=("earth1", "earth2", "ember1"), tree=("earth1", "ember1", "earth3"), acc="ember3", w="lava"),
    "mirefen":      dict(g=("moss0", "moss1", "earth1"), p=("earth0", "earth1", "earth2"), tree=("moss0", "shadow0", "moss1"), acc="shadow2", w="bog"),
    "shadowgate":   dict(g=("ink2", "ink3", "shadow1"), p=("ink3", "ink4", "ink5"), tree=("ink1", "shadow0", "ink3"), acc="shadow2", w="water"),
    "umbral_reach": dict(g=("ink1", "shadow0", "ink2"), p=("ink2", "ink3", "ink4"), tree=("ink0", "ink1", "shadow0"), acc="shadow2", w="black"),
}
WATER = {"water": ("water1", "water2", "water3", "water4"), "ice": ("water3", "water4", "ink6", "ink7"),
         "lava": ("ember1", "ember2", "ember3", "light0"), "bog": ("moss0", "earth1", "moss1", "moss2"),
         "black": ("ink0", "ink1", "shadow0", "shadow1")}


def ground(ld, seed):
    g0, g1, g2 = ld["g"]
    s = surf(T, T)
    rect(s, g1, 0, 0, T, T)
    r = random.Random(seed)
    for _ in range(10):
        x, y = r.randrange(T - 3), r.randrange(2, T)
        line(s, g2, (x, y), (x + 1, y - 3))
        line(s, g0, (x + 1, y + 1), (x + 3, y + 1))
    if seed % 3 == 2:
        for _ in range(3):
            px(s, ld["acc"], r.randrange(T), r.randrange(T))
    return s


def realm_set(name, ld):
    sh = Sheet("realm_" + name, T, T, origin=[0, 0], cols=16, kind="tileset")
    for i in range(3):
        sh.add(f"ground_{i}", [ground(ld, i)], 1, False)
    p0, p1, p2 = ld["p"]
    for i in range(3):
        s = surf(T, T)
        rect(s, p1, 0, 0, T, T)
        speckle(s, (p0, p2), 14 + i * 4, 50 + i, size=2)
        sh.add(f"path_{i}", [s], 1, False)
    w0, w1, w2, w3 = WATER[ld["w"]]

    def water(k, mask=15):
        """mask: N1 E2 S4 W8 set where the neighbour is water too; open sides get a shore."""
        s = surf(T, T)
        rect(s, w1, 0, 0, T, T)
        for i in range(3):
            x = (i * 11 + k * 4) % 26
            rect(s, w2, x, 6 + i * 9, 6, 1)
            px(s, w3, x + 2 + k, 5 + i * 9)
        if not mask & 1:
            rect(s, p2, 0, 0, T, 3); rect(s, w3, 0, 3, T, 1)
        if not mask & 4:
            rect(s, w0, 0, T - 4, T, 4); rect(s, p1, 0, T - 2, T, 2)
        if not mask & 8:
            rect(s, p2, 0, 0, 3, T); rect(s, w3, 3, 0, 1, T)
        if not mask & 2:
            rect(s, p1, T - 3, 0, 3, T); rect(s, w0, T - 4, 0, 1, T)
        return s
    sh.add("water", [water(0), water(1)], 2)
    for m in range(15):
        sh.add(f"shore_{m}", [water(0, m), water(1, m)], 2)

    def tree(part):
        t0, t1, t2 = ld["tree"]
        s = surf(T, T)
        if part == "top":
            ellipse(s, "ink0", 1, 3, 30, 29)
            ellipse(s, t0, 2, 4, 28, 28)
            ellipse(s, t1, 3, 4, 24, 22)
            ellipse(s, t2, 6, 6, 12, 9)
            speckle(s, (t0,), 8, 9, 5, 12, 22, 16, 2)
        else:
            ellipse(s, "ink0", 1, -4, 30, 20)
            ellipse(s, t0, 2, -4, 28, 18)
            rect(s, "ink0", 11, 10, 10, 18)
            rect(s, "earth1", 12, 10, 8, 18)
            rect(s, "earth2", 12, 10, 3, 18)
            ellipse(s, "ink0", 6, 26, 20, 5)
        return s
    sh.add("tree_top", [tree("top")], 1, False)
    sh.add("tree", [tree("base")], 1, False)                                   # F
    s = ground(ld, 1)                                                           # X rock / cliff top
    ellipse(s, "ink0", 3, 6, 26, 24)
    ellipse(s, "ink3", 4, 6, 24, 22)
    ellipse(s, "ink5", 8, 8, 12, 8)
    rect(s, "ink2", 6, 22, 20, 4)
    sh.add("rock", [s], 1, False)
    s = surf(T, T)                                                              # cliff face (2 tall, darker going down)
    rect(s, "ink3", 0, 0, T, 16)
    rect(s, "ink2", 0, 16, T, 16)
    rect(s, ld["g"][2], 0, 0, T, 2)
    for x in (5, 14, 25):
        line(s, "ink1", (x, 4), (x - 2, 30), 2)
    rect(s, "ink0", 0, T - 4, T, 4)
    sh.add("cliff_face", [s], 1, False)
    s = ground(ld, 0)                                                           # B reeds
    for x in range(2, T, 4):
        h = 14 + (x * 5) % 10
        line(s, ld["tree"][1], (x, T - 2), (x + 1, T - h), 2)
        px(s, ld["acc"], x + 1, T - h)
    sh.add("reeds", [s], 1, False)
    s = ground(ld, 2)                                                           # bush
    ellipse(s, "ink0", 4, 10, 24, 18)
    ellipse(s, ld["tree"][1], 5, 10, 22, 16)
    ellipse(s, ld["tree"][2], 8, 11, 9, 6)
    sh.add("bush", [s], 1, False)

    def building(kind):
        s = surf(T, T)
        if kind == "house":                                                     # H
            poly(s, "ink0", [(0, 15), (16, 1), (32, 15)])
            poly(s, "ember1", [(2, 15), (16, 3), (30, 15)])
            poly(s, "ember2", [(16, 3), (30, 15), (18, 15)])
            rect(s, "ink0", 3, 15, 26, 17)
            rect(s, "earth3", 4, 15, 24, 16)
            rect(s, "earth1", 13, 21, 6, 10)
            rect(s, "light0", 6, 19, 4, 4)
            rect(s, "light0", 22, 19, 4, 4)
        elif kind == "mine":                                                    # M
            ellipse(s, "ink0", 1, 4, 30, 32)
            ellipse(s, "ink3", 2, 5, 28, 30)
            ellipse(s, "ink0", 8, 12, 16, 22)
            rect(s, "earth2", 7, 12, 3, 20)
            rect(s, "earth2", 22, 12, 3, 20)
            rect(s, "earth3", 6, 10, 20, 3)
            rect(s, "ink4", 12, 26, 8, 2)
        elif kind == "portal":                                                  # P
            ellipse(s, "ink0", 3, 2, 26, 30)
            ellipse(s, "shadow1", 4, 3, 24, 28)
            ellipse(s, "shadow0", 8, 7, 16, 20)
            ellipse(s, "shadow2", 12, 11, 6, 8)
        elif kind == "castle":                                                  # C
            rect(s, "ink0", 2, 6, 28, 26)
            rect(s, "ink2", 3, 7, 26, 25)
            for x in (3, 11, 19, 26):
                rect(s, "ink2", x, 2, 4, 6)
            ellipse(s, "ink0", 11, 18, 10, 14)
            rect(s, "ember2", 15, 10, 2, 3)
        elif kind == "sign":                                                    # +
            rect(s, "earth1", 15, 14, 3, 16)
            rect(s, "ink0", 5, 5, 22, 12)
            rect(s, "earth3", 6, 6, 20, 10)
            line(s, "earth1", (8, 9), (23, 9))
            line(s, "earth1", (8, 12), (19, 12))
        elif kind == "chest":                                                   # T
            rect(s, "ink0", 6, 12, 20, 16)
            rect(s, "earth2", 7, 13, 18, 14)
            rect(s, "earth3", 7, 13, 18, 3)
            rect(s, "light0", 14, 18, 4, 4)
        elif kind == "vent":                                                    # V
            ellipse(s, "ink0", 6, 10, 20, 14)
            ellipse(s, "ink2", 8, 12, 16, 10)
            ellipse(s, "ink0", 12, 14, 8, 5)
        return s
    for k in ("house", "mine", "portal", "castle", "sign", "chest", "vent"):
        sh.add(k, [building(k)], 1, False)

    def waystone(lit, k=0):                                                     # L, a lantern on a standing stone
        s = surf(T, T)
        poly(s, "ink0", [(8, T), (10, 6), (16, 1), (22, 6), (24, T)])
        poly(s, "ink4", [(9, T - 1), (11, 7), (16, 3), (21, 7), (23, T - 1)])
        poly(s, "ink5", [(11, 7), (16, 3), (15, T - 1), (11, T - 1)])
        for y in (12, 20):
            line(s, "ink2", (12, y), (20, y + 1))
        rect(s, "ink0", 13, 8, 7, 8)
        rect(s, "light0" if lit else "ink2", 14, 9, 5, 6)
        if lit:
            rect(s, "light1", 15, 10 + k, 3, 3)
        return s
    sh.add("waystone", [waystone(False)], 1, False)
    sh.add("waystone_lit", [waystone(True, 0), waystone(True, 1)], 4)

    def bridge(broken):                                                         # # and =
        s = surf(T, T)
        for x in range(0, T, 6):
            if broken and 10 < x < 22:
                continue
            rect(s, "earth2", x, 4, 5, 24)
            rect(s, "earth3", x, 4, 5, 2)
            rect(s, "earth0", x + 4, 4, 1, 24)
        rect(s, "earth1", 0, 2, T, 2)
        rect(s, "earth1", 0, 28, T, 2)
        return s
    sh.add("bridge", [bridge(False)], 1, False)
    sh.add("bridge_broken", [bridge(True)], 1, False)
    s = ground(ld, 0)                                                           # Y ivy cliff (needs climb)
    rect(s, "ink3", 0, 0, T, T)
    for x in range(2, T, 5):
        for y in range(0, T, 3):
            px(s, "moss2" if (x + y) % 2 else "moss3", x + (y // 3) % 2, y)
    sh.add("gate_ivy", [s], 1, False)
    s = ground(ld, 1)                                                           # O rubble (needs pound)
    for (x, y, w) in ((3, 14, 12), (14, 8, 14), (10, 20, 16), (2, 4, 9)):
        ellipse(s, "ink0", x, y, w, w * 0.8)
        ellipse(s, "ink4", x + 1, y, w - 2, w * 0.7)
        px(s, "ink6", x + 3, y + 2)
    sh.add("gate_rubble", [s], 1, False)
    s = ground(ld, 2)                                                           # K shadow thorns (needs flare)
    for i in range(7):
        x = 2 + i * 4
        poly(s, "ink0", [(x - 2, T), (x + 1, 4 + (i * 7) % 10), (x + 3, T)])
        px(s, "shadow2", x + 1, 6 + (i * 7) % 10)
    sh.add("gate_thorns", [s], 1, False)
    sh.save()


# --- cave parallax layers (960x540; far is opaque, the rest are transparent strips) --------------
def parallax(name, th):
    W, H = 960, 540
    r = random.Random(zlib.crc32(name.encode()))
    r0, r1, r2, r3 = th["rock"]
    far = surf(W, H)
    band = ["ink0", th["wall"], "ink1"] if th["wall"] != "ink1" else ["ink0", "ink1", "ink2"]
    if name in ("shadow",):
        band = ["ink0", "shadow0", "ink1"]
    for i, col in enumerate(band):
        y0 = i * H // 3
        rect(far, col, 0, y0, W, H // 3 + 1)
        if i:  # 4-row checker dither at the seam
            for y in range(y0 - 4, y0):
                for x in range(y % 2, W, 2):
                    px(far, col, x, y)
    save_png(far, f"parallax/{name}_far.png")
    back = surf(W, H)                                                           # 0.25x: ink1 silhouettes, no ink0
    for x in range(-40, W, 70):
        h = r.randint(140, 320)
        poly(back, "ink1", [(x, H), (x + 35, H - h), (x + 80, H)])
        h2 = r.randint(60, 180)
        poly(back, "ink1", [(x + 20, 0), (x + 40, h2), (x + 60, 0)])
    save_png(back, f"parallax/{name}_back.png")
    mid = surf(W, H)                                                            # 0.5x: ink2 pillars and roots
    for x in range(30, W, 190):
        w = r.randint(24, 44)
        rect(mid, "ink2", x, 0, w, H)
        rect(mid, "ink3", x, 0, 3, H)
        for y in range(40, H, 90):
            line(mid, "ink2", (x + w, y), (x + w + r.randint(20, 60), y + r.randint(20, 60)), 4)
    save_png(mid, f"parallax/{name}_mid.png")
    front = surf(W, H)                                                          # 1.4x: solid ink0, <=15% of the screen
    for x in range(0, W, 160):
        h = r.randint(40, 90)
        poly(front, "ink0", [(x, 0), (x + 30, h), (x + 60, 0)])
    for x in range(80, W, 320):
        ellipse(front, "ink0", x, H - 50, r.randint(90, 140), 100)
    save_png(front, f"parallax/{name}_front.png")


def main():
    for n, th in CAVE.items():
        cave_set(n, th)
        parallax(n, th)
    for n, ld in LAND.items():
        realm_set(n, ld)


if __name__ == "__main__":
    main()
