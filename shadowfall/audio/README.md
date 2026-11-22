# Audio (B6)

All music and sound is made in code when first needed: no audio files.

| File | What |
|---|---|
| `audio.gd` | The `Audio` autoload: buses (Master, Music, SFX), music that follows the gloom, SFX, volumes (saved in `user://audio.cfg`) |
| `synth.gd` | The sound maker: pulse/triangle/sine/noise voices, echo, low-pass |
| `tunes.gd` | The tunes as text: `overworld` (title and map), `cave`, `boss`, plus the Shadow King sting. Rewrite them here |
| `sfx.gd` | The sound effects, one recipe each (`Audio.play_sfx("jump")`) |
| `CREDITS-audio.md` | Where any outside audio file would be logged (none) |

Each tune has 2 stems that loop together: `base` and `dark`. The dark stem fades in as `Game.gloom` rises
(`smoothstep(0.3, 0.9, gloom)`), the base drops to 75% and the music gets duller (low-pass 8 kHz → 1.8 kHz).
Set `Audio.intensity` (0..1) to push the dark stem in by hand (boss phase 2, Nightfall).
