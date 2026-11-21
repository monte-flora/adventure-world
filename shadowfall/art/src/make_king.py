"""The Shadow King, 192x256: always a silhouette (ink0), two shadow2 eyes and a shadow1 orb are his
only colour, an ember rim light from behind, smoke motes rising off him. Never gory. Original art."""
import math
import random

import pygame

from sfart import Sheet, c, circle, ellipse, flash, line, poly, px, surf

W, H = 192, 256


def rim(s, col1="ember1", col2="ember2"):
    """Back-lit edge: filled pixels with clear space 1-2 px to the side or above get ember."""
    m = pygame.mask.from_surface(s, 1)
    out = s.copy()
    for y in range(H):
        for x in range(W):
            if not m.get_at((x, y)):
                continue
            def clear(dx, dy):
                nx, ny = x + dx, y + dy
                return not (0 <= nx < W and 0 <= ny < H) or not m.get_at((nx, ny))
            if s.get_at((x, y))[:3] != c("ink0"):
                continue
            if clear(1, 0) or clear(-1, 0) or clear(0, -1):
                out.set_at((x, y), c(col2))
            elif clear(2, 0) or clear(-2, 0):
                out.set_at((x, y), c(col1))
    return out


def king(t=0.0, lift=0, arms=0.15, orb=1.0, eyes=True, blade=None, crown_glow=False, motes=0, seed=0):
    """t: sway phase; arms 0 (down) .. 1 (raised); orb glow scale; blade angle for the sword."""
    s = surf(W, H)
    cx, top = 96, 30 - lift
    sway = math.sin(t) * 3
    # robe: a tall tattered cone
    hem = 246 - lift
    pts = [(cx - 22, top + 50), (cx + 22, top + 50), (cx + 46 + sway, hem - 10)]
    for i in range(7):  # ragged hem, wisping down
        x = cx + 46 - i * 15 + sway
        pts.append((x - 4, hem + (6 if i % 2 else -2) + round(math.sin(t + i) * 3)))
    pts.append((cx - 48 + sway, hem - 12))
    poly(s, "ink0", pts)
    # shoulders / pauldrons
    ellipse(s, "ink0", cx - 44, top + 40, 40, 28)
    ellipse(s, "ink0", cx + 4, top + 40, 40, 28)
    poly(s, "ink0", [(cx - 50, top + 48), (cx - 60, top + 36), (cx - 40, top + 44)])
    poly(s, "ink0", [(cx + 50, top + 48), (cx + 60, top + 36), (cx + 40, top + 44)])
    # head and crown of spikes
    ellipse(s, "ink0", cx - 16, top + 10, 32, 38)
    for i, (dx, hgt) in enumerate(((-14, 18), (-7, 28), (0, 36), (7, 28), (14, 18))):
        poly(s, "ink0", [(cx + dx - 4, top + 14), (cx + dx, top + 14 - hgt), (cx + dx + 4, top + 14)])
    # arms
    for side in (-1, 1):
        sh = (cx + side * 34, top + 52)
        a = math.radians(100 - side * 10 - arms * 130) if side > 0 else math.radians(80 + arms * 130)
        hand = (sh[0] + math.cos(a) * 50, sh[1] + math.sin(a) * 50)
        line(s, "ink0", sh, hand, 14)
        circle(s, "ink0", *hand, 8)
        for k in (-1, 0, 1):  # claw fingers
            fa = a + k * 0.35
            line(s, "ink0", hand, (hand[0] + math.cos(fa) * 13, hand[1] + math.sin(fa) * 13), 3)
        if side < 0:
            orb_at = hand
    if blade is not None:
        b = math.radians(blade)
        hx, hy = cx + 34 + math.cos(math.radians(100 - 10)) * 40, top + 90
        line(s, "ink0", (hx, hy), (hx + math.cos(b) * 110, hy + math.sin(b) * 90), 10)
    s = rim(s)
    # eyes (only colour besides the orb)
    if eyes:
        for dx in (-8, 4):
            poly(s, "shadow2", [(cx + dx, top + 26), (cx + dx + 5, top + 27), (cx + dx + 4, top + 29), (cx + dx, top + 28)])
            px(s, "ink7" if crown_glow else "shadow2", cx + dx + 2, top + 27)
    # orb in the left hand
    if orb > 0:
        ox, oy = orb_at[0], orb_at[1] - 14
        r = 7 * orb
        circle(s, "shadow0", ox, oy, r + 3)
        circle(s, "shadow1", ox, oy, r)
        circle(s, "shadow2", ox - r * 0.3, oy - r * 0.3, max(1, r * 0.4))
    # smoke motes rising
    rnd = random.Random(seed)
    for i in range(10 + motes):
        x = cx + rnd.randint(-55, 55)
        y = (rnd.randint(20, 230) - lift - int(t * 9)) % 230 + 10
        col = rnd.choice(("ink2", "ink3", "shadow0"))
        circle(s, col, x, y, rnd.choice((1, 1, 2)))
    return s


def dissolve(s, k, n):
    """Fade-out frame: pixels drop away in a stable pattern and become motes (no alpha)."""
    out = s.copy()
    rnd = random.Random(3)
    keep = 1 - (k + 1) / n
    for y in range(H):
        for x in range(W):
            if rnd.random() > keep and out.get_at((x, y)).a:
                out.set_at((x, y), (0, 0, 0, 0))
                if rnd.random() < 0.04:
                    px(out, "shadow1" if rnd.random() < 0.5 else "ink3", x, max(0, y - k * 6))
    return out


def main():
    sh = Sheet("shadow_king", W, H, origin=[96, 250])
    sh.add("idle", [king(t=i * 1.57, seed=i) for i in range(4)], 4)
    sh.add("float", [king(t=i * 1.57, lift=round(4 + math.sin(i * 1.57) * 4), seed=i + 4) for i in range(4)], 6)
    sh.add("cast", [king(arms=a, orb=o, crown_glow=g, seed=i + 8)
                    for i, (a, o, g) in enumerate(((0.1, 1, 0), (0.4, 1.3, 0), (0.7, 1.6, 0), (1, 2, 1), (1, 2.3, 1), (0.5, 1, 0)))],
           10, False)
    sh.add("summon", [king(arms=0.6 + 0.4 * math.sin(i), orb=1 + i * 0.2, motes=i * 6, seed=i + 14) for i in range(6)], 10, False)
    sh.add("blade", [king(blade=-120, seed=20), king(blade=-40, seed=21), king(blade=40, seed=22), king(blade=80, seed=23)],
           10, False)
    sh.add("hurt", [flash(king(), "ink7"), king(t=1, lift=-2)], 12, False)
    base = king()
    sh.add("fade_out", [dissolve(base, k, 8) for k in range(8)], 8, False)
    sh.save()


if __name__ == "__main__":
    main()
