"""Shadowfall teen audio spike: every sound here is made by this script, from maths.

No samples, no downloads, nothing copied: the tunes below are original. Run it with any
Python 3 (standard library only). It writes .wav files, then squeezes them into .ogg
with ffmpeg if ffmpeg is on the PATH (pixi's web env has it):

    python spikes/audio/make_audio.py            # -> spikes/audio/out/*.ogg

The style is "NES rules, modern room": every tune keeps to 4 voices like an old
console (2 pulse waves, 1 triangle bass, 1 noise drum), then gets a soft echo and
a low-pass "darkness" filter that a console never had.
"""
import math
import os
import random
import shutil
import subprocess
import sys
import wave
from array import array

RATE = 22050                     # the game's mixer rate (game.py pre_init)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
OGG_QUALITY = "2"                # vorbis -q: 2 is ~64 kbps; plenty for chiptune

NOTE_STEPS = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3,
              "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}


def freq(name):
    letter, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE_STEPS[letter] + 12 * (octave - 4)) / 12)


# ----- the voices ------------------------------------------------------------------------
def osc(wave_name, phase, duty=0.5):
    """One sample of a wave, phase in [0, 1)."""
    if wave_name == "pulse":
        return 1.0 if phase < duty else -1.0
    if wave_name == "triangle":          # NES-like: 16 steps, a little gritty
        return round((4 * abs(phase - 0.5) - 1) * 7.5) / 7.5
    if wave_name == "sine":
        return math.sin(2 * math.pi * phase)
    raise ValueError(wave_name)


def envelope(j, n, attack, decay, sustain, release):
    """ADSR in samples. n = note length; the release happens inside the note."""
    if j < attack:
        return j / attack
    if j < attack + decay:
        return 1 - (1 - sustain) * (j - attack) / decay
    if j > n - release:
        return sustain * max(0.0, (n - j) / release)
    return sustain


def render_voice(notes, step, wave_name, vol, duty=0.5, adsr=(0.005, 0.08, 0.7, 0.03),
                 vibrato=0.0, length=None):
    """notes: space-separated, one per step; '-' holds, '.' rests, '|' is decoration."""
    seq = notes.replace("|", " ").split()
    n_step = int(RATE * step)
    total = length or len(seq) * n_step
    buf = [0.0] * total
    a, d, s, r = (max(1, int(RATE * x)) if i != 2 else x for i, x in enumerate(adsr))
    i = 0
    while i < len(seq):
        note, hold = seq[i], 1
        while i + hold < len(seq) and seq[i + hold] == "-":
            hold += 1
        if note not in ".-":
            f = freq(note)
            n = hold * n_step
            start = i * n_step
            phase = 0.0
            for j in range(n):
                if start + j >= total:
                    break
                vib = 1 + vibrato * math.sin(2 * math.pi * 5.5 * j / RATE) * min(1, j / (RATE * 0.25))
                phase = (phase + f * vib / RATE) % 1.0
                buf[start + j] += osc(wave_name, phase, duty) * envelope(j, n, a, d, s, r) * vol
        i += hold
    return buf


def render_noise(hits, step, vol, length=None, seed=7):
    """Noise-channel drums: k = low thud, s = snare, h = hat, c = long crash/wind."""
    seq = hits.replace("|", " ").split()
    n_step = int(RATE * step)
    total = length or len(seq) * n_step
    buf = [0.0] * total
    rng = random.Random(seed)
    for i, hit in enumerate(seq):
        if hit in ".-":
            continue
        dur = {"k": 0.14, "s": 0.10, "h": 0.03, "c": 0.9}[hit]
        n = int(RATE * dur)
        start = i * n_step
        held = 0.0
        for j in range(n):
            if start + j >= total:
                break
            fade = (1 - j / n) ** 2
            if hit == "k":       # a falling sine thump, NES-DPCM-ish
                v = math.sin(2 * math.pi * (90 - 50 * j / n) * j / RATE) * 1.4
            else:
                if hit == "s" or j % 2 == 0:   # hats/crash: sample-and-hold = "metallic" noise
                    held = rng.uniform(-1, 1)
                v = held * {"s": 0.8, "h": 0.35, "c": 0.3}[hit]
            buf[start + j] += v * fade * vol
    return buf


# ----- effects ----------------------------------------------------------------------------
def mix(*bufs):
    out = [0.0] * max(len(b) for b in bufs)
    for b in bufs:
        for i, v in enumerate(b):
            out[i] += v
    return out


def lowpass(buf, cutoff):
    """One-pole low-pass. Lower cutoff = duller, 'further away', darker."""
    a = 1 - math.exp(-2 * math.pi * cutoff / RATE)
    y, out = 0.0, []
    for v in buf:
        y += a * (v - y)
        out.append(y)
    return out


def echo(buf, delay, feedback, wet, loop=True):
    """A cave/room echo. loop=True wraps the tail to the start so the loop stays seamless."""
    d = int(RATE * delay)
    out = list(buf)
    n = len(out)
    for _ in range(2):                 # two passes so the wrapped tail settles
        for i in range(n):
            src = i - d
            if src < 0 and not loop:
                continue
            out[i] = buf[i] + out[src % n] * feedback
    return [b * (1 - wet) + o * wet for b, o in zip(buf, out)]


def sweep(f0, f1, dur, wave_name="pulse", duty=0.5, vol=0.6, curve=1.0, noise=0.0, seed=1):
    """A sound effect: pitch slides f0 -> f1 over dur seconds, fading out."""
    n = int(RATE * dur)
    rng = random.Random(seed)
    phase, out = 0.0, []
    for j in range(n):
        t = (j / n) ** curve
        phase = (phase + (f0 + (f1 - f0) * t) / RATE) % 1.0
        v = osc(wave_name, phase, duty) * (1 - noise) + rng.uniform(-1, 1) * noise
        out.append(v * vol * (1 - j / n) * min(1, j / 40))
    return out


def silence(sec):
    return [0.0] * int(RATE * sec)


def normalise(buf, peak=0.85):
    m = max(1e-9, max(abs(v) for v in buf))
    return [v * peak / m for v in buf]


def save(name, buf, peak=0.85):
    os.makedirs(OUT, exist_ok=True)
    buf = normalise(buf, peak)
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(array("h", (int(max(-1, min(1, v)) * 32767) for v in buf)).tobytes())
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        ogg = path[:-4] + ".ogg"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", path, "-c:a", "libvorbis",
                        "-q:a", OGG_QUALITY, ogg], check=True)
        os.remove(path)
        path = ogg
    print(f"{os.path.basename(path):28s} {len(buf) / RATE:5.1f} s  {os.path.getsize(path) // 1024:4d} KB")


# ----- the music: all original -------------------------------------------------------------
# THE SHADOWFALL MOTIF (the hero / the land): 5 notes, rising then falling back,
#   A3 . C4 . E4 - D4 . | B3 - - -     (A minor: hopeful start, unresolved end)
# THE SHADOW KING MOTIF: the same rhythm, but it falls, and the 4th note is a tritone
# (the "devil's interval") away from the first:  A3 G#3 F3 D#3 | E3
# Wave B reuses these two shapes everywhere (map, caves, boss, title) = leitmotifs.

def overworld():
    """The map under a darkening sky. Two stems that loop together (same length):
    overworld_base (always on) and overworld_dark (fades in as the darkness rises)."""
    bpm = 96
    step = 60 / bpm / 2                                   # eighth notes
    melody = ("A4 - C5 - E5 - D5 C5 | B4 - - - G4 - - - | A4 - C5 - E5 - G5 - | F5 - E5 - D5 - - - |"
              "C5 - D5 - E5 - A5 - | G5 - F5 - E5 - C5 - | D5 - C5 - B4 - G#4 - | A4 - - - . . . . |")
    harmony = ("E4 - - - A4 - - - | G4 - - - D4 - - - | E4 - - - C5 - - - | A4 - - - F4 - - - |"
               "A4 - - - C5 - - - | C5 - - - G4 - - - | F4 - - - E4 - - - | E4 - - - . . . . |")
    bass = ("A2 . A3 . A2 . E3 . | G2 . G3 . G2 . D3 . | F2 . F3 . F2 . C3 . | D2 . D3 . E2 . E3 . |" * 2)
    drums = ("k . h . s . h h | k . h k s . h . |" * 4)
    length = len(melody.replace("|", " ").split()) * int(RATE * step)
    base = mix(
        render_voice(melody, step, "pulse", 0.22, duty=0.25, vibrato=0.004, length=length),
        render_voice(harmony, step, "pulse", 0.10, duty=0.125, adsr=(0.02, 0.2, 0.5, 0.1), length=length),
        render_voice(bass, step, "triangle", 0.45, adsr=(0.002, 0.05, 0.8, 0.02), length=length),
        render_noise(drums, step, 0.30, length=length),
    )
    base = echo(base, step * 3, 0.25, 0.25)
    # darkness layer: a low drone a tritone under the key, plus a far-off bell playing the
    # Shadow King motif slowly, under a heavy low-pass. Alone it is just unease.
    drone = ("A1 - - - - - - - - - - - - - - - | D#2 - - - - - - - - - - - - - - - |" * 2)
    bell = (". . . . . . . . A5 - G#5 - F5 - D#5 - | E5 - - - - - - - . . . . . . . . |"
            ". . . . . . . . . . . . . . . . | . . . . . . . . D#5 - - - E5 - - - |")
    dark = mix(
        render_voice(drone, step, "pulse", 0.25, duty=0.5, adsr=(0.6, 0.5, 0.8, 0.6), length=length),
        render_voice(bell, step, "sine", 0.30, adsr=(0.003, 0.6, 0.0, 0.05), length=length),
        render_noise(". . . . . . . . . . . . . . . . | c - - - - - - - . . . . . . . . |" * 2, step, 0.25, length=length),
    )
    dark = echo(lowpass(dark, 900), step * 4, 0.45, 0.5)
    save("overworld_base", base)
    save("overworld_dark", dark, peak=0.6)
    save("overworld_preview_full_dark", mix(lowpass(base, 1800), dark))   # what darkness 100% sounds like


def cave():
    """Caves: ambient first (Hollow-Knight-style space), sparse, a slow heartbeat thud,
    the Shadowfall motif played low and slow on a soft triangle, long echo."""
    bpm = 70
    step = 60 / bpm / 2
    pad = ("A2 - - - - - - - - - - - - - - - | F2 - - - - - - - - - - - - - - - |"
           "D2 - - - - - - - - - - - - - - - | E2 - - - - - - - - - - - - - - - |")
    motif = (". . . . A3 - C4 - E4 - - - D4 - - - | B3 - - - - - - - . . . . . . . . |"
             ". . . . . . . . . . . . . . . . | . . . . G#3 - - - - - - - A3 - - - |")
    drip = (". . . . . . . . . . . E6 . . . . | . . . . . . . . . . . . . . B5 . |"
            ". . . . . . A6 . . . . . . . . . | . . . . . . . . . . . . . . . . |")
    beat = ("k . . . . . . . k . . . . . . . |" * 4)
    length = len(pad.replace("|", " ").split()) * int(RATE * step)
    music = mix(
        render_voice(pad, step, "pulse", 0.20, duty=0.125, adsr=(0.8, 0.5, 0.7, 0.8), length=length),
        render_voice(motif, step, "triangle", 0.45, adsr=(0.05, 0.3, 0.6, 0.2), vibrato=0.006, length=length),
        render_voice(drip, step, "sine", 0.25, adsr=(0.001, 0.25, 0.0, 0.01), length=length),
        render_noise(beat, step, 0.35, length=length),
    )
    music = echo(lowpass(music, 2200), 0.37, 0.5, 0.45)
    save("cave_loop", music)


def shadow_king():
    """The Shadow King motif as a 1-bar sting (boss intro / he appears on the map):
    falling line with a tritone, doubled an octave down, crash, long echo."""
    bpm = 80
    step = 60 / bpm / 2
    top = "A4 - G#4 - F4 - D#4 - | E4 - - - - - - - | . . . . . . . ."
    low = "A2 - G#2 - F2 - D#2 - | E2 - - - - - - - | . . . . . . . ."
    hit = "c . . . . . . . | k . . . . . . . | . . . . . . . ."
    length = len(top.replace("|", " ").split()) * int(RATE * step)
    sting = mix(
        render_voice(top, step, "pulse", 0.25, duty=0.25, adsr=(0.01, 0.2, 0.7, 0.4), vibrato=0.01, length=length),
        render_voice(low, step, "pulse", 0.25, duty=0.5, adsr=(0.01, 0.2, 0.8, 0.4), length=length),
        render_voice(low.replace("2", "1"), step, "triangle", 0.5, length=length),
        render_noise(hit, step, 0.4, length=length),
    )
    save("shadow_king_motif", echo(sting, 0.3, 0.4, 0.4, loop=False))


def sound_effects():
    # sword (R): a quick bright swish = falling noisy pulse
    save("sfx_sword_swing", sweep(1800, 300, 0.12, duty=0.125, vol=0.6, curve=0.6, noise=0.55, seed=2))
    # jump: a short rising pulse blip
    save("sfx_jump", sweep(260, 620, 0.11, duty=0.25, vol=0.6, curve=0.7))
    # hit (you hit a monster): a thud + crunch
    save("sfx_hit", mix(sweep(220, 50, 0.14, "triangle", vol=0.9),
                         sweep(900, 200, 0.07, duty=0.5, vol=0.5, noise=0.8, seed=4)))
    # hurt (a monster hits you): low falling minor second, buzzy
    save("sfx_hurt", sweep(330, 140, 0.25, duty=0.5, vol=0.6, curve=0.5, noise=0.15, seed=5))
    # Light Stone pickup: a bright arpeggio of the motif's first 3 notes, two octaves up, with echo
    up = []
    for note in ("A5", "C6", "E6", "A6"):
        up += sweep(freq(note), freq(note), 0.07, duty=0.25, vol=0.45)
    save("sfx_light_stone", echo(up + silence(0.5), 0.09, 0.45, 0.4, loop=False))
    # land: a soft thump
    save("sfx_land", sweep(160, 60, 0.06, "triangle", vol=0.8, noise=0.2, seed=6))


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        print("(ffmpeg not found: writing .wav files instead of .ogg)", file=sys.stderr)
    overworld()
    cave()
    shadow_king()
    sound_effects()
