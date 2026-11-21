#!/bin/sh
# Builds the web version of Shadowfall into shadowfall/build/web/ (needs Godot 4.7.2 and its web
# export templates). The levels are copied in for the export only, then removed, so ../levels stays
# the one copy.   Run from anywhere:  sh shadowfall/tools/export_web.sh
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
GODOT=${GODOT:-godot}
rm -rf "$here/levels" "$here/build/web"
mkdir -p "$here/build/web"
cp -R "$here/../levels" "$here/levels"
trap 'rm -rf "$here/levels"' EXIT
"$GODOT" --headless --path "$here" --import >/dev/null 2>&1 || true
"$GODOT" --headless --path "$here" --export-release Web "$here/build/web/index.html"
test -s "$here/build/web/index.pck"
echo "Web build: $here/build/web/index.html"
