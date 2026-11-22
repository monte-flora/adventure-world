class_name RealmTiles
## The realm drawn from art/sheets/realm_<land>.png: one TileSet with a source per land sheet, a
## ground layer (grass, path, water + shore autotile) and an object layer on top (trees, rocks, houses,
## Mines, waystones, gates). Gates and waystones change with Game, so refresh() redraws those.
## B1 owns this file.

const TILE := LevelFile.TILE
const SEA_LAND := "drowned_mere"             # squares no land draws are this land's open water
const NIGHT_LAND := "umbral_reach"
const WATER := "W~.="                        # letters drawn as water underneath
## Letter -> object tile (anim name in the realm sheet). F, X, L and the gates are picked in code.
const OBJECT := {
	"H": "house", "M": "mine", "S": "mine", "P": "portal", "C": "castle", "+": "sign", "T": "chest",
	"V": "vent", "B": "reeds", "#": "bridge", "=": "bridge_broken",
}
const GATE := {"Y": "gate_ivy", "O": "gate_rubble", "K": "gate_thorns"}

var world: WorldMap
var tile_set := TileSet.new()
var _source := {}                            # sheet name -> source id


func _init(w: WorldMap) -> void:
	world = w
	tile_set.tile_size = Vector2i(TILE, TILE)


## The sheet a square is drawn from.
func sheet_at(p: Vector2i) -> String:
	if world.nightfall:
		return "realm_" + NIGHT_LAND
	var id := world.land(p)
	return "realm_" + (WorldMap.realm_id(id) if id != "" else SEA_LAND)


func _src(sheet: String) -> int:
	if _source.has(sheet):
		return _source[sheet]
	if not FileAccess.file_exists(ArtSheet.DIR + sheet + ".json"):
		sheet = "realm_" + SEA_LAND if not sheet.ends_with(SEA_LAND) else sheet
		if _source.has(sheet):
			return _source[sheet]
	var src := TileSetAtlasSource.new()
	src.texture = ArtSheet.texture(sheet)
	src.texture_region_size = Vector2i(TILE, TILE)
	var anims: Dictionary = ArtSheet.meta(sheet)["anims"]
	for a in anims:
		var at := Vector2i(int(anims[a]["col"]), int(anims[a]["row"]))
		src.create_tile(at)
		var n := int(anims[a]["frames"])
		if n > 1:
			src.set_tile_animation_frames_count(at, n)
			for i in n:
				src.set_tile_animation_frame_duration(at, i, 1.0 / float(anims[a]["fps"]))
	var id := tile_set.add_source(src)
	_source[sheet] = id
	return id


func _put(layer: TileMapLayer, p: Vector2i, anim: String) -> void:
	var sheet := sheet_at(p)
	var a: Dictionary = ArtSheet.meta(sheet)["anims"].get(anim, {})
	if a.is_empty():
		layer.erase_cell(p)
		return
	layer.set_cell(p, _src(sheet), Vector2i(int(a["col"]), int(a["row"])))


## A stable 0..n-1 pick per square so grass and path vary without flicker.
static func variant(p: Vector2i, n: int) -> int:
	return absi(p.x * 73856093 ^ p.y * 19349663) % n


func is_water(p: Vector2i) -> bool:
	if p.x < 0 or p.y < 0 or p.x >= world.size.x or p.y >= world.size.y:
		return true
	return not world.cells.has(p) or world.at(p) in WATER


func is_rock(p: Vector2i) -> bool:
	return world.at(p) == "X" and not world.gates.has(p)


## The ground under square p: grass, path or water (with shore edges).
func ground(p: Vector2i) -> String:
	var ch := world.at(p)
	if is_water(p):
		var bits := 0
		for i in 4:
			if is_water(p + [Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT][i]):
				bits |= 1 << i
		return "water" if bits == 15 else "shore_%d" % bits
	if ch in "RI":
		return "path_%d" % variant(p, 3)
	return "ground_%d" % variant(p, 3)


## What stands on square p now (empty = nothing).
func object(p: Vector2i) -> String:
	var ch := world.at(p)
	if world.gates.has(p):
		return "" if world.gate_open(p) else "rock"
	if GATE.has(ch):
		return "" if world.walkable(p) else GATE[ch]
	match ch:
		"F":                                  # canopy over the trunks; the bottom row shows trunks
			return "tree_top" if world.at(p + Vector2i.DOWN) == "F" else "tree"
		"X":
			var alone := true
			for d in [Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT]:
				if is_rock(p + d):
					alone = false
			return "rock" if alone else "cliff_face"
		"L":
			return "waystone"
	return OBJECT.get(ch, "")


## Fills the layers for the whole realm (sea included). canopy (over the hero) gets the tree crown
## above each lone trunk, so a tree is 2 squares tall and you walk behind it.
func paint(ground_layer: TileMapLayer, objects: TileMapLayer, canopy: TileMapLayer = null) -> void:
	ground_layer.tile_set = tile_set
	objects.tile_set = tile_set
	if canopy:
		canopy.tile_set = tile_set
	for r in world.size.y:
		for c in world.size.x:
			var p := Vector2i(c, r)
			_put(ground_layer, p, ground(p))
			var o := object(p)
			if o != "":
				_put(objects, p, o)
			if canopy and o == "tree" and world.at(p + Vector2i.UP) != "F":
				_put(canopy, p + Vector2i.UP, "tree_top")


## Redraws the squares that change with Game: gates and waystones (lit is set by the caller).
func refresh(objects: TileMapLayer, lit: Callable) -> void:
	for p in world.cells:
		var ch: String = world.cells[p]
		if world.gates.has(p) or GATE.has(ch):
			var o := object(p)
			if o == "":
				objects.erase_cell(p)
			else:
				_put(objects, p, o)
		elif ch == "L":
			_put(objects, p, "waystone_lit" if lit.call(p) else "waystone")
