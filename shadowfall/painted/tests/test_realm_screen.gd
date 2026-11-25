extends TestCase
## One realm screen as one painting (`painted_screen: B3`, PaintedRealmScreen): only that screen
## changes, collision never does. Uses a made-up painting in user://, not levels/polish/.

const B3 := Vector2i(1, 2)
const RED := Color(1, 0, 0)


func _fake_painting(folder := "realm_B3") -> String:
	var root := ProjectSettings.globalize_path("user://realm_screen_test")
	DirAccess.make_dir_recursive_absolute(root.path_join(folder))
	var img := Image.create(480, 272, false, Image.FORMAT_RGB8)    # half size: it is stretched to 960 × 544
	img.fill(RED)
	img.save_png(root.path_join(folder).path_join("painted.png"))
	return root


func _realm(without_line := false) -> WorldMap:
	var texts := {}
	for f in Paths.level_files(WorldMap.land_folder()):
		var text := FileAccess.get_file_as_string(Paths.level(f))
		if LevelFile.from_text(text).setting("world") == "":
			texts[f] = text.replace("painted_screen: B3\n", "") if without_line else text
	var w := WorldMap.new()
	w.stitch(texts)
	return w


func test_the_line_names_a_screen() -> void:
	var w := WorldMap.new()
	w.stitch({"realm/1_t.txt": "at: 0 0\nhome: 0 0\npainted_screen: B3 a1\npainted_screen: Z9\nGG"})
	check_eq(w.painted_screens, {B3: "realm_B3", Vector2i(0, 0): "realm_A1"}, "B3 and A1")
	check_eq(w.errors.size(), 1, "Z9 is reported")
	check_eq(WorldMap.screen_name(B3), "B3", "and back")
	check_eq(_realm().painted_screens, {B3: "realm_B3"}, "Emberhold opts in Emberwick's screen")


func test_collision_is_the_level_files() -> void:
	var with := _realm()
	var without := _realm(true)
	check_eq(with.cells, without.cells, "same letters")
	check_eq(with.prop_cells, without.prop_cells, "same blocked prop squares")
	check_eq(with.prop_solid, without.prop_solid, "same footprints")


func test_no_painting_changes_nothing() -> void:
	CaveArt.polish_root = ProjectSettings.globalize_path("user://realm_screen_none")
	var w := _realm()
	var ps := PaintedRealmScreen.new(w)
	var holder := Node2D.new()
	var sprites := RealmProps.build(w, holder)
	check(ps.backgrounds.is_empty(), "no background")
	check_eq(ps.apply(sprites, {}, null), 0, "no sprite re-skinned")
	CaveArt.polish_root = ""
	ps.free()
	holder.free()


func test_the_painting_and_its_cut_outs_only_on_that_screen() -> void:
	CaveArt.polish_root = _fake_painting()
	var w := _realm()
	var ps := PaintedRealmScreen.new(w)
	CaveArt.polish_root = ""
	check_eq(ps.backgrounds.size(), 1, "one painting")
	var bg := ps.backgrounds[0]
	check_eq(bg.position, Vector2(960, 1088), "at B3's top-left")
	check_eq(bg.texture.get_size(), Vector2(960, 544), "stretched to the screen, 1 px = 1 game px")
	var holder := Node2D.new()
	var sprites := RealmProps.build(w, holder)
	var decor := RealmProps.scatter(w, holder)
	var before := {}
	var kids := {}
	for s: Sprite2D in sprites + decor.sprites:
		before[s] = s.texture
		kids[s] = s.get_child_count()
	var tiles := RealmTiles.new(w)
	var map := TileMapLayer.new()
	var objects := TileMapLayer.new()
	tiles.paint(map, objects)
	var n := ps.apply(sprites + decor.sprites, decor.gates, objects)
	check(n > 20, "Emberwick's props re-skinned (%d)" % n)
	var screen := Rect2(Vector2(960, 1088), Vector2(960, 544))
	var inside := 0
	for s: Sprite2D in sprites + decor.sprites:
		var art := Rect2(Vector2i((s.position + s.offset).round()), before[s].get_size())
		var gate: bool = s in decor.gates.values()
		if gate or not Rect2i(art).intersects(Rect2i(screen)):
			check(s.texture == before[s], "%s at %s is untouched" % [s.name, s.position])
			continue
		inside += 1
		var img := s.texture.get_image()
		var old: Image = before[s].get_image()
		old.decompress()
		var spot := Vector2i(-1, -1)               # an opaque pixel of the prop that lies on the painting
		for y in range(0, img.get_height(), 3):
			for x in range(0, img.get_width(), 3):
				if old.get_pixel(x, y).a > 0.5 and screen.has_point(art.position + Vector2(x, y)):
					spot = Vector2i(x, y)
					break
			if spot.x >= 0:
				break
		if spot.x >= 0:
			check(img.get_pixelv(spot).is_equal_approx(RED), "%s shows the painting" % s.name)
		check_eq(img.get_pixel(0, 0).a > 0.5, old.get_pixel(0, 0).a > 0.5, "%s keeps its shape" % s.name)
		check_eq(s.get_child_count(), kids[s], "%s keeps its lights" % s.name)
	check(inside == n, "every re-skinned sprite touches B3 (%d, %d)" % [inside, n])
	for p: Vector2i in w.cells:
		if w.cells[p] in "HMS" and WorldMap.screen_of(p) == B3:
			check(objects.get_cell_source_id(p) == -1, "no house or Mine tile on the painting at %s" % p)
	ps.free()
	holder.free()
	map.free()
	objects.free()


func test_layout_is_the_screen_as_a_map() -> void:
	var w := _realm()
	var got := PaintedRealmScreen.layout(w, B3)
	var img: Image = got.image
	check_eq(img.get_size(), Vector2i(960, 544), "the screen's size")
	for name in ["cottage_a", "cottage_b", "campfire", "well", "smithy", "tavern", "lamppost", "mine_mouth"]:
		check(got.props.has(name), "%s is on the map" % name)
	check(not got.props.has("waystone"), "B2's waystone is not")
	check_eq(got.gates, {"O": 5, "K": 5}, "the rubble and the thorns")
	var magenta := 0
	for y in range(0, img.get_height(), 4):
		for x in range(0, img.get_width(), 4):
			if img.get_pixel(x, y).is_equal_approx(PaintedRealmScreen.LAYOUT.gate):
				magenta += 1
	check(magenta > 3 * 64, "gate squares are magenta (%d)" % magenta)


func test_the_overworld_shows_it() -> void:
	CaveArt.polish_root = _fake_painting()
	Scenes.goto("overworld")
	await physics_frames(2)
	CaveArt.polish_root = ""
	var ow = Scenes.screen
	check_eq(ow.painted.backgrounds.size(), 1, "B3's painting is in the game")
	check(ow.painted.get_index() < ow.entities.get_index(), "under the hero and the props")
	check(ow.painted.backgrounds[0].material == ow.prop_sprites[0].material, "darkens like the props")
	CaveArt.polish_root = ProjectSettings.globalize_path("user://realm_screen_none")
	Scenes.goto("overworld")
	await physics_frames(2)
	CaveArt.polish_root = ""
	check(Scenes.screen.painted.backgrounds.is_empty(), "no painting: today's look")
