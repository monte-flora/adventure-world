# Shadowfall teen refactor: music and sound (Wave A, audio)

**Recommendation:** keep making every note in code. Use a "NES rules, modern room" sound: 4 chip voices per tune, plus echo, low-pass and stems. Two original leitmotifs. Music layers follow `game.gloom`. CC0 packs only for the few sounds that synthesis does badly, and each one is logged.

> **Update, Wave C3 (2026-11-22):** the user asked for a more authentic sound, so the **music** is now our own tunes (`shadowfall/audio/tunes.gd`) rendered on sampled orchestra instruments: `pixi run -e music render-music` (`shadowfall/audio/render/render_music.py`, FluidSynth + the MIT MuseScore_General SoundFont, downloaded, not committed) writes the base + dark `.ogg` stems to `shadowfall/audio/music/`. The code synth stays for SFX, the King sting and as the music fallback. Rule (d) below allows it.

Prototype: `spikes/audio/make_audio.py` (standard library only, about 3 s of CPU) → `spikes/audio/out/`, 11 files, **492 KB** in total.

## 1. How the game makes sound today
| What | Where | How |
|---|---|---|
| ~40 SFX | `game.py` `Sounds.RECIPES` | A list of notes, each a square, sine or noise wave with a linear fade. Built at start-up into `pygame.mixer.Sound(buffer=…)` |
| 12 tunes (one per place, plus `dusk` from `phase2/theme.py`) | `game.py` `TUNES`, `Music` | A text "tracker" (`"A4 - C5 . |"`), voices square, triangle, sine or bell, plus k/s/h drums. Rendered on a background thread |
| Crossfade | `Music.play` | Channels 0 and 1 are reserved, fading over 0.9 s |
| Web | `web/build_web.py` | Pre-renders every tune to `.ogg` with ffmpeg at -q 3, because the browser has no threads |
| Settings | `settings.py`: none | Only an on/off toggle. `MUSIC_VOLUME = 0.35` is hard-coded. Mono, 22050 Hz |

Gaps: no volume sliders, no layers, no echo or filter (so it sounds "toy"), no shared motif, one tune per place.

## 2. What the references teach (principles only, nothing copied)
| Game | What they did | Principle for us | Sources |
|---|---|---|---|
| Shovel Knight | Made in FamiTracker with the VRC6 expansion (NES plus 3 voices). The composers wrote "with six voices". The music could run on real hardware | A **fixed voice budget** makes a style. Arpeggios stand in for chords | [NL news](https://www.nintendolife.com/news/2014/06/shovel_knight_soundtracks_released_on_bandcamp), [NL feature](https://www.nintendolife.com/features/mega-man-shovel-knight-and-save-me-mr-tako-composers-on-getting-that-retro-sound) |
| A Link to the Past | One overworld theme returns (overture, overworld, credits). The Dark World has its own minor/Dorian theme. 8 voices, 64 KB of sample RAM | **Leitmotif** for the land. The **darkened world gets a minor recolour**, not a new random tune | [Wikipedia](https://en.wikipedia.org/wiki/The_Legend_of_Zelda:_A_Link_to_the_Past), [Hooktheory](https://hooktheory.com/theorytab/view/koji-kondo/dark-world-theme---the-legend-of-zelda-alttp), [SNESdev](https://snes.nesdev.org/wiki/S-SMP) |
| Hollow Knight | Brief: "dark elegance, minimal instrumentation", with one timbre per area. One theme is re-orchestrated across areas (the town theme turns into the forest). Each track has 2 or more stems. "The impact is bigger if there's not an omnipresent melody" | **Ambient first** in caves. **Stems** that fade. **Silence** as a tool. Boss music is intense but sad, not gory | [Game Developer](https://gamedeveloper.com/audio/crafting-an-evocative-score-for-i-hollow-knight-i-), [COG](https://cogconnected.com/feature/hollow-sounds-how-the-music-of-hollow-knight-tells-its-story/), [Bandcamp Daily](https://daily.bandcamp.com/features/christopher-larkin-hollow-knight-silksong-interview) |

## 3. How we make it: legal and cheap
| Option | Cost | Licence risk | Fits web build | Verdict |
|---|---|---|---|---|
| **A. Code synthesis (what we have now, upgraded)** | 0 | **None**: we own every note | Yes (pre-rendered to .ogg) | **Pick**. Kid and parent can edit tunes as text, which is the game's spirit |
| B. Tracker (Furnace GPL, BeepBox: "songs belong to their authors") | 0 | Low. The GPL covers the tool, not the song | Export to .ogg | Optional for a parent who wants a GUI. Export the .ogg and commit the source file next to it |
| C. sfxr-style (ChipTone: outputs CC0; jsfxr: code Apache-2.0) | 0 | Low | .ogg | OK for SFX ideas. Port the good ones into recipes |
| D. CC0 packs (Kenney: CC0, no credit) | 0 | Low if CC0 only. Freesound needs the **CC0** filter (CC BY needs credit, NC is not allowed). Sonniss is **not CC0** (no redistribution in a public repo) | .ogg | Only for wind and water ambience if synthesis sounds bad. Log each file in `CREDITS-audio.md` |
| E. Paid or AI music | $ / unclear | Unclear ownership | | **No** |

**Rule for Wave B:** an audio file may enter the repo only if (a) a script in the repo makes it, (b) a tracker source file we wrote sits next to it, or (c) it is CC0 and has a line in `CREDITS-audio.md` with its URL and licence. (d) (added in Wave C3) it is rendered by a script in the repo from samples or a SoundFont under a permissive licence (CC0, MIT, BSD, zlib or similar: shipping in a public repo and a game allowed, no NC/ND), with the source, licence, URL and any required notice in `CREDITS-audio.md`. Download the samples in the script; commit only the rendered files.

## 4. The prototype (all original; listen in `spikes/audio/out/`)
| File | Seconds | KB | What it shows |
|---|---|---|---|
| `overworld_base.ogg` | 20.0 loop | 96 | A minor, 96 bpm. 25% pulse melody (the Shadowfall motif), 12.5% pulse harmony, triangle bass, noise drums, echo |
| `overworld_dark.ogg` | 20.0 loop | 88 | **Darkness stem**, same length: a tritone drone (A–D#), a far bell playing the King motif, wind crash, low-pass 900 Hz |
| `overworld_preview_full_dark.ogg` | 20.0 | 88 | What 100% gloom sounds like: the base stem low-passed to 1.8 kHz, plus the dark stem |
| `cave_loop.ogg` | 27.4 loop | 123 | 70 bpm, ambient first. Slow pad, the motif low on triangle, water drips, a heartbeat thud, 0.37 s echo |
| `shadow_king_motif.ogg` | 9.0 sting | 37 | A G# F D# → E, falling with a tritone, in octaves, crash plus echo |
| `sfx_sword_swing` / `jump` / `hit` / `hurt` / `light_stone` / `land` | 0.1–0.8 | 3–6 each | Pitch sweeps with noise. The Light Stone chime is the motif's first notes, two octaves up |

**Leitmotifs** (the user can rewrite them; they are text in the script):
```
Shadowfall (land/hero):  A3 C4 E4 D4 | B3        rises, ends unresolved
Shadow King:             A3 G#3 F3 D#3 | E3      same rhythm, falls, tritone A–D#
```

## 5. Spec for Wave B: the music system
**Layers vs darkness** (figure: stem gain against `gloom` 0→1, with night adding to it):
```
gain 1.0 |base ████████████████████▇▇▇▇▆▆▆▆▅▅▅  (base low-pass 8k → 1.8k Hz)
     0.5 |                     ▂▃▄▅▆▇███████  dark stem
     0.0 +-----------------------------------  gloom 0   .3   .6   1
           day/low gloom: base only | dark = smoothstep(.3, .9, max(gloom, 0.6*night))
```

| Item | Number / rule |
|---|---|
| Voice budget per tune | 4 chip voices (2 pulse at 12.5/25/50% duty, 1 triangle, 1 noise), plus 1 "colour" voice per region (bell, sine pad). SFX never steal music voices: they get their own mixer channels |
| Stems | Every map and cave theme has 2: `base` and `dark`. Same length, cut to whole bars, started on the same frame on 2 channels (pygame) or as one `AudioStreamSynchronized` (Godot 4.3+). Gain updates at most 10× per second, ramped |
| Darkness input | `dark = smoothstep(0.3, 0.9, max(game.gloom, 0.6 * night_darkness))` (`phase2/theme.py` `gloom`, `phase2/monsters.darkness`) |
| Region themes | Map (base+dark), village (a safe, warm major variant of the motif, no dark stem), caves ×3 timbres (stone: triangle and drips; crystal: bell arps; lava: pulse ostinato), Nightfall Hollow (the motif in D# minor), castle, boss |
| Boss | 3 parts: intro sting (`shadow_king_motif`), loop A at 140 bpm, loop B (phase 2 of the fight, plus a stem). Switch on the bar line. **2 s of silence** before he speaks |
| Silence | Caves begin with 4–8 s of ambience only. Music ducks to 30% under dialogue. Death leaves 1.5 s of silence, then the cave sting |
| Transitions | Region change: crossfade 0.9 s (as now). Map → cave: map fades out 0.4 s, then the cave sting, then the loop. Fight start: 0.2 s cut |
| Volume settings | `settings.py`: `MUSIC_VOLUME = 0.35`, `SFX_VOLUME = 0.8`, `MASTER_VOLUME = 1.0`. Pause menu: 3 sliders in steps of 10%, saved in the save file. Mute stays on key M |
| Format | Mono, 22050 Hz, Vorbis -q 2 (about 4.5 KB per second). Loops are whole bars, with the echo tail wrapped to the start (done in the spike) |
| Size budget (web) | Music ≤ 4 MB in total (about 15 min of stems), SFX ≤ 300 KB. Measured now: 492 KB for 2 loops, 1 sting and 6 SFX |
| Web limits | No threads, so **pre-render everything** at build (as now). Audio starts only after the first click (pygbag's start screen gives that click). Use OGG only, never `mixer.music` queues (pygbag issue #106 is reported). Safari plays the OGG through pygbag's own decoder: **test on a real iPhone** |

**Module plan** (pygame path; if Godot wins, the same files become `godot/audio/*.gd` plus `.tres`):
| File | Owner (Wave B task) | Contents |
|---|---|---|
| `audio/synth.py` | B-A1 | The `make_audio.py` maths (pulse duty, triangle, noise, ADSR, vibrato, low-pass, echo, sweep), with tests |
| `audio/tunes/*.py` | B-A2 (map, village), B-A3 (caves ×3, Nightfall), B-A4 (castle, boss) | One file per region: tune text plus stem lists |
| `audio/sfx.py` | B-A5 | The new SFX recipes, keeping the current `game.sound(name)` names |
| `audio/mixer.py` | B-A1 | `Music` with stems, `set_darkness()`, duck, transitions, volume settings |
| `web/build_web.py` (audio part) | B-A1 | Renders `audio/tunes` to .ogg and checks the size budget |
| `tests/test_audio.py` | each owner adds its own cases | Stems are equal length, loops are whole bars, peak ≤ 0.9, total size within budget |

Tasks B-A2 to B-A5 each touch only their own files. B-A1 goes first, or in parallel against a fixed `synth.py` API.

## 6. Open questions for the user
1. Is the chip-plus-echo sound right? The other choice is softer piano and strings (Hollow Knight-like), which code synthesis does less well.
2. Do you like the two motifs, or will the kid write their own? (They are plain text in the script.)
3. Stereo? It doubles the file sizes. Mono is the recommendation.
4. May a few CC0 ambience files (wind, water) be used, or should everything be code-made?

## 7. What I did not verify
- **Nobody has listened to the files yet.** They were checked for length, size and that they encode, not by ear. The loop seams were not heard.
- The stems drifting apart on long pygame playback, and pygbag OGG on Safari/iOS.
- From the research: the Shovel Knight VRC6 and SFX channel claims come from secondary sources. Hollow Knight stems are cited from the Silksong interview. The sfxr, bfxr, FamiTracker, OpenMPT and OpenGameArt licences were not fetched.
- The Godot `AudioStreamSynchronized`/`AudioStreamInteractive` APIs were not tested.
