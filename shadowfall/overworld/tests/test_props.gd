extends TestCase
## G1: props from `prop:` lines (footprints block, y-sort, lights) and the painted ground (no seams).

const TILE := LevelFile.TILE


func _prop_world(props: String) -> WorldMap:
	var w := WorldMap.new()
	w.stitch({"realm/1_t.txt": "at: 0 0\nhome: 1 0\n%s\nGGGGGGGG\nHGGGGGGG\nGGGGGGGG" % props})
	return w


func test_prop_lines_load() -> void:
	var w := _prop_world("prop: rocks 1 4\nprop: flowers 0 2\nprop: no_such_thing 2 2\nprop: rocks one 2")
	check_eq(w.props.size(), 2, "two good props")
	check_eq(w.props[0].at, Vector2(4.5, 1.5) * TILE, "anchor on the square's middle")
	check(w.errors.size() == 2, "bad lines are reported: %s" % [w.errors])
	check(not w.walkable(Vector2i(4, 1)), "the rocks' square is blocked")
	check(w.walkable(Vector2i(2, 0)), "flowers have no footprint: walk through")
	var h := _prop_world("prop: cottage_a 0.5 0")
	check(h.walkable(Vector2i(0, 1)), "a prop never blocks a house (H) square")


func test_a_prop_blocks_the_hero_by_its_footprint() -> void:
	Scenes.goto("overworld")
	await physics_frames(2)
	var ow = Scenes.screen
	for m in ow.monsters:
		m.queue_free()
	ow.monsters.clear()
	var w := _prop_world("prop: rocks 1 4")
	ow.world = w
	ow.hero.world = w
	ow.hero.place(Vector2i(1, 1))
	ow.hero.drive = Vector2.RIGHT
	await physics_frames(60)
	var foot: Rect2 = w.prop_solid[0]
	check(ow.hero.position.x + HeroTop.HALF.x <= foot.position.x + 0.5,
		"stops at the rocks' footprint (hero right %.1f, rocks left %.1f)" % [ow.hero.position.x + HeroTop.HALF.x, foot.position.x])
	check(ow.hero.position.x > foot.position.x - HeroTop.HALF.x - 8.0, "right up against it (%.1f)" % ow.hero.position.x)
	var open := _prop_world("prop: flowers 1 4")
	ow.world = open
	ow.hero.world = open
	ow.hero.place(Vector2i(1, 1))
	await physics_frames(60)
	check(ow.hero.position.x > 5 * TILE, "walks through flowers (x %.0f)" % ow.hero.position.x)


func test_y_sort_puts_the_hero_behind_a_canopy() -> void:
	Scenes.goto("overworld")
	await physics_frames(2)
	var ow = Scenes.screen
	var oak: Sprite2D = null
	for s in ow.prop_sprites:
		if s.get_meta("prop") == "oak":
			oak = s
			break
	check(oak != null, "Emberhold has oaks")
	if oak == null:
		return
	check(oak.get_parent() == ow.entities and ow.entities.y_sort_enabled, "props sort with the hero")
	var art := Rect2(oak.position + oak.offset, oak.texture.get_size())
	ow.hero.position = Vector2(oak.position.x, art.position.y + art.size.y * 0.4)   # in the crown
	check(art.has_point(ow.hero.position), "the hero stands under the crown")
	check(ow.hero.position.y < oak.position.y, "north of the trunk: drawn first, so behind the canopy")
	ow.hero.position = oak.position + Vector2(0, 12)
	check(ow.hero.position.y > oak.position.y, "south of the trunk: in front")
	var lamp_lit := false
	for s in ow.prop_sprites:
		if s.get_meta("prop") == "lamppost" and RealmLight.has_light(s):
			lamp_lit = true
	check(lamp_lit, "lampposts carry a flickering light")


func test_painted_ground_has_no_seam_between_screens() -> void:
	var w := WorldMap.load_realm()
	var g := RealmGround.new(w)
	check(g.build(), "Emberhold asks for the painted ground and the grass texture exists")
	var em: Rect2i = w.lands["emberhold"].rect
	var edge_x := WorldMap.SCREEN.x * TILE                 # A3 | B3, inside Emberhold
	var top := (em.position.y + 18) * TILE
	var across := 0.0
	var inside := 0.0
	for y in range(top, top + 8 * TILE, 3):
		var a := g.color_at(Vector2(edge_x - 1, y))
		var b := g.color_at(Vector2(edge_x, y))
		var c := g.color_at(Vector2(edge_x - 41, y))
		var d := g.color_at(Vector2(edge_x - 40, y))
		check(a.a > 0.99 and b.a > 0.99, "painted on both sides of the screen edge (%d)" % y)
		across += _diff(a, b)
		inside += _diff(c, d)
	check(across <= inside * 1.5 + 0.5, "the screen edge is no harsher than inside (%.2f vs %.2f)" % [across, inside])
	var sea := g.color_at(Vector2(150, 150) * TILE)
	check(sea.a == 0.0, "other lands stay on today's tiles")
	g.free()


func _diff(a: Color, b: Color) -> float:
	return absf(a.r - b.r) + absf(a.g - b.g) + absf(a.b - b.b)


func test_painted_props_and_ground_follow_the_gloom() -> void:
	Game.gloom = 0.0
	Scenes.goto("overworld")
	await physics_frames(2)
	var ow = Scenes.screen
	var lamp: Sprite2D = null
	for s in ow.prop_sprites:
		if s.get_meta("prop") == "lamppost":
			lamp = s
	check(lamp != null, "Emberhold has a lamppost")
	if lamp == null:
		return
	var mat: ShaderMaterial = lamp.material
	check(mat != null and mat.shader.resource_path == "res://light/painted_gloom.gdshader", "props get the painted grade")
	check_eq(mat.get_shader_parameter("stage"), 0, "stage 0 to start")
	Game.gloom = 1.0
	await frames(2)
	check_eq(mat.get_shader_parameter("stage"), 3, "the props' stage follows the gloom")
	check_eq(ow.ground.material.get_shader_parameter("stage"), 3, "and the painted ground's")
	var img := lamp.texture.get_image()
	img.decompress()
	var c := Color(0, 0, 0, 0)
	for y in img.get_height():                       # the lamppost's most opaque, brightest pixel
		for x in img.get_width():
			var p := img.get_pixel(x, y)
			if p.a > 0.9 and p.v > c.v:
				c = p
	var dark := PaintedGloom.grade(c, 3)
	check(PaintedGloom.grade(c, 0) == c, "stage 0 leaves the art as painted")
	check(dark.v < c.v * 0.6, "stage 3 darker (%.2f -> %.2f)" % [c.v, dark.v])
	check(dark.s <= c.s * 0.6 + 0.01, "and greyer (%.2f -> %.2f)" % [c.s, dark.s])
	check(dark.b >= dark.g, "and shifted toward violet: %s" % dark)
	var px := Vector2(ow.world.lands["emberhold"].rect.position + Vector2i(10, 18)) * TILE
	var g0: Color = ow.ground.color_at(px, 0)
	var g3: Color = ow.ground.color_at(px, 3)
	check(g0.a > 0.99 and g3.v < g0.v * 0.6 and g3.s < g0.s, "the ground darkens and greys too (%s -> %s)" % [g0, g3])
	Game.gloom = 0.0


func test_each_lit_prop_has_its_lights_and_the_hero_stays_brightest() -> void:
	Scenes.goto("overworld")
	await physics_frames(2)
	var ow = Scenes.screen
	var hero_l: LanternLight = ow.hero.light
	var seen := {}
	var count := {}
	for p in ow.world.props:
		count[p.name] = p.meta.get("lights", []).size()
	for s in ow.prop_sprites:
		var want: int = count[s.get_meta("prop")]
		var lights: Array = s.get_children().filter(func(n): return n is LanternLight)
		check_eq(lights.size(), want, "%s: one light per .json light" % s.get_meta("prop"))
		for l: LanternLight in lights:
			seen[s.get_meta("prop")] = true
			check(l.base_energy < hero_l.base_energy and l.radius < hero_l.radius,
				"%s's light (%.2f, %.0f px) is under the hero's lantern" % [s.get_meta("prop"), l.base_energy, l.radius])
	for k in ["cottage_a", "lamppost", "campfire"]:
		check(seen.has(k), "Emberhold's %s is lit" % k)
	var fire := RealmProps.light(self, "campfire", Vector2.ZERO, 110.0)
	var window := RealmProps.light(self, "cottage_a", Vector2.ZERO, 44.0)
	check((fire.get_child(0) as Flicker).amount > (window.get_child(0) as Flicker).amount, "fire flickers more than a window")
	check(fire.base_energy > window.base_energy, "and burns stronger")
	fire.free()
	window.free()


func test_painted_lands_draw_crags_gates_and_water_without_changing_collision() -> void:
	var w := WorldMap.new()
	w.stitch({"realm/1_t.txt": "at: 0 0\nhome: 1 1\nground: painted\ncrags: rocks\ngate: Riven Gap 0 5 dash\n"
		+ "XXXXXXXX\nXHGGGGYX\nXGFFGGOX\nXGWWWWKX\nXGWWWWWX\nXXXXXXXX"})
	var before := {}
	for p in w.cells:
		before[p] = w.walkable(p)
	var root := Node2D.new()
	var d := RealmProps.scatter(w, root)
	for p in w.cells:
		check_eq(w.walkable(p), before[p], "square %s walks as its letter says" % p)
	check(w.prop_cells.is_empty() and w.prop_solid.is_empty(), "decor adds no footprints")
	for c in [Vector2i(6, 1), Vector2i(6, 2), Vector2i(6, 3), Vector2i(5, 0)]:
		check(d.gates.has(c) and d.gates[c].visible, "gate %s has its prop, shown while shut" % c)
	check_eq(d.gates[Vector2i(6, 1)].get_meta("prop"), "ivy_cliff", "Y is an ivy cliff")
	check_eq(d.gates[Vector2i(5, 0)].get_meta("prop"), RealmProps.GATE_ROCK, "a gate: rock is a boulder")
	var crags := 0
	for s: Sprite2D in d.sprites:
		if s.get_meta("prop") == "rocks":
			crags += 1
	check(crags >= 10, "the walls get the land's crags (%d)" % crags)
	Game.take_stone("leaf")
	RealmProps.refresh_gates(w, d.gates)
	check(not d.gates[Vector2i(6, 1)].visible, "the ivy cliff goes once you can climb")
	var g := RealmGround.new(w)
	check_eq(g.role_at(Vector2i(3, 4)), "deep_water", "water away from the shore is deep")
	check_eq(g.role_at(Vector2i(2, 3)), "shallow_water", "water by the land is the shore")
	check_eq(g.role_at(Vector2i(0, 0)), "cliff", "a wall is cliff")
	check_eq(g.role_at(Vector2i(5, 0)), "rocky_ground", "under the boulder: rocky ground")
	check_eq(g.role_at(Vector2i(2, 2)), "forest_floor", "under the trees: forest floor")
	check(g.build(), "builds")
	var water_first: int = g.material.get_shader_parameter("water_first")
	check(g.have[g.material_at(Vector2i(3, 4))] >= water_first and g.have[g.material_at(Vector2i(1, 2))] < water_first,
		"only the water ripples")
	g.free()
	root.free()


func test_a_land_paints_a_role_with_its_own_texture() -> void:
	var w := WorldMap.new()
	w.stitch({"realm/1_t.txt": "at: 0 0\nground: painted\npaint: grass mud\npaint: cliff no_such_texture\nXGG\nGGG"})
	var g := RealmGround.new(w)
	check_eq(g.material_at(Vector2i(1, 0)), "mud", "paint: grass mud")
	check_eq(g.material_at(Vector2i(0, 0)), "cliff", "a missing texture falls back to the shared one")
	g.free()
