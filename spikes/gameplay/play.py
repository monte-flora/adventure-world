"""
Try the feel numbers: /path/to/python spikes/gameplay/play.py   (Esc quits)
Keys: arrows move, SPACE jump (hold = higher), R attack (UP+R up, DOWN+R in the air = down strike / pogo),
SHIFT dash. Gamepad: stick / d-pad, A jump, X attack, RB or RT dash.
The dummy (red) and the spikes (^) can be pogoed. Touching the dummy or the spikes hurts: knockback,
i-frames, hit-stop, shake. Placeholder boxes only: no art.
"""
import os
import random
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feel  # noqa: E402

ROOM = [
    "########################################",
    "#......................................#",
    "#......................................#",
    "#..............................#.......#",
    "#..........======..............#.......#",
    "#..............................#.......#",
    "#......................###.....#.......#",
    "#...........................#..#.......#",
    "#.....###...................#..#.......#",
    "#...........................#..........#",
    "#.................###.......#..........#",
    "#..................................^^^^#",
    "########################################",
]
T = 24  # pixels per tile in this spike


def solid(tx, ty):
    if 0 <= ty < len(ROOM) and 0 <= tx < len(ROOM[0]):
        return ROOM[ty][tx] in "#="
    return True


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def main():
    pygame.init()
    screen = pygame.display.set_mode((len(ROOM[0]) * T, len(ROOM) * T))
    pygame.display.set_caption("Shadowfall feel spike")
    clock = pygame.time.Clock()
    pads = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    body = feel.Body(3.0, 12.0, solid)
    dummy = [22.0, 12.0, 0]            # x, feet y, flash frames
    spikes = (36.0, 11.4, 40.0, 12.0)
    frames = int(os.environ.get("SPIKE_FRAMES", "0"))  # >0: run this many frames then quit (smoke test)
    n = 0
    while True:
        jump_pressed = attack_pressed = dash_pressed = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                return
            if e.type == pygame.KEYDOWN:
                jump_pressed |= e.key == pygame.K_SPACE
                attack_pressed |= e.key == pygame.K_r
                dash_pressed |= e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT)
            if e.type == pygame.JOYBUTTONDOWN:
                jump_pressed |= e.button == 0
                attack_pressed |= e.button == 2
                dash_pressed |= e.button == 5
            if e.type == pygame.JOYAXISMOTION and e.axis == 5 and e.value > 0.5:
                dash_pressed = True
        k = pygame.key.get_pressed()
        move = (k[pygame.K_RIGHT] - k[pygame.K_LEFT])
        up, down, held = k[pygame.K_UP], k[pygame.K_DOWN], k[pygame.K_SPACE]
        for p in pads:
            ax = p.get_axis(0) if p.get_numaxes() else 0
            hat = p.get_hat(0) if p.get_numhats() else (0, 0)
            move = move or (1 if ax > 0.4 or hat[0] > 0 else -1 if ax < -0.4 or hat[0] < 0 else 0)
            down = down or (p.get_numaxes() > 1 and p.get_axis(1) > 0.5) or hat[1] < 0
            up = up or (p.get_numaxes() > 1 and p.get_axis(1) < -0.5) or hat[1] > 0
            held = held or p.get_button(0)
        frozen = body.hitstop > 0
        body.step(move, up, down, jump_pressed, held, dash_pressed, attack_pressed)

        me = (body.x - feel.PLAYER_W / 2, body.y - feel.PLAYER_H, body.x + feel.PLAYER_W / 2, body.y)
        dbox = (dummy[0] - 0.5, dummy[1] - 1.5, dummy[0] + 0.5, dummy[1])
        sword = body.attack_box()
        if not frozen and sword:
            if overlap(sword, dbox) and not dummy[2]:
                dummy[2] = 12
                if body.attack_dir == "down":
                    body.pogo()
                else:
                    body.juice("hit")
                    if body.on_ground:
                        body.vx, body.recoil = -body.facing * feel.RECOIL_SPEED, feel.RECOIL_FRAMES
            elif body.attack_dir == "down" and overlap(sword, spikes):
                body.pogo()
        if not frozen and (overlap(me, dbox) or overlap(me, spikes)):
            body.hurt(dummy[0] if overlap(me, dbox) else body.x - body.facing)
        dummy[2] = max(0, dummy[2] - 1)

        sx = sy = 0
        if body.shake[1]:
            sx, sy = random.randint(-body.shake[0], body.shake[0]), random.randint(-body.shake[0], body.shake[0])
        screen.fill((18, 16, 28))
        for ty, row in enumerate(ROOM):
            for tx, c in enumerate(row):
                if c in "#=":
                    pygame.draw.rect(screen, (70, 66, 96) if c == "#" else (110, 90, 60),
                                     (tx * T + sx, ty * T + sy, T, T if c == "#" else T // 3))
                elif c == "^":
                    pygame.draw.polygon(screen, (200, 200, 220), [(tx * T + sx, (ty + 1) * T + sy),
                                        (tx * T + T // 2 + sx, ty * T + T // 2 + sy), ((tx + 1) * T + sx, (ty + 1) * T + sy)])

        def rect(b):
            return pygame.Rect(b[0] * T + sx, b[1] * T + sy, (b[2] - b[0]) * T, (b[3] - b[1]) * T)
        pygame.draw.rect(screen, (255, 255, 255) if dummy[2] else (190, 60, 70), rect(dbox))
        if not (body.iframes and (body.iframes // 4) % 2):
            pygame.draw.rect(screen, (120, 220, 255) if body.dash else (240, 200, 90), rect(me))
        if sword:
            pygame.draw.rect(screen, (255, 255, 200), rect(sword), 2)
        pygame.display.flip()
        clock.tick(60)
        n += 1
        if frames and n >= frames:
            return


if __name__ == "__main__":
    main()
    pygame.quit()
