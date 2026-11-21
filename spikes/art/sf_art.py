"""Shadowfall teen art spike: the master palette and small drawing helpers (pygame only).

Everything here is original. The samples are made by make_samples.py.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

pygame.init()

NATIVE = (480, 270)          # game pixels; x4 = 1920x1080, x2 = 960x540, x3 = 1440x810
TILE = 16

# Shadowfall 32: the only colours any asset may use. Ramps run dark -> light, hue-shifted
# (shadows lean violet/blue, lights lean warm).
RAMPS = {
    "ink":    ["#0b0a12", "#1a1626", "#2b2540", "#463d5e", "#6b6187", "#9c93b0", "#d6d0e0", "#f4f1ea"],
    "moss":   ["#12261f", "#1f4031", "#2f6142", "#4f8a4b", "#8bbd5a"],
    "earth":  ["#2a1b17", "#4a2f25", "#74482f", "#a8703f", "#d9a95f"],
    "water":  ["#0f1d33", "#1b3557", "#2c5a85", "#4a8fb8", "#8fd0e0"],
    "ember":  ["#3d0f1f", "#7a1c2e", "#c23a3a", "#f0784a"],
    "light":  ["#f7c64a", "#fff2a8"],
    "shadow": ["#2a0f3d", "#5a1f78", "#a04ce0"],
}
PALETTE = [c for ramp in RAMPS.values() for c in ramp]
assert len(PALETTE) == 32 and len(set(PALETTE)) == 32


def rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


P = {f"{name}{i}": rgb(c) for name, ramp in RAMPS.items() for i, c in enumerate(ramp)}
INK = P["ink0"]


def nearest(colour):
    """Snap any colour to the closest palette colour (keeps palette discipline)."""
    r, g, b = colour[:3]
    return min((rgb(c) for c in PALETTE), key=lambda p: (p[0] - r) ** 2 + (p[1] - g) ** 2 * 1.3 + (p[2] - b) ** 2)


# --- the darkening world: 4 gloom stages, each a palette -> palette remap (a LUT) ---------
GLOOM_TINT = rgb("#2a0f3d")


def gloom_lut(stage):
    """stage 0 (dusk, as today) .. 3 (the Shadow King's night). A ramp-step remap: each stage
    moves a colour one step darker along its own ramp; at stage 3 the world ramps (moss, earth,
    water) drop into the grey-violet ink ramp. Accents (light, ember highs, shadow) never change,
    so lamps, eyes and danger stay bright. Always palette -> palette, always monotonic."""
    accents = set(RAMPS["light"] + RAMPS["ember"][2:] + RAMPS["shadow"])
    lut = {}
    for name, ramp in RAMPS.items():
        for i, c in enumerate(ramp):
            if stage == 0 or c in accents:
                out = c
            elif stage == 3 and name in ("moss", "earth", "water"):
                out = RAMPS["ink"][max(1, i)]
            else:
                out = ramp[max(0, i - stage)] if name != "ink" else ramp[max(0, i - (stage + 1) // 2)]
            lut[rgb(c)] = rgb(out)
    return lut


def apply_lut(surface, lut):
    out = surface.copy()
    px = pygame.PixelArray(out)
    for src, dst in lut.items():
        if src != dst:
            px.replace(src, dst)
    del px
    return out


# --- sprite helpers -------------------------------------------------------------------------
def grid(rows, key):
    """Letters -> a surface. '.' is clear. key maps letters to palette names ('moss2')."""
    w, h = max(len(r) for r in rows), len(rows)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                s.set_at((x, y), P[key[ch]])
    return s


def outline(sprite, colour=INK):
    """The 1-pixel outline rule: every clear pixel touching a filled one (4-way) turns ink."""
    w, h = sprite.get_size()
    out = sprite.copy()
    for y in range(h):
        for x in range(w):
            if sprite.get_at((x, y)).a:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and sprite.get_at((nx, ny)).a:
                    out.set_at((x, y), colour)
                    break
    return out


def scaled(surface, k):
    return pygame.transform.scale(surface, (surface.get_width() * k, surface.get_height() * k))


def drop_shadow(target, x, y, w):
    """Top-down depth cue: a flat dark oval under anything that stands on the ground."""
    sh = pygame.Surface((w, 4), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (*P["ink0"], 110), sh.get_rect())
    target.blit(sh, (x, y))


def posterize_alpha(a, steps=3):
    """Lights are banded (3 rings), never smooth gradients: keeps the pixel look."""
    return int(round(a * steps) / steps * 255)


def label(surface, text, pos, size=14, colour=P["ink7"]):
    font = pygame.font.Font(None, size)
    surface.blit(font.render(text, False, colour), pos)


def save(surface, name, scale=1):
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "..", "docs", "teen", "art", name)
    pygame.image.save(scaled(surface, scale) if scale > 1 else surface, os.path.normpath(out))
    print("saved", name)
