"""Start Adventure World in a web browser.

pygbag (https://github.com/pygame-web/pygbag) turns the game into a web page. A browser
needs the game to give it a turn after every picture it draws (so it can show the picture
and read the keyboard), so this loop says "await" once every frame.

On your own computer, play with  pixi run game  instead. To make the web page, run
web/build_web.py (see web/README.md).
"""
import asyncio
import time

import pygame

import game


def shortcuts_in_the_web_address():
    """Play-test shortcuts in the web address, like  index.html?castle  or  ?throne&fps"""
    try:
        import platform
        address = platform.window.location.search     # pygbag lets Python read the browser's address bar
    except Exception:
        return set()                                   # not in a browser
    return set(address.lstrip("?").split("&")) if address else set()


def say(message):
    """Write to the browser's console (in a browser, print() goes somewhere hidden)."""
    try:
        import platform
        platform.window.console.log(message)
    except Exception:
        print(message)


async def main():
    wanted = shortcuts_in_the_web_address()
    while True:
        await play(wanted)
        if not game.IN_BROWSER:
            break                              # on a computer, quitting closes the window
        wanted.discard("castle")               # in a browser there's nothing to close, so quitting
        wanted.discard("throne")               # starts over at the title screen
    pygame.quit()


async def play(wanted):
    """Play one game, until you quit."""
    app = game.App("", sound="mute" not in wanted, castle="castle" in wanted, throne="throne" in wanted)
    show_speed = "fps" in wanted               # ?fps prints how smoothly the game runs, every 5 seconds
    frames, seconds, game_time, show_time = 0, 0.0, 0.0, 0.0
    while app.running:
        dt = app.clock.tick(game.FPS) / 1000.0
        started = time.perf_counter()
        app.step(dt)                           # the game: move everything, then draw the picture
        drawn = time.perf_counter()
        pygame.display.flip()                  # hand the picture to the browser
        game_time += drawn - started
        show_time += time.perf_counter() - drawn
        frames += 1
        seconds += dt
        if show_speed and seconds >= 5:
            music = app.music
            say("FPS %.1f: %.1f ms game + %.1f ms showing it, per picture (%s) - music: %d tunes, playing %s"
                % (frames / seconds, 1000 * game_time / frames, 1000 * show_time / frames, app.state,
                   len(music.tunes), music.playing))
            frames, seconds, game_time, show_time = 0, 0.0, 0.0, 0.0
        await asyncio.sleep(0)                 # the browser's turn
    if pygame.mixer.get_init():
        pygame.mixer.stop()                    # hush the old game's music and sounds


if __name__ == "__main__":
    asyncio.run(main())
