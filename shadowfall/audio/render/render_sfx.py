"""Renders the big sound effects (the Shadow King's fight, the castle doors) on sampled orchestra
instruments and saves them as audio/sfx/<name>.ogg (mono, one shot, faded end).

    pixi run -e music render-sfx

Each sound is a few orchestra layers (orchestra hit, taiko, timpani, choir, brass, reverse cymbal...)
played by FluidSynth on the same SoundFont as the music (render_music.py), plus numpy noise for
whooshes and rumbles, and the victory sting. The list of names is sounds() below; the game plays them through
Audio.play_sfx(name) (Sfx.RECORDED). Change a recipe, run it again and commit the .ogg files.
"""
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

from render_music import (BASSES, BELLS, BRASS, CELLO, CHOIR, HORNS, KIT, OOHS, PPQ, RATE,
                          REVERSE_CYMBAL, STRINGS, TAIKO, TIMPANI, TREMOLO, TROMBONE, TUBA, midi_note,
                          render, soundfont, tool, track)

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "sfx"
ORCH_HIT, CONCERT_BASS_DRUM = (0, 55), (8, 116)
FADE = 0.15  # seconds of fade at the end of every sound
TEMPO_US = 500_000  # 120 bpm: a beat is 0.5 s, so ticks = seconds * 2 * PPQ


# A hit: (preset, note name or MIDI number, velocity, start s, length s).
def hits_midi(hits: list[tuple], length: float) -> bytes:
    def tick(s: float) -> int:
        return int(round(s * 2 * PPQ))

    channels: dict[tuple, int] = {}
    tracks = [track([(0, b"\xff\x51\x03" + TEMPO_US.to_bytes(3, "big")), (tick(length + 3), b"\xff\x01\x03end")])]
    for preset, note, vel, start, dur in hits:
        ev: list[tuple[int, bytes]] = []
        if preset not in channels:
            ch = 9 if preset[0] == 128 else [c for c in range(16) if c != 9 and c not in channels.values()][0]
            channels[preset] = ch
            if ch != 9:
                ev.append((0, bytes([0xB0 | ch, 0, preset[0]])))
            ev += [(0, bytes([0xC0 | ch, preset[1]])), (0, bytes([0xB0 | ch, 7, 120])),
                   (0, bytes([0xB0 | ch, 91, 60]))]
        ch = channels[preset]
        n = note if isinstance(note, int) else midi_note(note)
        ev += [(tick(start), bytes([0x90 | ch, n, vel])), (tick(start + dur), bytes([0x80 | ch, n, 0]))]
        tracks.append(track(ev))
    return b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQ) + b"".join(tracks)


def chord(preset, notes: str, vel: int, start: float, dur: float) -> list[tuple]:
    return [(preset, n, vel, start, dur) for n in notes.split()]


# ----- numpy layers -----
RNG = np.random.default_rng(7)


def noise_sweep(length: float, f0: float, f1: float, gain: float, attack: float = 0.02) -> np.ndarray:
    """White noise through a one-pole low-pass whose cutoff glides f0 -> f1: a whoosh."""
    n = int(length * RATE)
    x = RNG.standard_normal(n)
    cut = np.geomspace(f0, f1, n)
    a = np.exp(-2 * np.pi * cut / RATE)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    env = np.minimum(1.0, np.arange(n) / max(1, attack * RATE)) * np.linspace(1, 0, n) ** 1.5
    y = y * env
    return gain * y / max(1e-9, np.abs(y).max())


def rumble(length: float, freq: float, gain: float) -> np.ndarray:
    """A low sine with a fast swell and long decay, for weight under a hit."""
    t = np.arange(int(length * RATE)) / RATE
    env = (1 - np.exp(-t / 0.01)) * np.exp(-t / (length / 3))
    return gain * np.sin(2 * np.pi * freq * t * (1 - 0.3 * t / length)) * env


def at(x: np.ndarray, start: float, n: int) -> np.ndarray:
    out = np.zeros(n)
    i = int(start * RATE)
    k = min(len(x), n - i)
    if k > 0:
        out[i:i + k] = x[:k]
    return out


# name -> (length s, peak, orchestra hits, [(start s, numpy layer)])
def sounds() -> dict:
    return {
        # his blade cleaves the air: a falling dark whoosh, a low string stab, a taiko thud
        "boss_slash": (0.6, 0.8,
                       chord(STRINGS, "A2 D#3", 110, 0.05, 0.15) + [(TAIKO, 33, 100, 0.06, 0.3)],
                       [(0.0, noise_sweep(0.35, 6000, 300, 0.5, 0.04))]),
        # the Eclipse: a reverse cymbal and a dark choir on the tritone swell up, then a deep boom
        "boss_beam": (1.8, 0.85,
                      [(REVERSE_CYMBAL, 60, 110, 0.0, 1.1)] + chord(CHOIR, "A2 D#3 A3", 100, 0.1, 1.4)
                      + chord(TREMOLO, "A3 D#4", 90, 0.2, 1.2) + [(TIMPANI, 33, 120, 1.1, 0.6),
                                                                (CONCERT_BASS_DRUM, 36, 120, 1.1, 0.6)],
                      [(0.3, noise_sweep(0.9, 200, 5000, 0.35, 0.8)), (1.1, rumble(0.7, 45, 0.7))]),
        # a new phase: an orchestra hit on the tritone, war drums, a choir that cries out
        "boss_phase": (2.2, 0.9,
                       chord(ORCH_HIT, "A3 D#4", 127, 0.0, 0.4) + chord(BRASS, "A2 D#3 A3", 115, 0.0, 1.2)
                       + chord(CHOIR, "A3 D#4 A4", 105, 0.05, 1.8) + [(TAIKO, 33, 127, 0.0, 1.0),
                       (TIMPANI, 33, 120, 0.0, 1.5), (KIT, 49, 110, 0.0, 1.5)],
                       [(0.0, rumble(1.2, 40, 0.8))]),
        # a real cut: a sharp orchestra hit and a taiko
        "boss_hit": (0.5, 0.8,
                     chord(ORCH_HIT, "E4", 120, 0.0, 0.2) + [(TAIKO, 45, 115, 0.0, 0.3),
                                                           (TIMPANI, 40, 100, 0.0, 0.4)],
                     [(0.0, noise_sweep(0.12, 9000, 1500, 0.4, 0.002))]),
        # he falls: a huge hit, the choir slides down his motif, timpani roll, a long dark wind
        "boss_defeat": (3.6, 0.9,
                        chord(ORCH_HIT, "A3 E4", 127, 0.0, 0.5) + [(TAIKO, 33, 127, 0.0, 1.2),
                        (KIT, 49, 120, 0.0, 2.5)]
                        + [(CHOIR, n, 105, 0.3 + i * 0.45, 0.6 if i < 3 else 2.2)
                           for i, n in enumerate(["A4", "G#4", "F4", "D#4"])]
                        + chord(TROMBONE, "A2 E3", 95, 0.3, 1.6) + chord(TUBA, "A1", 100, 0.3, 2.8)
                        + [(TIMPANI, 33, 70 + i * 4, 1.6 + i * 0.07, 0.1) for i in range(12)]
                        + [(TIMPANI, 28, 127, 2.45, 1.0), (CONCERT_BASS_DRUM, 36, 127, 2.45, 1.0)],
                        [(0.0, rumble(1.5, 38, 0.8)), (0.4, noise_sweep(3.0, 1500, 120, 0.3, 1.0))]),
        # Sunfang, the dawn blade: a bright A-major hit, brass, bells and a rising shimmer
        "sunfang": (2.0, 0.85,
                    chord(ORCH_HIT, "A4 C#5 E5", 120, 0.0, 0.4) + chord(BRASS, "A3 C#4 E4 A4", 112, 0.0, 1.3)
                    + chord(HORNS, "A3 E4", 100, 0.0, 1.3) + chord(BELLS, "A5 E6", 100, 0.05, 1.5)
                    + chord(OOHS, "C#5 E5 A5", 90, 0.1, 1.6) + [(KIT, 49, 105, 0.0, 1.8)],
                    [(0.0, noise_sweep(0.5, 800, 9000, 0.25, 0.3))]),
        # a castle door grinds open: a deep timpani, low strings and a long stone scrape
        "door_open": (1.4, 0.8,
                      [(TIMPANI, 33, 110, 0.0, 0.8), (CONCERT_BASS_DRUM, 36, 105, 0.0, 0.8)]
                      + chord(BASSES, "A1", 100, 0.05, 1.1) + chord(CELLO, "E2 A2", 85, 0.1, 1.0),
                      [(0.0, noise_sweep(1.1, 700, 150, 0.5, 0.15)), (0.0, rumble(0.9, 50, 0.5))]),
        # victory: the Shadowfall motif (A C E D) rises again, and this time it resolves, to A major,
        # on brass, strings and choir, timpani rolling in, bells over it all
        "victory": (4.4, 0.9,
                    [(p, n, 112, st, d) for p in (BRASS, STRINGS)
                     for n, st, d in [("A4", 0.0, 0.3), ("C5", 0.3, 0.3), ("E5", 0.6, 0.3), ("D5", 0.9, 0.6),
                                      ("C#5", 1.5, 2.6)]]
                    + chord(HORNS, "A3 C4 E4", 92, 0.0, 0.9) + chord(HORNS, "A3 D4 F4", 96, 0.9, 0.6)
                    + chord(CELLO, "A2", 96, 0.0, 0.9) + chord(CELLO, "D2", 100, 0.9, 0.6)
                    + [(TIMPANI, 33, 60 + i * 6, 0.9 + i * 0.075, 0.08) for i in range(8)]
                    + chord(ORCH_HIT, "A3 C#4 E4", 118, 1.5, 0.4) + chord(BRASS, "A2 E3 A3 C#4 E4", 115, 1.5, 2.6)
                    + chord(HORNS, "E4 A4", 100, 1.5, 2.6) + chord(CHOIR, "A3 C#4 E4 A4", 100, 1.5, 2.6)
                    + chord(BASSES, "A1", 110, 1.5, 2.6) + chord(TUBA, "A1", 100, 1.5, 2.6)
                    + chord(BELLS, "A5 C#6 E6", 92, 1.55, 2.4)
                    + [(TIMPANI, 33, 127, 1.5, 1.2), (KIT, 49, 112, 1.5, 2.5), (TAIKO, 33, 120, 1.5, 1.0)],
                    []),
        # shut fast: an iron clank and a dull thud
        "door_locked": (0.45, 0.75,
                        [(TAIKO, 45, 100, 0.0, 0.25), (KIT, 56, 90, 0.0, 0.2), (KIT, 39, 70, 0.0, 0.2)],
                        [(0.0, noise_sweep(0.08, 5000, 800, 0.35, 0.002))]),
    }


def save_mono_ogg(x: np.ndarray, ogg: Path, tmp: Path) -> None:
    wav = tmp / (ogg.stem + ".wav")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(x, -1, 1) * 32767).round().astype("<i2").tobytes())
    subprocess.run([tool("ffmpeg"), "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis",
                    "-q:a", "3", "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                    str(ogg)], check=True)


def make(name: str, recipe: tuple, sf: Path, tmp: Path) -> np.ndarray:
    length, peak, hits, layers = recipe
    n = int(length * RATE)
    x = np.zeros(n)
    if hits:
        midi = tmp / f"{name}.mid"
        midi.write_bytes(hits_midi(hits, length))
        x += at(render(midi, tmp / f"{name}_raw.wav", sf).mean(axis=1), 0.0, n)
    for start, layer in layers:
        x += at(layer, start, n)
    x -= x.mean()
    x *= peak / max(1e-9, float(np.abs(x).max()))
    f = int(FADE * RATE)
    x[-f:] *= np.linspace(1, 0, f) ** 2
    x[:32] *= np.linspace(0, 1, 32)
    return x


def main() -> None:
    sf = soundfont()
    OUT.mkdir(exist_ok=True)
    total = 0
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for name, recipe in sounds().items():
            x = make(name, recipe, sf, tmp)
            ogg = OUT / f"{name}.ogg"
            save_mono_ogg(x, ogg, tmp)
            total += ogg.stat().st_size
            print(f"{ogg.relative_to(HERE.parent.parent)}: {len(x) / RATE:.2f} s, peak {np.abs(x).max():.2f}, "
                  f"{ogg.stat().st_size // 1024} KB")
    print(f"sfx total: {total // 1024} KB")


if __name__ == "__main__":
    main()
