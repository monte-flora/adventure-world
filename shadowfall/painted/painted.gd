class_name PaintedScreen
extends Node2D
## P1 prototype (not the real map): Emberhold at dusk as ONE painted screen, to compare with the tiles.
##   godot --path shadowfall --audio-driver Dummy res://painted/painted.tscn
## The ground is the user's painting with the people painted out (tools/clean_plate.py); the hero and
## people walk on it. emberwick.json holds the hand-made collision shapes, the foreground pieces
## (canopies, roofs, cliff tops: cut from the painting, y-sorted with the characters), people and lights.
## G talks to the person in front. `-- --shot=<png> --at=x,y` saves a screenshot and quits.

const DATA := "res://painted/emberwick.json"
const DUSK := Color(0.62, 0.6, 0.78)        # stand-in for E1's CanvasModulate dusk
const TALK_REACH := 44.0
const FEET := 12.0                          # sprite feet sit this far below a node's position

var data: Dictionary
var rects: Array[Rect2] = []
var polys: Array[PackedVector2Array] = []
var hero: PaintedHero
var people: Array[Person] = []
var sorted: Node2D                          # hero, people and foreground pieces, y-sorted
var exit_rect: Rect2
var banner: Label
var box: Node
var talking := false


func _ready() -> void:
	data = JSON.parse_string(FileAccess.get_file_as_string(DATA))
	for r in data["solid_rects"]:
		rects.append(Rect2(r[0], r[1], r[2], r[3]))
	for p in data["solid_polys"]:
		polys.append(_poly(p))
	var e: Array = data["cave_exit"]
	exit_rect = Rect2(e[0], e[1], e[2], e[3])
	var ground := Sprite2D.new()
	ground.texture = load("res://painted/emberwick_clean.png")
	ground.centered = false
	add_child(ground)
	sorted = Node2D.new()
	sorted.y_sort_enabled = true
	add_child(sorted)
	var front: Texture2D = load("res://painted/emberwick_front.png")
	for piece in data["front"]:
		var pts := _poly(piece["poly"])
		var box_r := Rect2(pts[0], Vector2.ZERO)
		for q in pts:
			box_r = box_r.expand(q)
		var s := Sprite2D.new()
		s.name = piece["name"]
		s.texture = front
		s.centered = false
		s.region_enabled = true
		s.region_rect = box_r
		s.position = Vector2(box_r.position.x, piece["base"])        # sorts by its base
		s.offset = Vector2(0, box_r.position.y - float(piece["base"]))
		sorted.add_child(s)
	hero = PaintedHero.new()
	hero.world = WorldMap.new()             # HeroTop needs one; the painted collision replaces it
	hero.scene = self
	var at: Array = data["hero"]
	hero.position = Vector2(at[0], at[1]) - Vector2(0, FEET)
	var opts := Paths.cmdline()
	if opts.has("at"):
		var xy: PackedStringArray = str(opts["at"]).split(",")
		hero.position = Vector2(float(xy[0]), float(xy[1])) - Vector2(0, FEET)
	sorted.add_child(hero)
	_spawn_people()
	_add_lights()
	var cam := Camera2D.new()               # the map's camera; one screen, so it stays put
	cam.process_callback = Camera2D.CAMERA2D_PROCESS_PHYSICS
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 8.0
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = 960
	cam.limit_bottom = 540
	cam.position = hero.position
	hero.add_child(cam)
	var ui := CanvasLayer.new()
	ui.layer = GloomLight.HUD_LAYER
	banner = Label.new()
	banner.size = Vector2(960, 40)
	banner.position = Vector2(0, 40)
	banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner.add_theme_font_override("font", UiStyle.font("body"))
	banner.add_theme_font_size_override("font_size", UiStyle.BODY * 3)
	banner.add_theme_color_override("font_color", UiStyle.LIGHT1)
	banner.add_theme_color_override("font_outline_color", UiStyle.INK0)
	banner.add_theme_constant_override("outline_size", 6)
	banner.text = Names.HOME
	ui.add_child(banner)
	add_child(ui)
	box = preload("res://ui/dialogue_box.tscn").instantiate()
	add_child(box)
	if opts.has("shot"):
		_shot(str(opts["shot"]))


func _poly(flat: Array) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in range(0, flat.size(), 2):
		out.append(Vector2(flat[i], flat[i + 1]))
	return out


## Does this box (screen px) touch a house, fence, tree, rock or cliff?
func blocked(r: Rect2) -> bool:
	for s in rects:
		if s.intersects(r):
			return true
	var box_pts := PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end,
		Vector2(r.position.x, r.end.y)])
	for p in polys:
		if not Geometry2D.intersect_polygons(box_pts, p).is_empty():
			return true
	return false


func _spawn_people() -> void:
	var by_id := {}
	for d in RulesData.get_file("people").get("people", []):
		by_id[d.get("id", "")] = d
	for spot in data["people"]:
		var d: Dictionary = by_id.get(spot["id"], {}).duplicate()
		if d.is_empty():
			continue
		d["move"] = "idle"                  # they stand where the painting had them
		var p := Person.new()
		p.setup(d, Vector2i.ZERO, hero.world)
		p.position = Vector2(spot["at"][0], spot["at"][1]) - Vector2(0, FEET)
		p.hero = hero
		people.append(p)
		sorted.add_child(p)
		rects.append(Rect2(p.position - Vector2(9, 6), Vector2(18, 14)))    # can't walk through people


func _add_lights() -> void:
	var dusk := CanvasModulate.new()
	dusk.color = DUSK
	add_child(dusk)
	var tex := GradientTexture2D.new()
	tex.width = 256
	tex.height = 256
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	tex.gradient = g
	for l in data["lights"]:
		_light(tex, Vector2(l["at"][0], l["at"][1]), Color(l["color"]), l["energy"], l["scale"], self)
	_light(tex, Vector2(0, FEET - 4), Color("ffd890"), 1.2, 1.1, hero)        # the hero's lantern


func _light(tex: Texture2D, at: Vector2, c: Color, energy: float, scale_: float, parent: Node) -> void:
	var l := PointLight2D.new()
	l.set_script(preload("res://painted/flicker.gd"))
	l.texture = tex
	l.position = at
	l.color = c
	l.base_energy = energy
	l.base_scale = scale_
	l.energy = energy
	l.texture_scale = scale_
	l.blend_mode = Light2D.BLEND_MODE_ADD
	parent.add_child(l)


func _physics_process(_dt: float) -> void:
	if exit_rect.has_point(hero.position + Vector2(0, FEET)):
		banner.text = "The Mine below " + Names.HOME
	elif banner.text != Names.HOME and not exit_rect.grow(24).has_point(hero.position + Vector2(0, FEET)):
		banner.text = Names.HOME


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed("interact") or talking:
		return
	var p := person_in_front()
	if p != null:
		get_viewport().set_input_as_handled()
		talk(p)


func person_in_front() -> Person:
	var best: Person = null
	for p in people:
		var d := p.position - hero.position
		if d.length() <= TALK_REACH and d.normalized().dot(hero.facing) > 0.3 \
				and (best == null or d.length() < (best.position - hero.position).length()):
			best = p
	return best


func talk(p: Person) -> void:
	talking = true
	hero.velocity = Vector2.ZERO
	hero.set_physics_process(false)
	p.face(hero.position)
	await box.talk(Conversation.new(p.id))  # shop and forge don't open in the prototype
	hero.set_physics_process(true)
	talking = false


func _shot(path: String) -> void:
	for i in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path)
	get_tree().quit()
