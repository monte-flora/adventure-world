"""Plays Shadowfall's tunes on sampled orchestra instruments and saves the music stems.

    pixi run -e music render-music

1. Godot dumps the note text from audio/tunes.gd (Tunes.parts) to JSON (dump_parts.gd).
2. Each stem (base, dark) of each tune becomes a MIDI file: every part goes to one or more
   instruments (ORCHESTRA below), the drum letters go to war drums (KITS).
3. FluidSynth plays the MIDI on MuseScore_General.sf3 (MIT, see CREDITS-audio.md), downloaded
   once into render/.cache/ (git-ignored). Nothing is played through the speakers.
4. The reverb tail past the loop end is folded back onto the start (seamless loop), the stem is
   cut to exactly 8 bars, lightly mastered (loudness target, peak ceiling) and saved as
   audio/music/<tune>_<stem>.ogg. Both stems of a tune have the same number of samples.

Change the tunes in tunes.gd, the instruments here, then run it again and commit the .ogg files.
"""
import hashlib
import json
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
AUDIO = HERE.parent
GAME = AUDIO.parent  # shadowfall/
OUT = AUDIO / "music"
CACHE = HERE / ".cache"
SF_URL = "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf3"
SF_SHA256 = "5b85b6c2c61d10b2b91cddd41efcce7b25cd31c8271d511c73afafbef20b6fa3"
RATE = 44100
PPQ = 480
TICKS_PER_STEP = PPQ // 4  # a step is a 16th note
TAIL = 6.0  # seconds of reverb rendered past the loop end, then folded back to the start
OGG_QUALITY = "3"  # libvorbis -q: about 110 kbit/s stereo

# Presets in MuseScore_General: (bank, program).
CELESTA, BELLS, VIOLIN, CELLO, BASSES = (0, 8), (0, 14), (0, 40), (0, 42), (0, 43)
TREMOLO, HARP, TIMPANI, STRINGS, SLOW_STRINGS = (0, 44), (0, 46), (0, 47), (0, 48), (0, 49)
CHOIR, OOHS, TROMBONE, TUBA, HORNS, BRASS = (0, 52), (0, 53), (0, 57), (0, 58), (0, 60), (0, 61)
TAIKO, REVERSE_CYMBAL, CONCERT_BASS_DRUM, KIT = (0, 116), (0, 119), (8, 116), (128, 48)

# A layer: (part, preset, transpose in semitones, velocity, pan -1..1, reverb send 0..127).
# Drum parts instead name a kit from KITS: (part, "kit:<name>", 0, velocity scale %, pan, reverb).
ORCHESTRA = {
    "overworld": {  # A minor, 96 bpm: horns carry the Shadowfall motif over strings and choir
        "base": [
            ("lead", HORNS, 0, 100, 0.2, 70),
            ("lead", STRINGS, 0, 62, -0.3, 70),
            ("harmony", CHOIR, 0, 68, 0.0, 90),
            ("harmony", SLOW_STRINGS, -12, 58, -0.4, 80),
            ("bass", CELLO, 0, 84, -0.2, 60),
            ("bass", BASSES, -12, 80, 0.1, 55),
            ("beat", "kit:war", 0, 95, 0.0, 60),
        ],
        "dark": [  # a tremolo drone a tritone under the key, a far bell and voices on the King's motif
            ("drone", TREMOLO, 12, 70, -0.3, 90),
            ("drone", BASSES, 0, 82, 0.2, 70),
            ("dark_lead", BELLS, -12, 78, 0.3, 110),
            ("dark_lead", OOHS, -12, 72, -0.1, 110),
            ("wind", "kit:wind", 0, 80, 0.0, 120),
            ("dark_beat", "kit:war", 0, 100, 0.0, 70),
        ],
    },
    "cave": {  # 70 bpm, ambient first: slow strings and voices, a lone cello, harp-and-celesta drips
        "base": [
            ("pad", SLOW_STRINGS, 12, 64, -0.3, 100),
            ("pad", OOHS, 12, 52, 0.3, 110),
            ("lead", CELLO, 0, 90, 0.1, 90),
            ("drip", HARP, 0, 72, 0.5, 120),
            ("drip", CELESTA, 0, 56, -0.5, 120),
            ("beat", "kit:heart", 0, 85, 0.0, 70),
        ],
        "dark": [  # basses and trembling strings, low brass on the King's motif, a taiko heartbeat
            ("drone", BASSES, 0, 80, -0.2, 90),
            ("drone", TREMOLO, 12, 56, 0.3, 100),
            ("dark_lead", TROMBONE, 12, 82, 0.2, 90),
            ("dark_lead", TUBA, 0, 86, -0.1, 80),
            ("dark_beat", "kit:taiko", 0, 100, 0.0, 80),
        ],
    },
    "boss": {  # 140 bpm: brass on the King's falling motif, galloping strings, war drums
        "base": [
            ("lead", BRASS, 0, 104, 0.2, 60),
            ("lead", HORNS, -12, 84, 0.4, 60),
            ("lead", STRINGS, 0, 80, -0.3, 60),
            ("bass", STRINGS, 12, 86, -0.5, 50),
            ("bass", CELLO, 0, 88, -0.1, 50),
            ("low", BASSES, 0, 90, 0.1, 50),
            ("low", TUBA, 0, 76, 0.3, 50),
            ("beat", "kit:war", 0, 105, 0.0, 50),
        ],
        "dark": [  # phase 2: shrieking violins on the tritone arpeggio, a choir, crashes and taiko
            ("dark_lead", VIOLIN, 0, 86, -0.4, 70),
            ("dark_lead", STRINGS, 0, 70, 0.4, 70),
            ("dark_lead", CHOIR, -12, 66, 0.0, 90),
            ("dark_beat", "kit:war", 0, 110, 0.0, 70),
        ],
    },
    "boss_eclipse": {  # phase 2, the Eclipse: low brass on his motif in the dark, trembling strings, half-time taiko
        "base": [
            ("lead", TROMBONE, 0, 104, 0.2, 80),
            ("lead", HORNS, 0, 86, -0.3, 80),
            ("lead", TUBA, -12, 72, 0.1, 70),
            ("bass", TREMOLO, 12, 80, -0.4, 70),
            ("bass", BASSES, 0, 92, 0.2, 60),
            ("pad", CHOIR, 0, 70, 0.0, 100),
            ("pad", OOHS, 6, 46, 0.3, 110),
            ("beat", "kit:taiko", 0, 110, 0.0, 70),
        ],
        "dark": [  # deeper night: violins shriek the tritone, a choir high above, crashes
            ("dark_lead", VIOLIN, 0, 84, -0.4, 90),
            ("dark_lead", CHOIR, -12, 70, 0.3, 100),
            ("dark_beat", "kit:war", 0, 105, 0.0, 70),
        ],
    },
    "boss_fall": {  # phase 3, the Fall: brass on the Shadowfall motif over driving 16th basses, full war drums
        "base": [
            ("lead", BRASS, 0, 108, 0.2, 60),
            ("lead", HORNS, -12, 90, 0.4, 60),
            ("lead", STRINGS, 0, 84, -0.3, 60),
            ("harmony", CHOIR, 0, 76, 0.0, 90),
            ("harmony", SLOW_STRINGS, -12, 64, -0.4, 80),
            ("bass", CELLO, 12, 92, -0.2, 50),
            ("bass", BASSES, 0, 96, 0.1, 50),
            ("beat", "kit:war", 0, 112, 0.0, 50),
        ],
        "dark": [  # the King answers: violins and strings on his tritone, a choir, crashes and taiko fills
            ("dark_lead", VIOLIN, 0, 88, -0.4, 70),
            ("dark_lead", STRINGS, -12, 72, 0.4, 70),
            ("dark_lead", CHOIR, -12, 66, 0.0, 90),
            ("dark_beat", "kit:war", 0, 110, 0.0, 70),
        ],
    },
}

# Drum letters (k thud, s snare, h hat, c crash/wind) -> hits: (preset, MIDI note, velocity, seconds).
KITS = {
    "war": {
        "k": [(TAIKO, 36, 112, 1.2), (CONCERT_BASS_DRUM, 36, 96, 1.5)],
        "s": [(TAIKO, 45, 88, 0.8), (KIT, 38, 62, 0.5)],
        "h": [(KIT, 42, 40, 0.2)],
        "c": [(KIT, 49, 92, 2.0), (TIMPANI, 33, 90, 2.0)],
    },
    "heart": {
        "k": [(CONCERT_BASS_DRUM, 36, 82, 1.5)],
        "s": [(KIT, 38, 40, 0.5)],
        "h": [(KIT, 42, 30, 0.2)],
        "c": [(KIT, 49, 60, 2.0)],
    },
    "taiko": {
        "k": [(TAIKO, 33, 104, 1.2), (TIMPANI, 33, 70, 1.5)],
        "s": [(TAIKO, 45, 80, 0.8)],
        "h": [(KIT, 42, 30, 0.2)],
        "c": [(KIT, 49, 70, 2.0)],
    },
    "wind": {"c": [(REVERSE_CYMBAL, 60, 70, 2.4)]},
}

# Light mastering: loudness target (RMS) with a peak ceiling, per stem. The dark stem sits under the base.
MASTER = {"base": (0.13, 0.89), "dark": (0.10, 0.70)}

NOTE_STEPS = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def midi_note(name: str) -> int:
    return 12 * (int(name[-1]) + 1) + NOTE_STEPS[name[:-1]]


def tokens(text: str) -> list[str]:
    return text.replace("|", " ").split()


def notes_of(text: str) -> list[tuple[int, int, str]]:
    """(start step, length in steps, note) for every note: "A4" plays, "-" holds, "." rests."""
    seq, out, i = tokens(text), [], 0
    while i < len(seq):
        hold = 1
        while i + hold < len(seq) and seq[i + hold] == "-":
            hold += 1
        if seq[i] not in (".", "-"):
            out.append((i, hold, seq[i]))
        i += hold
    return out


def accent(step: int) -> int:
    """Downbeats a little louder, so the music breathes like players."""
    return 10 if step % 16 == 0 else 5 if step % 4 == 0 else 0


# ----- MIDI writing (format 1, one track per instrument) -----
def vlq(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def track(events: list[tuple[int, bytes]]) -> bytes:
    data, now = b"", 0
    for tick, msg in sorted(events, key=lambda e: (e[0], e[1][0] & 0xF0 != 0x80)):  # note-offs first
        data += vlq(tick - now) + msg
        now = tick
    data += b"\x00\xff\x2f\x00"
    return b"MTrk" + struct.pack(">I", len(data)) + data


def stem_midi(tune: str, stem: str, info: dict, seconds_per_step: float) -> bytes:
    """One stem as a MIDI file; every layer of ORCHESTRA[tune][stem] gets its own channel."""
    rng = random.Random(f"{tune}-{stem}")
    parts = info["parts"]
    n_steps = len(tokens(parts[next(iter(parts))]))
    tail_ticks = int(TAIL / seconds_per_step * TICKS_PER_STEP)
    end = n_steps * TICKS_PER_STEP + tail_ticks
    tempo = int(60_000_000 / info["bpm"])
    tracks = [track([(0, b"\xff\x51\x03" + tempo.to_bytes(3, "big")), (end, b"\xff\x01\x04tail")])]
    channels: dict[tuple, int] = {}  # (preset, pan, reverb) -> channel

    def channel(preset, pan, rev, events):
        key = (preset, pan, rev)
        if key not in channels:
            ch = 9 if preset[0] == 128 else [c for c in range(16) if c != 9 and c not in channels.values()][0]
            channels[key] = ch
            bank = [] if ch == 9 else [(0, bytes([0xB0 | ch, 0, preset[0]]))]  # channel 10 is the drum bank
            events += bank + [(0, bytes([0xC0 | ch, preset[1]])),
                      (0, bytes([0xB0 | ch, 7, 110])), (0, bytes([0xB0 | ch, 10, round(64 + 63 * pan)])),
                      (0, bytes([0xB0 | ch, 91, rev])), (0, bytes([0xB0 | ch, 93, 0]))]
        return channels[key]

    for part, preset, transpose, vel, pan, rev in ORCHESTRA[tune][stem]:
        ev: list[tuple[int, bytes]] = []
        if isinstance(preset, str):  # drums
            kit = KITS[preset.split(":")[1]]
            for step, hit in enumerate(tokens(parts[part])):
                for hp, note, hv, dur in kit.get(hit, []):
                    ch = channel(hp, pan, rev, ev)
                    v = max(1, min(127, round((hv + accent(step) + rng.randint(-5, 5)) * vel / 100)))
                    on = step * TICKS_PER_STEP
                    off = on + max(1, int(dur / seconds_per_step * TICKS_PER_STEP))
                    ev += [(on, bytes([0x90 | ch, note, v])), (off, bytes([0x80 | ch, note, 0]))]
        else:
            ch = channel(preset, pan, rev, ev)
            for step, hold, name in notes_of(parts[part]):
                note = midi_note(name) + transpose
                v = max(1, min(127, vel + accent(step) + rng.randint(-4, 4)))
                on, off = step * TICKS_PER_STEP, (step + hold) * TICKS_PER_STEP
                ev += [(on, bytes([0x90 | ch, note, v])), (off, bytes([0x80 | ch, note, 0]))]
        tracks.append(track(ev))
    return b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQ) + b"".join(tracks)


# ----- tools -----
def tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        sys.exit(f"{name} not found: run this with  pixi run -e music render-music")
    return path


def soundfont() -> Path:
    sf = CACHE / "MuseScore_General.sf3"
    if not sf.exists():
        CACHE.mkdir(exist_ok=True)
        (CACHE / ".gitignore").write_text("*\n")
        (CACHE / ".gdignore").write_text("")
        print(f"Downloading the SoundFont (40 MB) from {SF_URL}")
        urllib.request.urlretrieve(SF_URL, sf)
    digest = hashlib.sha256(sf.read_bytes()).hexdigest()
    if digest != SF_SHA256:
        sys.exit(f"{sf} has sha256 {digest}, want {SF_SHA256}: delete it and run again")
    return sf


def dump_parts(tmp: Path) -> dict:
    out = tmp / "parts.json"
    subprocess.run([tool("godot"), "--headless", "--audio-driver", "Dummy", "--path", str(GAME),
                    "--script", "res://audio/render/dump_parts.gd", "--", str(out)], check=True,
                   capture_output=True)
    return json.loads(out.read_text())


def render(midi: Path, wav: Path, sf: Path) -> np.ndarray:
    """FluidSynth to a WAV file (never the speakers); returns float samples, shape (n, 2)."""
    subprocess.run([tool("fluidsynth"), "-ni", "-q", "-a", "file", "-r", str(RATE), "-g", "0.5",
                    "-o", "synth.reverb.active=1", "-o", "synth.reverb.room-size=0.85",
                    "-o", "synth.reverb.damp=0.35", "-o", "synth.reverb.width=1.0",
                    "-o", "synth.reverb.level=0.8", "-o", "synth.chorus.active=0",
                    "-o", "synth.polyphony=512", "-F", str(wav), "-T", "wav", "-O", "s16",
                    str(sf), str(midi)], check=True, capture_output=True)
    with wave.open(str(wav)) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels())
    return data.astype(np.float64) / 32768.0


def fold_loop(x: np.ndarray, n: int) -> np.ndarray:
    """Cuts to n samples and adds what rang on past the end back onto the start: a seamless loop."""
    if len(x) < n:
        x = np.vstack([x, np.zeros((n - len(x), x.shape[1]))])
    loop = x[:n].copy()
    tail = x[n:]
    while len(tail):
        k = min(len(tail), n)
        loop[:k] += tail[:k]
        tail = tail[k:]
    return loop


def master(x: np.ndarray, stem: str) -> np.ndarray:
    target_rms, ceiling = MASTER[stem]
    x = x - x.mean(axis=0)  # no DC offset
    rms = float(np.sqrt(np.mean(x ** 2)))
    gain = min(target_rms / max(rms, 1e-9), ceiling / max(float(np.abs(x).max()), 1e-9))
    return x * gain


def save_ogg(x: np.ndarray, ogg: Path, tmp: Path) -> None:
    wav = tmp / (ogg.stem + "_master.wav")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(x, -1, 1) * 32767).round().astype("<i2").tobytes())
    subprocess.run([tool("ffmpeg"), "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis",
                    "-q:a", OGG_QUALITY, "-map_metadata", "-1", "-fflags", "+bitexact",
                    "-flags:a", "+bitexact", str(ogg)], check=True)


def main() -> None:
    sf = soundfont()
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        data = dump_parts(tmp)
        total = 0
        for tune, info in data["tunes"].items():
            seconds_per_step = 60.0 / info["bpm"] / 4.0
            n_steps = len(tokens(info["parts"][next(iter(info["parts"]))]))
            n = round(n_steps * seconds_per_step * RATE)
            for stem in ("base", "dark"):
                midi = tmp / f"{tune}_{stem}.mid"
                midi.write_bytes(stem_midi(tune, stem, info, seconds_per_step))
                x = master(fold_loop(render(midi, tmp / f"{tune}_{stem}.wav", sf), n), stem)
                ogg = OUT / f"{tune}_{stem}.ogg"
                save_ogg(x, ogg, tmp)
                total += ogg.stat().st_size
                print(f"{ogg.relative_to(GAME)}: {n} samples ({n / RATE:.3f} s), "
                      f"peak {np.abs(x).max():.2f}, {ogg.stat().st_size // 1024} KB")
        print(f"music total: {total / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
