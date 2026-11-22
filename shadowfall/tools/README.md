# shadowfall/tools

Scripts for running, testing and exporting the Godot build (`run_tests.sh`, `export_web.sh`, owned by B0).
B7 (the kid's editor and the cave robot) adds its scripts here; `editor.py` and `cave_solver.py` stay in the repo root.
`polish.py` (+ `polish_import.gd`): the editor's Polish button: the cave map and prompt for Gemini, and the
import that makes `levels/polish/<cave>/painted.webp` (cave size, < 1 MB, shipped as is in the web build).
`import_art.sh` (`pixi run import-art`, + `art_import.gd`, `import_art.gd`): the realm's Gemini art
(`realm/gemini/README.txt`): props keyed off magenta into `realm/props/<name>.png` + `.json`, ground
textures made seamless into `realm/ground/<name>.png`. `make_placeholders.py` draws the striped stand-ins
in `realm/gemini/placeholder/`; `pixi run import-art --placeholders` imports those where `in/` has nothing.
