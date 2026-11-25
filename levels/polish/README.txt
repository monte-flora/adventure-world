Paint the caves with Gemini: pixi run gemini-caves

Every cave can have a painting behind its blocks (levels/polish/<cave>/painted.webp).
gemini-caves goes through the caves that don't have one yet, one at a time:
the Mines' caves, the stone caves, the Secret Mine, the Nightfall caves, the castle,
and last the Shadow King's throne hall (throne_room/: its map is throne_room.txt).

For each cave:
1. It copies the cave's map (layout.png) and opens Gemini in your browser (only the first time).
   Click Gemini's chat box, press Cmd+V to paste the map, then press Enter in the terminal.
2. It copies the words (prompt.txt). Press Cmd+V in Gemini again and send.
3. Download the painting you like. gemini-caves sees it land in Downloads, moves it here
   and makes painted.webp for the game. Then the next cave.

Keys while it waits: n = skip this cave, q = stop for now.

  pixi run gemini-caves --list                  which caves are painted
  pixi run gemini-caves 03                      just this cave (its number or name)
  pixi run gemini-caves --redo 03_blue_lvl_1 "more ice on the walls"
                                                paint one again, with what to fix
  pixi run gemini-caves --downloads ~/Desktop   watch another folder

Want different words for a cave? Change its prompt.txt: gemini-caves never overwrites it.
It only copies and opens the page: you do the Gemini part yourself (no keys, no robots on the site).

Paint a realm screen with Gemini: pixi run gemini-realm B3

One screen of the realm (30 x 17 squares) as one painting (levels/polish/realm_B3/).
The land file's `painted_screen: B3` line shows it in the game; walls and paths still come
from the land file. Steps (map, then your style picture, then the words):
1. It copies the screen's map (layout.png) and opens Gemini. Cmd+V in Gemini's chat, Enter here.
2. It copies your style picture (the painted-realm mockup: refs/realm_target_painted_mockup.jpg
   next to the game folder, or --style PICTURE). Cmd+V, Enter here.
3. It copies the words (prompt.txt). Cmd+V and send. Download the painting you like:
   it lands in levels/polish/realm_B3/ as painted.webp (960x544). pixi run game.

  pixi run gemini-realm B3 --export     just the map and words
  pixi run gemini-realm B3 --import     a painting you saved in the folder by hand
  python shadowfall/tools/painted_compare.py B3     today vs painted, gloom 0 and 3
