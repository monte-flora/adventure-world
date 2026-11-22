"""P1 prototype: makes the clean plate and the foreground cut-out for the painted Emberwick screen.

    python3 shadowfall/painted/tools/clean_plate.py [--debug out.png]

Needs Pillow + numpy (not in pixi; macOS python3 has them). Reads the user's painting
docs/teen/art/ref/overworld_target_b_characters.jpg, scales it to 960x540 and:
- erases the painted people, hero, horse and HUD (emberwick.json "erase" rects) by greedy patch
  cloning: 8-px blocks, each copied from the nearby spot whose surroundings match best;
- writes painted/emberwick_clean.png (the ground) and painted/emberwick_front.png (only the
  "front" polygons, cut from the clean plate: canopies, roofs, cliff tops; the rest transparent).
--debug draws the collision (red), front pieces (cyan) and exit (green) over the plate.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parent.parent
SRC = REPO / "docs/teen/art/ref/overworld_target_b_characters.jpg"
W, H = 960, 540
B = 8          # block size
RING = 6       # px of surroundings compared
RADIUS = 96    # search radius
STEP = 2


def fill(img: np.ndarray, hole: np.ndarray, no_source: np.ndarray) -> np.ndarray:
    img = img.copy()
    unknown = hole.copy()
    # sources must sit fully outside the original hole (grown by the ring)
    grown = np.zeros_like(hole)
    ys, xs = np.nonzero(hole)
    pad = B + RING
    bad = np.zeros((H + 2 * pad, W + 2 * pad), bool)
    bad[:pad, :] = bad[-pad:, :] = True
    bad[:, :pad] = bad[:, -pad:] = True
    bad[pad:-pad, pad:-pad] = hole | no_source     # never clone houses, fences, trees
    # bad_win[y, x]: the window at (y - RING, x - RING) of size B + 2 RING touches the hole or the edge
    from numpy.lib.stride_tricks import sliding_window_view as win
    k = B + 2 * RING
    bad_win = win(bad, (k, k)).any(axis=(2, 3))     # indexed by window top-left in padded coords
    blocks = sorted({(y // B * B, x // B * B) for y, x in zip(ys, xs)})
    todo = set(blocks)
    while todo:
        # onion peel: the block with the most known surroundings first
        def known(b):
            y, x = b
            y0, x0 = max(0, y - RING), max(0, x - RING)
            return (~unknown[y0:y + B + RING, x0:x + B + RING]).mean()
        by, bx = max(todo, key=known)
        todo.discard((by, bx))
        y0, x0 = by - RING, bx - RING
        ty0, tx0 = max(0, y0), max(0, x0)
        ty1, tx1 = min(H, by + B + RING), min(W, bx + B + RING)
        tgt = img[ty0:ty1, tx0:tx1]
        tmask = ~unknown[ty0:ty1, tx0:tx1]
        # every candidate offset at once: windows of the search area, STEP apart
        hgt, wid = ty1 - ty0, tx1 - tx0
        ay0, ax0 = max(0, ty0 - RADIUS), max(0, tx0 - RADIUS)
        ay1, ax1 = min(H, ty1 + RADIUS), min(W, tx1 + RADIUS)
        wins = win(img[ay0:ay1, ax0:ax1], (hgt, wid), axis=(0, 1))[::STEP, ::STEP]   # (ny, nx, 3, h, w)
        diff = ((wins - tgt.transpose(2, 0, 1)[None, None]) ** 2).sum(axis=2)
        d = (diff * tmask).sum(axis=(2, 3)) / max(1, tmask.sum())
        oy = ay0 + np.arange(d.shape[0]) * STEP - ty0
        ox = ax0 + np.arange(d.shape[1]) * STEP - tx0
        d = d + 0.02 * (oy[:, None] ** 2 + ox[None, :] ** 2)
        ok = ~bad_win[(by + oy - RING + pad)[:, None], (bx + ox - RING + pad)[None, :]]
        d[~ok] = np.inf
        iy, ix = np.unravel_index(np.argmin(d), d.shape)
        best = (int(oy[iy]), int(ox[ix]))
        dy, dx = best
        blk = unknown[by:by + B, bx:bx + B]
        img[by:by + B, bx:bx + B][blk] = img[by + dy:by + dy + B, bx + dx:bx + dx + B][blk]
        unknown[by:by + B, bx:bx + B] = False
    return img


def smooth_fill(low: np.ndarray, hole: np.ndarray, iters: int = 1500) -> np.ndarray:
    """Fills the hole in a blurred image by diffusing its edges inward (the light stays smooth)."""
    out = low.copy()
    out[hole] = low[~hole].mean(axis=0)
    for _ in range(iters):
        p = np.pad(out, ((1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 4.0
        out[hole] = avg[hole]
    return out


def main() -> None:
    data = json.loads((HERE / "emberwick.json").read_text())
    im = Image.open(SRC).convert("RGB").resize((W, H), Image.LANCZOS)
    img = np.asarray(im).astype(np.float32)
    hole = np.zeros((H, W), bool)
    for x, y, w, h in data["erase"]:
        hole[max(0, y):y + h, max(0, x):x + w] = True
    no_source = np.zeros((H, W), bool)
    for x, y, w, h in data["solid_rects"]:
        no_source[max(0, y):y + h, max(0, x):x + w] = True
    # light and texture apart: the smooth glow is diffused in, the detail is cloned
    from PIL import ImageFilter
    low = np.asarray(im.filter(ImageFilter.GaussianBlur(5))).astype(np.float32)
    detail = fill(img - low, hole, no_source)
    out = img.copy()
    wide = np.asarray(Image.fromarray(hole.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(17))) > 0
    out = smooth_fill(low, wide) + detail          # outside `wide` this is the painting again
    out[~wide] = img[~wide]
    clean = Image.fromarray(out.clip(0, 255).astype(np.uint8))
    clean.save(HERE / "emberwick_clean.png")
    alpha = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(alpha)
    for piece in data["front"]:
        d.polygon(piece["poly"], fill=255)
    front = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    front.paste(clean, (0, 0), alpha)
    front.save(HERE / "emberwick_front.png")
    if "--debug" in sys.argv:
        dbg = clean.convert("RGBA")
        ov = Image.new("RGBA", (W, H))
        o = ImageDraw.Draw(ov)
        for x, y, w, h in data["solid_rects"]:
            o.rectangle([x, y, x + w - 1, y + h - 1], fill=(255, 0, 0, 80), outline=(255, 0, 0, 200))
        for p in data["solid_polys"]:
            o.polygon(p, fill=(255, 0, 0, 80), outline=(255, 0, 0, 200))
        for piece in data["front"]:
            o.polygon(piece["poly"], outline=(0, 255, 255, 255))
            o.line([(min(piece["poly"][0::2]), piece["base"]), (max(piece["poly"][0::2]), piece["base"])], fill=(0, 255, 255, 255))
        x, y, w, h = data["cave_exit"]
        o.rectangle([x, y, x + w, y + h], outline=(0, 255, 0, 255))
        for p in data["people"]:
            x, y = p["at"]
            o.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 0, 255))
        Image.alpha_composite(dbg, ov).save(sys.argv[sys.argv.index("--debug") + 1])


if __name__ == "__main__":
    main()
