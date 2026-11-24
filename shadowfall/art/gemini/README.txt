MAKING THE CHARACTERS WITH GEMINI
=================================

Same helper as the realm's art (realm/gemini/README.txt), with --set characters:
    pixi run gemini-next --set characters                 the next missing picture
    pixi run gemini-next --set characters --list          which are done, which are missing
    pixi run gemini-next --set characters portrait_hero   just that one (or redo it)
    pixi run gemini-next --set characters --redo people_smith "bigger hands"
It copies the words, opens Gemini, waits for your download, puts it in in/ and runs
pixi run import-characters on it. Start a new Gemini chat for each picture.

What there is (prompts/, 43 pictures):
- portrait_hero, portrait_shadow_king: the title, pause and boss pictures (art/ui/*_portrait.png).
  The Shadow King is drawn on green, not magenta, because he is purple.
- face_<look>: a head-and-shoulders face for each villager look, shown beside the talk box
  (art/ui/faces/<look>.png). The seer is on green too.
  For a face that moves: animate it in Gemini, download the GIF or video. pixi run gemini-next takes
  a .gif, .mp4 or .webm for a face_*; the import (needs ffmpeg: brew install ffmpeg) makes
  art/ui/faces/<look>_anim.png + .json, which plays beside the talk box while the words type.
- people_<look>: each villager standing, 2 copies side by side (still + breathing in), written over
  art/sheets/people_<look>.png. Their spear, lantern or pack is still added by the game, so the
  picture has empty hands. Every direction uses this front view.
- hero_walk_down: a TEST of the hero walking toward you, 4 frames. It never replaces the live hero:
  it goes to art/sheets/candidates/hero_top_walk_down.png. Then run
      pixi run hero-compare
  and look at art/sheets/candidates/hero_compare.png (top: small, left today, right Gemini;
  then today big; then Gemini big). If one frame is off, hero_walk_fix.txt has words for
  Gemini's picture editing in the same chat.

By hand: paste STYLE_portraits.txt (portrait_*, face_*) or STYLE_characters.txt (the rest), then
the prompt; save the picture as in/<prompt name>.png (or .jpg/.webp; a face may be .gif/.mp4/.webm); run pixi run import-characters.
Until you make a picture the game keeps today's art. To undo one, git checkout its file.
assets.json sets the sizes. Never paste passwords or keys anywhere.
