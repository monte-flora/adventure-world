# One painted realm screen (Emberwick, B3)

`compare_B3.jpg`: today's B3 (left) vs B3 painted (right), gloom 0 (top) and 3 (bottom), in the real
overworld. The painting here is a PLACEHOLDER (the layout, blurred): the real one is the user's
Gemini painting and is never committed. Remake: `python shadowfall/tools/painted_compare.py B3 --placeholder`;
with the real painting in `levels/polish/realm_B3/`, drop `--placeholder`.

How it works: `shadowfall/painted/realm_screen.gd`. The painting lies over the screen's ground; each prop
and tree there is re-skinned with the painting cut out in its own shape, so it keeps its y-sort (you walk
behind canopies and roofs), its lights and the gloom. Gates (rubble, thorns) stay sprites: they open.
