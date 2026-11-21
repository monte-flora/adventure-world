"""Build Shadowfall's own pixel font from the hand-drawn glyphs in glyphs.py.

Standard library only (no fontTools, no PIL), so it runs with any Python 3:

    python spikes/font/make_font.py        # -> assets/fonts/

Writes, for each size: a PNG glyph sheet + JSON metrics (advance, kerning) and,
for body and small, a TTF with square-pixel outlines. Also a title style (body
letters cut 4x with bevelled corners, with outline and shading), the "Shadowfall" logo and a
preview of HUD + dialogue text in the Shadowfall 32 palette.
"""
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphs as G  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "fonts")
UNITS_PER_PIXEL = 64

# Shadowfall 32 (docs/teen/art/README.md). Only the colours used here.
PAL = {
    "ink0": 0x0B0A12, "ink1": 0x1A1626, "ink2": 0x2B2540, "ink3": 0x463D5E,
    "ink4": 0x6B6187, "ink5": 0x9C93B0, "ink6": 0xD6D0E0, "ink7": 0xF4F1EA,
    "moss1": 0x1F4031, "moss2": 0x2F6142, "earth1": 0x4A2F25, "earth4": 0xD9A95F,
    "water2": 0x2C5A85, "ember1": 0x7A1C2E, "ember2": 0xC23A3A, "ember3": 0xF0784A,
    "light0": 0xF7C64A, "light1": 0xFFF2A8,
    "shadow0": 0x2A0F3D, "shadow1": 0x5A1F78, "shadow2": 0xA04CE0,
}


def rgb(name, a=255):
    v = PAL[name]
    return (v >> 16, (v >> 8) & 255, v & 255, a)


# ---------------------------------------------------------------- font sizes
SIZES = {
    # cap: cap height; ascent/descent: px above/below the baseline in one line.
    "body": dict(src=G.BODY, cap=10, x_height=7, ascent=12, descent=4, spacing=1,
                 family="Shadowfall Body", lower_from_upper=False),
    "small": dict(src=G.SMALL, cap=7, x_height=7, ascent=8, descent=2, spacing=1,
                  family="Shadowfall Small", lower_from_upper=True),
}
ASCII = [chr(c) for c in range(32, 127)]


class Font:
    """Bitmaps + metrics for one size. glyph[cp] = list of rows (lists of 0/1),
    rows indexed from the line top (row 0 = top of the line box)."""

    def __init__(self, name, spec):
        self.name, self.spec = name, spec
        self.cap, self.ascent, self.descent = spec["cap"], spec["ascent"], spec["descent"]
        self.line_height = self.ascent + self.descent
        top = self.ascent - self.cap          # line row of glyph row 0
        raw = G.parse(spec["src"])
        if spec["lower_from_upper"]:
            for c in range(ord("a"), ord("z") + 1):
                raw.setdefault(c, raw[c - 32])
        for alias, target in G.ALIASES.items():
            raw.setdefault(alias, raw[target])
        self.bitmaps, self.width = {}, {}
        for cp, (start, rows) in raw.items():
            w = len(rows[0])
            bm = [[0] * w for _ in range(self.line_height)]
            for i, r in enumerate(rows):
                y = top + start + i
                assert 0 <= y < self.line_height, f"{name} U+{cp:04X} leaves the line box"
                bm[y] = [1 if ch == "#" else 0 for ch in r]
            self.bitmaps[cp], self.width[cp] = bm, w
        self.advance = {cp: w + spec["spacing"] for cp, w in self.width.items()}
        missing = [c for c in ASCII if ord(c) not in self.bitmaps]
        assert not missing, f"{name}: missing {missing}"
        self.kerning = self._auto_kern()

    def _auto_kern(self):
        """-1 px for letter pairs whose closest ink (same or next row) is >= 2 px
        wider than normal spacing, e.g. 'To', 'LT', 'Ay'. Digits stay tabular."""
        letters = [c for c in ASCII if c.isalpha() or c in ".,'\"-"]
        sp = self.spec["spacing"]
        right, left = {}, {}
        for c in letters:
            bm, w = self.bitmaps[ord(c)], self.width[ord(c)]
            right[c] = [w - 1 - max(i for i, v in enumerate(r) if v) if any(r) else None for r in bm]
            left[c] = [min(i for i, v in enumerate(r) if v) if any(r) else None for r in bm]
        pairs = {}
        for a in letters:
            for b in letters:
                gaps = []
                for y in range(self.line_height):
                    if right[a][y] is None:
                        continue
                    for y2 in (y - 1, y, y + 1):
                        if 0 <= y2 < self.line_height and left[b][y2] is not None:
                            gaps.append(right[a][y] + left[b][y2] + sp)
                if gaps and min(gaps) >= sp + 2:
                    pairs[a + b] = -1
        return pairs

    def text_width(self, text):
        w, prev = 0, None
        for ch in text:
            cp = ord(ch) if ord(ch) in self.bitmaps else ord("?")
            if prev:
                w += self.kerning.get(prev + ch, 0)
            w += self.advance[cp]
            prev = ch
        return w


# ---------------------------------------------------------------- tiny image
class Image:
    def __init__(self, w, h, fill=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.px = [list(fill) for _ in range(w * h)]

    def get(self, x, y):
        return self.px[y * self.w + x]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            if c[3] == 255:
                self.px[y * self.w + x] = list(c)
            elif c[3]:
                d, a = self.px[y * self.w + x], c[3] / 255
                self.px[y * self.w + x] = [round(c[i] * a + d[i] * (1 - a)) for i in range(3)] + [max(d[3], c[3])]

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def blit(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                c = other.get(x, y)
                if c[3]:
                    self.set(ox + x, oy + y, c)

    def scaled(self, k):
        out = Image(self.w * k, self.h * k)
        for y in range(out.h):
            for x in range(out.w):
                out.px[y * out.w + x] = list(self.get(x // k, y // k))
        return out

    def save(self, path):
        raw = b"".join(b"\x00" + bytes(v for x in range(self.w) for v in self.get(x, y))
                       for y in range(self.h))

        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
        png = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
        with open(path, "wb") as f:
            f.write(png)


def draw_text(img, font, x, y, text, color):
    """Draw text with its line top at y. text may be a list of (string, colour)."""
    parts = [(text, color)] if isinstance(text, str) else text
    prev = None
    for s, col in parts:
        for ch in s:
            cp = ord(ch) if ord(ch) in font.bitmaps else ord("?")
            if prev:
                x += font.kerning.get(prev + ch, 0)
            for yy, row in enumerate(font.bitmaps[cp]):
                for xx, v in enumerate(row):
                    if v:
                        img.set(x + xx, y + yy, col)
            x += font.advance[cp]
            prev = ch
    return x


# ---------------------------------------------------------------- sheets + json
def order(font):
    return sorted(font.bitmaps)


def build_sheet(font, cols=16):
    cps = order(font)
    cw = max(font.width.values()) + 1      # 1 px gap so filtering never bleeds
    ch = font.line_height + 1
    rows = (len(cps) + cols - 1) // cols
    img = Image(cols * cw, rows * ch)
    glyphs = {}
    for i, cp in enumerate(cps):
        gx, gy = (i % cols) * cw, (i // cols) * ch
        for y, row in enumerate(font.bitmaps[cp]):
            for x, v in enumerate(row):
                if v:
                    img.set(gx + x, gy + y, (255, 255, 255, 255))
        glyphs[chr(cp)] = dict(x=gx, y=gy, w=font.width[cp], h=font.line_height,
                               advance=font.advance[cp])
    return img, glyphs


def metrics_json(font, sheet_name, glyphs, scale=1, extra=None):
    d = {
        "name": font.spec["family"] if scale == 1 else "Shadowfall Title",
        "sheet": sheet_name,
        "how_to_draw": ("Blit each glyph's rect (x, y, w, h) from the sheet with its top-left at "
                        "(pen_x, line_top); then pen_x += advance + kerning[prev+this]. "
                        "Sheet is white on clear: tint it."),
        "line_height": font.line_height * scale,
        "baseline": font.ascent * scale,
        "ascent": font.ascent * scale,
        "descent": font.descent * scale,
        "cap_height": font.cap * scale,
        "x_height": font.spec["x_height"] * scale,
        "symbols": {k: chr(v) for k, v in G.SYMBOLS.items()},
        "kerning": {k: v * scale for k, v in sorted(font.kerning.items())},
        "glyphs": glyphs,
    }
    if extra:
        d.update(extra)
    return d


# ---------------------------------------------------------------- title style
def carve(bm, width, k, cut=2):
    """Scale a bitmap k times and chip a small 45-degree bevel off every outer
    corner, like letters cut in stone."""
    h = len(bm)

    def on(x, y):
        return 0 <= y < h and 0 <= x < width and bm[y][x]
    m = Image(width * k, h * k)
    for y in range(h):
        for x in range(width):
            if not on(x, y):
                continue
            for yy in range(k):
                for xx in range(k):
                    sx = -1 if xx < cut else 1 if xx >= k - cut else 0
                    sy = -1 if yy < cut else 1 if yy >= k - cut else 0
                    if sx and sy and not on(x + sx, y) and not on(x, y + sy) and not on(x + sx, y + sy):
                        dx = xx if sx < 0 else k - 1 - xx
                        dy = yy if sy < 0 else k - 1 - yy
                        if dx + dy < cut:
                            continue
                    m.set(x * k + xx, y * k + yy, (255, 255, 255, 255))
    return m


TITLE_SCALE = 4
TITLE_PAD = 5          # room for outline and drop shadow
TITLE_RAMP = ["ink7", "ink7", "ink6", "ink6", "ink5", "ink5", "ink4", "shadow2"]


def title_glyph(font, cp):
    """Body glyph -> carved 4x mask -> shaded fill, ink0 outline, violet shadow."""
    m = carve(font.bitmaps[cp], font.width[cp], TITLE_SCALE)
    p = TITLE_PAD
    out = Image(m.w + 2 * p, m.h + 2 * p)
    ink = [(x, y) for y in range(m.h) for x in range(m.w) if m.get(x, y)[3]]
    inkset = set(ink)
    cap_top, cap_px = (font.ascent - font.cap) * TITLE_SCALE, font.cap * TITLE_SCALE
    ring = {(x + dx, y + dy) for x, y in ink for dx in range(-2, 3) for dy in range(-2, 3)
            if abs(dx) + abs(dy) <= 3}
    for x, y in ring:                    # drop shadow: the outlined shape, 3 px lower
        out.set(x + p, y + p + 3, rgb("shadow1"))
    for x, y in ring:                    # 2-px outline
        out.set(x + p, y + p, rgb("ink0"))
    for x, y in ink:                     # banded fill, light from the top
        t = (y - cap_top) / cap_px
        band = TITLE_RAMP[min(len(TITLE_RAMP) - 1, max(0, int(t * (len(TITLE_RAMP) - 1))))]
        if (x, y - 1) not in inkset or (x - 1, y) not in inkset:
            band = "light1" if t < 0.5 else "ink7"     # 1-px rim light top-left
        out.set(x + p, y + p, rgb(band))
    return out


def build_title(font, chars):
    cps = [ord(c) for c in chars]
    cells = {cp: title_glyph(font, cp) for cp in cps}
    cols = 16
    cw = max(c.w for c in cells.values()) + 1
    ch = max(c.h for c in cells.values()) + 1
    img = Image(cols * cw, ((len(cps) + cols - 1) // cols) * ch)
    glyphs = {}
    for i, cp in enumerate(cps):
        gx, gy = (i % cols) * cw, (i // cols) * ch
        img.blit(cells[cp], gx, gy)
        glyphs[chr(cp)] = dict(x=gx, y=gy, w=cells[cp].w, h=cells[cp].h,
                               advance=font.advance[cp] * TITLE_SCALE)
    return img, glyphs, cells


def draw_title(img, font, cells, x, y, text):
    """y = line top. Each title cell has TITLE_PAD px of margin on every side.
    No kerning: the 2-px outlines of neighbours just touch at normal spacing."""
    for ch in text:
        cp = ord(ch)
        img.blit(cells[cp], x - TITLE_PAD, y - TITLE_PAD)
        x += font.advance[cp] * TITLE_SCALE
    return x


# ---------------------------------------------------------------- TTF writer
def outline(bm, cap):
    """Pixel bitmap -> TrueType contours (clockwise outer, y up, baseline 0)."""
    P = UNITS_PER_PIXEL
    h = len(bm)
    edges = {}

    def add(a, b):
        if (b, a) in edges:
            del edges[(b, a)]
        else:
            edges[(a, b)] = True
    for r, row in enumerate(bm):
        for c, v in enumerate(row):
            if not v:
                continue
            y0, y1 = (cap - r - 1), (cap - r)      # in pixels, y up
            x0, x1 = c, c + 1
            # clockwise in y-up: up the left, right along the top, down the right, back along the bottom
            add((x0, y0), (x0, y1))
            add((x0, y1), (x1, y1))
            add((x1, y1), (x1, y0))
            add((x1, y0), (x0, y0))
    nxt = {}
    for a, b in edges:
        nxt.setdefault(a, []).append(b)
    contours = []
    while nxt:
        start = next(iter(nxt))
        pts, cur = [start], start
        while True:
            b = nxt[cur].pop()
            if not nxt[cur]:
                del nxt[cur]
            if b == start:
                break
            pts.append(b)
            cur = b
        # drop points in the middle of straight lines
        clean = []
        n = len(pts)
        for i in range(n):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
                clean.append((b[0] * P, b[1] * P))
        contours.append(clean)
    assert h  # silence linters
    return contours


def checksum(data):
    data += b"\0" * (-len(data) % 4)
    return sum(struct.unpack(f">{len(data) // 4}I", data)) & 0xFFFFFFFF


def name_table(family, version):
    psname = family.replace(" ", "") + "-Regular"
    strings = {
        0: "Made for Shadowfall. Released under CC0 1.0 (public domain).",
        1: family, 2: "Regular", 3: f"{psname};{version}", 4: family,
        5: f"Version {version}", 6: psname,
        13: "CC0 1.0 Universal: no rights reserved. Use, change and share freely.",
        14: "https://creativecommons.org/publicdomain/zero/1.0/",
    }
    recs, blob = [], b""
    for nid, s in strings.items():
        enc = s.encode("utf-16-be")
        recs.append(struct.pack(">6H", 3, 1, 0x409, nid, len(enc), len(blob)))
        blob += enc
    return struct.pack(">3H", 0, len(recs), 6 + 12 * len(recs)) + b"".join(recs) + blob


def cmap_table(cmap):
    """Format 4 (BMP) subtable, shared by platform (0,3) and (3,1)."""
    segs = []
    for code in sorted(cmap):
        g = cmap[code]
        if segs and code == segs[-1][1] + 1 and g == segs[-1][2] + (code - segs[-1][0]):
            segs[-1][1] = code
        else:
            segs.append([code, code, g])
    segs.append([0xFFFF, 0xFFFF, 0])
    n = len(segs)
    sr = 2 * (1 << (n.bit_length() - 1))
    es = (n.bit_length() - 1)
    ends = b"".join(struct.pack(">H", s[1]) for s in segs)
    starts = b"".join(struct.pack(">H", s[0]) for s in segs)
    deltas = b"".join(struct.pack(">H", (s[2] - s[0]) & 0xFFFF if s[0] != 0xFFFF else 1) for s in segs)
    ranges = b"\0\0" * n
    body = struct.pack(">4H", 2 * n, sr, es, 2 * n - sr) + ends + b"\0\0" + starts + deltas + ranges
    sub = struct.pack(">3H", 4, 6 + len(body), 0) + body
    return struct.pack(">2H", 0, 2) + struct.pack(">2HI", 0, 3, 20) + struct.pack(">2HI", 3, 1, 20) + sub


def build_ttf(font, path, version="1.000"):
    P = UNITS_PER_PIXEL
    upem = font.line_height * P
    top = font.ascent - font.cap
    cps = [cp for cp in order(font)]
    # one glyph per distinct bitmap (aliases share)
    gid_of_bm, glyph_bms, cmap = {}, [None], {}
    adv = [font.advance[ord(" ")] * P]
    for cp in cps:
        key = (tuple(map(tuple, font.bitmaps[cp])), font.advance[cp])
        if key not in gid_of_bm:
            gid_of_bm[key] = len(glyph_bms)
            glyph_bms.append(font.bitmaps[cp])
            adv.append(font.advance[cp] * P)
        cmap[cp] = gid_of_bm[key]
    # glyph 0 (.notdef): an empty box
    w0 = 5
    nd = [[0] * w0 for _ in range(font.line_height)]
    for y in range(top, font.ascent):
        for x in range(w0):
            if x in (0, w0 - 1) or y in (top, font.ascent - 1):
                nd[y][x] = 1
    glyph_bms[0] = nd
    adv[0] = (w0 + 1) * P

    glyf, loca, hmtx = b"", [], b""
    bbox_all = [0, 0, 0, 0]
    max_pts = max_ct = 0
    lsbs = []
    for bm in glyph_bms:
        loca.append(len(glyf))
        # glyph row y in line box -> glyph row r relative to cap top: r = y - top
        cons = outline([row for row in bm[top:]], font.cap) if any(map(any, bm)) else []
        # rows above the cap (y < top) would be lost; assert none
        assert not any(map(any, bm[:top])), "ink above cap top"
        if not cons:
            lsbs.append(0)
            continue
        xs = [p[0] for c in cons for p in c]
        ys = [p[1] for c in cons for p in c]
        bb = (min(xs), min(ys), max(xs), max(ys))
        bbox_all = [min(bbox_all[0], bb[0]), min(bbox_all[1], bb[1]),
                    max(bbox_all[2], bb[2]), max(bbox_all[3], bb[3])]
        lsbs.append(bb[0])
        npts = sum(len(c) for c in cons)
        max_pts, max_ct = max(max_pts, npts), max(max_ct, len(cons))
        g = struct.pack(">h4h", len(cons), *bb)
        end = -1
        for c in cons:
            end += len(c)
            g += struct.pack(">H", end)
        g += struct.pack(">H", 0)                       # no instructions
        g += b"\x01" * npts                             # all on-curve, int16 deltas
        px = py = 0
        xd, yd = b"", b""
        for c in cons:
            for x, y in c:
                xd += struct.pack(">h", x - px)
                yd += struct.pack(">h", y - py)
                px, py = x, y
        g += xd + yd
        g += b"\0" * (-len(g) % 4)
        glyf += g
    loca.append(len(glyf))
    n = len(glyph_bms)
    for a, l in zip(adv, lsbs):
        hmtx += struct.pack(">Hh", a, l)

    asc, desc = font.ascent * P, font.descent * P
    when = 3_900_000_000                                 # fixed date: reproducible files
    head = struct.pack(">IIIIHHqq4hHHhhh", 0x00010000, 0x00010000, 0, 0x5F0F3CF5, 0b1011, upem,
                       when, when, *bbox_all, 0, font.line_height, 2, 1, 0)
    hhea = struct.pack(">I3hH3h3h4hhH", 0x00010000, asc, -desc, 0, max(adv),
                       min(lsbs), 0, bbox_all[2], 1, 0, 0, 0, 0, 0, 0, 0, n)
    maxp = struct.pack(">IH13H", 0x00010000, n, max_pts, max_ct, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0)
    first, last = min(cmap), max(cmap)
    os2 = struct.pack(">HhHHH11h10B4I4sHHH3hHHIIhhHHH",
                      4, sum(adv) // n, 400, 5, 0,
                      upem // 2, upem // 2, 0, P * 2, upem // 2, upem // 2, 0, asc // 2,
                      P, (font.spec["x_height"] // 2) * P, 0,
                      2, 0, 6, 9, 0, 0, 0, 0, 0, 0,         # panose: decorative-ish, regular
                      1, 0, 0, 0, b"SHDF", 0x40, first, min(last, 0xFFFF),
                      asc, -desc, 0, asc, desc, 1, 0,
                      font.spec["x_height"] * P, font.cap * P, 0, 32, 2)
    post = struct.pack(">IihhIIIII", 0x00030000, 0, -P, P, 0, 0, 0, 0, 0)
    pairs = []
    for k, v in font.kerning.items():
        a, b = cmap[ord(k[0])], cmap[ord(k[1])]
        pairs.append((a, b, v * P))
    pairs = sorted(set(pairs))
    npairs = len(pairs)
    sr = 6 * (1 << (npairs.bit_length() - 1)) if npairs else 0
    es = (npairs.bit_length() - 1) if npairs else 0
    sub = struct.pack(">4H", npairs, sr, es, 6 * npairs - sr) + b"".join(struct.pack(">HHh", *p) for p in pairs)
    kern = struct.pack(">HH", 0, 1) + struct.pack(">HHH", 0, 6 + len(sub), 0x0001) + sub

    tables = {
        b"OS/2": os2, b"cmap": cmap_table(cmap), b"glyf": glyf, b"head": head,
        b"hhea": hhea, b"hmtx": hmtx, b"kern": kern,
        b"loca": b"".join(struct.pack(">I", o) for o in loca),
        b"maxp": maxp, b"name": name_table(font.spec["family"], version), b"post": post,
    }
    tags = sorted(tables)
    nt = len(tags)
    sr = 16 * (1 << (nt.bit_length() - 1))
    out = struct.pack(">IHHHH", 0x00010000, nt, sr, nt.bit_length() - 1, nt * 16 - sr)
    offset = 12 + 16 * nt
    dirs, data = b"", b""
    for t in tags:
        d = tables[t]
        dirs += struct.pack(">4sIII", t, checksum(d), offset + len(data), len(d))
        data += d + b"\0" * (-len(d) % 4)
    font_bytes = bytearray(out + dirs + data)
    adj = (0xB1B0AFBA - checksum(bytes(font_bytes))) & 0xFFFFFFFF
    hoff = offset + sum(len(tables[t]) + (-len(tables[t]) % 4) for t in tags[:tags.index(b"head")])
    font_bytes[hoff + 8:hoff + 12] = struct.pack(">I", adj)
    with open(path, "wb") as f:
        f.write(bytes(font_bytes))


# ---------------------------------------------------------------- preview
def nine_box(img, x, y, w, h):
    img.rect(x, y, w, h, rgb("ink1"))
    for xx in range(x, x + w):
        img.set(xx, y, rgb("ink4"))
        img.set(xx, y + h - 1, rgb("ink4"))
    for yy in range(y, y + h):
        img.set(x, yy, rgb("ink4"))
        img.set(x + w - 1, yy, rgb("ink4"))
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        img.set(cx, cy, rgb("ink0"))             # cut corners


def preview(body, small, cells):
    W, H = 960, 540
    img = Image(W, H, rgb("ink0"))
    # a dark cave floor of 32-px tiles so the text is seen on real-looking ground
    for ty in range(0, H, 32):
        for tx in range(0, W, 32):
            base = "ink2" if (tx // 32 + ty // 32) % 2 else "ink1"
            img.rect(tx, ty, 32, 32, rgb(base))
            img.rect(tx, ty, 32, 1, rgb("ink3"))
            img.rect(tx, ty + 31, 32, 1, rgb("ink0"))
    hx, hy = 480, 300                                    # hero stand-in
    img.rect(hx - 8, hy - 24, 16, 24, rgb("ink6"))       # hero stand-in
    img.rect(hx - 8, hy - 24, 16, 1, rgb("ink0"))

    # HUD top-left: hearts + Light Stones (small font)
    H_, S_, C_ = chr(G.SYMBOLS["heart"]), chr(G.SYMBOLS["light_stone"]), chr(G.SYMBOLS["coin"])
    x = 12
    for i in range(5):
        x = draw_text(img, small, x, 10, H_, rgb("ember2" if i < 3 else "ink3")) + 1
    draw_text(img, small, 12, 24, [(S_, rgb("light0")), (" x 12", rgb("ink6"))], None)
    # HUD top-right: gold
    gold = "1,250"
    gw = small.text_width(C_ + " " + gold)
    draw_text(img, small, W - 12 - gw, 10, [(C_, rgb("light0")), (" " + gold, rgb("ink7"))], None)
    draw_text(img, small, W - 12 - small.text_width("THE DEEP HOLD"), 24, "the deep hold", rgb("ink5"))

    # title logo, top centre
    tw = sum(body.advance[ord(c)] for c in "Shadowfall") * TITLE_SCALE
    draw_title(img, body, cells, (W - tw) // 2, 52, "Shadowfall")

    # specimen panel
    nine_box(img, 40, 130, 250, 120)
    y = 138
    for line, f, col in (("ABCDEFGHIJKLM", body, "ink7"), ("NOPQRSTUVWXYZ", body, "ink7"),
                         ("abcdefghijklm", body, "ink6"), ("nopqrstuvwxyz", body, "ink6"),
                         ("0123456789 !?.,:;'\"()+-=/", body, "ink5"),
                         ("SMALL: HP 7/10  LV 4  0123456789", small, "ink6")):
        draw_text(img, f, 48, y, line, rgb(col))
        y += f.line_height + 1
    keys = "".join(chr(G.SYMBOLS[k]) for k in ("key_up", "key_down", "key_left", "key_right", "key_r"))
    draw_text(img, body, 48, y, [(keys, rgb("ink6")), ("  " + H_ + S_ + C_, rgb("light0"))], None)
    sx = 360
    draw_text(img, small, sx, 140, [(chr(G.SYMBOLS["key_r"]), rgb("ink6")), (" LANTERN", rgb("ink6"))], None)
    draw_text(img, small, sx, 152, [(chr(G.SYMBOLS["key_left"]) + chr(G.SYMBOLS["key_right"]), rgb("ink6")),
                                     (" MOVE", rgb("ink6"))], None)

    # dialogue box: 3 lines, ink1 fill, ink4 border, light0 for the key word
    bx, by, bw = 120, 412, 720
    bh = 3 * body.line_height + 2 * 10 + 12
    nine_box(img, bx, by, bw, bh)
    draw_text(img, small, bx + 12, by + 8, "WARDEN ORRIC OF THE ASHEN GATE", rgb("ember3"))
    ty = by + 8 + small.line_height + 2
    lines = [
        [("The Shadow King's host gathers beyond the Ashen Gate. Find the ", rgb("ink6"))],
        [("Light Stones", rgb("light0")), (" before the last beacon dies, or the realm falls to night.", rgb("ink6"))],
        [("Press ", rgb("ink6")), (chr(G.SYMBOLS["key_r"]), rgb("ink7")),
         (" to kindle your lantern. Steel yourself, Lightbearer.", rgb("ink6"))],
    ]
    for ln in lines:
        draw_text(img, body, bx + 12, ty, ln, None)
        ty += body.line_height
    draw_text(img, small, bx + bw - 16, by + bh - 12, chr(G.SYMBOLS["key_down"]), rgb("ink5"))
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    fonts = {name: Font(name, spec) for name, spec in SIZES.items()}
    for name, f in fonts.items():
        sheet, glyphs = build_sheet(f)
        sheet.save(os.path.join(OUT, f"shadowfall_{name}.png"))
        with open(os.path.join(OUT, f"shadowfall_{name}.json"), "w") as fh:
            json.dump(metrics_json(f, f"shadowfall_{name}.png", glyphs), fh, indent=1, ensure_ascii=True)
            fh.write("\n")
        build_ttf(f, os.path.join(OUT, f"Shadowfall{name.title()}.ttf"))
        print(f"{name}: {len(glyphs)} glyphs, {len(f.kerning)} kerning pairs, sheet {sheet.w}x{sheet.h}")
    body = fonts["body"]
    tchars = [c for c in ASCII]
    tsheet, tglyphs, cells = build_title(body, tchars)
    tsheet.save(os.path.join(OUT, "shadowfall_title.png"))
    tj = metrics_json(body, "shadowfall_title.png", tglyphs, scale=TITLE_SCALE, extra={
        "how_to_draw": (f"Pre-coloured (outline, shading, shadow): do not tint. Each rect has "
                        f"{TITLE_PAD} px of margin, so blit it at (pen_x - {TITLE_PAD}, line_top - {TITLE_PAD}); "
                        "then pen_x += advance (no kerning: outlines would overlap)."),
        "margin": TITLE_PAD, "kerning": {}})
    with open(os.path.join(OUT, "shadowfall_title.json"), "w") as fh:
        json.dump(tj, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    print(f"title: {len(tglyphs)} glyphs, sheet {tsheet.w}x{tsheet.h}")
    tw = sum(body.advance[ord(c)] for c in "Shadowfall") * TITLE_SCALE
    logo = Image(tw + 2 * TITLE_PAD + 2, body.line_height * TITLE_SCALE + 2 * TITLE_PAD)
    draw_title(logo, body, cells, TITLE_PAD, TITLE_PAD, "Shadowfall")
    logo.save(os.path.join(OUT, "shadowfall_logo.png"))
    print(f"logo: {logo.w}x{logo.h}")
    pv = preview(body, fonts["small"], cells)
    pv.save(os.path.join(OUT, "preview_960x540.png"))
    pv.scaled(2).save(os.path.join(OUT, "preview.png"))
    print("preview: preview.png (2x) and preview_960x540.png")


if __name__ == "__main__":
    main()
