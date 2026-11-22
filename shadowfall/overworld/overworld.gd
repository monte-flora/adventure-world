extends Node2D
## The overworld (top-down). B1 owns this folder.
##   Scenes.goto("overworld")                              the realm, at home
##   Scenes.goto("overworld", {"at": Vector2i(c, r)})       back from a cave: next to that Mine
##   Scenes.goto("overworld", {"realm": "nightfall"})       the Umbral Reach (Nightfall's mirror)
## Walk onto a Mine to play its cave; onto a waystone (L) to light it (heal, respawn point); G on a lit
## waystone travels to the next lit one. Ability gates (Y ivy cliff, O rubble, K shadow thorns, water,
## gate: lines) stay shut until Game.has_ability(). Placeholder colours until art/ has the tilesets.

const TILE := LevelFile.TILE
const MONSTERS_PER_LAND := 3
## Placeholder colours per letter: light realm, then Nightfall.
const COLORS := {
	"G": "5d8a3c", "F": "2f5a2a", "W": "2c4f7a", "~": "6f97b8", "X": "5b5560", "R": "9a7a4c",
	"M": "3a2f2a", "S": "3a2f2a", "H": "a0603a", "L": "d9b24a", "T": "7a5a2a", "+": "8a6a3a",
	"P": "8a5ad0", "=": "7a5030", "B": "7a8a4a", "I": "b8dce8", "V": "a05a4a", ".": "2c4f7a",
	"O": "7a6a5a", "Y": "3f7a3a", "K": "3a1f3a",
}
const NIGHT := {
	"G": "2e2a3a", "F": "1c1826", "W": "141428", "~": "1e2640", "X": "2a2630", "R": "4a3c40",
	"H": "5a3a5a", "L": "8a6ad0", "P": "c0a0ff", ".": "141428",
}

var world: WorldMap
var realm := "light"
var map: TileMapLayer
var gates_layer: Node2D
var hero: HeroTop
var cam: Camera2D
var banner: Label
var monsters: Array[MapMonster] = []
var respawn := Vector2i.ZERO
var last_cell := Vector2i(-1, -1)


func _ready() -> void:
	realm = Scenes.args.get("realm", "light")
	build(WorldMap.load_nightfall() if realm == "nightfall" else WorldMap.load_realm())


func build(w: WorldMap) -> void:
	world = w
	for e in w.errors:
		push_warning("overworld: " + e)
	var sea := ColorRect.new()                # squares no land draws are open water
	sea.size = Vector2(w.size * TILE)
	sea.color = Color(NIGHT["."] if realm == "nightfall" else COLORS["."])
	add_child(sea)
	map = TileMapLayer.new()
	map.tile_set = _tileset()
	for p in w.cells:
		var ch: String = w.cells[p]
		map.set_cell(p, 0, Vector2i(_index(ch), 0))
	add_child(map)
	gates_layer = Node2D.new()
	gates_layer.draw.connect(_draw_marks)
	add_child(gates_layer)
	Game.changed.connect(gates_layer.queue_redraw)
	hero = HeroTop.new()
	hero.world = w
	hero.hurt.connect(_on_hurt)
	hero.swung.connect(_on_swing)
	var start: Vector2i = w.home
	if Scenes.args.has("at"):
		start = _beside(Scenes.args["at"])
	hero.place(start)
	last_cell = hero.cell()
	respawn = w.home
	add_child(hero)
	_spawn_monsters()
	cam = Camera2D.new()
	cam.process_callback = Camera2D.CAMERA2D_PROCESS_PHYSICS
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 8.0
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = w.size.x * TILE
	cam.limit_bottom = w.size.y * TILE
	cam.position = hero.position
	add_child(cam)
	cam.reset_smoothing()
	var ui := CanvasLayer.new()
	banner = Label.new()
	banner.position = Vector2(24, 20)
	banner.add_theme_font_size_override("font_size", 24)
	ui.add_child(banner)
	add_child(ui)
	_arrive(hero.cell(), true)


func _physics_process(_dt: float) -> void:
	if hero == null:
		return
	cam.position = hero.position
	var c := hero.cell()
	if c != last_cell:
		last_cell = c
		_arrive(c)


## The hero just stepped onto square c (or starts there: then a Portal or Mine underfoot waits for a step).
func _arrive(c: Vector2i, starting := false) -> void:
	var id := world.land(c)
	if id != "" and not Game.flags.get("seen_land_" + id, false):
		Game.flags["seen_land_" + id] = true
		banner.text = world.land_name(id)
		get_tree().create_timer(3.0).timeout.connect(func(): if is_instance_valid(banner): banner.text = "")
	if starting and world.at(c) in "MSP":
		return
	match world.at(c):
		"L":
			light_waystone(c)
		"M", "S":
			if world.cave_of.has(c):
				Scenes.goto("cave", {"file": world.cave_of[c], "from": "overworld", "realm": realm, "mine": c})
		"P":
			if realm == "nightfall":
				Scenes.goto("overworld", {"realm": "light", "at": _portal_in_light()})
			elif Game.stones.size() >= Game.STONES.size():
				Scenes.goto("overworld", {"realm": "nightfall"})


## A waystone is a lantern: lights for good, heals fully, and is where you wake after a fall.
func light_waystone(c: Vector2i) -> void:
	Game.flags["waystone_%s_%d_%d" % [realm, c.x, c.y]] = true
	Game.hearts = Game.max_hearts
	respawn = c
	Game.changed.emit()


func waystone_lit(c: Vector2i) -> bool:
	return Game.flags.get("waystone_%s_%d_%d" % [realm, c.x, c.y], false)


## G on a lit waystone: travel to the next lit one (the pause map, ui/, can offer a full list later).
func travel_from(c: Vector2i) -> bool:
	var lit: Array[Vector2i] = []
	for p in world.waystones:
		if waystone_lit(p):
			lit.append(p)
	if lit.size() < 2 or c not in lit:
		return false
	lit.sort()
	var to := lit[(lit.find(c) + 1) % lit.size()]
	hero.place(to)
	last_cell = to
	respawn = to
	cam.position = hero.position
	cam.reset_smoothing()
	return true


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact") and world.at(hero.cell()) == "L":
		travel_from(hero.cell())


func _on_hurt(hearts_left: int) -> void:
	if hearts_left <= 0:                      # no lives: wake at the last lantern, hearts full
		Game.hearts = Game.max_hearts
		hero.place(respawn)
		hero.iframes = HeroTop.HURT_IFRAMES
		last_cell = respawn
		Game.changed.emit()


func _on_swing(at: Vector2, _facing: Vector2) -> void:
	for m in monsters.duplicate():
		if is_instance_valid(m) and hero.sword_hits(m.position):
			m.hit(2, at)


func _spawn_monsters() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 7 if realm == "light" else 13
	var by_land := {}
	var spots := world.cells.keys()
	spots.sort()
	for p in spots:
		var ch: String = world.cells[p]
		if ch in "GF" and (p - world.home).length() > 8.0:
			by_land.get_or_add(world.land(p), []).append(p)
	var lands := by_land.keys()
	lands.sort()
	for id in lands:
		var pool: Array = by_land[id]
		for i in mini(MONSTERS_PER_LAND, pool.size()):
			var kind: String = "shade" if realm == "nightfall" else ("slime" if id == "home" else ["slime", "zombie"][i % 2])
			var m := MapMonster.new()
			m.setup(world, hero, kind, pool[rng.randi_range(0, pool.size() - 1)], rng.randi())
			m.died.connect(func(dead): monsters.erase(dead))
			monsters.append(m)
			add_child(m)


## The walkable square next to a Mine (so coming back doesn't walk straight back in).
func _beside(c: Vector2i) -> Vector2i:
	for d in [Vector2i.DOWN, Vector2i.RIGHT, Vector2i.LEFT, Vector2i.UP,
			Vector2i(1, 1), Vector2i(-1, 1), Vector2i(1, -1), Vector2i(-1, -1)]:
		if world.walkable(c + d) and world.at(c + d) not in "MSP":
			return c + d
	return c


func _portal_in_light() -> Vector2i:
	var light := WorldMap.load_realm()
	var p := light._first("P")
	return p if p.x >= 0 else light.home


func _draw_marks() -> void:
	for p in world.waystones:                 # lanterns: dim until lit
		var lit := waystone_lit(p)
		var mid := Vector2(p) * TILE + Vector2.ONE * TILE / 2.0
		if lit:
			gates_layer.draw_circle(mid, 30, Color(1.0, 0.8, 0.4, 0.15))
		gates_layer.draw_rect(Rect2(mid - Vector2(5, 10), Vector2(10, 20)), Color("2a2430"))
		gates_layer.draw_circle(mid - Vector2(0, 2), 4, Color("ffd36a") if lit else Color("5a5060"))
	for p in world.cells:                     # ability gates: a bright edge while shut
		var ch: String = world.cells[p]
		var shut: bool = (WorldMap.GATE_LETTERS.has(ch) or world.gates.has(p)) and not world.walkable(p)
		if shut:
			gates_layer.draw_rect(Rect2(Vector2(p) * TILE + Vector2(2, 2), Vector2(TILE - 4, TILE - 4)),
				Color("e0c060"), false, 2.0)


func _letters() -> String:
	var s := ""
	for k in COLORS:
		s += k
	return s


func _index(ch: String) -> int:
	var i := _letters().find(ch)
	return i if i >= 0 else _letters().find("G")


func _tileset() -> TileSet:
	var letters := _letters()
	var img := Image.create(TILE * letters.length(), TILE, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	for i in letters.length():
		var ch := letters[i]
		var base := Color(NIGHT.get(ch, COLORS[ch])) if realm == "nightfall" else Color(COLORS[ch])
		img.fill_rect(Rect2i(i * TILE, 0, TILE, TILE), base)
		for n in 10:                          # a little texture so movement reads
			img.set_pixel(i * TILE + rng.randi_range(0, TILE - 1), rng.randi_range(0, TILE - 1), base.darkened(0.15))
		if ch in "MS":                        # a Mine mouth
			img.fill_rect(Rect2i(i * TILE + 8, 10, 16, 18), Color("0c0a10"))
		elif ch == "H":
			img.fill_rect(Rect2i(i * TILE + 6, 12, 20, 16), base.lightened(0.2))
	var src := TileSetAtlasSource.new()
	src.texture = ImageTexture.create_from_image(img)
	src.texture_region_size = Vector2i(TILE, TILE)
	for i in letters.length():
		src.create_tile(Vector2i(i, 0))
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)
	ts.add_source(src, 0)
	return ts
