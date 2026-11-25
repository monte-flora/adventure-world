MAKING THE CHARACTERS WITH GEMINI
=================================

Same helper as the realm's art (realm/gemini/README.txt), with --set characters:
    pixi run gemini-next --set characters                 the next missing picture
    pixi run gemini-next --set characters --list          which are done, which are missing
    pixi run gemini-next --set characters portrait_hero   just that one (or redo it)
    pixi run gemini-next --set characters --redo people_smith "bigger hands"
It copies the words, opens Gemini, waits for your download, puts it in in/ and runs
pixi run import-characters on it. Start a new Gemini chat for each picture.

What there is (prompts/, 55 pictures):
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
- hero_<anim>: the map hero (art/sheets/hero_top.png), one picture per row of the sheet:
  hero_idle_down/up/side, hero_walk_down/up/side (4 frames), hero_attack_down/up/side and
  hero_lantern_raise (3 frames), hero_attack_*_sunfang (the same swing with Sunfang; until you make
  one the plain swing is used). Side views face right; the game mirrors them. Each picture is cut
  into its row (art/sheets/candidates/hero_top_<anim>.png) and written into the live sheet; a row
  with no picture keeps today's drawn frames, so a few pictures already work. Roll and hurt stay
  drawn (a tumbling cloak and a flash: Gemini won't keep those steady). The cave hero is not touched.
      pixi run import-hero      just the hero pictures again (import-characters does them too)
      pixi run hero-compare     art/sheets/candidates/hero_compare.png: per row, small (left drawn,
                                right Gemini), then drawn big, then Gemini big
  If one frame is off, hero_walk_fix.txt has words for Gemini's picture editing in the same chat.
  A row too small (a wide swing)? Raise its box in assets.json "hero", then pixi run import-hero.
  Undo one row: delete in/hero_<anim>.* and candidates/hero_top_<anim>.png, then pixi run import-hero
  (or git checkout art/sheets/hero_top.png for all of them).

By hand: paste STYLE_portraits.txt (portrait_*, face_*) or STYLE_characters.txt (the rest), then
the prompt; save the picture as in/<prompt name>.png (or .jpg/.webp; a face may be .gif/.mp4/.webm); run pixi run import-characters.
Until you make a picture the game keeps today's art. To undo one, git checkout its file.
assets.json sets the sizes. Never paste passwords or keys anywhere.
