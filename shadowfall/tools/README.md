# shadowfall/tools

Scripts for running, testing and exporting the Godot build (`run_tests.sh`, `export_web.sh`, owned by B0).
B7 (the kid's editor and the cave robot) adds its scripts here; `editor.py` and `cave_solver.py` stay in the repo root.
`polish.py` (+ `polish_import.gd`): the editor's Polish button: the cave map and prompt for Gemini, and the
import that makes `levels/polish/<cave>/painted.webp` (cave size, < 1 MB, shipped as is in the web build).
