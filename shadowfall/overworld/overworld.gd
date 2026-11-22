extends Node2D
## The overworld (top-down). B1 owns this folder.
##   Scenes.goto("overworld")                              the realm, at home
##   Scenes.goto("overworld", {"at": Vector2i(c, r)})       back from a cave: next to that Mine
##   Scenes.goto("overworld", {"realm": "nightfall"})       the Umbral Reach (Nightfall's mirror)
## Walk onto a Mine to play its cave; onto a waystone (L) to light it (heal, respawn point); G on a lit
## waystone travels to the next lit one. Ability gates (Y ivy cliff, O rubble, K shadow thorns, water,
## gate: lines) stay shut until Game.has_ability(). Tiles: art/sheets/realm_<land> (RealmTiles).

const TILE := LevelFile.TILE
const MONSTERS_PER_LAND := 3
var world: WorldMap
var realm := "light"
var map: TileMapLayer                         # the ground: grass, path, water
var objects: TileMapLayer                     # trees, rocks, houses, Mines, waystones, gates
var tiles: RealmTiles
var canopy: TileMapLayer                      # tree crowns, drawn over the hero
var gates_layer: Node2D
var hero: HeroTop
var cam: Camera2D
var banner: Label
var monsters: Array[MapMonster] = []
var respawn := Vector2i.ZERO
var last_cell := Vector2i(-1, -1)
var heal := LumenHeal.new()                   # Q, standing still: a Lumen charge becomes a heart
## Game feel (docs/teen/gameplay §4): hit-stop freezes hero and monsters for a few frames.
const STOP_HIT := 3
const STOP_KILL := 6
const STOP_HURT := 10
const LOOK_AHEAD := 0.12                      # s of the hero's speed the camera leads by
const LOOK_MAX := 40.0                        # px
var stop := 0                                 # hit-stop frames left
var shake := Juice.Shake.new()
var hurt_edge: TextureRect                    # red at the screen's edges when you are hit


func _ready() -> void:
	realm = Scenes.args.get("realm", "light")
	build(WorldMap.load_nightfall() if realm == "nightfall" else WorldMap.load_realm())


func build(w: WorldMap) -> void:
	world = w
	for e in w.errors:
		push_warning("overworld: " + e)
	map = TileMapLayer.new()
	objects = TileMapLayer.new()
	canopy = TileMapLayer.new()
	tiles = RealmTiles.new(w)
	tiles.paint(map, objects, canopy)
	add_child(map)
	add_child(objects)
	gates_layer = Node2D.new()
	gates_layer.draw.connect(_draw_marks)
	add_child(gates_layer)
	Game.changed.connect(_on_game_changed)
	tiles.refresh(objects, waystone_lit)
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
	add_child(canopy)
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
	var light := GloomLight.new()
	add_child(light)
	map.material = light.world_material
	objects.material = light.world_material
	canopy.material = light.world_material
	light.follow(hero)
	add_child(preload("res://ui/hud.tscn").instantiate())
	var ui := CanvasLayer.new()
	ui.layer = GloomLight.HUD_LAYER
	banner = Label.new()
	banner.position = Vector2(0, 20)          # top middle: the HUD has the corners
	banner.size.x = 960
	banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner.add_theme_font_override("font", UiStyle.font("body"))
	banner.add_theme_font_size_override("font_size", UiStyle.BODY * 3)
	banner.add_theme_color_override("font_color", UiStyle.LIGHT1)
	banner.add_theme_color_override("font_outline_color", UiStyle.INK0)
	banner.add_theme_constant_override("outline_size", 6)
	banner.position.y = 56
	ui.add_child(banner)
	hurt_edge = _hurt_edge()
	ui.add_child(hurt_edge)
	add_child(ui)
	_arrive(hero.cell(), true)


func _physics_process(_dt: float) -> void:
	if hero == null:
		return
	cam.offset = shake.step(_dt)
	if stop > 0:
		stop -= 1
		if stop == 0:
			_freeze(false)
	cam.position = hero.position + (hero.velocity * LOOK_AHEAD).limit_length(LOOK_MAX)
	heal.step(Input.is_action_pressed("heal"), hero.velocity.length() < 1.0)
	var c := hero.cell()
	if c != last_cell:
		last_cell = c
		_arrive(c)


## The hero just stepped onto square c (or starts there: then a Portal or Mine underfoot waits for a step).
func _arrive(c: Vector2i, starting := false) -> void:
	if c == lost_light_cell():
		Vitals.recover_lost_light()
	var id := world.land(c)
	if id != "" and not Game.flags.get("seen_land_" + id, false):
		Game.flags["seen_land_" + id] = true
		show_banner(world.land_name(id))
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


## A land's name across the top the first time you enter it: fades in, holds, fades out.
func show_banner(text: String) -> void:
	banner.text = text.to_upper()
	banner.modulate.a = 0.0
	var t := banner.create_tween()
	t.tween_property(banner, "modulate:a", 1.0, 0.6)
	t.tween_interval(2.2)
	t.tween_property(banner, "modulate:a", 0.0, 0.8)
	t.tween_callback(func(): banner.text = "")


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


## Where this realm's Lost Light waits, or (-1, -1).
func lost_light_cell() -> Vector2i:
	var w: Dictionary = Vitals.lost_light().get("where", {})
	if w.get("scene", "") != "overworld" or w.get("realm", "") != realm:
		return Vector2i(-1, -1)
	return Vector2i(w.x, w.y)


func _on_hurt(hearts_left: int) -> void:
	heal.hit()
	hit_stop(STOP_HURT)
	shake.add(5, 12)
	hurt_edge.modulate.a = 1.0
	hurt_edge.create_tween().tween_property(hurt_edge, "modulate:a", 0.0, 0.4)
	if hearts_left <= 0:                      # no lives: the gold stays as a Lost Light; wake at the last lantern
		var c := hero.cell()
		Vitals.die({"scene": "overworld", "realm": realm, "x": c.x, "y": c.y})
		hero.place(respawn)
		hero.iframes = HeroTop.HURT_IFRAMES
		last_cell = respawn
		Game.changed.emit()


func _on_swing(at: Vector2, _facing: Vector2) -> void:
	for m in monsters.duplicate():
		if is_instance_valid(m) and hero.sword_hits(m.position):
			var fresh: bool = m.flash <= 0
			var killed: bool = m.hit(2, at)
			if fresh:
				Vitals.lumen_hit()
				_hit_fx(m, killed)


## A sword hit lands: sparks, a short stop and a tap of shake; a kill stops longer, shakes harder,
## plays the monster's poof and lets its light out as motes.
func _hit_fx(m: MapMonster, killed: bool) -> void:
	if not killed:
		hit_stop(STOP_HIT)
		shake.add(1, 4)
		Juice.burst(self, m.position, Color("fff2a8"), 6, 90.0, 0.2)
		return
	hit_stop(STOP_KILL)
	shake.add(2, 6)
	var poof := AnimatedSprite2D.new()
	poof.sprite_frames = m.sprite.sprite_frames
	poof.offset = m.sprite.offset
	poof.position = m.position + m.sprite.position
	poof.animation_finished.connect(poof.queue_free)
	add_child(poof)
	poof.play("poof")
	Juice.burst(self, m.position, Color("f7c64a"), 16, 70.0, 0.9, 2.0, -40.0)


## Freeze the hero and the monsters for `frames` physics frames (a longer stop is never cut short).
func hit_stop(frames: int) -> void:
	if frames > stop:
		stop = frames
		_freeze(true)


func _freeze(on: bool) -> void:
	hero.set_physics_process(not on)
	for m in monsters:
		if is_instance_valid(m):
			m.set_physics_process(not on)
			m.sprite.speed_scale = 0.0 if on else 1.0


func _hurt_edge() -> TextureRect:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 1.0])
	g.colors = PackedColorArray([Color(0.76, 0.23, 0.23, 0.0), Color(0.76, 0.23, 0.23, 0.7)])
	var tex := GradientTexture2D.new()
	tex.gradient = g
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.1, 0.5)
	var r := TextureRect.new()
	r.texture = tex
	r.set_anchors_preset(Control.PRESET_FULL_RECT)
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.modulate.a = 0.0
	return r


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
			var kind := MapMonster.kind_for("umbral_reach" if realm == "nightfall" else id, i)
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
	var ll := lost_light_cell()
	if ll.x >= 0:                             # your Lost Light: the gold you dropped
		var at := Vector2(ll) * TILE + Vector2.ONE * TILE / 2.0
		gates_layer.draw_circle(at, 12, Color(1.0, 0.85, 0.4, 0.35))
		gates_layer.draw_circle(at, 5, Color("ffe08a"))
	for p in world.waystones:                 # a lit lantern's warm pool
		if waystone_lit(p):
			gates_layer.draw_circle(Vector2(p) * TILE + Vector2.ONE * TILE / 2.0, 30, Color(1.0, 0.8, 0.4, 0.15))


func _on_game_changed() -> void:
	tiles.refresh(objects, waystone_lit)
	gates_layer.queue_redraw()
