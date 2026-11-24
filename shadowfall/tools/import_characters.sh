#!/bin/sh
# pixi run import-characters [portrait_hero people_smith ...]: Gemini character pictures -> game art (art/gemini/README.txt)
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
GODOT=${GODOT:-godot}
"$GODOT" --headless --path "$here" --import >/dev/null 2>&1 || true
"$GODOT" --headless --audio-driver Dummy --path "$here" --script res://tools/import_characters.gd -- "$@"
"$GODOT" --headless --path "$here" --import >/dev/null 2>&1 || true
