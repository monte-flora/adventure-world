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
