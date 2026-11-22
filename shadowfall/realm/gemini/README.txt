MAKING THE REALM'S ART WITH GEMINI
==================================

The ground is a few seamless textures (grass, road, water ...). Everything that stands on it (trees,
houses, lampposts, the campfire ...) is a "prop": one picture each, placed in the level files.
Until you make a picture, the game uses a grey-and-stripes placeholder for it.

1. Pick a prompt in prompts/ (ground_*.txt are the ground textures, the rest are props).
2. Open Gemini. Paste ALL of STYLE.txt, then the whole prompt file, and send it.
3. Like it? Download the picture and save it in the in/ folder, named after the prompt file:
       prompts/oak.txt          ->  in/oak.png
       prompts/ground_grass.txt ->  in/ground_grass.png
   (.png, .jpg or .webp all work.) Not great? Ask Gemini for another one: "again, but darker leaves".
4. In the terminal, in the game folder, run:
       pixi run import-art
   It cuts out the magenta background, shrinks the picture to the game's pixel size, makes ground
   textures tile with no seams, and writes shadowfall/realm/props/<name>.png + <name>.json
   (or shadowfall/realm/ground/<name>.png).
5. Play (pixi run shadowfall) or open the prop editor (pixi run realm-editor) to see it.

Tips
- Props must be ALONE on flat magenta (#FF00FF). If the cut-out has pink edges, ask Gemini for a
  "flatter, pure magenta background".
- assets.json says how big each prop is in the game and which part of it you bump into ("foot").
- A prop's .json in realm/props/ can be tweaked by hand (foot, anchor, lights, front). Put
  "keep": true in it and the next import keeps your changes.
- Never paste passwords or keys anywhere. Gemini only ever gets these prompts.
