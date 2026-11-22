# Audio (B6)

The music is our own tunes played by sampled orchestra instruments; the sound effects are made in code.

| File | What |
|---|---|
| `audio.gd` | The `Audio` autoload: buses (Master, Music, SFX), music that follows the gloom, SFX, volumes (saved in `user://audio.cfg`) |
| `tunes.gd` | The tunes as text on a 16th-note grid (`parts`): `overworld` (title and map), `cave`, `boss`, plus the Shadow King sting. Rewrite them here |
| `music/<tune>_<base\|dark>.ogg` | The tunes on real instruments (44.1 kHz stereo, exactly 8 bars, loop-clean). Made by the render script; don't edit by hand |
| `render/render_music.py` | Renders the stems: tunes → MIDI → FluidSynth + a free MIT SoundFont → fold the reverb tail into the loop → master → .ogg. The instruments for each part are in `ORCHESTRA` and `KITS` there |
| `render/dump_parts.gd` | Godot hands the tune text to the render script as JSON |
| `synth.gd` | The code synth: pulse/triangle/sine/noise voices, echo, low-pass. Makes the SFX, the King sting and the music fallback when a stem file is missing |
| `sfx.gd` | The sound effects, one recipe each (`Audio.play_sfx("jump")`) |
| `CREDITS-audio.md` | The SoundFont's source, licence and URL |

**Changed a tune or an instrument?** `pixi run -e music render-music` (macOS/Linux; it downloads the 40 MB
SoundFont once, renders silently to files, ~15 s), then commit `audio/music/*.ogg`. The `.ogg.import` files
keep `loop=true`.

| Tune | Base stem | Dark stem |
|---|---|---|
| overworld (A minor, 96 bpm) | French horns on the Shadowfall motif over strings, choir, cellos and basses, war drums (taiko, concert bass drum) | tremolo strings on a tritone drone, a far bell and voices on the Shadow King's motif, reverse-cymbal wind, war drums |
| cave (70 bpm) | slow strings and voices, a lone cello, harp and celesta drips, a soft bass-drum heartbeat | basses and tremolo strings, trombone and tuba on the King's motif, taiko heartbeat |
| boss (140 bpm) | brass and horns on the King's falling motif, galloping strings and cellos, basses and tuba, war drums | violins and strings shrieking the tritone arpeggio, choir, crashes and taiko |

Each tune has 2 stems that loop together: `base` and `dark`. The dark stem fades in as `Game.gloom` rises
(`smoothstep(0.3, 0.9, gloom)`), the base drops to 75% and the music gets duller (low-pass 8 kHz → 1.8 kHz).
Set `Audio.intensity` (0..1) to push the dark stem in by hand (boss phase 2, Nightfall).
