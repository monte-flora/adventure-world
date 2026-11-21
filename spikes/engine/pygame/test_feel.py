"""Headless checks of the spike's game feel: python -m pytest spikes/engine/pygame -q"""
import feel

FLAT = ["#" * 20] + ["#" + "." * 18 + "#"] * 8 + ["#" * 10 + "." * 10, "#" * 10 + "." * 10]
T = feel.TILE
FLOOR = 9 * T          # floor top is row 9 for columns 0..9, a drop after that


def settle(b, level=FLAT):
    for _ in range(120):
        feel.platform(b, level, 0, False, False, 1 / 60)
    return b


def run_off_ledge(extra):
    """Run right off the ledge at column 10, press jump `extra` seconds after leaving it."""
    b = settle(feel.Body(8.1 * T, 6 * T))
    assert b.on_floor
    t_left = None
    for _ in range(600):
        feel.platform(b, FLAT, 1, False, False, 1 / 240)
        if not b.on_floor:
            t_left = 0.0
            break
    assert t_left is not None
    for _ in range(round(extra * 240)):
        feel.platform(b, FLAT, 1, False, False, 1 / 240)
    vy0 = b.vy
    feel.platform(b, FLAT, 1, True, True, 1 / 240)
    return b.vy < 0 and vy0 >= 0


def test_lands_on_floor():
    b = settle(feel.Body(2.5 * T, 2.5 * T))
    assert b.on_floor and abs(b.y + b.h - FLOOR) < 1e-6


def test_coyote_jump_inside_window():
    assert run_off_ledge(0.06)


def test_no_jump_after_coyote_window():
    assert not run_off_ledge(0.15)


def test_jump_buffer():
    b = settle(feel.Body(2.5 * T, 2.5 * T))
    feel.platform(b, FLAT, 0, True, True, 1 / 60)      # jump
    while b.vy <= 0:
        feel.platform(b, FLAT, 0, False, True, 1 / 60)
    # falling: press jump a bit before landing
    while b.y + b.h < FLOOR - T / 2:
        feel.platform(b, FLAT, 0, False, True, 1 / 240)
    jumps = b.jumps
    feel.platform(b, FLAT, 0, True, True, 1 / 240)
    for _ in range(int(0.09 * 240)):
        feel.platform(b, FLAT, 0, False, True, 1 / 240)
    assert b.jumps == jumps + 1


def test_short_hop_lower_than_full_jump():
    def peak(hold):
        b = settle(feel.Body(2.5 * T, 2.5 * T))
        top = b.y
        feel.platform(b, FLAT, 0, True, True, 1 / 60)
        for _ in range(60):
            feel.platform(b, FLAT, 0, False, hold, 1 / 60)
            top = min(top, b.y)
        return FLOOR - b.h - top
    assert peak(False) < 0.6 * peak(True)
    assert 2.5 * T < peak(True) < 3 * T


def test_same_result_at_30_and_144_fps():
    def go(fps):
        b = feel.Body(2.5 * T, 2.5 * T)
        for _ in range(fps * 2):
            feel.walk(b, FLAT, 1, 0, 1 / fps)
        return b.x
    assert abs(go(30) - go(144)) < 1.0
