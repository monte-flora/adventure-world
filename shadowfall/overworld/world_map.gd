class_name WorldMap
## The realm as one grid of letters, stitched from the land files in levels/world/ (levels/README.md,
## "The Phase 2 world map"): each file's `at: row col` puts its drawing on the big map, `.` is "not
## this land", squares no land draws are open water. B1 owns this file.
## The realm is a grid of screens, 6 × 5 screens of 30 × 17 squares (docs/teen/levels R10); Nightfall
## (the Umbral Reach) is the 3 × 3 screens in the middle, the same footprint with dark terrain (R15).

const SCREEN := Vector2i(30, 17)        # squares per screen (960 × 540 at 32 px)
const GRID := Vector2i(6, 5)            # screens across, down
const MIRROR_FROM := Vector2i(2, 1)     # Nightfall mirrors screens C2..E4 (0-based column 2, row 1)
const MIRROR_SIZE := Vector2i(3, 3)

## Letters you can never walk on; water needs Tidebinder (swim). `.` is open water.
const SOLID := "X#"
const WATER := "W~O.="                  # O on today's maps is bubbles in the water; = a broken bridge
## Ability gates (docs/teen/levels §5): shut until the hero has the ability.
const GATE_LETTERS := {"Y": "climb", "K": "flare", "O": "pound"}
## Which land a world file is, by its number (levels/world/01 ... 08; the files keep their numbers).
## Display names come from rules/names.gd (Names.LAND), falling back to the file's `name:` line.
const LAND_OF_NUMBER := {"01": "home", "02": "woods", "03": "lake", "04": "portal", "05": "ruins",
	"06": "frost", "07": "desert", "08": "swamp", "09": "nightfall"}
## The levels/realm/ land ids by their rules/names.gd id (Names.LAND keys); art sheets are realm_<that>.
const REALM_ID := {"home": "emberhold", "woods": "weepingwold", "ruins": "hollowcrown",
	"lake": "drowned_mere", "frost": "wintermarch", "desert": "cinder_wastes", "swamp": "mirefen",
	"portal": "shadowgate", "nightfall": "umbral_reach"}

var cells := {}                         # Vector2i(col, row) -> letter
var land_of := {}                       # Vector2i -> land id
var lands := {}                         # land id -> {"name", "file", "rect": Rect2i, "says"}
var size := Vector2i.ZERO               # columns, rows
var home := Vector2i(-1, -1)
var mines: Array[Vector2i] = []         # nearest home first
var cave_of := {}                       # Mine cell -> cave file inside levels/ ("caves/01_....txt")
var waystones := {}                     # cell -> land id (each land's L)
var gates := {}                         # cell -> {"name", "needs"}: an ability id or a number of stones
var nightfall := false
## Props (levels/README.md "Props on the realm"): {"name", "at": Vector2 px (the prop's anchor), "meta"}.
var props: Array[Dictionary] = []
var prop_rects: Array[Rect2] = []       # footprints in realm px
var prop_solid: Array[Rect2] = []       # footprint parts inside blocked squares: the hero bumps into these
var prop_cells := {}                    # squares whose middle is under a footprint: nobody walks there
var prop_cover := {}                    # squares a prop stands on or hides: no tree, house or Mine tile there
const OPEN := "MSPLHT+"                 # squares a prop never blocks (Mines, waystones, houses, chests ...)
const PROP_DIR := "res://realm/props/"
var errors: PackedStringArray = []


## Where the land files are: levels/realm/ (the redrawn 6 × 5 realm) once it exists, else levels/world/.
static func land_folder() -> String:
	return "realm" if DirAccess.dir_exists_absolute(Paths.level("realm")) else "world"


## The light realm from every land file (the Umbral Reach's file, `world: umbral_reach`, is left out).
static func load_realm() -> WorldMap:
	var texts := {}
	for f in Paths.level_files(land_folder()):
		var text := FileAccess.get_file_as_string(Paths.level(f))
		if LevelFile.from_text(text).setting("world") == "":
			texts[f] = text
	var wm := WorldMap.new()
	wm.stitch(texts)
	wm.plan_caves(Paths.level_files("caves"), Paths.level_files("secret"))
	return wm


## Nightfall: the centre 3 × 3 screens of the light realm, in the dark.
static func load_nightfall() -> WorldMap:
	var light := load_realm()
	var wm := light.mirror()
	for f in Paths.level_files(land_folder()):       # its look (ground, paint, forest, crags, props) is its file's
		var lf := LevelFile.load_file(Paths.level(f))
		if lf.setting("world") == "umbral_reach":
			wm.dress(lf, f)
	wm.plan_caves(Paths.level_files("shadow"), PackedStringArray())
	return wm


## texts: file path ("world/01_home_meadow.txt") -> its text.
func stitch(texts: Dictionary) -> void:
	var names: Dictionary = _names("LAND")
	var keys := texts.keys()
	keys.sort()
	for f in keys:
		var lf := LevelFile.from_text(texts[f])
		var stem: String = f.get_file().get_basename()
		var id: String = lf.setting("land", LAND_OF_NUMBER.get(stem.left(2), stem))
		if lf.error != "":
			errors.append("%s: %s" % [f, lf.error])
		var at := lf.setting("at", "0 0").split(" ", false)
		if at.size() != 2:
			errors.append("%s: `at:` needs a row and a column" % f)
			continue
		var origin := Vector2i(int(at[1]), int(at[0]))
		var display: String = names.get(names_id(id), lf.setting("name", id))
		if names_id(id) == "home" and _names("HOME") != "":
			display = _names("HOME")
		lands[id] = {"name": display, "file": f, "rect": Rect2i(origin, Vector2i(lf.width, lf.height)),
			"says": lf.setting("says"), "ground": lf.setting("ground"), "paint": lf.all("paint"),
			"forest": lf.setting("forest").split(" ", false), "crags": lf.setting("crags").split(" ", false)}
		for r in lf.height:
			for c in lf.width:
				var ch := lf.at(c, r)
				if ch == ".":
					continue
				var p := origin + Vector2i(c, r)
				if cells.has(p):
					errors.append("%s and %s both draw square %d %d" % [lands[land_of[p]].file, f, p.y, p.x])
				cells[p] = ch
				land_of[p] = id
				size = Vector2i(maxi(size.x, p.x + 1), maxi(size.y, p.y + 1))
				if ch == "L":
					waystones[p] = id
		var h := lf.setting("home").split(" ", false)
		if h.size() == 2:
			home = origin + Vector2i(int(h[1]), int(h[0]))
		for line in lf.all("mine"):
			# "stone/1_the_crumbling_vigil.txt 23 8": the cave under the Mine at that row, column
			var mp := line.split(" ", false)
			if mp.size() == 3:
				cave_of[origin + Vector2i(int(mp[2]), int(mp[1]))] = mp[0]
		for line in lf.all("gate"):
			# "Desert Gate 7 0 3" or "Ivy Cliff 3 4 climb": name, row, col, then a level/stone count or an ability
			var parts := line.split(" ", false)
			if parts.size() >= 4:
				var cell := origin + Vector2i(int(parts[-2]), int(parts[-3]))
				gates[cell] = {"name": " ".join(parts.slice(0, parts.size() - 3)), "needs": parts[-1]}
		for line in lf.all("prop"):
			add_prop(line, origin, f)
	if home.x < 0:
		home = _first("H")
	for p in cells:
		if cells[p] == "M" or cells[p] == "S":
			mines.append(p)
	_sort_by_home(mines)


## Every Mine plays a cave file, nearest home first; the files go round again when there are more
## Mines than files (caves.py plan_cave_files). An S (the Secret Mine) plays the secret files.
func plan_caves(files: PackedStringArray, secret: PackedStringArray) -> void:
	var i := 0
	var s := 0
	for m in mines:
		if cave_of.has(m):                    # a mine: line already named its cave
			continue
		if cells[m] == "S" and secret.size() > 0:
			cave_of[m] = secret[s % secret.size()]
			s += 1
		elif files.size() > 0:
			cave_of[m] = files[i % files.size()]
			i += 1


## The Umbral Reach's painted look from its file: `ground:`, `paint:`, `forest:`, `crags:` and `prop:`
## lines (props in the mirror's own rows and columns).
func dress(lf: LevelFile, file := "") -> void:
	var land: Dictionary = lands["nightfall"]
	land["ground"] = lf.setting("ground")
	land["paint"] = lf.all("paint")
	land["forest"] = lf.setting("forest").split(" ", false)
	land["crags"] = lf.setting("crags").split(" ", false)
	for line in lf.all("prop"):
		add_prop(line, Vector2i.ZERO, file)


## The Umbral Reach: the centre screens, same footprint, dark terrain. Its home is the Portal.
func mirror() -> WorldMap:
	var wm := WorldMap.new()
	wm.nightfall = true
	var from := MIRROR_FROM * SCREEN
	var span := MIRROR_SIZE * SCREEN
	var reach: String = _names("LAND").get("nightfall", "the Umbral Reach")
	wm.lands["nightfall"] = {"name": reach, "file": "", "rect": Rect2i(Vector2i.ZERO, span), "says": ""}
	for r in span.y:
		for c in span.x:
			var p := Vector2i(c, r)
			var ch: String = cells.get(from + p, "W")
			if ch == "M" and wm.mines.size() >= 3:
				ch = "G"                            # Nightfall has 3 shadow caves
			wm.cells[p] = ch
			wm.land_of[p] = "nightfall"
			if ch == "M":
				wm.mines.append(p)
			elif ch == "L":
				wm.waystones[p] = "nightfall"
	wm.size = span
	wm.home = wm._first("P")
	if wm.home.x < 0:
		wm.home = wm._first_walkable()
	wm._sort_by_home(wm.mines)
	return wm


## One `prop: oak 12 30` line (the land's row and column; decimals move it part of a square): its
## anchor sits on the middle of that square. Unknown props are reported in errors and skipped.
func add_prop(line: String, origin: Vector2i, file := "") -> void:
	var parts := line.split(" ", false)
	if parts.size() != 3 or not parts[1].is_valid_float() or not parts[2].is_valid_float():
		errors.append("%s: `prop: %s` wants a name, a row and a column" % [file, line])
		return
	var meta := prop_meta(parts[0])
	if meta.is_empty():
		errors.append("%s: no prop called %s in realm/props/" % [file, parts[0]])
		return
	var pos := (Vector2(origin) + Vector2(float(parts[2]), float(parts[1])) + Vector2(0.5, 0.5)) * LevelFile.TILE
	props.append({"name": parts[0], "at": pos, "meta": meta})
	var t := float(LevelFile.TILE)
	var anchor: Array = meta.anchor
	var art := Rect2(pos - Vector2(anchor[0], anchor[1]), Vector2(meta.size[0], meta.size[1]))
	prop_cover[Vector2i(floori(pos.x / t), floori(pos.y / t))] = true
	for row in range(floori(art.position.y / t), ceili(art.end.y / t)):
		for col in range(floori(art.position.x / t), ceili(art.end.x / t)):
			if art.has_point((Vector2(col, row) + Vector2(0.5, 0.5)) * t):
				prop_cover[Vector2i(col, row)] = true
	var foot: Array = meta.get("foot", [])
	if foot.size() != 4:
		return
	var r := Rect2(pos + Vector2(foot[0] - anchor[0], foot[1] - anchor[1]), Vector2(foot[2], foot[3]))
	prop_rects.append(r)
	for row in range(floori(r.position.y / t), ceili(r.end.y / t)):
		for col in range(floori(r.position.x / t), ceili(r.end.x / t)):
			var c := Vector2i(col, row)
			if r.grow(1.0).has_point((Vector2(c) + Vector2(0.5, 0.5)) * t) and at(c) not in OPEN:
				prop_cells[c] = true
				prop_solid.append(r.intersection(Rect2(Vector2(c) * t, Vector2(t, t))))


static var _meta := {}


## A prop's JSON from realm/props/ (cached), or {} if there is none.
static func prop_meta(name: String) -> Dictionary:
	if not _meta.has(name):
		var p := PROP_DIR + name + ".json"
		var d = JSON.parse_string(FileAccess.get_file_as_string(p)) if FileAccess.file_exists(p) else null
		_meta[name] = d if d is Dictionary else {}
	return _meta[name]


## Does a prop's footprint stop the hero's box (realm px)? Only inside the squares it blocks, so a
## walk from square middle to square middle (WorldMap.path) never snags on one.
func prop_blocks(box: Rect2) -> bool:
	for r in prop_solid:
		if r.intersects(box):
			return true
	return false


func at(p: Vector2i) -> String:
	return cells.get(p, ".")


func land(p: Vector2i) -> String:
	return land_of.get(p, "")


func land_name(id: String) -> String:
	return lands[id].name if lands.has(id) else ""


## Can the hero stand on this square now? Gates read Game.has_ability() every time.
func walkable(p: Vector2i) -> bool:
	if p.x < 0 or p.y < 0 or p.x >= size.x or p.y >= size.y:
		return false
	if gates.has(p):
		return gate_open(p)
	if prop_cells.has(p):
		return false
	var ch := at(p)
	if ch in SOLID:
		return false
	if GATE_LETTERS.has(ch):
		return Game.has_ability(GATE_LETTERS[ch])
	if ch in WATER:
		return Game.has_ability("swim")
	return true


func gate_open(p: Vector2i) -> bool:
	var needs: String = gates[p].needs
	if needs.is_valid_int():
		return Game.stones.size() >= int(needs)
	return Game.has_ability(needs)


## A land's id in rules/names.gd ("emberhold" -> "home"); old ids stay as they are.
static func names_id(id: String) -> String:
	var k = REALM_ID.find_key(id)
	return k if k != null else id


## A land's levels/realm/ id ("home" -> "emberhold"): its art sheet is realm_<that>.
static func realm_id(id: String) -> String:
	return REALM_ID.get(id, id)


## Which screen (column, row) a square is on.
static func screen_of(p: Vector2i) -> Vector2i:
	return Vector2i(p.x / SCREEN.x, p.y / SCREEN.y)


## The shortest walk (4-way) between two squares as it is now; empty if there is none.
func path(from: Vector2i, to: Vector2i) -> Array[Vector2i]:
	var came := {from: from}
	var queue: Array[Vector2i] = [from]
	var head := 0
	while head < queue.size():
		var p := queue[head]
		head += 1
		if p == to:
			var out: Array[Vector2i] = []
			while p != from:
				out.push_front(p)
				p = came[p]
			return out
		for d in [Vector2i.RIGHT, Vector2i.LEFT, Vector2i.DOWN, Vector2i.UP]:
			var q: Vector2i = p + d
			if not came.has(q) and (walkable(q) or q == to):
				came[q] = p
				queue.append(q)
	return []


func _sort_by_home(list: Array[Vector2i]) -> void:
	var h := home
	list.sort_custom(func(a: Vector2i, b: Vector2i) -> bool:
		var da := (a - h).length_squared()
		var db := (b - h).length_squared()
		return da < db or (da == db and (a.y < b.y or (a.y == b.y and a.x < b.x))))


func _first(letter: String) -> Vector2i:
	var best := Vector2i(-1, -1)
	for p in cells:
		if cells[p] == letter and (best.x < 0 or p.y < best.y or (p.y == best.y and p.x < best.x)):
			best = p
	return best


func _first_walkable() -> Vector2i:
	for r in size.y:
		for c in size.x:
			if walkable(Vector2i(c, r)):
				return Vector2i(c, r)
	return Vector2i.ZERO


## A display-name table from rules/names.gd (B4's), or {} / "" while it doesn't have one yet.
static func _names(key: String):
	var consts: Dictionary = load("res://rules/names.gd").get_script_constant_map()
	return consts.get(key, {} if key != "HOME" else "")
