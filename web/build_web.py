"""Make the web-browser version of the game.

    pixi run -e web build-web

1. Turns every tune into a small .ogg sound file. On a computer the game makes its music
   with math while you play, but a browser can't do work in the background like that.
2. Copies just the files the game needs into web/build/adventure/.
3. Runs pygbag, which turns them into a web page in web/build/adventure/build/web/
   (and web.zip next to it, ready to upload to itch.io).
"""
import os
import shutil
import subprocess
import sys
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")      # no window or speakers needed to make the files
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

HERE = os.path.dirname(os.path.abspath(__file__))
GAME_FOLDER = os.path.dirname(HERE)
sys.path.insert(0, GAME_FOLDER)

import pygame  # noqa: E402

GAME_FILES = ["main.py", "game.py", "rules.py", "caves.py", "castle.py", "throne.py", "story.py", "sprites.py",
              "tutorial.py", "settings.py"]
GAME_FOLDERS = ["levels"]   # the caves and castle levels, one text file each
GAME_FOLDERS += ["phase2"]  # and the Phase 2 code (its world map is in levels/world)
APP = os.path.join(HERE, "build", "adventure")
OGG_QUALITY = "3"           # 0 = smallest, 10 = best sounding. 3 sounds fine for our math music


def make_music(folder):
    """Every tune -> one sound file, the same sound the game makes on a computer.
    Returns True if they're .ogg files, False if ffmpeg is missing and they stayed .wav."""
    pygame.mixer.pre_init(22050, -16, 1, 512)               # the same sound settings as the game
    pygame.init()
    import game
    music = game.Music(enabled=False)
    os.makedirs(folder, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    for name, tune in game.TUNES.items():
        wav = os.path.join(folder, name + ".wav")
        with wave.open(wav, "wb") as f:
            f.setnchannels(music.channels)
            f.setsampwidth(2)                                # 16-bit sound
            f.setframerate(music.rate)
            f.writeframes(music.make(tune))
        made = wav
        if ffmpeg:                                           # squeeze it into a small .ogg file
            ogg = os.path.join(folder, name + ".ogg")
            subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis",
                            "-q:a", OGG_QUALITY, ogg], check=True)
            os.remove(wav)
            made = ogg
        print("  %-10s %5.2f MB" % (os.path.basename(made), os.path.getsize(made) / 1e6))
    if not ffmpeg:
        print("  (no ffmpeg, so the music stays in big .wav files - run this with:  pixi run -e web build-web)")
    return bool(ffmpeg)


def main():
    shutil.rmtree(APP, ignore_errors=True)
    os.makedirs(APP)
    for name in GAME_FILES:
        shutil.copy(os.path.join(GAME_FOLDER, name), APP)
    for name in GAME_FOLDERS:
        shutil.copytree(os.path.join(GAME_FOLDER, name), os.path.join(APP, name),
                        ignore=shutil.ignore_patterns("*.md", "__pycache__"))
    print("Making the music...")
    small = make_music(os.path.join(APP, "web_music"))
    print("Making the web page with pygbag...")
    command = [sys.executable, "-m", "pygbag", "--archive", APP]
    if not small:
        command.insert(3, "--disable-sound-format-error")    # pygbag would rather have .ogg files
    subprocess.run(command, check=True)
    page = os.path.join(APP, "build", "web")
    print("Done! The web page is in", page)
    print("      and", os.path.join(APP, "build", "web.zip"), "is ready to upload to itch.io")


if __name__ == "__main__":
    main()
