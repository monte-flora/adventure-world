#!/bin/sh
# Runs the Godot tests headless, then boots the game for 2 s and fails on any script error.
#   sh shadowfall/tools/run_tests.sh [--only=caves]
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
GODOT=${GODOT:-godot}
"$GODOT" --headless --path "$here" --import >/dev/null 2>&1 || true
"$GODOT" --headless --fixed-fps 60 --path "$here" res://tests/run_tests.tscn -- "$@"
log=$("$GODOT" --headless --path "$here" --quit-after 120 2>&1)
echo "$log"
if echo "$log" | grep -E "SCRIPT ERROR|^ERROR|Parse Error" >/dev/null; then
  echo "Boot printed an error." >&2
  exit 1
fi
echo "$log" | grep -q "Shadowfall boot" || { echo "Boot didn't run." >&2; exit 1; }
