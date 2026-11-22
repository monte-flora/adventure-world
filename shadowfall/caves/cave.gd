class_name CaveScene
extends Node2D
## A cave (side view), built at run time from a levels/ text file. B2 owns this folder.
##   Scenes.goto("cave", {"file": "caves/01_the_easy_moss_cave.txt"})
##   Scenes.goto("cave", {"text": "theme: stone\n#####\n#S.E#\n#####"})   (tests)
## Every letter's meaning is in tiles.gd (CaveTiles) and levels/README.md. Touch E (or walk out the
## left edge) to go back to the overworld, next to the Mine you came from ("mine" and "realm" args).

const TILE := LevelFile.TILE
const DEFAULT_FILE := "caves/01_the_easy_moss_cave.txt"
# --- the cave's toys, in frames at 60 fps ---
const SPIKE_TRAP_UP := 60                        # A: up this long, then down as long
const JET_OFF := 90                              # J: quiet, then fire 3 tiles up
const JET_ON := 60
const JET_HEIGHT := 3
const GEYSER_EVERY := 150                        # M: a puff every 2.5 s
const GEYSER_PUFF := 30
const GEYSER_HEIGHT := 7.0                       # tiles it throws you
const MUSHROOM_HEIGHT := 5.0                     # tiles a mushroom bounces you
const CRUMBLE_SHAKE := 30                        # -: shakes, falls, comes back
const CRUMBLE_BACK := 180
const LAVA_RISE := 0.6 * TILE                    # pixels a second, after the diamond (lava rises: yes)
const FLARE_REACH := 4.0 * TILE                  # Dawnbrand burns shadow thorns this close
const GEM_GOLD := 1
const CHEST_GOLD := 10
const DIAMOND_GOLD := 25

signal left_cave(file: String)

var level: LevelFile
var file := ""
var grid := PackedStringArray()                  # the drawing; letters change as things break or are taken
var map: TileMapLayer
var hero: HeroSide
var monsters: Node2D
var props: Node2D
var overlay: Node2D
var checkpoint := Vector2.ZERO                   # where you wake up
var clock := 0                                   # frames since the cave opened
var crumbling := {}                              # Vector2i -> frames left before it falls
var fallen := {}                                 # Vector2i -> frames left before it comes back
var traps: Array[Vector2i] = []                  # A
var jets: Array[Vector2i] = []                   # J
var lava_rises := false
var lava_top := INF                              # top of the rising lava, in pixels
var leaving := false
var _solid_index := {}


func _ready() -> void:
	if Scenes.args.has("text"):
		build(LevelFile.from_text(Scenes.args["text"]), "")
	else:
		file = Scenes.args.get("file", DEFAULT_FILE)
		build(LevelFile.load_file(Paths.level(file)), file)


func build(lf: LevelFile, from_file := "") -> void:
	level = lf
	file = from_file
	if lf.error != "":
		push_error("cave: " + lf.error)
	for u in CaveTiles.unknown(lf):
		push_warning("cave %s: unknown letter '%s'" % [file, u])
	grid = lf.rows.duplicate()
	lava_rises = lf.setting("lava rises") == "yes"
	var pal := CaveTiles.palette(lf.theme())
	var bg := ColorRect.new()
	bg.color = Color(pal[3])
	bg.size = Vector2(lf.width, lf.height) * TILE
	add_child(bg)
	map = TileMapLayer.new()
	map.tile_set = _tileset(pal)
	add_child(map)
	for r in lf.height:
		for c in lf.width:
			var ch := lf.at(c, r)
			_set_tile(Vector2i(c, r), ch)
			if ch == "A":
				traps.append(Vector2i(c, r))
			elif ch == "J":
				jets.append(Vector2i(c, r))
	props = Node2D.new()
	add_child(props)
	_add_platforms(Color(pal[2]))
	_add_ropes()
	overlay = Node2D.new()
	overlay.draw.connect(_draw_overlay)
	add_child(overlay)
	monsters = Node2D.new()
	add_child(monsters)
	hero = HeroSide.new()
	hero.cave = self
	checkpoint = Vector2(lf.start()) * TILE + Vector2(TILE / 2.0, TILE - HeroSide.SIZE.y / 2.0)
	hero.position = checkpoint
	add_child(hero)
	_spawn_monsters()
	var cam := Camera2D.new()
	cam.process_callback = Camera2D.CAMERA2D_PROCESS_PHYSICS
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 10.0
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = lf.width * TILE
	cam.limit_bottom = lf.height * TILE
	hero.add_child(cam)
	var light := GloomLight.new()
	light.dark = lf.setting("dark") == "yes"
	add_child(light)
	map.material = light.world_material
	light.follow(hero)
	add_child(preload("res://ui/hud.tscn").instantiate())


# ---------------------------------------------------------------- the grid

func letter(cell: Vector2i) -> String:
	if cell.y < 0 or cell.y >= grid.size() or cell.x < 0 or cell.x >= grid[cell.y].length():
		return "#" if cell.x >= 0 else "."              # off the left edge is the way out
	return grid[cell.y][cell.x]


func cell_of(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x / TILE), floori(p.y / TILE))


func letter_at(p: Vector2) -> String:
	return letter(cell_of(p))


func cell_rect(cell: Vector2i) -> Rect2:
	return Rect2(Vector2(cell) * TILE, Vector2(TILE, TILE))


func set_letter(cell: Vector2i, ch: String) -> void:
	var row := grid[cell.y]
	grid[cell.y] = row.substr(0, cell.x) + ch + row.substr(cell.x + 1)
	_set_tile(cell, ch)


func _set_tile(cell: Vector2i, ch: String) -> void:
	if _solid_index.has(ch):
		map.set_cell(cell, 0, Vector2i(_solid_index[ch], 0))
	else:
		map.erase_cell(cell)


## Cells a rect covers.
func cells_in(r: Rect2) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	var a := cell_of(r.position)
	var b := cell_of(r.end - Vector2(0.01, 0.01))
	for y in range(a.y, b.y + 1):
		for x in range(a.x, b.x + 1):
			out.append(Vector2i(x, y))
	return out


func trap_up() -> bool:
	return (clock / SPIKE_TRAP_UP) % 2 == 0


func jet_on() -> bool:
	return clock % (JET_OFF + JET_ON) >= JET_OFF


func geyser_puffing() -> bool:
	return clock % GEYSER_EVERY < GEYSER_PUFF


# ---------------------------------------------------------------- what the Hero asks

func floor_letter(h: HeroSide) -> String:
	return letter_at(h.position + Vector2(0, HeroSide.SIZE.y / 2.0 + 2))


func wall_letter(h: HeroSide, d: int) -> String:
	return letter_at(h.position + Vector2(d * (HeroSide.SIZE.x / 2.0 + 2), 0))


func ladder_at(h: HeroSide) -> bool:
	return letter_at(h.position) in CaveTiles.CLIMB or letter_at(h.position + Vector2(0, HeroSide.SIZE.y / 2.0 - 2)) in CaveTiles.CLIMB


func is_safe_ground(h: HeroSide) -> bool:
	var y := h.position.y + HeroSide.SIZE.y / 2.0 + 2
	for x in [h.position.x - HeroSide.SIZE.x / 2.0, h.position.x + HeroSide.SIZE.x / 2.0]:
		var under := letter_at(Vector2(x, y))
		if not CaveTiles.is_solid(under) and under != "=":
			return false
	for cell in cells_in(h.rect().grow(TILE)):
		if letter(cell) in CaveTiles.HAZARD:
			return false
	return true


func rope_at(h: HeroSide):
	for r in props.get_children():
		if r is CaveProps.Rope and r.touches(h.position):
			return r
	return null


## The Hero stands on something: mushrooms bounce, geysers throw, crumbly ledges start to shake.
func landed_on(h: HeroSide) -> void:
	for x in [h.position.x - HeroSide.SIZE.x / 2.0 + 1, h.position.x + HeroSide.SIZE.x / 2.0 - 1]:
		var cell := cell_of(Vector2(x, h.position.y + HeroSide.SIZE.y / 2.0 + 2))
		match letter(cell):
			"o":
				h.velocity.y = -sqrt(2.0 * HeroSide.GRAVITY * MUSHROOM_HEIGHT * TILE)
				h.air_jump_used = false
				return
			"M":
				if geyser_puffing():
					h.velocity.y = -sqrt(2.0 * HeroSide.GRAVITY * GEYSER_HEIGHT * TILE)
					return
			"-":
				if not crumbling.has(cell):
					crumbling[cell] = CRUMBLE_SHAKE


## Kingsfall landed: break the cracked rock under the Hero.
func pounded(h: HeroSide) -> void:
	var y := h.position.y + HeroSide.SIZE.y / 2.0 + 2
	for x in [h.position.x - HeroSide.SIZE.x / 2.0, h.position.x, h.position.x + HeroSide.SIZE.x / 2.0]:
		var cell := cell_of(Vector2(x, y))
		if letter(cell) == "B":
			set_letter(cell, ".")


func roof_above(p: Vector2) -> Vector2:
	var cell := cell_of(p)
	while cell.y > 0 and not CaveTiles.is_solid(letter(cell + Vector2i(0, -1))):
		cell.y -= 1
	return Vector2(p.x, cell.y * TILE)


func ground_ahead(m: Node2D, d: float) -> bool:
	var p: Vector2 = m.position + Vector2(d * TILE * 0.6, TILE)
	return CaveTiles.is_solid(letter_at(p)) or letter_at(p) == "="


func shoot(from: Vector2, v: Vector2, _by: Node) -> void:
	var a := CaveMonster.Arrow.new()
	a.cave = self
	a.position = from
	a.velocity = v
	monsters.add_child(a)


func arrow_moved(a) -> void:
	if a.reflected:
		for m in monsters.get_children():
			if m is CaveMonster and m.rect().intersects(a.rect()):
				m.hit(a.position)
				a.queue_free()
				return
	elif a.rect().intersects(hero.rect()):
		hurt_hero(a.position, 1)
		a.queue_free()


func hurt_hero(from: Vector2, amount := 1) -> void:
	if hero.hurt(from, amount) and Game.hearts <= 0:
		_wake_at_checkpoint()


# ---------------------------------------------------------------- every frame

func _physics_process(_dt: float) -> void:
	clock += 1
	if hero == null or leaving:
		return
	_tick_crumbles()
	if lava_top < INF:
		lava_top -= LAVA_RISE / 60.0
	_attack()
	_touch()
	overlay.queue_redraw()


func _touch() -> void:
	var r := hero.rect()
	if hero.position.x < -4.0:
		leave()
		return
	if hero.position.y > level.height * TILE + 64.0:   # fell out of the world: a pit
		_hazard(hero.position)
		return
	var inner := r.grow(-3.0)
	for cell in cells_in(r.grow(2.0)):
		var ch := letter(cell)
		var cr := cell_rect(cell)
		match ch:
			"E":
				if inner.intersects(cr):
					leave()
					return
			"C":
				if inner.intersects(cr) and checkpoint != _cell_spot(cell):
					checkpoint = _cell_spot(cell)
					Game.hearts = Game.max_hearts
					Game.changed.emit()
			"$", "T", "*", "s":
				if inner.intersects(cr):
					_take(cell, ch)
			"u":
				if inner.intersects(cr) and Game.hearts < Game.max_hearts:
					Game.hearts = Game.max_hearts
					Game.changed.emit()
			"^", "~":
				if inner.intersects(Rect2(cr.position + Vector2(4, TILE * 0.5), Vector2(TILE - 8, TILE * 0.5))):
					_hazard(cr.get_center())
					return
			"!":
				if inner.intersects(cr.grow(-6.0)):
					_hazard(cr.get_center())
					return
			"A":
				if trap_up() and inner.intersects(Rect2(cr.position + Vector2(4, TILE * 0.4), Vector2(TILE - 8, TILE * 0.6))):
					_hazard(cr.get_center())
					return
			"n":
				_hazard(cr.get_center())
				return
			"<", ">":
				var open_side := 1.0 if ch == ">" else -1.0
				if (hero.position.x - cr.get_center().x) * open_side > 0.0:
					set_letter(cell, ".")
	if jet_on():
		for j in jets:
			var fire := Rect2(Vector2(j.x * TILE + 6, (j.y - JET_HEIGHT) * TILE), Vector2(TILE - 12, JET_HEIGHT * TILE))
			if inner.intersects(fire):
				_hazard(fire.get_center())
				return
	if r.end.y > lava_top:
		hurt_hero(Vector2(hero.position.x, lava_top + 50), 1)
		hero.velocity.y = -sqrt(2.0 * HeroSide.GRAVITY * 4.0 * TILE)
	for m in monsters.get_children():
		if m is CaveMonster and m.rect().intersects(inner):
			hurt_hero(m.position, 1)


func _cell_spot(cell: Vector2i) -> Vector2:
	return Vector2(cell) * TILE + Vector2(TILE / 2.0, TILE - HeroSide.SIZE.y / 2.0)


## Spikes, fire, lava, pits: lose a heart and go back to the last safe ground.
func _hazard(from: Vector2) -> void:
	if not hero.hurt(from, 1):
		return
	if Game.hearts <= 0:
		_wake_at_checkpoint()
	else:
		hero.position = hero.safe_spot
		hero.velocity = Vector2.ZERO


func _wake_at_checkpoint() -> void:
	Game.hearts = Game.max_hearts
	Game.changed.emit()
	hero.position = checkpoint
	hero.velocity = Vector2.ZERO
	hero.safe_spot = checkpoint
	if lava_top < INF:
		lava_top = level.height * TILE
	for m in monsters.get_children():
		m.queue_free()
	_spawn_monsters()


func _take(cell: Vector2i, ch: String) -> void:
	set_letter(cell, ".")
	match ch:
		"$":
			Game.gold += GEM_GOLD
		"T":
			Game.gold += CHEST_GOLD
			if lava_rises and level.find("*").is_empty():
				lava_top = level.height * TILE
		"*":
			var stone := stone_id()
			if stone != "":
				Game.take_stone(stone)
			else:
				Game.gold += DIAMOND_GOLD
			Game.flags["cave_done:" + file] = true
			if lava_rises:
				lava_top = level.height * TILE
		"s":
			Game.flags["sun_ore"] = int(Game.flags.get("sun_ore", 0)) + 1
	Game.changed.emit()


## Which Light Stone this cave's diamond holds (the "stone:" line), as an id, or "".
func stone_id() -> String:
	var want := level.setting("stone").to_lower().strip_edges()
	if want == "":
		return ""
	for s in Game.STONES:
		if want == s or want == Names.STONE[s].to_lower() or want.begins_with(s + " "):
			return s
	return ""


## R: monsters, levers, arrows; DOWN+R in the air pogos off monsters and spikes.
func _attack() -> void:
	if not hero.attacking():
		return
	var box := hero.attack_rect()
	var down := hero.attack_dir == Vector2i(0, 1)
	var bounced := false
	for m in monsters.get_children():
		if m in hero.attack_hits or not box.intersects(m.rect()):
			continue
		hero.attack_hits.append(m)
		if m is CaveMonster:
			m.hit(hero.position)
			bounced = true
		elif not m.reflected:
			m.reflected = true
			m.velocity = -m.velocity
			bounced = true
	for cell in cells_in(box):
		var ch := letter(cell)
		if ch == "L" and cell not in hero.attack_hits:
			hero.attack_hits.append(cell)
			pull_lever()
		elif ch in "^n" or (ch == "A" and trap_up()):
			bounced = true
	if down and bounced and hero.attack_hits.find("pogo") == -1:
		hero.attack_hits.append("pogo")
		hero.pogo()


func pull_lever() -> void:
	for r in grid.size():
		for c in grid[r].length():
			if grid[r][c] == "G":
				set_letter(Vector2i(c, r), ".")


## G (interact): dig the cracked rock in front of you or under you, or pull a lever.
func dig() -> void:
	var p := hero.position
	for spot in [p + Vector2(hero.facing * (HeroSide.SIZE.x / 2.0 + 8), 0),
			p + Vector2(hero.facing * (HeroSide.SIZE.x / 2.0 + 8), HeroSide.SIZE.y / 2.0 - 4),
			p + Vector2(0, HeroSide.SIZE.y / 2.0 + 8)]:
		var cell := cell_of(spot)
		if letter(cell) == "B":
			set_letter(cell, ".")
			return
		if letter(cell) == "L":
			pull_lever()
			return


## Dawnbrand: the lantern flares and burns the shadow thorns near you.
func flare() -> void:
	for cell in cells_in(Rect2(hero.position - Vector2.ONE * FLARE_REACH, Vector2.ONE * FLARE_REACH * 2.0)):
		if letter(cell) == "n":
			set_letter(cell, ".")


func _tick_crumbles() -> void:
	for cell in crumbling.keys():
		crumbling[cell] -= 1
		if crumbling[cell] <= 0:
			crumbling.erase(cell)
			fallen[cell] = CRUMBLE_BACK
			set_letter(cell, ".")
	for cell in fallen.keys():
		fallen[cell] -= 1
		if fallen[cell] <= 0 and not hero.rect().intersects(cell_rect(cell)):
			fallen.erase(cell)
			set_letter(cell, "-")


func leave() -> void:
	if leaving:
		return
	leaving = true
	left_cave.emit(file)
	var back := {"from_cave": file}
	if Scenes.args.has("mine"):                     # the overworld sent us: back next to that Mine
		back["at"] = Scenes.args["mine"]
	if Scenes.args.has("realm"):
		back["realm"] = Scenes.args["realm"]
	Scenes.goto("overworld", back)


# ---------------------------------------------------------------- building

func _spawn_monsters() -> void:
	for r in level.height:
		for c in level.width:
			var ch := level.at(c, r)
			if ch in CaveTiles.MONSTER:
				var m := CaveMonster.new()
				var size: Vector2 = CaveMonster.KINDS[ch][1]
				m.setup(ch, Vector2(c * TILE + TILE / 2.0, (r + 1) * TILE - size.y / 2.0), self)
				monsters.add_child(m)


## P rows: a 2-wide platform slides along each run of P's. U blocks: a platform as wide as the
## block rides from its top row to its bottom row.
func _add_platforms(col: Color) -> void:
	const H := 12.0
	for r in level.height:
		var c := 0
		while c < level.width:
			if level.at(c, r) != "P":
				c += 1
				continue
			var c0 := c
			while level.at(c, r) == "P":
				c += 1
			var a := Vector2(c0 * TILE, r * TILE)
			var b := Vector2(maxi(c0, c - 2) * TILE, r * TILE)
			_platform(a, b, Vector2(2 * TILE, H), col)
	var seen := {}
	for r in level.height:
		for c in level.width:
			if level.at(c, r) != "U" or seen.has(Vector2i(c, r)):
				continue
			var box := Rect2i(c, r, 1, 1)
			var todo: Array[Vector2i] = [Vector2i(c, r)]
			while not todo.is_empty():
				var p: Vector2i = todo.pop_back()
				if seen.has(p) or level.at(p.x, p.y) != "U":
					continue
				seen[p] = true
				box = box.expand(p).expand(p + Vector2i.ONE)
				for d in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
					todo.append(p + d)
			_platform(Vector2(box.position) * TILE, Vector2(box.position.x, box.end.y - 1) * TILE,
				Vector2(box.size.x * TILE, H), col)


func _platform(a: Vector2, b: Vector2, size: Vector2, col: Color) -> void:
	var p := CaveProps.Platform.new()
	p.setup(a, b, size, col)
	props.add_child(p)


func _add_ropes() -> void:
	for c in level.width:
		var r := 0
		while r < level.height:
			if level.at(c, r) != "R":
				r += 1
				continue
			var r0 := r
			while level.at(c, r) == "R":
				r += 1
			var rope := CaveProps.Rope.new()
			rope.setup(Vector2(c * TILE + TILE / 2.0, r0 * TILE), (r - r0) * TILE)
			props.add_child(rope)


func _tileset(pal: Array) -> TileSet:
	var letters := CaveTiles.SOLID + CaveTiles.LEDGE
	var rock := Color(pal[0])
	var colors := {"#": rock, "B": Color(pal[1]), "M": rock.lightened(0.15), "G": Color("6b6187"),
		"%": Color("2f6142"), "I": Color("8fd0e0"), "o": Color("c0506a"), "<": Color("7a5a3a"),
		">": Color("7a5a3a"), "n": Color("3a1a4a"), "F": rock, "=": Color(pal[2]), "-": Color(pal[2]).darkened(0.3)}
	var img := Image.create(TILE * letters.length(), TILE, false, Image.FORMAT_RGBA8)
	for i in letters.length():
		var ch := letters[i]
		var x := i * TILE
		if ch in CaveTiles.LEDGE:
			img.fill_rect(Rect2i(x, 0, TILE, 8), colors[ch])
			continue
		img.fill_rect(Rect2i(x, 0, TILE, TILE), colors[ch])
		img.fill_rect(Rect2i(x, 0, TILE, 2), Color(colors[ch]).lightened(0.12))
		match ch:
			"B":
				for k in 6:
					img.fill_rect(Rect2i(x + 6 + k * 3, 8 + (k % 2) * 6 + k * 2, 3, 3), rock.darkened(0.4))
			"G":
				for k in 4:
					img.fill_rect(Rect2i(x + 3 + k * 8, 0, 3, TILE), Color("3a3446"))
			"<", ">":
				img.fill_rect(Rect2i(x + (6 if ch == "<" else 18), 12, 8, 8), Color("f7c64a"))
			"M":
				img.fill_rect(Rect2i(x + 12, 0, 8, 6), Color("17141d"))
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)
	ts.add_physics_layer()
	var src := TileSetAtlasSource.new()
	src.texture = ImageTexture.create_from_image(img)
	src.texture_region_size = Vector2i(TILE, TILE)
	ts.add_source(src, 0)
	var h := TILE / 2.0
	for i in letters.length():
		var ch := letters[i]
		_solid_index[ch] = i
		src.create_tile(Vector2i(i, 0))
		if ch == "F":
			continue                                  # a secret wall: you walk right through
		var td := src.get_tile_data(Vector2i(i, 0), 0)
		td.add_collision_polygon(0)
		if ch in CaveTiles.LEDGE:
			td.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, -h + 8), Vector2(-h, -h + 8)]))
			td.set_collision_polygon_one_way(0, 0, true)
		else:
			td.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)]))
	return ts


# ---------------------------------------------------------------- drawing what isn't a tile

func _draw_overlay() -> void:
	var view := Rect2(hero.position - Vector2(700, 420), Vector2(1400, 840))
	for cell in cells_in(view.intersection(Rect2(Vector2.ZERO, Vector2(level.width, level.height) * TILE))):
		var ch := letter(cell)
		if ch == "." or ch == "#":
			continue
		var p := Vector2(cell) * TILE
		var mid := p + Vector2(TILE, TILE) / 2.0
		match ch:
			"^":
				for k in 3:
					overlay.draw_colored_polygon(PackedVector2Array([p + Vector2(k * 10 + 1, TILE), p + Vector2(k * 10 + 6, TILE * 0.5), p + Vector2(k * 10 + 11, TILE)]), Color("c8c8d8"))
			"A":
				var up := trap_up()
				for k in 3:
					overlay.draw_colored_polygon(PackedVector2Array([p + Vector2(k * 10 + 1, TILE), p + Vector2(k * 10 + 6, TILE * (0.4 if up else 0.85)), p + Vector2(k * 10 + 11, TILE)]), Color("c8c8d8") if up else Color("6a6a7a"))
			"!":
				overlay.draw_colored_polygon(PackedVector2Array([p + Vector2(6, TILE), mid + Vector2(0, -12 - (clock / 6) % 3 * 2), p + Vector2(TILE - 6, TILE)]), Color("ff8a2a"))
			"~":
				overlay.draw_rect(Rect2(p + Vector2(0, 6), Vector2(TILE, TILE - 6)), Color("e0453a"))
				overlay.draw_rect(Rect2(p + Vector2(0, 6), Vector2(TILE, 4)), Color("ffb040"))
			"J":
				overlay.draw_rect(Rect2(p + Vector2(8, TILE - 10), Vector2(TILE - 16, 10)), Color("6a6a7a"))
				if jet_on():
					overlay.draw_rect(Rect2(p + Vector2(8, -JET_HEIGHT * TILE + TILE - 10), Vector2(TILE - 16, JET_HEIGHT * TILE)), Color(1, 0.55, 0.15, 0.85))
			"$":
				overlay.draw_colored_polygon(PackedVector2Array([mid + Vector2(0, -7), mid + Vector2(6, 0), mid + Vector2(0, 7), mid + Vector2(-6, 0)]), Color("5ae0c0"))
			"*":
				overlay.draw_colored_polygon(PackedVector2Array([mid + Vector2(0, -12), mid + Vector2(10, 0), mid + Vector2(0, 12), mid + Vector2(-10, 0)]), Color("f7f0a0") if stone_id() != "" else Color("a0e8ff"))
			"s":
				overlay.draw_circle(mid, 8.0, Color("ffb030"))
			"T":
				overlay.draw_rect(Rect2(p + Vector2(4, 12), Vector2(TILE - 8, TILE - 12)), Color("8a5a2a"))
				overlay.draw_rect(Rect2(p + Vector2(4, 16), Vector2(TILE - 8, 3)), Color("f7c64a"))
			"u":
				overlay.draw_rect(Rect2(p + Vector2(4, TILE - 10), Vector2(TILE - 8, 10)), Color("4aa0e0"))
			"E":
				overlay.draw_rect(Rect2(p + Vector2(4, 0), Vector2(TILE - 8, TILE)), Color("1a1020"))
				overlay.draw_rect(Rect2(p + Vector2(4, 0), Vector2(TILE - 8, TILE)), Color("c9a66b"), false, 2.0)
			"C":
				overlay.draw_rect(Rect2(p + Vector2(13, 8), Vector2(6, TILE - 8)), Color("6a5a4a"))
				overlay.draw_circle(p + Vector2(16, 8), 6.0, Color("f7c64a") if checkpoint == _cell_spot(cell) else Color("8a7a5a"))
			"L":
				overlay.draw_line(mid + Vector2(0, 12), mid + Vector2(8, -8), Color("c9a66b"), 3.0)
			"H":
				overlay.draw_line(p + Vector2(6, 0), p + Vector2(6, TILE), Color("8a5a2a"), 3.0)
				overlay.draw_line(p + Vector2(TILE - 6, 0), p + Vector2(TILE - 6, TILE), Color("8a5a2a"), 3.0)
				for k in 3:
					overlay.draw_line(p + Vector2(6, 5 + k * 11), p + Vector2(TILE - 6, 5 + k * 11), Color("8a5a2a"), 2.0)
			"V":
				overlay.draw_line(mid + Vector2(-3, -16), mid + Vector2(3, 16), Color("5d7a3a"), 3.0)
			"F":
				if Game.has_ability("truesight"):
					overlay.draw_rect(Rect2(p, Vector2(TILE, TILE)), Color(0.6, 0.5, 1.0, 0.35))
			"i":
				overlay.draw_circle(mid, 4.0 + (clock / 8) % 2, Color("ffb040"))
			"w":
				overlay.draw_rect(Rect2(p + Vector2(8, 4), Vector2(16, 22)), Color("8aa0d0"))
			"f":
				overlay.draw_rect(Rect2(p + Vector2(8, 0), Vector2(16, 24)), Color("7a2a3a"))
			"-":
				if crumbling.has(cell):
					overlay.draw_rect(Rect2(p + Vector2(randf_range(-1, 1), 0), Vector2(TILE, 8)), Color(1, 1, 1, 0.25))
			"P", "U", "R", "S", "z", "k", "c", "x", "=", "B", "M", "G", "%", "I", "o", "<", ">", "n":
				pass
			_:
				overlay.draw_rect(Rect2(p + Vector2(4, 4), Vector2(24, 24)), Color.MAGENTA)  # an unknown letter
	if lava_top < INF:
		overlay.draw_rect(Rect2(Vector2(0, lava_top), Vector2(level.width * TILE, level.height * TILE - lava_top + 64)), Color(0.88, 0.27, 0.2, 0.9))
