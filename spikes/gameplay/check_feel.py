"""Measure the spike's numbers headless: python spikes/gameplay/check_feel.py (prints a table, exits 1 on a miss)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feel  # noqa: E402


def floor_only(tx, ty):
    return ty >= 10


def run(frames, **inputs_by_frame):
    """inputs_by_frame: fn(frame) -> dict of Body.step kwargs."""
    b = feel.Body(5.0, 10.0, floor_only)
    b.step()  # settle on the floor
    top, xs, log = b.y, [], []
    for f in range(frames):
        b.step(**inputs_by_frame["fn"](f, b))
        top = min(top, b.y)
        xs.append(b.x)
        log.append((f, b.on_ground))
    return b, 10.0 - top, xs, log


def main():
    rows = []
    # full jump: hold jump the whole way
    b, h, _, log = run(90, fn=lambda f, b: {"jump_pressed": f == 0, "jump_held": True})
    land = next(f for f, g in log[1:] if g)
    rows.append(("full jump height (tiles)", h, 3.1, 3.5))
    rows.append(("full jump air time (s)", land / 60, 0.6, 0.8))
    # short hop: a quick tap (jump held 4 frames)
    _, h, _, _ = run(90, fn=lambda f, b: {"jump_pressed": f == 0, "jump_held": f < 4})
    rows.append(("short hop height (tiles)", h, 1.1, 1.6))
    # double jump at the top of a full jump
    _, h, _, _ = run(120, fn=lambda f, b: {"jump_pressed": f in (0, 23), "jump_held": True})
    rows.append(("jump + double jump (tiles)", h, 5.0, 6.0))
    # time to top speed
    b = feel.Body(5.0, 10.0, floor_only)
    b.step()
    n = 0
    while b.vx < feel.RUN_MAX - 1e-6 and n < 60:
        b.step(move=1)
        n += 1
    rows.append(("frames to run speed", n, 5, 7))
    # stop
    m = 0
    while b.vx > 0 and m < 60:
        b.step()
        m += 1
    rows.append(("frames to stop", m, 3, 5))
    # dash distance from standstill
    b = feel.Body(5.0, 10.0, floor_only)
    b.step()
    x0 = b.x
    for f in range(feel.DASH_FRAMES):
        b.step(dash_pressed=f == 0)
    rows.append(("dash distance (tiles)", b.x - x0, 5.0, 6.0))
    # long jump: run + full jump horizontal reach
    b = feel.Body(0.0, 10.0, floor_only)
    b.step()
    for _ in range(20):
        b.step(move=1)
    x0, f = b.x, 0
    b.step(move=1, jump_pressed=True, jump_held=True)
    while not b.on_ground and f < 120:
        b.step(move=1, jump_held=True)
        f += 1
    rows.append(("running jump distance (tiles)", b.x - x0, 4.5, 6.0))
    # pogo bounce height
    b = feel.Body(5.0, 5.0, floor_only)
    b.vy = 0
    b.pogo()
    b.step()  # hit-stop frames
    top = b.y
    for _ in range(80):
        b.step(jump_held=True)
        top = min(top, b.y)
    rows.append(("pogo bounce height (tiles)", 5.0 - top, 2.3, 3.0))

    bad = 0
    print("%-32s %8s   %s" % ("measure", "value", "target"))
    for name, v, lo, hi in rows:
        ok = lo <= v <= hi
        bad += not ok
        print("%-32s %8.2f   %.1f-%.1f %s" % (name, v, lo, hi, "" if ok else "  <-- MISS"))
    print("gravity %.1f t/s^2, jump speed %.1f t/s" % (feel.GRAVITY, feel.JUMP_SPEED))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
