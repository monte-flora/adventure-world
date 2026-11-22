"""Shadowfall's own pixel font (assets/fonts/, built by spikes/font/make_font.py)."""
import json
import os
import struct

import pytest

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
ASCII = [chr(c) for c in range(32, 127)]
SYMBOLS = {"heart", "light_stone", "coin", "key_up", "key_down", "key_left", "key_right", "key_r"}


def load(size):
    with open(os.path.join(FONTS, f"shadowfall_{size}.json")) as f:
        return json.load(f)


@pytest.mark.parametrize("size", ["body", "small", "title"])
def test_every_ascii_glyph_is_in_the_sheet(size):
    font = load(size)
    with open(os.path.join(FONTS, font["sheet"]), "rb") as f:
        head = f.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n"
    sheet_w, sheet_h = struct.unpack(">II", head[16:24])
    missing = [c for c in ASCII if c not in font["glyphs"]]
    assert not missing, f"{size} is missing {missing}"
    for ch, g in font["glyphs"].items():
        assert g["advance"] > 0, ch
        assert 0 <= g["x"] and g["x"] + g["w"] <= sheet_w and g["y"] + g["h"] <= sheet_h, ch


@pytest.mark.parametrize("size", ["body", "small"])
def test_game_symbols_have_glyphs(size):
    font = load(size)
    assert set(font["symbols"]) == SYMBOLS
    for name, ch in font["symbols"].items():
        assert ch in font["glyphs"], name
    for pair in font["kerning"]:
        assert len(pair) == 2 and all(c in font["glyphs"] for c in pair)


@pytest.mark.parametrize("name", ["ShadowfallBody.ttf", "ShadowfallSmall.ttf"])
def test_ttf_files_are_truetype(name):
    with open(os.path.join(FONTS, name), "rb") as f:
        assert f.read(4) == b"\x00\x01\x00\x00"
