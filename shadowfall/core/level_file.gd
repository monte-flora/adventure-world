class_name LevelFile
## Reads one of today's level text files (levels/README.md): setting lines ("theme: moss"), then
## the drawing, one letter per tile. Same rule as caves.py: a line with ":" is a setting.
## New header lines from docs/teen/levels/README.md (stone, land, needs, dark) are read too;
## nothing uses them yet. Owned by core (B0); the tile meanings belong to caves/ (B2).

const TILE := 32                       # pixels per tile (user, 2026-11-21)

var path := ""
var settings := {}                     # "theme" -> "moss", "lava rises" -> "yes", ...
var rows := PackedStringArray()
var width := 0
var height := 0
var error := ""                        # empty when it loaded fine


static func load_file(file_path: String) -> LevelFile:
	var lf := LevelFile.new()
	lf.path = file_path
	if not FileAccess.file_exists(file_path):
		lf.error = "no such level file: " + file_path
		return lf
	lf.parse(FileAccess.get_file_as_string(file_path))
	return lf


static func from_text(text: String) -> LevelFile:
	var lf := LevelFile.new()
	lf.parse(text)
	return lf


func parse(text: String) -> void:
	for raw in text.strip_edges().split("\n"):
		var line := raw.strip_edges()
		if line.is_empty():
			continue
		if ":" in line:
			var kv := line.split(":", true, 1)
			settings[kv[0].strip_edges()] = kv[1].strip_edges()
		else:
			rows.append(line)
	height = rows.size()
	for r in rows:
		width = maxi(width, r.length())
	if height == 0:
		error = "the level has no drawing"
	for i in rows.size():
		if rows[i].length() != width:
			error = "every row must be the same length (row %d isn't)" % i
			rows[i] = rows[i].rpad(width, ".")


func setting(key: String, default := "") -> String:
	return settings.get(key, default)


func theme() -> String:
	return setting("theme", "stone")


## "needs: climb, pound" -> ["climb", "pound"]
func needs() -> PackedStringArray:
	var out := PackedStringArray()
	for n in setting("needs").split(",", false):
		out.append(n.strip_edges())
	return out


func at(col: int, row: int) -> String:
	if row < 0 or row >= height or col < 0 or col >= width:
		return "#"
	return rows[row][col]


## Every tile with this letter, as Vector2i(col, row).
func find(letter: String) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for r in height:
		var c := rows[r].find(letter)
		while c != -1:
			out.append(Vector2i(c, r))
			c = rows[r].find(letter, c + 1)
	return out


func start() -> Vector2i:
	var s := find("S")
	return s[0] if s.size() > 0 else Vector2i(1, height - 2)
