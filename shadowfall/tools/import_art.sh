#!/bin/sh
# pixi run import-art [--placeholders] [oak pine ...]: Gemini pictures -> game art (realm/gemini/README.txt)
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
GODOT=${GODOT:-godot}
"$GODOT" --headless --path "$here" --import >/dev/null 2>&1 || true
"$GODOT" --headless --audio-driver Dummy --path "$here" --script res://tools/import_art.gd -- "$@"
"$GODOT" --headless --path "$here" --import >/dev/null 2>&1 || true
