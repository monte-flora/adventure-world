extends Node2D
## The overworld (top-down). B1 owns this folder.
##   Scenes.goto("overworld")                              the realm, at home
##   Scenes.goto("overworld", {"at": Vector2i(c, r)})       back from a cave: next to that Mine
##   Scenes.goto("overworld", {"realm": "nightfall"})       the Umbral Reach (Nightfall's mirror)
## Walk onto a Mine to play its cave; onto a waystone (L) to light it (heal, respawn point); G on a lit
## waystone travels to the next lit one. Ability gates (Y ivy cliff, O rubble, K shadow thorns, water,
## gate: lines) stay shut until Game.has_ability(). Tiles: art/sheets/realm_<land> (RealmTiles).
## People (rules/data/people.json, Person) stand in the light realm's lands: face one and press G
## (interact) to talk; the talk runs in ui/dialogue_box (music ducked), then may open the shop or forge.

const TILE := LevelFile.TILE
const MONSTERS_PER_LAND := 3
var world: WorldMap
var realm := "light"
var map: TileMapLayer                         # the ground: grass, path, water
var objects: TileMapLayer                     # trees, rocks, houses, Mines, waystones, gates
var tiles: RealmTiles
var canopy: TileMapLayer                      # tree crowns, drawn over the hero
var ground: RealmGround                       # painted ground over the tiles (lands with `ground: painted`)
var prop_sprites: Array[Sprite2D] = []        # realm/props/ art from `prop:` lines (RealmProps)
var entities: Node2D                          # y-sorted: objects, hero, people, monsters
var dusk: RealmLight                          # CanvasModulate tint + warm PointLight2Ds
var gates_layer: Node2D
var hero: HeroTop
var cam: Camera2D
var banner: Label
var monsters: Array[MapMonster] = []
var respawn := Vector2i.ZERO
var last_cell := Vector2i(-1, -1)
var people: Array[Person] = []
var box: CanvasLayer                          # ui/dialogue_box.tscn
var talking := false
var screen: CanvasLayer                       # the shop or forge, while open (ui/)
const TALK_REACH := 1.4 * TILE                # px from the hero to a person you face
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
	var opts := Paths.cmdline()
	if opts.has("shot"):                      # -- --scene=overworld --shot=out.png [--cell=col,row] [--gloom=0..3]
		if opts.has("gloom"):
			Game.gloom = float(opts["gloom"]) / 3.0
		_shot(opts["shot"], opts.get("cell", ""))


## Saves a screenshot (a silent window, not headless) and quits: for checking the art.
func _shot(path: String, cell: String) -> void:
	var c := cell.split(",")
	if c.size() == 2:
		hero.place(Vector2i(int(c[0]), int(c[1])))
		cam.position = hero.position
		cam.reset_smoothing()
	for i in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path)
	get_tree().quit()


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
	if realm == "light":
		ground = RealmGround.new(w)
		if ground.build():
			add_child(ground)
		else:
			ground = null
	gates_layer = Node2D.new()
	gates_layer.draw.connect(_draw_marks)
	add_child(gates_layer)
	entities = Node2D.new()
	entities.name = "Entities"
	entities.y_sort_enabled = true            # whoever stands lower draws in front
	objects.y_sort_enabled = true
	entities.add_child(objects)
	add_child(entities)
	prop_sprites = RealmProps.build(w, entities, canopy)
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
	entities.add_child(hero)
	_spawn_monsters()
	_spawn_people()
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
	RealmProps.shade(prop_sprites, light.painted_material)
	if ground:
		light.track(ground.material)
	light.follow(hero)
	light.tinted = true
	dusk = RealmLight.new()
	add_child(dusk)
	_add_glows()
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
	box = preload("res://ui/dialogue_box.tscn").instantiate()
	add_child(box)
	_arrive(hero.cell(), true)


func _physics_process(_dt: float) -> void:
	if hero == null:
		return
	cam.offset = shake.step(_dt)
	if stop > 0:
		stop -= 1
		if stop == 0 and not talking:
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
	if not event.is_action_pressed("interact") or talking:
		return
	var p := person_in_front()
	if p != null:
		get_viewport().set_input_as_handled()
		talk(p)
	elif world.at(hero.cell()) == "L":
		travel_from(hero.cell())


## The nearest person the hero is facing and close to, or null.
func person_in_front() -> Person:
	var best: Person = null
	for p in people:
		var d := p.position - hero.position
		if p.visible and d.length() <= TALK_REACH and d.normalized().dot(hero.facing) > 0.3 \
				and (best == null or d.length() < (best.position - hero.position).length()):
			best = p
	return best


## A whole talk with p: everyone stands still, the music dips; then the shop or forge if it says so.
## Returns what the talk opened ("shop", "forge" or "").
func talk(p: Person) -> String:
	talking = true
	hero.velocity = Vector2.ZERO
	_freeze(true)
	p.face(hero.position)
	Audio.duck(true)
	var then: String = await box.talk(Conversation.new(p.id))
	if then == "shop" or then == "forge":
		screen = ShopScreen.new() if then == "shop" else ForgeScreen.new()
		if then == "shop":
			screen.trader = p.id
		add_child(screen)
		await screen.closed
		screen = null
	Audio.duck(false)
	_freeze(false)
	talking = false
	_show_people()
	return then


func _spawn_people() -> void:
	if realm != "light":
		return
	var taken := {}
	for d in RulesData.get_file("people").get("people", []):
		var at := person_cell(d, taken)
		if at.x < 0:
			push_warning("overworld: no place for %s" % d.get("id"))
			continue
		taken[at] = true
		var p := Person.new()
		p.setup(d, at, world)
		p.hero = hero
		people.append(p)
		entities.add_child(p)
	_show_people()


## Where a person stands: their land's top-left plus their row and column, or the nearest open square.
func person_cell(d: Dictionary, taken := {}) -> Vector2i:
	var pl: Dictionary = d.get("place", {})
	var id := str(pl.get("land", ""))
	for key in [id, WorldMap.realm_id(id), WorldMap.names_id(id)]:
		if world.lands.has(key):
			var want: Vector2i = world.lands[key].rect.position + Vector2i(int(pl.get("col", 0)), int(pl.get("row", 0)))
			for r in 5:
				for dy in range(-r, r + 1):
					for dx in range(-r, r + 1):
						var q := want + Vector2i(dx, dy)
						if maxi(absi(dx), absi(dy)) == r and _can_stand(q) and not taken.has(q):
							return q
	return Vector2i(-1, -1)


func _can_stand(q: Vector2i) -> bool:
	return world.walkable(q) and world.at(q) not in "MSPLHY" and not world.gates.has(q)


func _show_people() -> void:
	for p in people:
		p.visible = Conversation.visible(p.id)


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
			var killed: bool = m.hit(Forge.sword_damage(), at)
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
	for p in people:
		p.set_physics_process(not on)
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
			entities.add_child(m)


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


## Warm lights: the hero's lantern and each person's (unless E2's rig already gave them one), the
## houses' windows and every lit waystone.
func _add_glows() -> void:
	if not RealmLight.has_light(hero):
		RealmLight.glow(hero, Vector2(6, 4), RealmLight.LANTERN, 1.1)
	for p in people:
		if not RealmLight.has_light(p):
			RealmLight.glow(p, Vector2(0, 2), RealmLight.PERSON, 0.8)
	for c in world.cells:
		if world.cells[c] == "H" and not world.prop_cover.has(c):
			RealmLight.glow(objects, objects.map_to_local(c), RealmLight.WINDOW, 0.7)
	_waystone_glows()


var _waystone_lights := {}


func _waystone_glows() -> void:
	for p in world.waystones:
		if waystone_lit(p) and not _waystone_lights.has(p):
			_waystone_lights[p] = RealmLight.glow(objects, objects.map_to_local(p) + Vector2(0, -8), 90.0, 1.0)


func _on_game_changed() -> void:
	_waystone_glows()
	tiles.refresh(objects, waystone_lit)
	_show_people()
	gates_layer.queue_redraw()
