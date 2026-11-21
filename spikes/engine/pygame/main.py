"""Engine spike (pygame): a top-down walk with a scrolling camera, then a side-view jump with coyote time.

    python main.py            # play: arrows walk/run, SPACE jumps, TAB switches scene, ESC quits
    python main.py --bench    # a robot plays 10 s of each scene, then frame times go to bench_pygame.json
    python main.py --bench --pixel   # same, but drawn at 960x540 and scaled up 2x (camera snaps to whole pixels)

Smooth mode (the default) draws at the window size with pre-scaled tiles, so the camera can move by
1 screen pixel (1/4 of a game pixel). Pixel mode is how most pygame games scale and shows the stair-step.
The dark: a dark layer with a soft hole of light around the hero, multiplied over the picture.
Runs in a browser with pygbag (the loop is async).
"""
import asyncio
import json
import math
import os
import sys
import time

import pygame


def mean(xs):
    return sum(xs) / len(xs)


def pstdev(xs):     # not the statistics module: pygbag mistakes it for a PyPI package
    m = mean(xs)
    return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5

import feel

WEB = sys.platform == "emscripten"
BENCH = "--bench" in sys.argv or WEB     # in a browser the robot runs and the numbers show on screen
PIXEL = "--pixel" in sys.argv
W, H, SCALE = 960, 540, 2          # native 960x540 (32-px tiles), window 1920x1080
SECONDS = 10.0
GLOOM = 0.7         # how dark the world is (0 none, 1 darkest)

TOP = ["#" * 80] + ["#" + "".join("#" if (c * 7 + r * 13) % 23 == 0 else "." for c in range(78)) + "#"
                    for r in range(1, 59)] + ["#" * 80]
SIDE = ["#" * 120] + ["#" + "." * 118 + "#" for _ in range(14)]
for c in range(4, 118, 9):                          # ledges with gaps
    SIDE[10 - (c // 9) % 3] = SIDE[10 - (c // 9) % 3][:c] + "#####" + SIDE[10 - (c // 9) % 3][c + 5:]
SIDE += ["#" + "".join("." if 30 < c % 40 < 35 else "#" for c in range(1, 119)) + "#"] * 3  # floor with pits
SIDE = SIDE[:15] + SIDE[-3:]


def tiles(scale):
    t = feel.TILE * scale
    wall = pygame.Surface((t, t))
    wall.fill((54, 48, 70))
    pygame.draw.rect(wall, (84, 76, 104), (0, 0, t, t // 4))
    pygame.draw.rect(wall, (36, 32, 48), (0, 0, t, t), max(1, scale))
    floor = pygame.Surface((t, t))
    floor.fill((40, 72, 52))
    pygame.draw.circle(floor, (52, 92, 64), (t // 3, t // 3), max(1, t // 8))
    return wall, floor


def light_mask(size, gloom):
    """A dark layer (multiply) with a soft round light in the middle."""
    dark = int(255 * (1 - gloom))
    mask = pygame.Surface(size)
    mask.fill((dark, dark, int(dark * 1.2) if dark < 200 else dark))
    r = size[1] // 2
    glow = pygame.Surface((r * 2, r * 2))
    glow.fill((0, 0, 0))
    for i in range(r, 0, -2):
        v = int((255 - dark) * (1 - i / r) ** 0.7)
        pygame.draw.circle(glow, (v, v, v), (r, r), i)
    return mask, glow


class Spike:
    def __init__(self, screen):
        self.screen = screen
        self.scale = 1 if PIXEL else SCALE
        self.canvas = pygame.Surface((W, H)) if PIXEL else screen
        self.wall, self.floor = tiles(self.scale)
        size = self.canvas.get_size()
        self.mask, self.glow = light_mask(size, GLOOM)
        self.dark = pygame.Surface(size)
        self.scene = "top"
        self.reset()
        self.t = 0.0
        self.times = {"top": [], "side": []}
        self.work = {"top": [], "side": []}

    def reset(self):
        self.level = TOP if self.scene == "top" else SIDE
        self.body = feel.Body(80, 80) if self.scene == "top" else feel.Body(80, 300)
        self.cam = [self.body.x, self.body.y]

    def robot(self):
        t = self.t % 8
        if self.scene == "top":
            return [(1, 0), (0, 1), (-1, 0), (0, -1)][int(t // 2)] + (False, False)
        ix = 1 if (self.t % 16) < 8 else -1
        return ix, 0, (self.t % 0.8) < 1 / 60, (self.t % 0.8) < 0.3

    def update(self, dt, keys, pressed):
        if BENCH:
            ix, iy, jp, jh = self.robot()
        else:
            ix = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            iy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            jp, jh = pressed, keys[pygame.K_SPACE]
        if self.scene == "top":
            feel.walk(self.body, self.level, ix, iy, dt)
        else:
            feel.platform(self.body, self.level, ix, jp, jh, dt)
        # camera: eases toward the hero (frame-rate independent), clamped to the level
        k = 1 - math.exp(-10 * dt)
        for i, (p, half, size) in enumerate(((self.body.x, W / 2, len(self.level[0])),
                                             (self.body.y, H / 2, len(self.level)))):
            self.cam[i] += (p - self.cam[i]) * k
            self.cam[i] = max(half, min(size * feel.TILE - half, self.cam[i]))

    def draw(self):
        s, c = self.scale, self.canvas
        ox = round((self.cam[0] - W / 2) * s)       # in canvas pixels: whole game px (pixel) or 1/2 px (smooth)
        oy = round((self.cam[1] - H / 2) * s)
        t = feel.TILE * s
        c.fill((0, 0, 0))
        for row in range(oy // t, (oy + H * s) // t + 1):
            line = self.level[row] if 0 <= row < len(self.level) else ""
            for col in range(ox // t, (ox + W * s) // t + 1):
                if 0 <= col < len(line):
                    c.blit(self.wall if line[col] == "#" else self.floor, (col * t - ox, row * t - oy))
        b = self.body
        hx, hy = round(b.x * s) - ox, round(b.y * s) - oy
        pygame.draw.rect(c, (230, 200, 120), (hx, hy, b.w * s, b.h * s))
        # the dark
        self.dark.blit(self.mask, (0, 0))
        r = self.glow.get_width() // 2
        self.dark.blit(self.glow, (hx + b.w * s // 2 - r, hy + b.h * s // 2 - r), special_flags=pygame.BLEND_RGB_ADD)
        c.blit(self.dark, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        if PIXEL:
            pygame.transform.scale(c, self.screen.get_size(), self.screen)

    def report(self):
        out = {"engine": "pygame " + pygame.version.ver, "mode": " ".join(["pixel" if PIXEL else "smooth"] + [
               a[2:] for a in sys.argv if a in ("--busy", "--vsynconly")]),
               "driver": pygame.display.get_driver()}
        for scene, ts in self.times.items():
            ts = ts[30:]                              # skip warm-up
            if not ts:
                continue
            ms = sorted(x * 1000 for x in ts)
            out[scene] = {"frames": len(ms), "mean_ms": round(mean(ms), 3),
                          "stdev_ms": round(pstdev(ms), 3), "p99_ms": round(ms[int(len(ms) * .99)], 3),
                          "max_ms": round(ms[-1], 3), "late_over_20ms": sum(x > 20 for x in ms),
                          "work_mean_ms": round(1000 * mean(self.work[scene][30:]), 3)}
        return out


async def show(screen, result):
    """In a browser: print the numbers on the page and keep it open."""
    print(json.dumps(result))
    font = pygame.font.Font(None, 30)
    screen.fill((0, 0, 0))
    lines = [result["engine"] + " web " + result["mode"]] + [
        "%s: mean %.2f ms  stdev %.2f  p99 %.2f  late %d  work %.2f" % (
            k, v["mean_ms"], v["stdev_ms"], v["p99_ms"], v["late_over_20ms"], v["work_mean_ms"])
        for k, v in result.items() if isinstance(v, dict)]
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, (255, 255, 255)), (20, 20 + 34 * i))
    while True:
        pygame.display.flip()
        pygame.event.pump()
        await asyncio.sleep(0.5)


async def main():
    pygame.init()
    flags = pygame.SCALED     # vsync=1 only works with SCALED (or OPENGL); smooth mode is SCALED at 1:1
    try:
        screen = pygame.display.set_mode((W * SCALE, H * SCALE), flags, vsync=1)
    except pygame.error:
        screen = pygame.display.set_mode((W * SCALE, H * SCALE), flags)
    pygame.display.set_caption("Engine spike: pygame")
    spike = Spike(screen)
    clock = pygame.time.Clock()
    last = time.perf_counter()
    while True:
        pressed = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                return spike.report()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                pressed = True
            if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
                spike.scene = "side" if spike.scene == "top" else "top"
                spike.reset()
        now = time.perf_counter()
        dt, last = min(now - last, 0.1), now
        spike.times[spike.scene].append(dt)
        spike.t += dt
        w0 = time.perf_counter()
        spike.update(dt, pygame.key.get_pressed(), pressed)
        spike.draw()
        spike.work[spike.scene].append(time.perf_counter() - w0)
        pygame.display.flip()
        if "--busy" in sys.argv:
            clock.tick_busy_loop(60)        # spins for the last ms: steadier than tick()
        elif "--vsynconly" not in sys.argv:
            clock.tick(60)
        if sys.platform == "emscripten" or BENCH:
            await asyncio.sleep(0)
        if BENCH and spike.t > SECONDS:
            if spike.scene == "side":
                result = spike.report()
                if not WEB:
                    return result
                await show(screen, result)
            spike.scene, spike.t = "side", 0.0
            spike.reset()


if __name__ == "__main__":
    result = asyncio.run(main())
    print(json.dumps(result, indent=1))
    if BENCH:
        name = "bench_pygame%s%s.json" % ("_pixel" if PIXEL else "", "".join(
            "_" + a[2:] for a in sys.argv if a in ("--busy", "--vsynconly")))
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name), "w") as f:
            json.dump(result, f, indent=1)
