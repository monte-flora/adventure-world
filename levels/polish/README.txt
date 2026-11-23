Paint the caves with Gemini: pixi run gemini-caves

Every cave can have a painting behind its blocks (levels/polish/<cave>/painted.webp).
gemini-caves goes through the caves that don't have one yet, one at a time:
the Mines' caves, the stone caves, the Secret Mine, the Nightfall caves, then the castle.

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
