# Audio credits

**Music** (`audio/music/*.ogg`) is our own tunes (`audio/tunes.gd`), played on sampled instruments by
`audio/render/render_music.py` (FluidSynth). The SoundFont is downloaded by that script into
`audio/render/.cache/` (git-ignored); only the rendered stems are in the repo.
**Sound effects** are made in code by `audio/synth.gd` from the recipes in `audio/sfx.gd`. The code synth
also stays as the music fallback when a stem file is missing.

The rule (docs/teen/audio/README.md §3): an audio file may enter the repo only if (a) a script in the repo
makes it, (b) a tracker source file we wrote sits next to it, or (c) it is CC0 and has a line below with its
URL and licence. The stems are (a); the samples they are played on are listed below.

| Used for | Source | Licence | URL (checked 2026-11-22) |
|---|---|---|---|
| Every instrument in `audio/music/*.ogg` (strings, horns, brass, choir, taiko, timpani, harp, celesta, bells, orchestra kit) | MuseScore_General.sf3 v0.2 (S. Christian Collins), from FluidR3Mono (Michael Cowgill) and FluidR3 (Frank Wen); sha256 `5b85b6c2…0b6fa3` | MIT | https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/ (licence: `MuseScore_General_License.md`; per-preset sources: `MuseScore_General_Sample_Sources.csv`, no extra credit on any preset we use) |

Notices the MIT licence asks us to keep (from `MuseScore_General_License.md`):

> FluidR3 (original version) by Frank Wen Copyright (c) 2000-02. Mono conversion (FluidR3Mono) by Michael
> Cowgill Copyright (c) 2014-17. Adaptation for MuseScore_General.sf2 by S. Christian Collins Copyright (c)
> 2018-19. Temple Blocks instrument provided by Ethan Winer Copyright (c) 2002. Drumline Cymbals provided by
> Michael Schorsch Copyright (c) 2016. MuseScore_General.sf2 is shared under the MIT license, as was
> FluidR3Mono and FluidR3 before it.
>
> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
> associated documentation files (the "Software"), to deal in the Software without restriction, including
> without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
> following conditions: The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
> KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
> PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
> ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
