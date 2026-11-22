class_name CaveScene
extends Node2D
## A cave (side view), built at run time from a levels/ text file. B2 owns this folder.
##   Scenes.goto("cave", {"file": "caves/01_the_easy_moss_cave.txt"})
##   Scenes.goto("cave", {"text": "theme: stone\n#####\n#S.E#\n#####"})   (tests)
## Every letter's meaning is in tiles.gd (CaveTiles) and levels/README.md. Touch E (or walk out the
## left edge) to go back to the overworld, next to the Mine you came from ("mine" and "realm" args).

const TILE := LevelFile.TILE
const DEFAULT_FILE := "caves/01_the_easy_moss_cave.txt"
const LADDER_LAYER := 4                          # physics layer bit of ladder tops
const LADDER_TOP := "h"                          # tile only: the top rung of H or V, a one-way ledge
# --- the cave's toys, in frames at 60 fps (the pygame game's numbers, caves.py) ---
# Spike traps (A), flame jets (J) and steam geysers (M) all go off together, on one clock:
const TRAP_DOWN := 78                            # quiet this long (1.3 s)...
const TRAP_UP := 54                              # ...then on this long (0.9 s)
const TRAP_WARN := 24                            # jets and geysers fizzle this long before they go off
const JET_HEIGHT := 3                            # J: fire from its own block and 2 above
const GEYSER_HEIGHT := 7.4                       # M: tiles it throws you (you rise about 7)
const MUSHROOM_HEIGHT := 6.3                     # o: tiles a mushroom bounces you (about 6)
const CRUMBLE_SHAKE := 54                        # -: shakes 0.9 s, falls, comes back after 3 s
const CRUMBLE_BACK := 180
const LAVA_WAIT := 120                           # lava rises: yes: 2 s after the diamond...
const LAVA_RISE := 1.0 * TILE                    # ...then a tile a second, and stops just below E
const SPRING_REFILL := 3600                      # u: a healing spring fills up again after 60 s
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
var lava_wait := 0
var lava_stop := 0.0                             # the lava never rises above this
var springs := {}                                # Vector2i -> frames until a used spring is full again
var leaving := false
var heal := LumenHeal.new()                      # Q, standing still: a Lumen charge becomes a heart
var _solid_index := {}
var art_sheet := "tiles_stone"                   # the theme's tile sheet (CaveArt)
var art_tex: Texture2D
var parallax: Array[Parallax2D] = []             # far, back, mid, front
var cam: Camera2D
var juice: CaveJuice                             # hit-stop, shake, sparks, dust, hurt edge


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
	art_sheet = CaveArt.sheet(lf.theme())
	art_tex = ArtSheet.texture(art_sheet)
	for l in CaveArt.LAYERS:
		parallax.append(CaveArt.layer(lf.theme(), l[0], l[1]))
	for i in 3:
		add_child(parallax[i])
	map = TileMapLayer.new()
	map.tile_set = _tileset()
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
	add_child(parallax[3])                         # the front layer passes in front of the Hero
	juice = CaveJuice.new(self)
	add_child(juice)
	cam = Camera2D.new()
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
	for p in parallax:
		p.get_child(0).material = light.world_material
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
	for d in [Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT]:
		if letter(cell + d) in "#F":                # rock edges follow what is next to them
			_set_tile(cell + d, letter(cell + d))


## Which sides of a cell are rock (N1 E2 S4 W8), for the solid_<bits> tile.
func _rock_bits(cell: Vector2i) -> int:
	var bits := 0
	for i in 4:
		if letter(cell + [Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT][i]) in CaveTiles.SOLID:
			bits |= 1 << i
	return bits


func _set_tile(cell: Vector2i, ch: String) -> void:
	if cell.y < 0 or cell.y >= grid.size() or cell.x < 0 or cell.x >= grid[cell.y].length():
		return
	if ch == "#" or ch == "F":
		map.set_cell(cell, 0, Vector2i(_rock_bits(cell), 1 if ch == "#" else 2))
	elif _solid_index.has(ch):
		map.set_cell(cell, 0, Vector2i(_solid_index[ch], 0))
	elif ch in CaveTiles.CLIMB and letter(cell + Vector2i.UP) not in CaveTiles.CLIMB:
		map.set_cell(cell, 0, Vector2i(_solid_index[LADDER_TOP], 0))   # stand on a ladder's top
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


## Spike traps, flame jets and geysers: are they on right now? (all together, like pygame)
func trap_up() -> bool:
	return clock % (TRAP_DOWN + TRAP_UP) >= TRAP_DOWN


## Jets and geysers fizzle just before they go off, so you can see it coming.
func about_to_go_off() -> bool:
	var t := clock % (TRAP_DOWN + TRAP_UP)
	return t >= TRAP_DOWN - TRAP_WARN and t < TRAP_DOWN


func jet_on() -> bool:
	return trap_up()


func geyser_puffing() -> bool:
	return trap_up()


## A flame jet's fire: its own block and the 2 above it.
func jet_fire(j: Vector2i) -> Rect2:
	return Rect2(Vector2(j.x * TILE + 6, (j.y - JET_HEIGHT + 1) * TILE), Vector2(TILE - 12, JET_HEIGHT * TILE))


## The top rung of a ladder (or the top of a vine) works like a ledge: you can stand on it.
func ladder_top(cell: Vector2i) -> bool:
	return letter(cell) in CaveTiles.CLIMB and letter(cell + Vector2i.UP) not in CaveTiles.CLIMB


# ---------------------------------------------------------------- what the Hero asks

func floor_letter(h: HeroSide) -> String:
	return letter_at(h.position + Vector2(0, HeroSide.SIZE.y / 2.0 + 2))


func wall_letter(h: HeroSide, d: int) -> String:
	return letter_at(h.position + Vector2(d * (HeroSide.SIZE.x / 2.0 + 2), 0))


func ladder_at(h: HeroSide) -> bool:
	return letter_at(h.position) in CaveTiles.CLIMB or letter_at(h.position + Vector2(0, HeroSide.SIZE.y / 2.0 - 2)) in CaveTiles.CLIMB


## Standing on the top of a ladder: DOWN climbs down it.
func ladder_below(h: HeroSide) -> bool:
	return letter_at(h.position + Vector2(0, HeroSide.SIZE.y / 2.0 + 4)) in CaveTiles.CLIMB


## The middle of the ladder the Hero is on (hands on the middle, like pygame).
func ladder_x(h: HeroSide) -> float:
	return (floorf(h.position.x / TILE) + 0.5) * TILE


func is_safe_ground(h: HeroSide) -> bool:
	var y := h.position.y + HeroSide.SIZE.y / 2.0 + 2
	for x in [h.position.x - HeroSide.SIZE.x / 2.0, h.position.x + HeroSide.SIZE.x / 2.0]:
		var under := letter_at(Vector2(x, y))
		if not CaveTiles.is_solid(under) and under != "=" and under not in CaveTiles.CLIMB:
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


## A hard landing: dust at the Hero's feet.
func landed_hard(h: HeroSide) -> void:
	juice.dust(h.position + Vector2(0, HeroSide.SIZE.y / 2.0))


## Kingsfall landed: break the cracked rock under the Hero.
func pounded(h: HeroSide) -> void:
	var y := h.position.y + HeroSide.SIZE.y / 2.0 + 2
	juice.slam(Vector2(h.position.x, y - 2))
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
				juice.hit(m, m.hit(a.position))
				a.queue_free()
				return
	elif a.rect().intersects(hero.rect()):
		hurt_hero(a.position, 1)
		a.queue_free()


func hurt_hero(from: Vector2, amount := 1) -> void:
	if not hero.hurt(from, amount):
		return
	juice.hurt()
	heal.hit()
	if Game.hearts <= 0:
		_wake_at_checkpoint()


# ---------------------------------------------------------------- every frame

func _physics_process(dt: float) -> void:
	if hero == null or leaving:
		clock += 1
		return
	juice.step(dt, cam)
	if juice.stopped():                             # hit-stop: the whole cave waits, traps too
		return
	clock += 1
	_tick_crumbles()
	for cell in springs.keys():
		springs[cell] -= 1
		if springs[cell] <= 0:
			springs.erase(cell)
	if lava_top < INF:
		if lava_wait > 0:
			lava_wait -= 1
		else:
			lava_top = maxf(lava_stop, lava_top - LAVA_RISE / 60.0)
	_attack()
	heal.step(Input.is_action_pressed("heal"), hero.is_on_floor() and absf(hero.velocity.x) < 1.0)
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
	var ll := lost_light_spot()
	if ll.x < INF and inner.intersects(Rect2(ll - Vector2.ONE * TILE / 2.0, Vector2.ONE * TILE)):
		Vitals.recover_lost_light()
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
					Game.save()                    # a lantern shrine keeps your journey
			"$", "T":
				if inner.intersects(cr):
					_take(cell, ch)
			"*", "s":                                   # solid ore: bump it (or strike it, or dig it)
				if r.grow(1.0).intersects(cr):
					_take(cell, ch)
			"u":
				if inner.intersects(cr) and Game.hearts < Game.max_hearts and not springs.has(cell):
					Game.hearts = Game.max_hearts
					springs[cell] = SPRING_REFILL
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
			var fire := jet_fire(j)
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
	juice.hurt()
	heal.hit()
	if Game.hearts <= 0:
		_wake_at_checkpoint()
	else:
		hero.position = hero.safe_spot
		hero.velocity = Vector2.ZERO


## Your last heart: the gold stays here as a Lost Light (on safe ground if you fell out of the
## world), and you wake at the last lantern shrine.
func _wake_at_checkpoint() -> void:
	var at := hero.position
	if not Rect2(Vector2.ZERO, Vector2(level.width, level.height) * TILE).has_point(at):
		at = hero.safe_spot
	Vitals.die({"scene": "cave", "file": file, "x": at.x, "y": at.y})
	heal.hit()
	hero.position = checkpoint
	hero.velocity = Vector2.ZERO
	hero.safe_spot = checkpoint
	if lava_top < INF:
		_start_lava()
	for m in monsters.get_children():
		m.queue_free()
	_spawn_monsters()


## Where this cave's Lost Light waits, or INF if it is somewhere else (or there is none).
func lost_light_spot() -> Vector2:
	var ll := Vitals.lost_light()
	var w: Dictionary = ll.get("where", {})
	if w.get("scene", "") != "cave" or w.get("file", "") != file:
		return Vector2.INF
	return Vector2(w.x, w.y)


func _take(cell: Vector2i, ch: String) -> void:
	set_letter(cell, ".")
	match ch:
		"$":
			Game.gold += GEM_GOLD
		"T":
			Game.gold += CHEST_GOLD
			if lava_rises and level.find("*").is_empty():
				_start_lava()
		"*":
			var stone := stone_id()
			if stone != "":
				Game.take_stone(stone)
			else:
				Game.gold += DIAMOND_GOLD
			Game.flags["cave_done:" + file] = true
			Game.save()
			if lava_rises:
				_start_lava()
		"s":
			Game.flags["sun_ore"] = int(Game.flags.get("sun_ore", 0)) + 1
	Game.changed.emit()


## The treasure woke the lava: it waits a moment, then rises from the floor (never above the exit).
func _start_lava() -> void:
	lava_top = level.height * TILE
	lava_wait = LAVA_WAIT
	var exits := level.find("E")
	lava_stop = (exits.map(func(e): return e.y).min() + 1) * TILE if not exits.is_empty() else 0.0


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
			juice.hit(m, m.hit(hero.position))
			Vitals.lumen_hit()
			bounced = true
		elif not m.reflected:
			juice.spark(m.position)
			m.reflected = true
			m.velocity = -m.velocity
			bounced = true
	for cell in cells_in(box):
		var ch := letter(cell)
		if ch == "L" and cell not in hero.attack_hits:
			hero.attack_hits.append(cell)
			pull_lever()
		elif ch in "B*s" and cell not in hero.attack_hits:
			hero.attack_hits.append(cell)
			_break(cell)
		elif ch in "^n" or (ch == "A" and trap_up()):
			bounced = true
	if down and bounced and hero.attack_hits.find("pogo") == -1:
		hero.attack_hits.append("pogo")
		juice.spark(Vector2(box.get_center().x, box.end.y))
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
		if letter(cell) in "B*s":
			_break(cell)
			return
		if letter(cell) == "L":
			pull_lever()
			return


## Dig (or strike) cracked rock, diamond ore or Sun Shard ore: the ore gives its treasure.
func _break(cell: Vector2i) -> void:
	var ch := letter(cell)
	if ch in "B*s":
		juice.chips(cell_rect(cell).get_center(), Color(CaveTiles.palette(level.theme())[1]))
	if ch == "B":
		set_letter(cell, ".")
	elif ch in "*s":
		_take(cell, ch)


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
	p.tex = art_tex
	p.region = Rect2(ArtSheet.region(art_sheet, "platform"))
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


func _tileset() -> TileSet:
	var letters := CaveTiles.SOLID + CaveTiles.LEDGE + LADDER_TOP
	var img := Image.create(TILE * maxi(letters.length(), 16), TILE * 3, false, Image.FORMAT_RGBA8)
	for i in letters.length():                      # row 0: one tile per letter
		var ch := letters[i]
		var at := Vector2i(i * TILE, 0)
		if ch == LADDER_TOP:
			continue                                  # invisible: the ladder is drawn over it
		img.blit_rect(CaveArt.tile_image(art_sheet, CaveArt.MAP_TILE.get(ch, "solid_15")), Rect2i(0, 0, TILE, TILE), at)
		if ch in "<>":                                # a one-way wall: the marker shows the side it opens from
			img.fill_rect(Rect2i(at + Vector2i(6 if ch == "<" else 18, 12), Vector2i(8, 8)), Color("f7c64a"))
	for bits in 16:                                 # rows 1 and 2: rock (#) and secret wall (F) edges
		var rock := CaveArt.tile_image(art_sheet, "solid_%d" % bits)
		img.blit_rect(rock, Rect2i(0, 0, TILE, TILE), Vector2i(bits * TILE, TILE))
		img.blit_rect(rock, Rect2i(0, 0, TILE, TILE), Vector2i(bits * TILE, 2 * TILE))
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)
	ts.add_physics_layer()
	ts.add_physics_layer()
	ts.set_physics_layer_collision_layer(1, LADDER_LAYER)
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
		if ch == LADDER_TOP:                          # its own physics layer: a climbing Hero passes it
			td.add_collision_polygon(1)
			td.set_collision_polygon_points(1, 0, PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, -h + 8), Vector2(-h, -h + 8)]))
			td.set_collision_polygon_one_way(1, 0, true)
			continue
		td.add_collision_polygon(0)
		if ch in CaveTiles.LEDGE:
			td.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, -h + 8), Vector2(-h, -h + 8)]))
			td.set_collision_polygon_one_way(0, 0, true)
		else:
			td.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)]))
	for bits in 16:
		src.create_tile(Vector2i(bits, 1))
		src.create_tile(Vector2i(bits, 2))              # F: looks like rock, no collision
		var td := src.get_tile_data(Vector2i(bits, 1), 0)
		td.add_collision_polygon(0)
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
			"A":
				_spr("spike_trap", p, 3 if trap_up() else 0)
			"J":
				_spr("flame_jet", p, 0)
				if jet_on():
					for k in range(1, JET_HEIGHT):
						_spr("flame", p - Vector2(0, k * TILE))
				elif about_to_go_off():
					overlay.draw_circle(p + Vector2(16 + randf_range(-3, 3), -4), 3.0, Color("ffb040"))
			"M":                                       # the vent's steam: a column while it puffs
				if geyser_puffing():
					for k in 6:
						var y := -((clock * 4 + k * 37) % int(GEYSER_HEIGHT * TILE))
						overlay.draw_circle(p + Vector2(16 + sin((clock + k * 20) * 0.2) * 5, y), 7.0 + k % 3 * 2, Color(0.9, 0.95, 1.0, 0.55))
				elif about_to_go_off():
					overlay.draw_circle(p + Vector2(16 + randf_range(-3, 3), -4), 4.0, Color(0.9, 0.95, 1.0, 0.5))
			"T":
				_spr("chest", p, 0)
			"L":
				_spr("lever", p, 0)
			"u":                                       # a used spring stands empty until it fills up
				if springs.has(cell):
					_spr("spring", p, 0, Color(0.5, 0.5, 0.6))
				else:
					_spr("spring", p)
			"C":
				if checkpoint == _cell_spot(cell):
					_spr("checkpoint_lit", p)
				else:
					_spr("checkpoint", p, 0)
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
			"P", "U", "R", "S", "z", "k", "c", "x", "=", "B", "G", "%", "I", "o", "<", ">", "n", "*", "s":
				pass
			_:
				if CaveArt.SPRITE.has(ch):
					_spr(CaveArt.SPRITE[ch], p)
					continue
				overlay.draw_rect(Rect2(p + Vector2(4, 4), Vector2(24, 24)), Color.MAGENTA)  # an unknown letter
	var ll := lost_light_spot()
	if ll.x < INF:                                   # your Lost Light: the gold you dropped
		overlay.draw_circle(ll, 10.0 + (clock / 10) % 2 * 2, Color(1.0, 0.85, 0.4, 0.35))
		overlay.draw_circle(ll, 5.0, Color("ffe08a"))
	if lava_top < INF:
		overlay.draw_rect(Rect2(Vector2(0, lava_top), Vector2(level.width * TILE, level.height * TILE - lava_top + 64)), Color(0.88, 0.27, 0.2, 0.9))


## One tile of the theme's sheet at p (frame -1: play it at the sheet's fps).
func _spr(anim: String, p: Vector2, frame := -1, tint := Color.WHITE) -> void:
	if frame < 0:
		frame = CaveArt.frame_at(art_sheet, anim, clock)
	overlay.draw_texture_rect_region(art_tex, Rect2(p, Vector2(TILE, TILE)), Rect2(ArtSheet.region(art_sheet, anim, frame)), tint)
