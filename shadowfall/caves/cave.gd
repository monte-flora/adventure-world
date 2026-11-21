extends Node2D
## A cave (side view), built at run time from a levels/ text file. B2 owns this folder.
## Placeholder: rock, ledges and the start work; every other letter is drawn as a coloured square.
##   Scenes.goto("cave", {"file": "caves/01_the_easy_moss_cave.txt"})

const TILE := LevelFile.TILE
const DEFAULT_FILE := "caves/01_the_easy_moss_cave.txt"
const SOLID := "#BMG%I"        # rock-like letters (F, the secret wall, is walked through)
const LEDGE := "=-"            # jump up through it
const COLORS := {"#": "363046", "B": "74482f", "M": "5a5a70", "G": "6b6187", "%": "2f6142",
	"I": "8fd0e0", "=": "a8703f", "-": "d9a95f"}

var level: LevelFile
var map: TileMapLayer
var hero: HeroSide


func _ready() -> void:
	var file: String = Scenes.args.get("file", DEFAULT_FILE)
	build(LevelFile.load_file(Paths.level(file)))


func build(lf: LevelFile) -> void:
	level = lf
	if lf.error != "":
		push_error("cave: " + lf.error)
	map = TileMapLayer.new()
	map.tile_set = _tileset()
	for r in lf.height:
		for c in lf.width:
			var ch := lf.at(c, r)
			if ch in SOLID:
				map.set_cell(Vector2i(c, r), 0, Vector2i(0, 0))
			elif ch in LEDGE:
				map.set_cell(Vector2i(c, r), 0, Vector2i(1, 0))
	add_child(map)
	var marks := Node2D.new()                         # every other letter: a small marker for now
	marks.draw.connect(func():
		for r in lf.height:
			for c in lf.width:
				var ch := lf.at(c, r)
				if ch not in ".S" and ch not in SOLID and ch not in LEDGE:
					marks.draw_rect(Rect2(c * TILE + 8, r * TILE + 8, 16, 16), Color("f7c64a")))
	add_child(marks)
	hero = HeroSide.new()
	hero.position = Vector2(lf.start()) * TILE + Vector2(TILE / 2.0, TILE - HeroSide.SIZE.y / 2.0)
	add_child(hero)
	var cam := Camera2D.new()
	cam.process_callback = Camera2D.CAMERA2D_PROCESS_PHYSICS
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 10.0
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = lf.width * TILE
	cam.limit_bottom = lf.height * TILE
	hero.add_child(cam)


func _tileset() -> TileSet:
	var img := Image.create(TILE * 2, TILE, false, Image.FORMAT_RGBA8)
	img.fill_rect(Rect2i(0, 0, TILE, TILE), Color(COLORS["#"]))
	img.fill_rect(Rect2i(TILE, 0, TILE, 8), Color(COLORS["="]))
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)
	ts.add_physics_layer()
	var src := TileSetAtlasSource.new()
	src.texture = ImageTexture.create_from_image(img)
	src.texture_region_size = Vector2i(TILE, TILE)
	ts.add_source(src, 0)
	var h := TILE / 2.0
	for x in 2:
		src.create_tile(Vector2i(x, 0))
		var td := src.get_tile_data(Vector2i(x, 0), 0)
		td.add_collision_polygon(0)
		if x == 0:
			td.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)]))
		else:
			td.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, -h + 8), Vector2(-h, -h + 8)]))
			td.set_collision_polygon_one_way(0, 0, true)
	return ts
